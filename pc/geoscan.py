# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Snowman Geoscan – hellingskorrigert GNSS-posisjon til IDS Stream C (OneVision).

    mottakar (NMEA: GGA + helling) ──┐
    eigen IMU (valfri, PASHR o.l.) ──┼─► geoscan.py ─► korrigert NMEA ─┬─► seriell (com0com) → OneVision
                                     ┘                                 └─► TCP (port 5000) → andre program

Med NTRIP på hentar programmet korreksjonar og sender RTCM til mottakaren (ntrip_teneste.py), så Trimble Access
ikkje trengst. Elles blir ingenting sendt til mottakaren. Alle setningar utan posisjon går vidare uendra.
Posisjonen i GGA, RMC, GLL og PTNL,GGK blir retta for hellinga til vogna (sjå helling.py).

Køyr:  python geoscan.py                      (brukar geoscan_config.json ved sida av)
       python geoscan.py --fil opptak.nmea    (spel av ei fil, skriv korrigert NMEA til skjermen)
"""
import argparse
import json
import math
from collections import deque
import re
import socket
import sys
import threading
import time
from pathlib import Path

import helling as H
import koordinat as K
import nmea as N
from geoide import GEOID

HER = Path(__file__).resolve().parent
VERSJON = "0.9.24"
from opphav import NAMN, PRODUSENT, SIGNATUR   # namnet og opphavet (sjå opphav.py)
STANDARD = {
    "inn": [{"port": "COM23", "baud": 115200}],
    "ut_seriell": [{"port": "COM34", "baud": 115200, "setningar": ["GGA"]}],
    "tema": "mork",               # skjermtema: mork eller dagslys (høg kontrast for sollys)
    "kartlag": "topo",            # bakgrunnskart i Resultat: topo, graatone, flyfoto eller osm
    "tcp_port": 5000,
    "spakarm": {"fram": 0.0, "hogre": -0.60, "opp": 1.808},  # Norman: GPS 0,6 m til venstre (6.11), 1,808 m til undersida av hurtigfestet (9.11)
    "utgang": "rett_antenne",
    "mottakar_kompenserer": False,
    "djupn_sanntid": 0.0,
    "radar_djupn": 2.5,
    "apc_tillegg": 0.179,        # m, undersida av hurtigfestet → fasesenteret i R12i (Access 9.11.2026). Mastehøgda
                                 # er målt til undersida av hurtigfestet, same som stanghøgda i Trimble Access
    "spiss_over_bakken": 0.09,   # m, spissen av stonga står i GPS-støtta på ramma, 9 cm over bakken (Norman 9.11.2026)
    "streamc_xy": [0.13, 0.42],  # m, x fram frå enkoderen (venstre bakhjul), y sidevegs – målt av Norman 9.11.2026,
                                 # same som IDS-malen for standard GPS-støtte (bak til venstre)
    "vakt": {"qh_cm": 5.0, "qv_cm": 8.0, "alder_s": 2.0},   # grenser for kvalitetsvakta (raud stripe og lyd)
    "skannebreidd": 0.96,        # m, Stream C: IDS oppgir 96 cm, og objekt i .svy (7.11.2026) går ±0,479 m – stripa på karta
    "skannebreidd_ytre": 0.0,    # m, valfritt lysare felt utanfor stripa (0 = ingen)
    "onevision_mappe": "",       # arbeidsmappa i OneVision (tom = finn sjølv, sjå onevision_filer.py)
    "sone": "32",
    "hoegd": "nn2000",
    "kurs_kjelde": "auto",
    "stamp_null": 0.0, "krenging_null": 0.0, "snu_stamp": False, "snu_krenging": False,
    "utan_helling": "send_ukorrigert",
    "logg": "logg",
    "opptak": True,
    "status_port": 8088,
    "status_lan": False,
    "sjekk_oppdatering": True,
    "opne_nettlesar": True,
    "vis_oppstartlogo": True,
    "statuslinje_sek": 60,
    "ntrip": {"pa": False, "rtcm_til": None, "gga_intervall": 10},
}


LOGG_HOVUD = ("tid;fix;lat_inn;lon_inn;lat_ut;lon_ut;sone;E_ut;N_ut;h_nn2000_ut;h_bakke;korrigert;stamp;krenging;kurs;"
              "kurskjelde;djupn_sanntid;forskyving_cm;lat_radar;lon_radar;talker;imu;varsel")


radarmidt = H.radarmidt     # midten av radaren (skannestripa) – sjå helling.py


def dist_en(la1, lo1, la2, lo2):
    my, mx = H.meter_per_grad(la1)
    return (lo2 - lo1) * mx, (la2 - la1) * my


def load_cfg(path):
    cfg = dict(STANDARD)
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg


class Vakt:
    """Kvalitetsvakt (0.9.21): IMU borte, RTK FIX tapt, gamle data og dårleg nøyaktigheit. Eit varsel blir aktivt
    etter 1 s med feil, og går bort etter 2 s utan, så det ikkje blinkar ved kvart lite brot. «nr» aukar for kvart
    nytt varsel, så nettlesaren veit når det skal kome lyd og Windows-varsel."""
    PA, AV = 1.0, 2.0
    TEKST = {
        "imu": "IMU borte – R12i sender ${t}GGA (antenna), ikkje $INGGA. Masta blir ikkje retta for helling.",
        "rtk": "RTK FIX tapt – fix {q} ({namn}). Posisjonen kan vere fleire cm–m feil.",
        "noy": "Dårleg nøyaktigheit – QH {qh} cm, QV {qv} cm.",
        "alder": "Ingen nye posisjonar på {s} s – sjekk mottakaren og kabelen.",
    }

    def __init__(self, cfg):
        g = cfg.get("vakt") or {}
        self.qh = float(g.get("qh_cm", 5.0))
        self.qv = float(g.get("qv_cm", 8.0))
        self.alder = float(g.get("alder_s", 2.0))
        self.tilstand = {}               # nøkkel → {"feil_sidan", "ok_sidan", "aktiv", "sidan", "tekst"}
        self.nr = 0

    def sjekk(self, nokkel, feil, now, tekst=""):
        t = self.tilstand.setdefault(nokkel, {"feil_sidan": None, "ok_sidan": None, "aktiv": False, "sidan": None})
        if feil:
            t["tekst"] = tekst
            t["ok_sidan"] = None
            t["feil_sidan"] = t["feil_sidan"] or now
            if not t["aktiv"] and now - t["feil_sidan"] >= self.PA:
                t["aktiv"], t["sidan"] = True, now
                self.nr += 1
        else:
            t["feil_sidan"] = None
            t["ok_sidan"] = t["ok_sidan"] or now
            if t["aktiv"] and now - t["ok_sidan"] >= self.AV:
                t["aktiv"] = False

    def aktive(self, now=None):
        now = time.time() if now is None else now
        return [{"kva": k, "tekst": v.get("tekst", ""), "sekund": round(now - (v["sidan"] or now))}
                for k, v in self.tilstand.items() if v["aktiv"]]


FIXNAMN = {0: "ingen", 1: "GPS", 2: "DGPS", 4: "RTK FIX", 5: "RTK FLOAT", 6: "rekna"}


class Korrigerar:
    """Tek imot NMEA-linjer frå alle inngangar, og gir tilbake linjene som skal sendast ut."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.hel = H.Helling()
        self.lever = H.spakarm(cfg)     # opp = mastehøgd + apc_tillegg (til fasesenteret)
        self.lock = threading.Lock()
        self.status = {"fix": None, "sats": None, "stamp": None, "krenging": None, "kurs": None,
                       "kurskjelde": None, "forskyving_cm": None, "korrigert": False, "melding": "ventar på data",
                       "hellingskjelde": None, "geoide": None, "feil_sjekksum": 0}
        self.logfile = None
        self.komp = bool(cfg.get("mottakar_kompenserer"))   # R12i: tilt-kompensasjon i mottakaren
        # Berre $INGGA (INS-løysing med IMU) er stangspissen. $GNGGA/$GPGGA er antennefasesenteret, sjølv om
        # «mottakar_kompenserer» står på (felttest 7.11: R12i direkte på USB sende $GNGGA – IMU ikkje i bruk).
        self.komp_aktiv = False
        self.talker = None
        # «R12i med Trimble Access (IMU)»: Geoscan sender punktet frå R12i urørt (berre høgda i NN2000). Spissen av
        # stonga står i GPS-støtta på ramma, og OneVision flyttar sjølv frå spissen til radaren (Stream C.xml).
        self.urort = cfg.get("gps_oppsett") == "access"
        self.spiss = float(cfg.get("spiss_over_bakken", 0.09) or 0.0)
        # Når IMU-en fell ut og R12i byter til $GNGGA: kor mykje skal trekkjast frå for å kome til spissen?
        # Antenna (stanghøgd + fasesenter) eller 0 (stanghøgda alt trekt frå). Blir målt ved bytet (sjå _gn_hopp).
        # Startar R12i med $GNGGA (IMU slått av i Access), sender han antenna (9.11 kl. 08:52). Fell IMU-en ut
        # medan R12i sender $INGGA, held han fram med spissen (11.11: hopp +0,003 / +0,010 / +0,003 m) – sjå _urort.
        self.gn_red = {"m": self.lever[2], "kjelde": "antatt: IMU av frå start – R12i sender antenna (9.11 kl. 08:52)"}
        self.siste_epoke = None          # (talker, h_ell, fix, t) – førre GGA, til å måle hoppet ved IN/GN-byte
        self.vakt = Vakt(cfg)
        self.epoker = {}                 # UTC-tid → posisjon frå mottakaren (til samanlikning med PJK)
        self.zone = int(cfg["sone"]) if str(cfg.get("sone", "auto")).isdigit() else None
        if cfg.get("logg"):
            d = HER / cfg["logg"]
            d.mkdir(exist_ok=True)
            self.logfile = open(d / time.strftime("geoscan_%Y%m%d_%H%M%S.csv"), "a", encoding="utf-8")
            self.logfile.write(LOGG_HOVUD + "\n")

    def handle(self, line, now=None):
        line = line.strip()
        if not line.startswith("$"):
            return []
        if not N.valid(line):
            self.status["feil_sjekksum"] += 1
            return []
        with self.lock:
            if line[3:6] == "GST":          # nøyaktigheit (1 σ) frå mottakaren, som QH/QV i Xsite
                self._gst(line)
                return [line]
            if line.startswith("$PTNL,PJK,"):   # koordinatane i Trimble Access-jobben – til kontroll under Fix
                self._pjk(line)
                return [line]
            if line.startswith("$PTNL,GGK,"):   # DOP og ellipsoidehøgd frå Trimble (posisjonen blir retta vidare)
                self._ggk(line)
            if self.hel.feed(line, now):
                return [line]
            fields = N.split(line)
            k = N.kind(fields)
            if not k:
                return [line]
            pos = N.position(fields)
            if pos is None:
                return [line]
            return [self._correct(fields, k, pos, now)]

    def _gst(self, line):
        """$--GST,tid,rms,σmaj,σmin,orient,σlat,σlon,σhøgd: standardavvik i meter (1 σ). Vi viser QH = √(σlat²+σlon²)
        og QV = σhøgd i cm. R12i sender GST når han er slått på for porten (I/O Configuration → NMEA → GST)."""
        f = line.split("*")[0].split(",")
        try:
            la, lo, al = float(f[6]), float(f[7]), float(f[8])
        except (IndexError, ValueError):
            return
        self.status["noy"] = {"qh_cm": round(math.hypot(la, lo) * 100, 1), "qv_cm": round(al * 100, 1),
                              "t": time.time()}

    def _pjk(self, line):
        """$PTNL,PJK,tid,dato,nord,N,aust,E,kvalitet,sat,DOP,høgd,M. Nord og aust er i koordinatsystemet til jobben i
        Trimble Access (UTM, NTM …). Høgda er ellipsoidisk når ho byrjar med «EHT», elles frå jobben (geoide i Access).
        Blir samanlikna med Geoscan sin eigen posisjon for same tidspunkt (GGA med same UTC-tid)."""
        f = line.split("*")[0].split(",")
        try:
            nord, aust = float(f[4]), float(f[6])
        except (IndexError, ValueError):
            return
        hs = f[11] if len(f) > 11 else ""
        eht = hs.upper().startswith("EHT")
        try:
            h = float(hs[3:] if eht else hs) if hs else None
        except ValueError:
            h = None
        q = int(f[8]) if len(f) > 8 and f[8].isdigit() else None
        d = {"nord": nord, "aust": aust, "h": h, "eht": eht, "q": q, "sats": f[9] if len(f) > 9 else None,
             "dop": f[10] if len(f) > 10 else None, "tid": f[2], "t": time.time()}
        e = self.epoker.get(f[2])
        if e:                                  # same epoke: avvik mot Geoscan (UTM + NN2000/ellipsoide)
            dn, de = nord - e["N"], aust - e["E"]
            d["avvik_h_cm"] = round(math.hypot(dn, de) * 100, 1) if abs(dn) < 1000 and abs(de) < 1000 else None
            ref = e["h_ell"] if eht else e["h_nn"]
            d["avvik_v_cm"] = None if (h is None or ref is None or d["avvik_h_cm"] is None) else round((h - ref) * 100, 1)
            d["sone"] = e["sone"]
        self.status["pjk"] = d

    def _ggk(self, line):
        f = line.split("*")[0].split(",")
        try:
            self.status["ggk"] = {"q": int(f[8]) if f[8] else None, "dop": float(f[10]) if f[10] else None,
                                  "eht": float(f[11][3:]) if f[11].upper().startswith("EHT") else None, "t": time.time()}
        except (IndexError, ValueError):
            pass

    def _epoke(self, tid, lat, lon, h_ell):
        """Hugs posisjonen frå mottakaren (slik han kom inn) per UTC-tid, så PJK kan samanliknast med rett epoke."""
        if not tid:
            return
        try:
            z = self.zone or K.zone_of(lon)
            E, Nn = K.utm_forward(lat, lon, z)
            n = GEOID.n(lat, lon) if self.cfg.get("hoegd") == "nn2000" else None
        except Exception:
            return
        self.epoker[tid] = {"E": E, "N": Nn, "sone": z, "h_ell": h_ell,
                            "h_nn": None if (h_ell is None or n is None) else h_ell - n}
        while len(self.epoker) > 50:
            self.epoker.pop(next(iter(self.epoker)))

    def _correct(self, fields, k, pos, now):
        lat, lon = pos
        cfg, st = self.cfg, self.status
        gga = N.parse_gga(fields) if k == "GGA" else None
        if gga:
            self.talker = (fields[0] or "")[:2].upper()
            self.komp_aktiv = self.komp and self.talker == "IN"
            st.update(fix=gga["q"], sats=gga["sats"], talker=self.talker)
            try:
                st["hdop"] = float(fields[8])
            except (IndexError, ValueError):
                st["hdop"] = None
            self.hel.add_position(lat, lon, now)
            self._korreksjon(fields, now)
            self._vakt(gga, now)
        if self.urort:
            return self._urort(fields, gga, lat, lon, now)
        tilt = H.tilt_from(self.hel, cfg, now)
        hdg, hsrc = self.hel.heading(cfg)
        st.update(kurs=None if hdg is None else round(hdg, 1), kurskjelde=hsrc)
        if tilt is None or hdg is None:
            st.update(korrigert=False, stamp=None, krenging=None, forskyving_cm=None,
                      melding="ingen fersk helling" if tilt is None else "ventar på kurs (køyr nokre meter)")
            if self.komp_aktiv:
                st["melding"] = "masta retta i mottakaren (stangspiss)" + ("" if tilt is None else ", ventar på kurs")
            elif self.komp and self.talker:
                st["melding"] = (f"mottakaren sender antenneposisjon (${self.talker}GGA), ikkje stangspiss ($INGGA) "
                                 "– masta blir ikkje retta for helling. Slå på IMU i R12i, eller bruk ekstra hellingsmålar")
            elif cfg.get("utan_helling") == "stopp":
                return None
            pitch = roll = 0.0          # vatrett – gir same punkt som OneVision ville rekna sjølv
        else:
            pitch, roll, src = tilt
            st.update(korrigert=True, stamp=round(pitch, 2), krenging=round(roll, 2), hellingskjelde=src,
                      melding="korrigerer")
        lever = self.lever
        if hdg is None:                 # utan kurs kan ikkje forskyving fram/høgre leggjast i rett retning
            hdg, lever = 0.0, (0.0, 0.0, self.lever[2])
        d0 = float(cfg.get("djupn_sanntid") or 0.0) if st["korrigert"] else 0.0
        h_in = None
        if gga:
            h_in = None if gga["alt"] is None else gga["alt"] + (gga["sep"] or 0.0)   # ellipsoidisk høgd
            self._epoke(fields[1], lat, lon, h_in)
        la, lo, h2, off = self._point(lat, lon, 0.0 if h_in is None else h_in, lever, hdg, pitch, roll, d0)
        if not gga:
            return N.rewrite(fields, la, lo, dh=h2)
        if h_in is None:
            h2 = None
        n_geo = GEOID.n(la, lo) if cfg.get("hoegd") == "nn2000" else None
        st["geoide"] = None if n_geo is None else round(n_geo, 3)
        if n_geo is not None and h2 is not None:
            out = N.rewrite(fields, la, lo, alt=h2 - n_geo, sep=n_geo)
        else:
            out = N.rewrite(fields, la, lo, dh=None if h2 is None else h2 - h_in)
        st["forskyving_cm"] = round(off * 100, 1) if st["korrigert"] else None
        lat_r, lon_r = self.radarmidt(la, lo, st["kurs"])
        # Live-kartet på Status: posisjonen frå mottakaren og den retta posisjonen som blir sendt til OneVision
        st["pos"] = {"lat": round(lat, 8), "lon": round(lon, 8), "lat_ut": round(la, 8), "lon_ut": round(lo, 8),
                     "fix": gga["q"], "kurs": st["kurs"], "stamp": st["stamp"], "krenging": st["krenging"],
                     "korrigert": st["korrigert"], "t": round(now if now is not None else time.time(), 2),
                     "lat_r": None if lat_r is None else round(lat_r, 8), "lon_r": None if lon_r is None else round(lon_r, 8)}
        # Koordinatane til punktet som blir sendt til OneVision (UTM/EUREF89 og høgd), til kontroll på Status
        try:
            z = self.zone or K.zone_of(lo)
            E, Nn = K.utm_forward(la, lo, z)
            # Bakken: frå antenna ned masta (til spissen i støtta) og vidare spiss_over_bakken (9 cm) ned til bakken
            mast = (self.lever[2] if cfg.get("utgang") == "rett_antenne" else 0.0) + self.spiss
            h_nn = None if (h2 is None or n_geo is None) else h2 - n_geo
            st["pos"].update({"sone": z, "E": round(E, 3), "N": round(Nn, 3),
                              "h_ell": None if h2 is None else round(h2, 3),
                              "h_nn": None if h_nn is None else round(h_nn, 3),
                              "h_bakke": None if h_nn is None else round(h_nn - mast, 3)})
        except Exception:
            pass
        self._log(gga, lat, lon, la, lo, h2, n_geo, pitch, roll, hdg, d0, now, lat_r, lon_r)
        return out

    def oppsett_varsel(self):
        """Faste feil i oppsettet som gjer høgda feil (ikkje kortvarige – dei er i Vakt)."""
        ut = []
        if self.urort:
            opp = float((self.cfg.get("spakarm") or {}).get("opp", 0) or 0)
            if opp < 0.5:
                ut.append(f"Mastehøgda står på {opp:g} m. Set ho til stanghøgda i Trimble Access (1,808 m). Geoscan "
                          "treng ho når IMU-en fell ut og R12i sender antenna.")
            if float(self.cfg.get("apc_tillegg", 0.179) or 0) == 0:
                ut.append("«Frå undersida av hurtigfestet til fasesenteret» står på 0. For R12i skal det vere 0,179 m.")
        return ut

    def _korreksjon(self, fields, now):
        """Alderen på korreksjonane frå GGA (felt 13, sekund sidan siste RTCM). Han går ned att kvar gong ein ny
        korreksjon kjem fram til mottakaren, same om han kjem frå Trimble Access (Bluetooth) eller frå Geoscan
        (USB). Det gir aktivitetsstolpen på statussida, som NTRIP-stolpen i Xsite (ønske frå Norman 12.11). 0.9.24"""
        t = time.time() if now is None else now
        try:
            a = float(fields[13]) if len(fields) > 13 and fields[13] else None
        except ValueError:
            a = None
        k = self.status.setdefault("korreksjon", {"alder": None, "nye": 0, "ny_t": None})
        forrige = k["alder"]
        if a is not None and (forrige is None or a < forrige - 0.05):
            k["nye"] += 1
            k["ny_t"] = round(t, 2)
        k["alder"] = a

    def _vakt(self, gga, now):
        t = time.time() if now is None else now
        V = self.vakt
        venta_imu = self.urort or self.komp
        V.sjekk("imu", bool(venta_imu and self.talker and self.talker != "IN"), t,
                V.TEKST["imu"].replace("${t}", "$" + (self.talker or "??")))
        q = gga["q"]
        V.sjekk("rtk", q != 4, t, V.TEKST["rtk"].format(q=q, namn=FIXNAMN.get(q, "ukjend")))
        n = self.status.get("noy")
        darleg = bool(n and time.time() - n["t"] < 5 and (n["qh_cm"] > V.qh or n["qv_cm"] > V.qv))
        V.sjekk("noy", darleg, t, V.TEKST["noy"].format(qh=n["qh_cm"], qv=n["qv_cm"]) if n else "")

    def _gn_hopp(self, talker, h_in, q, t):
        """Mål hoppet i høgd når R12i byter mellom $INGGA (spissen) og $GNGGA. Hoppar høgda om lag mast + 0,179 m,
        sender R12i antenna utan IMU, og Geoscan må trekkje det frå. Held ho seg, er stanghøgda alt trekt frå."""
        p = self.siste_epoke
        if not p or h_in is None or p[1] is None or (p[0] == "IN") == (talker == "IN"):
            return
        if t - p[3] > 1.0 or q not in (2, 4, 5) or p[2] not in (2, 4, 5) or 4 not in (q, p[2]):
            return                      # RTK FIX på minst éi side, DGPS/FLOAT på den andre, og kort tid mellom (0.9.23)
        dh = h_in - p[1] if talker != "IN" else p[1] - h_in     # GN-høgd minus IN-høgd
        A = self.lever[2]
        if abs(dh - A) < 0.25:
            self.gn_red = {"m": A, "kjelde": f"målt: hopp {dh:+.2f} m – R12i sender antenna utan IMU"}
        elif abs(dh) < 0.25:
            self.gn_red = {"m": 0.0, "kjelde": f"målt: hopp {dh:+.2f} m – stanghøgda er alt trekt frå"}
        else:
            self.gn_red = dict(self.gn_red, kjelde=f"uklart hopp {dh:+.2f} m – brukar {self.gn_red['m']:.2f} m som før")

    def _urort(self, fields, gga, lat, lon, now):
        """«R12i med Trimble Access (IMU)»: punktet går urørt vidare. Høgda blir framleis gjort om til NN2000 med
        geoiden frå Kartverket (mottakaren brukar ein annan geoide – 9.11 var skilnaden 0,44 m)."""
        cfg, st = self.cfg, self.status
        if not gga:
            return N.rewrite(fields, lat, lon)
        t = time.time() if now is None else now
        talker = self.talker or ""
        h_in = None if gga["alt"] is None else gga["alt"] + (gga["sep"] or 0.0)
        p = self.siste_epoke
        if talker != "IN" and p and p[0] == "IN" and self.gn_red["kjelde"].startswith("antatt"):
            # IMU-en fall ut medan R12i sende spissen: han held fram med spissen (stanghøgda trekt frå). Målt 11.11.2026
            # på grusbana ved Velledalen grendahus, tre byte IN → GN med hopp på +0,003, +0,010 og +0,003 m. 0.9.23
            self.gn_red = {"m": 0.0, "kjelde": "antatt: IMU fall ut – R12i held fram med spissen (målt 11.11)"}
        self._gn_hopp(talker, h_in, gga["q"], t)
        red = 0.0 if talker == "IN" else self.gn_red["m"]
        h2 = None if h_in is None else h_in - red
        self._epoke(fields[1], lat, lon, h2)
        n_geo = GEOID.n(lat, lon) if cfg.get("hoegd") == "nn2000" else None
        st["geoide"] = None if n_geo is None else round(n_geo, 3)
        if n_geo is not None and h2 is not None:
            out = N.rewrite(fields, lat, lon, alt=h2 - n_geo, sep=n_geo)
        else:
            out = N.rewrite(fields, lat, lon, dh=-red if red else None)
        hdg, hsrc = self.hel.heading(cfg)
        st.update(kurs=None if hdg is None else round(hdg, 1), kurskjelde=hsrc, korrigert=False, stamp=None,
                  krenging=None, forskyving_cm=None, gn_reduksjon=dict(self.gn_red), urort=True)
        if talker == "IN":
            st["melding"] = "R12i rettar masta (IMU) – punktet går urørt til OneVision"
        else:
            st["melding"] = (f"IMU borte (${talker}GGA): Geoscan trekkjer frå {red:.2f} m ({self.gn_red['kjelde']}). "
                             "Masta blir ikkje retta for helling sidevegs.")
        lat_r, lon_r = self.radarmidt(lat, lon, st["kurs"])
        st["pos"] = {"lat": round(lat, 8), "lon": round(lon, 8), "lat_ut": round(lat, 8), "lon_ut": round(lon, 8),
                     "fix": gga["q"], "kurs": st["kurs"], "stamp": None, "krenging": None, "korrigert": False,
                     "t": round(t, 2), "lat_r": None if lat_r is None else round(lat_r, 8),
                     "lon_r": None if lon_r is None else round(lon_r, 8)}
        try:
            z = self.zone or K.zone_of(lon)
            E, Nn = K.utm_forward(lat, lon, z)
            h_nn = None if (h2 is None or n_geo is None) else h2 - n_geo
            st["pos"].update({"sone": z, "E": round(E, 3), "N": round(Nn, 3),
                              "h_ell": None if h2 is None else round(h2, 3),
                              "h_nn": None if h_nn is None else round(h_nn, 3),
                              "h_bakke": None if h_nn is None else round(h_nn - self.spiss, 3)})
        except Exception:
            pass
        self._log(gga, lat, lon, lat, lon, h2, n_geo, 0.0, 0.0, hdg or 0.0, 0.0, now, lat_r, lon_r)
        self.siste_epoke = (talker, h_in, gga["q"], t)
        return out

    def radarmidt(self, la, lo, kurs):
        """Midten av radaren (midt i skannestripa), til stripa på karta. Med «rett antenne» er punktet ut antenna,
        og radaren ligg spakarmen (fram, høgre) bak/ved sida av ho. Med «referansepunkt» er punktet ut alt
        midten av radaren. Utan kurs veit vi ikkje kva veg vogna står: None."""
        return radarmidt(la, lo, kurs, self.lever, self.cfg.get("utgang"))

    def _point(self, lat, lon, h, lever, hdg, pitch, roll, d0):
        """Punktet som blir sendt ut: masta retta (referansepunkt eller rett antenne), og om djupn_sanntid er sett,
        flytta vidare dit eit objekt på den djupna eigentleg ligg (berre sidelengs – høgda er framleis overflata)."""
        if self.komp_aktiv:
            # R12i med tilt på og stanghøgd = mastehøgda sender STANGSPISSEN: foten av masta, rett under antenna
            # når vogna står vatrett. Han ligg ikkje midt på radaren, men forskyvd (fram, høgre) frå han.
            # (Retta 7.11.2026: før vart spissen rekna som referansepunktet, og «rett antenne» flytta punktet
            #  ein ekstra gong sidelengs – 0,6 m til venstre for køyreretninga, som byter side når ein snur.)
            if self.cfg.get("utgang") == "rett_antenne":
                # Antenna om vogna var vatrett: rett over stangspissen. Ingen sideflytting.
                la, lo, h2, off = lat, lon, (None if h is None else h + lever[2]), 0.0
            else:
                # Referansepunktet på radaren: stangspissen minus den vassrette delen av spakarmen.
                dE, dN, _ = H.offset_enu((lever[0], lever[1], 0.0), hdg, 0.0, 0.0)
                my, mx = H.meter_per_grad(lat)
                la, lo, h2, off = lat - dN / my, lon - dE / mx, h, (dE * dE + dN * dN) ** 0.5
        else:
            fn = H.correct_level if self.cfg.get("utgang") == "rett_antenne" else H.correct
            la, lo, h2, off = fn(lat, lon, h, lever, hdg, pitch, roll)
        if d0:
            dE, dN, _ = H.object_shift(d0, hdg, pitch, roll)
            my, mx = H.meter_per_grad(la)
            la, lo = la + dN / my, lo + dE / mx
            e0, n0 = dist_en(lat, lon, la, lo)
            off = (e0 * e0 + n0 * n0) ** 0.5
        return la, lo, h2, off

    def _log(self, gga, lat, lon, la, lo, h2, n_geo, pitch, roll, hdg, d0, now, lat_r=None, lon_r=None):
        """Loggen er grunnlaget for å rette objekta etterpå (korriger_objekt.py): kvar posisjon som gjekk til
        OneVision, i UTM, med helling og kurs."""
        if not self.logfile:
            return
        z = self.zone or K.zone_of(lo)
        E, Nn = K.utm_forward(la, lo, z)
        t = time.time() if now is None else now
        st = self.status
        h_nn = "" if (h2 is None or n_geo is None) else f"{h2 - n_geo:.3f}"
        # Høgda på bakken under radaren (referansepunktet): «rett antenne» står spakarmen over bakken
        if self.urort:
            mast = self.spiss          # punktet ut er spissen av stonga på ramma
        else:
            mast = (self.lever[2] if self.cfg.get("utgang") == "rett_antenne" else 0.0) + self.spiss
        h_bakke = "" if h_nn == "" else f"{float(h_nn) - mast:.3f}"
        self.logfile.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))}.{int(t * 1000) % 1000:03d};{gga['q']};"
            f"{lat:.9f};{lon:.9f};{la:.9f};{lo:.9f};{z};{E:.3f};{Nn:.3f};{h_nn};{h_bakke};"
            f"{1 if st['korrigert'] else 0};{pitch:.2f};{roll:.2f};{hdg:.1f};{st['kurskjelde']};{d0:g};"
            f"{st['forskyving_cm'] if st['forskyving_cm'] is not None else ''};"
            f"{'' if lat_r is None else f'{lat_r:.9f}'};{'' if lon_r is None else f'{lon_r:.9f}'};"
            f"{self.talker or ''};{1 if self.talker == 'IN' else 0};"
            f"{','.join(v['kva'] for v in self.vakt.aktive(t))}\n")
        self.logfile.flush()


