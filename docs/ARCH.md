# ARCH.md — 혼살림 시스템 아키텍처

> D:\affiliate_hub\ 시스템 전체 구조·데이터 흐름·모듈 분리·외부 의존·배포 파이프라인의 1차 설계서.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 DB.md로 이어짐.
> 등급 표기: [확정] = 공식 1차 자료 / [관찰] = 업계·사례 / [추정] = 본 세션 설계 판단 / [확인 불가] = 검증 실패.
> 본 문서는 PLAN.md §9 결정 표 + DECISIONS.md A~H 항목을 전제로 함.

---

## 0. 본 문서가 다루는 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| 시스템 전체 그림 | DB 스키마 상세 → DB.md |
| 디렉토리·모듈 분리 | 시나리오 10개 명세 → SCENARIOS.md |
| 외부 API 의존 | 디자인 시스템 → DESIGN.md |
| 빌드·배포 파이프라인 | 페이지 템플릿 → FRONTEND.md |
| 진실성 검증 게이트 위치 | 검증 규칙 상세 → POLICY.md |
| 로깅 골격 | 운영 절차·장애 대응 → OPS.md |
| 보안 경계 (secrets) | 백업·복구 → BACKUP.md |

---

## 1. 시스템 개요 (한 페이지)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            혼살림 (Honsalim) 시스템                          │
└─────────────────────────────────────────────────────────────────────────────┘

   [외부 API]              [로컬 D:\affiliate_hub\]                  [클라우드]
 ┌──────────────┐         ┌────────────────────────┐         ┌──────────────────┐
 │ 쿠팡 Open API│────┐    │ src/ (Python 3.10)     │         │ GitHub 공개 저장소│
 │ 알리 Portals │────┤    │  ├─ collector          │         │ ├─ Actions 빌드  │
 │ Claude Haiku │────┼───▶│  ├─ enricher (Claude)  │────▶git─│ └─ wrangler 배포 │
 │              │    │    │  ├─ validator (게이트) │  push   └────────┬─────────┘
 └──────────────┘    │    │  ├─ writer (DB)        │                  │
                     │    │  ├─ builder (Jinja2)   │                  ▼
                     └───▶│  ├─ dashboard (HTML)   │         ┌──────────────────┐
                          │  ├─ deployer           │         │ Cloudflare Pages │
                          │  └─ tracker            │         │ + 서울 PoP (ICN) │
                          │                        │         │ + R2 (이미지)    │
                          │ data/honsalim.db (SQLite)        │ + D1 (클릭 로그) │
                          │ build/ (정적 산출물)    │         │ + Workers (/go/) │
                          │ logs/honsalim.log      │         └────────┬─────────┘
                          │ docs/ (5파일 시스템)    │                  │
                          └────────────────────────┘                  ▼
                                                              ┌──────────────┐
                                                              │ honsalim.com │
                                                              │ (사용자)     │
                                                              └──────────────┘
   [secrets 격리]
 ┌────────────────────────┐
 │ D:\secrets\            │  ← 코드 저장소 절대 금지
 │   affiliate_hub\       │  ← .env / API 키 / 토큰
 │     coupang.env        │
 │     ali.env            │
 │     claude.env         │
 │     cloudflare.env     │
 │     github.env         │
 └────────────────────────┘
```

**한 줄 요약**: 로컬에서 Python으로 수집·생성·검증한 콘텐츠를 SQLite에 저장하고, Jinja2로 정적 HTML 빌드 → GitHub 저장소 push → Actions가 wrangler로 Cloudflare Pages 배포 → 서울 PoP에서 사용자에게 서빙.

---

## 2. 전체 데이터 흐름

### 2-1. 글 1편 발행까지 (정상 경로)

```
① 수집  ─▶  ② 가공  ─▶  ③ 검증  ─▶  ④ 미리보기  ─▶  ⑤ 승인  ─▶  ⑥ 빌드  ─▶  ⑦ 배포  ─▶  ⑧ 추적
collector   enricher    validator    dashboard       사용자       builder    deployer    tracker
   │           │            │            │             │            │           │           │
   ▼           ▼            ▼            ▼             ▼            ▼           ▼           ▼
쿠팡/알리    Claude API   진실성·       로컬 HTML   1클릭 OK      manifest   GH Actions   D1 클릭로그
딥링크·     본문·요약·   Schema·     미리보기     상태 변경    증분 빌드   wrangler     Cloudflare
가격·재고   메타 생성    disclosure·                  pending      build/      Pages       Analytics
            (Haiku)      링크 무결성                 → approved    출력
            │                                          │
            ▼                                          ▼
         honsalim.db                              빌드 트리거
         articles 테이블
