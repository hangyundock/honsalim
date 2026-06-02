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
           a.schema_jsonld, a.published_at,
           s.season_peak, s.budget_min_krw, s.budget_max_krw,
           p.slug AS persona_slug, p.title_ko AS persona_title
    FROM articles a
    JOIN scenarios s ON s.id = a.scenario_id
    JOIN personas p ON p.id = s.persona_id
    WHERE a.status = 'published'
    ORDER BY a.published_at DESC
"""

ARTICLE_PRODUCTS_SQL = """
    SELECT pr.name, pr.price_krw, pr.deeplink_slug, pr.category_path
    FROM article_products ap
    JOIN products pr ON pr.id = ap.product_id
    WHERE ap.article_id = ?
    ORDER BY ap.display_order, ap.product_id
"""


def _price_krw(value: int | None) -> str:
    return f"{value:,}원" if value else ""


def _load_article_pages(conn: sqlite3.Connection) -> list[dict]:
    """published articles → 상세글 렌더 컨텍스트 (산문 본문 + /go/ 제휴 상품 카드).

    article.html 계약에 맞춘 dict: article(메타·body_html·페르소나/시즌/예산 칩) +
    products(이름·가격·/go/ 링크). 이미지는 우드톤 placeholder(§9 외부 이미지
    저작권 회색지대 회피 — 실제 대표 이미지는 Phase 3 AI 생성).
    """
    rows = conn.execute(ARTICLE_DETAIL_SQL).fetchall()
    pages: list[dict] = []
    for row in rows:
        prods = conn.execute(ARTICLE_PRODUCTS_SQL, (row["id"],)).fetchall()
        products = [
            {
                "name": pr["name"],
                "price": _price_krw(pr["price_krw"]),
                "url": f"/go/{pr['deeplink_slug']}",
                "img": WOOD[i % len(WOOD)],
                "cat": pr["category_path"] or "",
                "tag": "",  # 필수/추천/선택 등급 데이터 없음(v1) — 본문이 설명 담당
                "why": "",  # recommendation_note 미사용(v1)
            }
            for i, pr in enumerate(prods)
        ]
        pages.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "meta_description": row["meta_description"],
                "schema_raw": row["schema_jsonld"],
                "article": {
                    "slug": row["slug"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "desc": row["meta_description"],
                    "body_html": row["body_html"],
                    "persona": row["persona_slug"],
                    "persona_name": row["persona_title"],
                    "persona_icon": PERSONA_ICON.get(row["persona_slug"], ""),
                    "season": row["season_peak"] or "",
                    "budget": _budget_display(row["budget_min_krw"], row["budget_max_krw"]),
                },
                "products": products,
            }
        )
    return pages


CATEGORY_CATALOG_SQL = """
    SELECT p.name, p.price_krw, p.original_price_krw, p.discount_pct, p.sales_volume,
           p.image_url_external, p.deeplink_slug, cp.tier, cp.display_order
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ?
    ORDER BY CASE cp.tier WHEN 'budget' THEN 0 WHEN 'premium' THEN 1 ELSE 2 END,
             cp.display_order, p.id
"""

_TIER_LABEL = {"budget": "💰 실속", "premium": "⭐ 고급"}


def _catalog_item(row: sqlite3.Row) -> dict:
    """category_products⋈products 행 → 카탈로그 카드 컨텍스트.

    부풀린 할인(>70%)·정가 없는 경우는 product_filter.trusted_discount가 걸러 '단일가'로
    표시(정가·할인율 미노출 — 공정위 가격표시 정확성, §0). 가짜 점수·평점은 두지 않는다.
    """
    disc = product_filter.trusted_discount(row["discount_pct"])
    orig = row["original_price_krw"]
    show = disc is not None and bool(orig)
    tier = row["tier"] or "budget"
    return {
        "tier": tier,
        "tier_label": _TIER_LABEL.get(tier, "💰 실속"),
        "name": row["name"],
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
           p.image_url_external, p.deeplink_slug, cp.tier,
           cp.pros_json, cp.cons_json, cp.pick_reason, cp.pick_type, cp.display_order
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ? AND cp.is_featured = 1
    ORDER BY CASE cp.tier WHEN 'budget' THEN 0 WHEN 'premium' THEN 1 ELSE 2 END,
             p.sales_volume DESC, cp.display_order, p.id
"""


def _pick_item(row: sqlite3.Row) -> dict:
    """추천 6선 카드 컨텍스트 = 카탈로그 카드 + 장점·단점·추천대상·타입."""
    item = _catalog_item(row)
    item["pros"] = json.loads(row["pros_json"]) if row["pros_json"] else []
    item["cons"] = json.loads(row["cons_json"]) if row["cons_json"] else []
    item["reason"] = row["pick_reason"] or ""
    item["type"] = row["pick_type"] or ""
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
        prods = conn.execute(CATEGORY_CATALOG_SQL, (c["id"],)).fetchall()
        if not prods:
            continue
        picks = [_pick_item(r) for r in conn.execute(CATEGORY_PICKS_SQL, (c["id"],)).fetchall()]
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

        pages.append(
            {
                "slug": c["slug"],
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
                "products": [_catalog_item(r) for r in prods],
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
        "SELECT id, slug, name_ko, intro, group_name_ko FROM categories "
        "WHERE (? OR status = 'published') ORDER BY display_order, id",
        (1 if include_drafts else 0,),
    ).fetchall()
    groups: list[dict] = []
    for c in rows:
        count = conn.execute(
            "SELECT COUNT(*) FROM category_products WHERE category_id = ?", (c["id"],)
        ).fetchone()[0]
        item = {
            "slug": c["slug"],
            "name": c["name_ko"],
            "intro": c["intro"] or "",
            "count": count,
            "available": count > 0,
            "url": f"/categories/{c['slug']}/",
        }
        gname = c["group_name_ko"] or "기타"
        grp = next((g for g in groups if g["name"] == gname), None)
        if grp is None:
            # 키 이름은 'cards' — Jinja에서 group.items는 dict.items 메서드로 해석되는 함정 회피
            grp = {"name": gname, "cards": []}
            groups.append(grp)
        grp["cards"].append(item)
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
        article_pages = _load_article_pages(conn)
        category_pages = _load_category_pages(conn, include_drafts)
        category_groups = _load_categories_index(conn, include_drafts)
        home_categories = _load_home_categories(conn, include_drafts)
        home_best = _load_home_best(conn, include_drafts)
        home_deals = _load_home_deals(conn, include_drafts)
        home_themes = _load_home_themes(conn, include_drafts)
        guides = _load_guides(conn, include_drafts)
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
                **common,
            ),
        )
    article_slugs = [pg["slug"] for pg in article_pages]

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
                products=pg["products"],
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

    # sitemap.xml
    urls = (
        ["/", "/scenarios/", "/about/", "/categories/", "/guides/"]
        + [f"/categories/{slug}/" for slug in category_slugs]
        + [f"/personas/{p['id']}/" for p in personas]
        + [f"/articles/{slug}/" for slug in article_slugs]
    )
    w("sitemap.xml", _sitemap(urls))

    # robots.txt + _headers (배포 산출물 — 색인 규칙·캐시·보안 헤더)
    w("robots.txt", ROBOTS_TXT)
    w("_headers", HEADERS_FILE)

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
