#!/usr/bin/env python3
"""
Markdown 编辑器 - 专业的桌面 Markdown 编辑器
支持实时预览、数学公式、表格编辑、主题切换
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QToolBar, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QSpinBox,
    QLineEdit, QComboBox, QDialogButtonBox, QLabel, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QGroupBox, QPushButton,
    QTabWidget, QPlainTextEdit, QGridLayout, QFrame, QSizePolicy,
    QStyleFactory, QStyle, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QSize, QUrl, QSettings, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve, QPoint, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QAction, QSyntaxHighlighter,
    QTextCharFormat, QTextCursor, QKeySequence, QShortcut,
    QPainter, QLinearGradient, QBrush, QTextDocument, QPixmap,
    QDesktopServices, QFontDatabase, QPen
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False


# ============================================================================
# 主题配置
# ============================================================================

DARK_THEME = {
    "name": "深色",
    "background": "#0a0a0a",
    "card": "#111122",
    "accent_start": "#667eea",
    "accent_end": "#764ba2",
    "text": "#e0e0e0",
    "text_secondary": "#8888aa",
    "border": "#222244",
    "editor_bg": "#0d0d1a",
    "editor_fg": "#d4d4d4",
    "line_number": "#444466",
    "selection": "#333366",
    "toolbar_bg": "#0f0f1f",
    "sidebar_bg": "#08081a",
    "preview_bg": "#0a0a15",
    "button_hover": "#1a1a3a",
    "input_bg": "#111128",
    "scrollbar": "#333355",
    "scrollbar_hover": "#4444aa",
    "error": "#ff4444",
    "warning": "#ffaa00",
    "success": "#44ff88",
    "info": "#4488ff",
}

LIGHT_THEME = {
    "name": "浅色",
    "background": "#ffffff",
    "card": "#f5f5f5",
    "accent_start": "#667eea",
    "accent_end": "#764ba2",
    "text": "#333333",
    "text_secondary": "#666666",
    "border": "#dddddd",
    "editor_bg": "#ffffff",
    "editor_fg": "#333333",
    "line_number": "#999999",
    "selection": "#cce0ff",
    "toolbar_bg": "#f8f8f8",
    "sidebar_bg": "#f0f0f0",
    "preview_bg": "#ffffff",
    "button_hover": "#e8e8e8",
    "input_bg": "#ffffff",
    "scrollbar": "#cccccc",
    "scrollbar_hover": "#aaaaaa",
    "error": "#cc0000",
    "warning": "#cc8800",
    "success": "#00aa44",
    "info": "#0066cc",
}


# ============================================================================
# Markdown 语法高亮器
# ============================================================================

class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 语法高亮器"""

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.highlighting_rules = []
        self._setup_rules()

    def _setup_rules(self):
        """设置高亮规则"""
        self.highlighting_rules = []

        # 标题
        heading_format = QTextCharFormat()
        heading_format.setForeground(QColor(self.theme["accent_start"]))
        heading_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^#{1,6}\s+.*$', heading_format))

        # 加粗
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        bold_format.setForeground(QColor("#ffffff"))
        self.highlighting_rules.append((r'\*\*[^*]+\*\*', bold_format))
        self.highlighting_rules.append((r'__[^_]+__', bold_format))

        # 斜体
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor("#ccccff"))
        self.highlighting_rules.append((r'\*[^*]+\*', italic_format))
        self.highlighting_rules.append((r'_[^_]+_', italic_format))

        # 行内代码
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#ff8888"))
        code_format.setFontFamily("Consolas")
        self.highlighting_rules.append((r'`[^`]+`', code_format))

        # 代码块
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#ff8888"))
        code_block_format.setFontFamily("Consolas")
        code_block_format.setBackground(QColor("#1a1a2e"))
        self.highlighting_rules.append((r'^```.*$', code_block_format))

        # 链接
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#66bbff"))
        link_format.setFontUnderline(True)
        self.highlighting_rules.append((r'\[([^\]]+)\]\([^)]+\)', link_format))

        # 图片
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("#88ddaa"))
        self.highlighting_rules.append((r'!\[([^\]]*)\]\([^)]+\)', image_format))

        # 引用
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#aaaaff"))
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((r'^>\s+.*$', quote_format))

        # 列表
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#ffcc44"))
        self.highlighting_rules.append((r'^[\-\*\+]\s+', list_format))
        self.highlighting_rules.append((r'^\d+\.\s+', list_format))

        # 数学公式
        math_format = QTextCharFormat()
        math_format.setForeground(QColor("#ff88ff"))
        math_format.setFontFamily("Consolas")
        self.highlighting_rules.append((r'\$[^$]+\$', math_format))
        self.highlighting_rules.append((r'^\$\$.*\$\$$', math_format))

        # 分隔线
        hr_format = QTextCharFormat()
        hr_format.setForeground(QColor("#444466"))
        self.highlighting_rules.append((r'^[\-\*_]{3,}\s*$', hr_format))

        # 删除线
        strike_format = QTextCharFormat()
        strike_format.setForeground(QColor("#888888"))
        strike_format.setFontStrikeOut(True)
        self.highlighting_rules.append((r'~~[^~]+~~', strike_format))

        # 表格分隔符
        table_format = QTextCharFormat()
        table_format.setForeground(QColor("#666688"))
        self.highlighting_rules.append((r'^\|.*\|$', table_format))

    def update_theme(self, theme):
        """更新主题"""
        self.theme = theme
        self._setup_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        """高亮文本块"""
        for pattern, fmt in self.highlighting_rules:
            expression = re.compile(pattern, re.MULTILINE)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ============================================================================
