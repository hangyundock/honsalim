# EVENTS.md — 혼살림 세션 로그

> 자동 회전: 6번째 세션 시 가장 옛 세션이 docs/archive/EVENTS_YYYYMM.md로 이동.
> 옛 세션 검색은 ARCHIVE 인덱스 참조 후 archive/ 폴더 grep.
> Cap: 20KB.

## ARCHIVE 인덱스 (옛 세션 한 줄 요약)

- [EVENTS_202606.md](archive/EVENTS_202606.md):
  - 세션 #19 (2026-06-01 DeepSeek v4-pro 전면전환·카테고리 디자인 마무리·관련성 필터 require_all 근본수정·판매량 기준 추천 6선·신규 2카테고리·회귀 590→623)
  - 세션 #20 (2026-06-02 카테고리 4개 라이브 배포·홈 카테고리우선 大리디자인·배포 wrangler/산출물청소/HTML캐시 버그 4종 근본수정·회귀 623→632)
  - 세션 #21 (2026-06-02 도메인 honsalim→honsallim 이전·연결·301(알리 'ali' 차단 돌파)+알리 채널 등록+미충전이미지·순차등록엔진·홈 흰바탕캐시 근본수정·회귀 632→641)
  - 세션 #22 (2026-06-03 자율 게시 가드레일(E7→fail-closed)+살림3 합치기+8개 자동공개 라이브배포+측정인프라3종+/go/ Pages Function 수익경로 복구·개발 마무리→성장 전환·회귀 641→659)
  - 세션 #23 (2026-06-03 무인 스케줄러 A안(refresh-cycle) 구축+모니터링 대시보드+메인 체크아웃 정비+쿠팡 활성화 착수·회귀 659→678)
  - 세션 #24 (2026-06-03~06 Tier0 SEO 품질강화+쿠팡 승인용 /reviews/+멀티채널·무인마케팅 전략(DECISIONS S·T)+스케줄러 수동전환+subprocess UTF-8 근본수정·회귀 678→693)
  - 세션 #25 (2026-06-14 ★운영 대시보드 전면 구축 PyQt5 GUI(키워드 큐·글생성·승인·발행·예약·쿠팡 수동·설정)+마이그레이션 007 keyword_queue·DB v7·회귀 693→773)
  - 세션 #26 (2026-06-14 추천 키워드 생성 엔진(keyword_recommender)+대시보드 메뉴 순서 재정렬+노트북거치대 off-target exclude·회귀 773→782)
  - 세션 #27 (2026-06-14 '글 생성' 자동 키워드 선정(원클릭)+발행큐 맨위 자동+PR 자동화 논의·회귀 782→787)
  - 세션 #28 (2026-06-14 쿠팡 하이브리드 글—naver_blog식 원팝업+알리 데이터 결합+쿠팡 공식배너 이미지·회귀 782→806)
  - 세션 #29 (2026-06-14~15 ★B-i 무인 자동발행 전체(article_state·guardrail·auto_approve·auto-cycle·auto_mode OFF)+naver_blog 흐름 GUI+미리보기 버그수정+PR 자동머지·구글정책 정정·회귀 806→846)
  - 세션 #30 (2026-06-15 A 키워드 알리 영어검색 근본수정+doctor 게이트 복구+B 진행표시+★첫 라이브 글 발행(게이밍의자)+발행 build/site 커밋버그 적발+글 레이아웃 Tier2 재설계·회귀 846→851)
  - 세션 #31 (2026-06-15 ★카테고리 분류체계(대/중/소)+게이밍의자→'의자' 타입흡수+쿠팡 운영자추천 zone·정식 대가성+추천 8선+라이브 배포·회귀 851 유지·main ea2460e)
  - 세션 #32 (2026-06-15 운영 DB 반영(#31 미완·주인 런처 이식)+쿠팡 카드 광고차단 폴백+운영 대시보드 4기능(키워드삭제·카테고리쿠팡·원스톱 빌드배포·쿠팡존)+쿠팡 3선 균형 라이브·회귀 851→865·main e3a2219)
  - 세션 #33 (2026-06-15 ★무인 글 생성 파이프라인 완성 — SEO 주입·자가복원 재생성 루프·winnable 선정·초기검수 안전장치(min_published)·발행→라이브 버그 근본수정·회귀 865→873·main 3a96c49)
  - 세션 #34 (2026-06-16 글 렌더링=카테고리 구성 통합(category.html 재사용)·완전무인 골격 보강(auto_pick·스케줄러 reconcile·자동 migrate)·품질 대수술·migration 008 structured_json·회귀 873→896·main e9e3fd2)
  - 세션 #35 (2026-06-16 무인 발행 라이브 실증+글=카테고리 흡수(고아·중복 해소)+채널 역할분리(naver_blog 볼륨/honsalim 허브)+비전 게이트·자동 카테고리 생성·회귀 896→932)
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

