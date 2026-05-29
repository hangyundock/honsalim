"""dashboard.approve — 1클릭 승인 트리거 (BACKEND §2-6 [확정]).

state_machine.transition(validated → approved) + .approve/<id>.flag 파일 생성.
flag 파일은 scheduler·deployer가 polling 시 사용 (옵션, 본 모듈은 생성만).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from writer import state_machine

DEFAULT_FLAG_DIR = Path("data/dashboard/.approve")


def approve(
    conn: sqlite3.Connection,
    draft_id: int,
    user_note: str | None = None,
    flag_dir: Path | str = DEFAULT_FLAG_DIR,
) -> Path:
    """validated → approved 전이 + flag 파일 생성. Returns: flag 경로.

    cli cmd_approve와 흐름 동일하지만 dashboard 진입점에서도 사용 가능 (대칭).
    state_machine.IllegalStateError는 상위로 전파 (예: validated 아닌 상태).
    """
    reason = "dashboard approve" + (f" — {user_note}" if user_note else "")
    state_machine.transition(conn, draft_id, "approved", reason=reason)

    flag_path = Path(flag_dir) / f"{draft_id}.flag"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_content = {
        "draft_id": draft_id,
        "approved_at": datetime.now().isoformat(timespec="seconds"),
        "user_note": user_note or "",
    }
    import json

    flag_path.write_text(json.dumps(flag_content, ensure_ascii=False, indent=2), encoding="utf-8")
    return flag_path
