# OPS.md — 혼살림 운영·로깅·장애·자격증명

> 일·주·월·분기 운영 체크리스트 + 로그 회전 + 알림 채널 + 자격증명 만료 캘린더 + 장애 대응 + 사업자 등록 단계 절차.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 BACKUP.md로 이어짐.
> 등급: [확정] / [관찰] / [추정] / [확인 불가].
> 전제: ARCH §11 + BACKEND §3-5·§7 + POLICY §7·§8·§14 + DECISIONS C·D·E·H + CLAUDE.md §3 (5파일).

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| 일·주·월·분기 체크리스트 | 백업·복구 절차 → BACKUP.md |
| 로그 회전·알림 | 유지보수·확장 → MAINTENANCE.md |
| 자격증명 만료 캘린더 | Phase 일정 → SCHEDULE.md |
| 장애 대응 5종 | 검증 규칙 → POLICY.md |
| 사업자 등록 단계 절차 | 코드 모듈 → BACKEND.md |
| 사이트 다운 시 대응 | DB 스키마 → DB.md |

---

## 2. 운영 체크리스트

### 2-1. 일별 (자동)

| 항목 | 시각 | 자동/수동 | 도구 |
|------|------|---------|------|
| D1 clicks → clicks_daily 집계 | 03:00 KST | 자동 (CF cron 또는 로컬 cron) | wrangler |
| SQLite articles.view_count_cached 갱신 | 03:30 KST | 자동 | python -m honsalim report --daily |
| 로그 회전 점검 | 04:00 KST | 자동 | logging.handlers.TimedRotatingFileHandler |
| 외부 API 헬스 체크 | 09:00 KST | 자동 | python -m honsalim doctor |
| 게시 큐 미발행 글 알림 | 09:00 KST | 자동 → dashboard | dashboard.render() |

### 2-2. 주별 (사용자 + 자동) — 세션 #2 갱신 (DECISIONS C6·C8)

| 항목 | 시점 | 비고 |
|------|------|------|
| 신규 시나리오 **사용자 역량 내 최대 작성** (예: 주 5~7편) | 사용자 페이스 | SCENARIOS §6-1 |
| dashboard 검토 + 1클릭 승인 | 작성 직후 (수동) | CLAUDE §2.마 — **자동 "승인" 금지** |
| 자동 발행 (스케줄러) | **매일 11:00 KST** | DECISIONS C7. 큐 비면 정지 |
| 주간 리포트 자동 생성 | 일요일 새벽 | python -m honsalim report --weekly |
| 가격 변동 점검 | 일요일 | collector 재호출 → 가격 ±10% 변동 검출 |
| 큐 상태 점검 | 일요일 | `python -m honsalim scheduler-status` — 큐 < 7편 시 작성 알림 |

### 2-3. 월별

| 항목 | 시점 | 비고 |
|------|------|------|
| `VACUUM` SQLite | 매월 1일 새벽 | DB §15-2 |
| D1 clicks 90일 초과 자동 DELETE | 매월 1일 | POLICY §14-1 |
| D1 export 백업 | 매월 1일 | BACKUP.md |
| 자격증명 만료 D-7~D-30 점검 | 매월 1일 | §6 |
| 비용 집계 (Claude API·도메인) | 매월 1일 | PLAN §8 비교 |
| EVENTS.md 회전 점검 | 매월 1일 | CLAUDE.md §3 (6세션 시) |
| 사용자 직접 사진 라이브러리 점검 | 매월 1일 | 누락·고화질 보강 |
| **보안 점검 (I4)**: pip-audit + GitHub Dependabot 알림 정리 | 매월 1일 | POLICY §14-bis-4 |
| **GitHub Secret Scanning 알림 점검** | 매월 1일 | POLICY §14-bis-1 |

### 2-4. 분기별

| 항목 | 시점 | 비고 |
|------|------|------|
| 디자인 토큰 일관성 점검 | 분기 1일 | DESIGN §3 변경 영향 분석 |
| 외부 링크 일괄 무결성 (전체 글) | 분기 1일 | python -m honsalim validate --all-published --links-only |
| 의존성 보안 점검 | 분기 1일 | pip-audit + Dependabot |
| 콘텐츠 갱신 큐 정리 | 분기 1일 | 가격·재고 변동 글 일괄 갱신 검토 |
| 백업 복구 리허설 | 분기 1일 | BACKUP.md (3개월에 1번 실 복구 테스트) |

