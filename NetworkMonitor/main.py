#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetworkMonitor - 网络监控工具
实时监控网络速度、流量和连接状态
"""

import sys
import os
import csv
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Optional

import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSystemTrayIcon, QMenu, QDialog, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QMessageBox, QFileDialog,
    QFrame, QScrollArea, QSplitter, QGroupBox, QCheckBox, QDoubleSpinBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPoint, QRect
)
from PyQt6.QtGui import (
    QIcon, QAction, QPainter, QColor, QLinearGradient, QPen,
    QFont, QPixmap, QBrush, QPalette, QFontDatabase, QPolygon
)


# ============================================================================
# 颜色主题
# ============================================================================
class Colors:
    BG = "#0a0a0a"
    CARD = "#111122"
    CARD_LIGHT = "#1a1a33"
    TEXT = "#ffffff"
    TEXT_DIM = "#8888aa"
    ACCENT1 = "#667eea"
    ACCENT2 = "#764ba2"
    SUCCESS = "#4ade80"
    WARNING = "#fbbf24"
    DANGER = "#f87171"
    BORDER = "#2a2a44"
    HOVER = "#222244"


# ============================================================================
# 样式表
# ============================================================================
STYLESHEET = f"""
QMainWindow {{
    background-color: {Colors.BG};
}}
QWidget {{
    background-color: {Colors.BG};
    color: {Colors.TEXT};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    background-color: {Colors.BG};
}}
QTabBar::tab {{
    background-color: {Colors.CARD};
    color: {Colors.TEXT_DIM};
    border: 1px solid {Colors.BORDER};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background-color: {Colors.CARD_LIGHT};
    color: {Colors.TEXT};
    border-bottom: 2px solid {Colors.ACCENT1};
}}
QTabBar::tab:hover {{
    background-color: {Colors.HOVER};
}}
QTableWidget {{
    background-color: {Colors.CARD};
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    gridline-color: {Colors.BORDER};
    selection-background-color: {Colors.ACCENT1};
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {Colors.BORDER};
}}
QTableWidget::item:selected {{
    background-color: {Colors.ACCENT1};
}}
QHeaderView::section {{
    background-color: {Colors.CARD_LIGHT};
    color: {Colors.TEXT_DIM};
    border: none;
    border-bottom: 2px solid {Colors.ACCENT1};
    padding: 10px;
    font-weight: bold;
}}
QPushButton {{
    background-color: {Colors.CARD_LIGHT};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {Colors.HOVER};
    border-color: {Colors.ACCENT1};
}}
QPushButton:pressed {{
    background-color: {Colors.ACCENT1};
}}
QLabel {{
    color: {Colors.TEXT};
}}
QGroupBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
    color: {Colors.TEXT_DIM};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: {Colors.ACCENT1};
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {Colors.CARD};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 8px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {Colors.ACCENT1};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {Colors.CARD};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    selection-background-color: {Colors.ACCENT1};
}}
QScrollBar:vertical {{
    background-color: {Colors.BG};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background-color: {Colors.BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Colors.ACCENT1};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QCheckBox {{
    color: {Colors.TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {Colors.BORDER};
    background-color: {Colors.CARD};
}}
QCheckBox::indicator:checked {{
    background-color: {Colors.ACCENT1};
    border-color: {Colors.ACCENT1};
}}
"""


# ============================================================================
# 工具函数
# ============================================================================
def format_bytes(bytes_val: float) -> str:
    """格式化字节数"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """格式化速度"""
    return f"{format_bytes(bytes_per_sec)}/s"


# ============================================================================
# 网络监控线程
# ============================================================================
class NetworkMonitorThread(QThread):
    """后台网络监控线程"""
    speed_update = pyqtSignal(float, float)  # download, upload
    connections_update = pyqtSignal(list)
    bandwidth_update = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._last_recv = 0
        self._last_sent = 0
        self._last_time = 0
        self._interval = 1.0  # seconds

    def run(self):
        try:
            counters = psutil.net_io_counters()
            self._last_recv = counters.bytes_recv
            self._last_sent = counters.bytes_sent
            self._last_time = time.time()
        except Exception as e:
            self.error.emit(f"初始化失败: {e}")
            return

        while self._running:
            try:
                time.sleep(self._interval)
                if not self._running:
                    break

                # 速度计算
                counters = psutil.net_io_counters()
                now = time.time()
                elapsed = now - self._last_time

                if elapsed > 0:
                    download_speed = (counters.bytes_recv - self._last_recv) / elapsed
                    upload_speed = (counters.bytes_sent - self._last_sent) / elapsed
                    self.speed_update.emit(download_speed, upload_speed)

                self._last_recv = counters.bytes_recv
                self._last_sent = counters.bytes_sent
                self._last_time = now

                # 连接列表
                try:
                    connections = psutil.net_connections(kind='inet')
                    conn_list = []
                    for conn in connections[:100]:  # 限制数量
                        try:
                            proc_name = ""
                            if conn.pid:
                                try:
                                    proc = psutil.Process(conn.pid)
                                    proc_name = proc.name()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    proc_name = "未知"
                            
                            local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                            remote = ""
                            if conn.raddr:
                                remote = f"{conn.raddr.ip}:{conn.raddr.port}"
                            
                            status = conn.status if conn.status else ""
                            conn_type = "TCP" if conn.type == 1 else "UDP"
                            
                            conn_list.append({
                                'pid': conn.pid or 0,
                                'process': proc_name,
                                'type': conn_type,
                                'local': local,
                                'remote': remote,
                                'status': status
                            })
                        except Exception:
                            continue
                    self.connections_update.emit(conn_list)
                except (psutil.AccessDenied, PermissionError):
                    pass

                # 带宽使用（按进程）
                try:
                    proc_bandwidth = defaultdict(lambda: {'bytes_sent': 0, 'bytes_recv': 0})
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            p = proc
                            io = p.io_counters()
                            name = p.info['name'] or "未知"
                            proc_bandwidth[name]['bytes_sent'] += io.write_bytes
                            proc_bandwidth[name]['bytes_recv'] += io.read_bytes
                        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                            continue
                    
                    # 取前20个
                    sorted_procs = sorted(
                        proc_bandwidth.items(),
                        key=lambda x: x[1]['bytes_sent'] + x[1]['bytes_recv'],
                        reverse=True
                    )[:20]
                    self.bandwidth_update.emit(dict(sorted_procs))
                except Exception:
                    pass

            except Exception as e:
                if self._running:
                    self.error.emit(str(e))

    def stop(self):
        self._running = False
        self.wait(3000)


# ============================================================================
# 速度仪表盘组件
# ============================================================================
class SpeedGauge(QWidget):
    """速度仪表盘"""
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.value = 0.0
        self.max_value = 1024 * 1024  # 1MB/s default max
        self.setMinimumSize(200, 200)

    def set_value(self, value: float):
        self.value = value
        if value > self.max_value * 0.8:
            self.max_value = value * 1.5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 20

        # 背景圆弧
        pen = QPen(QColor(Colors.BORDER), 12, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, -270 * 16)

        # 值圆弧
        ratio = min(self.value / self.max_value, 1.0) if self.max_value > 0 else 0
        gradient = QLinearGradient(cx - r, cy, cx + r, cy)
        gradient.setColorAt(0, QColor(Colors.ACCENT1))
        gradient.setColorAt(1, QColor(Colors.ACCENT2))
        pen.setBrush(QBrush(gradient))
        pen.setWidth(14)
        painter.setPen(pen)
        span = int(-270 * 16 * ratio)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, span)

        # 中心文字
        painter.setPen(QColor(Colors.TEXT))
        font = QFont("Microsoft YaHei", 11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(0, cy - 30, w, 25), Qt.AlignmentFlag.AlignCenter, self.label)

        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(QRect(0, cy, w, 30), Qt.AlignmentFlag.AlignCenter, format_speed(self.value))

        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(Colors.TEXT_DIM))
        painter.drawText(QRect(0, cy + 30, w, 20), Qt.AlignmentFlag.AlignCenter, f"峰值: {format_speed(self.max_value)}")

        painter.end()


# ============================================================================
# 速度历史图表
# ============================================================================
class SpeedHistoryChart(QWidget):
    """速度历史图表"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_history = deque(maxlen=120)
        self.upload_history = deque(maxlen=120)
        self.setMinimumHeight(200)

    def add_data(self, download: float, upload: float):
        self.download_history.append(download)
        self.upload_history.append(upload)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 50
        chart_w = w - margin * 2
        chart_h = h - margin * 2

        if chart_w <= 0 or chart_h <= 0:
            painter.end()
            return

        # 背景
        painter.fillRect(margin, margin, chart_w, chart_h, QColor(Colors.CARD))

        # 网格线
        painter.setPen(QPen(QColor(Colors.BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = margin + int(chart_h * i / 4)
            painter.drawLine(margin, y, w - margin, y)

        # 数据
        all_data = list(self.download_history) + list(self.upload_history)
        if not all_data:
            painter.setPen(QColor(Colors.TEXT_DIM))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "等待数据...")
            painter.end()
            return

        max_val = max(all_data) if all_data else 1
        if max_val == 0:
            max_val = 1

        # 绘制下载曲线
        self._draw_curve(painter, list(self.download_history), max_val,
                        margin, chart_w, chart_h, QColor(Colors.ACCENT1), "下载")

        # 绘制上传曲线
        self._draw_curve(painter, list(self.upload_history), max_val,
                        margin, chart_w, chart_h, QColor(Colors.ACCENT2), "上传")

        # Y轴标签
        painter.setPen(QColor(Colors.TEXT_DIM))
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        for i in range(5):
            y = margin + int(chart_h * i / 4)
            val = max_val * (4 - i) / 4
            painter.drawText(5, y + 5, format_speed(val))

        painter.end()

    def _draw_curve(self, painter, data, max_val, margin, chart_w, chart_h, color, label):
        if len(data) < 2:
            return

        points = []
        for i, val in enumerate(data):
            x = margin + int(chart_w * i / (len(data) - 1))
            y = margin + chart_h - int(chart_h * val / max_val)
            points.append(QPoint(x, y))

        # 填充区域
        polygon = QPolygon(points + [QPoint(margin + chart_w, margin + chart_h), QPoint(margin, margin + chart_h)])
        fill_color = QColor(color)
        fill_color.setAlpha(30)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)

        # 曲线
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # 标签
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(points[-1] + QPoint(5, -5), label)


# ============================================================================
# 速度卡片
# ============================================================================
class SpeedCard(QFrame):
    """速度显示卡片"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            SpeedCard {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 12px; border: none;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel("0 B/s")
        self.value_label.setStyleSheet(f"color: {Colors.TEXT}; font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(self.value_label)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px; border: none;")
        layout.addWidget(self.detail_label)

    def set_value(self, value: float, detail: str = ""):
        self.value_label.setText(format_speed(value))
        if detail:
            self.detail_label.setText(detail)


# ============================================================================
# 统计卡片
# ============================================================================
class StatCard(QFrame):
    """统计卡片"""
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 15px;
            }}
            StatCard:hover {{
                border-color: {Colors.ACCENT1};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        header = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 20px; border: none;")
            header.addWidget(icon_label)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 12px; border: none;")
        header.addWidget(self.title_label)
        header.addStretch()
        layout.addLayout(header)

        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"color: {Colors.TEXT}; font-size: 20px; font-weight: bold; border: none;")
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


# ============================================================================
# 告警设置对话框
# ============================================================================
class AlertSettingsDialog(QDialog):
    """告警设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("告警设置")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 速度告警
        speed_group = QGroupBox("速度告警")
        speed_layout = QFormLayout(speed_group)
        
        self.download_alert = QCheckBox("启用下载速度告警")
        self.download_threshold = QDoubleSpinBox()
        self.download_threshold.setRange(0, 10000)
        self.download_threshold.setSuffix(" MB/s")
        self.download_threshold.setValue(10)
        
        self.upload_alert = QCheckBox("启用上传速度告警")
        self.upload_threshold = QDoubleSpinBox()
        self.upload_threshold.setRange(0, 10000)
        self.upload_threshold.setSuffix(" MB/s")
        self.upload_threshold.setValue(5)
        
        speed_layout.addRow(self.download_alert)
        speed_layout.addRow("下载阈值:", self.download_threshold)
        speed_layout.addRow(self.upload_alert)
        speed_layout.addRow("上传阈值:", self.upload_threshold)
        layout.addWidget(speed_group)

        # 流量告警
        traffic_group = QGroupBox("流量告警")
        traffic_layout = QFormLayout(traffic_group)
        
        self.traffic_alert = QCheckBox("启用流量告警")
        self.traffic_threshold = QDoubleSpinBox()
        self.traffic_threshold.setRange(0, 10000)
        self.traffic_threshold.setSuffix(" GB")
        self.traffic_threshold.setValue(100)
        
        traffic_layout.addRow(self.traffic_alert)
        traffic_layout.addRow("每日流量阈值:", self.traffic_threshold)
        layout.addWidget(traffic_group)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_settings(self):
        return {
            'download_alert': self.download_alert.isChecked(),
            'download_threshold': self.download_threshold.value() * 1024 * 1024,
            'upload_alert': self.upload_alert.isChecked(),
            'upload_threshold': self.upload_threshold.value() * 1024 * 1024,
            'traffic_alert': self.traffic_alert.isChecked(),
            'traffic_threshold': self.traffic_threshold.value() * 1024 * 1024 * 1024,
        }


# ============================================================================
# 主窗口
# ============================================================================
class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetworkMonitor - 网络监控工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 数据存储
        self.total_recv = 0
        self.total_sent = 0
        self.download_speed = 0
        self.upload_speed = 0
        self.speed_history = deque(maxlen=3600)  # 1小时历史
        self.alert_settings = {}
        self.alert_triggered = {}

        # 初始化UI
        self._init_ui()
        self._init_tray()
        self._init_monitor()

        # 定时刷新UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(1000)

    def _init_ui(self):
        """初始化界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("⚡ NetworkMonitor")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.ACCENT1}, stop:1 {Colors.ACCENT2});
            -webkit-background-clip: text;
            color: {Colors.ACCENT1};
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 按钮
        alert_btn = QPushButton("🔔 告警设置")
        alert_btn.clicked.connect(self._show_alert_settings)
        title_layout.addWidget(alert_btn)

        export_btn = QPushButton("📥 导出数据")
        export_btn.clicked.connect(self._export_data)
        title_layout.addWidget(export_btn)

        minimize_btn = QPushButton("🔽 最小化")
        minimize_btn.clicked.connect(self._minimize_to_tray)
        title_layout.addWidget(minimize_btn)

        main_layout.addLayout(title_layout)

        # 速度仪表盘区域
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(15)

        self.download_card = SpeedCard("📥 下载速度")
        speed_layout.addWidget(self.download_card)

        self.upload_card = SpeedCard("📤 上传速度")
        speed_layout.addWidget(self.upload_card)

        self.download_gauge = SpeedGauge("下载", Colors.ACCENT1)
        self.upload_gauge = SpeedGauge("上传", Colors.ACCENT2)
        
        gauge_layout = QHBoxLayout()
        gauge_layout.addWidget(self.download_gauge)
        gauge_layout.addWidget(self.upload_gauge)
        speed_layout.addLayout(gauge_layout, 1)

        main_layout.addLayout(speed_layout)

        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.total_recv_card = StatCard("总接收", "📥")
        stats_layout.addWidget(self.total_recv_card)

        self.total_sent_card = StatCard("总发送", "📤")
        stats_layout.addWidget(self.total_sent_card)

        self.connections_card = StatCard("活跃连接", "🔗")
        stats_layout.addWidget(self.connections_card)

        self.session_card = StatCard("运行时间", "⏱️")
        stats_layout.addWidget(self.session_card)

        main_layout.addLayout(stats_layout)

        # 标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        # 历史图表标签页
        self.history_chart = SpeedHistoryChart()
        self.tabs.addTab(self.history_chart, "📊 速度历史")

        # 连接列表标签页
        self.conn_table = QTableWidget()
        self.conn_table.setColumnCount(6)
        self.conn_table.setHorizontalHeaderLabels(["PID", "进程", "协议", "本地地址", "远程地址", "状态"])
        self.conn_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.conn_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.conn_table.setAlternatingRowColors(True)
        self.conn_table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {Colors.CARD_LIGHT};
            }}
        """)
        self.tabs.addTab(self.conn_table, "🔗 连接列表")

        # 带宽使用标签页
        self.bandwidth_table = QTableWidget()
        self.bandwidth_table.setColumnCount(4)
        self.bandwidth_table.setHorizontalHeaderLabels(["进程", "接收", "发送", "总计"])
        self.bandwidth_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bandwidth_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bandwidth_table.setAlternatingRowColors(True)
        self.bandwidth_table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {Colors.CARD_LIGHT};
            }}
        """)
        self.tabs.addTab(self.bandwidth_table, "📈 带宽使用")

        # 状态栏
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.CARD};
                color: {Colors.TEXT_DIM};
                border-top: 1px solid {Colors.BORDER};
                padding: 5px;
            }}
        """)
        self.statusBar().showMessage("就绪")

        # 启动时间
        self.start_time = datetime.now()

    def _init_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(Colors.ACCENT1))
        painter = QPainter(pixmap)
        painter.setPen(QColor(Colors.TEXT))
        painter.setFont(QFont("Arial", 16))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "N")
        painter.end()
        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray_icon.setToolTip("NetworkMonitor - 网络监控工具")

        # 托盘菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.CARD};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
            }}
            QMenu::item:selected {{
                background-color: {Colors.ACCENT1};
            }}
        """)
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _init_monitor(self):
        """初始化监控线程"""
        self.monitor_thread = NetworkMonitorThread()
        self.monitor_thread.speed_update.connect(self._on_speed_update)
        self.monitor_thread.connections_update.connect(self._on_connections_update)
        self.monitor_thread.bandwidth_update.connect(self._on_bandwidth_update)
        self.monitor_thread.error.connect(self._on_error)
        self.monitor_thread.start()

    def _on_speed_update(self, download: float, upload: float):
        """速度更新回调"""
        self.download_speed = download
        self.upload_speed = upload
        self.total_recv += download
        self.total_sent += upload

        # 记录历史
        self.speed_history.append({
            'time': datetime.now(),
            'download': download,
            'upload': upload
        })

        # 检查告警
        self._check_alerts(download, upload)

    def _on_connections_update(self, connections: list):
        """连接列表更新"""
        self.conn_table.setRowCount(len(connections))
        for i, conn in enumerate(connections):
            self.conn_table.setItem(i, 0, QTableWidgetItem(str(conn['pid'])))
            self.conn_table.setItem(i, 1, QTableWidgetItem(conn['process']))
            self.conn_table.setItem(i, 2, QTableWidgetItem(conn['type']))
            self.conn_table.setItem(i, 3, QTableWidgetItem(conn['local']))
            self.conn_table.setItem(i, 4, QTableWidgetItem(conn['remote']))
            self.conn_table.setItem(i, 5, QTableWidgetItem(conn['status']))
        
        self.connections_card.set_value(str(len(connections)))

    def _on_bandwidth_update(self, bandwidth: dict):
        """带宽使用更新"""
        self.bandwidth_table.setRowCount(len(bandwidth))
        for i, (name, data) in enumerate(bandwidth.items()):
            total = data['bytes_sent'] + data['bytes_recv']
            self.bandwidth_table.setItem(i, 0, QTableWidgetItem(name))
            self.bandwidth_table.setItem(i, 1, QTableWidgetItem(format_bytes(data['bytes_recv'])))
            self.bandwidth_table.setItem(i, 2, QTableWidgetItem(format_bytes(data['bytes_sent'])))
            self.bandwidth_table.setItem(i, 3, QTableWidgetItem(format_bytes(total)))

    def _on_error(self, msg: str):
        """错误处理"""
        self.statusBar().showMessage(f"错误: {msg}", 5000)

    def _update_ui(self):
        """更新UI"""
        # 速度卡片
        self.download_card.set_value(self.download_speed)
        self.upload_card.set_value(self.upload_speed)

        # 仪表盘
        self.download_gauge.set_value(self.download_speed)
        self.upload_gauge.set_value(self.upload_speed)

        # 统计卡片
        self.total_recv_card.set_value(format_bytes(self.total_recv))
        self.total_sent_card.set_value(format_bytes(self.total_sent))

        # 运行时间
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.session_card.set_value(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # 历史图表
        if self.speed_history:
            recent = list(self.speed_history)[-120:]
            for item in recent:
                self.history_chart.add_data(item['download'], item['upload'])

        # 状态栏
        self.statusBar().showMessage(
            f"下载: {format_speed(self.download_speed)} | "
            f"上传: {format_speed(self.upload_speed)} | "
            f"总接收: {format_bytes(self.total_recv)} | "
            f"总发送: {format_bytes(self.total_sent)}"
        )

    def _check_alerts(self, download: float, upload: float):
        """检查告警"""
        if not self.alert_settings:
            return

        alerts = []
        
        if self.alert_settings.get('download_alert', False):
            threshold = self.alert_settings.get('download_threshold', 0)
            if download > threshold:
                alerts.append(f"下载速度超过阈值: {format_speed(download)} > {format_speed(threshold)}")

        if self.alert_settings.get('upload_alert', False):
            threshold = self.alert_settings.get('upload_threshold', 0)
            if upload > threshold:
                alerts.append(f"上传速度超过阈值: {format_speed(upload)} > {format_speed(threshold)}")

        if self.alert_settings.get('traffic_alert', False):
            threshold = self.alert_settings.get('traffic_threshold', 0)
            total = self.total_recv + self.total_sent
            if total > threshold:
                alerts.append(f"流量超过阈值: {format_bytes(total)} > {format_bytes(threshold)}")

        if alerts:
            alert_key = '|'.join(alerts)
            now = time.time()
            if alert_key not in self.alert_triggered or now - self.alert_triggered[alert_key] > 60:
                self.alert_triggered[alert_key] = now
                self.tray_icon.showMessage(
                    "网络告警",
                    '\n'.join(alerts),
                    QSystemTrayIcon.MessageIcon.Warning,
                    5000
                )

    def _show_alert_settings(self):
        """显示告警设置"""
        dialog = AlertSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.alert_settings = dialog.get_settings()
            self.statusBar().showMessage("告警设置已保存", 3000)

    def _export_data(self):
        """导出数据"""
        filename, ftype = QFileDialog.getSaveFileName(
            self, "导出数据", 
            f"network_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "CSV文件 (*.csv);;文本文件 (*.txt)"
        )
        
        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                if filename.endswith('.csv'):
                    writer = csv.writer(f)
                    writer.writerow(['时间', '下载速度', '上传速度'])
                    for item in self.speed_history:
                        writer.writerow([
                            item['time'].strftime('%Y-%m-%d %H:%M:%S'),
                            f"{item['download']:.2f}",
                            f"{item['upload']:.2f}"
                        ])
                else:
                    f.write("NetworkMonitor 数据导出\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"总接收: {format_bytes(self.total_recv)}\n")
                    f.write(f"总发送: {format_bytes(self.total_sent)}\n\n")
                    f.write("速度历史:\n")
                    f.write("-" * 50 + "\n")
                    for item in self.speed_history:
                        f.write(f"{item['time'].strftime('%H:%M:%S')} | "
                               f"下载: {format_speed(item['download'])} | "
                               f"上传: {format_speed(item['upload'])}\n")

            self.statusBar().showMessage(f"数据已导出到: {filename}", 5000)
            QMessageBox.information(self, "导出成功", f"数据已导出到:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时出错:\n{str(e)}")

    def _minimize_to_tray(self):
        """最小化到托盘"""
        self.hide()
        self.tray_icon.showMessage(
            "NetworkMonitor",
            "程序已最小化到系统托盘",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def _show_from_tray(self):
        """从托盘恢复"""
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason):
        """托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self):
        """退出应用"""
        if self.monitor_thread.isRunning():
            self.monitor_thread.stop()
        QApplication.quit()

    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self._minimize_to_tray()


# ============================================================================
# 主函数
# ============================================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    
    # 设置应用程序信息
    app.setApplicationName("NetworkMonitor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NetworkMonitor")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
