# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #24 — (상세 EVENTS #23)

- [x] ~~무인 스케줄러 A안(refresh-cycle: 새로고침→자가복원→빌드→변경분 배포) · 모니터링 대시보드(무인사이클+공개카테고리건강+경고배너+바탕화면 아이콘) · Claude 예약작업 등록(매일 11:00 KST) · 메인 체크아웃 정비(stash·#22 ff·DB재생성 6공개/2보류)~~ ✅ #23
- [ ] **0. #23 머지 → 스케줄러 가동 확인**: #23이 origin/main에 올라야 예약작업이 refresh-cycle 가동. 머지 후 `refresh-cycle --dry-run`(또는 예약작업 Run now) 1회 점검. **첫 배포 시 보류 2개(laptop-stand·drying-rack) 라이브에서 내려감(fail-closed) — 검토 후 결정.**
- [ ] **1. ★★쿠팡 본격 (주인 명시)**: ①가입 완료 ②쿠팡 링크 생성 ③**승인용 데모 페이지(쿠팡 고지+링크) honsallim.com 배포→스샷 업로드** ④승인 후 **`collector.coupang` 구현**으로 쿠팡 상품 수집. 쿠팡=메인(§6). ⚠본인·가족 구매 금지.
- [x] ~~**2. 알리+쿠팡 페이지 배치 설계**~~ → **방향 합의(C안) [확정 #24 · DECISIONS S1·S2]**: "채널별 최선 추천 + 정성 기준(빠른배송 쿠팡/최저가 알리) + 가격 위임(숫자 박제 금지·갱신일)". 가격비교형(A안)=표시광고법 위험으로 탈락. **구현은 `collector.coupang`(쿠팡 상품 0) + 1~2주 트래픽 데이터 후 확정**.
- [ ] **3. ★성장 = 무인 마케팅 로드맵**([[growth-first-priority]] · 방향 [확정 #24 DECISIONS T1·T2]):
  - **Tier 0 ✅ 라이브(#24)**: ①데이터 기반 비교 포지셔닝(판매량=Information Gain·데이터 요약 박스) ②방법론·저자 E-E-A-T 페이지 `/method/` ③토픽 클러스터(홈오피스 필러 `/home-office/` + 허브↔스포크 내부링크). **④핸즈온 실경험=미채택**(제품 미소유+본인구매금지 → '데이터 기반 비교' 레인으로만 경쟁·DECISIONS T2). (2025.12 어필리 패널티군 회피)
  - **Tier 1 (병렬·승인 1~4주)**: Pinterest 자동 핀(개인정보처리방침+Standard API 승인→핀→리뷰페이지·첫머리 고지)
  - **Tier 2/3**: Threads 공짜 보조 → 쇼츠(차별화)·네이버블로그 연계
  - 공통: 소셜 게시물 첫머리 고지 자동삽입·정식계정·측정→더블다운. ❌양산/버너(연좌·도메인플래그). 새 사이트 6~12개월 인내.
- [ ] (선택) `docs/CATEGORIES.md` · D1 클릭로깅 복원 · main-protect status check · Chrome lookalike(관찰).
- 참고: **DB gitignore→재생성**(`register-categories --all --no-dry-run --auto-publish`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. ★메인=#22 동기화+DB재생성 완료(잔재 `stash@{0}`).

## 알리 통합 (D9)

- [x] ~~App Key/Secret·라이브검증(#11)·collect-products·C-1·enrich·4게이트(#12)·promote·상세글 렌더·라이브 게시(#13)~~ ✅
- [x] ~~honsalim.com whitelist('ali' 자동검증 Submit 차단)~~ → **honsallim.com 채널 등록 완료** ✅ #21 (겹ㄹ 도메인으로 'ali' 차단 돌파, Portals 나의웹사이트·content>vertical sites·별도 승인 게이트 없음)
- [x] ~~honsallim 채널 **Tracking ID(`ALI_TRACKING_ID=honsallim`) → ali.env 연결 + 개별 deeplink 247개** + /go/ 수익경로(Pages Function·302 알리)~~ ✅ #22

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
