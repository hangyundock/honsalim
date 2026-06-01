# STATE.md — 혼살림 현재 운영 상태

> 현재 진실만 기록. 이력은 EVENTS.md / DECISIONS.md 참조.
> 매 세션 종료 시 변경 영역만 갱신. Cap 10KB.

## 운영 현황 (Live)

| 영역 | 값 | 최종 확인 세션 |
|------|----|---------------|
| 진행 단계 | **#20: ★알리 'ali' 도메인 차단 해결(honsallim.com 구매·코드이전·미배포) + 홈 카테고리 우선 재편·실이미지·시즌 컬러타일 + ★콘텐츠 성장 전략·네이버 실측 방법론 + 1인 살림 카테고리 착수**(로컬·미배포). 도메인 honsalim→honsallim(코드 10곳 이전) / 홈=카테고리 카드+개념이미지(시나리오 대체) / ★키워드 네이버 실측("1인 ○○" 빈약→대표어+보조키워드) / 살림 3카테고리 seed+소스, **도마 수집·관련성 검증(45→25 정제)**. 회귀 **623 유지**. 남음=2카테고리 수집·정제·seo_keywords·build×3·미리보기·승인·배포·알리등록. 상세 EVENTS #20 / DECISIONS Q | 2026-06-02 #20 |
| 운영 모델 | 자동 게시 활성 (윈도우 스케줄러 매일 11:00 KST) + 발행 편수 최대화 + 보안 강화 7건. 자동 "승인"은 절대 금지 (E7) | #2 |
| Phase 1 완료 (#2~#3) | GitHub(2FA·Secrets·main-protect)·Cloudflare(도메인·Pages·R2·D1)·Anthropic·INDEXNOW 키·secrets·Git push·pre-commit 9종·Dependabot (세부 archive) | #3 |
| Phase 2 핵심 모듈 (#3~#5) | cli·common·validator·writer·collector·enricher·builder·deployer·tracker·workers (세부 BACKEND §2) + **#17: category_collect·category_page_builder·concept_image·category_writer** | #17 |
| Phase 2 회귀 테스트 | **623 / 623 PASS** [확정 pytest, #20] — #20은 도메인 이전·홈 카테고리화로 test_renderer 단언 갱신(신규 net 0, 623 유지). #19 +33. black·ruff·mypy 클린 | 2026-06-02 |
| CLI 명령 (BACKEND §9) | **18개** — doctor · db · collect · collect-products · enrich · validate · approve · promote · unapprove · deploy · sync-slugmap · build(+`--preview` draft포함 미리보기, #18) · dashboard · collect-category · build-category · **approve-category(#18 신규: draft→published 1클릭 승인)** · **unapprove-category(#18 신규: 공개 취소)** | #18 |
| Phase 2 흐름 골격 | collected→enriched→validated/rejected→approved→published 6 상태 + **5 게이트**(truth·schema·disclosure·links·**seo**, validate_and_save) + META-JSON + Article JSON-LD. 세부 DECISIONS J·O + EVENTS | #4~#16 |
| doctor (BACKEND §9) | §1~§14 + §10 모듈 진입점 **64개** + #19 **LLM 키 점검**(활성 모델 기준 OPENROUTER/ANTHROPIC). 64/64 OK | #19 |
| DB 초기화 | `data/honsalim.db` **v6** + categories(**8**: 홈오피스5(의자·책상·모니터받침대·노트북거치대·모니터암) + #20 살림3(**도마·빨래건조대·미니제습기**, seed `003`·전부 draft)) + **도마 라이브수집 25제품 연결**(빨래건조대·미니제습기 미수집) + products 정가/할인·판매량/만족도 (migration 002~006) + personas 3·scenarios 10. ※DB gitignore — 본 워크트리=**determined-bouman(#19) 복사본 + seed003 + 도마수집**. 새 워크트리=`db migrate`+`db seed`+`collect-category`로 재생성(seed·sources 커밋됨) | #20 |
| 설계 문서 진척 | **12/12 완료** + SUMMARY (docs/ 참조). 일관성 모순 0건 | #2 |
| 메모리 시스템 | feedback 7건([[incremental-critical-review]]·[[autonomous-safe-system]] 등) + reference market_research + MEMORY.md | #12 |
| 5파일 시스템 + 슬래시 명령 | ✅ 구축 (start/save/end) | #1 |
| 사이트 게시글 / 트래픽 / 수익 | **1편 라이브** (honsalim.com #13) — ※라이브는 **옛 도메인·옛 사이트**. 신 도메인 **honsallim.com 구매·코드이전 완료·미배포**(#20). 로컬: 홈오피스4 draft(#19) + 살림3 착수(도마 수집·검증, **빌드 전**) / N/A / N/A (수익은 /go/ + 알리 honsallim 등록 후) | #20 |

## 인프라

| 항목 | 값 |
|------|----|
| 프로젝트 폴더 | `D:\affiliate_hub\` (docs·archive·.claude/commands 하위) |
| 사이트 / 도메인 | 혼살림 / **honsallim.com**(신·겹ㄹ·만료 2027-06-01·Auto Renew, #20 알리 'ali' 차단 회피 이전·코드완료·**미배포·미연결**) + honsalim.com(구·만료 2027-05-28·#13 라이브 유지·→honsallim 301 예정) |
| 호스팅 | **Cloudflare Pages `honsalim`** + Custom domain (Dugi2020@naver.com) |
| GitHub | **`hangyundock/honsalim` Public** — origin/main = **e763e0f (#13)**, 배포됨. **build-and-deploy 워크플로 #13 재작성: main push → 커밋된 build/site를 Cloudflare Pages 배포 (CI 재빌드 없음, 글 DB는 로컬). 배포 success 확인** + CodeQL · lint · security(월간 pip-audit) ✅. ※로컬 main worktree(D:\affiliate_hub)는 7b572ad로 뒤처짐 — 다음 세션 pull 권장 |
| GitHub Secrets / Branch Protection | CF_API_TOKEN · CF_ACCOUNT_ID · INDEXNOW_KEY 등록 / ruleset `main-protect` Active |
| R2 / D1 | `honsalim-images` (APAC) / `honsalim-clicks` ID `9bae858e-456f-40e7-8084-c3b90e4ec3ca` |
| Python | 3.10 32-bit (TIMA·AutoBlog 시스템 공유) |
| DB / 로그 | `data/honsalim.db` (v6) / `logs/honsalim.log` (Phase 2) |
| secrets | **`D:\secrets\affiliate_hub\`** (cloudflare.env·indexnow.env·ali.env·복구 코드 2종) + **`D:\secrets\honsalim.env`** (GOOGLE_API_KEY) + **`D:\secrets\.env` OPENROUTER_API_KEY** (K-Content 공유 — DeepSeek 본문생성 경유, 세션 #19) |

## 자격증명 만료 (시급 사안)

| 자격증명 | 상태 | 갱신 |
|---------|------|------|
| 도메인 honsallim.com(신)/honsalim.com(구) | 2027-06-01 / 2027-05-28 | 둘 다 Auto Renew. 구→신 301 예정(#21) |
| Cloudflare API Token | 활성 (만료 GUI 미지원) | 6개월 회전 권장 — **2026-11-28** [추정] |
| Anthropic API Key | 영구 [관찰] | 6개월 회전 권장 — **2026-11-28** [추정] |
| INDEXNOW_KEY | 영구 [확정 — 공개 키] | 회전 불요 |
| GitHub PAT | 미발급 (Actions는 GITHUB_TOKEN 자동) [확정] | — |
| AliExpress Portals | **App Key/Secret·라이브 검증 완료** [확정]. ~~honsalim.com whitelist~~ **거부 확정 [확정 #20]**: XFeedback "Done"·"site/channel url containing string ali cannot be added" — 'ali' 문자열 영구 불가(자동+사람) → **honsallim.com(겹ㄹ)으로 이전**, 알리 폼 'ali' 통과 라이브 확인. #21: honsallim.com 채널 폼 제출(사이트 배포 후 소유권 인증) | 2026-06-02 |
| 쿠팡 파트너스 | 보류 | Phase 4 (콘텐츠 누적 후) 재가입 |

## 보안 / 권한

| 항목 | 상태 |
|------|------|
| `.claude/settings.json` deny 24·allow 14 | 사전 작성 완료 — Phase 1 사용자 검토 대기 |
| `D:\secrets\affiliate_hub\` 격리 | ✅ 운영 중 |
| pre-commit hook (9종) | ✅ detect-secrets v1.5.0 + trim/eof/yaml/json/large-files/merge-conflict/private-key + black·ruff·mypy 모두 Passed |
| GitHub Secrets / Branch Protection | ✅ 등록 / Active |

## 알려진 잔존 미해결

### ★ 시급 (다음 세션 #21) — #20 갱신 (상세 EVENTS #20 / DECISIONS Q). 도메인 이전·홈 재편·콘텐츠 전략·도마 착수 완료 → **나머지 살림 카테고리 정밀 구축 + 배포**가 다음.
> ★주인 원칙: **카테고리 신중·정밀·치밀**(잘못 짜면 페이지 전체 변경, Q5). 키워드는 **네이버 실측만**(상상 금지·Q3) — "1인 ○○"는 빈약하니 대표어+보조키워드.
1. **★나머지 2 살림 카테고리 수집·정제**: drying-rack·mini-dehumidifier `collect-category --no-dry-run` → 제품명 관련성 검증 → 오염 시 제외어 보강·재수집(도마 루프 그대로·Q5). (행거 68K·수납 46K·욕실선반 18K는 후속 확장 후보)
2. **seo_keywords.yml 등록**: 3 카테고리 대표+보조(실측값 — 도마/스텐도마/나무도마, 빨래건조대/접이식/미니, 미니제습기/원룸제습기/소형).
3. **build-category ×3**(도마·빨래건조대·미니제습기): DeepSeek 글 + Imagen 개념이미지(~$1.5-3)→draft. + **히어로 전용 배너 이미지**(카드 중복 해소·주인 지시).
4. **build --preview → 홈 확인(카테고리 7개) → 승인(`approve-category`) → honsallim.com 연결·배포·301**(honsalim→honsallim, CF Pages 커스텀도메인 + Redirect Rule).
5. **알리/쿠팡 등록**: honsallim.com 알리 채널 폼 제출(소유권 인증·사이트 라이브 후) + 쿠팡(가전용·Q4).
6. (이월) ★/go/ 링크 작동·main-protect 재활성화·office-chair 생성·노트북'전화'제외어.
- 참고: 미리보기=`PYTHONPATH=src python -m cli build --preview`(draft 포함, build/preview) + `localhost:8791`(.claude/launch.json). 공개=`build --full`. ★워크트리 실행=`PYTHONPATH=src python -m cli`. DB는 gitignore(determined-bouman 복사본+도마수집) → 새 워크트리는 `db migrate`+`db seed`+`collect-category` 재생성.

### 해소 (세션 #20) — 상세 EVENTS #20 / DECISIONS Q
- ~~★알리 'ali' 도메인 차단~~ ✅ **honsallim.com 구매·코드 이전**(단어 자체 문제→겹ㄹ 표준표기, 알리 폼 통과 확인). ※연결·배포는 #21
- ~~홈 회색 플레이스홀더·시나리오 구조~~ ✅ 카테고리 우선 재편 + 실 개념이미지 + 시즌 컬러타일
- ~~콘텐츠 고갈/SEO 우려~~ ✅ 성장 전략(세분화×Pillar/Cluster×갱신엔진) + ★네이버 실측 방법론 확립
- ~~상상 키워드 위험~~ ✅ 실측으로 "1인 ○○" 빈약 입증 → 대표어 전략 + 도마 수집·관련성 검증 루프 확립

### Phase 2 진척 가능 (검토 의존 큼)
- `src/builder/manifest.py` 증분 빌드 (ARCH §7·DB §10) · `src/collector/coupang.py` (Phase 4)
- (이전 해소분 #7·#9·#10·#12는 EVENTS archive 참조)

### Phase 1 잔존 (작음)
- Actions status check Branch Protection 추가 (Phase 2 안정 후)
- BitLocker 활성 (사용자 결정)
- (완료) 알리 Tracking ID·App Key/Secret 발급·ali.env 저장·라이브 검증 — 2026-05-30

### 보류
- AdSense 신청 (Phase 6, 2026-12)
- 영어 사이트 확장 (Phase 6 검토)
- 보조 호스팅 GitHub Pages (Phase 4 검토)

## 캘린더 알림

| 일자 | 이벤트 |
|------|--------|
| 2026-06 | Phase 2 핵심 시스템 본격 |
| 2026-07 중반 | Phase 3 디자인·콘텐츠 |
| 2026-07 말 | Phase 4 첫 출시 |
| 2026-08 | 운영 본격·가을 신학기 시즌 |
| 2026-09~10 | 홈오피스 시즌 발행 |
| 2026-11~12 | 새해 미니멀·신학기 1차 사전 발행 |
| 2026-11-28 | API Token·Anthropic Key 회전 [추정] |
| 2026-12 | Phase 6 6개월 결산 / AdSense 결정 |
| 2027-01 | 신학기 1차 시즌 검색 피크 |
| 2027-05 | 종합소득세 신고 (사업자 등록 후) / 도메인 갱신 |
| 2027-06 | Phase 7 1년 결산 |
