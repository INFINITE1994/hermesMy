"""
任务调度器模块 - 定时执行任务
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QFileDialog, QMessageBox,
    QDateTimeEdit, QCheckBox, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QThread
from PyQt6.QtGui import QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class AddTaskDialog(QDialog):
    """添加任务对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加定时任务")
        self.setMinimumWidth(500)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_label = QLabel("任务名称:")
        name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 80px;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入任务名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 执行类型
        type_layout = QHBoxLayout()
        type_label = QLabel("执行类型:")
        type_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 80px;")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["运行程序", "打开文件", "执行脚本", "显示消息"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 执行内容
        content_layout = QHBoxLayout()
        content_label = QLabel("执行内容:")
        content_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 80px;")
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("程序路径、文件路径或脚本内容")
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet(get_secondary_button_style())
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self.browse_file)
        content_layout.addWidget(content_label)
        content_layout.addWidget(self.content_edit)
        content_layout.addWidget(browse_btn)
        layout.addLayout(content_layout)
        
        # 触发时间
        time_layout = QHBoxLayout()
        time_label = QLabel("触发时间:")
        time_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 80px;")
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.datetime_edit)
        layout.addLayout(time_layout)
        
        # 重复设置
        repeat_layout = QHBoxLayout()
        repeat_label = QLabel("重复方式:")
        repeat_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 80px;")
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["不重复", "每天", "每周", "每月", "自定义"])
        repeat_layout.addWidget(repeat_label)
        repeat_layout.addWidget(self.repeat_combo)
        
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 365)
        self.repeat_spin.setValue(1)
        self.repeat_spin.setSuffix(" 分钟")
        self.repeat_spin.setVisible(False)
        repeat_layout.addWidget(self.repeat_spin)
        
        self.repeat_combo.currentTextChanged.connect(self.on_repeat_changed)
        layout.addLayout(repeat_layout)
        
        # 备注
        note_label = QLabel("备注:")
        note_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(note_label)
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(80)
        self.note_edit.setPlaceholderText("可选的任务备注")
        layout.addWidget(self.note_edit)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_repeat_changed(self, text):
        """重复方式改变"""
        self.repeat_spin.setVisible(text == "自定义")
        if text == "自定义":
            self.repeat_spin.setSuffix(" 分钟")
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.content_edit.setText(file_path)
    
    def get_task_data(self):
        """获取任务数据"""
        return {
            "name": self.name_edit.text(),
            "type": self.type_combo.currentText(),
            "content": self.content_edit.text(),
            "time": self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "repeat": self.repeat_combo.currentText(),
            "note": self.note_edit.toPlainText(),
            "enabled": True,
        }