### 2-5. 반기별

| 항목 | 시점 | 비고 |
|------|------|------|
| KPI 점검 (게시글·트래픽·수익) | 6/30, 12/31 | PLAN §6 |
| AdSense 신청 재결정 | 12/31 | D3 [확정] |
| 영어 확장 검토 | 12/31 | PLAN §2 |
| 보안 audit (deny·secrets·CSP) | 6/30, 12/31 | POLICY §10 |
| Phase 전환 판단 | 분기 마지막 | SCHEDULE.md |

### 2-6. 매 세션 (Claude·사용자)

| 항목 | 명령 | 비고 |
|------|------|------|
| 세션 시작 | `/honsalim-start` | STATE·EVENTS·DECISIONS·TODO 읽기 |
| 중간 저장 | `/honsalim-save` | 큰 변경 후 |
| 세션 종료 | `/honsalim-end` | STATE·EVENTS·TODO 갱신 + 자동 commit 1회 |

---

## 3. 로깅

### 3-1. 파일 구조

```
D:\affiliate_hub\logs\
├── honsalim.log               ← 현재
├── honsalim.log.2026-06-15    ← 어제
├── honsalim.log.2026-06-14    ← 그제
└── ...                        ← 90일 누적
```

### 3-2. 회전 정책 (BACKEND §7-1 보강)

| 항목 | 값 |
|------|----|
| 회전 방식 | TimedRotatingFileHandler (when='midnight') |
| 보관 일수 | 90일 (`backupCount=90`) |
| 단일 파일 크기 한계 | 50MB (예외 시 RotatingFileHandler 보조) |
| 인코딩 | UTF-8 |
| level | INFO 기본·DEBUG는 `--verbose`만 |

### 3-3. 형식

```
[YYYY-MM-DD HH:MM:SS.fff TZ] [모듈명] [LEVEL] 메시지 key=value
```

예시:
```
[2026-06-15 10:23:45.123 KST] [collector.coupang] INFO Collected products scenario_id=3 count=24
[2026-06-15 10:23:46.001 KST] [enricher.claude_client] INFO Article enriched draft_id=142 input_tokens=2340 output_tokens=890
[2026-06-15 10:23:47.512 KST] [validator.truth] WARN Direct photo missing draft_id=142
[2026-06-15 10:24:01.001 KST] [deployer.git_push] ERROR Push failed remote=main error="Authentication failed"
```

### 3-4. 출력 채널

| 채널 | 용도 |
|------|------|
| 파일 (honsalim.log) | 영구 기록 |
| stdout | CLI 실행 시 사용자 즉시 확인 |
| dashboard | 최근 24h 요약 표시 |
| STATE.md | ERROR 이상 자동 반영 (대용량 자동 갱신, 사용자 검토) |

### 3-5. redact 필터 (POLICY §10-1)

| 패턴 | 마스킹 |
|------|--------|
| `ANTHROPIC_API_KEY=sk-ant-...` | `ANTHROPIC_API_KEY=***` |
| `COUPANG_ACCESS_KEY=...` | `***` |
| `CF_API_TOKEN=...` | `***` |
| `GH_PAT=...` | `***` |
| 그 외 `*_KEY` `*_TOKEN` `*_SECRET` 정규식 | `***` |

---

## 4. 알림 채널

### 4-1. 알림 우선순위

| 우선 | 채널 | 대상 |
|------|------|------|
| 1 | dashboard 상단 배너 | 사용자가 다음 dashboard 열 때 |
| 2 | STATE.md "장애" 섹션 자동 갱신 | 사용자 세션 시작 시 |
| 3 | logs/honsalim.log ERROR | 사후 분석 |
| 4 | (선택) 이메일 → 운영자 | 치명적 (사이트 다운) |

이메일 알림은 Phase 4 검토 [추정] (초기 부담 회피).

### 4-2. 알림 트리거 [추정]

