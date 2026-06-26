#!/usr/bin/env python3
"""
ImageBatch - 批量图片处理工具
支持批量调整大小、格式转换、压缩、重命名、水印、旋转翻转
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QListWidget,
    QTabWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QGroupBox, QFormLayout, QGridLayout, QProgressBar,
    QMessageBox, QScrollArea, QFrame, QSplitter,
    QColorDialog, QSlider
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QUrl
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QDragEnterEvent, QDropEvent
)


# ─── 全局样式 ────────────────────────────────────────────────────────────────

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QTabWidget::pane {
    border: 1px solid #222233;
    border-radius: 8px;
    background-color: #111122;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #9999aa;
    border: 1px solid #222233;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    margin-right: 2px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #111122;
    color: #ffffff;
    border-bottom: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
}

QTabBar::tab:hover {
    background-color: #222244;
    color: #ccccdd;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #222233;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
    font-size: 13px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
    color: #667eea;
}

QPushButton {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #2a2a4e;
    border: 1px solid #4444aa;
}

QPushButton:pressed {
    background-color: #333366;
}

QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 24px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #778efb, stop:1 #875bb3);
}

QPushButton#dangerBtn {
    background-color: #4a1a1a;
    color: #ff6b6b;
    border: 1px solid #663333;
}

QPushButton#dangerBtn:hover {
    background-color: #5a2a2a;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0a0a1a;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #9999aa;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #333355;
    selection-background-color: #667eea;
}

QListWidget {
    background-color: #0a0a1a;
    color: #e0e0e0;
    border: 1px solid #222233;
    border-radius: 8px;
    padding: 5px;
    font-size: 12px;
}

QListWidget::item {
    padding: 5px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #222244;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #1a1a3e;
}

QProgressBar {
    background-color: #0a0a1a;
    border: 1px solid #222233;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 5px;
}

QScrollArea {
    border: none;
    background-color: #0a0a0a;
}

QScrollBar:vertical {
    background-color: #0a0a1a;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #333355;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4444aa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QSlider::groove:horizontal {
    height: 6px;
    background-color: #0a0a1a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
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

QLabel#cardTitle {
    color: #667eea;
    font-weight: bold;
    font-size: 14px;
}

QLabel#cardDesc {
    color: #8888aa;
    font-size: 11px;
}

QFrame#card {
    background-color: #111122;
    border: 1px solid #222233;
    border-radius: 10px;
    padding: 15px;
}

QCheckBox {
    color: #e0e0e0;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #333355;
    border-radius: 3px;
    background-color: #0a0a1a;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-color: #667eea;
}

QSplitter::handle {
    background-color: #222233;
    width: 2px;
}

QLabel#thumbLabel {
    border: 2px solid transparent;
    border-radius: 6px;
    padding: 2px;
}

QLabel#thumbLabel:hover {
    border: 2px solid #667eea;
}
"""


# ─── 图片处理线程 ──────────────────────────────────────────────────────────────

