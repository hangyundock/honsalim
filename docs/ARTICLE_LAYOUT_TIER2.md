# ARTICLE_LAYOUT_TIER2.md — 글(article) 레이아웃 종합 재설계 스펙 (세션 #30 확정)

> 다음 세션 즉시 구현용. 대화 없이도 이 문서만으로 작업 가능하게 작성.
> 목표: 글을 **"독서(텍스트 벽)"에서 "쇼핑(스캔·결정)"으로** — 카테고리(사진2)의 시각 언어를 쓰되
> 글은 **추천(롱테일) 의도**에 최적화. 주인 강력 요구(세션 #30): "의자 사러 왔는데 책 읽는 느낌".

---

## 0. 핵심 통찰 (3관점 리서치 수렴 — SEO·소비자행동·시각설계)

- **결론 먼저, 산문 나중** — 첫 화면이 "결정"이어야(빠른 결론 박스). 산문 도입 금지.
- **전체 나열 X → 큐레이션 픽(3~6) + 코멘터리** — 선택 피로↓ + 카테고리와 중복 회피.
- **비교는 표 1개**(알리 데이터) + **1위 강조**.
- **가이드 = 시각 블록**(체크포인트 박스·예산표·FAQ 아코디언) — 텍스트는 그 안에(SEO 유지), 문단 벽 제거.
- **가짜 평점 금지 → 누적 판매량 = 신뢰 신호**(§0). 별점 Review/AggregateRating 스키마 **금지**(자기수여=구글 수동조치 위험).
- ★**카테고리 vs 글 = 의도 분리**(카니발은 *같은 의도*에서 옴). 카테고리=전체 카탈로그·브라우징 / 글=큐레이션 픽·시나리오(자취·원룸) 코멘터리. **표 복붙·전체그리드 재현 금지**. 둘 다 색인(canonical 안 함).

## 1. 블루프린트 (확정 구조 — 위→아래 순서)

| # | 영역 | 시각 형태 | 데이터 출처 |
|---|------|----------|------------|
| 1 | 브레드크럼 + **H1**(예: "자취생 게이밍의자 추천 — 원룸 5~20만원 인체공학") | 텍스트 | 키워드 |
| 2 | 대가성 고지 + 작성자(혼살다)·"어떻게 골랐나" 1줄 | compact | 정적 |
| 3 | **⚡ 빠른 결론 박스**(조건부) | "예산최소→A · 가성비→B · 본격→C" | LLM `quick_verdict` |
| 4 | **🏆 추천 픽 카드**(큐레이션 3~6) | 이미지·**역할배지**(운영자추천/가성비/최다판매)·소스배지(쿠팡/알리)·가격(할인%)·**이런 분께**·**장단점**·구매 CTA | 쿠팡+알리 top + LLM 장단점/역할 |
| 5 | **📊 한눈에 비교표** | 이미지·제품·가격(정가취소선+할인%)·핵심스펙·이런분께·**누적판매**·구매 / **1위 강조** / (정렬 nice-to-have) | 알리 데이터(자동) |
| 6 | **✅ 사기 전 체크포인트** | 제목 박스 3~4개 | LLM `checkpoints[]` |
| 7 | **💰 예산대별 차이** | 표(예산대·특징·이런 분께) | LLM `budget_tiers[]` |
| 8 | **🤝 신뢰 박스** + 데이터 요약 | 박스(약속·이렇게 골랐어요·"누적판매 기준") | 정적+데이터 |
| 9 | **❓ FAQ 아코디언** | details/summary (★static HTML — JS 로드는 색인 안 됨) | `faqs[]`(이미 출력됨) |
| 10 | 풀 고지·사업자 + **관련 카테고리/글 내부링크** | footer | 정적 |

**공통**: 구매 CTA 3~4회 반복(픽·표·결론) · 모바일 sticky 구매바·표→카드 스택 · 스키마 **BreadcrumbList + ItemList만** · "어떻게 골랐나" 등 부차내용 progressive disclosure(머니 키워드는 접지 않음).

## 2. 쿠팡 vs 알리 역할 (하이브리드)

- **쿠팡**: 공식배너 이미지 + 구매. 운영자 큐레이션(수익). 데이터(할인·판매량) 없음 → 픽 카드(이미지·가격·장단점·구매), 역할배지 "운영자 추천".
- **알리**: 가격·정가·할인%·판매량 데이터(=Information Gain) → 비교표 + 픽 카드. 역할배지 "최다 판매"(판매량 1위)·"가성비"(최저가/할인). 장단점은 LLM 생성.
- 픽은 **소스 분리 zone이 아니라** 통합 "추천 픽"에 **역할 라벨 + 소스 배지**로(결정 우선·소스 투명).

## 3. 구현 범위

### (A) LLM enrich 구조화 출력 — `enricher/` 프롬프트 + 파서
산문 body 대신 구조화 JSON 추가 출력(기존 `title·summary·meta·faqs·products` 유지):
- `quick_verdict`: [{condition: "예산 최소", pick_ref, why}] ×2~3
- `picks`: [{product_ref(source+spid), role("운영자추천"|"가성비"|"최다판매"), for("이런 분께"), pros[2~3], cons[1~2], why}]
- `checkpoints`: [{title, why}] ×3~4
- `budget_tiers`: [{tier("5만원대"…), trait, for}]
- (faqs 이미 있음)
- 짧은 `lead`(도입 1~2문장)만 산문.
- ★**graceful fallback**: 구조화 필드 없으면 그 섹션 스킵(빈 섹션 X), 최악엔 현 산문 일부 유지. 검증 게이트(truth·schema·disclosure·links)는 유지.

### (B) 템플릿 — `templates/article.html` + 카테고리 컴포넌트 재사용
- 신규: 빠른 결론 박스.
- 재사용(`category.html` 패턴): 타입표(→예산표)·체크리스트박스·pick_card(장단점)·비교표(cmp)·FAQ 아코디언·신뢰박스. 단 **글 전용 클래스**(article 페이지는 category.css 미로드 → article.html `head_extra`에 스코프 CSS 또는 공통 CSS로).
- 스키마: `jsonld` BreadcrumbList + ItemList. 별점 금지.

### 단계
1. **목업 먼저**(이 블루프린트로 실제 화면) → 주인 확정.
2. 핵심 구현(빠른결론·픽카드·비교표·체크박스·예산표·FAQ) → 미리보기 HTTP 검증 → 배포.
3. nice-to-have 나중: 정렬 JS·모바일 sticky바·히어로 이미지(Imagen 비용).

## 4. 이미 된 것 (세션 #30 Tier 1 — 재사용 가능)

`renderer.py`·`product_card`(components.html)에 **데이터 플러밍 완료**(다음에 재사용):
- 글 상품카드가 `source`·`original_price_krw`·`discount_pct`·`sales_volume`을 가져옴(`ARTICLE_PRODUCTS_SQL`·`_draft_product_rows`·`_article_product_cards`).
- `product_card` 매크로 소스배지(쿠팡/알리)·할인(`p-sig`)·판매량(`p-vol`)·차등 버튼.
- 본문 3분할(`_split_article_body`: 도입/추천前/추천~) + 상품 소스분리(`coupang_products`/`ali_products`).
- ★Tier 1 article.html **레이아웃은 Tier 2로 대체 예정**(데이터 플러밍·매크로는 유지).

## 5. 비판적 점검 (구현 시 지킬 것)

- 중복 콘텐츠: 글=큐레이션 subset+시나리오 코멘터리. 카테고리 표/전체그리드 복붙 금지.
- SEO 텍스트: 표/박스/FAQ **안에** 텍스트(static HTML). 머니 키워드 visible.
- §0 진실성: 별점 안 만듦·판매량=proof. 픽은 "운영자/데이터 근거" 정직 표기(순위인 척 금지).
- 스키마 ≠ 보이는 콘텐츠 불일치 금지. Review 별점 스키마 금지.
- 과잉설계 경계: 핵심 먼저, JS·sticky·이미지는 나중.

## 6. 출처 (리서치 1차)
- Google: [고품질 제품 리뷰](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews) · [Review snippet 제약](https://developers.google.com/search/docs/appearance/structured-data/review-snippet)
- NN/g: [Data Tables](https://www.nngroup.com/articles/data-tables/) · [F-pattern](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) · [Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- Baymard: [Comparison features](https://baymard.com/blog/provide-comparison-features) · [Product list UX](https://baymard.com/blog/ecommerce-product-lists-report-and-benchmark)
- [Search Engine Land — Keyword cannibalization](https://searchengineland.com/guide/keyword-cannibalization)
