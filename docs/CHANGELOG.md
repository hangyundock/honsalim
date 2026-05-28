# CHANGELOG.md — 혼살림 설계·운영 변경 이력

> 설계 문서·결정·코드 변경 누적 기록.
> 등급 명시 의무 + 출처 명시.
> 작성: 2026-05-28 세션 #2.

---

## v1.0 — 2026-05-27 (세션 #1)

### Added (신규)

- 프로젝트 폴더 + docs/·docs/archive/·.claude/commands/ 생성
- 5파일 운영 시스템 구축 (CLAUDE·STATE·DECISIONS·TODO·EVENTS)
- 슬래시 명령 3개 (start/save/end)
- **PLAN.md** v1.0 작성 (비전·KPI·12개월 로드맵·페르소나 3·예산)
- **DECISIONS** A~H 카테고리 47건 [확정]
- 사이트명 **혼살림 (honsalim.com)** 확정
- 컨셉 **미니멀+따뜻함** + 시나리오 추천 + 페르소나×예산 확정
- 기술 스택: Python 3.10 + Jinja2 + Cloudflare Pages + SQLite + Claude Haiku

### 정밀 조사 출처

- 쿠팡 파트너스·알리 정책·수수료·법규 [확정·관찰]
- YouTube AI Slop 단속 (2026-01 한국 보도) [관찰]
- Google Helpful Content System 도입·통합 일자 [확정]
- 한국 1인 가구 KOSIS 통계 [확정]
- 모바일·검색 점유율 StatCounter [확정·관찰]

---

## v1.1 — 2026-05-27 (세션 #2 1차)

### Added (12개 설계 문서 + 사전 작성)

- **ARCH.md** v1.0 (~600줄) — 시스템 다이어그램·모듈 8개·외부 의존 5개·secrets·빌드·배포·게이트
- **DB.md** v1.0 (~650줄) — SQLite 9테이블 + D1 3테이블 + manifest JSON + 상태 머신 6개
- **SCENARIOS.md** v1.0 (~500줄) — 페르소나 3 + 시나리오 10편 + 시드
- **DESIGN.md** v1.0 (~650줄) — 토큰·Pretendard·컴포넌트 18·페이지 5·Claude Design 워크플로
- **FRONTEND.md** v1.0 (~600줄) — Jinja2·meta·Schema·sitemap·IndexNow·CWV
- **BACKEND.md** v1.0 (~600줄) — 모듈 8 인터페이스·Claude API 캐시·Workers·테스트
- **POLICY.md** v1.0 (~600줄) — 4단계 게이트·PIPA·사업자·접근성·보안
- **OPS.md** v1.0 (~600줄) — 체크리스트·로그·알림·장애·자격증명·사업자
- **BACKUP.md** v1.0 (~450줄) — 7대상 + 3계층 + 복구 리허설 + 재난
- **MAINTENANCE.md** v1.0 (~500줄) — 의존성·CVE·확장·마이그레이션·디자인 갱신
- **SCHEDULE.md** v1.0 (~500줄) — Phase 0~7·월별·시즌·KPI
- **SUMMARY.md** v1.0 — 12 문서 1페이지 요약 + 결정 25개 매트릭스
- **sql/migrations/001_initial_schema.sql** (DB 9테이블 + 트리거 + 인덱스)
- **sql/seeds/001_personas_scenarios.sql** (personas 3 + scenarios 10)
- 12 문서 일관성 점검 [관찰] — 모순 0건

---

## v1.2 — 2026-05-27~28 (세션 #2 2차)

### Changed (운영 모델 변경)

- **DECISIONS C4 폐기** (자동 게시 시간 없음) — 사용자 요청 "발행 편수 최대화 + 윈도우 스케줄러 자동 게시"
- **DECISIONS C5 폐기** (매주 2~3편) — 동일
- **CLAUDE.md §7·§8 갱신** — 운영 모델·시간 민감 제약

### Added (DECISIONS 신규)

