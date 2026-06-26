#!/usr/bin/env python3
"""
SysMonitor - 系统监控仪表板
基于 PyQt6 的专业级系统实时监控工具
"""

import sys
import os
import time
import platform
import socket
from datetime import datetime, timedelta
from collections import deque

import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QSplitter, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    QTimer, Qt, QSize, QThread, pyqtSignal, QObject, QPointF
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter,
    QPen, QPixmap, QIcon, QPaintEvent
)

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


# ─── 全局样式 ──────────────────────────────────────────────
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QTabWidget::pane {
    border: 1px solid #222244;
    background: #0a0a0a;
    border-radius: 6px;
}
QTabBar::tab {
    background: #111122;
    color: #888;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}
QTabBar::tab:hover:!selected {
    background: #1a1a33;
    color: #bbb;
}
QLabel {
    color: #e0e0e0;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background: #1a1a2e;
    text-align: center;
    color: white;
    font-size: 11px;
    height: 8px;
}
QProgressBar::chunk {
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
}
QTableWidget {
    background: #0d0d1a;
    alternate-background-color: #111122;
    gridline-color: #1a1a33;
    border: 1px solid #222244;
    border-radius: 6px;
    color: #e0e0e0;
    selection-background-color: #333366;
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background: #111122;
    color: #888;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #222244;
    border-bottom: 1px solid #222244;
    font-weight: bold;
    font-size: 12px;
}
QScrollBar:vertical {
    background: #0a0a0a;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #333;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea {
    border: none;
}
"""


# ─── 工具函数 ──────────────────────────────────────────────
def bytes_fmt(n, suffix="B"):
    """格式化字节数"""
    for unit in ("", "K", "M", "G", "T"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}{suffix}"
        n /= 1024
    return f"{n:.1f} P{suffix}"


def get_uptime():
    """获取系统运行时间"""
    boot = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    parts.append(f"{mins}分{secs}秒")
    return " ".join(parts)


def get_gpu_info():
    """尝试获取 GPU 信息"""
    info = "未检测到独立GPU"
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            capture_output=True, text=True, timeout=3
        )
        lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and l.strip() != 'Name']
        if lines:
            info = lines[0]
    except Exception:
        pass
    return info


# ─── 卡片组件 ──────────────────────────────────────────────
class Card(QFrame):
    """仪表板卡片"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111122, stop:1 #0e0e1e);
                border: 1px solid #1e1e3a;
                border-radius: 10px;
                padding: 16px;
            }
            QFrame:hover {
                border: 1px solid #333366;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size: 13px; color: #888; font-weight: bold; border: none;")
            layout.addWidget(lbl)
            self.title_label = lbl

        self._body = QVBoxLayout()
        self._body.setSpacing(6)
        layout.addLayout(self._body)

    def addWidget(self, w):
        self._body.addWidget(w)

    def addLayout(self, l):
        self._body.addLayout(l)


class MetricLabel(QLabel):
    """指标数值标签"""
    def __init__(self, text="", big=False):
        super().__init__(text)
        size = "28px" if big else "15px"
        weight = "bold" if big else "normal"
        self.setStyleSheet(f"font-size: {size}; font-weight: {weight}; color: #ffffff; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)


class SubLabel(QLabel):
    """小字标签"""
    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet("font-size: 12px; color: #666; border: none;")


class AccentProgressBar(QProgressBar):
    """渐变进度条"""
    def __init__(self):
        super().__init__()
        self.setMinimum(0)
        self.setMaximum(100)
        self.setTextVisible(False)
        self.setFixedHeight(8)


# ─── 系统数据采集线程 ────────────────────────────────────────
class SystemDataCollector(QThread):
    """后台线程采集系统数据"""
    data_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._running = True
        self._interval = 1.5  # 秒
        self._prev_net = psutil.net_io_counters()
        self._prev_time = time.time()
        self._prev_disk = psutil.disk_io_counters()

    def run(self):
        while self._running:
            data = self._collect()
            self.data_ready.emit(data)
            time.sleep(self._interval)

    def stop(self):
        self._running = False
        self.wait()

    def _collect(self):
        now = time.time()
        dt = now - self._prev_time
        if dt == 0:
            dt = 1

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0, percpu=True)
        cpu_total = psutil.cpu_percent(interval=0)
        cpu_freq = psutil.cpu_freq()
        try:
            cpu_temps = psutil.sensors_temperatures()
        except (AttributeError, Exception):
            cpu_temps = {}

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk
        disk_parts = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                disk_parts.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                pass

        disk_io = psutil.disk_io_counters()
        disk_read_speed = (disk_io.read_bytes - self._prev_disk.read_bytes) / dt if self._prev_disk else 0
        disk_write_speed = (disk_io.write_bytes - self._prev_disk.write_bytes) / dt if self._prev_disk else 0
        self._prev_disk = disk_io

        # Network
        net = psutil.net_io_counters()
        net_sent_speed = (net.bytes_sent - self._prev_net.bytes_sent) / dt
        net_recv_speed = (net.bytes_recv - self._prev_net.bytes_recv) / dt
        self._prev_net = net

        # Top processes
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                info = proc.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda p: p.get('cpu_percent', 0) or 0, reverse=True)
        top_procs = procs[:30]

        self._prev_time = now

        return {
            "cpu_percent": cpu_percent,
            "cpu_total": cpu_total,
            "cpu_freq": cpu_freq,
            "cpu_temps": cpu_temps,
            "mem": mem,
            "swap": swap,
            "disk_parts": disk_parts,
            "disk_read_speed": disk_read_speed,
            "disk_write_speed": disk_write_speed,
            "net_sent_speed": net_sent_speed,
            "net_recv_speed": net_recv_speed,
            "net_total_sent": net.bytes_sent,
            "net_total_recv": net.bytes_recv,
            "processes": top_procs,
            "timestamp": now,
        }


