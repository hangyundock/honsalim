# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★★ ops 자동화 로드맵 (캘린더 알림 등록됨 — ggpad2020 '개인업무')

- [ ] **1단계 · 8/13(수)** `/honsalim-ops` **2회차 단독 실행** — 코드 작업 없이 ops만 돌려
  **소모량 실측**(#52 파일럿은 구축 세션과 섞여 분리 불가) + 색인 요청 효과(기준선 27/42) +
  씨앗 잔량. 8/20경 3회차까지 돌려 주기 확정.
- [ ] **★2단계 · 8/24(월)** — **naver_blog(`D:\naver_blog`)에 ops 세션 이식**.
  ★**naver_blog 세션에서** 할 것(프로젝트 분리·CLAUDE/회귀가 다름). 선행 = 1단계 검증
  (미검증 상태로 복제하면 결함까지 복제·#48 교훈).
  naver_blog는 이미 보유: Qt 대시보드·스케줄러(11:05)·텔레그램(만료 D-1 검증)·백업·monitor·
  doctor·회귀 566 → **없는 건 ops 층 하나**. 측정(유입 검색어 71종·색인·순위)은 오히려 앞섬.
  ※교차 발견: 혼살림(구글) 노출 82%가 익명화 초롱테일 = naver_blog(네이버) 대표 키워드 유입 0건
  → **신생 매체 구조적 법칙**. ops가 두 프로젝트 발견을 주고받는 통로가 된다.
- [ ] **3단계** — 두 프로젝트 ops 보고를 **한 텔레그램 채널로 통합**(같은 봇 사용 중).

## ★ 다음 세션 #53 — (상세 EVENTS #52 · DECISIONS JJ)

- [ ] **★[관찰] 신규 씨앗 8종 첫 소비(08-08~)** — monitor-stand 계열 예상 [추정]. 자취밥솥·
  김장도마는 구간 미달이라 안 집는 게 정상(JJ2). 주간 요약 첫 회=**08-10(월)**.
- [ ] **★[측정] 색인 요청 11건 효과** — 08-07 실행('unknown' 5건 전부 커버). **기준선 27/42(64%)**.
  `cli gsc-report --index-coverage`로 측정. 잔여 3건: `/about/`·`/method/`·`/personas/homeoffice/`.
  ⛔`kw-e3d08a2c`는 재요청 무효(크롤 후 색인 거부).
- [ ] **★[전략·보류] 키워드 선정 신호** — 지금 데이터로 판정 불가(노출 66 중 82% 익명화·생존편향).
  **현행 유지** + GSC 쿼리 주간 적립. 재평가 = **월 노출 500+ 또는 비익명 쿼리 30+**.
- [ ] **[주인 결정] 레버 C 티스토리→혼살림 링크** — 외부 신호(백링크 ~0)의 유일한 합법 경로.
  실행은 autoblog/tistory 세션에서. **[주인 확인] 네이버 SA** 색인·노출 1회 확인.
- [ ] **[관찰] #51 효과** — 반영 2~8주. 기준선(08-05·28일) 노출 66·클릭 2·17.7위. **최근7=이전7=25 정체**.
- [ ] **[8월 말] 도마 6편 재평가** — Jaccard 0.628. ★게이밍의자 'Crawled–not indexed' = 과밀 신호 [추정].
- [ ] **[조건부]** 색인율 70%+ 시 1일 2편 검토(그 전엔 1편·JJ4) · **[관찰]** laptop-stand 색인 전환(HH6)
- [ ] **[주인 확인]** 08-02(일) 미기동(PC 절전?) · **[결정]** 여름이불 unpublished 2편
- [ ] **[보류]** 클릭 추적(II12·트래픽 후) · notify-alert가 발송 실패에도 rc=0(조용한 실패 위험) ·
  브랜드 blocklist · Cloudflare Web Analytics · IndexNow 오탐(HH10) · 쿠팡 부트스트랩
- ※**완료(#52)**: 무인 1·2일차 통과 · HH8 종결 · 씨앗 8종 · JJ1·JJ4 · **GSC 연동+색인 자동측정**
  (`5487b8a`) · **ops 파일럿**(`51d8a20`) · **GSC 쿼리 주간 적립**(`39c37b6`) · **추천창 재설계**(`2c99c0b`)
- 참고: ★**작업 함정**(매 세션) — 운영 폴더 브랜치==main([[autonomous-detached-head-silent-stop]]) ·
  push 전 ff 재동기화([[autonomous-deploy-advances-origin]]) · 한글→.py·UTF-8([[powershell-korean-encoding]]) ·
  Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` ·
  운영 DB 직접수정 불가 · 운영 모듈 import 시 `load_secrets()` 선행([[project_verify_script_load_secrets]]) ·
  라이브 검증은 curl/브라우저 UA([[live-verify-cloudflare-ua]]) ·
  ★게이트는 켜기 전 실제 산출물로 판정([[unmanned-monitoring-gate]])

## 시점 의존 잔존 · Phase 1~4 남음

- [ ] 알리 이미지 정책 조사(Phase 5 전) · M4/M5/M6(`GOOGLE_AI_OPTIMIZATION.md` §6).
- [ ] `.claude/settings.json` deny 룰 검토(24/14) · Branch Protection에 Actions status check
- Phase 2~3 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지 · 시즌 시나리오.
- Phase 4: 도메인·GSC·사이트맵·네이버 SA ✅(#40) / IndexNow·about·privacy·Person Schema ✅(#45) /
  **정식 배포 24편·카테고리 7개**(#52 실측) / **www 301** ✅(#51)
- 보류: BitLocker · 쿠팡 재가입(Phase 4 후) · AdSense(2026-12) · 영어 확장(2026-12 검토) ·
  보조 호스팅(트래픽 100+/일) · 다크 모드 · 검색·햄버거 메뉴·이메일 알림
