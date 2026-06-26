"""
ColorPicker - 专业色彩拾取与调色板工具
基于 PyQt6 的桌面色彩工具
"""

import sys
import json
import math
import struct
import colorsys
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QSpinBox, QSlider,
    QComboBox, QTextEdit, QGroupBox, QGridLayout, QFrame, QColorDialog,
    QSizePolicy, QScrollArea, QFileDialog, QMessageBox, QSplitter,
    QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import (
    Qt, QPoint, QRect, QSize, QTimer, pyqtSignal, QThread, QPointF
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPixmap, QImage,
    QLinearGradient, QRadialGradient, QConicalGradient, QCursor,
    QPainterPath, QFontMetrics, QClipboard, QPalette
)


# ── 颜色工具函数 ────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    r1, g1, b1 = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
    return h * 360, s * 100, l * 100


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    r1, g1, b1 = r / 255, g / 255, b / 255
    h, s, v = colorsys.rgb_to_hsv(r1, g1, b1)
    return h * 360, s * 100, v * 100


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)
    return int(r * 255), int(g * 255), int(b * 255)


def relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    l1 = relative_luminance(*c1)
    l2 = relative_luminance(*c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_rating(ratio: float) -> Tuple[str, str]:
    if ratio >= 7:
        return "AAA", "优秀 ✓"
    elif ratio >= 4.5:
        return "AA", "良好 ✓"
    elif ratio >= 3:
        return "AA (大字)", "一般"
    else:
        return "不通过", "不达标 ✗"


def generate_palette(r: int, g: int, b: int, palette_type: str) -> List[Tuple[int, int, int]]:
    h, s, v = rgb_to_hsv(r, g, b)
    colors = [(r, g, b)]
    if palette_type == "互补色":
        colors.append(hsv_to_rgb((h + 180) % 360, s, v))
    elif palette_type == "类似色":
        colors.append(hsv_to_rgb((h + 30) % 360, s, v))
        colors.append(hsv_to_rgb((h - 30) % 360, s, v))
    elif palette_type == "三角色":
        colors.append(hsv_to_rgb((h + 120) % 360, s, v))
        colors.append(hsv_to_rgb((h + 240) % 360, s, v))
    elif palette_type == "分裂互补":
        colors.append(hsv_to_rgb((h + 150) % 360, s, v))
        colors.append(hsv_to_rgb((h + 210) % 360, s, v))
    elif palette_type == "四角色":
        colors.append(hsv_to_rgb((h + 90) % 360, s, v))
        colors.append(hsv_to_rgb((h + 180) % 360, s, v))
        colors.append(hsv_to_rgb((h + 270) % 360, s, v))
    return colors


# ── 样式 ────────────────────────────────────────────────────────────────────

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
    border-radius: 8px;
    background-color: #111122;
}
QTabBar::tab {
    background-color: #111122;
    color: #888;
    padding: 10px 20px;
    margin: 2px 1px;
    border-radius: 6px 6px 0 0;
    min-width: 100px;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border-bottom: 2px solid #667eea;
}
QTabBar::tab:hover:!selected {
    background-color: #1a1a2e;
    color: #ccc;
}
QGroupBox {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #667eea;
}
QPushButton {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #2a2a4e;
    border: 1px solid #667eea;
}
QPushButton:pressed {
    background-color: #667eea;
}
QPushButton#accent {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#accent:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8efc, stop:1 #8b5fcf);
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0d0d1a;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #667eea;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #888;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #111122;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    selection-background-color: #667eea;
}
QSlider::groove:horizontal {
    background: #2a2a3a;
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
QTextEdit {
    background-color: #0d0d1a;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #667eea;
}
QLabel#subtitle {
    font-size: 11px;
    color: #666;
}
"""


# ── 色轮控件 ────────────────────────────────────────────────────────────────

class ColorWheel(QWidget):
    colorChanged = pyqtSignal(int, int, int)

    def __init__(self, size=220):
        super().__init__()
        self.setFixedSize(size, size)
        self._hue = 0
        self._sat = 100
        self._val = 100
        self._wheel_pixmap: Optional[QPixmap] = None
        self._dragging = False

    def set_hsv(self, h: float, s: float, v: float):
        self._hue = h
        self._sat = s
        self._val = v
        self.update()

    def _build_wheel(self):
        if self._wheel_pixmap and self._wheel_pixmap.size() == self.size():
            return
        w = self.width()
        h = self.height()
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2
        for y in range(h):
            for x in range(w):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    angle = math.atan2(dy, dx)
                    hue = (math.degrees(angle) + 360) % 360
                    sat = dist / radius * 100
                    r, g, b = hsv_to_rgb(hue, sat, 100)
                    img.setPixelColor(x, y, QColor(r, g, b))
                else:
                    img.setPixelColor(x, y, QColor(0, 0, 0, 0))
        self._wheel_pixmap = QPixmap.fromImage(img)

    def paintEvent(self, event):
        self._build_wheel()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawPixmap(0, 0, self._wheel_pixmap)
        # indicator
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) / 2
        angle_rad = math.radians(self._hue)
        sat_dist = self._sat / 100 * radius
        ix = cx + sat_dist * math.cos(angle_rad)
        iy = cy + sat_dist * math.sin(angle_rad)
        r, g, b = hsv_to_rgb(self._hue, self._sat, self._val)
        # outer ring
        p.setPen(QPen(QColor(255, 255, 255), 3))
        p.setBrush(QColor(r, g, b))
        p.drawEllipse(QPointF(ix, iy), 8, 8)
        # inner dot
        p.setPen(QPen(QColor(0, 0, 0, 100), 1))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(QPointF(ix, iy), 3, 3)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_color(event.position())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_color(event.position())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _update_color(self, pos: QPointF):
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) / 2
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > radius:
            dist = radius
        angle = math.atan2(dy, dx)
        self._hue = (math.degrees(angle) + 360) % 360
        self._sat = dist / radius * 100
        self.update()
        r, g, b = hsv_to_rgb(self._hue, self._sat, self._val)
        self.colorChanged.emit(r, g, b)


# ── 颜色预览方块 ────────────────────────────────────────────────────────────

class ColorPreview(QFrame):
    def __init__(self, size=60):
        super().__init__()
        self.setFixedSize(size, size)
        self._color = QColor(102, 126, 234)
        self.setStyleSheet("border: none;")

    def set_color(self, r: int, g: int, b: int):
        self._color = QColor(r, g, b)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # checkerboard
        s = 8
        for y in range(0, self.height(), s):
            for x in range(0, self.width(), s):
                c = QColor(60, 60, 60) if (x // s + y // s) % 2 == 0 else QColor(40, 40, 40)
                p.fillRect(x, y, s, s, c)
        # color
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        p.setClipPath(path)
        p.fillRect(self.rect(), self._color)
        p.end()


# ── 屏幕取色器 ──────────────────────────────────────────────────────────────

class ScreenPicker(QWidget):
    colorPicked = pyqtSignal(int, int, int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._magnifier_size = 150
        self._zoom = 8
        self._pos = QPoint(0, 0)
        self._color = QColor(0, 0, 0)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._active = False

    def start(self):
        self._active = True
        self.showFullScreen()
        self.setMouseTracking(True)
        self.grabMouse()
        self.grabKeyboard()
        self._timer.start(16)

    def stop(self):
        self._active = False
        self._timer.stop()
        self.releaseMouse()
        self.releaseKeyboard()
        self.hide()

    def _tick(self):
        self._pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        if screen:
            px = screen.grabWindow(0, self._pos.x() - 5, self._pos.y() - 5, 11, 11)
            if not px.isNull():
                img = px.toImage()
                c = img.pixelColor(5, 5)
                self._color = c
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.stop()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            r, g, b = self._color.red(), self._color.green(), self._color.blue()
            self.colorPicked.emit(r, g, b)
            self.stop()
        elif event.button() == Qt.MouseButton.RightButton:
            self.stop()

    def paintEvent(self, event):
        if not self._active:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # dim overlay
        p.fillRect(self.rect(), QColor(0, 0, 0, 40))
        # magnifier
        ms = self._magnifier_size
        mx = self._pos.x() + 20
        my = self._pos.y() - ms - 20
        # keep on screen
        sr = self.screen().geometry() if self.screen() else QRect(0, 0, 1920, 1080)
        if mx + ms > sr.width():
            mx = self._pos.x() - ms - 20
        if my < 0:
            my = self._pos.y() + 20
        # magnifier background
        p.setPen(QPen(QColor(102, 126, 234), 2))
        p.setBrush(QColor(17, 17, 34, 220))
        p.drawRoundedRect(mx, my, ms, ms, 10, 10)
        # zoomed pixels
        screen = QApplication.primaryScreen()
        if screen:
            half = self._zoom // 2
            px = screen.grabWindow(0, self._pos.x() - half, self._pos.y() - half,
                                   self._zoom + 1, self._zoom + 1)
            if not px.isNull():
                cell = ms / (self._zoom + 1)
                img = px.toImage()
                for gy in range(self._zoom + 1):
                    for gx in range(self._zoom + 1):
                        c = img.pixelColor(gx, gy)
                        p.fillRect(int(mx + 5 + gx * cell), int(my + 5 + gy * cell),
                                   int(cell) + 1, int(cell) + 1, c)
                # center highlight
                cx = mx + 5 + half * cell
                cy = my + 5 + half * cell
                p.setPen(QPen(QColor(255, 255, 255), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(int(cx), int(cy), int(cell), int(cell))
        # color swatch
        sy = my + ms + 8
        p.setPen(QPen(QColor(102, 126, 234), 1))
        p.setBrush(self._color)
        p.drawRoundedRect(mx, sy, 60, 24, 4, 4)
        # text
        p.setPen(QColor(255, 255, 255))
        f = QFont("Consolas", 10)
        p.setFont(f)
        hex_str = self._color.name().upper()
        p.drawText(mx + 66, sy + 16, hex_str)
        # instructions
        p.setPen(QColor(200, 200, 200))
        p.setFont(QFont("Microsoft YaHei", 10))
        p.drawText(mx, sy + 40, "左键拾取 | 右键/Esc 取消")
        p.end()


# ── 主窗口 ──────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 ColorPicker - 专业色彩工具")
        self.setMinimumSize(1080, 720)
        self.resize(1200, 800)
        self._r, self._g, self._b = 102, 126, 234
        self._color_history: List[Tuple[int, int, int]] = []
        self._picker: Optional[ScreenPicker] = None
        self._build_ui()
        self._update_all()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # header
        header = QHBoxLayout()
        title = QLabel("🎨 ColorPicker")
        title.setObjectName("title")
        subtitle = QLabel("专业色彩拾取与调色板工具")
        subtitle.setObjectName("subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        pick_btn = QPushButton("🖱️ 屏幕取色")
        pick_btn.setObjectName("accent")
        pick_btn.setFixedWidth(140)
        pick_btn.clicked.connect(self._start_picker)
        header.addWidget(pick_btn)
        main_layout.addLayout(header)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_wheel_tab(), "🎡 色轮")
        self.tabs.addTab(self._build_format_tab(), "📐 色彩格式")
        self.tabs.addTab(self._build_palette_tab(), "🎨 调色板")
        self.tabs.addTab(self._build_history_tab(), "📜 历史记录")
        self.tabs.addTab(self._build_contrast_tab(), "♿ 对比度")
        self.tabs.addTab(self._build_gradient_tab(), "🌈 渐变")
        self.tabs.addTab(self._build_export_tab(), "📤 导出")
        main_layout.addWidget(self.tabs, 1)

    # ── 色轮页 ──────────────────────────────────────────────────────────

    def _build_wheel_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setSpacing(16)

        # left: wheel + preview
        left = QVBoxLayout()
        self.color_wheel = ColorWheel(240)
        self.color_wheel.colorChanged.connect(self._on_wheel_color)
        left.addWidget(self.color_wheel, alignment=Qt.AlignmentFlag.AlignCenter)

        self.wheel_preview = ColorPreview(80)
        left.addWidget(self.wheel_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        hex_label = QLabel("#667EEA")
        hex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hex_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        hex_label.setStyleSheet("color: #667eea;")
        self.wheel_hex_label = hex_label
        left.addWidget(hex_label)
        left.addStretch()
        layout.addLayout(left)

        # right: sliders
        right = QVBoxLayout()
        right.setSpacing(14)

        # HSV sliders
        for label, name, max_val in [("色相 (H)", "hue", 360), ("饱和度 (S)", "sat", 100), ("明度 (V)", "val", 100)]:
            g = QGroupBox(label)
            gl = QVBoxLayout(g)
            h_layout = QHBoxLayout()
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, max_val)
            slider.setValue(0 if name == "hue" else 100)
            spin = QSpinBox()
            spin.setRange(0, max_val)
            spin.setValue(slider.value())
            spin.setFixedWidth(65)
            slider.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(slider.setValue)
            slider.valueChanged.connect(lambda v, n=name: self._on_slider(n, v))
            h_layout.addWidget(slider)
            h_layout.addWidget(spin)
            gl.addLayout(h_layout)
            right.addWidget(g)
            setattr(self, f"_slider_{name}", slider)
            setattr(self, f"_spin_{name}", spin)

        # color input
        g = QGroupBox("手动输入")
        gl = QVBoxLayout(g)
        input_layout = QHBoxLayout()
        self.hex_input = QLineEdit("#667eea")
        self.hex_input.setPlaceholderText("输入 HEX 颜色值...")
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_hex)
        input_layout.addWidget(self.hex_input)
        input_layout.addWidget(apply_btn)
        gl.addLayout(input_layout)

        # RGB inputs
        rgb_layout = QHBoxLayout()
        self.r_input = QSpinBox()
        self.r_input.setRange(0, 255)
        self.r_input.setPrefix("R: ")
        self.g_input = QSpinBox()
        self.g_input.setRange(0, 255)
        self.g_input.setPrefix("G: ")
        self.b_input = QSpinBox()
        self.b_input.setRange(0, 255)
        self.b_input.setPrefix("B: ")
        for sp in [self.r_input, self.g_input, self.b_input]:
            rgb_layout.addWidget(sp)
        rgb_apply = QPushButton("设置RGB")
        rgb_apply.clicked.connect(self._apply_rgb)
        rgb_layout.addWidget(rgb_apply)
        gl.addLayout(rgb_layout)
        right.addWidget(g)

        # add to history button
        hist_btn = QPushButton("📌 添加到历史记录")
        hist_btn.setObjectName("accent")
        hist_btn.clicked.connect(self._add_to_history)
        right.addWidget(hist_btn)

        right.addStretch()
        layout.addLayout(right, 1)
        return w

    # ── 格式页 ──────────────────────────────────────────────────────────

    def _build_format_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # preview row
        preview_row = QHBoxLayout()
        self.format_preview = ColorPreview(70)
        preview_row.addWidget(self.format_preview)
        pf = QLabel()
        pf.setObjectName("title")
        self.format_color_name = pf
        preview_row.addWidget(pf)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        # format cards
        grid = QGridLayout()
        grid.setSpacing(10)
        formats = [
            ("HEX", "hex"), ("RGB", "rgb"), ("HSL", "hsl"), ("HSV", "hsv"),
            ("CSS RGB", "css_rgb"), ("CSS HSL", "css_hsl"), ("整数", "int_val"), ("CMYK (近似)", "cmyk")
        ]
        for i, (label, attr) in enumerate(formats):
            g = QGroupBox(label)
            gl = QHBoxLayout(g)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setFont(QFont("Consolas", 11))
            copy_btn = QPushButton("复制")
            copy_btn.setFixedWidth(55)
            copy_btn.clicked.connect(lambda _, w=le: self._copy_text(w.text()))
            gl.addWidget(le, 1)
            gl.addWidget(copy_btn)
            grid.addWidget(g, i // 2, i % 2)
            setattr(self, f"fmt_{attr}", le)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    # ── 调色板页 ────────────────────────────────────────────────────────

    def _build_palette_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("调色板类型:"))
        self.palette_type = QComboBox()
        self.palette_type.addItems(["互补色", "类似色", "三角色", "分裂互补", "四角色"])
        self.palette_type.currentIndexChanged.connect(self._generate_palette)
        ctrl.addWidget(self.palette_type)
        gen_btn = QPushButton("🔄 生成调色板")
        gen_btn.setObjectName("accent")
        gen_btn.clicked.connect(self._generate_palette)
        ctrl.addWidget(gen_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # palette display
        self.palette_container = QWidget()
        self.palette_layout = QHBoxLayout(self.palette_container)
        self.palette_layout.setSpacing(8)
        layout.addWidget(self.palette_container)

        # palette colors list
        self.palette_scroll = QScrollArea()
        self.palette_scroll.setWidgetResizable(True)
        self.palette_scroll.setFixedHeight(200)
        self.palette_colors_widget = QWidget()
        self.palette_colors_layout = QVBoxLayout(self.palette_colors_widget)
        self.palette_scroll.setWidget(self.palette_colors_widget)
        layout.addWidget(self.palette_scroll)

        layout.addStretch()
        return w

    # ── 历史页 ──────────────────────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("已保存颜色: "))
        self.history_count = QLabel("0")
        self.history_count.setStyleSheet("color: #667eea; font-weight: bold;")
        ctrl.addWidget(self.history_count)
        ctrl.addStretch()
        clear_btn = QPushButton("🗑️ 清空历史")
        clear_btn.clicked.connect(self._clear_history)
        ctrl.addWidget(clear_btn)
        layout.addLayout(ctrl)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_grid = QGridLayout(self.history_widget)
        self.history_grid.setSpacing(8)
        self.history_scroll.setWidget(self.history_widget)
        layout.addWidget(self.history_scroll, 1)

        return w

    # ── 对比度页 ────────────────────────────────────────────────────────

    def _build_contrast_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setSpacing(16)

        # left: controls
        left = QVBoxLayout()
        left.setSpacing(12)

        # foreground
        g1 = QGroupBox("前景色 (文字)")
        gl1 = QVBoxLayout(g1)
        self.fg_picker = ColorPreview(50)
        fg_row = QHBoxLayout()
        fg_row.addWidget(self.fg_picker)
        self.fg_input = QLineEdit("#FFFFFF")
        self.fg_input.setFont(QFont("Consolas", 11))
        fg_apply = QPushButton("使用当前颜色")
        fg_apply.clicked.connect(lambda: self._set_contrast_color("fg"))
        fg_row.addWidget(self.fg_input)
        fg_row.addWidget(fg_apply)
        gl1.addLayout(fg_row)
        left.addWidget(g1)

        # background
        g2 = QGroupBox("背景色")
        gl2 = QVBoxLayout(g2)
        self.bg_picker = ColorPreview(50)
        bg_row = QHBoxLayout()
        bg_row.addWidget(self.bg_picker)
        self.bg_input = QLineEdit("#000000")
        self.bg_input.setFont(QFont("Consolas", 11))
        bg_apply = QPushButton("使用当前颜色")
        bg_apply.clicked.connect(lambda: self._set_contrast_color("bg"))
        bg_row.addWidget(self.bg_input)
        bg_row.addWidget(bg_apply)
        gl2.addLayout(bg_row)
        left.addWidget(g2)

        # calculate
        calc_btn = QPushButton("📊 计算对比度")
        calc_btn.setObjectName("accent")
        calc_btn.clicked.connect(self._calc_contrast)
        left.addWidget(calc_btn)

        # result
        g3 = QGroupBox("检测结果")
        gl3 = QVBoxLayout(g3)
        self.contrast_ratio_label = QLabel("对比度: -")
        self.contrast_ratio_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self.contrast_ratio_label.setStyleSheet("color: #667eea;")
        gl3.addWidget(self.contrast_ratio_label)
        self.wcag_aa = QLabel("AA 等级: -")
        self.wcag_aa.setFont(QFont("Microsoft YaHei", 12))
        gl3.addWidget(self.wcag_aa)
        self.wcag_aaa = QLabel("AAA 等级: -")
        self.wcag_aaa.setFont(QFont("Microsoft YaHei", 12))
        gl3.addWidget(self.wcag_aaa)
        left.addWidget(g3)
        left.addStretch()
        layout.addLayout(left)

        # right: preview
        right = QVBoxLayout()
        g4 = QGroupBox("预览效果")
        gl4 = QVBoxLayout(g4)
        self.contrast_preview = QLabel("Aa 文字预览\nColorPicker 色彩工具\nThe quick brown fox jumps over the lazy dog.\n1234567890 !@#$%^&*()")
        self.contrast_preview.setFont(QFont("Microsoft YaHei", 14))
        self.contrast_preview.setWordWrap(True)
        self.contrast_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contrast_preview.setMinimumHeight(200)
        self.contrast_preview.setStyleSheet("background-color: #000000; color: #FFFFFF; padding: 20px; border-radius: 10px;")
        gl4.addWidget(self.contrast_preview)
        right.addWidget(g4)
        right.addStretch()
        layout.addLayout(right, 1)

        return w

    # ── 渐变页 ──────────────────────────────────────────────────────────

    def _build_gradient_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("渐变类型:"))
        self.grad_type = QComboBox()
        self.grad_type.addItems(["线性渐变", "径向渐变", "锥形渐变"])
        self.grad_type.currentIndexChanged.connect(self._update_gradient)
        ctrl.addWidget(self.grad_type)

        ctrl.addWidget(QLabel("角度:"))
        self.grad_angle = QSpinBox()
        self.grad_angle.setRange(0, 360)
        self.grad_angle.setValue(90)
        self.grad_angle.setSuffix("°")
        self.grad_angle.valueChanged.connect(self._update_gradient)
        ctrl.addWidget(self.grad_angle)

        add_stop_btn = QPushButton("+ 添加色标")
        add_stop_btn.clicked.connect(self._add_gradient_stop)
        ctrl.addWidget(add_stop_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # gradient stops
        self.gradient_stops: List[Tuple[float, QColor]] = [
            (0.0, QColor(102, 126, 234)),
            (1.0, QColor(118, 75, 162))
        ]
        self.grad_stops_widget = QWidget()
        self.grad_stops_layout = QHBoxLayout(self.grad_stops_widget)
        layout.addWidget(self.grad_stops_widget)
        self._rebuild_gradient_stops()

        # preview
        g = QGroupBox("渐变预览")
        gl = QVBoxLayout(g)
        self.gradient_preview = QLabel()
        self.gradient_preview.setFixedHeight(120)
        self.gradient_preview.setStyleSheet("border-radius: 10px;")
        gl.addWidget(self.gradient_preview)
        layout.addWidget(g)

        # CSS output
        g2 = QGroupBox("CSS 代码")
        gl2 = QVBoxLayout(g2)
        self.gradient_css = QTextEdit()
        self.gradient_css.setFixedHeight(80)
        self.gradient_css.setReadOnly(True)
        gl2.addWidget(self.gradient_css)
        copy_grad = QPushButton("📋 复制 CSS")
        copy_grad.clicked.connect(lambda: self._copy_text(self.gradient_css.toPlainText()))
        gl2.addWidget(copy_grad)
        layout.addWidget(g2)

        layout.addStretch()
        return w

    # ── 导出页 ──────────────────────────────────────────────────────────

    def _build_export_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # format selection
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("导出格式:"))
        self.export_format = QComboBox()
        self.export_format.addItems(["CSS", "SCSS", "JSON", "ASE (Adobe)"])
        self.export_format.currentIndexChanged.connect(self._update_export_preview)
        ctrl.addWidget(self.export_format)
        export_btn = QPushButton("💾 导出文件")
        export_btn.setObjectName("accent")
        export_btn.clicked.connect(self._export_file)
        ctrl.addWidget(export_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # preview
        g = QGroupBox("导出预览")
        gl = QVBoxLayout(g)
        self.export_preview = QTextEdit()
        self.export_preview.setReadOnly(True)
        self.export_preview.setFont(QFont("Cascadia Code", 11))
        gl.addWidget(self.export_preview)
        copy_export = QPushButton("📋 复制代码")
        copy_export.clicked.connect(lambda: self._copy_text(self.export_preview.toPlainText()))
        gl.addWidget(copy_export)
        layout.addWidget(g)

        return w

    # ── 信号处理 ────────────────────────────────────────────────────────

    def _on_wheel_color(self, r: int, g: int, b: int):
        self._set_color(r, g, b)

    def _on_slider(self, name: str, value: int):
        h = self._slider_hue.value()
        s = self._slider_sat.value()
        v = self._slider_val.value()
        r, g, b = hsv_to_rgb(h, s, v)
        self._set_color(r, g, b, update_sliders=False)

    def _set_color(self, r: int, g: int, b: int, update_sliders=True):
        self._r, self._g, self._b = r, g, b
        if update_sliders:
            h, s, v = rgb_to_hsv(r, g, b)
            self._slider_hue.blockSignals(True)
            self._slider_sat.blockSignals(True)
            self._slider_val.blockSignals(True)
            self._slider_hue.setValue(int(h))
            self._slider_sat.setValue(int(s))
            self._slider_val.setValue(int(v))
            self._slider_hue.blockSignals(False)
            self._slider_sat.blockSignals(False)
            self._slider_val.blockSignals(False)
        self._update_all()

    def _update_all(self):
        r, g, b = self._r, self._g, self._b
        hex_str = rgb_to_hex(r, g, b)
        # wheel tab
        self.wheel_preview.set_color(r, g, b)
        self.wheel_hex_label.setText(hex_str.upper())
        self.r_input.blockSignals(True)
        self.g_input.blockSignals(True)
        self.b_input.blockSignals(True)
        self.r_input.setValue(r)
        self.g_input.setValue(g)
        self.b_input.setValue(b)
        self.r_input.blockSignals(False)
        self.g_input.blockSignals(False)
        self.b_input.blockSignals(False)
        # format tab
        self.format_preview.set_color(r, g, b)
        self.format_color_name.setText(f"  {hex_str.upper()}")
        h, s, l = rgb_to_hsl(r, g, b)
        hv, sv, vv = rgb_to_hsv(r, g, b)
        self.fmt_hex.setText(hex_str.upper())
        self.fmt_rgb.setText(f"rgb({r}, {g}, {b})")
        self.fmt_hsl.setText(f"hsl({h:.1f}°, {s:.1f}%, {l:.1f}%)")
        self.fmt_hsv.setText(f"hsv({hv:.1f}°, {sv:.1f}%, {vv:.1f}%)")
        self.fmt_css_rgb.setText(f"rgb({r}, {g}, {b})")
        self.fmt_css_hsl.setText(f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)")
        self.fmt_int_val.setText(str((r << 16) + (g << 8) + b))
        # CMYK
        if r == 0 and g == 0 and b == 0:
            c, m, y, k = 0, 0, 0, 100
        else:
            c = 1 - r / 255
            m = 1 - g / 255
            y = 1 - b / 255
            k = min(c, m, y)
            c = int((c - k) / (1 - k) * 100)
            m = int((m - k) / (1 - k) * 100)
            y = int((y - k) / (1 - k) * 100)
            k = int(k * 100)
        self.fmt_cmyk.setText(f"cmyk({c}%, {m}%, {y}%, {k}%)")
        # update wheel
        self.color_wheel.set_hsv(hv, sv, vv)
        # gradient
        self._update_gradient()
        self._update_export_preview()

    def _start_picker(self):
        if self._picker is None:
            self._picker = ScreenPicker()
            self._picker.colorPicked.connect(self._on_picked)
        self._picker.start()

    def _on_picked(self, r: int, g: int, b: int):
        self._set_color(r, g, b)
        self._add_to_history()

    def _apply_hex(self):
        text = self.hex_input.text().strip()
        if not text.startswith('#'):
            text = '#' + text
        if len(text) == 7:
            try:
                r, g, b = hex_to_rgb(text)
                self._set_color(r, g, b)
            except ValueError:
                pass

    def _apply_rgb(self):
        r = self.r_input.value()
        g = self.g_input.value()
        b = self.b_input.value()
        self._set_color(r, g, b)

    def _copy_text(self, text: str):
        if text:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)

    def _add_to_history(self):
        color = (self._r, self._g, self._b)
        if color not in self._color_history:
            self._color_history.insert(0, color)
            if len(self._color_history) > 50:
                self._color_history.pop()
            self._rebuild_history()

    def _clear_history(self):
        self._color_history.clear()
        self._rebuild_history()

    def _rebuild_history(self):
        self.history_count.setText(str(len(self._color_history)))
        # clear grid
        while self.history_grid.count():
            item = self.history_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cols = 8
        for i, (r, g, b) in enumerate(self._color_history):
            btn = QPushButton()
            btn.setFixedSize(60, 60)
            hex_str = rgb_to_hex(r, g, b).upper()
            btn.setToolTip(hex_str)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_str}; border: 1px solid #2a2a3a; border-radius: 6px; }}"
                f"QPushButton:hover {{ border: 2px solid #667eea; }}"
            )
            btn.clicked.connect(lambda _, rr=r, gg=g, bb=b: self._set_color(rr, gg, bb))
            self.history_grid.addWidget(btn, i // cols, i % cols)

    def _generate_palette(self):
        palette_type = self.palette_type.currentText()
        colors = generate_palette(self._r, self._g, self._b, palette_type)
        # clear
        while self.palette_layout.count():
            item = self.palette_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.palette_colors_layout.count():
            item = self.palette_colors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for r, g, b in colors:
            hex_str = rgb_to_hex(r, g, b)
            # swatch
            frame = QFrame()
            frame.setFixedSize(100, 100)
            frame.setStyleSheet(
                f"background-color: {hex_str}; border: 1px solid #2a2a3a; border-radius: 10px;"
            )
            self.palette_layout.addWidget(frame)
            # label
            label = QLabel(f"{hex_str.upper()}  |  rgb({r},{g},{b})")
            label.setFont(QFont("Consolas", 10))
            label.setStyleSheet(f"color: {hex_str}; padding: 4px;")
            self.palette_colors_layout.addWidget(label)

    def _set_contrast_color(self, which: str):
        hex_str = rgb_to_hex(self._r, self._g, self._b)
        if which == "fg":
            self.fg_input.setText(hex_str)
            self.fg_picker.set_color(self._r, self._g, self._b)
        else:
            self.bg_input.setText(hex_str)
            self.bg_picker.set_color(self._r, self._g, self._b)

    def _calc_contrast(self):
        try:
            fg = hex_to_rgb(self.fg_input.text().strip())
            bg = hex_to_rgb(self.bg_input.text().strip())
        except (ValueError, AttributeError):
            return
        ratio = contrast_ratio(fg, bg)
        aa, aa_text = wcag_rating(ratio)
        self.contrast_ratio_label.setText(f"对比度: {ratio:.2f}:1")
        self.wcag_aa.setText(f"AA 等级: {aa_text}")
        aaa_ratio = 7.0
        self.wcag_aaa.setText(f"AAA 等级: {'通过 ✓' if ratio >= aaa_ratio else '不通过 ✗'}")
        fg_hex = self.fg_input.text().strip()
        bg_hex = self.bg_input.text().strip()
        self.contrast_preview.setStyleSheet(
            f"background-color: {bg_hex}; color: {fg_hex}; padding: 20px; border-radius: 10px;"
        )

    def _add_gradient_stop(self):
        pos = 0.5
        color = QColor(self._r, self._g, self._b)
        self.gradient_stops.append((pos, color))
        self.gradient_stops.sort(key=lambda x: x[0])
        self._rebuild_gradient_stops()
        self._update_gradient()

    def _rebuild_gradient_stops(self):
        while self.grad_stops_layout.count():
            item = self.grad_stops_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, (pos, color) in enumerate(self.gradient_stops):
            frame = QFrame()
            frame.setFixedSize(80, 60)
            frame.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #2a2a3a; border-radius: 6px;"
            )
            frame.setToolTip(f"位置: {pos:.0%}")
            self.grad_stops_layout.addWidget(frame)

    def _update_gradient(self):
        grad_type = self.grad_type.currentIndex()
        angle = self.grad_angle.value()
        stops = sorted(self.gradient_stops, key=lambda x: x[0])
        if not stops:
            return
        # build CSS
        stop_str = ", ".join(f"{c.name()} {p*100:.0f}%" for p, c in stops)
        if grad_type == 0:  # linear
            css = f"linear-gradient({angle}deg, {stop_str})"
        elif grad_type == 1:  # radial
            css = f"radial-gradient(circle, {stop_str})"
        else:  # conic
            css = f"conic-gradient(from {angle}deg, {stop_str})"
        self.gradient_css.setText(css)
        # preview - build gradient for painting
        self.gradient_preview.setStyleSheet(
            f"background: {css}; border-radius: 10px; border: 1px solid #2a2a3a;"
        )

    def _update_export_preview(self):
        fmt = self.export_format.currentIndex()
        colors = self._color_history[:10] if self._color_history else [(self._r, self._g, self._b)]
        if fmt == 0:  # CSS
            lines = [":root {"]
            for i, (r, g, b) in enumerate(colors):
                lines.append(f"  --color-{i+1}: {rgb_to_hex(r, g, b)};")
            lines.append("}")
            self.export_preview.setText("\n".join(lines))
        elif fmt == 1:  # SCSS
            lines = []
            for i, (r, g, b) in enumerate(colors):
                lines.append(f"$color-{i+1}: {rgb_to_hex(r, g, b)};")
            self.export_preview.setText("\n".join(lines))
        elif fmt == 2:  # JSON
            data = {
                "colors": [
                    {"hex": rgb_to_hex(r, g, b), "rgb": [r, g, b], "hsl": list(rgb_to_hsl(r, g, b))}
                    for r, g, b in colors
                ]
            }
            self.export_preview.setText(json.dumps(data, indent=2, ensure_ascii=False))
        else:  # ASE
            self.export_preview.setText("ASE 格式需要导出为二进制文件\n请点击「导出文件」按钮保存")

    def _export_file(self):
        fmt = self.export_format.currentIndex()
        colors = self._color_history if self._color_history else [(self._r, self._g, self._b)]
        if fmt == 3:  # ASE
            path, _ = QFileDialog.getSaveFileName(self, "导出 ASE 文件", "palette.ase", "ASE Files (*.ase)")
            if path:
                self._export_ase(path, colors)
        else:
            ext_map = {0: ("CSS Files (*.css)", ".css"), 1: ("SCSS Files (*.scss)", ".scss"), 2: ("JSON Files (*.json)", ".json")}
            ext_filter, ext = ext_map[fmt]
            path, _ = QFileDialog.getSaveFileName(self, "导出文件", f"palette{ext}", ext_filter)
            if path:
                content = self.export_preview.toPlainText()
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def _export_ase(self, path: str, colors: List[Tuple[int, int, int]]):
        """Export colors as Adobe ASE format."""
        try:
            with open(path, 'wb') as f:
                # signature
                f.write(b'ASEF')
                # version 1.0
                f.write(struct.pack('>HH', 1, 0))
                # number of blocks
                f.write(struct.pack('>I', len(colors)))
                for i, (r, g, b) in enumerate(colors):
                    name = f"Color {i+1}"
                    name_bytes = name.encode('utf-16-be') + b'\x00\x00'
                    # color entry block
                    f.write(struct.pack('>H', 0x0001))  # group start
                    f.write(struct.pack('>I', len(name_bytes) + 2))  # block length
                    f.write(struct.pack('>H', len(name) + 1))  # name length
                    f.write(name_bytes)
                    # color model RGB
                    f.write(b'RGB ')
                    f.write(struct.pack('>fff', r / 255, g / 255, b / 255))
                    f.write(struct.pack('>H', 0))  # color type (global)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"ASE 导出失败: {e}")


# ── 入口 ────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    # dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Base, QColor(13, 13, 26))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(17, 17, 34))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(17, 17, 34))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Button, QColor(26, 26, 46))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
