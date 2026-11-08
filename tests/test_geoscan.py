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
    assert "Snowman Geoscan" in side and "Alpindata HP Brunstad Sørensen" in side
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
        dxf = _u.urlopen(base + "last-ned/resultat/" + _uq(r["filer"]["dxf"]), timeout=5).read().decode("cp1252")
        assert "POLYLINE" in dxf and "Vatn" in dxf and dxf.rstrip().endswith("EOF")
        assert "Vatn_DJUPN" in dxf and "1,99 m" in dxf                      # djupna som tekst på teikninga
        t0 = r["tabell"][0]
        assert t0["djupn_for"]["snitt"] == 2.0 and 1.985 < t0["djupn_etter"]["snitt"] < 1.996   # 2,0 · cos 6°
        pr = r["etter"]["features"][0]["properties"]
        assert len(pr["djupn_retta_m"]) == len(r["etter"]["features"][0]["geometry"]["coordinates"])
        # koordinatar og høgd over havet for objektet under bakken
        assert len(pr["utm_e"]) == len(pr["djupn_retta_m"]) and abs(pr["utm_e"][0] - pts[0][0]) < 0.5
        hb, ho, d1 = pr["bakke_nn2000_m"][0], pr["hoegd_nn2000_m"][0], pr["djupn_retta_m"][0]
        assert hb is not None and abs(ho - (hb - d1)) < 0.002
        # simulert antenne − mast. Toleransen dekkjer sidearmen (0,6 m) i ±6° krenging: 0,6 · sin 6° ≈ 6 cm
        assert abs(hb - (150.0 + 44.775 - GEOID.n(*spor[0][:2]) - G.STANDARD["spakarm"]["opp"])) < 0.1
        csvraw = _u.urlopen(base + "last-ned/resultat/" + _uq(r["filer"]["csv"]), timeout=5).read()
        assert csvraw.startswith(b"\xef\xbb\xbf")            # BOM, så Excel les æøå og – rett
        csvtxt = csvraw.decode("utf-8-sig")
        assert csvtxt.startswith("Snowman Geoscan – Alpindata HP Brunstad Sørensen")      # tittellina
        assert "djupn_retta_m" in csvtxt.splitlines()[1] and ";1,989;" in csvtxt and "." not in csvtxt.splitlines()[2]
        # namnet og signaturen er med i alle filtypane
        import opphav as OP
        gjtxt = _u.urlopen(base + "last-ned/resultat/" + _uq(r["filer"]["geojson"]), timeout=5).read()
        assert OP.sjekk_signatur(dxf) and OP.sjekk_signatur(csvtxt) and OP.sjekk_signatur(gjtxt)
        assert "SNOWMAN_GEOSCAN" in dxf and "Alpindata HP Brunstad Sørensen" in dxf
        assert r["filer"]["geojson"] == "røyr_retta.geojson"
        # svar og pakke
        post("api/svar", {"namn": "Norman", "svar": {"mast": "1,45", "ukjend": "x"}})
        pk = post("api/pakke", {"med_raa": True})
        with _zf.ZipFile(tmp_path / "pakkar" / pk["fil"]) as z:
            names = z.namelist()
            assert OP.sjekk_signatur(z.comment) and OP.SIGNATUR in z.read("SVAR.txt").decode()
            alt = b"".join(z.read(n) for n in names)
        assert "SVAR.txt" in names and any(n.startswith("logg/") for n in names) and any(n.startswith("filer/") for n in names)
        assert b"hemmeleg" not in alt and b"norman" not in alt and "1,45".encode() in alt
        # innstillingar: passordet blir aldri sendt ut, tomt passord = behald
        ii = get("api/innstillingar")
        assert ii["har_passord"] and "passord" not in ii
        post("api/innstillingar", dict(ii, mottakar="COM23", mast="1,45", sone="33", passord=""))
        saved = _json.loads(cfgp.read_text())
        assert saved["spakarm"]["opp"] == 1.45 and saved["sone"] == "33" and saved["inn"][0]["port"] == "COM23"
        post("api/innstillingar", dict(ii, mottakar="COM23", radar_djupn="6,0", passord=""))
        assert _json.loads(cfgp.read_text())["radar_djupn"] == 6.0
        assert _json.loads((tmp_path / "ntrip_lokal.json").read_text())["passord"] == "hemmeleg"
        assert app.oppd["omstart"]
        try:
            post("api/innstillingar", dict(ii, mottakar="COM23", mast="tjue"))
            assert False
        except _u.HTTPError as e:
            assert e.code == 400 and "mastehøgd" in _json.loads(e.read())["feil"]
    finally:
        stop.set()


def test_oppdatering_rorer_aldri_data_fra_operatoren():
    import oppdater as O
    files = O._files_from_zip(_zip({"pc/geoscan.py": 'VERSJON = "9.9.9"\n', "pc/innsendt/svar.json": "{}",
                                    "pc/pakkar/a.zip": "x", "pc/resultat/r.dxf": "x", "pc/ntrip_lokal.json": "{}"}))
    assert list(files) == [("geoscan.py",)]


def test_tom_logg_stoppar_ikkje_rettinga(tmp_path):
    """Ein logg som nettopp er oppretta (berre overskrift) eller er tom, skal hoppast over."""
    import korriger_objekt as KO
    import resultat as RES
    g, logfile = _logg_med_helling(tmp_path)
    (tmp_path / "logg" / "geoscan_20990101_000000.csv").write_text(G.LOGG_HOVUD + "\n", encoding="utf-8")
    (tmp_path / "logg" / "geoscan_20990101_000001.csv").write_text("", encoding="utf-8")
    logs = sorted((tmp_path / "logg").glob("geoscan_*.csv"))
    assert len(KO.Logg(logs).rows) == 1
    ok = RES.okter(tmp_path / "logg")
    assert len(ok) == 3 and sum(o["med_helling"] for o in ok) == 1


