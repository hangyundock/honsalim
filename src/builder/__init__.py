"""builder — 정적 사이트 생성 (manifest·renderer·pages·sitemap·assets·jsonld).

출처: ARCH §3 + BACKEND §2-5 [확정].

세션 #4: jsonld 빌더만 우선 구현. manifest·renderer 등은 후속.
"""

from __future__ import annotations

from .jsonld import build_article_jsonld

__all__ = ("build_article_jsonld",)
