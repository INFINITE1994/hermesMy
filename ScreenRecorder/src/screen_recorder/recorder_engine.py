"""
录制引擎模块 - 处理屏幕录制的核心逻辑
"""
import os
import time
import threading
from enum import Enum
from datetime import datetime

import numpy as np
from PIL import Image
import mss
import imageio

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class RecordingMode(Enum):
    """录制模式"""
    FULLSCREEN = 0
    REGION = 1
    WINDOW = 2


class RecorderEngine(QObject):
    """录制引擎"""
    
    recording_finished = pyqtSignal(str)  # 输出文件路径
    error_occurred = pyqtSignal(str)  # 错误信息
    frame_captured = pyqtSignal(int)  # 帧数
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_paused = False
        self.output_file = None
        self.recording_thread = None
        self.frame_count = 0
        self.start_time = 0
        
        # 录制参数
        self.mode = RecordingMode.FULLSCREEN
        self.fps = 30
        self.quality = 80
        self.region = None
        self.record_audio = False
        self.mic_audio = False
        self.show_cursor = True
        
        # 帧缓冲
        self.frame_buffer = []
        self.buffer_lock = threading.Lock()
    
    def start(self, mode, output_file, fps=30, quality=80, region=None,
              record_audio=False, mic_audio=False, show_cursor=True):
        """开始录制"""
        if self.is_recording:
            return False
        
        self.mode = mode
        self.output_file = output_file
        self.fps = fps
        self.quality = quality
        self.region = region
        self.record_audio = record_audio
        self.mic_audio = mic_audio
        self.show_cursor = show_cursor
        
        self.is_recording = True
        self.is_paused = False
        self.frame_count = 0
        self.frame_buffer = []
        self.start_time = time.time()
        
        # 启动录制线程
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()
        
        return True
    
    def stop(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # 等待录制线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
        
        # 保存视频
        self._save_video()
    
    def pause(self):
        """暂停录制"""
        self.is_paused = True
    
    def resume(self):
        """继续录制"""
        self.is_paused = False
    
    def _recording_loop(self):
        """录制主循环"""
        try:
            with mss.mss() as sct:
                # 获取录制区域
                if self.mode == RecordingMode.FULLSCREEN:
                    monitor = sct.monitors[1]  # 主显示器
                elif self.mode == RecordingMode.REGION and self.region:
                    monitor = {
                        "left": self.region.x(),
                        "top": self.region.y(),
                        "width": self.region.width(),
                        "height": self.region.height()
                    }
                else:
                    monitor = sct.monitors[1]
                
                frame_interval = 1.0 / self.fps
                
                while self.is_recording:
                    if self.is_paused:
                        time.sleep(0.1)
                        continue
                    
                    loop_start = time.time()
                    
                    # 捕获屏幕
                    screenshot = sct.grab(monitor)
                    
                    # 转换为numpy数组
                    frame = np.array(screenshot)
                    
                    # BGRA -> RGB
                    if frame.shape[2] == 4:
                        frame = frame[:, :, [2, 1, 0]]  # BGR
                        # 添加alpha通道或转换为RGB
                        frame = np.stack([frame[:,:,0], frame[:,:,1], frame[:,:,2]], axis=-1)
                    
                    # 添加到缓冲区
                    with self.buffer_lock:
                        self.frame_buffer.append(frame)
                        self.frame_count += 1
                    
                    # 发送帧数信号
                    self.frame_captured.emit(self.frame_count)
                    
                    # 控制帧率
                    elapsed = time.time() - loop_start
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        
        except Exception as e:
            self.error_occurred.emit(f"录制错误: {str(e)}")
    
    def _save_video(self):
        """保存视频文件"""
        if not self.frame_buffer:
            self.error_occurred.emit("没有捕获到任何帧")
            return
        
        try:
            output_dir = os.path.dirname(self.output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            fmt = os.path.splitext(self.output_file)[1].lower()
            
            if fmt == '.gif':
                self._save_gif()
            else:
                self._save_video_file()
            
            self.recording_finished.emit(self.output_file)
        
        except Exception as e:
            self.error_occurred.emit(f"保存视频失败: {str(e)}")
    
    def _save_video_file(self):
        """保存为MP4或AVI"""
        # 计算输出参数
        quality_param = self.quality / 100.0
        
        # 使用imageio保存
        writer = imageio.get_writer(
            self.output_file,
            fps=self.fps,
            quality=quality_param,
            codec='libx264' if self.output_file.endswith('.mp4') else 'libxvid',
            output_params=['-crf', str(int((1 - quality_param) * 51))]
        )
        
        with self.buffer_lock:
            frames = list(self.frame_buffer)
        
        for frame in frames:
            writer.append_data(frame)
        
        writer.close()
    
    def _save_gif(self):
        """保存为GIF"""
        with self.buffer_lock:
            frames = list(self.frame_buffer)
        
        # 降采样以减小GIF大小
        target_fps = min(self.fps, 15)
        skip = max(1, self.fps // target_fps)
        sampled_frames = frames[::skip]
        
        # 转换为PIL图像
        pil_frames = []
        for frame in sampled_frames:
            img = Image.fromarray(frame)
            # 调整大小
            if img.width > 1280:
                ratio = 1280 / img.width
                new_size = (1280, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            pil_frames.append(img)
        
        # 保存GIF
        duration = int(1000 / target_fps)
        pil_frames[0].save(
            self.output_file,
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
