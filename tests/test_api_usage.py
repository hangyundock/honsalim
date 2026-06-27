"""writer.api_usage + dashboard.queries.google_usage 회귀 (세션 #36).

Google(Imagen) 호출 사용량 추적·추정비용·상한 경고. 라이브 호출 없음(기록/집계 로직만).
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from common import db as _db
from common import settings
from writer import api_usage


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    conn.commit()
    return conn


class TestApiUsage:
    def test_record_imagen_ok_counts_cost(self) -> None:
        conn = _conn()
        assert api_usage.record_imagen(conn, ok=True) is True
        api_usage.record_imagen(conn, ok=True)
        s = api_usage.month_summary(conn)
        assert s["images"] == 2
        assert abs(s["est_cost_usd"] - 2 * api_usage.IMAGEN_UNIT_USD) < 1e-9
        assert s["last_429_at"] is None

    def test_record_429_flagged_no_cost(self) -> None:
        conn = _conn()
        api_usage.record_imagen(conn, ok=False, error="Imagen HTTP 429: spending cap exceeded")
        s = api_usage.month_summary(conn)
        assert s["images"] == 0
        assert s["est_cost_usd"] == 0.0
        assert s["last_429_at"] is not None  # 한도초과 발생 신호

    def test_record_non429_error_not_flagged(self) -> None:
        conn = _conn()
        api_usage.record_imagen(conn, ok=False, error="connection timeout")
        s = api_usage.month_summary(conn)
        assert s["images"] == 0 and s["last_429_at"] is None

    def test_missing_table_is_safe(self) -> None:
        """테이블 없으면(마이그레이션 전) 조용히 실패 — 추적이 이미지 생성을 막지 않음(§0)."""
        conn = sqlite3.connect(":memory:")
        assert api_usage.record_imagen(conn, ok=True) is False
        assert api_usage.month_summary(conn) == {
            "images": 0,
            "est_cost_usd": 0.0,
            "last_429_at": None,
        }


class TestGoogleUsageQuery:
    def test_pct_and_near_warning(self, monkeypatch: Any) -> None:
        from dashboard import queries

        conn = _conn()
        for _ in range(5):
            api_usage.record_imagen(conn, ok=True)  # 5건 x $0.02 = $0.10
        monkeypatch.setattr(
            settings, "get", lambda k, d=None, **kw: 0.12 if k == "google_spend_cap_usd" else d
        )
        gu = queries.google_usage(conn)
        assert gu["images"] == 5
        assert abs(gu["used_usd"] - 0.10) < 1e-9
        assert gu["pct"] is not None and gu["pct"] > 80
        assert gu["near_or_over"] is True

    def test_no_cap_means_no_pct(self, monkeypatch: Any) -> None:
        from dashboard import queries

        conn = _conn()
        api_usage.record_imagen(conn, ok=True)
        monkeypatch.setattr(
            settings, "get", lambda k, d=None, **kw: 0.0 if k == "google_spend_cap_usd" else d
        )
        gu = queries.google_usage(conn)
        assert gu["pct"] is None and gu["near_or_over"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
