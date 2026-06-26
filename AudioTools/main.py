#!/usr/bin/env python3
"""
AudioTools - 音频处理工具箱
A comprehensive audio processing toolbox built with PyQt6.
Features: Audio Converter, Trimmer, Merger, Volume Adjuster, Audio Info, Batch Convert, Audio Recorder.
"""

import sys
import os
import json
import time
import threading
import tempfile
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFileDialog, QLineEdit,
    QComboBox, QSlider, QProgressBar, QTextEdit, QTabWidget,
    QGroupBox, QListWidget, QListWidgetItem, QDoubleSpinBox,
    QMessageBox, QFrame, QScrollArea, QSplitter, QSpinBox,
    QCheckBox, QStatusBar
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QSize, QThread, QPropertyAnimation,
    QEasingCurve, QPoint, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QFontDatabase, QConicalGradient,
    QDesktopServices
)
from PyQt6.QtCore import QUrl

import numpy as np

# Try importing audio libraries
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


# ============================================================
# Signals helper for cross-thread communication
# ============================================================
class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


# ============================================================
# Stylesheet
# ============================================================
STYLESHEET = """
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #2a2a3a;
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
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover:!selected {
    background-color: #1a1a2e;
    color: #bbbbdd;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    margin-top: 10px;
    padding: 15px;
    padding-top: 25px;
    font-weight: bold;
    font-size: 13px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
    color: #9090cc;
}

QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 22px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b92ee, stop:1 #8a5fb5);
}

QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5566cc, stop:1 #603a8a);
}

QPushButton:disabled {
    background-color: #2a2a3a;
    color: #555566;
}

QPushButton.secondary {
    background-color: #1a1a2e;
    border: 1px solid #3a3a5a;
}

QPushButton.secondary:hover {
    background-color: #2a2a3e;
    border: 1px solid #667eea;
}

QPushButton.danger {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
}

QPushButton.success {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #667eea;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #667eea;
}

QComboBox {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    min-width: 120px;
}

QComboBox:focus {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #111122;
    border: 1px solid #3a3a5a;
    color: #e0e0e0;
    selection-background-color: #667eea;
}

QListWidget {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 5px;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
    margin: 2px;
}

QListWidget::item:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QListWidget::item:hover:!selected {
    background-color: #1a1a2e;
}

QTextEdit {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px;
    color: #e0e0e0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

QTextEdit:focus {
    border: 1px solid #667eea;
}

QProgressBar {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    text-align: center;
    color: white;
    font-weight: bold;
    height: 24px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 5px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #2a2a3a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 3px;
}

QLabel {
    color: #ccccdd;
}

QLabel.title {
    font-size: 20px;
    font-weight: bold;
    color: white;
}

QLabel.subtitle {
    font-size: 12px;
    color: #6666aa;
}

QLabel.section-title {
    font-size: 15px;
    font-weight: bold;
    color: #9090dd;
    padding: 5px 0;
}

QStatusBar {
    background-color: #0d0d1a;
    border-top: 1px solid #2a2a3a;
    color: #8888aa;
}

QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #2a2a3a;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QCheckBox {
    spacing: 8px;
    color: #ccccdd;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a3a5a;
    background-color: #0d0d1a;
}

QCheckBox::indicator:checked {
    background-color: #667eea;
    border-color: #667eea;
}

QSplitter::handle {
    background-color: #2a2a3a;
}
"""


