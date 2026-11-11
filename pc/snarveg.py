# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Snarvegane «Snowman Geoscan» og «Snowman Geoscan DEMO» på skrivebordet, med ikonet (0.9.22).

INSTALL.bat lagar snarvegane éin gong. 11.11.2026 hadde Norman mista ikonet. Frå 0.9.22 sjekkar Geoscan
snarvegane ved første start etter kvar oppdatering. Han lagar dei på nytt med ikonet i pc/ikon/geoscan.ico,
og ber Windows oppdatere ikon-mellomlageret (ie4uinit). Knappen «Lag snarvegar på nytt» under Innstillingar
gjer det same når som helst.
"""
import subprocess
import sys
from pathlib import Path

HER = Path(__file__).resolve().parent
SNARVEGAR = (("Snowman Geoscan", "START-GEOSCAN.bat"), ("Snowman Geoscan DEMO", "START-DEMO.bat"))


def _ps(s):
    return s.replace("'", "''")


def skript(pcdir=HER):
    """PowerShell som lagar snarvegane på skrivebordet (òg når skrivebordet ligg i OneDrive) og
    oppdaterer ikona i Windows."""
    ico = pcdir / "ikon" / "geoscan.ico"
    linjer = ["$ErrorActionPreference='Stop'",
              "$d=[Environment]::GetFolderPath('Desktop')",
              "$w=New-Object -ComObject WScript.Shell"]
    for namn, bat in SNARVEGAR:
        linjer += [f"$s=$w.CreateShortcut((Join-Path $d '{_ps(namn)}.lnk'))",
                   f"$s.TargetPath='{_ps(str(pcdir / bat))}'",
                   f"$s.WorkingDirectory='{_ps(str(pcdir))}'",
                   f"$s.IconLocation='{_ps(str(ico))},0'",
                   "$s.Description='Snowman Geoscan - Alpindata HP Brunstad Sorensen'",
                   "$s.Save()"]
    # Windows held på gamle ikon i eit mellomlager. ie4uinit -show ber Windows 10/11 lese dei på nytt.
    linjer.append("try { Start-Process -FilePath ie4uinit.exe -ArgumentList '-show' -WindowStyle Hidden } catch {}")
    return "; ".join(linjer)


def lag(pcdir=HER, versjon=None, tving=False, merke=None):
    """Lag snarvegane på nytt viss versjonen er ny sidan sist (eller tving=True).
    Returnerer (ok, melding). Gjer ingenting utanfor Windows."""
    if sys.platform != "win32":
        return False, "berre på Windows"
    merke = merke or (pcdir / "logg" / "snarveg.txt")
    if not tving and versjon and merke.is_file() and merke.read_text(encoding="utf-8").strip() == versjon:
        return True, "snarvegane er alt laga for denne versjonen"
    if not (pcdir / "ikon" / "geoscan.ico").is_file():
        return False, "fann ikkje ikon/geoscan.ico"
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", skript(pcdir)],
                           capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as e:
        return False, f"kunne ikkje lage snarvegar: {e}"
    if r.returncode != 0:
        return False, "kunne ikkje lage snarvegar: " + (r.stderr.strip() or r.stdout.strip())[:300]
    if versjon:
        merke.parent.mkdir(parents=True, exist_ok=True)
        merke.write_text(versjon, encoding="utf-8")
    return True, "Snarvegane «Snowman Geoscan» og «Snowman Geoscan DEMO» er laga på skrivebordet, med ikonet."
