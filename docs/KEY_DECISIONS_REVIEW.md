# KEY_DECISIONS_REVIEW.md — 핵심 결정 잔여 3건 검토 자료

> 작성: 세션 #4 (2026-05-28)
> 목적: 사용자 검토 부담 감소 — SUMMARY·REVIEW_QUESTIONS 검토 진입 전 사전 자료.
> 본 문서는 진단·질문만. 결정은 사용자.
>
> 핵심 결정 4건 중 ARCH §4 모듈 분리 → [ARCH_MODULE_DIAGNOSIS.md](ARCH_MODULE_DIAGNOSIS.md) 별도 자료.
> 본 문서: 나머지 3건 — manifest 형태 · 시나리오 우선순위 · 단축 URL 차단 목록.

---

## 결정 1: manifest 형태 (DB §10)

### 현재 명세 [추정 — 세션 #2]

manifest는 **JSON 파일** `data/manifest.json` (테이블 아님).

```
data/manifest.json
{
  "schema_version": 1,
  "articles": [{slug, content_hash, depends_on, last_built}, ...],
  "assets": [{path, hash}, ...],
  "templates": [{name, hash}, ...]
}
```

### 왜 JSON 파일인가 (DB §10-1 명시)
1. Git diff 가능 → 빌드 변경 검토·rollback 직관적
2. 사람이 직접 읽기 쉬움
3. CI에서 파싱 단순 (jq·Python json 표준)
4. SQLite에 들어가면 `sqlite3 .dump` 등 추가 도구 필요

### 사용자 검토 질문
- **(1a) JSON 파일 채택 OK?** → 그대로 진행
- **(1b) 다른 형태 검토?**
  - 옵션: SQLite 별도 테이블 (DB와 통합)
  - 옵션: 여러 작은 JSON (articles.json·assets.json·templates.json 분리)
  - 옵션: YAML (사람이 더 읽기 편함, jq 호환 약함)

### 권장 [추정]
**(1a) JSON 파일 그대로**. 명세 근거 강함 + Phase 2 builder.manifest 모듈이 아직 미작성이라 변경 비용 작음. 다만 검토 후 다른 선택 시 builder 구현 전 결정 권장.

### 영향 범위
- builder.manifest 모듈 구현 (Phase 2 잔존)
- 증분 빌드 판정 (ARCH §7-3, 5가지 재빌드 조건)
- Git diff 워크플로

---

## 결정 2: 시나리오 우선순위 (SCENARIOS §4-11)

### 현재 명세 [관찰 — 세션 #2]

10편 시즌별 발행 일정 표:

| # | 슬러그 | 발행 권장 | 시즌 | 페르소나 |
|---|--------|----------|------|----------|
| #4 | `gaeul-cheot-jachi-30` | 2026-06~07 | 가을 신학기 | A 자취생 |
| #5 | `homeoffice-chair-desk-50` | 2026-09~10 | 홈오피스 | B 재택 |
| #6 | `homeoffice-100-setup` | 2026-09~10 | 홈오피스 | B |
| #7 | `homeoffice-200-premium` | 2026-10~11 | 홈오피스 | B |
| #8 | `saehae-minimal-20` | 2026-11~12 | 새해 미니멀 | C 정착자 |
| #9 | `jeongchak-gajeon-up-50` | 2026-11~12 | 새해 | C |
| #1 | `wonroom-cheot-jachi-30` | 2026-12~2027-01 | 신학기 1차 | A |
| #2 | `cheot-jachi-50-complete` | 2026-12~2027-01 | 신학기 1차 | A |
| #10 | `isacheol-jeongni-30` | 2026-12~2027-01 | 봄 이사철 | C |
| #3 | `cheot-jachi-gajeon-100` | 2027-01 | 신학기 1차 | A |

원칙: 시즌 검색 피크 **2개월 전 발행** ([관찰] Google 인덱싱·신뢰 점수 누적).

### 사용자 검토 질문