class TaskSchedulerWidget(QWidget):
    """任务调度器界面"""
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self._setup_ui()
        self._add_demo_tasks()
        
        # 定时检查任务
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_tasks)
        self.check_timer.start(1000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("⏰ 任务调度器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 当前时间
        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"color: {ACCENT_END}; font-size: 14px;")
        self._update_time()
        title_layout.addWidget(self.time_label)
        
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("设置定时任务，支持一次性、每天、每周、每月重复执行")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("📊 总任务: 0")
        self.total_label.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
        """)
        stats_layout.addWidget(self.total_label)
        
        self.active_label = QLabel("✅ 活跃: 0")
        self.active_label.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            color: {SUCCESS_COLOR};
        """)
        stats_layout.addWidget(self.active_label)
        
        self.pending_label = QLabel("⏳ 待执行: 0")
        self.pending_label.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            color: {WARNING_COLOR};
        """)
        stats_layout.addWidget(self.pending_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 任务列表
        task_group = QGroupBox("任务列表")
        task_layout = QVBoxLayout(task_group)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加任务")
        add_btn.setStyleSheet(get_accent_button_style())
        add_btn.clicked.connect(self.add_task)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑任务")
        edit_btn.setStyleSheet(get_secondary_button_style())
        edit_btn.clicked.connect(self.edit_task)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除任务")
        delete_btn.setStyleSheet(get_danger_button_style())
        delete_btn.clicked.connect(self.delete_task)
        toolbar.addWidget(delete_btn)
        
        toolbar.addStretch()
        
        # 过滤
        filter_label = QLabel("显示:")
        filter_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        toolbar.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部任务", "仅启用", "仅禁用", "今天", "本周"])
        self.filter_combo.currentTextChanged.connect(self.filter_tasks)
        toolbar.addWidget(self.filter_combo)
        
        task_layout.addLayout(toolbar)
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "启用", "任务名称", "执行类型", "触发时间", "重复方式", "状态", "操作"
        ])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        task_layout.addWidget(self.task_table)
        
        layout.addWidget(task_group)
    
    def _update_time(self):
        """更新当前时间显示"""
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.time_label.setText(f"🕐 {current_time}")
        QTimer.singleShot(1000, self._update_time)
    
    def _add_demo_tasks(self):
        """添加演示任务"""
        demo_tasks = [
            {
                "name": "每日备份",
                "type": "执行脚本",
                "content": "backup.py",
                "time": QDateTime.currentDateTime().addSecs(7200).toString("yyyy-MM-dd HH:mm:ss"),
                "repeat": "每天",
                "note": "每日自动备份重要文件",
                "enabled": True,
            },
            {
                "name": "系统清理",
                "type": "运行程序",
                "content": "cleaner.exe",
                "time": QDateTime.currentDateTime().addSecs(14400).toString("yyyy-MM-dd HH:mm:ss"),
                "repeat": "每周",
                "note": "清理临时文件和缓存",
                "enabled": True,
            },
            {
                "name": "提醒喝水",
                "type": "显示消息",
                "content": "记得喝水休息！",
                "time": QDateTime.currentDateTime().addSecs(1800).toString("yyyy-MM-dd HH:mm:ss"),
                "repeat": "自定义",
                "note": "每30分钟提醒一次",
                "enabled": False,
            },
        ]
        
        self.tasks = demo_tasks
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        self.task_table.setRowCount(len(self.tasks))
        
        for i, task in enumerate(self.tasks):
            # 启用复选框
            checkbox = QCheckBox()
            checkbox.setChecked(task.get("enabled", True))
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_task(idx, state))
            self.task_table.setCellWidget(i, 0, checkbox)
            
            self.task_table.setItem(i, 1, QTableWidgetItem(task["name"]))
            self.task_table.setItem(i, 2, QTableWidgetItem(task["type"]))
            self.task_table.setItem(i, 3, QTableWidgetItem(task["time"]))
            self.task_table.setItem(i, 4, QTableWidgetItem(task["repeat"]))
            
            # 状态
            status = "待执行" if task.get("enabled", True) else "已禁用"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(SUCCESS_COLOR if task.get("enabled", True) else TEXT_SECONDARY))
            self.task_table.setItem(i, 5, status_item)
            
            # 操作按钮
            run_btn = QPushButton("立即执行")
            run_btn.setStyleSheet(get_secondary_button_style())
            run_btn.setFixedWidth(80)
            run_btn.clicked.connect(lambda checked, idx=i: self.run_task(idx))
            self.task_table.setCellWidget(i, 6, run_btn)
        
        self._update_stats()
    
    def _update_stats(self):
        """更新统计信息"""
        total = len(self.tasks)
        active = sum(1 for t in self.tasks if t.get("enabled", True))
        self.total_label.setText(f"📊 总任务: {total}")
        self.active_label.setText(f"✅ 活跃: {active}")
        self.pending_label.setText(f"⏳ 待执行: {active}")
    
    def add_task(self):
        """添加任务"""
        dialog = AddTaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            if task_data["name"]:
                self.tasks.append(task_data)
                self._update_table()
                QMessageBox.information(self, "成功", f"任务 '{task_data['name']}' 已添加！")
    
    def edit_task(self):
        """编辑任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的任务！")
            return
        
        # 简化：直接修改任务名称
        task = self.tasks[current_row]
        QMessageBox.information(self, "编辑任务", f"编辑任务: {task['name']}")
    
    def delete_task(self):
        """删除任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的任务！")
            return
        
        task_name = self.tasks[current_row]["name"]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务 '{task_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.tasks[current_row]
            self._update_table()
    
    def toggle_task(self, index, state):
        """切换任务启用状态"""
        if 0 <= index < len(self.tasks):
            self.tasks[index]["enabled"] = bool(state)
            self._update_stats()
    
    def run_task(self, index):
        """立即执行任务"""
        if 0 <= index < len(self.tasks):
            task = self.tasks[index]
            QMessageBox.information(self, "执行任务", f"正在执行任务: {task['name']}\n类型: {task['type']}\n内容: {task['content']}")
    
    def filter_tasks(self, filter_text):
        """过滤任务"""
        # 简化实现：显示所有
        self._update_table()
    
    def check_tasks(self):
        """检查是否有到期任务"""
        # 简化实现：仅更新显示
        pass
