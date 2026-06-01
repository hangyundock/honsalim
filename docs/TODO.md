# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션 #21) — #20 갱신 · 도메인 이전·홈 재편·콘텐츠 전략·도마 착수 완료 → 나머지 살림 카테고리 정밀 구축 + 배포 (상세 EVENTS #20 / DECISIONS Q)

> ★주인 원칙: **카테고리 신중·정밀·치밀**(잘못 짜면 페이지 전체 변경·Q5). 키워드는 **네이버 실측만**(상상 금지·Q3) — "1인 ○○" 빈약(1인냄비 350) → 대표어+보조키워드. 가전=쿠팡·비가전=알리(Q4).

- [x] ~~알리 'ali' 도메인 차단 해결(honsallim.com 구매·코드 10곳 이전) · 홈 카테고리화·실이미지·시즌 컬러타일 · 콘텐츠 전략·네이버 실측 · 도마 수집·관련성 검증(45→25)~~ ✅ #20
- [ ] **★나머지 2 살림 카테고리 수집·정제**: `collect-category drying-rack --no-dry-run` · `collect-category mini-dehumidifier --no-dry-run` → 제품명 관련성 검증 → 오염 시 `category_sources.yml` 제외어 보강·재수집(도마 루프). (행거·수납·욕실선반은 후속 확장 후보)
- [ ] **seo_keywords.yml 등록**: 도마(스텐도마·나무도마)·빨래건조대(접이식·미니)·미니제습기(원룸제습기·소형) — 네이버 실측 대표+보조.
- [ ] **build-category ×3**(도마·빨래건조대·미니제습기): DeepSeek 글 + Imagen 개념이미지(~$1.5-3)→draft. + **히어로 전용 배너 이미지**(카드 중복 해소·주인 지시).
- [ ] **build --preview → 홈 확인(카테고리 7개) → `approve-category` → honsallim.com 연결·배포·301**(honsalim→honsallim).
- [ ] **알리 honsallim.com 채널 등록**(사이트 배포 후 소유권 인증) + **쿠팡 가입**(가전용·Q4).
- [ ] (이월) **★/go/ 링크 작동**(D1 slug_map·go_gateway) · main-protect 재활성화 · office-chair 생성 · 노트북'전화'제외어.
- 참고: 미리보기=`PYTHONPATH=src python -m cli build --preview` + `localhost:8791`(.claude/launch.json). 공개=`build --full`. 워크트리 실행=`PYTHONPATH=src python -m cli`. DB(determined-bouman 복사본+도마수집)gitignore → 새 워크트리 `db migrate`+`db seed`+`collect-category` 재생성.

## 알리 통합 (D9)

- [x] ~~App Key/Secret·라이브검증(#11)·collect-products·C-1·enrich·4게이트(#12)·promote·상세글 렌더·라이브 게시(#13)~~ ✅
- [x] ~~honsalim.com whitelist~~ **거부 확정 #20** — XFeedback "Done", 'ali' 문자열 영구 불가 → **honsallim.com(겹ㄹ)으로 도메인 이전**(알리 폼 'ali' 통과 라이브 확인).
- [ ] **honsallim.com 알리 채널 등록**(사이트 배포 후 소유권 인증) → 승인 시 /go/ 동작 + 수익 추적 활성

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
