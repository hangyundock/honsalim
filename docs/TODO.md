# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료는 즉시 제거. 이력은 EVENTS.md.
> Cap 5KB.

## ★ 시급 (다음 세션)

- [ ] **알리 심사 결과 확인** (이메일, 2026-05-29~06-01)
- [ ] **docs/SUMMARY.md / REVIEW_QUESTIONS.md 정독** — Phase 2 후반 본격 진입 게이트
- [ ] 핵심 결정 포인트 사용자 의견 수렴
  - ARCH §4-2 모듈 분리 적정성 + pyproject.toml `honsalim` 패키지 가정 vs `src/` flat layout 모순
  - DB §10 manifest를 JSON 파일로 (테이블 아님)
  - SCENARIOS §4 초기 10편 시나리오 우선순위
  - POLICY §6-1 외부 단축 URL 차단 목록 추가/제외 검토
- [ ] `pip install -e .[dev]` 사용자 명시 승인 (jinja2·markdown·pytest 등)

## Phase 1: 인프라 (2026-06) — 진행 상황

### 완료 ✅ (세부 EVENTS #2·#3 참조)
- 세션 #2: GitHub(보안 6종·2FA) · Cloudflare(계정·2FA·도메인 결제·Pages·R2·D1·API Token) · Anthropic 키 · `secrets/cloudflare.env`·`claude.env` · Git init·push (`b413803`·`c2a6eb3`) · 알리 가입 신청
- 세션 #3: detect-secrets baseline UTF-8 재생성 + hook v1.5.0 정합 (`46fe5b4`)

### 남음 ⏳
- [ ] AliExpress 심사 결과 확인 (이메일 1~2영업일)
- [ ] 알리 승인 후 API 키 발급 + `ali.env` 작성
- [ ] `.claude/settings.json` deny 룰 사용자 검토 (사전 작성 완료, AutoBlog 패턴 확장 deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록**: Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check 추가 — Phase 2 코드 안정화 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후 (콘텐츠 누적·승인 의존)

## Phase 2: 핵심 시스템 (2026-06~07)

### 완료 ✅ (세션 #3~#4)
- [x] pyproject.toml + 의존성 명세 (Phase 1 사전 작성)
- [x] common 모듈 (config·logging·db·grading) — 4 파일
- [x] DB 마이그레이션 적용 — `data/honsalim.db` v1 + 13 테이블 + personas 3·scenarios 10
- [x] enricher.claude_client stub + prompt_loader (6 templates 로드)
- [x] enricher.meta_extractor (META-JSON 분리 추출) + 31 회귀 테스트 — 세션 #4
- [x] validator 4모듈 (truth·schema·disclosure·links) + 39 회귀 테스트 (세션 #4 보강: 1인칭/사진 게이트·AI soft 임계·Schema ItemList/Product·serialize_report 헬퍼)
- [x] writer ↔ validator 통합: `validate_and_save` (BACKEND §2-3 흐름, 세션 #4)
- [x] writer.state_machine (DB §12 6 상태 머신) + 13 회귀 테스트
- [x] writer.article_writer (drafts INSERT + promote_to_article) + 9 회귀 테스트
- [x] collector.scenario_loader (DB scenarios → 큐) + 11 회귀 테스트
- [x] tests/test_db.py (12) + tests/test_cli.py (12) — 안정성 강화
- [x] GitHub Actions workflows (build.yml·lint.yml) — Phase 1 사전 작성·세션 #3 버전 bump
- [x] cli doctor + db migrate + db seed (CLI 3 명령) + doctor §9~§12 보강 (Phase 2 게이트, 세션 #4)
- [x] builder.jsonld (Article Schema.org JSON-LD 빌더, 세션 #4) + 23 회귀
- [x] **회귀 테스트 172/172 PASS** [확정]

### 남음 ⏳ (검토 의존 큼)
- [ ] collector.coupang (쿠팡 가입 후·Phase 4)
- [ ] builder (manifest·renderer·pages·sitemap·assets)
- [ ] dashboard.render·approve (디자인 시안 Phase 3 의존)
- [ ] deployer (git_push·wrangler·verify)
- [ ] tracker.d1_aggregator + Workers go_gateway.js
- [ ] python -m honsalim build --full 성공 (Phase 2 종착)

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