# 表格编辑器对话框
# ============================================================================

class TableEditorDialog(QDialog):
    """表格编辑器对话框"""

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.setWindowTitle("📊 表格编辑器")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 控制行
        control_layout = QHBoxLayout()

        control_layout.addWidget(QLabel("行数:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.setValue(3)
        self.rows_spin.valueChanged.connect(self._update_grid)
        control_layout.addWidget(self.rows_spin)

        control_layout.addWidget(QLabel("列数:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 20)
        self.cols_spin.setValue(3)
        self.cols_spin.valueChanged.connect(self._update_grid)
        control_layout.addWidget(self.cols_spin)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 表格网格
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        layout.addWidget(self.grid_widget)

        # 对齐选项
        align_layout = QHBoxLayout()
        align_layout.addWidget(QLabel("对齐方式:"))
        self.align_combo = QComboBox()
        self.align_combo.addItems(["左对齐", "居中", "右对齐"])
        align_layout.addWidget(self.align_combo)
        align_layout.addStretch()
        layout.addLayout(align_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._update_grid()
        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme["background"]};
                color: {self.theme["text"]};
            }}
            QLabel {{
                color: {self.theme["text"]};
            }}
            QSpinBox, QComboBox {{
                background-color: {self.theme["input_bg"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 4px;
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {self.theme["input_bg"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {self.theme["card"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme["button_hover"]};
            }}
        """)

    def _update_grid(self):
        """更新表格网格"""
        # 清空现有控件
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rows = self.rows_spin.value()
        cols = self.cols_spin.value()

        self.cells = []
        for i in range(rows):
            row_cells = []
            for j in range(cols):
                cell = QLineEdit()
                cell.setMinimumWidth(80)
                cell.setPlaceholderText(f"单元格 ({i+1},{j+1})")
                self.grid_layout.addWidget(cell, i, j)
                row_cells.append(cell)
            self.cells.append(row_cells)

    def get_table_markdown(self) -> str:
        """获取 Markdown 表格代码"""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        align = self.align_combo.currentIndex()

        lines = []

        # 表头
        header = "| " + " | ".join(
            self.cells[0][j].text() or f"列{j+1}" for j in range(cols)
        ) + " |"
        lines.append(header)

        # 分隔线
        if align == 0:
            sep = "| " + " | ".join(":---" for _ in range(cols)) + " |"
        elif align == 1:
            sep = "| " + " | ".join(":---:" for _ in range(cols)) + " |"
        else:
            sep = "| " + " | ".join("---:" for _ in range(cols)) + " |"
        lines.append(sep)

        # 数据行
        for i in range(1, rows):
            row = "| " + " | ".join(
                self.cells[i][j].text() or "" for j in range(cols)
            ) + " |"
            lines.append(row)

        return "\n".join(lines)


# ============================================================================
# 查找替换面板
# ============================================================================

class FindReplaceWidget(QWidget):
    """查找替换面板"""

    def __init__(self, editor, theme=None, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.theme = theme or DARK_THEME
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # 查找
        layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入搜索内容...")
        self.find_input.returnPressed.connect(self.find_next)
        layout.addWidget(self.find_input)

        # 替换
        layout.addWidget(QLabel("替换:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("替换为...")
        layout.addWidget(self.replace_input)

        # 正则表达式
        self.regex_check = QCheckBox("正则")
        layout.addWidget(self.regex_check)

        # 区分大小写
        self.case_check = QCheckBox("区分大小写")
        layout.addWidget(self.case_check)

        # 按钮
        find_btn = QPushButton("查找下一个")
        find_btn.clicked.connect(self.find_next)
        layout.addWidget(find_btn)

        replace_btn = QPushButton("替换")
        replace_btn.clicked.connect(self.replace_current)
        layout.addWidget(replace_btn)

        replace_all_btn = QPushButton("全部替换")
        replace_all_btn.clicked.connect(self.replace_all)
        layout.addWidget(replace_all_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme["toolbar_bg"]};
                color: {self.theme["text"]};
            }}
            QLineEdit {{
                background-color: {self.theme["input_bg"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {self.theme["card"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme["button_hover"]};
            }}
            QCheckBox {{
                color: {self.theme["text"]};
            }}
            QLabel {{
                color: {self.theme["text_secondary"]};
            }}
        """)

    def update_theme(self, theme):
        """更新主题"""
        self.theme = theme
        self._apply_theme()

    def find_next(self):
        """查找下一个"""
        text = self.find_input.text()
        if not text:
            return

        flags = QTextDocument.FindFlag(0)
        if self.case_check.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self.regex_check.isChecked():
            cursor = self.editor.document().find(re.compile(text), self.editor.textCursor(), flags)
        else:
            cursor = self.editor.document().find(text, self.editor.textCursor(), flags)

        if cursor.isNull():
            QMessageBox.information(self, "查找", "未找到匹配内容")
        else:
            self.editor.setTextCursor(cursor)

    def replace_current(self):
        """替换当前选中"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        """全部替换"""
        text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not text:
            return

        content = self.editor.toPlainText()
        if self.regex_check.isChecked():
            if self.case_check.isChecked():
                new_content = re.sub(text, replace_text, content)
            else:
                new_content = re.sub(text, replace_text, content, flags=re.IGNORECASE)
        else:
            if self.case_check.isChecked():
                new_content = content.replace(text, replace_text)
            else:
                pattern = re.compile(re.escape(text), re.IGNORECASE)
                new_content = pattern.sub(replace_text, content)

        count = len(content) - len(new_content) if text != replace_text else 0
        self.editor.setPlainText(new_content)
        QMessageBox.information(self, "全部替换", f"已完成替换")


# ============================================================================
# 数学公式输入对话框
# ============================================================================

class MathInputDialog(QDialog):
    """数学公式输入对话框"""

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.setWindowTitle("∑ 插入数学公式")
        self.setMinimumSize(500, 300)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 公式类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("公式类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["行内公式 ($...$)", "块级公式 ($$...$$)"])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # 公式输入
        layout.addWidget(QLabel("LaTeX 公式:"))
        self.formula_input = QPlainTextEdit()
        self.formula_input.setPlaceholderText("例如: E = mc^2 或 \\sum_{i=1}^{n} x_i")
        self.formula_input.setFont(QFont("Consolas", 12))
        layout.addWidget(self.formula_input)

        # 常用公式模板
        template_group = QGroupBox("常用模板")
        template_layout = QGridLayout()
        templates = [
            ("分数", "\\frac{a}{b}"),
            ("求和", "\\sum_{i=1}^{n} x_i"),
            ("积分", "\\int_{a}^{b} f(x)dx"),
            ("极限", "\\lim_{x \\to \\infty} f(x)"),
            ("矩阵", "\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}"),
            ("根号", "\\sqrt{x}"),
        ]
        for i, (name, formula) in enumerate(templates):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, f=formula: self.formula_input.setPlainText(f))
            template_layout.addWidget(btn, i // 3, i % 3)
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme["background"]};
                color: {self.theme["text"]};
            }}
            QLabel {{
                color: {self.theme["text"]};
            }}
            QGroupBox {{
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
            }}
            QPlainTextEdit {{
                background-color: {self.theme["input_bg"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                border-radius: 4px;
            }}
            QComboBox {{
                background-color: {self.theme["input_bg"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {self.theme["card"]};
                color: {self.theme["text"]};
                border: 1px solid {self.theme["border"]};
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme["button_hover"]};
            }}
        """)

    def get_formula(self) -> str:
        """获取公式文本"""
        formula = self.formula_input.toPlainText().strip()
        if not formula:
            return ""
        if self.type_combo.currentIndex() == 0:
            return f"${formula}$"
        else:
            return f"$${formula}$$"


# ============================================================================
# Markdown 编辑器
# ============================================================================

class MarkdownEditor(QPlainTextEdit):
    """Markdown 编辑器控件"""

    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.setTabStopDistance(40)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._setup_font()

    def _setup_font(self):
        """设置字体"""
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    def update_theme(self, theme):
        """更新主题"""
        self.theme = theme
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {theme["editor_bg"]};
                color: {theme["editor_fg"]};
                border: none;
                selection-background-color: {theme["selection"]};
                padding: 8px;
            }}
        """)

    def keyPressEvent(self, event):
        """处理按键事件"""
        # Tab 缩进
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor, indent=True)
            else:
                cursor.insertText("    ")
            return

        # Shift+Tab 反缩进
        if event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor, indent=False)
            return

        # Enter 自动续行
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            # 检测列表前缀
            list_match = re.match(r'^(\s*[\-\*\+]|\s*\d+\.)\s', text)
            if list_match:
                prefix = list_match.group(1)
                # 如果当前行只有前缀，删除前缀
                if text.strip() == prefix.strip() or text.strip() == prefix.strip() + ".":
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.insertText("")
                else:
                    # 续行
                    if re.match(r'^\s*\d+\.', prefix):
                        num = int(re.search(r'(\d+)', prefix).group(1))
                        new_prefix = re.sub(r'\d+', str(num + 1), prefix)
                    else:
                        new_prefix = prefix
                    super().keyPressEvent(event)
                    self.textCursor().insertText(new_prefix + " ")
                return

            # 检测引用
            quote_match = re.match(r'^(\s*>\s*)', text)
            if quote_match:
                prefix = quote_match.group(1)
                if text.strip() == ">" or text.strip() == "> ":
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.insertText("")
                else:
                    super().keyPressEvent(event)
                    self.textCursor().insertText(prefix)
                return

        super().keyPressEvent(event)

    def _indent_selection(self, cursor, indent=True):
        """缩进/反缩进选中文本"""
        cursor.beginEditBlock()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        start_block = cursor.blockNumber()

        cursor.setPosition(end)
        if cursor.atBlockStart() and cursor.blockNumber() > start_block:
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock)
        end_block = cursor.blockNumber()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)

        for _ in range(end_block - start_block + 1):
            if indent:
                cursor.insertText("    ")
            else:
                # 移除前导空格
                line = cursor.block().text()
                if line.startswith("    "):
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor, 4)
                    cursor.removeSelectedText()
                elif line.startswith("\t"):
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
                    cursor.removeSelectedText()

            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)

        cursor.endEditBlock()


# ============================================================================
# 大纲树
# ============================================================================

class OutlineTree(QTreeWidget):
    """文档大纲树"""

    heading_clicked = pyqtSignal(int)

    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.setHeaderLabel("文档结构")
        self.setColumnCount(1)
        self.setIndentation(16)
        self.itemClicked.connect(self._on_item_clicked)
        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {self.theme["sidebar_bg"]};
                color: {self.theme["text"]};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {self.theme["button_hover"]};
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme["selection"]};
            }}
            QHeaderView::section {{
                background-color: {self.theme["sidebar_bg"]};
                color: {self.theme["text_secondary"]};
                border: none;
                padding: 4px 8px;
            }}
        """)

    def update_theme(self, theme):
        """更新主题"""
        self.theme = theme
        self._apply_theme()

    def update_outline(self, content: str):
        """更新大纲"""
        self.clear()
        lines = content.split('\n')
        parent_stack = [None]  # 栈用于跟踪父节点

        for line_num, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()

                item = QTreeWidgetItem()
                item.setText(0, f"{'  ' * (level - 1)}H{level}: {title}")
                item.setData(0, Qt.ItemDataRole.UserRole, line_num)

                # 找到合适的父节点
                while len(parent_stack) > level:
                    parent_stack.pop()

                parent = parent_stack[-1]
                if parent:
                    parent.addChild(item)
                else:
                    self.addTopLevelItem(item)

                # 更新栈
                while len(parent_stack) <= level:
                    parent_stack.append(None)
                parent_stack[level] = item

        self.expandAll()

    def _on_item_clicked(self, item, column):
        """点击大纲项"""
        line_num = item.data(0, Qt.ItemDataRole.UserRole)
        if line_num is not None:
            self.heading_clicked.emit(line_num)


# ============================================================================
# 预览视图
# ============================================================================

class PreviewView(QWidget):
    """预览视图"""

    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            layout.addWidget(self.web_view)
            self._update_preview("")
        else:
            # 回退到 QTextEdit
            self.text_view = QTextEdit()
            self.text_view.setReadOnly(True)
            self.text_view.setFont(QFont("Segoe UI", 11))
            layout.addWidget(self.text_view)

    def _get_mathjax_script(self) -> str:
        """获取 MathJax 脚本"""
        return """
        <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true,
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            }
        };
        </script>
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
        """

    def _get_pygments_css(self) -> str:
        """获取 Pygments CSS"""
        if HAS_PYGMENTS:
            try:
                formatter = HtmlFormatter(style='monokai')
                return formatter.get_style_defs('.codehilite')
            except:
                pass
        return ""

    def _build_html(self, content: str) -> str:
        """构建完整 HTML"""
        pygments_css = self._get_pygments_css()

        extensions = [
            TableExtension(),
            FencedCodeExtension(),
            CodeHiliteExtension(
                css_class='codehilite',
                linenums=False,
                guess_lang=True,
                noclasses=False,
            ),
            TocExtension(permalink=True),
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.smarty',
        ]

        try:
            md = markdown.Markdown(extensions=extensions)
            html_content = md.convert(content)
        except Exception as e:
            html_content = f"<p style='color: red;'>渲染错误: {str(e)}</p>"

        bg = self.theme["preview_bg"]
        text_color = self.theme["text"]
        border_color = self.theme["border"]
        accent = self.theme["accent_start"]
        code_bg = self.theme["card"]
        link_color = self.theme["accent_start"]
        blockquote_bg = self.theme["card"]

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        font-size: 15px;
        line-height: 1.7;
        color: {text_color};
        background-color: {bg};
        padding: 20px 30px;
        max-width: 100%;
        margin: 0;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {accent};
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        font-weight: 600;
    }}
    h1 {{ font-size: 2em; border-bottom: 2px solid {border_color}; padding-bottom: 0.3em; }}
    h2 {{ font-size: 1.6em; border-bottom: 1px solid {border_color}; padding-bottom: 0.2em; }}
    h3 {{ font-size: 1.3em; }}
    h4 {{ font-size: 1.1em; }}
    p {{ margin: 0.8em 0; }}
    a {{ color: {link_color}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code {{
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: {code_bg};
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.9em;
        color: #ff8888;
    }}
    pre {{
        background-color: {code_bg};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        overflow-x: auto;
        margin: 1em 0;
    }}
    pre code {{
        background: none;
        padding: 0;
        color: {text_color};
        font-size: 0.85em;
    }}
    blockquote {{
        border-left: 4px solid {accent};
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: {blockquote_bg};
        border-radius: 0 4px 4px 0;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }}
    th, td {{
        border: 1px solid {border_color};
        padding: 8px 12px;
        text-align: left;
    }}
    th {{
        background-color: {code_bg};
        font-weight: 600;
    }}
    tr:nth-child(even) {{
        background-color: rgba(255,255,255,0.02);
    }}
    img {{
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }}
    ul, ol {{
        margin: 0.5em 0;
        padding-left: 2em;
    }}
    li {{ margin: 0.3em 0; }}
    hr {{
        border: none;
        border-top: 2px solid {border_color};
        margin: 2em 0;
    }}
    .codehilite {{
        background-color: {code_bg};
        border-radius: 8px;
        overflow: auto;
    }}
    {pygments_css}
    .toc {{
        background-color: {code_bg};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        margin: 1em 0;
    }}
</style>
{self._get_mathjax_script()}
</head>
<body>
{html_content}
</body>
</html>"""

    def update_preview(self, content: str):
        """更新预览"""
        if HAS_WEBENGINE:
            html = self._build_html(content)
            self.web_view.setHtml(html)
        else:
            # 简单文本预览
            self.text_view.setMarkdown(content)

    def update_theme(self, theme):
        """更新主题"""
        self.theme = theme
        if hasattr(self, 'text_view'):
            self.text_view.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {theme["preview_bg"]};
                    color: {theme["text"]};
                    border: none;
                }}
            """)


# ============================================================================
# 主窗口
# ============================================================================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.is_modified = False
        self.current_theme = DARK_THEME
        self.settings = QSettings("MarkdownEditor", "MarkdownEditor")

        self.setWindowTitle("📝 Markdown 编辑器")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._setup_ui()
        self._setup_toolbar()
        self._setup_menus()
        self._setup_shortcuts()
        self._apply_theme()

        # 恢复窗口状态
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self._center_window()

        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(300)
        self.update_timer.timeout.connect(self._update_preview)

        # 设置状态栏
        self.statusBar().showMessage("就绪")

    def _center_window(self):
        """居中窗口"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = (geometry.width() - self.width()) // 2
            y = (geometry.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 查找替换面板
        self.find_replace = FindReplaceWidget(None, self.current_theme, self)
        self.find_replace.hide()
        main_layout.addWidget(self.find_replace)

        # 主内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 大纲侧边栏
        self.outline_tree = OutlineTree(self.current_theme, self)
        self.outline_tree.setMinimumWidth(200)
        self.outline_tree.setMaximumWidth(300)
        self.outline_tree.heading_clicked.connect(self._goto_heading)
        content_layout.addWidget(self.outline_tree)

        # 分割器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 编辑器
        self.editor = MarkdownEditor(self.current_theme)
        self.editor.setPlaceholderText("在此输入 Markdown 内容...")
        self.editor.textChanged.connect(self._on_text_changed)
        self.splitter.addWidget(self.editor)

        # 预览
        self.preview = PreviewView(self.current_theme)
        self.splitter.addWidget(self.preview)

        self.splitter.setSizes([600, 600])
        content_layout.addWidget(self.splitter)

        main_layout.addWidget(content_widget)

        # 更新查找替换的编辑器引用
        self.find_replace.editor = self.editor

        # 加载默认内容
        self._load_default_content()

    def _setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # 文件操作
        toolbar.addAction("📄 新建", self.new_file)
        toolbar.addAction("📂 打开", self.open_file)
        toolbar.addAction("💾 保存", self.save_file)
        toolbar.addSeparator()

        # 编辑操作
        toolbar.addAction("↩ 撤销", self.editor.undo)
        toolbar.addAction("↪ 重做", self.editor.redo)
        toolbar.addSeparator()

        # 格式化
        toolbar.addAction("𝐁 加粗", self._insert_bold)
        toolbar.addAction("𝐼 斜体", self._insert_italic)
        toolbar.addAction("H1", lambda: self._insert_heading(1))
        toolbar.addAction("H2", lambda: self._insert_heading(2))
        toolbar.addAction("H3", lambda: self._insert_heading(3))
        toolbar.addSeparator()

        # 列表
        toolbar.addAction("• 列表", self._insert_unordered_list)
        toolbar.addAction("1. 有序", self._insert_ordered_list)
        toolbar.addAction("> 引用", self._insert_blockquote)
        toolbar.addAction("</> 代码", self._insert_code_block)
        toolbar.addSeparator()

        # 插入
        toolbar.addAction("🔗 链接", self._insert_link)
        toolbar.addAction("🖼 图片", self._insert_image)
        toolbar.addAction("📊 表格", self._insert_table)
        toolbar.addAction("∑ 公式", self._insert_math)
        toolbar.addSeparator()

        # 导出
        toolbar.addAction("📤 HTML", self.export_html)
        toolbar.addAction("📑 PDF", self.export_pdf)
        toolbar.addAction("📝 DOCX", self.export_docx)
        toolbar.addSeparator()

        # 主题切换
        self.theme_action = toolbar.addAction("🌙 深色主题", self.toggle_theme)

        # 切换大纲
        toolbar.addAction("📋 大纲", self._toggle_outline)

    def _setup_menus(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建(&N)", self.new_file, QKeySequence.StandardKey.New)
        file_menu.addAction("打开(&O)", self.open_file, QKeySequence.StandardKey.Open)
        file_menu.addAction("保存(&S)", self.save_file, QKeySequence.StandardKey.Save)
        file_menu.addAction("另存为(&A)", self.save_file_as, QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("导出(&E)")
        export_menu.addAction("导出 HTML", self.export_html, QKeySequence("Ctrl+E"))
        export_menu.addAction("导出 PDF", self.export_pdf, QKeySequence("Ctrl+Shift+E"))
        export_menu.addAction("导出 DOCX", self.export_docx)

        file_menu.addSeparator()
        file_menu.addAction("退出(&Q)", self.close, QKeySequence.StandardKey.Quit)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销(&U)", self.editor.undo, QKeySequence.StandardKey.Undo)
        edit_menu.addAction("重做(&R)", self.editor.redo, QKeySequence.StandardKey.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("查找(&F)", self._show_find, QKeySequence.StandardKey.Find)
        edit_menu.addAction("替换(&H)", self._show_replace, QKeySequence("Ctrl+H"))
        edit_menu.addSeparator()
        edit_menu.addAction("全选(&A)", self.editor.selectAll, QKeySequence.StandardKey.SelectAll)

        # 格式菜单
        format_menu = menubar.addMenu("格式(&O)")
        format_menu.addAction("加粗(&B)", self._insert_bold, QKeySequence("Ctrl+B"))
        format_menu.addAction("斜体(&I)", self._insert_italic, QKeySequence("Ctrl+I"))
        format_menu.addSeparator()
        format_menu.addAction("标题 1", lambda: self._insert_heading(1), QKeySequence("Ctrl+1"))
        format_menu.addAction("标题 2", lambda: self._insert_heading(2), QKeySequence("Ctrl+2"))
        format_menu.addAction("标题 3", lambda: self._insert_heading(3), QKeySequence("Ctrl+3"))
        format_menu.addSeparator()
        format_menu.addAction("无序列表", self._insert_unordered_list)
        format_menu.addAction("有序列表", self._insert_ordered_list)
        format_menu.addAction("引用块", self._insert_blockquote)
        format_menu.addAction("代码块", self._insert_code_block, QKeySequence("Ctrl+`"))
        format_menu.addSeparator()
        format_menu.addAction("链接", self._insert_link, QKeySequence("Ctrl+K"))
        format_menu.addAction("图片", self._insert_image)
        format_menu.addAction("表格", self._insert_table)
        format_menu.addAction("数学公式", self._insert_math)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        view_menu.addAction("切换主题", self.toggle_theme, QKeySequence("Ctrl+Shift+T"))
        view_menu.addAction("切换大纲", self._toggle_outline, QKeySequence("Ctrl+\\"))
        view_menu.addSeparator()
        view_menu.addAction("全屏", self._toggle_fullscreen, QKeySequence("F11"))

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于(&A)", self._show_about)
        help_menu.addAction("Markdown 语法帮助", self._show_help)

    def _setup_shortcuts(self):
        """设置快捷键"""
        # 额外快捷键
        QShortcut(QKeySequence("Ctrl+G"), self, self._goto_line)

    def _apply_theme(self):
        """应用主题"""
        theme = self.current_theme

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme["background"]};
            }}
            QMenuBar {{
                background-color: {theme["toolbar_bg"]};
                color: {theme["text"]};
                border-bottom: 1px solid {theme["border"]};
                padding: 2px;
            }}
            QMenuBar::item {{
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme["button_hover"]};
            }}
            QMenu {{
                background-color: {theme["card"]};
                color: {theme["text"]};
                border: 1px solid {theme["border"]};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme["button_hover"]};
            }}
            QToolBar {{
                background-color: {theme["toolbar_bg"]};
                border: none;
                padding: 4px;
                spacing: 4px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                color: {theme["text"]};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {theme["button_hover"]};
                border-color: {theme["border"]};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {theme["selection"]};
            }}
            QStatusBar {{
                background-color: {theme["toolbar_bg"]};
                color: {theme["text_secondary"]};
                border-top: 1px solid {theme["border"]};
            }}
            QSplitter::handle {{
                background-color: {theme["border"]};
                width: 2px;
            }}
            QScrollBar:vertical {{
                background-color: {theme["background"]};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme["scrollbar"]};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme["scrollbar_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background-color: {theme["background"]};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme["scrollbar"]};
                border-radius: 5px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme["scrollbar_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)

        # 更新子组件主题
        self.editor.update_theme(theme)
        self.preview.update_theme(theme)
        self.outline_tree.update_theme(theme)
        self.find_replace.update_theme(theme)

    def _load_default_content(self):
        """加载默认内容"""
        default_content = """# 📝 Markdown 编辑器

欢迎使用 **Markdown 编辑器**！这是一个功能强大的桌面编辑器。

## ✨ 功能特性

- 🎨 **语法高亮** - 支持 Markdown 语法高亮显示
- 👁 **实时预览** - 左侧编辑，右侧实时预览
- 📊 **表格编辑** - 可视化创建和编辑表格
- ∑ **数学公式** - 支持 LaTeX 数学公式渲染
- 🌙 **主题切换** - 深色/浅色主题一键切换

## 📊 表格示例

| 功能 | 状态 | 说明 |
|:-----|:----:|-----:|
| 编辑器 | ✅ | 支持语法高亮 |
| 预览 | ✅ | 实时渲染 |
| 导出 | ✅ | HTML/PDF/DOCX |

## ∑ 数学公式

行内公式：$E = mc^2$

块级公式：

$$\\sum_{i=1}^{n} x_i = x_1 + x_2 + ... + x_n$$

$$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

## 💻 代码块

```python
def hello_world():
    print("Hello, Markdown Editor!")
    return True
```

## 📝 引用

> 这是一段引用文本。
> Markdown 让写作变得简单而优雅。

---

**提示**: 使用工具栏按钮或快捷键来格式化文本！
"""
        self.editor.setPlainText(default_content)

    # ========================================================================
    # 文件操作
    # ========================================================================

    def new_file(self):
        """新建文件"""
        if self._check_save():
            self.editor.clear()
            self.current_file = None
            self.is_modified = False
            self.setWindowTitle("📝 Markdown 编辑器 - 新文件")
            self.statusBar().showMessage("已创建新文件")

    def open_file(self):
        """打开文件"""
        if not self._check_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "",
            "Markdown 文件 (*.md *.markdown *.txt);;所有文件 (*.*)"
        )
        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """加载文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = file_path
            self.is_modified = False
            self.setWindowTitle(f"📝 Markdown 编辑器 - {Path(file_path).name}")
            self.statusBar().showMessage(f"已打开: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")

    def save_file(self):
        """保存文件"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "",
            "Markdown 文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            self._save_to_file(file_path)

    def _save_to_file(self, file_path: str):
        """保存到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.current_file = file_path
            self.is_modified = False
            self.setWindowTitle(f"📝 Markdown 编辑器 - {Path(file_path).name}")
            self.statusBar().showMessage(f"已保存: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件:\n{str(e)}")

    def _check_save(self) -> bool:
        """检查是否需要保存"""
        if not self.is_modified:
            return True
        reply = QMessageBox.question(
            self, "保存文件",
            "文件已修改，是否保存？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            self.save_file()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    # ========================================================================
    # 导出功能
    # ========================================================================

    def export_html(self):
        """导出 HTML"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 HTML", "", "HTML 文件 (*.html)"
        )
        if file_path:
            try:
                content = self.editor.toPlainText()
                html = self.preview._build_html(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.statusBar().showMessage(f"已导出 HTML: {file_path}")
                QMessageBox.information(self, "导出成功", f"已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出错误", str(e))

    def export_pdf(self):
        """导出 PDF"""
        if not HAS_WEBENGINE:
            QMessageBox.warning(self, "功能不可用", "PDF 导出需要 PyQt6-WebEngine")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 PDF", "", "PDF 文件 (*.pdf)"
        )
        if file_path:
            try:
                content = self.editor.toPlainText()
                html = self.preview._build_html(content)

                def on_pdf_ready(path):
                    self.statusBar().showMessage(f"已导出 PDF: {path}")
                    QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")

                self.preview.web_view.setHtml(html)
                QTimer.singleShot(1000, lambda: self.preview.web_view.page().printToPdf(file_path))
                QTimer.singleShot(2000, lambda: on_pdf_ready(file_path))
            except Exception as e:
                QMessageBox.critical(self, "导出错误", str(e))

    def export_docx(self):
        """导出 DOCX"""
        try:
            import subprocess
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出 DOCX", "", "Word 文档 (*.docx)"
            )
            if file_path:
                # 先导出为 HTML，然后提示用户转换
                html_path = file_path.replace('.docx', '.html')
                content = self.editor.toPlainText()
                html = self.preview._build_html(content)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)

                reply = QMessageBox.information(
                    self, "导出提示",
                    f"已导出 HTML 文件:\n{html_path}\n\n"
                    "如需转换为 DOCX，请使用 pandoc:\n"
                    f"pandoc {html_path} -o {file_path}",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
                )
                if reply == QMessageBox.StandardButton.Open:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(html_path))
        except Exception as e:
            QMessageBox.critical(self, "导出错误", str(e))

    # ========================================================================
    # 格式化操作
    # ========================================================================

    def _insert_bold(self):
        """插入加粗"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"**{text}**")
        else:
            cursor.insertText("****")
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.Move, 2)
            self.editor.setTextCursor(cursor)

    def _insert_italic(self):
        """插入斜体"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"*{text}*")
        else:
            cursor.insertText("**")
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.Move, 1)
            self.editor.setTextCursor(cursor)

    def _insert_heading(self, level: int):
        """插入标题"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        # 移除现有的标题前缀
        line = cursor.block().text()
        cleaned = re.sub(r'^#{1,6}\s*', '', line)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(f"{'#' * level} {cleaned}")

    def _insert_unordered_list(self):
        """插入无序列表"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.insertText("- ")

    def _insert_ordered_list(self):
        """插入有序列表"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.insertText("1. ")

    def _insert_blockquote(self):
        """插入引用"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.insertText("> ")

    def _insert_code_block(self):
        """插入代码块"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"```\n{text}\n```")
        else:
            cursor.insertText("```\n\n```")
            cursor.movePosition(QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.Move, 1)
            self.editor.setTextCursor(cursor)

    def _insert_link(self):
        """插入链接"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"[{text}](url)")
        else:
            cursor.insertText("[链接文本](url)")
            # 选中 "链接文本"
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.Move, 6)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
            self.editor.setTextCursor(cursor)

    def _insert_image(self):
        """插入图片"""
        cursor = self.editor.textCursor()
        cursor.insertText("![图片描述](图片路径)")

    def _insert_table(self):
        """插入表格"""
        dialog = TableEditorDialog(self, self.current_theme)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_md = dialog.get_table_markdown()
            cursor = self.editor.textCursor()
            cursor.insertText("\n" + table_md + "\n")

    def _insert_math(self):
        """插入数学公式"""
        dialog = MathInputDialog(self, self.current_theme)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            formula = dialog.get_formula()
            if formula:
                cursor = self.editor.textCursor()
                cursor.insertText(formula)

    # ========================================================================
    # 视图操作
    # ========================================================================

    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == DARK_THEME:
            self.current_theme = LIGHT_THEME
            self.theme_action.setText("☀ 浅色主题")
        else:
            self.current_theme = DARK_THEME
            self.theme_action.setText("🌙 深色主题")
        self._apply_theme()
        self._update_preview()

    def _toggle_outline(self):
        """切换大纲显示"""
        self.outline_tree.setVisible(not self.outline_tree.isVisible())

    def _toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_find(self):
        """显示查找"""
        self.find_replace.show()
        self.find_replace.find_input.setFocus()
        self.find_replace.find_input.selectAll()

    def _show_replace(self):
        """显示替换"""
        self.find_replace.show()
        self.find_replace.replace_input.setFocus()

    def _goto_heading(self, line_num: int):
        """跳转到标题"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.Move, line_num)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _goto_line(self):
        """跳转到行"""
        from PyQt6.QtWidgets import QInputDialog
        line, ok = QInputDialog.getInt(self, "跳转到行", "行号:", 1, 1, self.editor.document().blockCount())
        if ok:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.Move, line - 1)
            self.editor.setTextCursor(cursor)

    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于 Markdown 编辑器",
            "<h2>📝 Markdown 编辑器</h2>"
            "<p>版本 1.0.0</p>"
            "<p>一款专业的桌面 Markdown 编辑器，支持实时预览、数学公式、表格编辑等高级功能。</p>"
            "<p>基于 PyQt6 构建</p>"
            "<hr>"
            "<p>© 2024 MarkdownEditor Team</p>"
        )

    def _show_help(self):
        """显示帮助"""
        help_content = """# Markdown 语法帮助

## 标题
# 一级标题
## 二级标题
### 三级标题

## 强调
**加粗文本**
*斜体文本*
~~删除线~~

## 列表
- 无序列表项
1. 有序列表项

## 链接和图片
[链接文本](URL)
![图片描述](图片路径)

## 代码
`行内代码`
```语言
代码块
```

## 引用
> 引用文本

## 表格
| 列1 | 列2 |
|-----|-----|
| 内容 | 内容 |

## 数学公式
行内: $E = mc^2$
块级: $$\\sum_{i=1}^{n} x_i$$

## 分隔线
---
"""
        self.editor.setPlainText(help_content)

    # ========================================================================
    # 事件处理
    # ========================================================================

    def _on_text_changed(self):
        """文本改变"""
        self.is_modified = True
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + "*")
        self.update_timer.start()

        # 更新大纲
        self.outline_tree.update_outline(self.editor.toPlainText())

        # 更新状态栏
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        total_lines = self.editor.document().blockCount()
        word_count = len(self.editor.toPlainText().split())
        char_count = len(self.editor.toPlainText())
        self.statusBar().showMessage(
            f"行: {line}/{total_lines}  列: {col}  "
            f"字数: {word_count}  字符: {char_count}"
        )

    def _update_preview(self):
        """更新预览"""
        content = self.editor.toPlainText()
        self.preview.update_preview(content)

    def closeEvent(self, event):
        """关闭事件"""
        self.settings.setValue("geometry", self.saveGeometry())
        if self._check_save():
            event.accept()
        else:
            event.ignore()


# ============================================================================
# 程序入口
# ============================================================================

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Markdown 编辑器")
    app.setOrganizationName("MarkdownEditor")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
