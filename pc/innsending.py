# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
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
    {"id": "anna", "tekst": "Anna du vil fortelje (feil, ønske, observasjonar)", "type": "langtekst", "hjelp": ""},
]

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
        z.writestr("svar.json", json.dumps(sv, ensure_ascii=False, indent=1))
        tekst = [f"Snowman Geoscan {versjon} – pakke til utviklar", f"Laga {time.strftime('%Y-%m-%d %H:%M')}"
                 + (f" av {sv.get('namn')}" if sv.get("namn") else ""), ""]
        for s in SPORSMAL:
            tekst += [s["tekst"], "  " + (sv["svar"].get(s["id"]) or "(ikkje svara)"), ""]
        z.writestr("SVAR.txt", "\n".join(tekst))
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
