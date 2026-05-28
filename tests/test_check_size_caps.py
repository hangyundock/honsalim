"""tests/test_check_size_caps.py — scripts/check_size_caps 회귀.

출처: 세션 #6 추가 — size cap 자동 점검 도구 회귀.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "check_size_caps.py"


def _import_module():
    """check_size_caps 모듈 동적 import (scripts/ 비패키지)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_size_caps", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckFunction:
    def test_caps_dict_keys(self) -> None:
        mod = _import_module()
        assert set(mod.CAPS.keys()) == {
            "docs/STATE.md",
            "docs/EVENTS.md",
            "docs/TODO.md",
        }

    def test_caps_values_bytes(self) -> None:
        mod = _import_module()
        assert mod.CAPS["docs/STATE.md"] == 10 * 1024
        assert mod.CAPS["docs/EVENTS.md"] == 20 * 1024
        assert mod.CAPS["docs/TODO.md"] == 5 * 1024

    def test_check_returns_tuple(self) -> None:
        mod = _import_module()
        code, results = mod.check()
        assert isinstance(code, int)
        assert isinstance(results, list)
        assert len(results) == 3

    def test_check_results_schema(self) -> None:
        mod = _import_module()
        _, results = mod.check()
        for r in results:
            assert "path" in r
            assert "exists" in r
            assert "size" in r
            assert "cap" in r
            assert "ratio" in r

    def test_format_human_output(self) -> None:
        mod = _import_module()
        _, results = mod.check()
        text = mod.format_human(results)
        assert "docs/" in text
        assert "STATE.md" in text
        assert "EVENTS.md" in text
        assert "TODO.md" in text


class TestCliExecution:
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
