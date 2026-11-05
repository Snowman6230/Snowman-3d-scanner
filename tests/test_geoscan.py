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
