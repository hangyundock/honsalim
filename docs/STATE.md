# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#30: A 키워드 알리 영어검색 근본수정 + doctor 게이트 복구 + B 진행표시 + ★첫 라이브 글 발행 + 발행버그 적발 + 글 레이아웃 Tier1·★Tier2 종합 재설계** — A(`_gather_keyword_candidates`→`category_collect.search_tiers` 영어 티어, 미매핑 fail-closed)·doctor(`_load_module_from_path` sys.modules→exit 0)·B(`run_task` 진행바·상태·버튼). **첫 라이브 글=honsallim.com/articles/kw-e3d08a2c/(200·하이브리드 10상품)**. main 머지 3471248·7cb0168. 회귀 **851**. ★**적발: ①발행 build/site 커밋 버그(클릭만으론 404) ②file:// 미리보기 무스타일 ③글이 "텍스트벽=독서"→Tier2 블루프린트 확정(docs/ARTICLE_LAYOUT_TIER2.md)**. ★다음(#31)=글 레이아웃 Tier2 구현·발행버그 수정·미리보기 HTTP. 상세 EVENTS #30 | 2026-06-15 #30 |
| 운영 모델 | 자동 게시 활성(콘텐츠 큐). **refresh-cycle = 수동 운영(주인 직접 지시) — C13 [확정 #24], Claude 예약작업 비활성화**. 자동 "승인" 금지(E7→가드레일) | #24 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **851 / 851 PASS** [확정 pytest, #30] — #30 +5(A search_tiers·doctor 로더·B 진행표시) · #29 +40(미리보기 draft·적합성 가드·발행후 안전망). black·ruff·mypy 클린 | 2026-06-15 |
| CLI 명령 (BACKEND §9) | **29개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23)** · **#25 운영 대시보드: keyword-add·keyword-generate·keyword-list·reject·coupang-add·publish-queue·schedule** · **#26: keyword-recommend** · **#29: unpublish-article·republish-article·monitor-articles(발행후 안전망)·auto-cycle(무인 사이클·auto_mode ON일 때)** = **33개** | #29 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK [#29 +keyword_relevance·article_state×2·article_guardrail×2·auto_approve] | #29 |
| DB 초기화 | `data/honsalim.db` **v7** + categories(**5**)·category_products + products 정가/할인·판매량/만족도 + **keyword_queue(발행 큐·migration 007·drafts.keyword_id, #25)** (migration 002~**007**) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #25 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 공개 카테고리=5개** + **★첫 정식 글 1편=게이밍의자(honsallim.com/articles/kw-e3d08a2c/·#30·하이브리드 쿠팡1+알리)**. 글=새내기자취생 페르소나에서 링크(카테고리 페이지엔 안 나옴=정상·글≠카테고리). + 쿠팡 승인용 `/reviews/`. ★**현 라이브 글 레이아웃=구버전(텍스트벽)→#31 Tier2로 갱신 예정**(docs/ARTICLE_LAYOUT_TIER2.md). 측정(Cloudflare·GSC·네이버 누적). 수익=/go/→302 알리. `mini-dehumidifier` 가드레일 미달 자동비공개(점검 이월). collector.coupang(API)=15만원 후 | #30 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#29 (6f752d2 · B-i 무인 자동발행 + naver_blog GUI)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. #20 배포 success(run #39·#40) + CodeQL·lint ✅. ★**wrangler `pages deploy`에 `--commit-message=honsalim-auto-deploy`(ASCII)+`--commit-dirty=true` 명시** — git 한글 커밋메시지 CF 거부(code 8000111) 근본수정. ※로컬 main worktree는 뒤처짐 — 다음 워크트리는 origin/main 기준 |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v6) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\honsalim.env`** (GOOGLE_API_KEY) + **`D:\secrets\.env` OPENROUTER_API_KEY** (K-Content 공유 — DeepSeek 본문생성 경유, 세션 #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY | 영구 [확정 — 공개 키] | 회전 불요 |
| GitHub PAT | 미발급 (Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: honsallim 채널 + **`ALI_TRACKING_ID=honsallim`(ali.env·주인 직접)** → 수집 시 제품별 promotion_link 생성 → **247개 개별 deeplink**(#21 공통링크 한계 해소, affiliate_tag=honsallim 검증). `/go/`→302 알리 라이브 작동 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 다음 세션 #31 — 상세 EVENTS #30 / docs/ARTICLE_LAYOUT_TIER2.md
1. **★글 레이아웃 Tier2 구현 (최우선)**: 글을 "독서(텍스트벽)"→"쇼핑(스캔)"으로 — 빠른결론박스·큐레이션 픽카드·비교표·체크박스·예산표·FAQ아코디언. LLM 구조화 출력 + 템플릿 시각 컴포넌트(카테고리 재사용). **목업 먼저 확정**. ★중복콘텐츠 회피(글=시나리오 큐레이션, 카테고리=전체 카탈로그·의도 분리). 전체 스펙=**docs/ARTICLE_LAYOUT_TIER2.md**.
2. **★발행 build/site 자동커밋 버그**: `cmd_publish_queue`/`cmd_deploy`가 build/site 커밋 안 함→클릭만으론 404. 자동 커밋 단계 추가(무인 치명).
3. **미리보기 file://→HTTP 서빙**: 미리보기 버튼이 절대경로 CSS/이미지를 file://로 못 띄움(무스타일). 로컬 HTTP 서빙으로 개선.
4. (이월) PartC 키워드 틈점수 · off-target 씨앗 curation · mini-dehumidifier 점검 · ★성장 Tier0([[growth-first-priority]]).
- ★DB gitignore→재생성(`db migrate`+`db seed`). 발행/배포=main 체크아웃(C13). 워크트리=`PYTHONPATH=src python -m cli`. main직접머지=`git push origin HEAD:main`.

### Phase 2 진척 가능 (검토 의존 큼)
- `src/builder/manifest.py` 증분 빌드 (ARCH §7·DB §10) · `src/collector/coupang.py` (Phase 4)

### Phase 1 잔존 (작음)
- Actions status check Branch Protection 추가 (Phase 2 안정 후)
- BitLocker 활성 (사용자 결정)

### 보류
- AdSense 신청 (Phase 6, 2026-12)
- 영어 사이트 확장 (Phase 6 검토)
- 보조 호스팅 GitHub Pages (Phase 4 검토)

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
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