```

### 2-2. 단계별 책임

| 단계 | 모듈 | 입력 | 출력 | 자동/수동 |
|------|------|------|------|----------|
| ① 수집 | `collector` | 시나리오 + 카테고리 | 상품 후보 N개 (가격·이미지 URL·딥링크) | 자동 |
| ② 가공 | `enricher` | 후보 N개 | Claude Haiku 본문 + 요약 + 메타 | 자동 |
| ③ 검증 | `validator` | 본문·메타·링크 | pass/fail + 사유 | 자동 (게이트) |
| ④ 미리보기 | `dashboard` | DB pending 글 | 로컬 HTML 미리보기 | 자동 |
| ⑤ 승인 | 사용자 | 미리보기 | DB 상태 `approved` | **수동 (1클릭)** |
| ⑥ 빌드 | `builder` | approved 글 + 템플릿 | `build/` HTML 트리 | 자동 |
| ⑦ 배포 | `deployer` | `build/` | Cloudflare Pages 갱신 | 자동 |
| ⑧ 추적 | `tracker` | `/go/<slug>` 클릭 | D1 로그·집계 | 자동 |

**핵심 원칙**: ③과 ⑤는 **둘 다 통과**해야 빌드 진입. ③은 기계 검증, ⑤는 사람 검증. Google Helpful Content 패널티 회피 핵심(E7) [확정].

### 2-3. 데이터 영구성 매트릭스

| 자산 | 위치 | 영구? | 백업 |
|------|------|-------|------|
| 원본 글 (텍스트·메타) | `data/honsalim.db` (로컬) | 영구 | BACKUP.md (예정) |
| 미가공 수집 로그 | `data/raw/YYYY-MM/*.json` | 30일 회전 | 없음 (재수집 가능) |
| 빌드 산출물 | `build/` | 빌드마다 재생성 | 불필요 |
| 사용자 직접 사진 | `static/photos/` (Git 포함) | 영구 | Git |
| Cloudflare R2 이미지 | R2 버킷 | 영구 | R2 자체 백업 |
| 클릭 로그 | Cloudflare D1 | 1년 (집계 후 회전) | D1 export 월 1회 |
| 빌드 manifest | `data/manifest.json` | 영구 (증분 빌드 핵심) | Git |
| logs | `logs/honsalim.log` | 90일 회전 | 없음 |
| secrets | `D:\secrets\affiliate_hub\` | 영구 | 별도 (BACKUP.md) |

---

## 3. 디렉토리 구조

```
D:\affiliate_hub\
├── CLAUDE.md                  ← 본 프로젝트 표준 지시 (정적)
├── README.md                  ← GitHub 공개용 (Phase 1 작성)
├── pyproject.toml             ← Python 의존성·도구 설정 (Phase 2)
├── .gitignore                 ← secrets/data/build/.env/*.pickle 제외
├── .github/
│   └── workflows/
│       ├── build.yml          ← 빌드 + 배포 (Phase 2)
│       ├── lint.yml           ← Black·Ruff·Mypy + pip-audit warn (Phase 2)
│       └── security.yml       ← pip-audit 월간 + JSON artifact 90일 (Phase 2, 세션 #6)
├── .claude/
│   ├── commands/              ← 슬래시 명령 3개 (구축 완료)
│   │   ├── honsalim-start.md
│   │   ├── honsalim-save.md
│   │   └── honsalim-end.md
│   └── settings.json          ← deny 룰 (Phase 1)
├── docs/                      ← 14개 설계 문서 + 5파일 시스템
│   ├── PLAN.md                ← 완료
│   ├── ARCH.md                ← 본 문서
│   ├── DB.md                  ← 예정
│   ├── SCENARIOS.md           ← 예정
│   ├── DESIGN.md              ← 예정
│   ├── FRONTEND.md            ← 예정
│   ├── BACKEND.md             ← 예정
│   ├── POLICY.md              ← 예정
│   ├── OPS.md                 ← 예정
│   ├── BACKUP.md              ← 예정
│   ├── MAINTENANCE.md         ← 예정
│   ├── SCHEDULE.md            ← 예정
│   ├── STATE.md               ← 5파일 (동적 운영 상태)
│   ├── DECISIONS.md           ← 5파일 (영구 [확정])
│   ├── TODO.md                ← 5파일 (활성 작업)
│   ├── EVENTS.md              ← 5파일 (세션 로그)
│   └── archive/               ← EVENTS 자동 회전 보관소
├── src/                       ← Python 모듈 (Phase 2)
│   ├── __init__.py
│   ├── cli.py                 ← 엔트리 포인트 (python -m honsalim ...)
│   ├── common/
│   │   ├── config.py          ← secrets 로드 (D:\secrets\affiliate_hub\)
│   │   ├── logging.py         ← logs/honsalim.log 설정
│   │   ├── db.py              ← SQLite 연결·트랜잭션
│   │   └── grading.py         ← [확정]/[관찰]/[추정] 등급 처리
│   ├── collector/             ← ① 수집
│   │   ├── coupang.py         ← 쿠팡 Open API
│   │   ├── aliexpress.py      ← Phase 5 이후 (stub)
│   │   └── scenario_loader.py ← SCENARIOS.md → 수집 큐
│   ├── enricher/              ← ② 가공
│   │   ├── claude_client.py   ← Anthropic SDK (Haiku)
│   │   ├── prompt_templates/  ← .md 프롬프트 외부화
│   │   └── meta_extractor.py  ← 제목·요약·태그·Schema
│   ├── validator/             ← ③ 검증 게이트
│   │   ├── truth.py           ← 진실성 (가격·재고·1인칭)
│   │   ├── schema.py          ← Schema.org JSON-LD
│   │   ├── disclosure.py      ← 공정위 첫머리 문구
│   │   └── links.py           ← 링크 무결성·외부 단축 URL 차단
│   ├── writer/                ← DB 쓰기
│   │   ├── article_writer.py
│   │   └── state_machine.py   ← pending → approved → published
│   ├── builder/               ← ⑥ Jinja2 빌더
│   │   ├── manifest.py        ← 의존 그래프·증분 판정
│   │   ├── renderer.py        ← Jinja2 환경·필터
│   │   ├── pages.py           ← 글·목록·홈·검색·About
│   │   ├── sitemap.py         ← sitemap.xml·RSS·IndexNow
│   │   └── assets.py          ← CSS/JS 해시·이미지 최적화
│   ├── dashboard/             ← ④ 로컬 미리보기·승인
│   │   ├── render.py          ← pending 글 정적 HTML 생성
│   │   └── approve.py         ← 1클릭 승인 (파일 기반 트리거)
│   ├── deployer/              ← ⑦ 배포
│   │   ├── git_push.py        ← GitHub push (승인 후 only)
│   │   └── wrangler.py        ← 로컬 직접 배포 옵션 (백업 경로)
│   ├── tracker/               ← ⑧ 추적
│   │   ├── d1_aggregator.py   ← Cloudflare D1 클릭 집계
│   │   └── report.py          ← 주간·월간 리포트 생성
│   └── workers/               ← Cloudflare Workers 소스 (별도 배포)
│       └── go_gateway.js      ← /go/<slug> 리다이렉트 + D1 로깅
├── templates/                 ← Jinja2 템플릿 (Phase 3, DESIGN.md 의존)
│   ├── base.html
│   ├── article.html
│   ├── list.html
│   ├── home.html
│   └── partials/
├── static/                    ← 정적 자산 (Git 포함)
│   ├── css/
│   ├── js/
│   ├── photos/                ← 사용자 직접 촬영 사진
│   └── favicon/
├── data/                      ← Git 제외 (.gitignore)
│   ├── honsalim.db            ← SQLite (Phase 2 생성)
│   ├── manifest.json          ← 증분 빌드 의존 그래프
│   └── raw/                   ← 수집 원본 로그 (30일 회전)
├── build/                     ← Git 제외, 빌드마다 재생성
│   ├── index.html
│   ├── articles/
│   ├── go/                    ← 자체 redirect 스텁 (실제는 Workers)
│   ├── sitemap.xml
│   ├── robots.txt
│   └── _headers               ← Cloudflare Pages 헤더 룰
├── logs/                      ← Git 제외
│   └── honsalim.log           ← 90일 회전
└── tests/                     ← Phase 2
    ├── test_validator.py      ← 게이트 회귀 테스트 최우선
    ├── test_builder.py
    └── fixtures/
```

**핵심 분리 원칙**:
- `src/` = 빌드 로직만. 콘텐츠 데이터는 `data/`에만.
- `data/` `build/` `logs/` = **Git 제외**. 빌드는 재현 가능.
- `secrets/` = 저장소 외부. `D:\secrets\affiliate_hub\` 절대 경로.
- 14개 설계 문서는 모두 `docs/`. 5파일 시스템도 같은 폴더.

---

## 4. Python 모듈 구조 + 의존도

### 4-1. 모듈 의존 그래프

```
                    ┌────────────┐
                    │   cli.py   │  (사용자/Actions 진입점)
                    └─────┬──────┘
                          │
        ┌─────────────────┼───────────────────────┐
        ▼                 ▼                       ▼
   ┌─────────┐      ┌──────────┐            ┌──────────┐
   │collector│      │ enricher │            │ builder  │
   └────┬────┘      └────┬─────┘            └────┬─────┘
        │                │                       │
        └────┬───────────┴───────┐               │
             ▼                   ▼               │
        ┌──────────┐       ┌──────────┐         │
        │validator │──fail─│dashboard │◀────────┤
        └────┬─────┘       └────┬─────┘         │
             │                  │ (1클릭 승인)   │
             ▼                  ▼               │
        ┌──────────┐       ┌──────────┐         │
        │  writer  │◀──────│approve.py│         │
        └────┬─────┘       └──────────┘         │
             │                                  │
             ▼                                  │
        ┌──────────┐                            │
        │ db.py    │◀───────────────────────────┤
        │(SQLite)  │                            │
        └──────────┘                            │
                                                ▼
                                          ┌──────────┐
                                          │ deployer │
                                          └────┬─────┘
                                               ▼
                                          ┌──────────┐
                                          │ tracker  │
                                          └──────────┘

   ▲ common/ (config·logging·db·grading) ─ 모든 모듈이 의존
```

**규칙**:
- 모든 모듈은 `common/`에 의존 가능.
- `validator`는 **모든 콘텐츠 모듈의 통과 게이트**. 우회 불가.
- 순환 의존 금지 (cli → 하위 모듈 단방향).
- 외부 API 모듈(collector, enricher, deployer, tracker)은 `common/config.py`로만 secrets 접근.

### 4-2. 모듈별 책임 한 줄 표

| 모듈 | 책임 | 외부 의존 | 비고 |
|------|------|----------|------|
| `cli` | 엔트리 + 명령 라우팅 | — | `python -m honsalim collect / build / deploy ...` |
| `common.config` | secrets 로드 (.env) | OS env / 파일 | secrets 폴더만 접근 |
| `common.logging` | 로그 회전 | — | 90일 회전 [추정] |
| `common.db` | SQLite 연결 | sqlite3 | 트랜잭션 단위 보장 |
| `common.grading` | [확정]/[관찰]/[추정] 처리 | — | 본문 내 등급 자동 추출 |
| `collector.coupang` | 쿠팡 Open API | requests | 1차 (메인) |
| `collector.aliexpress` | 알리 Portals | requests | Phase 5 이후 (stub) |
| `collector.scenario_loader` | SCENARIOS.md 파싱 | — | 큐 생성 |
| `enricher.claude_client` | Claude Haiku 본문 생성 | anthropic SDK | 프롬프트 캐시 적용 |
| `enricher.prompt_templates/` | 프롬프트 외부화 | — | .md 파일로 보관 |
| `enricher.meta_extractor` | 제목·요약·태그·Schema | — | JSON-LD 사전 검증 |
| `validator.truth` | 1인칭·가격·재고 진실성 | — | E1·E7·E8 위반 차단 |
| `validator.schema` | Schema.org JSON-LD | — | F5 강제 |
| `validator.disclosure` | 공정위 disclosure | — | E1 위반 차단 |
| `validator.links` | 링크 무결성·단축 URL | — | D6 위반 차단 |
| `writer.article_writer` | DB 쓰기 | common.db | 트랜잭션 |
| `writer.state_machine` | 상태 전이 강제 | — | pending→approved→published |
| `builder.manifest` | 의존 그래프 + 증분 판정 | — | TIMA 비대화 교훈 회피 |
| `builder.renderer` | Jinja2 환경 + 필터 | jinja2 | 한국어 필터 (조사·날짜) |
| `builder.pages` | 페이지 생성 | renderer | 글·목록·홈·About·검색 |
| `builder.sitemap` | sitemap·RSS·IndexNow | — | F4 IndexNow API 통보 |
| `builder.assets` | CSS/JS 해시·이미지 | hashlib | B4 캐시 무효화 |
| `dashboard.render` | 미리보기 HTML | — | 로컬 파일 (서버 없음) |
| `dashboard.approve` | 1클릭 승인 트리거 | — | 파일 기반 (.approve/) |
| `deployer.git_push` | GitHub push | git CLI | 사용자 명시 승인 후 only |
| `deployer.wrangler` | 로컬 직접 배포 | wrangler CLI | Actions 다운 시 백업 |
| `tracker.d1_aggregator` | D1 클릭 집계 | Cloudflare API | 일 1회 |
| `tracker.report` | 주간·월간 리포트 | — | dashboard에 표시 |

### 4-3. CLI 명령 패턴 (제안)

| 명령 | 단계 | 빈도 |
|------|------|------|
| `python -m honsalim collect <시나리오>` | ① 수집 | 주 2~3회 |
| `python -m honsalim enrich <draft-id>` | ② 가공 | 수집 직후 |
| `python -m honsalim validate <draft-id>` | ③ 검증 | enrich 직후 (자동) |
| `python -m honsalim dashboard` | ④ 미리보기 생성 | validate 후 (자동) |
| `python -m honsalim approve <draft-id>` | ⑤ 승인 | **사용자 1클릭** |
| `python -m honsalim build` | ⑥ 빌드 | approve 시 자동 트리거 (옵션) |
| `python -m honsalim deploy` | ⑦ 배포 | **사용자 명시 승인 후** |
| `python -m honsalim report --weekly` | ⑧ 추적 | 주 1회 |
| `python -m honsalim doctor` | 헬스 체크 | 임의 |

---

## 5. 외부 의존 5개

| # | 의존 | 용도 | 무료 한도 | 키 위치 | 다운 시 영향 |
|---|------|------|----------|---------|-------------|
| 1 | **쿠팡 Open API** | 상품·딥링크·가격 | 일별 호출 제한 (정확 수치 [확인 불가]) | `D:\secrets\affiliate_hub\coupang.env` | 신규 수집 정지, 기존 글 영향 없음 |
| 2 | **AliExpress Portals** | (Phase 5 이후) | 미확인 | `D:\secrets\affiliate_hub\ali.env` | Phase 5까지 0 |
| 3 | **Claude API (Haiku)** | 본문·요약·메타 생성 | 종량 (월 5~15천원 예산) | `D:\secrets\affiliate_hub\claude.env` | 신규 글 작성 정지, 기존 글 영향 없음 |
| 4 | **Cloudflare** (Pages·R2·D1·Workers) | 호스팅·이미지·추적·redirect | 각각 무료 한도 충분 | `D:\secrets\affiliate_hub\cloudflare.env` | **치명** — 사이트 다운 |
| 5 | **GitHub** (저장소·Actions) | 코드·빌드·배포 | 공개 저장소 무제한 [확정] | `D:\secrets\affiliate_hub\github.env` (PAT) | Actions 다운 시 로컬 wrangler 백업 |

### 5-1. 각 의존의 보호 장치

- **쿠팡 API**: 호출 빈도 제한·재시도 백오프·에러 시 로컬 캐시 fallback (24h)
- **Claude API**: prompt caching 적용·재시도 1회·에러 시 큐에 잔류 (다음 실행 재시도)
- **Cloudflare**: account-level 재인증 절차 OPS.md 문서화 / 백업 경로로 wrangler 로컬 배포 보존
- **GitHub**: PAT 90일 갱신 알림 STATE.md "자격증명 만료" 표에 추가 (발급 시)

### 5-2. API 키 발급 순서 (Phase 1)

```
1. Cloudflare 계정 생성 → Registrar에서 honsalim.com 결제
2. Cloudflare Pages 프로젝트 + R2 버킷 + D1 DB + Workers 라우트 준비
3. GitHub 공개 저장소 생성 + PAT 발급 (repo·workflow 스코프)
4. Anthropic 계정에서 Claude API 키 발급 (이미 보유)
5. 쿠팡 파트너스 가입 → Open API 키 발급 (승인 1~3일 [관찰])
6. (Phase 5) AliExpress Portals 가입
```

---

## 6. secrets 격리 (D:\secrets\affiliate_hub\)

### 6-1. 폴더 구조

```
D:\secrets\affiliate_hub\           ← Phase 1에 생성, Git 외부, 본 디렉토리 외부
├── coupang.env                     ← COUPANG_ACCESS_KEY=...
│                                       COUPANG_SECRET_KEY=...
│                                       COUPANG_TAG_ID=...
├── ali.env                         ← (Phase 5)
├── claude.env                      ← ANTHROPIC_API_KEY=...
├── cloudflare.env                  ← CF_API_TOKEN=... (Pages·R2·D1·Workers 스코프)
│                                       CF_ACCOUNT_ID=...
│                                       R2_BUCKET=honsalim-images
│                                       D1_DATABASE_ID=...
├── github.env                      ← GH_PAT=...
└── README.txt                      ← 갱신 일자·만료일 메모 (수동 관리)
```

### 6-2. 로드 절차

```
common/config.py
   └─ 시작 시: D:\secrets\affiliate_hub\*.env 전체를 dotenv로 환경 변수 로드
   └─ 검증: 필수 키 누락 시 즉시 종료 (fail-fast)
   └─ 외부로 노출 금지: print·log·exception 메시지에 key 값 포함 차단
```

### 6-3. deny 룰 (.claude/settings.json) [추정]

Phase 1에 추가할 deny 패턴:

| 패턴 | 이유 |
|------|------|
| `D:\secrets\**` 모든 쓰기 차단 | 우발 갱신 방지 |
| `**/*.env` 파일 쓰기 차단 | 저장소에 .env 침투 방지 |
| `**/data/honsalim.db` 직접 쓰기 차단 | 트랜잭션 우회 방지 |
| `git push` 사용자 확인 필요 | H4 자동 push 금지 |
| `wrangler pages deploy` 사용자 확인 필요 | 외부 게시 사용자 승인 |

### 6-4. GitHub Actions에서의 secrets

| 항목 | 저장 위치 | 비고 |
|------|----------|------|
| `CF_API_TOKEN` | Repository Secrets | wrangler 인증 |
| `CF_ACCOUNT_ID` | Repository Secrets | wrangler 대상 |
| `ANTHROPIC_API_KEY` | (Actions 미사용) | 본문 생성은 로컬만 |
| `COUPANG_*` | (Actions 미사용) | 수집은 로컬만 |

**원칙**: Actions는 **빌드·배포만**. 본문 생성·수집은 로컬에서 인간 검토 후 push.

---

## 7. 빌드 파이프라인 (manifest 기반 증분 빌드)

### 7-1. TIMA 비대화 교훈 회피

TIMA 프로젝트에서 **증분 빌드 의존 그래프 미명시**로 부분 빌드 비대화 문제 발생 (DECISIONS B5 [확정]). 본 프로젝트는 시작부터 manifest 강제.

### 7-2. manifest 구조 (개념)

`data/manifest.json` 내용 (스키마는 DB.md에서 확정):

| 키 | 값 | 용도 |
|----|-----|-----|
| `articles[*].id` | 글 ID | DB와 매핑 |
| `articles[*].slug` | URL slug | 파일 경로 결정 |
| `articles[*].content_hash` | 본문 SHA256 | 변경 감지 |
| `articles[*].depends_on` | [템플릿명, 글 ID, ...] | 의존 그래프 |
| `articles[*].last_built` | 빌드 시각 | 증분 판정 |
| `assets[*]` | CSS·JS·이미지 해시 | 캐시 무효화 |
| `templates[*]` | 템플릿 파일 해시 | 의존 무효화 |

### 7-3. 빌드 판정 로직

```
글 N편이 있을 때 빌드 대상은:
  ① 자신의 content_hash 변경
  ② 자신이 의존하는 템플릿 변경
  ③ 자신이 인용하는 다른 글 ID 변경
  ④ 자신이 사용하는 asset (CSS/JS) 변경
  ⑤ depends_on에 없는 글이 추가됨 (목록·sitemap 영향)

