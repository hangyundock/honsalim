# GOOGLE_AI_OPTIMIZATION.md — Google AI 검색 최적화 가이드 정합

> 출처: Google Search Central 공식 가이드 (2026-05-15 발표) — 세션 #6 조사·적용 [확정].
> 원본: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide?hl=ko
> 분석 기사: Search Engine Journal "Google's New AI Search Guide Calls AEO And GEO 'Still SEO'"
> 본 문서: 공식 가이드 핵심 + 본 프로젝트 정합 매트릭스 + 강화 작업.

---

## 1. Google 공식 입장 한 줄 [확정 Google 공식 인용]

> "From Google Search's perspective, optimizing for generative AI search is optimizing for the search experience, and thus still SEO."

**AEO / GEO = SEO**. 별도 분야 X. 본 프로젝트 기존 SEO 전략(FRONTEND·POLICY) 그대로 유효.

---

## 2. 핵심 메커니즘 [확정 Google 공식]

| 메커니즘 | 설명 | 본 프로젝트 영향 |
|---------|------|----------------|
| **RAG (검색 증강 생성)** | Google 핵심 순위 시스템이 검색 색인에서 관련 페이지 retrieval → AI 답변 생성 | 페이지 색인·크롤링 가능성·신선도 우선 |
| **Query fan-out** | 모델이 관련 검색어 세트 생성 → 추가 정보 fetch | 시나리오 cross-link (related-scenarios)·페르소나×예산×시즌 구조가 자연 fan-out 친화 |

---

## 3. Google이 명시 부정한 "하지 마라" [확정 Google 공식]

| ❌ 회피 | 이유 |
|--------|------|
| **llms.txt 파일 생성** | "특별 처리 없음 — 새로운 기계 가독형 파일 불필요" |
| **콘텐츠 청킹 (작은 조각 분할)** | "Google 시스템이 다중 주제 이해 가능" |
| **AI용 별도 재작성** | "동의어·의미 이해 가능 — 특별한 방식 불필요" |
| **인증되지 않은 언급 추구** | "스팸 차단 시스템이 필터링" |
| **과도한·특수 Schema 마크업** | "구조화된 데이터 필수 아님" (단 기존 Schema.org는 리치 결과용 권장) |

→ 본 프로젝트에 추가 작업 의무 없음. `robots.txt`·`sitemap.xml`·Schema.org Article/ItemList/Product/BreadcrumbList(이미 [확정 J5]) 유지.

---

## 4. Google이 권장하는 "해라" [확정 Google 공식]

### A. 콘텐츠 차별화 (핵심)

| 권장 | 기준 |
|------|------|
| **non-commodity content** | 일반 지식 X, **독자적 인사이트** O |
| 예시 ❌ | "7 Tips for First-Time Homebuyers" (commodity) |
| 예시 ✅ | "Why We Waived the Inspection & Saved Money: A Look Inside the Sewer Line" (고유 경험·인사이트) |
| 사용자 중심 | 유용·신뢰·사람 중심 |

### B. 구조·HTML

| 권장 | 본 프로젝트 매핑 |
|------|---------------|
| 의미론적 HTML (h1·h2·h3·section·article) | FRONTEND §2 Jinja2 템플릿 [확정] |
| 단락·섹션·제목 명확 구조 | FRONTEND §3 위키바이형 패턴 [확정] |
| JavaScript SEO 모범 사례 | 본 프로젝트 정적 HTML 빌더 — JS 의존 X [확정 B7] |
| Core Web Vitals 우호 | FRONTEND §9 Critical CSS·Pretendard preload [확정] |
| 중복 콘텐츠 최소 | **시나리오 매트릭스 60 슬롯 — 진짜 다른 가치 의무 (M3 신설)** |

### C. 멀티미디어

| 권장 | 본 프로젝트 매핑 |
|------|---------------|
| 고화질 이미지·동영상 텍스트 뒷받침 | AI 생성 (Imagen 4 Fast, L6 [확정]) + 쿠팡 공식 위젯 (L8 [확정]) |
| 강화 필요 | **AI 이미지 시각 검수 (M4 신설)** — 가짜 보임 회피, 일관 톤 |

