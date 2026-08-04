# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]). 무인 발행이 origin 전진 → push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#49: 08-04 발행 0편 복구 + 'validated=5게이트 통과' 구멍 봉인** — 원인=사람이 07-27 넣은 `32인치모니터암` 미매핑. 그 과정에 **더 큰 결함** 적발: 미매핑 글은 seo skip인 채 validated가 되고 자동승인은 재검증을 안 해 **씨앗 매핑 추가가 곧 미검증 글 발행 트리거**(실데이터 반증 — 가드 OFF면 `ok=True`). 회귀 1230→**1258**. 상세 EVENTS #49·DECISIONS GG | 2026-08-04 #49 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT] 로그·텔레그램). 자가복원 **4겹**(#41 게이트 반려+#42 생성 예외+#44 안전정지+#48 과밀 감산 백스톱). fail-loud: #45 refill·생성0 / #47 반려 집계·비공개 배포·cli 크래시 / #48 형식오류 원문 / **#49 seo 미검증 글 자동승인 차단(`seo_unverified`)**. ★래퍼는 `main`일 때만 가동([[autonomous-detached-head-silent-stop]]). E7 완화=min_published | #49 |
| ★자동 승인 전제 | **`validated`는 'seo 게이트 통과'를 뜻하지 않는다** — 미매핑 키워드 글은 게이트가 **skip(=pass 취급)**된 채 validated(#49 GG3). auto_approve가 저장 보고서로 재확인해 보류(보고서 없음·손상도 fail-closed). 해소는 **재생성**뿐. 사람 1클릭 승인은 §2-마 지켜 **막지 않고 경고**(GG5) | #49 |
| ★발행 실패 대응 순서 | **CLAUDE.md §7-3 [확정 #48]** — ①격리 키워드는 **그대로 두면** 다음 사이클이 다른 키워드로 재개(`keyword-requeue` 금지) ②`cli experiment`로 **오프라인 분포 측정** ③라이브 재생성은 마지막 1회. ★n=1 라이브 판단 금지 | #48 |
| Phase 1·2 기반 (#2~#17) | Phase 1 인프라(GitHub·Cloudflare·secrets·pre-commit 9종) + 핵심 모듈 10종 + #17 카테고리 4종. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1258 PASS + 1 skip** [확정 pytest, #49] — #49 +28(seo 미검증 판정표·매핑 후 자동발행 차단·과차단 회귀 방지·사람 승인 경고·경고 드리프트 가드·인치 변형 매핑). 위젯 Qt 1 opt-in skip. black·ruff·mypy 클린 | 2026-08-04 |
| CLI 명령 (BACKEND §9) | **43개** — 코어 10 + 카테고리 + 운영(keyword-*·publish-queue·auto-cycle·refresh-cycle·monitor-articles·notify-alert) + experiment(#48 오프라인 분포·기본 dry-run). ※IndexNow는 CLI 아님=`deployer.indexnow` | #48 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD(author=혼살다·/about/·#45). ★키워드 글 seo 하한=**절대 횟수 min_count≥4**(FF3), 카테고리는 %하한. ★**seo 게이트는 키워드 매핑이 있어야 작동**(미매핑=skip·GG3). 세부 DECISIONS J·O·CC·FF·GG | #4~#49 |
| doctor (BACKEND §9) | §1~§16(+#45 §15 씨앗 정합·§16 IndexNow 배포 정합) + §10 모듈 진입점 **73개** + #19 LLM 키 점검 | #48 |
| DB 초기화 | `data/honsalim.db` **v10**(migration 002~010) + categories 9 + products + keyword_queue(#25) + articles.structured_json(#34) + api_usage(#36·#48 tokens_in/out) + personas 3·scenarios 10. ★대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed` | #48 |
| LLM 비용 추적 (#48) | `api_usage(provider='llm')` — **재시도·형식오류·빈응답까지 매 호출 1행**. enrich 로그 24h 요약. ★단가 `llm_price_*_per_1m` **미입력(0)** → 토큰만·비용 $0. 캐시 적중 59% 자동(FF7). 미연결: 카테고리 가이드·비전 게이트 | #48 |
| 설계 문서 / 메모리 / 5파일 | 설계 12/12 완료+SUMMARY(모순 0) · 메모리 feedback 7+reference · 5파일+슬래시 ✅ | #1~#12 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 6개** + **정식 글 21편**(#49 실측·08-03 `kw-73c464f5` 스텐도마 +1). sitemap 38 URL·라이브 200. ★**색인 원인 확정(#46·DD1)**: 라이브 29 URL·색인 4 → 격차=**크롤 예산/권위**(기술·얇음·중복·링크 정량 클린). 주인 **미색인 11개 색인요청 완료**(07-20·전환 확인 필요). 다음 레버=색인 전환+발행량+권위([[growth-first-priority]]) | #49 |
| 무인 키워드 공급 | 대기 큐 **pending 0**(27건 소진) → 매일 **추천 리필**이 자동 보충. 라이브 재현(#49): 네이버 정상·적격 **18개**·다음 선정 예상 `의자추천`(9,880). ★리필은 **yml secondary에서만** 나온다(정확 매칭) — 네이버 40건 중 20건이 미매핑 탈락. **약 18일치**, 소진 시 생성 0편·[ALERT] → 씨앗 보강이 곧 발행 지속성(GG7) | #49 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | 혼살림 / **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피·SSL Active·2027-06-01 Auto Renew) + honsalim.com(구·**301 Page Rule**·경로보존) / **Cloudflare Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#49**. **build-and-deploy: main push → 커밋된 build/site를 Cloudflare Pages 배포**(CI 재빌드 없음·글 DB 로컬). ★**무인 배포는 전부 `refresh_cycle`** — `deployer.git_push`는 commit 없는 stub이라 단독 사용 금지(#32·#47 EE4). ※★**반드시 main 유지**(detached면 무인 정지·#44) |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 32-bit (TIMA·AutoBlog 공유) / `logs/auto_cycle.log`(무인 1차 증거)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE(#37 분리)·telegram(#41 TIMA 봇 재사용) .env + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유·DeepSeek 본문생성 #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token / Anthropic API Key | 활성 / 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY / GitHub PAT | 영구(공개 키) / 미발급(Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → promotion_link·`/go/`→302 라이브 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

secrets 격리 · pre-commit 9종(detect-secrets v1.5.0+black·ruff·mypy 매 커밋 Passed) · GitHub Secrets · Branch Protection **전부 운영 중**. `.claude/settings.json` deny 24·allow 14 = 사용자 검토 대기.

## 알려진 잔존 미해결

### ★ 다음 세션 #50 — **작업 목록은 TODO.md**, 상세 근거는 EVENTS #49·DECISIONS GG
1. **★[관찰·최우선] #49 수정 라이브 1일차** — 08-05 11:11 사이클이 (a) 새 씨앗·가드가 실린 코드로 도는지(래퍼 `git pull` 후 실행) (b) `32인치모니터암` 재생성 시 **SEO 주입** 로그가 찍히고 게이트를 실측하는지 (c) 실패해도 다른 키워드로 자동 재개되는지.
2. **★[관찰] 리필 풀 소진** — 적격 18개 = 약 18일치(GG7). 줄어드는 속도를 보고 씨앗 보강 시점 판단. 미매핑 탈락 20건이 보강 후보 목록.
3. **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님). 작업 스케줄러 조회가 TIMA 가드에 막혀 **확인 불가**.
4. **[입력 대기·주인] LLM 단가** `llm_price_*_per_1m` — 0이라 비용 $0 표시(토큰은 기록 중).
5. **★[모니터링] 색인 전환**([[growth-first-priority]]) · 6.[이월] 도마 클러스터 편중 · 7.[결정] 여름이불 자동비공개 · 8.(이월) IndexNow 관찰성·draft 카테고리 3개·게이밍의자 이관·쿠팡 부트스트랩.
- ※#48 본문 예산 부작용은 **재현 안 됨**(GG8·n=2 둘 다 시도 1/3) → 예산 상향 불요·관찰 종료. slug는 #48 해결(FF8·라이브 3건 URL은 주인 결정으로 유지).
- ★**작업 함정**(매 세션): 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) · push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) · 한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처.

### 진척 가능(작음) / 보류
- 작음: `builder/manifest.py` 증분 빌드 · `collector/coupang.py`(Phase 4) · Actions status check · BitLocker
- 보류: AdSense(Phase 6·2026-12) · 영어 사이트 확장 · 보조 호스팅 GitHub Pages

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
