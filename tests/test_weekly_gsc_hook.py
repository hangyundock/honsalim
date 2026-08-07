"""주간 GSC 훅 배선 테스트 (세션 #52).

★단위 테스트만으론 '함수는 맞는데 아무도 안 부른다'를 못 잡는다(#48 배선 공백 교훈).
여기서는 **월요일 요약이 실제로 GSC 적립을 호출하는지**와, 실패해도 사이클이 죽지 않는지를 본다.
"""

from __future__ import annotations

import datetime as dt

import cli


class _FrozenDate(dt.date):
    """date.today()만 고정 — cli가 함수 안에서 `from datetime import date` 하므로 모듈 패치."""

    _today = dt.date(2026, 8, 10)  # 월요일

    @classmethod
    def today(cls) -> dt.date:  # type: ignore[override]
        return cls._today


def _freeze(monkeypatch, day: dt.date) -> None:
    _FrozenDate._today = day
    monkeypatch.setattr(dt, "date", _FrozenDate)


def test_weekly_summary_skips_when_not_monday(monkeypatch):
    _freeze(monkeypatch, dt.date(2026, 8, 11))  # 화요일
    assert cli._weekly_summary_lines() == []


def test_monday_summary_calls_gsc_collect(monkeypatch, tmp_path):
    """★배선 검증: 월요일 요약이 GSC 성과 + **적립**을 실제로 호출한다."""
    _freeze(monkeypatch, dt.date(2026, 8, 10))
    calls: list[str] = []

    class FakeConn:
        def execute(self, *a, **k):
            calls.append("db")
            return self

        def fetchone(self):
            return (0,)

        def close(self):
            pass

    monkeypatch.setattr(cli.db, "connect", lambda *a, **k: FakeConn())
    monkeypatch.setattr("validator.site_audit.audit_site", lambda *a, **k: [], raising=False)
    monkeypatch.setattr(
        "tracker.gsc.summary",
        lambda **k: {
            "totals": {"impressions": 66.0, "clicks": 2.0, "position": 17.7},
            "trend": {
                "last7": {"impressions": 25.0, "position": 16.6},
                "prev7": {"impressions": 25.0, "position": 16.5},
            },
        },
        raising=False,
    )
    monkeypatch.setattr(
        cli, "_gsc_collect", lambda days=28: (calls.append("collect"), (7, "적립 7건"))[1]
    )

    lines = cli._weekly_summary_lines()
    text = "\n".join(lines)
    assert "collect" in calls, "월요일 요약이 GSC 적립을 부르지 않는다 — 배선 끊김"
    assert "구글 검색 성과" in text and "적립 7건" in text


def test_monday_summary_survives_gsc_failure(monkeypatch):
    """GSC가 죽어도 주간 요약·사이클은 계속돼야 한다(§0) — 단, 조용히 넘어가지 않는다."""
    _freeze(monkeypatch, dt.date(2026, 8, 10))

    class FakeConn:
        def execute(self, *a, **k):
            return self

        def fetchone(self):
            return (0,)

        def close(self):
            pass

    monkeypatch.setattr(cli.db, "connect", lambda *a, **k: FakeConn())
    monkeypatch.setattr("validator.site_audit.audit_site", lambda *a, **k: [], raising=False)

    def boom(**k):
        raise RuntimeError("권한 없음")

    monkeypatch.setattr("tracker.gsc.summary", boom, raising=False)
    lines = cli._weekly_summary_lines()
    text = "\n".join(lines)
    assert "주간 요약" in text  # 요약 자체는 살아남고
    assert "구글 검색 성과 조회 실패" in text  # 실패는 드러난다


def test_collect_failure_does_not_kill_performance_lines(monkeypatch):
    """적립만 실패하면 성과 숫자는 그대로 보고된다(격리)."""
    _freeze(monkeypatch, dt.date(2026, 8, 10))
    monkeypatch.setattr(
        "tracker.gsc.summary",
        lambda **k: {
            "totals": {"impressions": 10.0, "clicks": 0.0, "position": 20.0},
            "trend": None,
        },
        raising=False,
    )

    def boom(days=28):
        raise RuntimeError("네트워크")

    monkeypatch.setattr(cli, "_gsc_collect", boom)
    lines = cli._weekly_gsc_lines()
    text = "\n".join(lines)
    assert "노출 10" in text
    assert "검색어 적립 실패" in text
