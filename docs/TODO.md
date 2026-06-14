# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #31 — (상세 EVENTS #30 / docs/ARTICLE_LAYOUT_TIER2.md)

- [ ] **★글 레이아웃 Tier2 구현 (최우선)** — 글을 "독서(텍스트벽)"→"쇼핑(스캔)"으로. 전체 블루프린트·근거·구현필드=**docs/ARTICLE_LAYOUT_TIER2.md**.
  - **구조**: ⚡빠른 결론 박스 → 🏆큐레이션 픽 카드(역할배지·소스배지·장단점) → 본문 체크포인트 박스 → 📊한눈에 비교표(1위 강조) → 💰예산대별 표 → 🤝신뢰 박스 → ❓FAQ 아코디언.
  - **(A) LLM enrich 구조화 출력**: `quick_verdict`·`picks[]`(역할·장단점·이런분께)·`checkpoints[]`·`budget_tiers[]`(+기존 faqs). graceful fallback. **(B) 템플릿**: 카테고리 시각 컴포넌트 재사용 + 빠른결론 박스 신규.
  - ★**목업 먼저 확정** → 구현 → 미리보기 HTTP 검증 → 배포. ★**중복콘텐츠 회피**(글=시나리오 큐레이션·카테고리=전체, 의도 분리). 별점 금지·판매량=신뢰.
  - Tier1(#30)에서 renderer 데이터플러밍(source·할인·판매량·본문분할·소스분리)·`product_card` 매크로 완료→**재사용**(article.html 레이아웃만 교체).
- [ ] **★발행 build/site 자동커밋 버그 근본수정** — `cmd_publish_queue`/`cmd_deploy`가 build/site 커밋 안 함→클릭만으론 글 404(수동 커밋해야 라이브). 자동 커밋 단계 추가(무인 치명).
- [ ] **미리보기 file://→HTTP 서빙** — 미리보기 버튼이 절대경로 CSS/이미지를 file://로 못 띄움(무스타일·이미지 안보임). 로컬 HTTP 서빙으로 충실한 미리보기.
- (이월) PartC 키워드 틈점수 · off-target 씨앗 curation · `mini-dehumidifier` 점검 · 쿠팡 본격(15만원 후) · ★성장 Tier0([[growth-first-priority]]·트래픽이 진짜 병목).
- 참고: 워크트리=`PYTHONPATH=src python -m cli` · DB gitignore→재생성(`db migrate`+`db seed`+`register-categories --all --no-dry-run`). 발행/배포=main 체크아웃. **main직접머지=`git push origin HEAD:main`**.

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
