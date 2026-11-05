@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata v/Hans Petter B. Sorensen
cd /d "%~dp0"
echo Snowman Geoscan DEMO - simulert mottakar og NTRIP-caster. Ikkje ekte malingar.
start "Geoscan simulator" python simuler.py --caster 2101
timeout /t 2 >nul
set ARG=
:start
python geoscan.py --config geoscan_config_demo.json %ARG%
if %errorlevel%==3 (set ARG=--omstart& goto start)
pause
