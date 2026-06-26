"""扫描识别标签页"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QTextEdit, QMessageBox, QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image


class ScanTab(QWidget):
    """扫描识别标签页"""

    def __init__(self, qr_scanner):
        super().__init__()
        self.qr_scanner = qr_scanner
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔍 扫描识别二维码")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("从图片文件中识别二维码内容")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # 主内容区域
        content_layout = QHBoxLayout()

        # 左侧：图片预览
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)

        self.image_label = QLabel("拖放图片到此处\n或点击下方按钮选择")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(350, 350)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px dashed #3a3a4a;
                border-radius: 12px;
                font-size: 16px;
                color: #666688;
            }
        """)
        self.image_label.setAcceptDrops(True)
        left_layout.addWidget(self.image_label)

        # 按钮行
        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("📂 选择图片")
        self.btn_open.setObjectName("primary")
        self.btn_open.clicked.connect(self._open_image)
        self.btn_paste = QPushButton("📋 粘贴图片")
        self.btn_paste.clicked.connect(self._paste_image)
        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_paste)
        left_layout.addLayout(btn_row)

        # 文件路径
        self.path_label = QLabel("")
        self.path_label.setObjectName("subtitle")
        self.path_label.setWordWrap(True)
        left_layout.addWidget(self.path_label)

        content_layout.addWidget(left_panel)

        # 右侧：识别结果
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)

        result_title = QLabel("📋 识别结果")
        result_title.setObjectName("sectionTitle")
        right_layout.addWidget(result_title)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("识别结果将在此处显示...")
        self.result_text.setMinimumHeight(200)
        right_layout.addWidget(self.result_text, 1)

        # 操作按钮
        action_row = QHBoxLayout()
        self.btn_copy = QPushButton("📋 复制内容")
        self.btn_copy.clicked.connect(self._copy_result)
        self.btn_clear = QPushButton("🗑️ 清除")
        self.btn_clear.clicked.connect(self._clear)
        action_row.addWidget(self.btn_copy)
        action_row.addWidget(self.btn_clear)
        right_layout.addLayout(action_row)

        # 状态
        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitle")
        right_layout.addWidget(self.status_label)

        content_layout.addWidget(right_panel)
        layout.addLayout(content_layout, 1)

        # 启用拖放
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                self._scan_file(file_path)

    def _open_image(self):
        """打开图片文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择二维码图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*.*)"
        )
        if path:
            self._scan_file(path)

    def _paste_image(self):
        """从剪贴板粘贴图片"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        if pixmap and not pixmap.isNull():
            # QPixmap -> PIL Image
            qimg = pixmap.toImage()
            buffer = qimg.bits().asstring(qimg.width() * qimg.height() * 4)
            img = Image.frombuffer("RGBA", (qimg.width(), qimg.height()), buffer, "raw", "BGRA")
            self._show_image(pixmap)
            self._scan_pil_image(img)
        else:
            QMessageBox.information(self, "提示", "剪贴板中没有图片")

    def _scan_file(self, file_path: str):
        """扫描文件"""
        self.path_label.setText(f"📁 {file_path}")

        # 显示预览
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self._show_image(pixmap)

        # 识别
        try:
            results = self.qr_scanner.scan_from_file(file_path)
            self._show_results(results)
            self.status_label.setText(f"✅ 成功识别 {len(results)} 个二维码")
        except Exception as e:
            self.result_text.setPlainText(f"❌ 识别失败: {str(e)}")
            self.status_label.setText("❌ 识别失败")

    def _scan_pil_image(self, img: Image.Image):
        """扫描PIL图片"""
        try:
            results = self.qr_scanner.scan_from_image(img)
            self._show_results(results)
            self.status_label.setText(f"✅ 成功识别 {len(results)} 个二维码")
        except Exception as e:
            self.result_text.setPlainText(f"❌ 识别失败: {str(e)}")
            self.status_label.setText("❌ 识别失败")

    def _show_image(self, pixmap: QPixmap):
        """显示图片预览"""
        label_size = self.image_label.size()
        scaled = pixmap.scaled(
            label_size.width() - 20,
            label_size.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _show_results(self, results: list[str]):
        """显示识别结果"""
        if not results:
            self.result_text.setPlainText("未识别到二维码内容")
            return

        display = []
        for i, content in enumerate(results, 1):
            if len(results) > 1:
                display.append(f"--- 二维码 #{i} ---\n{content}")
            else:
                display.append(content)

        self.result_text.setPlainText("\n\n".join(display))

    def _copy_result(self):
        """复制结果"""
        text = self.result_text.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.status_label.setText("📋 已复制到剪贴板")

    def _clear(self):
        """清除"""
        self.image_label.clear()
        self.image_label.setText("拖放图片到此处\n或点击下方按钮选择")
        self.result_text.clear()
        self.path_label.clear()
        self.status_label.clear()
