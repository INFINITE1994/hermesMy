#!/usr/bin/env python3
"""
BatteryMonitor - Windows 电池监控工具
实时监控电池状态、健康状况、功耗、充电历史等
"""

import sys
import os
import csv
import time
import json
import ctypes
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QProgressBar,
    QTabWidget, QSpinBox, QCheckBox, QComboBox, QMessageBox,
    QFileDialog, QGroupBox, QLineEdit, QTimeEdit, QSlider,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QSystemTrayIcon, QMenu, QStyle, QDialog, QFormLayout,
    QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, pyqtSignal, QThread
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QPainter,
    QBrush, QPen, QPixmap, QIcon, QAction, QFontDatabase
)

# ──────────────────────────────────────────────
# 数据收集线程
# ──────────────────────────────────────────────
class BatteryDataCollector(QThread):
    """后台线程：持续收集电池数据"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.history = []
        self.max_history = 3600  # 1小时的数据（每秒一次）
    
    def run(self):
        while self.running:
            try:
                data = self.collect_battery_data()
                self.history.append(data)
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]
                self.data_updated.emit(data)
            except Exception as e:
                pass
            time.sleep(1)
    
    def collect_battery_data(self):
        """收集电池数据"""
        battery = psutil.sensors_battery()
        if battery is None:
            return {
                'percent': 0,
                'power_plugged': False,
                'time_left': 0,
                'status': '未检测到电池',
                'timestamp': datetime.now(),
                'voltage': 0,
                'current': 0,
                'power': 0,
            }
        
        # 获取电池详细信息
        try:
            # 尝试通过 WMI 获取更详细的电池信息
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-WmiObject -Class Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus, EstimatedRunTime, DesignVoltage, FullChargeCapacity, DesignCapacity | ConvertTo-Json'],
                capture_output=True, timeout=5
            )
            stdout = result.stdout.decode('utf-8', errors='replace')
            wmi_data = json.loads(stdout) if stdout.strip() else {}
        except:
            wmi_data = {}
        
        # 计算功耗
        power = 0
        if battery.power_plugged:
            status = '充电中'
        else:
            status = '放电中'
            # 估算功耗（基于电池容量和剩余时间）
            if battery.secsleft > 0 and battery.percent > 0:
                # 假设电池容量约 50Wh
                capacity_wh = 50
                remaining_wh = capacity_wh * (battery.percent / 100)
                if battery.secsleft > 0:
                    power = remaining_wh / (battery.secsleft / 3600)
        
        return {
            'percent': battery.percent,
            'power_plugged': battery.power_plugged,
            'time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
            'status': status,
            'timestamp': datetime.now(),
            'voltage': wmi_data.get('DesignVoltage', 0) / 1000 if wmi_data.get('DesignVoltage') else 0,
            'current': power / 12 if power > 0 else 0,  # 假设 12V
            'power': power,
            'wmi': wmi_data,
        }
    
    def get_history(self, minutes=60):
        """获取历史数据"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [d for d in self.history if d['timestamp'] > cutoff]
    
    def stop(self):
        self.running = False
        self.wait()


# ──────────────────────────────────────────────
# 自定义组件：圆形电池指示器
# ──────────────────────────────────────────────
class CircularBatteryIndicator(QWidget):
    """圆形电池电量指示器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percent = 0
        self.status = ""
        self.setMinimumSize(200, 200)
    
    def set_value(self, percent, status=""):
        self.percent = percent
        self.status = status
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        x = (width - size) / 2
        y = (height - size) / 2
        
        # 背景圆环
        pen = QPen(QColor("#222244"), 12)
        painter.setPen(pen)
        painter.drawEllipse(int(x), int(y), int(size), int(size))
        
        # 进度圆环（渐变色）
        gradient = QLinearGradient(x, y, x + size, y + size)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#764ba2"))
        
        pen = QPen(QBrush(gradient), 12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        span_angle = int(self.percent * 360 / 100 * 16)
        start_angle = 90 * 16
        painter.drawArc(int(x + 6), int(y + 6), int(size - 12), int(size - 12), 
                       start_angle, span_angle)
        
        # 中心文字
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 36, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.percent}%")
        
        # 状态文字
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#8888aa"))
        painter.drawText(
            self.rect().adjusted(0, 50, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            self.status
        )
        
        painter.end()


# ──────────────────────────────────────────────
# 样式表
# ──────────────────────────────────────────────
STYLESHEET = """
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}

QTabWidget::pane {
    border: 1px solid #222244;
    background-color: #0a0a0a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #111122;
    color: #8888aa;
    padding: 12px 24px;
    margin: 2px;
    border-radius: 6px 6px 0 0;
    font-size: 13px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover {
    background-color: #1a1a33;
}

QFrame#card {
    background-color: #111122;
    border: 1px solid #222244;
    border-radius: 12px;
    padding: 16px;
}

QLabel {
    color: #ffffff;
    background: transparent;
}

QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 14px;
    color: #8888aa;
}

