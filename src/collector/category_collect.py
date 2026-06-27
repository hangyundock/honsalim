"""category_collect — 카테고리 단위 제품 수집·정제·티어 분류·연결 (세션 #17).

흐름 (collect-products 시나리오용과 분리 — 이쪽은 카테고리 1품목을 2티어로):
  category_sources.yml 정의 → 티어(실속/고급)별 검색어·밴드로 AliExpress 수집
  → product_filter 관련성 정제 → products upsert(정가/할인 포함)
  → category_products 연결(tier, is_featured=0 = 카탈로그).

추천 비교카드(is_featured=1) 6선은 자동 점수·순위 금지(§0 진실성) — 운영자(혼살다)가
별도로 큐레이션한다(§2-마). 본 모듈은 '전체 제품' 카탈로그를 자동으로 채운다.
"""

from __future__ import annotations

import re
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
    """category_sources.yml → {slug: CategorySpec}. 파일·yaml 없거나 깨지면 빈 dict.

    ★§0 방어(세션 #36): yml 파싱 오류(부분쓰기·잘못된 수동편집·인코딩)를 잡아 빈 dict로 폴백한다.
    여기서 예외가 전파되면 category_guardrail.check → auto_publish.monitor 전체가 크래시해 모든
    카테고리 검수가 마비된다. 빈 dict면 가드레일이 '정의 없음(보류)'로 안전하게 처리(미게시 우선).
    """
    if yaml is None or not path.exists():
        return {}
    try:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # 깨진 yml — 크래시 대신 안전 폴백(+가시화)
        from common.logging import get_logger

        get_logger(__name__).error("category_sources.yml 파싱 실패 — 빈 정의로 폴백: %s", exc)
        return {}
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
    vision_dropped: int = (
        0  # 비전 게이트가 카테고리 불일치로 드롭한 건수 (세션 #35, vision_gate ON 시)
    )
    per_tier: dict[str, dict[str, int]] = field(default_factory=dict)
    terms: list[tuple[str, SearchTerm]] = field(default_factory=list)


def _category_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return int(row[0]) if row else None


