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

## 최근 5세션

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

---

### 세션 #20 — 2026-06-02 (Opus 4.8 1M, ★카테고리 4개 라이브 배포 + 홈 카테고리우선 大리디자인 + 버그 4종 근본수정, 회귀 623→632)

**시작 상황**: `/honsalim-start`(워크트리 zealous-swartz, HEAD #19). 회귀 623. "우선순위부터" → 카테고리 4개 검토·승인·배포 착수. 도중 이미지 누락·배포 실패·홈 임시방편 발견 → 홈 리디자인까지 확대(사용자 반복 피드백).

**핵심 진척 [확정]** (전부 honsalim.com 배포 완료):
1. **카테고리 4개 라이브 배포**: '전화' 제외(폰·태블릿 겸용 1위 차단·운영자 결정) → DB재생성·수집·생성·승인(published) → honsalim.com 배포 성공(옛 #13 글 제거). 판매량 기준 6선.
2. **이미지 누락 오인 근본수정**: 원인=`loading="lazy"`+전체페이지 스크린샷(데이터·URL 148/148 200 정상). 미리보기=eager(검토 전부표시)/공개=lazy(CWV) + onerror 재시도1회→숨김.
3. **★산출물 청소 버그**: render_site가 out_dir 미청소 → 미게시/삭제 콘텐츠 잔존(옛 글 안 내려감). out_dir 내용물 청소 후 재생성(site/preview만, 서버 점유해도 안전).
4. **★배포 wrangler 실패(code 8000111)**: git 한글·특수문자 커밋메시지를 CF가 거부. build.yml `--commit-message=honsalim-auto-deploy`(ASCII)+`--commit-dirty=true` 명시 → 전 배포 안전. (테스트·아티팩트는 통과, 업로드 단계만 실패였음)
5. **HTML 엣지캐시 7일→5분**: _headers /* `max-age=0,s-maxage=300,must-revalidate`(정적자산은 1년 유지). 콘텐츠 반영지연 근본수정.
6. **★홈 카테고리우선 大리디자인**(임시방편 구조→완성): 레퍼런스(노서치·오늘의집·무신사) 조사 후 — 히어로(대표 개념이미지 home-hero.webp)·**기획전 캐러셀(A, 큰 키비주얼 배경이미지+오버레이·2슬라이드+점·home.js 자동회전)**·카테고리 그리드·**판매량BEST(C)**·**오늘의딜(D, 할인율순)**·**테마(E, 재택 홈오피스 세팅·카테고리 1순위)**·신뢰3박스·About(about.webp). 섹션간격 84→20px(사용자 3회 요청). ★C/D/E상품은 빌드마다 DB 자동 재계산(고정 아님)·테마주제/배너는 운영자 기획.
7. **구매가이드 /guides/ 페이지**: 깨진 네비링크(/guides/ 404) 해소 — 카테고리 '고르는 법' 모음. 내부링크 167종 **0 broken** 감사 확인.
8. **사업자 표기 정직화**: "등록 진행 중" 과장 제거(미등록 필드 조건부 숨김 — footer·about·article) + 이메일 dugi2020@naver.com. 사업자등록은 D4(월10만원 누적 후).
9. **회귀 623→632**(+9 가드). black·ruff·mypy 클린. 비용 ~$1(수집)+개념이미지 3장(~$0.06).

**무인·안전/정직성(§0)**: 이미지 데이터 정상 입증(가짜 없음)·산출물 청소로 삭제 반영 보장·배포 자가복원(commit-message)·BEST/딜/테마 실데이터 자동(가짜 지표 없음)·인구통계 "20대 BEST" 대신 상황 테마(데이터 없는 라벨 금지)·사업자 과장표기 제거.

**잔존 미해결 (#21)**: ①**미충전 이미지 전부 채우기**(/about/ 히어로 아트 등 placeholder 다수) ②**제품 등록 준비**(수익 카테고리 리스트화·순차 자동등록·알리+쿠팡) ③/go/ 제휴링크 작동(수익직결) ④office-chair ⑤무인 스케줄러. **사용자 원칙: 홈 완성도 우선 → "제법 홈페이지 같을 때" 제품 등록(대량등록 아님).**

**다음 세션 할 일**: 1) **미충전 이미지 전부 채우기**(페이지 완성도) 2) **수익 카테고리 리스트+순차 자동등록 설계** 3) /go/ 작동. ★홈 리디자인은 origin/main 배포 완료(다음 워크트리 이어짐)·DB는 gitignore→재생성 필요.

---

### 세션 #19 — 2026-06-01 (Opus 4.8 1M, ★DeepSeek v4-pro 전면 전환 + 카테고리 디자인 마무리 + 관련성 필터 근본수정 + ★판매량 기준 추천 6선 + 신규 2카테고리, 회귀 590→623)

**시작 상황**: `/honsalim-start`(워크트리 determined-bouman, HEAD #18). 회귀 590. 카테고리 페이지 추가 디자인 수정 요청으로 시작 → 도중 "AI를 DeepSeek로 바꿨다"(옆 AutoBlog #99가 메인에 미커밋 드롭인) 확인·전면 전환 → 추천 선정 기준(판매량) 개선까지 확대.

**핵심 진척 [확정]** (※전부 로컬·미배포. honsalim.com은 #13 첫 글 유지):

1. **카테고리 디자인 마무리**: 추천 카드 좌우 **행 정렬**(grid stretch·버튼 하단 고정 — 장단점 개수 달라도 아래단 일치) · 전체제품 **정렬(추천/가격/할인)·티어 필터 JS 작동**(`static/js/category.js`+data 속성, 기존엔 버튼만 있고 무동작) · 조건 버튼 **손가락 커서**(cursor:pointer). 브라우저 eval 측정으로 검증.
2. **★DeepSeek v4-pro 전면 전환**: 본문생성 Sonnet→`deepseek/deepseek-v4-pro`. `claude_client.build_llm_client` 모델 라우팅(claude→Anthropic SDK, 그 외→OpenRouter REST), 응답을 Anthropic 형태로 감싸 파싱·게이트 무수정. meta_extractor 통일·config ANTHROPIC 필수키 제거·doctor LLM 키 점검. 키=`D:\secrets\.env` OPENROUTER_API_KEY. 라이브 검증. 이미지는 Imagen 유지.
3. **DeepSeek 출력 변동 안정화**: 과밀(5.02%)·JSON 깨짐·"무조건" 단정표현 → 파서 후행콤마 관용+파싱실패 자가복원 + SEO 지시문 강화(통째반복 금지·밀도 3%·단정표현 금지). 결과 3%대 안정(노트북만 3.52% 수용).
4. **★관련성 필터 근본수정**: laptop-stand 상위 캠핑 테이블 오염 — 원인=`require_any`(OR, "노트북"만 있으면 통과). `require_all`('타입+대상' 동시) 도입→구조적 탈락 + 재수집 정합화(옛 오염 제거) + 과도 제외어 보정.
5. **★추천 6선 판매량 기준 선정**: "판매량·평점 기준" 요청 → 라이브 확인(`lastest_volume` 제공·`evaluate_rate` %만·별점 없음). migration 006 + 수집기 추출 + `select_featured`(판매량순·만족도 80% 하한·**항상 6개**·저평가 뒤로·부족분 0판매로) + 렌더러 판매량 정직표기. AI는 설명만. 89%대 보존·20%/66.7% 제외 검증.
6. **신규 2 + 기존 2 재빌드**: 노트북거치대·모니터암 신규 + 모니터받침대·책상 재빌드 → 4개 전부 판매량 기준 6선·draft. office-chair 제품 0(미생성).
7. **회귀 590→623** (+33). black·ruff·mypy 클린. CLAUDE.md §6 DeepSeek 갱신. 비용 ~$1.

**무인·안전(§0)**: 가짜 평점 금지(별점 없음→판매량만 정직표기)·저평가(<80%) 추천 제외·require_all 오염 차단·DeepSeek 출력 자가복원·AI 자동 published 차단. 전부 draft.

**다음 세션(#20) 할 일**: 1) 카테고리 4개 검토→`approve-category`+`build --full`→배포 2) 노트북 '전화' 제외어 결정 3) office-chair 생성 4) 메인 미커밋 DeepSeek 임시본 정리 5)(이월) /go/·알리 whitelist·main-protect. ★DB gitignore→재생성 시 collect(판매량 채움) 먼저.

---

### 세션 #18 — 2026-05-31 (Opus 4.8 1M, 운영자 승인 게이트 + doctor 보강 + ★카테고리 페이지 디자인 디버깅·정형화(글씨 흐림 진짜원인=backdrop-filter), 회귀 569→590)

**시작 상황**: `/honsalim-start`(워크트리 beautiful-bose-63b4f9, HEAD=#17 `8710a5e`). 회귀 569. "다음 할 일 순서대로 진행" → #18 1순위 승인 게이트부터. 도중 디자인 작은 수정 요청이 카테고리 페이지 디자인 대거 디버깅으로 확대.

**핵심 진척 [확정]** (※전부 **로컬·미배포**. honsalim.com은 #13 첫 글 유지):

1. **운영자 1클릭 승인 게이트** (O21): `build-category`가 글 저장 시 **`status='draft'` 고정**(AI 자동 published 차단·E7, 재빌드 시 재승인 강제) · **`approve-category`/`unapprove-category` CLI** · `writer/category_state.py`(approve/unapprove/pending_approval+전이검증+부분DB 견고성) · renderer **`published`만 렌더**(+`include_drafts` 미리보기) · 대시보드 "카테고리 승인 대기" 섹션.
2. **doctor 보강** (#18-3): §10 진입점 **64**(category_state·category_page_builder·concept_image·category_collect 등 6 추가, 64/64 OK).
3. **★카테고리 페이지 디자인 디버깅·정형화** (O22): 글씨 흐림 **진짜 원인 = `backdrop-filter`**(헤더 유리효과 → Windows Chrome 텍스트 GPU 합성·ClearType off) **제거**가 근본 해결. + 본문 #111·폭 1080px·최소 14px·마크다운 `**`→strong·FAQ 구분·추천카드 장단점 그룹·폰트 NanumSquare Neo. 정형화 확인(desk→monitor-stand 자동 동일·공통 CSS).
4. **#18 2순위 배포 진행**: 이 워크트리에 DB 재생성(desk·monitor `collect-category`+`build-category` --no-dry-run 라이브, 게이트 통과, **draft**). 디자인 확정. **승인+공개배포는 #19**.
5. **회귀 569→590** (+21: category_state 9·renderer published게이트/마크다운·design_tokens 가드 3·cli 3 등). black·ruff·mypy 클린. 비용 ~$0.6.

**무인·안전/진실성(§0)**: AI 자동 published 차단(E7) · 미승인 draft 완전 비공개 · 마크다운 XSS escape 후 변환 · 대시보드 부분DB 견고성 가드 · 디자인은 코드(공통)라 새 카테고리 자동 적용 + 재발방지 가드(색 대비·정렬·승인전이). 미리보기 캐시→강력새로고침/시크릿창.

**잔존 미해결 (#19)**: ①**카테고리 페이지 추가 디자인 수정**(사용자 "이 페이지 수정할 부분 더 있다" — 연속 작업) ②#18 2순위 배포 완료(승인+공개) ③나머지 카테고리(의자 build·모니터암 신규) ④(이월) /go/·알리 whitelist·main-protect.

**다음 세션 할 일**: 1) **카테고리 디자인 연속 수정**(DB 재생성→`build --preview`로 확인하며) 2) **승인(`approve-category`)+배포**(`build --full`→honsalim.com) 3) 나머지 카테고리. ★DB는 gitignore→재생성 필요(`collect-category`·`build-category` --no-dry-run, ~$0.6). 워크트리 실행=`PYTHONPATH=src python -m cli`.
