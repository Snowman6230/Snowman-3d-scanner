# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Resultat etter skanninga: loggøktene (spor med helling) og retting av eksportfiler frå GRED HD / OneVision.
Brukt av Resultat-fana i nettlesaren (webtenar.py). Alt blir rekna lokalt på PC-en.

    økter()                      → oversikt over loggfilene (tid, punkt, helling)
    spor(fil)                    → sporet til kartet: [lat, lon, helling°, retta?]
    rett_eksport(fil, …)         → objekta før og etter retting (lat/lon til kartet) og filer til nedlasting:
                                   <namn>_retta.geojson, .csv og .dxf i pc/resultat/
"""
import copy
import csv
import io
import json
import math
import time
from pathlib import Path

import koordinat as K
import korriger_objekt as KO
import svy_objekt as SVY
import opphav

HER = Path(__file__).resolve().parent


def _rows(path):
    try:
        head, rows, _ = KO.read_csv(path)
    except Exception:
        return
    if "korrigert" not in head:
        return
    ix = {h: i for i, h in enumerate(head)}
    for r in rows:
        if len(r) >= len(head):
            yield ix, r


def okter(loggdir):
    """Éi linje per loggfil (geoscan_*.csv), nyaste først."""
    out = []
    for p in sorted(Path(loggdir).glob("geoscan_*.csv"), reverse=True):
        n = nk = over3 = 0
        maxt, t0, t1 = 0.0, None, None
        for ix, r in _rows(p):
            n += 1
            t0 = t0 or r[ix["tid"]]
            t1 = r[ix["tid"]]
            if r[ix["korrigert"]] == "1":
                nk += 1
                tilt = math.hypot(KO.num(r[ix["stamp"]]) or 0, KO.num(r[ix["krenging"]]) or 0)
                maxt = max(maxt, tilt)
                over3 += tilt > 3
        out.append({"fil": p.name, "start": t0, "slutt": t1, "punkt": n, "med_helling": nk,
                    "maks_helling": round(maxt, 1), "over_3_prosent": round(100 * over3 / nk, 1) if nk else 0,
                    "storleik_kb": round(p.stat().st_size / 1024)})
    return out


def spor(path, maks=6000):
    """Sporet frå ei loggfil til kartet, tynna ut til maks punkt: [lat, lon, helling (grader), 1/0 retta]."""
    pts = []
    for ix, r in _rows(path):
        lat, lon = KO.num(r[ix["lat_ut"]]), KO.num(r[ix["lon_ut"]])
        if lat is None or lon is None:
            continue
        k = r[ix["korrigert"]] == "1"
        tilt = math.hypot(KO.num(r[ix["stamp"]]) or 0, KO.num(r[ix["krenging"]]) or 0) if k else 0.0
        pts.append([round(lat, 8), round(lon, 8), round(tilt, 1), 1 if k else 0])
    step = max(1, len(pts) // maks)
    return pts[::step]


# ---------- innlesing av eksport ----------
def les_objekt(path):
    """GeoJSON direkte, OneVision .svy (objekta i <Targets>), eller CSV (austing/nording/djupn) gjort om til GeoJSON-punkt med alle kolonnane som eigenskapar."""
    path = Path(path)
    if path.suffix.lower() in (".geojson", ".json"):
        return json.loads(path.read_text(encoding="utf-8-sig"))
    if path.suffix.lower() == ".svy":          # OneVision-målefil: objekta ligg i <Targets>
        return SVY.svy_til_geojson(path)
    head, rows, _ = KO.read_csv(path)
    ce, cn, cd = (KO.find_col(head, k) for k in "END")
    if None in (ce, cn, cd):
        raise ValueError(f"fann ikkje kolonnane austing/nording/djupn. Overskrift: {head}")
    feats = []
    for r in rows:
        if len(r) <= max(ce, cn, cd):
            continue
        E, N, d = KO.num(r[ce]), KO.num(r[cn]), KO.num(r[cd])
        if None in (E, N, d):
            continue
        feats.append({"type": "Feature", "properties": dict(zip(head, r)),
                      "geometry": {"type": "Point", "coordinates": [E, N, d]}})
    return {"type": "FeatureCollection", "features": feats}


def _to_latlon(gj, zone):
    """Kopi av geometrien i lat/lon (til kartet). Utan sone: None."""
    if not zone:
        return None
    g = copy.deepcopy(gj)
    for f in g.get("features", []):
        pts = list(KO._points((f.get("geometry") or {}).get("coordinates")))
        pr = f.setdefault("properties", {})
        pr["utm_e"], pr["utm_n"] = [round(p[0], 3) for p in pts], [round(p[1], 3) for p in pts]   # til koordinatvisinga
        for p in KO._points((f.get("geometry") or {}).get("coordinates")):
            lat, lon = K.utm_inverse(p[0], p[1], zone)
            p[0], p[1] = round(lon, 8), round(lat, 8)
    return g


# ---------- utfiler ----------
def skriv_csv(gj, path):
    """Alle punkt, eitt per line: objekt-id, lag, E, N, z, djupn før/etter og flytting.
    Semikolon og desimalkomma, så fila opnar rett i norsk Excel. UTF-8 med BOM, elles les Excel æøå og – feil."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([f"{opphav.NAMN} – {opphav.PRODUSENT}", time.strftime("%d.%m.%Y %H:%M"), opphav.SIGNATUR])
        w.writerow(["objekt", "lag", "type", "punkt", "E", "N", "z", "djupn_for_m", "djupn_retta_m", "flytta_cm",
                    "hoegd_nn2000_m", "bakke_nn2000_m"])
        for i, ft in enumerate(gj.get("features", [])):
            pr = ft.get("properties") or {}
            d0, d1, fl, ho, hb = (pr.get(k) or [] for k in ("djupn_for_m", "djupn_retta_m", "flytta_cm",
                                                             "hoegd_nn2000_m", "bakke_nn2000_m"))
            g = lambda a, j: "" if j >= len(a) or a[j] is None else str(a[j]).replace(".", ",")
            for j, p in enumerate(KO._points((ft.get("geometry") or {}).get("coordinates"))):
                w.writerow([pr.get("id", i + 1), pr.get("layer", ""), pr.get("type", ""), j + 1,
                            f"{p[0]:.3f}".replace(".", ","), f"{p[1]:.3f}".replace(".", ","),
                            "" if len(p) < 3 else f"{p[2]:.3f}".replace(".", ","), g(d0, j), g(d1, j), g(fl, j),
                            g(ho, j), g(hb, j)])


