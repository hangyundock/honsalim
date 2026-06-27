# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#38: ★완전무인 첫 라이브 발행(0-falsy 버그 근본수정) + 빈글차단 + 무인 표준 문서화 + 글/카테고리 정형화·featured 8 통일** — ①`auto_approve_min_published=0`(완전무인)이 `0 or 5=5`로 강제돼 완전무인 영구 차단하던 치명 버그→`settings.get_int/get_float`(0 보존) ②키워드+쿠팡 적재→예약 auto-cycle→자동 생성·승인·발행→`honsallim.com/articles/kw-625b3b85` 라이브 **무인 첫 성공** ③빈 글(상품0 키워드) LLM 호출 전 차단 ④무인 표준 순서 `docs/AUTOMATION.md`·CLAUDE.md §7(★키워드 선정도 자동) ⑤글이 자기 상품 렌더(쿠팡3·상단8·비교8)·featured 8 통일(글+카테고리 6개 LLM 재빌드 라이브) ⑥무인 토글+9초 프리징·추천 다중선택·카테고리 보기 경로. 회귀 950→**961**. main 푸시. 상세 EVENTS #38 | 2026-06-27 #38 |
| 운영 모델 | **★완전무인 가동 ON (#38 주인 결정·C13 수동운영 뒤집음)**: auto_mode ON·예약 **19:15 KST**·`auto_approve_min_published`=**0**(첫 글부터 자동승인). 키워드+쿠팡 적재→스케줄 auto-cycle 자동 생성·승인·발행→무관여. 발행글 사후 검토(발행 글 관리 탭 + monitor 자동비공개 2겹). 자동 "승인" 금지(E7)는 min_published로 완화—주인 0 선택 | #38 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **961 / 961 PASS** [확정 pytest, #38] — #38 +8(빈글차단·0-falsy 5건·글정형화 2건·featured 통일) · #37 +3 · #36 +18. black·ruff·mypy 클린 | 2026-06-27 |
| CLI 명령 (BACKEND §9) | **29개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23)** · **#25 운영 대시보드: keyword-add·keyword-generate·keyword-list·reject·coupang-add·publish-queue·schedule** · **#26: keyword-recommend** · **#29: unpublish-article·republish-article·monitor-articles·auto-cycle** · **#32: keyword-delete·category-coupang-add/list/remove·build-deploy** · **#35: suggest-categories·provision-category(자동 카테고리)** = **40개** | #35 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK [#29 +keyword_relevance·article_state×2·article_guardrail×2·auto_approve] | #29 |
| DB 초기화 | `data/honsalim.db` **v9** + categories(**9**: +mini-rice-cooker)·category_products + products 정가/할인·판매량/만족도 + keyword_queue(#25) + articles.structured_json(#34) + **api_usage(Google Imagen 사용량·추정비용·migration 009, #36)** (migration 002~**009**) + personas 3·scenarios 10. ★**대시보드 시작 시 자동 migrate**(#34·무명령). ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #36 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 공개 카테고리=6개**(의자·컴퓨터책상·모니터받침대·모니터암·도마·미니밥솥) — **#38 전부 featured 8(추천)·비교 8 통일·LLM 재빌드·승인·라이브 검증**. **정식 글 1편**(kw-625b3b85 '모니터받침대' = #38 ★무인 자동발행 첫 성공·쿠팡3·상단8·비교8). + 쿠팡 승인용 `/reviews/`. 측정(Cloudflare·GSC·네이버). 수익=/go/→302 알리/쿠팡. 대표이미지 6/6. collector.coupang(API)=15만원 후 | #38 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#37 (a5930c6 · 발행 글 관리 탭=무인 발행 사후검토)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. ★**빌드·배포는 `cmd_build_deploy`(refresh_cycle)가 build/site·functions/go를 commit+push** — `deployer.git_push` stub의 '미커밋' 버그 근본 우회(#32). wrangler `--commit-message`(ASCII)+`--commit-dirty` 유지. ※**운영 폴더(D:\affiliate_hub)는 #34(e9e3fd2)로 git pull 동기화함**(이번 세션·clean FF·13커밋). 워크트리는 origin/main 기준 |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v6) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\affiliate_hub\GOOGLE.env`** (GOOGLE_API_KEY — #37 `review-helpfulknow` 프로젝트로 분리=티스토리 한도 독립. ※상위 `D:\secrets\honsalim.env`는 코드 미사용) + **`D:\secrets\.env` OPENROUTER_API_KEY** (K-Content 공유 — DeepSeek 본문생성 경유, 세션 #19) |

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

### ★ 다음 세션 #39 — 상세 EVENTS #38
1. **★무인 운영 지속 관찰**(핵심): auto_mode ON·예약 19:15·min_published=0 가동 중 → **매일 자동 발행되는 글 품질 사후 검토**(발행 글 관리 탭 라이브 확인·monitor 자동비공개 2겹 그물). 키워드/쿠팡 큐 적재 보충(고갈 시 추천 자동보충되나 의도 키워드 관리). 무인 표준 순서=`docs/AUTOMATION.md`(매 세션 필독·키워드 직접입력/글 먼저생성 안내 금지).
2. (이월) `review-helpfulknow` 월 지출 한도(무인 폭주 방지·선택) · 쿠팡 수동 배너 부트스트랩(15만원→API) · `mini-dehumidifier` 점검 · ★성장=트래픽(GSC 색인·[[growth-first-priority]]).
- 워크트리=`PYTHONPATH=src python -m cli`. DB gitignore→재생성(대시보드 시작 시 자동 migrate). main직접머지=`git push origin HEAD:main`. ★PowerShell/cmd 한글→.py·ASCII([[powershell-korean-encoding]]). 운영 DB 직접수정 불가→주인 런처(#32 패턴·`D:\honsalim_test\*.bat`).

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
