-- 008_article_structured.sql
-- 발행 글 Tier 2 구조화 데이터 (세션 #34) — 키워드 글이 카테고리 페이지만큼 풍부하도록.
--
-- enriched_payload(draft·미리보기)의 product_notes(추천별 장단점·추천대상)·quick_verdict(빠른 결론)·
-- checkpoints(구매 전 체크)를 발행 시 articles에 보존한다. 미리보기와 발행 글의 레이아웃을 일치시킨다
-- (§2-마 검토 화면 = 발행 화면). 렌더러는 이 JSON을 structured로 _article_page_ctx에 넘겨 픽 카드/
-- 요약 박스를 채운다(없으면 graceful — 옛 글·구조화 없는 글도 안전, 영향 0).

ALTER TABLE articles ADD COLUMN structured_json TEXT;

INSERT INTO schema_version (version, description)
VALUES (8, 'articles.structured_json — 발행 글 Tier 2 구조화(추천 장단점·빠른결론·체크포인트) 보존 (세션 #34)');
