#!/usr/bin/env python3
"""
专业多线程下载管理器
Professional Multi-threaded Download Manager
"""

import sys
import os
import json
import time
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, unquote

import requests
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QMimeData, QMutex, QMutexLocker, QSettings
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter,
    QBrush, QPen, QPixmap, QClipboard, QAction, QShortcut, QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFrame, QScrollArea, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QSplitter, QMenu,
    QSystemTrayIcon, QFileDialog, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QToolButton, QSizePolicy,
    QStyledItemDelegate, QStyle, QStyleOptionProgressBar, QAbstractItemView
)


# ─── 数据模型 ────────────────────────────────────────────────────────────────

class DownloadStatus(Enum):
    PENDING = "等待中"
    DOWNLOADING = "下载中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    FAILED = "失败"
    CANCELLED = "已取消"


@dataclass
class DownloadTask:
    url: str
    filename: str = ""
    save_dir: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    total_size: int = 0
    downloaded_size: int = 0
    speed: float = 0.0
    progress: float = 0.0
    eta: str = ""
    threads: int = 8
    speed_limit: float = 0.0  # KB/s, 0 = unlimited
    error_msg: str = ""
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""
    completed_at: str = ""
    etag: str = ""
    accept_ranges: bool = False
    headers: dict = field(default_factory=dict)
    _chunks: list = field(default_factory=list, repr=False)
    _cancelled: bool = False
    _paused: bool = False

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.filename:
            parsed = urlparse(self.url)
            self.filename = unquote(parsed.path.split("/")[-1]) or "download"
        if not self.save_dir:
            self.save_dir = str(Path.home() / "Downloads")

    @property
    def full_path(self) -> str:
        return os.path.join(self.save_dir, self.filename)

    @property
    def progress_percent(self) -> int:
        return int(self.progress * 100)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "filename": self.filename,
            "save_dir": self.save_dir,
            "status": self.status.value,
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error_msg": self.error_msg,
            "retry_count": self.retry_count,
        }


# ─── 下载工作线程 ────────────────────────────────────────────────────────────

