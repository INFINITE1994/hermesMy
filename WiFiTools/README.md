# WiFiTools - 专业WiFi管理工具

## 功能特性

- **WiFi扫描器** - 扫描并列出所有可用WiFi网络
- **信号强度监测** - 实时显示信号强度与可视化指示器
- **网络详情** - 查看SSID、BSSID、信道、加密方式、速度等
- **已保存密码** - 查看已保存的WiFi密码
- **网速测试** - 测试网络上下行速度与延迟
- **信道分析** - 分析信道使用情况，找到最不拥挤的信道
- **WiFi配置管理** - 管理已保存的WiFi配置文件

## 环境要求

- Windows 10/11
- Python 3.10+
- 管理员权限（部分功能需要）

## 安装

```bash
pip install PyQt6 psutil
```

## 运行

```bash
python main.py
```

## 技术栈

- Python 3.10+
- PyQt6 (图形界面)
- psutil (系统监控)
- subprocess (调用Windows netsh命令)

## 截图

深色主题界面，采用 #667eea 至 #764ba2 渐变色设计风格。

## 许可证

MIT License
