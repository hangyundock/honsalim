# POLICY.md — 혼살림 정책·법무·진실성·보안

> 공정위 disclosure + truth/schema/disclosure/links 4단계 게이트 상세 규칙 + PIPA + 사업자 + 접근성 + 보안.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 OPS.md로 이어짐.
> 등급: [확정] / [관찰] / [추정] / [확인 불가].
> 전제: DECISIONS A·D·E·F·H + ARCH §6·§9 + BACKEND §2-3·§5 + DB §6·§9 + FRONTEND §5·§7.

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| 공정위 disclosure 정확 문구 | 일반 운영 절차 → OPS.md |
| truth/schema/disclosure/links 게이트 규칙 | 검증 코드 인터페이스 → BACKEND.md |
| AI 흔적 차단 패턴 | 백업·복구 → BACKUP.md |
| 1인칭 한국어 허용 조건 | 시나리오 콘텐츠 → SCENARIOS.md |
| 단축 URL 차단 목록 | 디자인 시스템 → DESIGN.md |
| PIPA 개인정보처리방침 골격 | 빌드·배포 → ARCH·BACKEND.md |
| 사업자 정보 footer 의무 | 사업자 등록 절차 → OPS.md |
| 접근성 검증 규칙 | 페이지 구조 → FRONTEND.md |
| 보안 정책 (secrets·deny 룰) | 보안 사고 대응 → OPS.md |

---

## 2. 공정위 disclosure (첫머리·푸터)

### 2-1. 의무 근거 [확정]

- 「표시·광고의 공정화에 관한 법률」 (공정위)
- 「추천·보증 등에 관한 표시·광고 심사지침」
- 위반 시 시정명령·과징금 + 쿠팡 측 수익 몰수 (E1 [확정])

### 2-2. 첫머리 disclosure 표준 문구

**한국어 단일** 한 줄 안내, 글 최상단:

```
이 글에는 쿠팡 파트너스 활동의 일환으로 일정 수수료를 제공받습니다.
(구매자에게 추가 비용은 발생하지 않습니다.)
```

배치 (FRONTEND §4-2 article.html):
- hero 위 또는 hero 직후
- `disclosure_banner` 컴포넌트
- 색: wood-100 배경 + wood-700 텍스트
- 닫기 버튼 X
- 모바일·데스크톱 동일 노출

### 2-3. 푸터 disclosure 풀 문구 (about·글 푸터)

```
혼살림은 쿠팡 파트너스 및 AliExpress Portals 어필리에이트 활동의 일환으로,
독자가 본 사이트의 추천 링크를 통해 상품을 구매할 경우 일정 수수료를 받습니다.
수수료는 구매자가 지불하는 가격에 추가되지 않으며, 본 사이트는 수수료 여부와
무관하게 추천 기준을 적용합니다. 본인 및 가족 구매 금지·자동 실행 광고 미사용
등 어필리에이트 정책을 준수합니다.
```

배치:
- 모든 글 푸터 (article.html)
- about.html 신뢰 섹션
- footer partial에는 "본 글에는 어필리에이트 링크 포함" 짧은 줄 + about 링크

### 2-4. 첫머리 disclosure 검증 (validator.disclosure)

| 검사 | 통과 조건 |
|------|----------|
| 첫머리 문구 존재 | 본문 첫 200자 안에 "쿠팡 파트너스" + "수수료" 키워드 모두 포함 |
| 푸터 풀 문구 존재 | 본문 마지막 800자 안에 "쿠팡 파트너스" + "AliExpress" + "본인 및 가족" 키워드 모두 포함 |
| 위치 정확성 | hero 직전·직후 중 한 곳에 `disclosure_banner` partial 호출 |
| 다른 글과 동일성 | 표준 문구 글자 변경 ≤ 3자 (오타 허용 범위만) |

fail 시: drafts.status='rejected' + reason="disclosure 누락 또는 변경: <상세>".

