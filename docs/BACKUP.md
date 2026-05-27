# BACKUP.md — 혼살림 백업·복구

> SQLite·secrets·사용자 직접 사진·R2·D1 백업 + 복구 리허설 + 재난 복구 시나리오.
> 작성: 2026-05-27 (Claude Opus 4.7) / 검토 후 MAINTENANCE.md로 이어짐.
> 등급: [확정] / [관찰] / [추정] / [확인 불가].
> 전제: DB §15-3 + OPS §8 + POLICY §10·§14-2 + DECISIONS B·H.

---

## 1. 본 문서 범위

| 다룸 | 다루지 않음 (별도 문서) |
|------|------------------------|
| 백업 대상 7종 분류 | 일상 운영 → OPS.md |
| 일·월 자동 백업 절차 | 의존성·코드 관리 → MAINTENANCE.md |
| 외부 저장 정책 | DB 스키마·운영 PRAGMA → DB.md |
| 복구 리허설 분기 1회 | 검증·보안 정책 → POLICY.md |
| 재난 복구 시나리오 (D 드라이브 손실) | Phase 일정 → SCHEDULE.md |
| 사용자 직접 사진 영구 보존 | 디자인·사진 가이드 → DESIGN.md |

---

## 2. 백업 대상 7종

| # | 자산 | 영구성 | 백업 주기 | 우선순위 |
|---|------|-------|----------|----------|
| 1 | `data/honsalim.db` (SQLite 콘텐츠) | 영구 | 일 1회 | ★★★★★ |
| 2 | `static/photos/` (사용자 직접 사진) | 영구 | 신규 추가 즉시 + 월 1회 동기 | ★★★★★ |
| 3 | `D:\secrets\affiliate_hub\` (자격증명) | 영구 | 회전 시·월 1회 | ★★★★★ |
| 4 | GitHub 저장소 (코드·docs·manifest) | Git 자동 | 푸시 시 | ★★★★ |
| 5 | Cloudflare D1 (clicks·clicks_daily) | 회전 | 월 1회 export | ★★★ |
| 6 | Cloudflare R2 (이미지, Phase 4+) | 영구 | 월 1회 동기 | ★★★ |
| 7 | `logs/honsalim.log` (운영 로그) | 90일 회전 | 백업 미대상 | ☆ |

**원칙** [추정]:
- 손실 시 콘텐츠·신뢰 재현 불가능한 자산은 ★★★★★ (DB·사진·secrets).
- Git 자동 추적 자산은 백업 자체보다 푸시 빈도가 중요.
- 로그는 운영 기록일 뿐, 백업 부담 ↑ 가치 ↓ → 백업 미대상.

---

## 3. 백업 저장 위치 (3계층)

### 3-1. 1차: 외부 드라이브 (오프라인)

- 위치: 사용자 보유 외부 HDD/SSD (예: `E:\backup\affiliate_hub\`)
- 빈도: 일 1회 (SQLite) / 월 1회 (사진·secrets)
- 사용 시점: 평상 복구
- 암호화 [추정]: secrets만 암호화 (7z + 패스워드 또는 VeraCrypt 컨테이너)

### 3-2. 2차: 클라우드 (개인)

- 옵션 후보 [추정, Phase 1 선택]:
  - Google Drive
  - 네이버 MYBOX
  - 마이크로소프트 OneDrive
- 빈도: 월 1회 (SQLite·secrets·사진)
- 사용 시점: 외부 드라이브 손상 시
- 암호화: secrets는 반드시 암호화 (개인 클라우드도 침해 가능)

### 3-3. 3차: GitHub (공개 저장소, 비-secrets만)

- 위치: github.com/<user>/honsalim (또는 affiliate_hub)
- 백업 자동: 코드·docs·manifest.json·static/photos/ (Git 추적 항목)
- secrets·DB·logs는 절대 X (POLICY §10-3 .gitignore)
- 사용 시점: 코드만 필요한 부분 복구

### 3-4. 3계층 원칙

- **데이터 자산 (DB·secrets·사진)**: 1차 + 2차 (오프라인 + 클라우드)
- **코드 자산**: 3차 (Git) + 로컬 D 드라이브 자동
- 동일 자산이 3곳 모두에 있으면 한 곳 손실 시에도 복구 가능

---

## 4. SQLite DB 백업 (#1, 가장 중요)

### 4-1. 일별 자동 백업

| 작업 | 명령 (개념) | 시간 |
|------|-----------|------|
| online backup (서비스 중단 없음) | `python -m honsalim db backup --target E:\backup\affiliate_hub\daily\` | 04:30 KST |
| 저장 파일명 | `honsalim_YYYY-MM-DD.db` | 일별 |
| 보관 일수 | 30일 (이후 자동 삭제) | — |

SQLite `BACKUP` 명령 사용 (Python `sqlite3.Connection.backup()`).

### 4-2. 주별 풀 백업

- 매 일요일 새벽
- 외부 드라이브 + 클라우드 (2차) 둘 다
- 추가로 `data/manifest.json`·`static/photos/` 동기 (rsync 또는 robocopy)

### 4-3. 백업 검증

- 매 백업 후 `PRAGMA integrity_check` 자동 실행
- 결과 PASS 아닐 시 logs ERROR + STATE.md 치명 기록

### 4-4. 복구 절차

```
[복구 명령 — 사용자 실행]
1. logs로 손상 시점 확인
2. 외부 드라이브에서 최근 정상 백업 선택
3. python -m honsalim db restore --source E:\backup\affiliate_hub\daily\honsalim_2026-06-14.db
4. PRAGMA integrity_check 확인
5. dashboard로 글 수·상태 확인
6. manifest 재생성 (python -m honsalim build --full)
```

복구 후 누락된 글은 손실 (백업 시점 이후 변경).

---

## 5. 사용자 직접 사진 백업 (#2)

### 5-1. 사진의 가치 [추정]

- 진실성 게이트 핵심 자산 (POLICY §3-1-3)
- 재촬영 어려움 (시간 경과 후 동일 환경 재현 불가)
- 손실 시 글 발행 차질

### 5-2. 백업 정책

| 트리거 | 작업 |
|--------|------|
| 신규 사진 추가 시 | 외부 드라이브 즉시 사본 (수동) |
| 월 1회 | static/photos/ → 클라우드 동기 |
| 분기 1회 | 백업본 무결성 (랜덤 10장 열어서 확인) |

### 5-3. 폴더 구조

```
static/photos/
├── 2026/
│   ├── 06/
│   │   ├── homeoffice-desk-natural-light-1.webp
│   │   ├── homeoffice-desk-natural-light-1.jpg   ← 원본 보관
│   │   ├── homeoffice-desk-natural-light-1.meta.json   ← alt·라이선스
│   │   └── ...
│   └── ...
└── ...
```

- 원본 JPG 보존 (재최적화 가능)
- 변환된 WebP는 Git에 포함 (저용량)
- 메타 JSON은 DB §9 `images` 테이블 입력 자료

### 5-4. 복구

- 외부 드라이브 → `static/photos/` 복사
- DB `images` 테이블이 정상이면 자동 매핑 복원

---

## 6. secrets 백업 (#3)

### 6-1. 가장 민감 — 암호화 필수

- 원본: `D:\secrets\affiliate_hub\`
- 백업: 1차·2차 모두 **암호화 컨테이너** 안에 보관
- 권장 도구:
  - 7z + 패스워드 (간단)
  - VeraCrypt 컨테이너 (강력)

### 6-2. 백업 빈도

| 트리거 | 작업 |
|--------|------|
| 자격증명 회전 시 | 즉시 외부 드라이브 갱신 |
| 월 1회 | 클라우드 동기 |

### 6-3. 패스워드 관리

- 사용자가 직접 관리 (Claude·코드 접근 금지)
- 1Password·Bitwarden 등 패스워드 매니저 권장 [추정]
- 패스워드 분실 시 모든 자격증명 재발급 (회복 절차 §10)

### 6-4. 복구

```
1. 외부 드라이브에서 secrets_2026-06-15.7z 복사
2. 7z extract (패스워드 입력)
3. D:\secrets\affiliate_hub\에 배치
4. python -m honsalim doctor로 전 키 검증
```

---

## 7. GitHub 저장소 백업 (#4)

### 7-1. Git 자동

- 매 push 시 GitHub remote가 사실상 백업
- main 브랜치 보호 (Settings → Branches) 권장
- force push 금지 (`H4` [확정] 사용자 승인 + 일반 push만)

### 7-2. 로컬 ↔ GitHub 동기

- 매 변경 후 즉시 push 권장 (사용자 승인 시)
- `/honsalim-end` 자동 commit 1회 (H3 [확정])
- push는 별도 사용자 승인 필요 (H4 [확정])

### 7-3. 저장소 자체 손실 시

- GitHub 측 사고 (극히 드문) [관찰]
- 로컬 .git이 있으면 새 remote에 push로 즉시 복구
- 로컬·remote 둘 다 손실 시 외부 드라이브 백업의 코드 사본 사용

### 7-4. 저장소 백업 옵션 (Phase 4) [추정]

- GitHub Enterprise Backup Util (개인 미적용)
- 단순 git clone 미러를 월 1회 외부 드라이브에 추가 보관 검토

---

## 8. Cloudflare D1 백업 (#5)

### 8-1. 월 1회 export

```
wrangler d1 export honsalim-clicks --output backup/d1_clicks_YYYY-MM.sql
```

저장 위치:
- 외부 드라이브 `E:\backup\affiliate_hub\d1\`
- 클라우드 2차 동기

### 8-2. clicks 90일 회전 ↔ 백업 시점

- POLICY §14-1: clicks 원본은 90일 후 자동 DELETE
- 백업은 그 이전에 export 의무 (월 1회면 충분)
- clicks_daily는 12개월 보관 (long-term)

### 8-3. 복구 (희귀)

- D1 자체 다운은 거의 없음 [관찰]
- 손상 시 wrangler d1 import로 복구
- 누락된 클릭은 재현 불가 (logs로 보간 X)

---

## 9. Cloudflare R2 백업 (#6, Phase 4+) [추정]

### 9-1. 초기 미사용

- Phase 1~3은 `static/images/` Pages 정적 자산 (Git 추적)
- 10GB 한도까지 R2 미사용 가능

### 9-2. R2 사용 시 백업 (Phase 4+)

```
wrangler r2 object list honsalim-images
wrangler r2 object get ... → 외부 드라이브
```

또는 S3-compatible 클라이언트 (rclone) 사용.

### 9-3. 빈도

- 월 1회
- 사진 변경 빈도 낮으므로 차분 동기 (rclone)

---

## 10. 복구 리허설 (분기 1회)

### 10-1. 목적

- 실제 백업이 복구 가능한지 검증
- 사용자가 절차에 익숙해지도록
- 백업 누락·손상 조기 발견

### 10-2. 절차

| 단계 | 작업 |
|------|------|
| 1 | 분기 첫 달 1일 새벽에 분리된 임시 폴더 생성 (`D:\affiliate_hub_test_restore\`) |
| 2 | 어제 백업 DB·secrets·사진 일부 복원 |
| 3 | python -m honsalim doctor → 전 키 OK |
| 4 | python -m honsalim build --full → build/ 생성 확인 |
| 5 | 로컬 미리보기 → 글 N편 정상 표시 확인 |
| 6 | 결과 EVENTS.md 다음 세션에 기록 |
| 7 | 임시 폴더 삭제 |

### 10-3. 리허설 fail 시

- 즉시 백업 절차 점검
- 누락 자산 식별·재백업
- STATE.md에 백업 상태 기록

---

## 11. 재난 복구 (D 드라이브 손실)

### 11-1. 시나리오

- D 드라이브 물리 손상 (HDD/SSD 고장)
- 영향: `D:\affiliate_hub\` + `D:\secrets\affiliate_hub\` 둘 다 손실 가능
- 단, GitHub와 외부 드라이브는 무사

### 11-2. 복구 절차 (1~2일 예상)

| 단계 | 작업 | 예상 시간 |
|------|------|---------|
| 1 | 새 드라이브 마운트·Python 3.10 설치 | 1~2시간 |
| 2 | GitHub에서 코드 clone → D:\affiliate_hub\ | 30분 |
| 3 | pip install -e . | 10분 |
| 4 | 외부 드라이브에서 secrets 복호화 → D:\secrets\affiliate_hub\ | 10분 |
| 5 | 외부 드라이브에서 honsalim.db 최신 → data\ | 5분 |
| 6 | 외부 드라이브에서 static/photos/ 최신 → 동일 위치 | 10분 |
| 7 | python -m honsalim doctor 전체 OK | 5분 |
| 8 | python -m honsalim build --full → 미리보기 | 5분 |
| 9 | 로컬에서 사이트 정상 인지 확인 → 사용자 안심 | 10분 |
| 10 | 향후 발행은 새 드라이브에서 진행 | — |

### 11-3. 클라우드만으로 복구 (외부 드라이브도 손실 시)

- 2차 클라우드 백업이 있으면 동일 절차
- 클라우드 secrets는 암호화 → 패스워드 필요

### 11-4. 모든 백업 손실 시 (최악)

- 코드: GitHub에서 복구 가능 (정상 push 이력)
- DB: 빈 상태에서 재시작. 글 N편이 사이트에 있어도 DB와 disconnect.
  - 대안: 사이트에서 글 스크랩 (자기 사이트 스크랩)
  - 또는 글을 다시 작성 (가능하지만 큰 손실)
- secrets: 모든 자격증명 재발급 (도메인은 갱신 가능, API 키 회전)
- 사진: 재촬영 (어려움)
- → **이 시나리오 방지가 백업 정책의 핵심.**

---

## 12. 백업 자동화 (Phase 2 [추정])

### 12-1. 일별 자동화

`src/scripts/daily_backup.py` 또는 OS 작업 스케줄러:

```
1. SQLite online backup → E:\backup\affiliate_hub\daily\honsalim_<date>.db
2. PRAGMA integrity_check
3. 30일 초과 daily 백업 자동 삭제
4. 결과 logs/honsalim.log INFO 기록
```

OS 작업 스케줄러 (Windows): 일 04:30 KST 트리거.

### 12-2. 월별 자동화

`src/scripts/monthly_backup.py`:

```
1. SQLite full + manifest + static/photos/ → 외부 드라이브 + 클라우드 동기
2. secrets는 사용자 수동 확인 (자동화 안 함, 보안)
3. D1 export → 외부 드라이브
4. 백업 결과 STATE.md "백업 상태" 행 갱신
```

### 12-3. 자동화 미적용 항목

- secrets 백업은 **수동** (자동화 시 패스워드 노출 위험)
- 복구 리허설은 **수동** (자동화 의미 없음)

---

## 13. 백업 모니터링

### 13-1. STATE.md "백업 상태" 섹션 [추정]

```
## 백업 상태 (월 1회 갱신)
| 자산 | 최근 백업 | 위치 | 상태 |
|------|----------|------|------|
| SQLite DB | 2026-06-15 04:30 | E:\backup\ + GDrive | OK |
| 사진 | 2026-06-01 | E:\backup\ | OK |
| secrets | 2026-06-01 | E:\backup\ 암호화 | OK |
| D1 export | 2026-06-01 | E:\backup\ | OK |
```

### 13-2. 결손 알림

- 일별 백업 fail → dashboard 빨간 배너 + STATE.md
- 월별 백업 7일 누락 → 동일

---

## 14. 다음 단계

BACKUP.md 사용자 검토 → 승인 후 **MAINTENANCE.md (유지보수·확장)** 작성 진입.

MAINTENANCE.md에서 확정할 핵심:
- 의존성 업데이트 정책 (anthropic·jinja2·pillow 등)
- 보안 패치·CVE 대응 절차
- 신규 페르소나·시나리오 확장 절차
- 신규 어필리에이트 (알리·기타) 도입 절차
- 사이트 마이그레이션 시나리오 (Cloudflare → 타사)
- 영어 확장 시 (hreflang·번역) 절차
- 디자인 갱신 (Claude Design 재시안) 절차
- 코드 리팩토링·기술 부채 관리

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (백업 7대상·3계층·복구 리허설·재난 시나리오) | Claude Opus 4.7 |
