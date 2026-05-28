"""run_tests.py — pytest 미설치 환경 일괄 회귀 실행 헬퍼.

출처: 세션 #5 추가 — pytest 환경 없는 운영자 머신에서도 일괄 회귀 검증.

동작:
    tests/test_*.py 모두 import → Test* 클래스의 test_* 메서드 자동 수집·실행.
    pytest 픽스처(tmp_path 등) 사용 케이스는 자동 SKIP (인자 개수 1 초과 시).

사용:
    python scripts/run_tests.py
    python scripts/run_tests.py tests/test_validator.py  # 특정 파일
    python scripts/run_tests.py --verbose                # 케이스별 출력

종료 코드:
    0 — 모두 PASS (SKIP 허용)
    1 — 1건 이상 FAIL
    2 — 컬렉션 오류 (import 실패 등)
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

# src/ + tests/ sys.path 보정 — conftest.py와 동일 동작
for p in (SRC_DIR, TESTS_DIR):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Windows 콘솔 cp949 회피
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _load_test_module(path: Path) -> Any:
    """tests/test_*.py 모듈 로드."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"spec load 실패: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collect_tests(module: Any) -> list[tuple[str, Any]]:
    """모듈에서 Test* 클래스 → test_* 메서드 수집.

    반환: [(case_name, callable), ...]
    """
    cases: list[tuple[str, Any]] = []
    for cls_name, cls in inspect.getmembers(module, inspect.isclass):
        if not cls_name.startswith("Test"):
            continue
        # 클래스가 본 모듈에서 정의된 것만
        if cls.__module__ != module.__name__:
            continue
        instance = None
        for method_name, method in inspect.getmembers(cls, inspect.isfunction):
            if not method_name.startswith("test_"):
                continue
            # 인자 개수 검사 — self 외 인자 있으면 pytest 픽스처 의존 (SKIP)
            sig = inspect.signature(method)
            params = list(sig.parameters.values())
            non_self = [p for p in params if p.name != "self"]
            if non_self:
                cases.append((f"{cls_name}.{method_name}", _make_skip(method_name, len(non_self))))
                continue
            if instance is None:
                instance = cls()
            cases.append((f"{cls_name}.{method_name}", getattr(instance, method_name)))
    return cases


def _make_skip(name: str, arg_count: int) -> Any:
    """pytest 픽스처 의존 케이스의 placeholder."""

    def _skip() -> None:
        raise _SkipException(f"pytest 픽스처 필요 ({arg_count} 인자)")

    _skip.__name__ = name
    return _skip


class _SkipException(Exception):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_tests")
    parser.add_argument("files", nargs="*", help="특정 test 파일 (없으면 tests/ 전부)")
    parser.add_argument("--verbose", action="store_true", help="케이스별 출력")
    args = parser.parse_args(argv)

    if args.files:
        targets = [Path(f).resolve() for f in args.files]
    else:
        targets = sorted(TESTS_DIR.glob("test_*.py"))

    if not targets:
        print("[ERROR] tests/test_*.py 없음")
        return 2

    total = passed = failed = skipped = 0
    failures: list[tuple[str, str]] = []

    for path in targets:
        try:
            module = _load_test_module(path)
        except Exception as e:
            print(f"[IMPORT FAIL] {path.name}: {type(e).__name__}: {e}")
            return 2

        cases = _collect_tests(module)
        if not cases:
            continue

        print(f"\n--- {path.name} ({len(cases)} 케이스) ---")
        for case_name, fn in cases:
            total += 1
            try:
                fn()
                passed += 1
                if args.verbose:
                    print(f"  PASS {case_name}")
            except _SkipException as e:
                skipped += 1
                if args.verbose:
                    print(f"  SKIP {case_name} — {e}")
            except Exception as e:
                failed += 1
                tb = traceback.format_exc()
                failures.append((f"{path.name}::{case_name}", tb))
                print(f"  FAIL {case_name}: {type(e).__name__}: {e}")

    print("\n=== 종합 ===")
    print(f"  total={total} pass={passed} fail={failed} skip={skipped}")

    if failures:
        print("\n=== FAIL 상세 ===")
        for fid, tb in failures[:5]:
            print(f"\n[{fid}]\n{tb}")
        if len(failures) > 5:
            print(f"... 추가 {len(failures) - 5}건")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
