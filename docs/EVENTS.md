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

## 최근 5세션

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

---

### 세션 #12 — 2026-05-30 (Opus 4.8 1M, 알리 상품수집 CLI→C-1 연결→enrich 풀구축→4게이트 통과 첫 글, 회귀 378→436, 10 commits, 워크트리 goofy-hopper)

**시작 상황**: `/honsalim-start` → 워크트리 `goofy-hopper-591e17`(main #11 bb6b50f 분기). 회귀 378. "상품 수집 CLI(collect-products)"가 다음 핵심.

**핵심 진척 [확정]** — 전체 콘텐츠 생성 파이프라인 end-to-end 구축·라이브 검증:

1. **collect-products CLI**: `--keywords`/`--scenario`, 기본 dry_run. AliExpress product.query → products upsert(멱등). 가격 밴드(min/max_sale_price)·검색어별 밴드(search_keywords.yml)·coupang_deferred 메커니즘.
2. **라이브 검증 확정**: ①검색어=영어·결과=한글 ②**가격 밴드(KRW)가 관련성 핵심 레버**(정렬 역효과) ③일반어→엉뚱 카테고리, 구체 검색어 필수 ④**AliExpress=소형 액세서리·수납 전용**, 가전·가구·전자본체·침구는 쿠팡.
3. **시나리오 튜닝**: homeoffice-chair-desk-50(8종 완벽)+wonroom·saehae·homeoffice-100·50-complete 적합분 + gajeon-100·gajeon-up-50 쿠팡 이관. (gaeul·isacheol·homeoffice-200 미착수)
4. **C-1 상품↔시나리오 연결**: `article_writer.record_scenario_candidates` — 후보를 시나리오 collected draft.raw_payload에 검색어 출처와 함께 기록(DB §5, 멱등).
5. **enrich 풀구축**: 후보 {{products}} 주입 + 응답 META/BODY 분리(split_article_response) + disclosure 자동삽입 + schema_jsonld + **featured 선언**(모델이 추천 ID 명시→truth 가격검증 정확 한정). max_tokens 4096→8192(잘림수정)+truncation 감지.
6. **disclosure 제휴처 인지형 [확정 공정위]**: 알리 글엔 "AliExpress 어필리에이트" 첫머리, 푸터는 쿠팡+알리. validator 첫머리=수수료+제휴처명1개. 표준 문구 강제(모델 임의 disclosure 차단).
7. **첫 글 4게이트 전부 통과**: validate(truth·schema·disclosure·links PASS), 실제 알리 상품 8개+실가격. draft 6 validated.

**무인·안전 장치**: truncation 감지·중단 / 파싱 실패 무저장 / 표준 disclosure 멱등 강제 / featured 미매칭 경고 / reject 시 상태 보존. **프로세스**: 점검에 ruff·black·mypy 선제 실행(lint churn 차단), `.gitignore` tmp_*.py.

**누적 commits 10건 [브랜치 claude/goofy-hopper-591e17 — main 미병합]**: 23e7466 인프라+5시나리오 / 7f6b99d C-1 / 4bc5a23 enrich 본문저장 / fd423bc max_tokens / 8e05f14 disclosure / 26603ae schema / 22d4b92 featured / a8f178c 프롬프트강화 / 10f87a3 표준강제 / c604c1d 제휴처 인지형 (+ 세션종료 docs).

**메모리 신설**: [[incremental-critical-review]] · [[autonomous-safe-system]].

**잔존 미해결 (다음 세션)**:
- **게시 경로 미배선**: approve(CLI 有)→**promote(CLI 미배선·함수만)**→상세글 렌더(#11 미구현)→배포. markdown→HTML·slug·article 필드 조립·schema 확정값 필요.
- 시나리오 3종 미튜닝 · 스타일 disclosure_banner(Phase 3~4 body 중복 조율) · schema_jsonld 임시값 promote 시 확정.
- **워크트리 브랜치 main 병합·push 필요**(ff 가능, main #11 미이동).

**다음 세션 할 일**: 1) 게시 경로 배선(promote CLI+상세글 렌더)→첫 글 게시 2) 시나리오 3종 튜닝 3) (자투리) 알리 whitelist·main-protect 재활성화

---

### 세션 #11 — 2026-05-29~30 (Opus 4.8 1M, 디자인 시안→Jinja2 5종 + builder.renderer + SEO/JSON-LD + enrich 버그수정 + 알리 수집기 골격, 회귀 352→378)

