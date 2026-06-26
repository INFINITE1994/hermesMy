@echo off
echo Building FileOrganizer...
cd /d "%~dp0FileOrganizer"
pyinstaller --noconfirm --onefile --windowed --name FileOrganizer --clean main.py
echo Done.
pause
