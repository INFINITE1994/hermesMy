# -*- coding: utf-8 -*-
"""
Translator - 专业桌面翻译工具
支持多语言翻译、词典查询、批量翻译等功能
"""

import sys
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QComboBox, QTabWidget,
    QListWidget, QListWidgetItem, QLineEdit, QFrame, QSplitter,
    QMessageBox, QFileDialog, QProgressBar, QScrollArea,
    QGridLayout, QGroupBox, QSizePolicy, QStyledItemDelegate,
    QStyle, QStyleOptionViewItem, QAbstractItemDelegate
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, QParallelAnimationGroup
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QLinearGradient,
    QGradient, QPainter, QBrush, QPen, QPixmap, QAction,
    QClipboard, QKeySequence, QShortcut, QFontDatabase
)


# ============================================================================
# 常量定义
# ============================================================================

# 颜色主题
COLORS = {
    'bg': '#0a0a0a',
    'card': '#111122',
    'card_hover': '#1a1a35',
    'accent_start': '#667eea',
    'accent_end': '#764ba2',
    'text': '#ffffff',
    'text_secondary': '#a0a0b0',
    'text_dim': '#606070',
    'border': '#2a2a3a',
    'success': '#4ade80',
    'error': '#f87171',
    'warning': '#fbbf24',
    'input_bg': '#16162a',
    'button_bg': '#1e1e3a',
    'button_hover': '#2a2a4a',
    'scrollbar': '#3a3a5a',
    'scrollbar_hover': '#4a4a6a',
}

# 语言列表
LANGUAGES = {
    'auto': '自动检测',
    'zh': '中文',
    'en': '英语',
    'ja': '日语',
    'ko': '韩语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'ru': '俄语',
    'pt': '葡萄牙语',
    'it': '意大利语',
    'vi': '越南语',
    'th': '泰语',
    'ar': '阿拉伯语',
    'nl': '荷兰语',
    'pl': '波兰语',
    'sv': '瑞典语',
    'da': '丹麦语',
    'fi': '芬兰语',
    'nb': '挪威语',
    'el': '希腊语',
    'cs': '捷克语',
    'ro': '罗马尼亚语',
    'hu': '匈牙利语',
    'tr': '土耳其语',
    'hi': '印地语',
    'id': '印尼语',
    'ms': '马来语',
    'uk': '乌克兰语',
}

# 语言代码列表（用于Google Translate）
LANG_CODES = list(LANGUAGES.keys())


# ============================================================================
# 翻译引擎
# ============================================================================

class TranslationEngine:
    """翻译引擎 - 使用Google Translate免费API"""

    BASE_URL = "https://translate.googleapis.com/translate_a/single"

    @staticmethod
    def translate(text: str, source: str = 'auto', target: str = 'zh') -> dict:
        """
        翻译文本

        Args:
            text: 要翻译的文本
            source: 源语言代码
            target: 目标语言代码

        Returns:
            dict: 包含翻译结果的字典
        """
        if not text.strip():
            return {'success': False, 'error': '请输入要翻译的文本'}

        try:
            params = {
                'client': 'gtx',
                'sl': source,
                'tl': target,
                'dt': ['t', 'bd', 'ex', 'md', 'rw', 'rm', 'ss', 'at'],
                'q': text
            }

            url = f"{TranslationEngine.BASE_URL}?{urllib.parse.urlencode(params, doseq=True)}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            # 解析翻译结果
            translated_text = ''
            if data and data[0]:
                for item in data[0]:
                    if item and item[0]:
                        translated_text += item[0]

            # 解析详细信息
            result = {
                'success': True,
                'translated': translated_text,
                'source': source if source != 'auto' else (data[2] if len(data) > 2 else 'auto'),
                'target': target,
                'definitions': [],
                'examples': [],
                'synonyms': [],
                'related': []
            }

            # 解析词典数据
            if data and len(data) > 12 and data[12]:
                for entry in data[12]:
                    if len(entry) > 1:
                        pos = entry[0]  # 词性
                        terms = []
                        if len(entry) > 1 and entry[1]:
                            for term_group in entry[1]:
                                if len(term_group) > 2:
                                    terms.append({
                                        'word': term_group[0],
                                        'frequency': term_group[2] if len(term_group) > 2 else '',
                                        'synonyms': term_group[1] if len(term_group) > 1 else []
                                    })
                        if terms:
                            result['definitions'].append({
                                'pos': pos,
                                'terms': terms[:5]
                            })

            # 解析例句
            if data and len(data) > 13 and data[13]:
                for example in data[13]:
                    if len(example) > 0 and example[0]:
                        result['examples'].append(example[0])

            return result

        except Exception as e:
            return {'success': False, 'error': f'翻译失败: {str(e)}'}

    @staticmethod
    def detect_language(text: str) -> str:
        """检测语言"""
        try:
            result = TranslationEngine.translate(text, 'auto', 'en')
            if result['success']:
                return result.get('source', 'auto')
        except:
            pass
        return 'auto'


