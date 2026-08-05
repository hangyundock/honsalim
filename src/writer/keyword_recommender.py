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
# 검색량 상한(이 이상은 동일 취급) — head 검색량 과가중 억제. 공략 구간(ceiling) 도입 후에는
# 구간 내에서만 작동하므로 사실상 무영향. 세션 #51 재검수에서 '상한을 낮춰 경쟁도를 결정자로'
# 안은 기각됐다(네이버 경쟁도 '낮음'이 305개 중 1개 — 변별력 없음). 상세는 settings.py 주석.
WINNABLE_VOL_CAP = 30000


def _setting_int(key: str, fallback: int) -> int:
    """설정 정수 조회 — 미초기화(단위 테스트·부트스트랩)면 폴백(멈추지 않음·§0)."""
    try:
        from common import settings

        return int(settings.get_int(key))
    except Exception:
        return fallback


def _volume_floor() -> int:
    """공략 구간 하한 — 설정(keyword_volume_floor).

    ★세션 #51: 옛 하한 2000이 네이버 후보의 94.8%(1,878/1,980)를 잘라 시스템이 최고경쟁
    구간만 골랐다. 0~300은 계속 배제(실측상 0~100만 1,095개 = 트래픽 기대 0).
    """
    return max(0, _setting_int("keyword_volume_floor", keyword_research.VOLUME_FLOOR))


def _volume_ceiling() -> int:
    """공략 구간 상한 — 설정(keyword_volume_ceiling). 0이면 상한 없음(옛 동작).

    검색량이 클수록 기존 강자(다나와·쿠팡·네이버블로그)가 점유해 신규 도메인이 못 이긴다.
    실제로 우리가 진 22편이 전부 고검색량 구간이었다(GSC 평균 18.2위). 경쟁도 데이터는
    변별력이 없어(위 주석) 검색량 자체를 난이도 지표로 쓴다.
    """
    return max(0, _setting_int("keyword_volume_ceiling", 0))


# 무인 리필의 추천 스캔 폭(#45) — 표시용 limit(20)와 분리. 상위가 미매핑 후보로 채워져도
# 매핑·공개 후보를 놓치지 않도록 충분히 넓게(전 씨앗 후보 합계보다 큼).
_REFILL_SCAN_LIMIT = 200


def _comp_factor(competition: Any) -> float:
    """네이버 compIdx(경쟁정도) → 가중치. 미상/미매칭은 중간(0.5)."""
    key = str(competition or "").strip()
    return _COMP_FACTOR.get(key) or _COMP_FACTOR.get(key.lower(), 0.5)


def winnable_score(volume: int | None, competition: Any, *, cap: int | None = None) -> float:
    """'틈' 점수 = 검색량(상한 cap) * 경쟁 가중. 검색량 미상(캐시)은 최하(-1.0). 세션 #33."""
    if volume is None:
        return -1.0
    return min(int(volume), cap if cap is not None else WINNABLE_VOL_CAP) * _comp_factor(
        competition
    )


# ── 카테고리 균형(라운드로빈) — 한 카테고리 연속 소진 방지 (세션 #50) ────────────
# 무인 리필은 winnable 점수 **전역 1위**를 매일 집는다. 그래서 한 카테고리가 상위를 점유하면
# 그 씨앗이 소진될 때까지 같은 주제만 나간다 — 큐 이력 실측: 07-20~27 cutting-board **6일 연속**
# (나무도마·스텐도마·도마추천·엔드그레인도마·실리콘도마·TPU도마). 같은 주제 글이 쌓이면 서로
# 검색 경쟁을 하고 색인·노출 효율이 떨어진다(GSC 실측: 도마 6편 상위 노출 0편, 씨앗 소진율 67%).
#
# ★설계 근거(실데이터로 1차안 기각): '마지막 사용 시점이 오래된 카테고리 우선'은 **누적 사용량을
#   무시**해 틀린다 — cutting-board는 6편이나 썼는데도 마지막 시점만 보면 우선 대상이 됐다.
#   그래서 **사용 횟수**를 1차 키로 쓴다. 다만 횟수만 쓰면 신규·소량 카테고리가 균형점에 닿을
#   때까지 연속 독식하므로, **직전 카테고리 연속 회피**를 그 앞에 둔다(격일 이상 간격 보장).
# ★점수는 버리지 않는다 — 동률(같은 사용 횟수) 판정에만 쓰므로 카테고리 안에서는 여전히
#   winnable 상위가 먼저 나간다. 후보 **집합**도 그대로라 '적격이 있는데 못 고르는' 일은 없다.
_BALANCE_HISTORY = 60  # 큐 이력 조회 폭 — 카테고리 7개 기준 한 바퀴를 넉넉히 덮음.
_UNMAPPED_RANK = 10**6  # 미매핑은 균형 대상이 아님 — 맨 뒤(어차피 리필 적격 필터가 거름).


