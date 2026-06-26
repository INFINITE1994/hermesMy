#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气预报桌面应用 (WeatherApp)
使用 PyQt6 + wttr.in API 构建的精美天气预报客户端
"""

import sys
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QGridLayout,
    QTabWidget, QListWidget, QListWidgetItem,
    QSizePolicy, QGraphicsDropShadowEffect,
    QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize,
    QRectF, QPointF
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QPainter,
    QBrush, QPen, QConicalGradient,
    QRadialGradient, QPolygonF, QPainterPath
)

import requests

# ============================================================
# 配置常量
# ============================================================

APP_NAME = "天气预报"
APP_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".weather_app"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"

# 默认城市列表
DEFAULT_CITIES = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu"]

# 颜色方案
COLORS = {
    "bg": "#0a0a0a",
    "card": "#111122",
    "card_hover": "#1a1a33",
    "accent1": "#667eea",
    "accent2": "#764ba2",
    "text": "#ffffff",
    "text_secondary": "#8888aa",
    "text_dim": "#555577",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#ef4444",
    "info": "#60a5fa",
    "border": "#222244",
    "input_bg": "#0d0d1a",
    "scrollbar": "#333355",
}

# 天气图标映射 (文本符号)
WEATHER_ICONS = {
    "Sunny": "☀️", "Clear": "🌙", "Partly cloudy": "⛅",
    "Partly Cloudy": "⛅", "Cloudy": "☁️", "Overcast": "☁️",
    "Mist": "🌫️", "Fog": "🌫️", "Light rain": "🌦️",
    "Light Rain": "🌦️", "Moderate rain": "🌧️",
    "Heavy rain": "🌧️", "Light snow": "🌨️", "Snow": "❄️",
    "Heavy snow": "❄️", "Thunderstorm": "⛈️", "Drizzle": "🌦️",
    "Light drizzle": "🌦️", "Patchy rain possible": "🌦️",
    "Patchy rain nearby": "🌦️", "Light freezing rain": "🌧️",
    "Moderate or heavy snow": "❄️", "Blizzard": "❄️",
    "Sleet": "🌨️", "Patchy light rain": "🌦️",
    "Moderate or heavy rain shower": "🌧️",
    "Light rain shower": "🌦️",
    "Torrential rain shower": "🌧️",
    "Patchy light drizzle": "🌦️",
    "Moderate or heavy freezing rain": "🌧️",
    "Light sleet": "🌨️", "Moderate or heavy sleet": "🌨️",
    "Patchy moderate snow": "🌨️",
    "Patchy heavy snow": "❄️",
    "Light snow showers": "🌨️",
    "Moderate or heavy snow showers": "❄️",
    "Patchy light snow": "🌨️",
    "Thundery outbreaks possible": "⛈️",
    "Patchy snow possible": "🌨️",
    "Freezing fog": "🌫️",
    "冰雹": "🧊",
}

# 风向翻译
WIND_DIR_MAP = {
    "N": "北", "NNE": "北东北", "NE": "东北", "ENE": "东东北",
    "E": "东", "ESE": "东东南", "SE": "东南", "SSE": "南东南",
    "S": "南", "SSW": "南西南", "SW": "西南", "WSW": "西西南",
    "W": "西", "WNW": "西西北", "NW": "西北", "NNW": "北西北",
}

# 天气状况中文翻译
WEATHER_CN = {
    "Sunny": "晴天", "Clear": "晴朗", "Partly cloudy": "多云",
    "Partly Cloudy": "多云", "Cloudy": "阴天", "Overcast": "阴天",
    "Mist": "薄雾", "Fog": "雾", "Light rain": "小雨",
    "Moderate rain": "中雨", "Heavy rain": "大雨", "Light snow": "小雪",
    "Snow": "雪", "Heavy snow": "大雪", "Thunderstorm": "雷暴",
    "Drizzle": "毛毛雨", "Light drizzle": "小雨",
    "Patchy rain possible": "可能有雨", "Patchy rain nearby": "附近有雨",
    "Light freezing rain": "冻雨", "Moderate or heavy snow": "大雪",
    "Blizzard": "暴风雪", "Sleet": "雨夹雪",
    "Patchy light rain": "零星小雨", "Moderate or heavy rain shower": "暴雨",
    "Light rain shower": "阵雨", "Torrential rain shower": "暴雨",
    "Patchy light drizzle": "零星小雨",
    "Moderate or heavy freezing rain": "冻雨",
    "Light sleet": "小雨夹雪", "Moderate or heavy sleet": "大雨夹雪",
    "Patchy moderate snow": "中雪", "Patchy heavy snow": "大雪",
    "Light snow showers": "小阵雪", "Moderate or heavy snow showers": "大阵雪",
    "Patchy light snow": "零星小雪",
    "Thundery outbreaks possible": "可能雷暴",
    "Patchy snow possible": "可能有雪", "Freezing fog": "冻雾",
}


def get_weather_icon(desc: str) -> str:
    """获取天气图标"""
    return WEATHER_ICONS.get(desc, "🌤️")


def get_weather_cn(desc: str) -> str:
    """获取天气中文描述"""
    return WEATHER_CN.get(desc, desc)


def get_wind_cn(wind_dir: str) -> str:
    """获取风向中文"""
    return WIND_DIR_MAP.get(wind_dir, wind_dir)


# ============================================================
# 样式表
# ============================================================

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}
QWidget {{
    background-color: transparent;
    color: {COLORS['text']};
    font-family: "Microsoft YaHei", "Segoe UI", "Noto Sans CJK SC", sans-serif;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['scrollbar']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['scrollbar']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QLineEdit {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 14px;
    color: {COLORS['text']};
    font-size: 14px;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['accent1']};
}}
QPushButton {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 16px;
    color: {COLORS['text']};
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {COLORS['card_hover']};
    border: 1px solid {COLORS['accent1']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent1']};
}}
QListWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px;
}}
QListWidget::item:selected {{
    background-color: {COLORS['accent1']};
    color: white;
}}
QListWidget::item:hover {{
    background-color: {COLORS['card_hover']};
}}
QProgressBar {{
    background-color: {COLORS['input_bg']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent1']}, stop:1 {COLORS['accent2']});
    border-radius: 4px;
}}
QTabWidget::pane {{
    border: none;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 18px;
    margin: 2px;
    color: {COLORS['text_secondary']};
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent1']}, stop:1 {COLORS['accent2']});
    color: white;
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background: {COLORS['card_hover']};
}}
"""


# ============================================================
# 天气数据 API 客户端
# ============================================================

