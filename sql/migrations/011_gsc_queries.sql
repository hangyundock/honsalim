-- 011_gsc_queries.sql — 구글 서치콘솔 검색어 적립 (세션 #52)
--
-- 배경: 우리는 **네이버 검색량**으로 키워드를 고르는데 트래픽은 **구글**에서만 받는다. 어느 쪽이
--   옳은 신호인지 판정하려 했으나 표본이 없어 실패했다(#52 ops 파일럿: 28일 노출 66 중 82%가
--   구글 익명화 쿼리 = 목표 키워드가 아닌 초롱테일). GSC는 **최근 16개월만** 보관하고 조회할
--   때마다 창이 밀리므로, 지금부터 주 1회 적립해 두지 않으면 몇 달 뒤에도 같은 이유로 판단이 불가하다.
--
-- 이 표의 목적: '구글에서 실제로 검색되는 우리 주제어' 사전을 시간에 걸쳐 축적한다.
--   재평가 기준(#52 확정) = 월 노출 500+ 또는 비익명 쿼리 30+ 축적 시 키워드 선정 신호 재판단.
--
-- ★멱등: (period_start, period_end, query, page) 유니크 — 같은 창을 다시 적립해도 중복이 아니라
--   최신 값으로 갱신된다(UPSERT). 무인 주간 훅이 두 번 돌아도 안전.
-- ※page는 NULL일 수 있다(쿼리 단독 집계) — SQLite는 NULL을 서로 다른 값으로 취급하므로
--   유니크 보장을 위해 저장 시 빈 문자열('')로 정규화한다(tracker.gsc_store가 담당).

CREATE TABLE IF NOT EXISTS gsc_queries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at   TEXT    NOT NULL,          -- 적립 시각 (ISO)
    period_start  TEXT    NOT NULL,          -- 조회 창 시작 (YYYY-MM-DD)
    period_end    TEXT    NOT NULL,          -- 조회 창 끝
    query         TEXT    NOT NULL,          -- 검색어 (구글 익명화분은 애초에 안 내려옴)
    page          TEXT    NOT NULL DEFAULT '', -- 잡힌 페이지 URL ('' = 쿼리 단독 집계)
    clicks        INTEGER NOT NULL DEFAULT 0,
    impressions   INTEGER NOT NULL DEFAULT 0,
    ctr           REAL    NOT NULL DEFAULT 0,
    position      REAL    NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_gsc_queries_window
    ON gsc_queries (period_start, period_end, query, page);

CREATE INDEX IF NOT EXISTS idx_gsc_queries_query ON gsc_queries (query);

INSERT INTO schema_version (version, description)
VALUES (11, 'gsc_queries — 구글 검색어 주간 적립(구글 실수요 사전·키워드 신호 재판단 근거) (세션 #52)');
