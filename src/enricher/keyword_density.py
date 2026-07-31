"""keyword_density — 대표키워드 밀도 '수렴 정책' 단일 소스 (세션 #48).

세션 #47은 재생성 지시를 정성("목표 1.7%로 높이세요")에서 정량("총 약 16회")으로 바꿨지만
라이브에서 수렴하지 않았다. 07-30·07-31 '책상추천' 실측(draft 38·39 본문 전수 확인):

    시도1 = 2회·6회(0.2~0.7%, 자연 문체)  →  "총 약 14~15회" 지시  →  시도2 = 31회(약 4%)

31회의 분포를 보면 LLM이 '횟수를 센' 게 아니라 **문체를 바꿨다** — 소제목 8/10개, 제품 문단
전부, FAQ 답변 전부에 1~2회씩 기계적으로 배치(예: "가성비 높은 책상추천이다"처럼 키워드를
제품 지칭 명사로 사용). 8섹션 표준 구조라 '구조 단위마다 1회'의 총합이 두 날 모두 31회로
같은 값에 수렴했다.

따라서 근본 원인은 세 가지이고, 본 모듈이 그 정책을 한 곳에서 정한다.

1. **이중 모드(bimodal)** — 자연 문체 2~6회 vs 도배 문체 ~31회. 그 사이가 비어 있다.
   게이트 하한 1.0%는 3,200자 산문에서 약 8회를 요구하는데 자연 문체(2~6회)로는 미달이라,
   모델이 "더 써라"를 받으면 자연 문체를 **포기하고** 도배 모드로 건너뛴다.
   → 목표를 SEO 최적(1.7%)이 아니라 **하한 + 20% 여유**로 낮춘다. 자연 문체에서 한 걸음
     거리라 문체를 바꾸지 않고도 도달할 수 있다. 게이트 통과 밴드 안이므로 기준 완화 아님.
2. **상한이 지시에 없었다** — 목표만 주고 "넘기지 말라"는 절대 상한이 없었다. → hard cap 동반.
3. **대체 표현 지시가 no-op** — 옛 `_short_form`은 단일 토큰 키워드('책상추천')에서 자기
   자신을 반환해 "과하면 줄임말로 대체하라"가 아무 뜻도 없었다. → `keyword_substitute`.

★게이트 기준(validator/seo.py DENSITY_FLOOR·CEIL)은 건드리지 않는다. 생성 지시와 사후
  감산의 목표점만 밴드 **안에서** 옮긴다(§0 자가복원 — 기준 완화 금지).
"""

from __future__ import annotations

import math
import re

# 재생성 목표 = 하한에 곱하는 계수. 자연 문체(관찰 2~6회)에서 한 걸음 거리라 도배 모드로
# 점프시키지 않으면서, 하한 미달로도 떨어지지 않아야 한다.
# ★1.2가 아니라 1.4인 이유(#48 자체 재검수에서 정정) — **실패 방향이 비대칭**이기 때문이다.
#   과밀(overshoot)은 density_fix가 결정적으로 되돌릴 수 있지만, 미달(undershoot)은 없는 문장을
#   지어낼 수 없어 **되돌릴 수단이 아예 없다**(그 사이클은 반려로 끝난다). 목표는 하한 쪽이 아니라
#   여유 쪽으로 치우쳐야 한다. 1.2는 실측(산문 3,123자)에서 목표 9회 vs 하한 최소 8회로 **여유가
#   1회뿐**이었다. 1.4는 목표 11회 vs 하한 8회로 3회 여유를 두면서도 도배를 유발한 #47의 14회보다
#   여전히 낮다.
SAFE_MARGIN = 1.4
# hard cap = 목표 에 곱하는 계수(최소 +2). 목표 10회면 상한 15회 — 산문이 30% 짧아져도
# 상한(3.5%)에 닿지 않는 폭이면서, 도배(31회)는 확실히 배제하는 밴드.
CAP_MARGIN = 1.5
# 단일 토큰 복합 키워드에서 떼어낼 꼬리 접미어 — 남는 머리 명사가 자연스러운 대체어가 된다.
# 예 '책상추천'→'책상' · '도마추천'→'도마'. 남는 부분이 2자 미만이면 대체어로 쓰지 않는다.
_TAIL_SUFFIXES = ("추천", "가이드", "순위", "비교", "베스트", "고르는법")


