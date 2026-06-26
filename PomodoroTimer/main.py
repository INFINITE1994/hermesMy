#!/usr/bin/env python3
"""
PomodoroTimer - 番茄钟计时器
专业专注时间管理工具
"""

import sys
import os
import json
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSystemTrayIcon, QMenu,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QListWidget,
    QListWidgetItem, QLineEdit, QFrame, QGridLayout, QScrollArea,
    QMessageBox, QTabWidget, QGroupBox, QStyle, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QSize, QPoint, QPropertyAnimation,
    QEasingCurve, pyqtSignal, QThread, QSettings
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QAction, QCloseEvent
)
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl


# ============================================================================
# 配置常量
# ============================================================================

APP_NAME = "番茄钟计时器"
APP_VERSION = "1.0.0"
APP_AUTHOR = "PomodoroTimer Developer"

# 默认时间 (秒)
DEFAULT_WORK_TIME = 25 * 60  # 25分钟
DEFAULT_SHORT_BREAK = 5 * 60  # 5分钟
DEFAULT_LONG_BREAK = 15 * 60  # 15分钟
POMODOROS_BEFORE_LONG_BREAK = 4

# 颜色方案
COLORS = {
    "background": "#0a0a0a",
    "card": "#111122",
    "card_hover": "#1a1a33",
    "accent_start": "#667eea",
    "accent_end": "#764ba2",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "text_muted": "#606070",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#f87171",
    "border": "#2a2a3a",
}

# 分心网站列表
DISTRACTING_WEBSITES = [
    "www.weibo.com", "weibo.com",
    "www.douyin.com", "douyin.com",
    "www.bilibili.com", "bilibili.com",
    "www.zhihu.com", "zhihu.com",
    "www.taobao.com", "taobao.com",
    "www.jd.com", "jd.com",
    "www.douban.com", "douban.com",
    "www.tiktok.com", "tiktok.com",
    "www.facebook.com", "facebook.com",
    "www.twitter.com", "twitter.com",
    "www.instagram.com", "instagram.com",
    "www.youtube.com", "youtube.com",
    "www.reddit.com", "reddit.com",
]


# ============================================================================
# 数据库管理
# ============================================================================

