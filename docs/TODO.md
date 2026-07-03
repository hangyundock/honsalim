# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #42 — (상세 EVENTS #41)

- [ ] **[관찰] 무인 재생성 실발행 추적**(#41 자가복원 검증) — pending 복귀한 4개(등받이·메쉬·허리편한·게이밍책상)+서재책상이 **개선된 재생성으로 실제 발행되는지** 매일 확인(하루 1편·나흘 순차). 재반려 시 자동 재시도(상한3)·상한 도달 failed 격리+[ALERT]/텔레그램 오는지. **텔레그램 일일 리포트(하트비트)가 11:11 후 실제 오는지** 첫날 확인.
- [ ] **미발행 승인글 2편 검토·결정**(게이밍의자·노트북받침대) — 라이브 미리보기로 품질 확인 후 발행/유지(주인 "검토 후 결정" 선택).
- [ ] **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]) — GSC/네이버 **색인 4→증가** 1~2주 추이. 핵심 URL 색인 요청. **씨앗 커버리지 확장**(seo_keywords.yml 미매핑) · **E-E-A-T**(M2 Person Schema+about).
- [ ] (이월) Phase 2 자가복원(ali off-target·배포 drift·git pull footgun) · IndexNow(Bing/Yandex) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API) · naver_blog 볼륨.
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
