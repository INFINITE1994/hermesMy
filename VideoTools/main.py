#!/usr/bin/env python3
"""
VideoTools - 视频处理工具箱
功能：格式转换、裁剪、合并、压缩、音频提取、视频信息查看、批量转换
"""

import sys
import os
import time
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QFileDialog, QComboBox,
    QLineEdit, QProgressBar, QTextEdit, QGroupBox, QGridLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QListWidget, QListWidgetItem,
    QFrame, QScrollArea, QSizePolicy, QStyle
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QLinearGradient, QPainter, QBrush

# ─────────────────────── 全局样式表 ───────────────────────
STYLESHEET = """
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
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
    margin: 2px;
    border-radius: 6px 6px 0 0;
    font-size: 13px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}
QTabBar::tab:hover:!selected {
    background-color: #1a1a2e;
    color: #aaaacc;
}
QGroupBox {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
    font-size: 14px;
    color: #9999bb;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #667eea;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b8ef8, stop:1 #8b5fc0);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #556ddb, stop:1 #653a91);
}
QPushButton:disabled {
    background: #2a2a3a;
    color: #555566;
}
QPushButton.secondary {
    background: #1a1a2e;
    border: 1px solid #2a2a3a;
    color: #8888aa;
}
QPushButton.secondary:hover {
    background: #222236;
    border: 1px solid #667eea;
    color: #aaaacc;
}
QPushButton.danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
}
QPushButton.danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b5a, stop:1 #d44637);
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #667eea;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    color: #e0e0e0;
    selection-background-color: #667eea;
}
QProgressBar {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    text-align: center;
    color: white;
    font-weight: bold;
    min-height: 24px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 5px;
}
QTextEdit {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px;
    color: #e0e0e0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}
QListWidget {
    background-color: #0d0d1a;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 4px;
    color: #e0e0e0;
}
QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}
QListWidget::item:hover:!selected {
    background-color: #1a1a2e;
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
    color: #8888aa;
    font-size: 12px;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background-color: #2a2a3a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


# ─────────────────────── 工作线程基类 ───────────────────────
class WorkerThread(QThread):
    """通用工作线程"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_ok = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False


class ConvertWorker(WorkerThread):
    """视频格式转换线程"""
    def __init__(self, input_path, output_path, target_format):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.target_format = target_format

    def run(self):
        try:
            from moviepy.editor import VideoFileClip
            self.log.emit(f"正在加载视频: {os.path.basename(self.input_path)}")
            self.progress.emit(10)
            clip = VideoFileClip(self.input_path)
            self.log.emit(f"视频信息: {clip.size[0]}x{clip.size[1]}, {clip.duration:.1f}秒")
            self.progress.emit(30)
            self.log.emit(f"正在转换为 {self.target_format} 格式...")
            clip.write_videofile(
                self.output_path,
                codec='libx264' if self.target_format in ['mp4', 'mkv', 'mov'] else None,
                audio_codec='aac' if self.target_format in ['mp4', 'mov'] else 'libvorbis',
                logger=None
            )
            self.progress.emit(100)
            clip.close()
            self.finished_ok.emit(True, f"转换完成: {self.output_path}")
        except Exception as e:
            self.finished_ok.emit(False, f"转换失败: {str(e)}")


class TrimWorker(WorkerThread):
    """视频裁剪线程"""
    def __init__(self, input_path, output_path, start_time, end_time):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.start_time = start_time
        self.end_time = end_time

    def run(self):
        try:
            from moviepy.editor import VideoFileClip
            self.log.emit(f"正在加载视频: {os.path.basename(self.input_path)}")
            self.progress.emit(10)
            clip = VideoFileClip(self.input_path)
            self.log.emit(f"裁剪范围: {self.start_time:.1f}s - {self.end_time:.1f}s")
            self.progress.emit(30)
            trimmed = clip.subclip(self.start_time, self.end_time)
            self.log.emit("正在保存裁剪后的视频...")
            self.progress.emit(50)
            trimmed.write_videofile(self.output_path, logger=None)
            self.progress.emit(100)
            trimmed.close()
            clip.close()
            self.finished_ok.emit(True, f"裁剪完成: {self.output_path}")
        except Exception as e:
            self.finished_ok.emit(False, f"裁剪失败: {str(e)}")


