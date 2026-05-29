# IMAGE_GENERATION.md — 혼살림 AI 이미지 생성 명세

> 출처: AutoBlog (`D:\autoblog\tistory_revival\ai_image_gen.py`) 패턴 이식 + 본 프로젝트 적용 — 세션 #6 [확정].
> 사용자 결정 (세션 #6): "사진 직접 촬영 없다. Google API로 AI 이미지 생성 사용."
> 본 문서: 도구·API·환경변수·프롬프트·법규·예산 — 다음 세션 자동 인식 의무.

---

## 1. 사용 도구 [확정]

| 항목 | 값 |
|------|----|
| **기본 모델** | `imagen-4.0-fast-generate-001` (Google **Imagen 4 Fast**) — 가성비 |
| **고품질 옵션** | `imagen-4.0-generate-001` (Imagen 4 Standard) |
| **대안** | `gemini-2.5-flash-image` (Nano Banana, generateContent 방식) |
| **API 종류** | Google Generative Language API (Gemini API) |

## 2. API 명세

### 2-1. Imagen 4 (predict)

```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:predict
Headers:
  x-goog-api-key: $GOOGLE_API_KEY
  Content-Type: application/json
Body:
  {
    "instances": [{"prompt": "<영어 프롬프트>"}],
    "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
  }
Response:
  {"predictions": [{"bytesBase64Encoded": "<base64>"}]}
```

### 2-2. Nano Banana (generateContent)

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent
Body:
  {"contents": [{"parts": [{"text": "<프롬프트>"}]}],
   "generationConfig": {"responseModalities": ["IMAGE"]}}
Response:
  candidates[].content.parts[].inlineData.data (base64)
```

## 3. 환경변수·secrets

- **`D:\secrets\honsalim.env`** [✅ 세션 #9 사용자 작성·결제 활성화]
  - `GOOGLE_API_KEY=<key>` — Google AI Studio 발급 (https://aistudio.google.com)
  - 보안상 secrets/ 바로 아래 단일 파일로 격리 (기존 `D:\secrets\affiliate_hub\*.env`와 분리, DECISIONS L6 #9 갱신)
  - 결제 활성화 필수 (무료티어 불가 [확정])
- `.gitignore`에 이미 `D:\secrets\` 외부 격리됨

## 4. 본 프로젝트 적용 모듈 [Phase 3 신설 예정]

| 모듈 | 책임 |
|------|------|
| `src/common/image_gen.py` | Google Imagen REST 호출 (AutoBlog 패턴 이식) |
| `src/enricher/image_prompt.py` | 시나리오·페르소나 → Imagen 프롬프트 빌더 |
| `src/builder/assets.py` | 생성 이미지 → `build/static/images/` 배치 + manifest 기록 |

### 4-1. 프롬프트 패턴 (페르소나별)

| 페르소나 | 프롬프트 키워드 (영어, Imagen 요구) |
|---------|-----------------------------------|
| 자취생 (jachisin) | "Korean small studio room interior, minimal warm tone, wood accent, soft lighting, no text" |
| 재택 (jaetaek) | "Korean home office desk setup, minimal warm tone, wood accent, soft natural light, no text" |
| 정착자 (jeongchakja) | "Korean cozy apartment living room, minimal warm tone, wood accent, soft lighting, no text" |

공통 후처리: `no text, no letters, no labels, no watermark anywhere` (AutoBlog 패턴).

### 4-2. aspect ratio

| 사용처 | 비율 |
|--------|------|
| 시나리오 hero | 16:9 |
| product card | 1:1 |
| persona hub | 4:3 |

## 5. 법규·정책 [확정]

| 항목 | 정합 |
|------|------|
| 상업적 사용 | OK (Google Imagen 약관 [관찰]) |
| 한국 표시광고법 AI 생성 명시 의무 | 없음 [확인 불가, 2026-05] |
| 본 프로젝트 명시 표기 | **footer에 "이미지는 AI 생성 일러스트레이션" 명시** (신뢰도·Google Helpful Content 안전 |
| 1인칭 표현 | **완전 차단** — AI 이미지로 "내가 써봤다" 게재 = 거짓 광고 (validator/truth.py L3 강화) |
| 인물 사진 | 자제 (한국 모델 키워드는 비용 효율 X — 미니멀 인테리어만) |
| 쿠팡 CDN 직접 다운로드 | 금지 (L2 유지, 저작권 회색지대) |
| 상품 이미지 | **쿠팡 공식 위젯** (Imagen 생성 X — 실제 제품 정확성) |

## 6. 예산 영향

| 시나리오 | 이미지 1장 | 1편당 6장 | 100편 | 월 |
|---------|-----------|----------|-------|------|
| Imagen 4 Fast | $0.02 | $0.12 | $12 | $24 ≈ 32,000원 [관찰 환율 1330] |

**PLAN §8 갱신 의무**: 월 ~16,000원 → ~48,000원 (Claude 5,000~15,000 + Imagen 32,000 + 도메인 1,300). 이는 1년 12개월 ≈ **576,000원 추가**.

## 7. 사용 흐름 (Phase 3+)

```
시나리오 enriched 완료
    ↓
enricher.image_prompt.build(scenario, persona)
    → "Korean small studio room interior, ..."
    ↓
common.image_gen.imagen4fast(prompt, aspect="16:9")
    → bytesBase64Encoded
    ↓
builder.assets.save(decoded_bytes, "scenarios/<slug>/hero.webp")
    ↓
manifest.json에 assets 등록
    ↓
Jinja2 템플릿 <img src="/static/images/scenarios/<slug>/hero.webp">
```

## 8. 회귀·테스트

- `tests/test_image_gen.py` (Phase 3 시점 신설)
- mock 패턴: `responses` 라이브러리 (이미 dev 의존)
- 실 호출은 `@pytest.mark.integration` (CI skip)

## 9. AutoBlog 참조 코드

본 프로젝트 구현 시 참조 의무 (DRY·검증된 패턴):

| 파일 | 본 프로젝트 매핑 |
|------|----------------|
| `D:\autoblog\tistory_revival\ai_image_gen.py` | `src/common/image_gen.py` 베이스 |
| `D:\autoblog\tistory_revival\image_prompt.py` | `src/enricher/image_prompt.py` 베이스 |
| `D:\autoblog\tistory_revival\image_fetcher.py` | Unsplash 폴백 (선택, 본 프로젝트 미정) |
| `D:\autoblog\tistory_revival\image_qa.py` | `src/validator/image_qa.py` (시각 검수, Phase 4+) |

## 10. AutoBlog vs 혼살림 차이

| 항목 | AutoBlog | 혼살림 |
|------|---------|-------|
| 사이트 | 티스토리 자동 블로그 (medical YMYL) | Cloudflare Pages 어필리에이트 (비YMYL) |
| 모델 | Imagen 4 Fast + Unsplash 폴백 | Imagen 4 Fast (폴백 미정) |
| 인물 | "한국 모델" 자동 부여 (블로그 시각성) | **인물 X**, 인테리어 분위기만 |
| 1인칭 | 허용 (블로그 톤) | **차단** (위키바이형 정보 분석) |
| 상품 이미지 | Imagen 생성 가능 | **쿠팡 공식 위젯만** (정확성·법규) |

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-28 (세션 #6) | 최초 작성 (AutoBlog 패턴 이식 + 본 프로젝트 적용 + L 카테고리 재변경 반영) | Claude Opus 4.7 |
