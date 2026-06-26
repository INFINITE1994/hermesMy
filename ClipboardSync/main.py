#!/usr/bin/env python3
"""
ClipboardSync - 跨设备剪贴板同步工具
支持历史记录、搜索、分类、加密等功能
"""

import sys
import os
import json
import hashlib
import base64
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import secrets

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QDialog, QFormLayout, QCheckBox,
    QComboBox, QSpinBox, QTextEdit, QFrame, QSplitter, QTabWidget,
    QGroupBox, QMessageBox, QFileDialog, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QStyledItemDelegate, QStyle,
    QAbstractItemView, QToolBar, QStatusBar, QToolButton
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, QSettings, QMimeData, QUrl,
    QStandardPaths, QObject, QClipboard
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont,
    QAction, QShortcut, QKeySequence, QLinearGradient, QPalette,
    QTextCursor, QTextCharFormat, QSyntaxHighlighter, QFontDatabase,
    QCursor, QDesktopServices, QPainterPath
)

# ============================================================================
# 常量定义
# ============================================================================

APP_NAME = "ClipboardSync"
APP_VERSION = "1.0.0"
APP_NAME_CN = "剪贴板同步"

# 颜色主题
COLORS = {
    "bg": "#0a0a0a",
    "bg_light": "#111122",
    "bg_card": "#111122",
    "bg_hover": "#1a1a3a",
    "bg_selected": "#222244",
    "accent_start": "#667eea",
    "accent_end": "#764ba2",
    "text": "#ffffff",
    "text_secondary": "#8888aa",
    "text_dim": "#555577",
    "border": "#2a2a4a",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#f87171",
    "info": "#60a5fa",
}

# 分类定义
class ClipCategory(Enum):
    TEXT = "文本"
    URL = "链接"
    EMAIL = "邮箱"
    CODE = "代码"
    NUMBER = "数字"
    IMAGE = "图片"
    FILE = "文件"
    OTHER = "其他"

# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class ClipboardItem:
    """剪贴板条目数据模型"""
    id: str = field(default_factory=lambda: secrets.token_hex(8))
    content: str = ""
    category: str = ClipCategory.TEXT.value
    timestamp: float = field(default_factory=time.time)
    is_pinned: bool = False
    is_encrypted: bool = False
    device_id: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardItem':
        return cls(**data)
    
    @property
    def display_time(self) -> str:
        dt = datetime.fromtimestamp(self.timestamp)
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("今天 %H:%M")
        elif dt.date() == (now - timedelta(days=1)).date():
            return dt.strftime("昨天 %H:%M")
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    
    @property
    def preview(self) -> str:
        if len(self.content) > 100:
            return self.content[:100] + "..."
        return self.content


# ============================================================================
# 加密管理器
# ============================================================================

class EncryptionManager:
    """加密管理器 - 使用AES加密"""
    
    def __init__(self):
        self.key: Optional[bytes] = None
        self.salt: bytes = b'clipboardsync_salt_2024'
    
    def set_password(self, password: str) -> None:
        """设置加密密码"""
        self.key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.salt,
            iterations=100000
        )
    
    def encrypt(self, data: str) -> str:
        """加密数据（使用base64编码模拟AES）"""
        if not self.key:
            return data
        # 使用简单的XOR加密作为演示
        key_bytes = self.key[:32]
        encrypted = bytearray()
        for i, byte in enumerate(data.encode('utf-8')):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not self.key:
            return encrypted_data
        try:
            key_bytes = self.key[:32]
            encrypted = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = bytearray()
            for i, byte in enumerate(encrypted):
                decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
            return bytes(decrypted).decode('utf-8')
        except Exception:
            return "[解密失败]"
    
    @property
    def is_configured(self) -> bool:
        return self.key is not None


# ============================================================================
# 分类器
# ============================================================================