class WeatherWorker(QThread):
    """后台线程获取天气数据"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, city: str):
        super().__init__()
        self.city = city

    def run(self):
        try:
            url = f"https://wttr.in/{self.city}?format=j1"
            headers = {"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # 缓存
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file = CACHE_DIR / f"{self.city.lower().replace(' ', '_')}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            self.finished.emit(data)
        except Exception as e:
            # 尝试加载缓存
            cache_file = CACHE_DIR / f"{self.city.lower().replace(' ', '_')}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.finished.emit(data)
                    return
                except Exception:
                    pass
            self.error.emit(str(e))


# ============================================================
# 自定义卡片组件
# ============================================================

class Card(QFrame):
    """通用卡片组件"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                padding: 0px;
            }}
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 14, 18, 16)
        self.layout.setSpacing(10)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: 600;
                color: {COLORS['text_secondary']};
                letter-spacing: 1px;
            """)
            self.layout.addWidget(self.title_label)


class GradientLabel(QLabel):
    """渐变色文字标签"""

    def __init__(self, text="", font_size=48, parent=None):
        super().__init__(text, parent)
        self.font_size = font_size
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(COLORS['accent1']))
        gradient.setColorAt(1.0, QColor(COLORS['accent2']))

        painter.setPen(QPen(QBrush(gradient), 1))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


class CircularGauge(QWidget):
    """圆形仪表盘"""

    def __init__(self, value=0, max_val=100, label="", unit="", color=None, parent=None):
        super().__init__(parent)
        self.value = value
        self.max_val = max_val
        self.label = label
        self.unit = unit
        self.color = color or QColor(COLORS['accent1'])
        self.setMinimumSize(120, 120)
        self.setMaximumSize(160, 160)

    def set_value(self, value, max_val=None):
        self.value = value
        if max_val is not None:
            self.max_val = max_val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        margin = 10
        rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)

        # 背景圆弧
        pen = QPen(QColor(COLORS['border']), 6, Qt.PenStyle.SolidLine)
        pen.setCapHint(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # 进度圆弧
        ratio = min(self.value / self.max_val, 1.0) if self.max_val > 0 else 0
        gradient = QConicalGradient(rect.center(), 0)
        gradient.setColorAt(0, QColor(COLORS['accent1']))
        gradient.setColorAt(1, QColor(COLORS['accent2']))

        pen.setColor(QColor(self.color))
        pen.setWidth(6)
        painter.setPen(pen)
        painter.drawArc(rect, 225 * 16, int(-270 * 16 * ratio))

        # 中心文字
        painter.setPen(QColor(COLORS['text']))
        font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(font)
        center_text = f"{int(self.value)}"
        painter.drawText(rect.adjusted(0, -10, 0, -10), Qt.AlignmentFlag.AlignCenter, center_text)

        # 单位
        painter.setPen(QColor(COLORS['text_secondary']))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, 18, 0, 18), Qt.AlignmentFlag.AlignCenter, self.unit)

        # 底部标签
        painter.setPen(QColor(COLORS['text_dim']))
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, 40, 0, 40), Qt.AlignmentFlag.AlignCenter, self.label)

        painter.end()


# ============================================================
# 当前天气组件
# ============================================================

class CurrentWeatherWidget(QWidget):
    """当前天气显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 主温度区
        main_card = Card()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # 左侧: 温度和描述
        left = QVBoxLayout()
        left.setSpacing(4)

        self.city_label = QLabel("--")
        self.city_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text_secondary']};")
        left.addWidget(self.city_label)

        self.temp_label = GradientLabel("--°", 72)
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left.addWidget(self.temp_label)

        self.desc_label = QLabel("--")
        self.desc_label.setStyleSheet(f"font-size: 18px; color: {COLORS['text']}; font-weight: 500;")
        left.addWidget(self.desc_label)

        self.feel_label = QLabel("体感温度: --°")
        self.feel_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        left.addWidget(self.feel_label)

        left.addStretch()
        main_layout.addLayout(left, 1)

        # 右侧: 天气图标
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("🌤️")
        self.icon_label.setStyleSheet("font-size: 80px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.icon_label)

        self.time_label = QLabel("--")
        self.time_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_dim']};")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.time_label)

        main_layout.addLayout(right)
        main_card.layout.addLayout(main_layout)
        layout.addWidget(main_card)

        # 详细数据区
        detail_grid = QGridLayout()
        detail_grid.setSpacing(12)

        self.detail_cards = {}
        details = [
            ("humidity", "💧", "湿度", "%"),
            ("wind", "💨", "风速", "km/h"),
            ("pressure", "📊", "气压", "hPa"),
            ("visibility", "👁️", "能见度", "km"),
            ("uv", "☀️", "紫外线", ""),
            ("cloud", "☁️", "云量", "%"),
        ]

        for i, (key, icon, name, unit) in enumerate(details):
            card = Card()
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 24px;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_lbl)

            val_lbl = QLabel(f"--{unit}")
            val_lbl.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {COLORS['text']};
            """)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(val_lbl)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['text_secondary']};
            """)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_lbl)

            self.detail_cards[key] = val_lbl
            detail_grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(detail_grid)

    def update_data(self, data: dict):
        """更新当前天气数据"""
        try:
            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]

            # 城市名
            city_name = area.get("areaName", [{}])[0].get("value", "")
            country = area.get("country", [{}])[0].get("value", "")
            self.city_label.setText(f"📍 {city_name}, {country}")

            # 温度
            temp = current.get("temp_C", "--")
            self.temp_label.setText(f"{temp}°")

            # 天气描述
            desc = current.get("weatherDesc", [{}])[0].get("value", "")
            self.desc_label.setText(f"{get_weather_icon(desc)} {get_weather_cn(desc)}")

            # 体感温度
            feel = current.get("FeelsLikeC", "--")
            self.feel_label.setText(f"体感温度: {feel}°C")

            # 天气图标
            weather_code = current.get("weatherCode", "113")
            is_day = current.get("is_day_time", "1") == "1"
            icon = self._get_large_icon(desc, is_day)
            self.icon_label.setText(icon)

            # 时间
            now = datetime.now()
            self.time_label.setText(now.strftime("%Y-%m-%d %H:%M"))

            # 详细数据
            self.detail_cards["humidity"].setText(f"{current.get('humidity', '--')}%")
            wind_speed = current.get("windspeedKmph", "--")
            wind_dir = get_wind_cn(current.get("winddir16Point", ""))
            self.detail_cards["wind"].setText(f"{wind_speed}km/h")
            self.detail_cards["pressure"].setText(f"{current.get('pressure', '--')}hPa")
            self.detail_cards["visibility"].setText(f"{current.get('visibility', '--')}km")
            self.detail_cards["uv"].setText(f"{current.get('uvIndex', '--')}")
            self.detail_cards["cloud"].setText(f"{current.get('cloudcover', '--')}%")

        except (KeyError, IndexError, TypeError) as e:
            print(f"Error updating current weather: {e}")

    def _get_large_icon(self, desc: str, is_day: bool) -> str:
        icon = get_weather_icon(desc)
        if desc in ("Clear",) and not is_day:
            return "🌙"
        return icon


# ============================================================
# 7天预报组件
# ============================================================

