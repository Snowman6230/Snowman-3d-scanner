@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata HP Brunstad Sorensen
cd /d "%~dp0"
set ARG=
:start
python geoscan.py %ARG%
if %errorlevel%==3 (set ARG=--omstart& goto start)
pause
