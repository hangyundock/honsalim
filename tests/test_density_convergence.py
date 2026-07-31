"""세션 #48 — 대표키워드 밀도 수렴(지시 ① + 결정적 감산 백스톱 ②) 회귀.

라이브 근거(07-30 draft 38 · 07-31 draft 39, 저장 본문 전수 확인):
    시도1 미달(2회·6회) → "총 약 14~15회" 지시 → 시도2 **31회**(4.33%·3.97%) → 반려 → 발행 0편
31회의 분포가 '소제목 8/10 + 상품 문단 전부 + FAQ 답변 전부'라 LLM이 횟수를 센 게 아니라
문체를 바꿨음이 확인됐다. 여기서는 그 실패를 재현하고, 수정이 실제로 막는지 고정한다.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar

import pytest

import cli
from enricher import density_fix
from enricher.keyword_density import (
    cap_count,
    join_josa,
    keyword_substitute,
    per_1000_band,
    regen_target_pct,
    rewrite_following_josa,
    target_count,
)
from enricher.seo_directive import build_seo_directive
from validator import serialize_report, validate_all
from validator.seo import DENSITY_CEIL, DENSITY_FLOOR, DENSITY_TARGET


class TestKeywordSubstitute:
    """★#48 근본원인 3 — 옛 `_short_form`이 단일 토큰에서 자기 자신을 반환해 no-op였다."""

    def test_single_token_compound_strips_tail(self) -> None:
        assert keyword_substitute("책상추천") == "책상"
        assert keyword_substitute("도마추천") == "도마"

    def test_spaced_keyword_prefers_head_noun_over_last_token(self) -> None:
        # '책상 추천'에서 마지막 토큰('추천')을 쓰면 주어가 사라진다 — 머리 명사가 옳다.
        assert keyword_substitute("책상 추천") == "책상"

    def test_multiword_without_tail_uses_last_token(self) -> None:
        assert keyword_substitute("노트북 거치대") == "거치대"

    def test_no_safe_substitute_returns_none(self) -> None:
        """★대체어를 못 구하면 None — 억지 대체어를 만들지 않는다(감산도 미적용)."""
        assert keyword_substitute("게이밍의자") is None
        assert keyword_substitute("") is None
        assert keyword_substitute(None) is None

    def test_never_returns_something_containing_the_keyword(self) -> None:
        # 대체어가 키워드를 품으면 감산이 0이 되어 무한 헛수고가 된다.
        for kw in ("책상추천", "도마추천", "노트북 거치대"):
            sub = keyword_substitute(kw)
            assert sub is None or kw.replace(" ", "") not in sub.replace(" ", "")


class TestJosa:
    """치환 후 조사 비문 방지 — '도마추천은'을 '도마은'으로 만들면 안 된다."""

    def test_join_josa_picks_form_by_batchim(self) -> None:
        assert join_josa("책상", "은") == "책상은"  # 받침 O
        assert join_josa("도마", "은") == "도마는"  # 받침 X
        assert join_josa("책상", "이다") == "책상이다"
        assert join_josa("도마", "이다") == "도마다"

    def test_rieul_exception_for_euro(self) -> None:
        # ㄹ 받침은 받침이 있어도 '로'를 쓴다 — '서울으로'는 비문.
        assert join_josa("서울", "으로") == "서울로"
        assert join_josa("책상", "으로") == "책상으로"

    def test_same_batchim_needs_no_josa_edit(self) -> None:
        # '책상추천'(천·받침) → '책상'(상·받침): 조사는 그대로 두면 된다.
        ok, consume, josa = rewrite_following_josa("이다.", "책상추천", "책상")
        assert (ok, consume, josa) == (True, 0, "")

    def test_differing_batchim_rewrites_josa(self) -> None:
        # '도마추천'(받침) → '도마'(받침 없음): 뒤 조사를 모음형으로 바꿔야 한다.
        ok, consume, josa = rewrite_following_josa("은 좋다", "도마추천", "도마")
        assert ok and consume == 1 and josa == "는"

    def test_ambiguous_following_hangul_is_refused(self) -> None:
        """★애매하면 건드리지 않는다 — '…추천은행'의 '은'은 조사가 아닐 수 있다."""
        ok, _, _ = rewrite_following_josa("은행에서", "도마추천", "도마")
        assert ok is False

    def test_boundary_after_keyword_is_always_safe(self) -> None:
        ok, consume, josa = rewrite_following_josa(" 가이드", "도마추천", "도마")
        assert (ok, consume, josa) == (True, 0, "")


