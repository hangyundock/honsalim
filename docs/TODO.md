# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #23 — 개발 거의 끝. **최우선 = 성장(트래픽·수익)**([[growth-first-priority]] 메모리). '완성/유지보수'와 구분. (상세 EVENTS #22)

- [x] ~~살림3 카테고리 합치기 · 알리 개별 deeplink(honsallim 247개) · ★자율 게시 가드레일(E7→fail-closed) · 8개 자동공개 · ★라이브 배포 · ★측정 인프라 3종(Cloudflare·GSC·네이버) · ★/go/ 수익경로(Pages Function) · office-chair 오염 자동적발·collect prune 근본수정~~ ✅ #22
- [ ] **★성장 최우선(매 세션 선제 고민)**: ①측정 데이터 **1~2주 후 리뷰**(GSC·네이버·Cloudflare)→뜨는 키워드 더블다운·죽은 것 정리 ②토픽 집중(홈오피스 클러스터 심화: 키보드·마우스·데스크매트 등 인접) ③롱테일 검색어(본문·FAQ) ④양질 콘텐츠. 한국 제품추천 SEO 6~12개월 장기전.
- [ ] (완성·저위험·성장 아님) **무인 스케줄러 A안**: published 새로고침(가격·판매량)→가드레일 monitor 자가복원→build→변경 시 배포. ★메인 체크아웃(`D:\affiliate_hub`)이 origin/main #22 pull 필요(스케줄러 실행처).
- [ ] (선택) `docs/CATEGORIES.md` 전략 문서 · D1 클릭로깅 복원(Pages Function D1 바인딩) · 쿠팡(트래픽 후) · main-protect status check.
- [ ] (관찰) Chrome lookalike 경고(honsalim↔honsallim) — 301+시간 해소.
- 참고: ★코드·도메인·8카테고리·측정·/go/는 origin/main(#22) 배포 완료. **DB gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run --auto-publish`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. 공개=`build --full`(/go/ 함수도 재생성).

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
