# TODO.md — 혼살림 활성 작업

> 활성 작업만. 완료 항목은 STATE.md "Phase X" 행 / EVENTS.md 참조.
> Cap 5KB.

## ★ 시급 (다음 세션 #22) — #21 완료: 도메인 honsallim 이전·연결·301 · 알리 honsallim 채널 등록 · 미충전이미지 · 순차등록엔진(register-categories) · 홈 흰바탕 캐시. 남은 핵심 = **살림 카테고리 합치기 + 수익 연결**. (상세 EVENTS #21)

- [x] ~~1번 미충전이미지(페르소나·about·시나리오, placeholder 0)·2번 순차등록엔진·홈 흰바탕캐시(cache-busting)·도메인 honsalim→honsallim 이전·연결·301·알리 honsallim 채널등록·OpenRouter 잘림 자가복원·Windows wrangler resolve_argv~~ ✅ #21
- [ ] **★살림 카테고리 합치기**: `loving-herschel-0091c7` 갈래의 `sql/seeds/003_categories_living.sql` + `category_sources.yml` 살림3(**cutting-board 도마·drying-rack 빨래건조대·mini-dehumidifier 미니제습기**) git show로 추출 → `db seed` → `register-categories cutting-board drying-rack mini-dehumidifier --no-dry-run` → approve+build --full+push (~$1.5).
- [ ] **★Tracking ID 연결**: 알리 honsallim 채널 Tracking ID → `D:\secrets\affiliate_hub\ali.env`(**주인 직접**) → 제품 재수집 시 개별 deeplink. 현재 `deeplink_url`은 공통 트래킹링크(모든 제품 동일).
- [ ] **★/go/ 작동**: wrangler `deny` 룰(`.claude/settings.json`)로 Claude 배포 차단 → **주인이 deny 제거** 후 `PYTHONPATH=src python scripts/deploy_go_gateway.py`(D1 schema·sync-slugmap 191·Workers). 코드(slug_map UNION·resolve_argv) 준비됨.
- [ ] (관찰) Chrome lookalike 경고(honsalim↔honsallim 1글자) — 301+시간·정상방문 학습으로 해소. 일반 방문자는 안 볼 가능성 큼.
- [ ] (이월) 쿠팡(방문자·트래픽 후) · 무인 발행 스케줄러(매일 11시) · main-protect.
- 참고: ★코드·도메인은 origin/main(#21) 배포 완료. **DB는 gitignore→재생성**(`db migrate`+`db seed`+`register-categories --all --no-dry-run` 또는 개별, ~$1.5). 워크트리=`PYTHONPATH=src python -m cli`. 미리보기=`build --preview`·공개=`build --full`.

## 알리 통합 (D9)

- [x] ~~App Key/Secret·라이브검증(#11)·collect-products·C-1·enrich·4게이트(#12)·promote·상세글 렌더·라이브 게시(#13)~~ ✅
- [x] ~~honsalim.com whitelist('ali' 자동검증 Submit 차단)~~ → **honsallim.com 채널 등록 완료** ✅ #21 (겹ㄹ 도메인으로 'ali' 차단 돌파, Portals 나의웹사이트·content>vertical sites·별도 승인 게이트 없음)
- [ ] honsallim 채널 **Tracking ID → ali.env 연결 + 개별 deeplink** 생성 (#22) → /go/ 작동 시 수익 추적

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

## Phase 2: 핵심 시스템 — 남음

> 완료 항목은 STATE.md "Phase 2 핵심 모듈 18개" + "회귀 342/342" + "CLI 10/11" 행 참조.

- [x] ~~CLI dashboard 명령~~ ✅ 세션 #9 완료 (G3 결정으로 Claude Design 미사용, stub HTML)
- [ ] `collector.coupang` (쿠팡 가입 후·Phase 4)
- [ ] `builder.renderer/pages/sitemap/assets` (Jinja2 + DESIGN 시안)
- [ ] `dashboard.render/approve` (디자인 시안 Phase 3 의존)
- [ ] `python -m honsalim build --full` 성공 (Phase 2 종착)

## Phase 3: 디자인·콘텐츠 (2026-07)

- [ ] Claude Design 시안 3~5종 (사용자 claude.ai/design)
- [ ] 시안 1개 선정 + DESIGN.md 토큰 미세 조정
- [x] ~~Jinja2 템플릿 5종 + partials~~ ✅ 2026-05-30 (base·home·scenario_list·article·persona_hub·about + header/footer + _macros/components). 잔여: Critical CSS·Pretendard preload·JSON-LD 매크로 (정식 빌더 시)
- [ ] AI 이미지 생성 (페르소나별 2~3장, Imagen 4 Fast)
- [ ] 시즌 신학기·홈오피스 시나리오 5편 작성 (#5~#10)
- [ ] 진실성 게이트 통과 + 사용자 1클릭 승인 + 시범 1편 로컬 미리보기·배포

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
