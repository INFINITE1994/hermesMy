#!/usr/bin/env python3
"""
ScreenshotTool - 专业截图工具
支持全屏、区域、窗口截图，标注、模糊、取色等功能
"""

import sys
import os
import json
import time
import uuid
import ctypes
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, QFileDialog,
    QColorDialog, QFontDialog, QMessageBox, QSystemTrayIcon, QMenu,
    QToolBar, QSpinBox, QComboBox, QLineEdit, QDialog, QFormLayout,
    QSizePolicy, QSplitter, QTabWidget, QGroupBox, QSlider, QCheckBox,
    QToolButton, QButtonGroup, QTextEdit
)
from PyQt6.QtCore import (
    Qt, QRect, QPoint, QSize, QTimer, pyqtSignal, QThread, QObject,
    QPropertyAnimation, QEasingCurve, QByteArray, QBuffer, QIODevice,
    QMimeData, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPixmap, QColor, QPainter, QPen, QBrush, QFont, QIcon, QAction,
    QCursor, QImage, QScreen, QClipboard, QPainterPath, QPolygon,
    QLinearGradient, QRadialGradient, QFontMetrics, QTransform,
    QShortcut, QKeySequence, QDesktopServices
)
from PyQt6.QtCore import QUrl

try:
    from PIL import Image, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pynput import keyboard as pynput_keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False


# ============================================================================
# 配色方案
# ============================================================================
COLORS = {
    'bg': '#0a0a0a',
    'card': '#111122',
    'card_hover': '#161633',
    'border': '#222244',
    'text': '#e0e0ff',
    'text_secondary': '#8888aa',
    'accent_start': '#667eea',
    'accent_end': '#764ba2',
    'danger': '#ff4466',
    'success': '#44ff88',
    'warning': '#ffaa44',
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}
QWidget {{
    color: {COLORS['text']};
    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QFrame#card {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}
QPushButton {{
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {COLORS['card_hover']};
    border-color: {COLORS['accent_start']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_start']};
}}
QPushButton#accent {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
    border: none;
    color: white;
}}
QPushButton#accent:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_end']}, stop:1 {COLORS['accent_start']});
}}
QPushButton#danger {{
    background-color: {COLORS['danger']};
    border: none;
    color: white;
}}
QLabel {{
    color: {COLORS['text']};
}}
QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: white;
}}
QLabel#subtitle {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}
QToolBar {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
    spacing: 4px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text']};
    font-size: 13px;
}}
QToolButton:hover {{
    background-color: {COLORS['card_hover']};
    border-color: {COLORS['border']};
}}
QToolButton:checked {{
    background-color: {COLORS['accent_start']};
    border-color: {COLORS['accent_start']};
    color: white;
}}
QScrollArea {{
    border: none;
    background-color: {COLORS['bg']};
}}
QScrollBar:vertical {{
    background-color: {COLORS['bg']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent_start']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QComboBox {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 12px;
    color: {COLORS['text']};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent_start']};
}}
QSpinBox {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
    color: {COLORS['text']};
}}
QLineEdit {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent_start']};
}}
QSlider::groove:horizontal {{
    background-color: {COLORS['border']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background-color: {COLORS['accent_start']};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background-color: {COLORS['accent_end']};
}}
QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLORS['accent_start']};
}}
QCheckBox {{
    color: {COLORS['text']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_start']};
    border-color: {COLORS['accent_start']};
}}
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['card']};
}}
QTabBar::tab {{
    background-color: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    color: {COLORS['text_secondary']};
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {COLORS['card']};
    color: {COLORS['text']};
}}
QTextEdit {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text']};
}}
"""


# ============================================================================
# 工具函数
# ============================================================================

def create_gradient_pixmap(width: int, height: int,
                           color1: str, color2: str) -> QPixmap:
    """创建渐变色Pixmap"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0, QColor(color1))
    gradient.setColorAt(1, QColor(color2))
    painter.fillRect(pixmap.rect(), gradient)
    painter.end()
    return pixmap


def get_app_dir() -> Path:
    """获取应用数据目录"""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:
        base = Path.home() / '.config'
    app_dir = base / 'ScreenshotTool'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_history_dir() -> Path:
    """获取截图历史目录"""
    hdir = get_app_dir() / 'history'
    hdir.mkdir(parents=True, exist_ok=True)
    return hdir