# ---------- inn og ut ----------
def portnamn(p):
    """«25» eller «com25» → «COM25». Andre namn (/dev/ttyUSB0, socket://…) står urørt."""
    p = str(p or "").strip()
    if re.fullmatch(r"\d{1,3}", p):
        return "COM" + p
    if re.fullmatch(r"(?i)com\d{1,3}", p):
        return p.upper()
    return p


def open_port(spec, write_timeout=None):
    import serial  # pyserial
    url = portnamn(spec["port"])
    return serial.serial_for_url(url, baudrate=int(spec.get("baud", 115200)), timeout=1,
                                 write_timeout=write_timeout)


UT_SKRIVETID = 0.2    # s. Les ikkje OneVision (lukka, heng), blir linja kasta i staden for at alt stoppar.


class Utgangar:
    def __init__(self, cfg):
        self.ports = [{"spec": s, "p": None, "feil": "", "kasta": 0} for s in cfg.get("ut_seriell") or []]
        self.clients, self.lock = [], threading.Lock()
        if cfg.get("tcp_port"):
            threading.Thread(target=self._tcp, args=(int(cfg["tcp_port"]),), daemon=True).start()

    def _tcp(self, port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(5)
        while True:
            c, _ = srv.accept()
            c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            with self.lock:
                self.clients.append(c)

    def send(self, line):
        data = (line + "\r\n").encode("ascii", "replace")
        for o in self.ports:
            # «setningar»: send berre desse til porten, t.d. ["GGA"] til OneVision (les berre GGA). Tom = alt.
            berre = o["spec"].get("setningar")
            if berre and not (line.startswith("$") and line[3:6] in berre):
                continue
            try:
                if o["p"] is None:
                    o["p"] = open_port(o["spec"], UT_SKRIVETID)
                    o["feil"] = ""
                o["p"].write(data)
                if o["kasta"] and o["feil"]:
                    o["feil"] = ""
            except Exception as e:
                if type(e).__name__ == "SerialTimeoutException":
                    # Porten er open, men ingen les (OneVision lukka eller heng). Kast linja og hald fram –
                    # elles stoppar heile Geoscan (logg, NTRIP-GGA, status) medan vi ventar.
                    o["kasta"] += 1
                    o["feil"] = f"ingen les porten – {o['kasta']} linjer kasta (er OneVision opna på andre enden?)"
                    continue
                # porten forsvann (com0com, USB) – prøv på nytt ved neste linje
                o["feil"] = str(e)
                try:
                    o["p"] and o["p"].close()
                except Exception:
                    pass
                o["p"] = None
        with self.lock:
            for c in list(self.clients):
                try:
                    c.sendall(data)
                except OSError:
                    self.clients.remove(c)


class App:
    """Heile Geoscan-tenesta: inngangar, korreksjon, utgangar, NTRIP, opptak og statusside."""

    open_port = staticmethod(lambda spec: open_port(spec))

    def __init__(self, cfg, cfg_path=None, omstart=False):
        import ntrip_teneste as NT
        from okt import Okt
        self.cfg = cfg
        self.cfg_path = Path(cfg_path) if cfg_path else HER / "geoscan_config.json"
        self.versjon = VERSJON
        self.loggdir = HER / (cfg.get("logg") or "logg")
        self.loggdir.mkdir(parents=True, exist_ok=True)
        self.k = Korrigerar(cfg)
        self.ut = Utgangar(cfg)
        self.state, self.handles = {}, {}
        self.innraa = {}      # siste NMEA-linjer per inngang, til live-statistikk og «Finn utstyr»
        self.write_lock = threading.Lock()
        self.raw_gga, self.last_gga_t = None, None
        self.started = time.time()
        self.rec = None
        if cfg.get("opptak") and cfg.get("logg"):
            d = HER / cfg["logg"]
            d.mkdir(exist_ok=True)
            self.rec = open(d / time.strftime("raa_%Y%m%d_%H%M%S.nmea"), "a", encoding="ascii", errors="replace")
            self.rec.write(f"# {NAMN} {VERSJON} - Alpindata HP Brunstad Sorensen - {SIGNATUR}\n")
        self.ntrip = NT.NtripTeneste(NT.load(cfg, HER), self, VERSJON)
        # økta: loggane frå denne oppstarten blir lagde til ho når operatøren har valt (sjå okt.py)
        self.okt = Okt(self.loggdir)
        for f in (getattr(self.k.logfile, "name", None), getattr(self.rec, "name", None)):
            if f:
                self.okt.legg_til_logg(Path(f).name)
        self.okt.auto(omstart)
        self.oppd = {"lokal": VERSJON, "github": None, "nyare": False, "melding": None, "feil": None, "sjekka": None, "avslutt": False, "koyrer": False, "logg": [], "omstart": False}

    def start(self):
        for spec in self.cfg["inn"]:
            threading.Thread(target=self.reader, args=(spec,), daemon=True).start()
        self.ntrip.start()
        if self.cfg.get("sjekk_oppdatering", True):
            threading.Thread(target=self.update_loop, daemon=True).start()
        if self.cfg.get("status_port"):
            import webtenar
            webtenar.start(self, int(self.cfg["status_port"]), bool(self.cfg.get("status_lan")))

    def line_in(self, line, now=None):
        """Éi NMEA-linje frå ein inngang: opptak, GGA til casteren, korreksjon og ut."""
        line = line.strip()
        if not line:
            return
        if self.rec:
            self.rec.write(line + "\n")
        if line.startswith("$") and line[3:6] == "GGA" and N.valid(line):
            self.raw_gga, self.last_gga_t = line, time.time()   # uendra GGA (antenna) til NTRIP-casteren
        for out in self.k.handle(line, now):
            if out:
                self.ut.send(out)

    def reader(self, spec):
        """Les éin inngang. Koplar til att av seg sjølv når porten forsvinn (laus USB, Bluetooth som fell ut).
        RTCM (binært) kan kome på same port – berre linjer som byrjar med $ blir tolka."""
        name = spec["port"]
        while True:
            try:
                p = open_port(spec)
                self.handles[name] = p
                self.state[name] = "open"
                buf = b""
                while True:
                    b = p.read(4096)
                    if not b:
                        continue
                    buf += b
                    while b"\n" in buf:
                        raw, buf = buf.split(b"\n", 1)
                        j = raw.rfind(b"$")
                        if j >= 0:
                            linje = raw[j:].decode("ascii", "replace")
                            self.innraa.setdefault(name, deque(maxlen=400)).append(linje.strip())
                            self.line_in(linje)
                    if len(buf) > 65536:
                        buf = buf[-4096:]
            except Exception as e:
                self.handles.pop(name, None)
                self.state[name] = f"feil: {e}"
                time.sleep(2)

    def innstat(self):
        """Kva som kjem på kvar inngang no: talker, rate, fix, satellittar, setningstypar (frå dei siste linjene)."""
        import finn_utstyr as FU
        ut = {}
        for name, d in list(self.innraa.items()):
            a = FU.analyser(("\n".join(list(d)[-200:])).encode("ascii", "replace"))
            ut[name] = {k: a[k] for k in ("kva", "talker", "hz", "fix", "sats", "typar", "helling")}
        return ut

    # ---------- oppdatering (oppdater.py) ----------
    def check_update(self):
        import oppdater
        lok, rem, nyare = oppdater.check()
        self.oppd.update(github=rem, nyare=nyare, melding=oppdater.remote_melding() if nyare else None,
                         feil=oppdater.SISTE_FEIL[0], nokkel_ugyldig=oppdater.NOKKEL_UGYLDIG[0],
                         sjekka=time.strftime("%Y-%m-%d %H:%M"))

    def update_loop(self, timar=3):
        """Sjå etter ny versjon ved oppstart og så kvar 3. time, så ein ny versjon (med melding) synest
        sjølv om programmet står på heile dagen."""
        while True:
            try:
                self.check_update()
            except Exception:
                pass
            time.sleep(timar * 3600)

    def avslutt(self):
        """Lagre alt og stopp reint (knappen «Avslutt»). Hovudløkka avsluttar med kode 0, og vindauget lukkar seg."""
        self.okt.lagre()
        try:
            self.k.logfile and self.k.logfile.flush()
            self.rec and self.rec.flush()
        except Exception:
            pass
        self.ntrip.stop.set()
        self.oppd["avslutt"] = True

    def run_update(self):
        """Køyrt frå statussida. Ved ny versjon: avslutt med kode 3, så START-GEOSCAN.bat startar på nytt."""
        import oppdater
        if self.oppd["koyrer"]:
            return
        self.oppd.update(koyrer=True, logg=[])
        log = self.oppd["logg"].append
        try:
            if oppdater.update(log=log):
                log("Startar Geoscan på nytt …")
                self.oppd["omstart"] = True
        except Exception as e:
            log(f"Oppdateringa feila: {e}")
        finally:
            self.oppd["koyrer"] = False

    def snapshot(self):
        k = dict(self.k.status)
        n = dict(self.ntrip.status)
        n["alder"] = None if not n.get("sist_data") else round(time.time() - n["sist_data"], 1)
        n.pop("sist_data", None)
        d25 = None
        rd = float(self.cfg.get("radar_djupn") or 2.5)
        if k.get("korrigert") and k.get("stamp") is not None:
            t = math.radians(math.hypot(k["stamp"], k["krenging"]))
            d25 = round(rd * math.sin(t) * 100, 1)
        for nk in ("noy", "pjk", "ggk"):
            ny = k.get(nk)
            if ny:
                k[nk] = dict(ny, alder=round(time.time() - ny["t"], 1))
        V = self.k.vakt
        ga = None if self.last_gga_t is None else time.time() - self.last_gga_t
        with self.k.lock:
            V.sjekk("alder", ga is not None and ga > V.alder, time.time(),
                    V.TEKST["alder"].format(s=round(ga or 0)))
            vakt = {"aktive": V.aktive(), "nr": V.nr, "oppsett": self.k.oppsett_varsel()}
        return {"korr": k, "vakt": vakt, "ntrip": n, "inn": dict(self.state), "innstat": self.innstat(),
                "gnss_alder": None if self.last_gga_t is None else round(time.time() - self.last_gga_t, 1),
                "ut": [{"port": o["spec"]["port"], "feil": o["feil"], "kasta": o["kasta"]} for o in self.ut.ports],
                "stripe": [float(self.cfg.get("skannebreidd") or 0.96), float(self.cfg.get("skannebreidd_ytre") or 0.0)],
                "tcp_port": self.cfg.get("tcp_port"), "tcp_klientar": len(self.ut.clients), "djupnfeil_25": d25, "radar_djupn": rd,
                "namn": NAMN, "produsent": PRODUSENT, "signatur": SIGNATUR,
                "oppdatering": {k2: v for k2, v in self.oppd.items()}, "demo": bool(self.cfg.get("demo"))}


def tilstand(app):
    """Det som er verdt ei ny line i vindauget når det endrar seg: fix, helling på/av, NTRIP, portar og ut-feil."""
    s, n = app.k.status, app.ntrip.status
    return (s.get("fix"), bool(s.get("korrigert")), n.get("tilstand"), tuple(sorted(app.state.items())),
            tuple(bool(o["feil"]) for o in app.ut.ports))


def status_line(app):
    s = app.k.status
    fixnamn = {0: "INGEN", 1: "GPS", 2: "DGPS", 4: "RTK FIX", 5: "RTK FLOAT", 6: "INS", 9: "SBAS"}
    hell = (f"stamp {s['stamp']:+.1f}° krenging {s['krenging']:+.1f}° ({s['hellingskjelde']}), "
            f"forskyving {s['forskyving_cm']} cm") if s["korrigert"] else s["melding"]
    porter = ", ".join(f"{n}: {v}" for n, v in app.state.items())
    utfeil = ", ".join(f"{o['spec']['port']}: {o['feil']}" for o in app.ut.ports if o["feil"])
    n = app.ntrip.status
    ntrip = "" if n["tilstand"] == "av" else f" | NTRIP {n['tilstand']}" + (f" ({n['melding']})" if n["melding"] else "")
    return (f"{time.strftime('%H:%M:%S')}  {fixnamn.get(s['fix'], s['fix'])}  sat {s['sats']}  "
            f"kurs {s['kurs']} ({s['kurskjelde']})  {hell}{ntrip}  | inn: {porter}"
            + (f" | ut-feil: {utfeil}" if utfeil else ""))


def oppstartlogo(sek=2.5):
    """Viser oppstartbiletet (ikon/oppstart.png: Snowman-logoen med georadaren) midt på skjermen i nokre sekund.
    Tenesta køyrer alt i bakgrunnen. Utan skjerm eller tkinter blir det berre hoppa over."""
    try:
        import tkinter as tk
        bilete = HER / "ikon" / "oppstart.png"
        if not bilete.exists():
            return
        rot = tk.Tk()
        rot.overrideredirect(True)
        rot.attributes("-topmost", True)
        img = tk.PhotoImage(file=str(bilete))
        w, h = img.width(), img.height()
        rot.geometry(f"{w}x{h}+{(rot.winfo_screenwidth() - w) // 2}+{(rot.winfo_screenheight() - h) // 2}")
        try:
            rot.wm_attributes("-transparentcolor", "#010203")      # runde hjørne på Windows
            rot.configure(bg="#010203")
        except tk.TclError:
            pass
        tk.Label(rot, image=img, bd=0, bg=rot["bg"]).pack()
        try:
            rot.iconbitmap(str(HER / "ikon" / "geoscan.ico"))
        except tk.TclError:
            pass
        rot.after(int(sek * 1000), rot.destroy)
        rot.mainloop()
    except Exception:
        pass


def main(argv=None):
    ap = argparse.ArgumentParser(description="Hellingskorrigert GNSS til IDS Stream C")
    ap.add_argument("--config", default=str(HER / "geoscan_config.json"))
    ap.add_argument("--fil", help="spel av ei NMEA-fil og skriv korrigert NMEA til skjermen")
    ap.add_argument("--omstart", action="store_true", help="(brukt av START-GEOSCAN.bat) ikkje opne nettlesaren på nytt")
    a = ap.parse_args(argv)
    cfg = load_cfg(Path(a.config))
    if a.fil:
        cfg["logg"] = None
        k = Korrigerar(cfg)
        t = 0.0
        for raw in Path(a.fil).read_text(encoding="ascii", errors="replace").splitlines():
            t += 0.1
            for out in k.handle(raw, now=t):
                if out:
                    print(out)
        return
    if cfg.get("hoegd") == "nn2000" and GEOID.n(62.4, 6.6) is None:
        print(f"ÅTVARING: geoiden kan ikkje lesast ({GEOID.err}). Høgda frå mottakaren blir brukt.", file=sys.stderr)
    app = App(cfg, a.config, omstart=a.omstart)
    app.start()
    print(f"\n  *  {NAMN.upper()}  {VERSJON}  *\n     {PRODUSENT}\n")
    # Snarvegane på skrivebordet med ikonet: lag dei på nytt ved første start etter kvar oppdatering (0.9.22)
    import snarveg as SV
    threading.Thread(target=lambda: print("  Snarvegar: " + SV.lag(HER, VERSJON)[1]), daemon=True).start()
    if cfg.get("vis_oppstartlogo", True) and not a.omstart:
        oppstartlogo()
    k = app.k
    if cfg.get("status_port") and cfg.get("opne_nettlesar", True) and not a.omstart:
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{cfg['status_port']}")).start()
    if cfg.get("demo"):
        print("*** DEMO: simulert mottakar og NTRIP-caster. Dette er IKKJE ekte målingar. ***")
    print(f"Spakarm fram {k.lever[0]} m, høgre {k.lever[1]} m, opp {k.lever[2]} m, "
          f"utgang «{cfg['utgang']}», TCP {cfg.get('tcp_port')}"
          + (f", status http://localhost:{cfg['status_port']}" if cfg.get("status_port") else "") + ". Ctrl+C stoppar.")
    print("Vindauget må vere ope medan du skannar – det kan liggje minimert. Lukkar du det, stoppar Snowman Geoscan.\n"
          "Alt blir vist i nettlesaren (http://localhost:%s). Her kjem berre ei line når noko endrar seg, og elles éi i minuttet.\n"
          % cfg.get("status_port"), flush=True)
    sist, sist_t = None, 0.0
    intervall = float(cfg.get("statuslinje_sek", 60))
    try:
        while True:
            time.sleep(2)
            if app.oppd["omstart"]:
                app.okt.lagre()
                print("Startar på nytt …", flush=True)
                time.sleep(1)
                sys.exit(3)          # START-GEOSCAN.bat startar på nytt ved kode 3
            if app.oppd.get("avslutt"):
                print("Snowman Geoscan er avslutta. Alt er lagra – neste gong kan du halde fram der du slapp.", flush=True)
                time.sleep(1.5)
                sys.exit(0)
            nokkel = tilstand(app)
            if nokkel != sist or time.time() - sist_t >= intervall:
                print(status_line(app), flush=True)
                sist, sist_t = nokkel, time.time()
    except KeyboardInterrupt:
        app.okt.lagre()


if __name__ == "__main__":
    main()
