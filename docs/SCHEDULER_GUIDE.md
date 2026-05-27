# SCHEDULER_GUIDE.md — 윈도우 작업 스케줄러 등록 가이드

> 비개발자용 단계별 가이드. DECISIONS C6·C7 자동 게시 활성.
> 작성: 2026-05-27 세션 #2.
> 적용 시점: Phase 1·2 (Python 모듈 작성 후).
> 등급: [확정] = Windows 공식·schtasks 표준 / [관찰] = 운영 사례 / [추정] = 본 세션 권장.

---

## 1. 등록 대상

| 작업 | 명령 | 빈도 |
|------|------|------|
| 자동 게시 (큐 1편 발행) | `python -m honsalim scheduler-publish` | 매일 11:00 KST (DECISIONS C7) |
| 일별 D1 집계 | `python -m honsalim tracker --aggregate-daily` | 매일 03:00 KST |
| 일별 DB 백업 | `python -m honsalim db backup` | 매일 04:30 KST (BACKUP §4) |
| 외부 API 헬스 체크 | `python -m honsalim doctor` | 매일 09:00 KST |

본 가이드는 1번 (자동 게시) 중심. 나머지 3개도 동일 패턴.

---

## 2. 사전 조건

| 조건 | 확인 |
|------|------|
| Phase 2 완료 (`python -m honsalim build` 동작) | [ ] |
| 첫 글 1편 dashboard 승인 완료 (큐에 1편) | [ ] |
| Anthropic·쿠팡·Cloudflare 자격증명 활성 (doctor 통과) | [ ] |
| GitHub 저장소 활성·`git push` 작동 | [ ] |

---

## 3. GUI로 등록 (권장 — 비개발자)

### 3-1. 작업 스케줄러 열기

1. Windows 검색창에 `작업 스케줄러` 입력 → 실행
2. 좌측 트리에서 **작업 스케줄러 라이브러리** 클릭

### 3-2. 새 작업 만들기

1. 우측 **작업 만들기...** 클릭 (단순 작업이 아닌 **작업 만들기** 선택)
2. **일반** 탭:
   - 이름: `honsalim-scheduler-publish`
   - 설명: `혼살림 자동 게시 — 매일 11:00 KST 큐 1편 발행`
   - 보안 옵션: **사용자가 로그온할 때만 실행**
   - **가장 높은 수준의 권한으로 실행** 체크 (관리자 권한)

### 3-3. 트리거

1. **트리거** 탭 → **새로 만들기...**
2. 작업 시작: **일정 예약 시**
3. 매일·시작: **오늘 날짜 11:00:00**
4. 매일 반복: **1일 마다**
5. **사용** 체크
6. 확인

### 3-4. 동작

1. **동작** 탭 → **새로 만들기...**
2. 작업: **프로그램 시작**
3. 프로그램/스크립트: `python` (또는 정확한 경로 `C:\Python310\python.exe`)
   - 정확한 경로 확인: PowerShell에서 `Get-Command python | Select-Object Source`
4. 인수 추가: `-m honsalim scheduler-publish`
5. 시작 위치: `D:\affiliate_hub\`
6. 확인

### 3-5. 조건·설정

1. **조건** 탭:
   - **컴퓨터의 AC 전원이 켜져 있는 경우에만** (노트북이면 체크 권장)
   - **이 작업을 실행하기 위해 절전 모드 종료** 체크
2. **설정** 탭:
   - **요청 시 작업 실행** 체크
   - **예약된 시작 시간을 놓친 경우 가능한 한 빨리 작업 시작** 체크
   - **작업이 실패할 경우 다시 시작 시도** 체크 (5분 후 1회)
   - 작업이 다음보다 오래 실행되면 중지: **30분**

### 3-6. 저장·테스트

1. 확인 → 비밀번호 입력 (Windows 로그인 비밀번호)
2. 작업 목록에서 `honsalim-scheduler-publish` 우클릭 → **실행** (테스트)
3. logs/honsalim.log 확인 (`scheduler-publish` 로그 기록 확인)

---

## 4. PowerShell로 등록 (대안)

GUI 대신 PowerShell 1줄로 가능 [확정 — Microsoft Learn].

```powershell
# PowerShell 관리자 권한으로 실행
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "-m honsalim scheduler-publish" `
  -WorkingDirectory "D:\affiliate_hub\"

$trigger = New-ScheduledTaskTrigger -Daily -At 11:00AM

$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -RestartCount 1 `
  -RestartInterval (New-TimeSpan -Minutes 5) `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
  -TaskName "honsalim-scheduler-publish" `
  -Description "혼살림 자동 게시 매일 11:00 KST" `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -RunLevel Highest
```

---

## 5. 작업 확인·관리

| 작업 | GUI | PowerShell |
|------|-----|-----------|
| 상태 확인 | 작업 스케줄러 → 라이브러리 | `Get-ScheduledTask -TaskName honsalim-scheduler-publish` |
| 즉시 실행 | 우클릭 → 실행 | `Start-ScheduledTask -TaskName honsalim-scheduler-publish` |
| 일시 정지 | 우클릭 → 사용 안 함 | `Disable-ScheduledTask -TaskName honsalim-scheduler-publish` |
| 삭제 | 우클릭 → 삭제 | `Unregister-ScheduledTask -TaskName honsalim-scheduler-publish` |
| 최근 실행 결과 | 일반 탭 → 마지막 실행 결과 | `Get-ScheduledTaskInfo -TaskName honsalim-scheduler-publish` |

---

## 6. 실패 시 진단

| 증상 | 원인 후보 | 확인 |
|------|----------|------|
| 11:00에 실행 안 됨 | 컴퓨터 절전·전원 OFF | 작업 조건의 절전 모드 종료 옵션 |
| 시작했지만 즉시 종료 | python 경로 오류 | 동작 탭의 정확한 python.exe 경로 |
| Python 실행되나 에러 | 의존성·secrets·DB 누락 | logs/honsalim.log + `python -m honsalim doctor` |
| 큐 비어서 멈춤 | 정상 (DECISIONS C8) | dashboard에 "큐 비었음" 알림 확인 |
| 빌드 성공 but 배포 실패 | git push·wrangler 인증 만료 | doctor 명령으로 외부 인증 점검 |

logs 위치: `D:\affiliate_hub\logs\honsalim.log`

---

## 7. AutoBlog와의 시간대 충돌 회피 (CLAUDE §8)

| 시각 | 프로젝트 | 작업 |
|------|---------|------|
| 09:00~10:30 KST | AutoBlog | 자동 게시 (별도 프로젝트) |
| **11:00 KST** | **혼살림** | **자동 게시 (큐 1편)** |
| 03:00·04:30·09:00 | 혼살림 (보조) | 집계·백업·헬스 체크 |

30분 이상 간격이므로 시스템 부하 분산 [추정].

---

## 8. 자동 게시가 의미하는 것 (재확인)

POLICY §13-0:
- 자동 "게시" = approved 상태 → published 전이 + 빌드 + 배포 (스케줄러)
- 자동 "승인" = ❌ **절대 금지**. validated → approved 전이는 **사용자 1클릭만 가능**

스케줄러는 큐에 있는 (= 이미 사용자가 승인한) 글만 발행. 큐가 비면 즉시 정지·dashboard 알림.

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (GUI·PowerShell 양방향 + 진단) | Claude Opus 4.7 |
