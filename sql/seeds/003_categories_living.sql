-- 003_categories_living.sql — 1인 살림 확장 카테고리 seed (세션 #20)
--
-- 출처: 네이버 검색광고 실측(세션 #20) 기반 선별. "1인 ○○" 키워드는 검색량 빈약(1인냄비 350 등)으로
--   확인되어, 대표어(고볼륨·중간경쟁·알리적합 비가전)로 카테고리를 잡고 1인은 콘텐츠 앵글+보조키워드로 공략.
--   실측: 빨래건조대 63,120 / 도마 40,270 / 미니제습기 18,170 (월, PC+모바일) — 전부 경쟁도 중간.
-- 가전(제습기·인덕션)은 국내 브랜드 지향이라 알리 부적합 → "미니/소형" 세그먼트만 채택.
-- status=draft (운영자 1클릭 승인 후 published — E7). INSERT OR IGNORE 멱등.

INSERT OR IGNORE INTO categories
  (slug, name_ko, intro, group_slug, group_name_ko, display_order, status)
VALUES
  ('cutting-board', '도마',
   '매일 쓰는 도마는 위생과 칼자국 관리가 핵심. 재질(나무·스텐·실리콘)별 장단을 1인 주방 기준으로 비교합니다.',
   'kitchen', '주방 살림', 60, 'draft'),
  ('drying-rack', '빨래건조대',
   '좁은 원룸에서 자리를 덜 차지하는 건조대. 접이식·미니·스탠드형을 공간과 빨래량 기준으로 비교합니다.',
   'living', '생활 살림', 70, 'draft'),
  ('mini-dehumidifier', '미니 제습기',
   '원룸·옷장 습기와 곰팡이를 잡는 소형 제습기. 흡습 방식과 용량을 1인 공간 기준으로 비교합니다.',
   'living', '생활 살림', 80, 'draft');
