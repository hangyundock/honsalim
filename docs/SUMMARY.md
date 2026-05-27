# SUMMARY.md — 혼살림 설계 12개 문서 1페이지 요약

> 비개발자 사용자가 12개 설계 문서(~5,800줄)를 빠르게 검토할 수 있도록 핵심만 압축.
> 작성: 2026-05-27 (Claude Opus 4.7) / 세션 #2 산출.
> 본 문서는 검토 보조용. 의문점은 원본 문서로.

---

## 1. 한 문장 요약

> 한국어 단일·1인 가구 분야 어필리에이트 추천 사이트 **혼살림(honsalim.com)**을, 사용자 1클릭 승인 + 자동 검증 게이트 구조로, Python·Jinja2·Cloudflare Pages 무료 인프라 위에 매주 2~3편 발행하는 운영 시스템.

---

## 2. 12개 문서 1줄씩

| # | 문서 | 1줄 요약 |
|---|------|---------|
| 1 | PLAN | 비전·KPI·로드맵·예산 (월 ~16,000원·12개월 100편 목표) |
| 2 | ARCH | 시스템 다이어그램·모듈 8개·외부 의존 5개·secrets 격리·빌드/배포 흐름 |
| 3 | DB | SQLite 9테이블 + D1 3테이블 + manifest JSON + 상태 머신 6개 |
| 4 | SCENARIOS | 페르소나 3 + 시나리오 10편 + 확장 룰 + DB 시드 |
| 5 | DESIGN | 미니멀+따뜻함 토큰·Pretendard·컴포넌트 18종·페이지 5종 와이어 |
| 6 | FRONTEND | Jinja2 템플릿 5종·meta/OG/Schema·sitemap·이미지·CWV |
| 7 | BACKEND | 모듈 8개 인터페이스·Claude API 캐시·Workers go_gateway·CLI 11종 |
| 8 | POLICY | 공정위 disclosure·진실성 30+패턴·외부 단축 URL 차단·PIPA·접근성 |
| 9 | OPS | 일/주/월/분기 체크리스트·로그·알림·장애 5종·자격증명 갱신 |
| 10 | BACKUP | 7대상·3계층(외부 드라이브+클라우드+GitHub)·복구 리허설·재난 |
| 11 | MAINTENANCE | 의존성·CVE·페르소나/시나리오 확장·영어 확장·디자인 갱신 |
| 12 | SCHEDULE | Phase 0~7·월별 체크포인트·시즌 캘린더·KPI 시점 |

---

## 3. 핵심 결정 25개 매트릭스

### A. 정체 (6)

| # | 결정 | 출처 |
|---|------|------|
| 1 | 사이트명 **혼살림 (honsalim.com)** | PLAN §1, DECISIONS A1·A2 |
| 2 | 분야 **1인 가구·자취·홈오피스·일상살림** (비YMYL) | A3 |
| 3 | 언어 **한국어 단일** (영어는 6개월 후) | A4 |
| 4 | 컨셉 **시나리오 추천 + 페르소나×예산** | A5 |
| 5 | 디자인 **미니멀+따뜻함** (흰+우드+부드러운 그림자) | A6 |
| 6 | 페르소나 **3개**: 자취생·재택·정착자 | SCENARIOS §3 |

### B. 기술·인프라 (6)

| # | 결정 | 출처 |
|---|------|------|
| 7 | Jinja2 직접 빌더 (AutoBlog 확장) | DECISIONS B1 |
| 8 | Cloudflare Pages 호스팅 (서울 PoP) | B3·B10 |
| 9 | DB는 SQLite + D1 분리 (콘텐츠/클릭) | DB §2 |
| 10 | Pretendard 한글 폰트 | B9 |
| 11 | Python 3.10 시스템 공유 (가상환경 X) | CLAUDE §12 |
| 12 | GitHub 공개 저장소·Actions 무제한 | H1 |

### C. 운영 (5) — 세션 #2 갱신

| # | 결정 | 출처 |
|---|------|------|
| 13 | **인간 1클릭 승인** 의무 (자동 "승인" 절대 X) | C1, POLICY §13 |
| 14 | **발행 편수 최대화** — 큐 기반·사용자 역량 내 최대 (시즌 2개월 사전) | C8, SCENARIOS §6-1 |
| 15 | **자동 "게시" 활성**: 윈도우 스케줄러 매일 11:00 KST 큐 1편 발행 (자동 "승인"은 금지) | C6·C7, POLICY §13-0 |
| 16 | 진실성 게이트 4단계: truth·schema·disclosure·links | ARCH §9 |
| 17 | 직접 사진 1~3장 의무 (1인칭 한국어 조건) | D5, POLICY §3-1-3 |

### D. 수익·정책 (5)

| # | 결정 | 출처 |
|---|------|------|
| 18 | 메인 쿠팡 + 보조 알리(Phase 5+) | D1·D2 |
| 19 | AdSense **6개월 후 재결정** | D3 |
| 20 | 사업자 등록은 **월 10만원 누적 후** | D4 |
| 21 | 외부 단축 URL 금지 + `/go/<slug>` 자체 게이트웨이 | D6·D7 |
| 22 | 본인·가족 구매 금지·자동 광고 금지·AI 100% 자동 금지 | E4·E5·E7 |

