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

## 1인칭 표현 금지 (DECISIONS L3·L5 [확정 세션 #6])

본문 1인칭 표현 **일체 금지** (위키바이형 정보 분석 톤 강제):
- ❌ "내가 써본 결과", "우리집에서 사용", "3개월 사용해보니"
- ✅ "이 제품은 ~한 특징", "예산 30만원에서 추천", "페르소나 자취생에게 적합"
- 위반 시 validator/truth.py `first_person_forbidden` fail

## 관련 시나리오 (함께 보면 좋은)

{% for r in related_scenarios %}
- {{r.title_ko}} ({{r.slug}})
{% endfor %}

## non-commodity content 의무 (DECISIONS M1 [확정 세션 #6 Google AI Optimization])

일반 지식 reword 회피, 시나리오 페르소나×예산×시즌 결합 **고유 인사이트** 의무:
- ❌ "자취생 30만원 추천 7가지" (commodity, 어디나 있는 콘텐츠)
- ✅ "원룸 6평 자취생 30만원 — 신학기 2주 후 필요한 우선순위 vs 한 학기 사용 본 가성비 분배"
- Google "확장된 콘텐츠 악용 = 모든 검색 변형 별도 콘텐츠 = 스팸 정책 위반" [확정 Google 공식]

## 출력 요청

system 프롬프트의 §2 형식대로 META-JSON + BODY-MARKDOWN 두 블록 분리 출력.
본문 분량 약 2,000~2,500자 (한국어). 8섹션 모두 포함. 1인칭 금지 + non-commodity 의무.
