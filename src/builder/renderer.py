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

import shutil
import sqlite3
import statistics
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from builder import jsonld
from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DEFAULT_OUT = PROJECT_ROOT / "build" / "site"
SITE_ORIGIN = "https://honsalim.com"
SITE_DESC = "1인 가구·자취·홈오피스·일상살림 추천 가이드. 혼자 살림을 따뜻하게 시작하세요."

# robots.txt — /go/ 게이트웨이(제휴 redirect)는 색인 제외, sitemap 안내
ROBOTS_TXT = f"User-agent: *\nAllow: /\nDisallow: /go/\n\nSitemap: {SITE_ORIGIN}/sitemap.xml\n"

# Cloudflare Pages _headers — 정적 자산 장기 캐시 + 기본 보안 헤더 (FRONTEND §9 / POLICY §6)
HEADERS_FILE = (
    "/static/*\n"
    "  Cache-Control: public, max-age=31536000, immutable\n"
    "\n"
    "/*\n"
    "  X-Content-Type-Options: nosniff\n"
    "  Referrer-Policy: strict-origin-when-cross-origin\n"
    "  X-Frame-Options: DENY\n"
)

WOOD = ["var(--wood-1)", "var(--wood-2)", "var(--wood-3)", "var(--wood-4)"]
PERSONA_ICON = {"cheot-jachi": "key", "homeoffice": "laptop", "minimal-life": "plant"}
PERSONA_IMG = {
    "cheot-jachi": "var(--wood-1)",
    "homeoffice": "var(--wood-4)",
    "minimal-life": "var(--wood-2)",
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

# 사업자 정보 — M2 결정(세션 #7)
BUSINESS_INFO = {
    "name": "혼살림",
    "rep": "혼살다 (운영자)",
    "bizno": "등록 진행 중",
    "mailorder": "등록 진행 중",
    "email": "dugihappyending@gmail.com",
    "addr": "등록 진행 중",
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


def _scenario_card(row: sqlite3.Row, idx: int) -> dict:
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
        "img": WOOD[idx % len(WOOD)],
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
    return [_scenario_card(r, i) for i, r in enumerate(rows)]


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


def _sitemap(urls: list[str]) -> str:
    items = "\n".join(f"  <url><loc>{SITE_ORIGIN}{u}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n</urlset>\n"
    )


def render_site(out_dir: Path = DEFAULT_OUT, db_path: Path = db.DB_PATH) -> dict:
    """DB → 정적 사이트 렌더. 반환: 빌드 요약 dict."""
    conn = db.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        scenarios = _load_scenarios(conn)
        personas = _load_personas(conn)
        article_pages = _load_article_pages(conn)
    finally:
        conn.close()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    common = {"asset_base": "/static", "personas": personas, "business_info": BUSINESS_INFO}
    org_ld = jsonld.build_organization_jsonld(SITE_ORIGIN, "혼살림", BUSINESS_INFO["email"])

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
            meta_title="모든 시나리오 | 혼살림",
            meta_description="페르소나·예산·시즌으로 좁혀 내 상황에 맞는 1인 가구 살림 추천을 찾아보세요.",
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [{"name": "홈", "url": "/"}, {"name": "시나리오"}], SITE_ORIGIN
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
            meta_title=f"{p['name']} | 혼살림 페르소나",
            meta_description=p["line"],
            schema_jsonld=jsonld.as_script_tags(
                [
                    jsonld.build_breadcrumb_jsonld(
                        [
                            {"name": "홈", "url": "/"},
                            {"name": "페르소나", "url": "/personas/"},
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
                        {"name": "시나리오", "url": "/scenarios/"},
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

    # sitemap.xml
    urls = (
        ["/", "/scenarios/", "/about/"]
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