### 세션 #40 — 2026-06-28 (Opus 4.8, ★성장 색인 토대 감사·정비 — 고아 글 해소·JSON-LD/사이트맵·파비콘·robots + GSC·네이버 라이브 확정, 회귀 989→996, main 배포·curl 검증)

**시작 상황**: `/honsalim-start`(#39 7146042). 주인 "성장(색인 토대 점검) 시작". 색인 토대 코드+라이브 감사→결함 근본수정·라이브 배포·검증.

**핵심 [확정]** (검증·main·라이브 curl. 상세 DECISIONS Y): ①6차원 감사+적대검증 — sitemap·robots·canonical 정상 / IndexNow 미구현(Bing용·무관) / 네이버·GSC는 콘솔 확인(오진 1 정정). ②**발행 글 고아 해소**(Y2): 글이 시나리오 카드(active=1)로만 닿아 active=0이면 사이트맵에만 존재(크롤·트래픽 0) → 홈·가이드허브·토픽카테고리 내부링크(시나리오 무관·`_article_guide_cards`). 라이브 inbound 0→복수. ③**JSON-LD 렌더 재생성**(Y3): canonical 끝슬래시·headline=글제목(IDX-03·04)·**사이트맵 lastmod**(Y4). ④**파비콘**(Y5): `/favicon.ico` 소프트404 해소(.ico+.svg 루트·라이브 image 200)·**robots `/cdn-cgi/` 제외**(Y6). ⑤**★GSC·네이버 둘 다 등록·사이트맵·크롤링 정상 확정**(Y1·주인 콘솔) — 토대 문제 아님·병목=색인 커버리지(각 색인 4·미색인은 신생 정상·내부링크가 레버). 회귀 989→**996**(+7). 클린. main 902b294·4dfe327·a8697b8. build-deploy 라이브 검증.

**무인·안전(§0)**: 결함 테스트 가드+라이브 검증. 편집 운영폴더 오입력 2회→워크트리 재이전([[worktree-edit-path-footgun]])·빌드배포가 origin 전진→병합 ff([[autonomous-deploy-advances-origin]]).

**잔존/다음(#41)**: ①색인 커버리지 관찰(4→증가)·핵심 URL 색인 요청 ②**[관찰] 무인 스케줄러 실작동**(대시보드 마지막 실행 '2026-06-06'—22:02 실제 도는지) ③(이월) 씨앗 커버리지·E-E-A-T·IndexNow.

---

### 세션 #39 — 2026-06-27 (Opus 4.8, 무인 발행 블로커 근본수정(A·B·C 라이브) + 비판가 5인 적대검증 + 자가복원 1차, 회귀 961→989, main 푸시)

**시작 상황**: `/honsalim-start`(#38 48ac85a). 주인 "무인 단계 테스트가 이전 세션 성공 못 함 → 실제 스케줄에 맞춰 재테스트". 예약을 21:26·22:02로 직접 바꿔 라이브로 돌리는 과정에서 '글은 생성·5게이트 통과하나 발행 0편'을 연쇄 적발·근본수정(§0 fail-fast). 운영 폴더(D:\affiliate_hub)=main 48ac85a.

**핵심 [확정]** (검증·main·일부 라이브):
1. **Ⓐ 쿠팡 수동배너 자동승인 면제**(라이브 적발·DECISIONS X1): 21:26 회차 '무중력의자'(쿠팡3)가 생성·5게이트 통과하나 자동승인 보류 — 원인=주인이 고른 쿠팡 배너를 office-chair `exclude_terms`(리클라이너·쿠션·소파)로 재검사해 거부(featured off-target 3=전부 쿠팡). → `eligible`이 `source=coupang` 면제. 22:02 재테스트로 **무중력의자 무인 발행→`honsallim.com/articles/kw-95e2ad52` 라이브 200**(사람 개입 0).
2. **Ⓑ 미매핑 사무의자 키워드 매핑**(X3): 메쉬·허리편한·학생용 의자가 secondary 미등록→무조건 보류 → office-chair secondary 추가. 입구 거부는 비채택.
3. **Ⓒ 키워드 글 SEO primary = 키워드 자신**(X2): 22:02 새 글 '등받이의자'가 seo `headings_keyword_low`로 rejected(광의 '사무용 의자'를 소제목 강요·rejected는 held에도 안 잡히는 침묵 정지). → `keyword_gate_config`로 키워드 자신을 primary·카테고리어는 보조. dry-run으로 draft #12 eligible False→True 실증.
4. **★자가복원 1차**(비판검증 후·X4·X5·X6): 주인 "근본적으로 막을 수 있나?" → 내 3제안(입구차단·skip·대시보드알림)을 비판가 5인(워크플로우·코드근거)으로 적대검증 → 결함 적발(추천엔진 자기파괴·생성前 판정불가·무인 중 대시보드 미열람·min_published 오경보) → 채택안 구현: `publishability` 단일판정·보류 `reason_code`·사이클 health 다이제스트(`auto_cycle_last.json`)/[ALERT](파일·로그)·생성 예외격리·발행가능 우선선정. 실 운영 큐에 dry-run 실증(발행가능 3/3·abnormal=false·오경보 없음).
회귀 961→**989**(+28). black·ruff·mypy(75파일) 클린. main 푸시(A·B·C **aaad6cb·b2933ff**·자가복원 **5774c50**).

**무인·안전(§0)**: fail-safe(나쁜 글 자동발행 안 됨)는 견고 유지 / 새로 fail-loud(자기보고) 추가. 막힌 키워드는 지우지 말고 강등+reason_code로 파일/로그 보고. 운영 배포=로컬 ff-merge(외부 push는 무인 발행이 자동 수행 — [[autonomous-deploy-advances-origin]]).

**잔존/다음(#40)**: ①**★성장 최우선**(주인 선택·[[growth-first-priority]]): 색인 토대 점검(GSC·사이트맵·IndexNow·네이버)·씨앗 커버리지 확장·E-E-A-T. ②무인 일일 발행(22:02) 관찰+자기보고 확인. ③(선택)Phase 2 자가복원: ali off-target·배포 drift·푸시 채널·git pull footgun.

---

### 세션 #38 — 2026-06-27 (Opus 4.8, ★완전무인 첫 라이브 발행 성공(0-falsy 버그 근본수정) + 빈글차단 + 무인 표준 문서화 + 글/카테고리 정형화·featured 8 통일, 회귀 950→961, main 푸시)

**시작 상황**: `/honsalim-start`(#37 395a1bb). 주인 "무인 가동 결정·실행". 운영 폴더는 이미 #37 동기화 확인. 주인이 **직접 무인을 켜서 라이브로 돌려보는** 과정에서 치명 버그·품질 문제를 연쇄 적발·근본 수정(§0 fail-fast).

**핵심 [확정]** (전부 검증·main·라이브):
1. **★완전무인 막던 0-falsy 버그 근본수정**(치명): `auto_approve_min_published=0`(완전무인)으로 설정해도 `int(settings.get(...) or 5)`에서 `0 or 5 = 5`로 강제돼 자동승인 영구 보류 → 글 생성되나 발행 안 됨. `settings.get_int/get_float`(0 보존) 헬퍼 신설·0 유효 설정 교체(무해/0=기본 곳은 원복). **주인이 직접 무인 켜서 라이브로 돌렸기에 적발**. 회귀 가드 5건. main **f026492**.
2. **★무인 자동발행 첫 라이브 성공**: 키워드(고용량멀티탭)+쿠팡 적재→예약 시각 auto-cycle→자동 생성·자동승인·발행·배포→`honsallim.com/articles/kw-625b3b85` 라이브(사람 개입 0). 0-falsy 수정 후 검증. 발행 후 404는 CI 배포 지연(버그 아님).
3. **빈 글 차단 가드**: 상품 0개 키워드('책거치대' 미매핑·쿠팡 미선택)는 LLM 호출 전 생성 중단·키워드 failed(수동·무인 공통·비용0). main **5405caf**.
4. **★무인 표준 작업 순서 문서화**(주인 강한 비판: 매 세션 같은 설명 반복·인수인계 단절): **키워드 선정도 자동**(씨앗 `seo_keywords.yml`→`keyword_recommender`(네이버 검색량·winnable)→`auto_pick_keyword`). '키워드 직접 입력'·'글 먼저 수동 생성' 안내 금지. CLAUDE.md §7 + **`docs/AUTOMATION.md`**(전체 파이프라인 표준·Claude 체크리스트) + DECISIONS C22·C23 + 메모리 보강. 추천 키워드 다중선택(체크박스·전체선택·행클릭). main **e4dda08·9c4bfa3·27faff5**.
5. **★글 정형화 근본수정**(워크플로우 4차원 분석으로 단일 원인 확정): 키워드 글이 매핑 카테고리 stale 컨텍스트를 통째 상속→자기 상품(쿠팡3+알리8) 폐기(쿠팡0·상단4·비교4). `_article_as_category_ctx`가 글 자기 picks/쿠팡/비교/카탈로그로 렌더하도록 보정 + 비교=픽 동수(옛 limit 6 제거). 라이브 검증 **쿠팡3·상단8·비교8**. 회귀 가드 2건. main **0e46125**.
6. **★featured 8 통일**: 글 `_article_featured` k=4(8)·카테고리 `featured_per_tier`(3=6) 불일치 → 둘 다 `featured_per_tier` 단일소스·기본 4(=8). 카테고리 6개 LLM 재빌드(featured 8·compare 8·truth/disclosure/links/SEO 게이트 통과)→`approve-category`→빌드·배포→**라이브 카테고리 8 검증**(글도 8 유지). 카테고리·모니터링에 '🌐 카테고리 보기' 경로 추가(주인 지적). main **678f55a·4e37c40** + 배포 **4875df2**.
7. **무인 ON/OFF 토글 + 9초 프리징 근본수정**: 상단 무인 토글(라디오버튼 오해 해소)+예약 재등록을 백그라운드로(schtasks 메인스레드 3회 동기호출→UI 9초 프리징 제거·즉시 갱신). main **aa3a2a7·ddd0522**.
회귀 950→**961**. black·ruff·mypy 클린.

**무인·안전(§0)**: 0-falsy 수정으로 완전무인 가능(주인 min_published=0 선택)·빈글 차단·글 정형화=자기상품(키워드별 쿠팡 반영)·featured 정형성. 카테고리 재빌드는 draft→사람 승인(§2-마). 라이브 게시(build-deploy)는 보안 가드로 주인만 실행.

**잔존/다음(#39)**: ①**무인 운영 지속 관찰**: 예약 19:15·auto_mode ON·min_published=0 상태 — 매일 자동 발행되는 글 품질 사후 검토(발행 글 관리 탭·monitor 2겹 그물). 키워드/쿠팡 큐 적재 보충. ②(이월) `review-helpfulknow` 월 상한(무인 폭주 방지)·쿠팡 수동 배너 부트스트랩(15만원→API)·★성장=트래픽(GSC 색인·[[growth-first-priority]]).

---

### 세션 #37 — 2026-06-27 (Opus 4.8, ★Google 프로젝트 분리(티스토리 한도 탈출) + 대표이미지 라이브 + 무인 운영모델 정밀검증(이미 구현 확인) + 발행 글 관리 탭, 회귀 950→953, main 푸시)

**시작 상황**: `/honsalim-start`(#36 1608d95). #37-1 운영 동기화 착수 → git은 이미 #36에 동기화돼 있었고(문서가 stale) 대시보드 재시작으로 migration 009 적용. 이후 주인 질문 흐름으로 Google 분리·운영모델 검증·신규 기능까지 확대.

**핵심 [확정]** (검증·main):
1. **운영 동기화 실태 확정**: 운영 폴더 = origin/main = 1608d95(=#36 전체 코드) **이미 동기화**·STATE의 "미반영"은 stale. 대시보드 재시작→migration 009 적용(`api_usage` 생성). **GOOGLE_API_KEY 실제 경로 정정 = `D:\secrets\affiliate_hub\GOOGLE.env`**(STATE의 honsalim.env는 코드가 안 읽음·`config.load_secrets`가 affiliate_hub\*.env만 로드).
2. **★Google 프로젝트 분리(근본 해결)**: 혼살림 Imagen이 티스토리와 한 프로젝트(Tstory Gemini·₩40,000 한도)를 공유 → 티스토리가 한도 소진 시 혼살림 이미지 429(=#36 대표이미지 막힘 원인). → 빈 `review-helpfulknow` 프로젝트(이미 Tier1 후불=결제 연결)로 키 발급·GOOGLE.env 교체 → 실제 이미지 1장 생성으로 **429 없이** end-to-end 입증. 티스토리와 한도 독립.
3. **#37-2 대표 이미지 라이브**: mini-rice-cooker 히어로 생성(`3_run_cleanup.bat`·새 키)→빌드·배포→`honsallim.com/categories/mini-rice-cooker/` 라이브 검증(이미지 HTTP 200·50KB webp·페이지 히어로 참조). main **3b6d46c**.
4. **★무인 운영모델 정밀검증(워크플로우 6지점)**: 주인 모델(대기키워드+쿠팡 배너 저장→스케줄 자동 생성·발행→무관여)이 **이미 코드 전부 구현**됨 확인 — `target_products` 저장→auto-cycle(쿠팡첨부 우선)→`auto_approve`(fail-closed)→발행, 저장 쿠팡 **항상** 글 포함(끊김 없음). **코드 수정 불요·설정/운영만**(auto_mode ON+스케줄러+키워드/쿠팡+첫 5편 사람검수). 메모리 [[autopublish-operational-model]]·상세 DECISIONS C21.
5. **★발행 글 관리 탭(주인 역제안 채택)**: SEO 안전=사전 클릭 아닌 '품질 검수'가 본질(클릭은 구글 신호 0)→내 과잉권고 정정. → 완전 무인 + **발행 글 사후 검토**(AutoBlog식). 대시보드 '발행 글 관리' 탭(목록·라이브링크·비공개/재공개·행더블클릭)+`queries.list_articles`, 기존 `unpublish/republish`(#29) UI 연결·비공개 시 sitemap 제외. 수정 미구현(=비공개+재생성). 회귀 950→**953**. main **a5930c6**.

**무인·안전(§0)**: auto_mode 기본 OFF·자동승인 fail-closed·첫 5편 사람검수·발행글 2겹 그물(monitor 자동비공개+사람). Google 분리로 티스토리 한도 영향 제거.

**잔존/다음(#38)**: ①**무인 가동 결정·실행**: 키워드/쿠팡 적재→자동 생성 몇 편으로 품질 확인→좋으면 auto_mode ON+스케줄러 등록(주인 결정·C13 수동운영 뒤집기). ②발행 글 관리 탭 **운영 동기화**(운영 폴더 `git pull`(#37 a5930c6)+대시보드 재시작). ③(이월) review-helpfulknow 월 상한(안전)·쿠팡 수동 배너 부트스트랩·★성장=트래픽(GSC 색인).

---

### 세션 #36 — 2026-06-27 (Opus 4.8, ★provision-category 첫 라이브 실증 + 라이브 버그3종 근본수정 + 근본자동화 + 적대적리뷰 7건 보강 + Google지출 트래커, 회귀 932→950, main 푸시)

**핵심 [확정]** (검증·main·라이브): ①**provision-category 첫 라이브**(미니 전기밥솥 자동생성→승인→배포→`honsallim.com/categories/mini-rice-cooker/` 라이브·6단계 입증). ②라이브 버그 3종: `to_spec` 한글 core를 require_any 강제→알리 기계번역 매칭 굶음→`require_any=()`로 비전 전담 / 자동 카테고리 `category_sources.yml` 미등록→`append_category_source` 자동등록(멱등·원자적) / 가이드 `image_prompt` 누락→slug 폴백. ③적대적 16건 리뷰→핵심 7건 보강(`load_sources` 깨진 yml 방어 등). ④**Google 지출 트래커**(migration 009 `api_usage`+대시보드 월상한·추정). 회귀 932→**950**. 클린.

**잔존/다음(#37)**: 대표 이미지(Google 월상한 대기)·리뷰 별개 개선·성장 트래픽. ★운영 동기화(git pull+대시보드 재시작=migrate 009).

---

> (세션 #19~#35는 docs/archive/EVENTS_202606.md로 회전됨 — ARCHIVE 인덱스 참조)