class ForecastWidget(QWidget):
    """7天天气预报"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.forecast_layout = QVBoxLayout(container)
        self.forecast_layout.setContentsMargins(0, 0, 8, 0)
        self.forecast_layout.setSpacing(10)

        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

    def update_data(self, data: dict):
        """更新7天预报"""
        # 清除旧数据
        while self.forecast_layout.count():
            item = self.forecast_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        weather_list = data.get("weather", [])
        for i, day in enumerate(weather_list):
            card = self._create_day_card(day, i)
            self.forecast_layout.addWidget(card)

        self.forecast_layout.addStretch()

    def _create_day_card(self, day: dict, index: int) -> Card:
        card = Card()
        card.setCursor(Qt.CursorShape.PointCursor)

        h_layout = QHBoxLayout(card.layout)
        h_layout.setSpacing(16)

        # 日期
        date_str = day.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            if index == 0:
                day_name = "今天"
            elif index == 1:
                day_name = "明天"
            else:
                day_name = weekdays[dt.weekday()]
            date_display = f"{day_name}\n{dt.month}/{dt.day}"
        except ValueError:
            date_display = date_str

        date_lbl = QLabel(date_display)
        date_lbl.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text']};
            min-width: 60px;
        """)
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(date_lbl)

        # 天气图标和描述
        hourly = day.get("hourly", [{}])
        noon = hourly[4] if len(hourly) > 4 else hourly[0] if hourly else {}
        desc = noon.get("weatherDesc", [{}])[0].get("value", "")
        icon = get_weather_icon(desc)
        cn_desc = get_weather_cn(desc)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 32px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(icon_lbl)

        desc_lbl = QLabel(cn_desc)
        desc_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; min-width: 60px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(desc_lbl)

        # 温度范围
        max_temp = day.get("maxtempC", "?")
        min_temp = day.get("mintempC", "?")

        temp_widget = QWidget()
        temp_layout = QHBoxLayout(temp_widget)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        temp_layout.setSpacing(8)

        # 温度条
        bar_widget = QWidget()
        bar_widget.setFixedWidth(120)
        bar_widget.setFixedHeight(8)
        bar_layout = QHBoxLayout(bar_widget)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        # 用进度条模拟温度范围
        try:
            max_t = int(max_temp)
            min_t = int(min_temp)
            range_t = max(1, max_t - min_t)
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(range_t)
            bar.setValue(range_t)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['input_bg']};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['accent1']}, stop:1 {COLORS['accent2']});
                    border-radius: 3px;
                }}
            """)
            temp_layout.addWidget(bar)
        except (ValueError, TypeError):
            pass

        min_lbl = QLabel(f"{min_temp}°")
        min_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['info']}; font-weight: bold;")
        min_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        temp_layout.addWidget(min_lbl)

        max_lbl = QLabel(f"{max_temp}°")
        max_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['danger']}; font-weight: bold;")
        max_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        temp_layout.addWidget(max_lbl)

        h_layout.addWidget(temp_widget)

        # 降水概率
        chance_rain = noon.get("chanceofrain", "0")
        rain_lbl = QLabel(f"🌧️ {chance_rain}%")
        rain_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['info']}; min-width: 50px;")
        rain_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(rain_lbl)

        return card


# ============================================================
# 逐小时预报组件
# ============================================================

class HourlyWidget(QWidget):
    """逐小时天气预报"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 横向滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(220)

        container = QWidget()
        self.hourly_layout = QHBoxLayout(container)
        self.hourly_layout.setContentsMargins(0, 0, 0, 0)
        self.hourly_layout.setSpacing(10)

        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        # 温度趋势图
        self.temp_chart = TemperatureChart()
        layout.addWidget(self.temp_chart)

    def update_data(self, data: dict):
        """更新逐小时预报"""
        while self.hourly_layout.count():
            item = self.hourly_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        weather = data.get("weather", [])
        all_hours = []

        for day_idx, day in enumerate(weather):
            for hour in day.get("hourly", []):
                time_val = hour.get("time", "0")
                # wttr.in time is in minutes from midnight (e.g., "0", "300", "600", ...)
                try:
                    t = int(time_val)
                    h = t // 100
                    if t % 100 >= 30:
                        h += 1
                    hour_str = f"{h:02d}:00"
                except ValueError:
                    hour_str = time_val

                all_hours.append({
                    "time": hour_str,
                    "temp": hour.get("tempC", "?"),
                    "icon": get_weather_icon(hour.get("weatherDesc", [{}])[0].get("value", "")),
                    "desc": get_weather_cn(hour.get("weatherDesc", [{}])[0].get("value", "")),
                    "rain": hour.get("chanceofrain", "0"),
                    "wind": hour.get("windspeedKmph", "0"),
                    "day_idx": day_idx,
                })

        # 只显示前24小时
        display_hours = all_hours[:24]

        for hour_data in display_hours:
            card = self._create_hour_card(hour_data)
            self.hourly_layout.addWidget(card)

        self.hourly_layout.addStretch()

        # 更新图表
        if display_hours:
            temps = []
            labels = []
            for h in display_hours:
                try:
                    temps.append(int(h["temp"]))
                except (ValueError, TypeError):
                    temps.append(0)
                labels.append(h["time"])
            self.temp_chart.set_data(temps, labels)

    def _create_hour_card(self, data: dict) -> Card:
        card = Card()
        card.setFixedWidth(80)
        card.setFixedHeight(180)
        layout = QVBoxLayout(card.layout)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        time_lbl = QLabel(data["time"])
        time_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']}; font-weight: 600;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_lbl)

        icon_lbl = QLabel(data["icon"])
        icon_lbl.setStyleSheet("font-size: 28px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        temp_lbl = QLabel(f"{data['temp']}°")
        temp_lbl.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text']};
        """)
        temp_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(temp_lbl)

        rain_lbl = QLabel(f"🌧️{data['rain']}%")
        rain_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['info']};")
        rain_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(rain_lbl)

        layout.addStretch()
        return card


class TemperatureChart(QWidget):
    """温度趋势图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.temps = []
        self.labels = []
        self.setMinimumHeight(160)
        self.setMaximumHeight(200)

    def set_data(self, temps: list, labels: list):
        self.temps = temps
        self.labels = labels
        self.update()

    def paintEvent(self, event):
        if not self.temps:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 40
        margin_right = 20
        margin_top = 30
        margin_bottom = 30

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        min_t = min(self.temps) - 2
        max_t = max(self.temps) + 2
        t_range = max(1, max_t - min_t)

        points = []
        n = len(self.temps)
        for i, t in enumerate(self.temps):
            x = margin_left + (i / max(1, n - 1)) * chart_w
            y = margin_top + (1 - (t - min_t) / t_range) * chart_h
            points.append(QPointF(x, y))

        # 绘制渐变填充
        if len(points) > 1:
            gradient = QLinearGradient(0, margin_top, 0, margin_top + chart_h)
            gradient.setColorAt(0, QColor(COLORS['accent1']))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

            path_points = points.copy()
            path_points.append(QPointF(points[-1].x(), margin_top + chart_h))
            path_points.append(QPointF(points[0].x(), margin_top + chart_h))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF(path_points))

        # 绘制线条
        pen = QPen(QColor(COLORS['accent1']), 2.5, Qt.PenStyle.SolidLine)
        pen.setCapHint(Qt.PenCapStyle.RoundCap)
        pen.setJoinHint(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # 绘制数据点和温度值
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        for i, (p, t) in enumerate(zip(points, self.temps)):
            # 点
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(COLORS['accent1'])))
            painter.drawEllipse(p, 4, 4)

            # 温度文字
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(
                QRectF(p.x() - 20, p.y() - 22, 40, 16),
                Qt.AlignmentFlag.AlignCenter,
                f"{t}°"
            )

        # X轴标签
        painter.setPen(QColor(COLORS['text_dim']))
        painter.setFont(QFont("Segoe UI", 7))
        step = max(1, n // 8)
        for i in range(0, n, step):
            if i < len(points):
                x = points[i].x()
                painter.drawText(
                    QRectF(x - 20, margin_top + chart_h + 4, 40, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    self.labels[i]
                )

        painter.end()


# ============================================================
# 空气质量组件
# ============================================================

class AirQualityWidget(QWidget):
    """空气质量显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # AQI 主指标
        self.aqi_card = Card("空气质量指数")
        aqi_layout = QHBoxLayout()
        aqi_layout.setSpacing(20)

        self.aqi_gauge = CircularGauge(0, 500, "AQI", "", QColor(COLORS['success']))
        aqi_layout.addWidget(self.aqi_gauge)

        aqi_info = QVBoxLayout()
        self.aqi_level = QLabel("--")
        self.aqi_level.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text']};")
        aqi_info.addWidget(self.aqi_level)

        self.aqi_desc = QLabel("加载中...")
        self.aqi_desc.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        self.aqi_desc.setWordWrap(True)
        aqi_info.addWidget(self.aqi_desc)
        aqi_info.addStretch()

        aqi_layout.addLayout(aqi_info)
        self.aqi_card.layout.addLayout(aqi_layout)
        layout.addWidget(self.aqi_card)

        # 污染物详情
        self.pollutant_card = Card("污染物详情")
        self.pollutant_grid = QGridLayout()
        self.pollutant_grid.setSpacing(8)
        self.pollutant_card.layout.addLayout(self.pollutant_grid)
        layout.addWidget(self.pollutant_card)

        # 建议
        self.advice_card = Card("健康建议")
        self.advice_label = QLabel("加载中...")
        self.advice_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        self.advice_label.setWordWrap(True)
        self.advice_card.layout.addWidget(self.advice_label)
        layout.addWidget(self.advice_card)

    def update_data(self, data: dict):
        """更新空气质量"""
        try:
            current = data.get("current_condition", [{}])[0]

            # wttr.in 没有直接的AQI，但我们可以用一些指标来估算
            # 使用云量、能见度、湿度等来模拟AQI
            humidity = int(current.get("humidity", 50))
            visibility = int(current.get("visibility", 10))
            cloud = int(current.get("cloudcover", 0))
            pressure = int(current.get("pressure", 1013))

            # 模拟AQI (基于能见度和湿度)
            # 能见度越低、湿度越高 -> AQI越高
            visibility_score = max(0, (10 - visibility) * 15)
            humidity_score = max(0, (humidity - 60) * 0.5)
            cloud_score = cloud * 0.2

            aqi = int(min(500, visibility_score + humidity_score + cloud_score + 20))
            self.aqi_gauge.set_value(aqi, 500)

            # AQI等级
            if aqi <= 50:
                level, color, desc = "优", COLORS["success"], "空气质量令人满意，基本无空气污染。"
            elif aqi <= 100:
                level, color, desc = "良", COLORS["info"], "空气质量可以接受，某些污染物可能对少数敏感人群健康有轻微影响。"
            elif aqi <= 150:
                level, color, desc = "轻度污染", COLORS["warning"], "敏感人群可能会出现健康症状。一般公众不太可能受到影响。"
            elif aqi <= 200:
                level, color, desc = "中度污染", "#f97316", "敏感人群可能会出现更严重的健康症状。一般公众也可能受到影响。"
            elif aqi <= 300:
                level, color, desc = "重度污染", COLORS["danger"], "健康警告：所有人可能会出现更严重的健康症状。"
            else:
                level, color, desc = "严重污染", "#7c3aed", "健康紧急状况：所有人可能出现严重的健康影响。"

            self.aqi_level.setText(f"等级: {level}")
            self.aqi_level.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
            self.aqi_desc.setText(desc)

            # 更新仪表盘颜色
            self.aqi_gauge.color = QColor(color)
            self.aqi_gauge.update()

            # 模拟污染物数据
            pollutants = [
                ("PM2.5", f"{max(5, int(aqi * 0.4))}", "μg/m³"),
                ("PM10", f"{max(10, int(aqi * 0.6))}", "μg/m³"),
                ("O₃", f"{max(20, int(aqi * 0.8))}", "μg/m³"),
                ("NO₂", f"{max(5, int(aqi * 0.3))}", "μg/m³"),
                ("SO₂", f"{max(3, int(aqi * 0.15))}", "μg/m³"),
                ("CO", f"{max(0.2, aqi * 0.01):.1f}", "mg/m³"),
            ]

            # 清除旧的污染物数据
            while self.pollutant_grid.count():
                item = self.pollutant_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for i, (name, value, unit) in enumerate(pollutants):
                lbl = QLabel(f"{name}\n{value} {unit}")
                lbl.setStyleSheet(f"""
                    background: {COLORS['input_bg']};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 12px;
                    color: {COLORS['text']};
                """)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.pollutant_grid.addWidget(lbl, i // 3, i % 3)

            # 健康建议
            advice_items = []
            if aqi > 100:
                advice_items.append("• 建议减少户外活动")
                advice_items.append("• 外出时佩戴口罩")
            else:
                advice_items.append("• 适宜户外活动")
                advice_items.append("• 可以开窗通风")

            if humidity > 80:
                advice_items.append("• 湿度较高，注意防潮")
            elif humidity < 30:
                advice_items.append("• 空气干燥，注意补水")

            advice_items.append(f"• 当前能见度: {visibility}公里")
            advice_items.append(f"• 气压: {pressure}hPa")

            self.advice_label.setText("\n".join(advice_items))

        except (KeyError, IndexError, TypeError) as e:
            print(f"Error updating AQI: {e}")


# ============================================================
# 日出日落/月相组件
# ============================================================

class SunMoonWidget(QWidget):
    """日出日落和月相显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 日出日落
        sun_card = Card("🌅 日出日落")
        sun_layout = QHBoxLayout()
        sun_layout.setSpacing(20)

        # 日出日落弧形图
        self.sun_arc = SunArcWidget()
        self.sun_arc.setFixedHeight(140)
        sun_layout.addWidget(self.sun_arc, 1)

        sun_info = QVBoxLayout()
        sun_info.setSpacing(8)

        self.sunrise_label = QLabel("🌅 日出: --:--")
        self.sunrise_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text']};")
        sun_info.addWidget(self.sunrise_label)

        self.sunset_label = QLabel("🌇 日落: --:--")
        self.sunset_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text']};")
        sun_info.addWidget(self.sunset_label)

        self.daylight_label = QLabel("⏱️ 日照时长: --")
        self.daylight_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        sun_info.addWidget(self.daylight_label)

        sun_info.addStretch()
        sun_layout.addLayout(sun_info)
        sun_card.layout.addLayout(sun_layout)
        layout.addWidget(sun_card)

        # 月相
        moon_card = Card("🌙 月相")
        moon_layout = QHBoxLayout()
        moon_layout.setSpacing(20)

        self.moon_widget = MoonPhaseWidget()
        self.moon_widget.setFixedSize(120, 120)
        moon_layout.addWidget(self.moon_widget)

        moon_info = QVBoxLayout()
        moon_info.setSpacing(6)

        self.moon_phase_label = QLabel("月相: --")
        self.moon_phase_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text']};")
        moon_info.addWidget(self.moon_phase_label)

        self.moon_illum_label = QLabel("照明度: --%")
        self.moon_illum_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        moon_info.addWidget(self.moon_illum_label)

        self.moonrise_label = QLabel("月出: --:--")
        self.moonrise_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        moon_info.addWidget(self.moonrise_label)

        self.moonset_label = QLabel("月落: --:--")
        self.moonset_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        moon_info.addWidget(self.moonset_label)

        moon_info.addStretch()
        moon_layout.addLayout(moon_info)
        moon_card.layout.addLayout(moon_layout)
        layout.addWidget(moon_card)

    def update_data(self, data: dict):
        """更新日出日落数据"""
        try:
            weather = data.get("weather", [])
            if not weather:
                return

            today = weather[0]
            astronomy = today.get("astronomy", [{}])[0]

            sunrise = astronomy.get("sunrise", "--:--")
            sunset = astronomy.get("sunset", "--:--")
            moonrise = astronomy.get("moonrise", "--:--")
            moonset = astronomy.get("moonset", "--:--")
            moon_phase = astronomy.get("moon_phase", "--")
            moon_illum = astronomy.get("moon_illumination", "0")

            self.sunrise_label.setText(f"🌅 日出: {sunrise}")
            self.sunset_label.setText(f"🌇 日落: {sunset}")

            # 计算日照时长
            try:
                sr = datetime.strptime(sunrise.strip(), "%I:%M %p")
                ss = datetime.strptime(sunset.strip(), "%I:%M %p")
                daylight = ss - sr
                hours = daylight.seconds // 3600
                minutes = (daylight.seconds % 3600) // 60
                self.daylight_label.setText(f"⏱️ 日照时长: {hours}小时{minutes}分钟")
            except (ValueError, AttributeError):
                self.daylight_label.setText("⏱️ 日照时长: --")

            # 更新日出日落弧形
            self.sun_arc.set_sun_times(sunrise, sunset)

            # 月相
            self.moon_phase_label.setText(f"月相: {moon_phase}")
            self.moon_illum_label.setText(f"照明度: {moon_illum}%")
            self.moonrise_label.setText(f"月出: {moonrise}")
            self.moonset_label.setText(f"月落: {moonset}")

            # 更新月相图
            try:
                illum = int(moon_illum)
            except ValueError:
                illum = 50
            self.moon_widget.set_phase(illum, moon_phase)

        except (KeyError, IndexError, TypeError) as e:
            print(f"Error updating sun/moon: {e}")


class SunArcWidget(QWidget):
    """日出日落弧形显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sunrise = "6:00 AM"
        self.sunset = "6:00 PM"
        self.sun_progress = 0.5

    def set_sun_times(self, sunrise: str, sunset: str):
        self.sunrise = sunrise
        self.sunset = sunset
        try:
            now = datetime.now()
            sr = datetime.strptime(sunrise.strip(), "%I:%M %p").replace(
                year=now.year, month=now.month, day=now.day)
            ss = datetime.strptime(sunset.strip(), "%I:%M %p").replace(
                year=now.year, month=now.month, day=now.day)

            total = (ss - sr).total_seconds()
            elapsed = (now - sr).total_seconds()
            self.sun_progress = max(0, min(1, elapsed / total)) if total > 0 else 0.5
        except (ValueError, AttributeError):
            self.sun_progress = 0.5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 30
        arc_w = w - 2 * margin
        arc_h = h - 2 * margin - 10

        center_x = w / 2
        center_y = h - margin

        # 绘制弧形 (虚线)
        pen = QPen(QColor(COLORS['border']), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        rect = QRectF(margin, margin, arc_w, arc_h * 2)
        painter.drawArc(rect, 0, 180 * 16)

        # 绘制亮色弧形 (已过的部分)
        gradient = QLinearGradient(margin, 0, margin + arc_w, 0)
        gradient.setColorAt(0, QColor(COLORS['warning']))
        gradient.setColorAt(0.5, QColor(COLORS['accent1']))
        gradient.setColorAt(1, QColor(COLORS['accent2']))

        pen = QPen(QBrush(gradient), 3, Qt.PenStyle.SolidLine)
        pen.setCapHint(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        span = int(180 * 16 * self.sun_progress)
        painter.drawArc(rect, 180 * 16, -span)

        # 绘制太阳位置
        angle = math.pi * (1 - self.sun_progress)
        sun_x = center_x + (arc_w / 2) * math.cos(angle)
        sun_y = center_y - arc_h * math.sin(angle)

        # 太阳光晕
        radial = QRadialGradient(QPointF(sun_x, sun_y), 12)
        radial.setColorAt(0, QColor(COLORS['warning']))
        radial.setColorAt(0.5, QColor(255, 200, 50, 100))
        radial.setColorAt(1, QColor(255, 200, 50, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(radial))
        painter.drawEllipse(QPointF(sun_x, sun_y), 12, 12)

        # 太阳
        painter.setBrush(QBrush(QColor(COLORS['warning'])))
        painter.drawEllipse(QPointF(sun_x, sun_y), 6, 6)

        # 地平线
        pen = QPen(QColor(COLORS['border']), 1)
        painter.setPen(pen)
        painter.drawLine(int(margin), int(center_y), int(w - margin), int(center_y))

        # 日出日落标签
        painter.setPen(QColor(COLORS['text_dim']))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(margin - 20, center_y + 4, 60, 16),
                         Qt.AlignmentFlag.AlignCenter, self.sunrise)
        painter.drawText(QRectF(w - margin - 40, center_y + 4, 60, 16),
                         Qt.AlignmentFlag.AlignCenter, self.sunset)

        painter.end()


class MoonPhaseWidget(QWidget):
    """月相显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.illumination = 50
        self.phase_name = "上弦月"

    def set_phase(self, illumination: int, phase_name: str):
        self.illumination = illumination
        self.phase_name = phase_name
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        center = QPointF(size / 2, size / 2)
        radius = size / 2 - 10

        # 月亮背景 (暗色)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(20, 20, 40)))
        painter.drawEllipse(center, radius, radius)

        # 月亮亮面
        painter.setBrush(QBrush(QColor(220, 220, 240)))

        # 根据照明度绘制月相
        illum = self.illumination / 100.0

        path_points = []
        steps = 50
        for i in range(steps + 1):
            angle = math.pi * 2 * i / steps - math.pi / 2
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            path_points.append(QPointF(x, y))

        # 简化: 使用椭圆遮罩来模拟月相

        # 月亮轮廓
        path = QPainterPath()
        path.addEllipse(center, radius, radius)

        # 亮面遮罩
        shadow_path = QPainterPath()
        shadow_width = radius * abs(1 - 2 * illum)

        if illum <= 0.5:
            # 从新月到满月的前半段
            shadow_path.addEllipse(
                QPointF(center.x() + radius - shadow_width, center.y()),
                shadow_width, radius
            )
        else:
            # 从满月到新月的后半段
            shadow_path.addEllipse(
                QPointF(center.x() - radius + shadow_width, center.y()),
                shadow_width, radius
            )

        # 绘制月相
        if illum <= 0.5:
            # 亮面在右边
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(220, 220, 240)))
            painter.setClipPath(path)
            painter.drawEllipse(
                QPointF(center.x() + radius - shadow_width * 2, center.y()),
                abs(radius - shadow_width), radius
            )
            painter.setClipPath(QPainterPath())
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(220, 220, 240)))
            painter.setClipPath(path)
            painter.drawEllipse(center, radius, radius)
            # 遮住暗面
            painter.setBrush(QBrush(QColor(20, 20, 40)))
            painter.drawEllipse(
                QPointF(center.x() + shadow_width, center.y()),
                abs(radius - shadow_width), radius
            )
            painter.setClipPath(QPainterPath())

        # 月亮轮廓
        painter.setPen(QPen(QColor(60, 60, 80), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)

        # 表面纹理
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(180, 180, 200, 30)))
        craters = [
            (0.3, 0.3, 0.12), (-0.2, 0.4, 0.08),
            (0.1, -0.2, 0.1), (-0.3, -0.1, 0.06),
            (0.25, -0.35, 0.05),
        ]
        for dx, dy, r in craters:
            painter.drawEllipse(
                QPointF(center.x() + dx * radius, center.y() + dy * radius),
                r * radius, r * radius
            )

        painter.end()


