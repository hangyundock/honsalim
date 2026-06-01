# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션 #20) — #19 갱신 · DeepSeek 전환·디자인·관련성·판매량 선정·신규 2카테고리 완료 → 검토·승인·배포 (상세 EVENTS #19)

> #19: 본문생성 Sonnet→**DeepSeek v4-pro**(OpenRouter 라우팅·파서견고화·SEO지시문 강화) + 카테고리 디자인 마무리(행정렬·정렬/필터 JS·커서) + 관련성 `require_all`(타입+대상)+재수집 정합화 + **추천6선 판매량 기준 선정**(만족도80%하한·항상6개·정직표기) + 신규 2카테고리. 회귀 623. 카테고리 4개 전부 draft. **전부 로컬·미배포.**

- [x] ~~카테고리 디자인 마무리 · DeepSeek 전환 · 출력 안정화 · 관련성 require_all · 판매량 기준 추천 6선 · 신규 2카테고리~~ ✅ #19
- [ ] **★카테고리 4개 검토 → 승인 → 배포**: 노트북거치대·모니터암·모니터받침대·컴퓨터책상(draft·6선). `approve-category <slug>` → `build --full` → honsalim.com (방법A, **사용자 승인**).
- [ ] **노트북거치대 '전화' 제외어 결정**(사용자): 1위 픽이 "전화 태블릿 겸용" 베스트셀러. 노트북 전용만 원하면 `category_sources.yml` laptop-stand exclude에 "전화" 추가 후 재수집·재빌드.
- [ ] **office-chair 콘텐츠 생성**: 제품 0 — `collect-category office-chair` → `build-category office-chair`.
- [ ] **메인 미커밋 DeepSeek 임시본 정리**: 메인(D:\affiliate_hub) AutoBlog #99 미커밋 `claude_client.py` → 이 워크트리 정식본이 supersede. 머지 전 되돌리기.
- [ ] (이월) **★/go/ 제휴 링크 작동**(D1 slug_map·go_gateway, 수익직결) · 알리 whitelist 답변 · main-protect 재활성화.
- 참고: ★다음 워크트리 **DB 재생성 필요**(gitignore) — 4개 카테고리 `collect-category` --no-dry-run(판매량 채움) + `build-category` --no-dry-run(API ~$1). 미리보기=`build --preview`·공개=`build --full`. 강력새로고침/시크릿창.

## 알리 통합 (D9)

- [x] ~~App Key/Secret·라이브검증(#11)·collect-products·C-1·enrich·4게이트(#12)·promote·상세글 렌더·라이브 게시(#13)~~ ✅
- [x] ~~honsalim.com whitelist 제출~~ ✅ #13 — **이메일 + 포털 XFeedback(스크린샷 증거, "To do") 제출, 답변 대기**. 사이트등록폼은 'ali' 자동검증으로 Submit 불가 → 사람 화이트리스트만 길.
- [ ] 알리 답변 후속 (승인 시 /go/ 동작 + 수익 추적 활성)

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
