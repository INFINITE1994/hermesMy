#!/usr/bin/env python3
"""
系统信息查看器 - System Information Viewer
基于 PyQt6 的专业系统信息查看工具
"""

import sys
import os
import platform
import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QFileDialog,
    QTabWidget, QGridLayout, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter, QBrush

import psutil

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


class SystemInfoCollector(QThread):
    """后台线程收集系统信息"""
    finished = pyqtSignal(dict)
    
    def run(self):
        info = {}
        try:
            info['os'] = self._get_os_info()
            info['cpu'] = self._get_cpu_info()
            info['memory'] = self._get_memory_info()
            info['disk'] = self._get_disk_info()
            info['gpu'] = self._get_gpu_info()
            info['network'] = self._get_network_info()
            info['motherboard'] = self._get_motherboard_info()
        except Exception as e:
            info['error'] = str(e)
        self.finished.emit(info)
    
    def _get_os_info(self) -> dict:
        """获取操作系统信息"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            try:
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
            except:
                product_name = platform.system()
            try:
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
            except:
                build = platform.version()
            try:
                display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            except:
                display_version = ""
            winreg.CloseKey(key)
        except:
            product_name = platform.system()
            build = platform.version()
            display_version = ""
        
        return {
            '系统名称': product_name,
            '版本号': platform.version(),
            '构建号': build,
            '系统架构': platform.architecture()[0],
            '计算机名': platform.node(),
            '发行版本': display_version,
            '系统位数': platform.machine()
        }
    
    def _get_cpu_info(self) -> dict:
        """获取CPU信息"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
        except:
            cpu_name = platform.processor()
        
        freq = psutil.cpu_freq()
        
        return {
            'CPU 型号': cpu_name,
            '物理核心数': psutil.cpu_count(logical=False),
            '逻辑核心数': psutil.cpu_count(logical=True),
            '当前频率': f"{freq.current:.2f} MHz" if freq else "未知",
            '最大频率': f"{freq.max:.2f} MHz" if freq else "未知",
            '最小频率': f"{freq.min:.2f} MHz" if freq else "未知",
            'CPU 使用率': f"{psutil.cpu_percent(interval=1)}%"
        }
    
    def _get_memory_info(self) -> dict:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        
        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'memorychip', 'get', 'manufacturer,speed,capacity,devicelocator'],
                capture_output=True, shell=True, encoding='mbcs', errors='replace'
            )
            lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and 'Capacity' not in l]
            slots = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    slots.append({
                        '制造商': parts[0] if parts[0] != '0' else '未知',
                        '容量': f"{int(parts[1]) / (1024**3):.0f} GB" if parts[1].isdigit() else parts[1],
                        '速度': f"{parts[2]} MHz" if parts[2].isdigit() else parts[2]
                    })
        except:
            slots = []
        
        return {
            '总内存': f"{mem.total / (1024**3):.2f} GB",
            '已使用': f"{mem.used / (1024**3):.2f} GB",
            '可用内存': f"{mem.available / (1024**3):.2f} GB",
            '使用率': f"{mem.percent}%",
            '内存插槽数': len(slots) if slots else '未知',
            '内存条详情': slots
        }
    
    def _get_disk_info(self) -> list:
        """获取磁盘信息"""
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                
                try:
                    import subprocess
                    result = subprocess.run(
                        ['wmic', 'diskdrive', 'get', 'model,size,mediatype'],
                        capture_output=True, shell=True, encoding='mbcs', errors='replace'
                    )
                    disk_model = '未知型号'
                    disk_type = '未知'
                    for line in result.stdout.split('\n'):
                        if part.device[:2] in line:
                            parts = line.strip().split()
                            if parts:
                                disk_model = parts[0]
                            break
                except:
                    disk_model = '未知型号'
                    disk_type = '未知'
                
                disks.append({
                    '设备': part.device,
                    '挂载点': part.mountpoint,
                    '文件系统': part.fstype,
                    '总容量': f"{usage.total / (1024**3):.2f} GB",
                    '已使用': f"{usage.used / (1024**3):.2f} GB",
                    '可用空间': f"{usage.free / (1024**3):.2f} GB",
                    '使用率': f"{usage.percent}%",
                    '型号': disk_model
                })
            except PermissionError:
                continue
        return disks
    
    def _get_gpu_info(self) -> list:
        """获取GPU信息"""
        gpus = []
        
        if HAS_GPUTIL:
            try:
                for gpu in GPUtil.getGPUs():
                    gpus.append({
                        'GPU 名称': gpu.name,
                        '显存总量': f"{gpu.memoryTotal:.0f} MB",
                        '已用显存': f"{gpu.memoryUsed:.0f} MB",
                        '可用显存': f"{gpu.memoryFree:.0f} MB",
                        '温度': f"{gpu.temperature}°C" if gpu.temperature else '未知',
                        '负载': f"{gpu.load * 100:.1f}%" if gpu.load else '未知'
                    })
            except:
                pass
        
        if not gpus:
            try:
                import subprocess
                result = subprocess.run(
                    ['wmic', 'path', 'win32_videocontroller', 'get', 'name,adapterram,driverversion'],
                    capture_output=True, shell=True, encoding='mbcs', errors='replace'
                )
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        parts = line.strip().split()
                        if parts:
                            gpus.append({
                                'GPU 名称': parts[0],
                                '显存': '未知',
                                '驱动版本': '未知'
                            })
            except:
                gpus.append({'GPU 名称': '未检测到GPU'})
        
        return gpus
    
    def _get_network_info(self) -> list:
        """获取网络信息"""
        interfaces = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for name, addr_list in addrs.items():
            interface = {
                '名称': name,
                '状态': '已连接' if stats.get(name, None) and stats[name].isup else '未连接',
                'IPv4': [],
                'IPv6': [],
                'MAC': ''
            }
            
            for addr in addr_list:
                if addr.family.name == 'AF_INET':
                    interface['IPv4'].append(addr.address)
                elif addr.family.name == 'AF_INET6':
                    interface['IPv6'].append(addr.address)
                elif addr.family.name == 'AF_PACKET':
                    interface['MAC'] = addr.address
            
            interfaces.append(interface)
        
        return interfaces
    
    def _get_motherboard_info(self) -> dict:
        """获取主板信息"""
        mb_info = {}
        
        try:
            import subprocess
            
            result = subprocess.run(
                ['wmic', 'baseboard', 'get', 'manufacturer,product,serialnumber'],
                capture_output=True, shell=True, encoding='mbcs', errors='replace'
            )
            lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and 'Manufacturer' not in l]
            if lines:
                parts = lines[0].split(None, 2)
                mb_info['主板制造商'] = parts[0] if parts else '未知'
                mb_info['主板型号'] = parts[1] if len(parts) > 1 else '未知'
                mb_info['序列号'] = parts[2] if len(parts) > 2 else '未知'
            
            result = subprocess.run(
                ['wmic', 'bios', 'get', 'manufacturer,smbiosbiosversion,releasedate'],
                capture_output=True, shell=True, encoding='mbcs', errors='replace'
            )
            lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and 'Manufacturer' not in l]
            if lines:
                parts = lines[0].split(None, 2)
                mb_info['BIOS 制造商'] = parts[0] if parts else '未知'
                mb_info['BIOS 版本'] = parts[1] if len(parts) > 1 else '未知'
                mb_info['BIOS 日期'] = parts[2] if len(parts) > 2 else '未知'
        except:
            mb_info = {
                '主板制造商': '未知',
                '主板型号': '未知',
                'BIOS 制造商': '未知',
                'BIOS 版本': '未知'
            }
        
        return mb_info


