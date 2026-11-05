# SNOWMAN Geoscan – hellingskorreksjon for IDS Stream C

Same prinsipp som i SNOWMAN Snødjupne: hellinga på maskina rettar både posisjonen og høgda/djupna. Snødjupne
reknar det for ei tråkkemaskin, Geoscan for ein georadar som skannar ned til ca. 2,5 m.

## Problemet

GNSS-antenna står på ei mast over radarvogna. OneVision reknar som om vogna alltid står vatrett. Når vogna hallar,
blir det to feil:

1. **Masta:** antenna står ikkje rett over radaren. Feilen er h·sin(helling).
2. **Djupna:** radaren måler avstanden vinkelrett på bakken, ikkje loddrett. Eit objekt på djupn d blir lagt
   d·sin(helling) feil sidelengs, mot oppsida av hellinga.

Total feil ≈ (h_mast + d)·sin(helling). Med h = 1,2 m:

| Helling | Overflata | 1,0 m djupt | 2,5 m djupt |
|---|---|---|---|
| 2° | 4 cm | 8 cm | 13 cm |
| 5° | 10 cm | 19 cm | 32 cm |
| 10° | 21 cm | 38 cm | 64 cm |

Skannebreidda til Stream C er 96 cm. Alt over nokre få grader flyttar altså røyr og kablar ein stor del av breidda.

## Løysinga i to delar

```
R12i (tilt på) ─► geoscan.py ─► NMEA ─► com0com ─► OneVision   (sanntid: masta retta)
                      │
                      └─► logg/geoscan_*.csv (posisjon, helling, kurs)
                                     │
GRED HD/OneVision: objekt (CSV) ─────┴─► korriger_objekt.py ─► objekt retta for djupn
```

**Del 1, sanntid (masta):** retta posisjon går til OneVision, éin posisjon per skann.
**Del 2, etterpå (djupna):** kvart objekt har si eiga djupn og blir retta med hellinga frå loggen der det vart
målt. Det kan ikkje gjerast med éin NMEA-posisjon. Vil ein ha ei grov retting i sanntid, kan `djupn_sanntid` setjast
til ei typisk djupn (til dømes 1,0 m). Objekta blir då retta for resten etterpå.

## Hellinga: Trimble R12i

R12i har innebygd IMU. Han gir ikkje ut stamp og krenging som tal: Trimble skriv at det ikkje finst noko ope
dataformat for heading frå R12i. Han reknar dei om internt og sender ut posisjonen til *stangspissen*. Det blir
brukt slik:

- **Masta:** set stanghøgda i R12i lik høgda frå antennefestet ned til referansepunktet på radaren. Ta målet frå
  merket for antennehøgd. Då sender R12i sjølv punktet på bakken, og masta blir retta i mottakaren
  (`"mottakar_kompenserer": true`). Norman har alt sett at dette verkar: hoppet på 2,2 m når IMU blir slått av og på.
- **Djupna:** krev stamp og krenging som tal. Det gir ikkje R12i. Alternativ:
  1. Ein liten IMU på ramma som sender NMEA ($PASHR, $xxHPR, $PSAT,HPR eller $PTNL,AVR). Han blir lagd til som ein
     ekstra inngang i `inn`, og programmet les han utan endringar. Dette er den sikraste løysinga.
  2. Rekna helling (som «estimat» i Snødjupne): stamp frå høgdeendringa langs sporet, krenging frå terrengmodellen.
     Ikkje laga enno.

Om IMU-en i R12i held justeringa på ei vogn som blir trekt, er ikkje testa. Trimble skriv at han kan miste
justeringa ved støyt eller rask snuing.

## Oppsett (pc/geoscan_config.json)

| Nøkkel | Tyding |
|---|---|
| `inn` | Portar å lese: R12i (COM23 USB), og eventuelt ein ekstra IMU. |
| `ut_seriell` | Portar å skrive til, til dømes com0com COM34 → COM24 for OneVision. |
| `tcp_port` | NMEA til fleire program over TCP (5000). Erstattar PowerShell-splitteren. |
| `spakarm` | Antennefasesenteret sett frå referansepunktet på radaren: fram, høgre, opp (m). |
| `utgang` | `rett_antenne`: der antenna ville stått om vogna var vatrett. Antenneoppsettet i OneVision kan då stå som før. `referansepunkt`: punktet på radaren, og antennehøgda i OneVision må setjast til 0. |
| `mottakar_kompenserer` | `true` når R12i har tilt på og stanghøgd = mast. Programmet rettar då ikkje masta ein gong til. |
| `djupn_sanntid` | Djupn (m) å rette for i sanntid. 0 = berre masta. |
| `hoegd` | `nn2000`: ellipsoidisk høgd − Kartverket-geoiden (HREF2018B). `mottakar`: høgda frå mottakaren. |
| `sone` | UTM-sone for loggen (32 for Sunnmøre). Objektfila må vere i same sone. |
| `stamp_null`, `krenging_null`, `snu_stamp`, `snu_krenging` | Kalibrering av ein ekstra IMU, sjå nedanfor. |
| `utan_helling` | `send_ukorrigert` (standard) eller `stopp` når hellinga manglar. |

## Kalibrering av ein ekstra IMU

1. Still vogna på eit fast punkt og les stamp og krenging. Snu vogna 180° på same punkt og les på nytt.
2. Nullpunktet er gjennomsnittet: `stamp_null = (s1 + s2)/2` og `krenging_null = (k1 + k2)/2`.
3. Forteikn: fronten opp skal gi + stamp, og høgre side ned skal gi + krenging. Er det motsett, set `snu_*`.

## Kontroll før bruk

1. **Statisk:** still vogna over eit innmålt punkt. Vipp ho 5–10° til kvar side. Posisjonen ut skal liggje i ro
   innan 1–2 cm.
2. **Djupn:** skann eit røyr med kjent trasé i ein sidebakke i begge retningar. Utan retting blir dei to sporane
   liggjande 2·(h + d)·sin(helling) frå kvarandre. Med retting skal dei falle saman.
3. Sjekk at fix er RTK FIX (4) ute. Det er ikkje stadfest enno.

## Køyring

```
pc\INSTALL.bat          (første gong)
pc\START-GEOSCAN.bat
python korriger_objekt.py --objekt ror.csv --logg logg\geoscan_*.csv --ut ror_retta.csv
python geoscan.py --fil opptak.nmea     (spel av eit opptak, skriv retta NMEA til skjermen)
```

## Ikkje avklart

Sjå [OPNE-SPORSMAL.md](OPNE-SPORSMAL.md) for den fullstendige lista.

- Eksportformatet frå GRED HD/OneVision for objekt (kolonnar, tid, koordinatsystem). Treng ei eksempelfil.
- Om OneVision brukar heading frå NMEA (HDT) til å leggje skannebeltet, eller berre sporet.
- Mastehøgda og kvar referansepunktet på Stream C er definert (midt i antennerekkja?).
