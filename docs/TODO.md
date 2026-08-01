# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #49 — (상세 EVENTS #48)

- [ ] **★[관찰·최우선] 본문 예산 축소 부작용** — #48이 산문 25~30%↓(출력 토큰 절감) 하면서 키워드 자연 출현이 4~7 → **3~5회(중앙 4)**로 하락. `min_count=4` 여유가 얇다(3샘플 중 1건 `count_low`). 재시도 3회가 흡수하고 08-01 정규 사이클은 시도 1회 통과했으나 **며칠 발행 안정성 관찰**. 흔들리면 총 예산 2,600~3,200 → 2,900~3,400자 상향, 검증은 `cli experiment --draft N --samples 5`(라이브 사이클 금지).
- [ ] **[입력 대기·주인] LLM 단가** — `llm_price_in_per_1m`·`llm_price_out_per_1m`이 0이라 비용 $0 표시. OpenRouter DeepSeek 실단가 입력 시 원가 집계 시작(토큰은 이미 기록 중).
- [ ] **★[모니터링] 색인 전환**([[growth-first-priority]]) — GSC 색인요청 **11개**(07-20)가 "색인 생성됨"으로 전환됐는지 확인. 안 되면 원인=권위/시간(코드 아님·#46 크롤예산 확정)·발행 지속. 남는 할당량으로 나머지 URL 추가 요청.
- [ ] **[이월 #47] 도마 클러스터 편중 대책** — 07-24~29 발행 6편 중 **4편이 도마**+cutting-board 카테고리. DD1 경고(글↔카테고리 겹침 44~50%)가 한 클러스터에 집중 → 얇은 중복으로 일부만 색인될 리스크. 씨앗 라운드로빈·카테고리 간 분산 검토.
- [ ] **[결정] 여름이불 무인 자동비공개** — #45 발행분을 #46 사후모니터가 '미달' 자동비공개(미매핑·얇음 추정). 방치 / 개선(카테고리 매핑·상품 보강 재발행) / 침구 쿠팡 카테고리 중 택. (현재 unpublished 2편)
- [ ] **[결정 대기] draft 카테고리 3개 공개 여부** — 노트북거치대·빨래건조대·미니제습기. 공개하는 것만 씨앗 투입(미니제습기 씨앗은 **2027-04**).
- [ ] **(선택) LLM 추적 미연결 경로** — 카테고리 가이드 생성(`generate_raw`)·비전 게이트(Haiku)·카테고리 설정 생성은 `api_usage` 기록 미연결. 일일 비용 주동력은 글 생성이라 후순위.
- [ ] **(선택) 게이밍의자 글 구조 이관** — article.html 폴백→카테고리 구조(주인 원하면).
- [ ] (이월) IndexNow 관찰성 갭(성공 경로 res.notes 미로그) · Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
- ※**완료(#48)**: 무인 발행 밀도 벽(B2 절대 하한) · 1인칭 오탐 · 비표준 slug(라이브 3건 URL은 주인 결정으로 유지) · #47 관찰 3종(pull 판정 ✅·로그 인코딩 부분 해결·스텐도마는 다른 키워드로 대체돼 미검증).
- 참고: ★**매 세션 시작 시 운영 폴더 브랜치 확인**(`git -C D:\affiliate_hub branch --show-current`==main·[[autonomous-detached-head-silent-stop]]). 워크트리=`PYTHONPATH=src python -m cli`(자동 migrate). ★**무인 발행이 origin 전진→push 전 `git merge --ff-only origin/main`**([[autonomous-deploy-advances-origin]]). 운영 DB 직접수정 불가→주인 런처. ★한글→.py·ASCII([[powershell-korean-encoding]]). ★Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]).

## 시점 의존 잔존 (세션 #6~7)

- [ ] 알리 이미지·상세페이지 정책 조사 (Phase 5 전) · M2/M4/M5/M6 (`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6)
- [ ] **혼살림 M2 Person Schema + about 운영자 정보** (Phase 4, E-E-A-T) — 사전결정 완료(필명 "혼살다"·사진없음, DECISIONS M2). 코드=`_macros/person.html`+`about.html`(FRONTEND §4-5)

## Phase 1: 인프라 — 남음

- [ ] `.claude/settings.json` deny 룰 사용자 검토 (deny 24·allow 14) · Branch Protection에 Actions status check
- 보류: BitLocker(사용자 결정) · 쿠팡 파트너스 재가입(Phase 4 출시 후)

## Phase 2~4 — 대부분 완료 (상세 STATE)

- Phase 2~3: 빌더·렌더러·템플릿·디자인·대시보드·발행경로 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지(Imagen·페르소나별) · 시즌 시나리오 작성.
- Phase 4: 도메인·GSC·사이트맵·네이버 SA ✅(#40) / IndexNow ✅(#45) / about·privacy·Person Schema ✅(#45) / **정식 배포 20편**(#48 실측·무인 자동발행 누적). ※Cloudflare Web Analytics 활성은 미완(선택)

## 보류 (Phase 6+)

- AdSense 신청 결정(2026-12) · 영어 사이트 확장(2026-12 검토) · 보조 호스팅 GitHub Pages(트래픽 100+/일) · 다크 모드(Phase 5+) · 검색·햄버거 메뉴·이메일 알림