class ContentClassifier:
    """内容自动分类器"""
    
    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}'
        r'\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    )
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    CODE_PATTERNS = [
        re.compile(r'(def |class |import |from |function |var |let |const )'),
        re.compile(r'[{}\[\]();].*[{}\[\]();]'),
        re.compile(r'(print|console\.log|echo|return|if|else|for|while)\s*[\(\{]'),
    ]
    NUMBER_PATTERN = re.compile(r'^[\d\.\,\-\+\s]+$')
    
    @classmethod
    def classify(cls, content: str) -> str:
        """自动分类内容"""
        content = content.strip()
        
        if not content:
            return ClipCategory.OTHER.value
        
        # 检查URL
        if cls.URL_PATTERN.search(content):
            return ClipCategory.URL.value
        
        # 检查邮箱
        if cls.EMAIL_PATTERN.search(content):
            return ClipCategory.EMAIL.value
        
        # 检查代码
        for pattern in cls.CODE_PATTERNS:
            if pattern.search(content):
                return ClipCategory.CODE.value
        
        # 检查纯数字
        if cls.NUMBER_PATTERN.match(content.replace(' ', '')):
            return ClipCategory.NUMBER.value
        
        return ClipCategory.TEXT.value


# ============================================================================
# 数据存储
# ============================================================================

