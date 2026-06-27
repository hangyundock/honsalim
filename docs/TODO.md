# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #41 — (상세 EVENTS #40)

- [ ] **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]) — #40 배포(내부링크·favicon·robots) 효과로 GSC/네이버 **색인 4→증가** 1~2주 추이 확인. 핵심 페이지 **URL 색인 요청**(GSC `URL 검사`·네이버 `웹 페이지 수집`: 글 2편→의자·모니터받침대 카테고리). robots `/cdn-cgi/`는 다음 빌드·배포 시 라이브(무해·급하지 않음).
- [ ] **[관찰] 무인 스케줄러 실작동 점검** — 대시보드 '무인 사이클 마지막 실행 **2026-06-06**' 표시. 22:02 자동 발행이 **실제 매일 도는지** 확인(미작동이면 완전무인인데 발행 0). 스케줄러 등록/로그 점검.
- [ ] (이월·성장) **씨앗 커버리지 확장**(seo_keywords.yml '미매핑' 해소) · **E-E-A-T**(M2 Person Schema+about 운영자) · (선택) IndexNow 구현(Bing/Yandex·#39 감사 미구현 확인).
- [ ] (이월) Phase 2 자가복원(ali off-target·배포 drift·푸시채널·git pull footgun) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API) · naver_blog 볼륨.
- 참고: 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). **main직접머지=`git push origin HEAD:main`**. 운영 DB 직접수정 불가→주인 런처. ★한글→.py·ASCII([[powershell-korean-encoding]]). ★무인 발행이 origin 전진([[autonomous-deploy-advances-origin]])—푸시 전 ff/merge. ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

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
- [x] **GSC DNS 인증 + 사이트맵 + 네이버 서치어드바이저** — ✅ 셋 다 등록·사이트맵 제출·크롤링 정상 확정(#40). Daum 웹마스터는 미등록(선택)
- [ ] IndexNow `<key>.txt` 배포 + 구현 (Bing/Yandex·미구현 #39 확인) + Cloudflare Web Analytics 활성
- [ ] about.html · 개인정보처리방침 게재 (E-E-A-T Person Schema)
- [ ] 첫 5~10편 정식 배포 (현재 2편)

## 보류 (Phase 6+)

- AdSense 신청 결정 (2026-12)
- 영어 사이트 확장 (2026-12 검토)
- 보조 호스팅 GitHub Pages (Phase 4 트래픽 100+/일 도달 시)
- 다크 모드 (Phase 5+)
- 검색 기능·햄버거 메뉴·이메일 알림 (Phase 4)
