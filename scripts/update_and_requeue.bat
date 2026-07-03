@echo off
REM 세션 #41 — 코드 최신화(git pull) + 검증 반려로 막힌 키워드 재시도 복귀. 주인 더블클릭용.
REM 대상: 최신 글이 '검증 반려'인 키워드만 (직접 반려한 글·발행된 글은 안전하게 제외).
REM 쿠팡 배너는 그대로 보존. 멱등(여러 번 실행해도 무해). 기존 cleanup 런처와 동일 패턴.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0\.."
echo === [1/2] 코드 최신화 (git pull) ===
git pull --ff-only
if errorlevel 1 echo [주의] git pull 실패 - 현재 코드로 계속 진행합니다.
echo.
echo === [2/2] 반려 키워드 재시도 복귀 ===
set PYTHONPATH=src
python -m cli keyword-requeue
echo.
echo 끝. 대시보드가 켜져 있으면 껐다 켜세요 (새 버튼·카운터 반영).
echo 다음 예약 시각(현재 11:11)에 자동으로 다시 생성·검증·발행됩니다.
pause
