# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Finn ut om com0com (virtuell kabel mellom Geoscan og OneVision) er installert, og kva portpar som finst.

Geoscan skriv på den eine enden av eit par (til dømes COM34), og OneVision les den andre (COM24). Ein COM-port kan
berre vere open i eitt program, så utan com0com (eller ein fysisk nullmodemkabel) kan ikkje OneVision få retta
posisjon i sanntid.

Tre kjelder, så det fungerer same korleis com0com er sett opp:
  1. Portlista frå Windows (pyserial). com0com-portar har maskinvare-ID «COM0COM\\PORT\\CNCA0» / «CNCB0».
  2. «setupc.exe list» i installasjonsmappa (gir òg namn på portar utanfor Ports-klassen og om EmuBR er på).
  3. Registeret: tenesta «com0com» finst når drivaren er installert, sjølv om det ikkje er laga noko par.
Endane heiter CNCA<n> og CNCB<n>; same n = same par.
"""
import os
import re
import subprocess
from pathlib import Path

NEDLASTING = "https://sourceforge.net/projects/com0com/files/com0com/2.2.2.0/"
RETTLEIING = ("https://github.com/Snowman6230/snowman-3d-scanner/blob/main/docs/BRUKARRETTLEIING.md"
              "#com0com--virtuell-kabel-mellom-geoscan-og-onevision")
_ENDE = re.compile(r"CNC([AB])(\d+)", re.I)


def par_fra_portar(portar):
    """portar: [(device, description, hwid)] → {n: {"A": "COM34", "B": "COM24"}} for com0com-portane."""
    par = {}
    for dev, desc, hwid in portar:
        tekst = f"{hwid or ''} {desc or ''}"
        if "com0com" not in tekst.lower() and not _ENDE.search(hwid or ""):
            continue
        m = _ENDE.search(hwid or "") or _ENDE.search(desc or "")
        if m:
            par.setdefault(int(m.group(2)), {})[m.group(1).upper()] = dev
    return par


def les_setupc(tekst):
    """Tolkar «setupc list»: «       CNCA0 PortName=COM34,EmuBR=yes» → ({n: {"A": "COM34"}}, {n: True om EmuBR})."""
    par, emubr = {}, {}
    for line in (tekst or "").splitlines():
        m = re.match(r"\s*CNC([AB])(\d+)\s+(.*)", line, re.I)
        if not m:
            continue
        n, ende, param = int(m.group(2)), m.group(1).upper(), m.group(3)
        pn = re.search(r"PortName=([^,\s]+)", param, re.I)
        namn = pn.group(1) if pn and pn.group(1) != "-" else f"CNC{ende}{n}"
        if namn.upper() == "COM#":       # «COM#» = Windows vel nummer sjølv; det verkelege namnet står i portlista
            namn = f"CNC{ende}{n}"
        par.setdefault(n, {})[ende] = namn
        if re.search(r"EmuBR=yes", param, re.I):
            emubr[n] = True
    return par, emubr


def _setupc():
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), r"C:\Program Files (x86)",
                 r"C:\Program Files"):
        if base and (Path(base) / "com0com" / "setupc.exe").is_file():
            return Path(base) / "com0com" / "setupc.exe"
    return None


def _teneste_finst():
    try:
        import winreg
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\com0com"))
        return True
    except Exception:
        return False


def par_fra_serialcomm(verdiar):
    """HARDWARE\\DEVICEMAP\\SERIALCOMM: {"\\Device\\com0com10": "COM44", "\\Device\\com0com20": "COM45"}.
    com0com-einingane heiter com0com1<n> (A-enden, CNCA<n>) og com0com2<n> (B-enden, CNCB<n>)."""
    par = {}
    for namn, port in (verdiar or {}).items():
        m = re.search(r"com0com([12])(\d+)$", str(namn), re.I)
        if m and port:
            par.setdefault(int(m.group(2)), {})["A" if m.group(1) == "1" else "B"] = str(port)
    return par


def _serialcomm():
    """Aktive serieportar frå registeret. Treng ikkje administrator, og tek med com0com-portar som ikkje ligg i
    Ports-klassen (då viser ikkje pyserial dei)."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
        ut, i = {}, 0
        while True:
            try:
                n, v, _ = winreg.EnumValue(k, i)
            except OSError:
                break
            ut[n] = v
            i += 1
        winreg.CloseKey(k)
        return ut
    except Exception:
        return {}


