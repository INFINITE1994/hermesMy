# 📋 剪贴板管理器 (ClipboardManager)

> 一款简洁优雅的 Windows 剪贴板历史管理工具，基于 PyQt6 构建。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📝 剪贴板历史 | 自动记录所有复制的文本和图片 |
| 🔍 全文搜索 | 支持 FTS 全文检索，快速找到历史内容 |
| 📌 收藏置顶 | 置顶常用片段，永不丢失 |
| ⚡ 快速粘贴 | 单击即可将历史内容复制回剪贴板 |
| 🏷️ 智能分类 | 自动识别：文本、链接、邮箱、代码、图片、数字 |
| 📤 导出功能 | 支持导出为 JSON / TXT 格式 |
| ⌨️ 全局热键 | `Ctrl + Shift + V` 随时显示/隐藏窗口 |
| 🔔 系统托盘 | 最小化后在后台运行，托盘图标管理 |

## 🚀 安装与运行

### 环境要求

- Windows 10/11
- Python 3.10+

### 安装依赖

```bash
cd ClipboardManager
pip install PyQt6 keyboard Pillow
```

### 运行程序

```bash
python main.py
```

或通过项目配置安装：

```bash
pip install -e .
clipboard-manager
```

## 🎨 界面设计

采用深色主题设计：

- **背景色**: `#0a0a0a`
- **卡片色**: `#111122`
- **渐变强调**: `#667eea` → `#764ba2`
- 全中文界面，操作直观

## 📁 数据存储

剪贴板历史数据存储在：

```
%APPDATA%/ClipboardManager/clipboard.db
```

使用 SQLite 数据库，支持全文搜索索引。

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Shift + V` | 显示/隐藏主窗口 |
| 点击「复制」按钮 | 将条目复制回剪贴板 |
| 点击「📌」按钮 | 置顶/取消置顶条目 |

## 📤 导出格式

### JSON 格式

```json
[
  {
    "content": "复制的文本内容",
    "category": "文本",
    "pinned": false,
    "created_at": "2024-01-15 10:30:00"
  }
]
```

### TXT 格式

```
[2024-01-15 10:30:00] [文本] ★
复制的文本内容
────────────────────────────────────────────────────────────
```

## 🏗️ 项目结构

```
ClipboardManager/
├── main.py          # 主程序入口
├── pyproject.toml   # 项目配置
└── README.md        # 本文件
```

## 🔧 技术细节

- **GUI 框架**: PyQt6
- **数据库**: SQLite + FTS4 全文搜索
- **全局热键**: keyboard 库
- **图片处理**: Pillow (可选)
- **线程安全**: 使用 WAL 模式的 SQLite

## 📄 许可证

MIT License

---

**Made with ❤️ for productivity**
