"""디자인 토큰 가독성 가드 — 본문 색 대비 회귀 방지 (세션 #18).

흰 배경(--bg) 대비 핵심 텍스트 토큰의 WCAG 명도 대비를 검증한다.
세션 #18에서 본문 토큰(--sub #3f464e ≈ 8:1)이 흐려 가독성이 떨어진 문제를
진한 색으로 개선했고, 다시 흐려지는 회귀를 자동 감지하기 위한 가드다.
(§0 자가복원: 무인 운영에서 색 가독성은 시각 확인이 어려우므로 수치로 고정한다.)
"""

from __future__ import annotations

import re
from pathlib import Path

TOKENS_CSS = Path(__file__).resolve().parent.parent / "static" / "css" / "tokens.css"
CATEGORY_CSS = Path(__file__).resolve().parent.parent / "static" / "css" / "category.css"

# (토큰, 흰 배경 대비 최소 명도비) — 세션 #18 흐림 개선 회귀 방지.
_MIN_CONTRAST: dict[str, float] = {
    "text": 10.0,  # 제목·강조·본문 강조 — 최고 또렷
    "sub": 9.0,  # ★본문 단락 — 가독성 핵심(흐림 재발 방지)
    "meta": 4.5,  # 메타·캡션 — WCAG AA 본문 최소
}


def _hex_token(css: str, name: str) -> str:
    """tokens.css에서 `--name: #rrggbb` 값을 추출."""
    m = re.search(rf"--{re.escape(name)}:\s*(#[0-9a-fA-F]{{6}})", css)
    assert m, f"--{name} 토큰을 tokens.css에서 찾지 못함"
    return m.group(1)


def _luminance(hex_color: str) -> float:
    """WCAG 2.x 상대 휘도."""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast(fg: str, bg: str) -> float:
    """WCAG 명도 대비 (밝은 쪽+0.05)/(어두운 쪽+0.05)."""
    lo, hi = sorted((_luminance(fg), _luminance(bg)))
    return (hi + 0.05) / (lo + 0.05)


def test_text_tokens_meet_contrast() -> None:
    """본문·제목·메타 토큰이 흰 배경 대비 가독성 기준을 충족 (흐림 회귀 방지)."""
    css = TOKENS_CSS.read_text(encoding="utf-8")
    bg = _hex_token(css, "bg")
    for name, minimum in _MIN_CONTRAST.items():
        fg = _hex_token(css, name)
        ratio = _contrast(fg, bg)
        assert ratio >= minimum, (
            f"--{name}({fg}) 흰 배경 대비 {ratio:.1f}:1 < 최소 {minimum}:1 — "
            f"본문 가독성 회귀(세션 #18). 더 진한 색 필요."
        )


def test_hierarchy_preserved() -> None:
    """위계 유지: text(가장 진함) ≥ sub ≥ meta(가장 옅음)."""
    css = TOKENS_CSS.read_text(encoding="utf-8")
    bg = _hex_token(css, "bg")
    c_text = _contrast(_hex_token(css, "text"), bg)
    c_sub = _contrast(_hex_token(css, "sub"), bg)
    c_meta = _contrast(_hex_token(css, "meta"), bg)
    assert (
        c_text >= c_sub >= c_meta
    ), f"색 위계 깨짐 — text {c_text:.1f} ≥ sub {c_sub:.1f} ≥ meta {c_meta:.1f} 여야 함"


def test_wrap_scoped_blocks_keep_horizontal_padding() -> None:
    """`.wrap`과 함께 쓰는 본문 컨테이너(.catpage/.catindex)가 `padding` shorthand로
    좌우 여백을 0으로 덮지 않는지 검증 — 덮으면 본문이 헤더보다 왼쪽으로 튀어나옴
    (세션 #18 정렬 버그). 좌우는 .wrap(24px)에 위임하고 상하만 지정해야 한다.
    """
    css = CATEGORY_CSS.read_text(encoding="utf-8")
    for cls in (".catpage", ".catindex"):
        # 단독 규칙 `.catpage { ... }`만 매칭(자손 셀렉터 `.catpage .x {`는 제외).
        blocks = re.findall(rf"{re.escape(cls)}\s*\{{([^}}]*)\}}", css)
        assert blocks, f"{cls} 단독 규칙을 category.css에서 찾지 못함"
        for body in blocks:
            assert not re.search(r"\bpadding\s*:", body), (
                f"{cls}가 padding shorthand 사용 — .wrap 좌우(24px)를 덮어 헤더와 어긋남. "
                f"padding-top/padding-bottom으로 분리하라(세션 #18)."
            )
