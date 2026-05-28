# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **Phase 1 ~95% + Phase 2 핵심 모듈 18개 + common.size_caps·회귀 342 PASS + CLI 10/11 + 결정 K1~K5 + L1~L8 (위키바이형 + AI Imagen) + M1~M7 (Google AI Optimization 정합) + Workers + tracker.report + doctor §14 + IMAGE_GENERATION + GOOGLE_AI_OPTIMIZATION** | #6 (2026-05-28) |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·보안 5종·Secrets·Branch Protection main-protect) · Cloudflare(2FA·도메인·Pages·R2·D1) · Anthropic·INDEXNOW 키 · secrets .env · Git push · pre-commit 9종 Passed · Dependabot PR 3건 | #3 |
| Phase 2 핵심 모듈 18개 (#3~#5) | cli · common/{config,logging,grading,db} · validator/{truth,schema,disclosure,links} · writer/{state_machine,article_writer} · collector/scenario_loader · enricher/{prompt_loader,claude_client,meta_extractor,retry} · builder/{jsonld,manifest} · deployer/{git_push,wrangler,verify} · tracker/{d1_aggregator,**report**} · **workers/go_gateway.js** | #5 |
| Phase 2 회귀 테스트 | **342 / 342 PASS** [확정 pytest 9.0.3, 2.63초] — 세션 #6 +9 (check_size_caps 9 + L 정책 validator 0 net: +1 신규 −1 폐기). 분배: validator 42 (L3 2차 1인칭 무조건 차단·owned_products 우회 케이스 폐기) + state_machine 14 + scenario_loader 11 + enricher 13 + retry 15 + meta_extractor 31 + jsonld 45 + manifest 22 + db 12 + cli 46 + article_writer 25 + integration_phase2 18 + deployer 14 + tracker 25 + check_size_caps 9 | #6 |
| CLI 명령 (BACKEND §9) | **10/11** — doctor · db migrate/seed · collect · enrich(dry_run) · validate · approve · unapprove · deploy(dry_run, H4) · build(manifest stub). 남은 1개 (dashboard)는 Phase 3 디자인 의존 | #5 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + 4 게이트 통합(validate_and_save) + META-JSON + Article JSON-LD + 1인칭/사진 게이트. 영구화 세션 #4 시점 5개 사항(tracker.d1_aggregator·deployer·builder.manifest·enricher.retry·state_machine 매트릭스 보강) → DECISIONS J + EVENTS #4·#5 누적 | #4~#5 |
| doctor (BACKEND §9) | §1~§8 기본 + §9 prompt_templates 6종 · §10 모듈 진입점 37개 · §11 state_machine 매트릭스 · §12 tests 로드 · §13 Workers JS (go_gateway.js) · **§14 docs/ size cap (CLAUDE.md §3 자동 점검)** — Phase 2 진입 게이트 자동 점검 | #6 |
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
| GitHub | **`hangyundock/honsalim` Public** — 세션 #6 종료 시점 origin/main 동기 (17 commits 모두 push). build-and-deploy ✅ + CodeQL ✅ + Graph ✅ + lint ✅ + security ✅ (월간 pip-audit) |
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
| AliExpress Portals | **승인 완료 + Tracking ID 발급 + ali.env 작성** [확정 doctor `[OK] secrets/ali.env (loaded)`·세션 #5] | App Key/Secret은 Phase 5 시점 발급 |
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
1. **본 세션 6 commits push origin main 사용자 승인 대기** — 90d60f6 lint fix · 5f6dfde security pyproject · bf82c73 scripts.check_size_caps · 987afed security workflow · f9299ab SUMMARY_PATCH · 55243bc doctor §14
2. **SUMMARY.md / REVIEW_QUESTIONS.md + SUMMARY_PATCH_v1.1.md 사용자 정독** — 진척 매트릭스 보조로 단축 (~30분), Phase 3 진입 게이트
3. **pip-audit transitive 13건 분석** — 직접 의존 3건 lower-bound는 적용. 환경 pip install -U 사용자 명시 승인 후 일괄 갱신 (cryptography·idna·lxml·pip·pyasn1·urllib3)
4. (참고) Phase 5 시점 (2026-11 이후) 알리 App Key/Secret 발급
5. (선택) BitLocker D 드라이브 활성 결정

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
- (완료) 알리 Tracking ID 발급·ali.env 작성·doctor 로드 검증 — 세션 #5
- (보류) 알리 App Key/Secret — Phase 5 시점 발급

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
