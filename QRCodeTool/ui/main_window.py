"""主窗口"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QFont

from ui.generate_tab import GenerateTab
from ui.scan_tab import ScanTab
from ui.batch_tab import BatchTab
from ui.history_tab import HistoryTab
from core.qr_generator import QRGenerator
from core.qr_scanner import QRScanner
from core.history_manager import HistoryManager


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QRCodeTool - 专业二维码生成与识别工具")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 800)

        # 初始化核心模块
        self.qr_generator = QRGenerator()
        self.qr_scanner = QRScanner()
        self.history_manager = HistoryManager()

        self._init_ui()
        self._init_menu()
        self._init_statusbar()

    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d0d1a, stop:0.5 #111133, stop:1 #0d0d1a);
                border-bottom: 1px solid #2a2a3a;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        # Logo/标题
        logo_label = QLabel("🔲")
        logo_label.setFont(QFont("Segoe UI Emoji", 24))
        header_layout.addWidget(logo_label)

        title_text = QLabel("QRCodeTool")
        title_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_text.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        header_layout.addWidget(title_text)

        subtitle = QLabel("专业二维码生成与识别")
        subtitle.setStyleSheet("color: #667eea; font-size: 13px; background: transparent; border: none; margin-left: 8px;")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        # 版本
        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #555577; font-size: 12px; background: transparent; border: none;")
        header_layout.addWidget(ver)

        main_layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.generate_tab = GenerateTab(self.qr_generator, self.history_manager)
        self.scan_tab = ScanTab(self.qr_scanner)
        self.batch_tab = BatchTab(self.qr_generator, self.history_manager)
        self.history_tab = HistoryTab(self.history_manager)

        self.tabs.addTab(self.generate_tab, "✨ 生成二维码")
        self.tabs.addTab(self.scan_tab, "🔍 扫描识别")
        self.tabs.addTab(self.batch_tab, "📦 批量生成")
        self.tabs.addTab(self.history_tab, "📚 历史记录")

        # 切换标签时刷新历史
        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)

    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建二维码(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        scan_action = QAction("扫描识别(&S)", self)
        scan_action.setShortcut("Ctrl+O")
        scan_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        tools_menu.addAction(scan_action)

        batch_action = QAction("批量生成(&B)", self)
        batch_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        tools_menu.addAction(batch_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_statusbar(self):
        """初始化状态栏"""
        status = QStatusBar()
        status.setStyleSheet("QStatusBar { background-color: #0d0d1a; color: #666688; border-top: 1px solid #2a2a3a; }")
        status.showMessage("就绪")
        self.setStatusBar(status)

    def _on_tab_changed(self, index):
        """标签切换"""
        if index == 3:  # 历史标签页
            self.history_tab.refresh()

    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self,
            "关于 QRCodeTool",
            "<h2>🔲 QRCodeTool</h2>"
            "<p>版本 1.0.0</p>"
            "<p>一款专业、精美的二维码生成与识别桌面工具。</p>"
            "<p>功能特性：</p>"
            "<ul>"
            "<li>支持文本、URL、WiFi、vCard二维码生成</li>"
            "<li>自定义颜色、Logo、尺寸</li>"
            "<li>批量生成二维码</li>"
            "<li>从图片识别二维码</li>"
            "<li>历史记录管理</li>"
            "<li>导出为PNG/JPG/SVG</li>"
            "</ul>"
            "<p>基于 PyQt6 + qrcode + Pillow 构建</p>"
            "<p>© 2024 QRCodeTool. MIT License.</p>"
        )
