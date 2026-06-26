"""
宏录制器模块 - 录制和回放鼠标键盘操作
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QFileDialog, QMessageBox,
    QFrame, QProgressBar, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR
)


class MacroRecorderWidget(QWidget):
    """宏录制器界面"""
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_playing = False
        self.recorded_actions = []
        self._setup_ui()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("🎬 宏录制器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 录制状态指示
        self.status_indicator = QLabel("⏹ 待机")
        self.status_indicator.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {TEXT_SECONDARY};
        """)
        title_layout.addWidget(self.status_indicator)
        
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("录制鼠标和键盘操作，支持保存和回放宏文件")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 控制面板
        control_group = QGroupBox("录制控制")
        control_layout = QHBoxLayout(control_group)
        
        # 录制按钮
        self.record_btn = QPushButton("⏺ 开始录制")
        self.record_btn.setStyleSheet(get_accent_button_style())
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setStyleSheet(get_danger_button_style())
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        # 回放按钮
        self.play_btn = QPushButton("▶ 回放")
        self.play_btn.setStyleSheet(get_success_button_style())
        self.play_btn.clicked.connect(self.play_macro)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        control_layout.addStretch()
        
        # 回放速度
        speed_label = QLabel("回放速度:")
        speed_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        control_layout.addWidget(speed_label)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "2x", "5x", "10x"])
        self.speed_combo.setCurrentText("1x")
        self.speed_combo.setFixedWidth(80)
        control_layout.addWidget(self.speed_combo)
        
        # 循环次数
        loop_label = QLabel("循环次数:")
        loop_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        control_layout.addWidget(loop_label)
        
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(1, 100)
        self.loop_spin.setValue(1)
        self.loop_spin.setFixedWidth(70)
        control_layout.addWidget(self.loop_spin)
        
        layout.addWidget(control_group)
        
        # 宏操作列表
        list_group = QGroupBox("录制的操作列表")
        list_layout = QVBoxLayout(list_group)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加操作")
        add_btn.setStyleSheet(get_secondary_button_style())
        add_btn.clicked.connect(self.add_action)
        toolbar_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.setStyleSheet(get_secondary_button_style())
        delete_btn.clicked.connect(self.delete_action)
        toolbar_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("🧹 清空列表")
        clear_btn.setStyleSheet(get_secondary_button_style())
        clear_btn.clicked.connect(self.clear_actions)
        toolbar_layout.addWidget(clear_btn)
        
        toolbar_layout.addStretch()
        
        # 保存/加载
        save_btn = QPushButton("💾 保存宏")
        save_btn.setStyleSheet(get_secondary_button_style())
        save_btn.clicked.connect(self.save_macro)
        toolbar_layout.addWidget(save_btn)
        
        load_btn = QPushButton("📂 加载宏")
        load_btn.setStyleSheet(get_secondary_button_style())
        load_btn.clicked.connect(self.load_macro)
        toolbar_layout.addWidget(load_btn)
        
        list_layout.addLayout(toolbar_layout)
        
        # 操作表格
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(5)
        self.actions_table.setHorizontalHeaderLabels(["序号", "类型", "操作", "参数", "延迟(ms)"])
        self.actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.actions_table.setAlternatingRowColors(True)
        self.actions_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_COLOR};
                alternate-background-color: #0d0d1a;
            }}
        """)
        list_layout.addWidget(self.actions_table)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
                border-radius: 3px;
            }}
        """)
        list_layout.addWidget(self.progress_bar)
        
        layout.addWidget(list_group)
    
    def toggle_recording(self):
        """切换录制状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录制"""
        self.is_recording = True
        self.record_btn.setText("⏸ 暂停录制")
        self.stop_btn.setEnabled(True)
        self.status_indicator.setText("⏺ 录制中...")
        self.status_indicator.setStyleSheet(f"""
            background-color: #1a0a0a;
            border: 1px solid {ERROR_COLOR};
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {ERROR_COLOR};
        """)
        
        # 模拟添加一些录制动作
        self._simulate_recording()
    
    def _simulate_recording(self):
        """模拟录制动作（演示用）"""
        demo_actions = [
            (1, "鼠标", "点击", "位置: (500, 300)", "0"),
            (2, "键盘", "输入", "文本: Hello", "100"),
            (3, "鼠标", "移动", "位置: (800, 400)", "50"),
            (4, "键盘", "快捷键", "Ctrl+C", "200"),
            (5, "鼠标", "双击", "位置: (600, 200)", "150"),
        ]
        
        self.recorded_actions = demo_actions
        self._update_table()
    
    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        self.record_btn.setText("⏺ 开始录制")
        self.stop_btn.setEnabled(False)
        self.play_btn.setEnabled(len(self.recorded_actions) > 0)
        self.status_indicator.setText("⏹ 已停止")
        self.status_indicator.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {TEXT_SECONDARY};
        """)
    
    def play_macro(self):
        """回放宏"""
        if not self.recorded_actions:
            QMessageBox.warning(self, "警告", "没有可回放的操作！")
            return
        
        self.is_playing = True
        self.play_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.recorded_actions))
        self.progress_bar.setValue(0)
        self.status_indicator.setText("▶ 回放中...")
        self.status_indicator.setStyleSheet(f"""
            background-color: #0a1a0a;
            border: 1px solid {SUCCESS_COLOR};
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {SUCCESS_COLOR};
        """)
        
        # 模拟回放进度
        self._play_timer = QTimer(self)
        self._play_step = 0
        self._play_timer.timeout.connect(self._play_next_step)
        self._play_timer.start(500)
    
    def _play_next_step(self):
        """回放下一步"""
        if self._play_step >= len(self.recorded_actions):
            self._play_timer.stop()
            self.is_playing = False
            self.play_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_indicator.setText("⏹ 待机")
            self.status_indicator.setStyleSheet(f"""
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 15px;
                padding: 6px 16px;
                font-size: 12px;
                color: {TEXT_SECONDARY};
            """)
            QMessageBox.information(self, "完成", "宏回放完成！")
            return
        
        self.progress_bar.setValue(self._play_step + 1)
        self._play_step += 1
    
    def add_action(self):
        """手动添加操作"""
        row = self.actions_table.rowCount()
        self.actions_table.insertRow(row)
        self.actions_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.actions_table.setItem(row, 1, QTableWidgetItem("鼠标"))
        self.actions_table.setItem(row, 2, QTableWidgetItem("点击"))
        self.actions_table.setItem(row, 3, QTableWidgetItem("位置: (0, 0)"))
        self.actions_table.setItem(row, 4, QTableWidgetItem("0"))
    
    def delete_action(self):
        """删除选中操作"""
        current_row = self.actions_table.currentRow()
        if current_row >= 0:
            self.actions_table.removeRow(current_row)
            self._renumber_actions()
    
    def clear_actions(self):
        """清空所有操作"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有操作吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.actions_table.setRowCount(0)
            self.recorded_actions.clear()
            self.play_btn.setEnabled(False)
    
    def _renumber_actions(self):
        """重新编号"""
        for row in range(self.actions_table.rowCount()):
            self.actions_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
    
    def _update_table(self):
        """更新表格显示"""
        self.actions_table.setRowCount(len(self.recorded_actions))
        for i, action in enumerate(self.recorded_actions):
            for j, value in enumerate(action):
                self.actions_table.setItem(i, j, QTableWidgetItem(str(value)))
        self.play_btn.setEnabled(len(self.recorded_actions) > 0)
    
    def save_macro(self):
        """保存宏文件"""
        if not self.recorded_actions:
            QMessageBox.warning(self, "警告", "没有可保存的操作！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存宏文件", "", "宏文件 (*.macro);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for action in self.recorded_actions:
                        f.write('|'.join(str(x) for x in action) + '\n')
                QMessageBox.information(self, "成功", f"宏已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def load_macro(self):
        """加载宏文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载宏文件", "", "宏文件 (*.macro);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.recorded_actions = []
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) == 5:
                            self.recorded_actions.append(tuple(parts))
                self._update_table()
                QMessageBox.information(self, "成功", f"宏已加载: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
