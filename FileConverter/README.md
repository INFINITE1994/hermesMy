# FileConverter - 通用文件格式转换器

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 简介

FileConverter 是一款功能强大的通用文件格式转换器，支持多种文件格式之间的转换。采用现代化的深色主题界面，支持拖拽操作和批量转换。

## ✨ 功能特性

### 🖼️ 图片转换
- 支持格式：PNG、JPG、WebP、BMP、TIFF、ICO
- 支持图片预览
- 支持质量调整

### 📄 文档转换
- DOCX 转 PDF
- PDF 转 DOCX
- TXT 转 PDF

### 🎵 音频转换
- 支持格式：MP3、WAV、FLAC、OGG
- 支持音频预览播放

### 🎬 视频转换
- 支持格式：MP4、AVI、MKV、MOV
- 支持视频预览

### 📦 压缩包转换
- 支持格式：ZIP、RAR、7Z、TAR

### 🚀 批量转换
- 支持同时转换多个文件
- 支持拖拽添加文件
- 实时转换进度显示

### 🎨 界面特性
- 现代化深色主题
- 渐变色强调效果
- 响应式布局
- 中文界面

## 🛠️ 安装

### 方式一：使用 pip 安装（推荐）

```bash
# 基础安装（仅图片转换）
pip install PyQt6 Pillow

# 完整安装（所有功能）
pip install PyQt6 Pillow pydub moviepy python-docx pypdf reportlab py7zr rarfile
```

### 方式二：从源码安装

```bash
git clone https://github.com/yourusername/fileconverter.git
cd fileconverter

# 基础安装
pip install -e .

# 完整安装
pip install -e ".[all]"
```

## 🚀 使用方法

### 启动应用

```bash
python main.py
```

### 基本操作

1. **选择转换类型**：在左侧导航栏选择要转换的文件类型
2. **添加文件**：
   - 点击"添加文件"按钮选择文件
   - 或直接拖拽文件到窗口
3. **选择输出格式**：在下拉菜单中选择目标格式
4. **开始转换**：点击"开始转换"按钮
5. **查看结果**：转换完成后可在输出目录查看文件

### 批量转换

1. 切换到"批量转换"标签页
2. 添加多个文件
3. 选择统一的输出格式
4. 点击"批量转换"

## 📁 项目结构

```
FileConverter/
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置
├── README.md           # 项目说明
└── requirements.txt    # 依赖列表
```

## 🔧 依赖说明

| 依赖包 | 用途 | 是否必需 |
|--------|------|----------|
| PyQt6 | GUI框架 | ✅ 是 |
| Pillow | 图片处理 | ✅ 是 |
| pydub | 音频处理 | ❌ 可选 |
| moviepy | 视频处理 | ❌ 可选 |
| python-docx | Word文档处理 | ❌ 可选 |
| pypdf | PDF处理 | ❌ 可选 |
| reportlab | PDF生成 | ❌ 可选 |
| py7zr | 7Z压缩包处理 | ❌ 可选 |
| rarfile | RAR压缩包处理 | ❌ 可选 |

## 🎨 界面预览

应用采用深色主题设计：
- 背景色：#0a0a0a
- 卡片色：#111122
- 强调色渐变：#667eea → #764ba2

## 📝 注意事项

1. 视频转换需要安装 FFmpeg
2. 音频转换需要安装 FFmpeg
3. RAR解压需要安装 unrar 工具
4. 某些格式转换可能需要额外的系统依赖

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [Pillow](https://python-pillow.org/)
- [FFmpeg](https://ffmpeg.org/)
