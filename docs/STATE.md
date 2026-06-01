# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#19: ★DeepSeek v4-pro 전면 전환 + 카테고리 디자인 마무리 + 관련성 필터 근본수정 + ★판매량 기준 추천 6선 + 신규 2카테고리** (로컬·미배포). 본문생성 Sonnet→DeepSeek(OpenRouter 라우팅·출력 안정화) / 디자인(추천카드 행정렬·정렬·필터 JS·커서) / 관련성 `require_all`(타입+대상)+재수집 정합화 / 추천6선=판매량순·만족도80%하한·항상6개·정직표기 / 카테고리 **4개 전부 draft·6선**. 회귀 590→**623**. 남음=승인+배포·노트북'전화'제외어. 상세 EVENTS #19 | 2026-06-01 #19 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **623 / 623 PASS** [확정 pytest, #19] — #19 +33 (test_llm_routing 10·require_all/정합화·select_featured 판매량선정·파서 견고화·지시문·map_product 신호 등). #18 590. black·ruff·mypy 클린 | 2026-06-01 |
| CLI 명령 (BACKEND §9) | **18개** — doctor · db · collect · collect-products · enrich · validate · approve · promote · unapprove · deploy · sync-slugmap · build(+`--preview` draft포함 미리보기, #18) · dashboard · collect-category · build-category · **approve-category(#18 신규: draft→published 1클릭 승인)** · **unapprove-category(#18 신규: 공개 취소)** | #18 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**5**: 의자·책상·모니터받침대·**노트북거치대·모니터암**)·category_products + products 정가/할인·**판매량(sales_volume)/만족도(evaluate_rate)** 컬럼 (migration 002~**006**, #19) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #19 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **1편 라이브 게시** (honsalim.com/articles/homeoffice-chair-desk-50/, #13 배포) + **카테고리 4개(노트북거치대·모니터암·모니터받침대·컴퓨터책상) 로컬 `draft`**(글+이미지+**판매량 기준 추천 6선 각 6개**, **미승인·미배포** — 승인+배포는 #20) / N/A / N/A (수익은 /go/ 링크 작동+알리 whitelist 후) | #19 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsalim.com** (만료 2027-05-28·Auto Renew·SSL Active) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **e763e0f (#13)**, 배포됨. **build-and-deploy 워크플로 #13 재작성: main push → 커밋된 build/site를 Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB는 로컬). 배포 success 확인** + CodeQL · lint · security(월간 pip-audit) ✅. ※로컬 main worktree(D:\affiliate_hub)는 7b572ad로 뒤처짐 — 다음 세션 pull 권장 |
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

### ★ 시급 (다음 세션 #20) — #19 갱신 (상세 EVENTS #19). DeepSeek 전환·디자인·관련성·판매량 선정·신규 2카테고리 완료 → **검토·승인·배포**가 다음 단계.
1. **★카테고리 4개 검토 → 승인 → 배포**: 노트북거치대·모니터암·모니터받침대·컴퓨터책상(전부 draft·6선). 검토 후 `approve-category <slug>`(draft→published) → `build --full`(build/site) → honsalim.com(방법A, **사용자 승인**). 현 `build/site`는 #13 옛 사이트.
2. **노트북거치대 '전화' 제외어 결정**: 1위 픽이 "전화 태블릿 겸용" 베스트셀러(판매량 1391·노트북 거치 가능). 노트북 전용만 원하면 `category_sources.yml` laptop-stand exclude에 "전화" 추가.
3. **office-chair(사무용 의자) 콘텐츠 생성**: 현재 제품 0 — `collect-category office-chair`(category_sources에 정의됨) → `build-category`.
4. **메인 작업본 미커밋 DeepSeek 임시본 정리**: 메인(D:\affiliate_hub)에 AutoBlog #99가 넣은 미커밋 `claude_client.py`(드롭인) 있음 — 이 워크트리의 정식 버전이 supersede. 머지 전 메인 미커밋분 되돌리면 충돌 없음.
5. (이월) ★/go/ 제휴 링크 작동(D1 slug_map·go_gateway, 수익직결) · 알리 whitelist 답변 · main-protect 재활성화.
- 참고: **미리보기=`PYTHONPATH=src python -m cli build --preview`**(draft 포함, `build/preview`) / 공개=`build --full`(published만). ★워크트리 실행=`PYTHONPATH=src python -m cli`. **DB는 gitignore→다음 워크트리에서 4개 카테고리 `collect-category` --no-dry-run + `build-category` --no-dry-run 재생성 필요**(판매량 채우려면 collect 먼저, API ~$1). 미리보기 시 강력새로고침/시크릿창.

### 해소 (세션 #19) — 상세 EVENTS #19
- ~~디자인 마무리~~ ✅ 추천카드 행 정렬·정렬/필터 JS 작동·손가락 커서
- ~~★DeepSeek 전면 전환~~ ✅ `build_llm_client` 라우팅(claude→Anthropic, 그 외→OpenRouter) + 출력 변동 안정화(파서 견고화·자가복원·SEO 지시문 강화로 과밀 3%대)
- ~~★관련성 필터 한계(캠핑 테이블 오염)~~ ✅ `require_all`(타입+대상) + 재수집 정합화
- ~~★추천 6선 불투명~~ ✅ **판매량 기준 선정**(migration 006·만족도 80% 하한·항상 6개·정직표기·AI는 설명만)
- 재발방지 가드 다수(회귀 +33=623). 공통 코드라 신규 카테고리 자동 적용·기존 4개 재빌드 완료

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
