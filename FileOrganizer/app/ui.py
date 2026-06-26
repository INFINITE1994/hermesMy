"""主界面"""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTabWidget, QPushButton, QLabel, QLineEdit,
    QSpinBox, QComboBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QFrame, QFileDialog, QMessageBox,
    QStatusBar, QGroupBox, QCheckBox, QAbstractItemView,
    QApplication,
)
from PyQt6.QtCore import Qt, QDir, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QIcon, QFont

from app.styles import get_stylesheet, BG_CARD, ACCENT_START, ACCENT_END
from app.organizer import format_size, scan_drives
from app.workers import (
    OrganizeByTypeWorker, OrganizeByDateWorker,
    FindDuplicatesWorker, FindEmptyFoldersWorker,
    CleanEmptyFoldersWorker, FindLargeFilesWorker,
    BatchRenamePreviewWorker, ExecuteRenamesWorker, UndoWorker,
)


class GradientCard(QFrame):
    """圆角卡片容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileOrganizer - 暗黑文件整理工具")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        self._worker = None
        self._last_results = []  # 用于撤销
        self._current_dir = ""

        self._setup_ui()
        self._connect_signals()
        self._update_status("就绪 - 请选择一个文件夹开始")

    def _setup_ui(self):
        """构建界面"""
        # 中央 widget
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 左侧面板 - 文件浏览器
        left_panel = self._create_left_panel()
        left_panel.setFixedWidth(320)

        # 右侧面板 - 功能区域
        right_panel = self._create_right_panel()

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([320, 1080])
        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("就绪")
        self.statusBar.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setValue(0)
        self.statusBar.addPermanentWidget(self.progress_bar)

        self.setStyleSheet(get_stylesheet())

    def _create_left_panel(self) -> QWidget:
        """创建左侧文件浏览器面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 路径输入
        path_card = GradientCard()
        path_layout = QVBoxLayout(path_card)
        path_layout.setContentsMargins(12, 12, 12, 12)

        path_label = QLabel("📂 选择文件夹")
        path_label.setObjectName("title")
        path_layout.addWidget(path_label)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("点击浏览选择文件夹...")
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit)

        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_btn)
        path_layout.addLayout(path_row)

        # 快速选择
        quick_row = QHBoxLayout()
        desktop_btn = QPushButton("桌面")
        desktop_btn.clicked.connect(lambda: self._set_path(str(Path.home() / "Desktop")))
        quick_row.addWidget(desktop_btn)
        docs_btn = QPushButton("文档")
        docs_btn.clicked.connect(lambda: self._set_path(str(Path.home() / "Documents")))
        quick_row.addWidget(docs_btn)
        dl_btn = QPushButton("下载")
        dl_btn.clicked.connect(lambda: self._set_path(str(Path.home() / "Downloads")))
        quick_row.addWidget(dl_btn)
        path_layout.addLayout(quick_row)

        layout.addWidget(path_card)

        # 文件树
        tree_card = GradientCard()
        tree_layout = QVBoxLayout(tree_card)
        tree_layout.setContentsMargins(8, 8, 8, 8)

        tree_label = QLabel("文件树")
        tree_label.setObjectName("title")
        tree_layout.addWidget(tree_label)

        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.rootPath())
        self.fs_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Drives)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.fs_model)
        self.tree_view.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.clicked.connect(self._on_tree_clicked)
        tree_layout.addWidget(self.tree_view)

        layout.addWidget(tree_card)

        # 目录信息
        self.info_card = GradientCard()
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        self.info_label = QLabel("请选择文件夹查看信息")
        self.info_label.setObjectName("subtitle")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(self.info_card)

        return panel

    def _create_right_panel(self) -> QWidget:
        """创建右侧功能面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 标题
        header = QHBoxLayout()
        title = QLabel("⚡ FileOrganizer")
        title.setObjectName("logo")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 功能选项卡
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_organize_tab(), "📁 文件整理")
        self.tabs.addTab(self._create_duplicates_tab(), "🔍 重复查找")
        self.tabs.addTab(self._create_rename_tab(), "✏️ 批量重命名")
        self.tabs.addTab(self._create_cleaner_tab(), "📂 空文件夹")
        self.tabs.addTab(self._create_large_tab(), "📊 大文件")
        layout.addWidget(self.tabs)

        # 撤销按钮
        undo_row = QHBoxLayout()
        undo_row.addStretch()
        self.undo_btn = QPushButton("↩️ 撤销上次操作")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._undo_last)
        undo_row.addWidget(self.undo_btn)
        layout.addLayout(undo_row)

        return panel

    def _create_organize_tab(self) -> QWidget:
        """文件整理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 按类型整理
        type_card = GradientCard()
        type_layout = QVBoxLayout(type_card)
        type_layout.setContentsMargins(16, 16, 16, 16)

        type_title = QLabel("📁 按文件类型自动分类")
        type_title.setObjectName("title")
        type_layout.addWidget(type_title)

        type_desc = QLabel("将文件自动整理到 图片/文档/视频/音频/压缩包/代码 等文件夹中")
        type_desc.setObjectName("subtitle")
        type_layout.addWidget(type_desc)

        type_btn_row = QHBoxLayout()
        self.type_preview_btn = QPushButton("📋 预览变更")
        self.type_preview_btn.clicked.connect(self._preview_type_org)
        type_btn_row.addWidget(self.type_preview_btn)

        self.type_exec_btn = QPushButton("🚀 执行整理")
        self.type_exec_btn.setObjectName("primary")
        self.type_exec_btn.setEnabled(False)
        self.type_exec_btn.clicked.connect(self._exec_type_org)
        type_btn_row.addWidget(self.type_exec_btn)
        type_layout.addLayout(type_btn_row)

        layout.addWidget(type_card)

        # 按日期整理
        date_card = GradientCard()
        date_layout = QVBoxLayout(date_card)
        date_layout.setContentsMargins(16, 16, 16, 16)

        date_title = QLabel("📅 按修改日期自动归档")
        date_title.setObjectName("title")
        date_layout.addWidget(date_title)

        date_desc = QLabel("根据文件修改时间创建 年/月 文件夹结构进行归档")
        date_desc.setObjectName("subtitle")
        date_layout.addWidget(date_desc)

        date_btn_row = QHBoxLayout()
        self.date_preview_btn = QPushButton("📋 预览变更")
        self.date_preview_btn.clicked.connect(self._preview_date_org)
        date_btn_row.addWidget(self.date_preview_btn)

        self.date_exec_btn = QPushButton("🚀 执行归档")
        self.date_exec_btn.setObjectName("primary")
        self.date_exec_btn.setEnabled(False)
        self.date_exec_btn.clicked.connect(self._exec_date_org)
        date_btn_row.addWidget(self.date_exec_btn)
        date_layout.addLayout(date_btn_row)

        layout.addWidget(date_card)

        # 预览表格
        preview_card = GradientCard()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        preview_header = QLabel("变更预览")
        preview_header.setObjectName("title")
        preview_layout.addWidget(preview_header)

        self.org_table = QTableWidget()
        self.org_table.setColumnCount(2)
        self.org_table.setHorizontalHeaderLabels(["源文件", "目标位置"])
        self.org_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.org_table.setAlternatingRowColors(True)
        self.org_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.org_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        preview_layout.addWidget(self.org_table)

        layout.addWidget(preview_card)
        return tab

    def _create_duplicates_tab(self) -> QWidget:
        """重复文件查找选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 控制区
        ctrl_card = GradientCard()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🔍 重复文件查找")
        title.setObjectName("title")
        ctrl_layout.addWidget(title)

        desc = QLabel("通过 MD5 哈希比对查找完全相同的文件，帮助释放磁盘空间")
        desc.setObjectName("subtitle")
        ctrl_layout.addWidget(desc)

        btn_row = QHBoxLayout()
        self.dup_scan_btn = QPushButton("🔍 开始扫描")
        self.dup_scan_btn.setObjectName("primary")
        self.dup_scan_btn.clicked.connect(self._scan_duplicates)
        btn_row.addWidget(self.dup_scan_btn)

        self.dup_delete_btn = QPushButton("🗑️ 删除选中")
        self.dup_delete_btn.setObjectName("danger")
        self.dup_delete_btn.setEnabled(False)
        self.dup_delete_btn.clicked.connect(self._delete_duplicates)
        btn_row.addWidget(self.dup_delete_btn)
        ctrl_layout.addLayout(btn_row)

        layout.addWidget(ctrl_card)

        # 结果表格
        result_card = GradientCard()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(8, 8, 8, 8)

        self.dup_table = QTableWidget()
        self.dup_table.setColumnCount(5)
        self.dup_table.setHorizontalHeaderLabels(["选择", "文件名", "路径", "大小", "哈希值"])
        self.dup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.dup_table.setColumnWidth(0, 50)
        self.dup_table.setAlternatingRowColors(True)
        self.dup_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        result_layout.addWidget(self.dup_table)

        # 统计信息
        self.dup_info = QLabel("")
        self.dup_info.setObjectName("subtitle")
        result_layout.addWidget(self.dup_info)

        layout.addWidget(result_card)
        return tab

    def _create_rename_tab(self) -> QWidget:
        """批量重命名选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 设置区
        settings_card = GradientCard()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("✏️ 批量重命名")
        title.setObjectName("title")
        settings_layout.addWidget(title)

        # 模式选择
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("命名模式:"))
        self.rename_mode = QComboBox()
        self.rename_mode.addItems([
            "顺序编号 (前缀_001)",
            "日期命名 (原名_20260101)",
            "自定义模式 ({n}_{o}{e})",
        ])
        self.rename_mode.currentIndexChanged.connect(self._on_rename_mode_changed)
        mode_row.addWidget(self.rename_mode)
        settings_layout.addLayout(mode_row)

        # 前缀
        prefix_row = QHBoxLayout()
        prefix_row.addWidget(QLabel("前缀/模式:"))
        self.rename_prefix = QLineEdit()
        self.rename_prefix.setPlaceholderText("输入前缀或自定义模式...")
        prefix_row.addWidget(self.rename_prefix)
        settings_layout.addLayout(prefix_row)

        # 起始编号
        num_row = QHBoxLayout()
        num_row.addWidget(QLabel("起始编号:"))
        self.rename_start = QSpinBox()
        self.rename_start.setRange(0, 99999)
        self.rename_start.setValue(1)
        num_row.addWidget(self.rename_start)

        num_row.addWidget(QLabel("分隔符:"))
        self.rename_sep = QComboBox()
        self.rename_sep.addItems(["_", "-", " "])
        num_row.addWidget(self.rename_sep)
        settings_layout.addLayout(num_row)

        # 提示
        self.rename_hint = QLabel("提示: 自定义模式支持 {n} 编号, {d} 日期, {o} 原名, {e} 扩展名")
        self.rename_hint.setObjectName("subtitle")
        settings_layout.addWidget(self.rename_hint)

        # 按钮
        btn_row = QHBoxLayout()
        self.rename_preview_btn = QPushButton("📋 预览重命名")
        self.rename_preview_btn.clicked.connect(self._preview_rename)
        btn_row.addWidget(self.rename_preview_btn)

        self.rename_exec_btn = QPushButton("🚀 执行重命名")
        self.rename_exec_btn.setObjectName("primary")
        self.rename_exec_btn.setEnabled(False)
        self.rename_exec_btn.clicked.connect(self._exec_rename)
        btn_row.addWidget(self.rename_exec_btn)
        settings_layout.addLayout(btn_row)

        layout.addWidget(settings_card)

        # 预览表格
        preview_card = GradientCard()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        self.rename_table = QTableWidget()
        self.rename_table.setColumnCount(2)
        self.rename_table.setHorizontalHeaderLabels(["原文件名", "新文件名"])
        self.rename_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rename_table.setAlternatingRowColors(True)
        self.rename_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        preview_layout.addWidget(self.rename_table)

        layout.addWidget(preview_card)
        return tab

    def _create_cleaner_tab(self) -> QWidget:
        """空文件夹清理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        ctrl_card = GradientCard()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("📂 空文件夹查找与清理")
        title.setObjectName("title")
        ctrl_layout.addWidget(title)

        desc = QLabel("快速扫描并清理指定目录下所有空文件夹")
        desc.setObjectName("subtitle")
        ctrl_layout.addWidget(desc)

        btn_row = QHBoxLayout()
        self.empty_scan_btn = QPushButton("🔍 扫描空文件夹")
        self.empty_scan_btn.setObjectName("primary")
        self.empty_scan_btn.clicked.connect(self._scan_empty)
        btn_row.addWidget(self.empty_scan_btn)

        self.empty_clean_btn = QPushButton("🗑️ 清理全部")
        self.empty_clean_btn.setObjectName("danger")
        self.empty_clean_btn.setEnabled(False)
        self.empty_clean_btn.clicked.connect(self._clean_empty)
        btn_row.addWidget(self.empty_clean_btn)
        ctrl_layout.addLayout(btn_row)

        layout.addWidget(ctrl_card)

        # 结果列表
        result_card = GradientCard()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(8, 8, 8, 8)

        self.empty_list = QTextEdit()
        self.empty_list.setReadOnly(True)
        self.empty_list.setPlaceholderText("扫描结果将显示在这里...")
        result_layout.addWidget(self.empty_list)

        self.empty_info = QLabel("")
        self.empty_info.setObjectName("subtitle")
        result_layout.addWidget(self.empty_info)

        layout.addWidget(result_card)
        return tab

    def _create_large_tab(self) -> QWidget:
        """大文件查找选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        ctrl_card = GradientCard()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("📊 大文件查找")
        title.setObjectName("title")
        ctrl_layout.addWidget(title)

        desc = QLabel("查找占用空间最大的文件，帮助释放磁盘空间")
        desc.setObjectName("subtitle")
        ctrl_layout.addWidget(desc)

        num_row = QHBoxLayout()
        num_row.addWidget(QLabel("显示前:"))
        self.large_n = QSpinBox()
        self.large_n.setRange(5, 500)
        self.large_n.setValue(20)
        self.large_n.setSuffix(" 个")
        num_row.addWidget(self.large_n)
        num_row.addStretch()

        self.large_scan_btn = QPushButton("🔍 开始查找")
        self.large_scan_btn.setObjectName("primary")
        self.large_scan_btn.clicked.connect(self._scan_large)
        num_row.addWidget(self.large_scan_btn)
        ctrl_layout.addLayout(num_row)

        layout.addWidget(ctrl_card)

        # 结果表格
        result_card = GradientCard()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(8, 8, 8, 8)

        self.large_table = QTableWidget()
        self.large_table.setColumnCount(4)
        self.large_table.setHorizontalHeaderLabels(["排名", "文件名", "路径", "大小"])
        self.large_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.large_table.setAlternatingRowColors(True)
        self.large_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        result_layout.addWidget(self.large_table)

        self.large_info = QLabel("")
        self.large_info.setObjectName("subtitle")
        result_layout.addWidget(self.large_info)

        layout.addWidget(result_card)
        return tab

    # ---- 信号连接 ----

    def _connect_signals(self):
        pass  # 各处已在创建时连接

    # ---- 工具方法 ----

    def _get_dir(self) -> str:
        """获取当前选中的目录"""
        d = self._current_dir
        if not d or not os.path.isdir(d):
            QMessageBox.warning(self, "提示", "请先选择一个有效的文件夹！")
            return ""
        return d

    def _browse_folder(self):
        """浏览选择文件夹"""
        d = QFileDialog.getExistingDirectory(self, "选择文件夹", self._current_dir or str(Path.home()))
        if d:
            self._set_path(d)

    def _set_path(self, path: str):
        """设置当前路径"""
        if os.path.isdir(path):
            self._current_dir = path
            self.path_edit.setText(path)
            index = self.fs_model.index(path)
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
            self._update_dir_info(path)
            self._update_status(f"已选择: {path}")

    def _on_tree_clicked(self, index):
        """树形视图点击"""
        path = self.fs_model.filePath(index)
        if os.path.isdir(path):
            self._current_dir = path
            self.path_edit.setText(path)
            self._update_dir_info(path)

    def _update_dir_info(self, path: str):
        """更新目录信息"""
        try:
            file_count = 0
            dir_count = 0
            total_size = 0
            for root, dirs, files in os.walk(path):
                dir_count += len(dirs)
                for f in files:
                    file_count += 1
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            self.info_label.setText(
                f"📁 {path}\n"
                f"文件: {file_count} 个 | 文件夹: {dir_count} 个\n"
                f"总大小: {format_size(total_size)}"
            )
        except Exception as e:
            self.info_label.setText(f"无法读取目录信息: {e}")

    def _update_status(self, msg: str):
        """更新状态栏"""
        self.status_label.setText(msg)

    def _set_busy(self, busy: bool, msg: str = ""):
        """设置忙碌状态"""
        self.progress_bar.setVisible(busy)
        if msg:
            self._update_status(msg)
        if not busy:
            self.progress_bar.setValue(0)

    def _start_worker(self, worker):
        """启动工作线程"""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "提示", "有操作正在进行，请等待完成！")
            return False
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.finished_signal.connect(self._on_worker_done)
        worker.error_signal.connect(self._on_worker_error)
        worker.start()
        return True

    def _on_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self._update_status(msg)

    def _on_worker_done(self, result):
        self._set_busy(False, "操作完成")

    def _on_worker_error(self, error: str):
        self._set_busy(False, f"错误: {error}")
        QMessageBox.critical(self, "错误", f"操作失败:\n{error}")

    def _on_rename_mode_changed(self, index: int):
        """重命名模式改变"""
        if index == 0:
            self.rename_prefix.setPlaceholderText("输入前缀，如: photo")
            self.rename_sep.setEnabled(True)
            self.rename_start.setEnabled(True)
        elif index == 1:
            self.rename_prefix.setPlaceholderText("输入前缀，如: vacation")
            self.rename_sep.setEnabled(True)
            self.rename_start.setEnabled(False)
        else:
            self.rename_prefix.setPlaceholderText("如: photo_{n}_{o}{e}")
            self.rename_sep.setEnabled(False)
            self.rename_start.setEnabled(True)

    # ---- 功能实现 ----

    def _preview_type_org(self):
        """预览按类型整理"""
        d = self._get_dir()
        if not d:
            return
        from app.organizer import organize_by_type
        self._set_busy(True, "正在生成预览...")
        moves = organize_by_type(d)
        self.org_table.setRowCount(len(moves))
        for i, m in enumerate(moves):
            self.org_table.setItem(i, 0, QTableWidgetItem(m["src"]))
            self.org_table.setItem(i, 1, QTableWidgetItem(m["info"]))
        self._pending_type_moves = moves
        self.type_exec_btn.setEnabled(bool(moves))
        self._set_busy(False, f"预览完成，{len(moves)} 个文件将被整理")

    def _exec_type_org(self):
        """执行按类型整理"""
        moves = getattr(self, "_pending_type_moves", [])
        if not moves:
            return
        self._set_busy(True, "正在整理文件...")

        worker = OrganizeByTypeWorker(self._current_dir)
        worker.finished_signal.connect(self._on_type_org_done)
        self._start_worker(worker)

    def _on_type_org_done(self, result):
        results = result.get("results", [])
        self._last_results = results
        self.undo_btn.setEnabled(bool(results))
        success = sum(1 for r in results if r.get("status") == "success")
        QMessageBox.information(self, "完成", f"整理完成！成功移动 {success} 个文件。")
        self._update_dir_info(self._current_dir)
        self.org_table.setRowCount(0)
        self.type_exec_btn.setEnabled(False)

    def _preview_date_org(self):
        """预览按日期整理"""
        d = self._get_dir()
        if not d:
            return
        from app.organizer import organize_by_date
        self._set_busy(True, "正在生成预览...")
        moves = organize_by_date(d)
        self.org_table.setRowCount(len(moves))
        for i, m in enumerate(moves):
            self.org_table.setItem(i, 0, QTableWidgetItem(m["src"]))
            self.org_table.setItem(i, 1, QTableWidgetItem(m["info"]))
        self._pending_date_moves = moves
        self.date_exec_btn.setEnabled(bool(moves))
        self._set_busy(False, f"预览完成，{len(moves)} 个文件将被归档")

    def _exec_date_org(self):
        """执行按日期整理"""
        moves = getattr(self, "_pending_date_moves", [])
        if not moves:
            return
        self._set_busy(True, "正在归档文件...")

        worker = OrganizeByDateWorker(self._current_dir)
        worker.finished_signal.connect(self._on_date_org_done)
        self._start_worker(worker)

    def _on_date_org_done(self, result):
        results = result.get("results", [])
        self._last_results = results
        self.undo_btn.setEnabled(bool(results))
        success = sum(1 for r in results if r.get("status") == "success")
        QMessageBox.information(self, "完成", f"归档完成！成功移动 {success} 个文件。")
        self._update_dir_info(self._current_dir)
        self.org_table.setRowCount(0)
        self.date_exec_btn.setEnabled(False)

    def _scan_duplicates(self):
        """扫描重复文件"""
        d = self._get_dir()
        if not d:
            return
        self._set_busy(True, "正在扫描重复文件...")
        self._dup_data = {}

        worker = FindDuplicatesWorker(d)
        worker.finished_signal.connect(self._on_dup_scan_done)
        self._start_worker(worker)

    def _on_dup_scan_done(self, duplicates):
        self._dup_data = duplicates
        self.dup_table.setRowCount(0)

        row = 0
        for h, files in duplicates.items():
            for i, f in enumerate(files):
                self.dup_table.insertRow(row)
                # 第一组的第一个文件标记为"保留"
                if i == 0:
                    item = QTableWidgetItem("保留")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.dup_table.setItem(row, 0, item)
                else:
                    cb = QTableWidgetItem()
                    cb.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    cb.setCheckState(Qt.CheckState.Unchecked)
                    self.dup_table.setItem(row, 0, cb)

                self.dup_table.setItem(row, 1, QTableWidgetItem(f["name"]))
                self.dup_table.setItem(row, 2, QTableWidgetItem(f["path"]))
                self.dup_table.setItem(row, 3, QTableWidgetItem(format_size(f["size"])))
                self.dup_table.setItem(row, 4, QTableWidgetItem(h[:16] + "..."))
                row += 1

        total_groups = len(duplicates)
        total_files = sum(len(v) for v in duplicates.values())
        wasted = sum(v[0]["size"] * (len(v) - 1) for v in duplicates.values())
        self.dup_info.setText(f"找到 {total_groups} 组重复文件，共 {total_files} 个，可释放 {format_size(wasted)} 空间")
        self.dup_delete_btn.setEnabled(total_groups > 0)
        self._set_busy(False, f"扫描完成，找到 {total_groups} 组重复文件")

    def _delete_duplicates(self):
        """删除选中的重复文件"""
        to_delete = []
        for row in range(self.dup_table.rowCount()):
            item = self.dup_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                path = self.dup_table.item(row, 2).text()
                to_delete.append(path)

        if not to_delete:
            QMessageBox.information(self, "提示", "请先勾选要删除的文件！")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(to_delete)} 个文件吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = 0
        for path in to_delete:
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                errors += 1

        QMessageBox.information(self, "完成", f"删除完成！成功 {deleted} 个，失败 {errors} 个")
        self._scan_duplicates()
        self._update_dir_info(self._current_dir)

    def _preview_rename(self):
        """预览重命名"""
        d = self._get_dir()
        if not d:
            return

        mode_map = {0: "sequential", 1: "date", 2: "custom"}
        pattern = mode_map.get(self.rename_mode.currentIndex(), "sequential")
        prefix = self.rename_prefix.text().strip()
        start = self.rename_start.value()
        sep = self.rename_sep.currentText()

        self._set_busy(True, "正在生成重命名预览...")
        self._pending_renames = []

        worker = BatchRenamePreviewWorker(d, pattern, prefix, start, sep)
        worker.finished_signal.connect(self._on_rename_preview_done)
        self._start_worker(worker)

    def _on_rename_preview_done(self, renames):
        self._pending_renames = renames
        self.rename_table.setRowCount(len(renames))
        for i, r in enumerate(renames):
            self.rename_table.setItem(i, 0, QTableWidgetItem(r["old_name"]))
            self.rename_table.setItem(i, 1, QTableWidgetItem(r["new_name"]))
        self.rename_exec_btn.setEnabled(bool(renames))
        self._set_busy(False, f"预览完成，{len(renames)} 个文件将被重命名")

    def _exec_rename(self):
        """执行重命名"""
        renames = getattr(self, "_pending_renames", [])
        if not renames:
            return

        reply = QMessageBox.question(
            self, "确认重命名",
            f"确定要重命名 {len(renames)} 个文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True, "正在重命名文件...")

        worker = ExecuteRenamesWorker(renames)
        worker.finished_signal.connect(self._on_rename_done)
        self._start_worker(worker)

    def _on_rename_done(self, results):
        self._last_results = results
        self.undo_btn.setEnabled(True)
        success = sum(1 for r in results if r.get("status") == "success")
        QMessageBox.information(self, "完成", f"重命名完成！成功 {success} 个文件。")
        self.rename_table.setRowCount(0)
        self.rename_exec_btn.setEnabled(False)
        self._update_dir_info(self._current_dir)

    def _scan_empty(self):
        """扫描空文件夹"""
        d = self._get_dir()
        if not d:
            return
        self._set_busy(True, "正在扫描空文件夹...")
        self._empty_folders = []

        worker = FindEmptyFoldersWorker(d)
        worker.finished_signal.connect(self._on_empty_scan_done)
        self._start_worker(worker)

    def _on_empty_scan_done(self, folders):
        self._empty_folders = folders
        if folders:
            self.empty_list.setPlainText("\n".join(folders))
            self.empty_info.setText(f"找到 {len(folders)} 个空文件夹")
        else:
            self.empty_list.setPlainText("没有找到空文件夹 ✓")
            self.empty_info.setText("")
        self.empty_clean_btn.setEnabled(bool(folders))

    def _clean_empty(self):
        """清理空文件夹"""
        folders = getattr(self, "_empty_folders", [])
        if not folders:
            return

        reply = QMessageBox.question(
            self, "确认清理",
            f"确定要删除 {len(folders)} 个空文件夹吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True, "正在清理空文件夹...")

        worker = CleanEmptyFoldersWorker(folders)
        worker.finished_signal.connect(self._on_empty_clean_done)
        self._start_worker(worker)

    def _on_empty_clean_done(self, results):
        success = sum(1 for r in results if r.get("status") == "success")
        self.empty_list.setPlainText(f"清理完成，删除了 {success} 个空文件夹 ✓")
        self.empty_clean_btn.setEnabled(False)
        self.empty_info.setText("")
        self._update_dir_info(self._current_dir)

    def _scan_large(self):
        """扫描大文件"""
        d = self._get_dir()
        if not d:
            return
        self._set_busy(True, "正在扫描大文件...")

        worker = FindLargeFilesWorker(d, self.large_n.value())
        worker.finished_signal.connect(self._on_large_scan_done)
        self._start_worker(worker)

    def _on_large_scan_done(self, files):
        self.large_table.setRowCount(len(files))
        total = 0
        for i, f in enumerate(files):
            self.large_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.large_table.setItem(i, 1, QTableWidgetItem(f["name"]))
            self.large_table.setItem(i, 2, QTableWidgetItem(f["path"]))
            self.large_table.setItem(i, 3, QTableWidgetItem(format_size(f["size"])))
            total += f["size"]
        self.large_info.setText(f"显示前 {len(files)} 个大文件，共占用 {format_size(total)}")
        self._set_busy(False, f"扫描完成")

    def _undo_last(self):
        """撤销上次操作"""
        if not self._last_results:
            return

        reply = QMessageBox.question(
            self, "确认撤销",
            "确定要撤销上次操作吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True, "正在撤销操作...")

        worker = UndoWorker(self._last_results)
        worker.finished_signal.connect(self._on_undo_done)
        self._start_worker(worker)

    def _on_undo_done(self, undos):
        self._last_results = []
        self.undo_btn.setEnabled(False)
        QMessageBox.information(self, "完成", "撤销操作完成！")
        self._update_dir_info(self._current_dir)

    def closeEvent(self, event):
        """关闭事件"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        event.accept()
