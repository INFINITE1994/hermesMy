#!/usr/bin/env python3
"""
ColorPalette - 智能配色方案生成器
===================================
一款功能强大的桌面配色工具，支持 AI 配色、图片提取、色彩和谐、
趋势配色、保存管理、多格式导出及无障碍检查。

作者: Nous Research
版本: 1.0.0
"""

import sys
import os
import json
import hashlib
import base64
import struct
import colorsys
import random
import math
import io
import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFileDialog, QMessageBox, QTabWidget, QScrollArea, QFrame,
    QSizePolicy, QSpacerItem, QSplitter, QTextEdit, QSpinBox,
    QDoubleSpinBox, QGroupBox, QCheckBox, QToolButton, QMenu,
    QColorDialog, QDialog, QFormLayout, QDialogButtonBox,
    QProgressBar, QStatusBar, QToolBar, QStackedWidget
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve,
    QMimeData, QUrl, pyqtSignal, QPoint, QRect, QThread
)
from PyQt6.QtGui import (
    QColor, QPalette, QFont, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QImage, QClipboard, QDrag,
    QAction, QCursor, QFontDatabase, QConicalGradient,
    QRadialGradient, QTransform
)

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ─── 色彩数据 ───────────────────────────────────────────────────────────────

KEYWORD_PALETTES = {
    "温暖": ["#FF6B6B", "#FFA07A", "#FFD700", "#FF8C42", "#E74C3C"],
    "冷色": ["#4A90D9", "#5DADE2", "#85C1E9", "#3498DB", "#2E86C1"],
    "自然": ["#27AE60", "#2ECC71", "#F39C12", "#D35400", "#8B4513"],
    "海洋": ["#1ABC9C", "#16A085", "#2980B9", "#3498DB", "#2C3E50"],
    "日落": ["#FF6B6B", "#FF8E53", "#FFC107", "#FF5722", "#9C27B0"],
    "森林": ["#2D5016", "#4A7C59", "#6B8F71", "#8FB996", "#AAD2BA"],
    "薰衣草": ["#9B59B6", "#8E44AD", "#C39BD3", "#D2B4DE", "#E8DAEF"],
    "极简": ["#2C3E50", "#ECF0F1", "#BDC3C7", "#95A5A6", "#7F8C8D"],
    "活力": ["#E74C3C", "#F39C12", "#2ECC71", "#3498DB", "#9B59B6"],
    "复古": ["#C0392B", "#D4A574", "#8B7355", "#556B2F", "#4A4A4A"],
    "霓虹": ["#FF00FF", "#00FFFF", "#FF1493", "#7FFF00", "#FF6347"],
    "糖果": ["#FFB6C1", "#FFD700", "#98FB98", "#87CEEB", "#DDA0DD"],
}

