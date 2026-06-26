"""生成二维码标签页"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QFileDialog, QColorDialog, QFrame, QGroupBox, QFormLayout,
    QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QImage
from PIL import Image
import io


class GenerateTab(QWidget):
    """生成二维码标签页"""

    qr_generated = pyqtSignal(str, str, str)  # content, type, image_path

    def __init__(self, qr_generator, history_manager):
        super().__init__()
        self.qr_generator = qr_generator
        self.history_manager = history_manager
        self.current_image = None
        self.fg_color = "#ffffff"
        self.bg_color = "#000000"
        self.logo_path = None
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 左侧：输入面板
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)

        # 标题
        title = QLabel("✨ 生成二维码")
        title.setObjectName("title")
        left_layout.addWidget(title)

        # 类型选择
        type_group = QGroupBox("二维码类型")
        type_layout = QVBoxLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["📝 文本/URL", "📶 WiFi配置", "👤 vCard名片"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        left_layout.addWidget(type_group)

        # 内容输入区域（堆叠）
        self.content_stack = {}

        # 文本输入
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入文本或URL...")
        self.text_input.setMinimumHeight(120)
        text_layout.addWidget(self.text_input)
        self.content_stack["text"] = text_widget

        # WiFi输入
        wifi_widget = QWidget()
        wifi_form = QFormLayout(wifi_widget)
        wifi_form.setContentsMargins(0, 0, 0, 0)
        self.wifi_ssid = QLineEdit()
        self.wifi_ssid.setPlaceholderText("WiFi名称")
        self.wifi_password = QLineEdit()
        self.wifi_password.setPlaceholderText("WiFi密码")
        self.wifi_security = QComboBox()
        self.wifi_security.addItems(["WPA", "WEP", "nopass"])
        self.wifi_hidden = QCheckBox("隐藏网络")
        wifi_form.addRow("📶 SSID:", self.wifi_ssid)
        wifi_form.addRow("🔑 密码:", self.wifi_password)
        wifi_form.addRow("🔒 加密:", self.wifi_security)
        wifi_form.addRow("", self.wifi_hidden)
        self.content_stack["wifi"] = wifi_widget

        # vCard输入
        vcard_widget = QWidget()
        vcard_form = QFormLayout(vcard_widget)
        vcard_form.setContentsMargins(0, 0, 0, 0)
        self.vcard_name = QLineEdit()
        self.vcard_name.setPlaceholderText("姓名")
        self.vcard_phone = QLineEdit()
        self.vcard_phone.setPlaceholderText("电话号码")
        self.vcard_email = QLineEdit()
        self.vcard_email.setPlaceholderText("邮箱地址")
        self.vcard_org = QLineEdit()
        self.vcard_org.setPlaceholderText("公司/组织")
        self.vcard_title = QLineEdit()
        self.vcard_title.setPlaceholderText("职位")
        self.vcard_url = QLineEdit()
        self.vcard_url.setPlaceholderText("个人网站")
        vcard_form.addRow("👤 姓名:", self.vcard_name)
        vcard_form.addRow("📞 电话:", self.vcard_phone)
        vcard_form.addRow("📧 邮箱:", self.vcard_email)
        vcard_form.addRow("🏢 组织:", self.vcard_org)
        vcard_form.addRow("💼 职位:", self.vcard_title)
        vcard_form.addRow("🌐 网站:", self.vcard_url)
        self.content_stack["vcard"] = vcard_widget

        # 内容容器
        self.content_container = QFrame()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        for w in self.content_stack.values():
            self.content_layout.addWidget(w)
            w.hide()
        self.content_stack["text"].show()
        left_layout.addWidget(self.content_container)

        # 自定义选项
        customize_group = QGroupBox("🎨 自定义样式")
        customize_layout = QVBoxLayout(customize_group)

        # 颜色选择
        color_row = QHBoxLayout()
        self.btn_fg = QPushButton("🎨 前景色")
        self.btn_fg.setStyleSheet(f"background-color: {self.fg_color}; color: #000000;")
        self.btn_fg.clicked.connect(self._pick_fg_color)
        self.btn_bg = QPushButton("🎨 背景色")
        self.btn_bg.setStyleSheet(f"background-color: {self.bg_color}; color: #ffffff;")
        self.btn_bg.clicked.connect(self._pick_bg_color)
        color_row.addWidget(self.btn_fg)
        color_row.addWidget(self.btn_bg)
        customize_layout.addLayout(color_row)

        # 尺寸
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("📏 尺寸:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 20)
        self.size_spin.setValue(10)
        self.size_spin.setSuffix(" (倍率)")
        size_row.addWidget(self.size_spin)
        customize_layout.addLayout(size_row)

        # Logo
        logo_row = QHBoxLayout()
        self.btn_logo = QPushButton("🖼️ 选择Logo")
        self.btn_logo.clicked.connect(self._pick_logo)
        self.logo_label = QLabel("未选择Logo")
        self.logo_label.setObjectName("subtitle")
        self.btn_clear_logo = QPushButton("❌ 清除")
        self.btn_clear_logo.clicked.connect(self._clear_logo)
        self.btn_clear_logo.setMaximumWidth(60)
        logo_row.addWidget(self.btn_logo)
        logo_row.addWidget(self.logo_label)
        logo_row.addWidget(self.btn_clear_logo)
        customize_layout.addLayout(logo_row)

        left_layout.addWidget(customize_group)

        # 生成按钮
        self.btn_generate = QPushButton("🚀 生成二维码")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.setMinimumHeight(48)
        self.btn_generate.clicked.connect(self._generate)
        left_layout.addWidget(self.btn_generate)

        left_layout.addStretch()

        # 右侧：预览面板
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)

        preview_title = QLabel("👁️ 预览")
        preview_title.setObjectName("title")
        right_layout.addWidget(preview_title)

        # 预览区域
        self.preview_label = QLabel("生成二维码后将在此处显示预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px dashed #3a3a4a;
                border-radius: 12px;
                font-size: 16px;
                color: #666688;
            }
        """)
        right_layout.addWidget(self.preview_label, 1)

        # 信息
        self.info_label = QLabel("")
        self.info_label.setObjectName("subtitle")
        self.info_label.setWordWrap(True)
        right_layout.addWidget(self.info_label)

        # 导出按钮
        export_row = QHBoxLayout()
        self.btn_save_png = QPushButton("💾 PNG")
        self.btn_save_png.setObjectName("primary")
        self.btn_save_png.clicked.connect(lambda: self._export("png"))
        self.btn_save_jpg = QPushButton("💾 JPG")
        self.btn_save_jpg.clicked.connect(lambda: self._export("jpg"))
        self.btn_save_svg = QPushButton("💾 SVG")
        self.btn_save_svg.clicked.connect(lambda: self._export("svg"))
        self.btn_save_png.setEnabled(False)
        self.btn_save_jpg.setEnabled(False)
        self.btn_save_svg.setEnabled(False)
        export_row.addWidget(self.btn_save_png)
        export_row.addWidget(self.btn_save_jpg)
        export_row.addWidget(self.btn_save_svg)
        right_layout.addLayout(export_row)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

    def _on_type_changed(self, index):
        """切换输入类型"""
        types = ["text", "wifi", "vcard"]
        for i, (key, widget) in enumerate(self.content_stack.items()):
            widget.setVisible(i == index)

    def _pick_fg_color(self):
        """选择前景色"""
        color = QColorDialog.getColor(QColor(self.fg_color), self, "选择前景色")
        if color.isValid():
            self.fg_color = color.name()
            self.btn_fg.setStyleSheet(f"background-color: {self.fg_color}; color: {'#000000' if color.lightness() > 128 else '#ffffff'};")

    def _pick_bg_color(self):
        """选择背景色"""
        color = QColorDialog.getColor(QColor(self.bg_color), self, "选择背景色")
        if color.isValid():
            self.bg_color = color.name()
            self.btn_bg.setStyleSheet(f"background-color: {self.bg_color}; color: {'#000000' if color.lightness() > 128 else '#ffffff'};")

    def _pick_logo(self):
        """选择Logo"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择Logo图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        if path:
            self.logo_path = path
            name = os.path.basename(path)
            self.logo_label.setText(f"📎 {name}")

    def _clear_logo(self):
        """清除Logo"""
        self.logo_path = None
        self.logo_label.setText("未选择Logo")

    def _get_content(self) -> tuple[str, str]:
        """获取当前输入内容"""
        index = self.type_combo.currentIndex()
        if index == 0:  # 文本
            text = self.text_input.toPlainText().strip()
            return text, "text"
        elif index == 1:  # WiFi
            ssid = self.wifi_ssid.text().strip()
            password = self.wifi_password.text().strip()
            security = self.wifi_security.currentText()
            hidden = self.wifi_hidden.isChecked()
            if not ssid:
                return "", "wifi"
            data = self.qr_generator.generate_wifi(ssid, password, security, hidden)
            return data, "wifi"
        elif index == 2:  # vCard
            name = self.vcard_name.text().strip()
            if not name:
                return "", "vcard"
            data = self.qr_generator.generate_vcard(
                name=name,
                phone=self.vcard_phone.text().strip(),
                email=self.vcard_email.text().strip(),
                org=self.vcard_org.text().strip(),
                title=self.vcard_title.text().strip(),
                url=self.vcard_url.text().strip(),
            )
            return data, "vcard"
        return "", "text"

    def _generate(self):
        """生成二维码"""
        content, qr_type = self._get_content()
        if not content:
            QMessageBox.warning(self, "提示", "请输入内容后再生成二维码")
            return

        try:
            self.current_image = self.qr_generator.generate(
                data=content,
                fg_color=self.fg_color,
                bg_color=self.bg_color,
                size=self.size_spin.value(),
                logo_path=self.logo_path,
            )

            # 更新预览
            self._update_preview()

            # 启用导出按钮
            self.btn_save_png.setEnabled(True)
            self.btn_save_jpg.setEnabled(True)
            self.btn_save_svg.setEnabled(True)

            # 保存到历史
            self.history_manager.add(content, qr_type)
            self.qr_generated.emit(content, qr_type, "")

            self.info_label.setText(f"✅ 生成成功 | 类型: {qr_type} | 尺寸: {self.current_image.size[0]}×{self.current_image.size[1]}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成二维码失败:\n{str(e)}")

    def _update_preview(self):
        """更新预览图片"""
        if self.current_image is None:
            return

        # PIL -> QPixmap
        img = self.current_image.copy()
        if img.mode != "RGB":
            img = img.convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # 缩放适配
        preview_size = self.preview_label.size()
        scaled = pixmap.scaled(
            preview_size.width() - 20,
            preview_size.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _export(self, fmt: str):
        """导出二维码"""
        if self.current_image is None:
            return

        filters = {
            "png": "PNG图片 (*.png)",
            "jpg": "JPG图片 (*.jpg *.jpeg)",
            "svg": "SVG矢量图 (*.svg)",
        }

        path, _ = QFileDialog.getSaveFileName(
            self, "导出二维码", f"qrcode.{fmt}",
            filters.get(fmt, "所有文件 (*.*)")
        )

        if not path:
            return

        try:
            if fmt == "svg":
                content, _ = self._get_content()
                svg_data = self.qr_generator.generate_svg(
                    content,
                    fg_color=self.fg_color,
                    bg_color=self.bg_color,
                )
                with open(path, "w", encoding="utf-8") as f:
                    f.write(svg_data)
            else:
                img = self.current_image.copy()
                if fmt == "jpg" and img.mode == "RGBA":
                    img = img.convert("RGB")
                img.save(path, quality=95)

            self.info_label.setText(f"✅ 已导出: {path}")
            QMessageBox.information(self, "成功", f"二维码已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
