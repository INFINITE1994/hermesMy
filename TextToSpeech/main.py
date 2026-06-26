"""
TextToSpeech - 专业文字转语音桌面工具
支持多语音、批量转换、音频保存、全局热键
"""

import sys
import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QTextEdit, QComboBox, QSlider, QPushButton,
    QFileDialog, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QSpinBox, QProgressBar, QSplitter,
    QFrame, QScrollArea, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter,
    QBrush, QPen, QPixmap, QAction, QKeySequence, QShortcut
)

import pyttsx3
import pyperclip

# ─── 常量 ────────────────────────────────────────────────────────────────

APP_NAME = "TextToSpeech"
APP_VERSION = "1.0.0"
APP_DIR = Path.home() / ".text_to_speech"
HISTORY_FILE = APP_DIR / "history.json"
SETTINGS_FILE = APP_DIR / "settings.json"

# 暗色主题色彩常量
COLORS = {
    "bg": "#0a0a0a",
    "card": "#111122",
    "card_hover": "#1a1a33",
    "accent_start": "#667eea",
    "accent_end": "#764ba2",
    "text": "#e0e0e0",
    "text_dim": "#8888aa",
    "border": "#2a2a44",
    "success": "#4ade80",
    "error": "#f87171",
    "warning": "#fbbf24",
    "slider_groove": "#2a2a44",
    "slider_handle": "#667eea",
}

# ─── 样式表 ──────────────────────────────────────────────────────────────

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}

QWidget {{
    color: {COLORS['text']};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg']};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {COLORS['card']};
    color: {COLORS['text_dim']};
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['card_hover']};
}}

QGroupBox {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px;
    font-weight: bold;
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS['accent_start']};
}}

QTextEdit {{
    background-color: {COLORS['card']};
    border: 2px solid {COLORS['border']};
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    selection-background-color: {COLORS['accent_start']};
}}

QTextEdit:focus {{
    border-color: {COLORS['accent_start']};
}}

QComboBox {{
    background-color: {COLORS['card']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:focus {{
    border-color: {COLORS['accent_start']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_dim']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_start']};
    outline: none;
}}

QPushButton {{
    background-color: {COLORS['card']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    color: {COLORS['text']};
}}

QPushButton:hover {{
    border-color: {COLORS['accent_start']};
    background-color: {COLORS['card_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_start']};
}}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    border: none;
    color: white;
}}

QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8ff0, stop:1 #8b5fb8);
}}

QPushButton#danger {{
    background-color: #331111;
    border-color: {COLORS['error']};
    color: {COLORS['error']};
}}

QPushButton#danger:hover {{
    background-color: #441111;
}}

QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {COLORS['slider_groove']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    border: none;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    border-radius: 3px;
}}

QSpinBox {{
    background-color: {COLORS['card']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px;
    font-size: 13px;
}}

QSpinBox:focus {{
    border-color: {COLORS['accent_start']};
}}

QTableWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['accent_start']};
}}

QHeaderView::section {{
    background-color: {COLORS['card']};
    color: {COLORS['accent_start']};
    padding: 10px;
    border: none;
    border-bottom: 2px solid {COLORS['accent_start']};
    font-weight: bold;
    font-size: 12px;
}}

QProgressBar {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    font-size: 11px;
    color: {COLORS['text']};
    height: 22px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    border-radius: 5px;
}}

QLabel#title {{
    font-size: 22px;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    -webkit-background-clip: text;
    color: {COLORS['accent_start']};
}}

QLabel#subtitle {{
    color: {COLORS['text_dim']};
    font-size: 12px;
}}

QLabel#status {{
    color: {COLORS['success']};
    font-size: 12px;
    padding: 4px 12px;
    background-color: #112211;
    border-radius: 10px;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg']};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent_start']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


# ─── 工作线程 ────────────────────────────────────────────────────────────

