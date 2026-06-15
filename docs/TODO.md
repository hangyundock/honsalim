# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #32 — (상세 EVENTS #31)

- [ ] **★★운영 DB 반영 (최우선·중요)** — 이 세션 승인 상태(의자 카테고리·추천 8선·LLM 가이드)는 **워크트리 복사본 DB(`data/honsalim.db`)에만** 있음. 운영 DB(`D:\affiliate_hub\data\honsalim.db`)는 미반영(옛 상태). **워크트리 폐기 시 복사본 소멸 → 반영 필수.**
  - 대시보드 닫고 **백업 후**: ① `scripts/apply_chair_taxonomy.py D:\affiliate_hub\data\honsalim.db`(rename·absorb·unpublish 멱등) + `build-category office-chair --no-dry-run`(LLM 8선·가이드 재생성·텍스트 달라짐) + `approve-category office-chair`, OR ② 워크트리 복사본을 sqlite backup으로 운영 이식(승인 콘텐츠 그대로·권장).
  - ※라이브(build/site·ea2460e)는 이미 배포·정상. 운영 DB는 다음 빌드/대시보드 일관성용.
- [ ] **부산물 정리** — `_fix_tax.py`(워크트리 루트 임시) 제거 · abandoned `article.html`/`article.css`(카테고리 모방·0 published라 무해) 정리 검토 · `category_products.product_type` 컬럼(복사본만·미사용·렌더는 이름 도출).
- [ ] (선택) 다른 카테고리(책상 등) 추천 8선 재빌드 · 모니터암·모니터 받침대 "모니터 거치"로 묶기.
- (이월) PartC 키워드 틈점수 · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장 Tier0([[growth-first-priority]]·트래픽이 진짜 병목).
- 참고: 워크트리=`PYTHONPATH=src python -m cli` · DB gitignore→재생성. 발행/배포=main 체크아웃. **main직접머지=`git push origin HEAD:main`**. ★PowerShell 한글 파이프 깨짐→.py 파일 실행([[powershell-korean-encoding]]).

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
