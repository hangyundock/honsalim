# ARCH_MODULE_DIAGNOSIS.md — `src/` 모듈 배치 모순 진단

> 작성: 세션 #4 (2026-05-28)
> 목적: 사용자 검토 부담 감소 — 핵심 결정 4건 중 ARCH §4-2 모듈 분리 결정 자료.
> 본 문서는 진단만. 결정은 사용자.

---

## 1. 모순 정확한 진단 [확정]

### 1-1. ARCH §3 디렉토리 설계 (line 155~194)

`src/` 안에 모듈 폴더를 **flat**으로 배치:

```
src/
├── cli.py
├── common/{config,logging,db,grading}.py
├── collector/{coupang,aliexpress,scenario_loader}.py
├── enricher/{claude_client,meta_extractor,retry,...}.py
├── validator/{truth,schema,disclosure,links}.py
├── writer/{article_writer,state_machine}.py
├── builder/{jsonld,manifest,renderer,...}.py
├── dashboard/, deployer/, tracker/, workers/
```

즉 `src/honsalim/` 같은 단일 패키지 폴더는 **없음**. 모듈이 `src/` 바로 아래.

### 1-2. pyproject.toml 가정 (line 43~48)

```toml
[project.scripts]
honsalim = "honsalim.cli:main"      ← honsalim.cli 모듈 경로

[tool.setuptools.packages.find]
where = ["src"]                      ← src/ 안에서 패키지 탐색
```

setuptools가 entry point `honsalim`을 만들 때 `honsalim.cli`를 import 시도 → 그러려면 `src/honsalim/cli.py` (또는 `src/honsalim/__init__.py` + `src/honsalim/cli.py`)가 있어야 함. **현재는 없음**.

### 1-3. 영향 [확정]

- `pip install -e .[dev]` 실행 시 setuptools가 src/ 안 여러 패키지(common·collector·validator 등)를 발견하지만, `honsalim` 패키지는 못 찾음.
- entry point `honsalim` 명령이 `ModuleNotFoundError: No module named 'honsalim'`로 실패.
- 현재는 회피: `python src/cli.py doctor` 직접 실행 (CLI docstring 명시).
- 회귀 테스트는 `conftest.py`가 `src/`를 `sys.path`에 추가해서 정상 import.

**즉 "모순"의 실질**: pyproject.toml의 entry point만 작동 안 함. 코드 자체는 정상.

---

## 2. 해결 옵션 3가지 비교

### 옵션 A: `src/honsalim/` 하위로 모듈 이동 (Python 표준 src-layout)

**구조**
```
src/honsalim/
├── __init__.py
├── cli.py
├── common/, collector/, enricher/, validator/, writer/, builder/, ...
```

**변경 범위**: **큼**
- 모든 모듈 파일 이동 (`src/cli.py` → `src/honsalim/cli.py` 등)
- 모든 test import 갱신 (`from validator import ...` → `from honsalim.validator import ...`)
- `tests/conftest.py` 경로 수정
- ARCH.md §3 디렉토리 트리 갱신

**장점**
- Python 표준 src-layout (PyPA 공식 권장 [관찰])
- `pip install -e .` 후 `honsalim` 명령 작동
- 외부 패키지 노출이 깔끔 (`import honsalim.validator`)

**단점**
- 현재 247 회귀 모두 import 경로 갱신 필요
- 큰 diff (15+ 모듈 + 11 test 파일)
- ARCH §3 문서도 같이 갱신

**작업 추정**: 1~2 commit, 회귀 모두 재검증 필요.

---

### 옵션 B: pyproject.toml을 flat layout에 맞춤

**변경**
```toml
[project.scripts]
honsalim = "cli:main"             ← honsalim. 제거

[tool.setuptools.packages.find]
where = ["src"]
include = ["common*", "collector*", "enricher*", "validator*",
           "writer*", "builder*", "dashboard*", "deployer*",
           "tracker*", "workers*"]
py-modules = ["cli"]              ← 또는 top-level py-module로 cli 등록
```

**변경 범위**: **작음**
- pyproject.toml만 수정
- src/·tests/·ARCH.md 모두 그대로

**장점**
- 코드 변경 없음
- 회귀 영향 0
- 빠르게 적용 가능

**단점**
- 비표준 (PyPA 권장 src-layout과 다름)
- `pip install` 후 `from cli import ...`가 가능해짐 — 흔한 이름이라 외부 충돌 위험 [관찰]
- `honsalim` 단일 진입점 의미 약화 — 여러 top-level 패키지가 노출됨

**작업 추정**: 1 commit, 회귀 그대로.

---