### E. 디자인·확장 (3)

| # | 결정 | 출처 |
|---|------|------|
| 23 | Claude Design 시안 + Claude Code 구현 하이브리드 | G1 |
| 24 | 벤치마크: 오늘의집·NYT Wirecutter·위키바이 | A6·DESIGN §2-3 |
| 25 | 페이지 5종: 홈·시나리오 허브·글·페르소나·About | DESIGN §6 |

### F. 보안 (7) — 세션 #2 신규 추가

| # | 결정 | 출처 |
|---|------|------|
| 26 | **GitHub 보안 다중 방어**: .gitignore + pre-commit hook (gitleaks/detect-secrets) + Secret Scanning + 브랜치 보호 + CodeQL | I1·I6, POLICY §14-bis-1 |
| 27 | 보안 헤더 의무 (CSP·HSTS·XCTO·XFO·Referrer·Permissions) | I2, POLICY §14-bis-2 |
| 28 | 외부 계정 2FA 의무 (GitHub·CF·쿠팡·Anthropic·도메인) | I3, POLICY §14-bis-3 |
| 29 | 의존성 보안 자동화 (Dependabot + pip-audit 월·npm audit 분기) | I4, POLICY §14-bis-4 |
| 30 | 로컬 디스크 BitLocker 암호화 | I5, POLICY §14-bis-5 |
| 31 | secrets 정기 회전 (GitHub PAT 90일·CF/Anthropic 180일) | I7, OPS §6 |
| 32 | 침해 사고 대응 7단계 (key 회전·repo 비공개·배포 정지 등) | POLICY §14-bis-7 |

---

## 4. 시나리오 10편 한눈에

| # | 슬러그 | 페르소나 | 예산 | 시즌 | 발행 시점 |
|---|--------|---------|------|------|----------|
| 1 | wonroom-cheot-jachi-30 | 자취생 | 30만 | 2~3월 | 2026-12 |
| 2 | cheot-jachi-50-complete | 자취생 | 50만 | 2~3월 | 2026-12 |
| 3 | cheot-jachi-gajeon-100 | 자취생 | 100만 | 2~3월 | 2027-01 |
| 4 | gaeul-cheot-jachi-30 | 자취생 | 30만 | 8~9월 | 2026-06~07 |
| 5 | homeoffice-chair-desk-50 | 재택 | 50만 | 11~1월 | 2026-09 |
| 6 | homeoffice-100-setup | 재택 | 100만 | 11~1월 | 2026-09 |
| 7 | homeoffice-200-premium | 재택 | 200만 | 11~1월 | 2026-10 |
| 8 | saehae-minimal-20 | 정착자 | 20만 | 1월 | 2026-11 |
| 9 | jeongchak-gajeon-up-50 | 정착자 | 50만 | 1월 | 2026-11 |
| 10 | isacheol-jeongni-30 | 정착자 | 30만 | 봄/가을 이사 | 2026-12 |

---

## 5. Phase 일정 한눈에

```
2026-05~06   Phase 0  설계      ← 12/12 완료 (본 세션)
2026-06      Phase 1  인프라     ← 도메인·GitHub·Cloudflare·쿠팡 키
2026-06~07   Phase 2  핵심 시스템 ← Python·DB·검증·빌드·배포
2026-07      Phase 3  디자인·콘텐츠 ← 시안·첫 10편
2026-07 말   Phase 4  첫 출시    ← 사이트 오픈
2026-08~11   Phase 5  운영·확장
2026-12      Phase 6  6개월 결산
2027-06      Phase 7  1년 결산
```

---

## 6. 비용 예산 (PLAN §8)

| 항목 | 월 |
|------|----|
| 도메인 honsalim.com | ~1,300원 |
| Cloudflare 4종 (Pages·R2·D1·Workers) | 0원 (무료 한도) |
| GitHub Actions | 0원 (공개 저장소) |
| Claude API (Haiku) | 5,000~15,000원 |
| **합계** | **~6,300~16,300원/월** |

---

## 7. 사용자 검토 체크리스트

**1단계 — 큰 방향 (10분)**
- [ ] 사이트명·도메인·분야·언어 (§3-A) 동의?
- [ ] 페르소나 3개 (§4) 누락된 페르소나 있는가?
- [ ] 시나리오 10편 (§4) 폐기·우선순위 변경할 편 있는가?
- [ ] 디자인 컨셉 "미니멀+따뜻함" (§3-A5) 동의?

**2단계 — 운영 모델 (10분)**
- [ ] 매주 2~3편 페이스 부담스럽지 않은가?
- [ ] 직접 사진 1~3장 의무 실행 가능한가?
- [ ] 1클릭 승인 패턴 (단순 HTML 대시보드) OK?
- [ ] 사업자 등록 **월 10만원 후** 동의 (vs 즉시)?

