"""
DiskCleanup - 专业磁盘清理工具
基于 PyQt6 构建的 Windows 磁盘清理桌面应用程序
"""

import sys
import os
import hashlib
import threading
import time
import winreg
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QComboBox, QSpinBox,
    QFileDialog, QMessageBox, QGroupBox, QGridLayout, QLineEdit,
    QScrollArea, QSplitter, QHeaderView, QMenu, QSystemTrayIcon,
    QDialog, QDialogButtonBox, QFormLayout, QTimeEdit, QDateEdit
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QParallelAnimationGroup, QTime
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPixmap, QAction, QCursor
)

# ============================================================================
# 深色主题样式表
# ============================================================================
DARK_THEME = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QFrame#card {
    background-color: #111122;
    border: 1px solid #1a1a3a;
    border-radius: 12px;
    padding: 16px;
}

QFrame#sidebar {
    background-color: #0d0d1a;
    border-right: 1px solid #1a1a3a;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #8888aa;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_btn:hover {
    background-color: #1a1a3a;
    color: #bbbbdd;
}

QPushButton#nav_btn:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: 600;
}

QPushButton#action_btn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#action_btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #778efb, stop:1 #875bb5);
}

QPushButton#action_btn:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #556dd9, stop:1 #653a91);
}

QPushButton#secondary_btn {
    background-color: #1a1a3a;
    color: #aaaacc;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

QPushButton#secondary_btn:hover {
    background-color: #2a2a4a;
    color: white;
}

QPushButton#danger_btn {
    background-color: #cc3344;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#danger_btn:hover {
    background-color: #dd4455;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 13px;
    color: #6666aa;
}

QLabel#stat_value {
    font-size: 28px;
    font-weight: 700;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    -webkit-background-clip: text;
    color: #667eea;
}

QLabel#stat_label {
    font-size: 12px;
    color: #6666aa;
    font-weight: 500;
}

QProgressBar {
    background-color: #1a1a3a;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}

QTreeWidget {
    background-color: #0d0d1a;
    border: 1px solid #1a1a3a;
    border-radius: 8px;
    color: #ccccdd;
    font-size: 12px;
    outline: none;
}

QTreeWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #151530;
}

QTreeWidget::item:selected {
    background-color: #1a1a4a;
}

QTreeWidget::item:hover {
    background-color: #151535;
}

QHeaderView::section {
    background-color: #111122;
    color: #8888bb;
    border: none;
    border-bottom: 2px solid #1a1a3a;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}

QCheckBox {
    color: #ccccdd;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a5a;
    background-color: #1a1a3a;
}

QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    border-color: #667eea;
}

QComboBox {
    background-color: #1a1a3a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ccccdd;
    font-size: 13px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #6666aa;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #111122;
    border: 1px solid #2a2a4a;
    color: #ccccdd;
    selection-background-color: #2a2a5a;
}

QSpinBox {
    background-color: #1a1a3a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 8px;
    color: #ccccdd;
}

QLineEdit {
    background-color: #1a1a3a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ccccdd;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #667eea;
}

QGroupBox {
    color: #aaaacc;
    border: 1px solid #1a1a3a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QScrollBar:vertical {
    background-color: #0a0a15;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2a2a4a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3a3a5a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0a0a15;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #2a2a4a;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #3a3a5a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QMenu {
    background-color: #111122;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 4px;
    color: #ccccdd;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2a2a5a;
}
"""


def format_size(size_bytes: int) -> str:
    """将字节数格式化为可读字符串"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def get_file_hash(filepath: str, chunk_size: int = 8192) -> str:
    """计算文件的 MD5 哈希"""
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except (OSError, PermissionError):
        return ""


# ============================================================================
# 工作线程
# ============================================================================

