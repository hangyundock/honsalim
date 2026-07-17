# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ **#44: 무인 10일 침묵 정지 복구** — 운영 폴더가 07-07 detached HEAD로 이탈해 auto-cycle이 매일 조용히 안전 정지한 것을 `main` 복귀로 해소. 재발방지=안전정지 텔레그램 경보. ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#44: 무인 발행 침묵 정지 복구 + 안전정지 텔레그램 경보 + 발행 글 title 근본수정 + 게이밍의자 재발행(라이브)** — 무인이 07-08~17 10일 조용히 멈춘 것(detached HEAD) 적발·복구. 근본수정: ①안전정지 fail-loud 경보(`notify-alert`) ②발행 글 `<title>`=글 제목(카테고리 guide_title 상속 중복 해소) ③게이밍의자 301 폐기+재발행(노트북받침대는 유지). 부수: Qt 가이드 테스트 크래시 gate·mini-rice 이미지 커밋. 회귀 1043→**1051**. 상세 EVENTS #44·DECISIONS BB | 2026-07-17 #44 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT] 로그·텔레그램=하트비트+경보+발행 제목·URL). 자가복원 **3겹**(#41 게이트 반려+#42 생성 예외+**#44 안전정지 경보** `notify-alert`·래퍼 3정지지점 fail-loud). ★래퍼는 `main`일 때만 가동 — detached면 정지+경보([[autonomous-detached-head-silent-stop]]). E7 완화=min_published | #44 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **1051 PASS + 1 skip** [확정 pytest, #44] — #44 +8(notify-alert 5·title 2·guide field 1), 위젯 Qt 크래시 테스트 1 opt-in skip · #42 +6 · #41 +41. black·ruff·mypy 클린 | 2026-07-17 |
| CLI 명령 (BACKEND §9) | **42개** — 코어(doctor·db·collect·enrich·validate·approve·promote·build·deploy·dashboard) + 카테고리(collect/build/approve·provision-category 등) + 운영(keyword-*·keyword-requeue·coupang-add·publish-queue·schedule·auto-cycle·refresh-cycle·build-deploy·monitor-articles·un/republish-article·**notify-alert #44**) | #44 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK | #29 |
| DB 초기화 | `data/honsalim.db` **v9**(migration 002~009) + categories 9·category_products + products(정가/할인·판매량) + keyword_queue(#25) + articles.structured_json(#34) + api_usage(#36) + personas 3·scenarios 10. ★대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed`(+`collect-category`) 재생성 | #36 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 6개** + **정식 글 8편**(+#44: **서재책상**(7/17 무인 발행·제품28)·**게이밍의자**(kw-e3d08a2c 301폐기·재공개)). 발행 글 `<title>`=글 제목 정합(#44). 미발행 1편(노트북받침대=중복 유지). ★**색인(#40)**: GSC 4/네이버 4. ★**다음 레버=색인 커버리지↑**([[growth-first-priority]]) | #44 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#44 (8629c62 · 침묵정지 복구·경보·title·게이밍의자 재발행)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. ★**빌드·배포는 `cmd_build_deploy`(refresh_cycle)가 build/site·functions/go를 commit+push** — `deployer.git_push` stub의 '미커밋' 버그 근본 우회(#32). wrangler `--commit-message`(ASCII)+`--commit-dirty` 유지. ※**운영 폴더(D:\affiliate_hub)=main 8629c62 동기화**·★**반드시 main 브랜치 유지**(detached면 무인 정지·#44). 워크트리는 origin/main 기준 |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v6) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\affiliate_hub\GOOGLE.env`** (GOOGLE_API_KEY — #37 `review-helpfulknow` 프로젝트로 분리=티스토리 한도 독립) + **`telegram.env`(#41 — TELEGRAM_BOT_TOKEN·CHAT_ID = TIMA `D:\secrets\settings.json` 봇 재사용·무인 알림)** + **`D:\secrets\.env` OPENROUTER_API_KEY** (K-Content 공유 — DeepSeek 본문생성, #19) |

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

### ★ 다음 세션 #45 — 상세 EVENTS #44
1. **[관찰] #44 무인·경보 실전 확인**: ①내일(07-18) 11:11 auto-cycle이 `main`에서 정상 발행되는지(auto_cycle.log·텔레그램) ②안전 정지 경보가 실제 정지 시 텔레그램으로 오는지 ③발행 글 `<title>`=글 제목이 새 무인 글에도 유지되는지.
2. **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]): GSC/네이버 색인 **4→증가** 관찰. #44 title 정합·내부링크 효과 기대. 핵심 URL 색인 요청. 씨앗 커버리지 확장·E-E-A-T(about/Person Schema).
3. **(선택) 게이밍의자 글 구조 이관**: 옛 article.html 렌더(빵부스러기 '내맘대로 세팅')→신규 글식 카테고리 구조(28개 광폭 카탈로그·홈>카테고리>의자). 발행·기능엔 문제없음.
4. (이월) Phase 2 자가복원(ali off-target·배포 drift·git pull footgun)·review-helpfulknow 월상한·쿠팡 부트스트랩(15만원→API).
- ★**매 세션 시작 시 운영 폴더 브랜치 확인** `git -C D:\affiliate_hub branch --show-current`==main([[autonomous-detached-head-silent-stop]]). 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). main직접머지=cherry-pick 또는 `git push origin HEAD:main`. ★한글→.py·ASCII([[powershell-korean-encoding]]). 운영 DB 직접수정 불가→주인 런처. ★무인 발행이 origin 전진([[autonomous-deploy-advances-origin]]). ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

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
