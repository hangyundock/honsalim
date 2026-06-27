"""category_config_gen — 한글 카테고리명 → 수집 설정(CategorySpec) 자동 생성 (세션 #35, ②).

새 카테고리를 만들 때 사람이 category_sources.yml에 영어 검색어·가격밴드·관련성 단어를 손으로
적던 병목을 제거한다. 한글 카테고리명(예: "가습기")을 주면 LLM이 알리 영어 검색어 2티어(실속·
고급)와 KRW 가격밴드, 핵심어·제외어를 JSON으로 생성한다.

관련성의 무거운 짐은 vision_relevance 게이트가 진다(이미지 의미 판정). 그래서 여기서 생성하는
exclude_terms는 최소만으로 충분하다 — LLM이 완벽한 제외어 리스트를 못 만들어도 비전이 backstop.

LLM은 기본 DeepSeek(OpenRouter) — Anthropic 키 불필요(비전 게이트만 Anthropic). dry_run·client
주입으로 비용 0 검증·테스트 가능.
"""

from __future__ import annotations

import json
import re
from typing import Any

from collector.category_collect import CategorySpec
from collector.keyword_map import SearchTerm

_SYSTEM = (
    "너는 1인가구·자취 어필리에이트 사이트의 상품 카테고리 설정을 만드는 도우미다. "
    "주어진 한글 카테고리에 대해 AliExpress 영어 검색어와 KRW 가격대를 정한다. "
    "반드시 JSON만 출력한다."
)

_USER = """한글 카테고리: "{label}"

이 카테고리의 알리익스프레스 수집 설정을 JSON으로 만들어라.
- core: 이 카테고리의 한글 핵심어 1개 (상품명에 보통 들어가는 단어)
- exclude: 헷갈리기 쉬운 다른 품목 한글 단어 0~6개 (없으면 빈 배열)
- tiers.budget: 실속형 — q(영어 검색어), min/max(KRW 정수)
- tiers.premium: 고급형 — q(영어 검색어, budget과 다르게 구체적), min/max(KRW 정수)

규칙: 가격대는 budget < premium로 겹치지 않게. q는 실제 알리에서 쓰는 일반 영어 명칭.
JSON만 출력: {{"core":"...","exclude":["..."],"tiers":{{"budget":{{"q":"...","min":0,"max":0}},"premium":{{"q":"...","min":0,"max":0}}}}}}"""


def _strip_fence(text: str) -> str:
    """코드펜스·잡음 제거."""
    t = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    return re.sub(r"```$", "", t).strip()


def _parse_json(text: str) -> dict[str, Any]:
    """LLM 응답에서 JSON 객체 추출 (첫 { } 블록)."""
    t = _strip_fence(text)
    m = re.search(r"\{.*\}", t, re.DOTALL)
    return dict(json.loads(m.group(0) if m else t, strict=False))


def _parse_json_array(text: str) -> list[Any]:
    """LLM 응답에서 JSON 배열 추출 (첫 [ ] 블록)."""
    t = _strip_fence(text)
    m = re.search(r"\[.*\]", t, re.DOTALL)
    parsed = json.loads(m.group(0) if m else t, strict=False)
    return list(parsed) if isinstance(parsed, list) else []


_SUGGEST_SYSTEM = (
    "너는 1인가구·자취 어필리에이트 사이트의 신규 상품 카테고리를 제안하는 도우미다. "
    "반드시 JSON 배열만 출력한다."
)

_SUGGEST_USER = """1인가구·자취·홈오피스·일상살림에 적합한 신규 상품 카테고리 {n}개를 제안하라.
이미 있는 카테고리(제외): {existing}

규칙: 알리익스프레스에서 살 수 있는 구체적 '품목' 단위(너무 넓은 범주 금지). 이미 있는 것과 겹치지 말 것.
JSON 배열만 출력: [{{"label":"한글 품목명","reason":"1인가구에 적합한 이유 한 줄"}}]"""


def _despace(s: str) -> str:
    return "".join((s or "").split()).lower()


