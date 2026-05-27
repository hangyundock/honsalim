# DB.md — 혼살림 데이터베이스 설계

> D:\affiliate_hub\ SQLite (로컬 콘텐츠) + Cloudflare D1 (클라우드 클릭 로그) 분리 설계서.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 SCENARIOS.md로 이어짐.
> 등급 표기: [확정] = 공식 1차 / [관찰] = 업계·사례 / [추정] = 본 세션 설계 / [확인 불가] = 검증 실패.
> 본 문서는 PLAN.md §9 · DECISIONS.md A~H · ARCH.md §2·§4·§7을 전제로 함.

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| SQLite 테이블 스키마 | 시나리오 콘텐츠 명세 → SCENARIOS.md |
| D1 클릭 로그 스키마 | 디자인·페이지 구조 → DESIGN·FRONTEND.md |
| 상태 머신 | 검증 게이트 규칙 → POLICY.md |
| 인덱스·성능 기본 | 일별 백업 절차 → BACKUP.md |
| 마이그레이션 전략 | 장애 대응 매뉴얼 → OPS.md |
| manifest JSON 구조 | 빌드 파이프라인 → ARCH·BACKEND.md |

---

## 2. SQLite vs D1 분리 원칙

### 2-1. 책임 분담

| DB | 위치 | 책임 | 영구성 |
|----|------|------|--------|
| **SQLite** (`data/honsalim.db`) | 로컬 D 드라이브 | 콘텐츠·메타·상태·승인 이력 — **source of truth** | 영구 (Git 외부, 별도 백업) |
| **Cloudflare D1** | 클라우드 | 클릭 로그·집계 — append-only 운영 통계 | 90일 회전 + 월 export |

### 2-2. 단방향 동기화

```
SQLite (source of truth)
   │
   ▼ 빌드 시 슬러그→딥링크 매핑 upsert
D1 (lookups + 클릭 로그)
   │
   ▼ 일별 집계
SQLite (집계 결과만 import, 원본 로그는 X)
```

**원칙** [추정]:
- D1은 **logs 저장소**. 콘텐츠 진실은 절대 D1에 없음.
- SQLite → D1: 빌드 단계에서 라우팅 정보(slug → 딥링크)만 upsert.
- D1 → SQLite: 일별 집계 결과(`clicks_daily`)만 import. 원본 클릭 로그는 D1에만.
- 양방향·실시간 동기 없음. 충돌·복잡도 0.

### 2-3. 왜 분리하는가

| 항목 | SQLite 단독 시 문제 | D1 분리로 해결 |
|------|---------------------|---------------|
| 클릭 기록 | Cloudflare Workers에서 D 드라이브 쓰기 불가 | D1 Workers binding 사용 |
| 쓰기 빈도 | 클릭 1건마다 SQLite write 불가능 (지리적·네트워크) | D1 edge write |
| 백업 단위 | 콘텐츠 + 로그 섞이면 백업 비대 | 콘텐츠만 깔끔히 백업 |

---

## 3. 테이블 전체 목록 (한 페이지)

### 3-1. SQLite 테이블 9개 + JSON 파일 1개

```
[SQLite] data/honsalim.db
┌─────────────────────────────────────────────────────────────┐
│  scenarios ──┬── articles ──── article_products ──── products
│              │     │                                  │
│              │     ├── article_personas ─── personas  │
│              │     ├── article_images ───── images    │
│              │     └── article_history (감사 로그)     │
│              │                                         │
│              └── drafts (작성 중, 상태 머신)             │
│                                                        │
│  clicks_daily (D1에서 일별 집계 import)                  │
│                                                        │
│  schema_version (마이그레이션 추적)                      │
└─────────────────────────────────────────────────────────────┘

[JSON 파일] data/manifest.json (테이블 아님, Git 추적)
   ├── articles[*].content_hash·depends_on·last_built
   ├── assets[*].hash
   └── templates[*].hash
```

### 3-2. Cloudflare D1 테이블 3개

