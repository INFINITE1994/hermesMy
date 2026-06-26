#!/usr/bin/env python3
"""
高级进程管理器 (ProcessManager)
一款功能强大、界面精美的 Windows 进程管理工具
"""

import sys
import os
import csv
import psutil
import time
from datetime import datetime
from collections import defaultdict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame, QGridLayout, QMessageBox, QFileDialog,
    QProgressBar, QStyledItemDelegate, QStyle, QMenu, QAbstractItemView,
    QComboBox, QTextEdit, QGroupBox, QScrollArea, QSizePolicy,
    QSystemTrayIcon, QStyleFactory
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, QSortFilterProxyModel, QAbstractTableModel,
    QModelIndex, QVariant
)
from PyQt6.QtGui import (
    QColor, QPalette, QFont, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QPixmap, QAction, QCursor, QFontDatabase,
    QConicalGradient, QRadialGradient
)


# ============================================================================
# 深色主题样式表
# ============================================================================
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 10pt;
}

QTabWidget::pane {
    border: 1px solid #2a2a3a;
    background-color: #111122;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #888;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a3a;
    color: #ccc;
}

QTableWidget {
    background-color: #111122;
    alternate-background-color: #16162e;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    gridline-color: #2a2a3a;
    selection-background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    selection-color: white;
}

QTableWidget::item {
    padding: 8px;
    border: none;
}

QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
}

QHeaderView::section {
    background-color: #1a1a2e;
    color: #667eea;
    padding: 10px;
    border: none;
    border-right: 1px solid #2a2a3a;
    border-bottom: 2px solid #667eea;
    font-weight: bold;
}

QTreeWidget {
    background-color: #111122;
    alternate-background-color: #16162e;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    outline: none;
}

QTreeWidget::item {
    padding: 6px;
    border: none;
}

QTreeWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTreeWidget::item:hover {
    background-color: #2a2a3a;
}

QTreeWidget::branch {
    background-color: #111122;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8ff0, stop:1 #8b5fb8);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5567d9, stop:1 #654091);
}

QPushButton:disabled {
    background-color: #333;
    color: #666;
}

QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff4757, stop:1 #ff6b81);
}

QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff5f6f, stop:1 #ff8191);
}

QPushButton#successBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ed573, stop:1 #7bed9f);
}

QPushButton#successBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3ee084, stop:1 #8cf0af);
}

QLineEdit {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 2px solid #2a2a3a;
    border-radius: 6px;
    padding: 10px 15px;
    font-size: 11pt;
}

QLineEdit:focus {
    border: 2px solid #667eea;
}

QLineEdit::placeholder {
    color: #555;
}

QLabel {
    color: #e0e0e0;
}

QLabel#titleLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #667eea;
}

QLabel#subtitleLabel {
    font-size: 11pt;
    color: #888;
}

QLabel#statLabel {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 15px;
    font-size: 10pt;
}

QLabel#statValue {
    font-size: 18pt;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    -webkit-background-clip: text;
    color: #667eea;
}

QFrame#card {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    padding: 15px;
}

QFrame#separator {
    background-color: #2a2a3a;
    max-height: 1px;
}

QComboBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 2px solid #2a2a3a;
    border-radius: 6px;
    padding: 8px 15px;
    min-width: 150px;
}

QComboBox:focus {
    border: 2px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #667eea;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    selection-background-color: #667eea;
}

QTextEdit {
    background-color: #111122;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 10px;
    font-family: "Consolas", "Courier New", monospace;
}

QProgressBar {
    background-color: #1a1a2e;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: white;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 4px;
}

QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #2a2a3a;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0a0a0a;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #2a2a3a;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #667eea;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
    font-weight: bold;
    color: #667eea;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    background-color: #111122;
}

QMenu {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 25px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #2a2a3a;
    margin: 5px 10px;
}

