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
KARTLAG = ("topo", "graatone", "flyfoto", "osm")    # bakgrunnskart i Resultat-fana
WEB = HER / "web"
MAKS_OPPLASTING = 500 * 1024 * 1024


def finn_utstyr(app):
    """Oppstartssjekken (finn_utstyr.py): skann ledige portar, bruk live-data for portane Geoscan alt les,
    finn com0com-para og OneVision-oppsettet, og lag eit forslag."""
    import com0com as C0
    import finn_utstyr as FU
    import innstillingar as INN
    cfgf = dict(app.cfg, **INN._read(app.cfg_path))
    c0c = C0.status(cfgf)
    virtuelle = {x for p in c0c.get("par") or [] for x in (p["geoscan"], p["onevision"]) if x}
    eigne = {n for n, v in app.state.items() if v == "open"}
    portar = INN.porter()
    skanna = FU.skann([p for p in portar if p["port"] not in virtuelle], hopp_over=eigne)
    stat = app.innstat()
    for n in eigne:
        r = dict(stat.get(n) or {"kva": "stille"})
        r.update(port=n, tilstand="brukt av Geoscan",
                 skildring=next((p["skildring"] for p in portar if p["port"] == n), ""),
                 baud=next((int(i.get("baud") or 115200) for i in cfgf.get("inn") or [] if i.get("port") == n), 115200))
        skanna[n] = r
    for v in sorted(virtuelle):
        skanna[v] = {"port": v, "tilstand": "com0com", "kva": "com0com",
                     "skildring": "virtuell kabel til OneVision", "melding": ""}
    ov = FU.les_onevision()
    f, atv = FU.forslag(skanna, c0c, cfgf, ov)
    g = skanna.get(f["mottakar"]) or {}
    f["talker"] = g.get("talker")
    return {"portar": sorted(skanna.values(), key=lambda r: (r.get("kva") != "gnss", r["port"])),
            "forslag": f, "atvaringar": atv, "onevision": ov, "com0com": c0c,
            "noverande": {"mottakar": (cfgf.get("inn") or [{}])[0].get("port"),
                          "onevision": (cfgf.get("ut_seriell") or [{}])[0].get("port") if cfgf.get("ut_seriell") else None}}


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
                    # Les fila, ikkje berre minnet: autolagra endringar gjeld først etter omstart, men skal synast
                    # (og ikkje bli skrivne over) når sida blir opna på nytt.
                    return self._send(INN.hent(app.cfg_path, dict(app.cfg, **INN._read(app.cfg_path))))
                if path == "/api/tema":
                    return self._send({"tema": INN._read(app.cfg_path).get("tema") or app.cfg.get("tema", "mork")})
                if path == "/api/kartlag":
                    return self._send({"kartlag": INN._read(app.cfg_path).get("kartlag") or app.cfg.get("kartlag", "topo")})
                if path == "/api/com0com":
                    import com0com as C0
                    st = C0.status(json.loads(Path(app.cfg_path).read_text(encoding="utf-8"))
                                   if Path(app.cfg_path).exists() else app.cfg)
                    st["skjult"] = app.cfg.get("skjul_com0com", "")
                    st["demo"] = bool(app.cfg.get("demo"))
                    return self._send(st)
                if path == "/api/okt":
                    return self._send(app.okt.status())
                if path == "/api/okter":
                    mine = set((app.okt.noverande or {}).get("loggar") or [])
                    return self._send([dict(o, i_okt=o["fil"] in mine) for o in RES.okter(loggdir())])
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
                if path == "/api/okt/val":
                    d = json.loads(self._body() or b"{}")
                    o = app.okt.fortset() if d.get("val") == "fortset" else app.okt.ny(d.get("namn", ""))
                    return self._send({"ok": True, "okt": o})
                if path == "/api/okt/lagre":
                    app.okt.lagre_ui(json.loads(self._body() or b"{}").get("ui") or {})
                    return self._send({"ok": True})
                if path == "/api/avslutt":
                    app.avslutt()
                    return self._send({"ok": True})
                if path == "/api/sjekk-oppdatering":
                    app.check_update()
                    return self._send({"ok": True, "oppdatering": dict(app.oppd)})
                if path == "/api/tilbake":
                    import oppdater
                    logg = []
                    ok = oppdater.rollback(log=logg.append)
                    if ok:
                        app.oppd["omstart"] = True
                    return self._send({"ok": ok, "logg": logg})
                if path == "/api/omstart":
                    app.oppd["omstart"] = True
                    return self._send({"ok": True})
                if path == "/api/innstillingar":
                    d = json.loads(self._body() or b"{}")
                    t = INN.lagre(app.cfg_path, d, streng=bool(d.get("omstart", True)))
                    # Autolagring frå sida sender omstart=false: berre lagre. Endringane gjeld etter neste omstart.
                    if d.get("omstart", True):
                        app.oppd["omstart"] = True       # nye innstillingar gjeld etter omstart (START-GEOSCAN.bat)
                    return self._send({"ok": True, "lagra": t, "fil": Path(app.cfg_path).name, "feil": INN.lagre.feil,
                                       "har_passord": bool(INN._read(INN.HER / "ntrip_lokal.json").get("passord")),
                                       "har_token": bool(INN._read(INN.HER / "oppdatering_lokal.json").get("token"))})
                if path == "/api/finn_utstyr":
                    return self._send(finn_utstyr(app))
                if path == "/api/bruk_oppsett":
                    d = json.loads(self._body() or b"{}")
                    cfgf = INN._read(app.cfg_path)
                    mot = INN._port(d.get("mottakar"))
                    if not mot:
                        raise ValueError("ingen mottakar å bruke")
                    inn = [{"port": mot, "baud": int(d.get("mottakar_baud") or 115200)}]
                    if INN._port(d.get("imu")):
                        inn.append({"port": INN._port(d["imu"]), "baud": int(d.get("imu_baud") or 115200)})
                    cfgf["inn"] = inn
                    ov = INN._port(d.get("onevision"))
                    if ov:
                        cfgf["ut_seriell"] = [{"port": ov, "baud": 115200, "setningar": ["GGA"]}]
                    if d.get("talker"):
                        # $INGGA = mottakaren rettar masta sjølv (stangspiss). Elles antenne.
                        cfgf["mottakar_kompenserer"] = d["talker"] == "IN"
                    Path(app.cfg_path).write_text(json.dumps(cfgf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    if d.get("omstart"):
                        app.oppd["omstart"] = True
                    return self._send({"ok": True, "lagra": INN.lagra_tid(app.cfg_path)})
                if path == "/api/kjeldetabell":
                    # Mountpoints frå casteren til nedtrekkslista. Tomt passord i skjemaet = bruk det lagra.
                    import ntripklient as NK
                    d = json.loads(self._body() or b"{}")
                    lok = INN._read(INN.HER / "ntrip_lokal.json")
                    caster = INN._caster_reinsk(str(d.get("caster") or lok.get("caster") or ""))
                    if not caster[0]:
                        raise ValueError("skriv inn casteradressa først")
                    pos = (app.k.status.get("pos") or {}) if hasattr(app, "k") else {}
                    try:
                        r = NK.fetch_sourcetable(caster[0], int(d.get("ntrip_port") or caster[1] or lok.get("port") or 2101),
                                                 str(d.get("brukar") or lok.get("brukar") or ""),
                                                 str(d.get("passord") or lok.get("passord") or ""),
                                                 lat=pos.get("lat"), lon=pos.get("lon"), timeout=10)
                    except NK.NtripError as e:
                        raise RuntimeError(str(e))
                    return self._send({"ok": True, "mounts": r["mounts"][:300], "caster": r["caster"]})
                if path == "/api/tema":
                    v = str(json.loads(self._body() or b"{}").get("tema", ""))
                    if v not in ("mork", "dagslys"):
                        raise ValueError("ukjent tema")
                    cfgf = INN._read(app.cfg_path)
                    cfgf["tema"] = v
                    Path(app.cfg_path).write_text(json.dumps(cfgf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    app.cfg["tema"] = v
                    return self._send({"ok": True, "lagra": INN.lagra_tid(app.cfg_path)})
                if path == "/api/kartlag":
                    v = str(json.loads(self._body() or b"{}").get("kartlag", ""))
                    if v not in KARTLAG:
                        raise ValueError("ukjent kart")
                    cfgf = INN._read(app.cfg_path)
                    cfgf["kartlag"] = v
                    Path(app.cfg_path).write_text(json.dumps(cfgf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    app.cfg["kartlag"] = v
                    return self._send({"ok": True, "lagra": INN.lagra_tid(app.cfg_path)})
                if path == "/api/com0com/lag":
                    import com0com as C0
                    pa, pb = C0.lag_par()
                    # Geoscan skriv på A-enden: set «Til OneVision» med ein gong (lagra i fila, gjeld etter omstart)
                    cfgf = INN._read(app.cfg_path)
                    gml = (cfgf.get("ut_seriell") or [{}])[0] if cfgf.get("ut_seriell") else {}
                    cfgf["ut_seriell"] = [dict(gml, port=pa, baud=gml.get("baud", 115200), setningar=["GGA"])]
                    Path(app.cfg_path).write_text(json.dumps(cfgf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    return self._send({"ok": True, "geoscan": pa, "onevision": pb, "lagra": INN.lagra_tid(app.cfg_path)})
                if path == "/api/com0com/skjul":
                    sig = str(json.loads(self._body() or b"{}").get("sig", ""))[:500]
                    cfgf = json.loads(Path(app.cfg_path).read_text(encoding="utf-8")) if Path(app.cfg_path).exists() else {}
                    cfgf["skjul_com0com"] = sig
                    Path(app.cfg_path).write_text(json.dumps(cfgf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    app.cfg["skjul_com0com"] = sig
                    return self._send({"ok": True, "lagra": INN.lagra_tid(app.cfg_path)})
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
                    app.okt.sett_resultat({"fil": src.name, "namn": src.name.split("_", 3)[-1], "z": d.get("z", "auto"),
                                           "sone": sone, "okter": okter, "maks_avstand": d.get("maks_avstand")})
                    return self._send(r)
                if path == "/api/pakke":
                    d = json.loads(self._body() or b"{}")
                    dagar = d.get("dagar")
                    zp = INS.lag_pakke(app.cfg_path, loggdir(), app.versjon, bool(d.get("med_raa", True)),
                                       int(dagar) if str(dagar or "").isdigit() else None, app.snapshot())
                    return self._send({"ok": True, "fil": zp.name, "mb": round(zp.stat().st_size / 1048576, 1)})
                return self._err("finst ikkje", 404)
            except (ValueError, RuntimeError) as e:
                return self._err(str(e))
            except Exception as e:
                return self._err(f"{type(e).__name__}: {e}", 500)

    srv = ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
