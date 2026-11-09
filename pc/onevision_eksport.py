# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Objekt (røyr og kablar) som er eksporterte frå OneVision til mappa «Exports» i målemappa (0.9.21).

OneVision 2.0-manualen (MNG/2016/0018, kap. 4.2): «Target Export» lagar IDS Geomap, ESRI Shapefile, AutoDesk DXF
og KML i mappa «Exports» i målemappa, eventuelt i eit anna koordinatsystem. Ved Holetomta 9.11.2026 var <Targets>
i .svy-fila tom, så røyra Norman merkte, låg truleg berre der.

Formatet frå OneVision har vi ikkje sett enno. Lesaren er difor generell:
– DXF: LINE, POLYLINE/VERTEX, LWPOLYLINE og POINT med høgd (kode 30), via lesaren i bakgrunn.py
– Shapefile: punkt og linjer (med og utan Z), med attributtane frå .dbf
Koordinatane blir gjorde om til UTM (sona frå .svy-fila) viss dei ser ut som breidd/lengd. z blir djupn (positiv
nedover) når alle z er mellom −20 og 0, elles blir tala brukte som dei er (korriger_objekt finn sjølv ut om z er
høgd eller djupn).
"""
import struct
from pathlib import Path

import koordinat as K

TYPAR = (".dxf", ".shp")


def filer(svy):
    d = Path(svy).parent / "Exports"
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.suffix.lower() in TYPAR and p.is_file())


def _dbf(path):
    """Attributtane i ein .dbf-fil: liste med dict per post (berre tekst og tal)."""
    try:
        b = Path(path).read_bytes()
    except OSError:
        return []
    n, hl, rl = struct.unpack_from("<IHH", b, 4)
    felt, i = [], 32
    while i < hl - 1 and b[i] != 0x0D:
        namn = b[i:i + 11].split(b"\0")[0].decode("latin-1")
        felt.append((namn, chr(b[i + 11]), b[i + 16]))
        i += 32
    ut = []
    for r in range(n):
        o = hl + r * rl + 1
        d, p = {}, o
        for namn, typ, ln in felt:
            v = b[p:p + ln].decode("latin-1", errors="replace").strip()
            p += ln
            if typ in "NF":
                try:
                    v = float(v) if v else None
                except ValueError:
                    pass
            d[namn] = v
        ut.append(d)
    return ut


def _shp(path):
    """→ [(type 'P'|'L', [(x, y, z|None), …]), …] frå ein .shp-fil (punkt, linjer og flater, med og utan Z)."""
    b = Path(path).read_bytes()
    ut, i = [], 100
    while i + 12 <= len(b):
        ln = struct.unpack_from(">i", b, i + 4)[0] * 2
        o = i + 8
        st = struct.unpack_from("<i", b, o)[0]
        if st in (1, 11, 21):
            x, y = struct.unpack_from("<2d", b, o + 4)
            z = struct.unpack_from("<d", b, o + 20)[0] if st == 11 else None
            ut.append(("P", [(x, y, z)]))
        elif st in (3, 5, 13, 15, 23, 25):
            nparts, npkt = struct.unpack_from("<2i", b, o + 36)
            parts = list(struct.unpack_from(f"<{nparts}i", b, o + 44))
            pk = o + 44 + 4 * nparts
            xy = [struct.unpack_from("<2d", b, pk + 16 * k) for k in range(npkt)]
            zs = [None] * npkt
            if st in (13, 15):
                zo = pk + 16 * npkt + 16
                zs = list(struct.unpack_from(f"<{npkt}d", b, zo))
            for a, e in zip(parts, parts[1:] + [npkt]):
                ut.append(("L", [(xy[k][0], xy[k][1], zs[k]) for k in range(a, e)]))
        else:
            ut.append(None)                 # tom eller ukjend form – held talet på postar likt med .dbf
        i += 8 + ln
    return ut


def _dxf(path):
    import bakgrunn as BG
    geo, _ = BG.tolk(path)
    ut = []
    for typ, lag, _farge, pkt, tekst in geo:
        if typ not in ("L", "P"):
            continue
        ut.append(("L" if typ == "L" else "P", [(x, y, getattr(p, "z", None)) for p in pkt for x, y in [p]],
                   {"layer": lag, **({"description": tekst} if tekst else {})}))
    return ut


def les(svy, sone=None):
    """GeoJSON (UTM) med alle objekta i Exports-mappa til målinga, eller None om det ikkje finst nokon."""
    feats = []
    for f in filer(svy):
        try:
            if f.suffix.lower() == ".shp":
                attr = _dbf(f.with_suffix(".dbf"))
                rad = [(g[0], g[1], attr[k] if k < len(attr) else {}) for k, g in enumerate(_shp(f)) if g]
            else:
                rad = _dxf(f)
        except Exception:
            continue
        for typ, pkt, pr in rad:
            pkt = [p for p in pkt if p[0] is not None and p[1] is not None]
            if not pkt:
                continue
            feats.append({"type": "Feature", "properties": dict(pr, kjelde=f.name),
                          "geometry": {"type": "Point" if typ == "P" or len(pkt) == 1 else "LineString",
                                       "coordinates": pkt}})
    if not feats:
        return None
    alle = [p for ft in feats for p in ft["geometry"]["coordinates"]]
    grader = all(abs(p[0]) <= 180 and abs(p[1]) <= 90 for p in alle)
    if grader:
        z0 = sone or K.zone_of(sum(p[0] for p in alle) / len(alle))
    zs = [p[2] for p in alle if p[2] is not None]
    djupn_neg = bool(zs) and all(-20 < z <= 0 for z in zs)
    for ft in feats:
        ny = []
        for x, y, z in ft["geometry"]["coordinates"]:
            if grader:
                x, y = K.utm_forward(y, x, z0)
            c = [round(x, 3), round(y, 3)]
            if z is not None:
                c.append(round(-z if djupn_neg else z, 3))
            ny.append(c)
        ft["geometry"]["coordinates"] = ny[0] if ft["geometry"]["type"] == "Point" else ny
    gj = {"type": "FeatureCollection", "name": "OneVision Exports", "kjelde": "Exports",
          "laga_av": "Snowman Geoscan – Alpindata HP Brunstad Sørensen", "features": feats}
    s = z0 if grader else sone
    if s:
        gj["crs"] = {"type": "name", "properties": {"name": f"urn:ogc:def:crs:EPSG::{25800 + int(s)}"}}
    return gj
