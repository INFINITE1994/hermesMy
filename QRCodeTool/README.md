# 🔲 QRCodeTool - 专业二维码生成与识别工具

一款功能强大、界面精美的二维码桌面工具，基于 PyQt6 构建。

## ✨ 功能特性

### 🎯 核心功能
- **生成二维码** - 支持文本、URL、WiFi配置、vCard名片
- **自定义样式** - 前景色/背景色、Logo嵌入、尺寸调整
- **批量生成** - 从 CSV/TXT 文件批量生成二维码
- **扫描识别** - 从图片文件识别二维码内容
- **历史记录** - 自动保存生成历史，方便回溯
- **多种导出** - 支持 PNG、JPG、SVG 格式导出

### 🎨 界面特色
- 暗黑主题设计（背景 #0a0a0a，卡片 #111122）
- 渐变色强调按钮（#667eea → #764ba2）
- 中文界面，操作直观
- 响应式布局，支持窗口缩放

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Windows 10/11

### 安装依赖
```bash
pip install PyQt6 qrcode[pil] Pillow opencv-python numpy
```

### 运行程序
```bash
python main.py
```

### 打包为可执行文件
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name QRCodeTool main.py
```

## 📁 项目结构
```
QRCodeTool/
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置
├── README.md            # 说明文档
├── ui/                  # UI 模块
│   ├── __init__.py
│   ├── main_window.py   # 主窗口
│   ├── generate_tab.py  # 生成标签页
│   ├── scan_tab.py      # 扫描标签页
│   ├── batch_tab.py     # 批量生成标签页
│   └── history_tab.py   # 历史记录标签页
├── core/                # 核心逻辑
│   ├── __init__.py
│   ├── qr_generator.py  # QR码生成器
│   ├── qr_scanner.py    # QR码扫描器
│   └── history_manager.py # 历史管理
└── resources/           # 资源文件
    └── styles/
        └── theme.qss    # 样式表
```

## 🛠️ 使用说明

### 生成二维码
1. 切换到「生成二维码」标签页
2. 选择类型（文本/URL/WiFi/vCard）
3. 输入内容
4. 自定义颜色和样式
5. 点击「生成二维码」
6. 使用「导出」按钮保存

### 批量生成
1. 准备 CSV 或 TXT 文件（每行一个内容）
2. 切换到「批量生成」标签页
3. 选择输入文件和输出目录
4. 点击「开始批量生成」

### 扫描识别
1. 切换到「扫描识别」标签页
2. 点击「选择图片」加载二维码图片
3. 自动识别并显示内容

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