class ImageProcessWorker(QThread):
    """图片处理工作线程"""
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(list)  # results
    error = pyqtSignal(str)

    def __init__(self, images: List[str], operations: List[Tuple], output_dir: str, output_format: str = ""):
        super().__init__()
        self.images = images
        self.operations = operations
        self.output_dir = output_dir
        self.output_format = output_format

    def run(self):
        results = []
        total = len(self.images)
        for i, img_path in enumerate(self.images):
            try:
                img = Image.open(img_path)
                if img.mode == 'RGBA' and self.output_format.upper() in ('JPG', 'JPEG'):
                    img = img.convert('RGB')
                
                for op_type, params in self.operations:
                    img = self._apply_operation(img, op_type, params)
                
                # 确定输出路径
                original = Path(img_path)
                if self.output_dir:
                    out_dir = Path(self.output_dir)
                else:
                    out_dir = original.parent / "ImageBatch_output"
                out_dir.mkdir(parents=True, exist_ok=True)
                
                fmt = self.output_format or original.suffix.lstrip('.')
                if fmt.lower() in ('jpg', 'jpeg'):
                    fmt = 'JPEG'
                elif fmt.lower() == 'png':
                    fmt = 'PNG'
                elif fmt.lower() == 'webp':
                    fmt = 'WebP'
                elif fmt.lower() == 'bmp':
                    fmt = 'BMP'
                else:
                    fmt = 'PNG'
                
                ext_map = {'JPEG': '.jpg', 'PNG': '.png', 'WebP': '.webp', 'BMP': '.bmp'}
                ext = ext_map.get(fmt, '.png')
                
                # 处理重命名
                new_name = original.stem + ext
                
                # 检查重命名操作
                for op_t, op_p in self.operations:
                    if op_t == 'rename' and 'final_name' in op_p:
                        new_name = op_p['final_name']
                        if not new_name.endswith(ext):
                            new_name = Path(new_name).stem + ext
                
                out_path = out_dir / new_name
                
                # 处理压缩质量
                quality = 85
                for op_t, op_p in self.operations:
                    if op_t == 'compress':
                        quality = op_p.get('quality', 85)
                
                save_kwargs = {}
                if fmt in ('JPEG', 'WebP'):
                    save_kwargs['quality'] = quality
                if fmt == 'PNG':
                    save_kwargs['optimize'] = True
                if fmt == 'JPEG':
                    save_kwargs['optimize'] = True
                
                if img.mode == 'RGBA' and fmt == 'JPEG':
                    img = img.convert('RGB')
                
                img.save(str(out_path), fmt, **save_kwargs)
                results.append(str(out_path))
            except Exception as e:
                results.append(f"ERROR:{img_path}:{str(e)}")
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit(results)

    def _apply_operation(self, img: Image.Image, op_type: str, params: dict) -> Image.Image:
        if op_type == 'resize':
            mode = params.get('mode', 'percent')
            if mode == 'percent':
                scale = params.get('percent', 100) / 100.0
                new_w = int(img.width * scale)
                new_h = int(img.height * scale)
            else:
                new_w = params.get('width', img.width)
                new_h = params.get('height', img.height)
                if params.get('keep_ratio', False):
                    ratio = min(new_w / img.width, new_h / img.height)
                    new_w = int(img.width * ratio)
                    new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        elif op_type == 'rotate':
            angle = params.get('angle', 0)
            if angle != 0:
                img = img.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
        
        elif op_type == 'flip':
            direction = params.get('direction', 'horizontal')
            if direction == 'horizontal':
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            else:
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        elif op_type == 'watermark_text':
            text = params.get('text', '')
            if text:
                img = self._add_text_watermark(img, params)
        
        elif op_type == 'watermark_image':
            wm_path = params.get('path', '')
            if wm_path and os.path.exists(wm_path):
                img = self._add_image_watermark(img, params)
        
        return img

    def _add_text_watermark(self, img: Image.Image, params: dict) -> Image.Image:
        text = params.get('text', 'Watermark')
        font_size = params.get('font_size', 36)
        opacity = params.get('opacity', 128)
        position = params.get('position', '右下角')
        color = params.get('color', '#ffffff')
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", font_size)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        positions = {
            '左上角': (10, 10),
            '右上角': (img.width - tw - 10, 10),
            '左下角': (10, img.height - th - 10),
            '右下角': (img.width - tw - 10, img.height - th - 10),
            '居中': ((img.width - tw) // 2, (img.height - th) // 2),
        }
        pos = positions.get(position, positions['右下角'])
        
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        draw.text(pos, text, fill=(r, g, b, opacity), font=font)
        
        return Image.alpha_composite(img, txt_layer)

    def _add_image_watermark(self, img: Image.Image, params: dict) -> Image.Image:
        wm_path = params.get('path', '')
        scale = params.get('scale', 20) / 100.0
        opacity = params.get('opacity', 128) / 255.0
        position = params.get('position', '右下角')
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        wm = Image.open(wm_path).convert('RGBA')
        wm_w = int(img.width * scale)
        wm_h = int(wm.height * (wm_w / wm.width))
        wm = wm.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        
        # 应用透明度
        r, g, b, a = wm.split()
        a = a.point(lambda x: int(x * opacity))
        wm = Image.merge('RGBA', (r, g, b, a))
        
        positions = {
            '左上角': (10, 10),
            '右上角': (img.width - wm_w - 10, 10),
            '左下角': (10, img.height - wm_h - 10),
            '右下角': (img.width - wm_w - 10, img.height - wm_h - 10),
            '居中': ((img.width - wm_w) // 2, (img.height - wm_h) // 2),
        }
        pos = positions.get(position, positions['右下角'])
        
        result = img.copy()
        result.paste(wm, pos, wm)
        return result


# ─── 缩略图预览组件 ─────────────────────────────────────────────────────────

class ThumbnailGrid(QWidget):
    """缩略图网格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.thumbnails = []

    def clear_thumbnails(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().deleteLater()
        self.thumbnails.clear()

    def add_thumbnail(self, pixmap: QPixmap, name: str):
        idx = len(self.thumbnails)
        col = idx % 4
        row = idx // 4

        container = QWidget()
        container.setFixedSize(140, 160)
        container.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border: 1px solid #222233;
                border-radius: 8px;
            }
            QWidget:hover {
                border: 1px solid #667eea;
                background-color: #1a1a3e;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        thumb = QLabel()
        thumb.setFixedSize(128, 120)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scaled = pixmap.scaled(126, 118, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        thumb.setPixmap(scaled)
        thumb.setStyleSheet("border: none; background: transparent;")

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #aaaacc; font-size: 10px; border: none; background: transparent;")
        name_lbl.setMaximumHeight(20)

        layout.addWidget(thumb)
        layout.addWidget(name_lbl)

        self.grid_layout.addWidget(container, row, col)
        self.thumbnails.append(container)


# ─── 功能面板基类 ─────────────────────────────────────────────────────────

class OperationPanel(QWidget):
    """操作面板基类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)

    def get_operations(self) -> List[Tuple]:
        """返回操作列表 [(op_type, params), ...]"""
        return []