class DownloadWorker(QThread):
    progress_update = pyqtSignal(object)
    chunk_progress = pyqtSignal(int, int)  # chunk_id, bytes_downloaded
    speed_update = pyqtSignal(float)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, task: DownloadTask, parent=None):
        super().__init__(parent)
        self.task = task
        self._mutex = QMutex()
        self._stop = False
        self._pause = False
        self._chunk_workers: List['ChunkWorker'] = []

    def run(self):
        try:
            self.task.status = DownloadStatus.DOWNLOADING
            self.progress_update.emit(self.task)
            self._download()
        except Exception as e:
            if not self._stop:
                self.task.status = DownloadStatus.FAILED
                self.task.error_msg = str(e)
                self.finished_signal.emit(self.task)

    def _download(self):
        task = self.task
        url = task.url
        headers = task.headers.copy()
        headers.setdefault("User-Agent", "DownloadManager/1.0")

        # Check if range requests are supported
        try:
            resp = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
            total_size = int(resp.headers.get("content-length", 0))
            accept_ranges = resp.headers.get("accept-ranges", "").lower() == "bytes"
            content_type = resp.headers.get("content-type", "")
        except Exception:
            resp = requests.get(url, headers=headers, timeout=15, stream=True, allow_redirects=True)
            total_size = int(resp.headers.get("content-length", 0))
            accept_ranges = False
            content_type = resp.headers.get("content-type", "")

        task.total_size = total_size
        task.accept_ranges = accept_ranges

        # Get final filename from Content-Disposition if available
        cd = resp.headers.get("content-disposition", "")
        if cd and "filename" in cd:
            match = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\';\r\n]+)', cd, re.IGNORECASE)
            if match:
                task.filename = unquote(match.group(1).strip())

        # Ensure save directory exists
        os.makedirs(task.save_dir, exist_ok=True)

        # Handle duplicate filenames
        base, ext = os.path.splitext(task.full_path)
        counter = 1
        final_path = task.full_path
        while os.path.exists(final_path):
            final_path = f"{base} ({counter}){ext}"
            counter += 1
        task.filename = os.path.basename(final_path)

        if total_size > 0 and accept_ranges and task.threads > 1:
            self._multi_thread_download(url, headers, total_size, final_path)
        else:
            self._single_thread_download(url, headers, final_path)

    def _multi_thread_download(self, url, headers, total_size, final_path):
        task = self.task
        chunk_size = total_size // task.threads
        chunks = []

        for i in range(task.threads):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < task.threads - 1 else total_size - 1
            chunks.append((start, end))

        # Download chunks
        chunk_files = []
        chunk_progress = [0] * task.threads
        total_downloaded = 0
        start_time = time.time()
        last_speed_check = start_time
        last_bytes = 0

        workers = []
        for i, (start, end) in enumerate(chunks):
            chunk_path = f"{final_path}.part{i}"
            chunk_files.append(chunk_path)
            worker = ChunkWorker(url, headers, start, end, chunk_path, task.speed_limit / task.threads)
            workers.append(worker)
            self._chunk_workers.append(worker)

        # Start all workers
        for w in workers:
            w.start()

        # Monitor progress
        while not self._stop:
            if self._pause:
                for w in workers:
                    w.pause()
                while self._pause and not self._stop:
                    self.msleep(200)
                if self._stop:
                    break
                for w in workers:
                    w.resume()

            all_done = True
            total_downloaded = 0
            for i, w in enumerate(workers):
                if w.isFinished():
                    total_downloaded += chunks[i][1] - chunks[i][0] + 1
                    if w.error:
                        self._stop_all_workers(workers)
                        raise Exception(w.error)
                else:
                    all_done = False
                    total_downloaded += w.downloaded

            now = time.time()
            elapsed = now - last_speed_check
            if elapsed >= 0.5:
                speed = (total_downloaded - last_bytes) / elapsed
                last_speed_check = now
                last_bytes = total_downloaded
                task.speed = speed
                self.speed_update.emit(speed)

            task.downloaded_size = total_downloaded
            task.progress = total_downloaded / total_size if total_size > 0 else 0

            if total_downloaded > 0 and task.speed > 0:
                remaining = total_size - total_downloaded
                eta_seconds = remaining / task.speed
                task.eta = str(timedelta(seconds=int(eta_seconds)))

            self.progress_update.emit(task)

            if all_done:
                break

            self.msleep(100)

        if self._stop:
            self._stop_all_workers(workers)
            # Clean up partial files
            for f in chunk_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except OSError:
                        pass
            if self.task.status != DownloadStatus.CANCELLED:
                self.task.status = DownloadStatus.FAILED
                self.task.error_msg = "下载已取消"
            self.finished_signal.emit(self.task)
            return

        # Merge chunks
        with open(final_path, "wb") as outfile:
            for chunk_path in chunk_files:
                with open(chunk_path, "rb") as infile:
                    while True:
                        data = infile.read(1024 * 1024)
                        if not data:
                            break
                        outfile.write(data)
                os.remove(chunk_path)

        task.status = DownloadStatus.COMPLETED
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.progress = 1.0
        task.downloaded_size = total_size
        self.finished_signal.emit(task)

    def _single_thread_download(self, url, headers, final_path):
        task = self.task
        resp = requests.get(url, headers=headers, stream=True, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0))
        task.total_size = total_size

        downloaded = 0
        start_time = time.time()
        last_speed_check = start_time
        last_bytes = 0

        with open(final_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if self._stop:
                    resp.close()
                    if os.path.exists(final_path):
                        try:
                            os.remove(final_path)
                        except OSError:
                            pass
                    self.task.status = DownloadStatus.CANCELLED if self.task._cancelled else DownloadStatus.FAILED
                    self.finished_signal.emit(self.task)
                    return

                while self._pause:
                    self.msleep(200)
                    if self._stop:
                        break

                if not chunk:
                    continue

                # Speed limiting
                if task.speed_limit > 0:
                    elapsed = time.time() - start_time
                    expected = task.speed_limit * 1024 * elapsed
                    if downloaded > expected:
                        self.msleep(50)

                f.write(chunk)
                downloaded += len(chunk)

                now = time.time()
                elapsed = now - last_speed_check
                if elapsed >= 0.5:
                    speed = (downloaded - last_bytes) / elapsed
                    last_speed_check = now
                    last_bytes = downloaded
                    task.speed = speed
                    self.speed_update.emit(speed)

                task.downloaded_size = downloaded
                task.progress = downloaded / total_size if total_size > 0 else 0

                if downloaded > 0 and task.speed > 0:
                    remaining = total_size - downloaded
                    eta_seconds = remaining / task.speed
                    task.eta = str(timedelta(seconds=int(eta_seconds)))

                self.progress_update.emit(task)

        task.status = DownloadStatus.COMPLETED
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.progress = 1.0
        self.finished_signal.emit(task)

    def _stop_all_workers(self, workers):
        for w in workers:
            w.stop()
        for w in workers:
            w.wait(3000)

    def pause(self):
        self._pause = True
        self.task.status = DownloadStatus.PAUSED
        self.task._paused = True
        self.progress_update.emit(self.task)

    def resume(self):
        self._pause = False
        self.task.status = DownloadStatus.DOWNLOADING
        self.task._paused = False
        self.progress_update.emit(self.task)

    def cancel(self):
        self._stop = True
        self.task._cancelled = True
        self.task.status = DownloadStatus.CANCELLED
        for w in self._chunk_workers:
            w.stop()


class ChunkWorker(QThread):
    def __init__(self, url, headers, start, end, save_path, speed_limit=0):
        super().__init__()
        self.url = url
        self.headers = headers.copy()
        self.headers["Range"] = f"bytes={start}-{end}"
        self.start = start
        self.end = end
        self.save_path = save_path
        self.speed_limit = speed_limit
        self.downloaded = 0
        self.error = ""
        self._stop = False
        self._pause = False

    def run(self):
        try:
            resp = requests.get(
                self.url, headers=self.headers, stream=True, timeout=30, allow_redirects=True
            )
            resp.raise_for_status()

            with open(self.save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if self._stop:
                        resp.close()
                        return

                    while self._pause:
                        self.msleep(200)
                        if self._stop:
                            return

                    if not chunk:
                        continue

                    if self.speed_limit > 0:
                        expected = self.speed_limit * 1024 * (time.time() - self._start_time)
                        if self.downloaded > expected:
                            self.msleep(50)

                    f.write(chunk)
                    self.downloaded += len(chunk)
        except Exception as e:
            if not self._stop:
                self.error = str(e)

    def stop(self):
        self._stop = True

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False


# ─── 历史记录管理 ────────────────────────────────────────────────────────────

class HistoryManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.records: List[dict] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.records = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def add(self, task: DownloadTask):
        record = task.to_dict()
        self.records.insert(0, record)
        if len(self.records) > 500:
            self.records = self.records[:500]
        self._save()

    def search(self, keyword: str) -> List[dict]:
        if not keyword:
            return self.records
        keyword_lower = keyword.lower()
        return [
            r for r in self.records
            if keyword_lower in r.get("filename", "").lower()
            or keyword_lower in r.get("url", "").lower()
        ]

    def clear(self):
        self.records.clear()
        self._save()


# ─── 自定义样式 ──────────────────────────────────────────────────────────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #222244;
    background: #0a0a0a;
    border-radius: 8px;
}

QTabBar::tab {
    background: #111122;
    color: #888;
    padding: 10px 24px;
    margin: 0 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    min-width: 80px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover:!selected {
    background: #1a1a33;
    color: #ccc;
}

QFrame#card {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 12px;
    padding: 16px;
}

QLabel {
    color: #e0e0e0;
}

QLabel#title {
    font-size: 28px;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

QLabel#subtitle {
    color: #666;
    font-size: 13px;
}

