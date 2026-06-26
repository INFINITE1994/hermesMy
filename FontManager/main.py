#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FontManager - 专业字体管理工具
功能：字体浏览、预览、比较、搜索、分类、导出
"""

import sys
import csv
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QSlider, QComboBox,
    QScrollArea, QFrame, QGridLayout, QTextEdit, QFileDialog,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem, QGroupBox,
    QSpinBox, QCheckBox, QSizePolicy, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QFont, QFontDatabase, QColor, QPalette, QLinearGradient,
    QPainter, QBrush, QPen, QIcon, QPixmap, QConicalGradient
)


# ==================== 主题样式 ====================
DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QTabWidget::pane {
    border: 1px solid #333355;
    background-color: #0a0a0a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #111122;
    color: #a0a0c0;
    padding: 10px 20px;
    margin: 2px;
    border-radius: 6px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover:!selected {
    background-color: #1a1a33;
}

QListWidget {
    background-color: #111122;
    border: 1px solid #333355;
    border-radius: 8px;
    padding: 5px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QListWidget::item:hover {
    background-color: #1a1a33;
}

QLineEdit {
    background-color: #111122;
    border: 2px solid #333355;
    border-radius: 8px;
    padding: 10px 15px;
    color: #e0e0e0;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #667eea;
}

QLineEdit::placeholder {
    color: #555577;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b92ff, stop:1 #8b5fc7);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #556eea, stop:1 #653ba2);
}

QPushButton:disabled {
    background-color: #333355;
    color: #666688;
}

QComboBox {
    background-color: #111122;
    border: 2px solid #333355;
    border-radius: 8px;
    padding: 8px 15px;
    color: #e0e0e0;
    font-size: 13px;
}

QComboBox:focus {
    border: 2px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #667eea;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #111122;
    border: 1px solid #333355;
    color: #e0e0e0;
    selection-background-color: #667eea;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #333355;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 3px;
}

QTextEdit {
    background-color: #111122;
    border: 2px solid #333355;
    border-radius: 8px;
    padding: 10px;
    color: #e0e0e0;
    font-size: 14px;
}

QTextEdit:focus {
    border: 2px solid #667eea;
}

QScrollArea {
    border: none;
    background-color: #0a0a0a;
}

QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #333355;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0a0a0a;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #333355;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #667eea;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #333355;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
    font-weight: bold;
    color: #a0a0c0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border-radius: 4px;
}

QLabel {
    color: #a0a0c0;
}

QSpinBox {
    background-color: #111122;
    border: 2px solid #333355;
    border-radius: 8px;
    padding: 8px;
    color: #e0e0e0;
}

QSpinBox:focus {
    border: 2px solid #667eea;
}

QCheckBox {
    spacing: 8px;
    color: #a0a0c0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #333355;
    background-color: #111122;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border: none;
}

QSplitter::handle {
    background-color: #333355;
    width: 3px;
}

QSplitter::handle:hover {
    background-color: #667eea;
}

QMessageBox {
    background-color: #111122;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QFileDialog {
    background-color: #111122;
}
"""


# ==================== 自定义组件 ====================
class FontCard(QFrame):
    """字体卡片组件"""

    clicked = pyqtSignal(str)

    def __init__(self, font_name: str, parent=None):
        super().__init__(parent)
        self.font_name = font_name
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border: 1px solid #333355;
                border-radius: 10px;
                padding: 15px;
            }
            QFrame:hover {
                border: 2px solid #667eea;
                background-color: #151530;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 字体名称
        name_label = QLabel(self.font_name)
        name_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(name_label)

        # 字体预览
        preview_label = QLabel("AaBbCcDd 1234567890")
        font = QFont(self.font_name, 24)
        preview_label.setFont(font)
        preview_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                background: transparent;
                border: none;
                padding: 10px 0;
            }
        """)
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)

        # 中文预览
        cn_preview = QLabel("字体预览示例 永字八法")
        cn_font = QFont(self.font_name, 18)
        cn_preview.setFont(cn_font)
        cn_preview.setStyleSheet("""
            QLabel {
                color: #a0a0c0;
                background: transparent;
                border: none;
                padding: 5px 0;
            }
        """)
        layout.addWidget(cn_preview)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(150)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.font_name)
        super().mousePressEvent(event)


class GradientWidget(QWidget):
    """渐变背景组件"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 渐变背景
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(102, 126, 234, 30))
        gradient.setColorAt(1, QColor(118, 75, 162, 30))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)


