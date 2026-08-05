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
    """build/site/articles/<slug>/index.html 생성. pages = {slug: [링크 대상 slug, ...]}"""
    for slug, links in pages.items():
        d = root / "build" / "site" / "articles" / slug
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
