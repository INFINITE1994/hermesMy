#!/usr/bin/env python3
"""
WiFiTools - 专业WiFi管理工具
============================
功能：WiFi扫描、信号强度、网络详情、已保存密码、网速测试、信道分析、配置管理
作者：WiFiTools Team
版本：1.0.0
"""

import sys
import os
import re
import json
import time
import subprocess
import threading
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTabWidget, QGroupBox, QTextEdit, QSplitter,
    QMessageBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QPainter,
    QBrush, QPen, QPixmap, QIcon, QConicalGradient
)

import psutil


# ─── 常量 ──────────────────────────────────────────────────────────────────────
APP_NAME = "WiFiTools"
APP_VERSION = "1.0.0"
BG_COLOR = "#0a0a0a"
CARD_COLOR = "#111122"
CARD_BORDER = "#222244"
ACCENT1 = "#667eea"
ACCENT2 = "#764ba2"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#8888aa"
TEXT_DIM = "#555577"
SUCCESS = "#00cc88"
WARNING = "#ffaa00"
ERROR = "#ff4466"
SIGNAL_STRONG = "#00cc88"
SIGNAL_MEDIUM = "#ffaa00"
SIGNAL_WEAK = "#ff4466"


# ─── 样式表 ──────────────────────────────────────────────────────────────────────
STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_COLOR};
}}
QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
}}
QFrame#card {{
    background-color: {CARD_COLOR};
    border: 1px solid {CARD_BORDER};
    border-radius: 12px;
    padding: 16px;
}}
QFrame#sidebar {{
    background-color: #080818;
    border-right: 1px solid {CARD_BORDER};
}}
QPushButton#nav_btn {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_btn:hover {{
    background-color: rgba(102, 126, 234, 0.1);
    color: {TEXT_PRIMARY};
}}
QPushButton#nav_btn[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT1}, stop:1 {ACCENT2});
    color: white;
    font-weight: 600;
}}
QPushButton#action_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT1}, stop:1 {ACCENT2});
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#action_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b91ee, stop:1 #8a5fb2);
}}
QPushButton#action_btn:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5570dd, stop:1 #6a3d95);
}}
QPushButton#secondary_btn {{
    background-color: rgba(102, 126, 234, 0.15);
    color: {ACCENT1};
    border: 1px solid {ACCENT1};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#secondary_btn:hover {{
    background-color: rgba(102, 126, 234, 0.25);
}}
QLabel#title {{
    color: {TEXT_PRIMARY};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#subtitle {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}
