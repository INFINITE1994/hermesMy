@echo off
echo Building CleanMaster...
cd /d "%~dp0CleanMaster"
pyinstaller --noconfirm --onefile --windowed --name CleanMaster --clean main.py
echo Done.
pause
