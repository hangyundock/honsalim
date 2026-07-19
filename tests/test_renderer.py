"""builder.renderer 회귀 테스트 — DB seed → 정적 사이트 렌더 (DECISIONS G4).

render_site는 db_path에서 자체 연결을 열므로 파일 기반 임시 DB를 사용한다.
"""

from __future__ import annotations

import json
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


def _build_article_site(tmp_path: Path, *, publish_category: bool = False) -> dict:
    """seed + 게시 article 1편(+상품 2건·article_products) 후 렌더 헬퍼.

    publish_category=True면 office-chair 카테고리에 제품 연결·승인(published) — 글의
    concept_image(office-chair)가 매핑돼 카테고리 경로(category.html 재사용·세션 #34)로
    렌더된다. 기본 False는 매핑 없음(article.html 폴백) — 기존 테스트 동작 유지.
    """
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
            "structured_json": json.dumps(
                {
                    "quick_verdict": "예산 따라 의자부터 고르세요.",
                    "checkpoints": [{"title": "요추 지지", "why": "장시간 착석 시 허리 보호"}],
                    "product_notes": {
                        "ali-p111": {
                            "pros": ["인체공학 설계", "튼튼한 프레임"],
                            "cons": ["조립 필요"],
                            "for_who": "재택 장시간 근무",
                        }
                    },
                    "concept_image": "/static/images/concepts/office-chair.webp",
                    "concept_image_alt": "의자 비교 가이드",
                },
                ensure_ascii=False,
            ),
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
        if publish_category:
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='p111'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='office-chair'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier) "
                "VALUES (?,?,'budget')",
                (cid, pid),
            )
            category_state.approve(conn, "office-chair")
            conn.commit()
    finally:
        conn.close()

    out = tmp_path / "site"
    summary = renderer.render_site(out_dir=out, db_path=db_path)
    return {"summary": summary, "out": out, "slug": slug}


@pytest.fixture()
def built_with_article(tmp_path: Path) -> dict:
    """seed + 게시 article 1편(+상품 2건·article_products) 후 렌더 (상세글 경로)."""
    return _build_article_site(tmp_path)


