"""ToolBox - Unified Launcher for HermesMy Tools."""
import sys
import os
import subprocess
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush

# ─── Version ───
VERSION = "1.0.0"
GITHUB_URL = "https://github.com/nousresearch/hermes-agent"

# ─── Tool registry ───
TOOLS = [
    {
        "name": "CleanMaster",
        "emoji": "🧹",
        "description": "系统清理大师\n清理垃圾文件、释放磁盘空间、优化系统性能",
        "path": r"G:\hermesMy\CleanMaster",
        "color": "#667eea",
    },
    {
        "name": "PDFMaster",
        "emoji": "📄",
        "description": "PDF 处理专家\n合并、拆分、转换、压缩 PDF 文档",
        "path": r"G:\hermesMy\PDFMaster",
        "color": "#f093fb",
    },
    {
        "name": "ImageBatch",
        "emoji": "🖼️",
        "description": "图片批处理工具\n批量转换格式、调整尺寸、添加水印",
        "path": r"G:\hermesMy\ImageBatch",
        "color": "#4facfe",
    },
    {
        "name": "FileOrganizer",
        "emoji": "📁",
        "description": "文件整理助手\n智能分类、批量重命名、整理目录结构",
        "path": r"G:\hermesMy\FileOrganizer",
        "color": "#43e97b",
    },
]

# ─── Stylesheet ───
STYLESHEET = """
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
}
QLabel {
    background: transparent;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #111122;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #333355;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #667eea;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


class ToolCard(QFrame):
    """A styled card widget representing a single tool."""

    def __init__(self, tool_info: dict, parent=None):
        super().__init__(parent)
        self.tool_info = tool_info
        self._hovered = False
        self.setFixedSize(280, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("toolCard")
        self.setStyleSheet(f"""
            QFrame#toolCard {{
                background-color: #111122;
                border: 1px solid #222244;
                border-radius: 16px;
                padding: 0px;
            }}
            QFrame#toolCard:hover {{
                border: 1px solid {self.tool_info['color']};
                background-color: #161633;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Emoji icon
        emoji_label = QLabel(self.tool_info["emoji"])
        emoji_label.setFont(QFont("Segoe UI Emoji", 36))
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji_label)

        # Tool name
        name_label = QLabel(self.tool_info["name"])
        name_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"color: {self.tool_info['color']};")
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(self.tool_info["description"])
        desc_label.setFont(QFont("Microsoft YaHei UI", 9))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #999999; line-height: 1.4;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Launch button
        self.launch_btn = QPushButton("🚀 启动")
        self.launch_btn.setFixedHeight(38)
        self.launch_btn.setFont(QFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))
        self.launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 19px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7b8ef7, stop:1 #8b5fbf);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5567d9, stop:1 #653a91);
            }}
        """)
        self.launch_btn.clicked.connect(self._launch_tool)
        layout.addWidget(self.launch_btn)

    def _launch_tool(self):
        tool_path = self.tool_info["path"]
        main_py = os.path.join(tool_path, "main.py")
        if not os.path.exists(main_py):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "启动失败",
                f"找不到工具入口文件:\n{main_py}\n\n请确认工具已正确安装。"
            )
            return
        try:
            subprocess.Popen(
                [sys.executable, main_py],
                cwd=tool_path,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0,
            )
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "启动失败",
                f"无法启动 {self.tool_info['name']}:\n{e}"
            )


class ToolBoxWindow(QMainWindow):
    """Main launcher window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HermesMy 工具箱")
        self.setMinimumSize(900, 700)
        self.resize(960, 740)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Header with gradient ───
        header = QFrame()
        header.setFixedHeight(160)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #667eea);
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 20, 40, 20)

        title = QLabel("🧰  HermesMy 工具箱")
        title.setFont(QFont("Microsoft YaHei UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("一站式工具管理平台 — 选择您需要的工具开始使用")
        subtitle.setFont(QFont("Microsoft YaHei UI", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8);")
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header)

        # ─── Scrollable content ───
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #0a0a0a; }")

        content = QWidget()
        content.setStyleSheet("background: #0a0a0a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(30)

        # ─── Section title: Tools ───
        section_label = QLabel("📋  可用工具")
        section_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        section_label.setStyleSheet("color: #cccccc;")
        content_layout.addWidget(section_label)

        # ─── Tool cards grid ───
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(24)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for idx, tool in enumerate(TOOLS):
            card = ToolCard(tool)
            row, col = divmod(idx, 2)
            grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(grid_widget)

        # ─── Spacer ───
        content_layout.addStretch()

        # ─── About section ───
        about_frame = QFrame()
        about_frame.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border: 1px solid #222244;
                border-radius: 12px;
            }
        """)
        about_layout = QVBoxLayout(about_frame)
        about_layout.setContentsMargins(24, 16, 24, 16)
        about_layout.setSpacing(8)

        about_title = QLabel("ℹ️  关于")
        about_title.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        about_title.setStyleSheet("color: #667eea;")
        about_layout.addWidget(about_title)

        about_text = QLabel(
            f"HermesMy 工具箱  v{VERSION}\n"
            "由 Nous Research 开发 · 基于 Hermes Agent 构建\n"
            "集成多款实用工具，提升日常工作效率"
        )
        about_text.setFont(QFont("Microsoft YaHei UI", 10))
        about_text.setStyleSheet("color: #888888;")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        github_btn = QPushButton("🔗  GitHub 项目主页")
        github_btn.setFixedWidth(200)
        github_btn.setFont(QFont("Microsoft YaHei UI", 10))
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #667eea;
                border: 1px solid #667eea;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.15);
            }
        """)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        about_layout.addWidget(github_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        content_layout.addWidget(about_frame)

        # ─── Footer ───
        footer = QLabel("© 2026 Nous Research  ·  HermesMy ToolBox")
        footer.setFont(QFont("Microsoft YaHei UI", 9))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #444444; padding: 8px;")
        content_layout.addWidget(footer)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette fallback
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#161633"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(STYLESHEET)

    window = ToolBoxWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
