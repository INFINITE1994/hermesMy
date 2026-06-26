#!/usr/bin/env python3
"""
TextTools - 文本处理工具箱
一个功能丰富的文本处理工具箱桌面应用
"""

import sys
import re
import json
import hashlib
import base64
import difflib
from urllib.parse import quote, unquote
from html import escape, unescape

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox,
    QGroupBox, QGridLayout, QLineEdit, QCheckBox, QSplitter,
    QFrame, QScrollArea, QMessageBox, QPlainTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QTextCharFormat, QSyntaxHighlighter,
    QTextCursor, QLinearGradient, QBrush, QPainter, QIcon
)


# ============================================================================
# 样式定义
# ============================================================================

DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}

QTabWidget::pane {
    border: 1px solid #2a2a3a;
    background-color: #0a0a0a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #111122;
    color: #8888aa;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #1a1a2e;
    color: #aaaacc;
}

QTextEdit, QPlainTextEdit {
    background-color: #111122;
    color: #e0e0f0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', 'Source Code Pro', monospace;
    font-size: 13px;
    selection-background-color: #667eea;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #667eea;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7790ee, stop:1 #875bb2);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5568cc, stop:1 #653a8a);
}

QPushButton.secondary {
    background-color: #1a1a2e;
    border: 1px solid #2a2a3a;
}

QPushButton.secondary:hover {
    background-color: #252540;
    border: 1px solid #667eea;
}

QComboBox {
    background-color: #111122;
    color: #e0e0f0;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8888aa;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #111122;
    color: #e0e0f0;
    border: 1px solid #2a2a3a;
    selection-background-color: #667eea;
}

QLineEdit {
    background-color: #111122;
    color: #e0e0f0;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #667eea;
}

QLabel {
    color: #b0b0cc;
    font-size: 13px;
}

QGroupBox {
    color: #8888aa;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-size: 13px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}

QCheckBox {
    color: #b0b0cc;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #2a2a3a;
    background-color: #111122;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border: none;
}

QSplitter::handle {
    background-color: #2a2a3a;
    width: 2px;
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
    height: 0px;
}

QScrollArea {
    border: none;
    background-color: #0a0a0a;
}
"""


# ============================================================================
# 自定义组件
# ============================================================================

class CardWidget(QFrame):
    """卡片式容器组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            CardWidget {
                background-color: #111122;
                border: 1px solid #2a2a3a;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(20, 20, 20, 20)


class GradientLabel(QLabel):
    """渐变色标题标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            GradientLabel {
                color: #667eea;
                font-size: 16px;
                font-weight: 700;
                padding: 4px 0;
            }
        """)


class ResultLabel(QLabel):
    """结果展示标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            ResultLabel {
                color: #88cc88;
                font-size: 12px;
                padding: 8px 12px;
                background-color: #0a1a0a;
                border-radius: 6px;
                border: 1px solid #1a3a1a;
            }
        """)
        self.setWordWrap(True)


# ============================================================================
# 正则表达式高亮器
# ============================================================================

class RegexHighlighter(QSyntaxHighlighter):
    """正则表达式匹配高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rules = []
        self.match_format = QTextCharFormat()
        self.match_format.setBackground(QColor("#667eea"))
        self.match_format.setForeground(QColor("#ffffff"))

    def set_pattern(self, pattern):
        self.highlight_rules = []
        if pattern:
            try:
                regex = QRegularExpression(pattern)
                self.highlight_rules.append((regex, self.match_format))
            except Exception:
                pass
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.highlight_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)


# ============================================================================
# 工具标签页基类
# ============================================================================

class BaseToolTab(QWidget):
    """工具标签页基类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(24, 24, 24, 24)

    def create_button_row(self, buttons):
        """创建按钮行"""
        row = QHBoxLayout()
        row.setSpacing(12)
        for btn in buttons:
            row.addWidget(btn)
        row.addStretch()
        return row

    def create_text_pair(self, left_label, right_label):
        """创建左右文本编辑器对"""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_card = CardWidget()
        left_title = GradientLabel(left_label)
        left_text = QTextEdit()
        left_text.setPlaceholderText(f"请输入{left_label}...")
        left_card.layout.addWidget(left_title)
        left_card.layout.addWidget(left_text)

        right_card = CardWidget()
        right_title = GradientLabel(right_label)
        right_text = QTextEdit()
        right_text.setReadOnly(True)
        right_text.setPlaceholderText(f"{right_label}将显示在这里...")
        right_card.layout.addWidget(right_title)
        right_card.layout.addWidget(right_text)

        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setSizes([1, 1])

        return splitter, left_text, right_text