QLabel#section-title {
    font-size: 16px;
    font-weight: bold;
    color: #b0b0d0;
    padding: 4px 0;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b91ee, stop:1 #8b5fb5);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5567cc, stop:1 #5f3d8a);
}

QPushButton:disabled {
    background: #333;
    color: #666;
}

QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff4444, stop:1 #cc2266);
}

QPushButton#danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6666, stop:1 #dd3377);
}

QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #44bb88, stop:1 #22aa66);
}

QPushButton#success:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #55cc99, stop:1 #33bb77);
}

QPushButton#secondary {
    background: #222244;
    color: #b0b0d0;
}

QPushButton#secondary:hover {
    background: #2a2a55;
}

QPushButton#icon-btn {
    background: transparent;
    padding: 8px;
    font-size: 18px;
    min-width: 36px;
    min-height: 36px;
}

QPushButton#icon-btn:hover {
    background: #222244;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0d0d1a;
    border: 1px solid #333355;
    color: #e0e0e0;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    selection-background-color: #667eea;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}

QComboBox QAbstractItemView {
    background: #111122;
    border: 1px solid #333355;
    color: #e0e0e0;
    selection-background-color: #667eea;
}

QTableWidget {
    background: #0a0a0a;
    alternate-background-color: #0f0f1a;
    gridline-color: #1a1a33;
    border: none;
    border-radius: 8px;
    font-size: 12px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #1a1a33;
}

QTableWidget::item:selected {
    background: #222255;
    color: white;
}

QHeaderView::section {
    background: #111122;
    color: #888;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #222244;
    font-weight: bold;
    font-size: 12px;
}

