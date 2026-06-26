"""
ScreenRecorder 主入口
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from .main_window import MainWindow


def main():
    """应用程序主入口"""
    # 高DPI支持
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenRecorder")
    app.setApplicationDisplayName("屏幕录制工具")
    app.setOrganizationName("ScreenRecorder")
    
    # 设置全局样式
    app.setStyleSheet(get_stylesheet())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


def get_stylesheet():
    """全局深色主题样式表"""
    return """
    /* 全局样式 */
    QMainWindow, QWidget {
        background-color: #0a0a0a;
        color: #e0e0e0;
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 13px;
    }
    
    /* 主窗口 */
    QMainWindow {
        border: none;
    }
    
    /* 按钮基础样式 */
    QPushButton {
        background-color: #1a1a2e;
        color: #e0e0e0;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 13px;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background-color: #2a2a4a;
        border: 1px solid #667eea;
    }
    
    QPushButton:pressed {
        background-color: #667eea;
        color: white;
    }
    
    QPushButton:disabled {
        background-color: #111122;
        color: #555555;
        border: 1px solid #1a1a2e;
    }
    
    /* 主要操作按钮 */
    QPushButton#primaryButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #667eea, stop:1 #764ba2);
        color: white;
        border: none;
        font-size: 14px;
        padding: 12px 24px;
    }
    
    QPushButton#primaryButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #7b9cff, stop:1 #8b5fcf);
    }
    
    QPushButton#primaryButton:disabled {
        background: #1a1a2e;
        color: #555555;
    }
    
    /* 危险按钮 */
    QPushButton#dangerButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #ff6b6b, stop:1 #ee5a24);
        color: white;
        border: none;
    }
    
    QPushButton#dangerButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #ff8787, stop:1 #ff7043);
    }
    
    /* 卡片样式 */
    QFrame#card {
        background-color: #111122;
        border: 1px solid #1a1a3e;
        border-radius: 12px;
        padding: 16px;
    }
    
    QFrame#card:hover {
        border: 1px solid #2a2a5e;
    }
    
    /* 标签 */
    QLabel {
        color: #e0e0e0;
        font-size: 13px;
    }
    
    QLabel#titleLabel {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
    }
    
    QLabel#subtitleLabel {
        font-size: 12px;
        color: #888888;
    }
    
    QLabel#statusLabel {
        font-size: 14px;
        color: #667eea;
        font-weight: bold;
    }
    
    QLabel#timerLabel {
        font-size: 36px;
        font-weight: bold;
        color: #667eea;
        font-family: "Consolas", monospace;
    }
    
    /* 复选框 */
    QCheckBox {
        color: #e0e0e0;
        spacing: 8px;
        font-size: 13px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #2a2a4a;
        border-radius: 4px;
        background-color: #111122;
    }
    
    QCheckBox::indicator:checked {
        background-color: #667eea;
        border: 2px solid #667eea;
    }
    
    QCheckBox::indicator:hover {
        border: 2px solid #667eea;
    }
    
    /* 下拉框 */
    QComboBox {
        background-color: #111122;
        color: #e0e0e0;
        border: 1px solid #2a2a4a;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        min-width: 120px;
    }
    
    QComboBox:hover {
        border: 1px solid #667eea;
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
        background-color: #111122;
        color: #e0e0e0;
        border: 1px solid #2a2a4a;
        selection-background-color: #667eea;
        selection-color: white;
    }
    
    /* 滑块 */
    QSlider::groove:horizontal {
        height: 6px;
        background: #1a1a2e;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background: #667eea;
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }
    
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #667eea, stop:1 #764ba2);
        border-radius: 3px;
    }
    
    /* 进度条 */
    QProgressBar {
        background-color: #1a1a2e;
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #667eea, stop:1 #764ba2);
        border-radius: 4px;
    }
    
    /* 分组框 */
    QGroupBox {
        background-color: #111122;
        border: 1px solid #1a1a3e;
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 20px;
        font-weight: bold;
        color: #667eea;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px;
        color: #667eea;
    }
    
    /* 滚动区域 */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    /* 系统托盘菜单 */
    QMenu {
        background-color: #111122;
        color: #e0e0e0;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 5px;
    }
    
    QMenu::item {
        padding: 8px 25px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #667eea;
        color: white;
    }
    
    QMenu::separator {
        height: 1px;
        background-color: #2a2a4a;
        margin: 5px 10px;
    }
    
    /* 工具栏 */
    QToolBar {
        background-color: #0d0d1a;
        border-bottom: 1px solid #1a1a3e;
        spacing: 8px;
        padding: 5px;
    }
    
    /* 状态栏 */
    QStatusBar {
        background-color: #0d0d1a;
        color: #888888;
        border-top: 1px solid #1a1a3e;
        font-size: 12px;
    }
    
    /* 标签页 */
    QTabWidget::pane {
        border: 1px solid #1a1a3e;
        border-radius: 8px;
        background-color: #0a0a0a;
    }
    
    QTabBar::tab {
        background-color: #111122;
        color: #888888;
        border: 1px solid #1a1a3e;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    
    QTabBar::tab:selected {
        background-color: #1a1a2e;
        color: #667eea;
        border-bottom: 2px solid #667eea;
    }
    
    QTabBar::tab:hover {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    
    /* 工具提示 */
    QToolTip {
        background-color: #1a1a2e;
        color: #e0e0e0;
        border: 1px solid #667eea;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    """


if __name__ == "__main__":
    main()
