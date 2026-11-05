# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Rett objekt frå georadaren (rør, kablar, holrom) for hellinga – djupnfeilen.

OneVision/GRED HD legg eit objekt loddrett under radaren. Når bakken hallar, ligg det eigentleg vinkelrett på
bakken, d·sin(helling) sidelengs mot oppsida. Dette skriptet les objekta (CSV med austing, nording og djupn i UTM)
og loggen frå geoscan.py (helling og kurs for kvar posisjon), og skriv ut retta koordinatar.

    python korriger_objekt.py --objekt ror.csv --logg logg/geoscan_20261106_090000.csv --ut ror_retta.csv

Objektfila: CSV (; , eller tab) med overskrift. Kolonnar blir funne på namn:
    austing: E, Aust, Austing, Easting, X     nording: N, Nord, Nording, Northing, Y
    djupn:   Djupn, Djupne, Dybde, Depth, D   (positiv nedover, meter)   valfri tid: Tid, Time
Alle andre kolonnar blir med uendra. UTM-sona kan setjast med --sone (elles same som loggen).

GeoJSON (eksport frå GRED HD/OneVision, Point/LineString o.l.) blir òg lese: [austing, nording, z], der z er djupn
(positiv nedover) eller høgd (NN2000). Sona blir lesen frå «crs» (EPSG 25832/25833/5972/5973 …). Resultatet er same
GeoJSON med retta koordinatar og eigenskapane «helling_retta» og «helling_maks_endring_cm».
    python korriger_objekt.py --objekt eksport.geojson --logg logg/geoscan_*.csv --ut eksport_retta.geojson
