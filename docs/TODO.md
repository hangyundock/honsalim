# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션)

- [x] ~~**docs/SUMMARY.md + REVIEW_QUESTIONS.md + SUMMARY_PATCH_v1.1.md 정독**~~ ✅ 세션 #9 완료 — Phase 3 진입 게이트 통과 [확정 사용자]
- [x] ~~**Phase 3 사전 작업**: Google AI Studio API 키 발급~~ ✅ 세션 #9 완료 — `D:\secrets\honsalim.env` (보안상 secrets/ 바로 아래 단일 파일로 결정, DECISIONS L6 갱신)
- [ ] dashboard 시안 진입 (Claude Design, 사용자 직접 claude.ai/design)
- [ ] (선택) 본 워크트리들(`peaceful-gagarin-b7fda4`·`dazzling-roentgen-b550f7` 등) 폐기 검토 — 세션 #8·#9 main 직접 작업 후 사용 가치 낮음

## 세션 #8 분리 완료 ★

- [x] ~~**네이버 보조 채널 분리 작업**~~ ✅ 세션 #8 완료 (6 Phase). `D:\naver_blog\` 별도 프로젝트 셋업·push·dazzling-hermann 폐기·마스터 동기화. 네이버 작업은 본 TODO에서 모두 제거 (이후 D:\naver_blog\docs\TODO.md 참조)

## 세션 #6 잔존 (시점 의존)

- [ ] **알리 이미지·상세페이지 정책 조사** — Phase 5 진입 전 (현재 docs 명시 없음)
- [ ] **M2/M4/M5/M6 Phase 3~6 진척 시점 작업** — `docs/GOOGLE_AI_OPTIMIZATION.md` §6

## 세션 #6 SEO 정합 통합 후 잔존 (cross-project · 별도 세션 권장)

- [x] ~~**AutoBlog Hana Kim 잔존 5편 처리**~~ ✅ 세션 #7 완료. 본질 작업(author/publisher Organization 갱신 + 1인칭 재작성) 이미 완료 확인 + post 5 FAQ 구조 정상화·FAQPage Schema 추가 + content_text 재동기화 (AUTOBLOG_TODO TASK_024 갱신)
- [x] ~~**Scaled Content Abuse 모듈 Step 1 dry-run**~~ ✅ 세션 #7 완료. AutoBlog `src/content/similarity.py` (4-gram word Jaccard) + tistory_revival `keyword_cluster.py` (어절+바이그램) + seo_gate hook + 회귀 13/13 PASS. Step 2 (fail 게이트 승격) 별도 세션 (1~2주 운영 데이터 후)
- [ ] **혼살림 M2 Person Schema + about 페이지 운영자 정보** — Phase 4 진입 시 (E-E-A-T author 강화)
  - 세션 #7 사전 결정 완료: 필명 "혼살다" / 운영 철학 / 전문성 영역 / 사진 없음 (DECISIONS M2-1~M2-7)
  - 코드 작업: `_macros/person.html` 매크로 작성 (FRONTEND §4-5-bis 명세) + `about.html` 본문 적용 (FRONTEND §4-5 초안)
  - 작업 시점: Phase 3 디자인 후 Phase 4 진입 직전

## Phase 1: 인프라 — 남음

- [ ] AliExpress App Key/Secret 발급 — Phase 5 시점 (2026-11 이후)
- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록** — Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check — Phase 2 안정 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후

## Phase 2: 핵심 시스템 — 남음

> 완료 항목은 STATE.md "Phase 2 핵심 모듈 18개" + "회귀 342/342" + "CLI 10/11" 행 참조.

- [ ] CLI dashboard 명령 — Phase 3 디자인 후 본격
- [ ] `collector.coupang` (쿠팡 가입 후·Phase 4)
- [ ] `builder.renderer/pages/sitemap/assets` (Jinja2 + DESIGN 시안)
- [ ] `dashboard.render/approve` (디자인 시안 Phase 3 의존)
- [ ] `python -m honsalim build --full` 성공 (Phase 2 종착)

## Phase 3: 디자인·콘텐츠 (2026-07)

- [ ] Claude Design 시안 3~5종 (사용자 claude.ai/design)
- [ ] 시안 1개 선정 + DESIGN.md 토큰 미세 조정
- [ ] Jinja2 템플릿 5종 + partials 18종 + Critical CSS + Pretendard preload
- [ ] AI 이미지 생성 (페르소나별 2~3장, Imagen 4 Fast)
- [ ] 시즌 신학기·홈오피스 시나리오 5편 작성 (#5~#10)
- [ ] 진실성 게이트 통과 + 사용자 1클릭 승인 + 시범 1편 로컬 미리보기·배포

## Phase 4: 첫 출시 (2026-07 말~08)

- [ ] honsalim.com 커스텀 도메인 연결
- [ ] GSC DNS TXT 인증 + 사이트맵 + 네이버 서치어드바이저 + Daum 웹마스터
- [ ] IndexNow `<key>.txt` 배포 + Cloudflare Web Analytics 활성
- [ ] about.html · 개인정보처리방침 게재
- [ ] 첫 5~10편 정식 배포

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 GitHub Pages (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
