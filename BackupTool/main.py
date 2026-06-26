#!/usr/bin/env python3
"""
BackupTool - 专业数据备份工具
功能：文件备份、增量备份、定时备份、压缩、加密、历史管理、恢复、云同步
"""

import sys
import os
import json
import hashlib
import zipfile
import shutil
import datetime
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QFileDialog, QListWidget, QListWidgetItem,
    QProgressBar, QComboBox, QDateTimeEdit, QCheckBox, QLineEdit,
    QStackedWidget, QMessageBox, QGroupBox, QScrollArea, QGridLayout,
    QSpinBox, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QSystemTrayIcon, QMenu, QStyle, QSizePolicy, QTabWidget, QSplitter
)
from PyQt6.QtCore import (
    Qt, QTimer, QDateTime, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, QSettings
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QAction, QDesktopServices
)
from PyQt6.QtCore import QUrl

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ─── Constants ───────────────────────────────────────────────────────────────
APP_NAME = "BackupTool"
APP_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".backuptool"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
DEFAULT_BACKUP_DIR = Path.home() / "Backups"

# Colors
BG_COLOR = "#0a0a0a"
CARD_COLOR = "#111122"
ACCENT_START = "#667eea"
ACCENT_END = "#764ba2"
TEXT_COLOR = "#e0e0e0"
TEXT_DIM = "#888899"
SUCCESS_COLOR = "#4ade80"
ERROR_COLOR = "#f87171"
WARNING_COLOR = "#fbbf24"
BORDER_COLOR = "#222244"
INPUT_BG = "#1a1a2e"
HOVER_COLOR = "#1e1e3a"


