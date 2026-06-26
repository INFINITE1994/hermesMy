@echo off
echo Building ImageBatch...
cd /d "%~dp0ImageBatch"
pyinstaller --noconfirm --onefile --windowed --name ImageBatch --clean main.py
echo Done.
pause