### D. 비즈니스 정보·로컬·쇼핑

| 권장 | 본 프로젝트 매핑 |
|------|---------------|
| Google 비즈니스 프로필 | **Phase 4 사업자 등록 후 검토 (M5 신설)** |
| Google Merchant Center | 어필리에이트 사이트라 적용 불요 [추정] |
| Business Agent (Search 챗) | Phase 6+ 검토 |

### E. AI Agent

| 권장 | 본 프로젝트 매핑 |
|------|---------------|
| AI 에이전트 대응 (UCP 프로토콜) | **Phase 6+ 검토 (M6 신설)** — Universal Commerce Protocol ucp.dev |

---

## 5. 본 프로젝트 정합 매트릭스

### 5-1. 이미 정합 [확정 Google 권장 충족]

| 영역 | 본 프로젝트 상태 | 출처 |
|------|----------------|------|
| sitemap.xml + robots.txt + IndexNow | FRONTEND §3·F1·F4 [확정] | F4·F5 |
| Schema.org Article + ItemList + Product + BreadcrumbList | builder.jsonld 4종 [확정 J5] | J5 |
| 의미론적 HTML | Jinja2 base.html + h1·h2·h3 구조 [확정] | FRONTEND §2 |
| Core Web Vitals 우호 | Critical CSS + Pretendard preload + 보안 헤더 [확정] | FRONTEND §9 |
| 위키바이형 정보 분석 톤 | L1·L3 [확정] | DECISIONS L |
| 1인칭 무조건 차단 | L3 [확정] validator/truth.py | DECISIONS L3 |
| 쿠팡 공식 위젯 (상품 이미지) | L8 [확정] | DECISIONS L8 |
| 시나리오 cross-link (Query fan-out 친화) | related-scenarios 컴포넌트 [확정] | DESIGN §6-3 |
| 자동 게시·인간 1클릭 승인 | C1·C7 [확정] | DECISIONS C |

### 5-2. 강화 필요 (M 카테고리 신설)

| # | 영역 | 작업 |
|---|------|------|
| **M1** | 콘텐츠 차별화 의무 강화 | Claude API enricher prompt에 "non-commodity content" 명시. 일반 지식 reword 회피, 시나리오 페르소나×예산×시즌 결합 고유 인사이트 의무 |
| **M2** | E-E-A-T author 강화 | `Person` Schema (운영자) + author 메타 + about 페이지 운영자 정보 명시 (Phase 4 진입 시) |
| **M3** | 시나리오 매트릭스 "확장 콘텐츠 악용" 회피 | 60 슬롯 시나리오 매트릭스 — 페르소나×예산×시즌 결합 진짜 다른 가치 의무. 단순 변형 (예: "30만 자취"·"35만 자취") 회피. SCENARIOS §2-1 매트릭스 차별화 기준 명시 |
| **M4** | AI 이미지 시각 검수 | AutoBlog `image_qa.py` 패턴 이식 — `src/validator/image_qa.py` 신설 (Phase 3 시점). 가짜 보임·일관성 자동 점검 |
| **M5** | Google Business Profile | Phase 4 사업자 등록 후 등록 검토 (운영자 신뢰성·로컬 노출) |
| **M6** | AI Agent UCP 프로토콜 대응 | Phase 6+ 검토 (Universal Commerce Protocol — Search 내 챗 기능) |

---

## 6. 본 프로젝트 추가 작업 의무 (다음 세션·Phase 진척 시)

### Phase 2 (현재)
- [ ] **enricher prompt 갱신** (M1) — `src/enricher/prompt_templates/article_main.md`에 "non-commodity content" 의무 추가
- [ ] **SCENARIOS §2-1 차별화 기준 명시** (M3) — 60 슬롯 매트릭스 진짜 다른 가치 의무

### Phase 3 (디자인·콘텐츠)
- [ ] **author 명시 + Person Schema** (M2)
- [ ] **AI 이미지 시각 검수 모듈** (M4) — `src/validator/image_qa.py` (AutoBlog 패턴 이식)

### Phase 4 (첫 출시)
- [ ] **Google Business Profile 등록** (M5)
- [ ] about 페이지 운영자 정보 명시

