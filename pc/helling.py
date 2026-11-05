# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Hellingskorreksjon for georadar (IDS Stream C): GNSS-antenna står på ein mast over radaren. Når radaren
hallar, står antenna ikkje rett over referansepunktet på radaren, og posisjonen til OneVision blir forskoven.

Opphav: lesinga av hellingsmeldingar (Helling.feed) er kopiert frå SNOWMAN Snødjupne, pc/v1.6/helling.py
(Snowman6230/Snowman-Snowdeept, commit 8a05dc4). Same forteikn som der: stamp + = fronten opp,
krenging + = høgre side ned. Korreksjonen er utvida til full 3D-spakarm (fram, høgre, opp), sidan antenna
på ein georadar ikkje alltid står midt over referansepunktet.

Koordinatar: lokalt aust–nord–opp (ENU). Kropp: x fram, y høgre, z opp.
  Antenna A = P + Lx·f + Ly·r + Lz·u   ⇒   P = A − (Lx·f + Ly·r + Lz·u)
der P er referansepunktet på radaren, L = spakarmen frå P til antennefasesenteret, og f, r, u er
fram-, høgre- og opp-vektoren til radaren rekna frå kurs ψ, stamp θ og krenging φ.

Feilen utan korreksjon er om lag h·sin(helling): 1,7 cm per grad ved h = 1,0 m. 5° gir 9 cm sidelengs.

Djupn (same prinsipp som snødjupna i Snødjupne – posisjon og høgd blir begge retta etter hellinga):
Radaren står på bakken. Når bakken hallar, er avstanden til eit objekt målt vinkelrett på bakken (langs −u), ikkje
loddrett. OneVision reknar som om vogna står vatrett, så eit objekt på djupn d blir plassert d·sin(helling) feil
sidelengs, mot oppsida av hellinga. Saman med masta:
    total feil ≈ (h_mast + d)·sin(helling)    –  5° og 1,2 m mast: 10 cm ved overflata, 32 cm på 2,5 m djupn.