```
[D1] honsalim-clicks DB
┌─────────────────────────────────────────────────────────────┐
│  slug_map ─── /go/<slug> → 쿠팡/알리 딥링크 매핑              │
│  clicks ───── 원본 클릭 로그 (append-only, 90일 회전)         │
│  clicks_daily ── 일별 집계 (SQLite로 export 후 D1에도 보관)   │
└─────────────────────────────────────────────────────────────┘
```

### 3-3. 관계 ER (단순화)

```
scenarios (1) ──< articles >── (M) products       (article_products 조인 테이블)
                     │
                     │──< article_personas >── personas
                     │
                     │──< article_images >── images
                     │
                     │── article_history (글 1편당 N개 변경 로그)

drafts (별도 흐름) → 승인 시 articles로 promotion
```

---

## 4. articles 테이블 (확정·발행 가능 상태만)

### 4-1. 컬럼 명세

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | — | 글 고유 ID |
| `slug` | TEXT UNIQUE | NO | — | URL slug (kebab-case, 한글 음차 또는 영문) |
| `scenario_id` | INTEGER | NO | — | scenarios.id FK |
| `title` | TEXT | NO | — | 제목 (한국어, 50~70자 권장) |
| `summary` | TEXT | NO | — | 요약 (한국어, 100~150자) |
| `body_md` | TEXT | NO | — | 본문 Markdown |
| `body_html` | TEXT | NO | — | 본문 HTML (빌드 직전 캐시) |
| `meta_description` | TEXT | NO | — | meta description (150자) |
| `meta_keywords` | TEXT | YES | NULL | SEO 키워드 쉼표 구분 |
| `schema_jsonld` | TEXT | NO | — | Schema.org JSON-LD 문자열 |
| `disclosure_first` | TEXT | NO | — | 공정위 첫머리 문구 (E1) |
| `status` | TEXT | NO | `'draft'` | `published` / `archived` / `unpublished` |
| `published_at` | TEXT (ISO 8601) | YES | NULL | 발행 시각 |
| `updated_at` | TEXT (ISO 8601) | NO | CURRENT_TIMESTAMP | 최종 수정 |
| `content_hash` | TEXT | NO | — | 본문 SHA256 (manifest 동기) |
| `truth_check_passed_at` | TEXT | NO | — | truth 게이트 통과 시각 |
| `user_approved_at` | TEXT | NO | — | 사용자 1클릭 승인 시각 |
| `user_approved_note` | TEXT | YES | NULL | 사용자 메모 (옵션) |
| `view_count_cached` | INTEGER | NO | 0 | clicks_daily 집계 캐시 |

### 4-2. 제약·트리거

- `slug` UNIQUE: 중복 URL 방지
- `status IN ('published','archived','unpublished')` CHECK
- `published_at IS NULL OR status = 'published'` CHECK (published 아니면 시각 없음)
- `updated_at` AFTER UPDATE 트리거 → 자동 갱신
- `truth_check_passed_at` AND `user_approved_at` 둘 다 NOT NULL이어야 INSERT 허용 (트리거 BEFORE INSERT)

### 4-3. 인덱스

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `idx_articles_slug` | `slug` | URL 라우팅 |
| `idx_articles_status_published_at` | `status`, `published_at DESC` | 목록 페이지 정렬 |
| `idx_articles_scenario_id` | `scenario_id` | 시나리오 허브 페이지 |
| `idx_articles_content_hash` | `content_hash` | manifest 동기 |

---

## 5. drafts 테이블 (작성 중·상태 머신 적용)

### 5-1. 컬럼 명세

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | — | draft 고유 ID |
| `scenario_id` | INTEGER | NO | — | scenarios.id FK |
| `working_title` | TEXT | YES | NULL | 작업 제목 (확정 전) |
| `status` | TEXT | NO | `'collected'` | §12 상태 머신 6단계 |
| `status_reason` | TEXT | YES | NULL | rejected 시 사유 등 |
| `raw_payload` | TEXT (JSON) | YES | NULL | 수집 원본 (collector 결과) |
| `enriched_payload` | TEXT (JSON) | YES | NULL | enricher 결과 (Claude 본문·메타) |
| `validation_report` | TEXT (JSON) | YES | NULL | validator 4단계 게이트 결과 |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | 생성 시각 |
| `updated_at` | TEXT | NO | CURRENT_TIMESTAMP | 최종 수정 |
| `promoted_article_id` | INTEGER | YES | NULL | 발행 시 articles.id 참조 |

