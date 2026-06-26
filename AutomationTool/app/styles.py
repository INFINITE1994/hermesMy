"""
AutomationTool - 主题样式
深色主题配色方案
"""

# 颜色常量
BG_COLOR = "#0a0a0a"
CARD_COLOR = "#111122"
CARD_BORDER = "#1a1a3a"
ACCENT_START = "#667eea"
ACCENT_END = "#764ba2"
TEXT_COLOR = "#e0e0e0"
TEXT_SECONDARY = "#8888aa"
HOVER_COLOR = "#1a1a3a"
PRESSED_COLOR = "#0d0d1a"
INPUT_BG = "#0a0a1a"
INPUT_BORDER = "#2a2a4a"
SUCCESS_COLOR = "#4ade80"
WARNING_COLOR = "#fbbf24"
ERROR_COLOR = "#f87171"
SCROLLBAR_BG = "#111122"
SCROLLBAR_HANDLE = "#2a2a4a"


def get_stylesheet():
    """返回应用程序的完整样式表"""
    return f"""
    /* 全局样式 */
    QMainWindow {{
        background-color: {BG_COLOR};
    }}
    
    QWidget {{
        background-color: {BG_COLOR};
        color: {TEXT_COLOR};
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    }}
    
    /* 选项卡样式 */
    QTabWidget::pane {{
        border: 1px solid {CARD_BORDER};
        background-color: {BG_COLOR};
        border-radius: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {CARD_COLOR};
        color: {TEXT_SECONDARY};
        padding: 12px 24px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 13px;
        min-width: 80px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {BG_COLOR};
        color: {TEXT_COLOR};
        border-bottom: 2px solid {ACCENT_START};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {HOVER_COLOR};
        color: {TEXT_COLOR};
    }}
    
    /* 按钮样式 */
    QPushButton {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}dd, stop:1 {ACCENT_END}dd);
    }}
    
    QPushButton:pressed {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}aa, stop:1 {ACCENT_END}aa);
    }}
    
    QPushButton:disabled {{
        background-color: {CARD_COLOR};
        color: {TEXT_SECONDARY};
    }}
    
    /* 输入框样式 */
    QLineEdit, QTextEdit, QSpinBox, QComboBox {{
        background-color: {INPUT_BG};
        border: 1px solid {INPUT_BORDER};
        color: {TEXT_COLOR};
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {ACCENT_START};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {TEXT_SECONDARY};
        margin-right: 10px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        color: {TEXT_COLOR};
        selection-background-color: {ACCENT_START};
    }}
    
    /* 列表和表格样式 */
    QListWidget, QTableWidget, QTreeWidget {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 4px;
        alternate-background-color: {CARD_COLOR};
    }}
    
    QListWidget::item, QTableWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    
    QListWidget::item:selected, QTableWidget::item:selected {{
        background-color: {ACCENT_START}33;
        color: {TEXT_COLOR};
    }}
    
    QListWidget::item:hover, QTableWidget::item:hover {{
        background-color: {HOVER_COLOR};
    }}
    
    QHeaderView::section {{
        background-color: {CARD_COLOR};
        color: {TEXT_SECONDARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {CARD_BORDER};
        font-weight: bold;
    }}
    
    /* 分组框样式 */
    QGroupBox {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 20px;
        font-size: 13px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {ACCENT_START};
    }}
    
    /* 标签样式 */
    QLabel {{
        color: {TEXT_COLOR};
        font-size: 13px;
    }}
    
    QLabel[class="title"] {{
        font-size: 18px;
        font-weight: bold;
        color: {TEXT_COLOR};
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 14px;
        color: {TEXT_SECONDARY};
    }}
    
    /* 复选框样式 */
    QCheckBox {{
        spacing: 8px;
        font-size: 13px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {INPUT_BORDER};
        background-color: {INPUT_BG};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {ACCENT_START};
        border-color: {ACCENT_START};
    }}
    
    /* 滚动条样式 */
    QScrollBar:vertical {{
        background-color: {SCROLLBAR_BG};
        width: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {SCROLLBAR_HANDLE};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {ACCENT_START};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {SCROLLBAR_BG};
        height: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {SCROLLBAR_HANDLE};
        border-radius: 5px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {ACCENT_START};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* 进度条样式 */
    QProgressBar {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        border-radius: 6px;
        text-align: center;
        color: {TEXT_COLOR};
        height: 20px;
    }}
    
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        border-radius: 5px;
    }}
    
    /* 状态栏样式 */
    QStatusBar {{
        background-color: {CARD_COLOR};
        color: {TEXT_SECONDARY};
        border-top: 1px solid {CARD_BORDER};
        font-size: 12px;
    }}
    
    /* 工具栏样式 */
    QToolBar {{
        background-color: {CARD_COLOR};
        border-bottom: 1px solid {CARD_BORDER};
        spacing: 6px;
        padding: 4px;
    }}
    
    /* 菜单样式 */
    QMenuBar {{
        background-color: {CARD_COLOR};
        color: {TEXT_COLOR};
        border-bottom: 1px solid {CARD_BORDER};
    }}
    
    QMenuBar::item:selected {{
        background-color: {HOVER_COLOR};
    }}
    
    QMenu {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        color: {TEXT_COLOR};
    }}
    
    QMenu::item:selected {{
        background-color: {ACCENT_START}33;
    }}
    
    /* 分割线 */
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{
        color: {CARD_BORDER};
    }}
    
    /* 日期时间编辑 */
    QDateTimeEdit {{
        background-color: {INPUT_BG};
        border: 1px solid {INPUT_BORDER};
        color: {TEXT_COLOR};
        padding: 8px 12px;
        border-radius: 6px;
    }}
    
    QDateTimeEdit::drop-down {{
        border: none;
        width: 30px;
    }}
    """


def get_card_style():
    """返回卡片样式"""
    return f"""
    QFrame {{
        background-color: {CARD_COLOR};
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 16px;
    }}
    """


def get_title_label_style():
    """返回标题标签样式"""
    return f"""
    QLabel {{
        font-size: 20px;
        font-weight: bold;
        color: {TEXT_COLOR};
        padding: 8px 0;
    }}
    """


def get_description_label_style():
    """返回描述标签样式"""
    return f"""
    QLabel {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
        padding: 4px 0;
    }}
    """


def get_accent_button_style():
    """返回强调按钮样式"""
    return f"""
    QPushButton {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_START}dd, stop:1 {ACCENT_END}dd);
    }}
    """


def get_danger_button_style():
    """返回危险按钮样式"""
    return f"""
    QPushButton {{
        background-color: {ERROR_COLOR};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {ERROR_COLOR}dd;
    }}
    """


def get_success_button_style():
    """返回成功按钮样式"""
    return f"""
    QPushButton {{
        background-color: {SUCCESS_COLOR};
        color: #000000;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {SUCCESS_COLOR}dd;
    }}
    """


def get_secondary_button_style():
    """返回次要按钮样式"""
    return f"""
    QPushButton {{
        background-color: {CARD_COLOR};
        color: {TEXT_COLOR};
        border: 1px solid {CARD_BORDER};
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 13px;
    }}
    
    QPushButton:hover {{
        background-color: {HOVER_COLOR};
        border-color: {ACCENT_START};
    }}
    """
