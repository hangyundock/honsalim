# BACKEND.md — 혼살림 Python 모듈·API·빌드 파이프라인

> Python 모듈 8개 인터페이스 + Claude API 호출 패턴 + Cloudflare API + Workers `go_gateway` + 빌드 manifest 핸들링 + 에러 처리 + 테스트 전략.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 POLICY.md로 이어짐.
> 등급: [확정] / [관찰] / [추정] / [확인 불가].
> 전제: ARCH §3·§4·§7·§8 + DB §4~§12 + FRONTEND §2·§7·§8 + DECISIONS B·D·E·F·H.

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| 8개 모듈 인터페이스 | 검증 규칙 상세 → POLICY.md |
| Claude API 호출 패턴·캐시 | 디자인 토큰 → DESIGN.md |
| Cloudflare API·Workers 코드 골격 | 운영 절차·장애 대응 → OPS.md |
| 빌드 manifest 코드 흐름 | DB 스키마 → DB.md |
| 에러 처리·재시도·로깅 표준 | 페이지 템플릿 → FRONTEND.md |
| 테스트 전략 | 백업·복구 → BACKUP.md |
| CLI 11개 인터페이스 | 배포 일정·자동화 → SCHEDULE.md |

---

## 2. 모듈 8개 인터페이스 (각 모듈 책임·입출력·핵심 함수)

### 2-1. collector (수집)

**책임**: 쿠팡·알리 API에서 시나리오별 상품 후보 수집 → drafts 테이블에 1건 INSERT.

| 함수 (개념) | 입력 | 출력 |
|------------|------|------|
| `collect_scenario(scenario_id)` | scenarios.id | drafts.id (`status='collected'`) |
| `coupang.search(category, keyword, limit)` | 검색 조건 | products 후보 N개 dict |
| `coupang.get_deeplink(product_id)` | 상품 ID | deeplink URL |
| `scenario_loader.load_queue()` | (없음) | active=1 시나리오 list (priority DESC) |

**Phase 1**: 쿠팡만. 알리는 stub.
**API rate limit** [추정]: 호출 간 200ms 슬립 + 최대 60 RPM 가정. 실측 후 OPS.md 조정.

### 2-2. enricher (Claude API 본문 생성)

**책임**: drafts.raw_payload → Claude Haiku → 본문·요약·메타·Schema 생성 → drafts.enriched_payload 저장.

| 함수 | 입력 | 출력 |
|------|------|------|
| `enrich_draft(draft_id)` | drafts.id | drafts (`status='enriched'`) |
| `claude_client.generate(prompt, cache_key)` | prompt + cache_key | response.text |
| `prompt_templates.load(name)` | 템플릿 이름 | 프롬프트 본문 (.md) |
| `meta_extractor.extract(body_md)` | 본문 | title / summary / meta_desc / schema |

**프롬프트 외부화**: `src/enricher/prompt_templates/*.md` — 코드에 inline 금지, 텍스트 파일로 분리.

**캐시 전략** [추정]: Claude prompt caching 활용.
- system prompt + DECISIONS·POLICY 인용 (고정) → cache_breakpoint
- scenarios·products (가변) → cache 외
- 90% 이상 cache hit 기대 → 비용 절감

### 2-3. validator (4단계 게이트, ARCH §9)

**책임**: drafts.enriched_payload 검증 → pass/fail + 사유 → drafts.validation_report 저장.

| 모듈 | 함수 | 검증 |
|------|------|------|
| `truth.py` | `check_truth(payload)` | 가격·재고·1인칭·AI 흔적 |
| `schema.py` | `check_schema(jsonld)` | JSON-LD 파싱·필수 필드 |
| `disclosure.py` | `check_disclosure(body_md)` | 첫머리·푸터 문구 존재 |
| `links.py` | `check_links(body_md)` | 외부 단축 URL 0건 + HEAD 200 |

**진입점**: `validate_draft(draft_id)` → 4개 모두 호출 → 결과 합산 → `validated` / `rejected`.

**규칙 상세**는 POLICY.md. 본 모듈은 **호출자**.

### 2-4. writer (DB 쓰기·상태 머신)

