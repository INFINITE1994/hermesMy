"""
文本扩展器模块 - 缩写词自动扩展为完整文本
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox,
    QDialog, QDialogButtonBox, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR
)


class AddSnippetDialog(QDialog):
    """添加文本片段对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加文本片段")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("为片段命名（便于管理）")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 缩写词
        abbr_layout = QHBoxLayout()
        abbr_label = QLabel("缩写词:")
        abbr_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.abbr_edit = QLineEdit()
        self.abbr_edit.setPlaceholderText("输入缩写词，例如: eml, addr, sig")
        abbr_layout.addWidget(abbr_label)
        abbr_layout.addWidget(self.abbr_edit)
        layout.addLayout(abbr_layout)
        
        # 触发方式
        trigger_layout = QHBoxLayout()
        trigger_label = QLabel("触发方式:")
        trigger_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["输入后自动扩展", "按Tab键扩展", "按空格键扩展", "按Enter键扩展"])
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_combo)
        layout.addLayout(trigger_layout)
        
        # 扩展文本
        expand_label = QLabel("扩展文本:")
        expand_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(expand_label)
        
        self.expand_edit = QTextEdit()
        self.expand_edit.setPlaceholderText("输入要扩展的完整文本...\n\n支持变量:\n{{date}} - 当前日期\n{{time}} - 当前时间\n{{clipboard}} - 剪贴板内容")
        self.expand_edit.setMinimumHeight(150)
        layout.addWidget(self.expand_edit)
        
        # 变量插入按钮
        var_layout = QHBoxLayout()
        var_label = QLabel("插入变量:")
        var_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        var_layout.addWidget(var_label)
        
        variables = [
            ("{{date}}", "当前日期"),
            ("{{time}}", "当前时间"),
            ("{{datetime}}", "日期时间"),
            ("{{clipboard}}", "剪贴板"),
            ("{{cursor}}", "光标位置"),
        ]
        
        for var, tooltip in variables:
            btn = QPushButton(var)
            btn.setStyleSheet(get_secondary_button_style())
            btn.setToolTip(tooltip)
            btn.setFixedWidth(90)
            btn.clicked.connect(lambda checked, v=var: self.insert_variable(v))
            var_layout.addWidget(btn)
        
        var_layout.addStretch()
        layout.addLayout(var_layout)
        
        # 分组
        group_layout = QHBoxLayout()
        group_label = QLabel("分组:")
        group_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.group_combo = QComboBox()
        self.group_combo.addItems(["默认", "邮件", "地址", "代码", "签名", "自定义"])
        self.group_combo.setEditable(True)
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)
        
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
    
    def insert_variable(self, var):
        """插入变量"""
        self.expand_edit.insertPlainText(var)
    
    def get_snippet_data(self):
        """获取片段数据"""
        return {
            "name": self.name_edit.text(),
            "abbreviation": self.abbr_edit.text(),
            "trigger": self.trigger_combo.currentText(),
            "expanded": self.expand_edit.toPlainText(),
            "group": self.group_combo.currentText(),
            "enabled": self.enabled_check.isChecked(),
            "usage_count": 0,
        }


