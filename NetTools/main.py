#!/usr/bin/env python3
"""
NetTools - 网络工具箱
一个功能齐全的网络工具箱桌面应用程序
"""

import sys
import os
import socket
import subprocess
import threading
import time
import re
import json
import ipaddress
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox,
    QGroupBox, QGridLayout, QProgressBar, QComboBox, QCheckBox,
    QMessageBox, QFileDialog, QSplitter, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor, QLinearGradient, QPainter, QBrush


# ==================== 样式常量 ====================
DARK_THEME = """
QMainWindow {
    background-color: #0a0a0a;
}

QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

QTabWidget::pane {
    border: 1px solid #333;
    background-color: #111122;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #b0b0b0;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #2a2a4e;
}

QGroupBox {
    background-color: #111122;
    border: 1px solid #333;
    border-radius: 12px;
    margin-top: 10px;
    padding: 20px 15px 15px 15px;
    font-weight: bold;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 15px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border-radius: 6px;
    margin-left: 10px;
}

QLineEdit {
    background-color: #1a1a2e;
    border: 2px solid #333;
    border-radius: 8px;
    padding: 10px 15px;
    color: #e0e0e0;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #667eea;
}

QLineEdit:hover {
    border-color: #444;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #7b8ff0, stop:1 #8b5fb8);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #5567d9, stop:1 #653a91);
}

QPushButton:disabled {
    background-color: #333;
    color: #666;
}

QPushButton#stopButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ff6b6b, stop:1 #ee5a24);
}

QPushButton#stopButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ff8888, stop:1 #ff7744);
}

QTextEdit {
    background-color: #0d0d1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    color: #00ff88;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #667eea;
}

QSpinBox {
    background-color: #1a1a2e;
    border: 2px solid #333;
    border-radius: 8px;
    padding: 8px;
    color: #e0e0e0;
    font-size: 14px;
}

QSpinBox:focus {
    border-color: #667eea;
}

QComboBox {
    background-color: #1a1a2e;
    border: 2px solid #333;
    border-radius: 8px;
    padding: 8px 15px;
    color: #e0e0e0;
    font-size: 14px;
    min-width: 120px;
}

QComboBox:focus {
    border-color: #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #667eea;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    border: 1px solid #333;
    color: #e0e0e0;
    selection-background-color: #667eea;
}

QProgressBar {
    border: 2px solid #333;
    border-radius: 8px;
    text-align: center;
    background-color: #1a1a2e;
    color: white;
    font-weight: bold;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}

QLabel {
    color: #b0b0b0;
    font-size: 13px;
}

QLabel#titleLabel {
    color: white;
    font-size: 18px;
    font-weight: bold;
}

QLabel#resultLabel {
    color: #00ff88;
    font-size: 16px;
    font-weight: bold;
}

QCheckBox {
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #333;
    background-color: #1a1a2e;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    border-color: #667eea;
}

QScrollArea {
    border: none;
    background-color: #0a0a0a;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 12px;
    margin: 0;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #333;
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #667eea;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 12px;
    margin: 0;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #333;
    min-width: 30px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #667eea;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
"""