def test_signatur_og_retta_csv_kan_lesast_att(tmp_path):
    """Tittellina med namnet skal ikkje øydeleggje innlesinga når ei retta CSV blir brukt på nytt."""
    import korriger_objekt as KO
    import opphav as OP
    p = tmp_path / "x.csv"
    p.write_text(f"{OP.NAMN} – {OP.PRODUSENT};01.01.2026;{OP.SIGNATUR}\nAust;Nord;Djupn\n1;2;3\n", encoding="utf-8")
    head, rows, d = KO.read_csv(p)
    assert head == ["Aust", "Nord", "Djupn"] and rows == [["1", "2", "3"]]
    assert OP.SIGNATUR.startswith("SNWGEO-") and OP.sjekk_signatur(OP.generator("1.0"))
    assert not OP.sjekk_signatur("anna program")


def test_sjekkliste_meldingar_og_pakke(tmp_path, monkeypatch):
    """Norman fyller ut sjekklista → pakka har SJEKKLISTE.txt og e-postadressa. Utviklaren svarar i
    meldingar.json → svaret kjem ved punktet, og meldinga kan merkjast som lesen."""
    import json as _json
    import zipfile as _zf
    import innsending as INS
    import opphav as OP
    monkeypatch.setattr(INS, "HER", tmp_path)
    INS.sjekk_lagre({"punkt": {"d1": {"status": "ok", "kommentar": "fint"}, "n2": {"status": "feil", "kommentar": "berre FLOAT"},
                               "xx": {"status": "ok"}, "d2": {"status": "tull"}}})
    s = INS.sjekk_les()["punkt"]
    assert s["d1"]["status"] == "ok" and s["n2"]["kommentar"] == "berre FLOAT" and "xx" not in s and s["d2"]["status"] == ""
    zp = INS.lag_pakke(tmp_path / "geoscan_config.json", tmp_path / "logg", "0.7.0")
    with _zf.ZipFile(zp) as z:
        sj = z.read("SJEKKLISTE.txt").decode()
        assert "1 godkjent" in sj and "1 ikkje godkjent" in sj and "berre FLOAT" in sj and "[X]" in sj
        assert OP.KONTAKT_EPOST in z.read("SVAR.txt").decode() and "sjekkliste.json" in z.namelist()
    (tmp_path / "meldingar.json").write_text(_json.dumps({"meldingar": [
        {"id": "b", "versjon": "0.7.1", "tittel": "Retta RTK", "sjekk": {"n2": {"tekst": "Bruk COM20", "prov_att": True}}},
        {"id": "a", "versjon": "0.7.0", "tittel": "Velkomen", "sjekk": {"n2": "gammalt svar", "d1": "takk"}}]}), encoding="utf-8")
    m = INS.meldingar()
    assert m["sjekk_svar"]["n2"] == {"tekst": "Bruk COM20", "prov_att": True, "versjon": "0.7.1", "dato": None}
    assert m["sjekk_svar"]["d1"]["tekst"] == "takk" and not any(x["lest"] for x in m["meldingar"])
    INS.melding_lest("b")
    assert [x["lest"] for x in INS.meldingar()["meldingar"]] == [True, False]


def test_meldingar_json_i_repoet_er_gyldig():
    import json as _json
    m = _json.loads((Path(__file__).resolve().parent.parent / "pc" / "meldingar.json").read_text(encoding="utf-8"))
    ids = [x["id"] for x in m["meldingar"]]
    assert ids and len(ids) == len(set(ids)) and all(x.get("tittel") for x in m["meldingar"])


def test_oppdatering_seier_ifra_om_privat_repo_utan_nokkel(monkeypatch):
    import io as _io
    import urllib.error
    import oppdater as O

    def privat(*a, **k):
        raise urllib.error.HTTPError("u", 404, "Not Found", {}, _io.BytesIO(b""))
    monkeypatch.setattr(O, "_get", privat)
    assert O.check()[1:] == (None, False) and O.SISTE_FEIL[0] == "nokkel"

    def utan_nett(*a, **k):
        raise OSError("ingen nett")
    monkeypatch.setattr(O, "_get", utan_nett)
    O.check()
    assert O.SISTE_FEIL[0] == "nett"
    monkeypatch.setattr(O, "_get", lambda *a, **k: b'VERSJON = "99.0.0"\n')
    assert O.check()[2] is True and O.SISTE_FEIL[0] is None


def test_okt_ny_fortset_og_arkiv(tmp_path):
    """Første oppstart: ny økt utan spørsmål. Neste: val. «Hald fram» tek med loggen frå denne oppstarten;
    «ny» arkiverer den førre. Omstart (oppdatering) held fram utan spørsmål."""
    from okt import Okt
    a = Okt(tmp_path)
    a.legg_til_logg("geoscan_1.csv")
    a.auto(omstart=False)
    assert a.val_gjort and a.noverande["loggar"] == ["geoscan_1.csv"]
    a.sett_resultat({"fil": "x.geojson", "namn": "x.geojson"})
    a.lagre_ui({"fane": "resultat", "valt": [1]})
    b = Okt(tmp_path)                                   # neste oppstart
    b.legg_til_logg("geoscan_2.csv")
    b.auto(omstart=False)
    st = b.status()
    assert not st["val_gjort"] and st["forrige"]["skanningar"] == 1 and st["forrige"]["resultat"] == "x.geojson"
    o = b.fortset()
    assert o["loggar"] == ["geoscan_1.csv", "geoscan_2.csv"] and o["ui"]["valt"] == [1] and o["resultat"]["fil"] == "x.geojson"
    c = Okt(tmp_path)
    c.auto(omstart=True)                                # omstart: same økt, ikkje spørsmål
    assert c.val_gjort and c.noverande["id"] == o["id"]
    d = Okt(tmp_path)
    n = d.ny("Storgata 12")
    assert n["namn"] == "Storgata 12" and n["resultat"] is None and n["id"] != o["id"]
    assert len(list((tmp_path / "okt_arkiv").glob("*.json"))) == 1


