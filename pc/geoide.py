# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Kartverket sin geoidemodell HREF2018B (NN2000 over EUREF89): N(lat, lon) i meter, NN2000 = ellipsoidisk − N.

Opphav: kopiert frå SNOWMAN Snødjupne, pc/v1.6/terrain.py (klassen Geoid og _geokeys), Snowman6230/Snowman-Snowdeept
commit 8a05dc4. Modellfila: © Kartverket, CC BY 4.0 – sjå geoide/LES-MEG.txt.
Krev numpy og tifffile. Manglar dei, returnerer n() None, og programmet brukar høgda frå mottakaren (med åtvaring).
"""
import math
from pathlib import Path

try:
    import numpy as np
    import tifffile
    AVAILABLE, IMPORT_ERROR = True, ""
except Exception as e:  # pragma: no cover
    AVAILABLE, IMPORT_ERROR = False, f"Geoiden manglar bibliotek ({e}). Køyr INSTALL.bat"


def _geokeys(tag_value):
    v = list(tag_value or [])
    keys = {}
    if len(v) >= 4:
        for i in range(v[3]):
            k, loc, cnt, val = v[4 + i * 4: 8 + i * 4]
            if loc == 0:
                keys[k] = val
    return keys


class Geoid:
    def __init__(self, path):
        self.path = Path(path)
        self.g = None
        self.err = "" if AVAILABLE else IMPORT_ERROR

    def _load(self):
        if self.g is None and not self.err:
            try:
                with tifffile.TiffFile(self.path) as tf:
                    p = tf.pages[0]
                    tags = {t.code: t.value for t in p.tags.values()}
                    a = p.asarray().astype(np.float64)
                sc, tp = tags[33550], tags[33922]
                pt = _geokeys(tags.get(34735)).get(1025) == 2  # PixelIsPoint: tiepunktet er midt i ruta
                self.g = {"a": a, "lon0": tp[3] + (0 if pt else sc[0] / 2), "lat0": tp[4] - (0 if pt else sc[1] / 2),
                          "dlon": sc[0], "dlat": sc[1]}
            except Exception as e:
                self.err = f"Geoidemodellen manglar eller kan ikkje lesast ({e})"
        return self.g

    def n(self, lat, lon):
        g = self._load()
        if not g or lat is None or lon is None:
            return None
        c, r = (lon - g["lon0"]) / g["dlon"], (g["lat0"] - lat) / g["dlat"]
        c0, r0 = int(math.floor(c)), int(math.floor(r))
        a = g["a"]
        if r0 < 0 or c0 < 0 or r0 + 1 >= a.shape[0] or c0 + 1 >= a.shape[1]:
            return None  # utanfor Noreg
        fc, fr = c - c0, r - r0
        v = (a[r0, c0] * (1 - fc) * (1 - fr) + a[r0, c0 + 1] * fc * (1 - fr)
             + a[r0 + 1, c0] * (1 - fc) * fr + a[r0 + 1, c0 + 1] * fc * fr)
        return None if not math.isfinite(v) else float(v)


GEOID = Geoid(Path(__file__).resolve().parent / "geoide" / "no_kv_HREF2018B_NN2000_EUREF89.tif")
