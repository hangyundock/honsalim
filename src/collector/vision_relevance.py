"""vision_relevance — 수집 상품 이미지를 Claude Haiku 비전으로 카테고리 관련성 판정 (세션 #35).

배경(근본 수정): 기존 product_filter는 순수 키워드/부분문자열 매칭이라 의미를 모른다. 그래서
카테고리마다 사람이 제외어 리스트를 손봐야 하고, 빠뜨린 단어가 있으면 쓰레기가 샌다(폰케이스가
의자에). 이 모듈은 상품 이미지를 Haiku가 직접 보고 "이게 정말 {카테고리}인가"를 의미로 판별해
그 한계를 보완한다 — 카테고리당 사람 단어튜닝 없이도 품질을 보증.

패턴 출처: D:\\autoblog\\tistory_revival\\image_qa.py (주인이 운영 중인 검증된 Haiku 사진 점검
게이트). honsalim용으로 ① 원격 URL 이미지(알리/쿠팡 hotlink) ② 상품 관련성 프롬프트 ③ 자동
발행 안전(fail_closed)으로 이식.

§0 자동 발행 안전: fail_closed=True 기본 — 오류·불확실·키 없음·이미지 없음은 드롭(False)으로
처리해 깜깜이 발행을 막는다. LLM/네트워크 장애가 오염 상품 통과로 이어지지 않음. 비용은 호출
측 cap으로 상한. 수동 쿠팡(사람이 고른 것)은 대상 아님 — 자동 수집 알리 상품에만 적용.
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # 저렴한 비전 모델 (tistory와 동일)
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 honsalim-vision-gate"

_PROMPT = (
    '이 이미지가 "{category}" 카테고리의 상품 사진인지 판정하라.\n'
    '참고 상품명(기계번역이라 부정확할 수 있음): "{name}"\n\n'
    '체크: (1) 사진 속 주된 사물이 실제로 "{category}"에 해당하는가 '
    "(2) 전혀 다른 품목(예: 폰케이스·티셔츠·차량용품·부속 액세서리)이 아닌가\n\n"
    '반드시 JSON만 출력: {{"ok": true 또는 false, "reason": "한국어로 간단히"}}'
)


def _resolve_key(api_key: str | None) -> str | None:
    """ANTHROPIC_API_KEY — 인자 우선, 없으면 환경, 그래도 없으면 secrets 로드 후 재조회."""
    if api_key:
        return api_key
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    try:
        from common import config

        config.load_secrets()
    except Exception:  # noqa: S110 — 키 조회 실패는 상위에서 fail_closed로 처리
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def _media_type(raw: bytes) -> str:
    """매직 바이트로 이미지 MIME 추정 (Claude vision 지원 형식). 미상은 jpeg(알리 기본 추정)."""
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _fetch_image(url: str, timeout: float = 15.0) -> tuple[bytes, str]:
    """원격 이미지 URL → (bytes, media_type). 브라우저 UA로 CDN hotlink 차단 회피."""
    import requests

    r = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout)
    r.raise_for_status()
    raw = r.content
    return raw, _media_type(raw)


def _call_vision(api_key: str, model: str, media_type: str, data_b64: str, prompt: str) -> str:
    """Haiku 비전 호출 → 원시 텍스트 응답. (테스트는 이 함수를 monkeypatch)."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    # content는 SDK 타입파라미터가 엄격해 Any로 둔다(이미지+텍스트 블록).
    content: Any = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data_b64},
        },
        {"type": "text", "text": prompt},
    ]
    msg = client.messages.create(
        model=model, max_tokens=200, messages=[{"role": "user", "content": content}]
    )
    block = msg.content[0]
    return str(getattr(block, "text", "")).strip()


def check_product_relevance(
    image_url: str,
    category_label: str,
    product_name: str = "",
    *,
    api_key: str | None = None,
    fail_closed: bool = True,
    model: str = DEFAULT_MODEL,
) -> tuple[bool, str]:
    """상품 이미지가 카테고리에 맞는지 Haiku 비전으로 판정. 반환: (ok, reason).

    fail_closed=True(기본): 키 없음·이미지 없음·페치 실패·API/파싱 오류 = False(드롭, 자동 안전).
    fail_closed=False: 같은 오류 시 True(통과) — 비전을 못 돌려도 파이프라인 안 막을 때.
    """
    key = _resolve_key(api_key)
    if not key:
        return (not fail_closed, "ANTHROPIC_API_KEY 없음")
    if not image_url:
        return (not fail_closed, "이미지 URL 없음")
    try:
        raw, media = _fetch_image(image_url)
        data = base64.b64encode(raw).decode()
    except Exception as e:  # 네트워크 등 모든 페치 실패를 fail_closed 정책대로 처리
        return (not fail_closed, f"이미지 페치 실패: {repr(e)[:60]}")
    prompt = _PROMPT.format(category=category_label, name=product_name or "(없음)")
    try:
        text = _call_vision(key, model, media, data, prompt)
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        d = json.loads(m.group(0) if m else text, strict=False)
        return bool(d.get("ok")), str(d.get("reason", ""))
    except Exception as e:  # API/파싱 오류는 fail_closed 정책대로 처리
        return (not fail_closed, f"비전 검수 오류: {repr(e)[:60]}")


def filter_relevant(
    products: list[dict[str, Any]],
    category_label: str,
    *,
    image_key: str = "image_url_external",
    cap: int = 40,
    fail_closed: bool = True,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """상품 목록을 비전 관련성으로 분리. 반환: {kept, dropped, checked, capped}.

    cap: 비전 호출 상한(비용 보호). 초과분은 비전 미검사로 kept에 통과(키워드 필터가 1차로
    걸렀다는 전제). capped 수를 함께 반환해 '조용한 누락' 없이 가시화(§0). dropped 항목엔
    _vision_reason을 덧붙인다.
    """
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    checked = 0
    capped = 0
    for p in products:
        if checked >= cap:
            capped += 1
            kept.append(p)
            continue
        url = str(p.get(image_key) or "")
        if not url:
            # 이미지 없으면 비전 판정 불가 — fail_closed면 드롭, 아니면 통과
            (dropped if fail_closed else kept).append(p)
            continue
        checked += 1
        ok, reason = check_product_relevance(
            url,
            category_label,
            str(p.get("name", "")),
            api_key=api_key,
            fail_closed=fail_closed,
            model=model,
        )
        if ok:
            kept.append(p)
        else:
            d = dict(p)
            d["_vision_reason"] = reason
            dropped.append(d)
    return {"kept": kept, "dropped": dropped, "checked": checked, "capped": capped}
