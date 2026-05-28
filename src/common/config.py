"""혼살림 환경 설정 로더.

출처: BACKEND §11 환경 변수 표준 [확정] + ARCH §6 secrets 격리 [확정].

설계:
- 모든 secrets는 D:\\secrets\\affiliate_hub\\*.env 에서 로드 (저장소 외부)
- python-dotenv로 읽기. 누락 시 fail-fast (BACKEND §11-2)
- secrets 값은 절대 로그에 출력하지 않음 (POLICY §14-bis-1)
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # 의존성 미설치 환경 대비
    load_dotenv = None  # type: ignore[assignment]


SECRETS_DIR = Path(r"D:\secrets\affiliate_hub")

# BACKEND §11-1 환경 변수 표 — Phase 1 운영 시점 필수 키
REQUIRED_KEYS_PHASE1: tuple[str, ...] = (
    "CF_API_TOKEN",
    "CF_ACCOUNT_ID",
    "ANTHROPIC_API_KEY",
    "INDEXNOW_KEY",
)

# Phase 2 이후 쿠팡·알리 추가 시 점진 확장
# (현재는 PHASE1과 동일. 쿠팡 활성 시점에 추가 키 unpacking)
REQUIRED_KEYS_PHASE2: tuple[str, ...] = (*REQUIRED_KEYS_PHASE1,)
# 향후 예시:
# REQUIRED_KEYS_PHASE2 = (*REQUIRED_KEYS_PHASE1, "COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_TAG_ID")


def load_secrets(secrets_dir: Path = SECRETS_DIR) -> dict[str, str | None]:
    """secrets 폴더의 모든 .env 파일을 환경에 로드.

    반환: 로드된 파일 경로 → 발견 여부 매핑. 값은 노출하지 않음.
    """
    if load_dotenv is None:
        raise RuntimeError(
            "python-dotenv 미설치. `pip install python-dotenv` 또는 pyproject.toml의 dependencies 설치 필요."
        )

    loaded: dict[str, str | None] = {}
    if not secrets_dir.exists():
        loaded[str(secrets_dir)] = "MISSING_DIR"
        return loaded

    # override=True — BACKEND §11 "secrets/*.env에서 읽음" 원칙
    # 시스템 환경에 빈 값으로 설정된 변수가 있어도 .env 값이 우선.
    for env_path in sorted(secrets_dir.glob("*.env")):
        ok = load_dotenv(env_path, override=True)
        loaded[env_path.name] = "loaded" if ok else "empty_or_missing"

    return loaded


def check_required(keys: Iterable[str] = REQUIRED_KEYS_PHASE1) -> dict[str, bool]:
    """필수 환경 변수의 존재 여부만 반환. 값은 노출하지 않음."""
    return {key: bool(os.environ.get(key)) for key in keys}


def assert_required(keys: Iterable[str] = REQUIRED_KEYS_PHASE1) -> None:
    """누락 시 SystemExit(2). BACKEND §9-2 exit code 표준."""
    missing = [k for k, present in check_required(keys).items() if not present]
    if missing:
        sys.stderr.write("[config] FATAL 필수 환경 변수 누락: " + ", ".join(missing) + "\n")
        sys.stderr.write(
            "[config] secrets 폴더의 .env 파일을 확인하세요: " + str(SECRETS_DIR) + "\n"
        )
        raise SystemExit(2)
