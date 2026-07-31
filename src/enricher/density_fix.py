"""density_fix — density_high 결정적 감산 백스톱 (세션 #48).

무인 발행이 07-30·07-31 이틀 연속 0편이 된 경로:

    시도1 미달(2~6회) → 정량 지시 → 시도2 도배(31회·약 4%) → 재시도 상한 도달 → 반려 → 발행 0편

지시(seo_directive·keyword_density)를 고쳐도 LLM 출력은 확률적이라 **수렴을 보장하지 못한다**.
과밀 방향만큼은 결정적으로 되돌릴 수 있으므로, LLM 재호출 없이(비용 0) 초과분을 대체어로
바꿔 밴드 안으로 되돌리는 마지막 백스톱을 둔다. #47이 지시만 고쳐 실패한 것의 근본 보강이다.

★적용 조건을 매우 좁게 잡는다(§0 안전 우선 — 본문을 함부로 고치지 않는다):
- 5게이트 중 **seo의 density_high 하나만** 남았을 때만 동작. 다른 미달이 하나라도 있으면 미적용.
- 제목(H1)·H1 앞(공정위 고지)·**모든 소제목**·**첫 산문 등장**은 절대 건드리지 않는다
  (title/intro/headings 요건 보존).
- 조사 형태가 갈리는데 뒤 글자가 애매하면 그 자리는 **건너뛴다**(keyword_density 조사 판정).
- 감산 후 **5게이트를 전부 다시 돌려** overall_pass가 아니면 원문으로 되돌린다.
- 대체어를 못 구하거나(단일 토큰·접미어 없음) 안전한 자리가 모자라면 **아무것도 하지 않는다**
  — 그때는 기존대로 반려되고 [ALERT]가 뜬다(조용한 실패 없음).
"""

from __future__ import annotations

import re
from typing import Any

from validator.seo import DENSITY_TARGET

from .keyword_density import keyword_substitute, ns, regen_target_pct, rewrite_following_josa

_HEADING_RE = re.compile(r"^\s*#{1,6}\s")
_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")


def _flexible_pattern(primary: str) -> re.Pattern[str]:
    """'책상추천'과 '책상 추천'을 모두 잡는 정규식 — 게이트가 띄어쓰기 무관으로 세기 때문."""
    return re.compile(r"\s*".join(re.escape(ch) for ch in ns(primary)))


def _only_density_high(report: dict[str, Any]) -> bool:
    """5게이트 통틀어 남은 미달이 seo density_high 하나뿐인가."""
    found = False
    for name, gate in (report.get("gates") or {}).items():
        for issue in gate.get("issues", []) or []:
            if name == "seo" and str(issue).startswith("density_high"):
                found = True
                continue
            return False
    return found


def _even_indices(total: int, pick: int) -> list[int]:
    """total개 중 pick개를 고르게 선택 — 감산 후에도 분포가 한쪽으로 쏠리지 않게."""
    if pick <= 0:
        return []
    if pick >= total:
        return list(range(total))
    if pick == 1:
        return [total - 1]
    return sorted({round(i * (total - 1) / (pick - 1)) for i in range(pick)})


def _candidates(
    lines: list[str], h1_idx: int, pattern: re.Pattern[str], substitute: str
) -> list[tuple[int, int, int, int, str]]:
    """치환해도 안전한 자리 목록 — (줄번호, 시작, 끝, 소비할 조사 길이, 새 조사)."""
    out: list[tuple[int, int, int, int, str]] = []
    first_kept = False
    for i in range(h1_idx + 1, len(lines)):
        line = lines[i]
        if _HEADING_RE.match(line):
            continue  # 소제목 — headings_keyword_low 방지를 위해 보존
        for m in pattern.finditer(line):
            if not first_kept:
                first_kept = True  # 첫 산문 등장 — intro_no_keyword 방지를 위해 보존
                continue
            ok, consume, josa = rewrite_following_josa(line[m.end() :], m.group(0), substitute)
            if ok:
                out.append((i, m.start(), m.end(), consume, josa))
    return out