**책임**: 모든 DB 쓰기를 중앙 집중. state_machine으로 상태 전이 강제.

| 함수 | 입력 | 출력 |
|------|------|------|
| `transition(draft_id, to_status, reason=None)` | id + 다음 상태 | 성공/IllegalStateError |
| `promote_to_article(draft_id, user_note=None)` | id + 메모 | articles.id |
| `archive_rejected(draft_id)` | id | (제거) — 30일 후 자동 (OPS.md) |

**중요**: SQL UPDATE 직접 호출 금지. 모든 상태 변경은 transition() 통과.

### 2-5. builder (Jinja2 빌더·manifest)

**책임**: DB articles → 정적 HTML 트리 출력 + sitemap·RSS·assets.

| 모듈 | 함수 | 비고 |
|------|------|------|
| `manifest.py` | `load()` `save()` `diff()` | data/manifest.json 핸들 |
| `renderer.py` | `render(template, ctx)` | Jinja2 환경 + 한국어 필터 |
| `pages.py` | `build_home()` `build_article(slug)` `build_lists()` `build_persona(slug)` `build_about()` | 페이지 5종 |
| `sitemap.py` | `build_sitemap()` `build_rss()` `notify_indexnow(urls)` | F4 IndexNow |
| `assets.py` | `process_images(dir)` `bundle_css()` `hash_files()` | webp·srcset·CSS minify |

**진입점**: `build_all()` 또는 `build_incremental(article_ids)`.

### 2-6. dashboard (로컬 미리보기·승인)

**책임**: pending drafts·validated drafts를 단일 HTML로 묶어 사용자에게 보여주고, 1클릭 승인 트리거.

| 함수 | 입력 | 출력 |
|------|------|------|
| `render_dashboard()` | (없음) | `data/dashboard/index.html` |
| `approve(draft_id, user_note=None)` | id | drafts 상태 `approved` + ` .approve/<id>.flag` 파일 생성 |

**1클릭 승인 패턴** [추정]:
- 대시보드 HTML에 `<form action="claude-cli://approve/<id>">` 표시 (실행 불가)
- 사용자는 옆에 표시된 명령 `python -m honsalim approve --draft <id>` 복사 실행
- 또는 사용자가 ID 알려주면 Claude가 명령 실행
- 별도 로컬 Flask 서버 없음 (단순화)

### 2-7. deployer (배포)

**책임**: build/ → GitHub push 또는 wrangler 직접 배포.

| 함수 | 입력 | 출력 |
|------|------|------|
| `git_push(commit_message)` | 메시지 | git push 결과 |
| `wrangler_deploy()` | (없음) | wrangler 결과 |
| `verify_deploy(url, expected_status=200)` | URL | bool |

**원칙**:
- 평상시 (수동 배포): git_push는 **사용자 명시 승인 후만** (H4 [확정])
- **자동 게시 (스케줄러)**: actor='system'으로 git_push 또는 wrangler_deploy 호출 가능. H4의 "사용자 명시 승인"은 **승인된 큐에 든 글의 발행**으로 간주 (DECISIONS C6 [확정]).
- 둘 다 자동 commit 메시지 포맷 H5 적용

### 2-7-bis. 스케줄러 모듈 (DECISIONS C6·C7 [확정], 신규)

**책임**: 윈도우 작업 스케줄러로 매일 11:00 KST 호출. 큐 1편 발행.

| 함수 | 입력 | 출력 |
|------|------|------|
| `scheduler.daily_publish()` | (없음) | 큐 1편 published + 빌드 + 배포 또는 큐 비면 정지 |
| `scheduler.queue_status()` | (없음) | approved 큐 N편 + 다음 발행 예정 |

**의사 흐름**:
```
def daily_publish():
    draft = SELECT * FROM drafts WHERE status='approved' ORDER BY user_approved_at ASC LIMIT 1
    if not draft:
        log.info("Queue empty, skip publish")
        dashboard.notify("큐 비었음")
        return
    writer.transition(draft.id, 'published', actor='system')
    article = writer.promote_to_article(draft.id)
    builder.build_incremental([article.id])
    deployer.deploy(method='git' if github_enabled else 'wrangler')
    sitemap.notify_indexnow([article.url])
    log.info(f"Auto-published draft_id={draft.id}")
```

