#!/usr/bin/env python3
"""DiskBenchmark - 磁盘性能基准测试工具"""

import sys
import os
import json
import time
import random
import csv
import io
import tempfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QProgressBar, QTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
    QGroupBox, QFileDialog, QMessageBox, QSplitter, QFrame, QScrollArea,
    QHeaderView, QSizePolicy, QCheckBox, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient, QBrush

import psutil


# ─── History Storage ───────────────────────────────────────────────────────────

HISTORY_DIR = Path(os.environ.get("APPDATA", tempfile.gettempdir())) / "DiskBenchmark"
HISTORY_FILE = HISTORY_DIR / "history.json"


def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_history(records: list[dict]):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── Benchmark Worker ──────────────────────────────────────────────────────────

class BenchmarkWorker(QThread):
    progress = pyqtSignal(int, str)   # percent, status text
    result = pyqtSignal(dict)         # final result dict
    error = pyqtSignal(str)

    def __init__(self, test_type: str, params: dict):
        super().__init__()
        self.test_type = test_type
        self.params = params
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _run_seq_rw(self, is_read: bool, block_size: int, total_mb: int):
        """Sequential read/write using temp file."""
        direction = "读取" if is_read else "写入"
        tmp = Path(tempfile.gettempdir()) / "_diskbench_seq.tmp"
        block = block_size
        total_bytes = total_mb * 1024 * 1024
        iterations = total_bytes // block
        data = os.urandom(block) if not is_read else None

        if not is_read:
            # Write test
            wrote = 0
            t0 = time.perf_counter()
            with open(tmp, "wb", buffering=0) as f:
                for i in range(iterations):
                    if self._cancelled:
                        return None
                    f.write(data)
                    wrote += block
                    pct = int((i + 1) / iterations * 100)
                    if pct % 5 == 0:
                        elapsed = time.perf_counter() - t0
                        speed = wrote / elapsed / (1024 * 1024) if elapsed > 0 else 0
                        self.progress.emit(pct, f"顺序写入: {speed:.1f} MB/s")
            elapsed = time.perf_counter() - t0
            speed = wrote / elapsed / (1024 * 1024)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return {"speed_mb_s": speed, "elapsed_s": elapsed, "bytes": wrote, "direction": direction}
        else:
            # Need file to exist first
            with open(tmp, "wb") as f:
                for _ in range(iterations):
                    f.write(data)
            # Read test
            read = 0
            t0 = time.perf_counter()
            with open(tmp, "rb", buffering=0) as f:
                for i in range(iterations):
                    if self._cancelled:
                        os.remove(tmp)
                        return None
                    chunk = f.read(block)
                    if not chunk:
                        break
                    read += len(chunk)
                    pct = int((i + 1) / iterations * 100)
                    if pct % 5 == 0:
                        elapsed = time.perf_counter() - t0
                        speed = read / elapsed / (1024 * 1024) if elapsed > 0 else 0
                        self.progress.emit(pct, f"顺序读取: {speed:.1f} MB/s")
            elapsed = time.perf_counter() - t0
            speed = read / elapsed / (1024 * 1024)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return {"speed_mb_s": speed, "elapsed_s": elapsed, "bytes": read, "direction": direction}

    def _run_random_rw(self, is_read: bool, block_size: int, count: int, file_size_mb: int = 256):
        """Random read/write using seek-based access."""
        direction = "随机读取" if is_read else "随机写入"
        tmp = Path(tempfile.gettempdir()) / "_diskbench_rand.tmp"
        file_size = file_size_mb * 1024 * 1024

        # Create test file if needed
        if not tmp.exists() or tmp.stat().st_size < file_size:
            self.progress.emit(5, f"准备测试文件...")
            with open(tmp, "wb") as f:
                remaining = file_size
                while remaining > 0 and not self._cancelled:
                    chunk = min(remaining, 1024 * 1024)
                    f.write(os.urandom(chunk))
                    remaining -= chunk

        data = os.urandom(block_size)
        total_ops = count
        bytes_done = 0
        t0 = time.perf_counter()
        max_offset = file_size - block_size

        mode = "rb" if is_read else "r+b"
        with open(tmp, mode, buffering=0) as f:
            for i in range(total_ops):
                if self._cancelled:
                    return None
                offset = random.randint(0, max_offset)
                f.seek(offset)
                if is_read:
                    f.read(block_size)
                else:
                    f.write(data)
                bytes_done += block_size
                pct = int((i + 1) / total_ops * 100)
                if pct % 10 == 0:
                    elapsed = time.perf_counter() - t0
                    iops = (i + 1) / elapsed if elapsed > 0 else 0
                    self.progress.emit(pct, f"{direction}: {iops:.0f} IOPS")

        elapsed = time.perf_counter() - t0
        iops = total_ops / elapsed
        speed = bytes_done / elapsed / (1024 * 1024)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return {"speed_mb_s": speed, "iops": iops, "elapsed_s": elapsed, "bytes": bytes_done, "ops": total_ops, "direction": direction}

    def _run_mixed(self, read_pct: int, block_size: int, count: int, file_size_mb: int = 256):
        """Mixed read/write workload."""
        tmp = Path(tempfile.gettempdir()) / "_diskbench_mixed.tmp"
        file_size = file_size_mb * 1024 * 1024

        if not tmp.exists() or tmp.stat().st_size < file_size:
            self.progress.emit(5, "准备测试文件...")
            with open(tmp, "wb") as f:
                remaining = file_size
                while remaining > 0 and not self._cancelled:
                    chunk = min(remaining, 1024 * 1024)
                    f.write(os.urandom(chunk))
                    remaining -= chunk

        write_data = os.urandom(block_size)
        max_offset = file_size - block_size
        total_ops = count
        read_count = 0
        write_count = 0
        bytes_done = 0
        t0 = time.perf_counter()

        with open(tmp, "r+b", buffering=0) as f:
            for i in range(total_ops):
                if self._cancelled:
                    return None
                offset = random.randint(0, max_offset)
                f.seek(offset)
                if random.randint(1, 100) <= read_pct:
                    f.read(block_size)
                    read_count += 1
                else:
                    f.write(write_data)
                    write_count += 1
                bytes_done += block_size
                pct = int((i + 1) / total_ops * 100)
                if pct % 10 == 0:
                    elapsed = time.perf_counter() - t0
                    iops = (i + 1) / elapsed if elapsed > 0 else 0
                    self.progress.emit(pct, f"混合负载 ({read_pct}:{100-read_pct}): {iops:.0f} IOPS")

        elapsed = time.perf_counter() - t0
        iops = total_ops / elapsed
        speed = bytes_done / elapsed / (1024 * 1024)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return {
            "speed_mb_s": speed, "iops": iops, "elapsed_s": elapsed,
            "bytes": bytes_done, "ops": total_ops,
            "read_ops": read_count, "write_ops": write_count,
            "direction": f"混合 ({read_pct}:{100-read_pct})"
        }

    def _run_block_size_test(self, sizes: list[int], is_read: bool, ops_per_size: int = 1000):
        """Test multiple block sizes."""
        results = []
        for idx, bs in enumerate(sizes):
            if self._cancelled:
                return None
            self.progress.emit(int(idx / len(sizes) * 100), f"测试块大小: {bs} bytes...")
            if is_read:
                r = self._run_random_rw(True, bs, ops_per_size, 128)
            else:
                r = self._run_random_rw(False, bs, ops_per_size, 128)
            if r:
                r["block_size"] = bs
                results.append(r)
        return {"test": "block_size", "read": is_read, "results": results}

    def _run_queue_depth_test(self, depths: list[int], block_size: int, is_read: bool, ops: int = 500):
        """Simulate queue depth test (sequential with varying buffer counts)."""
        results = []
        for idx, qd in enumerate(depths):
            if self._cancelled:
                return None
            self.progress.emit(int(idx / len(depths) * 100), f"队列深度: {qd}...")
            # Simulate by doing ops * qd total operations
            total_ops = ops * min(qd, 4)  # Scale down for practical runtime
            r = self._run_random_rw(is_read, block_size, total_ops, 128)
            if r:
                r["queue_depth"] = qd
                results.append(r)
        return {"test": "queue_depth", "read": is_read, "results": results}

    def run(self):
        try:
            tt = self.test_type
            p = self.params
            if tt == "seq_read":
                r = self._run_seq_rw(True, p["block_size"], p["total_mb"])
            elif tt == "seq_write":
                r = self._run_seq_rw(False, p["block_size"], p["total_mb"])
            elif tt == "rand_read":
                r = self._run_random_rw(True, p["block_size"], p["count"])
            elif tt == "rand_write":
                r = self._run_random_rw(False, p["block_size"], p["count"])
            elif tt == "mixed":
                r = self._run_mixed(p["read_pct"], p["block_size"], p["count"])
            elif tt == "block_size":
                r = self._run_block_size_test(p["sizes"], p["is_read"])
            elif tt == "queue_depth":
                r = self._run_queue_depth_test(p["depths"], p["block_size"], p["is_read"])
            else:
                self.error.emit(f"未知测试类型: {tt}")
                return

            if r is not None:
                r["test_type"] = tt
                r["timestamp"] = datetime.now().isoformat()
                self.progress.emit(100, "完成")
                self.result.emit(r)
            else:
                self.error.emit("测试已取消")
        except Exception as e:
            self.error.emit(str(e))


