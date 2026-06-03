"""dashboard 회귀 테스트 — BACKEND §2-6 + DECISIONS G3 [확정 #9].

render: drafts 그룹별 HTML 생성·status별 카드·1클릭 승인 명령 노출·24h fail 배너
approve: state_machine 연동·flag 파일 생성·IllegalStateError 전파
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from dashboard import approve as dash_approve
from dashboard import render as dash_render
from writer import state_machine

# ──────────────────────────────────────────
# 픽스처 — drafts 테이블 + 시드
# ──────────────────────────────────────────


def _new_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title_ko TEXT NOT NULL
        );
        CREATE TABLE drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL REFERENCES scenarios(id),
            working_title TEXT,
            status TEXT NOT NULL DEFAULT 'collected'
                CHECK (status IN ('collected','enriched','validated','approved','published','rejected')),
            status_reason TEXT,
            raw_payload TEXT,
            enriched_payload TEXT,
            validation_report TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            promoted_article_id INTEGER
        );
        INSERT INTO scenarios(slug, title_ko) VALUES ('s1', '시나리오1'), ('s2', '시나리오2');
        """)
    return conn


def _seed_drafts(conn: sqlite3.Connection, items: list[tuple[int, str, str | None]]) -> None:
    """items: [(scenario_id, status, working_title), ...]"""
    for scenario_id, status, title in items:
        conn.execute(
            "INSERT INTO drafts(scenario_id, status, working_title) VALUES (?,?,?)",
            (scenario_id, status, title),
        )
    conn.commit()


# ──────────────────────────────────────────
# render 회귀
# ──────────────────────────────────────────


def test_fetch_drafts_by_status_groups():
    conn = _new_conn()
    _seed_drafts(
        conn,
        [
            (1, "validated", "검토A"),
            (1, "validated", "검토B"),
            (2, "enriched", "보강A"),
            (1, "published", "게시A"),
        ],
    )
    grouped = dash_render.fetch_drafts_by_status(conn)
    assert len(grouped["validated"]) == 2
    assert len(grouped["enriched"]) == 1
    assert len(grouped["published"]) == 1
    assert len(grouped.get("rejected", [])) == 0


def test_render_html_contains_status_cards():
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "검토 카드")])
    grouped = dash_render.fetch_drafts_by_status(conn)
    html_str = dash_render.render_html(grouped, fail_24h=0)
    assert "검토 카드" in html_str
    assert 'data-status="validated"' in html_str
    assert "혼살림 dashboard" in html_str


def test_render_html_shows_approve_command_only_for_validated():
    conn = _new_conn()
    _seed_drafts(
        conn,
        [
            (1, "validated", "승인대상"),
            (1, "collected", "미수확"),
        ],
    )
    grouped = dash_render.fetch_drafts_by_status(conn)
    html_str = dash_render.render_html(grouped, fail_24h=0)
    # validated에만 approve 명령
    assert "python -m honsalim approve --draft" in html_str
    # validated 카드에 approve 명령 1회
    assert html_str.count("python -m honsalim approve --draft") == 1


def test_render_html_red_banner_when_fail_24h_3plus():
    grouped = {s: [] for s, _ in dash_render.STATUS_GROUPS}
    html_no_banner = dash_render.render_html(grouped, fail_24h=2)
    html_with_banner = dash_render.render_html(grouped, fail_24h=5)
    # CSS .banner-red는 항상 <style>에 정의돼 있음 → 실제 div 요소 사용 여부로 검증
    assert '<div class="banner-red">' not in html_no_banner
    assert '<div class="banner-red">' in html_with_banner
    assert "5건" in html_with_banner


def test_render_html_escapes_user_content():
    """working_title에 HTML 주입 시 escape — XSS 방지."""
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "<script>alert(1)</script>")])
    grouped = dash_render.fetch_drafts_by_status(conn)
    html_str = dash_render.render_html(grouped, fail_24h=0)
    assert "<script>alert(1)</script>" not in html_str
    assert "&lt;script&gt;" in html_str


def test_render_dashboard_writes_file(tmp_path: Path):
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "파일테스트")])
    out = tmp_path / "dash" / "index.html"
    written = dash_render.render_dashboard(conn=conn, output_path=out)
    assert written == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "파일테스트" in content


