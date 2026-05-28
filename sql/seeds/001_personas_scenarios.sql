-- 001_personas_scenarios.sql
-- 혼살림 초기 시드 (페르소나 3 + 시나리오 10)
-- 출처: SCENARIOS.md §8-1·§8-2
-- 적용 전제: 001_initial_schema.sql 적용 완료
-- 작성: 2026-05-27 (Claude Opus 4.7) / 세션 #2

-- =====================================================
-- personas (3건) — SCENARIOS.md §8-1
-- =====================================================
INSERT OR IGNORE INTO personas (slug, title_ko, description, age_range, display_order) VALUES
  ('cheot-jachi',  '새내기 자취생',     '첫 자취·이사 직전 20대',          '20대',    1),
  ('homeoffice',   '재택근무자',         '30~40대 홈오피스 셋업',           '30~40대', 2),
  ('minimal-life', '1인 가구 정착자',    '자취 2년차 이상 미니멀 라이프',    '30~40대', 3);

-- =====================================================
-- scenarios (10건) — SCENARIOS.md §8-2
-- persona_id는 (SELECT id FROM personas WHERE slug=?) 로 안전 매핑
-- =====================================================
INSERT OR IGNORE INTO scenarios (slug, title_ko, description, persona_id, budget_min_krw, budget_max_krw, season_peak, priority, active) VALUES
  ('wonroom-cheot-jachi-30',
   '원룸 첫 자취 30만원 필수템 패키지 — 신학기 완성',
   '신학기 1차 자취생을 위한 30만원 필수템 6~8개 추천',
   (SELECT id FROM personas WHERE slug='cheot-jachi'),
   250000, 350000, '2-3월', 100, 1),

  ('cheot-jachi-50-complete',
   '첫 자취 살림 50만원 완성판 — 원룸 1주일 안에 끝내기',
   '신학기 자취 50만원 완성 패키지 8~10개',
   (SELECT id FROM personas WHERE slug='cheot-jachi'),
   450000, 550000, '2-3월', 95, 1),

  ('cheot-jachi-gajeon-100',
   '새내기 자취 1인 가전 100만원 풀세트 — 후회 없는 첫 선택',
   '1인 가전 풀세트 10~12개',
   (SELECT id FROM personas WHERE slug='cheot-jachi'),
   900000, 1100000, '2-3월', 85, 1),

  ('gaeul-cheot-jachi-30',
   '가을 신학기 자취 보완 살림 30만원 — 1학기 후 진짜 필요한 것',
   '2학기 자취 보완 6~8개',
   (SELECT id FROM personas WHERE slug='cheot-jachi'),
   250000, 350000, '8-9월', 80, 1),

  ('homeoffice-chair-desk-50',
   '홈오피스 책상·의자 50만원 세팅 — 재택 8시간 견디는 조합',
   '홈오피스 책상·의자 핵심 6~8개',
   (SELECT id FROM personas WHERE slug='homeoffice'),
   450000, 550000, '11-1월', 95, 1),

  ('homeoffice-100-setup',
   '홈오피스 100만원 효율 셋업 — 모니터·조명·환경까지',
   '홈오피스 100만원 셋업 8~10개',
   (SELECT id FROM personas WHERE slug='homeoffice'),
   900000, 1100000, '11-1월', 85, 1),

  ('homeoffice-200-premium',
   '홈오피스 200만원 프리미엄 풀셋업 — 본격 1인 작업실',
   '홈오피스 프리미엄 10~12개',
   (SELECT id FROM personas WHERE slug='homeoffice'),
   1800000, 2200000, '11-1월', 70, 1),

  ('saehae-minimal-20',
   '1인 가구 새해 미니멀 살림 20만원 — 비우고 채우기',
   '새해 미니멀 정리·수납 6~8개',
   (SELECT id FROM personas WHERE slug='minimal-life'),
   150000, 250000, '1월', 90, 1),

  ('jeongchak-gajeon-up-50',
   '1인 정착 소형 가전 업그레이드 50만원 — 자취 3년차의 정답',
   '소형 가전 업그레이드 6~8개',
   (SELECT id FROM personas WHERE slug='minimal-life'),
   450000, 550000, '1월', 80, 1),

  ('isacheol-jeongni-30',
   '원룸 이사철 정리·수납 시스템 30만원 — 옮기기 전에 비우고',
   '봄/가을 이사철 수납 시스템 6~8개',
   (SELECT id FROM personas WHERE slug='minimal-life'),
   250000, 350000, '3-4월·9-10월', 70, 1);
