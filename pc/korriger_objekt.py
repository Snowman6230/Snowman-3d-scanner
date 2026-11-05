# SNOWMAN by Alpindata – Copyright © 2026 Hans Petter Brunstad Sørensen (Alpindata). Alle rettar reserverte.
"""Rett objekt frå georadaren (rør, kablar, holrom) for hellinga – djupnfeilen.

OneVision/GRED HD legg eit objekt loddrett under radaren. Når bakken hallar, ligg det eigentleg vinkelrett på
bakken, d·sin(helling) sidelengs mot oppsida. Dette skriptet les objekta (CSV med austing, nording og djupn i UTM)
og loggen frå geoscan.py (helling og kurs for kvar posisjon), og skriv ut retta koordinatar.

    python korriger_objekt.py --objekt ror.csv --logg logg/geoscan_20261106_090000.csv --ut ror_retta.csv

Objektfila: CSV (; , eller tab) med overskrift. Kolonnar blir funne på namn:
    austing: E, Aust, Austing, Easting, X     nording: N, Nord, Nording, Northing, Y
    djupn:   Djupn, Djupne, Dybde, Depth, D   (positiv nedover, meter)   valfri tid: Tid, Time
Alle andre kolonnar blir med uendra. Koordinatane må vere i same UTM-sone som loggen (sjå «sone» i oppsettet).
"""
import argparse
import csv
import io
import math
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
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
    rows = list(csv.reader(io.StringIO(text), dialect))
    return rows[0], rows[1:], dialect.delimiter


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

    def __init__(self, paths):
        self.rows, self.grid = [], {}
        for p in paths:
            head, rows, _ = read_csv(p)
            ix = {h: i for i, h in enumerate(head)}
            for r in rows:
                if len(r) < len(head) or r[ix["korrigert"]] != "1":
                    continue
                d = {"E": num(r[ix["E_ut"]]), "N": num(r[ix["N_ut"]]), "lat": num(r[ix["lat_ut"]]),
                     "lon": num(r[ix["lon_ut"]]), "stamp": num(r[ix["stamp"]]), "krenging": num(r[ix["krenging"]]),
                     "kurs": num(r[ix["kurs"]]), "d0": num(r[ix["djupn_sanntid"]]) or 0.0,
                     "t": parse_time(r[ix["tid"]]), "sone": int(r[ix["sone"]])}
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
    a = ap.parse_args(argv)
    head, rows, delim = read_csv(a.objekt)
    ce, cn, cd, ct = (find_col(head, k) for k in "ENDT")
    if None in (ce, cn, cd):
        sys.exit(f"Fann ikkje kolonnane austing/nording/djupn i {a.objekt}. Overskrift: {head}")
    logg = Logg(a.logg)
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