class TestRegenTarget:
    """★#48 근본원인 1 — 목표를 SEO 최적(1.7%)보다 낮춰 도배 모드 점프를 막되, 하한에는 붙이지 않는다."""

    def test_default_band_targets_just_above_floor(self) -> None:
        assert regen_target_pct(1.0, 3.5, 1.7) == pytest.approx(1.4)

    def test_target_biases_toward_headroom_not_toward_floor(self) -> None:
        """★실패 방향이 비대칭 — 과밀은 density_fix가 되돌리지만 미달은 되돌릴 수단이 없다.

        따라서 목표는 하한에 붙이면 안 된다. 실측 산문 3,123자 기준으로 하한(1.0%)을 겨우
        넘기는 최소 횟수보다 **최소 2회 이상** 여유가 있어야 한다(자체 재검수에서 1.2 → 1.4 정정).
        """
        chars, kw_len = 3123, 4
        floor_min = math.ceil(1.0 * chars / 100 / kw_len)  # 하한을 넘기는 최소 횟수
        need = target_count(chars, kw_len, regen_target_pct(1.0, 3.5, 1.7))
        assert need - floor_min >= 2, (need, floor_min)

    def test_never_exceeds_seo_optimum_when_optimum_is_inside_band(self) -> None:
        # 하한이 1.5%면 1.5의 1.4배=2.1% > 최적 1.7% → 최적으로 되돌린다(불필요한 과다 노출 방지).
        assert regen_target_pct(1.5, 3.5, 1.7) == pytest.approx(1.7)

    def test_high_floor_category_stays_inside_band(self) -> None:
        # 최적(1.7)이 하한(2.0) 밑이면 쓸 수 없다 — 하한 기준으로 올리되 밴드를 벗어나지 않는다.
        t = regen_target_pct(2.0, 4.0, 1.7)
        assert t == pytest.approx(2.8) and 2.0 <= t <= 4.0

    def test_absurd_band_falls_back_to_midpoint(self) -> None:
        t = regen_target_pct(3.0, 3.4, 1.7)
        assert t == pytest.approx(3.2) and 3.0 <= t <= 3.4

    def test_target_always_inside_band(self) -> None:
        for floor, ceil in ((1.0, 3.5), (1.5, 3.5), (2.0, 4.0), (3.0, 3.4), (0.5, 6.0)):
            assert floor <= regen_target_pct(floor, ceil, DENSITY_TARGET) <= ceil

    def test_cap_leaves_room_but_excludes_the_observed_spam(self) -> None:
        """상한은 목표보다 넉넉하되 라이브 도배(31회)는 확실히 배제해야 한다."""
        need = 10
        assert cap_count(need) == 15
        assert cap_count(need) < 31


