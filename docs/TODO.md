# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #53 — (상세 EVENTS #52 · DECISIONS JJ)

- [ ] **★[관찰] 신규 씨앗 8종 첫 소비 (08-08~)** — 리필이 새 씨앗을 집는지. monitor-stand 계열
  (경쟁 '중간'·카테고리 사용횟수 최저) 예상 [추정]. 수험생의자는 의자 순번상 후순위.
  자취밥솥(270)·김장도마(20)는 구간 미달이라 안 집는 게 정상(검색량 진입 시 자동 활성·JJ2).
  ★확인: 텔레그램 → `logs/auto_cycle.log` → `data/auto_cycle_last.json` · 주간 요약 첫 회=**08-10(월)**
- [ ] **★[측정] 색인 요청 11건 효과 확인** — 주인이 08-07 실행(카테고리 4·최근 글 3·허브 3·kw-1959c5b5,
  'unknown to Google' 5건 전부 커버). **기준선 = 색인 27/42(64%)**. 며칠 뒤
  `PYTHONPATH=src python -m cli gsc-report --index-coverage`로 변화 측정.
  잔여 요청 3건(낮음): `/about/`·`/method/`·`/personas/homeoffice/`.
  ⛔ `kw-e3d08a2c`는 재요청 무효(크롤 후 색인 거부 — 콘텐츠 판단).
- [ ] **[주인 확인] 네이버 서치어드바이저** — 콘솔에서 색인 수·검색 노출 여부 1회 확인
  (세션에선 [확인 불가] — 검색페이지 브라우저 정책 차단).
- [ ] **★★[전략 결정] 키워드 선정 신호** — ops 파일럿 실측: **네이버 검색량과 구글 노출 무상관**
  (24편 전수·페이지1 진입 글도 28일 노출 한 자릿수). 선택지 ①네이버 유지 ②GSC 쿼리 역주입
  ③롱테일 양으로 커버 ④naver_blog 채널로 분담(C19 강화). 상세=docs/reports/ops_2026-08-07.md
- [ ] **[주인 결정] 성장 레버 C — 티스토리→혼살림 링크** — 외부 신호(백링크 ~0)의 유일한 합법
  경로 = 보유 자산 소량 관련 링크(글당 1개 수준·과도하면 링크 스킴 위험·JJ4). 실행은
  autoblog/tistory 프로젝트 세션에서.
- [ ] **[관찰] #51 내부링크·구간 하강의 순위 효과** — 반영 2~8주. 기준선(08-05 GSC 28일):
  노출 66·클릭 2·평균 17.7위·색인 27/42. **최근7=이전7=25로 정체** 중.
- [ ] **[예정 8월 말] 도마 6편 상호경쟁 재평가** — 표본 쌓인 뒤 통합/차별화(Jaccard 0.628).
  ★단서: 게이밍의자가 'Crawled–not indexed'(구글이 색인 거부) — 의자 7편 과밀 신호 가능 [추정].
- [ ] **[관찰] laptop-stand 색인 전환** — 되면 빨래건조대·미니제습기 공개 판단(HH6).
- [ ] **[조건부] 발행 페이스** — 색인율 70%+ 시 1일 2편 검토(그 전엔 1편·JJ4 [주인 미결정]).
- [ ] **[주인 확인] 08-02(일) 미기동** — 로그 없음(코드 정지 아님). PC 절전 여부.
- [ ] **[결정] 여름이불 자동비공개** — 방치/개선 재발행/침구 쿠팡 중 택(unpublished 2편).
- [ ] **[보류—트래픽 후] 클릭 추적**(II12) · **(선택)** 브랜드 blocklist · LLM 추적 미연결 경로 ·
  Cloudflare Web Analytics(레버 C 시) · `/personas/` 허브 · notify-alert가 발송 실패에도 rc=0
  (무인 텔레그램 조용한 실패 위험 — ops 파일럿 적발)
- [ ] (이월) IndexNow 오탐(HH10) · Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 ·
  쿠팡 부트스트랩(15만원→API)
- ※**완료(#52)**: 무인 1·2일차 전항목 통과 · HH8 종결 · 씨앗 8종(`67731e1`) · 시즌 실측(JJ1) ·
  성장 병목 진단(JJ4) · **GSC API 연동+색인 커버리지 자동측정**(`5487b8a`) · **ops 파일럿 1회차**(`51d8a20`)
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
