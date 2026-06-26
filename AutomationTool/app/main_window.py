"""
AutomationTool - 主窗口
包含所有功能模块的选项卡界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from app.styles import get_stylesheet, BG_COLOR, CARD_COLOR, ACCENT_START, ACCENT_END, TEXT_COLOR, TEXT_SECONDARY
from app.modules import (
    MacroRecorderWidget,
    TaskSchedulerWidget,
    FileWatcherWidget,
    HotkeyManagerWidget,
    TextExpanderWidget,
    AutoClickerWidget,
    BatchRenameWidget,
    WorkflowBuilderWidget,
)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutomationTool - 专业桌面自动化工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 应用样式
        self.setStyleSheet(get_stylesheet())
        
        # 设置界面
        self._setup_ui()
        self._setup_statusbar()
        
        # 居中显示
        self._center_window()
    
    def _setup_ui(self):
        """设置主界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 选项卡部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(False)
        
        # 添加各个功能模块
        self._add_modules()
        
        main_layout.addWidget(self.tab_widget)
    
    def _create_header(self):
        """创建顶部标题栏"""
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CARD_COLOR}, stop:0.5 {CARD_COLOR}ee, stop:1 {CARD_COLOR});
                border-bottom: 1px solid #1a1a3a;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # 左侧 Logo 和标题
        left_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 28px;")
        left_layout.addWidget(icon_label)
        
        # 标题
        title_label = QLabel("AutomationTool")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            color: {ACCENT_START};
        """)
        left_layout.addWidget(title_label)
        
        # 版本
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; padding-top: 8px;")
        left_layout.addWidget(version_label)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # 右侧信息
        right_layout = QHBoxLayout()
        
        cpu_label = QLabel("💻 系统监控")
        cpu_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.cpu_value = QLabel("CPU: --%")
        self.cpu_value.setStyleSheet(f"color: {ACCENT_START}; font-size: 12px; font-weight: bold;")
        self.mem_value = QLabel("内存: --%")
        self.mem_value.setStyleSheet(f"color: {ACCENT_END}; font-size: 12px; font-weight: bold;")
        
        right_layout.addWidget(cpu_label)
        right_layout.addSpacing(12)
        right_layout.addWidget(self.cpu_value)
        right_layout.addSpacing(12)
        right_layout.addWidget(self.mem_value)
        
        layout.addLayout(right_layout)
        
        # 启动系统监控定时器
        self._start_system_monitor()
        
        return header
    
    def _start_system_monitor(self):
        """启动系统资源监控"""
        try:
            import psutil
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            self.cpu_value.setText("CPU: N/A")
            self.mem_value.setText("内存: N/A")
            return
        
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._update_system_info)
        self.monitor_timer.start(2000)  # 每2秒更新
        self._update_system_info()
    
    def _update_system_info(self):
        """更新系统信息"""
        if not self.psutil_available:
            return
        
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0)
            mem_percent = psutil.virtual_memory().percent
            
            # 根据使用率改变颜色
            cpu_color = "#4ade80" if cpu_percent < 70 else "#fbbf24" if cpu_percent < 90 else "#f87171"
            mem_color = "#4ade80" if mem_percent < 70 else "#fbbf24" if mem_percent < 90 else "#f87171"
            
            self.cpu_value.setText(f"CPU: {cpu_percent:.1f}%")
            self.cpu_value.setStyleSheet(f"color: {cpu_color}; font-size: 12px; font-weight: bold;")
            self.mem_value.setText(f"内存: {mem_percent:.1f}%")
            self.mem_value.setStyleSheet(f"color: {mem_color}; font-size: 12px; font-weight: bold;")
        except Exception:
            pass
    
    def _add_modules(self):
        """添加所有功能模块"""
        modules = [
            ("🎬 宏录制器", MacroRecorderWidget),
            ("⏰ 任务调度器", TaskSchedulerWidget),
            ("📁 文件监控器", FileWatcherWidget),
            ("⌨️ 快捷键管理器", HotkeyManagerWidget),
            ("📝 文本扩展器", TextExpanderWidget),
            ("🖱️ 自动点击器", AutoClickerWidget),
            ("📋 批量重命名", BatchRenameWidget),
            ("🔧 工作流构建器", WorkflowBuilderWidget),
        ]
        
        for name, widget_class in modules:
            widget = widget_class()
            self.tab_widget.addTab(widget, name)
    
    def _setup_statusbar(self):
        """设置状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        status_bar.addWidget(self.status_label)
        
        # 右侧信息
        right_label = QLabel("AutomationTool v1.0.0 | Python 3.10+ | PyQt6")
        right_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_bar.addPermanentWidget(right_label)
    
    def _center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = (geometry.width() - self.width()) // 2
            y = (geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有定时器
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
        
        # 接受关闭事件
        event.accept()
