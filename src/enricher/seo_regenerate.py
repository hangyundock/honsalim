"""seo_regenerate — SEO 게이트 통과까지 본문 재생성 루프 (AutoBlog 패턴). 세션 #15.

콘텐츠 생성기가 만든 (title, body_md)를 validator/seo.py 게이트로 측정하고, 미달이면
**게이트 issues를 피드백으로 다시 생성**시켜 통과를 유도한다. 무인 자동 운영에서 SEO 품질을
사람 개입 없이 끌어올리는 자가 보정 루프(§0).

게이트가 측정 자(尺)이고 본 루프가 그 자에 맞춰 다시 만든다 — 둘 다 세션 #15에서 구축.
실제 생성 함수(generate)는 카테고리 콘텐츠 생성기가 주입한다(여기서는 콜백만 받음).

★ 비용 과다청구 방지 (tistory 세션 #7·#10 교훈 — 실제 결제 사고):
- **재시도 상한 + 무한루프 금지**: 상한 도달 시 마지막 결과를 그대로 반환(계속 재생성 X).
- **보수적 기본 상한** DEFAULT_MAX_ATTEMPTS=2 (= 최대 2회 생성. tistory 운영도 max_retries=1).
- **게이트 과민 완화**(validator/seo.py): 하드 fail은 대표키워드(#1)만 → 오탐 재생성 비용 차단.
- 호출 측 계약(권장): ① generate 호출 **전** 사전점검(API 키·후보·세션)으로 0비용 중단,
  ② 통과 못 하면 다운스트림 유료 단계(이미지 등) **생략**하고 사람 검토로 — 돈 더 쓰지 말 것.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from validator.seo import check_seo

# generate(feedback) → (title, body_md). 첫 호출 feedback=None, 재시도 시 직전 issues 리스트.
GenerateFn = Callable[[list[str] | None], "tuple[str, str]"]

# 보수적 기본값 = 최대 2회 생성 (tistory 운영 max_retries=1 정신). 비용 상한.
DEFAULT_MAX_ATTEMPTS = 2


def regenerate_until_seo_pass(
    generate: GenerateFn,
    seo_config: dict[str, Any],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> dict[str, Any]:
    """SEO 게이트 통과까지 generate를 재호출.

    generate: feedback(직전 시도 issues 또는 None) → (title, body_md).
    seo_config: {primary, secondary, ...} — validator/seo.py payload["seo"] 형태.

    반환: {
        "title", "body_md",   # 최종(통과본 또는 마지막 시도)
        "passed": bool,       # 게이트 통과 여부
        "attempts": int,      # 실제 생성 횟수
        "report": dict,       # 마지막 seo 게이트 리포트(issues·warnings·metrics)
        "history": [issues, ...],  # 시도별 issues 누적(진단·로깅용)
    }
    """
    feedback: list[str] | None = None
    history: list[list[str]] = []
    title, body_md = "", ""
    report: dict[str, Any] = {}

    attempts = max(1, max_attempts)
    for attempt in range(1, attempts + 1):
        title, body_md = generate(feedback)
        ok, report = check_seo({"body_md": body_md, "title": title, "seo": seo_config})
        issues = list(report.get("issues", []))
        history.append(issues)
        if ok:
            return {
                "title": title,
                "body_md": body_md,
                "passed": True,
                "attempts": attempt,
                "report": report,
                "history": history,
            }
        feedback = issues  # 다음 시도에 게이트 미달 사유 전달

    return {
        "title": title,
        "body_md": body_md,
        "passed": False,
        "attempts": attempts,
        "report": report,
        "history": history,
    }
