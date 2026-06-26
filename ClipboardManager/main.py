"""
ClipboardManager - Windows 剪贴板历史管理器
============================================
功能：记录剪贴板历史、全文搜索、收藏置顶、快速粘贴、自动分类、导出、全局热键、系统托盘
"""

import sys
import os
import re
import json
import sqlite3
import base64
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QComboBox, QTextEdit, QSplitter,
    QFrame, QScrollArea, QStackedWidget, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QCheckBox, QGroupBox, QTabWidget,
    QGraphicsDropShadowEffect, QSizePolicy, QAbstractItemView,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem,
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QMimeData,
    QPropertyAnimation, QEasingCurve, QPoint, QRect,
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QClipboard, QAction, QFont,
    QColor, QPalette, QLinearGradient, QBrush, QPainter,
    QPen, QCursor, QKeySequence, QShortcut, QDesktopServices,
    QClipboard as QClipboardAlias,
)

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─────────────────────────── Paths ───────────────────────────
APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "ClipboardManager"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "clipboard.db"
ICON_DIR = APP_DIR / "icons"
ICON_DIR.mkdir(exist_ok=True)

# ─────────────────────────── Theme ───────────────────────────
DARK_BG = "#0a0a0a"
CARD_BG = "#111122"
CARD_BG_HOVER = "#1a1a33"
ACCENT_1 = "#667eea"
ACCENT_2 = "#764ba2"
TEXT_PRIMARY = "#e8e8f0"
TEXT_SECONDARY = "#8888aa"
TEXT_DIM = "#555577"
BORDER_COLOR = "#222244"
DANGER = "#ff4466"
SUCCESS = "#44cc88"
WARNING = "#ffaa44"

STYLESHEET = f"""
QMainWindow {{
    background-color: {DARK_BG};
}}
QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QLineEdit {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 10px 14px;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    selection-background-color: {ACCENT_1};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT_1};
}}
QPushButton {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 16px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {CARD_BG_HOVER};
    border: 1px solid {ACCENT_1};
}}
QPushButton:pressed {{
    background-color: {ACCENT_1};
}}
QPushButton#accentBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
    border: none;
    color: white;
    font-weight: bold;
}}
QPushButton#accentBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_1}dd, stop:1 {ACCENT_2}dd);
}}
QPushButton#pinBtn {{
    background-color: transparent;
    border: none;
    font-size: 16px;
    padding: 4px;
    min-width: 30px;
    max-width: 30px;
}}
QPushButton#pinBtn:hover {{
    background-color: {CARD_BG_HOVER};
    border-radius: 4px;
}}
QPushButton#categoryBtn {{
    background-color: {ACCENT_1}33;
    border: 1px solid {ACCENT_1}55;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    color: {ACCENT_1};
}}
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 4px;
    margin: 3px 6px;
}}
QListWidget::item:selected {{
    background-color: {CARD_BG_HOVER};
    border: 1px solid {ACCENT_1};
}}
QListWidget::item:hover {{
    background-color: {CARD_BG_HOVER};
    border: 1px solid {ACCENT_1}88;
}}
QComboBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 6px 12px;
    color: {TEXT_PRIMARY};
    min-width: 100px;
}}
QComboBox:hover {{
    border: 1px solid {ACCENT_1};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_1};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_COLOR};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_1}88;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    background: {CARD_BG};
}}
QTabBar::tab {{
    background: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    color: {TEXT_SECONDARY};
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {CARD_BG_HOVER};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT_1};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}
QLabel {{
    background: transparent;
}}
QLabel#titleLabel {{
    font-size: 20px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
}}
QLabel#subtitleLabel {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}
QLabel#countLabel {{
    font-size: 11px;
    color: {TEXT_DIM};
}}
QTextEdit {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px;
    color: {TEXT_PRIMARY};
}}
QMenu {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 4px;
    color: {TEXT_PRIMARY};
}}
QMenu::item {{
    padding: 8px 30px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT_1};
}}
QDialog {{
    background-color: {DARK_BG};
}}
QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER_COLOR};
    background: {CARD_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_1};
    border: 1px solid {ACCENT_1};
}}
"""