# ==================== 字体浏览器标签页 ====================
class FontBrowserTab(QWidget):
    """字体浏览器"""

    font_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_fonts = []
        self.setup_ui()
        self.load_fonts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 搜索栏
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索字体名称...")
        self.search_input.textChanged.connect(self.filter_fonts)
        search_layout.addWidget(self.search_input)

        self.clear_btn = QPushButton("清除")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_btn)

        layout.addLayout(search_layout)

        # 字体计数
        self.count_label = QLabel("加载中...")
        self.count_label.setStyleSheet("color: #667eea; font-size: 12px;")
        layout.addWidget(self.count_label)

        # 字体列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.font_container = QWidget()
        self.font_grid = QGridLayout(self.font_container)
        self.font_grid.setSpacing(15)
        self.font_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.font_container)
        layout.addWidget(self.scroll_area)

    def load_fonts(self):
        """加载系统字体"""
        font_db = QFontDatabase
        self.all_fonts = font_db.families()

        # 过滤掉一些特殊字体
        self.all_fonts = [f for f in self.all_fonts if not f.startswith('@')]

        self.display_fonts(self.all_fonts)
        self.count_label.setText(f"共找到 {len(self.all_fonts)} 个字体")

    def display_fonts(self, fonts):
        """显示字体列表"""
        # 清空现有内容
        while self.font_grid.count():
            item = self.font_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 限制显示数量以提高性能
        display_fonts = fonts[:200]

        cols = 2
        for i, font_name in enumerate(display_fonts):
            row = i // cols
            col = i % cols

            card = FontCard(font_name)
            card.clicked.connect(self.on_font_clicked)
            self.font_grid.addWidget(card, row, col)

        if len(fonts) > 200:
            more_label = QLabel(f"还有 {len(fonts) - 200} 个字体未显示，请使用搜索功能")
            more_label.setStyleSheet("color: #667eea; font-size: 14px; padding: 20px;")
            more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.font_grid.addWidget(more_label, (len(display_fonts) // cols) + 1, 0, 1, cols)

    def filter_fonts(self, text):
        """过滤字体"""
        if not text:
            self.display_fonts(self.all_fonts)
            self.count_label.setText(f"共找到 {len(self.all_fonts)} 个字体")
            return

        filtered = [f for f in self.all_fonts if text.lower() in f.lower()]
        self.display_fonts(filtered)
        self.count_label.setText(f"找到 {len(filtered)} 个匹配字体")

    def clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.display_fonts(self.all_fonts)
        self.count_label.setText(f"共找到 {len(self.all_fonts)} 个字体")

    def on_font_clicked(self, font_name):
        """字体点击事件"""
        self.font_selected.emit(font_name)


# ==================== 字体预览标签页 ====================
class FontPreviewTab(QWidget):
    """字体预览"""

    def __init__(self, font_list, parent=None):
        super().__init__(parent)
        self.font_list = font_list
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("字体预览")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                -webkit-background-clip: text;
                color: white;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 控制区域
        control_group = QGroupBox("预览设置")
        control_layout = QGridLayout()

        # 字体选择
        control_layout.addWidget(QLabel("选择字体:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.font_list)
        self.font_combo.currentTextChanged.connect(self.update_preview)
        control_layout.addWidget(self.font_combo, 0, 1)

        # 字体大小
        control_layout.addWidget(QLabel("字体大小:"), 1, 0)
        size_layout = QHBoxLayout()
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(12, 120)
        self.size_slider.setValue(36)
        self.size_slider.valueChanged.connect(self.update_preview)
        size_layout.addWidget(self.size_slider)

        self.size_label = QLabel("36pt")
        self.size_label.setFixedWidth(50)
        self.size_label.setStyleSheet("color: #667eea; font-weight: bold;")
        size_layout.addWidget(self.size_label)
        control_layout.addLayout(size_layout, 1, 1)

        # 自定义文本
        control_layout.addWidget(QLabel("预览文本:"), 2, 0)
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入自定义预览文本...")
        self.text_input.setText("The quick brown fox jumps over the lazy dog\n敏捷的棕色狐狸跳过了懒狗\nAaBbCcDdEeFf 0123456789")
        self.text_input.textChanged.connect(self.update_preview)
        control_layout.addWidget(self.text_input, 2, 1)

        # 预设文本
        control_layout.addWidget(QLabel("预设文本:"), 3, 0)
        preset_layout = QHBoxLayout()
        presets = [
            ("英文句子", "The quick brown fox jumps over the lazy dog"),
            ("中文句子", "永字八法 书法艺术 汉字之美"),
            ("数字符号", "0123456789 !@#$%^&*()"),
            (" pangram", "ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz"),
        ]
        for name, text in presets:
            btn = QPushButton(name)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, t=text: self.text_input.setText(t))
            preset_layout.addWidget(btn)
        control_layout.addLayout(preset_layout, 3, 1)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 预览区域
        preview_group = QGroupBox("预览效果")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #111122;
                border: 2px solid #333355;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # 初始预览
        self.update_preview()

    def update_preview(self):
        """更新预览"""
        font_name = self.font_combo.currentText()
        size = self.size_slider.value()
        text = self.text_input.text()

        self.size_label.setText(f"{size}pt")

        if not text:
            text = "The quick brown fox jumps over the lazy dog\n敏捷的棕色狐狸跳过了懒狗"

        font = QFont(font_name, size)
        self.preview_label.setFont(font)
        self.preview_label.setText(text)


# ==================== 字体比较标签页 ====================
class FontCompareTab(QWidget):
    """字体比较"""

    def __init__(self, font_list, parent=None):
        super().__init__(parent)
        self.font_list = font_list
        self.compare_items = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("字体比较")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 控制区域
        control_group = QGroupBox("比较设置")
        control_layout = QVBoxLayout()

        # 字体选择行
        font_select_layout = QHBoxLayout()
        font_select_layout.addWidget(QLabel("选择字体:"))

        self.compare_combo = QComboBox()
        self.compare_combo.addItems(self.font_list)
        font_select_layout.addWidget(self.compare_combo)

        self.add_btn = QPushButton("➕ 添加到比较")
        self.add_btn.setFixedWidth(120)
        self.add_btn.clicked.connect(self.add_to_compare)
        font_select_layout.addWidget(self.add_btn)

        self.clear_compare_btn = QPushButton("🗑️ 清空比较")
        self.clear_compare_btn.setFixedWidth(120)
        self.clear_compare_btn.clicked.connect(self.clear_compare)
        font_select_layout.addWidget(self.clear_compare_btn)

        control_layout.addLayout(font_select_layout)

        # 比较文本
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("比较文本:"))
        self.compare_text = QLineEdit()
        self.compare_text.setText("The quick brown fox jumps over the lazy dog\n敏捷的棕色狐狸跳过了懒狗\nAaBbCcDd 0123456789")
        self.compare_text.textChanged.connect(self.update_all_previews)
        text_layout.addWidget(self.compare_text)
        control_layout.addLayout(text_layout)

        # 字体大小
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字体大小:"))
        self.compare_size = QSlider(Qt.Orientation.Horizontal)
        self.compare_size.setRange(12, 72)
        self.compare_size.setValue(24)
        self.compare_size.valueChanged.connect(self.update_all_previews)
        size_layout.addWidget(self.compare_size)
        self.compare_size_label = QLabel("24pt")
        self.compare_size_label.setFixedWidth(50)
        self.compare_size_label.setStyleSheet("color: #667eea; font-weight: bold;")
        size_layout.addWidget(self.compare_size_label)
        control_layout.addLayout(size_layout)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 比较结果区域
        self.compare_scroll = QScrollArea()
        self.compare_scroll.setWidgetResizable(True)
        self.compare_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.compare_container = QWidget()
        self.compare_layout = QVBoxLayout(self.compare_container)
        self.compare_layout.setSpacing(15)

        self.compare_scroll.setWidget(self.compare_container)
        layout.addWidget(self.compare_scroll)

        # 提示
        self.hint_label = QLabel("请添加字体到比较列表")
        self.hint_label.setStyleSheet("color: #555577; font-size: 16px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_layout.addWidget(self.hint_label)

    def add_to_compare(self):
        """添加字体到比较"""
        font_name = self.compare_combo.currentText()
        if not font_name:
            return

        # 检查是否已添加
        if font_name in self.compare_items:
            QMessageBox.information(self, "提示", f"字体 '{font_name}' 已在比较列表中")
            return

        self.compare_items.append(font_name)

        # 隐藏提示
        if self.hint_label.isVisible():
            self.hint_label.hide()

        # 添加预览卡片
        self.add_compare_card(font_name)

    def add_compare_card(self, font_name):
        """添加比较卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border: 1px solid #333355;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        card_layout = QVBoxLayout(card)

        # 字体名称和删除按钮
        header_layout = QHBoxLayout()
        name_label = QLabel(font_name)
        name_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(name_label)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_compare_item(font_name, card))
        header_layout.addWidget(remove_btn)

        card_layout.addLayout(header_layout)

        # 预览文本
        preview = QLabel()
        preview.setWordWrap(True)
        preview.setStyleSheet("color: #e0e0e0; padding: 10px 0;")
        card_layout.addWidget(preview)

        # 保存引用以便更新
        card.setProperty("font_name", font_name)
        card.setProperty("preview_label", preview)

        self.compare_layout.addWidget(card)
        self.update_preview_card(card)

    def remove_compare_item(self, font_name, card):
        """移除比较项"""
        if font_name in self.compare_items:
            self.compare_items.remove(font_name)

        self.compare_layout.removeWidget(card)
        card.deleteLater()

        if not self.compare_items:
            self.hint_label.show()

    def clear_compare(self):
        """清空比较"""
        self.compare_items.clear()

        # 清空所有卡片
        while self.compare_layout.count():
            item = self.compare_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.hint_label.show()

    def update_preview_card(self, card):
        """更新单个预览卡片"""
        font_name = card.property("font_name")
        preview_label = card.property("preview_label")

        if not font_name or not preview_label:
            return

        size = self.compare_size.value()
        text = self.compare_text.text()

        self.compare_size_label.setText(f"{size}pt")

        if not text:
            text = "The quick brown fox jumps over the lazy dog\n敏捷的棕色狐狸跳过了懒狗"

        font = QFont(font_name, size)
        preview_label.setFont(font)
        preview_label.setText(text)

    def update_all_previews(self):
        """更新所有预览"""
        size = self.compare_size.value()
        self.compare_size_label.setText(f"{size}pt")

        for i in range(self.compare_layout.count()):
            item = self.compare_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                if card.property("font_name"):
                    self.update_preview_card(card)


# ==================== 字体分类标签页 ====================
class FontCategoryTab(QWidget):
    """字体分类"""

    def __init__(self, font_list, parent=None):
        super().__init__(parent)
        self.font_list = font_list
        self.setup_ui()
        self.categorize_fonts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("字体分类")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 分类选择
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("分类筛选:"))

        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "衬线字体", "无衬线字体", "等宽字体", "手写/装饰字体"])
        self.category_combo.currentTextChanged.connect(self.filter_by_category)
        filter_layout.addWidget(self.category_combo)

        self.category_count = QLabel("")
        self.category_count.setStyleSheet("color: #667eea;")
        filter_layout.addWidget(self.category_count)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 字体列表
        self.category_list = QListWidget()
        self.category_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #222244;
            }
        """)
        layout.addWidget(self.category_list)

    def categorize_fonts(self):
        """对字体进行分类"""
        self.categories = {
            "衬线字体": [],
            "无衬线字体": [],
            "等宽字体": [],
            "手写/装饰字体": []
        }

        # 简单的分类规则（基于常见字体名称）
        serif_keywords = ["serif", "times", "georgia", "palatino", "garamond", "book", "roman"]
        sans_keywords = ["sans", "arial", "helvetica", "calibri", "verdana", "tahoma", "segoe", "roboto", "open sans"]
        mono_keywords = ["mono", "courier", "consolas", "lucida console", "source code", "fira code", "fixedsys"]
        script_keywords = ["script", "cursive", "brush", "handwriting", "comic", "dancing", "pacifico", "lobster"]

        for font in self.font_list:
            font_lower = font.lower()

            if any(kw in font_lower for kw in mono_keywords):
                self.categories["等宽字体"].append(font)
            elif any(kw in font_lower for kw in script_keywords):
                self.categories["手写/装饰字体"].append(font)
            elif any(kw in font_lower for kw in serif_keywords):
                self.categories["衬线字体"].append(font)
            elif any(kw in font_lower for kw in sans_keywords):
                self.categories["无衬线字体"].append(font)
            else:
                # 默认归类为无衬线
                self.categories["无衬线字体"].append(font)

        self.filter_by_category("全部")

    def filter_by_category(self, category):
        """按分类筛选"""
        self.category_list.clear()

        if category == "全部":
            fonts = self.font_list
        else:
            fonts = self.categories.get(category, [])

        self.category_list.addItems(fonts)
        self.category_count.setText(f"共 {len(fonts)} 个字体")


# ==================== 字体信息标签页 ====================
class FontInfoTab(QWidget):
    """字体信息"""

    def __init__(self, font_list, parent=None):
        super().__init__(parent)
        self.font_list = font_list
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("字体信息")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 字体选择
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("选择字体:"))

        self.info_combo = QComboBox()
        self.info_combo.addItems(self.font_list)
        self.info_combo.currentTextChanged.connect(self.show_font_info)
        select_layout.addWidget(self.info_combo)

        layout.addLayout(select_layout)

        # 信息显示区域
        self.info_group = QGroupBox("字体详细信息")
        info_layout = QGridLayout()
        info_layout.setSpacing(15)

        # 信息字段
        self.info_labels = {}
        fields = [
            ("字体族名称", "family"),
            ("字体样式", "style"),
            ("字体大小", "size"),
            ("字体类型", "type"),
            ("是否等宽", "monospace"),
            ("支持中文", "chinese"),
            ("字符数量", "chars"),
        ]

        for i, (label, key) in enumerate(fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #a0a0c0; font-size: 13px;")
            info_layout.addWidget(lbl, i, 0)

            value = QLabel("--")
            value.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: bold;")
            info_layout.addWidget(value, i, 1)
            self.info_labels[key] = value

        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)

        # 字体预览
        preview_group = QGroupBox("字体预览")
        preview_layout = QVBoxLayout()

        self.info_preview = QLabel("AaBbCcDdEeFf\n0123456789\n字体预览示例")
        self.info_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_preview.setMinimumHeight(200)
        self.info_preview.setStyleSheet("""
            QLabel {
                background-color: #111122;
                border: 2px solid #333355;
                border-radius: 12px;
                padding: 20px;
                font-size: 36px;
            }
        """)
        preview_layout.addWidget(self.info_preview)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # 初始显示
        if self.font_list:
            self.show_font_info(self.font_list[0])

    def show_font_info(self, font_name):
        """显示字体信息"""
        if not font_name:
            return

        # 更新信息
        self.info_labels["family"].setText(font_name)

        # 检测字体特征
        font = QFont(font_name)

        # 检测是否等宽
        is_mono = QFontDatabase.isFixedPitch(font_name)
        self.info_labels["monospace"].setText("是" if is_mono else "否")

        # 检测是否支持中文（基于字体名称关键词判断）
        has_chinese = any(kw in font_name.lower() for kw in [
            "simsun", "simhei", "microsoft yahei", "nsimsun", "kaiti",
            "fangsong", "youyuan", "stzhongs", "stxingkai", "stliti",
            "dengxian", "source han", "noto", "wenquanyi", "wqy",
            "cjk", "chinese", "song", "hei", "kai", "ming",
            "yahei", "micro", "deng", "fang"
        ])
        self.info_labels["chinese"].setText("支持" if has_chinese else "可能不支持")

        # 字体样式
        style = QFontDatabase.styleString(font)
        self.info_labels["style"].setText(style)

        # 默认大小
        self.info_labels["size"].setText("可变")

        # 字体类型
        if is_mono:
            font_type = "等宽字体"
        elif "serif" in font_name.lower():
            font_type = "衬线字体"
        elif "sans" in font_name.lower():
            font_type = "无衬线字体"
        else:
            font_type = "其他"
        self.info_labels["type"].setText(font_type)

        # 字符数量（估算）
        self.info_labels["chars"].setText("Unicode 支持")

        # 更新预览
        preview_font = QFont(font_name, 36)
        self.info_preview.setFont(preview_font)


# ==================== 字体导出功能 ====================
class FontExporter:
    """字体导出器"""

    @staticmethod
    def export_to_csv(font_list, file_path):
        """导出为CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['字体名称', '是否等宽', '分类'])
                for font in font_list:
                    is_mono = QFontDatabase.isFixedPitch(font)
                    category = "等宽" if is_mono else "比例"
                    writer.writerow([font, "是" if is_mono else "否", category])
            return True
        except Exception as e:
            return str(e)

    @staticmethod
    def export_to_txt(font_list, file_path):
        """导出为TXT"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("FontManager - 字体列表导出\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"导出时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"字体总数: {len(font_list)}\n\n")
                f.write("-" * 60 + "\n")
                for i, font in enumerate(font_list, 1):
                    f.write(f"{i:4d}. {font}\n")
                f.write("-" * 60 + "\n")
            return True
        except Exception as e:
            return str(e)


# ==================== 主窗口 ====================
class FontManagerWindow(QMainWindow):
    """字体管理器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FontManager - 专业字体管理工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 获取字体列表
        self.font_list = self.get_system_fonts()

        self.setup_ui()
        self.setup_menu()

    def get_system_fonts(self):
        """获取系统字体列表"""
        font_db = QFontDatabase
        fonts = font_db.families()
        # 过滤掉特殊字体
        return [f for f in fonts if not f.startswith('@')]

    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题栏
        header = GradientWidget()
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        # Logo和标题
        logo_layout = QHBoxLayout()
        logo_label = QLabel("🔤")
        logo_label.setStyleSheet("font-size: 32px; background: transparent;")
        logo_layout.addWidget(logo_label)

        title_text = QVBoxLayout()
        title = QLabel("FontManager")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        title_text.addWidget(title)

        subtitle = QLabel("专业字体管理工具")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #a0a0c0;
                background: transparent;
            }
        """)
        title_text.addWidget(subtitle)
        logo_layout.addLayout(title_text)

        header_layout.addLayout(logo_layout)
        header_layout.addStretch()

        # 字体数量信息
        self.font_count_label = QLabel(f"系统字体: {len(self.font_list)} 个")
        self.font_count_label.setStyleSheet("""
            QLabel {
                color: #a0a0c0;
                font-size: 14px;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.font_count_label)

        main_layout.addWidget(header)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 创建标签页
        self.browser_tab = FontBrowserTab()
        self.preview_tab = FontPreviewTab(self.font_list)
        self.compare_tab = FontCompareTab(self.font_list)
        self.category_tab = FontCategoryTab(self.font_list)
        self.info_tab = FontInfoTab(self.font_list)

        # 连接信号
        self.browser_tab.font_selected.connect(self.on_font_selected)

        # 添加标签页
        self.tab_widget.addTab(self.browser_tab, "📚 字体浏览")
        self.tab_widget.addTab(self.preview_tab, "👁️ 字体预览")
        self.tab_widget.addTab(self.compare_tab, "⚖️ 字体比较")
        self.tab_widget.addTab(self.category_tab, "📂 字体分类")
        self.tab_widget.addTab(self.info_tab, "ℹ️ 字体信息")

        main_layout.addWidget(self.tab_widget)

        # 底部状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #111122;
                color: #a0a0c0;
                border-top: 1px solid #333355;
                padding: 5px;
            }
        """)
        self.statusBar().showMessage("就绪")

    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #111122;
                color: #a0a0c0;
                border-bottom: 1px solid #333355;
            }
            QMenuBar::item:selected {
                background-color: #667eea;
                color: white;
            }
            QMenu {
                background-color: #111122;
                color: #e0e0e0;
                border: 1px solid #333355;
            }
            QMenu::item:selected {
                background-color: #667eea;
            }
        """)

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        export_csv_action = file_menu.addAction("导出为 CSV")
        export_csv_action.triggered.connect(self.export_csv)

        export_txt_action = file_menu.addAction("导出为 TXT")
        export_txt_action.triggered.connect(self.export_txt)

        file_menu.addSeparator()

        refresh_action = file_menu.addAction("刷新字体列表")
        refresh_action.triggered.connect(self.refresh_fonts)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def on_font_selected(self, font_name):
        """字体选中事件"""
        # 切换到预览标签页
        self.tab_widget.setCurrentIndex(1)

        # 设置预览字体
        index = self.preview_tab.font_combo.findText(font_name)
        if index >= 0:
            self.preview_tab.font_combo.setCurrentIndex(index)

        self.statusBar().showMessage(f"已选择字体: {font_name}")

    def export_csv(self):
        """导出CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出字体列表", "font_list.csv", "CSV 文件 (*.csv)"
        )
        if file_path:
            result = FontExporter.export_to_csv(self.font_list, file_path)
            if result is True:
                QMessageBox.information(self, "成功", f"字体列表已导出到:\n{file_path}")
                self.statusBar().showMessage(f"已导出: {file_path}")
            else:
                QMessageBox.critical(self, "错误", f"导出失败:\n{result}")

    def export_txt(self):
        """导出TXT"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出字体列表", "font_list.txt", "文本文件 (*.txt)"
        )
        if file_path:
            result = FontExporter.export_to_txt(self.font_list, file_path)
            if result is True:
                QMessageBox.information(self, "成功", f"字体列表已导出到:\n{file_path}")
                self.statusBar().showMessage(f"已导出: {file_path}")
            else:
                QMessageBox.critical(self, "错误", f"导出失败:\n{result}")

    def refresh_fonts(self):
        """刷新字体列表"""
        self.font_list = self.get_system_fonts()
        self.font_count_label.setText(f"系统字体: {len(self.font_list)} 个")

        # 重新加载各标签页
        self.browser_tab.load_fonts()
        self.statusBar().showMessage("字体列表已刷新")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 FontManager",
            "<h2>FontManager v1.0.0</h2>"
            "<p>专业字体管理工具</p>"
            "<p>功能特性：</p>"
            "<ul>"
            "<li>字体浏览与预览</li>"
            "<li>多字体比较</li>"
            "<li>字体分类管理</li>"
            "<li>字体信息查看</li>"
            "<li>字体列表导出</li>"
            "</ul>"
            "<p>基于 PyQt6 开发</p>"
        )


# ==================== 程序入口 ====================
def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyleSheet(DARK_STYLE)

    # 设置应用程序属性
    app.setApplicationName("FontManager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FontManager")

    # 创建主窗口
    window = FontManagerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
