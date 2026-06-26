"""
测试脚本 - 验证应用程序是否可以正常启动
"""
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有模块是否可以正确导入"""
    print("测试模块导入...")
    
    try:
        from screen_recorder import __version__
        print(f"✓ screen_recorder 模块导入成功 (版本: {__version__})")
    except Exception as e:
        print(f"✗ screen_recorder 模块导入失败: {e}")
        return False
    
    try:
        from screen_recorder.recorder_engine import RecorderEngine, RecordingMode
        print("✓ recorder_engine 模块导入成功")
    except Exception as e:
        print(f"✗ recorder_engine 模块导入失败: {e}")
        return False
    
    try:
        from screen_recorder.annotation_widget import AnnotationOverlay
        print("✓ annotation_widget 模块导入成功")
    except Exception as e:
        print(f"✗ annotation_widget 模块导入失败: {e}")
        return False
    
    try:
        from screen_recorder.region_selector import RegionSelector
        print("✓ region_selector 模块导入成功")
    except Exception as e:
        print(f"✗ region_selector 模块导入失败: {e}")
        return False
    
    try:
        from screen_recorder.hotkey_manager import HotkeyManager
        print("✓ hotkey_manager 模块导入成功")
    except Exception as e:
        print(f"✗ hotkey_manager 模块导入失败: {e}")
        return False
    
    return True


def test_dependencies():
    """测试依赖是否安装"""
    print("\n测试依赖安装...")
    
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('PIL', 'Pillow'),
        ('imageio', 'imageio'),
        ('numpy', 'numpy'),
        ('mss', 'mss'),
    ]
    
    all_ok = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            print(f"✗ {package_name} 未安装")
            all_ok = False
    
    # 可选依赖
    optional = [
        ('cv2', 'opencv-python'),
        ('pynput', 'pynput'),
    ]
    
    for module_name, package_name in optional:
        try:
            __import__(module_name)
            print(f"✓ {package_name} 已安装 (可选)")
        except ImportError:
            print(f"⚠ {package_name} 未安装 (可选，部分功能可能不可用)")
    
    return all_ok


def test_gui():
    """测试GUI是否可以初始化"""
    print("\n测试GUI初始化...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        # 创建应用实例
        app = QApplication(sys.argv)
        print("✓ QApplication 创建成功")
        
        # 测试主窗口导入
        from screen_recorder.main_window import MainWindow
        print("✓ MainWindow 类导入成功")
        
        # 测试创建窗口（不显示）
        window = MainWindow()
        print("✓ MainWindow 实例创建成功")
        
        # 测试样式表
        from screen_recorder.main import get_stylesheet
        stylesheet = get_stylesheet()
        app.setStyleSheet(stylesheet)
        print("✓ 样式表应用成功")
        
        print("\n✓ 所有测试通过！应用程序可以正常启动。")
        return True
        
    except Exception as e:
        print(f"✗ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("ScreenRecorder 测试脚本")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n✗ 模块导入测试失败")
        return 1
    
    # 测试依赖
    if not test_dependencies():
        print("\n✗ 依赖测试失败")
        print("请运行: pip install PyQt6 Pillow imageio numpy mss")
        return 1
    
    # 测试GUI
    if not test_gui():
        print("\n✗ GUI测试失败")
        return 1
    
    print("\n" + "=" * 50)
    print("所有测试通过！")
    print("可以运行 'python main.py' 启动应用程序。")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
