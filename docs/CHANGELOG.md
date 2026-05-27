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

## 차기 v1.3 (Phase 1 진입 후 예정)

### To Do (사용자 검토 후)

- REVIEW_QUESTIONS.md 응답 반영
- pre-commit hook 도구 선택 (gitleaks vs detect-secrets)
- 자동 게시 시각 사용자 확인 (11:00 KST 유지 또는 변경)
- 외부 계정 발급 (Cloudflare·쿠팡·GitHub)
- secrets/.env 5종 생성
- 윈도우 작업 스케줄러 등록

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
