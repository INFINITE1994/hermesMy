# DiskSpaceAnalyzer - 磁盘空间分析器
# -*- coding: utf-8 -*-
"""
磁盘空间分析器 - 可视化分析磁盘使用情况
功能：树形图、旭日图、文件列表、文件夹树、Top100大文件、文件类型分析、旧文件查找、导出报告
"""

import os
import sys
import csv
import time
import locale
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict

import psutil
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QThread, pyqtSignal, QModelIndex, QSortFilterProxyModel,
    QAbstractTableModel, QAbstractItemModel, QRect, QPoint, QPointF
)
from PyQt6.QtGui import (
    QColor, QPainter, QFont, QPen, QBrush, QLinearGradient, QPalette,
    QIcon, QAction, QDesktopServices, QCursor, QPixmap, QConicalGradient,
    QRadialGradient
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QStatusBar, QMenuBar,
    QMenu, QFileDialog, QMessageBox, QTabWidget, QTreeView, QTableView,
    QHeaderView, QSplitter, QFrame, QGroupBox, QLineEdit, QSpinBox,
    QScrollArea, QSizePolicy, QStyledItemDelegate, QStyleOptionViewItem,
    QStyle, QTextEdit, QCheckBox, QToolButton, QAbstractItemView,
    QColumnView, QListWidget, QListWidgetItem, QStackedWidget, QSlider,
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox
)


# ───────────────────────── 数据结构 ─────────────────────────

@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    size: int
    modified: float
    accessed: float
    is_dir: bool
    ext: str = ""
    children: list = field(default_factory=list)
    parent: Optional['DirInfo'] = None


@dataclass
class DirInfo:
    """目录信息"""
    path: str
    name: str
    size: int = 0
    file_count: int = 0
    dir_count: int = 0
    children_dirs: list = field(default_factory=list)
    children_files: list = field(default_factory=list)
    parent: Optional['DirInfo'] = None


# ───────────────────────── 工具函数 ─────────────────────────

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    if i == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[i]}"


def get_file_ext(path: str) -> str:
    """获取文件扩展名"""
    ext = Path(path).suffix.lower()
    return ext if ext else "(无扩展名)"


def get_color_for_index(index: int, total: int, alpha: int = 200) -> QColor:
    """根据索引生成渐变色"""
    hue = (index * 137.508) % 360
    return QColor.fromHsv(int(hue), 180, 220, alpha)


def gradient_color(ratio: float) -> QColor:
    """根据比例生成从蓝到紫的渐变色"""
    r = int(102 + (118 - 102) * ratio)
    g = int(126 + (75 - 126) * ratio)
    b = int(234 + (162 - 234) * ratio)
    return QColor(r, g, b, 220)


# ───────────────────────── 扫描线程 ─────────────────────────

class ScanThread(QThread):
    """扫描目录的后台线程"""
    progress = pyqtSignal(str, int, int)  # (path, files_scanned, dirs_scanned)
    finished_signal = pyqtSignal(object)  # DirInfo
    error = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            result = self._scan(self.path)
            if not self._cancel:
                self.finished_signal.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _scan(self, path: str) -> DirInfo:
        """递归扫描目录"""
        dir_info = DirInfo(path=path, name=os.path.basename(path) or path)
        file_count = 0
        dir_count = 0
        try:
            entries = os.scandir(path)
            for entry in entries:
                if self._cancel:
                    break
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        dir_count += 1
                        child = self._scan(entry.path)
                        child.parent = dir_info
                        dir_info.children_dirs.append(child)
                        dir_info.size += child.size
                        file_count += child.file_count
                        dir_count += child.dir_count
                    elif entry.is_file(follow_symlinks=False):
                        file_count += 1
                        stat = entry.stat(follow_symlinks=False)
                        fi = FileInfo(
                            path=entry.path,
                            name=entry.name,
                            size=stat.st_size,
                            modified=stat.st_mtime,
                            accessed=stat.st_atime,
                            is_dir=False,
                            ext=get_file_ext(entry.name)
                        )
                        fi.parent = dir_info
                        dir_info.children_files.append(fi)
                        dir_info.size += stat.st_size
                except (PermissionError, OSError):
                    continue
                if file_count % 500 == 0:
                    self.progress.emit(path, file_count, dir_count)
        except (PermissionError, OSError):
            pass
        dir_info.file_count = file_count
        dir_info.dir_count = dir_count
        return dir_info


# ───────────────────────── 树形图组件 ─────────────────────────

