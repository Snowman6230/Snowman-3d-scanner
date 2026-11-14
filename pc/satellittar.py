# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Satellittar per system (0.9.25, ønske frå Hans Petter 14.11.2026): GPS, GLONASS, Galileo, BeiDou og QZSS.

To NMEA-setningar gir dette:
  $--GSV  satellittar i sikte. Talker-ID-en seier systemet (GP, GL, GA, GB/BD, GQ). Felt 3 er talet i sikte.
          NMEA 4.10 har signal-ID til slutt: same satellitt kan då kome i fleire rekkjer (L1, L2 …),
          så vi tek det største talet per system.
  $--GSA  satellittane som er brukte i løysinga (inntil 12 PRN per linje). NMEA 4.10 har system-ID i
          siste felt (1 GPS, 2 GLONASS, 3 Galileo, 4 BeiDou, 5 QZSS, 6 NavIC). Utan system-ID og med
          talker GN blir systemet funne frå PRN-nummeret (Trimble/NMEA-område).

R12i sender GSV og GSA berre når dei er slått på for porten (I/O Configuration → NMEA). Setningane går
uendra vidare; til OneVision blir uansett berre GGA sendt (ut_seriell → setningar).
"""
import time

SYSTEM = ("GPS", "GLONASS", "Galileo", "BeiDou", "QZSS", "NavIC")
KORT = {"GPS": "GPS", "GLONASS": "GLO", "Galileo": "GAL", "BeiDou": "BDS", "QZSS": "QZS", "NavIC": "IRN"}
TALKER = {"GP": "GPS", "GL": "GLONASS", "GA": "Galileo", "GB": "BeiDou", "BD": "BeiDou", "GQ": "QZSS",
          "QZ": "QZSS", "GI": "NavIC", "IR": "NavIC"}
SYSID = {"1": "GPS", "2": "GLONASS", "3": "Galileo", "4": "BeiDou", "5": "QZSS", "6": "NavIC"}
GAMAL = 5.0      # s: eldre data enn dette tel ikkje med


def system_frå_prn(prn):
    """Systemet frå PRN-nummeret når setninga ikkje seier det (GNGSA utan system-ID)."""
    if 1 <= prn <= 32:
        return "GPS"
    if 33 <= prn <= 64:
        return None          # SBAS – ikkje eit eige system her
    if 65 <= prn <= 96:
        return "GLONASS"
    if 193 <= prn <= 200:
        return "QZSS"
    if 201 <= prn <= 264 or 401 <= prn <= 437:
        return "BeiDou"
    if 301 <= prn <= 336:
        return "Galileo"
    return None


def _felt(line):
    return line.split("*")[0].split(",")


class Satellittar:
    def __init__(self):
        self.sikte = {}      # (system, signal) → (tal, t)
        self.bruk = {}       # system → (set av PRN, t)

    def feed(self, line, now=None):
        """Ta imot ei GSV- eller GSA-linje. Gir True om linja vart brukt."""
        t = time.time() if now is None else now
        typ = line[3:6]
        f = _felt(line)
        talker = f[0][1:3].upper()
        if typ == "GSV":
            sys = TALKER.get(talker)
            if not sys or len(f) < 4 or not f[3].strip().isdigit():
                return False
            # Etter blokkene på 4 felt kan det stå ein signal-ID (NMEA 4.10)
            rest = len(f) - 4
            signal = f[-1] if rest % 4 == 1 else ""
            self.sikte[(sys, signal)] = (int(f[3]), t)
            return True
        if typ == "GSA":
            if len(f) < 15:
                return False
            prn = [int(x) for x in f[3:15] if x.strip().isdigit()]
            sysid = f[18].strip() if len(f) > 18 else ""
            fast = SYSID.get(sysid) or (TALKER.get(talker) if talker != "GN" else None)
            if fast:
                grupper = {fast: set(prn)}
            else:
                grupper = {}
                for p in prn:
                    s = system_frå_prn(p)
                    if s:
                        grupper.setdefault(s, set()).add(p)
            for s, ps in grupper.items():
                # Fleire GSA-linjer for same system i same epoke: legg saman, elles byt ut
                gml = self.bruk.get(s)
                self.bruk[s] = ((gml[0] | ps) if gml and t - gml[1] < 0.15 else ps, t)
            return True
        return False

    def status(self, now=None):
        """{"system": [{"namn", "kort", "sikte", "bruk"}], "sikte": sum, "bruk": sum, "alder": s} eller None."""
        t = time.time() if now is None else now
        sikte, bruk, siste = {}, {}, None
        for (s, _sig), (n, ts) in self.sikte.items():
            if t - ts <= GAMAL:
                sikte[s] = max(sikte.get(s, 0), n)
                siste = ts if siste is None else max(siste, ts)
        for s, (ps, ts) in self.bruk.items():
            if t - ts <= GAMAL:
                bruk[s] = len(ps)
                siste = ts if siste is None else max(siste, ts)
        if siste is None:
            return None
        liste = [{"namn": s, "kort": KORT[s], "sikte": sikte.get(s), "bruk": bruk.get(s)}
                 for s in SYSTEM if s in sikte or s in bruk]
        return {"system": liste, "har_gsv": bool(sikte), "har_gsa": bool(bruk),
                "sikte": sum(sikte.values()) if sikte else None, "bruk": sum(bruk.values()) if bruk else None,
                "alder": round(t - siste, 1)}
