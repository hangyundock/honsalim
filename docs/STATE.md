# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#25: ★운영 대시보드 전면 구축(PyQt5)** — 키워드 큐(migration 007)·글 생성·1클릭 승인·예약 발행(schtasks·E7 준수)·쿠팡 수동 등록(공식 위젯/텍스트)·설정창 + 바탕화면 아이콘. 회귀 **773**(+80). ★다음(#26)=**(1)대시보드 라이브 첫 글 생성 확인(DeepSeek 비용·품질) (2)아이콘 main 재지정 (3)★원래 #25 미완: mini-dehumidifier 점검·쿠팡 본격·성장 Tier0+측정**. 상세 EVENTS #25 | 2026-06-14 #25 |
| 운영 모델 | 자동 게시 활성(콘텐츠 큐). **refresh-cycle = 수동 운영(주인 직접 지시) — C13 [확정 #24], Claude 예약작업 비활성화**. 자동 "승인" 금지(E7→가드레일) | #24 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **773 / 773 PASS** [확정 pytest, #25] — #25 +80 (운영 대시보드: settings·migration007·keyword_queue·dashboard queries/app smoke·cli keyword·publish_queue·scheduler·coupang_manual). #24 693. black·ruff·mypy 클린 | 2026-06-14 |
| CLI 명령 (BACKEND §9) | **28개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23)** · **#25 운영 대시보드: keyword-add·keyword-generate·keyword-list·reject·coupang-add·publish-queue·schedule** | #25 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v7** + categories(**5**)·category_products + products 정가/할인·판매량/만족도 + **keyword_queue(발행 큐·migration 007·drafts.keyword_id, #25)** (migration 002~**007**) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #25 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 공개 카테고리=5개**(honsallim.com·#24 refresh-cycle 배포). **`mini-dehumidifier`는 가드레일 미달(추천 1개<2)로 자가복원 자동 비공개** — #25 원인 점검 대상. + 쿠팡 승인용 `/reviews/` 리뷰페이지(흠플래닛 모니터암). 측정(Cloudflare·GSC·네이버 누적). 수익=/go/→302 알리. **쿠팡=가입 착수·collector.coupang 미구현** | #24 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#20 (홈 리디자인 포함)**, 배포됨. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. #20 배포 success(run #39·#40) + CodeQL·lint ✅. ★**wrangler `pages deploy`에 `--commit-message=honsalim-auto-deploy`(ASCII)+`--commit-dirty=true` 명시** — git 한글 커밋메시지 CF 거부(code 8000111) 근본수정. ※로컬 main worktree는 뒤처짐 — 다음 워크트리는 origin/main 기준 |
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

### ★ 다음 세션 #26 — 상세 EVENTS #25.
0. **운영 대시보드 실전화**: (a) **라이브 첫 글 생성 1회**(DeepSeek 비용·품질 확인 — 구조/라우팅만 검증) (b) **바탕화면 아이콘 main 재지정**(현재 워크트리→`D:\affiliate_hub`, 머지 후) (c) 설정 일부(쿠팡 모드/임계·llm_model·seo_max_attempts·jitter) 코드 연결.
1. **`mini-dehumidifier` 점검**: 추천 1개(<2)로 가드레일 자가복원→라이브 비공개. 추천 풀 부족 원인 확인 후 복원/보강.
2. **★★쿠팡 본격 (주인 명시)**: 이제 **대시보드 수동 등록**(coupang-add·공식 위젯/텍스트)으로 즉시 시작 가능 → 누적 15만원 후 `collector.coupang`(API) 구현. 쿠팡=메인(§6).
3. **멀티채널 배치 구현 (DECISIONS S1·S2)**: C안. 게이팅=쿠팡 + 1~2주 트래픽 데이터 후.
4. **★성장 Tier0 지속 (DECISIONS T1·T2 · [[growth-first-priority]])**: 측정(GSC·네이버·Cloudflare) 리뷰→더블다운. Tier1 Pinterest.
- ★**DB는 gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run --auto-publish`, ~$2). refresh-cycle·대시보드 발행/배포는 **main 체크아웃**에서(C13 수동).

### 해소 (세션 #25) — 상세 EVENTS #25
- ✅ **운영 대시보드 전면 구축(A~F)**: 설정 외부화 + 키워드 큐(migration 007) + PyQt5 GUI(키워드/글/모니터링/설정) + 키워드 글 생성·1클릭 승인·예약 발행(schtasks·E7·기본 OFF) + 쿠팡 수동 등록(공식 위젯/텍스트) + 설정창 + 바탕화면 아이콘. 회귀 693→773.

### 해소 (세션 #24) — 상세 EVENTS #24
- ✅ **멀티채널·무인마케팅 전략 확정(DECISIONS S·T)** · **쿠팡 승인용 `/reviews/`** · **Tier0 SEO 품질강화·필러** · **refresh-cycle 첫 라이브(자가복원 실증)** · **subprocess UTF-8 근본수정(run_text·회귀 693)** · **스케줄러 수동전환(C11 폐기→C13)**.

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
