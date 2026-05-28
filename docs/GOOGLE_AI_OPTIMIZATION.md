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