class TreemapWidget(QWidget):
    """树形图可视化"""
    clicked = pyqtSignal(str)  # 点击路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dir_info: Optional[DirInfo] = None
        self.rects: list[tuple[QRect, DirInfo | FileInfo, QColor, str]] = []
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.hovered_index = -1
        self.setToolTip("树形图可视化 - 显示文件夹大小分布")

    def set_data(self, dir_info: DirInfo):
        self.dir_info = dir_info
        self._layout_treemap()
        self.update()

    def _layout_treemap(self):
        self.rects.clear()
        if not self.dir_info or self.dir_info.size == 0:
            return
        w = self.width() - 4
        h = self.height() - 4
        if w <= 0 or h <= 0:
            return
        items = []
        for d in self.dir_info.children_dirs[:20]:
            items.append((d.size, d))
        for f in self.dir_info.children_files[:20]:
            items.append((f.size, f))
        items.sort(key=lambda x: x[0], reverse=True)
        total = sum(s for s, _ in items)
        if total == 0:
            return
        self._squarify(items, QRect(2, 2, w, h), total)

    def _squarify(self, items, rect: QRect, total: int):
        """简化的 squarified treemap 算法"""
        if not items or rect.width() <= 0 or rect.height() <= 0:
            return
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        horizontal = w >= h
        remaining = total
        pos = 0
        for i, (size, item) in enumerate(items):
            if remaining <= 0:
                break
            ratio = size / total
            if horizontal:
                cw = int(w * size / remaining) if remaining > 0 else 0
                r = QRect(x + pos, y, max(cw, 1), h)
            else:
                ch = int(h * size / remaining) if remaining > 0 else 0
                r = QRect(x, y + pos, w, max(ch, 1))
            color = gradient_color(i / max(len(items), 1))
            label = item.name if hasattr(item, 'name') else ""
            self.rects.append((r, item, color, f"{label}\n{format_size(size)}"))
            if horizontal:
                pos += max(cw, 1)
            else:
                pos += max(ch, 1)
            remaining -= size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0a0a0a"))
        if not self.rects:
            painter.setPen(QColor("#666"))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请选择目录开始扫描")
            painter.end()
            return
        for i, (r, item, color, label) in enumerate(self.rects):
            if r.width() < 2 or r.height() < 2:
                continue
            c = QColor(color)
            if i == self.hovered_index:
                c = c.lighter(130)
            painter.setPen(QPen(QColor("#0a0a0a"), 1))
            painter.setBrush(QBrush(c))
            painter.drawRect(r)
            if r.width() > 40 and r.height() > 25:
                painter.setPen(QColor("#fff"))
                font_size = min(10, max(7, r.width() // 15))
                painter.setFont(QFont("Microsoft YaHei", font_size))
                painter.drawText(r.adjusted(4, 2, -4, -2),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                                 label.split('\n')[0])
                if r.height() > 40:
                    painter.setPen(QColor("#ccc"))
                    painter.drawText(r.adjusted(4, 16, -4, -2),
                                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                                     label.split('\n')[1] if '\n' in label else "")
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.dir_info:
            self._layout_treemap()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        old = self.hovered_index
        self.hovered_index = -1
        for i, (r, _, _, label) in enumerate(self.rects):
            if r.contains(pos):
                self.hovered_index = i
                self.setToolTip(label.replace('\n', ' - '))
                break
        if self.hovered_index != old:
            self.update()

    def mousePressEvent(self, event):
        pos = event.pos()
        for i, (r, item, _, _) in enumerate(self.rects):
            if r.contains(pos):
                if hasattr(item, 'path'):
                    self.clicked.emit(item.path)
                break


# ───────────────────────── 旭日图组件 ─────────────────────────

class SunburstWidget(QWidget):
    """旭日图可视化"""
    clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dir_info: Optional[DirInfo] = None
        self.setMinimumSize(400, 300)
        self.arcs: list[tuple[float, float, float, float, QColor, str, str]] = []
        self.hovered = -1
        self.setMouseTracking(True)

    def set_data(self, dir_info: DirInfo):
        self.dir_info = dir_info
        self._build_arcs()
        self.update()

    def _build_arcs(self):
        self.arcs.clear()
        if not self.dir_info or self.dir_info.size == 0:
            return
        cx, cy = self.width() / 2, self.height() / 2
        max_r = min(cx, cy) - 20
        if max_r <= 0:
            return
        items = sorted(self.dir_info.children_dirs, key=lambda d: d.size, reverse=True)[:12]
        total = self.dir_info.size
        if total == 0:
            return
        angle = 0
        for i, d in enumerate(items):
            span = 360 * 16 * d.size / total
            color = gradient_color(i / max(len(items), 1))
            self.arcs.append((max_r * 0.3, max_r * 0.7, angle, span, color, d.name, format_size(d.size)))
            # 子级
            sub_items = sorted(d.children_dirs, key=lambda x: x.size, reverse=True)[:6]
            sub_angle = angle
            for j, sd in enumerate(sub_items):
                sub_span = span * sd.size / d.size if d.size > 0 else 0
                sub_color = gradient_color((i + j * 0.1) / max(len(items), 1))
                self.arcs.append((max_r * 0.7, max_r * 1.0, sub_angle, sub_span,
                                  sub_color.lighter(110), sd.name, format_size(sd.size)))
                sub_angle += sub_span
            angle += span

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0a0a0a"))
        cx, cy = self.width() / 2, self.height() / 2
        if not self.arcs:
            painter.setPen(QColor("#666"))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请选择目录开始扫描")
            painter.end()
            return
        for i, (inner_r, outer_r, start, span, color, name, size_str) in enumerate(self.arcs):
            c = QColor(color)
            if i == self.hovered:
                c = c.lighter(140)
            painter.setPen(QPen(QColor("#0a0a0a"), 1))
            painter.setBrush(QBrush(c))
            rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
            painter.drawEllipse(rect)
            # 内部用深色覆盖形成环
            inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
            painter.setBrush(QBrush(QColor("#0a0a0a")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(inner_rect)
            # 绘制弧段
            painter.setBrush(QBrush(c))
            painter.setPen(QPen(QColor("#0a0a0a"), 1))
            path_rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
            painter.drawPie(path_rect, int(start), int(span))
            inner_rect2 = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
            painter.setBrush(QBrush(QColor("#0a0a0a")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(inner_rect2)

        # 中心文字
        painter.setPen(QColor("#fff"))
        painter.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(cx - 80, cy - 15, 160, 30),
                         Qt.AlignmentFlag.AlignCenter, format_size(self.dir_info.size))
        painter.setPen(QColor("#aaa"))
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.drawText(QRectF(cx - 80, cy + 10, 160, 20),
                         Qt.AlignmentFlag.AlignCenter, self.dir_info.name)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.dir_info:
            self._build_arcs()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        cx, cy = self.width() / 2, self.height() / 2
        import math
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360
        old = self.hovered
        self.hovered = -1
        for i, (inner_r, outer_r, start_16, span_16, color, name, size_str) in enumerate(self.arcs):
            start = start_16 / 16
            span = span_16 / 16
            if inner_r <= dist <= outer_r:
                a = angle
                end = (start + span) % 360
                if start <= end:
                    if start <= a <= end:
                        self.hovered = i
                        self.setToolTip(f"{name}: {size_str}")
                        break
                else:
                    if a >= start or a <= end:
                        self.hovered = i
                        self.setToolTip(f"{name}: {size_str}")
                        break
        if self.hovered != old:
            self.update()


# ───────────────────────── 文件列表模型 ─────────────────────────

class FileTableModel(QAbstractTableModel):
    """文件列表数据模型"""
    HEADERS = ["名称", "大小", "类型", "修改日期", "路径"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: list[FileInfo] = []

    def set_files(self, files: list[FileInfo]):
        self.beginResetModel()
        self.files = files
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.files)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.files):
            return None
        f = self.files[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return f.name
            elif col == 1:
                return format_size(f.size)
            elif col == 2:
                return f.ext if not f.is_dir else "文件夹"
            elif col == 3:
                return datetime.fromtimestamp(f.modified).strftime("%Y-%m-%d %H:%M")
            elif col == 4:
                return f.path
        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 1:
                return QColor("#764ba2")
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 1:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        self.beginResetModel()
        reverse = order == Qt.SortOrder.DescendingOrder
        if column == 0:
            self.files.sort(key=lambda f: f.name.lower(), reverse=reverse)
        elif column == 1:
            self.files.sort(key=lambda f: f.size, reverse=reverse)
        elif column == 2:
            self.files.sort(key=lambda f: f.ext.lower(), reverse=reverse)
        elif column == 3:
            self.files.sort(key=lambda f: f.modified, reverse=reverse)
        elif column == 4:
            self.files.sort(key=lambda f: f.path.lower(), reverse=reverse)
        self.endResetModel()


# ───────────────────────── 文件夹树模型 ─────────────────────────

class FolderTreeItem:
    def __init__(self, data, parent=None):
        self.data = data
        self.parent_item = parent
        self.children: list['FolderTreeItem'] = []
        self._loaded = False

    def appendChild(self, child):
        self.children.append(child)

    def child(self, row):
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return 3

    def data(self, column):
        if isinstance(self.data, DirInfo):
            if column == 0:
                return self.data.name
            elif column == 1:
                return format_size(self.data.size)
            elif column == 2:
                return f"{self.data.file_count} 文件, {self.data.dir_count} 目录"
        elif isinstance(self.data, FileInfo):
            if column == 0:
                return self.data.name
            elif column == 1:
                return format_size(self.data.size)
            elif column == 2:
                return self.data.ext
        return None

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.children.index(self)
        return 0


class FolderTreeModel(QAbstractItemModel):
    """文件夹树数据模型"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = FolderTreeItem(None)

    def set_data(self, dir_info: DirInfo):
        self.beginResetModel()
        self.root_item = FolderTreeItem(None)
        self._add_children(self.root_item, dir_info)
        self.endResetModel()

    def _add_children(self, parent_item: FolderTreeItem, dir_info: DirInfo):
        item = FolderTreeItem(dir_info, parent_item)
        parent_item.appendChild(item)
        for d in sorted(dir_info.children_dirs, key=lambda x: x.size, reverse=True):
            child = FolderTreeItem(d, item)
            item.appendChild(child)
            self._add_children_rec(child, d)
        for f in sorted(dir_info.children_files, key=lambda x: x.size, reverse=True)[:50]:
            item.appendChild(FolderTreeItem(f, item))

    def _add_children_rec(self, parent_item: FolderTreeItem, dir_info: DirInfo):
        for d in sorted(dir_info.children_dirs, key=lambda x: x.size, reverse=True):
            child = FolderTreeItem(d, parent_item)
            parent_item.appendChild(child)
        for f in sorted(dir_info.children_files, key=lambda x: x.size, reverse=True)[:20]:
            parent_item.appendChild(FolderTreeItem(f, parent_item))

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_item = parent.internalPointer() if parent.isValid() else self.root_item
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        parent_item = parent.internalPointer() if parent.isValid() else self.root_item
        return parent_item.childCount()

    def columnCount(self, parent=QModelIndex()):
        return 3

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 1:
            return QColor("#667eea")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["名称", "大小", "信息"][section]
        return None


# ───────────────────────── 文件类型模型 ─────────────────────────

class FileTypeModel(QAbstractTableModel):
    """文件类型统计模型"""
    HEADERS = ["文件类型", "文件数量", "总大小", "占比"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_list: list[tuple[str, int, int, float]] = []

    def set_data(self, data_list):
        self.beginResetModel()
        self.data_list = data_list
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)

    def columnCount(self, parent=QModelIndex()):
        return 4

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.data_list):
            return None
        ext, count, size, pct = self.data_list[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return ext
            elif col == 1: return str(count)
            elif col == 2: return format_size(size)
            elif col == 3: return f"{pct:.1f}%"
        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 3: return QColor("#667eea")
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (1, 2, 3):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None


# ───────────────────────── 卡片框架 ─────────────────────────

class CardWidget(QFrame):
    """带标题的卡片容器"""
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background-color: #111122;
                border: 1px solid #222244;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold; border: none;")
            layout.addWidget(lbl)
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

    def addWidget(self, w):
        self.content_layout.addWidget(w)

    def addLayout(self, l):
        self.content_layout.addLayout(l)


# ───────────────────────── 统计卡片 ─────────────────────────

class StatCard(QFrame):
    """统计信息小卡片"""
    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 80)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111122, stop:1 #1a1a33);
                border: 1px solid #222244;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #888; font-size: 11px; border: none;")
        layout.addWidget(self.title_lbl)
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("color: #667eea; font-size: 18px; font-weight: bold; border: none;")
        layout.addWidget(self.value_lbl)

    def set_value(self, v: str):
        self.value_lbl.setText(v)


# ───────────────────────── 主窗口 ─────────────────────────

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("磁盘空间分析器 · DiskSpaceAnalyzer")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.dir_info: Optional[DirInfo] = None
        self.all_files: list[FileInfo] = []
        self.scan_thread: Optional[ScanThread] = None
        self._setup_ui()
        self._setup_menu()
        self._apply_style()
        self._load_drives()

    # ── UI 构建 ──

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ── 顶部栏 ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        logo = QLabel("💾 磁盘空间分析器")
        logo.setStyleSheet("""
            font-size: 20px; font-weight: bold; color: #667eea;
            padding: 4px 0;
        """)
        top_bar.addWidget(logo)
        top_bar.addStretch()

        # 驱动器选择
        self.drive_combo = QComboBox()
        self.drive_combo.setFixedWidth(220)
        self.drive_combo.setStyleSheet(self._combo_style())
        top_bar.addWidget(QLabel("磁盘:"))
        top_bar.addWidget(self.drive_combo)

        # 目录选择
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择要分析的目录...")
        self.path_edit.setMinimumWidth(300)
        self.path_edit.setStyleSheet(self._input_style())
        browse_btn = QPushButton("📂 浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.setStyleSheet(self._btn_style())
        browse_btn.clicked.connect(self._browse)
        top_bar.addWidget(self.path_edit)
        top_bar.addWidget(browse_btn)

        # 扫描按钮
        self.scan_btn = QPushButton("🔍 扫描")
        self.scan_btn.setFixedWidth(90)
        self.scan_btn.setStyleSheet(self._btn_primary_style())
        self.scan_btn.clicked.connect(self._start_scan)
        top_bar.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.setStyleSheet(self._btn_style())
        self.stop_btn.clicked.connect(self._stop_scan)
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)

        main_layout.addLayout(top_bar)

        # ── 统计卡片行 ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_total = StatCard("总大小")
        self.stat_files = StatCard("文件数")
        self.stat_dirs = StatCard("目录数")
        self.stat_largest = StatCard("最大文件")
        for card in [self.stat_total, self.stat_files, self.stat_dirs, self.stat_largest]:
            stats_row.addWidget(card)
        stats_row.addStretch()
        main_layout.addLayout(stats_row)

        # ── 进度条 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #111122; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #667eea, stop:1 #764ba2); border-radius: 3px; }
        """)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        # ── 主内容区 ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self._tab_style())
        main_layout.addWidget(self.tabs, 1)

        # Tab 1: 树形图
        self.treemap_tab = QWidget()
        treemap_layout = QVBoxLayout(self.treemap_tab)
        self.treemap = TreemapWidget()
        treemap_layout.addWidget(self.treemap)
        self.tabs.addTab(self.treemap_tab, "📊 树形图")

        # Tab 2: 旭日图
        self.sunburst_tab = QWidget()
        sunburst_layout = QVBoxLayout(self.sunburst_tab)
        self.sunburst = SunburstWidget()
        sunburst_layout.addWidget(self.sunburst)
        self.tabs.addTab(self.sunburst_tab, "🎯 旭日图")

        # Tab 3: 文件列表
        self.filelist_tab = QWidget()
        filelist_layout = QVBoxLayout(self.filelist_tab)
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索文件名...")
        self.search_edit.setStyleSheet(self._input_style())
        self.search_edit.textChanged.connect(self._filter_files)
        search_row.addWidget(self.search_edit)
        filelist_layout.addLayout(search_row)
        self.file_model = FileTableModel()
        self.file_proxy = QSortFilterProxyModel()
        self.file_proxy.setSourceModel(self.file_model)
        self.file_proxy.setFilterKeyColumn(0)
        self.file_table = QTableView()
        self.file_table.setModel(self.file_proxy)
        self.file_table.setSortingEnabled(True)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.verticalHeader().setDefaultSectionSize(28)
        self.file_table.setStyleSheet(self._table_style())
        self.file_table.doubleClicked.connect(self._open_file_location)
        filelist_layout.addWidget(self.file_table)
        self.tabs.addTab(self.filelist_tab, "📋 文件列表")

        # Tab 4: 文件夹树
        self.foldertree_tab = QWidget()
        foldertree_layout = QVBoxLayout(self.foldertree_tab)
        self.folder_model = FolderTreeModel()
        self.folder_tree = QTreeView()
        self.folder_tree.setModel(self.folder_model)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.header().setStretchLastSection(True)
        self.folder_tree.header().setDefaultSectionSize(150)
        self.folder_tree.setStyleSheet(self._tree_style())
        foldertree_layout.addWidget(self.folder_tree)
        self.tabs.addTab(self.foldertree_tab, "📁 文件夹树")

        # Tab 5: Top 100
        self.top100_tab = QWidget()
        top100_layout = QVBoxLayout(self.top100_tab)
        self.top100_model = FileTableModel()
        self.top100_table = QTableView()
        self.top100_table.setModel(self.top100_model)
        self.top100_table.setSortingEnabled(True)
        self.top100_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.top100_table.horizontalHeader().setStretchLastSection(True)
        self.top100_table.verticalHeader().setDefaultSectionSize(28)
        self.top100_table.setStyleSheet(self._table_style())
        self.top100_table.doubleClicked.connect(self._open_file_location_top100)
        top100_layout.addWidget(self.top100_table)
        self.tabs.addTab(self.top100_tab, "🏆 Top 100")

        # Tab 6: 文件类型分析
        self.filetype_tab = QWidget()
        filetype_layout = QVBoxLayout(self.filetype_tab)
        self.filetype_model = FileTypeModel()
        self.filetype_table = QTableView()
        self.filetype_table.setModel(self.filetype_model)
        self.filetype_table.setSortingEnabled(True)
        self.filetype_table.horizontalHeader().setStretchLastSection(True)
        self.filetype_table.verticalHeader().setDefaultSectionSize(28)
        self.filetype_table.setStyleSheet(self._table_style())
        filetype_layout.addWidget(self.filetype_table)
        self.tabs.addTab(self.filetype_tab, "📊 文件类型")

        # Tab 7: 旧文件查找
        self.oldfiles_tab = QWidget()
        oldfiles_layout = QVBoxLayout(self.oldfiles_tab)
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("未访问天数:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 3650)
        self.days_spin.setValue(90)
        self.days_spin.setStyleSheet(self._input_style())
        ctrl_row.addWidget(self.days_spin)
        find_old_btn = QPushButton("🔍 查找旧文件")
        find_old_btn.setStyleSheet(self._btn_primary_style())
        find_old_btn.clicked.connect(self._find_old_files)
        ctrl_row.addWidget(find_old_btn)
        ctrl_row.addStretch()
        oldfiles_layout.addLayout(ctrl_row)
        self.oldfiles_model = FileTableModel()
        self.oldfiles_table = QTableView()
        self.oldfiles_table.setModel(self.oldfiles_model)
        self.oldfiles_table.setSortingEnabled(True)
        self.oldfiles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.oldfiles_table.horizontalHeader().setStretchLastSection(True)
        self.oldfiles_table.verticalHeader().setDefaultSectionSize(28)
        self.oldfiles_table.setStyleSheet(self._table_style())
        oldfiles_layout.addWidget(self.oldfiles_table)
        self.tabs.addTab(self.oldfiles_tab, "📅 旧文件")

        # Tab 8: 导出报告
        self.export_tab = QWidget()
        export_layout = QVBoxLayout(self.export_tab)
        export_group = CardWidget("导出分析报告")
        btn_row = QHBoxLayout()
        html_btn = QPushButton("📄 导出 HTML 报告")
        html_btn.setStyleSheet(self._btn_primary_style())
        html_btn.setFixedHeight(40)
        html_btn.clicked.connect(self._export_html)
        csv_btn = QPushButton("📊 导出 CSV 数据")
        csv_btn.setStyleSheet(self._btn_style())
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._export_csv)
        btn_row.addWidget(html_btn)
        btn_row.addWidget(csv_btn)
        export_group.addLayout(btn_row)
        export_layout.addWidget(export_group)
        export_layout.addStretch()
        self.tabs.addTab(self.export_tab, "💾 导出")

    # ── 菜单 ──

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background: #0a0a0a; color: #ccc; border-bottom: 1px solid #222244; }
            QMenuBar::item:selected { background: #222244; }
            QMenu { background: #111122; color: #ccc; border: 1px solid #222244; }
            QMenu::item:selected { background: #667eea; }
        """)
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("打开目录...", self._browse)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于", self._show_about)

    # ── 样式 ──

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #0a0a0a; }
            QWidget { color: #ddd; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
            QLabel { color: #ccc; }
            QLineEdit, QSpinBox, QComboBox {
                background: #1a1a2e; color: #ddd; border: 1px solid #333;
                border-radius: 6px; padding: 6px 10px; font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #667eea; }
            QComboBox QAbstractItemView {
                background: #1a1a2e; color: #ddd; selection-background-color: #667eea;
            }
            QMenuBar { background: #0a0a0a; color: #ccc; }
            QStatusBar { background: #0a0a0a; color: #666; border-top: 1px solid #222244; }
            QScrollBar:vertical {
                background: #0a0a0a; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #333; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #0a0a0a; height: 10px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #333; border-radius: 5px; min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover { background: #555; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)

    def _combo_style(self):
        return "QComboBox { min-width: 200px; }"

    def _input_style(self):
        return ""

    def _btn_style(self):
        return """
            QPushButton {
                background: #1a1a2e; color: #ccc; border: 1px solid #333;
                border-radius: 6px; padding: 6px 16px; font-size: 13px;
            }
            QPushButton:hover { background: #222244; border-color: #667eea; }
            QPushButton:pressed { background: #333; }
            QPushButton:disabled { color: #555; background: #111; }
        """

    def _btn_primary_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 6px;
                padding: 6px 16px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7b92ee, stop:1 #8a5fb5);
            }
            QPushButton:pressed { background: #5567cc; }
            QPushButton:disabled { background: #333; color: #666; }
        """

    def _tab_style(self):
        return """
            QTabWidget::pane { border: 1px solid #222244; background: #0a0a0a; border-radius: 6px; }
            QTabBar::tab {
                background: #111122; color: #888; padding: 8px 18px;
                border: 1px solid #222244; border-bottom: none;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px; font-size: 13px;
            }
            QTabBar::tab:selected { background: #1a1a2e; color: #667eea; border-bottom: 2px solid #667eea; }
            QTabBar::tab:hover { background: #1a1a2e; color: #aaa; }
        """

    def _table_style(self):
        return """
            QTableView {
                background: #0a0a0a; color: #ddd; gridline-color: #222244;
                border: 1px solid #222244; border-radius: 6px;
                selection-background-color: #222244;
                alternate-background-color: #0f0f1a;
                font-size: 12px;
            }
            QTableView::item { padding: 4px 8px; }
            QTableView::item:selected { background: #222244; color: #667eea; }
            QHeaderView::section {
                background: #111122; color: #888; border: none;
                border-right: 1px solid #222244; border-bottom: 1px solid #222244;
                padding: 6px 10px; font-size: 12px; font-weight: bold;
            }
            QHeaderView::section:hover { background: #1a1a2e; color: #aaa; }
        """

    def _tree_style(self):
        return """
            QTreeView {
                background: #0a0a0a; color: #ddd; border: 1px solid #222244;
                border-radius: 6px; alternate-background-color: #0f0f1a;
                font-size: 12px;
            }
            QTreeView::item { padding: 4px 8px; }
            QTreeView::item:selected { background: #222244; color: #667eea; }
            QTreeView::item:hover { background: #1a1a2e; }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings { border-image: none; image: none; }
            QHeaderView::section {
                background: #111122; color: #888; border: none;
                border-right: 1px solid #222244; border-bottom: 1px solid #222244;
                padding: 6px 10px; font-size: 12px; font-weight: bold;
            }
        """

    # ── 驱动器 ──

    def _load_drives(self):
        self.drive_combo.clear()
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                label = f"{part.mountpoint} ({format_size(usage.total)})"
                self.drive_combo.addItem(label, part.mountpoint)
            except Exception:
                pass
        self.drive_combo.currentIndexChanged.connect(self._drive_changed)
        if self.drive_combo.count() > 0:
            self._drive_changed(0)

    def _drive_changed(self, index):
        path = self.drive_combo.currentData()
        if path:
            self.path_edit.setText(path)

    # ── 浏览 ──

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择目录", self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    # ── 扫描 ──

    def _start_scan(self):
        path = self.path_edit.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "错误", "请选择有效的目录路径")
            return
        self._stop_scan()
        self.progress_bar.setVisible(True)
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"正在扫描: {path} ...")
        self.scan_thread = ScanThread(path)
        self.scan_thread.progress.connect(self._on_scan_progress)
        self.scan_thread.finished_signal.connect(self._on_scan_done)
        self.scan_thread.error.connect(self._on_scan_error)
        self.scan_thread.start()

    def _stop_scan(self):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.cancel()
            self.scan_thread.wait(3000)
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_scan_progress(self, path, files, dirs):
        self.status_label.setText(f"扫描中... {files} 文件, {dirs} 目录")

    def _on_scan_error(self, msg):
        self._stop_scan()
        QMessageBox.critical(self, "扫描错误", msg)

    def _on_scan_done(self, dir_info: DirInfo):
        self._stop_scan()
        self.dir_info = dir_info
        self.all_files.clear()
        self._collect_files(dir_info)
        self.status_label.setText(
            f"扫描完成: {format_size(dir_info.size)} | {dir_info.file_count} 文件 | {dir_info.dir_count} 目录"
        )
        self._update_stats()
        self._update_views()

    def _collect_files(self, d: DirInfo):
        for f in d.children_files:
            self.all_files.append(f)
        for child in d.children_dirs:
            self._collect_files(child)

    # ── 更新视图 ──

    def _update_stats(self):
        if not self.dir_info:
            return
        self.stat_total.set_value(format_size(self.dir_info.size))
        self.stat_files.set_value(str(self.dir_info.file_count))
        self.stat_dirs.set_value(str(self.dir_info.dir_count))
        largest = max(self.all_files, key=lambda f: f.size, default=None)
        if largest:
            self.stat_largest.set_value(f"{format_size(largest.size)}")

    def _update_views(self):
        if not self.dir_info:
            return
        self.treemap.set_data(self.dir_info)
        self.sunburst.set_data(self.dir_info)
        self.file_model.set_files(sorted(self.all_files, key=lambda f: f.size, reverse=True))
        self.folder_model.set_data(self.dir_info)
        top100 = sorted(self.all_files, key=lambda f: f.size, reverse=True)[:100]
        self.top100_model.set_files(top100)
        self._update_file_types()

    def _update_file_types(self):
        type_map: dict[str, list] = defaultdict(lambda: [0, 0])
        total = sum(f.size for f in self.all_files) or 1
        for f in self.all_files:
            ext = f.ext
            type_map[ext][0] += 1
            type_map[ext][1] += f.size
        data = []
        for ext, (count, size) in sorted(type_map.items(), key=lambda x: x[1][1], reverse=True):
            data.append((ext, count, size, size / total * 100))
        self.filetype_model.set_data(data)

    # ── 搜索过滤 ──

    def _filter_files(self, text: str):
        self.file_proxy.setFilterFixedString(text)

    # ── 旧文件查找 ──

    def _find_old_files(self):
        if not self.all_files:
            QMessageBox.information(self, "提示", "请先扫描一个目录")
            return
        days = self.days_spin.value()
        cutoff = time.time() - days * 86400
        old = [f for f in self.all_files if f.accessed < cutoff and not f.is_dir]
        old.sort(key=lambda f: f.accessed)
        self.oldfiles_model.set_files(old)
        self.status_label.setText(f"找到 {len(old)} 个超过 {days} 天未访问的文件")

    # ── 导出 ──

    def _export_html(self):
        if not self.dir_info:
            QMessageBox.information(self, "提示", "请先扫描一个目录")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 HTML 报告", "disk_report.html", "HTML 文件 (*.html)")
        if not path:
            return
        top100 = sorted(self.all_files, key=lambda f: f.size, reverse=True)[:100]
        type_map: dict[str, list] = defaultdict(lambda: [0, 0])
        for f in self.all_files:
            type_map[f.ext][0] += 1
            type_map[f.ext][1] += f.size
        type_sorted = sorted(type_map.items(), key=lambda x: x[1][1], reverse=True)
        total_size = self.dir_info.size or 1

        html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>磁盘空间分析报告</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; background: #0a0a0a; color: #ddd; padding: 30px; }}
h1 {{ color: #667eea; }}
h2 {{ color: #764ba2; border-bottom: 1px solid #222244; padding-bottom: 8px; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
th {{ background: #111122; color: #888; padding: 10px; text-align: left; }}
td {{ padding: 8px 10px; border-bottom: 1px solid #222244; }}
tr:hover {{ background: #1a1a2e; }}
.card {{ background: #111122; border: 1px solid #222244; border-radius: 8px; padding: 20px; margin: 16px 0; }}
.stat {{ display: inline-block; margin: 0 20px 10px 0; }}
.stat-val {{ font-size: 24px; font-weight: bold; color: #667eea; }}
.stat-label {{ font-size: 12px; color: #888; }}
.bar {{ background: #222244; border-radius: 4px; height: 20px; }}
.bar-fill {{ background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; border-radius: 4px; }}
</style></head><body>
<h1>💾 磁盘空间分析报告</h1>
<p style="color:#666">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 目录: {self.dir_info.path}</p>
<div class="card">
<div class="stat"><div class="stat-val">{format_size(self.dir_info.size)}</div><div class="stat-label">总大小</div></div>
<div class="stat"><div class="stat-val">{self.dir_info.file_count}</div><div class="stat-label">文件数</div></div>
<div class="stat"><div class="stat-val">{self.dir_info.dir_count}</div><div class="stat-label">目录数</div></div>
</div>
<h2>📊 文件类型分布</h2>
<table><tr><th>类型</th><th>数量</th><th>大小</th><th>占比</th><th></th></tr>"""
        for ext, (cnt, sz) in type_sorted[:20]:
            pct = sz / total_size * 100
            html += f'<tr><td>{ext}</td><td>{cnt}</td><td>{format_size(sz)}</td><td>{pct:.1f}%</td>'
            html += f'<td><div class="bar"><div class="bar-fill" style="width:{min(pct, 100):.1f}%"></div></div></td></tr>'
        html += "</table><h2>🏆 Top 100 最大文件</h2><table><tr><th>#</th><th>文件名</th><th>大小</th><th>路径</th></tr>"
        for i, f in enumerate(top100, 1):
            html += f'<tr><td>{i}</td><td>{f.name}</td><td>{format_size(f.size)}</td><td style="color:#888">{f.path}</td></tr>'
        html += "</table></body></html>"
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(html)
        QMessageBox.information(self, "导出成功", f"HTML 报告已保存到:\n{path}")

    def _export_csv(self):
        if not self.all_files:
            QMessageBox.information(self, "提示", "请先扫描一个目录")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV 数据", "disk_report.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8-sig', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(["文件名", "大小(字节)", "大小", "类型", "修改日期", "访问日期", "路径"])
            for f in sorted(self.all_files, key=lambda x: x.size, reverse=True):
                writer.writerow([
                    f.name, f.size, format_size(f.size), f.ext,
                    datetime.fromtimestamp(f.modified).strftime("%Y-%m-%d %H:%M"),
                    datetime.fromtimestamp(f.accessed).strftime("%Y-%m-%d %H:%M"),
                    f.path
                ])
        QMessageBox.information(self, "导出成功", f"CSV 数据已保存到:\n{path}")

    # ── 双击打开位置 ──

    def _open_file_location(self, index):
        src = self.file_proxy.mapToSource(index)
        if src.isValid() and src.row() < len(self.file_model.files):
            path = self.file_model.files[src.row()].path
            self._open_in_explorer(path)

    def _open_file_location_top100(self, index):
        if index.isValid() and index.row() < len(self.top100_model.files):
            path = self.top100_model.files[index.row()].path
            self._open_in_explorer(path)

    def _open_in_explorer(self, path: str):
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            os.startfile(folder)

    # ── 关于 ──

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "<h2 style='color:#667eea'>磁盘空间分析器</h2>"
            "<p>DiskSpaceAnalyzer v1.0.0</p>"
            "<p>可视化分析磁盘使用情况的专业工具</p>"
            "<p style='color:#888'>技术栈: Python + PyQt6 + psutil</p>"
            "<p style='color:#666'>© 2026 Hermes Agent</p>"
        )

    def closeEvent(self, event):
        self._stop_scan()
        event.accept()


# ───────────────────────── 入口 ─────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DiskSpaceAnalyzer")
    app.setStyle("Fusion")

    # 全局调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#ddd"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0a0a0a"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0f0f1a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#ddd"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ccc"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#fff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#555"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