# ==================== 工作线程 ====================
class PingWorker(QThread):
    """Ping 工具工作线程"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, host: str, count: int = 4, timeout: int = 3):
        super().__init__()
        self.host = host
        self.count = count
        self.timeout = timeout
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit(f"正在 Ping {self.host}，发送 {self.count} 个数据包...\n")

            # 解析主机名
            try:
                ip = socket.gethostbyname(self.host)
                self.output_signal.emit(f"目标 IP: {ip}\n")
            except socket.gaierror:
                self.error_signal.emit(f"无法解析主机名: {self.host}")
                return

            # 执行 ping 命令
            if sys.platform == "win32":
                cmd = ["ping", "-n", str(self.count), "-w", str(self.timeout * 1000), self.host]
            else:
                cmd = ["ping", "-c", str(self.count), "-W", str(self.timeout), self.host]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='gbk' if sys.platform == "win32" else 'utf-8',
                errors='ignore'
            )

            while self._is_running:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_signal.emit(output.strip())

            if self._is_running:
                # 获取统计信息
                stdout, stderr = process.communicate()
                if stdout:
                    self.output_signal.emit("\n" + stdout)

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"Ping 错误: {str(e)}")

    def stop(self):
        self._is_running = False
        self.terminate()


class PortScanWorker(QThread):
    """端口扫描工作线程"""
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, host: str, start_port: int = 1, end_port: int = 1024, threads: int = 100):
        super().__init__()
        self.host = host
        self.start_port = start_port
        self.end_port = end_port
        self.threads = threads
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit(f"开始扫描 {self.host} 的端口...")
            self.output_signal.emit(f"端口范围: {self.start_port}-{self.end_port}\n")

            open_ports = []
            total_ports = self.end_port - self.start_port + 1
            scanned = 0

            def scan_port(port):
                nonlocal scanned
                if not self._is_running:
                    return

                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((self.host, port))
                    sock.close()

                    if result == 0:
                        try:
                            service = socket.getservbyname(port, 'tcp')
                        except:
                            service = "未知"
                        open_ports.append((port, service))
                        self.output_signal.emit(f"✓ 端口 {port} 开放 - {service}")

                    scanned += 1
                    if scanned % 50 == 0:
                        progress = int((scanned / total_ports) * 100)
                        self.progress_signal.emit(progress)
                        self.output_signal.emit(f"已扫描 {scanned}/{total_ports} 个端口...")

                except Exception as e:
                    pass

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = []
                for port in range(self.start_port, self.end_port + 1):
                    if not self._is_running:
                        break
                    futures.append(executor.submit(scan_port, port))

                for future in as_completed(futures):
                    if not self._is_running:
                        break
                    future.result()

            if self._is_running:
                self.progress_signal.emit(100)
                self.output_signal.emit(f"\n扫描完成！")
                self.output_signal.emit(f"共扫描 {total_ports} 个端口")

                if open_ports:
                    self.output_signal.emit(f"\n发现 {len(open_ports)} 个开放端口:")
                    self.output_signal.emit("-" * 40)
                    for port, service in sorted(open_ports):
                        self.output_signal.emit(f"  {port:<8} {service}")
                else:
                    self.output_signal.emit("\n未发现开放端口")

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"端口扫描错误: {str(e)}")

    def stop(self):
        self._is_running = False
        self.terminate()


class DNSLookupWorker(QThread):
    """DNS 查询工作线程"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, domain: str, record_type: str = "A"):
        super().__init__()
        self.domain = domain
        self.record_type = record_type

    def run(self):
        try:
            self.output_signal.emit(f"正在查询 {self.domain} 的 {self.record_type} 记录...\n")

            # 使用 nslookup 命令
            if sys.platform == "win32":
                cmd = ["nslookup", "-type=" + self.record_type, self.domain]
            else:
                cmd = ["nslookup", "-type=" + self.record_type, self.domain]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='gbk' if sys.platform == "win32" else 'utf-8',
                errors='ignore'
            )

            stdout, stderr = process.communicate()

            if stdout:
                self.output_signal.emit(stdout)
            if stderr:
                self.output_signal.emit(stderr)

            # 额外的 DNS 信息
            self.output_signal.emit("\n" + "=" * 50)
            self.output_signal.emit("详细 DNS 信息:")
            self.output_signal.emit("=" * 50)

            try:
                # 获取所有 IP 地址
                ips = socket.getaddrinfo(self.domain, None)
                self.output_signal.emit(f"\n所有 IP 地址:")
                seen = set()
                for info in ips:
                    ip = info[4][0]
                    if ip not in seen:
                        seen.add(ip)
                        self.output_signal.emit(f"  - {ip} ({info[0].name})")
            except Exception as e:
                self.output_signal.emit(f"获取详细信息失败: {e}")

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"DNS 查询错误: {str(e)}")


class IPInfoWorker(QThread):
    """IP 信息工作线程"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, get_local: bool = True, get_public: bool = True):
        super().__init__()
        self.get_local = get_local
        self.get_public = get_public

    def run(self):
        try:
            if self.get_local:
                self.output_signal.emit("=" * 60)
                self.output_signal.emit("本地网络信息")
                self.output_signal.emit("=" * 60)

                # 主机名
                hostname = socket.gethostname()
                self.output_signal.emit(f"\n主机名: {hostname}")

                # 网络接口信息
                self.output_signal.emit("\n网络接口:")
                self.output_signal.emit("-" * 60)

                for iface_name, iface_addrs in psutil.net_if_addrs().items():
                    self.output_signal.emit(f"\n接口: {iface_name}")
                    for addr in iface_addrs:
                        if addr.family == socket.AF_INET:
                            self.output_signal.emit(f"  IPv4: {addr.address}")
                            self.output_signal.emit(f"  子网掩码: {addr.netmask}")
                        elif addr.family == socket.AF_INET6:
                            self.output_signal.emit(f"  IPv6: {addr.address}")
                        elif hasattr(socket, 'AF_LINK') and addr.family == socket.AF_LINK:
                            self.output_signal.emit(f"  MAC: {addr.address}")

                # 网络统计
                net_io = psutil.net_io_counters()
                self.output_signal.emit("\n网络流量统计:")
                self.output_signal.emit("-" * 60)
                self.output_signal.emit(f"  发送字节: {self.format_bytes(net_io.bytes_sent)}")
                self.output_signal.emit(f"  接收字节: {self.format_bytes(net_io.bytes_recv)}")
                self.output_signal.emit(f"  发送包数: {net_io.packets_sent:,}")
                self.output_signal.emit(f"  接收包数: {net_io.packets_recv:,}")

            if self.get_public:
                self.output_signal.emit("\n" + "=" * 60)
                self.output_signal.emit("公网 IP 信息")
                self.output_signal.emit("=" * 60)

                try:
                    # 获取公网 IP
                    response = requests.get("https://api.ipify.org?format=json", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        public_ip = data['ip']
                        self.output_signal.emit(f"\n公网 IP: {public_ip}")

                        # 获取 IP 详细信息
                        try:
                            ip_response = requests.get(f"http://ip-api.com/json/{public_ip}", timeout=10)
                            if ip_response.status_code == 200:
                                ip_data = ip_response.json()
                                if ip_data.get('status') == 'success':
                                    self.output_signal.emit(f"国家: {ip_data.get('country', 'N/A')}")
                                    self.output_signal.emit(f"地区: {ip_data.get('regionName', 'N/A')}")
                                    self.output_signal.emit(f"城市: {ip_data.get('city', 'N/A')}")
                                    self.output_signal.emit(f"ISP: {ip_data.get('isp', 'N/A')}")
                                    self.output_signal.emit(f"组织: {ip_data.get('org', 'N/A')}")
                                    self.output_signal.emit(f"时区: {ip_data.get('timezone', 'N/A')}")
                        except:
                            self.output_signal.emit("无法获取 IP 详细信息")
                    else:
                        self.output_signal.emit("无法获取公网 IP")
                except Exception as e:
                    self.output_signal.emit(f"获取公网 IP 失败: {e}")

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"IP 信息获取错误: {str(e)}")

    def format_bytes(self, bytes: int) -> str:
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"


class TracerouteWorker(QThread):
    """路由追踪工作线程"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, host: str, max_hops: int = 30):
        super().__init__()
        self.host = host
        self.max_hops = max_hops
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit(f"正在追踪到 {self.host} 的路由...")
            self.output_signal.emit(f"最大跳数: {self.max_hops}\n")

            # 解析主机名
            try:
                ip = socket.gethostbyname(self.host)
                self.output_signal.emit(f"目标 IP: {ip}\n")
            except socket.gaierror:
                self.error_signal.emit(f"无法解析主机名: {self.host}")
                return

            # 执行 traceroute/tracert 命令
            if sys.platform == "win32":
                cmd = ["tracert", "-d", "-h", str(self.max_hops), self.host]
            else:
                cmd = ["traceroute", "-n", "-m", str(self.max_hops), self.host]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='gbk' if sys.platform == "win32" else 'utf-8',
                errors='ignore'
            )

            while self._is_running:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_signal.emit(output.rstrip())

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"路由追踪错误: {str(e)}")

    def stop(self):
        self._is_running = False
        self.terminate()


