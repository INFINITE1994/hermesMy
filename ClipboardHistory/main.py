"""
剪贴板历史管理工具 (ClipboardHistory)
增强版桌面剪贴板管理器 — PyQt6
"""

import sys
import os
import json
import uuid
import base64
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSystemTrayIcon, QMenu, QTabWidget, QFileDialog, QMessageBox,
    QFrame, QSplitter, QTextEdit, QScrollArea, QGridLayout,
    QAbstractItemView, QStyledItemDelegate, QStyle, QSizePolicy,
    QGraphicsDropShadowEffect, QToolButton, QComboBox,
)
from PyQt6.QtCore import (
    Qt, QTimer, QMimeData, QSize, pyqtSignal, QThread, QUrl, QSettings,
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QClipboard, QColor, QPainter,
    QLinearGradient, QFont, QAction, QDesktopServices, QPen, QBrush,
    QClipboard as QClipboardAlias,
)

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path.home() / ".clipboard_history"
HISTORY_FILE = DATA_DIR / "history.json"
IMAGES_DIR = DATA_DIR / "images"
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Style sheet
# ---------------------------------------------------------------------------
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #222244;
    border-radius: 6px;
    background: #0a0a0a;
}
QTabBar::tab {
    background: #111122;
    color: #8888aa;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1a1a33;
    color: #ffffff;
}
QLineEdit {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #667eea;
}
QLineEdit:focus {
    border: 1px solid #667eea;
}
QListWidget {
    background: #0a0a0a;
    border: 1px solid #181830;
    border-radius: 6px;
    outline: none;
}
QListWidget::item {
    background: #111122;
    border: 1px solid #181830;
    border-radius: 6px;
    padding: 10px;
    margin: 3px 6px;
    color: #d0d0e0;
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: #ffffff;
    border: 1px solid #667eea;
}
QListWidget::item:hover {
    background: #1a1a33;
    border: 1px solid #333366;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8ef8, stop:1 #8b5ec7);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5566cc, stop:1 #5e3d8a);
}
QPushButton#iconBtn {
    background: transparent;
    padding: 4px 8px;
    font-size: 16px;
}
QPushButton#iconBtn:hover {
    background: #1a1a33;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}