Masta kan rettast i sanntid (éin posisjon per skann). Djupnfeilen er ulik for kvart objekt og blir retta etterpå
(korriger_objekt.py), eller for éi valt djupn i sanntid (djupn_sanntid i oppsettet).
"""
import math
import time
from collections import deque

ANT_FRESH = 1.0   # sekund: så lenge er ei hellingsmåling gyldig (georadaren blir køyrd i 1–10 Hz)
MAX_TILT = 35.0   # grader: meir enn dette er ikkje truverdig for ein georadar på bakken

# WGS84 / GRS80 (EUREF89 brukar GRS80, skilnaden er utan betydning her)
_A = 6378137.0
_E2 = 6.69438002290e-3


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def meter_per_grad(lat):
    """(meter per grad breidd, meter per grad lengd) ved breidda lat – krumningsradiane til ellipsoiden."""
    s = math.sin(math.radians(lat))
    w = math.sqrt(1 - _E2 * s * s)
    m = _A * (1 - _E2) / w ** 3      # meridian
    n = _A / w                        # tverrkrumning
    return math.radians(1) * m, math.radians(1) * n * math.cos(math.radians(lat))


class Helling:
    """Siste hellingsmåling (stamp, krenging, kurs) frå mottakaren eller ein eigen IMU, og kurs frå GNSS-sporet."""

    def __init__(self):
        self.ant = None                  # {roll, pitch, heading, t, src}
        self.sentences = set()           # kva hellingsmeldingar som er sett
        self.track = deque(maxlen=50)    # (t, lat, lon) – til kurs frå sporet
        self.cog = None                  # siste kurs frå sporet (grader)

    # ---------- hellingsmeldingar (kopiert frå SNOWMAN Snødjupne) ----------
    def feed(self, line, now=None):
        """Les ei NMEA-linje. Returnerer True om ho hadde helling."""
        if not line.startswith("$"):
            return False
        body = line[1:].split("*")[0]
        p = body.split(",")
        tag = p[0]
        roll = pitch = hdg = None
        if tag.endswith("HPR") and len(p) >= 5:  # $GNHPR,tid,kurs,stamp,krenging,...
            hdg, pitch, roll, src = _f(p[2]), _f(p[3]), _f(p[4]), tag
        elif tag == "PSAT" and len(p) >= 6 and p[1] == "HPR":  # $PSAT,HPR,tid,kurs,stamp,krenging,...
            hdg, pitch, roll, src = _f(p[3]), _f(p[4]), _f(p[5]), "PSAT,HPR"
        elif tag == "PASHR" and len(p) >= 6:  # $PASHR,tid,kurs,T,krenging,stamp,...
            hdg, roll, pitch, src = _f(p[2]), _f(p[4]), _f(p[5]), "PASHR"
        elif tag == "PTNL" and len(p) >= 8 and p[1] == "AVR":  # $PTNL,AVR,tid,kurs,Yaw,stamp,Tilt,krenging,Roll,...
            hdg, pitch, roll, src = _f(p[3]), _f(p[5]), _f(p[7]), "PTNL,AVR"
        else:
            return False
        if roll is None or pitch is None:
            return False
        self.ant = {"roll": roll, "pitch": pitch, "heading": hdg,
                    "t": time.time() if now is None else now, "src": src}
        self.sentences.add(src)
        return True

    def fresh(self, now=None):
        now = time.time() if now is None else now
        return self.ant is not None and now - self.ant["t"] < ANT_FRESH

    # ---------- kurs frå sporet ----------
    def add_position(self, lat, lon, now=None, min_dist=0.5):
        """Kurs frå GNSS-sporet. Georadaren går sakte, så kursen blir først rekna når han har flytta seg min_dist m."""
        now = time.time() if now is None else now
        self.track.append((now, lat, lon))
        my, mx = meter_per_grad(lat)
        for t, la, lo in reversed(self.track):
            if now - t > 10:
                break
            dE, dN = (lon - lo) * mx, (lat - la) * my
            if math.hypot(dE, dN) >= min_dist:
                self.cog = math.degrees(math.atan2(dE, dN)) % 360
                break
        return self.cog

    def heading(self, cfg):
        """Kurs til korreksjonen: frå IMU/mottakar om han sender kurs og cfg ber om det, elles frå sporet."""
        if cfg.get("kurs_kjelde", "auto") in ("auto", "imu") and self.ant and self.ant.get("heading") is not None:
            return self.ant["heading"], "imu"
        return self.cog, "spor"


def unit_vectors(heading, pitch, roll):
    """Fram-, høgre- og opp-vektor (ENU) for radaren. Grader. stamp + = fronten opp, krenging + = høgre side ned."""
    psi, th, ph = map(math.radians, (heading, pitch, roll))
    f = (math.sin(psi) * math.cos(th), math.cos(psi) * math.cos(th), math.sin(th))
    r0 = (math.cos(psi), -math.sin(psi), 0.0)
    u0 = (-math.sin(psi) * math.sin(th), -math.cos(psi) * math.sin(th), math.cos(th))
    r = tuple(math.cos(ph) * a - math.sin(ph) * b for a, b in zip(r0, u0))
    u = tuple(math.sin(ph) * a + math.cos(ph) * b for a, b in zip(r0, u0))
    return f, r, u


def offset_enu(lever, heading, pitch, roll):
    """Vektoren frå referansepunktet P til antenna A i ENU (meter). lever = (fram, høgre, opp) i meter."""
    f, r, u = unit_vectors(heading, pitch, roll)
    lx, ly, lz = lever
    return tuple(lx * a + ly * b + lz * c for a, b, c in zip(f, r, u))


def correct(lat, lon, h, lever, heading, pitch, roll):
    """Referansepunktet på radaren: (lat, lon, høgd, horisontal forskyving i m). h er antennehøgda (ellipsoidisk
    eller ortometrisk – same slag kjem ut). Utan helling og med lever = (0, 0, h_mast) blir P rett under A."""
    dE, dN, dU = offset_enu(lever, heading, pitch, roll)
    my, mx = meter_per_grad(lat)
    return lat - dN / my, lon - dE / mx, (None if h is None else h - dU), math.hypot(dE, dN)


def correct_level(lat, lon, h, lever, heading, pitch, roll):
    """«Rett antenne»: der antenna ville stått om radaren var vatrett, med same referansepunkt og kurs.
    Brukast når OneVision sjølv har antenneoppsettet (høgd og forskyving) for vogna – då kan det stå urørt,
    og OneVision får ein posisjon som om vogna aldri hallar. Returnerer (lat, lon, høgd, horisontal forskyving i m)."""
    dE, dN, dU = offset_enu(lever, heading, pitch, roll)       # P → A slik vogna faktisk står
    lE, lN, lU = offset_enu(lever, heading, 0.0, 0.0)          # P → A om vogna var vatrett
    my, mx = meter_per_grad(lat)
    cE, cN, cU = lE - dE, lN - dN, lU - dU
    return lat + cN / my, lon + cE / mx, (None if h is None else h + cU), math.hypot(cE, cN)


def object_shift(depth, heading, pitch, roll):
    """Kor mykje eit objekt som OneVision har lagt loddrett under radaren på djupn `depth`, eigentleg ligg
    forskove: (dE, dN, loddrett djupn) i meter, ENU. Objektet ligg i P − depth·u (vinkelrett på bakken)."""
    f, r, u = unit_vectors(heading, pitch, roll)
    return -depth * u[0], -depth * u[1], depth * u[2]


def tilt_from(hel, cfg, now=None):
    """(stamp, krenging, kjelde) med kalibrering og forteiknsbyte frå cfg, eller None om ingen fersk måling."""
    if not hel.fresh(now):
        return None
    a = hel.ant
    pitch = (-a["pitch"] if cfg.get("snu_stamp") else a["pitch"]) - cfg.get("stamp_null", 0.0)
    roll = (-a["roll"] if cfg.get("snu_krenging") else a["roll"]) - cfg.get("krenging_null", 0.0)
    if abs(pitch) > MAX_TILT or abs(roll) > MAX_TILT:
        return None
    return pitch, roll, a["src"]
