#!/usr/bin/env python3
"""
QuickNote - 轻量级Markdown笔记应用
============================================
一个功能完整、界面美观的桌面笔记应用，
支持Markdown编辑、实时预览、笔记本管理、标签、搜索、导出等功能。
"""

import sys
import os
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Set

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit, QTextBrowser,
    QLineEdit, QPushButton, QLabel, QComboBox, QToolBar, QMenuBar,
    QMenu, QFileDialog, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QStatusBar, QFrame, QTabWidget, QStyle, QStyledItemDelegate,
    QAbstractItemView, QHeaderView, QSizePolicy, QCheckBox, QScrollArea,
    QGroupBox, QSpinBox, QFontComboBox, QToolButton, QWidgetAction,
    QSystemTrayIcon, QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QSize, QThread, pyqtSignal, QSettings, QDir,
    QSortFilterProxyModel, QModelIndex, QMimeData, QPoint, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QAction, QSyntaxHighlighter,
    QTextCharFormat, QTextDocument, QBrush, QLinearGradient,
    QPainter, QPixmap, QPen, QKeySequence, QShortcut, QTextCursor,
    QDesktopServices, QFontMetrics, QClipboard
)
from PyQt6.QtCore import QUrl

try:
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.toc import TocExtension
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

# ============================================================================
# 配置常量
# ============================================================================

APP_NAME = "QuickNote"
APP_VERSION = "1.0.0"
NOTES_DIR = Path.home() / ".quicknote" / "notebooks"
SETTINGS_FILE = Path.home() / ".quicknote" / "settings.json"

# 主题颜色
THEMES = {
    "dark": {
        "bg": "#0a0a0a",
        "card": "#111122",
        "card_hover": "#161636",
        "accent1": "#667eea",
        "accent2": "#764ba2",
        "text": "#e0e0e0",
        "text_secondary": "#8888aa",
        "border": "#222244",
        "input_bg": "#0d0d1a",
        "highlight": "#1a1a3a",
        "selection": "#667eea44",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "scrollbar": "#333355",
        "scrollbar_hover": "#4444aa",
        "sidebar_bg": "#080818",
        "toolbar_bg": "#0c0c1e",
        "preview_bg": "#0e0e1c",
    },
    "light": {
        "bg": "#f5f5f5",
        "card": "#ffffff",
        "card_hover": "#f0f0ff",
        "accent1": "#667eea",
        "accent2": "#764ba2",
        "text": "#1a1a2e",
        "text_secondary": "#666688",
        "border": "#ddddee",
        "input_bg": "#ffffff",
        "highlight": "#eeeef8",
        "selection": "#667eea22",
        "success": "#16a34a",
        "warning": "#d97706",
        "error": "#dc2626",
        "scrollbar": "#ccccdd",
        "scrollbar_hover": "#9999bb",
        "sidebar_bg": "#f0f0f8",
        "toolbar_bg": "#eeeef6",
        "preview_bg": "#fafafe",
    }
}

# Markdown转HTML的CSS样式
MARKDOWN_CSS_DARK = """
<style>
    body {
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        color: #e0e0e0;
        background: #0e0e1c;
        line-height: 1.7;
        padding: 16px;
        font-size: 14px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #c0c0ff;
        border-bottom: 1px solid #222244;
        padding-bottom: 8px;
        margin-top: 24px;
    }
    h1 { font-size: 24px; }
    h2 { font-size: 20px; }
    h3 { font-size: 17px; }
    a { color: #667eea; text-decoration: none; }
    a:hover { text-decoration: underline; }
    code {
        background: #1a1a3a;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: 13px;
        color: #a0a0ff;
    }
    pre {
        background: #111122;
        border: 1px solid #222244;
        border-radius: 8px;
        padding: 16px;
        overflow-x: auto;
    }
    pre code {
        background: transparent;
        padding: 0;
        color: #c0c0e0;
    }
    blockquote {
        border-left: 4px solid #667eea;
        margin: 16px 0;
        padding: 8px 16px;
        background: #111122;
        border-radius: 0 8px 8px 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
    }
    th, td {
        border: 1px solid #222244;
        padding: 10px 14px;
        text-align: left;
    }
    th {
        background: #1a1a3a;
        color: #c0c0ff;
    }
    tr:nth-child(even) { background: #111122; }
    img { max-width: 100%; border-radius: 8px; }
    hr {
        border: none;
        border-top: 1px solid #222244;
        margin: 24px 0;
    }
    ul, ol { padding-left: 24px; }
    li { margin: 4px 0; }
    .codehilite { background: #111122; border-radius: 8px; padding: 16px; }
    .codehilite .hll { background: #2a2a5a; }
    .codehilite .c { color: #6a9955; }
    .codehilite .k { color: #c586c0; }
    .codehilite .n { color: #d4d4d4; }
    .codehilite .o { color: #d4d4d4; }
    .codehilite .p { color: #d4d4d4; }
    .codehilite .s { color: #ce9178; }
    .codehilite .mi { color: #b5cea8; }
    .codehilite .kd { color: #569cd6; }
    .codehilite .kr { color: #569cd6; }
    .codehilite .kt { color: #4ec9b0; }
</style>
"""

MARKDOWN_CSS_LIGHT = """
<style>
    body {
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        color: #1a1a2e;
        background: #fafafe;
        line-height: 1.7;
        padding: 16px;
        font-size: 14px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2a2a5e;
        border-bottom: 1px solid #ddddee;
        padding-bottom: 8px;
        margin-top: 24px;
    }
    h1 { font-size: 24px; }
    h2 { font-size: 20px; }
    h3 { font-size: 17px; }
    a { color: #667eea; text-decoration: none; }
    a:hover { text-decoration: underline; }
    code {
        background: #eeeef8;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: 13px;
        color: #5a5a8a;
    }
    pre {
        background: #f0f0f8;
        border: 1px solid #ddddee;
        border-radius: 8px;
        padding: 16px;
        overflow-x: auto;
    }
    pre code {
        background: transparent;
        padding: 0;
        color: #2a2a4e;
    }
    blockquote {
        border-left: 4px solid #667eea;
        margin: 16px 0;
        padding: 8px 16px;
        background: #f0f0ff;
        border-radius: 0 8px 8px 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
    }
    th, td {
        border: 1px solid #ddddee;
        padding: 10px 14px;
        text-align: left;
    }
    th {
        background: #eeeef8;
        color: #2a2a5e;
    }
    tr:nth-child(even) { background: #f8f8fe; }
    img { max-width: 100%; border-radius: 8px; }
    hr {
        border: none;
        border-top: 1px solid #ddddee;
        margin: 24px 0;
    }
    ul, ol { padding-left: 24px; }
    li { margin: 4px 0; }
</style>
"""


# ============================================================================
# 工具函数
# ============================================================================

def ensure_dir(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default=None):
    """加载JSON文件"""
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else {}


def save_json(path: Path, data):
    """保存JSON文件"""
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(text: str) -> str:
    """将文本转换为安全的文件名"""
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    text = re.sub(r'\s+', '_', text)
    return text[:100]


# ============================================================================
# 笔记数据模型
# ============================================================================

