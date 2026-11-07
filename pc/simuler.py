# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Simulator for testing utan utstyr: ein mottakar som køyrer georadarvogna fram og tilbake i ein sidebakke,
og (valfritt) ein falsk NTRIP-caster. Alt er SIMULERT – ikkje bruk resultata som målingar.

    python simuler.py                       mottakar på TCP 7777 (GGA + PASHR 5 Hz)
    python simuler.py --caster 2101         også falsk caster: mountpoint SIM, sender RTCM-liknande byte
Set i geoscan_config.json:  "inn": [{"port": "socket://127.0.0.1:7777"}]
og eventuelt ntrip_lokal.json: {"pa": true, "caster": "127.0.0.1", "port": 2101, "mountpoint": "SIM"}

Simulatoren tel RTCM-byte som geoscan sender tilbake til «mottakaren», så NTRIP-vegen kan sjekkast.
"""
import argparse
import math
import socket
import threading
import time

import nmea as N

LAT0, LON0 = 62.3900, 6.5800   # Sykkylven (berre eit testpunkt)


class Mottakar:
    """Vogna skannar som ein ekte georadar: parallelle stripar aust–vest (40 m lange, 0,9 m mellom) over eit
    felt på 10 stripar, og så om att. Bakken hallar mot sør, så krenginga er ±6° alt etter køyreretninga.
    Stampen varierer ±1,5° langs stripa."""

    def __init__(self, hz=5.0, speed=1.2, length=40.0, sideslope=6.0, alt=150.0, sep=44.775, lanes=10, gap=0.9):
        self.hz, self.speed, self.length, self.side, self.alt, self.sep = hz, speed, length, sideslope, alt, sep
        self.lanes, self.gap = lanes, gap
        self.rtcm_bytes = 0

    def state(self, t):
        s = (t * self.speed) % (self.lanes * self.length)
        lane, along = int(s // self.length), s % self.length
        aust = lane % 2 == 0
        east = along if aust else self.length - along
        north = lane * self.gap
        hdg = 90.0 if aust else 270.0
        # bakken fell mot sør: køyrer ein aust, er høgre side (sør) nede → krenging +; vest → −
        roll = self.side if aust else -self.side
        pitch = 1.5 * math.sin(east / 6.0)
        my = 111320.0
        mx = my * math.cos(math.radians(LAT0))
        return LAT0 + north / my, LON0 + east / mx, hdg, pitch, roll

    def lines(self, t):
        lat, lon, hdg, pitch, roll = self.state(t)
        hh = time.strftime("%H%M%S", time.gmtime(t)) + f".{int(t * 100) % 100:02d}"
        la, ha = N.coord_out(lat, True)
        lo, ho = N.coord_out(lon, False)
        gga = N.build(["INGGA", hh, la, ha, lo, ho, "4", "18", "0.7", f"{self.alt:.3f}", "M", f"{self.sep:.3f}", "M",
                       "1.0", "0001"])
        pashr = N.build(["PASHR", hh, f"{hdg:.2f}", "T", f"{roll:.2f}", f"{pitch:.2f}", "", "0.02", "0.02", "0.05", "2", "1"])
        return [pashr, gga]

    def serve(self, port, stop):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(2)
        srv.settimeout(0.5)
        while not stop.is_set():
            try:
                c, _ = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self._client, args=(c, stop), daemon=True).start()
        srv.close()

    def _client(self, c, stop):
        c.settimeout(0.01)
        t0 = time.time()
        try:
            while not stop.is_set():
                for line in self.lines(time.time() - t0):
                    c.sendall((line + "\r\n").encode())
                end = time.time() + 1 / self.hz
                while time.time() < end:
                    try:
                        d = c.recv(4096)
                        if not d:
                            return
                        self.rtcm_bytes += len(d)
                    except socket.timeout:
                        pass
        except OSError:
            pass
        finally:
            c.close()


class FalskCaster:
    """NTRIP 1-caster med mountpoint SIM. Sender ein RTCM-liknande ramme (0xD3 …) kvart sekund, tel GGA."""

    def __init__(self, mountpoint="SIM"):
        self.mp, self.gga = mountpoint, 0

    def serve(self, port, stop):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(2)
        srv.settimeout(0.5)
        while not stop.is_set():
            try:
                c, _ = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self._client, args=(c, stop), daemon=True).start()
        srv.close()

    def _client(self, c, stop):
        try:
            req = c.recv(4096).decode("latin1")
            if f"GET /{self.mp} " not in req:
                tab = (f"STR;{self.mp};Simulert base;RTCM 3.2;1004(1),1012(1);2;GPS+GLO;SIM;NOR;62.39;6.58;1;0;sim;none;N;N;0;\r\n"
                       "STR;SIM2;Simulert base 2;RTCM 3.2;1074(1);2;GPS+GAL;SIM;NOR;62.50;6.80;1;0;sim;none;N;N;0;\r\n")
                c.sendall(b"SOURCETABLE 200 OK\r\n\r\n" + tab.encode() + b"ENDSOURCETABLE\r\n")
                return
            c.sendall(b"ICY 200 OK\r\n")
            c.settimeout(0.05)
            frame = bytes([0xD3, 0x00, 0x13]) + bytes(19) + b"\x00\x00\x00"
            while not stop.is_set():
                c.sendall(frame)
                end = time.time() + 1.0
                while time.time() < end:
                    try:
                        d = c.recv(1024)
                        if not d:
                            return
                        self.gga += d.count(b"GGA")
                    except socket.timeout:
                        pass
        except OSError:
            pass
        finally:
            c.close()


def main():
    ap = argparse.ArgumentParser(description="SIMULERT mottakar og NTRIP-caster for Geoscan")
    ap.add_argument("--port", type=int, default=7777)
    ap.add_argument("--caster", type=int, help="start også falsk NTRIP-caster på denne porten")
    a = ap.parse_args()
    stop = threading.Event()
    m = Mottakar()
    threading.Thread(target=m.serve, args=(a.port, stop), daemon=True).start()
    c = None
    if a.caster:
        c = FalskCaster()
        threading.Thread(target=c.serve, args=(a.caster, stop), daemon=True).start()
    print(f"SIMULERT mottakar på socket://127.0.0.1:{a.port}" + (f", falsk caster 127.0.0.1:{a.caster}/SIM" if c else "")
          + ". Ctrl+C stoppar.")
    try:
        while True:
            time.sleep(5)
            print(f"RTCM motteke: {m.rtcm_bytes} byte" + (f", GGA til casteren: {c.gga}" if c else ""), flush=True)
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
