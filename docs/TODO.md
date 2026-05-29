# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션)

> 공개 사이트 5종 시안·정식 빌더 renderer 완료 (2026-05-30, DECISIONS G4 / STATE) — 상세는 그쪽 참조.

- [ ] **빌더 잔여**: 상세글(article) 렌더(게시 콘텐츠 + body_html↔템플릿 매핑) · Pretendard self-host · critical CSS · feed.xml · robots.txt (FRONTEND §7·§9). [SEO 메타·JSON-LD ✅ 2026-05-30: OG·Breadcrumb·WebSite·Org]
- [ ] Scaled Content Abuse Step 2 (fail 게이트 승격) — 1~2주 운영 데이터 후 별도 세션

## 알리 통합 (D9 — 쿠팡 게이팅으로 앞당김, 2026-05-30)

- [x] ~~**App Key/Secret 발급 + 라이브 검증**~~ ✅ 2026-05-30 — 개발자 승인→앱 생성→키 ali.env 저장→실호출 성공(밀리초·매핑 확정). 수집기 production-ready (D9)
- [ ] **상품 수집 CLI** (`collect-products --keywords ...`) → product.query 결과를 **products 테이블에 적재** (next, 핵심)
- [ ] **상품↔시나리오 연결 → 첫 글 enrich·발행** — enrich --no-dry-run(API 비용·1클릭 승인) → 4게이트 → 발행
- [ ] **honsalim.com 사이트 whitelist** — "ali" 오탐 → affiliates@service.alibaba.com 문의·승인 대기 (사용자)
- [ ] **main-protect 브랜치 보호 재활성화** (공개 전환으로 꺼짐, Settings→Rules) + codeql-action 버전업

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
