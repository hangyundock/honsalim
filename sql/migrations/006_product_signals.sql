-- 006_product_signals.sql
-- 추천 6선 객관 선정 신호 (세션 #19) — 알리익스프레스 최근 판매량 + 긍정 피드백율.
--
-- 선정 규칙: 티어(실속/고급)별로 명백한 저품질(0<evaluate_rate<80%)만 제외 후 sales_volume 내림차순 상위 3개.
--   (AI는 선정에서 빠지고 장점·단점 등 '설명'만 작성 — 투명·재현 가능. 80% 하한은 세션 #19 실측 보정.)
-- 화면 표기: 판매량만 정직 표기("알리 최근 판매량 N, 판매처 기준"). 만족도는 변별력이 약해 선정 필터로만 사용.
-- 출처: 라이브 응답 실측 — lastest_volume(정수)·evaluate_rate("93.8%" 문자열) 확인 [확정 세션 #19].

ALTER TABLE products ADD COLUMN sales_volume  INTEGER;  -- 알리 lastest_volume (최근 판매량)
ALTER TABLE products ADD COLUMN evaluate_rate REAL;     -- 알리 긍정 피드백율 % (예: 93.8) — 선정 필터용

INSERT INTO schema_version (version, description)
VALUES (6, 'products.sales_volume + evaluate_rate — 추천 6선 객관 선정 신호 (세션 #19)');