class TestPer1000Band:
    """첫 생성엔 산문 길이를 모른다 — 길이에 비례하는 '1,000자당' 표현이라야 안전하다."""

    def test_band_holds_density_inside_gate_across_lengths(self) -> None:
        """모델이 요청 분량(2,000~2,500자)을 넘겨 3,500자를 써도 밴드가 유지돼야 한다.

        ★비율을 그대로 곱해 검산하면 길이가 약분돼 아무것도 검증하지 못한다(자체 점검에서
        적발). 실제로는 모델이 '1,000자당 N회'를 **정수 횟수**로 반올림해 쓰므로, 그 반올림된
        횟수로 밀도를 되계산해 게이트 밴드 안에 있는지 봐야 한다.
        """
        kw_len = 4
        low, high = per_1000_band(kw_len, DENSITY_FLOOR, DENSITY_CEIL, DENSITY_TARGET)
        assert low >= 1 and high > low
        for chars in (1500, 2000, 2500, 3000, 3500, 4200):
            written_low = max(1, round(low * chars / 1000))
            written_high = max(1, round(high * chars / 1000))
            density_low = written_low * kw_len / chars * 100
            density_high = written_high * kw_len / chars * 100
            assert DENSITY_FLOOR <= density_low <= DENSITY_CEIL, (chars, written_low, density_low)
            # 상한까지 꽉 채워 써도 게이트를 넘지 않아야 한다(넘으면 밴드 자체가 함정).
            assert density_high <= DENSITY_CEIL, (chars, written_high, density_high)

    def test_shorter_keyword_needs_more_repeats(self) -> None:
        low4, _ = per_1000_band(4, 1.0, 3.5, 1.7)
        low2, _ = per_1000_band(2, 1.0, 3.5, 1.7)
        assert low2 > low4

    def test_band_matches_the_regen_target_no_float_drift(self) -> None:
        """★부동소수점 드리프트 가드(#48 자체 재검수에서 적발).

        `pct / 100 * chars`처럼 나누기를 먼저 하면 1.4/100이 0.013999…가 되어, 정확히 3.5여야
        할 값이 3.4999…로 내려가 **첫 생성 밴드가 재생성 목표보다 한 회 적게** 나왔다. 첫 생성과
        재생성이 다른 숫자를 가리키면 모델이 사이클마다 다른 목표를 좇는다.
        """
        target = regen_target_pct(DENSITY_FLOOR, DENSITY_CEIL, DENSITY_TARGET)
        for kw_len in (2, 3, 4, 5, 6):
            low, _ = per_1000_band(kw_len, DENSITY_FLOOR, DENSITY_CEIL, DENSITY_TARGET)
            # 1,000자 기준 재생성 목표 횟수와 첫 생성 밴드 하단이 일치해야 한다.
            assert low == target_count(1000, kw_len, target), (kw_len, low)


class TestSeoDirectiveAntiSpam:
    """★#48 근본원인 2·3 — 첫 생성 지시가 도배를 부추기던 문구를 걷어냈는지 고정."""

    def test_no_longer_tells_model_to_write_more_as_body_grows(self) -> None:
        d = build_seo_directive("책상추천", ["원룸 책상"])
        assert "충분히 쓸 것" not in d
        assert "본문이 길수록 더 여러 번" not in d
        assert "1,000자당" in d  # 길이 비례 표현으로 대체됐다

    def test_states_a_hard_cap(self) -> None:
        d = build_seo_directive("책상추천")
        assert "넘기지 마라" in d

    def test_forbids_the_observed_spam_pattern(self) -> None:
        """라이브에서 실제로 나온 도배 형태를 이름으로 금지해야 한다(추상적 '도배 금지'는 실패)."""
        d = build_seo_directive("책상추천")
        assert "상품 소개 문단마다" in d
        assert "FAQ 답변마다" in d
        assert "상품을 가리키는 명사" in d

    def test_substitute_example_is_grammatical_and_not_a_noop(self) -> None:
        """옛 지시는 '책상추천'을 '책상추천'으로 대체하라는 no-op였다."""
        d = build_seo_directive("책상추천")
        assert "가성비 높은 책상이다" in d  # 조사까지 맞은 실제 대체 예시
        assert "가성비 높은 책상추천이다" in d  # ✗ 예시(도배 형태)도 함께 보여준다

    def test_keyword_without_substitute_still_gets_generic_alternative(self) -> None:
        d = build_seo_directive("게이밍의자")
        assert "이 제품" in d and d.count("게이밍의자") >= 1

    def test_empty_primary_emits_nothing(self) -> None:
        assert build_seo_directive("") == ""
        assert build_seo_directive(None) == ""