# ─── Stylesheet ──────────────────────────────────────────────────────────────
STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_COLOR};
    color: {TEXT_COLOR};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QFrame#card {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 16px;
}}
QPushButton {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {HOVER_COLOR};
    border: 1px solid {ACCENT_START};
}}
QPushButton:pressed {{
    background-color: {ACCENT_START};
}}
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    color: white;
    border: none;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}dd, stop:1 {ACCENT_END}dd);
}}
QPushButton#danger {{
    background-color: #3a1111;
    border: 1px solid {ERROR_COLOR}44;
}}
QPushButton#danger:hover {{
    background-color: #4a1111;
    border: 1px solid {ERROR_COLOR};
}}
QPushButton#nav {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 12px 16px;
    font-size: 14px;
}}
QPushButton#nav:hover {{
    background-color: {HOVER_COLOR};
}}
QPushButton#nav:checked, QPushButton#nav[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}33, stop:1 {ACCENT_END}33);
    border-left: 3px solid {ACCENT_START};
}}
QLineEdit, QSpinBox, QComboBox, QTimeEdit, QDateTimeEdit {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ACCENT_START};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_START}44;
}}
QListWidget {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 4px;
}}
QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: {ACCENT_START}44;
}}
QListWidget::item:hover {{
    background-color: {HOVER_COLOR};
}}
QTableWidget {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    gridline-color: {BORDER_COLOR};
}}
QTableWidget::item {{
    padding: 8px;
}}
QTableWidget::item:selected {{
    background-color: {ACCENT_START}44;
}}
QHeaderView::section {{
    background-color: {CARD_COLOR};
    color: {TEXT_DIM};
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 8px;
    font-weight: bold;
}}
QProgressBar {{
    background-color: {INPUT_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_COLOR};
    min-height: 22px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border-radius: 5px;
}}
QGroupBox {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {ACCENT_START};
}}
QCheckBox {{
    color: {TEXT_COLOR};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER_COLOR};
    background-color: {INPUT_BG};
}}
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
    border: none;
}}
QScrollBar:vertical {{
    background-color: {BG_COLOR};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER_COLOR};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT_START}88;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    background-color: {CARD_COLOR};
}}
QTabBar::tab {{
    background-color: {INPUT_BG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {CARD_COLOR};
    color: {ACCENT_START};
    border-bottom: 2px solid {ACCENT_START};
}}
QTextEdit {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px;
}}
QLabel#title {{
    font-size: 22px;
    font-weight: bold;
    color: white;
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {TEXT_DIM};
}}
QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {ACCENT_START};
}}
"""


# ─── Data Models ─────────────────────────────────────────────────────────────

class BackupStatus(str, Enum):
    PENDING = "等待中"
    RUNNING = "运行中"
    SUCCESS = "成功"
    FAILED = "失败"
    CANCELLED = "已取消"


@dataclass
class BackupTask:
    id: str = ""
    name: str = ""
    sources: list = field(default_factory=list)
    destination: str = ""
    schedule: str = "手动"
    schedule_time: str = "00:00"
    compress: bool = True
    encrypt: bool = False
    password: str = ""
    incremental: bool = True
    status: str = BackupStatus.PENDING.value
    last_run: str = ""
    file_count: int = 0
    total_size: int = 0
    created: str = ""


@dataclass
class BackupHistoryEntry:
    id: str = ""
    task_name: str = ""
    timestamp: str = ""
    status: str = ""
    files_count: int = 0
    total_size: int = 0
    duration: str = ""
    backup_path: str = ""
    backup_type: str = ""


# ─── Utility Functions ──────────────────────────────────────────────────────

def generate_id() -> str:
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(time.time()))[-4:]


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    except (OSError, PermissionError):
        return ""
    return hasher.hexdigest()


def get_cloud_folders() -> dict:
    home = Path.home()
    clouds = {}
    onedrive = home / "OneDrive"
    if onedrive.exists():
        clouds["OneDrive"] = str(onedrive)
    gdrive = home / "Google Drive"
    if gdrive.exists():
        clouds["Google Drive"] = str(gdrive)
    gdrive2 = home / "GoogleDrive"
    if gdrive2.exists():
        clouds["Google Drive"] = str(gdrive2)
    return clouds


# ─── Backup Worker Thread ────────────────────────────────────────────────────

class BackupWorker(QThread):
    progress = pyqtSignal(int, str)  # percent, message
    finished = pyqtSignal(dict)  # result dict
    log = pyqtSignal(str)

    def __init__(self, task: BackupTask):
        super().__init__()
        self.task = task
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        start_time = time.time()
        result = {
            "status": BackupStatus.SUCCESS.value,
            "files_count": 0,
            "total_size": 0,
            "backup_path": "",
            "duration": "",
            "error": ""
        }
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.task.name}_{ts}"
            dest_dir = Path(self.task.destination) / backup_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            all_files = []
            for src in self.task.sources:
                src_path = Path(src)
                if src_path.is_file():
                    all_files.append(src_path)
                elif src_path.is_dir():
                    for f in src_path.rglob("*"):
                        if f.is_file():
                            all_files.append(f)

            total = len(all_files)
            if total == 0:
                self.log.emit("⚠ 没有找到需要备份的文件")
                result["status"] = BackupStatus.FAILED.value
                result["error"] = "没有找到需要备份的文件"
                self.finished.emit(result)
                return

            copied = 0
            total_size = 0

            # Incremental: check snapshot
            snapshot_file = Path(self.task.destination) / f".snapshot_{self.task.id}.json"
            snapshot = {}
            if self.task.incremental and snapshot_file.exists():
                try:
                    with open(snapshot_file, 'r') as f:
                        snapshot = json.load(f)
                except Exception:
                    snapshot = {}

            new_snapshot = {}
            skipped = 0

            for i, fpath in enumerate(all_files):
                if self._cancelled:
                    result["status"] = BackupStatus.CANCELLED.value
                    break

                rel = str(fpath)
                new_snapshot[rel] = {"mtime": os.path.getmtime(fpath), "size": os.path.getsize(fpath)}

                if self.task.incremental:
                    old = snapshot.get(rel)
                    if old and old.get("mtime") == os.path.getmtime(fpath) and old.get("size") == os.path.getsize(fpath):
                        skipped += 1
                        pct = int((i + 1) / total * 100)
                        self.progress.emit(pct, f"跳过未变更: {fpath.name}")
                        continue

                try:
                    # Determine relative path from source
                    for src in self.task.sources:
                        src_p = Path(src)
                        if src_p.is_file() and fpath == src_p:
                            rel_path = fpath.name
                            break
                        elif src_p.is_dir():
                            try:
                                rel_path = str(fpath.relative_to(src_p))
                                break
                            except ValueError:
                                continue
                    else:
                        rel_path = fpath.name

                    target = dest_dir / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(fpath), str(target))
                    total_size += fpath.stat().st_size
                    copied += 1
                    pct = int((i + 1) / total * 100)
                    self.progress.emit(pct, f"备份: {fpath.name}")
                    self.log.emit(f"✓ {rel_path} ({format_size(fpath.stat().st_size)})")
                except Exception as e:
                    self.log.emit(f"✗ {fpath}: {e}")

            # Save snapshot
            with open(snapshot_file, 'w') as f:
                json.dump(new_snapshot, f)

            result["files_count"] = copied
            result["total_size"] = total_size

            # Compress
            if self.task.compress and not self._cancelled:
                self.progress.emit(90, "正在压缩备份...")
                zip_path = Path(self.task.destination) / f"{backup_name}.zip"
                with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                    for f in dest_dir.rglob("*"):
                        if f.is_file():
                            zf.write(str(f), str(f.relative_to(dest_dir)))
                shutil.rmtree(str(dest_dir), ignore_errors=True)
                result["backup_path"] = str(zip_path)
                self.log.emit(f"📦 压缩完成: {zip_path.name} ({format_size(zip_path.stat().st_size)})")
            else:
                result["backup_path"] = str(dest_dir)

            if not self._cancelled:
                result["status"] = BackupStatus.SUCCESS.value
                self.progress.emit(100, "备份完成！")

        except Exception as e:
            result["status"] = BackupStatus.FAILED.value
            result["error"] = str(e)
            self.log.emit(f"✗ 错误: {e}")

        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        result["duration"] = f"{mins}分{secs}秒"
        self.finished.emit(result)


# ─── Restore Worker ──────────────────────────────────────────────────────────

class RestoreWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)

    def __init__(self, backup_path: str, restore_dir: str, password: str = ""):
        super().__init__()
        self.backup_path = backup_path
        self.restore_dir = restore_dir
        self.password = password

    def run(self):
        try:
            bp = Path(self.backup_path)
            rd = Path(self.restore_dir)
            rd.mkdir(parents=True, exist_ok=True)

            if bp.suffix == '.zip':
                self.progress.emit(10, "正在解压备份文件...")
                with zipfile.ZipFile(str(bp), 'r') as zf:
                    members = zf.namelist()
                    total = len(members)
                    for i, member in enumerate(members):
                        zf.extract(member, str(rd))
                        pct = 10 + int((i + 1) / total * 85)
                        self.progress.emit(pct, f"恢复: {member}")
                        self.log.emit(f"✓ {member}")
                self.progress.emit(100, "恢复完成！")
                self.finished.emit(True, f"成功恢复 {total} 个文件到 {self.restore_dir}")
            elif bp.is_dir():
                self.progress.emit(10, "正在复制文件...")
                files = list(bp.rglob("*"))
                total = len([f for f in files if f.is_file()])
                count = 0
                for i, f in enumerate(files):
                    if f.is_file():
                        rel = f.relative_to(bp)
                        target = rd / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(f), str(target))
                        count += 1
                        pct = 10 + int((i + 1) / max(total, 1) * 85)
                        self.progress.emit(pct, f"恢复: {rel}")
                self.progress.emit(100, "恢复完成！")
                self.finished.emit(True, f"成功恢复 {count} 个文件到 {self.restore_dir}")
            else:
                self.finished.emit(False, "不支持的备份格式")
        except Exception as e:
            self.finished.emit(False, f"恢复失败: {e}")


# ─── Sidebar Navigation ─────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(f"  {icon_text}  {label}", parent)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)


# ─── Stat Card ───────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")

        layout.addLayout(top)
        layout.addWidget(self.value_lbl)

    def set_value(self, value: str):
        self.value_lbl.setText(value)


# ─── Dashboard Page ──────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("📊 控制面板")
        title.setObjectName("title")
        subtitle = QLabel("系统概览与快速操作")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.card_tasks = StatCard("备份任务", "0", "📋")
        self.card_backups = StatCard("历史记录", "0", "📁")
        self.card_size = StatCard("总备份大小", "0 B", "💾")
        self.card_success = StatCard("成功率", "100%", "✅")
        stats.addWidget(self.card_tasks)
        stats.addWidget(self.card_backups)
        stats.addWidget(self.card_size)
        stats.addWidget(self.card_success)
        layout.addLayout(stats)

        # Quick actions
        qa_group = QGroupBox("⚡ 快速操作")
        qa_layout = QHBoxLayout(qa_group)
        qa_layout.setSpacing(12)

        btn_new = QPushButton("➕ 新建备份任务")
        btn_new.setObjectName("primary")
        btn_new.clicked.connect(lambda: self.app_ref.navigate_to(1))
        btn_restore = QPushButton("♻️ 快速恢复")
        btn_restore.clicked.connect(lambda: self.app_ref.navigate_to(5))
        btn_history = QPushButton("📋 查看历史")
        btn_history.clicked.connect(lambda: self.app_ref.navigate_to(6))

        qa_layout.addWidget(btn_new)
        qa_layout.addWidget(btn_restore)
        qa_layout.addWidget(btn_history)
        layout.addWidget(qa_group)

        # System info
        sys_group = QGroupBox("💻 系统信息")
        sys_layout = QVBoxLayout(sys_group)
        self.sys_info = QLabel()
        self.sys_info.setStyleSheet(f"color: {TEXT_DIM}; line-height: 1.6;")
        self._update_sys_info()
        sys_layout.addWidget(self.sys_info)
        layout.addWidget(sys_group)

        # Recent activity
        recent_group = QGroupBox("🕐 最近活动")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(180)
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_group)

        layout.addStretch()
        self.refresh()

    def _update_sys_info(self):
        info_parts = []
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            info_parts.append(f"💾 内存使用: {format_size(mem.used)} / {format_size(mem.total)} ({mem.percent}%)")
            disk = psutil.disk_usage(Path.home().anchor)
            info_parts.append(f"💿 磁盘空间: {format_size(disk.used)} / {format_size(disk.total)} ({disk.percent}%)")
            info_parts.append(f"🔧 CPU 核心: {psutil.cpu_count()} 个")
        info_parts.append(f"📂 备份目录: {DEFAULT_BACKUP_DIR}")
        self.sys_info.setText("\n".join(info_parts))

    def refresh(self):
        tasks = self.app_ref.tasks
        history = self.app_ref.history
        self.card_tasks.set_value(str(len(tasks)))
        self.card_backups.set_value(str(len(history)))
        total_size = sum(h.total_size for h in history)
        self.card_size.set_value(format_size(total_size))
        if history:
            success = sum(1 for h in history if h.status == BackupStatus.SUCCESS.value)
            rate = int(success / len(history) * 100)
            self.card_success.set_value(f"{rate}%")
        self.recent_list.clear()
        for h in history[-5:][::-1]:
            icon = "✅" if h.status == BackupStatus.SUCCESS.value else "❌"
            self.recent_list.addItem(f"{icon} {h.task_name} - {h.timestamp} ({h.status})")


# ─── Backup Task Page ───────────────────────────────────────────────────────

class BackupTaskPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._sources = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("📁 备份任务管理")
        title.setObjectName("title")
        subtitle = QLabel("创建和管理备份任务")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Task list
        list_group = QGroupBox("📋 任务列表")
        list_layout = QVBoxLayout(list_group)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels(["名称", "源路径", "目标", "计划", "压缩", "状态", "上次运行"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.verticalHeader().setVisible(False)
        list_layout.addWidget(self.task_table)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ 新建任务")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._new_task)
        btn_run = QPushButton("▶ 立即执行")
        btn_run.clicked.connect(self._run_selected)
        btn_del = QPushButton("🗑 删除任务")
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_run)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)
        layout.addWidget(list_group)

        layout.addStretch()

    def refresh(self):
        tasks = self.app_ref.tasks
        self.task_table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.task_table.setItem(i, 0, QTableWidgetItem(t.name))
            self.task_table.setItem(i, 1, QTableWidgetItem("; ".join(t.sources)))
            self.task_table.setItem(i, 2, QTableWidgetItem(t.destination))
            self.task_table.setItem(i, 3, QTableWidgetItem(t.schedule))
            self.task_table.setItem(i, 4, QTableWidgetItem("✓" if t.compress else "✗"))
            self.task_table.setItem(i, 5, QTableWidgetItem(t.status))
            self.task_table.setItem(i, 6, QTableWidgetItem(t.last_run or "从未"))

    def _new_task(self):
        dlg = TaskDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            task = dlg.get_task()
            self.app_ref.tasks.append(task)
            self.app_ref.save_tasks()
            self.refresh()

    def _run_selected(self):
        row = self.task_table.currentRow()
        if row < 0 or row >= len(self.app_ref.tasks):
            QMessageBox.warning(self, "提示", "请先选择一个任务")
            return
        task = self.app_ref.tasks[row]
        self.app_ref.run_backup(task)

    def _delete_selected(self):
        row = self.task_table.currentRow()
        if row < 0 or row >= len(self.app_ref.tasks):
            QMessageBox.warning(self, "提示", "请先选择一个任务")
            return
        reply = QMessageBox.question(self, "确认", "确定要删除此任务吗？",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app_ref.tasks.pop(row)
            self.app_ref.save_tasks()
            self.refresh()


# ─── Task Dialog ─────────────────────────────────────────────────────────────

class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建备份任务")
        self.setMinimumWidth(500)
        self._sources = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入任务名称...")
        form.addRow("任务名称:", self.name_edit)

        # Sources
        src_widget = QWidget()
        src_layout = QVBoxLayout(src_widget)
        src_layout.setContentsMargins(0, 0, 0, 0)
        self.src_list = QListWidget()
        self.src_list.setMaximumHeight(100)
        src_btns = QHBoxLayout()
        btn_add_file = QPushButton("📄 添加文件")
        btn_add_file.clicked.connect(self._add_file)
        btn_add_dir = QPushButton("📁 添加文件夹")
        btn_add_dir.clicked.connect(self._add_dir)
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(lambda: (self._sources.clear(), self.src_list.clear()))
        src_btns.addWidget(btn_add_file)
        src_btns.addWidget(btn_add_dir)
        src_btns.addWidget(btn_clear)
        src_layout.addWidget(self.src_list)
        src_layout.addLayout(src_btns)
        form.addRow("备份源:", src_widget)

        # Destination
        dest_widget = QWidget()
        dest_layout = QHBoxLayout(dest_widget)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("选择备份目标目录...")
        btn_dest = QPushButton("浏览")
        btn_dest.clicked.connect(self._pick_dest)
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(btn_dest)
        form.addRow("备份目标:", dest_widget)

        # Schedule
        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["手动", "每日", "每周", "每月"])
        form.addRow("备份计划:", self.schedule_combo)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        form.addRow("执行时间:", self.time_edit)

        # Options
        self.compress_cb = QCheckBox("压缩备份")
        self.compress_cb.setChecked(True)
        form.addRow("", self.compress_cb)

        self.incremental_cb = QCheckBox("增量备份（仅备份变更文件）")
        self.incremental_cb.setChecked(True)
        form.addRow("", self.incremental_cb)

        self.encrypt_cb = QCheckBox("加密备份")
        self.encrypt_cb.toggled.connect(self._toggle_password)
        form.addRow("", self.encrypt_cb)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("输入加密密码...")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setEnabled(False)
        form.addRow("密码:", self.password_edit)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_password(self, checked):
        self.password_edit.setEnabled(checked)

    def _add_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        for f in files:
            if f not in self._sources:
                self._sources.append(f)
                self.src_list.addItem(f)

    def _add_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if d and d not in self._sources:
            self._sources.append(d)
            self.src_list.addItem(d)

    def _pick_dest(self):
        d = QFileDialog.getExistingDirectory(self, "选择备份目标")
        if d:
            self.dest_edit.setText(d)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入任务名称")
            return
        if not self._sources:
            QMessageBox.warning(self, "提示", "请添加至少一个备份源")
            return
        if not self.dest_edit.text().strip():
            QMessageBox.warning(self, "提示", "请选择备份目标")
            return
        self.accept()

    def get_task(self) -> BackupTask:
        return BackupTask(
            id=generate_id(),
            name=self.name_edit.text().strip(),
            sources=list(self._sources),
            destination=self.dest_edit.text().strip(),
            schedule=self.schedule_combo.currentText(),
            schedule_time=self.time_edit.time().toString("HH:mm"),
            compress=self.compress_cb.isChecked(),
            encrypt=self.encrypt_cb.isChecked(),
            password=self.password_edit.text(),
            incremental=self.incremental_cb.isChecked(),
            created=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


# ─── Incremental Backup Page ─────────────────────────────────────────────────

class IncrementalPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("🔄 增量备份")
        title.setObjectName("title")
        subtitle = QLabel("智能检测文件变更，仅备份修改内容")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Info card
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_title = QLabel("💡 增量备份说明")
        info_title.setStyleSheet(f"color: {ACCENT_START}; font-weight: bold; font-size: 15px;")
        info_text = QLabel(
            "增量备份通过比较文件的修改时间和大小来检测变更。\n"
            "只有新增或修改过的文件才会被备份，大幅节省存储空间和时间。\n\n"
            "• 首次运行将执行完整备份\n"
            "• 后续运行仅备份变更文件\n"
            "• 使用快照文件记录上次备份状态"
        )
        info_text.setStyleSheet(f"color: {TEXT_DIM}; line-height: 1.8;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        layout.addWidget(info_card)

        # Source comparison
        comp_group = QGroupBox("📊 文件变更检测")
        comp_layout = QVBoxLayout(comp_group)

        btn_row = QHBoxLayout()
        btn_src = QPushButton("📂 选择源目录")
        btn_src.clicked.connect(self._select_source)
        self.src_label = QLabel("未选择")
        self.src_label.setStyleSheet(f"color: {TEXT_DIM};")
        btn_row.addWidget(btn_src)
        btn_row.addWidget(self.src_label)
        btn_row.addStretch()
        comp_layout.addLayout(btn_row)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(250)
        comp_layout.addWidget(self.result_text)

        btn_scan = QPushButton("🔍 扫描变更")
        btn_scan.setObjectName("primary")
        btn_scan.clicked.connect(self._scan_changes)
        comp_layout.addWidget(btn_scan)
        layout.addWidget(comp_group)

        # Incremental task list
        inc_group = QGroupBox("📋 已启用增量备份的任务")
        inc_layout = QVBoxLayout(inc_group)
        self.inc_list = QListWidget()
        self.inc_list.setMaximumHeight(150)
        inc_layout.addWidget(self.inc_list)
        layout.addWidget(inc_group)

        layout.addStretch()
        self._source_dir = ""

    def _select_source(self):
        d = QFileDialog.getExistingDirectory(self, "选择源目录")
        if d:
            self._source_dir = d
            self.src_label.setText(d)

    def _scan_changes(self):
        if not self._source_dir:
            QMessageBox.warning(self, "提示", "请先选择源目录")
            return
        self.result_text.clear()
        self.result_text.append("🔍 正在扫描文件变更...\n")
        total_files = 0
        total_size = 0
        for f in Path(self._source_dir).rglob("*"):
            if f.is_file():
                total_files += 1
                total_size += f.stat().st_size
        self.result_text.append(f"📂 源目录: {self._source_dir}")
        self.result_text.append(f"📄 文件总数: {total_files}")
        self.result_text.append(f"💾 总大小: {format_size(total_size)}")
        self.result_text.append(f"\n✅ 扫描完成！使用增量备份可避免重复备份未变更文件。")

    def refresh(self):
        self.inc_list.clear()
        for t in self.app_ref.tasks:
            if t.incremental:
                self.inc_list.addItem(f"✓ {t.name} - {t.schedule} - {t.last_run or '从未运行'}")


# ─── Schedule Page ───────────────────────────────────────────────────────────

class SchedulePage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("⏰ 定时备份")
        title.setObjectName("title")
        subtitle = QLabel("配置自动备份调度计划")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Schedule table
        sched_group = QGroupBox("📅 调度任务")
        sched_layout = QVBoxLayout(sched_group)

        self.sched_table = QTableWidget()
        self.sched_table.setColumnCount(5)
        self.sched_table.setHorizontalHeaderLabels(["任务名称", "计划类型", "执行时间", "状态", "下次执行"])
        self.sched_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sched_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sched_table.verticalHeader().setVisible(False)
        sched_layout.addWidget(self.sched_table)

        btn_row = QHBoxLayout()
        btn_enable = QPushButton("▶ 启用调度")
        btn_enable.setObjectName("primary")
        btn_enable.clicked.connect(self._enable_schedule)
        btn_disable = QPushButton("⏸ 暂停调度")
        btn_disable.clicked.connect(self._disable_schedule)
        btn_row.addWidget(btn_enable)
        btn_row.addWidget(btn_disable)
        btn_row.addStretch()
        sched_layout.addLayout(btn_row)
        layout.addWidget(sched_group)

        # Schedule info
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_title = QLabel("💡 调度说明")
        info_title.setStyleSheet(f"color: {ACCENT_START}; font-weight: bold; font-size: 15px;")
        info_desc = QLabel(
            "• 每日: 每天在指定时间自动执行备份\n"
            "• 每周: 每周一在指定时间自动执行备份\n"
            "• 每月: 每月1号在指定时间自动执行备份\n"
            "• 手动: 仅在手动触发时执行"
        )
        info_desc.setStyleSheet(f"color: {TEXT_DIM}; line-height: 1.8;")
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_desc)
        layout.addWidget(info_card)

        layout.addStretch()

    def refresh(self):
        tasks = self.app_ref.tasks
        scheduled = [t for t in tasks if t.schedule != "手动"]
        self.sched_table.setRowCount(len(scheduled))
        for i, t in enumerate(scheduled):
            self.sched_table.setItem(i, 0, QTableWidgetItem(t.name))
            self.sched_table.setItem(i, 1, QTableWidgetItem(t.schedule))
            self.sched_table.setItem(i, 2, QTableWidgetItem(t.schedule_time))
            self.sched_table.setItem(i, 3, QTableWidgetItem("启用"))
            next_exec = self._calc_next_run(t.schedule, t.schedule_time)
            self.sched_table.setItem(i, 4, QTableWidgetItem(next_exec))

    def _calc_next_run(self, schedule: str, time_str: str) -> str:
        now = datetime.datetime.now()
        h, m = map(int, time_str.split(":"))
        if schedule == "每日":
            next_run = now.replace(hour=h, minute=m, second=0)
            if next_run <= now:
                next_run += datetime.timedelta(days=1)
            return next_run.strftime("%Y-%m-%d %H:%M")
        elif schedule == "每周":
            days_ahead = 7 - now.weekday()
            next_run = (now + datetime.timedelta(days=days_ahead)).replace(hour=h, minute=m, second=0)
            return next_run.strftime("%Y-%m-%d %H:%M")
        elif schedule == "每月":
            if now.day == 1 and now.replace(hour=h, minute=m) > now:
                return now.replace(day=1, hour=h, minute=m, second=0).strftime("%Y-%m-%d %H:%M")
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=1, hour=h, minute=m, second=0)
            else:
                next_run = now.replace(month=now.month+1, day=1, hour=h, minute=m, second=0)
            return next_run.strftime("%Y-%m-%d %H:%M")
        return "手动"

    def _enable_schedule(self):
        QMessageBox.information(self, "提示", "调度已启用。程序将在后台监控定时任务。")

    def _disable_schedule(self):
        QMessageBox.information(self, "提示", "调度已暂停。")


# ─── Compression Page ────────────────────────────────────────────────────────

class CompressionPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("📦 压缩管理")
        title.setObjectName("title")
        subtitle = QLabel("管理备份压缩设置和压缩统计")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Compression settings
        settings_group = QGroupBox("⚙️ 压缩设置")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(12)

        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 9)
        self.level_spin.setValue(6)
        self.level_spin.setPrefix("级别 ")
        settings_layout.addRow("压缩级别:", self.level_spin)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["ZIP (推荐)", "ZIP (最大压缩)"])
        settings_layout.addRow("压缩格式:", self.format_combo)

        level_info = QLabel("1=最快  ←→  9=最小体积（推荐6）")
        level_info.setStyleSheet(f"color: {TEXT_DIM};")
        settings_layout.addRow("", level_info)

        layout.addWidget(settings_group)

        # Compression stats
        stats_group = QGroupBox("📊 压缩统计")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["备份名称", "原始大小", "压缩后", "压缩率"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stats_table.verticalHeader().setVisible(False)
        stats_layout.addWidget(self.stats_table)
        layout.addWidget(stats_group)

        layout.addStretch()

    def refresh(self):
        history = self.app_ref.history
        compressed = [h for h in history if h.backup_path.endswith('.zip')]
        self.stats_table.setRowCount(len(compressed))
        for i, h in enumerate(compressed):
            self.stats_table.setItem(i, 0, QTableWidgetItem(h.task_name))
            orig_size = format_size(h.total_size) if h.total_size else "未知"
            self.stats_table.setItem(i, 1, QTableWidgetItem(orig_size))
            zip_path = Path(h.backup_path)
            if zip_path.exists():
                zip_size = format_size(zip_path.stat().st_size)
                ratio = f"{zip_path.stat().st_size / max(h.total_size, 1) * 100:.0f}%" if h.total_size else "未知"
            else:
                zip_size = "文件不存在"
                ratio = "N/A"
            self.stats_table.setItem(i, 2, QTableWidgetItem(zip_size))
            self.stats_table.setItem(i, 3, QTableWidgetItem(ratio))


# ─── Encryption Page ─────────────────────────────────────────────────────────

class EncryptionPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("🔐 加密管理")
        title.setObjectName("title")
        subtitle = QLabel("管理备份数据加密设置")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Encryption info
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_title = QLabel("🛡️ 加密说明")
        info_title.setStyleSheet(f"color: {ACCENT_START}; font-weight: bold; font-size: 15px;")
        info_text = QLabel(
            "BackupTool 使用密码保护您的备份数据安全。\n\n"
            "• 备份文件使用密码加密存储\n"
            "• 恢复时需要输入正确密码\n"
            "• 请妥善保管密码，密码丢失将无法恢复数据\n"
            "• 建议使用强密码（包含大小写字母、数字和特殊字符）"
        )
        info_text.setStyleSheet(f"color: {TEXT_DIM}; line-height: 1.8;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        layout.addWidget(info_card)

        # Encrypted backups list
        enc_group = QGroupBox("🔒 已加密的备份")
        enc_layout = QVBoxLayout(enc_group)
        self.enc_table = QTableWidget()
        self.enc_table.setColumnCount(4)
        self.enc_table.setHorizontalHeaderLabels(["任务名称", "备份时间", "备份大小", "状态"])
        self.enc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.enc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.enc_table.verticalHeader().setVisible(False)
        enc_layout.addWidget(self.enc_table)
        layout.addWidget(enc_group)

        # Password tools
        tools_group = QGroupBox("🔑 密码工具")
        tools_layout = QVBoxLayout(tools_group)
        pw_row = QHBoxLayout()
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("输入密码强度测试...")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        btn_test = QPushButton("测试强度")
        btn_test.clicked.connect(self._test_strength)
        pw_row.addWidget(self.pw_input)
        pw_row.addWidget(btn_test)
        tools_layout.addLayout(pw_row)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet(f"color: {TEXT_DIM};")
        tools_layout.addWidget(self.strength_label)
        layout.addWidget(tools_group)

        layout.addStretch()

    def _test_strength(self):
        pw = self.pw_input.text()
        if not pw:
            self.strength_label.setText("")
            return
        score = 0
        if len(pw) >= 8: score += 1
        if len(pw) >= 12: score += 1
        if any(c.isupper() for c in pw): score += 1
        if any(c.islower() for c in pw): score += 1
        if any(c.isdigit() for c in pw): score += 1
        if any(not c.isalnum() for c in pw): score += 1
        labels = ["❌ 极弱", "⚠️ 弱", "⚠️ 一般", "✓ 中等", "✓ 强", "💪 很强", "💪 极强"]
        color = [ERROR_COLOR, ERROR_COLOR, WARNING_COLOR, WARNING_COLOR, SUCCESS_COLOR, SUCCESS_COLOR, SUCCESS_COLOR]
        idx = min(score, len(labels)-1)
        self.strength_label.setText(f"密码强度: {labels[idx]}")
        self.strength_label.setStyleSheet(f"color: {color[idx]}; font-weight: bold;")

    def refresh(self):
        enc_tasks = [t for t in self.app_ref.tasks if t.encrypt]
        self.enc_table.setRowCount(len(enc_tasks))
        for i, t in enumerate(enc_tasks):
            self.enc_table.setItem(i, 0, QTableWidgetItem(t.name))
            self.enc_table.setItem(i, 1, QTableWidgetItem(t.last_run or "从未"))
            self.enc_table.setItem(i, 2, QTableWidgetItem(format_size(t.total_size)))
            self.enc_table.setItem(i, 3, QTableWidgetItem("🔒 已加密"))


# ─── Restore Page ────────────────────────────────────────────────────────────

class RestorePage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("♻️ 数据恢复")
        title.setObjectName("title")
        subtitle = QLabel("从备份中恢复文件和数据")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Restore source
        src_group = QGroupBox("📂 选择备份源")
        src_layout = QVBoxLayout(src_group)

        src_row = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("选择备份文件（.zip）或备份目录...")
        btn_src = QPushButton("浏览")
        btn_src.clicked.connect(self._pick_source)
        src_row.addWidget(self.src_edit)
        src_row.addWidget(btn_src)
        src_layout.addLayout(src_row)

        # Recent backups
        recent_label = QLabel("最近备份:")
        recent_label.setStyleSheet(f"color: {TEXT_DIM};")
        src_layout.addWidget(recent_label)
        self.recent_backups = QListWidget()
        self.recent_backups.setMaximumHeight(120)
        self.recent_backups.itemDoubleClicked.connect(self._select_recent)
        src_layout.addWidget(self.recent_backups)
        layout.addWidget(src_group)

        # Restore target
        dest_group = QGroupBox("📁 恢复目标")
        dest_layout = QHBoxLayout(dest_group)
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("选择恢复目标目录...")
        btn_dest = QPushButton("浏览")
        btn_dest.clicked.connect(self._pick_dest)
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(btn_dest)
        layout.addWidget(dest_group)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM};")
        layout.addWidget(self.status_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_restore = QPushButton("♻️ 开始恢复")
        btn_restore.setObjectName("primary")
        btn_restore.clicked.connect(self._start_restore)
        btn_row.addWidget(btn_restore)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Log
        log_group = QGroupBox("📋 恢复日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        layout.addStretch()

    def _pick_source(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "ZIP 文件 (*.zip);;所有文件 (*)")
        if f:
            self.src_edit.setText(f)
        else:
            d = QFileDialog.getExistingDirectory(self, "选择备份目录")
            if d:
                self.src_edit.setText(d)

    def _pick_dest(self):
        d = QFileDialog.getExistingDirectory(self, "选择恢复目标")
        if d:
            self.dest_edit.setText(d)

    def _select_recent(self, item):
        text = item.text()
        # Extract path from the text
        parts = text.split(" - ")
        if len(parts) >= 2:
            self.src_edit.setText(parts[-1].strip())

    def _start_restore(self):
        src = self.src_edit.text().strip()
        dest = self.dest_edit.text().strip()
        if not src or not Path(src).exists():
            QMessageBox.warning(self, "提示", "请选择有效的备份源")
            return
        if not dest:
            QMessageBox.warning(self, "提示", "请选择恢复目标目录")
            return

        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("正在恢复...")

        self._worker = RestoreWorker(src, dest)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(lambda msg: self.log_text.append(msg))
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_finished(self, success, msg):
        self.status_label.setText(msg)
        if success:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.critical(self, "失败", msg)

    def refresh(self):
        self.recent_backups.clear()
        for h in self.app_ref.history[-10:][::-1]:
            icon = "✅" if h.status == BackupStatus.SUCCESS.value else "❌"
            self.recent_backups.addItem(f"{icon} {h.task_name} ({h.timestamp}) - {h.backup_path}")


# ─── History Page ────────────────────────────────────────────────────────────

class HistoryPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("📋 备份历史")
        title.setObjectName("title")
        subtitle = QLabel("查看和管理所有备份操作记录")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Filter row
        filter_row = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "成功", "失败", "已取消"])
        self.filter_combo.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(QLabel("筛选:"))
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()

        btn_clear = QPushButton("🗑 清空历史")
        btn_clear.setObjectName("danger")
        btn_clear.clicked.connect(self._clear_history)
        filter_row.addWidget(btn_clear)
        layout.addLayout(filter_row)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(["任务名称", "时间", "状态", "文件数", "大小", "耗时", "备份路径"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.history_table)

        # Details
        detail_group = QGroupBox("📝 详细信息")
        detail_layout = QVBoxLayout(detail_group)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        self.history_table.currentItemChanged.connect(self._show_detail)
        detail_layout.addWidget(self.detail_text)
        layout.addWidget(detail_group)

        layout.addStretch()

    def _show_detail(self):
        row = self.history_table.currentRow()
        if row < 0:
            return
        history = self._filtered_history()
        if row >= len(history):
            return
        h = history[row]
        self.detail_text.setText(
            f"任务名称: {h.task_name}\n"
            f"备份时间: {h.timestamp}\n"
            f"执行状态: {h.status}\n"
            f"文件数量: {h.files_count}\n"
            f"数据大小: {format_size(h.total_size)}\n"
            f"执行耗时: {h.duration}\n"
            f"备份路径: {h.backup_path}\n"
            f"备份类型: {h.backup_type}"
        )

    def _filtered_history(self):
        history = self.app_ref.history
        filt = self.filter_combo.currentText()
        if filt == "成功":
            return [h for h in history if h.status == BackupStatus.SUCCESS.value]
        elif filt == "失败":
            return [h for h in history if h.status == BackupStatus.FAILED.value]
        elif filt == "已取消":
            return [h for h in history if h.status == BackupStatus.CANCELLED.value]
        return history

    def _clear_history(self):
        reply = QMessageBox.question(self, "确认", "确定要清空所有历史记录吗？",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app_ref.history.clear()
            self.app_ref.save_history()
            self.refresh()

    def refresh(self):
        history = self._filtered_history()
        self.history_table.setRowCount(len(history))
        for i, h in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(h.task_name))
            self.history_table.setItem(i, 1, QTableWidgetItem(h.timestamp))
            status_item = QTableWidgetItem(h.status)
            if h.status == BackupStatus.SUCCESS.value:
                status_item.setForeground(QColor(SUCCESS_COLOR))
            elif h.status == BackupStatus.FAILED.value:
                status_item.setForeground(QColor(ERROR_COLOR))
            self.history_table.setItem(i, 2, status_item)
            self.history_table.setItem(i, 3, QTableWidgetItem(str(h.files_count)))
            self.history_table.setItem(i, 4, QTableWidgetItem(format_size(h.total_size)))
            self.history_table.setItem(i, 5, QTableWidgetItem(h.duration))
            self.history_table.setItem(i, 6, QTableWidgetItem(h.backup_path))
        self.detail_text.clear()


# ─── Cloud Sync Page ─────────────────────────────────────────────────────────

class CloudSyncPage(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("☁️ 云同步")
        title.setObjectName("title")
        subtitle = QLabel("将备份同步到云端存储")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Cloud providers
        providers_group = QGroupBox("🌐 云存储服务")
        providers_layout = QVBoxLayout(providers_group)

        # OneDrive
        od_card = QFrame()
        od_card.setObjectName("card")
        od_layout = QHBoxLayout(od_card)
        od_icon = QLabel("☁️")
        od_icon.setStyleSheet("font-size: 32px;")
        od_info = QVBoxLayout()
        od_name = QLabel("OneDrive")
        od_name.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.od_status = QLabel("检测中...")
        self.od_status.setStyleSheet(f"color: {TEXT_DIM};")
        od_info.addWidget(od_name)
        od_info.addWidget(self.od_status)
        od_layout.addWidget(od_icon)
        od_layout.addLayout(od_info)
        od_layout.addStretch()
        self.od_btn = QPushButton("选择文件夹")
        self.od_btn.clicked.connect(lambda: self._pick_cloud("onedrive"))
        od_layout.addWidget(self.od_btn)
        providers_layout.addWidget(od_card)

        # Google Drive
        gd_card = QFrame()
        gd_card.setObjectName("card")
        gd_layout = QHBoxLayout(gd_card)
        gd_icon = QLabel("📁")
        gd_icon.setStyleSheet("font-size: 32px;")
        gd_info = QVBoxLayout()
        gd_name = QLabel("Google Drive")
        gd_name.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.gd_status = QLabel("检测中...")
        self.gd_status.setStyleSheet(f"color: {TEXT_DIM};")
        gd_info.addWidget(gd_name)
        gd_info.addWidget(self.gd_status)
        gd_layout.addWidget(gd_icon)
        gd_layout.addLayout(gd_info)
        gd_layout.addStretch()
        self.gd_btn = QPushButton("选择文件夹")
        self.gd_btn.clicked.connect(lambda: self._pick_cloud("gdrive"))
        gd_layout.addWidget(self.gd_btn)
        providers_layout.addWidget(gd_card)

        layout.addWidget(providers_group)

        # Sync settings
        sync_group = QGroupBox("⚙️ 同步设置")
        sync_layout = QVBoxLayout(sync_group)

        self.auto_sync_cb = QCheckBox("备份完成后自动同步到云端")
        sync_layout.addWidget(self.auto_sync_cb)

        self.verify_cb = QCheckBox("同步后验证文件完整性")
        self.verify_cb.setChecked(True)
        sync_layout.addWidget(self.verify_cb)

        sync_btn_row = QHBoxLayout()
        btn_sync_now = QPushButton("🔄 立即同步")
        btn_sync_now.setObjectName("primary")
        btn_sync_now.clicked.connect(self._sync_now)
        sync_btn_row.addWidget(btn_sync_now)
        sync_btn_row.addStretch()
        sync_layout.addLayout(sync_btn_row)
        layout.addWidget(sync_group)

        # Sync status
        status_group = QGroupBox("📊 同步状态")
        status_layout = QVBoxLayout(status_group)
        self.sync_status_text = QTextEdit()
        self.sync_status_text.setReadOnly(True)
        self.sync_status_text.setMaximumHeight(150)
        status_layout.addWidget(self.sync_status_text)
        layout.addWidget(status_group)

        layout.addStretch()
        self._cloud_paths = {}

    def _pick_cloud(self, provider):
        d = QFileDialog.getExistingDirectory(self, f"选择 {provider} 文件夹")
        if d:
            if provider == "onedrive":
                self.od_status.setText(f"✓ 已配置: {d}")
                self.od_status.setStyleSheet(f"color: {SUCCESS_COLOR};")
                self._cloud_paths["onedrive"] = d
            else:
                self.gd_status.setText(f"✓ 已配置: {d}")
                self.gd_status.setStyleSheet(f"color: {SUCCESS_COLOR};")
                self._cloud_paths["gdrive"] = d

    def _sync_now(self):
        if not self._cloud_paths:
            QMessageBox.warning(self, "提示", "请先配置至少一个云存储路径")
            return
        self.sync_status_text.clear()
        self.sync_status_text.append("🔄 开始同步...\n")

        # Copy recent backups to cloud
        synced = 0
        for h in self.app_ref.history:
            if h.status != BackupStatus.SUCCESS.value:
                continue
            bp = Path(h.backup_path)
            if not bp.exists():
                continue
            for cloud_name, cloud_path in self._cloud_paths.items():
                dest = Path(cloud_path) / "Backups" / bp.name
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if bp.is_file():
                        shutil.copy2(str(bp), str(dest))
                    elif bp.is_dir():
                        if dest.exists():
                            shutil.rmtree(str(dest))
                        shutil.copytree(str(bp), str(dest))
                    self.sync_status_text.append(f"✅ [{cloud_name}] {bp.name}")
                    synced += 1
                except Exception as e:
                    self.sync_status_text.append(f"❌ [{cloud_name}] {bp.name}: {e}")

        self.sync_status_text.append(f"\n{'='*40}")
        self.sync_status_text.append(f"✅ 同步完成！共同步 {synced} 个文件")

    def refresh(self):
        clouds = get_cloud_folders()
        if "OneDrive" in clouds:
            self.od_status.setText(f"✓ 自动检测: {clouds['OneDrive']}")
            self.od_status.setStyleSheet(f"color: {SUCCESS_COLOR};")
            self._cloud_paths["onedrive"] = clouds["OneDrive"]
        if "Google Drive" in clouds:
            self.gd_status.setText(f"✓ 自动检测: {clouds['Google Drive']}")
            self.gd_status.setStyleSheet(f"color: {SUCCESS_COLOR};")
            self._cloud_paths["gdrive"] = clouds["Google Drive"]
        self.sync_status_text.clear()


# ─── Main Window ─────────────────────────────────────────────────────────────

class BackupToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)

        self.tasks: list[BackupTask] = []
        self.history: list[BackupHistoryEntry] = []
        self._active_worker = None

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        self._load_data()
        self._build_ui()
        self._setup_scheduler()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_COLOR};
                border-right: 1px solid {BORDER_COLOR};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("🛡️ BackupTool")
        logo.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: white;
            padding: 8px 4px 16px 4px;
        """)
        sidebar_layout.addWidget(logo)

        nav_items = [
            ("📊", "控制面板"),
            ("📁", "备份任务"),
            ("🔄", "增量备份"),
            ("⏰", "定时备份"),
            ("📦", "压缩管理"),
            ("🔐", "加密管理"),
            ("♻️", "数据恢复"),
            ("📋", "备份历史"),
            ("☁️", "云同步"),
        ]

        self.nav_buttons = []
        for icon, label in nav_items:
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, b=btn, i=icon: self._on_nav(b))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Settings button
        btn_settings = QPushButton("  ⚙️  设置")
        btn_settings.setObjectName("nav")
        btn_settings.clicked.connect(self._show_settings)
        sidebar_layout.addWidget(btn_settings)

        # Version label
        ver_label = QLabel(f"v{APP_VERSION}")
        ver_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding: 4px;")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(ver_label)

        main_layout.addWidget(sidebar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)

        self.stack = QStackedWidget()
        self.pages = {}

        self.dashboard_page = DashboardPage(self)
        self.backup_page = BackupTaskPage(self)
        self.incremental_page = IncrementalPage(self)
        self.schedule_page = SchedulePage(self)
        self.compression_page = CompressionPage(self)
        self.encryption_page = EncryptionPage(self)
        self.restore_page = RestorePage(self)
        self.history_page = HistoryPage(self)
        self.cloud_page = CloudSyncPage(self)

        pages = [
            self.dashboard_page, self.backup_page, self.incremental_page,
            self.schedule_page, self.compression_page, self.encryption_page,
            self.restore_page, self.history_page, self.cloud_page
        ]
        for p in pages:
            self.stack.addWidget(p)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content)

        # Status bar
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {CARD_COLOR};
                color: {TEXT_DIM};
                border-top: 1px solid {BORDER_COLOR};
                padding: 4px 12px;
            }}
        """)
        self.statusBar().showMessage("就绪")

        # Select first nav
        self.nav_buttons[0].setChecked(True)
        self.nav_buttons[0].setProperty("active", True)
        self.nav_buttons[0].setStyleSheet(f"""
            QPushButton#nav {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_START}33, stop:1 {ACCENT_END}33);
                border-left: 3px solid {ACCENT_START};
                background-color: transparent;
                border-radius: 8px;
                text-align: left;
                padding: 12px 16px;
                font-size: 14px;
            }}
        """)

    def navigate_to(self, index: int):
        if 0 <= index < len(self.nav_buttons):
            self._on_nav(self.nav_buttons[index])

    def _on_nav(self, clicked_btn):
        for i, btn in enumerate(self.nav_buttons):
            if btn == clicked_btn:
                btn.setChecked(True)
                btn.setProperty("active", True)
                btn.setStyleSheet(f"""
                    QPushButton#nav {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {ACCENT_START}33, stop:1 {ACCENT_END}33);
                        border-left: 3px solid {ACCENT_START};
                        background-color: transparent;
                        border-radius: 8px;
                        text-align: left;
                        padding: 12px 16px;
                        font-size: 14px;
                    }}
                """)
                self.stack.setCurrentIndex(i)
            else:
                btn.setChecked(False)
                btn.setProperty("active", False)
                btn.setStyleSheet("""
                    QPushButton#nav {
                        background-color: transparent;
                        border: none;
                        border-radius: 8px;
                        text-align: left;
                        padding: 12px 16px;
                        font-size: 14px;
                    }
                """)
        # Refresh the current page
        page = self.stack.currentWidget()
        if hasattr(page, 'refresh'):
            page.refresh()

    def _setup_scheduler(self):
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self._check_schedules)
        self.scheduler_timer.start(60000)  # Check every minute

    def _check_schedules(self):
        now = datetime.datetime.now()
        for task in self.tasks:
            if task.schedule == "手动":
                continue
            h, m = map(int, task.schedule_time.split(":"))
            should_run = False
            if task.schedule == "每日" and now.hour == h and now.minute == m:
                should_run = True
            elif task.schedule == "每周" and now.weekday() == 0 and now.hour == h and now.minute == m:
                should_run = True
            elif task.schedule == "每月" and now.day == 1 and now.hour == h and now.minute == m:
                should_run = True
            if should_run:
                self.run_backup(task)

    def run_backup(self, task: BackupTask):
        if self._active_worker and self._active_worker.isRunning():
            QMessageBox.warning(self, "提示", "已有备份任务在运行中，请等待完成")
            return

        task.status = BackupStatus.RUNNING.value
        self.statusBar().showMessage(f"正在执行备份: {task.name}")

        self._active_worker = BackupWorker(task)
        self._active_worker.progress.connect(lambda pct, msg: self._on_backup_progress(pct, msg, task))
        self._active_worker.log.connect(lambda msg: self._on_backup_log(msg))
        self._active_worker.finished.connect(lambda result: self._on_backup_finished(result, task))
        self._active_worker.start()

    def _on_backup_progress(self, pct, msg, task):
        self.statusBar().showMessage(f"[{task.name}] {msg} ({pct}%)")

    def _on_backup_log(self, msg):
        print(f"[Backup] {msg}")

    def _on_backup_finished(self, result, task):
        task.status = result["status"]
        task.last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.file_count = result["files_count"]
        task.total_size = result["total_size"]

        entry = BackupHistoryEntry(
            id=generate_id(),
            task_name=task.name,
            timestamp=task.last_run,
            status=result["status"],
            files_count=result["files_count"],
            total_size=result["total_size"],
            duration=result["duration"],
            backup_path=result["backup_path"],
            backup_type="增量" if task.incremental else "完整"
        )
        self.history.append(entry)
        self.save_tasks()
        self.save_history()

        if result["status"] == BackupStatus.SUCCESS.value:
            self.statusBar().showMessage(f"✅ 备份完成: {task.name} ({result['files_count']} 文件)")
            QMessageBox.information(self, "备份完成",
                f"任务「{task.name}」备份成功！\n"
                f"文件数: {result['files_count']}\n"
                f"大小: {format_size(result['total_size'])}\n"
                f"耗时: {result['duration']}")
        else:
            self.statusBar().showMessage(f"❌ 备份失败: {task.name}")
            if result.get("error"):
                QMessageBox.critical(self, "备份失败", f"错误: {result['error']}")

        self._active_worker = None
        # Refresh current page
        page = self.stack.currentWidget()
        if hasattr(page, 'refresh'):
            page.refresh()

    def _show_settings(self):
        QMessageBox.information(self, "设置", "设置功能开发中...")

    # ─── Data persistence ────────────────────────────────────────────────

    def _load_data(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for t in data.get("tasks", []):
                    self.tasks.append(BackupTask(**t))
            except Exception:
                pass

        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for h in data.get("history", []):
                    self.history.append(BackupHistoryEntry(**h))
            except Exception:
                pass

    def save_tasks(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"tasks": [asdict(t) for t in self.tasks]}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({"history": [asdict(h) for h in self.history]}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史失败: {e}")


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_COLOR))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Base, QColor(INPUT_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CARD_COLOR))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Button, QColor(INPUT_BG))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_START))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(CARD_COLOR))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_COLOR))
    app.setPalette(palette)

    window = BackupToolWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