class MergeWorker(WorkerThread):
    """视频合并线程"""
    def __init__(self, input_paths, output_path):
        super().__init__()
        self.input_paths = input_paths
        self.output_path = output_path

    def run(self):
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            clips = []
            total = len(self.input_paths)
            for i, path in enumerate(self.input_paths):
                self.log.emit(f"正在加载视频 [{i+1}/{total}]: {os.path.basename(path)}")
                self.progress.emit(int((i / total) * 60))
                clip = VideoFileClip(path)
                clips.append(clip)
            self.log.emit(f"正在合并 {total} 个视频...")
            self.progress.emit(70)
            final = concatenate_videoclips(clips, method="compose")
            self.log.emit("正在保存合并后的视频...")
            self.progress.emit(85)
            final.write_videofile(self.output_path, logger=None)
            self.progress.emit(100)
            for c in clips:
                c.close()
            final.close()
            self.finished_ok.emit(True, f"合并完成: {self.output_path}")
        except Exception as e:
            self.finished_ok.emit(False, f"合并失败: {str(e)}")


class CompressWorker(WorkerThread):
    """视频压缩线程"""
    def __init__(self, input_path, output_path, quality):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.quality = quality

    def run(self):
        try:
            from moviepy.editor import VideoFileClip
            self.log.emit(f"正在加载视频: {os.path.basename(self.input_path)}")
            self.progress.emit(10)
            clip = VideoFileClip(self.input_path)
            bitrate_val = f"{int(2000 * self.quality / 100)}k"
            self.log.emit(f"压缩质量: {self.quality}%, 目标码率: {bitrate_val}")
            self.progress.emit(30)
            self.log.emit("正在压缩视频...")
            clip.write_videofile(
                self.output_path,
                bitrate=bitrate_val,
                audio_bitrate="128k",
                logger=None
            )
            self.progress.emit(100)
            clip.close()
            self.finished_ok.emit(True, f"压缩完成: {self.output_path}")
        except Exception as e:
            self.finished_ok.emit(False, f"压缩失败: {str(e)}")


class AudioExtractWorker(WorkerThread):
    """音频提取线程"""
    def __init__(self, input_path, output_path, audio_format):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.audio_format = audio_format

    def run(self):
        try:
            from moviepy.editor import VideoFileClip
            self.log.emit(f"正在加载视频: {os.path.basename(self.input_path)}")
            self.progress.emit(20)
            clip = VideoFileClip(self.input_path)
            self.log.emit("正在提取音频...")
            self.progress.emit(50)
            audio = clip.audio
            if audio is None:
                self.finished_ok.emit(False, "该视频不包含音频轨道")
                return
            codec = 'libmp3lame' if self.audio_format == 'mp3' else None
            audio.write_audiofile(self.output_path, codec=codec, logger=None)
            self.progress.emit(100)
            audio.close()
            clip.close()
            self.finished_ok.emit(True, f"音频提取完成: {self.output_path}")
        except Exception as e:
            self.finished_ok.emit(False, f"音频提取失败: {str(e)}")


class BatchConvertWorker(WorkerThread):
    """批量转换线程"""
    def __init__(self, input_paths, output_dir, target_format):
        super().__init__()
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.target_format = target_format

    def run(self):
        try:
            from moviepy.editor import VideoFileClip
            total = len(self.input_paths)
            success_count = 0
            for i, path in enumerate(self.input_paths):
                if not self._running:
                    self.finished_ok.emit(False, "批量转换已取消")
                    return
                name = Path(path).stem
                out = os.path.join(self.output_dir, f"{name}.{self.target_format}")
                self.log.emit(f"[{i+1}/{total}] 正在转换: {os.path.basename(path)}")
                self.progress.emit(int((i / total) * 100))
                try:
                    clip = VideoFileClip(path)
                    clip.write_videofile(
                        out,
                        codec='libx264' if self.target_format in ['mp4', 'mkv', 'mov'] else None,
                        audio_codec='aac' if self.target_format in ['mp4', 'mov'] else 'libvorbis',
                        logger=None
                    )
                    clip.close()
                    success_count += 1
                    self.log.emit(f"  ✓ 转换成功: {out}")
                except Exception as e:
                    self.log.emit(f"  ✗ 转换失败: {str(e)}")
            self.progress.emit(100)
            self.finished_ok.emit(True, f"批量转换完成: {success_count}/{total} 成功")
        except Exception as e:
            self.finished_ok.emit(False, f"批量转换失败: {str(e)}")


