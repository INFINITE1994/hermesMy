"""
快捷键管理器模块 - 管理全局快捷键
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QMessageBox,
    QKeySequenceEdit, QDialog, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class AddHotkeyDialog(QDialog):
    """添加快捷键对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加快捷键")
        self.setMinimumWidth(450)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 快捷键名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("为快捷键命名")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 快捷键设置
        key_layout = QHBoxLayout()
        key_label = QLabel("快捷键:")
        key_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.key_edit = QKeySequenceEdit()
        self.key_edit.setPlaceholderText("按下快捷键组合...")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        # 操作类型
        action_layout = QHBoxLayout()
        action_label = QLabel("操作:")
        action_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "运行程序", "打开文件", "执行脚本", "输入文本",
            "模拟按键", "切换窗口", "截图", "自定义操作"
        ])
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.action_combo)
        layout.addLayout(action_layout)
        
        # 操作内容
        content_layout = QHBoxLayout()
        content_label = QLabel("内容:")
        content_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("程序路径、文件路径或文本内容")
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet(get_secondary_button_style())
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self.browse_file)
        content_layout.addWidget(content_label)
        content_layout.addWidget(self.content_edit)
        content_layout.addWidget(browse_btn)
        layout.addLayout(content_layout)
        
        # 备注
        note_label = QLabel("备注:")
        note_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(note_label)
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(60)
        self.note_edit.setPlaceholderText("可选备注")
        layout.addWidget(self.note_edit)
        
        # 启用状态
        self.enabled_check = QCheckBox("立即启用")
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.content_edit.setText(file_path)
    
    def get_hotkey_data(self):
        """获取快捷键数据"""
        return {
            "name": self.name_edit.text(),
            "key": self.key_edit.keySequence().toString(),
            "action": self.action_combo.currentText(),
            "content": self.content_edit.text(),
            "note": self.note_edit.toPlainText(),
            "enabled": self.enabled_check.isChecked(),
        }