# ─────────────────────────── Database ───────────────────────────
class ClipDatabase:
    """SQLite database for clipboard history."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                content_hash TEXT,
                category TEXT DEFAULT 'text',
                is_pinned INTEGER DEFAULT 0,
                is_image INTEGER DEFAULT 0,
                image_data BLOB,
                image_thumbnail BLOB,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                last_used TEXT,
                use_count INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_clips_hash ON clips(content_hash);
            CREATE INDEX IF NOT EXISTS idx_clips_pinned ON clips(is_pinned);
            CREATE INDEX IF NOT EXISTS idx_clips_category ON clips(category);
            CREATE INDEX IF NOT EXISTS idx_clips_created ON clips(created_at);
            CREATE VIRTUAL TABLE IF NOT EXISTS clips_fts USING fts4(
                content, content='clips', content_rowid='id'
            );
            CREATE TRIGGER IF NOT EXISTS clips_ai AFTER INSERT ON clips BEGIN
                INSERT INTO clips_fts(rowid, content) VALUES (new.id, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS clips_ad AFTER DELETE ON clips BEGIN
                INSERT INTO clips_fts(clips_fts, rowid, content)
                    VALUES('delete', old.id, old.content);
            END;
            CREATE TRIGGER IF NOT EXISTS clips_au AFTER UPDATE ON clips BEGIN
                INSERT INTO clips_fts(clips_fts, rowid, content)
                    VALUES('delete', old.id, old.content);
                INSERT INTO clips_fts(rowid, content) VALUES (new.id, new.content);
            END;
        """)
        self.conn.commit()

    def add_clip(self, content: str, category: str = "text",
                 is_image: bool = False, image_data: bytes = None,
                 image_thumbnail: bytes = None) -> int | None:
        if is_image:
            h = hashlib.md5(image_data).hexdigest()
        else:
            h = hashlib.md5(content.encode("utf-8")).hexdigest()

        # Check duplicate - just update timestamp
        row = self.conn.execute(
            "SELECT id FROM clips WHERE content_hash=?", (h,)
        ).fetchone()
        if row:
            self.conn.execute(
                "UPDATE clips SET created_at=datetime('now','localtime'), "
                "use_count=use_count+1 WHERE id=?", (row[0],)
            )
            self.conn.commit()
            return None  # Signal: duplicate, not new

        cur = self.conn.execute(
            "INSERT INTO clips (content, content_hash, category, is_image, "
            "image_data, image_thumbnail) VALUES (?,?,?,?,?,?)",
            (content, h, category, int(is_image), image_data, image_thumbnail)
        )
        self.conn.commit()
        return cur.lastrowid

    def search(self, query: str, category: str = None, pinned_only: bool = False) -> list[dict]:
        if not query.strip():
            return self.get_clips(category=category, pinned_only=pinned_only)

        try:
            # Try FTS first
            terms = query.strip().split()
            fts_query = " OR ".join(f'"{t}"' for t in terms if t)
            rows = self.conn.execute(
                "SELECT c.id, c.content, c.category, c.is_pinned, c.is_image, "
                "c.image_data, c.image_thumbnail, c.created_at, c.use_count "
                "FROM clips c JOIN clips_fts f ON c.id = f.rowid "
                "WHERE clips_fts MATCH ? "
                "ORDER BY c.is_pinned DESC, c.created_at DESC LIMIT 200",
                (fts_query,)
            ).fetchall()
        except Exception:
            # Fallback to LIKE
            like = f"%{query}%"
            rows = self.conn.execute(
                "SELECT id, content, category, is_pinned, is_image, "
                "image_data, image_thumbnail, created_at, use_count "
                "FROM clips WHERE content LIKE ? "
                "ORDER BY is_pinned DESC, created_at DESC LIMIT 200",
                (like,)
            ).fetchall()

        return [self._row_to_dict(r) for r in rows]

    def get_clips(self, limit: int = 200, category: str = None,
                  pinned_only: bool = False) -> list[dict]:
        sql = ("SELECT id, content, category, is_pinned, is_image, "
               "image_data, image_thumbnail, created_at, use_count "
               "FROM clips WHERE 1=1")
        params = []
        if category and category != "全部":
            sql += " AND category=?"
            params.append(category)
        if pinned_only:
            sql += " AND is_pinned=1"
        sql += " ORDER BY is_pinned DESC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def toggle_pin(self, clip_id: int):
        self.conn.execute(
            "UPDATE clips SET is_pinned = 1 - is_pinned WHERE id=?", (clip_id,)
        )
        self.conn.commit()

    def delete_clip(self, clip_id: int):
        self.conn.execute("DELETE FROM clips WHERE id=?", (clip_id,))
        self.conn.commit()

    def clear_all(self, keep_pinned: bool = True):
        if keep_pinned:
            self.conn.execute("DELETE FROM clips WHERE is_pinned=0")
        else:
            self.conn.execute("DELETE FROM clips")
        self.conn.commit()

    def get_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]

    def export_json(self) -> str:
        rows = self.conn.execute(
            "SELECT content, category, is_pinned, created_at FROM clips "
            "ORDER BY is_pinned DESC, created_at DESC"
        ).fetchall()
        data = [
            {"content": r[0], "category": r[1], "pinned": bool(r[2]),
             "created_at": r[3]}
            for r in rows if r[0]
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)

    def export_txt(self) -> str:
        rows = self.conn.execute(
            "SELECT content, category, is_pinned, created_at FROM clips "
            "ORDER BY is_pinned DESC, created_at DESC"
        ).fetchall()
        lines = []
        for r in rows:
            if not r[0]:
                continue
            pin = " ★" if r[2] else ""
            lines.append(f"[{r[3]}] [{r[1]}]{pin}")
            lines.append(r[0])
            lines.append("─" * 60)
        return "\n".join(lines)

    def _row_to_dict(self, r) -> dict:
        return {
            "id": r[0], "content": r[1], "category": r[2],
            "is_pinned": bool(r[3]), "is_image": bool(r[4]),
            "image_data": r[5], "image_thumbnail": r[6],
            "created_at": r[7], "use_count": r[8],
        }