def test_avslutt_og_okt_via_api(tmp_path, monkeypatch):
    import json as _json
    import time as _time
    import urllib.request as _u
    import innsending as INS
    import webtenar as W
    for mod in (INS, W):
        monkeypatch.setattr(mod, "HER", tmp_path)
    ps = _free_port()
    cfg = dict(G.STANDARD, inn=[{"port": "socket://127.0.0.1:1"}], ut_seriell=[], tcp_port=_free_port(), status_port=ps,
               logg=str(tmp_path / "logg"), sjekk_oppdatering=False, opne_nettlesar=False)
    app = G.App(cfg, tmp_path / "cfg.json")
    app.start()
    _time.sleep(0.3)
    base = f"http://127.0.0.1:{ps}/"
    post = lambda p, d=None: _json.loads(_u.urlopen(_u.Request(base + p, data=_json.dumps(d or {}).encode(), method="POST"), timeout=5).read())
    st = _json.loads(_u.urlopen(base + "api/okt", timeout=5).read())
    assert st["val_gjort"] and st["noverande"]["loggar"]                 # første oppstart: ny økt, loggen med
    post("api/okt/lagre", {"ui": {"fane": "resultat", "grav": 150}})
    assert _json.loads((tmp_path / "logg" / "okt.json").read_text())["ui"]["grav"] == 150
    assert not app.oppd["avslutt"]
    post("api/avslutt")
    assert app.oppd["avslutt"] and app.ntrip.stop.is_set()


def _lag_svy(path, epsg=32632):
    """Ei lita, syntetisk OneVision .svy-fil i same format som Kagholvegen-fila (ingen ekte måledata)."""
    import base64
    import struct

    def target(namn, typ, punkt):
        nb = namn.encode("utf-16le")
        b = b"<Target>" + struct.pack("<III", 0, typ, len(nb)) + nb + bytes(25)
        for tvers, langs, e, n, d in punkt:
            b += struct.pack("<5dII", tvers, langs, e, n, d, 1, 1) + struct.pack("<d", 1e8)
        return b
    data = (target("L10032", 2, [(0.4785, 2.2, 375090.15, 6920839.74, 0.811), (0.4785, 2.3, 375090.18, 6920839.83, 0.811)])
            + target("T10047", 1, [(-0.383, 12.35, 375098.36, 6920846.53, 0.116), (0.383, 12.35, 375097.98, 6920847.21, 0.116)]))
    xml = (f'<Project SVY="3"><Survey><SpatialReferenceSystem><Projection Name="UTM Zone 32N"><EPSGCode>{epsg}'
           f'</EPSGCode></Projection></SpatialReferenceSystem><Targets><PropagationVelocity>100000000.00'
           f'</PropagationVelocity><Data>{base64.b64encode(data).decode()}</Data></Targets></Survey></Project>')
    path.write_text(xml, encoding="utf-8")
    return path


def test_svy_objekt_les_onevision_targets(tmp_path):
    import json
    import svy_objekt as S
    import korriger_objekt as KO
    import resultat as R
    p = _lag_svy(tmp_path / "maaling.svy")
    gj = S.svy_til_geojson(p)
    f = gj["features"]
    assert [x["properties"]["namn"] for x in f] == ["L10032", "T10047"]
    assert f[0]["properties"]["type"] == "linje" and f[1]["properties"]["type"] == "punkt"
    assert f[0]["geometry"]["coordinates"][0] == [375090.15, 6920839.74, 0.811]
    assert f[1]["properties"]["djupn_maks_m"] == 0.116 and f[0]["properties"]["fart_m_ns"] == 0.1
    assert KO.geojson_zone(gj) == 32                       # sona blir lesen frå crs (EPSG:32632)
    assert R.les_objekt(p)["features"][0]["properties"]["namn"] == "L10032"   # Resultat-fana tek .svy direkte
    ut = tmp_path / "o.geojson"
    S.main([str(p), str(ut)])
    assert len(json.loads(ut.read_text(encoding="utf-8"))["features"]) == 2


def test_utgang_heng_ikkje_naar_onevision_ikkje_les(monkeypatch):
    """Les ingen den andre enden av com0com-paret, skal linja kastast, ikkje stoppe Geoscan."""
    import serial
    import time as _t

    class Full:
        def __init__(self): self.n = 0
        def write(self, d):
            self.n += 1
            raise serial.SerialTimeoutException("Write timeout")
        def close(self): pass
    full, opna = Full(), []
    monkeypatch.setattr(G, "open_port", lambda spec, wt=None: (opna.append(wt), full)[1])
    u = G.Utgangar({"ut_seriell": [{"port": "COM34"}]})
    t0 = _t.time()
    for _ in range(5):
        u.send("$GPGGA,094016.70,6223.8710022,N,00634.9919464,E,4,20,0.60,14.594,M,45.01,M,01,2769*52")
    assert _t.time() - t0 < 1 and full.n == 5 and u.ports[0]["kasta"] == 5
    assert opna == [G.UT_SKRIVETID]                  # opna éin gong, med skrivetidsgrense, ikkje lukka/opna på nytt
    assert "ingen les" in u.ports[0]["feil"]


