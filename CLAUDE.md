# CLAUDE.md — 혼살림(Honsalim) 핸드오프 규칙

> D:\affiliate_hub\ 프로젝트 표준 지시 파일. 매 세션 자동 로드.
> 출처: D:\templates\CLAUDE_PROJECT_SETUP.md §3 템플릿 + 본 프로젝트 결정 사항 (§8.6 어필리에이트 유형 적용).

---

## 1. 사용자 정체성

- 사용자(주인)는 **비개발자**.
- 모든 코드는 Claude 작성·수정. 사용자는 검토·승인만.
- 사용자 한국어로 소통. Claude도 기본 한국어로 응답.

## 2. 핵심 작업 규칙

### (가) 비개발자 친화 출력
- 코드 직접 출력 금지. 결과만 핵심 요약.
- 파일 변경은 filesystem 도구로 직접 + diff 요약만.
- 사용자에게 PowerShell 코드 복붙·실행 시키지 않음.
- 슬래시 명령(`/honsalim-start` 등)은 사용자 직접 입력이라 노출 가능.

### (나) 추측 금지
- 모르면 "모르겠다". 출처 없으면 "출처 없음".
- 등급 명시: [확정] / [관찰] / [추정] / [확인 불가]

### (다) 변경 전 승인
1. 요약 보고 → 2. 사용자 확인 → 3. dryRun(가능 시) → 4. 적용 → 5. read 검증