class TestDensityDirectiveRegen:
    """재생성 지시(①) — 07-30·07-31 실측값으로 고정."""

    _M: ClassVar[dict[str, Any]] = {  # 07-31 draft 39 실측 — 산문 3,215자·'책상추천'(4자)
        "chars": 3215,
        "primary_len": 4,
        "density_floor": 1.0,
        "density_ceil": 3.5,
    }

    def test_target_is_lower_than_session47(self) -> None:
        """#47은 1.7%(약 14회)를 목표로 줘 모델이 도배 모드로 점프했다 → 1.4%로 낮춘다."""
        d = cli._density_directive("책상추천", {**self._M, "primary_freq": 6}, too_low=True)
        assert d is not None
        assert "총 약 11회" in d  # 1.4% * 3215 / 4
        assert "총 약 14회" not in d  # #47이 주던 값(1.7%) — 도배 모드를 유발했다

    def test_low_directive_carries_cap_and_anti_pattern(self) -> None:
        d = cli._density_directive("책상추천", {**self._M, "primary_freq": 6}, too_low=True)
        assert d is not None
        assert "17회를 넘기면" in d  # 절대 상한 동반
        assert "상품 소개 문단마다" in d and "FAQ 답변마다" in d
        assert "직전 생성은 6회뿐이라 미달" in d
        assert "회를 더" not in d  # 차이(delta) 지시 금지는 #47 그대로 유지

    def test_low_directive_drops_the_phrase_that_fueled_overshoot(self) -> None:
        """★'여러 문단·소제목에 고르게 나누세요'가 '단위마다 배치'로 읽힌 정황 → 제거."""
        d = cli._density_directive("책상추천", {**self._M, "primary_freq": 6}, too_low=True)
        assert d is not None
        assert "고르게 나누세요" not in d
        assert "도입부 1~2회" in d and "소제목 1~2회" in d  # 위치별 예산으로 대체

    def test_high_directive_replays_0731(self) -> None:
        d = cli._density_directive("책상추천", {**self._M, "primary_freq": 31}, too_low=False)
        assert d is not None
        assert "31회 써서 과밀" in d
        assert "총 약 11회" in d and "17회를 넘기면" in d
        assert "'책상'·'이 제품'·대명사" in d  # no-op이던 대체어 지시가 실제 대체어를 준다

    def test_missing_metrics_still_falls_back_without_crash(self) -> None:
        assert cli._density_directive("책상추천", {}, too_low=True) is None
        fb = cli._actionable_feedback(
            {"overall_pass": False, "gates": {"seo": {"issues": ["density_low: 밀도 0.4%"]}}},
            "책상추천",
        )
        assert len(fb) == 1 and "책상추천" in fb[0]

    def test_real_gate_pipeline_feeds_the_directive(self) -> None:
        """★드리프트 가드(#47 유지) — 실제 게이트 산출이 정량 지시로 이어지는 계약 고정."""
        body = "# 책상추천 고르는 법\n" + ("가나다라마바사아자차" * 70)
        report = serialize_report(validate_all({"body_md": body, "seo": {"primary": "책상추천"}}))
        assert "metrics" in report["gates"]["seo"]
        quantified = [f for f in cli._actionable_feedback(report, "책상추천") if "총 약" in f]
        assert quantified, "실제 게이트 산출로 정량 지시가 안 나옴"
        assert "원인:" in quantified[0]


def _spam_body(keyword: str = "책상추천", *, sections: int = 8) -> str:
    """07-31 draft 39의 도배 형태를 재현 — 소제목·상품 문단·FAQ 답변마다 키워드 배치."""
    filler = "원룸 자취방 공간을 고려한 배치와 예산 기준을 정리한 설명 문장을 덧붙인다"
    lines = [
        f"# 자취방 {keyword}, 원룸 6평에 딱 맞는 컴퓨터 책상 8선",
        "",
        f"이 {keyword} 가이드는 첫 자취를 앞둔 새내기를 위해 작성되었다. {filler}.",
        "",
        f"## 1. 누구를 위한 {keyword} 가이드인가",
        "",
        f"원룸 6평 기준을 먼저 정리한다. {filler}. 예산 배분도 함께 살핀다.",
        "",
    ]
    for i in range(sections):
        lines += [
            f"### 접이식 책상 {i + 1} ({30 + i}만원대)",
            "",
            f"{30 + i}만원대에서 가성비 높은 {keyword}이다. 상판 크기와 내구성을 함께 본다. "
            f"이 가격대 {keyword} 중에서는 무난한 선택지다. {filler}.",
            "",
        ]
    lines += ["## 6. 자주 묻는 질문", ""]
    for i in range(5):
        lines += [
            f"**Q: {keyword} 질문 {i + 1}**",
            "",
            f"A: 원룸 기준 {keyword}은 폭 80cm가 무난하다. {filler}.",
            "",
        ]
    return "\n".join(lines)


