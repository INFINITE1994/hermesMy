#!/usr/bin/env python3
"""
UnitConverter - 专业单位换算器
支持 9 大类单位换算，深色主题，中文界面
"""

import sys
import json
from functools import partial
from urllib.request import urlopen, Request
from urllib.error import URLError

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFrame, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QStackedWidget, QSpacerItem
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QThread, pyqtSignal, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush, QIcon, QPen, QPixmap
)


# ============================================================
# 单位转换数据
# ============================================================

CATEGORIES = [
    {"name": "长度", "icon": "📏", "key": "length"},
    {"name": "重量", "icon": "⚖️", "key": "weight"},
    {"name": "温度", "icon": "🌡️", "key": "temperature"},
    {"name": "面积", "icon": "📐", "key": "area"},
    {"name": "体积", "icon": "🧪", "key": "volume"},
    {"name": "速度", "icon": "🚀", "key": "speed"},
    {"name": "数据", "icon": "💾", "key": "data"},
    {"name": "时间", "icon": "⏰", "key": "time"},
    {"name": "汇率", "icon": "💱", "key": "currency"},
]

# 单位到基准单位的换算因子（基准：第一个单位）
UNITS = {
    "length": {
        "km": ("千米", 1000),
        "m": ("米", 1),
        "cm": ("厘米", 0.01),
        "mm": ("毫米", 0.001),
        "mile": ("英里", 1609.344),
        "yard": ("码", 0.9144),
        "foot": ("英尺", 0.3048),
        "inch": ("英寸", 0.0254),
    },
    "weight": {
        "kg": ("千克", 1),
        "g": ("克", 0.001),
        "mg": ("毫克", 0.000001),
        "ton": ("吨", 1000),
        "pound": ("磅", 0.453592),
        "ounce": ("盎司", 0.0283495),
    },
    "temperature": {
        "celsius": ("摄氏度", "special"),
        "fahrenheit": ("华氏度", "special"),
        "kelvin": ("开尔文", "special"),
    },
    "area": {
        "sqm": ("平方米", 1),
        "sqkm": ("平方千米", 1_000_000),
        "hectare": ("公顷", 10_000),
        "acre": ("英亩", 4046.8564224),
        "sqft": ("平方英尺", 0.09290304),
    },
    "volume": {
        "liter": ("升", 1),
        "ml": ("毫升", 0.001),
        "gallon": ("加仑(美)", 3.78541),
        "cup": ("杯", 0.236588),
        "cubicm": ("立方米", 1000),
    },
    "speed": {
        "kmh": ("千米/时", 1),
        "ms": ("米/秒", 3.6),
        "mph": ("英里/时", 1.60934),
        "knot": ("节", 1.852),
    },
    "data": {
        "byte": ("字节(B)", 1),
        "kb": ("KB", 1024),
        "mb": ("MB", 1024**2),
        "gb": ("GB", 1024**3),
        "tb": ("TB", 1024**4),
    },
    "time": {
        "second": ("秒", 1),
        "minute": ("分钟", 60),
        "hour": ("小时", 3600),
        "day": ("天", 86400),
        "week": ("周", 604800),
        "month": ("月(30天)", 2592000),
        "year": ("年(365天)", 31536000),
    },
    "currency": {
        "usd": ("美元(USD)", 1),
        "eur": ("欧元(EUR)", 1.08),
        "cny": ("人民币(CNY)", 0.14),
        "jpy": ("日元(JPY)", 0.0067),
        "gbp": ("英镑(GBP)", 1.27),
    },
}


def convert_temperature(value, from_unit, to_unit):
    """温度单位转换"""
    if from_unit == to_unit:
        return value
    # 先转为摄氏度
    if from_unit == "celsius":
        c = value
    elif from_unit == "fahrenheit":
        c = (value - 32) * 5 / 9
    elif from_unit == "kelvin":
        c = value - 273.15
    else:
        return 0
    # 从摄氏度转为目标单位
    if to_unit == "celsius":
        return c
    elif to_unit == "fahrenheit":
        return c * 9 / 5 + 32
    elif to_unit == "kelvin":
        return c + 273.15
    return 0


def convert_units(value, from_unit, to_unit, category):
    """通用单位转换"""
    if category == "temperature":
        return convert_temperature(value, from_unit, to_unit)

    units_data = UNITS.get(category, {})
    from_factor = units_data.get(from_unit, (None, 1))[1]
    to_factor = units_data.get(to_unit, (None, 1))[1]

    if category == "currency":
        # 汇率：先转为USD，再转为目标货币
        usd_value = value * from_factor
        return usd_value / to_factor
    else:
        # 标准转换：先转为基准单位，再转为目标单位
        base_value = value * from_factor
        return base_value / to_factor