### 5-2. 제약

- `status IN ('collected','enriched','validated','approved','published','rejected')` CHECK
- `promoted_article_id IS NULL OR status = 'published'` CHECK
- 상태 전이는 §12 머신 규칙 강제 (state_machine.py에서 검사 후 UPDATE)

### 5-3. 인덱스

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `idx_drafts_status` | `status` | 상태별 필터 (dashboard) |
| `idx_drafts_scenario_id` | `scenario_id` | 시나리오별 진행 현황 |
| `idx_drafts_created_at` | `created_at DESC` | 최근 작업 정렬 |

---

## 6. products 테이블 (쿠팡·알리 상품 정보)

### 6-1. 컬럼 명세

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | — | 상품 고유 ID |
| `source` | TEXT | NO | — | `coupang` / `aliexpress` |
| `source_product_id` | TEXT | NO | — | 외부 API의 상품 ID |
| `name` | TEXT | NO | — | 한국어 상품명 |
| `category_path` | TEXT | YES | NULL | "/가전/소형가전/공기청정기" 등 |
| `price_krw` | INTEGER | YES | NULL | 마지막 확인 가격 (원) |
| `price_checked_at` | TEXT | YES | NULL | 가격 확인 시각 |
| `currency` | TEXT | NO | `'KRW'` | 통화 |
| `image_url_external` | TEXT | YES | NULL | 외부 이미지 URL (DOWNLOAD 금지, 핫링크도 금지) |
| `deeplink_url` | TEXT | NO | — | 쿠팡 deep link 또는 알리 portals 링크 |
| `deeplink_slug` | TEXT UNIQUE | NO | — | `/go/<slug>` 자체 게이트웨이 슬러그 |
| `affiliate_tag` | TEXT | NO | — | 사용된 어필리에이트 태그 (감사용) |
| `availability` | TEXT | YES | NULL | `in_stock` / `out_of_stock` / `unknown` |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | 최초 등록 |
| `updated_at` | TEXT | NO | CURRENT_TIMESTAMP | 최종 갱신 |
| `last_seen_at` | TEXT | NO | CURRENT_TIMESTAMP | 마지막 API 응답 수신 |

### 6-2. 제약

- `(source, source_product_id)` UNIQUE: 동일 상품 중복 방지
- `source IN ('coupang','aliexpress')` CHECK
- `availability IN ('in_stock','out_of_stock','unknown')` CHECK
- `deeplink_slug` UNIQUE: `/go/` 라우팅 일대일

### 6-3. 인덱스

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `idx_products_source_product_id` | `source`, `source_product_id` | API 결과 매핑 |
| `idx_products_deeplink_slug` | `deeplink_slug` | D1 매핑 시 lookup |
| `idx_products_price_checked_at` | `price_checked_at` | 가격 갱신 큐 |

### 6-4. 이미지 정책 (DECISIONS D5·E5 관련)

- `image_url_external`은 **참조 메타데이터만**. 다운로드·재호스팅 금지 (저작권 회색지대).
- 글에 표시할 이미지는 별도 `images` 테이블 (§9): 쿠팡 공식 위젯 또는 사용자 직접 사진만.

---

## 7. scenarios 테이블 (시나리오 메타)

> 상세 시나리오 10개 명세는 **SCENARIOS.md**에서 확정. 본 절은 골격만.

### 7-1. 컬럼 명세

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | — | 시나리오 ID |
| `slug` | TEXT UNIQUE | NO | — | URL slug (예: `wonroom-cheot-jachi-30`) |
| `title_ko` | TEXT | NO | — | 시나리오 한국어 제목 |
| `description` | TEXT | NO | — | 설명 |
| `persona_id` | INTEGER | NO | — | personas.id FK (주 대상) |
| `budget_min_krw` | INTEGER | YES | NULL | 예산 하한 |
| `budget_max_krw` | INTEGER | YES | NULL | 예산 상한 |
| `season_peak` | TEXT | YES | NULL | "2-3월·8-9월" 등 |
| `priority` | INTEGER | NO | 0 | 발행 우선순위 |
| `active` | INTEGER | NO | 1 | 1=활성·0=비활성 |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | 등록 |