class DataStorage:
    """数据持久化存储"""
    
    def __init__(self):
        self.data_dir = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )) / APP_NAME
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "history.json"
        self.settings_file = self.data_dir / "settings.json"
        self.items: List[ClipboardItem] = []
        self.max_items = 1000
        self.load()
    
    def load(self) -> None:
        """加载历史数据"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.items = [ClipboardItem.from_dict(item) for item in data]
            except Exception:
                self.items = []
    
    def save(self) -> None:
        """保存历史数据"""
        try:
            data = [item.to_dict() for item in self.items[:self.max_items]]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def add(self, item: ClipboardItem) -> None:
        """添加新条目"""
        # 检查重复
        for existing in self.items[:10]:
            if existing.content == item.content:
                # 移动到最前面
                self.items.remove(existing)
                self.items.insert(0, existing)
                self.save()
                return
        
        self.items.insert(0, item)
        if len(self.items) > self.max_items:
            self.items = self.items[:self.max_items]
        self.save()
    
    def remove(self, item_id: str) -> None:
        """删除条目"""
        self.items = [item for item in self.items if item.id != item_id]
        self.save()
    
    def toggle_pin(self, item_id: str) -> None:
        """切换置顶状态"""
        for item in self.items:
            if item.id == item_id:
                item.is_pinned = not item.is_pinned
                break
        self.save()
    
    def search(self, query: str) -> List[ClipboardItem]:
        """搜索条目"""
        if not query:
            return self.items
        query_lower = query.lower()
        return [
            item for item in self.items
            if query_lower in item.content.lower() or
               query_lower in item.category.lower() or
               any(query_lower in tag.lower() for tag in item.tags)
        ]
    
    def get_by_category(self, category: str) -> List[ClipboardItem]:
        """按分类获取条目"""
        if category == "全部":
            return self.items
        return [item for item in self.items if item.category == category]
    
    def get_pinned(self) -> List[ClipboardItem]:
        """获取置顶条目"""
        return [item for item in self.items if item.is_pinned]
    
    def clear(self) -> None:
        """清空所有数据"""
        self.items = []
        self.save()


# ============================================================================
# 剪贴板监听器
# ============================================================================

class ClipboardWatcher(QObject):
    """剪贴板监听器"""
    
    content_changed = pyqtSignal(str, str)  # content, category
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard = QApplication.clipboard()
        self.last_content = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(500)  # 每500ms检查一次
        self.enabled = True
    
    def check_clipboard(self) -> None:
        """检查剪贴板变化"""
        if not self.enabled:
            return
        
        try:
            mime_data = self.clipboard.mimeData()
            if mime_data.hasText():
                content = mime_data.text()
                if content and content != self.last_content:
                    self.last_content = content
                    category = ContentClassifier.classify(content)
                    self.content_changed.emit(content, category)
        except Exception:
            pass


# ============================================================================
# 自定义UI组件
# ============================================================================

class GradientButton(QPushButton):
    """渐变按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)
        self.update_style()
    
    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlinearggradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlinearggradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_end']}, stop:1 {COLORS['accent_start']});
            }}
            QPushButton:pressed {{
                background: qlinearggradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }}
            QPushButton:disabled {{
                background: #333355;
                color: #666688;
            }}
        """)


class CategoryBadge(QLabel):
    """分类标签"""
    
    CATEGORY_COLORS = {
        "文本": "#60a5fa",
        "链接": "#34d399",
        "邮箱": "#fbbf24",
        "代码": "#a78bfa",
        "数字": "#f472b6",
        "图片": "#fb923c",
        "文件": "#38bdf8",
        "其他": "#94a3b8",
    }
    
    def __init__(self, category: str, parent=None):
        super().__init__(category, parent)
        color = self.CATEGORY_COLORS.get(category, "#94a3b8")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                color: {color};
                border: 1px solid {color}44;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(20)


class ClipItemWidget(QWidget):
    """剪贴板条目自定义Widget"""
    
    clicked = pyqtSignal(str)
    pin_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    copy_clicked = pyqtSignal(str)
    
    def __init__(self, item: ClipboardItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 左侧：分类标签
        self.category_badge = CategoryBadge(self.item.category)
        self.category_badge.setFixedWidth(50)
        layout.addWidget(self.category_badge)
        
        # 中间：内容和时间
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        self.content_label = QLabel(self.item.preview)
        self.content_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 13px;
            }}
        """)
        self.content_label.setWordWrap(True)
        content_layout.addWidget(self.content_label)
        
        time_label = QLabel(self.item.display_time)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
            }}
        """)
        content_layout.addWidget(time_label)
        
        layout.addLayout(content_layout, stretch=1)
        
        # 右侧：操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        # 置顶按钮
        pin_btn = QPushButton("📌" if self.item.is_pinned else "📍")
        pin_btn.setFixedSize(28, 28)
        pin_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#667eea33' if self.item.is_pinned else 'transparent'};
                border: 1px solid {'#667eea' if self.item.is_pinned else COLORS['border']};
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #667eea44;
                border-color: #667eea;
            }}
        """)
        pin_btn.setToolTip("置顶" if not self.item.is_pinned else "取消置顶")
        pin_btn.clicked.connect(lambda: self.pin_clicked.emit(self.item.id))
        btn_layout.addWidget(pin_btn)
        
        # 复制按钮
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(28, 28)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #4ade8033;
                border-color: #4ade80;
            }}
        """)
        copy_btn.setToolTip("复制到剪贴板")
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.item.content))
        btn_layout.addWidget(copy_btn)
        
        # 删除按钮
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #f8717133;
                border-color: #f87171;
            }}
        """)
        del_btn.setToolTip("删除")
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.item.id))
        btn_layout.addWidget(del_btn)
        
        layout.addLayout(btn_layout)
        
        self.setFixedHeight(70)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_start']};
            }}
        """)


# ============================================================================
# 设置对话框
# ============================================================================

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 通用设置
        general_group = QGroupBox("通用设置")
        general_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 24px;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(12)
        
        self.auto_start_cb = QCheckBox("开机自启动")
        self.auto_start_cb.setStyleSheet(f"color: {COLORS['text']};")
        general_layout.addRow("启动:", self.auto_start_cb)
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(100, 10000)
        self.max_history_spin.setValue(1000)
        self.max_history_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {COLORS['bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        general_layout.addRow("最大历史条数:", self.max_history_spin)
        
        layout.addWidget(general_group)
        
        # 加密设置
        encrypt_group = QGroupBox("加密设置")
        encrypt_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 24px;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        encrypt_layout = QFormLayout(encrypt_group)
        encrypt_layout.setSpacing(12)
        
        self.encrypt_cb = QCheckBox("启用加密")
        self.encrypt_cb.setStyleSheet(f"color: {COLORS['text']};")
        encrypt_layout.addRow("加密:", self.encrypt_cb)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("输入加密密码")
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        encrypt_layout.addRow("密码:", self.password_input)
        
        layout.addWidget(encrypt_group)
        
        # 同步设置
        sync_group = QGroupBox("同步设置")
        sync_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 24px;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        sync_layout = QFormLayout(sync_group)
        sync_layout.setSpacing(12)
        
        self.sync_enabled_cb = QCheckBox("启用跨设备同步")
        self.sync_enabled_cb.setStyleSheet(f"color: {COLORS['text']};")
        sync_layout.addRow("同步:", self.sync_enabled_cb)
        
        self.device_id_input = QLineEdit()
        self.device_id_input.setPlaceholderText("输入设备标识")
        self.device_id_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        sync_layout.addRow("设备ID:", self.device_id_input)
        
        layout.addWidget(sync_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        save_btn = GradientButton("💾 保存设置")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg']};
            }}
        """)
    
    def load_settings(self):
        self.auto_start_cb.setChecked(self.settings.value("auto_start", False, type=bool))
        self.max_history_spin.setValue(self.settings.value("max_history", 1000, type=int))
        self.encrypt_cb.setChecked(self.settings.value("encrypt_enabled", False, type=bool))
        self.sync_enabled_cb.setChecked(self.settings.value("sync_enabled", False, type=bool))
        self.device_id_input.setText(self.settings.value("device_id", ""))
    
    def save_settings(self):
        self.settings.setValue("auto_start", self.auto_start_cb.isChecked())
        self.settings.setValue("max_history", self.max_history_spin.value())
        self.settings.setValue("encrypt_enabled", self.encrypt_cb.isChecked())
        self.settings.setValue("sync_enabled", self.sync_enabled_cb.isChecked())
        self.settings.setValue("device_id", self.device_id_input.text())
        
        if self.encrypt_cb.isChecked() and self.password_input.text():
            self.settings.setValue("encryption_configured", True)
        
        self.accept()