- **C6** 자동 게시 활성 (윈도우 스케줄러, 자동 "승인"은 절대 금지)
- **C7** 자동 게시 기본 시각 매일 11:00 KST (AutoBlog 09:00~10:30과 30분 간격)
- **C8** 콘텐츠 발행 페이스: 큐 기반·사용자 작성 역량 내 최대
- **C9** KPI 게시글 12개월 100편 → 240편+ 상향
- **I1** GitHub 보안 다중 방어 (.gitignore·pre-commit·Secret Scanning·브랜치 보호·CodeQL)
- **I2** 보안 헤더 6종 의무 (CSP·HSTS·XCTO·XFO·Referrer·Permissions)
- **I3** 외부 계정 5종 2FA 의무
- **I4** 의존성 보안 자동화 (Dependabot·pip-audit·npm audit)
- **I5** 로컬 디스크 BitLocker 암호화
- **I6** GitHub CodeQL 자동 스캔
- **I7** secrets 정기 회전 (PAT 90일·기타 180일)

### Fixed (DECISIONS 정정, no-speculation 원칙 적용)

- **E7 정정** — "2024-03 16채널 47억뷰 종료"는 **YouTube AI Slop 사례**임을 명시. HCS 공식 정보 (2022-08 도입·2024-03 코어 통합·2023-02 AI 정책)로 갱신. 검증 안 된 HCS 구체 사례 인용 제거.

### Added (사전 설정·코드 11종 — Phase 1·2 즉시 가용)

- **`.gitignore`** (POLICY §10-3 + I1)
- **`.pre-commit-config.yaml`** (gitleaks A 활성·detect-secrets B 옵션)
- **`.claude/settings.json`** (AutoBlog 확장 deny 24·allow 14)
- **`build_headers_draft.txt`** (보안 헤더 6종)
- **`pyproject.toml`** (Python 3.10·의존성·black·ruff·mypy·pytest·coverage)
- **`wrangler.toml`** (Workers·D1 binding, database_id placeholder)
- **`.github/workflows/build.yml`** + **`lint.yml`** (CodeQL 포함)
- **`README.md`** (GitHub 공개 저장소용)
- **`src/enricher/prompt_templates/*.md`** 6개 (system_base·article_main·meta_extract·faq_generate·product_recommendation_note·tone_examples)
- **`docs/SCHEDULER_GUIDE.md`** (윈도우 작업 스케줄러 GUI·PowerShell)
- **`docs/VALIDATOR_PATTERNS.md`** (정규식 12 카테고리)
- **`docs/REVIEW_QUESTIONS.md`** (다음 세션 검토 질문 25개)
- 빈 폴더 + `.gitkeep` (src·src/common·src/enricher·tests·templates·static·data)

### Memory (Claude 영구 원칙 저장)

- `feedback_no_speculation` — 추측 금지·조사 후 사실만·등급 명시
- `feedback_same_session_continuity` — 같은 세션 연속 작업이 default

### Updated (8 영향 문서)

- PLAN.md §6 KPI 상향·§9 결정 표
- SCENARIOS.md §6-1 발행 페이스
- SCHEDULE.md §3-6 Phase 5
- OPS.md §2-2·§2-3 보안 점검 추가
- POLICY.md §13-0 자동 승인 vs 자동 게시·§13-4 스케줄러 큐·§14-bis 보안 종합 7절 신규
- BACKEND.md §2-7-bis 스케줄러 모듈·§9 CLI 명령·§10-2 보안 도구
- SUMMARY.md §C 운영 갱신·§F 보안 7건 신규·§11 산출물 표
- CLAUDE.md §7·§8

---

## v1.3 — 2026-05-28 (세션 #3, Phase 1 마무리 + Phase 2 기초 모듈)

### Added (Phase 2 핵심 모듈 9개·회귀 95)

- **`src/cli.py`** — doctor + db migrate + db seed (BACKEND §9 [확정])
- **`src/common/{config,logging,grading,db}.py`** — 4 파일 (BACKEND §7·§14·§15-1)
- **`src/validator/{__init__,truth,schema,disclosure,links}.py`** — 4 게이트 패턴 (POLICY §3·§4·§2·§6 + VALIDATOR_PATTERNS [확정])
- **`src/writer/state_machine.py`** — DB §12 6 상태 머신 (collected→enriched→validated→approved→published + rejected)
- **`src/writer/article_writer.py`** — drafts INSERT + promote_to_article + article_history 감사
- **`src/collector/scenario_loader.py`** — DB scenarios → 수집 큐
- **`src/enricher/{prompt_loader,claude_client}.py`** — 6 templates 로드 + Anthropic SDK stub (dry_run 기본)
- **회귀 테스트 95/95 PASS** [확정]: validator 25 + state_machine 13 + scenario_loader 11 + enricher 13 + db 11 + cli 13 + article_writer 9
- **DB 초기화**: `data/honsalim.db` v1 + 13 테이블 + personas 3 + scenarios 10 (seed idempotent)