class Note:
    """笔记数据类"""

    def __init__(self, filepath: Path, notebook: str = "默认"):
        self.filepath = filepath
        self.notebook = notebook
        self._cached_title = None
        self._cached_tags = None
        self._cached_modified = None

    @property
    def filename(self) -> str:
        return self.filepath.stem

    @property
    def title(self) -> str:
        if self._cached_title is None:
            self._load_meta()
        return self._cached_title or self.filename

    @title.setter
    def title(self, value: str):
        self._cached_title = value

    @property
    def tags(self) -> List[str]:
        if self._cached_tags is None:
            self._load_meta()
        return self._cached_tags or []

    @tags.setter
    def tags(self, value: List[str]):
        self._cached_tags = value

    @property
    def modified(self) -> datetime:
        try:
            return datetime.fromtimestamp(self.filepath.stat().st_mtime)
        except Exception:
            return datetime.now()

    @property
    def content(self) -> str:
        try:
            return self.filepath.read_text(encoding='utf-8')
        except Exception:
            return ""

    @content.setter
    def content(self, value: str):
        ensure_dir(self.filepath.parent)
        self.filepath.write_text(value, encoding='utf-8')

    def _load_meta(self):
        """从文件内容解析标题和标签"""
        content = self.content
        lines = content.split('\n')
        # 标题：第一个 # 开头的行
        for line in lines:
            if line.strip().startswith('# '):
                self._cached_title = line.strip()[2:].strip()
                break
        else:
            self._cached_title = self.filename
        # 标签：从内容中查找 #tag 或 YAML front matter
        self._cached_tags = []
        # 尝试从 front matter 读取
        if content.startswith('---'):
            try:
                end = content.index('---', 3)
                front_matter = content[3:end]
                for line in front_matter.split('\n'):
                    if line.strip().startswith('tags:'):
                        tag_str = line.split(':', 1)[1].strip()
                        if tag_str.startswith('['):
                            self._cached_tags = [t.strip().strip('"\'') for t in tag_str[1:-1].split(',')]
                        else:
                            self._cached_tags = [t.strip() for t in tag_str.split(',')]
            except (ValueError, IndexError):
                pass
        # 从内容中查找 #tag
        if not self._cached_tags:
            tag_pattern = re.compile(r'(?:^|\s)#([\w\u4e00-\u9fff]+)')
            self._cached_tags = list(set(tag_pattern.findall(content)))

    def delete(self):
        """删除笔记文件"""
        if self.filepath.exists():
            self.filepath.unlink()

    def rename(self, new_title: str):
        """重命名笔记"""
        new_slug = slugify(new_title)
        new_path = self.filepath.parent / f"{new_slug}.md"
        if new_path != self.filepath and not new_path.exists():
            self.filepath.rename(new_path)
            self.filepath = new_path
            self._cached_title = new_title

    def __repr__(self):
        return f"<Note '{self.title}' @ {self.filepath}>"


# ============================================================================
# 笔记管理器
# ============================================================================

class NoteManager:
    """管理所有笔记和笔记本"""

    def __init__(self, base_dir: Path = NOTES_DIR):
        self.base_dir = base_dir
        ensure_dir(base_dir)
        self._notes_cache: Dict[str, Note] = {}
        self._notebooks_cache: Set[str] = set()
        self.refresh()

    def refresh(self):
        """刷新笔记缓存"""
        self._notes_cache.clear()
        self._notebooks_cache.clear()
        self._notebooks_cache.add("默认")
        ensure_dir(self.base_dir / "默认")

        for notebook_dir in self.base_dir.iterdir():
            if notebook_dir.is_dir():
                notebook_name = notebook_dir.name
                self._notebooks_cache.add(notebook_name)
                for md_file in notebook_dir.glob("*.md"):
                    note = Note(md_file, notebook_name)
                    self._notes_cache[str(md_file)] = note

    @property
    def notebooks(self) -> List[str]:
        return sorted(self._notebooks_cache)

    @property
    def notes(self) -> List[Note]:
        return list(self._notes_cache.values())

    def get_notes(self, notebook: str = None) -> List[Note]:
        """获取指定笔记本的笔记"""
        if notebook:
            return [n for n in self.notes if n.notebook == notebook]
        return self.notes

    def search(self, query: str) -> List[Note]:
        """全文搜索笔记"""
        query_lower = query.lower()
        results = []
        for note in self.notes:
            content = note.content.lower()
            title = note.title.lower()
            tags = [t.lower() for t in note.tags]
            if query_lower in content or query_lower in title or query_lower in tags:
                results.append(note)
        return results

    def get_notes_by_tag(self, tag: str) -> List[Note]:
        """按标签获取笔记"""
        return [n for n in self.notes if tag in n.tags]

    def create_note(self, notebook: str = "默认", title: str = "新笔记") -> Note:
        """创建新笔记"""
        notebook_dir = self.base_dir / notebook
        ensure_dir(notebook_dir)

        slug = slugify(title)
        filepath = notebook_dir / f"{slug}.md"
        counter = 1
        while filepath.exists():
            filepath = notebook_dir / f"{slug}_{counter}.md"
            counter += 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = f"# {title}\n\n创建于 {now}\n\n开始写作...\n"
        filepath.write_text(content, encoding='utf-8')

        note = Note(filepath, notebook)
        note._cached_title = title
        self._notes_cache[str(filepath)] = note
        return note

    def create_notebook(self, name: str) -> str:
        """创建新笔记本"""
        notebook_dir = self.base_dir / name
        ensure_dir(notebook_dir)
        self._notebooks_cache.add(name)
        return name

    def delete_notebook(self, name: str):
        """删除笔记本及其所有笔记"""
        if name == "默认":
            return
        notebook_dir = self.base_dir / name
        if notebook_dir.exists():
            # 从缓存中移除
            to_remove = [k for k, v in self._notes_cache.items() if v.notebook == name]
            for k in to_remove:
                del self._notes_cache[k]
            shutil.rmtree(notebook_dir)
            self._notebooks_cache.discard(name)

    def rename_notebook(self, old_name: str, new_name: str):
        """重命名笔记本"""
        if old_name == "默认" or old_name == new_name:
            return
        old_dir = self.base_dir / old_name
        new_dir = self.base_dir / new_name
        if old_dir.exists() and not new_dir.exists():
            old_dir.rename(new_dir)
            self._notebooks_cache.discard(old_name)
            self._notebooks_cache.add(new_name)
            # 更新缓存
            for note in self._notes_cache.values():
                if note.notebook == old_name:
                    note.notebook = new_name

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for note in self.notes:
            tags.update(note.tags)
        return sorted(tags)


# ============================================================================
# Markdown 高亮器
# ============================================================================

