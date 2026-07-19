# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #46 — (상세 EVENTS #45)

- [ ] **[관찰] #45 무인·다양화·IndexNow 실전 확인** — ①내일 11:11 auto-cycle이 새 씨앗(7카테고리)에서 **주방 등 다양화 글** 발행하는지(카테고리 분포·auto_cycle.log·텔레그램) ②IndexNow 통지 실제 발송(변경분·키파일 라이브) ③미니밥솥형 카탈로그 재사용·refill 가드 라이브 정상.
- [ ] **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]) — GSC/네이버 **4→증가** 추이. **주인 콘솔 몫**: /about/·/privacy/·/method/·최근 글 색인 요청. #45 IndexNow·내부링크·E-E-A-T·씨앗 다양화 효과 관찰. 편중 지속 시 씨앗 추가·B② 정책 최소형(2~3주 관찰 후).
- [ ] **[결정 대기] draft 카테고리 3개 공개 여부** — 노트북거치대·빨래건조대·미니제습기. 공개하는 것만 씨앗 투입(미니제습기 씨앗은 **2027-04**=여름 2개월전). 새 클러스터 첫 글 사전검수 여부(기본=사후검토).
- [ ] **(선택) 게이밍의자 글 구조 이관** — article.html 폴백→카테고리 구조(주인 원하면).
- [ ] (이월) Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
- 참고: ★**매 세션 시작 시 운영 폴더 브랜치 확인**(`git -C D:\affiliate_hub branch --show-current`==main·[[autonomous-detached-head-silent-stop]]). 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). ★**무인 발행이 origin 전진→push 전 `git merge --ff-only origin/main`**([[autonomous-deploy-advances-origin]]). 운영 DB 직접수정 불가→주인 런처. ★한글→.py·ASCII([[powershell-korean-encoding]]). ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

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

- [x] honsallim.com 커스텀 도메인 연결 (라이브)
- [x] **GSC DNS 인증 + 사이트맵 + 네이버 서치어드바이저** — ✅ 셋 다 등록·사이트맵 제출·크롤링 정상 확정(#40)
- [x] **IndexNow `<key>.txt` 배포 + 구현** — ✅ #45 완료(키파일 라이브 200·배포 후 변경분 통지·키 라이브 폴링·doctor §16). Bing/Yandex용(F6 Google 무관). ※Cloudflare Web Analytics 활성은 미완(선택)
- [x] **about.html · 개인정보처리방침(/privacy/) 게재 (E-E-A-T Person Schema)** — ✅ #45 완료(운영자 Person·저자 혼살다 통일·정직성 정비·PIPA §30·라이브 검증)
- [x] **첫 5~10편 정식 배포** — ✅ 현재 12편(무인 자동발행 누적 + #45 여름이불)

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 GitHub Pages (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