- **(2a) 첫 발행 시즌이 가을 신학기(#4)인 게 OK?**
  - 이유: Phase 4 출시 (2026-07 말~08) 직후 가을 신학기 검색 피크 (8~9월)에 맞춤. 첫 글이 시즌 직격.
  - 또는 첫 발행을 홈오피스(#5~#7)로 변경 — 페르소나 B 재택근무자 시작.

- **(2b) 페르소나별 글 수 분배 (A:4, B:3, C:3) OK?**
  - 옵션: A 비중 늘리기 (자취생이 검색량 가장 많음 [관찰])
  - 옵션: 평등 분배 (3:3:3 + 추가 1편)

- **(2c) 슬러그 명명 한국어 로마자 OK?** (`cheot-jachi`, `homeoffice`, `minimal-life`)
  - 영문 SEO 약함 vs 한국 검색 친화 — 현재는 한국 검색 친화 우선 [추정]

- **(2d) 10편이 부족한가? 더 필요?**
  - 현재 10편은 시드. 추가는 SCENARIOS §2-1 "확장 큐"로 후속.

### 권장 [추정]
**(2a)(2b) 현재 일정·분배 그대로 진행** — 시즌 2개월 전 원칙 일관. 페르소나 A 비중은 검색량 근거. **(2c) 한국어 로마자 슬러그 그대로** — 한국 사용자 기억 용이. 본인 검색 직관성.

### 영향 범위
- Phase 3 첫 5~10편 작성 순서
- collector·enricher 시나리오 큐 순서
- 페르소나 사진 촬영 우선순위 (Phase 3)
- Cloudflare Pages 첫 배포 시점

---

## 결정 3: 단축 URL 차단 목록 (POLICY §6-1 / D6 [확정])

### 현재 명세 [확정 — 세션 #1·#2]

본문 안에 다음 도메인 발견 시 **즉시 fail** (links 게이트):

| 도메인 | 종류 | 차단 사유 |
|--------|------|----------|
| `vivoldi.com` | 회색지대 단축 | D6 [확정] |
| `bit.ly` | 일반 단축 | 신뢰성·추적 불투명 |
| `goo.gl` | 일반 단축 | 서비스 종료지만 잔존 차단 |
| `tinyurl.com` | 일반 단축 | 동일 |
| `t.co` | 트위터 | 동일 |
| `bitly.com` | 일반 단축 | bit.ly 풀 도메인 |
| `rebrand.ly` | 일반 단축 | 동일 |
| `ow.ly` | 일반 단축 | 동일 |
| `is.gd` | 일반 단축 | 동일 |
| `cutt.ly` | 일반 단축 | 동일 |
| `me2.do` | 카카오 단축 | 카카오 단축 서비스 |
| `n.kakao.com` (특정 패턴) | 카카오 단축 | 추가 — 현재 코드 미반영 [관찰] |

추가 룰:
- 자체 게이트웨이 `honsalim.com/go/<slug>`만 허용
- 쿠팡 `link.coupang.com`·`partners.coupang.com` 직접 허용

### 현재 코드 (validator/links.py)

`SHORT_URL_DOMAINS` 11개 활성 (n.kakao.com 패턴 누락):

```python
("vivoldi.com", "bit.ly", "goo.gl", "tinyurl.com", "t.co",
 "bitly.com", "rebrand.ly", "ow.ly", "is.gd", "cutt.ly", "me2.do")
```

### 사용자 검토 질문

- **(3a) 차단 목록 11개 + n.kakao.com 추가 OK?**
  - POLICY §6-1에는 12개 있지만 코드는 11개 활성. 12번째 `n.kakao.com` 패턴 활성화 여부 결정 필요.

- **(3b) 차단 목록 제외할 도메인 있는가?**
  - 예를 들어 `t.co` (트위터)는 트위터에서 자동 적용. 본문에 사용자 직접 쓸 가능성 낮음. 그러나 안전 우선이면 유지.

- **(3c) 새로 추가할 도메인?**
  - 옵션: `naver.me` (네이버 단축) — 국내 자주 보이는 단축. 현재 누락.
  - 옵션: `tiny.cc` · `shorturl.at` · `s.id` 등 신규 서비스
  - 옵션: 동적 갱신 (분기 1회 갱신 — POLICY §12 [관찰])

- **(3d) 자체 게이트웨이 `honsalim.com/go/<slug>` 외 자체 단축 추가 검토?**
  - 현재는 1개만. 마케팅 추적 시 더 필요할 수 있음 — 단 그게 외부 단축이면 자체 모순.

### 권장 [추정]
**(3a) n.kakao.com 추가 + 그대로 11→12개 활성** + **(3c) `naver.me` 추가 권장** (국내 사용량 높음). 갱신 주기는 [관찰] 운영 후 검토.

### 영향 범위
- `src/validator/links.py` `SHORT_URL_DOMAINS` 튜플
- 회귀 테스트 (현재 vivoldi·bit.ly 케이스 2개) — 신규 도메인 케이스 추가
- POLICY §6-1과 코드 정합

---

## 4. 결정 후 다음 단계

각 결정마다 사용자 답변 후 1 commit씩 적용 가능:
- (1) manifest 형태 — JSON 파일 그대로면 변경 없음, 다른 형태면 builder.manifest 구현 시 반영
- (2) 시나리오 우선순위 — 그대로면 변경 없음, 변경 시 SCENARIOS §4-11 갱신 + scenarios seed SQL 갱신
- (3) 단축 URL 목록 — 코드 1줄 추가 (예: `n.kakao.com`·`naver.me`) + 회귀 ~3개 추가

---

## 5. 관련 문서

- [SUMMARY.md](SUMMARY.md) — 12 문서 1페이지 요약 (사용자 검토 게이트)
- [REVIEW_QUESTIONS.md](REVIEW_QUESTIONS.md) — 사용자 검토 질문 25개
- [ARCH_MODULE_DIAGNOSIS.md](ARCH_MODULE_DIAGNOSIS.md) — 핵심 결정 #1 (모듈 분리)
- [DECISIONS.md](DECISIONS.md) — A~J 카테고리 영구 결정
- [DB.md §10](DB.md) — manifest 스키마 상세
- [SCENARIOS.md §4](SCENARIOS.md) — 시나리오 10편 명세
- [POLICY.md §6](POLICY.md) — links 게이트

---

| 버전 | 일자 | 작성자 |
|------|------|--------|
| 1.0 | 2026-05-28 | Claude Opus 4.7 (세션 #4) |
