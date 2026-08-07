"""tracker.gsc 단위 테스트 — 네트워크·자격증명 0 (세션 주입 fake). 세션 #52."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from tracker import gsc


class FakeResp:
    def __init__(self, payload: dict[str, Any], status_code: int = 200, text: str = ""):
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    """POST/GET 호출을 기록하고 큐 순서대로 응답 반환."""

    def __init__(self, responses: list[FakeResp]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def _next(self) -> FakeResp:
        if not self.responses:
            raise AssertionError("응답 큐 소진 — 예상보다 많은 호출")
        return self.responses.pop(0)

    def post(self, url: str, json: dict[str, Any] | None = None) -> FakeResp:
        self.calls.append({"method": "POST", "url": url, "json": json})
        return self._next()

    def get(self, url: str) -> FakeResp:
        self.calls.append({"method": "GET", "url": url})
        return self._next()


def _row(key: str, clicks: int, imps: int, pos: float) -> dict[str, Any]:
    return {"keys": [key], "clicks": clicks, "impressions": imps, "ctr": 0.0, "position": pos}


def test_query_paginates_until_short_page():
    # rowLimit=2 페이지 2회 꽉 참 → 3회째 1건(짧은 페이지)으로 종료. startRow 누적 검증.
    pages = [
        FakeResp({"rows": [_row("a", 1, 10, 5.0), _row("b", 2, 20, 6.0)]}),
        FakeResp({"rows": [_row("c", 3, 30, 7.0), _row("d", 4, 40, 8.0)]}),
        FakeResp({"rows": [_row("e", 5, 50, 9.0)]}),
    ]
    s = FakeSession(pages)
    rows = gsc.query(
        dt.date(2026, 7, 1), dt.date(2026, 7, 28), row_limit=2, session=s, site="sc-domain:x"
    )
    assert [r["keys"][0] for r in rows] == ["a", "b", "c", "d", "e"]
    assert [c["json"]["startRow"] for c in s.calls] == [0, 2, 4]


def test_query_encodes_site_url_and_normalizes_rows():
    s = FakeSession([FakeResp({"rows": [{"keys": ["q"], "clicks": "3", "impressions": None}]})])
    rows = gsc.query(
        dt.date(2026, 7, 1), dt.date(2026, 7, 2), session=s, site="sc-domain:honsallim.com"
    )
    assert "sc-domain%3Ahonsallim.com" in s.calls[0]["url"]
    assert rows == [{"keys": ["q"], "clicks": 3, "impressions": 0, "ctr": 0.0, "position": 0.0}]


def test_query_403_gives_permission_hint():
    s = FakeSession([FakeResp({}, status_code=403)])
    with pytest.raises(gsc.GscError, match="사용자"):
        gsc.query(dt.date(2026, 7, 1), dt.date(2026, 7, 2), session=s, site="sc-domain:x")


def test_query_404_hints_list_sites():
    s = FakeSession([FakeResp({}, status_code=404)])
    with pytest.raises(gsc.GscError, match="list-sites"):
        gsc.query(dt.date(2026, 7, 1), dt.date(2026, 7, 2), session=s, site="sc-domain:x")


def test_window_applies_data_lag():
    start, end = gsc.window(7, today=dt.date(2026, 8, 7))
    assert end == dt.date(2026, 8, 5)  # 오늘-2일 (지연 데이터 0 오판 방지)
    assert start == dt.date(2026, 7, 30)


def test_build_session_missing_key_is_instructive(tmp_path, monkeypatch):
    monkeypatch.setenv(gsc.ENV_KEY_PATH, str(tmp_path / "absent.json"))
    with pytest.raises(gsc.GscError, match="서비스 계정"):
        gsc.build_session()


def test_site_url_env_override(monkeypatch):
    monkeypatch.setenv(gsc.ENV_SITE_URL, "https://honsallim.com/")
    assert gsc.site_url() == "https://honsallim.com/"
    monkeypatch.delenv(gsc.ENV_SITE_URL)
    assert gsc.site_url() == gsc.DEFAULT_SITE_URL


def test_summary_totals_trend_and_sitemaps(monkeypatch):
    # 14일 창: by_date 14행(전반 7일 노출 10·후반 7일 노출 20) → 추이 검증.
    days = [dt.date(2026, 7, 23) + dt.timedelta(days=i) for i in range(14)]
    by_date = [
        _row(d.isoformat(), 1 if i < 7 else 2, 10 if i < 7 else 20, 20.0 if i < 7 else 10.0)
        for i, d in enumerate(days)
    ]
    responses = [
        FakeResp({"rows": by_date}),  # by_date
        FakeResp({"rows": [_row("쿼리", 3, 30, 5.0)]}),  # top_queries
        FakeResp({"rows": [_row("/articles/x/", 2, 20, 6.0)]}),  # top_pages
        FakeResp(
            {
                "sitemap": [
                    {
                        "path": "https://honsallim.com/sitemap.xml",
                        "contents": [{"submitted": "42", "indexed": "18"}],
                    }
                ]
            }
        ),
    ]
    s = FakeSession(responses)
    monkeypatch.setattr(gsc, "window", lambda d, today=None: (days[0], days[-1]))
    rep = gsc.summary(days=14, site="sc-domain:x", session=s)
    t = rep["totals"]
    assert t["clicks"] == 21 and t["impressions"] == 210
    # 노출 가중 평균 순위: (70*20 + 140*10) / 210 = 13.33…
    assert round(t["position"], 2) == 13.33
    assert rep["trend"]["prev7"]["impressions"] == 70
    assert rep["trend"]["last7"]["impressions"] == 140
    assert rep["trend"]["last7"]["position"] == 10.0
    assert rep["sitemaps"] == [
        {"path": "https://honsallim.com/sitemap.xml", "submitted": 42, "indexed": 18}
    ]


def test_summary_short_window_has_no_trend(monkeypatch):
    days = [dt.date(2026, 8, 1) + dt.timedelta(days=i) for i in range(7)]
    responses = [
        FakeResp({"rows": [_row(d.isoformat(), 0, 1, 1.0) for d in days]}),
        FakeResp({"rows": []}),
        FakeResp({"rows": []}),
        FakeResp({}, status_code=403),  # sitemap 실패는 요약을 죽이지 않는다(격리)
    ]
    s = FakeSession(responses)
    monkeypatch.setattr(gsc, "window", lambda d, today=None: (days[0], days[-1]))
    rep = gsc.summary(days=7, site="sc-domain:x", session=s)
    assert rep["trend"] is None
    assert rep["sitemaps"] == []


def test_key_path_default_is_secrets_dir(monkeypatch):
    monkeypatch.delenv(gsc.ENV_KEY_PATH, raising=False)
    p = gsc.key_path()
    assert p.name == gsc.DEFAULT_KEY_FILENAME
    assert "secrets" in str(p).lower()
