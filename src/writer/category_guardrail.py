"""writer.category_guardrail — 카테고리 자동 게시 가드레일 (세션 #22).

E7(사람이 매 건 승인)을 대체하는 **fail-closed 자동 판정**. 원칙: "확실히 안전할 때만
통과, 조금이라도 애매하면 보류"(미탐 < 오탐). 통과 → auto_publish가 draft→published 전이.
보류 → draft 유지 + 사유 로깅(사람은 보류된 예외만 본다). 무인 자율·§0.

검사(전부 자동·사람 눈 불필요):
  1. 글 존재          — guide_generated_at·guide_md 채워짐(빈 페이지 차단)
  2. 안전 게이트 재검증 — 저장된 산문에 truth·disclosure·links 재실행(API 불필요)
  3. 추천6선 무결성    — 2개 이상·deeplink 고유/존재·트래킹 태그 일관·가격 존재
  4. 관련성 휴리스틱   — category_sources.yml require/exclude 재적용(추천=엄격·전체=오염율 ≤5%)
  5. 추천6선 LLM 검수  — 키워드가 못 잡는 의미 오염(예: '아기 옷건조대+유아 변기')을 LLM yes/no로.
                         오류·불명확·NO는 전부 보류(fail-closed).

킬스위치: 게시 후 문제 발견 시 writer.category_state.unapprove(published→draft)로 즉시 비공개.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from collector import category_collect, product_filter
from validator import disclosure as disc_gate
from validator import links as links_gate
from validator import truth

# 전체 카탈로그 오염율 상한 — 초과 시 보류(추천6선은 0% 엄격, 꼬리까지 이 비율 이내만 자동 게시).
CONTAMINATION_CAP = 0.05

# LLM 의미검수 보류 임계 — 추천6선 중 이 수 이상이 NO일 때만 보류(세션 #22 라이브 보정).
#   1건 = LLM 노이즈/비결정 가능성(정당한 다기능 제품 오탐) → 관용·기록만. 2건+ = 체계적 오염.
_LLM_HOLD_THRESHOLD = 2

# 추천6선 관련성 LLM 재확인 — 키워드 필터가 못 잡는 의미 오염용.
# 임계 보정(세션 #22 라이브): '다기능이어도 주용도가 맞으면 YES, 명백히 다른 종류면 NO'.
#   너무 엄격하면(애매하면 전부 NO) 정당한 다기능 제품(마늘프레스 달린 도마)까지 떨궈 자동화가
#   무의미해짐 → 양방향 예시로 임계를 명확히. 진짜 오염(사무용의자의 캠핑의자)은 그대로 잡는다.
_RELEVANCE_SYSTEM = (
    "당신은 쇼핑몰 카테고리 분류 검수자다. 각 상품이 주어진 카테고리에 실제로 속하는 제품인지 "
    "판정한다. 상품의 주된 용도가 카테고리에 맞으면 다기능·복합 상품이어도 YES; 명백히 다른 "
    "종류의 물건이면 NO다. 예: '사무용 의자' 카테고리에 캠핑·낚시·화장대 의자는 NO, 마늘프레스가 "
    "달린 '도마'는 도마이므로 YES. 다른 말 없이 번호별로 'n:YES' 또는 'n:NO'만 한 줄씩 출력한다."
)


@dataclass
class GuardrailResult:
    """가드레일 판정 결과. passed=False면 auto_publish가 게시를 보류하고 사유를 보고한다."""

    slug: str
    passed: bool = False
    reasons: list[str] = field(default_factory=list)  # 보류 사유(사람이 볼 예외)
    checks: dict[str, bool] = field(default_factory=dict)  # 항목별 통과 여부(가시화)
    flagged_products: list[str] = field(default_factory=list)  # 오염 의심 상품명


def _relevance_prompt(category_name: str, category_intro: str, names: list[str]) -> str:
    lines = "\n".join(f"{i}. {nm}" for i, nm in enumerate(names, 1))
    intent = f"카테고리: {category_name}"
    if category_intro:
        intent += f"\n카테고리 설명: {category_intro}"
    return (
        f"{intent}\n\n"
        f"다음 각 상품이 이 카테고리의 제품으로 적합한지 판정:\n{lines}\n\n"
        "주된 용도가 맞으면 다기능이어도 YES, 명백히 다른 종류면 NO.\n"
        "출력: 각 번호마다 'n:YES' 또는 'n:NO' 한 줄씩. 설명 금지."
    )


def _parse_verdicts(text: str, n: int) -> dict[int, bool] | None:
    """'n:YES/NO' 라인 파싱 → {idx: bool}. n개를 모두 못 채우면 None(fail-closed)."""
    text = text.replace(chr(0xFF1A), ":")  # 전각 콜론 → ASCII (DeepSeek 출력 변동 대비)
    out: dict[int, bool] = {}
    for m in re.finditer(r"(\d+)\s*:\s*(YES|NO)", text, re.IGNORECASE):
        idx = int(m.group(1))
        if 1 <= idx <= n:
            out[idx] = m.group(2).upper() == "YES"
    return out if len(out) == n else None


def check_featured_relevance_llm(
    client: Any, category_name: str, names: list[str], category_intro: str = ""
) -> tuple[bool, list[str]]:
    """추천6선 LLM 관련성. 반환 (verified, bad):

      verified=True  → LLM이 정상 응답·파싱됨. bad=NO 판정 상품명(빈 리스트면 전부 YES).
      verified=False → LLM 호출·응답 파싱 실패(검증 불가). bad=[사유 1건] → 호출측이 fail-closed 보류.

    호출측은 (verified) 여부와 (bad 개수)를 구분해 처리한다: 검증 실패는 무조건 보류(미탐 방지),
    검증 성공 시 NO 개수가 임계 미만이면 관용(LLM 노이즈). category_intro로 판정 정확도를 높인다.
    """
    if not names:
        return True, []
    try:
        res = client.generate_raw(
            _RELEVANCE_SYSTEM,
            _relevance_prompt(category_name, category_intro, names),
            dry_run=False,
        )
        text = res.response_text or ""
    except Exception as e:  # API·네트워크 오류 — 검증 불가이므로 보류(fail-closed)
        return False, [f"LLM 검수 오류(보류): {type(e).__name__}: {str(e)[:80]}"]
    verdicts = _parse_verdicts(text, len(names))
    if verdicts is None:
        return False, [f"LLM 응답 파싱 실패(보류): {text[:100]!r}"]
    bad = [names[i - 1] for i in range(1, len(names) + 1) if not verdicts.get(i, False)]
    return True, bad


def check(
    conn: sqlite3.Connection,
    slug: str,
    client: Any | None = None,
    *,
    use_llm: bool = True,
) -> GuardrailResult:
    """카테고리 1개 자동 게시 적격 판정. 어떤 항목이라도 미흡하면 사유를 쌓고 passed=False.

    use_llm=True면 추천6선 의미 검수에 client.generate_raw를 호출(client 필수 — 없으면 보류).
    use_llm=False는 휴리스틱까지만(테스트·오프라인 점검용).
    """
    conn.row_factory = sqlite3.Row
    res = GuardrailResult(slug=slug)

    cat = conn.execute(
        "SELECT id, name_ko, intro, guide_md, guide_generated_at FROM categories WHERE slug = ?",
        (slug,),
    ).fetchone()
    if cat is None:
        res.reasons.append("categories에 없음")
        return res
    cid, cname, cintro = cat["id"], cat["name_ko"], (cat["intro"] or "")

    # 1. 글 존재 — build_and_save는 안전 게이트 통과 시에만 저장하므로 글 존재가 곧 통과를
    #    함의하나, fail-closed로 저장본을 직접 재검증(2번)한다.
    has_guide = cat["guide_generated_at"] is not None and bool(cat["guide_md"])
    res.checks["guide_exists"] = has_guide
    if not has_guide:
        res.reasons.append("가이드 글 없음(미생성)")

    # 2. 안전 게이트 재검증(truth·disclosure·links) — 저장된 산문 직접 재실행(API 불필요)
    if has_guide:
        gmd = cat["guide_md"]
        ok_t, _ = truth.check_truth({"body_md": gmd, "products": []})
        ok_d, _ = disc_gate.check_disclosure(gmd)
        ok_l, _ = links_gate.check_links(gmd)
        safe = ok_t and ok_d and ok_l
        res.checks["safety_gates"] = safe
        if not safe:
            failed = [n for n, ok in (("진실성", ok_t), ("고지", ok_d), ("링크", ok_l)) if not ok]
            res.reasons.append("안전 게이트 미통과: " + ", ".join(failed))

    # 3. 추천6선 데이터 무결성
    feats = conn.execute(
        "SELECT p.name, p.price_krw, p.deeplink_url, p.affiliate_tag "
        "FROM category_products cp JOIN products p ON p.id = cp.product_id "
        "WHERE cp.category_id = ? AND cp.is_featured = 1 ORDER BY cp.display_order",
        (cid,),
    ).fetchall()
    feat_names = [f["name"] for f in feats]
    integ_issues: list[str] = []
    if len(feats) < 2:
        integ_issues.append(f"추천 제품 {len(feats)}개(2개 미만)")
    dls = [f["deeplink_url"] for f in feats]
    if any(not d for d in dls):
        integ_issues.append("deeplink 누락")
    elif len(set(dls)) != len(dls):
        integ_issues.append("deeplink 중복(공통링크 의심)")
    tags = {f["affiliate_tag"] for f in feats}
    if any(not t for t in tags):
        integ_issues.append("트래킹 태그 누락")
    elif len(tags) > 1:
        integ_issues.append(f"트래킹 태그 불일치: {sorted(tags)}")
    if any(not f["price_krw"] for f in feats):
        integ_issues.append("가격 누락")
    res.checks["featured_integrity"] = not integ_issues
    if integ_issues:
        res.reasons.append("추천 데이터 무결성: " + "; ".join(integ_issues))

    # 4. 관련성 휴리스틱 — category_sources.yml require/exclude 재적용
    spec = category_collect.load_sources().get(slug)
    if spec is None:
        res.checks["relevance_heuristic"] = False
        res.reasons.append("category_sources.yml 정의 없음(검수 불가·보류)")
    else:

        def _ok(name: str) -> bool:
            return product_filter.is_relevant(
                name,
                require_any=spec.require_any,
                require_all=spec.require_all,
                exclude_terms=spec.exclude_terms,
            )

        feat_bad = [n for n in feat_names if not _ok(n)]
        allrows = conn.execute(
            "SELECT p.name FROM category_products cp JOIN products p ON p.id = cp.product_id "
            "WHERE cp.category_id = ?",
            (cid,),
        ).fetchall()
        total = len(allrows)
        cat_bad = [r["name"] for r in allrows if not _ok(r["name"])]
        contam = (len(cat_bad) / total) if total else 1.0
        res.checks["relevance_heuristic"] = not feat_bad and contam <= CONTAMINATION_CAP
        if feat_bad:
            res.flagged_products += feat_bad
            res.reasons.append("추천 오염(키워드): " + "; ".join(n[:30] for n in feat_bad[:3]))
        if contam > CONTAMINATION_CAP:
            res.reasons.append(
                f"전체 카탈로그 오염율 {contam * 100:.1f}% (>{CONTAMINATION_CAP * 100:.0f}%)"
            )

    # 5. 추천6선 LLM 의미 검수 — 단일 오탐 관용(세션 #22 라이브 보정)
    #    LLM은 다기능 제품명에 노이즈가 있고 temperature로 비결정적이라, '추천 1건이라도 의심이면
    #    전체 보류'로 쓰면 정당한 제품(반도체 미니제습기·브레드보드 도마)에 깨끗한 카테고리까지 막힌다.
    #    → 키워드(명확) 게이트는 엄격 유지하되, LLM(모호)은 _LLM_HOLD_THRESHOLD건 이상 의심일 때만
    #    보류(체계적 오염=office-chair 6/6은 그대로 잡힘). 단일 의심은 기록만(monitor에서 사후 가시화).
    if use_llm:
        if client is None:
            res.checks["relevance_llm"] = False
            res.reasons.append("LLM 검수 불가(client 없음·보류)")
        elif feat_names:
            verified, bad = check_featured_relevance_llm(client, cname, feat_names, cintro)
            if not verified:
                # LLM 호출·파싱 실패 = 검증 불가 → fail-closed 보류(미탐 방지)
                res.checks["relevance_llm"] = False
                res.reasons.append("LLM 검수 불가(보류): " + (bad[0] if bad else ""))
            else:
                res.flagged_products += [b for b in bad if b not in res.flagged_products]
                res.checks["relevance_llm"] = len(bad) < _LLM_HOLD_THRESHOLD
                if len(bad) >= _LLM_HOLD_THRESHOLD:
                    res.reasons.append(
                        f"추천 LLM 검수 {len(bad)}건 의심: " + "; ".join(b[:30] for b in bad[:3])
                    )

    res.passed = not res.reasons
    return res
