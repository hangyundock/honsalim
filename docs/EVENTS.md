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

## 최근 5세션

### 세션 #18 — 2026-05-31 (Opus 4.8 1M, 운영자 승인 게이트 + doctor 보강 + ★카테고리 페이지 디자인 디버깅·정형화(글씨 흐림 진짜원인=backdrop-filter), 회귀 569→590)

**시작 상황**: `/honsalim-start`(워크트리 beautiful-bose-63b4f9, HEAD=#17 `8710a5e`). 회귀 569. "다음 할 일 순서대로 진행" → #18 1순위 승인 게이트부터. 도중 디자인 작은 수정 요청이 카테고리 페이지 디자인 대거 디버깅으로 확대.

**핵심 진척 [확정]** (※전부 **로컬·미배포**. honsalim.com은 #13 첫 글 유지):

1. **운영자 1클릭 승인 게이트** (O21): `build-category`가 글 저장 시 **`status='draft'` 고정**(AI 자동 published 차단·E7, 재빌드 시 재승인 강제) · **`approve-category`/`unapprove-category` CLI** · `writer/category_state.py`(approve/unapprove/pending_approval+전이검증+부분DB 견고성) · renderer **`published`만 렌더**(+`include_drafts` 미리보기) · 대시보드 "카테고리 승인 대기" 섹션.
2. **doctor 보강** (#18-3): §10 진입점 **64**(category_state·category_page_builder·concept_image·category_collect 등 6 추가, 64/64 OK).
3. **★카테고리 페이지 디자인 디버깅·정형화** (O22, 사용자 라이브 피드백 다수·수십 분): 글씨 "흐리고 뭉개짐" 디버깅 — 색·폰트·굵기·크기·smoothing 다 만져도 안 됨 → 사용자 직관("뭔가 가미됨")으로 **진짜 원인 = `backdrop-filter`**(헤더 유리효과 → Windows Chrome 페이지 전체 텍스트 GPU 합성 → ClearType off → 흐림) **제거**가 근본 해결. 그 외: 본문색 #111 · 폭 1080px 단일칼럼 · 정보성 글씨 최소 14px · 마크다운 `**`→`<strong>` · 흔한실수 줄바꿈 · FAQ Q/A 구분(배경+마커) · 추천카드 장점/단점 그룹 · 가격+할인 같은 줄. 폰트 NanumSquare Neo 유지(나눔고딕 실험 후 사용자 선호로 복귀; cdnfonts NanumSquare Neo는 중간두께 없음·weight 400). **정형화 확인**: desk 수정 → monitor-stand 자동 동일(공통 CSS·템플릿·renderer).
4. **#18 2순위 배포 진행**: 이 워크트리에 DB 재생성(desk·monitor `collect-category`+`build-category` --no-dry-run 라이브, 게이트 통과, **draft**). 디자인 확정. **승인+공개배포는 #19**.
5. **회귀 569→590** (+21: category_state 9·renderer published게이트/마크다운·design_tokens 가드 3·cli 3 등). black·ruff·mypy 클린. 비용 ~$0.6.

**무인·안전/진실성(§0)**: AI 자동 published 차단(E7) · 미승인 draft 완전 비공개 · 마크다운 XSS escape 후 변환 · 대시보드 부분DB 견고성 가드 · 디자인은 코드(공통)라 새 카테고리 자동 적용 + 재발방지 가드(색 대비·정렬·승인전이). 미리보기 캐시→강력새로고침/시크릿창.

**잔존 미해결 (#19)**: ①**카테고리 페이지 추가 디자인 수정**(사용자 "이 페이지 수정할 부분 더 있다" — 연속 작업) ②#18 2순위 배포 완료(승인+공개) ③나머지 카테고리(의자 build·모니터암 신규) ④(이월) /go/·알리 whitelist·main-protect.

**다음 세션 할 일**: 1) **카테고리 디자인 연속 수정**(DB 재생성→`build --preview`로 확인하며) 2) **승인(`approve-category`)+배포**(`build --full`→honsalim.com) 3) 나머지 카테고리. ★DB는 gitignore→재생성 필요(`collect-category`·`build-category` --no-dry-run, ~$0.6). 워크트리 실행=`PYTHONPATH=src python -m cli`.

---

### 세션 #17 — 2026-05-31 (Opus 4.8 1M, ★카테고리 자동 등록 파이프라인 완성 + 사무용 의자 구성 표준 + 개념이미지(Imagen) + CLI + 정형화 입증(책상), 회귀 553→569)

**시작 상황**: `/honsalim-start`(워크트리 sad-wilbur-47961d, HEAD=origin/main #15–16 `ec6c3e4`). 회귀 553. 사용자 "다음 작업 진행"→#17 카테고리 구조. 도중 **"오늘 카테고리 제품 하나씩 실제 등록 테스트"** 요청 → end-to-end 파이프라인 구축으로 전환. 사용자가 의자(시안 있음) 대신 **모니터 받침대**(시안 없음)로 진짜 자동 등록 검증 지시.

**핵심 진척 [확정]** (※전부 **로컬·미배포**. honsalim.com은 #13 첫 글 유지):

1. **카테고리 데이터 모델** (O16): `categories`·`category_products` 테이블(migration 002~005) + `products` 정가/할인 컬럼 + products_store 저장 정합. seed=의자·책상·모니터. **렌더러가 DB 읽음**.
2. **카테고리 수집·정제·2티어** (O20): `collector/category_collect.py`+`category_sources.yml`. product_filter 관련성·부풀린할인 차단. 모니터 60→41·책상 59→28 정제.
3. **글 자동 생성** (O17): `enricher/category_page_builder.build_and_save` — 가이드8요소·추천6선(+타입)·FAQ·제품명비교표 JSON → disclosure → **SEO+진실성 통합게이트 통과까지 재생성**(상한2, 1인칭 fail 자동 재생성=자가복원) → 저장. 추천6선=AI 큐레이션(점수 금지). 비교표 확인불가="—".
4. **사무용 의자 구성 표준** (O18, 사용자): 공정위고지·타입선택기·신뢰박스2·**배너형 개념이미지**·타입표·체크리스트2열·추천2티어·한눈비교표·FAQ·전체카탈로그·**연관카테고리 크로스링크**. `category.html`·`categories_index.html`+`category.css`(.catpage 스코프).
5. **개념 이미지** (O19, 사용자): Imagen 4 Fast(AutoBlog 이식·REST·$0.02). ★**이미지엔 텍스트 없이 + 문구·CTA는 CSS 오버레이**(AI 한글 깨짐 방지·**SEO 노출**·수정 용이). webp(Pillow ~37KB). `GOOGLE.env`.
6. **CLI + 정형화 입증** (O20): `collect-category`·`build-category`. **책상 2명령 자동완성**(collect 59→28 → build 글+이미지+게이트 자동, 모니터와 동일 구조) — 정형화 라이브 입증.
7. **회귀 553→569** (+16). black·ruff·mypy 클린. 비용 ~$0.6.

**무인·안전/진실성(§0)**: 가짜 점수·평점 금지(추천=큐레이션) / 비교표 확인불가="—"(없는 스펙 금지) / 1인칭 fail 자동 재생성 / 부풀린할인 차단 / 이미지 텍스트 없이(SEO·정직) / 전부 로컬(배포 승인 후). **근본수정**: products_store 정가/할인 저장 · test fixture=마이그레이션 단일소스 · 전역 `.chk` 충돌(클래스 분리) · Jinja `group.items`/`c.values` 메서드 함정(키명 변경).

**잔존 미해결 (#18)**: ①**운영자 검토·1클릭 승인 게이트**(§2-마·E7 — 현재 build-category가 published 바로 전이) ②**배포**([6][7], build/site 갱신) ③doctor 보강(category 모듈) ④나머지 카테고리(모니터암 신규·의자 글생성) ⑤(이월) /go/·알리 whitelist·main-protect.

**다음 세션 할 일**: 1) **운영자 승인 게이트**(published→pending+1클릭 승인) 2) **배포**(build/site 갱신→honsalim.com) 3) doctor 보강·나머지 카테고리. ★워크트리 실행=`PYTHONPATH=src python -m cli`(honsalim 명령은 메인 가리킴).

---

### 세션 #15–16 — 2026-05-31 (Opus 4.8 1M, ★SEO 자동 최적화 엔진 + 전체제품 카탈로그 + ★디자인 大전환(우드톤→흰바탕 노써치) 1단계, 회귀 472→553)

> 한 연속 세션이나 작업량이 커서 **코드 주석을 2단계로 태깅**: **#15=SEO 엔진** / **#16=카탈로그·디자인 전환**. 둘 다 본 세션. **다음 세션은 #17.**

**시작 상황**: `/honsalim-start`(워크트리 blissful-poincare, HEAD #14 `d883fd6`). 사용자가 "카테고리 페이지 SEO 최적화"부터 요청 → 연속 진행.

**핵심 진척 [확정]** (※전부 **미배포·로컬**. honsalim.com은 #13 옛 사이트 유지):

1. **SEO 키워드 자동 최적화 엔진** (DECISIONS O10·O11): ①`validator/seo.py` 게이트(밀도·배치·보조키워드, opt-in payload["seo"], **하드 fail=대표키워드만**·네이버 1.7% 기준) = 5번째 검증 게이트 ②`collector/naver_searchad.py`(검색광고 API HMAC 클라이언트)+`keyword_research.py`(연관검색어→필터→보조 선별)+`seo_keywords.yml`(**office-chair·desk** 엔트리) ③`enricher/seo_directive.py`(2층 배치 지시)+`seo_regenerate.py`(게이트 통과까지 재생성). **라이브**: 사무용 의자 665개·컴퓨터 책상 874개 연관어→자동 선별.
2. **모델 Haiku→Sonnet + 비용 과다청구 방지** (O12): `DEFAULT_MODEL=claude-sonnet-4-6`. tistory #7·#10 교훈 이식(재시도 상한 2·게이트 과민완화·다운스트림 생략·사전점검). **책상 가이드 라이브 생성**: Sonnet 1회 통과·밀도 1.67%·보조 12개 자연삽입·**$0.049**.
3. **전체 제품 카탈로그** (O13): 노써치 종합점수 흉내 금지 → **점수 없는 가격·할인·타입 카탈로그**. 시안 `scripts/all_products_prototype.py`(데이터주도 `render_catalog`)+표준 `CATEGORY_PAGE.md §5-bis`. **책상 실수집 렌더**: 185 수집→오염 114 제거→유효 69 렌더 검증.
4. **상품 데이터 품질 필터** (O14): `collector/product_filter.py` — 관련성(핵심어·액세서리/브랜드/off-target 제외)+부풀린할인(>70%) 차단. `map_product`에 `original_price_krw`·`discount_pct` 추가(in-memory; **DB 컬럼은 추후**).
5. **★디자인 大전환 1단계** (O15·O3 구현): 라이브 사이트가 **옛 우드톤·페르소나 중심**임을 로컬 확인 → 확정 시안(흰 바탕·NanumSquare Neo·녹색) **렌더러 이식**. `static/css/tokens.css` 팔레트/폰트 1파일 교체로 **전 페이지 전환**(components/pages가 토큰 기반)+`base.html` 폰트+`header.html` 카테고리 네비. **`build/preview` 렌더·검증**(eval: bg흰색·NanumSquare·accent녹색·nav=홈/카테고리/구매가이드/세팅/About).
6. **회귀 472→553 PASS** (신규 SEO·카탈로그·필터 테스트 다수). black·ruff·mypy 클린.

**진행 순서 확정** (O15, 사용자): **디자인 토대→카테고리 구조→제품 렌더**. (1단계 디자인 완료)

**무인·안전/진실성(§0)**: 가짜 점수·평점 금지(카탈로그) / 부풀린 할인 차단 / 비용 과다청구 근본대책(tistory 교훈) / 오염 상품 필터 / 디자인은 로컬만(배포는 승인 후).

**잔존 미해결 (다음 세션 #17)**:
- **2단계 카테고리 구조**: 카테고리 인덱스(`/categories/`)+라우트+**홈 콘텐츠 카테고리화**(현재 페르소나 구조, **디자인만 새것**)+네비 `카테고리`·`구매가이드` 링크 배선.
- **3단계 제품 렌더**: 카테고리 페이지(가이드+비교카드+전체제품)를 **렌더러 `builder/renderer.py`에 이식**(현재 home/hub/persona/article만, 카테고리·전체제품 미지원)+**DB 영속화**(정가/할인 컬럼·수집 저장 — 렌더러는 DB를 읽음).
- **배포**: 새 디자인+카테고리 → build/site → honsalim.com(방법A, **사용자 승인 필요**).
- (이월) /go/ 링크 작동·알리 whitelist 답변·용어배포 확인·main-protect 재활성화. (미리보기 = `build/preview`)

**다음 세션 할 일**: 1) **2단계 카테고리 구조**(카테고리 인덱스+홈 카테고리화+라우트) 2) **3단계 렌더러 이식+DB 영속화**로 **책상 카테고리 페이지를 실데이터로 build/preview 완결**→확인 3) (승인 후) 배포.

---

### 세션 #14 — 2026-05-31 (Opus 4.8 1M, ★용어 일상화 + 사이트 大전환 기획(카테고리 비교·정보 사이트, 노써치형) + 카테고리 페이지 프로토타입, 회귀 470→472)

**시작 상황**: `/honsalim-start` → 워크트리 hopeful-kirch-af444e(HEAD=origin/main=9a722a7 #13). 회귀 470. 사용자가 라이브 첫 글을 보며 연속 개선 요청.

**핵심 진척 [확정]**:
1. **용어 일상화 (AI 자카 제거→신뢰)** [확정 사용자]: 시나리오→**내맘대로 세팅**(합성어 자리 "세팅")·페르소나→**라이프스타일**. 화면(템플릿 6)·renderer 문자열(meta·JSON-LD)·enrich 프롬프트 7·라이브 첫 글 본문 H2(DB body_md/html/hash 정합 정정) 교체. URL/코드/DB 내부명 유지(방문자 무관·위험). **재발방지 가드 테스트**(렌더 결과에 두 단어 0건). 회귀 470→**472 PASS**. build/site 재빌드(0건 확인, 배포 대기). ※**"AI가 작성" 비노출**(저자=운영자 "혼살다") 원칙 확정.
2. **사이트 大전환 기획 확정** [확정 사용자]: 노써치(nosearch.com) 정밀분석(메인·구매가이드·intro·에어컨 픽) → **"카테고리 우선 제품 비교·정보 사이트"**로 전환. 표준 `docs/CATEGORY_PAGE.md`(12컴포넌트)+콘텐츠 8요소+정직 큐레이터 포지셔닝(테스트 없음→스펙·기준 종합). **DECISIONS O 신규(O1~O9)**.
3. **카테고리 페이지 프로토타입** `scripts/category_page_prototype.py`(사무용 의자): 흰 바탕·NanumSquare Neo·💰실속(라이브 수집)/⭐고급 2분류 비교카드·한눈비교표·신뢰박스·8요소 가이드·정직 문구·독창 헤더.
4. **알리 API 라이브 검증** [확정]: collect-products로 사무용 의자 ~60개 수집(**구체검색어+가격밴드=진짜 제품**, 일반어+저밴드=액세서리만). **productdetail.get=product.query 동일 필드** — 가격/정가/할인율·이미지갤러리·카테고리 제공, **평점·구조화스펙·후기 미제공**(가짜 평점 금지). **가격 드리프트 실측**(게이밍 105,200→239,264 2배 → 빌드시 재조회·기준시각·재선정 규칙).
5. 신뢰 신호 = **정가→판매가+할인율**(가짜 평점 폐기) · "후기" 과장 문구 제거 · 공정위 고지 위치(2024.12 개정) 확인 · 알리 이미지 핫링크 정책.

**무인·안전/진실성(§0)**: 가짜 "긍정평가"·"후기" 주장 발견 즉시 제거. 가격 stale 발견→재조회 규칙화(O7). 경쟁사(노써치) 카피 우려 점검→구조만 참고·표현 원본화. 라이브 수집/배포는 사용자 승인 후.

**잔존 미해결 (다음 세션)**:
- **★본구현(자동화) 미완**: 콘텐츠 파이프라인(8요소·혼살다·진실성게이트)·카테고리별 2티어 수집·정가/할인 필드+가격재조회·렌더러 category 이식·"더보기"(전체제품) 페이지. (현재 목업 — `docs/design_drafts`·`tmp_*`·`data/`·`launch.json` gitignore라 새 워크트리엔 안 넘어옴 → 커밋된 `docs/CATEGORY_PAGE.md`+`scripts/category_page_prototype.py` 참조, 수집 재실행)
- 용어 교체 배포 반영 확인 · /go/ 링크 미작동 · 알리 이미지 허용 확인 · 네이버 폰트 확정(Chrome) · 알리 whitelist 답변.

**다음 세션 할 일**: 1) **페이지 재설계 본구현**(파이프라인→2티어 수집→가격재조회→렌더러→더보기) 2) 용어 배포 반영 확인 3) /go/ 링크 작동.

