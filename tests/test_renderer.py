"""builder.renderer 회귀 테스트 — DB seed → 정적 사이트 렌더 (DECISIONS G4).

render_site는 db_path에서 자체 연결을 열므로 파일 기반 임시 DB를 사용한다.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from builder import renderer
from builder.jsonld import build_article_jsonld
from common import db
from writer import article_writer, category_state
from writer.state_machine import transition


@pytest.fixture()
def built(tmp_path: Path) -> dict:
    """임시 DB에 migrate+seed 후 임시 디렉토리로 렌더. summary + out 반환."""
    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    out = tmp_path / "site"
    summary = renderer.render_site(out_dir=out, db_path=db_path)
    return {"summary": summary, "out": out}


_ARTICLE_BODY = (
    "이 글에는 AliExpress 어필리에이트 활동의 일환으로 일정 수수료를 제공받습니다. "
    "(구매자에게 추가 비용은 발생하지 않습니다.)\n\n"
    "# 홈오피스 50만원 세팅\n\n"
    "## 1. 의자\n인체공학 의자를 추천합니다. 가격 143,200원.\n\n"
    "## 2. 책상\n접이식 책상 95,600원으로 충분합니다.\n\n"
    "혼살림은 쿠팡 파트너스 및 AliExpress Portals 어필리에이트 활동의 일환으로 "
    "일정 수수료를 받습니다. 본인 및 가족 구매 금지·자동 실행 광고 미사용 등 "
    "어필리에이트 정책을 준수합니다."
)


@pytest.fixture()
def built_with_article(tmp_path: Path) -> dict:
    """seed + 게시 article 1편(+상품 2건·article_products) 후 렌더 (상세글 경로)."""
    import markdown as md_lib

    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    conn = db.connect(db_path)
    try:
        srow = conn.execute("SELECT id, slug FROM scenarios ORDER BY id LIMIT 1").fetchone()
        scenario_id, slug = srow[0], srow[1]
        for spid, price in (("p111", 143200), ("p222", 95600)):
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress', ?, ?, 'KRW', ?, ?, ?, 'honsalim', "
                "datetime('now'), datetime('now'), datetime('now'))",
                (
                    spid,
                    f"상품 {spid}",
                    price,
                    f"https://s.click.aliexpress.com/{spid}",
                    f"ali-{spid}",
                ),
            )
        conn.commit()

        did = article_writer.create_draft(conn, scenario_id=scenario_id)
        transition(conn, did, "enriched")
        transition(conn, did, "validated")
        transition(conn, did, "approved")
        schema = build_article_jsonld(
            meta={"title": "홈오피스 50만원 세팅", "meta_description": "재택 세팅 가이드"},
            scenario={"slug": slug},
            site_base_url="https://honsalim.com",
            image_url="https://honsalim.com/static/img/og-default.png",
            published_at="2026-05-30",
        )
        fields = {
            "slug": slug,
            "scenario_id": scenario_id,
            "title": "홈오피스 50만원 세팅",
            "summary": "재택 8시간 세팅",
            "body_md": _ARTICLE_BODY,
            "body_html": md_lib.markdown(_ARTICLE_BODY, extensions=["extra", "sane_lists"]),
            "meta_description": "재택 세팅 가이드",
            "schema_jsonld": schema,
            "disclosure_first": article_writer.extract_disclosure_first(_ARTICLE_BODY),
            "content_hash": article_writer.compute_content_hash(_ARTICLE_BODY),
            "truth_check_passed_at": "2026-05-30T00:00:00Z",
            "user_approved_at": "2026-05-30T00:00:00Z",
        }
        aid = article_writer.promote_to_article(conn, did, fields)
        article_writer.link_article_products(
            conn,
            aid,
            [
                {"source": "aliexpress", "source_product_id": "p111"},
                {"source": "aliexpress", "source_product_id": "p222"},
            ],
        )
    finally:
        conn.close()

    out = tmp_path / "site"
    summary = renderer.render_site(out_dir=out, db_path=db_path)
    return {"summary": summary, "out": out, "slug": slug}


class TestRenderSite:
    def test_core_pages_written(self, built: dict) -> None:
        out: Path = built["out"]
        for rel in (
            "index.html",
            "scenarios/index.html",
            "about/index.html",
            "404.html",
            "sitemap.xml",
            "personas/index.html",
            "static/css/tokens.css",
        ):
            assert (out / rel).exists(), f"{rel} 미생성"

    def test_seed_counts(self, built: dict) -> None:
        s = built["summary"]
        assert s["scenarios"] == 10
        assert s["personas"] == 3
        assert s["articles_published"] == 0  # 게시 콘텐츠 0편 (Phase 3~4 전)

    def test_persona_pages_per_slug(self, built: dict) -> None:
        out: Path = built["out"]
        for slug in ("cheot-jachi", "homeoffice", "minimal-life"):
            assert (out / "personas" / slug / "index.html").exists()

    def test_home_real_data_no_template_leftovers(self, built: dict) -> None:
        html = (built["out"] / "index.html").read_text(encoding="utf-8")
        assert "원룸 첫 자취" in html  # 실제 seed 시나리오 제목
        assert "{{" not in html and "{%" not in html  # Jinja 미전개 잔재 없음
        assert "&lt;svg" not in html  # 아이콘 SVG 미이스케이프

    def test_hub_has_ten_cards_and_data_driven_filters(self, built: dict) -> None:
        html = (built["out"] / "scenarios" / "index.html").read_text(encoding="utf-8")
        # 변형(s-card / s-card-soon) 무관하게 시나리오 카드 10개
        assert html.count('class="s-card') == 10
        assert 'data-value="2-3월"' in html  # season_peak 실값 기반 필터

    def test_scenarios_without_articles_are_not_linked(self, built: dict) -> None:
        """seed만(게시 글 0편) → 모든 시나리오 카드는 비클릭 '준비 중', /articles/ 링크 0개.

        글 없는 카드가 404로 가는 것 방지 (콘텐츠 단계 발행 중 깨진 링크 회피).
        """
        html = (built["out"] / "scenarios" / "index.html").read_text(encoding="utf-8")
        assert html.count("s-card-soon") == 10
        assert html.count("준비 중") == 10
        assert "/articles/" not in html  # 링크된 글 없음

    def test_about_image_policy_matches_l2(self, built: dict) -> None:
        """About 이미지 정책 = AI 생성 (DECISIONS L2), '직접 촬영' 문구 없음."""
        html = (built["out"] / "about" / "index.html").read_text(encoding="utf-8")
        assert "AI로 생성" in html
        assert "직접 촬영" not in html

    def test_sitemap_lists_core_urls(self, built: dict) -> None:
        xml = (built["out"] / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://honsalim.com/" in xml
        assert "https://honsalim.com/scenarios/" in xml
        assert "https://honsalim.com/personas/cheot-jachi/" in xml

    def test_robots_and_headers_written(self, built: dict) -> None:
        """배포 산출물 — robots.txt(색인 규칙·sitemap) + _headers(캐시·보안)."""
        robots = (built["out"] / "robots.txt").read_text(encoding="utf-8")
        assert "Sitemap: https://honsalim.com/sitemap.xml" in robots
        assert "Disallow: /go/" in robots  # 제휴 redirect 색인 제외
        headers = (built["out"] / "_headers").read_text(encoding="utf-8")
        assert "Cache-Control: public, max-age=31536000" in headers
        assert "X-Content-Type-Options: nosniff" in headers

    def test_home_meta_and_schema(self, built: dict) -> None:
        html = (built["out"] / "index.html").read_text(encoding="utf-8")
        assert 'property="og:title"' in html
        assert 'name="twitter:card"' in html
        assert '"@type": "WebSite"' in html
        assert '"@type": "Organization"' in html
        assert html.count('rel="canonical"') == 1  # 중복 canonical 없음

    def test_breadcrumb_schema_on_subpages(self, built: dict) -> None:
        scn = (built["out"] / "scenarios" / "index.html").read_text(encoding="utf-8")
        assert '"@type": "BreadcrumbList"' in scn
        per = (built["out"] / "personas" / "cheot-jachi" / "index.html").read_text(encoding="utf-8")
        assert '"@type": "BreadcrumbList"' in per


class TestRenderArticleDetail:
    """published article → 상세글 렌더 (산문 body_html + /go/ 제휴 상품 카드)."""

    def _html(self, built: dict) -> str:
        path = built["out"] / "articles" / built["slug"] / "index.html"
        assert path.exists(), "상세글 index.html 미생성"
        text: str = path.read_text(encoding="utf-8")
        return text

    def test_article_page_written_and_counted(self, built_with_article: dict) -> None:
        assert built_with_article["summary"]["articles_published"] == 1
        self._html(built_with_article)  # 존재 확인

    def test_go_affiliate_links_with_rel(self, built_with_article: dict) -> None:
        html = self._html(built_with_article)
        assert html.count("/go/ali-p111") == 1
        assert html.count("/go/ali-p222") == 1
        assert html.count("sponsored nofollow") == 2  # POLICY §6 제휴 링크 표기

    def test_prices_rendered(self, built_with_article: dict) -> None:
        html = self._html(built_with_article)
        assert "143,200원" in html
        assert "95,600원" in html

    def test_body_html_and_compliance(self, built_with_article: dict) -> None:
        html = self._html(built_with_article)
        assert html.count("<h1") == 1  # body_html H1 1개 — 템플릿 중복 없음
        assert "AliExpress 어필리에이트" in html  # 첫머리 대가성 고지
        assert "biz-grid" in html  # 사업자 정보 푸터
        assert "{{" not in html and "{%" not in html  # Jinja 미전개 잔재 없음

    def test_schema_and_canonical(self, built_with_article: dict) -> None:
        html = self._html(built_with_article)
        assert '"@type": "Article"' in html
        assert '"@type": "BreadcrumbList"' in html
        assert html.count('rel="canonical"') == 1


class TestCategoryPublishGate:
    """draft 카테고리는 렌더 제외, published만 공개 — 승인 게이트(세션 #18·§2-마·E7)."""

    def _seed_category_product(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress','cp1','의자 상품','KRW',50000,"
                "'https://s.click.aliexpress.com/cp1','ali-cp1','honsalim',"
                "datetime('now'),datetime('now'),datetime('now'))"
            )
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='cp1'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='office-chair'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier) VALUES (?,?,'budget')",
                (cid, pid),
            )
            conn.commit()
        finally:
            conn.close()

    def test_draft_category_not_rendered(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)  # seed 카테고리 = draft(미공개)
        self._seed_category_product(db_path)
        summary = renderer.render_site(out_dir=tmp_path / "site", db_path=db_path)
        # draft → 상세 미생성·카운트 0 (AI 자동 published 금지·E7)
        assert not (tmp_path / "site" / "categories" / "office-chair" / "index.html").exists()
        assert summary["categories"] == 0

    def test_published_category_rendered(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        self._seed_category_product(db_path)
        conn = db.connect(db_path)
        try:
            category_state.approve(conn, "office-chair")  # 사용자 승인 → published
        finally:
            conn.close()
        summary = renderer.render_site(out_dir=tmp_path / "site", db_path=db_path)
        assert (tmp_path / "site" / "categories" / "office-chair" / "index.html").exists()
        assert summary["categories"] == 1


class TestCategoryInteraction:
    """전체 제품 정렬·티어 필터(JS) 배선 + 추천 카드 좌우 행 정렬(CSS) 재발 방지 가드 (세션 #19).

    - 카탈로그 카드의 data-* 또는 #catSort/#catGrid 등 훅이 빠지면 정렬·필터가 조용히 죽는다.
    - 추천 카드의 grid stretch·flex 칼럼·버튼 하단 고정이 빠지면 장점·단점 개수 차이로
      좌우 카드 아래단이 다시 어긋난다. 무인 운영에서 시각 확인이 어려우므로 수치/구조로 고정.
    """

    _CSS = Path(__file__).resolve().parent.parent / "static" / "css" / "category.css"

    def _seed_and_publish(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "original_price_krw, discount_pct, deeplink_url, deeplink_slug, affiliate_tag, "
                "created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress','cw1','책상 상품','KRW',50000,71400,30,"
                "'https://s.click.aliexpress.com/cw1','ali-cw1','honsalim',"
                "datetime('now'),datetime('now'),datetime('now'))"
            )
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='cw1'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='desk'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier) VALUES (?,?,'budget')",
                (cid, pid),
            )
            category_state.approve(conn, "desk")  # 승인 → published
            conn.commit()
        finally:
            conn.close()

    def test_catalog_cards_carry_sort_filter_data(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        self._seed_and_publish(db_path)
        out = tmp_path / "site"
        renderer.render_site(out_dir=out, db_path=db_path)
        html = (out / "categories" / "desk" / "index.html").read_text(encoding="utf-8")
        # 정렬·필터 JS가 읽는 숫자/티어 데이터 (가격 오름차순·할인 내림차순·티어 필터)
        assert 'data-price="50000"' in html
        assert 'data-disc="30"' in html
        assert 'data-tier="budget"' in html
        assert 'data-idx="0"' in html
        for hook in ('id="catSort"', 'id="catTier"', 'id="catGrid"', 'id="catCount"'):
            assert hook in html, f"{hook} 누락 — 정렬·필터 JS 배선 끊김"
        assert "/static/js/category.js" in html, "category.js 미참조 — 인터랙션 비활성"
        # JS 자산이 실제 배포물에 복사됐는지 (static 복사 누락 회귀 방지)
        assert (out / "static" / "js" / "category.js").exists()

    def test_pick_cards_row_alignment_css(self) -> None:
        css = self._CSS.read_text(encoding="utf-8")
        picks = re.search(r"\.catpage \.picks \{([^}]*)\}", css)
        assert picks and "align-items: stretch" in picks.group(
            1
        ), ".picks가 align-items: stretch 아님 — 좌우 카드 행 높이 정렬 깨짐(세션 #19)"
        tcard = re.search(r"\.catpage \.tcard \{([^}]*)\}", css)
        assert tcard and "flex-direction: column" in tcard.group(
            1
        ), ".tcard가 flex 칼럼 아님 — 버튼 하단 고정 불가(세션 #19)"
        tbtns = re.search(r"\.catpage \.tbtns \{([^}]*)\}", css)
        assert tbtns and "margin-top: auto" in tbtns.group(
            1
        ), ".tbtns margin-top:auto 누락 — 버튼이 바닥에 안 붙어 카드 아래단 어긋남(세션 #19)"


class TestMarkdownInline:
    """산문 인라인 마크다운(**볼드**) 변환 — raw ** 화면 노출 방지(세션 #18)."""

    def test_bold_converted(self) -> None:
        assert str(renderer._md_inline("**책상** 하나")) == "<strong>책상</strong> 하나"

    def test_plain_passthrough(self) -> None:
        assert str(renderer._md_inline("일반 텍스트")) == "일반 텍스트"

    def test_xss_escaped(self) -> None:
        out = str(renderer._md_inline("<script>x</script>"))
        assert "<script>" not in out and "&lt;script&gt;" in out

    def test_empty(self) -> None:
        assert str(renderer._md_inline("")) == ""

    def test_sitemap_includes_article_url(self, built_with_article: dict) -> None:
        slug = built_with_article["slug"]
        xml = (built_with_article["out"] / "sitemap.xml").read_text(encoding="utf-8")
        assert f"https://honsalim.com/articles/{slug}/" in xml

    def test_scenario_with_article_links_others_soon(self, built_with_article: dict) -> None:
        """게시 글이 있는 시나리오 카드만 /articles/<slug>/로 링크, 나머지는 '준비 중'."""
        slug = built_with_article["slug"]
        hub = (built_with_article["out"] / "scenarios" / "index.html").read_text(encoding="utf-8")
        assert hub.count('class="s-card') == 10  # 카드 총 10
        assert f'href="/articles/{slug}/"' in hub  # 글 있는 카드는 링크됨
        assert hub.count("s-card-soon") == 9  # 나머지 9개는 비클릭
        assert hub.count("준비 중") == 9


# 브랜드 용어 가드 — 'AI 자카'(시나리오/페르소나)를 일상어로 교체 후 재발 방지 (세션 #14).
# 비개발자 일상어가 아닌 위 두 단어가 화면/검색 노출 텍스트에 다시 등장하면 빌드를
# 실패시켜 무인 회귀를 차단한다 (→ '내맘대로 세팅'·'라이프스타일').
_BANNED_DISPLAY_TERMS = ("시나리오", "페르소나")


def _assert_no_banned_terms(out: Path) -> None:
    """out 아래 모든 .html(메뉴·푸터·breadcrumb·meta·JSON-LD·본문 포함)에
    금지 용어가 없어야 한다. *.xml(영문 slug)·*.css/*.js(코드 주석)는 대상 외."""
    offenders: list[str] = []
    for html_path in sorted(out.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        for term in _BANNED_DISPLAY_TERMS:
            if term in text:
                offenders.append(f"{html_path.relative_to(out).as_posix()} → '{term}'")
    assert not offenders, "AI 자카 용어 노출 (일상어로 교체 필요):\n" + "\n".join(offenders)


class TestNoAiJargonTerms:
    """렌더된 어떤 페이지에도 '시나리오'·'페르소나'가 노출되면 안 된다 (세션 #14 용어 교체)."""

    def test_chrome_pages_have_no_banned_terms(self, built: dict) -> None:
        _assert_no_banned_terms(built["out"])

    def test_article_page_has_no_banned_terms(self, built_with_article: dict) -> None:
        _assert_no_banned_terms(built_with_article["out"])