def ns(text: str | None) -> str:
    """공백 제거 — validator/seo.py의 측정 기준(띄어쓰기 무관)과 동일하게 맞춘다."""
    return re.sub(r"\s", "", text or "")


def regen_target_pct(floor: float, ceil: float, seo_optimum: float) -> float:
    """재생성·감산이 겨냥할 목표 밀도(%) — 밴드 [floor, ceil] 안에서 결정.

    기본은 `floor * SAFE_MARGIN`(하한 + 20% 여유). SEO 최적치(네이버 실측 1.7%)보다 높아지는
    경우에만 최적치로 되돌리고(불필요한 과다 노출 방지), 그래도 밴드를 벗어나면 밴드 중앙으로
    폴백한다(카테고리가 하한·상한을 이상하게 오버라이드한 경우 방어).
    """
    target = floor * SAFE_MARGIN
    if seo_optimum < target and seo_optimum >= floor:
        target = seo_optimum
    if not (floor <= target <= ceil):
        target = (floor + ceil) / 2
    return target


def _round_half_up(value: float) -> int:
    """0.5는 항상 올림.

    파이썬 기본 `round()`는 은행가 반올림이라 3.5→4·4.5→4로 어긋나고, 운영자에게 "왜 이
    숫자인가"를 설명할 수 없다. 무인 운영에서 지시 숫자는 재현·설명 가능해야 하므로 고정한다.
    """
    return math.floor(value + 0.5)


def _count_for(pct: float, chars: int, kw_len: int) -> int:
    """밀도(%)를 반복 횟수로 — validator/seo.py 밀도 식의 역산.

    ★곱셈을 먼저 하고 나눗셈을 뒤로 미룬다. `pct / 100 * chars`처럼 나누기를 먼저 하면
    1.4/100이 0.013999…가 되어 정확히 3.5여야 할 값이 3.4999…로 내려가 한 회 적게 나온다
    (#48 자체 재검수에서 적발 — 첫 생성 밴드가 재생성 목표와 어긋나던 원인).
    """
    return max(1, _round_half_up(pct * chars / 100 / kw_len))


def target_count(chars: int, kw_len: int, target_pct: float) -> int:
    """목표 밀도를 만족하는 정확형 반복 횟수."""
    return _count_for(target_pct, chars, kw_len)


def min_count_for(pct: float, chars: int, kw_len: int) -> int:
    """밀도 하한을 넘기는 **최소** 반복 횟수.

    ★#48 라이브 적발: 지시가 상한에만 "탈락"을 붙이고 하한은 "약 N회"로만 말하자 모델이
    한쪽 경고만 추적해 0.78%까지 떨어뜨렸다(미달 탈락). 미달 경계도 숫자로 못박기 위한 값.
    """
    return max(1, math.ceil(pct * chars / 100 / kw_len))


def cap_count(need: int) -> int:
    """절대 상한 횟수 — 목표를 넘겨도 여기까지. 산문 길이가 줄어도 상한을 넘지 않는 폭."""
    return max(need + 2, _round_half_up(need * CAP_MARGIN))


