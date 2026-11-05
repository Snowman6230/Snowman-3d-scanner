"""Testar for hellingskorreksjonen og NMEA-omskrivinga. Køyr: python -m pytest tests"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))
import helling as H  # noqa: E402
import nmea as N  # noqa: E402
import geoscan as G  # noqa: E402
from geoide import GEOID  # noqa: E402

LAT, LON = 62.39, 6.58  # Sykkylven


def dist_m(la1, lo1, la2, lo2):
    my, mx = H.meter_per_grad(la1)
    return (lo2 - lo1) * mx, (la2 - la1) * my  # (aust, nord)


def test_ortonormale_vektorar():
    rnd = random.Random(1)
    for _ in range(200):
        f, r, u = H.unit_vectors(rnd.uniform(0, 360), rnd.uniform(-30, 30), rnd.uniform(-30, 30))
        for v in (f, r, u):
            assert abs(math.hypot(*v) - 1) < 1e-12
        dot = lambda a, b: sum(x * y for x, y in zip(a, b))
        assert abs(dot(f, r)) < 1e-12 and abs(dot(f, u)) < 1e-12 and abs(dot(r, u)) < 1e-12
        # høgrehandssystem: fram × høgre = ned
        cx = (f[1] * r[2] - f[2] * r[1], f[2] * r[0] - f[0] * r[2], f[0] * r[1] - f[1] * r[0])
        assert all(abs(a + b) < 1e-12 for a, b in zip(cx, u))


def test_vatrett_gir_punkt_rett_under():
    la, lo, h, off = H.correct(LAT, LON, 100.0, (0, 0, 1.2), 37.0, 0.0, 0.0)
    assert abs(la - LAT) < 1e-12 and abs(lo - LON) < 1e-12 and abs(h - 98.8) < 1e-9 and off < 1e-9


def test_stamp_fronten_opp_flyttar_punktet_fram():
    # kurs nord, fronten 10° opp: masta hallar bakover, referansepunktet ligg nord for antenna
    la, lo, h, off = H.correct(LAT, LON, 100.0, (0, 0, 1.0), 0.0, 10.0, 0.0)
    e, n = dist_m(LAT, LON, la, lo)
    assert abs(n - math.sin(math.radians(10))) < 1e-4 and abs(e) < 1e-4
    assert abs(h - (100 - math.cos(math.radians(10)))) < 1e-9


def test_krenging_hogre_ned():
    # kurs aust (høgre = sør), høgre side 5° ned: masta hallar mot sør, punktet ligg nord for antenna
    la, lo, h, off = H.correct(LAT, LON, 100.0, (0, 0, 1.2), 90.0, 0.0, 5.0)
    e, n = dist_m(LAT, LON, la, lo)
    assert abs(n - 1.2 * math.sin(math.radians(5))) < 1e-4 and abs(e) < 1e-4
    assert abs(off * 100 - 10.46) < 0.01  # 5° krenging, 1,2 m mast ≈ 10 cm


def test_spakarm_fram():
    # antenna 0,5 m framfor referansepunktet, vatrett, kurs vest: punktet ligg 0,5 m aust for antenna
    la, lo, h, off = H.correct(LAT, LON, 100.0, (0.5, 0, 1.0), 270.0, 0.0, 0.0)
    e, n = dist_m(LAT, LON, la, lo)
    assert abs(e - 0.5) < 1e-4 and abs(n) < 1e-4


def test_rett_antenne():
    # «rett antenne» = referansepunktet + spakarmen som om vogna var vatrett
    for hdg, p, r in ((0, 10, 0), (90, 0, 5), (213, -7, 4)):
        lever = (0.3, -0.1, 1.2)
        pla, plo, ph, _ = H.correct(LAT, LON, 100.0, lever, hdg, p, r)
        vla, vlo, vh, _ = H.correct_level(LAT, LON, 100.0, lever, hdg, p, r)
        e, n = dist_m(pla, plo, vla, vlo)
        le, ln, lu = H.offset_enu(lever, hdg, 0, 0)
        assert abs(e - le) < 1e-4 and abs(n - ln) < 1e-4 and abs(vh - ph - lu) < 1e-9
    # vatrett: rett antenne = antenna sjølv
    vla, vlo, vh, off = H.correct_level(LAT, LON, 100.0, (0.3, -0.1, 1.2), 50, 0, 0)
    assert abs(vla - LAT) < 1e-12 and abs(vlo - LON) < 1e-12 and abs(vh - 100) < 1e-9 and off < 1e-9


def test_nmea_sjekksum_og_koordinatar():
    line = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    assert N.valid(line)
    assert not N.valid(line[:-2] + "00")
    v, hemi = N.coord_out(N.coord_in("6223.4000000", "N"), True)
    assert (v, hemi) == ("6223.4000000", "N")
    v, hemi = N.coord_out(N.coord_in("00634.8000000", "E"), False)
    assert (v, hemi) == ("00634.8000000", "E")


def _gga(talker="IN", lat="6223.4000000", lon="00634.8000000", alt="150.000", sep="44.775"):
    return N.build([f"{talker}GGA", "120000.00", lat, "N", lon, "E", "4", "18", "0.7", alt, "M", sep, "M", "1.0", "0001"])


def test_talker_blir_verande():
    k = G.Korrigerar(dict(G.STANDARD, logg=None, hoegd="mottakar"))
    out = k.handle(_gga("IN"), now=1.0)[0]
    assert out.startswith("$INGGA,") and N.valid(out)


def test_ende_til_ende_med_pashr():
    cfg = dict(G.STANDARD, logg=None, hoegd="mottakar", utgang="referansepunkt",
               spakarm={"fram": 0, "hogre": 0, "opp": 1.2})
    k = G.Korrigerar(cfg)
    # PASHR: tid, kurs 90 (aust), T, krenging +5 (høgre side ned), stamp 0
    pashr = N.build(["PASHR", "120000.00", "90.0", "T", "5.00", "0.00", "", "0.01", "0.01", "0.02", "2", "1"])
    assert k.handle(pashr, now=1.0) == [pashr]
    out = k.handle(_gga(), now=1.05)[0]
    g = N.parse_gga(N.split(out))
    e, n = dist_m(N.coord_in("6223.4000000", "N"), N.coord_in("00634.8000000", "E"), g["lat"], g["lon"])
    assert abs(n - 1.2 * math.sin(math.radians(5))) < 1e-3 and abs(e) < 1e-3
    assert abs(g["alt"] - (150 - 1.2 * math.cos(math.radians(5)))) < 1e-3
    assert k.status["korrigert"] and abs(k.status["forskyving_cm"] - 10.5) < 0.1


def test_gammal_helling_gir_ukorrigert():
    cfg = dict(G.STANDARD, logg=None, hoegd="mottakar", utgang="rett_antenne")
    k = G.Korrigerar(cfg)
    pashr = N.build(["PASHR", "120000.00", "90.0", "T", "5.00", "0.00", "", "", "", "", "2", "1"])
    k.handle(pashr, now=1.0)
    out = k.handle(_gga(), now=5.0)[0]   # 4 s seinare: hellinga er for gammal
    g = N.parse_gga(N.split(out))
    assert abs(g["lat"] - N.coord_in("6223.4000000", "N")) < 1e-9 and not k.status["korrigert"]


def test_geoide_sykkylven():
    n = GEOID.n(LAT, LON)
    assert n is not None and 35 < n < 50


def test_djupn_25_m_ved_5_grader():
    # kurs aust, høgre side 5° ned: objekt på 2,5 m ligg 2,5·sin5° = 21,8 cm mot nord (oppsida)
    dE, dN, dv = H.object_shift(2.5, 90.0, 0.0, 5.0)
    assert abs(dN - 2.5 * math.sin(math.radians(5))) < 1e-9 and abs(dE) < 1e-9
    assert abs(dv - 2.5 * math.cos(math.radians(5))) < 1e-9


def test_r12i_kompenserer_sjolv():
    # R12i sender stangspissen P. Rett antenne = P + 1,2 m loddrett, same posisjon. Ingen helling trengst.
    cfg = dict(G.STANDARD, logg=None, hoegd="mottakar", utgang="rett_antenne", mottakar_kompenserer=True,
               spakarm={"fram": 0, "hogre": 0, "opp": 1.2})
    k = G.Korrigerar(cfg)
    out = k.handle(_gga(alt="148.800"), now=1.0)[0]
    g = N.parse_gga(N.split(out))
    assert abs(g["lat"] - N.coord_in("6223.4000000", "N")) < 1e-9 and abs(g["alt"] - 150.0) < 1e-6
    cfg["utgang"] = "referansepunkt"
    out = G.Korrigerar(cfg).handle(_gga(alt="148.800"), now=1.0)[0]
    assert abs(N.parse_gga(N.split(out))["alt"] - 148.8) < 1e-6


def test_korriger_objekt_ende_til_ende(tmp_path):
    import korriger_objekt as KO
    import koordinat as KK
    cfg = dict(G.STANDARD, hoegd="mottakar", utgang="referansepunkt", logg=str(tmp_path / "logg"),
               spakarm={"fram": 0, "hogre": 0, "opp": 1.2}, sone="32")
    k = G.Korrigerar(cfg)
    pashr = N.build(["PASHR", "120000.00", "90.0", "T", "5.00", "0.00", "", "", "", "", "2", "1"])
    k.handle(pashr, now=1000.0)
    out = k.handle(_gga(), now=1000.05)[0]
    k.logfile.close()
    g = N.parse_gga(N.split(out))
    E, Nn = KK.utm_forward(g["lat"], g["lon"], 32)
    obj = tmp_path / "ror.csv"
    obj.write_text(f"Id;Aust;Nord;Djupn\nR1;{E:.3f};{Nn:.3f};2,5\n", encoding="utf-8")
    logfile = next((tmp_path / "logg").glob("*.csv"))
    KO.main(["--objekt", str(obj), "--logg", str(logfile), "--ut", str(tmp_path / "ut.csv")])
    head, rows, _ = KO.read_csv(tmp_path / "ut.csv")
    r = dict(zip(head, rows[0]))
    assert abs(float(r["endring_cm"]) - 21.8) < 0.1          # 2,5 m · sin 5°
    assert abs(float(r["djupn_loddrett"]) - 2.490) < 0.001
    # retninga: mot sann nord, i rutenettet rotert med meridiankonvergensen
    dE, dN = float(r["E_retta"]) - E, float(r["N_retta"]) - Nn
    gam = KK.convergence(g["lat"], g["lon"], 32)
    assert abs(math.degrees(math.atan2(dE, dN)) + gam) < 0.5   # mm-avrunding i fila


def _zip(files, top="Snowman-3d-scanner-main"):
    import io as _io
    import zipfile as _zf
    b = _io.BytesIO()
    with _zf.ZipFile(b, "w") as z:
        for name, data in files.items():
            z.writestr(f"{top}/{name}", data)
    return b.getvalue()


def test_oppdatering_reserve_og_tilbake(tmp_path):
    import oppdater as O
    pc = tmp_path / "pc"
    pc.mkdir()
    (pc / "geoscan.py").write_text('VERSJON = "0.2.0"\n', encoding="utf-8")
    (pc / "helling.py").write_text("x = 1\n", encoding="utf-8")
    (pc / "geoscan_config.json").write_text('{"mitt": true}', encoding="utf-8")
    data = _zip({"pc/geoscan.py": 'VERSJON = "0.3.0"\n', "pc/helling.py": "x = 2\n", "pc/ny.py": "y = 1\n",
                 "pc/geoscan_config.json": '{"overskrive": true}', "pc/logg/a.csv": "skal ikkje med",
                 "README.md": "utanfor pc"})
    files = O._files_from_zip(data)
    assert ("geoscan_config.json",) not in files and ("logg", "a.csv") not in files
    n, res = O.install(files, pcdir=pc, log=lambda *_: None)
    assert n == 3 and O.version_of((pc / "geoscan.py").read_text()) == "0.3.0"
    assert (pc / "geoscan_config.json").read_text() == '{"mitt": true}'          # oppsettet er urørt
    assert O.install(files, pcdir=pc, log=lambda *_: None) == (0, None)         # ingenting nytt
    assert O.rollback(pcdir=pc, log=lambda *_: None)
    assert O.version_of((pc / "geoscan.py").read_text()) == "0.2.0"
    assert (pc / "helling.py").read_text() == "x = 1\n" and not (pc / "ny.py").exists()


def test_oydelagd_versjon_blir_ikkje_lagd_inn(tmp_path):
    import oppdater as O
    pc = tmp_path / "pc"
    pc.mkdir()
    (pc / "geoscan.py").write_text('VERSJON = "0.2.0"\n', encoding="utf-8")
    files = O._files_from_zip(_zip({"pc/geoscan.py": 'VERSJON = "0.3.0"\ndef (:\n'}))
    try:
        O.install(files, pcdir=pc, log=lambda *_: None)
        assert False, "skulle ha feila"
    except RuntimeError:
        pass
    assert O.version_of((pc / "geoscan.py").read_text()) == "0.2.0" and not (pc / "reserve").exists()


def _logg_med_helling(tmp_path, roll=5.0):
    cfg = dict(G.STANDARD, hoegd="nn2000", utgang="rett_antenne", logg=str(tmp_path / "logg"),
               spakarm={"fram": 0, "hogre": 0, "opp": 1.4}, sone="32")
    k = G.Korrigerar(cfg)
    pashr = N.build(["PASHR", "120000.00", "90.0", "T", f"{roll:.2f}", "0.00", "", "", "", "", "2", "1"])
    k.handle(pashr, now=1000.0)
    out = k.handle(_gga(), now=1000.05)[0]
    k.logfile.close()
    return N.parse_gga(N.split(out)), next((tmp_path / "logg").glob("*.csv"))


def test_geojson_utm33_djupn_og_hoegd(tmp_path):
    import json as _json
    import korriger_objekt as KO
    import koordinat as KK
    g, logfile = _logg_med_helling(tmp_path)
    # rett antenne → bakken under radaren: same horisontale punkt, 1,4 m lågare
    la, lo = g["lat"], g["lon"]
    E, Nn = KK.utm_forward(la, lo, 33)                     # objekta i UTM33 (EPSG 5973), loggen i UTM32
    h_bakke = g["alt"] - 1.4
    for z, mode in ((2.5, "djupn"), (round(h_bakke - 2.5, 3), "hoegd")):
        gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::5973"}},
              "features": [{"type": "Feature", "properties": {"id": 1},
                            "geometry": {"type": "LineString", "coordinates": [[E, Nn, z], [E + 0.2, Nn, z]]}}]}
        src = tmp_path / f"inn_{mode}.geojson"
        src.write_text(_json.dumps(gj))
        KO.main(["--objekt", str(src), "--logg", str(logfile), "--ut", str(tmp_path / "ut.geojson")])
        res = _json.loads((tmp_path / "ut.geojson").read_text())
        f = res["features"][0]
        p = f["geometry"]["coordinates"][0]
        assert f["properties"]["helling_retta"] == "2/2"
        assert abs(math.hypot(p[0] - E, p[1] - Nn) - 2.5 * math.sin(math.radians(5))) < 0.002
        dv = 2.5 * math.cos(math.radians(5))
        assert abs(p[2] - (dv if mode == "djupn" else h_bakke - dv)) < 0.002


def _free_port():
    import socket as _s
    with _s.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_ende_til_ende_simulator_ntrip_tcp_status(tmp_path):
    """Simulert mottakar + falsk caster → App → TCP-klient og statusside. Køyrer ca. 4 s."""
    import json as _json
    import socket as _s
    import threading as _t
    import time as _time
    import urllib.request as _u
    import simuler as S
    stop = _t.Event()
    pm, pc, pt, ps = (_free_port() for _ in range(4))
    m, c = S.Mottakar(hz=10), S.FalskCaster()
    _t.Thread(target=m.serve, args=(pm, stop), daemon=True).start()
    _t.Thread(target=c.serve, args=(pc, stop), daemon=True).start()
    _time.sleep(0.3)
    cfg = dict(G.STANDARD, inn=[{"port": f"socket://127.0.0.1:{pm}"}], ut_seriell=[], tcp_port=pt, status_port=ps,
               logg=str(tmp_path / "logg"), opptak=True, sjekk_oppdatering=False, hoegd="nn2000",
               ntrip={"pa": True, "caster": "127.0.0.1", "port": pc, "mountpoint": "SIM", "versjon": "1",
                      "gga_intervall": 1})
    app = G.App(cfg)
    app.start()
    try:
        _time.sleep(0.5)
        cl = _s.create_connection(("127.0.0.1", pt), timeout=3)
        _time.sleep(3.0)
        data = cl.recv(65536).decode()
        cl.close()
        st = _json.loads(_u.urlopen(f"http://127.0.0.1:{ps}/status", timeout=3).read())
        side = _u.urlopen(f"http://127.0.0.1:{ps}/", timeout=3).read().decode()
    finally:
        app.ntrip.stop.set()
        stop.set()
    ggas = [l for l in data.splitlines() if l.startswith("$INGGA")]
    assert ggas and all(N.valid(l) for l in ggas)
    assert st["korr"]["korrigert"] and st["korr"]["hellingskjelde"] == "PASHR"
    assert st["ntrip"]["tilstand"] == "tilkopla" and st["ntrip"]["byte"] > 0
    assert m.rtcm_bytes > 0 and c.gga > 0                      # RTCM kom fram til «mottakaren», GGA til casteren
    assert "Snowman Geoscan" in side and "Alpindata v/Hans Petter B. Sørensen" in side
    assert list((tmp_path / "logg").glob("raa_*.nmea")) and list((tmp_path / "logg").glob("geoscan_*.csv"))


def test_demo_brukar_aldri_ekte_ntrip_innlogging(tmp_path):
    import json as _json
    import ntrip_teneste as NT
    (tmp_path / "ntrip_lokal.json").write_text(_json.dumps({"caster": "ekte.caster.no", "passord": "hemmeleg"}))
    demo = _json.loads((Path(__file__).resolve().parent.parent / "pc" / "geoscan_config_demo.json").read_text())
    assert demo["demo"] is True
    n = NT.load(demo, tmp_path)
    assert n["caster"] == "127.0.0.1" and n.get("passord", "") == ""
    assert NT.load({"ntrip": {"pa": True}}, tmp_path)["caster"] == "ekte.caster.no"


def test_nettlesar_api_resultat_send_inn_innstillingar(tmp_path, monkeypatch):
    """Heile arbeidsflyten til operatøren via nettlesar-API-et: skann (simulert) → last opp eksport → rett →
    last ned DXF → svar på spørsmål → lag pakke (utan passord) → lagre innstillingar."""
    import json as _json
    import threading as _t
    import time as _time
    import urllib.request as _u
    import zipfile as _zf
    import innsending as INS
    import innstillingar as INN
    import koordinat as KK
    import simuler as S
    import webtenar as W
    from urllib.parse import quote as _uq
    for mod in (INS, INN, W):
        monkeypatch.setattr(mod, "HER", tmp_path)
    (tmp_path / "ntrip_lokal.json").write_text(_json.dumps({"caster": "c.no", "brukar": "norman", "passord": "hemmeleg"}))
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text("{}")
    stop = _t.Event()
    pm, ps = _free_port(), _free_port()
    m = S.Mottakar(hz=10, speed=2.0)
    _t.Thread(target=m.serve, args=(pm, stop), daemon=True).start()
    _time.sleep(0.3)
    cfg = dict(G.STANDARD, inn=[{"port": f"socket://127.0.0.1:{pm}"}], ut_seriell=[], tcp_port=_free_port(),
               status_port=ps, logg=str(tmp_path / "logg"), sjekk_oppdatering=False, opne_nettlesar=False)
    app = G.App(cfg, cfgp)
    app.start()
    base = f"http://127.0.0.1:{ps}/"

    def get(p):
        return _json.loads(_u.urlopen(base + p, timeout=5).read())

    def post(p, data=None, raw=None):
        body = raw if raw is not None else _json.dumps(data or {}).encode()
        return _json.loads(_u.urlopen(_u.Request(base + p, data=body, method="POST"), timeout=10).read())
    try:
        _time.sleep(3.0)
        app.k.logfile.flush()
        okter = get("api/okter")
        assert okter and okter[0]["med_helling"] > 5
        spor = get("api/spor?fil=" + okter[0]["fil"])
        med = [p for p in spor if p[3] == 1]
        assert len(med) > 5 and all(5.5 < p[2] < 7.0 for p in med)       # ±6° krenging + litt stamp
        # eksport i UTM33 langs sporet, 2,0 m djupt
        pts = [KK.utm_forward(p[0], p[1], 33) for p in med[::max(1, len(med) // 4)]]
        gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::5973"}},
              "features": [{"type": "Feature", "properties": {"id": 7, "layer": "Vatn", "type": "Pipe"},
                            "geometry": {"type": "LineString", "coordinates": [[e, n, 2.0] for e, n in pts]}}]}
        up = post("api/last-opp?type=eksport&namn=r%C3%B8yr.geojson", raw=_json.dumps(gj).encode())
        r = post("api/rett", {"fil": up["fil"], "z": "auto"})
        assert r["ok"] and r["z"] == "djupn" and r["sone"] == 33 and r["retta_punkt"] >= 2
        assert 2.0 * math.sin(math.radians(5.5)) * 100 < r["tabell"][0]["maks_endring_cm"] < 2.0 * math.sin(math.radians(7)) * 100
        dxf = _u.urlopen(base + "last-ned/resultat/" + _uq(r["filer"]["dxf"]), timeout=5).read().decode()
        assert "POLYLINE" in dxf and "Vatn" in dxf and dxf.rstrip().endswith("EOF")
        assert r["filer"]["geojson"] == "røyr_retta.geojson"
        # svar og pakke
        post("api/svar", {"namn": "Norman", "svar": {"mast": "1,45", "ukjend": "x"}})
        pk = post("api/pakke", {"med_raa": True})
        with _zf.ZipFile(tmp_path / "pakkar" / pk["fil"]) as z:
            names = z.namelist()
            alt = b"".join(z.read(n) for n in names)
        assert "SVAR.txt" in names and any(n.startswith("logg/") for n in names) and any(n.startswith("filer/") for n in names)
        assert b"hemmeleg" not in alt and b"norman" not in alt and "1,45".encode() in alt
        # innstillingar: passordet blir aldri sendt ut, tomt passord = behald
        ii = get("api/innstillingar")
        assert ii["har_passord"] and "passord" not in ii
        post("api/innstillingar", dict(ii, mottakar="COM23", mast="1,45", sone="33", passord=""))
        saved = _json.loads(cfgp.read_text())
        assert saved["spakarm"]["opp"] == 1.45 and saved["sone"] == "33" and saved["inn"][0]["port"] == "COM23"
        assert _json.loads((tmp_path / "ntrip_lokal.json").read_text())["passord"] == "hemmeleg"
        assert app.oppd["omstart"]
        try:
            post("api/innstillingar", dict(ii, mottakar="COM23", mast="tjue"))
            assert False
        except _u.HTTPError as e:
            assert e.code == 400 and "mastehøgd" in _json.loads(e.read())["feil"]
    finally:
        stop.set()
