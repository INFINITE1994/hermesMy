"""
摄像头叠加模块 - 在屏幕上显示摄像头画面
"""
import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPainterPath, QColor, QPen, QBrush


class WebcamOverlay(QWidget):
    """摄像头叠加窗口"""
    
    def __init__(self, camera_index=0, size=(240, 180), position="bottom_right"):
        super().__init__()
        self.setWindowTitle("摄像头")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 摄像头设置
        self.camera_index = camera_index
        self.target_size = size
        self.position = position
        self.rounded = True
        
        # 拖拽
        self.dragging = False
        self.drag_position = QPoint()
        
        # 摄像头
        self.cap = None
        self.camera_available = False
        
        # 图像显示
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 初始化摄像头
        self.init_camera()
        
        # 设置窗口大小
        self.setFixedSize(size[0] + 10, size[1] + 10)
        
        # 设置位置
        self.set_position(position)
        
        # 更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30fps
    
    def init_camera(self):
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                self.camera_available = True
                # 设置分辨率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            else:
                self.camera_available = False
                self.show_placeholder()
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            self.camera_available = False
            self.show_placeholder()
    
    def show_placeholder(self):
        """显示占位图"""
        pixmap = QPixmap(self.target_size[0], self.target_size[1])
        pixmap.fill(QColor("#1a1a2e"))
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("#667eea"), 2))
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📹 摄像头未连接")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
    
    def set_position(self, position):
        """设置窗口位置"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        
        geo = screen.availableGeometry()
        w, h = self.width(), self.height()
        margin = 20
        
        positions = {
            "top_left": (geo.x() + margin, geo.y() + margin),
            "top_right": (geo.x() + geo.width() - w - margin, geo.y() + margin),
            "bottom_left": (geo.x() + margin, geo.y() + geo.height() - h - margin),
            "bottom_right": (geo.x() + geo.width() - w - margin, geo.y() + geo.height() - h - margin),
        }
        
        x, y = positions.get(position, positions["bottom_right"])
        self.move(x, y)
    
    def update_frame(self):
        """更新摄像头帧"""
        if not self.camera_available or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # 转换颜色
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 调整大小
        h, w = rgb_frame.shape[:2]
        target_w, target_h = self.target_size
        
        # 保持宽高比缩放
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(rgb_frame, (new_w, new_h))
        
        # 创建带圆角的图像
        q_image = QImage(resized.data, new_w, new_h, 3 * new_w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # 创建圆角遮罩
        if self.rounded:
            rounded_pixmap = QPixmap(target_w, target_h)
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 创建圆形路径
            path = QPainterPath()
            center_x = target_w // 2
            center_y = target_h // 2
            radius = min(target_w, target_h) // 2 - 2
            path.addEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            painter.setClipPath(path)
            
            # 居中绘制
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            painter.drawPixmap(x_offset, y_offset, pixmap)
            
            # 绘制边框
            painter.setClipping(False)
            pen = QPen(QColor("#667eea"), 3)
            painter.setPen(pen)
            painter.drawPath(path)
            
            painter.end()
            
            self.image_label.setPixmap(rounded_pixmap)
        else:
            # 矩形显示
            final_pixmap = QPixmap(target_w, target_h)
            final_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制圆角矩形背景
            painter.setPen(QPen(QColor("#667eea"), 2))
            painter.setBrush(QBrush(QColor("#111122")))
            painter.drawRoundedRect(2, 2, target_w - 4, target_h - 4, 10, 10)
            
            # 居中绘制图像
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            painter.drawPixmap(x_offset, y_offset, pixmap)
            
            painter.end()
            
            self.image_label.setPixmap(final_pixmap)
    
    def set_rounded(self, rounded):
        """设置是否圆形显示"""
        self.rounded = rounded
    
    def set_size(self, size):
        """设置大小"""
        self.target_size = size
        self.setFixedSize(size[0] + 10, size[1] + 10)
    
    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 停止拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.cap:
            self.cap.release()
        self.timer.stop()
        event.accept()
    
    def hideEvent(self, event):
        """隐藏事件"""
        if self.cap:
            self.cap.release()
            self.camera_available = False
        self.timer.stop()
    
    def showEvent(self, event):
        """显示事件"""
        self.init_camera()
        self.timer.start(33)
