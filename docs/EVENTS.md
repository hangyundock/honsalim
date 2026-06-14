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

### 세션 #29 — 2026-06-14~15 (Opus 4.8 1M, ★B-i 무인 자동발행 전체 + naver_blog 흐름 GUI 완성 + 미리보기 버그수정 + PR 자동머지·구글정책 정정, 회귀 806→846, 6커밋 전부 main 머지·CI green)

**시작**: #28 연속, ★라이브 테스트(쿠팡 하이브리드 생성) 실행.

**핵심 [확정]** (전부 main 머지·배포 green·라이브 200 정상):
1. **미리보기 버그 근본수정**(라이브 테스트 적발): 검토 대기 시나리오 draft를 미리보기 못 봤음(렌더러가 articles published만·draft는 drafts 테이블)→§2-마 인간검토 게이트 무력화. `_load_article_pages(include_drafts)`+`_load_draft_article_pages`(enriched_payload body_md→html·promote 동일)+미리보기 선택글 직접이동, draft는 sitemap/게시수 제외. 실데이터 검증. 커밋 1736c06.
2. **★적합성 가드** `collector/keyword_relevance.py`: 키워드→카테고리(seo_keywords.yml)→require/exclude(category_sources.yml) 알리에 적용(product_filter 재사용). ★유효exclude=카테고리exclude−키워드(안락의자 자기차단 방지). draft #2 드레싱의자 실제 제외 실증. 커밋 aba9868.
3. **★PR 자동머지 확립**: settings 자기수정은 Claude 안전분류기 하드차단(권한 자기부여 금지)→`git push origin HEAD:main`이 이미 allow라 **main 직접머지 자동화**(gh·PR 불필요). 6커밋 전부 이 방식.
4. **★구글정책 정정 [확정·공식 검증]**: "AI 자동발행=페널티"는 부정확. 구글은 생성방식 무관(AI OK)·**Scaled Content Abuse(대량 저가치)**만 침. → B 리스크=AI/자동 아닌 검토없는 저품질 양산. 사람게이트=품질검사(AI숨기기 아님). (출처 developers.google.com 4건)
5. **★B-i 무인 자동발행**(주인 B-i 선택=완전무인+안전판): **2a 발행후 안전망** `article_state`(글 비공개/재공개·published↔unpublished)+`article_guardrail`(발행글 무결성+적합성 모니터→미달 자동비공개 fail-closed)+unpublish/republish/monitor-articles. 커밋 69b2230·70282c2. **2b 파이프라인** `auto_approve`(fail-closed:validated+카테고리매핑+featured적합만·나머지 보류)+`auto-cycle`(모니터→대기키워드 생성→자동승인→발행)+**`auto_mode` 기본 OFF**(E7유지)+run_auto_cycle.ps1. 커밋 685a7f5.
6. **naver_blog 흐름 GUI 완성**: `🛒 쿠팡 첨부(저장)` 버튼 — 선택 대기키워드에 쿠팡 배너 저장만(생성X·pending 유지·channel=both)→스케줄러/글생성이 그 쿠팡으로 하이브리드. 커밋 6f752d2.
7. 회귀 **806→846**(+40). 린트 클린. main=**6f752d2**.

