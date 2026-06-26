#!/usr/bin/env python3
"""FileOrganizer - 暗黑风格文件整理工具

现代化 Windows 桌面文件整理工具，支持：
- 按类型/日期自动分类文件
- 重复文件查找（MD5 哈希）
- 批量重命名（顺序编号/日期/自定义模式）
- 空文件夹查找与清理
- 大文件查找
- 预览与撤销支持
"""
import sys
import os

# 确保 app 包可以被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    # 高 DPI 支持
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("FileOrganizer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FileOrganizer")

    # 设置默认字体
    font = QFont("Microsoft YaHei UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    from app.ui import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
