# VALIDATOR_PATTERNS.md — 검증 게이트 정규식·패턴 사전 정의

> 출처: POLICY §3·§4·§5·§6 + BACKEND §2-3 [확정]
> 사용: Phase 2 validator 4모듈 구현 시 본 패턴을 코드에 삽입.
> 등급 엄격 적용: [확정] = 정규식 100% 정의 가능 / [관찰] = 일부 검출 패턴 / [추정] = 휴리스틱·튜닝 필요.

---

## 1. 외부 단축 URL 차단 (links 게이트) — [확정]

POLICY §6-1 도메인 정확 매칭. 정규식:

```python
SHORT_URL_DOMAINS = [
    r'vivoldi\.com',
    r'bit\.ly',
    r'goo\.gl',
    r'tinyurl\.com',
    r't\.co',
    r'bitly\.com',
    r'rebrand\.ly',
    r'ow\.ly',
    r'is\.gd',
    r'cutt\.ly',
    r'me2\.do',
]

# 호스트 추출 후 매칭
URL_PATTERN = re.compile(r'https?://([^/\s]+)')
```

[확정] — 정확 도메인 목록 명시. 본 목록 외 단축 URL 발견 시 분기 1회 갱신.

---

## 2. 허용 도메인 화이트리스트 (links 게이트) — [확정]

```python
ALLOWED_LINK_DOMAINS = [
    r'honsalim\.com',
    r'link\.coupang\.com',
    r'partners\.coupang\.com',
    r'ads-partners\.coupang\.com',
    # Phase 5 알리 추가 시:
    # r's\.click\.aliexpress\.com',
]
```

---

## 3. disclosure 첫머리 키워드 매칭 (disclosure 게이트) — [확정]

POLICY §2-2 표준 문구 검출:

```python
DISCLOSURE_FIRST_REQUIRED_KEYWORDS = [
    '쿠팡 파트너스',
    '수수료',
]
# 본문 첫 200자 안에 모두 포함되어야 통과
```

POLICY §2-3 푸터 풀 문구:

```python
DISCLOSURE_FOOTER_REQUIRED_KEYWORDS = [
    '쿠팡 파트너스',
    'AliExpress',
    '본인',  # "본인 및 가족"
]
# 본문 마지막 800자 안에 모두 포함
```

[확정] — POLICY 명시 그대로.

---

## 4. AI 자동 생성 흔적 (truth 게이트) — [관찰] + [추정]

POLICY §3-1-4 패턴 중 정규식 가능한 것만:

```python
# [확정] — 명시 단정형 패턴
AI_TRACE_PATTERNS_HARD = [
    r'본 글은 AI(가|로) ',
    r'ChatGPT(로|가) (작성|생성)',
    r'As an AI',
    r'I cannot ',
    r'다음은 [가-힣\s]{1,20} 입니다[:.]',  # LLM 출력 흔적
    r'\*\*\*+',  # 마크다운 깨짐 ***
    r'\$\$',  # LaTeX 흔적
]

# [관찰] — 일부 false positive 가능, 본문 분량에 따라 임계 조정
AI_TRACE_PATTERNS_SOFT = [
    (r'~로 알려져 있습니다', 3),  # 3회+ 발견 시 fail
    (r'(훌륭한|완벽한|최고의)', 5),  # 5회+ → fail
]
```

[관찰] 임계는 본문 평균 2,000자 기준. Phase 2 운영 후 튜닝.

---

## 5. 1인칭 표현 검출 (truth 게이트) — [관찰]

POLICY §3-1-3:

```python
FIRST_PERSON_PATTERNS = [
    r'써본 (결과|이후|후)',
    r'사용해보(니|면서)',
    r'내 (원룸|책상|방|집|자취)',
    r'우리(집|원룸)',
    r'(지난|작년) (여름|겨울|봄|가을)에 (사용|샀|샀더니)',
    r'(\d+개월|\d+년) (사용|썼)',
]

# 검출되면 → 해당 상품·전체 글에 user_photo 있는지 확인
# 없으면 → fail (POLICY §3-1-3)
```

[관찰] — 1인칭 한국어는 다양해서 100% 검출 불가. 자주 쓰는 패턴 중심.

---

## 6. 가격 정확성 (truth 게이트) — [확정]

POLICY §3-1-1:

