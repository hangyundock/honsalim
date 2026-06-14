# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #30 — (상세 EVENTS #29) · 라이브 테스트가 적발한 2대 문제 최우선

- [ ] **★A. 키워드 경로 알리 검색 근본수정 (최우선)**: `_gather_keyword_candidates`가 `ali.query_products(한글 키워드)` → "컴퓨터의자"에 폰케이스·티셔츠·가방 등 무관상품만 옴(가드가 다 거름→글 thin·쿠팡만). **키워드→카테고리 매핑 → 그 카테고리의 영어 tier 검색어**(`category_sources.yml` tiers.q "office chair" 등)로 알리 검색하게 수정 → 하이브리드에 알리 데이터 복원. (카테고리 경로는 이미 영어라 정상=라이브 5카테고리 멀쩡)
- [ ] **★B. 대시보드 진행/완료 표시**: 생성 1~2분 무표시 → 끝난지 모름(주인 반복지적). 작업 시작·진행중·완료 신호(상태 라벨/타이틀/버튼 비활성 등) 추가.
- [ ] **A·B 후 첫 라이브 글**: 게이밍의자(#3·쿠팡 첨부됨) `✨ 글 생성` → 제대로된 하이브리드(쿠팡+알리) → 미리보기 → 승인 → 발행. thin draft #3(컴퓨터의자) 반려.
- [ ] **DECISIONS/CLAUDE.md B-i 기록**: auto_mode 토글(기본 OFF)·fail-closed 자동승인·발행후 안전망·E7 보정(구글정책 정정=AI/자동 아닌 **저가치 양산**만 페널티). critical-review 지적 문서 정합.
- [ ] **B 켜기 (주인 결정)**: `auto_mode` ON + `run_auto_cycle.ps1` schtask 등록(C13 주인 통제). 그러면 대기키워드(+쿠팡 첨부분)로 매일 자동 생성·승인·발행·사후모니터.
- (이월) PartC 키워드 틈점수 · `mini-dehumidifier` 점검 · off-target 씨앗 curation · 쿠팡 본격(15만원 후) · 멀티채널(S1) · 성장 Tier0([[growth-first-priority]]·트래픽이 진짜 병목·6~12개월 인내).
- 참고: 워크트리=`PYTHONPATH=src python -m cli` · DB gitignore→재생성(`db migrate`+`db seed`+`register-categories --all --no-dry-run`). 발행/배포=main 체크아웃. **main 직접머지=`git push origin HEAD:main`(이미 allow·gh 불필요)**.

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
