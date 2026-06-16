"""category_autopilot — 신규 카테고리 자동 프로비저닝 오케스트레이션 (세션 #35, ③).

흐름: ②설정생성(generate_config) → 카테고리 행 생성(draft) → 수집(vision 게이트 강제) →
페이지 빌드(draft). ①발굴(category_config_gen.suggest_categories)이 후보를 주면 그 label로 호출.

안전(§0·§2-마): status='draft'로만 만들고 **자동 공개하지 않는다**. 사람이 대시보드에서 검토·
승인 후 배포(인간 편집 게이트 유지). 비전 게이트를 강제(vision=True)해 사람 단어튜닝 없이도 오염
상품을 거른다. dry_run·client 주입으로 비용 0 검증·테스트 가능. **라이브 첫 실행은 사람 감독 권장**
(외부 LLM·알리 호출·DB 쓰기).
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from collector import category_config_gen as cg
from collector.category_collect import collect_category


def _slugify_en(text: str) -> str:
    """영어 검색어 → URL 슬러그 (소문자·영숫자·하이픈). 비면 'category'."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "category"


def _ensure_category_row(conn: sqlite3.Connection, slug: str, label_ko: str) -> bool:
    """categories에 행 없으면 draft로 생성. 반환: 새로 만들었으면 True (자동 공개 안 함·§2-마)."""
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    if row:
        return False
    conn.execute(
        "INSERT INTO categories (slug, name_ko, status) VALUES (?, ?, 'draft')",
        (slug, label_ko),
    )
    conn.commit()
    return True


def provision_category(
    conn: sqlite3.Connection,
    label_ko: str,
    *,
    client: Any = None,
    dry_run: bool = True,
    build: bool = True,
) -> dict[str, Any]:
    """한글 카테고리명 → 설정생성 → 행(draft) → 수집(vision) → 빌드(draft). 반환: 요약 dict.

    dry_run=True(기본): LLM·수집·빌드 호출 없음(안전). 라이브는 dry_run=False(외부 비용·DB 쓰기).
    build=False면 수집까지만(페이지 빌드 생략). status는 항상 'draft' — 자동 공개 금지(§2-마).
    """
    if client is None and not dry_run:
        import os

        from common import settings
        from enricher.claude_client import ClaudeClient

        client = ClaudeClient(
            api_key=os.environ.get("ANTHROPIC_API_KEY") or None, model=settings.get("llm_model")
        )

    config = cg.generate_config(label_ko, client=client, dry_run=dry_run)
    if not config:
        return {"ok": False, "label": label_ko, "reason": "설정 생성 실패 또는 dry_run"}

    slug = _slugify_en(config["tiers"]["budget"]["q"])
    spec = cg.to_spec(slug, config)
    created = _ensure_category_row(conn, slug, label_ko)

    # 수집 — 비전 게이트 강제(vision=True). 자동 카테고리는 사람 단어튜닝이 없으므로 비전이 품질 보증.
    cres = collect_category(conn, slug, spec=spec, vision=True, dry_run=dry_run)

    build_result: dict[str, Any] | None = None
    if build and not dry_run and cres.relevant > 0:
        from enricher.category_page_builder import build_and_save

        build_result = build_and_save(conn, slug, client, dry_run=False)

    return {
        "ok": True,
        "label": label_ko,
        "slug": slug,
        "created": created,
        "relevant": cres.relevant,
        "vision_dropped": cres.vision_dropped,
        "linked": cres.linked,
        "build": build_result,
    }
