# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]). 무인 발행이 origin 전진 → push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#48: 무인 발행 밀도 벽 돌파 + 라이브 2편 + 비용 낭비 방지 5종 + slug 근본수정** — 07-30·31 발행 0편 원인=`책상추천` density 진동(도배↔미달). 키워드 글 하한을 **절대 횟수(min_count≥4)**로 전환(B2·주인 결정)·1인칭 오탐 화이트리스트 반전·재시도 2→3·과밀 감산 백스톱. 08-01 정규 사이클 **시도 1회 통과 자동 발행**. 회귀 1126→**1230**. 상세 EVENTS #48·DECISIONS FF | 2026-08-01 #48 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT] 로그·텔레그램). 자가복원 **4겹**(#41 게이트 반려+#42 생성 예외+#44 안전정지+**#48 과밀 감산 백스톱**). fail-loud: #45 refill·생성0 / #47 반려 집계·비공개 배포·cli 크래시 / **#48 형식오류 응답 원문 로깅**. ★래퍼는 `main`일 때만 가동([[autonomous-detached-head-silent-stop]]). E7 완화=min_published | #48 |
| ★발행 실패 대응 순서 | **CLAUDE.md §7-3 [확정 #48]** — ①격리된 키워드는 **그대로 두면** 다음 사이클이 다른 키워드로 재개(`keyword-requeue`로 되살리지 말 것) ②문제 키워드는 `cli experiment`로 **오프라인 분포 측정** ③라이브 재생성은 마지막 1회. ★n=1 라이브 판단 금지(#48에 6회 연속 실패) | #48 |
| Phase 1·2 기반 (#2~#17) | Phase 1 인프라(GitHub·Cloudflare·secrets·pre-commit 9종) + 핵심 모듈 10종(cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers) + #17 카테고리 4종. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1230 PASS + 1 skip** [확정 pytest, #48] — #48 +104(밀도 수렴·조사 안전 치환·감산 백스톱·배선 가드·경계 대칭·1인칭 화이트리스트·비용 통제 3종·slug 조각 판정/자가교정), 위젯 Qt 크래시 1 opt-in skip. black·ruff·mypy 클린 | 2026-08-01 |
| CLI 명령 (BACKEND §9) | **43개** — 코어 10 + 카테고리(provision-category 등) + 운영(keyword-*·publish-queue·auto-cycle·refresh-cycle·monitor-articles·notify-alert 등) + **experiment(#48 오프라인 분포 측정·기본 dry-run)**. ※IndexNow는 CLI 아님=`deployer.indexnow` | #48 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD(author=혼살다·/about/ 연결·#45). ★키워드 글 seo 하한=**절대 횟수 min_count≥4**(#48 FF3), 카테고리는 %하한 유지. 세부 DECISIONS J·O·CC·FF | #4~#48 |
| doctor (BACKEND §9) | §1~§16(+#45 §15 씨앗 정합·§16 IndexNow 배포 정합) + §10 모듈 진입점 **73개** + #19 LLM 키 점검 | #48 |
| DB 초기화 | `data/honsalim.db` **v10**(migration 002~010) + categories 9 + products + keyword_queue(#25) + articles.structured_json(#34) + api_usage(#36·**#48 tokens_in/out**) + personas 3·scenarios 10. ★대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed` 재생성 | #48 |
| LLM 비용 추적 (#48) | `api_usage(provider='llm')` — **재시도·형식오류·빈응답까지 매 호출 1행**. enrich 로그에 24h 요약. ★단가 `llm_price_in_per_1m`/`_out_per_1m` **미입력(0)** → 토큰만 기록·비용 $0. 캐시 적중 관측(실측 59% 자동·FF7). 미연결: 카테고리 가이드·비전 게이트 | #48 |
| 설계 문서 / 메모리 / 5파일 | 설계 12/12 완료+SUMMARY(모순 0) · 메모리 feedback 7+reference · 5파일+슬래시(start/save/end) ✅ | #1~#12 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 6개** + **정식 글 20편**(#48 +2: `kw-269a4bdb` 책상추천·`1-2` 1인용밥솥). ★**색인 원인 확정(#46·DD1)**: 라이브 29 URL·색인 4 → 격차=**크롤 예산/권위**(기술·얇음·중복·링크 정량 클린). 주인 **미색인 11개 색인요청 완료**(07-20·전환 확인 필요). 다음 레버=색인 전환+발행량+권위([[growth-first-priority]]) | #48 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | 혼살림 / **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피·SSL Active·2027-06-01 Auto Renew) + honsalim.com(구·**301 Page Rule**·경로보존) / **Cloudflare Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#48**(밀도 벽 돌파·비용 통제·slug), 운영 폴더 동기화됨. **build-and-deploy: main push → 커밋된 build/site를 Cloudflare Pages 배포**(CI 재빌드 없음·글 DB 로컬). ★**무인 배포는 전부 `refresh_cycle`** — `deployer.git_push`는 commit 없는 stub이라 단독 사용 금지(#32·#47 EE4). ※★**반드시 main 유지**(detached면 무인 정지·#44) |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 32-bit (TIMA·AutoBlog 공유) / `logs/auto_cycle.log`(무인 1차 증거·#47 UTF-8 복구)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE(#37 분리)·telegram(#41 TIMA 봇 재사용) .env + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유·DeepSeek 본문생성 #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY / GitHub PAT | 영구(공개 키·회전 불요) / 미발급(Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → promotion_link·`/go/`→302 라이브 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

secrets 격리 · pre-commit 9종(detect-secrets v1.5.0+black·ruff·mypy 매 커밋 Passed) · GitHub Secrets · Branch Protection **전부 운영 중**. `.claude/settings.json` deny 24·allow 14 = 사용자 검토 대기.

## 알려진 잔존 미해결

### ★ 다음 세션 #49 — **작업 목록은 TODO.md**, 상세 근거는 EVENTS #48·DECISIONS FF
1. **★[관찰·최우선] 본문 예산 축소 부작용** — 산문 25~30%↓(출력 토큰 절감)과 함께 키워드 자연 출현이 4~7 → **3~5회(중앙 4)**로 하락, `min_count=4` 여유가 얇다(3샘플 중 1건 `count_low`). 08-01 정규 사이클은 시도 1회 통과. 며칠 안정성 관찰 → 흔들리면 예산 2,900~3,400자 상향(검증은 `cli experiment`, 라이브 사이클 금지).
2. **[입력 대기·주인] LLM 단가** `llm_price_*_per_1m` — 0이라 비용 $0 표시(토큰은 기록 중).
3. **★[모니터링] 색인 전환**([[growth-first-priority]]) · 4.[이월] 도마 클러스터 편중 · 5.[결정] 여름이불 자동비공개 · 6.(이월) IndexNow 관찰성·draft 카테고리 3개·게이밍의자 이관·쿠팡 부트스트랩.
- ※**비표준 slug는 #48 해결**(FF8). 라이브 3건(`/articles/1/`·`/tpu/`·`/1-2/`)은 **주인 결정으로 URL 유지**(301 없이 바꾸면 색인 단절, 301도 크롤 예산 소모).
- ★**매 세션 시작 시 운영 폴더 브랜치 확인** `git -C D:\affiliate_hub branch --show-current`==main([[autonomous-detached-head-silent-stop]]). 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). ★무인 발행이 origin 전진→push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]). ★한글→.py·ASCII([[powershell-korean-encoding]]). 운영 DB 직접수정 불가→주인 런처. ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

### 진척 가능(작음) / 보류
- 작음: `builder/manifest.py` 증분 빌드 · `collector/coupang.py`(Phase 4) · Actions status check · BitLocker(사용자 결정)
- 보류: AdSense 신청(Phase 6·2026-12) · 영어 사이트 확장 · 보조 호스팅 GitHub Pages

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| ~2026-07 | (경과) Phase 2 시스템·Phase 3 디자인·**Phase 4 첫 출시 도달**(라이브 18편) |
| 2026-08 | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
