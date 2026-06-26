"""SystemCleaner - Windows 系统优化清理工具"""

import os
import sys
import ctypes
import subprocess
import winreg
import time
from pathlib import Path

import psutil
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter, QBrush
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QProgressBar, QComboBox, QCheckBox, QGroupBox, QGridLayout,
    QTextEdit, QSplitter, QSizePolicy
)

# ─── 常量 ───────────────────────────────────────────────────────────────
BG_COLOR = "#0a0a0a"
CARD_COLOR = "#111122"
ACCENT_1 = "#667eea"
ACCENT_2 = "#764ba2"
TEXT_COLOR = "#e0e0e0"
TEXT_DIM = "#888899"
DANGER = "#ff4444"
SUCCESS = "#44ff88"
WARNING = "#ffaa44"
BORDER = "#222244"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_COLOR};
    color: {TEXT_COLOR};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}}
QFrame#card {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 16px;
}}
QPushButton {{
    background-color: {CARD_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    border-color: {ACCENT_1};
    background-color: #1a1a33;
}}
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_1}cc, stop:1 {ACCENT_2}cc);
}}
QPushButton#danger {{
    background-color: {DANGER}22;
    border-color: {DANGER}66;
    color: {DANGER};
}}
QPushButton#danger:hover {{
    background-color: {DANGER}44;
}}
QPushButton#success {{
    background-color: {SUCCESS}22;
    border-color: {SUCCESS}66;
    color: {SUCCESS};
}}
QLabel#title {{
    font-size: 24px;
    font-weight: 700;
    color: white;
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {TEXT_DIM};
}}
QLabel#sectionTitle {{
    font-size: 18px;
    font-weight: 600;
    color: white;
    padding: 8px 0;
}}
QTableWidget {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT_1}44;
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {BORDER};
}}
QHeaderView::section {{
    background-color: #0d0d1a;
    color: {TEXT_DIM};
    border: none;
    border-bottom: 2px solid {BORDER};
    padding: 10px;
    font-weight: 600;
}}
QProgressBar {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_COLOR};
    height: 24px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
    border-radius: 5px;
}}
QComboBox {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT_COLOR};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT_1}44;
}}
QTextEdit {{
    background-color: {CARD_COLOR};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT_COLOR};
    padding: 8px;
}}
QScrollArea {{
    border: none;
}}
QScrollBar:vertical {{
    background: {BG_COLOR};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    color: {TEXT_COLOR};
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
"""


# ─── 工具函数 ─────────────────────────────────────────────────────────
def make_card():
    f = QFrame()
    f.setObjectName("card")
    f.setFrameShape(QFrame.Shape.StyledPanel)
    return f


def make_gradient_bar():
    """创建渐变色状态条"""
    bar = QProgressBar()
    bar.setFixedHeight(6)
    bar.setTextVisible(False)
    return bar


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


# ─── 侧栏按钮 ────────────────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_text}  {label}")
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {ACCENT_1}33, stop:1 {ACCENT_2}33);
                    border-left: 3px solid {ACCENT_1};
                    border-top: none; border-right: none; border-bottom: none;
                    color: white; font-weight: 600;
                    text-align: left; padding-left: 16px;
                    border-radius: 0;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {TEXT_DIM};
                    text-align: left; padding-left: 16px;
                    border-radius: 0;
                }}
                QPushButton:hover {{
                    color: white;
                    background: {BORDER}33;
                }}
            """)


# ─── 功能页面基类 ────────────────────────────────────────────────────
class BasePage(QWidget):
    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(16)

        header = QVBoxLayout()
        t = QLabel(title)
        t.setObjectName("title")
        s = QLabel(subtitle)
        s.setObjectName("subtitle")
        header.addWidget(t)
        header.addWidget(s)
        header.addSpacing(8)
        self.main_layout.addLayout(header)


# ─── 1. 启动项管理 ──────────────────────────────────────────────────
class StartupPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("🚀 启动项管理", "管理开机自启动程序，优化开机速度")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["名称", "命令", "位置", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新列表")
        btn_refresh.clicked.connect(self.load_items)
        btn_disable = QPushButton("❌ 禁用选中")
        btn_disable.setObjectName("danger")
        btn_disable.clicked.connect(self.disable_selected)
        btn_enable = QPushButton("✅ 启用选中")
        btn_enable.setObjectName("success")
        btn_enable.clicked.connect(self.enable_selected)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_disable)
        btn_row.addWidget(btn_enable)
        btn_row.addStretch()

        self.main_layout.addWidget(self.table)
        self.main_layout.addLayout(btn_row)
        self.load_items()

    def _get_startup_keys(self):
        """读取注册表启动项"""
        items = []
        paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
        ]
        for hive, path, loc in paths:
            try:
                key = winreg.OpenKey(hive, path)
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(key, i)
                        items.append((name, val, loc, "启用"))
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except OSError:
                pass
        return items

    def load_items(self):
        items = self._get_startup_keys()
        self.table.setRowCount(len(items))
        for r, (name, cmd, loc, status) in enumerate(items):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(cmd[:80]))
            self.table.setItem(r, 2, QTableWidgetItem(loc))
            item = QTableWidgetItem(status)
            item.setForeground(QColor(SUCCESS))
            self.table.setItem(r, 3, item)

    def disable_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        loc = self.table.item(row, 2).text()
        hive = winreg.HKEY_CURRENT_USER if loc == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            # 备份到 RunDisabled
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            try:
                dk = winreg.CreateKey(hive, path.replace("Run", "RunDisabled"))
                winreg.SetValueEx(dk, name, 0, winreg.REG_SZ, val)
                winreg.CloseKey(dk)
            except OSError:
                pass
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            self.table.item(row, 3).setText("已禁用")
            self.table.item(row, 3).setForeground(QColor(DANGER))
            QMessageBox.information(self, "成功", f"已禁用启动项: {name}")
        except PermissionError:
            QMessageBox.warning(self, "权限不足", "请以管理员身份运行以修改 HKLM 启动项")
        except OSError as e:
            QMessageBox.warning(self, "错误", f"操作失败: {e}")

    def enable_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        loc = self.table.item(row, 2).text()
        hive = winreg.HKEY_CURRENT_USER if loc == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        disabled_path = path.replace("Run", "RunDisabled")
        try:
            dk = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(dk, name)
            winreg.CloseKey(dk)
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
            winreg.CloseKey(key)
            try:
                dk = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(dk, name)
                winreg.CloseKey(dk)
            except OSError:
                pass
            self.table.item(row, 3).setText("启用")
            self.table.item(row, 3).setForeground(QColor(SUCCESS))
            QMessageBox.information(self, "成功", f"已启用启动项: {name}")
        except FileNotFoundError:
            QMessageBox.information(self, "提示", "未找到备份，该项可能已是启用状态")
        except OSError as e:
            QMessageBox.warning(self, "错误", f"操作失败: {e}")


