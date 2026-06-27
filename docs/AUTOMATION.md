# AUTOMATION.md — 혼살림 무인 자동화 작업 프로세스 표준 [확정 #38]

> **이 문서의 목적**: 무인/자동화 작업을 안내하기 전에 Claude가 매 세션 반드시 먼저 읽는 표준.
> 세션마다 같은 설명을 주인이 반복하지 않도록(인수인계 단절 방지) 전체 파이프라인을 코드 근거와 함께 박는다.
> 출처: #38 코드 정밀분석(키워드 선정 자동화 실체 확인) + 주인 강한 지시.

---

## 0. 핵심 원칙 — 한 줄 요약

**키워드도 글도 사람이 직접 만들지 않는다.** 운영자가 씨앗(키워드 자료)을 두고 무인을 켜면,
시스템이 **키워드 선정 → 상품 수집 → 글 생성 → 검증 → 승인 → 발행**을 매일 자동으로 순회한다.
운영자는 ①씨앗 유지관리 ②(선택)쿠팡 미리 첨부 ③무인 ON/OFF 통제 ④발행 후 사후 검토만 한다.

**★Claude 금지(반복 실수):**
- "키워드를 직접 입력하라"고 안내 금지 — 키워드는 **추천 엔진이 네이버 데이터로 선정**한다.
- "글을 먼저 수동 생성하라"고 안내 금지 — 글 생성은 **스케줄러가 자동**으로 한다.

---

## 1. 전체 파이프라인 한눈에

```
[씨앗 자료]                    [추천 엔진]                  [자동 선정]
seo_keywords.yml  ──────▶  keyword_recommender  ──────▶  auto_pick_keyword
(카테고리 대표키워드)        (네이버 검색량→winnable점수)     (대기큐·쿠팡우선·추천보충)
                                                                   │
                                                                   ▼
                                              cmd_keyword_generate (글 1편)
                                                                   │
   ┌───────────────────────────────────────────────────────────────┤
   ▼                                                               ▼
[상품 수집]                                                    [본문 생성]
_gather_keyword_candidates                                   enrich (DeepSeek)
= 저장 쿠팡(항상 포함) + 알리 카테고리 영어검색                = SEO 키워드 주입·자가복원 재생성
   │                                                               │
   └───────────────────────────────┬───────────────────────────────┘
                                    ▼
                          [5게이트 검증] validate
                 truth·schema·disclosure·links·seo (전부 통과해야 validated)
                                    │
                                    ▼
                          [자동 승인] auto_approve (fail-closed)
            validated + 카테고리매핑 + featured>0(on-target) + 발행≥min_published
                                    │
                                    ▼
                          [발행·배포] publish-queue → refresh_cycle
                          promote → build → git commit+push → CI → 라이브
                                    │
                                    ▼
                          [사후 모니터] article_guardrail.monitor
                          미달 글 자동 비공개 + 대시보드 '발행 글 관리' 사람 검토
```

위 전체를 **매일 예약 시각마다 `auto-cycle`이 1회 순회**(publish_per_day 편수). auto_mode ON일 때만.

---

## 2. 단계별 상세 (코드 근거)

