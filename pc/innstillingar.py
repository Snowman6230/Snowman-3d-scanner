# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Innstillingar frå nettlesaren: les og skriv geoscan_config.json og ntrip_lokal.json (innlogging).
Passordet blir aldri sendt til nettlesaren – berre om det finst. Tomt passordfelt = behald det gamle."""
import json
from pathlib import Path

HER = Path(__file__).resolve().parent


def porter():
    """COM-portane på PC-en (Windows) eller /dev/tty* (Linux), med skildring."""
    try:
        from serial.tools import list_ports
        return [{"port": p.device, "skildring": p.description or ""} for p in sorted(list_ports.comports())]
    except Exception:
        return []


def _read(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def hent(cfg_path, cfg):
    """Det innstillingssida viser."""
    n = dict(cfg.get("ntrip") or {})
    lok = {} if cfg.get("demo") else _read(HER / "ntrip_lokal.json")
    n.update(lok)
    inn = cfg.get("inn") or []
    s = cfg.get("spakarm") or {}
    return {
        "mottakar": inn[0]["port"] if inn else "",
        "mottakar_baud": inn[0].get("baud", 115200) if inn else 115200,
        "imu": inn[1]["port"] if len(inn) > 1 else "",
        "imu_baud": inn[1].get("baud", 115200) if len(inn) > 1 else 115200,
        "onevision": (cfg.get("ut_seriell") or [{}])[0].get("port", "") if cfg.get("ut_seriell") else "",
        "tcp_port": cfg.get("tcp_port", 5000),
        "mast": s.get("opp", 1.4), "fram": s.get("fram", 0.0), "hogre": s.get("hogre", 0.0),
        "mottakar_kompenserer": bool(cfg.get("mottakar_kompenserer")),
        "utgang": cfg.get("utgang", "rett_antenne"),
        "djupn_sanntid": cfg.get("djupn_sanntid", 0.0),
        "radar_djupn": cfg.get("radar_djupn", 2.5),
        "sone": str(cfg.get("sone", "32")),
        "opptak": bool(cfg.get("opptak", True)),
        "status_lan": bool(cfg.get("status_lan")),
        "stamp_null": cfg.get("stamp_null", 0.0), "krenging_null": cfg.get("krenging_null", 0.0),
        "snu_stamp": bool(cfg.get("snu_stamp")), "snu_krenging": bool(cfg.get("snu_krenging")),
        "ntrip_pa": bool(n.get("pa")), "caster": n.get("caster", ""), "ntrip_port": n.get("port", 2101),
        "mountpoint": n.get("mountpoint", ""), "brukar": n.get("brukar", ""), "har_passord": bool(n.get("passord")),
        "rtcm_til": n.get("rtcm_til") or "", "ntrip_versjon": str(n.get("versjon", "auto")),
        "demo": bool(cfg.get("demo")), "porter": porter(), "config_fil": Path(cfg_path).name,
        "har_token": bool(_read(HER / "oppdatering_lokal.json").get("token")),
    }


def _f(v, lo, hi, name):
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        raise ValueError(f"«{name}» må vere eit tal")
    if not lo <= x <= hi:
        raise ValueError(f"«{name}» må vere mellom {lo} og {hi}")
    return x


def lagre(cfg_path, d):
    """Skriv innstillingane. Kastar ValueError med ei forståeleg melding ved ugyldige verdiar."""
    cfg_path = Path(cfg_path)
    cfg = _read(cfg_path)
    if not str(d.get("mottakar", "")).strip():
        raise ValueError("vel porten til mottakaren")
    inn = [{"port": str(d["mottakar"]).strip(), "baud": int(d.get("mottakar_baud") or 115200)}]
    if str(d.get("imu", "")).strip():
        inn.append({"port": str(d["imu"]).strip(), "baud": int(d.get("imu_baud") or 115200)})
    cfg["inn"] = inn
    ov = str(d.get("onevision", "")).strip()
    cfg["ut_seriell"] = [{"port": ov, "baud": 115200}] if ov else []
    cfg["tcp_port"] = int(_f(d.get("tcp_port", 5000), 1, 65535, "TCP-port"))
    cfg["spakarm"] = {"fram": _f(d.get("fram", 0), -3, 3, "fram"), "hogre": _f(d.get("hogre", 0), -3, 3, "høgre"),
                      "opp": _f(d.get("mast", 1.4), 0, 5, "mastehøgd")}
    cfg["mottakar_kompenserer"] = bool(d.get("mottakar_kompenserer"))
    if d.get("utgang") not in ("rett_antenne", "referansepunkt"):
        raise ValueError("ukjend utgang")
    cfg["utgang"] = d["utgang"]
    cfg["djupn_sanntid"] = _f(d.get("djupn_sanntid", 0), 0, 20, "djupn i sanntid")
    cfg["radar_djupn"] = _f(d.get("radar_djupn", 2.5), 0.5, 30, "djupast georadaren skannar")
    if str(d.get("sone")) not in ("32", "33", "35", "auto"):
        raise ValueError("UTM-sone må vere 32, 33, 35 eller auto")
    cfg["sone"] = str(d["sone"])
    cfg["opptak"] = bool(d.get("opptak"))
    cfg["status_lan"] = bool(d.get("status_lan"))
    cfg["stamp_null"] = _f(d.get("stamp_null", 0), -20, 20, "stamp null")
    cfg["krenging_null"] = _f(d.get("krenging_null", 0), -20, 20, "krenging null")
    cfg["snu_stamp"], cfg["snu_krenging"] = bool(d.get("snu_stamp")), bool(d.get("snu_krenging"))
    n = dict(cfg.get("ntrip") or {})
    n["pa"] = bool(d.get("ntrip_pa"))
    n["rtcm_til"] = str(d.get("rtcm_til") or "").strip() or None
    n["versjon"] = str(d.get("ntrip_versjon") or "auto")
    cfg["ntrip"] = n
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not cfg.get("demo"):          # innlogginga i eiga fil som aldri kjem i git
        lp = HER / "ntrip_lokal.json"
        lok = _read(lp)
        for k_ui, k in (("caster", "caster"), ("mountpoint", "mountpoint"), ("brukar", "brukar")):
            lok[k] = str(d.get(k_ui) or "").strip()
        lok["port"] = int(_f(d.get("ntrip_port", 2101), 1, 65535, "NTRIP-port"))
        if d.get("passord"):
            lok["passord"] = str(d["passord"])
        lok.pop("pa", None)            # av/på ligg i geoscan_config.json
        lok.pop("rtcm_til", None)
        lok.pop("versjon", None)
        lp.write_text(json.dumps(lok, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if str(d.get("token") or "").strip():   # GitHub-nøkkel for oppdatering (berre lesetilgang), aldri i git
        tp = HER / "oppdatering_lokal.json"
        t = _read(tp)
        t["token"] = str(d["token"]).strip()
        tp.write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
    return cfg
