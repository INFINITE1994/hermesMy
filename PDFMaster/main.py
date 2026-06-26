"""PDFMaster - 专业PDF处理工具"""
import sys, os, io, re, math
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QComboBox, QProgressBar, QMessageBox, QStackedWidget,
    QFrame, QGraphicsDropShadowEffect, QTextEdit, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QMimeData, QUrl
from PyQt6.QtGui import (
    QColor, QLinearGradient, QPainter, QFont, QDragEnterEvent, QDropEvent,
    QIcon, QPalette, QBrush, QPen, QPixmap
)

# ── Workers ──────────────────────────────────────────────────────────────

class MergeWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, files, output):
        super().__init__()
        self.files = files
        self.output = output

    def run(self):
        try:
            from PyPDF2 import PdfMerger
            merger = PdfMerger()
            for i, f in enumerate(self.files):
                merger.append(f)
                self.progress.emit(int((i + 1) / len(self.files) * 100))
            merger.write(self.output)
            merger.close()
            self.finished.emit(self.output)
        except Exception as e:
            self.error.emit(str(e))


class SplitWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file, ranges_str, output_dir):
        super().__init__()
        self.file = file
        self.ranges_str = ranges_str
        self.output_dir = output_dir

    def run(self):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(self.file)
            total = len(reader.pages)
            ranges = self._parse_ranges(self.ranges_str, total)
            outputs = []
            for idx, (start, end) in enumerate(ranges):
                writer = PdfWriter()
                for p in range(start - 1, end):
                    writer.add_page(reader.pages[p])
                out_path = os.path.join(self.output_dir, f"split_{idx + 1}_p{start}-{end}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)
                outputs.append(out_path)
                self.progress.emit(int((idx + 1) / len(ranges) * 100))
            self.finished.emit("\n".join(outputs))
        except Exception as e:
            self.error.emit(str(e))

    def _parse_ranges(self, s, total):
        parts = re.split(r'[,;，；\s]+', s.strip())
        ranges = []
        for part in parts:
            part = part.strip()
            if '-' in part:
                a, b = part.split('-', 1)
                ranges.append((int(a.strip()), int(b.strip())))
            else:
                n = int(part)
                ranges.append((n, n))
        return ranges


class CompressWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file, output, quality):
        super().__init__()
        self.file = file
        self.output = output
        self.quality = quality

    def run(self):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(self.file)
            writer = PdfWriter()
            total = len(reader.pages)
            for i, page in enumerate(reader.pages):
                writer.add_page(page)
                self.progress.emit(int((i + 1) / total * 80))
            # Remove metadata & duplicates
            writer.add_metadata({})
            for page in writer.pages:
                page.compress_content_streams()
            self.progress.emit(90)
            with open(self.output, "wb") as f:
                writer.write(f)
            self.progress.emit(100)
            orig = os.path.getsize(self.file)
            new = os.path.getsize(self.output)
            ratio = (1 - new / orig) * 100 if orig else 0
            self.finished.emit(f"{self.output}\n原始: {self._fmt(orig)} → 压缩后: {self._fmt(new)} (减少 {ratio:.1f}%)")
        except Exception as e:
            self.error.emit(str(e))

    def _fmt(self, b):
        for u in ['B', 'KB', 'MB', 'GB']:
            if b < 1024: return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"


class WatermarkWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file, output, text, font_size, opacity, color, rotation):
        super().__init__()
        self.file = file
        self.output = output
        self.text = text
        self.font_size = font_size
        self.opacity = opacity
        self.color = color
        self.rotation = rotation

    def run(self):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from PyPDF2.generic import NameObject, NumberObject, ArrayObject, DictionaryObject, TextStringObject
            reader = PdfReader(self.file)
            writer = PdfWriter()
            total = len(reader.pages)
            for i, page in enumerate(reader.pages):
                wm_page = self._create_watermark_page(page, self.text)
                page.merge_page(wm_page)
                writer.add_page(page)
                self.progress.emit(int((i + 1) / total * 100))
            with open(self.output, "wb") as f:
                writer.write(f)
            self.finished.emit(self.output)
        except Exception as e:
            self.error.emit(str(e))

    def _create_watermark_page(self, page, text):
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter
        import io
        box = page.mediabox
        w, h = float(box.width), float(box.height)
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(w, h))
        c.saveState()
        c.setFont("Helvetica", self.font_size)
        c.setFillAlpha(self.opacity / 100.0)
        # Parse color hex
        color_hex = self.color.lstrip('#')
        r, g, b = int(color_hex[0:2], 16)/255, int(color_hex[2:4], 16)/255, int(color_hex[4:6], 16)/255
        c.setFillColorRGB(r, g, b)
        c.translate(w / 2, h / 2)
        c.rotate(self.rotation)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()
        packet.seek(0)
        wm_reader = PdfReader(packet)
        return wm_reader.pages[0]


class TextExtractWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file, output):
        super().__init__()
        self.file = file
        self.output = output

    def run(self):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(self.file)
            total = len(reader.pages)
            all_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    all_text.append(f"═══ 第 {i+1} 页 ═══\n{txt}")
                self.progress.emit(int((i + 1) / total * 100))
            result = "\n\n".join(all_text)
            with open(self.output, "w", encoding="utf-8") as f:
                f.write(result)
            self.finished.emit(f"{self.output}\n共提取 {total} 页，{len(result)} 字符")
        except Exception as e:
            self.error.emit(str(e))


class ImageExportWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file, output_dir, fmt, dpi):
        super().__init__()
        self.file = file
        self.output_dir = output_dir
        self.fmt = fmt
        self.dpi = dpi

    def run(self):
        try:
            # Try pdf2image first (requires poppler)
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(self.file, dpi=self.dpi)
                total = len(images)
                out_files = []
                for i, img in enumerate(images):
                    out_path = os.path.join(self.output_dir, f"page_{i + 1}.{self.fmt}")
                    img.save(out_path, self.fmt.upper())
                    out_files.append(out_path)
                    self.progress.emit(int((i + 1) / total * 100))
                self.finished.emit("\n".join(out_files))
                return
            except ImportError:
                pass
            except Exception:
                pass

            # Fallback: render with PyMuPDF if available
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(self.file)
                total = len(doc)
                out_files = []
                for i in range(total):
                    page = doc[i]
                    zoom = self.dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    out_path = os.path.join(self.output_dir, f"page_{i + 1}.{self.fmt}")
                    pix.save(out_path)
                    out_files.append(out_path)
                    self.progress.emit(int((i + 1) / total * 100))
                doc.close()
                self.finished.emit("\n".join(out_files))
                return
            except ImportError:
                pass

            self.error.emit("需要安装 pdf2image+poppler 或 PyMuPDF (pymupdf) 才能导出图片。\n请运行: pip install pymupdf")
        except Exception as e:
            self.error.emit(str(e))


# ── Drag-drop list ───────────────────────────────────────────────────────

class DragDropList(QListWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, placeholder="拖拽PDF文件到此处"):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.placeholder = placeholder
        self.setStyleSheet("""
            QListWidget {
                background: #0d0d1a;
                border: 2px dashed #333355;
                border-radius: 12px;
                color: #ccccdd;
                font-size: 14px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
            QListWidget::item:hover {
                background: #1a1a2e;
            }
        """)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        files = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith('.pdf'):
                files.append(p)
        if files:
            self.files_dropped.emit(files)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            p = QPainter(self.viewport())
            p.setFont(QFont("Microsoft YaHei", 14))
            p.setPen(QColor(80, 80, 120))
            p.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.placeholder)
            p.end()


# ── Gradient Button ──────────────────────────────────────────────────────

class GradientButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7b93ff, stop:1 #8b5fcf);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5570dd, stop:1 #653a91);
            }
            QPushButton:disabled {
                background: #333344;
                color: #666677;
            }
        """)


class SmallButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(34)
        self.setFont(QFont("Microsoft YaHei", 10))
        self.setStyleSheet("""
            QPushButton {
                background: #1a1a2e;
                color: #aaaacc;
                border: 1px solid #333355;
                border-radius: 8px;
                padding: 4px 14px;
            }
            QPushButton:hover {
                background: #252545;
                color: #ddddee;
                border-color: #555577;
            }
        """)


# ── Card Frame ───────────────────────────────────────────────────────────

class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #111122;
                border-radius: 16px;
                border: 1px solid #1a1a33;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)


# ── Tab Pages ────────────────────────────────────────────────────────────

class MergePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("合并PDF文件")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("将多个PDF文件按顺序合并为一个文件")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        self.list = DragDropList("拖拽PDF文件到此处添加")
        self.list.files_dropped.connect(self._add_files)
        layout.addWidget(self.list, 1)

        btn_row = QHBoxLayout()
        add_btn = SmallButton("+ 添加文件")
        add_btn.clicked.connect(self._browse)
        remove_btn = SmallButton("- 移除选中")
        remove_btn.clicked.connect(self._remove)
        clear_btn = SmallButton("清空列表")
        clear_btn.clicked.connect(self.list.clear)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.btn = GradientButton("开始合并")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)

        self.worker = None

    def _add_files(self, files):
        for f in files:
            if not any(self.list.item(i).data(Qt.ItemDataRole.UserRole) == f for i in range(self.list.count())):
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.ItemDataRole.UserRole, f)
                item.setToolTip(f)
                self.list.addItem(item)

    def _browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF (*.pdf)")
        self._add_files(files)

    def _remove(self):
        for item in reversed(self.list.selectedItems()):
            self.list.takeItem(self.list.row(item))

    def _run(self):
        if self.list.count() < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个PDF文件")
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存合并后的PDF", "merged.pdf", "PDF (*.pdf)")
        if not out:
            return
        files = [self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())]
        self.btn.setEnabled(False)
        self.progress.setValue(0)
        self.worker = MergeWorker(files, out)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self._done)
        self.worker.error.connect(self._err)
        self.worker.start()

    def _done(self, path):
        self.btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"合并完成！\n{path}")

    def _err(self, msg):
        self.btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


class SplitPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("拆分PDF文件")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("按页码范围将PDF拆分为多个文件")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择PDF文件...")
        self.file_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        browse_btn = SmallButton("浏览...")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        range_label = QLabel("页码范围（如: 1-3, 5, 7-10）")
        range_label.setStyleSheet("color: #9999bb; font-size: 13px;")
        layout.addWidget(range_label)

        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText("1-3, 5, 7-10")
        self.range_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        layout.addWidget(self.range_edit)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        self.btn = GradientButton("开始拆分")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)
        layout.addStretch()

        self.worker = None

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")
        if f: self.file_edit.setText(f)

    def _run(self):
        if not self.file_edit.text() or not self.range_edit.text():
            QMessageBox.warning(self, "提示", "请选择文件并输入页码范围")
            return
        out_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not out_dir: return
        self.btn.setEnabled(False)
        self.worker = SplitWorker(self.file_edit.text(), self.range_edit.text(), out_dir)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self._done)
        self.worker.error.connect(self._err)
        self.worker.start()

    def _done(self, msg):
        self.btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"拆分完成！\n{msg}")

    def _err(self, msg):
        self.btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


class CompressPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("压缩PDF文件")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("通过优化内部结构减小PDF文件体积")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择PDF文件...")
        self.file_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        browse_btn = SmallButton("浏览...")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        self.btn = GradientButton("开始压缩")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)
        layout.addStretch()
        self.worker = None

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")
        if f: self.file_edit.setText(f)

    def _run(self):
        if not self.file_edit.text():
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存", "compressed.pdf", "PDF (*.pdf)")
        if not out: return
        self.btn.setEnabled(False)
        self.worker = CompressWorker(self.file_edit.text(), out, 75)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self._done)
        self.worker.error.connect(self._err)
        self.worker.start()

    def _done(self, msg):
        self.btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"压缩完成！\n{msg}")

    def _err(self, msg):
        self.btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


class WatermarkPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("添加文字水印")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("为PDF每一页添加自定义文字水印")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择PDF文件...")
        self.file_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        browse_btn = SmallButton("浏览...")
        browse_btn.clicked.connect(lambda: self._set_file(QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        form = QGridLayout()
        form.setSpacing(10)

        def styled_line():
            le = QLineEdit()
            le.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
            return le

        def styled_spin(lo, hi, val):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            s.setStyleSheet("QSpinBox { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px; color: #ccccee; }")
            return s

        lbl = lambda t: QLabel(t)

        self.text_edit = styled_line()
        self.text_edit.setText("机密文件")
        self.text_edit.setPlaceholderText("水印文字")
        self.size_spin = styled_spin(10, 200, 48)
        self.opacity_spin = styled_spin(5, 100, 30)
        self.rotation_spin = styled_spin(-180, 180, 45)
        self.color_edit = styled_line()
        self.color_edit.setText("#888888")

        r = 0
        for label, widget in [("水印文字:", self.text_edit), ("字号:", self.size_spin), ("透明度%:", self.opacity_spin), ("旋转角度:", self.rotation_spin), ("颜色(十六进制):", self.color_edit)]:
            l = lbl(label)
            l.setStyleSheet("color: #9999bb; font-size: 13px;")
            form.addWidget(l, r, 0)
            form.addWidget(widget, r, 1)
            r += 1
        layout.addLayout(form)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        self.btn = GradientButton("添加水印")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)
        layout.addStretch()
        self.worker = None

    def _set_file(self, res):
        f = res[0] if isinstance(res, tuple) else res
        if f: self.file_edit.setText(f)

    def _run(self):
        if not self.file_edit.text():
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存", "watermarked.pdf", "PDF (*.pdf)")
        if not out: return
        self.btn.setEnabled(False)
        self.worker = WatermarkWorker(
            self.file_edit.text(), out, self.text_edit.text(),
            self.size_spin.value(), self.opacity_spin.value(),
            self.color_edit.text(), self.rotation_spin.value()
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(lambda p: (self.btn.setEnabled(True), QMessageBox.information(self, "完成", f"水印已添加！\n{p}")))
        self.worker.error.connect(lambda m: (self.btn.setEnabled(True), QMessageBox.critical(self, "错误", m)))
        self.worker.start()


class ImageExportPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("PDF转图片")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("将PDF每一页导出为PNG或JPG图片")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择PDF文件...")
        self.file_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        browse_btn = SmallButton("浏览...")
        browse_btn.clicked.connect(lambda: self._set_file(QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        opt_row = QHBoxLayout()
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["png", "jpg"])
        self.fmt_combo.setStyleSheet("QComboBox { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px; color: #ccccee; } QComboBox QAbstractItemView { background: #111122; color: #ccccee; selection-background-color: #667eea; }")
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setStyleSheet("QSpinBox { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px; color: #ccccee; }")
        opt_row.addWidget(QLabel("格式:"))
        opt_row.addWidget(self.fmt_combo)
        opt_row.addWidget(QLabel("DPI:"))
        opt_row.addWidget(self.dpi_spin)
        opt_row.addStretch()
        for w in [self.fmt_combo, self.dpi_spin]:
            pass
        # Style labels
        for i in range(opt_row.count()):
            w = opt_row.itemAt(i).widget()
            if isinstance(w, QLabel):
                w.setStyleSheet("color: #9999bb; font-size: 13px;")
        layout.addLayout(opt_row)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        self.btn = GradientButton("开始导出")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)
        layout.addStretch()
        self.worker = None

    def _set_file(self, res):
        f = res[0] if isinstance(res, tuple) else res
        if f: self.file_edit.setText(f)

    def _run(self):
        if not self.file_edit.text():
            return
        out_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not out_dir: return
        self.btn.setEnabled(False)
        self.worker = ImageExportWorker(self.file_edit.text(), out_dir, self.fmt_combo.currentText(), self.dpi_spin.value())
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(lambda m: (self.btn.setEnabled(True), QMessageBox.information(self, "完成", f"导出完成！\n{m}")))
        self.worker.error.connect(lambda m: (self.btn.setEnabled(True), QMessageBox.critical(self, "错误", m)))
        self.worker.start()


class TextExtractPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("提取PDF文本")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #eeeef5;")
        layout.addWidget(title)

        desc = QLabel("从PDF文件中提取全部文字内容并保存为TXT")
        desc.setStyleSheet("color: #7777aa; font-size: 13px;")
        layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择PDF文件...")
        self.file_edit.setStyleSheet("QLineEdit { background: #0d0d1a; border: 1px solid #333355; border-radius: 8px; padding: 8px 12px; color: #ccccee; font-size: 13px; }")
        browse_btn = SmallButton("浏览...")
        browse_btn.clicked.connect(lambda: self._set_file(QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #0d0d1a; border: 1px solid #333355; border-radius: 6px; height: 22px; text-align: center; color: #aaaacc; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        self.btn = GradientButton("开始提取")
        self.btn.clicked.connect(self._run)
        layout.addWidget(self.btn)
        layout.addStretch()
        self.worker = None

    def _set_file(self, res):
        f = res[0] if isinstance(res, tuple) else res
        if f: self.file_edit.setText(f)

    def _run(self):
        if not self.file_edit.text():
            return
        out, _ = QFileDialog.getSaveFileName(self, "保存", "extracted.txt", "文本 (*.txt)")
        if not out: return
        self.btn.setEnabled(False)
        self.worker = TextExtractWorker(self.file_edit.text(), out)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(lambda m: (self.btn.setEnabled(True), QMessageBox.information(self, "完成", f"提取完成！\n{m}")))
        self.worker.error.connect(lambda m: (self.btn.setEnabled(True), QMessageBox.critical(self, "错误", m)))
        self.worker.start()


# ── Main Window ──────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    NAV_ITEMS = [
        ("📄", "合并PDF"),
        ("✂️", "拆分PDF"),
        ("📦", "压缩PDF"),
        ("💧", "添加水印"),
        ("🖼️", "转为图片"),
        ("📝", "提取文本"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDFMaster - 专业PDF处理工具")
        self.setMinimumSize(960, 640)
        self.resize(1080, 720)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("QFrame { background: #08081a; border-right: 1px solid #1a1a33; }")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 24, 16, 24)
        sb_layout.setSpacing(4)

        logo = QLabel("PDFMaster")
        logo.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        logo.setStyleSheet("color: #eeeef5;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(logo)

        sub = QLabel("专业PDF处理工具")
        sub.setStyleSheet("color: #6666aa; font-size: 12px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(sub)

        sb_layout.addSpacing(24)

        self.nav_buttons = []
        for icon, label in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setFont(QFont("Microsoft YaHei", 11))
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #8888aa; border: none; border-radius: 10px; text-align: left; padding-left: 16px; }
                QPushButton:hover { background: #151530; color: #bbbbdd; }
            """)
            btn.clicked.connect(lambda checked, b=btn, i=self.NAV_ITEMS.index((icon,label)): self._nav(i))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()
        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #444466; font-size: 11px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # Content
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #0a0a0a; }")
        self.pages = [MergePage(), SplitPage(), CompressPage(), WatermarkPage(), ImageExportPage(), TextExtractPage()]
        for p in self.pages:
            self.stack.addWidget(p)
        main_layout.addWidget(self.stack, 1)

        self._nav(0)

    def _nav(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_buttons):
            if i == idx:
                btn.setStyleSheet("""
                    QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2); color: white; border: none; border-radius: 10px; text-align: left; padding-left: 16px; font-weight: bold; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #8888aa; border: none; border-radius: 10px; text-align: left; padding-left: 16px; }
                    QPushButton:hover { background: #151530; color: #bbbbdd; }
                """)


# ── Entry ────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Dark palette fallback
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(13, 13, 26))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 20, 40))
    palette.setColor(QPalette.ColorRole.Text, QColor(200, 200, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(20, 20, 40))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(200, 200, 220))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
