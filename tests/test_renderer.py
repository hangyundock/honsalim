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
            site_base_url="https://honsallim.com",
            image_url="https://honsallim.com/static/img/og-default.png",
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
            "categories/index.html",
            "guides/index.html",  # 구매가이드 — 네비 링크 깨짐(/guides/ 404) 방지(세션 #20)
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
        # 카테고리 우선 홈(세션 #20): 히어로 카피·카테고리 섹션은 항상 존재(안정 검사)
        assert "1인 가구" in html  # 히어로 eyebrow
        assert "카테고리 둘러보기" in html  # 카테고리 CTA
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

    def test_unregistered_business_info_not_shown(self, built: dict) -> None:
        """미등록 사업자 정보 숨김 (세션 #20 정직성).

        '등록 진행 중' 과장 표기는 어떤 경우에도 노출 금지. 미등록(빈 값)이면 빈
        사업자등록번호 라벨을 숨기고 '개인 운영'으로 정직 표기(사업자 등록=DECISIONS D4 이후).
        """
        home = (built["out"] / "index.html").read_text(encoding="utf-8")
        about = (built["out"] / "about" / "index.html").read_text(encoding="utf-8")
        assert "등록 진행 중" not in home
        assert "등록 진행 중" not in about
        if not renderer.BUSINESS_INFO["bizno"]:
            assert "사업자등록번호" not in home  # 빈 번호 라벨 미노출
            assert "통신판매업" not in home

    def test_sitemap_lists_core_urls(self, built: dict) -> None:
        xml = (built["out"] / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://honsallim.com/" in xml
        assert "https://honsallim.com/scenarios/" in xml
        assert "https://honsallim.com/personas/cheot-jachi/" in xml

    def test_robots_and_headers_written(self, built: dict) -> None:
        """배포 산출물 — robots.txt(색인 규칙·sitemap) + _headers(캐시·보안)."""
        robots = (built["out"] / "robots.txt").read_text(encoding="utf-8")
        assert "Sitemap: https://honsallim.com/sitemap.xml" in robots
        assert "Disallow: /go/" in robots  # 제휴 redirect 색인 제외
        headers = (built["out"] / "_headers").read_text(encoding="utf-8")
        # 정적 자산: 1년 immutable (성능)
        assert "Cache-Control: public, max-age=31536000, immutable" in headers
        assert "X-Content-Type-Options: nosniff" in headers
        # HTML(/*): 짧은 엣지 캐시 — 콘텐츠 수정/삭제가 수 분 내 반영(7일 지연 방지, 세션 #20)
        assert "s-maxage=300" in headers
        assert "max-age=0" in headers  # 브라우저 재검증
        # 더 구체적 경로(/static/*) 규칙이 /*(HTML) 규칙보다 먼저 와야 정적 1년 캐시가 우선 적용됨
        assert headers.index("max-age=31536000") < headers.index("s-maxage=300")

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


class TestReviewPages:
    """단건 추천 리뷰(/reviews/<slug>/) — 쿠팡 파트너스 승인용 운영자 큐레이션 페이지 가드.

    - 첫머리 대가성 고지(쿠팡 파트너스 + 수수료) 필수 — 공정위·쿠팡 파트너스 정책.
    - 쿠팡 제휴 링크는 rel="sponsored nofollow" + 외부 새 탭.
    - noindex + sitemap 제외(소프트 공개) — 알리+쿠팡 배치 설계 합의 전 색인·내부링크 보류.
    REVIEW_PAGES는 모듈 상수라 seed만으로도 렌더됨 → built(seed) 픽스처로 검사.
    """

    def _html(self, built: dict) -> str:
        path = built["out"] / "reviews" / "honplanet-monitor-arm" / "index.html"
        assert path.exists(), "리뷰 페이지 index.html 미생성"
        text: str = path.read_text(encoding="utf-8")
        return text

    def test_review_page_written(self, built: dict) -> None:
        self._html(built)

    def test_first_disclosure_present(self, built: dict) -> None:
        html = self._html(built)
        assert "쿠팡 파트너스" in html  # 제휴처명(쿠팡) — disclosure 게이트 기준
        assert "수수료" in html  # 대가성
        assert "대가성 안내" in html

    def test_coupang_affiliate_link_with_rel(self, built: dict) -> None:
        html = self._html(built)
        assert "https://link.coupang.com/a/ehtwmQRZAG" in html
        assert html.count("sponsored nofollow") >= 1  # 제휴 링크 표기(POLICY §6)
        assert 'target="_blank"' in html

    def test_affiliate_link_shown_as_text(self, built: dict) -> None:
        # 쿠팡 승인 심사 가시성 — 버튼뿐 아니라 link.coupang.com 주소를 글자로도 노출(쿠팡 예시 정합).
        html = self._html(built)
        assert "쿠팡 파트너스 링크:" in html
        assert "link.coupang.com/a/ehtwmQRZAG" in html  # https:// 없는 표시용 텍스트

    def test_hero_image_present_no_blocked_iframe(self, built: dict) -> None:
        # 히어로 = 자체 개념 이미지(항상 표시). 추적차단에 막히는 쿠팡 iframe 위젯은 미사용.
        html = self._html(built)
        assert "/static/images/concepts/monitor-arm.webp" in html
        assert "개념 이미지" in html  # 실제 제품 아님을 캡션으로 명시(정직성 §0)
        assert "coupa.ng" not in html  # 미표시되는 외부 iframe 배너 제거 확인

    def test_noindex_and_not_in_sitemap(self, built: dict) -> None:
        html = self._html(built)
        assert 'content="noindex' in html  # 소프트 공개 — 검색 비색인
        xml = (built["out"] / "sitemap.xml").read_text(encoding="utf-8")
        assert "/reviews/honplanet-monitor-arm/" not in xml  # 색인 제외와 일관

    def test_no_jinja_leftovers(self, built: dict) -> None:
        html = self._html(built)
        assert "{{" not in html and "{%" not in html
        assert "&lt;svg" not in html  # 아이콘 SVG 미이스케이프


class TestMethodPage:
    """추천 방법(방법론) 페이지 — E-E-A-T·신뢰 신호(데이터 기반 비교 명문화, 세션 #24 T2).

    2025.12 어필리에이트 패널티(손실군=소유·테스트 없는 Best 리스트) 회피 핵심:
    우리 고유 데이터(판매량)를 '데이터 기반 비교'로 명문화 + 가짜 평점 안 만듦을 공개.
    """

    def test_method_page_written_and_in_sitemap(self, built: dict) -> None:
        out: Path = built["out"]
        path = out / "method" / "index.html"
        assert path.exists(), "method 페이지 미생성"
        html = path.read_text(encoding="utf-8")
        assert "판매 데이터" in html or "판매량" in html  # 데이터 기반 포지셔닝
        assert "가짜 평점" in html  # 정직성 명문화
        assert "혼살다" in html  # 저자(E-E-A-T)
        assert "{{" not in html and "{%" not in html
        # noindex 아님(진짜 신뢰 콘텐츠) → sitemap 포함(리뷰 페이지와 대조)
        xml = (out / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://honsallim.com/method/" in xml

    def test_footer_links_to_method(self, built: dict) -> None:
        home = (built["out"] / "index.html").read_text(encoding="utf-8")
        assert 'href="/method/"' in home  # 사이트 전역 푸터 신뢰 동선


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
        page = tmp_path / "site" / "categories" / "office-chair" / "index.html"
        assert page.exists()
        assert summary["categories"] == 1
        html = page.read_text(encoding="utf-8")
        assert "업데이트 예정" not in html  # placeholder 제거(E-E-A-T 약화 신호, 세션 #24)
        assert 'href="/method/"' in html  # 방법론 신뢰 동선 연결

    def test_assets_cache_busting(self, built: dict) -> None:
        # 세션 #21: CSS·JS 링크에 ?v=내용해시 — immutable 장기캐시가 새 디자인(흰바탕)을
        # 옛 캐시(우드톤)로 가리던 문제 재발방지. 자산 내용이 바뀌면 ?v= 값이 달라진다.
        home = (built["out"] / "index.html").read_text(encoding="utf-8")
        assert ".css?v=" in home, "CSS 링크 cache-busting ?v= 누락"
        assert ".js?v=" in home, "JS 링크 cache-busting ?v= 누락"
        v = renderer._asset_version()
        assert len(v) == 8 and all(c in "0123456789abcdef" for c in v)


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

    def test_data_summary_information_gain(self, tmp_path: Path) -> None:
        # Information Gain(세션 #24 T2): 우리 수집 실데이터(판매량·가격)를 상단 요약으로 전면화.
        # 가짜 없이 도출 — 2025.12 어필리 패널티(얇은 콘텐츠) 회피·데이터 기반 비교 포지셔닝.
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        conn = db.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "sales_volume, deeplink_url, deeplink_slug, affiliate_tag, "
                "created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress','ds1','베스트 책상','KRW',49000,1234,"
                "'https://s.click.aliexpress.com/ds1','ali-ds1','honsalim',"
                "datetime('now'),datetime('now'),datetime('now'))"
            )
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='ds1'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='desk'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier) VALUES (?,?,'budget')",
                (cid, pid),
            )
            category_state.approve(conn, "desk")
            conn.commit()
        finally:
            conn.close()
        out = tmp_path / "site"
        renderer.render_site(out_dir=out, db_path=db_path)
        html = (out / "categories" / "desk" / "index.html").read_text(encoding="utf-8")
        assert "데이터로 본" in html  # 요약 박스 존재
        assert "비교 제품 <b>1개</b>" in html
        assert "49,000원" in html  # 실데이터 가격(가짜 아님)
        assert "베스트 책상" in html  # 판매량 1위 제품명
        assert "1,234" in html  # 실제 판매량 수치

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


