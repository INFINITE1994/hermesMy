"""
GIF Maker - 专业 GIF 制作与编辑工具
"""
import sys
import os
import time
import threading
import traceback
from pathlib import Path
from typing import Optional, List

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio.v3 as iio

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFileDialog, QComboBox,
    QSpinBox, QDoubleSpinBox, QSlider, QGroupBox, QScrollArea,
    QProgressBar, QTabWidget, QLineEdit, QTextEdit, QCheckBox,
    QRadioButton, QButtonGroup, QMessageBox, QSizePolicy,
    QSplitter, QFrame, QListWidget, QListWidgetItem, QInputDialog,
    QColorDialog, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPoint, QRect, QMimeData
)
from PyQt6.QtGui import (
    QPixmap, QImage, QIcon, QFont, QColor, QPainter, QLinearGradient,
    QPen, QBrush, QDragEnterEvent, QDropEvent, QAction, QCursor
)

# ─── Constants ────────────────────────────────────────────────────────────────

BG_COLOR = "#0a0a0a"
CARD_COLOR = "#111122"
ACCENT_START = "#667eea"
ACCENT_END = "#764ba2"
TEXT_COLOR = "#e0e0e0"
TEXT_DIM = "#888888"
BORDER_COLOR = "#2a2a3a"
HOVER_COLOR = "#1a1a2e"
INPUT_BG = "#1a1a2e"
BTN_BG = "#2a2a4a"
BTN_HOVER = "#3a3a5a"
SUCCESS_COLOR = "#4ade80"
ERROR_COLOR = "#f87171"
WARNING_COLOR = "#fbbf24"

SUPPORTED_VIDEO = "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v)"
SUPPORTED_IMAGE = "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff)"
SUPPORTED_GIF = "GIF 文件 (*.gif)"

# ─── Styles ───────────────────────────────────────────────────────────────────

STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_COLOR};
}}
QWidget {{
    color: {TEXT_COLOR};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background: {CARD_COLOR};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: {BG_COLOR};
    color: {TEXT_DIM};
    padding: 10px 20px;
    margin: 2px;
    border-radius: 6px 6px 0 0;
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background: {CARD_COLOR};
    color: {TEXT_COLOR};
    border-bottom: 2px solid {ACCENT_START};
}}
QTabBar::tab:hover:!selected {{
    background: {HOVER_COLOR};
    color: {TEXT_COLOR};
}}
QGroupBox {{
    background: {CARD_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {ACCENT_START};
}}
QPushButton {{
    background: {BTN_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    min-height: 20px;
}}
QPushButton:hover {{
    background: {BTN_HOVER};
    border-color: {ACCENT_START};
}}
QPushButton:pressed {{
    background: {ACCENT_START};
}}
QPushButton:disabled {{
    background: {BG_COLOR};
    color: {TEXT_DIM};
}}
QPushButton#accent {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    color: white;
    border: none;
}}
QPushButton#accent:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:0.5 {ACCENT_END}, stop:1 {ACCENT_START});
}}
QPushButton#danger {{
    background: #7f1d1d;
    border-color: {ERROR_COLOR};
}}
QPushButton#danger:hover {{
    background: #991b1b;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT_START};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_START};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER_COLOR};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT_START};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border-radius: 3px;
}}
QProgressBar {{
    background: {BG_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_COLOR};
    min-height: 22px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border-radius: 5px;
}}
QListWidget {{
    background: {BG_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 4px;
}}
QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background: {ACCENT_START};
    color: white;
}}
QListWidget::item:hover {{
    background: {HOVER_COLOR};
}}
QScrollBar:vertical {{
    background: {BG_COLOR};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_COLOR};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_START};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_COLOR};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_COLOR};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT_START};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {BORDER_COLOR};
    border-radius: 4px;
    background: {INPUT_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_START};
    border-color: {ACCENT_START};
}}
QRadioButton {{
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {BORDER_COLOR};
    border-radius: 9px;
    background: {INPUT_BG};
}}
QRadioButton::indicator:checked {{
    background: {ACCENT_START};
    border-color: {ACCENT_START};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QLabel#title {{
    font-size: 22px;
    font-weight: bold;
    color: {ACCENT_START};
}}
QLabel#subtitle {{
    color: {TEXT_DIM};
    font-size: 12px;
}}
QLabel#sectionTitle {{
    font-size: 15px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}
