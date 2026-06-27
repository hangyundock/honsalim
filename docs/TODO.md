# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #40 — (상세 EVENTS #39)

- [ ] **★성장(검색노출·트래픽) 최우선**([[growth-first-priority]]·주인 #39 선택) — ①**색인 토대 점검·정비**(GSC 색인·사이트맵·IndexNow·네이버 서치어드바이저 **실작동 확인**·빈 것 정비) ②**씨앗 커버리지 확장**(seo_keywords.yml — '미매핑' 근본 해소) ③E-E-A-T(about/Person Schema). *코딩 전 첫 단계 = 현재 색인 상태 확인(주인 계정 접근 필요할 수 있음).*
- [ ] **무인 일일 발행(22:02) 관찰** — 발행 글 품질 사후검토(발행 글 관리 탭·monitor 2겹) + **#39 자기보고 확인**(`[ALERT]` 로그·`data/auto_cycle_last.json`). 키워드/쿠팡 큐 보충. 무인 안내 전 `docs/AUTOMATION.md` 필독.
- [ ] (선택·보험) **Phase 2 자가복원** — ali off-target graceful-degrade · 배포 drift 가드 · 능동 푸시 채널 · `run_auto_cycle.ps1` git pull footgun 정정.
- [ ] (이월) `review-helpfulknow` 월 지출 한도 · 쿠팡 배너 부트스트랩(15만원→API) · `mini-dehumidifier` · naver_blog 볼륨(`/naver-start`).
- 참고: 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate)·DB gitignore→재생성. **main직접머지=`git push origin HEAD:main`**. 운영 DB 직접수정 불가→주인 런처. ★한글→.py·ASCII([[powershell-korean-encoding]]). ★무인 발행이 origin 전진([[autonomous-deploy-advances-origin]])—푸시 전 ff.

## 시점 의존 잔존 (세션 #6~7)

- [ ] 알리 이미지·상세페이지 정책 조사 (Phase 5 전) · M2/M4/M5/M6 (`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6)
- [ ] **혼살림 M2 Person Schema + about 운영자 정보** (Phase 4, E-E-A-T) — 사전결정 완료(필명 "혼살다"·사진없음, DECISIONS M2). 코드=`_macros/person.html`+`about.html`(FRONTEND §4-5)

## Phase 1: 인프라 — 남음

- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14)
- [ ] **윈도우 작업 스케줄러 등록** — Phase 2 코드 작성 후 (DECISIONS C7)
- [ ] Branch Protection에 Actions status check — Phase 2 안정 후

### 보류
- BitLocker (사용자 결정 — "프로그램 완성도 우선·추후 일괄")
- 쿠팡 파트너스 재가입 — Phase 4 출시 후

## Phase 2~3: 핵심 시스템·디자인 — 대부분 완료 (상세 STATE)
- 빌더·렌더러·템플릿·디자인·대시보드·발행경로 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지(Imagen·페르소나별) · 시즌 시나리오 작성.

## Phase 4: 첫 출시 (2026-07 말~08)

- [ ] honsalim.com 커스텀 도메인 연결
- [ ] GSC DNS TXT 인증 + 사이트맵 + 네이버 서치어드바이저 + Daum 웹마스터
- [ ] IndexNow `<key>.txt` 배포 + Cloudflare Web Analytics 활성
- [ ] about.html · 개인정보처리방침 게재
- [ ] 첫 5~10편 정식 배포

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 GitHub Pages (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
