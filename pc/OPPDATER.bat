@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata HP Brunstad Sorensen
cd /d "%~dp0"
python oppdater.py
pause
