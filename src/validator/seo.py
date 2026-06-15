"""seo 게이트 — 키워드 밀도·배치 (카테고리 비교·정보 페이지 SEO 최적화).

출처: AutoBlog `AUTOBLOG_SEO_MASTER.md` §3 + `tistory_revival/seo_gate.py` +
      `tistory_revival/WRITING_SPEC.md` 실측(네이버 상위 10 SERP 분석) [확정].
세션 #15: AutoBlog seo_gate.py를 혼살림 카테고리 페이지용으로 포팅. ★네이버 기준(다음 무시).

블로그 글 게이트와의 설계 차이:
- **산문(editorial prose)만 측정** — 상품명·가격·버튼 UI는 enrich 산문 밖이라 자연 제외.
  제목(H1)은 본문에서 떼어 별도 검사(밀도 측정 대상에서 제외).
- **대표키워드(primary, =#1) 정확형 밀도 ~1.7%(네이버)** 를 하드 검증. **보조키워드(secondary,
  네이버 연관검색어) 존재는 warning(자문)** — #1만 하드로 잡아 재생성 비용을 막는다(세션 #15).
- **opt-in**: payload에 "seo" 설정이 없으면 skip(pass) — 기존 세팅 글 파이프라인 무영향.
- **issues(하드 fail) / warnings(자문)** 분리 — 무인 자동 + 인간 편집 게이트(§2-마) 둘 다 지원.

가드레일(§0 안전):
- 밀도 하한·상한 둘 다 강제 — 과밀(도배)은 Google/네이버 어뷰징 패널티라 상한도 fail.
- 카운트는 모두 **띄어쓰기 무관**("사무용 의자"="사무용의자")로 측정(검색엔진 매칭과 동일).
"""

from __future__ import annotations

import re
from typing import Any

# ★ 네이버 기준 (세션 #15 사용자 결정: 다음 무시·네이버 검색량이 압도적 → 네이버만 잡는다).
#   WRITING_SPEC 네이버 실측 = 밀도 1.67% · 도입부 키워드 80% · 소제목 적음(평균 2).
# ★ 게이트 과민 = 불필요 재생성 = 실제 결제 비용 (tistory 세션 #7·#10 교훈). 그래서:
#   - 하드 fail은 대표키워드(=#1) 필수 항목만. 보조키워드·소제목 수는 warning(재생성 트리거 X).
#   - 상한은 넉넉히(3.5%) — 정상 글이 과밀로 오탐돼 재생성되는 비용 방지.
DENSITY_FLOOR = 1.0  # % — 미만이면 대표키워드를 사실상 안 쓴 글
DENSITY_CEIL = 3.5  # % — 초과면 과밀(도배)=스팸. 넉넉히 둬 오탐 재생성 비용 방지
DENSITY_TARGET = 1.7  # % — 네이버 상위 실측(directive·운영자 안내용 목표치)
INTRO_CHARS = 200  # 도입부 정의 — 산문 공백 제거 후 앞 N자
MIN_KW_IN_HEADINGS = 1  # 소제목 중 대표키워드 포함 최소 개수 (하드, 네이버 경량 — ≥1만)
TITLE_FRONT_MAX = 20  # 제목에서 대표키워드 시작 위치(공백 제거 기준) — 초과 시 warning(soft)
MIN_HEADINGS = 4  # 소제목 최소 개수 — 미만 시 warning(정보 깊이 권장, 재생성 트리거 X)
SECONDARY_MIN_RATIO = 0.5  # 보조키워드 존재율 하한 — 미만 시 warning(하드 아님, #1만 하드)


def _ns(text: str | None) -> str:
    """띄어쓰기·개행 등 모든 공백 제거 (검색엔진 키워드 매칭과 동일 기준)."""
    return re.sub(r"\s", "", text or "")


def _split_title_body(body_md: str, explicit_title: str) -> tuple[str, str]:
    """본문에서 첫 H1(`# 제목`) 줄을 떼어 (title, prose)로 분리.

    explicit_title이 있으면 그것을 title로 쓰고, H1 줄은 산문에서 제외만 한다.
    H1이 없으면 explicit_title을 title로, 본문 전체를 산문으로 본다.

    ★세션 #33: H1(제목) **앞**의 줄(시스템이 맨 앞에 삽입하는 공정위 disclosure 문구·서문)은
    산문 측정에서 제외한다. disclosure는 SEO 콘텐츠가 아닌데 도입부 앞 N자를 차지해
    intro_no_keyword·밀도 측정을 왜곡하던 버그의 근본 수정(disclosure 존재는 별도 게이트가 검증).
    """
    title = (explicit_title or "").strip()
    lines = body_md.splitlines()
    h1_idx = -1
    for i, line in enumerate(lines):
        m = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if m:
            h1_idx = i
            if not title:
                title = m.group(1).strip()
            break
    # H1이 있으면 그 이후만 산문(앞 서문·disclosure 제외). H1이 없으면 전체(현행 보존).
    prose_lines = lines[h1_idx + 1 :] if h1_idx >= 0 else lines
    return title, "\n".join(prose_lines)


