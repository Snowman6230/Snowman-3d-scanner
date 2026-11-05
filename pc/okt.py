# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Økter: alt operatøren held på med blir lagra, så han kan halde fram der han slapp.

Ei økt har:
  - loggane (skanningane) som høyrer til ho – kvar oppstart legg til loggen sin
  - siste resultat (eksportfila som vart retta, med z, sone og val av skanningar)
  - skjermtilstanden: fane, kartutsnitt, valde objekt, profil, «grav nedover» og tverrsnitt

Ved oppstart vel operatøren «hald fram med førre økt» eller «start ny økt». Ei avslutta økt blir lagd i
okt_arkiv/. Etter omstart (oppdatering, nye innstillingar) held programmet fram i same økt utan å spørje.
Alt ligg i loggmappa (logg/okt.json og logg/okt_arkiv/), som oppdateringa aldri rører.
"""
import json
import threading
import time
import uuid
from pathlib import Path


class Okt:
    def __init__(self, mappe):
        self.dir = Path(mappe)
        (self.dir / "okt_arkiv").mkdir(parents=True, exist_ok=True)
        self.fil = self.dir / "okt.json"
        self.lock = threading.Lock()
        self.noverande = None        # økta som er i bruk etter valet
        self.val_gjort = False
        self.forrige = self._les()
        self.denne_loggen = []       # loggfilene frå denne oppstarten (blir lagde til økta ved valet)

    # ---------- fil ----------
    def _les(self):
        try:
            return json.loads(self.fil.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _skriv(self):
        if self.noverande is None:
            return
        self.noverande["sist_lagra"] = time.strftime("%Y-%m-%d %H:%M:%S")
        tmp = self.fil.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.noverande, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.fil)        # atomisk: ei halvskriven økt blir aldri liggjande

    # ---------- val ved oppstart ----------
    def samandrag(self, o):
        if not o:
            return None
        r = o.get("resultat") or {}
        return {"id": o.get("id"), "namn": o.get("namn") or "", "starta": o.get("starta"),
                "sist_lagra": o.get("sist_lagra"), "skanningar": len(o.get("loggar") or []),
                "resultat": r.get("namn"), "fane": (o.get("ui") or {}).get("fane")}

    def ny(self, namn=""):
        with self.lock:
            if self.forrige and self.forrige.get("id"):
                arkiv = self.dir / "okt_arkiv" / f"{self.forrige.get('starta', '').replace(':', '').replace(' ', '_')}_{self.forrige['id'][:8]}.json"
                arkiv.write_text(json.dumps(self.forrige, ensure_ascii=False, indent=1), encoding="utf-8")
            self.noverande = {"id": uuid.uuid4().hex, "namn": str(namn or "")[:80],
                              "starta": time.strftime("%Y-%m-%d %H:%M:%S"), "loggar": list(self.denne_loggen),
                              "resultat": None, "ui": {}}
            self.val_gjort = True
            self._skriv()
            return self.noverande

    def fortset(self):
        with self.lock:
            if not self.forrige:
                self.val_gjort = False
            else:
                self.noverande = self.forrige
                lg = self.noverande.setdefault("loggar", [])
                for f in self.denne_loggen:
                    if f not in lg:
                        lg.append(f)
                self.val_gjort = True
                self._skriv()
                return self.noverande
        return self.ny()

    def auto(self, omstart):
        """Ingen førre økt → ny utan spørsmål. Omstart (oppdatering/innstillingar) → hald fram utan spørsmål."""
        if not self.forrige:
            self.ny()
        elif omstart:
            self.fortset()

    # ---------- under arbeidet ----------
    def legg_til_logg(self, namn):
        if not namn:
            return
        with self.lock:
            if namn not in self.denne_loggen:
                self.denne_loggen.append(namn)
            if self.noverande is not None and namn not in self.noverande.setdefault("loggar", []):
                self.noverande["loggar"].append(namn)
                self._skriv()

    def sett_resultat(self, r):
        with self.lock:
            if self.noverande is not None:
                self.noverande["resultat"] = r
                self._skriv()

    def lagre_ui(self, ui):
        with self.lock:
            if self.noverande is not None and isinstance(ui, dict):
                self.noverande.setdefault("ui", {}).update(ui)
                self._skriv()

    def lagre(self):
        with self.lock:
            self._skriv()

    def status(self):
        return {"val_gjort": self.val_gjort, "noverande": self.noverande,
                "forrige": None if self.val_gjort else self.samandrag(self.forrige)}
