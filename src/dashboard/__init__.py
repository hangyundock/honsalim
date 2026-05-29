"""dashboard 모듈 — 로컬 미리보기·1클릭 승인 (BACKEND §2-6).

- render: drafts(collected~published)를 단일 HTML로 렌더 (data/dashboard/index.html)
- approve: 1클릭 승인 트리거 (state_machine.transition + .approve/<id>.flag)
- 단순 단일 파일 HTML — Jinja2 미사용, Flask 서버 없음 (단일 사용자 운영)
"""

from . import approve, render

__all__ = ["approve", "render"]
