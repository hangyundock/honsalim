"""check_size_caps.py — docs/ 동적 파일 size cap 자동 점검 CLI.

출처: CLAUDE.md §3 5파일 시스템 cap — 세션 #6 추가.

핵심 로직은 src/common/size_caps에 존재. 본 파일은 CLI wrapper.

사용:
    python scripts/check_size_caps.py
    python scripts/check_size_caps.py --json    # 머신 판독용 출력

종료 코드:
    0 — 모두 cap 내
    1 — 1건 이상 cap 초과 (회전·정돈 필요)
    2 — 파일 없음 (구조 손상)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from common.size_caps import check, format_human  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="docs/ size cap 자동 점검")
    parser.add_argument("--json", action="store_true", help="JSON 출력 (머신 판독)")
    args = parser.parse_args()

    code, results = check()

    if args.json:
        print(json.dumps({"exit_code": code, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(format_human(results))
        if code == 1:
            print("\n→ EVENTS.md 초과 시 archive 회전, STATE/TODO 초과 시 정돈 필요.")
        elif code == 2:
            print("\n→ 누락 파일 복구 필요 (CLAUDE.md §3 5파일 시스템).")

    return code


if __name__ == "__main__":
    sys.exit(main())
