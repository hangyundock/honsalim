# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **Phase 1 ~95% + Phase 2 핵심 모듈 9개·회귀 62 PASS** [확정] | #3 (2026-05-28) |
| 운영 모델 (세션 #2 후반) | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건 + GitHub 보안 다중 방어 | #2 |
| Phase 1 외부 작업 완료 | GitHub(2FA·보안 5종) · Cloudflare(2FA·도메인·Pages·R2·D1) · Anthropic 키 · secrets .env · Git init·push · 알리 가입 신청 | #2 |
| Phase 1 세션 #3 정합성 | detect-secrets baseline UTF-8 + hook v1.5.0 · Dependabot PR 3건 일괄 처리 · gitignore SQLite WAL · settings.json Glob 차단 · INDEXNOW_KEY 발급·GitHub Secrets 3개 등록 · Branch Protection ruleset `main-protect` Active | #3 |
| Phase 2 핵심 모듈 9개 (세션 #3) | `src/cli.py` (doctor + db migrate + db seed) · `src/common/{config,logging,grading,db}.py` · `src/validator/{truth,schema,disclosure,links}.py` · `src/writer/state_machine.py` · `src/collector/scenario_loader.py` · `src/enricher/{prompt_loader,claude_client}.py` | #3 |
| Phase 2 회귀 테스트 | **62/62 PASS** [확정] — validator 25 + state_machine 13 + scenario_loader 11 + enricher 13. `tests/conftest.py` + 4 test 파일. pytest 미설치 환경에서도 standard library 직접 호출 가능 구조 | #3 |
| DB 초기화 | `data/honsalim.db` 생성 + schema_version v1 + 13 테이블 + personas 3 + scenarios 10 (seed idempotent INSERT OR IGNORE) | #3 |
| Phase 1 보류·대기 | BitLocker (사용자 결정) · 쿠팡 (Phase 4 후) · 알리 심사 대기 (1~2영업일) · Actions status check 등록 (Phase 2 코드 후) · pip install -e .[dev] (jinja2·markdown·pytest 등 사용자 승인) | #3 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (PLAN·ARCH·DB·SCENARIOS·DESIGN·FRONTEND·BACKEND·POLICY·OPS·BACKUP·MAINTENANCE·SCHEDULE + SUMMARY 비개발자 요약) | #2 |
| 일관성 점검 | ✅ 모순 0건 (167+73+44+34+211+43회 일관 인용) | #2 |
| 사전 작성 SQL | `sql/migrations/001_initial_schema.sql` + `sql/seeds/001_personas_scenarios.sql` | #2 |
| 사전 작성 설정 (세션 #2 추가) | `.gitignore` + `.pre-commit-config.yaml` + `.claude/settings.json` + `build_headers_draft.txt` + `docs/SCHEDULER_GUIDE.md` + `docs/VALIDATOR_PATTERNS.md` + `docs/REVIEW_QUESTIONS.md` | #2 |
| 사전 작성 코드 (세션 #2 추가) | `src/enricher/prompt_templates/` 6개 .md (system_base·article_main·meta_extract·faq_generate·product_recommendation_note·tone_examples) + `src/`·`tests/`·`templates/`·`static/`·`data/` 빈 폴더 + `.gitkeep` | #2 |
| 사전 작성 인프라 (세션 #2 옵션 A) | `pyproject.toml` + `wrangler.toml` + `.github/workflows/build.yml` + `lint.yml` + `README.md` + `docs/CHANGELOG.md` | #2 |
| 메모리 시스템 | feedback 2건 (no-speculation·same-session-continuity) + MEMORY.md 인덱스 | #2 |
| DECISIONS E7 정정 | YouTube 16채널 사례는 HCS와 별개임을 명시·HCS 공식 정보로 갱신 | #2 |
| 5파일 운영 시스템 | ✅ 구축 완료 | #1 |
| 슬래시 명령 (start/save/end) | ✅ 등록 완료 | #1 |
| 사이트 게시글 수 | 0편 (사이트 미오픈) | #2 |
| 트래픽 | N/A | #2 |
| 수익 | N/A | #2 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` |
| docs 폴더 | `D:\affiliate_hub\docs\` |
| archive 폴더 | `D:\affiliate_hub\docs\archive\` |
| 슬래시 명령 | `D:\affiliate_hub\.claude\commands\` |
| 사이트명 | 혼살림 (Honsalim) |
| 도메인 | **honsalim.com 등록 완료** (만료 2027-05-28·Auto Renew·SSL Active) |
| 호스팅 | **Cloudflare Pages `honsalim` 프로젝트 생성** + Custom domain honsalim.com 연결 (Dugi2020@naver.com 계정) |
| GitHub 저장소 | **`hangyundock/honsalim` Public — main HEAD `650eaa5` (#2 + #3 commits push 완료)** |
| GitHub Repository Secrets | **CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 완료** (세션 #3) |
| GitHub Branch Protection | **ruleset `main-protect` Active** — Restrict deletions + Block force pushes (세션 #3) |
| R2 버킷 | **`honsalim-images` (APAC)** |
| D1 DB | **`honsalim-clicks` ID: 9bae858e-456f-40e7-8084-c3b90e4ec3ca** |
| Python 환경 | 3.10 32-bit (시스템 공유, TIMA·AutoBlog 동일) |
| DB | `data/honsalim.db` (미생성, Phase 2) |
| 로그 | `logs/honsalim.log` (미생성, Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\` 운영** (cloudflare.env [CF_API_TOKEN·CF_ACCOUNT_ID·SITE_BASE_URL·ANTHROPIC_API_KEY] · indexnow.env · github-recovery-codes.txt · cloudflare 복구 코드) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 발급 | 만료 | 갱신 |
|---------|------|------|------|
| 도메인 honsalim.com | 2026-05-28 | 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 2026-05-28 | 미정 (GUI 미지원) | 6개월 회전 권장 (I7) — **다음 회전 2026-11-28** [추정] |
| Anthropic API Key | 기존 보유 | 영구 [관찰] | 6개월 회전 권장 (I7) — **다음 회전 2026-11-28** [추정] |
| INDEXNOW_KEY | 2026-05-28 (세션 #3) | 영구 [확정 — 공개 키] | 회전 불요 (사이트 노출용) |
| GitHub PAT | 미발급 | — | Actions는 GITHUB_TOKEN 자동 사용 → PAT 불요 [확정] |
| AliExpress Portals | 2026-05-28 신청 | 심사 대기 (D+1~D+2) | — |
| 쿠팡 파트너스 | 보류 | — | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 룰 | **사전 작성 완료** (deny 24·allow 14, AutoBlog 패턴 확장) — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 (cloudflare.env·indexnow.env·복구 코드 2종) |
| pre-commit hook | ✅ detect-secrets v1.5.0·baseline UTF-8 + trim/eof/yaml/json/large-files/merge-conflict/private-key·black·ruff·mypy 모두 Passed (세션 #3) |
| GitHub Secrets | ✅ CF_API_TOKEN·CF_ACCOUNT_ID·INDEXNOW_KEY 등록 (세션 #3) |
| GitHub Branch Protection | ✅ ruleset `main-protect` Active (세션 #3) |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션)
1. **알리 심사 결과 확인** (이메일, 2026-05-29~06-01 예상)
2. **SUMMARY.md / REVIEW_QUESTIONS.md 사용자 검토** — Phase 2 후반 본격 진입 게이트 (핵심 결정 4건: 모듈 분리·manifest 형태·시나리오 우선순위·단축 URL 목록)
3. ARCH §4 모듈 분리 결정 검토 — pyproject.toml `honsalim` 패키지 가정과 ARCH §3 `src/` flat layout 모순 해결
4. `pip install -e .[dev]` 사용자 명시 승인 (jinja2·markdown·pytest 정상 설치 → 의존성 7/7·표준 pytest 실행)

### Phase 2 진척 가능 (사용자 검토 영향 작음)
- `tests/test_db.py` · `tests/test_cli.py` 보강 (안정성 강화)
- `src/writer/article_writer.py` (drafts INSERT + enriched_payload 저장 — DB §5 활용)

### Phase 2 진척 가능 (검토 의존 큼 — 사용자 결정 후)
- `src/builder/manifest.py` 증분 빌드 JSON 인프라 (ARCH §7·DB §10)
- `src/dashboard/{render,approve}.py` (디자인 시안 Phase 3 의존)
- `src/deployer/{git_push,wrangler}.py` · `src/tracker/d1_aggregator.py`
- `src/workers/go_gateway.js` (Cloudflare Workers JS)

### Phase 1 잔존 (작은)
- Actions status check Branch Protection 추가 — Phase 2 코드 안정화 후
- BitLocker 활성 (사용자 결정 시점)
- 알리 승인 시 API 키 + `ali.env` 작성

### Phase 2 핵심 시스템 (2026-06~07)
- 모듈 8개·DB 마이그레이션·Claude 파이프라인·Jinja2 빌더·진실성 게이트·배포·테스트

### Phase 3 디자인·콘텐츠 (2026-07)
- Claude Design 시안 3~5종 (사용자 직접 Pro/Max 구독 활용)
- 템플릿 5종 + partials 18종
- 첫 5~10편 작성·승인·시범 배포

### 보류
- AdSense 신청 결정 (Phase 6, 2026-12)
- 영어 사이트 확장 (Phase 6 검토)
- 보조 호스팅 (GitHub Pages) (Phase 4 검토, MAINTENANCE §10)

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| 2026-05-28 | Phase 1 인프라 ~85% 도달 (예정 일정 앞당김) |
| 2026-05-29~06-01 | 알리 심사 결과 (이메일) |
| 2026-06 | Phase 2 핵심 시스템 (코드 본격 작성) |
| 2026-07 중반 | Phase 3 디자인 시안·콘텐츠 |
| 2026-07 말 | Phase 4 첫 출시 (사이트 오픈) |
| 2026-08 | 운영 본격 시작·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 콘텐츠 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) |
| 2027-06 | Phase 7 1년 결산 |
