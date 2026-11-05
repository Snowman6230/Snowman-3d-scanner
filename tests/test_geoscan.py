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
        assert abs(hb - (150.0 + 44.775 - GEOID.n(*spor[0][:2]) - 1.4)) < 0.05      # simulert antenne − mast
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
