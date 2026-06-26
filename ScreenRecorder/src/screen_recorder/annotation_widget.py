"""
标注叠加模块 - 在屏幕上绘制标注
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QCursor, QPainterPath


class AnnotationOverlay(QWidget):
    """全屏标注叠加层"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("标注层")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # 设置全屏
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        
        # 绘图状态
        self.drawing = False
        self.last_point = QPoint()
        self.current_point = QPoint()
        
        # 绘图设置
        self.pen_color = QColor("#ff4444")
        self.pen_width = 3
        self.tool = "pen"  # pen, line, rect, ellipse, arrow, text, eraser
        
        # 绘图历史
        self.strokes = []  # [(points, color, width, tool), ...]
        self.current_stroke = []
        
        # 橡皮擦大小
        self.eraser_size = 20
    
    def set_color(self, color_name):
        """设置画笔颜色"""
        color_map = {
            "红色": "#ff4444",
            "蓝色": "#4444ff",
            "绿色": "#44ff44",
            "黄色": "#ffff44",
            "白色": "#ffffff"
        }
        self.pen_color = QColor(color_map.get(color_name, "#ff4444"))
    
    def set_width(self, width):
        """设置画笔粗细"""
        self.pen_width = width
    
    def set_tool(self, tool):
        """设置工具"""
        self.tool = tool
        if tool == "eraser":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "text":
            self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
    
    def clear_all(self):
        """清除所有标注"""
        self.strokes = []
        self.update()
    
    def undo(self):
        """撤销最后一个笔画"""
        if self.strokes:
            self.strokes.pop()
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        
        # 绘制所有笔画
        for stroke in self.strokes:
            self._draw_stroke(painter, stroke)
        
        # 绘制当前笔画
        if self.drawing and self.current_stroke:
            self._draw_stroke(painter, self.current_stroke)
        
        # 绘制工具提示
        self._draw_tool_hint(painter)
        
        painter.end()
    
    def _draw_stroke(self, painter, stroke):
        """绘制一个笔画"""
        if len(stroke) < 4:
            return
        
        points, color, width, tool = stroke[0], stroke[1], stroke[2], stroke[3]
        
        pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        if tool == "pen":
            # 自由绘制
            path = QPainterPath()
            if len(points) > 0:
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                painter.drawPath(path)
        
        elif tool == "line":
            # 直线
            if len(points) >= 2:
                painter.drawLine(points[0], points[-1])
        
        elif tool == "rect":
            # 矩形
            if len(points) >= 2:
                rect = QRect(points[0], points[-1])
                painter.drawRect(rect)
        
        elif tool == "ellipse":
            # 椭圆
            if len(points) >= 2:
                rect = QRect(points[0], points[-1])
                painter.drawEllipse(rect)
        
        elif tool == "arrow":
            # 箭头
            if len(points) >= 2:
                start = points[0]
                end = points[-1]
                painter.drawLine(start, end)
                
                # 箭头头部
                import math
                angle = math.atan2(end.y() - start.y(), end.x() - start.x())
                arrow_len = 15
                arrow_angle = math.pi / 6
                
                p1 = QPoint(
                    int(end.x() - arrow_len * math.cos(angle - arrow_angle)),
                    int(end.y() - arrow_len * math.sin(angle - arrow_angle))
                )
                p2 = QPoint(
                    int(end.x() - arrow_len * math.cos(angle + arrow_angle)),
                    int(end.y() - arrow_len * math.sin(angle + arrow_angle))
                )
                painter.drawLine(end, p1)
                painter.drawLine(end, p2)
        
        elif tool == "eraser":
            # 橡皮擦（用背景色绘制）
            eraser_pen = QPen(QColor(0, 0, 0, 1), self.eraser_size,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(eraser_pen)
            path = QPainterPath()
            if len(points) > 0:
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                painter.drawPath(path)
    
    def _draw_tool_hint(self, painter):
        """绘制工具提示"""
        painter.setPen(QPen(QColor("#667eea"), 1))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        hint = f"工具: {self.tool} | 按ESC退出标注"
        painter.drawText(10, 20, hint)
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.current_stroke = [[event.pos()], self.pen_color, self.pen_width, self.tool]
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.drawing:
            self.current_point = event.pos()
            self.current_stroke[0].append(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if len(self.current_stroke[0]) > 1:
                self.strokes.append(self.current_stroke)
            self.current_stroke = []
            self.update()
    
    def keyPressEvent(self, event):
        """键盘按下"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo()
        elif event.key() == Qt.Key.Key_Delete:
            self.clear_all()
