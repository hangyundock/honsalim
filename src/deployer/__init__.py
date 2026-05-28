"""deployer — build/ → GitHub push 또는 wrangler 직접 배포.

출처: BACKEND §2-7 + DECISIONS H4·H5 [확정].

원칙:
- 평상시 수동 배포: git_push는 사용자 명시 승인 후만 (H4)
- 자동 게시 (스케줄러): actor='system' 호출 가능 — 승인 큐 발행 (DECISIONS C6)
- 모든 함수 dry_run=True 기본 (외부 영향 차단)
"""

from __future__ import annotations

from .git_push import git_push
from .verify import verify_deploy
from .wrangler import wrangler_deploy

__all__ = ("git_push", "verify_deploy", "wrangler_deploy")
