# CleanMaster

轻量级 Windows 系统清理工具。一键扫描并清理系统垃圾文件，释放磁盘空间。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能

- 🗑️ **临时文件清理** — 系统和用户临时文件
- 🌐 **浏览器缓存** — Chrome / Edge / Firefox 缓存
- ♻️ **回收站清理** — 一键清空回收站
- 💥 **崩溃转储** — 程序崩溃日志和转储文件
- 🔄 **Windows 更新缓存** — 旧更新下载文件
- 🖼️ **缩略图缓存** — 文件管理器缩略图缓存
- ⚡ **预读取文件** — 程序预读取缓存
- 🔧 **开发缓存** — npm / pip / uv 包管理器缓存

## 安装

```bash
pip install PyQt6 psutil send2trash
```

## 运行

```bash
python main.py
```

## 截图

深色主题，现代 UI，扫描结果一目了然。

## 安全说明

- 默认只勾选安全可删除的项目
- 可能影响系统功能的项目会标注 ⚠️ 需谨慎
- 删除的文件会先进入回收站（可恢复）
- 扫描可随时中断

## 技术栈

- Python 3.10+
- PyQt6 (GUI)
- psutil (系统信息)
- send2trash (安全删除)

## License

MIT
