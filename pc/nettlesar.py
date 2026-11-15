# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Opne statussida i eit eige appvindauge (0.9.28), og lukk det når Geoscan blir avslutta.

Ønske frå Norman 15.11.2026: Avslutt skal lukke både nettlesaren og cmd-vindauget. Ei nettside kan ikkje lukke ei
vanleg fane ho ikkje sjølv har opna, så Geoscan opnar sida i Edge eller Chrome i app-modus (`--app=`):
  - eit vanleg Windows-vindauge med knappane minimer/maksimer/lukk, eige ikon på oppgåvelinja, Alt+Tab
    (ikkje kioskmodus, som fyller skjermen og ikkje kan minimerast)
  - eiga, lita nettlesarprofil (`--user-data-dir`), så Avslutt lukkar berre dette vindauget og ingen andre
    Edge-/Chrome-vindauge
  - finst ikkje Edge eller Chrome, eller er valet «app_modus» slått av under Innstillingar: vanleg fane som før
"""
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

HER = Path(__file__).resolve().parent
_PROSESS = [None]


def profilmappe():
    """Nettlesarprofilen til Geoscan: %LOCALAPPDATA%\\SnowmanGeoscan\\nettlesar (elles pc/nettlesar)."""
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) / "SnowmanGeoscan" / "nettlesar") if base else (HER / "nettlesar")


def finn_nettlesar():
    """Sti til Edge eller Chrome (Edge først: finst alltid på Windows 10/11), eller None."""
    kandidatar = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        b = os.environ.get(env)
        if b:
            kandidatar += [Path(b) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                           Path(b) / "Google" / "Chrome" / "Application" / "chrome.exe"]
    for k in kandidatar:
        if k.is_file():
            return str(k)
    for namn in ("msedge", "microsoft-edge", "google-chrome", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(namn)
        if p:
            return p
    return None


def argument(exe, url, profil, ny_profil):
    """Kommandolina for appvindauget. Første gong: ein høveleg storleik (seinare hugsar nettlesaren han sjølv)."""
    a = [exe, f"--app={url}", f"--user-data-dir={profil}", "--no-first-run", "--no-default-browser-check",
         "--disable-features=msEdgeSidebarV2,msImplicitSignin,SigninInterceptBubble"]
    if ny_profil:
        a.append("--window-size=1500,950")
    return a


def opne(url, app_modus=True):
    """Opne statussida. Gir «app» når appvindauget vart opna, elles «fane»."""
    exe = finn_nettlesar() if app_modus else None
    if exe:
        profil = profilmappe()
        ny = not profil.exists()
        try:
            profil.mkdir(parents=True, exist_ok=True)
            flagg = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            _PROSESS[0] = subprocess.Popen(argument(exe, url, profil, ny), stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, creationflags=flagg)
            return "app"
        except Exception as e:
            print(f"Fekk ikkje opna appvindauget ({e}). Opnar i vanleg fane.", file=sys.stderr)
    webbrowser.open(url)
    return "fane"


def lukk():
    """Lukk appvindauget: prosessen Geoscan starta, og alle nettlesarprosessar med profilen til Geoscan
    (til dømes når vindauget var ope frå før, og den nye prosessen berre gav det vidare). Andre vindauge blir ikkje rørte."""
    p = _PROSESS[0]
    if p is not None and p.poll() is None:
        try:
            p.terminate()
        except Exception:
            pass
    if os.name == "nt":
        profil = str(profilmappe()).replace("'", "''")
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='msedge.exe' OR Name='chrome.exe'\" | "
              f"Where-Object {{ $_.CommandLine -like '*{profil}*' }} | "
              "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
