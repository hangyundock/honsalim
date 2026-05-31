-- 003_category_content.sql
-- 카테고리 가이드 글(AI 생성, 혼살다 명의) + 추천 6선 장단점 영속화 (세션 #17)
-- 출처: docs/CATEGORY_PAGE.md §2-6(구매가이드 8요소)·§2-7(추천 비교카드)·§3 콘텐츠 8요소
--
-- categories         : 구매가이드 산문(8요소)·FAQ + 생성 시각
-- category_products  : 추천 6선(is_featured=1)의 장점·단점·추천대상 (비교 카드용)
--                      is_featured·tier 컬럼은 002에서 신설 — 여기선 콘텐츠 메타만 추가

ALTER TABLE categories ADD COLUMN guide_title        TEXT;  -- 가이드 제목(예: "모니터 받침대, 어떻게 고를까")
ALTER TABLE categories ADD COLUMN guide_md           TEXT;  -- 8요소 구매가이드 산문(마크다운, disclosure 포함)
ALTER TABLE categories ADD COLUMN guide_html         TEXT;  -- 렌더용 HTML(마크다운 변환)
ALTER TABLE categories ADD COLUMN faq_json           TEXT;  -- [{"q":..,"a":..}, ...] JSON
ALTER TABLE categories ADD COLUMN guide_generated_at TEXT;  -- 생성 시각(추적·재생성 판단)

ALTER TABLE category_products ADD COLUMN pros_json   TEXT;  -- 추천 6선 장점 ["..", ".."] JSON (is_featured=1만)
ALTER TABLE category_products ADD COLUMN cons_json   TEXT;  -- 단점 JSON
ALTER TABLE category_products ADD COLUMN pick_reason TEXT;  -- 추천 대상/이유 한 줄

INSERT INTO schema_version (version, description)
VALUES (3, 'categories(guide_*·faq) + category_products(pros/cons/pick_reason) — 카테고리 가이드 글·추천 6선 (세션 #17)');