def _payload(body: str, keyword: str = "책상추천") -> dict[str, Any]:
    """★실제 발행 경로와 같은 payload — disclosure 삽입 + Article JSON-LD 포함.

    백스톱은 'density_high **하나만** 남았을 때'만 동작하므로, 다른 게이트가 깨진 반쪽짜리
    payload로 시험하면 늘 미적용이 되어 아무것도 검증하지 못한다(cmd_enrich가 실제로 넘기는
    _build_enriched_payload 형태를 그대로 맞춘다).
    """
    from builder.jsonld import build_article_jsonld
    from writer.article_writer import apply_disclosure

    meta = {
        "title": f"{keyword} 가이드",
        "summary": (
            "원룸 자취방 기준으로 공간과 예산을 함께 고려해 고르는 방법을 정리했다. "
            "배치 기준과 크기 기준을 영역별로 나누어 우선순위와 함께 안내한다."
        ),
        "meta_description": (
            "원룸 6평 자취방 기준 공간·예산별 선택 가이드 — 배치 기준과 크기 기준을 "
            "영역별로 나누어 우선순위와 확인 사항을 한눈에 정리했다."
        ),
        "meta_keywords": f"{keyword},원룸,자취방,신학기,예산",
    }
    return {
        "body_md": apply_disclosure(body, sources={"aliexpress"}),
        "schema_jsonld": build_article_jsonld(
            meta=meta,
            scenario={"slug": "wonroom-desk"},
            site_base_url="https://honsallim.com",
            image_url="https://honsallim.com/static/img/og-default.png",
            published_at="2026-07-31",
        ),
        "products": [],
        "photos": [],
        "seo": {"primary": keyword},
    }