class SpeedTestWorker(QThread):
    """网速测试工作线程"""
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit("=" * 60)
            self.output_signal.emit("网速测试")
            self.output_signal.emit("=" * 60)

            # 测试服务器列表
            test_urls = [
                ("http://speedtest.tele2.net/1MB.zip", "Tele2 (1MB)"),
                ("http://proof.ovh.net/files/1Mb.dat", "OVH (1MB)"),
                ("http://speedtest.ftp.otenet.gr/files/test1Mb.db", "Otenet (1MB)"),
            ]

            # 下载测试
            self.output_signal.emit("\n下载速度测试:")
            self.output_signal.emit("-" * 60)

            download_speeds = []
            for url, name in test_urls:
                if not self._is_running:
                    break

                try:
                    self.output_signal.emit(f"测试服务器: {name}")
                    start_time = time.time()
                    response = requests.get(url, timeout=30)
                    end_time = time.time()

                    if response.status_code == 200:
                        data_size = len(response.content)
                        duration = end_time - start_time
                        speed = (data_size * 8) / (duration * 1000000)  # Mbps
                        download_speeds.append(speed)
                        self.output_signal.emit(f"  数据大小: {data_size / 1024:.2f} KB")
                        self.output_signal.emit(f"  耗时: {duration:.2f} 秒")
                        self.output_signal.emit(f"  速度: {speed:.2f} Mbps")
                    else:
                        self.output_signal.emit(f"  请求失败: HTTP {response.status_code}")

                except Exception as e:
                    self.output_signal.emit(f"  测试失败: {e}")

                self.progress_signal.emit(33)

            # 上传测试 (模拟)
            self.output_signal.emit("\n上传速度测试:")
            self.output_signal.emit("-" * 60)

            upload_speeds = []
            for i in range(3):
                if not self._is_running:
                    break

                try:
                    self.output_signal.emit(f"测试 {i+1}/3...")
                    data = os.urandom(1024 * 100)  # 100KB
                    start_time = time.time()
                    response = requests.post(
                        "http://httpbin.org/post",
                        data=data,
                        timeout=30
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        duration = end_time - start_time
                        speed = (len(data) * 8) / (duration * 1000000)  # Mbps
                        upload_speeds.append(speed)
                        self.output_signal.emit(f"  数据大小: {len(data) / 1024:.2f} KB")
                        self.output_signal.emit(f"  耗时: {duration:.2f} 秒")
                        self.output_signal.emit(f"  速度: {speed:.2f} Mbps")

                except Exception as e:
                    self.output_signal.emit(f"  测试失败: {e}")

                self.progress_signal.emit(66)

            # Ping 测试
            self.output_signal.emit("\n延迟测试:")
            self.output_signal.emit("-" * 60)

            ping_results = []
            for host in ["8.8.8.8", "1.1.1.1", "114.114.114.114"]:
                if not self._is_running:
                    break

                try:
                    if sys.platform == "win32":
                        cmd = ["ping", "-n", "4", "-w", "1000", host]
                    else:
                        cmd = ["ping", "-c", "4", "-W", "1", host]

                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='gbk' if sys.platform == "win32" else 'utf-8',
                        errors='ignore'
                    )
                    stdout, _ = process.communicate()

                    # 提取平均延迟
                    if sys.platform == "win32":
                        match = re.search(r'平均 = (\d+)ms', stdout)
                    else:
                        match = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/', stdout)

                    if match:
                        avg_ping = float(match.group(1))
                        ping_results.append(avg_ping)
                        self.output_signal.emit(f"  {host}: {avg_ping:.2f} ms")
                    else:
                        self.output_signal.emit(f"  {host}: 超时")

                except Exception as e:
                    self.output_signal.emit(f"  {host}: 错误 - {e}")

                self.progress_signal.emit(100)

            # 汇总结果
            self.output_signal.emit("\n" + "=" * 60)
            self.output_signal.emit("测试结果汇总")
            self.output_signal.emit("=" * 60)

            if download_speeds:
                avg_download = sum(download_speeds) / len(download_speeds)
                self.output_signal.emit(f"平均下载速度: {avg_download:.2f} Mbps")
            else:
                self.output_signal.emit("下载速度: 测试失败")

            if upload_speeds:
                avg_upload = sum(upload_speeds) / len(upload_speeds)
                self.output_signal.emit(f"平均上传速度: {avg_upload:.2f} Mbps")
            else:
                self.output_signal.emit("上传速度: 测试失败")

            if ping_results:
                avg_ping = sum(ping_results) / len(ping_results)
                self.output_signal.emit(f"平均延迟: {avg_ping:.2f} ms")
            else:
                self.output_signal.emit("延迟: 测试失败")

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"网速测试错误: {str(e)}")

    def stop(self):
        self._is_running = False
        self.terminate()