TREND_PALETTES = {
    "Material Design 3": {
        "主色": ["#6750A4", "#625B71", "#7D5260", "#FFFFFF", "#1D1B20"],
        "描述": "Google Material You 设计系统配色"
    },
    "Flat UI": {
        "主色": ["#1ABC9C", "#2ECC71", "#3498DB", "#9B59B6", "#E74C3C"],
        "描述": "扁平化设计经典配色方案"
    },
    "Tailwind CSS": {
        "主色": ["#0EA5E9", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"],
        "描述": "Tailwind CSS 默认调色板"
    },
    "Instagram 渐变": {
        "主色": ["#405DE6", "#5851DB", "#833AB4", "#C13584", "#E1306C"],
        "描述": "Instagram 品牌渐变配色"
    },
    "Spotify": {
        "主色": ["#1DB954", "#191414", "#FFFFFF", "#535353", "#B3B3B3"],
        "描述": "Spotify 品牌色彩系统"
    },
    "暗黑模式": {
        "主色": ["#0D1117", "#161B22", "#21262D", "#58A6FF", "#C9D1D9"],
        "描述": "GitHub 暗黑主题配色"
    },
    "Glassmorphism": {
        "主色": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
        "描述": "毛玻璃风格流行配色"
    },
    "Cyberpunk": {
        "主色": ["#F72585", "#B5179E", "#7209B7", "#560BAD", "#480CA8"],
        "描述": "赛博朋克风格配色"
    },
}


# ─── 工具函数 ───────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(c1: str, c2: str) -> float:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    l1 = relative_luminance(r1, g1, b1)
    l2 = relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_grade(ratio: float) -> str:
    if ratio >= 7.0:
        return "AAA ✓"
    elif ratio >= 4.5:
        return "AA ✓"
    elif ratio >= 3.0:
        return "AA 大字 ✓"
    else:
        return "不通过 ✗"


def generate_harmony(base_hex: str, mode: str) -> list:
    r, g, b = hex_to_rgb(base_hex)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    def hls_to_hex(hue, light, sat):
        hue = hue % 1.0
        r2, g2, b2 = colorsys.hls_to_rgb(hue, light, sat)
        return rgb_to_hex(int(r2 * 255), int(g2 * 255), int(b2 * 255))

    if mode == "互补色":
        return [base_hex, hls_to_hex(h + 0.5, l, s)]
    elif mode == "类似色":
        return [hls_to_hex(h - 0.083, l, s), base_hex, hls_to_hex(h + 0.083, l, s)]
    elif mode == "三角色":
        return [base_hex, hls_to_hex(h + 1/3, l, s), hls_to_hex(h + 2/3, l, s)]
    elif mode == "分裂互补":
        return [base_hex, hls_to_hex(h + 0.417, l, s), hls_to_hex(h + 0.583, l, s)]
    elif mode == "四角色":
        return [base_hex, hls_to_hex(h + 0.25, l, s), hls_to_hex(h + 0.5, l, s), hls_to_hex(h + 0.75, l, s)]
    elif mode == "单色":
        return [hls_to_hex(h, max(0.1, l - 0.3), s), base_hex, hls_to_hex(h, min(0.9, l + 0.2), s)]
    return [base_hex]


def extract_colors_from_image(image_path: str, num_colors: int = 6) -> list:
    if not PIL_AVAILABLE:
        return ["#FF0000", "#00FF00", "#0000FF"]
    img = PILImage.open(image_path).convert("RGB")
    img = img.resize((150, 150))
    pixels = list(img.getdata())
    random.seed(42)
    samples = random.sample(pixels, min(len(pixels), num_colors * 50))
    centroids = random.sample(samples, min(num_colors, len(samples)))

    for _ in range(10):
        clusters = {}
        for i in range(len(centroids)):
            clusters[i] = []
        for px in samples:
            dists = [sum((a - b) ** 2 for a, b in zip(px, c)) for c in centroids]
            clusters[dists.index(min(dists))].append(px)
        new_centroids = []
        for i in range(len(centroids)):
            if clusters[i]:
                avg = tuple(sum(p[j] for p in clusters[i]) // len(clusters[i]) for j in range(3))
                new_centroids.append(avg)
            else:
                new_centroids.append(centroids[i])
        centroids = new_centroids

    return [rgb_to_hex(*c) for c in centroids]


# ─── 配色卡片组件 ────────────────────────────────────────────────────────────

class ColorSwatch(QFrame):
    """单个颜色色块卡片"""
    clicked = pyqtSignal(str)
    colorChanged = pyqtSignal(str, str)

    def __init__(self, hex_color: str, label: str = "", parent=None):
        super().__init__(parent)
        self._hex_color = hex_color
        self._label = label
        self.setFixedSize(100, 130)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(f"{hex_color}\n点击复制颜色值 | 右键修改颜色")

    @property
    def hex_color(self) -> str:
        return self._hex_color

    @hex_color.setter
    def hex_color(self, value: str):
        self._hex_color = value
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._hex_color)
            self.clicked.emit(self._hex_color)
        elif event.button() == Qt.MouseButton.RightButton:
            color = QColorDialog.getColor(QColor(self._hex_color), self, "选择颜色")
            if color.isValid():
                old = self._hex_color
                self._hex_color = color.name().upper()
                self.colorChanged.emit(old, self._hex_color)
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -35)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._hex_color))
        painter.drawRoundedRect(rect, 10, 10)

        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)

        painter.setPen(QColor(200, 200, 210))
        font = painter.font()
        font.setPixelSize(11)
        font.setFamily("Consolas")
        painter.setFont(font)
        text_rect = self.rect().adjusted(0, self.height() - 32, 0, -2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._hex_color)

        if self._label:
            painter.setPen(QColor(160, 160, 170))
            font.setPixelSize(9)
            font.setFamily("Segoe UI")
            painter.setFont(font)
            label_rect = self.rect().adjusted(0, self.height() - 18, 0, -2)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label)

        painter.end()


class ColorStrip(QFrame):
    """水平颜色条"""
    clicked = pyqtSignal(str)

    def __init__(self, colors: list, height: int = 60, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._height = height
        self.setFixedHeight(height)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    @property
    def colors(self) -> list:
        return self._colors

    @colors.setter
    def colors(self, value: list):
        self._colors = value
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._colors:
            idx = int(event.position().x() / self.width() * len(self._colors))
            idx = min(idx, len(self._colors) - 1)
            clipboard = QApplication.clipboard()
            clipboard.setText(self._colors[idx])
            self.clicked.emit(self._colors[idx])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self._height
        n = len(self._colors)
        if n == 0:
            painter.end()
            return
        seg_w = w / n
        for i, c in enumerate(self._colors):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c))
            x = int(i * seg_w)
            nw = int((i + 1) * seg_w) - x
            radius = 8
            if i == 0:
                painter.drawRoundedRect(x, 2, nw, h - 4, radius, 0)
            elif i == n - 1:
                painter.drawRoundedRect(x, 2, nw, h - 4, 0, radius)
            else:
                painter.drawRect(x, 2, nw, h - 4)
        painter.end()


# ─── 对话框 ──────────────────────────────────────────────────────────────────

DIALOG_STYLE = """
    QDialog { background: #111122; color: #e0e0f0; }
    QLabel { color: #c0c0d0; }
    QLineEdit, QComboBox {
        background: #1a1a2e; border: 1px solid #333;
        border-radius: 6px; padding: 8px; color: #e0e0f0;
    }
    QLineEdit:focus, QComboBox:focus { border-color: #667eea; }
    QPushButton {
        background: #1a1a2e; border: 1px solid #2a2a3e;
        border-radius: 6px; padding: 8px 16px; color: #e0e0f0;
    }
    QPushButton:hover { border-color: #667eea; }
"""