**윈도우 작업 스케줄러 등록 (Phase 1·2)**:
- 트리거: 매일 11:00 KST
- 작업: `python -m honsalim scheduler-publish`
- 작업 디렉토리: `D:\affiliate_hub\`
- 실패 시: 재시도 0회 (다음날로)·로그·dashboard 알림

### 2-8. tracker (D1 클릭 집계)

**책임**: D1 clicks → 일별 집계 → SQLite clicks_daily import.

| 함수 | 입력 | 출력 |
|------|------|------|
| `d1_aggregator.aggregate(date)` | 날짜 | D1 clicks_daily INSERT |
| `d1_aggregator.export_to_sqlite()` | (없음) | SQLite articles.view_count_cached 갱신 |
| `report.weekly()` | (없음) | HTML 리포트 + dashboard 갱신 |

**실행 주기** [추정]: 일 1회 새벽 + 주 1회 리포트. OPS.md에서 확정.

---

## 3. Claude API 호출 패턴

### 3-1. 모델·매개변수

| 항목 | 값 |
|------|----|
| 모델 | `claude-haiku-4-5-20251001` (본문 생성) |
| 비상 (장문·복잡) | `claude-sonnet-4-6` (수동 fallback, BACKEND 코드에선 미사용) |
| max_tokens | 4096 (글 본문 충분) |
| temperature | 0.4 (창의성 ↓, 일관성 ↑) |
| 출력 형식 | Markdown + JSON 메타 분리 |

### 3-2. 프롬프트 구조 (캐시 친화)

```
[system, 캐시 대상]
  - 혼살림 운영 원칙·등급 표기·1인칭 정책
  - DECISIONS E·F 인용 (정책)
  - DESIGN §3 토큰 인용 (디자인 일관성)
  - 출력 포맷 명세 (Markdown + JSON 분리)

[user, 가변]
  - 시나리오 메타 (제목·예산·시즌·페르소나)
  - 수집된 products N개 (이름·가격·카테고리)
  - 사용자 직접 사진 메타 (alt·라이선스)
  - 요청: "위 데이터로 SCENARIOS §5-1 구조의 글 1편 작성"
