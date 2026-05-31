# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션 #19) — #18 갱신 · 승인 게이트·doctor·디자인 디버깅 완료 → 디자인 마무리 + 배포 (DECISIONS O21~O22)

> #18: 운영자 승인 게이트(`approve-category` CLI·`category_state`·build-category→draft·renderer published 필터·대시보드 승인대기) + doctor 진입점 64 + ★카테고리 디자인 대거 디버깅(backdrop-filter 흐림 제거·색#111·폭1080·14px·FAQ Q/A·장점단점·마크다운). 회귀 590. DB 이 워크트리 재생성됨(draft). **전부 로컬·미배포.**

- [x] ~~운영자 1클릭 승인 게이트 · doctor 보강 · 카테고리 디자인 디버깅(흐림·색·폭·폰트·FAQ·장점단점·14px)~~ ✅ #18
- [ ] **★카테고리 페이지 추가 디자인 수정 (사용자 — 연속 작업)**: #18 디자인 대거 수정했으나 사용자가 "이 페이지 수정할 부분 더 있다". 다음 세션 이어서. (DB 재생성 후 `build --preview`로 desk/monitor 미리보기 확인하며)
- [ ] **★#18 2순위 배포 완료** (승인 후): `approve-category desk`·`monitor-stand`(draft→published) → `build --full`(build/site, published만) → honsalim.com (방법A, **사용자 승인**).
- [ ] **나머지 카테고리**: 의자 `build-category office-chair`(현재 카탈로그만) · 모니터암 등 신규(category_sources·seo_keywords·seed 등록 후 2명령).
- [ ] (이월) **★/go/ 제휴 링크 작동**(D1 slug_map·go_gateway, 수익직결) · 알리 whitelist 답변 · main-protect 재활성화.
- 참고: ★다음 워크트리는 **DB 재생성 필요**(gitignore) — `collect-category desk`·`monitor-stand` + `build-category` 각 `--no-dry-run`(API ~$0.6). 미리보기=`build --preview`(draft포함)·공개=`build --full`. 미리보기 시 강력새로고침/시크릿창.

## 알리 통합 (D9)

- [x] ~~App Key/Secret·라이브검증(#11)·collect-products·C-1·enrich·4게이트(#12)·promote·상세글 렌더·라이브 게시(#13)~~ ✅
- [x] ~~honsalim.com whitelist 제출~~ ✅ #13 — **이메일 + 포털 XFeedback(스크린샷 증거, "To do") 제출, 답변 대기**. 사이트등록폼은 'ali' 자동검증으로 Submit 불가 → 사람 화이트리스트만 길.
- [ ] 알리 답변 후속 (승인 시 /go/ 동작 + 수익 추적 활성)

## 세션 #6 잔존 (시점 의존)

- [ ] **알리 이미지·상세페이지 정책 조사** — Phase 5 진입 전 (현재 docs 명시 없음)
- [ ] **M2/M4/M5/M6 Phase 3~6 진척 시점 작업** — `docs/GOOGLE_AI_OPTIMIZATION.md` §6

## 세션 #6 SEO 정합 통합 후 잔존 (cross-project · 별도 세션 권장)

- [ ] **혼살림 M2 Person Schema + about 페이지 운영자 정보** — Phase 4 진입 시 (E-E-A-T author 강화)
  - 세션 #7 사전 결정 완료: 필명 "혼살다" / 운영 철학 / 전문성 영역 / 사진 없음 (DECISIONS M2-1~M2-7)
  - 코드 작업: `_macros/person.html` 매크로 작성 (FRONTEND §4-5-bis 명세) + `about.html` 본문 적용 (FRONTEND §4-5 초안)
  - 작업 시점: Phase 3 디자인 후 Phase 4 진입 직전

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