---

## 3. truth 게이트 — 진실성 검증

### 3-1. 30+ 검증 패턴

#### 3-1-1. 가격 정확성

| 검사 | 통과 조건 |
|------|----------|
| 본문 가격 = collector 가격 | 차이 ≤ 5% (변동 보호) |
| 가격 단위 명시 | "원" 또는 "₩" 표기 |
| 가격 변동 안내 | "{날짜} 기준" 문구 자동 삽입 |

#### 3-1-2. 재고·구매 가능성

| 검사 | 통과 조건 |
|------|----------|
| "재고 있음/없음" 본문 표현 | collector API 응답 일치 |
| "품절" "곧 출시" 부정확 표현 | 검출 시 fail (collector 응답 우선) |

#### 3-1-3. 1인칭·직접 경험

| 검사 | 통과 조건 |
|------|----------|
| 1인칭 표현 ("써본 결과"·"내가 사용"·"우리집에서") | 직접 사진 1+ 필수 |
| 직접 사진 없이 1인칭 사용 | fail (E7·E8 위반) |
| 특정 상품에 대한 강한 칭찬 ("최고"·"무조건") | 직접 사진 + 사용 기간 명시 필수 |

#### 3-1-4. AI 자동 생성 흔적 (E7 [확정])

| 패턴 (정규식) | 조치 |
|--------------|------|
| "본 글은 AI로 작성" / "ChatGPT로" | fail |
| "~로 알려져 있습니다" 반복 | warn (3회+ → fail) |
| "다음은 ~ 입니다:" 류 LLM 출력 패턴 | warn |
| "**\*\*\\$\\$**" 등 마크다운 깨짐 흔적 | fail |
| "I cannot" "As an AI" 영문 흔적 | fail |
| 동일 형용사 반복 ("훌륭한"·"완벽한") 5회+ | warn |
| 본문 3개 이상 단락에서 동일 문장 구조 | warn |

#### 3-1-5. 단정형 위험 표현 (의료·금융·법무 인접)

비YMYL 분야지만 단정형 회피 [추정]:

| 패턴 | 조치 |
|------|------|
| "100% 효과" "절대 안전" | fail |
| "병이 낫는다" "건강에 좋다" | fail (의료 단정형) |
| "확실히 절약된다" | warn |

#### 3-1-6. 가격 비교 정확성

| 검사 | 통과 조건 |
|------|----------|
| "쿠팡이 가장 저렴" 류 단정 | 비교 시점·근거 명시 또는 fail |
| "할인 50%" 등 수치 | 출처 시각 명시 |

#### 3-1-7. 한국어 1인칭 허용 범위 (E8 [확정])

영어 AutoBlog의 1인칭 금지 ↔ 한국 어필리에이트 정석 한국어 1인칭 허용. 단:

- 직접 사진 1+ 첨부 상품에 한정
- 사용 기간 ("3개월 사용"·"지난 겨울") 명시 권장
- 과장 ("내 인생 최고") 회피
- 본인 외 가족 사용 ("우리집 아이가") 신중 (의료·연령 민감)

### 3-2. truth 게이트 실행 흐름 (BACKEND §2-3)

```
def check_truth(payload):
    issues = []

    # 가격
    for product in payload.products:
        if abs(product.body_price - product.collected_price) / product.collected_price > 0.05:
            issues.append(("price_mismatch", product.id))

    # 1인칭 + 직접 사진
    first_person = re.search(r"써본|사용해본|내 원룸|우리집", payload.body)
    if first_person and not payload.has_user_photo:
        issues.append(("first_person_without_photo", first_person.group()))

    # AI 흔적
    for pattern in AI_PATTERNS:
        if re.search(pattern, payload.body):
            issues.append(("ai_pattern", pattern))

    # 단정형
    # ...

    return {"pass": len(issues) == 0, "issues": issues}
```