### Phase 1 외부 작업 완료 (Phase 1 ~95%)

- **GitHub Repository Secrets**: CF_API_TOKEN·CF_ACCOUNT_ID·INDEXNOW_KEY 등록 (사용자 Web UI)
- **INDEXNOW_KEY 발급**: `indexnow.env` 작성
- **Branch Protection** ruleset `main-protect` Active (Restrict deletions + Block force pushes)
- **pre-commit hook 9종 모두 Passed**: detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy
- **Dependabot PR 3건 일괄 처리** (checkout·setup-python·wrangler-action)

### Fixed (no-speculation 원칙 적용 사례)

- **detect-secrets baseline** UTF-16 LE → UTF-8 재생성 (PowerShell `>` 기본 인코딩 함정·CLAUDE.md 명시) + hook v1.4.0 → v1.5.0 정합
- **load_dotenv override=True** — 시스템 환경 변수가 빈 문자열일 때 secrets 무시 문제 해결
- **sys.stdout.reconfigure(utf-8)** — Windows cp949 콘솔 한국어 출력 보장
- **SQLite isolation_level=None vs executescript** 충돌 해결

---

## v1.4 — 2026-05-28 (세션 #4, Phase 2 후반 본격 + 사용자 검토 자료)

### Added (Phase 2 모듈 4종 추가·회귀 95→247)

- **`src/enricher/meta_extractor.py`** — META-JSON 분리 추출 (BACKEND §49 시그니처). parse_meta_json·validate_meta·normalize_meta 분리. dry_run=True 기본.
- **`src/enricher/retry.py`** — BACKEND §3-5 [확정] 재시도 정책. RateLimit 3회(1·2·4초+jitter) · Overloaded 1회(10초) · Timeout/BadRequest/APIError 즉시 fail. 의존성 주입 패턴 (SDK 미설치 환경 mock 회귀 가능).
- **`src/builder/__init__.py`** + **`src/builder/jsonld.py`** — Schema.org JSON-LD 빌더 4종 (Article·ItemList·Product + keywords 정규화). POLICY §4 + VALIDATOR §8 [확정] 필드 모두 충족.
- **회귀 테스트 247/247 PASS** [확정] — validator 39 + state_machine 14 + scenario_loader 11 + enricher 13 + retry 15 + meta_extractor 31 + jsonld 45 + db 12 + cli 31 + article_writer 25 + integration_phase2 11 (11 test 파일)

### Changed (기존 모듈 보강)

- **`src/validator/truth.py`**: 1인칭/사진 게이트 (POLICY §3-1-3 [확정] FIRST_PERSON_PATTERNS + photos/has_user_photo) + AI soft 임계 (VALIDATOR §4 [관찰])
- **`src/validator/schema.py`**: ItemList·Product 필수 필드 추가 (VALIDATOR §8 [확정])
- **`src/validator/__init__.py`**: serialize_report 헬퍼 — JSON 직렬화 가능 형태로 변환
- **`src/writer/article_writer.py`**: validate_and_save (BACKEND §2-3 흐름 통합) + compute_content_hash + extract_disclosure_first 헬퍼
- **`src/writer/state_machine.py`**: 매트릭스 보강 `approved → validated` (BACKEND §9 unapprove 정합)
- **`src/cli.py`**: 5 명령 추가 (collect·enrich(dry_run)·validate·approve·unapprove) + doctor §9~§12 보강 (prompt_templates·Phase 2 모듈 진입점·매트릭스·tests 로드)

### Added (CLI 명령 8/11 활성, BACKEND §9 [확정])

