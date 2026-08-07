"""writer.cluster_balance 테스트 — 클러스터 포화 판정·추천 정렬 (세션 #52).

배경: 추천 창이 검색량순이라 맨 위가 미매핑이었고, 어느 주제가 이미 포화인지는 화면에
없어서 운영자가 머리로 판단해야 했다(주인 지적). 정렬·숨김 로직을 GUI 밖에서 검증한다.
"""

from __future__ import annotations

import sqlite3

import pytest

from writer import cluster_balance as cb


def _rec(kw, *, publishable=True, score=1000.0, volume=None):
    return {
        "keyword": kw,
        "publishable": publishable,
        "score": score,
        "volume": volume,
        "source": "naver",
    }


@pytest.fixture()
def counts():
    # 2026-08-07 실측 분포
    return {
        "office-chair": 7,
        "cutting-board": 6,
        "desk": 5,
        "monitor-arm": 2,
        "mini-rice-cooker": 2,
        "monitor-stand": 2,
    }


def test_threshold_is_relative_to_average(counts):
    # 평균 4.0 x 1.5 = 6.0 → 의자(7)·도마(6)가 포화, 책상(5)은 아님
    assert cb.saturation_threshold(counts) == 6.0


def test_threshold_has_floor_for_small_sites():
    """★사이트 초기(전 카테고리 1편)에 2편짜리가 '포화'로 잡히면 추천이 텅 빈다."""
    assert cb.saturation_threshold({"a": 1, "b": 1}) == float(cb.SATURATION_MIN_ARTICLES)
    assert cb.saturation_threshold({}) == float(cb.SATURATION_MIN_ARTICLES)


def test_annotate_marks_saturation(monkeypatch, counts):
    monkeypatch.setattr(
        "collector.keyword_relevance.resolve_category",
        lambda kw, seo=None: {"공부의자": "office-chair", "원목모니터받침대": "monitor-stand"}.get(
            kw
        ),
    )
    recs = [_rec("공부의자"), _rec("원목모니터받침대"), _rec("모르는키워드")]
    cb.annotate(recs, counts)
    assert recs[0]["cluster"] == "office-chair" and recs[0]["saturated"] is True
    assert recs[1]["cluster"] == "monitor-stand" and recs[1]["saturated"] is False
    # 미매핑은 포화로 취급하지 않는다 — 이미 '발행 불가'로 걸러지므로 이중 처벌 금지
    assert recs[2]["cluster"] is None and recs[2]["saturated"] is False


def test_sort_puts_publishable_thin_cluster_first():
    """★핵심: 맨 위가 항상 '지금 넣기 가장 좋은 것'이어야 한다(⭐1순위 버튼 안전)."""
    rows = [
        {"keyword": "고볼륨미매핑", "publishable": False, "score": 9999.0, "cluster_count": 0},
        {
            "keyword": "포화클러스터",
            "publishable": True,
            "score": 5000.0,
            "saturated": True,
            "cluster_count": 7,
        },
        {
            "keyword": "얇은클러스터",
            "publishable": True,
            "score": 900.0,
            "saturated": False,
            "cluster_count": 2,
        },
        {
            "keyword": "더얇은클러스터",
            "publishable": True,
            "score": 800.0,
            "saturated": False,
            "cluster_count": 0,
        },
    ]
    got = [r["keyword"] for r in sorted(rows, key=cb.sort_key)]
    assert got == ["더얇은클러스터", "얇은클러스터", "포화클러스터", "고볼륨미매핑"]


def test_sort_treats_missing_publishable_as_neutral():
    """publishable 키가 없는 구 호출부·테스트 데이터를 '불가'로 강등하지 않는다."""
    rows = [
        {"keyword": "정보없음", "score": 100.0, "cluster_count": 0},
        {"keyword": "불가", "publishable": False, "score": 9999.0, "cluster_count": 0},
    ]
    assert [r["keyword"] for r in sorted(rows, key=cb.sort_key)] == ["정보없음", "불가"]


def test_prepare_hides_unpublishable_and_saturated_by_default(monkeypatch, counts):
    monkeypatch.setattr(
        "collector.keyword_relevance.resolve_category",
        lambda kw, seo=None: {"공부의자": "office-chair", "원목모니터받침대": "monitor-stand"}.get(
            kw
        ),
    )
    recs = [
        _rec("공부의자", score=8000),  # 포화
        _rec("원목모니터받침대", score=840),  # 정상
        _rec("미매핑", publishable=False, score=9999),  # 발행 불가
    ]
    p = cb.prepare(recs, counts)
    assert [r["keyword"] for r in p["rows"]] == ["원목모니터받침대"]
    assert p["hidden_unpublishable"] == 1 and p["hidden_saturated"] == 1
    assert p["total"] == 3


def test_prepare_toggles_reveal_hidden(monkeypatch, counts):
    monkeypatch.setattr(
        "collector.keyword_relevance.resolve_category",
        lambda kw, seo=None: {"공부의자": "office-chair"}.get(kw),
    )
    recs = [_rec("공부의자"), _rec("미매핑", publishable=False)]
    both = cb.prepare(recs, counts, show_unpublishable=True, show_saturated=True)
    assert len(both["rows"]) == 2  # 숨김은 차단이 아니다 — 토글로 전부 보인다
    assert both["hidden_unpublishable"] == 0 and both["hidden_saturated"] == 0


def test_summary_line_explains_why_list_is_short(monkeypatch, counts):
    monkeypatch.setattr(
        "collector.keyword_relevance.resolve_category",
        lambda kw, seo=None: {"공부의자": "office-chair"}.get(kw),
    )
    p = cb.prepare([_rec("공부의자"), _rec("미매핑", publishable=False)], counts)
    line = cb.summary_line(p)
    assert "표시 0건" in line and "발행 불가 1건" in line and "포화 클러스터 1건" in line
    assert "6.0편" in line


def test_published_counts_uses_operational_resolver(monkeypatch):
    """카테고리 해석은 운영 경로와 **같은 함수** — 따로 구현하면 판정이 어긋난다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE keyword_queue (keyword TEXT, slug TEXT);"
        "CREATE TABLE articles (slug TEXT, status TEXT);"
        "INSERT INTO keyword_queue VALUES ('공부의자','a'),('나무도마','b'),('미발행','c');"
        "INSERT INTO articles VALUES ('a','published'),('b','published'),('c','draft');"
    )
    monkeypatch.setattr(
        "collector.keyword_relevance.resolve_category",
        lambda kw, seo=None: {"공부의자": "office-chair", "나무도마": "cutting-board"}.get(kw),
    )
    assert cb.published_counts(conn) == {"office-chair": 1, "cutting-board": 1}
    conn.close()
