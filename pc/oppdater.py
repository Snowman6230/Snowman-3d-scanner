# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Oppdater Snowman Geoscan frå GitHub utan å installere på nytt.

Same prinsipp som Snødjupne (pc/v1.6/start_snowman.py, oppdater()): med git blir det «git pull», utan git blir
siste versjon lasta ned som zip og berre endra filer skrivne inn i pc-mappa. I tillegg her:
  - den nye versjonen blir kompilert og sjekka FØR noko blir skrive (ein øydelagd versjon blir aldri lagd inn)
  - filene som blir bytte ut, blir lagra i pc/reserve/<versjon>_<tid>/, så «tilbake» kan rulle tilbake
  - aldri rørt: geoscan_config.json, ntrip_lokal.json, oppdatering_lokal.json, logg/, reserve/
  - nye innstillingar kjem automatisk (geoscan.py fyller inn standardverdiar for nøklar som manglar)

Repoet er privat. Nedlasting krev då ein GitHub-nøkkel med berre lesetilgang i pc/oppdatering_lokal.json:
    {"token": "github_pat_..."}      (fine-grained token, berre «Contents: Read-only» på Snowman-3d-scanner)
Er repoet offentleg, trengst ingen nøkkel.

    python oppdater.py            hent og legg inn siste versjon
    python oppdater.py --sjekk    berre sjå om det finst ein nyare versjon
    python oppdater.py --tilbake  rull tilbake til førre versjon