def per_1000_band(kw_len: int, floor: float, ceil: float, seo_optimum: float) -> tuple[int, int]:
    """산문 길이를 모르는 **첫 생성** 프롬프트용 — '1,000자당 N~M회' 밴드.

    첫 생성 시점엔 실제 산문 길이를 알 수 없다(모델이 요청 분량 2,000~2,500자를 넘겨 3,000자
    가까이 쓰는 것이 관찰됨). 길이에 비례하는 '1,000자당' 표현이면 분량이 달라져도 밀도가
    자동으로 유지돼, 절대 횟수를 주고 빗나가는 문제를 애초에 없앤다.
    """
    target = regen_target_pct(floor, ceil, seo_optimum)
    low = _count_for(target, 1000, kw_len)
    # 상한은 밴드 상단이 아니라 목표의 CAP_MARGIN 배 — '넉넉한 상한'을 목표로 오인해
    # 위쪽에 붙는 앵커링을 막는다.
    high = max(low + 1, _round_half_up(low * CAP_MARGIN))
    return low, high


# ── 조사(josa) 안전 치환 ────────────────────────────────────────────────
# 한국어 조사는 앞 음절의 받침 유무로 형태가 갈린다('책상은'/'도마는'). 키워드를 대체어로
# 바꿀 때 받침 유무가 달라지면 뒤 조사도 함께 고쳐야 비문이 안 된다. (받침형, 모음형) 쌍.
# ★긴 형태를 먼저 매칭해야 한다('이다'가 '이'로 잘리면 안 됨) — 아래에서 길이순 정렬.
_JOSA_RAW: tuple[tuple[str, str], ...] = (
    ("이라면", "라면"),
    ("이지만", "지만"),
    ("이라는", "라는"),
    ("이라도", "라도"),
    ("이나마", "나마"),
    ("으로써", "로써"),
    ("으로서", "로서"),
    ("으로", "로"),
    ("이다", "다"),
    ("이라", "라"),
    ("이란", "란"),
    ("이나", "나"),
    ("이며", "며"),
    ("이면", "면"),
    ("이야", "야"),
    ("이랑", "랑"),
    ("이든", "든"),
    ("은", "는"),
    ("이", "가"),
    ("을", "를"),
    ("과", "와"),
)
_JOSA_PAIRS: tuple[tuple[str, str], ...] = tuple(sorted(_JOSA_RAW, key=lambda p: -len(p[0])))
# '으로/로'만 예외 — ㄹ 받침은 받침이 있어도 모음형('로')을 쓴다('서울로').
_RIEUL_EXCEPTIONS = frozenset({"으로", "으로써", "으로서"})
_HANGUL_BASE = 0xAC00
_HANGUL_LAST = 0xD7A3
_JONG_COUNT = 28
_JONG_RIEUL = 8


def _jong(ch: str) -> int | None:
    """한글 음절의 종성 인덱스(0=받침 없음). 한글 음절이 아니면 None."""
    if not ch:
        return None
    code = ord(ch)
    if not (_HANGUL_BASE <= code <= _HANGUL_LAST):
        return None
    return (code - _HANGUL_BASE) % _JONG_COUNT


def _takes_batchim_form(word: str, josa_batchim: str) -> bool | None:
    """word 뒤에 josa가 붙을 때 받침형을 쓰는가. 한글로 끝나지 않으면 None(판정 불가)."""
    jong = _jong(ns(word)[-1:] or "")
    if jong is None:
        return None
    if josa_batchim in _RIEUL_EXCEPTIONS and jong == _JONG_RIEUL:
        return False  # '서울로' — ㄹ 받침은 모음형
    return jong != 0


def join_josa(word: str, josa_batchim: str) -> str:
    """word에 조사를 문법에 맞는 형태로 붙인다(josa_batchim = 받침형 표기)."""
    pair = next((p for p in _JOSA_PAIRS if p[0] == josa_batchim), None)
    if pair is None:
        return word + josa_batchim
    use_batchim = _takes_batchim_form(word, josa_batchim)
    if use_batchim is None:
        return word + pair[0]
    return word + (pair[0] if use_batchim else pair[1])


def _is_boundary(after: str) -> bool:
    """치환 지점 뒤가 '조사가 붙지 않은' 자리인가 — 빈 문자열·공백·문장부호·비한글."""
    return _jong(after[:1]) is None