class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str = "pomodoro.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 创建会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                task_id INTEGER,
                completed BOOLEAN DEFAULT 0
            )
        ''')

        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT 0,
                pomodoros_completed INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()

    def add_session(self, duration: int, session_type: str, task_id: Optional[int] = None) -> int:
        """添加新的计时会话"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (start_time, duration, session_type, task_id) VALUES (?, ?, ?, ?)",
            (datetime.now(), duration, session_type, task_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def complete_session(self, session_id: int):
        """完成会话"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET end_time = ?, completed = 1 WHERE id = ?",
            (datetime.now(), session_id)
        )
        self.conn.commit()

    def get_sessions(self, days: int = 30) -> List[Dict]:
        """获取指定天数内的会话"""
        cursor = self.conn.cursor()
        since = datetime.now() - timedelta(days=days)
        cursor.execute(
            "SELECT * FROM sessions WHERE start_time >= ? AND completed = 1 ORDER BY start_time DESC",
            (since,)
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_today_sessions(self) -> List[Dict]:
        """获取今天的会话"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE start_time >= ? AND completed = 1 ORDER BY start_time DESC",
            (today,)
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_task(self, title: str, description: str = "") -> int:
        """添加新任务"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (title, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_tasks(self, completed: bool = False) -> List[Dict]:
        """获取任务列表"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC",
            (completed,)
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def complete_task(self, task_id: int):
        """完成任务"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()

    def increment_task_pomodoros(self, task_id: int):
        """增加任务的番茄数"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tasks SET pomodoros_completed = pomodoros_completed + 1 WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()

    def get_statistics(self) -> Dict:
        """获取统计数据"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        cursor = self.conn.cursor()

        # 今日统计
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE start_time >= ? AND completed = 1 AND session_type = 'work'",
            (today,)
        )
        today_count = cursor.fetchone()[0]

        # 本周统计
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE start_time >= ? AND completed = 1 AND session_type = 'work'",
            (week_ago,)
        )
        week_count = cursor.fetchone()[0]

        # 本月统计
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE start_time >= ? AND completed = 1 AND session_type = 'work'",
            (month_ago,)
        )
        month_count = cursor.fetchone()[0]

        # 总计
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE completed = 1 AND session_type = 'work'"
        )
        total_count = cursor.fetchone()[0]

        # 今日专注时间 (分钟)
        cursor.execute(
            "SELECT SUM(duration) FROM sessions WHERE start_time >= ? AND completed = 1 AND session_type = 'work'",
            (today,)
        )
        today_minutes = (cursor.fetchone()[0] or 0) // 60

        return {
            "today": today_count,
            "week": week_count,
            "month": month_count,
            "total": total_count,
            "today_minutes": today_minutes
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# ============================================================================
# 声音播放器
# ============================================================================

class SoundPlayer:
    """声音播放器"""

    def __init__(self):
        self.enabled = True
        self.sound_effect = None
        self._init_sound()

    def _init_sound(self):
        """初始化声音系统"""
        try:
            self.sound_effect = QSoundEffect()
            self._create_default_sound()
        except Exception as e:
            print(f"声音系统初始化失败: {e}")
            self.sound_effect = None

    def _create_default_sound(self):
        """创建默认提示音文件"""
        sound_dir = Path("sounds")
        sound_dir.mkdir(exist_ok=True)

        self.sound_file = sound_dir / "notification.wav"
        if not self.sound_file.exists():
            self._generate_wav(self.sound_file)

        self.sound_effect.setSource(QUrl.fromLocalFile(str(self.sound_file.absolute())))
        self.sound_effect.setVolume(0.5)

    def _generate_wav(self, filepath: Path):
        """生成简单的 WAV 提示音"""
        import struct
        import math

        sample_rate = 44100
        duration = 0.5
        frequency = 880

        num_samples = int(sample_rate * duration)
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            # 创建柔和的提示音
            envelope = 1.0 - (t / duration)
            value = int(32767 * envelope * math.sin(2 * math.pi * frequency * t) * 0.5)
            samples.append(struct.pack('<h', value))

        # 写入 WAV 文件
        with open(filepath, 'wb') as f:
            # RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + num_samples * 2))
            f.write(b'WAVE')
            # fmt chunk
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))  # PCM
            f.write(struct.pack('<H', 1))  # mono
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            # data chunk
            f.write(b'data')
            f.write(struct.pack('<I', num_samples * 2))
            f.write(b''.join(samples))

    def play(self):
        """播放提示音"""
        if self.enabled and self.sound_effect:
            try:
                self.sound_effect.play()
            except Exception as e:
                print(f"播放声音失败: {e}")


# ============================================================================
# 专注模式管理器
# ============================================================================

class FocusModeManager:
    """专注模式管理器 - 通过 hosts 文件阻止分心网站"""

    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    MARKER_START = "# PomodoroTimer Focus Mode Start"
    MARKER_END = "# PomodoroTimer Focus Mode End"

    def __init__(self):
        self.is_active = False

    def enable(self) -> bool:
        """启用专注模式"""
        try:
            self._modify_hosts(True)
            self.is_active = True
            return True
        except Exception as e:
            print(f"启用专注模式失败: {e}")
            return False

    def disable(self) -> bool:
        """禁用专注模式"""
        try:
            self._modify_hosts(False)
            self.is_active = False
            return True
        except Exception as e:
            print(f"禁用专注模式失败: {e}")
            return False

    def _modify_hosts(self, block: bool):
        """修改 hosts 文件"""
        try:
            with open(self.HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 移除旧的阻止规则
            start_idx = content.find(self.MARKER_START)
            end_idx = content.find(self.MARKER_END)
            if start_idx != -1 and end_idx != -1:
                content = content[:start_idx] + content[end_idx + len(self.MARKER_END):]

            # 添加新的阻止规则
            if block:
                entries = [self.MARKER_START]
                for site in DISTRACTING_WEBSITES:
                    entries.append(f"127.0.0.1 {site}")
                entries.append(self.MARKER_END)
                content = content.rstrip() + "\n" + "\n".join(entries) + "\n"

            with open(self.HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content)

            # 刷新 DNS 缓存
            os.system('ipconfig /flushdns > nul 2>&1')

        except PermissionError:
            raise Exception("需要管理员权限来修改 hosts 文件")


# ============================================================================
# 自定义样式
# ============================================================================

def get_stylesheet() -> str:
    """获取应用样式表"""
    return f"""
    /* 全局样式 */
    QMainWindow, QDialog {{
        background-color: {COLORS['background']};
    }}

    QWidget {{
        color: {COLORS['text_primary']};
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    }}

    /* 标签 */
    QLabel {{
        color: {COLORS['text_primary']};
    }}

    QLabel#titleLabel {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS['text_primary']};
    }}

    QLabel#timeLabel {{
        font-size: 72px;
        font-weight: bold;
        font-family: "Consolas", "Courier New", monospace;
        color: {COLORS['text_primary']};
    }}

    QLabel#statusLabel {{
        font-size: 16px;
        color: {COLORS['text_secondary']};
    }}

    QLabel#statNumber {{
        font-size: 36px;
        font-weight: bold;
        color: {COLORS['accent_start']};
    }}

    QLabel#statLabel {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
    }}

    /* 按钮 */
    QPushButton {{
        background-color: {COLORS['card']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: bold;
        min-width: 100px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['card_hover']};
        border-color: {COLORS['accent_start']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['accent_start']};
    }}

    QPushButton#primaryButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
        border: none;
        color: white;
        font-size: 16px;
        padding: 14px 32px;
    }}

    QPushButton#primaryButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_start']}dd, stop:1 {COLORS['accent_end']}dd);
    }}

    QPushButton#dangerButton {{
        background-color: {COLORS['danger']}33;
        border-color: {COLORS['danger']};
        color: {COLORS['danger']};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {COLORS['danger']}55;
    }}

    /* 输入框 */
    QLineEdit, QSpinBox {{
        background-color: {COLORS['card']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
    }}

    QLineEdit:focus, QSpinBox:focus {{
        border-color: {COLORS['accent_start']};
    }}

    /* 列表 */
    QListWidget {{
        background-color: {COLORS['card']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 4px;
    }}

    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}

    QListWidget::item:selected {{
        background-color: {COLORS['accent_start']}33;
    }}

    QListWidget::item:hover {{
        background-color: {COLORS['card_hover']};
    }}

    /* 框架 */
    QFrame#card {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 16px;
    }}

    /* 标签页 */
    QTabWidget::pane {{
        background-color: {COLORS['background']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
    }}

    QTabBar::tab {{
        background-color: {COLORS['card']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 20px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        border-bottom: 2px solid {COLORS['accent_start']};
    }}

    /* 复选框 */
    QCheckBox {{
        color: {COLORS['text_primary']};
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['card']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_start']};
        border-color: {COLORS['accent_start']};
    }}

    /* 分组框 */
    QGroupBox {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 24px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {COLORS['text_secondary']};
    }}

    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 8px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 4px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_start']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* 菜单 */
    QMenu {{
        background-color: {COLORS['card']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent_start']}33;
    }}
    """


# ============================================================================
# 计时器线程
# ============================================================================

class TimerThread(QThread):
    """计时器后台线程"""
    tick = pyqtSignal(int)  # 剩余秒数
    finished = pyqtSignal()

    def __init__(self, duration: int):
        super().__init__()
        self.duration = duration
        self.remaining = duration
        self._is_running = False
        self._is_paused = False

    def run(self):
        self._is_running = True
        self._is_paused = False

        while self._is_running and self.remaining > 0:
            if not self._is_paused:
                self.tick.emit(self.remaining)
                self.remaining -= 1
                time.sleep(1)
            else:
                time.sleep(0.1)

        if self._is_running and self.remaining <= 0:
            self.finished.emit()

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def stop(self):
        self._is_running = False
        self.wait()

    def reset(self, duration: int):
        self.duration = duration
        self.remaining = duration


# ============================================================================
# 主窗口
# ============================================================================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 初始化组件
        self.db = DatabaseManager()
        self.sound_player = SoundPlayer()
        self.focus_manager = FocusModeManager()

        # 计时器状态
        self.timer_thread: Optional[TimerThread] = None
        self.current_session_id: Optional[int] = None
        self.current_task_id: Optional[int] = None
        self.pomodoro_count = 0
        self.is_work_session = True
        self.is_running = False
        self.is_paused = False

        # 设置
        self.settings = QSettings("PomodoroTimer", "Settings")
        self.work_duration = self.settings.value("work_duration", DEFAULT_WORK_TIME, type=int)
        self.short_break_duration = self.settings.value("short_break", DEFAULT_SHORT_BREAK, type=int)
        self.long_break_duration = self.settings.value("long_break", DEFAULT_LONG_BREAK, type=int)
        self.auto_start_breaks = self.settings.value("auto_start_breaks", False, type=bool)
        self.focus_mode_enabled = self.settings.value("focus_mode", False, type=bool)
        self.sound_enabled = self.settings.value("sound_enabled", True, type=bool)

        self.sound_player.enabled = self.sound_enabled

        # 初始化UI
        self.init_ui()
        self.init_system_tray()
        self.update_statistics()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)

        # 应用样式
        self.setStyleSheet(get_stylesheet())

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 左侧面板 - 计时器
        left_panel = self.create_timer_panel()
        main_layout.addWidget(left_panel, stretch=2)

        # 右侧面板 - 标签页 (任务/统计/设置)
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)

    def create_timer_panel(self) -> QWidget:
        """创建计时器面板"""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)

        # 标题
        title_label = QLabel("🍅 番茄钟")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 会话状态
        self.status_label = QLabel("准备开始工作")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 计时器显示
        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        # 进度提示
        self.progress_label = QLabel("第 1 个番茄 · 休息后继续")
        self.progress_label.setObjectName("statusLabel")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.start_button = QPushButton("开始专注")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.toggle_timer)
        button_layout.addWidget(self.start_button)

        self.skip_button = QPushButton("跳过")
        self.skip_button.clicked.connect(self.skip_session)
        button_layout.addWidget(self.skip_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout)

        # 番茄计数
        count_layout = QHBoxLayout()
        count_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pomodoro_dots = []
        for i in range(4):
            dot = QLabel("○")
            dot.setFont(QFont("Segoe UI", 20))
            dot.setStyleSheet(f"color: {COLORS['text_muted']};")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_layout.addWidget(dot)
            self.pomodoro_dots.append(dot)

        layout.addLayout(count_layout)

        # 专注模式开关
        focus_layout = QHBoxLayout()
        focus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.focus_checkbox = QCheckBox("启用专注模式 (阻止分心网站)")
        self.focus_checkbox.setChecked(self.focus_mode_enabled)
        self.focus_checkbox.stateChanged.connect(self.toggle_focus_mode)
        focus_layout.addWidget(self.focus_checkbox)

        layout.addLayout(focus_layout)

        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tab_widget = QTabWidget()

        # 任务标签页
        task_tab = self.create_task_tab()
        self.tab_widget.addTab(task_tab, "任务")

        # 统计标签页
        stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(stats_tab, "统计")

        # 设置标签页
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "设置")

        layout.addWidget(self.tab_widget)

        return panel

    def create_task_tab(self) -> QWidget:
        """创建任务标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 添加任务
        add_layout = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入新任务...")
        self.task_input.returnPressed.connect(self.add_task)
        add_layout.addWidget(self.task_input)

        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_task)
        add_layout.addWidget(add_button)

        layout.addLayout(add_layout)

        # 任务列表
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.select_task)
        layout.addWidget(self.task_list)

        # 任务操作按钮
        task_buttons = QHBoxLayout()

        complete_button = QPushButton("完成任务")
        complete_button.setObjectName("primaryButton")
        complete_button.clicked.connect(self.complete_task)
        task_buttons.addWidget(complete_button)

        delete_button = QPushButton("删除")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_task)
        task_buttons.addWidget(delete_button)

        layout.addLayout(task_buttons)

        # 加载任务
        self.load_tasks()

        return widget

    def create_stats_tab(self) -> QWidget:
        """创建统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # 统计卡片网格
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

        # 今日番茄
        self.today_stat_label = QLabel("0")
        today_card = self.create_stat_card("今日番茄", self.today_stat_label, COLORS['accent_start'])
        stats_grid.addWidget(today_card, 0, 0)

        # 今日专注
        self.focus_stat_label = QLabel("0")
        focus_card = self.create_stat_card("今日专注(分钟)", self.focus_stat_label, COLORS['accent_end'])
        stats_grid.addWidget(focus_card, 0, 1)

        # 本周番茄
        self.week_stat_label = QLabel("0")
        week_card = self.create_stat_card("本周番茄", self.week_stat_label, COLORS['success'])
        stats_grid.addWidget(week_card, 1, 0)

        # 本月番茄
        self.month_stat_label = QLabel("0")
        month_card = self.create_stat_card("本月番茄", self.month_stat_label, COLORS['warning'])
        stats_grid.addWidget(month_card, 1, 1)

        layout.addLayout(stats_grid)

        # 总计
        total_frame = QFrame()
        total_frame.setObjectName("card")
        total_layout = QVBoxLayout(total_frame)

        total_label = QLabel("累计完成")
        total_label.setObjectName("statLabel")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(total_label)

        self.total_count_label = QLabel("0")
        self.total_count_label.setObjectName("statNumber")
        self.total_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(self.total_count_label)

        total_unit = QLabel("个番茄钟")
        total_unit.setObjectName("statLabel")
        total_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(total_unit)

        layout.addWidget(total_frame)

        layout.addStretch()

        # 保存引用以便更新
        self.stat_labels = {
            "today": self.today_stat_label,
            "focus": self.focus_stat_label,
            "week": self.week_stat_label,
            "month": self.month_stat_label,
        }

        return widget

    def create_stat_card(self, title: str, value_label: QLabel, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        value_label.setObjectName("statNumber")
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setObjectName("statLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return card

    def create_settings_tab(self) -> QWidget:
        """创建设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # 时间设置组
        time_group = QGroupBox("时间设置")
        time_layout = QFormLayout(time_group)

        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 60)
        self.work_spin.setValue(self.work_duration // 60)
        self.work_spin.setSuffix(" 分钟")
        time_layout.addRow("工作时长:", self.work_spin)

        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 30)
        self.short_break_spin.setValue(self.short_break_duration // 60)
        self.short_break_spin.setSuffix(" 分钟")
        time_layout.addRow("短休息:", self.short_break_spin)

        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(5, 60)
        self.long_break_spin.setValue(self.long_break_duration // 60)
        self.long_break_spin.setSuffix(" 分钟")
        time_layout.addRow("长休息:", self.long_break_spin)

        layout.addWidget(time_group)

        # 选项设置组
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)

        self.auto_break_checkbox = QCheckBox("自动开始休息")
        self.auto_break_checkbox.setChecked(self.auto_start_breaks)
        options_layout.addWidget(self.auto_break_checkbox)

        self.sound_checkbox = QCheckBox("启用声音提醒")
        self.sound_checkbox.setChecked(self.sound_enabled)
        self.sound_checkbox.stateChanged.connect(self.toggle_sound)
        options_layout.addWidget(self.sound_checkbox)

        layout.addWidget(options_group)

        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        layout.addStretch()

        return widget

    def init_system_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 创建简单的图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(COLORS['accent_start']))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("white"), 2))
        painter.setFont(QFont("Segoe UI", 16))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🍅")
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

        # 托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        """显示主窗口"""
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "应用已最小化到系统托盘",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_application(self):
        """退出应用"""
        # 停止计时器
        if self.timer_thread and self.timer_thread.isRunning():
            self.timer_thread.stop()

        # 禁用专注模式
        if self.focus_manager.is_active:
            self.focus_manager.disable()

        # 关闭数据库
        self.db.close()

        # 隐藏托盘图标
        self.tray_icon.hide()

        QApplication.quit()

    # ========================================================================
    # 计时器控制
    # ========================================================================

    def toggle_timer(self):
        """切换计时器状态"""
        if not self.is_running:
            self.start_timer()
        elif self.is_paused:
            self.resume_timer()
        else:
            self.pause_timer()

    def start_timer(self):
        """开始计时"""
        # 确定时长
        if self.is_work_session:
            duration = self.work_duration
            session_type = "work"
        else:
            if self.pomodoro_count % POMODOROS_BEFORE_LONG_BREAK == 0 and self.pomodoro_count > 0:
                duration = self.long_break_duration
            else:
                duration = self.short_break_duration
            session_type = "break"

        # 记录会话
        self.current_session_id = self.db.add_session(duration, session_type, self.current_task_id)

        # 启动计时器线程
        self.timer_thread = TimerThread(duration)
        self.timer_thread.tick.connect(self.update_display)
        self.timer_thread.finished.connect(self.timer_finished)
        self.timer_thread.start()

        # 更新UI
        self.is_running = True
        self.is_paused = False
        self.start_button.setText("暂停")

        if self.is_work_session:
            self.status_label.setText("专注中...")
            # 启用专注模式
            if self.focus_mode_enabled:
                self.focus_manager.enable()
        else:
            self.status_label.setText("休息中...")

    def pause_timer(self):
        """暂停计时"""
        if self.timer_thread:
            self.timer_thread.pause()
            self.is_paused = True
            self.start_button.setText("继续")
            self.status_label.setText("已暂停")

    def resume_timer(self):
        """继续计时"""
        if self.timer_thread:
            self.timer_thread.resume()
            self.is_paused = False
            self.start_button.setText("暂停")
            if self.is_work_session:
                self.status_label.setText("专注中...")
            else:
                self.status_label.setText("休息中...")

    def skip_session(self):
        """跳过当前会话"""
        if self.timer_thread and self.timer_thread.isRunning():
            self.timer_thread.stop()

        self.timer_finished()

    def reset_timer(self):
        """重置计时器"""
        if self.timer_thread and self.timer_thread.isRunning():
            self.timer_thread.stop()

        self.is_running = False
        self.is_paused = False
        self.is_work_session = True

        # 禁用专注模式
        if self.focus_manager.is_active:
            self.focus_manager.disable()

        # 更新显示
        self.update_display(self.work_duration)
        self.start_button.setText("开始专注")
        self.status_label.setText("准备开始工作")
        self.progress_label.setText(f"第 {self.pomodoro_count + 1} 个番茄 · 休息后继续")

    def update_display(self, seconds: int):
        """更新计时器显示"""
        minutes = seconds // 60
        secs = seconds % 60
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def timer_finished(self):
        """计时器完成"""
        # 播放提示音
        self.sound_player.play()

        # 完成会话
        if self.current_session_id:
            self.db.complete_session(self.current_session_id)

        # 更新任务番茄数
        if self.current_task_id and self.is_work_session:
            self.db.increment_task_pomodoros(self.current_task_id)

        # 禁用专注模式
        if self.focus_manager.is_active:
            self.focus_manager.disable()

        if self.is_work_session:
            # 完成一个番茄
            self.pomodoro_count += 1
            self.update_pomodoro_dots()

            # 显示通知
            self.tray_icon.showMessage(
                APP_NAME,
                f"太棒了！已完成第 {self.pomodoro_count} 个番茄钟！",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

            # 切换到休息模式
            self.is_work_session = False

            if self.pomodoro_count % POMODOROS_BEFORE_LONG_BREAK == 0:
                self.status_label.setText("长休息时间！")
                self.progress_label.setText("完成4个番茄，好好休息一下吧！")
            else:
                self.status_label.setText("短休息时间")
                self.progress_label.setText(f"还剩 {POMODOROS_BEFORE_LONG_BREAK - (self.pomodoro_count % POMODOROS_BEFORE_LONG_BREAK)} 个番茄进入长休息")

            # 自动开始休息
            if self.auto_start_breaks:
                self.start_timer()
            else:
                self.is_running = False
                self.start_button.setText("开始休息")
        else:
            # 休息结束
            self.tray_icon.showMessage(
                APP_NAME,
                "休息结束，准备好继续专注了吗？",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

            # 切换到工作模式
            self.is_work_session = True
            self.is_running = False

            self.start_button.setText("开始专注")
            self.status_label.setText("准备开始工作")
            self.progress_label.setText(f"第 {self.pomodoro_count + 1} 个番茄 · 休息后继续")
            self.update_display(self.work_duration)

        # 更新统计
        self.update_statistics()

    def update_pomodoro_dots(self):
        """更新番茄计数点"""
        current_cycle = self.pomodoro_count % POMODOROS_BEFORE_LONG_BREAK
        for i in range(4):
            if i < current_cycle or (current_cycle == 0 and self.pomodoro_count > 0):
                self.pomodoro_dots[i].setText("●")
                self.pomodoro_dots[i].setStyleSheet(f"color: {COLORS['accent_start']};")
            else:
                self.pomodoro_dots[i].setText("○")
                self.pomodoro_dots[i].setStyleSheet(f"color: {COLORS['text_muted']};")

    # ========================================================================
    # 任务管理
    # ========================================================================

    def add_task(self):
        """添加任务"""
        title = self.task_input.text().strip()
        if not title:
            return

        self.db.add_task(title)
        self.task_input.clear()
        self.load_tasks()

    def load_tasks(self):
        """加载任务列表"""
        self.task_list.clear()
        tasks = self.db.get_tasks(completed=False)

        for task in tasks:
            item = QListWidgetItem(f"📌 {task['title']} ({task['pomodoros_completed']}🍅)")
            item.setData(Qt.ItemDataRole.UserRole, task['id'])
            self.task_list.addItem(item)

    def select_task(self, item: QListWidgetItem):
        """选择任务"""
        self.current_task_id = item.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"当前任务: {item.text()}")

    def complete_task(self):
        """完成任务"""
        current_item = self.task_list.currentItem()
        if current_item:
            task_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.db.complete_task(task_id)
            self.load_tasks()
            self.current_task_id = None

    def delete_task(self):
        """删除任务"""
        current_item = self.task_list.currentItem()
        if current_item:
            task_id = current_item.data(Qt.ItemDataRole.UserRole)
            # 这里简化处理，直接标记为完成
            self.db.complete_task(task_id)
            self.load_tasks()
            self.current_task_id = None

    # ========================================================================
    # 统计更新
    # ========================================================================

    def update_statistics(self):
        """更新统计数据"""
        stats = self.db.get_statistics()

        # 更新统计卡片
        if hasattr(self, 'stat_labels'):
            self.stat_labels["today"].setText(str(stats["today"]))
            self.stat_labels["focus"].setText(str(stats["today_minutes"]))
            self.stat_labels["week"].setText(str(stats["week"]))
            self.stat_labels["month"].setText(str(stats["month"]))

        # 更新总计
        if hasattr(self, 'total_count_label'):
            self.total_count_label.setText(str(stats["total"]))

    # ========================================================================
    # 设置
    # ========================================================================

    def save_settings(self):
        """保存设置"""
        self.work_duration = self.work_spin.value() * 60
        self.short_break_duration = self.short_break_spin.value() * 60
        self.long_break_duration = self.long_break_spin.value() * 60
        self.auto_start_breaks = self.auto_break_checkbox.isChecked()
        self.focus_mode_enabled = self.focus_checkbox.isChecked()

        # 保存到 QSettings
        self.settings.setValue("work_duration", self.work_duration)
        self.settings.setValue("short_break", self.short_break_duration)
        self.settings.setValue("long_break", self.long_break_duration)
        self.settings.setValue("auto_start_breaks", self.auto_start_breaks)
        self.settings.setValue("focus_mode", self.focus_mode_enabled)
        self.settings.setValue("sound_enabled", self.sound_enabled)

        # 更新显示
        if not self.is_running:
            self.update_display(self.work_duration)

        QMessageBox.information(self, "设置", "设置已保存！")

    def toggle_focus_mode(self, state):
        """切换专注模式"""
        self.focus_mode_enabled = self.focus_checkbox.isChecked()
        self.settings.setValue("focus_mode", self.focus_mode_enabled)

    def toggle_sound(self, state):
        """切换声音"""
        self.sound_enabled = self.sound_checkbox.isChecked()
        self.sound_player.enabled = self.sound_enabled
        self.settings.setValue("sound_enabled", self.sound_enabled)


# ============================================================================
# 应用入口
# ============================================================================

def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_AUTHOR)

    # 设置应用图标
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(COLORS['accent_start']))
    painter = QPainter(pixmap)
    painter.setPen(QPen(QColor("white"), 3))
    painter.setFont(QFont("Segoe UI", 32))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🍅")
    painter.end()
    app.setWindowIcon(QIcon(pixmap))

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
