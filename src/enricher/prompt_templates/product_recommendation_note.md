# product_recommendation_note.md — product-card 코멘트 생성

> 출처: SCENARIOS §5-1 + FRONTEND §3-2 [확정]
> 사용: 본문 안 추천 상품 1개당 200~300자 코멘트 생성. 본문 생성에 자동 포함 또는 누락 보강.

다음 상품에 대한 추천 코멘트를 작성하세요.

상품: {{product.name}}
가격: {{product.price_krw}}원
카테고리: {{product.category_path}}
시나리오 페르소나: {{persona.title_ko}}
예산 fit: {{product.fit_reason}}
직접 사진 있음: {{has_user_photo}}  # true|false

## 작성 기준

- 분량: 200~300자 한국어
- 페르소나 톤 (SCENARIOS §3)
- 가격 대비 가치 명시
- 사용 시나리오 ("원룸 8평에서 …", "재택근무 8시간에 …")
- 1인칭 표현: **{{has_user_photo}}가 true인 경우에만 허용**
  - 예: "써본 결과 …", "내 원룸에서는 …", "지난 겨울 사용해보니 …"
  - false인 경우 객관 설명만 ("이 모델은 …", "사양은 …")
- 단점·주의사항 1개 이상 (가격·크기·소음·AS 등)

## 회피 (POLICY §3-1)

- "최고"·"무조건"·"100%" 등 과장
- "AS가 좋다고 알려져 있습니다" 등 출처 불명 단정
- 같은 형용사 반복 ("훌륭한"·"완벽한" 5회+)

## 출력

코멘트 텍스트만 (마크다운 헤더·JSON 없이). 한국어.
