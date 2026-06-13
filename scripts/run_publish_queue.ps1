# run_publish_queue.ps1 — 예약 발행 래퍼 (세션 #25)
#
# 윈도우 작업 스케줄러가 매일 설정 시각(config.json schedule_time, 기본 11:00 KST)에 호출.
# 승인된 큐(E7 사람 승인 완료)에서 하루 N편(publish_per_day) 발행→빌드→배포. 메인 체크아웃에서 실행.
# 안전(§0): 메인 브랜치 + DB 존재 시에만 가동, 아니면 안전 정지(로그 후 exit 0).
#
# 등록은 대시보드 "예약 발행" 토글 또는 `python -m cli schedule set` 사용.

$ErrorActionPreference = "Stop"

$Root = Split-Path $PSScriptRoot -Parent
$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Log = Join-Path $LogDir "publish_queue.log"

function Write-Log($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $Log -Value "[$ts] $msg" -Encoding UTF8
}

Write-Log "=== publish-queue 시작 (root=$Root) ==="
Set-Location $Root

# 1) 안전 점검 — 메인 브랜치
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
    Write-Log "DB 없음($Db) — 안전 정지(exit 0)"
    exit 0
}

# 3) 최신 코드 자기 갱신(best-effort)
try {
    & git pull --ff-only origin main 2>&1 | ForEach-Object { Write-Log "pull: $_" }
} catch {
    Write-Log "git pull 실패(무시·계속): $_"
}

# 4) 발행 (승인된 큐에서 N편 → 빌드 → 배포). LLM 미사용(이미 생성·승인된 글).
$env:PYTHONPATH = "src"
Write-Log "publish-queue --no-dry-run 실행"
$out = & python -m cli publish-queue --no-dry-run 2>&1
$code = $LASTEXITCODE
foreach ($line in $out) { Write-Log "cli: $line" }
Write-Log "=== 종료 (exit=$code) ==="
exit $code