```

### 3-3. 프롬프트 외부화 (`prompt_templates/`)

```
src/enricher/prompt_templates/
├── system_base.md                  ← 모든 호출 공통 system
├── article_main.md                 ← 본문 생성
├── meta_extract.md                 ← 메타·Schema 분리 추출
├── faq_generate.md                 ← FAQ 3~5개
├── product_recommendation_note.md  ← product-card 코멘트
└── tone_examples.md                ← 톤 예시 (1인칭 자연스럽게)
```

- 모두 .md 파일 (Git 추적·diff 가능)
- 코드에서 `prompt_templates.load(name)` 호출만

### 3-4. 캐시 활용 [추정]

Anthropic prompt caching:
- system_base + tone_examples + DECISIONS 인용 → cache_control breakpoint
- 90% 이상 hit 기대
- 캐시 TTL 5분이지만 enricher 배치 실행 시 연속 호출 → 캐시 유지

### 3-5. 에러 처리

| 에러 | 대응 |
|------|------|
| `RateLimitError` | 백오프 (1·2·4·8초) 후 재시도 3회 |
| `OverloadedError` | 백오프 10초 후 1회 재시도 |
| `APITimeoutError` | 큐 잔류 + 다음 실행 재시도 |
| `APIError 기타` | 로그 + 큐 잔류 |
| `BadRequestError` | 즉시 fail + STATE.md 알림 (프롬프트 오류 가능성) |

### 3-6. 비용 추적 [추정]

- 각 호출 후 `usage.input_tokens` / `usage.output_tokens` 로그
- 월별 집계 → STATE.md "수익" 옆에 "API 비용" 표기 (Phase 4 이후)
- PLAN §8 예산 (월 5~15천원) 초과 시 알림

---

## 4. Cloudflare API 호출 패턴

### 4-1. 4개 서비스 인터페이스

| 서비스 | API 종류 | 본 프로젝트 호출 |
|--------|---------|----------------|
| Pages | wrangler CLI | `wrangler pages deploy build/` |
| R2 | wrangler CLI 또는 S3-compatible API | 이미지 업로드 (Phase 4 검토) |
| D1 | wrangler d1 / REST API | slug_map upsert·집계 쿼리 |
| Workers | wrangler deploy | `go_gateway.js` 배포 |

### 4-2. wrangler 호환 방식

본 프로젝트는 **wrangler CLI 호출**을 기본으로 함 [추정]:
- 직접 REST API 사용보다 표준화·인증 단순
- subprocess로 호출
- `wrangler login` 1회 후 토큰 자동 사용

### 4-3. D1 매핑 upsert (빌드 시)

```
빌드 단계 마지막에:
  for product in published_products:
      wrangler d1 execute honsalim-clicks --command "
        INSERT INTO slug_map (slug, deeplink_url, source, product_id_local, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
          deeplink_url = excluded.deeplink_url,
          updated_at = excluded.updated_at
      "
```

배치 처리 (한 번에 100건씩) [추정].

### 4-4. D1 일별 집계

```
일 1회 새벽:
  wrangler d1 execute --command "
    INSERT OR REPLACE INTO clicks_daily (date, slug, click_count, ...)
    SELECT date(ts), slug, COUNT(*), ...
    FROM clicks
    WHERE date(ts) = date('now', '-1 day')
    GROUP BY date(ts), slug
  "

  wrangler d1 export → SQLite import
  SQLite articles.view_count_cached 갱신
```

### 4-5. R2 사용 (Phase 4 이후 [추정])

- 초기에는 `static/images/` Pages 정적 자산만 (10GB 무료)
- 글 수 100편 이상 + 이미지 누적 시 R2 분리 검토
- BACKUP.md에서 백업 절차 명시

---

## 5. Workers `go_gateway.js` 구현 골격

### 5-1. 라우트 설정 (wrangler.toml)

```
name = "honsalim-go-gateway"
main = "src/workers/go_gateway.js"
compatibility_date = "2026-01-01"

[[routes]]
pattern = "honsalim.com/go/*"
zone_name = "honsalim.com"

[[d1_databases]]
binding = "DB"
database_name = "honsalim-clicks"
database_id = "<from cloudflare.env>"
```

### 5-2. Worker 로직 (의사 코드)

```
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const slug = url.pathname.split('/go/')[1];

    if (!slug) return Response.redirect('https://honsalim.com/', 302);

    // 1. slug_map lookup (D1)
    const row = await env.DB
      .prepare("SELECT deeplink_url FROM slug_map WHERE slug = ?")
      .bind(slug)
      .first();

    if (!row) return Response.redirect('https://honsalim.com/', 302);

    // 2. 클릭 로그 (비동기, await X — 즉시 리다이렉트)
    const ua_hash = await hashUA(request.headers.get('User-Agent') || '');
    const country = request.headers.get('CF-IPCountry') || '';
    const referrer = sanitizeReferrer(request.headers.get('Referer') || '');
    const bot_flag = detectBot(request.headers.get('User-Agent') || '') ? 1 : 0;

    ctx.waitUntil(
      env.DB.prepare(`
        INSERT INTO clicks (slug, ts, ua_hash, country, referrer_domain, bot_flag)
        VALUES (?, datetime('now'), ?, ?, ?, ?)
      `).bind(slug, ua_hash, country, referrer, bot_flag).run()
    );

    // 3. 302 Redirect
    return Response.redirect(row.deeplink_url, 302);
  }
}

async function hashUA(ua) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ua));
  return Array.from(new Uint8Array(buf)).slice(0, 8)
    .map(b => b.toString(16).padStart(2, '0')).join('');
}

function sanitizeReferrer(ref) {
  try { return new URL(ref).hostname; } catch { return ''; }
}