class SavePaletteDialog(QDialog):
    def __init__(self, colors: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存配色方案")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)

        strip = ColorStrip(colors, 40)
        layout.addWidget(strip)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入配色方案名称...")
        self.tag_combo = QComboBox()
        self.tag_combo.addItems(["默认", "项目", "品牌", "网站", "插画", "UI设计", "其他"])
        self.tag_combo.setEditable(True)
        form.addRow("名称:", self.name_edit)
        form.addRow("标签:", self.tag_combo)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self) -> dict:
        return {"name": self.name_edit.text() or "未命名配色", "tag": self.tag_combo.currentText()}


class ContrastDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("无障碍对比度检查")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DIALOG_STYLE + """
            QPushButton#pickBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white; font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.fg_btn = QPushButton("前景色: #FFFFFF")
        self.fg_btn.setObjectName("pickBtn")
        self.bg_btn = QPushButton("背景色: #000000")
        self.bg_btn.setObjectName("pickBtn")
        self._fg = "#FFFFFF"
        self._bg = "#000000"
        self.fg_btn.clicked.connect(self._pick_fg)
        self.bg_btn.clicked.connect(self._pick_bg)
        row.addWidget(self.fg_btn)
        row.addWidget(self.bg_btn)
        layout.addLayout(row)

        self.preview = QLabel("Aa 预览文字 Sample Text 123")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("font-size: 24px; border-radius: 10px; padding: 20px;")
        layout.addWidget(self.preview)

        self.ratio_label = QLabel()
        self.ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ratio_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.ratio_label)

        self.wcag_label = QLabel()
        self.wcag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wcag_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.wcag_label)

        swap_btn = QPushButton("交换前景/背景")
        swap_btn.clicked.connect(self._swap)
        layout.addWidget(swap_btn)

        self._update()

    def _pick_fg(self):
        c = QColorDialog.getColor(QColor(self._fg), self)
        if c.isValid():
            self._fg = c.name().upper()
            self.fg_btn.setText(f"前景色: {self._fg}")
            self._update()

    def _pick_bg(self):
        c = QColorDialog.getColor(QColor(self._bg), self)
        if c.isValid():
            self._bg = c.name().upper()
            self.bg_btn.setText(f"背景色: {self._bg}")
            self._update()

    def _swap(self):
        self._fg, self._bg = self._bg, self._fg
        self.fg_btn.setText(f"前景色: {self._fg}")
        self.bg_btn.setText(f"背景色: {self._bg}")
        self._update()

    def _update(self):
        self.preview.setStyleSheet(
            f"font-size: 24px; border-radius: 10px; padding: 20px;"
            f"color: {self._fg}; background: {self._bg};"
        )
        ratio = contrast_ratio(self._fg, self._bg)
        self.ratio_label.setText(f"对比度: {ratio:.2f}:1")
        color = '#2ecc71' if ratio >= 4.5 else '#e74c3c'
        self.ratio_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        aa = "AA ✓" if ratio >= 4.5 else "AA ✗"
        aaa = "AAA ✓" if ratio >= 7.0 else "AAA ✗"
        aa_large = "AA 大字 ✓" if ratio >= 3.0 else "AA 大字 ✗"
        self.wcag_label.setText(f"WCAG 2.1:  {aa}  |  {aa_large}  |  {aaa}")


class ExportDialog(QDialog):
    def __init__(self, colors: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出配色方案")
        self.setMinimumWidth(450)
        self.setStyleSheet(DIALOG_STYLE + """
            QTextEdit {
                background: #0a0a0a; border: 1px solid #333;
                border-radius: 6px; color: #a0d0a0;
                font-family: Consolas; font-size: 12px;
            }
            QPushButton#exportBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white; font-weight: bold;
            }
        """)

        self._colors = colors
        layout = QVBoxLayout(self)

        fmt_row = QHBoxLayout()
        formats = ["CSS", "SCSS", "JSON", "ASE"]
        self._format = "CSS"
        self._fmt_btns = {}
        for f in formats:
            btn = QPushButton(f)
            btn.setCheckable(True)
            btn.setChecked(f == "CSS")
            btn.clicked.connect(lambda checked, fmt=f: self._set_format(fmt))
            self._fmt_btns[f] = btn
            fmt_row.addWidget(btn)
        layout.addLayout(fmt_row)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("📋 复制到剪贴板")
        copy_btn.setObjectName("exportBtn")
        copy_btn.clicked.connect(self._copy)
        save_btn = QPushButton("💾 保存到文件")
        save_btn.setObjectName("exportBtn")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._update_preview()

    def _set_format(self, fmt):
        self._format = fmt
        for f, btn in self._fmt_btns.items():
            btn.setChecked(f == fmt)
        self._update_preview()

    def _generate(self) -> str:
        c = self._colors

        if self._format == "CSS":
            lines = [":root {"]
            for i, color in enumerate(c):
                lines.append(f"  --color-{i+1}: {color};")
            lines.append("}")
            return "\n".join(lines)

        elif self._format == "SCSS":
            lines = []
            for i, color in enumerate(c):
                lines.append(f"$color-{i+1}: {color};")
            lines.append("")
            lines.append("$palette: (")
            for i, color in enumerate(c):
                comma = "," if i < len(c) - 1 else ""
                lines.append(f'  "color-{i+1}": {color}{comma}')
            lines.append(");")
            return "\n".join(lines)

        elif self._format == "JSON":
            data = {
                "palette": {
                    "name": "导出配色",
                    "colors": [{"hex": col, "rgb": list(hex_to_rgb(col))} for col in c]
                }
            }
            return json.dumps(data, indent=2, ensure_ascii=False)

        elif self._format == "ASE":
            return f"ASE 格式 (Adobe Swatch Exchange)\n\n将保存为二进制 ASE 文件。\n包含颜色: {', '.join(c)}\n\n点击「保存到文件」选择保存路径。"

        return ""

    def _update_preview(self):
        self.preview.setPlainText(self._generate())

    def _copy(self):
        QApplication.clipboard().setText(self._generate())
        QMessageBox.information(self, "已复制", "代码已复制到剪贴板")

    def _save(self):
        if self._format == "JSON":
            path, _ = QFileDialog.getSaveFileName(self, "保存 JSON", "palette.json", "JSON (*.json)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._generate())
                QMessageBox.information(self, "成功", f"JSON 文件已保存:\n{path}")
        elif self._format in ("CSS", "SCSS"):
            ext = self._format.lower()
            path, _ = QFileDialog.getSaveFileName(self, f"保存 {self._format}", f"palette.{ext}", f"{self._format} (*.{ext})")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._generate())
                QMessageBox.information(self, "成功", f"{self._format} 文件已保存:\n{path}")
        elif self._format == "ASE":
            path, _ = QFileDialog.getSaveFileName(self, "保存 ASE", "palette.ase", "ASE (*.ase)")
            if path:
                self._save_ase(path)

    def _save_ase(self, filepath: str):
        colors = self._colors
        buf = io.BytesIO()
        buf.write(b"ASEF")
        buf.write(struct.pack(">HH", 1, 0))
        buf.write(struct.pack(">I", len(colors)))

        for i, hex_c in enumerate(colors):
            r, g, b = hex_to_rgb(hex_c)
            name = f"Color {i+1}"
            name_bytes = name.encode("utf-16-be") + b"\x00\x00"
            buf.write(struct.pack(">H", 0x0001))
            block_data = io.BytesIO()
            block_data.write(struct.pack(">H", len(name) + 1))
            block_data.write(name_bytes)
            block_data.write(b"RGB ")
            block_data.write(struct.pack(">fff", r / 255.0, g / 255.0, b / 255.0))
            block_data.write(struct.pack(">H", 0))
            block_content = block_data.getvalue()
            buf.write(struct.pack(">I", len(block_content)))
            buf.write(block_content)

        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        QMessageBox.information(self, "成功", f"ASE 文件已保存:\n{filepath}")


class ShareDialog(QDialog):
    def __init__(self, colors: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分享配色方案")
        self.setMinimumWidth(500)
        self.setStyleSheet(DIALOG_STYLE + """
            QPushButton#shareBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white; font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)

        strip = ColorStrip(colors, 50)
        layout.addWidget(strip)

        hex_str = "-".join(c.lstrip("#") for c in colors)

        urls = [
            ("Coolors.co", f"https://coolors.co/{hex_str}"),
            ("Adobe Color", f"https://color.adobe.com/zh/create/color-relationship?base={colors[0].lstrip('#')}"),
        ]

        for name, url in urls:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{name}</b>")
            lbl.setFixedWidth(100)
            url_edit = QLineEdit(url)
            url_edit.setReadOnly(True)
            copy_btn = QPushButton("复制")
            copy_btn.setObjectName("shareBtn")
            copy_btn.setFixedWidth(60)
            copy_btn.clicked.connect(lambda checked, u=url: QApplication.clipboard().setText(u))
            row.addWidget(lbl)
            row.addWidget(url_edit)
            row.addWidget(copy_btn)
            layout.addLayout(row)

        share_data = json.dumps({"colors": colors}, ensure_ascii=False)
        encoded = base64.urlsafe_b64encode(share_data.encode()).decode()
        layout.addWidget(QLabel("<b>Base64 分享码:</b>"))
        b64_edit = QLineEdit(encoded)
        b64_edit.setReadOnly(True)
        layout.addWidget(b64_edit)

        copy_b64 = QPushButton("📋 复制分享码")
        copy_b64.setObjectName("shareBtn")
        copy_b64.clicked.connect(lambda: (QApplication.clipboard().setText(encoded), QMessageBox.information(self, "已复制", "分享码已复制到剪贴板")))
        layout.addWidget(copy_b64)