# ─────────────────────── UI 辅助函数 ───────────────────────
def create_file_selector(parent, label_text, file_filter="所有文件 (*)", is_dir=False):
    """创建文件选择行"""
    layout = QHBoxLayout()
    label = QLabel(label_text)
    label.setFixedWidth(90)
    line_edit = QLineEdit()
    line_edit.setReadOnly(True)
    line_edit.setPlaceholderText("请选择文件...")
    btn = QPushButton("浏览")
    btn.setFixedWidth(80)
    btn.setProperty("class", "secondary")
    btn.setStyleSheet("""
        QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                       padding: 8px 16px; border-radius: 6px; font-weight: bold; }
        QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
    """)
    def browse():
        if is_dir:
            path = QFileDialog.getExistingDirectory(parent, "选择文件夹")
        else:
            path, _ = QFileDialog.getOpenFileName(parent, "选择文件", "", file_filter)
        if path:
            line_edit.setText(path)
    btn.clicked.connect(browse)
    layout.addWidget(label)
    layout.addWidget(line_edit, 1)
    layout.addWidget(btn)
    return layout, line_edit


def format_duration(seconds):
    """格式化时长"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_size(bytes_size):
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


# ─────────────────────── 标签页组件 ───────────────────────

class ConvertTab(QWidget):
    """视频格式转换标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔄 视频格式转换")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        subtitle = QLabel("支持 MP4、AVI、MKV、MOV、WebM 格式互转")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件选择组
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout(file_group)
        self.input_layout, self.input_edit = create_file_selector(
            self, "输入文件:", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv)")
        file_layout.addLayout(self.input_layout)
        out_row = QHBoxLayout()
        out_label = QLabel("输出目录:")
        out_label.setFixedWidth(90)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setPlaceholderText("默认与输入文件相同目录")
        out_btn = QPushButton("浏览")
        out_btn.setFixedWidth(80)
        out_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        out_btn.clicked.connect(self._browse_output)
        out_row.addWidget(out_label)
        out_row.addWidget(self.output_dir_edit, 1)
        out_row.addWidget(out_btn)
        file_layout.addLayout(out_row)
        layout.addWidget(file_group)

        # 格式选择
        fmt_group = QGroupBox("目标格式")
        fmt_layout = QHBoxLayout(fmt_group)
        fmt_layout.addWidget(QLabel("转换为:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "MOV", "WebM"])
        self.format_combo.setFixedWidth(150)
        fmt_layout.addWidget(self.format_combo)
        fmt_layout.addStretch()
        layout.addWidget(fmt_group)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.convert_btn = QPushButton("🚀 开始转换")
        self.convert_btn.setFixedHeight(42)
        self.convert_btn.clicked.connect(self._start_convert)
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedHeight(42)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #e74c3c,stop:1 #c0392b);
                           color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff6b5a,stop:1 #d44637); }
            QPushButton:disabled { background: #2a2a3a; color: #555566; }
        """)
        self.stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self.convert_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        self.log_text.setPlaceholderText("操作日志将显示在此处...")
        layout.addWidget(self.log_text, 1)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self.output_dir_edit.setText(d)

    def _start_convert(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return
        fmt = self.format_combo.currentText().lower()
        out_dir = self.output_dir_edit.text().strip() or str(Path(input_path).parent)
        name = Path(input_path).stem
        output_path = os.path.join(out_dir, f"{name}_converted.{fmt}")
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = ConvertWorker(input_path, output_path, fmt)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self._append_log)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _stop(self):
        if self.worker:
            self.worker.stop()

    def _append_log(self, msg):
        self.log_text.append(msg)

    def _on_done(self, ok, msg):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._append_log(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


class TrimTab(QWidget):
    """视频裁剪标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("✂️ 视频裁剪")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("通过设置开始和结束时间裁剪视频片段")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件选择
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout(file_group)
        self.input_layout, self.input_edit = create_file_selector(
            self, "输入文件:", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv)")
        file_layout.addLayout(self.input_layout)
        layout.addWidget(file_group)

        # 时间设置
        time_group = QGroupBox("裁剪时间")
        time_layout = QGridLayout(time_group)
        time_layout.addWidget(QLabel("开始时间 (秒):"), 0, 0)
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 99999)
        self.start_spin.setDecimals(1)
        self.start_spin.setSuffix(" 秒")
        time_layout.addWidget(self.start_spin, 0, 1)
        time_layout.addWidget(QLabel("结束时间 (秒):"), 1, 0)
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0, 99999)
        self.end_spin.setDecimals(1)
        self.end_spin.setSuffix(" 秒")
        time_layout.addWidget(self.end_spin, 1, 1)
        hint = QLabel("💡 提示: 也可以使用 HH:MM:SS 格式，如 00:01:30 = 90秒")
        hint.setStyleSheet("color: #667eea; font-size: 11px;")
        time_layout.addWidget(hint, 2, 0, 1, 2)
        layout.addWidget(time_group)

        # 操作按钮
        self.trim_btn = QPushButton("✂️ 开始裁剪")
        self.trim_btn.setFixedHeight(42)
        self.trim_btn.clicked.connect(self._start_trim)
        layout.addWidget(self.trim_btn)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        layout.addWidget(self.log_text, 1)

    def _start_trim(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return
        start = self.start_spin.value()
        end = self.end_spin.value()
        if end <= start:
            QMessageBox.warning(self, "提示", "结束时间必须大于开始时间")
            return
        output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_trimmed{Path(input_path).suffix}")
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = TrimWorker(input_path, output_path, start, end)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log_text.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.trim_btn.setEnabled(False)

    def _on_done(self, ok, msg):
        self.trim_btn.setEnabled(True)
        self.log_text.append(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


class MergeTab(QWidget):
    """视频合并标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🔗 视频合并")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("将多个视频文件合并为一个视频")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件列表
        list_group = QGroupBox("视频文件列表")
        list_layout = QVBoxLayout(list_group)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加文件")
        add_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("➖ 移除选中")
        remove_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn = QPushButton("🗑 清空列表")
        clear_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        clear_btn.clicked.connect(lambda: self.file_list.clear())
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        list_layout.addWidget(self.file_list)
        layout.addWidget(list_group)

        # 操作按钮
        self.merge_btn = QPushButton("🔗 开始合并")
        self.merge_btn.setFixedHeight(42)
        self.merge_btn.clicked.connect(self._start_merge)
        layout.addWidget(self.merge_btn)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        layout.addWidget(self.log_text, 1)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv)")
        for f in files:
            self.file_list.addItem(QListWidgetItem(f))

    def _remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _start_merge(self):
        count = self.file_list.count()
        if count < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个视频文件")
            return
        paths = [self.file_list.item(i).text() for i in range(count)]
        first = paths[0]
        ext = Path(first).suffix
        output = str(Path(first).parent / f"merged_output{ext}")
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = MergeWorker(paths, output)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log_text.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.merge_btn.setEnabled(False)

    def _on_done(self, ok, msg):
        self.merge_btn.setEnabled(True)
        self.log_text.append(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


class CompressTab(QWidget):
    """视频压缩标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📦 视频压缩")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("降低视频码率以减小文件体积")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件选择
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout(file_group)
        self.input_layout, self.input_edit = create_file_selector(
            self, "输入文件:", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm)")
        file_layout.addLayout(self.input_layout)
        layout.addWidget(file_group)

        # 压缩设置
        comp_group = QGroupBox("压缩设置")
        comp_layout = QHBoxLayout(comp_group)
        comp_layout.addWidget(QLabel("压缩质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(50)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setFixedWidth(100)
        comp_layout.addWidget(self.quality_spin)
        comp_layout.addWidget(QLabel("(值越低，文件越小，质量越差)"))
        comp_layout.addStretch()
        layout.addWidget(comp_group)

        # 操作按钮
        self.compress_btn = QPushButton("📦 开始压缩")
        self.compress_btn.setFixedHeight(42)
        self.compress_btn.clicked.connect(self._start_compress)
        layout.addWidget(self.compress_btn)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        layout.addWidget(self.log_text, 1)

    def _start_compress(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return
        quality = self.quality_spin.value()
        output = str(Path(input_path).parent / f"{Path(input_path).stem}_compressed{Path(input_path).suffix}")
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = CompressWorker(input_path, output, quality)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log_text.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.compress_btn.setEnabled(False)

    def _on_done(self, ok, msg):
        self.compress_btn.setEnabled(True)
        self.log_text.append(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


class AudioExtractTab(QWidget):
    """音频提取标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🎵 音频提取")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("从视频文件中提取音频轨道")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件选择
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout(file_group)
        self.input_layout, self.input_edit = create_file_selector(
            self, "输入文件:", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm)")
        file_layout.addLayout(self.input_layout)
        layout.addWidget(file_group)

        # 格式设置
        fmt_group = QGroupBox("音频格式")
        fmt_layout = QHBoxLayout(fmt_group)
        fmt_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "WAV"])
        self.format_combo.setFixedWidth(120)
        fmt_layout.addWidget(self.format_combo)
        fmt_layout.addStretch()
        layout.addWidget(fmt_group)

        # 操作按钮
        self.extract_btn = QPushButton("🎵 开始提取")
        self.extract_btn.setFixedHeight(42)
        self.extract_btn.clicked.connect(self._start_extract)
        layout.addWidget(self.extract_btn)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        layout.addWidget(self.log_text, 1)

    def _start_extract(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return
        fmt = self.format_combo.currentText().lower()
        output = str(Path(input_path).parent / f"{Path(input_path).stem}.{fmt}")
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = AudioExtractWorker(input_path, output, fmt)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log_text.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.extract_btn.setEnabled(False)

    def _on_done(self, ok, msg):
        self.extract_btn.setEnabled(True)
        self.log_text.append(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


class VideoInfoTab(QWidget):
    """视频信息查看标签页"""
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("ℹ️ 视频信息")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("查看视频文件的详细元数据信息")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件选择
        file_group = QGroupBox("选择文件")
        file_layout = QVBoxLayout(file_group)
        self.input_layout, self.input_edit = create_file_selector(
            self, "视频文件:", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv)")
        file_layout.addLayout(self.input_layout)
        layout.addWidget(file_group)

        # 查看按钮
        self.info_btn = QPushButton("ℹ️ 获取信息")
        self.info_btn.setFixedHeight(42)
        self.info_btn.clicked.connect(self._get_info)
        layout.addWidget(self.info_btn)

        # 信息显示
        info_group = QGroupBox("视频详情")
        info_layout = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("选择视频文件后点击'获取信息'按钮...")
        self.info_text.setMinimumHeight(250)
        info_layout.addWidget(self.info_text)
        layout.addWidget(info_group, 1)

    def _get_info(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(input_path)
            file_size = os.path.getsize(input_path)
            info_lines = [
                f"{'═' * 50}",
                f"  📁 文件名:    {os.path.basename(input_path)}",
                f"  📏 文件大小:  {format_size(file_size)}",
                f"  📐 分辨率:    {clip.size[0]} × {clip.size[1]}",
                f"  ⏱️ 时长:      {format_duration(clip.duration)} ({clip.duration:.2f} 秒)",
                f"  🎬 帧率:      {clip.fps:.2f} fps",
                f"  🎨 编码格式:  {Path(input_path).suffix.upper().strip('.')}",
            ]
            if clip.audio:
                info_lines.extend([
                    f"  🎵 音频:      有",
                    f"  🎤 音频采样率: {clip.audio.fps} Hz",
                ])
            else:
                info_lines.append(f"  🎵 音频:      无")
            info_lines.append(f"{'═' * 50}")
            self.info_text.setPlainText("\n".join(info_lines))
            clip.close()
        except Exception as e:
            self.info_text.setPlainText(f"❌ 读取失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法读取视频信息:\n{str(e)}")


class BatchConvertTab(QWidget):
    """批量转换标签页"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📋 批量转换")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        subtitle = QLabel("一次性转换多个视频文件为统一格式")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # 文件列表
        list_group = QGroupBox("视频文件列表")
        list_layout = QVBoxLayout(list_group)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加文件")
        add_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("➖ 移除选中")
        remove_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn = QPushButton("🗑 清空列表")
        clear_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        clear_btn.clicked.connect(lambda: self.file_list.clear())
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        list_layout.addWidget(self.file_list)
        layout.addWidget(list_group)

        # 格式和输出目录
        settings_group = QGroupBox("转换设置")
        settings_layout = QGridLayout(settings_group)
        settings_layout.addWidget(QLabel("目标格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "MOV", "WebM"])
        self.format_combo.setFixedWidth(150)
        settings_layout.addWidget(self.format_combo, 0, 1)
        settings_layout.addWidget(QLabel("输出目录:"), 1, 0)
        out_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("默认输出到第一个文件所在目录")
        out_btn = QPushButton("浏览")
        out_btn.setFixedWidth(80)
        out_btn.setStyleSheet("""
            QPushButton { background: #1a1a2e; border: 1px solid #2a2a3a; color: #8888aa;
                           padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #222236; border: 1px solid #667eea; color: #aaaacc; }
        """)
        out_btn.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(out_btn)
        settings_layout.addLayout(out_row, 1, 1)
        layout.addWidget(settings_group)

        # 操作按钮
        btn_row2 = QHBoxLayout()
        self.convert_btn = QPushButton("🚀 开始批量转换")
        self.convert_btn.setFixedHeight(42)
        self.convert_btn.clicked.connect(self._start_batch)
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedHeight(42)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #e74c3c,stop:1 #c0392b);
                           color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff6b5a,stop:1 #d44637); }
            QPushButton:disabled { background: #2a2a3a; color: #555566; }
        """)
        self.stop_btn.clicked.connect(self._stop)
        btn_row2.addWidget(self.convert_btn)
        btn_row2.addWidget(self.stop_btn)
        layout.addLayout(btn_row2)

        # 进度和日志
        self.progress = QProgressBar()
        self.progress.setFixedHeight(24)
        layout.addWidget(self.progress)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        layout.addWidget(self.log_text, 1)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv)")
        for f in files:
            self.file_list.addItem(QListWidgetItem(f))

    def _remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self.output_edit.setText(d)

    def _stop(self):
        if self.worker:
            self.worker.stop()

    def _start_batch(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return
        paths = [self.file_list.item(i).text() for i in range(count)]
        fmt = self.format_combo.currentText().lower()
        out_dir = self.output_edit.text().strip() or str(Path(paths[0]).parent)
        self.log_text.clear()
        self.progress.setValue(0)
        self.worker = BatchConvertWorker(paths, out_dir, fmt)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log_text.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.start()
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_done(self, ok, msg):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_text.append(msg)
        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "错误", msg)


# ─────────────────────── 主窗口 ───────────────────────
class MainWindow(QMainWindow):
    """VideoTools 主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 VideoTools - 视频处理工具箱")
        self.setMinimumSize(900, 700)
        self.resize(960, 740)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题栏
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #667eea);
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        app_title = QLabel("🎬 VideoTools")
        app_title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background: transparent;")
        app_sub = QLabel("视频处理工具箱  v1.0")
        app_sub.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; background: transparent;")
        header_layout.addWidget(app_title)
        header_layout.addWidget(app_sub)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(ConvertTab(), "🔄 视频转换")
        self.tabs.addTab(TrimTab(), "✂️ 视频裁剪")
        self.tabs.addTab(MergeTab(), "🔗 视频合并")
        self.tabs.addTab(CompressTab(), "📦 视频压缩")
        self.tabs.addTab(AudioExtractTab(), "🎵 音频提取")
        self.tabs.addTab(VideoInfoTab(), "ℹ️ 视频信息")
        self.tabs.addTab(BatchConvertTab(), "📋 批量转换")
        main_layout.addWidget(self.tabs, 1)

        # 底部状态栏
        footer = QFrame()
        footer.setFixedHeight(30)
        footer.setStyleSheet("QFrame { background-color: #0d0d1a; border-top: 1px solid #1a1a2e; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)
        status = QLabel("就绪  |  基于 PyQt6 + MoviePy  |  支持格式: MP4 / AVI / MKV / MOV / WebM")
        status.setStyleSheet("color: #555577; font-size: 11px; background: transparent;")
        footer_layout.addWidget(status)
        footer_layout.addStretch()
        main_layout.addWidget(footer)


# ─────────────────────── 入口 ───────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
