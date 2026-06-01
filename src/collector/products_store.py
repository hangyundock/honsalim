"""products_store — 수집된 상품 dict → products 테이블 upsert.

출처: DB §6 products 스키마 [확정] + BACKEND §2-1 collector 책임.

``collector.aliexpress.map_product()`` 등이 반환하는 products-스키마 dict를
``UNIQUE(source, source_product_id)`` 기준으로 INSERT 또는 UPDATE 한다.

- 신규: INSERT (``created_at``·``updated_at``·``last_seen_at`` = CURRENT_TIMESTAMP)
- 기존: UPDATE (name·price·availability 등 갱신 + ``updated_at``·``last_seen_at`` 갱신,
        가격이 있으면 ``price_checked_at`` 갱신). ``created_at``·``deeplink_slug`` 보존.

``deeplink_url``·``source_product_id`` 등 NOT NULL 필수 필드가 빈 행은 적재하지 않고
skip 한다 (DB NOT NULL 제약 회피 + 제휴 링크 없는 상품은 무의미).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# products 테이블 NOT NULL·필수 필드 (DB §6) — 하나라도 비면 적재 불가
REQUIRED_FIELDS: tuple[str, ...] = (
    "source",
    "source_product_id",
    "name",
    "deeplink_url",
    "deeplink_slug",
    "affiliate_tag",
)

# ON CONFLICT 대상은 (source, source_product_id) 단일 — deeplink_slug는 source_product_id에서
# 결정론적(ali-<pid>)이라 같은 충돌 키로 수렴, 별도 UNIQUE 위반 없음.
_UPSERT_SQL = """
INSERT INTO products (
    source, source_product_id, name, category_path,
    price_krw, original_price_krw, discount_pct, price_checked_at,
    sales_volume, evaluate_rate,
    currency, image_url_external,
    deeplink_url, deeplink_slug, affiliate_tag, availability, last_seen_at
) VALUES (
    :source, :source_product_id, :name, :category_path,
    :price_krw, :original_price_krw, :discount_pct,
    CASE WHEN :price_krw IS NOT NULL THEN CURRENT_TIMESTAMP ELSE NULL END,
    :sales_volume, :evaluate_rate,
    :currency, :image_url_external,
    :deeplink_url, :deeplink_slug, :affiliate_tag, :availability, CURRENT_TIMESTAMP
)
ON CONFLICT(source, source_product_id) DO UPDATE SET
    name               = excluded.name,
    category_path      = excluded.category_path,
    price_krw          = excluded.price_krw,
    original_price_krw = excluded.original_price_krw,
    discount_pct       = excluded.discount_pct,
    price_checked_at   = CASE
                            WHEN excluded.price_krw IS NOT NULL THEN CURRENT_TIMESTAMP
                            ELSE products.price_checked_at END,
    sales_volume       = excluded.sales_volume,
    evaluate_rate      = excluded.evaluate_rate,
    currency           = excluded.currency,
    image_url_external = excluded.image_url_external,
    deeplink_url       = excluded.deeplink_url,
    affiliate_tag      = excluded.affiliate_tag,
    availability       = excluded.availability,
    updated_at         = CURRENT_TIMESTAMP,
    last_seen_at       = CURRENT_TIMESTAMP
"""


@dataclass
class UpsertResult:
    """적재 결과 집계 — 신규/갱신/스킵 건수."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    @property
    def total_written(self) -> int:
        return self.inserted + self.updated


def is_valid(row: dict[str, Any]) -> bool:
    """NOT NULL 필수 필드가 모두 채워졌는지 — 빈 값(None·"")은 무효."""
    return all(row.get(f) not in (None, "") for f in REQUIRED_FIELDS)


def upsert_products(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> UpsertResult:
    """상품 dict 리스트를 products 테이블에 upsert.

    각 행은 ``aliexpress.map_product()`` 형식 dict. 필수 필드 누락 시 skip.
    호출자가 conn 생명주기 관리 — 본 함수는 한 번 commit 후 결과 집계만 반환.
    """
    result = UpsertResult()
    for row in rows:
        if not is_valid(row):
            result.skipped += 1
            continue
        existing = conn.execute(
            "SELECT 1 FROM products WHERE source = ? AND source_product_id = ?",
            (row["source"], row["source_product_id"]),
        ).fetchone()
        params = {
            "source": row["source"],
            "source_product_id": row["source_product_id"],
            "name": row["name"],
            "category_path": row.get("category_path"),
            "price_krw": row.get("price_krw"),
            "original_price_krw": row.get("original_price_krw"),
            "discount_pct": row.get("discount_pct"),
            "sales_volume": row.get("sales_volume"),
            "evaluate_rate": row.get("evaluate_rate"),
            "currency": row.get("currency") or "KRW",
            "image_url_external": row.get("image_url_external"),
            "deeplink_url": row["deeplink_url"],
            "deeplink_slug": row["deeplink_slug"],
            "affiliate_tag": row["affiliate_tag"],
            "availability": row.get("availability") or "unknown",
        }
        conn.execute(_UPSERT_SQL, params)
        if existing:
            result.updated += 1
        else:
            result.inserted += 1
    conn.commit()
    return result
