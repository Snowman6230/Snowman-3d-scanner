# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Bakgrunnsfiler i kartet (0.9.19, ønske frå Norman 8.11.2026): DXF-teikningar og KOF-filer frå landmålar.

Filene blir lagra i pc/bakgrunn/ (berre på PC-en, aldri i git) og gjorde om til GeoJSON i breidd/lengd for
kartet. Kvar fil har eit koordinatsystem (UTM 32/33/35 eller NTM 5–30, EUREF89) og lag som kan slåast av og på.

DXF: ASCII-DXF (R12 og nyare). LINE, LWPOLYLINE, POLYLINE/VERTEX, POINT, CIRCLE, ARC, TEXT/MTEXT, SPLINE
(kontrollpunkt) og INSERT (blokker blir pakka ut). Bogar (bulge) blir rette liner. Høgd (z) blir ikkje brukt.
DWG er eit lukka format og må lagrast som DXF først.
KOF: 05-liner er punkt (namn, temakode, X = nord, Y = aust, høgd). 09_91 startar ei line, 09_99 sluttar ho,
09_96 sluttar og lukkar ho. Temakoden blir brukt som lag.
"""
import json
import math
import re
import time
from pathlib import Path

import koordinat as K

HER = Path(__file__).resolve().parent
DIR = HER / "bakgrunn"
MAKS_PUNKT = 400_000            # fleire punkt enn dette i éi fil gjer kartet tregt
ACI = {1: "#ff4040", 2: "#ffd84a", 3: "#3ecf74", 4: "#3fd7e0", 5: "#4e7bff", 6: "#e04fd0", 8: "#9a9a9a",
       9: "#c8c8c8", 30: "#ff9a3c", 40: "#ffb347", 140: "#5fb8ff", 150: "#4e9bff", 250: "#7a7a7a"}
STANDARDFARGE = "#e8e2c8"


# ---------------- koordinatsystem ----------------

def crs_til_latlon(crs):
    """«utm32» / «ntm10» → funksjon (aust, nord) → (lat, lon)."""
    m = re.fullmatch(r"(utm|ntm)(\d{1,2})", crs or "")
    if not m:
        raise ValueError(f"ukjent koordinatsystem: {crs}")
    sone = int(m.group(2))
    if m.group(1) == "utm":
        return lambda e, n: K.utm_inverse(e, n, sone)
    return lambda e, n: K.ntm_inverse(e, n, sone)


def gjett_crs(bbox, utm_sone=32, lon=None):
    """Gjett koordinatsystem frå storleiken på tala. UTM-nord i Noreg er ca. 6,4–7,9 mill., NTM-nord ca. 1,0–2,6 mill.
    (origo 58° N + 1 000 000). NTM-sone blir teken frå lengdegraden der vogna er (lon), elles 10."""
    if not bbox:
        return f"utm{utm_sone}", "tom fil"
    (e0, n0), (e1, n1) = bbox
    nm = (n0 + n1) / 2
    if 6.3e6 < nm < 8.0e6:
        return f"utm{utm_sone}", None
    if 0.9e6 < nm < 2.7e6:
        sone = int(math.floor(lon)) if lon is not None and 5 <= lon < 31 else 10
        return f"ntm{sone}", f"tala ser ut som NTM – sone {sone} er gjetta, sjekk mot kartet"
    return f"utm{utm_sone}", "tala liknar verken UTM eller NTM (lokalt koordinatsystem?) – fila kjem truleg feil"


# ---------------- DXF ----------------

def _par(tekst):
    li = tekst.splitlines()
    for i in range(0, len(li) - 1, 2):
        try:
            yield int(li[i].strip()), li[i + 1].strip()
        except ValueError:
            continue


def _entitetar(par):
    """Del (kode, verdi)-par i seksjonar og entitetar: {"seksjon": [ (type, [(kode, verdi), …]), … ]}."""
    seksjonar, seks, ent, i = {}, None, None, 0
    venta_namn = False
    for kode, v in par:
        if kode == 0:
            if ent is not None and seks is not None:
                seksjonar.setdefault(seks, []).append(ent)
            ent = None
            if v == "SECTION":
                venta_namn = True
                continue
            if v == "ENDSEC":
                seks = None
                continue
            if v == "EOF":
                break
            ent = (v, [])
        elif kode == 2 and venta_namn:
            seks, venta_namn = v, False
        elif ent is not None:
            ent[1].append((kode, v))
    if ent is not None and seks is not None:
        seksjonar.setdefault(seks, []).append(ent)
    return seksjonar


def _f(d, k, std=0.0):
    try:
        return float(d.get(k, std))
    except (TypeError, ValueError):
        return std


def _bue(cx, cy, r, a0, a1, n=48):
    if a1 < a0:
        a1 += 360
    steg = max(4, int(n * (a1 - a0) / 360))
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steg)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steg))) for i in range(steg + 1)]


def _geometri(liste):
    """Gjer DXF-entitetar om til (type, lag, farge, koordinatar, tekst) i teikningskoordinatar."""
    ut, i = [], 0
    while i < len(liste):
        typ, kv = liste[i]
        d = {}
        for k, v in kv:
            d.setdefault(k, v)
        lag, farge = d.get(8, "0"), int(_f(d, 62, 256))
        if typ == "LINE":
            ut.append(("L", lag, farge, [(_f(d, 10), _f(d, 20)), (_f(d, 11), _f(d, 21))], None))
        elif typ == "LWPOLYLINE":
            pkt, x = [], None
            for k, v in kv:
                if k == 10:
                    x = float(v)
                elif k == 20 and x is not None:
                    pkt.append((x, float(v)))
                    x = None
            if int(_f(d, 70)) & 1 and pkt:
                pkt.append(pkt[0])
            if len(pkt) > 1:
                ut.append(("L", lag, farge, pkt, None))
        elif typ == "POLYLINE":
            lukka, pkt = int(_f(d, 70)) & 1, []
            i += 1
            while i < len(liste) and liste[i][0] == "VERTEX":
                vd = dict(liste[i][1])
                pkt.append((_f(vd, 10), _f(vd, 20)))
                i += 1
            if lukka and pkt:
                pkt.append(pkt[0])
            if len(pkt) > 1:
                ut.append(("L", lag, farge, pkt, None))
            continue                       # SEQEND (eller neste entitet) blir handsama i neste runde
        elif typ == "POINT":
            ut.append(("P", lag, farge, [(_f(d, 10), _f(d, 20))], None))
        elif typ == "CIRCLE":
            ut.append(("L", lag, farge, _bue(_f(d, 10), _f(d, 20), _f(d, 40), 0, 360), None))
        elif typ == "ARC":
            ut.append(("L", lag, farge, _bue(_f(d, 10), _f(d, 20), _f(d, 40), _f(d, 50), _f(d, 51)), None))
        elif typ in ("TEXT", "MTEXT"):
            t = d.get(1, "")
            t = re.sub(r"\\[A-Za-z][^;]*;|\\P|[{}]", " ", t).strip()
            if t:
                ut.append(("T", lag, farge, [(_f(d, 10), _f(d, 20))], t[:80]))
        elif typ == "SPLINE":
            pkt, x = [], None
            for k, v in kv:
                if k == 10:
                    x = float(v)
                elif k == 20 and x is not None:
                    pkt.append((x, float(v)))
                    x = None
            if len(pkt) > 1:
                ut.append(("L", lag, farge, pkt, None))
        elif typ == "INSERT":
            ut.append(("I", lag, farge, [(_f(d, 10), _f(d, 20))],
                       (d.get(2, ""), _f(d, 41, 1.0), _f(d, 42, 1.0), _f(d, 50))))
        i += 1
    return ut


def les_dxf(tekst):
    """→ (geometriar, lagfargar). Geometri: (type L/P/T, lag, farge-ACI, [(x, y)…], tekst)."""
    if tekst.startswith("AutoCAD Binary DXF"):
        raise ValueError("binær DXF kan ikkje lesast – lagre som ASCII-DXF")
    sek = _entitetar(_par(tekst))
    lagfarge = {}
    for typ, kv in sek.get("TABLES", []):
        if typ == "LAYER":
            d = dict(kv)
            try:
                lagfarge[d.get(2, "")] = abs(int(d.get(62, 7)))
            except ValueError:
                pass
    blokker, namn, base, inn = {}, None, (0.0, 0.0), []
    for typ, kv in sek.get("BLOCKS", []):
        if typ == "BLOCK":
            d = dict(kv)
            namn, base, inn = d.get(2, ""), (_f(d, 10), _f(d, 20)), []
        elif typ == "ENDBLK":
            if namn is not None:
                blokker[namn] = (base, _geometri(inn))
            namn = None
        elif namn is not None:
            inn.append((typ, kv))

    def pakk_ut(geo, djupn=0):
        for g in geo:
            if g[0] != "I":
                yield g
                continue
            if djupn > 4 or g[4][0] not in blokker:
                continue
            (bx, by), bgeo = blokker[g[4][0]]
            (ix, iy), (_, sx, sy, rot) = g[3][0], g[4]
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            for b in pakk_ut(bgeo, djupn + 1):
                pkt = [(ix + ((x - bx) * sx) * c - ((y - by) * sy) * s, iy + ((x - bx) * sx) * s + ((y - by) * sy) * c)
                       for x, y in b[3]]
                lag = g[1] if b[1] == "0" else b[1]      # entitetar på lag 0 i ein blokk arvar laget til INSERT
                yield (b[0], lag, b[2] if b[2] != 0 else g[2], pkt, b[4])
    return list(pakk_ut(_geometri(sek.get("ENTITIES", [])))), lagfarge


# ---------------- KOF ----------------

def les_kof(tekst):
    """→ geometriar som for DXF. Lag = temakoden. X i KOF er nord, Y er aust."""
    ut, line, tema_line, lukk = [], None, None, False

    def slutt(lukk_ho=False):
        nonlocal line
        if line and len(line) > 1:
            pkt = line + ([line[0]] if lukk_ho else [])
            ut.append(("L", tema_line or "KOF", 256, pkt, None))
        elif line:
            ut.append(("P", tema_line or "KOF", 256, line, None))
        line = None

    for rad in tekst.splitlines():
        if not rad.strip() or rad.startswith("-"):
            continue
        r = rad.strip()
        if r.startswith("09"):
            kodar = re.findall(r"_(\d{2})", r)
            for k in kodar:
                if k in ("91", "92") or "72" <= k <= "79" or "82" <= k <= "89":
                    slutt()
                    line, tema_line = [], None
                elif k == "99":
                    slutt()
                elif k == "96":
                    slutt(lukk_ho=True)
            continue
        if not r.startswith("05"):
            continue
        tok = r[2:].split()
        tal = []
        for t in tok:
            try:
                tal.append(float(t))
            except ValueError:
                tal.append(None)
        store = [i for i, v in enumerate(tal) if v is not None and abs(v) >= 1000]
        if len(store) < 2:
            continue
        ix, iy = store[0], store[1]
        x_nord, y_aust = tal[ix], tal[iy]
        tekstar = [t for j, t in enumerate(tok[:ix]) if tal[j] is None or j < ix]
        tema = tekstar[1] if len(tekstar) > 1 else (tekstar[0] if tekstar else "KOF")
        punkt = (y_aust, x_nord)
        if line is not None:
            line.append(punkt)
            tema_line = tema_line or tema
        else:
            ut.append(("P", tema, 256, [punkt], tekstar[0] if tekstar else None))
    slutt()
    return ut, {}


# ---------------- lagring og omgjering ----------------

def _meta_fil():
    return DIR / "bakgrunn.json"


def liste():
    try:
        return json.loads(_meta_fil().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _lagre_meta(m):
    DIR.mkdir(exist_ok=True)
    _meta_fil().write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def _les_fil(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def tolk(path):
    tekst = _les_fil(path)
    suf = Path(path).suffix.lower()
    if suf == ".dxf":
        return les_dxf(tekst)
    if suf == ".kof":
        return les_kof(tekst)
    raise ValueError("berre DXF og KOF kan lesast. DWG må lagrast som DXF først")


def bbox(geo):
    xs = [x for g in geo for x, _ in g[3]]
    ys = [y for g in geo for _, y in g[3]]
    if not xs:
        return None
    # Ytterpunkt kan vere feil (t.d. ein tekst ved origo). Bruk 1–99 % for å gjette koordinatsystemet.
    xs.sort(), ys.sort()
    lo, hi = int(len(xs) * 0.01), max(0, int(len(xs) * 0.99) - 1)
    return (xs[lo], ys[lo]), (xs[hi], ys[hi])


def til_geojson(geo, lagfarge, crs, skala=1.0):
    f = crs_til_latlon(crs)
    feats, n = [], 0
    for typ, lag, farge, pkt, tekst in geo:
        aci = farge if farge not in (0, 256) else lagfarge.get(lag, 7)
        col = ACI.get(abs(aci), STANDARDFARGE)
        ll = []
        for x, y in pkt:
            la, lo = f(x * skala, y * skala)
            ll.append([round(lo, 8), round(la, 8)])
        n += len(ll)
        if n > MAKS_PUNKT:
            break
        if typ == "L":
            g = {"type": "LineString", "coordinates": ll}
        else:
            g = {"type": "Point", "coordinates": ll[0]}
        p = {"lag": lag, "farge": col}
        if tekst:
            p["tekst"] = tekst
        feats.append({"type": "Feature", "geometry": g, "properties": p})
    return {"type": "FeatureCollection", "features": feats, "avkorta": n > MAKS_PUNKT}


def legg_til(namn, data, crs="auto", utm_sone=32, lon=None):
    """Lagre ei ny bakgrunnsfil og gjer ho om. Returnerer metadata."""
    suf = Path(namn).suffix.lower()
    if suf == ".dwg":
        raise ValueError("DWG er eit lukka format. Opne teikninga og lagre ho som DXF (AutoCAD: Lagre som → DXF)")
    if suf not in (".dxf", ".kof"):
        raise ValueError("berre DXF og KOF kan brukast som bakgrunn")
    DIR.mkdir(exist_ok=True)
    fid = time.strftime("%Y%m%d_%H%M%S") + "_" + re.sub(r"[^\w.\-]", "_", Path(namn).name)[:60]
    (DIR / fid).write_bytes(data)
    m = {"id": fid, "namn": Path(namn).name, "type": suf[1:], "crs": crs, "synleg": True, "skjulte_lag": []}
    try:
        _gjer_om(m, utm_sone, lon)
    except Exception:
        (DIR / fid).unlink(missing_ok=True)
        raise
    alle = liste()
    alle.insert(0, m)
    _lagre_meta(alle)
    return m


def _gjer_om(m, utm_sone=32, lon=None):
    geo, lagfarge = tolk(DIR / m["id"])
    bb = bbox(geo)
    skala = 1.0
    if bb and (bb[0][1] + bb[1][1]) / 2 > 1e9:          # millimeter (t.d. 6 900 000 000) → meter
        skala = 0.001
        bb = ((bb[0][0] * skala, bb[0][1] * skala), (bb[1][0] * skala, bb[1][1] * skala))
    crs, merk = (gjett_crs(bb, utm_sone, lon) if m.get("crs") in (None, "", "auto") else (m["crs"], None))
    gj = til_geojson(geo, lagfarge, crs, skala)
    (DIR / (m["id"] + ".geojson")).write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")
    lag = {}
    for ft in gj["features"]:
        p = ft["properties"]
        lag.setdefault(p["lag"], {"n": 0, "farge": p["farge"]})["n"] += 1
    m.update(crs_brukt=crs, merknad=merk, lag=lag, tal=len(gj["features"]), avkorta=gj["avkorta"],
             skala=skala, gjort=time.strftime("%Y-%m-%d %H:%M"))
    return m


def endre(fid, synleg=None, crs=None, skjulte_lag=None, utm_sone=32, lon=None):
    alle = liste()
    for m in alle:
        if m["id"] == fid:
            if synleg is not None:
                m["synleg"] = bool(synleg)
            if skjulte_lag is not None:
                m["skjulte_lag"] = [str(x) for x in skjulte_lag]
            if crs is not None and crs != m.get("crs"):
                crs_til_latlon(crs) if crs != "auto" else None
                m["crs"] = crs
                _gjer_om(m, utm_sone, lon)
            _lagre_meta(alle)
            return m
    raise ValueError("fann ikkje bakgrunnsfila")


def slett(fid):
    alle = liste()
    ny = [m for m in alle if m["id"] != fid]
    if len(ny) == len(alle):
        return False
    for p in (DIR / fid, DIR / (fid + ".geojson")):
        p.unlink(missing_ok=True)
    _lagre_meta(ny)
    return True


def geojson(fid):
    if not any(m["id"] == fid for m in liste()):
        raise ValueError("fann ikkje bakgrunnsfila")
    return (DIR / (fid + ".geojson")).read_text(encoding="utf-8")
