# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #35 — (상세 EVENTS #34)

- [ ] **★★자동실현(완전 무인) 실제 라이브 테스트** (주인 #34 명시·최우선) — ①draft 7·8 등 미리보기 검토→승인→발행으로 **첫 5편 사람 검수·발행**(min_published=5 게이트 충족) ②설정 `auto_mode` ON ③'예약 켜기'(스케줄러 auto-cycle 등록) ④winnable 키워드 자동선정→생성→(5편후)자동승인→발행·배포 **전체 1회 라이브 검증**. **무인 가동 OFF→ON 실증이 목표.**
- [ ] (이월) 쿠팡 이미지 테스트(키워드 쿠팡 첨부→글 생성→상단 운영자추천 zone) · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장 Tier0([[growth-first-priority]]·트래픽이 진짜 병목).
- 참고: **draft 5·6=article.html 폴백(단순)·draft 7·8=카테고리 구성**(이미지·전체 카탈로그). 워크트리=`PYTHONPATH=src python -m cli`(★대시보드 시작 시 자동 migrate) · DB gitignore→재생성. **main직접머지=`git push origin HEAD:main`**. ★PowerShell/cmd 한글 깨짐→.py·ASCII([[powershell-korean-encoding]]).

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
