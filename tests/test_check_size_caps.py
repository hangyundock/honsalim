"""tests/test_check_size_caps.py — size cap 점검 회귀.

출처: 세션 #6 추가 — common.size_caps 모듈 + scripts/ CLI wrapper + doctor §14.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "check_size_caps.py"

# src/를 path에 추가 (conftest와 동일 패턴)
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from common import size_caps  # noqa: E402


class TestCommonModule:
    def test_caps_dict_keys(self) -> None:
        assert set(size_caps.CAPS.keys()) == {
            "docs/STATE.md",
            "docs/EVENTS.md",
            "docs/TODO.md",
        }

    def test_caps_values_bytes(self) -> None:
        assert size_caps.CAPS["docs/STATE.md"] == 10 * 1024
        assert size_caps.CAPS["docs/EVENTS.md"] == 20 * 1024
        assert size_caps.CAPS["docs/TODO.md"] == 5 * 1024

    def test_check_returns_tuple(self) -> None:
        code, results = size_caps.check()
        assert isinstance(code, int)
        assert isinstance(results, list)
        assert len(results) == 3

    def test_check_results_schema(self) -> None:
        _, results = size_caps.check()
        for r in results:
            assert "path" in r
            assert "exists" in r
            assert "size" in r
            assert "cap" in r
            assert "ratio" in r

    def test_format_human_output(self) -> None:
        _, results = size_caps.check()
        text = size_caps.format_human(results)
        assert "docs/" in text
        assert "STATE.md" in text
        assert "EVENTS.md" in text
        assert "TODO.md" in text

    def test_check_missing_file(self, tmp_path: Path) -> None:
        """대상 파일 없는 임시 디렉토리에서 exit_code=2."""
        code, results = size_caps.check(project_root=tmp_path)
        assert code == 2
        for r in results:
            assert r["exists"] is False

    def test_check_over_cap(self, tmp_path: Path) -> None:
        """STATE.md를 cap 초과로 만들면 exit_code=1."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "STATE.md").write_text("x" * (11 * 1024), encoding="utf-8")
        (docs_dir / "EVENTS.md").write_text("ok", encoding="utf-8")
        (docs_dir / "TODO.md").write_text("ok", encoding="utf-8")
        code, results = size_caps.check(project_root=tmp_path)
        assert code == 1
        state_result = next(r for r in results if r["path"] == "docs/STATE.md")
        assert state_result["over"] is True


class TestCliWrapper:
    def test_cli_runs(self) -> None:
        """본 프로젝트 docs/ 파일 모두 존재해야 PASS (코드 0)."""
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode in (
            0,
            1,
        ), f"unexpected exit {result.returncode}: {result.stdout}\n{result.stderr}"
        assert "STATE.md" in result.stdout
        assert "EVENTS.md" in result.stdout
        assert "TODO.md" in result.stdout

    def test_cli_json(self) -> None:
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPT), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert "exit_code" in data
        assert "results" in data
        assert len(data["results"]) == 3