QLabel#subtitleLabel {
    color: #667eea;
    font-size: 12px;
}
QLabel#categoryBadge {
    background: #1a1a33;
    color: #667eea;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
}
QComboBox {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e0e0e0;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: #111122;
    color: #e0e0e0;
    selection-background-color: #667eea;
}
QTextEdit {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 6px;
    color: #d0d0e0;
    padding: 8px;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background: #0a0a0a;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #333355;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #667eea;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QMenu {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 6px;
    padding: 4px;
    color: #e0e0e0;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #667eea;
    color: #ffffff;
}
"""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
class ClipItem:
    """Represents a single clipboard entry."""

    CATEGORIES = {
        "url": "🔗 URL",
        "email": "📧 邮箱",
        "code": "💻 代码",
        "number": "🔢 数字",
        "text": "📝 文本",
        "image": "🖼️ 图片",
        "file": "📁 文件路径",
    }

    def __init__(
        self,
        content: str = "",
        clip_type: str = "text",
        image_path: str = "",
        pinned: bool = False,
        created_at: str = "",
        clip_id: str = "",
    ):
        self.id = clip_id or str(uuid.uuid4())
        self.content = content
        self.clip_type = clip_type  # "text" or "image"
        self.image_path = image_path
        self.pinned = pinned
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.category = self._detect_category()

    def _detect_category(self) -> str:
        if self.clip_type == "image":
            return "image"
        text = self.content.strip()
        if re.match(r'^https?://', text):
            return "url"
        if re.match(r'^[\w.-]+@[\w.-]+\.\w+$', text):
            return "email"
        if re.match(r'^[A-Z]:\\', text) or text.startswith('\\\\'):
            return "file"
        if any(kw in text for kw in ('def ', 'class ', 'import ', 'function ',
                                      '{', '}', '=>', '```', 'SELECT ', 'CREATE ')):
            return "code"
        if re.match(r'^[\d.,\s\+\-\*/\=\(\)]+$', text) and len(text) < 80:
            return "number"
        return "text"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "clip_type": self.clip_type,
            "image_path": self.image_path,
            "pinned": self.pinned,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ClipItem":
        return cls(
            content=d.get("content", ""),
            clip_type=d.get("clip_type", "text"),
            image_path=d.get("image_path", ""),
            pinned=d.get("pinned", False),
            created_at=d.get("created_at", ""),
            clip_id=d.get("id", ""),
        )


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
class HistoryStore:
    """JSON-backed history store."""

    def __init__(self):
        self.items: list[ClipItem] = []
        self.load()

    def load(self):
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                self.items = [ClipItem.from_dict(d) for d in data]
            except Exception:
                self.items = []

    def save(self):
        data = [item.to_dict() for item in self.items]
        HISTORY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, item: ClipItem):
        # Deduplicate: remove existing identical content
        self.items = [i for i in self.items if i.content != item.content
                      or i.clip_type != item.clip_type]
        # Pinned items stay on top
        self.items.insert(0, item)
        self.save()

    def remove(self, item_id: str):
        self.items = [i for i in self.items if i.id != item_id]
        self.save()

    def toggle_pin(self, item_id: str):
        for item in self.items:
            if item.id == item_id:
                item.pinned = not item.pinned
                break
        self.save()

    def export_json(self, path: str):
        data = [item.to_dict() for item in self.items]
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def import_json(self, path: str):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        imported = [ClipItem.from_dict(d) for d in data]
        existing_ids = {i.id for i in self.items}
        for item in imported:
            if item.id not in existing_ids:
                self.items.append(item)
        self.save()


# ---------------------------------------------------------------------------
# Custom list item widget
# ---------------------------------------------------------------------------
class ClipItemWidget(QWidget):
    """Custom widget for rendering a clip in the list."""

    def __init__(self, clip: ClipItem, parent=None):
        super().__init__(parent)
        self.clip = clip
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Pin indicator
        pin_label = QLabel("📌" if self.clip.pinned else "")
        pin_label.setFixedWidth(20)
        pin_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(pin_label)

        # Content area
        if self.clip.clip_type == "image" and self.clip.image_path:
            thumb = QLabel()
            pixmap = QPixmap(self.clip.image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    80, 60, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                thumb.setPixmap(scaled)
            else:
                thumb.setText("🖼️ 图片")
            thumb.setFixedSize(80, 60)
            thumb.setStyleSheet("border-radius: 4px; background: #181830;")
            layout.addWidget(thumb)
        else:
            # Text content
            content_area = QVBoxLayout()
            content_area.setSpacing(2)

            # Truncated preview
            preview = self.clip.content[:200]
            if len(self.clip.content) > 200:
                preview += "…"
            text_label = QLabel(preview)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("color: #d0d0e0; font-size: 12px;")
            text_label.setMaximumHeight(48)
            content_area.addWidget(text_label)

            # Meta row
            meta = QHBoxLayout()
            meta.setSpacing(8)
            cat_badge = QLabel(ClipItem.CATEGORIES.get(self.clip.category, "📝 文本"))
            cat_badge.setStyleSheet(
                "background: #1a1a33; color: #667eea; border-radius: 4px; "
                "padding: 1px 6px; font-size: 10px;"
            )
            cat_badge.setFixedHeight(18)
            meta.addWidget(cat_badge)

            time_label = QLabel(self.clip.created_at)
            time_label.setStyleSheet("color: #555577; font-size: 10px;")
            meta.addWidget(time_label)
            meta.addStretch()
            content_area.addLayout(meta)

            layout.addLayout(content_area, 1)

        # Action buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)

        copy_btn = QToolButton()
        copy_btn.setText("📋")
        copy_btn.setToolTip("复制到剪贴板")
        copy_btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; font-size: 16px; "
            "padding: 4px; border-radius: 4px; } "
            "QToolButton:hover { background: #222244; }"
        )
        copy_btn.setFixedSize(28, 28)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        pin_btn = QToolButton()
        pin_btn.setText("📌" if not self.clip.pinned else "📍")
        pin_btn.setToolTip("取消置顶" if self.clip.pinned else "置顶收藏")
        pin_btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; font-size: 16px; "
            "padding: 4px; border-radius: 4px; } "
            "QToolButton:hover { background: #222244; }"
        )
        pin_btn.setFixedSize(28, 28)
        btn_layout.addWidget(pin_btn)

        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if self.clip.clip_type == "image" and self.clip.image_path:
            pixmap = QPixmap(self.clip.image_path)
            clipboard.setPixmap(pixmap)
        else:
            clipboard.setText(self.clip.content)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class ClipboardHistoryWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.store = HistoryStore()
        self.setWindowTitle("📋 剪贴板历史管理")
        self.setMinimumSize(520, 600)
        self.resize(560, 700)
        self._build_ui()
        self._setup_tray()
        self._setup_hotkey()
        self._start_clipboard_monitor()
        self._refresh_list()

    # ---- UI construction ----
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("📋 剪贴板历史")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        # Export / Import buttons
        export_btn = QPushButton("📤 导出")
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self._export_history)
        header.addWidget(export_btn)

        import_btn = QPushButton("📥 导入")
        import_btn.setFixedHeight(32)
        import_btn.clicked.connect(self._import_history)
        header.addWidget(import_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setFixedHeight(32)
        clear_btn.setStyleSheet(
            "QPushButton { background: #332222; } "
            "QPushButton:hover { background: #442222; }"
        )
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)
        main_layout.addLayout(header)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索剪贴板历史…")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.addItem("全部分类", "")
        for key, label in ClipItem.CATEGORIES.items():
            self.category_filter.addItem(label, key)
        self.category_filter.currentIndexChanged.connect(self._on_search)
        self.category_filter.setFixedWidth(120)
        search_layout.addWidget(self.category_filter)

        main_layout.addLayout(search_layout)

        # Stats
        self.stats_label = QLabel("共 0 条记录")
        self.stats_label.setObjectName("subtitleLabel")
        main_layout.addWidget(self.stats_label)

        # Tabs: All / Pinned
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # All tab
        self.all_list = QListWidget()
        self.all_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.all_list.setSpacing(2)
        self.all_list.itemDoubleClicked.connect(self._on_item_double_click)
        self.all_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.all_list.customContextMenuRequested.connect(self._show_context_menu)
        self.tabs.addTab(self.all_list, "📋 全部记录")

        # Pinned tab
        self.pinned_list = QListWidget()
        self.pinned_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pinned_list.setSpacing(2)
        self.pinned_list.itemDoubleClicked.connect(self._on_item_double_click)
        self.pinned_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pinned_list.customContextMenuRequested.connect(self._show_context_menu)
        self.tabs.addTab(self.pinned_list, "📌 收藏夹")

        # Status bar
        self.statusBar().showMessage("就绪 — 复制内容即可自动记录")
        self.statusBar().setStyleSheet(
            "background: #080810; color: #555577; border-top: 1px solid #181830; "
            "padding: 4px; font-size: 11px;"
        )

    # ---- Tray ----
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        # Create a simple icon programmatically
        self.tray.setIcon(self._create_tray_icon())
        self.tray.setToolTip("剪贴板历史管理")

        menu = QMenu()
        show_action = menu.addAction("📋 显示主窗口")
        show_action.triggered.connect(self._show_window)
        menu.addSeparator()
        quit_action = menu.addAction("❌ 退出")
        quit_action.triggered.connect(self._quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _create_tray_icon(self) -> QIcon:
        """Generate a tray icon programmatically."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Gradient circle
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#764ba2"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, size - 8, size - 8, 12, 12)
        # Clipboard symbol
        painter.setPen(QPen(QColor("#ffffff"), 3))
        painter.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📋")
        painter.end()
        return QIcon(pixmap)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_app(self):
        self.clipboard_timer.stop()
        self.tray.hide()
        QApplication.instance().quit()

    # ---- Hotkey ----
    def _setup_hotkey(self):
        """Use QTimer-based polling as a fallback hotkey mechanism.
           On Windows, QShortcut with native key works too."""
        try:
            from PyQt6.QtGui import QShortcut, QKeySequence
            shortcut = QShortcut(QKeySequence("Ctrl+Alt+V"), self)
            shortcut.activated.connect(self._toggle_visibility)
        except Exception:
            pass

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self._show_window()

    # ---- Clipboard monitoring ----
    def _start_clipboard_monitor(self):
        self.clipboard = QApplication.clipboard()
        self.last_content = ""
        self.last_pixmap_hash = None
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self._check_clipboard)
        self.clipboard_timer.start(500)  # Check every 500ms

    def _check_clipboard(self):
        mime: QMimeData = self.clipboard.mimeData()

        # Image check
        if mime.hasImage():
            pixmap = self.clipboard.pixmap()
            if pixmap and not pixmap.isNull():
                phash = hash(pixmap.toImage().bits().asstring(
                    pixmap.width() * pixmap.height() * 4
                ) if hasattr(pixmap.toImage().bits(), 'asstring') else str(id(pixmap)))
                if phash != self.last_pixmap_hash:
                    self.last_pixmap_hash = phash
                    self._save_image_clip(pixmap)
            return

        # Text check
        if mime.hasText():
            text = mime.text()
            if text and text != self.last_content:
                self.last_content = text
                item = ClipItem(content=text, clip_type="text")
                self.store.add(item)
                self._refresh_list()
                self.statusBar().showMessage(
                    f"已记录: {text[:60]}…", 3000
                )

    def _save_image_clip(self, pixmap: QPixmap):
        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.png"
        fpath = IMAGES_DIR / fname
        pixmap.save(str(fpath), "PNG")
        item = ClipItem(
            content=f"[图片] {fname}",
            clip_type="image",
            image_path=str(fpath),
        )
        self.store.add(item)
        self._refresh_list()
        self.statusBar().showMessage("已记录图片", 3000)

    # ---- List management ----
    def _refresh_list(self, filter_text: str = "", category: str = ""):
        self.all_list.clear()
        self.pinned_list.clear()

        pinned_count = 0
        total = 0
        for item in self.store.items:
            # Filter
            if filter_text and filter_text.lower() not in item.content.lower():
                continue
            if category and item.category != category:
                continue

            total += 1
            widget = ClipItemWidget(item)
            list_item = QListWidgetItem()
            list_item.setSizeHint(widget.sizeHint() + QSize(0, 10))
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)

            self.all_list.addItem(list_item)
            self.all_list.setItemWidget(list_item, widget)

            if item.pinned:
                pinned_count += 1
                pinned_item = QListWidgetItem()
                pinned_item.setSizeHint(widget.sizeHint() + QSize(0, 10))
                pinned_item.setData(Qt.ItemDataRole.UserRole, item.id)
                pinned_widget = ClipItemWidget(item)
                self.pinned_list.addItem(pinned_item)
                self.pinned_list.setItemWidget(pinned_item, pinned_widget)

        self.stats_label.setText(
            f"共 {total} 条记录 | 📌 {pinned_count} 条收藏"
        )

    def _on_search(self):
        text = self.search_input.text().strip()
        category = self.category_filter.currentData() or ""
        self._refresh_list(filter_text=text, category=category)

    # ---- Actions ----
    def _on_item_double_click(self, item: QListWidgetItem):
        clip_id = item.data(Qt.ItemDataRole.UserRole)
        for clip in self.store.items:
            if clip.id == clip_id:
                clipboard = QApplication.clipboard()
                if clip.clip_type == "image" and clip.image_path:
                    pixmap = QPixmap(clip.image_path)
                    clipboard.setPixmap(pixmap)
                else:
                    clipboard.setText(clip.content)
                self.statusBar().showMessage("已复制到剪贴板 ✓", 2000)
                break

    def _show_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        if not item:
            return

        clip_id = item.data(Qt.ItemDataRole.UserRole)
        clip = next((c for c in self.store.items if c.id == clip_id), None)
        if not clip:
            return

        menu = QMenu(self)
        copy_action = menu.addAction("📋 复制到剪贴板")
        pin_action = menu.addAction(
            "📌 取消置顶" if clip.pinned else "📌 置顶收藏"
        )
        delete_action = menu.addAction("🗑️ 删除")
        menu.addSeparator()
        detail_action = menu.addAction("📄 查看详情")

        action = menu.exec(list_widget.mapToGlobal(pos))
        if action == copy_action:
            clipboard = QApplication.clipboard()
            if clip.clip_type == "image" and clip.image_path:
                clipboard.setPixmap(QPixmap(clip.image_path))
            else:
                clipboard.setText(clip.content)
            self.statusBar().showMessage("已复制到剪贴板 ✓", 2000)
        elif action == pin_action:
            self.store.toggle_pin(clip_id)
            self._on_search()
        elif action == delete_action:
            self.store.remove(clip_id)
            self._on_search()
        elif action == detail_action:
            self._show_detail(clip)

    def _show_detail(self, clip: ClipItem):
        msg = QMessageBox(self)
        msg.setWindowTitle("📋 详细信息")
        msg.setTextFormat(Qt.TextFormat.PlainText)
        detail = (
            f"类型: {ClipItem.CATEGORIES.get(clip.category, '未知')}\n"
            f"时间: {clip.created_at}\n"
            f"置顶: {'是' if clip.pinned else '否'}\n"
            f"ID: {clip.id}\n"
            f"\n--- 内容 ---\n{clip.content[:2000]}"
        )
        msg.setText(detail)
        msg.exec()

    def _export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "clipboard_history.json",
            "JSON 文件 (*.json)"
        )
        if path:
            self.store.export_json(path)
            self.statusBar().showMessage(f"已导出到 {path}", 3000)

    def _import_history(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入历史记录", "",
            "JSON 文件 (*.json)"
        )
        if path:
            try:
                self.store.import_json(path)
                self._on_search()
                self.statusBar().showMessage(f"已从 {path} 导入", 3000)
            except Exception as e:
                QMessageBox.warning(self, "导入失败", str(e))

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史记录吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.store.items = []
            self.store.save()
            self._refresh_list()
            self.statusBar().showMessage("已清空历史记录", 3000)

    # ---- Window events ----
    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "剪贴板历史管理",
            "程序已最小化到系统托盘，双击图标可打开。",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.search_input.setFocus()
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# App entry
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLESHEET)
    app.setApplicationName("剪贴板历史管理")
    app.setApplicationDisplayName("ClipboardHistory")

    window = ClipboardHistoryWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
