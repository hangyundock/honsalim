"""category_writer.parse_category_page_response + category_page_builder 게이트 회귀.

라이브 Claude 호출 없음 — JSON 파싱(환각 slug 제거)·진실성 게이트만 검증.
"""

from __future__ import annotations

from enricher import category_page_builder as cpb
from enricher import category_writer as cw


class TestParseCategoryPage:
    def test_basic_and_hallucination_slug_removed(self) -> None:
        sample = (
            '{"title":"T","lead":"도입 문장","guide_intro":"기준",'
            '"type_table":[{"type":"고정형","trait":"단순","for":"단순 높이"}],'
            '"checkpoints":[{"title":"무게","why":"중요하다"}],"mistakes":"흔한 실수",'
            '"faq":[{"q":"Q","a":"A"}],'
            '"picks":[{"slug":"ali-1","tier":"premium","type":"서랍형","pros":["p1","p2"],"cons":["c1"],"for":"f"},'
            '{"slug":"GHOST-999","tier":"budget"}],'
            '"compare":{"rows":["높이조절","서랍"],'
            '"cells":[{"slug":"ali-1","values":["O","O"]},{"slug":"GHOST-999","values":["X"]}]}}'
        )
        r = cw.parse_category_page_response(sample, valid_slugs={"ali-1"})
        assert r["title"] == "T" and r["lead"] == "도입 문장"
        assert len(r["type_table"]) == 1 and len(r["checkpoints"]) == 1
        # 환각 slug(GHOST-999) 제거 — 제공 목록(ali-1)만 남음
        assert len(r["picks"]) == 1
        assert r["picks"][0]["slug"] == "ali-1"
        assert r["picks"][0]["type"] == "서랍형"
        assert r["picks"][0]["pros"] == ["p1", "p2"]
        # 비교표: GHOST는 picks에 없어 제거, ali-1만 / values는 rows 길이(2)에 맞춤
        assert len(r["compare"]["cells"]) == 1
        assert r["compare"]["cells"][0]["slug"] == "ali-1"
        assert len(r["compare"]["cells"][0]["values"]) == 2

    def test_codefence_stripped(self) -> None:
        r = cw.parse_category_page_response('```json\n{"title":"T","lead":"L"}\n```')
        assert r["title"] == "T" and r["lead"] == "L"

    def test_raw_newline_in_lead_ok(self) -> None:
        # lead에 raw 개행이 있어도 strict=False로 파싱
        r = cw.parse_category_page_response('{"title":"T","lead":"줄1\n줄2"}')
        assert "\n" in r["lead"]

    def test_missing_required_raises(self) -> None:
        for bad in ('{"faq":[]}', "not json", '{"title":"","lead":""}'):
            try:
                cw.parse_category_page_response(bad)
                raise AssertionError(f"CategoryPageError 기대: {bad!r}")
            except cw.CategoryPageError:
                pass


class TestGates:
    def test_first_person_fails_truth(self) -> None:
        # 1인칭 사용기 → truth 게이트 reject (§0·POLICY §3-1-3)
        _, gates = cpb._run_gates("제가 직접 써본 결과 정말 좋았습니다.")
        assert gates["truth"]["pass"] is False
        assert "truth" in gates and "disclosure" in gates and "links" in gates

    def test_clean_prose_passes_truth(self) -> None:
        # 1인칭·AI흔적·과장 없는 산문 → truth 게이트 통과
        _, gates = cpb._run_gates(
            "모니터 받침대는 화면을 눈높이에 맞추는 도구다. 소재와 높이를 기준으로 고른다."
        )
        assert gates["truth"]["pass"] is True
