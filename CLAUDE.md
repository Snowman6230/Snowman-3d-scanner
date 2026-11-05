# Snowman-3d-scanner

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

## Faste reglar

- Passord, brukarnamn og NTRIP-tenesteopplysingar skal aldri inn i repoet.
- Høgd: rekn ut ellipsoidehøgd (GGA-felt 9 + 11), og gjer om til NN2000 med Kartverket-geoiden. Stol ikkje på den ortometriske høgda frå mottakaren.
- Godta alle talker-ID-ar for NMEA ($GNGGA, $GPGGA, $INGGA osb.).

## Struktur

- `pc/`: Geoscan-programmet (Python, pyserial). Spesifikasjon i `docs/GEOSCAN.md`.
- `tests/`: `python -m pytest tests`. Køyr før push.
- Forteikn som i Snødjupne: stamp + = fronten opp, krenging + = høgre side ned. Kurs i grader frå sann nord.
