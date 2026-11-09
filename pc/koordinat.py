# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""GRS80 (EUREF89) ↔ UTM, og meridiankonvergens.

Opphav: utm_forward/utm_inverse og konstantane er kopierte frå SNOWMAN Snødjupne, pc/v1.6/terrain.py
(Snowman6230/Snowman-Snowdeept, commit 8a05dc4). Krüger-seriar (Karney 2011), mm-nøyaktig i sona.
"""
import math

_A, _F = 6378137.0, 1 / 298.257222101
_K0 = 0.9996
_n = _F / (2 - _F)
_AR = _A / (1 + _n) * (1 + _n**2 / 4 + _n**4 / 64)
_ALPHA = (_n / 2 - 2 * _n**2 / 3 + 5 * _n**3 / 16, 13 * _n**2 / 48 - 3 * _n**3 / 5, 61 * _n**3 / 240)
_BETA = (_n / 2 - 2 * _n**2 / 3 + 37 * _n**3 / 96, _n**2 / 48 + _n**3 / 15, 17 * _n**3 / 480)
_DELTA = (2 * _n - 2 * _n**2 / 3 - 2 * _n**3, 7 * _n**2 / 3 - 8 * _n**3 / 5, 56 * _n**3 / 15)


def zone_of(lon):
    return int((lon + 180) // 6) + 1


def utm_forward(lat, lon, zone):
    """Breidd/lengd (grader) → (austing, nording) i UTM-sone `zone` (nordlege halvkule)."""
    lon0 = math.radians(zone * 6 - 183)
    phi, lam = math.radians(lat), math.radians(lon) - lon0
    e = math.sqrt(_F * (2 - _F))
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi_, eta_ = math.atan2(t, math.cos(lam)), math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    xi, eta = xi_, eta_
    for j, a in enumerate(_ALPHA, 1):
        xi += a * math.sin(2 * j * xi_) * math.cosh(2 * j * eta_)
        eta += a * math.cos(2 * j * xi_) * math.sinh(2 * j * eta_)
    return 500000 + _K0 * _AR * eta, _K0 * _AR * xi


def utm_inverse(E, N, zone):
    """(austing, nording) i UTM-sone → (breidd, lengd) i grader."""
    xi, eta = N / (_K0 * _AR), (E - 500000) / (_K0 * _AR)
    xi_, eta_ = xi, eta
    for j, b in enumerate(_BETA, 1):
        xi_ -= b * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
        eta_ -= b * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
    chi = math.asin(math.sin(xi_) / math.cosh(eta_))
    phi = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(_DELTA, 1))
    lon = math.radians(zone * 6 - 183) + math.atan2(math.sinh(eta_), math.cos(xi_))
    return math.degrees(phi), math.degrees(lon)


def convergence(lat, lon, zone):
    """Meridiankonvergens γ (grader): rutenett-asimut = sann asimut − γ. Rekna numerisk frå utm_forward."""
    e0, n0 = utm_forward(lat, lon, zone)
    e1, n1 = utm_forward(lat + 1e-4, lon, zone)
    return -math.degrees(math.atan2(e1 - e0, n1 - n0))


def enu_to_grid(dE, dN, gamma):
    """Vektor i sann aust/nord → UTM-rutenett (meter, skalafaktoren under 0,04 % er sett bort frå)."""
    g = math.radians(gamma)
    return dE * math.cos(g) - dN * math.sin(g), dN * math.cos(g) + dE * math.sin(g)


# ---- Generell transversal Mercator (NTM og UTM), til bakgrunnsfiler (0.9.19) ----
# Same Krüger-seriar som over, men med fritt val av sentralmeridian, skalafaktor, falsk aust/nord og
# breidd for origo. NTM (EUREF89 NTM sone n): sentralmeridian n + 0,5°, skala 1,0, origo 58° N,
# falsk aust 100 000 m og falsk nord 1 000 000 m (Kartverket).

def _xi_eta(lat, lon, lon0):
    phi, lam = math.radians(lat), math.radians(lon - lon0)
    e = math.sqrt(_F * (2 - _F))
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi_, eta_ = math.atan2(t, math.cos(lam)), math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    xi, eta = xi_, eta_
    for j, a in enumerate(_ALPHA, 1):
        xi += a * math.sin(2 * j * xi_) * math.cosh(2 * j * eta_)
        eta += a * math.cos(2 * j * xi_) * math.sinh(2 * j * eta_)
    return xi, eta


def tm_forward(lat, lon, lon0, k0=1.0, fe=0.0, fn=0.0, lat0=0.0):
    xi, eta = _xi_eta(lat, lon, lon0)
    xi0 = _xi_eta(lat0, lon0, lon0)[0] if lat0 else 0.0
    return fe + k0 * _AR * eta, fn + k0 * _AR * (xi - xi0)


def tm_inverse(E, N, lon0, k0=1.0, fe=0.0, fn=0.0, lat0=0.0):
    xi0 = _xi_eta(lat0, lon0, lon0)[0] if lat0 else 0.0
    xi, eta = (N - fn) / (k0 * _AR) + xi0, (E - fe) / (k0 * _AR)
    xi_, eta_ = xi, eta
    for j, b in enumerate(_BETA, 1):
        xi_ -= b * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
        eta_ -= b * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
    chi = math.asin(math.sin(xi_) / math.cosh(eta_))
    phi = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(_DELTA, 1))
    return math.degrees(phi), lon0 + math.degrees(math.atan2(math.sinh(eta_), math.cos(xi_)))


def ntm_forward(lat, lon, sone):
    return tm_forward(lat, lon, sone + 0.5, 1.0, 100000.0, 1000000.0, 58.0)


def ntm_inverse(E, N, sone):
    return tm_inverse(E, N, sone + 0.5, 1.0, 100000.0, 1000000.0, 58.0)