QLabel#value {
    font-size: 24px;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    -webkit-background-clip: text;
    color: #667eea;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7788ff, stop:1 #8855cc);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5566dd, stop:1 #6633aa);
}

QPushButton#secondary {
    background-color: #222244;
    border: 1px solid #333366;
}

QPushButton#secondary:hover {
    background-color: #2a2a55;
}

QProgressBar {
    background-color: #222244;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: white;
    font-size: 10px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}

QSpinBox, QComboBox, QLineEdit, QTimeEdit {
    background-color: #1a1a33;
    border: 1px solid #333366;
    border-radius: 6px;
    padding: 8px;
    color: white;
    font-size: 13px;
}

QSpinBox:focus, QComboBox:focus, QLineEdit:focus, QTimeEdit:focus {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8888aa;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #222244;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 24px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #667eea;
}

QTableWidget {
    background-color: #111122;
    border: 1px solid #222244;
    border-radius: 8px;
    gridline-color: #222244;
    color: #ffffff;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #1a1a33;
}

QTableWidget::item:selected {
    background-color: #222244;
}

QHeaderView::section {
    background-color: #1a1a33;
    color: #8888aa;
    padding: 10px;
    border: none;
    border-right: 1px solid #222244;
    border-bottom: 1px solid #222244;
    font-weight: bold;
}

QCheckBox {
    spacing: 8px;
    color: #ffffff;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #333366;
    border-radius: 4px;
    background-color: #1a1a33;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-color: #667eea;
}