class TTSEngine(QThread):
    """TTS 引擎工作线程"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total

    def __init__(self):
        super().__init__()
        self._engine: Optional[pyttsx3.Engine] = None
        self._queue: list[str] = []
        self._voice_id: str = ""
        self._rate: int = 150
        self._volume: float = 1.0
        self._save_path: Optional[str] = None
        self._is_running = False
        self._lock = threading.Lock()

    def setup(self, voice_id: str = "", rate: int = 150, volume: float = 1.0):
        with self._lock:
            self._voice_id = voice_id
            self._rate = rate
            self._volume = volume

    def speak(self, text: str):
        """直接朗读文本"""
        with self._lock:
            self._queue = [text]
            self._save_path = None
        if not self.isRunning():
            self.start()

    def save(self, text: str, path: str):
        """保存为音频文件"""
        with self._lock:
            self._queue = [text]
            self._save_path = path
        if not self.isRunning():
            self.start()

    def batch_speak(self, texts: list[str]):
        """批量朗读"""
        with self._lock:
            self._queue = texts.copy()
            self._save_path = None
        if not self.isRunning():
            self.start()

    def batch_save(self, texts: list[str], directory: str):
        """批量保存"""
        with self._lock:
            self._queue = texts.copy()
            self._save_path = directory
        if not self.isRunning():
            self.start()

    def stop_speaking(self):
        """停止朗读"""
        with self._lock:
            self._queue.clear()
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    def run(self):
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._rate)
            self._engine.setProperty('volume', self._volume)
            if self._voice_id:
                self._engine.setProperty('voice', self._voice_id)

            with self._lock:
                queue = self._queue.copy()
                save_path = self._save_path

            total = len(queue)
            for i, text in enumerate(queue):
                self.progress.emit(i + 1, total)
                if not text.strip():
                    continue

                if save_path:
                    if total == 1:
                        # 单个文件保存
                        self._engine.save_to_file(text, save_path)
                    else:
                        # 批量保存，使用目录
                        filename = f"speech_{i+1}_{int(time.time())}.wav"
                        filepath = os.path.join(save_path, filename)
                        self._engine.save_to_file(text, filepath)
                    self._engine.runAndWait()
                else:
                    self._engine.say(text)
                    self._engine.runAndWait()

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._engine = None
            self.finished.emit()


# ─── 快捷键监听线程 ──────────────────────────────────────────────────────

class HotkeyListener(QThread):
    """全局快捷键监听"""
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = False
        self._listener = None

    def run(self):
        try:
            from pynput import keyboard

            def on_activate():
                self.hotkey_pressed.emit()

            hotkey = keyboard.HotKey(
                keyboard.HotKey.parse('<ctrl>+<shift>+s'),
                on_activate
            )

            def on_press(key):
                hotkey.press(self._listener.canonical(key))

            def on_release(key):
                hotkey.release(self._listener.canonical(key))

            with keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            ) as listener:
                self._listener = listener
                self._running = True
                listener.join()

        except ImportError:
            pass  # pynput 不可用时静默忽略
        except Exception:
            pass

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()


# ─── 主窗口 ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - 专业文字转语音工具")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)

        # 初始化目录
        APP_DIR.mkdir(exist_ok=True)

        # 初始化 TTS 引擎
        self.tts_engine = TTSEngine()
        self.tts_engine.finished.connect(self.on_tts_finished)
        self.tts_engine.error.connect(self.on_tts_error)
        self.tts_engine.progress.connect(self.on_tts_progress)

        # 初始化快捷键监听
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.hotkey_pressed.connect(self.on_hotkey)

        # 加载历史和设置
        self.history: list[dict] = self.load_history()
        self.settings: dict = self.load_settings()

        # 构建 UI
        self.setup_ui()
        self.load_voices()
        self.load_history_table()

        # 启动快捷键监听
        try:
            self.hotkey_listener.start()
        except Exception:
            pass

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ── 标题栏 ──
        header = QHBoxLayout()
        title_label = QLabel("🔊 文字转语音")
        title_label.setObjectName("title")
        header.addWidget(title_label)

        header.addStretch()

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status")
        header.addWidget(self.status_label)

        main_layout.addLayout(header)

        subtitle = QLabel("快捷键: Ctrl+Shift+S 朗读剪贴板内容  |  支持批量转换与音频导出")
        subtitle.setObjectName("subtitle")
        main_layout.addWidget(subtitle)

        # ── 主选项卡 ──
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 选项卡 1: 语音合成
        self.setup_speak_tab()

        # 选项卡 2: 批量转换
        self.setup_batch_tab()

        # 选项卡 3: 历史记录
        self.setup_history_tab()

        # 选项卡 4: 设置
        self.setup_settings_tab()

    def setup_speak_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 上半部分：文本输入
        text_group = QGroupBox("📝 输入文本")
        text_layout = QVBoxLayout(text_group)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("在此输入要转换为语音的文字...\n\n支持中文、英文及多种语言。")
        self.text_input.setMinimumHeight(180)
        text_layout.addWidget(self.text_input)

        # 字数统计
        stats_layout = QHBoxLayout()
        self.char_count_label = QLabel("字数: 0")
        self.char_count_label.setObjectName("subtitle")
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addStretch()

        # 从剪贴板粘贴按钮
        paste_btn = QPushButton("📋 从剪贴板粘贴")
        paste_btn.clicked.connect(self.paste_from_clipboard)
        stats_layout.addWidget(paste_btn)

        text_layout.addLayout(stats_layout)
        layout.addWidget(text_group)

        # 控制面板
        control_group = QGroupBox("🎛️ 语音控制")
        control_layout = QGridLayout(control_group)
        control_layout.setSpacing(16)

        # 语音选择
        control_layout.addWidget(QLabel("语音引擎:"), 0, 0)
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(300)
        control_layout.addWidget(self.voice_combo, 0, 1, 1, 2)

        # 语速控制
        control_layout.addWidget(QLabel("语速:"), 1, 0)
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(50, 300)
        self.rate_slider.setValue(self.settings.get("rate", 150))
        self.rate_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        control_layout.addWidget(self.rate_slider, 1, 1)
        self.rate_label = QLabel(f"{self.rate_slider.value()} 字/分")
        self.rate_label.setMinimumWidth(70)
        control_layout.addWidget(self.rate_label, 1, 2)
        self.rate_slider.valueChanged.connect(
            lambda v: self.rate_label.setText(f"{v} 字/分"))

        # 音量控制
        control_layout.addWidget(QLabel("音量:"), 2, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.settings.get("volume", 1.0) * 100))
        control_layout.addWidget(self.volume_slider, 2, 1)
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_label.setMinimumWidth(70)
        control_layout.addWidget(self.volume_label, 2, 2)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%"))

        layout.addWidget(control_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.speak_btn = QPushButton("🔊 开始朗读")
        self.speak_btn.setObjectName("primary")
        self.speak_btn.setMinimumHeight(44)
        self.speak_btn.clicked.connect(self.start_speak)
        btn_layout.addWidget(self.speak_btn)

        self.stop_btn = QPushButton("⏹ 停止朗读")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.clicked.connect(self.stop_speak)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        self.save_btn = QPushButton("💾 保存音频")
        self.save_btn.setMinimumHeight(44)
        self.save_btn.clicked.connect(self.save_audio)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        self.tabs.addTab(tab, "🎤 语音合成")

        # 连接文本变化信号
        self.text_input.textChanged.connect(self.update_char_count)

    def setup_batch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 批量输入区
        input_group = QGroupBox("📋 批量文本输入（每行一条）")
        input_layout = QVBoxLayout(input_group)

        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText(
            "每行输入一条文本，将按行批量转换语音...\n\n"
            "示例:\n"
            "你好，欢迎使用文字转语音工具\n"
            "这是第二条文本\n"
            "Hello, this is English text"
        )
        self.batch_input.setMinimumHeight(200)
        input_layout.addWidget(self.batch_input)

        batch_stats = QHBoxLayout()
        self.batch_count_label = QLabel("条目数: 0")
        self.batch_count_label.setObjectName("subtitle")
        batch_stats.addWidget(self.batch_count_label)
        batch_stats.addStretch()
        input_layout.addLayout(batch_stats)

        layout.addWidget(input_group)

        # 批量操作按钮
        btn_layout = QHBoxLayout()

        self.batch_speak_btn = QPushButton("🔊 批量朗读")
        self.batch_speak_btn.setObjectName("primary")
        self.batch_speak_btn.setMinimumHeight(44)
        self.batch_speak_btn.clicked.connect(self.batch_speak)
        btn_layout.addWidget(self.batch_speak_btn)

        self.batch_save_btn = QPushButton("📁 批量保存为WAV")
        self.batch_save_btn.setMinimumHeight(44)
        self.batch_save_btn.clicked.connect(self.batch_save)
        btn_layout.addWidget(self.batch_save_btn)

        self.batch_stop_btn = QPushButton("⏹ 停止")
        self.batch_stop_btn.setObjectName("danger")
        self.batch_stop_btn.setMinimumHeight(44)
        self.batch_stop_btn.clicked.connect(self.stop_speak)
        self.batch_stop_btn.setEnabled(False)
        btn_layout.addWidget(self.batch_stop_btn)

        layout.addLayout(btn_layout)

        # 批量进度
        self.batch_progress = QProgressBar()
        self.batch_progress.setVisible(False)
        layout.addWidget(self.batch_progress)

        layout.addStretch()

        self.tabs.addTab(tab, "📦 批量转换")

        # 连接信号
        self.batch_input.textChanged.connect(self.update_batch_count)

    def setup_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 操作栏
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("📜 转换历史"))

        action_layout.addStretch()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_history_table)
        action_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("🗑 清空历史")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self.clear_history)
        action_layout.addWidget(clear_btn)

        layout.addLayout(action_layout)

        # 历史表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["时间", "文本内容", "语音", "操作"])
        self.history_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(3, 120)
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['card']};
                alternate-background-color: {COLORS['card_hover']};
            }}
        """)
        self.history_table.setAlternatingRowColors(True)

        layout.addWidget(self.history_table)

        self.tabs.addTab(tab, "📜 历史记录")

    def setup_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)

        # 快捷键设置
        hotkey_group = QGroupBox("⌨️ 全局快捷键")
        hotkey_layout = QVBoxLayout(hotkey_group)

        hotkey_desc = QLabel(
            "当前快捷键: Ctrl + Shift + S\n\n"
            "功能: 读取剪贴板中的文本并朗读。\n"
            "在任何应用中复制文本后，按下快捷键即可朗读。"
        )
        hotkey_desc.setWordWrap(True)
        hotkey_layout.addWidget(hotkey_desc)

        hotkey_status = QLabel(
            f"监听状态: {'运行中' if self.hotkey_listener.isRunning() else '未启动'}")
        hotkey_layout.addWidget(hotkey_status)

        layout.addWidget(hotkey_group)

        # 保存设置
        save_group = QGroupBox("💾 默认保存路径")
        save_layout = QVBoxLayout(save_group)

        path_layout = QHBoxLayout()
        self.save_path_label = QLabel(
            self.settings.get("save_path", str(Path.home() / "Documents")))
        path_layout.addWidget(self.save_path_label, 1)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(browse_btn)

        save_layout.addLayout(path_layout)
        layout.addWidget(save_group)

        # 引擎信息
        info_group = QGroupBox("ℹ️ 引擎信息")
        info_layout = QVBoxLayout(info_group)

        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice_count = len(voices) if voices else 0
            engine.stop()
        except Exception:
            voice_count = 0

        info_text = QLabel(
            f"引擎: pyttsx3\n"
            f"可用语音数: {voice_count}\n"
            f"版本: {APP_VERSION}\n"
            f"配置目录: {APP_DIR}"
        )
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        layout.addStretch()

        # 保存按钮
        save_settings_btn = QPushButton("💾 保存设置")
        save_settings_btn.setObjectName("primary")
        save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(tab, "⚙️ 设置")

    # ── 语音加载 ──

    def load_voices(self):
        """加载系统可用语音"""
        self.voice_combo.clear()
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            engine.stop()

            if voices:
                for voice in voices:
                    display_name = voice.name
                    # 标记语言
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                        display_name += " [中文]"
                    elif 'en' in voice.id.lower() or 'english' in voice.name.lower():
                        display_name += " [英文]"
                    self.voice_combo.addItem(display_name, voice.id)

                # 恢复上次选择
                saved_voice = self.settings.get("voice_id", "")
                if saved_voice:
                    for i in range(self.voice_combo.count()):
                        if self.voice_combo.itemData(i) == saved_voice:
                            self.voice_combo.setCurrentIndex(i)
                            break

        except Exception as e:
            self.voice_combo.addItem(f"默认语音 (加载失败: {e})", "")

    # ── 语音操作 ──

    def get_current_voice_id(self) -> str:
        return self.voice_combo.currentData() or ""

    def get_current_rate(self) -> int:
        return self.rate_slider.value()

    def get_current_volume(self) -> float:
        return self.volume_slider.value() / 100.0

    def start_speak(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入要朗读的文本！")
            return

        self.tts_engine.setup(
            voice_id=self.get_current_voice_id(),
            rate=self.get_current_rate(),
            volume=self.get_current_volume()
        )
        self.tts_engine.speak(text)

        self.set_speaking_state(True)
        self.add_to_history(text)
        self.status_label.setText("正在朗读...")

    def stop_speak(self):
        self.tts_engine.stop_speaking()
        self.set_speaking_state(False)
        self.status_label.setText("已停止")

    def save_audio(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入要保存的文本！")
            return

        default_dir = self.settings.get(
            "save_path", str(Path.home() / "Documents"))
        default_name = f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存音频文件",
            os.path.join(default_dir, default_name),
            "WAV 音频 (*.wav);;所有文件 (*.*)"
        )

        if filepath:
            self.tts_engine.setup(
                voice_id=self.get_current_voice_id(),
                rate=self.get_current_rate(),
                volume=self.get_current_volume()
            )
            self.tts_engine.save(text, filepath)
            self.set_speaking_state(True)
            self.add_to_history(text, filepath)
            self.status_label.setText(f"正在保存: {os.path.basename(filepath)}")

    def batch_speak(self):
        texts = self.get_batch_texts()
        if not texts:
            QMessageBox.warning(self, "提示", "请先输入批量文本！")
            return

        self.tts_engine.setup(
            voice_id=self.get_current_voice_id(),
            rate=self.get_current_rate(),
            volume=self.get_current_volume()
        )
        self.tts_engine.batch_speak(texts)

        self.batch_progress.setVisible(True)
        self.batch_progress.setMaximum(len(texts))
        self.batch_progress.setValue(0)
        self.batch_speak_btn.setEnabled(False)
        self.batch_stop_btn.setEnabled(True)
        self.status_label.setText(f"批量朗读: 共 {len(texts)} 条")

        for text in texts:
            self.add_to_history(text)

    def batch_save(self):
        texts = self.get_batch_texts()
        if not texts:
            QMessageBox.warning(self, "提示", "请先输入批量文本！")
            return

        directory = QFileDialog.getExistingDirectory(
            self, "选择保存目录",
            self.settings.get("save_path", str(Path.home() / "Documents"))
        )

        if directory:
            self.tts_engine.setup(
                voice_id=self.get_current_voice_id(),
                rate=self.get_current_rate(),
                volume=self.get_current_volume()
            )
            self.tts_engine.batch_save(texts, directory)

            self.batch_progress.setVisible(True)
            self.batch_progress.setMaximum(len(texts))
            self.batch_progress.setValue(0)
            self.batch_speak_btn.setEnabled(False)
            self.batch_stop_btn.setEnabled(True)
            self.status_label.setText(f"批量保存中: 共 {len(texts)} 条")

            for text in texts:
                self.add_to_history(text, directory)

    def get_batch_texts(self) -> list[str]:
        raw = self.batch_input.toPlainText().strip()
        if not raw:
            return []
        return [line.strip() for line in raw.split('\n') if line.strip()]

    # ── 快捷键 ──

    def on_hotkey(self):
        """快捷键触发：朗读剪贴板内容"""
        try:
            text = pyperclip.paste().strip()
            if text:
                self.text_input.setPlainText(text)
                self.tabs.setCurrentIndex(0)
                QTimer.singleShot(100, self.start_speak)
            else:
                self.status_label.setText("剪贴板为空")
        except Exception as e:
            self.status_label.setText(f"快捷键错误: {e}")

    # ── TTS 回调 ──

    def on_tts_finished(self):
        self.set_speaking_state(False)
        self.progress_bar.setVisible(False)
        self.batch_progress.setVisible(False)
        self.status_label.setText("就绪")

    def on_tts_error(self, error_msg: str):
        self.set_speaking_state(False)
        self.progress_bar.setVisible(False)
        self.batch_progress.setVisible(False)
        self.status_label.setText(f"错误: {error_msg}")
        QMessageBox.critical(self, "语音引擎错误", f"朗读出错:\n{error_msg}")

    def on_tts_progress(self, current: int, total: int):
        if total > 1:
            self.batch_progress.setVisible(True)
            self.batch_progress.setMaximum(total)
            self.batch_progress.setValue(current)
            self.status_label.setText(f"处理中: {current}/{total}")

    def set_speaking_state(self, speaking: bool):
        self.speak_btn.setEnabled(not speaking)
        self.stop_btn.setEnabled(speaking)
        self.batch_speak_btn.setEnabled(not speaking)
        self.batch_stop_btn.setEnabled(speaking)
        self.save_btn.setEnabled(not speaking)

    # ── 历史管理 ──

    def add_to_history(self, text: str, save_path: str = ""):
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text[:200],  # 截断过长文本
            "voice": self.voice_combo.currentText(),
            "save_path": save_path,
            "rate": self.get_current_rate(),
            "volume": self.get_current_volume()
        }
        self.history.insert(0, entry)
        # 只保留最近 500 条
        self.history = self.history[:500]
        self.save_history()
        self.load_history_table()

    def load_history_table(self):
        self.history_table.setRowCount(len(self.history))
        for row, entry in enumerate(self.history):
            self.history_table.setItem(
                row, 0, QTableWidgetItem(entry.get("time", "")))

            text_item = QTableWidgetItem(entry.get("text", ""))
            text_item.setToolTip(entry.get("text", ""))
            self.history_table.setItem(row, 1, text_item)

            self.history_table.setItem(
                row, 2, QTableWidgetItem(entry.get("voice", "")))

            # 重播按钮
            replay_btn = QPushButton("🔊 重播")
            replay_btn.setMaximumHeight(28)
            replay_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_start']};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-size: 11px;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_end']};
                }}
            """)
            text = entry.get("text", "")
            replay_btn.clicked.connect(lambda checked, t=text: self.replay_text(t))
            self.history_table.setCellWidget(row, 3, replay_btn)

    def replay_text(self, text: str):
        if text:
            self.text_input.setPlainText(text)
            self.tabs.setCurrentIndex(0)
            QTimer.singleShot(200, self.start_speak)

    def clear_history(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.save_history()
            self.load_history_table()

    # ── 辅助功能 ──

    def paste_from_clipboard(self):
        try:
            text = pyperclip.paste()
            if text:
                self.text_input.setPlainText(text)
        except Exception:
            pass

    def update_char_count(self):
        count = len(self.text_input.toPlainText())
        self.char_count_label.setText(f"字数: {count}")

    def update_batch_count(self):
        texts = self.get_batch_texts()
        self.batch_count_label.setText(f"条目数: {len(texts)}")

    def browse_save_path(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择默认保存路径",
            self.save_path_label.text()
        )
        if directory:
            self.save_path_label.setText(directory)

    # ── 持久化 ──

    def load_history(self) -> list[dict]:
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_settings(self) -> dict:
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "rate": 150,
            "volume": 1.0,
            "voice_id": "",
            "save_path": str(Path.home() / "Documents")
        }

    def save_settings(self):
        settings = {
            "rate": self.rate_slider.value(),
            "volume": self.volume_slider.value() / 100.0,
            "voice_id": self.get_current_voice_id(),
            "save_path": self.save_path_label.text()
        }
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "设置已保存！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")

    # ── 窗口事件 ──

    def closeEvent(self, event):
        # 停止 TTS
        self.tts_engine.stop_speaking()
        self.tts_engine.quit()
        self.tts_engine.wait(2000)

        # 停止快捷键监听
        self.hotkey_listener.stop()
        self.hotkey_listener.quit()
        self.hotkey_listener.wait(1000)

        # 保存设置
        self.save_settings()

        event.accept()


# ─── 入口 ────────────────────────────────────────────────────────────────

def main():
    # 高 DPI 支持
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # 应用暗色主题
    app.setStyleSheet(STYLESHEET)

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