# ============================================================================
# 翻译工作线程
# ============================================================================

class TranslationWorker(QThread):
    """翻译工作线程"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

    def __init__(self, text, source='auto', target='zh'):
        super().__init__()
        self.text = text
        self.source = source
        self.target = target

    def run(self):
        self.progress.emit(30)
        result = TranslationEngine.translate(self.text, self.source, self.target)
        self.progress.emit(100)
        self.finished.emit(result)


# ============================================================================
# 自定义组件
# ============================================================================

class GradientButton(QPushButton):
    """渐变按钮"""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 创建渐变
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(COLORS['accent_start']))
        gradient.setColorAt(1, QColor(COLORS['accent_end']))

        # 绘制背景
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

        # 绘制文字
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class IconButton(QPushButton):
    """图标按钮"""
    def __init__(self, icon_text='', tooltip='', parent=None):
        super().__init__(icon_text, parent)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 36)


class CardWidget(QFrame):
    """卡片组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)


class SearchResultItem(QFrame):
    """搜索结果项"""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        label = QLabel(self.text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        layout.addWidget(label)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['input_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin: 2px 0;
            }}
            QFrame:hover {{
                background-color: {COLORS['card_hover']};
            }}
        """)


# ============================================================================
# 主窗口
# ============================================================================

class TranslatorWindow(QMainWindow):
    """翻译器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Translator - 专业翻译工具')
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 数据存储
        self.history = []
        self.favorites = []
        self.current_worker = None

        # 加载数据
        self.load_data()

        # 初始化UI
        self.init_ui()
        self.apply_theme()

        # 快捷键
        self.setup_shortcuts()

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题栏
        self.create_header(main_layout)

        # 主要内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # 左侧面板 - 翻译区域
        left_panel = self.create_translation_panel()
        content_layout.addWidget(left_panel, stretch=3)

        # 右侧面板 - 功能标签页
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, stretch=2)

        main_layout.addWidget(content_widget)

    def create_header(self, layout):
        """创建标题栏"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        # 标题
        title = QLabel('🌐 Translator')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Weight.Bold))
        title.setStyleSheet('color: white; background: transparent;')
        header_layout.addWidget(title)

        subtitle = QLabel('专业翻译工具')
        subtitle.setFont(QFont('Microsoft YaHei', 10))
        subtitle.setStyleSheet('color: rgba(255,255,255,0.8); background: transparent;')
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        # 状态信息
        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet('color: rgba(255,255,255,0.9); background: transparent;')
        header_layout.addWidget(self.status_label)

        layout.addWidget(header)

    def create_translation_panel(self):
        """创建翻译面板"""
        panel = CardWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        # 语言选择栏
        lang_bar = QWidget()
        lang_bar.setStyleSheet('background: transparent;')
        lang_layout = QHBoxLayout(lang_bar)
        lang_layout.setContentsMargins(0, 0, 0, 8)

        # 源语言
        self.source_lang = QComboBox()
        self.source_lang.setMinimumWidth(150)
        for code, name in LANGUAGES.items():
            self.source_lang.addItem(name, code)
        self.source_lang.setCurrentText('自动检测')
        lang_layout.addWidget(QLabel('源语言:'))
        lang_layout.addWidget(self.source_lang)

        # 交换按钮
        swap_btn = IconButton('⇄', '交换语言')
        swap_btn.clicked.connect(self.swap_languages)
        swap_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['accent_start']};
                border: 1px solid {COLORS['accent_start']};
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_start']};
                color: white;
            }}
        """)
        lang_layout.addWidget(swap_btn)

        # 目标语言
        self.target_lang = QComboBox()
        self.target_lang.setMinimumWidth(150)
        for code, name in LANGUAGES.items():
            if code != 'auto':
                self.target_lang.addItem(name, code)
        self.target_lang.setCurrentText('英语')
        lang_layout.addWidget(QLabel('目标语言:'))
        lang_layout.addWidget(self.target_lang)

        lang_layout.addStretch()
        layout.addWidget(lang_bar)

        # 输入区域
        input_group = QWidget()
        input_group.setStyleSheet('background: transparent;')
        input_layout = QVBoxLayout(input_group)

        input_header = QHBoxLayout()
        input_label = QLabel('📝 输入文本')
        input_label.setFont(QFont('Microsoft YaHei', 11, QFont.Weight.Bold))
        input_label.setStyleSheet(f'color: {COLORS["text"]}; background: transparent;')
        input_header.addWidget(input_label)

        # 字数统计
        self.char_count = QLabel('0 字符')
        self.char_count.setStyleSheet(f'color: {COLORS["text_secondary"]}; background: transparent;')
        input_header.addStretch()
        input_header.addWidget(self.char_count)

        input_layout.addLayout(input_header)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText('请输入要翻译的文本...\n\n支持 Ctrl+Enter 快速翻译')
        self.input_text.setMinimumHeight(150)
        self.input_text.textChanged.connect(self.update_char_count)
        input_layout.addWidget(self.input_text)

        # 翻译按钮栏
        btn_bar = QWidget()
        btn_bar.setStyleSheet('background: transparent;')
        btn_layout = QHBoxLayout(btn_bar)

        translate_btn = GradientButton('翻译')
        translate_btn.setFont(QFont('Microsoft YaHei', 11, QFont.Weight.Bold))
        translate_btn.clicked.connect(self.translate)
        btn_layout.addWidget(translate_btn)

        clear_btn = QPushButton('清空')
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_hover']};
                color: {COLORS['text']};
            }}
        """)
        clear_btn.clicked.connect(lambda: self.input_text.clear())
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['input_bg']};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
                border-radius: 2px;
            }}
        """)
        self.progress_bar.hide()
        btn_layout.addWidget(self.progress_bar)

        input_layout.addWidget(btn_bar)
        layout.addWidget(input_group)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f'background-color: {COLORS["border"]};')
        layout.addWidget(line)

        # 输出区域
        output_group = QWidget()
        output_group.setStyleSheet('background: transparent;')
        output_layout = QVBoxLayout(output_group)

        output_header = QHBoxLayout()
        output_label = QLabel('📄 翻译结果')
        output_label.setFont(QFont('Microsoft YaHei', 11, QFont.Weight.Bold))
        output_label.setStyleSheet(f'color: {COLORS["text"]}; background: transparent;')
        output_header.addWidget(output_label)

        output_header.addStretch()

        # 操作按钮
        copy_btn = IconButton('📋', '复制结果')
        copy_btn.clicked.connect(self.copy_result)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_start']};
            }}
        """)
        output_header.addWidget(copy_btn)

        fav_btn = IconButton('⭐', '收藏')
        fav_btn.clicked.connect(self.add_to_favorites)
        fav_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['warning']};
            }}
        """)
        output_header.addWidget(fav_btn)

        save_btn = IconButton('💾', '保存到文件')
        save_btn.clicked.connect(self.save_to_file)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success']};
            }}
        """)
        output_header.addWidget(save_btn)

        output_layout.addLayout(output_header)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        self.output_text.setPlaceholderText('翻译结果将显示在这里...')
        output_layout.addWidget(self.output_text)

        # 词典信息区域
        self.dict_area = QWidget()
        self.dict_area.setStyleSheet('background: transparent;')
        self.dict_layout = QVBoxLayout(self.dict_area)
        self.dict_layout.setContentsMargins(0, 8, 0, 0)
        self.dict_area.hide()
        output_layout.addWidget(self.dict_area)

        layout.addWidget(output_group)

        return panel

    def create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        panel.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 8px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['card']};
                color: {COLORS['accent_start']};
                border-bottom: 2px solid {COLORS['accent_start']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['card_hover']};
            }}
        """)

        # 历史记录标签页
        self.create_history_tab()

        # 收藏标签页
        self.create_favorites_tab()

        # 批量翻译标签页
        self.create_batch_tab()

        layout.addWidget(self.tab_widget)

        return panel

    def create_history_tab(self):
        """创建历史记录标签页"""
        history_widget = QWidget()
        history_widget.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(history_widget)
        layout.setSpacing(8)

        # 搜索框
        search_layout = QHBoxLayout()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText('🔍 搜索历史记录...')
        self.history_search.textChanged.connect(self.filter_history)
        self.history_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_start']};
            }}
        """)
        search_layout.addWidget(self.history_search)

        clear_history_btn = IconButton('🗑️', '清空历史')
        clear_history_btn.clicked.connect(self.clear_history)
        clear_history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
            }}
        """)
        search_layout.addWidget(clear_history_btn)
        layout.addLayout(search_layout)

        # 历史列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['card_hover']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_start']};
            }}
        """)
        self.history_list.itemDoubleClicked.connect(self.load_from_history)
        layout.addWidget(self.history_list)

        self.tab_widget.addTab(history_widget, '📜 历史记录')

    def create_favorites_tab(self):
        """创建收藏标签页"""
        favorites_widget = QWidget()
        favorites_widget.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(favorites_widget)
        layout.setSpacing(8)

        # 搜索框
        search_layout = QHBoxLayout()
        self.fav_search = QLineEdit()
        self.fav_search.setPlaceholderText('🔍 搜索收藏...')
        self.fav_search.textChanged.connect(self.filter_favorites)
        self.fav_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_start']};
            }}
        """)
        search_layout.addWidget(self.fav_search)

        export_btn = IconButton('📤', '导出收藏')
        export_btn.clicked.connect(self.export_favorites)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['accent_start']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_start']};
                color: white;
            }}
        """)
        search_layout.addWidget(export_btn)
        layout.addLayout(search_layout)

        # 收藏列表
        self.favorites_list = QListWidget()
        self.favorites_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['card_hover']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_start']};
            }}
        """)
        self.favorites_list.itemDoubleClicked.connect(self.load_from_favorites)
        layout.addWidget(self.favorites_list)

        self.tab_widget.addTab(favorites_widget, '⭐ 收藏')

    def create_batch_tab(self):
        """创建批量翻译标签页"""
        batch_widget = QWidget()
        batch_widget.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(batch_widget)
        layout.setSpacing(8)

        # 批量输入
        batch_input_label = QLabel('📝 批量输入（每行一条）')
        batch_input_label.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        batch_input_label.setStyleSheet(f'color: {COLORS["text"]}; background: transparent;')
        layout.addWidget(batch_input_label)

        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText('请输入要批量翻译的文本，每行一条...\n\n例如：\n你好\n世界\n早上好')
        self.batch_input.setMinimumHeight(120)
        self.batch_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.batch_input)

        # 批量翻译按钮
        batch_btn = GradientButton('开始批量翻译')
        batch_btn.clicked.connect(self.batch_translate)
        layout.addWidget(batch_btn)

        # 批量结果
        batch_result_label = QLabel('📄 翻译结果')
        batch_result_label.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        batch_result_label.setStyleSheet(f'color: {COLORS["text"]}; background: transparent;')
        layout.addWidget(batch_result_label)

        self.batch_output = QTextEdit()
        self.batch_output.setReadOnly(True)
        self.batch_output.setPlaceholderText('批量翻译结果将显示在这里...')
        self.batch_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.batch_output)

        # 复制批量结果
        copy_batch_btn = QPushButton('📋 复制全部结果')
        copy_batch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_hover']};
            }}
        """)
        copy_batch_btn.clicked.connect(lambda: self.copy_to_clipboard(self.batch_output.toPlainText()))
        layout.addWidget(copy_batch_btn)

        self.tab_widget.addTab(batch_widget, '📦 批量翻译')

    def apply_theme(self):
        """应用主题样式"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg']};
            }}
            QWidget {{
                color: {COLORS['text']};
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['accent_start']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['card']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['accent_start']};
            }}
            QTextEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['accent_start']};
            }}
            QLabel {{
                color: {COLORS['text']};
                background: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['scrollbar']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background-color: {COLORS['bg']};
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {COLORS['scrollbar']};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {COLORS['scrollbar_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)

    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+Enter 翻译
        translate_shortcut = QShortcut(QKeySequence('Ctrl+Return'), self)
        translate_shortcut.activated.connect(self.translate)

        # Ctrl+Shift+C 复制结果
        copy_shortcut = QShortcut(QKeySequence('Ctrl+Shift+C'), self)
        copy_shortcut.activated.connect(self.copy_result)

        # Ctrl+S 保存
        save_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        save_shortcut.activated.connect(self.save_to_file)

    # ========================================================================
    # 翻译功能
    # ========================================================================

    def translate(self):
        """执行翻译"""
        text = self.input_text.toPlainText().strip()
        if not text:
            self.show_status('请输入要翻译的文本', 'warning')
            return

        source = self.source_lang.currentData()
        target = self.target_lang.currentData()

        # 显示进度条
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_label.setText('翻译中...')
        self.status_label.setStyleSheet('color: rgba(255,255,255,0.9); background: transparent;')

        # 创建工作线程
        self.current_worker = TranslationWorker(text, source, target)
        self.current_worker.finished.connect(self.on_translation_complete)
        self.current_worker.progress.connect(self.progress_bar.setValue)
        self.current_worker.start()

    def on_translation_complete(self, result):
        """翻译完成回调"""
        self.progress_bar.hide()

        if result['success']:
            self.output_text.setText(result['translated'])

            # 显示词典信息
            self.show_dictionary_info(result)

            # 添加到历史
            self.add_to_history(
                self.input_text.toPlainText(),
                result['translated'],
                result.get('source', 'auto'),
                result.get('target', 'zh')
            )

            self.show_status('翻译完成', 'success')
        else:
            self.output_text.setText(f'错误: {result["error"]}')
            self.show_status('翻译失败', 'error')

    def show_dictionary_info(self, result):
        """显示词典信息"""
        # 清空词典区域
        while self.dict_layout.count():
            child = self.dict_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        has_info = False

        # 显示词典定义
        if result.get('definitions'):
            has_info = True
            dict_label = QLabel('📖 词典释义')
            dict_label.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
            dict_label.setStyleSheet(f'color: {COLORS["accent_start"]}; background: transparent;')
            self.dict_layout.addWidget(dict_label)

            for defn in result['definitions'][:3]:
                pos_label = QLabel(f'【{defn["pos"]}】')
                pos_label.setStyleSheet(f'color: {COLORS["warning"]}; background: transparent;')
                self.dict_layout.addWidget(pos_label)

                for term in defn['terms'][:3]:
                    term_text = f'  • {term["word"]}'
                    if term.get('synonyms'):
                        term_text += f' (同义词: {", ".join(term["synonyms"][:3])})'
                    term_label = QLabel(term_text)
                    term_label.setStyleSheet(f'color: {COLORS["text_secondary"]}; background: transparent;')
                    term_label.setWordWrap(True)
                    self.dict_layout.addWidget(term_label)

        # 显示例句
        if result.get('examples'):
            has_info = True
            example_label = QLabel('💡 例句')
            example_label.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
            example_label.setStyleSheet(f'color: {COLORS["success"]}; background: transparent;')
            self.dict_layout.addWidget(example_label)

            for example in result['examples'][:2]:
                # 清理HTML标签
                clean_example = re.sub(r'<[^>]+>', '', example)
                ex_label = QLabel(f'  • {clean_example}')
                ex_label.setStyleSheet(f'color: {COLORS["text_secondary"]}; background: transparent;')
                ex_label.setWordWrap(True)
                self.dict_layout.addWidget(ex_label)

        if has_info:
            self.dict_area.show()
        else:
            self.dict_area.hide()

    def swap_languages(self):
        """交换源语言和目标语言"""
        source_idx = self.source_lang.currentIndex()
        target_idx = self.target_lang.currentIndex()

        # 获取当前语言代码
        source_code = self.source_lang.currentData()
        target_code = self.target_lang.currentData()

        # 不能交换自动检测
        if source_code == 'auto':
            self.show_status('自动检测模式下无法交换语言', 'warning')
            return

        # 交换
        self.source_lang.setCurrentIndex(self.target_lang.currentIndex() + 1)  # +1 因为源语言有auto
        self.target_lang.setCurrentIndex(source_idx - 1)  # -1 因为目标语言没有auto

        # 交换文本
        input_text = self.input_text.toPlainText()
        output_text = self.output_text.toPlainText()
        self.input_text.setText(output_text)
        self.output_text.setText(input_text)

        self.show_status('语言已交换', 'info')

    # ========================================================================
    # 历史记录功能
    # ========================================================================

    def add_to_history(self, source, translated, source_lang, target_lang):
        """添加到历史记录"""
        entry = {
            'source': source,
            'translated': translated,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 避免重复
        if not any(h['source'] == source and h['translated'] == translated for h in self.history):
            self.history.insert(0, entry)
            self.update_history_list()
            self.save_data()

    def update_history_list(self, filter_text=''):
        """更新历史列表"""
        self.history_list.clear()

        for entry in self.history:
            source_preview = entry['source'][:50] + ('...' if len(entry['source']) > 50 else '')
            translated_preview = entry['translated'][:50] + ('...' if len(entry['translated']) > 50 else '')

            display_text = f"{source_preview}\n→ {translated_preview}\n{entry['timestamp']}"

            if filter_text and filter_text.lower() not in display_text.lower():
                continue

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.history_list.addItem(item)

    def filter_history(self, text):
        """过滤历史记录"""
        self.update_history_list(text)

    def load_from_history(self, item):
        """从历史记录加载"""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            self.input_text.setText(entry['source'])
            self.output_text.setText(entry['translated'])

            # 设置语言
            source_idx = self.source_lang.findData(entry['source_lang'])
            if source_idx >= 0:
                self.source_lang.setCurrentIndex(source_idx)

            target_idx = self.target_lang.findData(entry['target_lang'])
            if target_idx >= 0:
                self.target_lang.setCurrentIndex(target_idx)

    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, '确认清空',
            '确定要清空所有历史记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.history_list.clear()
            self.save_data()
            self.show_status('历史记录已清空', 'info')

    # ========================================================================
    # 收藏功能
    # ========================================================================

    def add_to_favorites(self):
        """添加到收藏"""
        source = self.input_text.toPlainText().strip()
        translated = self.output_text.toPlainText().strip()

        if not source or not translated:
            self.show_status('没有可收藏的翻译', 'warning')
            return

        entry = {
            'source': source,
            'translated': translated,
            'source_lang': self.source_lang.currentData(),
            'target_lang': self.target_lang.currentData(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 避免重复
        if not any(f['source'] == source and f['translated'] == translated for f in self.favorites):
            self.favorites.insert(0, entry)
            self.update_favorites_list()
            self.save_data()
            self.show_status('已添加到收藏', 'success')
        else:
            self.show_status('已在收藏中', 'info')

    def update_favorites_list(self, filter_text=''):
        """更新收藏列表"""
        self.favorites_list.clear()

        for entry in self.favorites:
            source_preview = entry['source'][:50] + ('...' if len(entry['source']) > 50 else '')
            translated_preview = entry['translated'][:50] + ('...' if len(entry['translated']) > 50 else '')

            display_text = f"⭐ {source_preview}\n→ {translated_preview}\n{entry['timestamp']}"

            if filter_text and filter_text.lower() not in display_text.lower():
                continue

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.favorites_list.addItem(item)

    def filter_favorites(self, text):
        """过滤收藏"""
        self.update_favorites_list(text)

    def load_from_favorites(self, item):
        """从收藏加载"""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            self.input_text.setText(entry['source'])
            self.output_text.setText(entry['translated'])

            source_idx = self.source_lang.findData(entry['source_lang'])
            if source_idx >= 0:
                self.source_lang.setCurrentIndex(source_idx)

            target_idx = self.target_lang.findData(entry['target_lang'])
            if target_idx >= 0:
                self.target_lang.setCurrentIndex(target_idx)

    def export_favorites(self):
        """导出收藏"""
        if not self.favorites:
            self.show_status('没有收藏可导出', 'warning')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出收藏', 'favorites.json',
            'JSON文件 (*.json);;文本文件 (*.txt)'
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.favorites, f, ensure_ascii=False, indent=2)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for entry in self.favorites:
                            f.write(f"原文: {entry['source']}\n")
                            f.write(f"译文: {entry['translated']}\n")
                            f.write(f"时间: {entry['timestamp']}\n")
                            f.write('-' * 50 + '\n')

                self.show_status(f'收藏已导出到: {file_path}', 'success')
            except Exception as e:
                self.show_status(f'导出失败: {str(e)}', 'error')

    # ========================================================================
    # 批量翻译功能
    # ========================================================================

    def batch_translate(self):
        """批量翻译"""
        text = self.batch_input.toPlainText().strip()
        if not text:
            self.show_status('请输入要批量翻译的文本', 'warning')
            return

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            self.show_status('没有有效的文本行', 'warning')
            return

        self.batch_output.clear()
        self.status_label.setText(f'批量翻译中... (0/{len(lines)})')

        source = self.source_lang.currentData()
        target = self.target_lang.currentData()

        # 逐行翻译
        results = []
        for i, line in enumerate(lines):
            result = TranslationEngine.translate(line, source, target)
            if result['success']:
                results.append(f"{line}\n→ {result['translated']}\n")
            else:
                results.append(f"{line}\n→ [翻译失败: {result['error']}]\n")

            self.status_label.setText(f'批量翻译中... ({i+1}/{len(lines)})')
            QApplication.processEvents()

        self.batch_output.setText('\n'.join(results))
        self.show_status(f'批量翻译完成，共 {len(lines)} 条', 'success')

    # ========================================================================
    # 工具功能
    # ========================================================================

    def copy_result(self):
        """复制翻译结果"""
        text = self.output_text.toPlainText()
        if text:
            self.copy_to_clipboard(text)
        else:
            self.show_status('没有可复制的内容', 'warning')

    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.show_status('已复制到剪贴板', 'success')

    def save_to_file(self):
        """保存到文件"""
        source = self.input_text.toPlainText()
        translated = self.output_text.toPlainText()

        if not source or not translated:
            self.show_status('没有可保存的内容', 'warning')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存翻译', 'translation.txt',
            '文本文件 (*.txt);;所有文件 (*.*)'
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"原文:\n{source}\n\n")
                    f.write(f"译文:\n{translated}\n\n")
                    f.write(f"翻译时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.show_status(f'已保存到: {file_path}', 'success')
            except Exception as e:
                self.show_status(f'保存失败: {str(e)}', 'error')

    def update_char_count(self):
        """更新字数统计"""
        count = len(self.input_text.toPlainText())
        self.char_count.setText(f'{count} 字符')

    def show_status(self, message, level='info'):
        """显示状态信息"""
        color_map = {
            'info': COLORS['text'],
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'error': COLORS['error']
        }

        self.status_label.setText(message)
        self.status_label.setStyleSheet(f'color: {color_map.get(level, COLORS["text"])}; background: transparent;')

        # 3秒后恢复
        QTimer.singleShot(3000, lambda: self.status_label.setText('就绪'))

    # ========================================================================
    # 数据持久化
    # ========================================================================

    def get_data_dir(self):
        """获取数据目录"""
        data_dir = Path.home() / '.translator'
        data_dir.mkdir(exist_ok=True)
        return data_dir

    def save_data(self):
        """保存数据"""
        data_dir = self.get_data_dir()

        try:
            with open(data_dir / 'history.json', 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)

            with open(data_dir / 'favorites.json', 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存数据失败: {e}')

    def load_data(self):
        """加载数据"""
        data_dir = self.get_data_dir()

        try:
            history_file = data_dir / 'history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)

            favorites_file = data_dir / 'favorites.json'
            if favorites_file.exists():
                with open(favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
        except Exception as e:
            print(f'加载数据失败: {e}')


# ============================================================================
# 应用入口
# ============================================================================

def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用字体
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)

    # 创建主窗口
    window = TranslatorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
