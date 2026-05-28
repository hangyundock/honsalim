"""check_size_caps.py — docs/ 동적 파일 size cap 자동 점검.

출처: CLAUDE.md §3 5파일 시스템 cap 정의 — 세션 #6 추가.

대상 파일·cap (CLAUDE.md §3):
    docs/STATE.md   — 10 KB
    docs/EVENTS.md  — 20 KB (초과 시 가장 옛 세션 archive 회전)
    docs/TODO.md    —  5 KB

DECISIONS.md / CLAUDE.md는 무제한이므로 제외.

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
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CAPS: dict[str, int] = {
    "docs/STATE.md": 10 * 1024,
    "docs/EVENTS.md": 20 * 1024,
    "docs/TODO.md": 5 * 1024,
}


def check() -> tuple[int, list[dict[str, Any]]]:
    """점검 실행. (exit_code, results) 반환."""
    results: list[dict[str, Any]] = []
    missing = False
    over = False

    for rel_path, cap in CAPS.items():
        path = PROJECT_ROOT / rel_path
        if not path.exists():
            results.append({"path": rel_path, "exists": False, "size": 0, "cap": cap, "ratio": 0.0})
            missing = True
            continue

        size = path.stat().st_size
        ratio = size / cap
        is_over = size > cap
        if is_over:
            over = True
        results.append(
            {
                "path": rel_path,
                "exists": True,
                "size": size,
                "cap": cap,
                "ratio": round(ratio, 3),
                "over": is_over,
            }
        )

    if missing:
        return 2, results
    if over:
        return 1, results
    return 0, results


def format_human(results: list[dict[str, Any]]) -> str:
    """사람 판독용 출력."""
    lines: list[str] = []
    lines.append("=== docs/ size cap 점검 (CLAUDE.md §3) ===")
    for r in results:
        path = r["path"]
        if not r["exists"]:
            lines.append(f"[FAIL] {path} — 파일 없음")
            continue
        size_kb = r["size"] / 1024
        cap_kb = r["cap"] / 1024
        pct = r["ratio"] * 100
        status = "OVER" if r.get("over") else "OK"
        marker = "[FAIL]" if r.get("over") else "[OK]"
        lines.append(
            f"{marker} {path:<18} {size_kb:6.2f} / {cap_kb:5.1f} KB ({pct:5.1f}%) {status}"
        )
    return "\n".join(lines)


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