QLabel#section_title {{
    color: {TEXT_PRIMARY};
    font-size: 15px;
    font-weight: 600;
}}
QLabel#metric_value {{
    color: {TEXT_PRIMARY};
    font-size: 28px;
    font-weight: 700;
}}
QLabel#metric_label {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
}}
QLabel#status_online {{
    color: {SUCCESS};
    font-weight: 600;
}}
QLabel#status_offline {{
    color: {ERROR};
    font-weight: 600;
}}
QTableWidget {{
    background-color: {CARD_COLOR};
    alternate-background-color: #0d0d1a;
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    gridline-color: #1a1a33;
    selection-background-color: rgba(102, 126, 234, 0.3);
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 8px;
    border: none;
}}
QHeaderView::section {{
    background-color: #0d0d1a;
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {CARD_BORDER};
    padding: 8px;
    font-size: 11px;
    font-weight: 600;
}}
QProgressBar {{
    background-color: #1a1a33;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT1}, stop:1 {ACCENT2});
    border-radius: 4px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
}}
QScrollBar::handle:vertical {{
    background: {CARD_BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QTextEdit {{
    background-color: {CARD_COLOR};
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', 'Microsoft YaHei', monospace;
    font-size: 12px;
    color: {TEXT_PRIMARY};
}}
"""


# ─── 工具函数 ──────────────────────────────────────────────────────────────────────
def run_cmd(cmd: str, timeout: int = 10) -> str:
    """执行Windows命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, encoding='gbk', errors='replace'
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return f"错误: {e}"


def parse_signal_level(signal_str: str) -> int:
    """解析信号强度百分比"""
    match = re.search(r'(\d+)%?', signal_str)
    if match:
        return int(match.group(1))
    return 0


def signal_to_bars(percent: int) -> str:
    """将百分比转换为信号格数"""
    if percent >= 75:
        return "████ 强"
    elif percent >= 50:
        return "███░ 中"
    elif percent >= 25:
        return "██░░ 弱"
    else:
        return "█░░░ 很弱"


def signal_color(percent: int) -> str:
    """根据信号强度返回颜色"""
    if percent >= 75:
        return SIGNAL_STRONG
    elif percent >= 50:
        return SIGNAL_MEDIUM
    else:
        return SIGNAL_WEAK


# ─── 工作线程 ──────────────────────────────────────────────────────────────────────
class WiFiScanThread(QThread):
    """WiFi扫描后台线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            output = run_cmd('netsh wlan show networks mode=bssid')
            networks = self._parse_networks(output)
            self.finished.emit(networks)
        except Exception as e:
            self.error.emit(str(e))

    def _parse_networks(self, output: str) -> list:
        networks = []
        current = {}
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('SSID') and 'BSSID' not in line:
                if current and current.get('ssid'):
                    networks.append(current)
                current = {'ssid': line.split(':', 1)[-1].strip()}
            elif 'BSSID' in line:
                current['bssid'] = line.split(':', 1)[-1].strip()
            elif 'Signal' in line:
                sig = line.split(':', 1)[-1].strip()
                current['signal'] = sig
                current['signal_int'] = parse_signal_level(sig)
            elif 'Authentication' in line:
                current['auth'] = line.split(':', 1)[-1].strip()
            elif 'Encryption' in line:
                current['encryption'] = line.split(':', 1)[-1].strip()
            elif 'Network type' in line:
                current['type'] = line.split(':', 1)[-1].strip()
            elif 'Channel' in line:
                ch = line.split(':', 1)[-1].strip()
                current['channel'] = ch
            elif 'Radio type' in line:
                current['radio'] = line.split(':', 1)[-1].strip()
        if current and current.get('ssid'):
            networks.append(current)
        networks.sort(key=lambda x: x.get('signal_int', 0), reverse=True)
        return networks


class SpeedTestThread(QThread):
    """网速测试后台线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = {}
            self.progress.emit("正在测试下载速度...")

            # 使用Windows内置工具测试
            # 测试下载 - 使用PowerShell
            dl_cmd = (
                'powershell -Command "'
                '$uri = \"http://speedtest.tele2.net/1MB.zip\"; '
                '$wc = New-Object System.Net.WebClient; '
                '$sw = [System.Diagnostics.Stopwatch]::StartNew(); '
                '$wc.DownloadFile($uri, \"$env:TEMP\\speedtest.tmp\"); '
                '$sw.Stop(); '
                '$elapsed = $sw.Elapsed.TotalSeconds; '
                '$size = (Get-Item \"$env:TEMP\\speedtest.tmp\").Length; '
                '$speed = [math]::Round(($size / $elapsed) / 1MB, 2); '
                'Write-Output \"$speed\"; '
                'Remove-Item \"$env:TEMP\\speedtest.tmp\" -Force"'
            )
            dl_out = run_cmd(dl_cmd, timeout=30)
            try:
                dl_speed = float(dl_out.strip().split('\n')[-1])
                result['download'] = f"{dl_speed:.2f} MB/s"
            except:
                result['download'] = "N/A"

            self.progress.emit("正在测试上传速度...")
            # 简单上传测试
            ul_cmd = (
                'powershell -Command "'
                '$uri = \"http://speedtest.tele2.net/upload.php\"; '
                '$data = New-Object byte[] 1048576; '
                '$rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new(); '
                '$rng.GetBytes($data); '
                '$wc = New-Object System.Net.WebClient; '
                '$sw = [System.Diagnostics.Stopwatch]::StartNew(); '
                '$wc.UploadData($uri, $data); '
                '$sw.Stop(); '
                '$speed = [math]::Round((1048576 / $sw.Elapsed.TotalSeconds) / 1MB, 2); '
                'Write-Output \"$speed\""'
            )
            ul_out = run_cmd(ul_cmd, timeout=30)
            try:
                ul_speed = float(ul_out.strip().split('\n')[-1])
                result['upload'] = f"{ul_speed:.2f} MB/s"
            except:
                result['upload'] = "N/A"

            self.progress.emit("正在测试延迟...")
            ping_cmd = 'ping -n 4 8.8.8.8'
            ping_out = run_cmd(ping_cmd, timeout=15)
            ping_match = re.search(r'Average = (\d+)ms', ping_out)
            if ping_match:
                result['ping'] = f"{ping_match.group(1)} ms"
            else:
                result['ping'] = "N/A"

            self.progress.emit("测试完成")
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─── 自定义组件 ──────────────────────────────────────────────────────────────────────
class GradientLabel(QLabel):
    """渐变色标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._gradient_colors = [ACCENT1, ACCENT2]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(self._gradient_colors[0]))
        gradient.setColorAt(1, QColor(self._gradient_colors[1]))
        painter.setPen(QPen(QBrush(gradient), 1))
        font = self.font()
        painter.setFont(font)
        painter.drawText(self.rect(), int(self.alignment()), self.text())


class SignalBar(QWidget):
    """信号强度条形图组件"""
    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self.setFixedHeight(24)
        self.setMinimumWidth(120)

    def setValue(self, value):
        self._value = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_h = 8
        y = (h - bar_h) / 2

        # 背景
        painter.setBrush(QColor("#1a1a33"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, int(y), w, bar_h, 4, 4)

        # 填充
        fill_w = int(w * self._value / 100)
        if fill_w > 0:
            gradient = QLinearGradient(0, 0, fill_w, 0)
            color = QColor(signal_color(self._value))
            gradient.setColorAt(0, color.lighter(130))
            gradient.setColorAt(1, color)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(0, int(y), fill_w, bar_h, 4, 4)


class MetricCard(QFrame):
    """指标卡片"""
    def __init__(self, title="", value="", subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedSize(180, 110)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 14, 16, 14)

        t = QLabel(title)
        t.setObjectName("metric_label")
        layout.addWidget(t)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metric_value")
        layout.addWidget(self.value_label)

        s = QLabel(subtitle)
        s.setObjectName("subtitle")
        layout.addWidget(s)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def setValue(self, text):
        self.value_label.setText(text)


# ─── 页面组件 ──────────────────────────────────────────────────────────────────────
class OverviewPage(QWidget):
    """概览页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_stats)
        self._update_timer.start(3000)
        self._update_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("📊 系统概览")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("实时监控系统网络状态")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        # 指标卡片行
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_status = MetricCard("连接状态", "检测中...", "")
        self.card_speed = MetricCard("当前网速", "--", "KB/s")
        self.card_sent = MetricCard("已发送", "--", "MB")
        self.card_recv = MetricCard("已接收", "--", "MB")
        self.card_conn = MetricCard("活跃连接", "--", "个")

        for card in [self.card_status, self.card_speed, self.card_sent,
                     self.card_recv, self.card_conn]:
            cards_layout.addWidget(card)
        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # 网络信息卡片
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)

        info_title = QLabel("🌐 当前网络信息")
        info_title.setObjectName("section_title")
        info_layout.addWidget(info_title)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        info_layout.addWidget(self.info_text)

        shadow = QGraphicsDropShadowEffect(info_card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        info_card.setGraphicsEffect(shadow)
        layout.addWidget(info_card)
        layout.addStretch()

    def _update_stats(self):
        try:
            net_io = psutil.net_io_counters()
            self.card_sent.setValue(f"{net_io.bytes_sent / 1048576:.1f}")
            self.card_recv.setValue(f"{net_io.bytes_recv / 1048576:.1f}")

            connections = psutil.net_connections(kind='inet')
            active = sum(1 for c in connections if c.status == 'ESTABLISHED')
            self.card_conn.setValue(str(active))

            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            wifi_info = []
            is_connected = False
            for name, stat in stats.items():
                if stat.isup and 'Wi-Fi' in name or 'Wireless' in name or 'WLAN' in name:
                    is_connected = True
                    if name in addrs:
                        for addr in addrs[name]:
                            if addr.family.name == 'AF_INET':
                                wifi_info.append(f"接口: {name}")
                                wifi_info.append(f"IP地址: {addr.address}")
                                wifi_info.append(f"子网掩码: {addr.netmask}")
                    wifi_info.append(f"速度: {stat.speed} Mbps")
                    wifi_info.append(f"MTU: {stat.mtu}")

            if is_connected:
                self.card_status.setValue("已连接")
                self.card_status.value_label.setStyleSheet(f"color: {SUCCESS}")
            else:
                self.card_status.setValue("未连接")
                self.card_status.value_label.setStyleSheet(f"color: {ERROR}")

            # 获取WiFi SSID
            wlan_out = run_cmd('netsh wlan show interfaces')
            ssid_match = re.search(r'SSID\s*:\s*(.+)', wlan_out)
            if ssid_match:
                wifi_info.insert(0, f"WiFi名称: {ssid_match.group(1).strip()}")

            self.info_text.setText('\n'.join(wifi_info) if wifi_info else "未检测到WiFi连接")

        except Exception:
            pass


class ScanPage(QWidget):
    """WiFi扫描页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_thread = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 顶部栏
        top = QHBoxLayout()
        title = QLabel("📡 WiFi扫描器")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()

        self.scan_btn = QPushButton("⟳ 开始扫描")
        self.scan_btn.setObjectName("action_btn")
        self.scan_btn.setFixedWidth(120)
        self.scan_btn.clicked.connect(self._start_scan)
        top.addWidget(self.scan_btn)
        layout.addLayout(top)

        subtitle = QLabel("扫描附近的WiFi网络并显示详细信息")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "SSID", "信号强度", "信号", "认证方式", "加密", "信道", "BSSID"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # 状态栏
        self.status_label = QLabel("点击扫描按钮开始搜索WiFi网络")
        self.status_label.setObjectName("subtitle")
        layout.addWidget(self.status_label)

        self._start_scan()

    def _start_scan(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        self.status_label.setText("正在扫描附近的WiFi网络...")
        self._scan_thread = WiFiScanThread()
        self._scan_thread.finished.connect(self._on_scan_done)
        self._scan_thread.error.connect(self._on_scan_error)
        self._scan_thread.start()

    def _on_scan_done(self, networks):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("⟳ 开始扫描")
        self.table.setRowCount(len(networks))
        for i, net in enumerate(networks):
            ssid = net.get('ssid', '未知')
            signal = net.get('signal', 'N/A')
            signal_int = net.get('signal_int', 0)
            auth = net.get('auth', 'N/A')
            enc = net.get('encryption', 'N/A')
            channel = net.get('channel', 'N/A')
            bssid = net.get('bssid', 'N/A')

            self.table.setItem(i, 0, QTableWidgetItem(ssid))
            self.table.setItem(i, 1, QTableWidgetItem(signal))

            # 信号强度条
            bar = SignalBar(signal_int)
            self.table.setCellWidget(i, 2, bar)

            self.table.setItem(i, 3, QTableWidgetItem(auth))
            self.table.setItem(i, 4, QTableWidgetItem(enc))
            self.table.setItem(i, 5, QTableWidgetItem(channel))
            self.table.setItem(i, 6, QTableWidgetItem(bssid))

        self.status_label.setText(f"扫描完成，发现 {len(networks)} 个网络")

    def _on_scan_error(self, err):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("⟳ 开始扫描")
        self.status_label.setText(f"扫描失败: {err}")


class PasswordPage(QWidget):
    """已保存密码页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        top = QHBoxLayout()
        title = QLabel("🔑 已保存密码")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()

        refresh_btn = QPushButton("⟳ 刷新")
        refresh_btn.setObjectName("action_btn")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._load_passwords)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        subtitle = QLabel("查看系统中已保存的WiFi密码（需要管理员权限）")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["配置名称", "密码"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitle")
        layout.addWidget(self.status_label)

        self._load_passwords()

    def _load_passwords(self):
        profiles_out = run_cmd('netsh wlan show profiles')
        profiles = re.findall(r'All User Profile\s*:\s*(.+)', profiles_out)
        if not profiles:
            profiles = re.findall(r'用户配置文件\s*:\s*(.+)', profiles_out)

        self.table.setRowCount(len(profiles))
        for i, profile in enumerate(profiles):
            name = profile.strip()
            self.table.setItem(i, 0, QTableWidgetItem(name))
            detail = run_cmd(f'netsh wlan show profile name="{name}" key=clear')
            key_match = re.search(r'Key Content\s*:\s*(.+)', detail)
            if not key_match:
                key_match = re.search(r'关键内容\s*:\s*(.+)', detail)
            password = key_match.group(1).strip() if key_match else "(无密码或受保护)"
            self.table.setItem(i, 1, QTableWidgetItem(password))

        self.status_label.setText(f"共找到 {len(profiles)} 个已保存的WiFi配置")


class SpeedTestPage(QWidget):
    """网速测试页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._test_thread = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚡ 网速测试")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("测试当前网络的下载、上传速度和延迟")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 结果卡片
        cards = QHBoxLayout()
        cards.setSpacing(12)

        self.dl_card = MetricCard("下载速度", "--", "MB/s")
        self.ul_card = MetricCard("上传速度", "--", "MB/s")
        self.ping_card = MetricCard("延迟", "--", "ms")

        for card in [self.dl_card, self.ul_card, self.ping_card]:
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 80))
            card.setGraphicsEffect(shadow)
            cards.addWidget(card)
        cards.addStretch()
        layout.addLayout(cards)

        # 进度
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("subtitle")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 按钮
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("▶ 开始测试")
        self.test_btn.setObjectName("action_btn")
        self.test_btn.setFixedWidth(140)
        self.test_btn.clicked.connect(self._start_test)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 日志
        log_label = QLabel("测试日志")
        log_label.setObjectName("section_title")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        shadow = QGraphicsDropShadowEffect(self.log_text)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.log_text.setGraphicsEffect(shadow)

    def _start_test(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.progress_bar.show()
        self.log_text.clear()
        self._test_thread = SpeedTestThread()
        self._test_thread.progress.connect(self._on_progress)
        self._test_thread.finished.connect(self._on_done)
        self._test_thread.error.connect(self._on_error)
        self._test_thread.start()

    def _on_progress(self, msg):
        self.progress_label.setText(msg)
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def _on_done(self, result):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("▶ 开始测试")
        self.progress_bar.hide()
        self.dl_card.setValue(result.get('download', 'N/A'))
        self.ul_card.setValue(result.get('upload', 'N/A'))
        self.ping_card.setValue(result.get('ping', 'N/A'))
        self.log_text.append(f"\n{'='*40}")
        self.log_text.append(f"下载: {result.get('download', 'N/A')}")
        self.log_text.append(f"上传: {result.get('upload', 'N/A')}")
        self.log_text.append(f"延迟: {result.get('ping', 'N/A')}")
        self.log_text.append(f"{'='*40}")

    def _on_error(self, err):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("▶ 开始测试")
        self.progress_bar.hide()
        self.progress_label.setText(f"测试失败: {err}")
        self.log_text.append(f"[错误] {err}")


class ChannelPage(QWidget):
    """信道分析页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        top = QHBoxLayout()
        title = QLabel("📶 信道分析")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()

        scan_btn = QPushButton("⟳ 分析信道")
        scan_btn.setObjectName("action_btn")
        scan_btn.setFixedWidth(120)
        scan_btn.clicked.connect(self._analyze)
        top.addWidget(scan_btn)
        layout.addLayout(top)

        subtitle = QLabel("分析各信道的使用情况，找到最不拥挤的信道")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 信道分布表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["信道", "网络数量", "信号强度", "拥挤程度"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # 推荐
        self.recommend_label = QLabel("")
        self.recommend_label.setObjectName("section_title")
        layout.addWidget(self.recommend_label)

        self._analyze()

    def _analyze(self):
        output = run_cmd('netsh wlan show networks mode=bssid')
        channels = {}
        for line in output.split('\n'):
            line = line.strip()
            if 'Channel' in line and ':' in line:
                ch = line.split(':', 1)[-1].strip()
                if ch.isdigit():
                    channels[ch] = channels.get(ch, 0) + 1

        if not channels:
            # Fallback
            channels = {"1": 0, "6": 0, "11": 0}

        self.table.setRowCount(len(channels))
        for i, (ch, count) in enumerate(sorted(channels.items(), key=lambda x: int(x[0]))):
            self.table.setItem(i, 0, QTableWidgetItem(f"信道 {ch}"))
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))

            # 拥挤程度
            if count == 0:
                level = "空闲"
                color = SUCCESS
            elif count <= 2:
                level = "畅通"
                color = SUCCESS
            elif count <= 4:
                level = "一般"
                color = WARNING
            else:
                level = "拥挤"
                color = ERROR

            level_item = QTableWidgetItem(level)
            level_item.setForeground(QColor(color))
            self.table.setItem(i, 3, level_item)

        # 推荐最佳信道
        best = min(channels.items(), key=lambda x: x[1])
        self.recommend_label.setText(f"✅ 推荐使用信道 {best[0]}（当前仅有 {best[1]} 个网络）")


class ProfilePage(QWidget):
    """WiFi配置管理页"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        top = QHBoxLayout()
        title = QLabel("📋 WiFi配置管理")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()

        refresh_btn = QPushButton("⟳ 刷新")
        refresh_btn.setObjectName("action_btn")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._load_profiles)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        subtitle = QLabel("管理系统中保存的WiFi配置文件")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["配置名称", "连接模式", "自动连接", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitle")
        layout.addWidget(self.status_label)

        # 操作说明
        help_card = QFrame()
        help_card.setObjectName("card")
        help_layout = QVBoxLayout(help_card)
        help_title = QLabel("💡 操作说明")
        help_title.setObjectName("section_title")
        help_layout.addWidget(help_title)
        help_text = QLabel(
            '• 删除配置：使用管理员权限运行本程序后，点击"删除"按钮\n'
            '• 导出配置：netsh wlan export profile name="名称"\n'
            '• 导入配置：netsh wlan add profile filename="文件路径"'
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        help_layout.addWidget(help_text)
        shadow = QGraphicsDropShadowEffect(help_card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        help_card.setGraphicsEffect(shadow)
        layout.addWidget(help_card)

        self._load_profiles()

    def _load_profiles(self):
        output = run_cmd('netsh wlan show profiles')
        profiles = re.findall(r'All User Profile\s*:\s*(.+)', output)
        if not profiles:
            profiles = re.findall(r'用户配置文件\s*:\s*(.+)', output)

        self.table.setRowCount(len(profiles))
        for i, profile in enumerate(profiles):
            name = profile.strip()
            self.table.setItem(i, 0, QTableWidgetItem(name))

            detail = run_cmd(f'netsh wlan show profile name="{name}"')
            mode_match = re.search(r'Network type\s*:\s*(.+)', detail)
            if not mode_match:
                mode_match = re.search(r'网络类型\s*:\s*(.+)', detail)
            mode = mode_match.group(1).strip() if mode_match else "N/A"
            self.table.setItem(i, 1, QTableWidgetItem(mode))

            auto_match = re.search(r'Connection mode\s*:\s*(.+)', detail)
            if not auto_match:
                auto_match = re.search(r'连接模式\s*:\s*(.+)', detail)
            auto = auto_match.group(1).strip() if auto_match else "N/A"
            self.table.setItem(i, 2, QTableWidgetItem(auto))

            del_btn = QPushButton("删除")
            del_btn.setObjectName("secondary_btn")
            del_btn.setFixedWidth(70)
            del_btn.clicked.connect(lambda checked, n=name: self._delete_profile(n))
            self.table.setCellWidget(i, 3, del_btn)

        self.status_label.setText(f"共 {len(profiles)} 个已保存的WiFi配置")

    def _delete_profile(self, name):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除WiFi配置 \"{name}\" 吗？\n此操作需要管理员权限。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            result = run_cmd(f'netsh wlan delete profile name="{name}"')
            if 'deleted' in result.lower() or '已删除' in result:
                QMessageBox.information(self, "成功", f"配置 \"{name}\" 已删除")
                self._load_profiles()
            else:
                QMessageBox.warning(self, "失败", f"删除失败，请以管理员权限运行\n{result}")


# ─── 主窗口 ──────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - 专业WiFi管理工具")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)
        self._current_nav = 0
        self._nav_buttons = []
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 侧边栏
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(4)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)

        # Logo
        logo = QLabel("📶 WiFiTools")
        logo.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 700;
            padding: 8px 4px 16px 4px;
        """)
        sidebar_layout.addWidget(logo)

        nav_items = [
            ("📊  系统概览", 0),
            ("📡  WiFi扫描", 1),
            ("🔑  已保存密码", 2),
            ("⚡  网速测试", 3),
            ("📶  信道分析", 4),
            ("📋  配置管理", 5),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; padding: 8px;")
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # 内容区
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(OverviewPage())
        self.stack.addWidget(ScanPage())
        self.stack.addWidget(PasswordPage())
        self.stack.addWidget(SpeedTestPage())
        self.stack.addWidget(ChannelPage())
        self.stack.addWidget(ProfilePage())

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content)

        self._switch_page(0)

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setStyle("Fusion")

    # 深色调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_COLOR))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_COLOR))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0d0d1a"))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(CARD_COLOR))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT1))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT_PRIMARY))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
