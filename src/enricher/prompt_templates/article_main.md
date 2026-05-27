# article_main.md — 본문 1편 생성 user 프롬프트 템플릿

> 출처: BACKEND §3-3 + SCENARIOS §5 [확정]
> 변수: {{scenario}}, {{products}}, {{personas}}, {{photos}}, {{related_scenarios}}
> 본 파일은 enricher 호출 시 변수 치환 후 user 메시지로 전송.

다음 시나리오의 본문을 system 프롬프트의 형식으로 작성하세요.

## 시나리오 메타

- 슬러그: {{scenario.slug}}
- 제목 후보: {{scenario.title_ko}}
- 페르소나: {{scenario.persona.title_ko}} ({{scenario.persona.slug}})
- 예산: {{scenario.budget_min_krw}}원 ~ {{scenario.budget_max_krw}}원
- 시즌: {{scenario.season_peak}}
- 검색 키워드: {{scenario.keywords}}

## 페르소나 상세

{{persona.title_ko}}: {{persona.description}}
연령: {{persona.age_range}}

## 수집된 상품 (collector 결과)

{% for p in products %}
### 상품 {{loop.index}}: {{p.name}}
- 카테고리: {{p.category_path}}
- 가격: {{p.price_krw}}원 (확인 시각: {{p.price_checked_at}})
- 재고: {{p.availability}}
- 카테고리 fit 이유: {{p.fit_reason}}
{% endfor %}

## 사용자 직접 사진 (직접 경험 1인칭 허용 상품)

{% for photo in photos %}
- 상품 슬러그: {{photo.product_slug}}
- 사진 alt: {{photo.alt_text_ko}}
- 라이선스: {{photo.license_note}}
{% endfor %}

위 사진 있는 상품에 한해 1인칭 표현 사용 가능. 다른 상품은 객관 설명만.

## 관련 시나리오 (함께 보면 좋은)

{% for r in related_scenarios %}
- {{r.title_ko}} ({{r.slug}})
{% endfor %}

## 출력 요청

system 프롬프트의 §2 형식대로 META-JSON + BODY-MARKDOWN 두 블록 분리 출력.
본문 분량 약 2,000~2,500자 (한국어). 8섹션 모두 포함.
