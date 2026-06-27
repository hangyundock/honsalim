# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #38 — (상세 EVENTS #37)

- [ ] **★무인 가동 결정·실행**(핵심) — 대기 키워드/쿠팡 배너 적재 → 자동 생성 몇 편으로 품질 직접 확인 → 좋으면 `auto_mode` ON + 스케줄러 등록(주인 결정·C13 '수동운영' 뒤집기). 무인 모델은 **이미 코드 완비**(#37 검증·끊김 없음). 첫 `min_published`(5)편 사람검수.
- [ ] **★발행 글 관리 탭 운영 동기화** — 운영 폴더 `git pull`(#37 a5930c6) + 대시보드 재시작 → '발행 글 관리' 탭(발행글 사후 검토·비공개/재공개·라이브링크) 노출.
- [ ] (이월) `review-helpfulknow` 월 지출 한도(무인 폭주 방지·선택) · 쿠팡 수동 배너 부트스트랩(15만원→API) · 적대적 별개개선(카탈로그 오염 가시화·비전 intro 주입) · `mini-dehumidifier` 점검 · ★성장=트래픽(GSC 색인·[[growth-first-priority]]) · naver_blog 볼륨(`/naver-start`).
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
