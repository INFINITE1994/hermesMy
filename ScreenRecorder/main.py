"""
ScreenRecorder - 专业级屏幕录制工具
===================================

支持功能：
- 全屏录制
- 区域录制
- 窗口录制
- 音频录制（系统音频 + 麦克风）
- 摄像头叠加
- 屏幕标注
- 多格式导出（MP4, AVI, GIF）
- 全局快捷键

运行方式：
    python main.py
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from screen_recorder.main import main

if __name__ == "__main__":
    main()
