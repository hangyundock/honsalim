# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #36 — (상세 EVENTS #35)

- [ ] **★비전 게이트·자동 카테고리 라이브 첫 실행** (감독 권장) — ①`D:\secrets\affiliate_hub\`에 **ANTHROPIC_API_KEY 존재 확인**(비전 게이트 필수·없으면 fail_closed 전량드롭) ②`provision-category <품목> --no-dry-run` 1개 실증(설정생성→수집(vision)→빌드 draft) ③대시보드 draft 검토→승인→배포 ④품질·비용·드롭률 확인.
- [ ] **naver_blog 볼륨 자동화 본격** (별도 프로젝트·`/naver-start`) — 6/16 첫 무인 자동발행 결과 확인 + 키워드 7개 7일 스케줄러 테스트(주인 모델·네이버 C-Rank 권위라 honsalim보다 적합).
- [ ] (이월) 쿠팡 카테고리 배너(카테고리·모니터링 탭) · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장=트래픽(GSC 색인·[[growth-first-priority]]).
- 참고: 운영 폴더=#35 동기화(fc1bf29+). 워크트리=`PYTHONPATH=src python -m cli`(대시보드 시작 시 자동 migrate)·DB gitignore→재생성. **main직접머지=`git push origin HEAD:main`**. 운영 DB 직접수정 불가→주인 런처. ★PowerShell/cmd 한글→.py·ASCII([[powershell-korean-encoding]]).

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