# ============================================================================
# 工具实现
# ============================================================================

class TextFormatConverter(BaseToolTab):
    """文本格式转换器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # 控制区
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        self.from_combo = QComboBox()
        self.from_combo.addItems(["Markdown", "HTML", "纯文本"])

        arrow_label = QLabel("➜")
        arrow_label.setStyleSheet("color: #667eea; font-size: 20px; font-weight: bold;")

        self.to_combo = QComboBox()
        self.to_combo.addItems(["HTML", "Markdown", "纯文本"])

        convert_btn = QPushButton("转换")
        convert_btn.clicked.connect(self._convert)

        swap_btn = QPushButton("交换")
        swap_btn.setProperty("class", "secondary")
        swap_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                border: 1px solid #2a2a3a;
            }
            QPushButton:hover {
                background-color: #252540;
                border: 1px solid #667eea;
            }
        """)
        swap_btn.clicked.connect(self._swap)

        control_layout.addWidget(QLabel("从:"))
        control_layout.addWidget(self.from_combo)
        control_layout.addWidget(arrow_label)
        control_layout.addWidget(QLabel("到:"))
        control_layout.addWidget(self.to_combo)
        control_layout.addWidget(convert_btn)
        control_layout.addWidget(swap_btn)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        # 文本区
        splitter, self.input_text, self.output_text = self.create_text_pair(
            "输入文本", "转换结果"
        )
        self.main_layout.addWidget(splitter)

    def _convert(self):
        text = self.input_text.toPlainText()
        if not text.strip():
            return

        from_fmt = self.from_combo.currentText()
        to_fmt = self.to_combo.currentText()

        try:
            # 先转为中间格式(纯文本)
            if from_fmt == "Markdown":
                plain = self._md_to_plain(text)
            elif from_fmt == "HTML":
                plain = self._html_to_plain(text)
            else:
                plain = text

            # 再从纯文本转为目标格式
            if to_fmt == "HTML":
                result = self._plain_to_html(plain)
            elif to_fmt == "Markdown":
                result = self._plain_to_md(plain)
            else:
                result = plain

            self.output_text.setPlainText(result)
        except Exception as e:
            self.output_text.setPlainText(f"转换错误: {str(e)}")

    def _swap(self):
        self.from_combo.setCurrentIndex(self.to_combo.currentIndex())
        self.to_combo.setCurrentIndex(
            0 if self.from_combo.currentIndex() == 0 else 0
        )
        temp = self.input_text.toPlainText()
        self.input_text.setPlainText(self.output_text.toPlainText())
        self.output_text.setPlainText(temp)

    def _md_to_plain(self, text):
        """简单Markdown转纯文本"""
        lines = text.split('\n')
        result = []
        for line in lines:
            # 移除标题标记
            line = re.sub(r'^#{1,6}\s+', '', line)
            # 移除粗体/斜体
            line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            line = re.sub(r'\*(.+?)\*', r'\1', line)
            line = re.sub(r'__(.+?)__', r'\1', line)
            line = re.sub(r'_(.+?)_', r'\1', line)
            # 移除行内代码
            line = re.sub(r'`(.+?)`', r'\1', line)
            # 移除链接格式
            line = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', line)
            # 移除图片
            line = re.sub(r'!\[(.+?)\]\(.+?\)', r'[图片: \1]', line)
            # 移除列表标记
            line = re.sub(r'^[\*\-\+]\s+', '• ', line)
            line = re.sub(r'^\d+\.\s+', '', line)
            # 移除引用
            line = re.sub(r'^>\s+', '', line)
            # 移除分割线
            line = re.sub(r'^[\-\*_]{3,}$', '---', line)
            result.append(line)
        return '\n'.join(result)

    def _html_to_plain(self, text):
        """HTML转纯文本"""
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<h[1-6][^>]*>(.+?)</h[1-6]>', r'\1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<li[^>]*>(.+?)</li>', r'• \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = unescape(text)
        return text.strip()

    def _plain_to_html(self, text):
        """纯文本转HTML"""
        escaped = escape(text)
        lines = escaped.split('\n')
        result = ['<div style="font-family: sans-serif; line-height: 1.6;">']
        for line in lines:
            if not line.strip():
                result.append('<br>')
            else:
                result.append(f'<p>{line}</p>')
        result.append('</div>')
        return '\n'.join(result)

    def _plain_to_md(self, text):
        """纯文本转Markdown"""
        return text