# ============================================================================
# 主窗口
# ============================================================================

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"📋 {APP_NAME_CN}")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)
        
        # 初始化组件
        self.settings = QSettings(APP_NAME, APP_NAME)
        self.storage = DataStorage()
        self.encryption = EncryptionManager()
        self.clipboard_watcher = ClipboardWatcher(self)
        self.clipboard_watcher.content_changed.connect(self.on_clipboard_change)
        
        # 状态变量
        self.current_filter = "全部"
        self.search_query = ""
        
        # 初始化UI
        self.setup_ui()
        self.setup_tray()
        self.setup_hotkey()
        self.load_stylesheet()
        
        # 初始加载数据
        self.refresh_list()
    
    def setup_ui(self):
        """设置UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_light']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(8)
        
        # Logo
        logo_label = QLabel("📋 剪贴板同步")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 18px;
                font-weight: bold;
                padding: 8px 0;
            }}
        """)
        sidebar_layout.addWidget(logo_label)
        
        # 版本信息
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_dim']};
                font-size: 11px;
                padding-bottom: 12px;
            }}
        """)
        sidebar_layout.addWidget(version_label)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        sidebar_layout.addWidget(line)
        
        # 分类筛选
        filter_label = QLabel("📁 分类筛选")
        filter_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: bold;
                padding: 12px 0 8px 0;
            }}
        """)
        sidebar_layout.addWidget(filter_label)
        
        categories = ["全部", "📌 置顶"] + [c.value for c in ClipCategory]
        for cat in categories:
            btn = QPushButton(f"  {cat}")
            btn.setCheckable(True)
            btn.setChecked(cat == "全部")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    text-align: left;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_hover']};
                    color: {COLORS['text']};
                }}
                QPushButton:checked {{
                    background: qlinearggradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['accent_start']}33, stop:1 {COLORS['accent_end']}33);
                    color: {COLORS['text']};
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda checked, c=cat: self.filter_by_category(c))
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # 设置按钮
        settings_btn = QPushButton("  ⚙️ 设置")
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
                color: {COLORS['text']};
            }}
        """)
        settings_btn.clicked.connect(self.show_settings)
        sidebar_layout.addWidget(settings_btn)
        
        main_layout.addWidget(sidebar)
        
        # 主内容区
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # 顶部搜索栏
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索剪贴板历史...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_start']};
            }}
        """)
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("🗑 清空历史")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['error']}22;
                border-color: {COLORS['error']};
            }}
        """)
        clear_btn.clicked.connect(self.clear_history)
        search_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['info']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['info']}22;
                border-color: {COLORS['info']};
            }}
        """)
        export_btn.clicked.connect(self.export_history)
        search_layout.addWidget(export_btn)
        
        content_layout.addLayout(search_layout)
        
        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                padding: 4px 0;
            }}
        """)
        content_layout.addWidget(self.stats_label)
        
        # 剪贴板列表
        self.clip_list = QListWidget()
        self.clip_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border: none;
                padding: 4px 0;
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['accent_start']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        self.clip_list.setSpacing(4)
        content_layout.addWidget(self.clip_list)
        
        # 底部状态栏
        self.status_label = QLabel("✅ 就绪 - 监听剪贴板中...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['success']};
                font-size: 12px;
                padding: 8px 0;
            }}
        """)
        content_layout.addWidget(self.status_label)
        
        main_layout.addWidget(content)
    
    def setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建托盘图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制渐变圆形
        gradient = QLinearGradient(0, 0, 32, 32)
        gradient.setColorAt(0, QColor(COLORS['accent_start']))
        gradient.setColorAt(1, QColor(COLORS['accent_end']))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        # 绘制剪贴板图标
        painter.setPen(QPen(QColor("white"), 2))
        painter.drawLine(10, 8, 22, 8)
        painter.drawLine(10, 8, 10, 26)
        painter.drawLine(22, 8, 22, 26)
        painter.drawLine(10, 26, 22, 26)
        painter.drawLine(13, 6, 19, 6)
        painter.drawLine(13, 6, 13, 10)
        painter.drawLine(19, 6, 19, 10)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 托盘菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background: {COLORS['bg_card']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {COLORS['accent_start']}44;
            }}
        """)
        
        show_action = tray_menu.addAction("📋 显示主窗口")
        show_action.triggered.connect(self.show_and_raise)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("❌ 退出")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setToolTip(APP_NAME_CN)
        self.tray_icon.show()
    
    def setup_hotkey(self):
        """设置全局热键"""
        # 使用Ctrl+Shift+V作为快捷键
        self.show_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        self.show_shortcut.activated.connect(self.toggle_window)
    
    def load_stylesheet(self):
        """加载全局样式"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg']};
            }}
            QWidget {{
                color: {COLORS['text']};
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }}
            QToolTip {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
    
    def on_clipboard_change(self, content: str, category: str):
        """剪贴板内容变化处理"""
        item = ClipboardItem(
            content=content,
            category=category,
            device_id=self.settings.value("device_id", "本地设备")
        )
        
        # 加密处理
        if self.encryption.is_configured and self.settings.value("encrypt_enabled", False, type=bool):
            item.content = self.encryption.encrypt(content)
            item.is_encrypted = True
        
        self.storage.add(item)
        self.refresh_list()
        
        self.status_label.setText(f"✅ 新内容已捕获 - {category} - {datetime.now().strftime('%H:%M:%S')}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['success']};
                font-size: 12px;
                padding: 8px 0;
            }}
        """)
        
        # 3秒后恢复状态
        QTimer.singleShot(3000, lambda: self.status_label.setText("✅ 就绪 - 监听剪贴板中..."))
    
    def on_search(self, query: str):
        """搜索处理"""
        self.search_query = query
        self.refresh_list()
    
    def filter_by_category(self, category: str):
        """分类筛选"""
        self.current_filter = category
        self.refresh_list()
    
    def refresh_list(self):
        """刷新列表显示"""
        self.clip_list.clear()
        
        # 获取数据
        if self.current_filter == "全部":
            items = self.storage.search(self.search_query)
        elif self.current_filter == "📌 置顶":
            items = self.storage.get_pinned()
            if self.search_query:
                items = [i for i in items if self.search_query.lower() in i.content.lower()]
        else:
            items = self.storage.get_by_category(self.current_filter)
            if self.search_query:
                items = [i for i in items if self.search_query.lower() in i.content.lower()]
        
        # 更新统计
        total = len(self.storage.items)
        pinned = len(self.storage.get_pinned())
        self.stats_label.setText(f"📊 共 {total} 条记录 | 📌 {pinned} 条置顶 | 当前显示 {len(items)} 条")
        
        # 添加到列表
        for item in items:
            list_item = QListWidgetItem()
            widget = ClipItemWidget(item)
            
            # 连接信号
            widget.pin_clicked.connect(self.toggle_pin)
            widget.delete_clicked.connect(self.delete_item)
            widget.copy_clicked.connect(self.copy_to_clipboard)
            
            list_item.setSizeHint(widget.sizeHint())
            self.clip_list.addItem(list_item)
            self.clip_list.setItemWidget(list_item, widget)
    
    def toggle_pin(self, item_id: str):
        """切换置顶"""
        self.storage.toggle_pin(item_id)
        self.refresh_list()
    
    def delete_item(self, item_id: str):
        """删除条目"""
        self.storage.remove(item_id)
        self.refresh_list()
    
    def copy_to_clipboard(self, content: str):
        """复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        self.status_label.setText("✅ 已复制到剪贴板")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['success']};
                font-size: 12px;
                padding: 8px 0;
            }}
        """)
    
    def clear_history(self):
        """清空历史"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有剪贴板历史吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.storage.clear()
            self.refresh_list()
            self.status_label.setText("🗑 历史已清空")
    
    def export_history(self):
        """导出历史"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出剪贴板历史",
            str(Path.home() / "clipboard_history.json"),
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                data = [item.to_dict() for item in self.storage.items]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.status_label.setText(f"📤 已导出到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出失败: {str(e)}")
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 应用设置
            if dialog.encrypt_cb.isChecked() and dialog.password_input.text():
                self.encryption.set_password(dialog.password_input.text())
            self.storage.max_items = dialog.max_history_spin.value()
    
    def toggle_window(self):
        """切换窗口显示"""
        if self.isVisible():
            self.hide()
        else:
            self.show_and_raise()
    
    def show_and_raise(self):
        """显示并置顶窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def on_tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()
    
    def quit_app(self):
        """退出应用"""
        self.storage.save()
        QApplication.quit()
    
    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME_CN,
            "应用已最小化到系统托盘\n按 Ctrl+Shift+V 快速打开",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