### 옵션 C: `src/honsalim/__init__.py`만 추가해 re-export

**구조**
```
src/
├── cli.py
├── honsalim/
│   ├── __init__.py          ← from collector import *; from validator import *; ...
│   └── cli.py               ← from cli import main (또는 직접 정의)
├── common/, collector/, ... (그대로)
```

**변경 범위**: **중간**
- `src/honsalim/__init__.py` 신설
- `src/honsalim/cli.py` 또는 re-export 추가
- `src/cli.py` 그대로 유지 (또는 `src/honsalim/cli.py`가 import)

**장점**
- 기존 모듈·테스트 경로 보존
- `honsalim` entry point 작동
- 점진적 마이그레이션 가능

**단점**
- 두 import 경로 공존 (`from validator` vs `from honsalim.validator`) — 일관성 약함
- 메인테넌스 부담 (re-export 누락 가능)
- ARCH §3과 실제 구조 더 복잡해짐

**작업 추정**: 1 commit, 회귀 그대로 + 새 import 경로 회귀 추가.

---

## 3. 옵션 비교 표

| 기준 | A (src-layout) | B (flat 유지) | C (re-export) |
|------|---------------|---------------|---------------|
| Python 표준 정합 | ✅ 정합 | ⚠️ 비표준 | ⚠️ 혼합 |
| 변경 범위 | 큼 (15+ 모듈) | **작음 (1 파일)** | 중간 (2~3 파일) |
| 회귀 영향 | 모두 재검증 | 없음 | 새 경로 회귀 추가 |
| 외부 노출 깔끔 | ✅ `honsalim.*` | ❌ 여러 top-level | ⚠️ 혼합 |
| ARCH §3 갱신 필요 | ✅ | ❌ | ❌ |
| `pip install -e .` 작동 | ✅ | ✅ | ✅ |
| 향후 확장성 | ✅ 표준 | ⚠️ 충돌 위험 | ⚠️ 일관성 약함 |
| 작업 commit 수 | 1~2건 + 회귀 재검증 | 1건 | 1건 + 회귀 보강 |

---

## 4. 권장 — [추정]

**Phase 2 안정성·향후 확장성**: 옵션 A (src-layout) 권장.

**근거**
1. Python 패키징 표준 (PyPA src-layout 공식 권장) — 향후 신규 개발자·도구 호환성
2. 외부 노출 깔끔 — `import honsalim.validator` 한 줄로 명확
3. ARCH §3과 정합 (단, ARCH §3 디렉토리 트리 자체를 src-layout으로 갱신 필요)
4. pyproject.toml과의 모순 근본 해결 (현재 entry point 작동 안 함)

**다만 [추정] 표시**: 본 추천은 일반 모범 사례 기반. 사용자 의도에 따라 다른 선택 가능 — 예를 들어 "변경 부담 최소화"가 우선이면 옵션 B도 합리적.

---

## 5. 사용자 결정 후 다음 작업

### 옵션 A 선택 시
1. `src/` 안 모듈을 `src/honsalim/`으로 이동 (1 commit)
2. 모든 test import 경로 갱신 (`from validator` → `from honsalim.validator`) (1 commit)
3. ARCH.md §3 디렉토리 트리 갱신 (1 commit)
4. 회귀 247/247 PASS 재확인
5. `pip install -e .[dev]` 사용자 명시 승인 후 적용
6. doctor 명령으로 entry point `honsalim` 작동 확인

### 옵션 B 선택 시
1. pyproject.toml `[project.scripts]` + `packages.find.include` 수정 (1 commit)
2. ARCH §3과 정합 OK (변경 불필요)
3. `pip install -e .[dev]` 사용자 명시 승인 후 적용

### 옵션 C 선택 시
1. `src/honsalim/__init__.py` re-export 작성 (1 commit)
2. 회귀 테스트에 `honsalim.*` 경로 추가 검증 (1 commit)
3. 점진 마이그레이션 — 코드 신규 작성은 `honsalim.*` 경로 사용 권장

---

## 6. 관련 문서

- [ARCH.md §3 디렉토리](ARCH.md) — 현재 flat 설계
- [ARCH.md §4 모듈 의존 그래프](ARCH.md)
- [pyproject.toml](../pyproject.toml)
- [BACKEND.md §9 CLI 명령](BACKEND.md) — `honsalim` 명령 명세
- [DECISIONS.md J3](DECISIONS.md) — CLI 8/11 활성

---

| 버전 | 일자 | 작성자 | 비고 |
|------|------|--------|------|
| 1.0 | 2026-05-28 | Claude Opus 4.7 (세션 #4) | 사용자 검토 자료 |