# ─── Styled Widgets ────────────────────────────────────────────────────────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2a2a3a;
    background: #0a0a0a;
    border-radius: 8px;
}
QTabBar::tab {
    background: #111122;
    color: #8888aa;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1a1a2e;
    color: #b8b8ff;
    border-bottom: 2px solid #667eea;
}
QTabBar::tab:hover {
    background: #1a1a2e;
    color: #aaaacc;
}
QGroupBox {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    color: #aaaacc;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #8888cc;
}
QPushButton {
    background-color: #1a1a2e;
    color: #ccccdd;
    border: 1px solid #333355;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #252545;
    border-color: #667eea;
}
QPushButton:pressed {
    background-color: #667eea;
    color: white;
}
QPushButton:disabled {
    background-color: #111122;
    color: #555566;
    border-color: #222233;
}
QPushButton[accent="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton[accent="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #778efb, stop:1 #875bb3);
}
QPushButton[accent="true"]:disabled {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #444466, stop:1 #444455);
    color: #666677;
}
QPushButton[danger="true"] {
    background-color: #3a1111;
    color: #ff6666;
    border-color: #552222;
}
QPushButton[danger="true"]:hover {
    background-color: #4a1515;
}
QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1a1a2e;
    color: #ccccdd;
    border: 1px solid #333355;
    border-radius: 5px;
    padding: 6px 10px;
    min-height: 24px;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #667eea;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #ccccdd;
    selection-background-color: #667eea;
    border: 1px solid #333355;
}
QProgressBar {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    text-align: center;
    color: #ccccdd;
    height: 22px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 5px;
}
QTableWidget {
    background-color: #111122;
    color: #ccccdd;
    gridline-color: #2a2a3a;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    selection-background-color: #2a2a5a;
}
QTableWidget::item {
    padding: 6px;
}
QHeaderView::section {
    background-color: #1a1a2e;
    color: #8888cc;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2a2a3a;
    font-weight: bold;
}
QTextEdit {
    background-color: #0d0d1a;
    color: #ccccdd;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 8px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}
QLabel {
    color: #aaaacc;
}
QLabel[heading="true"] {
    font-size: 16px;
    font-weight: bold;
    color: #ccccee;
}
QLabel[subheading="true"] {
    font-size: 11px;
    color: #666688;
}
QSlider::groove:horizontal {
    background: #1a1a2e;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #667eea;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 3px;
}
QCheckBox {
    color: #aaaacc;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #333355;
    background: #1a1a2e;
}
QCheckBox::indicator:checked {
    background: #667eea;
    border-color: #667eea;
}
QScrollBar:vertical {
    background: #0a0a0a;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #2a2a3a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #3a3a4a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def make_card(title: str) -> QGroupBox:
    g = QGroupBox(title)
    return g


def make_metric_card(value: str, label: str) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(12, 10, 12, 10)
    v = QLabel(value)
    v.setAlignment(Qt.AlignmentFlag.AlignCenter)
    v.setStyleSheet("font-size: 28px; font-weight: bold; color: #b8b8ff;")
    v.setProperty("heading", True)
    l = QLabel(label)
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l.setProperty("subheading", True)
    l.setStyleSheet("font-size: 11px; color: #666688;")
    lay.addWidget(v)
    lay.addWidget(l)
    w.setStyleSheet("background: #111122; border: 1px solid #2a2a3a; border-radius: 10px;")
    w._value_label = v
    return w


# ─── Main Window ───────────────────────────────────────────────────────────────

class DiskBenchmarkWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiskBenchmark - 磁盘性能基准测试")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        self._worker = None
        self._history = load_history()
        self._current_result = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚡ DiskBenchmark")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ccccee;")
        title.setProperty("heading", True)
        subtitle = QLabel("磁盘性能基准测试工具")
        subtitle.setProperty("subheading", True)
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #667eea; font-weight: bold;")
        header.addWidget(self.status_label)
        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        self._build_benchmark_tab()
        self._build_block_size_tab()
        self._build_queue_depth_tab()
        self._build_history_tab()
        self._build_compare_tab()

    # ── Benchmark Tab ──────────────────────────────────────────────────────

    def _build_benchmark_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Metrics row
        metrics = QHBoxLayout()
        self.m_speed = make_metric_card("-- MB/s", "速度")
        self.m_iops = make_metric_card("--", "IOPS")
        self.m_elapsed = make_metric_card("-- 秒", "耗时")
        self.m_size = make_metric_card("-- MB", "数据量")
        for m in [self.m_speed, self.m_iops, self.m_elapsed, self.m_size]:
            metrics.addWidget(m)
        layout.addLayout(metrics)

        # Controls
        ctrl_row = QHBoxLayout()
        cfg = make_card("测试配置")
        cfg_layout = QHBoxLayout(cfg)

        cfg_layout.addWidget(QLabel("测试类型:"))
        self.combo_test = QComboBox()
        self.combo_test.addItems([
            "顺序读取", "顺序写入", "随机读取", "随机写入", "混合负载"
        ])
        self.combo_test.currentIndexChanged.connect(self._on_test_type_changed)
        cfg_layout.addWidget(self.combo_test)

        cfg_layout.addWidget(QLabel("块大小:"))
        self.combo_block = QComboBox()
        self.combo_block.addItems(["512B", "4KB", "16KB", "64KB", "256KB", "1MB", "4MB"])
        self.combo_block.setCurrentIndex(1)
        cfg_layout.addWidget(self.combo_block)

        cfg_layout.addWidget(QLabel("数据量(MB):"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 4096)
        self.spin_size.setValue(64)
        self.spin_size.setSingleStep(16)
        cfg_layout.addWidget(self.spin_size)

        self.lbl_mix = QLabel("读比例%:")
        cfg_layout.addWidget(self.lbl_mix)
        self.spin_mix = QSpinBox()
        self.spin_mix.setRange(1, 99)
        self.spin_mix.setValue(70)
        cfg_layout.addWidget(self.spin_mix)
        self.lbl_mix.setVisible(False)
        self.spin_mix.setVisible(False)

        cfg_layout.addStretch()
        ctrl_row.addWidget(cfg)
        layout.addLayout(ctrl_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶ 开始测试")
        self.btn_start.setProperty("accent", True)
        self.btn_start.clicked.connect(self._start_benchmark)
        btn_row.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("✕ 取消")
        self.btn_cancel.setProperty("danger", True)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_benchmark)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()

        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(lambda: self._export("csv"))
        btn_row.addWidget(self.btn_export_csv)

        self.btn_export_txt = QPushButton("导出 TXT")
        self.btn_export_txt.setEnabled(False)
        self.btn_export_txt.clicked.connect(lambda: self._export("txt"))
        btn_row.addWidget(self.btn_export_txt)

        self.btn_export_html = QPushButton("导出 HTML")
        self.btn_export_html.setEnabled(False)
        self.btn_export_html.clicked.connect(lambda: self._export("html"))
        btn_row.addWidget(self.btn_export_html)

        layout.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("测试结果将在此显示...")
        layout.addWidget(self.output, 1)

        self.tabs.addTab(tab, "🔬 基准测试")

    def _on_test_type_changed(self, idx):
        is_mixed = idx == 4
        self.lbl_mix.setVisible(is_mixed)
        self.spin_mix.setVisible(is_mixed)

    def _get_block_size_bytes(self) -> int:
        text = self.combo_block.currentText()
        return int(text.replace("B", "").replace("K", "000").replace("M", "000000").replace("4000", "4096").replace("16000", "16384").replace("64000", "65536").replace("256000", "262144").replace("1000000", "1048576").replace("4000000", "4194304"))

    def _start_benchmark(self):
        idx = self.combo_test.currentIndex()
        block_size = self._get_block_size_bytes()
        total_mb = self.spin_size.value()

        types = ["seq_read", "seq_write", "rand_read", "rand_write", "mixed"]
        params = {"block_size": block_size, "total_mb": total_mb}

        if idx >= 2:
            params["count"] = max(500, total_mb * 100)
        if idx == 4:
            params["read_pct"] = self.spin_mix.value()

        self._run_worker(types[idx], params)

    def _run_worker(self, test_type: str, params: dict):
        self._set_running(True)
        self.output.clear()
        self.progress.setValue(0)
        self._worker = BenchmarkWorker(test_type, params)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(lambda: self._set_running(False))
        self._worker.start()

    def _set_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self.status_label.setText("测试中..." if running else "就绪")

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(pct)
        self.status_label.setText(msg)

    def _on_result(self, result: dict):
        self._current_result = result
        self._display_result(result)
        # Save to history
        record = {
            "id": len(self._history) + 1,
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "test_type": result.get("test_type", "unknown"),
            "result": result,
        }
        self._history.append(record)
        save_history(self._history)
        self.btn_export_csv.setEnabled(True)
        self.btn_export_txt.setEnabled(True)
        self.btn_export_html.setEnabled(True)
        self._refresh_history_table()
        self._refresh_compare_combo()

    def _on_error(self, msg: str):
        self.output.append(f'<span style="color:#ff6666;">❌ 错误: {msg}</span>')
        self.status_label.setText("出错")

    def _cancel_benchmark(self):
        if self._worker:
            self._worker.cancel()

    def _display_result(self, r: dict):
        tt = r.get("test_type", "")
        o = self.output

        if tt in ("seq_read", "seq_write", "rand_read", "rand_write", "mixed"):
            speed = r.get("speed_mb_s", 0)
            iops = r.get("iops", 0)
            elapsed = r.get("elapsed_s", 0)
            direction = r.get("direction", "")
            data_mb = r.get("bytes", 0) / (1024 * 1024)

            self.m_speed._value_label.setText(f"{speed:.1f} MB/s")
            self.m_iops._value_label.setText(f"{iops:.0f}" if iops else "N/A")
            self.m_elapsed._value_label.setText(f"{elapsed:.2f} 秒")
            self.m_size._value_label.setText(f"{data_mb:.1f} MB")

            o.append(f'<div style="margin:10px;">')
            o.append(f'<h3 style="color:#b8b8ff;">📊 {direction} 测试完成</h3>')
            o.append(f'<table style="color:#ccccdd;">')
            o.append(f'<tr><td style="padding:4px 16px;">速度:</td><td style="color:#66eeaa; font-weight:bold;">{speed:.2f} MB/s</td></tr>')
            if iops:
                o.append(f'<tr><td style="padding:4px 16px;">IOPS:</td><td style="color:#66eeaa; font-weight:bold;">{iops:.0f}</td></tr>')
            o.append(f'<tr><td style="padding:4px 16px;">耗时:</td><td>{elapsed:.3f} 秒</td></tr>')
            o.append(f'<tr><td style="padding:4px 16px;">数据量:</td><td>{data_mb:.1f} MB</td></tr>')
            if "read_ops" in r:
                o.append(f'<tr><td style="padding:4px 16px;">读操作:</td><td>{r["read_ops"]}</td></tr>')
                o.append(f'<tr><td style="padding:4px 16px;">写操作:</td><td>{r["write_ops"]}</td></tr>')
            o.append('</table></div>')

        elif tt == "block_size":
            results = r.get("results", [])
            o.append('<h3 style="color:#b8b8ff;">📊 块大小测试结果</h3>')
            o.append('<table style="color:#ccccdd; border-collapse:collapse;">')
            o.append('<tr style="border-bottom:1px solid #333;">'
                     '<th style="padding:6px 16px; text-align:left;">块大小</th>'
                     '<th style="padding:6px 16px;">速度 (MB/s)</th>'
                     '<th style="padding:6px 16px;">IOPS</th></tr>')
            for res in results:
                bs = res.get("block_size", 0)
                bs_str = f"{bs}B" if bs < 1024 else f"{bs//1024}KB" if bs < 1048576 else f"{bs//1048576}MB"
                o.append(f'<tr style="border-bottom:1px solid #222;">'
                         f'<td style="padding:4px 16px;">{bs_str}</td>'
                         f'<td style="padding:4px 16px; color:#66eeaa;">{res.get("speed_mb_s",0):.2f}</td>'
                         f'<td style="padding:4px 16px;">{res.get("iops",0):.0f}</td></tr>')
            o.append('</table>')

        elif tt == "queue_depth":
            results = r.get("results", [])
            o.append('<h3 style="color:#b8b8ff;">📊 队列深度测试结果</h3>')
            o.append('<table style="color:#ccccdd;">')
            o.append('<tr><th style="padding:6px 16px;">队列深度</th>'
                     '<th style="padding:6px 16px;">速度 (MB/s)</th>'
                     '<th style="padding:6px 16px;">IOPS</th></tr>')
            for res in results:
                qd = res.get("queue_depth", 0)
                o.append(f'<tr><td style="padding:4px 16px;">{qd}</td>'
                         f'<td style="padding:4px 16px; color:#66eeaa;">{res.get("speed_mb_s",0):.2f}</td>'
                         f'<td style="padding:4px 16px;">{res.get("iops",0):.0f}</td></tr>')
            o.append('</table>')

    # ── Block Size Tab ─────────────────────────────────────────────────────

    def _build_block_size_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        ctrl = QHBoxLayout()
        cfg = make_card("块大小测试配置")
        cfg_l = QHBoxLayout(cfg)

        cfg_l.addWidget(QLabel("模式:"))
        self.bs_mode = QComboBox()
        self.bs_mode.addItems(["顺序读取", "顺序写入", "随机读取", "随机写入"])
        cfg_l.addWidget(self.bs_mode)

        cfg_l.addWidget(QLabel("每组操作数:"))
        self.bs_ops = QSpinBox()
        self.bs_ops.setRange(100, 50000)
        self.bs_ops.setValue(2000)
        self.bs_ops.setSingleStep(500)
        cfg_l.addWidget(self.bs_ops)

        cfg_l.addStretch()
        ctrl.addWidget(cfg)
        layout.addLayout(ctrl)

        btn_row = QHBoxLayout()
        self.btn_bs_start = QPushButton("▶ 开始块大小测试")
        self.btn_bs_start.setProperty("accent", True)
        self.btn_bs_start.clicked.connect(self._start_block_size_test)
        btn_row.addWidget(self.btn_bs_start)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.bs_progress = QProgressBar()
        layout.addWidget(self.bs_progress)

        self.bs_output = QTextEdit()
        self.bs_output.setReadOnly(True)
        layout.addWidget(self.bs_output, 1)

        self.tabs.addTab(tab, "📦 块大小测试")

    def _start_block_size_test(self):
        sizes = [512, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304]
        is_read = self.bs_mode.currentIndex() in (0, 2)
        params = {"sizes": sizes, "is_read": is_read, "ops_per_size": self.bs_ops.value()}
        self._set_running(True)
        self.bs_output.clear()
        self._worker = BenchmarkWorker("block_size", params)
        self._worker.progress.connect(lambda p, m: self.bs_progress.setValue(p))
        self._worker.result.connect(self._on_bs_result)
        self._worker.error.connect(lambda e: self.bs_output.append(f"错误: {e}"))
        self._worker.finished.connect(lambda: self._set_running(False))
        self._worker.start()

    def _on_bs_result(self, r):
        self._display_result(r)
        record = {"id": len(self._history) + 1, "timestamp": r.get("timestamp", datetime.now().isoformat()),
                  "test_type": "block_size", "result": r}
        self._history.append(record)
        save_history(self._history)
        self._refresh_history_table()
        self._refresh_compare_combo()

    # ── Queue Depth Tab ────────────────────────────────────────────────────

    def _build_queue_depth_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        ctrl = QHBoxLayout()
        cfg = make_card("队列深度测试配置")
        cfg_l = QHBoxLayout(cfg)

        cfg_l.addWidget(QLabel("模式:"))
        self.qd_mode = QComboBox()
        self.qd_mode.addItems(["随机读取", "随机写入"])
        cfg_l.addWidget(self.qd_mode)

        cfg_l.addWidget(QLabel("每深度操作数:"))
        self.qd_ops = QSpinBox()
        self.qd_ops.setRange(100, 50000)
        self.qd_ops.setValue(1000)
        self.qd_ops.setSingleStep(500)
        cfg_l.addWidget(self.qd_ops)

        cfg_l.addStretch()
        ctrl.addWidget(cfg)
        layout.addLayout(ctrl)

        btn_row = QHBoxLayout()
        self.btn_qd_start = QPushButton("▶ 开始队列深度测试")
        self.btn_qd_start.setProperty("accent", True)
        self.btn_qd_start.clicked.connect(self._start_queue_depth_test)
        btn_row.addWidget(self.btn_qd_start)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.qd_progress = QProgressBar()
        layout.addWidget(self.qd_progress)

        self.qd_output = QTextEdit()
        self.qd_output.setReadOnly(True)
        layout.addWidget(self.qd_output, 1)

        self.tabs.addTab(tab, "📐 队列深度测试")

    def _start_queue_depth_test(self):
        depths = [1, 2, 4, 8, 16, 32, 64]
        is_read = self.qd_mode.currentIndex() == 0
        params = {"depths": depths, "block_size": 4096, "is_read": is_read, "ops": self.qd_ops.value()}
        self._set_running(True)
        self.qd_output.clear()
        self._worker = BenchmarkWorker("queue_depth", params)
        self._worker.progress.connect(lambda p, m: self.qd_progress.setValue(p))
        self._worker.result.connect(self._on_qd_result)
        self._worker.error.connect(lambda e: self.qd_output.append(f"错误: {e}"))
        self._worker.finished.connect(lambda: self._set_running(False))
        self._worker.start()

    def _on_qd_result(self, r):
        self._display_result(r)
        record = {"id": len(self._history) + 1, "timestamp": r.get("timestamp", datetime.now().isoformat()),
                  "test_type": "queue_depth", "result": r}
        self._history.append(record)
        save_history(self._history)
        self._refresh_history_table()
        self._refresh_compare_combo()

    # ── History Tab ────────────────────────────────────────────────────────

    def _build_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self._refresh_history_table)
        btn_row.addWidget(btn_refresh)

        btn_clear = QPushButton("🗑 清空历史")
        btn_clear.setProperty("danger", True)
        btn_clear.clicked.connect(self._clear_history)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["ID", "时间", "测试类型", "速度 (MB/s)", "IOPS"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.history_table, 1)

        self.tabs.addTab(tab, "📋 历史记录")
        self._refresh_history_table()

    def _refresh_history_table(self):
        t = self.history_table
        t.setRowCount(len(self._history))
        for i, rec in enumerate(reversed(self._history)):
            r = rec.get("result", {})
            t.setItem(i, 0, QTableWidgetItem(str(rec.get("id", ""))))
            t.setItem(i, 1, QTableWidgetItem(rec.get("timestamp", "")[:19]))
            tt = rec.get("test_type", "")
            type_map = {"seq_read": "顺序读取", "seq_write": "顺序写入", "rand_read": "随机读取",
                        "rand_write": "随机写入", "mixed": "混合负载", "block_size": "块大小",
                        "queue_depth": "队列深度"}
            t.setItem(i, 2, QTableWidgetItem(type_map.get(tt, tt)))

            if tt in ("block_size", "queue_depth"):
                sub = r.get("results", [])
                speeds = [s.get("speed_mb_s", 0) for s in sub]
                iops_list = [s.get("iops", 0) for s in sub]
                t.setItem(i, 3, QTableWidgetItem(f"{max(speeds):.2f}" if speeds else "-"))
                t.setItem(i, 4, QTableWidgetItem(f"{max(iops_list):.0f}" if iops_list else "-"))
            else:
                t.setItem(i, 3, QTableWidgetItem(f"{r.get('speed_mb_s', 0):.2f}"))
                t.setItem(i, 4, QTableWidgetItem(f"{r.get('iops', 0):.0f}" if r.get("iops") else "-"))

    def _clear_history(self):
        reply = QMessageBox.question(self, "确认", "确定要清空所有历史记录吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear()
            save_history(self._history)
            self._refresh_history_table()
            self._refresh_compare_combo()

    # ── Compare Tab ────────────────────────────────────────────────────────

    def _build_compare_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        ctrl = QHBoxLayout()
        cfg = make_card("结果对比")
        cfg_l = QHBoxLayout(cfg)

        cfg_l.addWidget(QLabel("记录1:"))
        self.cmp_combo1 = QComboBox()
        cfg_l.addWidget(self.cmp_combo1)

        cfg_l.addWidget(QLabel("记录2:"))
        self.cmp_combo2 = QComboBox()
        cfg_l.addWidget(self.cmp_combo2)

        btn_cmp = QPushButton("📊 对比")
        btn_cmp.setProperty("accent", True)
        btn_cmp.clicked.connect(self._do_compare)
        cfg_l.addWidget(btn_cmp)

        cfg_l.addStretch()
        ctrl.addWidget(cfg)
        layout.addLayout(ctrl)

        self.cmp_output = QTextEdit()
        self.cmp_output.setReadOnly(True)
        layout.addWidget(self.cmp_output, 1)

        self.tabs.addTab(tab, "📊 结果对比")
        self._refresh_compare_combo()

    def _refresh_compare_combo(self):
        for combo in [self.cmp_combo1, self.cmp_combo2]:
            combo.clear()
            for rec in self._history:
                tt = rec.get("test_type", "")
                type_map = {"seq_read": "顺序读取", "seq_write": "顺序写入", "rand_read": "随机读取",
                            "rand_write": "随机写入", "mixed": "混合负载", "block_size": "块大小",
                            "queue_depth": "队列深度"}
                label = f"#{rec.get('id')} {type_map.get(tt, tt)} {rec.get('timestamp','')[:19]}"
                combo.addItem(label, rec.get("id"))

    def _do_compare(self):
        idx1 = self.cmp_combo1.currentIndex()
        idx2 = self.cmp_combo2.currentIndex()
        if idx1 < 0 or idx2 < 0:
            QMessageBox.warning(self, "提示", "请选择两条记录进行对比")
            return

        r1 = self._history[idx1].get("result", {})
        r2 = self._history[idx2].get("result", {})
        o = self.cmp_output
        o.clear()

        o.append('<h3 style="color:#b8b8ff;">📊 结果对比</h3>')
        o.append('<table style="color:#ccccdd; border-collapse:collapse; width:100%;">')
        o.append('<tr style="border-bottom:2px solid #444;">'
                 '<th style="padding:8px; text-align:left;">指标</th>'
                 '<th style="padding:8px; text-align:center;">记录 1</th>'
                 '<th style="padding:8px; text-align:center;">记录 2</th>'
                 '<th style="padding:8px; text-align:center;">差异</th></tr>')

        s1 = r1.get("speed_mb_s", 0)
        s2 = r2.get("speed_mb_s", 0)
        diff_s = s2 - s1
        pct_s = (diff_s / s1 * 100) if s1 else 0
        color_s = "#66eeaa" if diff_s >= 0 else "#ff6666"
        o.append(f'<tr><td>速度 (MB/s)</td><td style="text-align:center;">{s1:.2f}</td>'
                 f'<td style="text-align:center;">{s2:.2f}</td>'
                 f'<td style="text-align:center; color:{color_s};">{diff_s:+.2f} ({pct_s:+.1f}%)</td></tr>')

        i1 = r1.get("iops", 0)
        i2 = r2.get("iops", 0)
        if i1 or i2:
            diff_i = i2 - i1
            pct_i = (diff_i / i1 * 100) if i1 else 0
            color_i = "#66eeaa" if diff_i >= 0 else "#ff6666"
            o.append(f'<tr><td>IOPS</td><td style="text-align:center;">{i1:.0f}</td>'
                     f'<td style="text-align:center;">{i2:.0f}</td>'
                     f'<td style="text-align:center; color:{color_i};">{diff_i:+.0f} ({pct_i:+.1f}%)</td></tr>')

        e1 = r1.get("elapsed_s", 0)
        e2 = r2.get("elapsed_s", 0)
        diff_e = e2 - e1
        color_e = "#66eeaa" if diff_e <= 0 else "#ff6666"
        o.append(f'<tr><td>耗时 (秒)</td><td style="text-align:center;">{e1:.3f}</td>'
                 f'<td style="text-align:center;">{e2:.3f}</td>'
                 f'<td style="text-align:center; color:{color_e};">{diff_e:+.3f}</td></tr>')

        o.append('</table>')

    # ── Export ─────────────────────────────────────────────────────────────

    def _export(self, fmt: str):
        if not self._current_result:
            QMessageBox.warning(self, "提示", "没有可导出的测试结果")
            return

        ext_map = {"csv": "CSV 文件 (*.csv)", "txt": "文本文件 (*.txt)", "html": "HTML 文件 (*.html)"}
        path, _ = QFileDialog.getSaveFileName(self, "导出结果", f"benchmark_{datetime.now():%Y%m%d_%H%M%S}.{fmt}", ext_map[fmt])
        if not path:
            return

        r = self._current_result
        try:
            if fmt == "csv":
                self._export_csv(path, r)
            elif fmt == "txt":
                self._export_txt(path, r)
            elif fmt == "html":
                self._export_html(path, r)
            QMessageBox.information(self, "成功", f"已导出到: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _export_csv(self, path: str, r: dict):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["指标", "值"])
            w.writerow(["测试时间", r.get("timestamp", "")])
            w.writerow(["测试类型", r.get("test_type", "")])
            if r.get("direction"):
                w.writerow(["方向", r["direction"]])
            if r.get("speed_mb_s"):
                w.writerow(["速度 (MB/s)", f'{r["speed_mb_s"]:.2f}'])
            if r.get("iops"):
                w.writerow(["IOPS", f'{r["iops"]:.0f}'])
            if r.get("elapsed_s"):
                w.writerow(["耗时 (秒)", f'{r["elapsed_s"]:.3f}'])
            if r.get("bytes"):
                w.writerow(["数据量 (MB)", f'{r["bytes"]/1048576:.2f}'])

    def _export_txt(self, path: str, r: dict):
        lines = ["═══ DiskBenchmark 测试结果 ═══", ""]
        lines.append(f"测试时间: {r.get('timestamp', '')}")
        lines.append(f"测试类型: {r.get('test_type', '')}")
        if r.get("direction"):
            lines.append(f"方向: {r['direction']}")
        if r.get("speed_mb_s"):
            lines.append(f"速度: {r['speed_mb_s']:.2f} MB/s")
        if r.get("iops"):
            lines.append(f"IOPS: {r['iops']:.0f}")
        if r.get("elapsed_s"):
            lines.append(f"耗时: {r['elapsed_s']:.3f} 秒")
        lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _export_html(self, path: str, r: dict):
        speed = r.get("speed_mb_s", 0)
        iops = r.get("iops", 0)
        elapsed = r.get("elapsed_s", 0)
        direction = r.get("direction", r.get("test_type", ""))
        html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>DiskBenchmark 结果</title>
<style>
body {{ background:#0a0a0a; color:#e0e0e0; font-family:'Microsoft YaHei',sans-serif; padding:40px; }}
.card {{ background:#111122; border:1px solid #2a2a3a; border-radius:12px; padding:30px; max-width:600px; margin:auto; }}
h1 {{ color:#b8b8ff; text-align:center; }}
.metric {{ display:flex; justify-content:space-around; margin:20px 0; }}
.m {{ text-align:center; }}
.m .v {{ font-size:32px; font-weight:bold; color:#b8b8ff; }}
.m .l {{ color:#666688; font-size:12px; }}
table {{ width:100%; margin-top:20px; }}
td {{ padding:8px 16px; }}
td:first-child {{ color:#8888cc; }}
.v2 {{ color:#66eeaa; font-weight:bold; }}
</style></head><body>
<div class="card">
<h1>⚡ DiskBenchmark</h1>
<p style="text-align:center; color:#666688;">{r.get('timestamp','')[:19]}</p>
<div class="metric">
<div class="m"><div class="v">{speed:.1f}</div><div class="l">MB/s</div></div>
{"<div class='m'><div class='v'>" + f"{iops:.0f}" + "</div><div class='l'>IOPS</div></div>" if iops else ""}
<div class="m"><div class="v">{elapsed:.2f}</div><div class="l">秒</div></div>
</div>
<table>
<tr><td>测试类型</td><td class="v2">{direction}</td></tr>
<tr><td>数据量</td><td>{r.get('bytes',0)/1048576:.1f} MB</td></tr>
</table></div></body></html>"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setStyle("Fusion")

    # Set dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#ccccdd"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ccccdd"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = DiskBenchmarkWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
