"""사용법 안내(GuideDialog) — 단계 진행 + 각 단계가 관련 탭으로 자동 전환 (네이버 대시보드에서 이식).

PyQt5 미설치 환경(CI Linux)에서는 skip. GuideDialog는 순수 PyQt(DB 불필요)라 오프스크린으로
QApplication만 띄워 검증한다(이벤트 루프 미진입).
"""

from __future__ import annotations

import os

import pytest

try:
    import PyQt5  # noqa: F401

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

pytestmark = pytest.mark.skipif(not _HAS_QT, reason="PyQt5 미설치 (CI Linux) — 데스크톱 전용")

# GuideDialog를 오프스크린 Qt로 렌더하면 일부 환경(#43 기록·이 샌드박스 포함)에서 Qt 네이티브
# 크래시(0xC0000005)가 나 pytest 프로세스를 통째로 죽인다 — 전체 회귀가 중단된다. 네이티브
# 크래시는 Python 예외로 못 잡으므로, 위젯을 실제로 만드는 테스트만 기본 skip하고 실데스크톱에서
# HONSALIM_QT_WIDGET_TESTS=1로 opt-in 실행한다(#43은 네이티브 디스플레이서 수동 검증 완료). 세션 #44.
_WIDGET_OK = os.environ.get("HONSALIM_QT_WIDGET_TESTS") == "1"


@pytest.mark.skipif(
    not _WIDGET_OK,
    reason="GuideDialog 오프스크린 렌더가 일부 환경서 Qt 네이티브 크래시(#43) — "
    "실데스크톱서 HONSALIM_QT_WIDGET_TESTS=1로 실행",
)
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
