#!/usr/bin/env python3
"""DiskAnalyzer - 磁盘空间分析器"""
import sys
import os
import csv
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFileDialog, QProgressBar, QHeaderView,
    QSpinBox, QFrame, QSplitter, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QFont, QBrush, QPen, QLinearGradient

# ── Dark theme ──────────────────────────────────────────────────────────────
STYLESHEET = """
QMainWindow, QWidget { background: #0a0a0a; color: #e0e0e0; font-family: 'Segoe UI', 'Microsoft YaHei'; }
QTabWidget::pane { border: 1px solid #333; background: #111122; }
QTabBar::tab { background: #1a1a2e; color: #aaa; padding: 10px 20px; border: 1px solid #333; border-bottom: none; }
QTabBar::tab:selected { background: #111122; color: #e0e0e0; border-bottom: 2px solid #667eea; }
QTreeWidget, QTableWidget { background: #111122; border: 1px solid #333; color: #e0e0e0; gridline-color: #222; }
QTreeWidget::item:hover, QTableWidget::item:hover { background: #1a1a3e; }
QTreeWidget::item:selected, QTableWidget::item:selected { background: #667eea; color: white; }
QHeaderView::section { background: #1a1a2e; color: #ccc; border: 1px solid #333; padding: 6px; }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #667eea, stop:1 #764ba2); color: white; border: none; padding: 8px 18px; border-radius: 4px; font-weight: bold; }
QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7b93ff, stop:1 #8b5fcf); }
QPushButton:disabled { background: #333; color: #666; }
QProgressBar { background: #1a1a2e; border: 1px solid #333; border-radius: 4px; text-align: center; color: white; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #667eea, stop:1 #764ba2); border-radius: 3px; }
QLabel { color: #ccc; }
QLabel#title { font-size: 16px; font-weight: bold; color: #667eea; }
QLabel#stat { font-size: 13px; padding: 4px; background: #1a1a2e; border-radius: 4px; }
QFrame#card { background: #111122; border: 1px solid #2a2a4a; border-radius: 8px; padding: 12px; }
QSpinBox, QComboBox { background: #1a1a2e; color: #e0e0e0; border: 1px solid #333; padding: 4px 8px; border-radius: 4px; }
QScrollBar:vertical { background: #0a0a0a; width: 10px; }
QScrollBar::handle:vertical { background: #333; border-radius: 5px; min-height: 20px; }
"""

def fmt_size(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


# ── Worker thread ───────────────────────────────────────────────────────────
class ScanWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def run(self):
        result = {'files': [], 'dirs': {}, 'types': defaultdict(lambda: [0, 0])}
        count = 0
        try:
            for entry in os.scandir(self.path):
                if self.isInterruptionRequested():
                    return
                try:
                    self._walk(entry, result, 0, count)
                    count += 1
                    if count % 50 == 0:
                        self.progress.emit(count, entry.path)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        self.finished.emit(result)
    
    def _walk(self, entry, result, depth, count):
        try:
            if entry.is_file(follow_symlinks=False):
                try:
                    st = entry.stat(follow_symlinks=False)
                    size = st.st_size
                    ext = os.path.splitext(entry.name)[1].lower()
                    result['files'].append((entry.path, size, st.st_atime, ext))
                    cat = self._cat(ext)
                    result['types'][cat][0] += 1
                    result['types'][cat][1] += size
                except OSError:
                    pass
            elif entry.is_dir(follow_symlinks=False):
                dir_size = 0
                try:
                    for child in os.scandir(entry.path):
                        if self.isInterruptionRequested():
                            return
                        count += 1
                        if count % 200 == 0:
                            self.progress.emit(count, child.path)
                        self._walk(child, result, depth+1, count)
                        # accumulate size from files list
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass

    @staticmethod
    def _cat(ext):
        imgs = {'.jpg','.jpeg','.png','.gif','.bmp','.svg','.webp','.ico','.tiff','.raw'}
        vids = {'.mp4','.avi','.mkv','.mov','.wmv','.flv','.webm','.m4v'}
        aud = {'.mp3','.wav','.flac','.aac','.ogg','.wma','.m4a'}
        docs = {'.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx','.txt','.rtf','.csv','.md'}
        code = {'.py','.js','.ts','.c','.cpp','.h','.java','.go','.rs','.html','.css','.json','.xml','.yaml','.yml','.sh','.bat'}
        arch = {'.zip','.rar','.7z','.tar','.gz','.bz2','.xz'}
        exe = {'.exe','.msi','.dll','.sys','.so'}
        if ext in imgs: return '图片'
        if ext in vids: return '视频'
        if ext in aud: return '音频'
        if ext in docs: return '文档'
        if ext in code: return '代码'
        if ext in arch: return '压缩包'
        if ext in exe: return '可执行文件'
        return '其他'


# ── Treemap widget ──────────────────────────────────────────────────────────
class TreemapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.rects = []
        self.setMinimumSize(400, 300)

    def set_data(self, data):
        self.rects = data
        self.update()

    def paintEvent(self, event):
        if not self.rects:
            p = QPainter(self)
            p.setPen(QColor('#666'))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, '扫描后显示 treemap')
            return
        p = QPainter(self)
        colors = ['#667eea','#764ba2','#f093fb','#4facfe','#00f2fe','#43e97b','#fa709a','#fee140']
        for i, (name, size, x, y, w, h) in enumerate(self.rects[:64]):
            c = QColor(colors[i % len(colors)])
            p.fillRect(int(x), int(y), max(1,int(w)), max(1,int(h)), c)
            p.setPen(QColor('#0a0a0a'))
            p.drawRect(int(x), int(y), max(1,int(w)), max(1,int(h)))
            if w > 60 and h > 20:
                p.setPen(QColor('white'))
                p.setFont(QFont('Segoe UI', 8))
                label = f"{os.path.basename(name)}\n{fmt_size(size)}"
                p.drawText(int(x)+4, int(y)+4, max(1,int(w-8)), max(1,int(h-8)), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap, label)


