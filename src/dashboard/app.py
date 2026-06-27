"""dashboard.app — 혼살림 운영 대시보드 (PyQt5 데스크톱 GUI, 세션 #25).

AutoBlog(tistory_revival) 패턴 차용: QThread + stdout 가로채기 → 실시간 로그(UI 안 멈춤).
비즈니스 로직은 PyQt 비의존 모듈(dashboard.queries·writer·deployer 등)에 두고 본 파일은
얇은 GUI 셸이다(테스트는 로직 모듈에서, CI(Linux)는 PyQt 미설치라 app은 import 안 함).

실행: PYTHONPATH=src python -m dashboard.app   (또는 scripts/run_dashboard 런처)

Phase B: 골격 + 통계 카드 + 탭(발행 큐/키워드/모니터링/설정) + 읽기뷰 + 실시간 로그.
액션 버튼(생성·승인·발행)·스케줄러·설정 편집은 Phase C~F에서 연결한다.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import traceback
from collections.abc import Callable
from typing import Any

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from common import db, settings
from dashboard import queries

# 상태별 색 (셀 배경) — AutoBlog 색 관례와 유사
STATUS_COLORS: dict[str, str] = {
    "pending": "#eceff1",
    "generating": "#fff8e1",
    "collected": "#eceff1",
    "enriched": "#e3f2fd",
    "validated": "#e8f5e9",
    "drafted": "#e8f5e9",
    "approved": "#fff3e0",
    "published": "#e1f5fe",
    "rejected": "#ffebee",
    "disabled": "#f5f5f5",
    "failed": "#ffebee",
}

# 상태 한글 표시 라벨 (세션 #35 주인 지시 — 화면 표시만 한글, DB status 값은 영어 유지).
# 상단 카드 용어(검토 대기·승인·게시)와 맞춘다. 미정의 상태는 원문 그대로(안전 폴백).
STATUS_LABELS: dict[str, str] = {
    "pending": "대기",
    "generating": "생성 중",
    "collected": "수집됨",
    "enriched": "보강됨",
    "validated": "검토 대기",
    "drafted": "글 생성됨",
    "approved": "승인됨",
    "published": "게시됨",
    "rejected": "반려됨",
    "disabled": "비활성",
    "failed": "실패",
    "unpublished": "비공개",
    "archived": "보관됨",
}


def _status_label(status: str) -> str:
    """원시 상태 코드(영어) → 화면용 한글 라벨. DB·상태머신 값은 그대로 두고 표시만 변환."""
    return STATUS_LABELS.get(status, status)


# 진행 상태 표시 (세션 #30 B) — 장시간 작업(글 생성 1~2분 등)의 시작/진행/완료 가시화.
# 주인 반복지적: 생성 중 무표시 → 끝난지 모름. 상태 라벨 색으로 즉시 구분.
_TITLE_IDLE = "혼살림 — 운영 대시보드"
_STATUS_IDLE_CSS = "color:#777;font-size:12px;padding:2px 4px;"
_STATUS_BUSY_CSS = "color:#e65100;font-size:12px;font-weight:bold;padding:2px 4px;"
_STATUS_OK_CSS = "color:#1b5e20;font-size:12px;font-weight:bold;padding:2px 4px;"
_STATUS_WARN_CSS = "color:#e65100;font-size:12px;font-weight:bold;padding:2px 4px;"
_STATUS_FAIL_CSS = "color:#b71c1c;font-size:12px;font-weight:bold;padding:2px 4px;"


# ─────────────────────────────────────────────────────────────
# 백그라운드 작업 — UI 프리징 방지 (AutoBlog WorkerThread 패턴)
# ─────────────────────────────────────────────────────────────
class _Stream:
    """print() 출력을 한 줄씩 Qt 시그널로 흘려보냄(실시간 로그)."""

    def __init__(self, sig: Any) -> None:
        self.sig = sig
        self._buf = ""

    def write(self, s: str) -> None:
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self.sig.emit(line)

    def flush(self) -> None:
        if self._buf:
            self.sig.emit(self._buf)
            self._buf = ""


class WorkerThread(QThread):
    """fn()을 별 스레드에서 실행하고 print()를 log 시그널로 스트리밍."""

    log = pyqtSignal(str)
    done = pyqtSignal(bool, object)  # (성공?, 결과 또는 오류문자열)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.fn = fn

    def run(self) -> None:  # QThread 진입점
        old = sys.stdout
        sys.stdout = _Stream(self.log)  # type: ignore[assignment]
        try:
            result = self.fn()
            sys.stdout.flush()
            self.done.emit(True, result)
        except Exception as e:  # 작업 실패를 UI로 전달(스레드 크래시 방지)
            self.done.emit(False, f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
        finally:
            sys.stdout = old


# ─────────────────────────────────────────────────────────────
# 통계 카드
# ─────────────────────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "StatCard{background:#ffffff;border:1px solid #e0e0e0;border-radius:8px;}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        self.val = QLabel("-")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        self.val.setFont(f)
        self.val.setAlignment(Qt.AlignCenter)
        cap = QLabel(label)
        cap.setAlignment(Qt.AlignCenter)
        cap.setStyleSheet("color:#666;font-size:11px;")
        lay.addWidget(self.val)
        lay.addWidget(cap)

    def set_value(self, v: Any) -> None:
        self.val.setText(str(v))


def _read_only_table(headers: list[str]) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t


def _cell(text: str, status: str | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if status and status in STATUS_COLORS:
        item.setBackground(QColor(STATUS_COLORS[status]))
    return item


# ─────────────────────────────────────────────────────────────
# 쿠팡 수동 상품 입력 폼 (Phase E)
# ─────────────────────────────────────────────────────────────
class CoupangProductDialog(QDialog):
    """쿠팡 공식 배너 → '이 키워드로 글 생성' 원팝업 (세션 #28 PartB, naver_blog식).

    키워드(주제)는 자동 채움(수정 가능). 배너(여러 개 가능)에서 이미지·링크·상품명 자동 추출 →
    쿠팡 첨부 + 알리 데이터 결합 하이브리드 글을 한 번에 생성. 배너 이미지는 hotlink(함정#3 무관).
    """

    def __init__(
        self,
        prefill_keyword: str = "",
        parent: QWidget | None = None,
        *,
        attach_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        self.attach_mode = attach_mode
        self.setWindowTitle("쿠팡 배너 첨부(저장)" if attach_mode else "쿠팡 배너 → 글 생성")
        self.resize(560, 420)
        form = QFormLayout(self)
        self.keyword = QLineEdit(prefill_keyword)
        self.keyword.setPlaceholderText("글 주제 키워드 (예: 무선청소기) — 자동 채움·수정 가능")
        if attach_mode:
            self.keyword.setReadOnly(True)  # 선택한 대기 키워드에 저장 (대상 고정)
        self.banner = QTextEdit()
        self.banner.setPlaceholderText(
            "쿠팡 파트너스 '블로그용 배너' HTML 붙여넣기 — <a><img></a> "
            "(여러 개면 줄바꿈 · 이미지·링크·상품명 자동 추출)"
        )
        self.banner.setMaximumHeight(110)
        self.name = QLineEdit()
        self.name.setPlaceholderText("비우면 배너 상품명(alt) 사용")
        self.url = QLineEdit()
        self.url.setPlaceholderText("비우면 배너 링크 사용")
        self.price = QLineEdit()
        self.price.setPlaceholderText("숫자만 (선택)")
        form.addRow("키워드(주제)", self.keyword)
        form.addRow("공식 배너 HTML", self.banner)
        form.addRow("상품명", self.name)
        form.addRow("파트너스 URL", self.url)
        form.addRow("가격(원)", self.price)
        note = QLabel(
            "💾 이 키워드에 쿠팡 배너를 저장만 합니다(생성 안 함·비용 없음). 키워드는 '대기'로 유지되고, "
            "스케줄러(auto-cycle) 또는 '글 생성' 시 이 쿠팡으로 하이브리드(쿠팡+알리) 글이 만들어집니다."
            if attach_mode
            else "✅ 배너 이미지가 글에 표시됩니다(hotlink·다운로드 아님). '이 키워드로 글 생성'을 누르면 "
            "쿠팡 + 알리 데이터를 합친 글이 만들어지고 검토 대기로 들어갑니다 "
            "(LLM 비용 발생·자동 발행 안 함)."
        )
        note.setStyleSheet("color:#1b5e20;font-size:11px;")
        note.setWordWrap(True)
        form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setText("이 키워드에 저장" if attach_mode else "이 키워드로 글 생성")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict[str, Any]:
        price_text = self.price.text().strip()
        return {
            "keyword": self.keyword.text().strip(),
            "name": self.name.text().strip(),
            "url": self.url.text().strip(),
            "price": int(price_text) if price_text.isdigit() else None,
            "banner": self.banner.toPlainText().strip() or None,
        }


# ─────────────────────────────────────────────────────────────
# 추천 키워드 선택 창 (세션 #26)
# ─────────────────────────────────────────────────────────────
class RecommendDialog(QDialog):
    """추천 키워드 목록에서 선택 — 한 행 선택 추가 또는 1순위 자동 추가.

    추천 생성(네이버 조회)은 부모의 백그라운드 작업에서 끝낸 뒤 결과만 넘겨받는다(UI 비프리징).
    """

    def __init__(self, recs: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("추천 키워드 — 선택")
        self.resize(640, 480)
        self.recs = recs
        self._choices: list[dict[str, Any]] = []
        lay = QVBoxLayout(self)
        info = QLabel(
            "검색량순 추천입니다. 맨 앞 체크박스로 여러 개를 한꺼번에 고른 뒤 "
            "'체크한 키워드 추가'를 누르세요(행을 클릭해도 체크됩니다).\n"
            "(월검색량=네이버 실데이터 · '캐시'=검색량 미상 보조키워드)"
        )
        info.setStyleSheet("color:#555;")
        info.setWordWrap(True)
        lay.addWidget(info)
        # 맨 앞 체크박스 컬럼 — 여러 키워드를 한 번에 골라 일괄 등록(#38 주인 요청).
        self.table = _read_only_table(["✓", "키워드", "월검색량", "경쟁도", "씨앗", "출처"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setRowCount(len(recs))
        for i, r in enumerate(recs):
            vol = f"{r['volume']:,}" if r.get("volume") is not None else "—"
            src = "네이버" if r.get("source") == "naver" else "캐시"
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table.setItem(i, 0, chk)
            self.table.setItem(i, 1, _cell(str(r.get("keyword") or "")))
            self.table.setItem(i, 2, _cell(vol))
            self.table.setItem(i, 3, _cell(str(r.get("competition") or "")))
            self.table.setItem(i, 4, _cell(str(r.get("seed") or "")))
            self.table.setItem(i, 5, _cell(src))
        # 키워드 등 다른 칸을 클릭해도 그 행 체크가 토글되게(체크박스 칸을 정확히 안 눌러도 편하게).
        self.table.cellClicked.connect(self._toggle_row)
        lay.addWidget(self.table, 1)
        bar = QHBoxLayout()
        b_all = QPushButton("전체 선택")
        b_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        b_none = QPushButton("전체 해제")
        b_none.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        b_sel = QPushButton("✅ 체크한 키워드 추가")
        b_sel.clicked.connect(self._choose_selected)
        b_top = QPushButton("⭐ 1순위만 추가")
        b_top.clicked.connect(self._choose_top)
        b_cancel = QPushButton("취소")
        b_cancel.clicked.connect(self.reject)
        bar.addWidget(b_all)
        bar.addWidget(b_none)
        bar.addStretch(1)
        bar.addWidget(b_sel)
        bar.addWidget(b_top)
        bar.addWidget(b_cancel)
        lay.addLayout(bar)

    def _toggle_row(self, row: int, col: int) -> None:
        if col == 0:
            return  # 체크박스 칸은 Qt가 직접 토글 — 중복 방지
        it = self.table.item(row, 0)
        if it is not None:
            it.setCheckState(Qt.Unchecked if it.checkState() == Qt.Checked else Qt.Checked)

    def _set_all(self, state: Qt.CheckState) -> None:
        for i in range(len(self.recs)):
            it = self.table.item(i, 0)
            if it is not None:
                it.setCheckState(state)

    def _checked_indices(self) -> list[int]:
        out = []
        for i in range(len(self.recs)):
            it = self.table.item(i, 0)
            if it is not None and it.checkState() == Qt.Checked:
                out.append(i)
        return out

    def _choose_selected(self) -> None:
        idxs = self._checked_indices()
        if not idxs:
            QMessageBox.information(
                self, "선택 필요", "체크박스로 키워드를 1개 이상 고르세요(또는 '1순위만 추가')."
            )
            return
        self._choices = [self.recs[i] for i in idxs]
        self.accept()

    def _choose_top(self) -> None:
        self._choices = [self.recs[0]] if self.recs else []
        self.accept()

    def chosen_list(self) -> list[dict[str, Any]]:
        return self._choices


# ─────────────────────────────────────────────────────────────
# 설정 편집 창 (Phase F)
# ─────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    """config.json 편집 폼 (정수/실수/선택/문자). 저장 시 settings.save."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("혼살림 설정")
        self.resize(480, 520)
        cfg = settings.load()
        form = QFormLayout(self)
        self._w: dict[str, QWidget] = {}

        def add_spin(key: str, label: str, lo: int, hi: int) -> None:
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(int(cfg.get(key, 0) or 0))
            self._w[key] = s
            form.addRow(label, s)

        def add_dspin(key: str, label: str, lo: float, hi: float) -> None:
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setValue(float(cfg.get(key, 0) or 0))
            self._w[key] = s
            form.addRow(label, s)

        def add_line(key: str, label: str) -> None:
            e = QLineEdit(str(cfg.get(key) or ""))
            self._w[key] = e
            form.addRow(label, e)

        def add_combo(key: str, label: str, opts: list[str]) -> None:
            c = QComboBox()
            c.addItems(opts)
            cur = str(cfg.get(key) or opts[0])
            if cur in opts:
                c.setCurrentText(cur)
            self._w[key] = c
            form.addRow(label, c)

        def add_check(key: str, label: str) -> None:
            cb = QCheckBox()
            cb.setChecked(bool(cfg.get(key, False)))
            self._w[key] = cb
            form.addRow(label, cb)

        add_spin("publish_per_day", "하루 발행 편수", 0, 50)
        add_line("schedule_time", "예약 시각 (HH:MM)")
        add_spin("schedule_jitter_min", "발행 지터(분)", 0, 120)
        # ★완전 무인(세션 #34) — 켜면 예약 작업이 생성·승인·발행까지 자동(끄면 승인 글만 발행).
        add_check("auto_mode", "완전 무인 모드 (생성·승인·발행 자동)")
        add_spin("auto_approve_min_published", "자동승인 전 사람 검수 편수", 0, 50)
        add_spin("enrich_max_attempts", "글 5게이트 재생성 상한", 1, 5)
        add_spin("featured_per_tier", "티어별 추천 수", 1, 10)
        add_dspin("satisfaction_floor", "만족도 하한(%)", 0.0, 100.0)
        add_spin("seo_max_attempts", "SEO 재생성 상한", 1, 5)
        add_combo("default_channel", "기본 채널", ["ali", "coupang", "both"])
        add_combo("coupang_mode", "쿠팡 모드", ["manual", "api"])
        add_spin("coupang_threshold_krw", "쿠팡 임계(원)", 0, 100_000_000)
        add_line("coupang_tag", "쿠팡 태그")
        # Google(Imagen) 월 지출 상한($) — ai.studio/spend에 설정한 값을 입력(0=미설정). 세션 #36
        add_dspin("google_spend_cap_usd", "Google 월 상한($, 0=미설정)", 0.0, 1000.0)
        add_line("llm_model", "LLM 모델")
        add_line("verify_url", "검증 URL")
        add_line("default_keyword_persona", "키워드 기본 페르소나(slug)")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def collect(self) -> dict[str, Any]:
        """위젯 값을 config dict로 수집(저장 전). 기존 config에 병합."""
        cfg = settings.load()
        for key, widget in self._w.items():
            if isinstance(widget, QSpinBox):
                cfg[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                cfg[key] = widget.value()
            elif isinstance(widget, QComboBox):
                cfg[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                cfg[key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                txt = widget.text().strip()
                cfg[key] = (txt or None) if key == "default_keyword_persona" else txt
        return cfg

    def save(self) -> None:
        cfg = self.collect()
        settings.save(cfg)
        # 예약이 켜져 있으면 변경된 시각·auto_mode로 작업 재등록(설정창에서 시간 조절이 실제 예약에
        # 반영되도록 + 무인 생성 wrapper footgun 방지·§0·세션 #35). 미등록이면 무동작.
        try:
            from deployer import scheduler

            new_time = str(cfg.get("schedule_time") or "").strip() or None
            scheduler.reconcile(bool(cfg.get("auto_mode", False)), new_time)
        except Exception:  # noqa: S110 — 재조정 실패가 설정 저장을 막지 않음(베스트에포트·§0)
            pass


# ─────────────────────────────────────────────────────────────
# 메인 윈도우
# ─────────────────────────────────────────────────────────────
class DashboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(_TITLE_IDLE)
        self.resize(1080, 720)
        self.worker: WorkerThread | None = None
        # 진행 표시(세션 #30 B): 작업 중 비활성화할 액션 버튼 모음 + busy 상태
        self._action_buttons: list[QPushButton] = []
        self._busy = False
        self._build_ui()
        self.refresh()

    # ---- UI 구성 ----
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

        # 통계 카드 행 + 새로고침
        cards_row = QHBoxLayout()
        self.cards: dict[str, StatCard] = {}
        for key, label in [
            ("keywords_pending", "대기 키워드"),
            ("drafts_validated", "검토 대기"),
            ("drafts_approved", "승인(발행 대기)"),
            ("articles_published", "게시 글"),
            ("categories_published", "공개 카테고리"),
        ]:
            c = StatCard(label)
            self.cards[key] = c
            cards_row.addWidget(c)
        btn_refresh = QPushButton("🔄 새로고침")
        btn_refresh.clicked.connect(self.refresh)
        cards_row.addWidget(btn_refresh)
        outer.addLayout(cards_row)

        # 상태 배너 (자동발행 설정 요약) + 무인 ON/OFF 토글 버튼(세션 #38).
        # 옛 배너는 QLabel뿐이라 '⚪ 무인 OFF' 동그라미가 라디오버튼처럼 보여도 클릭이 안 돼
        # 혼란을 줬다(주인 지적). 상단에서 바로 켜고 끄도록 실제 토글 버튼을 둔다.
        banner_row = QHBoxLayout()
        self.banner = QLabel()
        self.banner.setStyleSheet(
            "background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;"
            "padding:6px 10px;color:#1b5e20;"
        )
        banner_row.addWidget(self.banner, 1)
        self.btn_unmanned = QPushButton()
        self.btn_unmanned.setMinimumWidth(190)
        self.btn_unmanned.setToolTip("완전 무인 모드를 켜고 끕니다 (예약 시각마다 자동 생성·발행)")
        self.btn_unmanned.clicked.connect(self._on_toggle_unmanned)
        self._action_buttons.append(self.btn_unmanned)
        banner_row.addWidget(self.btn_unmanned)
        outer.addLayout(banner_row)

        # 탭
        self.tabs = QTabWidget()
        self.tab_queue = _read_only_table(["ID", "상태", "키워드/제목", "생성일"])
        self.tab_keywords = _read_only_table(["ID", "키워드", "채널", "상태", "점수", "미리선택"])
        # 발행 글 관리(세션 #37) — 완전 무인 발행의 사후 검토: 발행된 글을 목록·링크로 보고 비공개/재공개.
        self.tab_articles = _read_only_table(["제목", "상태", "발행일", "라이브 URL"])
        self.tab_articles.cellDoubleClicked.connect(lambda *_: self._on_article_open())
        # 메뉴 순서 = 운영 작업 순서 (세션 #26): 키워드(추천·추가·생성) → 발행 큐(검토·승인·발행)
        # → 카테고리·모니터링 → 설정. 시작점인 '키워드'가 맨 왼쪽.
        self.tabs.addTab(
            self._panel(
                self.tab_keywords,
                [
                    ("🎯 추천 키워드", self._on_recommend),
                    ("🆕 키워드 추가", self._on_add_keyword),
                    ("🛒 쿠팡 첨부(저장)", self._on_coupang_attach),
                    ("🛒 쿠팡 배너→글 생성", self._on_coupang_generate),
                    ("✨ 글 생성", self._on_generate),
                    ("🗑 키워드 삭제", self._on_keyword_delete),
                ],
            ),
            "키워드",
        )
        self.tabs.addTab(
            self._panel(
                self.tab_queue,
                [
                    ("👁 미리보기", self._on_preview),
                    ("✅ 승인", self._on_approve),
                    ("🚫 반려", self._on_reject),
                    ("🚀 발행(승인된 글)", self._on_publish),
                ],
            ),
            "발행 큐 (글)",
        )
        self.tabs.addTab(
            self._panel(
                self.tab_articles,
                [
                    ("🌐 라이브 보기", self._on_article_open),
                    ("🚫 비공개(내리기)", self._on_article_unpublish),
                    ("♻ 재공개", self._on_article_republish),
                ],
            ),
            "발행 글 관리",
        )
        self.tabs.addTab(self._build_monitor_tab(), "카테고리·모니터링")
        self.tabs.addTab(self._build_settings_tab(), "설정")
        outer.addWidget(self.tabs, 1)

        # 진행 상태 줄 (세션 #30 B) — 상태 라벨 + 불확정 진행바(소요시간 모름 → marquee)
        status_row = QHBoxLayout()
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet(_STATUS_IDLE_CSS)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 0~0 = 불확정(끝없이 흐르는 막대) — "작업 중"의 명확한 신호
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)  # 작업 중에만 표시
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.progress)
        outer.addLayout(status_row)

        # 실시간 로그
        log_label = QLabel("실행 로그")
        log_label.setStyleSheet("color:#555;font-size:11px;margin-top:4px;")
        outer.addWidget(log_label)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(130)
        self.log.setStyleSheet(
            "background:#1e1e1e;color:#d4d4d4;font-family:Consolas,monospace;font-size:12px;"
        )
        outer.addWidget(self.log)

    def _panel(self, table: QTableWidget, buttons: list[tuple[str, Callable[[], None]]]) -> QWidget:
        """표 위에 액션 버튼 툴바를 얹은 패널."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        for label, slot in buttons:
            b = QPushButton(label)
            b.clicked.connect(slot)
            bar.addWidget(b)
            self._action_buttons.append(b)  # 작업 중 일괄 비활성화 대상
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(table, 1)
        return w

    def _build_monitor_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.cycle_label = QLabel("무인 사이클: 기록 없음")
        self.cycle_label.setStyleSheet("padding:6px;")
        self.cycle_label.setWordWrap(True)
        lay.addWidget(self.cycle_label)
        # Google(Imagen) 추정 지출 — 결제 시점 예측(세션 #36). 새로고침 때 갱신.
        self.google_label = QLabel("Google 이미지 지출: 확인 중…")
        self.google_label.setStyleSheet("padding:6px;color:#444;")
        self.google_label.setWordWrap(True)
        lay.addWidget(self.google_label)
        # 카테고리 쿠팡 관리 (세션 #32) — 아래 표에서 카테고리 선택 후 사용
        bar = QHBoxLayout()
        for label, slot in [
            ("🛒 쿠팡 추가", self._on_category_coupang_add),
            ("🛒 쿠팡 제거", self._on_category_coupang_remove),
            ("🚀 빌드·배포", self._on_build_deploy),
        ]:
            b = QPushButton(label)
            b.clicked.connect(slot)
            bar.addWidget(b)
            self._action_buttons.append(b)
        bar.addStretch(1)
        lay.addLayout(bar)
        hint = QLabel(
            "아래 표에서 카테고리를 먼저 선택한 뒤 쿠팡을 추가/제거하세요. "
            "추가/제거 후 라이브 반영은 '🚀 빌드·배포'가 필요합니다."
        )
        hint.setStyleSheet("color:#666;font-size:11px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.tab_health = _read_only_table(["카테고리", "slug", "추천", "전체", "상태"])
        lay.addWidget(self.tab_health, 1)
        return w

    def _selected_category_slug(self) -> str | None:
        """카테고리·모니터링 표에서 선택된 행의 slug (컬럼 1)."""
        row = self.tab_health.currentRow()
        if row < 0:
            return None
        item = self.tab_health.item(row, 1)
        return item.text() if item else None

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        lay = QGridLayout(w)
        # 예약 발행 컨트롤 (Phase D)
        sched_row = QHBoxLayout()
        self.sched_label = QLabel("예약 발행: 확인 중…")
        self.sched_label.setStyleSheet("font-weight:bold;")
        b_on = QPushButton("⏰ 예약 켜기")
        b_on.clicked.connect(self._on_schedule_on)
        b_time = QPushButton("🕑 시간 변경")
        b_time.clicked.connect(self._on_schedule_time)
        b_off = QPushButton("⏹ 예약 끄기")
        b_off.clicked.connect(self._on_schedule_off)
        b_edit = QPushButton("⚙ 설정 편집")
        b_edit.clicked.connect(self._on_edit_settings)
        sched_row.addWidget(b_edit)
        sched_row.addWidget(self.sched_label)
        sched_row.addStretch(1)
        for b in (b_on, b_time, b_off):
            sched_row.addWidget(b)
        self._action_buttons += [b_edit, b_on, b_time, b_off]  # 작업 중 비활성화 대상
        sched_box = QWidget()
        sched_box.setLayout(sched_row)
        lay.addWidget(sched_box, 0, 0)

        info = QLabel(
            "예약을 켜면 매일 설정 시각에 '승인된 글'을 자동 발행합니다 "
            "(E7 준수 — 자동 승인은 하지 않음).\n"
            "전체 설정 편집 창은 Phase F에서 연결됩니다. 현재 값은 data/config.json에서 읽습니다."
        )
        info.setStyleSheet("color:#555;")
        lay.addWidget(info, 1, 0)
        self.settings_view = QLabel()
        self.settings_view.setStyleSheet(
            "font-family:Consolas,monospace;background:#fafafa;border:1px solid #eee;padding:8px;"
        )
        self.settings_view.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.settings_view, 2, 0)
        lay.setRowStretch(3, 1)
        return w

    # ---- 데이터 새로고침 ----
    def _open_conn(self) -> sqlite3.Connection | None:
        try:
            return db.connect(db.DB_PATH)
        except sqlite3.Error as e:
            self.append_log(f"[DB 오류] {e}")
            return None

    def _paint_unmanned(self, cfg: dict[str, Any] | None = None) -> None:
        """배너·무인 토글 버튼을 config만 읽어 즉시 갱신(schtasks 호출 없음 — 토글 즉각 반응용·#38)."""
        cfg = cfg if cfg is not None else settings.load()
        unmanned_on = bool(cfg.get("auto_mode"))
        unmanned = "🟢 완전 무인 ON" if unmanned_on else "⚪ 무인 OFF(사람 검수)"
        self.banner.setText(
            f"자동발행 — 하루 {cfg['publish_per_day']}편 · 예약 시각 {cfg['schedule_time']} KST "
            f"· 쿠팡 모드: {cfg['coupang_mode']} · {unmanned}"
        )
        self.btn_unmanned.setText("🟢 무인 ON — 끄기" if unmanned_on else "⚪ 무인 OFF — 켜기")
        self.btn_unmanned.setStyleSheet(
            "padding:6px 12px;font-weight:bold;border-radius:6px;"
            + (
                "background:#2e7d32;color:white;border:1px solid #1b5e20;"
                if unmanned_on
                else "background:#f5f5f5;color:#444;border:1px solid #bbb;"
            )
        )

    def refresh(self) -> None:
        cfg = settings.load()
        self._paint_unmanned(cfg)
        self.settings_view.setText(json.dumps(cfg, ensure_ascii=False, indent=2))
        self._refresh_schedule_label()

        conn = self._open_conn()
        if conn is None:
            return
        try:
            self._has_schema(conn)
            stats = queries.dashboard_stats(conn)
            for key, card in self.cards.items():
                card.set_value(stats.get(key, 0))
            self._fill_queue(queries.list_queue(conn))
            self._fill_keywords(queries.list_keywords(conn))
            self._fill_articles(queries.list_articles(conn))
            self._fill_health(conn)
        finally:
            conn.close()

    def _on_toggle_unmanned(self) -> None:
        """상단 배너의 무인 ON/OFF 토글(세션 #38). 켤 때 확인창 + 예약 작업 재등록.

        설정 다이얼로그의 'auto_mode' 체크와 같은 config 키를 쓰므로 한 곳만 바꿔도 동기화된다.
        """
        cfg = settings.load()
        turning_on = not bool(cfg.get("auto_mode", False))
        if turning_on:
            minp = int(cfg.get("auto_approve_min_published", 5) or 0)
            gate = (
                f"처음 {minp}편은 사람이 승인해야 발행되고, 그 뒤부터 완전 자동입니다."
                if minp > 0
                else "첫 글부터 사람 승인 없이 자동 발행됩니다(검수 편수 0)."
            )
            resp = QMessageBox.question(
                self,
                "완전 무인 켜기",
                "완전 무인 모드를 켤까요?\n\n"
                "· 예약 시각마다 등록된 키워드로 글을 자동 생성·발행합니다.\n"
                f"· {gate}\n"
                "· 같은 버튼을 다시 누르면 끕니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
        cfg["auto_mode"] = turning_on
        settings.save(cfg)
        # ★배너/버튼은 config만 읽어 즉시 갱신(schtasks 없음) — 토글이 바로 반응한다.
        self._paint_unmanned(cfg)
        self.append_log(f"[OK] 완전 무인 {'ON' if turning_on else 'OFF'}")
        # 예약 재등록(schtasks query+create)은 이 환경에서 호출당 수초 → 메인 스레드에서 돌리면
        # UI가 9초 얼어붙는다(#38 주인 지적). 백그라운드 스레드로 옮겨 UI 프리징을 없앤다.
        new_time = str(cfg.get("schedule_time") or "").strip() or None

        def _reconcile_task() -> Any:
            from deployer import scheduler

            r = scheduler.reconcile(turning_on, new_time)  # 미등록이면 None(무동작)
            if isinstance(r, tuple):
                print(f"[예약] {r[1]}")
            elif r is None:
                print("[예약] 예약 미등록 — '예약 켜기'를 누르면 이 모드로 등록됩니다")
            return r

        self.run_task(_reconcile_task, label="예약 재등록")

    def _has_schema(self, conn: sqlite3.Connection) -> None:
        """스키마 없으면 안내(무인 환경 친화)."""
        try:
            conn.execute("SELECT 1 FROM schema_version LIMIT 1")
        except sqlite3.OperationalError:
            self.append_log(
                "[안내] DB 스키마가 없습니다. 터미널에서 `python -m cli db migrate` 후 새로고침하세요."
            )

    def _fill_queue(self, rows: list[dict[str, Any]]) -> None:
        self.tab_queue.setRowCount(len(rows))
        for i, r in enumerate(rows):
            title = r.get("keyword") or r.get("working_title") or f"(제목 없음) #{r['id']}"
            st = str(r.get("status") or "")
            self.tab_queue.setItem(i, 0, _cell(str(r["id"])))
            self.tab_queue.setItem(i, 1, _cell(_status_label(st), st))
            self.tab_queue.setItem(i, 2, _cell(str(title)))
            self.tab_queue.setItem(i, 3, _cell(str(r.get("created_at") or "")))

    def _fill_articles(self, rows: list[dict[str, Any]]) -> None:
        """발행 글 관리 표 채우기(세션 #37). slug는 제목 셀 데이터(UserRole)에 보관 — 작업 시 사용."""
        self.tab_articles.setRowCount(len(rows))
        for i, r in enumerate(rows):
            st = str(r.get("status") or "")
            title = r.get("title") or f"(제목 없음) #{r['id']}"
            title_cell = _cell(str(title))
            title_cell.setData(Qt.UserRole, str(r.get("slug") or ""))
            self.tab_articles.setItem(i, 0, title_cell)
            self.tab_articles.setItem(i, 1, _cell(_status_label(st), st))
            self.tab_articles.setItem(i, 2, _cell(str(r.get("published_at") or "—")))
            self.tab_articles.setItem(i, 3, _cell(str(r.get("live_url") or "")))

    def _fill_keywords(self, rows: list[dict[str, Any]]) -> None:
        self.tab_keywords.setRowCount(len(rows))
        for i, r in enumerate(rows):
            st = str(r.get("status") or "")
            n_products = 0
            tp = r.get("target_products")
            if tp:
                try:
                    parsed = json.loads(tp)
                    n_products = len(parsed) if isinstance(parsed, list) else 0
                except (json.JSONDecodeError, TypeError):
                    n_products = 0
            self.tab_keywords.setItem(i, 0, _cell(str(r["id"])))
            self.tab_keywords.setItem(i, 1, _cell(str(r.get("keyword") or "")))
            self.tab_keywords.setItem(i, 2, _cell(str(r.get("channel") or "")))
            self.tab_keywords.setItem(i, 3, _cell(_status_label(st), st))
            self.tab_keywords.setItem(i, 4, _cell(str(r.get("score") or 0)))
            self.tab_keywords.setItem(i, 5, _cell(str(n_products)))

    def _fill_health(self, conn: sqlite3.Connection) -> None:
        cycle = queries.load_last_cycle(db.DB_PATH.parent / "refresh_cycle_last.json")
        if cycle:
            ks = cycle.get("killswitched") or []
            self.cycle_label.setText(
                f"무인 사이클 — 실행 {cycle.get('ran_at', '?')} · 공개 "
                f"{len(cycle.get('published', []))}개 · 새로고침 성공 {cycle.get('refresh_ok', 0)}"
                f"/실패 {cycle.get('refresh_fail', 0)}"
                + (f" · ⚠ 자가복원 {len(ks)}건" if ks else "")
            )
        else:
            self.cycle_label.setText("무인 사이클: 기록 없음 (refresh-cycle 실행 후 표시)")
        self._fill_google_usage(conn)
        health = queries.category_health(conn)
        self.tab_health.setRowCount(len(health))
        for i, h in enumerate(health):
            mark = "⚠ 미달" if h.get("flagged") else "✓ 정상"
            self.tab_health.setItem(i, 0, _cell(str(h.get("name_ko") or "")))
            self.tab_health.setItem(i, 1, _cell(str(h.get("slug") or "")))
            self.tab_health.setItem(i, 2, _cell(str(h.get("featured") or 0)))
            self.tab_health.setItem(i, 3, _cell(str(h.get("total") or 0)))
            self.tab_health.setItem(
                i, 4, _cell(mark, "failed" if h.get("flagged") else "published")
            )

    def _fill_google_usage(self, conn: sqlite3.Connection) -> None:
        """Google(Imagen) 추정 지출 라벨 갱신 — 결제 시점 예측(세션 #36).

        실제 구글 청구액이 아니라 우리 호출수에 단가를 곱한 추정('추정' 명시). 429/상한 임박 시 색상 경고.
        """
        gu = queries.google_usage(conn)
        cap, used = gu["cap_usd"], gu["used_usd"]
        msg = f"Google 이미지(추정): 이번 달 {gu['images']}장 · 약 ${used:.2f}"
        if cap > 0 and gu["pct"] is not None:
            msg += f" / 상한 ${cap:.2f} ({gu['pct']:.0f}%)"
        else:
            msg += " · 상한 미설정(설정에서 입력)"
        css = "padding:6px;color:#444;"
        if gu["last_429_at"]:
            msg += f"  ⛔ 한도초과 발생({str(gu['last_429_at'])[:10]}) — ai.studio/spend에서 상향"
            css = "padding:6px;color:#c0392b;font-weight:bold;"
        elif gu["near_or_over"]:
            msg += "  ⚠ 상한 임박 — 곧 결제 필요"
            css = "padding:6px;color:#e67e22;font-weight:bold;"
        self.google_label.setText(msg)
        self.google_label.setStyleSheet(css)

    # ---- 로그/작업 ----
    def append_log(self, line: str) -> None:
        self.log.append(line)
        self.log.ensureCursorVisible()

    def _set_busy(self, label: str) -> None:
        """작업 시작 — 진행 표시 켜기(진행바·상태 라벨·대기 커서·버튼 비활성·타이틀)."""
        self._busy = True
        self.status_label.setText(f"⏳ {label} 진행 중…")
        self.status_label.setStyleSheet(_STATUS_BUSY_CSS)
        self.progress.setVisible(True)
        self.setWindowTitle(f"⏳ {label}… — {_TITLE_IDLE}")
        for b in self._action_buttons:
            b.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def _set_done(self, outcome: str, label: str) -> None:
        """작업 종료 — 진행 표시 끄고 완료/경고/실패 표시 + 버튼·커서·타이틀 원복.

        outcome: 'ok'(성공) / 'warn'(완료했으나 코드≠0) / 'fail'(예외). 색으로 즉시 구분.
        """
        if not self._busy:  # 이중 호출 방어 — 대기 커서 스택 균형 유지
            return
        self._busy = False
        self.progress.setVisible(False)
        QApplication.restoreOverrideCursor()
        for b in self._action_buttons:
            b.setEnabled(True)
        self.setWindowTitle(_TITLE_IDLE)
        if outcome == "fail":
            self.status_label.setText(f"✗ {label} 실패 — 실행 로그 확인")
            self.status_label.setStyleSheet(_STATUS_FAIL_CSS)
        elif outcome == "warn":
            self.status_label.setText(f"⚠ {label} 완료(경고) — 실행 로그 확인")
            self.status_label.setStyleSheet(_STATUS_WARN_CSS)
        else:
            self.status_label.setText(f"✓ {label} 완료")
            self.status_label.setStyleSheet(_STATUS_OK_CSS)

    def run_task(
        self,
        fn: Callable[[], Any],
        on_done: Callable[[bool, Any], None] | None = None,
        *,
        label: str = "작업",
    ) -> None:
        """백그라운드 작업 실행(Phase C~ 액션 공용). 동시에 하나만.

        시작~완료를 진행 표시로 가시화(세션 #30 B): label이 상태 라벨/타이틀에 표시되고,
        작업 중 액션 버튼이 비활성·진행바가 흐르며, 끝나면 완료/경고/실패가 색으로 남는다.
        주인 반복지적('생성 1~2분 무표시 → 끝난지 모름')의 근본 대책.
        """
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(
                self, "실행 중", "다른 작업이 진행 중입니다. 잠시 후 다시 시도하세요."
            )
            return
        self.worker = WorkerThread(fn)
        self.worker.log.connect(self.append_log)

        def _finish(ok: bool, result: Any) -> None:
            if not ok:
                self.append_log(f"[오류] {result}")
                outcome = "fail"
            elif isinstance(result, int) and result != 0:
                self.append_log(f"[경고] 명령이 코드 {result}로 종료 — 위 로그를 확인하세요")
                outcome = "warn"
            else:
                outcome = "ok"
            self._set_done(outcome, label)  # 진행 표시 끄기 + 완료/경고/실패 (UI 원복 후 모달 표시)
            self.refresh()
            if not ok:
                QMessageBox.warning(self, "작업 실패", str(result).splitlines()[0])
            if on_done:
                on_done(ok, result)

        self.worker.done.connect(_finish)
        self._set_busy(label)  # 진행 표시 켜기
        self.worker.start()

    # ---- 액션 (Phase C) — 기존 CLI 명령을 백그라운드로 실행, 로그 스트리밍 ----
    def _selected_id(self, table: QTableWidget) -> int | None:
        items = table.selectedItems()
        if not items:
            return None
        id_item = table.item(items[0].row(), 0)
        try:
            return int(id_item.text()) if id_item else None
        except ValueError:
            return None

    def _selected_or_top(self, table: QTableWidget) -> int | None:
        """선택된 행 id, 없으면 맨 위(0행) id — '쓸데없는 선택 클릭' 제거. 표가 비면 None."""
        did = self._selected_id(table)
        if did is not None:
            return did
        if table.rowCount() <= 0:
            return None
        item = table.item(0, 0)
        try:
            return int(item.text()) if item else None
        except ValueError:
            return None

    def _selected_article_slug(self) -> str | None:
        """발행 글 관리 표에서 선택(없으면 맨 위) 행의 slug — 제목 셀 데이터(UserRole)에서 읽음."""
        items = self.tab_articles.selectedItems()
        if items:
            row = items[0].row()
        elif self.tab_articles.rowCount() > 0:
            row = 0
        else:
            return None
        cell = self.tab_articles.item(row, 0)
        slug = cell.data(Qt.UserRole) if cell else None
        return str(slug) if slug else None

    def _on_recommend(self) -> None:
        """추천 키워드 생성 → 선택 창 → 큐 추가. 정의된 선정 방식(keyword_research)을 SEO 씨앗에 적용."""
        seed, ok = QInputDialog.getText(
            self, "추천 키워드", "추천 주제어 (비우면 기존 카테고리 기반 자동 추천):"
        )
        if not ok:
            return
        custom = seed.strip() or None

        def task() -> list[dict[str, Any]]:
            from common import config
            from writer import keyword_recommender as kr

            config.load_secrets()  # 네이버 검색광고 키
            print("[추천] 네이버 연관검색어 조회 중…")
            conn = db.connect(db.DB_PATH)
            try:
                recs = kr.recommend(conn, custom_seed=custom, limit=30, live=True)
            finally:
                conn.close()
            print(f"[추천] 후보 {len(recs)}건")
            return recs

        self.run_task(task, on_done=self._after_recommend, label="추천 키워드 조회")

    def _after_recommend(self, ok: bool, result: Any) -> None:
        if not ok:
            return  # 오류는 run_task가 이미 로그/경고
        if not isinstance(result, list) or not result:
            QMessageBox.information(
                self,
                "추천 없음",
                "추천 키워드가 없습니다. 주제어를 바꾸거나 네이버 키를 확인하세요.",
            )
            return
        dlg = RecommendDialog(result, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        chosen = dlg.chosen_list()
        if not chosen:
            return

        def add_task() -> int:
            import cli

            n = 0
            for rec in chosen:
                kw = str(rec["keyword"])
                channel = str(rec.get("channel") or "ali")
                vol = int(rec.get("volume") or 0)
                note = f"추천(검색량 {vol}·씨앗 {rec.get('seed')})"
                cli.cmd_keyword_add(
                    argparse.Namespace(
                        keyword=kw,
                        channel=channel,
                        slug=None,
                        budget_min=None,
                        budget_max=None,
                        note=note,
                        score=float(vol),
                    )
                )
                print(f"[추천] 추가: {kw} (검색량 {vol})")
                n += 1
            print(f"[추천] {n}개 키워드 일괄 추가 완료")
            return 0

        self.run_task(add_task, label=f"키워드 {len(chosen)}개 추가")

    def _on_add_keyword(self) -> None:
        text, ok = QInputDialog.getText(
            self, "키워드 추가", "키워드/주제 (예: 자취생 전자레인지 추천):"
        )
        if not ok or not text.strip():
            return
        opts = ["ali", "coupang", "both"]
        default_ch = str(settings.get("default_channel", "ali"))
        idx = opts.index(default_ch) if default_ch in opts else 0
        channel, ok2 = QInputDialog.getItem(self, "채널 선택", "제휴 채널:", opts, idx, False)
        if not ok2:
            return
        kw = text.strip()

        def task() -> int:
            import cli

            return cli.cmd_keyword_add(
                argparse.Namespace(
                    keyword=kw,
                    channel=channel,
                    slug=None,
                    budget_min=None,
                    budget_max=None,
                    note=None,
                    score=0.0,
                )
            )

        self.run_task(task, label="키워드 추가")

    def _on_keyword_delete(self) -> None:
        """선택한 키워드 삭제 (연결 미발행 글 동반). 발행된 글 있으면 차단(라이브 보호)."""
        kid = self._selected_id(self.tab_keywords)
        if kid is None:
            QMessageBox.information(self, "키워드 선택", "삭제할 키워드를 먼저 선택하세요.")
            return
        row = self.tab_keywords.currentRow()
        kw_item = self.tab_keywords.item(row, 1) if row >= 0 else None
        kw = kw_item.text() if kw_item else str(kid)
        resp = QMessageBox.question(
            self,
            "키워드 삭제",
            f"키워드 #{kid} '{kw}'을(를) 삭제할까요?\n\n"
            "· 연결된 미발행 글(검토 대기 등)도 함께 삭제됩니다.\n"
            "· 발행된 글이 있으면 삭제되지 않습니다(라이브 보호).\n"
            "· 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            return cli.cmd_keyword_delete(argparse.Namespace(id=kid))

        self.run_task(task, label="키워드 삭제")

    def _on_generate(self) -> None:
        """글 생성. 줄을 선택했으면 그 키워드, 아니면 자동 선정(대기 큐 우선→없으면 추천·추가)."""
        kid = self._selected_id(self.tab_keywords)
        if kid is not None:
            self._confirm_and_generate(kid, label=f"키워드 #{kid}")
            return

        # 선택 없음 → 키워드 자동 선정 (정의된 방식). 네트워크 가능 → 백그라운드.
        def task() -> dict[str, Any] | None:
            from common import config
            from writer import keyword_recommender as kr

            config.load_secrets()  # 추천 시 네이버 키
            print("[자동] 키워드 선정 중 (대기 큐 우선 · 없으면 추천)…")
            conn = db.connect(db.DB_PATH)
            try:
                return kr.auto_pick_keyword(conn, live=True)
            finally:
                conn.close()

        self.run_task(task, on_done=self._after_auto_pick, label="키워드 자동 선정")

    def _after_auto_pick(self, ok: bool, result: Any) -> None:
        if not ok:
            return  # 오류는 run_task가 로그/경고
        if not isinstance(result, dict) or not result.get("keyword_id"):
            QMessageBox.information(
                self,
                "키워드 없음",
                "자동 선정할 키워드가 없습니다. '🎯 추천 키워드'로 추가하거나 '🆕 키워드 추가'를 쓰세요.",
            )
            return
        src = "대기 큐" if result.get("source") == "queue" else "자동 추천"
        self._confirm_and_generate(
            int(result["keyword_id"]), label=f"{src} 키워드 '{result.get('keyword')}'"
        )

    def _confirm_and_generate(self, kid: int, *, label: str) -> None:
        resp = QMessageBox.question(
            self,
            "글 생성",
            f"{label}(으)로 실제 글을 생성할까요?\n\n"
            "· 본문 생성 LLM 비용이 발생합니다.\n"
            "· 결과는 '검토 대기' 상태로 들어가며 자동 발행되지 않습니다(E7).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            return cli.cmd_keyword_generate(argparse.Namespace(id=kid, page_size=20, dry_run=False))

        self.run_task(task, label="글 생성")

    def _on_coupang_attach(self) -> None:
        """선택한 대기 키워드에 쿠팡 배너를 저장만 (생성 안 함·pending 유지·세션 #29 naver_blog 흐름).

        스케줄러(auto-cycle)나 '글 생성' 시 이 저장된 쿠팡으로 하이브리드(쿠팡+알리) 글이 만들어진다.
        """
        row = self.tab_keywords.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "키워드 선택", "쿠팡을 저장할 대기 키워드를 먼저 선택하세요."
            )
            return
        kid_item = self.tab_keywords.item(row, 0)
        kw_item = self.tab_keywords.item(row, 1)
        if kid_item is None or kw_item is None:
            return
        try:
            kid = int(kid_item.text())
        except ValueError:
            return
        keyword = kw_item.text()
        dlg = CoupangProductDialog(keyword, self, attach_mode=True)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        if not v["banner"] and not (v["name"] and v["url"]):
            QMessageBox.warning(
                self, "입력 필요", "쿠팡 배너 HTML을 붙여넣거나 상품명 + 파트너스 URL을 입력하세요."
            )
            return

        def task() -> int:
            from collector import coupang_manual

            conn = db.connect(db.DB_PATH)
            try:
                prods = coupang_manual.products_from_banners(
                    v["banner"],
                    name=v["name"],
                    url=v["url"],
                    price_krw=v["price"],
                    affiliate_tag=settings.get("coupang_tag"),
                )
                if not prods:
                    print("[쿠팡] 첨부할 상품 없음 — 배너 또는 상품명+URL 확인")
                    return 1
                for p in prods:
                    coupang_manual.add_to_keyword(conn, kid, p)
                # 쿠팡+알리 하이브리드 대상으로 (저장 후 생성 시 알리도 결합)
                conn.execute("UPDATE keyword_queue SET channel='both' WHERE id=?", (kid,))
                conn.commit()
                print(
                    f"[쿠팡] {len(prods)}개 저장 → 키워드 #{kid} {keyword!r} "
                    "(대기 유지 · 생성은 스케줄러/'글 생성' 시)"
                )
            finally:
                conn.close()
            return 0

        self.run_task(task, label="쿠팡 첨부")

    def _on_coupang_generate(self) -> None:
        """쿠팡 배너 붙여넣기 → 그 키워드로 하이브리드 글 생성 (원팝업·세션 #28 PartB)."""
        prefill = ""
        row = self.tab_keywords.currentRow()
        if row >= 0:
            item = self.tab_keywords.item(row, 1)  # 키워드 컬럼
            if item is not None:
                prefill = item.text()
        dlg = CoupangProductDialog(prefill, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        if not v["keyword"]:
            QMessageBox.warning(self, "입력 필요", "키워드(주제)를 입력하세요.")
            return
        if not v["banner"] and not (v["name"] and v["url"]):
            QMessageBox.warning(
                self, "입력 필요", "쿠팡 배너 HTML을 붙여넣거나 상품명 + 파트너스 URL을 입력하세요."
            )
            return

        def task() -> int:
            import cli
            from collector import coupang_manual
            from common import config
            from writer import keyword_queue as kq

            config.load_secrets()  # 알리 데이터 결합(+네이버)
            conn = db.connect(db.DB_PATH)
            try:
                kid = kq.get_or_create(conn, v["keyword"], channel="both")
                prods = coupang_manual.products_from_banners(
                    v["banner"],
                    name=v["name"],
                    url=v["url"],
                    price_krw=v["price"],
                    affiliate_tag=settings.get("coupang_tag"),
                )
                for p in prods:
                    coupang_manual.add_to_keyword(conn, kid, p)
                print(f"[쿠팡] {len(prods)}개 첨부 → 키워드 #{kid} {v['keyword']!r}")
            finally:
                conn.close()
            return cli.cmd_keyword_generate(argparse.Namespace(id=kid, page_size=20, dry_run=False))

        self.run_task(task, label="쿠팡 하이브리드 글 생성")

    def _on_category_coupang_add(self) -> None:
        """선택한 카테고리의 쿠팡 운영자추천 zone에 쿠팡 배너 상품 추가 (여러 개 가능·세션 #32)."""
        slug = self._selected_category_slug()
        if not slug:
            QMessageBox.information(
                self, "카테고리 선택", "쿠팡을 추가할 카테고리를 표에서 먼저 선택하세요."
            )
            return
        dlg = CoupangProductDialog(slug, self, attach_mode=True)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        if not v["banner"]:
            QMessageBox.warning(
                self, "배너 필요", "쿠팡 공식 배너 HTML(<a><img>)을 붙여넣으세요 (여러 개 가능)."
            )
            return

        def task() -> int:
            import cli

            return cli.cmd_category_coupang_add(argparse.Namespace(slug=slug, banner=v["banner"]))

        self.run_task(task, label="카테고리 쿠팡 추가")

    def _on_category_coupang_remove(self) -> None:
        """선택한 카테고리의 쿠팡 상품 목록에서 하나를 골라 링크 해제."""
        slug = self._selected_category_slug()
        if not slug:
            QMessageBox.information(
                self, "카테고리 선택", "쿠팡을 제거할 카테고리를 표에서 먼저 선택하세요."
            )
            return
        from collector import category_coupang

        conn = db.connect(db.DB_PATH)
        try:
            rows = category_coupang.list_coupang(conn, slug)
        finally:
            conn.close()
        if not rows:
            QMessageBox.information(self, "쿠팡 없음", f"카테고리 '{slug}'에 쿠팡 상품이 없습니다.")
            return
        labels = [f"#{r['id']} {r['name']}" for r in rows]
        choice, ok = QInputDialog.getItem(self, "쿠팡 제거", "제거할 상품:", labels, 0, False)
        if not ok:
            return
        try:
            pid = int(choice.split(maxsplit=1)[0].lstrip("#"))
        except (ValueError, IndexError):
            return

        def task() -> int:
            import cli

            return cli.cmd_category_coupang_remove(argparse.Namespace(slug=slug, product_id=pid))

        self.run_task(task, label="카테고리 쿠팡 제거")

    def _on_build_deploy(self) -> None:
        """현재 운영 DB로 빌드 → build/site 커밋 → main push (CI가 라이브 반영). 외부 게시(§2-마 확인)."""
        resp = QMessageBox.question(
            self,
            "빌드·배포",
            "현재 운영 DB 상태로 사이트를 빌드해 라이브(honsallim.com)에 배포할까요?\n\n"
            "· 카테고리·쿠팡 등 변경이 실제 사이트에 반영됩니다(외부 게시).\n"
            "· GitHub Actions가 약 1~2분 후 배포합니다.\n"
            "· 운영 폴더가 최신(main) 상태여야 합니다 — 아니면 push 실패로 안내됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            return cli.cmd_build_deploy(argparse.Namespace(dry_run=False, message=None))

        self.run_task(task, label="빌드·배포")

    # ---- 발행 글 사후 관리 (세션 #37) — 무인 발행 후 검토·내리기·되돌리기 ----
    def _on_article_open(self) -> None:
        """선택한 발행 글의 라이브 페이지를 브라우저로 연다(행 더블클릭도 동일)."""
        slug = self._selected_article_slug()
        if not slug:
            QMessageBox.information(self, "글 선택", "라이브로 열 글을 표에서 선택하세요.")
            return
        import webbrowser

        webbrowser.open(f"{queries.SITE_ORIGIN}/articles/{slug}/")
        self.append_log(f"[발행글] 라이브 열기: {queries.SITE_ORIGIN}/articles/{slug}/")

    def _on_article_unpublish(self) -> None:
        """선택한 발행 글 → 비공개 + 빌드·배포 (라이브·사이트맵에서 제거). 외부 게시(§2-라 확인)."""
        slug = self._selected_article_slug()
        if not slug:
            QMessageBox.information(self, "글 선택", "비공개로 내릴 글을 표에서 선택하세요.")
            return
        resp = QMessageBox.question(
            self,
            "글 비공개(내리기)",
            f"글 '{slug}'을(를) 라이브에서 내릴까요?\n\n"
            "· 비공개 처리 후 빌드·배포로 honsallim.com에서 사라집니다(외부 게시).\n"
            "· 사이트맵에서도 제외됩니다(색인 제거 신호).\n"
            "· '재공개'로 언제든 되돌릴 수 있습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            rc = cli.cmd_unpublish_article(
                argparse.Namespace(slug=slug, note="대시보드 사후검토 비공개")
            )
            if rc != 0:
                return rc
            print("[발행글] 비공개 완료 — 라이브 반영 위해 빌드·배포 진행")
            return cli.cmd_build_deploy(argparse.Namespace(dry_run=False, message=None))

        self.run_task(task, label="글 비공개+배포")

    def _on_article_republish(self) -> None:
        """선택한 비공개 글 → 재공개 + 빌드·배포 (라이브 복원). 외부 게시(§2-라 확인)."""
        slug = self._selected_article_slug()
        if not slug:
            QMessageBox.information(self, "글 선택", "재공개할 글을 표에서 선택하세요.")
            return
        resp = QMessageBox.question(
            self,
            "글 재공개",
            f"글 '{slug}'을(를) 다시 공개할까요?\n\n"
            "· 재공개 후 빌드·배포로 honsallim.com에 다시 올라갑니다(외부 게시).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            rc = cli.cmd_republish_article(argparse.Namespace(slug=slug))
            if rc != 0:
                return rc
            print("[발행글] 재공개 완료 — 라이브 반영 위해 빌드·배포 진행")
            return cli.cmd_build_deploy(argparse.Namespace(dry_run=False, message=None))

        self.run_task(task, label="글 재공개+배포")

    def _on_preview(self) -> None:
        # 선택(없으면 맨 위) 발행 큐 글 → 빌드 후 그 글 상세로 바로 이동 (검토 동선·§2-마, 세션 #29)
        did = self._selected_or_top(self.tab_queue)

        def task() -> int:
            import webbrowser

            import cli

            rc = cli.cmd_build(
                argparse.Namespace(manifest=None, full=False, preview=True, save_empty=False)
            )
            preview = db.PROJECT_ROOT / "build" / "preview"
            target = preview / "index.html"
            if did is not None:  # 선택한 글의 상세 페이지로 직접 이동(없으면 홈)
                conn = db.connect(db.DB_PATH)
                try:
                    srow = conn.execute(
                        "SELECT s.slug FROM drafts d JOIN scenarios s ON s.id = d.scenario_id "
                        "WHERE d.id = ?",
                        (did,),
                    ).fetchone()
                finally:
                    conn.close()
                if srow is not None:
                    art = preview / "articles" / str(srow[0]) / "index.html"
                    if art.exists():
                        target = art
            if target.exists():
                # file:// 대신 로컬 HTTP로 — 절대경로 /static·이미지가 정상 해석돼 라이브와 동일(세션 #34)
                from dashboard import preview_server

                url = preview_server.url_for(preview, target)
                webbrowser.open(url)
                print(f"[OK] 미리보기 열기: {url} (로컬 HTTP — 스타일·이미지 정상)")
            else:
                print(f"[WARN] 미리보기 파일 없음: {target} (먼저 글을 생성하세요)")
            return rc

        self.run_task(task, label="미리보기 빌드")

    def _on_approve(self) -> None:
        did = self._selected_or_top(self.tab_queue)  # 선택 없으면 맨 위 글
        if did is None:
            QMessageBox.information(self, "글 없음", "발행 큐에 승인할 글이 없습니다.")
            return

        def task() -> int:
            import cli

            return cli.cmd_approve(argparse.Namespace(draft=did, note="dashboard 승인"))

        self.run_task(task, label="승인")

    def _on_reject(self) -> None:
        did = self._selected_or_top(self.tab_queue)  # 선택 없으면 맨 위 글
        if did is None:
            QMessageBox.information(self, "글 없음", "발행 큐에 반려할 글이 없습니다.")
            return
        if (
            QMessageBox.question(
                self,
                "반려",
                f"draft #{did}를 반려할까요?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        def task() -> int:
            import cli

            return cli.cmd_reject(argparse.Namespace(draft=did, note="dashboard 반려"))

        self.run_task(task, label="반려")

    # ---- 발행·예약 (Phase D) ----
    def _refresh_schedule_label(self) -> None:
        try:
            from deployer import scheduler

            t = scheduler.query_scheduled_time()
            self.sched_label.setText(
                f"예약 발행: 매일 {t[0]:02d}:{t[1]:02d} 등록됨"
                if t
                else "예약 발행: 미등록 (수동 발행만)"
            )
        except Exception:  # 조회 실패는 UI에 표시만(크래시 방지)
            self.sched_label.setText("예약 발행: 확인 불가")

    def _on_publish(self) -> None:
        resp = QMessageBox.warning(
            self,
            "발행 (외부 게시)",
            "승인된 글을 실제로 사이트에 발행할까요?\n\n"
            "· 승인된 큐에서 설정 편수만큼 게시됩니다.\n"
            "· git push로 honsallim.com에 배포됩니다(되돌리기 번거로움).\n"
            "· 메인 체크아웃에서 실행해야 합니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        def task() -> int:
            import cli

            return cli.cmd_publish_queue(
                argparse.Namespace(count=None, no_deploy=False, dry_run=False)
            )

        self.run_task(task, label="발행")

    def _on_schedule_on(self) -> None:
        cfg = settings.load()
        t = cfg.get("schedule_time", "11:00")
        full_auto = bool(cfg.get("auto_mode", False))
        what = (
            "키워드 자동선정→글 생성→자동승인→발행까지 전부(완전 무인)"
            if full_auto
            else "승인된 글만 발행"
        )
        if (
            QMessageBox.question(
                self,
                "예약 발행 켜기",
                f"매일 {t}에 {what} 하도록 등록할까요?\n(Windows 작업 스케줄러)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        def task() -> int:
            import cli

            return cli.cmd_schedule(argparse.Namespace(schedule_action="set", time=None))

        self.run_task(task, label="예약 켜기")

    def _on_schedule_time(self) -> None:
        cur = str(settings.load().get("schedule_time", "11:00"))
        text, ok = QInputDialog.getText(
            self, "예약 시각 변경", "발행 시각 HH:MM (24시간):", text=cur
        )
        if not ok or not text.strip():
            return
        new_time = text.strip()

        def task() -> int:
            import cli

            return cli.cmd_schedule(argparse.Namespace(schedule_action="set", time=new_time))

        self.run_task(task, label="예약 시각 변경")

    def _on_schedule_off(self) -> None:
        if (
            QMessageBox.question(
                self,
                "예약 발행 끄기",
                "예약 발행 작업을 해제할까요? (이후 발행은 수동으로만)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        def task() -> int:
            import cli

            return cli.cmd_schedule(argparse.Namespace(schedule_action="off", time=None))

        self.run_task(task, label="예약 끄기")

    def _on_edit_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.save()
            self.append_log("[OK] 설정 저장됨 (data/config.json)")
            self.refresh()


def main() -> int:
    # 대기 마이그레이션 자동 적용(멱등·세션 #34) — 기존 운영 DB에 새 스키마(예: 008 structured_json)를
    # 무명령으로 반영(§2-가 비개발자 배려·§0 자가복원). DB가 아예 없으면 건너뜀(seed 포함 안내 UX 유지).
    try:
        from common import db as _db

        if _db.DB_PATH.exists():
            applied = _db.migrate(_db.DB_PATH)
            if applied:
                print(
                    f"[migrate] 대기 마이그레이션 {len(applied)}개 자동 적용 (v{applied[-1].version})"
                )
    except Exception as exc:  # 마이그레이션 실패가 대시보드 기동을 막지 않음(best-effort)
        print(f"[migrate] 자동 마이그레이션 건너뜀: {exc}")

    app = QApplication(sys.argv)
    win = DashboardWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