# ============================================================
# Gradient card widget
# ============================================================
class GradientCard(QFrame):
    """A card widget with a gradient border effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border: 1px solid #2a2a3a;
                border-radius: 12px;
            }
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)


# ============================================================
# Audio Converter Tab
# ============================================================
class AudioConverterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🎵 音频格式转换")
        header.setProperty("class", "title")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("在 MP3、WAV、FLAC、OGG、AAC 之间自由转换音频格式")
        desc.setProperty("class", "subtitle")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File selection group
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        input_row = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择输入音频文件...")
        input_btn = QPushButton("浏览")
        input_btn.setFixedWidth(80)
        input_btn.clicked.connect(self.browse_input)
        input_row.addWidget(self.input_path)
        input_row.addWidget(input_btn)
        file_layout.addLayout(input_row)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出路径...")
        output_btn = QPushButton("浏览")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(output_btn)
        file_layout.addLayout(output_row)

        layout.addWidget(file_group)

        # Format selection
        format_group = QGroupBox("输出设置")
        format_layout = QGridLayout(format_group)

        format_layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "WAV", "FLAC", "OGG", "AAC"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo, 0, 1)

        format_layout.addWidget(QLabel("比特率:"), 1, 0)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentText("192k")
        format_layout.addWidget(self.bitrate_combo, 1, 1)

        format_layout.addWidget(QLabel("采样率:"), 2, 0)
        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItems(["22050", "44100", "48000", "96000"])
        self.samplerate_combo.setCurrentText("44100")
        format_layout.addWidget(self.samplerate_combo, 2, 1)

        format_layout.setColumnStretch(1, 1)
        layout.addWidget(format_group)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        # Convert button
        btn_row = QHBoxLayout()
        self.convert_btn = QPushButton("🔄 开始转换")
        self.convert_btn.setFixedHeight(45)
        self.convert_btn.clicked.connect(self.start_convert)
        btn_row.addStretch()
        btn_row.addWidget(self.convert_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        self.log.setPlaceholderText("转换日志将显示在这里...")
        layout.addWidget(self.log)

        layout.addStretch()

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)
            # Auto-set output path
            inp = Path(path)
            fmt = self.format_combo.currentText().lower()
            self.output_path.setText(str(inp.parent / f"{inp.stem}_converted.{fmt}"))

    def browse_output(self):
        fmt = self.format_combo.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(
            self, "保存转换后的文件", "",
            f"{fmt.upper()} 文件 (*.{fmt});;所有文件 (*)"
        )
        if path:
            self.output_path.setText(path)

    def on_format_changed(self, fmt):
        fmt = fmt.lower()
        if self.input_path.text():
            inp = Path(self.input_path.text())
            self.output_path.setText(str(inp.parent / f"{inp.stem}_converted.{fmt}"))
        # Enable/disable bitrate based on format
        self.bitrate_combo.setEnabled(fmt != "wav")

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def start_convert(self):
        if not PYDUB_AVAILABLE:
            self.add_log("❌ 错误: pydub 未安装。请运行 pip install pydub")
            return

        input_file = self.input_path.text().strip()
        output_file = self.output_path.text().strip()

        if not input_file or not os.path.exists(input_file):
            self.add_log("❌ 错误: 请选择有效的输入文件")
            return
        if not output_file:
            self.add_log("❌ 错误: 请设置输出路径")
            return

        self.convert_btn.setEnabled(False)
        self.progress.setValue(0)
        self.add_log(f"开始转换: {Path(input_file).name}")

        # Run conversion in a thread
        self.thread = threading.Thread(
            target=self._convert_thread,
            args=(input_file, output_file),
            daemon=True
        )
        self.thread.start()

    def _convert_thread(self, input_file, output_file):
        try:
            # Update progress
            QTimer.singleShot(0, lambda: self.progress.setValue(20))
            QTimer.singleShot(0, lambda: self.add_log("正在加载音频文件..."))

            audio = AudioSegment.from_file(input_file)

            QTimer.singleShot(0, lambda: self.progress.setValue(50))
            QTimer.singleShot(0, lambda: self.add_log("正在转换格式..."))

            fmt = Path(output_file).suffix.lstrip('.')
            export_kwargs = {}
            if fmt in ('mp3', 'aac', 'ogg'):
                export_kwargs['bitrate'] = self.bitrate_combo.currentText()
            if fmt == 'aac':
                fmt = 'adts'
            if self.samplerate_combo.currentText():
                export_kwargs['parameters'] = ['-ar', self.samplerate_combo.currentText()]

            audio.export(output_file, format=fmt, **export_kwargs)

            QTimer.singleShot(0, lambda: self.progress.setValue(100))
            QTimer.singleShot(0, lambda: self.add_log(f"✅ 转换完成: {Path(output_file).name}"))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_log(f"❌ 转换失败: {str(e)}"))
        finally:
            QTimer.singleShot(0, lambda: self.convert_btn.setEnabled(True))


# ============================================================
# Audio Trimmer Tab
# ============================================================
class AudioTrimmerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("✂️ 音频裁剪")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("按时间截取音频片段，精确到毫秒")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        input_row = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择音频文件...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_input)
        input_row.addWidget(self.input_path)
        input_row.addWidget(browse_btn)
        file_layout.addLayout(input_row)

        self.file_info = QLabel("未选择文件")
        self.file_info.setStyleSheet("color: #8888aa;")
        file_layout.addWidget(self.file_info)

        layout.addWidget(file_group)

        # Time selection
        time_group = QGroupBox("裁剪时间")
        time_layout = QGridLayout(time_group)

        time_layout.addWidget(QLabel("开始时间 (秒):"), 0, 0)
        self.start_time = QDoubleSpinBox()
        self.start_time.setRange(0, 99999)
        self.start_time.setDecimals(3)
        self.start_time.setSingleStep(0.5)
        time_layout.addWidget(self.start_time, 0, 1)

        time_layout.addWidget(QLabel("结束时间 (秒):"), 1, 0)
        self.end_time = QDoubleSpinBox()
        self.end_time.setRange(0, 99999)
        self.end_time.setDecimals(3)
        self.end_time.setSingleStep(0.5)
        self.end_time.setValue(30)
        time_layout.addWidget(self.end_time, 1, 1)

        self.duration_label = QLabel("选取时长: 30.000 秒")
        self.duration_label.setStyleSheet("color: #667eea; font-weight: bold;")
        time_layout.addWidget(self.duration_label, 2, 0, 1, 2)

        self.start_time.valueChanged.connect(self.update_duration)
        self.end_time.valueChanged.connect(self.update_duration)

        time_layout.setColumnStretch(1, 1)
        layout.addWidget(time_group)

        # Output
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出路径...")
        output_btn = QPushButton("浏览")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(output_btn)
        output_layout.addLayout(output_row)

        layout.addWidget(output_group)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Trim button
        btn_row = QHBoxLayout()
        self.trim_btn = QPushButton("✂️ 开始裁剪")
        self.trim_btn.setFixedHeight(45)
        self.trim_btn.clicked.connect(self.start_trim)
        btn_row.addStretch()
        btn_row.addWidget(self.trim_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setPlaceholderText("裁剪日志...")
        layout.addWidget(self.log)

        layout.addStretch()

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)
            if PYDUB_AVAILABLE:
                try:
                    audio = AudioSegment.from_file(path)
                    duration = len(audio) / 1000.0
                    self.end_time.setValue(duration)
                    self.file_info.setText(
                        f"时长: {duration:.2f}秒 | 采样率: {audio.frame_rate}Hz | 声道: {audio.channels}"
                    )
                except Exception as e:
                    self.file_info.setText(f"读取失败: {e}")
            inp = Path(path)
            self.output_path.setText(str(inp.parent / f"{inp.stem}_trimmed{inp.suffix}"))

    def browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存裁剪后的文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg);;所有文件 (*)"
        )
        if path:
            self.output_path.setText(path)

    def update_duration(self):
        start = self.start_time.value()
        end = self.end_time.value()
        dur = max(0, end - start)
        self.duration_label.setText(f"选取时长: {dur:.3f} 秒")

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def start_trim(self):
        if not PYDUB_AVAILABLE:
            self.add_log("❌ 错误: pydub 未安装")
            return

        input_file = self.input_path.text().strip()
        output_file = self.output_path.text().strip()

        if not input_file or not os.path.exists(input_file):
            self.add_log("❌ 请选择有效的输入文件")
            return
        if not output_file:
            self.add_log("❌ 请设置输出路径")
            return

        self.trim_btn.setEnabled(False)
        self.add_log("开始裁剪...")

        self.thread = threading.Thread(
            target=self._trim_thread,
            args=(input_file, output_file),
            daemon=True
        )
        self.thread.start()

    def _trim_thread(self, input_file, output_file):
        try:
            QTimer.singleShot(0, lambda: self.progress.setValue(20))
            audio = AudioSegment.from_file(input_file)

            start_ms = int(self.start_time.value() * 1000)
            end_ms = int(self.end_time.value() * 1000)

            QTimer.singleShot(0, lambda: self.progress.setValue(50))
            trimmed = audio[start_ms:end_ms]

            QTimer.singleShot(0, lambda: self.progress.setValue(80))
            trimmed.export(output_file, format=Path(output_file).suffix.lstrip('.'))

            QTimer.singleShot(0, lambda: self.progress.setValue(100))
            QTimer.singleShot(0, lambda: self.add_log(f"✅ 裁剪完成: {Path(output_file).name}"))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_log(f"❌ 裁剪失败: {str(e)}"))
        finally:
            QTimer.singleShot(0, lambda: self.trim_btn.setEnabled(True))


# ============================================================
# Audio Merger Tab
# ============================================================
class AudioMergerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.files = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🔗 音频合并")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("将多个音频文件合并为一个文件")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File list
        list_group = QGroupBox("文件列表 (按顺序合并)")
        list_layout = QVBoxLayout(list_group)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        list_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加文件")
        add_btn.clicked.connect(self.add_files)
        remove_btn = QPushButton("➖ 移除选中")
        remove_btn.setProperty("class", "secondary")
        remove_btn.setStyleSheet("background-color: #1a1a2e; border: 1px solid #3a3a5a;")
        remove_btn.clicked.connect(self.remove_file)
        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setProperty("class", "danger")
        clear_btn.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);")
        clear_btn.clicked.connect(self.clear_files)
        up_btn = QPushButton("⬆️ 上移")
        up_btn.setProperty("class", "secondary")
        up_btn.setStyleSheet("background-color: #1a1a2e; border: 1px solid #3a3a5a;")
        up_btn.clicked.connect(self.move_up)
        down_btn = QPushButton("⬇️ 下移")
        down_btn.setProperty("class", "secondary")
        down_btn.setStyleSheet("background-color: #1a1a2e; border: 1px solid #3a3a5a;")
        down_btn.clicked.connect(self.move_down)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(up_btn)
        btn_row.addWidget(down_btn)
        list_layout.addLayout(btn_row)

        self.file_count_label = QLabel("已添加 0 个文件")
        self.file_count_label.setStyleSheet("color: #667eea;")
        list_layout.addWidget(self.file_count_label)

        layout.addWidget(list_group)

        # Output
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出路径...")
        output_btn = QPushButton("浏览")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(output_btn)
        output_layout.addLayout(output_row)

        layout.addWidget(output_group)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Merge button
        btn_row2 = QHBoxLayout()
        self.merge_btn = QPushButton("🔗 开始合并")
        self.merge_btn.setFixedHeight(45)
        self.merge_btn.clicked.connect(self.start_merge)
        btn_row2.addStretch()
        btn_row2.addWidget(self.merge_btn)
        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setPlaceholderText("合并日志...")
        layout.addWidget(self.log)

        layout.addStretch()

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a);;所有文件 (*)"
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_list.addItem(Path(p).name)
        self.file_count_label.setText(f"已添加 {len(self.files)} 个文件")

    def remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            self.files.pop(row)
            self.file_list.takeItem(row)
            self.file_count_label.setText(f"已添加 {len(self.files)} 个文件")

    def clear_files(self):
        self.files.clear()
        self.file_list.clear()
        self.file_count_label.setText("已添加 0 个文件")

    def move_up(self):
        row = self.file_list.currentRow()
        if row > 0:
            self.files[row], self.files[row - 1] = self.files[row - 1], self.files[row]
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentRow(row - 1)

    def move_down(self):
        row = self.file_list.currentRow()
        if row < len(self.files) - 1:
            self.files[row], self.files[row + 1] = self.files[row + 1], self.files[row]
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentRow(row + 1)

    def browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存合并后的文件", "",
            "MP3 文件 (*.mp3);;WAV 文件 (*.wav);;FLAC 文件 (*.flac);;所有文件 (*)"
        )
        if path:
            self.output_path.setText(path)

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def start_merge(self):
        if not PYDUB_AVAILABLE:
            self.add_log("❌ 错误: pydub 未安装")
            return

        if len(self.files) < 2:
            self.add_log("❌ 请至少添加2个文件")
            return

        output_file = self.output_path.text().strip()
        if not output_file:
            self.add_log("❌ 请设置输出路径")
            return

        self.merge_btn.setEnabled(False)
        self.add_log(f"开始合并 {len(self.files)} 个文件...")

        self.thread = threading.Thread(
            target=self._merge_thread,
            args=(list(self.files), output_file),
            daemon=True
        )
        self.thread.start()

    def _merge_thread(self, files, output_file):
        try:
            merged = AudioSegment.empty()
            total = len(files)

            for i, f in enumerate(files):
                QTimer.singleShot(0, lambda i=i: self.add_log(f"加载: {Path(files[i]).name}"))
                segment = AudioSegment.from_file(f)
                merged += segment
                progress = int((i + 1) / total * 80)
                QTimer.singleShot(0, lambda p=progress: self.progress.setValue(p))

            QTimer.singleShot(0, lambda: self.progress.setValue(90))
            QTimer.singleShot(0, lambda: self.add_log("正在导出..."))

            merged.export(output_file, format=Path(output_file).suffix.lstrip('.'))

            QTimer.singleShot(0, lambda: self.progress.setValue(100))
            QTimer.singleShot(0, lambda: self.add_log(f"✅ 合并完成: {Path(output_file).name}"))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_log(f"❌ 合并失败: {str(e)}"))
        finally:
            QTimer.singleShot(0, lambda: self.merge_btn.setEnabled(True))


# ============================================================
# Volume Adjuster Tab
# ============================================================
class VolumeAdjusterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🔊 音量调节")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("增大或减小音频音量，支持精确分贝控制")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        input_row = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择音频文件...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_input)
        input_row.addWidget(self.input_path)
        input_row.addWidget(browse_btn)
        file_layout.addLayout(input_row)

        layout.addWidget(file_group)

        # Volume control
        vol_group = QGroupBox("音量设置")
        vol_layout = QVBoxLayout(vol_group)

        # Slider row
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("🔊"))

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(-30, 30)
        self.volume_slider.setValue(0)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(5)
        self.volume_slider.valueChanged.connect(self.on_slider_changed)
        slider_row.addWidget(self.volume_slider)

        slider_row.addWidget(QLabel("🔊🔊🔊"))
        vol_layout.addLayout(slider_row)

        # dB display
        db_row = QHBoxLayout()
        db_row.addStretch()
        self.db_label = QLabel("0 dB (原始音量)")
        self.db_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #667eea;")
        db_row.addWidget(self.db_label)
        db_row.addStretch()
        vol_layout.addLayout(db_row)

        # Presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设:"))
        presets = [
            ("静音", -30), ("降低", -12), ("稍低", -6),
            ("原始", 0), ("稍高", 6), ("增大", 12), ("最大", 20)
        ]
        for name, val in presets:
            btn = QPushButton(name)
            btn.setProperty("class", "secondary")
            btn.setStyleSheet("background-color: #1a1a2e; border: 1px solid #3a3a5a; padding: 6px 12px;")
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, v=val: self.volume_slider.setValue(v))
            preset_layout.addWidget(btn)
        vol_layout.addLayout(preset_layout)

        # Custom dB input
        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("自定义分贝:"))
        self.custom_db = QDoubleSpinBox()
        self.custom_db.setRange(-60, 60)
        self.custom_db.setDecimals(1)
        self.custom_db.setSuffix(" dB")
        self.custom_db.setValue(0)
        apply_btn = QPushButton("应用")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(lambda: self.volume_slider.setValue(int(self.custom_db.value())))
        custom_row.addWidget(self.custom_db)
        custom_row.addWidget(apply_btn)
        vol_layout.addLayout(custom_row)

        layout.addWidget(vol_group)

        # Output
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出路径...")
        output_btn = QPushButton("浏览")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(output_btn)
        output_layout.addLayout(output_row)

        layout.addWidget(output_group)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Apply button
        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("🔊 应用音量调节")
        self.apply_btn.setFixedHeight(45)
        self.apply_btn.clicked.connect(self.start_adjust)
        btn_row.addStretch()
        btn_row.addWidget(self.apply_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(80)
        self.log.setPlaceholderText("操作日志...")
        layout.addWidget(self.log)

        layout.addStretch()

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)
            inp = Path(path)
            self.output_path.setText(str(inp.parent / f"{inp.stem}_volume{inp.suffix}"))

    def browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg);;所有文件 (*)"
        )
        if path:
            self.output_path.setText(path)

    def on_slider_changed(self, value):
        self.custom_db.setValue(value)
        if value == 0:
            self.db_label.setText("0 dB (原始音量)")
            self.db_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #667eea;")
        elif value > 0:
            self.db_label.setText(f"+{value} dB (增大)")
            self.db_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2ecc71;")
        else:
            self.db_label.setText(f"{value} dB (降低)")
            self.db_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def start_adjust(self):
        if not PYDUB_AVAILABLE:
            self.add_log("❌ 错误: pydub 未安装")
            return

        input_file = self.input_path.text().strip()
        output_file = self.output_path.text().strip()

        if not input_file or not os.path.exists(input_file):
            self.add_log("❌ 请选择有效的输入文件")
            return
        if not output_file:
            self.add_log("❌ 请设置输出路径")
            return

        self.apply_btn.setEnabled(False)
        dB = self.volume_slider.value()
        self.add_log(f"正在调整音量 ({dB:+d} dB)...")

        self.thread = threading.Thread(
            target=self._adjust_thread,
            args=(input_file, output_file, dB),
            daemon=True
        )
        self.thread.start()

    def _adjust_thread(self, input_file, output_file, dB):
        try:
            QTimer.singleShot(0, lambda: self.progress.setValue(30))
            audio = AudioSegment.from_file(input_file)

            QTimer.singleShot(0, lambda: self.progress.setValue(60))
            adjusted = audio.apply_gain(dB)

            QTimer.singleShot(0, lambda: self.progress.setValue(80))
            adjusted.export(output_file, format=Path(output_file).suffix.lstrip('.'))

            QTimer.singleShot(0, lambda: self.progress.setValue(100))
            QTimer.singleShot(0, lambda: self.add_log(f"✅ 音量调节完成: {Path(output_file).name}"))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_log(f"❌ 调节失败: {str(e)}"))
        finally:
            QTimer.singleShot(0, lambda: self.apply_btn.setEnabled(True))


# ============================================================
# Audio Info Tab
# ============================================================
class AudioInfoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("ℹ️ 音频信息")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("查看音频文件的详细元数据信息")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        input_row = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择音频文件...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_input)
        input_row.addWidget(self.input_path)
        input_row.addWidget(browse_btn)
        file_layout.addLayout(input_row)

        analyze_btn = QPushButton("🔍 分析音频")
        analyze_btn.setFixedHeight(40)
        analyze_btn.clicked.connect(self.analyze)
        file_layout.addWidget(analyze_btn)

        layout.addWidget(file_group)

        # Info display
        info_group = QGroupBox("音频详情")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("点击「分析音频」查看文件信息...")
        self.info_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)
        layout.addStretch()

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)

    def analyze(self):
        if not PYDUB_AVAILABLE:
            self.info_text.setPlainText("❌ 错误: pydub 未安装。请运行:\npip install pydub")
            return

        input_file = self.input_path.text().strip()
        if not input_file or not os.path.exists(input_file):
            self.info_text.setPlainText("❌ 请选择有效的音频文件")
            return

        try:
            audio = AudioSegment.from_file(input_file)
            file_size = os.path.getsize(input_file)
            duration = len(audio) / 1000.0
            bitrate = (file_size * 8) / duration / 1000 if duration > 0 else 0

            info = f"""
