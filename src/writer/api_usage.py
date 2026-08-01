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
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> bool:
    """API 사용 1건 기록. 테이블 없거나 오류면 조용히 False(추적이 본기능을 막지 않음·§0)."""
    try:
        conn.execute(
            "INSERT INTO api_usage (provider, kind, status, est_cost_usd, detail, "
            "tokens_in, tokens_out) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                provider,
                kind,
                status,
                float(est_cost_usd),
                (detail or "")[:200],
                tokens_in,
                tokens_out,
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False


def llm_cost_usd(tokens_in: int, tokens_out: int) -> float:
    """토큰 → 추정 비용(USD). **단가 설정이 없으면 0** — 모르는 값을 지어내지 않는다(§0).

    설정 `llm_price_in_per_1m` / `llm_price_out_per_1m`(백만 토큰당 USD)를 주인이 넣으면
    그때부터 원가가 집계된다. 넣지 않아도 토큰 수는 항상 기록되므로 사용량 추적은 유효하다.
    """
    from common import settings

    p_in = settings.get_float("llm_price_in_per_1m")
    p_out = settings.get_float("llm_price_out_per_1m")
    if p_in <= 0 and p_out <= 0:
        return 0.0
    return (tokens_in / 1_000_000) * p_in + (tokens_out / 1_000_000) * p_out


def record_llm(
    conn: sqlite3.Connection,
    *,
    model: str,
    tokens_in: int,
    tokens_out: int,
    purpose: str,
    status: str = "ok",
) -> bool:
    """LLM 호출 1건 기록 — ★재시도分도 각각 1행(세션 #48).

    #36의 Imagen 추적과 달리 LLM은 아무 기록이 없었다. 콘솔 로그의 usage는 재시도 중 마지막
    1회분만 남아 "오늘 얼마 썼나"에 답할 수 없었다(#48 적발). 호출 지점마다 호출해 전량 기록한다.
    """
    return record(
        conn,
        "llm",
        purpose,
        status,
        llm_cost_usd(tokens_in, tokens_out),
        model,
        tokens_in,
        tokens_out,
    )


def llm_summary(conn: sqlite3.Connection, days: int = 1) -> dict[str, Any]:
    """최근 N일 LLM 사용 요약 — calls·tokens_in·tokens_out·est_cost_usd."""
    empty: dict[str, Any] = {
        "calls": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "est_cost_usd": 0.0,
        "days": days,
    }
    try:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0), "
            "       COALESCE(SUM(est_cost_usd),0) "
            "FROM api_usage WHERE provider='llm' "
            "  AND created_at >= datetime('now', ?)",
            (f"-{max(1, int(days))} days",),
        ).fetchone()
    except sqlite3.Error:
        return empty
    if row is None:
        return empty
    return {
        "calls": int(row[0] or 0),
        "tokens_in": int(row[1] or 0),
        "tokens_out": int(row[2] or 0),
        "est_cost_usd": float(row[3] or 0.0),
        "days": days,
    }


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