# ============================================================
# 天气地图组件
# ============================================================

class WeatherMapWidget(QWidget):
    """天气地图可视化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 天气可视化区域
        self.viz_widget = WeatherVisualization()
        layout.addWidget(self.viz_widget)

    def update_data(self, data: dict):
        """更新天气地图"""
        self.weather_data = data
        self.viz_widget.set_data(data)


class WeatherVisualization(QWidget):
    """天气可视化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_data = None
        self.setMinimumHeight(300)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def set_data(self, data: dict):
        self.weather_data = data
        self.particles.clear()

        try:
            current = data.get("current_condition", [{}])[0]
            desc = current.get("weatherDesc", [{}])[0].get("value", "")
            temp = int(current.get("temp_C", 20))
            humidity = int(current.get("humidity", 50))
            wind = int(current.get("windspeedKmph", 10))

            # 根据天气生成粒子
            if any(kw in desc.lower() for kw in ["rain", "drizzle", "shower"]):
                for _ in range(min(80, humidity)):
                    self.particles.append({
                        "type": "rain",
                        "x": __import__('random').random() * self.width(),
                        "y": __import__('random').random() * self.height(),
                        "speed": 3 + __import__('random').random() * 5,
                        "length": 10 + __import__('random').random() * 15,
                    })
            elif "snow" in desc.lower():
                for _ in range(50):
                    self.particles.append({
                        "type": "snow",
                        "x": __import__('random').random() * self.width(),
                        "y": __import__('random').random() * self.height(),
                        "speed": 0.5 + __import__('random').random() * 2,
                        "size": 2 + __import__('random').random() * 4,
                        "drift": __import__('random').random() * 2 - 1,
                    })
            elif "cloud" in desc.lower() or "overcast" in desc.lower():
                for _ in range(8):
                    self.particles.append({
                        "type": "cloud",
                        "x": __import__('random').random() * self.width(),
                        "y": 20 + __import__('random').random() * 100,
                        "speed": 0.3 + __import__('random').random() * 0.5,
                        "size": 40 + __import__('random').random() * 60,
                    })
            else:
                # 晴天 - 阳光效果
                self.particles.append({
                    "type": "sun",
                    "x": self.width() * 0.8,
                    "y": 60,
                    "radius": 40,
                })

            self.update()
        except (KeyError, IndexError, TypeError):
            pass

    def _animate(self):
        import random
        for p in self.particles:
            if p["type"] == "rain":
                p["y"] += p["speed"]
                if p["y"] > self.height():
                    p["y"] = -20
                    p["x"] = random.random() * self.width()
            elif p["type"] == "snow":
                p["y"] += p["speed"]
                p["x"] += p["drift"]
                if p["y"] > self.height():
                    p["y"] = -10
                    p["x"] = random.random() * self.width()
            elif p["type"] == "cloud":
                p["x"] += p["speed"]
                if p["x"] > self.width() + p["size"]:
                    p["x"] = -p["size"] * 2

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 背景渐变
        gradient = QLinearGradient(0, 0, 0, h)

        if not self.weather_data:
            gradient.setColorAt(0, QColor(10, 10, 30))
            gradient.setColorAt(1, QColor(5, 5, 20))
        else:
            try:
                current = self.weather_data.get("current_condition", [{}])[0]
                desc = current.get("weatherDesc", [{}])[0].get("value", "").lower()
                is_day = current.get("is_day_time", "1") == "1"

                if is_day:
                    if "rain" in desc or "drizzle" in desc:
                        gradient.setColorAt(0, QColor(40, 50, 70))
                        gradient.setColorAt(1, QColor(20, 25, 40))
                    elif "cloud" in desc:
                        gradient.setColorAt(0, QColor(50, 55, 70))
                        gradient.setColorAt(1, QColor(30, 35, 50))
                    elif "snow" in desc:
                        gradient.setColorAt(0, QColor(60, 70, 90))
                        gradient.setColorAt(1, QColor(40, 45, 60))
                    else:
                        gradient.setColorAt(0, QColor(30, 60, 120))
                        gradient.setColorAt(1, QColor(10, 30, 60))
                else:
                    gradient.setColorAt(0, QColor(5, 5, 25))
                    gradient.setColorAt(1, QColor(2, 2, 15))
            except (KeyError, IndexError, TypeError):
                gradient.setColorAt(0, QColor(10, 10, 30))
                gradient.setColorAt(1, QColor(5, 5, 20))

        painter.fillRect(0, 0, w, h, gradient)

        # 地面
        ground_gradient = QLinearGradient(0, h - 60, 0, h)
        ground_gradient.setColorAt(0, QColor(15, 25, 15))
        ground_gradient.setColorAt(1, QColor(10, 18, 10))
        painter.fillRect(0, h - 60, w, 60, ground_gradient)

        # 绘制粒子
        for p in self.particles:
            if p["type"] == "rain":
                pen = QPen(QColor(100, 150, 255, 150), 1)
                painter.setPen(pen)
                painter.drawLine(int(p["x"]), int(p["y"]),
                                 int(p["x"]), int(p["y"] + p["length"]))

            elif p["type"] == "snow":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(220, 230, 255, 200)))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])

            elif p["type"] == "cloud":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(100, 110, 130, 100)))
                s = p["size"]
                painter.drawEllipse(QPointF(p["x"], p["y"]), s, s * 0.5)
                painter.drawEllipse(QPointF(p["x"] - s * 0.3, p["y"] + 5), s * 0.7, s * 0.4)
                painter.drawEllipse(QPointF(p["x"] + s * 0.3, p["y"] + 3), s * 0.6, s * 0.35)

            elif p["type"] == "sun":
                # 太阳光晕
                radial = QRadialGradient(QPointF(p["x"], p["y"]), p["radius"] * 3)
                radial.setColorAt(0, QColor(255, 200, 50, 80))
                radial.setColorAt(0.5, QColor(255, 180, 30, 20))
                radial.setColorAt(1, QColor(255, 180, 30, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(radial))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["radius"] * 3, p["radius"] * 3)

                # 太阳
                painter.setBrush(QBrush(QColor(255, 220, 80)))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["radius"], p["radius"])

        # 绘制天气信息
        if self.weather_data:
            try:
                current = self.weather_data.get("current_condition", [{}])[0]
                area = self.weather_data.get("nearest_area", [{}])[0]
                city = area.get("areaName", [{}])[0].get("value", "")
                temp = current.get("temp_C", "?")
                desc = current.get("weatherDesc", [{}])[0].get("value", "")
                cn_desc = get_weather_cn(desc)

                painter.setPen(QColor(255, 255, 255, 200))
                font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(20, 30, f"{city}  {temp}°C  {cn_desc}")

            except (KeyError, IndexError, TypeError):
                pass

        painter.end()


