# ScreenRecorder - 专业级屏幕录制工具

<div align="center">

🎬 **功能强大、简单易用的屏幕录制软件**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ 功能特性

### 🎥 录制模式
- **全屏录制** - 录制整个屏幕内容
- **区域录制** - 自由选择录制区域
- **窗口录制** - 录制指定窗口

### 🎤 音频录制
- 系统音频录制
- 麦克风录音
- 音频质量可调（64kbps ~ 无损）

### 📹 摄像头叠加
- 实时摄像头画面叠加
- 可拖拽调整位置
- 支持圆形/矩形显示
- 多种尺寸选择

### ✏️ 屏幕标注
- 画笔工具（自由绘制）
- 直线、矩形、椭圆、箭头
- 橡皮擦
- 多颜色、多粗细选择
- 支持撤销操作

### 🎬 导出格式
- **MP4** - 通用视频格式，压缩率高
- **AVI** - 无损/高质量视频
- **GIF** - 动图格式，适合分享

### ⌨️ 快捷键
| 快捷键 | 功能 |
|--------|------|
| `F9` | 开始/停止录制 |
| `F10` | 暂停/继续录制 |
| `Ctrl+Shift+S` | 截图 |
| `Ctrl+Shift+R` | 选择区域 |
| `ESC` | 退出标注模式 |

### 🎨 界面特色
- 深色主题，护眼舒适
- 渐变色设计，现代美观
- 中文界面，简单易用
- 系统托盘支持

## 📦 安装

### 系统要求
- Windows 10/11
- Python 3.10 或更高版本
- 摄像头（可选，用于摄像头叠加功能）

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone <repository-url>
   cd ScreenRecorder
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -e .
   ```
   
   或者使用 pip 直接安装依赖：
   ```bash
   pip install PyQt6 Pillow imageio imageio-ffmpeg numpy mss pynput opencv-python
   ```

4. **运行程序**
   ```bash
   python main.py
   ```

## 🚀 使用指南

### 基本录制流程

1. **选择录制模式**
   - 全屏录制：录制整个屏幕
   - 区域录制：点击"选择录制区域"按钮，拖拽选择
   - 窗口录制：选择要录制的窗口

2. **配置录制参数**
   - 帧率：15/24/30/60 FPS
   - 质量：1-100% 可调
   - 格式：MP4/AVI/GIF
   - 音频：开启/关闭，选择音源

3. **开始录制**
   - 点击"开始录制"按钮
   - 或按 `F9` 快捷键

4. **暂停/继续**
   - 点击"暂停"按钮
   - 或按 `F10` 快捷键

5. **停止录制**
   - 点击"停止"按钮
   - 或按 `F9` 快捷键
   - 文件自动保存到输出目录

### 截图功能

- 点击"截图"按钮
- 或按 `Ctrl+Shift+S`
- 截图保存为 PNG 格式

### 标注功能

1. 点击"标注"按钮开启标注模式
2. 选择工具（画笔、直线、矩形等）
3. 在屏幕上绘制标注
4. 按 `Ctrl+Z` 撤销
5. 按 `ESC` 退出标注模式

### 摄像头叠加

1. 点击"摄像头"按钮开启
2. 拖拽调整位置
3. 在设置中调整大小和形状

## 📁 项目结构

```
ScreenRecorder/
├── main.py                 # 主入口
├── pyproject.toml          # 项目配置
├── README.md               # 说明文档
└── src/
    └── screen_recorder/
        ├── __init__.py
        ├── main.py              # 应用程序入口
        ├── main_window.py       # 主窗口
        ├── recorder_engine.py   # 录制引擎
        ├── annotation_widget.py # 标注组件
        ├── webcam_widget.py     # 摄像头组件
        ├── region_selector.py   # 区域选择器
        └── hotkey_manager.py    # 快捷键管理
```

## ⚙️ 配置说明

### 输出目录
默认保存到：`~/Videos/ScreenRecorder/`

可在"输出设置"标签页中修改。

### 文件命名
默认使用自动命名：`ScreenRecord_20240101_120000.mp4`

可在"输出设置"中修改前缀。

## 🔧 常见问题

### Q: 摄像头无法打开？
A: 请检查：
- 摄像头是否连接
- 是否被其他程序占用
- 系统隐私设置是否允许访问摄像头

### Q: 录制的视频没有声音？
A: 请检查：
- "录制音频"选项是否开启
- 系统音频/麦克风是否选择正确
- 音频设备是否正常工作

### Q: 录制卡顿？
A: 建议：
- 降低帧率（如从60降到30）
- 降低视频质量
- 关闭不必要的程序
- 使用更高效的编码器

### Q: 如何提高录制质量？
A: 可以：
- 提高帧率（60 FPS）
- 提高质量设置（90-100%）
- 选择 H.264 编码器
- 使用更高的音频质量

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者

---

<div align="center">

**感谢使用 ScreenRecorder！** 🎬

</div>
