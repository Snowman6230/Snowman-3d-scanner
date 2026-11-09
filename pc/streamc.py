# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Skriv GPS-forskyvinga (xyz) frå Geoscan inn i OneVision sitt vogneoppsett, Stream C.xml.

OneVision har ingen stad i programmet der GPS-forskyvinga kan endrast (Norman 8.11.2026). Ho står i
<GPS Type="0" xyz="x;y;z"/> i Stream C.xml ved OneVision.exe (Program Files). Tala er meter, med punktum:
  x = fram frå enkoderen (i venstre bakhjul, origo i OneVision) til spissen av stonga
  y = sidevegs til spissen. IDS-malen for GPS-støtta bak til venstre har +0,42 (Norman målte 42 cm 9.11.2026).
      Kva forteikn som er venstre, er ikkje stadfest – det må testast ved å køyre langs eit kjent røyr.
  z = høgda OneVision trekkjer frå GPS-høgda (sjå z_for): 0,09 når Geoscan sender spissen urørt (Access/IMU)
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
import helling as H

HER = Path(__file__).resolve().parent
GPS_RE = re.compile(r'(<GPS\b[^>]*\bxyz=")([^"]*)(")')


def _tal(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if abs(v - round(v, 2)) < 1e-9 else f"{v:.3f}"


def z_for(cfg):
    """Høgda OneVision skal trekkje frå GPS-høgda for å kome ned til bakken. Avheng av kva Geoscan sender:
    – «R12i med Trimble Access (IMU)»: spissen av stonga på ramma, urørt → z = spissen over bakken (0,09)
    – «rett antenne» elles: antenna → z = spissen over bakken + mast + 0,179
    – «referansepunkt»: bakken under radaren → z = 0"""
    cfg = cfg or {}
    spiss = float(cfg.get("spiss_over_bakken", 0.09) or 0.0)
    if cfg.get("gps_oppsett") == "access":
        return round(spiss, 3), "spissen av stonga over bakken (Geoscan sender spissen urørt)"
    if cfg.get("utgang") == "referansepunkt":
        return 0.0, "0 – Geoscan sender bakken under radaren"
    a = H.spakarm(cfg)[2]
    return round(spiss + a, 3), f"spissen over bakken {spiss:g} + mast og fasesenter {a:.3f} (Geoscan sender antenna)"


def forslag(cfg, ov=None):
    """xyz Geoscan meiner OneVision bør ha (0.9.21): x og y som målt (streamc_xy: x fram frå enkoderen i venstre
    bakhjul, y sidevegs – standard 0.13;0.42, same som IDS-malen for GPS-støtta bak til venstre), z frå z_for."""
    xy = (cfg or {}).get("streamc_xy") or [0.13, 0.42]
    x, y = float(xy[0]), float(xy[1])
    z, kvifor = z_for(cfg)
    return {"x": x, "y": y, "z": z, "z_kvifor": kvifor, "xyz": f"{_tal(x)};{_tal(y)};{_tal(z)}"}


def virtualstore():
    """Windows legg ein skjult kopi i VirtualStore når eit gammalt program ikkje får skrive i Program Files.
    OneVision kan då lese kopien i staden for den verkelege fila."""
    import os
    la = os.environ.get("LOCALAPPDATA")
    if not la:
        return None
    stiar = [Path(la) / "VirtualStore" / pf / "IDSGeoRadar" / "OneVision" / under / "Stream C.xml"
             for pf in ("Program Files (x86)", "Program Files") for under in ("config", "")]
    return FU.les_onevision([s for s in stiar if s.is_file()]) if any(s.is_file() for s in stiar) else None


def brukt_sist(cfg):
    """xyz OneVision brukte i den nyaste målinga (kopien i Survey_…/Data/Stream C.xml)."""
    try:
        import onevision_filer as OVF
        for f in (OVF.finn(cfg, objekt_for=0).get("filer") or [])[:5]:
            if f.get("gps_xyz"):
                return {"namn": f.get("namn"), "xyz": f["gps_xyz"]}
    except Exception:
        pass
    return None


def _lik(a, b):
    return all(abs(float(a[i]) - float(b[i])) <= 0.005 for i in range(3))


def status(cfg, stiar=None, med_survey=True):
    fs = forslag(cfg)
    ov = FU.les_onevision(stiar)
    if not ov:
        return {"funne": False, "forslag": fs,
                "melding": "Fann ikkje Stream C.xml ved OneVision (Program Files\\IDSGeoRadar\\OneVision\\config)."}
    ulik = "x" not in ov or not _lik([ov["x"], ov["y"], ov["z"]], [fs["x"], fs["y"], fs["z"]]) or ov.get("komma_feil")
    ut = {"funne": True, "fil": ov["fil"], "xyz": ov["xyz"], "noverande": {k: ov.get(k) for k in "xyz"},
          "forslag": fs, "ulik": bool(ulik)}
    vs = virtualstore() if stiar is None else None
    if vs and "x" in vs:
        ut["virtualstore"] = {"fil": vs["fil"], "xyz": vs["xyz"],
                              "ulik": "x" not in ov or not _lik([vs["x"], vs["y"], vs["z"]], [ov["x"], ov["y"], ov["z"]])}
    if med_survey and stiar is None:
        b = brukt_sist(cfg)
        if b:
            b["ulik_fila"] = "x" in ov and not _lik(b["xyz"], [ov["x"], ov["y"], ov["z"]])
            ut["brukt_sist"] = b
    return ut


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
