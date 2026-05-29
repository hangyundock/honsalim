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
  - 세션 #6 (2026-05-28~29 정책 대재설계 L2 AI이미지 + Google AI Guide 정합 M1~M7 + cross-project 통합 + 회귀 342 + 17 commits)

## 최근 5세션

### 세션 #11 — 2026-05-29~30 (Opus 4.8 1M, 디자인 시안→Jinja2 5종 + builder.renderer + SEO/JSON-LD + enrich 버그수정 + 알리 수집기 골격, 회귀 352→378)

> ※ #10은 워크트리 6개·브랜치 6개 폐기 정리 커밋(2b260b2)만 — EVENTS 블록 미기재.

**시작 상황**: `/honsalim-start` → 워크트리 stupefied-lichterman (origin/main=#10 `2b260b2` 분기, 0/0 동기). 회귀 352. "공개 사이트 5종 시안"이 ★시급.

**핵심 진척 [확정]**:

1. **Claude Design 핸드오프 → 시안 5종 확정 (DECISIONS G4)**: "클로드 코드 인계" URL → WebFetch 4MB gzip → `docs/design_drafts/honsalim/`. 확정 조합 **톤 우드 / 카드 그림자 / 밀도 미니멀** (사용자 승인). 토큰 DESIGN §3 일치.
   - Jinja2 템플릿: `base·home·scenario_list·article·persona_hub·about·404` + `partials/{header,footer}` + `_macros/{components,meta}` / `static/css/{tokens,components,pages}` + `static/js/hub-filter.js`
   - 미리보기 `scripts/preview_build.py`(목업 19페이지) → 사용자 확인. `docs/design_drafts/CHOICE.md` 기록.
   - 정책 정정: About 이미지 "직접 촬영"→**"AI 생성+표기, 제품은 공식 위젯"**(L2). 운영자 "혼살다"·이메일·등록 진행 중(M2). 제휴링크 `rel="sponsored nofollow"`.

2. **정식 빌더 `src/builder/renderer.py`**: DB(personas·scenarios seed)→정적 사이트, `honsalim build --full`. 9페이지(home·hub·persona 3·about·404·sitemap). 게시 article 0편 → 상세글 미렌더(콘텐츠 단계).

3. **SEO 메타 + JSON-LD**: `_macros/meta.html`(OG·Twitter) + `jsonld.py` +3빌더(Breadcrumb·WebSite·Organization)+as_script_tags. base.html 연동.

4. **enrich 버그 수정**: `cmd_enrich`가 scenarios에 없는 컬럼 `s.keywords` 조회 → OperationalError. 제거 + 실행 회귀 테스트 추가.

5. **알리 수집기 골격 (DECISIONS D9)**: `collector.aliexpress` dry-run(서명 sha256 HMAC — 문서 4.5 예시 일치 검증, HTTP 0). 쿠팡 게이팅(사이트 완성 후 승인)으로 알리를 첫 상품 소스로 앞당김.

6. **회귀 352→378 PASS**: renderer 9 + jsonld 구조화 4 + cli-enrich 1 + aliexpress 12. `test_renderer`·`test_aliexpress_collector` 신설.

**알리 외부 작업 (사용자, 진행 중·미완)**:
- honsalim.com 사이트 등록이 **"ali" 부분문자열 오탐**(hons**ali**m)으로 거부 → whitelist 문의(대기).
- 기존 제휴 계정(dugi2020@naver.com) 사용(새 계정 실수 삭제). k-Content Hub(blogspot) 백업 등록.
- Open Platform Affiliate API 개발자 신청(Affiliates Individual·Korea) → **Under Review**(1~2 영업일). App Key/Secret 대기.

**잔존 미해결 (다음 세션)**:
- 알리 키 발급 후: 수집기 라이브 검증(timestamp 형식·응답 JSON 경로) + 상품 적재 + 첫 글 enrich(API 비용)·검증·승인·발행
- 빌더 잔여: 상세글 렌더·Pretendard self-host·critical CSS·feed.xml·robots.txt
- honsalim.com whitelist 승인

**다음 세션 할 일**:
1. 알리 승인 메일 확인 → App Key/Secret `ali.env` 저장
2. `collector.aliexpress` 라이브 검증 → products 적재
3. (대기 시) 빌더 잔여 콘텐츠 무관 항목(robots.txt·feed.xml 등)

---

### 세션 #9 — 2026-05-29 (Opus 4.7, Auto Mode, 자동 push 정책 N1 + dashboard 모듈 (CLI 11/11 완성) + secrets 경로 정정, 9 commits)

**시작 상황**: `/honsalim-start` → 세션 #8 직후 상태 확인. 본 워크트리(peaceful-gagarin-b7fda4)는 #6 종료(bfb0cbb)에서 분기, main은 #8 (da69624)까지 진행. 메인 D:\affiliate_hub에서 직접 main 브랜치로 작업 진행.

**핵심 진척 [확정]**:

1. **N1 자동 push 정책 신설** [확정 사용자 결정]:
   - 사용자 요청: "매 세션 종료마다 push 챙기는 부담 제거"
   - CLAUDE.md §2(라)·§11 갱신 (사용자 직접 — Auto Mode classifier가 agent config 자체 수정 차단)
   - `.claude/commands/honsalim-end.md` §7+규칙 갱신 (자동 push 단계 + destructive op 금지 명시)
   - `.claude/settings.json` deny 확장 — force(`--force`·`-f`·`--force-with-lease`·`--force-if-includes`·`--mirror`·`--delete`·refspec)·reset --hard·rebase·branch -D·checkout --·restore --·clean·worktree remove --force·tag -d·update-ref -d·commit --amend·reflog expire·filter-branch·filter-repo (Bash·PowerShell 양쪽 21+ 패턴) / allow에 `git push origin main`+`HEAD:main` 추가
   - DECISIONS N. 자동화 정책 신설 — **N1** 영구화

2. **사용자 외부 작업 완료** [확정 사용자 보고]:
   - SUMMARY/REVIEW_QUESTIONS/SUMMARY_PATCH_v1.1 정독 완료 (Phase 3 진입 게이트 통과)
   - Google AI Studio API 키 발급 + 결제 활성화 + `D:\secrets\honsalim.env` (사용자 보안 결정: secrets/ 바로 아래 단일 파일로 격리)
   - DECISIONS L6 경로 갱신 + DESIGN §11·IMAGE_GENERATION §3 정합 + STATE/TODO 시급 해소

3. **DECISIONS G3 신설** [확정 사용자 결정]:
   - Claude Design 적용 범위 = **공개 사이트 5종만** (홈·시나리오 허브·글·페르소나·About)
   - dashboard(관리자 페이지)는 **Claude Design 미사용** — 단순 stub HTML로 충분 (1인 운영·외부 노출 X)
   - STATE/TODO "dashboard 시안" stale 표기 정정 ("공개 사이트 5종 시안"이 정확)

4. **dashboard 모듈 신설 — CLI 11/11 완성** [확정 회귀 10/10 PASS]:
   - `src/dashboard/{__init__,render,approve}.py` 신설 (Jinja2 미사용, 단순 f-string + html.escape, BACKEND §2-6 명세)
   - `render_dashboard(conn, output_path)` — 6 상태 그룹별 카드 + 1클릭 승인 명령 (복사 버튼) + validator fail 24h 3건+ 빨간 배너 + XSS escape
   - `approve(conn, draft_id, user_note)` — state_machine.transition(validated→approved) + `.approve/<id>.flag` 파일 생성 (JSON)
   - `src/cli.py` cmd_dashboard 추가 — `--output`·`--open` (브라우저 자동) 옵션
   - `tests/test_dashboard.py` 신설 — render 7 + approve 3 = **10/10 PASS**
   - doctor §10 진입점 37 → **41** (+4 dashboard.{render,render_html,fetch_drafts_by_status,approve})
   - 회귀 342 → **352 PASS** [확정 pytest 3.18초]

**누적 commits 9건 [확정 origin/main 모두 동기 — N1 자동 push 첫 적용]**:
- 7705431 CLAUDE.md 포맷 정정 (사용자 직접 §2-라·§11 수정)
- 433cbe3 N1 자동 push 정책 (4 파일 + DECISIONS N 신설)
- 07a75e3 SUMMARY 정독 완료 + secrets honsalim.env 경로 정정
- a788648 settings.json deny 보완 - force-with-lease 등 5 패턴
- b8457ad G3 신설 - Claude Design은 공개 사이트 5종만
- e5ee0e0 dashboard 모듈 구현 (CLI 11/11 완성)
- (이 endcommit) /honsalim-end #9 종료

**메모리 신설**: [[no-unfounded-priority]] — "다음 진행" 질문 = 작업 계속 의도. 마감 명령 추천 금지. 같은 답변 반복 금지 (세션 #9 사용자 비판).

**잔존 미해결 (다음 세션)**:
- 공개 사이트 5종 시안 (사용자 claude.ai/design 직접)
- Phase 4 진입 시 about.html · Person Schema 적용 (M2-1~M2-7 사전 결정)
- Scaled Content Abuse Step 2 (fail 게이트 승격) — 1~2주 운영 데이터 후 별도 세션
- (선택) 본 워크트리들 폐기 검토

**다음 세션 할 일**:
1. 사용자 외부 작업 (claude.ai/design 5종 시안 생성·1개 선정)
2. 시안 선정 후 Claude Code → DESIGN.md 토큰 갱신 + Jinja2 템플릿 작성 진입

---

### 세션 #8 — 2026-05-29 (Opus 4.7, Auto Mode, 네이버 분리 작업 6 Phase + D:\naver_blog\ 신규 프로젝트 셋업·push·dazzling-hermann 폐기, 1 commit)

**시작 상황**: `/honsalim-start @docs/NAVER_SEPARATION_PLAN.md 따라 네이버 분리 작업 진행해줘` 명시 지시. SEPARATION_PLAN은 옛 dazzling-hermann-7d1424 워크트리 5 commits에만 존재 (main에 push 없음). 본 워크트리(roentgen)는 bfb0cbb 시점 분기 → 작업 중 main이 별도 흐름으로 #7 종료된 상태 발견.

**Phase 1 사전 확인 — 중대 발견 [확정]**:
- 혼살림 main(600caff)에 **네이버 흔적 0건** [확정 Glob·Grep]: `docs/NAVER_PLAN.md` 없음 · `DECISIONS §J` = "Phase 2 아키텍처"(네이버 무관) · `CLAUDE.md` 네이버 행 0건 · GitHub `hangyundock/honsalim` public 유지
- 네이버 D안 작업은 `dazzling-hermann-7d1424` 워크트리 5 commits(`c94f617`·`b2748b9`·`96e89f9`·`311371c`·`69d6956`)에 격리 (push 없음)
- → SEPARATION_PLAN 원안(6 Phase) Phase 4(혼살림 정리)는 거의 불필요 → 수정안(4 Phase + 축소된 Phase 4)으로 진행

**Phase 2 — D:\naver_blog\ 신규 폴더 셋업 [확정]**:
- 폴더: `D:\naver_blog\{.claude\commands, docs\archive}`
- 5파일: `CLAUDE.md`(8.5KB·네이버 §2(라) 자동 발행 금지 등) · `docs/STATE.md`(4.8KB) · `docs/EVENTS.md`(4.4KB·세션 #0 분리 작업) · `docs/TODO.md`(3.7KB·Phase 0~5 단계별) · `docs/DECISIONS.md`(10.8KB·옛 §J 18건 → §A~F 재분류·J14 폐기)
- 설정: `.claude/settings.json`(deny 22·allow 9·네이버 자동 게시 함수 deny) · `.gitignore`(secrets·data·storage_state·user_photos 제외) · `README.md`

**Phase 3 — 산출물 이전 [확정]**:
- `dazzling-hermann:docs/NAVER_PLAN.md`(477줄) → `D:\naver_blog\docs\PROJECT_PLAN.md`(35.9KB) — 통합 가정 수정: `src/naver/` → `src/`·"혼살림 저장소 private 전환" → "본 프로젝트 별도 private repo"·`§J` 참조 → `§A~F`
- 메모리 `project_naver_channel.md` → `C:\Users\dugi2\.claude\projects\D--naver_blog\memory\`로 이전 + `MEMORY.md` 신규 인덱스 작성

**Phase 4 — 혼살림 정리 (축소) [확정]**:
- main 코드/문서 변경 0건 (이미 깔끔 — Phase 1 검증 결과)
- 혼살림 영역 메모리 `MEMORY.md` 행 redirect 갱신 + 옛 `project_naver_channel.md`를 짧은 redirect stub으로 덮어쓰기
- 잔존 grep 검증: `naver` 흔적은 모두 Cloudflare 이메일·서치어드바이저 등록·IndexNow·외부 단축 URL 차단 등 본 분리와 무관한 정상 흔적 [확정]

**Phase 5 — GitHub 처리 [확정]**:
- 사용자 직접: GitHub `hangyundock/naver_blog` private repo 생성 (Add README/.gitignore/license 모두 off)
- Claude: `git init -b main` + `user.name/email` config + initial commit `6cfd67b`(9 files·1082 lines) + `git remote add origin` + `git push -u origin main` 명시 승인 → 성공 `* [new branch] main -> main`
- dazzling-hermann-7d1424 워크트리·브랜치 폐기 명시 승인 → `git worktree remove --force` + `git branch -D claude/dazzling-hermann-7d1424` (was 69d6956)

**Phase 6 — 마스터·메모리 동기화 [확정]**:
- `D:\templates\CLAUDE_PROJECT_SETUP.md §14` 실전 운영 listing: 혼살림 항목 갱신 + `D:\naver_blog\` 신규 항목 추가 (별도 polder·별도 private repo 명시)
- `D:\templates\PROJECT_MARKET_RESEARCH_FRAMEWORK.md §8.1` 사례 갱신: D안→C안 분리 작전 변경 반영 + 교훈 #1 갱신 ("통합 vs 분리 — STATE/TODO/EVENTS 혼동 회피 우선") + 분리 작업 기록 추가
- `D:\templates\naver\` 3 마스터 그대로 (양 프로젝트 공통 참조)

**작전 변경 의의**:
- 원안(D안 통합 + 혼살림 public→private) → 변경안(C안 별도 폴더 D:\naver_blog\) — 사유: 통합으로 STATE/TODO/EVENTS에 혼살림·네이버 섞여 혼동 + private 전환 시 CodeQL·Secret Scanning Alerts 유료화 부작용
- 결과: 혼살림 main public 유지·코드/docs 깔끔·CI 무료 활성 그대로 + 네이버는 별도 격리

**잔존 미해결 (다음 세션)**:
- 본 세션 commit 1건 push 사용자 명시 승인 (EVENTS #8·STATE 갱신)
- 본 워크트리(dazzling-roentgen-b550f7) 폐기 검토 — 분리 작업 후 사용 가치 낮음 (선택, 다음 세션은 main 또는 새 워크트리에서 시작 가능)

**다음 세션 할 일**:
1. SUMMARY/REVIEW_QUESTIONS/SUMMARY_PATCH 정독 (Phase 3 진입 게이트, 시급 아님 — 2026-07 이전까지)
2. Google AI Studio API 키 발급 + 결제 + google.env
3. dashboard 시안 (claude.ai/design)
4. (네이버 작업은 본 프로젝트 D:\naver_blog\로 분리됨 — 본 워크트리 작업 없음)

---

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
