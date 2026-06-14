# EVENTS.md — 혼살림 세션 로그

> 자동 회전: 6번째 세션 시 가장 옛 세션이 docs/archive/EVENTS_YYYYMM.md로 이동.
> 옛 세션 검색은 ARCHIVE 인덱스 참조 후 archive/ 폴더 grep.
> Cap: 20KB.

## ARCHIVE 인덱스 (옛 세션 한 줄 요약)

- [EVENTS_202606.md](archive/EVENTS_202606.md):
  - 세션 #19 (2026-06-01 DeepSeek v4-pro 전면전환·카테고리 디자인 마무리·관련성 필터 require_all 근본수정·판매량 기준 추천 6선·신규 2카테고리·회귀 590→623)
  - 세션 #20 (2026-06-02 카테고리 4개 라이브 배포·홈 카테고리우선 大리디자인·배포 wrangler/산출물청소/HTML캐시 버그 4종 근본수정·회귀 623→632)
  - 세션 #21 (2026-06-02 도메인 honsalim→honsallim 이전·연결·301(알리 'ali' 차단 돌파)+알리 채널 등록+미충전이미지·순차등록엔진·홈 흰바탕캐시 근본수정·회귀 632→641)
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

## 최근 5세션

### 세션 #26 — 2026-06-14 (Opus 4.8 1M, ★추천 키워드 생성 기능 + 대시보드 메뉴 순서 재정렬 + 노트북거치대 off-target 근본수정, 회귀 773→782)

**시작 상황**: origin/main #25(PR #10 머지). 떠 있는 운영 대시보드(메인 체크아웃)에서 "(A) 라이브 첫 글 생성"을 시작하려다, 주인이 **키워드를 수동 선정하지 말고 추천 키워드를 생성·목록으로 보여주고 선택(선택 없으면 자동 1순위)** + **탭 순서를 실행 우선순위대로** 요청. "키워드 선정 방식은 이미 정의돼 있음" 명시.

