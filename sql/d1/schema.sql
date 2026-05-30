-- D1 스키마 — Cloudflare D1 `honsalim-clicks` (database_id 9bae858e-…, wrangler.toml)
-- 출처: DB §11 [확정] + go_gateway.js(clicks writer) + tracker.d1_aggregator(clicks_daily writer).
--
-- SQLite migrations(sql/migrations/)와 별개 — D1는 원격 클릭 게이트웨이 전용 DB.
-- 적용(go-live, 사용자 명시 승인 후):
--   wrangler d1 execute honsalim-clicks --remote --file sql/d1/schema.sql
-- 멱등: CREATE TABLE IF NOT EXISTS — 재실행 안전.

-- ─── slug_map — /go/<slug> → 어필리에이트 deep link 라우팅 (DB §11-1) ───
-- 생산자: tracker.slug_map.sync_slug_map (published article 상품 → UPSERT, 매 배포 시)
-- 소비자: go_gateway.js (SELECT deeplink_url FROM slug_map WHERE slug = ?)
CREATE TABLE IF NOT EXISTS slug_map (
    slug             TEXT PRIMARY KEY,           -- /go/<slug> (= products.deeplink_slug)
    deeplink_url     TEXT NOT NULL,              -- 쿠팡·알리 deep link (302 대상)
    source           TEXT NOT NULL,              -- 'coupang' / 'aliexpress'
    product_id_local INTEGER,                    -- SQLite products.id (비강제 FK)
    updated_at       TEXT NOT NULL               -- 빌드/배포 시 upsert ISO 8601
);

-- ─── clicks — 원본 클릭 로그 (append-only, go_gateway.js INSERT) ───
-- go_gateway.js: INSERT INTO clicks (slug, ts, ua_hash, country, referrer_domain, bot_flag)
-- PII 회피(BACKEND §5-3): IP 미저장 · UA는 SHA-256 16자 · referrer hostname만.
CREATE TABLE IF NOT EXISTS clicks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT NOT NULL,
    ts              TEXT NOT NULL,               -- ISO 8601 (datetime('now'))
    ua_hash         TEXT,                        -- UA SHA-256 첫 16 hex
    country         TEXT,                        -- CF-IPCountry
    referrer_domain TEXT,                        -- referrer hostname만
    bot_flag        INTEGER NOT NULL DEFAULT 0   -- 0/1 (UA 기반 추정)
);
CREATE INDEX IF NOT EXISTS idx_clicks_slug_ts ON clicks (slug, ts);

-- ─── clicks_daily — 일별 집계 (tracker.d1_aggregator.aggregate INSERT) ───
-- aggregate(): INSERT INTO clicks_daily (date, slug, clicks) … ON CONFLICT(date, slug)
CREATE TABLE IF NOT EXISTS clicks_daily (
    date   TEXT NOT NULL,                        -- YYYY-MM-DD (KST)
    slug   TEXT NOT NULL,
    clicks INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (date, slug)
);
