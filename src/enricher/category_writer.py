"""category_writer — 카테고리 페이지 구매가이드 본문 생성 (세션 #15).

카테고리(예 "컴퓨터 책상")의 전문 8요소 가이드 산문을 운영자 "혼살다" 명의로 Sonnet 생성.
seo_keywords.gate_config({primary, secondary})를 받아 2층 키워드 배치 지시를 프롬프트에 주입하고,
enricher.seo_regenerate.regenerate_until_seo_pass로 SEO 게이트 통과까지 재생성(비용 상한 내).

상품 비교 카드·한눈비교표 등 12컴포넌트는 렌더러가 별도 결합 — 본 모듈은 **산문(8요소)** 담당.
출력은 "# 제목"으로 시작하는 마크다운(게이트의 _split_title_body가 제목/산문 분리).
"""

from __future__ import annotations

import json
import re
from typing import Any

from . import prompt_loader
from .seo_directive import build_seo_directive

# 정직한 큐레이터 페르소나 — AI 표기·1인칭 경험 금지(게이트와 정합).
CATEGORY_SYSTEM = (
    "당신은 1인 가구·홈오피스 살림 정보를 정직하게 큐레이션하는 한국어 에디터입니다. "
    "운영자 '혼살다' 명의로, 과장 없이 정확하고 실용적인 구매 가이드를 씁니다. "
    "직접 사용 경험을 지어내지 않고(1인칭 사용기 금지), 가짜 평점·후기·수치를 만들지 않습니다."
)


def build_category_prompt(
    category_name: str, seo: dict[str, Any], feedback: list[str] | None = None
) -> str:
    """카테고리 가이드 user 프롬프트 조립 (seo 2층 배치 지시 주입 + 재생성 피드백)."""
    directive = build_seo_directive(seo.get("primary"), seo.get("secondary"))
    prompt = prompt_loader.render(
        "category_guide",
        category_name=category_name,
        primary=seo.get("primary", ""),
        seo_directive=directive,
    )
    if feedback:
        prompt += "\n\n[지난 생성의 SEO 미달 — 반드시 보완]\n- " + "\n- ".join(feedback)
    return prompt


def generate_category_guide(
    client: Any,
    category_name: str,
    seo: dict[str, Any],
    *,
    feedback: list[str] | None = None,
    dry_run: bool = True,
) -> Any:
    """카테고리 가이드 1회 생성. client = ClaudeClient. 반환 = GenerateResult.

    응답 본문(response_text)이 "# 제목 + 마크다운". 호출 측이 regenerate 루프로 감쌀 수 있다.
    """
    user_prompt = build_category_prompt(category_name, seo, feedback)
    return client.generate_raw(CATEGORY_SYSTEM, user_prompt, dry_run=dry_run)


# ── 카테고리 페이지 통합 콘텐츠 (가이드 8요소 + FAQ + 추천 6선) — 세션 #17 ──


class CategoryPageError(ValueError):
    """카테고리 페이지 JSON 응답 파싱·검증 실패."""


def build_category_page_prompt(
    category_name: str,
    products: list[dict[str, Any]],
    seo: dict[str, Any] | None = None,
    feedback: list[str] | None = None,
) -> str:
    """category_page 프롬프트 조립 — 제품 목록(6선 후보) + SEO 지시(선택) 주입."""
    seo = seo or {}
    directive = (
        build_seo_directive(seo.get("primary"), seo.get("secondary")) if seo.get("primary") else ""
    )
    prompt = prompt_loader.render(
        "category_page",
        category_name=category_name,
        products=products,
        seo_directive=directive,
    )
    if feedback:
        prompt += "\n\n[지난 생성 보완 필요]\n- " + "\n- ".join(feedback)
    return prompt


def generate_category_page(
    client: Any,
    category_name: str,
    products: list[dict[str, Any]],
    *,
    seo: dict[str, Any] | None = None,
    feedback: list[str] | None = None,
    dry_run: bool = True,
) -> Any:
    """카테고리 페이지 콘텐츠 1회 생성. 반환 = GenerateResult(response_text=JSON 문자열).

    feedback: 직전 SEO 게이트 미달 issues — 재생성 시 프롬프트에 보완 지시로 주입.
    """
    user_prompt = build_category_page_prompt(category_name, products, seo, feedback)
    return client.generate_raw(CATEGORY_SYSTEM, user_prompt, dry_run=dry_run)