class GradientFrame(QFrame):
    """渐变色框架"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor('#667eea'))
        gradient.setColorAt(1, QColor('#764ba2'))
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()


class InfoCard(QFrame):
    """信息卡片组件"""
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #111122;
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
                border: 1px solid #2a2a3a;
            }
            QFrame:hover {
                border: 1px solid #667eea;
            }
        """)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        
        self.title_layout = QHBoxLayout()
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 24px; color: #667eea;")
        self.icon_label.setFixedWidth(30)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                font-size: 16px;
                font-weight: bold;
                font-family: "Microsoft YaHei", sans-serif;
            }
        """)
        
        self.title_layout.addWidget(self.icon_label)
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        
        self.layout.addLayout(self.title_layout)
        
        self.content_layout = QGridLayout()
        self.content_layout.setSpacing(6)
        self.content_layout.setColumnStretch(1, 1)
        self.layout.addLayout(self.content_layout)
        
        self.row = 0
    
    def add_info(self, label: str, value: str):
        """添加信息项"""
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("""
            QLabel {
                color: #8888aa;
                font-size: 12px;
                font-family: "Microsoft YaHei", sans-serif;
            }
        """)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        val = QLabel(str(value))
        val.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-family: "Microsoft YaHei", sans-serif;
            }
        """)
        val.setWordWrap(True)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.content_layout.addWidget(lbl, self.row, 0)
        self.content_layout.addWidget(val, self.row, 1)
        self.row += 1
    
    def add_spacer(self):
        self.content_layout.setRowStretch(self.row, 1)


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.system_info = {}
        self.init_ui()
        self.collect_info()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('系统信息查看器')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header = GradientFrame()
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🖥️ 系统信息查看器")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: "Microsoft YaHei", sans-serif;
                padding: 20px;
            }
        """)
        
        self.export_btn = QPushButton("📥 导出报告")
        self.export_btn.setFixedSize(120, 40)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                font-size: 14px;
                font-family: "Microsoft YaHei", sans-serif;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.export_btn.clicked.connect(self.export_report)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedSize(100, 40)
        refresh_btn.setStyleSheet(self.export_btn.styleSheet())
        refresh_btn.clicked.connect(self.collect_info)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(self.export_btn)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        main_layout.addWidget(header)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #0a0a0a;
            }
            QTabBar::tab {
                background-color: #111122;
                color: #8888aa;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 8px 8px 0 0;
                font-size: 13px;
                font-family: "Microsoft YaHei", sans-serif;
                font-weight: bold;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a2e;
                color: #667eea;
                border-bottom: 3px solid #667eea;
            }
            QTabBar::tab:hover {
                background-color: #1a1a2e;
                color: #8888ff;
            }
        """)
        
        self.os_tab = self.create_tab("操作系统", "💻")
        self.cpu_tab = self.create_tab("处理器", "⚡")
        self.memory_tab = self.create_tab("内存", "🧠")
        self.disk_tab = self.create_tab("存储", "💾")
        self.gpu_tab = self.create_tab("显卡", "🎮")
        self.network_tab = self.create_tab("网络", "🌐")
        self.mb_tab = self.create_tab("主板", "🔧")
        
        self.tab_widget.addTab(self.os_tab, "操作系统")
        self.tab_widget.addTab(self.cpu_tab, "处理器")
        self.tab_widget.addTab(self.memory_tab, "内存")
        self.tab_widget.addTab(self.disk_tab, "存储")
        self.tab_widget.addTab(self.gpu_tab, "显卡")
        self.tab_widget.addTab(self.network_tab, "网络")
        self.tab_widget.addTab(self.mb_tab, "主板")
        
        main_layout.addWidget(self.tab_widget)
        
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #111122;
                color: #8888aa;
                font-size: 12px;
                font-family: "Microsoft YaHei", sans-serif;
                padding: 5px;
            }
        """)
        self.statusBar().showMessage("正在收集系统信息...")
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
            }
            QScrollArea {
                border: none;
                background-color: #0a0a0a;
            }
            QWidget {
                background-color: #0a0a0a;
            }
        """)
    
    def create_tab(self, title: str, icon: str) -> QWidget:
        """创建标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0a0a0a;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #0a0a0a;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #333355;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #667eea;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #0a0a0a;")
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll)
        tab.scroll_widget = scroll_widget
        
        return tab
    
    def collect_info(self):
        """收集系统信息"""
        self.statusBar().showMessage("正在收集系统信息...")
        self.export_btn.setEnabled(False)
        
        self.collector = SystemInfoCollector()
        self.collector.finished.connect(self.on_info_collected)
        self.collector.start()
    
    def on_info_collected(self, info: dict):
        """系统信息收集完成"""
        self.system_info = info
        self.export_btn.setEnabled(True)
        
        if 'error' in info:
            self.statusBar().showMessage(f"收集信息时出错: {info['error']}")
            return
        
        self.update_os_tab(info.get('os', {}))
        self.update_cpu_tab(info.get('cpu', {}))
        self.update_memory_tab(info.get('memory', {}))
        self.update_disk_tab(info.get('disk', []))
        self.update_gpu_tab(info.get('gpu', []))
        self.update_network_tab(info.get('network', []))
        self.update_mb_tab(info.get('motherboard', {}))
        
        self.statusBar().showMessage(f"系统信息收集完成 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def update_os_tab(self, info: dict):
        """更新操作系统标签页"""
        self._clear_tab(self.os_tab)
        card = InfoCard("操作系统信息", "💻")
        for key, value in info.items():
            card.add_info(key, value)
        card.add_spacer()
        self.os_tab.scroll_widget.layout().addWidget(card)
        self.os_tab.scroll_widget.layout().addStretch()
    
    def update_cpu_tab(self, info: dict):
        """更新CPU标签页"""
        self._clear_tab(self.cpu_tab)
        card = InfoCard("处理器信息", "⚡")
        for key, value in info.items():
            card.add_info(key, value)
        card.add_spacer()
        self.cpu_tab.scroll_widget.layout().addWidget(card)
        self.cpu_tab.scroll_widget.layout().addStretch()
    
    def update_memory_tab(self, info: dict):
        """更新内存标签页"""
        self._clear_tab(self.memory_tab)
        
        card = InfoCard("内存信息", "🧠")
        for key, value in info.items():
            if key != '内存条详情':
                card.add_info(key, value)
        card.add_spacer()
        self.memory_tab.scroll_widget.layout().addWidget(card)
        
        if '内存条详情' in info and info['内存条详情']:
            for i, slot in enumerate(info['内存条详情'], 1):
                slot_card = InfoCard(f"内存插槽 {i}", "📦")
                for k, v in slot.items():
                    slot_card.add_info(k, v)
                slot_card.add_spacer()
                self.memory_tab.scroll_widget.layout().addWidget(slot_card)
        
        self.memory_tab.scroll_widget.layout().addStretch()
    
    def update_disk_tab(self, disks: list):
        """更新磁盘标签页"""
        self._clear_tab(self.disk_tab)
        for i, disk in enumerate(disks, 1):
            card = InfoCard(f"磁盘 {i}: {disk.get('设备', '')}", "💾")
            for key, value in disk.items():
                card.add_info(key, value)
            card.add_spacer()
            self.disk_tab.scroll_widget.layout().addWidget(card)
        self.disk_tab.scroll_widget.layout().addStretch()
    
    def update_gpu_tab(self, gpus: list):
        """更新GPU标签页"""
        self._clear_tab(self.gpu_tab)
        for i, gpu in enumerate(gpus, 1):
            card = InfoCard(f"显卡 {i}", "🎮")
            for key, value in gpu.items():
                card.add_info(key, value)
            card.add_spacer()
            self.gpu_tab.scroll_widget.layout().addWidget(card)
        self.gpu_tab.scroll_widget.layout().addStretch()
    
    def update_network_tab(self, interfaces: list):
        """更新网络标签页"""
        self._clear_tab(self.network_tab)
        for iface in interfaces:
            card = InfoCard(f"网络适配器: {iface.get('名称', '')}", "🌐")
            card.add_info('状态', iface.get('状态', ''))
            card.add_info('MAC 地址', iface.get('MAC', ''))
            for ip in iface.get('IPv4', []):
                card.add_info('IPv4', ip)
            for ip in iface.get('IPv6', []):
                card.add_info('IPv6', ip)
            card.add_spacer()
            self.network_tab.scroll_widget.layout().addWidget(card)
        self.network_tab.scroll_widget.layout().addStretch()
    
    def update_mb_tab(self, info: dict):
        """更新主板标签页"""
        self._clear_tab(self.mb_tab)
        card = InfoCard("主板信息", "🔧")
        for key, value in info.items():
            card.add_info(key, value)
        card.add_spacer()
        self.mb_tab.scroll_widget.layout().addWidget(card)
        self.mb_tab.scroll_widget.layout().addStretch()
    
    def _clear_tab(self, tab: QWidget):
        """清空标签页内容"""
        layout = tab.scroll_widget.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def export_report(self):
        """导出报告"""
        file_path, file_type = QFileDialog.getSaveFileName(
            self,
            "导出系统信息报告",
            f"system_info_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "HTML 文件 (*.html);;文本文件 (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.html'):
                self.export_html(file_path)
            else:
                if not file_path.endswith('.txt'):
                    file_path += '.txt'
                self.export_txt(file_path)
            
            self.statusBar().showMessage(f"报告已导出到: {file_path}")
            QMessageBox.information(self, "导出成功", f"系统信息报告已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出报告时出错:\n{str(e)}")
    
    def export_html(self, file_path: str):
        """导出HTML报告"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统信息报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: "Microsoft YaHei", sans-serif; 
            background: #0a0a0a; 
            color: #fff; 
            padding: 20px; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
        }
        .header h1 { font-size: 28px; }
        .header p { opacity: 0.9; margin-top: 5px; }
        .card { 
            background: #111122; 
            border-radius: 12px; 
            padding: 20px; 
            margin-bottom: 15px; 
            border: 1px solid #2a2a3a; 
        }
        .card h2 { 
            color: #667eea; 
            font-size: 18px; 
            margin-bottom: 15px; 
            padding-bottom: 10px; 
            border-bottom: 1px solid #2a2a3a; 
        }
        .info-row { 
            display: flex; 
            padding: 8px 0; 
            border-bottom: 1px solid #1a1a2e; 
        }
        .info-label { 
            width: 150px; 
            color: #8888aa; 
            flex-shrink: 0; 
        }
        .info-value { 
            color: #fff; 
            flex: 1; 
            word-break: break-all; 
        }
        .info-row:last-child { border-bottom: none; }
        .footer { 
            text-align: center; 
            color: #666; 
            margin-top: 30px; 
            font-size: 12px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥️ 系统信息报告</h1>
        <p>生成时间: """ + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
"""
        
        for section, data in self.system_info.items():
            if section == 'error':
                continue
            
            titles = {
                'os': '操作系统信息',
                'cpu': '处理器信息',
                'memory': '内存信息',
                'disk': '磁盘信息',
                'gpu': '显卡信息',
                'network': '网络信息',
                'motherboard': '主板信息'
            }
            
            html += f'    <div class="card">\n'
            html += f'        <h2>{titles.get(section, section)}</h2>\n'
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == '内存条详情':
                        continue
                    html += f'        <div class="info-row">\n'
                    html += f'            <div class="info-label">{key}</div>\n'
                    html += f'            <div class="info-value">{value}</div>\n'
                    html += f'        </div>\n'
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            html += f'        <div class="info-row">\n'
                            html += f'            <div class="info-label">{key}</div>\n'
                            html += f'            <div class="info-value">{value}</div>\n'
                            html += f'        </div>\n'
                        if i < len(data):
                            html += f'        <hr style="border-color: #2a2a3a; margin: 15px 0;">\n'
            
            html += '    </div>\n'
        
        html += """
    <div class="footer">
        <p>系统信息查看器 - 自动生成报告</p>
    </div>
</body>
</html>"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def export_txt(self, file_path: str):
        """导出TXT报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("系统信息报告")
        lines.append(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        
        titles = {
            'os': '操作系统信息',
            'cpu': '处理器信息',
            'memory': '内存信息',
            'disk': '磁盘信息',
            'gpu': '显卡信息',
            'network': '网络信息',
            'motherboard': '主板信息'
        }
        
        for section, data in self.system_info.items():
            if section == 'error':
                continue
            
            lines.append("-" * 60)
            lines.append(f"【{titles.get(section, section)}】")
            lines.append("-" * 60)
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == '内存条详情':
                        if value:
                            lines.append("")
                            lines.append("内存条详情:")
                            for i, slot in enumerate(value, 1):
                                lines.append(f"  插槽 {i}:")
                                for k, v in slot.items():
                                    lines.append(f"    {k}: {v}")
                        continue
                    lines.append(f"{key}: {value}")
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    lines.append(f"\n[项目 {i}]")
                    if isinstance(item, dict):
                        for key, value in item.items():
                            lines.append(f"  {key}: {value}")
            
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("报告生成完毕")
        lines.append("=" * 60)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor('#0a0a0a'))
    palette.setColor(QPalette.ColorRole.WindowText, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.Base, QColor('#111122'))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor('#1a1a2e'))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor('#111122'))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.Text, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.Button, QColor('#111122'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.BrightText, QColor('#667eea'))
    palette.setColor(QPalette.ColorRole.Link, QColor('#667eea'))
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#667eea'))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