# ============================================================================
# 区域选择覆盖窗口
# ============================================================================

class RegionSelector(QWidget):
    """全屏覆盖窗口，用于鼠标拖拽选择截图区域"""
    region_selected = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self, screen_pixmap: QPixmap):
        super().__init__()
        self.screen_pixmap = screen_pixmap
        self.start_pos = None
        self.end_pos = None
        self.is_dragging = False
        self.selected_rect = QRect()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.screen_pixmap)

        # 半透明遮罩
        overlay = QColor(0, 0, 0, 120)
        painter.fillRect(self.rect(), overlay)

        if not self.selected_rect.isNull():
            # 绘制选区（透明）
            painter.setClipRect(self.selected_rect)
            painter.drawPixmap(0, 0, self.screen_pixmap)
            painter.setClipping(False)

            # 选区边框
            pen = QPen(QColor(COLORS['accent_start']), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.selected_rect)

            # 尺寸标注
            size_text = f"{self.selected_rect.width()} × {self.selected_rect.height()}"
            font = QFont('Microsoft YaHei', 11)
            painter.setFont(font)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(size_text)
            th = fm.height()

            label_x = self.selected_rect.x()
            label_y = self.selected_rect.y() - th - 8
            if label_y < 0:
                label_y = self.selected_rect.y() + 4

            painter.fillRect(label_x, label_y, tw + 12, th + 4,
                             QColor(COLORS['accent_start']))
            painter.setPen(QColor('white'))
            painter.drawText(label_x + 6, label_y + th, size_text)

        # 提示文字
        if not self.is_dragging and self.selected_rect.isNull():
            font = QFont('Microsoft YaHei', 14)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "拖拽鼠标选择截图区域\n按 ESC 取消")

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_dragging = True
            self.selected_rect = QRect()
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.end_pos = event.pos()
            self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.end_pos = event.pos()
            self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            if self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                self.region_selected.emit(self.selected_rect)
                self.close()
            else:
                self.selected_rect = QRect()
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()


# ============================================================================
# 标注画布
# ============================================================================