def rewrite_following_josa(after: str, old_word: str, new_word: str) -> tuple[bool, int, str]:
    """키워드를 대체어로 바꿀 때 **바로 뒤 조사**를 새 단어에 맞게 고친다.

    반환 `(안전한가, 소비할 원문 길이, 새로 쓸 조사)`.
    - 두 단어가 모든 조사에서 같은 형태를 고르면(받침 유무·ㄹ 여부 동일) 조사를 건드릴 필요가
      없다 → `(True, 0, "")`. 실패한 키워드 대부분이 여기에 해당한다('책상추천'→'책상' 둘 다 받침).
    - 형태가 갈리면, 뒤에 붙은 조사를 **알려진 목록에서만** 찾아 짝으로 바꾼다. 조사 뒤가
      한글 음절이면(예 '…추천은행') 조사인지 단어 일부인지 확정할 수 없으므로 **불안전 판정**
      → 호출자가 그 자리를 건너뛴다. 애매하면 건드리지 않는다(§0 안전 우선).
    """
    old_jong = _jong(ns(old_word)[-1:] or "")
    new_jong = _jong(ns(new_word)[-1:] or "")
    if old_jong is None or new_jong is None:
        return False, 0, ""  # 한글로 끝나지 않으면 조사 형태를 판정할 수 없다
    # 두 단어가 모든 조사에서 같은 형태를 고르면 뒤를 볼 필요조차 없다(가장 흔한 경우).
    if (old_jong != 0) == (new_jong != 0) and (old_jong == _JONG_RIEUL) == (
        new_jong == _JONG_RIEUL
    ):
        return True, 0, ""
    if _is_boundary(after):
        return True, 0, ""  # 조사가 안 붙은 자리 — 그대로 치환해도 안전
    # 받침 유무가 갈리는데 뒤에 한글이 붙어 있다 — 조사 목록에서만 인정하고, 애매하면 포기.
    for batchim, vowel in _JOSA_PAIRS:
        old_batchim = _takes_batchim_form(old_word, batchim)
        new_batchim = _takes_batchim_form(new_word, batchim)
        if old_batchim is None or new_batchim is None:
            return False, 0, ""
        old_form = batchim if old_batchim else vowel
        if not after.startswith(old_form):
            continue
        if not _is_boundary(after[len(old_form) :]):
            return False, 0, ""  # 조사 뒤에 또 한글 — 조사가 아니라 단어 일부일 수 있다
        if old_batchim == new_batchim:
            return True, 0, ""
        return True, len(old_form), (batchim if new_batchim else vowel)
    return False, 0, ""


def keyword_substitute(primary: str | None) -> str | None:
    """대표키워드를 대신할 자연스러운 짧은 표현. 없으면 None(대체 지시·감산 모두 생략).

    옛 `seo_directive._short_form`은 다단어면 마지막 토큰, 단일어면 **자기 자신**을 반환했다.
    실패한 '책상추천'·'스텐도마'·'도마추천'이 전부 단일 토큰이라 "과하면 줄임말로 대체하라"는
    지시가 `'책상추천'을 '책상추천'으로 대체하라`가 되어 아무 효과가 없었다(#48 적발).

    순서: ①꼬리 접미어 제거('책상추천'→'책상', '책상 추천'→'책상') ②다단어면 마지막 토큰
    ('노트북 거치대'→'거치대'). 둘 다 못 구하면 None — 억지 대체어를 만들지 않는다.
    """
    p = (primary or "").strip()
    if not p:
        return None
    compact = ns(p)
    for suffix in _TAIL_SUFFIXES:
        if compact.endswith(suffix) and len(compact) - len(suffix) >= 2:
            return compact[: -len(suffix)]
    parts = p.split()
    if len(parts) > 1 and len(parts[-1]) >= 2:
        return parts[-1]
    return None