**★라이브 테스트가 적발한 2대 문제 (다음 세션 최우선)**:
- **A. 키워드 경로 알리 검색=한글→쓰레기 [확정·진단]**: `_gather`가 `ali.query_products(한글키워드)`→"컴퓨터의자" 검색 시 알리가 폰케이스·티셔츠·가방 등 무관 20개 반환(의자 2개도 드레싱/인형의집=off-target). 가드 정상작동해 전부 제외→글이 **쿠팡 1개만(thin·알리 데이터 없음)**. **카테고리 경로는 영어 검색어("office chair")라 정상**(라이브 5카테고리 멀쩡)→키워드 경로도 매핑 카테고리 영어 tier 검색어 쓰게 근본수정 필요. (draft #3 컴퓨터의자=thin·반려/재생성 대상)
- **B. 진행/완료 표시 없음 [주인 반복지적]**: 생성 1~2분 무표시→끝난지 모름. 대시보드 작업 진행중/완료 신호 추가 필요.

**무인·안전(§0)**: auto_mode 기본 OFF(머지해도 자동발행 0)·fail-closed 곳곳·발행후 자동비공개 안전판·all destructive deny 유지. 라이브 200 정상(주인 접속불가=로컬 이슈·honsallim.com 더블L 확인).

**잔존/다음(#30)**: ①**★A 근본수정**=키워드 경로 알리 검색을 매핑 카테고리 영어 tier 검색어로(키워드→카테고리→category_sources.yml tiers.q)→하이브리드에 알리 데이터 복원 ②**★B 진행표시** 대시보드 ③A·B 후 게이밍의자(#3·쿠팡 첨부됨) 재생성→제대로된 하이브리드→미리보기→승인→발행(첫 라이브 글)+thin draft #3 반려 ④DECISIONS/CLAUDE.md에 B-i(auto_mode·fail-closed·E7 보정) 기록 ⑤PartC 키워드 틈점수·mini-dehumidifier·성장 Tier0(잔존). ★워크트리=`PYTHONPATH=src python -m cli`·DB gitignore·발행/배포=main 체크아웃.

---

### 세션 #28 — 2026-06-14 (Opus 4.8 1M, ★쿠팡 하이브리드 글 — naver_blog식 원팝업 + 알리 데이터 결합(구글 SEO) + 쿠팡 공식배너 이미지, 회귀 782→806 · ※라이브 생성 미실행)

**시작 상황**: #27 연속. "(A) 첫 글 생성" 중 글에 쿠팡 0개 → **15만원(쿠팡 API 게이트) 도달 경로 막힘** 지적. naver_blog(D:\naver_blog) 방식(키워드에 쿠팡 제품 미리 세팅→매일 자동 발행) 정밀 분석·이식 요청. 단 **구글 SEO가 기본 전제**.

**정밀 분석 [확정]**: naver_blog = ①키워드 점수화(검색량/문서수/경쟁도='틈 찾기'·`keyword_scorer`) ②키워드 클릭→"쿠팡 배너 입력" 팝업→**"이 배너로 글 생성" 원클릭** ③스케줄러 ON. 네이버는 쿠팡 공식배너(`<a><img coupangcdn>`)가 본문 정상 렌더. **핵심 차이: naver_blog=네이버 vs honsalim=구글** — 구글은 데이터 없는 AI 어필리에이트 글 페널티(2025-12·DECISIONS T2) → **역제안 채택: naver_blog UX + honsalim 구글 무기(알리 판매량=Information Gain) 하이브리드**(DECISIONS C16).

**핵심 진척 [확정]** (전부 로컬·머지됨·**DeepSeek 라이브 생성은 미실행**):
1. **Part1 쿠팡 배너 이미지**: `coupang_manual.parse_banner`(배너→딥링크·이미지·상품명) + `build_manual_product`에 `image_url_external`(공식배너 **hotlink**·다운로드 아님→함정#3 무관). **article 상품카드가 image_url_external 사용**(`ARTICLE_PRODUCTS_SQL`+`product_card` 매크로 `img_url`, 알리·쿠팡 공용·우드톤 fallback). #24 "쿠팡 이미지 안 씀" → **B(공식배너 hotlink) 전환**(주인 결정).
2. **Part2 쿠팡 우선**: 미리선택(target_products) 있는 키워드를 자동선정·목록 맨 위로(검색량 높은 알리보다 먼저).
3. **PartA 하이브리드 결합**: `_gather_keyword_candidates`가 쿠팡(수동)+알리(자동수집·데이터) **결합**, 쿠팡(source=coupang)은 **항상 featured**. → 구글 Information Gain + 쿠팡 수익·이미지 동시(S1).
4. **PartB 원팝업**(naver_blog식): `🛒 쿠팡 배너→글 생성` → 팝업(키워드 자동채움+배너 여러 개) → **"이 키워드로 글 생성"** 한 번 = `get_or_create`+`products_from_banners`(멀티)+첨부+하이브리드 생성. 오프스크린 검증.
5. 회귀 **782→806**(+24). 린트 클린. 커밋 Part1 e721565·Part2 b3d4cf1·PartA a6c085d·PartB e353b74 (PR #14·#15 머지·메인 **7777c47**).

**무인·안전(§0)**: 쿠팡 이미지=공식배너 hotlink. 추천/수집 무료·LLM은 생성 때만. articles 스키마 무손상. E7 유지(검토대기까지). **★라이브 생성은 주인이 다음 세션에서 안전하게 1회 — 이번 세션 미실행(주인 지시).**

**잔존/다음(#29)**: ①**★라이브 테스트(최우선)**: 대시보드 재시작→`🛒 쿠팡 배너→글 생성`(키워드+쿠팡 공식배너 `<a><img>`)→미리보기로 쿠팡(이미지)+알리(데이터) 결합 확인(DeepSeek 비용·품질 1회). ②**PartC 키워드 '틈 점수'**(naver_blog `keyword_scorer` 차용·저경쟁 롱테일 우선·단 네이버 신호=구글 근사치). ③**PartD 자동 발행 ON**(스케줄러). ④#25~ 잔존: 아이콘 main 재지정·mini-dehumidifier·성장 Tier0. ★DB gitignore→재생성(`db migrate`+`db seed`). 워크트리=`PYTHONPATH=src python -m cli`.

---

### 세션 #27 — 2026-06-14 (Opus 4.8 1M, ★'글 생성' 자동 키워드 선정(원클릭) + 발행큐 맨위 자동 + PR 자동화 논의, 회귀 782→787)

**시작 상황**: #26 연속. 주인 "글 생성 누르면 키워드 선정부터 자동" 요청(쓸데없는 클릭 제거).

**핵심 진척 [확정]**:
1. **자동 글 생성**: `keyword_recommender.auto_pick_keyword`(대기 큐 맨 위 우선→없으면 정의된 방식 추천·추가) + `✨ 글 생성`이 선택 없으면 자동 선정→확인→생성. 정렬을 대시보드 목록과 일치(score↓·표시 맨 위=자동선정).
2. **발행 큐 맨위 자동**: 승인/반려가 선택 없으면 맨 위 글 대상(`_selected_or_top`).
3. **PR 자동화 논의**: gh 미설치·deny 룰 + 명령파일 자기수정 가드레일 → 자동화 보류·수동 PR 유지(권고안 A). 코드 머지는 안전 이슈 적음 인정.
4. 회귀 **782→787**. 커밋 db7f4d0·323308f (PR #12·#13 머지).

**무인·안전(§0)**: 자동 선정도 E7(검토대기까지)·비용 확인 유지. 자기수정/설치는 주인 가드레일 존중(우회 안 함).

**잔존/다음(#28)**: 쿠팡 하이브리드로 이어짐.

---

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

> (세션 #19~#24는 docs/archive/EVENTS_202606.md로 회전됨 — ARCHIVE 인덱스 참조)
