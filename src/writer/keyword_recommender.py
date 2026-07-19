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


# ── winnable('틈') 점수 — 검색량 * 경쟁 낮을수록 우선 (세션 #33) ──────────────
# 검색량만 보면 과경쟁 head를 잡아 좋은 글도 노출 0이 되므로, 수요는 있되 경쟁이 낮은
# '들어갈 틈'을 우선한다(naver_blog winnable 정신을 혼살림 가용 데이터로 적용).
_COMP_FACTOR: dict[str, float] = {
    "낮음": 1.0,
    "low": 1.0,
    "중간": 0.6,
    "mid": 0.6,
    "medium": 0.6,
    "높음": 0.3,
    "high": 0.3,
}
# 검색량 상한(이 이상은 동일 취급) — head 키워드 검색량 과가중 억제. [추정·운영 트래픽으로 보정].
WINNABLE_VOL_CAP = 30000
# 무인 리필의 추천 스캔 폭(#45) — 표시용 limit(20)와 분리. 상위가 미매핑 후보로 채워져도
# 매핑·공개 후보를 놓치지 않도록 충분히 넓게(전 씨앗 후보 합계보다 큼).
_REFILL_SCAN_LIMIT = 200


def _comp_factor(competition: Any) -> float:
    """네이버 compIdx(경쟁정도) → 가중치. 미상/미매칭은 중간(0.5)."""
    key = str(competition or "").strip()
    return _COMP_FACTOR.get(key) or _COMP_FACTOR.get(key.lower(), 0.5)


def winnable_score(volume: int | None, competition: Any) -> float:
    """'틈' 점수 = 검색량(상한 cap) * 경쟁 가중. 검색량 미상(캐시)은 최하(-1.0). 세션 #33."""
    if volume is None:
        return -1.0
    return min(int(volume), WINNABLE_VOL_CAP) * _comp_factor(competition)


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
                "require_terms": tuple(entry.get("require_terms") or ()),
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
                "require_terms": (),
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
                    require_terms=tuple(spec.get("require_terms") or ()),
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

    # winnable 정렬(세션 #33): '틈' 점수(검색량 * 경쟁 낮을수록 ↑) 내림차순 → 캐시(미상)는 뒤로.
    # 검색량만 보면 과경쟁 head를 잡아 노출 0이 되므로 경쟁 낮은 틈을 우선. stable=동점 원순서 보존.
    out.sort(key=lambda d: -winnable_score(d.get("volume"), d.get("competition")))
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

    1) status='pending' 키워드가 있으면 **맨 위 1건 재사용**(이미 큐에 있는 것 낭비 없음).
       정렬은 대시보드 목록(dashboard.queries.list_keywords)과 **동일**:
       **미리선택(쿠팡 등 target_products) 있는 키워드 우선** → score DESC → priority DESC → id.
       (쿠팡 세팅한 키워드가 검색량 높은 알리 추천보다 먼저 잡혀 '글 생성'에 쿠팡 포함 — 세션 #28 Part2)
    2) 없으면 **정의된 방식**(seo_keywords.yml 씨앗 + keyword_research)으로 top 추천 → 큐에 추가
       (score=월검색량) → 그 키워드.
    반환: {keyword_id, keyword, source: "queue"|"recommend"} 또는 None(추천도 없음).
    """
    from collector import keyword_relevance  # 지연 임포트(순환 회피)

    # pending 중 '발행가능(카테고리 매핑)'을 우선 집는다 — 미매핑은 후순위 강등(세션 #39).
    #   ★skip·삭제가 아니다: 미매핑 키워드는 큐에 그대로 남아 auto-cycle digest/ALERT로 운영자에게
    #   보고된다(추천 롱테일·완전무인 자동보충을 죽이지 않기 위함). 전부 미매핑이면 기존처럼 맨 위
    #   1건을 반환해 behavior를 보존한다(멈추지 않음 — 그 사유는 digest가 보고). 정렬은 대시보드
    #   목록과 동일(쿠팡 첨부 우선 → score → priority → id)을 유지하고 그 위에 매핑 우선만 얹는다.
    rows = conn.execute(
        "SELECT id, keyword FROM keyword_queue WHERE status = 'pending' "
        "ORDER BY (target_products IS NOT NULL AND target_products NOT IN ('', '[]')) DESC, "
        "score DESC, priority DESC, id"
    ).fetchall()
    if rows:
        for kid, kw in rows:
            # conn 전달(#45): draft 카테고리 매핑도 후순위 강등 — 생성 비용을 쓴 뒤 보류되는
            # 어긋남 방지(auto_approve category_draft와 정합)
            ok, _code = keyword_relevance.publishability(str(kw), conn)
            if ok:
                return {"keyword_id": int(kid), "keyword": str(kw), "source": "queue"}
        # 전부 미매핑 — 멈추지 않고 맨 위 1건(behavior 보존). digest가 '큐 발행가능 0'을 ALERT.
        return {"keyword_id": int(rows[0][0]), "keyword": str(rows[0][1]), "source": "queue"}

    # 큐가 빔 — 추천에서 자동 보충. ★세션 #45: '발행 가능' 추천만 큐에 넣는다.
    #   ①미매핑 → ali 수집 skip·상품 0·failed = 그날 무인 발행 0(여름이불류 침묵 데드엔드)
    #   ②draft(비공개) 카테고리 → 공개 허브 없는 고아 글
    # 첫 '매핑 + 카테고리 공개' 후보를 선택하고, 전부 부적격이면 None — auto-cycle이 '생성 0'
    # 으로 digest abnormal→[ALERT]·텔레그램(fail-loud). 사람 경로(대시보드 추천 다이얼로그·
    # 수동 추가)는 제한하지 않는다(운영자 판단 존중 — 부적격 사유는 발행 단계가 보류로 가시화).
    # ★스캔 폭(#45 적대검증): 표시용 기본 limit(20)로 자른 '뒤' 가드를 걸면 상위가 미매핑
    # 헤드로 채워질 때 21위+의 매핑 후보를 놓쳐 그날 생성 0이 된다 — 미매핑 후보는 큐에 안
    # 들어가 dedup에도 안 걸려 매일 상위에 잔류하는 반면 매핑 후보는 하루 1개씩 소비되므로
    # 시간이 갈수록 악화. 넉넉한 폭으로 스캔한다(비용 동일 — 네이버 호출 수는 씨앗 수로 결정,
    # limit은 출력 절단일 뿐).
    recs = recommend(
        conn,
        seeds=seeds,
        custom_seed=custom_seed,
        channel=channel,
        fetch=fetch,
        live=live,
        limit=_REFILL_SCAN_LIMIT,
    )
    top = None
    for rec in recs:
        slug = keyword_relevance.resolve_category(str(rec.get("keyword") or ""))
        if slug is None or keyword_relevance.category_blocked(conn, slug):
            continue
        top = rec
        break
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
