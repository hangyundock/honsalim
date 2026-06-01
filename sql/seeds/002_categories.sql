-- 002_categories.sql — 카테고리 seed (세션 #17)
--
-- 사무용 의자·컴퓨터 책상: 알리 소싱 라이브 검증 완료 (세션 #14·#15).
-- slug = seo_keywords.yml 키와 일치 (SEO 키워드·검색 밴드 연동).
-- name_ko = seo_keywords.yml primary. intro = 1인 가구 관점 한 줄 (운영자 혼살다 톤).
-- status = draft (콘텐츠 작성·검증 통과 후 published 전이 — 준비 안 된 빈 페이지 노출 방지).
-- INSERT OR IGNORE — slug UNIQUE 기반 idempotent (seed 반복 실행 안전).

INSERT OR IGNORE INTO categories
  (slug, name_ko, intro, group_slug, group_name_ko, scenario_slug, display_order, status)
VALUES
  ('office-chair', '사무용 의자',
   '하루 8시간 앉는 재택·홈오피스를 위한 의자. 요추 지지와 타입별 차이를 1인 가구 관점에서 비교합니다.',
   'homeoffice', '홈오피스', 'homeoffice-chair-desk-50', 10, 'draft'),
  ('desk', '컴퓨터 책상',
   '좁은 원룸·홈오피스에 맞는 컴퓨터 책상. 크기·형태·수납을 공간과 예산 기준으로 골라봅니다.',
   'homeoffice', '홈오피스', 'homeoffice-chair-desk-50', 20, 'draft'),
  ('monitor-stand', '모니터 받침대',
   '책상 위 공간을 정리하고 모니터를 눈높이에 맞추는 받침대. 형태·수납·재질을 1인 가구 책상 기준으로 비교합니다.',
   'homeoffice', '홈오피스', 'homeoffice-chair-desk-50', 30, 'draft'),
  -- 세션 #19 홈오피스 클러스터 확장 (DeepSeek 전환 후 첫 신규 생성)
  ('laptop-stand', '노트북 거치대',
   '노트북을 눈높이에 맞춰 목·어깨 부담을 줄이는 거치대. 높이·각도·접이·재질을 1인 가구 책상 기준으로 비교합니다.',
   'homeoffice', '홈오피스', 'homeoffice-chair-desk-50', 40, 'draft'),
  ('monitor-arm', '모니터암',
   '책상 위를 비우고 모니터 위치를 자유롭게 잡는 거치 암. VESA 호환·가동 방식·내구를 1인 가구 책상 기준으로 비교합니다.',
   'homeoffice', '홈오피스', 'homeoffice-chair-desk-50', 50, 'draft');
