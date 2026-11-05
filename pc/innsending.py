# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""«Send inn»: svar på dei opne spørsmåla, filer frå operatøren (eksportar, oppsettfiler, bilete), og éi pakke
(zip) med alt utviklaren treng. Pakka inneheld aldri passord eller brukarnamn.

Alt blir lagra i pc/innsendt/ (svar.json og filer/). Pakkane blir lagde i pc/pakkar/.
Spørsmåla er dei same som i docs/OPNE-SPORSMAL.md.
"""
import json
import platform
import re
import sys
import time
import zipfile
from pathlib import Path

HER = Path(__file__).resolve().parent
MAKS_FIL = 500 * 1024 * 1024

SPORSMAL = [
    {"id": "mast", "tekst": "Mastehøgd: frå merket for antennehøgd ned til underkanten av radaren (m)", "type": "tal",
     "hjelp": "Mål med tommestokk. Forventa ca. 1,40 eller 1,50 m."},
    {"id": "fram", "tekst": "Kor langt framfor masta ligg midten av antennerekkja (m)? Negativt om han ligg bak.",
     "type": "tal", "hjelp": "Mål langs vogna frå masta til midten av radaren."},
    {"id": "sida", "tekst": "Står masta midt på vogna sidelengs? Elles: kor mykje til høgre (m, negativt = venstre)",
     "type": "tal", "hjelp": "0 om ho står midt på."},
    {"id": "onevision_oppsett", "tekst": "Kva antenneoppsett står i OneVision no (høgd, forskyving fram/side)?",
     "type": "tekst", "hjelp": "Skriv av tala, eller legg ved eit skjermbilete under."},
    {"id": "imu", "tekst": "Blir det sett på ein ekstra IMU (hellingsmålar) på ramma? Kva modell?", "type": "tekst",
     "hjelp": "Utan han blir masta retta, men ikkje djupna."},
    {"id": "eksport", "tekst": "Kva eksportformat brukar du frå GRED HD / OneVision (GeoJSON, DXF, SHP, CSV)? Vel du djupn eller høgd?",
     "type": "tekst", "hjelp": "Legg ved ei ekte eksportfil under."},
    {"id": "kurs", "tekst": "Brukar OneVision kurs (heading) frå GNSS til å leggje skannebeltet, eller berre sporet?",
     "type": "tekst", "hjelp": "Står gjerne i GPS-oppsettet i OneVision."},
    {"id": "r12i_imu", "tekst": "Held R12i tilt-kompensasjonen seg når vogna blir trekt (støyt, snuing)?", "type": "tekst",
     "hjelp": "Sjå om posisjonen hoppar etter fortauskantar."},
    {"id": "rtk", "tekst": "Fekk du RTK FIX ute? Gjekk RTCM over USB, eller måtte du bruke Bluetooth port 2?", "type": "tekst",
     "hjelp": "Statussida viser fix og NTRIP."},
    {"id": "djupnesnitt", "tekst": "Kan GRED HD / OneVision eksportere djupnesnitt (time/depth slices) som bilete (GeoTIFF/KMZ) eller rådata?",
     "type": "tekst", "hjelp": "Då kan Snowman Geoscan vise radarbiletet cm for cm og rette det. Legg gjerne ved ei eksempelfil."},
    {"id": "anna", "tekst": "Anna du vil fortelje (feil, ønske, observasjonar)", "type": "langtekst", "hjelp": ""},
]

# Testsjekklista (same steg som docs/TESTPLAN.md). Status per punkt: "" (ikkje testa), ok, delvis, feil, irrelevant.
SJEKKLISTE = [
    {"steg": "Steg 1 – Demo utan utstyr", "punkt": [
        {"id": "d1", "tekst": "Programmet startar med oppstartbiletet, og nettlesaren opnar seg med Snowman Geoscan"},
        {"id": "d2", "tekst": "Status viser DEMO, RTK FIX, helling ±6° som skiftar ved snuing, og NTRIP «tilkopla»"},
        {"id": "d3", "tekst": "Resultat: sporet blir vist, og eksempelfila blir retta (kart, tabell, profil)"},
        {"id": "d4", "tekst": "Grav nedover, tverrsnitt, koordinatar og eksport (utsetting, CSV, GeoJSON, DXF) fungerer"},
        {"id": "d5", "tekst": "Rapporten kan skrivast ut eller lagrast som PDF"}]},
    {"steg": "Steg 2 – R12i innandørs", "punkt": [
        {"id": "r1", "tekst": "Trimble Access er lukka, og mottakarporten (t.d. COM23) står som «open»"},
        {"id": "r2", "tekst": "Fix og satellittar blir viste (DGPS er greitt innandørs)"},
        {"id": "r3", "tekst": "Posisjonen er fornuftig – rett stad på kartet"}]},
    {"steg": "Steg 3 – NTRIP og RTK ute", "punkt": [
        {"id": "n1", "tekst": "NTRIP står som «tilkopla», og kB-teljaren går"},
        {"id": "n2", "tekst": "RTK FIX ute – skriv om RTCM gjekk over USB eller Bluetooth port 2"},
        {"id": "n3", "tekst": "Kor lang tid tok det til RTK FIX? (minutt)"}]},
    {"steg": "Steg 4 – Felt med vogna", "punkt": [
        {"id": "f1", "tekst": "Statisk: posisjonen ligg i ro innan 1–2 cm når vogna blir vippa 5–10° til sidene"},
        {"id": "f2", "tekst": "OneVision viser «GNSS connection OK» med RTK gjennom com0com (COM24)"},
        {"id": "f3", "tekst": "R12i held tilt-kompensasjonen når vogna blir trekt (ingen hopp etter fortauskantar)"},
        {"id": "f4", "tekst": "Djupn: røyr skanna begge vegar i sidebakke fell saman etter retting (krev ekstra IMU)"},
        {"id": "f5", "tekst": "Ei ekte eksportfil frå GRED HD/OneVision blir lesen og retta under Resultat"}]},
]
STATUS = {"": "ikkje testa", "ok": "godkjent", "delvis": "delvis", "feil": "ikkje godkjent", "irrelevant": "ikkje relevant"}


def sjekk_les():
    try:
        return json.loads((_dir() / "sjekkliste.json").read_text(encoding="utf-8"))
    except Exception:
        return {"punkt": {}, "lagra": None}


def sjekk_lagre(data):
    cur = sjekk_les()
    ids = {p["id"] for st in SJEKKLISTE for p in st["punkt"]}
    for k, v in (data.get("punkt") or {}).items():
        if k in ids and isinstance(v, dict):
            s = str(v.get("status") or "")
            cur["punkt"][k] = {"status": s if s in STATUS else "", "kommentar": str(v.get("kommentar") or "")[:2000],
                               "tid": time.strftime("%Y-%m-%d %H:%M")}
    cur["lagra"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (_dir() / "sjekkliste.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return cur


def sjekk_tekst():
    cur, o = sjekk_les(), []
    n = {k: 0 for k in STATUS}
    for st in SJEKKLISTE:
        o += ["", st["steg"], "-" * len(st["steg"])]
        for p in st["punkt"]:
            v = cur["punkt"].get(p["id"], {})
            s = v.get("status", "")
            n[s] = n.get(s, 0) + 1
            o.append(f"[{ {'ok': 'OK', 'delvis': '~', 'feil': 'X', 'irrelevant': '-'}.get(s, ' ') }] {p['tekst']}  –  {STATUS.get(s, s)}"
                     + (f" ({v.get('tid')})" if v.get("tid") and s else ""))
            if v.get("kommentar"):
                o.append(f"      Kommentar: {v['kommentar']}")
    total = sum(n.values())
    return [f"Testsjekkliste: {n['ok']} godkjent, {n['delvis']} delvis, {n['feil']} ikkje godkjent, "
            f"{n['irrelevant']} ikkje relevant, {n['']} ikkje testa (av {total})"] + o


# ---------- meldingar frå utviklaren (pc/meldingar.json, kjem med oppdateringa) ----------
def meldingar():
    """Meldingane med «lest» frå denne PC-en, og svara på sjekklista samla per punkt (nyaste vinn)."""
    try:
        m = json.loads((HER / "meldingar.json").read_text(encoding="utf-8")).get("meldingar") or []
    except Exception:
        m = []
    try:
        lest = set(json.loads((_dir() / "lest.json").read_text(encoding="utf-8")))
    except Exception:
        lest = set()
    svar = {}
    for x in reversed(m):                 # eldste først, så den nyaste står att
        for pid, v in (x.get("sjekk") or {}).items():
            v = v if isinstance(v, dict) else {"tekst": str(v)}
            svar[pid] = {"tekst": v.get("tekst", ""), "prov_att": bool(v.get("prov_att")), "versjon": x.get("versjon"),
                         "dato": x.get("dato")}
    return {"meldingar": [dict(x, lest=x.get("id") in lest) for x in m], "sjekk_svar": svar}


def melding_lest(mid):
    p = _dir() / "lest.json"
    try:
        lest = set(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        lest = set()
    lest.add(str(mid)[:100])
    p.write_text(json.dumps(sorted(lest)), encoding="utf-8")


FILTYPAR = {"eksport": "Eksport frå GRED HD / OneVision (GeoJSON, CSV, DXF, SHP-zip)",
            "oppsett": "Oppsettfiler (t.d. SCANNH.xml frå R12i, OneVision-oppsett)",
            "bilete": "Bilete (vogna, masta, skjermbilete)", "anna": "Anna"}


def _dir():
    d = HER / "innsendt"
    (d / "filer").mkdir(parents=True, exist_ok=True)
    return d


def safe_name(name):
    name = Path(str(name)).name
    name = re.sub(r"[^A-Za-z0-9æøåÆØÅ._ -]", "_", name).strip(" .") or "fil"
    return name[:120]


def svar_les():
    p = _dir() / "svar.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"svar": {}, "lagra": None, "namn": ""}


def svar_lagre(data):
    cur = svar_les()
    ids = {s["id"] for s in SPORSMAL}
    for k, v in (data.get("svar") or {}).items():
        if k in ids:
            cur["svar"][k] = str(v)[:5000]
    if data.get("namn") is not None:
        cur["namn"] = str(data["namn"])[:100]
    cur["lagra"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (_dir() / "svar.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return cur


def fil_lagre(name, data, kind="anna"):
    """Lagrar ei opplasta fil i innsendt/filer/ med tid og type framfor namnet."""
    if len(data) > MAKS_FIL:
        raise ValueError(f"fila er for stor (maks {MAKS_FIL // 1024 // 1024} MB)")
    kind = kind if kind in FILTYPAR else "anna"
    fn = f"{time.strftime('%Y%m%d_%H%M%S')}_{kind}_{safe_name(name)}"
    p = _dir() / "filer" / fn
    p.write_bytes(data)
    return fn


def filer():
    out = []
    for p in sorted((_dir() / "filer").iterdir(), reverse=True):
        if p.is_file():
            parts = p.name.split("_", 3)
            kind = parts[2] if len(parts) > 3 and parts[2] in FILTYPAR else "anna"
            out.append({"fil": p.name, "namn": parts[3] if len(parts) > 3 else p.name, "type": kind,
                        "kb": round(p.stat().st_size / 1024), "tid": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))})
    return out


def fil_slett(fn):
    p = _dir() / "filer" / safe_name(fn)
    if p.is_file():
        p.unlink()
        return True
    return False


def _redact(obj):
    """Fjern alt som liknar innlogging før det kjem i pakka."""
    if isinstance(obj, dict):
        return {k: ("<fjerna>" if re.search(r"pass|brukar|user|token|nokkel|nøkkel", k, re.I) and v else _redact(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def lag_pakke(cfg_path, loggdir, versjon, med_raa=True, dagar=None, status=None):
    """Zip til utviklaren: svar, innsende filer, loggar, oppsett (utan innlogging) og systeminfo.
    dagar: berre loggar frå dei siste N dagane. Returnerer stien til zip-fila."""
    d = HER / "pakkar"
    d.mkdir(exist_ok=True)
    zp = d / f"SnowmanGeoscan_pakke_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    grense = time.time() - dagar * 86400 if dagar else 0
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        sv = svar_les()
        import opphav
        z.comment = opphav.generator(versjon).encode("utf-8")[:60000]
        z.writestr("svar.json", json.dumps(sv, ensure_ascii=False, indent=1))
        tekst = [f"{opphav.NAMN} {versjon} – pakke til utviklar", opphav.PRODUSENT, opphav.SIGNATUR,
                 f"Send til: {opphav.KONTAKT_EPOST}",
                 f"Laga {time.strftime('%Y-%m-%d %H:%M')}"
                 + (f" av {sv.get('namn')}" if sv.get("namn") else ""), ""]
        for s in SPORSMAL:
            tekst += [s["tekst"], "  " + (sv["svar"].get(s["id"]) or "(ikkje svara)"), ""]
        z.writestr("SVAR.txt", "\n".join(tekst))
        z.writestr("sjekkliste.json", json.dumps(sjekk_les(), ensure_ascii=False, indent=1))
        z.writestr("SJEKKLISTE.txt", "\n".join([f"{opphav.NAMN} {versjon} – testsjekkliste", opphav.PRODUSENT,
                                                 time.strftime("%Y-%m-%d %H:%M"), ""] + sjekk_tekst()))
        for p in (_dir() / "filer").iterdir():
            if p.is_file():
                z.write(p, f"filer/{p.name}")
        ld = Path(loggdir)
        if ld.exists():
            for p in sorted(ld.iterdir()):
                if not p.is_file() or p.stat().st_mtime < grense:
                    continue
                if p.suffix == ".nmea" and not med_raa:
                    continue
                z.write(p, f"logg/{p.name}")
        for name in ("geoscan_config.json", "ntrip_lokal.json"):
            p = Path(cfg_path) if name == "geoscan_config.json" else HER / name
            if p.exists():
                try:
                    z.writestr(f"oppsett/{name}", json.dumps(_redact(json.loads(p.read_text(encoding="utf-8"))),
                                                             ensure_ascii=False, indent=1))
                except Exception:
                    pass
        info = {"versjon": versjon, "python": sys.version, "system": platform.platform(), "maskin": platform.node()}
        if status:
            info["status"] = _redact(status)
        z.writestr("system.json", json.dumps(info, ensure_ascii=False, indent=1, default=str))
    return zp
