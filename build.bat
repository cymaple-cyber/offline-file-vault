@echo off
chcp 65001 >nul
title 离线文件保险箱 - Windows 打包工具
echo ================================
echo   离线文件保险箱 Windows 打包
echo ================================
echo.
echo [1/3] 安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络或 Python 环境
    pause
    exit /b 1
)

echo [2/3] 打包为 EXE...
pyinstaller --windowed --name "离线文件保险箱" --add-data "src;src" --clean main.py
if %errorlevel% neq 0 (
    echo 打包失败
    pause
    exit /b 1
)

echo [3/3] 清理临时文件...
rmdir /s /q build 2>nul
del /q *.spec 2>nul

echo.
echo ================================
echo   打包完成！
echo   EXE 位置: dist\离线文件保险箱.exe
echo ================================
echo.
start "" "dist"
pause
