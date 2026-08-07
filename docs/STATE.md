# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만. 이력은 EVENTS/DECISIONS. 매 세션 변경 영역만 갱신. Cap 10KB.
> ⚠️★세션 시작 시 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) · push 전 ff 재동기화([[autonomous-deploy-advances-origin]]).

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#52: ★GSC API 연동 + 색인 커버리지 자동측정(27/42) + 무인 운영 세션 `/honsalim-ops` 신설·파일럿 + GSC 쿼리 주간 적립 + 추천창 재설계(포화 판정 자동화) + 씨앗 8종(HH8 종결).** 무인 1·2일차 전항목 통과. **판단층까지 무인화**가 이 세션의 축. 상세 EVENTS #52·DECISIONS JJ·KK | 2026-08-07 #52 |
| 운영 모델 | **★완전무인 ON**: auto_mode·예약·`min_published`=**0**. 키워드+쿠팡 적재→auto-cycle 자동 생성·승인·발행→무관여. 자기보고 3겹(`auto_cycle_last.json`·[ALERT]·텔레그램). 자가복원 4겹(#41·#42·#44·#48). fail-loud #45~#50 + **#51 배포 게이트**. ★래퍼는 `main`일 때만 가동 | #51 |
| ★무인 감시(#51) | **배포 전 산출물 게이트** — `refresh_cycle`(배포 단일 관문) build 후·deploy 전 `site_audit`. 결함이면 **배포 중단+텔레그램**. doctor §17~§19와 같은 코드. 유사도는 warn·제외(164배). 주간 요약=월요일 사이클에 얹음 | #51 |
| ★측정·판단층(#52) | **GSC 연동**(서비스 계정·무료·속성 `sc-domain:honsallim.com`). CLI `gsc-report`(`--index-coverage`)·`gsc-collect`·`gsc-queries`. ★sitemap `indexed`는 **폐기 필드(항상 0)**(KK2). **월요일 훅**=성과+적립 자동(KK5). **`/honsalim-ops`**=점검→분석→허용범위 실행→보고(KK3·파일럿 1회·예약 미등록) | #52 |
| ★자동 승인 전제 | **`validated`≠'seo 통과'** — 미매핑 글은 게이트 skip인 채 validated(GG3). auto_approve가 저장 보고서로 재확인해 보류. 해소는 **재생성**뿐 | #49 |
| ★발행 실패 대응 | **CLAUDE.md §7-3 [확정 #48]** — ①격리는 두면 자동 재개(requeue 금지) ②`experiment` 오프라인 분포 ③라이브는 마지막 1회. ★n=1 판단 금지 | #48 |
| Phase 1·2 기반 | 인프라(GitHub·CF·secrets·pre-commit 9종) + 핵심 모듈 10종. 세부=BACKEND §2·archive | #17 |
| Phase 2 회귀 테스트 | **1369 PASS + 1 skip** [확정 pytest, #52] — #52 +40(GSC 14·적립 13·배선 4·클러스터 9). ★가드 실효성 **3회 역검증**(배선·정렬을 되돌려 실제 실패 확인). 옛: 1329[#51]. 위젯 Qt 1 opt-in skip. black·ruff·mypy 클린 | 2026-08-07 |
| CLI 명령 (BACKEND §9) | **46개** — 코어 10 + 카테고리 + 운영(keyword-*·publish-queue·auto-cycle·refresh-cycle·monitor-articles·notify-alert) + experiment(#48) + **gsc-report·gsc-collect·gsc-queries**(#52) | #52 |
| Phase 2 흐름 골격 | collected→enriched→validated→approved→published + **5 게이트**(truth·schema·disclosure·links·seo) + JSON-LD. 키워드 글 seo 하한=**min_count≥4**(FF3). ★seo는 매핑 있어야 작동(GG3) | #4~#49 |
| doctor (BACKEND §9) | §1~**§19**(#51 §17 내부링크·§18 유사 키워드·§19 온페이지 SEO — 배포 게이트와 동일 코드)·§15 씨앗 정합·§16 IndexNow + 모듈 진입점 **78개**(+GSC 5) + LLM 키 점검 | #52 |
| DB 초기화 | `data/honsalim.db` **v11**(002~011) + categories 9·products·keyword_queue·api_usage·**gsc_queries**(#52)·personas 3·scenarios 10. 대시보드 시작 시 자동 migrate. ※DB는 gitignore — 새 워크트리는 `db migrate`+`db seed` | #52 |
| ★운영 비용 (KK8 실측) | 청구는 **OpenRouter 하나뿐** — 잔액 **$6.36/25**·**혼살림 단독 월 $0.4 미만**. **새 결제 불요**. 나머지 **전부 0원**(GSC·네이버·CF·Actions·적립·Imagen) | #52 |
| 설계 문서 / 메모리 | 설계 12/12+SUMMARY(모순 0) · 메모리 feedback 8+reference · 5파일+슬래시 4종 ✅ | #52 |
| 사이트 게시글 / 트래픽 / 수익 | 카테고리 7·**정식 글 24편**·sitemap 42·라이브 200. GSC 28일(07-09~08-05) **노출 66·클릭 2·평균 17.7위**·최근7=이전7=**25 정체**. **색인 27/42(64%)**[URL검사 실측]. ★노출의 **82%가 익명화 초롱테일** = 목표 키워드는 노출권 밖(생존편향·KK4). 병목=①색인 ②외부신호(백링크 ~0) ③나이 41일 | #52 |
| ★무인 키워드 선정·공급 | 리필=**네이버 실검색량**(HH1). 키=직전 카테고리 회피→사용 횟수↓→점수(HH3). 공략구간 **[300,2000]**(II4). 후보는 yml secondary 정확 매칭+core 포함만(HH7). **#52 씨앗 8종**(monitor-stand 4=HH8 종결·선제 2종은 구간 진입 시 자동 활성 JJ2)·근친 변형 금지(JJ3). **추천창은 포화 자동 판정**(KK6: 발행가능→얇은 묶음→점수·평균 1.5배=포화) | #52 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 / 호스팅 | **honsallim.com 라이브**(겹ㄹ=알리 'ali' 차단 회피) + **www→non-www 301**(#51) + honsalim.com(구·301 Page Rule) / **CF Pages `honsalim`** |
| GitHub | **`hangyundock/honsalim` Public**. **main push → 커밋된 build/site를 Pages 배포**(CI 재빌드 없음). ★**무인 배포는 전부 `refresh_cycle`** — `git_push`는 stub이라 단독 금지(EE4). ※★**반드시 main 유지**(detached면 무인 정지·#44) |
| Secrets / Branch Protection | CF_API_TOKEN·CF_ACCOUNT_ID·INDEXNOW_KEY / `main-protect` Active |
| R2 / D1 | `honsalim-images`(APAC) / `honsalim-clicks` `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python / 로그 | 3.10 **32-bit**(TIMA 키움 API 요구·KK7) / `logs/auto_cycle.log`(무인 1차 증거)·`honsalim.log` |
| secrets | **`D:\secrets\affiliate_hub\`**: cloudflare·indexnow·ali·GOOGLE·telegram .env + **gsc_service_account.json**(#52) + 복구코드 2종 / **`D:\secrets\.env`**: OPENROUTER_API_KEY(K-Content 공유) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 2종 | 2027-05-28 / 06-01 | Auto Renew (D-60 알림) |
| CF API Token / GSC 서비스 계정 | 활성 / 만료 없음 [확정 #52] | 토큰 6개월 회전 권장 **2026-11-28** [추정] |
| INDEXNOW_KEY / GitHub PAT | 영구(공개 키) / 미발급(Actions는 GITHUB_TOKEN) [확정] | — |
| AliExpress Portals | **완전 연결** [확정 #22]: `ALI_TRACKING_ID=honsallim` → `/go/`→302 라이브 | 2026-06-03 |
| **OpenRouter 크레딧** | **잔액 $6.36 / 25** [확정 #52] — 2~3개월 뒤 소진 | 주인 직접 충전 |
| 쿠팡 파트너스 | 배너 수동 첨부 운영 중 | API는 누적 15만원 후 |

## 보안 / 권한

secrets 격리 · pre-commit 9종 · GitHub Secrets · Branch Protection **운영 중**. settings.json deny 24·allow 14 = 검토 대기.

## 알려진 잔존 미해결

### ★ 다음 세션 #53 — **작업 목록은 TODO.md**, 상세 근거는 EVENTS #52·DECISIONS JJ·KK

1. **★★ops 자동화 로드맵(캘린더 등록됨)** — **8/13(수) 1단계**: `/honsalim-ops` 2회차 **단독 실행**으로 소모량 실측(#52 파일럿은 구축 세션과 섞여 분리 불가). **8/24(월) 2단계**: naver_blog에 ops 이식(★naver_blog 세션에서·1단계 검증 선행). 3단계: 두 프로젝트 텔레그램 통합.
2. **★[측정] 색인 요청 11건 효과** — 기준선 **27/42(64%)**. `cli gsc-report --index-coverage`로 변화 확인. 잔여 요청 3건(`/about/`·`/method/`·`/personas/homeoffice/`). ⛔`kw-e3d08a2c`는 재요청 무효.
3. **[관찰] 신규 씨앗 8종 첫 소비(08-08~)** + 주간 요약·GSC 적립 첫 회 **08-10(월)** 도착 확인.
4. **[전략·보류] 키워드 선정 신호** — 판정 불가(KK4). 현행 유지 + 적립. 재평가 = 월 노출 500+ 또는 비익명 쿼리 30+.
5. **[주인 대기]** 레버 C(티스토리 링크) · 레버 D(네이버 SA) · 여름이불 · 08-02 미기동. **[8월 말]** 도마·의자 과밀 재평가(게이밍의자 색인 거부가 단서).
- ※**해결·종결**: #52 — 무인 1·2일차 통과 · HH8 종결 · 씨앗 8종 · **GSC 연동·색인 자동측정·ops 세션·쿼리 적립·추천창 재설계**(KK1~KK8).
- ⚠️**미해결(신규)**: `notify-alert`가 발송 실패에도 rc=0 — 무인 텔레그램이 조용히 죽어도 모른다.
- ★**작업 함정**(매 세션): 브랜치==main([[autonomous-detached-head-silent-stop]]) · push 전 ff 재동기화([[autonomous-deploy-advances-origin]]) · 한글→.py·UTF-8([[powershell-korean-encoding]]) · Edit 절대경로 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가 · import 전 `load_secrets()`([[project_verify_script_load_secrets]]) · 라이브 검증은 curl/브라우저 UA([[live-verify-cloudflare-ua]]) · ★게이트는 켜기 전 실제 산출물로 판정([[unmanned-monitoring-gate]]) · ★규칙은 이유를 알고 적용([[rules-know-the-why]])

### 진척 가능(작음) / 보류
- 작음: 증분 빌드 · `collector/coupang.py` · Actions status check · BitLocker / 보류: AdSense(2026-12)·영어 확장·보조 호스팅

## 캘린더 알림

> ★#52부터 **구글 캘린더(ggpad2020 '개인업무')에도 등록** — ops 로드맵 2건.

| 일자 | 이벤트 |
|------|--------|
| **2026-08-13(수)** | ★ops 2회차 단독 실행 — 소모량 실측 (구글 캘린더 알림) |
| **2026-08-24(월)** | ★★naver_blog에 ops 이식 (구글 캘린더 알림·naver_blog 세션에서) |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-10~11 | **OpenRouter 크레딧 소진 예상**($6.36 잔액) — 주인 충전 |
| 2026-11-28 | CF API Token 회전 [추정] · 새해 미니멀 사전 발행 |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 / 05 / 06 | 신학기 검색 피크 / 종소세·도메인 갱신 / Phase 7 1년 결산 |