def test_utgang_berre_valde_setningar(monkeypatch):
    class P:
        def __init__(self): self.d = []
        def write(self, d): self.d.append(d)
        def close(self): pass
    p = P()
    monkeypatch.setattr(G, "open_port", lambda spec, wt=None: p)
    u = G.Utgangar({"ut_seriell": [{"port": "COM34", "setningar": ["GGA"]}]})
    for l in ("$GPGGA,1*00", "$GPRMC,1*00", "$INGGA,2*00", "$PTNL,AVR,1*00"):
        u.send(l)
    assert [d.decode()[:6] for d in p.d] == ["$GPGGA", "$INGGA"]


def test_com0com_finn_par_og_forslag():
    import com0com as C
    portar = [("COM23", "Trimble USB", "USB VID:PID=1234:5678"),
              ("COM34", "com0com - serial port emulator CNCA0 (COM34)", "COM0COM\\PORT\\CNCA0"),
              ("COM24", "com0com - serial port emulator CNCB0 (COM24)", "COM0COM\\PORT\\CNCB0")]
    st = C.status({"ut_seriell": [{"port": "COM34"}]}, portar=portar, setupc_tekst="", windows=True, teneste=True, register=[])
    assert st["installert"] and st["par"] == [{"n": 0, "geoscan": "COM34", "onevision": "COM24", "emubr": False}]
    assert st["forslag"] == {"geoscan": "COM34", "onevision": "COM24"} and not st["atvaringar"]
    # brukaren har valt B-enden til Geoscan → OneVision skal lese A-enden
    st = C.status({"ut_seriell": [{"port": "COM24"}]}, portar=portar, setupc_tekst="", windows=True, teneste=True, register=[])
    assert st["forslag"] == {"geoscan": "COM24", "onevision": "COM34"}
    # feil port valt, og setupc seier EmuBR=yes
    st = C.status({"ut_seriell": [{"port": "COM5"}]}, portar=portar, windows=True, teneste=True, register=[],
                  setupc_tekst="       CNCA0 PortName=COM34,EmuBR=yes\n       CNCB0 PortName=COM24\n")
    assert any("ikkje ein com0com-port" in a for a in st["atvaringar"])
    assert any("emulate baud rate" in a for a in st["atvaringar"])


def test_com0com_ikkje_installert_og_utan_par():
    import com0com as C
    st = C.status({}, portar=[("COM23", "Trimble USB", "USB")], setupc_tekst="", windows=True, teneste=False, register=[])
    assert st["stotta"] and st["installert"] is False and st["par"] == [] and "sourceforge" in st["nedlasting"]
    st = C.status({}, portar=[], setupc_tekst="", windows=True, teneste=True, register=[])
    assert st["installert"] and any("ikkje noko portpar" in a for a in st["atvaringar"])
    assert C.status({}, windows=False)["stotta"] is False
    par, emu = C.les_setupc("       CNCA1 PortName=COM40\n       CNCB1 PortName=-\n")
    assert par == {1: {"A": "COM40", "B": "CNCB1"}} and emu == {}


def test_innstillingar_autolagring_utan_omstart(tmp_path, monkeypatch):
    """Autolagring skriv fila og gir tidspunkt tilbake, men startar ikkje Geoscan på nytt."""
    import json as _json
    import threading as _t
    import urllib.request as _u
    import innstillingar as INN
    import webtenar as W
    for mod in (INN, W):
        monkeypatch.setattr(mod, "HER", tmp_path)
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text("{}")
    app = G.App(dict(G.STANDARD, inn=[], ut_seriell=[], tcp_port=None, status_port=0,
                     logg=str(tmp_path / "logg"), ntrip={"pa": False}), cfgp)
    srv = W.start(app, 0)
    port = srv.server_address[1]

    def post(url, d):
        r = _u.Request(f"http://127.0.0.1:{port}{url}", data=_json.dumps(d).encode(), headers={"Content-Type": "application/json"})
        return _json.loads(_u.urlopen(r).read())
    try:
        d = dict(INN.hent(cfgp, {}), mottakar="COM23", onevision="COM34", mast="1,8", hogre="-0,6", omstart=False)
        r = post("/api/innstillingar", d)
        assert r["ok"] and r["lagra"] and r["fil"] == "geoscan_config.json"
        assert app.oppd["omstart"] is False
        c = _json.loads(cfgp.read_text())
        assert c["spakarm"]["opp"] == 1.8 and c["spakarm"]["hogre"] == -0.6
        assert c["ut_seriell"][0] == {"port": "COM34", "baud": 115200, "setningar": ["GGA"]}
        assert INN.hent(cfgp, c)["lagra_tid"] == r["lagra"]
        h = _json.loads(_u.urlopen(f"http://127.0.0.1:{port}/api/innstillingar").read())
        assert h["onevision"] == "COM34" and h["mast"] == 1.8     # sida viser det lagra, ikkje det gamle i minnet
        post("/api/com0com/skjul", {"sig": "[true,[]]"})
        assert _json.loads(cfgp.read_text())["skjul_com0com"] == "[true,[]]"
        assert _json.loads(cfgp.read_text())["spakarm"]["opp"] == 1.8      # andre innstillingar står urørt
        st = _json.loads(_u.urlopen(f"http://127.0.0.1:{port}/api/com0com").read())
        assert "stotta" in st and st["skjult"] == "[true,[]]"
        # eitt ugyldig felt: resten blir lagra, det ugyldige beheld gammal verdi og blir meldt tilbake
        r = post("/api/innstillingar", dict(d, mast="abc", fram="0,25", mottakar=""))
        c = _json.loads(cfgp.read_text())
        assert set(r["feil"]) == {"mast", "mottakar"} and "behalden" in r["feil"]["mast"]
        assert c["spakarm"] == {"fram": 0.25, "hogre": -0.6, "opp": 1.8} and c["inn"][0]["port"] == "COM23"
        d["omstart"] = True
        post("/api/innstillingar", d)
        assert app.oppd["omstart"] is True
    finally:
        srv.shutdown()