# ============================================================
# 获取实时汇率的线程
# ============================================================

class CurrencyFetchThread(QThread):
    """后台线程获取实时汇率"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            # 使用免费汇率 API
            url = "https://open.er-api.com/v6/latest/USD"
            req = Request(url, headers={"User-Agent": "UnitConverter/1.0"})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get("result") == "success":
                    rates = data.get("rates", {})
                    currency_map = {
                        "usd": ("美元(USD)", 1),
                        "eur": ("欧元(EUR)", 1.0 / rates.get("EUR", 1.08)),
                        "cny": ("人民币(CNY)", 1.0 / rates.get("CNY", 7.2)),
                        "jpy": ("日元(JPY)", 1.0 / rates.get("JPY", 149)),
                        "gbp": ("英镑(GBP)", 1.0 / rates.get("GBP", 0.79)),
                    }
                    self.finished.emit(currency_map)
                else:
                    self.error.emit("API返回错误")
        except (URLError, Exception) as e:
            self.error.emit(str(e))


# ============================================================
# 自定义组件
# ============================================================

class GradientButton(QPushButton):
    """渐变色按钮"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))


class SwapButton(QPushButton):
    """交换按钮"""
    def __init__(self, parent=None):
        super().__init__("⇄", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(60, 60)
        self.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))


class CategoryButton(QPushButton):
    """分类侧边栏按钮"""
    def __init__(self, icon, name, parent=None):
        super().__init__(f"{icon}  {name}", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)
        self.setFont(QFont("Microsoft YaHei", 11))
        self.setObjectName("categoryBtn")


