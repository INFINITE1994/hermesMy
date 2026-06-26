"""
全局快捷键管理模块
"""
import threading
from PyQt6.QtCore import QObject, pyqtSignal

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告: pynput未安装，全局快捷键功能不可用")


class HotkeyManager(QObject):
    """全局快捷键管理器"""
    
    hotkey_pressed = pyqtSignal(str)  # 快捷键动作名称
    
    def __init__(self):
        super().__init__()
        self.hotkeys = {}  # {key_combination: action_name}
        self.listener = None
        self.running = False
        
        if PYNPUT_AVAILABLE:
            self.start()
    
    def register_hotkey(self, key_combination, action_name):
        """注册快捷键
        
        Args:
            key_combination: 按键组合，如 'F9', 'ctrl+shift+s'
            action_name: 动作名称
        """
        self.hotkeys[key_combination.lower()] = action_name
    
    def unregister_hotkey(self, key_combination):
        """注销快捷键"""
        key = key_combination.lower()
        if key in self.hotkeys:
            del self.hotkeys[key]
    
    def start(self):
        """启动监听"""
        if not PYNPUT_AVAILABLE:
            return
        
        if self.running:
            return
        
        self.running = True
        
        try:
            # 使用listener监听键盘事件
            self.listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            self.listener.daemon = True
            self.listener.start()
        except Exception as e:
            print(f"启动快捷键监听失败: {e}")
            self.running = False
    
    def stop(self):
        """停止监听"""
        self.running = False
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass
    
    def _on_key_press(self, key):
        """键盘按下事件"""
        try:
            # 构建按键字符串
            key_str = self._key_to_string(key)
            if not key_str:
                return
            
            # 检查是否匹配注册的快捷键
            for hotkey, action in self.hotkeys.items():
                if self._match_hotkey(hotkey, key_str):
                    # 使用信号在主线程中处理
                    self.hotkey_pressed.emit(action)
                    break
        
        except Exception as e:
            pass
    
    def _key_to_string(self, key):
        """将按键转换为字符串"""
        try:
            # 特殊按键映射
            special_keys = {
                keyboard.Key.f1: 'f1',
                keyboard.Key.f2: 'f2',
                keyboard.Key.f3: 'f3',
                keyboard.Key.f4: 'f4',
                keyboard.Key.f5: 'f5',
                keyboard.Key.f6: 'f6',
                keyboard.Key.f7: 'f7',
                keyboard.Key.f8: 'f8',
                keyboard.Key.f9: 'f9',
                keyboard.Key.f10: 'f10',
                keyboard.Key.f11: 'f11',
                keyboard.Key.f12: 'f12',
                keyboard.Key.space: 'space',
                keyboard.Key.enter: 'enter',
                keyboard.Key.tab: 'tab',
                keyboard.Key.backspace: 'backspace',
                keyboard.Key.delete: 'delete',
                keyboard.Key.esc: 'escape',
                keyboard.Key.caps_lock: 'capslock',
            }
            
            # 修饰键
            modifier_keys = {
                keyboard.Key.ctrl_l: 'ctrl',
                keyboard.Key.ctrl_r: 'ctrl',
                keyboard.Key.alt_l: 'alt',
                keyboard.Key.alt_r: 'alt',
                keyboard.Key.shift_l: 'shift',
                keyboard.Key.shift_r: 'shift',
                keyboard.Key.cmd_l: 'win',
                keyboard.Key.cmd_r: 'win',
            }
            
            if key in special_keys:
                return special_keys[key]
            elif key in modifier_keys:
                return modifier_keys[key]
            elif hasattr(key, 'char') and key.char:
                return key.char.lower()
            else:
                return None
        
        except Exception:
            return None
    
    def _match_hotkey(self, hotkey_str, current_key):
        """检查是否匹配快捷键"""
        # 解析快捷键组合
        parts = hotkey_str.split('+')
        
        # 单个按键（如F9）
        if len(parts) == 1:
            return parts[0] == current_key
        
        # 组合键（如ctrl+shift+s）
        # 注意：这是一个简化的匹配，实际应用中需要跟踪修饰键状态
        return False
    
    def __del__(self):
        """析构函数"""
        self.stop()
