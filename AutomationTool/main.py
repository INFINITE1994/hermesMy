"""
AutomationTool - 专业桌面自动化工具
程序入口文件
"""

import sys
import os

# 确保能找到app模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from app.main_window import MainWindow


def main():
    """主函数 - 启动应用程序"""
    # 高DPI支持
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("AutomationTool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AutomationTool")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