def _lines(c, depth=0):
    """Linjer (lister av punkt) i ein geometri – Point blir ei «linje» med eitt punkt."""
    if c and isinstance(c[0], (int, float)):
        return [[c]]
    if c and c[0] and isinstance(c[0][0], (int, float)):
        return [c]
    out = []
    for x in c or []:
        out += _lines(x, depth + 1)
    return out


def skriv_dxf(gj, path):
    """Enkel DXF (R12, Windows-1252) som AutoCAD, Civil 3D, Gemini og GIS-program les: 3D-polylinjer og punkt,
    eitt lag per «layer» i eksporten. z er det same som i fila (djupn eller høgd). Djupna etter retting står
    som tekst ved kvart punkt på laget <lag>_DJUPN."""
    def layer(pr):
        s = str(pr.get("layer") or "GEOSCAN")
        return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in s)[:31] or "GEOSCAN"

    o = ["999", opphav.generator(), "999", opphav.COPYRIGHT, "0", "SECTION", "2", "ENTITIES"]
    # tittelfelt (laget SNOWMAN_GEOSCAN) nede til venstre for teikninga
    xs = [p[0] for ft in gj.get("features", []) for ln in _lines((ft.get("geometry") or {}).get("coordinates")) for p in ln]
    ys = [p[1] for ft in gj.get("features", []) for ln in _lines((ft.get("geometry") or {}).get("coordinates")) for p in ln]
    if xs:
        x0, y0 = min(xs), min(ys) - 1.5
        for k, (t, h) in enumerate(((opphav.NAMN, 0.5), (opphav.PRODUSENT, 0.3),
                                    (f"Retta for helling {time.strftime('%d.%m.%Y')} · {opphav.SIGNATUR}", 0.2))):
            o += ["0", "TEXT", "8", "SNOWMAN_GEOSCAN", "10", f"{x0:.3f}", "20", f"{y0 - k * 0.7:.3f}", "30", "0.0",
                  "40", f"{h:.2f}", "1", t]
    for ft in gj.get("features", []):
        lay = layer(ft.get("properties") or {})
        for ln in _lines((ft.get("geometry") or {}).get("coordinates")):
            if len(ln) == 1:
                p = ln[0]
                o += ["0", "POINT", "8", lay, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}", "30", f"{(p[2] if len(p) > 2 else 0):.3f}"]
                continue
            o += ["0", "POLYLINE", "8", lay, "66", "1", "70", "8", "10", "0.0", "20", "0.0", "30", "0.0"]
            for p in ln:
                o += ["0", "VERTEX", "8", lay, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}",
                      "30", f"{(p[2] if len(p) > 2 else 0):.3f}", "70", "32"]
            o += ["0", "SEQEND", "8", lay]
        # djupna som tekst ved punkta (eige lag <lag>_DJUPN), så ho kan lesast rett på teikninga
        d1 = (ft.get("properties") or {}).get("djupn_retta_m") or []
        pts = [p for ln in _lines((ft.get("geometry") or {}).get("coordinates")) for p in ln]
        for j, p in enumerate(pts):
            if j < len(d1) and d1[j] is not None:
                o += ["0", "TEXT", "8", (lay + "_DJUPN")[:31], "10", f"{p[0] + 0.15:.3f}", "20", f"{p[1] + 0.15:.3f}",
                      "30", "0.0", "40", "0.20", "1", f"{d1[j]:.2f} m".replace(".", ",")]
    o += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(o) + "\n", encoding="cp1252", errors="replace")   # DXF R12: ANSI_1252 (æøå)