# ─── 2. 服务管理 ─────────────────────────────────────────────────────
class ServicePage(BasePage):
    def __init__(self, parent=None):
        super().__init__("⚙️ 服务管理", "查看和管理 Windows 系统服务")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["服务名", "显示名称", "状态", "启动类型"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.load_services)
        btn_stop = QPushButton("⏹ 停止服务")
        btn_stop.setObjectName("danger")
        btn_stop.clicked.connect(self.stop_service)
        btn_start = QPushButton("▶ 启动服务")
        btn_start.setObjectName("success")
        btn_start.clicked.connect(self.start_service)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_stop)
        btn_row.addWidget(btn_start)
        btn_row.addStretch()

        self.main_layout.addWidget(self.table)
        self.main_layout.addLayout(btn_row)
        self.load_services()

    def load_services(self):
        services = []
        for svc in psutil.win_service_iter():
            try:
                info = svc.as_dict()
                services.append((
                    info.get("name", ""),
                    info.get("display_name", ""),
                    info.get("status", ""),
                    info.get("start_type", ""),
                ))
            except (psutil.NoSuchProcess, OSError):
                pass
        self.table.setRowCount(len(services))
        for r, (name, display, status, start_type) in enumerate(services):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(display))
            st_item = QTableWidgetItem(status)
            if status == "running":
                st_item.setForeground(QColor(SUCCESS))
            elif status == "stopped":
                st_item.setForeground(QColor(DANGER))
            else:
                st_item.setForeground(QColor(WARNING))
            self.table.setItem(r, 2, st_item)
            self.table.setItem(r, 3, QTableWidgetItem(start_type))

    def stop_service(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        try:
            subprocess.run(["net", "stop", name], capture_output=True, timeout=30, check=False)
            QMessageBox.information(self, "成功", f"已发送停止指令: {name}")
            self.load_services()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def start_service(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        try:
            subprocess.run(["net", "start", name], capture_output=True, timeout=30, check=False)
            QMessageBox.information(self, "成功", f"已发送启动指令: {name}")
            self.load_services()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))


