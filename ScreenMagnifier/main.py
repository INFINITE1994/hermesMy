"""
ScreenMagnifier - 屏幕放大镜工具
功能：放大取色、标尺、十字线、网格、截图、全局热键、系统托盘
"""
import sys
import os
import time
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSpinBox, QDoubleSpinBox,
    QFileDialog, QColorDialog, QSystemTrayIcon, QMenu, QToolTip,
    QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QPen, QFont, QIcon,
    QCursor, QScreen, QAction, QKeySequence, QShortcut, QFontDatabase,
    QLinearGradient, QBrush,
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread, QSize, QRect

try:
    from pynput import keyboard as pynput_keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ─── Theme ───────────────────────────────────────────────────────────────────
DARK_BG = "#0a0a0a"
CARD_BG = "#111122"
ACCENT_START = "#667eea"
ACCENT_END = "#764ba2"
TEXT_COLOR = "#e0e0e0"
TEXT_DIM = "#8888aa"
BORDER_COLOR = "#2a2a4a"
HOVER_COLOR = "#1a1a3a"
DANGER = "#ff4757"
SUCCESS = "#2ed573"

STYLE = f"""
QMainWindow {{
    background-color: {DARK_BG};
}}
QWidget {{
    color: {TEXT_COLOR};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QFrame#card {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 12px;
}}
QPushButton {{
    background-color: {CARD_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {HOVER_COLOR};
    border-color: {ACCENT_START};
}}
QPushButton:pressed {{
    background-color: #0d0d1a;
}}
QPushButton[accent="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton[accent="true"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT_START}dd, stop:1 {ACCENT_END}dd);
}}
QPushButton[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border: none;
    color: white;
}}
QLabel {{
    background: transparent;
}}
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: white;
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {TEXT_DIM};
}}
QLabel#zoomLabel {{
    font-size: 28px;
    font-weight: 700;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    -webkit-background-clip: text;
    color: white;
}}
QLabel#colorPreview {{
    border: 2px solid {BORDER_COLOR};
    border-radius: 8px;
    min-width: 40px;
    min-height: 40px;
}}
QLabel#colorValue {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 14px;
    font-weight: 600;
    color: {ACCENT_START};
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 4px 8px;
    color: {TEXT_COLOR};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {ACCENT_START};
}}
QToolTip {{
    background-color: {CARD_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px;
    font-size: 12px;
}}
"""