```python
def check_price_accuracy(body_md, products):
    # 본문에서 "1,200,000원" 류 가격 추출
    pattern = re.compile(r'([\d,]+)\s*원')
    body_prices = [int(m.replace(',', '')) for m in pattern.findall(body_md)]

    # collector 가격과 ±5% 이내 매칭 (POLICY §3-1-1)
    for p in products:
        if not any(abs(bp - p.price_krw) / p.price_krw <= 0.05 for bp in body_prices):
            return False, f"price_mismatch product_id={p.id}"
    return True, None
```

[확정] — POLICY 임계 5% 명시.

---

## 7. 단정형·과장 (truth 게이트) — [관찰]

POLICY §3-1-5:

```python
ABSOLUTE_FORBIDDEN = [
    r'100% 효과',
    r'절대 안전',
    r'무조건 (\w+)',
    r'반드시 (낫는|치료|효과)',
    r'병이 (낫는|치료)',
    r'건강에 (좋다|특효)',
]

WARN_PATTERNS = [
    (r'확실히 (절약|효과|좋)', 'warn'),
    (r'(최고|최저|최상)의', 'warn'),
]
```

[관찰] — 일부 false positive 가능 (예: "병원 가서 낫는"). 컨텍스트 검사 필요.

---

## 8. Schema.org JSON-LD 검증 (schema 게이트) — [확정]

POLICY §4 필수 필드:

```python
ARTICLE_SCHEMA_REQUIRED = [
    '@context', '@type', 'headline', 'description', 'image',
    'datePublished', 'dateModified', 'author', 'publisher', 'mainEntityOfPage',
]

ITEMLIST_SCHEMA_REQUIRED = [
    '@context', '@type', 'itemListElement',
]

ITEM_PRODUCT_REQUIRED = [
    '@type', 'name', 'offers',  # offers.price + offers.priceCurrency
]

REVIEW_SCHEMA_CONDITIONS = {
    'requires_user_photo': True,
    'requires_first_person': True,
    'max_reviews_per_article': 1,
    'forbidden_author_type': 'Organization',  # Person만
}
```

[확정] — POLICY §4 명시 그대로.

---

## 9. 광고·게재 정책 위반 (links 게이트 보강) — [확정]

POLICY §12-1:

```python
FORBIDDEN_AD_PATTERNS = [
    r'<script[^>]+(popup|autoplay|hijack)',  # 자동 실행 광고 (E5)
    r'<iframe[^>]+style="[^"]*(top:|left:)[^"]*0',  # 화면 점거 광고
    r'<a[^>]+target="_self"[^>]+rel="(?!nofollow)',  # rel 누락
]

REL_REQUIRED_PATTERN = r'rel="[^"]*(nofollow.*sponsored|sponsored.*nofollow)'
# 모든 외부 상품 링크는 nofollow sponsored 둘 다 필수 (POLICY §6-3)
```

[확정] — POLICY §12·§6-3 그대로.

---

## 10. 본문 분량 / 구조 (선택 검사) — [추정]

```python
BODY_LENGTH_MIN = 1500  # 한국어 글자 수
BODY_LENGTH_MAX = 4000
SECTION_COUNT_EXPECTED = 6  # 8섹션 중 1·8은 자동 (SCENARIOS §5-1)
H2_HEADER_PATTERN = r'^## '
```

[추정] — 운영 후 KPI에 따라 조정.

---

## 11. 적용 패턴 사용 흐름 (BACKEND §2-3)

```python
def validate_draft(draft_id):
    payload = load_draft(draft_id)
    report = {
        'truth': check_truth(payload),
        'schema': check_schema(payload.schema_jsonld),
        'disclosure': check_disclosure(payload.body_md),
        'links': check_links(payload.body_md),
    }
    overall_pass = all(r['pass'] for r in report.values())
    save_validation_report(draft_id, report)
    return overall_pass, report
```

---

## 12. 갱신 주기

| 패턴 | 갱신 빈도 | 사유 |
|------|----------|------|
| 단축 URL 도메인 (§1) | 분기 1회 | 신규 단축 서비스 출현 |
| AI 흔적 패턴 (§4) | 월 1회 | Claude 모델 업데이트 시 출력 패턴 변동 |
| 1인칭 패턴 (§5) | 분기 1회 | 사용자 글 패턴 누적 후 보강 |
| Schema 필수 필드 (§8) | 연 1회 | Schema.org 표준 변동 |
| 단정형 (§7) | 운영 후 false positive 누적 시 | — |

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (12 카테고리·등급 엄격) | Claude Opus 4.7 |
