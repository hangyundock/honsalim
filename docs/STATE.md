# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#17: 카테고리 자동 등록 파이프라인 완성 + 정형화 입증**(전부 로컬·미배포). DB(categories·category_products+정가/할인, migration 002~005) / `category_collect`(수집·정제·2티어) / `category_page_builder`(글 자동생성 → **SEO·진실성 통합게이트 재생성** → 저장) / **의자 구성 표준**(타입선택기·신뢰박스·배너이미지·타입표·체크리스트·추천2티어·비교표·연관) / **개념이미지 Imagen4 Fast**(텍스트없이+CSS오버레이) / **CLI collect-category·build-category**. ★정형화 입증=**책상 2명령 자동완성**. 모니터·책상 완성·의자 카탈로그만. 회귀 553→**569**. 남음(#18)=승인게이트·배포 (DECISIONS O16~O20) | 2026-05-31 #17 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **569 / 569 PASS** [확정 pytest, #17] — #17 +16 (category_collect·category_page·concept_image + test_db·products_store fixture **근본수정**=마이그레이션 단일소스). #15–16 553. black·ruff·mypy 클린 | 2026-05-31 |
| CLI 명령 (BACKEND §9) | **16개** — doctor · db · collect · collect-products · enrich · validate · approve · promote · unapprove · deploy · sync-slugmap · build · dashboard · **collect-category(#17 신규: 카테고리 수집·정제·2티어)** · **build-category(#17 신규: 카테고리 글+게이트+개념이미지 자동생성)** | #17 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **58개**. #18에 category 모듈 진입점 추가 예정 | #15–16 |
| DB 초기화 | `data/honsalim.db` **v5** + categories(3: 의자·책상·모니터)·category_products + products 정가/할인 컬럼 (migration 002~005, #17) + personas 3·scenarios 10. ※DB는 gitignore — 다음 워크트리는 `collect-category`·`build-category`로 재생성 | #17 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **1편 라이브 게시** (honsalim.com/articles/homeoffice-chair-desk-50/, #13 배포) + **카테고리 2개(모니터 받침대·컴퓨터 책상) 로컬 완성(글+이미지)·미배포(#17)** / N/A / N/A (수익은 /go/ 링크 작동+알리 whitelist 후) | #17 |

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
| DB / 로그 | `data/honsalim.db` (v1) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\honsalim.env`** (GOOGLE_API_KEY, 세션 #9 사용자 보안 결정 — secrets/ 바로 아래 단일 파일) |

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

### ★ 시급 (다음 세션 #18) — #17 갱신 (상세: DECISIONS O16~O20 · `docs/CATEGORY_PAGE.md` · EVENTS #17). 카테고리 파이프라인·정형화 완성됨 → 무인 운영 마무리 단계.
1. **★운영자 검토·1클릭 승인 게이트** (§2-마·E7): 생성된 카테고리(글·추천6선·이미지)를 대시보드 미리보기 → **사용자 1클릭 승인** → 공개. **현재 `build-category`가 status='published' 바로 전이** — AI 자동승인 금지 원칙상 `pending` 상태 + 승인 게이트 삽입 필요.
2. **★배포** ([6]→[7]): 새 카테고리(모니터·책상) → renderer `build/site` → honsalim.com (방법A, **사용자 승인**). 현재 `build/site`는 #13 옛 사이트라 새 카테고리 미반영 — 배포 시 build/site 갱신+commit+push.
3. **doctor 보강**: §10 진입점에 `category_collect`·`category_page_builder`·`concept_image` 추가(현재 미등록).
4. **나머지 카테고리**: 모니터암 등 신규(category_sources·seo_keywords·seed 등록 후 2명령) · 의자(현재 카탈로그만 → `build-category office-chair`로 글+이미지).
5. (이월) ★/go/ 제휴 링크 작동(D1 slug_map·go_gateway, 수익직결) · 알리 whitelist 답변 · main-protect 재활성화.
- 참고: 카테고리 미리보기=`build/preview`. ★워크트리 실행=`PYTHONPATH=src python -m cli <명령>` (`honsalim` 명령은 editable=메인 체크아웃 가리킴). DB는 gitignore→`collect-category`·`build-category`로 재생성.

### 해소 (세션 #17)
- ~~카테고리 구조·렌더러 이식·DB 영속화~~ ✅ categories·category_products DB(migration 002~005)+정가/할인 컬럼 · 카테고리 인덱스(`/categories/`)·상세 렌더러 이식 · 네비 라우트(깨진 링크 해소)
- ~~카테고리 글 자동 생성~~ ✅ category_page_builder(가이드8요소·추천6선·FAQ·제품명비교표) + **SEO+진실성 통합게이트 통과까지 재생성**(자가복원) + **개념이미지(Imagen 4 Fast, 텍스트없이+CSS오버레이·webp)**
- ~~정형화 입증~~ ✅ CLI collect-category·build-category → **책상 2명령 자동완성**(모니터와 동일)
- **근본 수정**: products_store 정가/할인 저장 정합 · test fixture=마이그레이션 단일소스(하드코딩 제거) · 전역 `.chk` 충돌(클래스명 분리) · Jinja `group.items`/`c.values` 메서드 함정(키명 변경)

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
| ~~2026-05-29~06-01~~ | ~~알리 심사 결과~~ → **2026-05-28 승인 [확정]** |
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
