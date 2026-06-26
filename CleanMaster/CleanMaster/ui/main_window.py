"""CleanMaster main window - Modern dark UI with Pro features."""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QProgressBar,
    QCheckBox, QSizePolicy, QSpacerItem, QTabWidget, QComboBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QMessageBox, QSplitter,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QSize, QPoint
)
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient

from CleanMaster.core.scanner import (
    Scanner, Cleaner, ScanReport, ScanResult, ScanProgress,
    LargeFileFinder, DuplicateFinder, StartupManager,
    DiskUsageAnalyzer, get_available_drives,
)


# ── Styling ──────────────────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
}
QLabel {
    background: transparent;
}
QPushButton {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2a2a4a;
    border-color: #4a4a8a;
}
QPushButton:pressed {
    background-color: #0f0f1f;
}
QPushButton#scanBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 14px 48px;
    font-size: 16px;
    border-radius: 12px;
}
QPushButton#scanBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8ff0, stop:1 #8b5fb8);
}
QPushButton#cleanBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f093fb, stop:1 #f5576c);
    color: white;
    border: none;
    padding: 14px 48px;
    font-size: 16px;
    border-radius: 12px;
}
QPushButton#cleanBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f5a8ff, stop:1 #f77085);
}
QPushButton#cleanBtn:disabled {
    background: #1a1a2e;
    color: #555;
}
QPushButton#proBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 28px;
    font-size: 14px;
    border-radius: 10px;
}
QPushButton#proBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8ff0, stop:1 #8b5fb8);
}
QPushButton#proBtn:disabled {
    background: #1a1a2e;
    color: #555;
}
QFrame#card {
    background-color: #111122;
    border: 1px solid #1a1a3a;
    border-radius: 12px;
    padding: 16px;
}
QFrame#card:hover {
    border-color: #2a2a5a;
}
QProgressBar {
    background-color: #111122;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #0a0a0a;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2a2a4a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #3a3a5a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0a0a0a;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2a2a4a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #3a3a5a;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QCheckBox {
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a5a;
    background: #111122;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    border-color: #667eea;
}
QTabWidget::pane {
    border: 1px solid #1a1a3a;
    border-radius: 8px;
    background: #0a0a0a;
}
QTabBar::tab {
    background-color: #111122;
    color: #888;
    border: 1px solid #1a1a3a;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    font-size: 13px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border-bottom: 2px solid #667eea;
}
QTabBar::tab:hover:!selected {
    background-color: #1a1a2e;
    color: #aaa;
}
QComboBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #4a4a8a;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #667eea;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    selection-background-color: #2a2a4a;
}
QTableWidget {
    background-color: #111122;
    alternate-background-color: #151530;
    border: 1px solid #1a1a3a;
    border-radius: 8px;
    gridline-color: #1a1a3a;
    font-size: 12px;
}
QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1a1a3a;
}
QTableWidget::item:selected {
    background-color: #2a2a5a;
}
QHeaderView::section {
    background-color: #1a1a2e;
    color: #888;
    border: none;
    border-bottom: 1px solid #2a2a4a;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}
QTreeWidget {
    background-color: #111122;
    alternate-background-color: #151530;
    border: 1px solid #1a1a3a;
    border-radius: 8px;
    font-size: 12px;
}
QTreeWidget::item {
    padding: 4px;
    border-bottom: 1px solid #1a1a3a;
}
QTreeWidget::item:selected {
    background-color: #2a2a5a;
}
QTreeWidget::item:hover {
    background-color: #1a1a3a;
}
QHeaderView::section:horizontal {
    background-color: #1a1a2e;
    color: #888;
    border: none;
    border-bottom: 1px solid #2a2a4a;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}
"""


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# ── Scan Worker Thread ──────────────────────────────────────────────────
class ScanWorker(QThread):
    progress = pyqtSignal(str, int)  # category, total_size
    finished = pyqtSignal(object)    # ScanReport

    def __init__(self):
        super().__init__()
        self.scanner = Scanner()

    def run(self):
        def on_progress(p: ScanProgress):
            self.progress.emit(p.current_category, p.total_size)
        report = self.scanner.full_scan(callback=on_progress)
        self.finished.emit(report)

    def stop(self):
        self.scanner.stop()


# ── Large File Finder Worker ────────────────────────────────────────────
class LargeFileWorker(QThread):
    progress = pyqtSignal(str, int)  # filepath, size
    finished = pyqtSignal(list)      # list of dicts

    def __init__(self, drive: str):
        super().__init__()
        self.drive = drive
        self.finder = LargeFileFinder()

    def run(self):
        def on_progress(path, size):
            self.progress.emit(path, size)
        results = self.finder.find_large_files(self.drive, top_n=20,
                                                callback=on_progress)
        self.finished.emit(results)

    def stop(self):
        self.finder.stop()


# ── Duplicate Finder Worker ─────────────────────────────────────────────
class DuplicateWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(dict)  # dict of hash -> list of dicts

    def __init__(self, drive: str):
        super().__init__()
        self.drive = drive
        self.finder = DuplicateFinder()

    def run(self):
        def on_progress(msg, count):
            self.progress.emit(msg, count)
        results = self.finder.find_duplicates(self.drive, callback=on_progress)
        self.finished.emit(results)

    def stop(self):
        self.finder.stop()


# ── Disk Usage Worker ────────────────────────────────────────────────────
class DiskUsageWorker(QThread):
    progress = pyqtSignal(str, int)  # path, size
    finished = pyqtSignal(list)      # list of dicts

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.analyzer = DiskUsageAnalyzer()

    def run(self):
        def on_progress(path, size):
            self.progress.emit(path, size)
        results = self.analyzer.analyze(self.path, depth=2, callback=on_progress)
        self.finished.emit(results)

    def stop(self):
        self.analyzer.stop()


# ── Category Card Widget ────────────────────────────────────────────────
class CategoryCard(QFrame):
    toggled = pyqtSignal()

    def __init__(self, category: str, size: int, safe: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.category = category
        self.size = size
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(safe)
        self.checkbox.stateChanged.connect(lambda: self.toggled.emit())
        layout.addWidget(self.checkbox)

        # Category icon (emoji)
        icons = {
            "临时文件": "🗑️",
            "浏览器缓存": "🌐",
            "回收站": "♻️",
            "崩溃转储": "💥",
            "Windows更新缓存": "🔄",
            "缩略图缓存": "🖼️",
            "安装包缓存": "📦",
            "预读取文件": "⚡",
            "开发缓存": "🔧",
            "最近文件记录": "📋",
        }
        icon_label = QLabel(icons.get(category, "📁"))
        icon_label.setFont(QFont("Segoe UI Emoji", 18))
        icon_label.setFixedWidth(36)
        layout.addWidget(icon_label)

        # Category name
        name_label = QLabel(category)
        name_label.setFont(QFont("Microsoft YaHei UI", 13))
        name_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(name_label)

        layout.addStretch()

        # Safety badge
        if not safe:
            badge = QLabel("⚠️ 需谨慎")
            badge.setStyleSheet("color: #ffa500; font-size: 12px;")
            layout.addWidget(badge)
            layout.addSpacing(8)

        # Size
        size_label = QLabel(format_size(size))
        size_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        size_label.setStyleSheet("color: #667eea;")
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        size_label.setFixedWidth(100)
        layout.addWidget(size_label)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()


# ═══════════════════════════════════════════════════════════════════════════
# Tab 1: Original Cleaner Tab
# ═══════════════════════════════════════════════════════════════════════════
class CleanerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report = None
        self.cards = []
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Status
        self.status_label = QLabel("点击「开始扫描」检测系统垃圾文件")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 11))
        self.status_label.setStyleSheet("color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Big Size Display
        self.size_label = QLabel("")
        self.size_label.setFont(QFont("Consolas", 48, QFont.Weight.Bold))
        self.size_label.setStyleSheet("color: #667eea;")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setVisible(False)
        layout.addWidget(self.size_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Category List
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setVisible(False)
        layout.addWidget(self.scroll_area, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.scan_btn = QPushButton("🔍  开始扫描")
        self.scan_btn.setObjectName("scanBtn")
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.clicked.connect(self._start_scan)
        btn_layout.addWidget(self.scan_btn)

        self.clean_btn = QPushButton("🧹  立即清理")
        self.clean_btn.setObjectName("cleanBtn")
        self.clean_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clean_btn.clicked.connect(self._start_clean)
        self.clean_btn.setEnabled(False)
        self.clean_btn.setVisible(False)
        btn_layout.addWidget(self.clean_btn)

        layout.addLayout(btn_layout)

    def _start_scan(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        self.progress_bar.setVisible(True)
        self.scroll_area.setVisible(False)
        self.size_label.setVisible(False)
        self.clean_btn.setVisible(False)

        for card in self.cards:
            card.deleteLater()
        self.cards.clear()

        self.worker = ScanWorker()
        self.worker.progress.connect(self._on_scan_progress)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.start()

    def _on_scan_progress(self, category: str, total_size: int):
        self.status_label.setText(f"正在扫描：{category}...")
        if total_size > 0:
            self.size_label.setVisible(True)
            self.size_label.setText(format_size(total_size))

    def _on_scan_finished(self, report: ScanReport):
        self.report = report
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍  重新扫描")

        if not report.results:
            self.status_label.setText("🎉 系统很干净，没有发现垃圾文件！")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
            return

        self.size_label.setVisible(True)
        self.size_label.setText(format_size(report.total_size))
        self.status_label.setText(f"发现 {len(report.results)} 项可清理内容")
        self.status_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")

        for category, size in sorted(report.categories.items(), key=lambda x: -x[1]):
            items = [r for r in report.results if r.category == category]
            all_safe = all(r.safe_to_delete for r in items)
            card = CategoryCard(category, size, safe=all_safe)
            card.toggled.connect(self._update_clean_btn)
            self.scroll_layout.addWidget(card)
            self.cards.append(card)

        self.scroll_area.setVisible(True)
        self.clean_btn.setVisible(True)
        self._update_clean_btn()

    def _update_clean_btn(self):
        selected_size = 0
        for card in self.cards:
            if card.is_checked():
                selected_size += card.size
        if selected_size > 0:
            self.clean_btn.setEnabled(True)
            self.clean_btn.setText(f"🧹  清理 {format_size(selected_size)}")
        else:
            self.clean_btn.setEnabled(False)
            self.clean_btn.setText("🧹  选择要清理的项目")

    def _start_clean(self):
        if not self.report:
            return

        selected_categories = set()
        for card in self.cards:
            if card.is_checked():
                selected_categories.add(card.category)

        if not selected_categories:
            return

        self.clean_btn.setEnabled(False)
        self.clean_btn.setText("清理中...")
        self.scan_btn.setEnabled(False)

        cleaned = 0
        failed = 0
        for result in self.report.results:
            if result.category in selected_categories:
                if Cleaner.delete_path(result.path, use_trash=True):
                    cleaned += 1
                else:
                    failed += 1

        if "回收站" in selected_categories:
            Cleaner.empty_recycle_bin()

        self.scan_btn.setEnabled(True)
        self.clean_btn.setText("✅ 清理完成")
        self.status_label.setText(f"已清理 {cleaned} 项，释放 {format_size(self.report.total_size)}")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
        self.size_label.setText("0 B")
        self.size_label.setStyleSheet("color: #4CAF50;")

        QTimer.singleShot(3000, self._reset_ui)

    def _reset_ui(self):
        self.clean_btn.setVisible(False)
        self.clean_btn.setEnabled(False)
        self.scroll_area.setVisible(False)
        self.size_label.setVisible(False)
        self.size_label.setStyleSheet("color: #667eea;")
        self.status_label.setText("点击「开始扫描」检测系统垃圾文件")
        self.status_label.setStyleSheet("color: #888;")
        self.scan_btn.setText("🔍  开始扫描")
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()
        self.report = None


# ═══════════════════════════════════════════════════════════════════════════
# Tab 2: Large File Finder
# ═══════════════════════════════════════════════════════════════════════════
class LargeFileTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("📂  大文件查找器")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        desc = QLabel("查找选定驱动器上最大的 20 个文件")
        desc.setFont(QFont("Microsoft YaHei UI", 11))
        desc.setStyleSheet("color: #666;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Drive selector
        drive_layout = QHBoxLayout()
        drive_layout.addStretch()
        drive_label = QLabel("选择驱动器：")
        drive_label.setFont(QFont("Microsoft YaHei UI", 12))
        drive_layout.addWidget(drive_label)

        self.drive_combo = QComboBox()
        for d in get_available_drives():
            self.drive_combo.addItem(d)
        self.drive_combo.setFixedWidth(120)
        drive_layout.addWidget(self.drive_combo)
        drive_layout.addStretch()
        layout.addLayout(drive_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.status_label.setStyleSheet("color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["#", "文件路径", "大小"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setVisible(False)
        layout.addWidget(self.table, 1)

        # Scan button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.find_btn = QPushButton("🔍  查找大文件")
        self.find_btn.setObjectName("proBtn")
        self.find_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.find_btn.clicked.connect(self._start_find)
        btn_layout.addWidget(self.find_btn)

        self.stop_btn = QPushButton("⏹  停止")
        self.stop_btn.setObjectName("proBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_find)
        self.stop_btn.setVisible(False)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _start_find(self):
        drive = self.drive_combo.currentText()
        self.find_btn.setEnabled(False)
        self.find_btn.setText("扫描中...")
        self.stop_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.table.setVisible(False)
        self.table.setRowCount(0)
        self.status_label.setText(f"正在扫描 {drive} ...")

        self.worker = LargeFileWorker(drive)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_find(self):
        if self.worker:
            self.worker.stop()

    def _on_progress(self, path: str, size: int):
        self.status_label.setText(f"扫描中: {path[:80]}...")

    def _on_finished(self, results: list):
        self.progress_bar.setVisible(False)
        self.stop_btn.setVisible(False)
        self.find_btn.setEnabled(True)
        self.find_btn.setText("🔍  查找大文件")

        if not results:
            self.status_label.setText("未找到文件")
            return

        self.status_label.setText(f"找到 {len(results)} 个大文件")
        self.table.setRowCount(len(results))

        for i, item in enumerate(results):
            rank = QTableWidgetItem(str(i + 1))
            rank.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, rank)

            path_item = QTableWidgetItem(item['path'])
            path_item.setToolTip(item['path'])
            self.table.setItem(i, 1, path_item)

            size_item = QTableWidgetItem(format_size(item['size']))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            size_item.setForeground(QColor("#667eea"))
            self.table.setItem(i, 2, size_item)

        self.table.setVisible(True)


# ═══════════════════════════════════════════════════════════════════════════
# Tab 3: Duplicate File Finder
# ═══════════════════════════════════════════════════════════════════════════
class DuplicateTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.duplicates = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("👯  重复文件查找器")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        desc = QLabel("通过 MD5 哈希查找重复文件，选择要删除的副本")
        desc.setFont(QFont("Microsoft YaHei UI", 11))
        desc.setStyleSheet("color: #666;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Drive selector
        drive_layout = QHBoxLayout()
        drive_layout.addStretch()
        drive_label = QLabel("选择驱动器：")
        drive_label.setFont(QFont("Microsoft YaHei UI", 12))
        drive_layout.addWidget(drive_label)

        self.drive_combo = QComboBox()
        for d in get_available_drives():
            self.drive_combo.addItem(d)
        self.drive_combo.setFixedWidth(120)
        drive_layout.addWidget(self.drive_combo)
        drive_layout.addStretch()
        layout.addLayout(drive_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.status_label.setStyleSheet("color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["", "文件路径", "大小", "MD5 哈希"])
        self.tree.setColumnWidth(0, 30)
        self.tree.setColumnWidth(2, 100)
        self.tree.setAlternatingRowColors(True)
        self.tree.setVisible(False)
        layout.addWidget(self.tree, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.find_btn = QPushButton("🔍  查找重复文件")
        self.find_btn.setObjectName("proBtn")
        self.find_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.find_btn.clicked.connect(self._start_find)
        btn_layout.addWidget(self.find_btn)

        self.stop_btn = QPushButton("⏹  停止")
        self.stop_btn.setObjectName("proBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_find)
        self.stop_btn.setVisible(False)
        btn_layout.addWidget(self.stop_btn)

        self.delete_btn = QPushButton("🗑️  删除选中")
        self.delete_btn.setObjectName("cleanBtn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.delete_btn.setVisible(False)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _start_find(self):
        drive = self.drive_combo.currentText()
        self.find_btn.setEnabled(False)
        self.find_btn.setText("扫描中...")
        self.stop_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.tree.setVisible(False)
        self.delete_btn.setVisible(False)
        self.tree.clear()
        self.status_label.setText(f"正在扫描 {drive} ...")

        self.worker = DuplicateWorker(drive)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_find(self):
        if self.worker:
            self.worker.stop()

    def _on_progress(self, msg: str, count: int):
        self.status_label.setText(msg[:100])

    def _on_finished(self, duplicates: dict):
        self.progress_bar.setVisible(False)
        self.stop_btn.setVisible(False)
        self.find_btn.setEnabled(True)
        self.find_btn.setText("🔍  查找重复文件")
        self.duplicates = duplicates

        if not duplicates:
            self.status_label.setText("未找到重复文件 ✅")
            return

        total_groups = len(duplicates)
        total_files = sum(len(files) for files in duplicates.values())
        wasted = sum(
            files[0]['size'] * (len(files) - 1)
            for files in duplicates.values()
        )
        self.status_label.setText(
            f"找到 {total_groups} 组重复文件（共 {total_files} 个文件），"
            f"可释放 {format_size(wasted)}"
        )

        self.tree.clear()
        for hash_val, files in duplicates.items():
            group = QTreeWidgetItem(self.tree)
            group.setText(0, "📁")
            group.setText(1, f"重复组 ({len(files)} 个文件)")
            group.setText(2, format_size(files[0]['size']))
            group.setText(3, hash_val[:16] + "...")
            group.setExpanded(True)

            # First file is "original" (not checked)
            first = QTreeWidgetItem(group)
            first.setFlags(first.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            first.setCheckState(0, Qt.CheckState.Unchecked)
            first.setText(1, files[0]['path'])
            first.setText(2, format_size(files[0]['size']))
            first.setText(3, "")
            first.setToolTip(1, files[0]['path'])

            # Rest are duplicates (checked by default)
            for f in files[1:]:
                item = QTreeWidgetItem(group)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked)
                item.setText(1, f['path'])
                item.setText(2, format_size(f['size']))
                item.setText(3, "")
                item.setToolTip(1, f['path'])

        self.tree.setVisible(True)
        self.delete_btn.setVisible(True)

    def _delete_selected(self):
        checked_paths = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                item = group.child(j)
                if item.checkState(0) == Qt.CheckState.Checked:
                    checked_paths.append(item.text(1))

        if not checked_paths:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要将 {len(checked_paths)} 个文件移到回收站吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        cleaned = 0
        for path in checked_paths:
            if Cleaner.delete_path(path, use_trash=True):
                cleaned += 1

        QMessageBox.information(self, "完成", f"已删除 {cleaned} 个文件")

        # Refresh
        self.tree.clear()
        self.delete_btn.setVisible(False)
        self.status_label.setText(f"已删除 {cleaned} 个重复文件 ✅")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 4: Startup Manager
# ═══════════════════════════════════════════════════════════════════════════
class StartupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.programs = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("🚀  启动项管理")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        desc = QLabel("管理 Windows 启动程序，禁用不需要的自启项可加快开机速度")
        desc.setFont(QFont("Microsoft YaHei UI", 11))
        desc.setStyleSheet("color: #666;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Status
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.status_label.setStyleSheet("color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["状态", "程序名称", "命令行", "位置", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 100)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.refresh_btn = QPushButton("🔄  刷新")
        self.refresh_btn.setObjectName("proBtn")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._load_startup)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Auto-load
        QTimer.singleShot(100, self._load_startup)

    def _load_startup(self):
        self.programs = StartupManager.get_startup_programs()
        self.table.setRowCount(len(self.programs))

        for i, prog in enumerate(self.programs):
            # Status
            status = "✅ 启用" if prog['enabled'] else "⛔ 禁用"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if prog['enabled']:
                status_item.setForeground(QColor("#4CAF50"))
            else:
                status_item.setForeground(QColor("#ff6b6b"))
            self.table.setItem(i, 0, status_item)

            # Name
            name_item = QTableWidgetItem(prog['name'])
            name_item.setToolTip(prog['name'])
            self.table.setItem(i, 1, name_item)

            # Command
            cmd_item = QTableWidgetItem(prog['command'])
            cmd_item.setToolTip(prog['command'])
            self.table.setItem(i, 2, cmd_item)

            # Location
            loc_item = QTableWidgetItem(prog['location'])
            loc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, loc_item)

            # Action button
            if 'RunOnce' not in prog['reg_path']:
                btn_text = "禁用" if prog['enabled'] else "启用"
                btn = QPushButton(btn_text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1a2e;
                        color: #e0e0e0;
                        border: 1px solid #2a2a4a;
                        border-radius: 4px;
                        padding: 4px 12px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #2a2a4a;
                    }
                """)
                btn.clicked.connect(lambda checked, idx=i: self._toggle_startup(idx))
                self.table.setCellWidget(i, 4, btn)
            else:
                once_item = QTableWidgetItem("(一次性)")
                once_item.setForeground(QColor("#666"))
                once_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 4, once_item)

        self.status_label.setText(f"共 {len(self.programs)} 个启动项")

    def _toggle_startup(self, index: int):
        prog = self.programs[index]
        name = prog['name']
        hive = prog['hive']
        reg_path = prog['reg_path']

        if prog['enabled']:
            success = StartupManager.disable_startup(name, hive, reg_path)
            action = "禁用"
        else:
            success = StartupManager.enable_startup(name, hive, reg_path)
            action = "启用"

        if success:
            prog['enabled'] = not prog['enabled']
            self._load_startup()  # Refresh
        else:
            QMessageBox.warning(self, "错误", f"无法{action} {name}")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 5: Disk Usage Analyzer
