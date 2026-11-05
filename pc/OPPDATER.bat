@echo off
chcp 65001 >nul
cd /d "%~dp0"
python oppdater.py
pause