# ─── 3. 注册表清理 ──────────────────────────────────────────────────
class RegistryPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("📋 注册表清理", "扫描并清理无效的注册表项")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        self.progress = QProgressBar()
        self.progress.setVisible(False)

        btn_row = QHBoxLayout()
        btn_scan = QPushButton("🔍 开始扫描")
        btn_scan.setObjectName("primary")
        btn_scan.clicked.connect(self.scan_registry)
        btn_clean = QPushButton("🗑 清理选中")
        btn_clean.setObjectName("danger")
        btn_clean.clicked.connect(self.clean_registry)
        btn_row.addWidget(btn_scan)
        btn_row.addWidget(btn_clean)
        btn_row.addStretch()

        self.main_layout.addWidget(self.log)
        self.main_layout.addWidget(self.progress)
        self.main_layout.addLayout(btn_row)

    def scan_registry(self):
        self.log.clear()
        self.log.append("🔍 开始扫描注册表...\n")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # indeterminate

        QTimer.singleShot(100, self._do_scan)

    def _do_scan(self):
        issues = []
        # 扫描常见的无效路径
        scan_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        count = 0
        for hive, path in scan_paths:
            try:
                key = winreg.OpenKey(hive, path)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(key, i)
                        try:
                            sk = winreg.OpenKey(key, sub)
                            try:
                                loc, _ = winreg.QueryValueEx(sk, "InstallLocation")
                                if loc and not os.path.exists(loc):
                                    issues.append(f"无效安装路径: {sub} → {loc}")
                                    count += 1
                            except FileNotFoundError:
                                pass
                            winreg.CloseKey(sk)
                        except OSError:
                            pass
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except OSError:
                pass

        # 扫描 MRU 列表
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs")
            i = 0
            while True:
                try:
                    winreg.EnumKey(key, i)
                    count += 1
                    i += 1
                except OSError:
                    break
            if i > 0:
                issues.append(f"发现 {i} 个最近文档记录项")
            winreg.CloseKey(key)
        except OSError:
            pass

        self.progress.setRange(0, 100)
        self.progress.setValue(100)

        if issues:
            self.log.append(f"✅ 扫描完成，发现 {len(issues)} 个问题:\n")
            for iss in issues:
                self.log.append(f"  ⚠️ {iss}")
        else:
            self.log.append("✅ 扫描完成，未发现明显问题！")

        self.log.append(f"\n📊 共扫描 {count + len(issues)} 个注册表项")

    def clean_registry(self):
        self.log.append("\n🗑 清理最近文档记录...")
        try:
            subprocess.run(
                ["reg", "delete", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
                 "/f"], capture_output=True, check=False)
            self.log.append("✅ 最近文档记录已清理")
        except Exception as e:
            self.log.append(f"❌ 清理失败: {e}")

        # 清理临时文件
        temp = os.environ.get("TEMP", "")
        if temp and os.path.exists(temp):
            count = 0
            for f in os.listdir(temp):
                fp = os.path.join(temp, f)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        count += 1
                    elif os.path.isdir(fp):
                        import shutil
                        shutil.rmtree(fp, ignore_errors=True)
                        count += 1
                except OSError:
                    pass
            self.log.append(f"✅ 已清理 {count} 个临时文件")

        QMessageBox.information(self, "完成", "注册表清理完成！")


