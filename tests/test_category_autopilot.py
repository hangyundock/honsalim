"""collector.category_autopilot 회귀 (세션 #35, ③) — 신규 카테고리 자동 프로비저닝 흐름.

라이브 LLM·알리·빌드 호출 없이 generate_config·collect_category·build_and_save를 모킹. 흐름
순서·비전 강제(vision=True)·생성 spec 주입·draft 행 생성·빌드 스킵 조건을 검증한다.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from collector import category_autopilot as ap
from collector.category_collect import CategoryCollectResult
from common import db as _db

_CONFIG: dict[str, Any] = {
    "core": "가습기",
    "exclude": [],
    "tiers": {
        "budget": {"q": "humidifier", "min": 5000, "max": 30000},
        "premium": {"q": "ultrasonic humidifier", "min": 30000, "max": 120000},
    },
}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    conn.commit()
    return conn


class TestSlugify:
    def test_basic(self) -> None:
        assert ap._slugify_en("ultrasonic humidifier") == "ultrasonic-humidifier"
        assert ap._slugify_en("Office Chair!!") == "office-chair"
        assert ap._slugify_en("") == "category"


class TestProvision:
    def test_dry_run_returns_not_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ap.cg, "generate_config", lambda label, **k: {})
        res = ap.provision_category(_conn(), "가습기", dry_run=True)
        assert res["ok"] is False

    def test_full_flow_mocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ap.cg, "generate_config", lambda label, **k: _CONFIG)
        captured: dict[str, Any] = {}

        def fake_collect(
            conn: Any,
            slug: str,
            *,
            spec: Any = None,
            vision: Any = None,
            dry_run: bool = True,
            **k: Any,
        ) -> CategoryCollectResult:
            captured["slug"] = slug
            captured["vision"] = vision
            captured["spec"] = spec
            return CategoryCollectResult(
                slug=slug, dry_run=dry_run, relevant=12, vision_dropped=3, linked=12
            )

        monkeypatch.setattr(ap, "collect_category", fake_collect)
        import enricher.category_page_builder as cpb

        monkeypatch.setattr(cpb, "build_and_save", lambda conn, slug, client, **k: {"saved": True})

        conn = _conn()
        res = ap.provision_category(conn, "가습기", client=object(), dry_run=False)
        assert res["ok"] is True and res["slug"] == "humidifier"
        assert res["created"] is True
        assert res["relevant"] == 12 and res["vision_dropped"] == 3 and res["linked"] == 12
        assert res["build"] == {"saved": True}
        # 비전 강제 + 생성 spec 주입
        assert captured["vision"] is True
        assert captured["spec"].slug == "humidifier"
        assert captured["spec"].require_any == ("가습기",)
        # 카테고리 행이 draft로 생성됨(자동 공개 안 함·§2-마)
        row = conn.execute(
            "SELECT name_ko, status FROM categories WHERE slug = 'humidifier'"
        ).fetchone()
        assert tuple(row) == ("가습기", "draft")

    def test_build_false_skips_build(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ap.cg, "generate_config", lambda label, **k: _CONFIG)
        monkeypatch.setattr(
            ap,
            "collect_category",
            lambda conn, slug, **k: CategoryCollectResult(slug=slug, dry_run=False, relevant=5),
        )
        import enricher.category_page_builder as cpb

        def boom(*a: Any, **k: Any) -> dict[str, Any]:
            raise AssertionError("build=False면 build_and_save 호출 안 됨")

        monkeypatch.setattr(cpb, "build_and_save", boom)
        res = ap.provision_category(_conn(), "가습기", client=object(), dry_run=False, build=False)
        assert res["build"] is None

    def test_zero_relevant_skips_build(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ap.cg, "generate_config", lambda label, **k: _CONFIG)
        monkeypatch.setattr(
            ap,
            "collect_category",
            lambda conn, slug, **k: CategoryCollectResult(slug=slug, dry_run=False, relevant=0),
        )
        import enricher.category_page_builder as cpb

        def boom(*a: Any, **k: Any) -> dict[str, Any]:
            raise AssertionError("수집 0건이면 빌드 안 함")

        monkeypatch.setattr(cpb, "build_and_save", boom)
        res = ap.provision_category(_conn(), "가습기", client=object(), dry_run=False)
        assert res["build"] is None and res["relevant"] == 0
