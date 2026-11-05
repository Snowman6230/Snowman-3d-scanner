# SNOWMAN by Alpindata – Copyright © 2026 Hans Petter Brunstad Sørensen (Alpindata). Alle rettar reserverte.
"""NMEA: sjekksum, tolking og omskriving av posisjonen i GGA, RMC, GLL og PTNL,GGK.

Talker-ID-en blir aldri endra ($INGGA blir verande $INGGA). Alle felt utanom posisjon og høgd blir som dei var.
"""


def checksum(body):
    c = 0
    for ch in body:
        c ^= ord(ch)
    return f"{c:02X}"


def valid(line):
    """True om lina har rett sjekksum. Linjer utan sjekksum blir godtekne (nokre eldre mottakarar)."""
    line = line.strip()
    if not line.startswith("$"):
        return False
    if "*" not in line:
        return True
    body, cs = line[1:].rsplit("*", 1)
    return checksum(body) == cs[:2].upper()


def build(fields):
    body = ",".join(fields)
    return f"${body}*{checksum(body)}"


def split(line):
    return line.strip()[1:].split("*")[0].split(",")


def coord_in(v, hemi):
    """ddmm.mmmm / dddmm.mmmm → desimalgrader."""
    if not v:
        return None
    x = float(v)
    d = int(x // 100)
    deg = d + (x - d * 100) / 60
    return -deg if hemi in ("S", "W") else deg


def coord_out(deg, is_lat, decimals=7):
    """Desimalgrader → (ddmm.mmmmmmm, halvkule). 7 desimalar på minutt ≈ 0,2 mm."""
    hemi = ("N" if deg >= 0 else "S") if is_lat else ("E" if deg >= 0 else "W")
    a = abs(deg)
    d = int(a)
    m = round((a - d) * 60, decimals)
    if m >= 60:
        d, m = d + 1, m - 60
    w = 2 if is_lat else 3
    return f"{d:0{w}d}{m:0{3 + decimals}.{decimals}f}", hemi


def kind(fields):
    t = fields[0]
    if t.endswith("GGA") and len(fields) >= 10:
        return "GGA"
    if t.endswith("RMC") and len(fields) >= 7:
        return "RMC"
    if t.endswith("GLL") and len(fields) >= 5:
        return "GLL"
    if t == "PTNL" and len(fields) >= 12 and fields[1] == "GGK":
        return "GGK"
    return None


_POS = {"GGA": (2, 4), "RMC": (3, 5), "GLL": (1, 3), "GGK": (4, 6)}


def parse_gga(fields):
    """{lat, lon, q, sats, alt, sep} frå ei GGA, eller None om ho ikkje har posisjon."""
    lat, lon = coord_in(fields[2], fields[3]), coord_in(fields[4], fields[5])
    if lat is None or lon is None:
        return None
    f = lambda i: float(fields[i]) if len(fields) > i and fields[i] else None
    return {"lat": lat, "lon": lon, "q": int(fields[6] or 0), "sats": fields[7],
            "alt": f(9), "sep": f(11)}


def position(fields):
    k = kind(fields)
    if not k:
        return None
    i, j = _POS[k]
    lat, lon = coord_in(fields[i], fields[i + 1]), coord_in(fields[j], fields[j + 1])
    return None if lat is None or lon is None else (lat, lon)


def rewrite(fields, lat, lon, dh=None, alt=None, sep=None):
    """Ny NMEA-line med ny posisjon. dh = endring i høgd (m) for GGA og GGK.
    For GGA kan alt og sep setjast direkte (NN2000-høgd og geoide frå Kartverket)."""
    k = kind(fields)
    f = list(fields)
    i, j = _POS[k]
    f[i], f[i + 1] = coord_out(lat, True)
    f[j], f[j + 1] = coord_out(lon, False)
    if k == "GGA":
        if alt is not None:
            f[9], f[10] = f"{alt:.3f}", "M"
            if sep is not None:
                f[11], f[12] = f"{sep:.3f}", "M"
        elif dh is not None and f[9]:
            f[9] = f"{float(f[9]) + dh:.3f}"
    elif k == "GGK" and dh is not None and f[11].startswith("EHT"):
        f[11] = f"EHT{float(f[11][3:]) + dh:.3f}"
    return build(f)
