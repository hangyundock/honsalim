# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #33 — (상세 EVENTS #32)

- [ ] **★★실제 제품 추가 배포 테스트 (주인 명시·최우선)** — 이번 세션 만든 대시보드 기능(카테고리 쿠팡 추가/제거·키워드 삭제·🚀 빌드·배포)으로 **실제 쿠팡 제품을 카테고리에 추가 → 빌드·배포** 하여 동작 검증. 운영 폴더는 #32(e3a2219) 동기화 완료(추가 git pull 불요·대시보드 재시작만).
- [ ] **부산물 정리** — `category_products.product_type` 컬럼(운영 DB·미사용·렌더 무관) · 옛 워크트리들 · 바탕화면 런처 3폴더(`honsalim_db_apply`·`honsalim_update`·`혼살림DB반영`) 삭제(주인).
- [ ] (선택) 다른 카테고리 쿠팡 추가 · 추천 8선 재빌드 · 모니터암·모니터 받침대 "모니터 거치"로 묶기.
- (이월) PartC 키워드 틈점수 · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장 Tier0([[growth-first-priority]]·트래픽이 진짜 병목).
- 참고: 워크트리=`PYTHONPATH=src python -m cli` · DB gitignore→재생성. **main직접머지=`git push origin HEAD:main`**. ★PowerShell/cmd 한글 깨짐→.py·ASCII([[powershell-korean-encoding]]).

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
