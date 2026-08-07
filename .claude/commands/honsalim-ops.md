# /honsalim-ops — 주간 무인 운영 세션 (파일럿 — 세션 #52 설계)

주인 개입 없이 예약 실행되는 **운영 판단 세션**: 점검 → 심층 분석 → 합의 범위 내 실행 → 보고.
사람이 수동 호출해도 동일하게 동작한다. 파일럿 검증(첫 1회)은 수동 호출로 한다
([[unmanned-monitoring-gate]] — 게이트·자동화는 켜기 전 실제로 돌려본다).

## 0. 안전 원칙 (CLAUDE.md §0 + 본 세션 특칙)

- **실패 시 무변경**: 어느 단계든 이상하면 파일을 바꾸지 말고 보고서 + 텔레그램 경보만 남기고 종료.
- **테스트 게이트**: 파일을 바꾸는 모든 실행은 black·ruff·mypy·회귀 전체 PASS가 선행 조건.
  하나라도 실패 = 실행 취소, '주인 결정 대기'로 강등.
- destructive git 절대 금지(DECISIONS N1). 발행 파이프라인(auto-cycle 영역) 개입 금지 — 생산은 이미 무인.
- 라이브 LLM 재생성 루프 금지(CLAUDE.md §7-3). n=1 라이브 판단 금지.
- 추측 금지 — 등급([확정]/[관찰]/[추정]/[확인 불가]) 명시. [[critical-final-review]] — 반증 후 최종만.

## 1. 점검 (read-only)

1. 운영 폴더 `git -C D:\affiliate_hub branch --show-current` == **main** (아니면 즉시 경보·종료 —
   [[autonomous-detached-head-silent-stop]])
2. `data/auto_cycle_last.json` + `logs/auto_cycle.log` 최근 7일 — 발행 연속성(빠진 날짜)·[ALERT]·
   "배포 차단"·refill_degraded (로그는 UTF-8 재디코드 후 판독 — [[powershell-korean-encoding]])
3. DB read-only — published 수·keyword_queue 상태 분포·failed 격리 키워드
4. 라이브 — 홈 + 최신 글 2편 + sitemap.xml HTTP 200 (curl·브라우저 UA — [[live-verify-cloudflare-ua]]).
   ★전 항목 동시 실패 = 도구 문제 먼저 의심.
5. `PYTHONPATH=src python -m cli gsc-report --json` — 노출·클릭·순위 추이 + sitemap 색인.
   연동 전/실패면 보고서에 '연동 대기'로 명시하고 계속(§0 실패 격리).

## 2. 심층 분석

- 발행 공백·게이트 반려 추이의 **원인**(로그 근거) · 씨앗 소진 예측(적격 후보 잔량)
- GSC 추이: 최근 7일 vs 이전 7일(노출·클릭·순위·색인) — 변화 원인 가설과 반증
- TODO.md 관찰 항목 소화 · 성장 레버(DECISIONS JJ4) 진행 상태

## 3. 실행 — 허용 범위 ONLY (그 외 전부 '주인 결정 대기'로 강등)

| 허용 | 선행 조건 |
|---|---|
| 씨앗 등재·보강 | DECISIONS **JJ1~JJ3** 원칙(공략구간 실측·근친 변형 금지·컨셉 정합·브랜드/YMYL/상품 불일치 제외) + `lint_alignment` 신규 이슈 0 + 회귀 전체 PASS |
| 문서 갱신 | EVENTS/STATE/TODO — cap·회전 규칙은 /honsalim-end와 동일 |
| 커밋·푸시 | 위 결과물만. push 전 `git fetch` + ff 확인([[autonomous-deploy-advances-origin]]) · 운영 폴더 ff 반영 |

**금지(제안만 하고 실행 않음)**: 글 비공개·통합 · 카테고리 공개 · 발행 페이스/게이트/설정 변경 ·
코드 수정 · 새 기능 · 외부 채널 게시 · 쿠팡/알리 계정 작업.

## 4. 보고 (주인이 보는 것)

1. **`docs/reports/ops_YYYY-MM-DD.md`** — 점검 표·분석·실행 내역·★주인 결정 대기 목록·다음 회차 관찰
2. **텔레그램** — `PYTHONPATH=src python -m cli notify-alert "<3~5줄 요약>"`
   (발행 상태 · GSC 추이 한 줄 · 실행 N건/대기 N건 · 보고서 경로)
3. **EVENTS.md** — ★루틴 전부-정상 회차는 쓰지 않는다(보고서 파일로 충분·cap 보호).
   실행(씨앗 등재 등)이나 이상이 있었던 회차만 간결 블록 추가, 제목은 세션 번호 대신
   `### ops-YYYY-MM-DD` 형식(사람 세션 번호 체계와 분리).

## 5. 파일럿 한정 규칙

- 첫 회차는 주인 수동 호출 → 결과·사용량을 보고 주기 편성(예약 등록)을 주인이 판단한다.
- 세션 말미에 사용량 요약(가능하면 explain-usage)을 보고서에 첨부 — 소모 실측 자료.
- 예약 등록 후에도 월 실행 상한(기본 5회)을 넘는 재실행은 하지 않는다.