def category_usage(
    conn: sqlite3.Connection,
    *,
    history: int = _BALANCE_HISTORY,
    seo: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, int], str | None]:
    """큐 이력 → (카테고리별 사용 횟수, 직전 사용 카테고리). 세션 #50.

    사람이 추가한 키워드도 그 카테고리를 **소비한 것**이므로 함께 센다(균형은 유입 경로와 무관).
    큐 테이블이 없거나(구 스키마) 비면 ({}, None) — 호출부가 기존 점수순으로 자연 폴백한다.
    """
    from collector import keyword_relevance  # 지연 임포트(순환 회피)

    try:
        rows = conn.execute(
            "SELECT keyword FROM keyword_queue ORDER BY created_at DESC, id DESC LIMIT ?",
            (int(history),),
        ).fetchall()
    except sqlite3.OperationalError:  # 큐 테이블 없음 — 균형 판정 생략(멈추지 않음)
        return {}, None

    data = seo if seo is not None else seo_keywords.load_all()
    counts: dict[str, int] = {}
    last: str | None = None
    for (kw,) in rows:
        slug = keyword_relevance.resolve_category(str(kw or ""), data)
        if slug is None:  # 미매핑은 어느 카테고리도 소비하지 않았다
            continue
        if last is None:  # 첫 매핑 행 = 가장 최근에 쓴 카테고리
            last = slug
        counts[slug] = counts.get(slug, 0) + 1
    return counts, last


def balance_sorted(
    recs: list[dict[str, Any]],
    counts: dict[str, int],
    last_slug: str | None,
    *,
    seo: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """추천 후보를 카테고리 균형순으로 **재배열**(집합 불변 — 정렬만). 세션 #50.

    키: (직전 카테고리면 1, 사용 횟수, -winnable 점수) 오름차순.
    """
    from collector import keyword_relevance  # 지연 임포트(순환 회피)

    data = seo if seo is not None else seo_keywords.load_all()

    def _key(rec: dict[str, Any]) -> tuple[int, int, float]:
        slug = keyword_relevance.resolve_category(str(rec.get("keyword") or ""), data)
        if slug is None:
            return (1, _UNMAPPED_RANK, 0.0)
        return (
            1 if slug == last_slug else 0,
            counts.get(slug, 0),
            -winnable_score(rec.get("volume"), rec.get("competition")),
        )

    return sorted(recs, key=_key)  # stable — 동률은 원(점수) 순서 보존


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
    volume_ceiling: int | None = None,
) -> list[dict[str, Any]]:
    """추천 키워드(검색량순). 항목: {keyword, volume, competition, seed, core, category, channel, source}.

    - custom_seed 지정 시 그 씨앗만 확장(임의 주제·core 미적용). 아니면 seeds, 그것도 없으면 기본 씨앗.
    - live=True: 네이버 실조회(씨앗별 실패 시 캐시 강등). live=False: 캐시(secondary)만 — 네트워크 0.
    - 공략 구간 [volume_floor, volume_ceiling] (세션 #51) — 미지정 시 설정값. ceiling=0이면 상한 없음.
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

    floor = _volume_floor() if volume_floor is None else volume_floor
    ceiling = _volume_ceiling() if volume_ceiling is None else volume_ceiling
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
            # 공략 구간 상한(세션 #51) — 검색량이 이보다 크면 기존 강자가 점유해 신규 도메인이
            # 못 이긴다. 캐시 강등분(volume=None)은 판정 불가라 통과시킨다(#50 강등 경로 보존).
            _v = row.get("volume")
            if ceiling and _v is not None and int(_v) > ceiling:
                continue
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
                return {
                    "keyword_id": int(kid),
                    "keyword": str(kw),
                    "source": "queue",
                    "degraded": False,  # 큐 재사용은 검색량 조회와 무관
                }
        # 전부 미매핑 — 멈추지 않고 맨 위 1건(behavior 보존). digest가 '큐 발행가능 0'을 ALERT.
        return {
            "keyword_id": int(rows[0][0]),
            "keyword": str(rows[0][1]),
            "source": "queue",
            "degraded": False,
        }

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
    # ★카테고리 균형(#50): 점수 1위만 집으면 한 카테고리가 소진될 때까지 연속 선택된다
    #   (실측 07-20~27 도마 6일 연속). 적게 쓴 카테고리 우선 + 직전 연속 회피로 순환시킨다.
    #   재배열일 뿐 후보 집합은 그대로 — 적격이 하나뿐이어도 그것을 고른다(§0 멈추지 않음).
    seo_data = seo_keywords.load_all()
    counts, last_slug = category_usage(conn, seo=seo_data)
    recs = balance_sorted(recs, counts, last_slug, seo=seo_data)

    top = None
    for rec in recs:
        slug = keyword_relevance.resolve_category(str(rec.get("keyword") or ""), seo_data)
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
    # ★degraded(#50 fail-loud): 네이버 실검색량이 아니라 캐시(yml secondary)로 고른 키워드인가.
    #   recommend는 조회 실패를 예외로 올리지 않고 캐시로 자가강등하므로(§0 멈추지 않음), 그
    #   사실이 여기서 새어나가지 않으면 **선정 품질이 무너진 채로 조용히 계속 돈다** — 실제로
    #   07-01~27 리필 10건이 전부 캐시였고 한 달간 아무도 몰랐다. 호출부(auto-cycle)가 이 값으로
    #   경보한다. 발행 자체는 되므로 '중단'이 아니라 '가시화'가 옳은 처리다.
    return {
        "keyword_id": kid,
        "keyword": top["keyword"],
        "source": "recommend",
        "degraded": str(top.get("source") or "") == "cached",
    }