위 5개 중 하나라도 해당 → 재빌드. 아니면 skip.
sitemap·RSS·홈·목록은 글 1편 변경 시 항상 재생성.
```

### 7-4. 빌드 출력

```
build/
├── index.html                       ← 홈
├── articles/<slug>/index.html       ← 글
├── scenarios/<scenario>/index.html  ← 시나리오 허브
├── personas/<persona>/index.html    ← 페르소나 허브
├── about/index.html
├── search/index.html
├── sitemap.xml
├── feed.xml
├── robots.txt
├── _headers                          ← Cloudflare Pages CSP·Cache-Control
└── _redirects                        ← 짧은 경로 → 정식 경로 (옵션)
```

### 7-5. CWV 목표 (B6 [확정])

| 지표 | 목표 | 측정 |
|------|------|------|
| LCP | ≤ 2.0초 | Cloudflare Web Analytics (RUM) |
| INP | ≤ 150ms | 동일 |
| CLS | ≤ 0.05 | 동일 |

빌드 단계에서 강제:
- 이미지 width·height 속성 의무 (CLS)
- 폰트 preload + font-display: swap (LCP)
- JS는 defer 의무·인라인 critical CSS (LCP·INP)

---

## 8. 배포 파이프라인

### 8-1. 듀얼 빌드 구조 (사용자 확정)

```
[1차 경로 — 평상시]                  [2차 경로 — 백업]

