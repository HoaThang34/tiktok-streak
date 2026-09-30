@echo off
chcp 65001 >nul
title TikTok Streak Manager
echo Đang khởi chạy TikTok Streak Manager...
python app.py
if errorlevel 1 (
    echo.
    echo [LỖI] Không thể chạy app.py. Vui lòng kiểm tra lại Python hoặc thư viện!
    pause
)
