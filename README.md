# 🧰 HermesMy 工具箱

一套轻量级 Windows 桌面工具集。深色主题，开箱即用，解决日常电脑维护需求。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## 📦 包含工具

| 工具 | 功能 | 一句话介绍 |
|------|------|-----------|
| 🧹 **CleanMaster** | 系统清理 | 一键清理系统垃圾，释放磁盘空间 |
| 📄 **PDFMaster** | PDF处理 | 合并、拆分、压缩、加水印、转图片 |
| 🖼️ **ImageBatch** | 图片批处理 | 批量调整大小、格式转换、压缩、重命名 |
| 📁 **FileOrganizer** | 文件整理 | 自动分类、查找重复、批量重命名 |
| 📋 **ClipboardManager** | 剪贴板管理 | 记录历史、搜索、置顶、分类 |
| 📝 **QuickNote** | 快速笔记 | Markdown编辑、笔记本、标签、导出 |
| 🔐 **PasswordManager** | 密码管理 | AES-256加密、密码生成、分类管理 |
| 📊 **SysMonitor** | 系统监控 | CPU/内存/磁盘/网络实时监控 |
| 🌐 **NetTools** | 网络工具 | Ping/端口扫描/DNS/测速/路由追踪 |
| 📱 **QRCodeTool** | 二维码工具 | 生成/扫描/批量生成二维码 |
| 🎨 **ColorPicker** | 取色器 | 屏幕取色/色轮/调色板/对比度检查 |
| 📝 **TextTools** | 文本工具 | JSON格式化/Base64/URL编解码/哈希/正则 |
| 📐 **UnitConverter** | 单位换算 | 长度/重量/温度/面积/体积/速度/数据/时间/货币 |
| ✏️ **MarkdownEditor** | Markdown编辑器 | 实时预览/语法高亮/导出HTML/PDF |
| 💾 **DiskAnalyzer** | 磁盘分析器 | 树状图/文件类型分析/大文件查找 |
| 🎬 **GIFMaker** | GIF制作 | 视频转GIF/图片合成/屏幕录制/编辑优化 |
| 🎵 **AudioTools** | 音频工具 | 格式转换/裁剪/合并/音量调节/录制 |
| 🔍 **RegexTester** | 正则测试器 | 实时匹配/常用模式/解释/保存 |
| 📸 **ScreenshotTool** | 截图工具 | 全屏/区域/窗口截图/标注/模糊 |
| ⏰ **TimerTools** | 计时器 | 倒计时/秒表/世界时钟/番茄钟/闹钟 |
| 🔒 **CryptoTools** | 加密工具 | 文本加密/文件加密/哈希/密码生成/JWT |
| 🎬 **VideoTools** | 视频工具 | 格式转换/裁剪/合并/压缩/音频提取 |
| 🕷️ **WebScraper** | 网页抓取 | URL抓取/链接提取/图片下载/批量抓取 |
| 💻 **SystemInfo** | 系统信息 | CPU/内存/磁盘/显卡/网络/主板详情 |
| 🧰 **ToolBox** | 工具箱启动器 | 一键启动所有工具的统一入口 |

## 🚀 快速开始

### 方式一：直接运行（需要Python环境）

```bash
# 安装依赖
pip install PyQt6 psutil send2trash PyPDF2 Pillow

# 启动工具箱
python ToolBox/main.py

# 或单独启动某个工具
python CleanMaster/main.py
python PDFMaster/main.py
python ImageBatch/main.py
python FileOrganizer/main.py
```

### 方式二：打包为exe

```bash
pip install pyinstaller
# 一键打包所有工具
build_all.bat
```

打包后的exe文件在各工具的 `dist/` 目录下。

## ✨ 设计特点

- 🌙 **深色主题** — 护眼的深色UI，适合长时间使用
- 🎨 **现代设计** — 渐变按钮、圆角卡片、流畅动画
- 🇨🇳 **全中文界面** — 零门槛使用
- ⚡ **轻量高效** — 纯Python实现，启动快，占用低
- 🔒 **安全优先** — 删除前预览，可恢复到回收站

## 📸 功能详情

### 🧹 CleanMaster 系统清理

**基础清理（免费）：**
- 临时文件清理
- 浏览器缓存（Chrome/Edge/Firefox）
- 回收站清理
- 崩溃转储文件
- Windows更新缓存
- 缩略图缓存
- 预读取文件
- 开发缓存（npm/pip/uv）

**Pro功能：**
- 🔍 大文件查找器 — 找出磁盘上最大的文件
- 🔁 重复文件查找器 — 按MD5哈希查找重复文件
- ⚡ 启动项管理 — 管理开机自启动程序
- 📊 磁盘分析器 — 可视化磁盘空间占用

### 📄 PDFMaster PDF处理

- 合并多个PDF为一个
- 按页码范围拆分PDF
- 压缩PDF减小文件大小
- 添加文字水印
- PDF页面转为图片
- 提取PDF中的文字

### 🖼️ ImageBatch 图片批处理

- 批量调整大小（按比例或固定尺寸）
- 批量格式转换（PNG/JPG/WebP/BMP）
- 批量压缩（可调质量）
- 批量重命名（序号/前缀后缀/查找替换）
- 批量添加文字/图片水印
- 批量旋转/翻转
- 预览效果

### 📁 FileOrganizer 文件整理

- 按文件类型自动分类
- 按日期自动归档
- 查找重复文件（MD5哈希）
- 批量重命名（序号/日期/自定义模式）
- 空文件夹查找清理
- 大文件查找器
- 操作预览和撤销

## 📁 项目结构

```
hermesMy/
├── CleanMaster/          # 系统清理工具
│   ├── core/             # 扫描引擎
│   ├── ui/               # 界面
│   └── main.py           # 入口
├── PDFMaster/            # PDF处理工具
│   └── main.py
├── ImageBatch/           # 图片批处理工具
│   └── main.py
├── FileOrganizer/        # 文件整理工具
│   ├── app/              # 应用模块
│   └── main.py
├── ToolBox/              # 统一启动器
│   └── main.py
├── build_all.bat         # 一键打包脚本
└── README.md
```

## 🛠️ 技术栈

- Python 3.10+
- PyQt6 (GUI框架)
- Pillow (图片处理)
- PyPDF2 (PDF处理)
- psutil (系统信息)
- send2trash (安全删除)

## 📝 License

MIT License - 免费使用，自由修改，自由分发。

## 🙏 支持作者

如果这些工具对你有帮助，欢迎：

- ⭐ 给项目点个 Star
- 🐛 提交 Issue 反馈问题
- 💡 提出新功能建议
- ☕ [请作者喝杯咖啡](https://github.com/sponsors/INFINITE1994)

---

Made with ❤️ by INFINITE1994
