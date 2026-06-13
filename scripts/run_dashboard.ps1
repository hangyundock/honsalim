# run_dashboard.ps1 — 혼살림 운영 대시보드 실행 (세션 #25)
# 콘솔에서 실행 시 사용. 바탕화면 바로가기는 launch_dashboard.vbs(콘솔 없이) 권장.

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$env:PYTHONPATH = "src"
python -m dashboard.app
