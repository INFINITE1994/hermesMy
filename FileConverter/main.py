#!/usr/bin/env python3
"""
FileConverter - 通用文件格式转换器
支持图片、文档、音频、视频、压缩包等多种格式转换
"""

import sys
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
    QMessageBox, QTextEdit, QGroupBox, QSpinBox
)
from PyQt6.QtCore import (
    Qt, QSize, QThread, pyqtSignal, QUrl
)
from PyQt6.QtGui import (
    QPixmap, QDragEnterEvent, QDropEvent, QAction
)

# 尝试导入可选依赖
try:
    from PIL import Image, ImageQt
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

try:
    import moviepy.editor as mp
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

try:
    from docx import Document
    from docx.shared import Inches
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False

import zipfile
import tarfile
import gzip
import bz2
import lzma


# 常量定义
APP_NAME = "FileConverter"
APP_VERSION = "1.0.0"
APP_TITLE = "通用文件格式转换器"

# 颜色常量
COLORS = {
    'bg': '#0a0a0a',
    'card': '#111122',
    'card_hover': '#1a1a33',
    'accent_start': '#667eea',
    'accent_end': '#764ba2',
    'text': '#ffffff',
    'text_secondary': '#8888aa',
    'success': '#4ade80',
    'error': '#f87171',
    'warning': '#fbbf24',
    'border': '#2a2a44',
}

# 格式定义
IMAGE_FORMATS = ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'ICO']
AUDIO_FORMATS = ['MP3', 'WAV', 'FLAC', 'OGG']
VIDEO_FORMATS = ['MP4', 'AVI', 'MKV', 'MOV']
ARCHIVE_FORMATS = ['ZIP', '7Z', 'TAR', 'GZ', 'BZ2', 'XZ']
DOCUMENT_FORMATS = ['PDF', 'DOCX', 'TXT']


class StyleSheet:
    """全局样式表"""
    
    MAIN = f"""
    QMainWindow {{
        background-color: {COLORS['bg']};
    }}
    
    QWidget {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    }}
    
    QLabel {{
        color: {COLORS['text']};
    }}
    
    QPushButton {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['card_hover']};
        border-color: {COLORS['accent_start']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['accent_start']};
    }}
    
    QPushButton:disabled {{
        background-color: #1a1a2e;
        color: #555577;
        border-color: #2a2a44;
    }}
    
    QComboBox {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 14px;
        min-width: 150px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS['accent_start']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text']};
        margin-right: 10px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['accent_start']};
        selection-color: white;
    }}
    
    QListWidget {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 5px;
        font-size: 13px;
    }}
    
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['accent_start']};
        color: white;
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['card_hover']};
    }}
    
    QProgressBar {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        text-align: center;
        color: {COLORS['text']};
        font-weight: bold;
        height: 25px;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
        border-radius: 7px;
    }}
    
    QTextEdit {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
    }}
    
    QSpinBox {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }}
    
    QCheckBox {{
        color: {COLORS['text']};
        spacing: 8px;
        font-size: 14px;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid {COLORS['border']};
        background-color: {COLORS['card']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_start']};
        border-color: {COLORS['accent_start']};
    }}
    
    QGroupBox {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        margin-top: 15px;
        padding-top: 25px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 5px 15px;
        background-color: {COLORS['accent_start']};
        color: white;
        border-radius: 5px;
        margin-left: 15px;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['bg']};
        width: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_start']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QTabWidget::pane {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['bg']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        margin-right: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border-bottom: 2px solid {COLORS['accent_start']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {COLORS['card_hover']};
        color: {COLORS['text']};
    }}
    
    QStatusBar {{
        background-color: {COLORS['card']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border']};
        font-size: 12px;
    }}
    
    QMenuBar {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['accent_start']};
    }}
    
    QMenu {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['accent_start']};
    }}
    
    QToolBar {{
        background-color: {COLORS['card']};
        border-bottom: 1px solid {COLORS['border']};
        spacing: 5px;
        padding: 5px;
    }}
    
    QSplitter::handle {{
        background-color: {COLORS['border']};
        width: 2px;
    }}
    """
    
    GRADIENT_BUTTON = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 25px;
        font-size: 15px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_start']}, stop:1 {COLORS['accent_end']});
        opacity: 0.9;
    }}
    
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_end']}, stop:1 {COLORS['accent_start']});
    }}
    
    QPushButton:disabled {{
        background: #2a2a44;
        color: #555577;
    }}
    """
    
    CARD = f"""
    QFrame {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 15px;
    }}
    
    QFrame:hover {{
        border-color: {COLORS['accent_start']};
    }}
    """
    
    NAV_BUTTON = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        border: none;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 14px;
        text-align: left;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
    }}
    
    QPushButton:checked {{
        background-color: {COLORS['card']};
        color: {COLORS['accent_start']};
        border-left: 3px solid {COLORS['accent_start']};
    }}
    """


