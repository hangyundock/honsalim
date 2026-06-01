"""category_collect — 카테고리 단위 제품 수집·정제·티어 분류·연결 (세션 #17).

흐름 (collect-products 시나리오용과 분리 — 이쪽은 카테고리 1품목을 2티어로):
  category_sources.yml 정의 → 티어(실속/고급)별 검색어·밴드로 AliExpress 수집
  → product_filter 관련성 정제 → products upsert(정가/할인 포함)
  → category_products 연결(tier, is_featured=0 = 카탈로그).

추천 비교카드(is_featured=1) 6선은 자동 점수·순위 금지(§0 진실성) — 운영자(혼살다)가
별도로 큐레이션한다(§2-마). 본 모듈은 '전체 제품' 카탈로그를 자동으로 채운다.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # 의존성 미설치 환경 대비
    yaml = None  # type: ignore[assignment]

from collector import aliexpress as ali
from collector import product_filter, products_store
from collector.keyword_map import SearchTerm

SOURCES_FILE = Path(__file__).resolve().parent / "category_sources.yml"


@dataclass(frozen=True)
class CategorySpec:
    """카테고리 1개의 수집 정의 — 핵심어·제외어 + 티어별 검색어."""

    slug: str
    require_any: tuple[str, ...]
    require_all: tuple[tuple[str, ...], ...]  # '타입+대상' 동시 검증 그룹 (세션 #19)
    exclude_terms: tuple[str, ...]
    tiers: dict[str, SearchTerm]  # tier_name(budget/premium) -> SearchTerm


def _tier_term(raw: Any) -> SearchTerm | None:
    """tiers 항목 {q, min, max} → SearchTerm. 무효면 None."""
    if not isinstance(raw, dict):
        return None
    q = str(raw.get("q", "")).strip()
    if not q:
        return None

    def _int(v: Any) -> int | None:
        return int(v) if isinstance(v, (int, float)) else None

    return SearchTerm(q=q, min_price=_int(raw.get("min")), max_price=_int(raw.get("max")))


def load_sources(path: Path = SOURCES_FILE) -> dict[str, CategorySpec]:
    """category_sources.yml → {slug: CategorySpec}. 파일·yaml 없으면 빈 dict."""
    if yaml is None or not path.exists():
        return {}
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cats = data.get("categories") if isinstance(data, dict) else None
    if not isinstance(cats, dict):
        return {}
    out: dict[str, CategorySpec] = {}
    for slug, spec in cats.items():
        if not isinstance(spec, dict):
            continue
        tiers: dict[str, SearchTerm] = {}
        for tname, traw in (spec.get("tiers") or {}).items():
            term = _tier_term(traw)
            if term is not None:
                tiers[str(tname)] = term
        require_all = tuple(
            tuple(str(x) for x in group if str(x).strip())
            for group in (spec.get("require_all") or [])
            if isinstance(group, list) and any(str(x).strip() for x in group)
        )
        out[str(slug)] = CategorySpec(
            slug=str(slug),
            require_any=tuple(str(x) for x in spec.get("require_any", ()) if str(x).strip()),
            require_all=require_all,
            exclude_terms=tuple(str(x) for x in spec.get("exclude_terms", ()) if str(x).strip()),
            tiers=tiers,
        )
    return out


@dataclass
class CategoryCollectResult:
    """수집·연결 결과 집계 — 가시화·검증용."""

    slug: str
    dry_run: bool
    category_id: int | None = None
    received: int = 0  # API 수신 총건
    relevant: int = 0  # 관련성 정제 통과 총건
    linked: int = 0  # category_products 연결 건수(중복 제외)
    removed_stale: int = 0  # 정합화로 제거된 옛 카탈로그 연결(재수집 시 오염 청소, 세션 #19)
    per_tier: dict[str, dict[str, int]] = field(default_factory=dict)
    terms: list[tuple[str, SearchTerm]] = field(default_factory=list)


def _category_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return int(row[0]) if row else None


_LINK_SQL = """
INSERT INTO category_products (category_id, product_id, tier, is_featured, display_order)
VALUES (:category_id, :product_id, :tier, 0, :display_order)
ON CONFLICT(category_id, product_id) DO UPDATE SET
    tier          = excluded.tier,
    display_order = excluded.display_order
