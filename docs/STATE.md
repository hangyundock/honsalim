# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#14: ① 용어 일상화**(시나리오→**내맘대로 세팅**·페르소나→**라이프스타일**) 화면·글본문·프롬프트·renderer 교체 + 재발방지 가드, **회귀 472 PASS**, build/site 재빌드(배포 대기). **② ★페이지/콘텐츠 大전환 기획 확정** — "**카테고리 우선 제품 비교·정보 사이트(노써치형)**". 표준 `docs/CATEGORY_PAGE.md`+프로토타입 `scripts/category_page_prototype.py`(사무용 의자·흰 바탕·NanumSquare Neo·2분류·실데이터). #13: 첫 글 라이브·무인배포(방법A). **★본구현 미완(자동화)**: 파이프라인·2티어 수집·가격 재조회·렌더러 이식 (DECISIONS O) | 2026-05-31 #14 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·보안 5종·Secrets·Branch Protection main-protect) · Cloudflare(2FA·도메인·Pages·R2·D1) · Anthropic·INDEXNOW 키 · secrets .env · Git push · pre-commit 9종 Passed · Dependabot PR 3건 | #3 |
| Phase 2 핵심 모듈 18개 (#3~#5) | cli · common/{config,logging,grading,db} · validator/{truth,schema,disclosure,links} · writer/{state_machine,article_writer} · collector/scenario_loader · enricher/{prompt_loader,claude_client,meta_extractor,retry} · builder/{jsonld,manifest} · deployer/{git_push,wrangler,verify} · tracker/{d1_aggregator,**report**} · **workers/go_gateway.js** | #5 |
| Phase 2 회귀 테스트 | **472 / 472 PASS** [확정 pytest, #14] — #14 +2(용어 재발방지 가드 `test_renderer`), #13 +34 (article_writer link/slug 7 + cli promote/sync 5 + renderer 상세글·404·robots 8 + slug_map 11 + tracker ts가드 1 + disclosure ali 1 등). #12 436. CI(GitHub Actions)에서도 470 통과 후 배포 | 2026-05-30 |
| CLI 명령 (BACKEND §9) | **14개** — doctor · db · collect · collect-products · enrich · validate · approve · **promote(#13 신규: article_fields 조립·md→HTML·article_products 연결)** · unapprove · deploy · **sync-slugmap(#13 신규: published 상품→D1 slug_map UPSERT, dry-run 기본)** · build · dashboard | #13 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + 4 게이트 통합(validate_and_save) + META-JSON + Article JSON-LD + 1인칭/사진 게이트. 영구화 세션 #4 시점 5개 사항(tracker.d1_aggregator·deployer·builder.manifest·enricher.retry·state_machine 매트릭스 보강) → DECISIONS J + EVENTS #4·#5 누적 | #4~#5 |
| doctor (BACKEND §9) | §1~§8 기본 + §9 prompt_templates 6종 · §10 모듈 진입점 **49개** (#13 +link_article_products·unique_article_slug·sync_slug_map·collect_slug_map_entries) · §11 state_machine 매트릭스 · §12 tests 로드 · §13 Workers JS · §14 size cap | #13 |
| DB 초기화 | `data/honsalim.db` v1 + 13 테이블 + personas 3 + scenarios 10 (seed idempotent) | #3 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (PLAN·ARCH·DB·SCENARIOS·DESIGN·FRONTEND·BACKEND·POLICY·OPS·BACKUP·MAINTENANCE·SCHEDULE). 일관성 모순 0건 | #2 |
| 사전 작성 산출물 (#2) | SQL 2편 + 설정 5건 + prompt_templates 6종 + 인프라 7건 (pyproject·wrangler·workflows·README·CHANGELOG 등). 세부는 EVENTS_202605.md | #2 |
| 메모리 시스템 | feedback 7건 (#9 [[no-unfounded-priority]] · **#12 [[incremental-critical-review]](배치금지·1건씩 점검·근본해결) · [[autonomous-safe-system]](무인·안전·자율)** 추가) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **1편 라이브 게시** (honsalim.com/articles/homeoffice-chair-desk-50/, #13 배포) / N/A / N/A (수익은 /go/ 링크 작동+알리 whitelist 후) | #13 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsalim.com** (만료 2027-05-28·Auto Renew·SSL Active) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **e763e0f (#13)**, 배포됨. **build-and-deploy 워크플로 #13 재작성: main push → 커밋된 build/site를 Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB는 로컬). 배포 success 확인** + CodeQL · lint · security(월간 pip-audit) ✅. ※로컬 main worktree(D:\affiliate_hub)는 7b572ad로 뒤처짐 — 다음 세션 pull 권장 |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v1) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\honsalim.env`** (GOOGLE_API_KEY, 세션 #9 사용자 보안 결정 — secrets/ 바로 아래 단일 파일) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY | 영구 [확정 — 공개 키] | 회전 불요 |
| GitHub PAT | 미발급 (Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **App Key/Secret·라이브 검증 완료** [확정]. honsalim.com whitelist('ali' 오탐) — **2채널 제출 완료, 답변 대기** [확정 #13]: ①이메일(새벽 affiliates@service.alibaba.com) ②**포털 XFeedback(스크린샷 증거 포함, My Feedbacks 상태 "To do")**. 사이트 라이브 상태로 제출. 사이트등록폼은 'ali' 자동검증으로 Submit 불가 → 사람 화이트리스트만 길. 무응답 3~4영업일 시 follow-up | 2026-05-30 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션 #15) — #14 갱신 (상세: DECISIONS O · `docs/CATEGORY_PAGE.md` §6)
0. **용어 일상화 배포 반영 확인**: #14 커밋 build/site(시나리오→세팅)가 Actions 배포로 honsalim.com에 실제 반영됐는지.
1. **★페이지 재설계 본구현 (최우선, 자동화)**: ① 콘텐츠 파이프라인(혼살다 명의 8요소 자동작성+진실성 게이트, enrich 개편) ② 카테고리별 **2티어 수집**(실속/고급 가격밴드 — `search_keywords.yml` 정형화) ③ 수집기 `target_original_price`·`discount` 필드+DB 컬럼 + **가격 빌드시 재조회**(드리프트 가드) ④ **렌더러에 category 템플릿 이식**(프로토타입 = `scripts/category_page_prototype.py`) ⑤ **"더 많은 제품 보기"(전체 제품)** 필터·정렬 리스트 페이지.
2. **★/go/ 제휴 링크 작동** — D1 slug_map 쓰기 + go_gateway Worker 배포(deny-list라 사람/CI). 수익 직결, 보류.
3. (확인) 알리 이미지 허용(affiliates@ 채널) · **네이버 폰트 NanumSquare Neo 확정**(Chrome 연결 시 직접 inspect) · 알리 whitelist 답변 · main-protect 재활성화.

### 해소 (세션 #13)
- ~~게시 경로 배선~~ ✅ promote CLI(article_products 연결)·renderer 상세글·article.html 실데이터화 → **첫 글 honsalim.com 라이브 게시**
- ~~무인 배포 파이프라인~~ ✅ 방법 A(build/site 커밋·Actions 배포, 배포 success 확인) · ~~codeql v3→v4~~ ✅ · ~~문서 cap/stale 정정~~ ✅
- **근본 수정**: d1_aggregator `clicks.timestamp→ts`(라이브 집계 실패 버그) · extract_disclosure_first 제휴처 무관(알리 글 None→promote NOT NULL 위반 잠복버그) · renderer LF(CRLF churn)
- 잔존 워크트리 5개·#12 병합건은 위 #13 시급 4·5 참조

### Phase 2 진척 가능 (검토 의존 큼)
- `src/builder/manifest.py` 증분 빌드 (ARCH §7·DB §10) · `src/collector/coupang.py` (Phase 4)
- (이전 해소분 #7·#9·#10·#12는 EVENTS archive 참조)

### Phase 1 잔존 (작음)
- Actions status check Branch Protection 추가 (Phase 2 안정 후)
- BitLocker 활성 (사용자 결정)
- (완료) 알리 Tracking ID·App Key/Secret 발급·ali.env 저장·라이브 검증 — 2026-05-30

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
