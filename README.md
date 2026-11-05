# Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

Repo: Snowman-3d-scanner.
Oppdrag for Norman Hole, Hole Anlegg AS.

Eige prosjekt, skilt frå SNOWMAN Snødjupne (Snowman6230/Snowman-Snowdeept).

## Dokument

- [Overlevering: GNSS-rover til snowman](docs/Overlevering_GNSS-rover_til_snowman.md) ([.docx](docs/Overlevering_GNSS-rover_til_snowman.docx))
- [Samanlikning med SNOWMAN Snødjupne](docs/Samanlikning_GNSS-rover_mot_SNOWMAN-Snodjupne.md)
- [Snowman Geoscan – hellingskorreksjon for IDS Stream C](docs/GEOSCAN.md)
- [Opne spørsmål](docs/OPNE-SPORSMAL.md) – det som manglar før drift
- [Brukarrettleiing for operatøren](docs/BRUKARRETTLEIING.md) – start her
- [Testplan](docs/TESTPLAN.md) – start med `pc\START-DEMO.bat`
- [Endringslogg](ENDRINGSLOGG.md)

## Program (pc/)

- `geoscan.py`: les R12i (og eventuelt ein ekstra IMU), og sender hellingsretta NMEA til OneVision (com0com) og TCP 5000. Skriv logg.
- `korriger_objekt.py`: rettar objekt frå georadaren (røyr, kablar) for djupnfeilen ut frå loggen.
- `ntrip_teneste.py` og `ntripklient.py`: hentar NTRIP-korreksjonar og sender RTCM til R12i (erstattar Trimble Access).
- `webtenar.py` og `web/index.html`: grensesnittet i nettlesaren (http://localhost:8088) med fanene Status, Resultat, Send inn og Innstillingar.
- `resultat.py`: loggøkter, spor og retting av eksport (GeoJSON/CSV → GeoJSON/CSV/DXF).
- `innsending.py` og `innstillingar.py`: Send inn-fana (svar, vedlegg, pakke) og Innstillingar-fana.
- `oppdater.py`: oppdatering frå GitHub utan ny installasjon (OPPDATER.bat, TILBAKE-TIL-FORRIGE.bat, eller knappen på statussida).
- `simuler.py`: simulert mottakar og NTRIP-caster for testing.
- `helling.py`, `nmea.py`, `koordinat.py`, `geoide.py`: delane bak. Opphav frå Snødjupne er notert i kvar fil.

Testar: `python -m pytest tests`
