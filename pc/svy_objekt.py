# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Les objekta (<Targets>) frå ei OneVision-målefil (.svy) og gjer dei om til GeoJSON.

OneVision lagrar dei automatisk funne objekta inne i .svy-fila, ikkje i ei eiga eksportfil. Formatet er ikkje
dokumentert av IDS. Det er tolka frå «Survey_2022.11.29_001 kagholvegen.svy» (Norman Hole, 6.11.2026):

    <SpatialReferenceSystem> … <EPSGCode>32632</EPSGCode>      koordinatsystemet til objekta
    <Targets><PropagationVelocity>1e8</PropagationVelocity><Data>base64</Data></Targets>

    Data: blokker som byrjar med b"<Target>":
      +12  uint32 type (1 = punkt, namn «T…»; 2 = linje, namn «L…»)
      +16  uint32 n, så namnet i UTF-16LE (n byte), til dømes «L10032» eller «T130174»
      deretter punkt på 56 byte (little-endian):
           double tvers (m, frå midten av skannebeltet)   double langs (m, i swathen)
           double austing   double nording                double djupn (m, positiv nedover)
           uint32  uint32 (ukjende)                       double utbreiingsfart (m/s)

«T»-objekt har to punkt tvers over beltet (±0,383 m). Djupna er rekna med farten som står i fila (0,1 m/ns i
Kagholvegen). Resultatet kan lesast av korriger_objekt.py og Resultat-fana som vanleg GeoJSON.

    python svy_objekt.py maaling.svy objekt.geojson
"""
import base64
import json
import re
import struct
import sys
from pathlib import Path

PUNKT = 56          # byte per punkt


def _ok(e, n, d):
    return 1e5 < e < 1e6 and 1e6 < n < 1e7 and 0 <= d < 20


def les_svy(path):
    """(epsg, [(namn, type, [(E, N, djupn, tvers, langs, fart_m_s), …]), …]) frå ei .svy-fil."""
    t = Path(path).read_bytes().decode("utf-8", "replace")
    m = re.search(r"<EPSGCode>\s*(\d+)\s*</EPSGCode>", t)
    epsg = int(m.group(1)) if m else None
    m = re.search(r"<Targets>.*?<Data>(.*?)</Data>", t, re.S)
    if not m:
        return epsg, []
    b = base64.b64decode("".join(m.group(1).split()))
    heads = [h.start() for h in re.finditer(b"<Target>", b)] + [len(b)]
    objekt = []
    for o, slutt in zip(heads, heads[1:]):
        if o + 20 > slutt:
            continue
        typ, n = struct.unpack_from("<II", b, o + 12)
        if n > 200 or o + 20 + n > slutt:
            continue
        namn = b[o + 20:o + 20 + n].decode("utf-16le", "replace")
        pkt = []
        i = o + 20 + n
        while i + PUNKT <= slutt:          # søk fram til første gyldige punkt, så fast steg på 56 byte
            tvers, langs, e, nn, d = struct.unpack_from("<5d", b, i)
            if _ok(e, nn, d) and abs(tvers) < 5:
                fart = struct.unpack_from("<d", b, i + 48)[0]
                pkt.append((e, nn, d, tvers, langs, fart))
                i += PUNKT
            else:
                i += 1
        if pkt:
            objekt.append((namn, typ, pkt))
    return epsg, objekt


def til_geojson(epsg, objekt, kjelde=""):
    feats = []
    for namn, typ, pkt in objekt:
        coords = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in pkt]
        geom = ({"type": "Point", "coordinates": coords[0]} if len(coords) == 1
                else {"type": "LineString", "coordinates": coords})
        fart = pkt[0][5]
        feats.append({"type": "Feature", "geometry": geom, "properties": {
            "namn": namn, "type": "linje" if typ == 2 or namn.startswith("L") else "punkt",
            "punkt": len(pkt), "djupn_min_m": round(min(p[2] for p in pkt), 3),
            "djupn_maks_m": round(max(p[2] for p in pkt), 3),
            "fart_m_ns": round(fart / 1e9, 4) if fart and 1e6 < fart < 3e8 else None}})
    gj = {"type": "FeatureCollection", "name": "OneVision-objekt",
          "laga_av": "Snowman Geoscan – Alpindata HP Brunstad Sørensen", "kjelde": kjelde, "features": feats}
    if epsg:
        gj["crs"] = {"type": "name", "properties": {"name": f"urn:ogc:def:crs:EPSG::{epsg}"}}
    return gj


def svy_til_geojson(path):
    epsg, objekt = les_svy(path)
    if not objekt:
        raise ValueError("fann ingen objekt (<Targets>) i .svy-fila")
    return til_geojson(epsg, objekt, Path(path).name)


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    if len(a) != 2:
        sys.exit("Bruk: python svy_objekt.py maaling.svy objekt.geojson")
    gj = svy_til_geojson(a[0])
    Path(a[1]).write_text(json.dumps(gj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(gj['features'])} objekt → {a[1]}")


if __name__ == "__main__":
    main()
