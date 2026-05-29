"""builder.renderer 회귀 테스트 — DB seed → 정적 사이트 렌더 (DECISIONS G4).

render_site는 db_path에서 자체 연결을 열므로 파일 기반 임시 DB를 사용한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from builder import renderer
from common import db


@pytest.fixture()
def built(tmp_path: Path) -> dict:
    """임시 DB에 migrate+seed 후 임시 디렉토리로 렌더. summary + out 반환."""
    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    out = tmp_path / "site"
    summary = renderer.render_site(out_dir=out, db_path=db_path)
    return {"summary": summary, "out": out}


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
        assert html.count('class="s-card"') == 10
        assert 'data-value="2-3월"' in html  # season_peak 실값 기반 필터

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
