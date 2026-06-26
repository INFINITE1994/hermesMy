"""历史记录标签页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QAbstractItemView, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from datetime import datetime


class HistoryTab(QWidget):
    """历史记录标签页"""

    item_selected = pyqtSignal(str)  # content

    def __init__(self, history_manager):
        super().__init__()
        self.history_manager = history_manager
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_row = QHBoxLayout()
        title = QLabel("📚 历史记录")
        title.setObjectName("title")
        title_row.addWidget(title)
        title_row.addStretch()

        # 搜索
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索内容...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        title_row.addWidget(self.search_input)

        # 刷新
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.refresh)
        title_row.addWidget(btn_refresh)

        layout.addLayout(title_row)

        subtitle = QLabel("查看和管理已生成的二维码历史")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 表格
        table_frame = QFrame()
        table_frame.setObjectName("card")
        table_layout = QVBoxLayout(table_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "类型", "内容", "时间"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self.table)

        # 底部操作
        bottom_row = QHBoxLayout()

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("选择一条记录查看详情...")
        self.detail_text.setMaximumHeight(120)
        bottom_row.addWidget(self.detail_text, 1)

        btn_col = QVBoxLayout()
        self.btn_copy = QPushButton("📋 复制内容")
        self.btn_copy.clicked.connect(self._copy_content)
        self.btn_delete = QPushButton("🗑️ 删除记录")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.clicked.connect(self._delete_record)
        self.btn_clear = QPushButton("💥 清空全部")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self._clear_all)
        btn_col.addWidget(self.btn_copy)
        btn_col.addWidget(self.btn_delete)
        btn_col.addWidget(self.btn_clear)
        btn_col.addStretch()
        bottom_row.addLayout(btn_col)

        table_layout.addLayout(bottom_row)

        # 统计
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("subtitle")
        table_layout.addWidget(self.stats_label)

        layout.addWidget(table_frame, 1)

    def refresh(self):
        """刷新列表"""
        records = self.history_manager.get_all()
        self._populate_table(records)

    def _populate_table(self, records: list[dict]):
        """填充表格"""
        self.table.setRowCount(len(records))
        type_labels = {
            "text": "📝 文本",
            "wifi": "📶 WiFi",
            "vcard": "👤 名片",
        }

        for i, record in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(record.get("id", ""))))

            qr_type = record.get("type", "text")
            self.table.setItem(i, 1, QTableWidgetItem(type_labels.get(qr_type, qr_type)))

            content = record.get("content", "")
            display = content[:100] + "..." if len(content) > 100 else content
            self.table.setItem(i, 2, QTableWidgetItem(display))

            ts = record.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            self.table.setItem(i, 3, QTableWidgetItem(ts))

        self.stats_label.setText(f"共 {len(records)} 条记录")

    def _on_search(self, text: str):
        """搜索"""
        if not text.strip():
            self.refresh()
            return
        records = self.history_manager.search(text.strip())
        self._populate_table(records)

    def _on_selection_changed(self):
        """选择变化"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.detail_text.clear()
            return

        row = rows[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            record_id = int(id_item.text())
            record = self.history_manager.get_by_id(record_id)
            if record:
                detail = f"类型: {record.get('type', 'text')}\n"
                detail += f"时间: {record.get('timestamp', '')}\n"
                detail += f"内容:\n{record.get('content', '')}"
                self.detail_text.setPlainText(detail)

    def _get_selected_id(self) -> int | None:
        """获取选中的记录ID"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            return int(id_item.text())
        return None

    def _copy_content(self):
        """复制内容"""
        record_id = self._get_selected_id()
        if record_id is None:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return

        record = self.history_manager.get_by_id(record_id)
        if record:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(record.get("content", ""))
            self.stats_label.setText("📋 已复制到剪贴板")

    def _delete_record(self):
        """删除记录"""
        record_id = self._get_selected_id()
        if record_id is None:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.delete(record_id)
            self.refresh()

    def _clear_all(self):
        """清空全部"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史记录吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear()
            self.refresh()
