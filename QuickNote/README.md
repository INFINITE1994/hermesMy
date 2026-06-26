# QuickNote

<p align="center">
  <strong>✨ 轻量级 Markdown 笔记应用 ✨</strong>
</p>

<p align="center">
  一个功能完整、界面美观的桌面笔记应用，基于 PyQt6 构建
</p>

---

## 📸 功能概览

| 功能 | 描述 |
|------|------|
| 📝 Markdown 编辑器 | 支持完整的 Markdown 语法，带语法高亮 |
| 📖 实时预览 | 左侧编辑，右侧即时渲染预览 |
| 📓 笔记本系统 | 用笔记本/文件夹分类管理笔记 |
| 🏷 标签系统 | 使用 `#标签` 快速分类和筛选笔记 |
| 🔍 全文搜索 | 跨所有笔记进行全文检索 |
| 📤 多格式导出 | 支持导出为 HTML / Markdown / TXT / PDF |
| 💾 自动保存 | 编辑时自动保存，无需担心丢失 |
| 💻 代码高亮 | 代码块语法高亮显示 |
| 🎨 主题切换 | 暗色 / 亮色主题一键切换 |

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows / macOS / Linux

### 安装依赖

```bash
pip install PyQt6 markdown Pygments
```

### 运行应用

```bash
cd QuickNote
python main.py
```

## 📁 项目结构

```
QuickNote/
├── main.py          # 主程序入口
├── pyproject.toml   # 项目配置
└── README.md        # 项目说明（本文件）
```

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 新建笔记 |
| `Ctrl+S` | 保存笔记 |
| `Ctrl+F` | 搜索笔记 |
| `Ctrl+T` | 切换暗色/亮色主题 |
| `Ctrl+P` | 切换预览面板 |
| `Ctrl++` | 放大字体 |
| `Ctrl+-` | 缩小字体 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Delete` | 删除笔记 |

## 📖 Markdown 语法支持

### 标题

```markdown
# 一级标题
## 二级标题
### 三级标题
```

### 文本格式

```markdown
**粗体文本**
*斜体文本*
~~删除线~~
`行内代码`
```

### 代码块

````markdown
```python
def hello():
    print("Hello, World!")
```
````

### 列表

```markdown
- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2
```

### 链接和图片

```markdown
[链接文本](https://example.com)
![图片描述](image.png)
```

### 引用

```markdown
> 这是一段引用文本
```

### 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
```

### 标签

```markdown
在笔记中使用 #标签名 来添加标签
例如: #工作 #学习 #重要
```

## 🏷 标签使用技巧

1. 在笔记内容中使用 `#标签名` 格式添加标签
2. 支持中文标签，如 `#工作笔记`、`#学习资料`
3. 左侧面板会自动显示所有标签
4. 点击标签可快速筛选相关笔记
5. 可通过菜单"笔记 → 添加标签"快速添加

## 📤 导出功能

支持四种导出格式：

- **HTML** - 生成带样式的网页文件，可直接在浏览器打开
- **Markdown** - 导出原始 .md 文件
- **TXT** - 导出纯文本，去除 Markdown 标记
- **PDF** - 导出 PDF 文件（需要 Qt 打印支持）

导出方式：
1. 菜单 → 文件 → 导出 → 选择格式
2. 右键点击笔记 → 导出 → 选择格式

## 🎨 主题定制

应用内置两套主题：

### 暗色主题（默认）
- 背景色: `#0a0a0a`
- 卡片色: `#111122`
- 强调色: `#667eea` → `#764ba2`（渐变）

### 亮色主题
- 背景色: `#f5f5f5`
- 卡片色: `#ffffff`
- 强调色: `#667eea` → `#764ba2`（渐变）

按 `Ctrl+T` 快速切换主题。

## 💾 数据存储

- 笔记存储位置: `~/.quicknote/notebooks/`
- 设置文件: `~/.quicknote/settings.json`
- 笔记以标准 Markdown (.md) 文件存储
- 每个笔记本对应一个子文件夹

## 🔧 开发说明

### 技术栈

- **GUI 框架**: PyQt6
- **Markdown 解析**: Python-Markdown
- **代码高亮**: Pygments
- **数据格式**: Markdown (.md)

### 依赖

```toml
[project]
dependencies = [
    "PyQt6>=6.4.0",
    "markdown>=3.4.0",
    "Pygments>=2.14.0",
]
```

## ❓ 常见问题

### Q: 应用启动后空白？

A: 请确保已安装所有依赖：
```bash
pip install PyQt6 markdown Pygments
```

### Q: 如何备份笔记？

A: 直接复制 `~/.quicknote/notebooks/` 文件夹即可，所有笔记都是标准 Markdown 文件。

### Q: 如何在多台电脑间同步？

A: 使用云同步工具（如 OneDrive、坚果云）同步 `~/.quicknote/` 文件夹。

### Q: 支持插入图片吗？

A: 支持 Markdown 图片语法 `![描述](url)`，目前支持网络图片链接。

## 📄 许可证

MIT License

---

<p align="center">
  <strong>QuickNote</strong> - 让记录更简单 ✨
</p>
