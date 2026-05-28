"""builder.manifest 회귀 — DB §10 [추정] JSON 인터페이스.

manifest 형태 결정은 사용자 검토 후 [확정] 예정. 본 회귀는 현재 인터페이스 보장.
"""

from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from builder import manifest as M


@contextmanager
def _tmpdir() -> Any:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


# ─── new_manifest / load / save ───────────────────────────────────────


class TestNewManifest:
    def test_has_required_keys(self) -> None:
        m = M.new_manifest()
        for key in ("schema_version", "last_full_build", "articles", "assets", "templates"):
            assert key in m

    def test_schema_version_is_1(self) -> None:
        assert M.new_manifest()["schema_version"] == M.MANIFEST_SCHEMA_VERSION == 1

    def test_collections_are_empty_dicts(self) -> None:
        m = M.new_manifest()
        assert m["articles"] == {}
        assert m["assets"] == {}
        assert m["templates"] == {}


class TestLoadSave:
    def test_load_missing_returns_new_manifest(self) -> None:
        with _tmpdir() as tmp:
            out = M.load(tmp / "nonexistent.json")
            assert out["schema_version"] == 1
            assert out["articles"] == {}

    def test_save_then_load_roundtrip(self) -> None:
        with _tmpdir() as tmp:
            m = M.new_manifest()
            m["last_full_build"] = "2026-05-28T11:00:00+09:00"
            M.upsert_article(m, "wonroom-30", article_id=1, content_hash="sha256:abc")
            path = tmp / "manifest.json"
            M.save(path, m)
            loaded = M.load(path)
            assert loaded["last_full_build"] == "2026-05-28T11:00:00+09:00"
            assert "wonroom-30" in loaded["articles"]
            assert loaded["articles"]["wonroom-30"]["content_hash"] == "sha256:abc"

    def test_save_is_human_readable_indent_2(self) -> None:
        with _tmpdir() as tmp:
            m = M.new_manifest()
            path = tmp / "m.json"
            M.save(path, m)
            text = path.read_text(encoding="utf-8")
            assert "  " in text  # indent 2
            assert text.endswith("\n")

    def test_save_sorts_keys_for_stable_diff(self) -> None:
        with _tmpdir() as tmp:
            m = M.new_manifest()
            M.upsert_article(m, "zebra", article_id=1, content_hash="sha256:z")
            M.upsert_article(m, "alpha", article_id=2, content_hash="sha256:a")
            path = tmp / "m.json"
            M.save(path, m)
            text = path.read_text(encoding="utf-8")
            assert text.index('"alpha"') < text.index('"zebra"')

    def test_save_creates_parent_dirs(self) -> None:
        with _tmpdir() as tmp:
            path = tmp / "nested" / "deep" / "m.json"
            M.save(path, M.new_manifest())
            assert path.exists()

    def test_load_non_object_raises(self) -> None:
        with _tmpdir() as tmp:
            path = tmp / "bad.json"
            path.write_text("[1, 2, 3]", encoding="utf-8")
            with raises(ValueError):
                M.load(path)

    def test_load_schema_version_mismatch_raises(self) -> None:
        with _tmpdir() as tmp:
            path = tmp / "old.json"
            path.write_text(
                json.dumps({"schema_version": 999, "articles": {}, "assets": {}, "templates": {}}),
                encoding="utf-8",
            )
            with raises(ValueError):
                M.load(path)


# ─── upsert helpers ───────────────────────────────────────────────────


class TestUpsertArticle:
    def test_creates_article_entry(self) -> None:
        m = M.new_manifest()
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:1")
        assert m["articles"]["x"]["id"] == 1
        assert m["articles"]["x"]["content_hash"] == "sha256:1"
        # default output_paths
        assert m["articles"]["x"]["output_paths"] == ["build/articles/x/index.html"]

    def test_updates_existing_article(self) -> None:
        m = M.new_manifest()
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:1")
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:2")
        assert m["articles"]["x"]["content_hash"] == "sha256:2"

    def test_custom_depends_on(self) -> None:
        m = M.new_manifest()
        deps = {"templates": ["article.html"], "articles": ["related"], "assets": ["main.css"]}
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:1", depends_on=deps)
        assert m["articles"]["x"]["depends_on"] == deps

    def test_empty_slug_raises(self) -> None:
        m = M.new_manifest()
        with raises(ValueError):
            M.upsert_article(m, "", article_id=1, content_hash="sha256:1")


class TestUpsertAssetTemplate:
    def test_upsert_asset(self) -> None:
        m = M.new_manifest()
        M.upsert_asset(m, "css/main.css", "sha256:css1")
        assert m["assets"]["css/main.css"] == "sha256:css1"

    def test_upsert_template(self) -> None:
        m = M.new_manifest()
        M.upsert_template(m, "article.html", "sha256:tpl1")
        assert m["templates"]["article.html"] == "sha256:tpl1"


# ─── needs_rebuild (ARCH §7-3 [추정] 5조건) ───────────────────────────


class TestNeedsRebuild:
    def test_new_article_needs_rebuild(self) -> None:
        m = M.new_manifest()
        ok, reasons = M.needs_rebuild(m, "x", current_content_hash="sha256:1")
        assert ok is True
        assert "new_article" in reasons

    def test_unchanged_no_rebuild(self) -> None:
        m = M.new_manifest()
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:1")
        ok, reasons = M.needs_rebuild(m, "x", current_content_hash="sha256:1")
        assert ok is False
        assert reasons == []

    def test_content_hash_changed(self) -> None:
        m = M.new_manifest()
        M.upsert_article(m, "x", article_id=1, content_hash="sha256:1")
        ok, reasons = M.needs_rebuild(m, "x", current_content_hash="sha256:2")
        assert ok is True
        assert "content_hash_changed" in reasons

    def test_template_dependency_changed(self) -> None:
        m = M.new_manifest()
        M.upsert_template(m, "article.html", "sha256:tplOLD")
        M.upsert_article(
            m,
            "x",
            article_id=1,
            content_hash="sha256:1",
            depends_on={"templates": ["article.html"], "articles": [], "assets": []},
        )
        ok, reasons = M.needs_rebuild(
            m,
            "x",
            current_content_hash="sha256:1",
            current_template_hashes={"article.html": "sha256:tplNEW"},
        )
        assert ok is True
        assert any("template_changed:article.html" in r for r in reasons)

    def test_asset_dependency_changed(self) -> None:
        m = M.new_manifest()
        M.upsert_asset(m, "css/main.css", "sha256:cssOLD")
        M.upsert_article(
            m,
            "x",
            article_id=1,
            content_hash="sha256:1",
            depends_on={"templates": [], "articles": [], "assets": ["css/main.css"]},
        )
        ok, reasons = M.needs_rebuild(
            m,
            "x",
            current_content_hash="sha256:1",
            current_asset_hashes={"css/main.css": "sha256:cssNEW"},
        )
        assert ok is True
        assert any("asset_changed:css/main.css" in r for r in reasons)

    def test_missing_dep_article(self) -> None:
        m = M.new_manifest()
        M.upsert_article(
            m,
            "x",
            article_id=1,
            content_hash="sha256:1",
            depends_on={"templates": [], "articles": ["missing"], "assets": []},
        )
        ok, reasons = M.needs_rebuild(m, "x", current_content_hash="sha256:1")
        assert ok is True
        assert any("dep_article_missing:missing" in r for r in reasons)


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