### 7-2. 인덱스

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `idx_scenarios_slug` | `slug` | 라우팅 |
| `idx_scenarios_persona_id` | `persona_id` | 페르소나 허브 |
| `idx_scenarios_priority_active` | `priority DESC`, `active` | 작업 큐 |

---

## 8. personas / 조인 테이블

### 8-1. personas 테이블

| 컬럼 | 타입 | NULL | 설명 |
|------|------|------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | 페르소나 ID |
| `slug` | TEXT UNIQUE | NO | `cheot-jachi` / `homeoffice` / `minimal-life` |
| `title_ko` | TEXT | NO | "새내기 자취생" 등 |
| `description` | TEXT | NO | 페르소나 설명 |
| `age_range` | TEXT | YES | "20대" 등 |
| `display_order` | INTEGER | NO 기본 0 | 표시 순서 |

초기 3개 (PLAN.md §4):
1. `cheot-jachi` — 새내기 자취생
2. `homeoffice` — 재택근무자
3. `minimal-life` — 1인 가구 정착자

### 8-2. article_products (조인 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `article_id` | INTEGER | articles.id FK |
| `product_id` | INTEGER | products.id FK |
| `display_order` | INTEGER | 글 내 노출 순서 |
| `recommendation_note` | TEXT | "예산 30만원에 가장 fit" 등 |
| PRIMARY KEY | (article_id, product_id) | — |

### 8-3. article_personas (조인 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `article_id` | INTEGER | articles.id FK |
| `persona_id` | INTEGER | personas.id FK |
| `relevance` | INTEGER | 1~5 점수 (옵션) |
| PRIMARY KEY | (article_id, persona_id) | — |

글 1편이 여러 페르소나에 걸칠 수 있음 (예: 자취생 + 1인 정착자 둘 다).

### 8-4. article_history (감사 로그)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | — |
| `article_id` | INTEGER | articles.id FK |
| `event_type` | TEXT | `created`·`updated`·`approved`·`unpublished`·`republished` |
| `actor` | TEXT | `user` / `claude` / `system` |
| `diff_summary` | TEXT | 변경 요약 (옵션) |
| `created_at` | TEXT | CURRENT_TIMESTAMP |

용도: 진실성 감사·롤백·법무 대응 시 변경 이력 추적.

---

## 9. images 테이블 (직접 사진·R2 경로·라이선스)

### 9-1. 컬럼 명세

| 컬럼 | 타입 | NULL | 설명 |
|------|------|------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | NO | 이미지 ID |
| `source_type` | TEXT | NO | `user_photo` / `coupang_widget` / `aliexpress_widget` |
| `local_path` | TEXT | YES | `static/photos/...` (Git 포함, user_photo만) |
| `r2_key` | TEXT | YES | `r2://honsalim-images/...` (옵션) |
| `widget_embed_html` | TEXT | YES | 쿠팡·알리 공식 위젯 임베드 코드 |
| `alt_text_ko` | TEXT | NO | 한국어 alt (접근성·SEO) |
| `width_px` | INTEGER | YES | width 속성 (CLS 방지, ARCH §7-5) |
| `height_px` | INTEGER | YES | height 속성 |
| `file_size_bytes` | INTEGER | YES | 최적화 추적 |
| `mime_type` | TEXT | YES | `image/webp` 권장 |
| `license_note` | TEXT | YES | "사용자 본인 촬영 2026-06-XX" 등 |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP |

### 9-2. 제약

- `source_type IN ('user_photo','coupang_widget','aliexpress_widget')` CHECK
- 외부 CDN 이미지 다운로드 → DB 저장 금지 (E5·D5 [확정]). 본 테이블에 진입 불가.

### 9-3. article_images 조인 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `article_id` | INTEGER | articles.id FK |
| `image_id` | INTEGER | images.id FK |
| `display_order` | INTEGER | 글 내 노출 순서 |
| `placement` | TEXT | `hero` / `inline` / `gallery` |
| PRIMARY KEY | (article_id, image_id) | — |

