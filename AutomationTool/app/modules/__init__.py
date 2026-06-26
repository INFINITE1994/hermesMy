"""
AutomationTool - 功能模块包
"""

from .macro_recorder import MacroRecorderWidget
from .task_scheduler import TaskSchedulerWidget
from .file_watcher import FileWatcherWidget
from .hotkey_manager import HotkeyManagerWidget
from .text_expander import TextExpanderWidget
from .auto_clicker import AutoClickerWidget
from .batch_rename import BatchRenameWidget
from .workflow_builder import WorkflowBuilderWidget

__all__ = [
    "MacroRecorderWidget",
    "TaskSchedulerWidget",
    "FileWatcherWidget",
    "HotkeyManagerWidget",
    "TextExpanderWidget",
    "AutoClickerWidget",
    "BatchRenameWidget",
    "WorkflowBuilderWidget",
]