QMessageBox {
    background-color: #111122;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QFileDialog {
    background-color: #111122;
}
"""


class ProcessWorker(QThread):
    """后台线程：获取进程数据"""
    data_ready = pyqtSignal(list)

    def run(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                          'status', 'username', 'create_time', 'ppid']):
            try:
                info = proc.info
                info['cpu_percent'] = info.get('cpu_percent', 0) or 0
                info['memory_percent'] = info.get('memory_percent', 0) or 0
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.data_ready.emit(processes)


class ResourceMonitorWidget(QWidget):
    """资源监控图表组件"""

    def __init__(self, title="CPU 使用率", color_start="#667eea", color_end="#764ba2", max_val=100):
        super().__init__()
        self.title = title
        self.color_start = color_start
        self.color_end = color_end
        self.max_val = max_val
        self.data_points = []
        self.max_points = 120
        self.setMinimumHeight(200)
        self.setMinimumWidth(300)

    def add_data(self, value):
        self.data_points.append(min(value, self.max_val))
        if len(self.data_points) > self.max_points:
            self.data_points = self.data_points[-self.max_points:]
        self.update()

    def paintEvent(self, event):
        if not self.data_points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        padding = 40
        chart_w = w - 2 * padding
        chart_h = h - 2 * padding

        # 背景
        painter.fillRect(0, 0, w, h, QColor("#111122"))

        # 边框
        painter.setPen(QPen(QColor("#2a2a3a"), 1))
        painter.drawRoundedRect(10, 10, w - 20, h - 20, 10, 10)

        # 标题
        painter.setPen(QColor("#667eea"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(20, 30, self.title)

        # 网格线
        painter.setPen(QPen(QColor("#1a1a2e"), 1))
        for i in range(5):
            y = padding + (chart_h * i / 4)
            painter.drawLine(int(padding), int(y), int(w - padding), int(y))
            val = int(self.max_val * (1 - i / 4))
            painter.setPen(QColor("#555"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(5, int(y - 5), int(30), 20,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           f"{val}%")
            painter.setPen(QPen(QColor("#1a1a2e"), 1))

        # 绘制曲线
        if len(self.data_points) > 1:
            gradient = QLinearGradient(0, padding, 0, h - padding)
            gradient.setColorAt(0, QColor(102, 126, 234, 80))
            gradient.setColorAt(1, QColor(118, 75, 162, 10))

            # 填充区域
            path_points = []
            for i, val in enumerate(self.data_points):
                x = padding + (chart_w * i / (self.max_points - 1))
                y = padding + chart_h * (1 - val / self.max_val)
                path_points.append((x, y))

            # 填充
            from PyQt6.QtGui import QPainterPath
            fill_path = QPainterPath()
            fill_path.moveTo(path_points[0][0], h - padding)
            for x, y in path_points:
                fill_path.lineTo(x, y)
            fill_path.lineTo(path_points[-1][0], h - padding)
            fill_path.closeSubpath()
            painter.fillPath(fill_path, QBrush(gradient))

            # 线条
            line_gradient = QLinearGradient(padding, 0, w - padding, 0)
            line_gradient.setColorAt(0, QColor("#667eea"))
            line_gradient.setColorAt(1, QColor("#764ba2"))
            painter.setPen(QPen(QBrush(line_gradient), 2.5))
            for i in range(len(path_points) - 1):
                painter.drawLine(int(path_points[i][0]), int(path_points[i][1]),
                               int(path_points[i+1][0]), int(path_points[i+1][1]))

            # 当前值
            if self.data_points:
                last_val = self.data_points[-1]
                painter.setPen(QColor("#667eea"))
                painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                painter.drawText(w - 120, 30, f"{last_val:.1f}%")

        painter.end()


class StatCard(QFrame):
    """统计卡片组件"""

    def __init__(self, title, value="0", icon="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 16))
        icon_label.setStyleSheet("color: #667eea;")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 10pt;")
        header.addWidget(title_label)
        header.addStretch()

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            font-size: 22pt;
            font-weight: bold;
            color: #667eea;
        """)

        layout.addLayout(header)
        layout.addWidget(self.value_label)

    def update_value(self, value):
        self.value_label.setText(str(value))


