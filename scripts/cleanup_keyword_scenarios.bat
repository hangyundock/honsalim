@echo off
REM 키워드 파생 가짜 시나리오 정리 + 흡수 글 비공개 (세션 #35) — 주인 더블클릭용 일회성 런처.
REM 운영 폴더(D:\affiliate_hub)에서 실행. 실행 전 DB 자동 백업, 멱등(재실행 무해).
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0\.."
echo === honsalim cleanup (scenarios + absorbed article) ===
python scripts\cleanup_keyword_scenarios.py
echo.
echo (끝나면 대시보드에서 '빌드.배포'를 눌러 라이브 반영하세요)
pause
