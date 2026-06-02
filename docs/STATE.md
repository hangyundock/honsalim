# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#21: ★도메인 honsalim→honsallim 이전·연결·301(알리 'ali' 차단 돌파) + 알리 채널 등록 + 미충전이미지·순차등록엔진(register-categories)·홈 흰바탕캐시 근본수정** (origin/main 배포). honsallim.com 라이브·SSL·**301 Page Rule**(경로보존). 알리 Portals honsallim 채널 등록(별도승인 없음). 페르소나/about/시나리오 이미지 채움(placeholder 0)·이미지 재사용. OpenRouter 잘림 자가복원·Windows wrangler `resolve_argv`·cache-busting(`?v=`). 회귀 **641**. ★살림 카테고리는 `loving-herschel` 갈래에만(미머지)→#22 합침. 상세 EVENTS #21 | 2026-06-02 #21 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **641 / 641 PASS** [확정 pytest, #21] — #21 +9 (cache-busting `?v=`·`common.proc.resolve_argv`·자가복원 RuntimeError·이미지 재사용·slug_map 카테고리 UNION·도메인 honsallim). #20 632. black·ruff·mypy 클린 | 2026-06-02 |
| CLI 명령 (BACKEND §9) | **18개** — doctor · db · collect · collect-products · enrich · validate · approve · promote · unapprove · deploy · sync-slugmap · build(+`--preview` draft포함 미리보기, #18) · dashboard · collect-category · build-category · **approve-category(#18 신규: draft→published 1클릭 승인)** · **unapprove-category(#18 신규: 공개 취소)** | #18 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**5**: 의자·책상·모니터받침대·**노트북거치대·모니터암**)·category_products + products 정가/할인·**판매량(sales_volume)/만족도(evaluate_rate)** 컬럼 (migration 002~**006**, #19) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #19 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **★카테고리 5개 라이브** (**honsallim.com**/categories/ : 노트북거치대·컴퓨터책상·모니터받침대·모니터암·**사무용의자**) + 홈·/guides/·/about/·페르소나/시나리오 이미지 채움 / N/A / N/A (수익=Tracking ID 연결 + /go/ 작동 후 — #22) | #21 |

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
| AliExpress Portals | **App Key/Secret·라이브 검증 완료** [확정]. ~~honsalim.com whitelist('ali' 차단)~~ → **honsallim.com 채널 등록 완료** [확정 #21]: Portals 나의 웹사이트에 honsallim 채널(Non-network·content>vertical sites·Korea·영어 desc) 등록 — **별도 승인 게이트 없이 즉시 등록**(다비교·k-Content Hub와 동일). 이전 honsalim.com은 'ali' 자동검증으로 Submit 자체 차단이었음 → 겹ㄹ 도메인으로 돌파. **다음: 채널 Tracking ID → ali.env 연결 → 개별 deeplink**(#22) | 2026-06-02 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션 #22) — #21에서 1·2번·홈캐시·도메인 이전·알리 채널 등록 완료. 남은 핵심 = **살림 카테고리 합치기 + 수익 연결(Tracking ID·/go/)**. 상세 EVENTS #21.
1. **★살림 카테고리 합치기**: `loving-herschel-0091c7` 갈래에만 있는 `sql/seeds/003_categories_living.sql` + `category_sources.yml` 살림3(**cutting-board 도마·drying-rack 빨래건조대·mini-dehumidifier 미니제습기**) 가져오기 → `db seed` → `register-categories cutting-board drying-rack mini-dehumidifier --no-dry-run`(2번에서 만든 순차 엔진) → approve+build --full+push. 비용~$1.5. ※origin/main 미머지라 git show로 파일 추출.
2. **★Tracking ID 연결**: 알리 honsallim 채널 Tracking ID → `D:\secrets\affiliate_hub\ali.env`(**주인 직접** 수정·Claude 접근금지) → 제품 재수집 시 **개별 deeplink** 생성. 현재 `deeplink_url`은 공통 트래킹링크(모든 제품 동일·whitelist 전 한계).
3. **★/go/ 작동**: wrangler **`deny` 룰**(`.claude/settings.json`)로 Claude 배포 차단(권한 자기수정 불가) → **주인이 wrangler deny 제거** 후 `PYTHONPATH=src python scripts/deploy_go_gateway.py`(D1 schema·sync-slugmap 191·Workers go_gateway 배포). 또는 Actions 워크플로 추가. 코드(slug_map 카테고리 UNION·resolve_argv) 준비됨.
4. (관찰) **Chrome lookalike 경고**: honsalim↔honsallim 1글자 차이로 Chrome 사칭 의심(주인 브라우저 히스토리 기반) → 301+시간·honsallim 정상방문 학습으로 해소. 일반 방문자는 안 볼 가능성 큼.
5. (이월) 쿠팡(방문자·트래픽 누적 후) · 무인 발행 스케줄러(매일 11시) · main-protect.
- ★**DB는 gitignore→다음 워크트리에서 `db migrate`+`db seed`+카테고리 재생성 필요**(`register-categories --all --no-dry-run` 또는 개별 collect/build, API ~$1.5). 워크트리 실행=`PYTHONPATH=src python -m cli`. 미리보기=`build --preview`(draft포함)·공개=`build --full`. ★코드·도메인은 origin/main(#21) 배포 완료 — 다음 워크트리 그대로 이어짐.

### 해소 (세션 #21) — 상세 EVENTS #21
- ✅ **도메인 honsalim→honsallim 이전·Cloudflare Pages 연결·SSL·301 Page Rule(경로보존)** · **알리 honsallim 채널 등록**('ali' 차단 돌파) · 미충전이미지(페르소나 3·about·시나리오, placeholder 0)·이미지 재사용 · `register-categories` 순차엔진·office-chair 등록(카테고리 5) · OpenRouter 잘림 자가복원 · Windows wrangler `resolve_argv` · ★홈 흰바탕 안보임=CSS 캐시→cache-busting(`?v=`). 회귀 641.

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