class ConverterThread(QThread):
    """转换线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)
    
    def __init__(self, input_files: List[str], output_format: str, output_dir: str, 
                 options: Dict[str, Any] = None):
        super().__init__()
        self.input_files = input_files
        self.output_format = output_format.lower()
        self.output_dir = output_dir
        self.options = options or {}
        self.is_cancelled = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        total = len(self.input_files)
        success_count = 0
        
        for i, input_file in enumerate(self.input_files):
            if self.is_cancelled:
                self.log.emit("⚠️ 转换已取消")
                self.finished.emit(False, "转换已取消")
                return
                
            try:
                self.log.emit(f"🔄 正在转换: {os.path.basename(input_file)}")
                
                # 确定输出文件路径
                input_path = Path(input_file)
                output_filename = input_path.stem + '.' + self.output_format
                output_path = Path(self.output_dir) / output_filename
                
                # 避免文件名冲突
                counter = 1
                while output_path.exists():
                    output_filename = f"{input_path.stem}_{counter}.{self.output_format}"
                    output_path = Path(self.output_dir) / output_filename
                    counter += 1
                
                # 根据输入文件类型选择转换方法
                input_ext = input_path.suffix.lower().lstrip('.')
                
                if input_ext in [f.lower() for f in IMAGE_FORMATS]:
                    success = self.convert_image(input_file, str(output_path))
                elif input_ext in [f.lower() for f in AUDIO_FORMATS]:
                    success = self.convert_audio(input_file, str(output_path))
                elif input_ext in [f.lower() for f in VIDEO_FORMATS]:
                    success = self.convert_video(input_file, str(output_path))
                elif input_ext in [f.lower() for f in ARCHIVE_FORMATS]:
                    success = self.convert_archive(input_file, str(output_path))
                elif input_ext in ['txt', 'docx', 'pdf']:
                    success = self.convert_document(input_file, str(output_path))
                else:
                    # 尝试直接复制
                    shutil.copy2(input_file, str(output_path))
                    success = True
                
                if success:
                    success_count += 1
                    self.log.emit(f"✅ 转换成功: {os.path.basename(input_file)} -> {output_filename}")
                else:
                    self.log.emit(f"❌ 转换失败: {os.path.basename(input_file)}")
                    
            except Exception as e:
                self.log.emit(f"❌ 转换错误: {os.path.basename(input_file)} - {str(e)}")
            
            # 更新进度
            progress = int((i + 1) / total * 100)
            self.progress.emit(progress)
        
        if success_count == total:
            self.finished.emit(True, f"成功转换 {success_count}/{total} 个文件")
        else:
            self.finished.emit(False, f"转换完成: {success_count}/{total} 个成功")
    
    def convert_image(self, input_file: str, output_file: str) -> bool:
        """转换图片格式"""
        if not HAS_PIL:
            self.log.emit("⚠️ 需要安装 Pillow: pip install Pillow")
            return False
            
        try:
            img = Image.open(input_file)
            
            # 处理透明通道
            if self.output_format in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA', 'P']:
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 设置保存参数
            save_kwargs = {}
            if self.output_format in ['jpg', 'jpeg']:
                save_kwargs['quality'] = self.options.get('quality', 95)
                save_kwargs['optimize'] = True
            elif self.output_format == 'png':
                save_kwargs['optimize'] = True
            elif self.output_format == 'webp':
                save_kwargs['quality'] = self.options.get('quality', 90)
            elif self.output_format == 'ico':
                # ICO需要特定尺寸
                sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                save_kwargs['sizes'] = sizes
            
            img.save(output_file, **save_kwargs)
            return True
            
        except Exception as e:
            self.log.emit(f"图片转换错误: {str(e)}")
            return False
    
    def convert_audio(self, input_file: str, output_file: str) -> bool:
        """转换音频格式"""
        if not HAS_PYDUB:
            self.log.emit("⚠️ 需要安装 pydub: pip install pydub")
            self.log.emit("⚠️ 还需要安装 FFmpeg")
            return False
            
        try:
            audio = AudioSegment.from_file(input_file)
            
            # 设置导出参数
            export_kwargs = {}
            if self.output_format == 'mp3':
                export_kwargs['bitrate'] = self.options.get('bitrate', '320k')
            elif self.output_format == 'wav':
                export_kwargs['parameters'] = ['-ar', '44100', '-ac', '2']
            
            audio.export(output_file, format=self.output_format, **export_kwargs)
            return True
            
        except Exception as e:
            self.log.emit(f"音频转换错误: {str(e)}")
            return False
    
    def convert_video(self, input_file: str, output_file: str) -> bool:
        """转换视频格式"""
        if not HAS_MOVIEPY:
            self.log.emit("⚠️ 需要安装 moviepy: pip install moviepy")
            self.log.emit("⚠️ 还需要安装 FFmpeg")
            return False
            
        try:
            video = mp.VideoFileClip(input_file)
            
            # 设置导出参数
            export_kwargs = {}
            if self.output_format == 'mp4':
                export_kwargs['codec'] = 'libx264'
                export_kwargs['bitrate'] = self.options.get('bitrate', '8000k')
            elif self.output_format == 'avi':
                export_kwargs['codec'] = 'png'
            
            video.write_videofile(output_file, **export_kwargs)
            video.close()
            return True
            
        except Exception as e:
            self.log.emit(f"视频转换错误: {str(e)}")
            return False
    
    def convert_archive(self, input_file: str, output_file: str) -> bool:
        """转换压缩包格式"""
        try:
            input_ext = Path(input_file).suffix.lower()
            
            # 先解压到临时目录
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # 解压源文件
                if input_ext == '.zip':
                    with zipfile.ZipFile(input_file, 'r') as zf:
                        zf.extractall(temp_dir)
                elif input_ext == '.7z' and HAS_7Z:
                    with py7zr.SevenZipFile(input_file, 'r') as zf:
                        zf.extractall(temp_dir)
                elif input_ext == '.rar' and HAS_RAR:
                    with rarfile.RarFile(input_file, 'r') as rf:
                        rf.extractall(temp_dir)
                elif input_ext == '.tar':
                    with tarfile.open(input_file, 'r') as tf:
                        tf.extractall(temp_dir)
                elif input_ext == '.gz':
                    with gzip.open(input_file, 'rb') as f_in:
                        with open(os.path.join(temp_dir, Path(input_file).stem), 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif input_ext == '.bz2':
                    with bz2.open(input_file, 'rb') as f_in:
                        with open(os.path.join(temp_dir, Path(input_file).stem), 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif input_ext == '.xz':
                    with lzma.open(input_file, 'rb') as f_in:
                        with open(os.path.join(temp_dir, Path(input_file).stem), 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    self.log.emit(f"不支持的压缩格式: {input_ext}")
                    return False
                
                # 压缩为目标格式
                if self.output_format == 'zip':
                    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, temp_dir)
                                zf.write(file_path, arcname)
                elif self.output_format == 'tar':
                    with tarfile.open(output_file, 'w') as tf:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, temp_dir)
                                tf.add(file_path, arcname)
                elif self.output_format == 'gz':
                    with open(os.path.join(temp_dir, os.listdir(temp_dir)[0]), 'rb') as f_in:
                        with gzip.open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif self.output_format == 'bz2':
                    with open(os.path.join(temp_dir, os.listdir(temp_dir)[0]), 'rb') as f_in:
                        with bz2.open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif self.output_format == 'xz':
                    with open(os.path.join(temp_dir, os.listdir(temp_dir)[0]), 'rb') as f_in:
                        with lzma.open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif self.output_format == '7z' and HAS_7Z:
                    with py7zr.SevenZipFile(output_file, 'w') as zf:
                        zf.writeall(temp_dir, '')
                else:
                    self.log.emit(f"不支持的目标格式: {self.output_format}")
                    return False
            
            return True
            
        except Exception as e:
            self.log.emit(f"压缩包转换错误: {str(e)}")
            return False
    
    def convert_document(self, input_file: str, output_file: str) -> bool:
        """转换文档格式"""
        input_ext = Path(input_file).suffix.lower()
        
        try:
            # TXT 转 PDF
            if input_ext == '.txt' and self.output_format == 'pdf':
                if not HAS_PDF:
                    self.log.emit("⚠️ 需要安装 reportlab: pip install reportlab")
                    return False
                    
                c = canvas.Canvas(output_file, pagesize=letter)
                c.setFont("Helvetica", 12)
                
                with open(input_file, 'r', encoding='utf-8') as f:
                    y = 750
                    for line in f:
                        if y < 50:
                            c.showPage()
                            c.setFont("Helvetica", 12)
                            y = 750
                        c.drawString(50, y, line.strip())
                        y -= 15
                
                c.save()
                return True
            
            # DOCX 转 PDF
            elif input_ext == '.docx' and self.output_format == 'pdf':
                if not HAS_DOCX or not HAS_PDF:
                    self.log.emit("⚠️ 需要安装 python-docx 和 reportlab")
                    return False
                    
                doc = Document(input_file)
                c = canvas.Canvas(output_file, pagesize=letter)
                c.setFont("Helvetica", 12)
                
                y = 750
                for para in doc.paragraphs:
                    if y < 50:
                        c.showPage()
                        c.setFont("Helvetica", 12)
                        y = 750
                    
                    text = para.text.strip()
                    if text:
                        # 处理长文本换行
                        words = text.split()
                        line = ""
                        for word in words:
                            test_line = line + " " + word if line else word
                            if c.stringWidth(test_line, "Helvetica", 12) < 500:
                                line = test_line
                            else:
                                c.drawString(50, y, line)
                                y -= 15
                                line = word
                                if y < 50:
                                    c.showPage()
                                    c.setFont("Helvetica", 12)
                                    y = 750
                        if line:
                            c.drawString(50, y, line)
                            y -= 15
                
                c.save()
                return True
            
            # PDF 转文本（简化版本）
            elif input_ext == '.pdf' and self.output_format == 'txt':
                if not HAS_PDF:
                    self.log.emit("⚠️ 需要安装 pypdf: pip install pypdf")
                    return False
                    
                reader = PdfReader(input_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                return True
            
            else:
                self.log.emit(f"不支持的文档转换: {input_ext} -> {self.output_format}")
                return False
                
        except Exception as e:
            self.log.emit(f"文档转换错误: {str(e)}")
            return False


class DropArea(QFrame):
    """拖拽区域"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 提示文字
        self.label = QLabel("拖拽文件到这里\n或点击下方按钮添加")
        self.label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 16px;
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 2px dashed {COLORS['border']};
                border-radius: 15px;
                padding: 30px;
            }}
            
            QFrame:hover {{
                border-color: {COLORS['accent_start']};
                background-color: {COLORS['card_hover']};
            }}
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['card_hover']};
                    border: 2px dashed {COLORS['accent_start']};
                    border-radius: 15px;
                    padding: 30px;
                }}
            """)
            self.label.setText("释放以添加文件")
            self.label.setStyleSheet(f"color: {COLORS['accent_start']}; font-size: 16px;")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 2px dashed {COLORS['border']};
                border-radius: 15px;
                padding: 30px;
            }}
            
            QFrame:hover {{
                border-color: {COLORS['accent_start']};
                background-color: {COLORS['card_hover']};
            }}
        """)
        self.label.setText("拖拽文件到这里\n或点击下方按钮添加")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 16px;")
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 2px dashed {COLORS['border']};
                border-radius: 15px;
                padding: 30px;
            }}
            
            QFrame:hover {{
                border-color: {COLORS['accent_start']};
                background-color: {COLORS['card_hover']};
            }}
        """)
        self.label.setText("拖拽文件到这里\n或点击下方按钮添加")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 16px;")


class ImagePreviewWidget(QLabel):
    """图片预览组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        self.setText("选择图片以预览")
        
    def load_image(self, image_path: str):
        """加载并显示图片"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图片以适应预览区域
                scaled = pixmap.scaled(
                    self.size() - QSize(20, 20),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled)
            else:
                self.setText("无法加载图片")
        except Exception as e:
            self.setText(f"预览错误: {str(e)}")
    
    def clear_preview(self):
        """清除预览"""
        self.clear()
        self.setText("选择图片以预览")


class ConvertPage(QWidget):
    """转换页面基类"""
    
    def __init__(self, title: str, formats: List[str], parent=None):
        super().__init__(parent)
        self.title = title
        self.formats = formats
        self.files = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text']};
            padding: 10px 0;
        """)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 左侧 - 文件列表和控制
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        # 拖拽区域
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        left_layout.addWidget(self.drop_area)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加文件")
        self.add_btn.clicked.connect(self.browse_files)
        btn_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空列表")
        self.clear_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.clear_btn)
        
        left_layout.addLayout(btn_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(200)
        left_layout.addWidget(self.file_list)
        
        # 文件数量标签
        self.file_count_label = QLabel("已添加 0 个文件")
        self.file_count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(self.file_count_label)
        
        content_layout.addWidget(left_widget, 1)
        
        # 右侧 - 设置和预览
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # 输出格式选择
        format_group = QGroupBox("输出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.formats)
        format_layout.addWidget(self.format_combo)
        
        right_layout.addWidget(format_group)
        
        # 输出目录
        output_group = QGroupBox("输出目录")
        output_layout = QVBoxLayout(output_group)
        
        self.output_dir_label = QLabel("与源文件相同目录")
        self.output_dir_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        output_layout.addWidget(self.output_dir_label)
        
        self.output_dir_btn = QPushButton("📁 选择输出目录")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_btn)
        
        right_layout.addWidget(output_group)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = ImagePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        
        right_layout.addWidget(preview_group)
        
        # 转换按钮
        self.convert_btn = QPushButton("🚀 开始转换")
        self.convert_btn.setStyleSheet(StyleSheet.GRADIENT_BUTTON)
        self.convert_btn.clicked.connect(self.start_convert)
        right_layout.addWidget(self.convert_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        right_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(right_widget, 1)
        
        layout.addLayout(content_layout)
        
        # 日志区域
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # 默认输出目录
        self.output_dir = ""
        
        # 转换线程
        self.converter_thread = None
        
    def browse_files(self):
        """浏览并添加文件"""
        file_filter = f"所有文件 (*.*);;{self.title}文件 ({' '.join(['*.' + f.lower() for f in self.formats])})"
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", file_filter)
        if files:
            self.add_files(files)
    
    def add_files(self, files: List[str]):
        """添加文件到列表"""
        for file_path in files:
            if file_path not in self.files:
                self.files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setToolTip(file_path)
                self.file_list.addItem(item)
        
        self.update_file_count()
        
        # 如果是图片，显示预览
        if self.files and HAS_PIL:
            self.preview_widget.load_image(self.files[-1])
    
    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.file_list.clear()
        self.update_file_count()
        self.preview_widget.clear_preview()
    
    def update_file_count(self):
        """更新文件数量显示"""
        count = len(self.files)
        self.file_count_label.setText(f"已添加 {count} 个文件")
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(dir_path)
    
    def start_convert(self):
        """开始转换"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先添加要转换的文件！")
            return
        
        # 确定输出目录
        output_dir = self.output_dir if self.output_dir else os.path.dirname(self.files[0])
        
        # 获取输出格式
        output_format = self.format_combo.currentText().lower()
        
        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 创建并启动转换线程
        self.converter_thread = ConverterThread(
            self.files.copy(),
            output_format,
            output_dir
        )
        self.converter_thread.progress.connect(self.update_progress)
        self.converter_thread.finished.connect(self.on_convert_finished)
        self.converter_thread.log.connect(self.add_log)
        self.converter_thread.start()
    
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def on_convert_finished(self, success: bool, message: str):
        """转换完成回调"""
        self.convert_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        if success:
            self.add_log(f"✅ {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.add_log(f"❌ {message}")
            QMessageBox.warning(self, "完成", message)


class ImageConvertPage(ConvertPage):
    """图片转换页面"""
    
    def __init__(self, parent=None):
        super().__init__("🖼️ 图片转换", IMAGE_FORMATS, parent)
        
        # 添加图片质量选项
        quality_group = QGroupBox("图片质量")
        quality_layout = QVBoxLayout(quality_group)
        
        quality_label = QLabel("质量 (1-100):")
        quality_layout.addWidget(quality_label)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        quality_layout.addWidget(self.quality_spin)
        
        # 插入到右侧设置区域
        self.layout().itemAt(1).layout().itemAt(1).widget().layout().insertWidget(2, quality_group)


class AudioConvertPage(ConvertPage):
    """音频转换页面"""
    
    def __init__(self, parent=None):
        super().__init__("🎵 音频转换", AUDIO_FORMATS, parent)
        
        # 添加音频比特率选项
        bitrate_group = QGroupBox("音频质量")
        bitrate_layout = QVBoxLayout(bitrate_group)
        
        bitrate_label = QLabel("比特率:")
        bitrate_layout.addWidget(bitrate_label)
        
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['128k', '192k', '256k', '320k'])
        self.bitrate_combo.setCurrentText('320k')
        bitrate_layout.addWidget(self.bitrate_combo)
        
        # 插入到右侧设置区域
        self.layout().itemAt(1).layout().itemAt(1).widget().layout().insertWidget(2, bitrate_group)


class VideoConvertPage(ConvertPage):
    """视频转换页面"""
    
    def __init__(self, parent=None):
        super().__init__("🎬 视频转换", VIDEO_FORMATS, parent)
        
        # 添加视频比特率选项
        bitrate_group = QGroupBox("视频质量")
        bitrate_layout = QVBoxLayout(bitrate_group)
        
        bitrate_label = QLabel("比特率:")
        bitrate_layout.addWidget(bitrate_label)
        
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['2000k', '4000k', '8000k', '12000k', '16000k'])
        self.bitrate_combo.setCurrentText('8000k')
        bitrate_layout.addWidget(self.bitrate_combo)
        
        # 插入到右侧设置区域
        self.layout().itemAt(1).layout().itemAt(1).widget().layout().insertWidget(2, bitrate_group)


class DocumentConvertPage(ConvertPage):
    """文档转换页面"""
    
    def __init__(self, parent=None):
        super().__init__("📄 文档转换", ['PDF', 'DOCX', 'TXT'], parent)


class ArchiveConvertPage(ConvertPage):
    """压缩包转换页面"""
    
    def __init__(self, parent=None):
        super().__init__("📦 压缩包转换", ARCHIVE_FORMATS, parent)


class BatchConvertPage(QWidget):
    """批量转换页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("🚀 批量转换")
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text']};
            padding: 10px 0;
        """)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        # 主要内容
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 左侧 - 文件列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        # 拖拽区域
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        left_layout.addWidget(self.drop_area)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加文件")
        self.add_btn.clicked.connect(self.browse_files)
        btn_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空列表")
        self.clear_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.clear_btn)
        
        left_layout.addLayout(btn_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(300)
        left_layout.addWidget(self.file_list)
        
        # 文件数量
        self.file_count_label = QLabel("已添加 0 个文件")
        self.file_count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(self.file_count_label)
        
        content_layout.addWidget(left_widget, 1)
        
        # 右侧 - 设置
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # 转换类型选择
        type_group = QGroupBox("转换类型")
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['图片', '音频', '视频', '文档', '压缩包'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        
        right_layout.addWidget(type_group)
        
        # 输出格式选择
        format_group = QGroupBox("输出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.update_format_options('图片')
        format_layout.addWidget(self.format_combo)
        
        right_layout.addWidget(format_group)
        
        # 输出目录
        output_group = QGroupBox("输出目录")
        output_layout = QVBoxLayout(output_group)
        
        self.output_dir_label = QLabel("与源文件相同目录")
        self.output_dir_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        output_layout.addWidget(self.output_dir_label)
        
        self.output_dir_btn = QPushButton("📁 选择输出目录")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_btn)
        
        right_layout.addWidget(output_group)
        
        # 转换按钮
        self.convert_btn = QPushButton("🚀 开始批量转换")
        self.convert_btn.setStyleSheet(StyleSheet.GRADIENT_BUTTON)
        self.convert_btn.clicked.connect(self.start_convert)
        right_layout.addWidget(self.convert_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        right_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(right_widget, 1)
        
        layout.addLayout(content_layout)
        
        # 日志区域
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # 默认输出目录
        self.output_dir = ""
        
        # 转换线程
        self.converter_thread = None
    
    def on_type_changed(self, type_name: str):
        """转换类型改变"""
        self.update_format_options(type_name)
    
    def update_format_options(self, type_name: str):
        """更新格式选项"""
        self.format_combo.clear()
        
        if type_name == '图片':
            self.format_combo.addItems(IMAGE_FORMATS)
        elif type_name == '音频':
            self.format_combo.addItems(AUDIO_FORMATS)
        elif type_name == '视频':
            self.format_combo.addItems(VIDEO_FORMATS)
        elif type_name == '文档':
            self.format_combo.addItems(['PDF', 'DOCX', 'TXT'])
        elif type_name == '压缩包':
            self.format_combo.addItems(ARCHIVE_FORMATS)
    
    def browse_files(self):
        """浏览并添加文件"""
        file_filter = "所有文件 (*.*);;图片文件 (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.ico);;音频文件 (*.mp3 *.wav *.flac *.ogv);;视频文件 (*.mp4 *.avi *.mkv *.mov);;文档文件 (*.pdf *.docx *.txt);;压缩包 (*.zip *.7z *.tar *.gz *.bz2 *.xz)"
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", file_filter)
        if files:
            self.add_files(files)
    
    def add_files(self, files: List[str]):
        """添加文件到列表"""
        for file_path in files:
            if file_path not in self.files:
                self.files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setToolTip(file_path)
                self.file_list.addItem(item)
        
        self.update_file_count()
    
    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.file_list.clear()
        self.update_file_count()
    
    def update_file_count(self):
        """更新文件数量显示"""
        count = len(self.files)
        self.file_count_label.setText(f"已添加 {count} 个文件")
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(dir_path)
    
    def start_convert(self):
        """开始批量转换"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先添加要转换的文件！")
            return
        
        # 确定输出目录
        output_dir = self.output_dir if self.output_dir else os.path.dirname(self.files[0])
        
        # 获取输出格式
        output_format = self.format_combo.currentText().lower()
        
        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 创建并启动转换线程
        self.converter_thread = ConverterThread(
            self.files.copy(),
            output_format,
            output_dir
        )
        self.converter_thread.progress.connect(self.update_progress)
        self.converter_thread.finished.connect(self.on_convert_finished)
        self.converter_thread.log.connect(self.add_log)
        self.converter_thread.start()
    
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def on_convert_finished(self, success: bool, message: str):
        """转换完成回调"""
        self.convert_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        if success:
            self.add_log(f"✅ {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.add_log(f"❌ {message}")
            QMessageBox.warning(self, "完成", message)


class NavButton(QPushButton):
    """导航按钮"""
    
    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setText(f"{icon} {text}" if icon else text)
        self.setCheckable(True)
        self.setStyleSheet(StyleSheet.NAV_BUTTON)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置样式
        self.setStyleSheet(StyleSheet.MAIN)
        
        # 设置UI
        self.setup_ui()
        
        # 设置状态栏
        self.setup_statusbar()
        
        # 设置菜单栏
        self.setup_menubar()
        
    def setup_ui(self):
        """设置UI"""
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['card']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)
        
        # Logo
        logo_label = QLabel("📁 FileConverter")
        logo_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['accent_start']};
            padding: 15px;
        """)
        nav_layout.addWidget(logo_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        nav_layout.addWidget(line)
        
        nav_layout.addSpacing(20)
        
        # 导航按钮
        self.nav_buttons = []
        
        pages = [
            ("图片转换", "🖼️"),
            ("音频转换", "🎵"),
            ("视频转换", "🎬"),
            ("文档转换", "📄"),
            ("压缩包转换", "📦"),
            ("批量转换", "🚀"),
        ]
        
        for text, icon in pages:
            btn = NavButton(text, icon)
            btn.clicked.connect(lambda checked, t=text: self.switch_page(t))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        nav_layout.addStretch()
        
        # 版本信息
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding: 10px;
        """)
        nav_layout.addWidget(version_label)
        
        main_layout.addWidget(nav_widget)
        
        # 右侧内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 页面堆栈
        self.page_stack = QStackedWidget()
        
        # 添加页面
        self.image_page = ImageConvertPage()
        self.audio_page = AudioConvertPage()
        self.video_page = VideoConvertPage()
        self.document_page = DocumentConvertPage()
        self.archive_page = ArchiveConvertPage()
        self.batch_page = BatchConvertPage()
        
        self.page_stack.addWidget(self.image_page)
        self.page_stack.addWidget(self.audio_page)
        self.page_stack.addWidget(self.video_page)
        self.page_stack.addWidget(self.document_page)
        self.page_stack.addWidget(self.archive_page)
        self.page_stack.addWidget(self.batch_page)
        
        content_layout.addWidget(self.page_stack)
        
        main_layout.addWidget(content_widget)
        
        # 默认选中第一个导航按钮
        self.nav_buttons[0].setChecked(True)
        self.switch_page("图片转换")
    
    def setup_statusbar(self):
        """设置状态栏"""
        self.statusBar().showMessage("就绪")
        
        # 添加依赖状态
        deps = []
        if HAS_PIL:
            deps.append("✅ Pillow")
        else:
            deps.append("❌ Pillow")
        
        if HAS_PYDUB:
            deps.append("✅ pydub")
        else:
            deps.append("❌ pydub")
        
        if HAS_MOVIEPY:
            deps.append("✅ moviepy")
        else:
            deps.append("❌ moviepy")
        
        if HAS_DOCX:
            deps.append("✅ python-docx")
        else:
            deps.append("❌ python-docx")
        
        if HAS_PDF:
            deps.append("✅ pypdf/reportlab")
        else:
            deps.append("❌ pypdf/reportlab")
        
        dep_label = QLabel(" | ".join(deps))
        dep_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding-right: 10px;")
        self.statusBar().addPermanentWidget(dep_label)
    
    def setup_menubar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开文件", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        deps_action = QAction("依赖状态", self)
        deps_action.triggered.connect(self.show_dependencies)
        help_menu.addAction(deps_action)
    
    def switch_page(self, page_name: str):
        """切换页面"""
        page_map = {
            "图片转换": 0,
            "音频转换": 1,
            "视频转换": 2,
            "文档转换": 3,
            "压缩包转换": 4,
            "批量转换": 5,
        }
        
        index = page_map.get(page_name, 0)
        self.page_stack.setCurrentIndex(index)
        
        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        # 更新状态栏
        self.statusBar().showMessage(f"当前页面: {page_name}")
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            # 根据文件类型切换到对应页面
            ext = Path(file_path).suffix.lower().lstrip('.')
            
            if ext in [f.lower() for f in IMAGE_FORMATS]:
                self.switch_page("图片转换")
                self.image_page.add_files([file_path])
            elif ext in [f.lower() for f in AUDIO_FORMATS]:
                self.switch_page("音频转换")
                self.audio_page.add_files([file_path])
            elif ext in [f.lower() for f in VIDEO_FORMATS]:
                self.switch_page("视频转换")
                self.video_page.add_files([file_path])
            elif ext in ['txt', 'docx', 'pdf']:
                self.switch_page("文档转换")
                self.document_page.add_files([file_path])
            elif ext in [f.lower() for f in ARCHIVE_FORMATS]:
                self.switch_page("压缩包转换")
                self.archive_page.add_files([file_path])
            else:
                QMessageBox.information(self, "提示", f"已添加文件: {os.path.basename(file_path)}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 FileConverter",
            f"""
            <h2>{APP_TITLE}</h2>
            <p>版本: {APP_VERSION}</p>
            <p>一款功能强大的通用文件格式转换器</p>
            <p>支持图片、音频、视频、文档、压缩包等多种格式转换</p>
            <br>
            <p>功能特性:</p>
            <ul>
                <li>多格式支持</li>
                <li>批量转换</li>
                <li>拖拽操作</li>
                <li>实时预览</li>
                <li>现代化深色主题</li>
            </ul>
            """
        )
    
    def show_dependencies(self):
        """显示依赖状态"""
        deps_info = "依赖状态:\n\n"
        
        deps = [
            ("PyQt6", "GUI框架", True),
            ("Pillow", "图片处理", HAS_PIL),
            ("pydub", "音频处理", HAS_PYDUB),
            ("moviepy", "视频处理", HAS_MOVIEPY),
            ("python-docx", "Word文档处理", HAS_DOCX),
            ("pypdf", "PDF处理", HAS_PDF),
            ("reportlab", "PDF生成", HAS_PDF),
            ("py7zr", "7Z压缩包处理", HAS_7Z),
            ("rarfile", "RAR压缩包处理", HAS_RAR),
        ]
        
        for name, desc, available in deps:
            status = "✅ 已安装" if available else "❌ 未安装"
            deps_info += f"{name}: {status} - {desc}\n"
        
        QMessageBox.information(self, "依赖状态", deps_info)


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("FileConverter")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
