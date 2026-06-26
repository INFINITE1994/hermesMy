#!/usr/bin/env python3
"""
RegexTester — 专业的正则表达式测试工具
======================================
PyQt6 桌面应用，提供正则表达式编写、测试、替换、模式管理等完整功能。
"""

import json
import re
import sys
from pathlib import Path

from PyQt6.QtCore import (
    QSize,
    Qt,
    QTimer,
)
from PyQt6.QtGui import (
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QPainter,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ── 常量 ──────────────────────────────────────────────────────────────────────

BG_DARK      = "#0a0a0a"
CARD_BG      = "#111122"
ACCENT_START = "#667eea"
ACCENT_END   = "#764ba2"
TEXT_COLOR    = "#e0e0e0"
TEXT_DIM      = "#888899"
HIGHLIGHT     = "#667eea44"
MATCH_COLORS  = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b",
                 "#fa709a", "#fee140", "#30cfd0"]

COMMON_PATTERNS = {
    "电子邮箱":           r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "中国大陆手机号":     r"1[3-9]\d{9}",
    "固定电话":           r"\d{3,4}[-\s]?\d{7,8}",
    "身份证号码":         r"\d{17}[\dXx]",
    "IPv4 地址":          r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "IPv6 地址":          r"([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}",
    "URL":               r"https?://[^\s<>\"']+",
    "日期 (YYYY-MM-DD)": r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    "时间 (HH:MM:SS)":   r"\d{1,2}:\d{2}(:\d{2})?",
    "HTML 标签":          r"<[^>]+>",
    "CSS 颜色":           r"#[0-9a-fA-F]{3,8}\b",
    "中文字符":           r"[\u4e00-\u9fff]+",
    "数字":              r"\b\d+(\.\d+)?\b",
    "单词":              r"\b[A-Za-z]+\b",
    "文件路径 (Windows)": r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*",
    "邮政编码":           r"\d{6}",
    "QQ 号":             r"[1-9]\d{4,10}",
    "MAC 地址":           r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",
    "十六进制数":         r"\b0[xX][0-9a-fA-F]+\b",
    "版本号":             r"\d+\.\d+\.\d+",
}

REGEX_REFERENCE = [
    ("基础匹配", [
        (".", "任意单个字符（除换行符）"),
        ("\\d", "数字 [0-9]"),
        ("\\D", "非数字"),
        ("\\w", "单词字符 [a-zA-Z0-9_]"),
        ("\\W", "非单词字符"),
        ("\\s", "空白字符"),
        ("\\S", "非空白字符"),
        ("\\b", "单词边界"),
        ("\\B", "非单词边界"),
    ]),
    ("量词", [
        ("*", "零次或多次"),
        ("+", "一次或多次"),
        ("?", "零次或一次"),
        ("{n}", "恰好 n 次"),
        ("{n,}", "至少 n 次"),
        ("{n,m}", "n 到 m 次"),
        ("*?", "零次或多次（非贪婪）"),
        ("+?", "一次或多次（非贪婪）"),
    ]),
    ("字符类", [
        ("[abc]", "匹配 a、b 或 c"),
        ("[^abc]", "不匹配 a、b、c"),
        ("[a-z]", "a 到 z 的范围"),
        ("[A-Za-z]", "所有字母"),
    ]),
    ("分组与引用", [
        ("(abc)", "捕获组"),
        ("(?:abc)", "非捕获组"),
        ("(?P<name>abc)", "命名捕获组"),
        ("\\1", "反向引用第 1 组"),
        ("a|b", "匹配 a 或 b"),
    ]),
    ("断言", [
        ("^", "行首"),
        ("$", "行尾"),
        ("(?=...)", "正向前瞻"),
        ("(?!...)", "负向前瞻"),
        ("(?<=...)", "正向后顾"),
        ("(?<!...)", "负向后顾"),
    ]),
    ("标志", [
        ("re.I / (?i)", "忽略大小写"),
        ("re.M / (?m)", "多行模式"),
        ("re.S / (?s)", "点号匹配换行符"),
        ("re.X / (?x)", "详细模式"),
    ]),
]