# ── Sunburst widget ─────────────────────────────────────────────────────────
class SunburstWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.setMinimumSize(400, 300)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data:
            p = QPainter(self)
            p.setPen(QColor('#666'))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, '扫描后显示旭日图')
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width()/2, self.height()/2
        r = min(cx, cy) - 20
        total = sum(s for _, s in self.data) or 1
        colors = ['#667eea','#764ba2','#f093fb','#4facfe','#00f2fe','#43e97b','#fa709a','#fee140','#a18cd1','#fbc2eb']
        angle = 90 * 16
        for i, (name, size) in enumerate(self.data[:12]):
            span = int(360 * 16 * size / total)
            c = QColor(colors[i % len(colors)])
            p.setBrush(c)
            p.setPen(QPen(QColor('#0a0a0a'), 1))
            p.drawPie(int(cx-r), int(cy-r), int(2*r), int(2*r), angle, span)
            mid_angle = (angle + span/2) / 16
            import math
            tx = cx + r*0.65 * math.cos(math.radians(mid_angle))
            ty = cy - r*0.65 * math.sin(math.radians(mid_angle))
            p.setPen(QColor('white'))
            p.setFont(QFont('Segoe UI', 8))
            label = f"{name}\n{size/1024/1024:.0f} MB"
            p.drawText(int(tx-40), int(ty-10), 80, 20, Qt.AlignmentFlag.AlignCenter, label)
            angle += span


