"""
AutomationTool - 测试脚本
验证应用程序可以正常导入和初始化
"""

import sys
import os

# 确保能找到app模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 导入成功")
    except ImportError as e:
        print(f"✗ PyQt6 导入失败: {e}")
        return False
    
    try:
        import psutil
        print("✓ psutil 导入成功")
    except ImportError as e:
        print(f"✗ psutil 导入失败: {e}")
        return False
    
    try:
        from app.styles import get_stylesheet
        print("✓ styles 模块导入成功")
    except ImportError as e:
        print(f"✗ styles 模块导入失败: {e}")
        return False
    
    try:
        from app.main_window import MainWindow
        print("✓ main_window 模块导入成功")
    except ImportError as e:
        print(f"✗ main_window 模块导入失败: {e}")
        return False
    
    try:
        from app.modules import (
            MacroRecorderWidget,
            TaskSchedulerWidget,
            FileWatcherWidget,
            HotkeyManagerWidget,
            TextExpanderWidget,
            AutoClickerWidget,
            BatchRenameWidget,
            WorkflowBuilderWidget,
        )
        print("✓ 所有功能模块导入成功")
    except ImportError as e:
        print(f"✗ 功能模块导入失败: {e}")
        return False
    
    return True


def test_styles():
    """测试样式生成"""
    print("\n测试样式生成...")
    
    try:
        from app.styles import (
            get_stylesheet,
            get_card_style,
            get_title_label_style,
            get_description_label_style,
            get_accent_button_style,
            get_danger_button_style,
            get_success_button_style,
            get_secondary_button_style,
        )
        
        stylesheet = get_stylesheet()
        assert len(stylesheet) > 0
        print("✓ 主样式表生成成功")
        
        card_style = get_card_style()
        assert len(card_style) > 0
        print("✓ 卡片样式生成成功")
        
        button_style = get_accent_button_style()
        assert len(button_style) > 0
        print("✓ 按钮样式生成成功")
        
        return True
    except Exception as e:
        print(f"✗ 样式测试失败: {e}")
        return False


def test_widgets():
    """测试部件创建"""
    print("\n测试部件创建...")
    
    try:
        # 创建 QApplication 实例
        from PyQt6.QtWidgets import QApplication
        
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        from app.modules import (
            MacroRecorderWidget,
            TaskSchedulerWidget,
            FileWatcherWidget,
            HotkeyManagerWidget,
            TextExpanderWidget,
            AutoClickerWidget,
            BatchRenameWidget,
            WorkflowBuilderWidget,
        )
        
        widgets = [
            ("MacroRecorderWidget", MacroRecorderWidget),
            ("TaskSchedulerWidget", TaskSchedulerWidget),
            ("FileWatcherWidget", FileWatcherWidget),
            ("HotkeyManagerWidget", HotkeyManagerWidget),
            ("TextExpanderWidget", TextExpanderWidget),
            ("AutoClickerWidget", AutoClickerWidget),
            ("BatchRenameWidget", BatchRenameWidget),
            ("WorkflowBuilderWidget", WorkflowBuilderWidget),
        ]
        
        for name, widget_class in widgets:
            try:
                widget = widget_class()
                print(f"✓ {name} 创建成功")
            except Exception as e:
                print(f"✗ {name} 创建失败: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 部件测试失败: {e}")
        return False


def test_main_window():
    """测试主窗口创建"""
    print("\n测试主窗口创建...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        from app.main_window import MainWindow
        
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 测试窗口属性
        assert window.windowTitle() == "AutomationTool - 专业桌面自动化工具"
        print("✓ 窗口标题正确")
        
        assert window.minimumSize().width() >= 1200
        assert window.minimumSize().height() >= 800
        print("✓ 窗口尺寸正确")
        
        return True
    except Exception as e:
        print(f"✗ 主窗口测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("AutomationTool 测试套件")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("样式生成", test_styles()))
    results.append(("部件创建", test_widgets()))
    results.append(("主窗口创建", test_main_window()))
    
    # 打印结果摘要
    print("\n" + "=" * 50)
    print("测试结果摘要")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 所有测试通过！应用程序可以正常运行。")
        return 0
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
