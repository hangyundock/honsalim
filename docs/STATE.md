# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]). 무인 발행이 origin 전진 → push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#50: 무인 리필이 한 달간 '검색량 없이' 돌던 근본원인 봉인** — `cmd_auto_cycle`이 `load_secrets`를 안 불러 리필이 네이버 실패→**캐시(yml 순서)로 자가강등**(리필 투입 10건 전부 score=0). 그래서 yml 순서대로 카테고리를 통째 소진(07-20~27 도마 6연속). +카테고리 균형(라운드로빈)·캐시 강등 fail-loud·도달 불가 씨앗 lint. 회귀 1258→**1274**. 상세 EVENTS #50·DECISIONS HH | 2026-08-05 #50 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT] 로그·텔레그램). 자가복원 **4겹**(#41 게이트 반려+#42 생성 예외+#44 안전정지+#48 과밀 감산 백스톱). fail-loud: #45 refill·생성0 / #47 반려집계·배포·크래시 / #48 형식오류 / #49 seo 미검증 차단 / **#50 캐시 강등(`refill_degraded`)**. ★래퍼는 `main`일 때만 가동([[autonomous-detached-head-silent-stop]]). E7 완화=min_published | #50 |
| ★자동 승인 전제 | **`validated`≠'seo 통과'** — 미매핑 글은 게이트 skip인 채 validated(GG3). auto_approve가 저장 보고서로 재확인해 보류(없음·손상도 fail-closed). 해소는 **재생성**뿐. 사람 승인은 §2-마 지켜 **경고만**(GG5) | #49 |
| ★발행 실패 대응 순서 | **본문=CLAUDE.md §7-3 [확정 #48]** — ①격리 키워드는 그대로 두면 자동 재개(`keyword-requeue` 금지) ②`cli experiment` 오프라인 분포 ③라이브는 마지막 1회. ★n=1 판단 금지 | #48 |
| Phase 1·2 기반 | 인프라(GitHub·Cloudflare·secrets·pre-commit 9종) + 핵심 모듈 10종 + 카테고리. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1274 PASS + 1 skip** [확정 pytest, #50] — #50 +16(카테고리 균형 8·캐시 강등 신호 3·배선 순서 고정 1·도달 불가 lint 4). ★가드 실효성 2회 역검증(수정을 되돌려 실제 실패 확인). 위젯 Qt 1 opt-in skip. black·ruff·mypy 클린 | 2026-08-05 |
| CLI 명령 (BACKEND §9) | **43개** — 코어 10 + 카테고리 + 운영(keyword-*·publish-queue·auto-cycle·refresh-cycle·monitor-articles·notify-alert) + experiment(#48 오프라인 분포·기본 dry-run). ※IndexNow는 CLI 아님=`deployer.indexnow` | #48 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published + **5 게이트**(truth·schema·disclosure·links·**seo**) + META-JSON + Article JSON-LD(author=/about/). ★키워드 글 seo 하한=**절대 횟수 min_count≥4**(FF3), 카테고리는 %하한. ★**seo는 키워드 매핑 있어야 작동**(미매핑=skip·GG3). 세부 DECISIONS J·O·CC·FF·GG | #4~#49 |
| doctor (BACKEND §9) | §1~§16(+#45 §15 씨앗 정합·§16 IndexNow 배포 정합) + §10 모듈 진입점 **73개** + #19 LLM 키 점검 | #48 |
| DB 초기화 | `data/honsalim.db` **v10**(migration 002~010) + categories 9 + products + keyword_queue + articles.structured_json + api_usage(tokens_in/out) + personas 3·scenarios 10. ★대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed` | #48 |
| LLM 비용 추적 | `api_usage(provider='llm')` — 재시도·형식오류·빈응답까지 매 호출 1행. ★단가 입력은 **불요 결정**(#50 HH9 — 실측 월 수백 원). 토큰만 기록해도 **이상 급증 감지는 유효**. 캐시 적중 59%(FF7). 미연결: 카테고리 가이드·비전 게이트 | #50 |
| 설계 문서 / 메모리 / 5파일 | 설계 12/12 완료+SUMMARY(모순 0) · 메모리 feedback 7+reference · 5파일+슬래시 ✅ | #1~#12 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 7개**(#50 laptop-stand 공개) + **정식 글 22편**(08-05 `kw-1194654f` 32인치모니터암 +1). sitemap **40 URL**·라이브 200. ★**색인 4→18 전환 확인**(#50 GSC 실측 — #46 요청 11개 효과). 3개월 노출 73·클릭 **2**·평균순위 **18.2**. 미색인 34 중 22는 정상(robots 20·404 1·리디렉트 1), 실제 대기 **12**. ★병목 이동: "구글이 모른다"→**"알지만 상위에 안 띄운다"** → 레버=권위·발행 지속([[growth-first-priority]]) | #50 |
| ★무인 키워드 선정·공급 (#50) | 리필은 **네이버 실검색량**으로 뽑는다(전엔 캐시 강등=씨앗 순서·HH1). 키 = **직전 카테고리 회피 → 사용 횟수 적은 순 → 점수**(HH3). 사람 경로는 §2-마로 균형 미적용. 큐 pending 0 → 매일 리필 보충: 적격 **20개**·10일 **5카테고리 순환**·다음 예상 `1인밥솥`. ★후보는 **yml secondary 정확 매칭 + core 포함**인 것만 — 어느 core도 안 담으면 **영구 도달 불가**(`doctor §15 unreachable` 5건·매핑 사전 역할은 유효해 삭제 금지·HH7). **미해결**: monitor-stand 도달가능 3개 중 2개 소진·보강 재료 없음(HH8) | #50 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | 혼살림 / **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피·SSL Active·2027-06-01 Auto Renew) + honsalim.com(구·**301 Page Rule**·경로보존) / **Cloudflare Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#50**. **build-and-deploy: main push → 커밋된 build/site를 Pages 배포**(CI 재빌드 없음·글 DB 로컬). ★**무인 배포는 전부 `refresh_cycle`** — `deployer.git_push`는 stub이라 단독 금지(#47 EE4). ※★**반드시 main 유지**(detached면 무인 정지·#44) |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 32-bit (TIMA·AutoBlog 공유) / `logs/auto_cycle.log`(무인 1차 증거)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE·telegram(TIMA 봇) .env + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유·DeepSeek #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token / Anthropic API Key | 활성 / 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY / GitHub PAT | 영구(공개 키) / 미발급(Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → promotion_link·`/go/`→302 라이브 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

secrets 격리 · pre-commit 9종(detect-secrets+black·ruff·mypy) · GitHub Secrets · Branch Protection **전부 운영 중**. `.claude/settings.json` deny 24·allow 14 = 검토 대기.

## 알려진 잔존 미해결

### ★ 다음 세션 #51 — **작업 목록은 TODO.md**, 상세 근거는 EVENTS #50·DECISIONS HH
1. **★[관찰·최우선] 08-06 사이클 1일차** — #50 수정이 라이브에서 처음 도는 날. (a) **도마가 아닌** 키워드(예상 `1인밥솥`)가 뽑히는가 = 카테고리 균형 작동 (b) 로그에 **"리필 검색량 조회 실패"가 없는가** = 네이버 연결 정상(있으면 키 문제가 별도로 존재). 확인: `logs/auto_cycle.log` + `data/auto_cycle_last.json`.
2. **[관찰] laptop-stand 색인 전환** — 되면 빨래건조대·미니제습기도 공개 판단(HH6). 둘은 씨앗이 없어 리필 기여 0·구조 페이지 노출만.
3. **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님). 스케줄러 조회가 TIMA 가드에 막혀 **확인 불가**.
4. **★[모니터링] 색인 요청 2차분**(주인 08-05 실행)([[growth-first-priority]]) · 5.[미해결] monitor-stand 공급 부족(위 표·HH8) · 6.[이월] 도마 클러스터 편중 · 7.[결정] 여름이불 자동비공개 · 8.(이월) IndexNow 오탐(HH10)·게이밍의자 이관·쿠팡 부트스트랩.
- ※**해결·종결**: #49 수정 라이브 검증 완료(08-05 seo `skip`→`pass`·article 24 발행) · LLM 단가 **불요 결정**(HH9·월 수백 원) · #48 본문 예산 관찰 종료(GG8).
- ★**작업 함정**(매 세션): 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) · push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) · 한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처.

### 진척 가능(작음) / 보류
- 작음: `builder/manifest.py` 증분 빌드 · `collector/coupang.py`(Phase 4) · Actions status check · BitLocker
- 보류: AdSense(2026-12) · 영어 확장 · 보조 호스팅

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| **2026-08 (현재)** | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
