# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#34: ★글 렌더링=카테고리 구성 통합 + 무인 골격 보강 + 품질 대수술** — 주인 "의자 페이지 최종구성 따라 재사용" 지시 실현. ①완전 무인 골격(키워드 자동보충 `auto_pick_keyword`·스케줄러 auto_mode 분기·GUI auto_mode 토글·대시보드 시작 시 자동 마이그레이션) ②품질(상품명 정리·본문 코드 제거·미리보기 로컬HTTP→file:// 무스타일 해소) ③★**글=category.html로 렌더**(별도 article 템플릿 폐기·매핑 카테고리 picks/**전체 카탈로그/이미지**/비교 물려받고 글은 제목·대가성 고지·가이드·빠른결론만·`_article_as_category_ctx`·`is_article` 조건부 additive·미매핑은 폴백) — 라이브 draft8 **카탈로그 36개·이미지 44개**·H1 1개·고지 유지·office-chair 무손상 ④Tier2·migration 008(structured_json·버전버그) 흡수. **auto_mode 기본 OFF**. 회귀 873→**896**. main **e9e3fd2**(13커밋). 상세 EVENTS #34 | 2026-06-16 #34 |
| 운영 모델 | 자동 게시 활성(콘텐츠 큐). **refresh-cycle = 수동 운영(주인 직접 지시) — C13 [확정 #24], Claude 예약작업 비활성화**. 자동 "승인" 금지(E7→가드레일) | #24 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **896 / 896 PASS** [확정 pytest, #34] — #34 +23(무인골격 보강·상품명/본문코드/미리보기HTTP·Tier2·글=카테고리 통합·migration 008) · #33 +8 · #32 +14. black·ruff·mypy 클린·doctor OK | 2026-06-16 |
| CLI 명령 (BACKEND §9) | **29개** — doctor·db·collect·collect-products·enrich·validate·approve·promote·unapprove·deploy·sync-slugmap·build(+`--preview`)·dashboard·collect-category·build-category·approve-category·unapprove-category(킬스위치)·register-categories(+`--auto-publish`)·auto-publish·category-status(+`--monitor`)·**refresh-cycle(#23)** · **#25 운영 대시보드: keyword-add·keyword-generate·keyword-list·reject·coupang-add·publish-queue·schedule** · **#26: keyword-recommend** · **#29: unpublish-article·republish-article·monitor-articles·auto-cycle** · **#32: keyword-delete·category-coupang-add/list/remove·build-deploy** = **38개** | #32 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **71개** + #19 LLM 키 점검. 71/71 OK [#29 +keyword_relevance·article_state×2·article_guardrail×2·auto_approve] | #29 |
| DB 초기화 | `data/honsalim.db` **v8** + categories(**8**)·category_products + products 정가/할인·판매량/만족도 + keyword_queue(발행 큐·#25) + **articles.structured_json(Tier2 발행 보존·migration 008, #34)** (migration 002~**008**) + personas 3·scenarios 10. ★**대시보드 시작 시 자동 migrate**(#34·무명령). ※DB는 gitignore — 다음 워크트리는 `db migrate`+`db seed`(+`collect-category`)로 재생성 | #34 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 공개 카테고리=5개**(office-chair="**의자**"·쿠팡 운영자추천 zone **쿠팡 3선 균형**(#32·flex 레이아웃)·추천 8선). **정식 글 0편**(게이밍의자 글 '의자'로 흡수·301). + 쿠팡 승인용 `/reviews/`. 측정(Cloudflare·GSC·네이버 누적). 수익=/go/→302 알리/쿠팡(go-링크 작동). `mini-dehumidifier` 가드레일 미달 자동비공개(이월). collector.coupang(API)=15만원 후 | #32 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·알리 'ali' 차단 회피·Cloudflare Pages 커스텀도메인 연결·SSL Active·**라이브**, 만료 2027-06-01·Auto Renew) + honsalim.com(구·만료 2027-05-28·**→honsallim 301 Page Rule** 적용·경로보존) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#34 (e9e3fd2 · 글=카테고리 구성 통합+무인골격+품질)**, CI green. **build-and-deploy: main push → 커밋된 build/site Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB 로컬)**. ★**빌드·배포는 `cmd_build_deploy`(refresh_cycle)가 build/site·functions/go를 commit+push** — `deployer.git_push` stub의 '미커밋' 버그 근본 우회(#32). wrangler `--commit-message`(ASCII)+`--commit-dirty` 유지. ※**운영 폴더(D:\affiliate_hub)는 #34(e9e3fd2)로 git pull 동기화함**(이번 세션·clean FF·13커밋). 워크트리는 origin/main 기준 |
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

### ★ 다음 세션 #35 — 상세 EVENTS #34
1. **★★자동실현(완전 무인) 실제 라이브 테스트** (주인 #34 명시·최우선): ①draft 7·8 등 미리보기 검토→승인→발행으로 **첫 5편 사람 검수·발행**(min_published=5 게이트 충족) ②설정 `auto_mode` ON ③'예약 켜기'→스케줄러 auto-cycle 등록 ④winnable 키워드 자동선정→생성→(5편후)자동승인→발행·배포 **전체 1회 라이브 검증**(주인 대시보드). **무인 가동 OFF→ON 실증이 목표.** 글은 카테고리 구성(이미지·전체 카탈로그)으로 나옴.
2. (이월) 쿠팡 이미지 테스트(키워드 쿠팡 첨부→글 생성→상단 운영자추천 zone) · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장 Tier0([[growth-first-priority]]·트래픽 병목).
- ★draft 5·6은 concept_image 이전 생성→article.html 폴백(단순). **draft 7·8(매핑 有)이 카테고리 구성**으로 나옴. 새 글은 전부 카테고리 구성.
- ★DB gitignore→재생성(★대시보드 시작 시 자동 migrate). 운영 폴더=#34 동기화됨. 워크트리=`PYTHONPATH=src python -m cli`. main직접머지=`git push origin HEAD:main`. ★PowerShell/cmd 한글 깨짐→.py·ASCII([[powershell-korean-encoding]]).

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
