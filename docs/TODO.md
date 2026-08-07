# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #53 — (상세 EVENTS #52 · DECISIONS JJ)

- [ ] **★[관찰] 신규 씨앗 8종 첫 소비 (08-08~)** — 리필이 새 씨앗을 집는지. monitor-stand 계열
  (경쟁 '중간'·카테고리 사용횟수 최저) 예상 [추정]. 수험생의자는 의자 순번상 후순위.
  자취밥솥(270)·김장도마(20)는 구간 미달이라 안 집는 게 정상(검색량 진입 시 자동 활성·JJ2).
  ★확인: 텔레그램 → `logs/auto_cycle.log` → `data/auto_cycle_last.json` · 주간 요약 첫 회=**08-10(월)**
- [ ] **[주인 10분] 성장 레버 A·D** — ①GSC 색인 요청 3차: 미색인 잔여 + 신규 3편
  (`kw-1194654f`·`kw-241434c3`·`kw-574de1ed`) ②네이버 서치어드바이저 콘솔에서 색인 수·검색
  노출 여부 1회 확인(세션에선 [확인 불가] — 검색페이지 브라우저 정책 차단).
- [ ] **[주인 결정] 성장 레버 C — 티스토리→혼살림 링크** — 외부 신호(백링크 ~0)의 유일한 합법
  경로 = 보유 자산 소량 관련 링크(글당 1개 수준·과도하면 링크 스킴 위험·JJ4). 실행은
  autoblog/tistory 프로젝트 세션에서.
- [ ] **[관찰] 내부링크·공략구간 하강의 순위 효과** — 반영 2~8주(#51 반영 08-05). 기준선:
  GSC 노출 73·클릭 2·평균 18.2위·색인 18. #53~ 색인·노출 변화 확인.
- [ ] **[예정 8월 말] 도마 6편 상호경쟁 재평가** — GSC 글별 노출 표본이 쌓인 뒤 통합/차별화
  판단(지금은 표본 부족·성급 금지). Jaccard 최고 0.628.
- [ ] **[관찰] laptop-stand 색인 전환** — 되면 빨래건조대·미니제습기도 공개 판단(HH6).
- [ ] **[조건부] 발행 페이스** — 색인율 70%+ 회복 시 1일 2편 검토(그 전엔 1편 유지 —
  미색인 재고 방지·JJ4 [제안 — 주인 미결정]).
- [ ] **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님). PC 절전 여부.
- [ ] **[결정] 여름이불 무인 자동비공개** — 방치 / 개선 재발행 / 침구 쿠팡 중 택(현재 unpublished 2편).
- [ ] **[보류 — 트래픽 후] 클릭 추적 연결**(II12) — `/go/`가 D1에 아무것도 안 씀. 트래픽이 붙은 뒤
  착수([[feedback_assist_not_overstep]] 과잉설계 금지).
- [ ] **(선택)** 브랜드 blocklist 보강 · LLM 추적 미연결 경로(카테고리 가이드·비전 게이트) ·
  Cloudflare Web Analytics(레버 C 실행 시 referral 측정용) · `/personas/` 전용 허브
- [ ] (이월) IndexNow 통지 오탐(HH10·Google 무관·우선순위 낮음) · Phase 2 자가복원(배포 drift) ·
  `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API)
- ※**완료(#52)**: 08-06·07 무인 1·2일차 전항목 통과(구간 픽·배포 게이트·균형) · monitor-stand
  공급 부족(HH8) 종결 · 씨앗 8종 등재(`67731e1`) · 시즌 실측(신학기·재택 기각·JJ1) · 성장 병목 진단(JJ4)
- 참고: ★**작업 함정**(매 세션) — 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) ·
  push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) ·
  한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) ·
  워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처 ·
  운영 모듈 직접 import 시 `config.load_secrets()` 선행([[project_verify_script_load_secrets]]) ·
  라이브 검증은 curl 또는 브라우저 UA([[live-verify-cloudflare-ua]]) ·
  ★**게이트·검사는 켜기 전 실제 산출물로 판정해 볼 것**([[unmanned-monitoring-gate]] — 과민하면 발행 정지)

## 시점 의존 잔존 · Phase 1~4 남음

- [ ] 알리 이미지·상세페이지 정책 조사(Phase 5 전) · M4/M5/M6(`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6).
- [ ] `.claude/settings.json` deny 룰 사용자 검토(deny 24·allow 14) · Branch Protection에 Actions status check
- Phase 2~3 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지 · 시즌 시나리오.
- Phase 4: 도메인·GSC·사이트맵·네이버 SA ✅(#40) / IndexNow·about·privacy·Person Schema ✅(#45) /
  **정식 배포 24편·카테고리 7개**(#52 실측) / **www 301** ✅(#51)
- 보류: BitLocker · 쿠팡 재가입(Phase 4 후) · AdSense(2026-12) · 영어 확장(2026-12 검토) ·
  보조 호스팅(트래픽 100+/일) · 다크 모드 · 검색·햄버거 메뉴·이메일 알림
