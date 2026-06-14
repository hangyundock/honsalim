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
    """쿠팡 파트너스 딥링크/위젯 수동 입력 폼. CDN 이미지 미사용(함정 #3)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("쿠팡 상품 추가 (수동)")
        self.resize(460, 280)
        form = QFormLayout(self)
        self.name = QLineEdit()
        self.url = QLineEdit()
        self.url.setPlaceholderText("쿠팡 파트너스 딥링크 (필수)")
        self.price = QLineEdit()
        self.price.setPlaceholderText("숫자만 (선택)")
        self.widget = QTextEdit()
        self.widget.setPlaceholderText("공식 위젯 HTML (선택)")
        self.widget.setMaximumHeight(70)
        form.addRow("상품명*", self.name)
        form.addRow("파트너스 URL*", self.url)
        form.addRow("가격(원)", self.price)
        form.addRow("위젯 HTML", self.widget)
        note = QLabel("⚠ 쿠팡 상품 이미지(CDN) 다운로드 금지 — 공식 위젯/텍스트만 (함정 #3)")
        note.setStyleSheet("color:#a50e0e;font-size:11px;")
        note.setWordWrap(True)
        form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict[str, Any]:
        price_text = self.price.text().strip()
        return {
            "name": self.name.text().strip(),
            "url": self.url.text().strip(),
            "price": int(price_text) if price_text.isdigit() else None,
            "widget": self.widget.toPlainText().strip() or None,
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
        self._choice: dict[str, Any] | None = None
        lay = QVBoxLayout(self)
        info = QLabel(
            "검색량순 추천입니다. 한 행을 선택해 추가하거나, '1순위 자동 추가'를 누르세요.\n"
            "(월검색량=네이버 실데이터 · '캐시'=검색량 미상 보조키워드)"
        )
        info.setStyleSheet("color:#555;")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.table = _read_only_table(["키워드", "월검색량", "경쟁도", "씨앗", "출처"])
        self.table.setRowCount(len(recs))
        for i, r in enumerate(recs):
            vol = f"{r['volume']:,}" if r.get("volume") is not None else "—"
            src = "네이버" if r.get("source") == "naver" else "캐시"
            self.table.setItem(i, 0, _cell(str(r.get("keyword") or "")))
            self.table.setItem(i, 1, _cell(vol))
            self.table.setItem(i, 2, _cell(str(r.get("competition") or "")))
            self.table.setItem(i, 3, _cell(str(r.get("seed") or "")))
            self.table.setItem(i, 4, _cell(src))
        if recs:
            self.table.selectRow(0)
        lay.addWidget(self.table, 1)
        bar = QHBoxLayout()
        b_sel = QPushButton("✅ 선택한 키워드 추가")
        b_sel.clicked.connect(self._choose_selected)
        b_top = QPushButton("⭐ 1순위 자동 추가")
        b_top.clicked.connect(self._choose_top)
        b_cancel = QPushButton("취소")
        b_cancel.clicked.connect(self.reject)
        bar.addWidget(b_sel)
        bar.addWidget(b_top)
        bar.addStretch(1)
        bar.addWidget(b_cancel)
        lay.addLayout(bar)

    def _choose_selected(self) -> None:
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self.recs):
            QMessageBox.information(
                self, "선택 필요", "키워드를 한 행 선택하거나 '1순위 자동 추가'를 누르세요."
            )
            return
        self._choice = self.recs[idx]
        self.accept()

    def _choose_top(self) -> None:
        if self.recs:
            self._choice = self.recs[0]
        self.accept()

    def chosen(self) -> dict[str, Any] | None:
        return self._choice


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

        add_spin("publish_per_day", "하루 발행 편수", 0, 50)
        add_line("schedule_time", "예약 시각 (HH:MM)")
        add_spin("schedule_jitter_min", "발행 지터(분)", 0, 120)
        add_spin("featured_per_tier", "티어별 추천 수", 1, 10)
        add_dspin("satisfaction_floor", "만족도 하한(%)", 0.0, 100.0)
        add_spin("seo_max_attempts", "SEO 재생성 상한", 1, 5)
        add_combo("default_channel", "기본 채널", ["ali", "coupang", "both"])
        add_combo("coupang_mode", "쿠팡 모드", ["manual", "api"])
        add_spin("coupang_threshold_krw", "쿠팡 임계(원)", 0, 100_000_000)
        add_line("coupang_tag", "쿠팡 태그")
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
            elif isinstance(widget, QLineEdit):
                txt = widget.text().strip()
                cfg[key] = (txt or None) if key == "default_keyword_persona" else txt
        return cfg

    def save(self) -> None:
        settings.save(self.collect())


# ─────────────────────────────────────────────────────────────
# 메인 윈도우
# ─────────────────────────────────────────────────────────────
class DashboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("혼살림 — 운영 대시보드")
        self.resize(1080, 720)
        self.worker: WorkerThread | None = None
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

        # 상태 배너 (자동발행 설정 요약)
        self.banner = QLabel()
        self.banner.setStyleSheet(
            "background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;"
            "padding:6px 10px;color:#1b5e20;"
        )
        outer.addWidget(self.banner)

        # 탭
        self.tabs = QTabWidget()
        self.tab_queue = _read_only_table(["ID", "상태", "키워드/제목", "생성일"])
        self.tab_keywords = _read_only_table(["ID", "키워드", "채널", "상태", "점수", "미리선택"])
        # 메뉴 순서 = 운영 작업 순서 (세션 #26): 키워드(추천·추가·생성) → 발행 큐(검토·승인·발행)
        # → 카테고리·모니터링 → 설정. 시작점인 '키워드'가 맨 왼쪽.
        self.tabs.addTab(
            self._panel(
                self.tab_keywords,
                [
                    ("🎯 추천 키워드", self._on_recommend),
                    ("🆕 키워드 추가", self._on_add_keyword),
                    ("🛒 쿠팡 상품 추가", self._on_coupang_add),
                    ("✨ 글 생성", self._on_generate),
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
        self.tabs.addTab(self._build_monitor_tab(), "카테고리·모니터링")
        self.tabs.addTab(self._build_settings_tab(), "설정")
        outer.addWidget(self.tabs, 1)

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
        self.tab_health = _read_only_table(["카테고리", "slug", "추천", "전체", "상태"])
        lay.addWidget(self.tab_health, 1)
        return w

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

    def refresh(self) -> None:
        cfg = settings.load()
        self.banner.setText(
            f"자동발행 — 하루 {cfg['publish_per_day']}편 · 예약 시각 {cfg['schedule_time']} KST "
            f"· 쿠팡 모드: {cfg['coupang_mode']}"
        )
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
            self._fill_health(conn)
        finally:
            conn.close()

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
            self.tab_queue.setItem(i, 1, _cell(st, st))
            self.tab_queue.setItem(i, 2, _cell(str(title)))
            self.tab_queue.setItem(i, 3, _cell(str(r.get("created_at") or "")))

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
            self.tab_keywords.setItem(i, 3, _cell(st, st))
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

    # ---- 로그/작업 ----
    def append_log(self, line: str) -> None:
        self.log.append(line)
        self.log.ensureCursorVisible()

    def run_task(
        self, fn: Callable[[], Any], on_done: Callable[[bool, Any], None] | None = None
    ) -> None:
        """백그라운드 작업 실행(Phase C~ 액션 공용). 동시에 하나만."""
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
                QMessageBox.warning(self, "작업 실패", str(result).splitlines()[0])
            elif isinstance(result, int) and result != 0:
                self.append_log(f"[경고] 명령이 코드 {result}로 종료 — 위 로그를 확인하세요")
            self.refresh()
            if on_done:
                on_done(ok, result)

        self.worker.done.connect(_finish)
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

        self.run_task(task, on_done=self._after_recommend)

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
        rec = dlg.chosen()
        if not rec:
            return
        kw = str(rec["keyword"])
        channel = str(rec.get("channel") or "ali")
        vol = int(rec.get("volume") or 0)
        note = f"추천(검색량 {vol}·씨앗 {rec.get('seed')})"

        def add_task() -> int:
            import cli

            return cli.cmd_keyword_add(
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

        self.run_task(add_task)

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

        self.run_task(task)

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

        self.run_task(task, on_done=self._after_auto_pick)

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

        self.run_task(task)

    def _on_coupang_add(self) -> None:
        kid = self._selected_id(self.tab_keywords)
        if kid is None:
            QMessageBox.information(
                self, "선택 필요", "키워드 탭에서 상품을 추가할 키워드를 먼저 선택하세요."
            )
            return
        dlg = CoupangProductDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        if not v["name"] or not v["url"]:
            QMessageBox.warning(self, "입력 필요", "상품명과 파트너스 URL은 필수입니다.")
            return

        def task() -> int:
            import cli

            return cli.cmd_coupang_add(
                argparse.Namespace(
                    keyword_id=kid,
                    name=v["name"],
                    url=v["url"],
                    price=v["price"],
                    widget=v["widget"],
                )
            )

        self.run_task(task)

    def _on_preview(self) -> None:
        def task() -> int:
            import webbrowser

            import cli

            rc = cli.cmd_build(
                argparse.Namespace(manifest=None, full=False, preview=True, save_empty=False)
            )
            idx = db.PROJECT_ROOT / "build" / "preview" / "index.html"
            if idx.exists():
                webbrowser.open(idx.as_uri())
                print(f"[OK] 미리보기 열기: {idx}")
            else:
                print(f"[WARN] 미리보기 파일 없음: {idx} (먼저 글을 생성하세요)")
            return rc

        self.run_task(task)

    def _on_approve(self) -> None:
        did = self._selected_or_top(self.tab_queue)  # 선택 없으면 맨 위 글
        if did is None:
            QMessageBox.information(self, "글 없음", "발행 큐에 승인할 글이 없습니다.")
            return

        def task() -> int:
            import cli

            return cli.cmd_approve(argparse.Namespace(draft=did, note="dashboard 승인"))

        self.run_task(task)

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

        self.run_task(task)

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

        self.run_task(task)

    def _on_schedule_on(self) -> None:
        t = settings.load().get("schedule_time", "11:00")
        if (
            QMessageBox.question(
                self,
                "예약 발행 켜기",
                f"매일 {t}에 승인된 글을 자동 발행하도록 등록할까요?\n(Windows 작업 스케줄러)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        def task() -> int:
            import cli

            return cli.cmd_schedule(argparse.Namespace(schedule_action="set", time=None))

        self.run_task(task)

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

        self.run_task(task)

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

        self.run_task(task)

    def _on_edit_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.save()
            self.append_log("[OK] 설정 저장됨 (data/config.json)")
            self.refresh()


def main() -> int:
    app = QApplication(sys.argv)
    win = DashboardWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
