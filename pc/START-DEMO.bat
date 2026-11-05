@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata HP Brunstad Sorensen
cd /d "%~dp0"
if not "%~1"=="min" (start "Snowman Geoscan" /min cmd /c ""%~f0" min" & exit /b)
echo Snowman Geoscan DEMO - simulert mottakar og NTRIP-caster. Ikkje ekte malingar.
start "Geoscan simulator" /min python simuler.py --caster 2101
timeout /t 2 >nul
set ARG=
:start
python geoscan.py --config geoscan_config_demo.json %ARG%
set KODE=%errorlevel%
if %KODE%==3 (set ARG=--omstart& goto start)
rem Avslutta: stopp simulatoren, og lukk vindauget (kode 0). Ved feil blir vindauget ståande.
taskkill /fi "WINDOWTITLE eq Geoscan simulator*" /f >nul 2>&1
if %KODE%==0 exit /b 0
pause
