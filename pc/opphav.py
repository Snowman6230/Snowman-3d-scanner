# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Opphavet til Snowman Geoscan: namn, produsent og signatur. Alt programmet lagar (rapportar, eksportfiler,
pakkar, loggar og nettsida) får namnet med seg – synleg i rapportar, og gøymt som metadata i datafiler, så
opphavet kan visast også når fila er sendt vidare.

Signaturen er ein fast tekst som blir lagd inn same stad i alle filer (GeoJSON «generator», DXF-kommentar 999,
zip-kommentar, HTTP «Server», HTML «generator»/«author»). sjekk_signatur() finn han att i ei fil.
"""
import base64
import hashlib

NAMN = "Snowman Geoscan"
PRODUSENT = "Alpindata v/Hans Petter B. Sørensen"
COPYRIGHT = "Copyright © 2026 Hans Petter Brunstad Sørensen (Alpindata). Alle rettar reserverte."
_KJERNE = "SNOWMAN GEOSCAN|ALPINDATA|HANS PETTER BRUNSTAD SØRENSEN|SYKKYLVEN|2026"
SIGNATUR = "SNWGEO-" + hashlib.sha256(_KJERNE.encode("utf-8")).hexdigest()[:16].upper()
SIGNATUR_B64 = base64.b64encode(_KJERNE.encode("utf-8")).decode("ascii")


def versjon():
    """Versjonsnummeret frå geoscan.py (VERSJON = "…"), utan å importere programmet."""
    import re
    from pathlib import Path
    try:
        m = re.search(r'^VERSJON = "([^"]+)"', (Path(__file__).resolve().parent / "geoscan.py").read_text(encoding="utf-8"), re.M)
        return m.group(1) if m else "?"
    except OSError:
        return "?"


def generator(versjon=None):
    """Éi line med namn, versjon, produsent og signatur – til metadata i filer."""
    return f"{NAMN} {versjon or globals()['versjon']()} – {PRODUSENT} – {SIGNATUR}"


def sjekk_signatur(data):
    """True om signaturen til Snowman Geoscan finst i fila (byte eller tekst)."""
    if isinstance(data, str):
        data = data.encode("utf-8", "replace")
    return SIGNATUR.encode("ascii") in data or SIGNATUR_B64.encode("ascii") in data
