"""common.size_caps — docs/ 동적 파일 size cap 정의·점검.

출처: CLAUDE.md §3 5파일 시스템 cap — 세션 #6 추가.

대상 파일·cap (CLAUDE.md §3):
    docs/STATE.md   — 10 KB
    docs/EVENTS.md  — 20 KB (초과 시 가장 옛 세션 archive 회전)
    docs/TODO.md    —  5 KB

DECISIONS.md / CLAUDE.md는 무제한이므로 제외.

사용 진입점:
    scripts/check_size_caps.py  — CLI 헬퍼
    src/cli.py doctor §14       — 운영 헬스 체크 통합
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CAPS: dict[str, int] = {
    "docs/STATE.md": 10 * 1024,
    "docs/EVENTS.md": 20 * 1024,
    "docs/TODO.md": 5 * 1024,
}


def check(project_root: Path | None = None) -> tuple[int, list[dict[str, Any]]]:
    """점검 실행.

    Args:
        project_root: 프로젝트 루트 override (테스트용). 기본은 PROJECT_ROOT.

    Returns:
        (exit_code, results) — exit_code: 0 OK / 1 cap 초과 / 2 파일 누락.
    """
    root = project_root or PROJECT_ROOT
    results: list[dict[str, Any]] = []
    missing = False
    over = False

    for rel_path, cap in CAPS.items():
        path = root / rel_path
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
    """사람 판독용 출력 (CLI·doctor 공통)."""
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
