"""게이밍의자 → '의자' 카테고리 흡수 — 분류 체계(대/중/소) 적용 (세션 #31).

기존 'office-chair' 카테고리를 **'의자'로 넓혀**(사무용+게이밍) 게이밍의자 글의 제품을 흡수한다.
타입(사무용/게이밍)은 렌더 시 제품명으로 도출(`renderer._derive_type`)하므로 별도 태그 불필요.
쿠팡(source=coupang) 제품은 렌더러가 상단 '운영자 추천' zone으로 분리한다.

멱등 — 여러 번 실행해도 안전. 운영 반영:  python scripts/apply_chair_taxonomy.py <db_path>
(인자 없으면 기본 data/honsalim.db)

★ UTF-8 한글은 이 .py 파일 실행으로만 안전 (PowerShell 파이프는 한글 깨짐 — 세션 #31 교훈).
"""

from __future__ import annotations

import sqlite3
import sys

GAMING_ARTICLE_SLUG = "kw-e3d08a2c"


def main(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id FROM categories WHERE slug='office-chair'").fetchone()
    if row is None:
        print("[FAIL] office-chair 카테고리 없음")
        return 1
    cid = row["id"]

    # 1) 카테고리 메타 — '의자'(사무용+게이밍)로 확장.
    #    guide_title은 빌드(LLM)가 SEO primary '사무용 의자'로 덮으므로, 빌드 후 이 스크립트를
    #    다시 실행해 양쪽 포괄 제목으로 덮어쓴다(SEO 키워드는 본문 밀도로 유지).
    conn.execute(
        "UPDATE categories SET name_ko = ?, intro = ?, guide_title = ? WHERE slug = 'office-chair'",
        (
            "의자",
            "사무용·게이밍 의자를 1인 가구 책상 기준으로 비교합니다.",
            "사무용·게이밍 의자 고르는 법 — 1인 가구 추천 비교",
        ),
    )

    # 2) 게이밍의자 글 제품 흡수 (멱등 — 이미 연결된 건 건너뜀)
    prods = conn.execute(
        "SELECT p.id, p.price_krw FROM article_products ap "
        "JOIN products p ON p.id = ap.product_id "
        "JOIN articles a ON a.id = ap.article_id WHERE a.slug = ?",
        (GAMING_ARTICLE_SLUG,),
    ).fetchall()
    added = 0
    for p in prods:
        if conn.execute(
            "SELECT 1 FROM category_products WHERE category_id = ? AND product_id = ?",
            (cid, p["id"]),
        ).fetchone():
            continue
        tier = "budget" if (p["price_krw"] or 0) < 100000 else "premium"
        conn.execute(
            "INSERT INTO category_products "
            "(category_id, product_id, tier, is_featured, display_order) VALUES (?, ?, ?, 0, 100)",
            (cid, p["id"], tier),
        )
        added += 1

    # 3) 게이밍의자 '글'은 의자 카테고리가 대체 → 비공개. 라이브 URL은 renderer.REDIRECTS가 의자로 301.
    cur = conn.execute(
        "UPDATE articles SET status='unpublished', published_at=NULL, updated_at=datetime('now') "
        "WHERE slug = ? AND status = 'published'",
        (GAMING_ARTICLE_SLUG,),
    )
    unpublished = cur.rowcount
    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM category_products WHERE category_id = ?", (cid,)
    ).fetchone()[0]
    conn.close()
    print(
        f"[OK] '의자' 카테고리 확장 · 게이밍 제품 {added}개 신규 흡수 · 총 {total}개 · "
        f"게이밍의자 글 비공개 {unpublished}건(→ 의자 카테고리 301)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data/honsalim.db"))