class TestDeterministicBackstop:
    """★#48 ② — 지시로 못 막은 과밀을 LLM 재호출 없이 결정적으로 되돌린다."""

    def test_spam_body_reproduces_the_live_failure(self) -> None:
        """전제 확인 — 재현 본문이 실제로 density_high로 떨어져야 시험이 의미가 있다."""
        report = serialize_report(validate_all(_payload(_spam_body())))
        issues = report["gates"]["seo"]["issues"]
        assert any(str(i).startswith("density_high") for i in issues), issues

    def test_backstop_brings_density_into_band(self) -> None:
        payload = _payload(_spam_body())
        report = serialize_report(validate_all(payload))
        result = density_fix.try_reduce_density(payload, report)
        assert result is not None, "감산이 적용돼야 한다"
        fixed, info = result
        after = serialize_report(validate_all(fixed))
        assert after["overall_pass"], after["gates"]["seo"]["issues"]
        metrics = after["gates"]["seo"]["metrics"]
        assert DENSITY_FLOOR <= metrics["density_pct"] <= DENSITY_CEIL
        assert info["freq_after"] < info["freq_before"]
        assert info["substitute"] == "책상"

    def test_backstop_preserves_title_intro_and_headings(self) -> None:
        """감산이 다른 게이트 요건(제목·도입부·소제목)을 깨뜨리면 안 된다."""
        payload = _payload(_spam_body())
        report = serialize_report(validate_all(payload))
        result = density_fix.try_reduce_density(payload, report)
        assert result is not None
        fixed, _ = result
        before_h1 = next(ln for ln in payload["body_md"].splitlines() if ln.startswith("# "))
        after_h1 = next(ln for ln in fixed["body_md"].splitlines() if ln.startswith("# "))
        assert after_h1 == before_h1 and "책상추천" in after_h1  # H1 원형 보존
        # disclosure(H1 앞)도 손대지 않는다 — 공정위 문구는 감산 대상이 아니다.
        assert fixed["body_md"].split("# ")[0] == payload["body_md"].split("# ")[0]
        after = serialize_report(validate_all(fixed))
        for code in ("title_no_keyword", "intro_no_keyword", "headings_keyword_low"):
            assert not any(str(i).startswith(code) for i in after["gates"]["seo"]["issues"])

    def test_backstop_never_touches_headings(self) -> None:
        payload = _payload(_spam_body())
        report = serialize_report(validate_all(payload))
        result = density_fix.try_reduce_density(payload, report)
        assert result is not None
        fixed, _ = result
        before_h = [ln for ln in payload["body_md"].splitlines() if ln.lstrip().startswith("#")]
        after_h = [ln for ln in fixed["body_md"].splitlines() if ln.lstrip().startswith("#")]
        assert before_h == after_h

    def test_replacement_is_grammatical(self) -> None:
        """'가성비 높은 책상추천이다' → '가성비 높은 책상이다'(조사 유지)."""
        payload = _payload(_spam_body())
        report = serialize_report(validate_all(payload))
        result = density_fix.try_reduce_density(payload, report)
        assert result is not None
        body = result[0]["body_md"]
        assert "가성비 높은 책상이다" in body
        assert "책상추천이다" not in body or body.count("책상추천이다") < 8
        assert "책상다" not in body and "책상은은" not in body

    def test_skips_when_other_gates_also_fail(self) -> None:
        """★적용 조건 — 다른 미달이 있으면 본문을 건드리지 않는다."""
        report = {
            "overall_pass": False,
            "gates": {
                "seo": {"issues": ["density_high: 밀도 4.3%"], "metrics": {}},
                "truth": {"issues": ["first_person_forbidden: 써보니"]},
            },
        }
        assert density_fix.try_reduce_density(_payload(_spam_body()), report) is None

    def test_skips_when_no_safe_substitute(self) -> None:
        payload = _payload(_spam_body("게이밍의자"), "게이밍의자")
        report = serialize_report(validate_all(payload))
        assert density_fix.try_reduce_density(payload, report) is None
        assert "대체어" in density_fix.skip_reason(payload, report)

    def test_skip_reason_is_always_explanatory(self) -> None:
        """무인 운영에서 조용한 미적용을 만들지 않는다(로그에 사유가 남아야 한다)."""
        payload = _payload(_spam_body())
        other = {
            "overall_pass": False,
            "gates": {"seo": {"issues": ["density_high: x"]}, "links": {"issues": ["bad"]}},
        }
        assert density_fix.skip_reason(payload, other)
        assert density_fix.skip_reason(payload, serialize_report(validate_all(payload)))

    def test_backstop_is_idempotent(self) -> None:
        """이미 밴드 안이면 다시 깎지 않는다(반복 적용으로 하한 미달 유발 금지)."""
        payload = _payload(_spam_body())
        report = serialize_report(validate_all(payload))
        result = density_fix.try_reduce_density(payload, report)
        assert result is not None
        fixed, _ = result
        again = serialize_report(validate_all(fixed))
        assert density_fix.try_reduce_density(fixed, again) is None

    def test_backstop_is_actually_wired_into_cmd_enrich(
        self, tmp_path: Any, monkeypatch: Any
    ) -> None:
        """★배선 가드 — 백스톱이 **실제 enrich 경로에서** 호출되는지 end-to-end로 고정.

        #47의 교훈이 정확히 이것이다: 고친 함수가 실제 흐름에 연결되지 않으면 무증상으로
        무력화된다. 단위 테스트로 try_reduce_density만 검증하면 cmd_enrich가 그것을 부르지
        않아도 초록불이 뜬다. LLM은 항상 과밀 본문을 뱉는 가짜로 대체(비용 0)하고, 재시도를
        전부 소진한 뒤 draft가 **게이트 통과 상태로 저장되는지**까지 본다.
        """
        import argparse
        import json

        from collector import keyword_relevance, seo_keywords
        from common import db
        from enricher import claude_client

        tmp_db = tmp_path / "enrich_backstop.db"
        monkeypatch.setattr(db, "DB_PATH", tmp_db)
        db.migrate(db_path=tmp_db)
        db.seed(db_path=tmp_db)
        assert cli.cmd_collect(argparse.Namespace(scenario_slug="wonroom-cheot-jachi-30")) == 0

        keyword = "책상추천"
        # 키워드 글 경로로 만든다 — seo_cfg가 붙어야 seo 게이트가 켜지고 density_high가 난다.
        conn = db.connect(tmp_db)
        try:
            cur = conn.execute(
                "INSERT INTO keyword_queue (keyword, slug, status) VALUES (?, ?, 'drafted')",
                (keyword, "kw-test-desk"),
            )
            conn.execute("UPDATE drafts SET keyword_id = ? WHERE id = 1", (cur.lastrowid,))
            conn.commit()
        finally:
            conn.close()
        monkeypatch.setattr(keyword_relevance, "resolve_category", lambda *a, **k: "desk")
        monkeypatch.setattr(
            seo_keywords,
            "keyword_gate_config",
            lambda *a, **k: {"primary": keyword, "secondary": []},
        )
        meta = {
            "title": f"{keyword} 가이드",
            "summary": (
                "원룸 자취방 기준으로 공간과 예산을 함께 고려해 고르는 방법을 정리했다. "
                "배치 기준과 크기 기준을 영역별로 나누어 우선순위와 함께 안내한다."
            ),
            "meta_description": (
                "원룸 6평 자취방 기준 공간·예산별 선택 가이드 — 배치 기준과 크기 기준을 "
                "영역별로 나누어 우선순위와 확인 사항을 한눈에 정리했다."
            ),
            "meta_keywords": f"{keyword},원룸,자취방,신학기,예산",
            "featured_products": [],
        }
        response = (
            "---META-JSON-START---\n"
            + json.dumps(meta, ensure_ascii=False)
            + "\n---META-JSON-END---\n"
            "---BODY-MARKDOWN-START---\n" + _spam_body(keyword) + "\n---BODY-MARKDOWN-END---\n"
        )
        calls: list[int] = []

        class AlwaysSpamClient:
            model = "fake/no-cost"

            def __init__(self, *a: Any, **k: Any) -> None:
                pass

            def generate_article(self, req: Any, dry_run: bool = True) -> Any:
                calls.append(1)
                return claude_client.GenerateResult(
                    system_blocks=[],
                    user_prompt="x",
                    response_text=response,
                    usage={"input": 1, "output": 1},
                    dry_run=False,
                    stop_reason="end_turn",
                )

        monkeypatch.setattr(claude_client, "ClaudeClient", AlwaysSpamClient)
        monkeypatch.setattr(cli.config, "load_secrets", lambda *a, **k: None)

        assert cli.cmd_enrich(argparse.Namespace(draft=1, dry_run=False)) == 0
        assert calls, "가짜 LLM이 호출되지 않았다 — 테스트가 live 경로를 타지 못했다"

        conn = db.connect(tmp_db)
        try:
            row = conn.execute("SELECT enriched_payload FROM drafts WHERE id = 1").fetchone()
        finally:
            conn.close()
        saved = json.loads(row[0])
        assert "density_fix" in saved, "백스톱이 cmd_enrich에 연결되지 않았다(무증상 무력화)"
        assert saved["density_fix"]["freq_after"] < saved["density_fix"]["freq_before"]
        assert serialize_report(validate_all(saved))[
            "overall_pass"
        ], "저장본이 게이트를 통과해야 한다"

    def test_passing_body_is_not_modified(self) -> None:
        body = "# 책상추천 고르는 법\n\n## 책상추천 기준\n\n" + (
            "책상추천을 고를 때 원룸 크기를 먼저 잰다. " + "설명 문장을 덧붙인다. " * 12
        )
        payload = _payload(body)
        report = serialize_report(validate_all(payload))
        if report["overall_pass"]:
            assert density_fix.try_reduce_density(payload, report) is None