---

### 세션 #13 — 2026-05-30 (Opus 4.8 1M, 게시 경로 완성·★첫 글 honsalim.com 라이브 게시·무인 배포 파이프라인(방법 A)·알리 whitelist 2채널 제출, 회귀 436→470, 1 commit e763e0f 배포 success)

**시작 상황**: `/honsalim-start` → 워크트리 `laughing-raman-13b581`(main=origin/main=7b572ad #12, 0/0 동기). 회귀 436. "잔존작업 정리 후 게시 경로 배선" 사용자 지시.

**핵심 진척 [확정]**:

1. **잔존작업 정리**: 문서 stale 정정(#12 워크트리 병합 이미 완료 확인·cap STATE 10KB↓)·**codeql v3→v4**. 잔존 워크트리 5개 폐기는 수동 거부로 보류.

2. **게시 경로 핵심 완성** (조사로 진짜 갭 발견 — 본문에 제휴 링크 0개라 순수 prose=수익0):
   - `extract_disclosure_first` **제휴처 무관 근본수정**(알리 글이 None→promote NOT NULL 위반하던 잠복버그 + 회귀 가드)
   - **promote CLI**(`cmd_promote`): enriched→article_fields 조립(md→HTML·slug·content_hash·disclosure)·`promote_to_article`·**`link_article_products`**(featured→article_products=/go/ 소스). 검증된 body_md 무변형(content_hash 무결)
   - **renderer 상세글**: articles⋈article_products⋈products → article.html → `articles/<slug>/index.html` + `.art-body` prose CSS
   - **article.html 실데이터화**(목업→body_html 산문 + 실제 product_card `/go/`·`rel=sponsored nofollow`) · **시나리오 카드 404 방지**(글 없으면 비클릭 "준비 중")
   - 라이브 검증: draft 6→article 1(8 제휴상품·실가격·고지). 데스크톱 3열/모바일 1열 반응형 확인

3. **D1 slug_map 동기화**: `tracker/slug_map.py`(published 상품→D1 UPSERT·SQL escape·dry-run 기본)+`sync-slugmap` CLI+`sql/d1/schema.sql`. dry-run 실데이터 검증(렌더 /go/ 8개와 동일집합). **d1_aggregator `clicks.timestamp→ts` 버그 근본수정+가드**(라이브 집계 실패 잠복).

4. **무인 배포 파이프라인 (방법 A — DECISIONS N2)**: `.gitignore` build/site 커밋 허용 · `build.yml` 재작성(test 게이트→build/site 검증→`pages deploy build/site`, CI 재빌드 없음) · robots.txt·_headers · renderer LF · pre-commit build/site 제외.

5. **★첫 글 go-live [확정]**: e763e0f(40파일, build/site 포함) commit → `git push origin HEAD:main`(FF) → **GitHub Actions deploy success**(CI 470 통과·CF_API_TOKEN Pages 권한 확인). honsalim.com placeholder→진짜 사이트(첫 글 "홈오피스 50만원 세팅" 8 제휴상품·고지) 라이브 검증.

6. **알리 whitelist 2채널 제출 [확정 사용자]**: ①이메일(새벽 affiliates@service.alibaba.com) ②**포털 XFeedback**(portals.aliexpress.com 우하단 봉투, 'ali' 오탐 해명+스크린샷 증거, My Feedbacks "To do"). **사이트등록폼은 'ali' 자동검증으로 Submit 불가 확정** → 사람 화이트리스트만 길. 채널유형=Content/Vertical sites 안내.

**무인·안전**: 배포 deny-list 확인(`wrangler deploy`·`honsalim deploy` Claude 차단=의도된 §2-라/마 장치) → 방법 A로 CI 배포. pre-commit이 mypy·line-ending 잡음(훅 정상). §0 원칙대로 발견 버그(d1_aggregator) 근본수정.

**잔존 미해결 (다음 세션)**:
- **★/go/ 제휴 링크 미작동(수익 직결)**: D1 slug_map 라이브 쓰기(`sync-slugmap --no-dry-run`, deny-list라 사람/CI) + go_gateway Worker 배포(deny-list). 현재 "추천 보기"→홈.
- 상품 이미지(우드톤 placeholder, 의도) · 시나리오 추가 글(현재 1편) · 알리 답변 대기 · 로컬 main pull(origin e763e0f, 로컬 main 7b572ad) · main-protect 재활성화.

**다음 세션 할 일**: 1) **/go/ 링크 작동**(D1 동기화+go_gateway Worker 배포)→첫 글 수익화 2) 상품 이미지 보강 3) 알리 whitelist 답변 확인(무응답 3~4영업일 시 follow-up)
