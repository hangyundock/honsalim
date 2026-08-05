# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 다음 세션 #51 — (상세 EVENTS #50 · DECISIONS HH)

- [ ] **★[관찰·최우선] 08-06 사이클 1일차 (#50 수정이 라이브에서 처음 도는 날)** — (a) **도마가 아닌** 키워드(예상 `1인밥솥`)가 뽑히는가 = 카테고리 균형 작동 (b) 로그에 **"리필 검색량 조회 실패"가 없는가** = 네이버 연결 정상(있으면 키 문제가 별도로 존재). ★확인: `logs/auto_cycle.log` tail + `data/auto_cycle_last.json`(`refill_degraded` 필드).
- [ ] **[관찰] laptop-stand 색인 전환** — 되면 **빨래건조대·미니제습기도 공개** 판단(HH6). 둘은 씨앗이 없어 리필 기여 0·구조 페이지 노출만(재고는 45·28개로 충분).
- [ ] **[미해결] monitor-stand 리필 공급 부족** — 도달 가능 씨앗 3개 중 2개 소진인데 **보강 재료 없음**(HH8). 균형 로직이 다른 카테고리로 채워 발행은 안 멈춘다. core('받침대') 완화는 TV거치대·멀티탭 노이즈 유입이라 미채택.
- [ ] **[주인 확인] 08-02(일) 사이클 미기동** — 로그 자체가 없음(코드 정지 아님·전후 정상). 스케줄러 조회가 TIMA 가드에 막혀 **확인 불가**. PC 절전 여부 확인 필요.
- [ ] **★[모니터링] 색인 요청 2차분**([[growth-first-priority]]) — 주인 08-05 실행. 1차(07-20 11개)는 **색인 4→18 전환 확인**됨. 2차 효과 확인 후 남는 할당량으로 추가 요청.
- [ ] **[이월 #47] 도마 클러스터 편중 대책** — 07-20~27 리필이 도마 6편 연속 생성(원인=HH1·HH2 **수정 완료**). 이미 발행된 6편의 상호 경쟁은 남음 — GSC 실측 상위 노출 0편, 통합·차별화 판단 필요.
- [ ] **[결정] 여름이불 무인 자동비공개** — #45 발행분을 #46 사후모니터가 '미달' 자동비공개. 방치 / 개선(매핑·상품 보강 재발행) / 침구 쿠팡 중 택(현재 unpublished 2편). ※#49 실측: seo는 7회·1.34%로 **기준 자체는 충족**.
- [ ] **(선택)** 브랜드 blocklist 보강(노스바유·어고트론·NB·알파스캔·한성 — 사람 추천 목록에만 노출·GG2 경고가 커버) · LLM 추적 미연결 경로(카테고리 가이드·비전 게이트) · 게이밍의자 글 구조 이관.
- [ ] (이월) **IndexNow 통지 오탐**(HH10 — 키 파일이 라이브 200인데 "미라이브"로 생략. 폴링 4회×30초가 CI를 못 기다린 것으로 보이나 첫 시도 실패 이유 [확인 불가]. **Google 무관**이라 우선순위 낮음) · Phase 2 자가복원(배포 drift) · `review-helpfulknow` 월상한 · 쿠팡 부트스트랩(15만원→API).
- ※**완료(#50)**: 리필 캐시 강등 근본수정(`load_secrets`·HH1) · 카테고리 균형(HH3) · 캐시 강등 fail-loud(HH4) · GSC 색인 4→**18** 확인(HH5) · laptop-stand 공개(HH6) · 도달 불가 씨앗 lint(HH7) · **LLM 단가=불요 결정**(HH9·월 수백 원·토큰 추적만으로 급증 감지 유효) · **씨앗 보강 자체 기각**(HH8 — ★옛 TODO "보강 후보=미매핑 20건"은 **틀린 안내**: 13건이 과포화 의자·`허리디스크의자`는 비YMYL 소지·나머지는 다른 제품/정보성/브랜드).
- 참고: ★**작업 함정**(매 세션) — 운영 폴더 브랜치==main 확인([[autonomous-detached-head-silent-stop]]) · push 전 `git merge --ff-only origin/main`([[autonomous-deploy-advances-origin]]) · 한글→.py·ASCII([[powershell-korean-encoding]]) · Edit 절대경로=운영 폴더 주의([[worktree-edit-path-footgun]]) · 워크트리=`PYTHONPATH=src python -m cli` · 운영 DB 직접수정 불가→주인 런처 · **운영 모듈 직접 import 시 `config.load_secrets()` 선행**([[project_verify_script_load_secrets]] — #50 근본원인이 이것).

## 시점 의존 잔존 · Phase 1~4 남음

- [ ] 알리 이미지·상세페이지 정책 조사(Phase 5 전) · M4/M5/M6(`GOOGLE_AI_OPTIMIZATION.md` §6, Phase 3~6). ※M2 Person Schema는 #45 완료.
- [ ] `.claude/settings.json` deny 룰 사용자 검토(deny 24·allow 14) · Branch Protection에 Actions status check
- Phase 2~3 완료(사이트 라이브). 잔여: `collector.coupang`(15만원 후) · AI 이미지(Imagen·페르소나별) · 시즌 시나리오.
- Phase 4: 도메인·GSC·사이트맵·네이버 SA ✅(#40) / IndexNow·about·privacy·Person Schema ✅(#45) / **정식 배포 22편·카테고리 7개**(#50 실측). ※Cloudflare Web Analytics 활성 미완(선택 — #50 실측상 사이트 내 방문·클릭 측정은 현재 전무)
- 보류: BitLocker · 쿠팡 재가입(Phase 4 후) · AdSense(2026-12) · 영어 확장(2026-12 검토) · 보조 호스팅(트래픽 100+/일) · 다크 모드 · 검색·햄버거 메뉴·이메일 알림
