"""writer.keyword_queue — 키워드 발행 큐 로직 (세션 #25).

운영 대시보드 "대기 키워드"의 추가·상태 전이·시나리오 브리지. PyQt 비의존(테스트 가능).

핵심 [확정 #25]: 키워드(주제)에서 **시나리오를 자동 파생**해 기존 drafts→articles 발행
기계(enrich·5게이트·promote)를 그대로 재사용한다. enrich가 scenario+persona 조인을 요구하므로
파생 시나리오에는 페르소나가 필요하다(keyword.persona_id → 기본 페르소나 순으로 해결).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from typing import Any

VALID_CHANNELS = frozenset({"ali", "coupang", "both"})
VALID_STATUSES = frozenset({"pending", "generating", "drafted", "published", "disabled", "failed"})


def slugify(text: str, fallback_prefix: str = "kw") -> str:
    """키워드 → URL-safe slug. ASCII 영숫자만; 한글 등으로 비면 키워드 해시 기반 안정 slug."""
    norm = unicodedata.normalize("NFKD", text or "")
    ascii_only = norm.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    if not s:
        h = hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:8]  # noqa: S324 (식별용·비보안)
        s = f"{fallback_prefix}-{h}"
    return s[:60]


def _unique_slug(conn: sqlite3.Connection, table: str, base: str) -> str:
    """table.slug 충돌 시 -2, -3 … 접미사. table은 코드 화이트리스트만."""
    assert table in {"keyword_queue", "scenarios"}  # noqa: S101 — 내부 호출 가드(주입 방지)
    slug = base
    n = 2
    while conn.execute(
        f"SELECT 1 FROM {table} WHERE slug = ?",  # noqa: S608 — table 화이트리스트
        (slug,),
    ).fetchone():
        slug = f"{base}-{n}"
        n += 1
    return slug


def add_keyword(
    conn: sqlite3.Connection,
    keyword: str,
    *,
    slug: str | None = None,
    channel: str = "ali",
    persona_id: int | None = None,
    budget_min_krw: int | None = None,
    budget_max_krw: int | None = None,
    target_products: list[dict[str, Any]] | None = None,
    notes: str | None = None,
    score: float = 0.0,
    priority: int = 0,
) -> int:
    """키워드 큐에 1건 추가 (status='pending'). 반환: 새 keyword_queue id.

    target_products: 운영자가 미리 선택/입력한 추천 상품(JSON 직렬화). 쿠팡 수동 입력 포함.
    """
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("keyword가 비어 있습니다")
    if channel not in VALID_CHANNELS:
        raise ValueError(f"channel은 {sorted(VALID_CHANNELS)} 중 하나여야 합니다: {channel!r}")
    base_slug = (slug or slugify(keyword)).strip() or slugify(keyword)
    uslug = _unique_slug(conn, "keyword_queue", base_slug)
    tp_json = (
        json.dumps(target_products, ensure_ascii=False) if target_products is not None else None
    )
    cur = conn.execute(
        "INSERT INTO keyword_queue (keyword, slug, channel, persona_id, budget_min_krw, "
        "budget_max_krw, target_products, notes, score, priority) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            keyword,
            uslug,
            channel,
            persona_id,
            budget_min_krw,
            budget_max_krw,
            tp_json,
            notes,
            score,
            priority,
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def get_or_create(
    conn: sqlite3.Connection, keyword: str, *, channel: str = "both", score: float = 0.0
) -> int:
    """키워드 텍스트로 pending 키워드를 찾고 없으면 새로 추가 (세션 #28 — 원팝업 생성용).

    '쿠팡 배너 입력 → 글 생성' 팝업이 키워드를 손으로 고르지 않고도 동작하도록: 같은 텍스트의
    pending 키워드가 있으면 재사용(중복 방지), 없으면 add_keyword로 생성. 반환: keyword_queue id.
    """
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("keyword가 비어 있습니다")
    row = conn.execute(
        "SELECT id FROM keyword_queue WHERE keyword = ? AND status = 'pending' ORDER BY id LIMIT 1",
        (keyword,),
    ).fetchone()
    if row:
        return int(row[0])
    return add_keyword(conn, keyword, channel=channel, score=score)


def set_status(
    conn: sqlite3.Connection, keyword_id: int, status: str, reason: str | None = None
) -> None:
    """키워드 상태 전이 (트리거가 updated_at 갱신)."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status는 {sorted(VALID_STATUSES)} 중 하나여야 합니다: {status!r}")
    conn.execute(
        "UPDATE keyword_queue SET status = ?, status_reason = ? WHERE id = ?",
        (status, reason, keyword_id),
    )
    conn.commit()