class TestCategoryProductImages:
    """카탈로그 상품 이미지 로딩 가드 (세션 #20 재발방지).

    증상: 검토 중 '이미지를 다 못 가져왔다'고 오인. 실제 원인은 loading="lazy" +
      전체페이지 스크린샷(화면 밖 이미지가 아직 미로드)일 뿐, 데이터·URL은 정상이었다
      (148개 전부 image_url_external 채움·알리 CDN 200 OK).
    대책: ①미리보기(검토)=eager 로딩 → 스크롤·전체스크린샷 없이 전부 표시
          ②공개 배포=lazy 유지(외부 이미지 40+ 동시 요청 방지·CWV/LCP)
          ③깨진 외부 이미지는 onerror로 자동 숨김(무인 graceful degrade·broken-icon 방지).
    무인 운영에서 시각 확인이 어려우므로 구조로 고정.
    """

    _IMG = "https://ae-pic-a1.aliexpress-media.com/kf/Simg1.jpg"

    def _render(self, tmp_path: Path, include_drafts: bool) -> str:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        conn = db.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "image_url_external, deeplink_url, deeplink_slug, affiliate_tag, "
                "created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress','img1','책상 상품','KRW',50000,?,"
                "'https://s.click.aliexpress.com/img1','ali-img1','honsalim',"
                "datetime('now'),datetime('now'),datetime('now'))",
                (self._IMG,),
            )
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='img1'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='desk'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier, is_featured) "
                "VALUES (?,?,'budget',1)",
                (cid, pid),
            )
            category_state.approve(conn, "desk")  # 승인 → published
            conn.commit()
        finally:
            conn.close()
        out = tmp_path / ("preview" if include_drafts else "site")
        renderer.render_site(out_dir=out, db_path=db_path, include_drafts=include_drafts)
        return (out / "categories" / "desk" / "index.html").read_text(encoding="utf-8")

    def test_catalog_image_src_present(self, tmp_path: Path) -> None:
        # 이미지 URL이 실제로 박혀야 함 — 빈 src·미수집은 회귀
        html = self._render(tmp_path, include_drafts=False)
        assert f'src="{self._IMG}"' in html
        assert 'src=""' not in html

    def test_production_uses_lazy(self, tmp_path: Path) -> None:
        # 공개 배포는 lazy (CWV/LCP 보호) — eager가 새지 않도록 고정
        html = self._render(tmp_path, include_drafts=False)
        assert 'loading="lazy"' in html
        assert 'loading="eager"' not in html

    def test_preview_uses_eager(self, tmp_path: Path) -> None:
        # 미리보기(검토)는 eager → 전체페이지 스크린샷·스크롤 없이 전부 표시(오인 재발 방지)
        html = self._render(tmp_path, include_drafts=True)
        assert 'loading="eager"' in html
        assert 'loading="lazy"' not in html

    def test_broken_image_onerror_retry_then_hide(self, tmp_path: Path) -> None:
        # 깨진 외부 이미지: 1회 재시도(일시 throttle 자가복구) → 그래도 실패 시 숨김(graceful degrade)
        html = self._render(tmp_path, include_drafts=False)
        assert "onerror=" in html
        assert "this.dataset.r" in html  # 재시도 1회 가드(무한루프 방지)
        assert "?r='+Date.now()" in html  # 캐시버스터 재요청
        assert "this.style.display='none'" in html  # 2차 실패 시 숨김


