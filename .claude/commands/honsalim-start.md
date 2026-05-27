# /honsalim-start — 혼살림 세션 시작

`D:\affiliate_hub\` 프로젝트 세션 시작 시 자동 실행.

다음 4개 파일 순서대로 읽고 현재 상태 파악:

1. `D:\affiliate_hub\docs\STATE.md` — 현재 운영 상태 (가장 자주 변동)
2. `D:\affiliate_hub\docs\EVENTS.md` — 최근 5세션 로그
3. `D:\affiliate_hub\docs\DECISIONS.md` 상단 (필요 시 grep)
4. `D:\affiliate_hub\docs\TODO.md` — 활성 작업 목록

규칙:
1. 설명은 핵심만 간략히. 소스 코드 출력 불필요.
2. 추측 금지. 모르면 "모르겠다". 등급 명시 [확정]/[관찰]/[추정]/[확인 불가]
3. 선택 사항 발생 시 추천안 제시 → 사용자 승인/거부
4. 보고만. 절대 파일 수정 금지.

파악 후 보고할 항목:
- 최근 세션 번호와 날짜 (EVENTS 첫 엔트리)
- 진행 단계 / 설계 문서 진척 / 사이트 게시글 수 (STATE)
- "다음 세션 할 일" (EVENTS 마지막 또는 TODO 시급)
- 시급 사안 (캘린더 알림·자격증명 만료)
- size cap 점검 (STATE 10KB / EVENTS 20KB / TODO 5KB) — 초과 시 보고

추가로 오늘 날짜 기준 시간 민감 사안 (도메인 갱신·자격증명 만료·캘린더 알림)을 STATE.md "캘린더 알림" 표 기준 체크해서 보고할 것.
