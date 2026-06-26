# GIF Maker - 专业 GIF 制作与编辑工具

## 功能特性

### 🎬 视频转 GIF
- 支持 MP4、AVI、MOV 等常见视频格式
- 可调节帧率、质量、分辨率
- 支持截取指定时间段

### 🖼️ 图片合成 GIF
- 支持 PNG、JPG、BMP、WebP 等图片格式
- 可调节每帧持续时间
- 支持排序和预览

### 📺 屏幕录制转 GIF
- 支持选择录制区域
- 实时预览录制内容
- 可调节录制帧率

### ✏️ GIF 编辑器
- 裁剪、缩放、旋转 GIF
- 添加文字水印
- 调整播放速度
- 支持逐帧编辑

### 📦 GIF 优化器
- 智能压缩减小文件体积
- 可调节颜色数量
- 支持有损/无损压缩

### 🎞️ 帧提取器
- 从 GIF 中提取单帧图片
- 支持批量导出
- 多种输出格式

### 👁️ 预览功能
- 实时预览 GIF 动画
- 支持暂停、逐帧播放
- 显示帧信息

## 环境要求

- Python 3.10+
- Windows 10/11

## 安装与运行

```bash
# 安装依赖
pip install PyQt6 Pillow imageio imageio-ffmpeg numpy

# 运行程序
python main.py
```

## 技术栈

- **界面框架**: PyQt6
- **图像处理**: Pillow
- **GIF/视频处理**: imageio + imageio-ffmpeg
- **数值计算**: NumPy

## 界面风格

采用深色主题设计，主色调为：
- 背景色: #0a0a0a
- 卡片色: #111122  
- 渐变强调色: #667eea → #764ba2

## 许可证

MIT License
