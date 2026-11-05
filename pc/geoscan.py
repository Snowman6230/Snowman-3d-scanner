# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
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
VERSJON = "0.6.0"
from opphav import NAMN, PRODUSENT, SIGNATUR   # namnet og opphavet (sjå opphav.py)
STANDARD = {
    "inn": [{"port": "COM23", "baud": 115200}],
    "ut_seriell": [{"port": "COM34", "baud": 115200}],
    "tcp_port": 5000,
    "spakarm": {"fram": 0.0, "hogre": 0.0, "opp": 1.40},
    "utgang": "rett_antenne",
    "mottakar_kompenserer": False,
    "djupn_sanntid": 0.0,
    "radar_djupn": 2.5,
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
    "ntrip": {"pa": False, "rtcm_til": None, "gga_intervall": 10},
}


LOGG_HOVUD = ("tid;fix;lat_inn;lon_inn;lat_ut;lon_ut;sone;E_ut;N_ut;h_nn2000_ut;h_bakke;korrigert;stamp;krenging;kurs;"
              "kurskjelde;djupn_sanntid;forskyving_cm")


def dist_en(la1, lo1, la2, lo2):
    my, mx = H.meter_per_grad(la1)
    return (lo2 - lo1) * mx, (la2 - la1) * my


def load_cfg(path):
    cfg = dict(STANDARD)
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg


class Korrigerar:
    """Tek imot NMEA-linjer frå alle inngangar, og gir tilbake linjene som skal sendast ut."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.hel = H.Helling()
        s = cfg["spakarm"]
        self.lever = (float(s.get("fram", 0)), float(s.get("hogre", 0)), float(s.get("opp", 0)))
        self.lock = threading.Lock()
        self.status = {"fix": None, "sats": None, "stamp": None, "krenging": None, "kurs": None,
                       "kurskjelde": None, "forskyving_cm": None, "korrigert": False, "melding": "ventar på data",
                       "hellingskjelde": None, "geoide": None, "feil_sjekksum": 0}
        self.logfile = None
        self.komp = bool(cfg.get("mottakar_kompenserer"))   # R12i: tilt-kompensasjon i mottakaren
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

    def _correct(self, fields, k, pos, now):
        lat, lon = pos
        cfg, st = self.cfg, self.status
        gga = N.parse_gga(fields) if k == "GGA" else None
        if gga:
            st.update(fix=gga["q"], sats=gga["sats"])
            self.hel.add_position(lat, lon, now)
        tilt = H.tilt_from(self.hel, cfg, now)
        hdg, hsrc = self.hel.heading(cfg)
        st.update(kurs=None if hdg is None else round(hdg, 1), kurskjelde=hsrc)
        if tilt is None or hdg is None:
            st.update(korrigert=False, stamp=None, krenging=None, forskyving_cm=None,
                      melding="ingen fersk helling" if tilt is None else "ventar på kurs (køyr nokre meter)")
            if self.komp:
                st["melding"] = "masta retta i mottakaren (stangspiss)" + ("" if tilt is None else ", ventar på kurs")
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
        self._log(gga, lat, lon, la, lo, h2, n_geo, pitch, roll, hdg, d0, now)
        return out

    def _point(self, lat, lon, h, lever, hdg, pitch, roll, d0):
        """Punktet som blir sendt ut: masta retta (referansepunkt eller rett antenne), og om djupn_sanntid er sett,
        flytta vidare dit eit objekt på den djupna eigentleg ligg (berre sidelengs – høgda er framleis overflata)."""
        if self.komp:
            # Mottakaren (R12i med tilt på, stanghøgd = antenne → referansepunkt) sender alt referansepunktet P.
            la, lo, h2, off = lat, lon, h, 0.0
            if self.cfg.get("utgang") == "rett_antenne":
                dE, dN, dU = H.offset_enu(lever, hdg, 0.0, 0.0)
                my, mx = H.meter_per_grad(lat)
                la, lo, h2 = lat + dN / my, lon + dE / mx, h + dU
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

    def _log(self, gga, lat, lon, la, lo, h2, n_geo, pitch, roll, hdg, d0, now):
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
        mast = self.lever[2] if self.cfg.get("utgang") == "rett_antenne" else 0.0
        h_bakke = "" if h_nn == "" else f"{float(h_nn) - mast:.3f}"
        self.logfile.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))}.{int(t * 1000) % 1000:03d};{gga['q']};"
            f"{lat:.9f};{lon:.9f};{la:.9f};{lo:.9f};{z};{E:.3f};{Nn:.3f};{h_nn};{h_bakke};"
            f"{1 if st['korrigert'] else 0};{pitch:.2f};{roll:.2f};{hdg:.1f};{st['kurskjelde']};{d0:g};"
            f"{st['forskyving_cm'] if st['forskyving_cm'] is not None else ''}\n")
        self.logfile.flush()


# ---------- inn og ut ----------
def open_port(spec):
    import serial  # pyserial
    url = spec["port"]
    return serial.serial_for_url(url, baudrate=int(spec.get("baud", 115200)), timeout=1)


class Utgangar:
    def __init__(self, cfg):
        self.ports = [{"spec": s, "p": None, "feil": ""} for s in cfg.get("ut_seriell") or []]
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
            try:
                if o["p"] is None:
                    o["p"] = open_port(o["spec"])
                    o["feil"] = ""
                o["p"].write(data)
            except Exception as e:  # porten forsvann (com0com, USB) – prøv på nytt ved neste linje
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

    def __init__(self, cfg, cfg_path=None):
        import ntrip_teneste as NT
        self.cfg = cfg
        self.cfg_path = Path(cfg_path) if cfg_path else HER / "geoscan_config.json"
        self.versjon = VERSJON
        self.loggdir = HER / (cfg.get("logg") or "logg")
        self.loggdir.mkdir(parents=True, exist_ok=True)
        self.k = Korrigerar(cfg)
        self.ut = Utgangar(cfg)
        self.state, self.handles = {}, {}
        self.write_lock = threading.Lock()
        self.raw_gga, self.last_gga_t = None, None
        self.started = time.time()
        self.rec = None
        if cfg.get("opptak") and cfg.get("logg"):
            d = HER / cfg["logg"]
            d.mkdir(exist_ok=True)
            self.rec = open(d / time.strftime("raa_%Y%m%d_%H%M%S.nmea"), "a", encoding="ascii", errors="replace")
            self.rec.write(f"# {NAMN} {VERSJON} - Alpindata v/Hans Petter B. Sorensen - {SIGNATUR}\n")
        self.ntrip = NT.NtripTeneste(NT.load(cfg, HER), self, VERSJON)
        self.oppd = {"lokal": VERSJON, "github": None, "nyare": False, "koyrer": False, "logg": [], "omstart": False}

    def start(self):
        for spec in self.cfg["inn"]:
            threading.Thread(target=self.reader, args=(spec,), daemon=True).start()
        self.ntrip.start()
        if self.cfg.get("sjekk_oppdatering", True):
            threading.Thread(target=self.check_update, daemon=True).start()
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
                            self.line_in(raw[j:].decode("ascii", "replace"))
                    if len(buf) > 65536:
                        buf = buf[-4096:]
            except Exception as e:
                self.handles.pop(name, None)
                self.state[name] = f"feil: {e}"
                time.sleep(2)

    # ---------- oppdatering (oppdater.py) ----------
    def check_update(self):
        import oppdater
        lok, rem, nyare = oppdater.check()
        self.oppd.update(github=rem, nyare=nyare)

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
        return {"korr": k, "ntrip": n, "inn": dict(self.state),
                "gnss_alder": None if self.last_gga_t is None else round(time.time() - self.last_gga_t, 1),
                "ut": [{"port": o["spec"]["port"], "feil": o["feil"]} for o in self.ut.ports],
                "tcp_port": self.cfg.get("tcp_port"), "tcp_klientar": len(self.ut.clients), "djupnfeil_25": d25, "radar_djupn": rd,
                "namn": NAMN, "produsent": PRODUSENT, "signatur": SIGNATUR,
                "oppdatering": {k2: v for k2, v in self.oppd.items()}, "demo": bool(self.cfg.get("demo"))}


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
    app = App(cfg, a.config)
    app.start()
    print(f"\n  *  {NAMN.upper()}  *\n     {PRODUSENT}\n")
    if cfg.get("vis_oppstartlogo", True) and not a.omstart:
        oppstartlogo()
    k = app.k
    if cfg.get("status_port") and cfg.get("opne_nettlesar", True) and not a.omstart:
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{cfg['status_port']}")).start()
    if cfg.get("demo"):
        print("*** DEMO: simulert mottakar og NTRIP-caster. Dette er IKKJE ekte målingar. ***")
    print(f"{NAMN} {VERSJON}\n{PRODUSENT}\n")
    print(f"Spakarm fram {k.lever[0]} m, høgre {k.lever[1]} m, opp {k.lever[2]} m, "
          f"utgang «{cfg['utgang']}», TCP {cfg.get('tcp_port')}"
          + (f", status http://localhost:{cfg['status_port']}" if cfg.get("status_port") else "") + ". Ctrl+C stoppar.")
    try:
        while True:
            time.sleep(2)
            if app.oppd["omstart"]:
                print("Ny versjon lagd inn – startar på nytt.", flush=True)
                time.sleep(1)
                sys.exit(3)          # START-GEOSCAN.bat startar på nytt ved kode 3
            print(status_line(app), flush=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