class ResultLabel(QLabel):
    """结果展示标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Microsoft YaHei", 14))
        self.setWordWrap(True)


# ============================================================
# 换算面板
# ============================================================

class ConversionPanel(QWidget):
    """单个类别的换算面板"""

    def __init__(self, category_key, parent=None):
        super().__init__(parent)
        self.category_key = category_key
        self.units_data = UNITS.get(category_key, {})
        self.unit_keys = list(self.units_data.keys())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 输入区域卡片
        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(20, 20, 20, 20)

        # 输入标签
        input_label = QLabel("输入数值")
        input_label.setObjectName("sectionLabel")
        input_layout.addWidget(input_label)

        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入要换算的数值...")
        self.input_field.setObjectName("inputField")
        self.input_field.setMinimumHeight(44)
        input_layout.addWidget(self.input_field)

        # 单位选择行
        unit_row = QHBoxLayout()
        unit_row.setSpacing(12)

        # 从单位
        from_group = QVBoxLayout()
        from_label = QLabel("从")
        from_label.setObjectName("unitLabel")
        self.from_combo = QComboBox()
        self.from_combo.setObjectName("unitCombo")
        self.from_combo.setMinimumHeight(40)
        for key in self.unit_keys:
            name = self.units_data[key][0]
            self.from_combo.addItem(name, key)
        from_group.addWidget(from_label)
        from_group.addWidget(self.from_combo)

        # 交换按钮
        self.swap_btn = SwapButton()
        self.swap_btn.setToolTip("交换单位")
        self.swap_btn.setObjectName("swapBtn")

        # 到单位
        to_group = QVBoxLayout()
        to_label = QLabel("到")
        to_label.setObjectName("unitLabel")
        self.to_combo = QComboBox()
        self.to_combo.setObjectName("unitCombo")
        self.to_combo.setMinimumHeight(40)
        for key in self.unit_keys:
            name = self.units_data[key][0]
            self.to_combo.addItem(name, key)
        if len(self.unit_keys) > 1:
            self.to_combo.setCurrentIndex(1)
        to_group.addWidget(to_label)
        to_group.addWidget(self.to_combo)

        unit_row.addLayout(from_group)
        unit_row.addWidget(self.swap_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        unit_row.addLayout(to_group)
        input_layout.addLayout(unit_row)

        layout.addWidget(input_card)

        # 转换按钮
        self.convert_btn = GradientButton("🔄  立即转换")
        self.convert_btn.setObjectName("convertBtn")
        layout.addWidget(self.convert_btn)

        # 结果卡片
        result_card = QFrame()
        result_card.setObjectName("card")
        result_layout = QVBoxLayout(result_card)
        result_layout.setSpacing(8)
        result_layout.setContentsMargins(20, 20, 20, 20)

        result_title = QLabel("转换结果")
        result_title.setObjectName("sectionLabel")
        result_layout.addWidget(result_title)

        self.result_label = ResultLabel()
        self.result_label.setObjectName("resultLabel")
        self.result_label.setText("输入数值后点击转换")
        result_layout.addWidget(self.result_label)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("detailLabel")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        result_layout.addWidget(self.detail_label)

        layout.addWidget(result_card)

        # 填充空间
        layout.addStretch()

        # 连接信号
        self.convert_btn.clicked.connect(self.do_convert)
        self.swap_btn.clicked.connect(self.swap_units)
        self.input_field.returnPressed.connect(self.do_convert)

        # 实时转换（输入变化时）
        self.input_field.textChanged.connect(self.live_convert)

    def swap_units(self):
        """交换单位"""
        from_idx = self.from_combo.currentIndex()
        to_idx = self.to_combo.currentIndex()
        self.from_combo.setCurrentIndex(to_idx)
        self.to_combo.setCurrentIndex(from_idx)
        self.do_convert()

    def do_convert(self):
        """执行转换"""
        text = self.input_field.text().strip()
        if not text:
            self.result_label.setText("⚠️  请输入数值")
            self.detail_label.setText("")
            return

        try:
            value = float(text)
        except ValueError:
            self.result_label.setText("❌  请输入有效的数字")
            self.detail_label.setText("")
            return

        from_key = self.from_combo.currentData()
        to_key = self.to_combo.currentData()
        from_name = self.units_data[from_key][0]
        to_name = self.units_data[to_key][0]

        result = convert_units(value, from_key, to_key, self.category_key)

        # 格式化结果
        if abs(result) >= 1e10 or (abs(result) < 0.0001 and result != 0):
            result_text = f"{result:.6e}"
        elif result == int(result) and abs(result) < 1e15:
            result_text = f"{int(result):,}"
        else:
            result_text = f"{result:,.6f}".rstrip('0').rstrip('.')

        self.result_label.setText(f"✨  {result_text}")
        self.detail_label.setText(
            f"<span style='color:#8888aa;'>{value:g} {from_name} = {result_text} {to_name}</span>"
        )

    def live_convert(self):
        """实时转换（延迟执行）"""
        if hasattr(self, '_live_timer'):
            self._live_timer.stop()
        else:
            self._live_timer = QTimer()
            self._live_timer.setSingleShot(True)
            self._live_timer.timeout.connect(self.do_convert)
        self._live_timer.start(300)

    def update_currency_rates(self, rates):
        """更新汇率数据"""
        if self.category_key == "currency":
            self.units_data = rates
            self.unit_keys = list(rates.keys())
            # 更新下拉框
            self.from_combo.clear()
            self.to_combo.clear()
            for key in self.unit_keys:
                name = rates[key][0]
                self.from_combo.addItem(name, key)
                self.to_combo.addItem(name, key)
            if len(self.unit_keys) > 1:
                self.to_combo.setCurrentIndex(1)


# ============================================================
# 主窗口
# ============================================================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnitConverter - 专业单位换算器")
        self.setMinimumSize(900, 640)
        self.resize(1000, 680)
        self.panels = {}
        self.init_ui()
        self.fetch_currency_rates()
        # 默认选中第一个分类
        QTimer.singleShot(100, lambda: self.select_category(0))

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------- 左侧侧边栏 --------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        # 应用标题
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 12, 8, 16)

        app_icon = QLabel("🔢")
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_icon.setFont(QFont("Segoe UI", 28))
        title_layout.addWidget(app_icon)

        app_title = QLabel("单位换算器")
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(app_title)

        app_subtitle = QLabel("UnitConverter")
        app_subtitle.setObjectName("appSubtitle")
        app_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(app_subtitle)

        sidebar_layout.addWidget(title_frame)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        sidebar_layout.addWidget(sep)

        sidebar_layout.addSpacing(8)

        # 分类按钮
        self.category_buttons = []
        for i, cat in enumerate(CATEGORIES):
            btn = CategoryButton(cat["icon"], cat["name"])
            btn.clicked.connect(partial(self.select_category, i))
            sidebar_layout.addWidget(btn)
            self.category_buttons.append(btn)

        sidebar_layout.addStretch()

        # 底部信息
        version_label = QLabel("v1.0.0")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        # -------- 右侧内容区 --------
        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题栏
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(64)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self.header_title = QLabel("📏 长度换算")
        self.header_title.setObjectName("headerTitle")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()

        self.status_label = QLabel("🟢 就绪")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)

        content_layout.addWidget(header)

        # 换算面板堆栈
        self.stack = QStackedWidget()
        self.stack.setObjectName("stack")
        for cat in CATEGORIES:
            panel = ConversionPanel(cat["key"])
            self.panels[cat["key"]] = panel
            self.stack.addWidget(panel)

        content_layout.addWidget(self.stack)

        main_layout.addWidget(content)

    def select_category(self, index):
        """选择分类"""
        cat = CATEGORIES[index]
        self.stack.setCurrentIndex(index)
        self.header_title.setText(f"{cat['icon']} {cat['name']}换算")

        # 更新按钮状态
        for i, btn in enumerate(self.category_buttons):
            if i == index:
                btn.setProperty("active", True)
            else:
                btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def fetch_currency_rates(self):
        """获取实时汇率"""
        self.status_label.setText("🟡 正在获取汇率...")
        self.currency_thread = CurrencyFetchThread()
        self.currency_thread.finished.connect(self.on_currency_fetched)
        self.currency_thread.error.connect(self.on_currency_error)
        self.currency_thread.start()

    def on_currency_fetched(self, rates):
        """汇率获取成功"""
        self.panels["currency"].update_currency_rates(rates)
        self.status_label.setText("🟢 汇率已更新")

    def on_currency_error(self, error_msg):
        """汇率获取失败"""
        self.status_label.setText("🟠 使用默认汇率")


# ============================================================
# 样式表
# ============================================================

STYLESHEET = """
/* 全局 */
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: transparent;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

