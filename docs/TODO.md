# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #26 — (상세 EVENTS #25)

- [x] ~~쿠팡 채널 통합 부트스트랩(`collector.coupang`+CLI·이미지 그리드·채널인식 고지·알리 가드·`/go/`)·모니터암 15개 라이브검증·회귀 710~~ ✅ #25
- [ ] **1. ★광고 배치 구현 (#25 합의·DECISIONS U4)**: **메인 첫 화면 쿠팡 배너(주인 원안)** + 카테고리 **결정지점(추천·비교 직후)** 배치. 근거=위치>형태. **효과=쿠팡 수익 리포트**(별도 클릭 측정 시스템 ❌ 과잉·[[assist-not-overstep]]). ★구현 전 "이 코드 이렇게 바꾼다" 먼저 짧게 보고.
- [ ] **2. 쿠팡 상품 추가 (수동)**: 다른 카테고리 = 주인이 '블로그용 HTML' 붙여주면 `coupang_products.yml`+`collect-coupang`. ⚠브라우저 자동화 정책 차단(재시도 금지·U3). 쿠팡 API는 **판매금액 15만원→최종승인** 후(U2, 내 수익금 아님). ⚠본인·가족 구매 금지.
- [ ] **3. ★성장이 진짜 병목 (정직하게·희망고문 금지)**([[growth-first-priority]] · DECISIONS T2):
  - **Tier 0 (지금·진행중)**: 사이트 SEO 품질 강화 — ①"데이터 기반 비교" 포지셔닝(알리 판매량=Information Gain) ②방법론·저자 E-E-A-T 페이지 ③토픽 클러스터+내부링크 ④소수 품목 주인 실경험. (2025.12 어필리에이트 패널티군 회피)
  - **Tier 1 (병렬·승인 1~4주)**: Pinterest 자동 핀(개인정보처리방침+Standard API 승인→핀→리뷰페이지·첫머리 고지)
  - **Tier 2/3**: Threads 공짜 보조 → 쇼츠(차별화)·네이버블로그 연계
  - 공통: 소셜 게시물 첫머리 고지 자동삽입·정식계정·측정→더블다운. ❌양산/버너(연좌·도메인플래그). 새 사이트 6~12개월 인내.
- [ ] (선택) `docs/CATEGORIES.md` · D1 클릭로깅 복원 · main-protect status check · Chrome lookalike(관찰).
- 참고: **DB gitignore→재생성**(`register-categories --all --no-dry-run --auto-publish`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. ★메인=#22 동기화+DB재생성 완료(잔재 `stash@{0}`).

> 알리 통합(App Key·collect·enrich·게이트·promote·게시·honsallim 채널·Tracking ID·247 deeplink·/go/) = #11~#22 완료 ✅ (상세 STATE/EVENTS).

## 시점 의존 잔존 (세션 #6~7)

- [ ] 알리 이미지·상세페이지 정책 조사 (Phase 5 전) · M2/M4/M5/M6 (`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6)
- [ ] **혼살림 M2 Person Schema + about 운영자 정보** (Phase 4, E-E-A-T) — 사전결정 완료(필명 "혼살다"·사진없음, DECISIONS M2). 코드=`_macros/person.html`+`about.html`(FRONTEND §4-5)

## Phase 1: 인프라 — 남음

- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록** — Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check — Phase 2 안정 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후

## Phase 2: 핵심 시스템 — 남음

> 완료 항목은 STATE.md "Phase 2 핵심 모듈 18개" + "회귀 342/342" + "CLI 10/11" 행 참조.

- [x] ~~CLI dashboard 명령~~ ✅ 세션 #9 완료 (G3 결정으로 Claude Design 미사용, stub HTML)
- [ ] `collector.coupang` (쿠팡 가입 후·Phase 4)
- [ ] `builder.renderer/pages/sitemap/assets` (Jinja2 + DESIGN 시안)
- [ ] `dashboard.render/approve` (디자인 시안 Phase 3 의존)
- [ ] `python -m honsalim build --full` 성공 (Phase 2 종착)

## Phase 3: 디자인·콘텐츠 (2026-07)

- [ ] Claude Design 시안 3~5종 (사용자 claude.ai/design)
- [ ] 시안 1개 선정 + DESIGN.md 토큰 미세 조정
- [x] ~~Jinja2 템플릿 5종 + partials~~ ✅ 2026-05-30 (base·home·scenario_list·article·persona_hub·about + header/footer + _macros/components). 잔여: Critical CSS·Pretendard preload·JSON-LD 매크로 (정식 빌더 시)
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
