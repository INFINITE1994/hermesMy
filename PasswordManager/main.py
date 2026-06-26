#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全密码管理器 - AES-256 本地加密密码管理工具
"""

import sys
import os
import json
import csv
import sqlite3
import hashlib
import secrets
import string
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QSpinBox, QCheckBox, QTextEdit,
    QMessageBox, QHeaderView, QFrame, QProgressBar, QSystemTrayIcon,
    QMenu, QStyle, QFileDialog, QScrollArea, QGroupBox, QTabWidget,
    QSplitter, QToolButton, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize,
    pyqtSignal, QThread, QMimeData
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QAction, QClipboard, QFontDatabase
)

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


# ============================================================================
# 加密模块
# ============================================================================

class CryptoManager:
    """AES-256 加密管理器"""
    
    def __init__(self):
        self.backend = default_backend()
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
    
    def set_master_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """设置主密码并生成加密密钥"""
        if salt is None:
            salt = secrets.token_bytes(16)
        self._salt = salt
        
        # PBKDF2 密钥派生
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        self._key = kdf.derive(password.encode('utf-8'))
        return salt
    
    def encrypt(self, plaintext: str) -> str:
        """加密字符串"""
        if not self._key:
            raise ValueError("未设置主密码")
        
        # 生成随机 IV
        iv = secrets.token_bytes(16)
        
        # 填充数据
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        # 加密
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # 返回 Base64 编码的 IV + 密文
        return base64.b64encode(iv + ciphertext).decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """解密字符串"""
        if not self._key:
            raise ValueError("未设置主密码")
        
        # 解码 Base64
        data = base64.b64decode(encrypted.encode('utf-8'))
        
        # 提取 IV 和密文
        iv = data[:16]
        ciphertext = data[16:]
        
        # 解密
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 去除填充
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        
        return plaintext.decode('utf-8')
    
    def hash_password(self, password: str) -> str:
        """生成密码哈希（用于验证）"""
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return base64.b64encode(salt + key).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            data = base64.b64decode(hashed.encode('utf-8'))
            salt = data[:32]
            stored_key = data[32:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key == stored_key
        except Exception:
            return False


# ============================================================================
# 数据库模块
# ============================================================================

class DatabaseManager:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # 创建表
        cursor = self.conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 密码条目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title_encrypted TEXT NOT NULL,
                username_encrypted TEXT,
                password_encrypted TEXT NOT NULL,
                url_encrypted TEXT,
                notes_encrypted TEXT,
                category TEXT DEFAULT '其他',
                favorite INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '📁',
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, name)
            )
        ''')
        
        self.conn.commit()
        
        # 插入默认分类
        self._init_default_categories()
    
    def _init_default_categories(self):
        """初始化默认分类"""
        default_categories = [
            ('邮箱', '📧'),
            ('社交', '💬'),
            ('银行', '🏦'),
            ('购物', '🛒'),
            ('工作', '💼'),
            ('游戏', '🎮'),
            ('其他', '📁')
        ]
        
        cursor = self.conn.cursor()
        for name, icon in default_categories:
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO categories (user_id, name, icon) VALUES (?, ?, ?)',
                    (1, name, icon)  # 假设 user_id=1
                )
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()
    
    def create_user(self, username: str, password_hash: str, salt: str) -> bool:
        """创建用户"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                (username, password_hash, salt)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def add_entry(self, user_id: int, entry: Dict) -> bool:
        """添加密码条目"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO entries (user_id, title_encrypted, username_encrypted,
                password_encrypted, url_encrypted, notes_encrypted, category, favorite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                entry['title'],
                entry.get('username', ''),
                entry['password'],
                entry.get('url', ''),
                entry.get('notes', ''),
                entry.get('category', '其他'),
                entry.get('favorite', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加条目失败: {e}")
            return False
    
    def get_entries(self, user_id: int, category: Optional[str] = None) -> List[Dict]:
        """获取密码条目"""
        cursor = self.conn.cursor()
        if category and category != '全部':
            cursor.execute(
                'SELECT * FROM entries WHERE user_id = ? AND category = ? ORDER BY favorite DESC, updated_at DESC',
                (user_id, category)
            )
        else:
            cursor.execute(
                'SELECT * FROM entries WHERE user_id = ? ORDER BY favorite DESC, updated_at DESC',
                (user_id,)
            )
        return [dict(row) for row in cursor.fetchall()]
    
    def update_entry(self, entry_id: int, entry: Dict) -> bool:
        """更新密码条目"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE entries SET
                    title_encrypted = ?,
                    username_encrypted = ?,
                    password_encrypted = ?,
                    url_encrypted = ?,
                    notes_encrypted = ?,
                    category = ?,
                    favorite = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                entry['title'],
                entry.get('username', ''),
                entry['password'],
                entry.get('url', ''),
                entry.get('notes', ''),
                entry.get('category', '其他'),
                entry.get('favorite', 0),
                entry_id
            ))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def delete_entry(self, entry_id: int) -> bool:
        """删除密码条目"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def search_entries(self, user_id: int, query: str) -> List[Dict]:
        """搜索密码条目（在内存中解密后搜索）"""
        # 返回所有条目，在 UI 层进行解密搜索
        return self.get_entries(user_id)
    
    def get_categories(self, user_id: int) -> List[Dict]:
        """获取分类列表"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE user_id = ?', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_category(self, user_id: int, name: str, icon: str = '📁') -> bool:
        """添加分类"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO categories (user_id, name, icon) VALUES (?, ?, ?)',
                (user_id, name, icon)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# ============================================================================
# 密码生成器
# ============================================================================

class PasswordGenerator:
    """密码生成器"""
    
    @staticmethod
    def generate(
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_chars: str = ""
    ) -> str:
        """生成密码"""
        chars = ""
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_lowercase:
            chars += string.ascii_lowercase
        if use_digits:
            chars += string.digits
        if use_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 排除指定字符
        for char in exclude_chars:
            chars = chars.replace(char, "")
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        # 确保密码包含所有选中的字符类型
        password = []
        if use_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if use_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if use_digits:
            password.append(secrets.choice(string.digits))
        if use_symbols:
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            for char in exclude_chars:
                symbols = symbols.replace(char, "")
            if symbols:
                password.append(secrets.choice(symbols))
        
        # 填充剩余长度
        remaining = length - len(password)
        for _ in range(remaining):
            password.append(secrets.choice(chars))
        
        # 随机打乱
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    @staticmethod
    def calculate_strength(password: str) -> Dict[str, Any]:
        """计算密码强度"""
        if not password:
            return {'score': 0, 'level': '无', 'color': '#666666'}
        
        score = 0
        feedback = []
        
        # 长度检查
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if len(password) < 8:
            feedback.append('密码太短')
        
        # 字符类型检查
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in string.punctuation for c in password)
        
        char_types = sum([has_upper, has_lower, has_digit, has_symbol])
        score += char_types
        
        if not has_upper:
            feedback.append('建议添加大写字母')
        if not has_lower:
            feedback.append('建议添加小写字母')
        if not has_digit:
            feedback.append('建议添加数字')
        if not has_symbol:
            feedback.append('建议添加特殊符号')
        
        # 重复字符检查
        if len(set(password)) < len(password) * 0.7:
            score -= 1
            feedback.append('重复字符过多')
        
        # 连续字符检查
        for i in range(len(password) - 2):
            if (ord(password[i]) + 1 == ord(password[i+1]) == ord(password[i+2]) - 1):
                score -= 1
                feedback.append('包含连续字符')
                break
        
        # 计算最终分数
        max_score = 7
        percentage = max(0, min(100, int((score / max_score) * 100)))
        
        # 确定等级
        if percentage < 30:
            level = '弱'
            color = '#ff4444'
        elif percentage < 50:
            level = '一般'
            color = '#ffaa00'
        elif percentage < 70:
            level = '中等'
            color = '#ffff00'
        elif percentage < 90:
            level = '强'
            color = '#44ff44'
        else:
            level = '非常强'
            color = '#00ff88'
        
        return {
            'score': percentage,
            'level': level,
            'color': color,
            'feedback': feedback
        }


# ============================================================================
# UI 样式
# ============================================================================

class AppStyles:
    """应用程序样式"""
    
    MAIN_STYLE = """
    QMainWindow {
        background-color: #0a0a0a;
    }
    
    QWidget {
        background-color: #0a0a0a;
        color: #ffffff;
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    }
    
    QLabel {
        color: #ffffff;
        background: transparent;
    }
    
    QLineEdit, QTextEdit, QSpinBox {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 12px;
        color: #ffffff;
        font-size: 14px;
        selection-background-color: #667eea;
    }
    
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
        border: 2px solid #667eea;
    }
    
    QLineEdit:hover, QTextEdit:hover {
        border: 2px solid #3a3a5a;
    }
    
    QPushButton {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 20px;
        color: #ffffff;
        font-size: 14px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #2a2a4a;
        border: 2px solid #667eea;
    }
    
    QPushButton:pressed {
        background-color: #667eea;
    }
    
    QPushButton#primaryButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
        border: none;
        color: white;
        font-weight: bold;
    }
    
    QPushButton#primaryButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b8ef8, stop:1 #8b5fcf);
    }
    
    QPushButton#dangerButton {
        background-color: #dc3545;
        border: none;
    }
    
    QPushButton#dangerButton:hover {
        background-color: #ff4757;
    }
    
    QTableWidget {
        background-color: #111122;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        gridline-color: #2a2a4a;
        selection-background-color: #667eea;
        alternate-background-color: #151530;
    }
    
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #2a2a4a;
    }
    
    QTableWidget::item:selected {
        background-color: #667eea;
    }
    
    QHeaderView::section {
        background-color: #1a1a2e;
        color: #ffffff;
        padding: 10px;
        border: none;
        border-right: 1px solid #2a2a4a;
        border-bottom: 2px solid #667eea;
        font-weight: bold;
    }
    
    QComboBox {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 12px;
        color: #ffffff;
        font-size: 14px;
        min-width: 150px;
    }
    
    QComboBox:hover {
        border: 2px solid #3a3a5a;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #1a1a2e;
        border: 2px solid #667eea;
        selection-background-color: #667eea;
        color: #ffffff;
    }
    
    QCheckBox {
        color: #ffffff;
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid #2a2a4a;
        background-color: #1a1a2e;
    }
    
    QCheckBox::indicator:checked {
        background-color: #667eea;
        border: 2px solid #667eea;
    }
    
    QProgressBar {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        text-align: center;
        color: #ffffff;
        height: 25px;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
        border-radius: 6px;
    }
    
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QScrollBar:vertical {
        background-color: #0a0a0a;
        width: 10px;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #2a2a4a;
        border-radius: 5px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #667eea;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QGroupBox {
        background-color: #111122;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 15px;
        font-weight: bold;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 5px;
        color: #667eea;
    }
    
    QTabWidget::pane {
        background-color: #111122;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
    }
    
    QTabBar::tab {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 20px;
        color: #888888;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: #111122;
        color: #667eea;
        border-bottom: 2px solid #667eea;
    }
    
    QTabBar::tab:hover {
        color: #ffffff;
    }
    
    QMenu {
        background-color: #1a1a2e;
        border: 2px solid #2a2a4a;
        border-radius: 8px;
        padding: 5px;
    }
    
    QMenu::item {
        padding: 8px 20px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #667eea;
    }
    
    QToolButton {
        background-color: transparent;
        border: none;
        border-radius: 6px;
        padding: 5px;
        color: #888888;
    }
    
    QToolButton:hover {
        background-color: #2a2a4a;
        color: #ffffff;
    }
    """
    
    CARD_STYLE = """
    QFrame {
        background-color: #111122;
        border: 2px solid #2a2a4a;
        border-radius: 12px;
        padding: 15px;
    }
    
    QFrame:hover {
        border: 2px solid #3a3a5a;
    }
    """
    
    GRADIENT_BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        color: white;
        font-size: 14px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b8ef8, stop:1 #8b5fcf);
    }
    
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5570dd, stop:1 #653a91);
    }
    """