def _enum_par():
    """Fallback: SYSTEM\\CurrentControlSet\\Enum\\COM0COM\\PORT\\CNCA0\\Device Parameters\\PortName."""
    par = {}
    try:
        import winreg
        rot = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\COM0COM\PORT")
        i = 0
        while True:
            try:
                inst = winreg.EnumKey(rot, i)
            except OSError:
                break
            i += 1
            m = _ENDE.search(inst)
            if not m:
                continue
            try:
                k = winreg.OpenKey(rot, inst + r"\Device Parameters")
                namn, _ = winreg.QueryValueEx(k, "PortName")
                winreg.CloseKey(k)
            except OSError:
                continue
            if namn and namn != "-":
                par.setdefault(int(m.group(2)), {})[m.group(1).upper()] = namn
        winreg.CloseKey(rot)
    except Exception:
        pass
    return par


def _portar():
    try:
        from serial.tools import list_ports
        return [(p.device, p.description, p.hwid) for p in list_ports.comports()]
    except Exception:
        return []


def status(cfg=None, portar=None, setupc_tekst=None, windows=None, teneste=None, register=None):
    """Kva statussida treng: installert, para, kva ende Geoscan og OneVision bør bruke, og åtvaringar.
    Argumenta etter cfg er berre for testar."""
    cfg = cfg or {}
    windows = (os.name == "nt") if windows is None else windows
    ut = (cfg.get("ut_seriell") or [{}])[0].get("port", "") if cfg.get("ut_seriell") else ""
    if not windows:
        return {"stotta": False, "installert": None, "par": [], "onevision_port": ut,
                "nedlasting": NEDLASTING, "rettleiing": RETTLEIING}
    par = par_fra_portar(_portar() if portar is None else portar)
    # Registeret (SERIALCOMM og Enum) finn com0com-portar som pyserial ikkje viser (utan «use Ports class»).
    reg = register if register is not None else [par_fra_serialcomm(_serialcomm()), _enum_par()]
    for kjelde in reg:
        for n, ender in kjelde.items():
            for e, namn in ender.items():
                par.setdefault(n, {}).setdefault(e, namn)
    emubr = {}
    if setupc_tekst is None:
        exe = _setupc()
        if exe:
            try:
                r = subprocess.run([str(exe), "list"], cwd=str(exe.parent), capture_output=True, text=True,
                                   timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                setupc_tekst = r.stdout
            except Exception:
                setupc_tekst = ""
    sp, emubr = les_setupc(setupc_tekst or "")
    for n, ender in sp.items():          # portlista vinn: der står det verkelege COM-namnet
        for e, namn in ender.items():
            par.setdefault(n, {}).setdefault(e, namn)
    teneste = _teneste_finst() if teneste is None else teneste
    installert = bool(par) or teneste or bool(setupc_tekst)
    liste = [{"n": n, "geoscan": p.get("A", ""), "onevision": p.get("B", ""), "emubr": bool(emubr.get(n))}
             for n, p in sorted(par.items())]
    atv = []
    alle = {x for p in liste for x in (p["geoscan"], p["onevision"]) if x}
    if installert and not liste:
        atv.append("com0com er installert, men det finst ikkje noko portpar. Opne «Setup for com0com» og lag eitt.")
    if ut and liste and ut not in alle:
        atv.append(f"«Til OneVision» er {ut}, men det er ikkje ein com0com-port. Vel den eine enden av eit par.")
    for p in liste:
        if p["emubr"]:
            atv.append(f"«emulate baud rate» er på for paret {p['geoscan']} ↔ {p['onevision']}. Slå det av, "
                       "elles kan OneVision få posisjonane for seint.")
    forslag = None
    if liste:
        bruk = next((p for p in liste if ut in (p["geoscan"], p["onevision"])), liste[0])
        g, o = bruk["geoscan"], bruk["onevision"]
        if ut == o:                      # brukaren har valt B-enden til Geoscan – då les OneVision A-enden
            g, o = o, g
        forslag = {"geoscan": g, "onevision": o}
    return {"stotta": True, "installert": installert, "par": liste, "forslag": forslag, "onevision_port": ut,
            "atvaringar": atv, "nedlasting": NEDLASTING, "rettleiing": RETTLEIING}


def ledig_par(brukte, onske=(("COM34", "COM24"), ("COM35", "COM25"), ("COM36", "COM26"), ("COM44", "COM45"))):
    """Første par der ingen av endane er i bruk. brukte: COM-namn som finst frå før."""
    b = {x.upper() for x in brukte}
    for a, c in onske:
        if a not in b and c not in b:
            return a, c
    n = 50
    while f"COM{n}" in b or f"COM{n + 1}" in b:
        n += 2
    return f"COM{n}", f"COM{n + 1}"


def lag_par_kommando(setupc, a, b):
    """PowerShell-kommando som køyrer «setupc install PortName=A PortName=B» som administrator.
    Windows spør om løyve (UAC). setupc må køyrast frå si eiga mappe (der .inf-fila ligg)."""
    for x in (a, b):
        if not re.fullmatch(r"COM\d{1,3}", x):
            raise ValueError(f"ugyldig portnamn: {x}")
    exe = str(setupc).replace("'", "''")
    import ntpath
    mappe = ntpath.dirname(str(setupc)).replace("'", "''")        # Windows-sti, òg når testane køyrer på Linux
    ps = (f"$p = Start-Process -FilePath '{exe}' -ArgumentList 'install PortName={a} PortName={b}' "
          f"-WorkingDirectory '{mappe}' -Verb RunAs -Wait -PassThru; exit $p.ExitCode")
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps]


