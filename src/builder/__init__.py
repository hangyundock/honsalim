"""builder — 정적 사이트 생성 (manifest·renderer·pages·sitemap·assets·jsonld).

출처: ARCH §3 + BACKEND §2-5 [확정].

세션 #4: jsonld 빌더만 우선 구현. manifest·renderer 등은 후속.
"""

from __future__ import annotations

from . import manifest
from .jsonld import build_article_jsonld, build_itemlist_jsonld, build_product_jsonld

__all__ = (
    "build_article_jsonld",
    "build_itemlist_jsonld",
    "build_product_jsonld",
    "manifest",
)