def suggest_categories(
    existing_labels: list[str],
    n: int = 5,
    *,
    client: Any = None,
    dry_run: bool = False,
    model: str | None = None,
) -> list[dict[str, str]]:
    """기존 카테고리를 제외한 신규 품목 후보 제안 — [{label, reason}]. (①, 세션 #35)

    LLM 브레인스토밍 + 기존명 중복 제거(despace). dry_run=True면 빈 리스트(비용 0). 후보는
    제안일 뿐 — 실제 품질은 ②설정생성·수집·비전게이트가 downstream에서 보증한다.
    """
    if client is None:
        from common import settings
        from enricher.claude_client import ClaudeClient

        client = ClaudeClient(model=model or settings.get("llm_model"))
    existing_str = ", ".join(existing_labels) if existing_labels else "(없음)"
    result = client.generate_raw(
        _SUGGEST_SYSTEM, _SUGGEST_USER.format(n=n, existing=existing_str), dry_run=dry_run
    )
    text = getattr(result, "response_text", None)
    if dry_run or not text:
        return []
    seen = {_despace(x) for x in existing_labels}
    out: list[dict[str, str]] = []
    for item in _parse_json_array(str(text)):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        if not label or _despace(label) in seen:
            continue
        seen.add(_despace(label))
        out.append({"label": label, "reason": str(item.get("reason", "")).strip()})
        if len(out) >= n:
            break
    return out


def _int_or_none(v: Any) -> int | None:
    return int(v) if isinstance(v, (int, float)) and v > 0 else None


def parse_config(text: str) -> dict[str, Any]:
    """LLM JSON 텍스트 → 정규화된 설정 dict. 필수(tiers.budget.q·premium.q) 없으면 ValueError."""
    raw = _parse_json(text)
    tiers_raw = raw.get("tiers") or {}
    tiers: dict[str, dict[str, Any]] = {}
    for name in ("budget", "premium"):
        t = tiers_raw.get(name) or {}
        q = str(t.get("q", "")).strip()
        if not q:
            raise ValueError(f"tiers.{name}.q 누락 — 설정 생성 실패")
        tiers[name] = {"q": q, "min": _int_or_none(t.get("min")), "max": _int_or_none(t.get("max"))}
    core = str(raw.get("core", "")).strip()
    if not core:
        raise ValueError("core(핵심어) 누락 — 설정 생성 실패")
    exclude = [str(x).strip() for x in (raw.get("exclude") or []) if str(x).strip()]
    return {"core": core, "exclude": exclude, "tiers": tiers}


def to_spec(slug: str, config: dict[str, Any]) -> CategorySpec:
    """정규화 설정 → CategorySpec. require_any=()(비전 게이트가 관련성 전담)·require_all=().

    require_any를 비운다(세션 #36 근본수정·라이브 실증). 알리는 한글 '기계번역' 상품명을 돌려주는데,
    core는 "미니 전기밥솥" 같은 특정 다어절 문구라 번역 변형("미니 전기 밥솥" 등)으로 통째 부분일치가
    거의 안 된다(30건 중 0~2건만 통과 → 비전 게이트가 굶음). 그래서 한글 core를 require_any로 강제하면
    #35 주석("관련성은 비전이 담당")과 정면으로 모순돼 자동 수집이 0편이 됐다. 키워드 사전필터는
    exclude_terms(저렴한 명백 제외)만 적용하고, '이게 그 물건인가'의 정밀 판정은 vision_relevance가
    이미지로 전담한다(provision은 vision=True 강제). core는 설정에 남되 사전필터엔 쓰지 않는다.
    """
    tiers = {
        name: SearchTerm(q=t["q"], min_price=t.get("min"), max_price=t.get("max"))
        for name, t in config["tiers"].items()
    }
    return CategorySpec(
        slug=slug,
        require_any=(),
        require_all=(),
        exclude_terms=tuple(config.get("exclude") or ()),
        tiers=tiers,
    )


def generate_config(
    label_ko: str, *, client: Any = None, dry_run: bool = False, model: str | None = None
) -> dict[str, Any]:
    """한글 카테고리명 → 정규화 설정 dict. client 주입 시 그걸 사용(테스트), 아니면 기본 LLM.

    dry_run=True면 빈 dict 반환(프롬프트만 — 비용 0). 실제 생성은 dry_run=False.
    """
    if client is None:
        from common import settings
        from enricher.claude_client import ClaudeClient

        client = ClaudeClient(model=model or settings.get("llm_model"))
    result = client.generate_raw(_SYSTEM, _USER.format(label=label_ko), dry_run=dry_run)
    text = getattr(result, "response_text", None)
    if dry_run or not text:
        return {}
    return parse_config(str(text))
