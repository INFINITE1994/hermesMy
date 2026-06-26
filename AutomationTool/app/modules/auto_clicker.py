"""
自动点击器模块 - 自动化鼠标点击
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSpinBox, QComboBox, QCheckBox, QMessageBox,
    QFrame, QSlider, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QCursor

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class AutoClickerWidget(QWidget):
    """自动点击器界面"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.click_count = 0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("🖱️ 自动点击器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 运行状态
        self.status_label = QLabel("⏹ 未运行")
        self.status_label.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {TEXT_SECONDARY};
        """)
        title_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("自动鼠标点击工具，可配置点击间隔、点击类型和点击次数")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 主内容区
        content_layout = QHBoxLayout()
        
        # 左侧：配置面板
        left_panel = QGroupBox("点击配置")
        left_layout = QVBoxLayout(left_panel)
        
        # 点击类型
        click_type_group = QGroupBox("点击类型")
        click_type_layout = QVBoxLayout(click_type_group)
        
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems(["左键单击", "右键单击", "中键单击", "左键双击"])
        self.click_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }}
        """)
        click_type_layout.addWidget(self.click_type_combo)
        
        left_layout.addWidget(click_type_group)
        
        # 点击间隔
        interval_group = QGroupBox("点击间隔")
        interval_layout = QVBoxLayout(interval_group)
        
        # 毫秒输入
        ms_layout = QHBoxLayout()
        ms_label = QLabel("间隔(毫秒):")
        ms_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.ms_spin = QSpinBox()
        self.ms_spin.setRange(1, 60000)
        self.ms_spin.setValue(100)
        self.ms_spin.setSuffix(" ms")
        self.ms_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {CARD_COLOR};
                border: 1px solid #1a1a3a;
                border-radius: 6px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        ms_layout.addWidget(ms_label)
        ms_layout.addWidget(self.ms_spin)
        interval_layout.addLayout(ms_layout)
        
        # 快速设置按钮
        quick_layout = QHBoxLayout()
        quick_ms = [50, 100, 200, 500, 1000, 2000]
        for ms in quick_ms:
            btn = QPushButton(f"{ms}ms")
            btn.setStyleSheet(get_secondary_button_style())
            btn.clicked.connect(lambda checked, v=ms: self.ms_spin.setValue(v))
            quick_layout.addWidget(btn)
        interval_layout.addLayout(quick_layout)
        
        # 滑块
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(1, 5000)
        self.interval_slider.setValue(100)
        self.interval_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {CARD_COLOR};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_START}, stop:1 {ACCENT_END});
                border-radius: 4px;
            }}
        """)
        self.interval_slider.valueChanged.connect(lambda v: self.ms_spin.setValue(v))
        self.ms_spin.valueChanged.connect(lambda v: self.interval_slider.setValue(min(v, 5000)))
        interval_layout.addWidget(self.interval_slider)
        
        left_layout.addWidget(interval_group)
        
        # 点击次数
        count_group = QGroupBox("点击次数")
        count_layout = QVBoxLayout(count_group)
        
        self.unlimited_check = QCheckBox("无限点击")
        self.unlimited_check.setChecked(True)
        self.unlimited_check.stateChanged.connect(self.toggle_count_limit)
        count_layout.addWidget(self.unlimited_check)
        
        count_input_layout = QHBoxLayout()
        count_label = QLabel("次数限制:")
        count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 999999)
        self.count_spin.setValue(100)
        self.count_spin.setEnabled(False)
        count_input_layout.addWidget(count_label)
        count_input_layout.addWidget(self.count_spin)
        count_layout.addLayout(count_input_layout)
        
        left_layout.addWidget(count_group)
        
        # 鼠标位置
        pos_group = QGroupBox("鼠标位置")
        pos_layout = QVBoxLayout(pos_group)
        
        self.current_pos_radio = QCheckBox("在当前鼠标位置点击")
        self.current_pos_radio.setChecked(True)
        pos_layout.addWidget(self.current_pos_radio)
        
        fixed_pos_layout = QHBoxLayout()
        x_label = QLabel("X:")
        x_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.setValue(500)
        self.x_spin.setEnabled(False)
        y_label = QLabel("Y:")
        y_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.setValue(300)
        self.y_spin.setEnabled(False)
        
        self.current_pos_radio.stateChanged.connect(self.toggle_position_mode)
        
        fixed_pos_layout.addWidget(x_label)
        fixed_pos_layout.addWidget(self.x_spin)
        fixed_pos_layout.addWidget(y_label)
        fixed_pos_layout.addWidget(self.y_spin)
        pos_layout.addLayout(fixed_pos_layout)
        
        left_layout.addWidget(pos_group)
        
        content_layout.addWidget(left_panel)
        
        # 右侧：控制和统计
        right_layout = QVBoxLayout()
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)
        
        # 开始/停止按钮
        self.start_btn = QPushButton("▶ 开始点击")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {SUCCESS_COLOR}, stop:1 #22c55e);
                color: #000000;
                border: none;
                padding: 20px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {SUCCESS_COLOR}dd, stop:1 #22c55edd);
            }}
        """)
        self.start_btn.clicked.connect(self.toggle_clicking)
        control_layout.addWidget(self.start_btn)
        
        # 快捷键提示
        hotkey_hint = QLabel("💡 提示: 按 F6 开始/停止")
        hotkey_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        hotkey_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(hotkey_hint)
        
        # 重置按钮
        reset_btn = QPushButton("🔄 重置计数")
        reset_btn.setStyleSheet(get_secondary_button_style())
        reset_btn.clicked.connect(self.reset_count)
        control_layout.addWidget(reset_btn)
        
        right_layout.addWidget(control_group)
        
        # 统计信息
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.count_display = QLabel("0")
        self.count_display.setStyleSheet(f"""
            font-size: 48px;
            font-weight: bold;
            color: {ACCENT_START};
            padding: 20px;
        """)
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.count_display)
        
        click_count_label = QLabel("点击次数")
        click_count_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        click_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(click_count_label)
        
        # 间隔显示
        separator = QLabel("─" * 30)
        separator.setStyleSheet(f"color: #1a1a3a;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(separator)
        
        self.cps_label = QLabel("CPS: 0 次/秒")
        self.cps_label.setStyleSheet(f"color: {ACCENT_END}; font-size: 16px; font-weight: bold;")
        self.cps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.cps_label)
        
        self.elapsed_label = QLabel("运行时间: 00:00:00")
        self.elapsed_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self.elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.elapsed_label)
        
        right_layout.addWidget(stats_group)
        
        # 预设配置
        preset_group = QGroupBox("⚡ 快速预设")
        preset_layout = QVBoxLayout(preset_group)
        
        presets = [
            ("慢速点击", 1000, "左键单击"),
            ("正常点击", 200, "左键单击"),
            ("快速点击", 50, "左键单击"),
            ("连点模式", 10, "左键单击"),
        ]
        
        for name, ms, click_type in presets:
            btn = QPushButton(f"{name} ({ms}ms)")
            btn.setStyleSheet(get_secondary_button_style())
            btn.clicked.connect(lambda checked, n=name, m=ms, t=click_type: self.apply_preset(m, t))
            preset_layout.addWidget(btn)
        
        right_layout.addWidget(preset_group)
        
        content_layout.addLayout(right_layout)
        
        layout.addLayout(content_layout, 1)
        
        # 点击定时器
        self.click_timer = QTimer(self)
        self.click_timer.timeout.connect(self.do_click)
        
        # 统计定时器
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.clicks_per_second = 0
        self.last_second_count = 0
        self.start_time = 0
    
    def toggle_count_limit(self, state):
        """切换次数限制"""
        self.count_spin.setEnabled(not state)
    
    def toggle_position_mode(self, state):
        """切换位置模式"""
        self.x_spin.setEnabled(not state)
        self.y_spin.setEnabled(not state)
    
    def toggle_clicking(self):
        """切换点击状态"""
        if not self.is_running:
            self.start_clicking()
        else:
            self.stop_clicking()
    
    def start_clicking(self):
        """开始点击"""
        self.is_running = True
        self.start_btn.setText("⏹ 停止点击")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ERROR_COLOR}, stop:1 #ef4444);
                color: white;
                border: none;
                padding: 20px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ERROR_COLOR}dd, stop:1 #ef4444dd);
            }}
        """)
        
        self.status_label.setText("▶ 运行中")
        self.status_label.setStyleSheet(f"""
            background-color: #0a1a0a;
            border: 1px solid {SUCCESS_COLOR};
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {SUCCESS_COLOR};
        """)
        
        # 启动定时器
        interval = self.ms_spin.value()
        self.click_timer.start(interval)
        
        # 启动统计定时器
        self.start_time = time.time()
        self.last_second_count = self.click_count
        self.stats_timer.start(1000)
    
    def stop_clicking(self):
        """停止点击"""
        self.is_running = False
        self.start_btn.setText("▶ 开始点击")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {SUCCESS_COLOR}, stop:1 #22c55e);
                color: #000000;
                border: none;
                padding: 20px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {SUCCESS_COLOR}dd, stop:1 #22c55edd);
            }}
        """)
        
        self.status_label.setText("⏹ 已停止")
        self.status_label.setStyleSheet(f"""
            background-color: {CARD_COLOR};
            border: 1px solid #1a1a3a;
            border-radius: 15px;
            padding: 6px 16px;
            font-size: 12px;
            color: {TEXT_SECONDARY};
        """)
        
        self.click_timer.stop()
        self.stats_timer.stop()
    
    def do_click(self):
        """执行点击"""
        self.click_count += 1
        self.count_display.setText(str(self.click_count))
        
        # 检查次数限制
        if not self.unlimited_check.isChecked():
            if self.click_count >= self.count_spin.value():
                self.stop_clicking()
                QMessageBox.information(self, "完成", f"已达到设定的点击次数: {self.count_spin.value()}")
    
    def update_stats(self):
        """更新统计信息"""
        # 计算CPS
        self.clicks_per_second = self.click_count - self.last_second_count
        self.last_second_count = self.click_count
        self.cps_label.setText(f"CPS: {self.clicks_per_second} 次/秒")
        
        # 计算运行时间
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        self.elapsed_label.setText(f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def reset_count(self):
        """重置计数"""
        self.click_count = 0
        self.count_display.setText("0")
        self.cps_label.setText("CPS: 0 次/秒")
        self.elapsed_label.setText("运行时间: 00:00:00")
    
    def apply_preset(self, ms, click_type):
        """应用预设"""
        self.ms_spin.setValue(ms)
        self.click_type_combo.setCurrentText(click_type)