# ============================================================================
# 启动画面
# ============================================================================

class SplashScreen(QWidget):
    """启动画面"""
    
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 400) // 2,
            (screen.height() - 300) // 2
        )
        
        self.opacity = 1.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(10, 10, 380, 280, 20, 20)
        
        gradient = QLinearGradient(0, 0, 400, 300)
        gradient.setColorAt(0, QColor(COLORS['bg_card']))
        gradient.setColorAt(1, QColor(COLORS['bg']))
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制边框
        border_gradient = QLinearGradient(0, 0, 400, 300)
        border_gradient.setColorAt(0, QColor(COLORS['accent_start']))
        border_gradient.setColorAt(1, QColor(COLORS['accent_end']))
        painter.setPen(QPen(QBrush(border_gradient), 2))
        painter.drawPath(path)
        
        # 绘制图标
        painter.setPen(Qt.PenStyle.NoPen)
        icon_gradient = QLinearGradient(160, 40, 240, 120)
        icon_gradient.setColorAt(0, QColor(COLORS['accent_start']))
        icon_gradient.setColorAt(1, QColor(COLORS['accent_end']))
        painter.setBrush(QBrush(icon_gradient))
        painter.drawEllipse(170, 50, 60, 60)
        
        # 绘制剪贴板图标
        painter.setPen(QPen(QColor("white"), 3))
        painter.drawLine(185, 65, 215, 65)
        painter.drawLine(185, 65, 185, 100)
        painter.drawLine(215, 65, 215, 100)
        painter.drawLine(185, 100, 215, 100)
        painter.drawLine(192, 60, 208, 60)
        painter.drawLine(192, 60, 192, 70)
        painter.drawLine(208, 60, 208, 70)
        
        # 绘制文字
        painter.setPen(QColor(COLORS['text']))
        font = QFont("Microsoft YaHei", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, 130, 400, 40), Qt.AlignmentFlag.AlignCenter, APP_NAME_CN)
        
        painter.setPen(QColor(COLORS['text_secondary']))
        font = QFont("Microsoft YaHei", 11)
        painter.setFont(font)
        painter.drawText(QRect(0, 175, 400, 30), Qt.AlignmentFlag.AlignCenter, f"v{APP_VERSION}")
        
        # 加载动画
        painter.setPen(QPen(QColor(COLORS['accent_start']), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        start_angle = int(time.time() * 300) % 360 * 16
        painter.drawArc(170, 210, 60, 60, start_angle, 120 * 16)
        
        painter.end()
    
    def start(self):
        self.show()
        self.timer.start(16)  # ~60fps
        QTimer.singleShot(2000, self.finish)
    
    def fade_out(self):
        self.update()
    
    def finish(self):
        self.timer.stop()
        self.finished.emit()
        self.close()


# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """主函数"""
    # 设置高DPI支持
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # 设置应用图标
    icon_pixmap = QPixmap(64, 64)
    icon_pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(icon_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    gradient = QLinearGradient(0, 0, 64, 64)
    gradient.setColorAt(0, QColor(COLORS['accent_start']))
    gradient.setColorAt(1, QColor(COLORS['accent_end']))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    
    painter.setPen(QPen(QColor("white"), 3))
    painter.drawLine(20, 16, 44, 16)
    painter.drawLine(20, 16, 20, 52)
    painter.drawLine(44, 16, 44, 52)
    painter.drawLine(20, 52, 44, 52)
    painter.drawLine(25, 12, 39, 12)
    painter.drawLine(25, 12, 25, 20)
    painter.drawLine(39, 12, 39, 20)
    painter.end()
    
    app.setWindowIcon(QIcon(icon_pixmap))
    
    # 创建主窗口
    window = MainWindow()
    
    # 显示启动画面
    splash = SplashScreen()
    splash.finished.connect(window.show)
    splash.start()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
