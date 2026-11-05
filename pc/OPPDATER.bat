@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata v/Hans Petter B. Sorensen
cd /d "%~dp0"
python oppdater.py
pause
