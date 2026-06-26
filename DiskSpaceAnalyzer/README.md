# 💾 磁盘空间分析器 (DiskSpaceAnalyzer)

一个功能强大的磁盘空间可视化分析工具，基于 Python + PyQt6 构建，提供直观的图形界面帮助您了解磁盘使用情况。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green?logo=qt)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 功能特性

### 📊 树形图可视化 (Treemap)
直观展示文件夹大小分布，矩形面积与文件夹大小成正比。支持鼠标悬停查看详细信息，点击可聚焦子目录。

### 🎯 旭日图 (Sunburst Chart)
环形层次结构图，从内到外展示目录层级关系。内环为一级目录，外环为子目录，扇区角度表示大小比例。

### 📋 文件列表
可排序的文件列表视图，支持按名称、大小、类型、修改日期排序。内置搜索过滤功能，快速定位目标文件。

### 📁 文件夹树
可展开的树形目录结构，显示每个文件夹的大小、文件数和子目录数。支持多列信息展示。

### 🏆 Top 100 大文件
一键找出系统中最大的 100 个文件，帮助快速定位占用空间的大文件。双击可打开文件所在目录。

### 📊 文件类型分析
按文件扩展名统计文件数量和大小，以表格形式展示各类型文件的占用比例。

### 📅 旧文件查找
自定义天数阈值，查找指定时间内未被访问的文件，帮助清理长期未使用的文件。

### 💾 导出报告
- **HTML 报告**: 生成精美的网页格式分析报告，包含统计信息、类型分布和 Top 100 文件列表
- **CSV 数据**: 导出完整文件列表数据，可在 Excel 中进一步分析

## 🎨 界面设计

- **暗色主题**: 护眼的深色界面，主背景 `#0a0a0a`，卡片背景 `#111122`
- **渐变配色**: 主题色从 `#667eea` 到 `#764ba2` 的渐变效果
- **中文界面**: 所有界面元素使用中文标签，符合国内用户习惯
- **响应式布局**: 自适应窗口大小，支持最大化和调整

## 📦 安装

### 前提条件

- Python 3.10 或更高版本
- Windows 10/11

### 安装步骤

1. 克隆或下载项目

```bash
cd DiskSpaceAnalyzer
```

2. 安装依赖

```bash
pip install PyQt6 psutil
```

或使用项目配置安装：

```bash
pip install -e .
```

## 🚀 使用方法

### 启动应用

```bash
python main.py
```

### 基本操作流程

1. **选择目录**: 从下拉菜单选择磁盘分区，或点击"浏览"按钮选择任意目录
2. **开始扫描**: 点击"🔍 扫描"按钮，等待扫描完成
3. **查看分析**: 通过各个标签页查看不同维度的分析结果
4. **导出报告**: 切换到"导出"标签页，选择导出 HTML 或 CSV 格式

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开目录选择对话框 |
| `Ctrl+Q` | 退出程序 |

## 🏗️ 项目结构

```
DiskSpaceAnalyzer/
├── main.py          # 主程序文件（包含所有功能模块）
├── pyproject.toml   # 项目配置文件
└── README.md        # 说明文档
```

## 🔧 技术架构

### 核心模块

- **MainWindow**: 主窗口，管理所有 UI 组件和业务逻辑
- **ScanThread**: 后台扫描线程，避免阻塞 UI
- **TreemapWidget**: 树形图自定义绘制组件
- **SunburstWidget**: 旭日图自定义绘制组件
- **FileTableModel**: 文件列表数据模型（支持排序）
- **FolderTreeModel**: 文件夹树数据模型
- **FileTypeModel**: 文件类型统计数据模型

### 数据结构

- **FileInfo**: 文件信息（路径、名称、大小、时间戳、扩展名）
- **DirInfo**: 目录信息（路径、大小、文件/目录计数、子项）

### 设计模式

- **MVC 模式**: 使用 Qt 的 Model/View 架构分离数据和视图
- **观察者模式**: 信号/槽机制实现组件间通信
- **线程模式**: 后台线程执行耗时操作，主线程保持 UI 响应

## ⚡ 性能优化

- 使用 `os.scandir()` 代替 `os.listdir()` 提升扫描效率
- 后台线程扫描，UI 实时更新进度
- 限制树形图和旭日图的显示项数，避免过度渲染
- 使用代理模型实现高效的搜索过滤和排序

## 📝 注意事项

1. 扫描大目录（如整个 C 盘）可能需要较长时间，请耐心等待
2. 部分系统目录可能因权限限制无法访问，程序会自动跳过
3. 扫描过程中可随时点击"停止"按钮中断
4. 导出的 CSV 文件使用 UTF-8-BOM 编码，可直接在 Excel 中打开

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 跨平台 GUI 框架
- [psutil](https://github.com/giampaolo/psutil) - 系统信息获取库
- [Python](https://www.python.org/) - 编程语言

---

<p align="center">
  <sub>由 Hermes Agent 创建 | 2026</sub>
</p>
