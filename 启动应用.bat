@echo off
title Smart Outfit Color System
cd /d "%~dp0"
echo ================================================
echo   智能穿搭色彩系统  Smart Outfit Color System
echo   正在启动，浏览器将自动打开 http://localhost:8501
echo   （关闭本黑色窗口即可停止应用）
echo ================================================
py -m streamlit run app.py
pause