class TestHomeRichSections:
    """홈 콘텐츠 모듈(판매량 BEST·오늘의 딜·테마 큐레이션) 렌더 가드 (세션 #20).

    - 테마 dict 키는 'picks'여야 함 — 'items'면 Jinja에서 dict.items() 메서드로 해석돼
      렌더가 TypeError로 죽는 함정(group.cards·compare.vals와 동일 계열).
    - 실데이터(판매량·할인) 기반 섹션이 데이터 있을 때 실제 노출되는지 구조로 고정.
    """

    def _seed_two_categories(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            specs = [
                ("desk", "hb-desk", 50000, 71400, 30, 300),
                ("monitor-arm", "hb-arm", 30000, None, None, 200),
            ]
            for slug, spid, price, orig, disc, vol in specs:
                conn.execute(
                    "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                    "original_price_krw, discount_pct, sales_volume, image_url_external, "
                    "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
                    "VALUES ('aliexpress',?,?,'KRW',?,?,?,?,?,?,?,'honsalim',"
                    "datetime('now'),datetime('now'),datetime('now'))",
                    (
                        spid,
                        f"{slug} 상품",
                        price,
                        orig,
                        disc,
                        vol,
                        "https://ae-pic-a1.aliexpress-media.com/kf/x.jpg",
                        f"https://s.click.aliexpress.com/{spid}",
                        f"ali-{spid}",
                    ),
                )
                pid = conn.execute(
                    "SELECT id FROM products WHERE source_product_id=?", (spid,)
                ).fetchone()[0]
                cid = conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()[0]
                conn.execute(
                    "INSERT INTO category_products (category_id, product_id, tier, is_featured) "
                    "VALUES (?,?,'budget',1)",
                    (cid, pid),
                )
                category_state.approve(conn, slug)
            conn.commit()
        finally:
            conn.close()

    def test_best_deals_theme_render(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        self._seed_two_categories(db_path)
        out = tmp_path / "site"
        renderer.render_site(out_dir=out, db_path=db_path)  # picks 키 오류 시 여기서 TypeError
        html = (out / "index.html").read_text(encoding="utf-8")
        assert "판매량 BEST" in html  # sales_volume>0 제품 존재 → 노출
        assert "오늘의 딜" in html  # 신뢰 할인(30%) 존재 → 노출
        assert "테마 추천" in html and "재택 홈오피스" in html  # 2개 카테고리 featured → 테마 노출


class TestBuildSiteClean:
    """산출물 청소 가드 (세션 #20 재발방지).

    버그: render_site가 out_dir을 청소하지 않아, 미게시/삭제된 콘텐츠의 옛 HTML이
      build/site에 잔존 → 배포 시 라이브에서 안 내려감(예: 옛 글 제거 지시 무력화).
    무인 운영에서 'unpublish/삭제 → 라이브 반영'이 깨지면 치명적이라 구조로 고정.
    """

    def test_stale_output_removed_on_rebuild(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        out = tmp_path / "site"
        out.mkdir(parents=True)
        # 이전 빌드에만 있던(이제 DB에 없는) 옛 산출물
        stale = out / "articles" / "old-removed" / "index.html"
        stale.parent.mkdir(parents=True)
        stale.write_text("STALE", encoding="utf-8")
        renderer.render_site(out_dir=out, db_path=db_path)
        assert not stale.exists(), "옛 산출물 잔존 — 미게시/삭제 콘텐츠가 라이브에 남음"
        assert (out / "index.html").exists()  # 정상 재생성은 유지


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
        assert f"https://honsallim.com/articles/{slug}/" in xml

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