class JsonFormatter(BaseToolTab):
    """JSON格式化器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # 控制区
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        format_btn = QPushButton("格式化")
        format_btn.clicked.connect(self._format_json)

        minify_btn = QPushButton("压缩")
        minify_btn.clicked.connect(self._minify_json)

        validate_btn = QPushButton("验证")
        validate_btn.clicked.connect(self._validate_json)

        self.indent_combo = QComboBox()
        self.indent_combo.addItems(["2 空格", "4 空格", "Tab", "无缩进"])

        control_layout.addWidget(format_btn)
        control_layout.addWidget(minify_btn)
        control_layout.addWidget(validate_btn)
        control_layout.addWidget(QLabel("缩进:"))
        control_layout.addWidget(self.indent_combo)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        # 文本区
        splitter, self.input_text, self.output_text = self.create_text_pair(
            "输入 JSON", "格式化结果"
        )
        self.main_layout.addWidget(splitter)

        # 状态标签
        self.status_label = ResultLabel("就绪")
        self.main_layout.addWidget(self.status_label)

    def _get_indent(self):
        idx = self.indent_combo.currentIndex()
        if idx == 0: return 2
        if idx == 1: return 4
        if idx == 2: return "\t"
        return None

    def _format_json(self):
        text = self.input_text.toPlainText()
        if not text.strip():
            return
        try:
            data = json.loads(text)
            indent = self._get_indent()
            result = json.dumps(data, indent=indent, ensure_ascii=False)
            self.output_text.setPlainText(result)
            self.status_label.setText("✓ JSON 格式化成功")
            self.status_label.setStyleSheet("""
                ResultLabel {
                    color: #88cc88; font-size: 12px; padding: 8px 12px;
                    background-color: #0a1a0a; border-radius: 6px;
                    border: 1px solid #1a3a1a;
                }
            """)
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ JSON 语法错误: {str(e)}")
            self.status_label.setStyleSheet("""
                ResultLabel {
                    color: #cc8888; font-size: 12px; padding: 8px 12px;
                    background-color: #1a0a0a; border-radius: 6px;
                    border: 1px solid #3a1a1a;
                }
            """)

    def _minify_json(self):
        text = self.input_text.toPlainText()
        if not text.strip():
            return
        try:
            data = json.loads(text)
            result = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            self.output_text.setPlainText(result)
            self.status_label.setText("✓ JSON 压缩成功")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ JSON 语法错误: {str(e)}")

    def _validate_json(self):
        text = self.input_text.toPlainText()
        if not text.strip():
            return
        try:
            data = json.loads(text)
            type_name = type(data).__name__
            if isinstance(data, dict):
                info = f"对象，包含 {len(data)} 个键"
            elif isinstance(data, list):
                info = f"数组，包含 {len(data)} 个元素"
            else:
                info = type_name
            self.status_label.setText(f"✓ 有效的 JSON ({info})")
            self.status_label.setStyleSheet("""
                ResultLabel {
                    color: #88cc88; font-size: 12px; padding: 8px 12px;
                    background-color: #0a1a0a; border-radius: 6px;
                    border: 1px solid #1a3a1a;
                }
            """)
        except json.JSONDecodeError as e:
            self.status_label.setText(f"✗ 无效的 JSON: 行 {e.lineno}, 列 {e.colno} - {e.msg}")
            self.status_label.setStyleSheet("""
                ResultLabel {
                    color: #cc8888; font-size: 12px; padding: 8px 12px;
                    background-color: #1a0a0a; border-radius: 6px;
                    border: 1px solid #3a1a1a;
                }
            """)


class Base64Codec(BaseToolTab):
    """Base64编解码器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        encode_btn = QPushButton("编码")
        encode_btn.clicked.connect(self._encode)

        decode_btn = QPushButton("解码")
        decode_btn.clicked.connect(self._decode)

        clear_btn = QPushButton("清空")
        clear_btn.setProperty("class", "secondary")
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #1a1a2e; border: 1px solid #2a2a3a; }
            QPushButton:hover { background-color: #252540; border: 1px solid #667eea; }
        """)
        clear_btn.clicked.connect(self._clear)

        control_layout.addWidget(encode_btn)
        control_layout.addWidget(decode_btn)
        control_layout.addWidget(clear_btn)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        splitter, self.input_text, self.output_text = self.create_text_pair(
            "输入文本", "Base64 结果"
        )
        self.main_layout.addWidget(splitter)

        self.status_label = ResultLabel("就绪")
        self.main_layout.addWidget(self.status_label)

    def _encode(self):
        text = self.input_text.toPlainText()
        if not text:
            return
        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
            self.output_text.setPlainText(encoded)
            self.status_label.setText(f"✓ 编码成功 (输入 {len(text)} 字符 → {len(encoded)} 字符)")
        except Exception as e:
            self.status_label.setText(f"✗ 编码失败: {str(e)}")

    def _decode(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            self.output_text.setPlainText(decoded)
            self.status_label.setText(f"✓ 解码成功 ({len(text)} 字符 → {len(decoded)} 字符)")
        except Exception as e:
            self.status_label.setText(f"✗ 解码失败: {str(e)}")

    def _clear(self):
        self.input_text.clear()
        self.output_text.clear()
        self.status_label.setText("已清空")


class UrlCodec(BaseToolTab):
    """URL编解码器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        encode_btn = QPushButton("编码")
        encode_btn.clicked.connect(self._encode)

        decode_btn = QPushButton("解码")
        decode_btn.clicked.connect(self._decode)

        encode_component_btn = QPushButton("编码组件")
        encode_component_btn.clicked.connect(self._encode_component)

        control_layout.addWidget(encode_btn)
        control_layout.addWidget(decode_btn)
        control_layout.addWidget(encode_component_btn)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        splitter, self.input_text, self.output_text = self.create_text_pair(
            "输入 URL", "编码/解码结果"
        )
        self.main_layout.addWidget(splitter)

        self.status_label = ResultLabel("提示: 「编码」保留 URL 结构，「编码组件」编码所有字符")
        self.main_layout.addWidget(self.status_label)

    def _encode(self):
        text = self.input_text.toPlainText()
        if not text:
            return
        try:
            # 分离URL的各部分进行编码
            encoded = quote(text, safe=':/?#[]@!$&\'()*+,;=-._~%')
            self.output_text.setPlainText(encoded)
            self.status_label.setText("✓ URL 编码成功")
        except Exception as e:
            self.status_label.setText(f"✗ 编码失败: {str(e)}")

    def _decode(self):
        text = self.input_text.toPlainText()
        if not text:
            return
        try:
            decoded = unquote(text)
            self.output_text.setPlainText(decoded)
            self.status_label.setText("✓ URL 解码成功")
        except Exception as e:
            self.status_label.setText(f"✗ 解码失败: {str(e)}")

    def _encode_component(self):
        text = self.input_text.toPlainText()
        if not text:
            return
        try:
            encoded = quote(text, safe='')
            self.output_text.setPlainText(encoded)
            self.status_label.setText("✓ URL 组件编码成功")
        except Exception as e:
            self.status_label.setText(f"✗ 编码失败: {str(e)}")


class HashGenerator(BaseToolTab):
    """哈希生成器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        generate_btn = QPushButton("生成哈希")
        generate_btn.clicked.connect(self._generate)

        self.upper_check = QCheckBox("大写输出")

        control_layout.addWidget(generate_btn)
        control_layout.addWidget(self.upper_check)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        # 输入
        input_card = CardWidget()
        input_title = GradientLabel("输入文本")
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("请输入要计算哈希的文本...")
        self.input_text.setMaximumHeight(150)
        input_card.layout.addWidget(input_title)
        input_card.layout.addWidget(self.input_text)
        self.main_layout.addWidget(input_card)

        # 结果区
        results_card = CardWidget()
        results_title = GradientLabel("哈希结果")
        results_card.layout.addWidget(results_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.md5_label = QLineEdit()
        self.md5_label.setReadOnly(True)
        self.md5_label.setPlaceholderText("MD5 哈希值")

        self.sha1_label = QLineEdit()
        self.sha1_label.setReadOnly(True)
        self.sha1_label.setPlaceholderText("SHA1 哈希值")

        self.sha256_label = QLineEdit()
        self.sha256_label.setReadOnly(True)
        self.sha256_label.setPlaceholderText("SHA256 哈希值")

        for i, (name, widget) in enumerate([
            ("MD5", self.md5_label),
            ("SHA1", self.sha1_label),
            ("SHA256", self.sha256_label)
        ]):
            label = QLabel(name)
            label.setStyleSheet("color: #667eea; font-weight: 700; font-size: 14px;")
            copy_btn = QPushButton("复制")
            copy_btn.setFixedWidth(60)
            copy_btn.clicked.connect(lambda checked, w=widget: self._copy(w))

            grid.addWidget(label, i, 0)
            grid.addWidget(widget, i, 1)
            grid.addWidget(copy_btn, i, 2)

        results_card.layout.addLayout(grid)
        self.main_layout.addWidget(results_card)

        self.status_label = ResultLabel("就绪")
        self.main_layout.addWidget(self.status_label)

    def _generate(self):
        text = self.input_text.toPlainText()
        if not text:
            return

        data = text.encode('utf-8')
        upper = self.upper_check.isChecked()

        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()

        if upper:
            md5, sha1, sha256 = md5.upper(), sha1.upper(), sha256.upper()

        self.md5_label.setText(md5)
        self.sha1_label.setText(sha1)
        self.sha256_label.setText(sha256)

        self.status_label.setText(f"✓ 已生成 3 种哈希 (输入 {len(text)} 字符, {len(data)} 字节)")

    def _copy(self, widget):
        text = widget.text()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText(f"✓ 已复制到剪贴板: {text[:20]}...")


class RegexTester(BaseToolTab):
    """正则表达式测试器"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # 正则输入
        regex_card = CardWidget()
        regex_title = GradientLabel("正则表达式")
        regex_card.layout.addWidget(regex_title)

        regex_row = QHBoxLayout()
        regex_row.addWidget(QLabel("表达式:"))
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式，如: \\d+")
        self.regex_input.textChanged.connect(self._on_regex_change)
        regex_row.addWidget(self.regex_input)

        self.case_check = QCheckBox("忽略大小写")
        self.case_check.stateChanged.connect(self._on_regex_change)
        regex_row.addWidget(self.case_check)

        regex_card.layout.addLayout(regex_row)

        # 标志位
        flags_row = QHBoxLayout()
        self.multiline_check = QCheckBox("多行模式")
        self.dotall_check = QCheckBox("点匹配换行")
        self.multiline_check.stateChanged.connect(self._on_regex_change)
        self.dotall_check.stateChanged.connect(self._on_regex_change)
        flags_row.addWidget(self.multiline_check)
        flags_row.addWidget(self.dotall_check)
        flags_row.addStretch()
        regex_card.layout.addLayout(flags_row)

        self.main_layout.addWidget(regex_card)

        # 测试文本
        text_card = CardWidget()
        text_title = GradientLabel("测试文本")
        self.test_text = QPlainTextEdit()
        self.test_text.setPlaceholderText("输入要测试的文本...")
        self.test_text.textChanged.connect(self._on_regex_change)
        self.highlighter = RegexHighlighter(self.test_text.document())
        text_card.layout.addWidget(text_title)
        text_card.layout.addWidget(self.test_text)
        self.main_layout.addWidget(text_card)

        # 匹配结果
        result_card = CardWidget()
        result_title = GradientLabel("匹配结果")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        result_card.layout.addWidget(result_title)
        result_card.layout.addWidget(self.result_text)
        self.main_layout.addWidget(result_card)

        self.status_label = ResultLabel("就绪")
        self.main_layout.addWidget(self.status_label)

    def _on_regex_change(self):
        pattern = self.regex_input.text()
        text = self.test_text.toPlainText()

        if not pattern or not text:
            self.result_text.clear()
            self.status_label.setText("请输入正则表达式和测试文本")
            self.highlighter.set_pattern("")
            return

        flags = 0
        if self.case_check.isChecked():
            flags |= re.IGNORECASE
        if self.multiline_check.isChecked():
            flags |= re.MULTILINE
        if self.dotall_check.isChecked():
            flags |= re.DOTALL

        try:
            regex = re.compile(pattern, flags)
            matches = list(regex.finditer(text))

            if matches:
                # 更新高亮
                self.highlighter.set_pattern(pattern)

                result_lines = [f"找到 {len(matches)} 个匹配:\n"]
                for i, m in enumerate(matches[:50]):  # 最多显示50个
                    result_lines.append(
                        f"[{i+1}] 位置 {m.start()}-{m.end()}: \"{m.group()}\""
                    )
                    if m.groups():
                        for j, g in enumerate(m.groups(), 1):
                            result_lines.append(f"     分组{j}: \"{g}\"")

                self.result_text.setPlainText('\n'.join(result_lines))
                self.status_label.setText(f"✓ 找到 {len(matches)} 个匹配")
            else:
                self.result_text.setPlainText("没有找到匹配")
                self.status_label.setText("未找到匹配")
                self.highlighter.set_pattern("")

        except re.error as e:
            self.result_text.clear()
            self.status_label.setText(f"✗ 正则表达式错误: {str(e)}")
            self.highlighter.set_pattern("")


class TextDiff(BaseToolTab):
    """文本对比工具"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # 控制区
        control_card = CardWidget()
        control_layout = QHBoxLayout()

        diff_btn = QPushButton("对比文本")
        diff_btn.clicked.connect(self._compare)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["逐行对比", "字符对比", "词对比"])

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #1a1a2e; border: 1px solid #2a2a3a; }
            QPushButton:hover { background-color: #252540; border: 1px solid #667eea; }
        """)
        clear_btn.clicked.connect(self._clear)

        control_layout.addWidget(diff_btn)
        control_layout.addWidget(QLabel("模式:"))
        control_layout.addWidget(self.mode_combo)
        control_layout.addWidget(clear_btn)
        control_layout.addStretch()

        control_card.layout.addLayout(control_layout)
        self.main_layout.addWidget(control_card)

        # 输入区
        input_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_card = CardWidget()
        left_title = GradientLabel("原始文本")
        self.left_text = QTextEdit()
        self.left_text.setPlaceholderText("输入原始文本...")
        left_card.layout.addWidget(left_title)
        left_card.layout.addWidget(self.left_text)

        right_card = CardWidget()
        right_title = GradientLabel("修改后文本")
        self.right_text = QTextEdit()
        self.right_text.setPlaceholderText("输入修改后的文本...")
        right_card.layout.addWidget(right_title)
        right_card.layout.addWidget(self.right_text)

        input_splitter.addWidget(left_card)
        input_splitter.addWidget(right_card)
        input_splitter.setSizes([1, 1])
        self.main_layout.addWidget(input_splitter)

        # 结果区
        result_card = CardWidget()
        result_title = GradientLabel("对比结果")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_card.layout.addWidget(result_title)
        result_card.layout.addWidget(self.result_text)
        self.main_layout.addWidget(result_card)

        self.status_label = ResultLabel("就绪")
        self.main_layout.addWidget(self.status_label)

    def _compare(self):
        left = self.left_text.toPlainText()
        right = self.right_text.toPlainText()

        if not left and not right:
            return

        mode = self.mode_combo.currentIndex()

        try:
            if mode == 0:  # 逐行
                diff = list(difflib.unified_diff(
                    left.splitlines(keepends=True),
                    right.splitlines(keepends=True),
                    fromfile='原始文本',
                    tofile='修改后文本',
                    lineterm=''
                ))
            elif mode == 1:  # 字符
                diff = list(difflib.unified_diff(
                    list(left), list(right),
                    fromfile='原始文本',
                    tofile='修改后文本'
                ))
            else:  # 词
                diff = list(difflib.unified_diff(
                    left.split(), right.split(),
                    fromfile='原始文本',
                    tofile='修改后文本'
                ))

            if diff:
                result = '\n'.join(diff)
                self.result_text.setPlainText(result)

                adds = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
                dels = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
                self.status_label.setText(f"✓ 对比完成: +{adds} 行新增, -{dels} 行删除")
            else:
                self.result_text.setPlainText("两段文本完全相同")
                self.status_label.setText("✓ 两段文本完全相同")

        except Exception as e:
            self.status_label.setText(f"✗ 对比失败: {str(e)}")

    def _clear(self):
        self.left_text.clear()
        self.right_text.clear()
        self.result_text.clear()


