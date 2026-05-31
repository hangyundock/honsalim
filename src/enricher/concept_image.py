"""concept_image — 카테고리 개념 이미지 생성 (Google Imagen 4 Fast, REST). 세션 #17.

AutoBlog tistory_revival/ai_image_gen.py 패턴 이식 — google SDK 없이 requests로 호출.
글만 길게 나열된 페이지는 지루해 이탈률이 높다 → "고르는 법" 섹션에 텍스트·브랜드 없는
개념 컨셉 사진 1장을 넣어 가독성·체류시간을 높인다(카테고리당 1장, 비용 ~$0.02 Fast).

- 텍스트 금지 프롬프트(워터마크·글자 없는 깨끗한 이미지) + Pillow webp 변환·리사이즈(로딩 최적화).
- GOOGLE_API_KEY는 config.load_secrets()로 GOOGLE.env에서 로드(코드가 환경변수로 사용).
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path

import requests

MODEL_FAST = "imagen-4.0-fast-generate-001"  # 가성비 $0.02/장 (AutoBlog 기본)
_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
ENV_KEY = "GOOGLE_API_KEY"
# 텍스트·로고·UI 금지 — 글자가 박힌 이미지는 신뢰도·재사용성 저하(AutoBlog 교훈)
_NO_TEXT = (
    "absolutely no text, no letters, no numbers, no labels, no watermark, no UI elements, no logos"
)
WEBP_MAX_WIDTH = 1280  # 리사이즈 최대 폭(로딩 최적화)


def build_concept_prompt(description_en: str) -> str:
    """개념 이미지 영어 프롬프트 — 깨끗한 1인 가구 홈오피스 컨셉 사진, 텍스트·브랜드 없음."""
    base = (description_en or "").strip()
    return (
        f"photorealistic high-quality photograph, {base}, "
        f"bright clean minimal Korean home office setting, unbranded plain objects, "
        f"soft natural light, shallow depth of field, {_NO_TEXT}"
    )


def _save_webp(raw: bytes, out_path: Path) -> None:
    """이미지 바이트 → 리사이즈 + webp 저장(로딩 최적화). Pillow 실패 시 원본 그대로 저장."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        if img.width > WEBP_MAX_WIDTH:
            new_h = round(img.height * WEBP_MAX_WIDTH / img.width)
            img = img.resize((WEBP_MAX_WIDTH, new_h), Image.Resampling.LANCZOS)
        img.save(out_path, "WEBP", quality=82, method=6)
    except Exception:
        out_path.write_bytes(raw)  # 폴백 — 변환 실패해도 원본 보존


def generate_concept_image(
    description_en: str,
    out_path: Path,
    *,
    aspect: str = "16:9",
    model: str = MODEL_FAST,
    api_key: str | None = None,
    timeout: int = 90,
) -> bool:
    """개념 이미지 1장 생성 → webp 저장. 성공 시 True, 빈 응답 False.

    api_key 미지정 시 os.environ[GOOGLE_API_KEY] 사용(config.load_secrets 선행 필요).
    HTTP 오류·키 누락은 예외 — 호출 측이 잡아 이미지 없이 진행(글은 이미 저장됨).
    """
    key = api_key if api_key is not None else os.environ.get(ENV_KEY, "")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY 미설정 — GOOGLE.env 확인 (config.load_secrets 선행)")
    body = {
        "instances": [{"prompt": build_concept_prompt(description_en)}],
        "parameters": {"sampleCount": 1, "aspectRatio": aspect},
    }
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    resp = requests.post(_URL.format(model=model), headers=headers, json=body, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Imagen HTTP {resp.status_code}: {resp.text[:300]}")
    preds = resp.json().get("predictions") or []
    if not preds:
        return False
    b64 = preds[0].get("bytesBase64Encoded")
    if not b64:
        return False
    _save_webp(base64.b64decode(b64), out_path)
    return True