### 2-1. 씨앗 자료 — `src/collector/seo_keywords.yml`
- 카테고리별 `primary`(대표키워드)·`core`(핵심어 필터)·`secondary`(네이버 연관검색어)·`exclude_terms`(off-target 제외).
- 현재 5개 카테고리: office-chair(사무용 의자)·desk(컴퓨터 책상)·monitor-stand(모니터 받침대)·laptop-stand(노트북 거치대)·monitor-arm(모니터암).
- 운영자 편집 대상(§2-마 인간 게이트). 새 카테고리는 여기 씨앗 추가 또는 `provision-category` 자동 생성(#35).
- 로더: `collector/seo_keywords.py:load_all()`.

### 2-2. 추천 엔진 — `writer/keyword_recommender.py`
- `default_seeds()`: yml → 씨앗 목록.
- `recommend(conn, custom_seed, limit, live)`: 씨앗마다 네이버 검색광고 실시간 조회(`keyword_research.research_keywords`, 월검색량 하한 2000) → 후보.
- `winnable_score(volume, competition)`: `min(검색량, cap) × 경쟁가중`(낮음1.0·중간0.6·높음0.3). **검색량 높되 경쟁 낮은 '틈' 키워드 우선** = 신생 사이트가 이길 수 있는 롱테일.
- 정렬(winnable 내림차순) + 기존 큐/시나리오 중복 제외 → 추천 목록 반환.

### 2-3. 무인 자동 선정 — `keyword_recommender.auto_pick_keyword()`
1. `status='pending'` 키워드 있으면 맨 위 1건 재사용. **정렬: 쿠팡 첨부(target_products) 있는 키워드 최우선** → score(검색량) → priority → id.
2. pending 없으면 추천에서 top 1건을 큐에 추가해 반환(자동 보충). **큐가 비어도 멈추지 않음**(완전 무인 핵심·#34).
3. 반환 `{keyword_id, keyword, source: "queue"|"recommend"}`.

### 2-4. 상품 수집 — `cli._gather_keyword_candidates()`
- ① 저장된 쿠팡(target_products) — **항상** 후보에 포함(필터 없음·사람이 골랐으므로).
- ② 알리 — 키워드→카테고리 매핑(`resolve_category`) → 카테고리 영어 티어 검색 → 키워드-적합성 필터.
- **후보 0개면 글 생성 중단·키워드 failed**(빈 글 방지 가드·#38). 쿠팡을 첨부했거나 매핑 카테고리가 있으면 0개가 안 됨.

### 2-5. 본문 생성 + 5게이트 — `cmd_enrich` → `validate`
- 본문 LLM = DeepSeek v4-pro(OpenRouter). 키워드→카테고리 SEO 키워드 주입 + 5게이트 미달 시 자가복원 재생성(상한 `enrich_max_attempts`).
- 5게이트: truth·schema·disclosure·links·seo. 전부 통과 → `validated`, 아니면 `rejected`.

### 2-6. 자동 승인 — `writer/auto_approve.py` (fail-closed)
모두 충족해야 승인: ①validated ②키워드 카테고리 매핑됨 ③featured 상품>0 & 전부 on-target ④발행 누적 ≥ `auto_approve_min_published`.
- ④ 미달이면 **전체 보류(held)** → 사람이 직접 승인. 초기 N편 품질 확인용 안전장치(#33).

### 2-7. 발행·배포 — `cmd_publish_queue` → `refresh_cycle`
- approved 글 promote → build/site·functions/go 렌더 → git commit+push → CI가 honsallim.com 반영.

### 2-8. 사후 모니터 — `article_guardrail.monitor`
- 발행 글 중 미달 자동 비공개 + 대시보드 '발행 글 관리' 탭에서 사람이 라이브 검토·비공개/재공개(#37). 2겹 그물.

---

## 3. 운영자 역할 (이것만 하면 된다)

| # | 역할 | 빈도 | 방법 |
|---|------|------|------|
| ① | 씨앗 유지관리 | 가끔 | seo_keywords.yml 대표 키워드 추가/수정 (또는 `provision-category`) |
| ② | 쿠팡 배너 미리 첨부 | 선택 | 🛒쿠팡 첨부(저장) — 원하는 키워드에 |
| ③ | 무인 ON/OFF 통제 | 1회 | 상단 무인 토글 + 예약 |
| ④ | 발행 후 사후 검토 | 선택 | '발행 글 관리' 탭 — 품질 나쁜 글 비공개 |

→ **키워드를 머리로 짜내거나 글을 직접 쓰는 일은 없다.**

---

## 4. 두 가지 모드

### A. 완전 무인 (auto_mode ON) — 기본 지향
1. (선택) 씨앗 점검 / 쿠팡 미리 첨부
2. 상단 무인 ON + 예약 켜기
3. → 매일 auto-cycle이 키워드 선정→수집→생성→승인→발행 전부 자동.
- `auto_approve_min_published=0`이면 첫 글부터 완전 무관여. >0이면 그 편수까지 사람이 승인 클릭(초기 검수).

### B. 반자동 (운영자가 키워드 고를 때)
1. 🎯추천 키워드 → 네이버 추천 N건에서 택1 → 큐 추가
2. (선택) 🛒쿠팡 첨부(저장)
3. 무인 OFF면 사람이 미리보기→승인→발행, ON이면 스케줄러가 처리.

---

## 5. 대시보드 버튼 ↔ 기능

| 탭 | 버튼 | 기능 |
|----|------|------|
| 키워드 | 🎯 추천 키워드 | 네이버 추천 N건 → 택1 → 큐 추가(pending) |
| 키워드 | 🆕 키워드 추가 | (보조) 임의 키워드 직접 추가 |
| 키워드 | 🛒 쿠팡 첨부(저장) | 키워드에 쿠팡 배너 저장(생성 안 함·pending 유지) |
| 키워드 | 🛒 쿠팡 배너→글 생성 | (반자동) 쿠팡 붙여 그 키워드로 즉시 글 생성 |
| 키워드 | ✨ 글 생성 | (반자동·수동) 자동선정 키워드로 즉시 1편 생성. **무인에선 안 씀** |
| 발행 큐 | 👁 미리보기 / ✅ 승인 / 🚫 반려 / 🚀 발행 | 사람 검수·발행(무인 OFF 또는 초기 N편) |
| 발행 글 관리 | 🌐 라이브 / 🚫 비공개 / ♻ 재공개 | 발행 후 사후 검토 |
| 상단 배너 | ⚪/🟢 무인 토글 | auto_mode ON/OFF(즉시 반영·예약 재등록 백그라운드) |
| 설정 | 자동승인 전 사람 검수 편수 | `auto_approve_min_published` |

---

## 6. 주요 CLI (헤드리스/스케줄러)

- `keyword-recommend [--add-top]` — 네이버 추천 생성(1순위 자동 추가)
- `auto-cycle` — ★완전 무인 1회 순회(선정→생성→승인→발행). auto_mode ON일 때만
- `publish-queue` — 승인 글만 발행(반자동)
- `schedule` — 예약 등록(auto_mode면 auto-cycle wrapper, 아니면 publish-queue wrapper)

---

## 7. 설정값 (`data/config.json`)

| 키 | 의미 | 기본 |
|----|------|------|
| `auto_mode` | 완전 무인 ON/OFF | false |
| `auto_approve_min_published` | 자동승인 전 사람검수 편수 | 5 |
| `publish_per_day` | 하루 발행 편수(=auto-cycle 1회 생성 상한) | 1 |
| `schedule_time` | 예약 시각 | "11:00" |
| `enrich_max_attempts` | 글 자가복원 재생성 상한 | 2 |
| `coupang_mode` | manual / api | manual |

---

## 8. 안전장치 (무인이어도 지켜지는 것)

- auto_mode 기본 OFF — 주인이 명시적으로 켜야 동작(E7).
- 5게이트 + auto_approve fail-closed — 미달 글 자동 발행 안 됨.
- min_published — 초기 N편 사람검수 강제(0으로 끄면 해제).
- 빈 글 차단(#38) — 상품 0개면 LLM 비용 전 중단.
- 사후 모니터 + 발행 글 관리 — 발행 후 2겹 검토.
- 빌드·배포는 commit+push 경유(deployer.git_push stub 우회·#32).

---

## 9. Claude 체크리스트 (무인 작업 안내 전 자문)

- [ ] 키워드를 '직접 입력하라'고 안내하려는가? → **멈춰라. 추천 엔진/auto_pick이 기본이다.**
- [ ] '글을 먼저 수동 생성하라'고 안내하려는가? → **멈춰라. 스케줄러가 자동 생성한다.**
- [ ] 운영 방식을 다시 묻거나 새 프로세스를 제안하려는가? → **멈춰라. 이 문서가 default다.**
- [ ] 위험(완전무인 vs Helpful Content·min_published)은 막지 말고 정보로만 제시했는가?

관련: CLAUDE.md §7 · DECISIONS C21·C22·C23 · 메모리 [[autopublish-operational-model]]·[[autonomous-safe-system]]·[[assist-not-overstep]].
