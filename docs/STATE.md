# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#40: 성장 — 색인 토대 감사·정비(라이브 검증)** — 6차원 감사(코드+라이브)+적대검증. 근본수정: ①**발행 글 고아 해소**(시나리오 active=0 의존 깨짐→홈·가이드·토픽카테고리 내부링크) ②**Article JSON-LD 렌더 재생성**(canonical 끝슬래시·headline 일관) ③**사이트맵 lastmod**(발행글) ④**파비콘**(네이버 소프트404 `/favicon.ico`) ⑤**robots `/cdn-cgi/` 제외**(GSC 404). build-deploy 라이브 + curl 전수 검증. ★**GSC·네이버 둘 다 등록·사이트맵·크롤링 정상 확정**(감사 [확인불가] 해소)—병목=색인 커버리지. 회귀 989→**996**. main **a8697b8**. 상세 EVENTS #40 | 2026-06-28 #40 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약 **22:02 KST**·`auto_approve_min_published`=**0**. 키워드+쿠팡 적재→스케줄 auto-cycle 자동 생성·승인·발행→무관여. 발행글 사후검토(발행 글 관리 탭 + monitor 2겹) + **#39 무인 자기보고**(사이클 health 다이제스트 `data/auto_cycle_last.json` + 발행0편 위험 시 [ALERT] 로그·대시보드 미의존). 자동 "승인" 금지(E7)는 min_published로 완화—주인 0 선택 | #39 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **996 / 996 PASS** [확정 pytest, #40] — #40 +7(고아·JSON-LD/lastmod·favicon·robots) · #39 +28 · #38 +8. black·ruff·mypy 클린 | 2026-06-28 |
| CLI 명령 (BACKEND §9) | **40개** — doctor·db·collect·enrich·validate·approve·promote·build(+`--preview`)·deploy·dashboard · 카테고리(collect/build/approve/unapprove/register-categories·suggest-categories·provision-category) · 운영(keyword-add/generate/list/recommend·coupang-add·publish-queue·schedule·auto-cycle·refresh-cycle·build-deploy·monitor-articles·unpublish/republish-article·keyword-delete·category-coupang-*) | #35 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK [#29 +keyword_relevance·article_state×2·article_guardrail×2·auto_approve] | #29 |
| DB 초기화 | `data/honsalim.db` **v9** + categories(**9**: +mini-rice-cooker)·category_products + products 정가/할인·판매량/만족도 + keyword_queue(#25) + articles.structured_json(#34) + **api_usage(Google Imagen 사용량·추정비용·migration 009, #36)** (migration 002~**009**) + personas 3·scenarios 10. ★**대시보드 시작 시 자동 migrate**(#34·무명령). ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #36 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 6개** + **정식 글 2편**(kw-625b3b85 모니터받침대·kw-95e2ad52 무중력의자). #40 색인 토대 정비 라이브: 글 내부링크(고아 해소)·파비콘·JSON-LD·사이트맵 lastmod. ★**색인 현황(#40 확인)**: GSC 색인 **4**/미색인 29(robots 16=의도된 `/go/`·404 1=cdn-cgi 무해·**발견-미색인 12**=신생 정상·내부링크가 레버), 네이버 색인 4·**16노출/0클릭**(롱테일이 콘텐츠와 일치). ★**다음 레버=색인 커버리지↑**([[growth-first-priority]])—URL 색인 요청·내부링크 효과 1~2주 관찰 | #40 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#40 (a8697b8 · 색인 토대 정비)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. ★**빌드·배포는 `cmd_build_deploy`(refresh_cycle)가 build/site·functions/go를 commit+push** — `deployer.git_push` stub의 '미커밋' 버그 근본 우회(#32). wrangler `--commit-message`(ASCII)+`--commit-dirty` 유지. ※**운영 폴더(D:\affiliate_hub)=#40 a8697b8 동기화**(빌드·배포가 origin 전진→병합 후 ff pull). 워크트리는 origin/main 기준 |
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

### ★ 다음 세션 #41 — 상세 EVENTS #40
1. **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]): #40 배포(내부링크·favicon·robots)로 GSC/네이버 색인 페이지가 **4→증가**하는지 1~2주 관찰. 핵심 페이지 URL 색인 요청(GSC `URL 검사`·네이버 `웹 페이지 수집`). robots `/cdn-cgi/` 라이브 반영=다음 빌드·배포 시(무해·급하지 않음).
2. **[관찰] 무인 스케줄러 실작동 점검** — 대시보드 '무인 사이클 마지막 실행=**2026-06-06**' 표시. 22:02 자동 발행이 **실제 매일 도는지** 확인(미작동이면 '완전무인'인데 발행 0). #40 미점검.
3. (이월) 씨앗 커버리지 확장(seo_keywords.yml 미매핑)·E-E-A-T(about/Person Schema)·Phase 2 자가복원(ali off-target·배포 drift·푸시채널·git pull footgun)·review-helpfulknow 월상한·쿠팡 부트스트랩(15만원→API).
- 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). main직접머지=`git push origin HEAD:main`. ★PowerShell/cmd 한글→.py·ASCII([[powershell-korean-encoding]]). 운영 DB 직접수정 불가→주인 런처. ★무인 발행이 origin 전진([[autonomous-deploy-advances-origin]])—푸시 전 ff/merge. ★Edit 절대경로 = 운영 폴더(워크트리 아님) 주의([[worktree-edit-path-footgun]]).

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