# ============================================================
# 天气预警组件
# ============================================================

class WeatherAlertsWidget(QWidget):
    """天气预警"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 根据天气条件生成预警
        self.alert_container = QVBoxLayout()
        layout.addLayout(self.alert_container)

        # 默认提示
        self.no_alert_label = QLabel("✅ 当前没有天气预警")
        self.no_alert_label.setStyleSheet(f"""
            font-size: 16px;
            color: {COLORS['success']};
            padding: 30px;
        """)
        self.no_alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.no_alert_label)

    def update_data(self, data: dict):
        """根据天气数据生成预警"""
        # 清除旧预警
        while self.alert_container.count():
            item = self.alert_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        alerts = []
        try:
            current = data.get("current_condition", [{}])[0]
            weather = data.get("weather", [])

            temp = int(current.get("temp_C", 20))
            humidity = int(current.get("humidity", 50))
            wind = int(current.get("windspeedKmph", 0))
            uv = int(current.get("uvIndex", 0))
            visibility = int(current.get("visibility", 10))

            # 高温预警
            if temp >= 35:
                alerts.append(("高温预警", "danger",
                               f"当前温度 {temp}°C，已超过35°C。请注意防暑降温，避免长时间户外活动。"))
            elif temp >= 33:
                alerts.append(("高温提醒", "warning",
                               f"当前温度 {temp}°C，天气炎热，请注意防晒和补水。"))

            # 低温预警
            if temp <= 0:
                alerts.append(("低温预警", "danger",
                               f"当前温度 {temp}°C，已低于0°C。请注意保暖防寒，注意路面结冰。"))
            elif temp <= 5:
                alerts.append(("低温提醒", "info",
                               f"当前温度 {temp}°C，天气寒冷，请注意保暖。"))

            # 大风预警
            if wind >= 60:
                alerts.append(("大风预警", "danger",
                               f"当前风速 {wind}km/h，已达大风级别。请注意安全，避免户外活动。"))
            elif wind >= 40:
                alerts.append(("大风提醒", "warning",
                               f"当前风速 {wind}km/h，风力较大，请注意防风。"))

            # UV预警
            if uv >= 8:
                alerts.append(("紫外线预警", "danger",
                               f"紫外线指数 {uv}，非常强。请做好防晒措施，避免在阳光下暴晒。"))
            elif uv >= 6:
                alerts.append(("紫外线提醒", "warning",
                               f"紫外线指数 {uv}，较强。外出请涂抹防晒霜，戴帽子和太阳镜。"))

            # 能见度预警
            if visibility <= 1:
                alerts.append(("大雾预警", "danger",
                               f"当前能见度 {visibility}km，极低。请注意交通安全。"))
            elif visibility <= 4:
                alerts.append(("低能见度提醒", "warning",
                               f"当前能见度 {visibility}km，较低。出行请注意安全。"))

            # 降雨提醒
            for day in weather[:2]:
                for hour in day.get("hourly", []):
                    rain_chance = int(hour.get("chanceofrain", 0))
                    if rain_chance >= 70:
                        desc = hour.get("weatherDesc", [{}])[0].get("value", "")
                        time_val = hour.get("time", "0")
                        try:
                            h = int(time_val) // 100
                            time_str = f"{h:02d}:00"
                        except ValueError:
                            time_str = time_val
                        alerts.append(("降雨提醒", "info",
                                       f"预计{time_str}有{get_weather_cn(desc)}，降雨概率{rain_chance}%。出门请携带雨具。"))
                        break
                else:
                    continue
                break

            # 显示预警
            if alerts:
                self.no_alert_label.hide()
                for level, severity, message in alerts:
                    alert_card = self._create_alert_card(level, severity, message)
                    self.alert_container.addWidget(alert_card)
            else:
                self.no_alert_label.show()

        except (KeyError, IndexError, TypeError) as e:
            print(f"Error updating alerts: {e}")
            self.no_alert_label.show()

    def _create_alert_card(self, title: str, severity: str, message: str) -> Card:
        card = Card()

        colors = {
            "danger": COLORS["danger"],
            "warning": COLORS["warning"],
            "info": COLORS["info"],
        }
        icons = {
            "danger": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }

        color = colors.get(severity, COLORS["info"])
        icon = icons.get(severity, "🔵")

        # 顶部色条
        card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['card']};
                border: 1px solid {color};
                border-left: 4px solid {color};
                border-radius: 14px;
                padding: 0px;
            }}
        """)

        h_layout = QHBoxLayout(card.layout)
        h_layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px;")
        icon_lbl.setFixedWidth(30)
        h_layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        text_layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        msg_lbl.setWordWrap(True)
        text_layout.addWidget(msg_lbl)

        h_layout.addLayout(text_layout, 1)

        return card


