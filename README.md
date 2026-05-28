# 혼살림 (Honsalim)

> 한국 1인 가구·자취·홈오피스·일상살림 어필리에이트 추천 사이트 빌더.
> 사이트: [honsalim.com](https://honsalim.com) (Phase 4 오픈 예정 — 2026-08)

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| 분야 | 1인 가구·자취·홈오피스·일상살림 (비YMYL) |
| 언어 | 한국어 단일 |
| 컨셉 | 시나리오 추천 + 페르소나×예산 결합 |
| 디자인 | 미니멀+따뜻함 (흰 + 우드 액센트) |
| 수익 | 쿠팡 파트너스 + AliExpress (보조) |

## 기술 스택

- **Python 3.10** — 빌더·콘텐츠 파이프라인
- **Jinja2** — 정적 사이트 빌더 (자체 manifest 기반 증분 빌드)
- **SQLite** — 로컬 콘텐츠·메타·상태
- **Cloudflare Pages** — 호스팅 (서울 PoP)
- **Cloudflare Workers + D1** — `/go/<slug>` 자체 redirect 게이트웨이 + 클릭 로그
- **Claude API (Haiku)** — 본문·요약·메타 생성 (인간 검토 후 발행)
- **GitHub Actions** — 빌드·배포 자동화

## 운영 원칙

1. **인간 편집 게이트** — Claude 자동 검증 4단계 + 사용자 1클릭 승인 후 발행
2. **자동 "승인" 절대 금지** — Google Helpful Content System 회피
3. **자동 "게시" 활성** — 윈도우 작업 스케줄러 매일 11:00 KST 큐 1편 발행
4. **진실성 게이트** — 가격·재고·1인칭·외부 단축 URL·Schema·공정위 disclosure 자동 검증
5. **직접 사진 의무** — 1인칭 한국어는 직접 보유·촬영 사진 첨부 상품에 한정

## 보안 정책

- secrets는 본 저장소 외부 (`D:\secrets\affiliate_hub\`) — 저장소에 절대 포함 X
- `.gitignore` 엄격 + pre-commit hook 9종 (detect-secrets·trim·black·ruff·mypy 등) — 우발 누설·품질 차단
- GitHub Secret Scanning + Dependabot + CodeQL 활성 + Branch Protection (main-protect)
- 외부 계정 5종 2FA 의무 (GitHub·Cloudflare·Anthropic·쿠팡·도메인)
- 보안 헤더 6종 (CSP·HSTS·X-Content-Type-Options·X-Frame-Options·Referrer-Policy·Permissions-Policy)
- 로컬 D 드라이브 BitLocker 암호화

자세한 보안 정책: `docs/POLICY.md` §14-bis

## 진행 단계 (Phase)

```
Phase 0  설계        2026-05    ✅ 완료 (12개 설계 문서 + SUMMARY)
Phase 1  인프라      2026-05~06 ✅ ~95% (GitHub·Cloudflare·도메인·R2·D1·secrets·pre-commit)
Phase 2  핵심 시스템  2026-06~07 🔄 진행 중 (모듈 13개·회귀 247/247·CLI 8/11)
Phase 3  디자인·콘텐츠 2026-07
Phase 4  첫 출시      2026-07 말~08
Phase 5  운영·확장    2026-08~11
Phase 6  6개월 결산   2026-12
Phase 7  1년 결산     2027-06
```

### Phase 2 진척 (세션 #4 기준)

- **핵심 모듈 13개**: cli · common · validator · writer · collector · enricher · builder
- **회귀 테스트 247/247 PASS** [확정]
- **CLI 명령 8/11**: doctor · db migrate/seed · collect · enrich(dry_run) · validate · approve · unapprove
- **state_machine**: 6 상태 머신 (collected→enriched→validated→approved→published + rejected/unapprove)
- **validator 4 게이트**: truth(가격·1인칭·AI 흔적·단정형) · schema(Article·ItemList·Product·Review) · disclosure(공정위) · links(단축 URL 차단·rel)
- **Schema.org JSON-LD 빌더**: Article·ItemList·Product
- **Claude API 재시도 정책** (BACKEND §3-5): RateLimit·Overloaded·Timeout·BadRequest·APIError

## 설계 문서

`docs/` 안에 15편 (1편 요약 + 12편 본문 + 검토 자료 2편):

| 문서 | 내용 |
|------|------|
| [SUMMARY.md](docs/SUMMARY.md) | 12편 1페이지 요약 + 결정 32개 매트릭스 |
| [PLAN.md](docs/PLAN.md) | 비전·KPI·로드맵·예산 |
| [ARCH.md](docs/ARCH.md) | 시스템 아키텍처·모듈·외부 의존 |
| [DB.md](docs/DB.md) | SQLite + D1 스키마 |
| [SCENARIOS.md](docs/SCENARIOS.md) | 페르소나 3 + 시나리오 10편 |
| [DESIGN.md](docs/DESIGN.md) | 디자인 시스템·컴포넌트 |
| [FRONTEND.md](docs/FRONTEND.md) | Jinja2·SEO·Schema·CWV |
| [BACKEND.md](docs/BACKEND.md) | Python 모듈·API·테스트 |
| [POLICY.md](docs/POLICY.md) | 공정위·진실성·보안 |
| [OPS.md](docs/OPS.md) | 운영·로깅·장애·자격증명 |
| [BACKUP.md](docs/BACKUP.md) | 백업·복구·재난 |
| [MAINTENANCE.md](docs/MAINTENANCE.md) | 유지보수·확장 |
| [SCHEDULE.md](docs/SCHEDULE.md) | Phase·시즌 캘린더·KPI |
| [ARCH_MODULE_DIAGNOSIS.md](docs/ARCH_MODULE_DIAGNOSIS.md) | `src/` flat vs `honsalim` 패키지 모순 진단 + 옵션 A/B/C |
| [KEY_DECISIONS_REVIEW.md](docs/KEY_DECISIONS_REVIEW.md) | manifest 형태·시나리오 우선순위·단축 URL 차단 목록 검토 자료 |

## 개발·기여

본 프로젝트는 1인 운영자 개인 사이트이며, **외부 기여를 받지 않습니다**. 보안·정책 위험 관리 및 콘텐츠 진실성 보장 목적입니다.

오류 신고·문의는 [이슈 트래커](../../issues) 또는 사이트 푸터 이메일로 부탁드립니다.

## 라이선스

- **코드**: 추후 결정 (Phase 1 사용자 결정)
- **콘텐츠**: All Rights Reserved (직접 작성·촬영물)

## 참조

- 운영 가이드: [docs/SCHEDULER_GUIDE.md](docs/SCHEDULER_GUIDE.md)
- 검증 규칙: [docs/POLICY.md](docs/POLICY.md)
- 검증 패턴: [docs/VALIDATOR_PATTERNS.md](docs/VALIDATOR_PATTERNS.md)
- 결정 이력: [docs/DECISIONS.md](docs/DECISIONS.md) (카테고리 A~J)
- 변경 이력: [docs/CHANGELOG.md](docs/CHANGELOG.md) (v1.0~v1.4)
