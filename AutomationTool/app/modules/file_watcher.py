"""
文件监控器模块 - 监控文件夹变化并触发操作
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QMessageBox,
    QTextEdit, QListWidget, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDir
from PyQt6.QtGui import QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class FileWatcherWidget(QWidget):
    """文件监控器界面"""
    
    def __init__(self):
        super().__init__()
        self.watchers = []
        self.events = []
        self._setup_ui()
        self._add_demo_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("📁 文件监控器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("实时监控文件夹变化，当文件被创建、修改或删除时触发自动化操作")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 主内容区
        content_layout = QHBoxLayout()
        
        # 左侧：监控配置
        left_panel = QGroupBox("监控配置")
        left_layout = QVBoxLayout(left_panel)
        
        # 添加监控
        add_group = QGroupBox("添加新监控")
        add_layout = QVBoxLayout(add_group)
        
        # 监控路径
        path_layout = QHBoxLayout()
        path_label = QLabel("监控路径:")
        path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 70px;")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择要监控的文件夹...")
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet(get_secondary_button_style())
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        add_layout.addLayout(path_layout)
        
        # 监控事件类型
        events_layout = QHBoxLayout()
        events_label = QLabel("监控事件:")
        events_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 70px;")
        events_layout.addWidget(events_label)
        
        self.create_check = QCheckBox("文件创建")
        self.create_check.setChecked(True)
        events_layout.addWidget(self.create_check)
        
        self.modify_check = QCheckBox("文件修改")
        self.modify_check.setChecked(True)
        events_layout.addWidget(self.modify_check)
        
        self.delete_check = QCheckBox("文件删除")
        self.delete_check.setChecked(True)
        events_layout.addWidget(self.delete_check)
        
        self.rename_check = QCheckBox("文件重命名")
        self.rename_check.setChecked(True)
        events_layout.addWidget(self.rename_check)
        
        events_layout.addStretch()
        add_layout.addLayout(events_layout)
        
        # 文件过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("文件过滤:")
        filter_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 70px;")
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("例如: *.txt, *.py, *.jpg (留空监控所有文件)")
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_edit)
        add_layout.addLayout(filter_layout)
        
        # 触发操作
        action_layout = QHBoxLayout()
        action_label = QLabel("触发操作:")
        action_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 70px;")
        self.action_combo = QComboBox()
        self.action_combo.addItems(["记录日志", "显示通知", "运行程序", "复制文件", "移动文件", "发送邮件"])
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.action_combo)
        add_layout.addLayout(action_layout)
        
        # 添加按钮
        add_btn = QPushButton("➕ 添加监控")
        add_btn.setStyleSheet(get_accent_button_style())
        add_btn.clicked.connect(self.add_watcher)
        add_layout.addWidget(add_btn)
        
        left_layout.addWidget(add_group)
        
        # 监控列表
        watcher_list_group = QGroupBox("活跃监控")
        watcher_list_layout = QVBoxLayout(watcher_list_group)
        
        self.watcher_list = QListWidget()
        self.watcher_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #1a1a3a;
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_START}33;
            }}
        """)
        watcher_list_layout.addWidget(self.watcher_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        start_btn = QPushButton("▶ 启动监控")
        start_btn.setStyleSheet(get_success_button_style())
        start_btn.clicked.connect(self.start_watcher)
        btn_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹ 停止监控")
        stop_btn.setStyleSheet(get_danger_button_style())
        stop_btn.clicked.connect(self.stop_watcher)
        btn_layout.addWidget(stop_btn)
        
        remove_btn = QPushButton("🗑️ 移除监控")
        remove_btn.setStyleSheet(get_secondary_button_style())
        remove_btn.clicked.connect(self.remove_watcher)
        btn_layout.addWidget(remove_btn)
        
        watcher_list_layout.addLayout(btn_layout)
        left_layout.addWidget(watcher_list_group)
        
        content_layout.addWidget(left_panel, 1)
        
        # 右侧：事件日志
        right_panel = QGroupBox("事件日志")
        right_layout = QVBoxLayout(right_panel)
        
        # 日志工具栏
        log_toolbar = QHBoxLayout()
        
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        log_toolbar.addWidget(self.auto_scroll_check)
        
        log_toolbar.addStretch()
        
        clear_log_btn = QPushButton("🧹 清空日志")
        clear_log_btn.setStyleSheet(get_secondary_button_style())
        clear_log_btn.clicked.connect(self.clear_log)
        log_toolbar.addWidget(clear_log_btn)
        
        export_btn = QPushButton("📤 导出日志")
        export_btn.setStyleSheet(get_secondary_button_style())
        export_btn.clicked.connect(self.export_log)
        log_toolbar.addWidget(export_btn)
        
        right_layout.addLayout(log_toolbar)
        
        # 事件日志表格
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(4)
        self.event_table.setHorizontalHeaderLabels(["时间", "事件类型", "文件路径", "详情"])
        self.event_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setAlternatingRowColors(True)
        self.event_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        right_layout.addWidget(self.event_table)
        
        # 统计
        stats_layout = QHBoxLayout()
        self.event_count_label = QLabel("📊 事件总数: 0")
        self.event_count_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        stats_layout.addWidget(self.event_count_label)
        
        self.watcher_count_label = QLabel("👁️ 活跃监控: 0")
        self.watcher_count_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        stats_layout.addWidget(self.watcher_count_label)
        
        stats_layout.addStretch()
        right_layout.addLayout(stats_layout)
        
        content_layout.addWidget(right_panel, 1)
        
        layout.addLayout(content_layout, 1)
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择监控文件夹")
        if folder:
            self.path_edit.setText(folder)
    
    def add_watcher(self):
        """添加监控"""
        path = self.path_edit.text()
        if not path:
            QMessageBox.warning(self, "警告", "请选择监控路径！")
            return
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "警告", "路径不存在！")
            return
        
        # 获取监控事件
        events = []
        if self.create_check.isChecked():
            events.append("创建")
        if self.modify_check.isChecked():
            events.append("修改")
        if self.delete_check.isChecked():
            events.append("删除")
        if self.rename_check.isChecked():
            events.append("重命名")
        
        if not events:
            QMessageBox.warning(self, "警告", "请至少选择一种监控事件！")
            return
        
        watcher = {
            "path": path,
            "events": events,
            "filter": self.filter_edit.text(),
            "action": self.action_combo.currentText(),
            "active": True,
        }
        
        self.watchers.append(watcher)
        self._update_watcher_list()
        self._update_stats()
        
        # 清空输入
        self.path_edit.clear()
        self.filter_edit.clear()
        
        QMessageBox.information(self, "成功", f"已添加监控: {path}")
    
    def start_watcher(self):
        """启动选中的监控"""
        current = self.watcher_list.currentRow()
        if current >= 0 and current < len(self.watchers):
            self.watchers[current]["active"] = True
            self._update_watcher_list()
            self._update_stats()
    
    def stop_watcher(self):
        """停止选中的监控"""
        current = self.watcher_list.currentRow()
        if current >= 0 and current < len(self.watchers):
            self.watchers[current]["active"] = False
            self._update_watcher_list()
            self._update_stats()
    
    def remove_watcher(self):
        """移除选中的监控"""
        current = self.watcher_list.currentRow()
        if current >= 0 and current < len(self.watchers):
            reply = QMessageBox.question(
                self, "确认", "确定要移除此监控吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.watchers[current]
                self._update_watcher_list()
                self._update_stats()
    
    def _update_watcher_list(self):
        """更新监控列表"""
        self.watcher_list.clear()
        for w in self.watchers:
            status = "🟢" if w["active"] else "🔴"
            events_str = ", ".join(w["events"])
            self.watcher_list.addItem(
                f"{status} {w['path']}\n   事件: {events_str} | 操作: {w['action']}"
            )
    
    def _update_stats(self):
        """更新统计"""
        active = sum(1 for w in self.watchers if w["active"])
        self.event_count_label.setText(f"📊 事件总数: {len(self.events)}")
        self.watcher_count_label.setText(f"👁️ 活跃监控: {active}")
    
    def _add_demo_data(self):
        """添加演示数据"""
        self.watchers = [
            {
                "path": "C:\\Users\\Documents",
                "events": ["创建", "修改"],
                "filter": "*.txt",
                "action": "记录日志",
                "active": True,
            },
            {
                "path": "C:\\Downloads",
                "events": ["创建"],
                "filter": "",
                "action": "显示通知",
                "active": True,
            },
        ]
        
        self.events = [
            ("2024-01-15 10:30:15", "创建", "C:\\Documents\\report.txt", "新文件已创建"),
            ("2024-01-15 10:31:22", "修改", "C:\\Documents\\data.csv", "文件内容已更新"),
            ("2024-01-15 10:32:45", "创建", "C:\\Downloads\\setup.exe", "下载完成"),
        ]
        
        self._update_watcher_list()
        self._update_event_table()
        self._update_stats()
    
    def _update_event_table(self):
        """更新事件表格"""
        self.event_table.setRowCount(len(self.events))
        for i, event in enumerate(self.events):
            self.event_table.setItem(i, 0, QTableWidgetItem(event[0]))
            
            # 事件类型带颜色
            event_type_item = QTableWidgetItem(event[1])
            if event[1] == "创建":
                event_type_item.setForeground(QColor(SUCCESS_COLOR))
            elif event[1] == "修改":
                event_type_item.setForeground(QColor(WARNING_COLOR))
            elif event[1] == "删除":
                event_type_item.setForeground(QColor(ERROR_COLOR))
            self.event_table.setItem(i, 1, event_type_item)
            
            self.event_table.setItem(i, 2, QTableWidgetItem(event[2]))
            self.event_table.setItem(i, 3, QTableWidgetItem(event[3]))
    
    def clear_log(self):
        """清空日志"""
        self.events.clear()
        self._update_event_table()
        self._update_stats()
    
    def export_log(self):
        """导出日志"""
        if not self.events:
            QMessageBox.warning(self, "警告", "没有可导出的日志！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "文本文件 (*.txt);;CSV文件 (*.csv)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for event in self.events:
                        f.write('\t'.join(event) + '\n')
                QMessageBox.information(self, "成功", f"日志已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