### (라) 안전 규칙
- 외부 게시(Cloudflare Pages 배포 등) 매번 명시 승인
- **git push**: `/honsalim-end` 호출 시 자동 (호출 자체가 사용자 명시 승인). 그 외 시점은 명시 승인 후만. force push·rebase·reset 등 destructive op는 절대 자동 금지 (DECISIONS N1 [확정 #9])
- 어필리에이트 게시: 자동 검증 게이트 통과 후 사용자 1클릭 승인 패턴
- 본인·가족 구매 금지 (쿠팡·알리 양사)
- 자동 실행·납치 광고 금지 (쿠팡 30일 수익 몰수 [확정 ZDNet 2025-10-03])
- secrets `D:\secrets\affiliate_hub\` 접근 금지 (코드 절대 nointeraction)
- 외부 단축 URL 금지 (Vivoldi 등 회색지대)

### (마) 인간 편집 게이트 (콘텐츠 게시 직전)
1. Claude 자동 검증: 진실성·Schema·공정위 disclosure·링크 무결성
2. 자동 검증 통과 → 사용자 대시보드에서 미리보기 검토
3. 사용자 1클릭 승인 → 빌드·배포
4. **자동 승인 절대 금지** (Google Helpful Content 패널티 회피)

## 3. 5파일 시스템 (CTX 과밀 근본 해결책 적용)

| 파일 | 역할 | Cap |
|------|------|-----|
| `CLAUDE.md` | 본 파일 (정적 규칙) | 무제한 |
| `docs/STATE.md` | 동적 운영 상태 | 10KB |
| `docs/DECISIONS.md` | 영구 [확정] | 무제한 |
| `docs/TODO.md` | 활성 작업 | 5KB |
| `docs/EVENTS.md` | 세션 로그 (최근 5세션) | 20KB·자동 회전 |
| `docs/archive/` | 자동 회전 archive | — |

매 세션 자동 로드: STATE + EVENTS + (필요 시) DECISIONS/TODO

## 4. 매 세션 필독

1. `docs/STATE.md` (가장 자주 변하는 정보)
2. `docs/EVENTS.md` (최근 5세션 로그)
3. `docs/DECISIONS.md` (필요 시 검색)

→ 시작은 `/honsalim-start` 슬래시 명령.

## 5. 모델 선택

- 권장: `/model opusplan` (Plan=Opus, Execution=Sonnet 자동 전환)
- Plan Mode: `Shift+Tab` 순환

## 6. 프로젝트 개요

- **사이트명**: 혼살림 (Honsalim)
- **도메인**: honsalim.com (예정, Cloudflare Registrar)
- **분야**: 1인 가구·자취·홈오피스·일상살림 어필리에이트 (비YMYL)
- **컨셉**: 시나리오 추천 + 미니멀+따뜻함
- **수익**: 쿠팡 파트너스(메인) + AliExpress(보조). AdSense 6개월 후 결정.
- **기술 스택**: Python 3.10 + Jinja2 직접 빌더 + Cloudflare Pages + SQLite + Claude API (Haiku)
- **빌드**: GitHub Actions (공개 저장소, Linux Python 3.10)
- **배포**: wrangler pages deploy (Direct Upload)
- **DB**: `data/honsalim.db` (SQLite)
- **로그**: `logs/honsalim.log`
- **secrets**: `D:\secrets\affiliate_hub\` (코드 저장소 절대 금지)

## 7. 운영 모델 — 세션 #2 갱신

- **자동 게시 활성 (윈도우 스케줄러)** — 사용자 1클릭 승인된 큐를 매일 11:00 KST에 1편 published 전이 + 빌드 + 배포 (DECISIONS C6·C7)
- **자동 "승인"은 절대 금지** — Google Helpful Content 패널티 회피 (E7 [확정]). AdSense 신청 여부와 무관하게 검색 노출 보호
- **콘텐츠 페이스**: 큐 기반 + 사용자 작성 역량 내 최대 (DECISIONS C8). 큐 비면 자동 정지 + dashboard 알림. 시즌 2개월 사전 발행
- **검증 게이트 자동**: 진실성·Schema·disclosure·링크
- **사용자 검토**: 대시보드 미리보기 → 1클릭 승인 → 큐 진입 → 스케줄러 발행

## 8. 시간 민감 제약 — 세션 #2 갱신

- AutoBlog(D:\autoblog\) 자동 게시 시간대(매일 09:00~10:30)는 별개 프로젝트
- 본 프로젝트 자동 게시: **매일 11:00 KST** (AutoBlog와 30분 이상 간격, DECISIONS C7)
- 윈도우 스케줄러 작업 등록은 Phase 1·2 시점
- 큐가 있을 때만 자동 발행, 큐 비면 자동 정지

## 9. 프로젝트 고유 함정

→ `docs/DECISIONS.md` 카테고리 A~H 참조. 필요 시 grep.

핵심 함정 5개:
1. AI 100% 자동 게시 → Google Helpful Content 패널티 위험 (2024-03 사례)
2. 쿠팡 외부 단축 URL 사용 → 회색지대, 일괄 차단 가능
3. 쿠팡 CDN 상품 이미지 다운로드 → 저작권 회색지대
4. 첫머리 대가성 문구 누락 → 공정위 위반 + 쿠팡 수익 몰수
5. 본인·가족 구매 → 부정행위 적발 시 계정 해지

## 10. 보조 파일 (필요 시)

- `docs/PLAN.md` — 비전·KPI·로드맵 (완성, 2026-05-27)
- `docs/ARCH.md` — 시스템 아키텍처 (예정)
- `docs/DB.md` — DB 스키마 (예정)
- `docs/SCENARIOS.md` — 시나리오 명세 (예정)
- `docs/DESIGN.md` — 디자인 시스템 (예정)
- `docs/FRONTEND.md` — 페이지·CWV·SEO·Schema (예정)
- `docs/BACKEND.md` — 모듈·API·빌드 (예정)
- `docs/POLICY.md` — 공정위·진실성·보안 (예정)
- `docs/OPS.md` — 운영·로깅·장애 (예정)
- `docs/BACKUP.md` — 백업·복구 (예정)
- `docs/MAINTENANCE.md` — 유지보수·확장 (예정)
- `docs/SCHEDULE.md` — Phase·체크포인트 (예정)

## 11. Git 운영

- **GitHub 공개 저장소** (Actions 무제한 [확정 GitHub])
- 저장소 URL: (생성 후 추가)
- `.gitignore` 엄격 — secrets/data/build/.env/*.pickle 제외
- 커밋 패턴: `[YYYY-MM-DD #N] <한 줄>`
- `/honsalim-end` 자동 commit 1회
- **자동 push**: `/honsalim-end` 호출 시만 (commit + push 일괄). 그 외 시점은 명시 승인 후만
- **force push·rebase·reset 등 destructive op는 절대 자동 금지** (DECISIONS N1 [확정 #9])

## 12. 실행 환경

- Python: 3.10 (32-bit, 시스템 Python, TIMA·AutoBlog 공유) — 환경 변경 금지
- 가상환경 미사용
- 인코딩: 모든 .py / .md UTF-8

## 13. 변경 이력

| 날짜 | 변경 | 작성자 |
|------|------|--------|
| 2026-05-27 | 최초 작성 (CLAUDE_PROJECT_SETUP §3 템플릿 기반, 혼살림 결정사항 반영, 5파일 시스템 적용) | Claude Opus 4.7 |
