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
    # 배너: 3줄 안내(세션 #41 — 상태/예정/다음 할 일)로 갱신됨. 테스트 config는 auto_mode
    # 기본 OFF → '무인 OFF' 상태줄 + 예정/할 일 줄이 포함돼야 한다(naver_blog UX 미러).
    banner = win.banner.text()
    assert "무인" in banner  # 상태줄 (ON/OFF 공통)
    assert "예정" in banner  # 런웨이줄
    assert "다음 할 일" in banner  # 행동 지시줄

    win.close()


def test_progress_busy_done_toggles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """세션 #30 B: 진행 표시 — 작업 시작/완료 시 진행바·버튼·상태 라벨·타이틀이 토글되는지.

    이벤트 루프·워커 스레드 없이 상태 메서드(_set_busy/_set_done)를 직접 검증. 표시 여부는
    부모 윈도우 미표시와 무관한 isHidden()(명시적 setVisible 상태)으로 확인.
    """
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

    # 초기: 진행바 숨김 · 액션 버튼 활성 · 타이틀 기본
    assert win.progress.isHidden() is True
    assert win._action_buttons and all(b.isEnabled() for b in win._action_buttons)
    assert win.windowTitle() == gui._TITLE_IDLE

    # 시작: 진행바 표시 · 버튼 일괄 비활성 · 상태 라벨에 작업명 · 타이틀에 진행 표시
    win._set_busy("글 생성")
    assert win.progress.isHidden() is False
    assert all(not b.isEnabled() for b in win._action_buttons)
    assert "글 생성" in win.status_label.text()
    assert "⏳" in win.windowTitle()

    # 완료(성공): 진행바 숨김 · 버튼 재활성 · 상태에 완료 · 타이틀 원복
    win._set_done("ok", "글 생성")
    assert win.progress.isHidden() is True
    assert all(b.isEnabled() for b in win._action_buttons)
    assert "완료" in win.status_label.text()
    assert win.windowTitle() == gui._TITLE_IDLE

    # 실패 경로: 상태에 실패 표시 + 버튼 복구(작업 실패해도 UI 잠기지 않음)
    win._set_busy("발행")
    win._set_done("fail", "발행")
    assert "실패" in win.status_label.text()
    assert all(b.isEnabled() for b in win._action_buttons)

    # 이중 _set_done 방어: busy 아닐 때 호출해도 무해(커서 스택 균형)
    win._set_done("ok", "노옵")  # _busy=False라 무시되어야
    assert "실패" in win.status_label.text()  # 상태 안 바뀜

    win.close()


def test_status_cells_render_korean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """세션 #35: 발행 큐·키워드 탭 '상태' 컬럼이 한글 라벨로 표시 (DB status 값은 영어 유지).

    주인 지시 — 화면에 'validated/drafted' 같은 영어가 보이지 않게. 매핑은 표시 레이어에서만
    하고 DB·상태머신 값은 그대로(쿼리 WHERE status='validated' 무영향). 미정의 상태는 원문 폴백.
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    dbpath = tmp_path / "honsalim.db"
    _make_db(dbpath)

    from common import db

    monkeypatch.setattr(db, "DB_PATH", dbpath)

    from PyQt5.QtWidgets import QApplication

    from dashboard import app as gui

    qapp = QApplication.instance() or QApplication([])
    assert qapp is not None

    # 순수 매핑 — 알려진 상태는 한글, 미정의는 원문 그대로(안전 폴백)
    assert gui._status_label("validated") == "검토 대기"
    assert gui._status_label("drafted") == "글 생성됨"
    assert gui._status_label("approved") == "승인됨"
    assert gui._status_label("published") == "게시됨"
    assert gui._status_label("pending") == "대기"
    assert gui._status_label("rejected") == "반려됨"
    assert gui._status_label("어떤상태없음") == "어떤상태없음"

    win = gui.DashboardWindow()
    win.refresh()
    # 발행 큐: draft status='validated' → '검토 대기'(영어 미노출)
    assert win.tab_queue.item(0, 1).text() == "검토 대기"
    # 키워드 탭: keyword status='pending' → '대기'
    assert win.tab_keywords.item(0, 3).text() == "대기"
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
