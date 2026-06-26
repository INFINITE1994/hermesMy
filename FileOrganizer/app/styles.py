"""暗黑主题样式定义"""

# 颜色常量
BG_DARK = "#0a0a0a"
BG_CARD = "#111122"
BG_CARD_HOVER = "#161633"
BG_INPUT = "#0d0d1a"
BORDER = "#2a2a4a"
BORDER_FOCUS = "#667eea"
TEXT_PRIMARY = "#e8e8f0"
TEXT_SECONDARY = "#8888aa"
TEXT_MUTED = "#555577"
ACCENT_START = "#667eea"
ACCENT_END = "#764ba2"
DANGER = "#e74c3c"
DANGER_HOVER = "#c0392b"
SUCCESS = "#2ecc71"
WARNING = "#f39c12"
PROGRESS_BG = "#1a1a2e"
PROGRESS_CHUNK = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);"


def get_stylesheet() -> str:
    return f"""
    /* 主窗口 */
    QMainWindow, QWidget#central {{
        background-color: {BG_DARK};
    }}

    /* 通用 QWidget */
    QWidget {{
        color: {TEXT_PRIMARY};
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 13px;
    }}

    /* 标签 */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#subtitle {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
    }}
    QLabel#title {{
        font-size: 18px;
        font-weight: bold;
        color: {TEXT_PRIMARY};
    }}
    QLabel#logo {{
        font-size: 28px;
        font-weight: bold;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* 卡片容器 */
    QFrame#card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 16px;
    }}
    QFrame#card:hover {{
        border-color: {BORDER_FOCUS};
    }}

    /* 按钮基础 */
    QPushButton {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 500;
        font-size: 13px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {BG_CARD_HOVER};
        border-color: {BORDER_FOCUS};
    }}
    QPushButton:pressed {{
        background-color: {BG_DARK};
    }}
    QPushButton:disabled {{
        background-color: {BG_DARK};
        color: {TEXT_MUTED};
        border-color: {BG_DARK};
    }}

    /* 主按钮（渐变） */
    QPushButton#primary {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        color: white;
        border: none;
        font-weight: bold;
    }}
    QPushButton#primary:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #7b8ef8, stop:1 #8b5fc0);
    }}
    QPushButton#primary:disabled {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #444466, stop:1 #444466);
        color: {TEXT_MUTED};
    }}

    /* 危险按钮 */
    QPushButton#danger {{
        background-color: {DANGER};
        color: white;
        border: none;
    }}
    QPushButton#danger:hover {{
        background-color: {DANGER_HOVER};
    }}

    /* 成功按钮 */
    QPushButton#success {{
        background-color: {SUCCESS};
        color: white;
        border: none;
    }}

    /* 输入框 */
    QLineEdit, QSpinBox {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {ACCENT_START};
    }}
    QLineEdit:focus, QSpinBox:focus {{
        border-color: {BORDER_FOCUS};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 3px;
    }}

    /* 下拉框 */
    QComboBox {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        min-width: 120px;
    }}
    QComboBox:hover {{
        border-color: {BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT_START};
        selection-color: white;
        border-radius: 4px;
    }}

    /* 树形视图 */
    QTreeView {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QTreeView::item {{
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QTreeView::item:selected {{
        background-color: {ACCENT_START};
        color: white;
    }}
    QTreeView::item:hover {{
        background-color: {BG_CARD_HOVER};
    }}
    QTreeView::branch {{
        background: transparent;
    }}

    /* 表格 */
    QTableWidget {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        gridline-color: {BORDER};
        alternate-background-color: {BG_CARD};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border-bottom: 1px solid {BORDER};
    }}
    QTableWidget::item:selected {{
        background-color: {ACCENT_START};
        color: white;
    }}
    QHeaderView::section {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: none;
        border-bottom: 2px solid {BORDER};
        padding: 8px;
        font-weight: bold;
    }}

    /* 进度条 */
    QProgressBar {{
        background-color: {PROGRESS_BG};
        border: 1px solid {BORDER};
        border-radius: 8px;
        text-align: center;
        color: {TEXT_PRIMARY};
        font-size: 11px;
        min-height: 18px;
        max-height: 18px;
    }}
    QProgressBar::chunk {{
        background: {PROGRESS_CHUNK}
        border-radius: 7px;
    }}

    /* 文本编辑 */
    QTextEdit, QPlainTextEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
    }}

    /* 复选框 */
    QCheckBox {{
        color: {TEXT_PRIMARY};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {BORDER};
        border-radius: 4px;
        background-color: {BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT_START};
        border-color: {ACCENT_START};
    }}
    QCheckBox::indicator:hover {{
        border-color: {BORDER_FOCUS};
    }}

    /* 滚动条 */
    QScrollBar:vertical {{
        background: {BG_DARK};
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {BORDER_FOCUS};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {BG_DARK};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {BORDER_FOCUS};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* Splitter */
    QSplitter::handle {{
        background: {BORDER};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* 状态栏 */
    QStatusBar {{
        background-color: {BG_CARD};
        color: {TEXT_SECONDARY};
        border-top: 1px solid {BORDER};
        font-size: 11px;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background: {BG_DARK};
    }}
    QTabBar::tab {{
        background: {BG_CARD};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER};
        border-bottom: none;
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {BG_DARK};
        color: {TEXT_PRIMARY};
        border-bottom: 2px solid {ACCENT_START};
    }}
    QTabBar::tab:hover:!selected {{
        background: {BG_CARD_HOVER};
        color: {TEXT_PRIMARY};
    }}

    /* Tooltip */
    QToolTip {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* GroupBox */
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        color: {TEXT_PRIMARY};
    }}
    """