class ResizePanel(OperationPanel):
    """调整大小面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 模式选择
        mode_group = QGroupBox("缩放模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.percent_radio = QCheckBox("按百分比缩放")
        self.percent_radio.setChecked(True)
        self.percent_radio.toggled.connect(self._update_mode)
        
        self.percent_spin = QDoubleSpinBox()
        self.percent_spin.setRange(1, 1000)
        self.percent_spin.setValue(100)
        self.percent_spin.setSuffix(" %")
        
        self.size_radio = QCheckBox("按固定尺寸")
        self.size_radio.toggled.connect(self._update_mode)
        
        size_widget = QWidget()
        size_layout = QFormLayout(size_widget)
        size_layout.setContentsMargins(0, 5, 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(600)
        self.height_spin.setSuffix(" px")
        self.keep_ratio = QCheckBox("保持宽高比")
        self.keep_ratio.setChecked(True)
        size_layout.addRow("宽度:", self.width_spin)
        size_layout.addRow("高度:", self.height_spin)
        size_layout.addRow(self.keep_ratio)
        
        self.size_widget = size_widget
        self.size_widget.setVisible(False)
        
        mode_layout.addWidget(self.percent_radio)
        mode_layout.addWidget(self.percent_spin)
        mode_layout.addWidget(self.size_radio)
        mode_layout.addWidget(self.size_widget)
        
        self.layout.addWidget(mode_group)
        self.layout.addStretch()

    def _update_mode(self):
        if self.percent_radio.isChecked():
            self.size_widget.setVisible(False)
            self.percent_spin.setVisible(True)
        else:
            self.size_widget.setVisible(True)
            self.percent_spin.setVisible(False)

    def get_operations(self):
        if self.percent_radio.isChecked():
            return [('resize', {'mode': 'percent', 'percent': self.percent_spin.value()})]
        else:
            return [('resize', {
                'mode': 'fixed',
                'width': self.width_spin.value(),
                'height': self.height_spin.value(),
                'keep_ratio': self.keep_ratio.isChecked()
            })]


class FormatPanel(OperationPanel):
    """格式转换面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        group = QGroupBox("目标格式")
        layout = QFormLayout(group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WebP", "BMP"])
        
        layout.addRow("输出格式:", self.format_combo)
        
        self.layout.addWidget(group)
        self.layout.addStretch()

    def get_format(self):
        return self.format_combo.currentText()


class CompressPanel(OperationPanel):
    """压缩面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        group = QGroupBox("压缩设置")
        layout = QVBoxLayout(group)
        
        form = QFormLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self._update_label)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setStyleSheet("color: #667eea; font-weight: bold; font-size: 14px;")
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.quality_slider)
        slider_layout.addWidget(self.quality_label)
        
        form.addRow("压缩质量:", slider_layout)
        
        self.hint_label = QLabel("提示: 80-95% 质量较好，文件大小适中")
        self.hint_label.setStyleSheet("color: #666688; font-size: 11px;")
        
        layout.addLayout(form)
        layout.addWidget(self.hint_label)
        
        self.layout.addWidget(group)
        self.layout.addStretch()

    def _update_label(self, val):
        self.quality_label.setText(f"{val}%")
        if val >= 90:
            hint = "提示: 高质量，文件较大"
        elif val >= 70:
            hint = "提示: 质量与大小平衡"
        elif val >= 50:
            hint = "提示: 中等压缩，质量有所损失"
        else:
            hint = "提示: 高压缩，质量损失明显"
        self.hint_label.setText(hint)

    def get_quality(self):
        return self.quality_slider.value()


class RenamePanel(OperationPanel):
    """重命名面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 模式选择
        mode_group = QGroupBox("命名模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["顺序命名", "添加前缀/后缀", "查找替换"])
        self.mode_combo.currentIndexChanged.connect(self._update_mode)
        mode_layout.addWidget(self.mode_combo)
        
        # 顺序命名
        self.seq_widget = QWidget()
        seq_layout = QFormLayout(self.seq_widget)
        seq_layout.setContentsMargins(0, 5, 0, 0)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("例如: photo_")
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, 99999)
        self.start_spin.setValue(1)
        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(1, 10)
        self.digits_spin.setValue(3)
        seq_layout.addRow("前缀:", self.prefix_edit)
        seq_layout.addRow("起始编号:", self.start_spin)
        seq_layout.addRow("编号位数:", self.digits_spin)
        
        # 前缀后缀
        self.affix_widget = QWidget()
        affix_layout = QFormLayout(self.affix_widget)
        affix_layout.setContentsMargins(0, 5, 0, 0)
        self.add_prefix = QLineEdit()
        self.add_prefix.setPlaceholderText("例如: vacation_")
        self.add_suffix = QLineEdit()
        self.add_suffix.setPlaceholderText("例如: _edited")
        affix_layout.addRow("添加前缀:", self.add_prefix)
        affix_layout.addRow("添加后缀:", self.add_suffix)
        self.affix_widget.setVisible(False)
        
        # 查找替换
        self.replace_widget = QWidget()
        replace_layout = QFormLayout(self.replace_widget)
        replace_layout.setContentsMargins(0, 5, 0, 0)
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("查找文本")
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("替换为")
        replace_layout.addRow("查找:", self.find_edit)
        replace_layout.addRow("替换为:", self.replace_edit)
        self.replace_widget.setVisible(False)
        
        mode_layout.addWidget(self.seq_widget)
        mode_layout.addWidget(self.affix_widget)
        mode_layout.addWidget(self.replace_widget)
        
        self.layout.addWidget(mode_group)
        self.layout.addStretch()

    def _update_mode(self, idx):
        self.seq_widget.setVisible(idx == 0)
        self.affix_widget.setVisible(idx == 1)
        self.replace_widget.setVisible(idx == 2)

    def get_rename_info(self):
        mode = self.mode_combo.currentIndex()
        if mode == 0:
            return {
                'mode': 'sequential',
                'prefix': self.prefix_edit.text(),
                'start': self.start_spin.value(),
                'digits': self.digits_spin.value()
            }
        elif mode == 1:
            return {
                'mode': 'affix',
                'prefix': self.add_prefix.text(),
                'suffix': self.add_suffix.text()
            }
        else:
            return {
                'mode': 'replace',
                'find': self.find_edit.text(),
                'replace': self.replace_edit.text()
            }


class WatermarkPanel(OperationPanel):
    """水印面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 水印类型
        type_group = QGroupBox("水印类型")
        type_layout = QVBoxLayout(type_group)
        
        self.text_radio = QCheckBox("文字水印")
        self.text_radio.setChecked(True)
        self.text_radio.toggled.connect(self._update_type)
        self.image_radio = QCheckBox("图片水印")
        self.image_radio.toggled.connect(self._update_type)
        
        type_layout.addWidget(self.text_radio)
        type_layout.addWidget(self.image_radio)
        
        # 文字水印设置
        self.text_widget = QWidget()
        text_layout = QFormLayout(self.text_widget)
        text_layout.setContentsMargins(0, 5, 0, 0)
        
        self.wm_text = QLineEdit()
        self.wm_text.setPlaceholderText("请输入水印文字")
        self.wm_text.setText("© ImageBatch")
        
        self.wm_font_size = QSpinBox()
        self.wm_font_size.setRange(8, 200)
        self.wm_font_size.setValue(36)
        
        self.wm_opacity = QSlider(Qt.Orientation.Horizontal)
        self.wm_opacity.setRange(10, 255)
        self.wm_opacity.setValue(128)
        
        opacity_layout = QHBoxLayout()
        self.opacity_label = QLabel("50%")
        opacity_layout.addWidget(self.wm_opacity)
        opacity_layout.addWidget(self.opacity_label)
        self.wm_opacity.valueChanged.connect(lambda v: self.opacity_label.setText(f"{int(v/255*100)}%"))
        
        self.wm_color = QPushButton("选择颜色")
        self.wm_color_val = "#ffffff"
        self.wm_color.setStyleSheet(f"background-color: {self.wm_color_val}; color: #000;")
        self.wm_color.clicked.connect(self._pick_color)
        
        text_layout.addRow("水印文字:", self.wm_text)
        text_layout.addRow("字体大小:", self.wm_font_size)
        text_layout.addRow("透明度:", opacity_layout)
        text_layout.addRow("颜色:", self.wm_color)
        
        # 图片水印设置
        self.image_widget = QWidget()
        img_layout = QFormLayout(self.image_widget)
        img_layout.setContentsMargins(0, 5, 0, 0)
        
        browse_layout = QHBoxLayout()
        self.wm_image_path = QLineEdit()
        self.wm_image_path.setPlaceholderText("选择水印图片...")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse_wm_image)
        browse_layout.addWidget(self.wm_image_path)
        browse_layout.addWidget(browse_btn)
        
        self.wm_scale = QSpinBox()
        self.wm_scale.setRange(5, 100)
        self.wm_scale.setValue(20)
        self.wm_scale.setSuffix(" %")
        
        self.wm_img_opacity = QSlider(Qt.Orientation.Horizontal)
        self.wm_img_opacity.setRange(10, 255)
        self.wm_img_opacity.setValue(128)
        
        img_opacity_layout = QHBoxLayout()
        self.img_opacity_label = QLabel("50%")
        img_opacity_layout.addWidget(self.wm_img_opacity)
        img_opacity_layout.addWidget(self.img_opacity_label)
        self.wm_img_opacity.valueChanged.connect(lambda v: self.img_opacity_label.setText(f"{int(v/255*100)}%"))
        
        img_layout.addRow("水印图片:", browse_layout)
        img_layout.addRow("缩放比例:", self.wm_scale)
        img_layout.addRow("透明度:", img_opacity_layout)
        
        self.image_widget.setVisible(False)
        
        # 位置选择
        pos_group = QGroupBox("水印位置")
        pos_layout = QVBoxLayout(pos_group)
        self.position_combo = QComboBox()
        self.position_combo.addItems(["左上角", "右上角", "居中", "左下角", "右下角"])
        self.position_combo.setCurrentText("右下角")
        pos_layout.addWidget(self.position_combo)
        
        self.layout.addWidget(type_group)
        self.layout.addWidget(self.text_widget)
        self.layout.addWidget(self.image_widget)
        self.layout.addWidget(pos_group)
        self.layout.addStretch()

    def _update_type(self):
        self.text_widget.setVisible(self.text_radio.isChecked())
        self.image_widget.setVisible(self.image_radio.isChecked())

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.wm_color_val), self, "选择水印颜色")
        if color.isValid():
            self.wm_color_val = color.name()
            self.wm_color.setStyleSheet(f"background-color: {self.wm_color_val}; color: #000;")

    def _browse_wm_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff)"
        )
        if path:
            self.wm_image_path.setText(path)

    def get_operations(self):
        position = self.position_combo.currentText()
        if self.text_radio.isChecked():
            text = self.wm_text.text()
            if text:
                return [('watermark_text', {
                    'text': text,
                    'font_size': self.wm_font_size.value(),
                    'opacity': self.wm_opacity.value(),
                    'color': self.wm_color_val,
                    'position': position
                })]
        else:
            path = self.wm_image_path.text()
            if path and os.path.exists(path):
                return [('watermark_image', {
                    'path': path,
                    'scale': self.wm_scale.value(),
                    'opacity': self.wm_img_opacity.value(),
                    'position': position
                })]
        return []


class RotatePanel(OperationPanel):
    """旋转翻转面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 旋转
        rotate_group = QGroupBox("旋转")
        rotate_layout = QVBoxLayout(rotate_group)
        
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["不旋转", "顺时针 90°", "顺时针 180°", "顺时针 270°"])
        rotate_layout.addWidget(self.rotate_combo)
        
        # 翻转
        flip_group = QGroupBox("翻转")
        flip_layout = QVBoxLayout(flip_group)
        
        self.flip_h = QCheckBox("水平翻转")
        self.flip_v = QCheckBox("垂直翻转")
        
        flip_layout.addWidget(self.flip_h)
        flip_layout.addWidget(self.flip_v)
        
        self.layout.addWidget(rotate_group)
        self.layout.addWidget(flip_group)
        self.layout.addStretch()

    def get_operations(self):
        ops = []
        angle_map = {0: 0, 1: 90, 2: 180, 3: 270}
        angle = angle_map.get(self.rotate_combo.currentIndex(), 0)
        if angle != 0:
            ops.append(('rotate', {'angle': angle}))
        if self.flip_h.isChecked():
            ops.append(('flip', {'direction': 'horizontal'}))
        if self.flip_v.isChecked():
            ops.append(('flip', {'direction': 'vertical'}))
        return ops


