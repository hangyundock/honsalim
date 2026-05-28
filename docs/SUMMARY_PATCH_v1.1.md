# SUMMARY_PATCH_v1.1.md — SUMMARY / REVIEW_QUESTIONS 진척 패치

> 출처: 세션 #2 SUMMARY/REVIEW_QUESTIONS 정독 보조용 — 세션 #6 작성.
> 사용: 사용자가 SUMMARY 정독 시 본 문서 cross-ref → 이미 [확정]된 부분 빠른 식별.
> 원본 SUMMARY.md / REVIEW_QUESTIONS.md는 작성 시점 보존 (역사 참조).

---

## 1. SUMMARY §3 결정 매트릭스 — 25 → 45 갱신

원본 SUMMARY §3은 결정 32개 매트릭스(A·B·C·D·E·F·I 7카테고리 32건). 세션 #4·#5에 신규 13건 추가.

### J. Phase 2 아키텍처 — 8건 [확정 세션 #4]

| # | 결정 |
|---|------|
| J1 | 모듈 의존 `writer → validator` 단방향 |
| J2 | state_machine `approved → validated` 보강 |
| J3 | CLI 8/11 활성 (세션 #5 10/11 도달) |
| J4 | `enrich` 기본 `dry_run=True` (API 비용 보호) |
| J5 | JSON-LD 빌더 4 인터페이스 |
| J6 | content_hash 형식 `sha256:<64hex>` |
| J7 | disclosure_first 추출/검증 분리 |
| J8 | payload 책임 호출자 분리 |

### K. 핵심 결정 5건 [확정 세션 #5]

| # | 결정 |
|---|------|
| K1 | manifest 형태 `data/manifest.json` 단일 JSON |
| K2 | 시나리오 우선순위 SCENARIOS §4-11 현 명세 그대로 |
| K3 | 외부 단축 URL 차단 11→13 (`n.kakao.com`·`naver.me`) |
| K4 | 모듈 분리 옵션 B (pyproject.toml flat 정합) |
| K5 | prompt_loader Jinja2 `ChainableUndefined` 채택 |

### L. 1인칭·사진·AI 이미지 정책 — 8건 [확정 세션 #6 2차 재변경]

| # | 결정 |
|---|------|
| L1 | 글 톤 — 위키바이형 3인칭 정보 분석만 (1인칭 액센트도 폐기) |
| L2 | 사진 정책 — **AI 생성 이미지 (Google Imagen 4 Fast) + 쿠팡 공식 위젯** |
| L3 | validator/truth — **1인칭 무조건 차단** (owned_products 메타 우회 폐기) |
| L4 | 벤치마크 차용 — Wirecutter·오늘의집 형식·톤 영감만, 위키바이가 실질 베이스 |
| L5 | E8 폐기 · D5 폐기 (사용자 사진 일체 없음) |
| L6 | Google Imagen 4 Fast 채택 (`imagen-4.0-fast-generate-001`, AutoBlog 패턴 이식) |
| L7 | 글 footer "이미지는 AI 생성 일러스트레이션" 표기 의무 |
| L8 | 상품 이미지 = 쿠팡 공식 위젯 (Imagen 생성 금지) |

**폐기**: E8 (한국어 1인칭 허용) · D5 (시나리오당 사진 의무) · L2/L3 1차 초안.
**참조**: `docs/IMAGE_GENERATION.md` (도구·API·프롬프트·예산 명세).

---

## 2. SUMMARY §5 Phase 일정 — 진척 갱신

원본은 작성 시점(세션 #2) Phase 0 완료 직후. 현 시점(세션 #6, 2026-05-28):

| Phase | 상태 | 비고 |
|-------|------|------|
| Phase 0 설계 | ✅ 100% | 12/12 + SUMMARY (세션 #2) |
| Phase 1 인프라 | ✅ ~95% | GitHub·CF·도메인·R2·D1·secrets·pre-commit·Dependabot — 세션 #2~#3 |
| Phase 2 핵심 시스템 | ✅ ~95% | 모듈 18개 · CLI 10/11 · 회귀 340 PASS · Workers · tracker — 세션 #3~#6 |
| Phase 3 디자인·콘텐츠 | ⏳ 진입 대기 | 사용자 SUMMARY 정독 + Claude Design 시안 |
| Phase 4~7 | ⏳ 일정대로 | 2026-07~ |

---

## 3. SUMMARY §8 Phase 1 사용자 액션 8건 — 완료 상태

| # | 액션 | 상태 |
|---|------|------|
| 1 | GitHub 공개 저장소 | ✅ `hangyundock/honsalim` (세션 #2) |
| 2 | 도메인 honsalim.com 가용성 + 결제 | ✅ Auto Renew, 만료 2027-05-28 |
| 3 | Cloudflare 계정 + Pages·R2·D1·Workers | ✅ 모두 활성 |
| 4 | `D:\secrets\affiliate_hub\` 폴더 | ✅ 운영 중 |
| 5 | 쿠팡 파트너스 가입 + Open API 키 | ⏳ Phase 4 출시 후 |
| 6 | `.gitignore`·`pyproject.toml`·deny 룰 | ✅ Phase 1 작성·검증 |
| 7 | Anthropic API 키 검증 | ✅ doctor `[OK]` |
| 8 | `python -m honsalim doctor` 통과 | ✅ "모든 필수 체크 통과" |

추가 — AliExpress 승인 + Tracking ID + `ali.env` (2026-05-28 세션 #5).

---

## 4. SUMMARY §11 사전 작성 산출물 사용 상태

| 파일 | 사용 상태 |
|------|----------|
| SUMMARY.md | 본 패치 대상 |
| REVIEW_QUESTIONS.md | 본 패치 §6 참고 |
| SCHEDULER_GUIDE.md | Phase 1·2 진행 중 (스케줄러 등록은 코드 완료 후) |
| VALIDATOR_PATTERNS.md | Phase 2 validator 작성 시 사용 — 12 카테고리 모두 코드 반영 [확정] |
| sql/migrations/001_initial_schema.sql | ✅ data/honsalim.db v1 적용 (세션 #3) |
| sql/seeds/001_personas_scenarios.sql | ✅ personas 3 + scenarios 10 적용 (세션 #3) |
| .gitignore | ✅ 적용 |
| .pre-commit-config.yaml | ✅ 9 hook 모두 PASS (gitleaks 대신 detect-secrets 채택 [확정]) |
| .claude/settings.json | ⏳ Phase 1 사용자 검토 대기 |
| build_headers_draft.txt | ⏳ Phase 2 후반·Phase 3 적용 |
| prompt_templates 5종 | ✅ enricher.prompt_loader 활성 (세션 #3) |

빈 폴더 `.gitkeep` 모두 Phase 2 진입으로 실제 모듈 채움.

---

## 5. SUMMARY §7 검토 체크리스트 — 자동 [확정] 항목

원본 체크리스트 25개 중 진척으로 자동 [확정]된 것:

**1단계 — 큰 방향** (모두 [확정] DECISIONS A1~A6):
- [x] 사이트명·도메인·분야·언어 동의 → DECISIONS A1~A4
- [x] 페르소나 3개 → SCENARIOS §3 + DB seed (3행)
- [x] 시나리오 10편 → DB seed (10행) + K2 [확정] 그대로 유지
- [x] 디자인 컨셉 "미니멀+따뜻함" → DECISIONS A5

**2단계 — 운영 모델** (모두 [확정] DECISIONS C·D·E):
- [x] 매주 페이스 → C8 "발행 편수 최대화" 큐 기반
- [x] 직접 사진 1~3장 → POLICY §3-1-3
- [x] 1클릭 승인 → POLICY §13
- [x] 사업자 등록 월 10만원 후 → D4

**3단계 — 일정·예산**: Phase 1 진행, 도메인 결제 완료, 월 ~16,000원 OK [확정].

**4단계 — 외부 의존**: CF·Anthropic·외부 백업 보유 [확정]. 쿠팡은 Phase 4로 연기.

**5단계 — 의문점**: 본 패치 §6에서 답변 또는 자동 해소.

---

## 6. REVIEW_QUESTIONS — 자동 [확정] 답변 매트릭스

원본 REVIEW_QUESTIONS 25 질문 답변 상태:

| Q | 질문 | 답 | 근거 |
|---|------|----|------|
| 1 | 사이트명 혼살림 | Y | DECISIONS A1 |
| 2 | 도메인 honsalim.com 결제 | Y | 도메인 등록 완료 (만료 2027-05-28) |
| 3 | 분야 1인 가구 | Y | DECISIONS A3 |
| 4 | 언어 한국어 단일 | Y | DECISIONS A4 |
| 5 | 페르소나 3개 | Y | SCENARIOS §3 |
| 6 | 시나리오 10편 | Y | K2 [확정] 현 명세 유지 |
| 7 | 디자인 미니멀+따뜻함 | Y | DECISIONS A5 |
| 8 | 발행 페이스 최대화 | Y | DECISIONS C8 |
| 9 | 자동 게시 11:00 KST | Y | DECISIONS C7 |
| 10 | 자동 "승인" 금지 | Y | POLICY §13 + E7 |
| 11 | 직접 사진 1~3장 의무 | Y | POLICY §3-1-3 |
| 12 | 1클릭 승인 단순 HTML | Y | DECISIONS C1 |
| 13 | 사업자 월 10만원 후 | Y | DECISIONS D4 |
| 14 | gitleaks vs detect-secrets | **B** detect-secrets | 세션 #3 채택, pre-commit 9 hook 활성 |
| 15 | 2FA 5종 | Y (GitHub·CF 활성) | 쿠팡·도메인은 Phase 4·등록 시 |
| 16 | BitLocker D 드라이브 | **보류** | "프로그램 완성도 우선·추후 일괄" — 세션 #3 |
| 17 | 7z vs VeraCrypt | **본 프로젝트 미사용** | `D:\secrets\affiliate_hub\` 격리만 |
| 18 | Phase 1 2026-06 초 | Y | 실제 2026-05-28 조기 진입 |
| 19 | 월 16,000원 | Y | (현 Phase 1·2 사용량 더 낮음) |
| 20 | 외부 백업 드라이브 | Y | (사용자 보유) |
| 21 | 12개월 240편+ KPI | Y | C9 큐 비면 자동 정지 |
| 22 | Cloudflare 계정 | Y | Phase 1 완료 |
| 23 | 쿠팡 파트너스 가입 | **연기** | Phase 4 출시 후 |
| 24 | Anthropic 키 활성 | Y | doctor [OK] |
| 25 | 저장소 이름 | **honsalim** | 채택 [확정] |

**자동 해소 23 / 25**. 남은 2 (Q16 BitLocker, Q23 쿠팡)는 사용자 명시 보류·연기.

---

## 7. 사용자 정독 시 권장 흐름

1. **SUMMARY §1~§3 (5분)**: 한 문장 요약 + 12 문서 1줄 + 결정 매트릭스 → 본 패치 §1에서 추가 13 결정 확인
2. **§4 시나리오 표 (3분)**: 페르소나 분배·시즌·발행 시점 — K2 [확정]이므로 변경 의지 없으면 통과
3. **§5 Phase 일정 (3분)**: 본 패치 §2 진척으로 갱신 시점 파악
4. **§6 비용 (1분)**: 변경 없음
5. **§7 체크리스트 (5분)**: 본 패치 §5 자동 [확정] 항목 cross-ref → 새 의문점만 메모
6. **REVIEW_QUESTIONS 25 질문 (10분)**: 본 패치 §6 매트릭스로 23건 자동 답변 확인 → Q16·Q23만 결정

**정독 예상 시간**: 본 패치 보조로 약 30분 (원본 40~60분 → 25~30분 단축).

정독 중 새 의문점 발견 시 REVIEW_QUESTIONS §6 자유 메모란 또는 채팅 직접 입력.

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.1 | 2026-05-28 | 최초 작성 (세션 #6, SUMMARY/REVIEW_QUESTIONS 진척 갱신 보조) | Claude Opus 4.7 |
