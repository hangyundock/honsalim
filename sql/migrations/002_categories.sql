-- 002_categories.sql
-- 혼살림 "카테고리 우선" 구조 전환 (세션 #17)
-- 출처: docs/CATEGORY_PAGE.md (세션 #14·#16 확정) + DECISIONS O2·O13·O14
--
-- 신설:
--   categories         : 제품 카테고리 정의 (사무용 의자·컴퓨터 책상 ...). seo_keywords.yml 키(slug)와 일치.
--   category_products  : 카테고리↔제품 연결 + 티어(실속/고급) + 추천 6선 여부.
-- 확장:
--   products.original_price_krw / discount_pct
--     : 세션 #16 map_product가 계산했으나 in-memory였던 신뢰 신호를 영속화
--       (정가→판매가+할인율, CATEGORY_PAGE.md §4). 렌더러가 DB를 읽으므로 컬럼 필요.

-- =====================================================
-- categories (세션 #17) — 제품 카테고리
-- =====================================================
CREATE TABLE categories (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  slug          TEXT NOT NULL UNIQUE,            -- office-chair, desk (seo_keywords.yml 키와 일치)
  name_ko       TEXT NOT NULL,                   -- 사무용 의자
  intro         TEXT,                            -- 인덱스·홈 카드 한줄 설명 (1인가구 관점)
  group_slug    TEXT,                            -- 상위 그룹 식별 (homeoffice ...) — 인덱스 그룹핑
  group_name_ko TEXT,                            -- 홈오피스
  scenario_slug TEXT,                            -- (선택) 연결 세팅 slug — 카테고리↔세팅 크로스링크
  display_order INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft','published')),  -- draft=준비 중(미노출/표시), published=공개
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_slug         ON categories(slug);
CREATE INDEX idx_categories_status_order ON categories(status, display_order);

-- 트리거: categories UPDATE 시 updated_at 자동 갱신 (articles·drafts 패턴과 동일)
CREATE TRIGGER trg_categories_updated_at
AFTER UPDATE ON categories
BEGIN
  UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- category_products (세션 #17) — 카테고리에 속한 제품 + 티어 + 추천 여부
--   추천·비교 카드(featured 2티어) + 전체 제품 카탈로그(전체)를 모두 이 테이블로 조회.
-- =====================================================
CREATE TABLE category_products (
  category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  product_id    INTEGER NOT NULL REFERENCES products(id),
  tier          TEXT CHECK (tier IN ('budget','premium')),   -- 💰실속 / ⭐고급 (NULL=카탈로그 전용)
  is_featured   INTEGER NOT NULL DEFAULT 0,                   -- 1=추천·비교 카드(엄선 6선) 노출
  display_order INTEGER NOT NULL DEFAULT 0,
  added_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (category_id, product_id)
);

CREATE INDEX idx_category_products_cat      ON category_products(category_id, display_order);
CREATE INDEX idx_category_products_featured ON category_products(category_id, is_featured, display_order);

-- =====================================================
-- products 신뢰 신호 컬럼 확장 (세션 #17)
--   기존 행은 NULL — 재수집 시 collector가 채움. 할인율은 product_filter가 부풀린 할인(>70%)을 차단한 값.
-- =====================================================
ALTER TABLE products ADD COLUMN original_price_krw INTEGER;
ALTER TABLE products ADD COLUMN discount_pct       INTEGER;

-- =====================================================
-- 마이그레이션 기록
-- =====================================================
INSERT INTO schema_version (version, description)
VALUES (2, 'categories + category_products + products(original_price_krw, discount_pct) — 카테고리 우선 구조 (세션 #17)');