**핵심 진척 [확정]** (전부 로컬·미배포·비용 거의 0 — 추천은 네이버 읽기전용 무료, LLM 비용은 글 생성 때만):
1. **"정의된 방식" 확정(조사)**: `collector.keyword_research`(네이버 연관검색어→핵심어/브랜드/거래성/검색량≥2000/대상부적합 필터→검색량순) + 씨앗=`seo_keywords.yml` 카테고리 대표키워드. 네이버 검색광고 키 3종 존재 확인.
2. **추천 엔진** `writer/keyword_recommender.py`(PyQt 비의존·테스트 가능): 정의된 방식을 SEO 씨앗에 적용→검색량순 추천. 큐/시나리오에 이미 있는 주제 중복 제외. 네이버 실패 시 캐시 보조키워드로 자가복원(§0). custom_seed로 임의 주제 확장. 회귀 9건.
3. **CLI `keyword-recommend`**(--seed·--limit·--no-live·--add-top) + doctor 진입점(64→65). 오프라인·**네이버 라이브 검증**(컴퓨터의자 32,000·게이밍의자 29,400 등 실검색량 정렬).
4. **대시보드 GUI**: 🎯 추천 키워드 버튼 + `RecommendDialog`(검색량·경쟁도·씨앗·출처 표시, 행 선택 추가 / ⭐ 1순위 자동 추가) + custom seed 입력. 추천 조회 백그라운드(UI 비프리징). 오프스크린 구성 검증.
5. **메뉴 순서 재정렬(요청)**: 키워드 → 발행 큐(글) → 카테고리·모니터링 → 설정 (작업 시작점이 맨 왼쪽).
6. **off-target 근본수정**: 라이브 검증서 `노트북 거치대` 씨앗(핵심어 '거치대' 광범위)이 핸드폰·자전거·태블릿·갤럭시탭 거치대 혼입 적발 → `seo_keywords.yml` laptop-stand에 `exclude_terms`(폰·태블릿·테블릿(철자변형)·아이패드·갤럭시탭·자전거·오토바이·차량) 추가→재검증서 제거 확인(노트북받침대 등 온타겟 유지). ★남은 `책·모니터 거치대`는 편집 판단 사안이라 미적용(주인 결정용·#27).
7. 회귀 **773→782**(+9). ruff·black·mypy 클린. CLI 28→**29**.

**무인·안전(§0)**: 추천=네이버 읽기전용(무료·게시 아님). 자가복원(네이버 실패→캐시). 중복 제외. 기존 add_keyword 재사용(articles 스키마 무손상). off-target 근본수정+재발방지 가드(exclude_terms).

**잔존/다음(#27)**: ①**머지+대시보드 재시작 필요**(현재 워크트리 → 라이브 대시보드 미반영). ②재시작 후 **추천→첫 글 생성**(원래 (A) 목표·DeepSeek 비용·품질 1회 확인). ③off-target 씨앗 추가 curation(책·모니터 거치대 등 판단 사안·받침대 발받침 모호). ④#25 잔존: 아이콘 main 재지정·mini-dehumidifier 점검·★★쿠팡 본격·★성장 Tier0+측정.

---

### 세션 #25 — 2026-06-14 (Opus 4.8 1M, ★운영 대시보드 전면 구축 — PyQt5 GUI(키워드 큐·글 생성·승인·발행·예약·쿠팡 수동·설정창) + 마이그레이션 007, 회귀 693→773)

**시작 상황**: origin/main #24. 주인이 AutoBlog 데스크톱 대시보드(PyQt5)를 보여주며 "혼살림에도 (알리+쿠팡이라 업그레이드된) 운영 대시보드 — 실제 발행·모니터링·대기키워드·키워드별 제품 미리입력·스케줄러 발행"을 요청. 선승인 3건(①글 발행 스트림+모니터링 ②1클릭 승인 게이트 유지 ③쿠팡 공식위젯·텍스트) 받고 6단계(A~F)로 진행.

**핵심 진척 [확정]** (전부 로컬·미배포·비용 $0 — 인프라/GUI):
1. **(A) 설정 외부화 + 키워드 DB**: `common/settings.py`(config.json·견고성=깨지면 기본값) + 마이그레이션 **007** `keyword_queue`(채널 ali/coupang/both·상태·target_products JSON·persona/budget) + `drafts.keyword_id`. DB v6→**v7**.
2. **(B) PyQt5 대시보드**: `dashboard/app.py`(GUI 셸) + `dashboard/queries.py`(읽기 로직·테스트 가능). 통계카드·4탭(발행큐/키워드/모니터링/설정)·실시간 로그(AutoBlog QThread+stdout 가로채기 패턴). 로직/GUI 분리 → CI(PyQt 미설치) 안전. 오프스크린 스모크 테스트.
3. **(C) 키워드→시나리오 자동 브리지**: `writer/keyword_queue.py` — 키워드에서 시나리오 자동 파생해 기존 drafts→articles 발행 기계 재사용(★articles 스키마 무손상=라이브 무위험). CLI `keyword-add/generate/list`·`reject`. enrich은 DeepSeek/OpenRouter 라우팅 코드 검증(라이브 첫 생성은 미실행).
4. **(D) 예약 발행**: `publish-queue`(승인된 큐 N편 promote→build→deploy·**E7 준수=승인된 것만**) + `deployer/scheduler.py`(schtasks query/create/delete) + `schedule` 명령 + `run_publish_queue.ps1`. **기본 OFF**(C13 수동전환 취지·주인이 켤 때만).
5. **(E) 쿠팡 수동 등록**: `collector/coupang_manual.py` + `coupang-add` — 공식 파트너스 딥링크/위젯·텍스트(★함정#3 CDN 이미지 다운로드 금지). target_products에 적재→글 생성 후보. 15만원 후 API 모드.
6. **(F) 설정창 + 런처**: `SettingsDialog`(발행편수·예약시각·추천수·쿠팡모드/임계/태그·검증URL 등 편집) + `featured_per_tier`·`satisfaction_floor` 카테고리 빌더 연결(미지정 시 설정→기존 기본, 동작 불변) + 바탕화면 런처(`launch_dashboard.vbs`·`run_dashboard.ps1`) + **바탕화면 아이콘**(OneDrive 리디렉션 대응 양쪽 생성).
7. 회귀 **693→773**(+80). black·ruff·mypy 클린. CLI 22→**28** 명령.

**무인·안전(§0)**: E7 인간 승인 게이트 유지(자동 발행=승인된 큐만, 자동 '승인' 없음)·함정#3 준수·C13 수동전환 취지(예약 기본 OFF)·키워드→시나리오 브리지로 라이브 articles 무손상·발행/배포는 메인 체크아웃 한정(워크트리는 안전 정지)·설정 견고성·schtasks는 대시보드(주인 권한)에서 실행.

**잔존/다음(#26)**: ①**대시보드 라이브 첫 글 생성**(DeepSeek 비용·품질 1회 확인 — 구조/라우팅만 검증됨) ②**바탕화면 아이콘 main 재지정**(현재 워크트리 가리킴 → 머지 후 `D:\affiliate_hub`) ③설정 일부(쿠팡 모드/임계·llm_model·seo_max_attempts·jitter) 코드 연결 ④★**원래 #25 미완**: mini-dehumidifier 점검·쿠팡 본격(API 15만원 후)·★성장 Tier0+측정. 대시보드가 이 작업들(키워드 발행·쿠팡 수동)의 실행 도구가 됨.

---

### 세션 #24 — 2026-06-03~06 (Opus 4.8 1M, ★Tier0 SEO 품질강화 + 쿠팡 승인용 리뷰페이지 + 멀티채널·무인마케팅 전략 확정(DECISIONS S·T) / 스케줄러 수동전환 + subprocess UTF-8 근본수정, 회귀 678→693)

**시작 상황**: #24는 06-03 brave-babbage 워크트리(PR #5~9 머지)에서 EVENTS/STATE 미갱신 채 종료(미닫힘) → 06-06 예약 refresh-cycle 자동실행으로 재개, 주인 **스케줄러 수동전환 지시**로 마감. 06-03·06-06 작업을 #24로 함께 닫음.

**핵심 진척 [확정]**:
1. **(06-03) 멀티채널 전략 — DECISIONS S1·S2** (상세는 DECISIONS): C안(채널별 최선 추천+정성 기준), 가격비교형(A안) 표시광고법 위험 탈락, 게이팅=collector.coupang+데이터 후.
2. **(06-03) 무인 마케팅 전략 — DECISIONS T1·T2** (상세는 DECISIONS): 소수 정식계정+공식API(양산·버너 금지), SEO=본진·Pinterest=최우선, 알리 판매량=Information Gain 반전무기, Tier0→3 로드맵.
3. **(06-03) 쿠팡 승인용 `/reviews/` + Tier0 실행**: 흠플래닛 모니터암 리뷰페이지+쿠팡 제휴링크 글자노출(위젯 미표시 실측→텍스트). + Tier0 SEO 품질강화·홈오피스 필러(토픽허브)·카테고리 UX.
4. **(06-06) ★무인 refresh-cycle 첫 라이브 실행 — 자가복원 실증**: 예약작업 자동실행 → 공개 6개 새로고침 **6/6 성공**, **`mini-dehumidifier` 가드레일 미달(추천 1개<2)→자가복원 자동 비공개(fail-closed 정상작동)** → 공개 6→5, 빌드·push·verify **200**.
5. **(06-06) ★subprocess UTF-8 디코딩 크래시 근본수정**: 사이클 중 백그라운드 리더스레드 `UnicodeDecodeError`(한글 Windows cp949가 git/wrangler UTF-8 출력 디코딩 실패·비치명이나 잠재결함). `common.proc.run_text` 헬퍼(utf-8 강제=재발방지 가드)+6개 호출부 통일. 회귀 3종(실제 한글출력 무크래시 실증) **678→693**. push 03a3dbb.
6. **(06-06) ★스케줄러 수동전환(주인 지시)**: Claude 예약작업 `honsalim-refresh-cycle` **비활성화**(C11 폐기). 이후 refresh-cycle은 **주인 직접 지시로만 수동 실행**. 작업 폴더 삭제는 주인이 직접.

**무인·안전(§0)**: 자가복원 fail-closed **첫 라이브 실증**(mini-dehumidifier)·인코딩 크래시 근본수정+재발방지 가드·실패격리. 단 **스케줄러 수동전환으로 '완전 무인 자동배포'는 보류 — 주인 통제 우선**(§0과 균형: 주인 결정 존중).

**잔존/다음(#25)**: ①`mini-dehumidifier` 추천 1개 원인 점검(현재 라이브 비공개) ②**★★쿠팡 본격**(`collector.coupang` 구현·승인 절차) ③멀티채널 배치 구현(데이터 후·S1) ④**★성장** Tier0 지속+측정(GSC·네이버·Cloudflare) 리뷰. ★DB gitignore→재생성. refresh-cycle 수동(C13)=`PYTHONPATH=src python -m cli refresh-cycle --no-dry-run`.

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

> (세션 #19·#20·#21은 docs/archive/EVENTS_202606.md로 회전됨 — ARCHIVE 인덱스 참조)