# ── 数据持久化 ────────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    d = Path.home() / ".regex_tester"
    d.mkdir(exist_ok=True)
    return d


def _patterns_file() -> Path:
    return _data_dir() / "patterns.json"


def load_saved_patterns() -> list[dict]:
    p = _patterns_file()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_saved_patterns(patterns: list[dict]) -> None:
    _patterns_file().write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── 正则语法高亮器 ────────────────────────────────────────────────────────────

class RegexHighlighter(QSyntaxHighlighter):
    """为正则表达式编辑器提供语法高亮。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []

        # 特殊字符  \d \w \s \b 等
        fmt_escape = QTextCharFormat()
        fmt_escape.setForeground(QColor("#f093fb"))
        self._rules.append((re.compile(r"\\[dDwWsSbBnrtfv0]"), fmt_escape))

        # 量词
        fmt_quant = QTextCharFormat()
        fmt_quant.setForeground(QColor("#4facfe"))
        self._rules.append((re.compile(r"[+*?](?:\?)?|\{(?:\d+(?:,\d*)?)\}"), fmt_quant))

        # 字符类
        fmt_class = QTextCharFormat()
        fmt_class.setForeground(QColor("#43e97b"))
        self._rules.append((re.compile(r"\[.*?\]"), fmt_class))

        # 分组括号
        fmt_group = QTextCharFormat()
        fmt_group.setForeground(QColor("#fa709a"))
        self._rules.append((re.compile(r"[()]"), fmt_group))

        # 断言
        fmt_anchor = QTextCharFormat()
        fmt_anchor.setForeground(QColor("#fee140"))
        self._rules.append((re.compile(r"[\^$]|\\[bB]"), fmt_anchor))

        # 竖线
        fmt_pipe = QTextCharFormat()
        fmt_pipe.setForeground(QColor("#30cfd0"))
        self._rules.append((re.compile(r"\|"), fmt_pipe))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── 自定义文本编辑器（行号） ──────────────────────────────────────────────────

class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint(event)


class CodeEditor(QPlainTextEdit):
    """带行号显示的文本编辑器。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.textChanged.connect(self._update_line_number_area_width)
        self._update_line_number_area_width(0)

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            cr.left(), cr.top(), self.line_number_area_width(), cr.height()
        )

    def line_number_area_paint(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#0d0d1a"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(TEXT_DIM))
                painter.drawText(
                    0, top, self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
        painter.end()


# ── 主窗口 ────────────────────────────────────────────────────────────────────

class RegexTesterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RegexTester — 正则表达式测试工具")
        self.setMinimumSize(800, 600)
        self.resize(1280, 860)
        self._saved_patterns: list[dict] = load_saved_patterns()
        self._match_timer = QTimer(self)
        self._match_timer.setSingleShot(True)
        self._match_timer.setInterval(200)
        self._match_timer.timeout.connect(self._run_match)
        self._build_ui()
        self._apply_theme()
        self._load_pattern_list()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # 顶部标题
        title = QLabel("⚡ RegexTester")
        title.setObjectName("title")
        subtitle = QLabel("专业的正则表达式测试工具")
        subtitle.setObjectName("subtitle")
        title_row = QVBoxLayout()
        title_row.addWidget(title)
        title_row.addWidget(subtitle)
        root_layout.addLayout(title_row)

        # 主体分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(main_splitter, 1)

        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # ── 正则表达式输入区 ──
        regex_group = self._card("正则表达式")
        regex_inner = QVBoxLayout()

        regex_flags_row = QHBoxLayout()
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式…")
        self.regex_input.setObjectName("regexInput")
        self.regex_input.textChanged.connect(self._schedule_match)
        regex_flags_row.addWidget(self.regex_input, 1)

        self.flag_i = QCheckBox("i")
        self.flag_m = QCheckBox("m")
        self.flag_s = QCheckBox("s")
        self.flag_x = QCheckBox("x")
        for cb in (self.flag_i, self.flag_m, self.flag_s, self.flag_x):
            cb.setObjectName("flagCb")
            cb.stateChanged.connect(self._schedule_match)
            regex_flags_row.addWidget(cb)
        regex_inner.addLayout(regex_flags_row)

        # 正则高亮预览
        self.regex_preview = QLineEdit()
        self.regex_preview.setReadOnly(True)
        self.regex_preview.setPlaceholderText("高亮预览…")
        self.regex_preview.setObjectName("regexPreview")
        regex_inner.addWidget(self.regex_preview)

        regex_group.setLayout(regex_inner)
        left_layout.addWidget(regex_group)

        # ── 测试字符串 ──
        test_group = self._card("测试字符串")
        test_inner = QVBoxLayout()
        self.test_input = CodeEditor()
        self.test_input.setPlaceholderText("输入要测试的文本…")
        self.test_input.setObjectName("testInput")
        self.test_input.textChanged.connect(self._schedule_match)
        self.highlighter = RegexHighlighter(self.test_input.document())
        test_inner.addWidget(self.test_input)
        test_group.setLayout(test_inner)
        left_layout.addWidget(test_group, 1)

        # ── 替换区 ──
        replace_group = self._card("查找与替换")
        replace_inner = QVBoxLayout()
        replace_row = QHBoxLayout()
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("替换为…（支持 \\1 \\g<name> 等）")
        self.replace_input.setObjectName("replaceInput")
        self.replace_input.textChanged.connect(self._update_replace)
        replace_row.addWidget(self.replace_input, 1)
        self.replace_btn = QPushButton("全部替换")
        self.replace_btn.setObjectName("accentBtn")
        self.replace_btn.clicked.connect(self._do_replace)
        replace_row.addWidget(self.replace_btn)
        replace_inner.addLayout(replace_row)

        self.replace_preview = QPlainTextEdit()
        self.replace_preview.setReadOnly(True)
        self.replace_preview.setPlaceholderText("替换结果预览…")
        self.replace_preview.setObjectName("replacePreview")
        self.replace_preview.setMaximumHeight(80)
        replace_inner.addWidget(self.replace_preview)
        replace_group.setLayout(replace_inner)
        left_layout.addWidget(replace_group)

        main_splitter.addWidget(left_panel)

        # 右侧面板（标签页）
        right_tabs = QTabWidget()
        right_tabs.setObjectName("rightTabs")

        # 匹配结果
        match_tab = QWidget()
        match_layout = QVBoxLayout(match_tab)
        self.match_info = QLabel("共 0 个匹配")
        self.match_info.setObjectName("matchInfo")
        match_layout.addWidget(self.match_info)
        self.match_table = QTableWidget(0, 4)
        self.match_table.setHorizontalHeaderLabels(["序号", "匹配内容", "位置", "长度"])
        self.match_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.match_table.verticalHeader().setVisible(False)
        self.match_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.match_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.match_table.setObjectName("matchTable")
        match_layout.addWidget(self.match_table)

        # 分组详情
        self.group_tree = QTreeWidget()
        self.group_tree.setHeaderLabels(["组", "内容", "位置"])
        self.group_tree.setObjectName("groupTree")
        self.group_tree.setMaximumHeight(200)
        match_layout.addWidget(self.group_tree)
        right_tabs.addTab(match_tab, "匹配结果")

        # 常用模式
        patterns_tab = QWidget()
        patterns_layout = QVBoxLayout(patterns_tab)
        patterns_search = QHBoxLayout()
        self.pattern_search_input = QLineEdit()
        self.pattern_search_input.setPlaceholderText("搜索模式…")
        self.pattern_search_input.textChanged.connect(self._filter_common_patterns)
        patterns_search.addWidget(self.pattern_search_input)
        patterns_layout.addLayout(patterns_search)
        self.common_patterns_list = QListWidget()
        self.common_patterns_list.setObjectName("commonList")
        self.common_patterns_list.itemDoubleClicked.connect(self._use_common_pattern)
        self._all_common_items: list[tuple[str, str]] = []
        for name, pat in COMMON_PATTERNS.items():
            self._all_common_items.append((name, pat))
            self.common_patterns_list.addItem(f"{name}  →  {pat}")
        patterns_layout.addWidget(self.common_patterns_list)
        right_tabs.addTab(patterns_tab, "常用模式")

        # 正则参考
        ref_tab = QWidget()
        ref_layout = QVBoxLayout(ref_tab)
        ref_tree = QTreeWidget()
        ref_tree.setHeaderLabels(["语法", "说明"])
        ref_tree.header().setStretchLastSection(True)
        ref_tree.setObjectName("refTree")
        for cat, items in REGEX_REFERENCE:
            cat_item = QTreeWidgetItem(ref_tree)
            cat_item.setText(0, cat)
            cat_item.setExpanded(True)
            for sym, desc in items:
                child = QTreeWidgetItem(cat_item)
                child.setText(0, sym)
                child.setText(1, desc)
        ref_layout.addWidget(ref_tree)
        right_tabs.addTab(ref_tab, "正则参考")

        # 解释
        explain_tab = QWidget()
        explain_layout = QVBoxLayout(explain_tab)
        self.explain_btn = QPushButton("🔍 解释当前正则表达式")
        self.explain_btn.setObjectName("accentBtn")
        self.explain_btn.clicked.connect(self._explain_regex)
        explain_layout.addWidget(self.explain_btn)
        self.explain_output = QTextEdit()
        self.explain_output.setReadOnly(True)
        self.explain_output.setPlaceholderText("点击上方按钮，查看正则表达式的中文解释…")
        self.explain_output.setObjectName("explainOutput")
        explain_layout.addWidget(self.explain_output)
        right_tabs.addTab(explain_tab, "解释")

        # 保存模式
        save_tab = QWidget()
        save_layout = QVBoxLayout(save_tab)
        save_name_row = QHBoxLayout()
        save_name_row.addWidget(QLabel("名称:"))
        self.save_name_input = QLineEdit()
        self.save_name_input.setPlaceholderText("给模式起个名字…")
        save_name_row.addWidget(self.save_name_input, 1)
        self.save_btn = QPushButton("💾 保存当前模式")
        self.save_btn.setObjectName("accentBtn")
        self.save_btn.clicked.connect(self._save_current_pattern)
        save_name_row.addWidget(self.save_btn)
        save_layout.addLayout(save_name_row)
        self.saved_list = QListWidget()
        self.saved_list.setObjectName("savedList")
        self.saved_list.itemDoubleClicked.connect(self._load_saved_pattern)
        save_layout.addWidget(self.saved_list)
        del_row = QHBoxLayout()
        del_row.addStretch()
        self.del_btn = QPushButton("🗑 删除选中")
        self.del_btn.clicked.connect(self._delete_saved_pattern)
        del_row.addWidget(self.del_btn)
        save_layout.addLayout(del_row)
        right_tabs.addTab(save_tab, "保存模式")

        main_splitter.addWidget(right_tabs)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)

        # 状态栏
        self.statusBar().showMessage("就绪")

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    def _card(self, title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setObjectName("card")
        return g

    def _get_flags(self) -> int:
        f = 0
        if self.flag_i.isChecked():
            f |= re.IGNORECASE
        if self.flag_m.isChecked():
            f |= re.MULTILINE
        if self.flag_s.isChecked():
            f |= re.DOTALL
        if self.flag_x.isChecked():
            f |= re.VERBOSE
        return f

    def _schedule_match(self):
        self._match_timer.start()

    def _compile_regex(self) -> re.Pattern | None:
        pattern_text = self.regex_input.text()
        if not pattern_text:
            return None
        try:
            return re.compile(pattern_text, self._get_flags())
        except re.error:
            return None

    # ── 匹配 ─────────────────────────────────────────────────────────────────

    def _run_match(self):
        text = self.test_input.toPlainText()
        pattern = self._compile_regex()
        self.match_table.setRowCount(0)
        self.group_tree.clear()
        self._update_replace()

        if not pattern or not text:
            self.match_info.setText("共 0 个匹配")
            self.statusBar().showMessage("就绪")
            return

        try:
            matches = list(pattern.finditer(text))
        except Exception as e:
            self.match_info.setText(f"错误: {e}")
            self.statusBar().showMessage(f"匹配出错: {e}")
            return

        self.match_info.setText(f"共 {len(matches)} 个匹配")
        self.match_table.setRowCount(len(matches))

        for i, m in enumerate(matches):
            color = MATCH_COLORS[i % len(MATCH_COLORS)]
            self.match_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            item_text = QTableWidgetItem(m.group(0)[:200])
            item_text.setForeground(QColor(color))
            self.match_table.setItem(i, 1, item_text)
            self.match_table.setItem(i, 2, QTableWidgetItem(str(m.start())))
            self.match_table.setItem(i, 3, QTableWidgetItem(str(m.end() - m.start())))

            # 分组树
            match_node = QTreeWidgetItem(self.group_tree)
            match_node.setText(0, f"匹配 {i+1}")
            match_node.setText(1, m.group(0)[:100])
            match_node.setText(2, f"{m.start()}-{m.end()}")

            if m.lastindex:
                for gi in range(1, m.lastindex + 1):
                    child = QTreeWidgetItem(match_node)
                    child.setText(0, f"组 {gi}")
                    g = m.group(gi)
                    child.setText(1, g[:100] if g else "(无)")
                    child.setText(2, f"{m.start(gi)}-{m.end(gi)}" if g else "")

            # 命名组
            if m.groupdict():
                for name, val in m.groupdict().items():
                    child = QTreeWidgetItem(match_node)
                    child.setText(0, f"组 '{name}'")
                    child.setText(1, val[:100] if val else "(无)")

            match_node.setExpanded(True)

        # 高亮测试文本中的匹配
        self._highlight_test_text(text, matches)
        self.statusBar().showMessage(f"找到 {len(matches)} 个匹配，耗时 OK")

    def _highlight_test_text(self, text: str, matches: list):
        """在测试文本中高亮所有匹配项。"""
        extra_sels = []
        for i, m in enumerate(matches):
            sel = QTextEdit.ExtraSelection()
            sel.cursor = self.test_input.textCursor()
            sel.cursor.setPosition(m.start())
            sel.cursor.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            color = QColor(MATCH_COLORS[i % len(MATCH_COLORS)])
            color.setAlpha(50)
            sel.format.setBackground(color)
            extra_sels.append(sel)
        self.test_input.setExtraSelections(extra_sels)

    # ── 替换 ─────────────────────────────────────────────────────────────────

    def _update_replace(self):
        text = self.test_input.toPlainText()
        pattern = self._compile_regex()
        repl = self.replace_input.text()
        if not pattern or not text:
            self.replace_preview.setPlainText("")
            return
        try:
            result = pattern.sub(repl, text)
            self.replace_preview.setPlainText(result[:2000])
        except Exception as e:
            self.replace_preview.setPlainText(f"替换错误: {e}")

    def _do_replace(self):
        text = self.test_input.toPlainText()
        pattern = self._compile_regex()
        repl = self.replace_input.text()
        if not pattern or not text:
            return
        try:
            result = pattern.sub(repl, text)
            self.test_input.setPlainText(result)
            self.statusBar().showMessage("替换完成")
        except Exception as e:
            self.statusBar().showMessage(f"替换出错: {e}")

    # ── 常用模式 ──────────────────────────────────────────────────────────────

    def _filter_common_patterns(self, query: str):
        self.common_patterns_list.clear()
        q = query.lower()
        for name, pat in self._all_common_items:
            if q in name.lower() or q in pat.lower():
                self.common_patterns_list.addItem(f"{name}  →  {pat}")

    def _use_common_pattern(self, item):
        text = item.text()
        pat = text.split("→")[-1].strip()
        self.regex_input.setText(pat)
        self.statusBar().showMessage(f"已加载常用模式")

    # ── 解释 ─────────────────────────────────────────────────────────────────

    def _explain_regex(self):
        pattern = self.regex_input.text()
        if not pattern:
            self.explain_output.setHtml("<p style='color:#888'>请先输入正则表达式</p>")
            return

        lines = ["<h3 style='color:#667eea'>正则表达式解释</h3>"]
        lines.append(f"<p><b>模式:</b> <code style='color:#43e97b;background:#1a1a2e;padding:2px 6px;border-radius:3px'>{self._html_esc(pattern)}</code></p>")
        lines.append("<hr style='border-color:#222'>")
        lines.append("<table cellspacing='6' cellpadding='4'>")
        lines.append("<tr><th style='color:#667eea;text-align:left'>部分</th><th style='color:#667eea;text-align:left'>说明</th></tr>")

        i = 0
        while i < len(pattern):
            ch = pattern[i]

            if ch == "\\" and i + 1 < len(pattern):
                nxt = pattern[i + 1]
                esc_map = {
                    "d": ("\\d", "任意数字 [0-9]"),
                    "D": ("\\D", "任意非数字"),
                    "w": ("\\w", "任意单词字符 [a-zA-Z0-9_]"),
                    "W": ("\\W", "任意非单词字符"),
                    "s": ("\\s", "任意空白字符（空格、制表符等）"),
                    "S": ("\\S", "任意非空白字符"),
                    "b": ("\\b", "单词边界"),
                    "B": ("\\B", "非单词边界"),
                    "n": ("\\n", "换行符"),
                    "t": ("\\t", "制表符"),
                    "r": ("\\r", "回车符"),
                    ".": ("\\.", "匹配字面量点号 ."),
                    "\\": ("\\\\", "匹配字面量反斜杠 \\"),
                    "(": ("\\(", "匹配字面量左括号 ("),
                    ")": ("\\)", "匹配字面量右括号 )"),
                    "[": ("\\[", "匹配字面量左方括号 ["),
                    "]": ("\\]", "匹配字面量右方括号 ]"),
                    "{": ("\\{", "匹配字面量左花括号 {"),
                    "}": ("\\}", "匹配字面量右花括号 }"),
                    "+": ("\\+", "匹配字面量加号 +"),
                    "*": ("\\*", "匹配字面量星号 *"),
                    "?": ("\\?", "匹配字面量问号 ?"),
                    "|": ("\\|", "匹配字面量竖线 |"),
                    "^": ("\\^", "匹配字面量脱字符 ^"),
                    "$": ("\\$", "匹配字面量美元符 $"),
                }
                if nxt in esc_map:
                    sym, desc = esc_map[nxt]
                    lines.append(f"<tr><td style='color:#f093fb'><code>{self._html_esc(sym)}</code></td><td>{desc}</td></tr>")
                elif nxt.isdigit():
                    lines.append(f"<tr><td style='color:#f093fb'><code>\\{nxt}</code></td><td>反向引用第 {nxt} 个捕获组</td></tr>")
                else:
                    lines.append(f"<tr><td style='color:#f093fb'><code>\\{nxt}</code></td><td>转义字符 '{nxt}'</td></tr>")
                i += 2
                continue

            if ch == "[":
                end = pattern.find("]", i)
                if end != -1:
                    cls = pattern[i:end + 1]
                    neg = "不" if len(cls) > 1 and cls[1] == "^" else ""
                    lines.append(f"<tr><td style='color:#43e97b'><code>{self._html_esc(cls)}</code></td><td>字符类：{neg}匹配其中的任意字符</td></tr>")
                    i = end + 1
                    continue

            if ch == "(":
                end = self._find_group_end(pattern, i)
                inner = pattern[i + 1:end - 1] if end > i else ""
                if inner.startswith("?:"):
                    desc = f"非捕获组 (?:…)，匹配但不捕获"
                elif inner.startswith("?="):
                    desc = f"正向前瞻 (?=…)，匹配后面跟着指定内容的位置"
                elif inner.startswith("?!"):
                    desc = f"负向前瞻 (?!…)，匹配后面不跟着指定内容的位置"
                elif inner.startswith("?<="):
                    desc = f"正向后顾 (?<=…)，匹配前面是指定内容的位置"
                elif inner.startswith("?<!"):
                    desc = f"负向后顾 (?<!…)，匹配前面不是指定内容的位置"
                elif inner.startswith("?P<"):
                    name_end = inner.find(">")
                    name = inner[3:name_end] if name_end > 0 else "?"
                    desc = f"命名捕获组 (?P&lt;{name}&gt;…)，捕获并命名为 '{name}'"
                else:
                    desc = "捕获组 (…)，匹配并捕获内容"
                lines.append(f"<tr><td style='color:#fa709a'><code>(</code></td><td>{desc}</td></tr>")
                i += 1
                continue

            if ch == ")":
                lines.append(f"<tr><td style='color:#fa709a'><code>)</code></td><td>分组结束</td></tr>")
                i += 1
                continue

            simple_map = {
                ".": "任意单个字符（除换行符外）",
                "*": "零次或多次（贪婪）",
                "+": "一次或多次（贪婪）",
                "?": "零次或一次（贪婪）",
                "|": "或 — 匹配左边或右边的表达式",
                "^": "行首锚点",
                "$": "行尾锚点",
            }
            if ch in simple_map:
                lines.append(f"<tr><td style='color:#4facfe'><code>{self._html_esc(ch)}</code></td><td>{simple_map[ch]}</td></tr>")
                i += 1
                continue

            if ch == "{":
                end = pattern.find("}", i)
                if end != -1:
                    quant = pattern[i:end + 1]
                    inner = quant[1:-1]
                    if "," in inner:
                        parts = inner.split(",", 1)
                        if parts[1].strip() == "":
                            desc = f"至少 {parts[0]} 次"
                        else:
                            desc = f"{parts[0]} 到 {parts[1]} 次"
                    else:
                        desc = f"恰好 {inner} 次"
                    lines.append(f"<tr><td style='color:#4facfe'><code>{self._html_esc(quant)}</code></td><td>量词：{desc}</td></tr>")
                    i = end + 1
                    continue

            if ch == "\\":
                i += 1
                continue

            lines.append(f"<tr><td style='color:#e0e0e0'><code>{self._html_esc(ch)}</code></td><td>匹配字面量字符 '{ch}'</td></tr>")
            i += 1

        lines.append("</table>")

        # 标志说明
        flags = self._get_flags()
        if flags:
            lines.append("<hr style='border-color:#222'>")
            lines.append("<p><b>启用的标志:</b> ")
            flag_descs = []
            if flags & re.IGNORECASE:
                flag_descs.append("IGNORECASE (忽略大小写)")
            if flags & re.MULTILINE:
                flag_descs.append("MULTILINE (多行模式)")
            if flags & re.DOTALL:
                flag_descs.append("DOTALL (点号匹配换行)")
            if flags & re.VERBOSE:
                flag_descs.append("VERBOSE (详细模式)")
            lines.append(", ".join(flag_descs))
            lines.append("</p>")

        self.explain_output.setHtml("\n".join(lines))

    @staticmethod
    def _html_esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _find_group_end(pattern: str, start: int) -> int:
        depth = 0
        i = start
        while i < len(pattern):
            if pattern[i] == "(":
                depth += 1
            elif pattern[i] == ")":
                depth -= 1
                if depth == 0:
                    return i + 1
            elif pattern[i] == "\\":
                i += 1
            i += 1
        return len(pattern)

    # ── 保存模式 ──────────────────────────────────────────────────────────────

    def _save_current_pattern(self):
        name = self.save_name_input.text().strip()
        pat = self.regex_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入模式名称")
            return
        if not pat:
            QMessageBox.warning(self, "提示", "正则表达式为空")
            return
        entry = {"name": name, "pattern": pat, "flags": self._get_flags()}
        # 更新或追加
        for i, p in enumerate(self._saved_patterns):
            if p["name"] == name:
                self._saved_patterns[i] = entry
                break
        else:
            self._saved_patterns.append(entry)
        save_saved_patterns(self._saved_patterns)
        self._load_pattern_list()
        self.save_name_input.clear()
        self.statusBar().showMessage(f"模式 '{name}' 已保存")

    def _load_pattern_list(self):
        self.saved_list.clear()
        for p in self._saved_patterns:
            self.saved_list.addItem(f"{p['name']}  →  {p['pattern']}")

    def _load_saved_pattern(self, item):
        idx = self.saved_list.row(item)
        if 0 <= idx < len(self._saved_patterns):
            p = self._saved_patterns[idx]
            self.regex_input.setText(p["pattern"])
            flags = p.get("flags", 0)
            self.flag_i.setChecked(bool(flags & re.IGNORECASE))
            self.flag_m.setChecked(bool(flags & re.MULTILINE))
            self.flag_s.setChecked(bool(flags & re.DOTALL))
            self.flag_x.setChecked(bool(flags & re.VERBOSE))
            self.statusBar().showMessage(f"已加载模式 '{p['name']}'")

    def _delete_saved_pattern(self):
        idx = self.saved_list.currentRow()
        if 0 <= idx < len(self._saved_patterns):
            name = self._saved_patterns[idx]["name"]
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除模式 '{name}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self._saved_patterns[idx]
                save_saved_patterns(self._saved_patterns)
                self._load_pattern_list()
                self.statusBar().showMessage(f"已删除模式 '{name}'")

    # ── 主题 ──────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG_DARK};
                color: {TEXT_COLOR};
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }}
            QGroupBox#card {{
                background-color: {CARD_BG};
                border: 1px solid #222244;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px 8px 8px 8px;
                font-weight: bold;
            }}
            QGroupBox#card::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 10px;
                color: {ACCENT_START};
            }}
            QLineEdit, QPlainTextEdit, QTextEdit, QPlainTextEdit#replacePreview {{
                background-color: #0d0d1a;
                color: {TEXT_COLOR};
                border: 1px solid #222244;
                border-radius: 4px;
                padding: 4px 6px;
                selection-background-color: {ACCENT_START};
            }}
            QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
                border: 1px solid {ACCENT_START};
            }}
            QLineEdit#regexInput {{
                font-family: "Consolas", "Courier New", monospace;
                font-size: 14px;
                padding: 6px 8px;
            }}
            QCheckBox#flagCb {{
                color: {ACCENT_START};
                font-weight: bold;
                spacing: 2px;
            }}
            QCheckBox#flagCb::indicator {{
                width: 16px; height: 16px;
                border: 1px solid #444;
                border-radius: 3px;
                background: #0d0d1a;
            }}
            QCheckBox#flagCb::indicator:checked {{
                background: {ACCENT_START};
                border-color: {ACCENT_START};
            }}
            QPushButton#accentBtn {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton#accentBtn:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_START}cc, stop:1 {ACCENT_END}cc);
            }}
            QPushButton#accentBtn:pressed {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT_START}88, stop:1 {ACCENT_END}88);
            }}
            QPushButton {{
                background-color: #1a1a2e;
                color: {TEXT_COLOR};
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT_START};
            }}
            QTabWidget::pane {{
                border: 1px solid #222244;
                background: {CARD_BG};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background: #0d0d1a;
                color: {TEXT_DIM};
                padding: 8px 16px;
                border: 1px solid #222244;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {CARD_BG};
                color: {ACCENT_START};
                border-bottom: 2px solid {ACCENT_START};
            }}
            QTableWidget, QTreeWidget, QListWidget {{
                background-color: #0d0d1a;
                color: {TEXT_COLOR};
                border: 1px solid #222244;
                border-radius: 4px;
                alternate-background-color: #111128;
                gridline-color: #1a1a2e;
            }}
            QHeaderView::section {{
                background-color: #111122;
                color: {ACCENT_START};
                border: none;
                border-bottom: 1px solid #222244;
                padding: 4px;
                font-weight: bold;
            }}
            QTableWidget::item:selected, QListWidget::item:selected {{
                background-color: {ACCENT_START}44;
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {ACCENT_START}22;
            }}
            QScrollBar:vertical {{
                background: #0a0a0a;
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #333;
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: #0a0a0a;
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: #333;
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            QLabel#title {{
                font-size: 22px;
                font-weight: bold;
                color: {ACCENT_START};
            }}
            QLabel#subtitle {{
                font-size: 12px;
                color: {TEXT_DIM};
            }}
            QLabel#matchInfo {{
                font-size: 14px;
                font-weight: bold;
                color: {ACCENT_START};
            }}
            QStatusBar {{
                background-color: #0d0d1a;
                color: {TEXT_DIM};
                border-top: 1px solid #222244;
            }}
            QSplitter::handle {{
                background: #222244;
                width: 2px;
            }}
            #explainOutput {{
                font-size: 13px;
                line-height: 1.6;
            }}
        """)


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RegexTesterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