╔══════════════════════════════════════════════════════════════╗
║                    📁 音频文件信息                            ║
╚══════════════════════════════════════════════════════════════╝

  📄 文件名:     {Path(input_file).name}
  📂 文件路径:   {input_file}
  📊 文件大小:   {file_size / 1024 / 1024:.2f} MB ({file_size:,} bytes)
  📋 文件格式:   {Path(input_file).suffix.upper().lstrip('.')}

╔══════════════════════════════════════════════════════════════╗
║                    🎵 音频参数                               ║
╚══════════════════════════════════════════════════════════════╝

  ⏱️ 时长:       {int(duration // 3600):02d}:{int((duration % 3600) // 60):02d}:{duration % 60:06.3f}
                ({duration:.3f} 秒)

  📡 比特率:     {bitrate:.1f} kbps
  🎤 采样率:     {audio.frame_rate:,} Hz
  🔊 声道数:     {audio.channels} ({'单声道' if audio.channels == 1 else '立体声' if audio.channels == 2 else f'{audio.channels}声道'})
  📐 采样位深:   {audio.sample_width * 8} bit
  📦 帧数:       {audio.frame_count():,}
  📏 帧大小:     {audio.frame_width} bytes

╔══════════════════════════════════════════════════════════════╗
║                    📊 音频统计                               ║
╚══════════════════════════════════════════════════════════════╝

  📈 最大振幅:   {audio.max}
  📉 RMS 响度:   {audio.rms}
  🔇 静音阈值:   {audio.dBFS:.1f} dBFS
""".strip()

            self.info_text.setPlainText(info)

        except Exception as e:
            self.info_text.setPlainText(f"❌ 分析失败: {str(e)}")


# ============================================================
# Batch Convert Tab
# ============================================================
class BatchConvertTab(QWidget):
    def __init__(self):
        super().__init__()
        self.files = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("📦 批量转换")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("批量转换多个音频文件，统一输出格式")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # File list
        list_group = QGroupBox("文件列表")
        list_layout = QVBoxLayout(list_group)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        list_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加文件")
        add_btn.clicked.connect(self.add_files)
        add_dir_btn = QPushButton("📁 添加文件夹")
        add_dir_btn.setProperty("class", "secondary")
        add_dir_btn.setStyleSheet("background-color: #1a1a2e; border: 1px solid #3a3a5a;")
        add_dir_btn.clicked.connect(self.add_directory)
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);")
        clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(add_dir_btn)
        btn_row.addWidget(clear_btn)
        list_layout.addLayout(btn_row)

        self.file_count = QLabel("已添加 0 个文件")
        self.file_count.setStyleSheet("color: #667eea;")
        list_layout.addWidget(self.file_count)

        layout.addWidget(list_group)

        # Settings
        settings_group = QGroupBox("转换设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "WAV", "FLAC", "OGG", "AAC"])
        settings_layout.addWidget(self.format_combo, 0, 1)

        settings_layout.addWidget(QLabel("比特率:"), 1, 0)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentText("192k")
        settings_layout.addWidget(self.bitrate_combo, 1, 1)

        settings_layout.addWidget(QLabel("输出目录:"), 2, 0)
        output_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("选择输出目录...")
        output_btn = QPushButton("浏览")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.browse_output_dir)
        output_row.addWidget(self.output_dir)
        output_row.addWidget(output_btn)
        settings_layout.addLayout(output_row, 2, 1)

        settings_layout.setColumnStretch(1, 1)
        layout.addWidget(settings_group)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #8888aa;")
        layout.addWidget(self.status_label)

        # Convert button
        btn_row2 = QHBoxLayout()
        self.convert_btn = QPushButton("📦 开始批量转换")
        self.convert_btn.setFixedHeight(45)
        self.convert_btn.clicked.connect(self.start_batch_convert)
        btn_row2.addStretch()
        btn_row2.addWidget(self.convert_btn)
        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setPlaceholderText("批量转换日志...")
        layout.addWidget(self.log)

        layout.addStretch()

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma);;所有文件 (*)"
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_list.addItem(Path(p).name)
        self.file_count.setText(f"已添加 {len(self.files)} 个文件")

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma'}
            count = 0
            for f in Path(dir_path).iterdir():
                if f.suffix.lower() in audio_exts and str(f) not in self.files:
                    self.files.append(str(f))
                    self.file_list.addItem(f.name)
                    count += 1
            self.file_count.setText(f"已添加 {len(self.files)} 个文件")
            self.add_log(f"从文件夹添加了 {count} 个文件")

    def clear_files(self):
        self.files.clear()
        self.file_list.clear()
        self.file_count.setText("已添加 0 个文件")

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir.setText(dir_path)

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def start_batch_convert(self):
        if not PYDUB_AVAILABLE:
            self.add_log("❌ 错误: pydub 未安装")
            return

        if not self.files:
            self.add_log("❌ 请添加要转换的文件")
            return

        output_dir = self.output_dir.text().strip()
        if not output_dir:
            self.add_log("❌ 请选择输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)

        self.convert_btn.setEnabled(False)
        self.add_log(f"开始批量转换 {len(self.files)} 个文件...")

        self.thread = threading.Thread(
            target=self._batch_thread,
            args=(list(self.files), output_dir),
            daemon=True
        )
        self.thread.start()

    def _batch_thread(self, files, output_dir):
        try:
            total = len(files)
            success = 0
            failed = 0
            fmt = self.format_combo.currentText().lower()
            bitrate = self.bitrate_combo.currentText()

            for i, f in enumerate(files):
                try:
                    name = Path(f).stem
                    output_file = os.path.join(output_dir, f"{name}.{fmt}")

                    QTimer.singleShot(0, lambda f=f: self.add_log(f"转换: {Path(f).name}"))
                    QTimer.singleShot(0, lambda i=i: self.status_label.setText(f"正在处理 {i+1}/{total}..."))

                    audio = AudioSegment.from_file(f)
                    export_fmt = 'adts' if fmt == 'aac' else fmt
                    kwargs = {}
                    if fmt in ('mp3', 'aac', 'ogg'):
                        kwargs['bitrate'] = bitrate
                    audio.export(output_file, format=export_fmt, **kwargs)

                    success += 1
                except Exception as e:
                    failed += 1
                    QTimer.singleShot(0, lambda f=f, e=e: self.add_log(f"❌ 失败: {Path(f).name} - {e}"))

                progress = int((i + 1) / total * 100)
                QTimer.singleShot(0, lambda p=progress: self.progress.setValue(p))

            QTimer.singleShot(0, lambda: self.status_label.setText(
                f"完成! 成功: {success}, 失败: {failed}"
            ))
            QTimer.singleShot(0, lambda: self.add_log(
                f"✅ 批量转换完成! 成功: {success}, 失败: {failed}"
            ))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_log(f"❌ 批量转换失败: {str(e)}"))
        finally:
            QTimer.singleShot(0, lambda: self.convert_btn.setEnabled(True))


# ============================================================
# Audio Recorder Tab
# ============================================================
class AudioRecorderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recorded_frames = []
        self.sample_rate = 44100
        self.channels = 1
        self.recording_start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🎙️ 音频录制")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout.addWidget(header)

        desc = QLabel("从麦克风录制音频，支持多种输出格式")
        desc.setStyleSheet("font-size: 12px; color: #6666aa; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Device selection
        device_group = QGroupBox("录制设备")
        device_layout = QVBoxLayout(device_group)

        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("输入设备:"))
        self.device_combo = QComboBox()
        self.refresh_devices()
        device_row.addWidget(self.device_combo)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(40)
        refresh_btn.clicked.connect(self.refresh_devices)
        device_row.addWidget(refresh_btn)
        device_layout.addLayout(device_row)

        # Settings
        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("采样率:"))
        self.sr_combo = QComboBox()
        self.sr_combo.addItems(["22050", "44100", "48000", "96000"])
        self.sr_combo.setCurrentText("44100")
        self.sr_combo.currentTextChanged.connect(lambda t: setattr(self, 'sample_rate', int(t)))
        settings_row.addWidget(self.sr_combo)

        settings_row.addWidget(QLabel("声道:"))
        self.ch_combo = QComboBox()
        self.ch_combo.addItems(["单声道 (1)", "立体声 (2)"])
        self.ch_combo.currentIndexChanged.connect(lambda i: setattr(self, 'channels', i + 1))
        settings_row.addWidget(self.ch_combo)
        device_layout.addLayout(settings_row)

        layout.addWidget(device_group)

        # Recording display
        rec_group = QGroupBox("录制控制")
        rec_layout = QVBoxLayout(rec_group)

        # Time display
        time_row = QHBoxLayout()
        time_row.addStretch()
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
            font-family: 'Consolas', 'Courier New', monospace;
            padding: 20px;
        """)
        time_row.addWidget(self.time_label)
        time_row.addStretch()
        rec_layout.addLayout(time_row)

        # Status
        self.status_label = QLabel("⚫ 就绪")
        self.status_label.setStyleSheet("font-size: 16px; color: #8888aa;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_layout.addWidget(self.status_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.record_btn = QPushButton("🎙️ 开始录制")
        self.record_btn.setFixedSize(180, 55)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff5555, stop:1 #dd3333);
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        btn_row.addWidget(self.record_btn)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setFixedSize(120, 55)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        btn_row.addWidget(self.stop_btn)

        btn_row.addStretch()
        rec_layout.addLayout(btn_row)

        layout.addWidget(rec_group)

        # Output settings
        output_group = QGroupBox("保存设置")
        output_layout = QVBoxLayout(output_group)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("保存格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["WAV", "MP3", "FLAC", "OGG"])
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch()
        output_layout.addLayout(fmt_row)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择保存路径...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(browse_btn)
        output_layout.addLayout(output_row)

        save_btn = QPushButton("💾 保存录音")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self.save_recording)
        output_layout.addWidget(save_btn)

        layout.addWidget(output_group)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(80)
        self.log.setPlaceholderText("录制日志...")
        layout.addWidget(self.log)

        layout.addStretch()

    def refresh_devices(self):
        self.device_combo.clear()
        if SOUNDDEVICE_AVAILABLE:
            try:
                devices = sd.query_devices()
                for i, d in enumerate(devices):
                    if d['max_input_channels'] > 0:
                        self.device_combo.addItem(f"{d['name']}", i)
            except Exception:
                self.device_combo.addItem("默认设备", -1)
        else:
            self.device_combo.addItem("sounddevice 未安装", -1)

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {msg}")

    def toggle_recording(self):
        if not SOUNDDEVICE_AVAILABLE:
            self.add_log("❌ 错误: sounddevice 未安装")
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.recorded_frames = []
        self.recording_start_time = time.time()

        self.record_btn.setText("🎙️ 录制中...")
        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("🔴 正在录制...")
        self.status_label.setStyleSheet("font-size: 16px; color: #e74c3c;")

        self.timer.start(100)

        device_idx = self.device_combo.currentData()
        if device_idx is None or device_idx < 0:
            device_idx = None

        def callback(indata, frames, time_info, status):
            self.recorded_frames.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_idx,
                callback=callback,
                blocksize=1024
            )
            self.stream.start()
            self.add_log(f"开始录制 (采样率: {self.sample_rate}Hz, 声道: {self.channels})")
        except Exception as e:
            self.add_log(f"❌ 录制失败: {e}")
            self.is_recording = False
            self.record_btn.setText("🎙️ 开始录制")
            self.record_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("⚫ 就绪")
            self.status_label.setStyleSheet("font-size: 16px; color: #8888aa;")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.timer.stop()

        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass

        self.record_btn.setText("🎙️ 开始录制")
        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⚫ 已停止")
        self.status_label.setStyleSheet("font-size: 16px; color: #8888aa;")

        if self.recorded_frames:
            duration = len(self.recorded_frames) * 1024 / self.sample_rate
            self.add_log(f"录制完成，时长: {duration:.1f}秒")

            # Auto-set output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fmt = self.format_combo.currentText().lower()
            default_path = os.path.join(os.path.expanduser("~"), "Desktop", f"recording_{timestamp}.{fmt}")
            self.output_path.setText(default_path)
        else:
            self.add_log("录制完成（无数据）")

    def update_time(self):
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def browse_output(self):
        fmt = self.format_combo.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(
            self, "保存录音", "",
            f"{fmt.upper()} 文件 (*.{fmt});;所有文件 (*)"
        )
        if path:
            self.output_path.setText(path)

    def save_recording(self):
        if not self.recorded_frames:
            self.add_log("❌ 没有录音数据，请先录制")
            return

        output_file = self.output_path.text().strip()
        if not output_file:
            self.add_log("❌ 请设置保存路径")
            return

        try:
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            fmt = Path(output_file).suffix.lstrip('.')

            if fmt == 'wav' or not PYDUB_AVAILABLE:
                sf.write(output_file, audio_data, self.sample_rate)
            else:
                # Use pydub for other formats
                temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                sf.write(temp_wav.name, audio_data, self.sample_rate)
                temp_wav.close()

                audio = AudioSegment.from_wav(temp_wav.name)
                export_fmt = 'adts' if fmt == 'aac' else fmt
                audio.export(output_file, format=export_fmt)

                os.unlink(temp_wav.name)

            self.add_log(f"✅ 录音已保存: {Path(output_file).name}")
        except Exception as e:
            self.add_log(f"❌ 保存失败: {str(e)}")


# ============================================================
# Main Window
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioTools - 音频处理工具箱 v1.0")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header bar
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:0.5 #764ba2, stop:1 #667eea);
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("🎵 AudioTools")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent;")
        header_layout.addWidget(title)

        subtitle = QLabel("音频处理工具箱")
        subtitle.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        version = QLabel("v1.0.0")
        version.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.6); background: transparent;")
        header_layout.addWidget(version)

        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)

        self.tabs.addTab(AudioConverterTab(), "🎵 格式转换")
        self.tabs.addTab(AudioTrimmerTab(), "✂️ 音频裁剪")
        self.tabs.addTab(AudioMergerTab(), "🔗 音频合并")
        self.tabs.addTab(VolumeAdjusterTab(), "🔊 音量调节")
        self.tabs.addTab(AudioInfoTab(), "ℹ️ 音频信息")
        self.tabs.addTab(BatchConvertTab(), "📦 批量转换")
        self.tabs.addTab(AudioRecorderTab(), "🎙️ 音频录制")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("就绪 | 音频处理工具箱 v1.0")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #0d0d1a;
                border-top: 1px solid #2a2a3a;
                color: #8888aa;
                font-size: 12px;
            }
        """)

        # Check dependencies
        self.check_dependencies()

    def check_dependencies(self):
        issues = []
        if not PYDUB_AVAILABLE:
            issues.append("pydub 未安装")
        if not SOUNDDEVICE_AVAILABLE:
            issues.append("sounddevice 未安装")

        if issues:
            self.statusBar().showMessage(f"⚠️ 缺少依赖: {', '.join(issues)} | 请运行: pip install pydub sounddevice")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Apply dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d0d1a"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#111122"))
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

    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
