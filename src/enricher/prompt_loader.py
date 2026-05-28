"""prompt_templates/*.md 로더 + 단순 변수 치환.

출처: BACKEND §3-3 + ARCH §3 [확정].

설계:
- prompt_templates/*.md는 Git 추적·diff 가능 (BACKEND §3-3)
- 코드에서 load(name) 호출만
- Jinja2 미설치 환경 대비 — 단순 {{var}} 치환만 fallback 지원
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

TEMPLATE_DIR = Path(__file__).resolve().parent / "prompt_templates"

# BACKEND §3-3 명시 6종
KNOWN_TEMPLATES: tuple[str, ...] = (
    "system_base",
    "article_main",
    "meta_extract",
    "faq_generate",
    "product_recommendation_note",
    "tone_examples",
)

# {{var}} 또는 {{ var }} 또는 {{ var.attr }} — 단순 변수만 처리 (Jinja2 fallback)
_SIMPLE_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


@lru_cache(maxsize=16)
def load(name: str) -> str:
    """prompt_templates/{name}.md 내용 반환. 캐시.

    name: 확장자 제외 (예: 'system_base').
    """
    path = TEMPLATE_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt template not found: {name}.md")
    return path.read_text(encoding="utf-8")


def list_templates() -> list[str]:
    """prompt_templates/ 안의 .md 파일명 목록 (확장자 제외)."""
    if not TEMPLATE_DIR.exists():
        return []
    return sorted(p.stem for p in TEMPLATE_DIR.glob("*.md"))


def verify_known_templates_present() -> dict[str, bool]:
    """BACKEND §3-3 명시 6종이 모두 존재하는지."""
    return {name: (TEMPLATE_DIR / f"{name}.md").exists() for name in KNOWN_TEMPLATES}


def _resolve_path(scope: dict[str, Any], path: str) -> Any:
    """'scenario.title_ko' 같은 점 표기 해석. 키 누락 시 빈 문자열."""
    value: Any = scope
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            return ""
    return value


def render_simple(template: str, **vars: Any) -> str:
    """Jinja2 미설치 환경용 fallback — {{var}}·{{obj.attr}}만 치환.

    {% for %}·{% if %} 등은 처리하지 않음.
    Phase 2 후반 Jinja2 도입 시 본 함수를 jinja2.Environment.from_string으로 교체.
    """

    def replace(match: re.Match[str]) -> str:
        value = _resolve_path(vars, match.group(1))
        return str(value) if value is not None else ""

    return _SIMPLE_VAR_RE.sub(replace, template)


def render(template_name: str, **vars: Any) -> str:
    """템플릿 로드 + 변수 치환 (단순 또는 Jinja2)."""
    raw = load(template_name)
    try:
        import jinja2

        env = jinja2.Environment(
            autoescape=False,  # noqa: S701 - 본 결과는 HTML 아니라 LLM 프롬프트
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return str(env.from_string(raw).render(**vars))
    except ImportError:
        return render_simple(raw, **vars)
