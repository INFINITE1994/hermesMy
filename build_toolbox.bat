@echo off
echo Building ToolBox...
cd /d "%~dp0ToolBox"
pyinstaller --noconfirm --onefile --windowed --name ToolBox --clean main.py
echo Done.
pause