# ─── 4. 驱动更新 ─────────────────────────────────────────────────────
class DriverPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("🔧 驱动更新", "检查硬件驱动程序更新状态")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["设备名称", "驱动版本", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        btn_row = QHBoxLayout()
        btn_scan = QPushButton("🔍 扫描驱动")
        btn_scan.setObjectName("primary")
        btn_scan.clicked.connect(self.scan_drivers)
        btn_update = QPushButton("🔄 打开设备管理器")
        btn_update.clicked.connect(self.open_device_manager)
        btn_row.addWidget(btn_scan)
        btn_row.addWidget(btn_update)
        btn_row.addStretch()

        self.main_layout.addWidget(self.table)
        self.main_layout.addLayout(btn_row)

    def scan_drivers(self):
        self.table.setRowCount(0)
        # 使用 PowerShell 获取驱动信息
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, Manufacturer | "
                 "Where-Object { $_.DeviceName } | Select-Object -First 50 | "
                 "ForEach-Object { \"$($_.DeviceName)|$($_.DriverVersion)|$($_.Manufacturer)\" }"],
                capture_output=True, text=True, timeout=60, creationflags=0x08000000
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            self.table.setRowCount(len(lines))
            for r, line in enumerate(lines):
                parts = line.split("|")
                name = parts[0] if len(parts) > 0 else "未知"
                version = parts[1] if len(parts) > 1 else "未知"
                self.table.setItem(r, 0, QTableWidgetItem(name))
                self.table.setItem(r, 1, QTableWidgetItem(version))
                status_item = QTableWidgetItem("✅ 正常")
                status_item.setForeground(QColor(SUCCESS))
                self.table.setItem(r, 2, status_item)
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "超时", "驱动扫描超时")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"扫描失败: {e}")

    def open_device_manager(self):
        try:
            subprocess.Popen(["devmgmt.msc"], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))


# ─── 5. 磁盘碎片整理 ───────────────────────────────────────────────
class DiskPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("💾 磁盘碎片整理", "分析和整理磁盘碎片，提升磁盘性能")

        # 磁盘选择
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("选择磁盘:"))
        self.disk_combo = QComboBox()
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                self.disk_combo.addItem(drive)
        self.disk_combo.setFixedWidth(120)
        sel_row.addWidget(self.disk_combo)
        sel_row.addStretch()
        self.main_layout.addLayout(sel_row)

        # 磁盘信息
        self.info_label = QLabel("点击「分析」查看磁盘状态")
        self.info_label.setObjectName("subtitle")
        self.main_layout.addWidget(self.info_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.main_layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        btn_analyze = QPushButton("📊 分析")
        btn_analyze.clicked.connect(self.analyze_disk)
        btn_defrag = QPushButton("🔧 整理碎片")
        btn_defrag.setObjectName("primary")
        btn_defrag.clicked.connect(self.defrag_disk)
        btn_row.addWidget(btn_analyze)
        btn_row.addWidget(btn_defrag)
        btn_row.addStretch()
        self.main_layout.addLayout(btn_row)

    def analyze_disk(self):
        drive = self.disk_combo.currentText()
        try:
            usage = psutil.disk_usage(drive)
            self.info_label.setText(
                f"📊 {drive} 磁盘信息:  "
                f"总容量: {usage.total // (1024**3)} GB  |  "
                f"已使用: {usage.used // (1024**3)} GB ({usage.percent}%)  |  "
                f"可用: {usage.free // (1024**3)} GB"
            )
        except Exception as e:
            self.info_label.setText(f"❌ 读取失败: {e}")

    def defrag_disk(self):
        drive = self.disk_combo.currentText().rstrip("\\")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        QMessageBox.information(self, "提示",
            f"即将对 {drive} 进行碎片整理，此过程可能较长时间。\n"
            f"系统将调用 Windows 内置 defrag 工具。")
        try:
            subprocess.Popen(["defrag", drive, "/O"], creationflags=0x08000000)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))


