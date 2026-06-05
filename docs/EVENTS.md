# EVENTS.md — 혼살림 세션 로그

> 자동 회전: 6번째 세션 시 가장 옛 세션이 docs/archive/EVENTS_YYYYMM.md로 이동.
> 옛 세션 검색은 ARCHIVE 인덱스 참조 후 archive/ 폴더 grep.
> Cap: 20KB.

## ARCHIVE 인덱스 (옛 세션 한 줄 요약)

- [EVENTS_202605.md](archive/EVENTS_202605.md):
  - 세션 #1 (2026-05-27 프로젝트 신규 셋업·정밀 조사·5파일 시스템·슬래시 명령 등록)
  - 세션 #2 (2026-05-27~28 Phase 0 설계 12/12 + Phase 1 외부 작업: GitHub·Cloudflare·도메인·R2·D1·Git push)
  - 세션 #3 (2026-05-28 Phase 1 마무리·Phase 2 핵심 모듈 9개·회귀 95·14 commits)
  - 세션 #4 (2026-05-28 Phase 2 풀 골격 + 검토 자료 2건 + DECISIONS J 8건·메모리 no-excessive-approval·회귀 95→295·21 commits)
  - 세션 #5 (2026-05-28 CLI 10/11 deployer/build + 핵심 결정 K1~K4 + 알리 승인 + pip install -e .[dev] + 회귀 333 PASS + 11 commits)
  - 세션 #6 (2026-05-28~29 정책 대재설계 L2 AI이미지 + Google AI Guide 정합 M1~M7 + cross-project 통합 + 회귀 342 + 17 commits)
  - 세션 #7 (2026-05-29 cross-project 잔존 3건(AutoBlog Hana Kim·혼살림 M2 Person Schema·Scaled Content Abuse Step1)·필명 "혼살다" 확정·pip-audit 0건·2 commits)
  - 세션 #8 (2026-05-29 네이버 작업 D:\naver_blog\ 별도 프로젝트 분리(C안)·private repo·dazzling-hermann 폐기·1 commit)
  - 세션 #9 (2026-05-29 자동 push 정책 N1 + dashboard 모듈 CLI 11/11 + secrets 경로 정정·회귀 352·9 commits)
  - 세션 #11 (2026-05-29~30 디자인 시안 5종·Jinja2 템플릿·builder.renderer·SEO/JSON-LD·enrich 버그수정·알리 수집기 골격+라이브검증·회귀 378. ※#10은 워크트리 폐기 정리만)
  - 세션 #12 (2026-05-30 알리 상품수집 CLI→C-1 연결→enrich 풀구축→4게이트 통과 첫 글·회귀 378→436·10 commits·메모리 incremental-critical-review·autonomous-safe-system 신설)
  - 세션 #13 (2026-05-30 게시 경로 완성·★첫 글 honsalim.com 라이브 게시·무인 배포 파이프라인(방법A)·알리 whitelist 2채널 제출·회귀 436→470·1 commit e763e0f 배포 success)
  - 세션 #14 (2026-05-31 용어 일상화(내맘대로 세팅·라이프스타일)+사이트 大전환 기획(카테고리 비교·노써치형 DECISIONS O1~O9)+카테고리 프로토타입·알리 API 라이브검증·회귀 470→472)
  - 세션 #15–16 (2026-05-31 SEO 자동최적화 엔진·네이버 검색광고·전체제품 카탈로그·product_filter·디자인 大전환 1단계(우드톤→흰바탕 tokens 교체)·회귀 472→553 / 다음=#17)
  - 세션 #17 (2026-05-31 카테고리 자동등록 파이프라인 완성·사무용의자 구성표준·개념이미지(Imagen)·collect-category/build-category CLI·정형화 입증(책상)·회귀 553→569)
  - 세션 #18 (2026-05-31 운영자 1클릭 승인 게이트(O21·build-category draft 고정)·doctor §10 64진입점·★카테고리 페이지 디자인 디버깅(글씨 흐림 진짜원인=backdrop-filter 제거)·회귀 569→590)
- [EVENTS_202606.md](archive/EVENTS_202606.md):
  - 세션 #19 (2026-06-01 ★DeepSeek v4-pro 전면 전환·관련성 필터 require_all 근본수정·★판매량 기준 추천6선(migration 006)·신규 2카테고리·회귀 590→623)
  - 세션 #20 (2026-06-02 ★카테고리 4개 라이브 배포·홈 카테고리우선 大리디자인·버그 4종 근본수정(산출물청소·wrangler 8000111·캐시·이미지오인)·회귀 623→632)