# ─────────────────────────── Category Detection ───────────────────────────
def detect_category(text: str) -> str:
    if not text:
        return "文本"
    text_stripped = text.strip()
    if re.match(r'^https?://', text_stripped):
        return "链接"
    if re.match(r'^[\w.+-]+@[\w-]+\.[\w.-]+$', text_stripped):
        return "邮箱"
    # Code detection heuristics
    code_patterns = [
        r'[\{\}\[\]];?\s*$', r'^\s*(def |class |import |from |function |const |let |var )',
        r'^\s*(if |for |while |return |try |catch )', r'=>|->|::',
        r'^\s*//', r'^\s*#(?!\\s)', r'console\.log|print\(|System\.out',
    ]
    for p in code_patterns:
        if re.search(p, text, re.MULTILINE):
            return "代码"
    # Number
    if re.match(r'^[\d.,]+$', text_stripped):
        return "数字"
    return "文本"


def get_category_icon(cat: str) -> str:
    return {
        "链接": "🔗", "邮箱": "📧", "代码": "💻",
        "文本": "📝", "图片": "🖼️", "数字": "🔢",
    }.get(cat, "📝")


# ─────────────────────────── Clip Widget ───────────────────────────
class ClipWidget(QWidget):
    """Custom widget for displaying a single clip in the list."""

    copy_requested = pyqtSignal(int)
    pin_toggled = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, clip_data: dict, parent=None):
        super().__init__(parent)
        self.clip_data = clip_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Pin button
        self.pin_btn = QPushButton()
        self.pin_btn.setObjectName("pinBtn")
        self.pin_btn.setText("📌" if self.clip_data["is_pinned"] else "📍")
        self.pin_btn.setToolTip("置顶" if not self.clip_data["is_pinned"] else "取消置顶")
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.clip_data["id"]))
        layout.addWidget(self.pin_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Category badge + timestamp
        meta_layout = QHBoxLayout()
        cat = self.clip_data["category"]
        cat_label = QLabel(f"{get_category_icon(cat)} {cat}")
        cat_label.setObjectName("categoryBtn")
        cat_label.setFixedHeight(22)
        meta_layout.addWidget(cat_label)
        meta_layout.addStretch()

        ts = self.clip_data.get("created_at", "")
        if ts:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                ts_text = dt.strftime("%m-%d %H:%M")
            except Exception:
                ts_text = ts
            ts_label = QLabel(ts_text)
            ts_label.setObjectName("countLabel")
            meta_layout.addWidget(ts_label)

        content_layout.addLayout(meta_layout)

        # Content preview
        if self.clip_data["is_image"]:
            preview = QLabel("🖼️ [图片]")
            preview.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
            # Show thumbnail if available
            td = self.clip_data.get("image_thumbnail")
            if td:
                pix = QPixmap()
                pix.loadFromData(td)
                if not pix.isNull():
                    scaled = pix.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                    preview.setPixmap(scaled)
            content_layout.addWidget(preview)
        else:
            text = self.clip_data.get("content", "")
            preview_text = text[:200].replace("\n", " ").replace("\r", "")
            if len(text) > 200:
                preview_text += "…"
            preview = QLabel(preview_text)
            preview.setWordWrap(True)
            preview.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; padding: 2px 0;")
            preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content_layout.addWidget(preview)

        layout.addLayout(content_layout, stretch=1)

        # Action buttons
        action_layout = QVBoxLayout()
        action_layout.setSpacing(4)

        copy_btn = QPushButton("复制")
        copy_btn.setToolTip("复制到剪贴板")
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setFixedWidth(56)
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.clip_data["id"]))
        action_layout.addWidget(copy_btn)

        del_btn = QPushButton("删除")
        del_btn.setToolTip("删除此记录")
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setFixedWidth(56)
        del_btn.setStyleSheet(f"QPushButton {{ color: {DANGER}; border-color: {DANGER}33; }}")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.clip_data["id"]))
        action_layout.addWidget(del_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)


