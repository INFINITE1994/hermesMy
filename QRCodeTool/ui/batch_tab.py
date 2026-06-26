"""批量生成标签页"""
import os
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QLineEdit, QColorDialog,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor


class BatchWorker(QThread):
    """批量生成工作线程"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(int, int)  # success_count, fail_count
    error = pyqtSignal(str)

    def __init__(self, qr_generator, items, output_dir, fmt, fg_color, bg_color, size):
        super().__init__()
        self.qr_generator = qr_generator
        self.items = items
        self.output_dir = output_dir
        self.fmt = fmt
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.size = size
        self._running = True

    def run(self):
        success = 0
        fail = 0
        total = len(self.items)

        for i, item in enumerate(self.items):
            if not self._running:
                break

            content = item.strip()
            if not content:
                continue

            try:
                # 生成文件名
                safe_name = "".join(c for c in content[:30] if c.isalnum() or c in "._- ").strip()
                if not safe_name:
                    safe_name = f"qr_{i+1:04d}"
                filename = f"{safe_name}.{self.fmt}"
                filepath = os.path.join(self.output_dir, filename)

                # 避免重名
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{safe_name}_{counter}.{self.fmt}"
                    filepath = os.path.join(self.output_dir, filename)
                    counter += 1

                if self.fmt == "svg":
                    svg_data = self.qr_generator.generate_svg(
                        content, self.fg_color, self.bg_color
                    )
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(svg_data)
                else:
                    img = self.qr_generator.generate(
                        data=content,
                        fg_color=self.fg_color,
                        bg_color=self.bg_color,
                        size=self.size,
                    )
                    if self.fmt == "jpg" and img.mode == "RGBA":
                        img = img.convert("RGB")
                    img.save(filepath, quality=95)

                success += 1
                self.progress.emit(i + 1, total, f"✅ {filename}")
            except Exception as e:
                fail += 1
                self.progress.emit(i + 1, total, f"❌ {content[:20]}... 失败: {str(e)[:50]}")

        self.finished.emit(success, fail)

    def stop(self):
        self._running = False


class BatchTab(QWidget):
    """批量生成标签页"""

    def __init__(self, qr_generator, history_manager):
        super().__init__()
        self.qr_generator = qr_generator
        self.history_manager = history_manager
        self.worker = None
        self.items = []
        self.fg_color = "#ffffff"
        self.bg_color = "#000000"
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("📦 批量生成二维码")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("从CSV/TXT文件批量生成多个二维码")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 设置区域
        settings_frame = QFrame()
        settings_frame.setObjectName("card")
        settings_layout = QVBoxLayout(settings_frame)

        # 文件选择
        file_row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("选择包含内容的CSV或TXT文件...")
        self.file_path.setReadOnly(True)
        btn_file = QPushButton("📂 选择文件")
        btn_file.clicked.connect(self._select_file)
        btn_manual = QPushButton("✏️ 手动输入")
        btn_manual.clicked.connect(self._manual_input)
        file_row.addWidget(self.file_path, 1)
        file_row.addWidget(btn_file)
        file_row.addWidget(btn_manual)
        settings_layout.addLayout(file_row)

        # 输出设置
        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出目录...")
        self.output_path.setReadOnly(True)
        btn_output = QPushButton("📁 输出目录")
        btn_output.clicked.connect(self._select_output)

        output_row.addWidget(QLabel("输出目录:"))
        output_row.addWidget(self.output_path, 1)
        output_row.addWidget(btn_output)
        settings_layout.addLayout(output_row)

        # 格式和颜色
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("格式:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PNG", "JPG", "SVG"])
        opt_row.addWidget(self.fmt_combo)

        opt_row.addWidget(QLabel("尺寸:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 15)
        self.size_spin.setValue(8)
        opt_row.addWidget(self.size_spin)

        self.btn_fg = QPushButton("🎨 前景色")
        self.btn_fg.clicked.connect(self._pick_fg)
        self.btn_bg = QPushButton("🎨 背景色")
        self.btn_bg.clicked.connect(self._pick_bg)
        opt_row.addWidget(self.btn_fg)
        opt_row.addWidget(self.btn_bg)

        settings_layout.addLayout(opt_row)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("🚀 开始批量生成")
        self.btn_start.setObjectName("primary")
        self.btn_start.setMinimumHeight(44)
        self.btn_start.clicked.connect(self._start_batch)
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_batch)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        settings_layout.addLayout(btn_row)

        layout.addWidget(settings_frame)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # 预览表格
        preview_frame = QFrame()
        preview_frame.setObjectName("card")
        preview_layout = QVBoxLayout(preview_frame)

        preview_title = QLabel("📋 内容预览")
        preview_title.setObjectName("sectionTitle")
        preview_layout.addWidget(preview_title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["序号", "内容", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        preview_layout.addWidget(self.table)

        # 状态
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("subtitle")
        preview_layout.addWidget(self.status_label)

        layout.addWidget(preview_frame, 1)

    def _select_file(self):
        """选择输入文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "",
            "文本文件 (*.txt *.csv);;所有文件 (*.*)"
        )
        if path:
            self.file_path.setText(path)
            self._load_file(path)

    def _load_file(self, path: str):
        """加载文件内容"""
        self.items = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 尝试CSV解析
            if path.lower().endswith(".csv"):
                try:
                    reader = csv.reader(content.splitlines())
                    for row in reader:
                        if row:
                            self.items.append(row[0].strip())
                except Exception:
                    self.items = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                self.items = [line.strip() for line in content.splitlines() if line.strip()]

            # 更新表格
            self._update_table()
            self.status_label.setText(f"📂 已加载 {len(self.items)} 条数据")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败:\n{str(e)}")

    def _manual_input(self):
        """手动输入"""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getMultiLineText(
            self, "手动输入", "每行一个内容（文本/URL）:",
            "\n".join(self.items) if self.items else ""
        )
        if ok and text.strip():
            self.items = [line.strip() for line in text.splitlines() if line.strip()]
            self.file_path.setText(f"手动输入 ({len(self.items)} 条)")
            self._update_table()
            self.status_label.setText(f"✏️ 已输入 {len(self.items)} 条数据")

    def _select_output(self):
        """选择输出目录"""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_path.setText(path)

    def _pick_fg(self):
        """选前景色"""
        color = QColorDialog.getColor(QColor(self.fg_color), self, "前景色")
        if color.isValid():
            self.fg_color = color.name()

    def _pick_bg(self):
        """选背景色"""
        color = QColorDialog.getColor(QColor(self.bg_color), self, "背景色")
        if color.isValid():
            self.bg_color = color.name()

    def _update_table(self):
        """更新表格"""
        self.table.setRowCount(len(self.items))
        for i, item in enumerate(self.items):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            content_display = item[:80] + "..." if len(item) > 80 else item
            self.table.setItem(i, 1, QTableWidgetItem(content_display))
            self.table.setItem(i, 2, QTableWidgetItem("待生成"))

    def _start_batch(self):
        """开始批量生成"""
        if not self.items:
            QMessageBox.warning(self, "提示", "请先加载数据文件或手动输入内容")
            return

        output_dir = self.output_path.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)

        fmt = self.fmt_combo.currentText().lower()

        # 重置表格状态
        for i in range(self.table.rowCount()):
            self.table.setItem(i, 2, QTableWidgetItem("等待中..."))

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.items))

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker = BatchWorker(
            self.qr_generator, self.items, output_dir, fmt,
            self.fg_color, self.bg_color, self.size_spin.value()
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_batch(self):
        """停止批量生成"""
        if self.worker:
            self.worker.stop()

    def _on_progress(self, current, total, message):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total}")

        # 更新表格
        row = current - 1
        if 0 <= row < self.table.rowCount():
            status = "✅ 成功" if "✅" in message else "❌ 失败"
            self.table.setItem(row, 2, QTableWidgetItem(status))
            self.table.scrollToItem(self.table.item(row, 0))

        self.status_label.setText(message)

    def _on_finished(self, success, fail):
        """批量生成完成"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText(f"🎉 完成！成功: {success}，失败: {fail}")

        if fail == 0:
            QMessageBox.information(self, "完成", f"批量生成完成！\n成功生成 {success} 个二维码")
        else:
            QMessageBox.warning(self, "完成", f"批量生成完成\n成功: {success}，失败: {fail}")
