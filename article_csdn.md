# Python桌面工具开发实战：从0到1做一个系统清理工具

## 前言

很多Python初学者学完基础语法后，不知道做什么项目练手。今天分享一个完整的实战项目：用PyQt6做一个Windows系统清理工具。

这个项目涉及：
- PyQt6 GUI开发
- 文件系统操作
- 多线程编程
- 注册表操作
- 打包发布

## 最终效果

深色主题，现代UI，支持扫描10类垃圾文件，一键清理。

## 技术栈

- Python 3.10+
- PyQt6（GUI框架）
- psutil（系统信息）
- send2trash（安全删除）

## 核心代码

### 1. 扫描引擎

```python
import os
import tempfile
from dataclasses import dataclass

@dataclass
class ScanResult:
    category: str
    path: str
    size: int
    description: str
    safe_to_delete: bool = True

class Scanner:
    def __init__(self):
        self.user_profile = os.environ.get("USERPROFILE", "")
        self.local_app = os.environ.get("LOCALAPPDATA", "")
        self.temp_dir = tempfile.gettempdir()
    
    def scan_temp_files(self, report):
        """扫描临时文件"""
        self._scan_dir_contents(
            self.temp_dir, 
            "临时文件", 
            "系统临时文件", 
            report
        )
    
    def scan_browser_cache(self, report):
        """扫描浏览器缓存"""
        browsers = {
            "Chrome": os.path.join(self.local_app, "Google", "Chrome", 
                                   "User Data", "Default", "Cache"),
            "Edge": os.path.join(self.local_app, "Microsoft", "Edge", 
                                 "User Data", "Default", "Cache"),
        }
        for name, path in browsers.items():
            if os.path.exists(path):
                size = self._get_dir_size(path)
                if size > 0:
                    report.add(ScanResult(
                        category="浏览器缓存",
                        path=path,
                        size=size,
                        description=f"{name}浏览器缓存",
                    ))
```

### 2. PyQt6界面

```python
from PyQt6.QtWidgets import QMainWindow, QPushButton, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统清理工具")
        self.setMinimumSize(580, 700)
        
        # 扫描按钮
        self.scan_btn = QPushButton("🔍 开始扫描")
        self.scan_btn.clicked.connect(self.start_scan)
        
        # 结果显示
        self.result_label = QLabel("点击开始扫描")
```

### 3. 多线程扫描

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ScanWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.scanner = Scanner()
    
    def run(self):
        report = self.scanner.full_scan(
            callback=lambda p: self.progress.emit(p.category, p.total_size)
        )
        self.finished.emit(report)
```

### 4. 深色主题

```python
DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 14px 48px;
}
"""
```

## 打包发布

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name CleanMaster main.py
```

## 项目地址

完整代码：https://github.com/INFINITE1994/hermesMy/tree/master/CleanMaster

## 总结

这个项目适合Python中级开发者练手。涉及的技术点很多，但每个都不难。做完之后你会对PyQt6、文件系统操作、多线程有更深入的理解。

有问题欢迎在评论区讨论。
