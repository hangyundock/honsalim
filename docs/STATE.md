# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#31: ★카테고리 분류 체계(대/중/소) 구축 + 게이밍의자→'의자' 타입 흡수 + 쿠팡 운영자추천 zone·정식 대가성 + 추천 8선 + 라이브 배포** — 제품 종류(게이밍 등)=별도 카테고리 아닌 **타입 필터**(Baymard 과잉카테고리화 회피). office-chair→**"의자"**(사무용+게이밍 흡수, 타입=제품명 `_derive_type`). 인덱스 재설계(대분류·썸네일·타입칩), **category.html 재사용**. 쿠팡 상단 운영자추천 zone·정식 대가성(상단+옆·함정#4). 게이밍의자 글 **비공개+301 리다이렉트**(`_redirects`). 회귀 **851 유지**. main 직접푸시 **ea2460e**→CI 배포·라이브 검증(honsallim.com/categories/·office-chair). ★**다음 최우선(#32)=운영 DB 반영**(이 세션 승인 상태=의자·8선·LLM 가이드가 **워크트리 복사본 DB에만**·운영 DB 미반영). 상세 EVENTS #31 | 2026-06-15 #31 |
| 운영 모델 | 자동 게시 활성(콘텐츠 큐). **refresh-cycle = 수동 운영(주인 직접 지시) — C13 [확정 #24], Claude 예약작업 비활성화**. 자동 "승인" 금지(E7→가드레일) | #24 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **851 / 851 PASS** [확정 pytest, #31] — #31(카테고리 분류체계·타입필터·쿠팡 zone·301 리다이렉트 코드 — 테스트 수 유지) · #30 +5(A search_tiers·doctor 로더·B 진행표시). black·ruff·mypy 클린 | 2026-06-15 |
| CLI 명령 (BACKEND §9) | **29개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23)** · **#25 운영 대시보드: keyword-add·keyword-generate·keyword-list·reject·coupang-add·publish-queue·schedule** · **#26: keyword-recommend** · **#29: unpublish-article·republish-article·monitor-articles(발행후 안전망)·auto-cycle(무인 사이클·auto_mode ON일 때)** = **33개** | #29 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK [#29 +keyword_relevance·article_state×2·article_guardrail×2·auto_approve] | #29 |
| DB 초기화 | `data/honsalim.db` **v7** + categories(**5**)·category_products + products 정가/할인·판매량/만족도 + **keyword_queue(발행 큐·migration 007·drafts.keyword_id, #25)** (migration 002~**007**) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #25 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 공개 카테고리=5개**(office-chair="**의자**"=사무용+게이밍 타입 필터·쿠팡 운영자추천 zone·추천 8선, #31). **정식 글 0편**(게이밍의자 글 #30→#31 '의자' 카테고리로 흡수·비공개+301 리다이렉트·종류=타입). + 쿠팡 승인용 `/reviews/`. 측정(Cloudflare·GSC·네이버 누적). 수익=/go/→302 알리. `mini-dehumidifier` 가드레일 미달 자동비공개(점검 이월). collector.coupang(API)=15만원 후 | #31 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#31 (ea2460e · 카테고리 분류체계+게이밍의자 흡수+쿠팡 zone)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. #20 배포 success(run #39·#40) + CodeQL·lint ✅. ★**wrangler `pages deploy`에 `--commit-message=honsalim-auto-deploy`(ASCII)+`--commit-dirty=true` 명시** — git 한글 커밋메시지 CF 거부(code 8000111) 근본수정. ※로컬 main worktree는 뒤처짐 — 다음 워크트리는 origin/main 기준 |
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

### ★ 다음 세션 #32 — 상세 EVENTS #31
1. **★★운영 DB 반영 (최우선·중요)**: 이 세션 승인 상태(의자 카테고리·추천 8선·LLM 가이드)는 **워크트리 복사본 DB(`data/honsalim.db`)에만** 있고, 운영 DB(`D:\affiliate_hub\data\honsalim.db`)는 미반영(옛 상태·mtime 03:22 무변동). **워크트리 폐기 시 복사본 소멸 → 반영 필수.** 대시보드 닫고 백업 후 ①`scripts/apply_chair_taxonomy.py D:\affiliate_hub\data\honsalim.db`(rename·absorb·unpublish 멱등) + `build-category office-chair --no-dry-run`(LLM 재생성) + `approve-category office-chair`, OR ②복사본을 sqlite backup으로 운영 이식(승인 콘텐츠 그대로·권장). ※라이브(build/site·ea2460e)는 이미 배포·정상 — 운영 DB는 다음 빌드 일관성용.
2. **부산물 정리**: `_fix_tax.py`(워크트리 루트 임시·삭제 가드 막힘) 제거 · abandoned `article.html`/`article.css`(카테고리 모방·0 published라 무해) 정리 검토 · `category_products.product_type` 컬럼(복사본만·미사용).
3. (선택) 다른 카테고리(책상 등) 추천 8선 재빌드 · 모니터암·모니터 받침대 "모니터 거치"로 묶기.
4. (이월) PartC 키워드 틈점수 · mini-dehumidifier 점검 · ★성장 Tier0([[growth-first-priority]]).
- ★DB gitignore→재생성. 발행/배포=main 체크아웃(C13). 워크트리=`PYTHONPATH=src python -m cli`. main직접머지=`git push origin HEAD:main`. ★PowerShell 한글 파이프 깨짐→.py 파일 실행([[powershell-korean-encoding]]).

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