QProgressBar {
    background: #0d0d1a;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}

QScrollBar:vertical {
    background: #0a0a0a;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #333355;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #444477;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0a0a0a;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #333355;
    border-radius: 4px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background: #444477;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    border: 1px solid #222244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    color: #b0b0d0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}

QTextEdit {
    background: #0d0d1a;
    border: 1px solid #333355;
    color: #e0e0e0;
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
}

QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #333355;
    background: #0d0d1a;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border: none;
}

QSplitter::handle {
    background: #222244;
    width: 2px;
}

QToolTip {
    background: #1a1a33;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QMenu {
    background: #111122;
    border: 1px solid #333355;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: #222255;
}
"""


# ─── 主窗口 ──────────────────────────────────────────────────────────────────

class DownloadManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("专业下载管理器 - DownloadManager")
        self.setMinimumSize(1100, 720)
        self.resize(1200, 780)

        self._tasks: Dict[str, DownloadTask] = {}
        self._workers: Dict[str, DownloadWorker] = {}
        self._clipboard_text = ""
        self._max_concurrent = 3

        config_dir = os.path.join(str(Path.home()), ".download_manager")
        os.makedirs(config_dir, exist_ok=True)
        self._history = HistoryManager(os.path.join(config_dir, "history.json"))
        self._settings = QSettings("HermesAgent", "DownloadManager")

        self._setup_ui()
        self._setup_clipboard_timer()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("⬇ 专业下载管理器")
        title.setObjectName("title")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        self._speed_label = QLabel("▼ 0 B/s")
        self._speed_label.setStyleSheet("font-size: 15px; color: #667eea; font-weight: bold;")
        header.addWidget(self._speed_label)

        self._count_label = QLabel("0 个下载")
        self._count_label.setStyleSheet("font-size: 13px; color: #666;")
        self._count_label.setContentsMargins(16, 0, 0, 0)
        header.addWidget(self._count_label)

        layout.addLayout(header)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_download_tab(), "📥 下载任务")
        self._tabs.addTab(self._create_batch_tab(), "📋 批量下载")
        self._tabs.addTab(self._create_history_tab(), "📜 历史记录")
        self._tabs.addTab(self._create_settings_tab(), "⚙ 设置")
        layout.addWidget(self._tabs)

        # Status bar
        self.statusBar().setStyleSheet(
            "background: #111122; color: #666; border-top: 1px solid #222244; padding: 4px 16px; font-size: 12px;"
        )
        self.statusBar().showMessage("就绪 — 粘贴下载链接或拖拽文件开始下载")

    def _create_download_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # URL input
        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(10)

        url_row = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("输入下载链接 (支持 http/https)...")
        self._url_input.returnPressed.connect(self._add_download)
        url_row.addWidget(self._url_input, 1)

        self._add_btn = QPushButton("➕ 添加下载")
        self._add_btn.setFixedWidth(130)
        self._add_btn.clicked.connect(self._add_download)
        url_row.addWidget(self._add_btn)

        input_layout.addLayout(url_row)

        # Options row
        opts = QHBoxLayout()
        opts.addWidget(QLabel("线程数:"))
        self._threads_spin = QSpinBox()
        self._threads_spin.setRange(1, 32)
        self._threads_spin.setValue(8)
        self._threads_spin.setFixedWidth(80)
        opts.addWidget(self._threads_spin)

        opts.addSpacing(16)
        opts.addWidget(QLabel("限速 (KB/s):"))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(0, 999999)
        self._limit_spin.setValue(0)
        self._limit_spin.setSpecialValueText("无限制")
        self._limit_spin.setFixedWidth(120)
        opts.addWidget(self._limit_spin)

        opts.addSpacing(16)
        opts.addWidget(QLabel("保存到:"))
        self._save_dir_input = QLineEdit()
        self._save_dir_input.setText(str(Path.home() / "Downloads"))
        self._save_dir_input.setPlaceholderText("保存目录...")
        opts.addWidget(self._save_dir_input, 1)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        browse_btn.setToolTip("选择保存目录")
        browse_btn.clicked.connect(self._browse_save_dir)
        opts.addWidget(browse_btn)

        input_layout.addLayout(opts)
        layout.addWidget(input_card)

        # Download table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("下载队列"))

        toolbar.addStretch()

        self._pause_all_btn = QPushButton("⏸ 全部暂停")
        self._pause_all_btn.setObjectName("secondary")
        self._pause_all_btn.clicked.connect(self._pause_all)
        toolbar.addWidget(self._pause_all_btn)

        self._resume_all_btn = QPushButton("▶ 全部继续")
        self._resume_all_btn.setObjectName("success")
        self._resume_all_btn.clicked.connect(self._resume_all)
        toolbar.addWidget(self._resume_all_btn)

        self._clear_btn = QPushButton("🗑 清除已完成")
        self._clear_btn.setObjectName("danger")
        self._clear_btn.clicked.connect(self._clear_completed)
        toolbar.addWidget(self._clear_btn)

        table_layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(["文件名", "大小", "进度", "速度", "剩余时间", "状态", "操作"])
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 200)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 80)
        self._table.setColumnWidth(6, 200)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_table_context_menu)
        table_layout.addWidget(self._table)

        layout.addWidget(table_card)
        return widget

    def _create_batch_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        card_layout.addWidget(QLabel("📋 批量下载"))
        desc = QLabel("每行输入一个URL，点击按钮批量添加到下载队列")
        desc.setObjectName("subtitle")
        card_layout.addWidget(desc)

        self._batch_input = QTextEdit()
        self._batch_input.setPlaceholderText(
            "https://example.com/file1.zip\nhttps://example.com/file2.zip\nhttps://example.com/file3.zip"
        )
        self._batch_input.setMinimumHeight(200)
        card_layout.addWidget(self._batch_input)

        opts = QHBoxLayout()
        opts.addWidget(QLabel("线程数:"))
        batch_threads = QSpinBox()
        batch_threads.setRange(1, 32)
        batch_threads.setValue(8)
        batch_threads.setFixedWidth(80)
        self._batch_threads_spin = batch_threads
        opts.addWidget(batch_threads)

        opts.addSpacing(16)
        opts.addWidget(QLabel("限速 (KB/s):"))
        batch_limit = QSpinBox()
        batch_limit.setRange(0, 999999)
        batch_limit.setValue(0)
        batch_limit.setSpecialValueText("无限制")
        batch_limit.setFixedWidth(120)
        self._batch_limit_spin = batch_limit
        opts.addWidget(batch_limit)

        opts.addStretch()

        add_batch_btn = QPushButton("➕ 批量添加")
        add_batch_btn.clicked.connect(self._add_batch_downloads)
        opts.addWidget(add_batch_btn)

        card_layout.addLayout(opts)

        paste_btn = QPushButton("📋 从剪贴板粘贴")
        paste_btn.setObjectName("secondary")
        paste_btn.setFixedWidth(160)
        paste_btn.clicked.connect(self._paste_clipboard)
        card_layout.addWidget(paste_btn)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        # Search
        search_row = QHBoxLayout()
        self._history_search = QLineEdit()
        self._history_search.setPlaceholderText("🔍 搜索下载历史...")
        self._history_search.textChanged.connect(self._search_history)
        search_row.addWidget(self._history_search, 1)

        clear_history_btn = QPushButton("🗑 清空历史")
        clear_history_btn.setObjectName("danger")
        clear_history_btn.setFixedWidth(120)
        clear_history_btn.clicked.connect(self._clear_history)
        search_row.addWidget(clear_history_btn)

        card_layout.addLayout(search_row)

        # History table
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(["文件名", "大小", "状态", "下载时间", "链接"])
        self._history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setAlternatingRowColors(True)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setShowGrid(False)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.setColumnWidth(1, 100)
        self._history_table.setColumnWidth(2, 80)
        self._history_table.setColumnWidth(3, 160)
        card_layout.addWidget(self._history_table)

        self._history_count_label = QLabel("共 0 条记录")
        self._history_count_label.setObjectName("subtitle")
        card_layout.addWidget(self._history_count_label)

        layout.addWidget(card)
        return widget

    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # General settings
        general = QFrame()
        general.setObjectName("card")
        gen_layout = QVBoxLayout(general)
        gen_layout.setSpacing(12)

        gen_layout.addWidget(QLabel("⚙ 通用设置"))

        form = QGridLayout()
        form.setSpacing(10)

        form.addWidget(QLabel("最大并发下载数:"), 0, 0)
        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 20)
        self._concurrent_spin.setValue(self._max_concurrent)
        self._concurrent_spin.setFixedWidth(100)
        self._concurrent_spin.valueChanged.connect(self._update_concurrent)
        form.addWidget(self._concurrent_spin, 0, 1)

        form.addWidget(QLabel("默认线程数:"), 1, 0)
        self._default_threads_spin = QSpinBox()
        self._default_threads_spin.setRange(1, 32)
        self._default_threads_spin.setValue(8)
        self._default_threads_spin.setFixedWidth(100)
        form.addWidget(self._default_threads_spin, 1, 1)

        form.addWidget(QLabel("默认保存目录:"), 2, 0)
        dir_row = QHBoxLayout()
        self._default_dir_input = QLineEdit()
        self._default_dir_input.setText(str(Path.home() / "Downloads"))
        dir_row.addWidget(self._default_dir_input, 1)
        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._browse_default_dir)
        dir_row.addWidget(browse_btn)
        form.addLayout(dir_row, 2, 1)

        self._clipboard_check = QCheckBox("监控剪贴板，自动检测下载链接")
        self._clipboard_check.setChecked(True)
        form.addWidget(self._clipboard_check, 3, 0, 1, 2)

        self._auto_retry_check = QCheckBox("失败后自动重试（最多3次）")
        self._auto_retry_check.setChecked(True)
        form.addWidget(self._auto_retry_check, 4, 0, 1, 2)

        gen_layout.addLayout(form)
        layout.addWidget(general)

        # User-Agent
        ua_card = QFrame()
        ua_card.setObjectName("card")
        ua_layout = QVBoxLayout(ua_card)
        ua_layout.addWidget(QLabel("🌐 HTTP 设置"))

        ua_form = QFormLayout()
        self._ua_input = QLineEdit()
        self._ua_input.setText("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        ua_form.addRow("User-Agent:", self._ua_input)
        ua_layout.addLayout(ua_form)

        layout.addWidget(ua_card)
        layout.addStretch()
        return widget

    # ─── 剪贴板监控 ───────────────────────────────────────────────────────

    def _setup_clipboard_timer(self):
        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.timeout.connect(self._check_clipboard)
        self._clipboard_timer.start(2000)

    def _check_clipboard(self):
        if not self._clipboard_check.isChecked():
            return
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text and text != self._clipboard_text:
            self._clipboard_text = text
            if self._is_download_url(text):
                self.statusBar().showMessage(f"🔗 检测到下载链接: {text[:80]}...")
                self._url_input.setText(text)

    def _is_download_url(self, text: str) -> bool:
        if not text.startswith(("http://", "https://")):
            return False
        download_exts = {
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
            ".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage",
            ".iso", ".img", ".bin",
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
            ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
            ".apk", ".ipa", ".pkg",
        }
        parsed = urlparse(text)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in download_exts)

    # ─── 下载操作 ─────────────────────────────────────────────────────────

    def _add_download(self):
        url = self._url_input.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "错误", "请输入有效的HTTP/HTTPS链接")
            return

        task = DownloadTask(
            url=url,
            save_dir=self._save_dir_input.text() or str(Path.home() / "Downloads"),
            threads=self._threads_spin.value(),
            speed_limit=float(self._limit_spin.value()),
        )
        task.headers = {"User-Agent": self._ua_input.text()}

        self._tasks[task.url] = task
        self._url_input.clear()
        self._start_download(task)

    def _add_batch_downloads(self):
        text = self._batch_input.toPlainText().strip()
        if not text:
            return
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        count = 0
        for url in lines:
            if not url.startswith(("http://", "https://")):
                continue
            if url in self._tasks:
                continue
            task = DownloadTask(
                url=url,
                save_dir=self._save_dir_input.text() or str(Path.home() / "Downloads"),
                threads=self._batch_threads_spin.value(),
                speed_limit=float(self._batch_limit_spin.value()),
            )
            task.headers = {"User-Agent": self._ua_input.text()}
            self._tasks[task.url] = task
            self._start_download(task)
            count += 1

        self._batch_input.clear()
        self.statusBar().showMessage(f"已添加 {count} 个下载任务")
        self._tabs.setCurrentIndex(0)

    def _paste_clipboard(self):
        clipboard = QApplication.clipboard()
        self._batch_input.setPlainText(clipboard.text())

    def _start_download(self, task: DownloadTask):
        # Check concurrent limit
        active = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.DOWNLOADING)
        if active >= self._max_concurrent:
            task.status = DownloadStatus.PENDING
            self._update_table()
            return

        worker = DownloadWorker(task)
        worker.progress_update.connect(self._on_progress_update)
        worker.speed_update.connect(self._on_speed_update)
        worker.finished_signal.connect(self._on_download_finished)
        self._workers[task.url] = worker
        worker.start()
        self._update_table()

    def _pause_download(self, url: str):
        if url in self._workers:
            self._workers[url].pause()

    def _resume_download(self, url: str):
        if url in self._workers:
            self._workers[url].resume()

    def _cancel_download(self, url: str):
        if url in self._workers:
            self._workers[url].cancel()
            self._workers[url].wait(2000)
            del self._workers[url]
        if url in self._tasks:
            self._tasks[url].status = DownloadStatus.CANCELLED
        self._update_table()

    def _retry_download(self, url: str):
        if url in self._tasks:
            task = self._tasks[url]
            if task.retry_count >= task.max_retries:
                QMessageBox.information(self, "提示", "已达最大重试次数")
                return
            task.retry_count += 1
            task.status = DownloadStatus.PENDING
            task.downloaded_size = 0
            task.progress = 0
            task.error_msg = ""
            self._start_download(task)

    def _pause_all(self):
        for url in list(self._workers.keys()):
            self._pause_download(url)

    def _resume_all(self):
        for url in list(self._workers.keys()):
            self._resume_download(url)

    def _clear_completed(self):
        to_remove = [url for url, t in self._tasks.items()
                     if t.status in (DownloadStatus.COMPLETED, DownloadStatus.CANCELLED, DownloadStatus.FAILED)]
        for url in to_remove:
            if url in self._workers:
                del self._workers[url]
            del self._tasks[url]
        self._update_table()

    def _browse_save_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择保存目录", self._save_dir_input.text())
        if d:
            self._save_dir_input.setText(d)

    def _browse_default_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择默认保存目录", self._default_dir_input.text())
        if d:
            self._default_dir_input.setText(d)

    def _update_concurrent(self, value: int):
        self._max_concurrent = value

    # ─── 信号处理 ─────────────────────────────────────────────────────────

    def _on_progress_update(self, task: DownloadTask):
        self._update_table()

    def _on_speed_update(self, speed: float):
        self._speed_label.setText(f"▼ {self._format_speed(speed)}")

    def _on_download_finished(self, task: DownloadTask):
        if task.status == DownloadStatus.COMPLETED:
            self._history.add(task)
            self.statusBar().showMessage(f"✅ 下载完成: {task.filename}")
        elif task.status == DownloadStatus.FAILED:
            if self._auto_retry_check.isChecked() and task.retry_count < task.max_retries:
                self._retry_download(task.url)
                return
            self._history.add(task)
            self.statusBar().showMessage(f"❌ 下载失败: {task.filename} — {task.error_msg}")

        if task.url in self._workers:
            del self._workers[task.url]

        self._update_table()
        self._start_pending_downloads()

    def _start_pending_downloads(self):
        active = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.DOWNLOADING)
        pending = [t for t in self._tasks.values() if t.status == DownloadStatus.PENDING]
        for task in pending[:self._max_concurrent - active]:
            self._start_download(task)

    # ─── 表格更新 ─────────────────────────────────────────────────────────

    def _update_table(self):
        tasks = list(self._tasks.values())
        self._table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Filename
            name_item = QTableWidgetItem(task.filename)
            name_item.setToolTip(task.url)
            self._table.setItem(row, 0, name_item)

            # Size
            size_text = f"{self._format_size(task.downloaded_size)} / {self._format_size(task.total_size)}" if task.total_size > 0 else self._format_size(task.downloaded_size)
            self._table.setItem(row, 1, QTableWidgetItem(size_text))

            # Progress bar
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(4, 2, 4, 2)
            progress_bar = QProgressBar()
            progress_bar.setValue(int(task.progress * 100))
            progress_bar.setFormat(f"{task.progress * 100:.1f}%")
            progress_bar.setTextVisible(True)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #0d0d1a;
                    border: none;
                    border-radius: 5px;
                    height: 16px;
                    text-align: center;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 5px;
                }
            """)
            progress_layout.addWidget(progress_bar)
            self._table.setCellWidget(row, 2, progress_widget)

            # Speed
            speed_text = self._format_speed(task.speed) if task.status == DownloadStatus.DOWNLOADING else "—"
            self._table.setItem(row, 3, QTableWidgetItem(speed_text))

            # ETA
            self._table.setItem(row, 4, QTableWidgetItem(task.eta if task.status == DownloadStatus.DOWNLOADING else "—"))

            # Status
            status_item = QTableWidgetItem(task.status.value)
            status_colors = {
                DownloadStatus.PENDING: "#888",
                DownloadStatus.DOWNLOADING: "#667eea",
                DownloadStatus.PAUSED: "#e6a23c",
                DownloadStatus.COMPLETED: "#67c23a",
                DownloadStatus.FAILED: "#f56c6c",
                DownloadStatus.CANCELLED: "#909399",
            }
            status_item.setForeground(QColor(status_colors.get(task.status, "#888")))
            self._table.setItem(row, 5, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            if task.status == DownloadStatus.DOWNLOADING:
                pause_btn = QPushButton("⏸")
                pause_btn.setObjectName("icon-btn")
                pause_btn.setToolTip("暂停")
                pause_btn.setFixedSize(32, 32)
                pause_btn.clicked.connect(lambda _, u=task.url: self._pause_download(u))
                actions_layout.addWidget(pause_btn)

                cancel_btn = QPushButton("✖")
                cancel_btn.setObjectName("icon-btn")
                cancel_btn.setToolTip("取消")
                cancel_btn.setFixedSize(32, 32)
                cancel_btn.setStyleSheet("QPushButton:hover { background: #442222; }")
                cancel_btn.clicked.connect(lambda _, u=task.url: self._cancel_download(u))
                actions_layout.addWidget(cancel_btn)

            elif task.status == DownloadStatus.PAUSED:
                resume_btn = QPushButton("▶")
                resume_btn.setObjectName("icon-btn")
                resume_btn.setToolTip("继续")
                resume_btn.setFixedSize(32, 32)
                resume_btn.setStyleSheet("QPushButton:hover { background: #224422; }")
                resume_btn.clicked.connect(lambda _, u=task.url: self._resume_download(u))
                actions_layout.addWidget(resume_btn)

                cancel_btn = QPushButton("✖")
                cancel_btn.setObjectName("icon-btn")
                cancel_btn.setToolTip("取消")
                cancel_btn.setFixedSize(32, 32)
                cancel_btn.setStyleSheet("QPushButton:hover { background: #442222; }")
                cancel_btn.clicked.connect(lambda _, u=task.url: self._cancel_download(u))
                actions_layout.addWidget(cancel_btn)

            elif task.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                retry_btn = QPushButton("🔄")
                retry_btn.setObjectName("icon-btn")
                retry_btn.setToolTip("重试")
                retry_btn.setFixedSize(32, 32)
                retry_btn.setStyleSheet("QPushButton:hover { background: #223344; }")
                retry_btn.clicked.connect(lambda _, u=task.url: self._retry_download(u))
                actions_layout.addWidget(retry_btn)

            elif task.status == DownloadStatus.COMPLETED:
                open_btn = QPushButton("📂")
                open_btn.setObjectName("icon-btn")
                open_btn.setToolTip("打开文件")
                open_btn.setFixedSize(32, 32)
                open_btn.setStyleSheet("QPushButton:hover { background: #223344; }")
                open_btn.clicked.connect(lambda _, p=task.full_path: self._open_file(p))
                actions_layout.addWidget(open_btn)

                folder_btn = QPushButton("📁")
                folder_btn.setObjectName("icon-btn")
                folder_btn.setToolTip("打开文件夹")
                folder_btn.setFixedSize(32, 32)
                folder_btn.setStyleSheet("QPushButton:hover { background: #223344; }")
                folder_btn.clicked.connect(lambda _, p=task.save_dir: os.startfile(p))
                actions_layout.addWidget(folder_btn)

            actions_layout.addStretch()
            self._table.setCellWidget(row, 6, actions_widget)

        # Update count
        active = sum(1 for t in tasks if t.status == DownloadStatus.DOWNLOADING)
        total = len(tasks)
        self._count_label.setText(f"{active} 下载中 / {total} 总计")

    def _show_table_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        tasks = list(self._tasks.values())
        if row >= len(tasks):
            return
        task = tasks[row]

        menu = QMenu(self)
        if task.status == DownloadStatus.DOWNLOADING:
            menu.addAction("暂停", lambda: self._pause_download(task.url))
            menu.addAction("取消", lambda: self._cancel_download(task.url))
        elif task.status == DownloadStatus.PAUSED:
            menu.addAction("继续", lambda: self._resume_download(task.url))
            menu.addAction("取消", lambda: self._cancel_download(task.url))
        elif task.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            menu.addAction("重试", lambda: self._retry_download(task.url))
        elif task.status == DownloadStatus.COMPLETED:
            menu.addAction("打开文件", lambda: self._open_file(task.full_path))
            menu.addAction("打开文件夹", lambda: os.startfile(task.save_dir))

        menu.addSeparator()
        menu.addAction("复制链接", lambda: QApplication.clipboard().setText(task.url))
        menu.addAction("从列表移除", lambda: self._remove_task(task.url))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _remove_task(self, url: str):
        if url in self._workers:
            self._workers[url].cancel()
            self._workers[url].wait(1000)
            del self._workers[url]
        if url in self._tasks:
            del self._tasks[url]
        self._update_table()

    def _open_file(self, path: str):
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "错误", f"文件不存在: {path}")

    # ─── 历史记录 ─────────────────────────────────────────────────────────

    def _search_history(self, text: str):
        self._load_history_table(text)

    def _load_history_table(self, keyword: str = ""):
        records = self._history.search(keyword)
        self._history_table.setRowCount(len(records))

        for row, record in enumerate(records):
            self._history_table.setItem(row, 0, QTableWidgetItem(record.get("filename", "")))
            self._history_table.setItem(row, 1, QTableWidgetItem(self._format_size(record.get("total_size", 0))))
            self._history_table.setItem(row, 2, QTableWidgetItem(record.get("status", "")))
            self._history_table.setItem(row, 3, QTableWidgetItem(record.get("completed_at", record.get("created_at", ""))))
            url_item = QTableWidgetItem(record.get("url", ""))
            url_item.setToolTip(record.get("url", ""))
            self._history_table.setItem(row, 4, url_item)

        self._history_count_label.setText(f"共 {len(records)} 条记录")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有下载历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear()
            self._load_history_table()

    # ─── 工具方法 ─────────────────────────────────────────────────────────

    @staticmethod
    def _format_size(size: int) -> str:
        if size <= 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        s = float(size)
        while s >= 1024 and i < len(units) - 1:
            s /= 1024
            i += 1
        return f"{s:.1f} {units[i]}" if i > 0 else f"{int(s)} B"

    @staticmethod
    def _format_speed(speed: float) -> str:
        if speed <= 0:
            return "0 B/s"
        units = ["B/s", "KB/s", "MB/s", "GB/s"]
        i = 0
        while speed >= 1024 and i < len(units) - 1:
            speed /= 1024
            i += 1
        return f"{speed:.1f} {units[i]}" if i > 0 else f"{int(speed)} B/s"

    def closeEvent(self, event):
        # Stop all workers
        for worker in self._workers.values():
            worker.cancel()
            worker.wait(1000)
        event.accept()


# ─── 入口 ────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)

    window = DownloadManager()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
