# run_auto_cycle.ps1 — ★무인 자동 사이클 래퍼 (B-i·세션 #29)
#
# 윈도우 작업 스케줄러가 매일 설정 시각에 호출(주인이 직접 등록 — C13 예약은 주인 통제).
# auto-cycle = 사후모니터 → 대기키워드 생성 → fail-closed 자동승인 → 발행. 메인 체크아웃에서 실행.
#
# ★ auto_mode(config.json) ON일 때만 실제 동작 — OFF(기본)면 즉시 안전 정지(사람 게이트 E7 유지).
#   생성 단계는 DeepSeek 비용 발생(publish_per_day 상한). 안전(§0): 메인 브랜치 + DB 존재 시에만 가동.

$ErrorActionPreference = "Stop"

# ★#47: python은 UTF-8로 출력(cli가 stdout 재구성)하는데 PS가 콘솔 코드페이지(cp949)로
# 디코드해 로그의 한글이 영구히 깨졌다(무인 진단성 훼손 — #47 3일 공백 진단 때 판독 곤란).
# 콘솔 없는 환경(드묾)에서 실패해도 래퍼는 계속(§0).
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Root = Split-Path $PSScriptRoot -Parent
$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Log = Join-Path $LogDir "auto_cycle.log"

function Write-Log($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $Log -Value "[$ts] $msg" -Encoding UTF8
}

# ★안전 정지 시 주인 휴대폰으로 통지(세션 #44 — fail-loud, §0). 무인 중엔 대시보드를 안 보므로
#   조용한 정지가 며칠씩 방치되던 문제(2026-07-08~17 실제 10일 침묵) 근본 대책. 발송은 best-effort —
#   실패해도 래퍼 흐름에 영향 없음(cli notify-alert가 항상 exit 0).
function Send-Alert($msg) {
    try {
        & python -m cli notify-alert "$msg" 2>&1 | ForEach-Object { Write-Log "alert: $_" }
    } catch {
        Write-Log "alert 발송 시도 실패(무시): $_"
    }
}

Write-Log "=== auto-cycle 시작 (root=$Root) ==="
Set-Location $Root
$env:PYTHONPATH = "src"  # notify-alert(common import) + 아래 auto-cycle 공용

# 1) 안전 점검 — 메인 브랜치
try {
    $branch = (& git rev-parse --abbrev-ref HEAD).Trim()
} catch {
    Write-Log "git 사용 불가 — 안전 정지(exit 0)"
    Send-Alert "무인 자동 발행이 멈췄습니다: 운영 폴더에서 git 사용 불가. 자동 발행이 안 됩니다 — PC/저장소 상태 확인이 필요합니다."
    exit 0
}
if ($branch -ne "main") {
    Write-Log "현재 브랜치=$branch (main 아님) — 안전 정지(exit 0)"
    Send-Alert "무인 자동 발행이 멈췄습니다: 운영 폴더가 'main'이 아닌 '$branch' 브랜치입니다. 'main'으로 복귀하기 전까지 매일 발행이 건너뜁니다."
    exit 0
}

# 2) 안전 점검 — DB 존재
$Db = Join-Path $Root "data\honsalim.db"
if (-not (Test-Path $Db)) {
    Write-Log "DB 없음($Db) — 안전 정지(exit 0)"
    Send-Alert "무인 자동 발행이 멈췄습니다: DB 파일이 없습니다($Db). 자동 발행이 안 됩니다 — 복구가 필요합니다."
    exit 0
}

# 3) 최신 코드 자기 갱신(best-effort)
# ★#47 근본수정: 옛 try/catch는 EAP=Stop + 2>&1 조합에서 git의 정상 진행 메시지("From ...",
# stderr 출력)가 예외로 승격돼 **매일 "git pull 실패"로 기록**됐다(성공/실패 판별 불능 —
# origin 전진 시 자기갱신이 침묵 실패하면 다음날 발행 push가 비FF 거부로 정지하는 경로).
# stderr를 예외로 만들지 않게 EAP를 잠시 낮추고, 성패는 $LASTEXITCODE로만 판정한다.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$pullOut = & git pull --ff-only origin main 2>&1
$ErrorActionPreference = $prevEap
foreach ($line in $pullOut) { Write-Log "pull: $line" }
if ($LASTEXITCODE -ne 0) {
    Write-Log "git pull 실패(exit=$LASTEXITCODE) - 무시하고 계속(원격 전진 상태면 발행 push가 거부될 수 있음)"
} else {
    Write-Log "git pull 성공(exit=0)"
}

# 4) 자동 사이클 (auto_mode ON일 때만 생성·승인·발행 — OFF면 cli가 즉시 중단)
Write-Log "auto-cycle --no-dry-run 실행"
$out = & python -m cli auto-cycle --no-dry-run 2>&1
$code = $LASTEXITCODE
foreach ($line in $out) { Write-Log "cli: $line" }
# ★#47 fail-loud: cli가 예외로 죽으면(exit≠0) digest·텔레그램 자기보고가 아예 안 나가
# 조용한 실패가 된다(가드 3종만 경보하던 구멍). 발행 실패 rc는 cli도 경보를 보내므로
# 중복될 수 있으나, 침묵보다 중복이 낫다(§0). 발송 실패는 무시(best-effort).
if ($code -ne 0) {
    Send-Alert "무인 자동 발행 사이클이 비정상 종료했습니다(exit=$code). 오늘 발행이 안 됐을 수 있습니다 - logs\auto_cycle.log 확인이 필요합니다."
}
Write-Log "=== 종료 (exit=$code) ==="
exit $code
