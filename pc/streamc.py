# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Skriv GPS-forskyvinga (xyz) frå Geoscan inn i OneVision sitt vogneoppsett, Stream C.xml.

OneVision har ingen stad i programmet der GPS-forskyvinga kan endrast (Norman 8.11.2026). Ho står i
<GPS Type="0" xyz="x;y;z"/> i Stream C.xml ved OneVision.exe (Program Files). Tala er meter, med punktum:
  x = fram/bak frå enkodaren (origo i OneVision) – blir ikkje endra her
  y = sidevegs – same tal som spakarmen «høgre» i Geoscan, men FORTEIKNET i fila blir halde (ikkje stadfest
      kva veg OneVision reknar; det må testast med køyring fram og tilbake over eit kjent røyr)
  z = mastehøgda
Fila ligg under Program Files, så skriving krev ofte administratorløyve. Då blir den nye fila lagd i reserve/
og kopiert på plass med Windows sitt løyve-vindauge (UAC). Det blir alltid teke kopi av den gamle fila først.
"""
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import finn_utstyr as FU

HER = Path(__file__).resolve().parent
GPS_RE = re.compile(r'(<GPS\b[^>]*\bxyz=")([^"]*)(")')


def _tal(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if abs(v - round(v, 2)) < 1e-9 else f"{v:.3f}"


def forslag(cfg, ov):
    """xyz Geoscan meiner OneVision bør ha: x som før, y = |høgre| med forteiknet som står, z = mastehøgda."""
    s = (cfg or {}).get("spakarm") or {}
    hogre, mast = abs(float(s.get("hogre", 0) or 0)), float(s.get("opp", 0) or 0)
    x = ov.get("x", 0.0) if ov else 0.0
    y0 = ov.get("y", 0.0) if ov else 0.0
    y = -hogre if y0 < 0 else hogre
    return {"x": x, "y": y, "z": mast, "xyz": f"{_tal(x)};{_tal(y)};{_tal(mast)}"}


def status(cfg, stiar=None):
    ov = FU.les_onevision(stiar)
    if not ov:
        return {"funne": False, "melding": "Fann ikkje Stream C.xml ved OneVision (Program Files\\IDSGeoRadar\\OneVision)."}
    fs = forslag(cfg, ov)
    ulik = "x" not in ov or abs(ov["y"] - fs["y"]) > 0.005 or abs(ov["z"] - fs["z"]) > 0.005 or ov.get("komma_feil")
    return {"funne": True, "fil": ov["fil"], "xyz": ov["xyz"], "noverande": {k: ov.get(k) for k in "xyz"},
            "forslag": fs, "ulik": bool(ulik)}


def ny_tekst(tekst, xyz):
    if not re.fullmatch(r"-?\d+(\.\d+)?;-?\d+(\.\d+)?;-?\d+(\.\d+)?", xyz):
        raise ValueError(f"ugyldig xyz: {xyz} (skal vere tre tal med punktum, skilde med semikolon)")
    ny, n = GPS_RE.subn(lambda m: m.group(1) + xyz + m.group(3), tekst, count=1)
    if n != 1:
        raise ValueError("fann ikkje <GPS … xyz=\"…\"> i Stream C.xml")
    return ny


def _onevision_koyrer():
    if sys.platform != "win32":
        return False
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq OneVision.exe"], capture_output=True, text=True, timeout=5)
        return "OneVision.exe" in r.stdout
    except Exception:
        return False


def skriv(cfg, xyz=None, stiar=None, admin=None, reserve=None):
    """Skriv xyz (standard: forslaget frå Geoscan). Returnerer kva som vart gjort."""
    st = status(cfg, stiar)
    if not st["funne"]:
        raise RuntimeError(st["melding"])
    xyz = xyz or st["forslag"]["xyz"]
    fil = Path(st["fil"])
    raw = fil.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    tekst = raw.decode("utf-8-sig", errors="strict")
    ny = ny_tekst(tekst, xyz)
    ny_b = (b"\xef\xbb\xbf" if bom else b"") + ny.encode("utf-8")
    ts = time.strftime("%Y%m%d_%H%M%S")
    res = Path(reserve) if reserve else HER / "reserve"
    res.mkdir(exist_ok=True)
    kopi = res / f"Stream C_{ts}.xml"            # kopi av originalen hos oss, same kva som skjer
    kopi.write_bytes(raw)
    ut = {"fil": str(fil), "for": st["xyz"], "etter": xyz, "kopi": str(kopi), "admin": False,
          "onevision_koyrer": _onevision_koyrer()}
    try:
        shutil.copy2(fil, fil.with_name(f"Stream C.xml.bak_{ts}"))
        fil.write_bytes(ny_b)
    except PermissionError:
        if sys.platform != "win32" and admin is None:
            raise
        tmp = res / f"Stream C_ny_{ts}.xml"
        tmp.write_bytes(ny_b)
        (admin or _admin_kopier)(tmp, fil, ts)
        ut["admin"] = True
    if (FU.les_onevision([fil]) or {}).get("xyz") != xyz:
        raise RuntimeError("Stream C.xml vart ikkje endra (sa du nei til løyve-vindauget?)")
    return ut


def _admin_kopier(tmp, fil, ts):
    """Kopier som administrator (Windows spør om løyve). Tek kopi av originalen i same mappe først.
    Kommandoane står i eit lite skript i reserve/, så det blir ingen problem med hermeteikn i stiane."""
    q = lambda p: str(p).replace("'", "''")
    bak = fil.with_name(f"Stream C.xml.bak_{ts}")
    skript = tmp.with_suffix(".ps1")
    skript.write_text(f"Copy-Item -LiteralPath '{q(fil)}' -Destination '{q(bak)}' -Force\r\n"
                      f"Copy-Item -LiteralPath '{q(tmp)}' -Destination '{q(fil)}' -Force\r\n", encoding="utf-8-sig")
    ps = (f"$p = Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','{q(skript)}' "
          f"-Verb RunAs -Wait -PassThru -WindowStyle Hidden; exit $p.ExitCode")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError("kopieringa som administrator feila: " + (r.stderr or r.stdout).strip()[:300])
