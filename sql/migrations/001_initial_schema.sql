-- 001_initial_schema.sql
-- 혼살림 SQLite 초기 스키마
-- 출처: DB.md §4~§9·§13·§14·§15-1
-- 작성: 2026-05-27 (Claude Opus 4.7) / 세션 #2

-- =====================================================
-- PRAGMA (DB.md §15-1)
-- =====================================================
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA temp_store = MEMORY;

-- =====================================================
-- schema_version (DB.md §14-2)
-- =====================================================
CREATE TABLE IF NOT EXISTS schema_version (
  version     INTEGER PRIMARY KEY,
  applied_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- =====================================================
-- personas (DB.md §8-1)
-- =====================================================
CREATE TABLE personas (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  slug          TEXT NOT NULL UNIQUE,
  title_ko      TEXT NOT NULL,
  description   TEXT NOT NULL,
  age_range     TEXT,
  display_order INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- scenarios (DB.md §7-1)
-- =====================================================
CREATE TABLE scenarios (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  slug            TEXT NOT NULL UNIQUE,
  title_ko        TEXT NOT NULL,
  description     TEXT NOT NULL,
  persona_id      INTEGER NOT NULL REFERENCES personas(id),
  budget_min_krw  INTEGER,
  budget_max_krw  INTEGER,
  season_peak     TEXT,
  priority        INTEGER NOT NULL DEFAULT 0,
  active          INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenarios_slug             ON scenarios(slug);
CREATE INDEX idx_scenarios_persona_id       ON scenarios(persona_id);
CREATE INDEX idx_scenarios_priority_active  ON scenarios(priority DESC, active);

-- =====================================================
-- products (DB.md §6)
-- =====================================================
CREATE TABLE products (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  source              TEXT NOT NULL CHECK (source IN ('coupang','aliexpress')),
  source_product_id   TEXT NOT NULL,
  name                TEXT NOT NULL,
  category_path       TEXT,
  price_krw           INTEGER,
  price_checked_at    TEXT,
  currency            TEXT NOT NULL DEFAULT 'KRW',
  image_url_external  TEXT,
  deeplink_url        TEXT NOT NULL,
  deeplink_slug       TEXT NOT NULL UNIQUE,
  affiliate_tag       TEXT NOT NULL,
  availability        TEXT CHECK (availability IN ('in_stock','out_of_stock','unknown')),
  created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (source, source_product_id)
);

CREATE INDEX idx_products_source_product_id  ON products(source, source_product_id);
CREATE INDEX idx_products_deeplink_slug      ON products(deeplink_slug);
CREATE INDEX idx_products_price_checked_at   ON products(price_checked_at);

-- =====================================================
-- images (DB.md §9)
-- =====================================================
CREATE TABLE images (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type         TEXT NOT NULL CHECK (source_type IN ('user_photo','coupang_widget','aliexpress_widget')),
  local_path          TEXT,
  r2_key              TEXT,
  widget_embed_html   TEXT,
  alt_text_ko         TEXT NOT NULL,
  width_px            INTEGER,
  height_px           INTEGER,
  file_size_bytes     INTEGER,
  mime_type           TEXT,
  license_note        TEXT,
  created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- drafts (DB.md §5)
-- =====================================================
CREATE TABLE drafts (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  scenario_id          INTEGER NOT NULL REFERENCES scenarios(id),
  working_title        TEXT,
  status               TEXT NOT NULL DEFAULT 'collected'
                         CHECK (status IN ('collected','enriched','validated','approved','published','rejected')),
  status_reason        TEXT,
  raw_payload          TEXT,
  enriched_payload     TEXT,
  validation_report    TEXT,
  created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  promoted_article_id  INTEGER,
  CHECK (promoted_article_id IS NULL OR status = 'published')
);

CREATE INDEX idx_drafts_status      ON drafts(status);
CREATE INDEX idx_drafts_scenario_id ON drafts(scenario_id);
CREATE INDEX idx_drafts_created_at  ON drafts(created_at DESC);

-- =====================================================
-- articles (DB.md §4)
-- =====================================================
CREATE TABLE articles (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  slug                    TEXT NOT NULL UNIQUE,
  scenario_id             INTEGER NOT NULL REFERENCES scenarios(id),
  title                   TEXT NOT NULL,
  summary                 TEXT NOT NULL,
  body_md                 TEXT NOT NULL,
  body_html               TEXT NOT NULL,
  meta_description        TEXT NOT NULL,
  meta_keywords           TEXT,
  schema_jsonld           TEXT NOT NULL,
  disclosure_first        TEXT NOT NULL,
  status                  TEXT NOT NULL DEFAULT 'published'
                            CHECK (status IN ('published','archived','unpublished')),
  published_at            TEXT,
  updated_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  content_hash            TEXT NOT NULL,
  truth_check_passed_at   TEXT NOT NULL,
  user_approved_at        TEXT NOT NULL,
  user_approved_note      TEXT,
  view_count_cached       INTEGER NOT NULL DEFAULT 0,
  CHECK (published_at IS NULL OR status = 'published')
);

CREATE INDEX idx_articles_slug                  ON articles(slug);
CREATE INDEX idx_articles_status_published_at   ON articles(status, published_at DESC);
CREATE INDEX idx_articles_scenario_id           ON articles(scenario_id);
CREATE INDEX idx_articles_content_hash          ON articles(content_hash);

-- 트리거: articles UPDATE 시 updated_at 자동 갱신
CREATE TRIGGER trg_articles_updated_at
AFTER UPDATE ON articles
BEGIN
  UPDATE articles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 트리거: drafts UPDATE 시 updated_at 자동 갱신
CREATE TRIGGER trg_drafts_updated_at
AFTER UPDATE ON drafts
BEGIN
  UPDATE drafts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- 조인 테이블 (DB.md §8-2·§8-3·§9-3)
-- =====================================================
CREATE TABLE article_products (
  article_id           INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  product_id           INTEGER NOT NULL REFERENCES products(id),
  display_order        INTEGER NOT NULL DEFAULT 0,
  recommendation_note  TEXT,
  PRIMARY KEY (article_id, product_id)
);

CREATE TABLE article_personas (
  article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  persona_id  INTEGER NOT NULL REFERENCES personas(id),
  relevance   INTEGER NOT NULL DEFAULT 5 CHECK (relevance BETWEEN 1 AND 5),
  PRIMARY KEY (article_id, persona_id)
);

CREATE TABLE article_images (
  article_id     INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  image_id       INTEGER NOT NULL REFERENCES images(id),
  display_order  INTEGER NOT NULL DEFAULT 0,
  placement      TEXT NOT NULL CHECK (placement IN ('hero','inline','gallery')),
  PRIMARY KEY (article_id, image_id)
);

-- =====================================================
-- article_history (DB.md §8-4) — 감사 로그
-- =====================================================
CREATE TABLE article_history (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id    INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  event_type    TEXT NOT NULL
                  CHECK (event_type IN ('created','updated','approved','unpublished','republished')),
  actor         TEXT NOT NULL CHECK (actor IN ('user','claude','system')),
  diff_summary  TEXT,
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_article_history_article_id ON article_history(article_id);

-- =====================================================
-- clicks_daily (DB.md §11-1) — D1에서 import
-- =====================================================
CREATE TABLE clicks_daily (
  date              TEXT NOT NULL,
  slug              TEXT NOT NULL,
  click_count       INTEGER NOT NULL DEFAULT 0,
  unique_ua_count   INTEGER NOT NULL DEFAULT 0,
  top_country       TEXT,
  PRIMARY KEY (date, slug)
);

CREATE INDEX idx_clicks_daily_date ON clicks_daily(date DESC);
CREATE INDEX idx_clicks_daily_slug ON clicks_daily(slug);

-- =====================================================
-- 마이그레이션 기록
-- =====================================================
INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema: personas, scenarios, products, images, drafts, articles + joins + history + clicks_daily');
