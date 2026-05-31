-- 005_category_concept_image.sql
-- 카테고리 개념 이미지 (Google Imagen 4 Fast 생성) — 세션 #17
-- "고르는 법" 섹션에 텍스트 없는 컨셉 사진 1장을 넣어 가독성·체류시간↑ (글만 나열 시 이탈 방지).
--   concept_image     : 배포 경로(/static/images/concepts/<slug>.webp)
--   concept_image_alt : 접근성·SEO용 한글 대체 텍스트

ALTER TABLE categories ADD COLUMN concept_image     TEXT;
ALTER TABLE categories ADD COLUMN concept_image_alt TEXT;

INSERT INTO schema_version (version, description)
VALUES (5, 'categories.concept_image + concept_image_alt — 개념 이미지(Imagen) (세션 #17)');