def test_kartlag_blir_lagra(tmp_path, monkeypatch):
    import json as _json
    import urllib.error as _ue
    import urllib.request as _u
    import innstillingar as INN
    import webtenar as W
    for mod in (INN, W):
        monkeypatch.setattr(mod, "HER", tmp_path)
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text(_json.dumps({"spakarm": {"opp": 1.8}}))
    app = G.App(dict(G.STANDARD, inn=[], ut_seriell=[], tcp_port=None, status_port=0,
                     logg=str(tmp_path / "logg"), ntrip={"pa": False}), cfgp)
    srv = W.start(app, 0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def post(d):
        r = _u.Request(base + "/api/kartlag", data=_json.dumps(d).encode(), headers={"Content-Type": "application/json"})
        return _json.loads(_u.urlopen(r).read())
    try:
        assert _json.loads(_u.urlopen(base + "/api/kartlag").read())["kartlag"] == "topo"
        assert post({"kartlag": "flyfoto"})["ok"]
        r = _u.Request(base + "/api/tema", data=_json.dumps({"tema": "dagslys"}).encode(), headers={"Content-Type": "application/json"})
        assert _json.loads(_u.urlopen(r).read())["ok"]
        assert _json.loads(_u.urlopen(base + "/api/tema").read())["tema"] == "dagslys"
        assert _json.loads(_u.urlopen(base + "/api/kartlag").read())["kartlag"] == "flyfoto"
        c = _json.loads(cfgp.read_text())
        assert c["kartlag"] == "flyfoto" and c["spakarm"]["opp"] == 1.8       # andre innstillingar står urørt
        try:
            post({"kartlag": "tull"})
            assert False
        except _ue.HTTPError:
            pass
    finally:
        srv.shutdown()


def test_portnamn_blir_retta():
    import innstillingar as INN
    assert G.portnamn("25") == "COM25" and G.portnamn(" com3 ") == "COM3" and G.portnamn("COM34") == "COM34"
    assert G.portnamn("/dev/ttyUSB0") == "/dev/ttyUSB0" and G.portnamn("socket://x:1") == "socket://x:1"
    assert INN._port("25") == "COM25" and INN._port("com24") == "COM24" and INN._port("") == ""


def test_com0com_lag_par_kommando_og_ledige_portar():
    import com0com as C
    assert C.ledig_par(["COM3", "COM23"]) == ("COM34", "COM24")
    assert C.ledig_par(["COM34"]) == ("COM35", "COM25")
    k = C.lag_par_kommando(r"C:\Program Files (x86)\com0com\setupc.exe", "COM34", "COM24")
    assert k[0] == "powershell" and "-Verb RunAs" in k[-1] and "install PortName=COM34 PortName=COM24" in k[-1]
    assert "-WorkingDirectory 'C:\\Program Files (x86)\\com0com'" in k[-1]
    import pytest
    with pytest.raises(ValueError):
        C.lag_par_kommando("setupc.exe", "COM34; rm", "COM24")


def test_comdb_reserverte_namn_blir_unngatt():
    import com0com as C
    brukte = C.comdb_brukte(bytes([0b00000100, 0, 0, 0b10000000, 0b00000010]))   # COM3, COM32, COM34
    assert brukte == {"COM3", "COM32", "COM34"}
    assert C.ledig_par(["COM3"] + sorted(brukte)) == ("COM35", "COM25")
    assert C.comdb_brukte(bytes([0, 0, 0b10000000])) == {"COM24"}                  # bit 23 = COM24


def test_com0com_finn_par_i_registeret_utan_ports_klasse():
    """Første køyring 6.11: paret COM44 ↔ COM45 fanst, men var ikkje i portlista frå pyserial."""
    import com0com as C
    sc = {r"\Device\BthModem0": "COM4", r"\Device\com0com10": "COM44", r"\Device\com0com20": "COM45"}
    assert C.par_fra_serialcomm(sc) == {0: {"A": "COM44", "B": "COM45"}}
    st = C.status({"ut_seriell": [{"port": "COM44"}]}, portar=[("COM3", "Seriell USB-enhet", "USB")], setupc_tekst="",
                  windows=True, teneste=True, register=[C.par_fra_serialcomm(sc)])
    assert st["par"] == [{"n": 0, "geoscan": "COM44", "onevision": "COM45", "emubr": False}]
    assert st["forslag"] == {"geoscan": "COM44", "onevision": "COM45"} and not st["atvaringar"]


def test_casteradresse_blir_reinska(tmp_path, monkeypatch):
    import json as _json
    import innstillingar as INN
    monkeypatch.setattr(INN, "HER", tmp_path)
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text("{}")
    d = dict(INN.hent(cfgp, {}), mottakar="COM3", ntrip_pa=True, caster=" http://caster.eksempel.no:2102/TH ",
             mountpoint="", brukar="x", passord="y")
    INN.lagre(cfgp, d)
    lok = _json.loads((tmp_path / "ntrip_lokal.json").read_text())
    assert lok["caster"] == "caster.eksempel.no" and lok["port"] == 2102 and lok["mountpoint"] == "TH"


def test_live_posisjon_i_status():
    """Live-kartet på Status les korr.pos: mottakarposisjon, retta posisjon, fix og kurs."""
    k = G.Korrigerar(dict(G.STANDARD, logg=None))
    k.handle("$GPGGA,094016.70,6223.8710022,N,00634.9919464,E,4,20,0.60,14.594,M,45.01,M,01,2769*52")
    p = k.status["pos"]
    assert p["fix"] == 4 and abs(p["lat"] - 62.39785) < 1e-4 and abs(p["lon"] - 6.58320) < 1e-4
    assert {"lat_ut", "lon_ut", "kurs", "krenging", "stamp", "korrigert", "t"} <= set(p)


def test_oppdatering_ugyldig_nokkel_prover_utan(tmp_path, monkeypatch):
    """6.11: nøkkelen på PC-en var ugyldig, og sjekken sa «repoet er privat» sjølv om repoet var ope."""
    import io
    import json as _json
    import urllib.error
    import oppdater as O
    monkeypatch.setattr(O, "HER", tmp_path)
    (tmp_path / "oppdatering_lokal.json").write_text(_json.dumps({"token": "gammal"}))
    (tmp_path / "geoscan.py").write_text('VERSJON = "0.9.0"\n')
    sende = []

    def urlopen(req, timeout=0):
        auth = req.get_header("Authorization")
        sende.append(auth)
        if auth:
            raise urllib.error.HTTPError(req.full_url, 401, "Bad credentials", {}, io.BytesIO())
        return io.BytesIO(b'VERSJON = "0.9.2"\n')
    monkeypatch.setattr(O.urllib.request, "urlopen", urlopen)
    lok, rem, nyare = O.check()
    assert (lok, rem, nyare) == ("0.9.0", "0.9.2", True) and O.SISTE_FEIL[0] is None
    assert O.NOKKEL_UGYLDIG[0] is True and sende == ["Bearer gammal", None]


def test_r12i_stangspiss_med_sidearm_blir_ikkje_flytta():
    """Felttest Norman 7.11: R12i (tilt på) sender stangspissen. Med GPS 0,6 m til venstre vart punktet flytta
    0,6 m til venstre for køyreretninga ein gong for mykje (spor køyrde motsett veg låg ca. 1,2 m frå kvarandre)."""
    import math
    cfg = dict(G.STANDARD, logg=None, hoegd="mottakar", utgang="rett_antenne", mottakar_kompenserer=True,
               spakarm={"fram": 0.4, "hogre": -0.6, "opp": 1.8})
    k = G.Korrigerar(cfg)
    ut = None
    for i, lon in enumerate(("00634.0000000", "00634.0010000", "00634.0020000", "00634.0030000")):  # austover
        ut = k.handle(_gga(lon=lon, alt="148.200"), now=1.0 + i)[0]
    g = N.parse_gga(N.split(ut))
    assert abs(g["lat"] - N.coord_in("6223.4000000", "N")) < 1e-9          # ingen sideflytting
    assert abs(g["lon"] - N.coord_in("00634.0030000", "E")) < 1e-9
    assert abs(g["alt"] - 150.0) < 1e-6                                       # antenna = spiss + 1,8 m
    # Referansepunktet ligg 0,6 m til HØGRE for masta (sør når ein køyrer aust) og 0,4 m bak spissen
    cfg["utgang"] = "referansepunkt"
    k = G.Korrigerar(cfg)
    for i, lon in enumerate(("00634.0000000", "00634.0010000", "00634.0020000", "00634.0030000")):
        ut = k.handle(_gga(lon=lon, alt="148.200"), now=1.0 + i)[0]
    g = N.parse_gga(N.split(ut))
    dn = (g["lat"] - N.coord_in("6223.4000000", "N")) * 111320
    de = (g["lon"] - N.coord_in("00634.0030000", "E")) * 111320 * math.cos(math.radians(62.39))
    assert abs(dn + 0.6) < 0.02 and abs(de + 0.4) < 0.02


def test_mountpoint_liste_fraa_casteren(tmp_path, monkeypatch):
    """Norman 7.11: «på mountpoint må du leggje inn rullefelt som hentar mountpoint»."""
    import json as _json
    import socket
    import threading
    import urllib.request as _u
    import innstillingar as INN
    import webtenar as W
    import simuler as S
    for mod in (INN, W):
        monkeypatch.setattr(mod, "HER", tmp_path)
    s0 = socket.socket(); s0.bind(("127.0.0.1", 0)); cport = s0.getsockname()[1]; s0.close()
    stop = threading.Event()
    threading.Thread(target=S.FalskCaster("TH").serve, args=(cport, stop), daemon=True).start()
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text("{}")
    app = G.App(dict(G.STANDARD, inn=[], ut_seriell=[], tcp_port=None, status_port=0,
                     logg=str(tmp_path / "logg"), ntrip={"pa": False}), cfgp)
    srv = W.start(app, 0)
    try:
        import time as _time
        _time.sleep(0.3)
        r = _u.Request(f"http://127.0.0.1:{srv.server_address[1]}/api/kjeldetabell",
                       data=_json.dumps({"caster": f"http://127.0.0.1:{cport}/", "brukar": "", "passord": ""}).encode(),
                       headers={"Content-Type": "application/json"})
        d = _json.loads(_u.urlopen(r).read())
        assert d["ok"] and sorted(m["mountpoint"] for m in d["mounts"]) == ["SIM2", "TH"]   # nærmaste først når posisjonen er kjend
    finally:
        srv.shutdown(); stop.set()


def test_gngga_er_antenne_sjolv_om_mottakar_kompenserer_er_paa():
    """Felttest 7.11: R12i direkte på USB sende $GNGGA (antennefasesenteret, IMU ikkje i bruk). Geoscan trudde
    det var stangspissen og la til mastehøgda – høgda til OneVision vart 1,8 m for høg. Berre $INGGA er spissen."""
    cfg = dict(G.STANDARD, logg=None, hoegd="mottakar", utgang="rett_antenne", mottakar_kompenserer=True,
               spakarm={"fram": 0.4, "hogre": -0.6, "opp": 1.8})
    k = G.Korrigerar(cfg)
    out = k.handle(_gga(talker="GN", alt="150.000"), now=1.0)[0]
    g = N.parse_gga(N.split(out))
    assert abs(g["alt"] - 150.0) < 1e-6 and abs(g["lat"] - N.coord_in("6223.4000000", "N")) < 1e-9
    assert "antenneposisjon ($GNGGA)" in k.status["melding"] and not k.komp_aktiv
    out = k.handle(_gga(talker="IN", alt="148.200"), now=2.0)[0]          # $INGGA: spissen → antenne = +1,8 m
    assert abs(N.parse_gga(N.split(out))["alt"] - 150.0) < 1e-6 and k.komp_aktiv
    assert "stangspiss" in k.status["melding"]


def _nmea_bytes(talker="GN", n=10, hz=1.0, fix=4, ekstra=()):
    ut = []
    for i in range(n):
        t = 50000 + i / hz
        hh, mm, ss = int(t // 3600), int(t % 3600 // 60), t % 60
        ut.append(N.build([f"{talker}GGA", f"{hh:02d}{mm:02d}{ss:05.2f}", "6217.6758806", "N", "00638.5705991", "E",
                           str(fix), "14", "0.9", "67.958", "M", "45.210", "M", "1.0", "0000"]))
        ut.extend(ekstra)
    return ("\r\n".join(ut) + "\r\n").encode()


def test_finn_utstyr_tolkar_data():
    import finn_utstyr as FU
    a = FU.analyser(_nmea_bytes("GN", 10, 1.0))
    assert a["kva"] == "gnss" and a["talker"] == "GN" and a["hz"] == 1.0 and a["fix"] == 4 and a["sats"] == 14
    a = FU.analyser(_nmea_bytes("IN", 11, 10.0))
    assert a["talker"] == "IN" and a["hz"] == 10.0
    pashr = N.build(["PASHR", "120000.00", "90.0", "T", "5.00", "0.00", "", "", "", "", "2", "1"])
    a = FU.analyser(((pashr + "\r\n") * 5).encode())
    assert a["kva"] == "helling" and a["helling"]
    assert FU.analyser(b"\xd3\x00\x13" + bytes(30))["kva"] == "binaer"
    assert FU.analyser(b"")["kva"] == "stille"
    assert FU.analyser(b"$GNGGA,1,2*00\r\n")["kva"] == "ukjend"            # feil sjekksum


def test_finn_utstyr_skann_og_forslag():
    import finn_utstyr as FU

    class Port:
        def __init__(self, data): self.data = data
        def read(self, n):
            d, self.data = self.data[:n], self.data[n:]
            if not d:
                time.sleep(0.01)
            return d
        def close(self): pass

    def opne(port, baud):
        if port == "COM9":
            raise PermissionError("could not open port 'COM9': PermissionError(13, 'Access is denied.')")
        if port == "COM3":
            return Port(_nmea_bytes("GN", 6, 1.0))
        if port == "COM5":
            return Port(_nmea_bytes("IN", 20, 10.0))
        return Port(b"")
    import time
    portar = [{"port": p, "skildring": s} for p, s in
              (("COM3", "Seriell USB-enhet"), ("COM5", "Bluetooth"), ("COM9", "x"), ("COM11", "Bluetooth"))]
    res = FU.skann(portar, opne=opne, sekund=0.2, frist=5)
    assert res["COM9"]["tilstand"] == "oppteken" and res["COM11"]["kva"] == "stille"
    f, atv = FU.forslag(res, {"stotta": True, "installert": True, "par": [{"geoscan": "COM34", "onevision": "COM24"}],
                              "forslag": {"geoscan": "COM34", "onevision": "COM24"}},
                        {"spakarm": {"opp": 1.8, "hogre": -0.6}},
                        {"fil": "Stream C.xml", "xyz": "0.13;0.42;1,9", "x": 0.13, "y": 0.42, "z": 1.9, "komma_feil": True})
    assert f["mottakar"] == "COM5" and f["onevision"] == "COM34"               # IN (IMU) og 10 Hz føre GN 1 Hz
    assert any("fleire portar" in a for a in atv) and any("komma" in a for a in atv)
    assert any("Mastehøgda i OneVision er 1.9" in a for a in atv) and any("Sideforskyvinga" in a for a in atv)
    f, atv = FU.forslag({"COM3": res["COM3"]})
    assert f["mottakar"] == "COM3" and any("antenneposisjon" in a for a in atv) and any("5 Hz" in a for a in atv)


def test_les_onevision_stream_c(tmp_path):
    import finn_utstyr as FU
    f = tmp_path / "Stream C.xml"
    f.write_text('<RadarConfiguration><Radar><GPSs Count="1"><GPS Type="0" xyz="0.13;0.42;1,6"/></GPSs></Radar></RadarConfiguration>',
                 encoding="utf-8")
    ov = FU.les_onevision([tmp_path / "finst_ikkje.xml", f])
    assert ov["komma_feil"] and ov["z"] == 1.6 and ov["y"] == 0.42
    assert FU.les_onevision([tmp_path / "x.xml"]) is None


def test_finn_utstyr_api(tmp_path, monkeypatch):
    import json as _json
    import urllib.request as _u
    import finn_utstyr as FU
    import innstillingar as INN
    import innsending as IS
    import webtenar as W
    for mod in (INN, W, IS):
        monkeypatch.setattr(mod, "HER", tmp_path)
    monkeypatch.setattr(INN, "porter", lambda: [{"port": "COM3", "skildring": "Seriell USB-enhet"}])
    monkeypatch.setattr(FU, "skann", lambda portar, hopp_over=(), **k: {"COM3": dict(
        FU.analyser(_nmea_bytes("GN", 6, 1.0)), port="COM3", baud=115200, tilstand="open", skildring="USB")})
    monkeypatch.setattr(FU, "les_onevision", lambda stiar=None: None)
    cfgp = tmp_path / "geoscan_config.json"
    cfgp.write_text(_json.dumps({"inn": [{"port": "COM23"}], "spakarm": {"opp": 1.8}}))
    app = G.App(dict(G.STANDARD, inn=[], ut_seriell=[], tcp_port=None, status_port=0,
                     logg=str(tmp_path / "logg"), ntrip={"pa": False}), cfgp)
    srv = W.start(app, 0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def post(u, d):
        r = _u.Request(base + u, data=_json.dumps(d).encode(), headers={"Content-Type": "application/json"})
        return _json.loads(_u.urlopen(r).read())
    try:
        r = post("/api/finn_utstyr", {})
        assert r["forslag"]["mottakar"] == "COM3" and r["forslag"]["talker"] == "GN"
        assert r["noverande"]["mottakar"] == "COM23" and any("antenneposisjon" in a for a in r["atvaringar"])
        # Resultatet blir med i pakka av seg sjølv: fil i loggmappa, kommentar i sjekkpunkt r0, SKANNING.txt
        filer = list(app.loggdir.glob("finn_utstyr_*.json"))
        assert len(filer) == 1 and "Mottakar: COM3 ($GNGGA, antenne, 1.0 Hz" in filer[0].read_text(encoding="utf-8")
        assert IS.sjekk_les()["punkt"]["r0"]["kommentar"].startswith("[auto] Mottakar: COM3")
        import zipfile
        zp = IS.lag_pakke(cfgp, app.loggdir, G.VERSJON)
        with zipfile.ZipFile(zp) as z:
            assert "Mottakar: COM3" in z.read("SKANNING.txt").decode("utf-8")
            assert any(n.startswith("logg/finn_utstyr_") for n in z.namelist())
        post("/api/bruk_oppsett", dict(r["forslag"], onevision="34"))
        c = _json.loads(cfgp.read_text())
        assert c["inn"] == [{"port": "COM3", "baud": 115200}] and c["mottakar_kompenserer"] is False
        assert c["ut_seriell"][0]["port"] == "COM34" and c["spakarm"]["opp"] == 1.8 and app.oppd["omstart"] is False
    finally:
        srv.shutdown()


def test_onevision_filer_nyaste_forst(tmp_path):
    """Målefilene frå OneVision blir funne i undermapper og sorterte nyaste først (dato og nummer i namnet)."""
    import onevision_filer as OVF
    rot = tmp_path / "Projects"
    for namn in ("Survey_2026.11.07_001", "Survey_2026.11.08_002", "Survey_2026.11.08_001"):
        (rot / namn).mkdir(parents=True)
        (rot / namn / f"{namn}.svy").write_text("<Survey></Survey>")
    (rot / "anna.txt").write_text("x")
    r = OVF.finn({"onevision_mappe": str(rot)})
    assert [f["namn"] for f in r["filer"][:3]] == ["Survey_2026.11.08_002.svy", "Survey_2026.11.08_001.svy",
                                                  "Survey_2026.11.07_001.svy"]
    assert r["filer"][0]["dato"] == "2026-11-08" and r["filer"][0]["nr"] == 2
    assert OVF.er_funnen({"onevision_mappe": str(rot)}, r["filer"][0]["sti"])
    assert not OVF.er_funnen({"onevision_mappe": str(rot)}, str(rot / "anna.txt"))


def test_onevision_filer_gps_xyz_per_maaling(tmp_path):
    """Vogneoppsettet per måling (Survey_…/Data/Stream C.xml) blir lese saman med .svy."""
    import onevision_filer as OVF
    m = tmp_path / "Projects" / "Survey_2026.11.08_001"
    (m / "Data").mkdir(parents=True)
    (m / "Survey_2026.11.08_001.svy").write_text("<Survey></Survey>")
    (m / "Data" / "Stream C.xml").write_text('<Cfg><GPS Name="g" xyz="0.13;0.42;1.9"/></Cfg>')
    f = OVF.finn({"onevision_mappe": str(tmp_path / "Projects")})["filer"][0]
    assert f["gps_xyz"] == [0.13, 0.42, 1.9]


def test_resultat_utan_helling(tmp_path):
    """Utan hellingsdata (eller med helling slått av) blir objekta viste urørte, med merknad – ikkje feil."""
    import json as _json
    import resultat as RES
    gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:32632"}},
          "features": [{"type": "Feature", "properties": {"id": 1},
                        "geometry": {"type": "LineString", "coordinates": [[379000.0, 6920000.0, 0.8], [379002.0, 6920001.0, 0.9]]}}]}
    f = tmp_path / "obj.geojson"
    f.write_text(_json.dumps(gj))
    for helling in (True, False):
        r = RES.rett_eksport(f, [], tmp_path / "ut", helling=helling)
        assert r["merknad"] and r["helling"] is False and r["sone"] == 32
        assert r["tabell"][0]["djupn_etter"]["snitt"] == 0.85
