"""category_writer.parse_category_page_response + category_page_builder 게이트 회귀.

라이브 Claude 호출 없음 — JSON 파싱(환각 slug 제거)·진실성 게이트만 검증.
"""

from __future__ import annotations

from typing import Any

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

    def test_trailing_comma_repaired(self) -> None:
        # 세션 #19(B): LLM 흔한 후행 콤마(,} ,]) — 제거 후 파싱
        r = cw.parse_category_page_response('{"title":"T","lead":"L","faq":[{"q":"Q","a":"A"},],}')
        assert r["title"] == "T" and r["lead"] == "L"
        assert len(r["faq"]) == 1

    def test_codefence_with_surrounding_prose(self) -> None:
        # 코드펜스 + 앞뒤 설명문이 섞여도 { } 추출로 파싱(DeepSeek 변동 대비)
        raw = '다음은 결과입니다:\n```json\n{"title":"T","lead":"L"}\n```\n확인 바랍니다.'
        r = cw.parse_category_page_response(raw)
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


class TestSelectFeatured:
    """추천 6선 결정적 선정 — 판매량순 + 만족도(≥90%) 하한 필터 (세션 #19)."""

    @staticmethod
    def _p(slug: str, tier: str, vol: int, rate: float = 95.0, disc: int = 10) -> dict:
        return {
            "slug": slug,
            "tier": tier,
            "name": slug,
            "volume": vol,
            "rate": rate,
            "discount_pct": disc,
        }

    def test_top_volume_per_tier(self) -> None:
        prods = [
            self._p("b1", "budget", 100),
            self._p("b2", "budget", 500),
            self._p("b3", "budget", 300),
            self._p("b4", "budget", 50),
            self._p("p1", "premium", 900),
            self._p("p2", "premium", 200),
            self._p("p3", "premium", 700),
        ]
        sel = cpb.select_featured(prods, per_tier=3)
        assert [s["slug"] for s in sel if s["tier"] == "budget"] == ["b2", "b3", "b1"]
        assert [s["slug"] for s in sel if s["tier"] == "premium"] == ["p1", "p3", "p2"]

    def test_low_satisfaction_excluded_when_enough_candidates(self) -> None:
        prods = [
            self._p("hi", "budget", 1000, rate=70.0),  # 판매량 최고지만 만족도 명백히 낮음(<80)
            self._p("a", "budget", 300),
            self._p("b", "budget", 200),
            self._p("c", "budget", 100),
        ]
        sel = [s["slug"] for s in cpb.select_featured(prods, per_tier=3)]
        assert "hi" not in sel and set(sel) == {"a", "b", "c"}

    def test_fills_count_with_poor_last(self) -> None:
        # 6개를 채우되(주인 요구: 항상 채움) 만족도<80은 맨 뒤 — 자리 모자랄 때만 채움
        prods = [
            self._p("ok", "budget", 100, rate=95.0),
            self._p("low1", "budget", 500, rate=70.0),  # 저평가 → 뒤로(판매량 많아도)
            self._p("low2", "budget", 400, rate=60.0),  # 저평가 → 뒤로
        ]
        sel = [s["slug"] for s in cpb.select_featured(prods, per_tier=3)]
        assert sel == ["ok", "low1", "low2"]  # ok(적격) 먼저, 저평가는 판매량순으로 채움

    def test_last_resort_when_all_low(self) -> None:
        # 전부 저평가뿐이면(적격 0) 최후수단으로 판매량순 표시(빈 섹션 방지)
        prods = [
            self._p("a", "budget", 500, rate=70.0),
            self._p("b", "budget", 300, rate=60.0),
        ]
        sel = [s["slug"] for s in cpb.select_featured(prods, per_tier=3)]
        assert sel == ["a", "b"]  # 판매량순

    def test_unknown_or_zero_rate_passes_only_known_low_excluded(self) -> None:
        # 만족도 없음(None)·0은 '판단 보류=통과'(신상품 부당 제외 방지), 명시적 저평가(0<r<90)만 제외
        prods = [
            self._p("new", "budget", 900, rate=None),  # type: ignore[arg-type]
            self._p("zero", "budget", 800, rate=0.0),
            self._p("good", "budget", 100, rate=95.0),
            self._p("bad", "budget", 700, rate=60.0),  # 명시적 저평가 → 제외
        ]
        sel = [s["slug"] for s in cpb.select_featured(prods, per_tier=3)]
        assert sel == ["new", "zero", "good"]  # bad(60%) 제외, 나머지 판매량순

    def test_handles_missing_signals(self) -> None:
        prods = [
            {
                "slug": "x",
                "tier": "budget",
                "name": "x",
                "volume": None,
                "rate": None,
                "discount_pct": None,
            }
        ]
        assert [s["slug"] for s in cpb.select_featured(prods, per_tier=3)] == ["x"]  # 크래시 없음


