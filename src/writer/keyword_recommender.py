"""writer.keyword_recommender — 추천 키워드 생성 (세션 #26).

'어떤 키워드를 쓸지'의 **선정 방식은 이미 정의돼 있다**(collector.keyword_research:
네이버 연관검색어 → 핵심어 포함·브랜드·거래성·검색량(≥2000)·대상부적합 필터 → 검색량순).
본 모듈은 그 방식을 **기존 카테고리 SEO 씨앗**(collector.seo_keywords.yml의 primary)에 적용해
'다음에 쓸 만한' 롱테일 키워드를 검색량순으로 추천한다(운영 대시보드 🎯 추천 키워드).
PyQt 비의존 = 테스트 가능 / CI(Linux) 안전.

설계:
- 씨앗(seed): 기본 = seo_keywords.yml 카테고리 primary 전부(운영자 편집 대상·on-brand·알리 공급 검증).
              custom_seed로 임의 주제(자취·주방·수납 등) 확장 가능(core 미적용).
- 데이터: 네이버 검색광고 실 월검색량(live). 키 없음·네트워크 실패 시 yml 캐시 secondary로
          자동 강등(§0 자가복원 — 멈추지 않음, volume=None 표기).
- 중복 제거: 이미 keyword_queue·scenarios에 있는 주제는 추천에서 제외.
- 비용: 네이버 읽기 전용 조회(무료). 본문 LLM 비용은 글 생성 단계에서만 발생.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

from collector import keyword_research, seo_keywords


def _norm(text: str | None) -> str:
    """주제 비교용 정규화: NFKC + 공백 제거 + 소문자."""
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", text or "")).lower()


def default_seeds(path: Path | None = None) -> list[dict[str, Any]]:
    """seo_keywords.yml 카테고리 → 씨앗 목록 [{seed, core, exclude_terms, category, cached_secondary}]."""
    entries = seo_keywords.load_all() if path is None else seo_keywords.load_all(path)
    seeds: list[dict[str, Any]] = []
    for key, entry in sorted(entries.items()):
        primary = str(entry.get("primary") or "").strip()
        if not primary:
            continue
        seeds.append(
            {
                "seed": primary,
                "core": entry.get("core"),
                "exclude_terms": tuple(entry.get("exclude_terms") or ()),
                "category": key,
                "cached_secondary": list(entry.get("secondary") or []),
            }
        )
    return seeds


def _existing_topics(conn: sqlite3.Connection) -> set[str]:
    """이미 큐/시나리오에 있는 주제(정규화) — 추천 중복 제외용."""
    topics: set[str] = set()
    try:
        for (kw,) in conn.execute("SELECT keyword FROM keyword_queue"):
            topics.add(_norm(kw))
    except sqlite3.OperationalError:  # 큐 테이블 없음(구 스키마) — 중복 제외 생략
        pass
    try:
        for title, slug in conn.execute("SELECT title_ko, slug FROM scenarios"):
            topics.add(_norm(title))
            topics.add(_norm(slug))
    except sqlite3.OperationalError:
        pass
    topics.discard("")
    return topics


def recommend(
    conn: sqlite3.Connection,
    *,
    seeds: list[dict[str, Any]] | None = None,
    custom_seed: str | None = None,
    limit: int = 20,
    channel: str = "ali",
    fetch: Callable[..., list[dict[str, Any]]] | None = None,
    live: bool = True,
    volume_floor: int | None = None,
) -> list[dict[str, Any]]:
    """추천 키워드(검색량순). 항목: {keyword, volume, competition, seed, core, category, channel, source}.

    - custom_seed 지정 시 그 씨앗만 확장(임의 주제·core 미적용). 아니면 seeds, 그것도 없으면 기본 씨앗.
    - live=True: 네이버 실조회(씨앗별 실패 시 캐시 강등). live=False: 캐시(secondary)만 — 네트워크 0.
    """
    if custom_seed and custom_seed.strip():
        seed_list: list[dict[str, Any]] = [
            {
                "seed": custom_seed.strip(),
                "core": None,
                "exclude_terms": (),
                "category": None,
                "cached_secondary": [],
            }
        ]
    elif seeds is not None:
        seed_list = seeds
    else:
        seed_list = default_seeds()

    floor = keyword_research.VOLUME_FLOOR if volume_floor is None else volume_floor
    existing = _existing_topics(conn)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for spec in seed_list:
        seed = str(spec.get("seed") or "").strip()
        if not seed:
            continue
        rows: list[dict[str, Any]] = []
        source = "cached"
        if live:
            try:
                res = keyword_research.research_keywords(
                    seed,
                    core=spec.get("core"),
                    exclude_terms=tuple(spec.get("exclude_terms") or ()),
                    volume_floor=floor,
                    fetch=fetch,
                    dry_run=False,
                )
                rows = list(res.get("candidates") or [])
                source = "naver"
            except Exception:  # 네이버 실패는 캐시로 자가복원(무인 안전·멈추지 않음)
                rows = []
        if not rows:  # 강등: 캐시된 secondary (검색량 미상)
            rows = [
                {"keyword": k, "volume": None, "competition": "unknown"}
                for k in spec.get("cached_secondary", [])
            ]
            source = "cached"
        for row in rows:
            keyword = str(row.get("keyword") or "").strip()
            norm = _norm(keyword)
            if not keyword or norm in seen or norm in existing:
                continue
            seen.add(norm)
            out.append(
                {
                    "keyword": keyword,
                    "volume": row.get("volume"),
                    "competition": row.get("competition", "unknown"),
                    "seed": seed,
                    "core": spec.get("core"),
                    "category": spec.get("category"),
                    "channel": channel,
                    "source": source,
                }
            )

    # 검색량 있는 것 우선(내림차순) → 캐시(volume None)는 뒤로(stable=원순서 보존)
    out.sort(key=lambda d: (d["volume"] is None, -(d["volume"] or 0)))
    return out[:limit]


def top_recommendation(conn: sqlite3.Connection, **kwargs: Any) -> dict[str, Any] | None:
    """추천 1순위(선택 없을 때 자동 세팅용). 없으면 None."""
    recs = recommend(conn, **kwargs)
    return recs[0] if recs else None


def auto_pick_keyword(
    conn: sqlite3.Connection,
    *,
    channel: str = "ali",
    seeds: list[dict[str, Any]] | None = None,
    custom_seed: str | None = None,
    fetch: Callable[..., list[dict[str, Any]]] | None = None,
    live: bool = True,
) -> dict[str, Any] | None:
    """글 생성용 키워드 **자동 선정** (운영자 무개입 — '글 생성' 한 번에 키워드까지).

    1) status='pending' 키워드가 있으면 우선순위(priority·score·id)순 1건 **재사용**(이미 큐에 있는 것 낭비 없음).
    2) 없으면 **정의된 방식**(seo_keywords.yml 씨앗 + keyword_research)으로 top 추천 → 큐에 추가
       (score=월검색량) → 그 키워드.
    반환: {keyword_id, keyword, source: "queue"|"recommend"} 또는 None(추천도 없음).
    """
    row = conn.execute(
        "SELECT id, keyword FROM keyword_queue WHERE status = 'pending' "
        "ORDER BY priority DESC, score DESC, id LIMIT 1"
    ).fetchone()
    if row:
        return {"keyword_id": int(row[0]), "keyword": str(row[1]), "source": "queue"}

    top = top_recommendation(
        conn, seeds=seeds, custom_seed=custom_seed, channel=channel, fetch=fetch, live=live
    )
    if top is None:
        return None

    from writer import keyword_queue as kq  # 지연 임포트(순환 회피)

    kid = kq.add_keyword(
        conn,
        top["keyword"],
        channel=str(top.get("channel") or channel),
        score=float(top.get("volume") or 0),
    )
    return {"keyword_id": kid, "keyword": top["keyword"], "source": "recommend"}