QFrame#separator {{
    background: {BORDER_COLOR};
    max-height: 1px;
}}
QSplitter::handle {{
    background: {BORDER_COLOR};
    width: 2px;
}}
QDialog {{
    background: {CARD_COLOR};
}}
"""

# ─── Worker threads ───────────────────────────────────────────────────────────

class VideoToGifWorker(QThread):
    progress = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_path, output_path, fps, quality, scale, start_time, end_time):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.fps = fps
        self.quality = quality
        self.scale = scale
        self.start_time = start_time
        self.end_time = end_time

    def run(self):
        try:
            reader = iio.imiter(self.video_path, plugin="pyav")
            meta = iio.immeta(self.video_path, plugin="pyav")
            src_fps = meta.get("fps", 30)

            start_frame = int(self.start_time * src_fps)
            end_frame = int(self.end_time * src_fps) if self.end_time > 0 else float('inf')

            frames = []
            count = 0
            for frame in reader:
                if count < start_frame:
                    count += 1
                    continue
                if count >= end_frame:
                    break
                img = Image.fromarray(frame)
                if self.scale != 1.0:
                    w, h = img.size
                    img = img.resize((int(w * self.scale), int(h * self.scale)), Image.Resampling.LANCZOS)
                frames.append(np.array(img))
                count += 1
                step = min(90, int((count - start_frame) / max(1, (end_frame - start_frame)) * 90))
                self.progress.emit(step)

            if not frames:
                self.error.emit("未提取到任何帧")
                return

            # Skip frames to match target fps
            if self.fps < src_fps:
                skip = max(1, int(src_fps / self.fps))
                frames = frames[::skip]

            duration = 1000 / self.fps
            self.progress.emit(95)

            iio.imwrite(self.output_path, frames, duration=duration, loop=0,
                        quantize_factor=max(1, 10 - self.quality // 10))
            self.progress.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.error.emit(f"视频转换失败: {str(e)}")


class ImagesToGifWorker(QThread):
    progress = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, image_paths, output_path, duration, loop, optimize, resize_w, resize_h):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
        self.duration = duration
        self.loop = loop
        self.optimize = optimize
        self.resize_w = resize_w
        self.resize_h = resize_h

    def run(self):
        try:
            frames = []
            total = len(self.image_paths)
            for i, path in enumerate(self.image_paths):
                img = Image.open(path).convert("RGBA")
                if self.resize_w > 0 and self.resize_h > 0:
                    img = img.resize((self.resize_w, self.resize_h), Image.Resampling.LANCZOS)
                elif self.resize_w > 0:
                    ratio = self.resize_w / img.width
                    img = img.resize((self.resize_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
                # Convert RGBA to RGB with white background for GIF
                if img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                frames.append(img)
                self.progress.emit(int((i + 1) / total * 90))

            self.progress.emit(95)
            frames[0].save(
                self.output_path, save_all=True, append_images=frames[1:],
                duration=self.duration, loop=0 if self.loop else 1,
                optimize=self.optimize
            )
            self.progress.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.error.emit(f"图片合成失败: {str(e)}")


class GifOptimizeWorker(QThread):
    progress = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, colors, lossy, scale):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.colors = colors
        self.lossy = lossy
        self.scale = scale

    def run(self):
        try:
            gif = Image.open(self.input_path)
            frames = []
            durations = []
            try:
                while True:
                    frame = gif.copy().convert("RGBA")
                    if self.scale != 1.0:
                        w, h = frame.size
                        frame = frame.resize((int(w * self.scale), int(h * self.scale)),
                                            Image.Resampling.LANCZOS)
                    bg = Image.new("RGBA", frame.size, (255, 255, 255, 255))
                    bg.paste(frame, mask=frame.split()[3] if frame.mode == "RGBA" else None)
                    quantized = bg.convert("RGB").quantize(colors=self.colors, method=Image.Quantize.MEDIANCUT)
                    frames.append(quantized)
                    dur = gif.info.get("duration", 100)
                    durations.append(dur)
                    gif.seek(gif.tell() + 1)
                    self.progress.emit(min(90, int(gif.tell() / max(1, 100) * 90)))
            except EOFError:
                pass

            if not frames:
                self.error.emit("无法读取 GIF 帧")
                return

            self.progress.emit(95)
            frames[0].save(
                self.output_path, save_all=True, append_images=frames[1:],
                duration=durations, loop=0, optimize=True
            )
            self.progress.emit(100)

            orig_size = os.path.getsize(self.input_path)
            new_size = os.path.getsize(self.output_path)
            msg = f"优化完成！原始: {orig_size//1024}KB → 新: {new_size//1024}KB (减少 {max(0,(1-new_size/orig_size)*100):.1f}%)"
            self.finished_signal.emit(msg)
        except Exception as e:
            self.error.emit(f"优化失败: {str(e)}")


class FrameExtractWorker(QThread):
    progress = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, gif_path, output_dir, fmt):
        super().__init__()
        self.gif_path = gif_path
        self.output_dir = output_dir
        self.fmt = fmt

    def run(self):
        try:
            gif = Image.open(self.gif_path)
            count = 0
            total = 0
            try:
                while True:
                    gif.seek(gif.tell() + 1)
                    total += 1
            except EOFError:
                pass
            total += 1

            gif.seek(0)
            for i in range(total):
                frame = gif.copy().convert("RGBA")
                ext = self.fmt.lower()
                out_path = os.path.join(self.output_dir, f"frame_{i:04d}.{ext}")
                if ext in ("jpg", "jpeg"):
                    bg = Image.new("RGB", frame.size, (255, 255, 255))
                    bg.paste(frame, mask=frame.split()[3] if frame.mode == "RGBA" else None)
                    bg.save(out_path, quality=95)
                else:
                    frame.save(out_path)
                count += 1
                self.progress.emit(int(count / total * 100))
                gif.seek(i + 1) if i + 1 < total else None

            self.finished_signal.emit(f"成功提取 {count} 帧到: {self.output_dir}")
        except EOFError:
            self.finished_signal.emit(f"成功提取 {count} 帧到: {self.output_dir}")
        except Exception as e:
            self.error.emit(f"提取失败: {str(e)}")


# ─── Custom Widgets ───────────────────────────────────────────────────────────

class GifPreviewWidget(QLabel):
    """Animated GIF preview widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QLabel {{
                background: {BG_COLOR};
                border: 2px dashed {BORDER_COLOR};
                border-radius: 12px;
                color: {TEXT_DIM};
                font-size: 14px;
            }}
        """)
        self.setText("拖放文件到此处\n或点击上方按钮选择")
        self.setAcceptDrops(True)
        self._frames = []
        self._durations = []
        self._current = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._playing = False
        self._frame_count = 0

    def load_gif(self, path: str):
        self.stop()
        try:
            gif = Image.open(path)
            self._frames = []
            self._durations = []
            try:
                while True:
                    frame = gif.copy().convert("RGBA")
                    self._frames.append(frame)
                    self._durations.append(gif.info.get("duration", 100))
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass
            self._frame_count = len(self._frames)
            if self._frames:
                self._current = 0
                self._show_frame(0)
                self.play()
        except Exception as e:
            self.setText(f"加载失败: {e}")

    def load_image(self, path: str):
        self.stop()
        try:
            img = Image.open(path).convert("RGBA")
            self._frames = [img]
            self._durations = [100]
            self._frame_count = 1
            self._current = 0
            self._show_pil_image(img)
        except Exception as e:
            self.setText(f"加载失败: {e}")

    def set_pil_frames(self, pil_frames, durations=None):
        self.stop()
        self._frames = pil_frames
        self._durations = durations or [100] * len(pil_frames)
        self._frame_count = len(pil_frames)
        if pil_frames:
            self._current = 0
            self._show_frame(0)
            self.play()

    def play(self):
        if self._frames and not self._playing:
            self._playing = True
            dur = max(20, self._durations[self._current])
            self._timer.start(dur)

    def pause(self):
        self._playing = False
        self._timer.stop()

    def stop(self):
        self.pause()
        self._current = 0
        self._frames = []
        self._durations = []
        self._frame_count = 0

    def next_frame(self):
        if self._frames:
            self._current = (self._current + 1) % self._frame_count
            self._show_frame(self._current)

    def prev_frame(self):
        if self._frames:
            self._current = (self._current - 1) % self._frame_count
            self._show_frame(self._current)

    def _next_frame(self):
        if self._frames:
            self._current = (self._current + 1) % self._frame_count
            self._show_frame(self._current)
            dur = max(20, self._durations[self._current])
            self._timer.setInterval(dur)

    def _show_frame(self, idx):
        if 0 <= idx < len(self._frames):
            self._show_pil_image(self._frames[idx])

    def _show_pil_image(self, pil_img):
        pil_img = pil_img.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.size() - QSize(20, 20),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)

    def get_frame_count(self):
        return self._frame_count

    def get_current_index(self):
        return self._current

    @property
    def is_playing(self):
        return self._playing


class DropListWidget(QListWidget):
    """List widget with drag & drop support."""
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setMinimumHeight(120)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    paths.append(path)
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ─── Helper functions ─────────────────────────────────────────────────────────

def make_h_line():
    line = QFrame()
    line.setObjectName("separator")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line


def make_label(text, obj_name=None):
    lbl = QLabel(text)
    if obj_name:
        lbl.setObjectName(obj_name)
    return lbl


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024*1024):.2f} MB"


# ─── Tab: Video to GIF ───────────────────────────────────────────────────────

class VideoToGifTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File selection
        file_group = QGroupBox("📁 选择视频文件")
        fg = QHBoxLayout(file_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择视频文件...")
        self.path_edit.setReadOnly(True)
        fg.addWidget(self.path_edit, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse)
        fg.addWidget(browse_btn)
        layout.addWidget(file_group)

        # Settings
        settings_group = QGroupBox("⚙️ 转换设置")
        sg = QGridLayout(settings_group)
        sg.setSpacing(10)

        sg.addWidget(QLabel("帧率 (FPS):"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(10)
        sg.addWidget(self.fps_spin, 0, 1)

        sg.addWidget(QLabel("质量:"), 0, 2)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(80)
        self.quality_label = QLabel("80")
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        sg.addWidget(self.quality_slider, 0, 3)
        sg.addWidget(self.quality_label, 0, 4)

        sg.addWidget(QLabel("缩放比例:"), 1, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 3.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        sg.addWidget(self.scale_spin, 1, 1)

        sg.addWidget(QLabel("开始时间 (秒):"), 1, 2)
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 9999)
        sg.addWidget(self.start_spin, 1, 3, 1, 2)

        sg.addWidget(QLabel("结束时间 (秒):"), 2, 0)
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0, 9999)
        self.end_spin.setValue(0)
        self.end_spin.setSpecialValueText("到结尾")
        sg.addWidget(self.end_spin, 2, 1)

        layout.addWidget(settings_group)

        # Preview & convert
        self.preview = GifPreviewWidget()
        layout.addWidget(self.preview, 1)

        btn_layout = QHBoxLayout()
        self.convert_btn = QPushButton("🎬 开始转换")
        self.convert_btn.setObjectName("accent")
        self.convert_btn.clicked.connect(self._convert)
        self.convert_btn.setEnabled(False)
        btn_layout.addWidget(self.convert_btn)
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", SUPPORTED_VIDEO)
        if path:
            self.video_path = path
            self.path_edit.setText(path)
            self.convert_btn.setEnabled(True)

    def _convert(self):
        if not self.video_path:
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存 GIF", "", SUPPORTED_GIF)
        if not out:
            return

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.worker = VideoToGifWorker(
            self.video_path, out,
            self.fps_spin.value(), self.quality_slider.value(),
            self.scale_spin.value(), self.start_spin.value(), self.end_spin.value()
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, path):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.preview.load_gif(path)
        QMessageBox.information(self, "完成", f"GIF 已保存到:\n{path}")

    def _on_error(self, msg):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


# ─── Tab: Images to GIF ──────────────────────────────────────────────────────

class ImagesToGifTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File list
        file_group = QGroupBox("🖼️ 图片列表")
        fg = QVBoxLayout(file_group)

        self.list_widget = DropListWidget()
        self.list_widget.files_dropped.connect(self._add_files)
        fg.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加图片")
        add_btn.clicked.connect(self._add_images)
        btn_row.addWidget(add_btn)
        remove_btn = QPushButton("➖ 移除选中")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(lambda: self.list_widget.clear())
        btn_row.addWidget(clear_btn)
        fg.addLayout(btn_row)
        layout.addWidget(file_group)

        # Settings
        settings_group = QGroupBox("⚙️ 合成设置")
        sg = QGridLayout(settings_group)
        sg.setSpacing(10)

        sg.addWidget(QLabel("每帧持续时间 (毫秒):"), 0, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 10000)
        self.duration_spin.setValue(200)
        sg.addWidget(self.duration_spin, 0, 1)

        self.loop_check = QCheckBox("循环播放")
        self.loop_check.setChecked(True)
        sg.addWidget(self.loop_check, 0, 2)

        self.optimize_check = QCheckBox("优化文件大小")
        self.optimize_check.setChecked(True)
        sg.addWidget(self.optimize_check, 0, 3)

        sg.addWidget(QLabel("宽度 (0=自动):"), 1, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(0, 4096)
        sg.addWidget(self.width_spin, 1, 1)

        sg.addWidget(QLabel("高度 (0=自动):"), 1, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(0, 4096)
        sg.addWidget(self.height_spin, 1, 3)

        layout.addWidget(settings_group)

        # Preview
        self.preview = GifPreviewWidget()
        layout.addWidget(self.preview, 1)

        # Create
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("🎬 创建 GIF")
        self.create_btn.setObjectName("accent")
        self.create_btn.clicked.connect(self._create)
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", SUPPORTED_IMAGE)
        self._add_files(paths)

    def _add_files(self, paths):
        for p in paths:
            if self.list_widget.count() == 0 or not any(
                self.list_widget.item(i).text() == p for i in range(self.list_widget.count())
            ):
                self.list_widget.addItem(QListWidgetItem(p))

    def _remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def _get_paths(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def _create(self):
        paths = self._get_paths()
        if not paths:
            QMessageBox.warning(self, "提示", "请先添加图片")
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存 GIF", "", SUPPORTED_GIF)
        if not out:
            return

        self.create_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.worker = ImagesToGifWorker(
            paths, out,
            self.duration_spin.value(), self.loop_check.isChecked(),
            self.optimize_check.isChecked(), self.width_spin.value(), self.height_spin.value()
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, path):
        self.progress.setVisible(False)
        self.create_btn.setEnabled(True)
        self.preview.load_gif(path)
        QMessageBox.information(self, "完成", f"GIF 已保存到:\n{path}")

    def _on_error(self, msg):
        self.progress.setVisible(False)
        self.create_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


# ─── Tab: Screen Recording ───────────────────────────────────────────────────

class ScreenRecordTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._frames = []
        self._timer = QTimer()
        self._timer.timeout.connect(self._capture_frame)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Info
        info = QLabel("💡 屏幕录制说明：点击开始录制后，将捕获整个屏幕。录制完成后可保存为 GIF。")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {TEXT_DIM}; padding: 10px; background: {BG_COLOR}; border-radius: 8px;")
        layout.addWidget(info)

        # Settings
        settings_group = QGroupBox("⚙️ 录制设置")
        sg = QGridLayout(settings_group)

        sg.addWidget(QLabel("录制帧率:"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 30)
        self.fps_spin.setValue(10)
        sg.addWidget(self.fps_spin, 0, 1)

        sg.addWidget(QLabel("缩放比例:"), 0, 2)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 1.0)
        self.scale_spin.setValue(0.5)
        self.scale_spin.setSingleStep(0.1)
        sg.addWidget(self.scale_spin, 0, 3)

        layout.addWidget(settings_group)

        # Preview
        self.preview = GifPreviewWidget()
        self.preview.setText("录制预览将在此显示")
        layout.addWidget(self.preview, 1)

        # Status
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM};")
        layout.addWidget(self.status_label)

        # Controls
        ctrl_layout = QHBoxLayout()
        self.record_btn = QPushButton("🔴 开始录制")
        self.record_btn.setObjectName("accent")
        self.record_btn.clicked.connect(self._toggle_recording)
        ctrl_layout.addWidget(self.record_btn)

        self.save_btn = QPushButton("💾 保存 GIF")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save)
        ctrl_layout.addWidget(self.save_btn)

        layout.addLayout(ctrl_layout)

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._frames = []
        self._recording = True
        self.record_btn.setText("⏹️ 停止录制")
        self.save_btn.setEnabled(False)
        interval = 1000 // self.fps_spin.value()
        self._timer.start(interval)
        self.status_label.setText("🔴 录制中...")

    def _stop_recording(self):
        self._recording = False
        self._timer.stop()
        self.record_btn.setText("🔴 开始录制")
        count = len(self._frames)
        self.status_label.setText(f"录制完成: {count} 帧")
        if count > 0:
            self.save_btn.setEnabled(True)
            self._show_last_frame()

    def _capture_frame(self):
        try:
            screen = QApplication.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(0)
                scale = self.scale_spin.value()
                if scale != 1.0:
                    pixmap = pixmap.scaled(
                        int(pixmap.width() * scale), int(pixmap.height() * scale),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                img = pixmap.toImage()
                buffer = img.bits().asstring(img.sizeInBytes())
                pil_img = Image.frombuffer("RGBA", (img.width(), img.height()), buffer, "raw", "BGRA")
                self._frames.append(pil_img.convert("RGB"))
                self.status_label.setText(f"🔴 录制中... {len(self._frames)} 帧")
        except Exception as e:
            self.status_label.setText(f"捕获错误: {e}")

    def _show_last_frame(self):
        if self._frames:
            last = self._frames[-1]
            data = last.tobytes("raw", "RGB")
            qimg = QImage(data, last.width, last.height, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            scaled = pixmap.scaled(self.preview.size() - QSize(20, 20),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.preview.setPixmap(scaled)

    def _save(self):
        if not self._frames:
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存 GIF", "", SUPPORTED_GIF)
        if not out:
            return
        try:
            duration = 1000 // self.fps_spin.value()
            self._frames[0].save(
                out, save_all=True, append_images=self._frames[1:],
                duration=duration, loop=0, optimize=True
            )
            self.preview.load_gif(out)
            QMessageBox.information(self, "完成", f"GIF 已保存到:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")


# ─── Tab: GIF Editor ─────────────────────────────────────────────────────────

class GifEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._frames = []
        self._durations = []
        self._gif_path = None
        self._text_color = "#FFFFFF"
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Left: preview
        left = QVBoxLayout()
        self.preview = GifPreviewWidget()
        left.addWidget(self.preview, 1)

        # Frame info
        self.frame_info = QLabel("帧: 0/0")
        self.frame_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_info.setStyleSheet(f"color: {TEXT_DIM};")
        left.addWidget(self.frame_info)

        # Frame controls
        fc = QHBoxLayout()
        prev_btn = QPushButton("⏮")
        prev_btn.setFixedWidth(50)
        prev_btn.clicked.connect(lambda: self.preview.prev_frame())
        fc.addWidget(prev_btn)
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedWidth(50)
        self.play_btn.clicked.connect(self._toggle_play)
        fc.addWidget(self.play_btn)
        next_btn = QPushButton("⏭")
        next_btn.setFixedWidth(50)
        next_btn.clicked.connect(lambda: self.preview.next_frame())
        fc.addWidget(next_btn)
        left.addLayout(fc)

        layout.addLayout(left, 3)

        # Right: controls
        right = QVBoxLayout()

        # Load
        load_btn = QPushButton("📂 加载 GIF")
        load_btn.clicked.connect(self._load)
        right.addWidget(load_btn)

        # Crop
        crop_group = QGroupBox("✂️ 裁剪")
        cg = QGridLayout(crop_group)
        cg.addWidget(QLabel("左:"), 0, 0)
        self.crop_left = QSpinBox(); self.crop_left.setRange(0, 9999)
        cg.addWidget(self.crop_left, 0, 1)
        cg.addWidget(QLabel("上:"), 0, 2)
        self.crop_top = QSpinBox(); self.crop_top.setRange(0, 9999)
        cg.addWidget(self.crop_top, 0, 3)
        cg.addWidget(QLabel("宽:"), 1, 0)
        self.crop_w = QSpinBox(); self.crop_w.setRange(0, 9999); self.crop_w.setSpecialValueText("原始")
        cg.addWidget(self.crop_w, 1, 1)
        cg.addWidget(QLabel("高:"), 1, 2)
        self.crop_h = QSpinBox(); self.crop_h.setRange(0, 9999); self.crop_h.setSpecialValueText("原始")
        cg.addWidget(self.crop_h, 1, 3)
        crop_btn = QPushButton("应用裁剪")
        crop_btn.clicked.connect(self._crop)
        cg.addWidget(crop_btn, 2, 0, 1, 4)
        right.addWidget(crop_group)

        # Resize
        resize_group = QGroupBox("📐 缩放")
        rg = QGridLayout(resize_group)
        rg.addWidget(QLabel("宽度:"), 0, 0)
        self.resize_w = QSpinBox(); self.resize_w.setRange(1, 4096); self.resize_w.setValue(320)
        rg.addWidget(self.resize_w, 0, 1)
        rg.addWidget(QLabel("高度:"), 0, 2)
        self.resize_h = QSpinBox(); self.resize_h.setRange(1, 4096); self.resize_h.setValue(240)
        rg.addWidget(self.resize_h, 0, 3)
        resize_btn = QPushButton("应用缩放")
        resize_btn.clicked.connect(self._resize)
        rg.addWidget(resize_btn, 1, 0, 1, 4)
        right.addWidget(resize_group)

        # Rotate
        rotate_group = QGroupBox("🔄 旋转")
        rog = QHBoxLayout(rotate_group)
        rot90_btn = QPushButton("↻ 90°")
        rot90_btn.clicked.connect(lambda: self._rotate(90))
        rog.addWidget(rot90_btn)
        rot180_btn = QPushButton("↻ 180°")
        rot180_btn.clicked.connect(lambda: self._rotate(180))
        rog.addWidget(rot180_btn)
        rot270_btn = QPushButton("↺ 270°")
        rot270_btn.clicked.connect(lambda: self._rotate(270))
        rog.addWidget(rot270_btn)
        right.addWidget(rotate_group)

        # Text
        text_group = QGroupBox("✏️ 添加文字")
        tg = QGridLayout(text_group)
        tg.addWidget(QLabel("文字:"), 0, 0)
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("输入文字...")
        tg.addWidget(self.text_edit, 0, 1, 1, 2)
        tg.addWidget(QLabel("大小:"), 1, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 200)
        self.font_size.setValue(24)
        tg.addWidget(self.font_size, 1, 1)
        self.color_btn = QPushButton("🎨 颜色")
        self.color_btn.clicked.connect(self._pick_color)
        tg.addWidget(self.color_btn, 1, 2)
        tg.addWidget(QLabel("位置:"), 2, 0)
        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["居中", "左上", "右上", "左下", "右下"])
        tg.addWidget(self.pos_combo, 2, 1, 1, 2)
        text_btn = QPushButton("应用文字")
        text_btn.clicked.connect(self._add_text)
        tg.addWidget(text_btn, 3, 0, 1, 3)
        right.addWidget(text_group)

        # Speed
        speed_group = QGroupBox("⏩ 播放速度")
        sg = QHBoxLayout(speed_group)
        sg.addWidget(QLabel("每帧 (毫秒):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(10, 5000)
        self.speed_spin.setValue(100)
        sg.addWidget(self.speed_spin)
        speed_btn = QPushButton("应用")
        speed_btn.clicked.connect(self._set_speed)
        sg.addWidget(speed_btn)
        right.addWidget(speed_group)

        # Save
        right.addStretch()
        save_btn = QPushButton("💾 保存 GIF")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        right.addWidget(save_btn)

        layout.addLayout(right, 2)

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 GIF", "", SUPPORTED_GIF)
        if path:
            self._gif_path = path
            gif = Image.open(path)
            self._frames = []
            self._durations = []
            try:
                while True:
                    self._frames.append(gif.copy().convert("RGBA"))
                    self._durations.append(gif.info.get("duration", 100))
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass
            self._update_preview()
            w, h = self._frames[0].size
            self.resize_w.setValue(w)
            self.resize_h.setValue(h)
            self.frame_info.setText(f"帧: {len(self._frames)} | 尺寸: {w}×{h}")

    def _update_preview(self):
        if self._frames:
            self.preview.set_pil_frames(self._frames, self._durations)

    def _toggle_play(self):
        if self.preview.is_playing:
            self.preview.pause()
            self.play_btn.setText("▶")
        else:
            self.preview.play()
            self.play_btn.setText("⏸")

    def _crop(self):
        if not self._frames:
            return
        l, t = self.crop_left.value(), self.crop_top.value()
        w = self.crop_w.value() or self._frames[0].width - l
        h = self.crop_h.value() or self._frames[0].height - t
        self._frames = [f.crop((l, t, l + w, t + h)) for f in self._frames]
        self._update_preview()
        self.frame_info.setText(f"已裁剪至 {w}×{h}")

    def _resize(self):
        if not self._frames:
            return
        w, h = self.resize_w.value(), self.resize_h.value()
        self._frames = [f.resize((w, h), Image.Resampling.LANCZOS) for f in self._frames]
        self._update_preview()
        self.frame_info.setText(f"已缩放至 {w}×{h}")

    def _rotate(self, deg):
        if not self._frames:
            return
        self._frames = [f.rotate(-deg, expand=True) for f in self._frames]
        self._update_preview()
        w, h = self._frames[0].size
        self.frame_info.setText(f"已旋转 {deg}° → {w}×{h}")

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._text_color), self)
        if color.isValid():
            self._text_color = color.name()

    def _add_text(self):
        if not self._frames or not self.text_edit.text():
            return
        text = self.text_edit.text()
        size = self.font_size.value()
        pos = self.pos_combo.currentText()
        color = self._text_color

        try:
            font = ImageFont.truetype("arial.ttf", size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        new_frames = []
        for frame in self._frames:
            overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            w, h = frame.size

            if pos == "居中":
                x, y = (w - tw) // 2, (h - th) // 2
            elif pos == "左上":
                x, y = 10, 10
            elif pos == "右上":
                x, y = w - tw - 10, 10
            elif pos == "左下":
                x, y = 10, h - th - 10
            else:
                x, y = w - tw - 10, h - th - 10

            # Shadow
            draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 150))
            draw.text((x, y), text, font=font, fill=color + "ff" if len(color) == 7 else color)
            new_frames.append(Image.alpha_composite(frame, overlay))

        self._frames = new_frames
        self._update_preview()

    def _set_speed(self):
        self._durations = [self.speed_spin.value()] * len(self._frames)
        self._update_preview()

    def _save(self):
        if not self._frames:
            QMessageBox.warning(self, "提示", "请先加载 GIF")
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存 GIF", "", SUPPORTED_GIF)
        if not out:
            return
        try:
            rgb_frames = []
            for f in self._frames:
                if f.mode == "RGBA":
                    bg = Image.new("RGB", f.size, (255, 255, 255))
                    bg.paste(f, mask=f.split()[3])
                    rgb_frames.append(bg)
                else:
                    rgb_frames.append(f.convert("RGB"))

            rgb_frames[0].save(
                out, save_all=True, append_images=rgb_frames[1:],
                duration=self._durations, loop=0, optimize=True
            )
            QMessageBox.information(self, "完成", f"GIF 已保存到:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")


# ─── Tab: GIF Optimizer ──────────────────────────────────────────────────────

class GifOptimizerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gif_path = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File
        file_group = QGroupBox("📁 选择 GIF 文件")
        fg = QHBoxLayout(file_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 GIF 文件...")
        self.path_edit.setReadOnly(True)
        fg.addWidget(self.path_edit, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse)
        fg.addWidget(browse_btn)
        layout.addWidget(file_group)

        # Original info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_DIM}; padding: 8px;")
        layout.addWidget(self.info_label)

        # Settings
        settings_group = QGroupBox("⚙️ 优化设置")
        sg = QGridLayout(settings_group)
        sg.setSpacing(10)

        sg.addWidget(QLabel("颜色数量:"), 0, 0)
        self.colors_spin = QSpinBox()
        self.colors_spin.setRange(2, 256)
        self.colors_spin.setValue(128)
        sg.addWidget(self.colors_spin, 0, 1)

        sg.addWidget(QLabel("缩放比例:"), 0, 2)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 1.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        sg.addWidget(self.scale_spin, 0, 3)

        layout.addWidget(settings_group)

        # Preview
        preview_layout = QHBoxLayout()
        self.preview_orig = GifPreviewWidget()
        self.preview_opt = GifPreviewWidget()
        preview_layout.addWidget(self.preview_orig)
        preview_layout.addWidget(self.preview_opt)
        layout.addLayout(preview_layout, 1)

        # Labels
        label_layout = QHBoxLayout()
        orig_lbl = QLabel("原始")
        orig_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        opt_lbl = QLabel("优化后")
        opt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_layout.addWidget(orig_lbl)
        label_layout.addWidget(opt_lbl)
        layout.addLayout(label_layout)

        # Optimize
        self.optimize_btn = QPushButton("📦 开始优化")
        self.optimize_btn.setObjectName("accent")
        self.optimize_btn.clicked.connect(self._optimize)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
        layout.addWidget(self.result_label)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 GIF", "", SUPPORTED_GIF)
        if path:
            self._gif_path = path
            self.path_edit.setText(path)
            size = os.path.getsize(path)
            try:
                gif = Image.open(path)
                w, h = gif.size
                frames = 0
                try:
                    while True:
                        frames += 1
                        gif.seek(gif.tell() + 1)
                except EOFError:
                    pass
                self.info_label.setText(f"文件大小: {format_size(size)} | 尺寸: {w}×{h} | 帧数: {frames}")
            except:
                self.info_label.setText(f"文件大小: {format_size(size)}")
            self.preview_orig.load_gif(path)
            self.optimize_btn.setEnabled(True)

    def _optimize(self):
        if not self._gif_path:
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存优化后的 GIF", "", SUPPORTED_GIF)
        if not out:
            return

        self.optimize_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.result_label.setText("")

        self.worker = GifOptimizeWorker(
            self._gif_path, out,
            self.colors_spin.value(), False, self.scale_spin.value()
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, msg):
        self.progress.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.result_label.setText(msg)
        # Try to load optimized gif from the message
        QMessageBox.information(self, "完成", msg)

    def _on_error(self, msg):
        self.progress.setVisible(False)
        self.optimize_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


# ─── Tab: Frame Extractor ────────────────────────────────────────────────────

class FrameExtractorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gif_path = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File
        file_group = QGroupBox("📁 选择 GIF 文件")
        fg = QHBoxLayout(file_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 GIF 文件...")
        self.path_edit.setReadOnly(True)
        fg.addWidget(self.path_edit, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse)
        fg.addWidget(browse_btn)
        layout.addWidget(file_group)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_DIM};")
        layout.addWidget(self.info_label)

        # Settings
        settings_group = QGroupBox("⚙️ 提取设置")
        sg = QGridLayout(settings_group)

        sg.addWidget(QLabel("输出格式:"), 0, 0)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PNG", "JPG", "BMP", "WebP"])
        sg.addWidget(self.fmt_combo, 0, 1)

        layout.addWidget(settings_group)

        # Preview
        self.preview = GifPreviewWidget()
        layout.addWidget(self.preview, 1)

        # Extract
        btn_layout = QHBoxLayout()
        self.extract_btn = QPushButton("🎞️ 提取所有帧")
        self.extract_btn.setObjectName("accent")
        self.extract_btn.clicked.connect(self._extract)
        self.extract_btn.setEnabled(False)
        btn_layout.addWidget(self.extract_btn)
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 GIF", "", SUPPORTED_GIF)
        if path:
            self._gif_path = path
            self.path_edit.setText(path)
            self.preview.load_gif(path)
            try:
                gif = Image.open(path)
                frames = 0
                try:
                    while True:
                        frames += 1
                        gif.seek(gif.tell() + 1)
                except EOFError:
                    pass
                w, h = gif.size
                self.info_label.setText(f"尺寸: {w}×{h} | 帧数: {frames}")
            except:
                self.info_label.setText("")
            self.extract_btn.setEnabled(True)

    def _extract(self):
        if not self._gif_path:
            return
        out_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not out_dir:
            return

        self.extract_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        fmt = self.fmt_combo.currentText().lower()
        self.worker = FrameExtractWorker(self._gif_path, out_dir, fmt)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, msg):
        self.progress.setVisible(False)
        self.extract_btn.setEnabled(True)
        QMessageBox.information(self, "完成", msg)

    def _on_error(self, msg):
        self.progress.setVisible(False)
        self.extract_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


# ─── Tab: GIF Info / Preview ─────────────────────────────────────────────────

class GifInfoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File
        file_group = QGroupBox("📁 选择 GIF 文件")
        fg = QHBoxLayout(file_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 GIF 文件或拖放到下方...")
        self.path_edit.setReadOnly(True)
        fg.addWidget(self.path_edit, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse)
        fg.addWidget(browse_btn)
        layout.addWidget(file_group)

        # Info
        self.info_text = QLabel("")
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet(f"""
            color: {TEXT_COLOR};
            background: {BG_COLOR};
            padding: 12px;
            border-radius: 8px;
            font-family: "Consolas", monospace;
            line-height: 1.6;
        """)
        layout.addWidget(self.info_text)

        # Preview
        self.preview = GifPreviewWidget()
        layout.addWidget(self.preview, 1)

        # Controls
        ctrl = QHBoxLayout()
        play_btn = QPushButton("▶ 播放")
        play_btn.clicked.connect(lambda: self.preview.play())
        ctrl.addWidget(play_btn)
        pause_btn = QPushButton("⏸ 暂停")
        pause_btn.clicked.connect(lambda: self.preview.pause())
        ctrl.addWidget(pause_btn)
        prev_btn = QPushButton("⏮ 上一帧")
        prev_btn.clicked.connect(lambda: self.preview.prev_frame())
        ctrl.addWidget(prev_btn)
        next_btn = QPushButton("⏭ 下一帧")
        next_btn.clicked.connect(lambda: self.preview.next_frame())
        ctrl.addWidget(next_btn)

        self.frame_label = QLabel("")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl.addWidget(self.frame_label)
        layout.addLayout(ctrl)

        # Timer for frame info
        self._info_timer = QTimer()
        self._info_timer.timeout.connect(self._update_frame_info)
        self._info_timer.start(100)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 GIF", "", SUPPORTED_GIF)
        if path:
            self._load(path)

    def _load(self, path):
        self.path_edit.setText(path)
        try:
            gif = Image.open(path)
            w, h = gif.size
            frames = 0
            total_duration = 0
            try:
                while True:
                    dur = gif.info.get("duration", 100)
                    total_duration += dur
                    frames += 1
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass

            size = os.path.getsize(path)
            self.info_text.setText(
                f"📄 文件: {os.path.basename(path)}\n"
                f"📦 大小: {format_size(size)}\n"
                f"📐 尺寸: {w} × {h} 像素\n"
                f"🎞️ 帧数: {frames}\n"
                f"⏱️ 总时长: {total_duration/1000:.2f} 秒\n"
                f"🔄 循环: {'是' if gif.info.get('loop', 0) == 0 else '否'}"
            )
            self.preview.load_gif(path)
        except Exception as e:
            self.info_text.setText(f"读取失败: {e}")

    def _update_frame_info(self):
        total = self.preview.get_frame_count()
        current = self.preview.get_current_index()
        if total > 0:
            self.frame_label.setText(f"帧 {current + 1}/{total}")


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Maker - 专业 GIF 制作与编辑工具")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("🎬 GIF Maker")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        subtitle = QLabel("专业 GIF 制作与编辑工具")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px;")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        header_layout.addWidget(version)
        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(VideoToGifTab(), "🎬 视频转 GIF")
        self.tabs.addTab(ImagesToGifTab(), "🖼️ 图片合成 GIF")
        self.tabs.addTab(ScreenRecordTab(), "📺 屏幕录制")
        self.tabs.addTab(GifEditorTab(), "✏️ GIF 编辑器")
        self.tabs.addTab(GifOptimizerTab(), "📦 GIF 优化器")
        self.tabs.addTab(FrameExtractorTab(), "🎞️ 帧提取器")
        self.tabs.addTab(GifInfoTab(), "👁️ GIF 预览")
        main_layout.addWidget(self.tabs, 1)

        # Status bar
        status = QWidget()
        status.setFixedHeight(30)
        status.setStyleSheet(f"background: {CARD_COLOR}; border-top: 1px solid {BORDER_COLOR};")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(16, 0, 16, 0)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        mem_label = QLabel("Powered by PyQt6 + Pillow + imageio")
        mem_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        status_layout.addWidget(mem_label)
        main_layout.addWidget(status)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Set default font
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