class TextExpanderWidget(QWidget):
    """文本扩展器界面"""
    
    def __init__(self):
        super().__init__()
        self.snippets = []
        self._setup_ui()
        self._add_demo_snippets()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("📝 文本扩展器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("设置缩写词自动扩展为完整文本，支持变量插入，提高输入效率")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 使用说明
        tips_group = QGroupBox("💡 使用说明")
        tips_layout = QVBoxLayout(tips_group)
        
        tips = [
            "• 设置缩写词和对应的完整文本",
            "• 输入缩写词后，根据触发方式自动扩展",
            "• 支持插入日期、时间、剪贴板等变量",
            "• 可按分组管理文本片段",
        ]
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            tips_layout.addWidget(tip_label)
        
        layout.addWidget(tips_group)
        
        # 主内容区
        content_layout = QHBoxLayout()
        
        # 左侧：片段列表
        left_panel = QGroupBox("文本片段")
        left_layout = QVBoxLayout(left_panel)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加片段")
        add_btn.setStyleSheet(get_accent_button_style())
        add_btn.clicked.connect(self.add_snippet)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setStyleSheet(get_secondary_button_style())
        edit_btn.clicked.connect(self.edit_snippet)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除")
        delete_btn.setStyleSheet(get_danger_button_style())
        delete_btn.clicked.connect(self.delete_snippet)
        toolbar.addWidget(delete_btn)
        
        toolbar.addStretch()
        
        # 搜索
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索片段...")
        self.search_edit.setMaximumWidth(200)
        self.search_edit.textChanged.connect(self.search_snippets)
        toolbar.addWidget(self.search_edit)
        
        left_layout.addLayout(toolbar)
        
        # 片段表格
        self.snippet_table = QTableWidget()
        self.snippet_table.setColumnCount(5)
        self.snippet_table.setHorizontalHeaderLabels([
            "启用", "缩写词", "名称", "触发方式", "使用次数"
        ])
        self.snippet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.snippet_table.setAlternatingRowColors(True)
        self.snippet_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        self.snippet_table.currentItemChanged.connect(self.preview_snippet)
        left_layout.addWidget(self.snippet_table)
        
        # 统计
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("📊 总计: 0 个片段")
        self.total_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        stats_layout.addWidget(self.total_label)
        stats_layout.addStretch()
        
        # 导入导出
        import_btn = QPushButton("📥 导入")
        import_btn.setStyleSheet(get_secondary_button_style())
        import_btn.clicked.connect(self.import_snippets)
        stats_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.setStyleSheet(get_secondary_button_style())
        export_btn.clicked.connect(self.export_snippets)
        stats_layout.addWidget(export_btn)
        
        left_layout.addLayout(stats_layout)
        
        content_layout.addWidget(left_panel, 1)
        
        # 右侧：预览
        right_panel = QGroupBox("预览")
        right_layout = QVBoxLayout(right_panel)
        
        # 预览内容
        self.preview_name = QLabel("选择一个片段查看预览")
        self.preview_name.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ACCENT_START};")
        right_layout.addWidget(self.preview_name)
        
        self.preview_abbr = QLabel("")
        self.preview_abbr.setStyleSheet(f"font-size: 14px; color: {TEXT_SECONDARY};")
        right_layout.addWidget(self.preview_abbr)
        
        # 分隔线
        separator = QLabel("─" * 40)
        separator.setStyleSheet(f"color: #1a1a3a;")
        right_layout.addWidget(separator)
        
        expand_label = QLabel("扩展文本:")
        expand_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        right_layout.addWidget(expand_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }}
        """)
        right_layout.addWidget(self.preview_text)
        
        # 测试区域
        test_group = QGroupBox("🧪 测试区域")
        test_layout = QVBoxLayout(test_group)
        
        test_hint = QLabel("在此输入缩写词测试扩展效果:")
        test_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        test_layout.addWidget(test_hint)
        
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("输入缩写词...")
        self.test_input.textChanged.connect(self.test_expand)
        test_layout.addWidget(self.test_input)
        
        self.test_result = QLabel("")
        self.test_result.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 6px;
            padding: 12px;
            font-size: 13px;
            color: {SUCCESS_COLOR};
        """)
        self.test_result.setWordWrap(True)
        test_layout.addWidget(self.test_result)
        
        right_layout.addWidget(test_group)
        
        content_layout.addWidget(right_panel, 1)
        
        layout.addLayout(content_layout, 1)
    
    def _add_demo_snippets(self):
        """添加演示片段"""
        self.snippets = [
            {
                "name": "邮箱地址",
                "abbreviation": "eml",
                "trigger": "输入后自动扩展",
                "expanded": "user@example.com",
                "group": "默认",
                "enabled": True,
                "usage_count": 45,
            },
            {
                "name": "家庭地址",
                "abbreviation": "addr",
                "trigger": "按Tab键扩展",
                "expanded": "北京市朝阳区xxx街道xxx号",
                "group": "地址",
                "enabled": True,
                "usage_count": 23,
            },
            {
                "name": "当前日期",
                "abbreviation": "td",
                "trigger": "输入后自动扩展",
                "expanded": "{{date}}",
                "group": "默认",
                "enabled": True,
                "usage_count": 67,
            },
            {
                "name": "邮件签名",
                "abbreviation": "sig",
                "trigger": "按Tab键扩展",
                "expanded": "此致\n敬礼\n张三\n电话: 13800138000",
                "group": "签名",
                "enabled": True,
                "usage_count": 34,
            },
            {
                "name": "代码模板",
                "abbreviation": "pydef",
                "trigger": "按Tab键扩展",
                "expanded": "def function_name():\n    \"\"\"函数说明\"\"\"\n    pass",
                "group": "代码",
                "enabled": False,
                "usage_count": 12,
            },
        ]
        
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        self.snippet_table.setRowCount(len(self.snippets))
        
        for i, snippet in enumerate(self.snippets):
            # 启用复选框
            checkbox = QCheckBox()
            checkbox.setChecked(snippet["enabled"])
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_snippet(idx, state))
            self.snippet_table.setCellWidget(i, 0, checkbox)
            
            # 缩写词带颜色
            abbr_item = QTableWidgetItem(snippet["abbreviation"])
            abbr_item.setForeground(QColor(ACCENT_START))
            font = abbr_item.font()
            font.setBold(True)
            abbr_item.setFont(font)
            self.snippet_table.setItem(i, 1, abbr_item)
            
            self.snippet_table.setItem(i, 2, QTableWidgetItem(snippet["name"]))
            self.snippet_table.setItem(i, 3, QTableWidgetItem(snippet["trigger"]))
            
            # 使用次数
            usage_item = QTableWidgetItem(str(snippet["usage_count"]))
            usage_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.snippet_table.setItem(i, 4, usage_item)
        
        self.total_label.setText(f"📊 总计: {len(self.snippets)} 个片段")
    
    def preview_snippet(self, current, previous):
        """预览选中的片段"""
        if current is None:
            return
        
        row = current.row()
        if 0 <= row < len(self.snippets):
            snippet = self.snippets[row]
            self.preview_name.setText(snippet["name"])
            self.preview_abbr.setText(f"缩写词: {snippet['abbreviation']} | 触发: {snippet['trigger']}")
            
            # 处理变量
            expanded = snippet["expanded"]
            expanded = expanded.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
            expanded = expanded.replace("{{time}}", datetime.now().strftime("%H:%M:%S"))
            expanded = expanded.replace("{{datetime}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            self.preview_text.setText(expanded)
    
    def test_expand(self, text):
        """测试扩展"""
        if not text:
            self.test_result.setText("")
            return
        
        for snippet in self.snippets:
            if snippet["enabled"] and snippet["abbreviation"] == text:
                expanded = snippet["expanded"]
                expanded = expanded.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
                expanded = expanded.replace("{{time}}", datetime.now().strftime("%H:%M:%S"))
                expanded = expanded.replace("{{datetime}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.test_result.setText(f"✅ 匹配: {snippet['name']}\n\n{expanded}")
                return
        
        self.test_result.setText("❌ 未找到匹配的缩写词")
    
    def add_snippet(self):
        """添加片段"""
        dialog = AddSnippetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_snippet_data()
            if data["name"] and data["abbreviation"]:
                # 检查重复
                for s in self.snippets:
                    if s["abbreviation"] == data["abbreviation"]:
                        QMessageBox.warning(self, "警告", f"缩写词 '{data['abbreviation']}' 已存在！")
                        return
                
                self.snippets.append(data)
                self._update_table()
                QMessageBox.information(self, "成功", f"片段 '{data['name']}' 已添加！")
            else:
                QMessageBox.warning(self, "警告", "请填写名称和缩写词！")
    
    def edit_snippet(self):
        """编辑片段"""
        current = self.snippet_table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的片段！")
            return
        
        snippet = self.snippets[current]
        dialog = AddSnippetDialog(self)
        dialog.name_edit.setText(snippet["name"])
        dialog.abbr_edit.setText(snippet["abbreviation"])
        dialog.expand_edit.setText(snippet["expanded"])
        dialog.enabled_check.setChecked(snippet["enabled"])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_snippet_data()
            if data["name"] and data["abbreviation"]:
                data["usage_count"] = snippet["usage_count"]
                self.snippets[current] = data
                self._update_table()
    
    def delete_snippet(self):
        """删除片段"""
        current = self.snippet_table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的片段！")
            return
        
        name = self.snippets[current]["name"]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除片段 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.snippets[current]
            self._update_table()
    
    def toggle_snippet(self, index, state):
        """切换片段启用状态"""
        if 0 <= index < len(self.snippets):
            self.snippets[index]["enabled"] = bool(state)
    
    def search_snippets(self, text):
        """搜索片段"""
        for row in range(self.snippet_table.rowCount()):
            match = False
            for col in range(1, self.snippet_table.columnCount()):
                item = self.snippet_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.snippet_table.setRowHidden(row, not match if text else False)
    
    def import_snippets(self):
        """导入片段"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入片段", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            QMessageBox.information(self, "导入", f"片段已导入: {file_path}")
    
    def export_snippets(self):
        """导出片段"""
        if not self.snippets:
            QMessageBox.warning(self, "警告", "没有可导出的片段！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出片段", "", "JSON文件 (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "导出", f"片段已导出到: {file_path}")
