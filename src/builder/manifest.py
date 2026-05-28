"""builder.manifest — 증분 빌드 의존 그래프 (JSON 파일).

출처: DB §10 [추정] + ARCH §7-2 [확정].

설계:
- `data/manifest.json` 단일 파일 (테이블 아님 — DB §10-1 근거 4가지)
- 빌드 시 한 번 load → 갱신 → 한 번 save
- Git diff 가능 (사람이 읽을 수 있는 JSON)
- 형태 결정은 [추정] — 사용자 검토 후 KEY_DECISIONS_REVIEW.md §결정 1 응답 시 확정
- 본 모듈: 인터페이스만. CLI `build` 명령 활성화 시 builder.renderer/pages와 결합

함수:
- new_manifest()                : 빈 manifest dict 생성 (schema_version=1)
- load(path)                    : JSON 파일 로드 (없으면 new_manifest)
- save(path, manifest)          : JSON 파일 저장 (Git diff 친화 indent=2)
- upsert_article(manifest, ...) : articles[slug] 추가·갱신
- upsert_asset(manifest, ...)   : assets[path] = hash
- upsert_template(manifest, ...): templates[name] = hash
- needs_rebuild(manifest, slug, current_hash, ...) : 5 재빌드 조건 [추정]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = 1
DEFAULT_MANIFEST_PATH = Path("data") / "manifest.json"


def new_manifest() -> dict[str, Any]:
    """빈 manifest dict 생성 — DB §10-2 [확정] 스키마."""
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "last_full_build": None,
        "articles": {},
        "assets": {},
        "templates": {},
    }


def load(path: str | Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    """JSON 파일 로드. 파일 없으면 new_manifest 반환 (첫 빌드)."""
    p = Path(path)
    if not p.exists():
        return new_manifest()
    raw = p.read_text(encoding="utf-8")
    data: Any = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"manifest 최상위가 객체 아님: {type(data).__name__}")
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            f"manifest schema_version 불일치: {data.get('schema_version')} "
            f"(기대 {MANIFEST_SCHEMA_VERSION})"
        )
    # 필수 키 보강 (옛 manifest 호환)
    for key in ("articles", "assets", "templates"):
        data.setdefault(key, {})
    return data


def save(path: str | Path, manifest: dict[str, Any]) -> None:
    """JSON 파일 저장 — Git diff 친화 (indent=2·정렬·한국어 보존)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    p.write_text(text + "\n", encoding="utf-8")


def upsert_article(
    manifest: dict[str, Any],
    slug: str,
    *,
    article_id: int,
    content_hash: str,
    depends_on: dict[str, list[str]] | None = None,
    last_built: str | None = None,
    output_paths: list[str] | None = None,
) -> None:
    """articles[slug] 추가·갱신 — DB §10-2 [확정] 형식."""
    if not slug:
        raise ValueError("slug 빈 값")
    manifest.setdefault("articles", {})[slug] = {
        "id": article_id,
        "content_hash": content_hash,
        "depends_on": depends_on or {"templates": [], "articles": [], "assets": []},
        "last_built": last_built,
        "output_paths": output_paths or [f"build/articles/{slug}/index.html"],
    }


def upsert_asset(manifest: dict[str, Any], path: str, asset_hash: str) -> None:
    """assets[path] = hash."""
    if not path:
        raise ValueError("path 빈 값")
    manifest.setdefault("assets", {})[path] = asset_hash


def upsert_template(manifest: dict[str, Any], name: str, template_hash: str) -> None:
    """templates[name] = hash."""
    if not name:
        raise ValueError("name 빈 값")
    manifest.setdefault("templates", {})[name] = template_hash


def needs_rebuild(
    manifest: dict[str, Any],
    slug: str,
    *,
    current_content_hash: str,
    current_template_hashes: dict[str, str] | None = None,
    current_asset_hashes: dict[str, str] | None = None,
) -> tuple[bool, list[str]]:
    """ARCH §7-3 [추정] 5가지 재빌드 조건 — 변경 감지.

    반환: (rebuild_required, reasons)
    조건:
    1. slug가 manifest.articles에 없음 (신규)
    2. content_hash 변경
    3. 의존 템플릿 중 하나라도 hash 변경
    4. 의존 article의 content_hash 변경 (related links 등)
    5. 의존 asset의 hash 변경
    """
    articles = manifest.get("articles", {})
    if slug not in articles:
        return True, ["new_article"]

    entry = articles[slug]
    reasons: list[str] = []

    if entry.get("content_hash") != current_content_hash:
        reasons.append("content_hash_changed")

    depends = entry.get("depends_on", {})

    if current_template_hashes:
        manifest_tpl = manifest.get("templates", {})
        for tpl in depends.get("templates", []):
            cur = current_template_hashes.get(tpl)
            old = manifest_tpl.get(tpl)
            if cur is not None and cur != old:
                reasons.append(f"template_changed:{tpl}")

    if current_asset_hashes:
        manifest_assets = manifest.get("assets", {})
        for asset in depends.get("assets", []):
            cur = current_asset_hashes.get(asset)
            old = manifest_assets.get(asset)
            if cur is not None and cur != old:
                reasons.append(f"asset_changed:{asset}")

    # 의존 article 변경 (related links 등) — 호출자가 직접 비교 (manifest 안 내에서)
    manifest_articles = manifest.get("articles", {})
    for dep_slug in depends.get("articles", []):
        dep_entry = manifest_articles.get(dep_slug)
        if dep_entry is None:
            reasons.append(f"dep_article_missing:{dep_slug}")
        # 의존 article의 hash 변화는 호출자가 결정 시점에 따로 비교

    return (len(reasons) > 0), reasons