---

## 10. manifest (JSON 파일, 테이블 아님)

> ARCH.md §7-2에서 윤곽 제시. 본 절에서 스키마 확정.

### 10-1. 왜 JSON 파일인가 [추정]

- Git diff 가능 → 빌드 변경 검토·rollback 직관적
- 단일 파일이므로 빌드 시 한 번 로드·완료 시 한 번 저장 (트랜잭션 단순)
- 검토 시 비개발자도 텍스트 에디터로 열어 확인 가능
- SQLite에 들어가면 `sqlite3 .dump` 등 추가 도구 필요

### 10-2. 스키마

```
data/manifest.json
{
  "schema_version": 1,
  "last_full_build": "2026-06-XX T HH:MM:SS+09:00",
  "articles": {
    "<slug>": {
      "id": 142,
      "content_hash": "sha256:...",
      "depends_on": {
        "templates": ["article.html", "base.html", "partials/product_card.html"],
        "articles": ["recommended-related-1", "recommended-related-2"],
        "assets": ["css/main.css", "js/lazyload.js"]
      },
      "last_built": "2026-06-XX T HH:MM:SS+09:00",
      "output_paths": [
        "build/articles/<slug>/index.html"
      ]
    }
  },
  "assets": {
    "css/main.css": "sha256:...",
    "js/lazyload.js": "sha256:..."
  },
  "templates": {
    "article.html": "sha256:...",
    "base.html": "sha256:..."
  }
}
```

### 10-3. 증분 빌드 판정

ARCH.md §7-3에 5가지 재빌드 조건 명시. 본 manifest는 그 판정 자료.

---

## 11. clicks (Cloudflare D1)

### 11-1. D1 테이블 3개

#### slug_map (라우팅)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `slug` | TEXT PRIMARY KEY | `/go/<slug>` |
| `deeplink_url` | TEXT NOT NULL | 쿠팡·알리 deep link |
| `source` | TEXT NOT NULL | `coupang` / `aliexpress` |
| `product_id_local` | INTEGER | SQLite products.id 참조 (비강제 FK) |
| `updated_at` | TEXT NOT NULL | 빌드 시 upsert |

#### clicks (원본 로그, append-only)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | — |
| `slug` | TEXT NOT NULL | slug_map.slug |
| `ts` | TEXT NOT NULL | ISO 8601 |
| `ua_hash` | TEXT | UA SHA256 16자 (PII 회피) |
| `country` | TEXT | CF-IPCountry 헤더 |
| `referrer_domain` | TEXT | referrer 도메인만 (path X) |
| `bot_flag` | INTEGER | 0/1 (UA 기반 추정) |

회전: 90일 후 DELETE (월 1회 cron). 집계 결과만 보존.

#### clicks_daily (집계)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | TEXT | YYYY-MM-DD |
| `slug` | TEXT | — |
| `click_count` | INTEGER | — |
| `unique_ua_count` | INTEGER | ua_hash 기준 근사 unique |
| `top_country` | TEXT | — |
| PRIMARY KEY | (date, slug) | — |

### 11-2. SQLite ↔ D1 동기 흐름

```
[빌드 단계]
   articles + products → 매핑 추출 → D1 slug_map UPSERT

[일 1회 cron, 다음날 새벽]
   D1 clicks → GROUP BY (date, slug) → D1 clicks_daily INSERT
   D1 clicks_daily → SQLite clicks_daily import
   SQLite articles.view_count_cached 갱신

[월 1회]
   D1 clicks 90일 이상 DELETE
   D1 clicks_daily export → BACKUP.md 절차에 따라 백업
```

### 11-3. 개인정보 보호 (PIPA E2 관련) [추정]

- IP 주소 저장 금지. country만 헤더에서 추출.
- UA 원문 저장 금지. SHA256 16자 hash만.
- 정확한 처리 방침은 **POLICY.md** 개인정보처리방침에서 확정.

---

## 12. 상태 머신 (drafts.status)

### 12-1. 6 상태 전이도

