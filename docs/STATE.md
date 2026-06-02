# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#20: ★카테고리 4개 라이브 배포 + 홈 카테고리우선 大리디자인 + 버그 4종 근본수정** (origin/main 배포 완료). 카테고리 배포(옛 #13 글 제거)·이미지 누락 근본수정·산출물 청소 버그·wrangler 커밋메시지(CF 8000111)·HTML캐시 fix / **홈**: 히어로 대표이미지·기획전 캐러셀·BEST·딜·테마·신뢰·구매가이드(/guides/)·섹션간격·사업자표기/이메일. 회귀 **632**. 상세 EVENTS #20 | 2026-06-02 #20 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **632 / 632 PASS** [확정 pytest, #20] — #20 +9 (이미지 lazy/eager·onerror 가드·산출물 청소 가드·배포 워크플로 commit-message 가드·홈 BEST/딜/테마 렌더·HTML캐시·사업자 숨김·/guides/ 핵심페이지). #19 623. black·ruff·mypy 클린 | 2026-06-02 |
| CLI 명령 (BACKEND §9) | **18개** — doctor · db · collect · collect-products · enrich · validate · approve · promote · unapprove · deploy · sync-slugmap · build(+`--preview` draft포함 미리보기, #18) · dashboard · collect-category · build-category · **approve-category(#18 신규: draft→published 1클릭 승인)** · **unapprove-category(#18 신규: 공개 취소)** | #18 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**5**: 의자·책상·모니터받침대·**노트북거치대·모니터암**)·category_products + products 정가/할인·**판매량(sales_volume)/만족도(evaluate_rate)** 컬럼 (migration 002~**006**, #19) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #19 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **★카테고리 4개 라이브** (honsalim.com/categories/ + 노트북거치대·컴퓨터책상·모니터받침대·모니터암, #20 배포 성공·옛 #13 글 제거) + **홈 카테고리우선 리디자인 라이브**(/honsalim-end #20 배포분) + /guides/·/about/ / N/A / N/A (수익은 **/go/ 링크 작동**+알리 whitelist 후 — 미작동) | #20 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsalim.com** (만료 2027-05-28·Auto Renew·SSL Active) |
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

### ★ 시급 (다음 세션 #21) — 사용자 지시: **홈페이지 완성도 우선(제품 대량등록 아님)** → "제법 홈페이지 같다" 판단 시 제품 등록. 상세 EVENTS #20.
1. **★미충전 이미지 전부 채우기** (사용자 핵심 지시): 이미지 자리는 있는데 비어있는 곳을 다 채워 "페이지 다운(=완성된) 모습" 만들기. 확인된 곳: **`/about/` 페이지 우측 히어로 아트(about.html — 회색 placeholder)**. 점검 필요: scenario_card·persona·season 등 `image_block(var(--wood-N))` placeholder 다수. (홈 hero/about·카테고리 개념이미지는 이미 채움). → 개념이미지 파이프라인(`enricher/concept_image.generate_concept_image`, Imagen 4:3/16:9, ~$0.02/장)로 생성.
2. **★제품 등록 준비 — 수익 카테고리 리스트화 + 순차 자동 적용**(사용자 지시): 미리 수익 카테고리(제품 선택)를 선별해 **리스트**로 만들고, 그 리스트를 **순차적으로 자동 등록**(`collect-category`→`build-category` 반복)되게 설계. 알리+쿠팡 둘 다 등록 예정이라 우선 구조부터.
3. **★/go/ 제휴 링크 작동**(D1 slug_map·go_gateway 워커) — 제품 클릭·수익 직결. 무인 자동등록 전 필수 골격(현재 미작동·정적 audit 제외).
4. **office-chair 콘텐츠 생성**: 제품 0 — `collect-category office-chair`→`build-category`.
5. (이월) 알리 whitelist 답변 · 쿠팡 파트너스 재가입(Phase 4) · 무인 발행 스케줄러(매일 11시, Phase 2) · main-protect.
- ★**홈 大리디자인 코드는 #20에서 origin/main 배포 완료** — 다음 워크트리(origin/main 기준)에 그대로 이어짐. **DB는 gitignore→다음 워크트리에서 4개 카테고리 `collect-category` --no-dry-run + `build-category` --no-dry-run 재생성 필요**(API ~$1). 워크트리 실행=`PYTHONPATH=src python -m cli`. 미리보기=`build --preview`(draft포함)·공개=`build --full`. CSS 변경 확인 시 강력새로고침(Ctrl+Shift+R).

### 해소 (세션 #20) — 상세 EVENTS #20
- ✅ 카테고리 4개 배포 · '전화' 제외 · 이미지 누락 근본수정(lazy+스크린샷) · 산출물 청소 버그 · wrangler 커밋메시지(8000111)·HTML캐시 fix · **홈 카테고리우선 大리디자인** · 구매가이드(/guides/, 내부링크 0 broken) · 사업자표기 정직화·이메일. 회귀 632(+9 가드).

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
