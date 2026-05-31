-- 004_category_structured.sql
-- 카테고리 페이지 구조화 콘텐츠 (세션 #17 — 사무용 의자 구성 표준 차용)
-- 출처: scripts/category_page_prototype.py 구조 + docs/CATEGORY_PAGE.md §2
--
-- categories.content_json : 도입·타입비교표·체크리스트·흔한실수·한눈비교표를 한 JSON에 저장
--   {lead, guide_intro, type_table:[{type,trait,for}], checkpoints:[{title,why}],
--    mistakes, compare:{rows:[],cells:[{slug,values:[]}]}}
--   (guide_md/guide_html은 SEO 측정·기록용 산문 합본으로 재사용 — 003 컬럼 유지)
-- category_products.pick_type : 추천 6선 타입명(타입 선택기·카드 배지)

ALTER TABLE categories ADD COLUMN content_json TEXT;
ALTER TABLE category_products ADD COLUMN pick_type TEXT;

INSERT INTO schema_version (version, description)
VALUES (4, 'categories.content_json + category_products.pick_type — 카테고리 구조화 콘텐츠(의자 구성) (세션 #17)');