```
                  ┌─────────────────────────────────┐
                  │                                 │
   collector      ▼     enricher       validator    │
 ─────────► collected ─────────► enriched ────┬─── pass ──┐
                  ▲                            │           │
                  │                            └─── fail ──┼──► rejected
                  │                                        │       │
                  │                                        ▼       │
                  │                                  validated      │
                  │                                        │       │
                  │                              사용자 1클릭      │
                  │                                        ▼       │
                  │                                   approved     │
                  │                                        │       │
                  │                              builder 발행       │
                  │                                        ▼       │
                  │                                  published     │
                  │                                                │
                  └────────────── 재수집 ─────────────────────────┘
```

### 12-2. 상태 정의

| 상태 | 의미 | 전이 가능 다음 상태 | 표시 |
|------|------|---------------------|------|
| `collected` | API 수집 완료, Claude 호출 전 | `enriched` | dashboard "수집됨" |
| `enriched` | Claude 본문·메타 완료, 검증 전 | `validated` / `rejected` | "가공됨" |
| `validated` | 4단계 검증 통과, 승인 대기 | `approved` / `rejected` | "검증 통과 → 승인 대기" |
| `approved` | 사용자 1클릭 승인, 빌드 대기 | `published` | "승인됨" |
| `published` | 빌드·배포 완료, articles 진입 | `rejected` (unpublish) | "발행됨" |
| `rejected` | 어느 단계든 실패·거부 | `collected` (재시도) | "거부됨 + 사유" |

### 12-3. 전이 규칙 강제 [추정]

`writer.state_machine.py`에서 다음 함수 패턴:

```
def transition(draft_id, to_status, reason=None):
    # 1. 현재 상태 SELECT
    # 2. 전이 매트릭스 lookup
    # 3. 허용되지 않으면 IllegalStateError
    # 4. 전이 시 BEFORE UPDATE 트리거 → article_history 인서트 (감사 로그)
    # 5. UPDATE drafts SET status = ?, status_reason = ?, updated_at = ?
```

**우회 금지**: `db.py` 레벨에서 raw UPDATE를 차단하는 트리거 두지는 않지만, code review·테스트로 강제. CLI는 `state_machine.transition()`만 호출.

### 12-4. 검증 fail 시 행동

- `rejected`로 전이 + `status_reason`에 4단계 게이트 중 실패 항목 명시
- dashboard 상단 표시
- 사용자가 사유 검토 후 `collected`로 reset 가능 (재시도)
- 30일 후 자동 archive (data/raw/ 이동 + DB 삭제) [추정, OPS.md 확정]

---

## 13. 인덱스 전략 (요약)

### 13-1. 모든 인덱스 한눈에

| 테이블 | 인덱스 | 컬럼 |
|--------|--------|------|
| `articles` | `idx_articles_slug` | `slug` |
| `articles` | `idx_articles_status_published_at` | `status`, `published_at DESC` |
| `articles` | `idx_articles_scenario_id` | `scenario_id` |
| `articles` | `idx_articles_content_hash` | `content_hash` |
| `drafts` | `idx_drafts_status` | `status` |
| `drafts` | `idx_drafts_scenario_id` | `scenario_id` |
| `drafts` | `idx_drafts_created_at` | `created_at DESC` |
| `products` | `idx_products_source_product_id` | `source`, `source_product_id` |
| `products` | `idx_products_deeplink_slug` | `deeplink_slug` |
| `products` | `idx_products_price_checked_at` | `price_checked_at` |
| `scenarios` | `idx_scenarios_slug` | `slug` |
| `scenarios` | `idx_scenarios_persona_id` | `persona_id` |
| `scenarios` | `idx_scenarios_priority_active` | `priority DESC`, `active` |
| `personas` | (UNIQUE on slug) | `slug` |

### 13-2. 인덱스 추가 기준 [추정]

- 글 수 < 1,000 이전: 위 인덱스로 충분. SQLite full scan도 ms 단위.
- 글 수 ≥ 5,000: `EXPLAIN QUERY PLAN`으로 slow query 분석 후 추가.
- 본 프로젝트 12개월 KPI = 100편 → 인덱스 추가 필요 가능성 낮음.

---

## 14. 마이그레이션 전략

### 14-1. 자체 SQL 파일 + schema_version (Alembic 미사용)

