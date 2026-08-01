-- 010_api_usage_tokens.sql — LLM 토큰 사용량 추적 컬럼 (세션 #48)
--
-- 배경: #36의 api_usage는 Google Imagen 전용(장수·추정단가)이라 **정작 매일 돈이 나가는 LLM
--   본문 생성은 아무 기록이 없었다**. 콘솔 로그의 usage는 재시도 중 '마지막 1회분'만 남고 나머지는
--   버려져, "오늘 얼마 썼나"에 시스템이 답을 못 했다(#48 실측 중 적발 — 라이브 15콜의 비용을
--   원화로 환산 불가).
--
-- 토큰은 항상 기록한다. 단가는 설정(llm_price_*)이 있을 때만 est_cost_usd로 환산한다 —
-- 모르는 단가를 지어내지 않는다(§0 가짜 지표 금지). 단가 미설정 시 est_cost_usd=0, 토큰은 유효.
--
-- 기존 행(Imagen)은 NULL로 남는다 — 하위 호환.

ALTER TABLE api_usage ADD COLUMN tokens_in INTEGER;
ALTER TABLE api_usage ADD COLUMN tokens_out INTEGER;

INSERT INTO schema_version (version, description)
VALUES (10, 'api_usage.tokens_in/out — LLM 토큰 사용량 추적(재시도 포함), 비용 가시화 (세션 #48)');