class WhoisWorker(QThread):
    """Whois 查询工作线程"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, domain: str):
        super().__init__()
        self.domain = domain

    def run(self):
        try:
            self.output_signal.emit(f"正在查询 {self.domain} 的 Whois 信息...\n")

            # 使用 whois 命令
            if sys.platform == "win32":
                # Windows 可能没有 whois 命令，使用 nslookup 作为备选
                self.output_signal.emit("Windows 系统使用在线查询...")
                self.query_whois_online()
            else:
                try:
                    cmd = ["whois", self.domain]
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()

                    if stdout:
                        self.output_signal.emit(stdout)
                    if stderr:
                        self.output_signal.emit(stderr)
                except FileNotFoundError:
                    self.query_whois_online()

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"Whois 查询错误: {str(e)}")

    def query_whois_online(self):
        """在线 Whois 查询"""
        try:
            # 使用 whoisxmlapi.com 的免费 API (需要注册获取 API key)
            # 这里使用一个备选方案
            response = requests.get(
                f"https://whois.arin.net/rest/domain/{self.domain}.json",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.output_signal.emit(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.output_signal.emit("无法获取 Whois 信息")
                self.output_signal.emit("请使用命令行工具: whois " + self.domain)
        except Exception as e:
            self.output_signal.emit(f"在线查询失败: {e}")
            self.output_signal.emit("请使用命令行工具: whois " + self.domain)


class NetworkScanWorker(QThread):
    """网络扫描工作线程"""
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, network: str = "192.168.1.0/24", timeout: float = 0.5):
        super().__init__()
        self.network = network
        self.timeout = timeout
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit(f"开始扫描网络: {self.network}")
            self.output_signal.emit("=" * 60)

            # 解析网络地址
            try:
                net = ipaddress.ip_network(self.network, strict=False)
            except ValueError as e:
                self.error_signal.emit(f"无效的网络地址: {e}")
                return

            hosts = list(net.hosts())
            total_hosts = len(hosts)
            self.output_signal.emit(f"扫描范围: {hosts[0]} - {hosts[-1]}")
            self.output_signal.emit(f"总主机数: {total_hosts}\n")

            discovered_devices = []
            scanned = 0

            def scan_host(ip):
                nonlocal scanned
                if not self._is_running:
                    return

                ip_str = str(ip)
                try:
                    # 尝试 ping
                    if sys.platform == "win32":
                        cmd = ["ping", "-n", "1", "-w", str(int(self.timeout * 1000)), ip_str]
                    else:
                        cmd = ["ping", "-c", "1", "-W", str(self.timeout), ip_str]

                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='gbk' if sys.platform == "win32" else 'utf-8',
                        errors='ignore'
                    )
                    stdout, _ = process.communicate()

                    if process.returncode == 0:
                        # 尝试获取主机名
                        try:
                            hostname = socket.gethostbyaddr(ip_str)[0]
                        except:
                            hostname = "未知"

                        # 尝试获取 MAC 地址 (仅本地网络)
                        mac = self.get_mac(ip_str)

                        device_info = {
                            'ip': ip_str,
                            'hostname': hostname,
                            'mac': mac
                        }
                        discovered_devices.append(device_info)
                        self.output_signal.emit(f"✓ 发现设备: {ip_str} ({hostname})")

                except Exception as e:
                    pass

                scanned += 1
                if scanned % 10 == 0:
                    progress = int((scanned / total_hosts) * 100)
                    self.progress_signal.emit(progress)

            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = []
                for host in hosts:
                    if not self._is_running:
                        break
                    futures.append(executor.submit(scan_host, host))

                for future in as_completed(futures):
                    if not self._is_running:
                        break
                    future.result()

            if self._is_running:
                self.progress_signal.emit(100)
                self.output_signal.emit("\n" + "=" * 60)
                self.output_signal.emit(f"扫描完成！")
                self.output_signal.emit(f"发现 {len(discovered_devices)} 台设备")
                self.output_signal.emit("=" * 60)

                if discovered_devices:
                    self.output_signal.emit("\n设备列表:")
                    self.output_signal.emit("-" * 60)
                    self.output_signal.emit(f"{'IP 地址':<16} {'主机名':<30} {'MAC 地址':<18}")
                    self.output_signal.emit("-" * 60)

                    for device in sorted(discovered_devices, key=lambda x: ipaddress.ip_address(x['ip'])):
                        self.output_signal.emit(
                            f"{device['ip']:<16} {device['hostname']:<30} {device['mac']:<18}"
                        )
                else:
                    self.output_signal.emit("\n未发现在线设备")

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"网络扫描错误: {str(e)}")

    def get_mac(self, ip: str) -> str:
        """获取 IP 对应的 MAC 地址"""
        try:
            if sys.platform == "win32":
                # Windows: 使用 arp 命令
                result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True, encoding='gbk', errors='ignore')
                if result.returncode == 0:
                    # 解析 MAC 地址
                    match = re.search(r'([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})', result.stdout)
                    if match:
                        return match.group(1)
            else:
                # Linux/Mac: 使用 arp 命令
                result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
                if result.returncode == 0:
                    match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', result.stdout)
                    if match:
                        return match.group(1)
        except:
            pass
        return "未知"

    def stop(self):
        self._is_running = False
        self.terminate()


# ==================== 主窗口 ====================
class NetToolsMainWindow(QMainWindow):
    """NetTools 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetTools - 网络工具箱")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 设置样式
        self.setStyleSheet(DARK_THEME)

        # 初始化 UI
        self.init_ui()

        # 存储工作线程
        self.workers = {}

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("🌐 NetTools - 网络工具箱")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(version_label)

        main_layout.addLayout(title_layout)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 创建各个工具标签页
        self.create_ping_tab()
        self.create_port_scan_tab()
        self.create_dns_tab()
        self.create_ip_info_tab()
        self.create_traceroute_tab()
        self.create_speed_test_tab()
        self.create_whois_tab()
        self.create_network_scan_tab()

        main_layout.addWidget(self.tab_widget)

        # 状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("background-color: #111122; color: #b0b0b0;")

    def create_ping_tab(self):
        """创建 Ping 工具标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("Ping 设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("目标主机:"), 0, 0)
        self.ping_host_input = QLineEdit()
        self.ping_host_input.setPlaceholderText("输入 IP 地址或域名 (如: google.com)")
        input_layout.addWidget(self.ping_host_input, 0, 1, 1, 2)

        input_layout.addWidget(QLabel("数据包数量:"), 1, 0)
        self.ping_count_spin = QSpinBox()
        self.ping_count_spin.setRange(1, 100)
        self.ping_count_spin.setValue(4)
        input_layout.addWidget(self.ping_count_spin, 1, 1)

        input_layout.addWidget(QLabel("超时(秒):"), 1, 2)
        self.ping_timeout_spin = QSpinBox()
        self.ping_timeout_spin.setRange(1, 10)
        self.ping_timeout_spin.setValue(3)
        input_layout.addWidget(self.ping_timeout_spin, 1, 3)

        layout.addWidget(input_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.ping_start_btn = QPushButton("开始 Ping")
        self.ping_start_btn.clicked.connect(self.start_ping)
        button_layout.addWidget(self.ping_start_btn)

        self.ping_stop_btn = QPushButton("停止")
        self.ping_stop_btn.setObjectName("stopButton")
        self.ping_stop_btn.clicked.connect(lambda: self.stop_worker("ping"))
        self.ping_stop_btn.setEnabled(False)
        button_layout.addWidget(self.ping_stop_btn)

        button_layout.addStretch()

        self.ping_clear_btn = QPushButton("清空")
        self.ping_clear_btn.clicked.connect(lambda: self.ping_output.clear())
        button_layout.addWidget(self.ping_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.ping_output = QTextEdit()
        self.ping_output.setReadOnly(True)
        self.ping_output.setMinimumHeight(300)
        layout.addWidget(self.ping_output)

        self.tab_widget.addTab(tab, "🏓 Ping")

    def create_port_scan_tab(self):
        """创建端口扫描标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("端口扫描设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("目标主机:"), 0, 0)
        self.port_host_input = QLineEdit()
        self.port_host_input.setPlaceholderText("输入 IP 地址或域名")
        input_layout.addWidget(self.port_host_input, 0, 1, 1, 3)

        input_layout.addWidget(QLabel("起始端口:"), 1, 0)
        self.port_start_spin = QSpinBox()
        self.port_start_spin.setRange(1, 65535)
        self.port_start_spin.setValue(1)
        input_layout.addWidget(self.port_start_spin, 1, 1)

        input_layout.addWidget(QLabel("结束端口:"), 1, 2)
        self.port_end_spin = QSpinBox()
        self.port_end_spin.setRange(1, 65535)
        self.port_end_spin.setValue(1024)
        input_layout.addWidget(self.port_end_spin, 1, 3)

        input_layout.addWidget(QLabel("线程数:"), 2, 0)
        self.port_threads_spin = QSpinBox()
        self.port_threads_spin.setRange(10, 500)
        self.port_threads_spin.setValue(100)
        input_layout.addWidget(self.port_threads_spin, 2, 1)

        layout.addWidget(input_group)

        # 进度条
        self.port_progress = QProgressBar()
        self.port_progress.setValue(0)
        layout.addWidget(self.port_progress)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.port_start_btn = QPushButton("开始扫描")
        self.port_start_btn.clicked.connect(self.start_port_scan)
        button_layout.addWidget(self.port_start_btn)

        self.port_stop_btn = QPushButton("停止")
        self.port_stop_btn.setObjectName("stopButton")
        self.port_stop_btn.clicked.connect(lambda: self.stop_worker("port_scan"))
        self.port_stop_btn.setEnabled(False)
        button_layout.addWidget(self.port_stop_btn)

        button_layout.addStretch()

        self.port_clear_btn = QPushButton("清空")
        self.port_clear_btn.clicked.connect(lambda: self.port_output.clear())
        button_layout.addWidget(self.port_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.port_output = QTextEdit()
        self.port_output.setReadOnly(True)
        self.port_output.setMinimumHeight(300)
        layout.addWidget(self.port_output)

        self.tab_widget.addTab(tab, "🔌 端口扫描")

    def create_dns_tab(self):
        """创建 DNS 查询标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("DNS 查询设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("域名:"), 0, 0)
        self.dns_domain_input = QLineEdit()
        self.dns_domain_input.setPlaceholderText("输入域名 (如: google.com)")
        input_layout.addWidget(self.dns_domain_input, 0, 1, 1, 2)

        input_layout.addWidget(QLabel("记录类型:"), 1, 0)
        self.dns_type_combo = QComboBox()
        self.dns_type_combo.addItems(["A", "AAAA", "MX", "CNAME", "NS", "TXT", "SOA"])
        input_layout.addWidget(self.dns_type_combo, 1, 1)

        layout.addWidget(input_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.dns_start_btn = QPushButton("查询")
        self.dns_start_btn.clicked.connect(self.start_dns_lookup)
        button_layout.addWidget(self.dns_start_btn)

        button_layout.addStretch()

        self.dns_clear_btn = QPushButton("清空")
        self.dns_clear_btn.clicked.connect(lambda: self.dns_output.clear())
        button_layout.addWidget(self.dns_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.dns_output = QTextEdit()
        self.dns_output.setReadOnly(True)
        self.dns_output.setMinimumHeight(300)
        layout.addWidget(self.dns_output)

        self.tab_widget.addTab(tab, "🔍 DNS 查询")

    def create_ip_info_tab(self):
        """创建 IP 信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.ip_local_btn = QPushButton("获取本地 IP")
        self.ip_local_btn.clicked.connect(lambda: self.start_ip_info(True, False))
        button_layout.addWidget(self.ip_local_btn)

        self.ip_public_btn = QPushButton("获取公网 IP")
        self.ip_public_btn.clicked.connect(lambda: self.start_ip_info(False, True))
        button_layout.addWidget(self.ip_public_btn)

        self.ip_all_btn = QPushButton("获取全部信息")
        self.ip_all_btn.clicked.connect(lambda: self.start_ip_info(True, True))
        button_layout.addWidget(self.ip_all_btn)

        button_layout.addStretch()

        self.ip_clear_btn = QPushButton("清空")
        self.ip_clear_btn.clicked.connect(lambda: self.ip_output.clear())
        button_layout.addWidget(self.ip_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.ip_output = QTextEdit()
        self.ip_output.setReadOnly(True)
        self.ip_output.setMinimumHeight(400)
        layout.addWidget(self.ip_output)

        self.tab_widget.addTab(tab, "🌐 IP 信息")

    def create_traceroute_tab(self):
        """创建路由追踪标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("路由追踪设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("目标主机:"), 0, 0)
        self.trace_host_input = QLineEdit()
        self.trace_host_input.setPlaceholderText("输入 IP 地址或域名")
        input_layout.addWidget(self.trace_host_input, 0, 1, 1, 2)

        input_layout.addWidget(QLabel("最大跳数:"), 1, 0)
        self.trace_hops_spin = QSpinBox()
        self.trace_hops_spin.setRange(5, 100)
        self.trace_hops_spin.setValue(30)
        input_layout.addWidget(self.trace_hops_spin, 1, 1)

        layout.addWidget(input_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.trace_start_btn = QPushButton("开始追踪")
        self.trace_start_btn.clicked.connect(self.start_traceroute)
        button_layout.addWidget(self.trace_start_btn)

        self.trace_stop_btn = QPushButton("停止")
        self.trace_stop_btn.setObjectName("stopButton")
        self.trace_stop_btn.clicked.connect(lambda: self.stop_worker("traceroute"))
        self.trace_stop_btn.setEnabled(False)
        button_layout.addWidget(self.trace_stop_btn)

        button_layout.addStretch()

        self.trace_clear_btn = QPushButton("清空")
        self.trace_clear_btn.clicked.connect(lambda: self.trace_output.clear())
        button_layout.addWidget(self.trace_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.trace_output = QTextEdit()
        self.trace_output.setReadOnly(True)
        self.trace_output.setMinimumHeight(300)
        layout.addWidget(self.trace_output)

        self.tab_widget.addTab(tab, "🛤️ 路由追踪")

    def create_speed_test_tab(self):
        """创建网速测试标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 说明
        info_label = QLabel("网速测试将测试您的网络下载、上传速度和延迟。")
        info_label.setStyleSheet("color: #888; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)

        # 进度条
        self.speed_progress = QProgressBar()
        self.speed_progress.setValue(0)
        layout.addWidget(self.speed_progress)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.speed_start_btn = QPushButton("开始测试")
        self.speed_start_btn.clicked.connect(self.start_speed_test)
        button_layout.addWidget(self.speed_start_btn)

        self.speed_stop_btn = QPushButton("停止")
        self.speed_stop_btn.setObjectName("stopButton")
        self.speed_stop_btn.clicked.connect(lambda: self.stop_worker("speed_test"))
        self.speed_stop_btn.setEnabled(False)
        button_layout.addWidget(self.speed_stop_btn)

        button_layout.addStretch()

        self.speed_clear_btn = QPushButton("清空")
        self.speed_clear_btn.clicked.connect(lambda: self.speed_output.clear())
        button_layout.addWidget(self.speed_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.speed_output = QTextEdit()
        self.speed_output.setReadOnly(True)
        self.speed_output.setMinimumHeight(300)
        layout.addWidget(self.speed_output)

        self.tab_widget.addTab(tab, "⚡ 网速测试")

    def create_whois_tab(self):
        """创建 Whois 查询标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("Whois 查询设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("域名:"), 0, 0)
        self.whois_domain_input = QLineEdit()
        self.whois_domain_input.setPlaceholderText("输入域名 (如: google.com)")
        input_layout.addWidget(self.whois_domain_input, 0, 1, 1, 2)

        layout.addWidget(input_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.whois_start_btn = QPushButton("查询")
        self.whois_start_btn.clicked.connect(self.start_whois_lookup)
        button_layout.addWidget(self.whois_start_btn)

        button_layout.addStretch()

        self.whois_clear_btn = QPushButton("清空")
        self.whois_clear_btn.clicked.connect(lambda: self.whois_output.clear())
        button_layout.addWidget(self.whois_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.whois_output = QTextEdit()
        self.whois_output.setReadOnly(True)
        self.whois_output.setMinimumHeight(300)
        layout.addWidget(self.whois_output)

        self.tab_widget.addTab(tab, "📋 Whois 查询")

    def create_network_scan_tab(self):
        """创建网络扫描标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("网络扫描设置")
        input_layout = QGridLayout(input_group)

        input_layout.addWidget(QLabel("网络地址:"), 0, 0)
        self.scan_network_input = QLineEdit()
        self.scan_network_input.setPlaceholderText("输入网络地址 (如: 192.168.1.0/24)")
        self.scan_network_input.setText("192.168.1.0/24")
        input_layout.addWidget(self.scan_network_input, 0, 1, 1, 2)

        input_layout.addWidget(QLabel("超时(秒):"), 1, 0)
        self.scan_timeout_spin = QSpinBox()
        self.scan_timeout_spin.setRange(1, 5)
        self.scan_timeout_spin.setValue(1)
        self.scan_timeout_spin.setSingleStep(1)
        input_layout.addWidget(self.scan_timeout_spin, 1, 1)

        layout.addWidget(input_group)

        # 进度条
        self.scan_progress = QProgressBar()
        self.scan_progress.setValue(0)
        layout.addWidget(self.scan_progress)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.scan_start_btn = QPushButton("开始扫描")
        self.scan_start_btn.clicked.connect(self.start_network_scan)
        button_layout.addWidget(self.scan_start_btn)

        self.scan_stop_btn = QPushButton("停止")
        self.scan_stop_btn.setObjectName("stopButton")
        self.scan_stop_btn.clicked.connect(lambda: self.stop_worker("network_scan"))
        self.scan_stop_btn.setEnabled(False)
        button_layout.addWidget(self.scan_stop_btn)

        button_layout.addStretch()

        self.scan_clear_btn = QPushButton("清空")
        self.scan_clear_btn.clicked.connect(lambda: self.scan_output.clear())
        button_layout.addWidget(self.scan_clear_btn)

        layout.addLayout(button_layout)

        # 输出区域
        self.scan_output = QTextEdit()
        self.scan_output.setReadOnly(True)
        self.scan_output.setMinimumHeight(300)
        layout.addWidget(self.scan_output)

        self.tab_widget.addTab(tab, "📡 网络扫描")

    # ==================== 工具方法 ====================
    def start_worker(self, name: str, worker: QThread, start_btn: QPushButton, stop_btn: QPushButton):
        """启动工作线程"""
        if name in self.workers and self.workers[name].isRunning():
            return

        self.workers[name] = worker
        start_btn.setEnabled(False)
        stop_btn.setEnabled(True)
        self.statusBar().showMessage(f"正在执行 {name}...")

        worker.finished_signal.connect(lambda: self.worker_finished(name, start_btn, stop_btn))
        worker.error_signal.connect(lambda msg: self.worker_error(name, msg, start_btn, stop_btn))
        worker.start()

    def stop_worker(self, name: str):
        """停止工作线程"""
        if name in self.workers and self.workers[name].isRunning():
            self.workers[name].stop()
            self.statusBar().showMessage(f"已停止 {name}")

    def worker_finished(self, name: str, start_btn: QPushButton, stop_btn: QPushButton):
        """工作线程完成"""
        start_btn.setEnabled(True)
        stop_btn.setEnabled(False)
        self.statusBar().showMessage(f"{name} 完成")

    def worker_error(self, name: str, msg: str, start_btn: QPushButton, stop_btn: QPushButton):
        """工作线程错误"""
        start_btn.setEnabled(True)
        stop_btn.setEnabled(False)
        self.statusBar().showMessage(f"{name} 错误")
        QMessageBox.warning(self, "错误", msg)

    # ==================== Ping 工具 ====================
    def start_ping(self):
        """开始 Ping"""
        host = self.ping_host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "警告", "请输入目标主机地址")
            return

        count = self.ping_count_spin.value()
        timeout = self.ping_timeout_spin.value()

        worker = PingWorker(host, count, timeout)
        worker.output_signal.connect(lambda msg: self.append_output(self.ping_output, msg))
        worker.error_signal.connect(lambda msg: self.append_output(self.ping_output, f"\n错误: {msg}"))

        self.start_worker("ping", worker, self.ping_start_btn, self.ping_stop_btn)

    # ==================== 端口扫描 ====================
    def start_port_scan(self):
        """开始端口扫描"""
        host = self.port_host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "警告", "请输入目标主机地址")
            return

        start_port = self.port_start_spin.value()
        end_port = self.port_end_spin.value()
        threads = self.port_threads_spin.value()

        if start_port > end_port:
            QMessageBox.warning(self, "警告", "起始端口不能大于结束端口")
            return

        worker = PortScanWorker(host, start_port, end_port, threads)
        worker.output_signal.connect(lambda msg: self.append_output(self.port_output, msg))
        worker.progress_signal.connect(self.port_progress.setValue)

        self.start_worker("port_scan", worker, self.port_start_btn, self.port_stop_btn)

    # ==================== DNS 查询 ====================
    def start_dns_lookup(self):
        """开始 DNS 查询"""
        domain = self.dns_domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "警告", "请输入域名")
            return

        record_type = self.dns_type_combo.currentText()

        worker = DNSLookupWorker(domain, record_type)
        worker.output_signal.connect(lambda msg: self.append_output(self.dns_output, msg))

        self.start_worker("dns", worker, self.dns_start_btn, self.dns_start_btn)

    # ==================== IP 信息 ====================
    def start_ip_info(self, get_local: bool, get_public: bool):
        """开始获取 IP 信息"""
        worker = IPInfoWorker(get_local, get_public)
        worker.output_signal.connect(lambda msg: self.append_output(self.ip_output, msg))

        self.start_worker("ip_info", worker, self.ip_all_btn, self.ip_all_btn)

    # ==================== 路由追踪 ====================
    def start_traceroute(self):
        """开始路由追踪"""
        host = self.trace_host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "警告", "请输入目标主机地址")
            return

        max_hops = self.trace_hops_spin.value()

        worker = TracerouteWorker(host, max_hops)
        worker.output_signal.connect(lambda msg: self.append_output(self.trace_output, msg))

        self.start_worker("traceroute", worker, self.trace_start_btn, self.trace_stop_btn)

    # ==================== 网速测试 ====================
    def start_speed_test(self):
        """开始网速测试"""
        worker = SpeedTestWorker()
        worker.output_signal.connect(lambda msg: self.append_output(self.speed_output, msg))
        worker.progress_signal.connect(self.speed_progress.setValue)

        self.start_worker("speed_test", worker, self.speed_start_btn, self.speed_stop_btn)

    # ==================== Whois 查询 ====================
    def start_whois_lookup(self):
        """开始 Whois 查询"""
        domain = self.whois_domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "警告", "请输入域名")
            return

        worker = WhoisWorker(domain)
        worker.output_signal.connect(lambda msg: self.append_output(self.whois_output, msg))

        self.start_worker("whois", worker, self.whois_start_btn, self.whois_start_btn)

    # ==================== 网络扫描 ====================
    def start_network_scan(self):
        """开始网络扫描"""
        network = self.scan_network_input.text().strip()
        if not network:
            QMessageBox.warning(self, "警告", "请输入网络地址")
            return

        timeout = self.scan_timeout_spin.value()

        worker = NetworkScanWorker(network, timeout)
        worker.output_signal.connect(lambda msg: self.append_output(self.scan_output, msg))
        worker.progress_signal.connect(self.scan_progress.setValue)

        self.start_worker("network_scan", worker, self.scan_start_btn, self.scan_stop_btn)

    # ==================== 辅助方法 ====================
    def append_output(self, text_edit: QTextEdit, message: str):
        """追加输出到文本框"""
        text_edit.append(message)
        # 滚动到底部
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible()


# ==================== 主函数 ====================
def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("NetTools")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NetTools")

    # 创建主窗口
    window = NetToolsMainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