```
src/common/migrations/
├── 001_initial_schema.sql       ← 모든 CREATE TABLE
├── 002_add_article_history.sql  ← 후속 변경
├── 003_...
└── runner.py                    ← schema_version 비교 후 미적용 .sql 순차 실행
```

### 14-2. schema_version 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `version` | INTEGER PRIMARY KEY | 1부터 증가 |
| `applied_at` | TEXT | CURRENT_TIMESTAMP |
| `description` | TEXT | 마이그레이션 한 줄 설명 |

### 14-3. 적용 흐름

```
python -m honsalim db migrate
   └─ migrations/*.sql 글로브
   └─ schema_version에서 MAX(version) 조회
   └─ MAX+1 ~ latest까지 BEGIN ─ apply ─ COMMIT 순차 실행
   └─ 실패 시 ROLLBACK + 로그
```

### 14-4. dryRun

```
python -m honsalim db migrate --dry-run
   └─ 실행할 .sql 목록만 출력, 적용 X
```

CLAUDE.md §2.다 "dryRun(가능 시)" 만족.

### 14-5. Alembic 미선택 이유 [추정]

| 항목 | Alembic | 자체 SQL |
|------|---------|---------|
| 의존성 | SQLAlchemy + Alembic | sqlite3 표준만 |
| 학습 곡선 (비개발자 검토) | 높음 | 낮음 (.sql 직접 읽기) |
| 자동 생성 | 모델 diff 기반 | 수동 작성 |
| 본 프로젝트 변경 빈도 | 낮음 (월 0~1회) | 적합 |
| ORM 미사용과의 일관성 | 불일치 | 일치 |

---

## 15. 성능·백업 포인트

### 15-1. SQLite 운영 설정 [추정]

연결 시 적용 PRAGMA:

| PRAGMA | 값 | 효과 |
|--------|----|------|
| `journal_mode` | `WAL` | 동시 read/write 충돌 감소 |
| `synchronous` | `NORMAL` | 안전성 ↔ 성능 균형 |
| `foreign_keys` | `ON` | FK 제약 강제 |
| `temp_store` | `MEMORY` | 임시 정렬 빠름 |

### 15-2. VACUUM·ANALYZE 일정 [추정]

- `VACUUM`: 월 1회 새벽 cron (사용자 미사용 시간)
- `ANALYZE`: 마이그레이션 직후 + 글 수 100·500·1,000 도달 시
- 자동화는 OPS.md에서 확정

### 15-3. 백업 포인트

상세는 BACKUP.md. 본 절은 DB 관점만:

| 자산 | 백업 빈도 | 위치 |
|------|----------|------|
| `data/honsalim.db` | 일 1회 자동 | 외부 드라이브 + cloud (BACKUP.md) |
| `data/manifest.json` | Git (자동) | 저장소 |
| `data/raw/` | 불필요 (재수집 가능) | — |
| D1 `clicks` | 월 1회 export | BACKUP.md |
| D1 `clicks_daily` | 월 1회 export + SQLite import | 이중화 |

### 15-4. 크기 추정 [추정]

| 시점 | 글 수 | DB 크기 추정 |
|------|------|--------------|
| 3개월 | 30편 | ~5MB |
| 12개월 | 100편 | ~20MB |
| 24개월 | 200편 | ~50MB |

본문 평균 2,000자 + HTML 캐시 + 메타 기준. SQLite 한계(거의 무한)와 비교해 매우 여유.

---

## 16. 다음 단계

DB.md 사용자 검토 → 승인 후 **SCENARIOS.md (시나리오 10개 명세·확장)** 작성 진입.

SCENARIOS.md에서 확정할 핵심:
- 페르소나 3개 × 예산 구간 × 시즌 매트릭스
- 초기 시나리오 10편 (제목·예산·페르소나·시즌·우선순위)
- 확장 시나리오 패턴 (월 2~3편 추가 룰)
- 시나리오별 상품 카테고리·키워드·검색 의도
- SCENARIOS.md → scenarios·personas 테이블 시드 데이터 산출

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (SQLite 9테이블 + D1 3테이블 + manifest JSON) | Claude Opus 4.7 |