/* 侧边栏 */
#sidebar {
    background-color: #0e0e18;
    border-right: 1px solid #1a1a2e;
}

#titleFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 12px;
    padding: 8px;
}

#appTitle {
    color: white;
    font-size: 16px;
    font-weight: bold;
}

#appSubtitle {
    color: rgba(255,255,255,0.7);
    font-size: 11px;
}

#separator {
    background-color: #2a2a3e;
    max-height: 1px;
}

/* 分类按钮 */
#categoryBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    text-align: left;
    color: #a0a0b8;
}

#categoryBtn:hover {
    background-color: #1a1a2e;
    color: #e0e0f0;
}

#categoryBtn[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: bold;
}

#versionLabel {
    color: #444466;
    font-size: 10px;
}

/* 内容区 */
#content {
    background-color: #0a0a0a;
}

#header {
    background-color: #0e0e18;
    border-bottom: 1px solid #1a1a2e;
}

#headerTitle {
    font-size: 18px;
    font-weight: bold;
    color: #e8e8f0;
}

#statusLabel {
    font-size: 11px;
    color: #8888aa;
}

/* 卡片 */
#card {
    background-color: #111122;
    border: 1px solid #1e1e33;
    border-radius: 12px;
}

#sectionLabel {
    color: #9999bb;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}

/* 输入框 */
#inputField {
    background-color: #0a0a14;
    border: 2px solid #2a2a44;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 16px;
    color: #e0e0f0;
    selection-background-color: #667eea;
}

#inputField:focus {
    border-color: #667eea;
}

#inputField:hover {
    border-color: #3a3a55;
}

/* 下拉框 */
#unitCombo {
    background-color: #0a0a14;
    border: 2px solid #2a2a44;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #e0e0f0;
    min-width: 120px;
}

#unitCombo:focus {
    border-color: #667eea;
}

#unitCombo::drop-down {
    border: none;
    width: 30px;
}

#unitCombo::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #667eea;
    margin-right: 8px;
}

#unitCombo QAbstractItemView {
    background-color: #111122;
    border: 1px solid #2a2a44;
    color: #e0e0f0;
    selection-background-color: #667eea;
    selection-color: white;
    padding: 4px;
}

/* 单位标签 */
#unitLabel {
    color: #7777aa;
    font-size: 11px;
    font-weight: bold;
}

/* 交换按钮 */
#swapBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    border: none;
    border-radius: 30px;
    color: white;
    font-size: 22px;
    padding: 0;
}

#swapBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7b92ee, stop:1 #8b5fb5);
}

#swapBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5566cc, stop:1 #663a8a);
}

/* 转换按钮 */
#convertBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 15px;
    padding: 12px;
    font-weight: bold;
}

#convertBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b92ee, stop:1 #8b5fb5);
}

#convertBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5566cc, stop:1 #663a8a);
}

/* 结果标签 */
#resultLabel {
    color: #a8b4ff;
    font-size: 28px;
    font-weight: bold;
    padding: 16px 0;
}

#detailLabel {
    color: #666688;
    font-size: 12px;
    padding: 4px 0;
}

/* 滚动条 */
QScrollBar:vertical {
    background-color: #0a0a14;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2a2a44;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3a3a55;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* 工具提示 */
QToolTip {
    background-color: #1a1a2e;
    color: #e0e0f0;
    border: 1px solid #667eea;
    border-radius: 4px;
    padding: 6px;
}
"""


# ============================================================
# 入口
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 设置深色调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0a0a14"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # 应用样式表
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