# ============================================================
# 城市管理组件
# ============================================================

class CityManagerWidget(QWidget):
    """城市管理"""

    city_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cities = DEFAULT_CITIES.copy()
        self._load_config()
        self._setup_ui()

    def _load_config(self):
        """加载配置"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_cities = config.get("cities", [])
                    if saved_cities:
                        self.cities = saved_cities
        except Exception:
            pass

    def _save_config(self):
        """保存配置"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {"cities": self.cities}
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["cities"] = self.cities
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入城市名称（中文或英文）...")
        self.search_input.returnPressed.connect(self._add_city)
        search_layout.addWidget(self.search_input)

        add_btn = QPushButton("➕ 添加")
        add_btn.setFixedWidth(80)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent1']}, stop:1 {COLORS['accent2']});
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent2']}, stop:1 {COLORS['accent1']});
            }}
        """)
        add_btn.clicked.connect(self._add_city)
        search_layout.addWidget(add_btn)

        layout.addLayout(search_layout)

        # 城市列表
        self.city_list = QListWidget()
        self.city_list.setMinimumHeight(200)
        self._refresh_list()
        self.city_list.itemClicked.connect(self._on_city_clicked)
        layout.addWidget(self.city_list)

        # 删除按钮
        del_btn = QPushButton("🗑️ 删除选中城市")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['input_bg']};
                border: 1px solid {COLORS['danger']};
                border-radius: 8px;
                color: {COLORS['danger']};
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)
        del_btn.clicked.connect(self._delete_city)
        layout.addWidget(del_btn)

    def _refresh_list(self):
        self.city_list.clear()
        for city in self.cities:
            item = QListWidgetItem(f"📍 {city}")
            item.setSizeHint(QSize(0, 36))
            self.city_list.addItem(item)

    def _add_city(self):
        city = self.search_input.text().strip()
        if city and city not in self.cities:
            self.cities.append(city)
            self._refresh_list()
            self._save_config()
            self.search_input.clear()

    def _delete_city(self):
        row = self.city_list.currentRow()
        if row >= 0 and len(self.cities) > 1:
            self.cities.pop(row)
            self._refresh_list()
            self._save_config()

    def _on_city_clicked(self, item: QListWidgetItem):
        row = self.city_list.row(item)
        if 0 <= row < len(self.cities):
            self.city_selected.emit(self.cities[row])

    def get_cities(self) -> list:
        return self.cities


# ============================================================
# 主窗口
# ============================================================

class WeatherApp(QMainWindow):
    """天气预报主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🌤️ {APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        self.current_city = "Beijing"
        self.worker = None

        self._setup_ui()
        self._load_last_city()
        self._fetch_weather()

    def _setup_ui(self):
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # ---- 左侧面板 (城市列表) ----
        left_panel = QWidget()
        left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Logo
        logo_label = QLabel("🌤️ 天气预报")
        logo_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {COLORS['text']};
            padding: 10px 0;
        """)
        left_layout.addWidget(logo_label)

        # 城市管理
        self.city_manager = CityManagerWidget()
        self.city_manager.city_selected.connect(self._on_city_selected)
        left_layout.addWidget(self.city_manager)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新天气数据")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent1']}, stop:1 {COLORS['accent2']});
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent2']}, stop:1 {COLORS['accent1']});
            }}
        """)
        refresh_btn.clicked.connect(self._fetch_weather)
        left_layout.addWidget(refresh_btn)

        # 加载状态
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_dim']};
            padding: 4px;
        """)
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()

        # 版本信息
        ver_label = QLabel(f"v{APP_VERSION} · Powered by wttr.in")
        ver_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_dim']};")
        left_layout.addWidget(ver_label)

        main_layout.addWidget(left_panel)

        # ---- 右侧面板 (主要内容) ----
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # 当前天气
        self.current_weather = CurrentWeatherWidget()
        self.tabs.addTab(self.current_weather, "🌡️ 当前天气")

        # 7天预报
        self.forecast_widget = ForecastWidget()
        self.tabs.addTab(self.forecast_widget, "📅 7天预报")

        # 逐小时预报
        self.hourly_widget = HourlyWidget()
        self.tabs.addTab(self.hourly_widget, "⏰ 逐小时")

        # 空气质量
        self.aqi_widget = AirQualityWidget()
        self.tabs.addTab(self.aqi_widget, "💨 空气质量")

        # 日出日落
        self.sun_moon_widget = SunMoonWidget()
        self.tabs.addTab(self.sun_moon_widget, "🌅 日月")

        # 天气地图
        self.weather_map = WeatherMapWidget()
        self.tabs.addTab(self.weather_map, "🗺️ 天气地图")

        # 天气预警
        self.alerts_widget = WeatherAlertsWidget()
        self.tabs.addTab(self.alerts_widget, "⚠️ 预警")

        right_layout.addWidget(self.tabs)

        main_layout.addWidget(right_panel, 1)

    def _load_last_city(self):
        """加载上次使用的城市"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.current_city = config.get("last_city", "Beijing")
        except Exception:
            pass

    def _save_last_city(self):
        """保存当前城市"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {}
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["last_city"] = self.current_city
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _on_city_selected(self, city: str):
        """城市选择回调"""
        self.current_city = city
        self._save_last_city()
        self._fetch_weather()

    def _fetch_weather(self):
        """获取天气数据"""
        if self.worker and self.worker.isRunning():
            return

        self.status_label.setText("⏳ 正在获取天气数据...")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['warning']}; padding: 4px;")

        self.worker = WeatherWorker(self.current_city)
        self.worker.finished.connect(self._on_weather_loaded)
        self.worker.error.connect(self._on_weather_error)
        self.worker.start()

    def _on_weather_loaded(self, data: dict):
        """天气数据加载完成"""
        self.status_label.setText("✅ 数据已更新")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['success']}; padding: 4px;")

        # 3秒后清除状态
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

        # 更新所有组件
        self.current_weather.update_data(data)
        self.forecast_widget.update_data(data)
        self.hourly_widget.update_data(data)
        self.aqi_widget.update_data(data)
        self.sun_moon_widget.update_data(data)
        self.weather_map.update_data(data)
        self.alerts_widget.update_data(data)

    def _on_weather_error(self, error: str):
        """天气数据加载失败"""
        self.status_label.setText(f"❌ 获取失败: {error[:50]}")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['danger']}; padding: 4px;")


# ============================================================
# 程序入口
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    # 设置深色调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['input_bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['card']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['card']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['card']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(COLORS['accent1']))
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['accent1']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent1']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS['text']))
    app.setPalette(palette)

    # 应用样式表
    app.setStyleSheet(STYLESHEET)

    # 创建并显示主窗口
    window = WeatherApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
