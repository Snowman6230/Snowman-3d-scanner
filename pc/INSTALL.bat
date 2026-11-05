@echo off
chcp 65001 >nul
title Snowman Geoscan - installasjon
cd /d "%~dp0"
echo.
echo   Snowman Geoscan
echo   Alpindata HP Brunstad Sorensen
echo   ---------------------------------------
echo.
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 goto ingenpython
echo Installerer det programmet treng ...
python -m pip install --upgrade --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto pipfeil
echo.
echo Lagar snarvegar pa skrivebordet ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $w=New-Object -ComObject WScript.Shell; foreach($p in @(@('Snowman Geoscan','START-GEOSCAN.bat'),@('Snowman Geoscan DEMO','START-DEMO.bat'))){ $s=$w.CreateShortcut((Join-Path $d ($p[0]+'.lnk'))); $s.TargetPath=(Join-Path '%~dp0' $p[1]); $s.WorkingDirectory='%~dp0'; $s.IconLocation=(Join-Path '%~dp0' 'ikon\geoscan.ico'); $s.Description='Snowman Geoscan - Alpindata HP Brunstad Sorensen'; $s.Save() }"
echo.
echo Ferdig. Start med snarvegen "Snowman Geoscan" pa skrivebordet,
echo eller prov forst "Snowman Geoscan DEMO" (simulert, utan utstyr).
echo.
pause
exit /b 0

:ingenpython
echo Python manglar. Prover a installere Python 3.12 (krev internett) ...
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto manuell
echo.
echo Python er installert. LUKK dette vindauget og dobbeltklikk INSTALL.bat EIN GONG TIL.
pause
exit /b 0

:manuell
echo.
echo Fekk ikkje installert Python automatisk.
echo Last ned Python fra https://www.python.org/downloads/ og kryss av for
echo "Add python.exe to PATH" under installasjonen. Kjor sa INSTALL.bat pa nytt.
pause
exit /b 1

:pipfeil
echo.
echo Installasjonen feila. Sjekk at PC-en er pa internett, og prov igjen.
pause
exit /b 1
