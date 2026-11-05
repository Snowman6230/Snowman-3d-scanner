@echo off
chcp 65001 >nul
cd /d "%~dp0"
:start
python geoscan.py
if %errorlevel%==3 goto start
pause