def _category_name_ko(conn: sqlite3.Connection, slug: str) -> str | None:
    """카테고리 한글명(비전 게이트 프롬프트용 — '의자'/'모니터 받침대'). 없으면 None."""
    row = conn.execute("SELECT name_ko FROM categories WHERE slug = ?", (slug,)).fetchone()
    return str(row[0]) if row and row[0] else None


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
    spec: CategorySpec | None = None,
    vision: bool | None = None,
    dry_run: bool = True,
    page_size: int = 30,
    sleep: float = 0.2,
) -> CategoryCollectResult:
    """카테고리 slug의 티어별 검색어로 수집·정제·연결.

    spec: 명시하면 category_sources.yml 대신 그 CategorySpec을 쓴다(자동 생성 카테고리·세션 #35 ③).
        None이면 yml에서 로드(기존 동작).
    vision: 비전 게이트 사용 여부 강제 — None이면 설정(vision_gate)을 따른다. 자동 provisioning은
        True로 강제(사람 단어튜닝 없이 품질 보증).
    dry_run=True: 검색어·밴드만 채운 결과 반환 (HTTP·DB 쓰기 없음 — 키 불필요).
    dry_run=False: ali.env 자격증명 + 실제 호출(쿼터 소모) + DB 쓰기 (§2-라 사용자 승인 후).

    호출자가 conn 생명주기 관리. 같은 제품이 두 티어에 겹쳐 잡히면 첫 티어로 한 번만 연결.
    """
    if spec is None:
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

    # 비전 관련성 게이트(세션 #35) — 설정 ON 시 수집 상품 이미지를 Haiku가 보고 카테고리 적합성을
    # 판정해 키워드 필터가 못 거른 오염(엉뚱한 사물)을 드롭. fail_closed(불확실=드롭·자동 안전).
    # 기본 OFF라 기존 카테고리 수집엔 무영향. 자동 카테고리 생성 시 사람 단어튜닝을 대체한다.
    from common import settings as _settings

    use_vision = _settings.get("vision_gate", False) if vision is None else vision
    if use_vision:
        from collector import vision_relevance

        label = _category_name_ko(conn, slug) or slug
        vres = vision_relevance.filter_relevant(
            all_rows,
            label,
            cap=int(_settings.get("vision_gate_cap", 40) or 40),
            fail_closed=True,
        )
        result.vision_dropped = len(vres["dropped"])
        all_rows = vres["kept"]
        result.relevant = len(all_rows)
        if not all_rows:
            return result

    products_store.upsert_products(conn, all_rows)

    # 이번 수집에서 관련(필터 통과)으로 확인된 제품 id 집합 — 정합화 기준.
    relevant_ids: set[int] = set()
    for r in all_rows:
        prow = conn.execute(
            "SELECT id FROM products WHERE source = ? AND source_product_id = ?",
            (r.get("source"), r.get("source_product_id")),
        ).fetchone()
        if prow is not None:
            relevant_ids.add(int(prow[0]))

    # 정합화(세션 #19): 카탈로그(is_featured=0) 연결을 먼저 비우고 이번 수집분으로 재구성한다.
    # → 필터를 강화해 재수집하면 옛 오염 상품이 자동 제거(재수집 idempotent).
    prev_catalog = conn.execute(
        "SELECT COUNT(*) FROM category_products WHERE category_id = ? AND is_featured = 0",
        (result.category_id,),
    ).fetchone()[0]
    conn.execute(
        "DELETE FROM category_products WHERE category_id = ? AND is_featured = 0",
        (result.category_id,),
    )
    # ★세션 #22 근본수정: 이제 비관련이 된 옛 추천(is_featured=1)도 제거. 안 그러면 필터를 강화해도
    #   옛 오염 추천이 남아 build의 select_featured(판매량순)가 그놈을 다시 뽑아 오염이 영속된다.
    #   여전히 관련인 추천(product_id ∈ relevant_ids)은 보존 — build가 6선을 재확정하기 전 안전.
    featured_rows = conn.execute(
        "SELECT product_id FROM category_products WHERE category_id = ? AND is_featured = 1",
        (result.category_id,),
    ).fetchall()
    stale_featured = [
        (result.category_id, int(fr[0])) for fr in featured_rows if int(fr[0]) not in relevant_ids
    ]
    if stale_featured:
        conn.executemany(
            "DELETE FROM category_products WHERE category_id = ? AND product_id = ?",
            stale_featured,
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


def search_tiers(
    spec: CategorySpec,
    *,
    page_size: int = 30,
    sleep: float = 0.2,
) -> tuple[list[dict[str, Any]], int]:
    """카테고리 spec의 영어 티어 검색어로 알리 검색 → 원시 상품(정제·DB 무관·순수).

    ``collect_category``와 같은 ali 호출 규약(티어별 영어 q + 가격밴드 + 호출 간 sleep)을 쓰되
    관련성 필터·DB 쓰기는 호출자에 맡긴다(키워드 경로는 키워드-인지 '유효 제외어'를 써야 해서
    필터를 분리한다 — keyword_relevance.filter_products). 키워드→글 경로가 **한글 키워드 직접검색**
    (알리 영어 인덱스에 매칭 실패 → 폰케이스·티셔츠 등 잡동사니, 세션 #29 라이브 적발) 대신 이
    영어 검색을 재사용한다. 호출 전 ``config.load_secrets()`` 필요(자격증명).

    티어 간 중복 제품(source+source_product_id)은 한 번만 담는다. 반환 (raw_rows, received_total).
    """
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    received = 0
    for i, (_tname, term) in enumerate(spec.tiers.items()):
        if i:
            time.sleep(sleep)  # 호출 간 간격 (rate limit 보호) — collect_category와 동일
        res = ali.query_products(
            term.q,
            timestamp=int(time.time() * 1000),
            dry_run=False,
            page_size=page_size,
            min_sale_price=term.min_price,
            max_sale_price=term.max_price,
        )
        received += len(res.products)
        for r in res.products:
            key = (r.get("source"), r.get("source_product_id"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
    return rows, received


def append_category_source(
    slug: str, label_ko: str, spec: CategorySpec, *, path: Path = SOURCES_FILE
) -> bool:
    """자동 생성 카테고리를 category_sources.yml에 등록 (세션 #36 근본수정).

    provision-category가 만든 카테고리를 category_guardrail이 검수할 수 있게 yml에 항목을 추가한다.
    yml에 없으면 가드레일이 "정의 없음(검수 불가)"로 무조건 보류('미달')해 자동 카테고리가 영구
    플래그·자동 비공개 위험에 놓인다(라이브 적발) → 생성 시 함께 등록해 근본 차단.

    require_any=[] 로 쓴다 — 관련성 정밀 판정은 수집 시 비전 게이트(vision_relevance)가 이미 수행
    하고, 자동 수집 상품은 이름이 제각각이라 단일 키워드로 못 묶기 때문(#36 to_spec과 동일 원칙).
    이미 같은 slug가 정의돼 있으면 건드리지 않는다(멱등). 사람이 라이브 실측으로 다듬는다(§2-마).

    반환: 새로 추가했으면 True, 이미 있거나 파일/yaml 없으면 False.
    """
    if yaml is None or not path.exists():
        return False
    from common.logging import get_logger

    log = get_logger(__name__)
    original = path.read_text(encoding="utf-8")
    # 멱등 — 이미 같은 slug 키(2칸 들여쓰기, 인라인 주석 허용)가 있으면 그대로 둔다(사람 수정 보존).
    if re.search(rf"^\s{{2}}{re.escape(slug)}:\s*(?:#.*)?$", original, re.MULTILINE):
        return False
    # 제외어·검색어 새너타이즈 — yaml 흐름 시퀀스([..])를 깨는 특수문자가 든 항목은 버린다(제외어는
    # 비전 게이트의 보조 백스톱이라 일부 빠져도 무해). 깨진 yml은 load_sources 전체를 다운시켜 모든
    # 카테고리 가드레일을 마비시키므로 절대 만들지 않는다(§0). 버려진 항목은 로깅(가시화).
    bad = set(",[]{}:#\"'\\\n")
    excl_terms = [t for t in spec.exclude_terms if t and not (bad & set(t))]
    dropped = [t for t in spec.exclude_terms if t and (bad & set(t))]
    excl = ", ".join(excl_terms)
    lines = [
        "",
        f"  # {label_ko} — provision-category(자동 프로비저닝) 생성. "
        "require_any=[](관련성=비전 게이트·#36).",
        f"  {slug}:",
        "    require_any: []",
        f"    exclude_terms: [{excl}]",
        "    tiers:",
    ]
    for tname in ("budget", "premium"):
        term = spec.tiers.get(tname)
        if term is None:
            continue
        q = term.q.replace("\\", "").replace('"', "").replace("\n", " ").strip()
        parts = [f'q: "{q}"']
        if term.min_price is not None:
            parts.append(f"min: {term.min_price}")
        if term.max_price is not None:
            parts.append(f"max: {term.max_price}")
        lines.append(f"      {tname}: {{{', '.join(parts)}}}")
    block = "\n".join(lines) + "\n"
    new_text = (original if original.endswith("\n") else original + "\n") + block
    # 쓰기 전 검증 — 깨지면 운영 파일을 아예 안 건드린다(노출 0).
    try:
        yaml.safe_load(new_text)
    except Exception as exc:  # 어떤 파싱 오류든 등록 건너뜀(가드레일 다운 방지·§0)
        log.error("append_category_source: %s yaml 생성 실패 — 등록 건너뜀: %s", slug, exc)
        return False
    # 원자적 교체 — temp에 쓴 뒤 rename(부분쓰기가 운영 파일에 노출되지 않음·동시 reader 안전).
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(path)
    if dropped:
        log.warning("append_category_source: %s 제외어 yaml특수문자로 제외됨 %r", slug, dropped)
    return True
