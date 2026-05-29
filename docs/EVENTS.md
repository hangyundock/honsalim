# EVENTS.md — 혼살림 세션 로그

> 자동 회전: 6번째 세션 시 가장 옛 세션이 docs/archive/EVENTS_YYYYMM.md로 이동.
> 옛 세션 검색은 ARCHIVE 인덱스 참조 후 archive/ 폴더 grep.
> Cap: 20KB.

## ARCHIVE 인덱스 (옛 세션 한 줄 요약)

- [EVENTS_202605.md](archive/EVENTS_202605.md):
  - 세션 #1 (2026-05-27 프로젝트 신규 셋업·정밀 조사·5파일 시스템·슬래시 명령 등록)
  - 세션 #2 (2026-05-27~28 Phase 0 설계 12/12 + Phase 1 외부 작업: GitHub·Cloudflare·도메인·R2·D1·Git push)
  - 세션 #3 (2026-05-28 Phase 1 마무리·Phase 2 핵심 모듈 9개·회귀 95·14 commits)
  - 세션 #4 (2026-05-28 Phase 2 풀 골격 + 검토 자료 2건 + DECISIONS J 8건·메모리 no-excessive-approval·회귀 95→295·21 commits)
  - 세션 #5 (2026-05-28 CLI 10/11 deployer/build + 핵심 결정 K1~K4 + 알리 승인 + pip install -e .[dev] + 회귀 333 PASS + 11 commits)

## 최근 5세션

### 세션 #7 — 2026-05-29 (Opus 4.7, Auto Mode, cross-project 잔존 3건 처리 + M2 사전 결정 + pip-audit 재검증, 2 commits)

**시작 상황**: `/honsalim-start` → 세션 #6 정합성 양호. TODO.md cap 임박 (4,556 B / 5KB 91%) 사용자 지적 → 정리 진행 (~22% 축소). 사용자 "어제 작업 이어서" 지시 → cross-project 잔존 3건 (Hana Kim 5편·M2 Person Schema·Scaled Content Abuse) "3건 모두 순차 진행" 결정.

**핵심 진척 [확정]**:

1. **TODO.md cap 정리**:
   - 4,556 B (91%) → **3,549 B (71%)** [확정] — ~~취소선~~ 완료 항목 6건 삭제 + Phase 2 소제목 통합 + STATE 카운트 정합

2. **Task #1 — AutoBlog Hana Kim 5편 처리 [확정]**:
   - 본질 작업 (author/publisher Organization 갱신 + 1인칭 재작성)은 세션 #6 이전 이미 완료된 사실 확인 — post_id 1~5 본문 Hana Kim 0건 · author-bio K-Content Hub · JSON-LD author/publisher Organization 5/5편 완료
   - 보강 작업: post 5 FAQ 비정상 구조 `<p><h3>Q</h3>A</p>` → `<h3>Q</h3><p>A</p>` 정상화 3건 + FAQPage JSON-LD Schema 3 Q&A 추가
   - post 1~5 content_text 재동기화 — 알려진 이슈 #16 stale 1인칭 잔존 (1~4건 each) → **0건** [확정]
   - DB 백업: `D:\autoblog\data\autoblog.db.before_task024_20260529_084403`
   - AUTOBLOG_TODO.md TASK_024 완료 표기

3. **Task #2 — 혼살림 M2 Person Schema + about 사전 결정 7건 [확정]**:
   - 운영자 정체성 = 필명 + 운영 철학 (사용자 결정 A안)
   - **필명 = "혼살다"** (혼자+살다 합성, 사이트명 정합) · 운영 철학 = "혼자 살아도 충분히 따뜻한 일상을, 가성비 좋게."
   - 전문성 (knowsAbout) = 1인 가구 살림·자취·홈오피스·일상 살림 · 사진 미게재 (사용자 사진 없음 + AI 사진은 거짓) · 이메일 dugihappyending@gmail.com · 사업자 등록 진행 중 표기
   - DECISIONS M2-1~M2-7 추가 + FRONTEND §4-5 about.html 본문 텍스트 초안 + §4-5-bis Person Schema 매크로(_macros/person.html) 사전 명세 + POLICY §8-4 운영자명·이메일 정합 추가