# ─── CPU 仪表板面板 ──────────────────────────────────────────
class CpuPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 总体使用率
        total_card = Card("处理器总览")
        self.cpu_total_bar = AccentProgressBar()
        self.cpu_total_label = MetricLabel("0%", big=True)
        self.cpu_freq_label = SubLabel("--")
        self.cpu_temp_label = SubLabel("--")

        h = QHBoxLayout()
        h.addWidget(self.cpu_total_label)
        h.addStretch()
        h.addWidget(self.cpu_freq_label)
        total_card.addLayout(h)
        total_card.addWidget(self.cpu_total_bar)
        total_card.addWidget(self.cpu_temp_label)
        layout.addWidget(total_card)

        # 各核心
        cores_card = Card("各核心使用率")
        self.cores_grid = QGridLayout()
        self.cores_grid.setSpacing(8)
        cores_card.addLayout(self.cores_grid)
        layout.addWidget(cores_card)

        self._core_widgets = []
        layout.addStretch()

    def update_data(self, data):
        cpu_total = data["cpu_total"]
        cpu_percents = data["cpu_percent"]
        cpu_freq = data["cpu_freq"]
        cpu_temps = data["cpu_temps"]

        self.cpu_total_bar.setValue(int(cpu_total))
        self.cpu_total_label.setText(f"{cpu_total:.1f}%")

        # 颜色
        if cpu_total > 90:
            color = "#ff4444"
        elif cpu_total > 70:
            color = "#ffaa00"
        else:
            color = "#667eea"
        self.cpu_total_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 4px; background: #1a1a2e; height: 8px; }}
            QProgressBar::chunk {{ border-radius: 4px; background: {color}; }}
        """)

        if cpu_freq:
            self.cpu_freq_label.setText(f"频率: {cpu_freq.current:.0f} MHz")

        # 温度
        temp_str = "--"
        if cpu_temps:
            for name, entries in cpu_temps.items():
                if entries:
                    t = entries[0].current
                    temp_str = f"温度: {t:.0f}°C"
                    break
        self.cpu_temp_label.setText(temp_str)

        # 核心
        n = len(cpu_percents)
        if len(self._core_widgets) != n:
            # 重建
            for w in self._core_widgets:
                w.deleteLater()
            self._core_widgets.clear()
            cols = 4
            for i in range(n):
                row, col = divmod(i, cols)
                frame = QFrame()
                frame.setStyleSheet("""
                    QFrame { background: #0d0d1a; border: 1px solid #1e1e3a; border-radius: 6px; padding: 6px; }
                """)
                fl = QVBoxLayout(frame)
                fl.setContentsMargins(8, 6, 8, 6)
                fl.setSpacing(4)
                lbl = QLabel(f"核心 {i}")
                lbl.setStyleSheet("font-size: 11px; color: #666; border:none;")
                val = QLabel("0%")
                val.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; border:none;")
                bar = AccentProgressBar()
                fl.addWidget(lbl)
                fl.addWidget(val)
                fl.addWidget(bar)
                self.cores_grid.addWidget(frame, row, col)
                self._core_widgets.append((val, bar))

        for i, (val, bar) in enumerate(self._core_widgets):
            pct = cpu_percents[i]
            val.setText(f"{pct:.0f}%")
            bar.setValue(int(pct))
            if pct > 90:
                c = "#ff4444"
            elif pct > 70:
                c = "#ffaa00"
            else:
                c = "#667eea"
            bar.setStyleSheet(f"""
                QProgressBar {{ border:none; border-radius:4px; background:#1a1a2e; height:8px; }}
                QProgressBar::chunk {{ border-radius:4px; background:{c}; }}
            """)


# ─── 内存面板 ──────────────────────────────────────────────
class MemoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # RAM
        ram_card = Card("物理内存 (RAM)")
        self.ram_bar = AccentProgressBar()
        self.ram_label = MetricLabel("0 / 0 GB", big=True)
        self.ram_pct = SubLabel("0%")
        ram_card.addWidget(self.ram_label)
        ram_card.addWidget(self.ram_pct)
        ram_card.addWidget(self.ram_bar)
        layout.addWidget(ram_card)

        # Swap
        swap_card = Card("交换分区 (Swap)")
        self.swap_bar = AccentProgressBar()
        self.swap_label = MetricLabel("0 / 0 GB", big=True)
        self.swap_pct = SubLabel("0%")
        swap_card.addWidget(self.swap_label)
        swap_card.addWidget(self.swap_pct)
        swap_card.addWidget(self.swap_bar)
        layout.addWidget(swap_card)

        # 详细
        detail_card = Card("内存详情")
        self.detail_labels = {}
        for key in ["总内存", "可用内存", "已用内存", "缓存", "总Swap", "已用Swap"]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet("color: #888; font-size: 12px; border:none;")
            v = QLabel("--")
            v.setStyleSheet("color: #e0e0e0; font-size: 12px; border:none;")
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            detail_card.addLayout(row)
            self.detail_labels[key] = v

        layout.addWidget(detail_card)
        layout.addStretch()

    def update_data(self, data):
        mem = data["mem"]
        swap = data["swap"]

        total_gb = mem.total / (1024**3)
        used_gb = mem.used / (1024**3)
        self.ram_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.ram_pct.setText(f"使用率: {mem.percent}%")
        self.ram_bar.setValue(int(mem.percent))

        stotal = swap.total / (1024**3)
        sused = swap.used / (1024**3)
        self.swap_label.setText(f"{sused:.1f} / {stotal:.1f} GB")
        self.swap_pct.setText(f"使用率: {swap.percent}%")
        self.swap_bar.setValue(int(swap.percent))

        self.detail_labels["总内存"].setText(bytes_fmt(mem.total))
        self.detail_labels["可用内存"].setText(bytes_fmt(mem.available))
        self.detail_labels["已用内存"].setText(bytes_fmt(mem.used))
        self.detail_labels["缓存"].setText(bytes_fmt(getattr(mem, 'cached', 0)))
        self.detail_labels["总Swap"].setText(bytes_fmt(swap.total))
        self.detail_labels["已用Swap"].setText(bytes_fmt(swap.used))


# ─── 磁盘面板 ──────────────────────────────────────────────
class DiskPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        io_card = Card("磁盘 I/O 速度")
        self.read_speed = MetricLabel("读取: 0 B/s", big=True)
        self.write_speed = MetricLabel("写入: 0 B/s", big=True)
        io_card.addWidget(self.read_speed)
        io_card.addWidget(self.write_speed)
        layout.addWidget(io_card)

        parts_card = Card("磁盘分区")
        self.parts_layout = QVBoxLayout()
        parts_card.addLayout(self.parts_layout)
        layout.addWidget(parts_card)
        layout.addStretch()

        self._part_widgets = []

    def update_data(self, data):
        self.read_speed.setText(f"读取: {bytes_fmt(data['disk_read_speed'])}/s")
        self.write_speed.setText(f"写入: {bytes_fmt(data['disk_write_speed'])}/s")

        parts = data["disk_parts"]
        # 重建分区列表
        for w in self._part_widgets:
            w.deleteLater()
        self._part_widgets.clear()

        for p in parts:
            frame = QFrame()
            frame.setStyleSheet("QFrame { background: #0d0d1a; border: 1px solid #1e1e3a; border-radius: 6px; padding: 8px; }")
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(10, 8, 10, 8)
            fl.setSpacing(4)

            title = QLabel(f"{p['device']}  ({p['mountpoint']})  [{p['fstype']}]")
            title.setStyleSheet("font-size: 13px; font-weight: bold; color: #aaa; border:none;")
            fl.addWidget(title)

            bar = AccentProgressBar()
            bar.setValue(int(p['percent']))
            if p['percent'] > 90:
                c = "#ff4444"
            elif p['percent'] > 75:
                c = "#ffaa00"
            else:
                c = "#667eea"
            bar.setStyleSheet(f"""
                QProgressBar {{ border:none; border-radius:4px; background:#1a1a2e; height:8px; }}
                QProgressBar::chunk {{ border-radius:4px; background:{c}; }}
            """)
            fl.addWidget(bar)

            info = QLabel(f"已用 {bytes_fmt(p['used'])} / 总计 {bytes_fmt(p['total'])}  ({p['percent']}%)  可用: {bytes_fmt(p['free'])}")
            info.setStyleSheet("font-size: 11px; color: #888; border:none;")
            fl.addWidget(info)

            self.parts_layout.addWidget(frame)
            self._part_widgets.append(frame)


# ─── 网络面板 ──────────────────────────────────────────────
class NetworkPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        speed_card = Card("网络速度")
        self.upload_label = MetricLabel("上传: 0 B/s", big=True)
        self.download_label = MetricLabel("下载: 0 B/s", big=True)
        speed_card.addWidget(self.upload_label)
        speed_card.addWidget(self.download_label)
        layout.addWidget(speed_card)

        total_card = Card("累计流量")
        self.total_sent_label = MetricLabel("发送: 0 B")
        self.total_recv_label = MetricLabel("接收: 0 B")
        total_card.addWidget(self.total_sent_label)
        total_card.addWidget(self.total_recv_label)
        layout.addWidget(total_card)

        layout.addStretch()

    def update_data(self, data):
        self.upload_label.setText(f"上传: {bytes_fmt(data['net_sent_speed'])}/s")
        self.download_label.setText(f"下载: {bytes_fmt(data['net_recv_speed'])}/s")
        self.total_sent_label.setText(f"发送: {bytes_fmt(data['net_total_sent'])}")
        self.total_recv_label.setText(f"接收: {bytes_fmt(data['net_total_recv'])}")


# ─── 进程面板 ──────────────────────────────────────────────
class ProcessPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("进程列表 (按 CPU 使用率排序)")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #aaa;")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PID", "名称", "状态", "CPU%", "内存%", "内存用量"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def update_data(self, data):
        procs = data["processes"]
        self.table.setRowCount(len(procs))
        for i, p in enumerate(procs):
            pid = p.get('pid', 0)
            name = p.get('name', '?')
            status = p.get('status', '?')
            cpu = p.get('cpu_percent', 0) or 0
            mem_pct = p.get('memory_percent', 0) or 0
            mem_info = p.get('memory_info')
            mem_rss = mem_info.rss if mem_info else 0

            self.table.setItem(i, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(status))

            cpu_item = QTableWidgetItem(f"{cpu:.1f}")
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cpu > 50:
                cpu_item.setForeground(QColor("#ff6666"))
            self.table.setItem(i, 3, cpu_item)

            mem_item = QTableWidgetItem(f"{mem_pct:.1f}")
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if mem_pct > 10:
                mem_item.setForeground(QColor("#ffaa66"))
            self.table.setItem(i, 4, mem_item)

            rss_item = QTableWidgetItem(bytes_fmt(mem_rss))
            rss_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 5, rss_item)


# ─── 图表面板 ──────────────────────────────────────────────
class GraphPanel(QWidget):
    def __init__(self, max_points=120):
        super().__init__()
        self.max_points = max_points
        self.cpu_history = deque(maxlen=max_points)
        self.mem_history = deque(maxlen=max_points)
        self.net_sent_history = deque(maxlen=max_points)
        self.net_recv_history = deque(maxlen=max_points)
        self.time_labels = deque(maxlen=max_points)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if HAS_PYQTGRAPH:
            pg.setConfigOptions(antialias=True)
            pg.setConfigOption('background', '#0d0d1a')
            pg.setConfigOption('foreground', '#888')

            # CPU 图表
            cpu_card = Card("CPU 使用率历史")
            self.cpu_plot = pg.PlotWidget()
            self.cpu_plot.setMinimumHeight(180)
            self.cpu_plot.showGrid(x=True, y=True, alpha=0.15)
            self.cpu_plot.setYRange(0, 100)
            self.cpu_plot.setLabel('left', '使用率 (%)')
            self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('#667eea', width=2))
            cpu_card.addWidget(self.cpu_plot)
            layout.addWidget(cpu_card)

            # 内存图表
            mem_card = Card("内存使用率历史")
            self.mem_plot = pg.PlotWidget()
            self.mem_plot.setMinimumHeight(180)
            self.mem_plot.showGrid(x=True, y=True, alpha=0.15)
            self.mem_plot.setYRange(0, 100)
            self.mem_plot.setLabel('left', '使用率 (%)')
            self.mem_curve = self.mem_plot.plot(pen=pg.mkPen('#764ba2', width=2))
            mem_card.addWidget(self.mem_plot)
            layout.addWidget(mem_card)

            # 网络图表
            net_card = Card("网络流量历史")
            self.net_plot = pg.PlotWidget()
            self.net_plot.setMinimumHeight(180)
            self.net_plot.showGrid(x=True, y=True, alpha=0.15)
            self.net_plot.setLabel('left', '速度 (B/s)')
            self.net_sent_curve = self.net_plot.plot(pen=pg.mkPen('#44cc88', width=2), name='上传')
            self.net_recv_curve = self.net_plot.plot(pen=pg.mkPen('#4488ff', width=2), name='下载')
            legend = self.net_plot.addLegend()
            net_card.addWidget(self.net_plot)
            layout.addWidget(net_card)
        else:
            placeholder = QLabel("安装 pyqtgraph 以启用实时图表:\npip install pyqtgraph")
            placeholder.setStyleSheet("font-size: 16px; color: #666; padding: 40px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)

        layout.addStretch()

    def update_data(self, data):
        now = data["timestamp"]
        cpu = data["cpu_total"]
        mem = data["mem"].percent
        net_s = data["net_sent_speed"]
        net_r = data["net_recv_speed"]

        self.cpu_history.append(cpu)
        self.mem_history.append(mem)
        self.net_sent_history.append(max(net_s, 0))
        self.net_recv_history.append(max(net_r, 0))
        self.time_labels.append(now)

        if HAS_PYQTGRAPH:
            x = list(range(len(self.cpu_history)))
            self.cpu_curve.setData(x, list(self.cpu_history))
            self.mem_curve.setData(x, list(self.mem_history))
            self.net_sent_curve.setData(x, list(self.net_sent_history))
            self.net_recv_curve.setData(x, list(self.net_recv_history))


# ─── 系统信息面板 ──────────────────────────────────────────
class SystemInfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_card = Card("系统信息")

        self.info_labels = {}
        items = [
            ("操作系统", f"{platform.system()} {platform.release()} {platform.version()}"),
            ("主机名", socket.gethostname()),
            ("处理器", platform.processor() or "未知"),
            ("Python 版本", platform.python_version()),
            ("物理核心数", str(psutil.cpu_count(logical=False))),
            ("逻辑核心数", str(psutil.cpu_count(logical=True))),
            ("总内存", bytes_fmt(psutil.virtual_memory().total)),
            ("GPU", get_gpu_info()),
            ("运行时间", get_uptime()),
        ]

        for key, val in items:
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setFixedWidth(100)
            k.setStyleSheet("font-size: 13px; color: #667eea; font-weight: bold; border:none;")
            v = QLabel(val)
            v.setStyleSheet("font-size: 13px; color: #e0e0e0; border:none;")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            info_card.addLayout(row)
            self.info_labels[key] = v

        layout.addWidget(info_card)

        # 网络接口
        net_card = Card("网络接口")
        try:
            addrs = psutil.net_if_addrs()
            for iface, addr_list in addrs.items():
                row = QHBoxLayout()
                k = QLabel(f"{iface}:")
                k.setFixedWidth(120)
                k.setStyleSheet("font-size: 12px; color: #667eea; border:none;")
                ips = [a.address for a in addr_list if a.family == socket.AF_INET]
                v = QLabel(", ".join(ips) if ips else "(无 IPv4)")
                v.setStyleSheet("font-size: 12px; color: #aaa; border:none;")
                row.addWidget(k)
                row.addWidget(v)
                row.addStretch()
                net_card.addLayout(row)
        except Exception:
            pass

        layout.addWidget(net_card)
        layout.addStretch()

    def update_data(self, data):
        self.info_labels["运行时间"].setText(get_uptime())


# ─── 告警面板 ──────────────────────────────────────────────
class AlertPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.alert_card = Card("⚠️ 告警状态")
        self.cpu_alert_label = QLabel("CPU 使用率正常")
        self.cpu_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")
        self.mem_alert_label = QLabel("内存使用率正常")
        self.mem_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")
        self.disk_alert_label = QLabel("磁盘使用率正常")
        self.disk_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")

        self.alert_card.addWidget(self.cpu_alert_label)
        self.alert_card.addWidget(self.mem_alert_label)
        self.alert_card.addWidget(self.disk_alert_label)
        layout.addWidget(self.alert_card)

        # 阈值设置
        threshold_card = Card("告警阈值")
        self.cpu_threshold = 80
        self.mem_threshold = 85
        self.disk_threshold = 90

        for name, val in [("CPU", self.cpu_threshold), ("内存", self.mem_threshold), ("磁盘", self.disk_threshold)]:
            row = QHBoxLayout()
            lbl = QLabel(f"{name} 告警阈值: {val}%")
            lbl.setStyleSheet("font-size: 12px; color: #888; border:none;")
            row.addWidget(lbl)
            row.addStretch()
            threshold_card.addLayout(row)

        layout.addWidget(threshold_card)

        # 最近告警
        history_card = Card("告警历史")
        self.alert_history = QLabel("暂无告警记录")
        self.alert_history.setStyleSheet("font-size: 12px; color: #888; border:none;")
        self.alert_history.setWordWrap(True)
        history_card.addWidget(self.alert_history)
        layout.addWidget(history_card)

        layout.addStretch()
        self._alerts = []

    def update_data(self, data):
        cpu = data["cpu_total"]
        mem = data["mem"].percent
        now = datetime.now().strftime("%H:%M:%S")

        # CPU
        if cpu > self.cpu_threshold:
            self.cpu_alert_label.setText(f"⚠️ CPU 使用率过高: {cpu:.1f}% (阈值 {self.cpu_threshold}%)")
            self.cpu_alert_label.setStyleSheet("font-size: 14px; color: #ff4444; font-weight: bold; border:none;")
            self._add_alert(f"[{now}] CPU 告警: {cpu:.1f}%")
        else:
            self.cpu_alert_label.setText(f"✅ CPU 使用率正常: {cpu:.1f}%")
            self.cpu_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")

        # Memory
        if mem > self.mem_threshold:
            self.mem_alert_label.setText(f"⚠️ 内存使用率过高: {mem:.1f}% (阈值 {self.mem_threshold}%)")
            self.mem_alert_label.setStyleSheet("font-size: 14px; color: #ff4444; font-weight: bold; border:none;")
            self._add_alert(f"[{now}] 内存告警: {mem:.1f}%")
        else:
            self.mem_alert_label.setText(f"✅ 内存使用率正常: {mem:.1f}%")
            self.mem_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")

        # Disk
        max_disk = max((p["percent"] for p in data["disk_parts"]), default=0)
        if max_disk > self.disk_threshold:
            self.disk_alert_label.setText(f"⚠️ 磁盘使用率过高: {max_disk:.1f}% (阈值 {self.disk_threshold}%)")
            self.disk_alert_label.setStyleSheet("font-size: 14px; color: #ff4444; font-weight: bold; border:none;")
        else:
            self.disk_alert_label.setText(f"✅ 磁盘使用率正常: {max_disk:.1f}%")
            self.disk_alert_label.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")

    def _add_alert(self, msg):
        self._alerts.append(msg)
        if len(self._alerts) > 20:
            self._alerts = self._alerts[-20:]
        self.alert_history.setText("\n".join(reversed(self._alerts)))


# ─── 仪表板主视图 ──────────────────────────────────────────
class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # CPU 卡片
        cpu_card = Card("处理器")
        self.cpu_total_bar = AccentProgressBar()
        self.cpu_val = MetricLabel("0%", big=True)
        self.cpu_sub = SubLabel("-- 核心")
        cpu_card.addWidget(self.cpu_val)
        cpu_card.addWidget(self.cpu_sub)
        cpu_card.addWidget(self.cpu_total_bar)
        layout.addWidget(cpu_card, 0, 0)

        # 内存卡片
        mem_card = Card("内存")
        self.mem_bar = AccentProgressBar()
        self.mem_val = MetricLabel("0%", big=True)
        self.mem_sub = SubLabel("--")
        mem_card.addWidget(self.mem_val)
        mem_card.addWidget(self.mem_sub)
        mem_card.addWidget(self.mem_bar)
        layout.addWidget(mem_card, 0, 1)

        # 磁盘卡片
        disk_card = Card("磁盘 I/O")
        self.disk_read = MetricLabel("读: 0 B/s")
        self.disk_write = MetricLabel("写: 0 B/s")
        disk_card.addWidget(self.disk_read)
        disk_card.addWidget(self.disk_write)
        layout.addWidget(disk_card, 0, 2)

        # 网络卡片
        net_card = Card("网络")
        self.net_up = MetricLabel("↑ 0 B/s")
        self.net_down = MetricLabel("↓ 0 B/s")
        net_card.addWidget(self.net_up)
        net_card.addWidget(self.net_down)
        layout.addWidget(net_card, 1, 0)

        # 告警卡片
        alert_card = Card("⚠️ 告警")
        self.alert_status = QLabel("✅ 系统正常")
        self.alert_status.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")
        alert_card.addWidget(self.alert_status)
        layout.addWidget(alert_card, 1, 1)

        # 进程卡片
        proc_card = Card("Top 进程")
        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(3)
        self.proc_table.setHorizontalHeaderLabels(["名称", "CPU%", "内存%"])
        self.proc_table.horizontalHeader().setStretchLastSection(True)
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.proc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setMaximumHeight(200)
        self.proc_table.setAlternatingRowColors(True)
        proc_card.addWidget(self.proc_table)
        layout.addWidget(proc_card, 1, 2)

        # 图表 (跨整行)
        if HAS_PYQTGRAPH:
            pg.setConfigOptions(antialias=True)
            pg.setConfigOption('background', '#0d0d1a')
            pg.setConfigOption('foreground', '#888')

            graph_card = Card("实时监控图表")
            splitter = QSplitter(Qt.Orientation.Horizontal)

            self.cpu_plot = pg.PlotWidget()
            self.cpu_plot.setMinimumHeight(200)
            self.cpu_plot.showGrid(x=True, y=True, alpha=0.15)
            self.cpu_plot.setYRange(0, 100)
            self.cpu_plot.setLabel('left', 'CPU (%)')
            self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('#667eea', width=2))

            self.mem_plot = pg.PlotWidget()
            self.mem_plot.setMinimumHeight(200)
            self.mem_plot.showGrid(x=True, y=True, alpha=0.15)
            self.mem_plot.setYRange(0, 100)
            self.mem_plot.setLabel('left', '内存 (%)')
            self.mem_curve = self.mem_plot.plot(pen=pg.mkPen('#764ba2', width=2))

            self.net_plot = pg.PlotWidget()
            self.net_plot.setMinimumHeight(200)
            self.net_plot.showGrid(x=True, y=True, alpha=0.15)
            self.net_plot.setLabel('left', '网络 (B/s)')
            self.net_up_curve = self.net_plot.plot(pen=pg.mkPen('#44cc88', width=2), name='上传')
            self.net_down_curve = self.net_plot.plot(pen=pg.mkPen('#4488ff', width=2), name='下载')
            self.net_plot.addLegend()

            splitter.addWidget(self.cpu_plot)
            splitter.addWidget(self.mem_plot)
            splitter.addWidget(self.net_plot)
            graph_card.addWidget(splitter)
            layout.addWidget(graph_card, 2, 0, 1, 3)

        # 历史数据
        self._max = 120
        self.cpu_hist = deque(maxlen=self._max)
        self.mem_hist = deque(maxlen=self._max)
        self.net_up_hist = deque(maxlen=self._max)
        self.net_down_hist = deque(maxlen=self._max)

    def update_data(self, data):
        cpu = data["cpu_total"]
        mem = data["mem"]
        ncores = len(data["cpu_percent"])

        self.cpu_val.setText(f"{cpu:.1f}%")
        self.cpu_sub.setText(f"{ncores} 个核心")
        self.cpu_total_bar.setValue(int(cpu))
        self._color_bar(self.cpu_total_bar, cpu)

        self.mem_val.setText(f"{mem.percent:.1f}%")
        used_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)
        self.mem_sub.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.mem_bar.setValue(int(mem.percent))
        self._color_bar(self.mem_bar, mem.percent)

        self.disk_read.setText(f"读: {bytes_fmt(data['disk_read_speed'])}/s")
        self.disk_write.setText(f"写: {bytes_fmt(data['disk_write_speed'])}/s")

        self.net_up.setText(f"↑ {bytes_fmt(data['net_sent_speed'])}/s")
        self.net_down.setText(f"↓ {bytes_fmt(data['net_recv_speed'])}/s")

        # 告警
        alerts = []
        if cpu > 80:
            alerts.append(f"CPU {cpu:.0f}%")
        if mem.percent > 85:
            alerts.append(f"内存 {mem.percent:.0f}%")
        max_disk = max((p["percent"] for p in data["disk_parts"]), default=0)
        if max_disk > 90:
            alerts.append(f"磁盘 {max_disk:.0f}%")
        if alerts:
            self.alert_status.setText(f"⚠️ 告警: {', '.join(alerts)}")
            self.alert_status.setStyleSheet("font-size: 14px; color: #ff4444; font-weight: bold; border:none;")
        else:
            self.alert_status.setText("✅ 系统正常")
            self.alert_status.setStyleSheet("font-size: 14px; color: #44cc88; border:none;")

        # Top 进程
        procs = data["processes"][:10]
        self.proc_table.setRowCount(len(procs))
        for i, p in enumerate(procs):
            name = p.get('name', '?')
            cpu_p = p.get('cpu_percent', 0) or 0
            mem_p = p.get('memory_percent', 0) or 0
            self.proc_table.setItem(i, 0, QTableWidgetItem(name))
            cpu_item = QTableWidgetItem(f"{cpu_p:.1f}")
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cpu_p > 30:
                cpu_item.setForeground(QColor("#ff6666"))
            self.proc_table.setItem(i, 1, cpu_item)
            mem_item = QTableWidgetItem(f"{mem_p:.1f}")
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.proc_table.setItem(i, 2, mem_item)

        # 图表数据
        self.cpu_hist.append(cpu)
        self.mem_hist.append(mem.percent)
        self.net_up_hist.append(max(data['net_sent_speed'], 0))
        self.net_down_hist.append(max(data['net_recv_speed'], 0))

        if HAS_PYQTGRAPH:
            x = list(range(len(self.cpu_hist)))
            self.cpu_curve.setData(x, list(self.cpu_hist))
            self.mem_curve.setData(x, list(self.mem_hist))
            self.net_up_curve.setData(x, list(self.net_up_hist))
            self.net_down_curve.setData(x, list(self.net_down_hist))

    def _color_bar(self, bar, pct):
        if pct > 90:
            c = "#ff4444"
        elif pct > 70:
            c = "#ffaa00"
        else:
            c = "#667eea"
        bar.setStyleSheet(f"""
            QProgressBar {{ border:none; border-radius:4px; background:#1a1a2e; height:8px; }}
            QProgressBar::chunk {{ border-radius:4px; background:{c}; }}
        """)


# ─── 主窗口 ──────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SysMonitor - 系统监控仪表板")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("⚡ SysMonitor")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; border:none;")
        header_layout.addWidget(title)

        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); border:none;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.time_label)

        main_layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.dashboard = DashboardPanel()
        self.cpu_panel = CpuPanel()
        self.mem_panel = MemoryPanel()
        self.disk_panel = DiskPanel()
        self.net_panel = NetworkPanel()
        self.proc_panel = ProcessPanel()
        self.graph_panel = GraphPanel()
        self.info_panel = SystemInfoPanel()
        self.alert_panel = AlertPanel()

        self.tabs.addTab(self.dashboard, "📊 仪表板")
        self.tabs.addTab(self.cpu_panel, "🔲 CPU")
        self.tabs.addTab(self.mem_panel, "💾 内存")
        self.tabs.addTab(self.disk_panel, "💿 磁盘")
        self.tabs.addTab(self.net_panel, "🌐 网络")
        self.tabs.addTab(self.proc_panel, "⚙️ 进程")
        self.tabs.addTab(self.graph_panel, "📈 图表")
        self.tabs.addTab(self.info_panel, "ℹ️ 系统信息")
        self.tabs.addTab(self.alert_panel, "⚠️ 告警")

        main_layout.addWidget(self.tabs)

        # 底部状态栏
        status = QFrame()
        status.setFixedHeight(28)
        status.setStyleSheet("QFrame { background: #080810; border-top: 1px solid #1e1e3a; }")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(12, 0, 12, 0)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 11px; color: #555; border:none;")
        status_layout.addWidget(self.status_label)
        self.fps_label = QLabel()
        self.fps_label.setStyleSheet("font-size: 11px; color: #555; border:none;")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.fps_label)
        main_layout.addWidget(status)

        # 数据采集线程
        self.collector = SystemDataCollector()
        self.collector.data_ready.connect(self._on_data)
        self.collector.start()

        # 时钟
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self._frame_count = 0
        self._last_fps_time = time.time()

    def _update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(now)

    def _on_data(self, data):
        self._frame_count += 1
        now = time.time()
        dt = now - self._last_fps_time
        if dt >= 2:
            fps = self._frame_count / dt
            self.fps_label.setText(f"更新: {fps:.1f} 次/秒")
            self._frame_count = 0
            self._last_fps_time = now

        cpu = data["cpu_total"]
        mem = data["mem"].percent
        self.status_label.setText(
            f"CPU: {cpu:.1f}%  |  内存: {mem:.1f}%  |  "
            f"上传: {bytes_fmt(data['net_sent_speed'])}/s  |  "
            f"下载: {bytes_fmt(data['net_recv_speed'])}/s"
        )

        # 更新当前可见面板
        idx = self.tabs.currentIndex()
        panels = [
            self.dashboard, self.cpu_panel, self.mem_panel,
            self.disk_panel, self.net_panel, self.proc_panel,
            self.graph_panel, self.info_panel, self.alert_panel
        ]
        if idx < len(panels):
            panels[idx].update_data(data)

    def closeEvent(self, event):
        self.collector.stop()
        super().closeEvent(event)


# ─── 入口 ──────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d0d1a"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#111122"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