**3단계 — 일정·예산 (10분)**
- [ ] Phase 1 진입 시점 2026-06 초 가능한가?
- [ ] 도메인 honsalim.com 결제 의사 OK?
- [ ] 월 ~16,000원 (Claude 구독 별도) OK?

**4단계 — 외부 의존 사전 확인**
- [ ] Cloudflare 계정 보유 또는 신규 가입 의사?
- [ ] 쿠팡 파트너스 가입 의사?
- [ ] Anthropic API 키 활성 (이미 보유)?
- [ ] 외부 백업 드라이브 보유?

**5단계 — 의문점 메모**
- 12 문서 중 미진한 부분이나 추가 결정 필요한 사항 메모.
- 다음 세션에 가져와서 변경·보강 진행.

---

## 8. Phase 1 진입 직전 사용자 액션 (참고)

| # | 액션 | 누가 |
|---|------|-----|
| 1 | GitHub 공개 저장소 생성 | 사용자 |
| 2 | 도메인 honsalim.com 가용성 재확인 + 결제 (Cloudflare Registrar) | 사용자 |
| 3 | Cloudflare 계정 + Pages·R2·D1·Workers 준비 | 사용자 |
| 4 | `D:\secrets\affiliate_hub\` 폴더 생성 | 사용자 |
| 5 | 쿠팡 파트너스 가입 + Open API 키 신청 | 사용자 (1~3일 대기) |
| 6 | `.gitignore`·`pyproject.toml`·deny 룰 작성 | Claude (사용자 OK 후) |
| 7 | Anthropic API 키 검증 | Claude |
| 8 | `python -m honsalim doctor` 통과 | Claude |

---

## 9. 잠재적 위험 5개 (PLAN §10)

| # | 위험 | 완화 |
|---|------|------|
| 1 | Google Helpful Content 패널티 (AI 자동 게시) | 1클릭 승인·직접 사진·진실성 게이트 |
| 2 | 신규 도메인 sandbox 6~12개월 무트래픽 | KPI 현실 가정·콘텐츠 축적 우선 |
| 3 | 쿠팡 이미지 저작권 회색지대 | 공식 위젯·직접 촬영만 |
| 4 | 사업자등록 지연 법적 위험 | 월 10만원 즉시 등록 |
| 5 | Cloudflare/쿠팡/알리 계정 lockout | 재인증 절차 문서화·자격증명 정기 회전 |

---

## 10. 다음 단계

1. **사용자**: 본 SUMMARY로 큰 그림 검토 (30~40분 예상) + `docs/REVIEW_QUESTIONS.md`에 답.
2. **다음 세션**: 의문점 → 변경 결정 시 DECISIONS 갱신 + 영향받는 12 문서 v1.2 갱신.
3. **Phase 1 진입 OK 시**: SCHEDULE §3-2의 11개 액션 순차 실행 (사전 작성된 5건 파일 즉시 사용 가능).

문서가 두꺼워서 12편 모두 정독은 비현실적입니다. 본 요약을 게이트로 사용하시고, 의심 가는 부분만 원본 문서로 들어가서 확인하시면 됩니다.

---

## 11. 세션 #2 사전 작성 산출물 (검토 대상)

본 세션에 추가로 작성된 산출물 — Phase 1·2에서 즉시 사용 가능. 사용자 검토 권장.

| 파일 | 용도 | Phase |
|------|------|------|
| `docs/SUMMARY.md` | 본 문서 — 12 문서 + 결정 32개 + 검토 체크리스트 | 검토 시 |
| `docs/REVIEW_QUESTIONS.md` | 다음 세션 검토 질문지 25개 | 검토 시 |
| `docs/SCHEDULER_GUIDE.md` | 윈도우 작업 스케줄러 등록 (GUI·PowerShell) | Phase 1·2 |
| `docs/VALIDATOR_PATTERNS.md` | validator 정규식·패턴 12 카테고리 | Phase 2 |
| `sql/migrations/001_initial_schema.sql` | DB 9테이블 + 트리거 + 인덱스 | Phase 2 |
| `sql/seeds/001_personas_scenarios.sql` | personas 3 + scenarios 10 시드 | Phase 2 |
| `.gitignore` | secrets·data·build·logs 차단 | Phase 1 |
| `.pre-commit-config.yaml` | gitleaks/detect-secrets 옵션 + lint·format hooks | Phase 1 |
| `.claude/settings.json` | deny 24·allow 14 (AutoBlog 패턴 확장) | Phase 1 |
| `build_headers_draft.txt` | 보안 헤더 6종 (CSP·HSTS 등) | Phase 2~4 |
| `src/enricher/prompt_templates/*.md` (5개) | system_base·article_main·meta_extract·faq_generate·product_recommendation_note | Phase 2 |

빈 폴더 + `.gitkeep`: `src/`·`tests/`·`templates/`·`static/`·`data/` (Phase 2 진입 시 즉시 사용).

---

| 버전 | 일자 | 변경 | 작성자 |
|------|------|------|--------|
| 1.0 | 2026-05-27 | 최초 작성 (12 문서 요약 + 결정 25개 + 검토 체크리스트) | Claude Opus 4.7 |
