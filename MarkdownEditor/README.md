# 📝 Markdown 编辑器

一款专业的桌面 Markdown 编辑器，基于 PyQt6 构建，支持实时预览、数学公式渲染、表格编辑等高级功能。

## ✨ 功能特性

### 核心功能
- **分屏视图** - 左侧编辑器，右侧实时预览
- **语法高亮** - Markdown 语法高亮显示
- **工具栏** - 快捷按钮：加粗、斜体、标题、列表、链接、图片、代码块
- **文件管理** - 新建、打开、保存、另存为
- **导出功能** - 导出为 HTML、PDF、DOCX 格式

### 高级功能
- **表格编辑器** - 可视化创建和编辑表格
- **数学公式** - LaTeX 数学公式渲染支持
- **主题切换** - 深色/浅色主题一键切换
- **文档大纲** - 侧边栏显示文档结构
- **查找替换** - 支持正则表达式的搜索和替换

## 🛠️ 安装

### 环境要求
- Python 3.10 或更高版本
- Windows 10/11

### 安装步骤

1. 克隆或下载项目
```bash
git clone https://github.com/markdown-editor/MarkdownEditor.git
cd MarkdownEditor
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -e .
```

4. 运行应用
```bash
python main.py
```

## 🎯 使用指南

### 快捷键
| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 新建文件 |
| `Ctrl+O` | 打开文件 |
| `Ctrl+S` | 保存文件 |
| `Ctrl+Shift+S` | 另存为 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Ctrl+F` | 查找 |
| `Ctrl+H` | 替换 |
| `Ctrl+B` | 加粗 |
| `Ctrl+I` | 斜体 |
| `Ctrl+1~6` | 标题 1-6 |
| `Ctrl+E` | 导出 HTML |
| `Ctrl+Shift+T` | 切换主题 |
| `F11` | 全屏 |

### 工具栏按钮
- **B** - 加粗文本
- *I* - 斜体文本
- **H1-H3** - 标题
- **•** - 无序列表
- **1.** - 有序列表
- **>** - 引用块
- **</>** - 代码块
- **🔗** - 插入链接
- **🖼️** - 插入图片
- **📊** - 插入表格
- **∑** - 插入数学公式

### 数学公式
支持 LaTeX 数学公式语法：
- 行内公式：`$E = mc^2$`
- 块级公式：`$$\sum_{i=1}^{n} x_i = x_1 + x_2 + ... + x_n$$`

### 表格编辑
点击工具栏的表格按钮，可以：
- 设置行列数
- 可视化编辑单元格内容
- 自动生成 Markdown 表格语法

## 🎨 主题

### 深色主题（默认）
- 背景色：`#0a0a0a`
- 卡片色：`#111122`
- 强调色渐变：`#667eea` → `#764ba2`

### 浅色主题
- 背景色：`#ffffff`
- 卡片色：`#f5f5f5`
- 强调色：保持一致

## 📁 项目结构

```
MarkdownEditor/
├── main.py          # 主程序入口
├── pyproject.toml   # 项目配置
└── README.md        # 项目说明
```

## 🔧 依赖项

- **PyQt6** - GUI 框架
- **PyQt6-WebEngine** - Web 渲染引擎（用于预览）
- **markdown** - Markdown 解析器
- **Pygments** - 语法高亮

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。
