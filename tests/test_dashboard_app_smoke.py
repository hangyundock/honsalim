"""dashboard.app 오프스크린 스모크 테스트 — GUI 골격이 빌드·채워지는지 (세션 #25).

PyQt5 미설치 환경(CI Linux)에서는 skip. 설치된 데스크톱(Windows)에서는 offscreen 플랫폼으로
QApplication을 띄우지 않고 윈도우를 구성·새로고침해 표가 채워지는지 검증(이벤트 루프 미진입).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

try:
    import PyQt5  # noqa: F401

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

pytestmark = pytest.mark.skipif(not _HAS_QT, reason="PyQt5 미설치 (CI Linux) — 데스크톱 전용")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.executescript("""
        INSERT INTO personas (slug, title_ko, description) VALUES ('p', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s', 'S', 'd', 1);
        INSERT INTO keyword_queue (keyword, slug, status) VALUES ('전자레인지', 'micro', 'pending');
        INSERT INTO drafts (scenario_id, working_title, status) VALUES (1, '테스트 글', 'validated');
        """)
    conn.commit()
    conn.close()


def test_window_builds_and_populates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    dbpath = tmp_path / "honsalim.db"
    _make_db(dbpath)

    from common import db

    monkeypatch.setattr(db, "DB_PATH", dbpath)

    from PyQt5.QtWidgets import QApplication

    from dashboard import app as gui

    qapp = QApplication.instance() or QApplication([])
    assert qapp is not None

    win = gui.DashboardWindow()
    win.refresh()

    # 통계 카드: 대기 키워드 1
    assert win.cards["keywords_pending"].val.text() == "1"
    # 발행 큐: validated 1건
    assert win.tab_queue.rowCount() == 1
    # 키워드 탭: 1건
    assert win.tab_keywords.rowCount() == 1
    # 배너에 설정 요약 표시
    assert "자동발행" in win.banner.text()

    win.close()


def test_dialogs_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """쿠팡/설정 다이얼로그가 빌드되고 값 수집이 동작하는지 (Phase E·F)."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    from dashboard import app as gui

    qapp = QApplication.instance() or QApplication([])
    assert qapp is not None

    cdlg = gui.CoupangProductDialog()
    v = cdlg.values()
    assert v["name"] == "" and v["price"] is None  # 빈 폼 안전

    sdlg = gui.SettingsDialog()
    cfg = sdlg.collect()
    assert "publish_per_day" in cfg and "coupang_mode" in cfg
    assert isinstance(cfg["featured_per_tier"], int)
