"""dashboard.queries — 운영 대시보드 읽기 데이터 레이어 (세션 #25).

PyQt에 비의존(테스트 가능). GUI(app.py)와 HTML 모니터(render.py) 양쪽이 쓸 수 있는 순수 함수.
기존 render.py의 데이터 함수(load_last_cycle 등)를 재사용하고, 키워드 큐·통계·카테고리 건강
데이터를 dict 형태로 추가한다. 모든 함수는 테이블 미존재(마이그레이션 전)에도 안전(§0).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from writer import auto_publish

from . import render

# render.py의 순수 데이터 함수 재노출 (중복 제거)
load_last_cycle = render.load_last_cycle


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def dashboard_stats(conn: sqlite3.Connection) -> dict[str, int]:
    """상단 통계 카드용 카운트. 테이블 없으면 해당 항목 0 (안전)."""

    def _count(sql: str) -> int:
        try:
            row = conn.execute(sql).fetchone()
            return int(row[0]) if row else 0
        except sqlite3.OperationalError:
            return 0

    return {
        "keywords_pending": _count("SELECT COUNT(*) FROM keyword_queue WHERE status='pending'"),
        "keywords_total": _count("SELECT COUNT(*) FROM keyword_queue"),
        "drafts_validated": _count("SELECT COUNT(*) FROM drafts WHERE status='validated'"),
        "drafts_approved": _count("SELECT COUNT(*) FROM drafts WHERE status='approved'"),
        "articles_published": _count("SELECT COUNT(*) FROM articles WHERE status='published'"),
        "categories_published": _count("SELECT COUNT(*) FROM categories WHERE status='published'"),
        # ★세션 #41 — 반려/미발행 가시화(옛 '조용한 데드엔드'가 어느 카운터에도 안 잡혀 무인
        # 운영 중 사람이 문제를 못 보던 근본 문제 해소). 게이트 반려 상한 도달로 격리된 키워드,
        # 자동 재생성 대기 중(pending·fail_count>0), 승인됐으나 미발행인 글을 각각 노출한다.
        "keywords_gate_failed": _count(
            "SELECT COUNT(*) FROM keyword_queue WHERE status='failed' "
            "AND status_reason LIKE '%반려%'"
        ),
        "keywords_retrying": _count(
            "SELECT COUNT(*) FROM keyword_queue WHERE status='pending' AND fail_count > 0"
        ),
        "articles_unpublished": _count("SELECT COUNT(*) FROM articles WHERE status='unpublished'"),
    }


def list_keywords(
    conn: sqlite3.Connection, status: str | None = None, limit: int = 500
) -> list[dict[str, Any]]:
    """키워드 큐 목록. 정렬: **미리선택(쿠팡 등 target_products) 있는 키워드 우선** → score → priority → id.

    auto_pick_keyword와 동일 정렬(화면 맨 위 = 자동 선정 대상). 쿠팡 세팅한 키워드가
    검색량 높은 알리 추천보다 먼저 와 '글 생성'에 쿠팡이 포함됨(세션 #28 Part2). status 지정 시 필터.
    """
    if not _table_exists(conn, "keyword_queue"):
        return []
    conn.row_factory = sqlite3.Row
    base = "SELECT * FROM keyword_queue"
    order = (
        " ORDER BY (target_products IS NOT NULL AND target_products NOT IN ('', '[]')) DESC, "
        "score DESC, priority DESC, id LIMIT ?"
    )
    if status:
        rows = conn.execute(base + " WHERE status = ?" + order, (status, limit)).fetchall()
    else:
        rows = conn.execute(base + order, (limit,)).fetchall()
    return [dict(r) for r in rows]


def list_queue(
    conn: sqlite3.Connection,
    statuses: tuple[str, ...] = ("validated", "approved", "published"),
    limit: int = 500,
) -> list[dict[str, Any]]:
    """발행 큐 — drafts(검토대기/승인/게시) + 연결 키워드 제목. 최신순."""
    if not _table_exists(conn, "drafts"):
        return []
    conn.row_factory = sqlite3.Row
    qmarks = ",".join("?" * len(statuses))
    has_kw = _table_exists(conn, "keyword_queue")
    # 키워드 큐(마이그레이션 007) 유무에 따라 컬럼/조인 분기 — 보간 값은 모두 코드 상수(주입 아님).
    # 001-only DB는 drafts.keyword_id 컬럼도 없으므로 NULL 별칭으로 대체.
    kw_select = "d.keyword_id, k.keyword" if has_kw else "NULL AS keyword_id, NULL AS keyword"
    kw_join = "LEFT JOIN keyword_queue k ON k.id = d.keyword_id" if has_kw else ""
    sql = f"SELECT d.id, d.working_title, d.status, d.status_reason, d.created_at, {kw_select} FROM drafts d {kw_join} WHERE d.status IN ({qmarks}) ORDER BY d.created_at DESC LIMIT ?"  # noqa: S608
    rows = conn.execute(sql, (*statuses, limit)).fetchall()
    return [dict(r) for r in rows]


SITE_ORIGIN = "https://honsallim.com"


def list_articles(
    conn: sqlite3.Connection,
    statuses: tuple[str, ...] = ("published", "unpublished", "archived"),
    limit: int = 500,
) -> list[dict[str, Any]]:
    """발행 글 관리 목록 — articles(공개/비공개/보관) + 라이브 URL. 공개 먼저·최신 발행순 (세션 #37).

    완전 무인 발행의 '사후 검토' 화면용: 자동 발행된 글을 사람이 목록·링크로 확인하고
    비공개(내리기)/재공개한다. 렌더러는 published만 렌더하므로 unpublished는 라이브에 없다
    (live_url은 published 글의 실제 주소, 비공개 글은 참고용). 테이블 없으면 [] (안전·§0).
    """
    if not _table_exists(conn, "articles"):
        return []
    conn.row_factory = sqlite3.Row
    qmarks = ",".join("?" * len(statuses))
    # 보간되는 qmarks는 상태 수만큼의 '?'(값 주입 아님)·값은 파라미터로 — list_queue와 동일 안전 패턴.
    sql = f"SELECT id, slug, title, status, published_at, updated_at FROM articles WHERE status IN ({qmarks}) ORDER BY (status = 'published') DESC, COALESCE(published_at, updated_at) DESC, id DESC LIMIT ?"  # noqa: S608
    rows = conn.execute(sql, (*statuses, limit)).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["live_url"] = f"{SITE_ORIGIN}/articles/{r['slug']}/"
        out.append(d)
    return out


def auto_forecast(conn: sqlite3.Connection, cfg: dict[str, Any], now: datetime) -> dict[str, Any]:
    """무인 발행 예측 — '재고(쿠팡 첨부 대기)가 며칠분이고 어떤 순서로 나가는지' (세션 #41).

    naver_blog 대시보드 런웨이 UX 미러(주인 지시). 소비 순서 = auto_pick_keyword와 동일 근사:
    발행가능(카테고리 매핑) 우선 → 쿠팡 첨부 우선 → score → priority → id. 예측일은 매일
    schedule_time 1회(publish_per_day=1 기준) — 오늘 아직 발행 전이고 예약 시각 이전이면 오늘부터.

    반환 dict: pending 목록(picks·이름/쿠팡 여부), coupang_pending, retrying, gate_failed,
    dates(발행 예정일 리스트·datetime), published_today.
    """
    from datetime import timedelta

    from collector import keyword_relevance

    rows = conn.execute(
        "SELECT id, keyword, score, priority, fail_count, "
        "(target_products IS NOT NULL AND target_products NOT IN ('','[]')) AS cp "
        "FROM keyword_queue WHERE status='pending' "
        "ORDER BY cp DESC, score DESC, priority DESC, id"
    ).fetchall()
    picks: list[dict[str, Any]] = []
    for r in rows:
        # conn 전달(#45): draft 카테고리 매핑 키워드가 '발행가능·예정일'로 잘못 표시되지 않게
        ok, _code = keyword_relevance.publishability(str(r[1]), conn)
        picks.append(
            {
                "id": int(r[0]),
                "keyword": str(r[1]),
                "coupang": bool(r[5]),
                "publishable": ok,
                "retrying": int(r[4] or 0) > 0,
            }
        )
    # auto_pick은 '발행가능'을 먼저 집는다 — 안정 정렬로 매핑 우선만 얹음(그 외 순서 보존).
    picks.sort(key=lambda p: not p["publishable"])

    gate_failed = int(
        conn.execute(
            "SELECT COUNT(*) FROM keyword_queue WHERE status='failed' "
            "AND status_reason LIKE '%반려%'"
        ).fetchone()[0]
    )
    # published_at은 UTC 저장이지만 발행은 오전(KST) 예약이라 UTC 날짜 == KST 날짜(주석·§0 확인).
    published_today = int(
        conn.execute(
            "SELECT COUNT(*) FROM articles WHERE status='published' "
            "AND substr(published_at, 1, 10) = ?",
            (now.date().isoformat(),),
        ).fetchone()[0]
    )

    # 발행 예정일 — 오늘 발행 전 + 예약 시각 이전이면 오늘부터, 아니면 내일부터 매일 1회.
    try:
        hh, mm = (int(x) for x in str(cfg.get("schedule_time") or "11:00").split(":", 1))
    except ValueError:
        hh, mm = 11, 0
    first = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if published_today or now >= first:
        first += timedelta(days=1)
    dates: list[datetime] = [first + timedelta(days=i) for i in range(len(picks) or 1)]

    return {
        "picks": picks,
        "pending": len(picks),
        "coupang_pending": sum(1 for p in picks if p["coupang"]),
        "retrying": sum(1 for p in picks if p["retrying"]),
        "gate_failed": gate_failed,
        "published_today": published_today,
        "dates": dates,
    }


_WEEK_KO = "월화수목금토일"


def _fmt_day(d: datetime) -> str:
    return f"{d.month}/{d.day}({_WEEK_KO[d.weekday()]})"


def banner_lines(
    conn: sqlite3.Connection, cfg: dict[str, Any], now: datetime
) -> tuple[list[str], str]:
    """대시보드 상단 안내 배너 3줄(상태/예정/다음 할 일) + 심각도 level (세션 #41).

    naver_blog 대시보드 UX 미러(주인 지시): 어쩌다 열어봐도 ①지금 무인이 도는지 ②재고(쿠팡
    첨부)로 언제까지 수익 글이 나가는지 ③다음에 뭘 해야 하는지가 한눈에 보이게.
    반환: (HTML 줄 리스트, level) — level은 'ok'|'caution'|'alert' (배너 색 결정).
    """
    fc = auto_forecast(conn, cfg, now)
    on = bool(cfg.get("auto_mode"))
    per_day = cfg.get("publish_per_day", 1)
    low_threshold = int(cfg.get("coupang_low_threshold", 2) or 0)

    # 1줄 — 상태
    head = (
        f"🟢 완전 무인 ON — 하루 {per_day}편 · 예약 {cfg.get('schedule_time')} KST"
        if on
        else "⚪ 무인 OFF(사람 검수) — 승인된 글만 예약 발행"
    )
    head += f" · 쿠팡 모드 {cfg.get('coupang_mode')}"
    if fc["published_today"]:
        head += " · 오늘 발행 완료 ✅"

    # 2줄 — 예정(런웨이): 예상 소비 순서로 날짜+키워드. 쿠팡 첨부 재고가 며칠분인지 명시.
    cp = fc["coupang_pending"]
    picks = fc["picks"]
    dates = fc["dates"]
    if not picks:
        sched = (
            "📅 예정: 대기 키워드 <b>0개</b> — 예약 시각마다 자동 추천으로 보충해 계속 "
            "발행합니다(쿠팡 링크 없음)"
        )
    else:
        shown = [
            f"{_fmt_day(dates[i])} {p['keyword']}{'🛒' if p['coupang'] else ''}"
            for i, p in enumerate(picks[:4])
        ]
        span = " → ".join(shown) + (" …" if len(picks) > 4 else "")
        if cp:
            until = _fmt_day(dates[cp - 1]) if cp <= len(dates) else "?"
            tail = f"쿠팡 첨부 <b>{cp}편 = {cp}일분, {until}까지</b> 수익 링크 유지"
        else:
            tail = "쿠팡 첨부 <b>0편</b> — 수익 링크 없는 글로 발행됩니다"
        sched = f"📅 예정: {span}  ({tail})"
        if fc["retrying"]:
            sched += f" · 자동 재시도 대기 {fc['retrying']}건"

    # 3줄 — 다음 할 일 (심각도 순: 무인 OFF > 반려 상한 > 쿠팡 0 > 쿠팡 임박 > 충분)
    if not on:
        todo = "👉 다음 할 일: 상단 <b>[무인 ON]</b>을 켜면 매일 자동 생성·발행됩니다"
        level = "caution"
    elif fc["gate_failed"]:
        todo = (
            f"👉 다음 할 일: <b>⚠️ 반려(검토 필요) {fc['gate_failed']}건</b> — 키워드 탭 "
            "<b>[🔁 반려 재시도]</b> 또는 내용 검토"
        )
        level = "alert"
    elif cp == 0:
        todo = (
            "👉 다음 할 일: <b>🛒 [쿠팡 첨부(저장)]</b>으로 키워드+배너를 미리 넣어두세요 "
            "(지금은 쿠팡 수익 없는 글로 계속됩니다)"
        )
        level = "alert"
    elif cp <= low_threshold:
        todo = (
            f"👉 다음 할 일: <b>⚠️ 쿠팡 첨부 {cp}편뿐</b> — 소진 전 "
            "<b>[🛒 쿠팡 첨부(저장)]</b>으로 보충하면 수익 링크가 끊기지 않습니다"
        )
        level = "caution"
    else:
        until = _fmt_day(fc["dates"][cp - 1]) if cp <= len(fc["dates"]) else "?"
        todo = (
            f"👉 다음 할 일: ✅ 쿠팡 첨부 {cp}편 충분 — {until}까지 커버. "
            "소진 전 <b>[🛒 쿠팡 첨부(저장)]</b>으로 보충하면 무인 수익 유지"
        )
        level = "ok"

    return [head, sched, todo], level


def category_health(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """공개 카테고리 건강 — 추천수/전체수 + 가드레일 미달 사유(휴리스틱·무비용)."""
    if not _table_exists(conn, "categories"):
        return []
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT c.id, c.slug, c.name_ko, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id AND is_featured=1) "
        "AS featured, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id) AS total "
        "FROM categories c WHERE c.status='published' ORDER BY c.display_order, c.id"
    ).fetchall()
    # 사후 감시(LLM 미사용) — render.render_health_section과 동일 기준
    flags = {f["slug"]: f.get("reasons", []) for f in auto_publish.monitor(conn, use_llm=False)}
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["flagged"] = r["slug"] in flags
        d["reasons"] = flags.get(r["slug"], [])
        out.append(d)
    return out


def google_usage(conn: sqlite3.Connection) -> dict[str, Any]:
    """Google(Imagen) 이번 달 추정 사용량 + 상한 대비 — 대시보드 표시용 (세션 #36).

    구글 실제 청구액은 단순 API 키로 못 가져와 우리 호출수에 단가를 곱해 **추정**한다('추정' 명시·§0).
    상한(설정 google_spend_cap_usd)>0이면 사용률(%)·임박(≥80%) 경고를 함께 반환. last_429_at이
    있으면 최근 한도초과(429) 발생 = 결제/상한 상향 필요 신호.
    """
    from common import settings
    from writer import api_usage

    s = api_usage.month_summary(conn, "google_imagen")
    cap = float(settings.get("google_spend_cap_usd", 0.0) or 0.0)  # 0.0=미설정(기본도 0.0)·무해
    used = float(s["est_cost_usd"])
    pct = (used / cap * 100.0) if cap > 0 else None
    return {
        "images": int(s["images"]),
        "used_usd": used,
        "cap_usd": cap,
        "pct": pct,
        "near_or_over": bool(pct is not None and pct >= 80.0),
        "last_429_at": s["last_429_at"],
    }
