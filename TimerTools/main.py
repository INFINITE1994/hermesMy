#!/usr/bin/env python3
"""
TimerTools - 计时工具箱
一款功能丰富的计时器与闹钟工具箱桌面应用程序
使用 PyQt6 构建，具有深色主题和精美的渐变配色方案
"""

import sys
import json
import math
import winsound
from datetime import datetime, timedelta, date
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QTimeEdit, QDateEdit, QComboBox,
    QLineEdit, QListWidget, QListWidgetItem, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QScrollArea, QSizePolicy, QCheckBox, QTextEdit, QSplitter
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QDate, QUrl, QSize, QPropertyAnimation,
    QEasingCurve, pyqtSignal
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter,
    QBrush, QPen, QPixmap, QFontDatabase
)

# ─── 常量 ───────────────────────────────────────────────────────────────────

APP_NAME = "TimerTools"
APP_VERSION = "1.0.0"
WINDOW_TITLE = "⏱ TimerTools - 计时工具箱"
CARD_STYLE = """
    QFrame[objectName="card"] {
        background-color: #111122;
        border: 1px solid #222244;
        border-radius: 12px;
        padding: 16px;
    }
"""

DARK_THEME = """
/* ─── 全局样式 ─── */
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ─── 选项卡 ─── */
QTabWidget::pane {
    border: 1px solid #222244;
    background-color: #0a0a0a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #111122;
    color: #8888aa;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #667eea;
    color: white;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #222244;
    color: #bbbbdd;
}

/* ─── 按钮 ─── */
QPushButton {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #764ba2;
}

QPushButton:pressed {
    background-color: #5567cc;
}

QPushButton:disabled {
    background-color: #333355;
    color: #666688;
}

QPushButton[objectName="dangerBtn"] {
    background-color: #e74c3c;
}

QPushButton[objectName="dangerBtn"]:hover {
    background-color: #c0392b;
}

QPushButton[objectName="successBtn"] {
    background-color: #27ae60;
}

QPushButton[objectName="successBtn"]:hover {
    background-color: #2ecc71;
}

QPushButton[objectName="accentBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-size: 15px;
    padding: 12px 32px;
}

QPushButton[objectName="accentBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #764ba2, stop:1 #667eea);
}

/* ─── 标签 ─── */
QLabel {
    color: #ccccdd;
    font-size: 13px;
}

QLabel[objectName="title"] {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel[objectName="subtitle"] {
    font-size: 14px;
    color: #8888aa;
}

QLabel[objectName="timerDisplay"] {
    font-size: 52px;
    font-weight: bold;
    color: #667eea;
    font-family: "Consolas", "Courier New", monospace;
    padding: 20px;
}

QLabel[objectName="pomodoroDisplay"] {
    font-size: 72px;
    font-weight: bold;
    font-family: "Consolas", "Courier New", monospace;
    padding: 24px;
}

QLabel[objectName="clockDisplay"] {
    font-size: 36px;
    font-weight: bold;
    color: #764ba2;
    font-family: "Consolas", "Courier New", monospace;
}

QLabel[objectName="zoneName"] {
    font-size: 15px;
    font-weight: bold;
    color: #667eea;
}

QLabel[objectName="zoneTime"] {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
    font-family: "Consolas", monospace;
}

QLabel[objectName="zoneDate"] {
    font-size: 12px;
    color: #8888aa;
}

/* ─── 输入控件 ─── */
QSpinBox, QTimeEdit, QDateEdit, QComboBox, QLineEdit {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #333366;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}

QSpinBox:focus, QTimeEdit:focus, QDateEdit:focus,
QComboBox:focus, QLineEdit:focus {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #333366;
    selection-background-color: #667eea;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #222244;
    border: none;
    width: 20px;
}

/* ─── 表格 ─── */
QTableWidget {
    background-color: #111122;
    color: #e0e0e0;
    gridline-color: #222244;
    border: 1px solid #222244;
    border-radius: 8px;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #667eea;
}

QHeaderView::section {
    background-color: #1a1a2e;
    color: #8888aa;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #667eea;
    font-weight: bold;
}

/* ─── 列表 ─── */
QListWidget {
    background-color: #111122;
    color: #e0e0e0;
    border: 1px solid #222244;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}

QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #1a1a2e;
}

QListWidget::item:selected {
    background-color: #667eea;
    color: white;
}

/* ─── 分组框 ─── */
QGroupBox {
    color: #667eea;
    border: 1px solid #222244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}

/* ─── 滚动条 ─── */
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #333366;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ─── 文本编辑 ─── */
QTextEdit {
    background-color: #111122;
    color: #e0e0e0;
    border: 1px solid #222244;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}

/* ─── 复选框 ─── */
QCheckBox {
    color: #ccccdd;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #333366;
    background-color: #1a1a2e;
}

QCheckBox::indicator:checked {
    background-color: #667eea;
    border-color: #667eea;
}
"""


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def make_card() -> QFrame:
    """创建一个卡片样式的 QFrame"""
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(CARD_STYLE)
    return card


