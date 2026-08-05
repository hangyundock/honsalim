# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]). 무인 발행이 origin 전진 → push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#51: 글↔글 내부링크 0→**132** + 키워드 공략구간 하강(2000+ → **300~2000**·후보 94.8% 회복) + og:image 전 42페이지 누락 수정 + ★무인 감시 자동화(배포 전 게이트) + www 301.** 40일간 결함을 몰랐던 원인=배포 후 검증이 홈 1페이지 상태코드만 봤음. 상세 EVENTS #51·DECISIONS II | 2026-08-05 #51 |
| 운영 모델 | **★완전무인 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT]·텔레그램). 자가복원 **4겹**(#41 게이트 반려·#42 생성 예외·#44 안전정지·#48 과밀 감산). fail-loud: #45·#47·#48·#49·#50 캐시강등 · **#51 배포 게이트**. ★래퍼는 `main`일 때만 가동 | #51 |
| ★무인 감시(#51) | **배포 전 산출물 게이트** — `refresh_cycle`(무인 배포 단일 관문) build 후·deploy 전 `validator.site_audit` 실행. 결함이면 **배포 중단+텔레그램**(주인 승인). doctor §17~§19와 **같은 코드**(단일 진실원). 검사=내부링크·title·canonical·H1·og:image·JSON-LD·제휴 rel·sitemap·대가성 고지. 유사도는 warn·게이트 제외(성능 164배). 게이트 137ms. 주간 요약=사이클이 월요일에 얹음 | #51 |
| ★자동 승인 전제 | **`validated`≠'seo 통과'** — 미매핑 글은 게이트 skip인 채 validated(GG3). auto_approve가 저장 보고서로 재확인해 보류. 해소는 **재생성**뿐 | #49 |
| ★발행 실패 대응 순서 | **본문=CLAUDE.md §7-3 [확정 #48]** — ①격리 키워드는 두면 자동 재개(`keyword-requeue` 금지) ②`cli experiment` 오프라인 분포 ③라이브는 마지막 1회. ★n=1 판단 금지 | #48 |
| Phase 1·2 기반 | 인프라(GitHub·Cloudflare·secrets·pre-commit 9종) + 핵심 모듈 10종 + 카테고리. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1329 PASS + 1 skip** [확정 pytest, #51] — #51 +55(내부링크 가드·공략구간·site_audit·배포 게이트·doctor 검사기). ★가드 실효성 **6회 역검증**. 옛: **1274**[#50] — #50 +16(카테고리 균형 8·캐시 강등 신호 3·배선 순서 고정 1·도달 불가 lint 4). ★가드 실효성 2회 역검증(수정을 되돌려 실제 실패 확인). 위젯 Qt 1 opt-in skip. black·ruff·mypy 클린 | 2026-08-05 |
| CLI 명령 (BACKEND §9) | **43개** — 코어 10 + 카테고리 + 운영(keyword-*·publish-queue·auto-cycle·refresh-cycle·monitor-articles·notify-alert) + experiment(#48). ※IndexNow=`deployer.indexnow` | #48 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published + **5 게이트**(truth·schema·disclosure·links·seo) + META-JSON + Article JSON-LD. 키워드 글 seo 하한=**절대 횟수 min_count≥4**(FF3). ★seo는 키워드 매핑 있어야 작동(GG3). 세부 DECISIONS J·O·CC·FF·GG | #4~#49 |
| doctor (BACKEND §9) | §1~**§19**(+#51 §17 내부링크 정합·§18 유사 키워드·§19 온페이지 SEO·컴플라이언스 — 배포 게이트와 동일 코드) · §15 씨앗 정합·§16 IndexNow + §10 모듈 진입점 **73개** + #19 LLM 키 점검 | #48 |
| DB 초기화 | `data/honsalim.db` **v10**(migration 002~010) + categories 9·products·keyword_queue·articles.structured_json·api_usage·personas 3·scenarios 10. 대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed` | #48 |
| LLM 비용 추적 | `api_usage(provider='llm')` — 재시도·형식오류까지 매 호출 1행. 단가 입력은 **불요 결정**(HH9·월 수백 원) — 토큰만으로 급증 감지 유효. 캐시 적중 59%(FF7) | #50 |
| 설계 문서 / 메모리 / 5파일 | 설계 12/12 완료+SUMMARY(모순 0) · 메모리 feedback 7+reference · 5파일+슬래시 ✅ | #1~#12 |
| 사이트 게시글 / 트래픽 / 수익 | 카테고리 7·**정식 글 22편**·sitemap 40·라이브 200. **글↔글 링크 132개**(전 **0**)·고아 0. **og:image 42/42**. 제휴 317종 완전 일치·깨진 링크 0. GSC 노출 73·클릭 **2**·평균 **18.2**위. ★사이트 나이 **40일** — 클릭률 2.7%는 18위권 평균 이상이라 **콘텐츠 아닌 순위 문제** | #51 |
| ★무인 키워드 선정·공급 | 리필은 **네이버 실검색량**으로 뽑는다(HH1). 키 = 직전 카테고리 회피 → 사용 횟수 적은 순 → 점수(HH3). **#51: 공략구간 [300,2000]** — 옛 하한 2000이 후보 94.8%를 버렸다(II4). 후보는 yml secondary 정확 매칭+core 포함인 것만(도달 불가 5건·`doctor §15`·HH7). **미해결**: monitor-stand 공급 부족(HH8) | #51 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | 혼살림 / **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피·SSL Active·2027-06-01 Auto Renew) + **www→non-www 301**(#51) + honsalim.com(구·**301 Page Rule**·경로보존) / **Cloudflare Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#50**. **build-and-deploy: main push → 커밋된 build/site를 Pages 배포**(CI 재빌드 없음·글 DB 로컬). ★**무인 배포는 전부 `refresh_cycle`** — `deployer.git_push`는 stub이라 단독 금지(#47 EE4). ※★**반드시 main 유지**(detached면 무인 정지·#44) |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 32-bit (TIMA·AutoBlog 공유) / `logs/auto_cycle.log`(무인 1차 증거)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE·telegram(TIMA 봇) .env + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유·DeepSeek #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token / Anthropic API Key | 활성 / 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY / GitHub PAT | 영구(공개 키) / 미발급(Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → promotion_link·`/go/`→302 라이브 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

secrets 격리 · pre-commit 9종(detect-secrets+black·ruff·mypy) · GitHub Secrets · Branch Protection **전부 운영 중**. `.claude/settings.json` deny 24·allow 14 = 검토 대기.

## 알려진 잔존 미해결

### ★ 다음 세션 #52 — **작업 목록은 TODO.md**, 상세 근거는 EVENTS #51·DECISIONS II

1. **★[관찰·최우선] 08-06 사이클 1일차** — #50(카테고리 균형)+#51(새 공략구간·배포 게이트)이 라이브에서 **처음 함께 도는 날**. (a) 300~2000 구간에서 head가 아닌 구체 키워드가 뽑히는가 (b) 텔레그램에 **"배포 차단"** 경보가 없는가 (c) 리필 검색량 조회 실패 없음. 확인: 텔레그램 → `logs/auto_cycle.log` → `data/auto_cycle_last.json`.
2. **[관찰] 대기 키워드 0개** — 주간 요약 실측. 새 구간에서 실제 적격 후보가 나오는지는 08-06에 확인. 0편이면 ceiling 상향 판단.
3. **[관찰] 내부링크·구간 하강의 순위 효과** — 반영 2~8주. 기준선 = 노출 73·클릭 2·평균 18.2위.
4. **[보류] 클릭 추적 미연결**(II12) — `/go/`가 D1에 안 씀. 트래픽 붙은 뒤 착수(과잉설계 금지).
5. 이월: laptop-stand 색인 · monitor-stand 공급 부족(HH8) · 도마 6편 상호경쟁 · 여름이불 결정 · 08-02 미기동 · IndexNow 오탐(HH10).
- ※**해결·종결**: #51 — 글↔글 링크 0(II1)·매핑 concept_image 단일의존(II3)·og:image 전 페이지 누락(II6)·감시 수동(II7)·www 미접속(II11)·게이밍의자 글 구조 이관.
- ★**작업 함정**(매 세션): 운영 폴더 브랜치==main([[autonomous-detached-head-silent-stop]]) · push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) · 한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처 · 운영 모듈 import 시 `load_secrets()` 선행([[project_verify_script_load_secrets]]) · 라이브 검증은 curl/브라우저 UA([[live-verify-cloudflare-ua]]) · ★게이트는 켜기 전 실제 산출물로 판정([[unmanned-monitoring-gate]])

### 진척 가능(작음) / 보류
- 작음: `builder/manifest.py` 증분 빌드 · `collector/coupang.py`(Phase 4) · Actions status check · BitLocker
- 보류: AdSense(2026-12) · 영어 확장 · 보조 호스팅

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| **2026-08 (현재)** | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
