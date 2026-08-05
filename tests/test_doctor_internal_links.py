"""doctor §17 내부링크 정합 회귀 테스트 (세션 #51).

★왜 검사기 자체를 테스트하나: §17은 "글↔글 링크 0"이라는 **사람이 라이브를 손으로 뜯어야
발견되던 결함**을 자동 감지하려고 넣은 것이다. 검사기가 조용히 망가지면(경로 오타·정규식
변경) 결함이 있어도 통과해 버려 감지 장치가 무의미해진다. 그래서 '고아를 실제로 잡는지'를
고정한다.

doctor 전체 실행은 환경 의존이 커서(test_cli.py 서두) 여기서는 순수 함수만 격리 검증한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import cli


def _site(root: Path, pages: dict[str, list[str]]) -> None:
    """build/site/articles/<slug>/index.html 생성. pages = {slug: [링크 대상 slug, ...]}

    ★#51 리팩터 후 검사는 사이트 **전체**를 보므로 홈(build/site/index.html)이 있어야 한다.
    없으면 '빌드 전'으로 판단해 건너뛴다(그 동작 자체는 test_skips_when_not_built가 고정).
    """
    home = root / "build" / "site"
    home.mkdir(parents=True, exist_ok=True)
    (home / "index.html").write_text("<html><body>home</body></html>", encoding="utf-8")
    for slug, links in pages.items():
        d = home / "articles" / slug
        d.mkdir(parents=True, exist_ok=True)
        body = "".join(f'<a href="/articles/{t}/">{t}</a>' for t in links)
        (d / "index.html").write_text(f"<html><body>{body}</body></html>", encoding="utf-8")


class TestCheckInternalLinks:
    def test_detects_orphans(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """inbound 0인 글이 있으면 FAIL — 이게 #51에서 40일간 방치됐던 실제 상태다."""
        _site(tmp_path, {"a": ["b"], "b": ["a"], "orphan": ["a"]})  # orphan은 아무도 안 가리킴
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        ok = cli._check_internal_links()
        assert ok is False
        assert "orphan" in capsys.readouterr().out

    def test_detects_dead_ends(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """outbound 0(다른 글로 못 나감)도 FAIL — 렌더 경로 둘 중 하나만 고친 경우를 잡는다."""
        _site(tmp_path, {"a": ["b"], "b": ["a"], "stuck": []})
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_internal_links() is False
        assert "stuck" in capsys.readouterr().out

    def test_passes_when_fully_linked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _site(tmp_path, {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]})
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_internal_links() is True
        assert "고아 0" in capsys.readouterr().out

    def test_self_link_does_not_count_as_inbound(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """자기 자신을 가리키는 링크로 고아 판정을 피해갈 수 없다(가짜 통과 차단)."""
        _site(tmp_path, {"a": ["b"], "b": ["a"], "fake": ["fake"]})
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_internal_links() is False

    def test_skips_when_not_built(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """빌드 전(fresh checkout)이면 건너뛴다 — doctor는 멈추지 않는다(§0)."""
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_internal_links() is True
        assert "건너뜀" in capsys.readouterr().out

    def test_single_article_is_not_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """글이 1편뿐이면 형제가 있을 수 없다 — 오탐 금지."""
        _site(tmp_path, {"only": []})
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_internal_links() is True


def _page(
    root: Path,
    rel: str,
    *,
    title: str = "제목입니다",
    canonical: str | None = None,
    h1: int = 1,
    og_image: bool = True,
    noindex: bool = False,
    extra: str = "",
) -> None:
    """온페이지 SEO 점검용 최소 HTML 생성."""
    url = "/" + rel + "/" if rel else "/"
    can = canonical if canonical is not None else f"https://honsallim.com{url}"
    d = root / "build" / "site" / rel if rel else root / "build" / "site"
    d.mkdir(parents=True, exist_ok=True)
    head = f'<title>{title}</title><link rel="canonical" href="{can}">'
    if og_image:
        head += '<meta property="og:image" content="https://honsallim.com/x.webp">'
    if noindex:
        head += '<meta name="robots" content="noindex, follow">'
    head += '<meta name="description" content="설명이 충분히 들어간 메타 디스크립션입니다.">'
    body = "".join(f"<h1>H{i}</h1>" for i in range(h1)) + extra
    (d / "index.html").write_text(f"<html><head>{head}</head><body>{body}</body></html>", "utf-8")


def _sitemap(root: Path, urls: list[str]) -> None:
    locs = "".join(f"<loc>https://honsallim.com{u}</loc>" for u in urls)
    (root / "build" / "site" / "sitemap.xml").write_text(f"<urlset>{locs}</urlset>", "utf-8")


class TestCheckSeoOnpage:
    """doctor §19 — #51 수동 감사에서 '전 42페이지 og:image 누락'을 처음 발견했다.

    매크로는 og_image를 지원하는데 렌더 호출부가 안 넘긴 배선 누락이었고, twitter:card가
    'summary'로 떨어져 공유 카드가 텍스트만 나왔다. 사람이 HTML을 뜯어야 보이던 결함이라
    검사를 고정한다. 오탐(중복 title이지만 canonical로 통합된 경우)도 함께 고정.
    """

    def test_detects_missing_og_image(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _page(tmp_path, "", og_image=False)
        _sitemap(tmp_path, ["/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        assert "og:image" in capsys.readouterr().out

    def test_detects_missing_canonical_and_bad_h1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _page(tmp_path, "", canonical="", h1=2)
        _sitemap(tmp_path, ["/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        out = capsys.readouterr().out
        assert "canonical 없음" in out and "H1 2개" in out

    def test_detects_affiliate_link_without_rel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """제휴 링크 rel 누락은 구글 정책 위반 — 수익 몰수까지 가는 경로라 FAIL."""
        _page(tmp_path, "", extra='<a href="/go/ali-1">상품</a>')
        _sitemap(tmp_path, ["/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        assert "nofollow" in capsys.readouterr().out

    def test_detects_broken_jsonld(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _page(tmp_path, "", extra='<script type="application/ld+json">{망가진</script>')
        _sitemap(tmp_path, ["/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        assert "JSON-LD" in capsys.readouterr().out

    def test_noindex_page_is_exempt(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """noindex 페이지는 색인 대상이 아니므로 온페이지·sitemap 대조에서 제외(오탐 방지)."""
        _page(tmp_path, "")
        _page(tmp_path, "reviews/x", noindex=True, og_image=False, canonical="")
        _sitemap(tmp_path, ["/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is True

    def test_duplicate_title_with_canonical_is_not_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """제목이 같아도 한쪽이 다른 쪽을 canonical로 가리키면 정상 처리 — #51 /personas/ 오탐."""
        _page(tmp_path, "personas/a", title="같은 제목")
        _page(
            tmp_path, "personas", title="같은 제목", canonical="https://honsallim.com/personas/a/"
        )
        _sitemap(tmp_path, ["/personas/a/", "/personas/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is True

    def test_sitemap_pointing_to_missing_page_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """sitemap이 없는 URL을 가리키면 크롤러가 404를 먹는다 — 색인 신뢰 손상."""
        _page(tmp_path, "")
        _sitemap(tmp_path, ["/", "/사라진페이지/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        assert "산출물 없음" in capsys.readouterr().out

    def test_clean_site_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _page(tmp_path, "", title="홈 제목입니다")
        _page(tmp_path, "about", title="소개 제목입니다")
        _sitemap(tmp_path, ["/", "/about/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is True
        assert "온페이지 SEO" in capsys.readouterr().out

    def test_real_duplicate_self_canonical_titles_fail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """둘 다 자기 자신을 canonical로 두면서 제목이 같으면 진짜 중복 — 구글이 하나를 버린다."""
        _page(tmp_path, "", title="홈 제목입니다")  # 홈이 없으면 검사가 '빌드 전'으로 건너뛴다
        _page(tmp_path, "a", title="완전히 같은 제목")
        _page(tmp_path, "b", title="완전히 같은 제목")
        _sitemap(tmp_path, ["/", "/a/", "/b/"])
        monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
        assert cli._check_seo_onpage() is False
        assert "title 중복" in capsys.readouterr().out