class MagnifierView(QWidget):
    """Magnified view widget - displays magnified screen area around cursor."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 2.0
        self.capture_radius = 150  # pixels around cursor to capture
        self.magnified_pixmap = None
        self.show_crosshair = True
        self.show_grid = False
        self.grid_size = 20
        self.crosshair_color = QColor(ACCENT_START)
        self.grid_color = QColor(100, 100, 180, 60)
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Timer for continuous capture
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnified)
        self.timer.start(50)  # 20 fps
    
    def set_zoom(self, zoom):
        self.zoom_factor = max(1.0, min(20.0, zoom))
    
    def update_magnified(self):
        """Capture screen area around cursor and magnify it."""
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        if not screen:
            return
        
        r = int(self.capture_radius / self.zoom_factor)
        rect = QRect(cursor_pos.x() - r, cursor_pos.y() - r, r * 2, r * 2)
        
        # Clamp to screen bounds
        screen_rect = screen.geometry()
        rect = rect.intersected(screen_rect)
        
        if rect.width() <= 0 or rect.height() <= 0:
            return
        
        pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        if pixmap.isNull():
            return
        
        # Scale up
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.magnified_pixmap = scaled
        self.update()
    
    def paintEvent(self, event):
        if not self.magnified_pixmap:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw magnified image centered
        x = (self.width() - self.magnified_pixmap.width()) // 2
        y = (self.height() - self.magnified_pixmap.height()) // 2
        painter.drawPixmap(x, y, self.magnified_pixmap)
        
        cx = self.width() // 2
        cy = self.height() // 2
        
        # Draw crosshair
        if self.show_crosshair:
            pen = QPen(self.crosshair_color, 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(cx, 0, cx, self.height())
            painter.drawLine(0, cy, self.width(), cy)
            # Center marker
            painter.setPen(QPen(QColor(255, 80, 80, 200), 2))
            painter.drawLine(cx - 10, cy, cx + 10, cy)
            painter.drawLine(cx, cy - 10, cx, cy + 10)
        
        # Draw grid
        if self.show_grid:
            pen = QPen(self.grid_color, 0.5)
            painter.setPen(pen)
            gs = self.grid_size
            for gx in range(0, self.width(), gs):
                painter.drawLine(gx, 0, gx, self.height())
            for gy in range(0, self.height(), gs):
                painter.drawLine(0, gy, self.width(), gy)
        
        # Border
        painter.setPen(QPen(QColor(BORDER_COLOR), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        
        painter.end()


class RulerWidget(QWidget):
    """Transparent ruler overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.ruler_length = 500
        self.setFixedSize(self.ruler_length + 40, 60)
        self._drag_pos = None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.setBrush(QColor(10, 10, 30, 200))
        painter.setPen(QPen(QColor(ACCENT_START), 1))
        painter.drawRoundedRect(5, 5, self.ruler_length + 30, 50, 8, 8)
        
        # Ruler marks
        pen = QPen(QColor(ACCENT_START), 1)
        painter.setPen(pen)
        font = QFont("Consolas", 7)
        painter.setFont(font)
        
        for i in range(self.ruler_length + 1):
            x = 20 + i
            if i % 100 == 0:
                painter.setPen(QPen(QColor(ACCENT_START), 2))
                painter.drawLine(x, 15, x, 45)
                painter.drawText(x + 2, 14, str(i))
            elif i % 50 == 0:
                painter.setPen(QPen(QColor(ACCENT_START), 1))
                painter.drawLine(x, 25, x, 45)
            elif i % 10 == 0:
                painter.setPen(QPen(QColor("#444466"), 1))
                painter.drawLine(x, 35, x, 45)
        
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class ColorPickerOverlay(QWidget):
    """Full-screen transparent overlay for picking a color."""
    
    color_picked = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._screen_pixmap = None
        self._zoom_timer = QTimer(self)
        self._zoom_timer.timeout.connect(self.update)
        self._zoom_timer.start(30)
    
    def showEvent(self, event):
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
            self._screen_pixmap = screen.grabWindow(0)
        self.grabMouse()
        self.raise_()
    
    def paintEvent(self, event):
        if not self._screen_pixmap:
            return
        
        painter = QPainter(self)
        
        # Draw dimmed screenshot
        painter.drawPixmap(0, 0, self._screen_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        
        # Get pixel color under cursor
        pos = QCursor.pos()
        x, y = pos.x(), pos.y()
        
        img = self._screen_pixmap.toImage()
        if 0 <= x < img.width() and 0 <= y < img.height():
            color = QColor(img.pixel(x, y))
        else:
            color = QColor(0, 0, 0)
        
        # Draw magnifier circle
        mag_r = 60
        mag_scale = 8
        src_r = mag_r // mag_scale
        src_rect = QRect(x - src_r, y - src_r, src_r * 2, src_r * 2)
        dst_rect = QRect(x - mag_r - 10, y - mag_r - 10, mag_r * 2, mag_r * 2)
        
        # Offset if near edges
        if dst_rect.top() < 0:
            dst_rect.moveTop(y + 20)
        if dst_rect.left() < 0:
            dst_rect.moveLeft(x + 20)
        if dst_rect.right() > self.width():
            dst_rect.moveRight(x - 20)
        if dst_rect.bottom() > self.height():
            dst_rect.moveBottom(y - 20)
        
        painter.setPen(QPen(QColor(ACCENT_START), 2))
        painter.setBrush(QColor(10, 10, 30, 220))
        painter.drawEllipse(dst_rect)
        
        # Draw magnified pixels
        clipped = src_rect.intersected(QRect(0, 0, img.width(), img.height()))
        if clipped.width() > 0 and clipped.height() > 0:
            sub = img.copy(clipped)
            sub_scaled = QPixmap.fromImage(sub).scaled(
                dst_rect.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            # Clip to circle
            painter.save()
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.addEllipse(float(dst_rect.x()), float(dst_rect.y()),
                            float(dst_rect.width()), float(dst_rect.height()))
            painter.setClipPath(path)
            painter.drawPixmap(dst_rect.x(), dst_rect.y(), sub_scaled)
            painter.restore()
            
            # Draw center pixel indicator
            cx = dst_rect.x() + dst_rect.width() // 2
            cy = dst_rect.y() + dst_rect.height() // 2
            ps = mag_scale
            painter.setPen(QPen(QColor(255, 255, 255), 1.5))
            painter.drawRect(cx - ps // 2, cy - ps // 2, ps, ps)
        
        # Draw color info
        info_x = dst_rect.right() + 10
        info_y = dst_rect.top()
        painter.setPen(QPen(QColor(BORDER_COLOR), 1))
        painter.setBrush(QColor(10, 10, 30, 230))
        info_rect = QRect(info_x, info_y, 160, 80)
        painter.drawRoundedRect(info_rect, 8, 8)
        
        # Color swatch
        painter.setBrush(color)
        painter.setPen(QPen(QColor(TEXT_COLOR), 1))
        painter.drawRect(info_x + 10, info_y + 10, 30, 30)
        
        # Color text
        painter.setPen(QColor(TEXT_COLOR))
        painter.setFont(QFont("Consolas", 10))
        hex_str = color.name().upper()
        painter.drawText(info_x + 50, info_y + 22, hex_str)
        rgb_str = f"R:{color.red()} G:{color.green()} B:{color.blue()}"
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(info_x + 50, info_y + 42, rgb_str)
        
        # Cursor position
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor(TEXT_DIM))
        pos_str = f"({x}, {y})"
        painter.drawText(info_x + 50, info_y + 62, pos_str)
        
        # Crosshair lines
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, y, self.width(), y)
        painter.drawLine(x, 0, x, self.height())
        
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.globalPosition().toPoint()
            if self._screen_pixmap:
                img = self._screen_pixmap.toImage()
                if 0 <= pos.x() < img.width() and 0 <= pos.y() < img.height():
                    color = QColor(img.pixel(pos.x(), pos.y()))
                    self.color_picked.emit(color)
            self.releaseMouse()
            self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            self.releaseMouse()
            self.close()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.releaseMouse()
            self.close()


class GridOverlay(QWidget):
    """Full-screen semi-transparent grid overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.grid_size = 50
        self.grid_color = QColor(ACCENT_START)
        self.grid_alpha = 40
    
    def showEvent(self, event):
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
    
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(self.grid_color.red(), self.grid_color.green(),
                          self.grid_color.blue(), self.grid_alpha), 1)
        painter.setPen(pen)
        
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        painter.end()


class GlobalHotkeyThread(QThread):
    """Thread for listening to global hotkeys via pynput."""
    
    hotkey_triggered = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
    
    def run(self):
        if not HAS_PYNPUT:
            return
        
        def on_activate(name):
            self.hotkey_triggered.emit(name)
        
        def for_canonical(f):
            return lambda k: f(l.canonical(k))
        
        hotkeys = {
            '<ctrl>+<alt>+m': lambda: on_activate('magnify'),
            '<ctrl>+<alt>+c': lambda: on_activate('color_pick'),
            '<ctrl>+<alt>+r': lambda: on_activate('ruler'),
            '<ctrl>+<alt>+g': lambda: on_activate('grid'),
            '<ctrl>+<alt>+s': lambda: on_activate('screenshot'),
            '<ctrl>+<alt>+h': lambda: on_activate('toggle_visibility'),
        }
        
        try:
            with pynput_keyboard.GlobalHotKeys(hotkeys) as l:
                l.join()
        except Exception:
            pass
    
    def stop(self):
        self._running = False
        self.terminate()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 屏幕放大镜 - ScreenMagnifier")
        self.setMinimumSize(520, 620)
        self.resize(520, 620)
        self.setStyleSheet(STYLE)
        
        # State
        self.current_color = QColor(0, 0, 0)
        self.ruler_widget = None
        self.grid_overlay = None
        self.color_picker = None
        
        self._init_ui()
        self._init_tray()
        self._init_hotkeys()
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # ── Header ──
        header = QLabel("🔍 屏幕放大镜")
        header.setObjectName("title")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        subtitle = QLabel("实时屏幕放大 · 取色器 · 标尺 · 网格 · 截图")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(8)
        
        # ── Magnifier Card ──
        mag_card = QFrame()
        mag_card.setObjectName("card")
        mag_layout = QVBoxLayout(mag_card)
        mag_layout.setSpacing(10)
        
        mag_title = QLabel("📐 放大镜")
        mag_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #8888cc;")
        mag_layout.addWidget(mag_title)
        
        # Magnifier view
        self.magnifier = MagnifierView()
        self.magnifier.setMinimumHeight(260)
        mag_layout.addWidget(self.magnifier)
        
        # Zoom controls
        zoom_row = QHBoxLayout()
        zoom_row.setSpacing(8)
        
        zoom_label = QLabel("放大倍率:")
        zoom_label.setStyleSheet("font-size: 12px; color: #8888aa;")
        zoom_row.addWidget(zoom_label)
        
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(1.0, 20.0)
        self.zoom_spin.setValue(2.0)
        self.zoom_spin.setSingleStep(0.5)
        self.zoom_spin.setDecimals(1)
        self.zoom_spin.setSuffix("×")
        self.zoom_spin.setStyleSheet("min-width: 80px;")
        self.zoom_spin.valueChanged.connect(lambda v: self.magnifier.set_zoom(v))
        zoom_row.addWidget(self.zoom_spin)
        
        zoom_row.addStretch()
        
        # Quick zoom buttons
        for z in [1.5, 2.0, 4.0, 8.0, 16.0]:
            btn = QPushButton(f"{z}×")
            btn.setFixedSize(44, 32)
            btn.clicked.connect(lambda checked, v=z: self.zoom_spin.setValue(v))
            zoom_row.addWidget(btn)
        
        mag_layout.addLayout(zoom_row)
        
        # Toggle buttons row
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)
        
        self.crosshair_btn = QPushButton("✚ 十字线")
        self.crosshair_btn.setProperty("active", True)
        self.crosshair_btn.setCheckable(True)
        self.crosshair_btn.setChecked(True)
        self.crosshair_btn.toggled.connect(self._toggle_crosshair)
        toggle_row.addWidget(self.crosshair_btn)
        
        self.grid_btn = QPushButton("▦ 网格")
        self.grid_btn.setCheckable(True)
        self.grid_btn.toggled.connect(self._toggle_grid)
        toggle_row.addWidget(self.grid_btn)
        
        mag_layout.addLayout(toggle_row)
        
        main_layout.addWidget(mag_card)
        
        # ── Tools Row ──
        tools_row = QHBoxLayout()
        tools_row.setSpacing(10)
        
        # Color picker card
        color_card = QFrame()
        color_card.setObjectName("card")
        color_layout = QVBoxLayout(color_card)
        color_layout.setSpacing(8)
        
        color_title = QLabel("🎨 取色器")
        color_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888cc;")
        color_layout.addWidget(color_title)
        
        self.color_preview = QLabel()
        self.color_preview.setObjectName("colorPreview")
        self.color_preview.setFixedSize(40, 40)
        self.color_preview.setStyleSheet(
            f"background-color: #000000; border: 2px solid {BORDER_COLOR}; border-radius: 8px;"
        )
        color_layout.addWidget(self.color_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.color_value = QLabel("#000000")
        self.color_value.setObjectName("colorValue")
        self.color_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_layout.addWidget(self.color_value)
        
        pick_btn = QPushButton("🔍 拾取颜色")
        pick_btn.setProperty("accent", True)
        pick_btn.clicked.connect(self._start_color_pick)
        color_layout.addWidget(pick_btn)
        
        copy_btn = QPushButton("📋 复制色值")
        copy_btn.clicked.connect(self._copy_color)
        color_layout.addWidget(copy_btn)
        
        tools_row.addWidget(color_card)
        
        # Screenshot card
        ss_card = QFrame()
        ss_card.setObjectName("card")
        ss_layout = QVBoxLayout(ss_card)
        ss_layout.setSpacing(8)
        
        ss_title = QLabel("📸 截图")
        ss_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888cc;")
        ss_layout.addWidget(ss_title)
        
        ss_desc = QLabel("捕获当前放大区域\n并保存为图片")
        ss_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
        ss_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ss_layout.addWidget(ss_desc)
        
        ss_btn = QPushButton("📸 保存截图")
        ss_btn.setProperty("accent", True)
        ss_btn.clicked.connect(self._take_screenshot)
        ss_layout.addWidget(ss_btn)
        
        ss_clip_btn = QPushButton("📋 复制到剪贴板")
        ss_clip_btn.clicked.connect(self._screenshot_to_clipboard)
        ss_layout.addWidget(ss_clip_btn)
        
        tools_row.addWidget(ss_card)
        
        # Ruler card
        ruler_card = QFrame()
        ruler_card.setObjectName("card")
        ruler_layout = QVBoxLayout(ruler_card)
        ruler_layout.setSpacing(8)
        
        ruler_title = QLabel("📏 标尺")
        ruler_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888cc;")
        ruler_layout.addWidget(ruler_title)
        
        ruler_desc = QLabel("屏幕标尺\n可拖动定位")
        ruler_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
        ruler_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruler_layout.addWidget(ruler_desc)
        
        self.ruler_btn = QPushButton("📏 显示标尺")
        self.ruler_btn.setCheckable(True)
        self.ruler_btn.toggled.connect(self._toggle_ruler)
        ruler_layout.addWidget(self.ruler_btn)
        
        ruler_len_row = QHBoxLayout()
        rl = QLabel("长度:")
        rl.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
        ruler_len_row.addWidget(rl)
        self.ruler_len_spin = QSpinBox()
        self.ruler_len_spin.setRange(100, 1920)
        self.ruler_len_spin.setValue(500)
        self.ruler_len_spin.setSuffix(" px")
        self.ruler_len_spin.valueChanged.connect(self._update_ruler_length)
        ruler_len_row.addWidget(self.ruler_len_spin)
        ruler_layout.addLayout(ruler_len_row)
        
        tools_row.addWidget(ruler_card)
        
        main_layout.addLayout(tools_row)
        
        # ── Grid Overlay Card ──
        grid_card = QFrame()
        grid_card.setObjectName("card")
        grid_layout_h = QHBoxLayout(grid_card)
        grid_layout_h.setSpacing(12)
        
        grid_title = QLabel("🔲 全屏网格覆盖")
        grid_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888cc;")
        grid_layout_h.addWidget(grid_title)
        
        grid_size_label = QLabel("网格大小:")
        grid_size_label.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
        grid_layout_h.addWidget(grid_size_label)
        
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 200)
        self.grid_size_spin.setValue(50)
        self.grid_size_spin.setSuffix(" px")
        self.grid_size_spin.valueChanged.connect(self._update_grid_size)
        grid_layout_h.addWidget(self.grid_size_spin)
        
        self.grid_overlay_btn = QPushButton("▦ 显示网格")
        self.grid_overlay_btn.setCheckable(True)
        self.grid_overlay_btn.toggled.connect(self._toggle_grid_overlay)
        grid_layout_h.addWidget(self.grid_overlay_btn)
        
        grid_layout_h.addStretch()
        
        main_layout.addWidget(grid_card)
        
        # ── Hotkeys Info ──
        hk_card = QFrame()
        hk_card.setObjectName("card")
        hk_layout = QHBoxLayout(hk_card)
        hk_layout.setSpacing(16)
        
        hk_title = QLabel("⌨️ 快捷键")
        hk_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888cc;")
        hk_layout.addWidget(hk_title)
        
        hotkeys_info = [
            ("Ctrl+Alt+M", "放大镜"),
            ("Ctrl+Alt+C", "取色"),
            ("Ctrl+Alt+R", "标尺"),
            ("Ctrl+Alt+G", "网格"),
            ("Ctrl+Alt+S", "截图"),
            ("Ctrl+Alt+H", "显示/隐藏"),
            ("滚轮", "缩放"),
        ]
        
        for key, desc in hotkeys_info:
            lbl = QLabel(f"<b>{key}</b> {desc}")
            lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
            hk_layout.addWidget(lbl)
        
        hk_layout.addStretch()
        
        main_layout.addWidget(hk_card)
        
        # ── Status Bar ──
        status = QLabel("就绪 · Ctrl+Alt+H 显示/隐藏窗口")
        status.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM}; padding: 4px;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(status)
    
    def _init_tray(self):
        """Initialize system tray icon."""
        # Create a simple icon via QPixmap
        icon_size = 64
        pm = QPixmap(icon_size, icon_size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, icon_size, icon_size)
        grad.setColorAt(0, QColor(ACCENT_START))
        grad.setColorAt(1, QColor(ACCENT_END))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(4, 4, icon_size - 8, icon_size - 8, 12, 12)
        p.setPen(QPen(QColor(255, 255, 255), 3))
        p.setFont(QFont("Arial", 28))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "🔍")
        p.end()
        
        self.tray_icon = QSystemTrayIcon(QIcon(pm), self)
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {CARD_BG};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: {HOVER_COLOR};
            }}
        """)
        
        show_action = QAction("🔍 显示主窗口", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        pick_action = QAction("🎨 取色器", self)
        pick_action.triggered.connect(self._start_color_pick)
        tray_menu.addAction(pick_action)
        
        ruler_action = QAction("📏 标尺", self)
        ruler_action.triggered.connect(lambda: self.ruler_btn.toggle())
        tray_menu.addAction(ruler_action)
        
        grid_action = QAction("▦ 网格", self)
        grid_action.triggered.connect(lambda: self.grid_overlay_btn.toggle())
        tray_menu.addAction(grid_action)
        
        ss_action = QAction("📸 截图", self)
        ss_action.triggered.connect(self._take_screenshot)
        tray_menu.addAction(ss_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("❌ 退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("屏幕放大镜 - ScreenMagnifier")
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()
    
    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()
    
    def _init_hotkeys(self):
        """Initialize global hotkeys."""
        self.hotkey_thread = None
        
        # Local shortcuts (always work when window is focused)
        QShortcut(QKeySequence("Ctrl+Q"), self, self._quit_app)
        QShortcut(QKeySequence("Escape"), self, self.close)
        
        if HAS_PYNPUT:
            self.hotkey_thread = GlobalHotkeyThread(self)
            self.hotkey_thread.hotkey_triggered.connect(self._handle_hotkey)
            self.hotkey_thread.start()
    
    def _handle_hotkey(self, action):
        if action == 'magnify':
            self.showNormal()
            self.activateWindow()
        elif action == 'color_pick':
            self._start_color_pick()
        elif action == 'ruler':
            self.ruler_btn.toggle()
        elif action == 'grid':
            self.grid_overlay_btn.toggle()
        elif action == 'screenshot':
            self._take_screenshot()
        elif action == 'toggle_visibility':
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()
    
    def _toggle_crosshair(self, checked):
        self.magnifier.show_crosshair = checked
        self.crosshair_btn.setProperty("active", checked)
        self.crosshair_btn.style().unpolish(self.crosshair_btn)
        self.crosshair_btn.style().polish(self.crosshair_btn)
    
    def _toggle_grid(self, checked):
        self.magnifier.show_grid = checked
    
    def _start_color_pick(self):
        self.color_picker = ColorPickerOverlay()
        self.color_picker.color_picked.connect(self._on_color_picked)
        self.color_picker.showFullScreen()
    
    def _on_color_picked(self, color):
        self.current_color = color
        hex_str = color.name().upper()
        self.color_preview.setStyleSheet(
            f"background-color: {hex_str}; border: 2px solid {BORDER_COLOR}; border-radius: 8px;"
        )
        self.color_value.setText(hex_str)
        self.showNormal()
        self.activateWindow()
    
    def _copy_color(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.color_value.text())
            self.tray_icon.showMessage("复制成功", f"已复制: {self.color_value.text()}", 
                                        QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def _take_screenshot(self):
        if self.magnifier.magnified_pixmap:
            path, _ = QFileDialog.getSaveFileName(
                self, "保存截图", 
                os.path.expanduser(f"~/Desktop/screenshot_{int(time.time())}.png"),
                "PNG 图片 (*.png);;JPEG 图片 (*.jpg);;所有文件 (*.*)"
            )
            if path:
                self.magnifier.magnified_pixmap.save(path)
                self.tray_icon.showMessage("截图已保存", f"已保存到: {path}",
                                            QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def _screenshot_to_clipboard(self):
        if self.magnifier.magnified_pixmap:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setPixmap(self.magnifier.magnified_pixmap)
                self.tray_icon.showMessage("复制成功", "截图已复制到剪贴板",
                                            QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def _toggle_ruler(self, checked):
        if checked:
            self.ruler_widget = RulerWidget()
            self.ruler_widget.show()
            self.ruler_btn.setText("📏 隐藏标尺")
        else:
            if self.ruler_widget:
                self.ruler_widget.close()
                self.ruler_widget = None
            self.ruler_btn.setText("📏 显示标尺")
    
    def _update_ruler_length(self, value):
        if self.ruler_widget:
            self.ruler_widget.ruler_length = value
            self.ruler_widget.setFixedSize(value + 40, 60)
            self.ruler_widget.update()
    
    def _toggle_grid_overlay(self, checked):
        if checked:
            self.grid_overlay = GridOverlay()
            self.grid_overlay.grid_size = self.grid_size_spin.value()
            self.grid_overlay.showFullScreen()
            self.grid_overlay_btn.setText("▦ 隐藏网格")
        else:
            if self.grid_overlay:
                self.grid_overlay.close()
                self.grid_overlay = None
            self.grid_overlay_btn.setText("▦ 显示网格")
    
    def _update_grid_size(self, value):
        if self.grid_overlay:
            self.grid_overlay.grid_size = value
            self.grid_overlay.update()
    
    def _quit_app(self):
        if self.hotkey_thread:
            self.hotkey_thread.stop()
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Minimize to tray on close."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "屏幕放大镜",
            "已最小化到系统托盘，双击图标或使用 Ctrl+Alt+H 恢复",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        step = 0.5
        if delta > 0:
            self.zoom_spin.setValue(self.zoom_spin.value() + step)
        else:
            self.zoom_spin.setValue(self.zoom_spin.value() - step)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenMagnifier")
    app.setApplicationDisplayName("屏幕放大镜")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
