# Snowman Geoscan – logo, namn og opphav

*Alpindata v/Hans Petter B. Sørensen*

## Logo og ikon

Kjelda til alt er `pc/ikon/lag-ikon.py`. Endre der og køyr `python3 lag-ikon.py`, så blir alle filene laga på
nytt og er like. Skriptet krev Playwright/Chromium og Pillow, men berre ved utvikling.

Uttrykket er det same som i SNOWMAN Snødjupne: natthimmel, dei kvite fjelltoppane frå SNOWMAN-logoen, snøflata,
og same fargar og skrift. I staden for tråkkemaskina står **georadarvogna** (IDS Stream C, sett frå sida) med
GNSS-masta på snøflata. Radarbølgjene går ned i bakken mot eit nedgrave røyr.

| Fil | Bruk |
|---|---|
| `pc/ikon/geoscan.svg` | Hovudikonet (512 × 512), kjeldefil |
| `pc/ikon/geoscan-enkel.svg` | Forenkla ikon for 16–48 px |
| `pc/ikon/geoscan-logo.svg` | Logo med tekst: fjelltoppar, SNOWMAN, GEOSCAN og «Alpindata v/Hans Petter B. Sørensen» |
| `pc/ikon/geoscan.ico` | Snarvegane på skrivebordet (16–256 px) |
| `pc/ikon/oppstart.png` | Oppstartbiletet som blir vist når programmet startar |
| `pc/web/vendor/geoscan-ikon.*`, `geoscan-logo.svg` | Nettlesaren: fane-ikon, toppfelt og rapportar |

Fargar: natt `#0b2a44` → `#15507c`, snø `#ffffff`/`#dcecf7`, radar raud `#d42c2c`, GPS `#19e07a`,
radarbølgjer og GEOSCAN `#7fe9ff`, røyr `#ff9d3c`, jord `#6b5138` → `#2f2318`, undertekst `#8cc8f0`.

## Namnet i alt programmet lagar

`pc/opphav.py` har namnet (`NAMN`), produsenten (`PRODUSENT`), copyright og ein fast signatur (`SIGNATUR`,
`SNWGEO-…`). Han blir lagd inn slik:

| Kvar | Synleg | Gøymt (metadata) |
|---|---|---|
| Oppstart | Oppstartbilete med logo, namn i vindauget | – |
| Nettlesaren | Logo og namn øvst | `<meta generator/author>`, HTTP «Server: SnowmanGeoscan/…» |
| Rapport (skriv ut / PDF / HTML) | Logo og namn øvst, namn og signatur nedst på kvar side | `<meta generator>` |
| DXF | Tittelfelt på laget `SNOWMAN_GEOSCAN` | Kommentar 999 med namn, versjon og signatur |
| GeoJSON | – | `generator`, `produsent` og `snowman_geoscan.generator` |
| CSV for Excel | Første line: namn, dato og signatur | – |
| Pakke til utviklar (zip) | Namn i SVAR.txt | Zip-kommentar |
| Rå NMEA-logg | – | Første line `# Snowman Geoscan …` |

Utsettingsfila for Trimble Access har med vilje ikkje noko ekstra, så importen ikkje feilar.
`opphav.sjekk_signatur(fil)` finn signaturen att i ei fil.
