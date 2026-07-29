# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #48 — (상세 EVENTS #47)

- [ ] **[관찰] 07-30 11:11 사이클 3종 검증** — ①`스텐도마` 재생성이 새 정량 지시로 게이트 통과하는지(실패해도 #47 수정으로 **1일차 텔레그램 경보**·3일 침묵 없음) ②`auto_cycle.log` 한글 정상 기록(EE5③) ③pull "성공(exit=0)" 기록(EE5②). 로그 확인만으로 판정.
- [ ] **★[모니터링] 색인 전환**([[growth-first-priority]]) — GSC 색인요청 **11개**(07-20 요청)가 "색인 생성됨"으로 전환됐는지 확인. 안 되면 원인=권위/시간(코드 아님·#46서 크롤예산 확정)·발행 지속. 남는 할당량으로 나머지 URL 추가 요청.
- [ ] **★[신규 #47] 도마 클러스터 편중 대책** — 07-24~29 발행 6편 중 **4편이 도마**+cutting-board 카테고리. DD1 경고(글↔카테고리 겹침 44~50%)가 한 클러스터에 집중 → 얇은 중복으로 일부만 색인될 리스크. 씨앗 라운드로빈·카테고리 간 분산 등 검토.
- [ ] **[신규 #47] 비표준 slug 2건 점검** — article #6 slug=`1`, #18 slug=`tpu`(정상 `kw-<hash>`). slug 생성 경로 확인·영향 판단.
- [ ] **[결정] 여름이불 무인 자동비공개** — #45 발행분을 #46 사후모니터가 '미달' 자동비공개(미매핑·얇음 추정). 방치 / 개선(카테고리 매핑·상품 보강 재발행) / 침구 쿠팡 카테고리 중 택. (현재 unpublished 2편)
- [ ] **[결정 대기] draft 카테고리 3개 공개 여부** — 노트북거치대·빨래건조대·미니제습기. 공개하는 것만 씨앗 투입(미니제습기 씨앗은 **2027-04**). 새 클러스터 첫 글 사전검수 여부(기본=사후검토).
- [ ] **(선택) 게이밍의자 글 구조 이관** — article.html 폴백→카테고리 구조(주인 원하면).
- [ ] (이월) IndexNow 관찰성 갭(성공 경로 res.notes 미로그) · Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
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
- [x] **첫 5~10편 정식 배포** — ✅ 현재 **18편**(무인 자동발행 누적·07-24~29 6편 연속. DB 실측 #47)

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 GitHub Pages (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