| 조건 | 액션 |
|------|------|
| validator fail 24h ≥ 3건 | dashboard 빨간 배너 |
| 빌드 5분 이상 | warn 로그 |
| 배포 실패 | STATE.md "장애" + dashboard 배너 |
| 외부 API 1시간 다운 | STATE.md "장애" + warn 로그 |
| 자격증명 만료 D-7 | dashboard 노란 배너 + STATE.md |
| 자격증명 만료 D-1 | dashboard 빨간 배너 + STATE.md |
| 사이트 200 응답 실패 (verify) | STATE.md "치명" + 이메일 (Phase 4) |

### 4-3. STATE.md "장애" 섹션 자동 갱신

본 절을 통해 다음 세션 시작 시 사용자가 즉시 인식:

```
## 장애 (자동 기록)
| 일시 | 영역 | 메시지 |
|------|------|--------|
| 2026-06-15 10:24:01 | deployer.git_push | 인증 실패 |
```

사용자가 해결 후 수동으로 행 제거.

---

## 5. 장애 대응 5종 (ARCH 부록 B 보강)

### 5-1. 쿠팡 API 다운

**증상**: collector 호출 timeout 또는 5xx.
**영향**: 신규 수집만. 기존 글 영향 없음.
**대응**:
1. logs 확인 (1시간 지속?)
2. 쿠팡 Status 페이지 확인 (있다면)
3. 1시간 + 1시간 후 재시도
4. 24h 이상 → 수집 일시 정지·다른 시나리오 작업

### 5-2. Claude API 다운

**증상**: enricher 호출 5xx 또는 OverloadedError.
**영향**: 신규 본문 생성만. 기존 글 영향 없음.
**대응**:
1. 큐 잔류 (자동 재시도)
2. Anthropic Status 페이지 확인
3. 24h 이상 → 사용자 알림 + 수동 대기

### 5-3. Cloudflare Pages 다운

**증상**: 사이트 200 응답 실패.
**영향**: **치명** — 사이트 다운.
**대응**:
1. Cloudflare Status 페이지 즉시 확인
2. 대부분 자동 복구 (분 단위)
3. 30분 이상 지속 → DNS A/B 전환 검토 (Phase 4 보조 배포 준비된 경우만)
4. 사용자에게 즉시 보고 + STATE.md 치명 기록

### 5-4. GitHub Actions 다운

**증상**: push 후 Actions 실행 안 됨.
**영향**: 자동 배포 정지.
**대응**:
1. GitHub Status 확인
2. 로컬에서 `python -m honsalim deploy --method wrangler` 직접 배포 (ARCH §8-1 2차)
3. 사용자 명시 승인 필요 (H4 [확정])

### 5-5. D1 클릭 손실

**증상**: D1 쿼리 timeout 또는 클릭 수 0.
**영향**: 통계 부정확. 사이트·수익 영향 없음.
**대응**:
1. Cloudflare Status 확인
2. Cloudflare Analytics에서 페이지뷰 fallback 추정
3. D1 복구 후 누락 기간 명시 (clicks_daily 보간 X)

### 5-6. 일반 원칙

- 즉시 복구 시도하지 않음 (사용자 승인 게이트 유지)
- 외부 의존 다운 시 사이트 자체는 정상 운영 가능
- 패닉 동작 (강제 push·강제 deploy) 금지

---

## 6. 자격증명 만료 캘린더

### 6-1. 자격증명 목록 (Phase 1 발급 후 채움)

| 자격증명 | 발급일 | 만료일 | 갱신 주기 | 자동 알림 |
|---------|-------|--------|----------|----------|
| 도메인 honsalim.com | TBD | TBD (1년) | 연 1회 | D-30·D-7·D-1 |
| Cloudflare API token | TBD | TBD | 검토 (영구 가능) | 회전 시 |
| GitHub PAT | TBD | TBD (90일) | 90일마다 | D-7·D-1 |
| Anthropic API key | TBD | 영구 | 회전 권장 (6개월) | 자율 |
| 쿠팡 Open API 키 | TBD | TBD | 검토 | 회전 시 |
| 사업자 등록증 | TBD | 영구 | — | — |
| 통신판매업 신고 | TBD | 영구 | — | — |
| 도메인 WHOIS | 자동 | — | — | — |

### 6-2. STATE.md "자격증명 만료" 표 동기화

