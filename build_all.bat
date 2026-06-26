@echo off
echo ========================================
echo  Building All HermesMy Tools
echo ========================================
echo.

echo [1/5] Building CleanMaster...
cd /d "%~dp0CleanMaster"
pyinstaller --noconfirm --onefile --windowed --name CleanMaster --clean main.py 2>nul
if %errorlevel%==0 (echo    OK) else (echo    FAILED)

echo [2/5] Building PDFMaster...
cd /d "%~dp0PDFMaster"
pyinstaller --noconfirm --onefile --windowed --name PDFMaster --clean main.py 2>nul
if %errorlevel%==0 (echo    OK) else (echo    FAILED)

echo [3/5] Building ImageBatch...
cd /d "%~dp0ImageBatch"
pyinstaller --noconfirm --onefile --windowed --name ImageBatch --clean main.py 2>nul
if %errorlevel%==0 (echo    OK) else (echo    FAILED)

echo [4/5] Building FileOrganizer...
cd /d "%~dp0FileOrganizer"
pyinstaller --noconfirm --onefile --windowed --name FileOrganizer --clean main.py 2>nul
if %errorlevel%==0 (echo    OK) else (echo    FAILED)

echo [5/5] Building ToolBox...
cd /d "%~dp0ToolBox"
pyinstaller --noconfirm --onefile --windowed --name ToolBox --clean main.py 2>nul
if %errorlevel%==0 (echo    OK) else (echo    FAILED)

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Exe files are in each tool's dist\ folder.
echo.
pause
