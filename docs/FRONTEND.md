# FRONTEND.md — 혼살림 프론트엔드·SEO·Schema·CWV 설계

> Jinja2 템플릿 구조 + meta/OG/Schema 표준 + sitemap·RSS·IndexNow + 이미지·CSS·JS 자산 + CWV 측정.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 BACKEND.md로 이어짐.
> 등급: [확정] / [관찰] / [추정] / [확인 불가].
> 본 문서는 ARCH.md §3·§7·§8 + DB.md §4~§9 + DESIGN.md §5·§6·§9 + DECISIONS B·F를 전제로 함.

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| Jinja2 템플릿 구조 | Python 빌더 모듈 → BACKEND.md |
| meta·OG·Twitter Card 표준 | 검증 게이트 규칙 → POLICY.md |
| Schema.org JSON-LD 자동 주입 | DB 스키마 → DB.md |
| sitemap·RSS·IndexNow 발신 | 디자인 토큰·컴포넌트 → DESIGN.md |
| 이미지·CSS·JS 자산 전략 | 콘텐츠 구조 → SCENARIOS.md |
| CWV 측정·모니터링 | 운영 모니터링 절차 → OPS.md |
| 한글 SEO 최적화·hreflang 골격 | 다국어 콘텐츠 → (영어 확장 시 별도) |

---

## 2. Jinja2 템플릿 구조

### 2-1. templates/ 디렉토리

```
D:\affiliate_hub\templates\
├── base.html                       ← 모든 페이지 공통 (head·header·footer)
├── home.html                       ← / (홈)
├── article.html                    ← /articles/<slug>/
├── scenario_list.html              ← /scenarios/
├── persona_hub.html                ← /personas/<slug>/
├── about.html                      ← /about/
├── 404.html                        ← 미사용 경로
├── feed.xml                        ← RSS (XML 출력)
├── sitemap.xml                     ← sitemap (XML 출력)
├── _macros/
│   ├── schema.html                 ← JSON-LD 매크로 4종
│   ├── meta.html                   ← meta·OG·Twitter 매크로
│   ├── image.html                  ← srcset·lazy load 매크로
│   └── disclosure.html             ← 첫머리·푸터 disclosure
└── partials/
    ├── header.html
    ├── footer.html
    ├── disclosure_banner.html      ← E1 첫머리
    ├── hero_article.html
    ├── product_card.html           ← /go/ 게이트웨이 자동
    ├── budget_table.html
    ├── faq_section.html
    ├── related_scenarios.html
    ├── breadcrumb.html
    ├── scenario_card.html
    ├── persona_card.html
    ├── tag_chip.html
    ├── button_primary.html
    ├── personal_photo_badge.html
    └── price_update_note.html
```

### 2-2. 템플릿 상속 트리

```
base.html
  ├── home.html
  ├── article.html
  ├── scenario_list.html
  ├── persona_hub.html
  ├── about.html
  └── 404.html

base.html이 정의하는 블록:
  {% block title %}        — 페이지 제목
  {% block meta %}         — meta·OG·Twitter
  {% block schema %}       — JSON-LD
  {% block head_extra %}   — preload·canonical 등
  {% block breadcrumb %}   — 빵부스러기 (홈 제외)
  {% block main %}         — 본문
  {% block footer_extra %} — 페이지별 footer 추가 요소
```

### 2-3. Jinja2 설정 표준 [추정]

```
환경 옵션:
  autoescape=True (XSS 차단)
  trim_blocks=True, lstrip_blocks=True (출력 깔끔)
  enable_async=False (단순화)

커스텀 필터:
  ko_number       — 1200000 → "1,200,000"
  ko_won          — 1200000 → "1,200,000원"
  ko_date         — ISO → "2026년 6월 1일"
  ko_relative     — ISO → "3일 전" (옵션)
  ko_excerpt      — text → N자 잘라 "..."
  slugify_ko      — 한글 → kebab (음차 + 영문)
  md_to_html      — Markdown → HTML (제한 안전 모드)
  schema_jsonld   — dict → JSON-LD 문자열
```

---

## 3. 베이스·partials·매크로

