@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata v/Hans Petter B. Sorensen
cd /d "%~dp0"
:start
python geoscan.py
if %errorlevel%==3 goto start
pause
