"""혼살림 정보 등급 표기 유틸.

출처: POLICY §3·VALIDATOR_PATTERNS §4 [확정] + CLAUDE.md §2-나 [확정].

4등급 (CLAUDE.md §2-나):
- [확정]    : 1차 출처·공식 문서·법령·코드 동작 검증으로 100% 확실
- [관찰]    : 작성 시점 직접 확인 (스크린샷·출력·문서 인용) — 변동 가능
- [추정]    : 추론·일반 패턴 기반 — 검증 필요
- [확인 불가] : 모르거나 출처 없음 — 명시적 표기

본 유틸은 모든 모듈에서 import하여 일관 표기.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Grade(enum.Enum):
    """정보 신뢰도 4등급."""

    CONFIRMED = "[확정]"
    OBSERVED = "[관찰]"
    INFERRED = "[추정]"
    UNVERIFIED = "[확인 불가]"

    @property
    def korean(self) -> str:
        """대괄호 포함 한국어 표기 — 본문·로그에 그대로 삽입."""
        return self.value

    @property
    def code(self) -> str:
        """ASCII 코드 표기 (DB·JSON 등) — 외부 영문 매핑."""
        return self.name


@dataclass(frozen=True)
class GradedFact:
    """등급이 부여된 사실 1건.

    예:
        GradedFact("도메인 honsalim.com 만료 2027-05-28", Grade.CONFIRMED, "Cloudflare 결제 영수증")
    """

    text: str
    grade: Grade
    source: str | None = None

    def format(self) -> str:
        """한국어 표기 — {grade} {text} (출처: {source}) 형식."""
        if self.source:
            return f"{self.grade.korean} {self.text} (출처: {self.source})"
        return f"{self.grade.korean} {self.text}"

    def __str__(self) -> str:  # 편의
        return self.format()


def confirmed(text: str, source: str | None = None) -> GradedFact:
    """[확정] 등급 short helper."""
    return GradedFact(text, Grade.CONFIRMED, source)


def observed(text: str, source: str | None = None) -> GradedFact:
    """[관찰] 등급 short helper."""
    return GradedFact(text, Grade.OBSERVED, source)


def inferred(text: str, source: str | None = None) -> GradedFact:
    """[추정] 등급 short helper."""
    return GradedFact(text, Grade.INFERRED, source)


def unverified(text: str, source: str | None = None) -> GradedFact:
    """[확인 불가] 등급 short helper."""
    return GradedFact(text, Grade.UNVERIFIED, source)