### 3-1. base.html 골격 (의사 구조)

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>{% block title %}혼살림{% endblock %}</title>

  {# meta 매크로 #}
  {% block meta %}
    {% include "_macros/meta.html" %}
  {% endblock %}

  {# Schema JSON-LD #}
  {% block schema %}{% endblock %}

  {# 폰트·CSS preload #}
  <link rel="preload" as="font" type="font/woff2"
        href="/static/fonts/Pretendard-Variable.woff2" crossorigin>
  <link rel="preload" as="style" href="/static/css/main.{{ asset_hash.main_css }}.css">

  {# Critical CSS 인라인 (첫 화면) #}
  <style>{{ critical_css | safe }}</style>

  {# 본 CSS 비차단 로드 #}
  <link rel="stylesheet" href="/static/css/main.{{ asset_hash.main_css }}.css"
        media="print" onload="this.media='all'">

  {# canonical·hreflang #}
  <link rel="canonical" href="{{ canonical_url }}">
  {% block head_extra %}{% endblock %}
</head>
<body>
  {% include "partials/header.html" %}

  <main id="main-content">
    {% block breadcrumb %}{% endblock %}
    {% block main %}{% endblock %}
  </main>

  {% include "partials/footer.html" %}

  {# 비핵심 JS defer #}
  <script defer src="/static/js/lazyload.{{ asset_hash.lazyload_js }}.js"></script>
  {% block footer_extra %}{% endblock %}
</body>
</html>
```

### 3-2. partials 책임 분리

| Partial | 책임 | 입력 변수 |
|---------|------|----------|
| `header.html` | 브랜드 + nav | (없음, 정적) |
| `footer.html` | 4컬럼 + 사업자 + disclosure | `business_info` (등록 후) |
| `disclosure_banner.html` | 글 첫머리 E1 | (정적 문구) |
| `hero_article.html` | 페이지 hero | `article` 객체 |
| `product_card.html` | 상품 카드 + /go/ | `product` 객체 |
| `budget_table.html` | 예산 분배표 | `products[]`, `budget_target` |
| `faq_section.html` | FAQ 토글 | `faqs[]` |
| `related_scenarios.html` | 관련 시나리오 | `related[]` |
| `breadcrumb.html` | 빵부스러기 + Schema | `crumbs[]` |
| `scenario_card.html` | 시나리오 카드 | `scenario` 객체 |
| `persona_card.html` | 페르소나 진입 | `persona` 객체 |
| `tag_chip.html` | 태그 칩 | `text`, `kind` |
| `personal_photo_badge.html` | 직접 촬영 마크 | (정적) |
| `price_update_note.html` | "가격은 YYYY-MM-DD 기준" | `checked_at` |

### 3-3. 매크로 표준 호출

```
{% from "_macros/meta.html" import meta_tags %}
{{ meta_tags(title, description, og_image, canonical_url) }}

{% from "_macros/schema.html" import article_schema, breadcrumb_schema %}
{{ article_schema(article) }}
{{ breadcrumb_schema(crumbs) }}

{% from "_macros/image.html" import responsive_img %}
{{ responsive_img(image, sizes="(min-width: 1024px) 720px, 100vw") }}

{% from "_macros/disclosure.html" import first_line, footer_full %}
{{ first_line() }}
```

---

## 4. 페이지 5종 템플릿 명세

### 4-1. home.html (`/`)

**렌더 데이터**:
- `personas[]` — 3개
- `featured_scenarios[]` — priority 상위 6개
- `season_calendar[]` — 5개 시즌
- `latest_articles[]` — 6편

**구조 (DESIGN §6-1 일치)**:
```
{% extends "base.html" %}
{% block title %}혼살림 — 1인 가구 살림 추천{% endblock %}
{% block main %}
  Hero (브랜드 메시지 + 페르소나 진입 3 버튼)
  Featured scenarios (scenario-card × 6)
  Season calendar (시즌 진입 5개)
  About 짧은 카드 + disclosure 링크
{% endblock %}
```

### 4-2. article.html (`/articles/<slug>/`)

**렌더 데이터**:
- `article` — articles row + 조인 (products·images·personas)
- `crumbs[]` — Home > 페르소나 > 시나리오 > 글
- `faqs[]` — drafts.enriched_payload에서 추출
- `related[]` — 관련 시나리오 2~3편
- `prev_article` / `next_article` — 같은 페르소나 시간순

**구조 (DESIGN §6-3 일치)**:
```
{% extends "base.html" %}
{% block title %}{{ article.title }} | 혼살림{% endblock %}
{% block meta %}
  {{ meta_tags(article.title, article.meta_description,
              article.hero_image.url, article.canonical_url) }}
{% endblock %}
{% block schema %}
  {{ breadcrumb_schema(crumbs) }}
  {{ article_schema(article) }}
  {{ itemlist_schema(article.products) }}
  {% if article.has_review_eligible %}
    {{ review_schema(article.review_products) }}
  {% endif %}
{% endblock %}
{% block main %}
  {{ first_line() }}                  ← disclosure E1
  {% include "partials/hero_article.html" %}
  <section>누구를 위한 가이드인가 …</section>
  <section>왜 이 예산·시즌인가 …</section>
  <section class="products">
    {% for p in article.products %}
      {% include "partials/product_card.html" %}
    {% endfor %}
  </section>
  {% include "partials/budget_table.html" %}
  {% include "partials/faq_section.html" %}
  {% include "partials/related_scenarios.html" %}
  {{ footer_full(business_info) }}
{% endblock %}
```

### 4-3. scenario_list.html (`/scenarios/`)

- 필터 사이드바 (lg 이상)
- 카드 그리드 (모바일 1열·sm 2열·lg 3열)
- pagination

### 4-4. persona_hub.html (`/personas/<slug>/`)

- persona hero + 정보 사이드 (lg 이상)
- 해당 persona의 시나리오 카드 N개

### 4-5. about.html (`/about/`)

- 운영자 소개 + 신뢰 정책 + 사업자 정보 + 개인정보처리방침 링크

---

## 5. meta · OG · Twitter Card 표준

### 5-1. 모든 페이지 의무 (`_macros/meta.html`)

```
<meta name="description" content="{{ description | truncate(155) }}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#FAF6F1">  ← wood-50

<!-- Open Graph -->
<meta property="og:type" content="{{ og_type | default('website') }}">
<meta property="og:site_name" content="혼살림">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:image" content="{{ og_image }}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="ko_KR">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ description }}">
<meta name="twitter:image" content="{{ og_image }}">

<!-- GSC·Naver 인증 (Phase 1 발급 시 주입) -->
<meta name="google-site-verification" content="{{ gsc_token | default('') }}">
<meta name="naver-site-verification" content="{{ naver_token | default('') }}">
```

### 5-2. 페이지별 메타 차이

| 페이지 | og:type | image 출처 |
|--------|---------|-----------|
| 홈 | `website` | 사이트 대표 이미지 (운영자 직접 촬영) |
| 글 | `article` | article.hero_image (DB §9) |
| 시나리오 허브 | `website` | 페르소나 카테고리 이미지 |
| 페르소나 허브 | `profile` (또는 website) | persona 대표 이미지 |
| About | `website` | 운영자 환경 이미지 |

### 5-3. canonical 규칙

- 모든 페이지 self-canonical (자기 자신 가리킴)
- 쿼리 파라미터 (`?utm=...`) 없는 정규 URL
- 페이지네이션 (`?page=2`): self-canonical + `rel="prev/next"` (Phase 4 검토)
- 트레일링 슬래시 통일: 디렉토리 형태 (`/articles/<slug>/`)

### 5-4. robots.txt

```
User-agent: *
Allow: /
Disallow: /go/             ← 자체 게이트웨이 크롤링 차단

Sitemap: https://honsalim.com/sitemap.xml
```

---

## 6. Schema.org JSON-LD 자동 주입

### 6-1. 의무 Schema (F5 [확정])

| 페이지 | Schema |
|--------|--------|
| 모든 페이지 | BreadcrumbList |
| 글 | Article + ItemList (추천 상품) |
| 글 (직접 사용·사진 시) | Review (해당 상품만, F5) |
| 홈 | WebSite + 검색 박스 (Phase 4) |
| 페르소나 허브 | ItemList (시나리오 카드 목록) |
| 시나리오 허브 | ItemList |
| About | Person 또는 Organization (사업자 등록 후) |

### 6-2. 매크로 의사 출력 (Article)

```
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{ article.title }}",
  "description": "{{ article.meta_description }}",
  "image": ["{{ article.hero_image.absolute_url }}"],
  "datePublished": "{{ article.published_at }}",
  "dateModified": "{{ article.updated_at }}",
  "author": {
    "@type": "Person",
    "name": "혼살림 운영자",
    "url": "{{ site.base_url }}/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "혼살림",
    "logo": {
      "@type": "ImageObject",
      "url": "{{ site.base_url }}/static/img/brand-mark.png"
    }
  },
  "mainEntityOfPage": "{{ article.canonical_url }}"
}
</script>
```

### 6-3. ItemList 의사 출력

```
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    {% for p in article.products %}
    {
      "@type": "ListItem",
      "position": {{ loop.index }},
      "item": {
        "@type": "Product",
        "name": "{{ p.name }}",
        "image": "{{ p.image.absolute_url }}",
        "offers": {
          "@type": "Offer",
          "price": "{{ p.price_krw }}",
          "priceCurrency": "KRW",
          "availability": "https://schema.org/{{ p.availability_schema }}"
        }
      }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
```

### 6-4. Review Schema 적용 조건 (F5 엄격)

다음 모두 충족 시에만 출력:
- 사용자 직접 사진 1+ 첨부
- 본문 1인칭 직접 경험 표현 존재
- `images.source_type = 'user_photo'` 라벨
- 본 상품의 review가 글 1편당 1개만 (남발 금지)

검증 게이트에서 위 조건 외에 Review JSON-LD 자동 삽입 차단 (POLICY.md).

### 6-5. Google Indexing API 미사용 (F6 [확정])

어필리에이트 사이트의 Indexing API 사용은 정책 위반. 본 사이트는 IndexNow + sitemap만.

---

## 7. sitemap · RSS · IndexNow

### 7-1. sitemap.xml 생성

빌드 단계 `builder.sitemap` 모듈에서 자동 생성:

```
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://honsalim.com/</loc>
    <lastmod>{{ site_last_mod }}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  {% for a in articles %}
  <url>
    <loc>https://honsalim.com/articles/{{ a.slug }}/</loc>
    <lastmod>{{ a.updated_at }}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  {% endfor %}
  {# 페르소나·시나리오 허브 #}
</urlset>
```

### 7-2. RSS (feed.xml)

- 최근 30편
- `<title>` `<description>` `<pubDate>` 필수
- `<content:encoded>` 본문 발췌 (300자 요약)
- AdSense·SNS 차원 RSS 구독 niche 활용

### 7-3. IndexNow API 통보 (F4 [확정])

배포 직후 변경된 URL을 한 번에 전송:

```
POST https://api.indexnow.org/indexnow
Content-Type: application/json
{
  "host": "honsalim.com",
  "key": "{{ indexnow_key }}",
  "keyLocation": "https://honsalim.com/{{ indexnow_key }}.txt",
  "urlList": ["https://honsalim.com/articles/<slug>/", ...]
}
```

- 키 파일 `<key>.txt`를 `static/`에 두고 빌드 시 포함
- Bing·네이버·Yandex·Yep에 단일 통보로 분배 [확정]
- 실패 시 warn (block 안 함)

### 7-4. 네이버 서치어드바이저 (F2 의무)

- HTML 메타 토큰 (`naver-site-verification`) 의무
- 사이트맵 직접 등록 + RSS 등록
- 콘텐츠 발행 시 "수집 요청" 수동 또는 API (Phase 4)

### 7-5. 다음 웹마스터도구 (F3)

- HTML 메타 또는 파일 인증
- sitemap 등록

### 7-6. GSC (F1)

- Cloudflare DNS TXT (Domain property)
- 가장 권위 있음 (sub-domain 통합)

---

## 8. 이미지 srcset · lazy load

### 8-1. 매크로 `responsive_img` 의사 출력

```
<img
  src="/static/images/{{ image.slug }}-720w.webp"
  srcset="
    /static/images/{{ image.slug }}-480w.webp 480w,
    /static/images/{{ image.slug }}-768w.webp 768w,
    /static/images/{{ image.slug }}-1200w.webp 1200w,
    /static/images/{{ image.slug }}-1600w.webp 1600w"
  sizes="(min-width: 1024px) 720px, 100vw"
  width="{{ image.width_px }}"
  height="{{ image.height_px }}"
  alt="{{ image.alt_text_ko }}"
  loading="{{ 'eager' if image.is_hero else 'lazy' }}"
  fetchpriority="{{ 'high' if image.is_hero else 'auto' }}"
  decoding="async">
```

### 8-2. 4단 srcset (DESIGN §10-4)

| 폭 | 용도 |
|----|------|
| 480w | 모바일 작은 화면 |
| 768w | 모바일 큰 화면·태블릿 세로 |
| 1200w | 태블릿 가로·데스크톱 |
| 1600w | 고DPI 데스크톱 |

### 8-3. 변환 파이프라인 (BACKEND·assets)

- 원본 JPG/PNG → WebP 변환 (Pillow)
- 4단 폭별 리사이즈
- 메타 (width·height·file_size·mime_type) DB 저장
- 빌드 시 `static/images/<slug>-<w>w.webp` 출력

### 8-4. lazy load (네이티브 우선)

- `loading="lazy"` 우선 (브라우저 네이티브)
- IntersectionObserver fallback 미사용 (보조 JS 부담 회피)

### 8-5. 쿠팡 공식 위젯 (D5)

- iframe 또는 script 임베드
- 빌드 시 placeholder 박스 reserve (CLS 0.05 보호)
- `aspect-ratio` CSS로 박스 크기 강제

---

## 9. CSS · JS 자산 전략

### 9-1. CSS 파이프라인 [추정]

```
templates/_partials/tokens.css   ← DESIGN.md §3 토큰 (CSS 변수)
templates/_partials/base.css     ← reset + 타이포 + 그리드
templates/_partials/components.css ← 컴포넌트 18종
       │
       ▼ (빌드 단계 builder.assets)
build/static/css/main.<hash>.css
build/static/css/critical.<hash>.css  ← 첫 화면용
```

- minify (csso 또는 lightningcss 등 Python wrapper 또는 단순 정규식)
- hash 8자리 (캐시 무효화, B4 [확정])
- critical CSS는 base.html `<style>` 인라인 (LCP 보호)

### 9-2. JS 최소화

- jQuery·React·Vue 미사용 (Phase 4까지)
- 필요 JS 2개 한정:
  - `lazyload.js` — 네이티브 미지원 폴백 (~5KB)
  - `analytics.js` — Cloudflare Web Analytics 1줄 (외부 로드)
- 모든 JS `defer`

### 9-3. font 전략

- Pretendard Variable woff2 단일
- `preload` + `font-display: swap`
- subset 미적용 (한글 전체 필요)
- self-host (CDN 의존 X)

### 9-4. 캐시 헤더 (build/_headers, Cloudflare Pages)

```
/static/*
  Cache-Control: public, max-age=31536000, immutable

/articles/*
  Cache-Control: public, max-age=300, s-maxage=3600

/
  Cache-Control: public, max-age=60, s-maxage=600
```

### 9-5. CSP 헤더 (Phase 4 검토)

- default-src 'self'
- img-src 'self' + 쿠팡 위젯 도메인
- script-src 'self' + Cloudflare Analytics
- Phase 4에서 외부 위젯 도메인 화이트리스트 확정

---

## 10. CWV 측정 · 모니터링

### 10-1. 측정 도구 2종

| 도구 | 종류 | 용도 |
|------|------|------|
| Cloudflare Web Analytics | RUM (실제 사용자) | LCP·INP·CLS 실측 |
| PageSpeed Insights (수동) | Synthetic | 변경 직후 회귀 점검 |

### 10-2. 목표 (B6 [확정])

| 지표 | 목표 | block 기준 |
|------|------|-----------|
| LCP | ≤ 2.0초 | ≤ 2.5초 (PageSpeed) |
| INP | ≤ 150ms | ≤ 200ms |
| CLS | ≤ 0.05 | ≤ 0.1 |

### 10-3. 빌드 단계 정적 점검 [추정]

- 모든 img에 width·height 속성 존재 검사 (CLS 0.05 강제)
- Pretendard preload 링크 존재 검사
- Critical CSS 인라인 존재 검사
- 본문 외부 JS 차단 (광고·트래커 inline 금지)

### 10-4. RUM 알림 [추정]

OPS.md에서 확정:
- LCP 75th percentile > 2.5초 24시간 지속 → STATE.md 알림
- CLS 0.1 초과 페이지 발견 → 즉시 알림

---

## 11. 한글 SEO 최적화

### 11-1. 네이버·다음 우선 [관찰]

| 항목 | 적용 |
|------|------|
| meta description | 한국어 150자 (영문 기준과 다름) |
| 제목 길이 | 28~32자 (네이버 검색 결과 잘림 방지) |
| h2·h3 구조 | 위키바이 패턴 — 짧은 h2 + 명사형 |
| 첫 80자 | 글의 핵심 검색어 자연스럽게 포함 |
| 이미지 alt | 한국어 + 핵심 키워드 |
| URL slug | 한글 음차 또는 영문 (UTF-8 한글 URL은 SNS 공유 시 깨짐 사례 [관찰]) |

### 11-2. URL 한글 vs 영문 [추정]

- 본 사이트: **영문 kebab-case** (음차) 선택
- 이유: SNS·이메일 공유 시 한글 URL이 percent-encode → 신뢰도 ↓
- 예: `wonroom-cheot-jachi-30` (좋음) / `원룸-첫-자취-30` (회피)

### 11-3. 키워드 자연 배치

- 본문 첫 80자 내 핵심 키워드 1회
- h2 헤더에 키워드 변형 2~3회 (남발 금지)
- 이미지 alt에 1회
- meta description에 1회

### 11-4. 네이버 정책 [관찰]

- 어필리에이트 사이트 자체는 차단되지 않음
- 단, "광고성 도배"는 검색 노출 ↓
- 본 프로젝트는 인간 편집 + 직접 사진 + 1인칭 → 정상 콘텐츠로 인식 기대

### 11-5. Daum

- 카카오 광고 충돌 가능성 [관찰] (어필리에이트는 명시 차단 아님)
- F3 등록 의무

---

## 12. 다국어 확장 슬롯 (hreflang 골격)

### 12-1. Phase 6 영어 확장 검토 대비 [추정]

현 시점 한국어 단일. 단, 후속 확장 가능성을 차단하지 않도록 골격만 준비:

| 항목 | 한국어 단독 (현재) | 영어 추가 (Phase 6+) |
|------|--------------------|----------------------|
| URL 구조 | `/articles/<slug>/` | `/ko/articles/...` + `/en/articles/...` |
| hreflang | `<link rel="alternate" hreflang="ko" href="...">` | 다국어 매핑 추가 |
| sitemap | 단일 | hreflang 매핑 sitemap |
| canonical | self | self per locale |

### 12-2. 영어 확장 시 작업 [추정]

- DB.md `articles.locale` 컬럼 추가 (`ko`/`en`)
- 영문 페르소나·시나리오 재기획
- 영문 도메인 분리 vs 서브폴더 결정 (서브폴더 권장 [관찰])

### 12-3. 본 시점 권고

- 현재는 hreflang **빈 골격만** 매크로에 두기
- 한국어 단일 시점에는 출력 안 함 (이중 설정 혼란 회피)

---

## 13. 다음 단계

FRONTEND.md 사용자 검토 → 승인 후 **BACKEND.md (Python 모듈·API·빌드 파이프라인 상세)** 작성 진입.

BACKEND.md에서 확정할 핵심:
- collector·enricher·validator·writer·builder·dashboard·deployer·tracker 각 모듈 인터페이스
- Claude API 프롬프트 외부화·캐시 적용
- Cloudflare API 호출 패턴 (Pages·R2·D1·Workers)
- Workers `go_gateway.js` 구현 골격
- 빌드 manifest 핸들링 코드 흐름
- 에러 처리·재시도·로깅 표준
- 테스트 전략 (validator 회귀 테스트 최우선)
- CLI 명령 11개 인터페이스 명세

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (Jinja2 + meta·OG·Schema + sitemap·IndexNow + CWV) | Claude Opus 4.7 |
