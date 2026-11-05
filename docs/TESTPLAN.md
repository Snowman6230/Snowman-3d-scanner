# Testplan – Snowman Geoscan

*Alpindata v/Hans Petter B. Sørensen*

Fire steg, frå skrivebordet til felt. Ta neste steg først når det førre er godkjent.

## Steg 1 – Demo utan utstyr (kva Windows-PC som helst, 10 min)

1. Installer Python 3.11 eller nyare frå python.org. Kryss av for **«Add python.exe to PATH»**.
2. Last ned repoet: på github.com/Snowman6230/Snowman-3d-scanner, vel **Code → Download ZIP** og pakk ut.
3. Dobbeltklikk `pc\INSTALL.bat` (første gong).
4. Dobbeltklikk `pc\START-DEMO.bat`. Det opnar seg to vindauge og nettlesaren med statussida.

**Godkjent når** statussida viser den raude DEMO-linja, RTK FIX, helling ±6° som skiftar når vogna snur, ei retting på
ca. 15 cm og NTRIP «tilkopla». Simulatorvindauget skal vise at RTCM kjem fram og GGA blir sendt til casteren.

## Steg 2 – Mot R12i innandørs (Norman sin T100, 30 min)

1. Lukk Trimble Access. Berre eitt program kan ha COM23 open.
2. I `pc\geoscan_config.json`: `"inn": [{"port": "COM23"}]`, `"ut_seriell": []` og `"mottakar_kompenserer": false`.
3. Start `START-GEOSCAN.bat`.

**Godkjent når** porten står som «open», fix og satellittar blir viste, og posisjonen er fornuftig (DGPS innandørs
er greitt). Statussida skal seie «ingen fersk helling», sidan R12i ikkje sender stamp og krenging som tal.

## Steg 3 – NTRIP og RTK ute (30 min)

1. Kopier `ntrip_lokal.eksempel.json` til `ntrip_lokal.json`, og fyll inn caster, port, mountpoint TH, brukar og
   passord. Fila blir aldri lagd i git.
2. Prøv først utan `rtcm_til`, så RTCM går over USB.
3. Gå ut med fri sikt og vent 1–3 minutt.

**Godkjent når** NTRIP står som «tilkopla», kB-teljaren går, og fix blir **RTK FIX**. Blir det verande DGPS eller
FLOAT medan NTRIP er tilkopla: set `"rtcm_til"` til Bluetooth-porten (port 2, t.d. COM20) og prøv på nytt.
Skriv ned kva som verka, i `docs/OPNE-SPORSMAL.md` (punkt 7).

## Steg 4 – Hellingskorreksjon og OneVision i felt

**4a. Masta, statisk:**
1. Set stanghøgda i R12i lik mastehøgda (mål ho), og slå på tilt.
2. Set `"mottakar_kompenserer": true` og `"spakarm": {"opp": <mastehøgda>}`.
3. Still vogna over eit innmålt punkt (spikar). Vipp ho 5–10° til kvar side og framover/bakover.

Godkjent: posisjonen ut skal liggje i ro innan 1–2 cm. Utan tilt i R12i flyttar han seg ca. 2,4 cm per grad.

**4b. OneVision:**
1. Set `"ut_seriell": [{"port": "COM34"}]` (com0com-paret COM34 → COM24).
2. Vel COM24 i OneVision. Antenneoppsettet i OneVision skal stå som før.

Godkjent: OneVision viser «GNSS connection OK» med RTK.

**4c. Djupna (krev ekstra IMU på ramma):**
1. Skann eit røyr med kjent trasé i ein sidebakke, éin gong i kvar retning.
2. Eksporter objekta.
3. Køyr `korriger_objekt.py` med loggen.

Godkjent: utan retting ligg dei to sporane 2·(h + d)·sin(helling) frå kvarandre, med retting skal dei falle saman.
Ta vare på eksportfila: ho er den ekte eksempelfila som manglar (punkt 4).

## Etter kvar felttur

- Loggane ligg i `pc\logg\`: `geoscan_*.csv` (retting) og `raa_*.nmea` (alt mottakaren sende).
- Send `raa_*.nmea` til utviklinga. Med `python geoscan.py --fil raa_….nmea` kan turen spelast av att og
  feilsøkjast utan å reise ut.
