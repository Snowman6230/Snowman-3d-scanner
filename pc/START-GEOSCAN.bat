@echo off
chcp 65001 >nul
title Snowman Geoscan - Alpindata HP Brunstad Sorensen
cd /d "%~dp0"
if not "%~1"=="min" (start "Snowman Geoscan" /min cmd /c ""%~f0" min" & exit /b)
set ARG=
:start
python geoscan.py %ARG%
if %errorlevel%==3 (set ARG=--omstart& goto start)
rem Avslutt-knappen gir kode 0: lukk vindauget. Ved feil blir vindauget ståande, så feilen kan lesast.
if %errorlevel%==0 exit /b 0
pause
