-- 009_api_usage.sql — 외부 API 사용량/비용 추적 (세션 #36)
--
-- 배경: Google(Imagen) 월 지출 상한 초과(429)로 자동 카테고리 대표 이미지 생성이 막힘. 구글의 실제
--   청구액은 단순 API 키로 조회 불가 → 우리가 직접 거는 Imagen 호출을 기록해 '이번 달 사용·추정비용·
--   상한 대비'를 대시보드에 보여 결제 시점을 미리 알 수 있게 한다(명시적 추정, 가짜 지표 아님·§0).
--
-- 호출 1건 = 1행. 성공만 비용에 집계(est_cost_usd>0). 429/오류는 status로 구분해 한도초과 알림에 사용.

CREATE TABLE IF NOT EXISTS api_usage (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    provider     TEXT NOT NULL,                       -- 'google_imagen'
    kind         TEXT NOT NULL,                       -- 'image'
    status       TEXT NOT NULL,                       -- 'ok' | 'error_429' | 'error'
    est_cost_usd REAL NOT NULL DEFAULT 0,             -- 성공 시 장당 추정 단가(~0.02), 실패 0
    detail       TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_api_usage_provider_created
    ON api_usage(provider, created_at);

INSERT INTO schema_version (version, description)
VALUES (9, 'api_usage — 외부 API(Google Imagen) 사용량/추정비용 추적, 대시보드 지출 표시 (세션 #36)');
