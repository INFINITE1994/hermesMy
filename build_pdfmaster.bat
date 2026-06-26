@echo off
echo Building PDFMaster...
cd /d "%~dp0PDFMaster"
pyinstaller --noconfirm --onefile --windowed --name PDFMaster --clean main.py
echo Done.
pause
