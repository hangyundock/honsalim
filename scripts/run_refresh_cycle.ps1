# run_refresh_cycle.ps1 — 무인 일일 새로고침·자가복원·빌드·배포 래퍼 (A안·세션 #23)
#
# 윈도우 작업 스케줄러가 매일 11:00 KST에 호출(DECISIONS C6·C7). 메인 체크아웃에서 실행.
# 안전(§0): 메인 브랜치 + DB 존재 시에만 가동, 아니면 안전 정지(로그 후 exit 0). 모든 단계 로그.
#
# 등록 예시(관리자 PowerShell, 1회):
#   $A = New-ScheduledTaskAction -Execute "powershell.exe" `
#        -Argument "-NoProfile -ExecutionPolicy Bypass -File D:\affiliate_hub\scripts\run_refresh_cycle.ps1"
#   $T = New-ScheduledTaskTrigger -Daily -At 11:00
#   Register-ScheduledTask -TaskName "honsalim-refresh-cycle" -Action $A -Trigger $T -Description "혼살림 무인 새로고침·배포"

$ErrorActionPreference = "Stop"

# 프로젝트 루트 = 이 스크립트(scripts/)의 부모
$Root = Split-Path $PSScriptRoot -Parent
$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Log = Join-Path $LogDir "refresh_cycle.log"

function Write-Log($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $Log -Value "[$ts] $msg" -Encoding UTF8
}

Write-Log "=== refresh-cycle 시작 (root=$Root) ==="
Set-Location $Root

# 1) 안전 점검 — 메인 브랜치인가
try {
    $branch = (& git rev-parse --abbrev-ref HEAD).Trim()
} catch {
    Write-Log "git 사용 불가 — 안전 정지(exit 0)"
    exit 0
}
if ($branch -ne "main") {
    Write-Log "현재 브랜치=$branch (main 아님) — 안전 정지(exit 0)"
    exit 0
}

# 2) 안전 점검 — DB 존재
$Db = Join-Path $Root "data\honsalim.db"
if (-not (Test-Path $Db)) {
    Write-Log "DB 없음($Db) — 안전 정지(exit 0). db migrate/seed + register-categories 필요"
    exit 0
}

# 3) 최신 코드로 자기 갱신(best-effort, 실패해도 계속)
try {
    & git pull --ff-only origin main 2>&1 | ForEach-Object { Write-Log "pull: $_" }
} catch {
    Write-Log "git pull 실패(무시·계속): $_"
}

# 4) 사이클 실행 (LLM 미사용 → 비용 ~$0). 출력은 로그로.
$env:PYTHONPATH = "src"
Write-Log "refresh-cycle --no-dry-run 실행"
$out = & python -m cli refresh-cycle --no-dry-run --verify-url "https://honsallim.com/" 2>&1
$code = $LASTEXITCODE
foreach ($line in $out) { Write-Log "cli: $line" }
Write-Log "=== 종료 (exit=$code) ==="
exit $code
