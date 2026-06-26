"""
TextEditor - 一个轻量级的代码编辑器
支持语法高亮、多标签页、代码缩略图等功能
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPlainTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QMenuBar, QMenu, QFileDialog,
    QMessageBox, QDialog, QLabel, QLineEdit, QCheckBox, QPushButton,
    QComboBox, QStatusBar, QSplitter, QFrame, QScrollArea, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QToolBar, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import (
    Qt, QRect, QSize, QTimer, pyqtSignal, QRegularExpression,
    QPointF, QRectF
)
from PyQt6.QtGui import (
    QColor, QPainter, QFont, QTextFormat, QSyntaxHighlighter,
    QTextCharFormat, QTextCursor, QKeySequence, QAction, QPalette,
    QLinearGradient, QBrush, QPen, QPixmap, QFontMetrics, QTextDocument,
    QIcon, QPaintEvent, QResizeEvent, QTextBlock
)


# ═══════════════════════════════════════════════════════════
# 颜色主题配置
# ═══════════════════════════════════════════════════════════
class Theme:
    BG_DARK = "#0a0a0a"
    CARD_BG = "#111122"
    ACCENT_START = "#667eea"
    ACCENT_END = "#764ba2"
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#888888"
    LINE_NUM_BG = "#0d0d1a"
    LINE_NUM_FG = "#444466"
    SELECTION_BG = "#2a2a4a"
    CURRENT_LINE = "#151530"
    BORDER = "#1a1a3a"
    TAB_ACTIVE = "#181838"
    TAB_INACTIVE = "#0e0e20"
    MENU_BG = "#0c0c1e"
    STATUS_BG = "#08081a"
    MINIMAP_BG = "#0b0b1c"

    # 语法高亮颜色
    SYNTAX_KEYWORD = "#c792ea"
    SYNTAX_STRING = "#c3e88d"
    SYNTAX_COMMENT = "#546e7a"
    SYNTAX_FUNCTION = "#82aaff"
    SYNTAX_NUMBER = "#f78c6c"
    SYNTAX_OPERATOR = "#89ddff"
    SYNTAX_CLASS = "#ffcb6b"
    SYNTAX_TAG = "#f07178"
    SYNTAX_ATTR = "#ffcb6b"
    SYNTAX_BUILTIN = "#82aaff"
    SYNTAX_DECORATOR = "#c792ea"
    SYNTAX_HEADING = "#c792ea"
    SYNTAX_LINK = "#82aaff"
    SYNTAX_BOLD = "#ffcb6b"
    SYNTAX_CODE = "#c3e88d"


# ═══════════════════════════════════════════════════════════
# 语法高亮器
# ═══════════════════════════════════════════════════════════
class HighlightRule:
    """语法规则"""
    def __init__(self, pattern: str, fmt: QTextCharFormat, group: int = 0):
        self.pattern = QRegularExpression(pattern)
        self.format = fmt
        self.group = group


class PythonHighlighter(QSyntaxHighlighter):
    """Python 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        kw_fmt = self._make_format(Theme.SYNTAX_KEYWORD, bold=True)
        keywords = [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
            'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
            'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
            'True', 'False', 'None'
        ]
        for kw in keywords:
            self.rules.append(HighlightRule(r'\b' + kw + r'\b', kw_fmt))

        builtin_fmt = self._make_format(Theme.SYNTAX_BUILTIN)
        builtins = [
            'print', 'len', 'range', 'int', 'str', 'float', 'list', 'dict',
            'set', 'tuple', 'bool', 'type', 'isinstance', 'issubclass', 'super',
            'property', 'staticmethod', 'classmethod', 'enumerate', 'zip', 'map',
            'filter', 'sorted', 'reversed', 'any', 'all', 'min', 'max', 'sum',
            'abs', 'round', 'open', 'input', 'format', 'id', 'hash', 'repr',
            'dir', 'vars', 'hasattr', 'getattr', 'setattr', 'delattr', 'callable',
            'iter', 'next', 'slice', 'object', 'Exception', 'ValueError',
            'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'ImportError', 'FileNotFoundError', 'RuntimeError', 'StopIteration'
        ]
        for b in builtins:
            self.rules.append(HighlightRule(r'\b' + b + r'\b', builtin_fmt))

        self.rules.append(HighlightRule(r'\bdef\s+(\w+)', self._make_format(Theme.SYNTAX_FUNCTION, bold=True), 1))
        self.rules.append(HighlightRule(r'\bclass\s+(\w+)', self._make_format(Theme.SYNTAX_CLASS, bold=True), 1))
        self.rules.append(HighlightRule(r'@\w+', self._make_format(Theme.SYNTAX_DECORATOR)))
        self.rules.append(HighlightRule(r'\bself\b', self._make_format(Theme.SYNTAX_KEYWORD, italic=True)))

        self.rules.append(HighlightRule(r'#[^\n]*', self._make_format(Theme.SYNTAX_COMMENT, italic=True)))
        self.rules.append(HighlightRule(r'""".*?"""', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"'''.*?'''", self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'f"[^"\\]*(\\.[^"\\]*)*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"b?'[^'\\]*(\\.[^'\\]*)*'", self._make_format(Theme.SYNTAX_STRING)))

        self.rules.append(HighlightRule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'0x[0-9a-fA-F]+', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'0b[01]+', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'0o[0-7]+', self._make_format(Theme.SYNTAX_NUMBER)))

        self.rules.append(HighlightRule(r'[+\-*/%=<>!&|^~]+', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'[{}()\[\]:;,\.]', self._make_format(Theme.SYNTAX_OPERATOR)))

        self.tri_single = QRegularExpression("'''")
        self.tri_double = QRegularExpression('"""')

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                if rule.group > 0:
                    start = match.capturedStart(rule.group)
                    length = match.capturedLength(rule.group)
                else:
                    start = match.capturedStart()
                    length = match.capturedLength()
                self.setFormat(start, length, rule.format)

        self.setCurrentBlockState(0)
        self._highlight_multiline(text, self.tri_single, 1)
        self._highlight_multiline(text, self.tri_double, 2)

    def _highlight_multiline(self, text: str, delim: QRegularExpression, state: int):
        if self.previousBlockState() == state:
            start = 0
            add = 0
        else:
            match = delim.match(text)
            if not match.hasMatch():
                return
            start = match.capturedStart()
            add = match.capturedLength()

        while start >= 0:
            end_match = delim.match(text, start + add)
            if end_match.hasMatch():
                end = end_match.capturedEnd()
                length = end - start
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(state)
                length = len(text) - start

            fmt = QTextCharFormat()
            fmt.setForeground(QColor(Theme.SYNTAX_STRING))
            self.setFormat(start, length, fmt)

            if self.currentBlockState() == state:
                break

            match = delim.match(text, start + length)
            if match.hasMatch():
                start = match.capturedStart()
                add = match.capturedLength()
            else:
                break