def _apply(
    lines: list[str], spans: list[tuple[int, int, int, int, str]], substitute: str
) -> list[str]:
    """선택된 자리를 대체어로 치환 — 줄 안에서는 오른쪽부터 적용해 인덱스를 보존."""
    out = list(lines)
    for i, start, end, consume, josa in sorted(spans, key=lambda s: (-s[0], -s[1])):
        line = out[i]
        out[i] = line[:start] + substitute + josa + line[end + consume :]
    return out


def try_reduce_density(
    payload: dict[str, Any], report: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """density_high만 남은 본문을 결정적으로 감산. 실패·미적용이면 None.

    반환: (감산된 payload 사본, 요약 info). 호출자는 info를 로그·payload에 남긴다.
    """
    from validator import serialize_report, validate_all

    if not _only_density_high(report):
        return None
    seo_cfg = payload.get("seo") or {}
    primary = str(seo_cfg.get("primary") or "").strip()
    body_md = payload.get("body_md") or ""
    if not primary or not body_md:
        return None
    substitute = keyword_substitute(primary)
    if not substitute or ns(primary) in ns(substitute):
        return None  # 대체어 없음 — 억지로 만들지 않는다(호출자가 사유를 로그)

    metrics = ((report.get("gates") or {}).get("seo") or {}).get("metrics") or {}
    try:
        floor = float(metrics.get("density_floor") or 0.0)
        ceil = float(metrics.get("density_ceil") or 0.0)
        before_pct = float(metrics.get("density_pct") or 0.0)
        before_freq = int(metrics.get("primary_freq") or 0)
    except (TypeError, ValueError):
        return None
    if floor <= 0 or ceil <= floor:
        return None
    target_pct = regen_target_pct(floor, ceil, DENSITY_TARGET)

    lines = body_md.splitlines()
    h1_idx = next((i for i, ln in enumerate(lines) if _H1_RE.match(ln)), -1)
    cands = _candidates(lines, h1_idx, _flexible_pattern(primary), substitute)
    if not cands:
        return None

    # ★예측식 대신 **실제 게이트로 측정**한다 — 대체어 길이차·띄어쓰기·인접 결합 같은 변수를
    #   계산으로 맞히려다 틀리느니, 후보 수만큼 돌려보고 통과하는 것 중 목표에 가장 가까운 것을
    #   고른다(순수 문자열 연산이라 비용 0). 후보는 수십 개 수준.
    best: tuple[float, int, list[str], dict[str, Any]] | None = None
    for n in range(1, len(cands) + 1):
        picked = [cands[i] for i in _even_indices(len(cands), n)]
        trial_lines = _apply(lines, picked, substitute)
        trial_body = "\n".join(trial_lines)
        trial_payload = {**payload, "body_md": trial_body}
        trial_report = serialize_report(validate_all(trial_payload))
        if not trial_report["overall_pass"]:
            continue
        seo_metrics = trial_report["gates"]["seo"].get("metrics") or {}
        pct = float(seo_metrics.get("density_pct") or 0.0)
        distance = abs(pct - target_pct)
        if best is None or distance < best[0]:
            best = (distance, n, trial_lines, trial_report)
    if best is None:
        return None

    _, removed, new_lines, new_report = best
    new_payload = {**payload, "body_md": "\n".join(new_lines)}
    after_metrics = new_report["gates"]["seo"].get("metrics") or {}
    info = {
        "applied": True,
        "keyword": primary,
        "substitute": substitute,
        "replaced": removed,
        "candidates": len(cands),
        "freq_before": before_freq,
        "freq_after": int(after_metrics.get("primary_freq") or 0),
        "density_before": round(before_pct, 2),
        "density_after": float(after_metrics.get("density_pct") or 0.0),
        "target_pct": round(target_pct, 2),
    }
    return new_payload, info


def skip_reason(payload: dict[str, Any], report: dict[str, Any]) -> str:
    """백스톱이 동작하지 않은 이유 — 무인 운영에서 조용한 실패를 만들지 않기 위한 로그용."""
    if not _only_density_high(report):
        return "density_high 외 다른 게이트 미달도 있어 미적용"
    primary = str((payload.get("seo") or {}).get("primary") or "").strip()
    substitute = keyword_substitute(primary)
    if not substitute:
        return f"'{primary}'의 안전한 대체어를 못 구함(단일 토큰·접미어 없음)"
    return "안전한 치환 자리가 부족하거나 감산 후에도 게이트 미통과"
