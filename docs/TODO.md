# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #43 — (상세 EVENTS #42)

- [ ] **[관찰] #42 라이브 효과 확인** — ①발행 글 넓은 카탈로그(24~41개)·빵부스러기·세부 가이드 칩이 honsallim.com 실반영 curl/브라우저 ②텔레그램 발행 알림(제목+URL)이 매일 예약 후 오는지 ③제공자 403 재시도·생성 예외 자가복원이 실전 무인 사이클을 안 죽이는지(로그).
- [ ] **미발행 승인글 2편 검토·결정**(게이밍의자·노트북받침대) — 라이브 미리보기로 품질 확인 후 발행/유지(주인 "검토 후 결정" 선택).
- [ ] **★성장 — 색인 커버리지 관찰·가속**([[growth-first-priority]]) — GSC/네이버 **색인 4→증가** 추이. #42 내부링크 대폭 강화 효과 기대. 핵심 URL 색인 요청. **씨앗 커버리지 확장**(seo_keywords.yml 미매핑) · **E-E-A-T**(M2 Person Schema+about).
- [ ] (이월) Phase 2 자가복원(ali off-target·배포 drift·git pull footgun) · IndexNow(Bing/Yandex) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
- [ ] **[별개 프로젝트] D:\naver_blog #11 미커밋** — 이번 세션에 리치 글 엔진(post 13)·알리 연동 작업 후 문서 갱신했으나 **커밋 안 됨**. `/naver-end`로 별도 마무리 필요(회귀 152).
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