class JavaScriptHighlighter(QSyntaxHighlighter):
    """JavaScript 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        kw_fmt = self._make_format(Theme.SYNTAX_KEYWORD, bold=True)
        keywords = [
            'async', 'await', 'break', 'case', 'catch', 'class', 'const',
            'continue', 'debugger', 'default', 'delete', 'do', 'else',
            'export', 'extends', 'finally', 'for', 'function', 'if',
            'import', 'in', 'instanceof', 'let', 'new', 'of', 'return',
            'static', 'super', 'switch', 'this', 'throw', 'try', 'typeof',
            'var', 'void', 'while', 'with', 'yield', 'true', 'false', 'null',
            'undefined', 'NaN', 'Infinity'
        ]
        for kw in keywords:
            self.rules.append(HighlightRule(r'\b' + kw + r'\b', kw_fmt))

        builtin_fmt = self._make_format(Theme.SYNTAX_BUILTIN)
        builtins = [
            'console', 'window', 'document', 'Math', 'JSON', 'Array',
            'Object', 'String', 'Number', 'Boolean', 'Date', 'RegExp',
            'Map', 'Set', 'WeakMap', 'WeakSet', 'Promise', 'Symbol',
            'Error', 'TypeError', 'RangeError', 'SyntaxError',
            'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURI',
            'decodeURI', 'setTimeout', 'setInterval', 'clearTimeout',
            'clearInterval', 'fetch', 'alert', 'confirm', 'prompt'
        ]
        for b in builtins:
            self.rules.append(HighlightRule(r'\b' + b + r'\b', builtin_fmt))

        self.rules.append(HighlightRule(r'\b(function)\s+(\w+)', self._make_format(Theme.SYNTAX_KEYWORD, bold=True), 1))
        self.rules.append(HighlightRule(r'\b(function)\s+(\w+)', self._make_format(Theme.SYNTAX_FUNCTION, bold=True), 2))
        self.rules.append(HighlightRule(r'(?<=\.)\w+(?=\s*\()', self._make_format(Theme.SYNTAX_FUNCTION)))
        self.rules.append(HighlightRule(r'(?<=\.)\w+(?!\s*[(:])', self._make_format(Theme.SYNTAX_ATTR)))

        self.rules.append(HighlightRule(r'//[^\n]*', self._make_format(Theme.SYNTAX_COMMENT, italic=True)))
        self.rules.append(HighlightRule(r'/\*.*?\*/', self._make_format(Theme.SYNTAX_COMMENT, italic=True)))
        self.rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'`[^`\\]*(\\.[^`\\]*)*`', self._make_format(Theme.SYNTAX_STRING)))

        self.rules.append(HighlightRule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'0x[0-9a-fA-F]+', self._make_format(Theme.SYNTAX_NUMBER)))

        self.rules.append(HighlightRule(r'[+\-*/%=<>!&|^~?:]+', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'[{}()\[\]:;,\.]', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'=>', self._make_format(Theme.SYNTAX_OPERATOR)))

        self.comment_start = QRegularExpression(r'/\*')
        self.comment_end = QRegularExpression(r'\*/')

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                if rule.group > 0:
                    start = match.capturedStart(rule.group)
                    length = match.capturedLength(rule.group)
                else:
                    start = match.capturedStart()
                    length = match.capturedLength()
                self.setFormat(start, length, rule.format)

        self.setCurrentBlockState(0)
        self._highlight_block_comment(text)

    def _highlight_block_comment(self, text: str):
        if self.previousBlockState() == 1:
            start = 0
            add = 0
        else:
            match = self.comment_start.match(text)
            if not match.hasMatch():
                return
            start = match.capturedStart()
            add = match.capturedLength()

        while start >= 0:
            end_match = self.comment_end.match(text, start + add)
            if end_match.hasMatch():
                end = end_match.capturedEnd()
                length = end - start
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
                length = len(text) - start

            fmt = QTextCharFormat()
            fmt.setForeground(QColor(Theme.SYNTAX_COMMENT))
            fmt.setFontItalic(True)
            self.setFormat(start, length, fmt)

            if self.currentBlockState() == 1:
                break

            match = self.comment_start.match(text, start + length)
            if match.hasMatch():
                start = match.capturedStart()
                add = match.capturedLength()
            else:
                break


class HtmlHighlighter(QSyntaxHighlighter):
    """HTML 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def _setup_rules(self):
        self.rules.append(HighlightRule(r'<!--.*?-->', self._make_format(Theme.SYNTAX_COMMENT)))
        self.rules.append(HighlightRule(r'</?\w+', self._make_format(Theme.SYNTAX_TAG, bold=True)))
        self.rules.append(HighlightRule(r'(?<=\s)\w+(?==)', self._make_format(Theme.SYNTAX_ATTR)))
        self.rules.append(HighlightRule(r'"[^"]*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"'[^']*'", self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'&\w+;', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'[<>/?!=]', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'\bDOCTYPE\b', self._make_format(Theme.SYNTAX_KEYWORD, bold=True)))

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class CssHighlighter(QSyntaxHighlighter):
    """CSS 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def _setup_rules(self):
        self.rules.append(HighlightRule(r'/\*.*?\*/', self._make_format(Theme.SYNTAX_COMMENT)))
        self.rules.append(HighlightRule(r'[.#][\w-]+', self._make_format(Theme.SYNTAX_TAG, bold=True)))
        self.rules.append(HighlightRule(r'@[\w-]+', self._make_format(Theme.SYNTAX_KEYWORD, bold=True)))
        self.rules.append(HighlightRule(r'[\w-]+(?=\s*:)', self._make_format(Theme.SYNTAX_ATTR)))
        self.rules.append(HighlightRule(r':[\w-]+', self._make_format(Theme.SYNTAX_FUNCTION)))
        self.rules.append(HighlightRule(r'"[^"]*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r"'[^']*'", self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'\b\d+\.?\d*(px|em|rem|%|vh|vw|s|ms|deg|fr)?\b', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'#[0-9a-fA-F]{3,8}\b', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'[{}();:,]', self._make_format(Theme.SYNTAX_OPERATOR)))

        css_props = [
            'color', 'background', 'margin', 'padding', 'border', 'display',
            'position', 'width', 'height', 'font', 'text', 'flex', 'grid',
            'align', 'justify', 'overflow', 'z-index', 'opacity', 'transform',
            'transition', 'animation', 'cursor', 'box-shadow', 'border-radius'
        ]
        for p in css_props:
            self.rules.append(HighlightRule(r'\b' + p + r'\b', self._make_format(Theme.SYNTAX_ATTR)))

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class JsonHighlighter(QSyntaxHighlighter):
    """JSON 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def _setup_rules(self):
        self.rules.append(HighlightRule(r'"[^"]*"\s*(?=:)', self._make_format(Theme.SYNTAX_ATTR, bold=True)))
        self.rules.append(HighlightRule(r'"[^"]*"', self._make_format(Theme.SYNTAX_STRING)))
        self.rules.append(HighlightRule(r'\b(true|false|null)\b', self._make_format(Theme.SYNTAX_KEYWORD, bold=True)))
        self.rules.append(HighlightRule(r'\b-?\d+\.?\d*([eE][+-]?\d+)?\b', self._make_format(Theme.SYNTAX_NUMBER)))
        self.rules.append(HighlightRule(r'[{}()\[\]:,]', self._make_format(Theme.SYNTAX_OPERATOR)))

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 语法高亮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[HighlightRule] = []
        self._setup_rules()

    def _make_format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        self.rules.append(HighlightRule(r'^#{1,6}\s+.*$', self._make_format(Theme.SYNTAX_HEADING, bold=True)))
        self.rules.append(HighlightRule(r'\*\*[^*]+\*\*', self._make_format(Theme.SYNTAX_BOLD, bold=True)))
        self.rules.append(HighlightRule(r'__[^_]+__', self._make_format(Theme.SYNTAX_BOLD, bold=True)))
        self.rules.append(HighlightRule(r'(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)', self._make_format(Theme.SYNTAX_COMMENT, italic=True)))
        self.rules.append(HighlightRule(r'(?<!_)_(?!_)([^_]+)(?<!_)_(?!_)', self._make_format(Theme.SYNTAX_COMMENT, italic=True)))
        self.rules.append(HighlightRule(r'`[^`]+`', self._make_format(Theme.SYNTAX_CODE)))
        self.rules.append(HighlightRule(r'```[\s\S]*?```', self._make_format(Theme.SYNTAX_CODE)))
        self.rules.append(HighlightRule(r'\[([^\]]+)\]\([^)]+\)', self._make_format(Theme.SYNTAX_LINK)))
        self.rules.append(HighlightRule(r'!\[([^\]]*)\]\([^)]+\)', self._make_format(Theme.SYNTAX_LINK)))
        self.rules.append(HighlightRule(r'^\s*[-*+]\s', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'^\s*\d+\.\s', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'^>\s.*$', self._make_format(Theme.SYNTAX_STRING, italic=True)))
        self.rules.append(HighlightRule(r'~~[^~]+~~', self._make_format(Theme.SYNTAX_COMMENT)))
        self.rules.append(HighlightRule(r'^---$', self._make_format(Theme.SYNTAX_OPERATOR)))
        self.rules.append(HighlightRule(r'^\*\*\*$', self._make_format(Theme.SYNTAX_OPERATOR)))

    def highlightBlock(self, text: str):
        for rule in self.rules:
            it = rule.pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                if rule.group > 0:
                    start = match.capturedStart(rule.group)
                    length = match.capturedLength(rule.group)
                else:
                    start = match.capturedStart()
                    length = match.capturedLength()
                self.setFormat(start, length, rule.format)


# ═══════════════════════════════════════════════════════════
# 行号区域
# ═══════════════════════════════════════════════════════════
class LineNumberArea(QWidget):
    """行号显示区域"""
    def __init__(self, editor: 'CodeEditor'):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent):
        self.editor.line_number_area_paint_event(event)


# ═══════════════════════════════════════════════════════════
# 代码编辑器
# ═══════════════════════════════════════════════════════════
class CodeEditor(QPlainTextEdit):
    """自定义代码编辑器"""
    content_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter: Optional[QSyntaxHighlighter] = None
        self._word_wrap = False
        self._auto_indent = True

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                padding-left: 8px;
                selection-background-color: {Theme.SELECTION_BG};
                selection-color: {Theme.TEXT_PRIMARY};
            }}
        """)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCursorWidth(2)

    def _connect_signals(self):
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self.content_changed.emit()

    def set_word_wrap(self, wrap: bool):
        self._word_wrap = wrap
        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth if wrap
            else QPlainTextEdit.LineWrapMode.NoWrap
        )

    def set_highlighter(self, highlighter: QSyntaxHighlighter):
        if self.highlighter:
            self.highlighter.setDocument(None)
        self.highlighter = highlighter
        if highlighter:
            highlighter.setDocument(self.document())

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(max(1, self.blockCount()))))
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event: QPaintEvent):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(Theme.LINE_NUM_BG))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_line:
                    painter.setPen(QColor(Theme.ACCENT_START))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor(Theme.LINE_NUM_FG))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                painter.drawText(
                    0, top, self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

        painter.end()

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setPen(QColor(Theme.CURRENT_LINE).lighter(120))

        cursor = self.textCursor()
        block = cursor.block()
        if block.isValid():
            rect = self.blockBoundingGeometry(block).translated(self.contentOffset())
            painter.drawLine(
                int(rect.left()), int(rect.bottom()),
                int(self.viewport().width()), int(rect.bottom())
            )
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab and not event.modifiers():
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor, indent=True)
            else:
                cursor.insertText("    ")
            return
        elif event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self._indent_selection(cursor, indent=False)
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self._auto_indent:
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            indent = ""
            for ch in text:
                if ch in (' ', '\t'):
                    indent += ch
                else:
                    break
            if text.rstrip().endswith(':'):
                indent += "    "
            super().keyPressEvent(event)
            cursor = self.textCursor()
            cursor.insertText(indent)
            return

        super().keyPressEvent(event)

    def _indent_selection(self, cursor: QTextCursor, indent: bool):
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
                line = cursor.block().text()
                if line.startswith("    "):
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.MoveAnchor)
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.insertText(line[4:])
                elif line.startswith("\t"):
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.MoveAnchor)
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.insertText(line[1:])

            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)

        cursor.endEditBlock()


# ═══════════════════════════════════════════════════════════
# 缩略图组件
# ═══════════════════════════════════════════════════════════
class MinimapWidget(QWidget):
    """代码缩略图"""
    def __init__(self, editor: CodeEditor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setFixedWidth(120)
        self._scale = 0.15
        self._scroll_offset = 0.0
        self._dragging = False

        self.editor.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.editor.textChanged.connect(self.update)
        self.editor.updateRequest.connect(lambda: self.update())

    def _on_scroll(self, value):
        self._scroll_offset = value
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(Theme.MINIMAP_BG))

        doc = self.editor.document()
        font = QFont("Consolas", 2)
        metrics = QFontMetrics(font)

        block = doc.begin()
        y = 2
        char_w = metrics.horizontalAdvance('M')
        char_h = metrics.height()

        while block.isValid():
            if block.isVisible():
                text = block.text()
                x = 2
                for i, ch in enumerate(text):
                    if not ch.isspace():
                        painter.fillRect(
                            int(x), int(y),
                            max(1, int(char_w * 0.8)),
                            max(1, int(char_h * 0.6)),
                            QColor(Theme.TEXT_SECONDARY).lighter(80)
                        )
                    x += char_w * 0.6
                y += char_h * 0.8
            block = block.next()

        viewport_height = self.editor.viewport().height()
        doc_height = self.editor.verticalScrollBar().maximum() + viewport_height
        if doc_height > 0:
            visible_ratio = viewport_height / doc_height
            scroll_ratio = self.editor.verticalScrollBar().value() / max(1, self.editor.verticalScrollBar().maximum())

            view_h = max(20, int(self.height() * visible_ratio))
            view_y = int(scroll_ratio * (self.height() - view_h))

            painter.setPen(QPen(QColor(Theme.ACCENT_START), 1.5))
            painter.setBrush(QBrush(QColor(Theme.ACCENT_START + "20")))
            painter.drawRect(0, view_y, self.width() - 1, view_h)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._scroll_to_position(event.position().y())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._scroll_to_position(event.position().y())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _scroll_to_position(self, y: float):
        ratio = y / max(1, self.height())
        scrollbar = self.editor.verticalScrollBar()
        scrollbar.setValue(int(ratio * scrollbar.maximum()))


# ═══════════════════════════════════════════════════════════
# 查找替换对话框
# ═══════════════════════════════════════════════════════════
class FindReplaceDialog(QDialog):
    """查找替换对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor: Optional[CodeEditor] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("查找与替换")
        self.setFixedSize(480, 200)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.CARD_BG};
                color: {Theme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                font-family: Consolas;
            }}
            QLineEdit:focus {{
                border: 1px solid {Theme.ACCENT_START};
            }}
            QPushButton {{
                background-color: {Theme.TAB_ACTIVE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_START};
                border: 1px solid {Theme.ACCENT_START};
            }}
            QCheckBox {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 11px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入搜索内容...")
        find_row.addWidget(self.find_input)
        layout.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("替换:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("输入替换内容...")
        replace_row.addWidget(self.replace_input)
        layout.addLayout(replace_row)

        options_row = QHBoxLayout()
        self.case_check = QCheckBox("区分大小写")
        self.whole_word_check = QCheckBox("全词匹配")
        self.regex_check = QCheckBox("正则表达式")
        options_row.addWidget(self.case_check)
        options_row.addWidget(self.whole_word_check)
        options_row.addWidget(self.regex_check)
        options_row.addStretch()
        layout.addLayout(options_row)

        btn_row = QHBoxLayout()
        self.find_btn = QPushButton("查找下一个")
        self.find_btn.clicked.connect(self.find_next)
        self.replace_btn = QPushButton("替换")
        self.replace_btn.clicked.connect(self.replace_current)
        self.replace_all_btn = QPushButton("全部替换")
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.find_btn)
        btn_row.addWidget(self.replace_btn)
        btn_row.addWidget(self.replace_all_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.status_label)

    def set_editor(self, editor: CodeEditor):
        self.editor = editor

    def _get_search_flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case_check.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_word_check.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        return flags

    def find_next(self):
        if not self.editor:
            return
        text = self.find_input.text()
        if not text:
            return

        flags = self._get_search_flags()

        if self.regex_check.isChecked():
            regex = QRegularExpression(text)
            if not regex.isValid():
                self.status_label.setText("无效的正则表达式")
                return
            cursor = self.editor.document().find(regex, self.editor.textCursor(), flags)
        else:
            cursor = self.editor.document().find(text, self.editor.textCursor(), flags)

        if cursor.isNull():
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            if self.regex_check.isChecked():
                cursor = self.editor.document().find(QRegularExpression(text), cursor, flags)
            else:
                cursor = self.editor.document().find(text, cursor, flags)

        if cursor.isNull():
            self.status_label.setText("未找到匹配内容")
        else:
            self.editor.setTextCursor(cursor)
            self.status_label.setText("")

    def replace_current(self):
        if not self.editor:
            return
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        if not self.editor:
            return
        text = self.find_input.text()
        replacement = self.replace_input.text()
        if not text:
            return

        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

        flags = self._get_search_flags()
        count = 0

        if self.regex_check.isChecked():
            regex = QRegularExpression(text)
            if not regex.isValid():
                self.status_label.setText("无效的正则表达式")
                cursor.endEditBlock()
                return
            cursor = self.editor.document().find(regex, self.editor.textCursor(), flags)
        else:
            cursor = self.editor.document().find(text, self.editor.textCursor(), flags)

        while not cursor.isNull():
            cursor.insertText(replacement)
            count += 1
            if self.regex_check.isChecked():
                cursor = self.editor.document().find(QRegularExpression(text), cursor, flags)
            else:
                cursor = self.editor.document().find(text, cursor, flags)

        cursor.endEditBlock()
        self.status_label.setText(f"已替换 {count} 处")


# ═══════════════════════════════════════════════════════════
# 标签页组件
# ═══════════════════════════════════════════════════════════
class EditorTab(QWidget):
    """编辑器标签页"""
    def __init__(self, file_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.encoding = "utf-8"
        self.is_modified = False
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(30000)  # 30秒自动保存

        self._setup_ui()

        if file_path:
            self.load_file(file_path)
        else:
            self._apply_highlighter()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = CodeEditor()
        self.editor.content_changed.connect(self._on_content_changed)

        self.minimap = MinimapWidget(self.editor)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.minimap)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([800, 120])

        layout.addWidget(splitter)

    def _on_content_changed(self):
        self.is_modified = True
        main_win = self.window()
        if hasattr(main_win, 'update_tab_title'):
            main_win.update_tab_title(self)

    def _auto_save(self):
        if self.is_modified and self.file_path:
            self.save_file()

    def _get_highlighter_for_file(self, file_path: str) -> QSyntaxHighlighter:
        ext = Path(file_path).suffix.lower()
        highlighters = {
            '.py': PythonHighlighter,
            '.js': JavaScriptHighlighter,
            '.jsx': JavaScriptHighlighter,
            '.ts': JavaScriptHighlighter,
            '.tsx': JavaScriptHighlighter,
            '.html': HtmlHighlighter,
            '.htm': HtmlHighlighter,
            '.xml': HtmlHighlighter,
            '.css': CssHighlighter,
            '.scss': CssHighlighter,
            '.less': CssHighlighter,
            '.json': JsonHighlighter,
            '.md': MarkdownHighlighter,
            '.markdown': MarkdownHighlighter,
            '.rst': MarkdownHighlighter,
        }
        cls = highlighters.get(ext)
        if cls:
            return cls(self.editor.document())
        return None

    def _apply_highlighter(self):
        if self.file_path:
            hl = self._get_highlighter_for_file(self.file_path)
            if hl:
                self.editor.set_highlighter(hl)

    def load_file(self, file_path: str, encoding: str = "utf-8"):
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            self.file_path = file_path
            self.encoding = encoding
            self.editor.setPlainText(content)
            self._apply_highlighter()
            self.is_modified = False
            return True
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                self.file_path = file_path
                self.encoding = 'gbk'
                self.editor.setPlainText(content)
                self._apply_highlighter()
                self.is_modified = False
                return True
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法读取文件: {e}")
                return False
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件: {e}")
            return False

    def save_file(self, file_path: Optional[str] = None, encoding: Optional[str] = None):
        path = file_path or self.file_path
        enc = encoding or self.encoding
        if not path:
            return False
        try:
            with open(path, 'w', encoding=enc) as f:
                f.write(self.editor.toPlainText())
            self.file_path = path
            self.encoding = enc
            self.is_modified = False
            main_win = self.window()
            if hasattr(main_win, 'update_tab_title'):
                main_win.update_tab_title(self)
            return True
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法保存文件: {e}")
            return False

    def export_html(self, output_path: str):
        """导出为带语法高亮的 HTML"""
        doc = self.editor.document()
        blocks = []
        block = doc.begin()

        while block.isValid():
            layout = block.layout()
            if layout:
                line_text = block.text()
                spans = []
                it = block.begin()
                while not it.atEnd():
                    fragment = it.fragment()
                    if fragment.isValid():
                        fmt = fragment.format()
                        color = fmt.foreground().color().name() if fmt.foreground().style() != Qt.BrushStyle.NoBrush else Theme.TEXT_PRIMARY
                        text = fragment.text()
                        spans.append((text, color))
                    it += 1
                blocks.append(spans)
            block = block.next()

        html_lines = []
        for line_spans in blocks:
            line_html = ""
            for text, color in line_spans:
                escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                line_html += f'<span style="color: {color}">{escaped}</span>'
            html_lines.append(line_html)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="{self.encoding}">
    <title>{Path(self.file_path).name if self.file_path else '未命名'}</title>
    <style>
        body {{
            background-color: {Theme.BG_DARK};
            color: {Theme.TEXT_PRIMARY};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            padding: 20px;
            margin: 0;
        }}
        pre {{
            margin: 0;
            white-space: pre-wrap;
        }}
        .line-number {{
            color: {Theme.LINE_NUM_FG};
            user-select: none;
            display: inline-block;
            width: 50px;
            text-align: right;
            margin-right: 20px;
        }}
        .line {{
            display: block;
        }}
    </style>
</head>
<body>
<pre>"""

        for i, line_html in enumerate(html_lines, 1):
            html_content += f'<span class="line"><span class="line-number">{i}</span>{line_html}</span>\n'

        html_content += """</pre>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


# ═══════════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════════
class TextEditorMainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.recent_files: List[str] = []
        self.max_recent_files = 15
        self._config_path = Path.home() / ".texteditor_config.json"

        self._load_config()
        self._setup_window()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()

        self.new_file()

    def _setup_window(self):
        self.setWindowTitle("TextEditor - 代码编辑器")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tab_widget)

        self._apply_tab_style()

    def _apply_tab_style(self):
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Theme.BG_DARK};
            }}
            QTabBar::tab {{
                background-color: {Theme.TAB_INACTIVE};
                color: {Theme.TEXT_SECONDARY};
                padding: 8px 20px;
                margin-right: 1px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 12px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.TAB_ACTIVE};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 2px solid {Theme.ACCENT_START};
            }}
            QTabBar::tab:hover {{
                background-color: {Theme.TAB_ACTIVE};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTabBar::close-button {{
                image: none;
                subcontrol-position: right;
            }}
            QTabBar {{
                background-color: {Theme.CARD_BG};
            }}
        """)

    def _setup_menus(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {Theme.MENU_BG};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 1px solid {Theme.BORDER};
                padding: 2px 8px;
            }}
            QMenuBar::item:selected {{
                background-color: {Theme.TAB_ACTIVE};
            }}
            QMenu {{
                background-color: {Theme.CARD_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 30px 6px 20px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.ACCENT_START};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.BORDER};
                margin: 4px 10px;
            }}
        """)

        file_menu = menubar.addMenu("文件(&F)")
        self._add_action(file_menu, "新建文件(&N)", "Ctrl+N", self.new_file)
        self._add_action(file_menu, "打开文件(&O)...", "Ctrl+O", self.open_file)
        self._add_action(file_menu, "保存(&S)", "Ctrl+S", self.save_file)
        self._add_action(file_menu, "另存为(&A)...", "Ctrl+Shift+S", self.save_file_as)
        file_menu.addSeparator()

        self.recent_menu = file_menu.addMenu("最近文件(&R)")
        self._update_recent_menu()

        file_menu.addSeparator()
        self._add_action(file_menu, "导出为 HTML(&E)...", "Ctrl+Shift+E", self.export_html)
        file_menu.addSeparator()
        self._add_action(file_menu, "关闭标签页(&W)", "Ctrl+W", self.close_current_tab)
        self._add_action(file_menu, "退出(&Q)", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("编辑(&E)")
        self._add_action(edit_menu, "撤销(&U)", "Ctrl+Z", lambda: self._current_editor().undo() if self._current_editor() else None)
        self._add_action(edit_menu, "重做(&R)", "Ctrl+Y", lambda: self._current_editor().redo() if self._current_editor() else None)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "剪切(&T)", "Ctrl+X", lambda: self._current_editor().cut() if self._current_editor() else None)
        self._add_action(edit_menu, "复制(&C)", "Ctrl+C", lambda: self._current_editor().copy() if self._current_editor() else None)
        self._add_action(edit_menu, "粘贴(&P)", "Ctrl+V", lambda: self._current_editor().paste() if self._current_editor() else None)
        self._add_action(edit_menu, "全选(&A)", "Ctrl+A", lambda: self._current_editor().selectAll() if self._current_editor() else None)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "查找替换(&F)...", "Ctrl+F", self.show_find_replace)

        view_menu = menubar.addMenu("视图(&V)")
        self.word_wrap_action = QAction("自动换行(&W)", self)
        self.word_wrap_action.setCheckable(True)
        self.word_wrap_action.setChecked(False)
        self.word_wrap_action.setShortcut("Alt+Z")
        self.word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(self.word_wrap_action)

        encoding_menu = menubar.addMenu("编码(&C)")
        self.encoding_group = []
        for enc in ["UTF-8", "GBK", "ASCII"]:
            action = QAction(enc, self)
            action.setCheckable(True)
            action.setChecked(enc == "UTF-8")
            action.triggered.connect(lambda checked, e=enc: self.set_encoding(e))
            encoding_menu.addAction(action)
            self.encoding_group.append(action)

        help_menu = menubar.addMenu("帮助(&H)")
        self._add_action(help_menu, "关于(&A)...", "", self.show_about)

    def _add_action(self, menu: QMenu, text: str, shortcut: str, callback):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def _setup_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {Theme.CARD_BG};
                border-bottom: 1px solid {Theme.BORDER};
                padding: 4px 8px;
                spacing: 4px;
            }}
            QToolButton {{
                background-color: transparent;
                color: {Theme.TEXT_PRIMARY};
                border: none;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QToolButton:hover {{
                background-color: {Theme.TAB_ACTIVE};
                border-radius: 4px;
            }}
        """)
        self.addToolBar(toolbar)

        toolbar.addAction("新建", self.new_file)
        toolbar.addAction("打开", self.open_file)
        toolbar.addAction("保存", self.save_file)
        toolbar.addSeparator()
        toolbar.addAction("查找", self.show_find_replace)
        toolbar.addSeparator()
        toolbar.addAction("导出HTML", self.export_html)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Theme.STATUS_BG};
                color: {Theme.TEXT_SECONDARY};
                border-top: 1px solid {Theme.BORDER};
                padding: 2px 10px;
                font-size: 11px;
            }}
        """)
        self.statusbar.showMessage("就绪")

        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_START};
                padding: 0 10px;
                font-size: 11px;
            }}
        """)
        self.statusbar.addPermanentWidget(self.encoding_label)

        self.position_label = QLabel("行 1, 列 1")
        self.position_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                padding: 0 10px;
                font-size: 11px;
            }}
        """)
        self.statusbar.addPermanentWidget(self.position_label)

    def _apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(Theme.BG_DARK))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(Theme.BG_DARK))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Theme.CARD_BG))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Theme.CARD_BG))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(Theme.CARD_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, QColor(Theme.ACCENT_START))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(Theme.SELECTION_BG))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Theme.TEXT_PRIMARY))
        QApplication.instance().setPalette(palette)

    def _current_editor(self) -> Optional[CodeEditor]:
        tab = self.tab_widget.currentWidget()
        if tab and isinstance(tab, EditorTab):
            return tab.editor
        return None

    def _current_tab(self) -> Optional[EditorTab]:
        tab = self.tab_widget.currentWidget()
        if tab and isinstance(tab, EditorTab):
            return tab
        return None

    def new_file(self):
        tab = EditorTab()
        index = self.tab_widget.addTab(tab, "未命名")
        self.tab_widget.setCurrentIndex(index)
        self._connect_cursor_signals(tab)
        self.statusbar.showMessage("新建文件")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "",
            "所有支持的文件 (*.py *.js *.jsx *.ts *.tsx *.html *.htm *.css *.json *.md *.txt *.xml *.rst *.log *.cfg *.ini *.yaml *.yml *.toml);;Python 文件 (*.py);;JavaScript 文件 (*.js *.jsx *.ts *.tsx);;Web 文件 (*.html *.htm *.css);;JSON 文件 (*.json);;Markdown (*.md);;所有文件 (*.*)"
        )
        if file_path:
            self._open_file_path(file_path)

    def _open_file_path(self, file_path: str):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, EditorTab) and tab.file_path == file_path:
                self.tab_widget.setCurrentIndex(i)
                return

        tab = EditorTab()
        if tab.load_file(file_path):
            name = Path(file_path).name
            index = self.tab_widget.addTab(tab, name)
            self.tab_widget.setCurrentIndex(index)
            self._connect_cursor_signals(tab)
            self._add_recent_file(file_path)
            self.statusbar.showMessage(f"已打开: {file_path}")
        else:
            tab.deleteLater()

    def _connect_cursor_signals(self, tab: EditorTab):
        tab.editor.cursorPositionChanged.connect(self._update_cursor_position)

    def _update_cursor_position(self):
        editor = self._current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.position_label.setText(f"行 {line}, 列 {col}")

    def save_file(self):
        tab = self._current_tab()
        if tab:
            if tab.file_path:
                if tab.save_file():
                    self.statusbar.showMessage(f"已保存: {tab.file_path}")
            else:
                self.save_file_as()

    def save_file_as(self):
        tab = self._current_tab()
        if tab:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "另存为", "",
                "Python 文件 (*.py);;JavaScript 文件 (*.js);;HTML 文件 (*.html);;CSS 文件 (*.css);;JSON 文件 (*.json);;Markdown (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                if tab.save_file(file_path):
                    name = Path(file_path).name
                    self.tab_widget.setTabText(self.tab_widget.currentIndex(), name)
                    self._add_recent_file(file_path)
                    self.statusbar.showMessage(f"已保存: {file_path}")

    def close_tab(self, index: int):
        tab = self.tab_widget.widget(index)
        if isinstance(tab, EditorTab):
            if tab.is_modified:
                reply = QMessageBox.question(
                    self, "保存更改",
                    f"文件 '{Path(tab.file_path).name if tab.file_path else '未命名'}' 已修改。\n是否保存更改？",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Save:
                    self.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
            self.tab_widget.removeTab(index)
            tab.deleteLater()

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())

    def show_find_replace(self):
        if not hasattr(self, '_find_dialog'):
            self._find_dialog = FindReplaceDialog(self)
        tab = self._current_tab()
        if tab:
            self._find_dialog.set_editor(tab.editor)
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()

    def toggle_word_wrap(self):
        wrap = self.word_wrap_action.isChecked()
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, EditorTab):
                tab.editor.set_word_wrap(wrap)

    def set_encoding(self, encoding: str):
        for action in self.encoding_group:
            action.setChecked(action.text() == encoding)
        tab = self._current_tab()
        if tab:
            tab.encoding = encoding.lower()
            self.encoding_label.setText(encoding)
            self.statusbar.showMessage(f"编码已切换为: {encoding}")

    def export_html(self):
        tab = self._current_tab()
        if not tab:
            return
        default_name = Path(tab.file_path).stem + ".html" if tab.file_path else "export.html"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出为 HTML", default_name,
            "HTML 文件 (*.html);;所有文件 (*.*)"
        )
        if file_path:
            tab.export_html(file_path)
            self.statusbar.showMessage(f"已导出: {file_path}")

    def update_tab_title(self, tab: EditorTab):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == tab:
                name = Path(tab.file_path).name if tab.file_path else "未命名"
                if tab.is_modified:
                    name = "● " + name
                self.tab_widget.setTabText(i, name)
                break

    def _on_tab_changed(self, index):
        tab = self.tab_widget.widget(index)
        if isinstance(tab, EditorTab):
            self.encoding_label.setText(tab.encoding.upper())
            self._update_cursor_position()

    def _add_recent_file(self, file_path: str):
        abs_path = str(Path(file_path).resolve())
        if abs_path in self.recent_files:
            self.recent_files.remove(abs_path)
        self.recent_files.insert(0, abs_path)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self._update_recent_menu()
        self._save_config()

    def _update_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_files:
            action = QAction("无最近文件", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return
        for path in self.recent_files:
            if os.path.exists(path):
                action = QAction(str(Path(path).name), self)
                action.setToolTip(path)
                action.triggered.connect(lambda checked, p=path: self._open_file_path(p))
                self.recent_menu.addAction(action)
        self.recent_menu.addSeparator()
        clear_action = QAction("清除记录", self)
        clear_action.triggered.connect(self._clear_recent)
        self.recent_menu.addAction(clear_action)

    def _clear_recent(self):
        self.recent_files.clear()
        self._update_recent_menu()
        self._save_config()

    def _load_config(self):
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.recent_files = config.get('recent_files', [])
        except Exception:
            self.recent_files = []

    def _save_config(self):
        try:
            config = {
                'recent_files': self.recent_files,
                'max_recent': self.max_recent_files
            }
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def show_about(self):
        QMessageBox.about(
            self, "关于 TextEditor",
            "<h2 style='color: #667eea;'>TextEditor v1.0.0</h2>"
            "<p>一个轻量级的代码编辑器</p>"
            "<p>功能特性:</p>"
            "<ul>"
            "<li>多标签页编辑</li>"
            "<li>语法高亮 (Python, JS, HTML, CSS, JSON, Markdown)</li>"
            "<li>行号显示</li>"
            "<li>查找替换 (支持正则表达式)</li>"
            "<li>自动保存</li>"
            "<li>多编码支持</li>"
            "<li>代码缩略图</li>"
            "<li>导出为 HTML</li>"
            "</ul>"
            "<p>基于 PyQt6 构建</p>"
        )

    def closeEvent(self, event):
        unsaved = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, EditorTab) and tab.is_modified:
                name = Path(tab.file_path).name if tab.file_path else "未命名"
                unsaved.append(name)

        if unsaved:
            reply = QMessageBox.question(
                self, "保存更改",
                f"以下文件有未保存的更改:\n\n{chr(10).join(unsaved)}\n\n是否在退出前保存所有更改？",
                QMessageBox.StandardButton.SaveAll | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.SaveAll:
                for i in range(self.tab_widget.count()):
                    tab = self.tab_widget.widget(i)
                    if isinstance(tab, EditorTab) and tab.is_modified:
                        tab.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        self._save_config()
        event.accept()


# ═══════════════════════════════════════════════════════════
# 启动应用
# ═══════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TextEditor")
    app.setApplicationVersion("1.0.0")

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    window = TextEditorMainWindow()
    window.show()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            window._open_file_path(file_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
