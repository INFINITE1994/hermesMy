"""
工作流构建器模块 - 可视化工作流设计
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QComboBox, QMessageBox,
    QScrollArea, QFrame, QTextEdit, QFileDialog, QSplitter,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QFont, QDrag, QPixmap

from app.styles import (
    get_card_style, get_accent_button_style, get_danger_button_style,
    get_success_button_style, get_secondary_button_style,
    ACCENT_START, ACCENT_END, TEXT_SECONDARY, CARD_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR
)


class WorkflowNode:
    """工作流节点"""
    
    def __init__(self, node_type, name, x=0, y=0):
        self.node_type = node_type
        self.name = name
        self.x = x
        self.y = y
        self.width = 160
        self.height = 80
        self.id = id(self)
        self.config = {}
        self.input_connections = []
        self.output_connections = []
    
    def get_rect(self):
        return QRect(self.x, self.y, self.width, self.height)
    
    def contains(self, point):
        return self.get_rect().contains(point)


class WorkflowCanvas(QWidget):
    """工作流画布"""
    
    node_selected = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.connections = []
        self.selected_node = None
        self.dragging = False
        self.drag_offset = QPoint(0, 0)
        self.connecting = False
        self.connect_from = None
        self.connect_to = None
        
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        # 添加演示节点
        self._add_demo_nodes()
    
    def _add_demo_nodes(self):
        """添加演示节点"""
        nodes = [
            WorkflowNode("开始", "开始", 50, 200),
            WorkflowNode("条件判断", "检查文件", 270, 200),
            WorkflowNode("文件操作", "读取文件", 490, 100),
            WorkflowNode("延时等待", "等待5秒", 490, 300),
            WorkflowNode("结束", "完成", 710, 200),
        ]
        
        self.nodes = nodes
        
        # 添加连接
        self.connections = [
            (nodes[0], nodes[1]),
            (nodes[1], nodes[2]),
            (nodes[1], nodes[3]),
            (nodes[2], nodes[4]),
            (nodes[3], nodes[4]),
        ]
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景网格
        self._draw_grid(painter)
        
        # 绘制连接线
        for from_node, to_node in self.connections:
            self._draw_connection(painter, from_node, to_node)
        
        # 绘制节点
        for node in self.nodes:
            self._draw_node(painter, node)
        
        painter.end()
    
    def _draw_grid(self, painter):
        """绘制网格"""
        painter.setPen(QPen(QColor("#1a1a2a"), 1))
        
        width = self.width()
        height = self.height()
        
        for x in range(0, width, 30):
            painter.drawLine(x, 0, x, height)
        
        for y in range(0, height, 30):
            painter.drawLine(0, y, width, y)
    
    def _draw_node(self, painter, node):
        """绘制节点"""
        rect = node.get_rect()
        
        # 节点颜色
        colors = {
            "开始": (QColor("#22c55e"), QColor("#166534")),
            "结束": (QColor("#ef4444"), QColor("#991b1b")),
            "条件判断": (QColor("#f59e0b"), QColor("#92400e")),
            "文件操作": (QColor("#3b82f6"), QColor("#1e3a5f")),
            "延时等待": (QColor("#8b5cf6"), QColor("#4c1d95")),
            "执行命令": (QColor("#06b6d4"), QColor("#164e63")),
            "发送通知": (QColor("#ec4899"), QColor("#831843")),
        }
        
        main_color, dark_color = colors.get(node.node_type, (QColor(ACCENT_START), QColor("#1a1a3a")))
        
        # 选中状态
        if node == self.selected_node:
            painter.setPen(QPen(QColor(ACCENT_START), 3))
            painter.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 12, 12)
        
        # 绘制节点背景
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, dark_color)
        gradient.setColorAt(1, QColor(dark_color.red() + 20, dark_color.green() + 20, dark_color.blue() + 20))
        
        painter.setPen(QPen(main_color, 2))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 10, 10)
        
        # 绘制节点类型标识
        type_rect = QRect(rect.x() + 8, rect.y() + 8, rect.width() - 16, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(main_color))
        painter.drawRoundedRect(type_rect, 4, 4)
        
        painter.setPen(QPen(QColor("white")))
        font = QFont("Microsoft YaHei", 8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(type_rect, Qt.AlignmentFlag.AlignCenter, node.node_type)
        
        # 绘制节点名称
        name_rect = QRect(rect.x() + 8, rect.y() + 35, rect.width() - 16, 30)
        painter.setPen(QPen(QColor("#e0e0e0")))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, node.name)
        
        # 绘制连接点
        self._draw_ports(painter, node, main_color)
    
    def _draw_ports(self, painter, node, color):
        """绘制连接点"""
        # 输入端口（左侧）
        input_port = QPoint(node.x, node.y + node.height // 2)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(QColor("#111122")))
        painter.drawEllipse(input_port, 6, 6)
        
        # 输出端口（右侧）
        output_port = QPoint(node.x + node.width, node.y + node.height // 2)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(QColor("#111122")))
        painter.drawEllipse(output_port, 6, 6)
    
    def _draw_connection(self, painter, from_node, to_node):
        """绘制连接线"""
        start = QPoint(from_node.x + from_node.width, from_node.y + from_node.height // 2)
        end = QPoint(to_node.x, to_node.y + to_node.height // 2)
        
        # 计算控制点
        mid_x = (start.x() + end.x()) // 2
        
        painter.setPen(QPen(QColor(ACCENT_START), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 绘制贝塞尔曲线
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(start)
        path.cubicTo(QPoint(mid_x, start.y()), QPoint(mid_x, end.y()), end)
        painter.drawPath(path)
        
        # 绘制箭头
        arrow_size = 8
        angle = 0  # 简化箭头方向
        
        arrow_p1 = QPoint(end.x() - arrow_size, end.y() - arrow_size // 2)
        arrow_p2 = QPoint(end.x() - arrow_size, end.y() + arrow_size // 2)
        
        painter.setBrush(QBrush(QColor(ACCENT_START)))
        from PyQt6.QtGui import QPolygon
        arrow = QPolygon([end, arrow_p1, arrow_p2])
        painter.drawPolygon(arrow)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # 检查是否点击了节点
            for node in reversed(self.nodes):
                if node.contains(pos):
                    self.selected_node = node
                    self.dragging = True
                    self.drag_offset = QPoint(pos.x() - node.x, pos.y() - node.y)
                    self.node_selected.emit(node)
                    self.update()
                    return
            
            self.selected_node = None
            self.node_selected.emit(None)
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and self.selected_node:
            pos = event.pos()
            self.selected_node.x = pos.x() - self.drag_offset.x()
            self.selected_node.y = pos.y() - self.drag_offset.y()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.dragging = False
    
    def add_node(self, node_type, name, x=100, y=100):
        """添加节点"""
        node = WorkflowNode(node_type, name, x, y)
        self.nodes.append(node)
        self.update()
        return node
    
    def delete_selected(self):
        """删除选中的节点"""
        if self.selected_node:
            # 删除相关连接
            self.connections = [
                (f, t) for f, t in self.connections
                if f != self.selected_node and t != self.selected_node
            ]
            self.nodes.remove(self.selected_node)
            self.selected_node = None
            self.update()
    
    def connect_selected(self):
        """连接选中的节点"""
        if len(self.nodes) >= 2:
            # 连接最后两个节点
            self.connections.append((self.nodes[-2], self.nodes[-1]))
            self.update()


class WorkflowBuilderWidget(QWidget):
    """工作流构建器界面"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("🔧 工作流构建器")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_START};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述
        desc = QLabel("可视化拖拽式工作流设计，支持多种节点类型，快速构建自动化流程")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(desc)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 工作流操作
        new_btn = QPushButton("📄 新建工作流")
        new_btn.setStyleSheet(get_secondary_button_style())
        new_btn.clicked.connect(self.new_workflow)
        toolbar.addWidget(new_btn)
        
        open_btn = QPushButton("📂 打开工作流")
        open_btn.setStyleSheet(get_secondary_button_style())
        open_btn.clicked.connect(self.open_workflow)
        toolbar.addWidget(open_btn)
        
        save_btn = QPushButton("💾 保存工作流")
        save_btn.setStyleSheet(get_secondary_button_style())
        save_btn.clicked.connect(self.save_workflow)
        toolbar.addWidget(save_btn)
        
        toolbar.addSpacing(20)
        
        # 编辑操作
        delete_btn = QPushButton("🗑️ 删除节点")
        delete_btn.setStyleSheet(get_danger_button_style())
        delete_btn.clicked.connect(self.delete_node)
        toolbar.addWidget(delete_btn)
        
        connect_btn = QPushButton("🔗 连接节点")
        connect_btn.setStyleSheet(get_secondary_button_style())
        connect_btn.clicked.connect(self.connect_nodes)
        toolbar.addWidget(connect_btn)
        
        toolbar.addStretch()
        
        # 执行
        run_btn = QPushButton("▶ 执行工作流")
        run_btn.setStyleSheet(get_success_button_style())
        run_btn.clicked.connect(self.run_workflow)
        toolbar.addWidget(run_btn)
        
        layout.addLayout(toolbar)
        
        # 主内容区
        content_layout = QHBoxLayout()
        
        # 左侧：节点面板
        left_panel = QGroupBox("节点库")
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(200)
        
        # 节点分类
        categories = [
            ("控制流", [
                ("开始", "🟢"),
                ("结束", "🔴"),
                ("条件判断", "❓"),
                ("循环", "🔄"),
            ]),
            ("文件操作", [
                ("文件操作", "📁"),
                ("文件监控", "👁️"),
                ("批量处理", "📦"),
            ]),
            ("系统操作", [
                ("执行命令", "💻"),
                ("延时等待", "⏱️"),
                ("发送通知", "🔔"),
            ]),
            ("数据处理", [
                ("数据转换", "🔀"),
                ("文本处理", "📝"),
                ("数据验证", "✅"),
            ]),
        ]
        
        for category_name, nodes in categories:
            cat_label = QLabel(category_name)
            cat_label.setStyleSheet(f"""
                color: {ACCENT_START};
                font-weight: bold;
                font-size: 12px;
                padding: 8px 0 4px 0;
            """)
            left_layout.addWidget(cat_label)
            
            for node_name, icon in nodes:
                btn = QPushButton(f"{icon} {node_name}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {CARD_COLOR};
                        border: 1px solid #1a1a3a;
                        border-radius: 6px;
                        padding: 8px;
                        text-align: left;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        background-color: #1a1a3a;
                        border-color: {ACCENT_START};
                    }}
                """)
                btn.clicked.connect(lambda checked, n=node_name: self.add_node(n))
                left_layout.addWidget(btn)
        
        left_layout.addStretch()
        
        content_layout.addWidget(left_panel)
        
        # 中间：画布
        canvas_group = QGroupBox("工作流画布")
        canvas_layout = QVBoxLayout(canvas_group)
        
        # 画布滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: #0a0a1a;
                border: 1px solid #1a1a3a;
                border-radius: 8px;
            }}
        """)
        
        self.canvas = WorkflowCanvas()
        self.canvas.node_selected.connect(self.on_node_selected)
        scroll_area.setWidget(self.canvas)
        
        canvas_layout.addWidget(scroll_area)
        
        # 画布提示
        hint = QLabel("💡 提示: 从左侧节点库拖拽节点到画布，点击节点可选中，使用工具栏连接节点")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        canvas_layout.addWidget(hint)
        
        content_layout.addWidget(canvas_group, 1)
        
        # 右侧：属性面板
        right_panel = QGroupBox("节点属性")
        right_layout = QVBoxLayout(right_panel)
        right_panel.setFixedWidth(250)
        
        # 节点信息
        self.node_type_label = QLabel("类型: -")
        self.node_type_label.setStyleSheet(f"color: {ACCENT_START}; font-weight: bold;")
        right_layout.addWidget(self.node_type_label)
        
        self.node_name_edit = QLineEdit()
        self.node_name_edit.setPlaceholderText("节点名称")
        self.node_name_edit.textChanged.connect(self.update_node_name)
        right_layout.addWidget(self.node_name_edit)
        
        # 节点配置
        config_label = QLabel("配置:")
        config_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        right_layout.addWidget(config_label)
        
        self.config_edit = QTextEdit()
        self.config_edit.setPlaceholderText("节点配置参数...")
        self.config_edit.setMaximumHeight(150)
        right_layout.addWidget(self.config_edit)
        
        # 分隔线
        separator = QLabel("─" * 30)
        separator.setStyleSheet(f"color: #1a1a3a;")
        right_layout.addWidget(separator)
        
        # 工作流信息
        info_label = QLabel("📊 工作流信息")
        info_label.setStyleSheet(f"color: {ACCENT_START}; font-weight: bold;")
        right_layout.addWidget(info_label)
        
        self.node_count_label = QLabel("节点数: 0")
        self.node_count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        right_layout.addWidget(self.node_count_label)
        
        self.conn_count_label = QLabel("连接数: 0")
        self.conn_count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        right_layout.addWidget(self.conn_count_label)
        
        right_layout.addStretch()
        
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout, 1)
        
        # 更新统计
        self._update_stats()
    
    def add_node(self, node_type):
        """添加节点"""
        x = 100 + len(self.canvas.nodes) * 50
        y = 100 + (len(self.canvas.nodes) % 3) * 120
        self.canvas.add_node(node_type, node_type, x, y)
        self._update_stats()
    
    def delete_node(self):
        """删除节点"""
        self.canvas.delete_selected()
        self._update_stats()
    
    def connect_nodes(self):
        """连接节点"""
        self.canvas.connect_selected()
        self._update_stats()
    
    def on_node_selected(self, node):
        """节点选中事件"""
        if node:
            self.node_type_label.setText(f"类型: {node.node_type}")
            self.node_name_edit.setText(node.name)
            self.config_edit.setText(str(node.config))
        else:
            self.node_type_label.setText("类型: -")
            self.node_name_edit.clear()
            self.config_edit.clear()
    
    def update_node_name(self, text):
        """更新节点名称"""
        if self.canvas.selected_node and text:
            self.canvas.selected_node.name = text
            self.canvas.update()
    
    def _update_stats(self):
        """更新统计"""
        self.node_count_label.setText(f"节点数: {len(self.canvas.nodes)}")
        self.conn_count_label.setText(f"连接数: {len(self.canvas.connections)}")
    
    def new_workflow(self):
        """新建工作流"""
        reply = QMessageBox.question(
            self, "确认", "确定要新建工作流吗？当前工作流将被清除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            self.canvas.selected_node = None
            self.canvas.update()
            self._update_stats()
    
    def open_workflow(self):
        """打开工作流"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开工作流", "", "工作流文件 (*.workflow);;所有文件 (*)"
        )
        if file_path:
            QMessageBox.information(self, "打开", f"工作流已加载: {file_path}")
    
    def save_workflow(self):
        """保存工作流"""
        if not self.canvas.nodes:
            QMessageBox.warning(self, "警告", "没有可保存的工作流！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存工作流", "", "工作流文件 (*.workflow)"
        )
        if file_path:
            QMessageBox.information(self, "保存", f"工作流已保存到: {file_path}")
    
    def run_workflow(self):
        """执行工作流"""
        if not self.canvas.nodes:
            QMessageBox.warning(self, "警告", "没有可执行的工作流！")
            return
        
        QMessageBox.information(
            self, "执行工作流",
            f"开始执行工作流\n节点数: {len(self.canvas.nodes)}\n连接数: {len(self.canvas.connections)}"
        )
