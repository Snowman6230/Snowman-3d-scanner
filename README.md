# Snowman-3d-scanner

Oppdrag for Norman Hole, Hole Anlegg AS.

Eige prosjekt, skilt frå SNOWMAN Snødjupne (Snowman6230/Snowman-Snowdeept).

## Dokument

- [Overlevering: GNSS-rover til snowman](docs/Overlevering_GNSS-rover_til_snowman.md) ([.docx](docs/Overlevering_GNSS-rover_til_snowman.docx))
- [Samanlikning med SNOWMAN Snødjupne](docs/Samanlikning_GNSS-rover_mot_SNOWMAN-Snodjupne.md)
- [SNOWMAN Geoscan – hellingskorreksjon for IDS Stream C](docs/GEOSCAN.md)
- [Opne spørsmål](docs/OPNE-SPORSMAL.md) – det som manglar før drift

## Program (pc/)

- `geoscan.py`: les R12i (og eventuelt ein ekstra IMU), og sender hellingsretta NMEA til OneVision (com0com) og TCP 5000. Skriv logg.
- `korriger_objekt.py`: rettar objekt frå georadaren (røyr, kablar) for djupnfeilen ut frå loggen.
- `helling.py`, `nmea.py`, `koordinat.py`, `geoide.py`: delane bak. Opphav frå Snødjupne er notert i kvar fil.

Testar: `python -m pytest tests`
