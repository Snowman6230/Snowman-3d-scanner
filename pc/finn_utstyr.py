# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Automatisk oppstartssjekk: finn mottakaren, hellingsmålaren og porten til OneVision utan å vite portnummer.

Norman 7.11.2026: «Ein burde ha ein oppstartsekvens som tolkar kva som blir sendt, kva COM-port, GGA-type osb.,
og som skannar portane. Oppsettet tek enormt med tid, og vi kan bruke forskjellige roverar.»

Kva som skjer:
  1. Alle COM-portar blir lista (pyserial), og com0com-para blir funne (com0com.py).
  2. Kvar ledig port blir opna og lytta på i nokre sekund, på vanlege baudrater (USB-portar bryr seg ikkje om
     baud, så første forsøk held). Portar som Geoscan sjølv har opne, blir ikkje opna – der blir det brukt det
     Geoscan faktisk tek imot (live-statistikk).
  3. Dataa blir tolka: NMEA med gyldig sjekksum, talker-ID ($INGGA = IMU-retta stangspiss, $GNGGA/$GPGGA =
     antenne), rate i Hz, fix, satellittar, hellingssetningar ($PTNL,AVR, $PASHR, $xxHPR) og RTCM/UBX (binært).
  4. Forslag: mottakar = porten med GGA (IN føre GN, høgast rate), hellingsmålar = port med berre helling,
     OneVision = Geoscan-enden av eit com0com-par. Åtvaringar for låg rate, antenne utan IMU osb.
  5. OneVision sitt GPS-oppsett (Stream C.xml) blir lese og samanlikna med mastehøgd og forskyving.