def play_alert():
    """播放系统提示音"""
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


def play_alarm_sound():
    """播放闹钟提示音"""
    try:
        winsound.Beep(800, 300)
        winsound.Beep(1000, 300)
        winsound.Beep(800, 300)
    except Exception:
        pass


def format_duration(seconds: int) -> str:
    """格式化时长为 HH:MM:SS"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_duration_ms(ms: int) -> str:
    """格式化毫秒时长为 HH:MM:SS.cc"""
    total_seconds = ms // 1000
    centiseconds = (ms % 1000) // 10
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}.{centiseconds:02d}"
    return f"{m:02d}:{s:02d}.{centiseconds:02d}"


# ─── 倒计时选项卡 ──────────────────────────────────────────────────────────────

class CountdownTab(QWidget):
    """倒计时器 - 设置倒计时并在结束时发出提示音"""

    def __init__(self):
        super().__init__()
        self.remaining = 0
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("⏱ 倒计时器")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 时间显示
        self.display = QLabel("00:00:00")
        self.display.setObjectName("timerDisplay")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.display)

        # 设置区域
        card = make_card()
        grid = QGridLayout(card)
        grid.setSpacing(12)

        grid.addWidget(QLabel("小时:"), 0, 0)
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setFixedWidth(100)
        grid.addWidget(self.hour_spin, 0, 1)

        grid.addWidget(QLabel("分钟:"), 0, 2)
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 59)
        self.min_spin.setFixedWidth(100)
        grid.addWidget(self.min_spin, 0, 3)

        grid.addWidget(QLabel("秒数:"), 0, 4)
        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)
        self.sec_spin.setFixedWidth(100)
        grid.addWidget(self.sec_spin, 0, 5)

        layout.addWidget(card)

        # 进度条文本
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("subtitle")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("▶ 开始")
        self.start_btn.setObjectName("successBtn")
        self.start_btn.setFixedWidth(120)
        self.start_btn.clicked.connect(self._start)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setFixedWidth(120)
        self.pause_btn.clicked.connect(self._pause)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)

        self.reset_btn = QPushButton("↺ 重置")
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.setFixedWidth(120)
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)

        # 预设按钮
        preset_card = make_card()
        preset_layout = QHBoxLayout(preset_card)
        preset_layout.setSpacing(8)
        preset_label = QLabel("快速预设:")
        preset_label.setObjectName("subtitle")
        preset_layout.addWidget(preset_label)

        for label, mins in [("1分钟", 1), ("5分钟", 5), ("10分钟", 10),
                            ("15分钟", 15), ("25分钟", 25), ("30分钟", 30),
                            ("60分钟", 60)]:
            btn = QPushButton(label)
            btn.setFixedWidth(80)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a2e;
                    border: 1px solid #333366;
                    padding: 6px 12px;
                    font-size: 12px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #667eea;
                    border-color: #667eea;
                }
            """)
            btn.clicked.connect(lambda checked, m=mins: self._set_preset(m))
            preset_layout.addWidget(btn)

        layout.addWidget(preset_card)
        layout.addStretch()

    def _set_preset(self, minutes: int):
        if not self.running:
            self.hour_spin.setValue(minutes // 60)
            self.min_spin.setValue(minutes % 60)
            self.sec_spin.setValue(0)

    def _start(self):
        if not self.running:
            total = (self.hour_spin.value() * 3600 +
                     self.min_spin.value() * 60 +
                     self.sec_spin.value())
            if total == 0:
                return
            if self.remaining == 0:
                self.remaining = total
                self.total = total
            self.running = True
            self.timer.start(1000)
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self._update_display()

    def _pause(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

    def _reset(self):
        self.running = False
        self.timer.stop()
        self.remaining = 0
        self.display.setText("00:00:00")
        self.progress_label.setText("")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def _tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            if self.remaining == 0:
                self.timer.stop()
                self.running = False
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.display.setText("00:00:00")
                self.progress_label.setText("⏰ 时间到！")
                play_alert()

    def _update_display(self):
        self.display.setText(format_duration(self.remaining))
        if self.total > 0:
            pct = int((self.total - self.remaining) / self.total * 100)
            bar_len = 40
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            self.progress_label.setText(f"[{bar}] {pct}%")


# ─── 秒表选项卡 ──────────────────────────────────────────────────────────────

class StopwatchTab(QWidget):
    """秒表 - 开始/停止/计圈，记录圈数时间"""

    def __init__(self):
        super().__init__()
        self.elapsed_ms = 0
        self.running = False
        self.laps = []
        self.last_lap_ms = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("⏱ 秒表")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.display = QLabel("00:00.00")
        self.display.setObjectName("timerDisplay")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.display)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("▶ 开始")
        self.start_btn.setObjectName("successBtn")
        self.start_btn.setFixedWidth(120)
        self.start_btn.clicked.connect(self._start_stop)
        btn_layout.addWidget(self.start_btn)

        self.lap_btn = QPushButton("🏁 计圈")
        self.lap_btn.setFixedWidth(120)
        self.lap_btn.clicked.connect(self._lap)
        self.lap_btn.setEnabled(False)
        btn_layout.addWidget(self.lap_btn)

        self.reset_btn = QPushButton("↺ 重置")
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.setFixedWidth(120)
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)

        # 圈数列表
        lap_label = QLabel("📋 圈数记录")
        lap_label.setObjectName("subtitle")
        layout.addWidget(lap_label)

        self.lap_list = QTableWidget()
        self.lap_list.setColumnCount(4)
        self.lap_list.setHorizontalHeaderLabels(["圈数", "圈用时", "累计时间", "差异"])
        self.lap_list.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.lap_list.verticalHeader().setVisible(False)
        self.lap_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.lap_list)

        # 统计
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("subtitle")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)

    def _start_stop(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.start_btn.setText("▶ 继续")
            self.start_btn.setObjectName("successBtn")
            self.start_btn.setStyleSheet("")
            self.lap_btn.setEnabled(False)
        else:
            self.running = True
            self.timer.start(10)  # 10ms resolution
            self.start_btn.setText("⏸ 停止")
            self.start_btn.setObjectName("dangerBtn")
            self.start_btn.setStyleSheet("")
            self.lap_btn.setEnabled(True)

    def _lap(self):
        if not self.running:
            return
        lap_time = self.elapsed_ms - self.last_lap_ms
        self.laps.append({
            'number': len(self.laps) + 1,
            'lap_time': lap_time,
            'total_time': self.elapsed_ms,
        })
        self.last_lap_ms = self.elapsed_ms
        self._update_lap_table()

    def _reset(self):
        self.running = False
        self.timer.stop()
        self.elapsed_ms = 0
        self.last_lap_ms = 0
        self.laps = []
        self.display.setText("00:00.00")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("successBtn")
        self.start_btn.setStyleSheet("")
        self.lap_btn.setEnabled(False)
        self.lap_list.setRowCount(0)
        self.stats_label.setText("")

    def _tick(self):
        self.elapsed_ms += 10
        self.display.setText(format_duration_ms(self.elapsed_ms))

    def _update_lap_table(self):
        self.lap_list.setRowCount(len(self.laps))
        best = min(l['lap_time'] for l in self.laps)
        worst = max(l['lap_time'] for l in self.laps)

        for i, lap in enumerate(self.laps):
            self.lap_list.setItem(i, 0, QTableWidgetItem(f"#{lap['number']}"))
            self.lap_list.setItem(i, 1, QTableWidgetItem(
                format_duration_ms(lap['lap_time'])))
            self.lap_list.setItem(i, 2, QTableWidgetItem(
                format_duration_ms(lap['total_time'])))

            # 差异列
            if len(self.laps) > 1:
                avg = sum(l['lap_time'] for l in self.laps) / len(self.laps)
                diff = lap['lap_time'] - avg
                sign = "+" if diff >= 0 else ""
                self.lap_list.setItem(i, 3, QTableWidgetItem(
                    f"{sign}{format_duration_ms(int(abs(diff)))}"))
            else:
                self.lap_list.setItem(i, 3, QTableWidgetItem("-"))

        # 统计
        if len(self.laps) > 1:
            avg = sum(l['lap_time'] for l in self.laps) / len(self.laps)
            self.stats_label.setText(
                f"最快圈: {format_duration_ms(best)} | "
                f"最慢圈: {format_duration_ms(worst)} | "
                f"平均圈: {format_duration_ms(int(avg))} | "
                f"总圈数: {len(self.laps)}"
            )


# ─── 世界时钟选项卡 ──────────────────────────────────────────────────────────

# 常用时区映射（Windows 兼容）
TIMEZONE_MAP = {
    "北京 (UTC+8)": 8,
    "东京 (UTC+9)": 9,
    "首尔 (UTC+9)": 9,
    "新加坡 (UTC+8)": 8,
    "悉尼 (UTC+11)": 11,
    "迪拜 (UTC+4)": 4,
    "莫斯科 (UTC+3)": 3,
    "柏林 (UTC+2)": 2,
    "巴黎 (UTC+2)": 2,
    "伦敦 (UTC+1)": 1,
    "纽约 (UTC-4)": -4,
    "芝加哥 (UTC-5)": -5,
    "丹佛 (UTC-6)": -6,
    "洛杉矶 (UTC-7)": -7,
    "夏威夷 (UTC-10)": -10,
    "奥克兰 (UTC+12)": 12,
    "孟买 (UTC+5:30)": 5.5,
    "曼谷 (UTC+7)": 7,
    "开罗 (UTC+2)": 2,
    "圣保罗 (UTC-3)": -3,
}


class WorldClockTab(QWidget):
    """世界时钟 - 显示多个时区的当前时间"""

    def __init__(self):
        super().__init__()
        self.clocks = ["北京 (UTC+8)", "纽约 (UTC-4)", "伦敦 (UTC+1)",
                        "东京 (UTC+9)", "洛杉矶 (UTC-7)", "悉尼 (UTC+11)"]
        self._build_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_clocks)
        self.timer.start(1000)
        self._update_clocks()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🌍 世界时钟")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 本地时间
        local_card = make_card()
        local_layout = QVBoxLayout(local_card)
        local_label = QLabel("📍 本地时间")
        local_label.setObjectName("subtitle")
        local_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        local_layout.addWidget(local_label)
        self.local_time = QLabel("--:--:--")
        self.local_time.setObjectName("clockDisplay")
        self.local_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        local_layout.addWidget(self.local_time)
        self.local_date = QLabel("")
        self.local_date.setObjectName("subtitle")
        self.local_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        local_layout.addWidget(self.local_date)
        layout.addWidget(local_card)

        # 添加时区控制
        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(TIMEZONE_MAP.keys())
        add_layout.addWidget(self.tz_combo)

        add_btn = QPushButton("➕ 添加时区")
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self._add_tz)
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        layout.addLayout(add_layout)

        # 时区网格
        self.clock_grid = QGridLayout()
        self.clock_grid.setSpacing(12)
        layout.addLayout(self.clock_grid)

        layout.addStretch()

    def _add_tz(self):
        tz = self.tz_combo.currentText()
        if tz not in self.clocks:
            self.clocks.append(tz)
            self._rebuild_clocks()

    def _rebuild_clocks(self):
        # 清除旧的
        while self.clock_grid.count():
            item = self.clock_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.clock_labels = {}
        for i, tz_name in enumerate(self.clocks):
            card = make_card()
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)

            # 删除按钮
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666;
                    border: none;
                    font-size: 14px;
                    min-width: 24px;
                    padding: 0;
                }
                QPushButton:hover {
                    color: #e74c3c;
                }
            """)
            del_btn.clicked.connect(lambda checked, name=tz_name: self._remove_tz(name))
            top_row = QHBoxLayout()
            top_row.addStretch()
            top_row.addWidget(del_btn)
            card_layout.addLayout(top_row)

            name_lbl = QLabel(tz_name)
            name_lbl.setObjectName("zoneName")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_lbl)

            time_lbl = QLabel("--:--:--")
            time_lbl.setObjectName("zoneTime")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(time_lbl)

            date_lbl = QLabel("")
            date_lbl.setObjectName("zoneDate")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(date_lbl)

            col = i % 3
            row = i // 3
            self.clock_grid.addWidget(card, row, col)
            self.clock_labels[tz_name] = (time_lbl, date_lbl)

    def _remove_tz(self, name):
        if name in self.clocks and len(self.clocks) > 1:
            self.clocks.remove(name)
            self._rebuild_clocks()

    def _update_clocks(self):
        now_utc = datetime.utcnow()
        self.local_time.setText(datetime.now().strftime("%H:%M:%S"))
        self.local_date.setText(datetime.now().strftime("%Y年%m月%d日 %A"))

        if not hasattr(self, 'clock_labels') or not self.clock_labels:
            self._rebuild_clocks()

        for tz_name in self.clocks:
            if tz_name in self.clock_labels:
                offset = TIMEZONE_MAP.get(tz_name, 0)
                tz_time = now_utc + timedelta(hours=offset)
                time_lbl, date_lbl = self.clock_labels[tz_name]
                time_lbl.setText(tz_time.strftime("%H:%M:%S"))
                date_lbl.setText(tz_time.strftime("%Y-%m-%d"))


# ─── 番茄钟选项卡 ──────────────────────────────────────────────────────────────

class PomodoroTab(QWidget):
    """番茄钟 - 25/5 分钟工作/休息循环"""

    def __init__(self):
        super().__init__()
        self.work_minutes = 25
        self.break_minutes = 5
        self.remaining = 0
        self.running = False
        self.is_work = True
        self.cycle_count = 0
        self.total_work_seconds = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🍅 番茄钟")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 状态标签
        self.status_label = QLabel("🎯 准备工作")
        self.status_label.setObjectName("subtitle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 时间显示
        self.display = QLabel("25:00")
        self.display.setObjectName("pomodoroDisplay")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.display)

        # 进度
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("subtitle")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        # 设置
        settings_card = make_card()
        settings_layout = QHBoxLayout(settings_card)
        settings_layout.setSpacing(20)

        settings_layout.addWidget(QLabel("工作时长:"))
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 120)
        self.work_spin.setValue(25)
        self.work_spin.setSuffix(" 分钟")
        self.work_spin.setFixedWidth(110)
        self.work_spin.valueChanged.connect(self._update_settings)
        settings_layout.addWidget(self.work_spin)

        settings_layout.addWidget(QLabel("休息时长:"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(5)
        self.break_spin.setSuffix(" 分钟")
        self.break_spin.setFixedWidth(110)
        self.break_spin.valueChanged.connect(self._update_settings)
        settings_layout.addWidget(self.break_spin)

        settings_layout.addStretch()
        layout.addWidget(settings_card)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("▶ 开始专注")
        self.start_btn.setObjectName("accentBtn")
        self.start_btn.setFixedWidth(160)
        self.start_btn.clicked.connect(self._start_pause)
        btn_layout.addWidget(self.start_btn)

        self.skip_btn = QPushButton("⏭ 跳过")
        self.skip_btn.setFixedWidth(120)
        self.skip_btn.clicked.connect(self._skip)
        btn_layout.addWidget(self.skip_btn)

        self.reset_btn = QPushButton("↺ 重置")
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.setFixedWidth(120)
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)

        # 统计
        stats_card = make_card()
        stats_layout = QHBoxLayout(stats_card)
        self.cycle_label = QLabel("🍅 完成周期: 0")
        self.cycle_label.setObjectName("subtitle")
        stats_layout.addWidget(self.cycle_label)

        self.work_time_label = QLabel("⏱ 总专注时间: 0分钟")
        self.work_time_label.setObjectName("subtitle")
        stats_layout.addWidget(self.work_time_label)
        stats_layout.addStretch()
        layout.addWidget(stats_card)

        layout.addStretch()
        self._update_display()

    def _update_settings(self):
        if not self.running:
            self.work_minutes = self.work_spin.value()
            self.break_minutes = self.break_spin.value()
            self._update_display()

    def _update_display(self):
        if self.is_work:
            mins = self.work_minutes
        else:
            mins = self.break_minutes

        if self.remaining == 0:
            total = mins * 60
        else:
            total = self.remaining

        self.display.setText(format_duration(total))

    def _start_pause(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.start_btn.setText("▶ 继续")
        else:
            if self.remaining == 0:
                if self.is_work:
                    self.remaining = self.work_minutes * 60
                    self.total = self.work_minutes * 60
                else:
                    self.remaining = self.break_minutes * 60
                    self.total = self.break_minutes * 60
            self.running = True
            self.timer.start(1000)
            self.start_btn.setText("⏸ 暂停")

    def _skip(self):
        self.running = False
        self.timer.stop()
        self._switch_mode()

    def _reset(self):
        self.running = False
        self.timer.stop()
        self.remaining = 0
        self.is_work = True
        self.start_btn.setText("▶ 开始专注")
        self.status_label.setText("🎯 准备工作")
        self.display.setStyleSheet("")  # reset color
        self._update_display()

    def _switch_mode(self):
        if self.is_work:
            self.cycle_count += 1
            self.cycle_label.setText(f"🍅 完成周期: {self.cycle_count}")
            self.is_work = False
            self.status_label.setText("☕ 休息时间")
            self.remaining = self.break_minutes * 60
            self.total = self.break_minutes * 60
            self.display.setStyleSheet("color: #27ae60; font-size: 72px; font-weight: bold;")
        else:
            self.is_work = True
            self.status_label.setText("🎯 工作时间")
            self.remaining = self.work_minutes * 60
            self.total = self.work_minutes * 60
            self.display.setStyleSheet("color: #667eea; font-size: 72px; font-weight: bold;")

        self.start_btn.setText("▶ 开始")
        self.running = False
        self._update_display()
        play_alert()

    def _tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            if self.is_work:
                self.total_work_seconds += 1
                mins = self.total_work_seconds // 60
                self.work_time_label.setText(f"⏱ 总专注时间: {mins}分钟")
            self._update_display()

            # 进度
            pct = int((self.total - self.remaining) / self.total * 100)
            bar_len = 40
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            self.progress_label.setText(f"[{bar}] {pct}%")

            if self.remaining == 0:
                self.timer.stop()
                self.running = False
                self._switch_mode()


# ─── 闹钟选项卡 ──────────────────────────────────────────────────────────────

class AlarmItem:
    """闹钟数据对象"""
    def __init__(self, time_str: str, label: str = "", enabled: bool = True):
        self.time_str = time_str  # HH:MM
        self.label = label
        self.enabled = enabled
        self.triggered = False


class AlarmTab(QWidget):
    """闹钟 - 设置多个闹钟"""

    def __init__(self):
        super().__init__()
        self.alarms: list[AlarmItem] = []
        self._build_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_alarms)
        self.timer.start(1000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("⏰ 闹钟")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 当前时间
        self.current_time = QLabel("--:--:--")
        self.current_time.setObjectName("clockDisplay")
        self.current_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_time)

        # 添加闹钟
        add_card = make_card()
        add_layout = QHBoxLayout(add_card)
        add_layout.setSpacing(10)

        add_layout.addWidget(QLabel("时间:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime().addSecs(3600))
        self.time_edit.setFixedWidth(120)
        add_layout.addWidget(self.time_edit)

        add_layout.addWidget(QLabel("标签:"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("闹钟备注（可选）")
        self.label_edit.setFixedWidth(200)
        add_layout.addWidget(self.label_edit)

        add_btn = QPushButton("➕ 添加闹钟")
        add_btn.setFixedWidth(130)
        add_btn.clicked.connect(self._add_alarm)
        add_layout.addWidget(add_btn)

        add_layout.addStretch()
        layout.addWidget(add_card)

        # 闹钟列表
        list_label = QLabel("📋 已设置的闹钟")
        list_label.setObjectName("subtitle")
        layout.addWidget(list_label)

        self.alarm_list = QListWidget()
        layout.addWidget(self.alarm_list)

        # 删除按钮
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        del_btn = QPushButton("🗑 删除选中")
        del_btn.setObjectName("dangerBtn")
        del_btn.setFixedWidth(130)
        del_btn.clicked.connect(self._delete_alarm)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)

        # 提示
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: bold;")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.alert_label)

        self._update_clock()

    def _update_clock(self):
        self.current_time.setText(datetime.now().strftime("%H:%M:%S"))

    def _add_alarm(self):
        t = self.time_edit.time().toString("HH:mm")
        label = self.label_edit.text().strip()
        alarm = AlarmItem(t, label)
        self.alarms.append(alarm)
        self._refresh_list()
        self.label_edit.clear()

    def _delete_alarm(self):
        row = self.alarm_list.currentRow()
        if 0 <= row < len(self.alarms):
            self.alarms.pop(row)
            self._refresh_list()

    def _refresh_list(self):
        self.alarm_list.clear()
        for alarm in self.alarms:
            status = "✅" if alarm.enabled else "⬜"
            label_part = f" - {alarm.label}" if alarm.label else ""
            self.alarm_list.addItem(f"{status} {alarm.time_str}{label_part}")

    def _check_alarms(self):
        self._update_clock()
        now = datetime.now().strftime("%H:%M")
        for alarm in self.alarms:
            if alarm.enabled and alarm.time_str == now and not alarm.triggered:
                alarm.triggered = True
                label = alarm.label if alarm.label else alarm.time_str
                self.alert_label.setText(f"⏰ 闹钟响了: {label}")
                play_alarm_sound()
                QTimer.singleShot(10000, lambda: self.alert_label.setText(""))
            elif alarm.time_str != now:
                alarm.triggered = False


# ─── 日期计算器选项卡 ──────────────────────────────────────────────────────────

class DateCalcTab(QWidget):
    """日期计算器 - 计算两个日期之间的天数"""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("📅 日期计算器")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 计算天数差
        card1 = make_card()
        card1_layout = QVBoxLayout(card1)

        card1_title = QLabel("📆 计算两个日期之间的天数")
        card1_title.setObjectName("subtitle")
        card1_layout.addWidget(card1_title)

        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        date_layout.addWidget(QLabel("起始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setFixedWidth(160)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setFixedWidth(160)
        date_layout.addWidget(self.end_date)

        calc_btn = QPushButton("🔢 计算")
        calc_btn.setFixedWidth(100)
        calc_btn.clicked.connect(self._calc_diff)
        date_layout.addWidget(calc_btn)

        date_layout.addStretch()
        card1_layout.addLayout(date_layout)

        self.diff_result = QLabel("")
        self.diff_result.setStyleSheet("font-size: 20px; color: #667eea; font-weight: bold;")
        self.diff_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card1_layout.addWidget(self.diff_result)

        layout.addWidget(card1)

        # 日期加减
        card2 = make_card()
        card2_layout = QVBoxLayout(card2)

        card2_title = QLabel("➕ 日期加减计算")
        card2_title.setObjectName("subtitle")
        card2_layout.addWidget(card2_title)

        add_layout = QHBoxLayout()
        add_layout.setSpacing(12)

        add_layout.addWidget(QLabel("基准日期:"))
        self.base_date = QDateEdit()
        self.base_date.setCalendarPopup(True)
        self.base_date.setDate(QDate.currentDate())
        self.base_date.setFixedWidth(160)
        add_layout.addWidget(self.base_date)

        add_layout.addWidget(QLabel("加减天数:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(-99999, 99999)
        self.days_spin.setValue(100)
        self.days_spin.setFixedWidth(100)
        add_layout.addWidget(self.days_spin)

        add_btn = QPushButton("📅 计算")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self._calc_add)
        add_layout.addWidget(add_btn)

        add_layout.addStretch()
        card2_layout.addLayout(add_layout)

        self.add_result = QLabel("")
        self.add_result.setStyleSheet("font-size: 20px; color: #764ba2; font-weight: bold;")
        self.add_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card2_layout.addWidget(self.add_result)

        layout.addWidget(card2)

        # 星期计算
        card3 = make_card()
        card3_layout = QVBoxLayout(card3)

        card3_title = QLabel("📅 查看某天是星期几")
        card3_title.setObjectName("subtitle")
        card3_layout.addWidget(card3_title)

        dow_layout = QHBoxLayout()
        dow_layout.setSpacing(12)

        dow_layout.addWidget(QLabel("日期:"))
        self.dow_date = QDateEdit()
        self.dow_date.setCalendarPopup(True)
        self.dow_date.setDate(QDate.currentDate())
        self.dow_date.setFixedWidth(160)
        dow_layout.addWidget(self.dow_date)

        dow_btn = QPushButton("📅 查询")
        dow_btn.setFixedWidth(100)
        dow_btn.clicked.connect(self._calc_dow)
        dow_layout.addWidget(dow_btn)

        dow_layout.addStretch()
        card3_layout.addLayout(dow_layout)

        self.dow_result = QLabel("")
        self.dow_result.setStyleSheet("font-size: 18px; color: #e0e0e0;")
        self.dow_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card3_layout.addWidget(self.dow_result)

        layout.addWidget(card3)
        layout.addStretch()

    def _calc_diff(self):
        d1 = self.start_date.date().toPyDate()
        d2 = self.end_date.date().toPyDate()
        delta = d2 - d1
        days = delta.days
        weeks = abs(days) // 7
        remaining = abs(days) % 7

        direction = "之后" if days > 0 else "之前" if days < 0 else "是同一天"
        result_text = f"相隔 {abs(days)} 天"
        if weeks > 0:
            result_text += f"（{weeks} 周 {remaining} 天）"
        result_text += f"  ·  {d2.strftime('%Y-%m-%d')} 在 {d1.strftime('%Y-%m-%d')} {direction}"

        self.diff_result.setText(result_text)

    def _calc_add(self):
        base = self.base_date.date().toPyDate()
        days = self.days_spin.value()
        result = base + timedelta(days=days)

        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        wd = weekdays_cn[result.weekday()]

        direction = "后" if days > 0 else "前"
        self.add_result.setText(
            f"{base.strftime('%Y-%m-%d')} {abs(days)} 天{direction} → "
            f"{result.strftime('%Y-%m-%d')} ({wd})"
        )

    def _calc_dow(self):
        d = self.dow_date.date().toPyDate()
        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        wd = weekdays_cn[d.weekday()]

        today = date.today()
        delta = d - today
        if delta.days == 0:
            relative = "（今天）"
        elif delta.days == 1:
            relative = "（明天）"
        elif delta.days == -1:
            relative = "（昨天）"
        elif delta.days > 0:
            relative = f"（{delta.days} 天后）"
        else:
            relative = f"（{abs(delta.days)} 天前）"

        self.dow_result.setText(f"{d.strftime('%Y-%m-%d')} 是 {wd} {relative}")


# ─── 会议规划选项卡 ──────────────────────────────────────────────────────────

MEETING_ZONES = {
    "北京 (UTC+8)": 8,
    "东京 (UTC+9)": 9,
    "纽约 (UTC-4)": -4,
    "伦敦 (UTC+1)": 1,
    "洛杉矶 (UTC-7)": -7,
    "悉尼 (UTC+11)": 11,
    "柏林 (UTC+2)": 2,
    "迪拜 (UTC+4)": 4,
    "孟买 (UTC+5:30)": 5.5,
    "新加坡 (UTC+8)": 8,
    "首尔 (UTC+9)": 9,
    "莫斯科 (UTC+3)": 3,
    "圣保罗 (UTC-3)": -3,
    "巴黎 (UTC+2)": 2,
    "芝加哥 (UTC-5)": -5,
}


class MeetingPlannerTab(QWidget):
    """会议规划 - 在多个时区之间找到重叠的工作时间"""

    def __init__(self):
        super().__init__()
        self.selected_zones = ["北京 (UTC+8)", "纽约 (UTC-4)", "伦敦 (UTC+1)"]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🤝 会议规划")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("在多个时区之间找到共同的工作时间窗口")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # 选择时区
        tz_card = make_card()
        tz_layout = QVBoxLayout(tz_card)

        tz_header = QLabel("📍 参与时区")
        tz_header.setObjectName("subtitle")
        tz_layout.addWidget(tz_header)

        add_tz_layout = QHBoxLayout()
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(MEETING_ZONES.keys())
        add_tz_layout.addWidget(self.tz_combo)

        add_btn = QPushButton("➕ 添加")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._add_zone)
        add_tz_layout.addWidget(add_btn)

        add_tz_layout.addStretch()
        tz_layout.addLayout(add_tz_layout)

        self.zone_list = QListWidget()
        self.zone_list.setMaximumHeight(100)
        tz_layout.addWidget(self.zone_list)

        del_btn = QPushButton("🗑 删除选中")
        del_btn.setObjectName("dangerBtn")
        del_btn.setFixedWidth(120)
        del_btn.clicked.connect(self._remove_zone)
        tz_layout.addWidget(del_btn)

        layout.addWidget(tz_card)

        # 工作时间设置
        work_card = make_card()
        work_layout = QHBoxLayout(work_card)
        work_layout.addWidget(QLabel("工作时间范围:"))
        self.work_start = QSpinBox()
        self.work_start.setRange(0, 23)
        self.work_start.setValue(9)
        self.work_start.setSuffix(":00")
        self.work_start.setFixedWidth(90)
        work_layout.addWidget(self.work_start)

        work_layout.addWidget(QLabel("到"))
        self.work_end = QSpinBox()
        self.work_end.setRange(1, 24)
        self.work_end.setValue(18)
        self.work_end.setSuffix(":00")
        self.work_end.setFixedWidth(90)
        work_layout.addWidget(self.work_end)

        plan_btn = QPushButton("🔍 分析")
        plan_btn.setObjectName("accentBtn")
        plan_btn.setFixedWidth(100)
        plan_btn.clicked.connect(self._analyze)
        work_layout.addWidget(plan_btn)
        work_layout.addStretch()
        layout.addWidget(work_card)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(len(self.selected_zones) + 1)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.result_table)

        # 建议
        self.suggestion = QLabel("")
        self.suggestion.setStyleSheet("font-size: 15px; color: #667eea; font-weight: bold;")
        self.suggestion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.suggestion.setWordWrap(True)
        layout.addWidget(self.suggestion)

        self._refresh_zone_list()

    def _add_zone(self):
        zone = self.tz_combo.currentText()
        if zone not in self.selected_zones:
            self.selected_zones.append(zone)
            self._refresh_zone_list()

    def _remove_zone(self):
        row = self.zone_list.currentRow()
        if 0 <= row < len(self.selected_zones):
            self.selected_zones.pop(row)
            self._refresh_zone_list()

    def _refresh_zone_list(self):
        self.zone_list.clear()
        for z in self.selected_zones:
            self.zone_list.addItem(z)

    def _analyze(self):
        if len(self.selected_zones) < 2:
            self.suggestion.setText("请至少选择两个时区")
            return

        work_start = self.work_start.value()
        work_end = self.work_end.value()

        # 分析 UTC 每个小时，看各地是否在工作时间内
        headers = ["UTC 时间"] + self.selected_zones
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(24)

        good_hours = []

        for utc_hour in range(24):
            utc_item = QTableWidgetItem(f"{utc_hour:02d}:00")
            self.result_table.setItem(utc_hour, 0, utc_item)

            all_work = True
            for i, zone_name in enumerate(self.selected_zones):
                offset = MEETING_ZONES.get(zone_name, 0)
                local_hour = (utc_hour + offset) % 24

                item = QTableWidgetItem(f"{local_hour:02d}:00")
                self.result_table.setItem(utc_hour, i + 1, item)

                if not (work_start <= local_hour < work_end):
                    all_work = False
                    item.setBackground(QColor("#2a1a1a"))
                    item.setForeground(QColor("#cc6666"))
                else:
                    item.setBackground(QColor("#1a2a1a"))
                    item.setForeground(QColor("#66cc66"))

            if all_work:
                good_hours.append(utc_hour)
                utc_item.setBackground(QColor("#1a2a1a"))
                utc_item.setForeground(QColor("#66cc66"))
            else:
                utc_item.setBackground(QColor("#2a1a1a"))
                utc_item.setForeground(QColor("#cc6666"))

        self.result_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        if good_hours:
            hours_str = ", ".join(f"{h:02d}:00 UTC" for h in good_hours)
            self.suggestion.setText(
                f"✅ 推荐会议时间（所有地区都在工作时间内）：{hours_str}"
            )
        else:
            # 找重叠最多的时段
            best_utc = 0
            best_count = 0
            for utc_hour in range(24):
                count = 0
                for zone_name in self.selected_zones:
                    offset = MEETING_ZONES.get(zone_name, 0)
                    local_hour = (utc_hour + offset) % 24
                    if work_start <= local_hour < work_end:
                        count += 1
                if count > best_count:
                    best_count = count
                    best_utc = utc_hour

            self.suggestion.setText(
                f"⚠️ 没有完美的会议时间。最佳时段: {best_utc:02d}:00 UTC "
                f"({best_count}/{len(self.selected_zones)} 个地区在工作时间内)"
            )


# ─── 主窗口 ─────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """TimerTools 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)

        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)

        # 添加各个功能选项卡
        self.tabs.addTab(CountdownTab(), "⏱ 倒计时")
        self.tabs.addTab(StopwatchTab(), "⏱ 秒表")
        self.tabs.addTab(WorldClockTab(), "🌍 世界时钟")
        self.tabs.addTab(PomodoroTab(), "🍅 番茄钟")
        self.tabs.addTab(AlarmTab(), "⏰ 闹钟")
        self.tabs.addTab(DateCalcTab(), "📅 日期计算")
        self.tabs.addTab(MeetingPlannerTab(), "🤝 会议规划")

        self.setCentralWidget(self.tabs)

        # 状态栏
        self.statusBar().showMessage("TimerTools v1.0.0 - 计时工具箱")
        self.statusBar().setStyleSheet(
            "background-color: #111122; color: #666688; padding: 4px; font-size: 12px;"
        )


# ─── 入口 ───────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 应用深色主题
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # 应用样式表
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