OPS·BACKEND 자동 점검 (월 1회) → STATE.md 갱신:

```
## 자격증명 만료
| 자격증명 | 발급 | 만료 | 갱신 |
|---------|------|------|------|
| GitHub PAT | 2026-06-01 | 2026-08-30 | D-7 알림 |
```

### 6-3. 갱신 절차

#### 도메인
1. Cloudflare Registrar 로그인
2. 자동 갱신 활성 확인 (권장)
3. 결제 카드 만료 여부 확인

#### GitHub PAT
1. github.com/settings/tokens
2. 기존 PAT regenerate (90일)
3. `D:\secrets\affiliate_hub\github.env` 갱신
4. 로컬에서 doctor 명령 통과 확인

#### Cloudflare API token
1. Cloudflare → My Profile → API Tokens
2. 권한 동일하게 새 토큰 발급
3. `cloudflare.env` 갱신 + GitHub Repository Secrets 갱신
4. doctor 통과 확인

#### 쿠팡 Open API
1. 파트너스 대시보드 → API 설정
2. 키 회전
3. `coupang.env` 갱신
4. collector 테스트 호출

---

## 7. 사업자 등록 단계 절차 (D4 [확정])

### 7-1. 조건

- 월 수익 10만원 누적 후 (PLAN §9 D4)
- 또는 사용자 판단으로 조기 등록

### 7-2. 등록 절차 [관찰]

| 단계 | 내용 | 시점 |
|------|------|------|
| 1 | 홈택스 → 사업자등록 신청 | 수익 발생 후 |
| 2 | 업종 코드: 광고대행업 743002 (D4 [확정]) | 동일 |
| 3 | 간이과세자 (연 8,000만원 미만) | 동일 |
| 4 | 통신판매업 신고 (구청·시청) | 사업자 후 1주 내 |
| 5 | 사업용 계좌 (선택) | 운영 분리 시 |
| 6 | 부가세 신고 (1·7월) | 분기별 |
| 7 | 종합소득세 (5월) | 연 1회 |

### 7-3. 등록 후 본 사이트 변경

- about.html 사업자 정보 게재 (POLICY §8-2)
- footer 사업자 정보 추가
- 개인정보처리방침 사업자 명의로 갱신

### 7-4. 등록 전 임시 정책

POLICY §8-4: "개인 운영자, 사업자 등록 진행 중" 명시.

---

## 8. 데이터 운영

### 8-1. SQLite 일상 운영

| 작업 | 빈도 | 명령 |
|------|------|------|
| `VACUUM` | 월 1회 | python -m honsalim db vacuum |
| `ANALYZE` | 마이그레이션 후 + 분기 1회 | python -m honsalim db analyze |
| `PRAGMA integrity_check` | 분기 1회 | python -m honsalim db check |
| 백업 | 일 1회 | BACKUP.md |

### 8-2. D1 일상 운영

| 작업 | 빈도 |
|------|------|
| clicks 90일 초과 DELETE | 매월 1일 자동 |
| clicks_daily 12개월 초과 DELETE | 매월 1일 자동 |
| slug_map 갱신 | 매 빌드 시 |
| Cloudflare 측 백업 export | 매월 1일 |

### 8-3. logs/ 운영

- 회전 90일 (§3-2)
- 백업 미대상 (재현 가능, BACKUP.md)
- 분기 1회 logs grep으로 ERROR 누적 점검

---

## 9. 외부 API 비용·rate limit 관리

### 9-1. Claude API

| 항목 | 정책 |
|------|------|
| 월 예산 | 5,000~15,000원 (PLAN §8) |
| 초과 알림 | dashboard 노란 배너 + STATE.md |
| 캐시 활용 | 90% hit 목표 (BACKEND §3-4) |
| Haiku 우선 | Sonnet은 수동 fallback만 |

### 9-2. 쿠팡 Open API

| 항목 | 정책 |
|------|------|
| 호출 빈도 | 200ms 슬립·최대 60 RPM [추정] |
| 일일 한도 | 미확인 [확인 불가] — 실측 후 갱신 |
| 캐시 | 24시간 (수집 결과) |

### 9-3. 알리 Portals (Phase 5)

미적용.

