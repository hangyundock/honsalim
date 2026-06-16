"""혼살림 정적 사이트 렌더러 — DB + Jinja2 템플릿 → 정적 HTML.

출처: FRONTEND §2~§4 + Claude Design 핸드오프 템플릿 (DECISIONS G4).

미리보기 `scripts/preview_build.py`(목업 데이터)와 달리, 본 렌더러는 실제
SQLite DB(personas·scenarios·articles)를 읽어 공개 사이트를 생성한다.

현 상태 [확정 2026-05-30]: 게시 articles 0편.
- home·scenarios·personas·about → 시나리오/페르소나 시드(실데이터)로 렌더.
- 상세글(article 상세 페이지)은 published articles + body_html↔템플릿 매핑 설계
  후 추가 (현재 0편이라 미렌더). 시나리오 카드 링크(/articles/<slug>/)는
  콘텐츠 게시(Phase 3~4) 후 활성화.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sqlite3
import statistics
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from builder import jsonld
from collector import product_filter
from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DEFAULT_OUT = PROJECT_ROOT / "build" / "site"
SITE_ORIGIN = "https://honsallim.com"
SITE_DESC = "1인 가구·자취·홈오피스·일상살림 추천 가이드. 혼자 살림을 따뜻하게 시작하세요."

# ── 상품명 표시 정리 (세션 #34) ──────────────────────────────────────────
# 알리 원본 상품명은 기계번역 키워드 나열·제로폭문자·잡기호가 섞여, 카드에 그대로 쓰면 지저분하다
# (예: "게임 의자, 리클라이닝, 컴퓨터 의자, 집, 점심 시간, ..."). **표시용으로만** 정리한다 —
# 저장값·타입추출(_derive_type)·관련성 필터는 원본을 써 신호를 보존한다. 결정적·무비용(LLM 무관·§0).
_INVISIBLE = frozenset(
    cp
    for lo, hi in ((0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2060), (0xFEFF, 0xFEFF))
    for cp in range(lo, hi + 1)
)
_MULTISPACE_RE = re.compile(r"\s+")


def clean_product_name(raw: str, max_len: int = 44, max_parts: int = 3) -> str:
    """알리 원본 상품명 → 카드 표시용 깔끔한 이름. 결정적·무비용(세션 #34).

    제로폭/방향제어 문자·홀로 떠도는 기호(°) 제거 → 공백 정리 → 콤마 나열형은 앞쪽 핵심
    max_parts개 구절만 취함(끝없는 키워드 나열 차단) → 길이 초과 시 단어 경계 절단. 빈 값은 '추천 상품'.
    """
    s = unicodedata.normalize("NFKC", raw or "").translate({c: None for c in _INVISIBLE})
    s = s.replace("°", " ")
    s = _MULTISPACE_RE.sub(" ", s).strip(" ,·-|")
    if not s:
        return "추천 상품"
    parts = [p.strip() for p in s.split(",") if p.strip()][:max_parts]
    name = " ".join(parts)
    if len(name) > max_len:
        cut = name[:max_len].rstrip()
        name = (cut.rsplit(" ", 1)[0] if " " in cut else cut) + "…"
    return name or "추천 상품"


# robots.txt — /go/ 게이트웨이(제휴 redirect)는 색인 제외, sitemap 안내
ROBOTS_TXT = f"User-agent: *\nAllow: /\nDisallow: /go/\n\nSitemap: {SITE_ORIGIN}/sitemap.xml\n"

# Cloudflare Pages _headers — 정적 자산 장기 캐시 + 기본 보안 헤더 (FRONTEND §9 / POLICY §6)
HEADERS_FILE = (
    # 정적 자산(해시·버전 무관 안정 자산)은 1년 immutable — 더 구체적 경로라 /* 보다 우선 적용.
    "/static/*\n"
    "  Cache-Control: public, max-age=31536000, immutable\n"
    "\n"
    # HTML 등 그 외 전체 — 짧은 엣지 캐시(5분)+브라우저 재검증. 무인 일일 발행/수정·삭제가
    # 최대 7일 지연되던 문제(세션 #20) 방지: 콘텐츠 변경이 수 분 내 반영되도록 origin에서 명시.
    "/*\n"
    "  Cache-Control: public, max-age=0, s-maxage=300, must-revalidate\n"
    "  X-Content-Type-Options: nosniff\n"
    "  Referrer-Policy: strict-origin-when-cross-origin\n"
    "  X-Frame-Options: DENY\n"
)

# 301 리다이렉트 (Cloudflare Pages _redirects 형식) — 카테고리로 흡수돼 비공개된 글의 라이브 URL을
# 후속 카테고리로 영구 이전(404·SEO 손실 방지, 세션 #31 분류 체계). (src, dst) 튜플.
REDIRECTS: list[tuple[str, str]] = [
    # 게이밍의자 글 → 의자 카테고리(게이밍=의자의 타입으로 흡수, #31)
    ("/articles/kw-e3d08a2c/", "/categories/office-chair/"),
]

WOOD = ["var(--wood-1)", "var(--wood-2)", "var(--wood-3)", "var(--wood-4)"]
PERSONA_ICON = {"cheot-jachi": "key", "homeoffice": "laptop", "minimal-life": "plant"}
# 페르소나 공간 개념이미지(scripts/gen_persona_images.py 생성). 값이 비면 image_block
# 매크로가 우드톤 placeholder로 폴백(graceful·무인 안전). 세션 #21: 미충전 placeholder 채움.
PERSONA_IMG = {
    "cheot-jachi": "/static/images/concepts/persona-cheot-jachi.webp",
    "homeoffice": "/static/images/concepts/persona-homeoffice.webp",
    "minimal-life": "/static/images/concepts/persona-minimal-life.webp",
}

# 시즌 캘린더 — 콘텐츠 무관 정적 4분기 (홈 섹션)
SEASON_CALENDAR = [
    {
        "icon": "spring",
        "name": "봄",
        "sub": "이사·풀세팅",
        "months": "2~4월",
        "desc": "이사 성수기. 원룸 첫 세팅과 수납 정리 수요가 가장 높은 시기.",
        "img": "var(--wood-3)",
        "url": "/scenarios/",
    },
    {
        "icon": "summer",
        "name": "여름",
        "sub": "제습·수면",
        "months": "5~8월",
        "desc": "습기·열대야 대응. 제습기·서큘레이터·암막·쿨매트 중심.",
        "img": "var(--wood-1)",
        "url": "/scenarios/",
    },
    {
        "icon": "fall",
        "name": "가을",
        "sub": "주방·정리",
        "months": "9~10월",
        "desc": "환절기 정리와 주방 살림 보강. 빨래 건조 고민이 시작되는 시기.",
        "img": "var(--wood-2)",
        "url": "/scenarios/",
    },
    {
        "icon": "winter",
        "name": "겨울",
        "sub": "난방·보온",
        "months": "11~1월",
        "desc": "난방비·보온이 핵심. 전기요·온수매트·가전 정착 수요 급증.",
        "img": "var(--wood-4)",
        "url": "/scenarios/",
    },
]

# 사업자 정보 — M2 결정(세션 #7) + 세션 #20: 미등록 필드는 빈 값으로 숨김.
# bizno·mailorder·addr는 사업자 등록(DECISIONS D4: 월 10만원 누적 후) 전까지 빈 값 →
# footer/about/article에서 조건부로 미표시(정직성 §0: "등록 진행 중" 과장 표기 제거).
# 등록 후 실제 값을 채우면 자동으로 다시 노출된다.
BUSINESS_INFO = {
    "name": "혼살림",
    "rep": "혼살다 (운영자)",
    "bizno": "",
    "mailorder": "",
    "email": "dugi2020@naver.com",
    "addr": "",
}

# 허브 예산 필터 — 실제 시드 예산 분포 기준
BUDGET_FILTERS = [
    {"id": "low", "label": "~35만 원"},
    {"id": "mid", "label": "35~70만 원"},
    {"id": "high", "label": "70만 원+"},
]


def _budget_display(mn: int | None, mx: int | None) -> str:
    if mn and mx:
        return f"{mn // 10000}~{mx // 10000}만 원"
    if mx:
        return f"~{mx // 10000}만 원"
    return ""


def _budget_tier(mx: int | None) -> str:
    if not mx:
        return ""
    if mx <= 350000:
        return "low"
    if mx <= 700000:
        return "mid"
    return "high"


def _scenario_card(row: sqlite3.Row) -> dict:
    slug = row["slug"]
    # 게시된 글이 있는 시나리오만 /articles/<slug>/로 링크 — 없으면 url=None(비클릭 '준비 중').
    # 글 없는 카드가 404로 가는 것을 방지 (콘텐츠 단계적 발행 중 깨진 링크 회피).
    article_slug = row["article_slug"] if "article_slug" in row.keys() else None
    has_article = bool(article_slug)
    product_count = row["product_count"] if "product_count" in row.keys() else 0
    return {
        "id": slug,
        "title": row["title_ko"],
        "desc": row["description"],
        "persona": row["persona_slug"],
        "persona_name": row["persona_title"],
        "persona_icon": PERSONA_ICON.get(row["persona_slug"], ""),
        "season": row["season_peak"] or "",
        "season_icon": "",  # season_peak는 월 범위 텍스트 — 아이콘 오매핑 회피
        "budget": _budget_display(row["budget_min_krw"], row["budget_max_krw"]),
        "budget_tier": _budget_tier(row["budget_max_krw"]),
        "count": product_count if has_article else 0,
        # 시나리오 카드 이미지 = 소속 페르소나 개념이미지 재사용(추가 비용 0). 세션 #21.
        "img": PERSONA_IMG.get(row["persona_slug"], ""),
        "cap": row["season_peak"] or "",
        "url": f"/articles/{article_slug}/" if has_article else None,
        "available": has_article,
    }


def _load_scenarios(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT s.*, p.slug AS persona_slug, p.title_ko AS persona_title,
               (SELECT a.slug FROM articles a
                WHERE a.scenario_id = s.id AND a.status = 'published'
                ORDER BY a.published_at DESC LIMIT 1) AS article_slug,
               (SELECT COUNT(*) FROM article_products ap
                JOIN articles a2 ON a2.id = ap.article_id
                WHERE a2.scenario_id = s.id AND a2.status = 'published') AS product_count
        FROM scenarios s JOIN personas p ON p.id = s.persona_id
        WHERE s.active = 1
        ORDER BY s.priority DESC, s.id
        """).fetchall()
    return [_scenario_card(r) for r in rows]