- `doctor` · `db migrate` · `db seed` · `collect <slug>` · `enrich --draft <id> [--no-dry-run]` · `validate --draft <id>` · `approve --draft <id> [--note]` · `unapprove --draft <id>`
- 남은 3개: `dashboard` · `build` · `deploy` (builder/dashboard/deployer 모듈 의존)

### Added (통합 회귀 — Phase 2 모듈 결합 검증)

- **`tests/test_integration_phase2.py`** 11 케이스
  * 정상 전체 흐름 (collected→enriched→validated→approved→published)
  * truth/disclosure fail rejected
  * rejected → collected 재수집 → 재처리
  * state_machine 위반 차단 (skip·미승인 promote)
  * builder.jsonld ↔ validator.check_schema 정합
  * content_hash·disclosure_first 자동 생성 + articles 컬럼 저장
  * validation_report 영속화

### Added (DECISIONS J 카테고리 신규, 8건)

- **J1** 모듈 의존 방향: writer → validator 단방향
- **J2** state_machine 매트릭스 보강 (approved → validated)
- **J3** CLI 명령 8/11 활성
- **J4** enrich 기본 dry_run (Claude API 비용 보호)
- **J5** JSON-LD 빌더 4 인터페이스
- **J6** content_hash 형식: `sha256:` + 64자 hex
- **J7** disclosure_first 추출 헬퍼 (POLICY §2-2 [확정])
- **J8** payload 책임 분리 — enriched_payload 구조는 [관찰]

### Added (사용자 검토 자료 2건 — 핵심 결정 4건 자료 완비)

- **`docs/ARCH_MODULE_DIAGNOSIS.md`** — `src/` flat vs pyproject.toml `honsalim` 패키지 모순 진단 + 옵션 A/B/C 비교 + 권장 [추정]
- **`docs/KEY_DECISIONS_REVIEW.md`** — manifest 형태 · 시나리오 우선순위 · 단축 URL 차단 목록 3건 검토 자료

### Updated (운영 문서)

- **STATE.md**: cap 98% → 66% 정돈 (운영 현황 표 통합·중복 제거)
- **TODO.md**: cap 96% → 62% 정돈
- **EVENTS.md**: 세션 #2 archive 회전 (cap 20KB 초과 회피, 22.9KB → 9.4KB)
- **DECISIONS.md**: J 카테고리 신설

### Memory (Claude 영구 원칙 강화)

