"""dashboard.preview_server 회귀 테스트 (세션 #34).

미리보기를 로컬 HTTP로 서빙해 절대경로(/static·이미지)가 정상 해석되는지 검증 —
file://에서 무스타일로 깨지던 EVENTS #30 한계의 근본 해소. 순수 stdlib(PyQt 비의존).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from dashboard import preview_server


def _fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as r:  # noqa: S310 — 127.0.0.1 로컬 전용
        data: bytes = r.read()
    return data.decode("utf-8")


def _make_site(root: Path) -> None:
    (root / "static" / "css").mkdir(parents=True)
    (root / "static" / "css" / "tokens.css").write_text("body{color:red}", encoding="utf-8")
    (root / "index.html").write_text("<html>HOME</html>", encoding="utf-8")
    art = root / "articles" / "kw-foo"
    art.mkdir(parents=True)
    (art / "index.html").write_text("<html>ARTICLE</html>", encoding="utf-8")


def test_serves_index_over_http(tmp_path: Path) -> None:
    _make_site(tmp_path)
    base = preview_server.serve(tmp_path)
    assert base.startswith("http://127.0.0.1:")
    assert "HOME" in _fetch(base + "/")


def test_absolute_static_path_resolves(tmp_path: Path) -> None:
    # ★핵심: file://에서 깨지던 절대경로 /static/...이 HTTP 루트에선 정상 해석(라이브와 동일)
    _make_site(tmp_path)
    base = preview_server.serve(tmp_path)
    assert "color:red" in _fetch(base + "/static/css/tokens.css")


def test_url_for_article_directory(tmp_path: Path) -> None:
    _make_site(tmp_path)
    target = tmp_path / "articles" / "kw-foo" / "index.html"
    url = preview_server.url_for(tmp_path, target)
    assert url.endswith("/articles/kw-foo/")
    assert "ARTICLE" in _fetch(url)


def test_url_for_index_is_root(tmp_path: Path) -> None:
    _make_site(tmp_path)
    url = preview_server.url_for(tmp_path, tmp_path / "index.html")
    assert "HOME" in _fetch(url)


def test_same_dir_reuses_server(tmp_path: Path) -> None:
    _make_site(tmp_path)
    assert preview_server.serve(tmp_path) == preview_server.serve(tmp_path)