def check_seo(payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """seo 게이트 검사 (세션 #15).

    payload 기대 키:
    - body_md : 본문 Markdown (첫 `# 제목` 줄은 제목으로 분리, 나머지를 산문으로 측정)
    - title   : (선택) 명시 제목. 없으면 body_md의 H1에서 추출
    - seo     : {
          "primary":   "사무용 의자",            # 대표키워드(필수)
          "secondary": ["가성비 사무용 의자", ...],  # 보조키워드(선택, 네이버 연관검색어)
          "density_floor": 1.0,  # (선택) 카테고리별 하한 오버라이드
          "density_ceil":  3.5,  # (선택) 상한 오버라이드
      }

    seo 또는 seo.primary가 없으면 skip(pass) — 기존 파이프라인 무영향.

    반환: (pass, {"issues": [...], "warnings": [...], "metrics": {...}, "gate": "seo"}).
    """
    seo = payload.get("seo") or {}
    primary = (seo.get("primary") or "").strip()
    if not primary:
        return True, {
            "issues": [],
            "warnings": [],
            "metrics": {"skipped": True},
            "gate": "seo",
        }

    secondary = [s for s in (seo.get("secondary") or []) if s and s.strip()]
    # `or` 형태 — yml에서 키가 None/누락/0으로 와도 기본값으로 안전 복원 (§0 자가복원).
    floor = float(seo.get("density_floor") or DENSITY_FLOOR)
    ceil = float(seo.get("density_ceil") or DENSITY_CEIL)

    body_md = payload.get("body_md") or ""
    title, prose = _split_title_body(body_md, payload.get("title") or "")

    prose_ns = _ns(prose)
    chars = len(prose_ns)
    primary_ns = _ns(primary)
    freq = prose_ns.count(primary_ns)
    density = freq * len(primary_ns) / max(chars, 1) * 100

    headings = re.findall(r"^\s*#{2,6}\s*(.+?)\s*$", prose, re.M)
    kw_in_h = sum(1 for h in headings if primary_ns in _ns(h))

    intro = prose_ns[:INTRO_CHARS]
    title_ns = _ns(title)

    present_secondary = [s for s in secondary if _ns(s) in prose_ns]
    missing_secondary = [s for s in secondary if _ns(s) not in prose_ns]

    issues: list[str] = []
    warnings: list[str] = []

    # 밀도 (하한·상한 둘 다 강제)
    if chars == 0:
        issues.append("density_empty: 산문 본문이 비어 있음")
    elif density < floor:
        issues.append(
            f"density_low: 대표키워드 '{primary}' 밀도 {density:.2f}% < {floor}% "
            f"(네이버 목표 ~{DENSITY_TARGET}%, 정확형 노출을 늘릴 것)"
        )
    elif density > ceil:
        issues.append(
            f"density_high: 대표키워드 '{primary}' 밀도 {density:.2f}% > {ceil}% "
            f"(도배 = 스팸/어뷰징 위험, 줄일 것)"
        )

    # 제목
    if not title_ns:
        issues.append("title_missing: 대표키워드 포함 제목 필요")
    elif primary_ns not in title_ns:
        issues.append(f"title_no_keyword: 제목에 대표키워드 '{primary}' 없음")
    elif title_ns.find(primary_ns) > TITLE_FRONT_MAX:
        warnings.append(
            f"title_keyword_late: 제목 내 대표키워드가 {title_ns.find(primary_ns)}자 뒤 "
            f"— 앞쪽 배치 권장"
        )

    # 도입부
    if chars and primary_ns not in intro:
        issues.append(f"intro_no_keyword: 도입부(앞 {INTRO_CHARS}자)에 대표키워드 '{primary}' 없음")

    # 소제목 내 대표키워드
    if kw_in_h < MIN_KW_IN_HEADINGS:
        issues.append(
            f"headings_keyword_low: 소제목 내 대표키워드 {kw_in_h}개 < {MIN_KW_IN_HEADINGS}개"
        )

    # 소제목 수 (정보 깊이 — soft)
    if len(headings) < MIN_HEADINGS:
        warnings.append(
            f"headings_few: 소제목 {len(headings)}개 < {MIN_HEADINGS}개 (정보 깊이 보강 권장)"
        )

    # 보조키워드 존재 — ★ warning만 (하드 fail 아님). "#1(대표)만 잡고 간다"(세션 #15 사용자) +
    # 보조 미달로 재생성하면 키워드 욱여넣기·재생성 비용 유발 → 자문으로만 surfacing(인간 검토).
    if secondary:
        ratio = len(present_secondary) / len(secondary)
        if ratio < SECONDARY_MIN_RATIO:
            warnings.append(
                f"secondary_coverage_low: 보조키워드 존재율 {ratio * 100:.0f}% "
                f"< {SECONDARY_MIN_RATIO * 100:.0f}% (누락: {missing_secondary})"
            )
        elif missing_secondary:
            warnings.append(
                f"secondary_missing: 보조키워드 일부 누락(자연스러우면 무시 가능): {missing_secondary}"
            )

    metrics: dict[str, Any] = {
        "chars": chars,
        "primary": primary,
        "primary_freq": freq,
        "density_pct": round(density, 2),
        "headings": len(headings),
        "headings_with_keyword": kw_in_h,
        "secondary_present": present_secondary,
        "secondary_missing": missing_secondary,
    }

    return len(issues) == 0, {
        "issues": issues,
        "warnings": warnings,
        "metrics": metrics,
        "gate": "seo",
    }