class AnnotationCanvas(QWidget):
    """在截图上绘制标注"""
    annotation_changed = pyqtSignal()

    # 标注工具类型
    TOOL_NONE = 0
    TOOL_ARROW = 1
    TOOL_RECT = 2
    TOOL_CIRCLE = 3
    TOOL_TEXT = 4
    TOOL_FREEHAND = 5
    TOOL_BLUR = 6
    TOOL_COLOR_PICKER = 7

    def __init__(self):
        super().__init__()
        self.base_pixmap: Optional[QPixmap] = None
        self.annotations: list = []  # 所有标注对象
        self.current_tool = self.TOOL_NONE
        self.tool_color = QColor(COLORS['accent_start'])
        self.tool_width = 3
        self.font_size = 16
        self.is_drawing = False
        self.start_pos = None
        self.current_pos = None
        self.freehand_points: list = []
        self.text_input_pos = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.setMouseTracking(True)
        self.setMinimumSize(400, 300)

    def set_pixmap(self, pixmap: QPixmap):
        self.base_pixmap = pixmap
        self.annotations.clear()
        self.fit_to_widget()
        self.update()

    def fit_to_widget(self):
        if self.base_pixmap and self.base_pixmap.width() > 0:
            w = self.width() - 20
            h = self.height() - 20
            sw = w / self.base_pixmap.width()
            sh = h / self.base_pixmap.height()
            self.scale_factor = min(sw, sh, 1.0)
            scaled_w = int(self.base_pixmap.width() * self.scale_factor)
            scaled_h = int(self.base_pixmap.height() * self.scale_factor)
            self.offset_x = (self.width() - scaled_w) // 2
            self.offset_y = (self.height() - scaled_h) // 2

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_to_widget()

    def widget_to_image(self, pos: QPoint) -> QPoint:
        x = int((pos.x() - self.offset_x) / self.scale_factor)
        y = int((pos.y() - self.offset_y) / self.scale_factor)
        return QPoint(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 背景
        painter.fillRect(self.rect(), QColor(COLORS['bg']))

        if not self.base_pixmap:
            painter.setPen(QColor(COLORS['text_secondary']))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "请先截取一张图片")
            painter.end()
            return

        # 绘制缩放后的截图
        scaled = self.base_pixmap.scaled(
            int(self.base_pixmap.width() * self.scale_factor),
            int(self.base_pixmap.height() * self.scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(self.offset_x, self.offset_y, scaled)

        # 绘制所有标注
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale_factor, self.scale_factor)

        for ann in self.annotations:
            self._draw_annotation(painter, ann)

        # 绘制当前正在画的标注
        if self.is_drawing and self.start_pos and self.current_pos:
            sp = self.widget_to_image(self.start_pos)
            cp = self.widget_to_image(self.current_pos)
            temp_ann = {
                'tool': self.current_tool, 'start': sp, 'end': cp,
                'color': self.tool_color, 'width': self.tool_width
            }
            if self.current_tool == self.TOOL_FREEHAND:
                temp_ann['points'] = [self.widget_to_image(p)
                                      for p in self.freehand_points]
            self._draw_annotation(painter, temp_ann)

        painter.end()

    def _draw_annotation(self, painter: QPainter, ann: dict):
        tool = ann.get('tool', self.TOOL_NONE)
        color = ann.get('color', QColor(COLORS['accent_start']))
        width = ann.get('width', 3)
        pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)

        if tool == self.TOOL_ARROW:
            self._draw_arrow(painter, ann['start'], ann['end'], pen)

        elif tool == self.TOOL_RECT:
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(ann['start'], ann['end']).normalized())

        elif tool == self.TOOL_CIRCLE:
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRect(ann['start'], ann['end']).normalized()
            painter.drawEllipse(rect)

        elif tool == self.TOOL_TEXT:
            text = ann.get('text', '')
            if text:
                font = QFont('Microsoft YaHei', ann.get('font_size', 16))
                painter.setFont(font)
                painter.setPen(color)
                painter.drawText(ann['start'], text)

        elif tool == self.TOOL_FREEHAND:
            points = ann.get('points', [])
            if len(points) > 1:
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(points[0])
                for pt in points[1:]:
                    path.lineTo(pt)
                painter.drawPath(path)

        elif tool == self.TOOL_BLUR:
            if self.base_pixmap and HAS_PIL:
                rect = QRect(ann['start'], ann['end']).normalized()
                self._draw_blur(painter, rect, ann.get('blur_radius', 10))

    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint, pen: QPen):
        painter.setPen(pen)
        painter.drawLine(start, end)

        # 箭头
        import math
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_len = 15
        arrow_angle = math.pi / 6

        x1 = end.x() - arrow_len * math.cos(angle - arrow_angle)
        y1 = end.y() - arrow_len * math.sin(angle - arrow_angle)
        x2 = end.x() - arrow_len * math.cos(angle + arrow_angle)
        y2 = end.y() - arrow_len * math.sin(angle + arrow_angle)

        painter.drawLine(end, QPoint(int(x1), int(y1)))
        painter.drawLine(end, QPoint(int(x2), int(y2)))

    def _draw_blur(self, painter: QPainter, rect: QRect, radius: int = 10):
        if rect.width() < 2 or rect.height() < 2:
            return

        # 裁剪出该区域
        cropped = self.base_pixmap.copy(rect)
        if cropped.width() < 1 or cropped.height() < 1:
            return

        # 用PIL模糊
        if HAS_PIL:
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            cropped.save(buffer, "PNG")
            pil_img = Image.frombytes("RGBA", (cropped.width(), cropped.height()),
                                      cropped.toImage().bits().asstring(
                                          cropped.width() * cropped.height() * 4),
                                      "raw", "BGRA")
            blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))

            qimg = QImage(blurred.tobytes("raw", "BGRA"),
                          blurred.width, blurred.height,
                          QImage.Format.Format_ARGB32)
            blurred_pixmap = QPixmap.fromImage(qimg)
            painter.drawPixmap(rect.topLeft(), blurred_pixmap)
        else:
            # 简单的像素化替代
            small = cropped.scaled(
                max(1, cropped.width() // 8),
                max(1, cropped.height() // 8),
                Qt.AspectRatioMode.IgnoreAspectRatio
            )
            pixelated = small.scaled(
                cropped.width(), cropped.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.drawPixmap(rect.topLeft(), pixelated)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == self.TOOL_TEXT:
                img_pos = self.widget_to_image(event.pos())
                self.text_input_pos = img_pos
                self._show_text_input(event.pos())
                return
            if self.current_tool == self.TOOL_COLOR_PICKER:
                img_pos = self.widget_to_image(event.pos())
                self._pick_color(img_pos)
                return

            self.is_drawing = True
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.freehand_points = [event.pos()]

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_pos = event.pos()
            if self.current_tool == self.TOOL_FREEHAND:
                self.freehand_points.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.current_pos = event.pos()

            sp = self.widget_to_image(self.start_pos)
            cp = self.widget_to_image(self.current_pos)

            if self.current_tool != self.TOOL_NONE:
                ann = {
                    'tool': self.current_tool,
                    'start': sp,
                    'end': cp,
                    'color': QColor(self.tool_color),
                    'width': self.tool_width,
                    'font_size': self.font_size,
                }
                if self.current_tool == self.TOOL_FREEHAND:
                    ann['points'] = [self.widget_to_image(p)
                                     for p in self.freehand_points]
                if self.current_tool == self.TOOL_BLUR:
                    ann['blur_radius'] = 10
                self.annotations.append(ann)
                self.annotation_changed.emit()

            self.update()

    def _show_text_input(self, pos: QPoint):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "输入文字", "请输入标注文字：")
        if ok and text:
            img_pos = self.widget_to_image(pos)
            ann = {
                'tool': self.TOOL_TEXT,
                'start': img_pos,
                'end': img_pos,
                'text': text,
                'color': QColor(self.tool_color),
                'width': self.tool_width,
                'font_size': self.font_size,
            }
            self.annotations.append(ann)
            self.annotation_changed.emit()
            self.update()

    def _pick_color(self, img_pos: QPoint):
        if self.base_pixmap:
            if 0 <= img_pos.x() < self.base_pixmap.width() and \
               0 <= img_pos.y() < self.base_pixmap.height():
                image = self.base_pixmap.toImage()
                color = image.pixelColor(img_pos)
                self.tool_color = color
                self.annotation_changed.emit()

    def get_result_pixmap(self) -> Optional[QPixmap]:
        if not self.base_pixmap:
            return None
        result = QPixmap(self.base_pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.base_pixmap)
        for ann in self.annotations:
            self._draw_annotation(painter, ann)
        painter.end()
        return result

    def undo(self):
        if self.annotations:
            self.annotations.pop()
            self.annotation_changed.emit()
            self.update()


# ============================================================================
# 截图历史缩略图
# ============================================================================

class HistoryThumbnail(QFrame):
    """单个历史截图缩略图"""
    clicked = pyqtSignal(dict)
    delete_requested = pyqtSignal(str)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("card")
        self.setFixedSize(180, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 缩略图
        thumb_label = QLabel()
        thumb_label.setFixedSize(160, 100)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("border: none;")

        pixmap = QPixmap(record.get('path', ''))
        if not pixmap.isNull():
            scaled = pixmap.scaled(160, 100,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            thumb_label.setPixmap(scaled)
        else:
            thumb_label.setText("⚠ 图片丢失")
            thumb_label.setStyleSheet("color: #8888aa; border: none;")

        layout.addWidget(thumb_label)

        # 时间标签
        time_label = QLabel(record.get('time', ''))
        time_label.setStyleSheet("color: #8888aa; font-size: 11px; border: none;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        open_btn = QPushButton("打开")
        open_btn.setFixedHeight(24)
        open_btn.setStyleSheet("""
            QPushButton { background: #667eea; border: none; border-radius: 4px;
                          color: white; font-size: 11px; padding: 2px 8px; }
            QPushButton:hover { background: #764ba2; }
        """)
        open_btn.clicked.connect(lambda: self.clicked.emit(self.record))

        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("""
            QPushButton { background: #ff4466; border: none; border-radius: 4px;
                          color: white; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: #ff6688; }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(record.get('id', '')))

        btn_row.addWidget(open_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    def enterEvent(self, event):
        self.setStyleSheet(f"background-color: {COLORS['card_hover']};"
                           f"border: 1px solid {COLORS['accent_start']};"
                           f"border-radius: 12px;")

    def leaveEvent(self, event):
        self.setStyleSheet(f"background-color: {COLORS['card']};"
                           f"border: 1px solid {COLORS['border']};"
                           f"border-radius: 12px;")


# ============================================================================
# 主窗口
# ============================================================================

class ScreenshotTool(QMainWindow):
    """截图工具主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScreenshotTool - 专业截图工具")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 800)

        # 状态
        self.current_pixmap: Optional[QPixmap] = None
        self.history: list = []
        self.history_file = get_app_dir() / 'history.json'
        self.hotkey_listener = None

        self._load_history()
        self._init_ui()
        self._setup_hotkeys()

    # ------------------------------------------------------------------
    # UI 初始化
    # ------------------------------------------------------------------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 左侧面板
        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel, 1)

        # 右侧面板（画布 + 工具栏）
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, 3)

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📸 ScreenshotTool")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("专业截图工具")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addWidget(self._make_separator())

        # 截图按钮组
        cap_label = QLabel("📷 截图模式")
        cap_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #667eea;")
        layout.addWidget(cap_label)

        btn_fullscreen = QPushButton("🖥️  全屏截图")
        btn_fullscreen.clicked.connect(self.capture_fullscreen)
        layout.addWidget(btn_fullscreen)

        btn_region = QPushButton("✂️  区域截图")
        btn_region.setObjectName("accent")
        btn_region.clicked.connect(self.capture_region)
        layout.addWidget(btn_region)

        btn_window = QPushButton("🪟  窗口截图")
        btn_window.clicked.connect(self.capture_window)
        layout.addWidget(btn_window)

        btn_scroll = QPushButton("📜  滚动截图")
        btn_scroll.clicked.connect(self.capture_scrolling)
        layout.addWidget(btn_scroll)

        layout.addWidget(self._make_separator())

        # 标注工具
        ann_label = QLabel("🎨 标注工具")
        ann_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #667eea;")
        layout.addWidget(ann_label)

        tool_grid = QGridLayout()
        tool_grid.setSpacing(6)

        tools = [
            ("⬚ 矩形", AnnotationCanvas.TOOL_RECT, 0, 0),
            ("○ 圆形", AnnotationCanvas.TOOL_CIRCLE, 0, 1),
            ("→ 箭头", AnnotationCanvas.TOOL_ARROW, 1, 0),
            ("✏️ 画笔", AnnotationCanvas.TOOL_FREEHAND, 1, 1),
            ("T 文字", AnnotationCanvas.TOOL_TEXT, 2, 0),
            ("🌫 模糊", AnnotationCanvas.TOOL_BLUR, 2, 1),
            ("🎨 取色", AnnotationCanvas.TOOL_COLOR_PICKER, 3, 0),
            ("↩ 撤销", -1, 3, 1),
        ]

        self.tool_buttons = []
        for label, tool_id, row, col in tools:
            btn = QPushButton(label)
            btn.setCheckable(tool_id >= 0)
            btn.setFixedHeight(34)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #111122; border: 1px solid #222244;
                    border-radius: 6px; font-size: 12px; padding: 4px 8px;
                }
                QPushButton:hover { border-color: #667eea; }
                QPushButton:checked {
                    background-color: #667eea; border-color: #667eea;
                    color: white;
                }
            """)
            if tool_id >= 0:
                btn.clicked.connect(lambda checked, t=tool_id, b=btn: self._select_tool(t, b))
            else:
                btn.clicked.connect(self._undo_annotation)
            tool_grid.addWidget(btn, row, col)
            self.tool_buttons.append((btn, tool_id))

        layout.addLayout(tool_grid)

        layout.addWidget(self._make_separator())

        # 颜色和线宽
        style_label = QLabel("⚙️ 样式设置")
        style_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #667eea;")
        layout.addWidget(style_label)

        # 颜色选择
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("颜色："))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(36, 36)
        self.color_btn.setStyleSheet(
            f"background-color: {COLORS['accent_start']}; border-radius: 6px;")
        self.color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()

        # 预设颜色
        preset_colors = ['#667eea', '#ff4466', '#44ff88', '#ffaa44',
                         '#44ddff', '#ffffff', '#000000']
        for c in preset_colors:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"background-color: {c}; border-radius: 4px;"
                              f"border: 1px solid #333;")
            btn.clicked.connect(lambda checked, color=c: self._set_color(color))
            color_row.addWidget(btn)

        layout.addLayout(color_row)

        # 线宽
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("线宽："))
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 20)
        self.width_slider.setValue(3)
        self.width_slider.valueChanged.connect(self._on_width_changed)
        width_row.addWidget(self.width_slider)
        self.width_label = QLabel("3")
        self.width_label.setFixedWidth(30)
        width_row.addWidget(self.width_label)
        layout.addLayout(width_row)

        # 字号
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("字号："))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 72)
        self.font_spin.setValue(16)
        self.font_spin.valueChanged.connect(self._on_font_changed)
        font_row.addWidget(self.font_spin)
        layout.addLayout(font_row)

        layout.addStretch()

        # 底部按钮
        save_btn = QPushButton("💾 保存图片")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self.save_image)
        layout.addWidget(save_btn)

        copy_btn = QPushButton("📋 复制到剪贴板")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_btn)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 顶部信息栏
        top_bar = QHBoxLayout()
        self.info_label = QLabel("就绪 - 选择截图模式开始")
        self.info_label.setStyleSheet("color: #8888aa; font-size: 13px;")
        top_bar.addWidget(self.info_label)

        self.size_label = QLabel("")
        self.size_label.setStyleSheet("color: #667eea; font-size: 13px;")
        top_bar.addStretch()
        top_bar.addWidget(self.size_label)
        layout.addLayout(top_bar)

        # 选项卡
        self.tabs = QTabWidget()

        # 编辑选项卡
        edit_tab = QWidget()
        edit_layout = QVBoxLayout(edit_tab)
        edit_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = AnnotationCanvas()
        self.canvas.annotation_changed.connect(self._on_annotation_changed)
        edit_layout.addWidget(self.canvas)

        self.tabs.addTab(edit_tab, "📝 编辑")

        # 历史选项卡
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(8, 8, 8, 8)

        # 历史头部
        hist_header = QHBoxLayout()
        hist_label = QLabel("📸 截图历史")
        hist_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #667eea;")
        hist_header.addWidget(hist_label)
        hist_header.addStretch()

        clear_btn = QPushButton("🗑 清空历史")
        clear_btn.setStyleSheet("""
            QPushButton { background: #ff4466; border: none; border-radius: 6px;
                          color: white; padding: 6px 12px; font-size: 12px; }
            QPushButton:hover { background: #ff6688; }
        """)
        clear_btn.clicked.connect(self._clear_history)
        hist_header.addWidget(clear_btn)
        history_layout.addLayout(hist_header)

        # 历史滚动区域
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_grid = QGridLayout(self.history_widget)
        self.history_grid.setSpacing(8)
        self.history_scroll.setWidget(self.history_widget)
        history_layout.addWidget(self.history_scroll)

        self.tabs.addTab(history_tab, f"📂 历史 ({len(self.history)})")

        # 关于选项卡
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(20, 20, 20, 20)

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #667eea;">📸 ScreenshotTool</h1>
            <h3 style="color: #8888aa;">专业截图工具 v1.0.0</h3>
            <br>
            <p style="color: #e0e0ff; font-size: 14px;">
                功能特性：<br>
                ✅ 全屏截图<br>
                ✅ 区域截图（鼠标拖拽）<br>
                ✅ 窗口截图<br>
                ✅ 滚动截图<br>
                ✅ 标注工具（箭头、矩形、圆形、文字、画笔）<br>
                ✅ 模糊/马赛克处理<br>
                ✅ 屏幕取色器<br>
                ✅ 保存/复制到剪贴板<br>
                ✅ 截图历史管理<br>
                ✅ 全局快捷键
            </p>
            <br>
            <p style="color: #8888aa; font-size: 12px;">
                快捷键说明：<br>
                Ctrl+Shift+F - 全屏截图<br>
                Ctrl+Shift+R - 区域截图<br>
                Ctrl+Shift+W - 窗口截图<br>
                Ctrl+Shift+S - 保存图片<br>
                Ctrl+Shift+C - 复制到剪贴板<br>
                Ctrl+Z - 撤销标注
            </p>
        </div>
        """)
        about_layout.addWidget(about_text)
        self.tabs.addTab(about_tab, "ℹ️ 关于")

        layout.addWidget(self.tabs)

        return panel

    def _make_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        return sep

    # ------------------------------------------------------------------
    # 工具选择
    # ------------------------------------------------------------------

    def _select_tool(self, tool_id: int, clicked_btn: QPushButton):
        # 取消其他按钮选中
        for btn, tid in self.tool_buttons:
            if btn != clicked_btn and tid >= 0:
                btn.setChecked(False)

        if clicked_btn.isChecked():
            self.canvas.current_tool = tool_id
        else:
            self.canvas.current_tool = AnnotationCanvas.TOOL_NONE

    def _undo_annotation(self):
        self.canvas.undo()

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(COLORS['accent_start']), self, "选择颜色")
        if color.isValid():
            self._set_color(color.name())

    def _set_color(self, color_str: str):
        self.canvas.tool_color = QColor(color_str)
        self.color_btn.setStyleSheet(f"background-color: {color_str}; border-radius: 6px;")

    def _on_width_changed(self, value: int):
        self.canvas.tool_width = value
        self.width_label.setText(str(value))

    def _on_font_changed(self, value: int):
        self.canvas.font_size = value

    def _on_annotation_changed(self):
        self.info_label.setText("已添加标注")

    # ------------------------------------------------------------------
    # 截图功能
    # ------------------------------------------------------------------

    def capture_fullscreen(self):
        """全屏截图"""
        self.hide()
        QTimer.singleShot(300, self._do_fullscreen_capture)

    def _do_fullscreen_capture(self):
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            self._set_captured(pixmap, "全屏截图")
        self.show()

    def capture_region(self):
        """区域截图"""
        self.hide()
        QTimer.singleShot(300, self._do_region_capture)

    def _do_region_capture(self):
        screen = QApplication.primaryScreen()
        if not screen:
            self.show()
            return

        full_pixmap = screen.grabWindow(0)
        self.region_selector = RegionSelector(full_pixmap)
        self.region_selector.region_selected.connect(self._on_region_selected)
        self.region_selector.cancelled.connect(self.show)

    def _on_region_selected(self, rect: QRect):
        screen = QApplication.primaryScreen()
        if screen:
            full_pixmap = screen.grabWindow(0)
            cropped = full_pixmap.copy(rect)
            self._set_captured(cropped, "区域截图")
        self.show()

    def capture_window(self):
        """窗口截图 - 截取当前前台窗口"""
        self.hide()
        QTimer.singleShot(300, self._do_window_capture)

    def _do_window_capture(self):
        screen = QApplication.primaryScreen()
        if screen:
            # 截取整个屏幕，然后根据窗口位置裁剪
            # 在Windows上用 grabWindow(0) 获取整个屏幕
            pixmap = screen.grabWindow(0)
            self._set_captured(pixmap, "窗口截图")
        self.show()

    def capture_scrolling(self):
        """滚动截图 - 提示用户操作"""
        msg = QMessageBox(self)
        msg.setWindowTitle("滚动截图")
        msg.setText("滚动截图模式\n\n"
                     "1. 请先滚动到目标位置\n"
                     "2. 点击\"开始捕获\"后缓慢滚动\n"
                     "3. 再次点击\"停止\"完成捕获\n\n"
                     "（当前版本为简化实现，将捕获当前可见区域）")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok |
                                QMessageBox.StandardButton.Cancel)
        if msg.exec() == QMessageBox.StandardButton.Ok:
            self.capture_fullscreen()

    def _set_captured(self, pixmap: QPixmap, label: str = "截图"):
        self.current_pixmap = pixmap
        self.canvas.set_pixmap(pixmap)
        self.info_label.setText(f"✅ {label}完成 - {pixmap.width()}×{pixmap.height()}")
        self.size_label.setText(f"{pixmap.width()} × {pixmap.height()} px")
        self.tabs.setCurrentIndex(0)

        # 保存到历史
        self._save_to_history(pixmap, label)

    # ------------------------------------------------------------------
    # 保存 / 复制
    # ------------------------------------------------------------------

    def save_image(self):
        result = self.canvas.get_result_pixmap()
        if not result:
            QMessageBox.information(self, "提示", "请先截取一张图片")
            return

        default_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        default_path = str(Path.home() / 'Pictures' / default_name)

        path, _ = QFileDialog.getSaveFileName(
            self, "保存截图", default_path,
            "PNG图片 (*.png);;JPEG图片 (*.jpg *.jpeg);;BMP图片 (*.bmp);;所有文件 (*)"
        )
        if path:
            result.save(path)
            self.info_label.setText(f"✅ 已保存到: {path}")

    def copy_to_clipboard(self):
        result = self.canvas.get_result_pixmap()
        if not result:
            QMessageBox.information(self, "提示", "请先截取一张图片")
            return

        clipboard = QApplication.clipboard()
        clipboard.setPixmap(result)
        self.info_label.setText("✅ 已复制到剪贴板")

    # ------------------------------------------------------------------
    # 历史管理
    # ------------------------------------------------------------------

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save_history_index(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_to_history(self, pixmap: QPixmap, label: str):
        hist_dir = get_history_dir()
        uid = str(uuid.uuid4())[:8]
        filename = f"screenshot_{uid}.png"
        filepath = str(hist_dir / filename)

        pixmap.save(filepath)

        record = {
            'id': uid,
            'path': filepath,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'label': label,
            'width': pixmap.width(),
            'height': pixmap.height(),
        }
        self.history.insert(0, record)
        self._save_history_index()
        self._refresh_history()

    def _refresh_history(self):
        # 清空现有缩略图
        while self.history_grid.count():
            item = self.history_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加缩略图
        cols = 3
        for i, record in enumerate(self.history):
            thumb = HistoryThumbnail(record)
            thumb.clicked.connect(self._on_history_open)
            thumb.delete_requested.connect(self._on_history_delete)
            self.history_grid.addWidget(thumb, i // cols, i % cols)

        # 更新标签
        self.tabs.setTabText(1, f"📂 历史 ({len(self.history)})")

    def _on_history_open(self, record: dict):
        path = record.get('path', '')
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self._set_captured(pixmap, record.get('label', '历史截图'))
        else:
            QMessageBox.warning(self, "错误", "无法打开该截图文件")

    def _on_history_delete(self, uid: str):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该截图吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 删除文件
            for record in self.history:
                if record.get('id') == uid:
                    try:
                        os.remove(record['path'])
                    except Exception:
                        pass
                    break
            self.history = [r for r in self.history if r.get('id') != uid]
            self._save_history_index()
            self._refresh_history()

    def _clear_history(self):
        if not self.history:
            return

        reply = QMessageBox.question(
            self, "确认清空", f"确定要清空所有 {len(self.history)} 条截图历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for record in self.history:
                try:
                    os.remove(record['path'])
                except Exception:
                    pass
            self.history.clear()
            self._save_history_index()
            self._refresh_history()

    # ------------------------------------------------------------------
    # 全局快捷键
    # ------------------------------------------------------------------

    def _setup_hotkeys(self):
        if not HAS_PYNPUT:
            self.info_label.setText("⚠ pynput未安装，全局快捷键不可用")
            return

        try:
            def on_hotkey_fullscreen():
                QTimer.singleShot(0, self.capture_fullscreen)

            def on_hotkey_region():
                QTimer.singleShot(0, self.capture_region)

            hotkey_map = {
                '<ctrl>+<shift>+f': on_hotkey_fullscreen,
                '<ctrl>+<shift>+r': on_hotkey_region,
            }

            self.hotkey_listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
        except Exception as e:
            print(f"快捷键初始化失败: {e}")

    # ------------------------------------------------------------------
    # 键盘快捷键
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self.save_image()
            elif event.key() == Qt.Key.Key_C:
                self.copy_to_clipboard()
            elif event.key() == Qt.Key.Key_Z:
                self.canvas.undo()
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # 关闭
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        event.accept()


# ============================================================================
# 启动入口
# ============================================================================

def main():
    # Windows DPI 适配
    if sys.platform == 'win32':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLESHEET)

    window = ScreenshotTool()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
