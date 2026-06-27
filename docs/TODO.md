# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #37 — (상세 EVENTS #36)

- [ ] **★운영 동기화 (이 세션 코드 반영)** — 운영 폴더 `git pull`(#36 커밋) + **대시보드 재시작**(자동 migrate 009 → Google 지출 트래커 작동) → 설정에서 "Google 월 상한($)" 입력. ※운영 폴더엔 현재 to_spec·yml만 수동반영·나머지(append_category_source·이미지폴백·api_usage·대시보드) 미반영.
- [ ] **★대표 이미지 채우기** — Google 월 상한(ai.studio/spend) 풀린 뒤 `D:\honsalim_test\3_run_cleanup.bat` 재실행 → 대표이미지 생성 → 대시보드 🚀 빌드·배포.
- [ ] **리뷰 별개 개선**(적대적 16건 중 미반영) — 대시보드 카탈로그 오염 가시화(승인 전 사람검토 강화)·비전게이트 프롬프트 category_intro 주입·vision cap 커버리지 경고.
- [ ] (이월) `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장=트래픽(GSC 색인·[[growth-first-priority]]) · naver_blog 볼륨(`/naver-start`).
- 참고: 워크트리=`PYTHONPATH=src python -m cli`(대시보드 시작 시 자동 migrate)·DB gitignore→재생성. **main직접머지=`git push origin HEAD:main`**. 운영 DB 직접수정 불가→주인 런처(`D:\honsalim_test\*.bat`). ★PowerShell/cmd 한글→.py·ASCII([[powershell-korean-encoding]]).

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
