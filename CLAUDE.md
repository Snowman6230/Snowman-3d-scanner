# Snowman-3d-scanner – Snowman Geoscan

Programmet heiter **Snowman Geoscan**. Under namnet står alltid «Alpindata HP Brunstad Sørensen»
(statusside, oppstart, dokument). Namn, produsent og signatur ligg i `pc/opphav.py`. Alt programmet lagar
(rapportar, eksportfiler, pakkar, loggar) skal ha med namnet: synleg i rapportar og gøymt som metadata i
datafiler (sjå `docs/LOGO.md`). Logoen er same uttrykk som SNOWMAN Snødjupne, men med georadar. Kjelda er
`pc/ikon/lag-ikon.py`.

Oppdrag for Norman Hole, Hole Anlegg AS. Eigar: Hans Petter Brunstad Sørensen (Alpindata).
Skriv alltid på nynorsk: kode-kommentarar, dokumentasjon og commit-meldingar.

## Avgrensing mot SNOWMAN Snødjupne

- Dette repoet er eit **eige prosjekt**. SNOWMAN Snødjupne (Snowman6230/Snowman-Snowdeept) er eit anna prosjekt og skal **ikkje endrast** herifrå. Det kan berre lesast som referanse.
- Treng ein kode frå Snødjupne (NTRIP-klient, GGA-tolking, geoide, helling), skal han **kopierast inn hit** med opphav notert. Dei to repoa skal aldri koplast saman med submodule eller import på tvers.

## Utgangspunkt

- `docs/Overlevering_GNSS-rover_til_snowman.docx` (og `.md`): overleveringa frå Norman Hole 5.11.2026. Ho omtalar Trimble R12i, NTRIP mountpoint TH og NMEA til OneVision (IDS Stream C georadar).
- `docs/Samanlikning_GNSS-rover_mot_SNOWMAN-Snodjupne.md`: kva Snødjupne allereie løyser, og kva som manglar.

## Opne spørsmål – spør eigaren

`docs/OPNE-SPORSMAL.md` listar det som manglar: mastehøgd, referansepunktet til OneVision, ekstra IMU,
eksportformat frå GRED HD og meir. Eigaren var ikkje sikker 5.11.2026 og vil bli spurt seinare.
**Ved byrjinga av nytt arbeid i dette repoet: spør eigaren om dei opne punkta** før du byggjer vidare på
mellombelse verdiar. Flytt svar til «Avklart» med dato.

## Testpakkar frå Norman og svar tilbake

Norman fyller ut testsjekklista og spørsmåla under «Send inn», og sender pakka (zip) til hansps@alpindata.no.
Når Hans Petter gir deg ei pakke:

1. Les `SJEKKLISTE.txt`, `SVAR.txt`, `filer/`, `logg/` og `system.json`. Rådata (`logg/raa_*.nmea`) kan
   spelast av med `python pc/geoscan.py --fil …`.
2. Flytt svar på opne spørsmål til «Avklart» i `docs/OPNE-SPORSMAL.md`, og rett innstillingar og kode.
3. **Svar Norman** med ei ny melding øvst i `pc/meldingar.json`. Meldinga skal **alltid nemne versjonsnummeret**
   (i tittelen og ved kvar endring i teksten), slik at Norman ser kva versjon han må ha. Ho skal ha `id` (unik), `dato`, `versjon`,
   `tittel` og `tekst`, og `sjekk` med svar per punkt (`{"n2": {"tekst": "…", "prov_att": true}}`).
4. Auk `VERSJON`, skriv i `ENDRINGSLOGG.md`, test og push. Norman ser tittelen på meldinga i
   «Ny versjon»-lina. Etter oppdateringa ser han meldinga øvst og svara ved punkta i sjekklista.

## Faste reglar

- Passord, brukarnamn og NTRIP-tenesteopplysingar skal aldri inn i repoet.
- Høgd: rekn ut ellipsoidehøgd (GGA-felt 9 + 11), og gjer om til NN2000 med Kartverket-geoiden. Stol ikkje på den ortometriske høgda frå mottakaren.
- Godta alle talker-ID-ar for NMEA ($GNGGA, $GPGGA, $INGGA osb.).

## Struktur

- `pc/`: Geoscan-programmet (Python, pyserial). Spesifikasjon i `docs/GEOSCAN.md`.
- `tests/`: `python -m pytest tests`. Køyr før push.
- Forteikn som i Snødjupne: stamp + = fronten opp, krenging + = høgre side ned. Kurs i grader frå sann nord.

## Versjon og oppdatering

- Auk `VERSJON` i `pc/geoscan.py` ved kvar endring som skal ut til PC-ane. Oppdateringa (`pc/oppdater.py`)
  samanliknar versjonsnummeret, og utan ny versjon ser ikkje PC-ane endringa.
- Skriv i `ENDRINGSLOGG.md` (nyaste øvst, med dato, kva og kvifor).
- Filer som berre ligg på PC-en (`geoscan_config.json`, `ntrip_lokal.json`, `oppdatering_lokal.json`, `logg/`,
  `reserve/`, `innsendt/`, `pakkar/`, `resultat/`) blir aldri overskrivne. Nye innstillingar skal ha standardverdi i `STANDARD` i `geoscan.py`.
