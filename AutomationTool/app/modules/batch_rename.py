"""
批量重命名模块 - 批量重命名文件
"""

import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QMessageBox,
    QSpinBox, QRadioButton, QButtonGroup, QFrame, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class BatchRenameWidget(QWidget):
    """批量重命名界面"""
    
    def __init__(self):
        super().__init__()
        self.files = []
        self.preview_names = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("📋 批量重命名")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("批量重命名文件，支持正则替换、序号填充、大小写转换等多种模式")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 主内容区
        content_layout = QHBoxLayout()
        
        # 左侧：配置面板
        left_panel = QGroupBox("重命名配置")
        left_layout = QVBoxLayout(left_panel)
        
        # 文件夹选择
        folder_layout = QHBoxLayout()
        folder_label = QLabel("文件夹:")
        folder_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择包含文件的文件夹...")
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet(get_secondary_button_style())
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(browse_btn)
        left_layout.addLayout(folder_layout)
        
        # 文件过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("过滤:")
        filter_label.setStyleSheet(f"color: {TEXT_SECONDARY}; min-width: 60px;")
        self.filter_combo = QComboBox()
        self.filter_combo.setEditable(True)
        self.filter_combo.addItems([
            "所有文件", "*.txt", "*.jpg", "*.png", "*.pdf",
            "*.doc", "*.docx", "*.xls", "*.xlsx", "*.py", "*.js"
        ])
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        
        # 加载按钮
        load_btn = QPushButton("📂 加载文件")
        load_btn.setStyleSheet(get_accent_button_style())
        load_btn.clicked.connect(self.load_files)
        filter_layout.addWidget(load_btn)
        left_layout.addLayout(filter_layout)
        
        # 重命名模式
        mode_group = QGroupBox("重命名模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup()
        
        # 模式1: 查找替换
        self.replace_radio = QRadioButton("查找替换")
        self.replace_radio.setChecked(True)
        self.mode_group.addButton(self.replace_radio, 0)
        mode_layout.addWidget(self.replace_radio)
        
        replace_layout = QHBoxLayout()
        replace_layout.setContentsMargins(20, 0, 0, 0)
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("查找内容")
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("替换为")
        self.regex_check = QCheckBox("正则表达式")
        replace_layout.addWidget(self.find_edit)
        replace_layout.addWidget(QLabel("→"))
        replace_layout.addWidget(self.replace_edit)
        replace_layout.addWidget(self.regex_check)
        mode_layout.addLayout(replace_layout)
        
        # 模式2: 添加前后缀
        self.affix_radio = QRadioButton("添加前缀/后缀")
        self.mode_group.addButton(self.affix_radio, 1)
        mode_layout.addWidget(self.affix_radio)
        
        affix_layout = QHBoxLayout()
        affix_layout.setContentsMargins(20, 0, 0, 0)
        prefix_label = QLabel("前缀:")
        prefix_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("添加前缀")
        suffix_label = QLabel("后缀:")
        suffix_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("添加后缀")
        affix_layout.addWidget(prefix_label)
        affix_layout.addWidget(self.prefix_edit)
        affix_layout.addWidget(suffix_label)
        affix_layout.addWidget(self.suffix_edit)
        mode_layout.addLayout(affix_layout)
        
        # 模式3: 序号填充
        self.sequence_radio = QRadioButton("序号填充")
        self.mode_group.addButton(self.sequence_radio, 2)
        mode_layout.addWidget(self.sequence_radio)
        
        seq_layout = QHBoxLayout()
        seq_layout.setContentsMargins(20, 0, 0, 0)
        seq_name_label = QLabel("名称模板:")
        seq_name_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.seq_name_edit = QLineEdit()
        self.seq_name_edit.setPlaceholderText("例如: 文件_{n}")
        seq_start_label = QLabel("起始:")
        seq_start_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.seq_start_spin = QSpinBox()
        self.seq_start_spin.setRange(0, 9999)
        self.seq_start_spin.setValue(1)
        seq_digits_label = QLabel("位数:")
        seq_digits_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.seq_digits_spin = QSpinBox()
        self.seq_digits_spin.setRange(1, 10)
        self.seq_digits_spin.setValue(3)
        seq_layout.addWidget(seq_name_label)
        seq_layout.addWidget(self.seq_name_edit)
        seq_layout.addWidget(seq_start_label)
        seq_layout.addWidget(self.seq_start_spin)
        seq_layout.addWidget(seq_digits_label)
        seq_layout.addWidget(self.seq_digits_spin)
        mode_layout.addLayout(seq_layout)
        
        # 模式4: 大小写转换
        self.case_radio = QRadioButton("大小写转换")
        self.mode_group.addButton(self.case_radio, 3)
        mode_layout.addWidget(self.case_radio)
        
        case_layout = QHBoxLayout()
        case_layout.setContentsMargins(20, 0, 0, 0)
        self.case_combo = QComboBox()
        self.case_combo.addItems(["全部大写", "全部小写", "首字母大写", "驼峰命名"])
        case_layout.addWidget(self.case_combo)
        case_layout.addStretch()
        mode_layout.addLayout(case_layout)
        
        # 模式5: 扩展名修改
        self.ext_radio = QRadioButton("修改扩展名")
        self.mode_group.addButton(self.ext_radio, 4)
        mode_layout.addWidget(self.ext_radio)
        
        ext_layout = QHBoxLayout()
        ext_layout.setContentsMargins(20, 0, 0, 0)
        ext_label = QLabel("新扩展名:")
        ext_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.ext_edit = QLineEdit()
        self.ext_edit.setPlaceholderText("例如: txt")
        ext_layout.addWidget(ext_label)
        ext_layout.addWidget(self.ext_edit)
        ext_layout.addStretch()
        mode_layout.addLayout(ext_layout)
        
        left_layout.addWidget(mode_group)
        
        # 预览和执行按钮
        btn_layout = QHBoxLayout()
        
        preview_btn = QPushButton("👁️ 预览")
        preview_btn.setStyleSheet(get_accent_button_style())
        preview_btn.clicked.connect(self.preview_rename)
        btn_layout.addWidget(preview_btn)
        
        execute_btn = QPushButton("✅ 执行重命名")
        execute_btn.setStyleSheet(get_success_button_style())
        execute_btn.clicked.connect(self.execute_rename)
        btn_layout.addWidget(execute_btn)
        
        left_layout.addLayout(btn_layout)
        
        content_layout.addWidget(left_panel)
        
        # 右侧：文件列表和预览
        right_panel = QGroupBox("文件列表")
        right_layout = QVBoxLayout(right_panel)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.file_count_label = QLabel("📁 文件数: 0")
        self.file_count_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        stats_layout.addWidget(self.file_count_label)
        stats_layout.addStretch()
        
        clear_btn = QPushButton("🧹 清空列表")
        clear_btn.setStyleSheet(get_secondary_button_style())
        clear_btn.clicked.connect(self.clear_files)
        stats_layout.addWidget(clear_btn)
        
        right_layout.addLayout(stats_layout)
        
        # 文件表格
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["序号", "原文件名", "新文件名"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        right_layout.addWidget(self.file_table)
        
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout, 1)
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_edit.setText(folder)
            self.load_files()
    
    def load_files(self):
        """加载文件"""
        folder = self.folder_edit.text()
        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "警告", "请先选择有效的文件夹！")
            return
        
        # 获取过滤器
        filter_text = self.filter_combo.currentText()
        
        self.files = []
        try:
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    if filter_text == "所有文件" or self._match_filter(filename, filter_text):
                        self.files.append(filename)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")
            return
        
        self.files.sort()
        self.preview_names = self.files.copy()
        self._update_table()
        self.file_count_label.setText(f"📁 文件数: {len(self.files)}")
    
    def _match_filter(self, filename, filter_text):
        """匹配过滤器"""
        if filter_text.startswith("*."):
            ext = filter_text[1:]
            return filename.lower().endswith(ext.lower())
        return True
    
    def _update_table(self):
        """更新表格"""
        self.file_table.setRowCount(len(self.files))
        
        for i, (old_name, new_name) in enumerate(zip(self.files, self.preview_names)):
            self.file_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.file_table.setItem(i, 1, QTableWidgetItem(old_name))
            
            # 新文件名带颜色
            new_item = QTableWidgetItem(new_name)
            if old_name != new_name:
                new_item.setForeground(QColor(SUCCESS_COLOR))
            self.file_table.setItem(i, 2, new_item)
    
    def preview_rename(self):
        """预览重命名结果"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先加载文件！")
            return
        
        self.preview_names = []
        
        for filename in self.files:
            name, ext = os.path.splitext(filename)
            new_name = filename
            
            if self.replace_radio.isChecked():
                # 查找替换
                find_text = self.find_edit.text()
                replace_text = self.replace_edit.text()
                if find_text:
                    if self.regex_check.isChecked():
                        try:
                            new_name = re.sub(find_text, replace_text, filename)
                        except re.error:
                            new_name = filename
                    else:
                        new_name = filename.replace(find_text, replace_text)
            
            elif self.affix_radio.isChecked():
                # 添加前后缀
                prefix = self.prefix_edit.text()
                suffix = self.suffix_edit.text()
                new_name = f"{prefix}{name}{suffix}{ext}"
            
            elif self.sequence_radio.isChecked():
                # 序号填充
                template = self.seq_name_edit.text()
                if template:
                    idx = self.files.index(filename) + self.seq_start_spin.value()
                    digits = self.seq_digits_spin.value()
                    seq_str = str(idx).zfill(digits)
                    new_name = template.replace("{n}", seq_str) + ext
            
            elif self.case_radio.isChecked():
                # 大小写转换
                case_mode = self.case_combo.currentText()
                if case_mode == "全部大写":
                    new_name = name.upper() + ext
                elif case_mode == "全部小写":
                    new_name = name.lower() + ext
                elif case_mode == "首字母大写":
                    new_name = name.capitalize() + ext
                elif case_mode == "驼峰命名":
                    words = re.split(r'[_\-\s]+', name)
                    new_name = ''.join(w.capitalize() for w in words) + ext
            
            elif self.ext_radio.isChecked():
                # 修改扩展名
                new_ext = self.ext_edit.text()
                if new_ext:
                    if not new_ext.startswith('.'):
                        new_ext = '.' + new_ext
                    new_name = name + new_ext
            
            self.preview_names.append(new_name)
        
        self._update_table()
        QMessageBox.information(self, "预览", "重命名预览已更新！")
    
    def execute_rename(self):
        """执行重命名"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先加载文件！")
            return
        
        if self.files == self.preview_names:
            QMessageBox.warning(self, "警告", "没有需要重命名的文件！")
            return
        
        # 确认
        changed_count = sum(1 for o, n in zip(self.files, self.preview_names) if o != n)
        reply = QMessageBox.question(
            self, "确认重命名",
            f"确定要重命名 {changed_count} 个文件吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        folder = self.folder_edit.text()
        success_count = 0
        errors = []
        
        for old_name, new_name in zip(self.files, self.preview_names):
            if old_name != new_name:
                try:
                    old_path = os.path.join(folder, old_name)
                    new_path = os.path.join(folder, new_name)
                    os.rename(old_path, new_path)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{old_name}: {str(e)}")
        
        if errors:
            QMessageBox.warning(
                self, "部分完成",
                f"成功重命名 {success_count} 个文件\n失败 {len(errors)} 个:\n" + "\n".join(errors[:5])
            )
        else:
            QMessageBox.information(self, "完成", f"成功重命名 {success_count} 个文件！")
        
        # 重新加载文件
        self.load_files()
    
    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.preview_names.clear()
        self.file_table.setRowCount(0)
        self.file_count_label.setText("📁 文件数: 0")