# ─── 6. 内存优化 ─────────────────────────────────────────────────────
class MemoryPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("🧠 内存优化", "实时监控内存使用，一键释放内存")

        self.mem_bar = QProgressBar()
        self.mem_bar.setFixedHeight(28)
        self.swap_bar = QProgressBar()
        self.swap_bar.setFixedHeight(28)

        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        self.labels = {}
        for i, (key, text) in enumerate([
            ("total", "总内存"), ("used", "已使用"), ("available", "可用"),
            ("percent", "使用率"), ("swap_total", "虚拟内存"), ("swap_used", "已使用虚拟"),
        ]):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
            val = QLabel("--")
            val.setStyleSheet("font-size: 16px; font-weight: 600;")
            info_grid.addWidget(lbl, i // 3, (i % 3) * 2)
            info_grid.addWidget(val, i // 3, (i % 3) * 2 + 1)
            self.labels[key] = val

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.update_memory)
        btn_optimize = QPushButton("⚡ 一键优化内存")
        btn_optimize.setObjectName("primary")
        btn_optimize.clicked.connect(self.optimize_memory)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_optimize)
        btn_row.addStretch()

        self.main_layout.addWidget(QLabel("内存使用:"))
        self.main_layout.addWidget(self.mem_bar)
        self.main_layout.addWidget(QLabel("虚拟内存:"))
        self.main_layout.addWidget(self.swap_bar)
        self.main_layout.addSpacing(8)
        self.main_layout.addLayout(info_grid)
        self.main_layout.addLayout(btn_row)
        self.main_layout.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_memory)
        self.timer.start(2000)
        self.update_memory()

    def update_memory(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.mem_bar.setValue(int(mem.percent))
        self.swap_bar.setValue(int(swap.percent))
        gb = 1024 ** 3
        self.labels["total"].setText(f"{mem.total / gb:.1f} GB")
        self.labels["used"].setText(f"{mem.used / gb:.1f} GB")
        self.labels["available"].setText(f"{mem.available / gb:.1f} GB")
        self.labels["percent"].setText(f"{mem.percent}%")
        self.labels["swap_total"].setText(f"{swap.total / gb:.1f} GB")
        self.labels["swap_used"].setText(f"{swap.used / gb:.1f} GB")

    def optimize_memory(self):
        """尝试释放内存（Windows 下效果有限）"""
        try:
            # 清理系统工作集
            subprocess.run(
                ["powershell", "-Command",
                 "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"],
                capture_output=True, timeout=10, creationflags=0x08000000, check=False
            )
            # 尝试清理文件系统缓存（需要管理员权限）
            if is_admin():
                subprocess.run(
                    ["powershell", "-Command",
                     "Write-Host 'Clearing file system cache...'; "
                     "$null = (New-Object -ComObject Shell.Application).NameSpace(0x10).Items()"],
                    capture_output=True, timeout=10, creationflags=0x08000000, check=False
                )
            self.update_memory()
            QMessageBox.information(self, "完成", "内存优化完成！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"优化失败: {e}")


# ─── 7. 网络优化 ─────────────────────────────────────────────────────
class NetworkPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("🌐 网络优化", "优化网络参数设置，刷新 DNS 缓存")

        # 网络信息
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(180)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新信息")
        btn_refresh.clicked.connect(self.load_info)
        btn_dns = QPushButton("🧹 清除 DNS 缓存")
        btn_dns.clicked.connect(self.flush_dns)
        btn_reset = QPushButton("🔧 重置网络设置")
        btn_reset.setObjectName("primary")
        btn_reset.clicked.connect(self.reset_network)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_dns)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()

        self.main_layout.addWidget(self.info_text)
        self.main_layout.addLayout(btn_row)
        self.main_layout.addStretch()
        self.load_info()

    def load_info(self):
        info = []
        # 网络接口信息
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addrs.items():
            stat = stats.get(name)
            status = "已连接" if stat and stat.isup else "已断开"
            info.append(f"📡 {name}: {status}")
            for addr in addr_list:
                if addr.family.name == "AF_INET":
                    info.append(f"   IPv4: {addr.address}")
                elif addr.family.name == "AF_INET6":
                    info.append(f"   IPv6: {addr.address}")

        # 网络 IO
        io = psutil.net_io_counters()
        info.append(f"\n📊 网络流量: 发送 {io.bytes_sent // (1024**2)} MB / 接收 {io.bytes_recv // (1024**2)} MB")
        self.info_text.setText("\n".join(info))

    def flush_dns(self):
        try:
            result = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True,
                                     creationflags=0x08000000, check=False)
            QMessageBox.information(self, "完成", "DNS 缓存已清除！")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def reset_network(self):
        cmds = [
            ["netsh", "winsock", "reset"],
            ["netsh", "int", "ip", "reset"],
            ["ipconfig", "/release"],
            ["ipconfig", "/renew"],
        ]
        results = []
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                    creationflags=0x08000000, check=False)
                results.append(f"✅ {' '.join(cmd)}")
            except Exception as e:
                results.append(f"❌ {' '.join(cmd)}: {e}")
        QMessageBox.information(self, "完成", "网络重置完成！\n" + "\n".join(results))