class _Res:
    """generate_raw 반환 호환 — response_text·usage."""

    def __init__(self, text: str) -> None:
        self.response_text = text
        self.usage: dict = {}


class _FakeClient:
    """1차 bad JSON → 2차 good JSON 순으로 응답하는 가짜 LLM 클라이언트."""

    def __init__(self, texts: list[str]) -> None:
        self._texts = texts
        self.calls = 0

    def generate_raw(self, system_text: str, user_prompt: str, dry_run: bool = True) -> _Res:
        t = self._texts[min(self.calls, len(self._texts) - 1)]
        self.calls += 1
        return _Res(t)


_GOOD_JSON = (
    '{"title":"노트북 거치대 고르는 법","lead":"노트북 거치대는 화면을 눈높이에 맞추는 도구다.",'
    '"guide_intro":"소재와 높이를 기준으로 고른다.","type_table":[],"checkpoints":[],'
    '"mistakes":"","picks":[],"compare":{"rows":[],"cells":[]},"faq":[]}'
)
_BAD_JSON = '여기 결과입니다:\n{"title": "x", oops 유효하지 않은 JSON'  # } 없음 → 파싱 실패


class TestBuildAndSaveRecovery:
    """build_and_save가 파싱 실패를 재생성으로 자가복원하는지 (세션 #19 B2)."""

    def _conn(self) -> Any:
        import sqlite3

        from common import db as _db

        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON")
        for m in _db.discover_migrations():
            conn.executescript(m.path.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) VALUES ('parse-test', '테스트', 'draft')"
        )
        conn.execute(
            "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
            "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
            "VALUES ('aliexpress','t1','노트북 거치대 알루미늄','KRW',30000,"
            "'https://s.click.aliexpress.com/t1','ali-t1','tag',"
            "datetime('now'),datetime('now'),datetime('now'))"
        )
        pid = conn.execute("SELECT id FROM products WHERE source_product_id='t1'").fetchone()[0]
        cid = conn.execute("SELECT id FROM categories WHERE slug='parse-test'").fetchone()[0]
        conn.execute(
            "INSERT INTO category_products (category_id, product_id, tier) VALUES (?,?,'budget')",
            (cid, pid),
        )
        conn.commit()
        return conn

    def test_recovers_after_one_parse_failure(self) -> None:
        conn = self._conn()
        client = _FakeClient([_BAD_JSON, _GOOD_JSON])
        rep = cpb.build_and_save(
            conn, "parse-test", client, dry_run=False, generate_image=False, max_attempts=2
        )
        assert rep["saved"] is True  # 2차 정상 JSON으로 저장됨
        assert client.calls == 2  # 1차 파싱 실패 → 2차 재생성

    def test_all_parse_failures_raise(self) -> None:
        conn = self._conn()
        client = _FakeClient([_BAD_JSON, _BAD_JSON])
        try:
            cpb.build_and_save(
                conn, "parse-test", client, dry_run=False, generate_image=False, max_attempts=2
            )
            raise AssertionError("CategoryPageError 기대")
        except cw.CategoryPageError:
            pass
