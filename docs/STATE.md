# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.
>
> ⚠️ ★매 세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]). 무인 발행이 origin 전진 → push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#47: 무인 발행 3일 공백 근본수정(반려 집계·밀도 지시) + 전체 정밀진단 안정화 5건** — 07-21~23 발행 0편 원인=`스텐도마` 게이트 반려 3연속(침묵 정지 아님) / fail-loud 구멍 3개 봉인(반려 집계·비공개 배포·cli 크래시) / 래퍼 3건(pull 판정·로그 인코딩·경보)+busy_timeout. 회귀 1116→**1126**. 상세 EVENTS #47·DECISIONS EE | 2026-07-29 #47 |
| 운영 모델 | **★완전무인 가동 ON**: auto_mode ON·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT] 로그·텔레그램). 자가복원 **3겹**(#41 게이트 반려+#42 생성 예외+#44 안전정지 경보). #45 fail-loud 보강(refill 매핑·공개 한정·생성0 경보·`category_draft` 보류). **#47 fail-loud 구멍 3개 봉인**: 게이트 반려를 성공으로 세던 집계 정정(`RC_GATE_REJECTED`)·비공개-only 날 배포 실패 경보·cli 비정상 종료(exit≠0) 래퍼 경보. ★래퍼는 `main`일 때만 가동([[autonomous-detached-head-silent-stop]]). E7 완화=min_published | #47 |
| Phase 1·2 기반 (#2~#17) | Phase 1 인프라(GitHub·Cloudflare·secrets·pre-commit 9종) + 핵심 모듈 10종(cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers) + #17 카테고리 4종. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1126 PASS + 1 skip** [확정 pytest, #47] — #47 +10(반려 집계 fail-loud 2·밀도 정량지시 5(실경로 드리프트 가드 포함)·비공개-only 배포 3·busy_timeout 1), 위젯 Qt 크래시 테스트 1 opt-in skip. black·ruff·mypy 클린 | 2026-07-29 |
| CLI 명령 (BACKEND §9) | **42개** — 코어(doctor·db·collect·enrich·validate·approve·promote·build·deploy·dashboard) + 카테고리(collect/build/approve·provision-category 등) + 운영(keyword-*·keyword-requeue·coupang-add·publish-queue·schedule·auto-cycle·refresh-cycle·build-deploy·monitor-articles·un/republish-article·notify-alert). ※IndexNow는 CLI 아님=`deployer.indexnow`(배포 후속) | #44 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD(author=혼살다·/about/ 연결·#45). 세부 DECISIONS J·O·CC + EVENTS | #4~#45 |
| doctor (BACKEND §9) | §1~§16(+#45 §15 씨앗 정합·§16 IndexNow 배포 정합) + §10 모듈 진입점 **71개** + #19 LLM 키 점검 | #45 |
| DB 초기화 | `data/honsalim.db` **v9**(migration 002~009) + categories 9·category_products + products(정가/할인·판매량) + keyword_queue(#25) + articles.structured_json(#34) + api_usage(#36) + personas 3·scenarios 10. ★대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed`(+`collect-category`) 재생성 | #36 |
| 설계 문서 / 메모리 / 5파일 | 설계 12/12 완료+SUMMARY(모순 0) · 메모리 feedback 7+reference · 5파일+슬래시(start/save/end) ✅ | #1~#12 |
| 사이트 게시글 / 트래픽 / 수익 | **라이브 카테고리 6개** + **정식 글 18편**(#46 12편 + 07-24~29 무인 6편 연속 발행). ★**색인 원인 확정(#46·DD1)**: 라이브 29 URL·색인 4 → 격차=**크롤 예산/권위**(기술·얇음·중복·링크 정량 클린). 주인 **미색인 11개 색인요청 완료**(07-20·전환 확인 필요). 다음 레버=색인 전환+발행량+권위([[growth-first-priority]]) | #47 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | 혼살림 / **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피·SSL Active·2027-06-01 Auto Renew) + honsalim.com(구·**301 Page Rule**·경로보존) / **Cloudflare Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **#47 `289a7aa`**(정밀진단 안정화 5건), 운영 폴더 동기화됨. **build-and-deploy: main push → 커밋된 build/site를 Cloudflare Pages 배포**(CI 재빌드 없음·글 DB 로컬). ★**무인 배포는 전부 `refresh_cycle`**(build/site·functions/go를 commit+push) — `deployer.git_push`는 commit 없는 stub이라 단독 사용 금지(#32·#47 EE4). ※★**반드시 main 브랜치 유지**(detached면 무인 정지·#44) |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 32-bit (TIMA·AutoBlog 공유) / `logs/auto_cycle.log`(무인 1차 증거·#47 UTF-8 복구)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE(#37 분리)·telegram(#41 TIMA 봇 재사용) .env + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유·DeepSeek 본문생성 #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsalim.com | 만료 2027-05-28 | Auto Renew (D-60 알림) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY | 영구 [확정 — 공개 키] | 회전 불요 |
| GitHub PAT | 미발급 (Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → 제품별 promotion_link 생성·`/go/`→302 라이브 작동 | 2026-06-03 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| secrets 격리 / pre-commit 9종 / GitHub Secrets·Branch Protection | ✅ 전부 운영 중(detect-secrets v1.5.0+black·ruff·mypy 매 커밋 Passed) |
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — 사용자 검토 대기 |

## 알려진 잔존 미해결

### ★ 다음 세션 #48 — 상세 EVENTS #47
1. **[관찰] 07-30 11:11 사이클 3종 검증** — ①`스텐도마` 재생성이 새 정량 지시("총 약 N회")로 게이트 통과하는지(실패해도 #47 수정으로 **1일차 텔레그램 경보**) ②`auto_cycle.log` 한글이 정상 기록되는지(EE5③) ③pull이 "성공(exit=0)"으로 기록되는지(EE5②). 셋 다 로그 확인만으로 판정 가능.
2. **★[모니터링] 색인 전환**([[growth-first-priority]]): GSC 색인요청 11개(07-20)가 "색인 생성됨"으로 옮겨졌는지 확인. 안 되면 원인=권위/시간(코드 아님)·발행 지속. ※색인 원인은 #46서 확정(크롤 예산)—추가 진단 불요.
3. **★[관찰·신규 #47] 도마 클러스터 편중 위험**: 07-24~29 발행 6편 중 **4편이 도마**(도마추천·엔드그레인도마·실리콘도마·TPU도마) + cutting-board 카테고리. DD1이 경고한 **글↔카테고리 8-shingle 겹침 44~50%**가 한 클러스터에 집중 → 크롤 후 '얇은 중복'으로 일부만 색인될 리스크. 씨앗 다양화(#45)가 작동하나 소진 순서상 같은 카테고리를 연속 소비. 대책 검토(씨앗 라운드로빈·카테고리 간 분산) 필요.
4. **[관찰·신규 #47] 비표준 slug 2건**: article #6 slug=`1`, #18 slug=`tpu`(정상은 `kw-<hash>`). URL 품질·색인 영향 [확인 불가] — slug 생성 경로 점검 필요.
5. **[결정] 여름이불 무인 자동비공개**: #45 발행분을 #46 사후모니터가 '미달' 자동비공개 → 방치 / 개선(카테고리 매핑·상품 보강 후 재발행) / 침구 쿠팡 카테고리 중 택. (현재 unpublished 2편)
6. (이월) IndexNow 관찰성 갭(성공 경로 res.notes 미로그·Bing/Yandex 이차) · draft 카테고리 3개(노트북거치대·빨래건조대·미니제습기) 공개 여부(미니제습기 씨앗 2027-04) · 게이밍의자 이관 · 쿠팡 부트스트랩(15만원→API).
- ★**매 세션 시작 시 운영 폴더 브랜치 확인** `git -C D:\affiliate_hub branch --show-current`==main([[autonomous-detached-head-silent-stop]]). 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). ★무인 발행이 origin 전진→push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]). ★한글→.py·ASCII([[powershell-korean-encoding]]). 운영 DB 직접수정 불가→주인 런처. ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

### 진척 가능 / 잔존 (작음)
- `builder/manifest.py` 증분 빌드 · `collector/coupang.py`(Phase 4) · Actions status check Branch Protection · BitLocker(사용자 결정)

### 보류
- AdSense 신청(Phase 6·2026-12) · 영어 사이트 확장 · 보조 호스팅 GitHub Pages

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| ~2026-07 | (경과) Phase 2 시스템·Phase 3 디자인·**Phase 4 첫 출시 도달**(라이브 18편) |
| 2026-08 | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
