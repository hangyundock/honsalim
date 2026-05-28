# PIP_AUDIT_ANALYSIS.md — 세션 #6 pip-audit 16건 분석

> 출처: pip-audit 2.10.0 직접 실행 결과 (2026-05-28 세션 #6 [확정]).
> 환경: Python 3.10.11 32-bit + honsalim 의존성 (pyproject.toml + transitive).
> 본 문서: 사용자 `pip install -U` 환경 갱신 의사결정 보조.

---

## 1. 요약

- **총 16건 / 9 패키지** [확정]
- **직접 의존 7건 / 3 패키지** — `pyproject.toml lower-bound` 갱신 완료 [확정 commit 5f6dfde]
- **Transitive 9건 / 6 패키지** — 도구/SDK 의존, 본 프로젝트 코드 직접 사용 X
- **본 프로젝트 코드 직접 영향**: pillow (이미지 처리) · requests (HTTP) · python-dotenv (secrets 로드)

---

## 2. 직접 의존 3 패키지 7건 [본 세션 lower-bound 처리]

| 패키지 | 현재 | 권장 | CVE | 본 프로젝트 사용처 |
|--------|------|------|-----|--------------------|
| pillow | 12.1.1 | 12.2.0 | CVE-2026-40192·42309·42310·42311 · PYSEC-2026-165 | 이미지 처리 (Phase 3·4 사용자 직접 사진 리사이즈) |
| python-dotenv | 1.2.1 | 1.2.2 | CVE-2026-28684 | secrets/*.env 로드 (Phase 1·2 활성) |
| requests | 2.32.5 | 2.33.0 | CVE-2026-25645 | Cloudflare Pages·D1·IndexNow HTTP 호출 (Phase 2~) |

**상태**: `pyproject.toml` lower-bound 갱신 완료 (`>=12.2`·`>=1.2.2`·`>=2.33`). CI 환경에서는 다음 `pip install -e .[dev]` 시 자동 적용 [확정]. 운영자 머신은 사용자 명시 승인 후 `pip install -U` 별도.

---

## 3. Transitive 6 패키지 9건

| 패키지 | 현재 | 권장 | CVE | 의존 경로 [추정] |
|--------|------|------|-----|------------------|
| urllib3 | 2.6.3 | 2.7.0 | PYSEC-2026-141·142 | requests → urllib3 |
| idna | 3.11 | 3.15 | CVE-2026-45409 | requests → idna |
| cryptography | 46.0.5 | 46.0.7 | PYSEC-2026-35·36 | detect-secrets / requests 도구 transitive |
| pyasn1 | 0.6.2 | 0.6.3 | CVE-2026-30922 | cryptography → pyasn1 |
| lxml | 6.0.2 | 6.1.0 | PYSEC-2026-87 | pip-audit · responses 등 도구 transitive |
| pip | 26.0.1 | 26.1 | CVE-2026-3219·6357 | Python 환경 (도구) |

**본 프로젝트 코드 직접 영향**: 없음 (transitive). 단, `requests` 호출 시 urllib3·idna·cryptography는 내부적으로 사용됨 — `requests` 갱신 시 자동 함께 갱신될 수 있음.

---

## 4. 사용자 권장 처리 명령

> CLAUDE.md §2(라) — pip install 등 환경 변경은 사용자 명시 승인 후. 본 권장은 의사결정 보조.

### A안 — 일괄 갱신 (권장)

```powershell
# 직접 의존 + transitive 핵심 한 번에
python -m pip install -U pillow requests python-dotenv urllib3 idna cryptography pyasn1 lxml

# pip 자체 별도
python -m pip install --upgrade pip
```

**예상 결과**: 본 세션 pip-audit 16건 → 거의 0건 (남은 transitive는 새 출시 후 자동 갱신).

### B안 — 직접 의존만 (보수적)

```powershell
python -m pip install -U pillow requests python-dotenv
```

transitive는 다음 `pip install -e .[dev]` 또는 다음 도구 출시 시 자동 갱신.

### C안 — 현 상태 유지 (보류)

`pyproject.toml` lower-bound는 이미 갱신됨. CI 환경(GitHub Actions)에서는 매 build 시 최신 설치되므로 운영 안전. 로컬 환경 보안은 사용자 판단.

---

## 5. 검증 (갱신 후)

```powershell
python -m pip_audit
# 기대: "No known vulnerabilities found"
# 또는 남은 transitive 1~2건만

python -m pytest -q
# 기대: 342 passed (회귀 무영향 확인)

python -m src.cli doctor
# 기대: 모든 필수 체크 통과
```

---

## 6. 다음 자동 점검

- `lint.yml` — 매 PR/push 시 `pip-audit` step (continue-on-error, 알림만)
- `security.yml` — 매월 1일 09:00 UTC 전수 점검 + JSON artifact 90일 + GitHub Step Summary [확정 commit 987afed]
- Dependabot — 직접 의존 PR 자동 생성 (이미 활성, 세션 #3 Dependabot PR 3건 처리됨 [확정])

---

| 버전 | 일자 | 작성자 |
|------|------|--------|
| 1.0 | 2026-05-28 (세션 #6) | Claude Opus 4.7 |