class TestRenderSite:
    def test_core_pages_written(self, built: dict) -> None:
        out: Path = built["out"]
        for rel in (
            "index.html",
            "scenarios/index.html",
            "about/index.html",
            "privacy/index.html",  # 개인정보처리방침(PIPA E2·세션 #45)
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
        assert "Disallow: /cdn-cgi/" in robots  # Cloudflare 내부(이메일 보호) 크롤 제외(#40)
        headers = (built["out"] / "_headers").read_text(encoding="utf-8")
        # 정적 자산: 1년 immutable (성능)
        assert "Cache-Control: public, max-age=31536000, immutable" in headers
        assert "X-Content-Type-Options: nosniff" in headers
        # HTML(/*): 짧은 엣지 캐시 — 콘텐츠 수정/삭제가 수 분 내 반영(7일 지연 방지, 세션 #20)
        assert "s-maxage=300" in headers
        assert "max-age=0" in headers  # 브라우저 재검증
        # 더 구체적 경로(/static/*) 규칙이 /*(HTML) 규칙보다 먼저 와야 정적 1년 캐시가 우선 적용됨
        assert headers.index("max-age=31536000") < headers.index("s-maxage=300")

    def test_favicon_at_root_and_referenced(self, built: dict) -> None:
        """파비콘 루트 배포 + 전 페이지 참조 — /favicon.ico 부재 시 빈 200(소프트 404)으로
        네이버 색인 제외되던 문제 해소(세션 #40)."""
        out: Path = built["out"]
        assert (
            out / "favicon.ico"
        ).exists(), "favicon.ico 루트 미배포 → /favicon.ico 소프트404 재발"
        assert (out / "favicon.svg").exists(), "favicon.svg 루트 미배포"
        html = (out / "index.html").read_text(encoding="utf-8")
        assert 'href="/favicon.ico"' in html  # base.html 전 페이지 참조

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


class TestPrivacyPage:
    """개인정보처리방침 단독 페이지(/privacy/) — PIPA 게재 의무(E2 [확정])·세션 #45.

    내용은 실제 수집 현실(직접 수집 없음·D1 로깅 보류 R4) 기준 — 과대 기술 금지(§0 정직성).
    이전엔 footer가 /about/#privacy 앵커(방침 전문 없는 '빈 약속')로 연결됐다.
    """

    def test_privacy_page_written_and_honest(self, built: dict) -> None:
        out: Path = built["out"]
        path = out / "privacy" / "index.html"
        assert path.exists(), "privacy 페이지 미생성"
        html = path.read_text(encoding="utf-8")
        assert "개인정보처리방침" in html
        assert "직접 수집하지 않는" in html  # 실수집 현실 기준(과대 기술 금지)
        assert "Cloudflare" in html  # 호스팅 위탁 고지
        assert "30일" in html  # 이메일 문의 응답 원칙(POLICY §7-5)
        assert "{{" not in html and "{%" not in html

    def test_privacy_in_sitemap_without_lastmod(self, built: dict) -> None:
        xml = (built["out"] / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://honsallim.com/privacy/" in xml  # 정적 페이지 — lastmod 없음(SITEMAP-02)

    def test_footer_links_to_privacy_page(self, built: dict) -> None:
        home = (built["out"] / "index.html").read_text(encoding="utf-8")
        assert 'href="/privacy/"' in home  # 전 페이지 푸터 — 단독 페이지로 연결
        assert 'href="/about/#privacy"' not in home  # 옛 앵커('빈 약속') 잔재 없음


class TestAboutEEAT:
    """세션 #45 — About 운영자 Person Schema(M2) + 부정직 문구 정리(L3·정직성 §0)."""

    def test_about_has_person_jsonld(self, built: dict) -> None:
        html = (built["out"] / "about" / "index.html").read_text(encoding="utf-8")
        assert '"@type": "Person"' in html  # 운영자 Person 엔티티(E-E-A-T)
        assert "혼살다" in html  # 필명(M2-2)
        assert '"knowsAbout"' in html  # 전문성 영역(M2-4)

    def test_no_false_experience_claims(self, built: dict) -> None:
        """1인칭·거짓 경험 주장 제거(L3·QRG §4.5.3 — 가짜 경험 바이오는 최저 품질 신호)."""
        about = (built["out"] / "about" / "index.html").read_text(encoding="utf-8")
        method = (built["out"] / "method" / "index.html").read_text(encoding="utf-8")
        for banned in ("실제 경험에서 출발", "검색에 며칠을 썼습니다", "실사용 경험"):
            assert banned not in about, f"about에 거짓 경험 문구 잔존: {banned}"
            assert banned not in method, f"method에 거짓 경험 문구 잔존: {banned}"
        # 완전무인(자동 승인) 현실과 모순되는 '사람이 검토한 뒤 공개' 단정 제거
        assert "그냥 올라가지 않습니다" not in method
        assert "직접 사용 경험을 주장하지 않습니다" in about  # 정직 명문화


class TestIndexnowKeyFile:
    """세션 #45 — IndexNow <key>.txt 루트 생성(env 기반·미설정이면 생략·§0)."""

    KEY = "abcd1234efgh5678"

    def _render(self, tmp_path: Path, key: str | None, monkeypatch: pytest.MonkeyPatch) -> Path:
        if key is None:
            monkeypatch.delenv("INDEXNOW_KEY", raising=False)
        else:
            monkeypatch.setenv("INDEXNOW_KEY", key)
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        out = tmp_path / "site"
        renderer.render_site(out_dir=out, db_path=db_path)
        return out

    def test_key_file_written_with_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out = self._render(tmp_path, self.KEY, monkeypatch)
        f = out / f"{self.KEY}.txt"
        assert f.exists()
        assert f.read_text(encoding="utf-8").strip() == self.KEY

    def test_no_key_file_without_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        out = self._render(tmp_path, None, monkeypatch)
        assert not (out / f"{self.KEY}.txt").exists()  # 미설정 — 조용히 생략(빌드는 정상)

    def test_invalid_key_not_written(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        out = self._render(tmp_path, "bad key/../x", monkeypatch)
        txts = [p.name for p in out.glob("*.txt") if p.name != "robots.txt"]
        assert txts == []  # 형식 밖 env 값은 경로로 새지 않음(방어)


class TestPillarPage:
    """홈오피스 필러(허브) — 토픽 클러스터 hub (세션 #24 T2). 공개 스포크 있을 때만 렌더.

    단순 링크모음이 아닌 '갖추는 순서·예산'(진짜 가치) + 허브↔스포크 양방향 내부링크.
    """

    def _publish_office_chair(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
                "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
                "VALUES ('aliexpress','pl1','의자 상품','KRW',80000,"
                "'https://s.click.aliexpress.com/pl1','ali-pl1','honsalim',"
                "datetime('now'),datetime('now'),datetime('now'))"
            )
            pid = conn.execute("SELECT id FROM products WHERE source_product_id='pl1'").fetchone()[
                0
            ]
            cid = conn.execute("SELECT id FROM categories WHERE slug='office-chair'").fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier) VALUES (?,?,'budget')",
                (cid, pid),
            )
            category_state.approve(conn, "office-chair")  # homeoffice 그룹 공개
            conn.commit()
        finally:
            conn.close()

    def test_pillar_rendered_with_spokes_and_backlink(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        self._publish_office_chair(db_path)
        out = tmp_path / "site"
        renderer.render_site(out_dir=out, db_path=db_path)
        path = out / "home-office" / "index.html"
        assert path.exists(), "홈오피스 필러 미생성"
        html = path.read_text(encoding="utf-8")
        assert "갖추는 순서" in html  # 진짜 가치(순서)
        assert "예산대별 조합" in html
        assert "/categories/office-chair/" in html  # 허브→스포크 링크
        assert "{{" not in html and "{%" not in html
        # 스포크→허브 백링크(양방향)
        cat = (out / "categories" / "office-chair" / "index.html").read_text(encoding="utf-8")
        assert "/home-office/" in cat
        # 색인 대상 → sitemap 포함
        xml = (out / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://honsallim.com/home-office/" in xml

    def test_pillar_skipped_when_no_published_spokes(self, built: dict) -> None:
        # seed만(홈오피스 카테고리 draft) → 공개 스포크 0 → 빈 허브 방지 위해 미렌더
        assert not (built["out"] / "home-office" / "index.html").exists()


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
        # Tier 2(세션 #31): 같은 상품이 추천 픽 카드 + 한눈 비교표에 함께 노출된다(결정·비교
        # 두 관점). 단건 카드 시절의 '상품당 링크 1개' 가정 대신, 모든 /go/ 제휴 링크가
        # 빠짐없이 rel="sponsored nofollow"로 표기되는지(POLICY §6)를 레이아웃 독립 불변식으로 고정.
        html = self._html(built_with_article)
        assert "/go/ali-p111" in html
        assert "/go/ali-p222" in html
        assert html.count("/go/") == html.count("sponsored nofollow"), "표기 안 된 제휴 링크 존재"
        assert html.count("/go/") >= 4  # 픽 카드(이미지·이름·가격·구매) 다중 노출

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

    def test_jsonld_main_entity_matches_canonical(self, built_with_article: dict) -> None:
        # 렌더 시점 재생성된 Article JSON-LD의 mainEntityOfPage가 canonical과 끝슬래시까지
        # 일치(세션 #40 IDX-04) — 자기참조 URL 불일치 제거.
        html = self._html(built_with_article)
        slug = built_with_article["slug"]
        assert f'"mainEntityOfPage": "https://honsallim.com/articles/{slug}/"' in html
        assert f'rel="canonical" href="https://honsallim.com/articles/{slug}/"' in html

    def test_jsonld_headline_matches_title(self, built_with_article: dict) -> None:
        # JSON-LD headline = 글 제목(페이지 제목과 동일 소스) — 3중 분산 제거(세션 #40 IDX-03).
        html = self._html(built_with_article)
        assert '"headline": "홈오피스 50만원 세팅"' in html

    def test_sitemap_article_has_lastmod_static_does_not(self, built_with_article: dict) -> None:
        # 발행 글은 lastmod(published_at)로 재크롤 신호 / 정적 페이지는 lastmod 생략(부정확 신호
        # 회피) — 세션 #40 SITEMAP-02.
        slug = built_with_article["slug"]
        xml = (built_with_article["out"] / "sitemap.xml").read_text(encoding="utf-8")
        art_line = next(ln for ln in xml.splitlines() if f"/articles/{slug}/" in ln)
        assert "<lastmod>" in art_line
        home_line = next(ln for ln in xml.splitlines() if "<loc>https://honsallim.com/</loc>" in ln)
        assert "<lastmod>" not in home_line


class TestArticleInternalLinks:
    """발행 글 내부링크 — 고아(orphan) 방지(세션 #40).

    발행 글이 '시나리오 카드(active=1 시나리오에 글 연결)'로만 닿도록 설계돼, 글이 묶인
    시나리오가 비활성이면 어떤 페이지에서도 링크되지 않는 고아가 됐다(사이트맵에만 존재 →
    색인돼도 크롤·트래픽 0). 근본 수정: 시나리오 상태와 무관하게 홈·구매가이드 허브에서 항상
    글로 닿는다. 이 불변식을 회귀 가드로 고정한다.
    """

    def test_article_linked_from_home(self, built_with_article: dict) -> None:
        slug = built_with_article["slug"]
        home = (built_with_article["out"] / "index.html").read_text(encoding="utf-8")
        assert f"/articles/{slug}/" in home, "홈 '추천 가이드'에서 발행 글로 링크되지 않음"

    def test_article_linked_from_guides_hub(self, built_with_article: dict) -> None:
        slug = built_with_article["slug"]
        guides = (built_with_article["out"] / "guides" / "index.html").read_text(encoding="utf-8")
        assert f"/articles/{slug}/" in guides, "구매가이드 허브에서 발행 글로 링크되지 않음"

    def test_article_not_orphan(self, built_with_article: dict) -> None:
        # 사이트맵·글 자신을 제외한 '탐색 가능한 페이지' 중 최소 1곳이 글로 링크해야 한다
        # (감사 #40의 grep 방법론을 회귀 가드로 고정 — 고아면 inbound=0).
        out: Path = built_with_article["out"]
        slug = built_with_article["slug"]
        needle = f"/articles/{slug}/"
        own = out / "articles" / slug / "index.html"
        inbound = [
            path.relative_to(out).as_posix()
            for path in out.rglob("*.html")
            if path != own and needle in path.read_text(encoding="utf-8")
        ]
        assert inbound, "발행 글이 어떤 탐색 페이지에서도 링크되지 않는 고아 상태"


@pytest.fixture()
def built_with_draft(tmp_path: Path) -> dict:
    """seed + 검토 대기(validated) 시나리오 draft 1편(쿠팡 이미지 + 알리 상품) → 미리보기·공개 둘 다 렌더.

    키워드→글 파이프라인이 만든 draft를 발행 전에 미리보기로 검토하는 경로(§2-마, 세션 #29).
    본문·메타·featured 상품은 enriched_payload(promote와 동일 소스)에 채운다.
    """
    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    conn = db.connect(db_path)
    try:
        srow = conn.execute("SELECT id, slug FROM scenarios ORDER BY id LIMIT 1").fetchone()
        scenario_id, slug = srow[0], srow[1]
        # 하이브리드 결합 화면 검증용: 쿠팡 공식배너 이미지(hotlink) + 알리(판매량) 상품
        conn.execute(
            "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
            "image_url_external, deeplink_url, deeplink_slug, affiliate_tag, "
            "created_at, updated_at, last_seen_at) "
            "VALUES ('coupang','cpx','쿠팡 의자','KRW',59000,?,"
            "'https://link.coupang.com/a/CP','coupang-cpx','coupang-partners',"
            "datetime('now'),datetime('now'),datetime('now'))",
            ("https://image.coupangcdn.com/chair.jpg",),
        )
        conn.execute(
            "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
            "sales_volume, deeplink_url, deeplink_slug, affiliate_tag, "
            "created_at, updated_at, last_seen_at) "
            "VALUES ('aliexpress','alx','알리 의자','KRW',42000,1500,"
            "'https://s.click.aliexpress.com/alx','ali-alx','honsalim',"
            "datetime('now'),datetime('now'),datetime('now'))"
        )
        did = article_writer.create_draft(conn, scenario_id=scenario_id)
        transition(conn, did, "enriched")
        schema = build_article_jsonld(
            meta={"title": "컴퓨터의자 하이브리드", "meta_description": "쿠팡+알리 비교"},
            scenario={"slug": slug},
            site_base_url="https://honsallim.com",
            image_url="https://honsallim.com/static/img/og-default.png",
            published_at="2026-06-14",
        )
        article_writer.save_enriched(
            conn,
            did,
            {
                "body_md": _ARTICLE_BODY,
                "title": "컴퓨터의자 하이브리드",
                "summary": "쿠팡 이미지 + 알리 판매량",
                "meta_description": "쿠팡+알리 비교",
                "schema_jsonld": schema,
                "products": [
                    {"source": "coupang", "source_product_id": "cpx"},
                    {"source": "aliexpress", "source_product_id": "alx"},
                ],
            },
        )
        transition(conn, did, "validated")  # 검토 대기
    finally:
        conn.close()

    preview = tmp_path / "preview"
    site = tmp_path / "site"
    renderer.render_site(out_dir=preview, db_path=db_path, include_drafts=True)
    summary = renderer.render_site(out_dir=site, db_path=db_path, include_drafts=False)
    return {"preview": preview, "site": site, "summary": summary, "slug": slug}


class TestRenderDraftArticlePreview:
    """검토 대기 시나리오 draft 미리보기 (세션 #29) — §2-마 인간 검토 게이트 핵심.

    버그(세션 #28→#29 라이브 테스트가 적발): _load_article_pages가 published만 렌더해
    키워드→글 파이프라인이 만든 draft를 승인 전에 미리보기로 볼 수 없었다(게이트 무력화).
    근본 수정: include_drafts=True면 validated draft도 발행 후와 동일 화면으로 렌더.
    """

    def _preview_html(self, built: dict) -> str:
        path = built["preview"] / "articles" / built["slug"] / "index.html"
        assert path.exists(), "검토 대기 draft 상세글이 미리보기에 미생성"
        text: str = path.read_text(encoding="utf-8")
        return text

    def test_draft_rendered_with_review_banner(self, built_with_draft: dict) -> None:
        html = self._preview_html(built_with_draft)
        assert "컴퓨터의자 하이브리드" in html  # draft 제목
        assert "검토용 미리보기" in html  # 검토 배너(공개엔 없음)
        assert "{{" not in html and "{%" not in html  # Jinja 미전개 잔재 없음

    def test_hybrid_products_shown_with_coupang_image(self, built_with_draft: dict) -> None:
        # 핵심: 쿠팡 공식배너 이미지(hotlink) + 알리 상품이 발행 후처럼 /go/ 카드로 표시
        html = self._preview_html(built_with_draft)
        assert "https://image.coupangcdn.com/chair.jpg" in html  # 쿠팡 이미지 hotlink
        assert "/go/coupang-cpx" in html  # 쿠팡 제휴 링크
        assert "/go/ali-alx" in html  # 알리 제휴 링크
        assert "쿠팡 의자" in html and "알리 의자" in html

    def test_draft_absent_from_public_build(self, built_with_draft: dict) -> None:
        # 공개 배포(include_drafts=False)엔 draft 글이 없어야 함 (E7·AI 자동 게시 금지)
        assert not (
            built_with_draft["site"] / "articles" / built_with_draft["slug"] / "index.html"
        ).exists()
        assert built_with_draft["summary"]["articles_published"] == 0

    def test_draft_excluded_from_sitemap(self, built_with_draft: dict) -> None:
        # draft slug가 (미리보기) sitemap에도 새면 안 됨 — 미발행 글 색인 위험 방지
        xml = (built_with_draft["preview"] / "sitemap.xml").read_text(encoding="utf-8")
        assert f"/articles/{built_with_draft['slug']}/" not in xml


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
        assert "데이터 수집" in html  # 수집 날짜 표기(애매한 '최근' 대체·신뢰 신호, 세션 #24)
        assert "알리 최근 판매량" not in html  # '최근'(시점 불명확) 라벨 제거
        # 제품명·가격에도 링크(이미지·버튼 외) — 클릭 영역 확대(세션 #24)
        assert html.count('href="/go/ali-ds1"') >= 4  # 이미지+이름+가격+버튼

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


class TestCleanProductName:
    """상품명 표시 정리 (세션 #34) — 알리 원본 기계번역명을 카드용으로 깔끔하게."""

    def test_comma_salad_capped_to_few_parts(self) -> None:
        # 끝없는 키워드 나열 → 앞쪽 핵심 몇 구절만(나열 차단)
        raw = "게임 의자, 리클라이닝, 컴퓨터 의자, 집, 점심 시간, 인체 공학, 기숙사, 학생, 학습, 사무실"
        out = renderer.clean_product_name(raw)
        assert out == "게임 의자 리클라이닝 컴퓨터 의자"
        assert "학생" not in out and "사무실" not in out

    def test_long_name_truncated_at_word_boundary(self) -> None:
        raw = "인체공학적 게이밍 의자 높이 조절 가능 하이백 회전식 사무실 의자 스트리머 침실용 완전 리클라이닝 패딩 팔걸이"
        out = renderer.clean_product_name(raw)
        assert len(out) <= 45
        assert out.endswith("…")

    def test_strips_invisible_and_stray_symbols(self) -> None:
        # 제로폭(U+200C)·홀로 떠도는 ° 제거 — 소스엔 코드포인트로(보이지 않는 문자 직접 금지)
        zwnj = chr(0x200C)
        raw = f"{zwnj} 빈티지 스타일 회전 의자, Smooth-360 °   회전"
        out = renderer.clean_product_name(raw)
        assert zwnj not in out
        assert "°" not in out
        assert out.startswith("빈티지 스타일 회전 의자")

    def test_empty_or_none_safe_fallback(self) -> None:
        assert renderer.clean_product_name("") == "추천 상품"
        assert renderer.clean_product_name(None) == "추천 상품"  # type: ignore[arg-type]

    def test_clean_name_passthrough(self) -> None:
        # 이미 깔끔한 이름은 그대로(불필요한 변형 없음)
        assert renderer.clean_product_name("스탠드 책상 조명") == "스탠드 책상 조명"


class TestArticleTier2Structured:
    """Tier 2 구조화(세션 #34) — structured(LLM)가 추천 장단점·빠른결론·체크포인트를 채운다."""

    @staticmethod
    def _cards() -> list[dict]:
        base = {"img_url": "", "orig": "", "disc": "", "disc_num": 0}
        return [
            {
                **base,
                "source": "aliexpress",
                "name": "A",
                "price": "5만원",
                "url": "/go/ali-1",
                "volume": 10,
                "price_num": 50000,
            },
            {
                **base,
                "source": "aliexpress",
                "name": "B",
                "price": "9만원",
                "url": "/go/ali-2",
                "volume": 5,
                "price_num": 90000,
            },
        ]

    def _ctx(self, structured: dict | None) -> dict:
        return renderer._article_page_ctx(
            slug="kw-x",
            title="T",
            summary="",
            meta_description="",
            schema_raw=None,
            body_html="<p>intro</p><h2>가이드</h2><p>본문</p>",
            persona_slug="",
            persona_title="",
            season_peak=None,
            budget_min=None,
            budget_max=None,
            products=self._cards(),
            structured=structured,
        )

    def test_structured_fills_picks_and_sections(self) -> None:
        ctx = self._ctx(
            {
                "quick_verdict": "예산 5만원이면 A, 길게 쓸 거면 B.",
                "checkpoints": [{"title": "요추 지지", "why": "허리 통증 예방"}],
                "product_notes": {
                    "ali-1": {
                        "pros": ["저렴", "발판"],
                        "cons": ["통기성 낮음"],
                        "for_who": "첫 자취",
                    },
                },
            }
        )
        assert ctx["quick_verdict"].startswith("예산")
        assert ctx["has_checkpoints"] is True
        assert ctx["checkpoints"][0]["title"] == "요추 지지"
        pick = next(
            p for p in ctx["picks_budget"] + ctx["picks_premium"] if p["url"] == "/go/ali-1"
        )
        assert pick["pros"] == ["저렴", "발판"]
        assert pick["cons"] == ["통기성 낮음"]
        assert pick["reason"] == "첫 자취"

    def test_no_structured_graceful(self) -> None:
        ctx = self._ctx(None)
        assert ctx["quick_verdict"] == ""
        assert ctx["has_checkpoints"] is False
        assert all(p["pros"] == [] for p in ctx["picks_budget"] + ctx["picks_premium"])


class TestPublishedArticleTier2:
    """발행 글(end-to-end·migration→promote→SQL→render)이 구조화로 빠른결론·체크포인트·픽 장단점 렌더."""

    def test_renders_verdict_checkpoint_pros(self, built_with_article: dict) -> None:
        slug = built_with_article["slug"]
        html = (built_with_article["out"] / "articles" / slug / "index.html").read_text(
            encoding="utf-8"
        )
        assert "빠른 결론" in html
        assert "예산 따라 의자부터" in html  # quick_verdict
        assert "요추 지지" in html  # checkpoint title
        assert "인체공학 설계" in html  # 픽 장점(pros) — pick_card에 렌더
        assert "cat-hero" in html  # 개념 이미지 배너(시각 격차 보강·세션 #34)
        assert "office-chair.webp" in html


class TestArticleAsCategory:
    """글을 카테고리 페이지 구성으로 재사용 (세션 #34) — 매핑 도출 + 컨텍스트 병합."""

    def test_cat_slug_from_concept(self) -> None:
        assert (
            renderer._cat_slug_from_concept("/static/images/concepts/office-chair.webp")
            == "office-chair"
        )
        assert renderer._cat_slug_from_concept("") == ""

    def test_article_uses_own_products_not_category(self) -> None:
        """세션 #38+#42: 픽·쿠팡·비교·요약은 글 고유, 전체 카탈로그는 글 상품 우선+카테고리 광폭.

        #38은 base(카테고리) 통째 상속으로 글이 수집한 쿠팡·픽·비교가 폐기되던 것을 바로잡았고,
        #42는 그 과교정(카탈로그까지 글 수집분 3~8개로 축소 → '고를 게 없는' 페이지, 라이브 적발:
        메쉬의자 글 전체 3개 vs 참조 카테고리 23~46개)을 바로잡는다 — 주인 지시 "참조 페이지 수준
        제품 구색으로 정형화". 카탈로그 = 글 상품(키워드 적합, 앞) + base 전체(중복 slug 제외, 뒤).
        """
        base = {
            "slug": "monitor-stand",
            "category": {"name": "모니터 받침대", "lead": "L"},
            # 카테고리 카탈로그 — 글 카탈로그 '뒤에' 광폭 구색으로 이어붙는다(#42).
            # DUP은 글 상품과 같은 slug — 중복 제거 검증용.
            "products": [{"name": "CAT_PROD", "slug": "cat-1"}, {"name": "DUP", "slug": "art-1"}],
            "picks_budget": [{"name": "CAT_PICK"}],
            "picks_premium": [],
            "has_picks": True,
            "coupang_picks": [],  # 카테고리엔 쿠팡 0
            "has_coupang": False,
            "compare": {"cols": [], "rows": []},
            "has_compare": False,
            "catalog_types": ["서랍형"],
            "data_summary": {"count": 99},
        }
        art = {
            "slug": "kw-x",
            "title": "키워드 글 제목",
            "is_draft": True,
            "quick_verdict": "QV",
            "checkpoints": [{"title": "c", "why": "w"}],
            "article": {
                "intro_html": "<h1>키워드 글 제목</h1>",
                "guide_pre": "PRE",
                "guide_post": "POST",
            },
            "picks_budget": [{"name": "ART_B1"}, {"name": "ART_B2"}],
            "picks_premium": [{"name": "ART_P1"}, {"name": "ART_P2"}],
            "has_picks": True,
            "coupang_picks": [{"name": "CP1"}, {"name": "CP2"}, {"name": "CP3"}],
            "compare": {"cols": [1, 2, 3], "rows": ["할인"]},
            "has_compare": True,
            "catalog": [{"name": "ART_CAT1", "slug": "art-1"}],
            "art_data_summary": {"count": 5},
        }
        ctx = renderer._article_as_category_ctx(art, base)
        # 정형 구성·메타는 유지
        assert ctx["is_article"] is True
        assert ctx["is_draft"] is True
        assert ctx["slug"] == "kw-x"  # URL은 글 slug
        assert ctx["category"]["name"] == "키워드 글 제목"  # H1 = 글 제목(SEO)
        assert ctx["article_intro_html"] == "<h1>키워드 글 제목</h1>"  # 대가성 고지 포함 intro
        assert ctx["quick_verdict"] == "QV"
        assert ctx["article_guide_pre"] == "PRE"
        # ★추천·비교·요약은 글 자신의 것 (base 카테고리가 아님) — #38 회귀 가드
        assert ctx["picks_budget"] == art["picks_budget"]
        assert ctx["picks_premium"] == art["picks_premium"]
        assert ctx["coupang_picks"] == art["coupang_picks"]  # 글 쿠팡 3개
        assert ctx["has_coupang"] is True  # 카테고리는 False였지만 글엔 쿠팡 있음
        assert ctx["compare"] == art["compare"]
        assert ctx["has_compare"] is True
        assert ctx["data_summary"] == art["art_data_summary"]
        # ★전체 카탈로그 = 글 상품 먼저 + 카테고리 광폭 구색(같은 slug 중복 제거) — #42 회귀 가드
        assert [it["name"] for it in ctx["products"]] == ["ART_CAT1", "CAT_PROD"]
        assert ctx["catalog_types"] == ["서랍형"]  # 타입 필터 칩 복원(참조 페이지와 동일 UX)
        # ★화면 빵부스러기용 상위 카테고리(#42) — 홈>카테고리>{카테고리}>글 탐색·SEO 계층
        assert ctx["parent_category"] == {
            "name": "모니터 받침대",
            "url": "/categories/monitor-stand/",
        }

    def test_attach_guides_to_groups(self) -> None:
        """세션 #42: 카테고리 인덱스 카드에 세부 가이드(발행 글) 칩 자동 부착 — 좀비 경로 차단.

        상단 메뉴 '카테고리' 인덱스에서 발행 글 링크가 0이라(라이브 적발: 메쉬의자 글)
        cap개까지 칩 노출 + 초과분 '+N개'. 새 글 발행 시 렌더가 자동 반영(무인)."""
        groups: list[dict] = [
            {
                "name": "홈오피스",
                "cards": [{"slug": "office-chair"}, {"slug": "desk"}],
            }
        ]
        guides: dict[str, list[dict]] = {
            "office-chair": [{"label": f"가이드{i}", "url": f"/articles/kw-{i}/"} for i in range(5)]
        }
        renderer._attach_guides_to_groups(groups, guides, cap=4)
        chair, desk = groups[0]["cards"]
        assert len(chair["guides"]) == 4  # cap 초과분 절단
        assert chair["guides_more"] == 1  # '+1개 →' 링크
        assert desk["guides"] == [] and desk["guides_more"] == 0  # 글 없는 카테고리 graceful

    def test_compare_columns_match_picks_count(self) -> None:
        """세션 #38: 비교표 열 수 == 추천 픽 수(정형성). 옛 기본 limit 6은 picks 8을 6으로 잘랐다."""
        picks = [
            {
                "name": f"P{i}",
                "type": "t",
                "tier": "budget",
                "price": "1만",
                "disc": "10%",
                "volume": "100",
            }
            for i in range(8)
        ]
        cmp = renderer._build_article_compare(picks, limit=len(picks))
        assert len(cmp["cols"]) == 8  # 8개 픽 → 8열 (옛 limit 6이면 6)

    def test_article_featured_follows_per_tier(self) -> None:
        """글 픽 개수 = featured_per_tier (글·카테고리 통일·#38). 옛 k=4 하드코딩이면 항상 4였다."""
        cards = [{"volume": i, "disc_num": 0} for i in range(10)]
        assert len(renderer._article_featured(cards, 4)) == 4  # 티어당 4 → 총 8
        assert len(renderer._article_featured(cards, 3)) == 3  # 티어당 3 → 총 6 (설정 따라감)


class TestArticleTitleTag:
    """세션 #44: 카테고리 매핑 글의 <title> = 글 제목 — 근본수정 가드.

    category.html의 title 블록이 카테고리 guide_title을 상속해, 같은 카테고리의 발행 글
    전부가 동일 <title>이 됐다(중복 제목·og:title/JSON-LD headline과 불일치 — 라이브 적발:
    서재책상 글 <title>=컴퓨터 책상 고르는 법…). 글은 글 제목, 카테고리 페이지는 기존 그대로.
    """

    def test_mapped_article_title_is_article_title(self, tmp_path: Path) -> None:
        built = _build_article_site(tmp_path, publish_category=True)
        html = (built["out"] / "articles" / built["slug"] / "index.html").read_text(
            encoding="utf-8"
        )
        # 카테고리 매핑 경로로 렌더됐는지(빵부스러기 상위 카테고리 존재) 먼저 보장
        assert "/categories/office-chair/" in html
        assert "<title>홈오피스 50만원 세팅 | 혼살림</title>" in html  # 글 제목
        assert "고르는 법 | 혼살림</title>" not in html  # 카테고리 제목 상속 아님

    def test_category_page_title_unchanged(self, tmp_path: Path) -> None:
        # 카테고리 페이지 <title>은 기존 그대로(guide_title 폴백) — 이미 색인된 제목 불변
        built = _build_article_site(tmp_path, publish_category=True)
        cat = (built["out"] / "categories" / "office-chair" / "index.html").read_text(
            encoding="utf-8"
        )
        assert "<title>사무용 의자 고르는 법 | 혼살림</title>" in cat
