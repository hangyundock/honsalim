"""collector.coupang — 쿠팡 파트너스 수동 상품 적재 (API 미사용 부트스트랩, 세션 #24).

쿠팡 Open API는 **최종승인(누적 판매 15만원) 후에야** 사용 가능하다 [확정 — 쿠팡 FAQ:
"최종승인이 완료되어야 파트너스 API 기능 이용 및 첫 정산이 가능합니다"]. 승인 전에는
닭-달걀(수집하려면 API, API 쓰려면 승인)이라, 운영자가 '링크 생성'으로 만든 딥링크를
``coupang_products.yml`` 에 기록하고 본 모듈이 products(source='coupang') + category_products로
적재한다(수동 부트스트랩). 승인 후 정식 API 자동수집(Phase 4)으로 대체한다.

흐름 (collector.category_collect 알리 패턴과 대칭):
  coupang_products.yml 정의 → map_coupang_product → products upsert(products_store 재사용)
  → category_products 연결(tier=NULL=쿠팡 채널 전용, pick_reason=노트).

§0 안전:
- 가짜 데이터 금지: 쿠팡은 알리 같은 판매량·평점 신호가 없으므로 sales_volume/evaluate_rate=NULL.
- 쿠팡 상품 이미지 다운로드 금지(§9 함정3): image_url_external 미저장 — 카드는 텍스트 위주.
- 재발 방지: 알리 재수집·재빌드가 쿠팡 링크를 지우지 않도록, 알리 파이프라인의 category_products
  삭제를 source='aliexpress'로 한정한다(category_collect·category_page_builder). 본 모듈 적재분은
  source='coupang'이라 그 삭제 대상에서 구조적으로 제외된다.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # 의존성 미설치 환경 대비 (category_collect와 동일 방어)
    yaml = None  # type: ignore[assignment]

from collector import products_store

SOURCES_FILE = Path(__file__).resolve().parent / "coupang_products.yml"

# 쿠팡 파트너스 ID (마이페이지 표기 · 딥링크에 이미 추적 포함되므로 비밀 아님). affiliate_tag 기록용.
COUPANG_PARTNER_TAG = "AF4831369"


@dataclass(frozen=True)
class CoupangSpec:
    """쿠팡 수동 상품 1건 — 운영자 딥링크 + 표시 정보."""

    category: str
    name: str
    coupang_url: str
    code: str  # 딥링크에서 추출한 코드 → source_product_id·slug(cp-<code>)
    price_krw: int | None = None
    original_price_krw: int | None = None
    note: str = ""
    display_order: int = 0
    # 쿠팡 '상품 링크 → 블로그용(a 태그)' HTML이 제공하는 공식 이미지 URL(hotlink). 다운로드·자체호스팅
    # 금지(§9 함정3)지만 쿠팡 링크생성기가 임베드용으로 직접 준 이미지 URL은 정식 사용(세션 #24).
    image_url: str = ""


def extract_shortcode(url: str) -> str | None:
    """쿠팡 딥링크에서 코드 추출. `link.coupang.com/a/<코드>` → `<코드>`.

    추적 파라미터(?...)·경로 뒤 슬래시는 버린다. 형식이 다르면 None(호출자가 명시 id 요구).
    """
    if not url or "/a/" not in url:
        return None
    tail = url.split("/a/", 1)[1]
    code = tail.split("/")[0].split("?")[0].strip()
    return code or None


def _int(v: Any) -> int | None:
    return int(v) if isinstance(v, (int, float)) else None


def load_coupang_sources(
    path: Path = SOURCES_FILE, *, slug: str | None = None
) -> list[CoupangSpec]:
    """coupang_products.yml → [CoupangSpec]. 파일·yaml 없으면 빈 리스트.

    slug 지정 시 해당 카테고리만. 코드 추출 불가(딥링크 형식 이상)·필수값 누락 건은 건너뛴다.
    명시 ``id`` 가 있으면 우선 사용(딥링크 형식이 달라도 적재 가능).
    """
    if yaml is None or not path.exists():
        return []
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("products") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    out: list[CoupangSpec] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category", "")).strip()
        name = str(raw.get("name", "")).strip()
        url = str(raw.get("coupang_url", "")).strip()
        code = str(raw.get("id", "")).strip() or (extract_shortcode(url) or "")
        if not (category and name and url and code):
            continue  # 필수값 누락 — 무효 행 skip(가시화는 collect_coupang가 received-mapped로)
        if slug is not None and category != slug:
            continue
        out.append(
            CoupangSpec(
                category=category,
                name=name,
                coupang_url=url,
                code=code,
                price_krw=_int(raw.get("price_krw")),
                original_price_krw=_int(raw.get("original_price_krw")),
                note=str(raw.get("note", "")).strip(),
                display_order=_int(raw.get("display_order")) or 0,
                image_url=str(raw.get("image_url", "")).strip(),
            )
        )
    return out


def map_coupang_product(
    spec: CoupangSpec, partner_tag: str = COUPANG_PARTNER_TAG
) -> dict[str, Any]:
    """CoupangSpec → products 테이블 dict (products_store.upsert_products 입력).

    할인율은 정가>판매가일 때만 계산(알리 map_product와 동일 신뢰 규칙). 판매량·평점은 없음(NULL).
    이미지는 §9 함정3로 미저장.
    """
    sale = spec.price_krw
    orig = spec.original_price_krw
    discount_pct = round((orig - sale) / orig * 100) if orig and sale and orig > sale else None
    return {
        "source": "coupang",
        "source_product_id": spec.code,
        "name": spec.name,
        "category_path": None,
        "price_krw": sale,
        "original_price_krw": orig,
        "discount_pct": discount_pct,
        "sales_volume": None,  # 쿠팡 — 알리 판매량 신호 없음(가짜 금지 §0)
        "evaluate_rate": None,
        "currency": "KRW",
        # 쿠팡 링크생성기가 '블로그용' HTML로 제공한 공식 이미지 URL만 hotlink(임베드 정식 사용).
        # 우리가 product 페이지에서 다운로드·스크랩하는 것은 금지(§9 함정3) — 빈 값이면 미표시.
        "image_url_external": spec.image_url or None,
        "deeplink_url": spec.coupang_url,
        "deeplink_slug": f"cp-{spec.code}",
        "affiliate_tag": partner_tag,
        "availability": "unknown",
    }


@dataclass
class CoupangCollectResult:
    """적재 결과 집계 — 가시화·검증용."""

    dry_run: bool
    specs: list[CoupangSpec] = field(default_factory=list)
    upserted: int = 0  # products 신규+갱신
    linked: int = 0  # category_products 연결(중복 제외)
    pruned: int = 0  # yml에 없어 제거된 옛 쿠팡 연결(정합화)
    skipped_no_category: list[str] = field(default_factory=list)  # categories에 없는 slug


_LINK_SQL = """
INSERT INTO category_products (category_id, product_id, tier, is_featured, display_order, pick_reason)
VALUES (:category_id, :product_id, NULL, 0, :display_order, :note)
ON CONFLICT(category_id, product_id) DO UPDATE SET
    display_order = excluded.display_order,
    pick_reason   = excluded.pick_reason
