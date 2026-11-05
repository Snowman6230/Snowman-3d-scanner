@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo SNOWMAN Geoscan DEMO - simulert mottakar og NTRIP-caster. Ikkje ekte malingar.
start "Geoscan simulator" python simuler.py --caster 2101
timeout /t 2 >nul
start "" http://localhost:8088
python geoscan.py --config geoscan_config_demo.json
pause
