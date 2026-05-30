# meta_extract.md — META-JSON 분리 추출 프롬프트 (옵션, 실패 시 재시도용)

> 출처: BACKEND §3-3 + FRONTEND §5·§6 [확정]
> 사용: article_main.md 응답에서 META-JSON 파싱 실패 시 본 프롬프트로 재요청.

다음 본문에서 메타 정보만 추출하여 JSON으로 출력하세요.

본문:
```
{{body_md}}
```

라이프스타일 슬러그: {{persona.slug}}
세팅 슬러그: {{scenario.slug}}

## 출력 형식 (엄격)

```json
{
  "title": "본문 페이지 제목 (60자 이내·한국어)",
  "summary": "본문 1~2문장 요약 (100~150자·한국어)",
  "meta_description": "검색 결과용 메타 설명 (150자·한국어·핵심 키워드 1회 포함)",
  "meta_keywords": "쉼표 구분 5~8개 한국어 키워드",
  "faqs": [
    {"q": "질문 1", "a": "본문 기반 답변"},
    {"q": "질문 2", "a": "..."}
  ],
  "schema_recommended_review_eligible": [
    "직접 사진 있고 1인칭 사용된 상품의 slug 목록"
  ]
}
```

JSON 외 다른 텍스트 출력 금지.
