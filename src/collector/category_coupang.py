"""collector.category_coupang — 카테고리 쿠팡 운영자추천 zone 상품 관리 (세션 #32).

쿠팡 운영자추천 zone(renderer.CATEGORY_COUPANG_SQL: category_products⋈products WHERE
source='coupang')에 상품을 직접 추가/제거한다. 흐름: 쿠팡 공식 배너 파싱(coupang_manual)
→ products 업서트 → category_products 링크. 저작권 안전(함정#3): 공식 배너 이미지 hotlink만.

기존엔 쿠팡이 키워드(target_products)·글 경유로만 카테고리에 흡수됐다. 본 모듈로 운영자가
카테고리 단위로 쿠팡 추천을 직접 큐레이션한다(배열 균형·여러 개). build --full 시 go-링크·
카테고리 페이지가 DB와 일치하게 재생성된다(slug_map이 카테고리 연결 쿠팡 상품을 포함).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from . import coupang_manual, products_store


def category_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return int(row[0]) if row else None


def add_banners(
    conn: sqlite3.Connection,
    slug: str,
    banner_html: str | None,
    *,
    affiliate_tag: str | None = None,
) -> dict[str, Any]:
    """쿠팡 배너(여러 개 가능) → 카테고리 쿠팡존에 추가.

    배너 파싱 → products 업서트 → category_products 링크(중복 안전·INSERT OR IGNORE).
    반환 {'category': slug, 'added': n, 'names': [...]}. 카테고리 없으면 ValueError,
    상품명/딥링크 못 채우면 coupang_manual이 ValueError.
    """
    cid = category_id(conn, slug)
    if cid is None:
        raise ValueError(f"카테고리 slug={slug!r} 없음")
    prods = coupang_manual.products_from_banners(banner_html, affiliate_tag=affiliate_tag)
    if not prods:
        return {"category": slug, "added": 0, "names": []}
    products_store.upsert_products(conn, prods)
    base = conn.execute(
        "SELECT COALESCE(MAX(cp.display_order), 0) FROM category_products cp "
        "JOIN products p ON p.id = cp.product_id "
        "WHERE cp.category_id = ? AND p.source = 'coupang'",
        (cid,),
    ).fetchone()[0]
    names: list[str] = []
    for i, prod in enumerate(prods, start=1):
        pid = conn.execute(
            "SELECT id FROM products WHERE source = 'coupang' AND source_product_id = ?",
            (prod["source_product_id"],),
        ).fetchone()
        if pid is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO category_products "
            "(category_id, product_id, tier, is_featured, display_order) "
            "VALUES (?, ?, NULL, 0, ?)",
            (cid, int(pid[0]), base + i),
        )
        names.append(prod["name"])
    conn.commit()
    return {"category": slug, "added": len(names), "names": names}


def list_coupang(conn: sqlite3.Connection, slug: str) -> list[dict[str, Any]]:
    """카테고리 쿠팡존 상품 목록 (id, name, image_url_external, deeplink_url, display_order)."""
    cid = category_id(conn, slug)
    if cid is None:
        return []
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT p.id, p.name, p.image_url_external, p.deeplink_url, cp.display_order "
        "FROM category_products cp JOIN products p ON p.id = cp.product_id "
        "WHERE cp.category_id = ? AND p.source = 'coupang' "
        "ORDER BY cp.display_order, p.id",
        (cid,),
    ).fetchall()
    return [dict(r) for r in rows]


def remove(conn: sqlite3.Connection, slug: str, product_id: int) -> int:
    """카테고리에서 쿠팡 상품 링크 해제 (products 행은 보존 — 다른 곳서 재사용 가능). 반환: 삭제 수."""
    cid = category_id(conn, slug)
    if cid is None:
        raise ValueError(f"카테고리 slug={slug!r} 없음")
    n = conn.execute(
        "DELETE FROM category_products WHERE category_id = ? AND product_id = ? "
        "AND product_id IN (SELECT id FROM products WHERE source = 'coupang')",
        (cid, int(product_id)),
    ).rowcount
    conn.commit()
    return int(n)