function detectBot(ua) {
  return /bot|crawl|spider|slurp|preview/i.test(ua);
}
```

### 5-3. 보안·운영

- 미등록 slug → 홈 302 (404 X, 봇 학습 차단)
- IP 미저장 (PIPA 회피)
- UA 원문 미저장 (SHA256 16자만)
- referrer는 도메인만
- bot UA는 어필리에이트 호출 차감 위험 → 같은 redirect 하지만 D1에 bot_flag=1 기록 (분석용)

### 5-4. 배포

```
wrangler deploy
```

Phase 1에 배포 후 빌드 시마다 slug_map upsert로 자동 갱신.

---

## 6. 빌드 manifest 코드 흐름 (ARCH §7 구체화)

### 6-1. 빌드 명령 진입

```
$ python -m honsalim build [--full | --incremental]

  1. manifest = load("data/manifest.json")
  2. db_articles = SELECT * FROM articles WHERE status='published'
  3. db_assets = scan(static/, templates/) → hash 계산
  4. needs_rebuild = manifest.diff(db_articles, db_assets, db_templates)
  5. if --full: rebuild_all = True
  6. for article in needs_rebuild:
       render_article(article)
       update manifest[slug]
  7. 항상 재생성:
     render_home()
     render_lists()
     render_persona_hubs()
     render_about()
     render_sitemap()
     render_rss()
  8. process_assets()  ← webp·CSS hash·minify
  9. save manifest → "data/manifest.json"
  10. notify_indexnow(changed_urls)
```

### 6-2. diff 알고리즘 [추정]

```
def diff(self, db_articles, db_assets, db_templates):
    changed = set()
    for a in db_articles:
        m = self.articles.get(a.slug)
        if not m:
            changed.add(a.id); continue              # 신규
        if m['content_hash'] != a.content_hash:
            changed.add(a.id); continue              # 본문 변경
        for tpl in m['depends_on']['templates']:
            if self.templates[tpl] != db_templates[tpl]:
                changed.add(a.id); break              # 템플릿 변경
        for asset in m['depends_on']['assets']:
            if self.assets[asset] != db_assets[asset]:
                changed.add(a.id); break              # asset 변경
        for ref in m['depends_on']['articles']:
            if ref in changed:
                changed.add(a.id); break              # 인용 글 변경
    return [a for a in db_articles if a.id in changed]
```

### 6-3. depends_on 자동 추출 [추정]

Jinja2 렌더 시 `{% include %}` `{% from ... import %}` `<img src="...">` `<a href="/articles/...">` 추적:
- 렌더 wrapping 환경에서 호출된 템플릿·매크로·자산 기록
- 본문 안 다른 글 슬러그 정규식 검출
- 빌드 후 manifest에 depends_on 저장

복잡도 높으므로 1차 구현은 단순 "모든 글이 base.html + 페이지 템플릿 + 컴포넌트 5종 의존"으로 일괄 처리 → 후속 최적화 (MAINTENANCE.md).

---

## 7. 에러 처리·재시도·로깅 표준

### 7-1. 로깅 포맷

```
[YYYY-MM-DD HH:MM:SS.fff TZ] [모듈명] [LEVEL] 메시지 ctx=...