### 9-4. Cloudflare

| 서비스 | 무료 한도 | 본 프로젝트 사용 추정 |
|--------|---------|---------------------|
| Pages | 무제한 (대역폭) | 충분 |
| R2 | 10GB 저장 + 무료 egress | 충분 (Phase 4까지) |
| D1 | 5GB / 5M reads, 100k writes / day | 충분 |
| Workers | 100k req/day | 충분 (글당 클릭 수 작음) |

### 9-5. GitHub Actions

- 공개 저장소 무제한 [확정]
- 동시 실행 5개 제한 (병렬 빌드 시 영향) [관찰]

---

## 10. 모니터링 대시보드 (dashboard 모듈)

### 10-1. dashboard 화면 구성 [추정]

```
┌──────────────────────────────────────────┐
│ 혼살림 대시보드 (생성: YYYY-MM-DD HH:MM)  │
├──────────────────────────────────────────┤
│ [장애 알림]                              │
│   ⚠ deployer.git_push 인증 실패 (2시간 전) │
├──────────────────────────────────────────┤
│ [작업 큐]                                │
│   collected   2 편                       │
│   enriched    1 편                       │
│   validated   3 편 ← 승인 대기            │
│   approved    0 편                       │
│   rejected    1 편 (사유: 직접 사진 누락) │
├──────────────────────────────────────────┤
│ [승인 대기 글]                           │
│   #142 원룸 첫 자취 30만원 (미리보기 →) │
│   #143 가을 자취 보완 30만원 (미리보기 →) │
│   #144 ...                              │
│   [승인 명령: approve --draft <id>]      │
├──────────────────────────────────────────┤
│ [최근 7일 통계]                          │
│   조회 1,234 / 클릭 56 / 신규 글 3편     │
├──────────────────────────────────────────┤
│ [자격증명 만료 D-30 이내]                │
│   GitHub PAT D-12                       │
└──────────────────────────────────────────┘
```

### 10-2. 미리보기 링크

- 각 글 미리보기 → `data/dashboard/preview/<draft_id>.html`
- 실제 글 디자인 적용
- "이대로 발행" 버튼 (실행은 X, 명령 복사)

### 10-3. dashboard 갱신 트리거

- 매 `validate` 후 자동 갱신
- 매 `approve` 후 자동 갱신
- 매 일 09:00 KST 자동
- 사용자가 `python -m honsalim dashboard` 직접 실행

---

## 11. 사이트 다운 시 대응 (5-3 보강)

### 11-1. 감지

- 자동 verify (Phase 2): 분 1회 home `/` HEAD 검사
- 실패 시 STATE.md 치명 기록 + dashboard 빨간 배너
- (Phase 4) 이메일 알림

### 11-2. 1차 대응 (사용자)

1. https://www.cloudflarestatus.com 확인
2. honsalim.com 직접 접속 (브라우저)
3. Cloudflare Dashboard → Pages → Deployments 상태

### 11-3. 2차 대응 (지속 30분+)

1. Cloudflare 지원팀 문의
2. (Phase 4 준비된 경우) GitHub Pages 보조 배포 활성 (MAINTENANCE.md)
3. 사용자 SNS·이메일로 사이트 다운 안내 (선택)

### 11-4. 복구 후

- STATE.md 치명 기록 → "복구됨 (YYYY-MM-DD HH:MM)" 표시
- 다운 시간·원인·재발 방지책 EVENTS.md 다음 세션에 기록
- 누락된 클릭 통계는 보간 X (POLICY §14-1 정직성)

---

## 12. 다음 단계

OPS.md 사용자 검토 → 승인 후 **BACKUP.md (백업·복구 절차)** 작성 진입.

BACKUP.md에서 확정할 핵심:
- SQLite DB 백업 일별 자동·외부 드라이브
- secrets 백업 (암호화·별도 위치)
- 사용자 직접 사진 백업
- Cloudflare R2·D1 export 절차
- 복구 리허설 분기 1회 절차
- 사이트 통째 복구 (도메인 + 코드 + DB + 이미지)
- 재난 복구 (D 드라이브 손실) 시나리오

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (체크리스트·로그·알림·장애·자격증명·사업자 절차) | Claude Opus 4.7 |