class ProcessDetailPanel(QFrame):
    """进程详情面板"""

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("📋 进程详情")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        layout.addWidget(title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(400)
        layout.addWidget(self.detail_text)

        btn_layout = QHBoxLayout()

        self.kill_btn = QPushButton("❌ 终止进程")
        self.kill_btn.setObjectName("dangerBtn")
        self.kill_btn.clicked.connect(self.kill_process)
        btn_layout.addWidget(self.kill_btn)

        self.suspend_btn = QPushButton("⏸ 暂停进程")
        self.suspend_btn.clicked.connect(self.suspend_process)
        btn_layout.addWidget(self.suspend_btn)

        self.resume_btn = QPushButton("▶ 恢复进程")
        self.resume_btn.setObjectName("successBtn")
        self.resume_btn.clicked.connect(self.resume_process)
        btn_layout.addWidget(self.resume_btn)

        layout.addLayout(btn_layout)

        self.current_pid = None

    def update_detail(self, pid):
        self.current_pid = pid
        try:
            proc = psutil.Process(pid)
            info = proc.as_dict(attrs=[
                'pid', 'name', 'status', 'username', 'create_time',
                'cpu_percent', 'memory_percent', 'memory_info',
                'num_threads', 'exe', 'cmdline', 'cwd',
                'ppid', 'nice', 'io_counters'
            ])

            details = []
            details.append(f"📌 进程名称: {info.get('name', 'N/A')}")
            details.append(f"🆔 进程ID: {info.get('pid', 'N/A')}")
            details.append(f"👤 用户: {info.get('username', 'N/A')}")
            details.append(f"📊 状态: {info.get('status', 'N/A')}")
            details.append(f"⚡ CPU使用率: {info.get('cpu_percent', 0):.1f}%")
            details.append(f"💾 内存使用率: {info.get('memory_percent', 0):.1f}%")

            mem_info = info.get('memory_info')
            if mem_info:
                details.append(f"📈 内存详情: RSS={mem_info.rss / 1024 / 1024:.1f}MB, VMS={mem_info.vms / 1024 / 1024:.1f}MB")

            details.append(f"🧵 线程数: {info.get('num_threads', 'N/A')}")
            details.append(f"🏢 父进程ID: {info.get('ppid', 'N/A')}")
            details.append(f"🎯 优先级: {info.get('nice', 'N/A')}")

            create_time = info.get('create_time')
            if create_time:
                details.append(f"⏰ 创建时间: {datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')}")

            exe = info.get('exe')
            if exe:
                details.append(f"📁 可执行文件: {exe}")

            cmdline = info.get('cmdline')
            if cmdline:
                details.append(f"💻 命令行: {' '.join(cmdline) if isinstance(cmdline, list) else cmdline}")

            cwd = info.get('cwd')
            if cwd:
                details.append(f"📂 工作目录: {cwd}")

            io = info.get('io_counters')
            if io:
                details.append(f"📥 读取字节: {io.read_bytes / 1024 / 1024:.1f}MB")
                details.append(f"📤 写入字节: {io.write_bytes / 1024 / 1024:.1f}MB")

            self.detail_text.setText("\n\n".join(details))

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.detail_text.setText(f"⚠️ 无法获取进程信息: {e}")
            self.current_pid = None

    def kill_process(self):
        if self.current_pid:
            reply = QMessageBox.question(
                self, "确认终止",
                f"确定要终止进程 PID {self.current_pid} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    proc = psutil.Process(self.current_pid)
                    proc.kill()
                    QMessageBox.information(self, "成功", f"进程 {self.current_pid} 已终止")
                    self.detail_text.clear()
                    self.current_pid = None
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"终止进程失败: {e}")

    def suspend_process(self):
        if self.current_pid:
            try:
                proc = psutil.Process(self.current_pid)
                proc.suspend()
                QMessageBox.information(self, "成功", f"进程 {self.current_pid} 已暂停")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"暂停进程失败: {e}")

    def resume_process(self):
        if self.current_pid:
            try:
                proc = psutil.Process(self.current_pid)
                proc.resume()
                QMessageBox.information(self, "成功", f"进程 {self.current_pid} 已恢复")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"恢复进程失败: {e}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级进程管理器 - ProcessManager")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # 数据存储
        self.process_data = []
        self.cpu_history = []
        self.mem_history = []

        # 初始化UI
        self.init_ui()

        # 定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_processes)
        self.refresh_timer.start(2000)

        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resources)
        self.resource_timer.start(1000)

        # 初始加载
        self.refresh_processes()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 左侧导航栏
        nav_frame = QFrame()
        nav_frame.setObjectName("card")
        nav_frame.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setSpacing(5)
        nav_layout.setContentsMargins(10, 15, 10, 15)

        logo_label = QLabel("🖥️ 进程管理器")
        logo_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(logo_label)

        nav_layout.addSpacing(20)

        self.nav_buttons = []
        nav_items = [
            ("📊 仪表盘", 0),
            ("📋 进程列表", 1),
            ("🌳 进程树", 2),
            ("📈 资源监控", 3),
            ("🚀 启动项", 4),
            ("⚙️ 服务", 5),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    text-align: left;
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #1a1a2e;
                }
            """)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #555; font-size: 9pt;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(version_label)

        main_layout.addWidget(nav_frame)

        # 右侧内容区
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # 搜索栏
        search_frame = QFrame()
        search_frame.setObjectName("card")
        search_layout = QHBoxLayout(search_frame)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索进程名称、PID或用户...")
        self.search_input.textChanged.connect(self.filter_processes)
        search_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部进程", "运行中", "睡眠中", "停止"])
        self.filter_combo.currentTextChanged.connect(self.filter_processes)
        search_layout.addWidget(self.filter_combo)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_processes)
        search_layout.addWidget(refresh_btn)

        export_btn = QPushButton("📤 导出")
        export_btn.clicked.connect(self.export_processes)
        search_layout.addWidget(export_btn)

        content_layout.addWidget(search_frame)

        # 主标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # 创建各个标签页
        self.create_dashboard_tab()
        self.create_process_list_tab()
        self.create_process_tree_tab()
        self.create_resource_monitor_tab()
        self.create_startup_tab()
        self.create_services_tab()

        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(content_widget)

    def create_dashboard_tab(self):
        """仪表盘标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 统计卡片行
        stats_layout = QHBoxLayout()

        self.cpu_card = StatCard("CPU 使用率", "0%", "⚡")
        stats_layout.addWidget(self.cpu_card)

        self.mem_card = StatCard("内存使用率", "0%", "💾")
        stats_layout.addWidget(self.mem_card)

        self.process_count_card = StatCard("运行进程", "0", "📋")
        stats_layout.addWidget(self.process_count_card)

        self.thread_count_card = StatCard("总线程数", "0", "🧵")
        stats_layout.addWidget(self.thread_count_card)

        layout.addLayout(stats_layout)

        # 资源监控图表
        charts_layout = QHBoxLayout()

        self.cpu_chart = ResourceMonitorWidget("CPU 使用率趋势", "#667eea", "#764ba2")
        charts_layout.addWidget(self.cpu_chart)

        self.mem_chart = ResourceMonitorWidget("内存使用率趋势", "#2ed573", "#7bed9f")
        charts_layout.addWidget(self.mem_chart)

        layout.addLayout(charts_layout)

        # 高占用进程
        top_label = QLabel("🔥 资源占用 Top 10 进程")
        top_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #667eea;")
        layout.addWidget(top_label)

        self.top_table = QTableWidget()
        self.top_table.setColumnCount(5)
        self.top_table.setHorizontalHeaderLabels(["PID", "进程名称", "CPU %", "内存 %", "状态"])
        self.top_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.top_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.top_table.setAlternatingRowColors(True)
        layout.addWidget(self.top_table)

        self.tab_widget.addTab(tab, "📊 仪表盘")

    def create_process_list_tab(self):
        """进程列表标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # 进程表格
        splitter = QSplitter(Qt.Orientation.Horizontal)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "进程名称", "CPU %", "内存 %", "状态", "用户", "线程数", "创建时间"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setSortingEnabled(True)
        self.process_table.itemClicked.connect(self.on_process_selected)
        self.process_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_process_context_menu)

        table_layout.addWidget(self.process_table)

        # 底部操作栏
        action_layout = QHBoxLayout()

        self.kill_btn = QPushButton("❌ 终止选中进程")
        self.kill_btn.setObjectName("dangerBtn")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        action_layout.addWidget(self.kill_btn)

        self.priority_btn = QPushButton("⬆ 设置优先级")
        self.priority_btn.clicked.connect(self.set_process_priority)
        action_layout.addWidget(self.priority_btn)

        action_layout.addStretch()

        self.process_count_label = QLabel("共 0 个进程")
        self.process_count_label.setStyleSheet("color: #888;")
        action_layout.addWidget(self.process_count_label)

        table_layout.addLayout(action_layout)

        splitter.addWidget(table_container)

        # 详情面板
        self.detail_panel = ProcessDetailPanel()
        splitter.addWidget(self.detail_panel)

        splitter.setSizes([900, 400])

        layout.addWidget(splitter)
        self.tab_widget.addTab(tab, "📋 进程列表")

    def create_process_tree_tab(self):
        """进程树标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("🌳 进程树 - 父子关系")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        layout.addWidget(header)

        self.process_tree = QTreeWidget()
        self.process_tree.setHeaderLabels(["进程名称", "PID", "CPU %", "内存 %", "状态", "用户"])
        self.process_tree.setColumnCount(6)
        self.process_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.process_tree.setAlternatingRowColors(True)
        self.process_tree.setAnimated(True)
        self.process_tree.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.process_tree)

        btn_layout = QHBoxLayout()
        expand_btn = QPushButton("📂 全部展开")
        expand_btn.clicked.connect(self.process_tree.expandAll)
        btn_layout.addWidget(expand_btn)

        collapse_btn = QPushButton("📁 全部折叠")
        collapse_btn.clicked.connect(self.process_tree.collapseAll)
        btn_layout.addWidget(collapse_btn)

        btn_layout.addStretch()

        refresh_tree_btn = QPushButton("🔄 刷新树")
        refresh_tree_btn.clicked.connect(self.build_process_tree)
        btn_layout.addWidget(refresh_tree_btn)

        layout.addLayout(btn_layout)

        self.tab_widget.addTab(tab, "🌳 进程树")

    def create_resource_monitor_tab(self):
        """资源监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("📈 实时资源监控")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        layout.addWidget(header)

        # 大图表
        self.big_cpu_chart = ResourceMonitorWidget("系统 CPU 使用率", "#667eea", "#764ba2", 100)
        self.big_cpu_chart.setMinimumHeight(250)
        layout.addWidget(self.big_cpu_chart)

        self.big_mem_chart = ResourceMonitorWidget("系统内存使用率", "#2ed573", "#7bed9f", 100)
        self.big_mem_chart.setMinimumHeight(250)
        layout.addWidget(self.big_mem_chart)

        # 进程级监控
        monitor_header = QLabel("🔍 单进程资源监控")
        monitor_header.setStyleSheet("font-size: 12pt; font-weight: bold; color: #667eea;")
        layout.addWidget(monitor_header)

        pid_layout = QHBoxLayout()
        pid_layout.addWidget(QLabel("输入PID:"))

        self.monitor_pid_input = QLineEdit()
        self.monitor_pid_input.setPlaceholderText("输入要监控的进程PID...")
        pid_layout.addWidget(self.monitor_pid_input)

        monitor_btn = QPushButton("📊 开始监控")
        monitor_btn.clicked.connect(self.start_process_monitor)
        pid_layout.addWidget(monitor_btn)

        layout.addLayout(pid_layout)

        self.process_cpu_chart = ResourceMonitorWidget("进程 CPU 使用率", "#ffa502", "#ff6348", 100)
        self.process_cpu_chart.setMinimumHeight(200)
        layout.addWidget(self.process_cpu_chart)

        self.tab_widget.addTab(tab, "📈 资源监控")

    def create_startup_tab(self):
        """启动项管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("🚀 启动项管理")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        layout.addWidget(header)

        self.startup_table = QTableWidget()
        self.startup_table.setColumnCount(5)
        self.startup_table.setHorizontalHeaderLabels(["名称", "命令", "位置", "用户", "状态"])
        self.startup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.startup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.startup_table.setAlternatingRowColors(True)
        layout.addWidget(self.startup_table)

        btn_layout = QHBoxLayout()

        refresh_startup_btn = QPushButton("🔄 刷新启动项")
        refresh_startup_btn.clicked.connect(self.load_startup_items)
        btn_layout.addWidget(refresh_startup_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self.tab_widget.addTab(tab, "🚀 启动项")

    def create_services_tab(self):
        """服务管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("⚙️ Windows 服务管理")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #667eea;")
        layout.addWidget(header)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("状态过滤:"))

        self.service_filter = QComboBox()
        self.service_filter.addItems(["全部", "运行中", "已停止", "启动中"])
        self.service_filter.currentTextChanged.connect(self.filter_services)
        filter_layout.addWidget(self.service_filter)

        self.service_search = QLineEdit()
        self.service_search.setPlaceholderText("🔍 搜索服务名称...")
        self.service_search.textChanged.connect(self.filter_services)
        filter_layout.addWidget(self.service_search)

        layout.addLayout(filter_layout)

        self.service_table = QTableWidget()
        self.service_table.setColumnCount(6)
        self.service_table.setHorizontalHeaderLabels([
            "服务名称", "显示名称", "状态", "启动类型", "PID", "描述"
        ])
        self.service_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.service_table.horizontalHeader().setStretchLastSection(True)
        self.service_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.service_table.setAlternatingRowColors(True)
        self.service_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.service_table.customContextMenuRequested.connect(self.show_service_context_menu)
        layout.addWidget(self.service_table)

        btn_layout = QHBoxLayout()

        refresh_services_btn = QPushButton("🔄 刷新服务")
        refresh_services_btn.clicked.connect(self.load_services)
        btn_layout.addWidget(refresh_services_btn)

        btn_layout.addStretch()

        self.service_count_label = QLabel("共 0 个服务")
        self.service_count_label.setStyleSheet("color: #888;")
        btn_layout.addWidget(self.service_count_label)

        layout.addLayout(btn_layout)

        self.tab_widget.addTab(tab, "⚙️ 服务")

    def switch_tab(self, index):
        """切换标签页"""
        self.tab_widget.setCurrentIndex(index)
        # 更新导航按钮样式
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #667eea, stop:1 #764ba2);
                        text-align: left;
                        padding: 12px 15px;
                        border-radius: 8px;
                        font-size: 11pt;
                        color: white;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        text-align: left;
                        padding: 12px 15px;
                        border-radius: 8px;
                        font-size: 11pt;
                        color: #e0e0e0;
                    }
                    QPushButton:hover {
                        background-color: #1a1a2e;
                    }
                """)

    def refresh_processes(self):
        """刷新进程列表"""
        self.worker = ProcessWorker()
        self.worker.data_ready.connect(self.on_processes_loaded)
        self.worker.start()

    def on_processes_loaded(self, processes):
        """进程数据加载完成"""
        self.process_data = processes
        self.update_process_table()
        self.update_dashboard()
        self.build_process_tree()

    def update_process_table(self):
        """更新进程表格"""
        search_text = self.search_input.text().lower()
        filter_status = self.filter_combo.currentText()

        filtered = []
        for proc in self.process_data:
            # 搜索过滤
            if search_text:
                name = str(proc.get('name', '')).lower()
                pid = str(proc.get('pid', ''))
                user = str(proc.get('username', '') or '').lower()
                if search_text not in name and search_text not in pid and search_text not in user:
                    continue

            # 状态过滤
            if filter_status != "全部进程":
                status_map = {"运行中": "running", "睡眠中": "sleeping", "停止": "stopped"}
                if proc.get('status') != status_map.get(filter_status, ''):
                    continue

            filtered.append(proc)

        self.process_table.setRowCount(len(filtered))

        for row, proc in enumerate(filtered):
            items = [
                str(proc.get('pid', '')),
                str(proc.get('name', '')),
                f"{proc.get('cpu_percent', 0):.1f}",
                f"{proc.get('memory_percent', 0):.1f}",
                str(proc.get('status', '')),
                str(proc.get('username', '') or 'N/A'),
                str(proc.get('num_threads', '')),
                datetime.fromtimestamp(proc['create_time']).strftime('%Y-%m-%d %H:%M') if proc.get('create_time') else 'N/A'
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 高亮高占用
                if col == 2 and float(text) > 50:
                    item.setForeground(QColor("#ff4757"))
                elif col == 3 and float(text) > 50:
                    item.setForeground(QColor("#ffa502"))

                self.process_table.setItem(row, col, item)

        self.process_count_label.setText(f"共 {len(filtered)} 个进程")

    def update_dashboard(self):
        """更新仪表盘"""
        # 系统资源
        cpu_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory()

        self.cpu_card.update_value(f"{cpu_percent:.1f}%")
        self.mem_card.update_value(f"{mem.percent:.1f}%")
        self.process_count_card.update_value(str(len(self.process_data)))

        total_threads = sum(p.get('num_threads', 0) or 0 for p in self.process_data)
        self.thread_count_card.update_value(str(total_threads))

        # 更新图表
        self.cpu_chart.add_data(cpu_percent)
        self.mem_chart.add_data(mem.percent)
        self.big_cpu_chart.add_data(cpu_percent)
        self.big_mem_chart.add_data(mem.percent)

        # Top 10 进程
        sorted_procs = sorted(self.process_data,
                            key=lambda x: x.get('cpu_percent', 0) + x.get('memory_percent', 0),
                            reverse=True)[:10]

        self.top_table.setRowCount(len(sorted_procs))
        for row, proc in enumerate(sorted_procs):
            items = [
                str(proc.get('pid', '')),
                str(proc.get('name', '')),
                f"{proc.get('cpu_percent', 0):.1f}%",
                f"{proc.get('memory_percent', 0):.1f}%",
                str(proc.get('status', ''))
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.top_table.setItem(row, col, item)

    def update_resources(self):
        """更新资源监控"""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()

        self.cpu_chart.add_data(cpu)
        self.mem_chart.add_data(mem.percent)
        self.big_cpu_chart.add_data(cpu)
        self.big_mem_chart.add_data(mem.percent)

        # 更新监控的进程
        if hasattr(self, 'monitor_pid') and self.monitor_pid:
            try:
                proc = psutil.Process(self.monitor_pid)
                self.process_cpu_chart.add_data(proc.cpu_percent())
            except:
                pass

    def build_process_tree(self):
        """构建进程树"""
        self.process_tree.clear()

        # 构建父子关系
        children_map = defaultdict(list)
        all_pids = set()

        for proc in self.process_data:
            pid = proc.get('pid')
            ppid = proc.get('ppid', 0)
            all_pids.add(pid)
            children_map[ppid].append(proc)

        # 创建根节点（没有父进程或父进程不在列表中的）
        root_items = []
        for proc in self.process_data:
            ppid = proc.get('ppid', 0)
            if ppid == 0 or ppid not in all_pids:
                item = self.create_tree_item(proc)
                root_items.append(item)
                self.process_tree.addTopLevelItem(item)
                self.add_children(item, proc.get('pid'), children_map)

        self.process_tree.expandToDepth(1)

    def create_tree_item(self, proc):
        """创建树节点"""
        item = QTreeWidgetItem()
        item.setText(0, str(proc.get('name', '')))
        item.setText(1, str(proc.get('pid', '')))
        item.setText(2, f"{proc.get('cpu_percent', 0):.1f}%")
        item.setText(3, f"{proc.get('memory_percent', 0):.1f}%")
        item.setText(4, str(proc.get('status', '')))
        item.setText(5, str(proc.get('username', '') or 'N/A'))
        item.setData(0, Qt.ItemDataRole.UserRole, proc.get('pid'))

        # 颜色标记
        if proc.get('cpu_percent', 0) > 30:
            item.setForeground(2, QColor("#ff4757"))
        if proc.get('memory_percent', 0) > 30:
            item.setForeground(3, QColor("#ffa502"))

        return item

    def add_children(self, parent_item, parent_pid, children_map):
        """递归添加子进程"""
        for child in children_map.get(parent_pid, []):
            child_item = self.create_tree_item(child)
            parent_item.addChild(child_item)
            self.add_children(child_item, child.get('pid'), children_map)

    def on_process_selected(self, item):
        """选中进程"""
        row = item.row()
        pid_item = self.process_table.item(row, 0)
        if pid_item:
            try:
                pid = int(pid_item.text())
                self.detail_panel.update_detail(pid)
            except ValueError:
                pass

    def on_tree_item_clicked(self, item):
        """树节点点击"""
        pid = item.data(0, Qt.ItemDataRole.UserRole)
        if pid:
            self.detail_panel.update_detail(pid)

    def filter_processes(self):
        """过滤进程"""
        self.update_process_table()

    def kill_selected_process(self):
        """终止选中进程"""
        selected = self.process_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要终止的进程")
            return

        row = selected[0].row()
        pid = int(self.process_table.item(row, 0).text())
        name = self.process_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "确认终止",
            f"确定要终止进程 {name} (PID: {pid}) 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                proc = psutil.Process(pid)
                proc.kill()
                QMessageBox.information(self, "成功", f"进程 {name} 已终止")
                self.refresh_processes()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"终止进程失败: {e}")

    def set_process_priority(self):
        """设置进程优先级"""
        selected = self.process_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择进程")
            return

        row = selected[0].row()
        pid = int(self.process_table.item(row, 0).text())

        try:
            proc = psutil.Process(pid)
            current_nice = proc.nice()

            # 简单的优先级选择对话框
            msg = QMessageBox(self)
            msg.setWindowTitle("设置优先级")
            msg.setText(f"当前优先级: {current_nice}\n选择新的优先级:")

            priorities = [
                ("低 (-10)", -10),
                ("低于正常 (-5)", -5),
                ("正常 (0)", 0),
                ("高于正常 (5)", 5),
                ("高 (10)", 10),
                ("实时 (15)", 15),
            ]

            buttons = []
            for name, val in priorities:
                btn = msg.addButton(name, QMessageBox.ButtonRole.ActionRole)
                btn.setProperty("nice_value", val)

            msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked and clicked.property("nice_value") is not None:
                proc.nice(clicked.property("nice_value"))
                QMessageBox.information(self, "成功", "优先级已更新")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"设置优先级失败: {e}")

    def show_process_context_menu(self, pos):
        """进程右键菜单"""
        menu = QMenu(self)

        kill_action = QAction("❌ 终止进程", self)
        kill_action.triggered.connect(self.kill_selected_process)
        menu.addAction(kill_action)

        detail_action = QAction("📋 查看详情", self)
        detail_action.triggered.connect(lambda: self.show_selected_detail())
        menu.addAction(detail_action)

        menu.addSeparator()

        priority_action = QAction("⬆ 设置优先级", self)
        priority_action.triggered.connect(self.set_process_priority)
        menu.addAction(priority_action)

        menu.exec(QCursor.pos())

    def show_selected_detail(self):
        """显示选中进程详情"""
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            pid = int(self.process_table.item(row, 0).text())
            self.detail_panel.update_detail(pid)

    def export_processes(self):
        """导出进程列表"""
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "导出进程列表",
            f"processes_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "CSV 文件 (*.csv);;文本文件 (*.txt)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['PID', '进程名称', 'CPU %', '内存 %', '状态', '用户', '创建时间', '可执行文件'])
                    for proc in self.process_data:
                        try:
                            p = psutil.Process(proc['pid'])
                            exe = p.exe() if p.exe() else 'N/A'
                        except:
                            exe = 'N/A'
                        writer.writerow([
                            proc.get('pid', ''),
                            proc.get('name', ''),
                            f"{proc.get('cpu_percent', 0):.1f}",
                            f"{proc.get('memory_percent', 0):.1f}",
                            proc.get('status', ''),
                            proc.get('username', '') or 'N/A',
                            datetime.fromtimestamp(proc['create_time']).strftime('%Y-%m-%d %H:%M:%S') if proc.get('create_time') else 'N/A',
                            exe
                        ])
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"进程列表导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(f"{'PID':<8} {'进程名称':<25} {'CPU %':<8} {'内存 %':<8} {'状态':<12} {'用户':<20}\n")
                    f.write("-" * 80 + "\n")
                    for proc in self.process_data:
                        f.write(f"{proc.get('pid', ''):<8} "
                               f"{proc.get('name', ''):<25} "
                               f"{proc.get('cpu_percent', 0):<8.1f} "
                               f"{proc.get('memory_percent', 0):<8.1f} "
                               f"{proc.get('status', ''):<12} "
                               f"{str(proc.get('username', '') or 'N/A'):<20}\n")

            QMessageBox.information(self, "成功", f"进程列表已导出到:\n{file_path}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败: {e}")

    def start_process_monitor(self):
        """开始监控指定进程"""
        pid_text = self.monitor_pid_input.text().strip()
        if not pid_text:
            QMessageBox.warning(self, "警告", "请输入进程PID")
            return

        try:
            pid = int(pid_text)
            proc = psutil.Process(pid)
            self.monitor_pid = pid
            name = proc.name()
            QMessageBox.information(self, "成功", f"开始监控进程: {name} (PID: {pid})")
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "错误", f"进程 PID {pid_text} 不存在")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的PID数字")

    def load_startup_items(self):
        """加载启动项"""
        self.startup_table.setRowCount(0)

        try:
            import winreg

            startup_items = []

            # 注册表启动项位置
            registry_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "当前用户"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "所有用户"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "所有用户(一次)"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "当前用户(一次)"),
            ]

            for hive, path, location in registry_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({
                                'name': name,
                                'command': value,
                                'location': location,
                                'user': '当前用户' if hive == winreg.HKEY_CURRENT_USER else '系统',
                                'status': '启用'
                            })
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except WindowsError:
                    pass

            self.startup_table.setRowCount(len(startup_items))
            for row, item in enumerate(startup_items):
                self.startup_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.startup_table.setItem(row, 1, QTableWidgetItem(item['command']))
                self.startup_table.setItem(row, 2, QTableWidgetItem(item['location']))
                self.startup_table.setItem(row, 3, QTableWidgetItem(item['user']))
                self.startup_table.setItem(row, 4, QTableWidgetItem(item['status']))

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载启动项失败: {e}")

    def load_services(self):
        """加载Windows服务"""
        self.all_services = []
        self.service_count = 0

        for svc in psutil.win_service_iter():
            try:
                info = svc.as_dict()
                self.all_services.append(info)
            except:
                pass

        self.service_count = len(self.all_services)
        self.filter_services()

    def filter_services(self):
        """过滤服务"""
        if not hasattr(self, 'all_services'):
            self.load_services()
            return

        filter_text = self.service_filter.currentText()
        search_text = self.service_search.text().lower()

        filtered = []
        for svc in self.all_services:
            # 状态过滤
            status = svc.get('status', '')
            if filter_text == "运行中" and status != 'running':
                continue
            elif filter_text == "已停止" and status != 'stopped':
                continue
            elif filter_text == "启动中" and status != 'start_pending':
                continue

            # 搜索过滤
            if search_text:
                name = str(svc.get('name', '')).lower()
                display = str(svc.get('display_name', '')).lower()
                if search_text not in name and search_text not in display:
                    continue

            filtered.append(svc)

        self.service_table.setRowCount(len(filtered))
        for row, svc in enumerate(filtered):
            items = [
                str(svc.get('name', '')),
                str(svc.get('display_name', '')),
                str(svc.get('status', '')),
                str(svc.get('start_type', '')),
                str(svc.get('pid', '') or ''),
                str(svc.get('description', '') or '')
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.service_table.setItem(row, col, item)

                # 状态颜色
                if col == 2:
                    if text == 'running':
                        item.setForeground(QColor("#2ed573"))
                    elif text == 'stopped':
                        item.setForeground(QColor("#ff4757"))
                    elif 'pending' in text:
                        item.setForeground(QColor("#ffa502"))

        self.service_count_label.setText(f"共 {len(filtered)} 个服务")

    def show_service_context_menu(self, pos):
        """服务右键菜单"""
        selected = self.service_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        svc_name = self.service_table.item(row, 0).text()
        svc_status = self.service_table.item(row, 2).text()

        menu = QMenu(self)

        if svc_status == 'running':
            stop_action = QAction("⏹ 停止服务", self)
            stop_action.triggered.connect(lambda: self.manage_service(svc_name, 'stop'))
            menu.addAction(stop_action)

            restart_action = QAction("🔄 重启服务", self)
            restart_action.triggered.connect(lambda: self.manage_service(svc_name, 'restart'))
            menu.addAction(restart_action)
        elif svc_status == 'stopped':
            start_action = QAction("▶ 启动服务", self)
            start_action.triggered.connect(lambda: self.manage_service(svc_name, 'start'))
            menu.addAction(start_action)

        menu.exec(QCursor.pos())

    def manage_service(self, service_name, action):
        """管理服务"""
        try:
            svc = psutil.win_service(service_name)
            display_name = svc.name()

            if action == 'stop':
                svc.stop()
                QMessageBox.information(self, "成功", f"服务 {display_name} 已停止")
            elif action == 'start':
                svc.start()
                QMessageBox.information(self, "成功", f"服务 {display_name} 已启动")
            elif action == 'restart':
                svc.stop()
                time.sleep(1)
                svc.start()
                QMessageBox.information(self, "成功", f"服务 {display_name} 已重启")

            self.load_services()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"操作失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        self.resource_timer.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 设置深色主题
    app.setStyleSheet(DARK_STYLESHEET)

    # 设置应用程序图标（使用内置图标）
    app.setWindowIcon(QIcon())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