> ※ #10은 워크트리 6개·브랜치 6개 폐기 정리 커밋(2b260b2)만 — EVENTS 블록 미기재.

**시작 상황**: `/honsalim-start` → 워크트리 stupefied-lichterman (origin/main=#10 `2b260b2` 분기, 0/0 동기). 회귀 352. "공개 사이트 5종 시안"이 ★시급.

**핵심 진척 [확정]**:

1. **Claude Design 핸드오프 → 시안 5종 확정 (DECISIONS G4)**: "클로드 코드 인계" URL → WebFetch 4MB gzip → `docs/design_drafts/honsalim/`. 확정 조합 **톤 우드 / 카드 그림자 / 밀도 미니멀** (사용자 승인). 토큰 DESIGN §3 일치.
   - Jinja2 템플릿: `base·home·scenario_list·article·persona_hub·about·404` + `partials/{header,footer}` + `_macros/{components,meta}` / `static/css/{tokens,components,pages}` + `static/js/hub-filter.js`
   - 미리보기 `scripts/preview_build.py`(목업 19페이지) → 사용자 확인. `docs/design_drafts/CHOICE.md` 기록.
   - 정책 정정: About 이미지 "직접 촬영"→**"AI 생성+표기, 제품은 공식 위젯"**(L2). 운영자 "혼살다"·이메일·등록 진행 중(M2). 제휴링크 `rel="sponsored nofollow"`.

2. **정식 빌더 `src/builder/renderer.py`**: DB(personas·scenarios seed)→정적 사이트, `honsalim build --full`. 9페이지(home·hub·persona 3·about·404·sitemap). 게시 article 0편 → 상세글 미렌더(콘텐츠 단계).

3. **SEO 메타 + JSON-LD**: `_macros/meta.html`(OG·Twitter) + `jsonld.py` +3빌더(Breadcrumb·WebSite·Organization)+as_script_tags. base.html 연동.

4. **enrich 버그 수정**: `cmd_enrich`가 scenarios에 없는 컬럼 `s.keywords` 조회 → OperationalError. 제거 + 실행 회귀 테스트 추가.

5. **알리 수집기 골격 (DECISIONS D9)**: `collector.aliexpress` dry-run(서명 sha256 HMAC — 문서 4.5 예시 일치 검증, HTTP 0). 쿠팡 게이팅(사이트 완성 후 승인)으로 알리를 첫 상품 소스로 앞당김.

6. **회귀 352→378 PASS**: renderer 9 + jsonld 구조화 4 + cli-enrich 1 + aliexpress 12. `test_renderer`·`test_aliexpress_collector` 신설.

**알리 외부 작업 (사용자, 진행 중·미완)**:
- honsalim.com 사이트 등록이 **"ali" 부분문자열 오탐**(hons**ali**m)으로 거부 → whitelist 문의(대기).
- 기존 제휴 계정(dugi2020@naver.com) 사용(새 계정 실수 삭제). k-Content Hub(blogspot) 백업 등록.
- Open Platform Affiliate API 개발자 신청(Affiliates Individual·Korea) → **승인** → App Console에서 **Affiliates API 앱 생성** → App Key/Secret 발급·ali.env 저장 → **라이브 검증 성공** ✅ (밀리초 timestamp·응답 파싱·상품 매핑 전 필드 정상, deeplink=`s.click.aliexpress` 제휴링크). **수집기 production-ready**.
- **저장소 visibility 정정**: 네이버 작업 때 private로 바꿨던 것 발견 → **public 복구**(H1 일치) → CodeQL 그린. (공개 전환으로 push ruleset 꺼짐 → main-protect 재활성화 필요)

**잔존 미해결 (다음 세션)**:
- 상품 수집 CLI → products 적재 → 첫 글 enrich(API 비용)·검증·승인·발행
- 빌더 잔여: 상세글 렌더·Pretendard self-host·critical CSS·feed.xml·robots.txt
- honsalim.com 사이트 whitelist 승인 / main-protect 브랜치 보호 재활성화 / codeql-action 버전업

**다음 세션 할 일**:
1. 상품 수집 CLI(`collect-products`) → products 테이블 적재
2. 상품↔시나리오 연결 → 첫 글 enrich·검증·승인·발행
3. (자투리) main-protect 재활성화 · codeql-action 버전업 · 빌더 잔여