로컬 D:\affiliate_hub\               로컬 D:\affiliate_hub\
   │                                    │
   ▼ python -m honsalim build           ▼ python -m honsalim build
build/                                build/
   │                                    │
   ▼ git add build/ && commit            │
   ▼ git push (사용자 승인)              ▼ wrangler pages deploy
GitHub                                Cloudflare Pages
   │
   ▼ Actions trigger
빌드 검증 (재현성·CWV 측정)
   │
   ▼ wrangler pages deploy
Cloudflare Pages
```

**평상시 1차 경로 채택 이유** [추정]:
- 공개 저장소이므로 Actions 비용 0
- 재현성 검증 (로컬 빌드 = Actions 빌드 일치)
- CWV·Schema·sitemap을 Actions에서 자동 회귀 테스트

**2차 경로 활용 시점**:
- GitHub Actions 다운
- 긴급 수정 (typo·링크 깨짐 등)
- 사용자 명시 승인 후

### 8-2. GitHub Actions 워크플로 3종 (Phase 2 [확정])

| 파일 | 트리거 | 책임 | 비고 |
|------|--------|------|------|
| `build.yml` | push main + workflow_dispatch | lint → test → build → wrangler deploy → IndexNow | renderer 미작성 시 build/deploy 자동 skip (Phase 3 게이트) |
| `lint.yml` | push main + PR | Black·Ruff·Mypy 정합 + pip-audit (continue-on-error) + CodeQL | 코드 품질 게이트, 매 push |
| `security.yml` | cron 매월 1일 09:00 UTC + workflow_dispatch | pip-audit 전수 + JSON artifact 90일 + GitHub Step Summary | DECISIONS I4 정기 보안 점검 |

`.github/workflows/build.yml` 단계 [확정 세션 #5 build ✅]:

| 단계 | 내용 | 실패 시 |
|------|------|---------|
| 1. checkout | repo clone | block |
| 2. setup Python 3.10 | 환경 셋업 | block |
| 3. install deps | pyproject.toml | block |
| 4. lint | Black·Ruff·Mypy | warn (block은 lint.yml) |
| 5. test | pytest | block |
| 6. build | `python -m honsalim build` | block |
| 7. diff | 로컬 build 결과와 일치? | warn |
| 8. validate | sitemap·robots·_headers 생성 확인 | block |
| 9. wrangler deploy | `wrangler pages deploy build/` | block |
| 10. IndexNow | F4 일괄 통보 | warn |

### 8-3. Cloudflare Pages 설정 (Phase 1)

| 항목 | 값 |
|------|----|
| 프로젝트명 | honsalim |
| 프로덕션 브랜치 | main |
| 빌드 명령 | (없음, Direct Upload) |
| 출력 디렉토리 | build/ |
| 커스텀 도메인 | honsalim.com (F7 .pages.dev 단독 운영 금지) |
| 헤더 룰 | _headers 파일 (CSP·Cache-Control) |
| Functions | 미사용 (Workers는 별도) |

### 8-4. Cloudflare Workers — `/go/<slug>` 게이트웨이 (D7 [확정])

```
사용자 클릭 (혼살림 글 상품 링크)
   │
   ▼
