"""scenario_loader — DB scenarios → 수집 큐.

출처: ARCH §3 + BACKEND §2-1 + SCENARIOS §8 + DB §7 [확정].

흐름:
1. scenarios 테이블에서 active=1·priority DESC 정렬
2. 이미 drafts에 collected/enriched/validated/approved 상태로 진행 중인 시나리오 제외
3. 남은 시나리오를 우선순위 순으로 반환 — collector.coupang가 처리할 큐
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

# scenarios가 drafts로 이미 진행 중인지 판단할 때 제외할 상태
IN_PROGRESS_STATES: tuple[str, ...] = ("collected", "enriched", "validated", "approved")


@dataclass(frozen=True)
class ScenarioRow:
    """수집 큐 항목 — scenarios + 페르소나 슬러그 조인 결과."""

    id: int
    slug: str
    title_ko: str
    priority: int
    persona_slug: str
    budget_min_krw: int | None
    budget_max_krw: int | None
    season_peak: str | None


def _row_to_scenario(row: sqlite3.Row | tuple) -> ScenarioRow:
    return ScenarioRow(
        id=int(row[0]),
        slug=str(row[1]),
        title_ko=str(row[2]),
        priority=int(row[3]),
        persona_slug=str(row[4]),
        budget_min_krw=int(row[5]) if row[5] is not None else None,
        budget_max_krw=int(row[6]) if row[6] is not None else None,
        season_peak=str(row[7]) if row[7] is not None else None,
    )


def list_active_scenarios(conn: sqlite3.Connection, limit: int = 50) -> list[ScenarioRow]:
    """active=1 시나리오 전체 — priority DESC 정렬.

    drafts 진행 상태 무관. dashboard·전체 조회용.
    """
    cur = conn.execute(
        """
        SELECT s.id, s.slug, s.title_ko, s.priority, p.slug,
               s.budget_min_krw, s.budget_max_krw, s.season_peak
        FROM scenarios s
        JOIN personas p ON s.persona_id = p.id
        WHERE s.active = 1
        ORDER BY s.priority DESC, s.id ASC
        LIMIT ?
        """,
        (limit,),
    )
    return [_row_to_scenario(r) for r in cur.fetchall()]


def next_scenarios_for_collection(conn: sqlite3.Connection, limit: int = 10) -> list[ScenarioRow]:
    """수집 큐 — drafts 진행 중·발행됨이 아닌 active 시나리오.

    제외 조건:
    - status IN ('collected','enriched','validated','approved')
      → 이미 어딘가에서 처리 중
    - status = 'published' 는 포함 (재집행 가능 — 후속 시즌 갱신용)
    - status = 'rejected' 는 포함 (재시도 가능 — 단 사용자가 검토 후 결정)
    """
    placeholders = ",".join("?" * len(IN_PROGRESS_STATES))
    query = f"""
        SELECT s.id, s.slug, s.title_ko, s.priority, p.slug,
               s.budget_min_krw, s.budget_max_krw, s.season_peak
        FROM scenarios s
        JOIN personas p ON s.persona_id = p.id
        WHERE s.active = 1
          AND s.id NOT IN (
              SELECT scenario_id FROM drafts WHERE status IN ({placeholders})
          )
        ORDER BY s.priority DESC, s.id ASC
        LIMIT ?
    """  # noqa: S608
    cur = conn.execute(query, (*IN_PROGRESS_STATES, limit))
    return [_row_to_scenario(r) for r in cur.fetchall()]
