"""Quick smoke test for ProcessManager."""
import sys
import os

# Add current dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
import psutil
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter

print("[OK] All imports successful")
print(f"[OK] psutil version: {psutil.__version__}")

# Test psutil works
cpu = psutil.cpu_percent(interval=0.1)
mem = psutil.virtual_memory()
procs = list(psutil.process_iter())
print(f"[OK] CPU: {cpu}%, Memory: {mem.percent}%")
print(f"[OK] Found {len(procs)} running processes")

# Test Qt app creation (headless - no window shown)
os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QApplication(sys.argv)

# Import main module
from main import MainWindow, DARK_STYLESHEET, ProcessWorker, ResourceMonitorWidget, StatCard, ProcessDetailPanel

print("[OK] All classes imported from main.py")

# Test stylesheet applies
app.setStyleSheet(DARK_STYLESHEET)
print("[OK] Stylesheet applied successfully")

# Test window creation
window = MainWindow()
print("[OK] MainWindow created successfully")

# Verify window has expected components
assert hasattr(window, 'process_table'), "Missing process_table"
assert hasattr(window, 'process_tree'), "Missing process_tree"
assert hasattr(window, 'detail_panel'), "Missing detail_panel"
assert hasattr(window, 'cpu_chart'), "Missing cpu_chart"
assert hasattr(window, 'mem_chart'), "Missing mem_chart"
assert hasattr(window, 'service_table'), "Missing service_table"
assert hasattr(window, 'startup_table'), "Missing startup_table"
assert hasattr(window, 'top_table'), "Missing top_table"
assert hasattr(window, 'search_input'), "Missing search_input"
assert hasattr(window, 'tab_widget'), "Missing tab_widget"
print("[OK] All UI components verified")

# Test tab count
assert window.tab_widget.count() == 6, f"Expected 6 tabs, got {window.tab_widget.count()}"
print("[OK] 6 tabs present")

# Test stat cards
assert hasattr(window, 'cpu_card'), "Missing cpu_card"
assert hasattr(window, 'mem_card'), "Missing mem_card"
assert hasattr(window, 'process_count_card'), "Missing process_count_card"
assert hasattr(window, 'thread_count_card'), "Missing thread_count_card"
print("[OK] Dashboard stat cards present")

# Test charts
assert hasattr(window, 'big_cpu_chart'), "Missing big_cpu_chart"
assert hasattr(window, 'big_mem_chart'), "Missing big_mem_chart"
assert hasattr(window, 'process_cpu_chart'), "Missing process_cpu_chart"
print("[OK] Resource monitor charts present")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