def comdb_brukte(data):
    """Tolkar ComDB-bitmappa frå registeret: bit n-1 sett = COMn reservert («in use» i COM port database).
    Windows hugsar namn etter utstyr som er fjerna. Brukar vi eit slikt namn, spør com0com om lov (dialog)."""
    ut = set()
    for i, byte in enumerate(data or b""):
        for j in range(8):
            if byte & (1 << j):
                ut.add(f"COM{i * 8 + j + 1}")
    return ut


def _comdb():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\COM Name Arbiter")
        data, _ = winreg.QueryValueEx(k, "ComDB")
        winreg.CloseKey(k)
        return comdb_brukte(data)
    except Exception:
        return set()


def lag_par(a=None, b=None):
    """Lagar eit com0com-par (Windows spør om administratorløyve). Gir (a, b) tilbake, eller kastar RuntimeError."""
    if os.name != "nt":
        raise RuntimeError("berre på Windows")
    exe = _setupc()
    if not exe:
        raise RuntimeError("fann ikkje setupc.exe – er com0com installert? (venta i Program Files\\com0com)")
    if not (a and b):
        a, b = ledig_par([p[0] for p in _portar()] + list(_serialcomm().values()) + sorted(_comdb()))
    try:
        r = subprocess.run(lag_par_kommando(exe, a, b), capture_output=True, text=True, timeout=180,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise RuntimeError("Windows-dialogen vart ikkje svara på innan 3 minutt")
    if r.returncode != 0:
        raise RuntimeError("paret vart ikkje laga (sa du nei i Windows-dialogen?) " + (r.stderr or "").strip()[:200])
    return a, b