class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown语法高亮"""

    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self.theme = theme
        self._setup_rules()

    def _setup_rules(self):
        self.rules = []
        c = THEMES[self.theme]

        # 标题
        heading_fmt = QTextCharFormat()
        heading_fmt.setForeground(QColor(c["accent1"]))
        heading_fmt.setFontWeight(QFont.Weight.Bold)
        for i in range(1, 7):
            pattern = re.compile(rf'^{"#" * i}\s+.+$', re.MULTILINE)
            self.rules.append((pattern, heading_fmt))

        # 粗体
        bold_fmt = QTextCharFormat()
        bold_fmt.setFontWeight(QFont.Weight.Bold)
        bold_fmt.setForeground(QColor(c["text"]))
        self.rules.append((re.compile(r'\*\*[^*]+\*\*'), bold_fmt))
        self.rules.append((re.compile(r'__[^_]+__'), bold_fmt))

        # 斜体
        italic_fmt = QTextCharFormat()
        italic_fmt.setFontItalic(True)
        italic_fmt.setForeground(QColor(c["text_secondary"]))
        self.rules.append((re.compile(r'\*[^*]+\*'), italic_fmt))
        self.rules.append((re.compile(r'(?<!_)_(?!_)[^_]+(?<!_)_(?!_)'), italic_fmt))

        # 行内代码
        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor("#a0a0ff"))
        code_fmt.setBackground(QColor(c["highlight"]))
        self.rules.append((re.compile(r'`[^`\n]+`'), code_fmt))

        # 链接
        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor(c["accent1"]))
        link_fmt.setFontUnderline(True)
        self.rules.append((re.compile(r'\[([^\]]+)\]\([^)]+\)'), link_fmt))

        # 图片
        img_fmt = QTextCharFormat()
        img_fmt.setForeground(QColor(c["success"]))
        self.rules.append((re.compile(r'!\[([^\]]*)\]\([^)]+\)'), img_fmt))

        # 列表
        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor(c["accent2"]))
        self.rules.append((re.compile(r'^[\s]*[-*+]\s', re.MULTILINE), list_fmt))
        self.rules.append((re.compile(r'^[\s]*\d+\.\s', re.MULTILINE), list_fmt))

        # 引用
        quote_fmt = QTextCharFormat()
        quote_fmt.setForeground(QColor(c["text_secondary"]))
        quote_fmt.setFontItalic(True)
        self.rules.append((re.compile(r'^>\s+.+$', re.MULTILINE), quote_fmt))

        # 分割线
        hr_fmt = QTextCharFormat()
        hr_fmt.setForeground(QColor(c["border"]))
        self.rules.append((re.compile(r'^---+$', re.MULTILINE), hr_fmt))
        self.rules.append((re.compile(r'^\*\*\*+$', re.MULTILINE), hr_fmt))

        # 标签 #tag
        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor(c["warning"]))
        self.rules.append((re.compile(r'(?:^|\s)#([\w\u4e00-\u9fff]+)'), tag_fmt))

        # 代码块
        self.code_block_fmt = QTextCharFormat()
        self.code_block_fmt.setBackground(QColor(c["highlight"]))
        self.code_block_fmt.setForeground(QColor("#a0a0ff"))

    def update_theme(self, theme: str):
        self.theme = theme
        self.rules.clear()
        self._setup_rules()
        self.rehighlight()

    def highlightBlock(self, text: str):
        # 先应用普通规则
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

        # 代码块处理
        self.setCurrentBlockState(0)
        if text.strip().startswith("```"):
            self.setFormat(0, len(text), self.code_block_fmt)
            if self.previousBlockState() == 1:
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
        elif self.previousBlockState() == 1:
            self.setFormat(0, len(text), self.code_block_fmt)
            if text.strip().endswith("```"):
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)


# ============================================================================
# 主题样式
# ============================================================================

def get_stylesheet(theme: str) -> str:
    """生成完整的应用样式表"""
    c = THEMES[theme]
    return f"""
    /* 全局 */
    QMainWindow, QDialog {{
        background-color: {c["bg"]};
        color: {c["text"]};
    }}
    QWidget {{
        color: {c["text"]};
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        font-size: 13px;
    }}

    /* 菜单栏 */
    QMenuBar {{
        background-color: {c["toolbar_bg"]};
        border-bottom: 1px solid {c["border"]};
        padding: 2px 4px;
    }}
    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {c["highlight"]};
    }}
    QMenu {{
        background-color: {c["card"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c["highlight"]};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c["border"]};
        margin: 4px 8px;
    }}

    /* 工具栏 */
    QToolBar {{
        background-color: {c["toolbar_bg"]};
        border-bottom: 1px solid {c["border"]};
        padding: 4px;
        spacing: 4px;
    }}
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px 10px;
        color: {c["text"]};
    }}
    QToolButton:hover {{
        background-color: {c["highlight"]};
        border-color: {c["border"]};
    }}
    QToolButton:pressed {{
        background-color: {c["accent1"]}33;
    }}

    /* 侧边栏 */
    QFrame#sidebar {{
        background-color: {c["sidebar_bg"]};
        border-right: 1px solid {c["border"]};
    }}

    /* 树形视图 */
    QTreeWidget {{
        background-color: {c["sidebar_bg"]};
        border: none;
        outline: none;
        font-size: 13px;
    }}
    QTreeWidget::item {{
        padding: 6px 8px;
        border-radius: 6px;
        margin: 1px 4px;
    }}
    QTreeWidget::item:selected {{
        background-color: {c["accent1"]}33;
        color: {c["accent1"]};
    }}
    QTreeWidget::item:hover {{
        background-color: {c["highlight"]};
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}

    /* 输入框 */
    QLineEdit {{
        background-color: {c["input_bg"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 8px 12px;
        color: {c["text"]};
        selection-background-color: {c["accent1"]}44;
    }}
    QLineEdit:focus {{
        border-color: {c["accent1"]};
    }}

    /* 文本编辑器 */
    QTextEdit {{
        background-color: {c["input_bg"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 12px;
        color: {c["text"]};
        font-family: 'Cascadia Code', 'Consolas', 'Microsoft YaHei', monospace;
        font-size: 14px;
        selection-background-color: {c["accent1"]}44;
        line-height: 1.6;
    }}
    QTextEdit:focus {{
        border-color: {c["accent1"]};
    }}

    /* 预览区域 */
    QTextBrowser {{
        background-color: {c["preview_bg"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 4px;
    }}

    /* 按钮 */
    QPushButton {{
        background-color: {c["card"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 8px 16px;
        color: {c["text"]};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c["highlight"]};
        border-color: {c["accent1"]};
    }}
    QPushButton:pressed {{
        background-color: {c["accent1"]}33;
    }}
    QPushButton#primary {{
        background-color: {c["accent1"]};
        color: white;
        border: none;
    }}
    QPushButton#primary:hover {{
        background-color: {c["accent2"]};
    }}
    QPushButton#danger {{
        background-color: transparent;
        color: {c["error"]};
        border-color: {c["error"]}44;
    }}
    QPushButton#danger:hover {{
        background-color: {c["error"]}22;
    }}

    /* 下拉框 */
    QComboBox {{
        background-color: {c["input_bg"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 6px 12px;
        color: {c["text"]};
        min-width: 100px;
    }}
    QComboBox:focus {{
        border-color: {c["accent1"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c["card"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        selection-background-color: {c["highlight"]};
    }}

    /* 标签页 */
    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        border-radius: 8px;
        background-color: {c["card"]};
    }}
    QTabBar::tab {{
        background-color: transparent;
        border: none;
        padding: 8px 16px;
        color: {c["text_secondary"]};
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {c["accent1"]};
        border-bottom-color: {c["accent1"]};
    }}
    QTabBar::tab:hover {{
        color: {c["text"]};
    }}

    /* 分割器 */
    QSplitter::handle {{
        background-color: {c["border"]};
        width: 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {c["accent1"]};
    }}

    /* 滚动条 */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {c["scrollbar"]};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c["scrollbar_hover"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c["scrollbar"]};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c["scrollbar_hover"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* 状态栏 */
    QStatusBar {{
        background-color: {c["toolbar_bg"]};
        border-top: 1px solid {c["border"]};
        color: {c["text_secondary"]};
        padding: 2px 8px;
    }}

    /* 复选框 */
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {c["border"]};
        background-color: {c["input_bg"]};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c["accent1"]};
        border-color: {c["accent1"]};
    }}

    /* 分组框 */
    QGroupBox {{
        border: 1px solid {c["border"]};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {c["accent1"]};
    }}

    /* 标签 */
    QLabel {{
        color: {c["text"]};
    }}
    QLabel#subtitle {{
        color: {c["text_secondary"]};
        font-size: 12px;
    }}
    QLabel#heading {{
        font-size: 16px;
        font-weight: bold;
        color: {c["text"]};
    }}

    /* 进度条 */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {c["border"]};
        text-align: center;
        height: 6px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c["accent1"]}, stop:1 {c["accent2"]});
        border-radius: 4px;
    }}

    /* SpinBox */
    QSpinBox {{
        background-color: {c["input_bg"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 4px 8px;
        color: {c["text"]};
    }}
    """


# ============================================================================
# 主窗口
# ============================================================================

class QuickNoteWindow(QMainWindow):
    """QuickNote 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1280, 800)

        # 设置
        self.settings = load_json(SETTINGS_FILE, {
            "theme": "dark",
            "last_notebook": "默认",
            "last_note": None,
            "window_geometry": None,
            "auto_save_interval": 2000,
            "font_size": 14,
            "show_preview": True,
        })

        # 主题
        self.current_theme = self.settings.get("theme", "dark")

        # 笔记管理器
        self.note_manager = NoteManager(NOTES_DIR)

        # 当前笔记
        self.current_note: Optional[Note] = None

        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setInterval(self.settings.get("auto_save_interval", 2000))
        self.auto_save_timer.timeout.connect(self._auto_save)

        # 搜索防抖定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._perform_search)

        # 初始化UI
        self._init_ui()
        self._apply_theme()

        # 加载最后的笔记
        self._load_initial_state()

    def _init_ui(self):
        """初始化用户界面"""
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 菜单栏
        self._create_menu_bar()

        # 工具栏
        self._create_toolbar()

        # 主内容区
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 主分割器 (侧边栏 | 编辑区)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(1)

        # 侧边栏
        self._create_sidebar()
        self.main_splitter.addWidget(self.sidebar_frame)

        # 编辑区分割器 (编辑器 | 预览)
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setHandleWidth(1)

        # 编辑器
        self._create_editor()
        self.editor_splitter.addWidget(self.editor_frame)

        # 预览
        self._create_preview()
        self.editor_splitter.addWidget(self.preview_frame)

        self.editor_splitter.setSizes([500, 500])
        self.main_splitter.addWidget(self.editor_splitter)
        self.main_splitter.setSizes([280, 1000])

        content_layout.addWidget(self.main_splitter)
        main_layout.addWidget(content_widget)

        # 状态栏
        self._create_status_bar()

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建笔记", self._new_note)
        file_menu.addAction("新建笔记本", self._new_notebook)
        file_menu.addSeparator()
        file_menu.addAction("保存", self._save_note)
        file_menu.addSeparator()

        # 导出子菜单
        export_menu = file_menu.addMenu("导出")
        export_menu.addAction("导出为 HTML", lambda: self._export_note("html"))
        export_menu.addAction("导出为 Markdown", lambda: self._export_note("md"))
        export_menu.addAction("导出为 TXT", lambda: self._export_note("txt"))
        export_menu.addAction("导出为 PDF", lambda: self._export_note("pdf"))

        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销", self._undo)
        edit_menu.addAction("重做", self._redo)
        edit_menu.addSeparator()
        edit_menu.addAction("剪切", self._cut)
        edit_menu.addAction("复制", self._copy)
        edit_menu.addAction("粘贴", self._paste)
        edit_menu.addSeparator()
        edit_menu.addAction("查找", self._focus_search)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        view_menu.addAction("切换预览", self._toggle_preview)
        view_menu.addAction("切换主题", self._toggle_theme)
        view_menu.addSeparator()
        view_menu.addAction("放大", self._zoom_in)
        view_menu.addAction("缩小", self._zoom_out)

        # 笔记菜单
        note_menu = menubar.addMenu("笔记(&N)")
        note_menu.addAction("添加标签", self._add_tag_dialog)
        note_menu.addAction("重命名笔记", self._rename_note)
        note_menu.addSeparator()
        note_menu.addAction("删除笔记", self._delete_note)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("使用帮助", self._show_help)
        help_menu.addAction("关于", self._show_about)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        # 新建笔记
        new_btn = QToolButton()
        new_btn.setText("📝 新建")
        new_btn.setToolTip("新建笔记 (Ctrl+N)")
        new_btn.clicked.connect(self._new_note)
        toolbar.addWidget(new_btn)

        # 保存
        save_btn = QToolButton()
        save_btn.setText("💾 保存")
        save_btn.setToolTip("保存笔记 (Ctrl+S)")
        save_btn.clicked.connect(self._save_note)
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        # 搜索框
        search_label = QLabel("  🔍 ")
        toolbar.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索笔记...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input)

        # 清除搜索
        clear_btn = QToolButton()
        clear_btn.setText("✕")
        clear_btn.setToolTip("清除搜索")
        clear_btn.clicked.connect(self._clear_search)
        toolbar.addWidget(clear_btn)

        # 弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # 主题切换
        self.theme_btn = QToolButton()
        self.theme_btn.setText("🌙 暗色" if self.current_theme == "dark" else "☀️ 亮色")
        self.theme_btn.setToolTip("切换主题 (Ctrl+T)")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)

        # 预览切换
        self.preview_btn = QToolButton()
        self.preview_btn.setText("👁 预览")
        self.preview_btn.setToolTip("切换预览 (Ctrl+P)")
        self.preview_btn.clicked.connect(self._toggle_preview)
        toolbar.addWidget(self.preview_btn)

    def _create_sidebar(self):
        """创建侧边栏"""
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebar")
        self.sidebar_frame.setMinimumWidth(220)
        self.sidebar_frame.setMaximumWidth(400)

        layout = QVBoxLayout(self.sidebar_frame)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)

        # 笔记本选择器
        nb_header = QHBoxLayout()
        nb_label = QLabel("📓 笔记本")
        nb_label.setObjectName("heading")
        nb_header.addWidget(nb_label)

        add_nb_btn = QPushButton("+")
        add_nb_btn.setFixedSize(28, 28)
        add_nb_btn.setToolTip("新建笔记本")
        add_nb_btn.clicked.connect(self._new_notebook)
        nb_header.addWidget(add_nb_btn)

        layout.addLayout(nb_header)

        self.notebook_combo = QComboBox()
        self.notebook_combo.currentTextChanged.connect(self._on_notebook_changed)
        layout.addWidget(self.notebook_combo)

        # 笔记列表
        notes_header = QHBoxLayout()
        notes_label = QLabel("📄 笔记")
        notes_label.setObjectName("heading")
        notes_header.addWidget(notes_label)

        add_note_btn = QPushButton("+")
        add_note_btn.setFixedSize(28, 28)
        add_note_btn.setObjectName("primary")
        add_note_btn.setToolTip("新建笔记")
        add_note_btn.clicked.connect(self._new_note)
        notes_header.addWidget(add_note_btn)

        layout.addLayout(notes_header)

        self.note_tree = QTreeWidget()
        self.note_tree.setHeaderHidden(True)
        self.note_tree.setAnimated(True)
        self.note_tree.setIndentation(16)
        self.note_tree.currentItemChanged.connect(self._on_note_selected)
        self.note_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_tree.customContextMenuRequested.connect(self._show_note_context_menu)
        layout.addWidget(self.note_tree, 1)

        # 标签区域
        tag_header = QLabel("🏷 标签")
        tag_header.setObjectName("heading")
        layout.addWidget(tag_header)

        self.tag_container = QWidget()
        self.tag_layout = QVBoxLayout(self.tag_container)
        self.tag_layout.setContentsMargins(0, 0, 0, 0)
        self.tag_layout.setSpacing(4)

        tag_scroll = QScrollArea()
        tag_scroll.setWidget(self.tag_container)
        tag_scroll.setWidgetResizable(True)
        tag_scroll.setMaximumHeight(150)
        tag_scroll.setStyleSheet("QScrollArea { border: none; }")
        layout.addWidget(tag_scroll)

        # 笔记计数
        self.note_count_label = QLabel()
        self.note_count_label.setObjectName("subtitle")
        self.note_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.note_count_label)

    def _create_editor(self):
        """创建编辑器"""
        self.editor_frame = QFrame()
        layout = QVBoxLayout(self.editor_frame)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(6)

        # 标题编辑
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("笔记标题...")
        self.title_edit.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 8px 4px;
                background: transparent;
            }
            QLineEdit:focus {
                border-bottom-color: #667eea;
            }
        """)
        self.title_edit.textChanged.connect(self._on_title_changed)
        layout.addWidget(self.title_edit)

        # 标签显示
        self.tags_label = QLabel("标签: 无")
        self.tags_label.setObjectName("subtitle")
        layout.addWidget(self.tags_label)

        # 编辑器
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("开始用Markdown写作...")
        self.editor.setAcceptRichText(False)
        self.editor.setTabStopDistance(
            QFontMetrics(self.editor.font()).horizontalAdvance(' ') * 4
        )
        self.editor.textChanged.connect(self._on_text_changed)

        # 语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document(), self.current_theme)

        layout.addWidget(self.editor, 1)

        # 底部工具栏
        bottom_bar = QHBoxLayout()

        format_btns = [
            ("B", "加粗", self._insert_bold),
            ("I", "斜体", self._insert_italic),
            ("~", "删除线", self._insert_strikethrough),
            ("</>", "代码", self._insert_code),
            ("🔗", "链接", self._insert_link),
            ("📷", "图片", self._insert_image),
            ("•", "列表", self._insert_list),
            ("❝", "引用", self._insert_quote),
            ("—", "分割线", self._insert_hr),
        ]

        for text, tooltip, callback in format_btns:
            btn = QPushButton(text)
            btn.setFixedSize(32, 28)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            bottom_bar.addWidget(btn)

        bottom_bar.addStretch()

        self.cursor_label = QLabel("行 1, 列 1")
        self.cursor_label.setObjectName("subtitle")
        bottom_bar.addWidget(self.cursor_label)

        layout.addLayout(bottom_bar)

    def _create_preview(self):
        """创建预览区域"""
        self.preview_frame = QFrame()
        layout = QVBoxLayout(self.preview_frame)
        layout.setContentsMargins(4, 8, 8, 8)
        layout.setSpacing(6)

        preview_header = QHBoxLayout()
        preview_label = QLabel("📖 预览")
        preview_label.setObjectName("heading")
        preview_header.addWidget(preview_label)

        preview_header.addStretch()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedHeight(28)
        refresh_btn.clicked.connect(self._update_preview)
        preview_header.addWidget(refresh_btn)

        layout.addLayout(preview_header)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        layout.addWidget(self.preview, 1)

        # 初始隐藏预览（如果设置）
        if not self.settings.get("show_preview", True):
            self.preview_frame.hide()

    def _create_status_bar(self):
        """创建状态栏"""
        status = self.statusBar()
        status.setFixedHeight(28)

        self.status_label = QLabel("就绪")
        status.addWidget(self.status_label, 1)

        self.word_count_label = QLabel("字数: 0")
        status.addPermanentWidget(self.word_count_label)

        self.char_count_label = QLabel("字符: 0")
        status.addPermanentWidget(self.char_count_label)

        self.save_status_label = QLabel("●")
        self.save_status_label.setToolTip("保存状态")
        self.save_status_label.setStyleSheet("color: #4ade80;")
        status.addPermanentWidget(self.save_status_label)

    # ------------------------------------------------------------------
    # 主题
    # ------------------------------------------------------------------

    def _apply_theme(self):
        """应用当前主题"""
        self.setStyleSheet(get_stylesheet(self.current_theme))
        if hasattr(self, 'highlighter'):
            self.highlighter.update_theme(self.current_theme)
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText("🌙 暗色" if self.current_theme == "dark" else "☀️ 亮色")
        if hasattr(self, 'preview') and self.current_note:
            self._update_preview()

    def _toggle_theme(self):
        """切换主题"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.settings["theme"] = self.current_theme
        self._apply_theme()
        self._save_settings()

    # ------------------------------------------------------------------
    # 笔记本管理
    # ------------------------------------------------------------------

    def _refresh_notebooks(self):
        """刷新笔记本列表"""
        current = self.notebook_combo.currentText()
        self.notebook_combo.blockSignals(True)
        self.notebook_combo.clear()
        self.notebook_combo.addItems(self.note_manager.notebooks)
        # 恢复选择
        idx = self.notebook_combo.findText(current)
        if idx >= 0:
            self.notebook_combo.setCurrentIndex(idx)
        self.notebook_combo.blockSignals(False)

    def _on_notebook_changed(self, notebook: str):
        """笔记本选择改变"""
        if notebook:
            self._refresh_note_list(notebook)
            self.settings["last_notebook"] = notebook

    def _new_notebook(self):
        """新建笔记本"""
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建笔记本", "笔记本名称:")
        if ok and name.strip():
            name = name.strip()
            if name in self.note_manager.notebooks:
                QMessageBox.warning(self, "提示", f"笔记本 '{name}' 已存在")
                return
            self.note_manager.create_notebook(name)
            self._refresh_notebooks()
            self.notebook_combo.setCurrentText(name)
            self._show_status(f"已创建笔记本: {name}")

    # ------------------------------------------------------------------
    # 笔记管理
    # ------------------------------------------------------------------

    def _refresh_note_list(self, notebook: str = None):
        """刷新笔记列表"""
        self.note_tree.clear()
        if notebook is None:
            notebook = self.notebook_combo.currentText()

        notes = self.note_manager.get_notes(notebook)
        notes.sort(key=lambda n: n.modified, reverse=True)

        for note in notes:
            item = QTreeWidgetItem()
            item.setText(0, note.title)
            item.setToolTip(0, f"{note.title}\n修改时间: {note.modified.strftime('%Y-%m-%d %H:%M')}\n标签: {', '.join(note.tags) if note.tags else '无'}")
            item.setData(0, Qt.ItemDataRole.UserRole, note)
            self.note_tree.addTopLevelItem(item)

        self.note_count_label.setText(f"共 {len(notes)} 条笔记")
        self._refresh_tags()

    def _refresh_tags(self):
        """刷新标签列表"""
        # 清除旧标签按钮
        while self.tag_layout.count():
            child = self.tag_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tags = self.note_manager.get_all_tags()
        if not tags:
            no_tag = QLabel("暂无标签")
            no_tag.setObjectName("subtitle")
            self.tag_layout.addWidget(no_tag)
            return

        # 全部标签按钮
        all_btn = QPushButton("📋 全部")
        all_btn.setFixedHeight(28)
        all_btn.clicked.connect(lambda: self._filter_by_tag(None))
        self.tag_layout.addWidget(all_btn)

        for tag in tags:
            btn = QPushButton(f"🏷 {tag}")
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, t=tag: self._filter_by_tag(t))
            self.tag_layout.addWidget(btn)

    def _filter_by_tag(self, tag: str):
        """按标签筛选"""
        self.note_tree.clear()
        if tag:
            notes = self.note_manager.get_notes_by_tag(tag)
            self._show_status(f"标签筛选: {tag} ({len(notes)} 条)")
        else:
            notes = self.note_manager.notes
            notes.sort(key=lambda n: n.modified, reverse=True)

        for note in notes:
            item = QTreeWidgetItem()
            item.setText(0, f"[{note.notebook}] {note.title}")
            item.setData(0, Qt.ItemDataRole.UserRole, note)
            self.note_tree.addTopLevelItem(item)

    def _on_note_selected(self, current, previous):
        """笔记选择改变"""
        if current is None:
            return
        note = current.data(0, Qt.ItemDataRole.UserRole)
        if note and note != self.current_note:
            self._load_note(note)

    def _load_note(self, note: Note):
        """加载笔记到编辑器"""
        # 保存当前笔记
        if self.current_note:
            self._save_note()

        self.current_note = note
        self.title_edit.blockSignals(True)
        self.editor.blockSignals(True)

        self.title_edit.setText(note.title)
        self.editor.setPlainText(note.content)

        self.title_edit.blockSignals(False)
        self.editor.blockSignals(False)

        self._update_tags_label()
        self._update_preview()
        self._update_word_count()
        self._show_status(f"已加载: {note.title}")
        self.settings["last_note"] = str(note.filepath)

    def _new_note(self):
        """新建笔记"""
        notebook = self.notebook_combo.currentText() or "默认"
        note = self.note_manager.create_note(notebook, "新笔记")
        self._refresh_note_list(notebook)
        self._load_note(note)

        # 选中新笔记
        for i in range(self.note_tree.topLevelItemCount()):
            item = self.note_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == note:
                self.note_tree.setCurrentItem(item)
                break

        self.title_edit.selectAll()
        self.title_edit.setFocus()
        self._show_status("已创建新笔记")

    def _save_note(self):
        """保存当前笔记"""
        if not self.current_note:
            return

        title = self.title_edit.text().strip() or "无标题"
        content = self.editor.toPlainText()

        # 更新标题（如果改变）
        if title != self.current_note.title:
            self.current_note.rename(title)

        # 保存内容
        self.current_note.content = content
        self.current_note._cached_title = title
        self.current_note._cached_tags = None  # 重新解析标签

        # 刷新UI
        self.save_status_label.setStyleSheet("color: #4ade80;")
        self.save_status_label.setToolTip("已保存")
        self._show_status(f"已保存: {title}")

    def _auto_save(self):
        """自动保存"""
        if self.current_note:
            self._save_note()
            self.save_status_label.setStyleSheet("color: #4ade80;")
            self.save_status_label.setToolTip("自动保存")

    def _delete_note(self):
        """删除笔记"""
        if not self.current_note:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除笔记 '{self.current_note.title}' 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            title = self.current_note.title
            self.current_note.delete()
            self.note_manager.refresh()
            self.current_note = None
            self.editor.clear()
            self.title_edit.clear()
            self.preview.clear()
            self._refresh_note_list()
            self._show_status(f"已删除: {title}")

    def _rename_note(self):
        """重命名笔记"""
        if not self.current_note:
            return
        from PyQt6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(
            self, "重命名笔记", "新标题:", text=self.current_note.title
        )
        if ok and new_title.strip():
            self.current_note.rename(new_title.strip())
            self.title_edit.setText(new_title.strip())
            self._refresh_note_list()
            self._show_status(f"已重命名: {new_title}")

    def _add_tag_dialog(self):
        """添加标签对话框"""
        if not self.current_note:
            return
        from PyQt6.QtWidgets import QInputDialog
        tag, ok = QInputDialog.getText(self, "添加标签", "标签名称:")
        if ok and tag.strip():
            tag = tag.strip()
            content = self.editor.toPlainText()
            if f"#{tag}" not in content:
                # 在文档末尾添加标签
                if not content.endswith('\n'):
                    content += '\n'
                content += f"\n#{tag}"
                self.editor.setPlainText(content)
            self._show_status(f"已添加标签: {tag}")

    def _update_tags_label(self):
        """更新标签显示"""
        if self.current_note:
            tags = self.current_note.tags
            if tags:
                self.tags_label.setText(f"标签: {', '.join(tags)}")
            else:
                self.tags_label.setText("标签: 无")

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------

    def _on_search_changed(self, text: str):
        """搜索文本改变"""
        self.search_timer.start()

    def _perform_search(self):
        """执行搜索"""
        query = self.search_input.text().strip()
        if not query:
            self._refresh_note_list()
            return

        results = self.note_manager.search(query)
        self.note_tree.clear()

        for note in results:
            item = QTreeWidgetItem()
            item.setText(0, f"[{note.notebook}] {note.title}")
            item.setToolTip(0, f"笔记本: {note.notebook}")
            item.setData(0, Qt.ItemDataRole.UserRole, note)
            self.note_tree.addTopLevelItem(item)

        self._show_status(f"搜索 '{query}': 找到 {len(results)} 条结果")

    def _clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self._refresh_note_list()

    def _focus_search(self):
        """聚焦搜索框"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    # ------------------------------------------------------------------
    # 编辑器操作
    # ------------------------------------------------------------------

    def _on_text_changed(self):
        """文本改变"""
        if self.current_note:
            self.save_status_label.setStyleSheet("color: #fbbf24;")
            self.save_status_label.setToolTip("未保存")
            self.auto_save_timer.start()
        self._update_word_count()
        self._update_preview()
        self._update_tags_label()

    def _on_title_changed(self, title: str):
        """标题改变"""
        if self.current_note:
            self.save_status_label.setStyleSheet("color: #fbbf24;")
            self.auto_save_timer.start()

    def _update_word_count(self):
        """更新字数统计"""
        text = self.editor.toPlainText()
        chars = len(text)
        # 中文字符 + 英文单词
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        words = chinese_chars + english_words

        self.word_count_label.setText(f"字数: {words}")
        self.char_count_label.setText(f"字符: {chars}")

        # 更新光标位置
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_label.setText(f"行 {line}, 列 {col}")

    def _insert_bold(self):
        self._wrap_selection("**", "**")

    def _insert_italic(self):
        self._wrap_selection("*", "*")

    def _insert_strikethrough(self):
        self._wrap_selection("~~", "~~")

    def _insert_code(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            self._wrap_selection("`", "`")
        else:
            cursor.insertText("```\n\n```")
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            self.editor.setTextCursor(cursor)

    def _insert_link(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"[{text}](url)")
        else:
            cursor.insertText("[链接文本](url)")

    def _insert_image(self):
        cursor = self.editor.textCursor()
        cursor.insertText("![图片描述](图片url)")

    def _insert_list(self):
        cursor = self.editor.textCursor()
        cursor.insertText("\n- ")

    def _insert_quote(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            lines = text.split('\n')
            quoted = '\n'.join(f"> {line}" for line in lines)
            cursor.insertText(quoted)
        else:
            cursor.insertText("\n> ")

    def _insert_hr(self):
        cursor = self.editor.textCursor()
        cursor.insertText("\n\n---\n\n")

    def _wrap_selection(self, prefix: str, suffix: str):
        """用前后缀包裹选中文本"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{prefix}{text}{suffix}")
        else:
            cursor.insertText(f"{prefix}文本{suffix}")
            # 选中"文本"以便编辑
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(suffix))
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 2)
            self.editor.setTextCursor(cursor)

    def _undo(self):
        self.editor.undo()

    def _redo(self):
        self.editor.redo()

    def _cut(self):
        self.editor.cut()

    def _copy(self):
        self.editor.copy()

    def _paste(self):
        self.editor.paste()

    def _zoom_in(self):
        font = self.editor.font()
        size = font.pointSize()
        if size < 32:
            font.setPointSize(size + 1)
            self.editor.setFont(font)
            self.settings["font_size"] = size + 1

    def _zoom_out(self):
        font = self.editor.font()
        size = font.pointSize()
        if size > 8:
            font.setPointSize(size - 1)
            self.editor.setFont(font)
            self.settings["font_size"] = size - 1

    # ------------------------------------------------------------------
    # 预览
    # ------------------------------------------------------------------

    def _toggle_preview(self):
        """切换预览显示"""
        if self.preview_frame.isVisible():
            self.preview_frame.hide()
            self.settings["show_preview"] = False
        else:
            self.preview_frame.show()
            self._update_preview()
            self.settings["show_preview"] = True

    def _update_preview(self):
        """更新Markdown预览"""
        if not self.preview_frame.isVisible():
            return

        content = self.editor.toPlainText()
        if not content:
            self.preview.setHtml("<html><body style='color: #888; padding: 20px;'>开始写作，预览将在这里显示...</body></html>")
            return

        if HAS_MARKDOWN:
            try:
                extensions = [
                    FencedCodeExtension(),
                    TableExtension(),
                    TocExtension(permalink=True),
                    'markdown.extensions.nl2br',
                    'markdown.extensions.sane_lists',
                ]
                if HAS_PYGMENTS:
                    extensions.append(
                        CodeHiliteExtension(css_class='codehilite', linenums=False, guess_lang=True)
                    )

                html = markdown.markdown(
                    content,
                    extensions=extensions,
                    output_format='html5'
                )
            except Exception as e:
                html = f"<p style='color: red;'>Markdown解析错误: {e}</p><pre>{content}</pre>"
        else:
            # 简单的Markdown转HTML
            html = self._simple_markdown_to_html(content)

        # 应用主题CSS
        css = MARKDOWN_CSS_DARK if self.current_theme == "dark" else MARKDOWN_CSS_LIGHT
        full_html = f"<!DOCTYPE html><html><head>{css}</head><body>{html}</body></html>"
        self.preview.setHtml(full_html)

    def _simple_markdown_to_html(self, text: str) -> str:
        """简单的Markdown转HTML（无依赖时使用）"""
        html = text
        # 标题
        for i in range(6, 0, -1):
            pattern = r'^' + '#' * i + r'\s+(.+)$'
            html = re.sub(pattern, f'<h{ i }>\\1</h{ i }>', html, flags=re.MULTILINE)
        # 粗体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        # 斜体
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        # 行内代码
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        # 链接
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
        # 换行
        html = html.replace('\n', '<br>')
        return html

    # ------------------------------------------------------------------
    # 导出
    # ------------------------------------------------------------------

    def _export_note(self, format_type: str):
        """导出笔记"""
        if not self.current_note:
            QMessageBox.information(self, "提示", "请先选择或创建一个笔记")
            return

        content = self.editor.toPlainText()
        title = self.current_note.title

        filters = {
            "html": ("HTML文件 (*.html)", ".html"),
            "md": ("Markdown文件 (*.md)", ".md"),
            "txt": ("文本文件 (*.txt)", ".txt"),
            "pdf": ("PDF文件 (*.pdf)", ".pdf"),
        }

        filter_str, ext = filters[format_type]
        default_name = f"{slugify(title)}{ext}"

        filepath, _ = QFileDialog.getSaveFileName(
            self, f"导出为 {ext.upper()[1:]}", default_name, filter_str
        )

        if not filepath:
            return

        try:
            if format_type == "html":
                self._export_html(filepath, content, title)
            elif format_type == "md":
                Path(filepath).write_text(content, encoding='utf-8')
            elif format_type == "txt":
                # 去除Markdown标记
                plain = re.sub(r'[#*`\[\]()>~_-]', '', content)
                Path(filepath).write_text(plain, encoding='utf-8')
            elif format_type == "pdf":
                self._export_pdf(filepath, content, title)

            self._show_status(f"已导出: {filepath}")
            QMessageBox.information(self, "导出成功", f"笔记已导出到:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出时出错:\n{str(e)}")

    def _export_html(self, filepath: str, content: str, title: str):
        """导出为HTML"""
        if HAS_MARKDOWN:
            extensions = [FencedCodeExtension(), TableExtension(), 'markdown.extensions.nl2br']
            if HAS_PYGMENTS:
                extensions.append(CodeHiliteExtension(css_class='codehilite'))
            html_body = markdown.markdown(content, extensions=extensions, output_format='html5')
        else:
            html_body = self._simple_markdown_to_html(content)

        css = MARKDOWN_CSS_DARK if self.current_theme == "dark" else MARKDOWN_CSS_LIGHT
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
{html_body}
</body>
</html>"""
        Path(filepath).write_text(full_html, encoding='utf-8')

    def _export_pdf(self, filepath: str, content: str, title: str):
        """导出为PDF"""
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QPainter

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filepath)
            printer.setPageSize(QPrinter.PageSize.A4)

            # 生成HTML
            if HAS_MARKDOWN:
                html_body = markdown.markdown(content, extensions=[FencedCodeExtension(), TableExtension()], output_format='html5')
            else:
                html_body = self._simple_markdown_to_html(content)

            css = """
            body { font-family: 'Microsoft YaHei', sans-serif; font-size: 12pt; line-height: 1.6; color: #333; }
            h1, h2, h3 { color: #2a2a5e; }
            code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
            pre { background: #f5f5f5; padding: 12px; border-radius: 6px; }
            """
            full_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><style>{css}</style></head><body>{html_body}</body></html>"

            doc = QTextDocument()
            doc.setHtml(full_html)
            doc.print_(printer)

        except ImportError:
            # 回退方案：使用文本导出
            raise Exception("PDF导出需要Qt打印支持。请尝试导出为HTML后使用浏览器打印。")

    # ------------------------------------------------------------------
    # 其他
    # ------------------------------------------------------------------

    def _show_note_context_menu(self, position):
        """显示笔记右键菜单"""
        item = self.note_tree.itemAt(position)
        if not item:
            return

        note = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        menu.addAction("📝 重命名", lambda: self._rename_note)
        menu.addAction("🏷 添加标签", lambda: self._add_tag_dialog)
        menu.addSeparator()

        export_menu = menu.addMenu("📤 导出")
        export_menu.addAction("HTML", lambda: self._export_note("html"))
        export_menu.addAction("Markdown", lambda: self._export_note("md"))
        export_menu.addAction("TXT", lambda: self._export_note("txt"))

        menu.addSeparator()
        menu.addAction("🗑 删除", lambda: self._delete_note)

        menu.exec(self.note_tree.viewport().mapToGlobal(position))

    def _show_help(self):
        """显示帮助"""
        help_text = """
<h2>QuickNote 使用帮助</h2>

<h3>📝 基本操作</h3>
<ul>
<li><b>新建笔记</b>: Ctrl+N 或点击工具栏"新建"按钮</li>
<li><b>保存笔记</b>: Ctrl+S 或自动保存</li>
<li><b>搜索笔记</b>: Ctrl+F 聚焦搜索框</li>
</ul>

<h3>📓 笔记本管理</h3>
<ul>
<li>在左侧选择笔记本查看其中的笔记</li>
<li>点击"+"创建新笔记本</li>
<li>右键点击笔记本可重命名或删除</li>
</ul>

<h3>🏷 标签使用</h3>
<ul>
<li>在笔记中使用 <code>#标签名</code> 添加标签</li>
<li>左侧标签栏可按标签筛选笔记</li>
<li>可通过菜单"笔记 → 添加标签"快速添加</li>
</ul>

<h3>📝 Markdown语法</h3>
<ul>
<li><code># 标题</code> - 一级标题</li>
<li><code>**粗体**</code> - <b>粗体</b></li>
<li><code>*斜体*</code> - <i>斜体</i></li>
<li><code>`代码`</code> - 行内代码</li>
<li><code>```语言```</code> - 代码块</li>
<li><code>[链接](url)</code> - 超链接</li>
<li><code>> 引用</code> - 引用块</li>
<li><code>- 列表</code> - 无序列表</li>
</ul>

<h3>📤 导出功能</h3>
<ul>
<li>支持导出为 HTML、Markdown、TXT、PDF 格式</li>
<li>通过菜单"文件 → 导出"或右键菜单</li>
</ul>

<h3>🎨 快捷键</h3>
<ul>
<li><b>Ctrl+T</b> - 切换暗色/亮色主题</li>
<li><b>Ctrl+P</b> - 切换预览面板</li>
<li><b>Ctrl++</b> / <b>Ctrl+-</b> - 放大/缩小字体</li>
</ul>
"""
        dlg = QDialog(self)
        dlg.setWindowTitle("使用帮助")
        dlg.setMinimumSize(500, 600)
        layout = QVBoxLayout(dlg)

        browser = QTextBrowser()
        browser.setHtml(help_text)
        layout.addWidget(browser)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        dlg.exec()

    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于 QuickNote",
            f"""
<h2>QuickNote</h2>
<p>版本 {APP_VERSION}</p>
<p>轻量级 Markdown 笔记应用</p>
<br>
<p>✨ 功能特性:</p>
<ul>
<li>📝 Markdown 编辑与实时预览</li>
<li>📓 笔记本管理系统</li>
<li>🏷 标签筛选</li>
<li>🔍 全文搜索</li>
<li>📤 多格式导出</li>
<li>💾 自动保存</li>
<li>🎨 暗色/亮色主题</li>
<li>💻 代码语法高亮</li>
</ul>
<br>
<p>基于 PyQt6 构建</p>
<p>数据存储: {NOTES_DIR}</p>
"""
        )

    def _show_status(self, message: str, timeout: int = 3000):
        """显示状态消息"""
        self.status_label.setText(message)
        QTimer.singleShot(timeout, lambda: self.status_label.setText("就绪"))

    def _load_initial_state(self):
        """加载初始状态"""
        self._refresh_notebooks()

        # 恢复上次的笔记本
        last_nb = self.settings.get("last_notebook", "默认")
        idx = self.notebook_combo.findText(last_nb)
        if idx >= 0:
            self.notebook_combo.setCurrentIndex(idx)

        # 恢复上次的笔记
        last_note_path = self.settings.get("last_note")
        if last_note_path:
            for note in self.note_manager.notes:
                if str(note.filepath) == last_note_path:
                    self._load_note(note)
                    # 选中
                    for i in range(self.note_tree.topLevelItemCount()):
                        item = self.note_tree.topLevelItem(i)
                        if item.data(0, Qt.ItemDataRole.UserRole) == note:
                            self.note_tree.setCurrentItem(item)
                            break
                    break

        # 如果没有笔记，创建一个示例
        if not self.note_manager.notes:
            self._create_sample_note()

        # 设置编辑器字体大小
        font_size = self.settings.get("font_size", 14)
        font = self.editor.font()
        font.setPointSize(font_size)
        self.editor.setFont(font)

    def _create_sample_note(self):
        """创建示例笔记"""
        sample_content = """# 👋 欢迎使用 QuickNote

这是一个轻量级的 **Markdown 笔记应用**，帮助你高效记录和管理笔记。

## ✨ 主要功能

- 📝 **Markdown 编辑** - 支持丰富的 Markdown 语法
- 📖 **实时预览** - 左侧编辑，右侧即时预览
- 📓 **笔记本管理** - 用笔记本分类组织你的笔记
- 🏷 **标签系统** - 使用 #标签 快速分类和筛选
- 🔍 **全文搜索** - 快速找到你需要的内容
- 📤 **多格式导出** - 支持 HTML/Markdown/TXT/PDF
- 💾 **自动保存** - 无需担心丢失内容
- 🎨 **主题切换** - 暗色/亮色主题随心切换

## 📖 Markdown 示例

### 代码块

```python
def hello():
    print("Hello, QuickNote! 🎉")
    return "欢迎使用"
```

### 表格

| 功能 | 状态 | 快捷键 |
|------|------|--------|
| 新建笔记 | ✅ | Ctrl+N |
| 保存 | ✅ | Ctrl+S |
| 搜索 | ✅ | Ctrl+F |
| 切换主题 | ✅ | Ctrl+T |

### 引用

> 好记性不如烂笔头。
> 
> — 每一个认真记录的人

## 🏷 标签示例

这是一个带有 #欢迎 #教程 #入门 标签的笔记。

## 🚀 开始使用

1. 点击左侧 **"+"** 创建新笔记
2. 在编辑区用 Markdown 写作
3. 右侧实时查看预览效果
4. 使用标签整理你的笔记
5. 随时导出分享

---

💡 **提示**: 试试 `Ctrl+T` 切换暗色/亮色主题！

---

*QuickNote v{version} - 让记录更简单*
"""
        notebook = self.notebook_combo.currentText() or "默认"
        note = self.note_manager.create_note(notebook, "欢迎使用 QuickNote")
        note.content = sample_content.format(version=APP_VERSION)
        note._cached_title = "欢迎使用 QuickNote"
        note._cached_tags = ["欢迎", "教程", "入门"]
        self._refresh_note_list(notebook)
        self._load_note(note)

        # 选中
        for i in range(self.note_tree.topLevelItemCount()):
            item = self.note_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == note:
                self.note_tree.setCurrentItem(item)
                break

    # ------------------------------------------------------------------
    # 窗口事件
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存笔记
        if self.current_note:
            self._save_note()

        # 保存设置
        self.settings["last_notebook"] = self.notebook_combo.currentText()
        if self.current_note:
            self.settings["last_note"] = str(self.current_note.filepath)
        self._save_settings()

        event.accept()

    def _save_settings(self):
        """保存设置"""
        save_json(SETTINGS_FILE, self.settings)

    def resizeEvent(self, event):
        """窗口大小改变"""
        super().resizeEvent(event)


# ============================================================================
# 主入口
# ============================================================================

def main():
    """应用主入口"""
    # 确保目录存在
    ensure_dir(NOTES_DIR)
    ensure_dir(SETTINGS_FILE.parent)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("QuickNote")

    # 设置默认字体
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # 创建并显示主窗口
    window = QuickNoteWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