# ============================================================================
# 对话框
# ============================================================================

class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None, is_first_time=False):
        super().__init__(parent)
        self.is_first_time = is_first_time
        self.password = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("🔐 密码管理器 - 登录")
        self.setMinimumSize(400, 300)
        self.setStyleSheet(AppStyles.MAIN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # 标题
        title = QLabel("🔐 密码管理器")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #667eea; background: transparent;")
        layout.addWidget(title)
        
        # 副标题
        if self.is_first_time:
            subtitle = QLabel("首次使用，请设置主密码")
        else:
            subtitle = QLabel("请输入主密码")
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888; background: transparent;")
        layout.addWidget(subtitle)
        
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("输入主密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)
        
        # 确认密码（首次使用）
        if self.is_first_time:
            self.confirm_input = QLineEdit()
            self.confirm_input.setPlaceholderText("确认主密码")
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_input.returnPressed.connect(self.accept)
            layout.addWidget(self.confirm_input)
        
        # 错误提示
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4444; background: transparent;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        if not self.is_first_time:
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
        
        login_btn = QPushButton("确定" if self.is_first_time else "登录")
        login_btn.setObjectName("primaryButton")
        login_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(login_btn)
        
        layout.addLayout(btn_layout)
        
        self.password_input.setFocus()
    
    def validate_and_accept(self):
        password = self.password_input.text()
        
        if not password:
            self.error_label.setText("请输入密码")
            return
        
        if len(password) < 6:
            self.error_label.setText("密码至少需要6个字符")
            return
        
        if self.is_first_time:
            confirm = self.confirm_input.text()
            if password != confirm:
                self.error_label.setText("两次输入的密码不一致")
                return
        
        self.password = password
        self.accept()
    
    def get_password(self) -> Optional[str]:
        return self.password


class EntryDialog(QDialog):
    """密码条目编辑对话框"""
    
    def __init__(self, parent=None, entry=None, categories=None, crypto=None):
        super().__init__(parent)
        self.entry = entry
        self.categories = categories or []
        self.crypto = crypto
        self.setup_ui()
        
        if entry:
            self.load_entry()
    
    def setup_ui(self):
        self.setWindowTitle("✏️ 编辑密码" if self.entry else "➕ 添加密码")
        self.setMinimumSize(500, 600)
        self.setStyleSheet(AppStyles.MAIN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # 标题
        title = QLabel("✏️ 编辑密码" if self.entry else "➕ 添加新密码")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea; background: transparent;")
        layout.addWidget(title)
        
        # 表单
        form = QFormLayout()
        form.setSpacing(12)
        
        # 名称
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("例如：Gmail、微信、支付宝")
        form.addRow("名称:", self.title_input)
        
        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名/邮箱/手机号")
        form.addRow("用户名:", self.username_input)
        
        # 密码
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        
        show_btn = QPushButton("👁")
        show_btn.setFixedSize(40, 40)
        show_btn.setToolTip("显示/隐藏密码")
        show_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(show_btn)
        
        generate_btn = QPushButton("🎲")
        generate_btn.setFixedSize(40, 40)
        generate_btn.setToolTip("生成密码")
        generate_btn.clicked.connect(self.generate_password)
        password_layout.addWidget(generate_btn)
        
        form.addRow("密码:", password_layout)
        
        # 密码强度
        self.strength_bar = QProgressBar()
        self.strength_bar.setFixedHeight(8)
        self.strength_bar.setRange(0, 100)
        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 12px; background: transparent;")
        
        strength_layout = QVBoxLayout()
        strength_layout.addWidget(self.strength_bar)
        strength_layout.addWidget(self.strength_label)
        form.addRow("", strength_layout)
        
        self.password_input.textChanged.connect(self.update_strength)
        
        # 网址
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        form.addRow("网址:", self.url_input)
        
        # 分类
        self.category_combo = QComboBox()
        for cat in self.categories:
            self.category_combo.addItem(f"{cat['icon']} {cat['name']}", cat['name'])
        form.addRow("分类:", self.category_combo)
        
        # 备注
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("添加备注信息...")
        self.notes_input.setMaximumHeight(100)
        form.addRow("备注:", self.notes_input)
        
        layout.addLayout(form)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def generate_password(self):
        password = PasswordGenerator.generate(
            length=16,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_symbols=True
        )
        self.password_input.setText(password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
    
    def update_strength(self, text):
        result = PasswordGenerator.calculate_strength(text)
        self.strength_bar.setValue(result['score'])
        self.strength_label.setText(f"强度: {result['level']}")
        self.strength_label.setStyleSheet(f"color: {result['color']}; font-size: 12px; background: transparent;")
        
        # 更新进度条颜色
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {result['color']};
                border-radius: 6px;
            }}
        """)
    
    def load_entry(self):
        if not self.entry:
            return
        
        try:
            self.title_input.setText(self.crypto.decrypt(self.entry['title_encrypted']))
            self.username_input.setText(self.crypto.decrypt(self.entry['username_encrypted']) if self.entry['username_encrypted'] else '')
            self.password_input.setText(self.crypto.decrypt(self.entry['password_encrypted']))
            self.url_input.setText(self.crypto.decrypt(self.entry['url_encrypted']) if self.entry['url_encrypted'] else '')
            self.notes_input.setText(self.crypto.decrypt(self.entry['notes_encrypted']) if self.entry['notes_encrypted'] else '')
            
            # 设置分类
            category = self.entry.get('category', '其他')
            index = self.category_combo.findText(category, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载条目失败: {str(e)}")
    
    def validate_and_accept(self):
        title = self.title_input.text().strip()
        password = self.password_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "错误", "请输入名称")
            self.title_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "错误", "请输入密码")
            self.password_input.setFocus()
            return
        
        self.accept()
    
    def get_data(self) -> Dict:
        category = self.category_combo.currentData()
        return {
            'title': self.title_input.text().strip(),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text().strip(),
            'url': self.url_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'category': category if category else '其他'
        }


class PasswordGeneratorDialog(QDialog):
    """密码生成器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.generated_password = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("🎲 密码生成器")
        self.setMinimumSize(450, 500)
        self.setStyleSheet(AppStyles.MAIN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # 标题
        title = QLabel("🎲 密码生成器")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea; background: transparent;")
        layout.addWidget(title)
        
        # 生成的密码显示
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setFont(QFont("Consolas", 16))
        self.password_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_display.setMinimumHeight(50)
        layout.addWidget(self.password_display)
        
        # 密码强度
        self.strength_bar = QProgressBar()
        self.strength_bar.setFixedHeight(10)
        self.strength_bar.setRange(0, 100)
        layout.addWidget(self.strength_bar)
        
        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 12px; background: transparent;")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.strength_label)
        
        # 选项
        options_group = QGroupBox("生成选项")
        options_layout = QFormLayout(options_group)
        
        # 长度
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)
        self.length_spin.setFixedHeight(35)
        options_layout.addRow("密码长度:", self.length_spin)
        
        # 字符类型
        self.uppercase_check = QCheckBox("大写字母 (A-Z)")
        self.uppercase_check.setChecked(True)
        options_layout.addRow(self.uppercase_check)
        
        self.lowercase_check = QCheckBox("小写字母 (a-z)")
        self.lowercase_check.setChecked(True)
        options_layout.addRow(self.lowercase_check)
        
        self.digits_check = QCheckBox("数字 (0-9)")
        self.digits_check.setChecked(True)
        options_layout.addRow(self.digits_check)
        
        self.symbols_check = QCheckBox("特殊符号 (!@#$...)")
        self.symbols_check.setChecked(True)
        options_layout.addRow(self.symbols_check)
        
        layout.addWidget(options_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        generate_btn = QPushButton("🔄 生成密码")
        generate_btn.setObjectName("primaryButton")
        generate_btn.clicked.connect(self.generate)
        btn_layout.addWidget(generate_btn)
        
        copy_btn = QPushButton("📋 复制")
        copy_btn.clicked.connect(self.copy_password)
        btn_layout.addWidget(copy_btn)
        
        layout.addLayout(btn_layout)
        
        # 确认按钮
        use_btn = QPushButton("✅ 使用此密码")
        use_btn.setObjectName("primaryButton")
        use_btn.clicked.connect(self.accept)
        layout.addWidget(use_btn)
        
        # 初始生成
        self.generate()
    
    def generate(self):
        password = PasswordGenerator.generate(
            length=self.length_spin.value(),
            use_uppercase=self.uppercase_check.isChecked(),
            use_lowercase=self.lowercase_check.isChecked(),
            use_digits=self.digits_check.isChecked(),
            use_symbols=self.symbols_check.isChecked()
        )
        self.password_display.setText(password)
        self.generated_password = password
        
        # 更新强度显示
        result = PasswordGenerator.calculate_strength(password)
        self.strength_bar.setValue(result['score'])
        self.strength_label.setText(f"强度: {result['level']}")
        self.strength_label.setStyleSheet(f"color: {result['color']}; font-size: 14px; font-weight: bold; background: transparent;")
        
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                text-align: center;
                height: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {result['color']};
                border-radius: 6px;
            }}
        """)
    
    def copy_password(self):
        if self.generated_password:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_password)
            QMessageBox.information(self, "成功", "密码已复制到剪贴板")
    
    def get_password(self) -> Optional[str]:
        return self.generated_password


# ============================================================================
# 主窗口
# ============================================================================

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, user_id: int, username: str, crypto: CryptoManager, db: DatabaseManager):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.crypto = crypto
        self.db = db
        self.current_category = "全部"
        self.clipboard_timer = None
        self.inactivity_timer = None
        self.last_activity = time.time()
        self.locked = False
        
        self.setup_ui()
        self.load_entries()
        self.setup_inactivity_timer()
    
    def setup_ui(self):
        self.setWindowTitle("🔐 安全密码管理器")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(AppStyles.MAIN_STYLE)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 侧边栏
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border-right: 2px solid #2a2a4a;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # Logo
        logo_label = QLabel("🔐 密码管理器")
        logo_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #667eea; padding: 10px; background: transparent;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        
        # 用户信息
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_label = QLabel(f"👤 {self.username}")
        user_label.setStyleSheet("color: #ffffff; font-size: 14px; background: transparent;")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_label)
        sidebar_layout.addWidget(user_frame)
        
        sidebar_layout.addSpacing(10)
        
        # 搜索框
        search_label = QLabel("🔍 搜索")
        search_label.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        sidebar_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索密码...")
        self.search_input.textChanged.connect(self.search_entries)
        sidebar_layout.addWidget(self.search_input)
        
        sidebar_layout.addSpacing(10)
        
        # 分类列表
        categories_label = QLabel("📂 分类")
        categories_label.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        sidebar_layout.addWidget(categories_label)
        
        # 全部分类按钮
        all_btn = QPushButton("📁 全部")
        all_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                border: none;
                border-radius: 8px;
                padding: 10px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7b8ef8;
            }
        """)
        all_btn.clicked.connect(lambda: self.change_category("全部"))
        sidebar_layout.addWidget(all_btn)
        
        # 分类按钮
        self.category_buttons = {}
        categories = self.db.get_categories(self.user_id)
        for cat in categories:
            btn = QPushButton(f"{cat['icon']} {cat['name']}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                    text-align: left;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2a2a4a;
                }
            """)
            btn.clicked.connect(lambda checked, name=cat['name']: self.change_category(name))
            sidebar_layout.addWidget(btn)
            self.category_buttons[cat['name']] = btn
        
        sidebar_layout.addStretch()
        
        # 底部按钮
        lock_btn = QPushButton("🔒 锁定")
        lock_btn.clicked.connect(self.lock_application)
        sidebar_layout.addWidget(lock_btn)
        
        main_layout.addWidget(sidebar)
        
        # 主内容区
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 当前分类标题
        self.category_title = QLabel("📁 全部密码")
        self.category_title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        self.category_title.setStyleSheet("color: #ffffff; background: transparent;")
        toolbar.addWidget(self.category_title)
        
        toolbar.addStretch()
        
        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #888888; background: transparent;")
        toolbar.addWidget(self.stats_label)
        
        toolbar.addSpacing(10)
        
        # 添加按钮
        add_btn = QPushButton("➕ 添加密码")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_entry)
        toolbar.addWidget(add_btn)
        
        # 密码生成器按钮
        gen_btn = QPushButton("🎲 生成器")
        gen_btn.clicked.connect(self.show_generator)
        toolbar.addWidget(gen_btn)
        
        # 导入导出按钮
        import_btn = QPushButton("📥 导入")
        import_btn.clicked.connect(self.import_csv)
        toolbar.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.clicked.connect(self.export_csv)
        toolbar.addWidget(export_btn)
        
        content_layout.addLayout(toolbar)
        
        # 密码表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["名称", "用户名", "密码", "分类", "更新时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 200)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #111122;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                gridline-color: #2a2a4a;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1a1a2e;
            }
            QTableWidget::item:selected {
                background-color: rgba(102, 126, 234, 0.3);
            }
        """)
        content_layout.addWidget(self.table)
        
        main_layout.addWidget(content)
        
        # 状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #111122;
                color: #888888;
                border-top: 1px solid #2a2a4a;
                padding: 5px;
            }
        """)
        self.statusBar().showMessage("就绪")
    
    def setup_inactivity_timer(self):
        """设置不活动计时器"""
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(1000)  # 每秒检查一次
    
    def check_inactivity(self):
        """检查是否需要自动锁定"""
        if time.time() - self.last_activity > 300:  # 5分钟不活动
            self.lock_application()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.last_activity = time.time()
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        self.last_activity = time.time()
        super().keyPressEvent(event)
    
    def lock_application(self):
        """锁定应用程序"""
        self.locked = True
        self.hide()
        
        # 显示登录对话框
        dialog = LoginDialog(self, is_first_time=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_password()
            if password and self.crypto.verify_password(password, self.db.get_user(self.username)['password_hash']):
                self.locked = False
                self.last_activity = time.time()
                self.show()
            else:
                QMessageBox.warning(self, "错误", "密码错误")
                self.lock_application()
        else:
            # 用户取消，退出应用
            QApplication.quit()
    
    def change_category(self, category: str):
        """切换分类"""
        self.current_category = category
        
        # 更新按钮样式
        all_btn = self.findChild(QPushButton, "全部")
        
        # 更新标题
        category_icons = {
            "全部": "📁",
            "邮箱": "📧",
            "社交": "💬",
            "银行": "🏦",
            "购物": "🛒",
            "工作": "💼",
            "游戏": "🎮",
            "其他": "📁"
        }
        icon = category_icons.get(category, "📁")
        self.category_title.setText(f"{icon} {category}密码")
        
        self.load_entries()
    
    def load_entries(self, search_query: str = ""):
        """加载密码条目"""
        if search_query:
            entries = self.db.search_entries(self.user_id, search_query)
        elif self.current_category == "全部":
            entries = self.db.get_entries(self.user_id)
        else:
            entries = self.db.get_entries(self.user_id, self.current_category)
        
        # 解密并过滤
        decrypted_entries = []
        for entry in entries:
            try:
                decrypted = {
                    'id': entry['id'],
                    'title': self.crypto.decrypt(entry['title_encrypted']),
                    'username': self.crypto.decrypt(entry['username_encrypted']) if entry['username_encrypted'] else '',
                    'password': self.crypto.decrypt(entry['password_encrypted']),
                    'url': self.crypto.decrypt(entry['url_encrypted']) if entry['url_encrypted'] else '',
                    'notes': self.crypto.decrypt(entry['notes_encrypted']) if entry['notes_encrypted'] else '',
                    'category': entry['category'],
                    'favorite': entry['favorite'],
                    'updated_at': entry['updated_at']
                }
                
                # 搜索过滤
                if search_query:
                    query_lower = search_query.lower()
                    if (query_lower not in decrypted['title'].lower() and
                        query_lower not in decrypted['username'].lower() and
                        query_lower not in decrypted['url'].lower()):
                        continue
                
                decrypted_entries.append(decrypted)
            except Exception:
                continue
        
        # 更新表格
        self.table.setRowCount(len(decrypted_entries))
        
        for row, entry in enumerate(decrypted_entries):
            # 名称
            title_item = QTableWidgetItem(entry['title'])
            title_item.setData(Qt.ItemDataRole.UserRole, entry['id'])
            self.table.setItem(row, 0, title_item)
            
            # 用户名
            self.table.setItem(row, 1, QTableWidgetItem(entry['username']))
            
            # 密码（隐藏）
            password_item = QTableWidgetItem("••••••••")
            password_item.setData(Qt.ItemDataRole.UserRole, entry['password'])
            self.table.setItem(row, 2, password_item)
            
            # 分类
            self.table.setItem(row, 3, QTableWidgetItem(entry['category']))
            
            # 更新时间
            self.table.setItem(row, 4, QTableWidgetItem(str(entry['updated_at'])))
            
            # 操作按钮
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)
            
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(30, 30)
            copy_btn.setToolTip("复制密码")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #667eea;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #7b8ef8;
                }
            """)
            copy_btn.clicked.connect(lambda checked, pw=entry['password']: self.copy_to_clipboard(pw))
            actions_layout.addWidget(copy_btn)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setToolTip("编辑")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a4a;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #3a3a5a;
                }
            """)
            edit_btn.clicked.connect(lambda checked, eid=entry['id']: self.edit_entry(eid))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setToolTip("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #ff4757;
                }
            """)
            delete_btn.clicked.connect(lambda checked, eid=entry['id']: self.delete_entry(eid))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 5, actions_widget)
        
        # 更新统计
        self.stats_label.setText(f"共 {len(decrypted_entries)} 条记录")
    
    def search_entries(self, query: str):
        """搜索条目"""
        self.load_entries(query)
    
    def add_entry(self):
        """添加新条目"""
        categories = self.db.get_categories(self.user_id)
        dialog = EntryDialog(self, categories=categories, crypto=self.crypto)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            # 加密数据
            encrypted_entry = {
                'title': self.crypto.encrypt(data['title']),
                'username': self.crypto.encrypt(data['username']) if data['username'] else '',
                'password': self.crypto.encrypt(data['password']),
                'url': self.crypto.encrypt(data['url']) if data['url'] else '',
                'notes': self.crypto.encrypt(data['notes']) if data['notes'] else '',
                'category': data['category']
            }
            
            if self.db.add_entry(self.user_id, encrypted_entry):
                self.load_entries()
                self.statusBar().showMessage("✅ 密码已添加", 3000)
            else:
                QMessageBox.warning(self, "错误", "添加失败")
    
    def edit_entry(self, entry_id: int):
        """编辑条目"""
        entries = self.db.get_entries(self.user_id)
        entry = next((e for e in entries if e['id'] == entry_id), None)
        
        if not entry:
            return
        
        categories = self.db.get_categories(self.user_id)
        dialog = EntryDialog(self, entry=entry, categories=categories, crypto=self.crypto)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            # 加密数据
            encrypted_entry = {
                'title': self.crypto.encrypt(data['title']),
                'username': self.crypto.encrypt(data['username']) if data['username'] else '',
                'password': self.crypto.encrypt(data['password']),
                'url': self.crypto.encrypt(data['url']) if data['url'] else '',
                'notes': self.crypto.encrypt(data['notes']) if data['notes'] else '',
                'category': data['category']
            }
            
            if self.db.update_entry(entry_id, encrypted_entry):
                self.load_entries()
                self.statusBar().showMessage("✅ 密码已更新", 3000)
            else:
                QMessageBox.warning(self, "错误", "更新失败")
    
    def delete_entry(self, entry_id: int):
        """删除条目"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条密码吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_entry(entry_id):
                self.load_entries()
                self.statusBar().showMessage("✅ 密码已删除", 3000)
            else:
                QMessageBox.warning(self, "错误", "删除失败")
    
    def copy_to_clipboard(self, text: str):
        """复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.statusBar().showMessage("✅ 已复制到剪贴板，30秒后自动清除", 3000)
        
        # 启动清除计时器
        if self.clipboard_timer:
            self.clipboard_timer.stop()
        
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.setSingleShot(True)
        self.clipboard_timer.timeout.connect(self.clear_clipboard)
        self.clipboard_timer.start(30000)  # 30秒
    
    def clear_clipboard(self):
        """清除剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.clear()
        self.statusBar().showMessage("🔒 剪贴板已清除", 3000)
    
    def show_generator(self):
        """显示密码生成器"""
        dialog = PasswordGeneratorDialog(self)
        dialog.exec()
    
    def import_csv(self):
        """导入CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入CSV文件", "", "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            imported_count = 0
            categories = self.db.get_categories(self.user_id)
            category_names = [c['name'] for c in categories]
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get('名称', row.get('name', row.get('title', '')))
                    username = row.get('用户名', row.get('username', ''))
                    password = row.get('密码', row.get('password', ''))
                    url = row.get('网址', row.get('url', ''))
                    notes = row.get('备注', row.get('notes', ''))
                    category = row.get('分类', row.get('category', '其他'))
                    
                    if not title or not password:
                        continue
                    
                    # 加密数据
                    encrypted_entry = {
                        'title': self.crypto.encrypt(title),
                        'username': self.crypto.encrypt(username) if username else '',
                        'password': self.crypto.encrypt(password),
                        'url': self.crypto.encrypt(url) if url else '',
                        'notes': self.crypto.encrypt(notes) if notes else '',
                        'category': category if category in category_names else '其他'
                    }
                    
                    if self.db.add_entry(self.user_id, encrypted_entry):
                        imported_count += 1
            
            self.load_entries()
            QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条密码")
        
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"导入失败: {str(e)}")
    
    def export_csv(self):
        """导出CSV文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV文件", "passwords.csv", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            entries = self.db.get_entries(self.user_id)
            
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['名称', '用户名', '密码', '网址', '备注', '分类'])
                
                for entry in entries:
                    try:
                        title = self.crypto.decrypt(entry['title_encrypted'])
                        username = self.crypto.decrypt(entry['username_encrypted']) if entry['username_encrypted'] else ''
                        password = self.crypto.decrypt(entry['password_encrypted'])
                        url = self.crypto.decrypt(entry['url_encrypted']) if entry['url_encrypted'] else ''
                        notes = self.crypto.decrypt(entry['notes_encrypted']) if entry['notes_encrypted'] else ''
                        category = entry['category']
                        
                        writer.writerow([title, username, password, url, notes, category])
                    except Exception:
                        continue
            
            QMessageBox.information(self, "导出成功", f"已导出到:\n{file_path}")
        
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出失败: {str(e)}")


# ============================================================================
# 应用程序入口
# ============================================================================

class PasswordManagerApp:
    """密码管理器应用程序"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        self.app.setStyleSheet(AppStyles.MAIN_STYLE)
        
        # 数据目录
        self.data_dir = Path.home() / ".password_manager"
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.crypto = CryptoManager()
        self.db = DatabaseManager(str(self.data_dir / "passwords.db"))
        self.main_window = None
    
    def run(self) -> int:
        """运行应用程序"""
        # 检查是否首次使用
        user = self.db.get_user("admin")
        
        if not user:
            # 首次使用，设置主密码
            dialog = LoginDialog(is_first_time=True)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return 0
            
            password = dialog.get_password()
            if not password:
                return 0
            
            # 创建用户
            password_hash = self.crypto.hash_password(password)
            salt = secrets.token_bytes(16)
            salt_b64 = base64.b64encode(salt).decode('utf-8')
            
            if not self.db.create_user("admin", password_hash, salt_b64):
                QMessageBox.critical(None, "错误", "创建用户失败")
                return 0
            
            # 设置加密密钥
            self.crypto.set_master_password(password, salt)
        else:
            # 登录
            dialog = LoginDialog(is_first_time=False)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return 0
            
            password = dialog.get_password()
            if not password:
                return 0
            
            # 验证密码
            if not self.crypto.verify_password(password, user['password_hash']):
                QMessageBox.critical(None, "错误", "密码错误")
                return 0
            
            # 设置加密密钥
            salt = base64.b64decode(user['salt'].encode('utf-8'))
            self.crypto.set_master_password(password, salt)
        
        # 显示主窗口
        self.main_window = MainWindow(
            user_id=user['id'] if user else 1,
            username="admin",
            crypto=self.crypto,
            db=self.db
        )
        self.main_window.show()
        
        return self.app.exec()


def main():
    """主函数"""
    app = PasswordManagerApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
