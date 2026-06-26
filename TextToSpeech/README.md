# 🔊 TextToSpeech - 专业文字转语音工具

一款基于 PyQt6 的专业文字转语音桌面应用，支持中文界面、多语音选择、批量转换、音频保存等功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 核心功能

### 🎤 语音合成
- **文本输入** - 支持中英文及多种语言文本
- **语音选择** - 自动检测系统已安装的 TTS 语音引擎
- **语速控制** - 50~300 字/分钟可调
- **音量控制** - 0~100% 无级调节
- **实时预览** - 即时朗读，所见即所得

### 📦 批量转换
- **多行输入** - 每行一条文本，批量处理
- **批量朗读** - 按顺序自动朗读所有文本
- **批量导出** - 一键保存为多个 WAV 文件

### 💾 音频保存
- **WAV 格式** - 高质量无损音频输出
- **自定义路径** - 可选择保存位置
- **批量保存** - 支持批量导出到指定目录

### 📜 历史记录
- **自动记录** - 每次转换自动保存历史
- **快速重播** - 一键重新朗读历史文本
- **历史管理** - 支持清空、浏览历史记录

### ⌨️ 全局快捷键
- **Ctrl+Shift+S** - 读取剪贴板内容并朗读
- **全局可用** - 在任何应用中均可触发
- **即按即读** - 复制文本后按下快捷键即可

## 🎨 界面设计

采用专业暗色主题设计：
- 背景色: `#0a0a0a`
- 卡片色: `#111122`
- 渐变强调: `#667eea` → `#764ba2`
- 全中文界面标签
- 圆角卡片式布局

## 📋 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **依赖包**:
  - PyQt6 >= 6.5.0
  - pyttsx3 >= 2.90
  - pynput >= 1.7.6
  - pyperclip >= 1.8.2

## 🚀 安装与运行

### 方式一：使用 pip 安装依赖

```bash
# 进入项目目录
cd TextToSpeech

# 安装依赖
pip install PyQt6 pyttsx3 pynput pyperclip

# 运行程序
python main.py
```

### 方式二：使用 pyproject.toml

```bash
# 进入项目目录
cd TextToSpeech

# 安装项目（含所有依赖）
pip install .

# 运行程序
python main.py
```

### 方式三：开发模式安装

```bash
# 以开发模式安装（可编辑）
pip install -e .

# 运行程序
python main.py
```

## 📁 项目结构

```
TextToSpeech/
├── main.py           # 主程序文件
├── pyproject.toml    # 项目配置与依赖
└── README.md         # 说明文档（本文件）
```

## 🔧 配置说明

程序配置文件保存在用户目录下：
- **设置文件**: `~/.text_to_speech/settings.json`
- **历史文件**: `~/.text_to_speech/history.json`

### 可配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| rate | int | 150 | 语速（字/分钟） |
| volume | float | 1.0 | 音量（0.0~1.0） |
| voice_id | str | "" | 语音引擎 ID |
| save_path | str | ~/Documents | 默认保存路径 |

## 📖 使用指南

### 基本使用

1. 启动程序：`python main.py`
2. 在文本框中输入要转换的文字
3. 选择合适的语音引擎
4. 调整语速和音量
5. 点击「开始朗读」或「保存音频」

### 批量转换

1. 切换到「批量转换」选项卡
2. 每行输入一条文本
3. 点击「批量朗读」或「批量保存为WAV」

### 全局快捷键

1. 复制任意文本到剪贴板
2. 按下 `Ctrl+Shift+S`
3. 程序自动朗读剪贴板内容

## 🐛 常见问题

### Q: 没有语音引擎可用？

A: 请确保系统已安装 TTS 语音包：
- Windows 10/11: 设置 → 时间和语言 → 语言 → 添加语言 → 下载语音包
- 或安装第三方 TTS 引擎

### Q: 中文语音效果不佳？

A: 建议安装以下中文语音：
- Microsoft Huihui Desktop
- Microsoft Kangkang Desktop
- 或使用第三方高质量 TTS 引擎

### Q: 快捷键不生效？

A: 请检查：
- 程序是否正在运行
- 是否有其他程序占用了相同快捷键
- pynput 库是否正确安装

## 📄 许可证

本项目采用 MIT 许可证。详见项目根目录 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。

---

**TextToSpeech** - 让文字开口说话 🎙️
