# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #50 — (상세 EVENTS #49 · DECISIONS GG)

- [ ] **★[관찰·최우선] #49 수정 라이브 1일차 (08-05 11:11)** — (a) 래퍼 `git pull`이 새 코드·씨앗을 실었는지 (b) `32인치모니터암` 재생성 시 **"SEO 주입" 로그**가 찍히고 seo 게이트가 `skip`이 아니라 실측되는지 (c) 실패해도 다른 키워드로 자동 재개되는지. ★확인 명령: `logs/auto_cycle.log` tail + `data/auto_cycle_last.json`.
- [ ] **★[관찰] 리필 풀 소진 속도** — 적격 **18개 ≈ 18일치**(GG7). 소진되면 생성 0편·[ALERT]. 보강 후보 = #49가 관측한 **미매핑 탈락 20건**(키보드받침대 5,800·자바라거치대 4,370·컴퓨터의자추천 3,740·회의용의자 3,570 등).
- [ ] **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님·08-01·03·04은 정상). 작업 스케줄러 조회가 TIMA 가드에 막혀 **확인 불가**. PC 절전·미가동 여부 확인 필요.
- [ ] **[입력 대기·주인] LLM 단가** — `llm_price_in_per_1m`·`llm_price_out_per_1m`이 0이라 비용 $0 표시. OpenRouter DeepSeek 실단가 입력 시 원가 집계 시작(토큰은 이미 기록 중).
- [ ] **★[모니터링] 색인 전환**([[growth-first-priority]]) — GSC 색인요청 **11개**(07-20)가 "색인 생성됨"으로 전환됐는지 확인. 안 되면 원인=권위/시간(코드 아님·#46 크롤예산 확정)·발행 지속. 남는 할당량으로 나머지 URL 추가 요청.
- [ ] **[이월 #47] 도마 클러스터 편중 대책** — 07-24~29 발행 6편 중 **4편이 도마**+cutting-board 카테고리. DD1 경고(글↔카테고리 겹침 44~50%)가 한 클러스터에 집중 → 얇은 중복으로 일부만 색인될 리스크. 씨앗 라운드로빈·카테고리 간 분산 검토.
- [ ] **[결정] 여름이불 무인 자동비공개** — #45 발행분을 #46 사후모니터가 '미달' 자동비공개. 방치 / 개선(매핑·상품 보강 재발행) / 침구 쿠팡 중 택(현재 unpublished 2편). ※#49 실측: seo는 7회·1.34%로 **기준 자체는 충족**.
- [ ] **[결정 대기] draft 카테고리 3개 공개 여부** — 노트북거치대·빨래건조대·미니제습기. 공개하는 것만 씨앗 투입(미니제습기 씨앗은 **2027-04**). ※#49 리필 실측에서 laptop-stand 후보 7건이 `category_draft`로 탈락 중 — 공개하면 리필 풀이 늘어난다.
- [ ] **(선택) 브랜드 blocklist 보강** — #49 네이버 실측에서 노스바유·어고트론·NB·알파스캔·한성 모니터암이 `DEFAULT_BRAND_BLOCK` 미등재라 추천 후보에 올라온다(미매핑이라 무인 리필은 자동 배제·사람 경로만 노출). GG2 경고가 커버하므로 후순위.
- [ ] **(선택) LLM 추적 미연결 경로** — 카테고리 가이드 생성(`generate_raw`)·비전 게이트(Haiku)·카테고리 설정 생성은 `api_usage` 기록 미연결. 일일 비용 주동력은 글 생성이라 후순위.
- [ ] **(선택) 게이밍의자 글 구조 이관** — article.html 폴백→카테고리 구조(주인 원하면).
- [ ] (이월) IndexNow 관찰성 갭(성공 경로 res.notes 미로그) · Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
- ※**완료(#49)**: 08-04 발행 0편 복구 · seo 미검증 글 자동발행 봉인(GG3) · 씨앗 인치 변형 6개(GG6) · 사람 추가/승인 경로 경고(GG2·GG5) · draft #48 폐기 · **#48 본문 예산 관찰 종료**(GG8 — 재현 안 됨·상향 불요).
- 참고: ★**작업 함정**(매 세션) — 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) · push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) · 한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처.

## 시점 의존 잔존 · Phase 1~4 남음

- [ ] 알리 이미지·상세페이지 정책 조사(Phase 5 전) · M4/M5/M6(`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6). ※M2 Person Schema는 #45 완료.
- [ ] `.claude/settings.json` deny 룰 사용자 검토(deny 24·allow 14) · Branch Protection에 Actions status check
- Phase 2~3 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지(Imagen·페르소나별) · 시즌 시나리오.
- Phase 4: 도메인·GSC·사이트맵·네이버 SA ✅(#40) / IndexNow·about·privacy·Person Schema ✅(#45) / **정식 배포 21편**(#49 실측). ※Cloudflare Web Analytics 활성 미완(선택)
- 보류: BitLocker · 쿠팡 재가입(Phase 4 후) · AdSense(2026-12) · 영어 확장(2026-12 검토) · 보조 호스팅(트래픽 100+/일) · 다크 모드 · 검색·햄버거 메뉴·이메일 알림