# ---------- retting ----------
def rett_eksport(objektfil, loggfiler, utdir, zmode="auto", sone=None, maks_avstand=1.0):
    """Rett ei eksportfil mot loggane. Returnerer det kartet og tabellen treng, og skriv utfilene."""
    gj = les_objekt(objektfil)
    zone = sone or KO.geojson_zone(gj)
    logg = KO.Logg(loggfiler, zone)
    if not logg.rows:
        raise ValueError("loggane har ingen posisjonar med helling. Var hellinga tilgjengeleg under skanninga? "
                         "(Med berre R12i blir masta retta, men djupna krev ein ekstra IMU på ramma.)")
    zone = zone or logg.rows[0]["sone"]
    orig = copy.deepcopy(gj)
    ok, miss, zmode = KO.correct_geojson(gj, logg, zmode, maks_avstand)
    gj.setdefault("properties", {})
    gj["snowman_geoscan"] = {"generator": opphav.generator(), "produsent": opphav.PRODUSENT,
                             "retta": time.strftime("%Y-%m-%d %H:%M:%S"), "z": zmode, "utm_sone": zone,
                             "loggar": [Path(p).name for p in loggfiler]}
    utdir = Path(utdir)
    utdir.mkdir(parents=True, exist_ok=True)
    stem = Path(objektfil).stem
    # opplasta filer har tidsstempel framfor namnet – ta det bort i utfilene
    if stem[:8].isdigit() and stem.count("_") >= 3:      # <dato>_<tid>_<type>_<namn>
        stem = stem.split("_", 3)[-1]
    filer = {"geojson": f"{stem}_retta.geojson", "csv": f"{stem}_retta.csv", "dxf": f"{stem}_retta.dxf"}
    (utdir / filer["geojson"]).write_text(json.dumps(gj, ensure_ascii=False, indent=1), encoding="utf-8")
    skriv_csv(gj, utdir / filer["csv"])
    skriv_dxf(gj, utdir / filer["dxf"])
    tabell = []
    for i, fr in enumerate(gj.get("features", []), 1):
        pr = fr.get("properties") or {}
        f0 = [x for x in pr.get("djupn_for_m") or [] if x is not None]
        f1 = [x for x in pr.get("djupn_retta_m") or [] if x is not None]
        st = lambda v: None if not v else {"min": round(min(v), 2), "maks": round(max(v), 2), "snitt": round(sum(v) / len(v), 2)}
        tabell.append({"nr": i, "id": pr.get("id", i), "lag": pr.get("layer", ""), "type": pr.get("type", ""),
                       "skildring": pr.get("description", ""), "retta": pr.get("helling_retta", ""),
                       "maks_endring_cm": pr.get("helling_maks_endring_cm", 0),
                       "djupn_for": st(f0), "djupn_etter": st(f1)})
    return {"retta_punkt": ok, "utan_logg": miss, "z": zmode, "sone": zone, "filer": filer, "tabell": tabell,
            "for": _to_latlon(orig, zone), "etter": _to_latlon(gj, zone)}
