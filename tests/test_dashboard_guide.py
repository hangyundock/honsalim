"""사용법 안내(GuideDialog) — 단계 진행 + 각 단계가 관련 탭으로 자동 전환 (네이버 대시보드에서 이식).

PyQt5 미설치 환경(CI Linux)에서는 skip. GuideDialog는 순수 PyQt(DB 불필요)라 오프스크린으로
QApplication만 띄워 검증한다(이벤트 루프 미진입).
"""

from __future__ import annotations

import pytest

try:
    import PyQt5  # noqa: F401

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

pytestmark = pytest.mark.skipif(not _HAS_QT, reason="PyQt5 미설치 (CI Linux) — 데스크톱 전용")


def test_guide_dialog_navigation_and_tab_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    from dashboard import app as gui

    QApplication.instance() or QApplication([])
    steps = gui.GUIDE_STEPS
    assert steps[0]["tab"] == 0  # ★1단계 = 제품 키워드 탭(index 0)
    visited: list[int] = []
    dlg = gui.GuideDialog(steps, visited.append)
    assert dlg.i == 0
    assert visited[-1] == 0  # 첫 단계에서 키워드 탭으로 이동
    for _ in range(len(steps) - 1):  # 끝까지 진행
        dlg._next()
    assert dlg.i == len(steps) - 1
    assert dlg.b_next.text().startswith("닫기")  # 마지막 단계 = 닫기
    assert visited[-1] == 4  # 마지막 단계 = 설정 탭
    dlg._prev()
    assert dlg.i == len(steps) - 2  # 이전으로도 이동


def test_guide_steps_have_required_fields() -> None:
    from dashboard import app as gui

    for s in gui.GUIDE_STEPS:
        assert s["title"] and s["body"]
        assert s["tab"] is None or s["tab"] in (0, 1, 2, 3, 4)