def _load_personas(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM personas ORDER BY display_order, id").fetchall()
    out: list[dict] = []
    for r in rows:
        slug = r["slug"]
        brows = conn.execute(
            "SELECT budget_min_krw, budget_max_krw, season_peak FROM scenarios "
            "WHERE persona_id = ? AND active = 1",
            (r["id"],),
        ).fetchall()
        mids = [
            (b["budget_min_krw"] + b["budget_max_krw"]) // 2
            for b in brows
            if b["budget_min_krw"] and b["budget_max_krw"]
        ]
        avg = f"{round(statistics.mean(mids) / 10000)}만 원" if mids else ""
        peaks = list(dict.fromkeys(b["season_peak"] for b in brows if b["season_peak"]))
        out.append(
            {
                "id": slug,
                "name": r["title_ko"],
                "line": r["description"],
                "desc": r["description"],
                "icon": PERSONA_ICON.get(slug, ""),
                "img": PERSONA_IMG.get(slug, WOOD[0]),
                "bullets": [],  # DB 스키마에 없음 — 콘텐츠 보강 시 추가
                "keywords": [],
                "avgBudget": avg,
                "peak": " · ".join(peaks),
                "url": f"/personas/{slug}/",
            }
        )
    return out


ARTICLE_DETAIL_SQL = """
    SELECT a.id, a.slug, a.title, a.summary, a.body_html, a.meta_description,
           a.schema_jsonld, a.published_at, a.structured_json,
           s.season_peak, s.budget_min_krw, s.budget_max_krw,
           p.slug AS persona_slug, p.title_ko AS persona_title
    FROM articles a
    JOIN scenarios s ON s.id = a.scenario_id
    JOIN personas p ON p.id = s.persona_id
    WHERE a.status = 'published'
    ORDER BY a.published_at DESC
"""

ARTICLE_PRODUCTS_SQL = """
    SELECT pr.name, pr.price_krw, pr.deeplink_slug, pr.category_path, pr.image_url_external,
           pr.source, pr.original_price_krw, pr.discount_pct, pr.sales_volume
    FROM article_products ap
    JOIN products pr ON pr.id = ap.product_id
    WHERE ap.article_id = ?
    ORDER BY ap.display_order, ap.product_id
"""

# 검토 대기(validated) 시나리오 draft — 미리보기 전용(§2-마 인간 검토 게이트, 세션 #29).
# 본문·메타·featured 상품은 drafts.enriched_payload(JSON)에 있다(promote와 동일 소스).
DRAFT_ARTICLE_SQL = """
    SELECT d.id, d.enriched_payload,
           s.slug AS scenario_slug, s.season_peak, s.budget_min_krw, s.budget_max_krw,
           p.slug AS persona_slug, p.title_ko AS persona_title
    FROM drafts d
    JOIN scenarios s ON s.id = d.scenario_id
    JOIN personas p ON p.id = s.persona_id
    WHERE d.status = 'validated' AND d.enriched_payload IS NOT NULL
    ORDER BY d.id DESC
"""


def _price_krw(value: int | None) -> str:
    return f"{value:,}원" if value else ""


def _article_product_cards(prods: list) -> list[dict]:
    """products 행 목록 → article.html 상품카드 컨텍스트 (published·draft 공용).

    img_url=image_url_external(알리/쿠팡 공식배너 hotlink — 카테고리와 동일), 없으면 우드톤 fallback.
    source(쿠팡/알리)·할인(부풀린 할인은 trusted_discount가 차단)·판매량을 함께 담아 글 카드가
    쿠팡(이미지·구매)/알리(데이터=Information Gain)로 차등 렌더되게 한다 (세션 #30 글 레이아웃).
    """
    from collector import product_filter

    cards: list[dict] = []
    for i, pr in enumerate(prods):
        disc = product_filter.trusted_discount(pr["discount_pct"])
        orig = pr["original_price_krw"]
        show_disc = disc is not None and bool(orig)
        cards.append(
            {
                "source": pr["source"] or "",
                "name": clean_product_name(pr["name"]),
                "price": _price_krw(pr["price_krw"]),
                "url": f"/go/{pr['deeplink_slug']}",
                "img": WOOD[i % len(WOOD)],  # img_url 없을 때 우드톤 fallback 색
                "img_url": pr["image_url_external"] or "",  # 실제 상품 이미지(hotlink)
                "cat": pr["category_path"] or "",
                "tag": "",
                "why": "",  # 구조화 장단점은 Tier 2(LLM)에서 — v1은 데이터(가격·할인·판매량)로
                "orig": _price_krw(orig) if show_disc else "",  # 정가(할인 신뢰 시만)
                "disc": f"{disc}%" if show_disc else "",  # 할인율(부풀림 차단 후)
                "volume": pr["sales_volume"] or 0,  # 알리 판매량(Information Gain)
                "price_num": pr["price_krw"] or 0,  # 데이터 요약 가격대 계산용(화면 비노출)
                "disc_num": disc or 0,  # 픽 역할(가성비) 도출용 숫자 할인율(화면 비노출)
            }
        )
    return cards


def _vol_fmt(v: int | None) -> str:
    """판매량 정수 → 천단위 콤마 문자열(0/None은 빈 값)."""
    return f"{v:,}" if v else ""


def _article_tier_split(ali_cards: list[dict]) -> tuple[list[dict], list[dict]]:
    """알리 카드를 가격 기준 2티어(💰실속/⭐고급)로 분할 (CATEGORY_PAGE §2-7 구조 차용).

    글에는 category_products.tier 컬럼이 없으므로 가격 중앙값으로 나눈다(저가=실속, 고가=고급).
    한쪽이 비지 않도록 절반 분할. 카테고리 페이지와 동일한 2티어 비교 경험을 글에도 제공.
    """
    s = sorted(ali_cards, key=lambda c: c.get("price_num") or 0)
    n = len(s)
    if n == 0:
        return [], []
    if n == 1:
        return s, []
    half = (n + 1) // 2
    return s[:half], s[half:]


def _article_featured(cards: list[dict], k: int = 4) -> list[dict]:
    """티어 내 추천 featured 선정 — 판매량 desc(없으면 할인) 상위 k (CATEGORY_PAGE §2-7).

    k=4 → 실속 4 + 고급 4 = 추천 8선(주인 요청·세션 #34 상품 중심). LLM이 featured 8개 선언 시 채워짐.
    """
    return sorted(
        cards, key=lambda c: (c.get("volume") or 0, c.get("disc_num") or 0), reverse=True
    )[:k]


def _article_pick_item(card: dict, tier: str, type_label: str) -> dict:
    """글 추천 카드 컨텍스트 — category.html pick_card 매크로 호환(이미지·장단점·추천대상).

    장단점(pros/cons)·추천대상(reason)은 LLM 구조화 출력(Tier 2-A)에서 채운다 — 없으면
    pick_card 매크로가 그 줄만 건너뜀(graceful). 가격·할인·판매량은 데이터로 도출.
    """
    return {
        "tier": tier,
        "type": type_label,
        "name": card["name"],
        "price": card["price"],
        "orig": card["orig"],
        "disc": card["disc"],
        "volume": _vol_fmt(card.get("volume")),
        "img_url": card["img_url"],
        "url": card["url"],
        "pros": card.get("pros") or [],
        "cons": card.get("cons") or [],
        "reason": card.get("for_who") or "",
    }


def _article_coupang_pick(card: dict) -> dict:
    """쿠팡 운영자 추천 픽 — 별도 zone(주인 결정 #31). 할인·판매량 데이터 없음(공식 배너만)."""
    return {
        "tier": "coupang",
        "coupang": True,
        "type": "운영자 추천",
        "name": card["name"],
        "price": card["price"],
        "orig": card["orig"],
        "disc": card["disc"],
        "volume": "",
        "img_url": card["img_url"],
        "url": card["url"],
        "pros": card.get("pros") or [],
        "cons": card.get("cons") or [],
        "reason": card.get("for_who") or "운영자가 직접 고른 제품",
    }


def _article_catalog_item(card: dict, tier: str) -> dict:
    """글 전체 제품 카탈로그 카드 — category.html .grid .card 호환(정렬·필터 data-* 포함)."""
    return {
        "tier": tier,
        "tier_label": "💰 실속" if tier == "budget" else "⭐ 고급",
        "name": card["name"],
        "price": card["price"],
        "orig": card["orig"],
        "disc": card["disc"],
        "price_num": card.get("price_num") or 0,
        "disc_num": card.get("disc_num") or 0,
        "volume": _vol_fmt(card.get("volume")),
        "img_url": card["img_url"],
        "url": card["url"],
        "slug": (card.get("url") or "").rsplit("/", 1)[-1],
    }


def _build_article_compare(featured: list[dict], limit: int = 6) -> dict:
    """추천 featured(알리) → 한눈 비교표 (category.html cmp 형식: rows·cols).

    데이터(할인·누적 판매)만 비교 — 평점·스펙 같은 미보유 데이터는 만들지 않음(§0 진실성).
    """
    cols = [
        {
            "name": c["name"],
            "type": c.get("type", ""),
            "tier": c.get("tier", "budget"),
            "price": c["price"],
            "vals": [c["disc"] or "—", c["volume"] or "—"],
        }
        for c in featured[:limit]
    ]
    return {"rows": ["할인", "누적 판매"], "cols": cols}


def _build_article_data_summary(ali_cards: list[dict]) -> dict:
    """글 상단 데이터 요약 — 수집 실데이터(개수·가격대·판매 1위)에서 도출(가짜 없음·§0)."""
    if not ali_cards:
        return {"count": 0}
    prices = [c["price_num"] for c in ali_cards if c.get("price_num")]
    vols = [((c.get("volume") or 0), c["name"]) for c in ali_cards]
    top_v, top_n = max(vols, key=lambda x: x[0]) if vols else (0, "")
    return {
        "count": len(ali_cards),
        "price_range": (f"{_price_krw(min(prices))} ~ {_price_krw(max(prices))}" if prices else ""),
        "top_name": ((top_n[:28] + "…" if len(top_n) > 28 else top_n) if top_v > 0 else ""),
        "top_volume": f"{top_v:,}" if top_v > 0 else "",
    }


def _split_article_guide(body_html: str) -> tuple[str, str, str]:
    """본문 HTML → (도입, 가이드 前, 가이드 後) 3분할 (세션 #31 카테고리 구조).

    - 도입 = 첫 ``<h2>`` 전(H1 + 첫머리 대가성 고지 + 리드).
    - 제품 나열 '추천 상품' 섹션(``<h2>``에 '추천'·'제품' 포함)은 **본문에서 제외** —
      그 자리는 시각 추천 카드(2티어·카탈로그)로 대체한다(주인 지시 #31: 텍스트 말고 이미지).
    - 가이드 前 = 추천 섹션 앞 정보 섹션(누구를 위한·왜 예산), 가이드 後 = 추천 섹션 뒤(예산 분배·FAQ 등).
    SEO 정보 콘텐츠(가이드)는 유지하되, 제품은 이미지 카드로 본다(텍스트 벽 제거).
    """
    m = re.search(r"<h2", body_html)
    if not m:
        return body_html, "", ""
    intro, rest = body_html[: m.start()], body_html[m.start() :]
    heads = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", rest, re.S))
    # 제품 나열 섹션('추천 상품'/'추천 제품' 등) 헤딩 — '상품'·'제품' 단어로 식별(다른 '추천' 헤딩 오매칭 방지)
    rec_i = next(
        (i for i, mm in enumerate(heads) if ("상품" in mm.group(1) or "제품" in mm.group(1))),
        None,
    )
    if rec_i is None:
        return intro, rest, ""  # 추천 섹션 없음 → 전부 가이드 前
    guide_pre = rest[: heads[rec_i].start()]
    # 추천 섹션은 다음 <h2>까지 — 그 뒤(예산 분배·FAQ 등)만 가이드 後로 살린다
    guide_post = rest[heads[rec_i + 1].start() :] if rec_i + 1 < len(heads) else ""
    return intro, guide_pre, guide_post


def _article_page_ctx(
    *,
    slug: str,
    title: str,
    summary: str,
    meta_description: str,
    schema_raw: str | None,
    body_html: str,
    persona_slug: str,
    persona_title: str,
    season_peak: str | None,
    budget_min: int | None,
    budget_max: int | None,
    products: list[dict],
    is_draft: bool = False,
    structured: dict | None = None,
) -> dict:
    """article.html 렌더 컨텍스트 (published·draft 공용). is_draft=True면 검토용 배너 표시.

    세션 #31 Tier 2: 글을 '독서(텍스트 벽)'→'쇼핑(스캔)'으로. 빠른 결론·추천 픽 카드(역할·
    소스 배지)·한눈 비교표(알리 데이터)·체크포인트·예산표를 시각 블록으로 배치한다.
    - 픽/비교표/데이터 요약은 상품 데이터로 항상 도출(LLM 없이도 작동).
    - quick_verdict·checkpoints·budget_tiers와 픽의 장단점은 LLM 구조화 출력(structured)이
      있을 때만 채움 — 없으면 그 섹션만 건너뜀(graceful fallback, 빈 섹션 X).
    본문(intro/pre/rec)은 무손상(SEO 콘텐츠 보존) — 위치만 분할(세션 #30 데이터 플러밍 재사용).
    """
    # Tier 2 구조화(세션 #34): structured(LLM 출력)의 추천별 장단점·추천대상을 카드에 slug로 부착 →
    # pick_card 매크로가 카테고리와 동일하게 렌더. quick_verdict·checkpoints는 컨텍스트로 전달.
    notes = (structured or {}).get("product_notes") or {}
    for c in products:
        n = notes.get((c.get("url") or "").rsplit("/", 1)[-1])
        if n:
            c["pros"] = list(n.get("pros") or [])
            c["cons"] = list(n.get("cons") or [])
            c["for_who"] = str(n.get("for_who") or n.get("for") or "")
    intro_html, guide_pre, guide_post = _split_article_guide(body_html)
    coupang_cards = [p for p in products if p["source"] == "coupang"]
    ali_cards = [p for p in products if p["source"] != "coupang"]
    # 알리 2티어(💰실속/⭐고급) 분할 + 티어별 추천 featured (CATEGORY_PAGE §2-7)
    budget_cards, premium_cards = _article_tier_split(ali_cards)
    picks_budget = [
        _article_pick_item(c, "budget", "💰 실속형") for c in _article_featured(budget_cards)
    ]
    picks_premium = [
        _article_pick_item(c, "premium", "⭐ 고급형") for c in _article_featured(premium_cards)
    ]
    # 쿠팡 = 상단 별도 '운영자 추천' zone (주인 결정 #31)
    coupang_picks = [_article_coupang_pick(c) for c in coupang_cards]
    # 전체 제품 카탈로그 (알리 전체, 티어 태그) — CATEGORY_PAGE §5-bis (많은 제품 노출)
    catalog = [_article_catalog_item(c, "budget") for c in budget_cards] + [
        _article_catalog_item(c, "premium") for c in premium_cards
    ]
    compare = _build_article_compare(picks_budget + picks_premium)
    return {
        "slug": slug,
        "title": title,
        "meta_description": meta_description,
        "schema_raw": schema_raw,
        "is_draft": is_draft,  # sitemap·게시수 제외 플래그 (공개 산출물 아님)
        "article": {
            "slug": slug,
            "title": title,
            "summary": summary,
            "desc": meta_description,
            "body_html": body_html,  # 전체(스키마·호환용) — 렌더는 분할본 사용
            "intro_html": intro_html,  # H1 + 첫머리 고지 + 리드
            "guide_pre": guide_pre,  # 추천 前 가이드 정보(누구를 위한·왜 예산)
            "guide_post": guide_post,  # 추천 後 가이드(예산 분배·FAQ 등)
            "persona": persona_slug,
            "persona_name": persona_title,
            "persona_icon": PERSONA_ICON.get(persona_slug, ""),
            "season": season_peak or "",
            "budget": _budget_display(budget_min, budget_max),
            "is_draft": is_draft,
        },
        "products": products,
        # 카테고리 구조 컨텍스트 (세션 #31): 쿠팡 운영자추천 + 알리 2티어 + 비교표 + 전체 카탈로그
        "coupang_picks": coupang_picks,
        "picks_budget": picks_budget,
        "picks_premium": picks_premium,
        "has_picks": bool(coupang_picks or picks_budget or picks_premium),
        "compare": compare,
        "has_compare": len(compare["cols"]) >= 2,
        "catalog": catalog,
        "has_catalog": bool(catalog),
        "art_data_summary": _build_article_data_summary(ali_cards),
        # Tier 2 구조화(세션 #34) — LLM structured가 있을 때만 채움(없으면 빈 값·섹션 건너뜀)
        "quick_verdict": str((structured or {}).get("quick_verdict") or ""),
        "checkpoints": (structured or {}).get("checkpoints") or [],
        "has_checkpoints": bool((structured or {}).get("checkpoints")),
        "concept_image": str((structured or {}).get("concept_image") or ""),  # 글 히어로(세션 #34)
        "concept_image_alt": str((structured or {}).get("concept_image_alt") or ""),
    }


def _load_article_pages(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """published articles → 상세글 렌더 컨텍스트 (산문 본문 + /go/ 제휴 상품 카드).

    include_drafts=True(미리보기·검토용·§2-마)면 검토 대기(validated) 시나리오 draft도 함께
    렌더 → 운영자가 승인 전에 발행 후와 동일한 화면(쿠팡 이미지+알리 데이터)을 본다. 공개
    배포(기본)는 published만. 상품 이미지는 image_url_external(알리·쿠팡 공식배너 hotlink) 사용.
    """
    pages: list[dict] = []
    seen_slugs: set[str] = set()
    for row in conn.execute(ARTICLE_DETAIL_SQL).fetchall():
        prods = conn.execute(ARTICLE_PRODUCTS_SQL, (row["id"],)).fetchall()
        try:  # Tier 2 구조화(세션 #34) — 발행 글의 추천 장단점·빠른결론·체크포인트(있으면)
            structured = json.loads(row["structured_json"]) if row["structured_json"] else None
        except (json.JSONDecodeError, TypeError):
            structured = None
        pages.append(
            _article_page_ctx(
                slug=row["slug"],
                title=row["title"],
                summary=row["summary"],
                meta_description=row["meta_description"],
                schema_raw=row["schema_jsonld"],
                body_html=row["body_html"],
                persona_slug=row["persona_slug"],
                persona_title=row["persona_title"],
                season_peak=row["season_peak"],
                budget_min=row["budget_min_krw"],
                budget_max=row["budget_max_krw"],
                products=_article_product_cards(prods),
                structured=structured,
            )
        )
        seen_slugs.add(row["slug"])
    if include_drafts:
        pages.extend(_load_draft_article_pages(conn, seen_slugs))
    return pages


def _load_draft_article_pages(conn: sqlite3.Connection, seen_slugs: set[str]) -> list[dict]:
    """검토 대기(validated) 시나리오 draft → 상세글 컨텍스트 (미리보기 전용·§2-마 검토 게이트).

    본문·메타·featured 상품은 drafts.enriched_payload(JSON)에 있다(promote와 동일 소스).
    body_md→HTML 변환도 promote와 동일(검증 본문 무변형 — validated 본문 = published 본문).
    같은 slug published 글이 있으면 published 우선(미리보기에서 라이브 글을 draft로 덮지 않음).
    draft 글은 sitemap·게시수에서 제외되고 build/preview에만 생성된다(공개 배포 산출물 아님).
    """
    from writer import article_writer  # 본문 변환 공용(제품 코드 제거) — promote와 동일

    pages: list[dict] = []
    for row in conn.execute(DRAFT_ARTICLE_SQL).fetchall():
        slug = row["scenario_slug"]
        if slug in seen_slugs:
            continue  # published 우선
        try:
            ep = json.loads(row["enriched_payload"])
        except (json.JSONDecodeError, TypeError):
            continue
        body_md = ep.get("body_md")
        if not body_md or not ep.get("title"):
            continue  # 본문/메타 없는 draft(dry_run 등)는 미리보기 제외
        pages.append(
            _article_page_ctx(
                slug=slug,
                title=ep["title"],
                summary=ep.get("summary") or "",
                meta_description=ep.get("meta_description") or "",
                schema_raw=ep.get("schema_jsonld"),
                body_html=article_writer.render_body_html(body_md),
                persona_slug=row["persona_slug"],
                persona_title=row["persona_title"],
                season_peak=row["season_peak"],
                budget_min=row["budget_min_krw"],
                budget_max=row["budget_max_krw"],
                products=_article_product_cards(
                    _draft_product_rows(conn, ep.get("products") or [])
                ),
                is_draft=True,
                structured=ep,  # quick_verdict·checkpoints·budget_tiers (LLM Tier 2-A·있으면)
            )
        )
        seen_slugs.add(slug)
    return pages


def _draft_product_rows(conn: sqlite3.Connection, featured: list[dict]) -> list:
    """featured(enriched_payload['products']) → products 테이블 행 (이미지·가격·링크).

    promote의 link_article_products와 동일하게 (source_product_id[, source])로 products를 조회 —
    발행 후 article_products 경로와 같은 데이터(같은 화면). products에 없는 항목은 건너뜀.
    """
    rows: list = []
    for f in featured:
        spid = f.get("source_product_id")
        if not spid:
            continue
        src = f.get("source")
        if src:
            pr = conn.execute(
                "SELECT name, price_krw, deeplink_slug, category_path, image_url_external, "
                "source, original_price_krw, discount_pct, sales_volume "
                "FROM products WHERE source_product_id = ? AND source = ? LIMIT 1",
                (str(spid), str(src)),
            ).fetchone()
        else:
            pr = conn.execute(
                "SELECT name, price_krw, deeplink_slug, category_path, image_url_external, "
                "source, original_price_krw, discount_pct, sales_volume "
                "FROM products WHERE source_product_id = ? LIMIT 1",
                (str(spid),),
            ).fetchone()
        if pr is not None:
            rows.append(pr)
    return rows


# 대분류(그룹) 메타 — 카테고리 인덱스 섹션 헤더용(아이콘·한 줄 설명). 세션 #31 분류 체계.
GROUP_META: dict[str, dict] = {
    "homeoffice": {"icon": "💻", "desc": "책상 위 작업 환경"},
    "kitchen": {"icon": "🍳", "desc": "자취 주방 필수템"},
    "living": {"icon": "🧺", "desc": "원룸 일상 정리"},
}

# 카테고리 내 '타입(소분류)' 도출 규칙 — 제품명 키워드로 분류(파생·투명, DB 스키마 무변경).
# CATEGORY_PAGE §2-2(의자=사무용·게이밍·안장형) + Baymard(종류는 카테고리 아닌 '필터')·세션 #31.
# 규칙 없는 카테고리는 타입 미표시(단일). 첫 매칭 우선, 미매칭은 DEFAULT.
CATEGORY_TYPE_RULES: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "office-chair": [
        ("게이밍", ("게이밍", "게임", "레이싱", "레이서", "gaming", "racing")),
        ("안장형", ("안장", "무릎", "saddle", "kneeling")),
    ],
    "desk": [
        ("스탠딩", ("스탠딩", "전동", "모션", "높이조절", "높이 조절", "standing")),
        ("접이식", ("접이", "폴딩", "folding")),
    ],
    "drying-rack": [
        ("스탠드형", ("스탠드", "타워", "수직")),
        ("미니", ("미니", "소형", "mini")),
    ],
}
CATEGORY_TYPE_DEFAULT: dict[str, str] = {
    "office-chair": "사무용",
    "desk": "일반",
    "drying-rack": "일반형",
}


def _derive_type(cat_slug: str, name: str) -> str:
    """제품명 → 카테고리 내 타입(소분류). 규칙 없는 카테고리는 빈 문자열(타입 미사용)."""
    rules = CATEGORY_TYPE_RULES.get(cat_slug)
    if not rules:
        return ""
    n = name or ""
    for label, kws in rules:
        if any(k in n for k in kws):
            return label
    return CATEGORY_TYPE_DEFAULT.get(cat_slug, "")


CATEGORY_CATALOG_SQL = """
    SELECT p.name, p.price_krw, p.original_price_krw, p.discount_pct, p.sales_volume,
           p.image_url_external, p.deeplink_slug, p.source, cp.tier, cp.display_order
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ?
    ORDER BY CASE cp.tier WHEN 'budget' THEN 0 WHEN 'premium' THEN 1 ELSE 2 END,
             cp.display_order, p.id
"""

_TIER_LABEL = {"budget": "💰 실속", "premium": "⭐ 고급"}


def _catalog_item(row: sqlite3.Row, cat_slug: str = "") -> dict:
    """category_products⋈products 행 → 카탈로그 카드 컨텍스트.

    부풀린 할인(>70%)·정가 없는 경우는 product_filter.trusted_discount가 걸러 '단일가'로
    표시(정가·할인율 미노출 — 공정위 가격표시 정확성, §0). 가짜 점수·평점은 두지 않는다.
    type = 제품명 기반 타입(소분류·필터용, 세션 #31). source = 쿠팡/알리(운영자추천 zone 분리).
    """
    disc = product_filter.trusted_discount(row["discount_pct"])
    orig = row["original_price_krw"]
    show = disc is not None and bool(orig)
    tier = row["tier"] or "budget"
    src = row["source"] if "source" in row.keys() else ""
    return {
        "tier": tier,
        "tier_label": _TIER_LABEL.get(tier, "💰 실속"),
        "type": _derive_type(cat_slug, row["name"]),  # 소분류(사무용/게이밍 등) — 필터 data-type
        "source": src or "",
        "name": clean_product_name(row["name"]),
        "price": _price_krw(row["price_krw"]),
        "orig": _price_krw(orig) if show else "",
        "disc": f"{disc}%" if show else "",
        # 정렬/필터 JS용 숫자값(화면 비노출) — 가격 오름차순·할인율 내림차순 정렬 키
        "price_num": row["price_krw"] or 0,
        "disc_num": disc or 0,
        # 알리 최근 판매량 — 정직 표기("판매처 기준"). 추천 6선 선정 근거(세션 #19)
        "volume": f"{row['sales_volume']:,}" if row["sales_volume"] else "",
        "img_url": row["image_url_external"] or "",
        "url": f"/go/{row['deeplink_slug']}",
        "slug": row["deeplink_slug"],
    }


CATEGORY_PICKS_SQL = """
    SELECT p.name, p.price_krw, p.original_price_krw, p.discount_pct, p.sales_volume,
           p.image_url_external, p.deeplink_slug, p.source, cp.tier,
           cp.pros_json, cp.cons_json, cp.pick_reason, cp.pick_type, cp.display_order
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ? AND cp.is_featured = 1 AND p.source != 'coupang'
    ORDER BY CASE cp.tier WHEN 'budget' THEN 0 WHEN 'premium' THEN 1 ELSE 2 END,
             p.sales_volume DESC, cp.display_order, p.id
"""

# 쿠팡 운영자 추천 zone — 카테고리에 연결된 쿠팡(source=coupang) 제품. 별도 상단 노출(주인 결정 #31).
CATEGORY_COUPANG_SQL = """
    SELECT p.name, p.price_krw, p.original_price_krw, p.discount_pct, p.sales_volume,
           p.image_url_external, p.deeplink_slug, p.source, cp.tier,
           cp.pros_json, cp.cons_json, cp.pick_reason, cp.pick_type, cp.display_order
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ? AND p.source = 'coupang'
    ORDER BY cp.display_order, p.id
"""


def _pick_item(row: sqlite3.Row, cat_slug: str = "") -> dict:
    """추천 6선 카드 컨텍스트 = 카탈로그 카드 + 장점·단점·추천대상·타입."""
    item = _catalog_item(row, cat_slug)
    item["pros"] = json.loads(row["pros_json"]) if row["pros_json"] else []
    item["cons"] = json.loads(row["cons_json"]) if row["cons_json"] else []
    item["reason"] = row["pick_reason"] or ""
    item["type"] = row["pick_type"] or ""
    return item


def _category_coupang_pick(row: sqlite3.Row) -> dict:
    """쿠팡 운영자 추천 픽 (카테고리 상단 별도 zone). pick_card 매크로 호환 — 주인 결정 #31."""
    item = _catalog_item(row)
    item["type"] = "운영자 추천"
    item["coupang"] = True
    item["pros"] = json.loads(row["pros_json"]) if row["pros_json"] else []
    item["cons"] = json.loads(row["cons_json"]) if row["cons_json"] else []
    item["reason"] = row["pick_reason"] or "운영자가 직접 고른 제품"
    return item


_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _md_inline(text: str) -> Markup:
    """카테고리 산문의 인라인 마크다운(**볼드**)을 안전한 HTML로 변환 (세션 #18).

    AI가 생성한 lead·가이드 산문에 남는 raw `**`가 화면에 노출되는 것을 방지한다.
    XSS 방지: 먼저 전체 escape 후 `**` 패턴만 <strong>으로 치환(AI 산문 신뢰 한정).
    Markup 반환 → Jinja autoescape에서 이중 escape 없이 그대로 출력.
    """
    if not text:
        return Markup("")
    # html.escape를 먼저 적용했으므로 ** 치환 결과는 안전 — S704는 의도된 사용
    return Markup(_MD_BOLD_RE.sub(r"<strong>\1</strong>", html.escape(text)))  # noqa: S704


_CIRCLED_RE = re.compile(r"(?=[②③④⑤⑥⑦⑧⑨⑩])")


def _md_mistakes(text: str) -> Markup:
    """흔한 실수 — ①②③ 번호 항목을 단락으로 분리(② 이후 항목 앞에 빈 줄). 세션 #18."""
    if not text:
        return Markup("")
    # _md_inline이 이미 escape한 안전 HTML에 <br>만 추가 — S704는 의도된 사용
    return Markup(_CIRCLED_RE.sub("<br><br>", str(_md_inline(text))))  # noqa: S704


def _load_category_pages(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """제품이 연결된 카테고리만 → 카테고리 페이지 컨텍스트.

    가이드 본문(guide_html)·추천 6선(is_featured)·FAQ가 있으면 포함, 없으면 카탈로그만('준비 중').
    연결 제품 0인 카테고리(미수집)는 빈 페이지 방지를 위해 렌더하지 않음.
    include_drafts=True는 미리보기(검토)용 — draft도 렌더(§2-마). 기본(공개 배포)은 published만.
    """
    # include_drafts=1이면 (1 OR ...)로 전체, 0이면 published만 — 파라미터 바인딩(안전)
    cats = conn.execute(
        "SELECT id, slug, name_ko, intro, group_slug, guide_title, content_json, faq_json, "
        "concept_image, concept_image_alt "
        "FROM categories WHERE (? OR status = 'published') ORDER BY display_order, id",
        (1 if include_drafts else 0,),
    ).fetchall()
    pages: list[dict] = []
    for c in cats:
        prods_all = conn.execute(CATEGORY_CATALOG_SQL, (c["id"],)).fetchall()
        # 쿠팡(운영자 추천)은 카탈로그·티어에서 분리 — 상단 별도 zone(주인 결정 #31)
        prods = [r for r in prods_all if r["source"] != "coupang"]
        coupang_picks = [
            _category_coupang_pick(r)
            for r in conn.execute(CATEGORY_COUPANG_SQL, (c["id"],)).fetchall()
        ]
        if not prods and not coupang_picks:
            continue
        picks = [
            _pick_item(r, c["slug"])
            for r in conn.execute(CATEGORY_PICKS_SQL, (c["id"],)).fetchall()
        ]
        catalog = [_catalog_item(r, c["slug"]) for r in prods]
        # 타입(소분류) 필터 칩 — 카탈로그에 실제 존재하는 타입만(파생·정직, 빈 칩 없음)
        cat_types = list(dict.fromkeys(it["type"] for it in catalog if it["type"]))
        faq = json.loads(c["faq_json"]) if c["faq_json"] else []
        content = json.loads(c["content_json"]) if c["content_json"] else {}
        has_guide = bool(content.get("lead"))

        # 한눈 비교표: cells의 slug → 추천 6선 헤더(이름·타입·가격) 매핑
        pick_map = {p["slug"]: p for p in picks}
        raw_compare = content.get("compare") or {}
        cols: list[dict] = []
        for cell in raw_compare.get("cells") or []:
            p = pick_map.get(cell.get("slug"))
            if p:
                cols.append(
                    {
                        "name": p["name"],
                        "type": p.get("type", ""),
                        "tier": p["tier"],
                        "price": p["price"],
                        # 키 이름 'vals' — Jinja에서 c.values는 dict.values 메서드로 해석되는 함정 회피
                        "vals": cell.get("values", []),
                    }
                )
        compare = {"rows": raw_compare.get("rows") or [], "cols": cols}

        # 같은 그룹의 다른 카테고리 — 하단 크로스링크 배너(연관 추천·내부링크·SEO)
        related = [
            {
                "name": r["name_ko"],
                "intro": r["intro"] or "",
                "url": f"/categories/{r['slug']}/",
                "available": r["pc"] > 0,  # 연결 제품 있으면 클릭, 없으면 '준비 중'
            }
            for r in conn.execute(
                "SELECT slug, name_ko, intro, "
                "(SELECT COUNT(*) FROM category_products WHERE category_id = categories.id) AS pc "
                "FROM categories WHERE group_slug = ? AND id != ? "
                "AND (? OR status = 'published') ORDER BY display_order, id",
                (c["group_slug"], c["id"], 1 if include_drafts else 0),
            ).fetchall()
        ]

        # 데이터 요약(Information Gain·세션 #24 T2) — 우리가 수집한 실데이터에서 도출(가짜 없음).
        # "데이터 기반 비교" 포지셔닝을 상단에 전면화 → 2025.12 어필리 패널티(얇은 콘텐츠) 회피.
        prices = [r["price_krw"] for r in prods if r["price_krw"]]
        vols = [((r["sales_volume"] or 0), r["name"]) for r in prods]
        top_vol, top_name = max(vols, key=lambda x: x[0]) if vols else (0, "")
        collected_row = conn.execute(
            "SELECT MAX(p.last_seen_at) FROM category_products cp "
            "JOIN products p ON p.id = cp.product_id WHERE cp.category_id = ?",
            (c["id"],),
        ).fetchone()
        collected = (collected_row[0] or "")[:10]  # YYYY-MM-DD (데이터 수집일·신뢰 신호)
        data_summary = {
            "count": len(prods),
            "collected": collected,
            "price_range": (
                f"{_price_krw(min(prices))} ~ {_price_krw(max(prices))}" if prices else ""
            ),
            "top_name": (
                (top_name[:28] + "…" if len(top_name) > 28 else top_name) if top_vol > 0 else ""
            ),
            "top_volume": f"{top_vol:,}" if top_vol > 0 else "",
        }

        # 필러 백링크 — 같은 그룹에 필러 허브가 있으면 카테고리→필러 역링크(허브-스포크 완성, 세션 #24)
        pillar_link = (
            {"url": f"/{PILLAR_HOME_OFFICE['slug']}/", "title": PILLAR_HOME_OFFICE["title"]}
            if c["group_slug"] == PILLAR_HOME_OFFICE["group_slug"]
            else None
        )
        pages.append(
            {
                "slug": c["slug"],
                "data_summary": data_summary,
                "pillar_link": pillar_link,
                "category": {
                    "name": c["name_ko"],
                    "intro": c["intro"] or "",
                    "guide_title": c["guide_title"] or "",
                    "has_guide": has_guide,
                    "lead": _md_inline(content.get("lead", "")),
                    "guide_intro": _md_inline(content.get("guide_intro", "")),
                    "type_table": [
                        {
                            "type": t.get("type", ""),
                            "trait": _md_inline(t.get("trait", "")),
                            "for": _md_inline(t.get("for", "")),
                        }
                        for t in content.get("type_table", [])
                    ],
                    "checkpoints": [
                        {"title": cp.get("title", ""), "why": _md_inline(cp.get("why", ""))}
                        for cp in content.get("checkpoints", [])
                    ],
                    "mistakes": _md_mistakes(content.get("mistakes", "")),
                    "faq": [{"q": f.get("q", ""), "a": _md_inline(f.get("a", ""))} for f in faq],
                    "concept_image": c["concept_image"] or "",
                    "concept_image_alt": c["concept_image_alt"] or "",
                },
                "products": catalog,
                "catalog_types": cat_types,
                "coupang_picks": coupang_picks,
                "has_coupang": bool(coupang_picks),
                "picks_budget": [p for p in picks if p["tier"] == "budget"],
                "picks_premium": [p for p in picks if p["tier"] == "premium"],
                "has_picks": bool(picks),
                "compare": compare,
                "has_compare": bool(compare["rows"] and compare["cols"]),
                "related": related,
            }
        )
    return pages


def _load_categories_index(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """카테고리 인덱스 — 그룹별 카드 목록. available = 연결 제품 ≥ 1.

    include_drafts=True는 미리보기(검토)용 — draft도 포함(§2-마). 기본은 published만.
    """
    rows = conn.execute(
        "SELECT id, slug, name_ko, intro, group_slug, group_name_ko, concept_image FROM categories "
        "WHERE (? OR status = 'published') ORDER BY display_order, id",
        (1 if include_drafts else 0,),
    ).fetchall()
    groups: list[dict] = []
    for c in rows:
        # 카탈로그 제품(쿠팡 제외) 이름 → 개수 + 타입(소분류) 칩 도출(파생·정직, 세션 #31)
        names = conn.execute(
            "SELECT p.name FROM category_products cp JOIN products p ON p.id = cp.product_id "
            "WHERE cp.category_id = ? AND p.source != 'coupang'",
            (c["id"],),
        ).fetchall()
        count = len(names)
        types = list(
            dict.fromkeys(t for t in (_derive_type(c["slug"], r["name"]) for r in names) if t)
        )
        item = {
            "slug": c["slug"],
            "name": c["name_ko"],
            "intro": c["intro"] or "",
            "count": count,
            "available": count > 0,
            "url": f"/categories/{c['slug']}/",
            "thumb": c["concept_image"] or "",  # 대표 썸네일(개념 이미지)
            "types": types,  # 소분류 칩
        }
        gname = c["group_name_ko"] or "기타"
        grp = next((g for g in groups if g["name"] == gname), None)
        if grp is None:
            meta = GROUP_META.get(c["group_slug"] or "", {})
            # 키 이름은 'cards' — Jinja에서 group.items는 dict.items 메서드로 해석되는 함정 회피
            grp = {
                "name": gname,
                "icon": meta.get("icon", "📦"),
                "desc": meta.get("desc", ""),
                "total": 0,
                "cards": [],
            }
            groups.append(grp)
        grp["cards"].append(item)
        grp["total"] += count
    return groups


def _load_home_categories(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """홈 카테고리 그리드용 — 공개(또는 미리보기 시 draft 포함) 카테고리 카드.

    카테고리 인덱스와 달리 홈은 라인업을 보여주는 자리라 제품 0개도 '준비 중'으로 노출.
    concept_image를 포함해 시각적 카드로 렌더한다(세션 #20 홈 카테고리화).
    """
    rows = conn.execute(
        "SELECT id, slug, name_ko, intro, concept_image, concept_image_alt FROM categories "
        "WHERE (? OR status = 'published') ORDER BY display_order, id",
        (1 if include_drafts else 0,),
    ).fetchall()
    cats: list[dict] = []
    for c in rows:
        count = conn.execute(
            "SELECT COUNT(*) FROM category_products WHERE category_id = ?", (c["id"],)
        ).fetchone()[0]
        cats.append(
            {
                "slug": c["slug"],
                "name": c["name_ko"],
                "intro": c["intro"] or "",
                "count": count,
                "available": count > 0,
                "url": f"/categories/{c['slug']}/",
                "concept_image": c["concept_image"] or "",
                "concept_image_alt": c["concept_image_alt"] or c["name_ko"],
            }
        )
    return cats


# 홈 기획전 배너 (A) — 큰 키비주얼 캐러셀. 운영자 편집 대상, 실제 내용만 노출(가짜 세일 금지, §0).
# image는 static 기준 상대경로. 알리 세일 등 기간 한정 기획전은 운영자가 슬라이드 추가/삭제.
HOME_BANNERS: list[dict] = [
    {
        "eyebrow": "NEW",
        "title": "새 카테고리 4종, 지금 열었어요",
        "sub": "노트북거치대·컴퓨터책상·모니터암·모니터받침대 — 판매량·정가·할인 기준으로 비교했어요.",
        "href": "/categories/",
        "cta": "카테고리 보기",
        "image": "images/concepts/monitor-arm.webp",
    },
    {
        "eyebrow": "정직 비교",
        "title": "가짜 평점 없이, 기준으로 고릅니다",
        "sub": "알리 판매량과 정가·할인율로만 추천합니다. 별점·후기를 지어내지 않아요.",
        "href": "/about/",
        "cta": "운영 원칙 보기",
        "image": "images/concepts/desk.webp",
    },
]

# 홈 테마 큐레이션 (E) — 상황·테마 기반 정직 묶음(인구통계 데이터 주장 아님, §0).
# 각 테마는 카테고리별 1순위(판매량 기준 추천)를 모아 '세팅'으로 제안. 품목이 늘면 테마 추가.
HOME_THEMES: list[dict] = [
    {
        "title": "재택 홈오피스 책상 세팅",
        "desc": "오래 앉아 일하는 책상 위 — 자세와 공간을 한 번에 정리하는 조합.",
        "categories": ["desk", "monitor-arm", "monitor-stand", "laptop-stand"],
    },
]

# 단건 추천 리뷰 페이지(/reviews/<slug>/) — 운영자 큐레이션 상수(HOME_BANNERS와 동일 성격).
# 쿠팡 파트너스 승인용 + 첫 쿠팡 추천. collector.coupang 구현(Phase 4) 전까지의 정식 interim:
# DB 파이프라인이 아니라 운영자가 직접 큐레이션하므로 가짜 후기 금지(§0) — 사실·정보 위주로 기술.
# review.html이 noindex + sitemap 제외(소프트 공개) — 알리+쿠팡 배치 설계(TODO) 합의 후 정식 노출 전환.
REVIEW_PAGES: list[dict] = [
    {
        "slug": "honplanet-monitor-arm",
        "crumb": "흠플래닛 모니터암",
        "title": "흠플래닛 싱글 모니터암 — 책상 위를 비우는 가장 쉬운 방법",
        "name": "흠플래닛 싱글 모니터암, 블랙, 1세트",
        "price": "20,990원",
        "orig": "33,400원",
        "discount": "37%",
        "note": "책상 가장자리에 고정하는 클램프형 싱글(모니터 1대) 모니터암 · 로켓배송",
        "coupang_link": "https://link.coupang.com/a/ehtwmQRZAG",
        # 제휴 링크를 글자로도 노출(쿠팡 승인 심사 — 파트너스 링크 가시성). https:// 제외 표기.
        "coupang_link_display": "link.coupang.com/a/ehtwmQRZAG",
        # 히어로 = 모니터암 개념 이미지(우리 AI 일러스트·비용 0). 쿠팡 상품 이미지는 직접 다운로드
        # 금지(저작권 회색지대, CLAUDE.md 함정 #3)이고 공식 iframe 위젯은 추적차단 브라우저에서
        # 미표시되어, 항상 보이는 자체 개념 이미지를 헤더로 사용(실제 제품 아님을 캡션 명시).
        "hero_image": "/images/concepts/monitor-arm.webp",
        "hero_alt": "모니터암으로 띄운 모니터들이 놓인 깔끔한 홈오피스 책상 (개념 이미지)",
        "hero_caption": "▲ 모니터암을 적용한 홈오피스 책상 예시 — 혼살림 개념 이미지(실제 제품과 다를 수 있어요)",
        "lead": (
            "모니터를 책상에서 띄우면 그 아래 공간이 통째로 살아납니다. 좁은 원룸 책상, "
            "재택 홈오피스에서 모니터암 하나로 자세와 공간을 한 번에 정리하는 방법을 정리했습니다."
        ),
        "body": [
            {
                "h": "모니터암, 왜 쓸까",
                "p": [
                    "모니터암은 모니터를 책상 위에 직접 올려두는 대신 팔(arm)로 띄워 잡아주는 거치대입니다. "
                    "가장 큰 차이는 책상 위 공간입니다. 모니터 발이 차지하던 자리가 사라져 키보드·서류·간단한 "
                    "작업 공간이 그대로 넓어집니다.",
                ],
                "ul": [
                    "높이·거리·각도를 자유롭게 조절해 눈높이를 맞추기 쉽습니다 — 장시간 작업 시 목·어깨 부담을 줄이는 데 도움이 됩니다.",
                    "모니터 받침대(고정 높이)보다 조절 범위가 넓어, 앉은키나 책상 높이가 제각각인 1인 가구에 유연합니다.",
                    "모니터를 옆으로 밀거나 돌릴 수 있어, 책상을 작업·식사 등 다른 용도로 전환하기 편합니다.",
                ],
            },
            {
                "h": "이 제품은 어떤가요",
                "p": [
                    "흠플래닛 싱글 모니터암은 모니터 1대를 책상 가장자리에 클램프(집게)로 고정해 쓰는 가장 일반적인 "
                    "형태입니다. 작성 시점 기준 정가 33,400원에서 37% 내린 20,990원이며, 로켓배송으로 빠르게 받을 수 있습니다.",
                    "다만 모니터암은 내 모니터와의 호환이 중요합니다. 아래 항목은 구매 전 쿠팡 상품 페이지에서 "
                    "본인 모니터 사양과 직접 대조해 확인하시길 권합니다.",
                ],
                "ul": [
                    "VESA 규격(모니터 뒷면 나사 간격) 지원 여부와 크기",
                    "지원 모니터 무게(내하중)와 화면 크기 범위",
                    "책상 두께가 클램프 고정 범위 안에 드는지",
                ],
            },
            {
                "h": "이런 분께 맞습니다",
                "ul": [
                    "재택·홈오피스로 모니터 1대를 오래 들여다보는 분",
                    "책상이 좁아 모니터 받침대만으로는 공간이 부족한 분",
                    "모니터 높이·거리를 상황에 따라 자주 바꾸고 싶은 분",
                ],
            },
        ],
    }
]

HOME_CROSS_SQL = """
    SELECT p.id, p.name, p.price_krw, p.original_price_krw, p.discount_pct, p.sales_volume,
           p.image_url_external, p.deeplink_slug, cp.tier,
           ca.name_ko AS cat_name, ca.slug AS cat_slug
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    JOIN categories ca ON ca.id = cp.category_id
    WHERE (? OR ca.status = 'published')
"""


def _home_product_item(row: sqlite3.Row) -> dict:
    """홈 BEST·딜·테마 공용 제품 카드 컨텍스트 (카테고리명 포함)."""
    disc = product_filter.trusted_discount(row["discount_pct"])
    orig = row["original_price_krw"]
    show = disc is not None and bool(orig)
    return {
        "name": row["name"],
        "cat_name": row["cat_name"],
        "cat_url": f"/categories/{row['cat_slug']}/",
        "price": _price_krw(row["price_krw"]),
        "orig": _price_krw(orig) if show else "",
        "disc": f"{disc}%" if show else "",
        "disc_num": disc or 0,
        "volume": f"{row['sales_volume']:,}" if row["sales_volume"] else "",
        "img_url": row["image_url_external"] or "",
        "url": f"/go/{row['deeplink_slug']}",
    }


def _load_home_best(
    conn: sqlite3.Connection, include_drafts: bool = False, limit: int = 8
) -> list[dict]:
    """판매량 BEST (C) — 공개 카테고리 제품 중 알리 최근 판매량 상위. 실데이터·정직 표기."""
    rows = conn.execute(
        HOME_CROSS_SQL
        + " AND COALESCE(p.sales_volume,0) > 0 ORDER BY COALESCE(p.sales_volume,0) DESC, p.id",
        (1 if include_drafts else 0,),
    ).fetchall()
    seen: set = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(_home_product_item(r))
        if len(out) >= limit:
            break
    return out


def _load_home_deals(
    conn: sqlite3.Connection, include_drafts: bool = False, limit: int = 8
) -> list[dict]:
    """오늘의딜/할인 BEST (D) — 신뢰 가능한 할인율(부풀림 제외) 높은 순. 수집시점 기준."""
    rows = conn.execute(HOME_CROSS_SQL + " ORDER BY p.id", (1 if include_drafts else 0,)).fetchall()
    seen: set = set()
    scored: list[tuple] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        disc = product_filter.trusted_discount(r["discount_pct"])
        if disc and r["original_price_krw"]:
            scored.append((disc, _home_product_item(r)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:limit]]


def _load_home_themes(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """테마 큐레이션 (E) — 테마별 카테고리 1순위 묶음. 최소 2품목 모여야 노출."""
    out: list[dict] = []
    for th in HOME_THEMES:
        items: list[dict] = []
        for slug in th["categories"]:
            row = conn.execute(
                HOME_CROSS_SQL + " AND ca.slug = ? AND cp.is_featured = 1 "
                "ORDER BY COALESCE(p.sales_volume,0) DESC, cp.display_order LIMIT 1",
                (1 if include_drafts else 0, slug),
            ).fetchone()
            if row:
                items.append(_home_product_item(row))
        if len(items) >= 2:
            # 키 이름 'picks' — Jinja에서 t.items는 dict.items 메서드로 해석되는 함정 회피
            out.append({"title": th["title"], "desc": th["desc"], "picks": items})
    return out


def _load_guides(conn: sqlite3.Connection, include_drafts: bool = False) -> list[dict]:
    """구매가이드 인덱스 (/guides/) — 가이드 본문이 있는 카테고리의 '고르는 법' 모음.

    가이드는 카테고리 페이지 상단에 렌더되므로 링크는 해당 카테고리 페이지로 보낸다.
    content_json.lead가 있어야(=가이드 생성됨) 노출(세션 #20, 깨진 /guides/ 링크 해소).
    """
    rows = conn.execute(
        "SELECT slug, name_ko, intro, guide_title, content_json, concept_image, concept_image_alt "
        "FROM categories WHERE (? OR status = 'published') ORDER BY display_order, id",
        (1 if include_drafts else 0,),
    ).fetchall()
    out: list[dict] = []
    for c in rows:
        content = json.loads(c["content_json"]) if c["content_json"] else {}
        if not content.get("lead"):  # 가이드 본문 있는 카테고리만
            continue
        out.append(
            {
                "title": c["guide_title"] or f"{c['name_ko']} 고르는 법",
                "name": c["name_ko"],
                "intro": c["intro"] or "",
                "url": f"/categories/{c['slug']}/",
                "concept_image": c["concept_image"] or "",
                "concept_image_alt": c["concept_image_alt"] or c["name_ko"],
            }
        )
    return out


# 홈오피스 필러(허브) — 토픽 클러스터 hub (세션 #24 T2). 운영자 큐레이션(갖추는 순서·예산) +
# 동적 스포크(DB의 homeoffice 그룹 공개 카테고리). 단순 링크모음이 아닌 '진짜 가치'(순서·예산·데이터)로
# 얇은 콘텐츠 패널티 회피 + 토픽 권위 엔진. 살림 그룹은 클러스터가 얇아 보류(클러스터 충분해지면 추가).
PILLAR_HOME_OFFICE: dict = {
    "slug": "home-office",
    "group_slug": "homeoffice",
    "title": "재택 홈오피스 책상 환경 완전 가이드",
    "lead": (
        "재택·1인 작업실, 무엇부터 어떤 순서로 갖춰야 할까요? 예산이 빠듯할수록 "
        "순서가 중요합니다. 오래 앉아 일하는 책상 위를, 자세와 공간을 함께 정리하는 길을 정리했어요."
    ),
    "steps": [
        {
            "n": "1",
            "title": "의자 — 가장 먼저",
            "cat": "office-chair",
            "why": "하루 8시간 앉는다면 허리·목·자세에 가장 큰 영향을 줍니다. 예산이 빠듯해도 의자부터 챙기세요.",
        },
        {
            "n": "2",
            "title": "책상 — 공간의 기준",
            "cat": "desk",
            "why": "방 크기와 작업에 맞는 크기·높이를 고릅니다. 의자와의 높이 궁합이 자세를 좌우합니다.",
        },
        {
            "n": "3",
            "title": "모니터 높이 — 눈높이·목",
            "cat": "monitor-arm",
            "cat2": "monitor-stand",
            "why": "모니터를 눈높이로 올리면 목 부담이 줄어요. 책상이 좁거나 자주 위치를 바꾸면 모니터암, 단순하게는 받침대.",
        },
    ],
    "budgets": [
        {
            "tier": "💰 실속",
            "range": "~30만원",
            "desc": "기본 의자 + 접이식·소형 책상 + 모니터 받침대. 시작에 충분.",
        },
        {
            "tier": "🪑 표준",
            "range": "30~70만원",
            "desc": "인체공학 의자 + 적당한 책상 + 모니터암. 오래 앉아도 편한 조합.",
        },
        {
            "tier": "⭐ 본격",
            "range": "70만원+",
            "desc": "고급 의자 + 넓은 책상 + 듀얼 모니터암. 본격 1인 작업실.",
        },
    ],
}


def _load_pillar_spokes(
    conn: sqlite3.Connection, group_slug: str, include_drafts: bool = False
) -> tuple[list[dict], int]:
    """필러 스포크 — 해당 그룹의 (공개) 카테고리 + 제품 수. 토픽 클러스터 허브-스포크 링크."""
    rows = conn.execute(
        "SELECT slug, name_ko, intro, concept_image, concept_image_alt, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id = categories.id) AS pc "
        "FROM categories WHERE group_slug = ? AND (? OR status = 'published') "
        "ORDER BY display_order, id",
        (group_slug, 1 if include_drafts else 0),
    ).fetchall()
    spokes = [
        {
            "slug": r["slug"],
            "name": r["name_ko"],
            "intro": r["intro"] or "",
            "url": f"/categories/{r['slug']}/",
            "count": r["pc"],
            "available": r["pc"] > 0,
            "concept_image": r["concept_image"] or "",
            "concept_image_alt": r["concept_image_alt"] or r["name_ko"],
        }
        for r in rows
    ]
    total = sum(s["count"] for s in spokes)
    return spokes, total


def _sitemap(urls: list[str]) -> str:
    items = "\n".join(f"  <url><loc>{SITE_ORIGIN}{u}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n</urlset>\n"
    )


def _asset_version() -> str:
    """static CSS·JS 내용 해시(8자) — cache-busting 버전 (세션 #21).

    파일이 바뀌면 값이 달라져 링크 URL(?v=)이 바뀌므로, immutable 장기 캐시여도 브라우저·
    엣지가 새 자산을 받는다. CSS/JS 변경이 방문자에게 반영 안 되던 근본 문제 해결(흰바탕
    디자인이 옛 우드톤 캐시에 막히던 현상). 내용 불변이면 값도 동일 → 캐시 이점 유지.
    """
    h = hashlib.sha256()
    for rel in (
        "css/tokens.css",
        "css/components.css",
        "css/pages.css",
        "css/category.css",
        "css/article.css",
        "js/home.js",
        "js/category.js",
        "js/hub-filter.js",
    ):
        p = STATIC_DIR / rel
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:8]


def render_site(
    out_dir: Path = DEFAULT_OUT, db_path: Path = db.DB_PATH, include_drafts: bool = False
) -> dict:
    """DB → 정적 사이트 렌더. 반환: 빌드 요약 dict.

    include_drafts=True는 미리보기(검토)용 — 미승인 draft 카테고리도 렌더(§2-마).
    공개 배포(build/site)는 기본값(published만) 사용.
    """
    conn = db.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        scenarios = _load_scenarios(conn)
        personas = _load_personas(conn)
        article_pages = _load_article_pages(conn, include_drafts)
        category_pages = _load_category_pages(conn, include_drafts)
        category_groups = _load_categories_index(conn, include_drafts)
        home_categories = _load_home_categories(conn, include_drafts)
        home_best = _load_home_best(conn, include_drafts)
        home_deals = _load_home_deals(conn, include_drafts)
        home_themes = _load_home_themes(conn, include_drafts)
        guides = _load_guides(conn, include_drafts)
        pillar_spokes, pillar_total = _load_pillar_spokes(
            conn, PILLAR_HOME_OFFICE["group_slug"], include_drafts
        )
    finally:
        conn.close()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # cache-busting: 모든 템플릿에서 {{ asset_version }} 사용 (CSS·JS URL ?v=)
    env.globals["asset_version"] = _asset_version()
    # eager_images: 미리보기(검토)는 즉시 로딩 — 운영자가 전체페이지 스크린샷·스크롤 없이도
    # 모든 상품 이미지를 한 번에 확인(세션 #20 재발방지: lazy+전체스크린샷 → 화면 밖 이미지 미로드 오인).
    # 공개 배포는 lazy 유지(외부 이미지 40+ 다발 요청 방지·CWV/LCP 보호).
    common = {
        "asset_base": "/static",
        "personas": personas,
        "business_info": BUSINESS_INFO,
        "eager_images": include_drafts,
    }
    org_ld = jsonld.build_organization_jsonld(SITE_ORIGIN, "혼살림", BUSINESS_INFO["email"])

    # 산출물 청소 후 재생성 — 미게시·삭제된 콘텐츠가 배포물(라이브)에 잔존하지 않도록(세션 #20).
    # 정적 사이트는 DB 현재 상태와 정확히 일치해야 한다(예: 글 unpublish/삭제 → 라이브에서도 제거).
    # 안전장치: 빌드 산출물 디렉토리(site/preview)만 청소 — 저장소 루트 등 오삭제 방지.
    if out_dir.exists() and out_dir.name in ("site", "preview"):
        # 디렉토리 자체가 아니라 '내용물'만 제거 — 실행 중인 미리보기 서버가 out_dir을
        # cwd로 점유해도 안전(Windows WinError 32 회피). 정적 사이트는 DB 상태와 정확히 일치.
        for child in out_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def w(rel: str, html: str) -> None:
        page = out_dir / rel
        page.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" — Windows에서도 LF로 통일 (배포 산출물 CRLF churn 방지)
        page.write_text(html, encoding="utf-8", newline="\n")
        written.append(rel)

    # 홈 (상위 우선순위 6개)
    w(
        "index.html",
        env.get_template("home.html").render(
            active_nav="home",
            canonical_url=f"{SITE_ORIGIN}/",
            meta_title="혼살림 — 혼자 살림을 따뜻하게 시작하는 가이드",
            meta_description=SITE_DESC,
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_website_jsonld(SITE_ORIGIN, "혼살림"),
                    org_ld,
                ]
            ),
            featured_scenarios=scenarios[:6],
            season_calendar=SEASON_CALENDAR,
            home_categories=home_categories,
            home_banners=HOME_BANNERS,
            home_best=home_best,
            home_deals=home_deals,
            home_themes=home_themes,
            **common,
        ),
    )

    # 시나리오 허브
    season_filters = [
        {"value": v, "icon": ""}
        for v in dict.fromkeys(s["season"] for s in scenarios if s["season"])
    ]
    w(
        "scenarios/index.html",
        env.get_template("scenario_list.html").render(
            active_nav="hub",
            canonical_url=f"{SITE_ORIGIN}/scenarios/",
            meta_title="내맘대로 세팅 | 혼살림",
            meta_description="라이프스타일·예산·시즌으로 좁혀 내 상황에 맞는 1인 가구 살림 추천을 찾아보세요.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "내맘대로 세팅"}], SITE_ORIGIN
                    ),
                    org_ld,
                ]
            ),
            scenarios=scenarios,
            budget_filters=BUDGET_FILTERS,
            season_filters=season_filters,
            **common,
        ),
    )

    # 페르소나 허브 (전체 + 개별)
    persona_tmpl = env.get_template("persona_hub.html")
    for i, p in enumerate(personas):
        pcards = [s for s in scenarios if s["persona"] == p["id"]]
        html = persona_tmpl.render(
            active_nav="persona",
            canonical_url=f"{SITE_ORIGIN}/personas/{p['id']}/",
            meta_title=f"{p['name']} | 혼살림 라이프스타일",
            meta_description=p["line"],
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [
                            {"name": "홈", "url": "/"},
                            {"name": "라이프스타일", "url": "/personas/"},
                            {"name": p["name"]},
                        ],
                        SITE_ORIGIN,
                    ),
                    org_ld,
                ]
            ),
            persona=p,
            scenarios=pcards,
            **common,
        )
        w(f"personas/{p['id']}/index.html", html)
        if i == 0:
            w("personas/index.html", html)

    # About
    w(
        "about/index.html",
        env.get_template("about.html").render(
            active_nav="about",
            canonical_url=f"{SITE_ORIGIN}/about/",
            meta_title="About | 혼살림",
            meta_description="혼살림은 1인 가구의 살림을 상황별로 정리해 추천합니다. 운영 원칙과 신뢰·고지 정책을 투명하게 공개합니다.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "About"}], SITE_ORIGIN
                    ),
                    org_ld,
                ]
            ),
            **common,
        ),
    )

    # 추천 방법(방법론) — E-E-A-T·신뢰 신호(데이터 기반 비교 명문화, 세션 #24 T2)
    w(
        "method/index.html",
        env.get_template("method.html").render(
            active_nav="",
            canonical_url=f"{SITE_ORIGIN}/method/",
            meta_title="혼살림은 이렇게 고릅니다 — 추천 방법·기준",
            meta_description="혼살림은 광고가 아니라 실제 판매 데이터와 기준으로 1인 가구·홈오피스 제품을 비교합니다. 가짜 평점 없이, 투명하게.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "추천 방법"}], SITE_ORIGIN
                    ),
                    org_ld,
                ]
            ),
            **common,
        ),
    )

    # 홈오피스 필러(허브) — 토픽 클러스터 hub (세션 #24 T2). 공개 스포크가 있을 때만 렌더.
    pillar_rendered = any(s["available"] for s in pillar_spokes)
    if pillar_rendered:
        po = PILLAR_HOME_OFFICE
        w(
            f"{po['slug']}/index.html",
            env.get_template("pillar.html").render(
                active_nav="",
                canonical_url=f"{SITE_ORIGIN}/{po['slug']}/",
                meta_title=f"{po['title']} | 혼살림",
                meta_description=po["lead"][:150],
                schema_jsonld=jsonld.as_script_tags(
                    [
                        jsonld.build_breadcrumb_jsonld(
                            [{"name": "홈", "url": "/"}, {"name": po["title"]}], SITE_ORIGIN
                        ),
                        org_ld,
                    ]
                ),
                pillar=po,
                spokes=pillar_spokes,
                pillar_total=pillar_total,
                **common,
            ),
        )

    # 404
    w("404.html", env.get_template("404.html").render(active_nav="", **common))

    # 상세글: published articles → article.html (산문 body_html + /go/ 제휴 상품 카드)
    art_tmpl = env.get_template("article.html")
    for pg in article_pages:
        slug = pg["slug"]
        schema = jsonld.as_script_tags(
            [
                jsonld.build_breadcrumb_jsonld(
                    [
                        {"name": "홈", "url": "/"},
                        {"name": "내맘대로 세팅", "url": "/scenarios/"},
                        {"name": pg["title"]},
                    ],
                    SITE_ORIGIN,
                ),
                pg["schema_raw"],
            ]
        )
        w(
            f"articles/{slug}/index.html",
            art_tmpl.render(
                active_nav="",
                canonical_url=f"{SITE_ORIGIN}/articles/{slug}/",
                meta_title=f"{pg['title']} | 혼살림",
                meta_description=pg["meta_description"],
                schema_jsonld=schema,
                article=pg["article"],
                products=pg["products"],
                coupang_picks=pg["coupang_picks"],
                picks_budget=pg["picks_budget"],
                picks_premium=pg["picks_premium"],
                has_picks=pg["has_picks"],
                compare=pg["compare"],
                has_compare=pg["has_compare"],
                catalog=pg["catalog"],
                has_catalog=pg["has_catalog"],
                art_data_summary=pg["art_data_summary"],
                quick_verdict=pg["quick_verdict"],  # Tier 2 구조화(세션 #34)
                checkpoints=pg["checkpoints"],
                has_checkpoints=pg["has_checkpoints"],
                concept_image=pg["concept_image"],
                concept_image_alt=pg["concept_image_alt"],
                **common,
            ),
        )
    # sitemap·게시수는 published만 — draft 미리보기 글은 제외(공개 색인·카운트 누출 방지, 세션 #29)
    article_slugs = [pg["slug"] for pg in article_pages if not pg.get("is_draft")]

    # 카테고리 인덱스 (/categories/) — 그룹별 카드, 미수집 카테고리는 '준비 중'
    w(
        "categories/index.html",
        env.get_template("categories_index.html").render(
            active_nav="category",
            canonical_url=f"{SITE_ORIGIN}/categories/",
            meta_title="카테고리 | 혼살림",
            meta_description="1인 가구·홈오피스 품목을 카테고리별로 비교하고 골라보세요.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "카테고리"}], SITE_ORIGIN
                    ),
                    org_ld,
                ]
            ),
            groups=category_groups,
            **common,
        ),
    )

    # 구매가이드 인덱스 (/guides/) — 카테고리별 '고르는 법' 모음 (없으면 '준비 중'으로 graceful)
    w(
        "guides/index.html",
        env.get_template("guides_index.html").render(
            active_nav="guide",
            canonical_url=f"{SITE_ORIGIN}/guides/",
            meta_title="구매가이드 | 혼살림",
            meta_description="1인 가구·홈오피스 품목을 무엇을 보고 골라야 하는지 카테고리별로 정리한 구매가이드.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "구매가이드"}], SITE_ORIGIN
                    ),
                    org_ld,
                ]
            ),
            guides=guides,
            **common,
        ),
    )

    # 카테고리 상세 (/categories/<slug>/) — 전체 제품 카탈로그 (점수 없음)
    cat_tmpl = env.get_template("category.html")
    for pg in category_pages:
        cslug = pg["slug"]
        cname = pg["category"]["name"]
        w(
            f"categories/{cslug}/index.html",
            cat_tmpl.render(
                active_nav="category",
                canonical_url=f"{SITE_ORIGIN}/categories/{cslug}/",
                meta_title=f"{cname} 전체 제품 | 혼살림",
                meta_description=pg["category"]["intro"]
                or f"{cname} 전체 제품을 가격·할인·티어로 비교하세요.",
                schema_jsonld=jsonld.as_script_tags(
                    [
                        jsonld.build_breadcrumb_jsonld(
                            [
                                {"name": "홈", "url": "/"},
                                {"name": "카테고리", "url": "/categories/"},
                                {"name": cname},
                            ],
                            SITE_ORIGIN,
                        ),
                        org_ld,
                    ]
                ),
                category=pg["category"],
                data_summary=pg["data_summary"],
                pillar_link=pg["pillar_link"],
                products=pg["products"],
                catalog_types=pg["catalog_types"],
                coupang_picks=pg["coupang_picks"],
                has_coupang=pg["has_coupang"],
                picks_budget=pg["picks_budget"],
                picks_premium=pg["picks_premium"],
                has_picks=pg["has_picks"],
                compare=pg["compare"],
                has_compare=pg["has_compare"],
                related=pg["related"],
                **common,
            ),
        )
    category_slugs = [pg["slug"] for pg in category_pages]

    # 단건 추천 리뷰 (/reviews/<slug>/) — 운영자 큐레이션 상수(REVIEW_PAGES).
    # noindex(review.html) + sitemap 제외(소프트 공개) — 색인·내부링크는 배치 설계 합의 후.
    review_tmpl = env.get_template("review.html")
    for rv in REVIEW_PAGES:
        w(
            f"reviews/{rv['slug']}/index.html",
            review_tmpl.render(
                active_nav="",
                canonical_url=f"{SITE_ORIGIN}/reviews/{rv['slug']}/",
                meta_title=f"{rv['title']} | 혼살림",
                meta_description=rv["lead"][:150],
                review=rv,
                **common,
            ),
        )

    # sitemap.xml
    urls = (
        ["/", "/scenarios/", "/about/", "/method/", "/categories/", "/guides/"]
        + ([f"/{PILLAR_HOME_OFFICE['slug']}/"] if pillar_rendered else [])
        + [f"/categories/{slug}/" for slug in category_slugs]
        + [f"/personas/{p['id']}/" for p in personas]
        + [f"/articles/{slug}/" for slug in article_slugs]
    )
    w("sitemap.xml", _sitemap(urls))

    # robots.txt + _headers (배포 산출물 — 색인 규칙·캐시·보안 헤더)
    w("robots.txt", ROBOTS_TXT)
    w("_headers", HEADERS_FILE)
    # _redirects — 카테고리로 흡수돼 비공개된 글의 라이브 URL 301 이전(세션 #31)
    if REDIRECTS:
        w("_redirects", "".join(f"{src}  {dst}  301\n" for src, dst in REDIRECTS))

    # static 복사
    shutil.copytree(STATIC_DIR, out_dir / "static", dirs_exist_ok=True)

    return {
        "out_dir": str(out_dir),
        "pages": len(written),
        "scenarios": len(scenarios),
        "personas": len(personas),
        "categories": len(category_slugs),
        "articles_published": len(article_slugs),
        "written": written,
    }


if __name__ == "__main__":
    summary = render_site()
    print(f"[OK] 사이트 렌더: {summary['out_dir']}")
    print(
        f"     페이지 {summary['pages']}개 · 시나리오 {summary['scenarios']} · "
        f"페르소나 {summary['personas']} · 게시글 {summary['articles_published']}"
    )
    if summary["articles_published"] == 0:
        print(
            "     [NOTE] 게시 article 0편 — 상세글 미렌더. 시나리오 카드 링크는 콘텐츠 게시 후 활성."
        )
