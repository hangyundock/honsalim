"""writer.api_usage — 외부 API 사용량/비용 추적 (세션 #36).

Google Imagen 호출(개념 이미지)을 한 건씩 기록해, 대시보드가 '이번 달 사용 장수·추정 비용·상한 대비'를
보여준다. 구글의 실제 청구액은 단순 API 키로 못 가져오므로(공개 조회 API 없음), 우리가 거는 호출을
직접 세어 **추정**한다 — 화면에는 '추정'으로 명시한다(가짜 지표 금지·§0).

추적 실패(테이블 미존재 등)는 본기능(이미지 생성)을 절대 막지 않는다 — 조용히 무시한다(§0 견고성).
"""

from __future__ import annotations

import sqlite3
from typing import Any

# Imagen 4 Fast 장당 추정 단가(USD) — AutoBlog/공식 기준. 실제 청구와 다를 수 있어 '추정'으로 표기.
IMAGEN_UNIT_USD = 0.02


def record(
    conn: sqlite3.Connection,
    provider: str,
    kind: str,
    status: str,
    est_cost_usd: float = 0.0,
    detail: str | None = None,
) -> bool:
    """API 사용 1건 기록. 테이블 없거나 오류면 조용히 False(추적이 본기능을 막지 않음·§0)."""
    try:
        conn.execute(
            "INSERT INTO api_usage (provider, kind, status, est_cost_usd, detail) "
            "VALUES (?, ?, ?, ?, ?)",
            (provider, kind, status, float(est_cost_usd), (detail or "")[:200]),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False


def record_imagen(conn: sqlite3.Connection, *, ok: bool, error: str | None = None) -> bool:
    """Imagen 호출 1건 기록 — 성공은 단가 집계, 실패는 429/오류로 구분(한도초과 알림용)."""
    if ok:
        return record(conn, "google_imagen", "image", "ok", IMAGEN_UNIT_USD)
    status = "error_429" if (error and "429" in error) else "error"
    return record(conn, "google_imagen", "image", status, 0.0, error)


def month_summary(conn: sqlite3.Connection, provider: str = "google_imagen") -> dict[str, Any]:
    """이번 달(UTC 기준) 사용 요약. 테이블 없으면 0. 반환: images·est_cost_usd·last_429_at."""
    try:
        row = conn.execute(
            "SELECT "
            "  SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) AS images, "
            "  COALESCE(SUM(est_cost_usd), 0) AS cost, "
            "  MAX(CASE WHEN status='error_429' THEN created_at END) AS last_429 "
            "FROM api_usage "
            "WHERE provider = ? "
            "  AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')",
            (provider,),
        ).fetchone()
    except sqlite3.Error:
        return {"images": 0, "est_cost_usd": 0.0, "last_429_at": None}
    if row is None:
        return {"images": 0, "est_cost_usd": 0.0, "last_429_at": None}
    return {
        "images": int(row[0] or 0),
        "est_cost_usd": float(row[1] or 0.0),
        "last_429_at": row[2],
    }
