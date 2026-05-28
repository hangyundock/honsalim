"""tracker — D1 클릭 집계 + 로컬 SQLite import.

출처: BACKEND §2-8 [확정].

흐름:
1. Cloudflare D1 clicks 테이블 → 일별 집계
2. SQLite articles.view_count_cached 갱신
3. weekly·monthly 리포트 → dashboard

dry_run=True 기본 — D1 API 호출은 명시 승인 후.
"""

from __future__ import annotations

from .d1_aggregator import aggregate, export_to_sqlite

__all__ = ("aggregate", "export_to_sqlite")
