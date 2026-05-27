# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **Phase 0: 설계 완료 → Phase 1 인프라 대기** | #2 (2026-05-27) |
| 운영 모델 갱신 (세션 #2 후반) | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건 + GitHub 보안 다중 방어 | #2 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (PLAN·ARCH·DB·SCENARIOS·DESIGN·FRONTEND·BACKEND·POLICY·OPS·BACKUP·MAINTENANCE·SCHEDULE + SUMMARY 비개발자 요약) | #2 |
| 일관성 점검 | ✅ 모순 0건 (167+73+44+34+211+43회 일관 인용) | #2 |
| 사전 작성 SQL | `sql/migrations/001_initial_schema.sql` + `sql/seeds/001_personas_scenarios.sql` | #2 |
| 사전 작성 설정 (세션 #2 추가) | `.gitignore` + `.pre-commit-config.yaml` + `.claude/settings.json` + `build_headers_draft.txt` + `docs/SCHEDULER_GUIDE.md` + `docs/VALIDATOR_PATTERNS.md` + `docs/REVIEW_QUESTIONS.md` | #2 |
| 사전 작성 코드 (세션 #2 추가) | `src/enricher/prompt_templates/` 6개 .md (system_base·article_main·meta_extract·faq_generate·product_recommendation_note·tone_examples) + `src/`·`tests/`·`templates/`·`static/`·`data/` 빈 폴더 + `.gitkeep` | #2 |
| 사전 작성 인프라 (세션 #2 옵션 A) | `pyproject.toml` + `wrangler.toml` + `.github/workflows/build.yml` + `lint.yml` + `README.md` + `docs/CHANGELOG.md` | #2 |
| 메모리 시스템 | feedback 2건 (no-speculation·same-session-continuity) + MEMORY.md 인덱스 | #2 |
| DECISIONS E7 정정 | YouTube 16채널 사례는 HCS와 별개임을 명시·HCS 공식 정보로 갱신 | #2 |
| 5파일 운영 시스템 | ✅ 구축 완료 | #1 |
| 슬래시 명령 (start/save/end) | ✅ 등록 완료 | #1 |
| 사이트 게시글 수 | 0편 (사이트 미오픈) | #2 |
| 트래픽 | N/A | #2 |
| 수익 | N/A | #2 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` |
| docs 폴더 | `D:\affiliate_hub\docs\` |
| archive 폴더 | `D:\affiliate_hub\docs\archive\` |
| 슬래시 명령 | `D:\affiliate_hub\.claude\commands\` |
| 사이트명 | 혼살림 (Honsalim) |
| 도메인 | honsalim.com (구매 전, Phase 1) |
| 호스팅 | Cloudflare Pages (계정 미생성, Phase 1) |
| GitHub 저장소 | 미생성 (Phase 1) |
| Python 환경 | 3.10 32-bit (시스템 공유, TIMA·AutoBlog 동일) |
| DB | `data/honsalim.db` (미생성, Phase 2) |
| 로그 | `logs/honsalim.log` (미생성, Phase 2) |
| secrets | `D:\secrets\affiliate_hub\` (미생성, Phase 1) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 발급 | 만료 | 갱신 |
|---------|------|------|------|
| (아직 없음 — Phase 1에서 발급) | — | — | — |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 룰 | 미설정 (Phase 1 POLICY §10-2 기준) |
| `D:\secrets\affiliate_hub\` 격리 | 미생성 (Phase 1) |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션)
1. 12개 설계 문서 사용자 검토 (특히 핵심 결정 사항 — 4개 결정 포인트 / 5개 결정 포인트 등)
2. Phase 1 진입 사용자 명시 OK

### 중간 (Phase 1 인프라, 2026-06)
1. 도메인 honsalim.com 가용성 재확인 + 결제 (Cloudflare Registrar)
2. GitHub 공개 저장소 생성 + 초기 push (사용자 승인)
3. Cloudflare 계정 + Pages 프로젝트 + R2 + D1 + Workers 라우트
4. `D:\secrets\affiliate_hub\` 생성 + 자격증명 보관
5. `.claude/settings.json` deny 룰 설정
6. 쿠팡 파트너스 가입 + Open API 키 발급 (승인 1~3일)
7. Anthropic API 키 (보유) 검증
8. `python -m honsalim doctor` 전체 OK

### Phase 2 핵심 시스템 (2026-06~07)
- 모듈 8개·DB 마이그레이션·Claude 파이프라인·Jinja2 빌더·진실성 게이트·배포·테스트

### Phase 3 디자인·콘텐츠 (2026-07)
- Claude Design 시안 3~5종 (사용자 직접 Pro/Max 구독 활용)
- 템플릿 5종 + partials 18종
- 첫 5~10편 작성·승인·시범 배포

### 보류
- AdSense 신청 결정 (Phase 6, 2026-12)
- 영어 사이트 확장 (Phase 6 검토)
- 보조 호스팅 (GitHub Pages) (Phase 4 검토, MAINTENANCE §10)

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| 2026-06 초 | Phase 1 인프라 구축 시작 |
| 2026-06 중반 | Phase 2 핵심 시스템 |
| 2026-07 중반 | Phase 3 디자인 시안·콘텐츠 |
| 2026-07 말 | Phase 4 첫 출시 (사이트 오픈) |
| 2026-08 | 운영 본격 시작·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 콘텐츠 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) |
| 2027-06 | Phase 7 1년 결산 |
