# SysMonitor - 系统监控仪表板

一个基于 PyQt6 的专业级 Windows 系统实时监控工具，采用深色主题设计。

## 功能特性

- **CPU 监控** - 实时显示每个核心的使用率、温度（如支持）
- **内存监控** - RAM 使用率、交换分区、内存组成
- **磁盘监控** - 各磁盘使用情况、读写速度
- **网络监控** - 上传/下载速度、总传输数据量
- **进程列表** - 按 CPU/内存排序的 Top 进程
- **历史图表** - CPU/内存/网络的实时折线图
- **系统信息** - 操作系统、主机名、运行时间、GPU 信息
- **告警系统** - CPU/内存超过阈值时的视觉告警

## 安装

```bash
pip install PyQt6 psutil pyqtgraph
```

或使用项目管理：

```bash
pip install -e .
```

## 运行

```bash
python main.py
```

## 技术栈

- Python 3.10+
- PyQt6
- psutil
- pyqtgraph

## 界面预览

深色主题配色方案：
- 背景色：#0a0a0a
- 卡片色：#111122
- 强调色渐变：#667eea → #764ba2

## 许可证

MIT License