# ── Main window ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DiskAnalyzer - 磁盘空间分析器')
        self.resize(1200, 800)
        self.worker = None
        self.scan_data = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel('📊 DiskAnalyzer 磁盘空间分析器')
        title.setObjectName('title')
        hdr.addWidget(title)
        hdr.addStretch()
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setMinimumWidth(300)
        self.path_combo.setStyleSheet("QComboBox { background: #1a1a2e; color: #e0e0e0; }")
        for d in self._drives():
            self.path_combo.addItem(d)
        hdr.addWidget(QLabel('扫描路径:'))
        hdr.addWidget(self.path_combo)
        btn_browse = QPushButton('浏览...')
        btn_browse.clicked.connect(self._browse)
        hdr.addWidget(btn_browse)
        self.btn_scan = QPushButton('开始扫描')
        self.btn_scan.clicked.connect(self._scan)
        hdr.addWidget(self.btn_scan)
        layout.addLayout(hdr)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet('color: #667eea;')
        layout.addWidget(self.status_label)

        # Stats bar
        stats_frame = QFrame()
        stats_frame.setObjectName('card')
        self.stats_layout = QHBoxLayout(stats_frame)
        self.stat_labels = {}
        for key in ['总大小','文件数','文件夹数','最大文件']:
            lbl = QLabel(f'{key}: -')
            lbl.setObjectName('stat')
            self.stats_layout.addWidget(lbl)
            self.stat_labels[key] = lbl
        layout.addWidget(stats_frame)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_treemap_tab(), '🗺️ Treemap 可视化')
        self.tabs.addTab(self._build_sunburst_tab(), '☀️ 旭日图')
        self.tabs.addTab(self._build_file_list_tab(), '📋 文件列表')
        self.tabs.addTab(self._build_folder_tree_tab(), '📁 文件夹树')
        self.tabs.addTab(self._build_top100_tab(), '🏆 Top 100 大文件')
        self.tabs.addTab(self._build_type_tab(), '📊 文件类型分析')
        self.tabs.addTab(self._build_old_tab(), '🕐 旧文件查找')
        layout.addWidget(self.tabs)

        # Export bar
        exp = QHBoxLayout()
        exp.addStretch()
        btn_html = QPushButton('导出 HTML 报告')
        btn_html.clicked.connect(lambda: self._export('html'))
        exp.addWidget(btn_html)
        btn_csv = QPushButton('导出 CSV 报告')
        btn_csv.clicked.connect(lambda: self._export('csv'))
        exp.addWidget(btn_csv)
        layout.addLayout(exp)

    def _drives(self):
        import string
        drives = []
        for c in string.ascii_uppercase:
            p = f'{c}:\\'
            if os.path.exists(p):
                drives.append(p)
        return drives

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, '选择目录')
        if d:
            self.path_combo.setCurrentText(d)

    def _build_treemap_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.treemap = TreemapWidget()
        l.addWidget(self.treemap)
        return w

    def _build_sunburst_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.sunburst = SunburstWidget()
        l.addWidget(self.sunburst)
        return w

    def _build_file_list_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.file_table = QTableWidget(0, 4)
        self.file_table.setHorizontalHeaderLabels(['文件名','大小','修改时间','类型'])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.setSortingEnabled(True)
        l.addWidget(self.file_table)
        return w

    def _build_folder_tree_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(['名称','大小','文件数'])
        self.folder_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        l.addWidget(self.folder_tree)
        return w

    def _build_top100_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.top100_table = QTableWidget(0, 3)
        self.top100_table.setHorizontalHeaderLabels(['文件名','大小','路径'])
        self.top100_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.top100_table.setSortingEnabled(True)
        l.addWidget(self.top100_table)
        return w

    def _build_type_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.type_table = QTableWidget(0, 3)
        self.type_table.setHorizontalHeaderLabels(['类型','文件数','总大小'])
        self.type_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.type_table.setSortingEnabled(True)
        l.addWidget(self.type_table)
        return w

    def _build_old_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        h = QHBoxLayout()
        h.addWidget(QLabel('未访问天数:'))
        self.old_days = QSpinBox()
        self.old_days.setRange(1, 3650)
        self.old_days.setValue(90)
        h.addWidget(self.old_days)
        btn = QPushButton('查找')
        btn.clicked.connect(self._find_old)
        h.addWidget(btn)
        h.addStretch()
        l.addLayout(h)
        self.old_table = QTableWidget(0, 4)
        self.old_table.setHorizontalHeaderLabels(['文件名','大小','最后访问','路径'])
        self.old_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.old_table.setSortingEnabled(True)
        l.addWidget(self.old_table)
        return w

    # ── Scanning ────────────────────────────────────────────────────────────
    def _scan(self):
        path = self.path_combo.currentText().strip()
        if not os.path.isdir(path):
            QMessageBox.warning(self, '错误', f'路径无效: {path}')
            return
        self.btn_scan.setEnabled(False)
        self.progress.setRange(0, 0)
        self.status_label.setText(f'正在扫描 {path} ...')
        self.worker = ScanWorker(path)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, count, path):
        self.status_label.setText(f'已扫描 {count} 项: {path[:80]}...')

    def _on_finished(self, data):
        self.scan_data = data
        self.btn_scan.setEnabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        files = data['files']
        types = data['types']
        self.status_label.setText(f'扫描完成! 共 {len(files)} 个文件')
        
        total_size = sum(f[1] for f in files)
        dirs_count = sum(1 for f in files if True)  # approximation
        biggest = max(files, key=lambda f: f[1]) if files else ('-', 0, 0, '')
        
        self.stat_labels['总大小'].setText(f'总大小: {fmt_size(total_size)}')
        self.stat_labels['文件数'].setText(f'文件数: {len(files):,}')
        dirs_set = set()
        for f in files:
            dirs_set.add(os.path.dirname(f[0]))
        self.stat_labels['文件夹数'].setText(f'文件夹数: {len(dirs_set):,}')
        self.stat_labels['最大文件'].setText(f'最大文件: {fmt_size(biggest[1])}')

        # Populate file table
        self.file_table.setSortingEnabled(False)
        self.file_table.setRowCount(min(len(files), 5000))
        for i, (path, size, atime, ext) in enumerate(sorted(files, key=lambda x: -x[1])[:5000]):
            self.file_table.setItem(i, 0, QTableWidgetItem(os.path.basename(path)))
            si = QTableWidgetItem()
            si.setData(Qt.ItemDataRole.DisplayRole, fmt_size(size))
            si.setData(Qt.ItemDataRole.UserRole, size)
            self.file_table.setItem(i, 1, si)
            self.file_table.setItem(i, 2, QTableWidgetItem(datetime.fromtimestamp(atime).strftime('%Y-%m-%d %H:%M')))
            self.file_table.setItem(i, 3, QTableWidgetItem(ext))
        self.file_table.setSortingEnabled(True)

        # Top 100
        top = sorted(files, key=lambda x: -x[1])[:100]
        self.top100_table.setSortingEnabled(False)
        self.top100_table.setRowCount(len(top))
        for i, (path, size, _, _) in enumerate(top):
            self.top100_table.setItem(i, 0, QTableWidgetItem(os.path.basename(path)))
            si = QTableWidgetItem(fmt_size(size))
            si.setData(Qt.ItemDataRole.UserRole, size)
            self.top100_table.setItem(i, 1, si)
            self.top100_table.setItem(i, 2, QTableWidgetItem(os.path.dirname(path)))
        self.top100_table.setSortingEnabled(True)

        # Type analysis
        type_list = sorted(types.items(), key=lambda x: -x[1][1])
        self.type_table.setSortingEnabled(False)
        self.type_table.setRowCount(len(type_list))
        for i, (cat, (count, size)) in enumerate(type_list):
            self.type_table.setItem(i, 0, QTableWidgetItem(cat))
            self.type_table.setItem(i, 1, QTableWidgetItem(str(count)))
            si = QTableWidgetItem(fmt_size(size))
            si.setData(Qt.ItemDataRole.UserRole, size)
            self.type_table.setItem(i, 2, si)
        self.type_table.setSortingEnabled(True)

        # Treemap - simple squarified layout
        self._build_treemap(files, total_size)

        # Sunburst - top level dirs
        dir_sizes = defaultdict(int)
        for path, size, _, _ in files:
            rel = path.replace(self.path_combo.currentText().strip(), '').lstrip('\\/')
            top_dir = rel.split('\\')[0].split('/')[0] if rel else '(root)'
            dir_sizes[top_dir] += size
        sunburst_data = sorted(dir_sizes.items(), key=lambda x: -x[1])[:12]
        self.sunburst.set_data(sunburst_data)

        # Folder tree
        self._build_folder_tree(files)

    def _build_treemap(self, files, total):
        path = self.path_combo.currentText().strip()
        dir_sizes = defaultdict(int)
        for fpath, size, _, _ in files:
            rel = fpath.replace(path, '').lstrip('\\/')
            top_dir = rel.split('\\')[0].split('/')[0] if rel else '(root)'
            dir_sizes[top_dir] += size
        items = sorted(dir_sizes.items(), key=lambda x: -x[1])[:30]
        # Simple squarified-ish layout
        rects = []
        w, h = 780, 500
        x, y = 10, 10
        row_h = h
        remaining_total = sum(s for _, s in items) or 1
        row_w = w
        for name, size in items:
            frac = size / remaining_total
            rw = row_w * frac
            rects.append((name, size, x, y, rw, row_h))
            x += rw
        self.treemap.set_data(rects)

    def _build_folder_tree(self, files):
        path = self.path_combo.currentText().strip()
        tree = defaultdict(lambda: [0, 0])
        for fpath, size, _, _ in files:
            rel = fpath.replace(path, '').lstrip('\\/')
            parts = rel.replace('/', '\\').split('\\')
            for depth in range(len(parts)):
                key = '\\'.join(parts[:depth+1])
                tree[key][0] += 1
                if depth == len(parts)-1:
                    tree[key][1] += size
        self.folder_tree.clear()
        root_item = QTreeWidgetItem(self.folder_tree, [os.path.basename(path.rstrip('\\')) or path, '', ''])
        self._add_tree_children(root_item, tree, '')

    def _add_tree_children(self, parent, tree, prefix):
        children = {}
        for key, (count, size) in tree.items():
            if prefix:
                if not key.startswith(prefix + '\\'):
                    continue
                rest = key[len(prefix)+1:]
            else:
                rest = key
            if '\\' in rest:
                top = rest.split('\\')[0]
                if top not in children:
                    children[top] = [0, 0]
                children[top][0] += count
                children[top][1] += size
            else:
                if rest not in children:
                    children[rest] = [count, size]
                else:
                    children[rest][0] += count
        for name in sorted(children.keys()):
            cnt, sz = children[name]
            child = QTreeWidgetItem(parent, [name, fmt_size(sz), str(cnt)])
            full = f"{prefix}\\{name}" if prefix else name
            self._add_tree_children(child, tree, full)

    def _find_old(self):
        if not self.scan_data:
            QMessageBox.information(self, '提示', '请先扫描目录')
            return
        days = self.old_days.value()
        cutoff = time.time() - days * 86400
        old = [(p, s, a) for p, s, a, _ in self.scan_data['files'] if a < cutoff]
        old.sort(key=lambda x: x[2])
        self.old_table.setSortingEnabled(False)
        self.old_table.setRowCount(min(len(old), 2000))
        for i, (path, size, atime) in enumerate(old[:2000]):
            self.old_table.setItem(i, 0, QTableWidgetItem(os.path.basename(path)))
            si = QTableWidgetItem(fmt_size(size))
            si.setData(Qt.ItemDataRole.UserRole, size)
            self.old_table.setItem(i, 1, si)
            self.old_table.setItem(i, 2, QTableWidgetItem(datetime.fromtimestamp(atime).strftime('%Y-%m-%d %H:%M')))
            self.old_table.setItem(i, 3, QTableWidgetItem(os.path.dirname(path)))
        self.old_table.setSortingEnabled(True)
        self.status_label.setText(f'找到 {len(old)} 个超过 {days} 天未访问的文件')

    def _export(self, fmt):
        if not self.scan_data:
            QMessageBox.information(self, '提示', '请先扫描目录')
            return
        ext = '*.html' if fmt == 'html' else '*.csv'
        path, _ = QFileDialog.getSaveFileName(self, '导出报告', '', f'文件 ({ext})')
        if not path:
            return
        files = self.scan_data['files']
        types = self.scan_data['types']
        if fmt == 'csv':
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(['文件路径','大小(字节)','大小','最后访问','类型'])
                for p, s, a, e in sorted(files, key=lambda x: -x[1]):
                    w.writerow([p, s, fmt_size(s), datetime.fromtimestamp(a).strftime('%Y-%m-%d %H:%M'), e])
        else:
            html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>DiskAnalyzer 报告</title>',
                '<style>body{background:#0a0a0a;color:#e0e0e0;font-family:Segoe UI;max-width:1200px;margin:auto;padding:20px}',
                'h1{color:#667eea}table{width:100%;border-collapse:collapse}th{background:#1a1a2e;padding:8px;text-align:left}',
                'td{padding:6px;border-bottom:1px solid #222}tr:hover{background:#1a1a3e}.card{background:#111122;padding:16px;border-radius:8px;margin:12px 0}</style></head><body>',
                f'<h1>📊 DiskAnalyzer 磁盘分析报告</h1><p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>']
            total = sum(s for _, s, _, _ in files)
            html.append(f'<div class="card"><h2>概览</h2><p>总文件数: {len(files):,} | 总大小: {fmt_size(total)}</p></div>')
            html.append('<div class="card"><h2>文件类型分布</h2><table><tr><th>类型</th><th>文件数</th><th>大小</th></tr>')
            for cat, (cnt, sz) in sorted(types.items(), key=lambda x: -x[1][1]):
                html.append(f'<tr><td>{cat}</td><td>{cnt:,}</td><td>{fmt_size(sz)}</td></tr>')
            html.append('</table></div>')
            html.append('<div class="card"><h2>Top 100 大文件</h2><table><tr><th>文件</th><th>大小</th><th>路径</th></tr>')
            for p, s, _, _ in sorted(files, key=lambda x: -x[1])[:100]:
                html.append(f'<tr><td>{os.path.basename(p)}</td><td>{fmt_size(s)}</td><td>{os.path.dirname(p)}</td></tr>')
            html.append('</table></div></body></html>')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
        self.status_label.setText(f'报告已导出: {path}')


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
