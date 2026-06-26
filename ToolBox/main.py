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
    {
        "name": "ClipboardManager",
        "emoji": "📋",
        "description": "剪贴板管理器\n记录剪贴板历史、搜索、置顶、分类",
        "path": r"G:\hermesMy\ClipboardManager",
        "color": "#ffa500",
    },
    {
        "name": "QuickNote",
        "emoji": "📝",
        "description": "快速笔记\nMarkdown编辑器、笔记本管理、标签、导出",
        "path": r"G:\hermesMy\QuickNote",
        "color": "#ff6b6b",
    },
    {
        "name": "PasswordManager",
        "emoji": "🔐",
        "description": "密码管理器\nAES-256加密、密码生成、分类管理",
        "path": r"G:\hermesMy\PasswordManager",
        "color": "#2ecc71",
    },
    {
        "name": "SysMonitor",
        "emoji": "📊",
        "description": "系统监控\nCPU/内存/磁盘/网络实时监控",
        "path": r"G:\hermesMy\SysMonitor",
        "color": "#e74c3c",
    },
    {
        "name": "NetTools",
        "emoji": "🌐",
        "description": "网络工具箱\nPing/端口扫描/DNS/测速/路由追踪",
        "path": r"G:\hermesMy\NetTools",
        "color": "#3498db",
    },
    {
        "name": "QRCodeTool",
        "emoji": "📱",
        "description": "二维码工具\n生成/扫描/批量生成二维码",
        "path": r"G:\hermesMy\QRCodeTool",
        "color": "#9b59b6",
    },
    {
        "name": "ColorPicker",
        "emoji": "🎨",
        "description": "取色器\n屏幕取色/色轮/调色板/对比度检查",
        "path": r"G:\hermesMy\ColorPicker",
        "color": "#e67e22",
    },
    {
        "name": "TextTools",
        "emoji": "📝",
        "description": "文本工具箱\nJSON格式化/Base64/URL编解码/哈希/正则",
        "path": r"G:\hermesMy\TextTools",
        "color": "#1abc9c",
    },
    {
        "name": "UnitConverter",
        "emoji": "📐",
        "description": "单位换算\n长度/重量/温度/面积/体积/速度/数据/时间/货币",
        "path": r"G:\hermesMy\UnitConverter",
        "color": "#f39c12",
    },
    {
        "name": "MarkdownEditor",
        "emoji": "✏️",
        "description": "Markdown编辑器\n实时预览/语法高亮/导出HTML/PDF",
        "path": r"G:\hermesMy\MarkdownEditor",
        "color": "#e74c3c",
    },
    {
        "name": "DiskAnalyzer",
        "emoji": "💾",
        "description": "磁盘分析器\n树状图/文件类型分析/大文件查找",
        "path": r"G:\hermesMy\DiskAnalyzer",
        "color": "#2ecc71",
    },
    {
        "name": "GIFMaker",
        "emoji": "🎬",
        "description": "GIF制作工具\n视频转GIF/图片合成/屏幕录制/编辑优化",
        "path": r"G:\hermesMy\GIFMaker",
        "color": "#e91e63",
    },
    {
        "name": "AudioTools",
        "emoji": "🎵",
        "description": "音频工具箱\n格式转换/裁剪/合并/音量调节/录制",
        "path": r"G:\hermesMy\AudioTools",
        "color": "#ff9800",
    },
    {
        "name": "RegexTester",
        "emoji": "🔍",
        "description": "正则测试器\n实时匹配/常用模式/解释/保存",
        "path": r"G:\hermesMy\RegexTester",
        "color": "#9c27b0",
    },
    {
        "name": "ScreenshotTool",
        "emoji": "📸",
        "description": "截图工具\n全屏/区域/窗口截图/标注/模糊",
        "path": r"G:\hermesMy\ScreenshotTool",
        "color": "#00bcd4",
    },
    {
        "name": "TimerTools",
        "emoji": "⏰",
        "description": "计时器工具箱\n倒计时/秒表/世界时钟/番茄钟/闹钟",
        "path": r"G:\hermesMy\TimerTools",
        "color": "#ff5722",
    },
    {
        "name": "CryptoTools",
        "emoji": "🔒",
        "description": "加密工具箱\n文本加密/文件加密/哈希/密码生成/JWT",
        "path": r"G:\hermesMy\CryptoTools",
        "color": "#607d8b",
    },
    {
        "name": "VideoTools",
        "emoji": "🎬",
        "description": "视频工具箱\n格式转换/裁剪/合并/压缩/音频提取",
        "path": r"G:\hermesMy\VideoTools",
        "color": "#ff4081",
    },
    {
        "name": "WebScraper",
        "emoji": "🕷️",
        "description": "网页抓取器\nURL抓取/链接提取/图片下载/批量抓取",
        "path": r"G:\hermesMy\WebScraper",
        "color": "#4caf50",
    },
    {
        "name": "SystemInfo",
        "emoji": "💻",
        "description": "系统信息\nCPU/内存/磁盘/显卡/网络/主板详情",
        "path": r"G:\hermesMy\SystemInfo",
        "color": "#2196f3",
    },
    {
        "name": "EmojiPicker",
        "emoji": "😀",
        "description": "Emoji选择器\n搜索/分类/收藏/最近使用",
        "path": r"G:\hermesMy\EmojiPicker",
        "color": "#ffc107",
    },
    {
        "name": "WeatherApp",
        "emoji": "🌤️",
        "description": "天气预报\n实时天气/7天预报/空气质量/日出日落",
        "path": r"G:\hermesMy\WeatherApp",
        "color": "#03a9f4",
    },
    {
        "name": "Translator",
        "emoji": "🌍",
        "description": "翻译工具\n多语言翻译/自动检测/历史记录/批量翻译",
        "path": r"G:\hermesMy\Translator",
        "color": "#8bc34a",
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
