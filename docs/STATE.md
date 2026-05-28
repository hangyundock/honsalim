# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **Phase 1 ~95% + Phase 2 핵심 모듈 18개·회귀 333 (331 PASS/0 FAIL/2 SKIP) [확정 직접 호출] + CLI 10/11 + 결정 K1~K4 + Workers + tracker.report** | #5 (2026-05-28) |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·보안 5종·Secrets·Branch Protection main-protect) · Cloudflare(2FA·도메인·Pages·R2·D1) · Anthropic·INDEXNOW 키 · secrets .env · Git push · pre-commit 9종 Passed · Dependabot PR 3건 | #3 |
| Phase 2 핵심 모듈 18개 (#3~#5) | cli · common/{config,logging,grading,db} · validator/{truth,schema,disclosure,links} · writer/{state_machine,article_writer} · collector/scenario_loader · enricher/{prompt_loader,claude_client,meta_extractor,retry} · builder/{jsonld,manifest} · deployer/{git_push,wrangler,verify} · tracker/{d1_aggregator,**report**} · **workers/go_gateway.js** | #5 |
| Phase 2 회귀 테스트 | **333** (직접 호출 331 PASS / 0 FAIL / 2 SKIP — pytest tmp_path 의존) [확정 `scripts/run_tests.py`] — validator 42 + state_machine 14 + scenario_loader 11 + enricher 13 + retry 15 + meta_extractor 31 + jsonld 45 + manifest 22 + db 12 + cli 46 + article_writer 25 + integration_phase2 18 + deployer 14 + tracker **25** (+13 report) | #5 |
| tracker.d1_aggregator (세션 #4) | BACKEND §2-8 [확정] — aggregate(date, dry_run=True) wrangler d1 execute · export_to_sqlite(aggregates) articles.view_count_cached UPDATE. D1 SQL UPSERT 패턴 (ON CONFLICT) — 재실행 안전 | #4 |
| deployer (세션 #4) | BACKEND §2-7 [확정] — git_push · wrangler_deploy · verify_deploy. 모두 dry_run=True 기본 (외부 영향 차단, DECISIONS H4). 실제 push·deploy·HEAD는 사용자 명시 승인 후 dry_run=False | #4 |
| builder.manifest (세션 #4) | DB §10 [추정] JSON 인터페이스 — new/load/save/upsert_article/upsert_asset/upsert_template/needs_rebuild (ARCH §7-3 5조건). 형태 결정은 사용자 검토 후 [확정] | #4 |
| enricher.retry (세션 #4) | BACKEND §3-5 [확정] — RateLimit 3회(1·2·4초+jitter) · Overloaded 1회(10초) · Timeout/BadRequest/APIError 즉시 fail · SDK 미설치 환경 mock 회귀 가능 | #4 |
| CLI 명령 (BACKEND §9) | **10/11** — doctor · db migrate/seed · collect · enrich (dry_run) · validate · approve · unapprove · **deploy (dry_run 기본 H4)** · **build (manifest stub)**. 남은 1개 (dashboard)는 디자인 Phase 3 의존 | #5 |
| state_machine 매트릭스 보강 (세션 #4) | `approved → validated` 추가 — BACKEND §9 unapprove 정합. DB §12-2 매트릭스 갱신 | #4 |
| Phase 2 통합 회귀 (세션 #4) | `tests/test_integration_phase2.py` 11 케이스 — 정상 전체 흐름(collected→published) + truth/disclosure fail rejected + rejected 재수집 + state_machine 위반 차단 + builder↔validator 정합 + content_hash/disclosure_first 자동 생성 + validation_report 영속화 | #4 |
| Phase 2 흐름 골격 [관찰] | collected→enriched→validated/rejected→approved→published 6 상태 + 4 게이트 통합 (validate_and_save) + META-JSON 추출 + Article JSON-LD 빌더 + 1인칭/사진 게이트. 남은 영역: collector(쿠팡)·builder.manifest·dashboard·deployer·tracker | #4 |
| doctor (BACKEND §9) | §1~§8 기본 + §9 prompt_templates 6종 · §10 모듈 진입점 **37개** (+tracker.report 5) · §11 state_machine 매트릭스 · §12 tests 로드 · **§13 Workers JS 파일 (go_gateway.js)** — Phase 2 진입 게이트 자동 점검 | #5 |
| DB 초기화 | `data/honsalim.db` v1 + 13 테이블 + personas 3 + scenarios 10 (seed idempotent) | #3 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (PLAN·ARCH·DB·SCENARIOS·DESIGN·FRONTEND·BACKEND·POLICY·OPS·BACKUP·MAINTENANCE·SCHEDULE). 일관성 모순 0건 | #2 |
| 사전 작성 산출물 (#2) | SQL 2편 + 설정 5건 + prompt_templates 6종 + 인프라 7건 (pyproject·wrangler·workflows·README·CHANGELOG 등). 세부는 EVENTS_202605.md | #2 |
| 메모리 시스템 | feedback 2건 ([[no-speculation]] · [[same-session-continuity]] — 세션 #4 위반 사례 3회 누적 기록·강화) + MEMORY.md | #4 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | 0편 (Phase 4 출시 전) / N/A / N/A | #2 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsalim.com** (만료 2027-05-28·Auto Renew·SSL Active) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main 동기 (세션 #5 검증 `git rev-list --count origin/main..main = 0`) [확정] |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v1) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·복구 코드 2종) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY | 영구 [확정 — 공개 키] | 회전 불요 |
| GitHub PAT | 미발급 (Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **2026-05-28 승인 완료** [확정 — 이메일 "Your affiliate account is ready"] | API 키 발급·`ali.env` 작성 사용자 작업 대기 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션)
1. **알리 API 키 발급 + `ali.env` 작성** — 승인 완료 (2026-05-28). portals.aliexpress.com 로그인 후 Tracking ID·App Key 발급
2. **SUMMARY.md / REVIEW_QUESTIONS.md 사용자 검토** — Phase 2 본격 진입 게이트
3. (완료) ~~핵심 결정 4건~~ — DECISIONS K1·K2·K3·K4 [확정] 등재 (세션 #5)
4. `pip install -e .[dev]` 사용자 명시 승인 — pytest·ruff·black·jinja2·markdown 정식 설치 후 회귀 320 재검증 (K3 +3 추가)
5. push origin main — 본 세션 추가 commit 누적 (사용자 승인 후)

### Phase 2 진척 가능 (검토 영향 작음)
- (현재 안전 진척 후보 모두 소진 — 다음은 사용자 검토 4건 의존)

### Phase 2 진척 가능 (검토 의존 큼 — 사용자 결정 후)
- `src/builder/manifest.py` 증분 빌드 (ARCH §7·DB §10)
- `src/dashboard/{render,approve}.py` (디자인 시안 Phase 3 의존)
- `src/deployer/{git_push,wrangler}.py` · `src/tracker/d1_aggregator.py` · `src/workers/go_gateway.js`
- `src/collector/coupang.py` (Phase 4)

### Phase 1 잔존 (작음)
- Actions status check Branch Protection 추가 (Phase 2 안정 후)
- BitLocker 활성 (사용자 결정)
- (다음 세션) 알리 API 키 발급 → ali.env 작성 — 승인 완료 (2026-05-28)

### 보류
- AdSense 신청 (Phase 6, 2026-12)
- 영어 사이트 확장 (Phase 6 검토)
- 보조 호스팅 GitHub Pages (Phase 4 검토)

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| ~~2026-05-29~06-01~~ | ~~알리 심사 결과~~ → **2026-05-28 승인 [확정]** |
| 2026-06 | Phase 2 핵심 시스템 본격 |
| 2026-07 중반 | Phase 3 디자인·콘텐츠 |
| 2026-07 말 | Phase 4 첫 출시 |
| 2026-08 | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