- **`feedback_same_session_continuity` 강화**: 위반 사례 3회 누적 기록 (세션 #2·#3·#4). 종료 추천 전 의무 자문 4질문 + "종료는 사용자 명시 요청 시에만" 룰

---

## v1.5 — 2026-05-28 (세션 #5, Phase 2 ~95% 도달 + K1~K5 [확정] + 회귀 333)

### Added (핵심 결정 5건 [확정] — DECISIONS K 신설)

- **K1** manifest 형태 `data/manifest.json` 단일 JSON [확정]
- **K2** 시나리오 우선순위 SCENARIOS §4-11 현 명세 그대로 [확정]
- **K3** 외부 단축 URL 차단 11→13 (`n.kakao.com`+`naver.me`) — links.py + POLICY §6-1 + 회귀 3
- **K4** 모듈 분리 옵션 B (pyproject.toml flat 정합) — `honsalim` entry point 검증 [확정]
- **K5** prompt_loader Jinja2 `ChainableUndefined` 채택 — 회귀 환경 호환

### Added (Phase 2 잔존 모듈)

- **`src/workers/go_gateway.js`** (BACKEND §5 [확정]) — Cloudflare Workers /go/<slug> → D1 lookup → 302. 보안: IP 미저장·UA SHA-256 16자·referrer hostname만·bot UA flag
- **`src/tracker/report.py`** (BACKEND §2-8) — aggregate_weekly·aggregate_monthly·top_articles_by_clicks·render_html_stub
- **`scripts/run_tests.py`** — pytest 미설치 환경 일괄 회귀 헬퍼

### Added (CLI deploy/build 10/11)

- **`cmd_deploy`** dry_run=True 기본 (DECISIONS H4) — deployer 3단계
- **`cmd_build`** — builder.manifest stub 호출 (renderer Phase 3 의존)

### Added (doctor §13 + 진입점 37)

- §13 Workers JS 파일 점검 (export default 패턴)
- §10 진입점 37/37 OK (+ tracker.report 5 + writer 헬퍼 2)

### Updated (CI 인프라)

- pre-commit 버전 일괄 upgrade (Black 24.1→26.5 등) → 9 hook 모두 Passed [확정]
- build.yml: renderer 미작성 시 자동 skip (Phase 3 전 build/deploy 건너뜀)
- mypy: 8개 py.typed marker + mypy_path = "src" — flat src layout 정합 (K4)
- anthropic.OverloadedError getattr fallback (SDK 버전 미확정 호환)

### Updated (운영 환경)

- `pip install -e .[dev]` 사용자 명시 승인·적용 → pytest 9.0.3·black 26.5.1·ruff 0.15.14·mypy 2.1.0 등 설치
- `honsalim.exe` entry point 정상 작동 — K4 검증 [확정]
- 회귀: 247 → 333 (+86) PASS / 0 FAIL / 0 SKIP [확정 pytest 2.21초]
- push origin main 2회 명시 승인·푸시 (11 commits 모두 외부 백업)

### Updated (외부)

- AliExpress Affiliate 승인 [확정 2026-05-28 D+0] + Tracking ID `honsalim` + `D:\secrets\affiliate_hub\ali.env` 작성·검증
- doctor `[OK] secrets/ali.env (loaded)` 정합

### Known (다음 세션 처리)

- CI lint #15 Black format check fail (commit 86f9bb4) — 코드 동작·CI 핵심·회귀 모두 정상

---

## v1.6 — 2026-05-28 (세션 #6, 보안 강화 + 운영 인프라 + 회귀 333→342)

### Fixed (CI lint)

- **CI lint #15 Black format check fail 해소** (90d60f6) — test 3건 (`test_state_machine.py`·`test_tracker.py`·`test_article_writer.py`) black 26.5.1 multiline str inline 정합. 코드 동작 무영향, 격식 변경만. pre-commit 9 hook 모두 Passed

### Added (보안 강화)

- **`pyproject.toml` 직접 의존 3건 lower-bound** (5f6dfde) — pillow≥12.2 (5 CVE) · requests≥2.33 (CVE-2026-25645) · python-dotenv≥1.2.2 (CVE-2026-28684). pip-audit 16건 / 9 패키지 진단 결과 직접 영향 3건 [확정]
- **`.github/workflows/security.yml` 신규** (987afed) — pip-audit 월간 cron (매월 1일 09:00 UTC) + workflow_dispatch + JSON artifact 90일 + GitHub Step Summary. DECISIONS I4 정합

### Added (운영 인프라)

- **`src/common/size_caps.py` + `scripts/check_size_caps.py`** (bf82c73 → 55243bc) — docs/ size cap 자동 점검 (CLAUDE.md §3 STATE 10KB·EVENTS 20KB·TODO 5KB). CAPS dict + check(project_root) + format_human. CLI + doctor §14 통합
- **`src/cli.py` doctor §14** (55243bc) — size cap 운영 게이트 자동 점검. cap 초과는 WARN (회전·정돈 신호), 파일 누락은 FAIL (5파일 시스템 손상)

### Added (사용자 정독 보조)

- **`docs/SUMMARY_PATCH_v1.1.md`** (f9299ab) — SUMMARY/REVIEW_QUESTIONS 진척 패치. 결정 매트릭스 25→45 (J 8 + K 5) · Phase 진척 · 사전 작성 산출물 사용 상태 · REVIEW_QUESTIONS 23/25 자동 [확정]. 정독 시간 40~60분 → 25~30분 단축

### Updated (운영 문서 + cap 정돈)

- **STATE.md**: 9.37 → 8.05 KB (93.7% → 80.5%) — 세션 #4 영구화 5개 행 정돈 (DECISIONS J + EVENTS 누적)
- **TODO.md**: 4.35 → 4.00 KB (87.1% → 80.0%) — 세션 #5 완료 항목 EVENTS·STATE 누적분 제거
- 본 세션 7 commits 누적 (90d60f6·5f6dfde·bf82c73·987afed·f9299ab·55243bc·5f50025)

### Updated (회귀 테스트)

- 333 → 342 / 342 PASS [확정 pytest 9.0.3, 2.74초] — `tests/test_check_size_caps.py` +9 (TestCommonModule 7 + TestCliWrapper 2)
- common.size_caps 직접 회귀: CAPS schema·check·format_human·missing file·over cap 케이스

### Memory (Claude 영구 원칙 강화)

- **`feedback_no_end_of_step_prompting` 신설** — 한 작업 끝날 때마다 마감 제안 출력 금지. 컨텍스트 80%+ 또는 사용자 명시 지시 또는 시급 작업 모두 소진일 때만. 세션 #6 사용자 비판 (컨텍스트 7% 시점) 반영

### Changed (1인칭·사진·AI 이미지 정책 — DECISIONS L 8건, 2차 재변경)

- **L1·L2·L3·L4·L5·L6·L7·L8 [확정]** — 사용자 결정 "사진 직접 촬영 없음, Google API로 AI 이미지 생성":
  - E8(한국어 1인칭 허용)·D5(시나리오당 사진 의무)·L2/L3 1차 초안 **모두 폐기**
  - 1인칭 **무조건 차단** (L3·L5) — AI 이미지로 거짓 광고 회피
  - **Google Imagen 4 Fast 채택** (L6) — `imagen-4.0-fast-generate-001`, AutoBlog `D:\autoblog\tistory_revival\ai_image_gen.py` 패턴 이식
  - AI 생성 명시 표기 (L7) + 상품 이미지는 쿠팡 공식 위젯만 (L8)
- **`docs/IMAGE_GENERATION.md` 신설** — 도구·API·환경변수·프롬프트·법규·예산·AutoBlog 매핑 명세
- **POLICY §3-1-3·§3-1-7·§3-3** 재갱신 — 1인칭 무조건 fail. 페르소나 사진 → AI 생성 이미지 (`source_type='ai_generated'` + `ai_model` + `prompt_used` 메타)
- **DESIGN §11-2** 재갱신 — 사진 사전 촬영 폐기. Google AI Studio API 키 발급·결제 활성화로 대체
- **`src/validator/truth.py`** — `_check_first_person` 단순화 (인자 없음, 무조건 차단). 이슈 코드 `first_person_forbidden`. 회귀 갱신 (validator 43→43, owned_products 우회 케이스 폐기)
- **예산 영향** [관찰] — Imagen $0.02/장 × 100편 × 6장 = $24/월 ≈ 32,000원 → PLAN §8 갱신 의무 (다음 세션)

### Known (다음 세션 처리)

- 본 세션 push origin main — 사용자 명시 키워드 승인 후 (추가 commits 누적)
- pip-audit 환경 갱신 — pip install -U 사용자 명시 승인 후 (A안 권장)
- SUMMARY/REVIEW_QUESTIONS + SUMMARY_PATCH_v1.1.md 사용자 정독 (Phase 3 진입 게이트)
- 페르소나별 인테리어 사진 6~9장 사전 촬영 (L2 — Phase 3 시작 전)

---

## 변경 로그 작성 규칙

| 항목 | 룰 |
|------|-----|
| 버전 번호 | Phase 결산 시 메이저 (v2.0·v3.0) / 세션 변경 시 마이너 (v1.1·v1.2) |
| 일자 | 작업 일자 (KST) — 등급 [확정] |
| 분류 | Added·Changed·Fixed·Removed·Memory·Updated |
| 출처 | DECISIONS 코드·문서 절 인용 의무 |
| 등급 | [확정]/[관찰]/[추정]/[확인 불가] 명시 |

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-28 | 최초 작성 (v1.0·v1.1·v1.2 누적 + 차기 v1.3) | Claude Opus 4.7 |
| 1.1 | 2026-05-28 | v1.3 (세션 #3) + v1.4 (세션 #4) 정식 추가, 차기 v1.5 명시 | Claude Opus 4.7 |
| 1.2 | 2026-05-28 | v1.5 (세션 #5) + v1.6 (세션 #6) 정식 추가, 차기 섹션 폐기 | Claude Opus 4.7 |