Ingenting blir skrive til nokon port, og ingen innstillingar blir endra før brukaren trykkjer «Bruk dette».
"""
import os
import re
import threading
import time
from collections import Counter
from pathlib import Path

BAUDAR = (115200, 9600, 38400, 57600, 19200, 4800)
HELLING = ("PTNL,AVR", "PASHR", "HPR", "PSAT,HPR")


def _sjekksum_ok(line):
    m = re.match(r"^\$([^*]+)\*([0-9A-Fa-f]{2})\s*$", line)
    if not m:
        return False
    c = 0
    for ch in m.group(1):
        c ^= ord(ch)
    return c == int(m.group(2), 16)


def _sek(t):
    try:
        return int(t[:2]) * 3600 + int(t[2:4]) * 60 + float(t[4:])
    except (ValueError, IndexError):
        return None


def analyser(data, sekund=None):
    """Tolkar rå bytes frå ein port. Returnerer kva det er og detaljar."""
    rtcm = data.count(b"\xd3\x00")
    ubx = data.count(b"\xb5\x62")
    linjer = [l.strip() for l in data.decode("ascii", "replace").replace("\r", "\n").split("\n")]
    nmea = [l[l.rfind("$"):] for l in linjer if "$" in l]
    gyldige = [l for l in nmea if _sjekksum_ok(l)]
    typar, talkarar, gga = Counter(), Counter(), []
    helling = False
    for l in gyldige:
        f = l[1:].split("*")[0].split(",")
        hode = f[0]
        if hode.startswith("P"):
            typ = hode if hode not in ("PTNL", "PSAT") else f"{hode},{f[1] if len(f) > 1 else ''}"
        else:
            typ = hode[2:]
            talkarar[hode[:2]] += 1 if typ == "GGA" else 0
        typar[typ] += 1
        if any(h in l for h in HELLING):
            helling = True
        if hode.endswith("GGA") and len(f) > 7:
            gga.append({"talker": hode[:2], "t": _sek(f[1]), "fix": int(f[6] or 0), "sats": int(f[7] or 0)})
    hz = None
    tider = [g["t"] for g in gga if g["t"] is not None]
    if len(tider) >= 2 and tider[-1] > tider[0]:
        hz = round((len(tider) - 1) / (tider[-1] - tider[0]), 1)
    elif gga and sekund:
        hz = round(len(gga) / sekund, 1)
    talker = talkarar.most_common(1)[0][0] if talkarar else None
    if gga:
        kva = "gnss"
    elif helling:
        kva = "helling"
    elif rtcm or ubx:
        kva = "binaer"
    elif data.strip():
        kva = "ukjend"
    else:
        kva = "stille"
    return {"kva": kva, "talker": talker, "hz": hz, "fix": gga[-1]["fix"] if gga else None,
            "sats": gga[-1]["sats"] if gga else None, "typar": dict(typar.most_common(8)), "helling": helling,
            "rtcm": rtcm, "ubx": ubx, "nmea": len(gyldige), "feil_sjekksum": len(nmea) - len(gyldige),
            "byte": len(data)}


def _opne(port, baud):
    import serial
    return serial.Serial(port, baud, timeout=0.3)


def skann_port(port, sekund=2.5, opne=None):
    """Prøver vanlege baudrater til det kjem gyldig NMEA. Returnerer analysen + port, baud og tilstand."""
    opne = opne or _opne
    beste = None
    for i, baud in enumerate(BAUDAR):
        try:
            p = opne(port, baud)
        except Exception as e:
            tekst = str(e)
            oppteken = isinstance(e, PermissionError) or "Access is denied" in tekst or "Tilgang nekta" in tekst \
                or "PermissionError" in tekst or "Ingen tilgang" in tekst
            return {"port": port, "tilstand": "oppteken" if oppteken else "feil", "melding": tekst[:160], "kva": None}
        try:
            data, slutt = b"", time.time() + (sekund if i == 0 else sekund * 0.6)
            while time.time() < slutt and len(data) < 200_000:
                data += p.read(4096) or b""
        finally:
            try:
                p.close()
            except Exception:
                pass
        a = analyser(data, sekund)
        a.update(port=port, baud=baud, tilstand="open")
        if a["nmea"]:
            return a
        if beste is None:
            beste = a
        if not data:              # ingenting i det heile: baud speler inga rolle (stille eller USB utan data)
            return a
    return beste


def skann(portar, hopp_over=(), frist=12.0, opne=None, sekund=2.5):
    """Skannar portane parallelt (Bluetooth-portar kan bruke lang tid på å opne). portar: [{"port","skildring"}]."""
    res, traadar = {}, []
    for p in portar:
        if p["port"] in hopp_over:
            continue

        def jobb(pp=p):
            r = skann_port(pp["port"], sekund, opne)
            r["skildring"] = pp.get("skildring", "")
            res[pp["port"]] = r
        t = threading.Thread(target=jobb, daemon=True)
        t.start()
        traadar.append((p, t))
    slutt = time.time() + frist
    for p, t in traadar:
        t.join(max(0.0, slutt - time.time()))
    for p, t in traadar:
        if p["port"] not in res:
            res[p["port"]] = {"port": p["port"], "skildring": p.get("skildring", ""), "tilstand": "svarar ikkje",
                              "melding": "porten opna seg ikkje i tide (Bluetooth-eining av eller utanfor rekkjevidd?)",
                              "kva": None}
    return res


def les_onevision(stiar=None):
    """GPS-oppsettet i OneVision (Stream C.xml ved OneVision.exe). (fil, x, y, z, komma_feil) eller None."""
    if stiar is None:
        stiar = []
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                     r"C:\Program Files (x86)", r"C:\Program Files"):
            if base:
                for under in (r"IDSGeoRadar\OneVision\config", r"IDSGeoRadar\OneVision"):
                    stiar.append(Path(base) / under / "Stream C.xml")
    for f in stiar:
        try:
            t = Path(f).read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        m = re.search(r'<GPS\b[^>]*\bxyz="([^"]*)"', t)
        if not m:
            continue
        deler = m.group(1).split(";")
        komma = any("," in d for d in deler)
        try:
            x, y, z = (float(d.replace(",", ".")) for d in deler[:3])
        except ValueError:
            return {"fil": str(f), "xyz": m.group(1), "feil": "kunne ikkje tolke xyz"}
        return {"fil": str(f), "xyz": m.group(1), "x": x, "y": y, "z": z, "komma_feil": komma}
    return None


def forslag(skanna, c0c=None, cfg=None, ov=None):
    """Kva oppsett som bør brukast, og åtvaringar. skanna: {port: analyse}."""
    cfg = cfg or {}
    gnss = [r for r in skanna.values() if r.get("kva") == "gnss"]
    gnss.sort(key=lambda r: (r.get("talker") != "IN", -(r.get("hz") or 0), -(r.get("fix") or 0)))
    hell = [r for r in skanna.values() if r.get("kva") == "helling" and (not gnss or r["port"] != gnss[0]["port"])]
    f = {"mottakar": gnss[0]["port"] if gnss else None, "mottakar_baud": gnss[0].get("baud") if gnss else None,
         "imu": hell[0]["port"] if hell else None, "imu_baud": hell[0].get("baud") if hell else None,
         "onevision": (c0c or {}).get("forslag", {}).get("geoscan") if c0c and c0c.get("forslag") else None}
    atv = []
    if not gnss:
        opptekne = [r["port"] for r in skanna.values() if r.get("tilstand") == "oppteken"]
        atv.append("Fann ingen GNSS-mottakar." + (f" Desse portane er opptekne av eit anna program (Trimble Access, "
                   f"NMEA-splitter?): {', '.join(opptekne)}." if opptekne else " Er mottakaren slått på og kopla til?"))
    else:
        g = gnss[0]
        if g.get("talker") != "IN":
            atv.append(f"Mottakaren sender ${g.get('talker') or '??'}GGA (antenneposisjon). Masta blir ikkje retta for "
                       "helling av mottakaren. Slå på IMU i R12i ($INGGA), eller bruk ekstra hellingsmålar.")
        if g.get("hz") is not None and g["hz"] < 4.5:
            atv.append(f"Mottakaren sender {g['hz']:g} posisjon(ar) i sekundet. Set GGA til 5 Hz eller meir på porten "
                       "i mottakaren – då blir spora jamnare.")
        if g.get("fix") in (0, None):
            atv.append("Mottakaren har ingen posisjon enno (fix 0). Gå ut under open himmel.")
        if len(gnss) > 1:
            atv.append("Fann fleire portar med GNSS: " + ", ".join(r["port"] for r in gnss) + ". Den beste er valt.")
    if c0c is not None and c0c.get("stotta"):
        if not c0c.get("installert"):
            atv.append("com0com er ikkje installert – OneVision kan ikkje få posisjon frå Geoscan.")
        elif not c0c.get("par"):
            atv.append("com0com er installert, men utan portpar.")
    if ov:
        mast = float(((cfg.get("spakarm") or {}).get("opp")) or 0)
        side = abs(float(((cfg.get("spakarm") or {}).get("hogre")) or 0))
        if ov.get("komma_feil"):
            atv.append(f"OneVision ({Path(ov['fil']).name}): GPS xyz «{ov['xyz']}» har komma. Bruk punktum.")
        if "z" in ov and mast and abs(ov["z"] - mast) > 0.02:
            atv.append(f"Mastehøgda i OneVision er {ov['z']:g} m, i Geoscan {mast:g} m. Bruk same målte tal begge "
                       "stader (og som stanghøgd i mottakaren).")
        if "y" in ov and side and abs(abs(ov["y"]) - side) > 0.02:
            atv.append(f"Sideforskyvinga i OneVision er {abs(ov['y']):g} m, i Geoscan {side:g} m.")
    return f, atv


def samandrag(res):
    """Kort tekst om ei skanning (til sjekklista og pakka), så operatøren slepp skjermbilete."""
    f = res.get("forslag") or {}
    port = {r["port"]: r for r in res.get("portar") or []}
    g = port.get(f.get("mottakar")) or {}
    linjer = []
    if g:
        linjer.append(f"Mottakar: {g['port']} (${g.get('talker') or '??'}GGA, "
                      f"{'stangspiss/IMU' if g.get('talker') == 'IN' else 'antenne'}, {g.get('hz')} Hz, "
                      f"fix {g.get('fix')}, {g.get('sats')} sat, {g.get('baud')} baud, {g.get('tilstand')})")
    else:
        linjer.append("Mottakar: ikkje funnen")
    if f.get("imu"):
        linjer.append(f"Hellingsmålar: {f['imu']}")
    c0c = res.get("com0com") or {}
    if c0c.get("forslag"):
        linjer.append(f"OneVision: Geoscan → {c0c['forslag']['geoscan']}, OneVision les {c0c['forslag']['onevision']}")
    ov = res.get("onevision")
    linjer.append(f"Stream C.xml: GPS xyz «{ov['xyz']}»" if ov else "Stream C.xml: ikkje funnen")
    andre = [f"{r['port']}={r.get('kva') or r.get('tilstand')}" for r in res.get("portar") or [] if r["port"] != g.get("port")]
    if andre:
        linjer.append("Andre portar: " + ", ".join(andre))
    for a in res.get("atvaringar") or []:
        linjer.append("Åtvaring: " + a)
    return linjer