"""


def _category_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return int(row[0]) if row else None


def collect_coupang(
    conn: sqlite3.Connection, slug: str | None = None, *, dry_run: bool = True
) -> CoupangCollectResult:
    """coupang_products.yml 의 쿠팡 상품을 products + category_products로 적재.

    dry_run=True(기본): yml 로드·매핑만(DB 쓰기 없음). dry_run=False: upsert + 연결.
    slug 지정 시 해당 카테고리만. 호출자가 conn 생명주기 관리.
    """
    specs = load_coupang_sources(slug=slug)
    result = CoupangCollectResult(dry_run=dry_run, specs=specs)
    if dry_run or not specs:
        return result

    rows = [map_coupang_product(s) for s in specs]
    up = products_store.upsert_products(conn, rows)
    result.upserted = up.total_written

    seen_categories: dict[str, int | None] = {}
    for spec in specs:
        if spec.category not in seen_categories:
            seen_categories[spec.category] = _category_id(conn, spec.category)
        cid = seen_categories[spec.category]
        if cid is None:
            if spec.category not in result.skipped_no_category:
                result.skipped_no_category.append(spec.category)
            continue
        prow = conn.execute(
            "SELECT id FROM products WHERE source = 'coupang' AND source_product_id = ?",
            (spec.code,),
        ).fetchone()
        if prow is None:
            continue
        conn.execute(
            _LINK_SQL,
            {
                "category_id": cid,
                "product_id": int(prow[0]),
                "display_order": spec.display_order,
                "note": spec.note or None,
            },
        )
        result.linked += 1

    # 정합화(idempotent·§0): 이번 yml에 없는 옛 쿠팡 연결을 카테고리별로 제거. 알리(source='aliexpress')는
    # 절대 안 건드림(source='coupang' 한정) → 재실행하면 yml이 곧 진실. category_collect 알리 정합화와 대칭.
    for cat in {s.category for s in specs}:
        cid = seen_categories.get(cat)
        if cid is None:
            continue
        codes = [s.code for s in specs if s.category == cat]
        # placeholders는 '?'(파라미터 자리표시자)만 — 실제 값은 (cid, *codes)로 바인딩되어 인젝션 없음.
        placeholders = ",".join("?" * len(codes))
        del_sql = (
            "DELETE FROM category_products WHERE category_id = ? AND product_id IN "  # noqa: S608
            f"(SELECT id FROM products WHERE source = 'coupang' AND source_product_id NOT IN ({placeholders}))"
        )
        cur = conn.execute(del_sql, (cid, *codes))
        result.pruned += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0

    conn.commit()
    return result