### Phase 6+
- [ ] **UCP 프로토콜 대응** (M6, AI Agent)

---

## 7. 핵심 안심 사항 [확정 Google 공식]

- **본 프로젝트가 이미 잘 하고 있는 것**: SEO 기초·Schema.org·CWV·robots/sitemap·인간 1클릭 승인·차별화 컨셉(시나리오 결합)
- **본 프로젝트가 안 해도 되는 것**: llms.txt·콘텐츠 청킹·AI용 재작성·특수 Schema — Google이 명시 부정
- **AEO/GEO 별도 전략 불요** — 기존 SEO 정책 그대로 적용

---

## 7-bis. AutoBlog/tistory_revival 통합 (cross-project)

본 가이드는 AutoBlog 영역에도 적용됨 (사용자 명시 통합 지시, 세션 #6):

- `D:\autoblog\AUTOBLOG_SEO_MASTER.md` — TASK_019 Phase 1A+1B (약 2주 SEO 조사) + 본 가이드 통합 마스터 (글쓰기 직전 1 페이지)
- `D:\autoblog\AUTOBLOG_DECISIONS.md` §H4 (AI Guide 인지, 세션 #89) + §H6·H7 (마스터 참조·non-commodity)
- `D:\autoblog\tistory_revival\TISTORY_DECISIONS.md` §Q (마스터 참조·tistory 적용)
- AutoBlog 발견 추가: AI Overview 별도 기준 없음 [확정 P1B S7] — 본 프로젝트 M7 정합 강화

### 7-bis-2. AutoBlog/tistory_revival prompt 코드 적용 [확정 세션 #6 2026-05-29]

기존 AutoBlog/tistory_revival prompt에 이미 강한 정합 [확정]:
- AutoBlog `src/content/templates/system_prompt.txt` Rule 1 (1인칭 차단)·Rule 12 (INFORMATION GAIN = non-commodity 명시)·Rule 13 (people-first)
- tistory_revival `content_profiles.py` HEALTH·GENERAL system (가짜 1인칭 금지·의료 안전·과장 금지)

본 세션 추가 강화 (사용자 명시 진행):
- AutoBlog system_prompt.txt **Rule 14 신규** (Scaled Content Abuse 회피 — 키워드 클러스터 중복 글 70%+ 차별화 의무·`_quality_warning: duplicate_risk` 시그널)
- AutoBlog system_prompt.txt **Rule 15 신규** (AUTHOR INTEGRITY — 가짜 author 주장 금지, QRG §4.5.3 정합)
- tistory_revival `content_profiles.py` HEALTH·GENERAL 둘 다 **[차별화·non-commodity]·[저자 정직성]** 절 신규 추가
- 검증: `python -c "..." → non-commodity in health/general: True` [확정]

**결과**: AutoBlog/tistory_revival 매일 자동 발행 글에 본 정합 즉시 적용 (다음 호출부터).

### 7-bis-3. tistory_revival seo_gate.py 코드 게이트 추가 [확정 세션 #6 2026-05-29]

`D:\autoblog\tistory_revival\seo_gate.py`에 게이트 신규 추가:
- **`_FAKE_AUTHOR` 패턴 3건** — "저자/에디터가 직접·체험·방문·테스트", "우리 팀·저희 팀이 직접·체험·테스트", "본 저자/에디터/블로그가 직접·체험·방문" 차단
- `check_article()` `fake_author` 검출 시 issue 추가 — "가짜 author 주장 발견 (AUTOBLOG_SEO_MASTER §2 #9·QRG §4.5.3 Lowest 위험)"
- `metrics["가짜author"]` 필드 추가 (재생성 피드백용)
- 검증: 정상 글 통과 + 위반 글 차단 [확정 직접 테스트]

**효과**: tistory_revival 매일 자동 발행 시 가짜 author 주장 자동 차단 (재생성 피드백 트리거). prompt (content_profiles)와 함께 2단계 방어.

### 7-bis-4. AutoBlog FAQPage Schema 자동 생성 [확정 세션 #6 2026-05-29]

`D:\autoblog\src\content\enhancer.py` `inject_eeat_signals()` 보강:
- **`_extract_faqs(content)` 신설** — 본문 끝 `<h3>Q?</h3><p>A</p>` 패턴 자동 추출 (질문이 ?로 끝나는 H3만, 일반 섹션 오탐 X)
- **FAQPage JSON-LD 자동 추가** — FAQ 1+ 있을 때만, BlogPosting JSON-LD 다음에 삽입
- Google 공식 리치 결과 권장 (Q&A 검색 노출 가능) — AUTOBLOG_SEO_MASTER §2 #1 명시
- 영향: FAQ 없는 글 0, FAQ 있는 글만 Schema 추가
- 검증: 2개 Q/A 추출·일반 h3 오탐 X [확정 직접 테스트]

**효과**: AutoBlog system_prompt Rule 10 ("End the post with a short FAQ section containing 2-3 questions using <h3> tags")이 이미 강제 — 본 세션 이전 발행 글도 자동 적용 (재처리 시).

## 9. AutoBlog 2주 SEO 조사 (P1A+P1B) 통합 — 본 프로젝트 적용

> 출처: `D:\autoblog\tasks\TASK_019_FINAL_SYNTHESIS.md` §2 + `D:\autoblog\AUTOBLOG_SEO_MASTER.md` (혼살림 세션 #6 cross-project 검증)
> Google AI Guide (2026-05-15)는 본 결과의 **공식 확정·확장**. 본 §9는 본 프로젝트 정합 + 누락 6건 명시.

### 9-1. S1~S12 본 프로젝트 정합 매트릭스

| AutoBlog | 본 프로젝트 적용 | 상태 |
|---------|---------------|------|
| S1 AI 콘텐츠 자체 금지 X | enricher Claude API 활용 | ✅ |
| S2 Scaled Content Abuse = "primary purpose manipulating + little value" | M3 확장 콘텐츠 악용 회피 | ✅ |
| S3 QRG §4.5.3 가짜 author profile = Lowest | §9-2 author 거짓 금지 정책 | ⚠️ → 본 §9-2 신설 |
| S4 가짜 1인칭 + AI 바이오 = §4.5.3 정면 | L3 1인칭 무조건 차단 | ✅ 회피 |
| S5 Helpful Content "first-hand expertise" 충돌 | L3 + L7 AI 명시 표기 | ✅ |
| S6 E-E-A-T 자체는 순위 요소 X — Trust 축이 본질 | §9-2 명시 | ⚠️ → 본 §9-2 신설 |
| S7 AI Overview 별도 기준 없음 | M7 정합 | ✅ |
| S8 Core Ranking = Page-level + site-wide + Topic-level 3축 | §9-2 명시 | ⚠️ → 본 §9-2 신설 |
| S9 저품질 페이지가 site-wide 저해 | §9-2 정리 의무 | ⚠️ → 본 §9-2 신설 |
| S10 "lots of content many topics" 경고 신호 | SCENARIOS 60 슬롯 = 동일 위험 영역 | ⚠️ → 본 §9-3 점검 |
| S11 author "written or reviewed" + AI disclosure | publisher 명시 (M2 강화 Phase 4) | ⚠️ 부분 |
| S12 제3자 DA/authority 점수는 Google 신호 X | §9-2 명시 | ⚠️ → 본 §9-2 신설 |

**정합률**: 완전 5/12 + 부분 7/12 → 본 §9 갱신으로 12/12 정합 달성.

### 9-2. 누락 6건 본 프로젝트 적용 명시 [확정 세션 #6]

**N1 (S3 정합) — author 거짓 금지 [확정]**:
- 본 프로젝트 운영자 = 사용자 본인 1인 (가상 페르소나 X — Hana Kim 류 위험 원천 차단)
- about 페이지 운영자 정보 = 본인 실명·실 운영 (M2 Phase 4 의무)
- 본 프로젝트 author 영역 약점 없음 [확정], 단 약점 발생 시 §4.5.3 정면 일치 위험 인지

**N2 (S6 정합) — E-E-A-T는 순위 요소 X, Trust 축이 본질 [확정 P1B S6]**:
- Helpful Content 공식 문서: "E-E-A-T itself isn't a specific ranking factor"
- Trust (신뢰)가 family 최상위 — 진실성·정확성·투명성이 본질
- 본 프로젝트 truth 게이트 4단계 (POLICY §3 + ARCH §9) 정합 — Trust 축 충족

**N3 (S8 정합) — Core Ranking 3축 [확정 P1B S8]**:
- (a) Page-level: 글 단위 품질
- (b) Site-wide signals: 사이트 전체 신호 (저품질 페이지 영향)
- (c) Topic-level expertise: 주제 영역 전문성 — **혼살림 = 1인 가구·자취·홈오피스 단일 주제 집중**으로 본 축 강함

**N4 (S9 정합) — 저품질 페이지가 site-wide 저해 [확정]**:
- Core Updates 공식: "deleting the unhelpful content can help the good content on your site perform better"
- 본 프로젝트 운영 의무: 발행된 글 중 trafffic·체류 저조한 글은 정기 검토 → 보강 또는 비공개 처리 (Phase 5+ 운영 의무)
- 대시보드에 "저성과 글 목록" 추가 검토 (tracker.report 확장)

**N5 (S12 정합) — 제3자 DA/authority 점수는 Google 신호 X [확정]**:
- 2024-03 Core+Spam Update 블로그 원문: 제3자 도구 점수 (Moz DA, Ahrefs DR 등)는 Google이 사용하는 신호 아님
- 본 프로젝트 운영 의무: 외부 SEO 도구 점수에 의존하지 않음. Google Search Console·Cloudflare Analytics·실측 클릭/체류만 활용

### 9-3. SCENARIOS 60 슬롯 = "lots of content many topics" 경고 신호 점검 [확정]

AutoBlog S10 위험 신호 3건:
1. **"extensive automation to produce content on many topics"** — 본 프로젝트 자동 게시 활성 (C7), 단일 주제 (1인 가구) 집중이므로 위험 작음
2. **"producing lots of content on many different topics"** — SCENARIOS 60 슬롯 매트릭스 = 동일 주제 (1인 가구) 내 세부 분류이지 다른 주제 아님 → 위험 작음
3. **"changing the date of pages to make them seem fresh"** — 본 프로젝트 정책 없음 — `unapprove → validated` 패턴은 콘텐츠 갱신 시 사용, 단순 날짜 변경 X. 명시 의무

**판정**: 본 프로젝트 SCENARIOS 60 슬롯은 단일 주제 (1인 가구) 내 세부 결합이라 S10 위험 직접 해당 X. M3 차별화 의무 + N3 (c) Topic-level expertise로 강함. 단 단순 변형 글 양산은 여전히 금지 (M3 [확정]).

### 9-4. 다음 세션 자동 인식 핵심 (§9 영역)

- **S3+S4+S5** Hana Kim 위험 = 본 프로젝트 L3 1인칭 무조건 차단으로 원천 회피 (사용자 본인 1인 운영)
- **S6** E-E-A-T 자체는 순위 요소 X — Trust 축이 본질
- **S8** Core Ranking 3축 — 본 프로젝트 Topic-level (1인 가구 단일 주제) 강함
- **S9** 저품질 페이지 정리 의무 — Phase 5+ 대시보드 확장
- **S10** "lots of content many topics" = 본 프로젝트 SCENARIOS 60 슬롯 ≠ 위험 (단일 주제 세부 분류)
- **S12** 제3자 DA 점수 X — Google Search Console·실측만 활용

---

## 8. 다음 세션 자동 인식 핵심

- Google AI 검색 = SEO 그대로 (별도 분야 X)
- llms.txt·청킹·AI 재작성 안 함 (Google 부정)
- non-commodity content (독자적 인사이트) 의무
- Query fan-out 친화 구조 (related-scenarios cross-link)
- 본 프로젝트 강화 작업 6건 (M1~M6) DECISIONS M 카테고리

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-28 (세션 #6) | 최초 작성 (Google 공식 가이드 2026-05-15 + 본 프로젝트 정합 매트릭스 + M 카테고리 6건 신설) | Claude Opus 4.7 |
