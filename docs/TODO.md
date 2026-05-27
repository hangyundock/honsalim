# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료는 즉시 제거. 이력은 EVENTS.md.
> Cap 5KB.

## ★ 시급 (다음 세션)

- [ ] **docs/SUMMARY.md 정독** (1페이지 요약 + 결정 25개 매트릭스 + 검토 체크리스트) — 12 문서 검토 게이트
- [ ] 12개 설계 문서 사용자 검토 (PLAN·ARCH·DB·SCENARIOS·DESIGN·FRONTEND·BACKEND·POLICY·OPS·BACKUP·MAINTENANCE·SCHEDULE) — SUMMARY로 우선, 의심 부분만 원본
- [ ] 핵심 결정 포인트 사용자 의견 수렴
  - ARCH §4-2 모듈 28개 분리 적정성
  - DB §10 manifest를 JSON 파일로 (테이블 아님)
  - SCENARIOS §4 초기 10편 시나리오 우선순위
  - POLICY §6-1 외부 단축 URL 차단 목록 추가/제외 검토
- [ ] Phase 1 진입 사용자 명시 OK

## Phase 1: 인프라 (2026-06)

- [ ] GitHub 공개 저장소 생성 (이름 후보: honsalim 또는 affiliate_hub) + **Secret Scanning 활성·main 브랜치 보호·CodeQL 활성** (DECISIONS I1·I6)
- [ ] pre-commit hook 설정 (gitleaks 또는 detect-secrets) — `.pre-commit-config.yaml` **사전 작성 완료** (옵션 A·B 중 선택, Phase 1 사용자 결정) (DECISIONS I1)
- [ ] 외부 계정 5종 2FA 활성 (GitHub·Cloudflare·Anthropic·쿠팡·Registrar) (DECISIONS I3)
- [ ] 로컬 D 드라이브 BitLocker 활성 (DECISIONS I5)
- [ ] **윈도우 작업 스케줄러 등록**: 매일 11:00 KST `python -m honsalim scheduler-publish` (DECISIONS C7)
- [ ] 도메인 honsalim.com 가용성 재확인 + 결제 (Cloudflare Registrar)
- [ ] Cloudflare 계정 + Pages 프로젝트 + R2 버킷 + D1 DB + Workers 라우트
- [ ] `D:\secrets\affiliate_hub\` 폴더 생성 + 자격증명 .env 5개
- [ ] `.claude/settings.json` deny 룰 설정 (POLICY §10-2) — **사전 작성 완료** (AutoBlog 패턴 확장 deny 24·allow 14, Phase 1 사용자 검토)
- [ ] 쿠팡 파트너스 가입 + Open API 키 발급 (승인 1~3일)
- [ ] Anthropic API 키 검증 (보유)
- [ ] python -m honsalim doctor 전체 OK
- [ ] STATE.md "자격증명 만료" 표 발급일·만료일 기재

## Phase 2: 핵심 시스템 (2026-06~07)

- [ ] pyproject.toml + 의존성 (anthropic·jinja2·requests·pillow 등)
- [ ] common 모듈 (config·logging·db·grading)
- [ ] DB 마이그레이션 001 (스키마 + personas·scenarios seed) — **사전 작성 완료**: `sql/migrations/001_initial_schema.sql`·`sql/seeds/001_personas_scenarios.sql`. Phase 2에서 검토 후 `src/common/migrations/`로 이동·적용
- [ ] collector.coupang
- [ ] enricher.claude_client + prompt_templates/*.md
- [ ] validator 4모듈 (truth·schema·disclosure·links) — 회귀 테스트 30+ 케이스
- [ ] writer.state_machine
- [ ] builder (manifest·renderer·pages·sitemap·assets)
- [ ] dashboard.render·approve
- [ ] deployer (git_push·wrangler·verify)
- [ ] tracker.d1_aggregator + Workers go_gateway.js
- [ ] GitHub Actions workflows (build.yml·lint.yml)
- [ ] python -m honsalim build --full 성공

## Phase 3: 디자인·콘텐츠 (2026-07)

- [ ] Claude Design 시안 3~5종 생성 (사용자 직접 claude.ai/design)
- [ ] 시안 1개 선정 + docs/design_drafts/CHOICE.md 기록
- [ ] DESIGN.md 토큰 미세 조정 (시안 결과 반영)
- [ ] Jinja2 템플릿 5종 + partials 18종 구현
- [ ] Critical CSS + Pretendard preload
- [ ] 사용자 직접 사진 촬영 (페르소나·상품) — 페르소나별 2~3장
- [ ] 시즌 신학기·홈오피스 시나리오 우선 5편 작성 (#5~#10)
- [ ] 진실성 게이트 통과 + 사용자 1클릭 승인
- [ ] 시범 1편 로컬 미리보기 + 배포

## Phase 4: 첫 출시 (2026-07 말~08)

- [ ] honsalim.com 커스텀 도메인 연결
- [ ] GSC DNS TXT 인증 + 사이트맵 등록
- [ ] 네이버 서치어드바이저 등록 + 사이트맵 + RSS
- [ ] Daum 웹마스터도구 등록
- [ ] IndexNow 키 + <key>.txt 배포
- [ ] Cloudflare Web Analytics 활성
- [ ] about.html · 개인정보처리방침 게재
- [ ] 첫 5~10편 정식 배포

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 (GitHub Pages) 도입 (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
