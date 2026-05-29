# DECISIONS.md — 혼살림 영구 [확정]

> 시간 흘러도 안 변하는 결정만. 출처·세션 번호 필수.
> 새 사실이 옛 [확정] 뒤집을 시: ~~취소선~~ + 세션 번호 + 새 항목.
> 무제한 cap. 영구 보존.

## A. 프로젝트 정체 [확정]

- **A1. 사이트명**: 혼살림 (Honsalim) — 세션 #1
- **A2. 도메인**: honsalim.com (Cloudflare Registrar, 마진 0) — 세션 #1
  - **세션 #2 (2026-05-28) 등록 완료**: 만료 2027-05-28·Auto Renew ON·SSL Active·Custom domain 연결
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
- **L6. Google Imagen 4 Fast 채택 [확정 세션 #6]**: AI 이미지 생성 도구는 **Google `imagen-4.0-fast-generate-001`** (Gemini API REST). AutoBlog (`D:\autoblog\tistory_revival\ai_image_gen.py`) 패턴 이식. 환경변수 `GOOGLE_API_KEY` (D:\secrets\affiliate_hub\google.env Phase 3 신설). 가격 $0.02/장. 무료티어 불가 — 결제 활성화 필수. 본 프로젝트 적용 명세 `docs/IMAGE_GENERATION.md` [확정] — 세션 #6
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

## 폐기된 결정 (역사 참조용)

| 폐기일 | 결정 | 폐기 사유 |
|--------|------|----------|
| 세션 #2 (2026-05-27) | C4 자동 게시 시간 없음 | 윈도우 스케줄러 자동 게시 활성 결정 → C6·C7로 대체 |
| 세션 #2 (2026-05-27) | C5 매주 2~3편 | 발행 편수 최대화 결정 → C8·C9로 대체 |
| 세션 #6 (2026-05-28) | E8 한국어 1인칭 허용 | 사용자 직접 사진 일체 없음 결정 → AI 이미지로 1인칭 게재는 거짓 광고 → L3 1인칭 완전 차단 (2차 변경 시 L1 선택적 액센트도 폐기) |
| 세션 #6 (2026-05-28) | D5 직접 사진 1~3장 의무 | 사용자 사진 일체 없음 → L2 AI 생성 + 쿠팡 위젯으로 전면 대체 |
| 세션 #6 (2026-05-28) | L2 초안 (페르소나 사진 6~9장) | 사용자 사진 없음 결정 → L2 재정의 (AI 생성) |
| 세션 #6 (2026-05-28) | L3 초안 (owned_products 메타 1인칭 허용) | 사용자 사진 없음 → AI 이미지로 1인칭은 거짓 광고 → L3 재정의 (1인칭 완전 차단) |