# ═══════════════════════════════════════════════════════════════════════════
class DiskUsageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("📊  磁盘使用分析")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        desc = QLabel("查看磁盘空间的可视化使用情况")
        desc.setFont(QFont("Microsoft YaHei UI", 11))
        desc.setStyleSheet("color: #666;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Drive selector
        drive_layout = QHBoxLayout()
        drive_layout.addStretch()
        drive_label = QLabel("选择驱动器：")
        drive_label.setFont(QFont("Microsoft YaHei UI", 12))
        drive_layout.addWidget(drive_label)

        self.drive_combo = QComboBox()
        for d in get_available_drives():
            self.drive_combo.addItem(d)
        self.drive_combo.setFixedWidth(120)
        drive_layout.addWidget(self.drive_combo)
        drive_layout.addStretch()
        layout.addLayout(drive_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.status_label.setStyleSheet("color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "大小", "占比", "路径"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setVisible(False)
        layout.addWidget(self.tree, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.analyze_btn = QPushButton("📊  分析磁盘")
        self.analyze_btn.setObjectName("proBtn")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.clicked.connect(self._start_analyze)
        btn_layout.addWidget(self.analyze_btn)

        self.stop_btn = QPushButton("⏹  停止")
        self.stop_btn.setObjectName("proBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_analyze)
        self.stop_btn.setVisible(False)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _start_analyze(self):
        drive = self.drive_combo.currentText()
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("分析中...")
        self.stop_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.tree.setVisible(False)
        self.tree.clear()
        self.status_label.setText(f"正在分析 {drive} ...")

        self.worker = DiskUsageWorker(drive)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_analyze(self):
        if self.worker:
            self.worker.stop()

    def _on_progress(self, path: str, size: int):
        self.status_label.setText(f"分析中: {path[:80]}")

    def _on_finished(self, results: list):
        self.progress_bar.setVisible(False)
        self.stop_btn.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("📊  分析磁盘")

        if not results:
            self.status_label.setText("无法分析该驱动器")
            return

        total_size = sum(item['size'] for item in results)
        self.status_label.setText(f"总计: {format_size(total_size)}")

        self.tree.clear()
        self._populate_tree(self.tree.invisibleRootItem(), results, total_size)
        self.tree.expandToDepth(0)
        self.tree.setVisible(True)

    def _populate_tree(self, parent_item, items: list, total_size: int):
        for item in items:
            if item['size'] == 0:
                continue

            tree_item = QTreeWidgetItem(parent_item)
            tree_item.setText(0, item['name'])
            tree_item.setText(1, format_size(item['size']))
            tree_item.setText(2, f"{item['size'] / total_size * 100:.1f}%")
            tree_item.setText(3, item['path'])
            tree_item.setToolTip(3, item['path'])

            # Color code by size
            pct = item['size'] / total_size * 100
            if pct > 20:
                tree_item.setForeground(1, QColor("#f5576c"))
            elif pct > 10:
                tree_item.setForeground(1, QColor("#ffa500"))
            elif pct > 5:
                tree_item.setForeground(1, QColor("#667eea"))

            if item.get('children'):
                self._populate_tree(tree_item, item['children'], total_size)


# ── Main Window ─────────────────────────────────────────────────────────
class CleanMasterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleanMaster Pro")
        self.setMinimumSize(640, 700)
        self.resize(640, 760)

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        # ── Header ──
        header = QLabel("CleanMaster Pro")
        header.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        header.setStyleSheet("color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        subtitle = QLabel("系统清理 · 磁盘分析 · 启动管理 · 重复文件查找")
        subtitle.setFont(QFont("Microsoft YaHei UI", 11))
        subtitle.setStyleSheet("color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        main_layout.addSpacing(4)

        # ── Tab Widget ──
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tabs.addTab(CleanerTab(), "🧹 垃圾清理")
        self.tabs.addTab(LargeFileTab(), "📂 大文件")
        self.tabs.addTab(DuplicateTab(), "👯 重复文件")
        self.tabs.addTab(StartupTab(), "🚀 启动项")
        self.tabs.addTab(DiskUsageTab(), "📊 磁盘分析")

        main_layout.addWidget(self.tabs, 1)

        # ── Footer ──
        footer = QLabel("v2.0.0 Pro  ·  Made with ❤️  ·  github.com/INFINITE1994")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: #444;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setStyle("Fusion")

    window = CleanMasterWindow()
    window.show()
    sys.exit(app.exec())
