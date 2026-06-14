"""혼살림 운영 설정 로더 — data/config.json (세션 #25).

운영 대시보드 "설정창"에서 조정하는 값(발행 편수·예약 시각·추천 개수·쿠팡 모드 등)을
코드 하드코딩 대신 config.json에 보관한다. 파일이 없거나 깨져도 기본값으로 안전 동작(§0 견고성).
값은 DEFAULTS에 파일 값을 병합 — 부분 설정만 둬도 나머지는 기본값으로 채워진다.

위치: data/config.json (gitignore 대상 — 머신별 운영 상태. DB와 동일하게 저장소 외부).
secrets(API 키)는 여기 두지 않는다 — secrets는 D:\\secrets\\affiliate_hub\\*.env (common.config).
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "config.json"

# 운영자 조정 가능한 기본값 — 설정창(Phase F)이 이 키들을 편집한다.
# 각 값은 기존 하드코딩 상수와 정합(전환 시 기본 동작 불변).
DEFAULTS: dict[str, Any] = {
    # ── 발행 스케줄 ──
    "publish_per_day": 1,  # 하루 자동 발행 편수 (승인된 큐에서)
    "schedule_time": "11:00",  # 예약 발행 시각 KST (DECISIONS C7 — AutoBlog와 30분+ 간격)
    "schedule_jitter_min": 10,  # 발행 지터(분) — 자연스러운 패턴
    # ★B-i 완전 무인 자동 사이클(생성→자동승인→발행→사후모니터). 기본 OFF = 사람 게이트(E7) 유지.
    # 켜면 auto-cycle이 동작 — 자동 승인은 fail-closed(적합성 검증 가능+featured 적합만, 세션 #29).
    "auto_mode": False,
    # ── 추천/품질 ──
    "featured_per_tier": 3,  # 티어별 추천 수 (실속+고급 = 총 6). category_page_builder 정합
    "satisfaction_floor": 80.0,  # 알리 긍정 피드백율 하한 % (006 신호 필터)
    "seo_max_attempts": 2,  # SEO 게이트 재생성 상한 (비용 과다청구 방지 — CLAUDE §6)
    # ── 채널 ──
    "default_channel": "ali",  # 신규 키워드 기본 채널: ali | coupang | both
    "default_keyword_persona": None,  # 키워드 파생 시나리오 기본 페르소나 slug (None=첫 페르소나)
    "coupang_mode": "manual",  # manual(수동 입력·공식 위젯) | api (15만원 후 자동 수집)
    "coupang_threshold_krw": 150000,  # 쿠팡 API 발급 기준 누적 수익 (모드 전환 안내)
    "coupang_tag": "coupang-partners",  # 쿠팡 파트너스 affiliate_tag (수동 상품 적재용)
    # ── LLM ──
    "llm_model": "deepseek/deepseek-v4-pro",  # 본문 생성 모델 (세션 #19)
    # ── 배포 검증 ──
    "verify_url": "https://honsallim.com/",  # 발행 후 HTTP 검증 URL
}


def load(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """config.json을 기본값에 병합해 반환. 없거나 깨지면 기본값만(§0 견고성 — 무인 안전 정지 방지)."""
    values = deepcopy(DEFAULTS)
    p = Path(path)
    if not p.exists():
        return values
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return values
    if isinstance(raw, dict):
        for k, v in raw.items():
            values[str(k)] = v
    return values


def get(key: str, default: Any = None, path: Path = CONFIG_PATH) -> Any:
    """단일 설정값 조회 (편의). 파일에 없으면 DEFAULTS, 그것도 없으면 default."""
    return load(path).get(key, DEFAULTS.get(key, default))


def save(values: dict[str, Any], path: Path = CONFIG_PATH) -> Path:
    """설정 저장 — 기본값에 병합 후 기록(부분 저장도 안전). 반환: 저장 경로.

    알 수 없는 키도 보존한다(상위 호환). UTF-8·들여쓰기 2.
    """
    merged = deepcopy(DEFAULTS)
    for k, v in values.items():
        merged[str(k)] = v
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def ensure_config_file(path: Path = CONFIG_PATH) -> Path:
    """config.json이 없으면 기본값으로 생성. 있으면 그대로. 반환: 경로."""
    p = Path(path)
    if not p.exists():
        return save({}, p)
    return p
