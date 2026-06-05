# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#25: ★쿠팡 채널 통합(`collector.coupang` 수동 부트스트랩) + 모니터암 이미지 그리드 라이브검증**. 쿠팡 '블로그용 HTML'→`coupang_products.yml`→적재(prune)→알리와 분리된 "쿠팡 로켓배송" 이미지 그리드(채널별 최선·S1)·채널인식 고지·`/go/` 작동·알리 가드(source 한정). 모니터암 쿠팡 **15개 이미지 라이브검증**. 회귀 **710**. ★다음=**광고 배치 구현(메인 첫화면 쿠팡 배너[주인 원안]+카테고리 결정지점), 효과=쿠팡 수익리포트(측정 시스템 안 만듦)**. ⚠쿠팡 API는 최종승인(**판매금액 15만원**, 수익금 아님) 후·브라우저 자동화는 정책 차단(수동 유지). 상세 EVENTS #25·DECISIONS U | 2026-06-06 #25 |
| 운영 모델 | 자동 게시 활성 + **무인 사이클(refresh-cycle·매일 11:00 KST 예약작업) — #23 머지 후 가동**. 자동 "승인" 금지(E7→가드레일) | #23 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **710 / 710 PASS** [확정 pytest, #25] — #25 +32 (coupang collect: 딥링크파싱·yml·매핑·적재·정합화prune·알리가드 + renderer 쿠팡 그리드·이미지·고지). #23 678. black·ruff·mypy 클린 | 2026-06-06 |
| CLI 명령 (BACKEND §9) | **22개** — …(21개)… refresh-cycle(#23) + **collect-coupang(#25: coupang_products.yml→products(source='coupang')+category_products 적재·정합화 prune, 기본 dry_run)** | #25 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **65개**(#25 +collector.coupang.collect_coupang) + #19 **LLM 키 점검**. 65/65 OK | #25 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**5**: 의자·책상·모니터받침대·**노트북거치대·모니터암**)·category_products + products 정가/할인·**판매량(sales_volume)/만족도(evaluate_rate)** 컬럼 (migration 002~**006**, #19) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #19 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback **8건**(#25 신규 [[assist-not-overstep]]: 월권·희망고문·과잉설계 금지 + [[no-speculation]] 보강) + reference market_research + MEMORY.md | #25 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브=카테고리 8개**(honsallim.com). 측정(Cloudflare·GSC·네이버 누적). 수익=/go/→302 알리·247개. **쿠팡 채널 통합 코드 완료(#25)·미배포** — 모니터암 쿠팡 15개 이미지 그리드 로컬검증. ⚠**현실: 신규 도메인=검색노출 거의 0, 트래픽이 진짜 병목**(신규 어필리 6~12개월 인내·대부분 실패). 다음=광고 배치+성장 | #25 |

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
1. **★광고 배치 구현 (#25 합의·DECISIONS U4)**: **메인 첫 화면 쿠팡 배너(주인 원안)** + 카테고리 **결정지점(추천·비교 직후)** 배치. 근거=위치>형태(ATF 고가치). **효과 검증=쿠팡 수익 리포트**(별도 클릭 측정 시스템 만들지 말 것·과잉). 구현 전 "이 코드 이렇게 바꾼다" 먼저 짧게 보고 후 진행.
2. **★성장이 진짜 병목 ([[growth-first-priority]])**: 신규 도메인=검색노출 거의 0. 트래픽 없으면 쿠팡 수익도 0(15만원 승인도 멈춤). Tier0 SEO 품질·롱테일·토픽클러스터(DECISIONS T2)부터. **현실적·정직하게**(희망고문 금지·[[assist-not-overstep]]).
3. **쿠팡 상품 추가 (수동 부트스트랩)**: 다른 카테고리에 쿠팡 상품 넣으려면 주인이 '블로그용 HTML' 붙여주면 처리(`coupang_products.yml` 추가→`collect-coupang`). ⚠브라우저 자동화는 정책 차단(재시도 금지·U3). 쿠팡 API는 판매 15만원→최종승인 후(U2).
4. (보류) 알리+쿠팡 배치 최종형은 1~2주 트래픽 데이터 후 확정(S2 게이팅).
- ★**DB는 gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run --auto-publish`+`collect-coupang --all --no-dry-run`, ~$2). 워크트리=`PYTHONPATH=src python -m cli`. ★이번 워크트리 브랜치=`claude/beautiful-neumann-eabaa8`(PR로 main 머지 필요).

### 해소 (세션 #25) — 상세 EVENTS #25
- ✅ **★쿠팡 채널 통합**(`collector.coupang`+CLI·이미지 그리드·채널인식 고지·알리 가드·`/go/`) · 모니터암 15개 라이브검증 · 최종승인 문턱 확인(판매 15만원) · 브라우저 자동화 시도→정책 차단 확인 · ★메모리 신규([[assist-not-overstep]]). 회귀 710.

### Phase 2 진척 가능 (검토 의존 큼)
- `src/builder/manifest.py` 증분 빌드 (ARCH §7·DB §10) · `src/collector/coupang.py` **API판(현재는 수동 부트스트랩만 구현·#25)은 최종승인 후**
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
