# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션 #21) — 사용자 지시: **홈페이지 완성도 우선** → "제법 홈페이지 같다" 판단 시 제품 등록 (상세 EVENTS #20)

> #20: 카테고리 4개 라이브 배포 + 홈 카테고리우선 大리디자인(히어로 대표이미지·기획전 캐러셀·BEST·딜·테마·신뢰·구매가이드) + 버그 4종 근본수정(이미지 lazy오인·산출물청소·wrangler커밋메시지·HTML캐시) + 사업자표기/이메일. 회귀 632. **origin/main 배포 완료.**

- [x] ~~카테고리 4개 승인·배포 · '전화' 제외 · 이미지 누락 근본수정 · 산출물 청소 · wrangler/HTML캐시 fix · 홈 大리디자인 · 구매가이드 · 사업자표기·이메일~~ ✅ #20
- [ ] **★미충전 이미지 전부 채우기**(사용자 핵심): 이미지 자리 있는데 빈 곳 다 채워 "완성된 페이지" 모습으로. 확인된 곳=**`/about/` 우측 히어로 아트(about.html placeholder)**. 점검=scenario_card·persona·season `image_block(var(--wood))` 다수. 생성=`concept_image.generate_concept_image`(Imagen ~$0.02).
- [ ] **★제품 등록 준비 — 수익 카테고리 리스트화 + 순차 자동 적용**(사용자): 수익 카테고리(제품 선택) 선별→리스트→순차 자동 등록(`collect-category`→`build-category` 반복) 설계. 알리+쿠팡 둘 다 예정 → 구조부터.
- [ ] **★/go/ 제휴 링크 작동**(D1 slug_map·go_gateway 워커, 수익직결) — 무인 자동등록 전 필수 골격.
- [ ] **office-chair 콘텐츠 생성**: 제품 0 — `collect-category office-chair` → `build-category office-chair`.
- [ ] (이월) 알리 whitelist 답변 · 쿠팡 파트너스 재가입(Phase 4) · 무인 발행 스케줄러(매일 11시) · main-protect.
- 참고: ★홈 리디자인 코드는 **origin/main 배포 완료** — 다음 워크트리에 그대로 이어짐. **DB 재생성 필요**(gitignore) — 4개 카테고리 `collect-category`+`build-category` --no-dry-run(API ~$1). 워크트리 실행=`PYTHONPATH=src python -m cli`. 미리보기=`build --preview`·공개=`build --full`. CSS확인=Ctrl+Shift+R.
- **무인 자동등록 준비 체크리스트**(사용자 원칙): 내부링크 0 broken ✅ / 페이지 graceful ✅ / 법적페이지 ✅ / 배포 ✅ / **미충전 이미지** ⬜ / **/go/ 작동** ⬜ / **스케줄러** ⬜ → 골격 완성 후 제품 등록.

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
