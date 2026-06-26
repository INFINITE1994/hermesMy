#!/usr/bin/env python3
"""
QRCodeTool - 专业二维码生成与识别工具
======================================

一款功能强大、界面精美的二维码桌面工具。
支持生成、扫描、批量处理、历史管理等功能。

使用方法:
    python main.py

依赖:
    pip install PyQt6 qrcode[pil] Pillow opencv-python numpy
"""

import sys
import os

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def load_stylesheet() -> str:
    """加载样式表"""
    qss_path = os.path.join(project_root, "resources", "styles", "theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    """主函数"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    # 高DPI支持
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("QRCodeTool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("QRCodeTool")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # 加载样式表
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        # 内置最小样式
        app.setStyleSheet("""
            QMainWindow { background-color: #0a0a0a; }
            QWidget { color: #e0e0e0; font-family: "Microsoft YaHei", sans-serif; }
            QTabWidget::pane { background-color: #111122; border: 1px solid #2a2a3a; border-radius: 8px; }
            QTabBar::tab { background-color: #1a1a2e; color: #8888aa; padding: 10px 20px; border-radius: 6px; }
            QTabBar::tab:selected { background-color: #111122; color: #ffffff; }
            QLineEdit, QTextEdit, QComboBox { background-color: #1a1a2e; border: 1px solid #2a2a3a; border-radius: 6px; padding: 8px; color: #ffffff; }
            QPushButton { background-color: #1a1a2e; border: 1px solid #2a2a3a; border-radius: 6px; padding: 8px 16px; color: #e0e0e0; }
            QPushButton:hover { border: 1px solid #667eea; }
        """)

    # 导入并创建主窗口
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