"""
import argparse
import csv
import io
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import helling as H
import koordinat as K

NAMN = {"E": ("e", "aust", "austing", "easting", "east", "x"),
        "N": ("n", "nord", "nording", "northing", "north", "y"),
        "D": ("djupn", "djupne", "dybde", "depth", "d", "djup"),
        "T": ("tid", "time", "tidspunkt", "timestamp")}


def read_csv(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    first = text.split("\n", 1)[0]
    try:
        delim = csv.Sniffer().sniff(text[:4096], delimiters=";,\t").delimiter
    except csv.Error:          # t.d. ein logg med berre overskrifta – vel det teiknet som finst i overskrifta
        delim = max(";,\t", key=first.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    if rows and rows[0] and str(rows[0][0]).startswith("Snowman Geoscan"):   # tittellina i filer frå Snowman Geoscan
        rows = rows[1:]
    if not rows:
        return [], [], delim
    return rows[0], rows[1:], delim


def num(v):
    return float(str(v).strip().replace(",", ".")) if str(v).strip() else None


def parse_time(v):
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v.strip(), fmt).timestamp()
        except ValueError:
            pass
    return None


class Logg:
    """Posisjonane frå geoscan.py med helling, i eit rutenett på 1 m for rask oppslag."""

    def __init__(self, paths, zone=None):
        """zone: UTM-sona til objekta. Loggposisjonane blir rekna om dit frå lat/lon (loggen kan vere i ei anna sone)."""
        self.rows, self.grid = [], {}
        for p in paths:
            try:
                head, rows, _ = read_csv(p)
            except Exception:
                continue           # ein øydelagd eller tom logg skal ikkje stoppe rettinga
            ix = {h: i for i, h in enumerate(head)}
            if "korrigert" not in ix:
                continue
            for r in rows:
                if len(r) < len(head) or r[ix["korrigert"]] != "1":
                    continue
                lat, lon = num(r[ix["lat_ut"]]), num(r[ix["lon_ut"]])
                z = zone or int(r[ix["sone"]])
                E, Nn = K.utm_forward(lat, lon, z)
                d = {"E": E, "N": Nn, "lat": lat, "lon": lon, "stamp": num(r[ix["stamp"]]),
                     "krenging": num(r[ix["krenging"]]), "kurs": num(r[ix["kurs"]]),
                     "d0": num(r[ix["djupn_sanntid"]]) or 0.0, "t": parse_time(r[ix["tid"]]), "sone": z,
                     "h_bakke": num(r[ix["h_bakke"]]) if "h_bakke" in ix else None}
                self.rows.append(d)
                self.grid.setdefault((int(d["E"] // 1), int(d["N"] // 1)), []).append(d)

    def nearest(self, E, N, t=None, maxdist=1.0, maxtime=2.0):
        if t is not None:
            cand = [r for r in self.rows if r["t"] is not None and abs(r["t"] - t) <= maxtime]
            if cand:
                r = min(cand, key=lambda r: abs(r["t"] - t))
                return r, math.hypot(r["E"] - E, r["N"] - N)
        best, bd = None, maxdist
        ce, cn = int(E // 1), int(N // 1)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for r in self.grid.get((ce + i, cn + j), ()):
                    dd = math.hypot(r["E"] - E, r["N"] - N)
                    if dd <= bd:
                        best, bd = r, dd
        return best, bd


def correct_object(E, N, depth, rec):
    """(E_retta, N_retta, loddrett djupn, endring i m) for eitt objekt, gitt loggposten der det vart målt."""
    dE, dN, dv = H.object_shift(depth - rec["d0"], rec["kurs"], rec["stamp"], rec["krenging"])
    _, _, dv = H.object_shift(depth, rec["kurs"], rec["stamp"], rec["krenging"])
    gE, gN = K.enu_to_grid(dE, dN, K.convergence(rec["lat"], rec["lon"], rec["sone"]))
    return E + gE, N + gN, dv, math.hypot(gE, gN)


# ---------- GeoJSON (eksport frå GRED HD / OneVision) ----------
EPSG_SONE = {25832: 32, 25833: 33, 25835: 35, 5972: 32, 5973: 33, 5975: 35, 32632: 32, 32633: 33, 32635: 35}


def geojson_zone(gj):
    """UTM-sone frå «crs» (t.d. urn:ogc:def:crs:EPSG::5973 = EUREF89 UTM33 + NN2000), eller None."""
    name = str(((gj.get("crs") or {}).get("properties") or {}).get("name", ""))
    m = re.search(r"(\d{4,5})\s*$", name)
    return EPSG_SONE.get(int(m.group(1))) if m else None


def _points(c):
    """Alle koordinatpunkt [E, N, z] i ein geometri (uansett nesting)."""
    if c and isinstance(c[0], (int, float)):
        yield c
    else:
        for x in c or []:
            yield from _points(x)


def correct_geojson(gj, logg, zmode="auto", maxdist=1.0):
    """Rett alle punkt i ein FeatureCollection på staden. zmode: «djupn» (z positiv nedover), «hoegd» (NN2000),
    eller «auto» (høgd om alle z > 20 m). Returnerer (retta, utan loggpunkt, zmode).
    Kvart objekt får eigenskapane djupn_for_m, djupn_retta_m (loddrett djupn under bakken, eitt tal per punkt)
    og flytta_cm, så djupna kan visast og eksporterast utan å vite om z var djupn eller høgd. hoegd_nn2000_m er
    høgda over havet for objektet (bakken frå loggen − loddrett djupn), bakke_nn2000_m høgda på bakken over."""
    pts = [p for f in gj.get("features", []) for p in _points((f.get("geometry") or {}).get("coordinates"))]
    if zmode == "auto":
        zmode = "hoegd" if pts and all(len(p) > 2 and p[2] > 20 for p in pts) else "djupn"
    ok = miss = 0
    for f in gj.get("features", []):
        maxch, n_ok, n = 0.0, 0, 0
        d_for, d_etter, flytta = [], [], []      # per punkt: djupn før/etter (m, loddrett under bakken) og flytting
        h_obj, h_bakke = [], []                   # per punkt: høgd NN2000 for objektet og for bakken over det
        for p in _points((f.get("geometry") or {}).get("coordinates")):
            n += 1
            if len(p) < 3:
                d_for.append(None), d_etter.append(None), flytta.append(None), h_obj.append(None), h_bakke.append(None)
                continue
            rec, _ = logg.nearest(p[0], p[1], None, maxdist)
            if rec is None or (zmode == "hoegd" and rec.get("h_bakke") is None):
                miss += 1
                d0 = round(p[2], 3) if zmode == "djupn" else None
                d_for.append(d0), d_etter.append(d0), flytta.append(None)   # urørt: same djupn som før
                h_obj.append(round(p[2], 3) if zmode == "hoegd" else None), h_bakke.append(None)
                continue
            d = p[2] if zmode == "djupn" else rec["h_bakke"] - p[2]
            E2, N2, dv, ch = correct_object(p[0], p[1], abs(d), rec)
            p[0], p[1] = round(E2, 3), round(N2, 3)
            p[2] = round(dv if zmode == "djupn" else rec["h_bakke"] - dv, 3)
            d_for.append(round(abs(d), 3)), d_etter.append(round(dv, 3)), flytta.append(round(ch * 100, 1))
            hb = rec.get("h_bakke")
            h_bakke.append(None if hb is None else round(hb, 3))
            h_obj.append(None if hb is None else round(hb - dv, 3))
            maxch, n_ok = max(maxch, ch), n_ok + 1
            ok += 1
        pr = f.setdefault("properties", {})
        pr["helling_retta"] = f"{n_ok}/{n}"
        pr["helling_maks_endring_cm"] = round(maxch * 100, 1)
        pr["djupn_for_m"], pr["djupn_retta_m"], pr["flytta_cm"] = d_for, d_etter, flytta
        pr["hoegd_nn2000_m"], pr["bakke_nn2000_m"] = h_obj, h_bakke
    return ok, miss, zmode


def find_col(head, key):
    low = [h.strip().lower() for h in head]
    for name in NAMN[key]:
        if name in low:
            return low.index(name)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rett georadar-objekt for helling (djupnfeil)")
    ap.add_argument("--objekt", required=True)
    ap.add_argument("--logg", required=True, nargs="+")
    ap.add_argument("--ut", required=True)
    ap.add_argument("--maks-avstand", type=float, default=1.0, help="meter frå objekt til næraste loggpunkt")
    ap.add_argument("--z", choices=("auto", "djupn", "hoegd"), default="auto",
                    help="GeoJSON: er z djupn (positiv nedover) eller høgd (NN2000)? auto: høgd om alle z > 20")
    ap.add_argument("--sone", type=int, help="UTM-sona til objekta (elles frå crs i GeoJSON, eller loggen)")
    a = ap.parse_args(argv)
    if Path(a.objekt).suffix.lower() in (".geojson", ".json"):
        gj = json.loads(Path(a.objekt).read_text(encoding="utf-8-sig"))
        zone = a.sone or geojson_zone(gj)
        logg = Logg(a.logg, zone)
        if not logg.rows:
            sys.exit("Loggen har ingen posisjonar med helling (korrigert = 1). Var hellinga tilgjengeleg under skanninga?")
        ok, miss, zmode = correct_geojson(gj, logg, a.z, a.maks_avstand)
        Path(a.ut).write_text(json.dumps(gj, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Retta {ok} punkt (z = {zmode}, UTM-sone {zone or 'frå loggen'}). {miss} utan loggpunkt innan "
              f"{a.maks_avstand} m (står urørte). → {a.ut}")
        return
    head, rows, delim = read_csv(a.objekt)
    ce, cn, cd, ct = (find_col(head, k) for k in "ENDT")
    if None in (ce, cn, cd):
        sys.exit(f"Fann ikkje kolonnane austing/nording/djupn i {a.objekt}. Overskrift: {head}")
    logg = Logg(a.logg, a.sone)
    if not logg.rows:
        sys.exit("Loggen har ingen posisjonar med helling (korrigert = 1). Var hellinga tilgjengeleg under skanninga?")
    out = [head + ["E_retta", "N_retta", "djupn_loddrett", "endring_cm", "stamp", "krenging", "kurs", "avstand_logg_m"]]
    ok = mangel = 0
    for r in rows:
        if not r or len(r) <= max(ce, cn, cd):
            continue
        E, N, d = num(r[ce]), num(r[cn]), num(r[cd])
        t = parse_time(r[ct]) if ct is not None else None
        rec, dist = logg.nearest(E, N, t, a.maks_avstand)
        if rec is None or d is None:
            out.append(r + ["", "", "", "", "", "", "", ""])
            mangel += 1
            continue
        E2, N2, dv, ch = correct_object(E, N, abs(d), rec)
        out.append(r + [f"{E2:.3f}", f"{N2:.3f}", f"{dv:.3f}", f"{ch * 100:.1f}", f"{rec['stamp']:.2f}",
                        f"{rec['krenging']:.2f}", f"{rec['kurs']:.1f}", f"{dist:.2f}"])
        ok += 1
    with open(a.ut, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=delim).writerows(out)
    print(f"Retta {ok} objekt. {mangel} utan loggpunkt innan {a.maks_avstand} m (står urørte). → {a.ut}")


if __name__ == "__main__":
    main()
