# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #29 — (상세 EVENTS #28)

- [ ] **★0. 라이브 테스트 (최우선)**: 대시보드 재시작 → `🛒 쿠팡 배너→글 생성`(키워드 + 쿠팡 공식배너 `<a><img>`) → 미리보기로 **쿠팡(이미지) + 알리(판매량 데이터) 결합** 확인 (DeepSeek 비용·품질 1회). 알리 단독 빠른 글은 `✨ 글 생성`.
- [ ] **★PartC 키워드 '틈 점수'**: naver_blog `keyword_scorer` 차용(검색량/문서수/경쟁도→저경쟁 롱테일 우선·신규 사이트 구글 랭킹). 단 네이버 신호=구글 근사치(정직 보정).
- [ ] **PartD 자동 발행 ON**: 스케줄러(구현됨·기본 OFF) 켜서 승인된 글 매일 자동 발행(E7 준수=승인된 것만).
- [ ] **off-target 씨앗 curation**: 책·모니터 거치대(편집 판단)·받침대(발받침 모호) exclude_terms 보강.
- [ ] **0. `mini-dehumidifier` 점검**: 추천 1개(<2)로 가드레일 자가복원→라이브 비공개. 추천 풀 부족 원인 확인 후 복원/보강 결정.
- [ ] **1. ★★쿠팡 본격 (주인 명시)**: ①가입 완료 ②`/reviews/` 승인용 페이지 활용 ③승인 후 **`collector.coupang` 구현**으로 쿠팡 상품 수집. 쿠팡=메인(§6). ⚠본인·가족 구매 금지.
- [ ] **2. 멀티채널 배치 구현 (DECISIONS S1·S2)**: 방향=C안(채널별 최선 추천+정성 기준) 확정. 게이팅=`collector.coupang` + 1~2주 트래픽 데이터 후 최종 배치. 가격비교형(A안) 금지.
- [ ] **3. ★성장 = 무인 마케팅 로드맵**([[growth-first-priority]] · 방향 [확정 #24 DECISIONS T1·T2]):
  - **Tier 0 (지금)**: SEO 품질 — "데이터 기반 비교" 포지셔닝(알리 판매량=Information Gain)·E-E-A-T·토픽 클러스터·소수 품목 주인 실경험.
  - **Tier 1 (병렬·승인 1~4주)**: Pinterest 자동 핀(개인정보처리방침+Standard API 승인→리뷰페이지·첫머리 고지). Tier2/3=Threads→쇼츠/네이버연계.
  - 공통: 소셜 첫머리 고지 자동삽입·정식계정·측정→더블다운. ❌양산/버너. 새 사이트 6~12개월 인내.
- [ ] (선택) `docs/CATEGORIES.md` · D1 클릭로깅 복원 · main-protect status check · Chrome lookalike(관찰).
- 참고: **DB gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. 발행/배포·라이브 테스트는 **main 체크아웃**(C13 수동).

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