def test_count_validation_fails_24h_only_validator_rejected():
    conn = _new_conn()
    # validator 사유 rejected만 카운트
    conn.execute(
        "INSERT INTO drafts(scenario_id, status, status_reason, updated_at) "
        "VALUES (1, 'rejected', 'validator truth fail', datetime('now', '-1 hour'))"
    )
    conn.execute(
        "INSERT INTO drafts(scenario_id, status, status_reason, updated_at) "
        "VALUES (1, 'rejected', 'user manual reject', datetime('now', '-1 hour'))"
    )
    conn.execute(
        "INSERT INTO drafts(scenario_id, status, status_reason, updated_at) "
        "VALUES (1, 'rejected', 'validator schema fail', datetime('now', '-2 day'))"
    )
    conn.commit()
    n = dash_render.count_validation_fails_24h(conn)
    assert n == 1


# ──────────────────────────────────────────
# 무인 모니터링 섹션 회귀 (세션 #23)
# ──────────────────────────────────────────


def test_load_last_cycle_missing_returns_none(tmp_path: Path):
    assert dash_render.load_last_cycle(tmp_path / "nope.json") is None


def test_load_last_cycle_corrupt_returns_none(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert dash_render.load_last_cycle(p) is None


def test_render_cycle_section_no_report():
    html_str = dash_render.render_cycle_section(None)
    assert "아직 실행 기록 없음" in html_str


def test_render_cycle_section_shows_killswitch_and_deploy():
    report = {
        "ran_at": "2026-06-03T11:00:00+09:00",
        "dry_run": False,
        "published": ["a", "b"],
        "refreshed": [{"slug": "a", "ok": False, "error": "API 실패"}],
        "refresh_ok": 1,
        "refresh_fail": 1,
        "killswitched": ["b"],
        "deployed": True,
        "changed": True,
        "verify_status": 200,
    }
    html_str = dash_render.render_cycle_section(report)
    assert "2026-06-03T11:00:00+09:00" in html_str
    assert "자가복원" in html_str and "b" in html_str
    assert "새로고침 실패 a" in html_str
    assert "배포됨" in html_str and "verify 200" in html_str


def test_render_health_section_no_categories_table():
    conn = _new_conn()  # categories 테이블 없음 (부분 DB)
    html_str, flags = dash_render.render_health_section(conn)
    assert html_str == "" and flags == 0


def test_render_health_section_lists_published(tmp_path: Path):
    from common import db

    db_path = tmp_path / "t.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    conn = db.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("UPDATE categories SET status='published' WHERE slug='office-chair'")
    conn.commit()
    try:
        html_str, flag_count = dash_render.render_health_section(conn)
    finally:
        conn.close()
    assert "office-chair" in html_str
    assert "공개 카테고리 건강" in html_str
    assert flag_count >= 0  # 휴리스틱 미달 카운트(빈 카테고리면 1+)


def test_render_dashboard_includes_monitoring_and_alert(tmp_path: Path):
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "x")])
    report_p = tmp_path / "cycle.json"
    report_p.write_text(
        json.dumps(
            {
                "ran_at": "2026-06-03T11:00:00+09:00",
                "dry_run": False,
                "published": ["a"],
                "refreshed": [],
                "refresh_ok": 1,
                "refresh_fail": 0,
                "killswitched": ["a"],
                "deployed": False,
                "changed": False,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "index.html"
    dash_render.render_dashboard(conn=conn, output_path=out, cycle_report_path=report_p)
    content = out.read_text(encoding="utf-8")
    assert "무인 사이클" in content
    assert '<div class="banner-amber">' in content  # 자가복원 경고 배너
    assert "자가복원" in content


# ──────────────────────────────────────────
# approve 회귀
# ──────────────────────────────────────────


def test_approve_transitions_validated_to_approved(tmp_path: Path):
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "승인테스트")])
    flag = dash_approve.approve(conn, draft_id=1, user_note="검토 OK", flag_dir=tmp_path)
    assert state_machine.current_status(conn, 1) == "approved"
    assert flag.exists()
    data = json.loads(flag.read_text(encoding="utf-8"))
    assert data["draft_id"] == 1
    assert data["user_note"] == "검토 OK"


def test_approve_raises_on_illegal_state(tmp_path: Path):
    conn = _new_conn()
    _seed_drafts(conn, [(1, "collected", "미검토")])
    with raises(state_machine.IllegalStateError):
        dash_approve.approve(conn, draft_id=1, flag_dir=tmp_path)


def test_approve_flag_dir_auto_created(tmp_path: Path):
    conn = _new_conn()
    _seed_drafts(conn, [(1, "validated", "디렉터리테스트")])
    deep = tmp_path / "a" / "b" / "c"
    flag = dash_approve.approve(conn, draft_id=1, flag_dir=deep)
    assert deep.exists()
    assert flag.parent == deep