# ─── 主窗口 ──────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 ColorPalette - 智能配色方案生成器")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        self._saved_palettes = self._load_saved()
        self._current_colors = []
        self._swatches = []

        self._setup_style()
        self._build_ui()
        self._update_status("就绪 — 欢迎使用 ColorPalette 智能配色方案生成器")

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0a0a0a;
            }
            QTabWidget::pane {
                border: 1px solid #222;
                background: #0a0a0a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #111122;
                color: #8888aa;
                border: 1px solid #222;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #1a1a2e;
                color: #667eea;
                border-bottom: 2px solid #667eea;
            }
            QTabBar::tab:hover {
                background: #161628;
                color: #aaaacc;
            }
            QScrollArea {
                border: none;
                background: #0a0a0a;
            }
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QFrame#card {
                background: #111122;
                border: 1px solid #1a1a2e;
                border-radius: 12px;
                padding: 16px;
            }
            QLabel { color: #c0c0d0; }
            QLabel#title {
                color: #e0e0f0;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#subtitle {
                color: #8888aa;
                font-size: 12px;
            }
            QPushButton#primary {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#primary:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7b93ee, stop:1 #8b5fbf);
            }
            QPushButton#primary:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #556dd9, stop:1 #653a91);
            }
            QPushButton#secondary {
                background: #1a1a2e;
                border: 1px solid #2a2a3e;
                border-radius: 8px;
                padding: 10px 20px;
                color: #c0c0d0;
                font-size: 13px;
            }
            QPushButton#secondary:hover {
                border-color: #667eea;
                color: #e0e0f0;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #1a1a2e;
                border: 1px solid #2a2a3e;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e0e0f0;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #1a1a2e;
                color: #e0e0f0;
                selection-background-color: #667eea;
                border: 1px solid #333;
            }
            QStatusBar {
                background: #0d0d1a;
                color: #666688;
                font-size: 12px;
            }
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 8)
        main_layout.setSpacing(12)

        # ─── Header ───
        header = QHBoxLayout()
        title = QLabel("🎨 ColorPalette")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0f0;")
        subtitle = QLabel("智能配色方案生成器")
        subtitle.setStyleSheet("font-size: 13px; color: #667eea; margin-left: 8px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()

        for text, tip, slot in [
            ("🔍 对比度", "无障碍对比度检查", self._show_contrast),
            ("💾 保存", "保存当前配色", self._save_palette),
            ("📤 导出", "导出配色方案", self._show_export),
            ("🔗 分享", "生成分享链接", self._show_share),
        ]:
            btn = QPushButton(text)
            btn.setToolTip(tip)
            btn.setObjectName("secondary")
            btn.clicked.connect(slot)
            header.addWidget(btn)

        main_layout.addLayout(header)

        # ─── Tabs ───
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_ai_tab(), "🤖 AI 配色")
        self.tabs.addTab(self._build_image_tab(), "🖼️ 图片提取")
        self.tabs.addTab(self._build_harmony_tab(), "🎯 色彩和谐")
        self.tabs.addTab(self._build_trend_tab(), "🔥 趋势配色")
        self.tabs.addTab(self._build_saved_tab(), "📁 我的收藏")
        main_layout.addWidget(self.tabs)

        # ─── Current palette ───
        self.palette_frame = QFrame()
        self.palette_frame.setObjectName("card")
        palette_layout = QVBoxLayout(self.palette_frame)
        palette_layout.setSpacing(10)

        pal_header = QHBoxLayout()
        pal_title = QLabel("当前配色方案")
        pal_title.setObjectName("title")
        pal_header.addWidget(pal_title)
        pal_header.addStretch()
        self.palette_name_label = QLabel("")
        self.palette_name_label.setObjectName("subtitle")
        pal_header.addWidget(self.palette_name_label)
        palette_layout.addLayout(pal_header)

        self.color_strip = ColorStrip([], 50)
        palette_layout.addWidget(self.color_strip)

        self.swatch_layout = QHBoxLayout()
        self.swatch_layout.setSpacing(8)
        self.swatch_container = QWidget()
        self.swatch_container.setLayout(self.swatch_layout)
        palette_layout.addWidget(self.swatch_container)

        act_row = QHBoxLayout()
        act_row.setSpacing(8)

        add_btn = QPushButton("➕ 添加颜色")
        add_btn.setObjectName("secondary")
        add_btn.clicked.connect(self._add_color)
        act_row.addWidget(add_btn)

        random_btn = QPushButton("🎲 随机配色")
        random_btn.setObjectName("secondary")
        random_btn.clicked.connect(self._random_palette)
        act_row.addWidget(random_btn)

        act_row.addStretch()

        self.color_count_label = QLabel("0 个颜色")
        self.color_count_label.setStyleSheet("color: #666688; font-size: 12px;")
        act_row.addWidget(self.color_count_label)

        palette_layout.addLayout(act_row)
        main_layout.addWidget(self.palette_frame)

        self.statusBar().showMessage("就绪")

    def _build_ai_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(self._lbl("输入关键词生成配色", True))
        card_layout.addWidget(self._lbl("选择预设关键词或输入自定义描述", False, True))

        input_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入关键词，如: 温暖、海洋、森林...")
        self.ai_input.returnPressed.connect(self._generate_ai_palette)
        input_row.addWidget(self.ai_input)

        generate_btn = QPushButton("✨ 生成配色")
        generate_btn.setObjectName("primary")
        generate_btn.clicked.connect(self._generate_ai_palette)
        input_row.addWidget(generate_btn)
        card_layout.addLayout(input_row)
        layout.addWidget(card)

        kw_card = QFrame()
        kw_card.setObjectName("card")
        kw_layout = QVBoxLayout(kw_card)
        kw_layout.addWidget(self._lbl("快速选择", True))

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, kw in enumerate(KEYWORD_PALETTES.keys()):
            btn = QPushButton(kw)
            btn.setObjectName("secondary")
            btn.clicked.connect(lambda checked, k=kw: self._apply_keyword(k))
            grid.addWidget(btn, i // 4, i % 4)
        kw_layout.addLayout(grid)
        layout.addWidget(kw_card)
        layout.addStretch()
        return widget

    def _build_image_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(self._lbl("从图片提取配色", True))
        card_layout.addWidget(self._lbl("上传图片，自动分析并提取主要颜色", False, True))

        if not PIL_AVAILABLE:
            warn = QLabel("⚠️ 需要安装 Pillow 库: pip install Pillow")
            warn.setStyleSheet("color: #e74c3c; font-size: 13px;")
            card_layout.addWidget(warn)

        btn_row = QHBoxLayout()
        upload_btn = QPushButton("📂 选择图片")
        upload_btn.setObjectName("primary")
        upload_btn.clicked.connect(self._upload_image)
        btn_row.addWidget(upload_btn)

        self.color_count_spin = QSpinBox()
        self.color_count_spin.setRange(3, 12)
        self.color_count_spin.setValue(6)
        self.color_count_spin.setPrefix("提取 ")
        self.color_count_spin.setSuffix(" 个颜色")
        btn_row.addWidget(self.color_count_spin)
        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        self.image_label = QLabel("支持 JPG、PNG、BMP、WebP 格式\n\n将图片拖拽到这里或点击上方按钮选择")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "color: #666688; padding: 40px; border: 2px dashed #333; border-radius: 10px; font-size: 14px;"
        )
        self.image_label.setMinimumHeight(200)
        card_layout.addWidget(self.image_label)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _build_harmony_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(self._lbl("色彩和谐生成", True))
        card_layout.addWidget(self._lbl("基于色彩理论生成和谐配色方案", False, True))

        color_row = QHBoxLayout()
        self.harmony_base = "#667eea"
        self.harmony_color_btn = QPushButton()
        self.harmony_color_btn.setFixedSize(50, 50)
        self.harmony_color_btn.setStyleSheet(
            f"background: {self.harmony_base}; border-radius: 8px; border: 2px solid #444;"
        )
        self.harmony_color_btn.clicked.connect(self._pick_harmony_color)
        color_row.addWidget(self.harmony_color_btn)

        self.harmony_hex = QLineEdit(self.harmony_base)
        self.harmony_hex.setFixedWidth(120)
        self.harmony_hex.textChanged.connect(self._update_harmony_preview)
        color_row.addWidget(self.harmony_hex)

        self.harmony_mode = QComboBox()
        self.harmony_mode.addItems(["互补色", "类似色", "三角色", "分裂互补", "四角色", "单色"])
        self.harmony_mode.currentTextChanged.connect(lambda: self._generate_harmony())
        color_row.addWidget(self.harmony_mode)

        gen_btn = QPushButton("🎯 生成")
        gen_btn.setObjectName("primary")
        gen_btn.clicked.connect(self._generate_harmony)
        color_row.addWidget(gen_btn)
        color_row.addStretch()
        card_layout.addLayout(color_row)

        self.harmony_strip = ColorStrip([], 60)
        card_layout.addWidget(self.harmony_strip)

        self.harmony_info = QLabel("选择基色和和谐类型，点击生成")
        self.harmony_info.setStyleSheet("color: #8888aa; font-size: 12px;")
        self.harmony_info.setWordWrap(True)
        card_layout.addWidget(self.harmony_info)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _build_trend_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(self._lbl("流行趋势配色", True))
        card_layout.addWidget(self._lbl("精选热门配色方案，一键应用", False, True))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        for name, data in TREND_PALETTES.items():
            trend_card = QFrame()
            trend_card.setStyleSheet("""
                QFrame {
                    background: #0d0d1a;
                    border: 1px solid #1a1a2e;
                    border-radius: 10px;
                    padding: 12px;
                }
                QFrame:hover { border-color: #667eea; }
            """)
            t_layout = QVBoxLayout(trend_card)

            name_row = QHBoxLayout()
            name_lbl = QLabel(f"<b>{name}</b>")
            name_lbl.setStyleSheet("color: #e0e0f0; font-size: 14px;")
            name_row.addWidget(name_lbl)
            name_row.addStretch()

            apply_btn = QPushButton("应用")
            apply_btn.setObjectName("primary")
            apply_btn.setFixedSize(60, 30)
            apply_btn.clicked.connect(lambda checked, n=name: self._apply_trend(n))
            name_row.addWidget(apply_btn)
            t_layout.addLayout(name_row)

            desc = QLabel(data["描述"])
            desc.setStyleSheet("color: #666688; font-size: 11px;")
            t_layout.addWidget(desc)

            strip = ColorStrip(data["主色"], 40)
            t_layout.addWidget(strip)

            scroll_layout.addWidget(trend_card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        card_layout.addWidget(scroll)

        layout.addWidget(card)
        return widget

    def _build_saved_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        header_row = QHBoxLayout()
        header_row.addWidget(self._lbl("我的收藏", True))
        header_row.addStretch()

        import_btn = QPushButton("📥 导入")
        import_btn.setObjectName("secondary")
        import_btn.clicked.connect(self._import_palette)
        header_row.addWidget(import_btn)
        card_layout.addLayout(header_row)

        self.saved_scroll = QScrollArea()
        self.saved_scroll.setWidgetResizable(True)
        self.saved_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.saved_widget = QWidget()
        self.saved_layout = QVBoxLayout(self.saved_widget)
        self.saved_layout.setSpacing(8)
        self.saved_scroll.setWidget(self.saved_widget)
        card_layout.addWidget(self.saved_scroll)

        layout.addWidget(card)
        self._refresh_saved_list()
        return widget

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _lbl(self, text: str, title=False, subtitle=False) -> QLabel:
        lbl = QLabel(text)
        if title:
            lbl.setObjectName("title")
        elif subtitle:
            lbl.setObjectName("subtitle")
        return lbl

    def _update_status(self, msg: str):
        self.statusBar().showMessage(msg)

    # ─── Palette management ──────────────────────────────────────────────

    def set_palette(self, colors: list, name: str = ""):
        self._current_colors = list(colors)
        self.color_strip.colors = colors

        while self.swatch_layout.count():
            item = self.swatch_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._swatches.clear()
        for i, c in enumerate(colors):
            swatch = ColorSwatch(c, f"#{i+1}")
            swatch.clicked.connect(lambda hex_c: self._update_status(f"已复制 {hex_c}"))
            swatch.colorChanged.connect(self._on_swatch_color_changed)
            self.swatch_layout.addWidget(swatch)
            self._swatches.append(swatch)

        self.swatch_layout.addStretch()
        self.palette_name_label.setText(name)
        self.color_count_label.setText(f"{len(colors)} 个颜色")
        self._update_status(f"已设置配色: {len(colors)} 个颜色")

    def _on_swatch_color_changed(self, old_color: str, new_color: str):
        for i, swatch in enumerate(self._swatches):
            if swatch.hex_color == new_color:
                self._current_colors[i] = new_color
                break
        self.color_strip.colors = self._current_colors
        self._update_status(f"颜色已修改: {old_color} → {new_color}")

    def _add_color(self):
        color = QColorDialog.getColor(QColor("#667eea"), self, "选择颜色")
        if color.isValid():
            self._current_colors.append(color.name().upper())
            self.set_palette(self._current_colors)

    def _random_palette(self):
        base_h = random.random()
        colors = []
        for i in range(5):
            h = (base_h + i * 0.15 + random.uniform(-0.05, 0.05)) % 1.0
            s = random.uniform(0.5, 0.9)
            l = random.uniform(0.3, 0.7)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            colors.append(rgb_to_hex(int(r*255), int(g*255), int(b*255)))
        self.set_palette(colors, "随机配色")

    # ─── AI Palette ──────────────────────────────────────────────────────

    def _generate_ai_palette(self):
        text = self.ai_input.text().strip()
        if not text:
            self._update_status("请输入关键词")
            return
        self._apply_keyword(text)

    def _apply_keyword(self, keyword: str):
        if keyword in KEYWORD_PALETTES:
            self.set_palette(KEYWORD_PALETTES[keyword], f"AI 配色 - {keyword}")
        else:
            h = hashlib.md5(keyword.encode()).hexdigest()
            colors = []
            for i in range(5):
                idx1 = (i * 2) % len(h)
                idx2 = (i * 2 + 2) % len(h)
                seed = int(h[idx1:idx1+2], 16) / 255.0
                hue = (seed + i * 0.2) % 1.0
                idx3 = ((i + 5) * 2) % len(h)
                idx4 = idx3 + 2
                sat = 0.5 + (int(h[idx3:idx4] if idx4 <= len(h) else h[:2], 16) / 255.0) * 0.4
                idx5 = ((i + 10) * 2) % len(h)
                idx6 = idx5 + 2
                light = 0.35 + (int(h[idx5:idx6] if idx6 <= len(h) else h[2:4], 16) / 255.0) * 0.35
                r, g, b = colorsys.hls_to_rgb(hue, light, sat)
                colors.append(rgb_to_hex(int(r*255), int(g*255), int(b*255)))
            self.set_palette(colors, f"AI 配色 - {keyword}")

    # ─── Image extraction ────────────────────────────────────────────────

    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;所有文件 (*.*)"
        )
        if not path:
            return

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setStyleSheet("border: 2px solid #333; border-radius: 10px; padding: 10px;")

        num = self.color_count_spin.value()
        colors = extract_colors_from_image(path, num)
        self.set_palette(colors, f"图片提取 - {Path(path).name}")
        self._update_status(f"已从图片提取 {len(colors)} 个颜色")

    # ─── Color Harmony ───────────────────────────────────────────────────

    def _pick_harmony_color(self):
        color = QColorDialog.getColor(QColor(self.harmony_base), self, "选择基色")
        if color.isValid():
            self.harmony_base = color.name().upper()
            self.harmony_hex.setText(self.harmony_base)
            self.harmony_color_btn.setStyleSheet(
                f"background: {self.harmony_base}; border-radius: 8px; border: 2px solid #444;"
            )

    def _update_harmony_preview(self, text: str):
        if len(text) == 7 and text.startswith("#"):
            try:
                QColor(text)
                self.harmony_base = text.upper()
                self.harmony_color_btn.setStyleSheet(
                    f"background: {self.harmony_base}; border-radius: 8px; border: 2px solid #444;"
                )
            except Exception:
                pass

    def _generate_harmony(self):
        mode = self.harmony_mode.currentText()
        colors = generate_harmony(self.harmony_base, mode)
        self.harmony_strip.colors = colors
        self.harmony_info.setText(f"{mode}: {' → '.join(colors)}")
        self.set_palette(colors, f"色彩和谐 - {mode}")

    # ─── Trend Palettes ──────────────────────────────────────────────────

    def _apply_trend(self, name: str):
        if name in TREND_PALETTES:
            self.set_palette(TREND_PALETTES[name]["主色"], f"趋势 - {name}")

    # ─── Save / Load ─────────────────────────────────────────────────────

    def _save_path(self) -> str:
        p = Path.home() / ".colorpalette" / "palettes.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)

    def _load_saved(self) -> list:
        path = self._save_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _persist_saved(self):
        with open(self._save_path(), "w", encoding="utf-8") as f:
            json.dump(self._saved_palettes, f, ensure_ascii=False, indent=2)

    def _save_palette(self):
        if not self._current_colors:
            QMessageBox.information(self, "提示", "当前没有配色方案，请先生成一个。")
            return

        dlg = SavePaletteDialog(self._current_colors, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            entry = {
                "name": data["name"],
                "tag": data["tag"],
                "colors": list(self._current_colors),
                "created": datetime.datetime.now().isoformat()
            }
            self._saved_palettes.append(entry)
            self._persist_saved()
            self._refresh_saved_list()
            self._update_status(f"已保存: {data['name']}")

    def _refresh_saved_list(self):
        while self.saved_layout.count():
            item = self.saved_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._saved_palettes:
            empty = QLabel("还没有收藏的配色方案。\n生成配色后点击「保存」按钮收藏。")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #666688; padding: 40px;")
            self.saved_layout.addWidget(empty)
            self.saved_layout.addStretch()
            return

        for idx, pal in enumerate(reversed(self._saved_palettes)):
            real_idx = len(self._saved_palettes) - 1 - idx
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0d0d1a;
                    border: 1px solid #1a1a2e;
                    border-radius: 10px;
                    padding: 10px;
                }
                QFrame:hover { border-color: #667eea; }
            """)
            c_layout = QVBoxLayout(card)

            row = QHBoxLayout()
            name_lbl = QLabel(f"<b>{pal['name']}</b>")
            name_lbl.setStyleSheet("color: #e0e0f0; font-size: 13px;")
            row.addWidget(name_lbl)

            tag_lbl = QLabel(f"[{pal.get('tag', '默认')}]")
            tag_lbl.setStyleSheet("color: #667eea; font-size: 11px;")
            row.addWidget(tag_lbl)
            row.addStretch()

            load_btn = QPushButton("加载")
            load_btn.setObjectName("primary")
            load_btn.setFixedSize(50, 28)
            load_btn.clicked.connect(lambda checked, i=real_idx: self._load_saved_palette(i))
            row.addWidget(load_btn)

            del_btn = QPushButton("删除")
            del_btn.setFixedSize(50, 28)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a2e; border: 1px solid #2a2a3e;
                    border-radius: 6px; padding: 4px; color: #e74c3c; font-size: 11px;
                }
                QPushButton:hover { border-color: #e74c3c; }
            """)
            del_btn.clicked.connect(lambda checked, i=real_idx: self._delete_saved(i))
            row.addWidget(del_btn)
            c_layout.addLayout(row)

            strip = ColorStrip(pal["colors"], 35)
            c_layout.addWidget(strip)

            date_lbl = QLabel(pal.get("created", "")[:16].replace("T", " "))
            date_lbl.setStyleSheet("color: #555; font-size: 10px;")
            c_layout.addWidget(date_lbl)

            self.saved_layout.addWidget(card)

        self.saved_layout.addStretch()

    def _load_saved_palette(self, idx: int):
        pal = self._saved_palettes[idx]
        self.set_palette(pal["colors"], pal["name"])
        self.tabs.setCurrentIndex(0)

    def _delete_saved(self, idx: int):
        name = self._saved_palettes[idx]["name"]
        reply = QMessageBox.question(self, "确认删除", f"确定要删除「{name}」吗？")
        if reply == QMessageBox.StandardButton.Yes:
            del self._saved_palettes[idx]
            self._persist_saved()
            self._refresh_saved_list()
            self._update_status(f"已删除: {name}")

    def _import_palette(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配色", "", "JSON (*.json);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "colors" in data:
                colors = data["colors"]
            elif isinstance(data, list):
                colors = data
            else:
                raise ValueError("格式不支持")
            self.set_palette(colors, f"导入 - {Path(path).name}")
            self._update_status("配色方案已导入")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法导入文件:\n{e}")

    # ─── Export / Share / Contrast ────────────────────────────────────────

    def _show_export(self):
        if not self._current_colors:
            QMessageBox.information(self, "提示", "当前没有配色方案。")
            return
        dlg = ExportDialog(self._current_colors, self)
        dlg.exec()

    def _show_share(self):
        if not self._current_colors:
            QMessageBox.information(self, "提示", "当前没有配色方案。")
            return
        dlg = ShareDialog(self._current_colors, self)
        dlg.exec()

    def _show_contrast(self):
        dlg = ContrastDialog(self)
        dlg.exec()


# ─── 入口 ────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
