# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#24: ★쿠팡 가입+승인 데모 + 멀티채널 배치설계(C안) + 무인 마케팅 정밀기획(T) + Tier 0 SEO 라이브**. 쿠팡 파트너스 가입 완료(승인 심사 대기·`/reviews/` 데모). 알리+쿠팡 배치=C안(채널별 최선·정성 기준·가격 위임·DECISIONS S). 무인 마케팅=SEO본진+Pinterest(DECISIONS T·버너양산 거부). Tier 0 라이브: `/method/`·카테고리 데이터요약·**홈오피스 필러 `/home-office/`**·핸즈온 미채택 정직화. 회귀 **690**. ★다음=**(1)쿠팡 승인→collector.coupang (2)Pinterest (3)필러 노출강화 (4)성장 측정**. 상세 EVENTS #24 | 2026-06-03 #24 |
| 운영 모델 | 자동 게시 활성 + **무인 사이클(refresh-cycle·매일 11:00 KST 예약작업) — #23 머지 후 가동**. 자동 "승인" 금지(E7→가드레일) | #23 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **690 / 690 PASS** [확정 pytest, #24] — #24 +12 (리뷰페이지·method 페이지·카테고리 데이터요약/링크·홈오피스 필러 가드). #23 678. black·ruff·mypy 클린 | 2026-06-03 |
| CLI 명령 (BACKEND §9) | **21개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23: 무인 새로고침→자가복원→빌드→변경분 배포, 기본 dry_run, 매 실행 후 대시보드 갱신)** | #23 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**5**: 의자·책상·모니터받침대·**노트북거치대·모니터암**)·category_products + products 정가/할인·**판매량(sales_volume)/만족도(evaluate_rate)** 컬럼 (migration 002~**006**, #19) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #19 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브(#24)=카테고리 6 공개**(보류 2 자연 비공개) + **`/method/`(방법론·E-E-A-T)** + **`/home-office/` 필러**(토픽 허브) + **`/reviews/` 쿠팡 데모**(noindex). 각 카테고리 '데이터로 본 N' 요약+수집일+제품명/가격 링크. 측정(Cloudflare·GSC·네이버 1~2주 누적). 수익=/go/→302 알리·172개 + **쿠팡 가입완료·승인 대기**(collector.coupang 미구현) | #24 |

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
| 쿠팡 파트너스 | **가입 완료·승인 심사 대기 [#24]** | honsallim.com 채널 등록 + 승인용 `/reviews/honplanet-monitor-arm/` 데모 배포·스샷 등록. 승인 후 `collector.coupang` 구현. 최종 정산엔 누적 15만원 조건 [관찰] |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 다음 세션 #25 — 상세 EVENTS #24.
1. **★★쿠팡 승인 대기 → 승인 시 `collector.coupang` 구현**(현재 stub→쿠팡 상품 수집). 승인 메일/마이페이지 알림 확인. 쿠팡=메인 채널(§6). 최종 정산엔 누적 15만원 조건 [관찰].
2. **★Tier 1 Pinterest** ([[growth-first-priority]]·DECISIONS T1): 개인정보처리방침 페이지 + Pinterest Standard API 승인 → 자동 핀(→리뷰페이지 유도·첫머리 고지·절제). 무인 마케팅 1순위 자동화 채널.
3. **필러 노출 강화**: 홈/구매가이드 → `/home-office/` 눈에 띄는 링크 (현재 sitemap·카테고리 백링크만).
4. **알리+쿠팡 배치 C안 구현** (DECISIONS S): 쿠팡 상품 생기고 1~2주 트래픽 데이터 후 확정.
5. **#23 무인 스케줄러 가동 확인**(미검증) + 성장 측정 리뷰(GSC·네이버·Cloudflare).
- ★**DB는 gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run --auto-publish`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. ★**배포=워크트리 브랜치 push → GitHub PR 병합**(하니스가 main 직접 push·PR 생성 차단 — 세션 #24 패턴). 엣지캐시 5분(배포 반영 지연).

### 해소 (세션 #24) — 상세 EVENTS #24
- ✅ 쿠팡 가입+승인 데모 배포 · 알리+쿠팡 배치설계(C안·DECISIONS S) · 무인 마케팅 정밀기획(DECISIONS T) · Tier 0 SEO(방법론 `/method/`·카테고리 데이터요약·홈오피스 필러 `/home-office/`) 라이브 · 핸즈온 미채택 정직화(method·about) · 보류 2개 자연 비공개(공개 6). 회귀 690.

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
