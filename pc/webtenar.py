# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Nettlesargrensesnittet til Snowman Geoscan: http://localhost:8088

Fanene Status, Resultat, Send inn og Innstillingar (pc/web/index.html). Alt blir køyrt lokalt på PC-en.
Sida kan opnast på mobil/nettbrett når status_lan er på, men endringar (lagre, laste opp, oppdatere, rette,
lage pakke) er berre lov frå PC-en sjølv (127.0.0.1).
"""
import json
import mimetypes
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HER = Path(__file__).resolve().parent
WEB = HER / "web"
MAKS_OPPLASTING = 500 * 1024 * 1024


def start(app, port=8088, lan=False):
    import innsending as INS
    import innstillingar as INN
    import resultat as RES

    def loggdir():
        return app.loggdir

    nedlasting = {"resultat": lambda: HER / "resultat", "pakke": lambda: HER / "pakkar",
                  "innsendt": lambda: HER / "innsendt" / "filer", "logg": loggdir}

    import opphav

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "SnowmanGeoscan/" + opphav.versjon() + " (Alpindata)"
        sys_version = ""

        def log_message(self, *a):
            pass

        # ---------- svar ----------
        def _send(self, body, typ="application/json", code=200, extra=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False, default=str).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", typ)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _err(self, msg, code=400):
            self._send({"ok": False, "feil": msg}, code=code)

        def _local(self):
            return self.client_address[0] in ("127.0.0.1", "::1")

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAKS_OPPLASTING:
                raise ValueError("for stor")
            return self.rfile.read(n) if n else b""

        # ---------- GET ----------
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            path = u.path
            try:
                if path in ("/", "/index.html"):
                    return self._send((WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
                if path.startswith("/vendor/"):
                    f = (WEB / "vendor" / Path(path).name)
                    if f.is_file():
                        return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream",
                                          extra={"Cache-Control": "max-age=86400"})
                    return self._err("finst ikkje", 404)
                if path == "/status":
                    return self._send(app.snapshot())
                if path == "/api/innstillingar":
                    return self._send(INN.hent(app.cfg_path, app.cfg))
                if path == "/api/okter":
                    return self._send(RES.okter(loggdir()))
                if path == "/api/spor":
                    f = loggdir() / Path(q.get("fil", "")).name
                    return self._send(RES.spor(f) if f.is_file() else [])
                if path == "/api/innsending":
                    return self._send({"sporsmal": INS.SPORSMAL, "svar": INS.svar_les(), "filer": INS.filer(),
                                       "filtypar": INS.FILTYPAR, "sjekkliste": INS.SJEKKLISTE, "status": INS.STATUS,
                                       "sjekk": INS.sjekk_les(), "epost": opphav.KONTAKT_EPOST,
                                       "sjekk_svar": INS.meldingar()["sjekk_svar"]})
                if path == "/api/meldingar":
                    return self._send(INS.meldingar())
                if path == "/api/resultatfiler":
                    d = HER / "resultat"
                    fl = sorted(d.iterdir(), key=lambda p: -p.stat().st_mtime) if d.exists() else []
                    return self._send([{"fil": p.name, "kb": round(p.stat().st_size / 1024)} for p in fl if p.is_file()])
                if path.startswith("/last-ned/"):
                    _, _, kind, name = path.split("/", 3)
                    base = nedlasting.get(kind)
                    f = base() / Path(urllib.parse.unquote(name)).name if base else None
                    if f is None or not f.is_file():
                        return self._err("finst ikkje", 404)
                    disp = "attachment; filename*=UTF-8''" + urllib.parse.quote(f.name)
                    return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream",
                                      extra={"Content-Disposition": disp})
                return self._err("finst ikkje", 404)
            except Exception as e:  # aldri la ein feil stoppe tenesta
                return self._err(f"{type(e).__name__}: {e}", 500)

        # ---------- POST (berre frå PC-en) ----------
        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            path = u.path
            if not self._local():
                return self._err("endringar kan berre gjerast på PC-en der Snowman Geoscan køyrer", 403)
            try:
                if path == "/oppdater":
                    threading.Thread(target=app.run_update, daemon=True).start()
                    return self._send({"ok": True}, code=202)
                if path == "/api/omstart":
                    app.oppd["omstart"] = True
                    return self._send({"ok": True})
                if path == "/api/innstillingar":
                    d = json.loads(self._body() or b"{}")
                    INN.lagre(app.cfg_path, d)
                    app.oppd["omstart"] = True       # nye innstillingar gjeld etter omstart (START-GEOSCAN.bat)
                    return self._send({"ok": True})
                if path == "/api/melding-lest":
                    INS.melding_lest(json.loads(self._body() or b"{}").get("id", ""))
                    return self._send({"ok": True})
                if path == "/api/sjekkliste":
                    return self._send({"ok": True, "sjekk": INS.sjekk_lagre(json.loads(self._body() or b"{}"))})
                if path == "/api/opne-mappe":
                    import os
                    import subprocess
                    import sys as _sys
                    d = HER / "pakkar"
                    d.mkdir(exist_ok=True)
                    if os.name == "nt":
                        os.startfile(str(d))                     # Utforskaren, så pakka kan dragast inn i e-posten
                    elif _sys.platform == "darwin":
                        subprocess.Popen(["open", str(d)])
                    else:
                        subprocess.Popen(["xdg-open", str(d)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return self._send({"ok": True})
                if path == "/api/svar":
                    return self._send({"ok": True, "svar": INS.svar_lagre(json.loads(self._body() or b"{}"))})
                if path == "/api/last-opp":
                    fn = INS.fil_lagre(q.get("namn", "fil"), self._body(), q.get("type", "anna"))
                    return self._send({"ok": True, "fil": fn})
                if path == "/api/slett-fil":
                    return self._send({"ok": INS.fil_slett(json.loads(self._body() or b"{}").get("fil", ""))})
                if path == "/api/rett":
                    d = json.loads(self._body() or b"{}")
                    src = HER / "innsendt" / "filer" / INS.safe_name(d.get("fil", ""))
                    if not src.is_file():
                        return self._err("fann ikkje fila")
                    okter = [Path(x).name for x in d.get("okter") or []]
                    logs = [loggdir() / x for x in okter] if okter else sorted(loggdir().glob("geoscan_*.csv"))
                    logs = [p for p in logs if p.is_file()]
                    if app.cfg.get("demo") and (WEB / "vendor" / "demo-logg.csv").is_file():
                        logs.append(WEB / "vendor" / "demo-logg.csv")   # DEMO: ferdig logg over heile simulatorfeltet
                    if not logs:
                        return self._err("ingen loggar å rette mot. Skann først med Snowman Geoscan i gang.")
                    sone = d.get("sone")
                    r = RES.rett_eksport(src, logs, HER / "resultat", d.get("z", "auto"),
                                         int(sone) if str(sone or "").isdigit() else None,
                                         float(d.get("maks_avstand") or 1.0))
                    r["ok"] = True
                    return self._send(r)
                if path == "/api/pakke":
                    d = json.loads(self._body() or b"{}")
                    dagar = d.get("dagar")
                    zp = INS.lag_pakke(app.cfg_path, loggdir(), app.versjon, bool(d.get("med_raa", True)),
                                       int(dagar) if str(dagar or "").isdigit() else None, app.snapshot())
                    return self._send({"ok": True, "fil": zp.name, "mb": round(zp.stat().st_size / 1048576, 1)})
                return self._err("finst ikkje", 404)
            except ValueError as e:
                return self._err(str(e))
            except Exception as e:
                return self._err(f"{type(e).__name__}: {e}", 500)

    srv = ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
