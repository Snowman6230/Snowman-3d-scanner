# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Finn målefilene frå OneVision (Survey_ÅÅÅÅ.MM.DD_NNN … .svy) automatisk, nyaste først.

OneVision lagrar kvar måling i arbeidsmappa som er vald i «New Project» (hos Norman 8.11.2026:
E:/Dokumenter/OneVision/Projects/). Prosjektnamnet er Survey_<dato>_<nr>, og objekta ligg i .svy-fila.
Vi veit ikkje sikkert om .svy ligg rett i Projects eller i ei undermappe per måling, så vi leitar tre nivå ned.

Mapper som blir leita i (dei som finst):
  1. «onevision_mappe» i innstillingane, om ho er sett
  2. <Dokument>/OneVision/Projects og <Dokument>/OneVision for brukaren
  3. X:/Dokumenter/OneVision/Projects og X:/Documents/OneVision/Projects på alle stasjonar C–Z
"""
import os
import re
import string
import time
from pathlib import Path

NAMN_RE = re.compile(r"Survey_(\d{4})[.\-_](\d{2})[.\-_](\d{2})_(\d+)", re.I)
MAKS_DJUPN = 3          # mappenivå under rotmappa
MAKS_FILER = 200
_cache = {}             # sti -> (mtime, tal objekt)


def rotmapper(cfg=None):
    cfg = cfg or {}
    kand = []
    eiga = (cfg.get("onevision_mappe") or "").strip()
    if eiga:
        kand.append(Path(eiga))
    heim = Path(os.path.expanduser("~"))
    for dok in ("Documents", "Dokumenter", "Dokument"):
        kand += [heim / dok / "OneVision" / "Projects", heim / dok / "OneVision"]
    od = os.environ.get("OneDrive")
    if od:
        for dok in ("Documents", "Dokumenter"):
            kand.append(Path(od) / dok / "OneVision" / "Projects")
    if os.name == "nt":
        for b in string.ascii_uppercase[2:]:
            if not os.path.exists(f"{b}:\\"):
                continue
            for dok in ("Dokumenter", "Documents"):
                kand.append(Path(f"{b}:\\") / dok / "OneVision" / "Projects")
    ut, sett = [], set()
    for p in kand:
        try:
            if p.is_dir():
                k = str(p.resolve()).lower()
                if k not in sett:
                    sett.add(k)
                    ut.append(p)
        except OSError:
            pass
    return ut


def _leit(rot, djupn=0):
    try:
        with os.scandir(rot) as it:
            for e in it:
                try:
                    if e.is_file() and e.name.lower().endswith(".svy"):
                        yield Path(e.path)
                    elif e.is_dir() and djupn < MAKS_DJUPN and not e.name.startswith("."):
                        yield from _leit(e.path, djupn + 1)
                except OSError:
                    continue
    except OSError:
        return


def tal_objekt(sti):
    """Tal objekt i .svy (med mellomlager). None om fila ikkje kan lesast."""
    try:
        mt = sti.stat().st_mtime
        c = _cache.get(str(sti))
        if c and c[0] == mt:
            return c[1]
        import svy_objekt as SVY
        _, obj = SVY.les_svy(sti)
        _cache[str(sti)] = (mt, len(obj))
        return len(obj)
    except Exception:
        return None


def info(sti, med_objekt=False):
    st = sti.stat()
    m = NAMN_RE.search(sti.name) or NAMN_RE.search(sti.parent.name)
    dato = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
    d = {"sti": str(sti), "namn": sti.name, "mappe": str(sti.parent), "dato": dato,
         "nr": int(m.group(4)) if m else None, "endra": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
         "mtime": st.st_mtime, "kb": round(st.st_size / 1024)}
    if med_objekt:
        d["objekt"] = tal_objekt(sti)
    return d


def finn(cfg=None, objekt_for=10):
    """{'mapper': [...], 'filer': [...]} – nyaste måling først (dato i namnet, så nummer, så endringstid).
    Talet på objekt blir lese for dei `objekt_for` nyaste."""
    rotar = rotmapper(cfg)
    funne, sett = [], set()
    for r in rotar:
        for f in _leit(r):
            k = str(f).lower()
            if k in sett:
                continue
            sett.add(k)
            try:
                funne.append(info(f))
            except OSError:
                pass
            if len(funne) >= MAKS_FILER:
                break
    funne.sort(key=lambda d: (d["dato"] or "", d["nr"] or 0, d["mtime"]), reverse=True)
    for d in funne[:objekt_for]:
        d["objekt"] = tal_objekt(Path(d["sti"]))
    return {"mapper": [str(r) for r in rotar], "filer": funne}


def er_funnen(cfg, sti):
    """Sant berre for .svy-filer som finn() sjølv har funne (nettsida skal ikkje kunne lese vilkårlege filer)."""
    try:
        p = Path(sti).resolve()
    except OSError:
        return False
    if p.suffix.lower() != ".svy" or not p.is_file():
        return False
    for r in rotmapper(cfg):
        try:
            p.relative_to(r.resolve())
            return True
        except ValueError:
            continue
    return False