def get_keyword(conn: sqlite3.Connection, keyword_id: int) -> dict[str, Any] | None:
    """단일 키워드 행 → dict (없으면 None)."""
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM keyword_queue WHERE id = ?", (keyword_id,)).fetchone()
    return dict(row) if row else None


def link_draft(conn: sqlite3.Connection, keyword_id: int, draft_id: int) -> None:
    """생성된 draft를 키워드에 역링크 (drafts.keyword_id 설정 — 마이그레이션 007 컬럼)."""
    conn.execute("UPDATE drafts SET keyword_id = ? WHERE id = ?", (keyword_id, draft_id))
    conn.commit()


def _resolve_default_persona(
    conn: sqlite3.Connection, default_persona_slug: str | None
) -> int | None:
    """페르소나 id 결정: slug 지정 시 그것, 없으면 첫 페르소나(id 최소)."""
    if default_persona_slug:
        row = conn.execute(
            "SELECT id FROM personas WHERE slug = ?", (default_persona_slug,)
        ).fetchone()
        if row:
            return int(row[0])
    row = conn.execute("SELECT id FROM personas ORDER BY id LIMIT 1").fetchone()
    return int(row[0]) if row else None


def ensure_scenario_for_keyword(
    conn: sqlite3.Connection,
    keyword_id: int,
    *,
    default_persona_slug: str | None = None,
) -> int:
    """키워드 → 시나리오 자동 파생(없으면 생성, 있으면 재사용). 반환: scenario_id.

    파생 시나리오: slug=키워드 slug 기반, title=description=키워드, persona=해결된 기본,
    budget=키워드 예산. keyword_queue.scenario_id에 연결해 재생성 시 재사용(중복 방지).
    """
    kw = get_keyword(conn, keyword_id)
    if kw is None:
        raise ValueError(f"keyword id={keyword_id} 없음")
    if kw.get("scenario_id"):
        return int(kw["scenario_id"])

    persona_id = kw.get("persona_id") or _resolve_default_persona(conn, default_persona_slug)
    if persona_id is None:
        raise ValueError("페르소나가 없습니다 — `db seed`로 페르소나를 먼저 만드세요")

    sslug = _unique_slug(conn, "scenarios", str(kw["slug"]))
    # active=0 — 키워드 파생 시나리오는 '내맘대로 세팅'(라이프스타일 시나리오) 목록에 노출하지 않는다
    # (세션 #35: 제품 키워드 글이 가짜 시나리오로 세팅 페이지를 오염시키던 문제 근본 차단). draft FK용
    # 으로만 존재하고, 글은 카테고리로 흡수·리다이렉트되므로 세팅에 카드가 필요 없다.
    cur = conn.execute(
        "INSERT INTO scenarios (slug, title_ko, description, persona_id, "
        "budget_min_krw, budget_max_krw, active) VALUES (?, ?, ?, ?, ?, ?, 0)",
        (
            sslug,
            kw["keyword"],
            kw["keyword"],
            persona_id,
            kw.get("budget_min_krw"),
            kw.get("budget_max_krw"),
        ),
    )
    scenario_id = int(cur.lastrowid or 0)
    conn.execute("UPDATE keyword_queue SET scenario_id = ? WHERE id = ?", (scenario_id, keyword_id))
    conn.commit()
    return scenario_id
