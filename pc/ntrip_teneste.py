# SNOWMAN by Alpindata – Copyright © 2026 Hans Petter Brunstad Sørensen (Alpindata). Alle rettar reserverte.
"""NTRIP i Geoscan: hentar RTCM frå casteren og sender det til mottakaren (R12i har ikkje eige internett).
Erstattar den delen av Trimble Access som sender korreksjonar.

    casteren (mountpoint) ──RTCM──► geoscan ──► mottakaren: same port som NMEA (USB) eller eigen port
                         ◄──GGA───            (Bluetooth port 2 på R12i)

Skilnad frå Snødjupne: Snødjupne sender aldri noko til mottakaren og reknar RTK sjølv. Her skal mottakaren
rekne RTK (og tilt) sjølv, så han må få korreksjonane.

Innlogginga ligg i pc/ntrip_lokal.json, som aldri blir lagt i git (sjå .gitignore).
"""
import json
import threading
import time
from pathlib import Path

import ntripklient as NC

STANDARD = {"pa": False, "caster": "", "port": 2101, "mountpoint": "", "brukar": "", "passord": "",
            "versjon": "auto", "gga_intervall": 10, "rtcm_til": None, "vakthund_s": 15}


def load(cfg, here):
    """NTRIP-oppsett: standard ← geoscan_config.json «ntrip» ← ntrip_lokal.json (innlogging, ikkje i git)."""
    n = dict(STANDARD)
    n.update(cfg.get("ntrip") or {})
    lokal = Path(here) / "ntrip_lokal.json"
    if lokal.exists():
        n.update(json.loads(lokal.read_text(encoding="utf-8")))
    return n


class NtripTeneste:
    def __init__(self, ncfg, app, version=""):
        self.cfg, self.app, self.ver = ncfg, app, version
        self.status = {"tilstand": "av", "melding": "", "protokoll": None, "byte": 0, "sist_data": None,
                       "sist_gga": None, "tilkoplingar": 0}
        self.stop = threading.Event()
        self._own = None   # eigen port for RTCM når han ikkje er ein av inngangane

    def start(self):
        if not self.cfg.get("pa"):
            return
        if not (self.cfg.get("caster") and self.cfg.get("mountpoint")):
            self.status.update(tilstand="feil", melding="caster/mountpoint manglar i ntrip_lokal.json")
            return
        threading.Thread(target=self._loop, daemon=True).start()

    # ---------- RTCM til mottakaren ----------
    def _target(self):
        return self.cfg.get("rtcm_til") or (self.app.cfg["inn"][0]["port"] if self.app.cfg.get("inn") else None)

    def write_rtcm(self, data):
        name = self._target()
        if name is None:
            return
        h = self.app.handles.get(name)
        if h is not None:                      # same port som vi les NMEA frå (USB)
            with self.app.write_lock:
                h.write(data)
            return
        if self._own is None:                  # eigen port, til dømes Bluetooth port 2
            spec = {"port": name, "baud": self.cfg.get("rtcm_baud", 115200)}
            self._own = self.app.open_port(spec)
        self._own.write(data)

    # ---------- hovudløkka ----------
    def _gga(self):
        return self.app.raw_gga

    def _loop(self):
        st, c = self.status, self.cfg
        while not self.stop.is_set():
            gga = self._gga()
            if not gga and c.get("versjon") != "1":
                st.update(tilstand="ventar", melding="ventar på posisjon (GGA) frå mottakaren")
                time.sleep(1)
                if time.time() - self.app.started < 20:
                    continue        # etter 20 s: prøv likevel – mange castarar treng ikkje GGA
            try:
                st.update(tilstand="koplar", melding=f"koplar til {c['caster']}:{c['port']}/{c['mountpoint']}")
                s = NC.open_stream(c["caster"], c["port"], c["mountpoint"], c.get("brukar", ""), c.get("passord", ""),
                                   c.get("versjon", "auto"), self.ver, gga)
            except NC.NtripError as e:
                st.update(tilstand="feil", melding=str(e))
                self._wait(60 if e.code in ("auth", "mount") else 10)   # feil passord: ikkje hamre på casteren
                continue
            except OSError as e:
                st.update(tilstand="feil", melding=f"casteren svarar ikkje ({e})")
                self._wait(10)
                continue
            st.update(tilstand="tilkopla", melding="", protokoll=s.proto, tilkoplingar=st["tilkoplingar"] + 1)
            last_gga = 0.0
            last_data = time.time()
            try:
                if gga:
                    s.send_gga(gga)
                    last_gga = time.time()
                    st["sist_gga"] = last_gga
                while not self.stop.is_set():
                    d = s.read()
                    now = time.time()
                    if d:
                        last_data = now
                        st["byte"] += len(d)
                        st["sist_data"] = now
                        try:
                            self.write_rtcm(d)
                        except Exception as e:      # mottakarporten er borte – lukk eigen port, prøv neste gong
                            st["melding"] = f"kan ikkje skrive RTCM til {self._target()}: {e}"
                            if self._own is not None:
                                try:
                                    self._own.close()
                                except Exception:
                                    pass
                                self._own = None
                    elif now - last_data > c.get("vakthund_s", 15):
                        raise ConnectionError(f"ingen korreksjonar på {c.get('vakthund_s', 15)} s")
                    g = self._gga()
                    if g and now - last_gga >= c.get("gga_intervall", 10):
                        s.send_gga(g)
                        last_gga = st["sist_gga"] = now
            except (ConnectionError, OSError) as e:
                st.update(tilstand="fråkopla", melding=f"{e} – koplar til att")
            finally:
                s.close()
            self._wait(2)

    def _wait(self, sek):
        self.stop.wait(sek)
