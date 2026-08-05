# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #52 — (상세 EVENTS #51 · DECISIONS II)

- [ ] **★[관찰·최우선] 08-06 사이클 1일차 — #50+#51이 라이브에서 처음 함께 도는 날**
  (a) **새 공략구간**(300~2000)에서 키워드가 뽑히는가 = head가 아닌 구체 키워드인가
  (b) **배포 전 게이트**가 통과하는가 = 텔레그램에 "배포 차단" 경보가 없는가
  (c) 카테고리 균형 작동(도마 아닌 키워드) · "리필 검색량 조회 실패" 없음
  ★확인: 텔레그램 → `logs/auto_cycle.log` → `data/auto_cycle_last.json`
- [ ] **[관찰] 대기 키워드 0개** — 주간 요약 실측. 리필이 자동 보충하도록 되어 있으나 새 구간에서
  실제로 적격 후보가 나오는지는 08-06에 확인된다. 0편 발행이면 구간을 넓힐지 판단(ceiling 상향).
- [ ] **[관찰] 내부링크·구간 하강의 순위 효과** — 반영에 2~8주. GSC 평균순위 18.2 / 노출 73 / 클릭 2가
  기준선. 색인·노출 변화를 #53~ 에서 확인.
- [ ] **[관찰] laptop-stand 색인 전환** — 되면 빨래건조대·미니제습기도 공개 판단(HH6).
- [ ] **[미해결] monitor-stand 리필 공급 부족** — 도달 가능 씨앗 3개 중 2개 소진·보강 재료 없음(HH8).
  균형 로직이 다른 카테고리로 채워 발행은 안 멈춘다.
- [ ] **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님). PC 절전 여부.
- [ ] **[이월 #47] 도마 클러스터 편중 대책** — 원인은 수정 완료(HH1·HH2). 이미 발행된 6편의 상호
  경쟁은 남음(GSC 상위 노출 0편). #51 유사도 실측 Jaccard 최고 0.628 — 통합·차별화 판단 필요.
- [ ] **[결정] 여름이불 무인 자동비공개** — 방치 / 개선 재발행 / 침구 쿠팡 중 택(현재 unpublished 2편).
- [ ] **[보류 — 트래픽 후] 클릭 추적 연결**(II12) — `/go/` 함수가 D1에 아무것도 안 씀. 지금은 방문자가
  적어 데이터가 무의미. **트래픽이 붙은 뒤 착수**([[feedback_assist_not_overstep]] 과잉설계 금지).
- [ ] **(선택)** 브랜드 blocklist 보강 · LLM 추적 미연결 경로(카테고리 가이드·비전 게이트) ·
  Cloudflare Web Analytics 활성 · `/personas/` 전용 허브(현재 첫 페르소나 복사·canonical로 통합됨)
- [ ] (이월) IndexNow 통지 오탐(HH10·Google 무관·우선순위 낮음) · Phase 2 자가복원(배포 drift) ·
  `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API)
- ※**완료(#51)**: 글↔글 내부링크 0→132(II1·II2) · 카테고리 매핑 자가복원(II3) · 공략구간 하강(II4) ·
  og:image 42/42(II6) · **배포 전 산출물 게이트**(II7) · 주간 리포트(II10) · www 301(II11) ·
  doctor §17·§18·§19 · 게이밍의자 글 구조 이관(II3으로 해소)
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
  **정식 배포 22편·카테고리 7개·내부링크 132개**(#51 실측) / **www 301** ✅(#51)
- 보류: BitLocker · 쿠팡 재가입(Phase 4 후) · AdSense(2026-12) · 영어 확장(2026-12 검토) ·
  보조 호스팅(트래픽 100+/일) · 다크 모드 · 검색·햄버거 메뉴·이메일 알림