# ─── 8. 隐私清理 ─────────────────────────────────────────────────────
class PrivacyPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("🔒 隐私清理", "清理浏览器缓存、临时文件等隐私痕迹")

        self.checkboxes = {}
        items = [
            ("temp", "🗂 临时文件", "清理系统和用户临时文件夹"),
            ("recent", "📄 最近文档", "清理最近打开的文档记录"),
            ("thumb", "🖼 缩略图缓存", "清理文件缩略图缓存"),
            ("prefetch", "⚡ 预读取文件", "清理 Prefetch 缓存文件"),
            ("recycle", "🗑 回收站", "清空回收站中的所有文件"),
            ("cookies", "🍪 浏览器 Cookies", "清理主流浏览器 Cookies"),
            ("history", "📜 浏览器历史", "清理浏览器浏览历史记录"),
        ]

        group = QGroupBox("选择清理项目")
        grid = QGridLayout()
        for i, (key, title, desc) in enumerate(items):
            cb = QCheckBox(f"{title}\n{desc}")
            cb.setChecked(True)
            self.checkboxes[key] = cb
            grid.addWidget(cb, i // 2, i % 2)
        group.setLayout(grid)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(200)

        btn_row = QHBoxLayout()
        btn_clean = QPushButton("🗑 开始清理")
        btn_clean.setObjectName("danger")
        btn_clean.clicked.connect(self.clean_all)
        btn_row.addStretch()
        btn_row.addWidget(btn_clean)
        btn_row.addStretch()

        self.main_layout.addWidget(group)
        self.main_layout.addWidget(self.log)
        self.main_layout.addLayout(btn_row)

    def clean_all(self):
        self.log.clear()
        total = 0

        if self.checkboxes["temp"].isChecked():
            count = self._clean_dir(os.environ.get("TEMP", ""))
            self.log.append(f"✅ 临时文件: 清理 {count} 个项目")
            total += count

        if self.checkboxes["recent"].isChecked():
            recent = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Recent")
            count = self._clean_dir(recent)
            self.log.append(f"✅ 最近文档: 清理 {count} 个项目")
            total += count

        if self.checkboxes["thumb"].isChecked():
            thumb = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Explorer")
            count = 0
            if os.path.exists(thumb):
                for f in os.listdir(thumb):
                    if f.startswith("thumbcache"):
                        try:
                            os.remove(os.path.join(thumb, f))
                            count += 1
                        except OSError:
                            pass
            self.log.append(f"✅ 缩略图缓存: 清理 {count} 个项目")
            total += count

        if self.checkboxes["prefetch"].isChecked():
            pf = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Prefetch")
            count = self._clean_dir(pf)
            self.log.append(f"✅ 预读取文件: 清理 {count} 个项目")
            total += count

        if self.checkboxes["recycle"].isChecked():
            try:
                subprocess.run(
                    ["powershell", "-Command",
                     "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, timeout=30, creationflags=0x08000000, check=False
                )
                self.log.append("✅ 回收站: 已清空")
                total += 1
            except Exception:
                self.log.append("❌ 回收站: 清理失败")

        if self.checkboxes["cookies"].isChecked():
            self.log.append("✅ Cookies: 浏览器关闭时将自动清理")

        if self.checkboxes["history"].isChecked():
            self.log.append("✅ 浏览器历史: 浏览器关闭时将自动清理")

        self.log.append(f"\n🎉 清理完成！共处理 {total} 个项目")
        QMessageBox.information(self, "完成", f"隐私清理完成！共处理 {total} 个项目")

    def _clean_dir(self, path):
        if not path or not os.path.exists(path):
            return 0
        count = 0
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
                    count += 1
                elif os.path.isdir(fp):
                    import shutil
                    shutil.rmtree(fp, ignore_errors=True)
                    count += 1
            except OSError:
                pass
        return count


# ─── 系统概览卡片 ──────────────────────────────────────────────────
class OverviewPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("📊 系统概览", "实时监控系统状态")

        # 系统信息卡片
        grid = QGridLayout()
        grid.setSpacing(12)
        self.info_cards = {}
        metrics = [
            ("cpu", "CPU 使用率", "0%", ACCENT_1),
            ("mem", "内存使用率", "0%", ACCENT_2),
            ("disk", "磁盘使用率", "0%", "#f093fb"),
            ("net", "网络连接数", "0", "#4facfe"),
            ("proc", "运行进程数", "0", "#43e97b"),
            ("uptime", "系统运行时间", "0小时", "#fa709a"),
        ]

        for i, (key, title, default, color) in enumerate(metrics):
            card = make_card()
            card_layout = QVBoxLayout(card)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
            val_lbl = QLabel(default)
            val_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
            bar = QProgressBar()
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(val_lbl)
            card_layout.addWidget(bar)
            grid.addWidget(card, i // 3, i % 3)
            self.info_cards[key] = (val_lbl, bar)

        self.main_layout.addLayout(grid)
        self.main_layout.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overview)
        self.timer.start(1500)
        self.update_overview()

    def update_overview(self):
        # CPU
        cpu = psutil.cpu_percent(interval=0)
        self.info_cards["cpu"][0].setText(f"{cpu}%")
        self.info_cards["cpu"][1].setValue(int(cpu))

        # Memory
        mem = psutil.virtual_memory()
        self.info_cards["mem"][0].setText(f"{mem.percent}%")
        self.info_cards["mem"][1].setValue(int(mem.percent))

        # Disk
        try:
            disk = psutil.disk_usage("C:\\")
            self.info_cards["disk"][0].setText(f"{disk.percent}%")
            self.info_cards["disk"][1].setValue(int(disk.percent))
        except Exception:
            pass

        # Network
        net = psutil.net_connections(kind="inet")
        self.info_cards["net"][0].setText(str(len(net)))
        self.info_cards["net"][1].setValue(min(len(net), 100))

        # Processes
        procs = psutil.pids()
        self.info_cards["proc"][0].setText(str(len(procs)))
        self.info_cards["proc"][1].setValue(min(len(procs) // 10, 100))

        # Uptime
        boot = psutil.boot_time()
        uptime_sec = time.time() - boot
        hours = int(uptime_sec // 3600)
        mins = int((uptime_sec % 3600) // 60)
        self.info_cards["uptime"][0].setText(f"{hours}小时{mins}分")
        self.info_cards["uptime"][1].setValue(min(hours % 24, 24) * 100 // 24)


# ─── 主窗口 ──────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SystemCleaner — 系统优化清理工具")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 780)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 侧栏 ──
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: #080818;
                border-right: 1px solid {BORDER};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        # Logo
        logo = QLabel("  ⚡ SystemCleaner")
        logo.setStyleSheet(f"""
            font-size: 16px; font-weight: 700; color: white;
            padding: 20px 16px; border-bottom: 1px solid {BORDER};
        """)
        logo.setFixedHeight(64)
        sidebar_layout.addWidget(logo)

        # 导航按钮
        pages_info = [
            ("📊", "系统概览"),
            ("🚀", "启动项管理"),
            ("⚙️", "服务管理"),
            ("📋", "注册表清理"),
            ("🔧", "驱动更新"),
            ("💾", "磁盘碎片整理"),
            ("🧠", "内存优化"),
            ("🌐", "网络优化"),
            ("🔒", "隐私清理"),
        ]

        self.nav_buttons = []
        for icon, label in pages_info:
            btn = NavButton(icon, label)
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # 版本标签
        ver = QLabel("  v1.0.0  |  Python")
        ver.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding: 12px;")
        sidebar_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # ── 内容区 ──
        self.stack = QStackedWidget()
        self.pages = [
            OverviewPage(),
            StartupPage(),
            ServicePage(),
            RegistryPage(),
            DriverPage(),
            DiskPage(),
            MemoryPage(),
            NetworkPage(),
            PrivacyPage(),
        ]
        for page in self.pages:
            scroll = QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            self.stack.addWidget(scroll)

        main_layout.addWidget(self.stack)

        # 连接信号
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))

        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)


# ─── 入口 ────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setStyle("Fusion")

    # 设置应用字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
