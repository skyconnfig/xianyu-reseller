@echo off
REM 闲鱼转卖助手 2.0 - Windows 编译脚本

echo ==========================================
echo    闲鱼转卖助手 2.0 - 重新编译脚本
echo ==========================================
echo.

REM 检查 Python 版本
echo [1/5] 检查 Python 环境...
python --version 2>&1 | findstr /C:"3.13" >nul && (
    echo ✅ Python 3.13 已安装
) || (
    echo ❌ 错误：需要 Python 3.13+
    pause
    exit /b 1
)

REM 创建虚拟环境
echo.
echo [2/5] 创建虚拟环境...
if not exist "venv\" (
    python -m venv venv
    echo ✅ 虚拟环境已创建
) else (
    echo ✅ 虚拟环境已存在
)

REM 激活虚拟环境并安装依赖
echo.
echo [3/5] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt --quiet
echo ✅ 依赖已安装

REM 检查主程序文件
echo.
echo [4/5] 检查源码文件...
if not exist "main.py" (
    echo ❌ 错误：找不到 main.py
    echo    请先恢复源码（参考 main.py 框架）
    pause
    exit /b 1
)
echo ✅ 找到 main.py

REM 使用 PyInstaller 编译
echo.
echo [5/5] 开始编译...
echo    这可能需要几分钟，请稍候...

pyinstaller --onefile ^
           --windowed ^
           --name "咸鱼转卖助手2.0【鱼小铺版】" ^
           --icon "assets/icon.ico" ^
           --add-data "config;config" ^
           --hidden-import requests ^
           --hidden-import urllib3 ^
           --hidden-import imageio ^
           --hidden-import PIL ^
           --hidden-import asyncio ^
           --hidden-import concurrent.futures ^
           main.py

REM 检查编译结果
echo.
if exist "dist\咸鱼转卖助手2.0【鱼小铺版】.exe" (
    echo ✅ 编译成功！
    echo.
    echo 输出文件：
    dir dist\*.exe | findstr /C:".exe"
    echo.
    echo ==========================================
    echo    编译完成！文件在 dist\ 目录
    echo ==========================================
) else (
    echo ❌ 编译失败，请检查错误信息
    pause
    exit /b 1
)

pause
