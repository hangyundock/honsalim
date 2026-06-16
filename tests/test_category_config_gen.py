"""collector.category_config_gen 회귀 (세션 #35, ②) — 한글 카테고리명 → 수집 설정 자동생성.

LLM은 fake client 주입으로 호출 없이 검증. JSON 파싱(코드펜스·누락)·정규화·CategorySpec 변환·
dry_run을 확인한다.
"""

from __future__ import annotations

import pytest

from collector import category_config_gen as cg

_VALID = (
    '{"core":"가습기","exclude":["차량","디퓨저"],'
    '"tiers":{"budget":{"q":"humidifier","min":5000,"max":30000},'
    '"premium":{"q":"ultrasonic humidifier","min":30000,"max":120000}}}'
)


class _FakeResult:
    def __init__(self, text: str | None) -> None:
        self.response_text = text


class _FakeClient:
    def __init__(self, text: str) -> None:
        self._text = text
        self.called = False

    def generate_raw(self, system: str, user: str, dry_run: bool = True) -> _FakeResult:
        self.called = True
        return _FakeResult(None if dry_run else self._text)


class TestParseConfig:
    def test_valid(self) -> None:
        c = cg.parse_config(_VALID)
        assert c["core"] == "가습기"
        assert c["exclude"] == ["차량", "디퓨저"]
        assert c["tiers"]["budget"] == {"q": "humidifier", "min": 5000, "max": 30000}
        assert c["tiers"]["premium"]["q"] == "ultrasonic humidifier"

    def test_code_fence(self) -> None:
        c = cg.parse_config("```json\n" + _VALID + "\n```")
        assert c["core"] == "가습기"

    def test_zero_price_becomes_none(self) -> None:
        text = (
            '{"core":"선풍기","tiers":{"budget":{"q":"fan","min":0,"max":0},'
            '"premium":{"q":"tower fan","min":30000,"max":90000}}}'
        )
        c = cg.parse_config(text)
        assert c["tiers"]["budget"]["min"] is None and c["tiers"]["budget"]["max"] is None
        assert c["exclude"] == []  # 누락 시 빈 배열

    def test_missing_tier_q_raises(self) -> None:
        text = (
            '{"core":"x","tiers":{"budget":{"min":1,"max":2},"premium":{"q":"y","min":3,"max":4}}}'
        )
        with pytest.raises(ValueError):
            cg.parse_config(text)

    def test_missing_core_raises(self) -> None:
        text = '{"tiers":{"budget":{"q":"a","min":1,"max":2},"premium":{"q":"b","min":3,"max":4}}}'
        with pytest.raises(ValueError):
            cg.parse_config(text)


class TestToSpec:
    def test_builds_spec(self) -> None:
        spec = cg.to_spec("humidifier", cg.parse_config(_VALID))
        assert spec.slug == "humidifier"
        assert spec.require_any == ("가습기",)
        assert spec.require_all == ()
        assert spec.exclude_terms == ("차량", "디퓨저")
        assert set(spec.tiers) == {"budget", "premium"}
        assert spec.tiers["premium"].q == "ultrasonic humidifier"
        assert spec.tiers["budget"].min_price == 5000


class TestGenerateConfig:
    def test_with_injected_client(self) -> None:
        client = _FakeClient(_VALID)
        c = cg.generate_config("가습기", client=client)
        assert client.called is True
        assert c["core"] == "가습기"
        assert c["tiers"]["premium"]["max"] == 120000

    def test_dry_run_no_parse(self) -> None:
        client = _FakeClient(_VALID)
        c = cg.generate_config("가습기", client=client, dry_run=True)
        assert c == {}  # dry_run: 응답 없음 → 빈 dict

    def test_empty_response_returns_empty(self) -> None:
        client = _FakeClient("")
        # generate_raw가 dry_run=False라도 빈 텍스트면 빈 dict
        c = cg.generate_config("가습기", client=client, dry_run=False)
        assert c == {}


class TestSuggestCategories:
    _SUGGEST = (
        '[{"label":"가습기","reason":"건조한 원룸 필수"},'
        '{"label":"의자","reason":"중복(기존)"},'
        '{"label":"전기포트","reason":"1인 가전"}]'
    )

    def test_suggests_and_dedupes_existing(self) -> None:
        client = _FakeClient(self._SUGGEST)
        out = cg.suggest_categories(["의자", "책상"], n=5, client=client)
        labels = [x["label"] for x in out]
        assert "가습기" in labels and "전기포트" in labels
        assert "의자" not in labels  # 기존 카테고리는 제외
        assert all(x["reason"] for x in out)

    def test_respects_n_limit(self) -> None:
        client = _FakeClient(self._SUGGEST)
        out = cg.suggest_categories([], n=1, client=client)
        assert len(out) == 1

    def test_dry_run_empty(self) -> None:
        client = _FakeClient(self._SUGGEST)
        assert cg.suggest_categories([], client=client, dry_run=True) == []

    def test_code_fenced_array(self) -> None:
        client = _FakeClient("```json\n" + self._SUGGEST + "\n```")
        out = cg.suggest_categories([], n=5, client=client)
        assert [x["label"] for x in out] == ["가습기", "의자", "전기포트"]