### 3-3. 사용자 직접 사진 메타 필수 (DB §9)

`images` 테이블 row 검증:
- `source_type = 'user_photo'`
- `license_note` 비어있지 않음
- `alt_text_ko` 비어있지 않음
- `width_px > 0` AND `height_px > 0`

이중 하나라도 누락 → 해당 사진 truth 게이트 가산점 0.

---

## 4. schema 게이트 — Schema.org JSON-LD 검증

### 4-1. Article Schema 필수 필드 (F5)

| 필드 | 의무 |
|------|------|
| `@context` = "https://schema.org" | 필수 |
| `@type` = "Article" | 필수 |
| `headline` | 필수, 110자 이내 |
| `description` | 필수 |
| `image` 배열 (1+ 항목) | 필수 |
| `datePublished` (ISO 8601) | 필수 |
| `dateModified` (ISO 8601) | 필수 |
| `author.@type` = "Person" 또는 "Organization" | 필수 |
| `publisher.@type` = "Organization" | 필수 |
| `publisher.logo.url` | 필수 |
| `mainEntityOfPage` | 필수 |

### 4-2. ItemList 필수 필드

| 필드 | 의무 |
|------|------|
| `@type` = "ItemList" | 필수 |
| `itemListElement` 배열 (1+ 항목) | 필수 |
| 각 항목 `position`, `item.@type=Product`, `item.name`, `item.offers.price`, `item.offers.priceCurrency` | 필수 |

### 4-3. Review Schema 엄격 조건 (F5 [확정])

다음 모두 충족 시에만:
- `validator.truth`에서 직접 사진·1인칭 둘 다 확인됨
- 글 1편당 Review schema 1개 이하
- `review.author` = "Person" + 운영자명 (Organization 금지)
- `review.itemReviewed.@type` = "Product"
- `review.reviewRating.ratingValue` 명시

위반 시: schema 게이트 fail.

### 4-4. BreadcrumbList 필수

모든 글·허브에 적용:
- 3+ 항목 (Home → 페르소나 → 시나리오 → 글 또는 ... → 시나리오 허브)
- `position` 정수 1부터
- `item` URL 유효

### 4-5. 게이트 fail 시 처리

- JSON-LD 파싱 실패 → fail
- 필수 필드 누락 → fail
- Review schema가 조건 미충족인데 출력 → fail
- 통과 시 빌드 단계에서 head에 자동 주입

---

## 5. disclosure 게이트

§2-4 동일. 단순 텍스트 매칭이므로 게이트 로직 작음.

추가 검사:
- 첫머리 disclosure가 글 본문 안 이미지나 다른 컴포넌트 사이에 끼지 않음 (즉시 가독)
- 푸터 풀 문구의 줄바꿈 보존
- "혼살림은" 운영자 표현 유지 (브랜드 이름 변경 자동 추적 트리거)

---

## 6. links 게이트 — 외부 단축 URL 차단 + 무결성

### 6-1. 단축 URL 차단 패턴 (D6 [확정])

본문 안에 다음 도메인 링크 존재 시 즉시 fail:

