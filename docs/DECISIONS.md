# DECISIONS.md — 혼살림 영구 [확정]

> 시간 흘러도 안 변하는 결정만. 출처·세션 번호 필수.
> 새 사실이 옛 [확정] 뒤집을 시: ~~취소선~~ + 세션 번호 + 새 항목.
> 무제한 cap. 영구 보존.

## A. 프로젝트 정체 [확정]

- **A1. 사이트명**: 혼살림 (Honsalim) — 세션 #1
- **A2. 도메인**: ~~honsalim.com~~ → **honsallim.com**(겹ㄹ) [확정 #21] — 알리(AliExpress)가 'ali' 포함 url(honsa**li**m)을 영구 차단("url containing string ali cannot be added", 자동+사람) → 'll' 표준표기 honsa**ll**im.com으로 이전. Cloudflare Registrar.
  - 세션 #2 honsalim.com 등록(만료 2027-05-28). **세션 #21 honsallim.com Pages 커스텀도메인 연결·SSL Active·라이브**(만료 2027-06-01·Auto Renew). honsalim.com(구)은 **301 Page Rule**(`honsalim.com/*` → `https://honsallim.com/$1`, 경로보존)로 신 도메인 전환·유지. 코드 SITE_ORIGIN·sitemap·canonical 전부 honsallim. ※인프라 리소스명(`honsalim-clicks` D1·Pages 프로젝트 `honsalim`·`honsalim.db`)은 불변
- **A3. 분야**: 1인 가구·자취·홈오피스·일상살림 (비YMYL) — 세션 #1
- **A4. 타겟 언어**: 한국어 단일 (영어 확장은 6개월 후 검토) — 세션 #1
- **A5. 컨셉**: 시나리오 추천 + 특화 결합 (페르소나×예산×시나리오) — 세션 #1
- **A6. 디자인 톤**: 미니멀+따뜻함 (흰 배경+우드 액센트+부드러운 그림자) — 세션 #1

## B. 기술 스택 [확정]

- **B1. SSG**: Jinja2 직접 빌더 (자체 빌더, AutoBlog 패턴 확장) — G1 조사
- **B2. 빌드 환경**: GitHub Actions (Linux, Python 3.10) — G1 조사
- **B3. 호스팅**: Cloudflare Pages (Direct Upload via wrangler) — G1 조사
- **B4. 캐시 무효화**: 파일명 해시 + 자동 무효화 — G1 조사
- **B5. 증분 빌드**: manifest 기반 + 의존 그래프 명시 (TIMA 비대화 교훈 회피) — G1 조사
- **B6. CWV 목표**: LCP ≤ 2.0초 / INP ≤ 150ms / CLS ≤ 0.05 — G1 조사
- **B7. DB**: SQLite (`data/honsalim.db`) — 세션 #1
- **B8. 이미지 호스팅**: Cloudflare R2 (10GB 무료) + Pages 정적 자산 — G3 조사
- **B9. 한글 폰트**: Pretendard 권장 (G1 조사 + DESIGN 추후 확정)
- **B10. 한국 응답 속도**: Cloudflare 서울 PoP (ICN) 보유 — G1 조사 [확정]
- **B11. Cloudflare 계정**: `Dugi2020@naver.com` 기존 사용 (kfood-buddy·kdrama-api와 동일 계정) — 세션 #2
- **B12. D1 DB**: `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` — 세션 #2
- **B13. R2 버킷**: `honsalim-images` (APAC) — 세션 #2
- **B14. Pages 프로젝트**: `honsalim` (placeholder 배포·honsalim.com 연결) — 세션 #2

## C. 운영 모델 [확정]

- **C1. 인간 편집 게이트**: Claude 자동 검증 + 사용자 최종 1클릭 승인 — 세션 #1
- **C2. 5파일 시스템 적용**: CLAUDE + STATE + DECISIONS + TODO + EVENTS — 세션 #1
- **C3. EVENTS.md 자동 회전**: 6세션 시 옛 세션 → docs/archive/ — 세션 #1
- ~~**C4. 자동 게시 시간**: 사용자 명시 승인 후만 (AutoBlog 매일 09:30 패턴 미적용) — 세션 #1~~ — **폐기 세션 #2**
- ~~**C5. 콘텐츠 발행**: 매주 2~3편 — 세션 #1~~ — **폐기 세션 #2**
- **C6. 자동 게시 활성 (윈도우 스케줄러)**: 사용자 1클릭 승인 완료된 글 큐를 윈도우 스케줄러가 매일 정해진 시각에 published 전이 + 빌드 + 배포. **자동 "승인"은 절대 금지 (POLICY E7 [확정] 유지)** — 세션 #2
- **C7. 자동 게시 기본 시각**: 매일 11:00 KST (AutoBlog 09:00~10:30 시간대 충돌 회피, 사용자 조정 가능) — 세션 #2
- **C8. 콘텐츠 발행 페이스**: 큐 기반 + 사용자 작성 역량 내 최대. 큐 있으면 매일 1편 발행, 큐 비면 자동 정지 + dashboard 알림 — 세션 #2
- **C9. KPI 게시글 수 상향**: 12개월 100편 → **240편+** (매일 1편 가정 + 사용자 휴식·시즌 조정). 트래픽·수익 KPI는 그대로 유지 — 세션 #2
- **C10. 무인 새로고침 사이클 (refresh-cycle, A안) [확정 #23]**: `deployer/refresh_cycle.py` + CLI `refresh-cycle`(기본 dry_run). 단계=①published 새로고침(collect_category·가격/판매량·LLM 미사용) ②가드레일 monitor 자가복원(미달 시 auto_killswitch=자동 unapprove·fail-closed) ③build(render+/go/) ④build/site·functions/go **변경 시에만** commit+push origin main→CI 배포. 일일 비용 ~$0. 매 실행 후 `data/refresh_cycle_last.json` 기록+대시보드 갱신. 안전=실패격리·사전조건(main·DB) 미충족 안전정지·destructive git 금지. 회귀 12 — 세션 #23
- ~~**C11. 무인 작업 등록 = Claude 예약작업 [확정 #23]**: Claude 예약작업 `honsalim-refresh-cycle`(cron `0 11 * * *`)이 매일 자동 refresh-cycle~~ — **폐기 세션 #24** (주인 지시로 수동 전환 → C13)
- **C12. 모니터링 대시보드 = 무인 허브 [확정 #23]**: `dashboard/render.py`에 "무인 사이클(최근 실행)"·"공개 카테고리 건강(미달 ⚠+킬스위치 명령)"·경고 배너 추가. 로컬 정적 HTML(`data/dashboard/index.html`·비공개·배포 X). 바탕화면 아이콘 "혼살림 모니터링"이 직접 염. refresh-cycle이 매 실행 후 자동 갱신. 회귀 7 — 세션 #23
- **C13. refresh-cycle = 수동 운영 전환 [확정 #24, 주인 지시]**: C11(Claude 예약작업 자동 11:00) 폐기. 주인이 "스케줄러 삭제·직접 지시·컨트롤"로 결정 → 예약작업 `honsalim-refresh-cycle` **비활성화**(작업 폴더는 주인이 직접 삭제). refresh-cycle **코드·대시보드(C10·C12)는 유지** — 주인 지시 시 메인 체크아웃에서 **수동 실행** `PYTHONPATH=src python -m cli refresh-cycle --no-dry-run --verify-url "https://honsallim.com/"`. ★§0(완전 무인) vs 주인 통제 권한 충돌 시 **주인 통제 우선**(메모리 [[assist-not-overstep]]) — 자동배포는 주인이 원할 때 재활성화 가능 — 세션 #24
- **C14. 운영 대시보드 (PyQt5) [확정 #25, 주인 요청]**: AutoBlog식 데스크톱 운영 대시보드를 PyQt5(시스템 Python 기설치·환경 무변경)로 구축. 로직(`dashboard/queries.py`·`writer/keyword_queue.py`·`deployer/scheduler.py` 등)/GUI(`dashboard/app.py`) 분리 → CI(PyQt 미설치) 안전. **①키워드 큐 모델**: `keyword_queue`(migration 007)에서 **키워드→시나리오 자동 파생**으로 기존 drafts→articles 발행 기계 재사용(★articles 스키마 무손상=라이브 무위험). **②발행**: `publish-queue`(승인된 큐만 promote→build→deploy·**E7 준수**, 자동 '승인' 없음). 예약=schtasks(`deployer/scheduler.py`), **기본 OFF**(C13 수동전환 취지·주인이 켤 때만 등록). **③쿠팡 수동**: `collector/coupang_manual.py`(공식 파트너스 딥링크/위젯·텍스트, ★함정#3 CDN 이미지 다운로드 금지)→누적 15만원 후 API. **④설정 외부화**: `common/settings.py`(`data/config.json`·설정창 편집·깨지면 기본값). 선승인 3건(글 스트림+모니터링/1클릭 승인 유지/쿠팡 공식위젯). 회귀 693→773. CLI 22→28 — 세션 #25
- **C15. 추천 키워드 생성 + 대시보드 메뉴 순서 [확정 #26, 주인 요청]**: 운영자가 키워드를 수동 선정하지 않도록, **이미 정의된 선정 방식**(`collector.keyword_research`: 네이버 연관검색어→핵심어 포함/브랜드/거래성/검색량≥2000/대상부적합 필터→검색량순)을 **기존 SEO 씨앗**(`collector/seo_keywords.yml` 카테고리 primary)에 적용하는 추천 엔진 `writer/keyword_recommender.py`(PyQt 비의존·테스트 가능) 신설. ①대시보드 **🎯 추천 키워드**: 검색량순 목록 → **행 선택 추가 또는 ⭐1순위 자동 추가**(주인 "선택 없으면 자동 세팅" 요청). ②`custom_seed`로 임의 주제 확장(자취·주방 등). ③중복 제외(이미 큐·시나리오에 있는 주제). ④**자가복원**: 네이버 실패·키 없음 시 yml 캐시 보조키워드로 강등(멈춤 없음, volume=None). ⑤비용=네이버 읽기전용(무료)·LLM 비용은 글 생성 단계에서만. ⑥CLI `keyword-recommend`(--seed·--limit·--no-live·--add-top) + doctor 진입점. **메뉴 순서=작업 우선순위순**(키워드→발행 큐(글)→카테고리·모니터링→설정, 시작점이 맨 왼쪽). **off-target 근본수정**: 핵심어가 광범위한 씨앗(노트북 거치대=핵심어 '거치대')은 `seo_keywords.yml`의 `exclude_terms`로 혼입 차단(폰·태블릿·자전거·차량 등·재발방지 가드, 책상의 학생·유아 패턴과 동일). 회귀 773→782. CLI 28→29 — 세션 #26
- **C15-b. '글 생성' 자동 키워드 선정 [확정 #27]**: `✨ 글 생성`이 키워드 선택 없이 눌려도 `keyword_recommender.auto_pick_keyword`로 자동 선정(대기 큐 맨 위 우선→없으면 정의된 방식 추천·추가). 정렬은 대시보드 목록과 동일(미리선택 있는 것→score↓→priority↓→id, '화면 맨 위'=자동 선정). 발행 큐 승인/반려도 선택 없으면 맨 위 글 대상(`_selected_or_top`). E7·비용 확인은 유지 — 세션 #27
- **C16. 쿠팡 하이브리드 글 = naver_blog UX + 구글 무기 [확정 #28, 주인 채택]**: naver_blog(D:\naver_blog) 발행 방식 정밀 분석 후 역제안 채택. naver_blog는 ①키워드 점수화('틈 찾기'·검색량/문서수/경쟁도·`keyword_scorer`) ②키워드 클릭→쿠팡 배너 팝업→"이 배너로 글 생성" 원클릭 ③스케줄러 ON으로 **자동화 UX 우위**. **단 naver_blog=네이버(C-Rank)·honsalim=구글** — 구글 2025-12 어필리에이트 업데이트가 '데이터 없는 AI 어필리에이트 글' 강타(T2). → **naver_blog UX는 차용하되 honsalim 글은 알리 판매량 데이터(Information Gain)로 페널티 회피**하는 하이브리드. ①**쿠팡 이미지 = 공식 배너 hotlink**(`<a><img coupangcdn>`) 도입 — 다운로드 아님이라 함정#3 무관(쿠팡 공식 임베드). ~~#24 "쿠팡 이미지 안 씀(텍스트)"~~ 폐기→**B 전환**(자체사이트 `<img>` 정상 렌더·iframe 위젯과 별개). 광고차단 일부 미표시는 고지(소수·링크 작동). ②**글 = 알리(데이터)+쿠팡(수익·이미지) 결합**(`_gather_keyword_candidates`)·쿠팡(운영자 수동선택)은 **항상 featured**. ③**원팝업** `🛒 쿠팡 배너→글 생성`(키워드 자동 `get_or_create`·멀티배너 `products_from_banners`·하이브리드 생성 한 번). ④article 상품카드가 `image_url_external` 사용(알리·쿠팡 공용·우드톤 fallback). 회귀 782→806. 잔존: PartC 키워드 '틈 점수'(`keyword_scorer` 차용·네이버 신호=구글 근사치)·PartD 자동발행 ON·**라이브 테스트 미실행** — 세션 #28

## D. 어필리에이트·수익 [확정]

- **D1. 메인 어필리에이트**: 쿠팡 파트너스 — 세션 #1
  - **세션 #2 정정**: 사용자 회원 탈퇴 + 쿠팡 정책 [확정 — 쿠팡 공식]: 콘텐츠 있는 승인 URL만 광고 가능 → **Phase 4 출시 후 재가입** (콘텐츠 누적 의존)
- **D2. 보조 어필리에이트**: AliExpress Portals — 세션 #1
  - **세션 #2 임시 우선순위 변경**: 쿠팡 가입 보류로 D2 알리 먼저 진행. 가입 신청 완료 (2026-05-28 심사 대기). honsalim.com이 "ali" 문자열 충돌로 거부 → primary site 임시 우회 (kcontenthubblog 사용·승인 후 honsalim.com secondary 추가 예정)
- **D3. AdSense**: 6개월 후 트래픽·수익 보고 재결정 — 세션 #1
- **D4. 사업자 등록**: 월 10만원 누적 후 (간이과세자, 광고대행업 743002) — 세션 #1
- **D5. 이미지 전략**: 글당 추천 상품 5~10개 + 사용자 직접 사진 1~3장 + 쿠팡 공식 위젯 — 세션 #1
- **D6. 외부 단축 URL 금지** (쿠팡 회색지대) — G5 조사
- **D7. 자체 redirect 게이트웨이 OK**: `/go/<slug>` Cloudflare Workers 패턴 — G3 조사
- **D8. 쿠팡 + YouTube Shopping 통합**: 2024-06-04~ (장기 YouTube 채널 도입 시 활용) — G4 조사 [확정]
- **D9. 알리 우선 통합 (쿠팡 게이팅) [확정 2026-05-30]**: 쿠팡 파트너스는 **사이트 완성 후 승인 신청** 가능(승인된 사이트만 API 사용) — 출시 전엔 불가. 따라서 **AliExpress를 첫 상품 소스로 앞당김** (원래 Phase 5 예정 → Phase 3 착수).
  - **계정**: 기존 제휴 계정(dugi2020@naver.com, 사이트 "다비교" 보유) 사용. 이번에 만든 새 계정은 사용자 실수로 삭제 → 기존 계정으로 진행.
  - **차단 이슈**: honsalim.com 사이트 등록이 **"ali" 부분문자열 오탐**(hons**ali**m)으로 거부 → AliExpress **whitelist 수동 승인 필요** (사용자 문의 진행 중). 가짜 URL 우회 금지.
  - **자격 증명**: `ALI_TRACKING_ID`·`ALI_APP_KEY`·`ALI_APP_SECRET` 모두 ali.env 저장 완료 ✅ (2026-05-30). 개발자 프로필(Affiliates Individual·Korea) 승인 → Open Platform App Console에서 **Affiliates API 앱 생성** → 키 발급. `Standard API for Publishers(Default)` **Active**. App Status=**Test**(운영 전환 `Apply Online`은 사이트 배포 시).
  - **API 스펙** (Open Platform Affiliate API Guidance): `aliexpress.affiliate.product.query`(키워드·페이지 50/쿼리 5000) · `productdetail.get` · `category.get`. 서명 sha256 HMAC(정렬 key+value, app_secret), app_signature 비필수. 게이트웨이 `api-sg.aliexpress.com/sync`.
  - **구현·라이브 검증 완료 [확정 2026-05-30]**: `src/collector/aliexpress.py` (서명 문서 4.5 예시 일치·회귀 +12). **실호출 성공** — `timestamp=밀리초` 확정, 응답 경로(`...product_query_response→resp_result→result→products→product[]`) + 상품 매핑 전 필드 정상(name·price_krw(KRW)·deeplink_url=`s.click.aliexpress` 제휴링크·image·category·tracking=honsalim). **수집기 production-ready**. 코드 수정 불요.
  - **잔존**: honsalim.com 사이트 등록 whitelist 승인 대기(affiliates@service.alibaba.com 문의). 차기 = 상품 수집 CLI → products 적재 → 첫 글.

## E. 정책·법무 [확정]

- **E1. 공정위 disclosure 의무**: 모든 글 첫머리·푸터 (위반 시 과징금 + 쿠팡 수익 몰수) — G5 조사
- **E2. 개인정보처리방침 의무** (PIPA, 위반 시 최대 2,000만원) — G5 조사
- **E3. 사업자 정보 footer 의무** (정보통신망법, 위반 시 최대 500만원) — 사업자등록 후 — G5 조사
- **E4. 본인·가족 구매 금지** — G5 조사
- **E5. 자동 실행·납치 광고 금지** (쿠팡 30일 수익 몰수 + 계정 해지, ZDNet 2025-10-03) — G5 조사
- **E6. 상표 키워드 PPC 금지** (AliExpress 영구 정지) — G5 조사
- **E7. AI 100% 자동 게시 금지** [확정 원칙] — Google Helpful Content System (HCS)은 2022-08 도입·2024-03 코어 알고리즘 통합 [확정 — Google Search Central 공식]. "검색 트래픽만 목적의 자동 생성 콘텐츠" 강등 알고리즘. AI 생성 콘텐츠 자체는 차별 X (2023-02 Google 공식)이지만 인간 검토 없는 자동 게시는 E-E-A-T 미충족 위험. 본 프로젝트 회피책: 인간 1클릭 승인 + 직접 사진 + 1인칭 검증 (POLICY §13).
  - **세션 #2 정정**: 기존 인용 "2024-03 16채널 47억뷰 종료"는 **YouTube AI Slop 단속 사례** (한국 보도 2026-01)로 Google 검색 HCS와 별개. HCS 관련 어필리에이트 트래픽 급감 사례 다수 보도 [관찰 — 출처별 검증 필요]. 구체 사례 인용은 추후 검증 후 추가.
- **E8. 한국어 1인칭 허용** (영어 AutoBlog 1인칭 금지 정책 미적용 — 한국 어필리에이트 정석) — G4 조사

## F. SEO·인덱싱 [확정]

- **F1. GSC 인증**: DNS TXT (Cloudflare DNS Domain property) — G2 조사
- **F2. 네이버 서치어드바이저 등록 의무** (HTML 메타·파일) — G2 조사
- **F3. Daum 웹마스터도구 등록** — G2 조사
- **F4. IndexNow API 자동 통보** (Bing+네이버+Yandex+Yep 단일) — G2 조사
- **F5. Schema.org**: BreadcrumbList + ItemList + Article 중심. Review는 직접 사용 상품만 — G2 조사
- **F6. Google Indexing API 사용 금지** (어필리에이트 정책 위반, 계정 차단 위험) — G2 조사
- **F7. .pages.dev 단독 운영 금지** (커스텀 도메인 필수, SNS 공유 신뢰도) — G2 조사

## G. 디자인 도구 [확정]

- **G1. 하이브리드 워크플로**: Claude Design 시안 → DESIGN.md 명세 추출 → Claude Code로 Jinja2 템플릿 생성 — 세션 #1
- **G2. Claude Design**: claude.ai/design (Pro/Max 플랜 포함, 2026-04-17 출시, research preview) — 세션 #1
- **G3. Claude Design 적용 범위 [확정 세션 #9]**: **공개 사이트 5종(홈·시나리오 허브·글·페르소나·About)만**. dashboard(관리자 페이지, BACKEND §2-6)는 Claude Design 미사용 — 단순 stub HTML로 충분 (사용자 1인 운영, 외부 노출 없음). STATE/TODO "dashboard 시안" 표기는 stale — "공개 사이트 5종 시안"이 정확.
- **G4. 디자인 시안 확정 [확정 2026-05-30 디자인 핸드오프 구현]**: Claude Design "클로드 코드 인계" 핸드오프(`api.anthropic.com/v1/design` → WebFetch로 4MB gzip 수신 → `docs/design_drafts/honsalim/`)로 5종 시안 수령.
  - **확정 조합 = 톤 우드 / 카드 그림자 / 밀도 미니멀** (사용자 승인). 디자인 토큰(`#FAF6F1`·`#A87F4D`·`#7A5530` 등)은 DESIGN.md §3과 일치 확인.
  - **산출물**: Jinja2 템플릿 5종(`base`·`home`·`scenario_list`·`article`·`persona_hub`·`about`) + `partials/{header,footer}` + `_macros/components.html` + `static/css/{tokens,components,pages}.css`(변형 토글 제거·확정값 baked-in) + `static/js/hub-filter.js`(허브 필터 점진적 향상). 미리보기 `scripts/preview_build.py`(목업 데이터 19페이지) → 사용자 확인 완료.
  - **정책 정정**: 디자인 About의 "직접 촬영" 이미지 문구 → **"AI 생성+AI 표기, 제품은 공식 위젯"**으로 수정 (L2 [확정] 정합). 운영자 "혼살다"·이메일 확정·사업자번호 "등록 진행 중"(M2) 반영. 제휴 링크 `rel="sponsored nofollow"`.
  - **미반영(차기)**: 정식 빌더(`builder.renderer`)·DB 연동·meta/JSON-LD 매크로·Pretendard self-host·critical CSS·Person Schema(M2-1~M2-7)는 Phase 3 후속.

## H. Git 운영 [확정]

- **H1. GitHub 공개 저장소** (Actions 무제한 [확정 GitHub]) — 세션 #1
- **H2. secrets 분리**: `D:\secrets\affiliate_hub\` (코드 저장소 절대 금지) — 세션 #1
- **H3. 자동 commit**: `/honsalim-end` 자동 1회 — 세션 #1
- **H4. 자동 push 금지**: 사용자 명시 승인 후만 — 세션 #1
- **H5. 커밋 메시지 포맷**: `[YYYY-MM-DD #N] <한 줄>` — 세션 #1

## I. 보안 강화 [확정] — 세션 #2 신규

- **I1. GitHub 보안 파일 차단 다중 방어**: (1) `.gitignore` 엄격 (2) **pre-commit hook = detect-secrets** (gitleaks는 V3 백신 차단으로 폐기, 세션 #2 확정) (3) **GitHub Secret Scanning + Push Protection 활성** (4) Repository Settings 보호 — 세션 #2
  - **세션 #2 보강**: GitHub Advanced Security 활성 — Private vulnerability reporting·Dependency graph·Dependabot alerts/security updates/grouped/malware/version updates(dependabot.yml 작성)·CodeQL(lint.yml)·Copilot Autofix·Push protection 모두 ON
- **I2. 보안 헤더 의무**: CSP + HSTS + X-Content-Type-Options + X-Frame-Options + Referrer-Policy + Permissions-Policy 모두 적용 (Cloudflare Pages `_headers`) — 세션 #2
- **I3. 외부 계정 2FA 의무**: GitHub·Cloudflare·쿠팡·Anthropic·도메인 Registrar 모두 2FA (TOTP 또는 보안 키) 활성 — 세션 #2
- **I4. 의존성 보안 자동화**: GitHub Dependabot Alerts + pip-audit 월 1회 + npm audit (wrangler) 분기 1회 — 세션 #2
- **I5. 로컬 디스크 암호화**: D 드라이브 BitLocker 또는 동등 암호화 활성 (사용자 시스템) — 세션 #2
- **I6. CodeQL 활성**: GitHub 공개 저장소 CodeQL 자동 스캔 — 세션 #2
- **I7. secrets 회전 정기 의무화**: GitHub PAT 90일 / Cloudflare API token 180일 / Anthropic key 180일 / 쿠팡 키 정책 확인 후 — 세션 #2

## J. Phase 2 아키텍처 [확정] — 세션 #4 신규

- **J1. 모듈 의존 방향**: `writer → validator` 단방향. `writer.article_writer`가 `validator` 모듈을 import해서 `validate_and_save` 통합 함수 제공. 역방향 금지 (validator → writer는 순환 위험). 코드 명시 — 세션 #4 (`6d5cff1`)
- **J2. state_machine 매트릭스 보강**: `approved → validated` 전이 추가. BACKEND §9 `unapprove` 명령 정합. DB §12-2 원본 매트릭스를 갱신함. 다른 전이는 변경 없음 — 세션 #4 (`07c6fc8`)
- **J3. CLI 명령 8/11 활성**: doctor · db migrate/seed · collect · enrich · validate · approve · unapprove. 남은 3 (dashboard·build·deploy)은 builder/dashboard/deployer 모듈 의존 — 세션 #4
- **J4. `enrich` 기본 dry_run**: Claude API 비용 보호 — 기본은 `dry_run=True` (prompt 빌드 + 상태 전이만, API 호출 없음). `--no-dry-run` 명시 시에만 실호출. 사용자 부주의 비용 발생 방어 — 세션 #4
- **J5. JSON-LD 빌더 4 인터페이스**: `build_article_jsonld(meta, scenario, ...)` · `build_itemlist_jsonld(items, list_name)` · `build_product_jsonld(product, image_url, description, brand_name, currency='KRW')` · `_normalize_keywords` 헬퍼. POLICY §4 + VALIDATOR §8 [확정] 필드 모두 충족·validator.check_schema 정합 검증 통과 — 세션 #4 (`d492483`, `225122d`)
- **J6. content_hash 형식**: `"sha256:" + 64자hex` (UTF-8 인코딩). DB §4-1 + manifest §10 일관. `compute_content_hash(body_md)` 헬퍼 — 결정적 (같은 입력 → 같은 hash) — 세션 #4 (`aef26c5`)
- **J7. disclosure_first 추출**: `extract_disclosure_first(body_md)` — 본문 첫 300자 첫 단락에서 "쿠팡 파트너스"+"수수료" 둘 다 포함된 텍스트 반환. POLICY §2-2 [확정] 추출 헬퍼. 검증 책임은 validator.disclosure 별도 (추출과 검증 분리) — 세션 #4 (`aef26c5`)
- **J8. payload 책임 분리**: `validate_and_save(conn, draft_id, payload)`는 payload 구조를 호출자 책임으로. enriched_payload 구조는 [관찰] — validator.validate_all 호환 키 (body_md, schema_jsonld, products, photos) 가정. 향후 enriched_payload 형식 결정 후 정식 [확정] — 세션 #4 (`6d5cff1`)

## K. 핵심 결정 4건 응답 [확정] — 세션 #5 신규

- **K1. manifest 형태 — `data/manifest.json` 단일 JSON 파일 확정**: DB §10 추정을 확정으로 승격. 근거 4가지 — Git diff 가능·사람이 읽기 쉬움·jq 호환·sqlite3 .dump 등 추가 도구 불요. builder.manifest 모듈 (`b8d7cc7` 세션 #4)이 이미 본 형태로 stub 작성됨. 향후 변경 없음 — 세션 #5
- **K2. 시나리오 우선순위 현재 명세 그대로 확정**: SCENARIOS §4-11 일정·페르소나 분배·슬러그 명명 모두 현 상태 유지. (a) 첫 발행 `#4 gaeul-cheot-jachi-30` 가을 신학기 (2026-06~07) — Phase 4 출시 직후 시즌 직격. (b) 페르소나 분배 A자취:4, B재택:3, C정착:3 — A 검색량 최대 [관찰]. (c) 한국어 로마자 슬러그 (`cheot-jachi`·`homeoffice`) — 한국 검색 친화·사용자 기억 용이. (d) 10편 시드로 충분, 확장은 SCENARIOS §2-1 후속 큐 — 세션 #5
- **K3. 외부 단축 URL 차단 11→13개 확정**: `n.kakao.com` (POLICY §6-1 누락분) + `naver.me` (국내 사용 빈번 [관찰]) 신규 추가. 코드 `src/validator/links.py` SHORT_URL_DOMAINS + POLICY §6-1 표 + 회귀 3건 동시 갱신. `t.co`·기타 제외 검토 안 함 — 안전 우선 — 세션 #5
- **K4. 모듈 분리 — 옵션 B (pyproject.toml flat 정합) 확정**: ARCH §4-2 모순(pyproject가 `honsalim.cli:main` 가정 vs 실제 `src/` flat) 해소. 코드 그대로 두고 `pyproject.toml` `[project.scripts]` + `packages.find.include` 수정. 옵션 A (src-layout 표준)는 변경 부담 큼에 비해 본 프로젝트 규모·운영자 환경에서 비용 대비 효익 약함. 향후 PyPA 표준 정합이 필요해지면 옵션 A로 마이그레이션 가능. **검증**: `pip install -e .[dev]` 후 `honsalim doctor` entry point 정상 작동 [확정 세션 #5] — 세션 #5
- **K5. prompt_loader Jinja2 `ChainableUndefined` 채택 [확정]**: `src/enricher/prompt_loader.py`의 jinja2 분기에서 `Environment(undefined=jinja2.ChainableUndefined)` 적용. 사유: 회귀 테스트의 부분 dict + 본문 템플릿의 dotted access 결합에서 기본 `Undefined`는 chain 시 `UndefinedError` 발생. jinja2 미설치 fallback인 `render_simple`은 silent로 빈 문자열 반환 → 두 분기 동작 일치. **결과**: 회귀 333/333 PASS [확정 pytest 9.0.3]. 외부 영향 없음 — 세션 #5

## L. 1인칭·사진 정책 재설계 [확정] — 세션 #6 신규

> 본 카테고리는 E8 (한국어 1인칭 허용)·D5 (직접 사진 1~3장 의무)의 현실 정합 문제 해소.
> 사용자가 수백~수천 제품 직접 보유·촬영 불가능 — 위키바이형 정보 분석 모델로 재설계.
> 벤치마크 3개 중 Wirecutter(직접 사용 100%)·오늘의집(UGC) 모델은 1인 운영 본 프로젝트에 적용 불가 — 형식·톤 영감만 차용.

- **L1. 글 톤 — 위키바이형 정보 분석 기본 [확정]**: 시나리오 본문 기본 톤은 3인칭 정보·분석·비교형 ("이 제품은 ~", "예산별 비교 ~", "페르소나 ~에게 적합 ~"). 한국어 SEO 구조 (h2·h3·표·요약) + 진실성 표기 + 등급 칩 (Wirecutter 형식 차용). 1인칭은 선택적 액센트 — 본인 실보유 5~10개 제품에 한정 — 세션 #6
- **L2. 사진 정책 — AI 생성 이미지 + 쿠팡 공식 위젯 [확정 세션 #6 2차 재변경]**: 사용자 직접 촬영 사진 **일체 없음**. 페르소나·시나리오 hero 이미지는 **Google Imagen 4 Fast로 AI 생성** (인테리어 분위기, 인물 X). 상품 이미지는 **쿠팡 공식 위젯**으로 일괄 처리 (Imagen 생성 X — 실제 제품 정확성·법규). 쿠팡 CDN 직접 다운로드 금지 유지. 시안 작성 시 페르소나 사진 6~9장 사전 촬영 요구 폐기 — `docs/IMAGE_GENERATION.md` 참조 — 세션 #6
- **L3. validator/truth 1인칭 완전 차단 [확정 세션 #6 2차 재변경]**: 본문에서 1인칭 표현 (POLICY §3-1-3 패턴) 감지 시 **무조건 fail**. AI 생성 이미지는 본인 실사용 증거 아님 — 1인칭 "내가 써봤다" 사용 시 거짓 광고·공정위 위반. owned_products 메타 우회 폐기 — 1인칭 완전 차단 강제 — 세션 #6
- **L4. 벤치마크 차용 범위 명문화 [확정]**: Wirecutter는 **추천 표·진실성 표기 형식만** (실제 직접 사용 모델 차용 X — 1인 운영 불가능). 오늘의집은 **시각 톤·시나리오 카드 레이아웃 영감만** (UGC 사진 풍부함 차용 X — 회원 시스템 필요). 위키바이가 **실질 베이스** (정보 집계·한국어 SEO·표). DESIGN §12 매핑 정합 갱신 의무 — 세션 #6
- **L5. E8 폐기·D5 폐기 [확정 세션 #6 2차 재변경]**: E8 (한국어 1인칭 허용) **전면 폐기** — 1인칭 완전 차단 (L3). D5 (직접 사진 1~3장 의무) **전면 폐기** — 사용자 직접 촬영 일체 없음 (L2). 사진은 AI 생성 + 쿠팡 위젯만 — 세션 #6
- **L6. Google Imagen 4 Fast 채택 [확정 세션 #6, 경로 갱신 #9]**: AI 이미지 생성 도구는 **Google `imagen-4.0-fast-generate-001`** (Gemini API REST). AutoBlog (`D:\autoblog\tistory_revival\ai_image_gen.py`) 패턴 이식. 환경변수 `GOOGLE_API_KEY` (**`D:\secrets\honsalim.env`** 세션 #9 사용자 보안 결정 — secrets/ 바로 아래 단일 파일로 격리. 기존 `D:\secrets\affiliate_hub\*.env`와 분리). 가격 $0.02/장. 무료티어 불가 — 결제 활성화 필수. 본 프로젝트 적용 명세 `docs/IMAGE_GENERATION.md` [확정] — 세션 #6·#9
- **L7. AI 이미지 명시 표기 [확정 세션 #6]**: 글 footer에 "이미지는 AI 생성 일러스트레이션" 한 줄 명시 의무. 한국 표시광고법상 명시 의무는 없으나 [확인 불가, 2026-05], 신뢰도·Google Helpful Content 안전 + 1인칭 차단 정합. 인물 이미지는 자제 (인테리어 분위기만) — 세션 #6
- **L8. 상품 이미지 = 쿠팡 공식 위젯 [확정 세션 #6]**: 추천 상품 이미지는 **쿠팡 공식 위젯 embed**만 사용. Imagen으로 상품 이미지 생성 금지 (실제 제품 정확성·법규 — 가짜 제품 이미지 = 소비자 기만). 쿠팡 CDN 직접 다운로드 금지 유지 — 세션 #6

## M. Google AI 검색 최적화 정합 [확정] — 세션 #6 신규

> 출처: Google Search Central 공식 가이드 "AI Optimization Guide" (2026-05-15 발표) — 사용자 명시 의무 적용.
> 원본: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide?hl=ko
> 본 프로젝트 정합 매트릭스: `docs/GOOGLE_AI_OPTIMIZATION.md`
> 핵심: Google 공식 "AEO/GEO = SEO". 기존 SEO 정책 그대로 유효 + 6건 강화.

- **M1. non-commodity content 의무 [확정]**: Claude API enricher prompt에 "일반 지식 reword 회피, 시나리오 페르소나×예산×시즌 결합 고유 인사이트 의무" 명시. Google 예시: ❌ "7 Tips for First-Time Homebuyers" / ✅ "Why We Waived the Inspection & Saved Money". `src/enricher/prompt_templates/article_main.md` 갱신 의무 (Phase 2 진척) — 세션 #6
- **M2. E-E-A-T author 강화 [확정]**: `Person` Schema (운영자) + author 메타 + about 페이지 운영자 정보 명시 (Phase 4 진입 시). publisher Schema(이미 [확정 POLICY §4-1])와 정합 — 세션 #6
  - **M2-1. 운영자 정체성 = 필명 + 운영 철학 [확정 세션 #7]**: 실명 비공개. E-E-A-T author 일부 충족 + 사생활 보호. 사용자 1인 운영 사적 결정 정합.
  - **M2-2. 필명 = "혼살다" [확정 세션 #7]**: 혼자+살다 합성. 사이트명 "혼살림"과 일관 + 함축도·친근감. Person Schema name + about 페이지 byline + 글 푸터 표시.
  - **M2-3. 운영 철학 핵심 메시지 [확정 세션 #7]**: "혼자 살아도 충분히 따뜻한 일상을, 가성비 좋게." 혼살림 컨셉(미니멀+따뜻함) + 1인 가구 타깃 독자 공감. Person Schema description + about 페이지 헤드라인.
  - **M2-4. 전문성 영역 (knowsAbout) [확정 세션 #7]**: 1인 가구 살림 · 자취 · 홈오피스 · 일상 살림. SCENARIOS 페르소나 매트릭스 정합. Person Schema knowsAbout 배열.
  - **M2-5. 운영자 사진 미게재 [확정 세션 #7]**: 사용자 직접 사진 일체 없음 [확정 L2] + AI 생성 사진은 실제 사람 X → 거짓 광고. 사진 대신 사이트 브랜드 이미지·일러스트 사용. POLICY §6 review.author Person + L 카테고리 정합.
  - **M2-6. 이메일 = dugihappyending@gmail.com [확정 세션 #7]**: 사용자 등록 이메일 그대로. Person Schema email (선택) + about 페이지 연락처 + footer.
  - **M2-7. 사업자 등록 전 임시 운영자 표기 [확정 세션 #7]**: "개인 운영자, 사업자 등록 진행 중" 명시 (POLICY §8-4 정합). PLAN §9 D4 (월 10만원 누적) 후 사업자 등록 → publisher Organization 사업자등록번호 추가.
- **M3. 시나리오 매트릭스 "확장 콘텐츠 악용" 회피 [확정]**: SCENARIOS §2-1 60 슬롯 매트릭스 — 페르소나×예산×시즌 결합 진짜 다른 가치 의무. 단순 변형 (예: "30만 자취"·"35만 자취" 만 다른 글) 회피. Google 공식 "확장된 콘텐츠 악용 = 모든 검색 변형에 별도 콘텐츠 = 스팸 정책 위반" 정합. SCENARIOS §2-1 차별화 기준 명시 의무 — 세션 #6
- **M4. AI 이미지 시각 검수 [확정]**: AutoBlog `D:\autoblog\tistory_revival\image_qa.py` 패턴 이식 → `src/validator/image_qa.py` 신설 (Phase 3 시점). 가짜 보임·일관성 자동 점검. Google "고화질 멀티미디어" 권장 정합 — 세션 #6
- **M5. Google Business Profile 등록 [확정]**: Phase 4 사업자 등록 후 등록 (운영자 신뢰성·로컬 노출). Google 공식 권장 — 세션 #6
- **M6. UCP 프로토콜 (AI Agent) [확정 검토 보류]**: Universal Commerce Protocol (ucp.dev) Phase 6+ 검토. Google AI Agent (Search 내 챗) 대응 — 세션 #6
- **M7. llms.txt·콘텐츠 청킹·AI 재작성·특수 Schema 안 함 [확정]**: Google 공식 명시 부정 — 본 프로젝트 추가 작업 의무 없음. 본 결정 영구화로 다음 세션 재검토 회피 — 세션 #6

## N. 자동화 정책 [확정] — 세션 #9 신규

- **N1. `/honsalim-end` 자동 push [확정 세션 #9, 사용자 결정]**:
  마감 명령 호출 자체가 사용자 명시 승인. `git push origin main` 자동 실행 (commit + push 일괄).
  사유: 매 세션 종료마다 push 확인 부담 제거. branch protection `main-protect` + pre-commit hook 9종 + secrets D:\secrets 격리로 안전망 확보. 본 세션 #5·#6·#7·#8 모두 사용자가 push 승인했음 — 실질적 명시 승인 패턴 영구화.
  **자동 금지 유지**: force push(`--force`·`-f`·`--mirror`·`--delete`·refspec `:`) · rebase · reset --hard · branch -D · checkout -- · restore -- · clean · worktree remove --force · tag -d · update-ref -d (모두 `.claude/settings.json` deny rule + CLAUDE.md §2-라 보호).
  **그 외 시점 push**: 명시 승인 후만 (변동 없음).
  적용 파일: `CLAUDE.md` §2(라)·§11 / `.claude/commands/honsalim-end.md` §7+규칙 / `.claude/settings.json` deny+allow.

- **N2. 무인 배포 = 방법 A (build/site 커밋 → GitHub Actions 배포) [확정 세션 #13, 사용자 결정]**:
  배포 경로를 "로컬 wrangler(B)"가 아니라 "**빌드 산출물(build/site 공개 HTML)을 저장소에 커밋 → main push → GitHub Actions가 Cloudflare Pages에 업로드**"로 확정.
  사유: ①배포 실행 명령(`wrangler ... deploy`·`python -m honsalim deploy`)은 `.claude/settings.json` deny로 **Claude 차단**(§2-라/§2-마 안전장치) → 배포는 사람/CI만 실행 가능 ②§11 "build/ 커밋 금지"는 글 DB(data/)·비공개 데이터 보호가 목적이고, **build/site는 어차피 공개될 HTML이라 노출 위험 없음** → "공개 산출물은 배포용 커밋 허용"으로 §11 보강 ③CI는 글 DB를 못 보므로(로컬 전용) **재빌드 없이 커밋된 build/site를 업로드만**.
  적용: `.gitignore`(`build/*` + `!build/site/`) / `.github/workflows/build.yml` 재작성(test 게이트→build/site 검증→`pages deploy build/site --branch=main`) / renderer robots.txt·_headers·LF 출력 / pre-commit trailing·eof 훅 build/site 제외.
  **첫 적용 [확정 #13]**: e763e0f push → Actions deploy success → honsalim.com 첫 글 라이브. CF_API_TOKEN Pages 권한 확인됨.
  **인간 게이트 유지**(§2-마): 콘텐츠는 promote(published) 전 사용자 승인 후에만 render·commit·push.

## O. 페이지 재설계·콘텐츠 모델 [확정] — 세션 #14 신규

> 상세 표준 = `docs/CATEGORY_PAGE.md`. 프로토타입 = `scripts/category_page_prototype.py`.

- **O1. 용어 일상화 [확정 #14, 사용자]**: AI 자카(AI가 쓰는 티) 제거 → 신뢰. **시나리오 → "내맘대로 세팅"(합성어 자리는 "세팅") / 페르소나 → "라이프스타일"**. 화면 텍스트·글 본문·enrich 프롬프트·renderer 문자열 교체(코드·DB·URL `scenarios/`·`personas/`는 내부라 유지). 재발 방지 가드 테스트(`tests/test_renderer.py`: 렌더 결과에 두 단어 0건). **회귀 472 PASS**. ※ **"AI가 작성"이라는 표현/인식 절대 금지** — 저자=운영자 "혼살다". AI 표기는 *개념 이미지*에만.
- **O2. 사이트 모델 = 카테고리 우선 제품 비교·정보 사이트(노써치형) [확정 #14, 사용자]**: 1급=품목 카테고리(구매가이드+비교+상세), 세팅=보조(카테고리 잇는 큐레이션 경로). 우리 유형=**용도 큐레이션+가이드+기능/가격대 비교**. 단일 알리·테스트 없음 → 멀티벤더 최저가·랩테스트형 불가(정직). 노써치 정밀분석 결과 반영(교육=구매가이드 / 선택=추천·랭킹 분리, 소비자 질문 순서로 흐름).
- **O3. 디자인 = 노써치식 흰 바탕 + 폰트 NanumSquare Neo [확정 #14, 사용자]**: 우드톤/Claude풍 폐기. NanumSquare Neo(네이버 제작·무료, 웹폰트 로드 확인) — 네이버 채용페이지 폰트로 [추정](Chrome 미연결로 직접 inspect 미확정). 배너·개념이미지=디자인 AI 생성, 제품사진=알리 실사진 핫링크.
- **O4. 카테고리 페이지 표준 템플릿(12컴포넌트) [확정 #14]**: 고지(최상단)→타입선택기(+더보기)→제목·저자혼살다·날짜→도입+신뢰박스 2개→기본정보(전문 8요소)→2분류(💰실속/⭐고급) 비교카드→한눈비교표→더보기(전체제품)→FAQ→고지. 섹션헤더=왼쪽강조선+eyebrow(노써치 검정박스 카피 금지·독창화). 상세 `docs/CATEGORY_PAGE.md` §2.
- **O5. 콘텐츠 8요소(전문가급·정직 큐레이터) [확정 #14]**: 스펙해독·기준+왜·트레이드오프·용도매핑·흔한실수·정직한단점·객관기준인용·1인가구렌즈. 가드레일: 추측금지·등급·의료단정금지·과장금지·1인칭금지·일반지식reword금지·경쟁사 문장카피 금지(구조만 참고).
- **O6. 신뢰 신호 = 정가→판매가+할인율 [확정 #14, 라이브검증]**: 알리 API(product.query=productdetail.get **동일 필드**) 제공=가격/정가/할인율·이미지갤러리·영상·2단계카테고리·판매처. **미제공=평점·긍정평가율·구조화스펙·후기텍스트** → 가짜 평점 절대 금지. "이렇게 골랐어요"에 "후기" 주장 금지.
- **O7. 가격 드리프트 규칙 [확정 #14, 라이브검증]**: 알리 가격 변동 큼(게이밍 105,200→239,264 2배 실측, 저장값 stale). 필수: 빌드시 재조회+"기준 시각" 표기+진실성게이트 변동거름+**가격대 이탈 시 자동 재선정**. (틀린 가격=신뢰붕괴+공정위 가격정확성 위반)
- **O8. 알리 이미지 = 제휴 API image_url 핫링크 [확정 #14]**: 다운로드·재호스팅 금지(L8·함정#3 정신), 공식 제휴 소재 핫링크만. 명시 허용은 [추정→권장: affiliates@service.alibaba.com 채널 확인].
- **O9. 공정위 고지 위치 고정 [확정 #14, 출처 공정위]**: 「추천·보증 심사지침」 2024.12.1 개정 — **제목/글 첫 부분 표시 의무**. 우리는 최상단 유지(준수). 문구는 자사 원본(경쟁사 카피 금지).
- **O10. SEO 키워드 최적화 = 네이버 기준 [확정 #15-16, 사용자]**: **다음(Daum) 무시·네이버만**(네이버 검색량 압도적, "1등만 잡고"). 대표키워드(=#1) 정확형 밀도 **~1.7%**(네이버 실측, 다음 2.05% 폐기)+제목앞·도입부·소제목. 보조키워드(연관검색어)는 자연 분산. 구현 = `validator/seo.py` 게이트(opt-in, payload["seo"]) — **하드 fail은 대표키워드만**, 보조·소제목수는 warning(과민=불필요 재생성=비용). AutoBlog `seo_gate.py` 포팅.
- **O11. 키워드 소싱 = 네이버 검색광고 API [확정 #15-16, 라이브검증]**: seed(한글 대표어)→연관검색어 실 월검색량/경쟁도→**자동 필터**(핵심어 포함 필수·브랜드 제외·거래성 제외·대표 부분문자열 중복 제외·off-target 제외)→검색량순 보조키워드. 자격증명 = `D:\secrets\affiliate_hub\naver_searchad.env`(NAVER_SEARCHAD_API_KEY/SECRET_KEY/CUSTOMER_ID, tistory_revival에서 복사·재사용). 결과 영속화 = `src/collector/seo_keywords.yml`(운영자 검토). 모듈: `collector/{naver_searchad,keyword_research,seo_keywords}.py`. 라이브: 사무용 의자 665개·컴퓨터 책상 874개 연관어 선별 확인.
- **O12. 본문 생성 모델 = Sonnet + 비용 과다청구 방지 [확정 #15-16, 사용자]**: `DEFAULT_MODEL=claude-sonnet-4-6`(Haiku→Sonnet, 카테고리 본문 품질 우선·저볼륨). tistory도 글생성=Sonnet. ★**비용 사고 방지**(tistory 세션 #7·#10 교훈): ①재생성 상한 보수적(`seo_regenerate.DEFAULT_MAX_ATTEMPTS=2`, 무한루프 금지) ②게이트 과민완화(#1만 하드)로 오탐 재생성 차단 ③지출 전 사전점검 ④게이트 탈락 시 다운스트림 유료단계 생략. 라이브 검증: 책상 가이드 1회 통과·밀도 1.67%·$0.049.
- **O13. 전체 제품 = 점수 없는 카탈로그 [확정 #15-16, 사용자]**: 노써치 '랭킹(종합점수)' **흉내 금지**(우리는 평점·점수·상세스펙 데이터 없음·O6). **가격·할인·타입 필터/정렬 카탈로그** + 하단 정직 고지("점수 안 매김·품질순위 아님"). 정렬=추천순(실속→고급, 할인율순)·가격순·할인순. 카드그리드(데스크톱3/모바일2). 진입점 3곳(타입선택기끝·비교카드아래·하단). 표준 `CATEGORY_PAGE.md §5-bis`, 시안 `scripts/all_products_prototype.py`.
- **O14. 상품 데이터 품질 필터 [확정 #15-16, 라이브검증 근본대책]**: 라이브 수집 오염 실측 대책. `collector/product_filter.py`: ①관련성(카테고리 핵심어 포함 필수+액세서리/타카테고리/브랜드 제외 — 책상 185개 중 114개 오염 제거) ②**부풀린 할인 차단**(할인율>70%는 알리 정가 패딩 의심→할인 신호 미표시, 공정위 가격정확성·O7).
- **O15. 진행 순서 = 디자인 토대 → 카테고리 구조 → 제품 렌더 [확정 #15-16, 사용자]**: 디자인 전환이라 토대 먼저(안 그러면 페이지마다 디자인 재작업·불일치). "디자인 토대"=확정 시안(O3 흰 바탕+NanumSquare Neo)을 **렌더러 공용 base로 이식**(목업 아님). 구현=`static/css/tokens.css` 팔레트/폰트 교체(components/pages가 토큰 기반이라 1파일로 전 페이지 전환)+`base.html` 폰트+`header.html` 카테고리 네비. **1단계 완료·검증**(build/preview 렌더). 남음=홈 콘텐츠 카테고리화·카테고리/전체제품 렌더러 이식·DB 영속화(정가/할인 컬럼·수집저장).
- **O16. 카테고리 데이터 모델 [확정 #17]**: `categories`(slug=seo_keywords 키·name_ko·intro·group_slug·status·guide_md·content_json·faq_json·concept_image)·`category_products`(tier=budget/premium·is_featured·pros/cons/pick_reason/pick_type) DB 테이블(migration 002·003·004·005). 렌더러가 DB를 읽어 페이지 생성(scenarios/personas와 동일 패턴). `products`에 `original_price_krw`·`discount_pct` 컬럼 + products_store 저장 정합.
- **O17. 카테고리 콘텐츠 자동 생성 [확정 #17]**: `enricher/category_page_builder.build_and_save(slug)` — 글(가이드8요소·추천6선(+타입)·FAQ·**제품명 기반 한눈비교표**) JSON 생성 → disclosure 삽입 → **SEO + 진실성(truth·disclosure·links) 통합 게이트 통과까지 재생성**(상한2, 1인칭 등 미달도 자동 재생성=자가복원) → DB 저장 후 개념이미지. 추천6선=AI 큐레이션(가짜 점수·평점 금지·O6). 비교표 확인 불가 항목="—"(없는 스펙 금지). 산문 합본(##소제목)으로 SEO 밀도 측정.
- **O18. 카테고리 페이지 구성 = 사무용 의자 프로토타입 표준 [확정 #17, 사용자]**: 공정위고지 · 타입선택기 · 신뢰박스2(🤝약속/📋이렇게골랐어요, 정적) · **배너형 개념이미지** · 타입비교표 · 체크리스트(2열 카드) · 추천6선 2티어(tcard) · 한눈비교표 · FAQ · 전체 제품 카탈로그(§5-bis) · **연관 카테고리 크로스링크**(같은 group, 사진3형). `templates/category.html`·`categories_index.html`+`static/css/category.css`(.catpage/.catindex 스코프 — 전역 .chk 충돌 회피 교훈). `/categories/`(인덱스)·`/categories/<slug>/`(상세) 라우트.
- **O19. 개념 이미지 = Imagen 4 Fast + CSS 텍스트 오버레이 [확정 #17, 사용자]**: 글만 나열 시 이탈↑ → "고르는 법"에 개념 컨셉 이미지(이탈 방지). AutoBlog `ai_image_gen` 이식(`enricher/concept_image.py`, REST·requests·`imagen-4.0-fast-generate-001`·$0.02/장). ★**이미지엔 텍스트 없이 생성 + 문구·CTA는 HTML/CSS 오버레이** — AI는 한글 텍스트를 깨뜨리므로(쇼핑몰 배너도 디자이너 레이어). 장점: 글자 선명·**검색 노출(SEO)**·문구 수정 용이. webp 변환·리사이즈(Pillow, ~37KB). `GOOGLE_API_KEY`=`D:\secrets\affiliate_hub\GOOGLE.env`(config.load_secrets로 환경변수, 키값 비노출).
- **O20. 카테고리 CLI·정형화 입증 [확정 #17]**: `collect-category <slug>`(수집·정제·2티어 연결)·`build-category <slug>`(글+게이트+이미지). 검색어·키워드(yml) 정의 → **2명령으로 페이지 자동 완성**. **책상으로 정형화 라이브 입증**(collect 59→정제28 → build 글+이미지+게이트 자동, 모니터와 동일 구조). 카테고리 등록(category_sources.yml·seo_keywords.yml·seed)은 운영자 수동(§2-마 검토 대상). ★워크트리에선 `honsalim` 명령(editable=메인 체크아웃 가리킴) 대신 `PYTHONPATH=src python -m cli`로 실행.
- **O21. 카테고리 공개 승인 게이트 [확정 #18]** (§2-마·E7 구현): `build-category`가 글 저장 시 `status='draft'` 고정 — **AI 자동 published 절대 금지**. 재빌드(콘텐츠 변경) 시에도 draft로 되돌려 **재승인 강제**(미승인 변경 노출 방지). 공개는 **`approve-category <slug>`**(draft→published, 사용자 1클릭)만, 취소는 `unapprove-category`. `writer/category_state.py`(approve/unapprove/pending_approval+전이검증, categories 미마이그레이션 부분 DB 견고성 가드). 렌더러는 **`status='published'`만 렌더**(공개 `build --full`=build/site) / **미리보기는 `build --preview`**(`include_drafts=True`, draft 포함, build/preview — §2-마 검토용). 대시보드(`dashboard`)에 "카테고리 승인 대기" 섹션(draft+글생성됨) + `approve-category` 명령 복사 버튼. 회귀 가드 `tests/test_category_state.py`.
- **O22. 카테고리 페이지 디자인 디버깅·정형화 [확정 #18, 라이브검증]**: 글씨 "흐리고 뭉개짐"의 ★**진짜 원인 = `backdrop-filter`**(헤더·페르소나탭 유리효과) — Windows Chrome에서 페이지 전체 텍스트를 GPU 합성으로 끌어들여 ClearType(subpixel) 렌더가 꺼지고 흐릿한 grayscale로 바뀜. **제거**(불투명 배경 대체)가 근본 해결(색·굵기·폰트로는 해결 불가). 부수 사실: cdnfonts **NanumSquare Neo는 중간 두께 없음**(350/400/700/800/900 — weight 500 무시됨, 제목용 폰트지만 본문도 weight 400로 사용). 디자인 표준(전 카테고리 공통 CSS·템플릿·renderer라 **새 카테고리 자동 적용**): 본문색 **#111**(거의 검정) · 콘텐츠 폭 **1080px 단일칼럼**(네이버 1300은 2단 기준이라 단일칼럼엔 넓음) · **정보성 글씨 최소 14px**(tier-intro 기준; 배지·eyebrow·아바타·마커는 장식 예외) · 산문 마크다운 `**`→`<strong>` 렌더(raw 노출 방지, XSS escape 후) · 흔한실수 ①②③ 줄바꿈 · **FAQ Q/A 구분**(질문 회색배경+녹색 Q마커 / 답변 흰배경+회색 A마커) · 추천카드 장점/단점 그룹 라벨 · 가격+할인율 같은 줄. 가드 `tests/test_design_tokens.py`(색 대비·위계·`.wrap` 좌우패딩 shorthand 금지). ★미리보기 확인 시 **브라우저 캐시→강력새로고침(Ctrl+Shift+R)/시크릿창** 필수.

## P. DeepSeek 전환·판매량 선정·관련성 필터 [확정] — 세션 #19 신규

- **P1. 본문 생성 모델 = DeepSeek v4-pro (OpenRouter 경유) [확정 #19, 주인 결정·전 K-Content 통일]**: O12의 `claude-sonnet-4-6` → **`deepseek/deepseek-v4-pro`**. `enricher/claude_client.build_llm_client`가 모델명으로 라우팅 — **"claude"로 시작=Anthropic SDK, 그 외=OpenRouter REST(`requests`)**. OpenRouter 응답을 Anthropic Message 형태(`.content[0].text`·`.usage`·`.stop_reason`)로 감싸 기존 파싱·게이트·잘림감지 무수정 재사용. 키=`D:\secrets\.env` `OPENROUTER_API_KEY`(환경변수 우선·없으면 그 키만 읽음). config 필수키에서 ANTHROPIC 제거·doctor가 활성 모델 기준 LLM 키 점검. 이미지는 Google Imagen 유지(텍스트 LLM 무관). ※O12의 모델 지정만 대체, **비용 방지책(재시도 상한 2·게이트 과민완화)은 유지**.
- **P2. DeepSeek 출력 변동 안정화 [확정 #19, 실측]**: DeepSeek는 Sonnet보다 형식·SEO 준수가 불안정(과밀 5%·JSON 깨짐·"무조건" 단정표현). 근본대책: ①파서 후행콤마 관용 ②빌드 루프 **파싱 실패도 자가복원**(순수 JSON 재요청 재생성) ③SEO 지시문 강화(`seo_directive`: 대표키워드 통째반복 금지·줄임말 대체·밀도 최대 3%·'무조건/절대/최고' 단정표현 금지). 결과 밀도 3%대 통과(노트북만 3.52% 수용).
- **P3. 추천 6선 = 판매량 기준 결정적 선정 [확정 #19, 사용자]**: O17의 "AI 큐레이션"을 **객관 규칙으로 대체** — AI는 선정 권한 없이 **설명(장단점·추천대상)만** 작성. migration 006(`products.sales_volume`=알리 `lastest_volume`·`evaluate_rate`=긍정 피드백율%). `category_page_builder.select_featured`: 티어별 정렬키 **(만족도 명백한 저평가 아님, 판매량↓, 신뢰할인율↓)** → 상위 per_tier. **만족도 80% 미만(명백한 저품질)만 뒤로**(90%는 89%대 베스트셀러를 떨궈 80%로 실측 보정), 데이터 없음(None/0=피드백 없음)은 통과. **항상 6개 채움**(주인 요구 — 부족분은 미검증 0판매 제품으로, 단 저평가는 최후순위). ★**평점(별점) 사용 불가**: 알리 API 미제공([확정 #14·O6])·조작 우려 → 가짜 평점 금지. 화면은 **판매량만 정직표기**("알리 최근 판매량 N·판매처 기준"), 만족도는 변별력 약해(대부분 90%+) 선정 필터로만 비표시.
- **P4. 상품 관련성 = require_all('타입+대상' 동시) [확정 #19, 실측 근본수정]**: `product_filter.is_relevant`에 `require_all`(OR-그룹들의 AND) 추가. `require_any`(OR 한 줄)는 "노트북"만 언급한 캠핑 테이블도 통과시켜 카탈로그 오염 → laptop-stand는 `[[노트북 계열],[거치대 계열]]` 둘 다 가진 상품만 통과(구조적 차단). + `category_collect` **재수집 정합화**(is_featured=0 카탈로그를 비우고 재구성 → 필터 강화 후 재수집하면 옛 오염 자동 제거, 추천 6선은 보존). 과도 제외어(데스크탑/태블릿이 정상 노트북 스탠드 탈락)는 require_all이 거르므로 최소화.
- **P5. 카테고리 페이지 인터랙션 [확정 #19]**: 추천 카드 좌우 **행 정렬**(grid-area 행 배치·stretch·버튼 `margin-top:auto`로 장단점 개수 달라도 아래단 일치, 모바일은 그룹 스택). 전체 제품 **정렬(추천/가격/할인)·티어 필터 = `static/js/category.js`**(서버 렌더 카드 data 속성 기반 클라이언트 재정렬·표시; JS 없으면 서버 기본=추천순·전체, 점진 향상). 조건 버튼 `cursor:pointer`. ★전부 공통 코드(template/css/js·select_featured·build_llm_client)라 **신규 카테고리 자동 적용**.

## Q. 카테고리 배포·홈 리디자인·배포 안정화 [확정] — 세션 #20 신규

- **Q1. 배포 wrangler 커밋메시지 = ASCII 고정 [확정 #20, 라이브 근본수정]**: `cloudflare/wrangler-action@v4`의 `pages deploy`가 **git 커밋 메시지를 CF 배포 메타데이터로 전송**하는데, 본 프로젝트 커밋 규칙(`[YYYY-MM-DD #N]` 한국어+`★`·`→` 등)을 Cloudflare API가 거부(**code 8000111 "Invalid commit message, must be valid UTF-8"**) → 파일 업로드 성공·배포 생성만 실패. `build.yml` 명령에 `--commit-message=honsalim-auto-deploy`(ASCII)+`--commit-dirty=true` 명시로 git 메시지 스크래핑 우회 → 전 배포 안전. 가드 `tests/test_deploy_workflow.py`. (wrangler-action이 매번 최신 wrangler 설치 → 4.96.0부터 메타 전송이 드러난 것으로 [추정])
- **Q2. 정적 산출물 청소 = build 시 out_dir 내용물 제거 후 재생성 [확정 #20]**: `render_site`가 out_dir을 안 비워 **미게시·삭제된 콘텐츠의 옛 HTML이 build/site에 잔존**(배포 시 라이브에서 안 내려감 — 무인 'unpublish→라이브 반영' 깨짐). site/preview 디렉토리 **내용물만** 제거 후 재생성(디렉토리 자체는 유지 → 실행 중 미리보기 서버가 cwd로 점유해도 Windows WinError 32 회피). 가드 `tests/test_renderer.py::TestBuildSiteClean`.
- **Q3. HTML 엣지캐시 단축 [확정 #20]**: `_headers` `/*`에 `Cache-Control: public, max-age=0, s-maxage=300, must-revalidate`(HTML 5분·브라우저 재검증), `/static/*`는 1년 immutable 유지. 콘텐츠 수정/삭제가 최대 7일 지연되던 문제 근본수정(무인 일일 발행 전제). ※CF 측 Cache Rule이 장기 캐시를 강제하면 우선하므로 대시보드 병행 점검. 옛 캐시본은 Purge Everything/Custom Purge로 비움.
- **Q4. 이미지 로딩 = 미리보기 eager / 공개 lazy + onerror 재시도 [확정 #20]**: '이미지 누락' 신고의 원인은 **데이터가 아니라 `loading="lazy"`+전체페이지 스크린샷**(화면 밖 이미지 미로드; 데이터·URL 148/148 200 정상). 미리보기(`include_drafts`)=eager(검토 시 전부 표시)·공개=lazy(외부 이미지 다발 요청 방지·CWV). 깨진 외부 이미지는 `onerror`로 1회 재시도(캐시버스터)→재실패 시 숨김(자가복원). 가드 `TestCategoryProductImages`.
- **Q5. 홈 = 카테고리 우선 + 콘텐츠 모듈 [확정 #20, 사용자·레퍼런스 노서치/오늘의집/무신사]**: 옛 페르소나/시나리오 중심 홈(임시방편)→**카테고리 우선**. 모듈: 히어로(대표 개념이미지)·**기획전 캐러셀(A, 운영자 기획·가짜 세일 금지)**·카테고리 그리드·**판매량 BEST(C)**·**오늘의 딜(D, 할인율순)**·**테마 큐레이션(E, 상황 기반)**·신뢰3박스·About. ★**C/D/E의 상품은 빌드마다 DB에서 자동 재계산**(고정 아님 — 제품 늘면 자동 반영), **테마 주제·기획전 배너는 운영자 기획**(품질·정직성). 인구통계 "20대 BEST"는 데이터 없어 금지 → 상황 테마로. 가드 `TestHomeRichSections`.
- **Q6. 구매가이드 페이지 /guides/ [확정 #20]**: 상단 네비 구매가이드가 가리키던 `/guides/`가 페이지 없어 404(유일 깨진 링크) → 카테고리별 '고르는 법' 가이드를 모은 `/guides/` 인덱스 생성. 내부링크 167종 0 broken 확인. 무인 자동화 전 **사이트 골격(모든 링크·페이지)이 에러 없이 완성** 후 제품 등록 — 사용자 원칙(§0).
- **Q7. 사업자 정보 미등록 시 숨김 [확정 #20, M2 갱신]**: 사업자등록 전(DECISIONS D4: 월10만원 누적 후)에는 footer·about·article에서 **빈 사업자번호·통신판매업·주소 필드를 조건부 숨김**("등록 진행 중" 과장 표기 제거 — 정직성 §0). 등록 후 실제 값 채우면 자동 재노출. 사이트 표기 이메일 = **dugi2020@naver.com**(BUSINESS_INFO·Organization JSON-LD 포함 전체).

## R. 자율 게시 가드레일·수익경로·성장 전환 [확정] — 세션 #22 신규

- **R1. E7 개정: 사람 게시승인 → fail-closed 가드레일 + 사후 킬스위치 [확정 #22, 주인 결정]**: E7("자동 승인 절대 금지")의 **문구**를 "자동 가드레일 + 사후 거부권"으로 교체(취지=Google Helpful/Scaled Content 패널티 회피는 유지). `writer/category_guardrail.check` 5중 fail-closed 검사 — ①글 존재 ②안전게이트(truth·disclosure·links) 재검증 ③추천6선 무결성(2개+·deeplink 고유·트래킹 일관·가격) ④관련성 휴리스틱(category_sources require/exclude 재적용, 추천=엄격·전체 오염율≤5%) ⑤추천6선 LLM 의미검수. **조금이라도 애매하면 보류(미탐<오탐)**, 통과만 `auto_publish`가 published 전이. 안전 핵심='무승인'이 아니라 **느린 발행(C8)+자동 가드레일+사후 킬스위치(`unapprove-category`)+`monitor` 재검수**. CLI: `auto-publish`·`register-categories --auto-publish`·`category-status --monitor`. 테스트 18.
- **R2. LLM 의미검수 단일오탐 관용 [확정 #22, 라이브 보정]**: LLM(temperature 비결정·다기능 제품명 노이즈)을 hard 게이트로 쓰면 정당한 제품(반도체 미니제습기·브레드보드 도마)에 깨끗한 카테고리까지 막힘. → 키워드(명확) 게이트는 엄격 유지, **LLM(모호)은 추천6선 중 `_LLM_HOLD_THRESHOLD`(=2)건 이상 NO일 때만 보류**(체계적 오염=office-chair 6/6은 그대로 잡힘). 단일 NO는 기록만(monitor 가시화). LLM 호출/파싱 실패는 별도 fail-closed 보류.
- **R3. 재수집 시 비관련 옛 추천도 prune [확정 #22, 근본수정]**: `category_collect`가 카탈로그(is_featured=0)만 비우고 추천(is_featured=1)은 보존하던 것(P4)을 보강 — **필터 강화로 이제 비관련이 된 옛 추천(relevant_ids에 없는 is_featured=1)도 삭제**. 안 그러면 옛 오염(캠핑의자)이 추천에 남아 select_featured(판매량순)가 다시 뽑아 오염 영속(office-chair 라이브 적발). 여전히 관련인 추천은 보존.
- **R4. /go/ 어필리에이트 리다이렉트 = Cloudflare Pages Function [확정 #22]**: 별도 Worker(`wrangler deploy` — `.claude/settings.json` deny + 권한 자기수정 금지로 하네스 차단)·D1 대신 **`functions/go/[[path]].js` Pages Function**으로 `/go/<slug>`→알리 deeplink 302(미등록→홈). 정규 Pages 배포(git push → CI의 `wrangler pages deploy`가 `functions/` 자동 컴파일)로 함께 배포 — 권한·인프라 단순화. 알리 deeplink ~1065자라 `_redirects`(1000자 제한) 불가 → 함수에 맵 임베드(`builder.go_function`, build --full에서 published 상품 247개로 재생성). `/go/`만 가로채 정적 사이트·_headers 무영향(라이브 검증). **트레이드오프: D1 클릭 로깅 보류**(go_gateway.js Worker 코드 보존 — 추후 Pages Function D1 바인딩으로 복원).
- **R5. 알리 개별 deeplink = honsallim 트래킹ID [확정 #22]**: 알리 Portals honsallim 채널 Tracking ID를 `ALI_TRACKING_ID`(ali.env·주인 직접)에 설정 → 수집 시 API가 제품별 promotion_link 생성. #21의 "공통 트래킹링크(모든 제품 동일)" 한계 해소 — 247개 개별 deeplink(공통 접두부+제품별 분기), affiliate_tag=honsallim 검증.
- **R6. ★개발 마무리 → 성장 최우선 전환 [확정 #22, 주인 명시]**: 무인 가드레일·자동공개·측정 인프라·수익경로(/go/) 완비로 **개발 단계는 거의 끝**. **이제부터 매 세션 최우선 목표 = 성장(검색노출·트래픽·수익)**, '완성/유지보수'(스케줄러·자동화)와 구분. 매 세션 Claude가 선제적으로 성장안을 심도있게 제시(주인 매번 설명 불요). 레버=측정데이터 기반·토픽집중(홈오피스 심화)·롱테일·양질콘텐츠·인내. 메모리 [[growth-first-priority]] 최우선 등재. ※측정 인프라 셋업 완료(#22): Cloudflare Web Analytics·GSC(DNS인증+사이트맵)·네이버 서치어드바이저(meta+사이트맵).

## S. 멀티 채널(쿠팡+알리) 노출 전략 [확정] — 세션 #24 신규

> 정밀 리서치(정책·국내UX·해외+SEO 3축) + 비판점검 결과. 상세 EVENTS #24. [[design-research-first]]·[[incremental-critical-review]].

- **S1. 멀티채널 배치 방향 = "채널별 최선 추천 + 정성 기준 안내"(C안) [확정 #24, 리서치+주인 합의]**: 쿠팡·알리를 한 페이지에 노출하는 모델. ①**같은 상품 가짜 매칭 금지** — 쿠팡/알리는 파는 상품이 다름(직구 제네릭 vs 국내유통)이라 "한 상품 두 판매처 비교"(위어커터형)는 우리한텐 거짓 → **채널별로 각자 최선 상품을 정직 추천**(다른 상품일 수 있음). ②**차별 축 = 가격 아닌 정성**("국내 빠른배송·교환 쉬움=쿠팡 / 최저가·배송 김=알리" 등 변동 적고 거짓 안 되는 기준; preference uncertainty 감소→전환↑). ③**가격 숫자 박제 금지** → "가격은 링크에서 확인"+**갱신일**(무인 stale 회피·O7 연장). ④버튼마다 대가성 문구(첫머리+버튼근처·확정표현·**두 채널 모두 고지**·공정위 2024.12·O9). ⑤**추천 이유(왜) 필수**(thin/scaled content 패널티 방어). ⑥**수수료로 추천 편향 금지**(순서=판매량·적합성 등 진짜 근거·§0·O6·P3). ⑦모바일=가벼운 CSS sticky+버튼 세로스택(무거운 JS 위젯 금지·CWV). 채널 표기는 `products.source`(coupang/aliexpress) 기반.
- **S2. 가격비교형(A안) 탈락 + 리서치 근거·게이팅 [확정 #24]**: ★**가격 비교형 배치(쿠팡 vs 알리 최저가) 탈락** — 무인 운영에서 두 채널 가격이 서로 다르게 stale화되면 비교 결론이 거짓→**표시광고법 부당광고**(알리 실제 공정위 과징금 2.93억원×2·가짜정가/할인율 사례). "작성시점 기준" 면책 불충분. ★**쿠팡 공식 위젯에 가격 표시 위임 불가** — 추적차단 브라우저에서 미표시(세션 #24 `/reviews/` 데모 실측) → 위젯 의존 금지·텍스트 "링크에서 확인". ★**멀티채널 자체는 SEO 유리**(Google 공식 "여러 판매처 링크" 권장)·**선택마비 무관**(채널 2개·Chernev 2015 메타분석). **게이팅: 최종 배치·구현은 (a)`collector.coupang` 구현(현재 쿠팡 상품 0) + (b)1~2주 트래픽 데이터 후 확정** — 이번엔 방향·금지선만 확정(주인 "데이터로 결정" 판단 유지). 미해소 [확인불가]: 쿠팡 약관 가격표시 조항(로그인 차단)=가격 숫자 미표기로 자동 회피. 출처: 공정위 추천보증지침(2024.12.1)·표시광고법·알리 과징금(mdtoday)·Google 멀티판매처/Helpful Content·노써치 큐레이션·Chernev 2015.

## T. 무인 마케팅 전략 [확정] — 세션 #24 신규

> 정밀 리서치(소셜 배포·한국시장·SEO·자동화/컴플라이언스 4축) + 비판점검. 상세 EVENTS #24. [[growth-first-priority]]·[[design-research-first]].

- **T1. 무인 마케팅 채널 전략 = "소수 정식계정 + 공식 API + 절제 + 고유콘텐츠"(양산·버너 금지) [확정 #24, 리서치+주인 합의]**: ★**"버너 계정 양산·쇼츠 무한·하방위험 없음" 전략 탈락** — 플랫폼이 도메인(honsallim.com)을 스팸 플래그하면 정상 채널까지 도달 불능(플랫폼 측 연좌 실재)·YouTube 비진정콘텐츠 정책(2025.07)이 AI 양산을 사냥하고 위반 시 **내 모든 채널 연좌 삭제**·다계정=핑거프린트 일괄밴+프록시/인증 지속 수작업(=무인과 모순). **채널 우선순위**: ①**SEO/구글 = 본진**(외부 도메인이 동등경쟁 가능한 유일 검색채널; 네이버는 자사 블로그/카페 우대로 외부 도메인 불리) ②**Pinterest = 최우선 자동화 채널**(무료 공식API·외부유도가 플랫폼 본질·핀 수명 4개월+ 누적·한국 600만·인테리어/살림 토픽 일치·구매의도 85%; 단 Standard API 승인+개인정보처리방침 필요·핀→리뷰페이지·직접 제휴링크 금지) ③**Threads = 공짜 보조**(무료API 250/일·한국 트래픽 미약→기대 낮게). **탈락/후순위**: X(2026 종량과금+URL글 고가+링크 리치 -30~50%)·인스타(캡션 링크 불가)·틱톡(수동심사·엄격)·레딧(자동화 즉밴)·YouTube쇼츠(클릭링크 막힘+양산 연좌밴→차별화·나중). **네이버 블로그=별도 프로젝트**(D:\naver_blog·사람편집·자동복제 금지·연계만).
- **T2. SEO·콘텐츠 본진 + 2025.12 어필리에이트 패널티 회피 + 컴플라이언스 [확정 #24]**: ★**우리 사이트가 현재 'Dec2025 어필리에이트 손실군' 프로필에 가까움**(어필리에이트 71% 강타·평균 -42%, "소유·테스트 없는 Best 리스트" -87%; 우리=AI 자동생성+직접 안 써봄). **반전 무기 = 알리 판매량 데이터 = Google Information Gain(고유정보)** → **"데이터 기반 비교" 포지셔닝(+43% 승자군)**. **반드시 할 것**: ①모든 글 고유데이터 1개+(판매량·가격대 분석) ②토픽 클러스터(필러 3~4 + 롱테일 + 내부링크) ③E-E-A-T(저자 혼살다·방법론 페이지·첫머리 고지) ④발행속도 사람기준 2~4배(큐 1편/일 부합) ⑤**소수 핵심품목 주인 실사진/1인칭**(순수 100% 무인은 SEO 천장 — 구글이 '경험' 보상). 새 사이트 랭킹 **6~12개월 인내**(6개월 무성과 정상·조급한 양산이 독). **컴플라이언스**: 공정위 2024.12·X 2026.02 — **모든 소셜 게시물 첫머리/제목 대가성 고지 자동삽입 의무**(더보기·댓글 숨김 금지·누락=과징금+쿠팡 몰수). **측정 → 되는 채널 더블다운**(데이터 기반). **실행 로드맵**: Tier0 사이트 SEO 품질(지금·복리)→Tier1 Pinterest(병렬·승인 1~4주)→Tier2 Threads→Tier3 쇼츠/네이버연계. ※구글 백링크 패널티 공포는 과장(외부 스팸링크는 구글이 무시) — 진짜 리스크는 본 사이트가 scaled content로 보이는 것.

## U. 글 레이아웃·키워드 검색·배포 [확정] — 세션 #30 신규

> 라이브 검증 + 3관점 리서치(SEO·소비자행동·시각설계). 상세 EVENTS #30 / docs/ARTICLE_LAYOUT_TIER2.md. [[design-research-first]]·[[incremental-critical-review]].

- **U1. 키워드→글 경로 알리 검색 = 카테고리 영어 티어 검색어 [확정 #30, 라이브 검증]**: 한글 키워드 직접검색은 알리 영어 인덱스 매칭 실패→폰케이스·티셔츠 등 잡동사니(라이브 적발). 키워드→`keyword_relevance.resolve_category`→`category_collect.search_tiers`(영어 q "office chair"…)로 검색 후 키워드-적합성 필터→쿠팡과 결합. 미매핑 키워드=알리 건너뜀(fail-closed). 새 주제는 `category_sources.yml`에 카테고리(영어 q+제외어) 선등록 필요("아무 키워드나 완벽한 글" 아님). 라이브: 게이밍의자→하이브리드 13개(쿠팡1+알리12 의자)·thin 해소.
- **U2. 글(article) 레이아웃 = "카테고리 시각 언어 + 추천(롱테일) 의도 구조" [확정 #30, 리서치+주인]**: 글은 산문 텍스트벽("독서") 금지 → 시각 컴포넌트("쇼핑")로. 블루프린트: ⚡빠른결론박스→🏆큐레이션 픽카드(역할·소스·장단점)→체크포인트박스→📊비교표(1위강조)→💰예산표→🤝신뢰박스→❓FAQ아코디언. ①**결론 먼저**(NN/g F패턴) ②**전체 나열 X, 큐레이션 3~6 + 코멘터리** ③비교는 표 1개+1위 강조 ④가이드=시각 블록(텍스트는 그 안에·SEO 유지) ⑤**가짜 평점 금지→누적 판매량=신뢰**(별점 Review/AggregateRating 스키마=구글 수동조치 위험·금지) ⑥★**글 vs 카테고리 의도 분리**(카니발=같은 의도에서 옴·글=큐레이션/시나리오, 카테고리=전체 카탈로그). LLM 구조화 출력(`quick_verdict·picks·checkpoints·budget_tiers`)+카테고리 컴포넌트 재사용. 전체 스펙=docs/ARTICLE_LAYOUT_TIER2.md.
- **U3. 발행/배포 = build/site 커밋 + git push origin main → CI [확정 #30]**: `cmd_deploy`는 `git push origin main`(skip_wrangler)→GitHub Action이 **커밋된 build/site**를 Cloudflare Pages 배포(재빌드 없음). ★**현 버그: `cmd_publish_queue`/`cmd_deploy`가 build/site를 커밋 안 함** → 발행 클릭만으론 글이 CI에 안 감(라이브 404), 수동 build/site 커밋 필요 → #31 근본수정(무인 치명).

## 폐기된 결정 (역사 참조용)

| 폐기일 | 결정 | 폐기 사유 |
|--------|------|----------|
| 세션 #2 (2026-05-27) | C4 자동 게시 시간 없음 | 윈도우 스케줄러 자동 게시 활성 결정 → C6·C7로 대체 |
| 세션 #2 (2026-05-27) | C5 매주 2~3편 | 발행 편수 최대화 결정 → C8·C9로 대체 |
| 세션 #6 (2026-05-28) | E8 한국어 1인칭 허용 | 사용자 직접 사진 일체 없음 결정 → AI 이미지로 1인칭 게재는 거짓 광고 → L3 1인칭 완전 차단 (2차 변경 시 L1 선택적 액센트도 폐기) |
| 세션 #6 (2026-05-28) | D5 직접 사진 1~3장 의무 | 사용자 사진 일체 없음 → L2 AI 생성 + 쿠팡 위젯으로 전면 대체 |
| 세션 #6 (2026-05-28) | L2 초안 (페르소나 사진 6~9장) | 사용자 사진 없음 결정 → L2 재정의 (AI 생성) |
| 세션 #6 (2026-05-28) | L3 초안 (owned_products 메타 1인칭 허용) | 사용자 사진 없음 → AI 이미지로 1인칭은 거짓 광고 → L3 재정의 (1인칭 완전 차단) |
