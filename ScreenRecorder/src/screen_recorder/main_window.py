"""
主窗口模块 - 应用程序主界面
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QCheckBox, QSlider, QGroupBox,
    QFrame, QSystemTrayIcon, QMenu, QFileDialog, QMessageBox,
    QSpinBox, QDoubleSpinBox, QTabWidget, QScrollArea, QSizePolicy,
    QApplication, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread, QPoint, QRect
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QAction, QCursor, QFont, QPainter,
    QLinearGradient, QColor, QPen, QBrush, QPolygon, QShortcut, QKeySequence
)

from .recorder_engine import RecorderEngine, RecordingMode
from .annotation_widget import AnnotationOverlay
from .webcam_widget import WebcamOverlay
from .region_selector import RegionSelector
from .hotkey_manager import HotkeyManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScreenRecorder - 屏幕录制工具")
        self.setMinimumSize(900, 650)
        self.resize(960, 680)
        
        # 核心组件
        self.recorder = RecorderEngine()
        self.hotkey_manager = HotkeyManager()
        self.annotation_overlay = None
        self.webcam_overlay = None
        self.region_selector = None
        
        # 状态
        self.is_recording = False
        self.is_paused = False
        self.recording_time = 0
        self.selected_region = None
        
        # 计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # 初始化UI
        self.init_ui()
        self.init_system_tray()
        self.init_hotkeys()
        
        # 连接信号
        self.recorder.recording_finished.connect(self.on_recording_finished)
        self.recorder.error_occurred.connect(self.on_error)
    
    def init_ui(self):
        """初始化用户界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # 左侧 - 录制控制
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # 右侧 - 设置面板
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout)
        
        # 底部状态栏
        self.statusBar().showMessage("就绪 - 准备录制")
    
    def create_header(self):
        """创建标题栏"""
        header = QFrame()
        header.setObjectName("card")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Logo和标题
        title_layout = QVBoxLayout()
        
        title = QLabel("🎬 ScreenRecorder")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        
        subtitle = QLabel("专业级屏幕录制工具 · 支持全屏/区域/窗口录制")
        subtitle.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # 录制状态
        self.status_label = QLabel("⏸️ 就绪")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)
        
        return header
    
    def create_left_panel(self):
        """创建左侧面板 - 录制控制"""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # 录制模式选择
        mode_group = QGroupBox("录制模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🖥️ 全屏录制",
            "📐 区域录制",
            "🪟 窗口录制"
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        # 区域选择按钮
        self.select_region_btn = QPushButton("选择录制区域")
        self.select_region_btn.clicked.connect(self.select_region)
        self.select_region_btn.setEnabled(False)
        mode_layout.addWidget(self.select_region_btn)
        
        # 窗口选择
        self.window_combo = QComboBox()
        self.window_combo.addItems(["当前活动窗口", "选择窗口..."])
        self.window_combo.setVisible(False)
        mode_layout.addWidget(self.window_combo)
        
        layout.addWidget(mode_group)
        
        # 计时器显示
        timer_frame = QFrame()
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setObjectName("timerLabel")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.timer_label)
        
        self.file_size_label = QLabel("文件大小: 0 MB")
        self.file_size_label.setObjectName("subtitleLabel")
        self.file_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.file_size_label)
        
        layout.addWidget(timer_frame)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.record_btn = QPushButton("⏺️ 开始录制")
        self.record_btn.setObjectName("primaryButton")
        self.record_btn.clicked.connect(self.toggle_recording)
        btn_layout.addWidget(self.record_btn)
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
        # 快捷操作
        quick_layout = QHBoxLayout()
        
        self.screenshot_btn = QPushButton("📷 截图")
        self.screenshot_btn.setToolTip("截取当前屏幕 (Ctrl+Shift+S)")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        quick_layout.addWidget(self.screenshot_btn)
        
        self.annotation_btn = QPushButton("✏️ 标注")
        self.annotation_btn.setToolTip("开启/关闭标注模式")
        self.annotation_btn.setCheckable(True)
        self.annotation_btn.clicked.connect(self.toggle_annotation)
        quick_layout.addWidget(self.annotation_btn)
        
        self.webcam_btn = QPushButton("📹 摄像头")
        self.webcam_btn.setToolTip("开启/关闭摄像头叠加")
        self.webcam_btn.setCheckable(True)
        self.webcam_btn.clicked.connect(self.toggle_webcam)
        quick_layout.addWidget(self.webcam_btn)
        
        layout.addLayout(quick_layout)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """创建右侧面板 - 设置"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签页
        tabs = QTabWidget()
        
        # 录制设置标签页
        record_tab = QWidget()
        record_layout = QVBoxLayout(record_tab)
        record_layout.setSpacing(12)
        
        # 视频设置
        video_group = QGroupBox("视频设置")
        video_layout = QGridLayout(video_group)
        video_layout.setSpacing(10)
        
        video_layout.addWidget(QLabel("帧率 (FPS):"), 0, 0)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "24", "30", "60"])
        self.fps_combo.setCurrentText("30")
        video_layout.addWidget(self.fps_combo, 0, 1)
        
        video_layout.addWidget(QLabel("视频质量:"), 1, 0)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(80)
        self.quality_label = QLabel("80%")
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_label.setText(f"{v}%"))
        video_layout.addWidget(self.quality_slider, 1, 1)
        video_layout.addWidget(self.quality_label, 1, 2)
        
        video_layout.addWidget(QLabel("输出格式:"), 2, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "GIF"])
        video_layout.addWidget(self.format_combo, 2, 1)
        
        video_layout.addWidget(QLabel("编码器:"), 3, 0)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264 (推荐)", "MPEG-4", "无压缩"])
        video_layout.addWidget(self.codec_combo, 3, 1)
        
        record_layout.addWidget(video_group)
        
        # 音频设置
        audio_group = QGroupBox("音频设置")
        audio_layout = QGridLayout(audio_group)
        audio_layout.setSpacing(10)
        
        self.audio_enabled = QCheckBox("录制音频")
        self.audio_enabled.setChecked(True)
        audio_layout.addWidget(self.audio_enabled, 0, 0, 1, 2)
        
        self.system_audio = QCheckBox("系统声音")
        self.system_audio.setChecked(True)
        audio_layout.addWidget(self.system_audio, 1, 0)
        
        self.mic_audio = QCheckBox("麦克风")
        self.mic_audio.setChecked(False)
        audio_layout.addWidget(self.mic_audio, 1, 1)
        
        audio_layout.addWidget(QLabel("音频质量:"), 2, 0)
        self.audio_quality = QComboBox()
        self.audio_quality.addItems(["低 (64kbps)", "中 (128kbps)", "高 (256kbps)", "无损"])
        self.audio_quality.setCurrentIndex(1)
        audio_layout.addWidget(self.audio_quality, 2, 1)
        
        record_layout.addWidget(audio_group)
        
        # 鼠标设置
        mouse_group = QGroupBox("鼠标设置")
        mouse_layout = QVBoxLayout(mouse_group)
        
        self.show_cursor = QCheckBox("显示鼠标指针")
        self.show_cursor.setChecked(True)
        mouse_layout.addWidget(self.show_cursor)
        
        self.highlight_click = QCheckBox("高亮鼠标点击")
        self.highlight_click.setChecked(True)
        mouse_layout.addWidget(self.highlight_click)
        
        record_layout.addWidget(mouse_group)
        
        record_layout.addStretch()
        tabs.addTab(record_tab, "录制设置")
        
        # 高级设置标签页
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setSpacing(12)
        
        # 摄像头设置
        cam_group = QGroupBox("摄像头设置")
        cam_layout = QGridLayout(cam_group)
        cam_layout.setSpacing(10)
        
        cam_layout.addWidget(QLabel("摄像头位置:"), 0, 0)
        self.cam_position = QComboBox()
        self.cam_position.addItems(["左上角", "右上角", "左下角", "右下角"])
        self.cam_position.setCurrentIndex(3)
        cam_layout.addWidget(self.cam_position, 0, 1)
        
        cam_layout.addWidget(QLabel("摄像头大小:"), 1, 0)
        self.cam_size = QComboBox()
        self.cam_size.addItems(["小 (160x120)", "中 (240x180)", "大 (320x240)"])
        self.cam_size.setCurrentIndex(1)
        cam_layout.addWidget(self.cam_size, 1, 1)
        
        self.cam_rounded = QCheckBox("圆形摄像头画面")
        self.cam_rounded.setChecked(True)
        cam_layout.addWidget(self.cam_rounded, 2, 0, 1, 2)
        
        advanced_layout.addWidget(cam_group)
        
        # 标注设置
        annot_group = QGroupBox("标注设置")
        annot_layout = QGridLayout(annot_group)
        annot_layout.setSpacing(10)
        
        annot_layout.addWidget(QLabel("画笔颜色:"), 0, 0)
        self.pen_color = QComboBox()
        self.pen_color.addItems(["红色", "蓝色", "绿色", "黄色", "白色"])
        annot_layout.addWidget(self.pen_color, 0, 1)
        
        annot_layout.addWidget(QLabel("画笔粗细:"), 1, 0)
        self.pen_width = QSpinBox()
        self.pen_width.setRange(1, 20)
        self.pen_width.setValue(3)
        annot_layout.addWidget(self.pen_width, 1, 1)
        
        advanced_layout.addWidget(annot_group)
        
        # 快捷键设置
        hotkey_group = QGroupBox("快捷键")
        hotkey_layout = QGridLayout(hotkey_group)
        hotkey_layout.setSpacing(10)
        
        hotkeys = [
            ("开始/停止录制", "F9"),
            ("暂停/继续", "F10"),
            ("截图", "Ctrl+Shift+S"),
            ("选择区域", "Ctrl+Shift+R"),
        ]
        
        for i, (action, key) in enumerate(hotkeys):
            hotkey_layout.addWidget(QLabel(action), i, 0)
            key_label = QLabel(key)
            key_label.setStyleSheet("color: #667eea; font-weight: bold;")
            hotkey_layout.addWidget(key_label, i, 1)
        
        advanced_layout.addWidget(hotkey_group)
        
        advanced_layout.addStretch()
        tabs.addTab(advanced_tab, "高级设置")
        
        # 输出设置标签页
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        output_layout.setSpacing(12)
        
        # 输出路径
        path_group = QGroupBox("输出路径")
        path_layout = QHBoxLayout(path_group)
        
        self.output_path = QLabel(os.path.expanduser("~/Videos/ScreenRecorder"))
        self.output_path.setStyleSheet("color: #888888;")
        path_layout.addWidget(self.output_path, stretch=1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_output_path)
        path_layout.addWidget(browse_btn)
        
        output_layout.addWidget(path_group)
        
        # 文件命名
        naming_group = QGroupBox("文件命名")
        naming_layout = QVBoxLayout(naming_group)
        
        self.auto_naming = QCheckBox("自动命名 (录制时间)")
        self.auto_naming.setChecked(True)
        naming_layout.addWidget(self.auto_naming)
        
        naming_layout.addWidget(QLabel("文件名前缀:"))
        self.prefix_input = QComboBox()
        self.prefix_input.setEditable(True)
        self.prefix_input.addItems(["ScreenRecord", "录屏", "Video"])
        naming_layout.addWidget(self.prefix_input)
        
        output_layout.addWidget(naming_group)
        
        # 历史记录
        history_group = QGroupBox("最近录制")
        history_layout = QVBoxLayout(history_group)
        
        self.history_label = QLabel("暂无录制记录")
        self.history_label.setObjectName("subtitleLabel")
        self.history_label.setWordWrap(True)
        history_layout.addWidget(self.history_label)
        
        output_layout.addWidget(history_group)
        
        output_layout.addStretch()
        tabs.addTab(output_tab, "输出设置")
        
        layout.addWidget(tabs)
        
        return panel
    
    def init_system_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标（使用文本生成简单图标）
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#667eea"))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("white"), 3))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(22, 22, 20, 20)
        painter.end()
        
        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray_icon.setToolTip("ScreenRecorder - 屏幕录制工具")
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        record_action = QAction("开始录制", self)
        record_action.triggered.connect(self.toggle_recording)
        tray_menu.addAction(record_action)
        
        screenshot_action = QAction("截图", self)
        screenshot_action.triggered.connect(self.take_screenshot)
        tray_menu.addAction(screenshot_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def init_hotkeys(self):
        """初始化全局快捷键"""
        self.hotkey_manager.hotkey_pressed.connect(self.on_hotkey)
        self.hotkey_manager.register_hotkey("F9", "toggle_recording")
        self.hotkey_manager.register_hotkey("F10", "toggle_pause")
        self.hotkey_manager.register_hotkey("ctrl+shift+s", "screenshot")
        self.hotkey_manager.register_hotkey("ctrl+shift+r", "select_region")
    
    def on_hotkey(self, action):
        """处理快捷键"""
        if action == "toggle_recording":
            self.toggle_recording()
        elif action == "toggle_pause":
            self.toggle_pause()
        elif action == "screenshot":
            self.take_screenshot()
        elif action == "select_region":
            self.select_region()
    
    def on_mode_changed(self, index):
        """录制模式改变"""
        self.select_region_btn.setEnabled(index == 1)
        self.window_combo.setVisible(index == 2)
    
    def select_region(self):
        """选择录制区域"""
        self.hide()
        QTimer.singleShot(300, self._do_select_region)
    
    def _do_select_region(self):
        """执行区域选择"""
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.on_region_selected)
        self.region_selector.show()
    
    def on_region_selected(self, rect):
        """区域选择完成"""
        self.selected_region = rect
        self.show()
        if rect:
            self.statusBar().showMessage(
                f"已选择区域: {rect.width()}x{rect.height()} at ({rect.x()}, {rect.y()})")
    
    def toggle_recording(self):
        """切换录制状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录制"""
        # 获取录制参数
        mode = self.mode_combo.currentIndex()
        fps = int(self.fps_combo.currentText())
        quality = self.quality_slider.value()
        fmt = self.format_combo.currentText()
        
        # 构建输出路径
        output_dir = self.output_path.text()
        os.makedirs(output_dir, exist_ok=True)
        
        if self.auto_naming.isChecked():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self.prefix_input.currentText()
            filename = f"{prefix}_{timestamp}.{fmt.lower()}"
        else:
            filename = f"recording.{fmt.lower()}"
        
        output_file = os.path.join(output_dir, filename)
        
        # 录制模式
        if mode == 0:
            rec_mode = RecordingMode.FULLSCREEN
        elif mode == 1:
            rec_mode = RecordingMode.REGION
        else:
            rec_mode = RecordingMode.WINDOW
        
        # 音频设置
        record_audio = self.audio_enabled.isChecked()
        mic = self.mic_audio.isChecked()
        
        # 开始录制
        success = self.recorder.start(
            mode=rec_mode,
            output_file=output_file,
            fps=fps,
            quality=quality,
            region=self.selected_region if mode == 1 else None,
            record_audio=record_audio,
            mic_audio=mic,
            show_cursor=self.show_cursor.isChecked()
        )
        
        if success:
            self.is_recording = True
            self.is_paused = False
            self.recording_time = 0
            self.timer.start(1000)
            
            self.record_btn.setText("⏹️ 停止录制")
            self.record_btn.setObjectName("dangerButton")
            self.record_btn.style().unpolish(self.record_btn)
            self.record_btn.style().polish(self.record_btn)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("🔴 录制中")
            
            self.statusBar().showMessage(f"正在录制: {output_file}")
            
            # 最小化到托盘
            if self.sender() == self.record_btn:
                self.showMinimized()
    
    def toggle_pause(self):
        """切换暂停状态"""
        if not self.is_recording:
            return
        
        if self.is_paused:
            self.recorder.resume()
            self.is_paused = False
            self.pause_btn.setText("⏸️ 暂停")
            self.status_label.setText("🔴 录制中")
            self.timer.start(1000)
        else:
            self.recorder.pause()
            self.is_paused = True
            self.pause_btn.setText("▶️ 继续")
            self.status_label.setText("⏸️ 已暂停")
            self.timer.stop()
    
    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.recorder.stop()
        self.timer.stop()
        
        self.is_recording = False
        self.is_paused = False
        
        self.record_btn.setText("⏺️ 开始录制")
        self.record_btn.setObjectName("primaryButton")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ 暂停")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏸️ 就绪")
        
        self.statusBar().showMessage("录制已停止")
    
    def update_timer(self):
        """更新计时器"""
        self.recording_time += 1
        hours = self.recording_time // 3600
        minutes = (self.recording_time % 3600) // 60
        seconds = self.recording_time % 60
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # 更新文件大小估算
        fps = int(self.fps_combo.currentText())
        quality = self.quality_slider.value()
        est_size = self.recording_time * fps * quality * 0.0001  # 粗略估算
        self.file_size_label.setText(f"预估大小: {est_size:.1f} MB")
    
    def on_recording_finished(self, output_file):
        """录制完成"""
        self.stop_recording()
        
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            self.history_label.setText(
                f"最近录制: {os.path.basename(output_file)}\n"
                f"大小: {size_mb:.1f} MB\n"
                f"时长: {self.timer_label.text()}")
            
            self.tray_icon.showMessage(
                "录制完成",
                f"文件已保存: {os.path.basename(output_file)}\n大小: {size_mb:.1f} MB",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    def on_error(self, error_msg):
        """错误处理"""
        QMessageBox.critical(self, "录制错误", f"发生错误:\n{error_msg}")
        self.stop_recording()
    
    def take_screenshot(self):
        """截图"""
        output_dir = self.output_path.text()
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        output_file = os.path.join(output_dir, filename)
        
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            pixmap.save(output_file, "PNG")
            
            self.tray_icon.showMessage(
                "截图已保存",
                f"文件: {filename}",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
            self.statusBar().showMessage(f"截图已保存: {output_file}")
    
    def toggle_annotation(self, checked):
        """切换标注模式"""
        if checked:
            if not self.annotation_overlay:
                self.annotation_overlay = AnnotationOverlay()
            self.annotation_overlay.show()
            self.statusBar().showMessage("标注模式已开启")
        else:
            if self.annotation_overlay:
                self.annotation_overlay.hide()
            self.statusBar().showMessage("标注模式已关闭")
    
    def toggle_webcam(self, checked):
        """切换摄像头叠加"""
        if checked:
            if not self.webcam_overlay:
                self.webcam_overlay = WebcamOverlay()
            self.webcam_overlay.show()
            self.statusBar().showMessage("摄像头叠加已开启")
        else:
            if self.webcam_overlay:
                self.webcam_overlay.hide()
            self.statusBar().showMessage("摄像头叠加已关闭")
    
    def browse_output_path(self):
        """浏览输出路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_path.text())
        if path:
            self.output_path.setText(path)
    
    def tray_icon_activated(self, reason):
        """托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def quit_application(self):
        """退出应用"""
        if self.is_recording:
            reply = QMessageBox.question(
                self, "确认退出",
                "正在录制中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self.stop_recording()
        
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.quit()
    
    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        if self.is_recording:
            reply = QMessageBox.question(
                self, "确认退出",
                "正在录制中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.stop_recording()
        
        event.accept()
        QApplication.quit()
