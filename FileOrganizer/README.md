# FileOrganizer - 暗黑风格文件整理工具

## 简介

FileOrganizer 是一款现代化的 Windows 桌面文件整理工具，采用暗黑主题设计，帮助您高效管理和组织电脑中的文件。

## 功能特性

### 1. 📁 按类型自动分类
自动将文件按类型整理到对应文件夹：
- 🖼️ 图片（jpg, png, gif, bmp, svg, webp, ico, tiff）
- 📄 文档（pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv）
- 🎬 视频（mp4, avi, mkv, mov, wmv, flv, webm）
- 🎵 音频（mp3, wav, flac, aac, ogg, wma, m4a）
- 📦 压缩包（zip, rar, 7z, tar, gz, bz2）
- 💻 代码（py, js, html, css, java, cpp, c, h, ts, go, rs）
- 🔤 字体（ttf, otf, woff, woff2, eot）
- 📋 其他

### 2. 📅 按日期自动整理
根据文件的修改日期，自动创建 年/月 文件夹结构进行归档。

### 3. 🔍 重复文件查找
通过 MD5 哈希值检测完全相同的文件，支持：
- 自动选中保留最新/最旧的文件
- 预览后批量删除

### 4. ✏️ 批量重命名
支持多种重命名模式：
- 顺序编号（前缀 + 编号）
- 日期命名（原文件名 + 日期）
- 自定义模式（支持 {n} 编号、{d} 日期、{o} 原名、{e} 扩展名 占位符）

### 5. 📂 空文件夹查找与清理
快速扫描并清理指定目录下的所有空文件夹。

### 6. 📊 大文件查找
查找指定目录下占用空间最大的 N 个文件，帮助释放磁盘空间。

### 7. 👁️ 预览与撤销
- 所有操作执行前可预览变更
- 支持撤销上一次操作

## 系统要求

- Windows 10/11
- Python 3.10+
- PyQt6 >= 6.5
- psutil >= 5.9

## 安装与运行

```bash
# 安装依赖
pip install PyQt6 psutil

# 运行程序
python main.py
```

## 界面预览

- 🎨 暗黑主题（背景 #0a0a0a，卡片 #111122）
- 💜 渐变色强调按钮（#667eea → #764ba2）
- 📐 圆角设计
- 🌳 树形目录浏览

## 项目结构

```
FileOrganizer/
├── main.py              # 程序入口
├── pyproject.toml       # 项目配置
├── README.md            # 说明文档
└── app/
    ├── __init__.py
    ├── ui.py            # 主界面
    ├── styles.py        # 样式定义
    ├── workers.py       # 后台工作线程
    └── organizer.py     # 文件整理核心逻辑
```

## 许可证

MIT License
