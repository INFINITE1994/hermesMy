"""
区域选择模块 - 选择屏幕录制区域
"""
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QCursor


class RegionSelector(QWidget):
    """区域选择器"""
    
    region_selected = pyqtSignal(QRect)  # 选中的区域
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择录制区域")
        
        # 全屏覆盖
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        # 选择状态
        self.selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selected_rect = QRect()
        
        # 提示标签
        self.hint_label = QLabel("拖拽鼠标选择录制区域，按ESC取消", self)
        self.hint_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        self.hint_label.adjustSize()
        self.hint_label.move(20, 20)
        
        self.show()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        
        # 半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if not self.selected_rect.isNull():
            # 清除选中区域的遮罩（透明）
            painter.setClipRect(self.selected_rect)
            painter.fillRect(self.selected_rect, QColor(0, 0, 0, 0))
            painter.setClipping(False)
            
            # 绘制选中区域边框
            pen = QPen(QColor("#667eea"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.selected_rect)
            
            # 绘制尺寸信息
            size_text = f"{self.selected_rect.width()} x {self.selected_rect.height()}"
            painter.setPen(QColor("white"))
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            
            # 计算尺寸标签位置
            text_rect = painter.boundingRect(0, 0, 200, 30, Qt.AlignmentFlag.AlignCenter, size_text)
            text_x = self.selected_rect.center().x() - text_rect.width() // 2
            text_y = self.selected_rect.bottom() + 25
            
            # 绘制背景
            bg_rect = text_rect.adjusted(-10, -5, 10, 5)
            bg_rect.moveTopLeft(QPoint(text_x - 10, text_y - 5))
            painter.fillRect(bg_rect, QColor(0, 0, 0, 180))
            
            painter.drawText(text_x, text_y + 15, size_text)
            
            # 绘制角点
            self._draw_corner_points(painter)
        
        painter.end()
    
    def _draw_corner_points(self, painter):
        """绘制角点"""
        rect = self.selected_rect
        points = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]
        
        painter.setPen(QPen(QColor("#667eea"), 2))
        painter.setBrush(QBrush(QColor("#667eea")))
        
        for point in points:
            painter.drawEllipse(point, 5, 5)
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selected_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.selecting:
            self.end_point = event.pos()
            self.selected_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            self.end_point = event.pos()
            self.selected_rect = QRect(self.start_point, self.end_point).normalized()
            
            # 检查选择区域是否有效
            if self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                self.region_selected.emit(self.selected_rect)
            else:
                self.region_selected.emit(QRect())
            
            self.close()
    
    def keyPressEvent(self, event):
        """键盘按下"""
        if event.key() == Qt.Key.Key_Escape:
            self.region_selected.emit(QRect())
            self.close()