honsalim.com/go/<slug>
   │
   ▼
Cloudflare Workers (`go_gateway.js`)
   │
   ├─▶ D1 INSERT: timestamp·slug·UA·국가·referrer
   │
   ▼
302 Redirect → 쿠팡 딥링크 (D:\secrets\... 에서 빌드 시 주입된 매핑)
```

**중요**:
- 외부 단축 URL 금지 (D6 [확정]) → 자체 게이트웨이로 우회
- redirect는 **즉시 (D1 쓰기를 await하지 않음)**
- slug → 쿠팡 딥링크 매핑은 Workers 내장 KV 또는 D1 lookup (DB.md에서 확정)

### 8-5. 배포 사용자 승인 패턴

```
1. python -m honsalim build
2. (Claude → 사용자) "build/ 생성 완료. 미리보기 X편, 변경 Y편. 배포할까요?"
3. (사용자) "ok"
4. python -m honsalim deploy  (git push 또는 wrangler 직접)
5. Cloudflare Pages 빌드 완료 후 URL 보고
6. (옵션) Claude 자동 verify: HTTP 200 + Schema valid + sitemap 200
```

---

## 9. 진실성 검증 게이트

빌드 직전, 모든 글이 통과해야 하는 4단계 자동 게이트. 하나라도 fail → DB 상태 변경 금지.

| 단계 | 검사 | fail 시 | DECISIONS |
|------|------|---------|----------|
| 9-1. **truth** | 가격 정확성·재고 일치·1인칭 직접 경험 표현 | 글 rejected 상태 + 사유 로그 | E1·E7·E8 |
| 9-2. **schema** | JSON-LD BreadcrumbList·ItemList·Article 유효 | 동일 | F5 |
| 9-3. **disclosure** | 첫머리·푸터 공정위 문구 존재 | 동일 (E1 가장 치명) | E1·E5 |
| 9-4. **links** | 모든 외부 링크 HTTP 200·외부 단축 URL 0건 | 동일 | D6 |

상세 규칙·문구·예외는 **POLICY.md**에서 확정. 본 문서는 게이트 **위치**만 정의.

### 9-1 truth 게이트 세부 [추정]

- 가격: 본문 명시 가격 ↔ collector 수집 가격 차이 ≤ 5% (가격 변동 보호)
- 재고: 본문 "재고 있음/없음" ↔ API 응답 일치
- 1인칭: "사용해본 결과"·"실제로 써보니" 패턴 검출. 사용자 직접 사진(D5) 첨부 없으면 차단
- AI 자동 생성 흔적: "본 글은 AI가..."·"~로 알려져 있습니다" 등 패턴 차단

### 9-2 schema 게이트

- JSON-LD 파싱 가능
- 필수 필드 (name·image·offers·aggregateRating) 결측 없음
- Review schema는 **사용자 직접 사용 상품만** (F5 [확정])

### 9-3 disclosure 게이트

- 첫머리: "이 글에는 쿠팡 파트너스 활동의 일환으로..." 문구
- 푸터: 사업자 등록 후 사업자 정보 (E3)
- 위치·문구 일치: POLICY.md에서 정확 문구 확정

### 9-4 links 게이트

- 외부 단축 URL 패턴 (vivoldi·bit.ly·...) 0건
- 쿠팡 직접 딥링크 사용 (`link.coupang.com`)
- `/go/<slug>` 자체 게이트웨이만 허용
- HEAD 요청으로 404 검출

---

## 10. 자체 redirect 게이트웨이 (`/go/<slug>`)

§8-4에서 흐름 다룸. 본 절은 보안·운영 관점.

| 항목 | 값 |
|------|----|
| 라우트 | `honsalim.com/go/*` |
| 런타임 | Cloudflare Workers |
| 데이터 저장 | Cloudflare D1 |
| 매핑 소스 | 빌드 시 D1에 일괄 upsert (slug → 딥링크) |
| 보안 | slug 미등록 시 홈으로 302 (404 없음, 봇 학습 차단) |
| 클릭 차감 | UA bot 감지 시 D1 기록만, 어필리에이트 호출 없음 [추정] |
| 회전 | D1 클릭 로그 90일 후 집계 → 원본 삭제 |

**주의**: rel="nofollow sponsored" 필수 (E1·SEO).

---

## 11. 로깅·모니터링

### 11-1. 로컬 로그

```
logs/honsalim.log
   포맷: [YYYY-MM-DD HH:MM:SS] [모듈] [등급] 메시지
   회전: 90일 + 50MB [추정, OPS.md 확정]
   레벨: INFO 기본 / DEBUG 임시 / ERROR 알림
   민감정보: secrets 키 절대 미출력 (config.py에서 차단)
```

### 11-2. Cloudflare 측 관측

| 도구 | 용도 | 비용 |
|------|------|------|
| Cloudflare Web Analytics | RUM (LCP·INP·CLS) | 무료 |
| Cloudflare Workers Metrics | /go/ 호출 수·에러율 | 무료 |
| Cloudflare D1 | 클릭 로그 + 일별 집계 | 무료 한도 |
| Cloudflare Pages Deployments | 배포 이력·rollback | 무료 |

### 11-3. 에러 알림 [추정, OPS.md 확정]

- `validator` fail이 24h 내 3건 이상 → dashboard 상단 표시
- `deployer` 실패 → STATE.md "장애" 섹션 자동 갱신 (Phase 2 자동화)
- 외부 API 키 만료 D-7 → STATE.md "자격증명 만료" 표 알림

---

## 12. 개발 환경

### 12-1. Python 환경

| 항목 | 값 |
|------|----|
| Python | 3.10 32-bit (시스템 공유, TIMA·AutoBlog와 동일) — CLAUDE.md §12 [확정] |
| 가상환경 | 미사용 (동일 §12) |
| 의존 관리 | `pyproject.toml` + `pip install -e .` |
| 인코딩 | 모든 .py / .md UTF-8 |
| 라인 끝 | LF (Git autocrlf=input) |

### 12-2. 주요 라이브러리 [추정, Phase 2 확정]

| 라이브러리 | 용도 | 비고 |
|----------|------|------|
| `anthropic` | Claude API | 공식 SDK |
| `jinja2` | 템플릿 엔진 | B1 |
| `requests` | HTTP | 쿠팡·알리·Cloudflare |
| `python-dotenv` | .env 로드 | secrets |
| `pyyaml` | 설정·메타 | manifest 후보 |
| `markdown` | docs 렌더 (옵션) | dashboard 미리보기 |
| `pytest` | 테스트 | 핵심 |
| `black`·`ruff`·`mypy` | 린트·타입 | CI |
| `pillow` | 이미지 최적화 | webp 변환 |

### 12-3. 개발 도구

| 도구 | 용도 |
|------|------|
| `wrangler` CLI | Cloudflare 배포·로그·D1 쿼리 |
| `gh` CLI | GitHub 저장소·PR (옵션) |
| `git` | 버전 관리 |
| `node`·`npm` | wrangler·Workers 빌드 |

### 12-4. 로컬·Actions 환경 일치 보장

- Python 버전 고정 (`.python-version` 또는 `pyproject.toml`)
- 의존성 lockfile (`requirements.lock` 또는 `uv.lock`)
- Actions에서 Linux Python 3.10 사용 → 로컬 Windows와 OS 차이 존재 → 빌드 산출물 diff 단계로 검증 (§8-2 단계 7)

---

## 부록 A. 글 1편 발행 전체 시퀀스 (예시)

신학기 시즌, 시나리오 "원룸 첫 자취 30만원 패키지" 글 발행 가정.

```
[1주차 화]
사용자 →  /honsalim-start
Claude →  STATE·EVENTS 보고
사용자 →  "이번 주 신학기 시나리오 1편 발행 진행해줘"

[1] 수집
Claude →  python -m honsalim collect --scenario "원룸_첫_자취_30만"
       →  쿠팡 API 호출 → 책상·의자·조명·이불·주방 6개 카테고리 30개 후보 수집
       →  data/raw/2026-06/...json 저장
       →  drafts 테이블에 row 1건 (status=collected)

[2] 가공
Claude →  python -m honsalim enrich --draft 142
       →  Claude Haiku 호출 (프롬프트 캐시)
       →  본문 2,000자 + 요약 + 메타 + Schema JSON-LD
       →  drafts.status = enriched

[3] 검증 (자동 게이트)
Claude →  python -m honsalim validate --draft 142
       →  truth (1인칭·가격) → ⚠ 사용자 직접 사진 0장 → 한국어 1인칭 표현 차단 [E8]
       →  Claude → "직접 사진 1~3장 필요 (페르소나 신뢰)"
사용자 →  사진 3장 업로드 (책상·조명·이불 셋업 샷)
Claude →  python -m honsalim validate --draft 142 (재시도)
       →  4단계 게이트 모두 pass
       →  drafts.status = validated

[4] 미리보기
Claude →  python -m honsalim dashboard
       →  data/dashboard/index.html 갱신
       →  사용자에게 로컬 경로 안내

[5] 승인
사용자 →  미리보기 열람 → "ok, 게시해줘"
Claude →  python -m honsalim approve --draft 142
       →  drafts.status = approved
       →  articles 테이블로 이전

[6] 빌드
Claude →  python -m honsalim build
       →  manifest 증분 판정: 글 1편 추가 + sitemap·RSS·홈·시나리오 허브 재생성
       →  build/articles/wonroom-cheot-jachi-30/index.html 등 5개 파일
       →  Claude → "빌드 완료, 변경 파일 5개, build/ 검토 후 배포 여부 알려달라"

[7] 배포 (사용자 명시 승인)
사용자 →  "배포해줘"
Claude →  python -m honsalim deploy
       →  git add build/ && git commit -m "[2026-06-XX #N] 시나리오 1편 추가"
       →  git push origin main (H4 사용자 승인 만족)
       →  GitHub Actions 자동 시작 (5~7분)
       →  wrangler pages deploy 완료
       →  IndexNow API 통보 → 네이버·Bing·Yandex
       →  Claude → "배포 완료. honsalim.com/articles/wonroom-cheot-jachi-30/"

[8] 추적
24h 후
Claude →  python -m honsalim report --weekly
       →  D1 클릭 집계: 글당 조회·클릭·국가
       →  주간 리포트 dashboard 표시
```

---

## 부록 B. 장애 시나리오 5개

### B-1. 쿠팡 API 다운
- 영향: 신규 수집 정지. 기존 글 게시·서빙 영향 없음.
- 대응: collector 재시도 (지수 백오프). 24h 이상 지속 시 STATE.md 장애 섹션 갱신·콘텐츠 발행 일시 정지.

### B-2. Claude API 다운
- 영향: 신규 본문 생성 정지.
- 대응: 큐에 잔류. 다음 실행 시 자동 재시도. 24h 이상 → 사용자 알림.

### B-3. Cloudflare Pages 다운
- 영향: **사이트 다운** (치명).
- 대응: Cloudflare 측 복구 대기 (SLA·자동 장애 조치). 별도 호스팅 즉시 전환은 미준비.
- 대안 [추정, MAINTENANCE.md 확정]: build/ 산출물을 GitHub Pages에도 보조 배포 (DNS A/B 전환 가능)?

### B-4. GitHub Actions 다운
- 영향: 자동 배포 정지. 1차 경로 단절.
- 대응: 로컬 wrangler 직접 배포 (§8-1 2차 경로). 사용자 승인 후 즉시 대체 가능.

### B-5. D1 클릭 로그 손실
- 영향: 클릭 통계 부정확. 사이트 가용성·수익에는 무영향.
- 대응: Cloudflare Analytics에서 페이지뷰 fallback 추정. D1 백업은 월 1회 export (BACKUP.md).

---

## 13. 다음 단계

ARCH.md 사용자 검토 → 승인 후 **DB.md (SQLite 스키마·인덱스·최적화)** 작성 진입.

DB.md에서 확정할 핵심:
- `articles` `drafts` `products` `clicks` `manifest` 테이블 스키마
- 글 상태 머신 (collected → enriched → validated → approved → published)
- 인덱스 전략 (slug·published_at·scenario_id)
- 마이그레이션 도구 (Alembic vs 자체 SQL 파일)
- D1 (클릭 로그) ↔ SQLite (콘텐츠) 분리 운영 패턴

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (12장 + 부록 A·B) | Claude Opus 4.7 |