def parse_category_page_response(
    response_text: str, valid_slugs: set[str] | None = None
) -> dict[str, Any]:
    """JSON 응답 → {title, guide_md, faq, picks}. 환각 slug·형식 오류를 방어적으로 정제.

    valid_slugs 지정 시 picks에서 제공 목록에 없는 slug(환각)는 제거 — §0 진실성.
    """
    text = response_text.strip()
    if text.startswith("```"):  # 코드펜스 제거
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise CategoryPageError("응답에서 JSON 객체를 찾을 수 없음")
    try:
        # strict=False — guide_md(마크다운)의 raw 개행 등 제어문자 허용 (모델 응답 방어)
        data = json.loads(text[start : end + 1], strict=False)
    except json.JSONDecodeError as ex:
        raise CategoryPageError(f"JSON 파싱 실패: {ex}") from ex

    title = str(data.get("title", "")).strip()
    lead = str(data.get("lead", "")).strip()
    if not title or not lead:
        raise CategoryPageError("title 또는 lead 누락")

    def _strs(seq: Any, limit: int) -> list[str]:
        return [str(x).strip() for x in (seq or []) if str(x).strip()][:limit]

    type_table = [
        {
            "type": str(t.get("type", "")).strip(),
            "trait": str(t.get("trait", "")).strip(),
            "for": str(t.get("for", "")).strip(),
        }
        for t in (data.get("type_table") or [])
        if isinstance(t, dict) and str(t.get("type", "")).strip()
    ][:6]

    checkpoints = [
        {"title": str(c.get("title", "")).strip(), "why": str(c.get("why", "")).strip()}
        for c in (data.get("checkpoints") or [])
        if isinstance(c, dict) and str(c.get("title", "")).strip()
    ][:8]

    picks: list[dict[str, Any]] = []
    for p in data.get("picks") or []:
        if not isinstance(p, dict):
            continue
        slug = str(p.get("slug", "")).strip()
        if not slug or (valid_slugs is not None and slug not in valid_slugs):
            continue  # 환각·미제공 slug 제거
        tier = p.get("tier") if p.get("tier") in ("budget", "premium") else "budget"
        picks.append(
            {
                "slug": slug,
                "tier": tier,
                "type": str(p.get("type", "")).strip(),
                "pros": _strs(p.get("pros"), 4),
                "cons": _strs(p.get("cons"), 3),
                "for": str(p.get("for", "")).strip(),
            }
        )
    pick_slugs = {p["slug"] for p in picks}

    compare_raw = data.get("compare") or {}
    rows = _strs(compare_raw.get("rows") if isinstance(compare_raw, dict) else None, 6)
    cells: list[dict[str, Any]] = []
    for cell in (compare_raw.get("cells") or []) if isinstance(compare_raw, dict) else []:
        if not isinstance(cell, dict):
            continue
        slug = str(cell.get("slug", "")).strip()
        if slug not in pick_slugs:  # picks에 없는 제품 비교는 제거
            continue
        vals = [str(v).strip() or "—" for v in (cell.get("values") or [])]
        vals = (vals + ["—"] * len(rows))[: len(rows)]  # rows 길이에 맞춤(부족분 —)
        cells.append({"slug": slug, "values": vals})
    compare = {"rows": rows, "cells": cells}

    faq = [
        {"q": str(f.get("q", "")).strip(), "a": str(f.get("a", "")).strip()}
        for f in (data.get("faq") or [])
        if isinstance(f, dict) and str(f.get("q", "")).strip()
    ]

    return {
        "title": title,
        "image_prompt": str(data.get("image_prompt", "")).strip(),
        "image_alt": str(data.get("image_alt", "")).strip(),
        "lead": lead,
        "guide_intro": str(data.get("guide_intro", "")).strip(),
        "type_table": type_table,
        "checkpoints": checkpoints,
        "mistakes": str(data.get("mistakes", "")).strip(),
        "picks": picks,
        "compare": compare,
        "faq": faq,
    }
