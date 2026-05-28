# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션)

- [ ] **CI lint #15 Black format check fail fix** — GitHub Actions에서 raw log 캡쳐 → Claude fix → push (5~10분, 우선순위 낮음)
- [ ] **docs/SUMMARY.md / REVIEW_QUESTIONS.md 정독** — Phase 2 후반 본격 진입 게이트 (2026-07 이전까지)

## 세션 #5 완료 항목 (참고)
- [x] 알리 Tracking ID + `ali.env` (환경 변수 로드 검증 완료)
- [x] 핵심 결정 5건 (K1·K2·K3·K4·K5) DECISIONS 등재
- [x] `pip install -e .[dev]` — 회귀 333 PASS, `honsalim` entry point 작동
- [x] push origin main — 11 commits 전부 동기
- [x] Workers `go_gateway.js` + tracker.report + 회귀 헬퍼 + doctor §13
- [x] CI build-and-deploy 정상화 (renderer skip 동작)

## Phase 1: 인프라 — 남음 ⏳

- [x] ~~(완료)~~ AliExpress Tracking ID 발급 + `ali.env` 작성 (세션 #5)
- [ ] AliExpress App Key/Secret 발급 — Phase 5 시점 (2026-11 이후)
- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록** — Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check — Phase 2 안정 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후

## Phase 2: 핵심 시스템 — 남음 ⏳

> 완료 항목은 STATE.md "Phase 2 핵심 모듈 16개" + "회귀 295/295" + "CLI 8/11" 행 참조.

### 안전 진척 (검토 의존 작음)
- [x] ~~CLI deploy 명령~~ (세션 #5, dry_run=True 기본, deployer 3단계 호출)
- [x] ~~CLI build 명령 (manifest stub)~~ (세션 #5, renderer 미작성 — manifest 로드·요약만)
- [ ] CLI dashboard 명령 — Phase 3 디자인 후 본격

### 검토 의존 큼 (사용자 결정 후)
- [ ] `collector.coupang` (쿠팡 가입 후·Phase 4)
- [x] ~~`builder.manifest` 형태 결정~~ (K1 [확정] JSON 파일)
- [ ] `builder.renderer/pages/sitemap/assets` (Jinja2 + DESIGN 시안)
- [ ] `dashboard.render/approve` (디자인 시안 Phase 3 의존)
- [x] ~~`tracker.report`~~ (세션 #5 데이터 집계 함수 완료, HTML 렌더는 dashboard 통합 시 jinja2 — `render_html_stub`만)
- [x] ~~Workers `go_gateway.js`~~ (세션 #5 BACKEND §5 명세 충실 구현 — wrangler deploy는 사용자 명시 승인 후)
- [ ] `python -m honsalim build --full` 성공 (Phase 2 종착)

## Phase 3: 디자인·콘텐츠 (2026-07)

- [ ] Claude Design 시안 3~5종 (사용자 claude.ai/design)
- [ ] 시안 1개 선정 + DESIGN.md 토큰 미세 조정
- [ ] Jinja2 템플릿 5종 + partials 18종 + Critical CSS + Pretendard preload
- [ ] 사용자 직접 사진 (페르소나별 2~3장)
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