"""
import argparse
import io
import json
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

HER = Path(__file__).resolve().parent
REPO = "Snowman6230/Snowman-3d-scanner"
GREIN = "main"
ALDRI = {"geoscan_config.json", "ntrip_lokal.json", "oppdatering_lokal.json"}
ALDRI_MAPPER = {"logg", "reserve", "__pycache__", ".venv"}


def _token():
    p = HER / "oppdatering_lokal.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("token") or None
    except Exception:
        return None


def _get(url, accept=None, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Snowman-Geoscan-oppdatering"})
    if accept:
        req.add_header("Accept", accept)
    t = _token()
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    return urllib.request.urlopen(req, timeout=timeout).read()


def version_of(text):
    m = re.search(r'^VERSJON = "([^"]+)"', text, re.M)
    return m.group(1) if m else "?"


def local_version():
    return version_of((HER / "geoscan.py").read_text(encoding="utf-8"))


def vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", v))


def remote_version():
    """Versjonen på GitHub (les berre geoscan.py, ikkje heile pakka)."""
    data = _get(f"https://api.github.com/repos/{REPO}/contents/pc/geoscan.py?ref={GREIN}",
                accept="application/vnd.github.raw", timeout=15)
    return version_of(data.decode("utf-8", "replace"))


def check():
    """(lokal, på GitHub, nyare?) – eller (lokal, None, False) utan nett/tilgang."""
    lok = local_version()
    try:
        rem = remote_version()
    except Exception:
        return lok, None, False
    if rem == "?":                      # fann ikkje versjonsnummeret (t.d. eldre versjon på GitHub)
        return lok, None, False
    return lok, rem, vkey(rem) > vkey(lok)


def _skip(rel):
    return rel[0] in ALDRI_MAPPER or (len(rel) == 1 and rel[0] in ALDRI) or any(r == "__pycache__" for r in rel)


def _files_from_zip(data):
    """{relativ sti under pc/: byte} frå zip-en (toppmappa i zip-en blir hoppa over, uansett namn)."""
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for m in z.infolist():
            parts = m.filename.split("/")
            if m.is_dir() or len(parts) < 3 or parts[1] != "pc":
                continue
            rel = tuple(parts[2:])
            if not _skip(rel):
                out[rel] = z.read(m)
    return out


def _verify(files):
    """Kompiler alle .py i ei mellombels mappe. Kastar RuntimeError om noko er øydelagt."""
    if ("geoscan.py",) not in files:
        raise RuntimeError("pakka manglar geoscan.py")
    with tempfile.TemporaryDirectory() as d:
        for rel, b in files.items():
            p = Path(d).joinpath(*rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
            if p.suffix == ".py":
                try:
                    py_compile.compile(str(p), doraise=True)
                except py_compile.PyCompileError as e:
                    raise RuntimeError(f"feil i {'/'.join(rel)}: {e.msg}")


def install(files, pcdir=HER, log=print):
    """Skriv endra filer inn i pcdir. Gamle utgåver blir lagra i reserve/. Returnerer (tal filer, reservemappe)."""
    _verify(files)
    old = version_of((pcdir / "geoscan.py").read_text(encoding="utf-8")) if (pcdir / "geoscan.py").exists() else "ny"
    res = pcdir / "reserve" / f"{old}_{time.strftime('%Y%m%d_%H%M%S')}"
    changed = []
    for rel, b in files.items():
        dst = pcdir.joinpath(*rel)
        if dst.exists() and dst.read_bytes() == b:
            continue                  # uendra (viktig for .bat-fila som køyrer no)
        changed.append((rel, dst, b))
    if not changed:
        return 0, None
    for rel, dst, b in changed:
        bak = res.joinpath(*rel)
        bak.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.copy2(dst, bak)
        else:
            (bak.parent / (bak.name + ".ny")).write_bytes(b"")   # merke: fila fanst ikkje før
    for rel, dst, b in changed:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b)
    (res / "OPPDATERING.txt").write_text(
        f"Oppdatert {time.strftime('%Y-%m-%d %H:%M:%S')} frå v{old}.\n" + "\n".join("/".join(r) for r, _, _ in changed) + "\n",
        encoding="utf-8")
    return len(changed), res


def rollback(pcdir=HER, log=print):
    """Legg tilbake filene frå siste reserve (og fjern filer som kom med oppdateringa)."""
    root = pcdir / "reserve"
    snaps = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime) if root.exists() else []
    if not snaps:
        log("Ingen reserve å rulle tilbake til.")
        return False
    snap = snaps[-1]
    for f in snap.rglob("*"):
        if f.is_dir() or f.name == "OPPDATERING.txt":
            continue
        rel = f.relative_to(snap)
        if f.name.endswith(".ny"):
            tgt = pcdir / rel.parent / f.name[:-3]
            if tgt.exists():
                tgt.unlink()
        else:
            tgt = pcdir / rel
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, tgt)
    shutil.rmtree(snap)
    log(f"Rulla tilbake til v{snap.name.split('_')[0]}.")
    return True


def update(log=print):
    """Hent og legg inn siste versjon. Returnerer True om noko vart endra."""
    repo_root = HER.parent
    old = local_version()
    if (repo_root / ".git").exists() and shutil.which("git"):
        log("Hentar siste versjon med git …")
        r = subprocess.run(["git", "-C", str(repo_root), "pull", "--ff-only"], capture_output=True, text=True)
        if r.returncode != 0:
            log("Oppdateringa feila: " + (r.stderr.strip() or r.stdout.strip()))
            return False
        changed = "Already up to date" not in r.stdout
    else:
        log("Lastar ned siste versjon frå GitHub …")
        try:
            if _token():
                data = _get(f"https://api.github.com/repos/{REPO}/zipball/{GREIN}")
            else:
                data = _get(f"https://github.com/{REPO}/archive/refs/heads/{GREIN}.zip")
        except Exception as e:
            log(f"Fekk ikkje lasta ned ({e}). Sjekk nettet, og at pc/oppdatering_lokal.json har ein gyldig nøkkel "
                f"(repoet er privat).")
            return False
        try:
            n, res = install(_files_from_zip(data), log=log)
        except RuntimeError as e:
            log(f"Den nye versjonen vart IKKJE lagd inn: {e}. Ingenting er endra.")
            return False
        changed = n > 0
        log(f"{n} filer oppdaterte." + (f" Reserve: {res}" if res else ""))
    if changed and (HER / "requirements.txt").exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check",
                        "-r", str(HER / "requirements.txt")])
    new = local_version()
    log(f"Ferdig: v{old} → v{new}. Start Geoscan på nytt." if new != old else f"Ferdig: du har siste versjon (v{new}).")
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description="Oppdater Snowman Geoscan frå GitHub")
    ap.add_argument("--sjekk", action="store_true", help="berre sjå om det finst ein nyare versjon")
    ap.add_argument("--tilbake", action="store_true", help="rull tilbake til førre versjon")
    a = ap.parse_args(argv)
    if a.tilbake:
        rollback()
    elif a.sjekk:
        lok, rem, nyare = check()
        print(f"Installert v{lok}. " + ("Fekk ikkje kontakt med GitHub." if rem is None
                                         else f"Ny versjon v{rem} finst." if nyare else "Du har siste versjon."))
    else:
        update()


if __name__ == "__main__":
    main()
