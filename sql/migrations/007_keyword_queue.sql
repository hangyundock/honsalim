-- 007_keyword_queue.sql
-- 키워드 발행 큐 — 운영 대시보드 "대기 키워드" + 키워드별 제품 미리선택 (세션 #25).
--
-- 모델 [확정 #25]: 키워드(주제)를 1급 큐로 관리. 글 생성 시 키워드에서 시나리오를 자동 파생
--   (scenario_id)하여 기존 drafts→articles 발행 기계를 그대로 재사용한다. articles 스키마를
--   건드리지 않아 라이브 사이트에 무위험(안전 우선 §0). scenario_id NOT NULL 제약 충족.
-- 명명: collector.keyword_map / keyword_research(SEO 키워드 연구)와 구분해 keyword_queue.
-- target_products: 운영자가 미리 선택/입력한 추천 상품(JSON). 쿠팡 수동 입력(공식 위젯/텍스트) 포함.
--   형식 예: [{"source":"coupang","source_product_id":"...","name":"...","deeplink_url":"...",
--             "price_krw":12900,"widget_html":"<...>"}]

CREATE TABLE keyword_queue (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword         TEXT NOT NULL,                      -- 검색 키워드/주제 (예: "자취생 전자레인지 추천")
  slug            TEXT NOT NULL UNIQUE,               -- 식별·URL slug
  channel         TEXT NOT NULL DEFAULT 'ali'
                    CHECK (channel IN ('ali','coupang','both')),
  status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','generating','drafted','published','disabled','failed')),
  status_reason   TEXT,
  persona_id      INTEGER REFERENCES personas(id),    -- 선택: 콘텐츠 각도(없으면 기본 페르소나)
  budget_min_krw  INTEGER,
  budget_max_krw  INTEGER,
  target_products TEXT,                               -- JSON: 미리선택 상품 [{source,source_product_id,...}]
  notes           TEXT,                               -- 운영자 메모
  score           REAL NOT NULL DEFAULT 0,            -- 정렬 우선순위(검색량 등)
  priority        INTEGER NOT NULL DEFAULT 0,         -- 수동 우선순위
  scenario_id     INTEGER REFERENCES scenarios(id),   -- 자동 파생 시나리오(재생성 시 재사용)
  times_used      INTEGER NOT NULL DEFAULT 0,
  fail_count      INTEGER NOT NULL DEFAULT 0,
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_keyword_queue_status  ON keyword_queue(status);
CREATE INDEX idx_keyword_queue_channel ON keyword_queue(channel);
CREATE INDEX idx_keyword_queue_order   ON keyword_queue(score DESC, priority DESC, id);

-- updated_at 자동 갱신 트리거 (다른 테이블과 동일 패턴)
CREATE TRIGGER trg_keyword_queue_updated_at
AFTER UPDATE ON keyword_queue
BEGIN
  UPDATE keyword_queue SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- drafts ↔ keyword 역링크 (nullable). 기존 시나리오 draft는 NULL.
-- 단순 ADD COLUMN — 테이블 재구축 없이 무손상(기존 데이터·트리거·인덱스 보존).
ALTER TABLE drafts ADD COLUMN keyword_id INTEGER REFERENCES keyword_queue(id);
CREATE INDEX idx_drafts_keyword_id ON drafts(keyword_id);

INSERT INTO schema_version (version, description)
VALUES (7, 'keyword_queue 발행 큐 + drafts.keyword_id — 운영 대시보드 키워드 모델 (세션 #25)');
