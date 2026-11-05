# Snowman-3d-scanner

Oppdrag for Norman Hole, Hole Anlegg AS. Eigar: Hans Petter Brunstad Sørensen (Alpindata).
Skriv alltid på nynorsk: kode-kommentarar, dokumentasjon og commit-meldingar.

## Avgrensing mot SNOWMAN Snødjupne

- Dette repoet er eit **eige prosjekt**. SNOWMAN Snødjupne (Snowman6230/Snowman-Snowdeept) er eit anna prosjekt og skal **ikkje endrast** herifrå. Det kan berre lesast som referanse.
- Treng ein kode frå Snødjupne (NTRIP-klient, GGA-tolking, geoide, helling), skal han **kopierast inn hit** med opphav notert. Dei to repoa skal aldri koplast saman med submodule eller import på tvers.

## Utgangspunkt

- `docs/Overlevering_GNSS-rover_til_snowman.docx` (og `.md`): overleveringa frå Norman Hole 5.11.2026. Ho omtalar Trimble R12i, NTRIP mountpoint TH og NMEA til OneVision (IDS Stream C georadar).
- `docs/Samanlikning_GNSS-rover_mot_SNOWMAN-Snodjupne.md`: kva Snødjupne allereie løyser, og kva som manglar.

## Faste reglar

- Passord, brukarnamn og NTRIP-tenesteopplysingar skal aldri inn i repoet.
- Høgd: rekn ut ellipsoidehøgd (GGA-felt 9 + 11), og gjer om til NN2000 med Kartverket-geoiden. Stol ikkje på den ortometriske høgda frå mottakaren.
- Godta alle talker-ID-ar for NMEA ($GNGGA, $GPGGA, $INGGA osb.).