4. **Task #3 — Scaled Content Abuse 모듈 Step 1 dry-run [확정]**:
   - 사용자 결정 B안 (dry-run + 단계적, fail 게이트 별도 세션)
   - `D:\autoblog\src\content\similarity.py` 신설 — 4-gram word Jaccard + HTML/JSON-LD/script 정규화 + `compute_similarity` / `find_duplicates` / `check_duplicate_dry_run` / `check_post_against_published` (DB 통합 헬퍼)
   - `D:\autoblog\tistory_revival\keyword_cluster.py` 신설 — tistory posts 본문 미저장 대응 (어절+바이그램 키워드 Jaccard)
   - `D:\autoblog\tistory_revival\seo_gate.py` 수정 — `check_article(published_keywords=None)` 옵션 인자 추가, dry-run hook (metrics 필드만, issues 추가 X, 기존 호출자 영향 0)
   - `D:\autoblog\test_similarity.py` 신설 — 회귀 **13/13 PASS** [확정] (similarity 7 + keyword_cluster 6)

5. **pip-audit 재검증 [확정]**:
   - 현재 pip-audit = **0건** ("No known vulnerabilities found") — 세션 #6 결과 유지
   - STATE.md 시급 #3 "transitive 13건 분석" stale 해소
   - STATE.md 시급 #1 "세션 #6 push 대기" stale 해소 (이미 push 완료)
   - 단순 outdated 패키지는 시스템 Python 공유 (TIMA·AutoBlog) — CLAUDE.md §12 환경 변경 금지 정합 → 무차별 -U 안 함

6. **AutoBlog git 저장소 결정 [확정 사용자]**:
   - D:\autoblog는 git 저장소 아님 확인 — **로컬만 유지** (사용자 결정, git init·remote 만들지 않음)
   - AutoBlog 변경 사항은 로컬 파일·DB 백업으로만 영구화

**누적 commits 2건 [확정 origin/main 모두 동기]**:
- `9f1a37a` cross-project 잔존 3건 처리 + M2 사전 결정 7건 (혼살림 docs 4 파일)
- `78096b2` STATE 시급 정리 - stale 2건 해소

**AutoBlog 측 변경 (로컬만)**: similarity.py 신설 + keyword_cluster.py 신설 + seo_gate.py 수정 + test_similarity.py 신설 + AUTOBLOG_TODO.md TASK_024·TASK_025 갱신 + data/autoblog.db (post 5 FAQ + post 1~5 content_text)