QSlider::groove:horizontal {
    background: #222244;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #333366;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}
"""


# ──────────────────────────────────────────────
# 主窗口
# ──────────────────────────────────────────────
class BatteryMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BatteryMonitor - 电池监控工具")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        
        # 初始化数据收集器
        self.collector = BatteryDataCollector()
        self.collector.data_updated.connect(self.update_battery_data)
        
        # 初始化 UI
        self.init_ui()
        
        # 启动数据收集
        self.collector.start()
        
        # 告警设置
        self.alert_threshold = 20
        self.alert_enabled = True
        self.alert_shown = False
        
        # 睡眠定时器
        self.sleep_timer = None
        self.sleep_minutes = 0
        
        # 充电历史记录
        self.charge_history = []
        
    def init_ui(self):
        """初始化用户界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 顶部标题
        header = QHBoxLayout()
        title = QLabel("🔋 BatteryMonitor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #667eea;")
        header.addWidget(title)
        
        header.addStretch()
        
        # 状态指示器
        self.status_label = QLabel("● 实时监控中")
        self.status_label.setStyleSheet("color: #4ade80; font-size: 13px;")
        header.addWidget(self.status_label)
        
        layout.addLayout(header)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #222244; max-height: 1px;")
        layout.addWidget(line)
        
        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_status_tab(), "📊 电池状态")
        self.tabs.addTab(self.create_health_tab(), "💊 电池健康")
        self.tabs.addTab(self.create_power_plan_tab(), "⚡ 电源计划")
        self.tabs.addTab(self.create_history_tab(), "📈 充电历史")
        self.tabs.addTab(self.create_alerts_tab(), "🔔 电池告警")
        self.tabs.addTab(self.create_consumption_tab(), "🔌 功耗监控")
        self.tabs.addTab(self.create_sleep_tab(), "😴 睡眠定时")
        self.tabs.addTab(self.create_export_tab(), "💾 数据导出")
        
        layout.addWidget(self.tabs)
    
    def create_card(self, title_text, layout_class=QVBoxLayout):
        """创建卡片容器"""
        frame = QFrame()
        frame.setObjectName("card")
        layout = layout_class(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        if title_text:
            title = QLabel(title_text)
            title.setObjectName("title")
            layout.addWidget(title)
        
        return frame, layout
    
    # ── 电池状态标签页 ──
    def create_status_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        
        # 左侧：圆形指示器
        left_frame, left_layout = self.create_card("")
        
        self.battery_indicator = CircularBatteryIndicator()
        left_layout.addWidget(self.battery_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.battery_status_label = QLabel("检测中...")
        self.battery_status_label.setStyleSheet("font-size: 16px; color: #8888aa; margin-top: 10px;")
        self.battery_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.battery_status_label)
        
        left_frame.setFixedWidth(300)
        layout.addWidget(left_frame)
        
        # 右侧：详细信息
        right_frame, right_layout = self.create_card("电池详细信息")
        
        info_grid = QGridLayout()
        info_grid.setSpacing(16)
        
        self.info_labels = {}
        info_items = [
            ("电量百分比", "percent"),
            ("充电状态", "status"),
            ("剩余时间", "time_left"),
            ("电压", "voltage"),
            ("电流", "current"),
            ("功率", "power"),
            ("电源连接", "plugged"),
            ("更新时间", "updated"),
        ]
        
        for i, (label_text, key) in enumerate(info_items):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            label.setStyleSheet("color: #8888aa; font-size: 12px;")
            info_grid.addWidget(label, row, col)
            
            value = QLabel("--")
            value.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold;")
            info_grid.addWidget(value, row, col + 1)
            
            self.info_labels[key] = value
        
        right_layout.addLayout(info_grid)
        right_layout.addStretch()
        
        layout.addWidget(right_frame)
        
        return widget
    
    # ── 电池健康标签页 ──
    def create_health_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 健康概览
        overview_frame, overview_layout = self.create_card("电池健康概览")
        
        health_grid = QGridLayout()
        health_grid.setSpacing(20)
        
        # 健康度
        health_group = QVBoxLayout()
        health_label = QLabel("电池健康度")
        health_label.setStyleSheet("color: #8888aa;")
        health_group.addWidget(health_label)
        
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(85)
        self.health_bar.setFormat("%p%")
        health_group.addWidget(self.health_bar)
        
        health_grid.addLayout(health_group, 0, 0)
        
        # 设计容量
        self.design_capacity_label = QLabel("设计容量: --")
        self.design_capacity_label.setStyleSheet("font-size: 14px;")
        health_grid.addWidget(self.design_capacity_label, 0, 1)
        
        # 当前容量
        self.current_capacity_label = QLabel("当前容量: --")
        self.current_capacity_label.setStyleSheet("font-size: 14px;")
        health_grid.addWidget(self.current_capacity_label, 0, 2)
        
        overview_layout.addLayout(health_grid)
        layout.addWidget(overview_frame)
        
        # 电池详细信息
        detail_frame, detail_layout = self.create_card("电池详细信息")
        
        detail_grid = QGridLayout()
        detail_grid.setSpacing(12)
        
        self.health_details = {}
        details = [
            ("制造商", "manufacturer"),
            ("序列号", "serial"),
            ("化学类型", "chemistry"),
            ("循环次数", "cycles"),
            ("设计电压", "design_voltage"),
            ("磨损程度", "wear_level"),
        ]
        
        for i, (label_text, key) in enumerate(details):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text + ":")
            label.setStyleSheet("color: #8888aa; font-size: 13px;")
            detail_grid.addWidget(label, row, col)
            
            value = QLabel("检测中...")
            value.setStyleSheet("font-size: 13px;")
            detail_grid.addWidget(value, row, col + 1)
            
            self.health_details[key] = value
        
        detail_layout.addLayout(detail_grid)
        layout.addWidget(detail_frame)
        
        # 刷新按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新电池信息")
        refresh_btn.clicked.connect(self.refresh_health_info)
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    # ── 电源计划标签页 ──
    def create_power_plan_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 当前计划
        current_frame, current_layout = self.create_card("当前电源计划")
        
        self.current_plan_label = QLabel("检测中...")
        self.current_plan_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        current_layout.addWidget(self.current_plan_label)
        
        layout.addWidget(current_frame)
        
        # 可用计划
        plans_frame, plans_layout = self.create_card("可用电源计划")
        
        self.plan_buttons = []
        plans = [
            ("节能模式", "节能", "降低性能以延长电池续航"),
            ("平衡模式", "平衡", "平衡性能与能耗（推荐）"),
            ("高性能模式", "高性能", "最大性能，较高能耗"),
        ]
        
        for name, scheme, desc in plans:
            plan_widget = QFrame()
            plan_widget.setStyleSheet("""
                QFrame {
                    background-color: #1a1a33;
                    border: 1px solid #333366;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    border: 1px solid #667eea;
                }
            """)
            plan_layout = QHBoxLayout(plan_widget)
            
            info_layout = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setStyleSheet("font-size: 15px; font-weight: bold;")
            info_layout.addWidget(name_label)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #8888aa; font-size: 12px;")
            info_layout.addWidget(desc_label)
            
            plan_layout.addLayout(info_layout)
            plan_layout.addStretch()
            
            btn = QPushButton("应用")
            btn.setFixedWidth(80)
            btn.clicked.connect(lambda checked, s=scheme: self.apply_power_plan(s))
            plan_layout.addWidget(btn)
            
            self.plan_buttons.append(btn)
            plans_layout.addWidget(plan_widget)
        
        layout.addWidget(plans_frame)
        layout.addStretch()
        
        return widget
    
    # ── 充电历史标签页 ──
    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 时间范围选择
        range_frame, range_layout = self.create_card("")
        range_layout.setContentsMargins(12, 12, 12, 12)
        
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("显示时间范围:"))
        
        self.history_range = QComboBox()
        self.history_range.addItems(["最近 5 分钟", "最近 15 分钟", "最近 30 分钟", "最近 1 小时"])
        self.history_range.currentIndexChanged.connect(self.update_history_chart)
        range_row.addWidget(self.history_range)
        
        range_row.addStretch()
        
        clear_btn = QPushButton("清除历史")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self.clear_history)
        range_row.addWidget(clear_btn)
        
        range_layout.addLayout(range_row)
        layout.addWidget(range_frame)
        
        # 图表区域（使用简单绘图）
        chart_frame, chart_layout = self.create_card("电量变化趋势")
        
        self.chart_widget = QWidget()
        self.chart_widget.setMinimumHeight(300)
        self.chart_widget.paintEvent = self.paint_chart
        chart_layout.addWidget(self.chart_widget)
        
        layout.addWidget(chart_frame)
        
        # 统计信息
        stats_frame, stats_layout = self.create_card("统计信息")
        
        stats_grid = QGridLayout()
        self.stats_labels = {}
        
        stats = [
            ("平均电量", "avg_percent"),
            ("最低电量", "min_percent"),
            ("最高电量", "max_percent"),
            ("充电次数", "charge_count"),
        ]
        
        for i, (name, key) in enumerate(stats):
            label = QLabel(name)
            label.setStyleSheet("color: #8888aa;")
            stats_grid.addWidget(label, i // 2, (i % 2) * 2)
            
            value = QLabel("--")
            value.setStyleSheet("font-weight: bold;")
            stats_grid.addWidget(value, i // 2, (i % 2) * 2 + 1)
            
            self.stats_labels[key] = value
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_frame)
        
        return widget
    
    def paint_chart(self, event):
        """绘制历史图表"""
        painter = QPainter(self.chart_widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.chart_widget.rect()
        w = rect.width()
        h = rect.height()
        
        # 背景
        painter.fillRect(rect, QColor("#0a0a0a"))
        
        # 获取历史数据
        minutes = [5, 15, 30, 60][self.history_range.currentIndex()]
        history = self.collector.get_history(minutes)
        
        if len(history) < 2:
            painter.setPen(QColor("#8888aa"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "等待数据收集...")
            painter.end()
            return
        
        # 绘制网格
        painter.setPen(QPen(QColor("#222244"), 1))
        for i in range(5):
            y = int(h * i / 4)
            painter.drawLine(40, y, w - 10, y)
        
        # 绘制数据线
        gradient = QLinearGradient(0, 0, w, 0)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#764ba2"))
        
        pen = QPen(QBrush(gradient), 2)
        painter.setPen(pen)
        
        points = []
        for i, data in enumerate(history):
            x = int(40 + (w - 50) * i / (len(history) - 1))
            y = int(h - (h - 20) * data['percent'] / 100)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Y 轴标签
        painter.setPen(QColor("#8888aa"))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        for i in range(5):
            y = int(h * i / 4)
            painter.drawText(5, y + 5, f"{100 - i * 25}%")
        
        painter.end()
    
    # ── 电池告警标签页 ──
    def create_alerts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 告警设置
        settings_frame, settings_layout = self.create_card("告警设置")
        
        # 启用告警
        self.alert_enabled_check = QCheckBox("启用低电量告警")
        self.alert_enabled_check.setChecked(True)
        self.alert_enabled_check.stateChanged.connect(self.toggle_alert)
        settings_layout.addWidget(self.alert_enabled_check)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("低电量阈值:"))
        
        self.alert_threshold_spin = QSpinBox()
        self.alert_threshold_spin.setRange(5, 50)
        self.alert_threshold_spin.setValue(20)
        self.alert_threshold_spin.setSuffix("%")
        self.alert_threshold_spin.valueChanged.connect(self.set_alert_threshold)
        threshold_layout.addWidget(self.alert_threshold_spin)
        
        threshold_layout.addStretch()
        settings_layout.addLayout(threshold_layout)
        
        # 告警动作
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("告警动作:"))
        
        self.alert_action = QComboBox()
        self.alert_action.addItems(["仅显示通知", "播放声音", "进入睡眠模式", "进入休眠模式"])
        action_layout.addWidget(self.alert_action)
        
        action_layout.addStretch()
        settings_layout.addLayout(action_layout)
        
        layout.addWidget(settings_frame)
        
        # 充电完成告警
        charge_frame, charge_layout = self.create_card("充电完成告警")
        
        self.charge_alert_check = QCheckBox("电池充满时提醒")
        self.charge_alert_check.setChecked(True)
        charge_layout.addWidget(self.charge_alert_check)
        
        self.charge_threshold_spin = QSpinBox()
        self.charge_threshold_spin.setRange(80, 100)
        self.charge_threshold_spin.setValue(95)
        self.charge_threshold_spin.setSuffix("%")
        
        charge_row = QHBoxLayout()
        charge_row.addWidget(QLabel("提醒阈值:"))
        charge_row.addWidget(self.charge_threshold_spin)
        charge_row.addStretch()
        charge_layout.addLayout(charge_row)
        
        layout.addWidget(charge_frame)
        
        # 告警历史
        history_frame, history_layout = self.create_card("告警历史")
        
        self.alert_history_table = QTableWidget()
        self.alert_history_table.setColumnCount(3)
        self.alert_history_table.setHorizontalHeaderLabels(["时间", "类型", "详情"])
        self.alert_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.alert_history_table)
        
        layout.addWidget(history_frame)
        
        return widget
    
    # ── 功耗监控标签页 ──
    def create_consumption_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 实时功耗
        realtime_frame, realtime_layout = self.create_card("实时功耗")
        
        power_grid = QGridLayout()
        power_grid.setSpacing(20)
        
        self.power_labels = {}
        power_items = [
            ("当前功率", "current_power", "W"),
            ("平均功率", "avg_power", "W"),
            ("峰值功率", "peak_power", "W"),
            ("累计能耗", "total_energy", "Wh"),
        ]
        
        for i, (name, key, unit) in enumerate(power_items):
            group = QVBoxLayout()
            
            label = QLabel(name)
            label.setStyleSheet("color: #8888aa; font-size: 12px;")
            group.addWidget(label)
            
            value = QLabel(f"-- {unit}")
            value.setStyleSheet("font-size: 22px; font-weight: bold; color: #667eea;")
            group.addWidget(value)
            
            power_grid.addLayout(group, i // 2, i % 2)
            self.power_labels[key] = value
        
        realtime_layout.addLayout(power_grid)
        layout.addWidget(realtime_frame)
        
        # 进程功耗
        process_frame, process_layout = self.create_card("高耗电进程")
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["进程名称", "CPU %", "内存 %", "影响"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        process_layout.addWidget(self.process_table)
        
        refresh_btn = QPushButton("刷新进程列表")
        refresh_btn.clicked.connect(self.refresh_process_list)
        process_layout.addWidget(refresh_btn)
        
        layout.addWidget(process_frame)
        
        return widget
    
    # ── 睡眠定时标签页 ──
    def create_sleep_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 定时设置
        timer_frame, timer_layout = self.create_card("睡眠定时器")
        
        # 模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("操作:"))
        
        self.sleep_mode = QComboBox()
        self.sleep_mode.addItems(["睡眠", "休眠", "关机", "锁定屏幕"])
        mode_layout.addWidget(self.sleep_mode)
        mode_layout.addStretch()
        timer_layout.addLayout(mode_layout)
        
        # 时间设置
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("延迟时间:"))
        
        self.sleep_minutes_spin = QSpinBox()
        self.sleep_minutes_spin.setRange(1, 720)
        self.sleep_minutes_spin.setValue(30)
        self.sleep_minutes_spin.setSuffix(" 分钟")
        time_layout.addWidget(self.sleep_minutes_spin)
        time_layout.addStretch()
        timer_layout.addLayout(time_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.sleep_start_btn = QPushButton("▶ 开始定时")
        self.sleep_start_btn.clicked.connect(self.start_sleep_timer)
        btn_layout.addWidget(self.sleep_start_btn)
        
        self.sleep_stop_btn = QPushButton("⏹ 取消定时")
        self.sleep_stop_btn.setObjectName("secondary")
        self.sleep_stop_btn.clicked.connect(self.stop_sleep_timer)
        self.sleep_stop_btn.setEnabled(False)
        btn_layout.addWidget(self.sleep_stop_btn)
        
        btn_layout.addStretch()
        timer_layout.addLayout(btn_layout)
        
        # 倒计时显示
        self.sleep_countdown = QLabel("定时器未启动")
        self.sleep_countdown.setStyleSheet("font-size: 18px; color: #8888aa; margin-top: 10px;")
        self.sleep_countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.sleep_countdown)
        
        layout.addWidget(timer_frame)
        
        # 快捷按钮
        quick_frame, quick_layout = self.create_card("快捷操作")
        
        quick_grid = QGridLayout()
        quick_times = [5, 15, 30, 60, 120, 180]
        
        for i, minutes in enumerate(quick_times):
            btn = QPushButton(f"{minutes} 分钟后睡眠")
            btn.clicked.connect(lambda checked, m=minutes: self.quick_sleep(m))
            quick_grid.addWidget(btn, i // 3, i % 3)
        
        quick_layout.addLayout(quick_grid)
        layout.addWidget(quick_frame)
        
        layout.addStretch()
        
        return widget
    
    # ── 数据导出标签页 ──
    def create_export_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 导出设置
        export_frame, export_layout = self.create_card("数据导出")
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))
        
        self.export_format = QComboBox()
        self.export_format.addItems(["CSV 文件", "TXT 文件", "JSON 文件"])
        format_layout.addWidget(self.export_format)
        format_layout.addStretch()
        export_layout.addLayout(format_layout)
        
        # 时间范围
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("数据范围:"))
        
        self.export_range = QComboBox()
        self.export_range.addItems(["最近 5 分钟", "最近 15 分钟", "最近 30 分钟", "最近 1 小时", "全部数据"])
        range_layout.addWidget(self.export_range)
        range_layout.addStretch()
        export_layout.addLayout(range_layout)
        
        # 导出内容
        content_label = QLabel("导出内容:")
        export_layout.addWidget(content_label)
        
        self.export_checks = {
            'battery': QCheckBox("电池状态"),
            'health': QCheckBox("电池健康"),
            'power': QCheckBox("功耗数据"),
            'history': QCheckBox("充电历史"),
        }
        
        for check in self.export_checks.values():
            check.setChecked(True)
            export_layout.addWidget(check)
        
        # 导出按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        export_btn = QPushButton("📁 选择保存位置并导出")
        export_btn.setFixedWidth(200)
        export_btn.clicked.connect(self.export_data)
        btn_layout.addWidget(export_btn)
        
        export_layout.addLayout(btn_layout)
        
        layout.addWidget(export_frame)
        
        # 预览区域
        preview_frame, preview_layout = self.create_card("数据预览")
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["时间", "电量 %", "状态", "功率 W", "温度 °C"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        preview_layout.addWidget(self.preview_table)
        
        preview_btn_layout = QHBoxLayout()
        preview_btn = QPushButton("刷新预览")
        preview_btn.setObjectName("secondary")
        preview_btn.clicked.connect(self.refresh_preview)
        preview_btn_layout.addWidget(preview_btn)
        preview_btn_layout.addStretch()
        preview_layout.addLayout(preview_btn_layout)
        
        layout.addWidget(preview_frame)
        
        return widget
    
    # ──────────────────────────────────────────
    # 数据更新方法
    # ──────────────────────────────────────────
    def update_battery_data(self, data):
        """更新电池数据"""
        # 更新圆形指示器
        self.battery_indicator.set_value(data['percent'], data['status'])
        
        # 更新状态文本
        self.battery_status_label.setText(data['status'])
        
        # 更新详细信息
        self.info_labels['percent'].setText(f"{data['percent']}%")
        self.info_labels['status'].setText(data['status'])
        
        # 剩余时间
        if data['time_left'] > 0:
            hours = data['time_left'] // 3600
            minutes = (data['time_left'] % 3600) // 60
            self.info_labels['time_left'].setText(f"{hours}小时{minutes}分钟")
        elif data['time_left'] == -1:
            self.info_labels['time_left'].setText("计算中...")
        else:
            self.info_labels['time_left'].setText("已充满/充电中")
        
        self.info_labels['voltage'].setText(f"{data['voltage']:.1f} V")
        self.info_labels['current'].setText(f"{data['current']:.2f} A")
        self.info_labels['power'].setText(f"{data['power']:.1f} W")
        self.info_labels['plugged'].setText("是 ✓" if data['power_plugged'] else "否 ✗")
        self.info_labels['updated'].setText(data['timestamp'].strftime("%H:%M:%S"))
        
        # 存储历史
        self.charge_history.append(data)
        if len(self.charge_history) > 3600:
            self.charge_history = self.charge_history[-3600:]
        
        # 检查告警
        if self.alert_enabled and data['percent'] <= self.alert_threshold and not data['power_plugged']:
            if not self.alert_shown:
                self.show_alert(f"电池电量低！当前电量 {data['percent']}%", "warning")
                self.alert_shown = True
        elif data['percent'] > self.alert_threshold:
            self.alert_shown = False
        
        # 充电完成告警
        if (self.charge_alert_check.isChecked() and 
            data['percent'] >= self.charge_threshold_spin.value() and 
            data['power_plugged']):
            pass  # 可以添加充电完成通知
        
        # 更新图表
        self.update_history_chart()
        
        # 更新功耗
        self.update_power_display(data)
    
    def update_history_chart(self):
        """更新历史图表"""
        self.chart_widget.update()
        
        # 更新统计
        if self.charge_history:
            percents = [d['percent'] for d in self.charge_history]
            self.stats_labels['avg_percent'].setText(f"{sum(percents)/len(percents):.1f}%")
            self.stats_labels['min_percent'].setText(f"{min(percents)}%")
            self.stats_labels['max_percent'].setText(f"{max(percents)}%")
            
            # 计算充电次数
            charges = 0
            for i in range(1, len(self.charge_history)):
                if (self.charge_history[i]['power_plugged'] and 
                    not self.charge_history[i-1]['power_plugged']):
                    charges += 1
            self.stats_labels['charge_count'].setText(str(charges))
    
    def update_power_display(self, data):
        """更新功耗显示"""
        self.power_labels['current_power'].setText(f"{data['power']:.1f} W")
        
        if self.charge_history:
            powers = [d['power'] for d in self.charge_history if d['power'] > 0]
            if powers:
                self.power_labels['avg_power'].setText(f"{sum(powers)/len(powers):.1f} W")
                self.power_labels['peak_power'].setText(f"{max(powers):.1f} W")
                
                # 计算累计能耗 (Wh)
                total_wh = sum(powers) / 3600  # 每秒采样
                self.power_labels['total_energy'].setText(f"{total_wh:.2f} Wh")
    
    def refresh_health_info(self):
        """刷新电池健康信息"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-WmiObject -Class Win32_Battery | Select-Object * | ConvertTo-Json'],
                capture_output=True, timeout=10
            )
            
            stdout = result.stdout.decode('utf-8', errors='replace').strip()
            if stdout:
                data = json.loads(stdout)
                if isinstance(data, list):
                    data = data[0]
                
                self.health_details['manufacturer'].setText(data.get('Manufacturer', '未知'))
                self.health_details['serial'].setText(data.get('SerialNumber', '未知'))
                self.health_details['chemistry'].setText(data.get('Chemistry', '未知'))
                
                # 设计容量和当前容量
                design = data.get('DesignCapacity', 0)
                full_charge = data.get('FullChargeCapacity', 0)
                
                if design > 0:
                    self.design_capacity_label.setText(f"设计容量: {design} mWh")
                    self.current_capacity_label.setText(f"当前容量: {full_charge} mWh")
                    
                    health = (full_charge / design) * 100 if design > 0 else 0
                    self.health_bar.setValue(int(health))
                    self.health_details['wear_level'].setText(f"{100 - health:.1f}%")
                
                self.health_details['design_voltage'].setText(
                    f"{data.get('DesignVoltage', 0) / 1000:.1f} V"
                )
            else:
                # 使用 psutil 作为后备
                battery = psutil.sensors_battery()
                if battery:
                    self.health_details['manufacturer'].setText("系统电池")
                    self.health_details['serial'].setText("N/A")
                    self.health_details['chemistry'].setText("锂离子")
                    self.health_details['cycles'].setText("N/A")
                    self.health_details['design_voltage'].setText("N/A")
                    self.health_details['wear_level'].setText("N/A")
                    
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取电池信息失败: {str(e)}")
    
    def apply_power_plan(self, scheme):
        """应用电源计划"""
        try:
            # 获取电源方案 GUID
            result = subprocess.run(
                ['powercfg', '/list'],
                capture_output=True, timeout=10
            )
            stdout = result.stdout.decode('utf-8', errors='replace')
            
            schemes = {
                '节能': 'a1841308-3541-4fab-bc81-f71556f20b4a',
                '平衡': '381b4222-f694-41f0-9685-ff5bb260df2e',
                '高性能': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
            }
            
            guid = schemes.get(scheme)
            if guid:
                subprocess.run(['powercfg', '/setactive', guid], check=True)
                QMessageBox.information(self, "成功", f"已切换到{scheme}模式")
                self.refresh_power_plan()
            else:
                QMessageBox.warning(self, "错误", "未找到对应的电源方案")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"切换电源方案失败: {str(e)}")
    
    def refresh_power_plan(self):
        """刷新当前电源计划"""
        try:
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True, timeout=10
            )
            
            stdout = result.stdout.decode('utf-8', errors='replace')
            if stdout:
                # 解析输出
                parts = stdout.split()
                for i, part in enumerate(parts):
                    if '节能' in part or 'Power Saver' in part:
                        self.current_plan_label.setText("🔋 节能模式")
                        return
                    elif '平衡' in part or 'Balanced' in part:
                        self.current_plan_label.setText("⚖️ 平衡模式")
                        return
                    elif '高性能' in part or 'High Performance' in part:
                        self.current_plan_label.setText("🚀 高性能模式")
                        return
                
                self.current_plan_label.setText("⚡ 自定义电源方案")
        except:
            self.current_plan_label.setText("检测失败")
    
    def clear_history(self):
        """清除历史数据"""
        self.collector.history.clear()
        self.charge_history.clear()
        self.chart_widget.update()
        QMessageBox.information(self, "成功", "历史数据已清除")
    
    def toggle_alert(self, state):
        """切换告警状态"""
        self.alert_enabled = state == Qt.CheckState.Checked.value
    
    def set_alert_threshold(self, value):
        """设置告警阈值"""
        self.alert_threshold = value
    
    def show_alert(self, message, alert_type="info"):
        """显示告警"""
        self.add_alert_history(message, alert_type)
        
        if alert_type == "warning":
            QMessageBox.warning(self, "电池告警", message)
        else:
            QMessageBox.information(self, "通知", message)
    
    def add_alert_history(self, message, alert_type):
        """添加告警历史"""
        row = self.alert_history_table.rowCount()
        self.alert_history_table.insertRow(row)
        self.alert_history_table.setItem(row, 0, QTableWidgetItem(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.alert_history_table.setItem(row, 1, QTableWidgetItem(alert_type))
        self.alert_history_table.setItem(row, 2, QTableWidgetItem(message))
    
    def refresh_process_list(self):
        """刷新进程列表"""
        self.process_table.setRowCount(0)
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0.5:  # 只显示 CPU 使用率 > 0.5% 的进程
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按 CPU 使用率排序
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        for proc in processes[:20]:  # 只显示前 20 个
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)
            
            self.process_table.setItem(row, 0, QTableWidgetItem(proc['name']))
            self.process_table.setItem(row, 1, QTableWidgetItem(f"{proc['cpu_percent']:.1f}%"))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{proc['memory_percent']:.1f}%"))
            
            # 影响评估
            impact = "低"
            if proc['cpu_percent'] > 50:
                impact = "高"
            elif proc['cpu_percent'] > 20:
                impact = "中"
            self.process_table.setItem(row, 3, QTableWidgetItem(impact))
    
    def start_sleep_timer(self):
        """启动睡眠定时器"""
        self.sleep_minutes = self.sleep_minutes_spin.value()
        mode = self.sleep_mode.currentText()
        
        self.sleep_start_btn.setEnabled(False)
        self.sleep_stop_btn.setEnabled(True)
        self.sleep_countdown.setText(f"⏳ {mode}定时器已启动: {self.sleep_minutes} 分钟后")
        
        # 启动倒计时
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.update_sleep_countdown)
        self.sleep_timer.start(1000)  # 每秒更新
        
        self.sleep_end_time = datetime.now() + timedelta(minutes=self.sleep_minutes)
    
    def stop_sleep_timer(self):
        """停止睡眠定时器"""
        if self.sleep_timer:
            self.sleep_timer.stop()
            self.sleep_timer = None
        
        self.sleep_start_btn.setEnabled(True)
        self.sleep_stop_btn.setEnabled(False)
        self.sleep_countdown.setText("定时器已取消")
    
    def update_sleep_countdown(self):
        """更新睡眠倒计时"""
        remaining = (self.sleep_end_time - datetime.now()).total_seconds()
        
        if remaining <= 0:
            self.sleep_timer.stop()
            self.execute_sleep_action()
            return
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.sleep_countdown.setText(
            f"⏳ 剩余时间: {minutes:02d}:{seconds:02d}")
    
    def execute_sleep_action(self):
        """执行睡眠/休眠操作"""
        mode = self.sleep_mode.currentText()
        
        try:
            if mode == "睡眠":
                subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
            elif mode == "休眠":
                subprocess.run(['shutdown', '/h'])
            elif mode == "关机":
                subprocess.run(['shutdown', '/s', '/t', '0'])
            elif mode == "锁定屏幕":
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"执行操作失败: {str(e)}")
        
        self.stop_sleep_timer()
    
    def quick_sleep(self, minutes):
        """快捷睡眠设置"""
        self.sleep_minutes_spin.setValue(minutes)
        self.sleep_mode.setCurrentText("睡眠")
        self.start_sleep_timer()
    
    def export_data(self):
        """导出数据"""
        file_format = self.export_format.currentText()
        
        if "CSV" in file_format:
            ext = "csv"
            filter_str = "CSV 文件 (*.csv)"
        elif "TXT" in file_format:
            ext = "txt"
            filter_str = "文本文件 (*.txt)"
        else:
            ext = "json"
            filter_str = "JSON 文件 (*.json)"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出数据", 
            f"battery_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
            filter_str
        )
        
        if not filename:
            return
        
        try:
            # 获取要导出的数据
            data_range = self.export_range.currentIndex()
            minutes = [5, 15, 30, 60, 9999][data_range]
            
            if minutes >= 9999:
                history = self.collector.history
            else:
                history = self.collector.get_history(minutes)
            
            if ext == "csv":
                self.export_csv(filename, history)
            elif ext == "txt":
                self.export_txt(filename, history)
            else:
                self.export_json(filename, history)
            
            QMessageBox.information(self, "成功", f"数据已导出到:\n{filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")
    
    def export_csv(self, filename, data):
        """导出 CSV"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '电量 %', '状态', '功率 W', '电压 V', '电流 A'])
            
            for item in data:
                writer.writerow([
                    item['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    item['percent'],
                    item['status'],
                    f"{item['power']:.1f}",
                    f"{item['voltage']:.1f}",
                    f"{item['current']:.2f}",
                ])
    
    def export_txt(self, filename, data):
        """导出 TXT"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("BatteryMonitor - 电池数据导出\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for item in data:
                f.write(f"时间: {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  电量: {item['percent']}%\n")
                f.write(f"  状态: {item['status']}\n")
                f.write(f"  功率: {item['power']:.1f} W\n")
                f.write("-" * 40 + "\n")
    
    def export_json(self, filename, data):
        """导出 JSON"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'data_count': len(data),
            'data': [{
                'time': item['timestamp'].isoformat(),
                'percent': item['percent'],
                'status': item['status'],
                'power': item['power'],
                'voltage': item['voltage'],
                'current': item['current'],
            } for item in data]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def refresh_preview(self):
        """刷新预览"""
        self.preview_table.setRowCount(0)
        
        history = self.collector.get_history(5)  # 最近 5 分钟
        
        for item in history[-50:]:  # 最多显示 50 条
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            
            self.preview_table.setItem(row, 0, QTableWidgetItem(
                item['timestamp'].strftime('%H:%M:%S')))
            self.preview_table.setItem(row, 1, QTableWidgetItem(f"{item['percent']}%"))
            self.preview_table.setItem(row, 2, QTableWidgetItem(item['status']))
            self.preview_table.setItem(row, 3, QTableWidgetItem(f"{item['power']:.1f}"))
            self.preview_table.setItem(row, 4, QTableWidgetItem("--"))
    
    def closeEvent(self, event):
        """关闭事件"""
        self.collector.stop()
        
        if self.sleep_timer:
            self.sleep_timer.stop()
        
        event.accept()


# ──────────────────────────────────────────────
# 程序入口
# ──────────────────────────────────────────────
def main():
    # 设置 DPI 缩放
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    # 设置应用图标（使用系统图标）
    app.setWindowIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
    
    window = BatteryMonitor()
    window.show()
    
    # 初始化健康信息
    window.refresh_health_info()
    window.refresh_power_plan()
    window.refresh_process_list()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