## 최근 5세션

### 세션 #25 — 2026-06-05~06 (Opus 4.8 1M, ★쿠팡 채널 통합(수동 부트스트랩)+모니터암 이미지 그리드 라이브검증 / ★주인 신뢰 비판 → 보조역할·월권금지 메모리 신규, 회귀 678→710)

**시작 상황**: `/honsalim-start`(워크트리 beautiful-neumann, EVENTS #23·git엔 #24 커밋 미기록). 주인 "쿠팡 최종승인 심사미달이 문제인지 15만원 미달인지" 질문에서 시작 → 쿠팡 노출 방식 논의로 확대.

**핵심 진척 [확정]**:
1. **★쿠팡 채널 통합(`collector.coupang` 수동 부트스트랩·DECISIONS U1)**: 쿠팡 API는 최종승인 후라 닭-달걀 → 운영자 '블로그용(a태그) HTML'을 `coupang_products.yml`에 기록 → `collect-coupang`(CLI 22번째)이 products(`source='coupang'`,slug `cp-<코드>`)+category_products 적재(**정합화 prune**). 렌더러=알리와 **분리된 "쿠팡 로켓배송" 이미지 그리드**(S1). **채널인식 고지**("쿠팡 파트너스 및 AliExpress"). **알리 가드(§0)**: category_collect·select_featured 리셋을 `source='aliexpress'` 한정→쿠팡 보존. `/go/` 채널무관 작동.
2. **★이미지 그리드(U5)**: 쿠팡 '블로그용' 제공 이미지 URL **hotlink=정식**(다운로드만 §9 금지). 모니터암 **쿠팡 15개 이미지 그리드 라이브검증**(전부 로딩). onerror graceful fallback.
3. **★광고차단 진단 [확인됨]**: uBlock Origin Lite가 'affiliate/banner' 이미지 차단 → 광고차단 사용자만 미표시(대다수 모바일·비차단은 표시). 자체호스팅 우회는 §9/계정위험으로 안 함.
4. **최종승인 문턱 = 판매금액 15만원**(내 수익금 아님·U2 [확인됨]).
5. 회귀 **678→710**(+32). 린트 클린.

**★프로세스·신뢰 (가장 중요·메모리화)**: 주인이 **신뢰 훼손**을 강하게 지적 — ①브라우저 자동화 된다고 **미확인을 사실처럼 전제**하고 확장 설치까지 시켰으나 **쿠팡=정책 차단**(U3)으로 실패 ②주인이 알고 결정한 **배너를 "규정 위반"으로 막은 월권**(특히 '광고 없음'=우리 문구=주인 선택) ③"몇 개 링크→15만원→API"식 **희망고문**(트래픽이 진짜 병목·신규도메인 검색노출 거의 0) ④측정 시스템 **과잉설계**. → **메모리 신규 [[assist-not-overstep]]**(월권·희망고문·과잉설계 금지) + [[no-speculation]] 보강(치명적 가정 먼저 확인/경고). 광고 효과는 **위치>형태**(ATF 고가치·CPM 교차검증)·**효과검증=쿠팡 수익리포트**(측정 시스템 안 만듦·U4).

**잔존/다음(#26)**: **(1)★광고 배치 구현**(메인 첫화면 쿠팡 배너[주인 원안]+카테고리 결정지점·구현 전 코드 미리보고). **(2)★성장이 진짜 병목**(정직하게·희망고문 금지). **(3)쿠팡 상품 추가**=수동(주인 블로그용 HTML)·API는 판매15만원 후·브라우저 자동화 재시도 금지. ★브랜치 `claude/beautiful-neumann-eabaa8`=PR로 main 머지.

---

### 세션 #24 — 2026-06-03 (Opus 4.8 1M, Tier 0 SEO 품질강화 + 홈오피스 필러(토픽 허브) + 리뷰페이지 쿠팡 링크 + 멀티채널/무인마케팅 전략 확정, PR #6~9 / ※EVENTS 미기록분 #25에서 사후 1블록 정리)

**핵심 [확정]** (git 커밋 ba5a091·2c39f31·bfe9389·8b2289c, origin/main 머지):
1. **멀티채널·무인마케팅 전략 정밀리서치 확정** → DECISIONS **S1·S2**(채널별 최선 추천 C안·가격비교 A안 탈락) + **T1·T2**(SEO 본진·Pinterest 최우선·양산금지·2025.12 어필리 패널티 회피).
2. **Tier 0 SEO 품질 강화**: "데이터 기반 비교" 포지셔닝·E-E-A-T·토픽 클러스터.
3. **홈오피스 필러(토픽 허브)** 페이지 + 카테고리 UX 수정 + 카테고리→필러 역링크.
4. **리뷰 페이지**(`/reviews/`·noindex) 쿠팡 제휴 링크 글자 노출 + 히어로 이미지(미표시 iframe 제거) — 쿠팡 승인 데모 interim. ※#25에서 카테고리 페이지 정식 통합으로 발전.

---

### 세션 #23 — 2026-06-03 (Opus 4.8 1M, ★무인 스케줄러 A안(refresh-cycle) 구축·가동 셋업 + 모니터링 대시보드 + 메인 체크아웃 정비 + 쿠팡 활성화 착수, 회귀 659→678)

**시작 상황**: origin/main #22. 주인 "무인스케줄안 진행·승인 미리받고 끝까지". 모니터링 대시보드 + 쿠팡 가입 착수로 확대.

**핵심 진척 [확정]**:
1. **★refresh-cycle(A안·C10)**: `deployer/refresh_cycle.py`+CLI(기본 dry_run) — published 새로고침→가드레일 자가복원(fail-closed 자동 비공개)→빌드→**변경분만** push→CI 배포. LLM 미사용 ~$0/일. dry-run+라이브 자가복원 오프라인 실증. 래퍼 `scripts/run_refresh_cycle.ps1`(main·DB fail-safe).
2. **★모니터링 대시보드(C12)**: "무인 사이클"+"공개 카테고리 건강(미달 ⚠+킬스위치)"+경고 배너. refresh-cycle이 매 실행 후 `data/refresh_cycle_last.json`+대시보드 자동 갱신. **바탕화면 아이콘 "혼살림 모니터링"**.
3. **★Claude 예약작업(C11)**: `honsalim-refresh-cycle`(매일 11:00 KST·지터~10분). 윈도우 작업스케줄러 직접 등록은 안전가드 차단→Claude 예약작업이 대안(앱 열려있을 때).
4. **★메인 체크아웃 정비**: D:\affiliate_hub가 #17+미커밋 DeepSeek 잔재+5월28일 DB 방치 → 잔재 `stash@{0}` 보관 → #22 ff → DB 재생성(~$2): **6 공개 + 2 보류**(laptop-stand·drying-rack, 가드레일 fail-closed). 낡은DB=`data/honsalim.db.bak_session23_may28`.
5. **★쿠팡 활성화 착수**: 파트너스 가입(honsallim.com). 승인엔 라이브 페이지 쿠팡 고지+링크 스샷 필요. `disclosure.py` 이미 쿠팡 지원·`collector.coupang` 미구현. 쿠팡=메인 채널(§6)·시점 앞당김.
6. 회귀 **659→678**(+19). 린트 클린.

**무인·안전(§0)**: dry-run 우선·실패 격리·fail-closed 킬스위치·변경 감지 배포·사전조건 미충족 안전정지·예약작업 destructive git 금지·잔재 비파괴 보관.

**잔존/다음(#24)**: **(0)#23 머지→스케줄러 가동 확인**(첫 배포 시 보류 2개 라이브에서 내려감). **(1)★★쿠팡 본격**(링크생성→승인 데모페이지→스샷→`collector.coupang` 구현). **(2)★★미결정 설계 — 알리+쿠팡 페이지 배치(주인 아직 못 들음·반드시 논의)**: 혼합 vs 분리·추천6선 섞기·가격비교·/go/ 쿠팡 분기. **(3)★성장**(측정 리뷰). (4)보류 2개 검토.

---

### 세션 #22 — 2026-06-03 (Opus 4.8 1M, ★자율 게시 가드레일(E7→fail-closed)+살림3 합치기+8개 자동공개 라이브배포+측정인프라3종+/go/ Pages Function 수익경로 복구 / 개발 마무리→성장 전환, 회귀 641→659)

**시작 상황**: 워크트리 infallible-greider, HEAD #21 `11f8b40`, 회귀 641. 살림 카테고리 합치기 착수 → 주인 "자동 가능한 건 승인 없이 자동화" 요구 → 자율 게시 가드레일 구축으로 확대 → 라이브 배포·측정·/go/까지.

**핵심 진척 [확정]**:
1. **살림3 합치기 + 알리 개별 deeplink(R5)**: loving-herschel의 seed003+sources 살림3(도마·빨래건조대·미니제습기) 적용(laptop-stand '전화' 제외 보존)·DB재생성(8)·재수집. `ALI_TRACKING_ID=honsallim`→**247개 개별 deeplink**(공통링크 해소).
2. **★자율 게시 가드레일(R1·R2)**: E7(사람 게시승인)을 **fail-closed 가드레일+사후 킬스위치**로 개정. `category_guardrail`(5중 검사)·`auto_publish`·CLI 4종(auto-publish·register --auto-publish·category-status --monitor·킬스위치)·테스트 18. LLM 단일오탐 관용(2건+만 보류).
3. **★자가복원 루프 실증 + 버그 근본수정(R3)**: 가드레일이 **수동검토 안 한 office-chair에서 진짜 오염(캠핑/외골격/화장 의자) 자동 적발** → exclude 보강 → 재수집. 발견: `category_collect`가 비관련 옛 추천을 안 지워 오염 영속 → **prune 근본수정**. 8개 전부 가드레일 통과 자동공개.
4. **★라이브 배포**: build --full → push origin main → CI(build-and-deploy) **success** → honsallim.com 8개 카테고리 라이브(HTTP 200 검증).
5. **★측정 인프라 3종(R6)**: ①Cloudflare Web Analytics(자동) ②GSC(DNS 자동인증+사이트맵 제출, fetch 비동기) ③네이버 서치어드바이저(meta 심고 배포+소유확인+사이트맵). honsallim 반영.
6. **★/go/ 수익경로 복구(R4)**: 제품 클릭 404였음 → Worker(wrangler deny 차단) 대신 `functions/go/[[path]].js` **Pages Function**으로 정규 git push 배포. 라이브 검증: /go/→**302 알리**·미등록→홈·정적사이트/_headers 무영향. 247개 제품.
7. **★개발 마무리→성장 전환(R6, 주인 명시)**: 매 세션 최우선=**성장**. 메모리 [[growth-first-priority]] 최우선 등재.
8. 회귀 **641→659**(+18). 린트 클린. 배포 3커밋(#22·네이버·/go/). 비용 ~$2.

**무인·안전(§0)**: 가드레일 fail-closed(미탐<오탐)·자가복원 루프(적발→수정→재수집→통과)·collect prune·킬스위치·monitor·/go/ 미등록→홈(봇차단).

**다음 세션(#23+)**: ★**성장 최우선**([[growth-first-priority]]) — 측정 데이터 1~2주 후 리뷰(GSC/네이버/Cloudflare)→키워드 더블다운, 홈오피스 토픽 심화, 롱테일 콘텐츠. (완성·저위험) 무인 스케줄러 A안. (선택) CATEGORIES.md·D1 클릭로깅·쿠팡. ★DB gitignore→재생성(`register-categories --all --no-dry-run --auto-publish`). 워크트리=`PYTHONPATH=src python -m cli`.

---

### 세션 #21 — 2026-06-02 (Opus 4.8 1M, ★도메인 honsalim→honsallim 이전·연결·301(알리 'ali' 차단 돌파) + 알리 채널 등록 + 미충전이미지·순차등록엔진·홈 흰바탕캐시 근본수정, 회귀 632→641)

**시작 상황**: `/honsalim-start`(워크트리 trusting-lamarr, HEAD #20 `a34955d`). 회귀 632. 사용자 "1·2·3 순서대로·승인 미리받고 끝까지" → 미충전이미지·제품등록·/go/ 착수. 도중 홈 흰바탕 안보임(캐시)·★honsallim 도메인 미반영(loving-herschel 갈래에만 존재) 발견 → 도메인 이전·연결·알리등록까지 확대.

**핵심 진척 [확정]**:
1. **1번 미충전 이미지**(라이브): 페르소나 3장(`scripts/gen_persona_images.py`)·about 히어로(기존 about.webp)·시나리오 카드=소속 페르소나 이미지 재사용(비용0). `image_block` `img_url` 지원(하위호환). build-category **이미지 있으면 재사용**(#20 보존·비용절감). 단색 placeholder **0**.
2. **2번 순차등록 엔진**(라이브): `register-categories [slugs|--all]` — 순차 collect→build·실패격리·draft(E7). office-chair 등록(카테고리 5). **근본수정**: ①OpenRouter 응답 잘림(JSONDecodeError) 자가복원(claude_client resp.json 재시도 + build_and_save가 RuntimeError도 재생성) ②Windows wrangler.cmd subprocess 미해석(FileNotFoundError) → `common/proc.resolve_argv`(실행시 shutil.which, command필드 불변→테스트 0영향).
3. **★홈 흰바탕=CSS 캐시** 근본수정: tokens/pages.css는 흰바탕 최신(배포 정상)인데 `immutable`+버전없는 파일명 → 옛 우드톤 CSS가 브라우저 캐시에 박힘. renderer `asset_version`(static CSS·JS 내용해시)을 모든 링크 `?v=` 부착(cache-busting). 일반 새로고침으로 새 디자인 받음.
4. **★도메인 honsalim.com → honsallim.com 이전·연결·301**(알리 'ali' 차단 돌파): 알리가 'ali' 포함 url(honsa**li**m) 영구차단 → 'll' honsa**ll**im.com. 코드·테스트 치환(인프라명 honsalim-clicks·Pages명·DB 보존)+validator 허용도메인 신·구 둘다. Cloudflare Pages 커스텀도메인·SSL Active + **Page Rule 301**(honsalim.com/* → https://honsallim.com/$1 경로보존, 라이브검증). sitemap·canonical honsallim.
5. **★알리 채널 honsallim 등록** [확정]: Portals "나의 웹사이트"에 honsallim.com 채널(Non-network·content>vertical sites·Korea·영어 desc) **등록완료**(별도 승인게이트 없음). 이전 honsalim.com은 Submit 자체 차단이었음 → 'ali' 돌파.
6. 회귀 **632→641**. black·ruff·mypy 클린. 비용 ~$1(수집·빌드)+페르소나 3장. origin/main 배포 3회(#21·#21-2 cache-busting·#21-3 도메인).

**★중요 — 갈라진 작업 갈래 인지**: honsallim 도메인 이전·**살림 카테고리**는 `loving-herschel-0091c7` 브랜치 #20에 있었으나 **origin/main 미머지**(내 베이스=zealous #20 `a34955d`)라 인수인계 STATE에 없었음. 도메인은 이번에 origin/main 직접 적용 완료. **살림 카테고리(cutting-board 도마·drying-rack 빨래건조대·mini-dehumidifier 미니제습기) = seed `003_categories_living.sql` + category_sources.yml 3개 = loving-herschel에만 존재** → #22에 합쳐야(register-categories 엔진으로 데이터 생성).

**무인·안전(§0)**: 이미지 재사용(가짜·퇴행 방지)·실패격리(무인 안전)·자가복원(잘림·일시 API)·cache-busting(변경 반영 보장)·도메인 301(SEO 중복 정리)·알리 honest disclosure description.

**잔존 미해결 (#22)**: ①**살림 카테고리 합치기**(loving-herschel seed003·sources 살림3개 → `db seed` → `register-categories cutting-board drying-rack mini-dehumidifier --no-dry-run` → approve+build --full+push, 비용~$1.5) ②**Tracking ID 연결**(honsallim 채널 tracking ID → `ali.env` 주인직접 → 개별 deeplink; 현 deeplink는 공통 트래킹링크) ③**/go/ 작동**(deny 룰: 주인이 `.claude/settings.json` wrangler deny 제거 후 `scripts/deploy_go_gateway.py` 또는 Actions. slug_map 191·D1 schema·resolve_argv 준비됨) ④Chrome lookalike 경고(301+시간 해소·관찰) ⑤쿠팡(방문자 후).

**다음 세션 할 일**: 1)**살림 카테고리 합치기**(register-categories로) 2)Tracking ID 연결+개별 deeplink 3)/go/ 작동(주인 deny 해제 후). ★DB gitignore→재생성(`db migrate`+`db seed`+카테고리 collect/build). 워크트리 실행=`PYTHONPATH=src python -m cli`.