class ClipListWidgetItem(QListWidgetItem):
    """List widget item that holds ClipWidget."""

    def __init__(self, clip_data: dict, parent=None):
        super().__init__(parent)
        self.clip_data = clip_data
        self.setSizeHint(QSize(0, 90))


# ─────────────────────────── Main Window ───────────────────────────
class ClipboardManagerWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.db = ClipDatabase()
        self.last_clip_content = ""
        self.last_clip_image_hash = ""
        self._is_shown = True

        self._init_window()
        self._init_ui()
        self._init_tray()
        self._init_clipboard_monitor()
        self._init_hotkey()
        self._refresh_list()

    def _init_window(self):
        self.setWindowTitle("剪贴板管理器")
        self.setMinimumSize(520, 600)
        self.resize(600, 750)
        # Icon
        self.setWindowIcon(self._create_app_icon())

    def _create_app_icon(self) -> QIcon:
        """Create a simple gradient icon programmatically."""
        pix = QPixmap(64, 64)
        pix.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 64, 64)
        grad.setColorAt(0, QColor(ACCENT_1))
        grad.setColorAt(1, QColor(ACCENT_2))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 56, 56, 14, 14)
        painter.setPen(QPen(QColor("white"), 3))
        painter.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        painter.drawText(QRect(4, 4, 56, 56), Qt.AlignmentFlag.AlignCenter, "C")
        painter.end()
        return QIcon(pix)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("📋 剪贴板管理器")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        self.count_label = QLabel("0 条记录")
        self.count_label.setObjectName("countLabel")
        header.addWidget(self.count_label)

        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip("设置")
        settings_btn.clicked.connect(self._show_settings)
        header.addWidget(settings_btn)

        main_layout.addLayout(header)

        # ── Search bar ──
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索剪贴板内容…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input, stretch=1)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["全部", "文本", "链接", "邮箱", "代码", "图片", "数字"])
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self.category_filter)

        main_layout.addLayout(search_layout)

        # ── Toolbar ──
        toolbar = QHBoxLayout()

        self.pin_filter_btn = QPushButton("📌 仅显示置顶")
        self.pin_filter_btn.setCheckable(True)
        self.pin_filter_btn.toggled.connect(self._on_filter_changed)
        toolbar.addWidget(self.pin_filter_btn)

        toolbar.addStretch()

        export_btn = QPushButton("📤 导出")
        export_btn.clicked.connect(self._export_history)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self._clear_history)
        toolbar.addWidget(clear_btn)

        main_layout.addLayout(toolbar)

        # ── Clip list ──
        self.clip_list = QListWidget()
        self.clip_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.clip_list.setSpacing(2)
        main_layout.addWidget(self.clip_list, stretch=1)

        # ── Status bar ──
        status = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("subtitleLabel")
        status.addWidget(self.status_label)
        status.addStretch()

        hotkey_label = QLabel("Ctrl+Shift+V 显示/隐藏")
        hotkey_label.setObjectName("countLabel")
        status.addWidget(hotkey_label)
        main_layout.addLayout(status)

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self._create_app_icon(), self)
        self.tray.setToolTip("剪贴板管理器 - 运行中")

        menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        menu.addSeparator()

        export_json_action = QAction("导出为 JSON", self)
        export_json_action.triggered.connect(lambda: self._do_export("json"))
        menu.addAction(export_json_action)

        export_txt_action = QAction("导出为 TXT", self)
        export_txt_action.triggered.connect(lambda: self._do_export("txt"))
        menu.addAction(export_txt_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _init_clipboard_monitor(self):
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)
        # Initial check
        self._check_clipboard()

    def _init_hotkey(self):
        if HAS_KEYBOARD:
            try:
                keyboard.add_hotkey('ctrl+shift+v', self._toggle_visibility)
                self.status_label.setText("全局热键已注册 (Ctrl+Shift+V)")
            except Exception as e:
                self.status_label.setText(f"热键注册失败: {e}")
        else:
            self.status_label.setText("提示: 安装 keyboard 库以启用全局热键")

    def _toggle_visibility(self):
        # Must use signal to call from non-Qt thread
        QTimer.singleShot(0, self._do_toggle)

    def _do_toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self._is_shown = True

    def _on_clipboard_changed(self):
        QTimer.singleShot(100, self._check_clipboard)

    def _check_clipboard(self):
        mime = self.clipboard.mimeData()
        if mime.hasImage():
            img = self.clipboard.image()
            if img and not img.isNull():
                img_hash = hashlib.md5(img.bits().asstring(img.sizeInBytes())).hexdigest() if img.sizeInBytes() > 0 else ""
                if img_hash != self.last_clip_image_hash:
                    self.last_clip_image_hash = img_hash
                    # Save image data
                    ba = BytesIO()
                    # Convert QImage to bytes
                    pix = QPixmap.fromImage(img)
                    buf = BytesIO()
                    pix.save(buf, "PNG")
                    img_data = buf.getvalue()
                    # Thumbnail
                    thumb = BytesIO()
                    scaled = pix.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                    scaled.save(thumb, "PNG")
                    self.db.add_clip(
                        content=f"[图片 {img.width()}x{img.height()}]",
                        category="图片", is_image=True,
                        image_data=img_data,
                        image_thumbnail=thumb.getvalue()
                    )
                    self._refresh_list()
            return

        if mime.hasText():
            text = mime.text()
            if text and text != self.last_clip_content:
                self.last_clip_content = text
                cat = detect_category(text)
                self.db.add_clip(content=text, category=cat)
                self._refresh_list()

    def _refresh_list(self):
        query = self.search_input.text().strip()
        cat = self.category_filter.currentText()
        pinned = self.pin_filter_btn.isChecked()

        if query:
            clips = self.db.search(query, category=cat, pinned_only=pinned)
        else:
            clips = self.db.get_clips(category=cat, pinned_only=pinned)

        self.clip_list.clear()
        for clip in clips:
            item = ClipListWidgetItem(clip)
            widget = ClipWidget(clip)
            widget.copy_requested.connect(self._copy_clip)
            widget.pin_toggled.connect(self._toggle_pin)
            widget.delete_requested.connect(self._delete_clip)
            self.clip_list.addItem(item)
            self.clip_list.setItemWidget(item, widget)

        total = self.db.get_count()
        self.count_label.setText(f"{total} 条记录 | 显示 {len(clips)} 条")

    def _on_search(self, text):
        self._refresh_list()

    def _on_filter_changed(self, *args):
        self._refresh_list()

    def _copy_clip(self, clip_id: int):
        clips = self.db.get_clips(limit=9999)
        for c in clips:
            if c["id"] == clip_id:
                if c["is_image"] and c["image_data"]:
                    img = QImage()
                    img.loadFromData(c["image_data"])
                    self.clipboard.setImage(img)
                else:
                    self.clipboard.setText(c["content"])
                self.last_clip_content = c.get("content", "")
                self.status_label.setText(f"已复制到剪贴板 ✓")
                QTimer.singleShot(2000, lambda: self.status_label.setText("就绪"))
                break

    def _toggle_pin(self, clip_id: int):
        self.db.toggle_pin(clip_id)
        self._refresh_list()

    def _delete_clip(self, clip_id: int):
        self.db.delete_clip(clip_id)
        self._refresh_list()

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有剪贴板历史记录吗？\n（置顶记录将保留）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all(keep_pinned=True)
            self._refresh_list()
            self.status_label.setText("历史已清空 ✓")

    def _export_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("导出剪贴板历史")
        dialog.setFixedSize(360, 200)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("选择导出格式：")
        label.setStyleSheet(f"font-size: 14px; color: {TEXT_PRIMARY};")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        json_btn = QPushButton("📄 JSON 格式")
        json_btn.setObjectName("accentBtn")
        json_btn.clicked.connect(lambda: (dialog.accept(), self._do_export("json")))
        btn_layout.addWidget(json_btn)

        txt_btn = QPushButton("📝 TXT 格式")
        txt_btn.setObjectName("accentBtn")
        txt_btn.clicked.connect(lambda: (dialog.accept(), self._do_export("txt")))
        btn_layout.addWidget(txt_btn)
        layout.addLayout(btn_layout)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        layout.addStretch()
        dialog.exec()

    def _do_export(self, fmt: str):
        ext = "json" if fmt == "json" else "txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出", f"clipboard_export.{ext}",
            f"{'JSON 文件' if fmt == 'json' else '文本文件'} (*.{ext})"
        )
        if not path:
            return
        content = self.db.export_json() if fmt == "json" else self.db.export_txt()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.status_label.setText(f"已导出到 {path} ✓")
        QTimer.singleShot(4000, lambda: self.status_label.setText("就绪"))

    def _show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setFixedSize(420, 320)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⚙️ 设置")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Hotkey info
        group1 = QGroupBox("全局热键")
        g1_layout = QVBoxLayout(group1)
        g1_layout.addWidget(QLabel("显示/隐藏窗口: Ctrl + Shift + V"))
        g1_layout.addWidget(QLabel(f"热键库状态: {'已安装' if HAS_KEYBOARD else '未安装 (pip install keyboard)'}"))
        layout.addWidget(group1)

        # Database info
        group2 = QGroupBox("数据库")
        g2_layout = QVBoxLayout(group2)
        g2_layout.addWidget(QLabel(f"数据库路径: {DB_PATH}"))
        g2_layout.addWidget(QLabel(f"记录数量: {self.db.get_count()}"))
        open_btn = QPushButton("打开数据库目录")
        open_btn.clicked.connect(lambda: os.startfile(str(DB_PATH.parent)))
        g2_layout.addWidget(open_btn)
        layout.addWidget(group2)

        layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("accentBtn")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "剪贴板管理器",
            "已最小化到系统托盘，继续在后台运行。\nCtrl+Shift+V 可快速打开。",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def _quit_app(self):
        if HAS_KEYBOARD:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        self.tray.hide()
        QApplication.quit()


# ─────────────────────────── Entry Point ───────────────────────────
def main():
    # High DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("剪贴板管理器")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    app.setStyleSheet(STYLESHEET)

    # Set app-wide font
    font = QFont("Microsoft YaHei", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = ClipboardManagerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
