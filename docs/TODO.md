# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션)

- [ ] **알리 심사 결과 확인** (이메일, 2026-05-29~06-01)
- [ ] **docs/SUMMARY.md / REVIEW_QUESTIONS.md 정독** — Phase 2 후반 본격 진입 게이트
- [ ] 핵심 결정 4건 의견 수렴
  - ARCH §4-2 모듈 분리: pyproject.toml `honsalim` 패키지 가정 vs `src/` flat layout 모순
  - DB §10 manifest를 JSON 파일로 (테이블 아님)
  - SCENARIOS §4 초기 10편 시나리오 우선순위
  - POLICY §6-1 외부 단축 URL 차단 목록 추가/제외 검토
- [ ] `pip install -e .[dev]` 사용자 명시 승인 (jinja2·markdown·pytest 등)
- [ ] push origin main 사용자 승인 (현재 6 commit ahead)

## Phase 1: 인프라 — 남음 ⏳

- [ ] AliExpress 승인 후 API 키 발급 + `ali.env` 작성
- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록** — Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check — Phase 2 안정 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후

## Phase 2: 핵심 시스템 — 남음 ⏳

> 완료 항목은 STATE.md "Phase 2 핵심 모듈 12개" + "회귀 225/225" + "CLI 6/11" 행 참조.

### 안전 진척 (검토 의존 작음)
- [ ] CLI 나머지 5 명령 (collect·unapprove·dashboard·build·deploy) — Phase 2 후속
- [ ] enricher.claude_client 실호출 에러 처리·재시도 (BACKEND §3-5)
- [ ] DECISIONS.md 갱신 — 세션 #4 새 [확정] 사실 등록

### 검토 의존 큼 (사용자 결정 후)
- [ ] `collector.coupang` (쿠팡 가입 후·Phase 4)
- [ ] `builder.manifest` 증분 빌드 (ARCH §7·DB §10)
- [ ] `builder.renderer/pages/sitemap/assets` (Jinja2 + DESIGN 시안)
- [ ] `dashboard.render/approve` (디자인 시안 Phase 3 의존)
- [ ] `deployer.git_push/wrangler/verify`
- [ ] `tracker.d1_aggregator` + Workers `go_gateway.js`
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