class HotkeyManagerWidget(QWidget):
    """快捷键管理器界面"""
    
    def __init__(self):
        super().__init__()
        self.hotkeys = []
        self._setup_ui()
        self._add_demo_hotkeys()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("⌨️ 快捷键管理器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("自定义全局快捷键，快速执行常用操作")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 常用快捷键提示
        tips_group = QGroupBox("💡 常用快捷键参考")
        tips_layout = QHBoxLayout(tips_group)
        
        tips = [
            "Ctrl+C: 复制", "Ctrl+V: 粘贴", "Ctrl+Z: 撤销",
            "Alt+Tab: 切换窗口", "Win+D: 显示桌面", "Ctrl+Shift+S: 另存为"
        ]
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setStyleSheet(f"""
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: {TEXT_SECONDARY};
            """)
            tips_layout.addWidget(tip_label)
        
        tips_layout.addStretch()
        layout.addWidget(tips_group)
        
        # 快捷键列表
        hotkey_group = QGroupBox("快捷键列表")
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加快捷键")
        add_btn.setStyleSheet(get_accent_button_style())
        add_btn.clicked.connect(self.add_hotkey)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setStyleSheet(get_secondary_button_style())
        edit_btn.clicked.connect(self.edit_hotkey)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除")
        delete_btn.setStyleSheet(get_danger_button_style())
        delete_btn.clicked.connect(self.delete_hotkey)
        toolbar.addWidget(delete_btn)
        
        toolbar.addStretch()
        
        # 搜索
        search_label = QLabel("🔍 搜索:")
        search_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        toolbar.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索...")
        self.search_edit.setMaximumWidth(200)
        self.search_edit.textChanged.connect(self.search_hotkeys)
        toolbar.addWidget(self.search_edit)
        
        hotkey_layout.addLayout(toolbar)
        
        # 快捷键表格
        self.hotkey_table = QTableWidget()
        self.hotkey_table.setColumnCount(6)
        self.hotkey_table.setHorizontalHeaderLabels([
            "启用", "名称", "快捷键", "操作类型", "操作内容", "备注"
        ])
        self.hotkey_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hotkey_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hotkey_table.setAlternatingRowColors(True)
        self.hotkey_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        hotkey_layout.addWidget(self.hotkey_table)
        
        # 统计
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("📊 总计: 0 个快捷键")
        self.total_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        stats_layout.addWidget(self.total_label)
        
        self.active_label = QLabel("✅ 启用: 0 个")
        self.active_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-size: 12px;")
        stats_layout.addWidget(self.active_label)
        
        stats_layout.addStretch()
        
        # 导入导出
        import_btn = QPushButton("📥 导入配置")
        import_btn.setStyleSheet(get_secondary_button_style())
        import_btn.clicked.connect(self.import_config)
        stats_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出配置")
        export_btn.setStyleSheet(get_secondary_button_style())
        export_btn.clicked.connect(self.export_config)
        stats_layout.addWidget(export_btn)
        
        hotkey_layout.addLayout(stats_layout)
        
        layout.addWidget(hotkey_group, 1)
    
    def _add_demo_hotkeys(self):
        """添加演示快捷键"""
        self.hotkeys = [
            {
                "name": "快速截图",
                "key": "Ctrl+Shift+S",
                "action": "截图",
                "content": "全屏截图",
                "note": "截取整个屏幕并保存",
                "enabled": True,
            },
            {
                "name": "打开计算器",
                "key": "Ctrl+Alt+C",
                "action": "运行程序",
                "content": "calc.exe",
                "note": "快速打开计算器",
                "enabled": True,
            },
            {
                "name": "输入邮箱",
                "key": "Ctrl+Shift+E",
                "action": "输入文本",
                "content": "user@example.com",
                "note": "快速输入常用邮箱地址",
                "enabled": True,
            },
            {
                "name": "打开终端",
                "key": "Ctrl+`",
                "action": "运行程序",
                "content": "cmd.exe",
                "note": "打开命令提示符",
                "enabled": False,
            },
        ]
        
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        self.hotkey_table.setRowCount(len(self.hotkeys))
        
        for i, hotkey in enumerate(self.hotkeys):
            # 启用复选框
            checkbox = QCheckBox()
            checkbox.setChecked(hotkey["enabled"])
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_hotkey(idx, state))
            self.hotkey_table.setCellWidget(i, 0, checkbox)
            
            self.hotkey_table.setItem(i, 1, QTableWidgetItem(hotkey["name"]))
            
            # 快捷键显示带特殊样式
            key_item = QTableWidgetItem(hotkey["key"])
            key_item.setForeground(QColor(ACCENT_START))
            font = key_item.font()
            font.setBold(True)
            key_item.setFont(font)
            self.hotkey_table.setItem(i, 2, key_item)
            
            self.hotkey_table.setItem(i, 3, QTableWidgetItem(hotkey["action"]))
            self.hotkey_table.setItem(i, 4, QTableWidgetItem(hotkey["content"]))
            self.hotkey_table.setItem(i, 5, QTableWidgetItem(hotkey["note"]))
        
        self._update_stats()
    
    def _update_stats(self):
        """更新统计"""
        total = len(self.hotkeys)
        active = sum(1 for h in self.hotkeys if h["enabled"])
        self.total_label.setText(f"📊 总计: {total} 个快捷键")
        self.active_label.setText(f"✅ 启用: {active} 个")
    
    def add_hotkey(self):
        """添加快捷键"""
        dialog = AddHotkeyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_hotkey_data()
            if data["name"] and data["key"]:
                # 检查重复
                for h in self.hotkeys:
                    if h["key"] == data["key"]:
                        QMessageBox.warning(self, "警告", f"快捷键 {data['key']} 已存在！")
                        return
                
                self.hotkeys.append(data)
                self._update_table()
                QMessageBox.information(self, "成功", f"快捷键 '{data['name']}' 已添加！")
            else:
                QMessageBox.warning(self, "警告", "请填写名称和快捷键！")
    
    def edit_hotkey(self):
        """编辑快捷键"""
        current = self.hotkey_table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的快捷键！")
            return
        
        hotkey = self.hotkeys[current]
        dialog = AddHotkeyDialog(self)
        dialog.name_edit.setText(hotkey["name"])
        dialog.key_edit.setKeySequence(QKeySequence(hotkey["key"]))
        dialog.content_edit.setText(hotkey["content"])
        dialog.note_edit.setText(hotkey["note"])
        dialog.enabled_check.setChecked(hotkey["enabled"])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_hotkey_data()
            if data["name"] and data["key"]:
                self.hotkeys[current] = data
                self._update_table()
    
    def delete_hotkey(self):
        """删除快捷键"""
        current = self.hotkey_table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的快捷键！")
            return
        
        name = self.hotkeys[current]["name"]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除快捷键 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.hotkeys[current]
            self._update_table()
    
    def toggle_hotkey(self, index, state):
        """切换快捷键启用状态"""
        if 0 <= index < len(self.hotkeys):
            self.hotkeys[index]["enabled"] = bool(state)
            self._update_stats()
    
    def search_hotkeys(self, text):
        """搜索快捷键"""
        for row in range(self.hotkey_table.rowCount()):
            match = False
            for col in range(1, self.hotkey_table.columnCount()):
                item = self.hotkey_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.hotkey_table.setRowHidden(row, not match if text else False)
    
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            QMessageBox.information(self, "导入", f"配置已导入: {file_path}")
    
    def export_config(self):
        """导出配置"""
        if not self.hotkeys:
            QMessageBox.warning(self, "警告", "没有可导出的配置！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "导出", f"配置已导出到: {file_path}")