class WordCounter(BaseToolTab):
    """字数统计工具"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # 输入区
        input_card = CardWidget()
        input_title = GradientLabel("输入文本")
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入或粘贴文本，统计结果将实时更新...")
        self.input_text.textChanged.connect(self._count)
        input_card.layout.addWidget(input_title)
        input_card.layout.addWidget(self.input_text)
        self.main_layout.addWidget(input_card)

        # 统计结果
        stats_card = CardWidget()
        stats_title = GradientLabel("统计结果")
        stats_card.layout.addWidget(stats_title)

        grid = QGridLayout()
        grid.setSpacing(16)

        stats = [
            ("字数", "0", "#667eea"),
            ("字符数(含空格)", "0", "#764ba2"),
            ("字符数(不含空格)", "0", "#667eea"),
            ("行数", "0", "#764ba2"),
            ("段落数", "0", "#667eea"),
            ("句子数", "0", "#764ba2"),
            ("中文字数", "0", "#667eea"),
            ("英文单词", "0", "#764ba2"),
        ]

        self.stat_labels = {}
        for i, (name, value, color) in enumerate(stats):
            row, col = divmod(i, 2)

            container = QFrame()
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: #0a0a14;
                    border: 1px solid #2a2a3a;
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(4)

            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")

            value_label = QLabel("0")
            value_label.setStyleSheet("color: #e0e0f0; font-size: 24px; font-weight: 700;")

            container_layout.addWidget(name_label)
            container_layout.addWidget(value_label)

            self.stat_labels[name] = value_label
            grid.addWidget(container, row, col)

        stats_card.layout.addLayout(grid)
        self.main_layout.addWidget(stats_card)

    def _count(self):
        text = self.input_text.toPlainText()

        # 字数
        words = len(text.split()) if text.strip() else 0

        # 字符数
        chars_with_space = len(text)
        chars_no_space = len(text.replace(' ', '').replace('\t', '').replace('\n', ''))

        # 行数
        lines = text.count('\n') + 1 if text else 0

        # 段落数
        paragraphs = len([p for p in text.split('\n\n') if p.strip()]) if text.strip() else 0

        # 句子数
        sentences = len(re.split(r'[.!?。！？]+', text.strip())) if text.strip() else 0

        # 中文字数
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))

        # 英文单词
        english = len(re.findall(r'[a-zA-Z]+', text))

        self.stat_labels["字数"].setText(str(words))
        self.stat_labels["字符数(含空格)"].setText(str(chars_with_space))
        self.stat_labels["字符数(不含空格)"].setText(str(chars_no_space))
        self.stat_labels["行数"].setText(str(lines))
        self.stat_labels["段落数"].setText(str(paragraphs))
        self.stat_labels["句子数"].setText(str(sentences))
        self.stat_labels["中文字数"].setText(str(chinese))
        self.stat_labels["英文单词"].setText(str(english))


# ============================================================================
# 主窗口
# ============================================================================

class TextToolsWindow(QMainWindow):
    """TextTools 主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TextTools - 文本处理工具箱")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 创建主容器
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                padding: 16px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)

        title = QLabel("🛠️ TextTools")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: 700;")

        subtitle = QLabel("文本处理工具箱")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 14px;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tabs.addTab(TextFormatConverter(), "📄 文本格式转换")
        self.tabs.addTab(JsonFormatter(), "📋 JSON 格式化")
        self.tabs.addTab(Base64Codec(), "🔐 Base64 编解码")
        self.tabs.addTab(UrlCodec(), "🌐 URL 编解码")
        self.tabs.addTab(HashGenerator(), "#️⃣ 哈希生成器")
        self.tabs.addTab(RegexTester(), "🔍 正则测试器")
        self.tabs.addTab(TextDiff(), "📊 文本对比")
        self.tabs.addTab(WordCounter(), "📝 字数统计")

        main_layout.addWidget(self.tabs)


# ============================================================================
# 入口
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 应用深色主题
    app.setStyleSheet(DARK_STYLE)

    # 设置应用字体
    font = QFont("Microsoft YaHei", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = TextToolsWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
