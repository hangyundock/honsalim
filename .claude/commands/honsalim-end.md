# /honsalim-end — 혼살림 세션 종료

`D:\affiliate_hub\` 프로젝트 세션 종료 시 실행.

작업 순서:

## 1. STATE.md 갱신 (변경 영역만)
- 진행 단계 / 설계 문서 진척
- 사이트 게시글 수 / 트래픽 / 수익 (Phase 4 이후)
- 잔존 미해결 갱신 (해결된 항목 제거·신규 추가)

## 2. TODO.md 갱신
- 완료 항목 제거
- 신규 작업 추가
- 우선순위 재정렬

## 3. DECISIONS.md 갱신
- 새 [확정] 사실 있으면 카테고리(A~H) 분류 후 추가
- 옛 [확정] 뒤집어진 경우: ~~취소선~~ + 세션 번호 + 새 항목

## 4. EVENTS.md 새 세션 블록 append
- 형식: `### 세션 #N — YYYY-MM-DD (모델, 한 줄 요약)`
- 본문 4섹션:
  - 시작 상황
  - 실행 결과 (등급 명시 [확정]/[관찰]/[추정])
  - 잔존 미해결
  - 다음 세션 할 일

## 5. ★ 자동 회전 검사 (EVENTS.md 본문 세션 개수 >= 6)
- 가장 옛 세션 1줄 요약 추출
- 원문은 `docs/archive/EVENTS_YYYYMM.md`에 append
- EVENTS.md 본문에서 그 세션 삭제
- EVENTS.md "ARCHIVE 인덱스"에 1줄 요약 추가

## 6. Size cap 점검
- STATE.md > 10KB → 갱신 누락 항목 점검 보고
- EVENTS.md > 20KB → 단일 세션 비대 점검
- TODO.md > 5KB → 옛 작업 정리

## 7. ★ 자동 commit + push (DECISIONS N1 [확정 #9])
- `git add -A` (`.gitignore` 제외 파일만)
- `git commit -m "[YYYY-MM-DD #N] <한 줄 요약>"`
- **자동 `git push origin main`** — `/honsalim-end` 호출 자체가 사용자 명시 승인
- push 실패 시 (CI fail · branch protection 충돌 등) 사용자 보고 + 다음 세션 재시도
- **force push·rebase·reset 등 destructive op는 절대 자동 금지** (`.claude/settings.json` deny rule)

## 8. 사용자 보고
- 갱신된 파일 목록
- 새 세션 번호
- 자동 회전 발생 여부 + archive 추가 내용
- 다음 세션 시작 명령 (`/honsalim-start`) 안내

## 규칙
- 보고만 절대 X. 실제 파일 변경.
- 변경 후 read 검증.
- 비개발자 친화 — diff 요약만 채팅 출력.
- 외부 배포(Cloudflare Pages 등) 매번 명시 승인. 본 명령의 `git push origin main`은 호출 자체가 승인 (DECISIONS N1).
- force push·rebase·reset 등 destructive op는 절대 자동 금지.
