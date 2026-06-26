@echo off
REM CryptoTools 启动脚本
REM 检查是否安装了依赖

echo ========================================
echo   CryptoTools - 加密工具箱
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 正在检查依赖...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo 依赖已就绪，正在启动CryptoTools...
echo.
python main.py

pause