# ─── 主窗口 ────────────────────────────────────────────────────────────────

class ImageBatchWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImageBatch - 批量图片处理工具")
        self.setMinimumSize(1200, 750)
        self.resize(1300, 800)
        self.images: List[str] = []
        self.worker = None
        self.output_dir = ""
        self._init_ui()
        self.setAcceptDrops(True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 左侧：图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("📷 ImageBatch")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #667eea;")
        left_layout.addWidget(title_label)

        # 添加图片按钮
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 添加图片")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_images)
        
        add_folder_btn = QPushButton("📁 添加文件夹")
        add_folder_btn.clicked.connect(self._add_folder)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.clicked.connect(self._clear_images)
        
        btn_row.addWidget(add_btn)
        btn_row.addWidget(add_folder_btn)
        btn_row.addWidget(clear_btn)
        left_layout.addLayout(btn_row)

        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left_layout.addWidget(self.image_list)

        # 图片计数
        self.count_label = QLabel("已添加 0 张图片")
        self.count_label.setStyleSheet("color: #666688; font-size: 11px;")
        left_layout.addWidget(self.count_label)

        # 输出目录
        out_row = QHBoxLayout()
        out_label = QLabel("📂 输出目录:")
        out_label.setStyleSheet("color: #aaaacc; font-size: 12px;")
        self.out_path_edit = QLineEdit()
        self.out_path_edit.setPlaceholderText("默认: 原目录/ImageBatch_output")
        out_browse = QPushButton("浏览")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(out_label)
        out_row.addWidget(self.out_path_edit)
        out_row.addWidget(out_browse)
        left_layout.addLayout(out_row)

        # 右侧：功能选项卡和预览
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 功能选项卡
        self.tabs = QTabWidget()
        self.resize_panel = ResizePanel()
        self.format_panel = FormatPanel()
        self.compress_panel = CompressPanel()
        self.rename_panel = RenamePanel()
        self.watermark_panel = WatermarkPanel()
        self.rotate_panel = RotatePanel()
        
        self.tabs.addTab(self.resize_panel, "📐 调整大小")
        self.tabs.addTab(self.format_panel, "🔄 格式转换")
        self.tabs.addTab(self.compress_panel, "📦 压缩")
        self.tabs.addTab(self.rename_panel, "✏️ 重命名")
        self.tabs.addTab(self.watermark_panel, "💧 水印")
        self.tabs.addTab(self.rotate_panel, "🔃 旋转翻转")
        
        right_layout.addWidget(self.tabs, 1)

        # 预览区域
        preview_frame = QFrame()
        preview_frame.setObjectName("card")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setSpacing(8)
        
        preview_header = QHBoxLayout()
        preview_title = QLabel("👀 预览")
        preview_title.setObjectName("cardTitle")
        preview_header.addWidget(preview_title)
        
        preview_btn = QPushButton("预览效果")
        preview_btn.clicked.connect(self._preview_effect)
        preview_header.addWidget(preview_btn)
        preview_header.addStretch()
        
        preview_layout.addLayout(preview_header)
        
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_grid = ThumbnailGrid()
        self.preview_scroll.setWidget(self.preview_grid)
        self.preview_scroll.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_scroll)
        
        right_layout.addWidget(preview_frame)

        # 进度条和执行按钮
        bottom_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m")
        bottom_row.addWidget(self.progress_bar, 1)
        
        self.exec_btn = QPushButton("🚀 开始处理")
        self.exec_btn.setObjectName("primaryBtn")
        self.exec_btn.clicked.connect(self._execute)
        bottom_row.addWidget(self.exec_btn)
        
        right_layout.addLayout(bottom_row)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666688; font-size: 11px;")
        right_layout.addWidget(self.status_label)

        # 添加到主布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([320, 680])
        main_layout.addWidget(splitter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        img_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path) and Path(path).suffix.lower() in img_exts:
                if path not in self.images:
                    self.images.append(path)
                    self.image_list.addItem(os.path.basename(path))
            elif os.path.isdir(path):
                for f in sorted(os.listdir(path)):
                    fp = os.path.join(path, f)
                    if os.path.isfile(fp) and Path(f).suffix.lower() in img_exts:
                        if fp not in self.images:
                            self.images.append(fp)
                            self.image_list.addItem(f)
        self._update_count()

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff *.tif);;所有文件 (*)"
        )
        for f in files:
            if f not in self.images:
                self.images.append(f)
                self.image_list.addItem(os.path.basename(f))
        self._update_count()

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            img_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
            for f in sorted(os.listdir(folder)):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp) and Path(f).suffix.lower() in img_exts:
                    if fp not in self.images:
                        self.images.append(fp)
                        self.image_list.addItem(f)
            self._update_count()

    def _clear_images(self):
        self.images.clear()
        self.image_list.clear()
        self.preview_grid.clear_thumbnails()
        self._update_count()

    def _update_count(self):
        count = len(self.images)
        self.count_label.setText(f"已添加 {count} 张图片")
        self.progress_bar.setRange(0, count)
        self.progress_bar.setValue(0)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.output_dir = folder
            self.out_path_edit.setText(folder)

    def _preview_effect(self):
        if not self.images:
            QMessageBox.information(self, "提示", "请先添加图片！")
            return
        
        self.preview_grid.clear_thumbnails()
        self.status_label.setText("正在生成预览...")
        
        # 预览前几张
        preview_count = min(8, len(self.images))
        for i in range(preview_count):
            try:
                img = Image.open(self.images[i])
                
                # 应用当前操作预览
                ops = self._collect_operations()
                for op_type, params in ops:
                    img = self._apply_preview_op(img, op_type, params)
                
                # 转为 QPixmap
                if img.mode == 'RGBA':
                    qimg = QImage(img.tobytes(), img.width, img.height,
                                  img.width * 4, QImage.Format.Format_RGBA8888)
                else:
                    img = img.convert('RGB')
                    qimg = QImage(img.tobytes(), img.width, img.height,
                                  img.width * 3, QImage.Format.Format_RGB888)
                
                pixmap = QPixmap.fromImage(qimg)
                name = os.path.basename(self.images[i])
                self.preview_grid.add_thumbnail(pixmap, name)
            except Exception as e:
                print(f"Preview error: {e}")
        
        self.status_label.setText(f"已预览 {preview_count} 张图片")

    def _apply_preview_op(self, img: Image.Image, op_type: str, params: dict) -> Image.Image:
        try:
            if op_type == 'resize':
                mode = params.get('mode', 'percent')
                if mode == 'percent':
                    scale = params.get('percent', 100) / 100.0
                    new_w = max(1, int(img.width * scale))
                    new_h = max(1, int(img.height * scale))
                else:
                    new_w = params.get('width', img.width)
                    new_h = params.get('height', img.height)
                    if params.get('keep_ratio', False):
                        ratio = min(new_w / img.width, new_h / img.height)
                        new_w = max(1, int(img.width * ratio))
                        new_h = max(1, int(img.height * ratio))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            elif op_type == 'rotate':
                angle = params.get('angle', 0)
                if angle != 0:
                    img = img.rotate(-angle, expand=True)
            elif op_type == 'flip':
                d = params.get('direction', 'horizontal')
                if d == 'horizontal':
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                else:
                    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        except Exception:
            pass
        return img

    def _collect_operations(self):
        ops = []
        idx = self.tabs.currentIndex()
        
        if idx == 0:  # resize
            ops.extend(self.resize_panel.get_operations())
        elif idx == 2:  # compress
            ops.append(('compress', {'quality': self.compress_panel.get_quality()}))
        elif idx == 4:  # watermark
            ops.extend(self.watermark_panel.get_operations())
        elif idx == 5:  # rotate
            ops.extend(self.rotate_panel.get_operations())
        
        return ops

    def _execute(self):
        if not self.images:
            QMessageBox.information(self, "提示", "请先添加图片！")
            return
        
        ops = self._collect_operations()
        
        # 收集重命名信息
        rename_info = None
        if self.tabs.currentIndex() == 3:
            rename_info = self.rename_panel.get_rename_info()
        
        # 格式
        out_format = ""
        if self.tabs.currentIndex() == 1:
            out_format = self.format_panel.get_format()
        
        # 如果没有操作，添加一个默认的
        if not ops and not out_format and not rename_info:
            QMessageBox.information(self, "提示", "请先配置处理参数！")
            return
        
        # 处理重命名
        if rename_info:
            mode = rename_info['mode']
            for i, img_path in enumerate(self.images):
                original = Path(img_path)
                if mode == 'sequential':
                    num = rename_info['start'] + i
                    digits = rename_info['digits']
                    new_name = f"{rename_info['prefix']}{str(num).zfill(digits)}"
                elif mode == 'affix':
                    new_name = f"{rename_info['prefix']}{original.stem}{rename_info['suffix']}"
                else:
                    new_name = original.stem.replace(rename_info['find'], rename_info['replace'])
                
                # 添加重命名操作
                rename_ops = list(ops)
                rename_ops.append(('rename', {'final_name': new_name}))
                
                # 这里需要修改，为每张图设置不同的重命名
                # 实际处理在线程中，需要特殊处理
        
        # 输出目录
        out_dir = self.out_path_edit.text() or ""
        
        self.exec_btn.setEnabled(False)
        self.status_label.setText("正在处理...")
        self.progress_bar.setRange(0, len(self.images))
        self.progress_bar.setValue(0)
        
        # 处理重命名的特殊情况
        if rename_info:
            self._execute_with_rename(ops, rename_info, out_dir, out_format)
            return
        
        self.worker = ImageProcessWorker(self.images, ops, out_dir, out_format)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _execute_with_rename(self, ops, rename_info, out_dir, out_format):
        """带重命名的特殊处理"""
        mode = rename_info['mode']
        all_ops = []
        
        for i, img_path in enumerate(self.images):
            original = Path(img_path)
            if mode == 'sequential':
                num = rename_info['start'] + i
                digits = rename_info['digits']
                new_name = f"{rename_info['prefix']}{str(num).zfill(digits)}"
            elif mode == 'affix':
                new_name = f"{rename_info['prefix']}{original.stem}{rename_info['suffix']}"
            else:
                new_name = original.stem.replace(rename_info['find'], rename_info['replace'])
            
            img_ops = list(ops)
            img_ops.append(('rename', {'final_name': new_name}))
            all_ops.append(img_ops)
        
        # 为每张图片单独处理
        self._rename_ops = all_ops
        self._rename_idx = 0
        self._rename_results = []
        self._rename_out_dir = out_dir
        self._rename_out_format = out_format
        self._process_next_rename()

    def _process_next_rename(self):
        if self._rename_idx >= len(self.images):
            self._on_finished(self._rename_results)
            return
        
        i = self._rename_idx
        ops = self._rename_ops[i]
        
        worker = ImageProcessWorker([self.images[i]], ops, self._rename_out_dir, self._rename_out_format)
        worker.progress.connect(lambda c, t: self._on_progress(i + 1, len(self.images)))
        worker.finished.connect(self._on_rename_finished)
        worker.start()
        self._rename_worker = worker

    def _on_rename_finished(self, results):
        self._rename_results.extend(results)
        self._rename_idx += 1
        self._process_next_rename()

    def _on_progress(self, current, total):
        self.progress_bar.setValue(current)
        self.status_label.setText(f"处理中... {current}/{total}")

    def _on_finished(self, results):
        self.exec_btn.setEnabled(True)
        
        errors = [r for r in results if r.startswith("ERROR:")]
        success = [r for r in results if not r.startswith("ERROR:")]
        
        msg = f"处理完成！\n成功: {len(success)} 张\n失败: {len(errors)} 张"
        if errors:
            msg += "\n\n失败详情:\n" + "\n".join(errors[:5])
        
        QMessageBox.information(self, "完成", msg)
        self.status_label.setText(f"完成 - 成功 {len(success)} 张，失败 {len(errors)} 张")
        self.progress_bar.setValue(len(self.images))


# ─── 入口 ──────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setStyle("Fusion")
    
    window = ImageBatchWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