| 도메인 | 종류 |
|--------|------|
| `vivoldi.com` | 회색지대 단축 (D6 [확정] 차단) |
| `bit.ly` | 일반 단축 |
| `goo.gl` | 일반 단축 (서비스 종료지만 잔존 차단) |
| `tinyurl.com` | 일반 단축 |
| `t.co` | 트위터 |
| `bitly.com` | 일반 단축 |
| `rebrand.ly` | 일반 단축 |
| `ow.ly` | 일반 단축 |
| `is.gd` | 일반 단축 |
| `cutt.ly` | 일반 단축 |
| `me2.do` | 카카오 단축 |
| `n.kakao.com` | 카카오 단축 (DECISIONS K3 활성 — 세션 #5) |
| `naver.me` | 네이버 단축 (DECISIONS K3 추가 — 세션 #5) |

추가 룰:
- 도메인 길이 ≤ 7자 + 경로 매우 짧음 → 의심 (warn)
- 자체 게이트웨이 `honsalim.com/go/<slug>`만 허용
- 쿠팡 `link.coupang.com` `partners.coupang.com` 직접 허용

### 6-2. 링크 무결성 (HEAD 200)

| 검사 | 통과 조건 |
|------|----------|
| 본문 모든 외부 링크 HEAD 200 | timeout 5초, 재시도 1회 |
| /go/<slug> 게이트웨이 매핑 존재 | slug_map에 slug 등록됨 |
| 같은 글 내 동일 상품 링크 중복 ≤ 3회 | 광고 인상 회피 |

### 6-3. rel 속성 강제 (FRONTEND §3-2 product_card)

- 외부 상품 링크: `rel="nofollow sponsored"` 의무
- 누락 시 빌드 단계 fail (validator·post-render 검사 모두)

### 6-4. /go/ 링크 검증

- 모든 상품 카드의 CTA가 `/go/<slug>` 패턴인지 검사
- 직접 쿠팡 URL 본문 노출 차단 (보호 목적, 사용자가 실수로 비-게이트 URL 게시 방지)

---

## 7. 개인정보처리방침 (PIPA E2 [확정])

### 7-1. 의무 근거

- 「개인정보 보호법」 (PIPA)
- 위반 시 최대 2,000만원 [확정]
- about.html 또는 별도 `/privacy/` 페이지에 게재 의무

### 7-2. 본 사이트의 개인정보 수집·처리 범위 [추정]

| 항목 | 처리 여부 | 위치 |
|------|----------|------|
| IP 주소 | **미저장** (Cloudflare 캐시만 경유) | — |
| User-Agent | SHA-256 16자 hash만 (D1 clicks) | D1 |
| 국가 (CF-IPCountry) | 저장 | D1 |
| referrer | 도메인만 저장 (path X) | D1 |
| 이메일 | 미수집 (Phase 4까지) | — |
| 댓글 | 미사용 | — |

### 7-3. 처리방침 페이지 골격

```
혼살림 개인정보처리방침

1. 처리 목적
   본 사이트는 어필리에이트 클릭 통계 및 사이트 운영 통계 수집 목적으로
   최소한의 비식별 정보만 처리합니다.

2. 처리 항목
   - 비식별: 접속 국가, 브라우저 종류(해시), 유입 도메인
   - 미수집: 개인을 식별할 수 있는 정보 일체

3. 보유 기간
   - 원본 로그: 90일 (이후 자동 삭제)
   - 일별 집계: 12개월 (이후 자동 삭제)

4. 제3자 제공
   - Cloudflare (위탁 처리, 미국·한국 PoP)
   - 쿠팡 파트너스 (어필리에이트 링크 클릭 시 쿠팡으로 이동, 본 사이트는 클릭 정보를 쿠팡에 전달하지 않음)

5. 이용자 권리
   - 비식별 정보만 처리하므로 개별 열람·삭제 요청 적용 대상이 아니나,
     관련 문의는 아래 이메일로 접수받습니다.

6. 처리방침 변경
   - 변경 시 사이트 공지 + 본 페이지 갱신일자 변경

7. 운영 책임자
   - (사업자 등록 후 사업자 정보 게재)
   - 문의: <이메일>

본 방침은 YYYY-MM-DD부터 시행됩니다.
```

### 7-4. 위탁 처리 명시

Cloudflare는 데이터 처리 위탁자. 공식 DPA 링크 또는 위탁자 정보 명시 [추정, Phase 1 검토].

### 7-5. 사용자 권리 응답 절차

- 이메일 문의 접수 후 30일 이내 응답
- 본 사이트는 비식별 정보만 처리하므로 대부분 "처리 정보 없음" 응답

---

## 8. 사업자 정보 footer (E3 [확정])

### 8-1. 의무 근거

- 「정보통신망법」 + 「전자상거래법」
- 위반 시 최대 500만원 [확정]
- 사업자 등록 후 적용 (PLAN §9 D4: 월 10만원 누적 후)

### 8-2. 의무 표시 항목

| 항목 | 표시 위치 |
|------|----------|
| 상호 | footer |
| 대표자명 | footer |
| 사업자 등록번호 | footer |
| 통신판매업 신고번호 | footer (어필리에이트는 통판신고 필요) |
| 사업장 주소 | footer (자택 주소 비공개 옵션 → 비상주 사무실 또는 PO Box [추정]) |
| 전화번호 | footer (대표 또는 비공개 시 이메일만) |
| 이메일 | footer |
| 호스팅 사업자 (Cloudflare) | footer |

### 8-3. footer partial 변수

```
{# templates/partials/footer.html #}
{% if business_info %}
<dl class="business-info">
  <dt>상호</dt><dd>{{ business_info.name }}</dd>
  <dt>대표자</dt><dd>{{ business_info.ceo }}</dd>
  <dt>사업자등록번호</dt><dd>{{ business_info.tax_id }}</dd>
  ...
</dl>
{% else %}
<p class="business-info-pending">
  사업자 정보는 사업자 등록 완료 후 게재 예정입니다.
</p>
{% endif %}
```

### 8-4. 등록 전 임시 정책

- 사업자 등록 전에는 "개인 운영자, 사업자 등록 진행 중" 명시
- 이메일·운영자명만 표시
- 어필리에이트 활동 자체는 사업자 미등록 상태에서도 가능 (이론) [관찰]

---

## 9. 접근성 검증 규칙 (DESIGN §8 보강)

### 9-1. 빌드 단계 자동 검사

| 검사 | 기준 |
|------|------|
| 모든 `<img>` `alt` 속성 존재 | 빈 alt도 허용 안 함 (장식 이미지는 `alt=""` 의도) |
| `<a>` 텍스트 또는 aria-label 존재 | "여기" "more" 같은 빈약 텍스트 warn |
| `<h1>` 페이지당 1개 | 2개 이상 fail |
| 헤더 단계 skip 검사 | h1 → h3 점프 warn |
| `<button>` 또는 `<a role="button">` 텍스트 | 빈 button fail |
| `<form> <label>` 연결 | for-id 매칭 검사 |
| 색 대비 자동 (CSS 변수 기반) | wood-500 on wood-50 등 사전 계산 후 토큰 검증 |
| 키보드 포커스 outline 존재 | CSS 자동 검사 (outline: none + :focus-visible 보강 필요) |

### 9-2. 화면 외 요소

- skip-to-content 링크 존재 (header.html 첫 요소)
- 모바일 햄버거 메뉴 (Phase 4) 키보드 접근

### 9-3. WCAG 2.1 AA 목표 [추정]

- 본 시점 목표: AA 기본 충족
- AAA는 비목표 (콘텐츠 사이트에서 과도)

---

## 10. 보안 정책 (secrets·deny 룰)

### 10-1. secrets 격리 (ARCH §6 보강)

- 경로: `D:\secrets\affiliate_hub\` (절대 경로, 코드 저장소 외부)
- 백업: BACKUP.md에서 별도 절차 (외부 드라이브·암호화)
- 로딩: `common/config.py`에서만 (다른 모듈 직접 접근 금지)
- 로그 출력: redact 필터 (BACKEND §7-4)

### 10-2. `.claude/settings.json` deny 룰 (ARCH §6-3)

Phase 1 설정 [추정]:

```
{
  "permissions": {
    "deny": [
      "Bash(rm -rf D:\\\\secrets\\\\affiliate_hub\\\\*)",
      "Write(D:\\\\secrets\\\\affiliate_hub\\\\*)",
      "Edit(D:\\\\secrets\\\\affiliate_hub\\\\*)",
      "Read(D:\\\\secrets\\\\affiliate_hub\\\\*)",
      "Bash(git push*)",
      "Bash(wrangler pages deploy*)",
      "Bash(rm -rf D:\\\\affiliate_hub\\\\data\\\\honsalim.db)"
    ],
    "ask": [
      "Bash(git push*)",
      "Bash(wrangler*)",
      "Bash(curl*api.coupang*)",
      "Bash(curl*api.anthropic*)"
    ]
  }
}
```

### 10-3. Git 보안 (`.gitignore`)

```
# secrets·data·build·logs 절대 추적 금지
D:\\secrets\\           ← 외부지만 안전 차원
data/honsalim.db
data/raw/
data/manifest.json     ← 검토: Git 추적 vs 제외
build/
logs/
*.pickle
*.env
.env.local

# 빌드 산출물·임시
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
```

**manifest.json은 Git 추적 권장** [추정] — 빌드 일관성·diff·rollback 위해. 단, 데이터 영역(`data/`) 자체는 .gitignore.

### 10-4. CSP (Phase 4 검토)

- script-src 'self' + Cloudflare Analytics
- img-src 'self' + 쿠팡 위젯 도메인
- frame-src 쿠팡 위젯
- default-src 'self'

### 10-5. 의존성 보안 (Phase 4)

- `pip-audit` 또는 `safety` 월 1회
- GitHub Dependabot 활성 (공개 저장소)

---

## 11. 본인·가족 구매 금지 (E4 [확정])

### 11-1. 정책 명시

- 본인 또는 가족이 본 사이트 어필리에이트 링크로 구매 금지
- 부정행위 적발 시 쿠팡 계정 해지 위험 [확정]
- about.html 신뢰 섹션 명시

### 11-2. 운영자 자기 점검 [추정]

- 사용자 본인이 추천 상품 구매 시 쿠팡 다른 경로 (검색·직접) 사용
- 가족도 동일 안내

### 11-3. 위반 시

- 즉시 해당 클릭·수익 자진 반환 검토
- 사이트 측 자동 검출은 불가 (쿠팡 측 책임)

---

## 12. 광고·게재 정책 (E5·E6·E7)

### 12-1. 금지 행동

| 행동 | 근거 | 결과 |
|------|------|------|
| 자동 실행·납치 광고 | E5 ZDNet 2025-10-03 [확정] | 쿠팡 30일 수익 몰수 + 계정 해지 |
| 상표 키워드 PPC 광고 | E6 [확정] | AliExpress 영구 정지 |
| AI 100% 자동 게시 | E7 Google 2024-03 [확정] | Helpful Content 패널티 |
| 쿠팡 CDN 이미지 재호스팅 | DECISIONS [확정] | 저작권 회색지대 |
| 외부 단축 URL | D6 [확정] | 일괄 차단 위험 |

### 12-2. 광고 직접 노출 정책 (현재) [추정]

- 본 사이트는 광고 직접 게재 0 (Phase 6까지)
- 어필리에이트 텍스트·이미지 위젯만
- AdSense는 6개월 후 재결정 (D3 [확정])

### 12-3. 광고 게재 시 룰 (Phase 6+) [추정]

- 광고 영역 명시 ("광고" 라벨)
- CLS 영향 차단 (placeholder 박스)
- 상단 광고 0 (사용자 신뢰 우선)
- 본문 안 광고 최소 (1편당 1개 이하)

---

## 13. 인간 편집 게이트 — 자동 "승인" 금지 (CLAUDE.md §2.마)

### 13-0. 자동 "승인" vs 자동 "게시" 구분 (DECISIONS C6·C7 [확정])

| 단계 | 자동/수동 | 비고 |
|------|---------|------|
| 수집·가공·검증 | **자동** | collector·enricher·validator |
| **승인 (validated → approved)** | **수동 1클릭 (사용자만)** | E7 [확정]. 절대 자동화 금지 |
| 게시 (approved → published) + 빌드 + 배포 | **자동 (윈도우 스케줄러 매일 11:00 KST)** | 큐가 있을 때만, 큐 비면 자동 정지 |

**원칙**: AI는 "이 글이 충분히 좋다"고 판단할 수 없음. Google Helpful Content 알고리즘은 자동 발행 흔적을 학습 (E7 2024-03 16채널 47억뷰 종료 사례 [확정]). AdSense 신청 여부와 무관하게 어필리에이트 사이트도 검색 노출 의존이므로 패널티 영향 동일.

### 13-1. 원칙

- 자동 검증 4단계 통과 → 사용자 1클릭 승인 (수동) → 큐 진입 → 윈도우 스케줄러 자동 게시
- **자동 "승인" 절대 금지** (Google Helpful Content 회피)

### 13-2. 자동 승인이 발견되면

- BACKEND·dashboard 코드에 자동 승인 경로가 발견되면 즉시 차단
- 어떤 이유로도 우회 금지 (테스트·디버그 포함)
- `state_machine.transition()`에 `actor` 인자 의무 → `'user'`가 아닌 경우 `approved` 전이 거부

### 13-3. 검증 (BACKEND §2-4)

```
def transition(draft_id, to_status, reason=None, actor=None):
    if to_status == 'approved' and actor != 'user':
        raise IllegalStateError("approved 전이는 actor='user'만 가능")
    # published 전이는 'system'(스케줄러) 또는 'user' 모두 허용
    if to_status == 'published' and actor not in ('user','system'):
        raise IllegalStateError("published 전이는 user 또는 system만 가능")
    ...
```

### 13-4. 윈도우 스케줄러 게시 큐 (C6·C7)

- approved 글 큐: `drafts.status = 'approved'` ORDER BY user_approved_at ASC
- 매일 11:00 KST 스케줄러 작업: 큐의 첫 글 published 전이 + builder.build_incremental + deployer.deploy
- 큐 비면 즉시 종료 + dashboard 알림 (다음날 발행 0)
- 시즌 사전 발행 가능 (큐에 N편 채워두고 페이스 조절)

---

## 14-bis. 보안 종합 (DECISIONS I1~I7 [확정])

§10 기존 보안 정책에 더해 종합 정리.

### 14-bis-1. GitHub 보안 (I1)

**다중 방어**:
1. **`.gitignore` 엄격** — secrets·data·build·logs·.env·*.pickle 모두 제외 (§10-3)
2. **pre-commit hook** — 커밋 직전 자동 스캔:
   - `gitleaks` 또는 `detect-secrets` 둘 중 하나 (Phase 1에서 선택)
   - API 키·토큰·비밀번호 패턴 검출 시 commit 중단
   - 설치: `pip install pre-commit` + `.pre-commit-config.yaml` (Phase 1)
3. **GitHub Secret Scanning** — Repository Settings에서 활성 (공개 저장소 무료)
4. **Repository 보호** — main 브랜치 보호·force push 금지·관리자 외 push 차단
5. **CodeQL 활성 (I6)** — Actions에서 코드 정적 분석 자동
6. **분기 1회 수동 점검** — GitHub Code search로 본 저장소에서 `API_KEY`·`TOKEN`·`SECRET` 패턴 검출

### 14-bis-2. 보안 헤더 (I2)

`build/_headers` (Cloudflare Pages):

```
/*
  Content-Security-Policy: default-src 'self'; img-src 'self' https://*.coupangcdn.com https://ae01.alicdn.com; script-src 'self' https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-src https://link.coupang.com; connect-src 'self' https://cloudflareinsights.com
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
```

상세 도메인 화이트리스트는 Phase 4에서 확정 (CSP 너무 엄격하면 위젯 깨짐).

### 14-bis-3. 2FA 의무 (I3)

| 계정 | 2FA |
|------|-----|
| GitHub | TOTP 또는 보안 키 (FIDO2 권장) |
| Cloudflare | TOTP 의무 |
| Anthropic | TOTP |
| 쿠팡 파트너스 | SMS 또는 TOTP (제공 시) |
| 도메인 Registrar | TOTP (Cloudflare 통합 시 동일) |

복구 코드는 secrets 폴더 암호화 저장 (BACKUP §6).

### 14-bis-4. 의존성 보안 (I4)

- **GitHub Dependabot Alerts**: 공개 저장소 자동 활성 [확정 세션 #2]
- **pip-audit 자동 — 2단계** [확정 세션 #6]:
  - `lint.yml` step (continue-on-error) — PR/push 시 알림만, block X
  - `security.yml` cron 매월 1일 09:00 UTC — 전수 점검 + JSON artifact 90일 + GitHub Step Summary
- **npm audit (wrangler 빌드 시)**: 분기 1회
- 알림 시 우선순위 평가 후 패치 (MAINTENANCE §3) — `pyproject.toml` lower-bound 갱신 + `pip install -U` 사용자 명시 승인 후

### 14-bis-5. 로컬 보안 (I5)

- D 드라이브 BitLocker 활성 (Windows Pro)
- 로그인 비밀번호 강도 ≥ 12자 + 특수문자
- `D:\secrets\affiliate_hub\`는 BitLocker 외에도 NTFS 권한으로 본인 외 접근 차단
- Windows Defender 또는 동등 백신 활성

### 14-bis-6. Workers·D1·R2 접근 제한

- Workers `go_gateway.js`만 D1 binding 보유
- D1 직접 접근은 wrangler CLI (로컬 인증) 또는 Workers
- R2는 wrangler CLI + Cloudflare 인증

### 14-bis-7. 침해 사고 대응 (PIPA §14-3 보강)

| 단계 | 작업 |
|------|------|
| 1 | secrets 즉시 회전 (모든 키) |
| 2 | GitHub Repository 비공개 전환 (의심 시) |
| 3 | Cloudflare Pages 배포 일시 정지 |
| 4 | logs 분석으로 침해 범위 추정 |
| 5 | 사용자 데이터 침해 시 PIPA 통지 (72시간 내) |
| 6 | 복구 후 EVENTS.md 기록 + POLICY 갱신 |

---

## 14. 데이터 처리 절차 (PIPA 보강)

### 14-1. 클릭 로그 보관 주기

| 데이터 | 주기 |
|--------|------|
| D1 clicks (원본) | 90일 후 자동 DELETE |
| D1 clicks_daily (집계) | 12개월 후 자동 DELETE |
| SQLite clicks_daily import | 동일 12개월 |
| logs/honsalim.log | 90일 회전 |

### 14-2. 백업 (BACKUP.md 상세)

- 원본 DB는 일 1회 외부 드라이브 백업
- 로그·클릭은 백업 미대상 (재현 가능)

### 14-3. 침해 사고 대응 [추정, OPS.md 확정]

- 식별 정보 미수집이므로 통상 침해 대응 절차 비대상
- 단, 사이트 변조·해킹 사고 시 운영자 책임 → OPS.md

---

## 15. 다음 단계

POLICY.md 사용자 검토 → 승인 후 **OPS.md (운영·로깅·장애·자격증명 갱신)** 작성 진입.

OPS.md에서 확정할 핵심:
- 일·주·월·분기 운영 체크리스트
- 로그 회전 90일 + 50MB 자동화
- 장애 알림 채널 (STATE.md + 이메일?)
- 자격증명 만료 캘린더 (쿠팡 OAuth·GitHub PAT·Cloudflare API token)
- 데이터·코드 백업 스케줄
- 사이트 다운 시 대응 절차
- 사업자 등록 단계별 절차

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (4단계 게이트·PIPA·사업자·보안·금지 규칙) | Claude Opus 4.7 |