**잔존 미해결 (다음 세션)**:
- SUMMARY.md / REVIEW_QUESTIONS.md / SUMMARY_PATCH_v1.1.md 사용자 정독 (Phase 3 진입 게이트)
- Google AI Studio API 키 발급 + `D:\secrets\affiliate_hub\google.env` (Phase 3 진입 전)
- Scaled Content Abuse Step 2 (fail 게이트 승격) — 1~2주 운영 데이터 후 별도 세션
- (참고) AutoBlog Blogger 사이드바 gadget "Hana Kim — Seoul, Korea" 수동 편집 (API 관할 밖)
- (참고) AutoBlog post 6·7·9·13·22 내부 링크 anchor text stale (알려진 이슈 #17, 별도)

**다음 세션 할 일**:
1. 사용자 정독 시간 (SUMMARY + PATCH, 약 25~30분)
2. Google AI Studio API 키 발급 + 결제 + google.env (사용자 외부 작업)
3. dashboard 시안 진입 (Claude Design, 사용자 직접)

---

### 세션 #6 — 2026-05-28~29 (Opus 4.7, Auto Mode, 정책 대재설계 + Google AI 정합 + cross-project 통합, 17 commits)

**시작 상황**: `/honsalim-start` → 세션 #5 마무리 정합성 양호. 사용자 "추천제안으로 실행" 지시 → A(lint #15 fix) 자율 진행. 본 세션 중간 사용자 명시 비판으로 [[no-end-of-step-prompting]] 메모리 신설.

**핵심 진척 [확정]**:

1. **정책 대재설계 — L 카테고리 2차 변경 (사용자 결정)**:
   - 1차: L1~L5 위키바이형 (수백 제품 보유 불가능 사용자 지적) → E8·D5 폐기
   - 2차: 사용자 "사진 직접 촬영 없음, Google API로 AI 이미지" 결정 → L2 재정의 + L3 1인칭 무조건 차단 + L6/L7/L8 신설 (Google Imagen 4 Fast `imagen-4.0-fast-generate-001`, AI 명시 표기, 상품 이미지는 쿠팡 공식 위젯)
   - `docs/IMAGE_GENERATION.md` 신설 (AutoBlog `ai_image_gen.py` 패턴 이식·$0.02/장·결제 의무)

2. **Google AI Optimization Guide 정합 (2026-05-15 공식 발표)**:
   - DECISIONS M1~M7 신설 (non-commodity·E-E-A-T author·차별화·이미지 검수·Business Profile·UCP·llms.txt 부정)
   - `docs/GOOGLE_AI_OPTIMIZATION.md` 신설 + §9 AutoBlog 2주 조사 S1~S12 통합 (12/12 정합)
   - SCENARIOS §2-1 차별화 의무 + enricher prompt non-commodity + 1인칭 금지

3. **cross-project 통합 (사용자 명시 진행)**:
   - AutoBlog `AUTOBLOG_SEO_MASTER.md` 신설 (TASK_019 2주 조사 + Google AI Guide 통합 글쓰기 1 페이지)
   - AutoBlog DECISIONS H6·H7 (SEO_MASTER 참조·non-commodity) + system_prompt Rule 14·15 (Scaled Content Abuse·AUTHOR INTEGRITY) + enhancer.py FAQPage Schema 자동 생성
   - tistory_revival DECISIONS Q1·Q2 + content_profiles.py 차별화·저자 정직성 + seo_gate.py `_FAKE_AUTHOR` 게이트
   - `D:\templates\naver\` 마스터 3종 신설 (NAVER_POLICY·NAVER_SEO_MASTER·NAVER_AUTOMATION_SPEC)

4. **운영 인프라**:
   - 회귀 333 → 342 PASS [확정 pytest 2.63초]
   - doctor §14 docs/ size cap 통합 + `src/common/size_caps.py` + `scripts/check_size_caps.py`
   - `.github/workflows/security.yml` 월간 pip-audit + 90일 artifact
   - `pyproject.toml` 직접 의존 3건 lower-bound + pip install -U 16건 환경 갱신 (A안 적용) → pip-audit 0 [확정]
   - `docs/PIP_AUDIT_ANALYSIS.md` 신설
   - CI lint #15 Black fix (commit 90d60f6) — 모든 워크플로 ✅ 정상화

5. **문서 정합**:
   - SUMMARY_PATCH_v1.1.md 신설 (정독 보조, 결정 45 + REVIEW 23/25 자동 해소)
   - CHANGELOG v1.5(세션 #5) + v1.6(세션 #6) 정식
   - PLAN §8 예산 갱신 (~16,000 → ~48,000원/월, Imagen 추가)
   - ARCH/BACKEND/POLICY/OPS 정합 갱신

**누적 commits 17건** [확정 origin/main 모두 동기]: 90d60f6·5f6dfde·bf82c73·987afed·f9299ab·55243bc·5f50025·b04b249·ed77853·58005f2·7309d55·adb117e·e9e7de9·97da9b2·42a2921·ac710b6·d870607·4a33a72·b0da256·dfcb955·10fd5ee·3a3d908 (commits 23개 일부 cross-project record)

**메모리 신설**: [[no-end-of-step-prompting]] — 한 단계 끝날 때마다 마감·push 자동 제안 금지 (세션 #6 사용자 비판 반영).

**잔존 미해결 (다음 세션)**:
- SUMMARY/REVIEW_QUESTIONS + SUMMARY_PATCH 정독 (사용자 직접, Phase 3 진입 게이트)
- Google AI Studio API 키 발급 + 결제 + `google.env` (Phase 3 진입 전)
- 알리 이미지·상세페이지 정책 조사 (Phase 5 진입 전)
- M2/M4/M5/M6 Phase 3~6 작업
- cross-project: AutoBlog Hana Kim 5편 처리 (TASK_024) + Scaled Content Abuse 모듈 (TASK_025) + 혼살림 M2 Person Schema
- B2/B3 tistory_revival FAQPage·Person Schema (별도 세션)

**다음 세션 할 일**:
1. 본 세션 종료 후 사용자 정독 시간 (SUMMARY + PATCH)
2. Google AI Studio API 키 발급
3. Phase 3 진입 전 사진 사전 준비 폐기 (L2 [확정] AI 생성으로 대체)
4. dashboard 시안 진입 (Claude Design, 사용자 직접)

---