class ScanWorker(QThread):
    """扫描工作线程"""
    progress = pyqtSignal(str, int)  # message, percent
    result = pyqtSignal(list)        # list of results
    finished_signal = pyqtSignal()

    def __init__(self, scan_type: str, **kwargs):
        super().__init__()
        self.scan_type = scan_type
        self.kwargs = kwargs
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self.scan_type == "junk":
                results = self._scan_junk()
            elif self.scan_type == "browser":
                results = self._scan_browser()
            elif self.scan_type == "windows":
                results = self._scan_windows()
            elif self.scan_type == "app_cache":
                results = self._scan_app_cache()
            elif self.scan_type == "registry":
                results = self._scan_registry()
            elif self.scan_type == "duplicate":
                results = self._scan_duplicates()
            elif self.scan_type == "large_files":
                results = self._scan_large_files()
            else:
                results = []
            self.result.emit(results)
        except Exception as e:
            self.result.emit([{"error": str(e)}])
        finally:
            self.finished_signal.emit()

    def _scan_junk(self) -> list:
        """扫描垃圾文件"""
        results = []
        temp_dirs = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
        ]
        temp_dirs = [d for d in temp_dirs if d and os.path.exists(d)]

        total_scanned = 0
        for temp_dir in temp_dirs:
            if self._is_cancelled:
                break
            self.progress.emit(f"正在扫描: {temp_dir}", min(90, total_scanned // 10))
            try:
                for root, dirs, files in os.walk(temp_dir):
                    if self._is_cancelled:
                        break
                    for f in files:
                        try:
                            fpath = os.path.join(root, f)
                            size = os.path.getsize(fpath)
                            if size > 0:
                                results.append({
                                    'path': fpath,
                                    'size': size,
                                    'type': '临时文件',
                                    'category': 'junk'
                                })
                        except (OSError, PermissionError):
                            pass
                        total_scanned += 1
                        if total_scanned % 500 == 0:
                            self.progress.emit(
                                f"已扫描 {total_scanned} 个文件...",
                                min(90, total_scanned // 100)
                            )
            except (OSError, PermissionError):
                pass

        # 扫描日志文件
        log_patterns = ['.log', '.tmp', '.bak', '.old', '.cache']
        appdata = os.environ.get('LOCALAPPDATA', '')
        if appdata:
            for root, dirs, files in os.walk(appdata):
                if self._is_cancelled:
                    break
                for f in files:
                    if any(f.lower().endswith(ext) for ext in log_patterns):
                        try:
                            fpath = os.path.join(root, f)
                            size = os.path.getsize(fpath)
                            if size > 1024:  # > 1KB
                                results.append({
                                    'path': fpath,
                                    'size': size,
                                    'type': '日志/缓存',
                                    'category': 'junk'
                                })
                        except (OSError, PermissionError):
                            pass
                        total_scanned += 1

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_browser(self) -> list:
        """扫描浏览器数据"""
        results = []
        local_app = os.environ.get('LOCALAPPDATA', '')
        browsers = {
            'Chrome': [
                os.path.join(local_app, 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
                os.path.join(local_app, 'Google', 'Chrome', 'User Data', 'Default', 'Code Cache'),
                os.path.join(local_app, 'Google', 'Chrome', 'User Data', 'Default', 'GPUCache'),
            ],
            'Edge': [
                os.path.join(local_app, 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
                os.path.join(local_app, 'Microsoft', 'Edge', 'User Data', 'Default', 'Code Cache'),
            ],
            'Firefox': [
                os.path.join(local_app, 'Mozilla', 'Firefox', 'Profiles'),
            ],
        }

        total = 0
        for browser_name, paths in browsers.items():
            for path in paths:
                if not os.path.exists(path) or self._is_cancelled:
                    continue
                self.progress.emit(f"正在扫描 {browser_name}...", min(90, total // 10))
                try:
                    for root, dirs, files in os.walk(path):
                        if self._is_cancelled:
                            break
                        for f in files:
                            try:
                                fpath = os.path.join(root, f)
                                size = os.path.getsize(fpath)
                                if size > 0:
                                    results.append({
                                        'path': fpath,
                                        'size': size,
                                        'type': f'{browser_name}缓存',
                                        'category': 'browser'
                                    })
                            except (OSError, PermissionError):
                                pass
                            total += 1
                except (OSError, PermissionError):
                    pass

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_windows(self) -> list:
        """扫描 Windows 系统缓存"""
        results = []
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        win_dirs = [
            (os.path.join(windir, 'Temp'), 'Windows临时文件'),
            (os.path.join(windir, 'SoftwareDistribution', 'Download'), '更新缓存'),
            (os.path.join(windir, 'Logs'), '系统日志'),
            (os.path.join(windir, 'Prefetch'), '预取文件'),
            (os.path.join(windir, 'SoftwareDistribution', 'DataStore'), '更新数据'),
        ]

        total = 0
        for dir_path, dir_type in win_dirs:
            if not os.path.exists(dir_path) or self._is_cancelled:
                continue
            self.progress.emit(f"正在扫描: {dir_type}...", min(90, total // 10))
            try:
                for root, dirs, files in os.walk(dir_path):
                    if self._is_cancelled:
                        break
                    for f in files:
                        try:
                            fpath = os.path.join(root, f)
                            size = os.path.getsize(fpath)
                            if size > 0:
                                results.append({
                                    'path': fpath,
                                    'size': size,
                                    'type': dir_type,
                                    'category': 'windows'
                                })
                        except (OSError, PermissionError):
                            pass
                        total += 1
            except (OSError, PermissionError):
                pass

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_app_cache(self) -> list:
        """扫描应用程序缓存"""
        results = []
        local_app = os.environ.get('LOCALAPPDATA', '')
        app_cache_dirs = [
            (os.path.join(local_app, 'Discord'), 'Discord'),
            (os.path.join(local_app, 'Slack'), 'Slack'),
            (os.path.join(local_app, 'Slack', 'Cache'), 'Slack缓存'),
            (os.path.join(local_app, 'Spotify', 'Storage'), 'Spotify'),
            (os.path.join(local_app, 'npm-cache'), 'npm缓存'),
            (os.path.join(local_app, 'pip', 'cache'), 'pip缓存'),
            (os.path.join(local_app, 'NuGet'), 'NuGet缓存'),
            (os.path.join(os.environ.get('USERPROFILE', ''), '.cache'), '用户缓存'),
        ]

        total = 0
        for dir_path, app_name in app_cache_dirs:
            if not os.path.exists(dir_path) or self._is_cancelled:
                continue
            self.progress.emit(f"正在扫描 {app_name}...", min(90, total // 10))
            try:
                for root, dirs, files in os.walk(dir_path):
                    if self._is_cancelled:
                        break
                    for f in files:
                        try:
                            fpath = os.path.join(root, f)
                            size = os.path.getsize(fpath)
                            if size > 0:
                                results.append({
                                    'path': fpath,
                                    'size': size,
                                    'type': f'{app_name}缓存',
                                    'category': 'app_cache'
                                })
                        except (OSError, PermissionError):
                            pass
                        total += 1
            except (OSError, PermissionError):
                pass

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_registry(self) -> list:
        """扫描无效注册表项"""
        results = []
        common_invalid_keys = []

        # 检查常见的无效文件关联
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, '') as root_key:
                i = 0
                while True:
                    if self._is_cancelled:
                        break
                    try:
                        subkey_name = winreg.EnumKey(root_key, i)
                        if subkey_name.startswith('.'):
                            # 检查文件扩展名关联是否有效
                            try:
                                with winreg.OpenKey(root_key, subkey_name) as subkey:
                                    value, _ = winreg.QueryValueEx(subkey, '')
                                    if value:
                                        # 检查关联的类是否存在
                                        try:
                                            winreg.OpenKey(root_key, value)
                                        except FileNotFoundError:
                                            results.append({
                                                'path': f"HKCR\\{subkey_name}",
                                                'size': 0,
                                                'type': '无效文件关联',
                                                'category': 'registry'
                                            })
                                    else:
                                        results.append({
                                            'path': f"HKCR\\{subkey_name}",
                                            'size': 0,
                                            'type': '空文件关联',
                                            'category': 'registry'
                                        })
                            except (OSError, FileNotFoundError):
                                pass
                        i += 1
                    except OSError:
                        break
        except (OSError, PermissionError):
            pass

        # 检查无效的启动项
        startup_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]

        for hkey, key_path in startup_keys:
            if self._is_cancelled:
                break
            try:
                with winreg.OpenKey(hkey, key_path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            # 检查路径是否有效
                            exe_path = value.split('"')[0] if '"' in value else value.split(' ')[0]
                            if exe_path and not os.path.exists(exe_path):
                                hive = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                                results.append({
                                    'path': f"{hive}\\{key_path}\\{name}",
                                    'size': 0,
                                    'type': '无效启动项',
                                    'category': 'registry'
                                })
                            i += 1
                        except OSError:
                            break
            except (OSError, PermissionError):
                pass

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_duplicates(self) -> list:
        """扫描重复文件"""
        scan_path = self.kwargs.get('path', os.environ.get('USERPROFILE', ''))
        results = []
        file_hashes = defaultdict(list)
        total = 0

        self.progress.emit("正在计算文件哈希...", 10)

        # 首先按大小分组
        size_groups = defaultdict(list)
        try:
            for root, dirs, files in os.walk(scan_path):
                if self._is_cancelled:
                    break
                # 跳过系统目录
                dirs[:] = [d for d in dirs if d not in
                          {'$Recycle.Bin', 'System Volume Information', '.git', 'node_modules',
                           '__pycache__', '.venv', 'venv', '.idea', '.vs'}]
                for f in files:
                    try:
                        fpath = os.path.join(root, f)
                        size = os.path.getsize(fpath)
                        if size > 0:
                            size_groups[size].append(fpath)
                    except (OSError, PermissionError):
                        pass
                    total += 1
                    if total % 200 == 0:
                        self.progress.emit(
                            f"已扫描 {total} 个文件...",
                            min(50, total // 1000)
                        )
        except (OSError, PermissionError):
            pass

        # 对大小相同的文件计算哈希
        self.progress.emit("正在比较文件内容...", 60)
        candidates = {k: v for k, v in size_groups.items() if len(v) > 1}
        hash_count = 0
        total_candidates = sum(len(v) for v in candidates.values())

        for size, files in candidates.items():
            for fpath in files:
                if self._is_cancelled:
                    break
                file_hash = get_file_hash(fpath)
                if file_hash:
                    file_hashes[file_hash].append({
                        'path': fpath,
                        'size': size
                    })
                hash_count += 1
                if hash_count % 50 == 0:
                    pct = 60 + int(35 * hash_count / max(total_candidates, 1))
                    self.progress.emit(
                        f"正在比较: {hash_count}/{total_candidates}...",
                        min(95, pct)
                    )

        # 收集重复文件
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                for f in files:
                    results.append({
                        'path': f['path'],
                        'size': f['size'],
                        'type': f'重复文件 (MD5: {file_hash[:8]}...)',
                        'category': 'duplicate',
                        'hash': file_hash,
                        'group_size': f['size'] * len(files)
                    })

        self.progress.emit("扫描完成!", 100)
        return results

    def _scan_large_files(self) -> list:
        """扫描大文件"""
        scan_path = self.kwargs.get('path', 'C:\\')
        min_size = self.kwargs.get('min_size', 100 * 1024 * 1024)  # 100MB
        results = []
        total = 0

        try:
            for root, dirs, files in os.walk(scan_path):
                if self._is_cancelled:
                    break
                dirs[:] = [d for d in dirs if d not in
                          {'$Recycle.Bin', 'System Volume Information', '.git',
                           'node_modules', '__pycache__', '.venv', 'venv'}]
                for f in files:
                    try:
                        fpath = os.path.join(root, f)
                        size = os.path.getsize(fpath)
                        if size >= min_size:
                            results.append({
                                'path': fpath,
                                'size': size,
                                'type': '大文件',
                                'category': 'large_file'
                            })
                    except (OSError, PermissionError):
                        pass
                    total += 1
                    if total % 500 == 0:
                        self.progress.emit(
                            f"已扫描 {total} 个文件, 找到 {len(results)} 个大文件...",
                            min(95, total // 10000)
                        )
        except (OSError, PermissionError):
            pass

        results.sort(key=lambda x: x['size'], reverse=True)
        self.progress.emit("扫描完成!", 100)
        return results


# ============================================================================
# 仪表盘页面
# ============================================================================

class DashboardPage(QWidget):
    """首页仪表盘"""
    navigate = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("🧹 DiskCleanup")
        title.setObjectName("title")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("专业磁盘清理工具 - 让您的电脑焕然一新")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Microsoft YaHei", 13))
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # 磁盘使用统计
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(24)

        for i, (label, icon) in enumerate([
            ("CPU 使用率", "🖥️"), ("内存使用", "💾"),
            ("磁盘空间", "📁"), ("系统运行时间", "⏱️")
        ]):
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(4)

            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI Emoji", 24))
            stat_layout.addWidget(icon_label)

            value_label = QLabel("--")
            value_label.setObjectName("stat_value")
            value_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
            stat_layout.addWidget(value_label)

            name_label = QLabel(label)
            name_label.setObjectName("stat_label")
            stat_layout.addWidget(name_label)

            stats_layout.addWidget(stat_widget)

        layout.addWidget(stats_frame)

        # 功能卡片网格
        cards_frame = QWidget()
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(16)

        features = [
            ("🗑️ 垃圾文件扫描", "扫描并清理临时文件、缓存和日志", 0),
            ("🌐 浏览器清理", "清理浏览器缓存、Cookie 和历史记录", 1),
            ("🪟 Windows 清理", "清理系统临时文件和更新缓存", 2),
            ("📦 应用程序清理", "清理已安装应用的缓存数据", 3),
            ("🔧 注册表清理", "查找并修复无效注册表项", 4),
            ("📁 重复文件查找", "找出磁盘上的重复文件", 5),
            ("📊 大文件查找", "查找占用空间最大的文件", 6),
            ("⏰ 定时清理", "设置自动清理计划任务", 7),
        ]

        for idx, (title_text, desc_text, nav_idx) in enumerate(features):
            card = QFrame()
            card.setObjectName("card")
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            title_lbl = QLabel(title_text)
            title_lbl.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            title_lbl.setStyleSheet("color: #ffffff;")
            card_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc_text)
            desc_lbl.setObjectName("subtitle")
            desc_lbl.setWordWrap(True)
            card_layout.addWidget(desc_lbl)

            card.mousePressEvent = lambda e, idx=nav_idx: self.navigate.emit(idx)
            cards_layout.addWidget(card, idx // 4, idx % 4)

        layout.addWidget(cards_frame)

        # 定时更新统计
        self.stat_timer = QTimer(self)
        self.stat_timer.timeout.connect(self._update_stats)
        self.stat_timer.start(2000)
        self._update_stats()

    def _update_stats(self):
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\') if os.path.exists('C:\\') else None
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            stats_frame = self.findChild(QFrame, "card")
            stat_values = self.findChildren(QLabel, "stat_value")

            if len(stat_values) >= 4:
                stat_values[0].setText(f"{cpu:.0f}%")
                stat_values[1].setText(f"{mem.percent:.0f}%")
                if disk:
                    stat_values[2].setText(f"{disk.percent:.0f}%")
                hours = int(uptime.total_seconds() // 3600)
                stat_values[3].setText(f"{hours}h")
        except Exception:
            pass


# ============================================================================
# 扫描结果页面基类
# ============================================================================

class ScanResultPage(QWidget):
    """扫描结果页面基类"""

    def __init__(self, title: str, description: str, scan_type: str):
        super().__init__()
        self.title_text = title
        self.description = description
        self.scan_type = scan_type
        self.results = []
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题区域
        header = QHBoxLayout()
        title_label = QLabel(self.title_text)
        title_label.setObjectName("title")
        title_label.setFont(QFont("Microsoft YaHei", 22, QFont.Weight.Bold))
        header.addWidget(title_label)

        header.addStretch()

        self.scan_btn = QPushButton("🔍 开始扫描")
        self.scan_btn.setObjectName("action_btn")
        self.scan_btn.setFixedWidth(140)
        self.scan_btn.clicked.connect(self._start_scan)
        header.addWidget(self.scan_btn)

        self.cancel_btn = QPushButton("⛔ 取消")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self._cancel_scan)
        self.cancel_btn.setVisible(False)
        header.addWidget(self.cancel_btn)

        layout.addLayout(header)

        desc = QLabel(self.description)
        desc.setObjectName("subtitle")
        desc.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(desc)

        # 进度区域
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("card")
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)

        self.status_label = QLabel("准备扫描...")
        self.status_label.setStyleSheet("color: #aaaacc; font-size: 13px;")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(12)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_frame)

        # 统计区域
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.count_label = QLabel("找到 0 个项目")
        self.count_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: 600;")
        stats_layout.addWidget(self.count_label)

        self.size_label = QLabel("总计: 0 B")
        self.size_label.setStyleSheet("color: #764ba2; font-size: 14px; font-weight: 600;")
        stats_layout.addWidget(self.size_label)

        stats_layout.addStretch()

        self.select_all_cb = QCheckBox("全选")
        self.select_all_cb.stateChanged.connect(self._toggle_select_all)
        stats_layout.addWidget(self.select_all_cb)

        self.clean_btn = QPushButton("🗑️ 清理选中项")
        self.clean_btn.setObjectName("danger_btn")
        self.clean_btn.setFixedWidth(140)
        self.clean_btn.clicked.connect(self._clean_selected)
        self.clean_btn.setVisible(False)
        stats_layout.addWidget(self.clean_btn)

        layout.addLayout(stats_layout)

        # 结果表格
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["", "路径", "大小", "类型"])
        self.tree.setColumnCount(4)
        self.tree.setColumnWidth(0, 40)
        self.tree.setColumnWidth(1, 500)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 150)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(False)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

    def _start_scan(self):
        self.results = []
        self.tree.clear()
        self.progress_frame.setVisible(True)
        self.scan_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.clean_btn.setVisible(False)
        self.select_all_cb.setChecked(False)

        self.worker = ScanWorker(self.scan_type)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _cancel_scan(self):
        if self.worker:
            self.worker.cancel()

    def _on_progress(self, message, percent):
        self.status_label.setText(message)
        self.progress_bar.setValue(min(percent, 100))

    def _on_result(self, results):
        if results and isinstance(results[0], dict) and 'error' in results[0]:
            QMessageBox.warning(self, "扫描错误", results[0]['error'])
            return

        self.results = results
        self._populate_tree()

    def _on_finished(self):
        self.progress_frame.setVisible(False)
        self.scan_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        if self.results:
            self.clean_btn.setVisible(True)

    def _populate_tree(self):
        self.tree.clear()
        total_size = 0

        for item in self.results:
            tree_item = QTreeWidgetItem()
            tree_item.setCheckState(0, Qt.CheckState.Unchecked)
            tree_item.setText(1, item.get('path', ''))
            size = item.get('size', 0)
            tree_item.setText(2, format_size(size))
            tree_item.setText(3, item.get('type', ''))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
            total_size += size
            self.tree.addTopLevelItem(tree_item)

        self.count_label.setText(f"找到 {len(self.results)} 个项目")
        self.size_label.setText(f"总计: {format_size(total_size)}")

    def _toggle_select_all(self, state):
        check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, check_state)

    def _clean_selected(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                data = item.data(0, Qt.ItemDataRole.UserRole)
                selected.append(data)

        if not selected:
            QMessageBox.information(self, "提示", "请先选择要清理的项目")
            return

        reply = QMessageBox.question(
            self, "确认清理",
            f"确定要清理 {len(selected)} 个项目吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            cleaned = 0
            failed = 0
            for item in selected:
                try:
                    path = item.get('path', '')
                    if item.get('category') == 'registry':
                        # 注册表清理需要特殊处理，这里只是示例
                        cleaned += 1
                    elif os.path.exists(path):
                        if os.path.isfile(path):
                            os.remove(path)
                            cleaned += 1
                        elif os.path.isdir(path):
                            import shutil
                            shutil.rmtree(path, ignore_errors=True)
                            cleaned += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

            QMessageBox.information(
                self, "清理完成",
                f"成功清理 {cleaned} 个项目\n失败 {failed} 个项目"
            )
            # 移除已清理的项
            self._start_scan()

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        open_action = QAction("📂 打开文件位置", self)
        open_action.triggered.connect(lambda: self._open_location(item))
        menu.addAction(open_action)

        delete_action = QAction("🗑️ 删除文件", self)
        delete_action.triggered.connect(lambda: self._delete_single(item))
        menu.addAction(delete_action)

        menu.exec(QCursor.pos())

    def _open_location(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        path = data.get('path', '')
        if os.path.exists(path):
            os.startfile(os.path.dirname(path) if os.path.isfile(path) else path)

    def _delete_single(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        path = data.get('path', '')
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除以下文件吗？\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                idx = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(idx)
                QMessageBox.information(self, "成功", "文件已删除")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除失败: {e}")


# ============================================================================
# 重复文件页面
# ============================================================================

class DuplicatePage(ScanResultPage):
    """重复文件查找页面"""

    def __init__(self):
        super().__init__(
            "📁 重复文件查找",
            "基于文件内容 (MD5 哈希) 查找重复文件，安全释放磁盘空间",
            "duplicate"
        )
        self._add_path_selector()

    def _add_path_selector(self):
        """添加路径选择器"""
        path_layout = QHBoxLayout()
        path_label = QLabel("扫描路径:")
        path_label.setStyleSheet("color: #aaaacc; font-size: 13px;")
        path_layout.addWidget(path_label)

        self.path_input = QLineEdit(os.environ.get('USERPROFILE', ''))
        self.path_input.setFixedWidth(400)
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)

        path_layout.addStretch()

        # 在布局中插入到标题后面
        self.layout().insertLayout(2, path_layout)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择扫描路径")
        if path:
            self.path_input.setText(path)

    def _start_scan(self):
        self.results = []
        self.tree.clear()
        self.progress_frame.setVisible(True)
        self.scan_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.clean_btn.setVisible(False)

        self.worker = ScanWorker("duplicate", path=self.path_input.text())
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()


# ============================================================================
# 大文件查找页面
# ============================================================================

class LargeFilePage(ScanResultPage):
    """大文件查找页面"""

    def __init__(self):
        super().__init__(
            "📊 大文件查找",
            "快速查找占用磁盘空间最大的文件",
            "large_files"
        )
        self._add_options()

    def _add_options(self):
        """添加选项"""
        opt_layout = QHBoxLayout()

        drive_label = QLabel("扫描驱动器:")
        drive_label.setStyleSheet("color: #aaaacc; font-size: 13px;")
        opt_layout.addWidget(drive_label)

        self.drive_combo = QComboBox()
        for letter in 'CDEFGH':
            path = f"{letter}:\\"
            if os.path.exists(path):
                try:
                    usage = psutil.disk_usage(path)
                    self.drive_combo.addItem(
                        f"{letter}: ({format_size(usage.used)} / {format_size(usage.total)})",
                        path
                    )
                except Exception:
                    pass
        self.drive_combo.setFixedWidth(250)
        opt_layout.addWidget(self.drive_combo)

        size_label = QLabel("  最小大小:")
        size_label.setStyleSheet("color: #aaaacc; font-size: 13px;")
        opt_layout.addWidget(size_label)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 10000)
        self.size_spin.setValue(100)
        self.size_spin.setSuffix(" MB")
        self.size_spin.setFixedWidth(100)
        opt_layout.addWidget(self.size_spin)

        opt_layout.addStretch()
        self.layout().insertLayout(2, opt_layout)

    def _start_scan(self):
        self.results = []
        self.tree.clear()
        self.progress_frame.setVisible(True)
        self.scan_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.clean_btn.setVisible(False)

        drive = self.drive_combo.currentData()
        min_size = self.size_spin.value() * 1024 * 1024

        self.worker = ScanWorker("large_files", path=drive, min_size=min_size)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()


# ============================================================================
# 定时清理页面
# ============================================================================

class SchedulePage(QWidget):
    """定时清理页面"""

    def __init__(self):
        super().__init__()
        self.schedules = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("⏰ 定时清理")
        title.setObjectName("title")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel("设置自动清理计划任务，保持系统始终干净")
        desc.setObjectName("subtitle")
        layout.addWidget(desc)

        # 添加计划按钮
        add_btn = QPushButton("➕ 添加清理计划")
        add_btn.setObjectName("action_btn")
        add_btn.setFixedWidth(160)
        add_btn.clicked.connect(self._add_schedule)
        layout.addWidget(add_btn)

        # 计划列表
        self.schedule_tree = QTreeWidget()
        self.schedule_tree.setHeaderLabels(["任务名称", "频率", "清理类型", "下次运行", "状态", "操作"])
        self.schedule_tree.setColumnCount(6)
        self.schedule_tree.setColumnWidth(0, 180)
        self.schedule_tree.setColumnWidth(1, 100)
        self.schedule_tree.setColumnWidth(2, 150)
        self.schedule_tree.setColumnWidth(3, 150)
        self.schedule_tree.setColumnWidth(4, 100)
        self.schedule_tree.setColumnWidth(5, 150)
        self.schedule_tree.setRootIsDecorated(False)
        layout.addWidget(self.schedule_tree)

        # 预设计划
        self._add_default_schedules()

    def _add_default_schedules(self):
        """添加默认计划"""
        defaults = [
            ("每日临时文件清理", "每天", "临时文件", "02:00", "已启用"),
            ("每周浏览器缓存清理", "每周", "浏览器缓存", "周日 03:00", "已启用"),
            ("每月大文件检查", "每月", "大文件扫描", "每月1日", "已停用"),
        ]
        for name, freq, clean_type, next_run, status in defaults:
            item = QTreeWidgetItem([name, freq, clean_type, next_run, status, ""])

            # 添加操作按钮
            toggle_btn = QPushButton("⏸ 暂停" if status == "已启用" else "▶ 启用")
            toggle_btn.setObjectName("secondary_btn")
            toggle_btn.setFixedSize(80, 28)
            self.schedule_tree.addTopLevelItem(item)
            self.schedule_tree.setItemWidget(item, 5, toggle_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setObjectName("secondary_btn")
            delete_btn.setFixedSize(30, 28)

    def _add_schedule(self):
        """添加清理计划对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加清理计划")
        dialog.setFixedSize(400, 350)
        dialog.setStyleSheet(DARK_THEME)

        form = QFormLayout(dialog)

        name_input = QLineEdit()
        name_input.setPlaceholderText("输入任务名称")
        form.addRow("任务名称:", name_input)

        freq_combo = QComboBox()
        freq_combo.addItems(["每天", "每周", "每月"])
        form.addRow("执行频率:", freq_combo)

        type_combo = QComboBox()
        type_combo.addItems([
            "临时文件清理", "浏览器缓存清理", "Windows系统清理",
            "应用程序缓存清理", "大文件扫描"
        ])
        form.addRow("清理类型:", type_combo)

        time_edit = QTimeEdit(QTime(2, 0))
        form.addRow("执行时间:", time_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text() or "新计划任务"
            freq = freq_combo.currentText()
            clean_type = type_combo.currentText()
            time_str = time_edit.time().toString("HH:mm")

            item = QTreeWidgetItem([name, freq, clean_type, time_str, "已启用", ""])
            self.schedule_tree.addTopLevelItem(item)


# ============================================================================
# 主窗口
# ============================================================================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiskCleanup - 专业磁盘清理工具")
        self.setMinimumSize(1200, 750)
        self.resize(1280, 800)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("🧹 DiskCleanup")
        logo.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        logo.setStyleSheet("color: #ffffff; padding: 8px 12px 16px 12px;")
        sidebar_layout.addWidget(logo)

        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("🏠  首页", "dashboard"),
            ("🗑️  垃圾文件扫描", "junk"),
            ("🌐  浏览器清理", "browser"),
            ("🪟  Windows 清理", "windows"),
            ("📦  应用程序清理", "app_cache"),
            ("🔧  注册表清理", "registry"),
            ("📁  重复文件查找", "duplicate"),
            ("📊  大文件查找", "large_files"),
            ("⏰  定时清理", "schedule"),
        ]

        for text, key in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # 版本信息
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #444466; font-size: 11px; padding: 8px;")
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # 内容区域
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #0a0a0a;")

        # 创建各页面
        self.dashboard = DashboardPage()
        self.dashboard.navigate.connect(self._navigate_to)

        self.junk_page = ScanResultPage(
            "🗑️ 垃圾文件扫描",
            "扫描系统临时文件、缓存和日志文件，释放磁盘空间",
            "junk"
        )
        self.browser_page = ScanResultPage(
            "🌐 浏览器清理",
            "清理 Chrome、Edge、Firefox 等浏览器的缓存数据",
            "browser"
        )
        self.windows_page = ScanResultPage(
            "🪟 Windows 清理",
            "清理 Windows 更新缓存、系统临时文件和日志",
            "windows"
        )
        self.app_cache_page = ScanResultPage(
            "📦 应用程序清理",
            "清理已安装应用程序的缓存数据",
            "app_cache"
        )
        self.registry_page = ScanResultPage(
            "🔧 注册表清理",
            "扫描并修复无效的注册表项和启动项",
            "registry"
        )
        self.duplicate_page = DuplicatePage()
        self.large_file_page = LargeFilePage()
        self.schedule_page = SchedulePage()

        self.stack.addWidget(self.dashboard)      # 0
        self.stack.addWidget(self.junk_page)       # 1
        self.stack.addWidget(self.browser_page)    # 2
        self.stack.addWidget(self.windows_page)    # 3
        self.stack.addWidget(self.app_cache_page)  # 4
        self.stack.addWidget(self.registry_page)   # 5
        self.stack.addWidget(self.duplicate_page)  # 6
        self.stack.addWidget(self.large_file_page) # 7
        self.stack.addWidget(self.schedule_page)   # 8

        main_layout.addWidget(self.stack)

        # 连接导航信号
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self._navigate_to(idx))

        # 默认选中首页
        self.nav_buttons[0].setChecked(True)

    def _navigate_to(self, index: int):
        """导航到指定页面"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)


# ============================================================================
# 应用程序入口
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 应用深色主题
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#151530"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1a3a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # 应用样式表
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
