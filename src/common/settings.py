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
    # 자동 승인 안전장치(세션 #33): 발행 이력이 이 수 미만이면 자동 승인 보류(초기 사람 검수 단계).
    # 사람이 N편 직접 승인·발행해 품질을 확인한 뒤 자동 승인으로 전환(autonomous-safe-system).
    "auto_approve_min_published": 5,
    # ── 추천/품질 ──
    "featured_per_tier": 4,  # 티어별 추천 수 (실속+고급 = 총 8·#38 글/카테고리 통일). builder·renderer 공용
    "satisfaction_floor": 80.0,  # 알리 긍정 피드백율 하한 % (006 신호 필터)
    "seo_max_attempts": 2,  # SEO 게이트 재생성 상한 (카테고리 페이지 — 비용 방지 CLAUDE §6)
    "enrich_max_attempts": 2,  # 키워드 글 5게이트 재생성 상한 (세션 #33 무인 자가복원 — 비용 방지)
    # 비전 관련성 게이트(세션 #35): 수집 상품 이미지를 Haiku가 보고 카테고리 적합성 판정 → 오염 드롭.
    # 기본 OFF(기존 카테고리 무영향·키워드 필터만). 자동 카테고리 생성 시 ON으로 사람 단어튜닝 대체.
    "vision_gate": False,
    "vision_gate_cap": 40,  # 카테고리당 비전 호출 상한 (비용 보호)
    # ── 채널 ──
    "default_channel": "ali",  # 신규 키워드 기본 채널: ali | coupang | both
    "default_keyword_persona": None,  # 키워드 파생 시나리오 기본 페르소나 slug (None=첫 페르소나)
    "coupang_mode": "manual",  # manual(수동 입력·공식 위젯) | api (15만원 후 자동 수집)
    "coupang_threshold_krw": 150000,  # 쿠팡 API 발급 기준 누적 수익 (모드 전환 안내)
    "coupang_tag": "coupang-partners",  # 쿠팡 파트너스 affiliate_tag (수동 상품 적재용)
    # ── 외부 API 비용(세션 #36) ──
    # Google(Imagen) 월 지출 상한($). 주인이 ai.studio/spend에 설정한 값을 여기 입력하면 대시보드가
    # '추정 사용액 / 상한(%)'을 보여 결제 시점을 미리 알린다. 0=미설정(사용액만 표시).
    "google_spend_cap_usd": 0.0,
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


def get_int(key: str, path: Path = CONFIG_PATH) -> int:
    """정수 설정값 — **0도 보존**(falsy `... or N` 함정 방지·#38).

    `int(get(key) or N)`은 설정값이 0일 때 0을 falsy로 보고 N으로 덮어쓰는 버그가 있었다
    (auto_approve_min_published=0=완전무인이 5로 강제돼 자동발행이 막힘). 이 헬퍼는 값이
    None/누락일 때만 DEFAULTS로 폴백하고, 0은 그대로 0으로 돌려준다.
    """
    v = load(path).get(key, DEFAULTS.get(key))
    if v is None:
        v = DEFAULTS.get(key, 0)
    return int(v)


def get_float(key: str, path: Path = CONFIG_PATH) -> float:
    """실수 설정값 — **0.0도 보존**(falsy `... or N` 함정 방지·#38). None/누락이면 DEFAULTS."""
    v = load(path).get(key, DEFAULTS.get(key))
    if v is None:
        v = DEFAULTS.get(key, 0.0)
    return float(v)


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