"""


def collect_category(
    conn: sqlite3.Connection,
    slug: str,
    *,
    dry_run: bool = True,
    page_size: int = 30,
    sleep: float = 0.2,
) -> CategoryCollectResult:
    """카테고리 slug의 티어별 검색어로 수집·정제·연결.

    dry_run=True: 검색어·밴드만 채운 결과 반환 (HTTP·DB 쓰기 없음 — 키 불필요).
    dry_run=False: ali.env 자격증명 + 실제 호출(쿼터 소모) + DB 쓰기 (§2-라 사용자 승인 후).

    호출자가 conn 생명주기 관리. 같은 제품이 두 티어에 겹쳐 잡히면 첫 티어로 한 번만 연결.
    """
    sources = load_sources()
    if slug not in sources:
        raise KeyError(f"category_sources.yml에 {slug!r} 정의 없음 (정의됨: {sorted(sources)})")
    spec = sources[slug]
    result = CategoryCollectResult(slug=slug, dry_run=dry_run)
    result.terms = list(spec.tiers.items())
    result.category_id = _category_id(conn, slug)

    if dry_run:
        return result
    if result.category_id is None:
        raise KeyError(f"categories에 {slug!r} 행 없음 — db seed 필요")

    from common import config

    config.load_secrets()  # ali.env → ALI_APP_KEY/SECRET/TRACKING_ID

    tier_rows: dict[str, list[dict[str, Any]]] = {}
    for i, (tname, term) in enumerate(spec.tiers.items()):
        if i:
            time.sleep(sleep)  # 호출 간 간격 (rate limit 보호, BACKEND §2-1)
        res = ali.query_products(
            term.q,
            timestamp=int(time.time() * 1000),
            dry_run=False,
            page_size=page_size,
            min_sale_price=term.min_price,
            max_sale_price=term.max_price,
        )
        relevant = [
            r
            for r in res.products
            if product_filter.is_relevant(
                r.get("name", ""),
                require_any=spec.require_any,
                require_all=spec.require_all,
                exclude_terms=spec.exclude_terms,
            )
        ]
        tier_rows[tname] = relevant
        result.received += len(res.products)
        result.per_tier[tname] = {"received": len(res.products), "relevant": len(relevant)}

    all_rows = [r for rows in tier_rows.values() for r in rows]
    result.relevant = len(all_rows)
    if not all_rows:
        return result

    products_store.upsert_products(conn, all_rows)

    # 정합화(세션 #19): 카탈로그(is_featured=0) 연결을 먼저 비우고 이번 수집분으로 재구성한다.
    # → 필터를 강화해 재수집하면 옛 오염 상품이 자동 제거(재수집 idempotent). 추천 6선(is_featured=1)은
    #   build-category가 관리하므로 보존(아래 INSERT의 ON CONFLICT는 is_featured를 건드리지 않음).
    prev_catalog = conn.execute(
        "SELECT COUNT(*) FROM category_products WHERE category_id = ? AND is_featured = 0",
        (result.category_id,),
    ).fetchone()[0]
    conn.execute(
        "DELETE FROM category_products WHERE category_id = ? AND is_featured = 0",
        (result.category_id,),
    )

    order = 0
    seen: set[int] = set()
    for tname, rows in tier_rows.items():
        for r in rows:
            prow = conn.execute(
                "SELECT id FROM products WHERE source = ? AND source_product_id = ?",
                (r.get("source"), r.get("source_product_id")),
            ).fetchone()
            if prow is None:
                continue
            pid = int(prow[0])
            if pid in seen:  # 두 티어에 겹친 제품 — 첫 티어 우선, 한 번만 연결
                continue
            seen.add(pid)
            conn.execute(
                _LINK_SQL,
                {
                    "category_id": result.category_id,
                    "product_id": pid,
                    "tier": tname,
                    "display_order": order,
                },
            )
            order += 1
    new_catalog = conn.execute(
        "SELECT COUNT(*) FROM category_products WHERE category_id = ? AND is_featured = 0",
        (result.category_id,),
    ).fetchone()[0]
    conn.commit()
    result.linked = len(seen)
    result.removed_stale = max(0, int(prev_catalog) - int(new_catalog))
    return result
