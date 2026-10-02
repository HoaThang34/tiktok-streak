@echo off
chcp 65001 >nul
title TikTok Streak Manager
cd /d "%~dp0"

echo ========================================================
echo            TIKTOK STREAK MANAGER (PORTABLE)
echo ========================================================
echo.

if exist "%~dp0python_embed\python.exe" (
    echo [*] Đang khởi chạy với Python Portable...
    "%~dp0python_embed\python.exe" app.py
) else (
    echo [*] Đang khởi chạy với Python hệ thống...
    python app.py
)

if errorlevel 1 (
    echo.
    echo [LỖI] Không thể khởi chạy ứng dụng!
    echo Vui lòng kiểm tra lại Google Chrome hoặc file log.
    pause
)