예:
[2026-06-15 10:23:45.123 KST] [enricher.claude_client] INFO Article enriched draft_id=142 input_tokens=2340 output_tokens=890
[2026-06-15 10:23:46.001 KST] [validator.truth] WARN Direct photo missing draft_id=142 — fail truth gate
```

### 7-2. 레벨 기준

| 레벨 | 사용 |
|------|------|
| DEBUG | 임시·개발 (CI에선 off) |
| INFO | 정상 진행 (수집 N건·생성 1편·배포 완료) |
| WARN | 회복 가능 (단일 게이트 fail·재시도 성공) |
| ERROR | 회복 불가 (배포 실패·API 다운) |

### 7-3. 재시도 정책 [추정]

| 작업 | 재시도 | 백오프 |
|------|--------|--------|
| Claude API | 3회 | 1·2·4초 + jitter |
| 쿠팡 API | 3회 | 0.5·1·2초 |
| wrangler 배포 | 2회 | 5·15초 |
| IndexNow 통보 | 1회 | 즉시 |
| 외부 링크 HEAD | 2회 | 1초 |

### 7-4. 보안 로그 룰

- secrets 키·토큰 절대 로그 출력 금지
- `common/logging.py`에 redact 필터 적용
- 사용자 메모는 로그 출력 가능 (개인정보 없는 가정)

### 7-5. 에러 알림 [추정, OPS.md 확정]

| 조건 | 알림 |
|------|------|
| validator fail 24h 3건+ | dashboard 상단 빨간 배너 |
| 배포 실패 | STATE.md "장애" 섹션 자동 갱신 |
| API 키 만료 D-7 | STATE.md "자격증명 만료" 알림 |
| 빌드 5분 이상 지속 | warn 로그 |

---

## 8. 테스트 전략

### 8-1. 핵심 회귀 테스트 (validator 최우선)

`tests/test_validator.py`:
- truth 게이트 30+ 케이스 (1인칭 패턴·가격 변동·재고)
- schema 유효성 (10+ 케이스)
- disclosure 첫머리 누락·오타
- links 단축 URL 패턴 (vivoldi·bit.ly·...)

**규칙**: validator 변경 시 회귀 테스트 100% 통과 필수.

### 8-2. 빌더 테스트

`tests/test_builder.py`:
- manifest diff 알고리즘 (신규·변경·삭제)
- Jinja2 렌더 fixture (글 1편 ↔ 출력 HTML 일치)
- sitemap·RSS XML 유효성

### 8-3. fixture 패턴

`tests/fixtures/`:
- `sample_article.json` — drafts·articles 샘플
- `sample_products.json` — 쿠팡 응답 모킹
- `sample_html_outputs/` — 기대 출력

### 8-4. 외부 API 모킹

- 쿠팡·Claude API는 `responses` 라이브러리로 모킹 [추정]
- CI에서 실 호출 0건 (비용·rate limit 보호)
- 실 API 호출 테스트는 manual `pytest -m integration`

### 8-5. CI 통합 (Phase 2)

`.github/workflows/lint.yml`:
- pre-commit hook (black·ruff·mypy)
- pytest 전체

`.github/workflows/build.yml` (ARCH §8-2):
- lint + test + build + deploy

### 8-6. 테스트 커버리지 목표 [추정]

- validator: ≥ 90% (가장 중요)
- builder.manifest: ≥ 80%
- collector·enricher: ≥ 50% (외부 API 의존 모킹 한계)
- 전체: ≥ 70%

---

## 9. CLI 명령 11개 인터페이스 명세

ARCH §4-3에서 정의한 CLI 명령들의 상세 인터페이스.

| 명령 | 인자 | 출력 |
|------|------|------|
| `collect <scenario_slug>` | 시나리오 슬러그 | drafts.id 생성·INFO 로그 |
| `enrich [--draft <id>] [--all-collected]` | draft ID 또는 일괄 | drafts (`status='enriched'`) |
| `validate [--draft <id>] [--all-enriched]` | 동일 | drafts (`status='validated'/'rejected'`) |
| `dashboard` | — | `data/dashboard/index.html` 갱신·열기 |
| `approve --draft <id> [--note <text>]` | 승인 | drafts (`status='approved'`) |
| `unapprove --draft <id>` | 취소 | drafts → `validated` 회귀 |
| `build [--full] [--incremental]` | 모드 | build/ 갱신·manifest 저장 |
| `deploy [--method git|wrangler]` | 방법 | git push 또는 wrangler 결과 |
| `scheduler-publish` | (없음) | 큐 1편 자동 발행 (스케줄러 호출용) |
| `scheduler-status` | (없음) | 큐 N편 + 다음 발행 예정 |
| `report --weekly|--monthly` | 주기 | HTML 리포트 + dashboard |
| `doctor` | — | secrets·DB·외부 API 헬스 체크 |
| `db migrate [--dry-run]` | 옵션 | 마이그레이션 실행·dryRun |

### 9-1. 공통 옵션

| 옵션 | 의미 |
|------|------|
| `--verbose` | DEBUG 로그 활성 |
| `--quiet` | WARN 이상만 |
| `--json` | 결과를 JSON으로 (스크립트 가능) |
| `--dry-run` | 실제 변경 없이 계획만 출력 |

### 9-2. exit code 표준

- 0: 성공
- 1: 사용자 에러 (잘못된 인자)
- 2: 데이터 에러 (DB·secrets 누락)
- 3: 외부 API 에러
- 4: 검증 fail (validator)
- 10+: 예기치 못한 예외

CI·자동화에서 exit code로 분기.

---

## 10. 의존성 관리 (`pyproject.toml`) [추정]

### 10-1. 1차 의존성

| 패키지 | 버전 핀 (Phase 2 확정) | 용도 |
|--------|----------------------|------|
| anthropic | >=0.50 | Claude API |
| jinja2 | >=3.1 | 템플릿 |
| requests | >=2.31 | HTTP |
| python-dotenv | >=1.0 | secrets |
| pyyaml | >=6.0 | 설정·메타 |
| markdown | >=3.5 | Markdown 렌더 |
| pillow | >=10.0 | 이미지 |
| pytest | >=8.0 | 테스트 |

### 10-2. 개발 의존성

| 패키지 | 용도 |
|--------|------|
| black | 포맷 |
| ruff | 린트 |
| mypy | 타입 |
| responses | API 모킹 |
| pre-commit | hook 프레임워크 |
| gitleaks 또는 detect-secrets | **secrets 누설 차단 (POLICY §14-bis-1 [I1])** |
| pip-audit | 의존성 보안 (I4) |

### 10-3. lockfile [추정]

`requirements.lock` 또는 `uv.lock` (Phase 2 결정).
- Actions에서 동일 환경 보장 (ARCH §12-4)

---

## 11. 환경 변수 표준

### 11-1. 12 Factor 원칙 적용 [추정]

모든 설정값은 secrets/*.env에서 읽음. 코드에 하드코딩 금지.

| 환경 변수 | 출처 | 용도 |
|-----------|------|------|
| `ANTHROPIC_API_KEY` | claude.env | Claude API |
| `COUPANG_ACCESS_KEY` | coupang.env | 쿠팡 |
| `COUPANG_SECRET_KEY` | coupang.env | 쿠팡 |
| `COUPANG_TAG_ID` | coupang.env | 어필리에이트 태그 |
| `CF_API_TOKEN` | cloudflare.env | wrangler |
| `CF_ACCOUNT_ID` | cloudflare.env | wrangler |
| `D1_DATABASE_ID` | cloudflare.env | D1 |
| `R2_BUCKET` | cloudflare.env | R2 (옵션) |
| `INDEXNOW_KEY` | cloudflare.env | F4 |
| `GSC_TOKEN` | cloudflare.env | F1 |
| `NAVER_TOKEN` | cloudflare.env | F2 |
| `GH_PAT` | github.env | GitHub push (선택) |
| `SITE_BASE_URL` | (코드 기본값) | https://honsalim.com |
| `LOG_LEVEL` | (코드 기본 INFO) | 디버그 시 DEBUG |

### 11-2. 누락 시 fail-fast (config.py)

```
필수 키 누락 → 즉시 SystemExit + 어떤 키 누락인지 로그
(secrets 값은 절대 로그 출력 X)
```

---

## 12. 다음 단계

BACKEND.md 사용자 검토 → 승인 후 **POLICY.md (공정위·진실성·보안·정책 검증 규칙)** 작성 진입.

POLICY.md에서 확정할 핵심:
- 공정위 disclosure 정확 문구 (첫머리·푸터)
- 진실성 검증 규칙 30+ 패턴
- AI 자동 생성 흔적 차단 규칙
- 1인칭 한국어 허용 조건 (직접 사진 필수)
- 외부 단축 URL 차단 패턴 목록
- 개인정보처리방침 의무 (PIPA E2)
- 사업자 정보 footer 의무 (E3)
- 접근성 검증 규칙
- 보안 정책 (secrets·deny 룰)

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (모듈 8개 + Claude/CF API + Workers + manifest + 테스트) | Claude Opus 4.7 |
