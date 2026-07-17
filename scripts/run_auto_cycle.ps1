# run_auto_cycle.ps1 — ★무인 자동 사이클 래퍼 (B-i·세션 #29)
#
# 윈도우 작업 스케줄러가 매일 설정 시각에 호출(주인이 직접 등록 — C13 예약은 주인 통제).
# auto-cycle = 사후모니터 → 대기키워드 생성 → fail-closed 자동승인 → 발행. 메인 체크아웃에서 실행.
#
# ★ auto_mode(config.json) ON일 때만 실제 동작 — OFF(기본)면 즉시 안전 정지(사람 게이트 E7 유지).
#   생성 단계는 DeepSeek 비용 발생(publish_per_day 상한). 안전(§0): 메인 브랜치 + DB 존재 시에만 가동.

$ErrorActionPreference = "Stop"

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
try {
    & git pull --ff-only origin main 2>&1 | ForEach-Object { Write-Log "pull: $_" }
} catch {
    Write-Log "git pull 실패(무시·계속): $_"
}

# 4) 자동 사이클 (auto_mode ON일 때만 생성·승인·발행 — OFF면 cli가 즉시 중단)
Write-Log "auto-cycle --no-dry-run 실행"
$out = & python -m cli auto-cycle --no-dry-run 2>&1
$code = $LASTEXITCODE
foreach ($line in $out) { Write-Log "cli: $line" }
Write-Log "=== 종료 (exit=$code) ==="
exit $code
