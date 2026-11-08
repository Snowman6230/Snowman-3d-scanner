# Snowman Geoscan – hellingskorreksjon for IDS Stream C

*Alpindata HP Brunstad Sørensen*

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

Skannebreidda til Stream C er 96 cm ifølgje IDS. Mellom dei ytste spora (V24, 23 kanalar) er det 77 cm (±0,383 m i .svy). Karta i Geoscan viser stripa med 77 cm og eit lysare felt ut til 96 cm, midt på radaren (0.9.17). Alt over nokre få grader flyttar altså røyr og kablar ein stor del av breidda.

## Løysinga i to delar

```
NTRIP-caster ◄─GGA── geoscan.py ──RTCM──► R12i            (erstattar Trimble Access for korreksjonane)
R12i (tilt på) ─NMEA─► geoscan.py ─► NMEA ─► com0com ─► OneVision   (sanntid: masta retta)
                           ├─► TCP 5000 (andre program)   ├─► statusside http://localhost:8088
                           └─► logg/geoscan_*.csv (posisjon, helling, kurs) + logg/raa_*.nmea (opptak)
                                     │
OneVision .svy / GRED HD: objekt (GeoJSON/CSV) ─┴─► korriger_objekt.py ─► objekt retta for djupn
```

**Del 1, sanntid (masta):** retta posisjon går til OneVision, éin posisjon per skann.
**Del 2, etterpå (djupna):** kvart objekt har si eiga djupn og blir retta med hellinga frå loggen der det vart
målt. Det kan ikkje gjerast med éin NMEA-posisjon. Vil ein ha ei grov retting i sanntid, kan `djupn_sanntid` setjast
til ei typisk djupn (til dømes 1,0 m). Objekta blir då retta for resten etterpå.

## Hellinga: Trimble R12i

R12i har innebygd IMU. Han gir ikkje ut stamp og krenging som tal: Trimble skriv at det ikkje finst noko ope
dataformat for heading frå R12i. Han reknar dei om internt og sender ut posisjonen til *stangspissen*. Det blir
brukt slik:

- **Masta:** set stanghøgda i R12i lik høgda frå antennefestet ned til bakken (mastefoten). Ta målet frå
  merket for antennehøgd. Då sender R12i sjølv **stangspissen** – foten av masta, rett under antenna når vogna
  står vatrett – og masta blir retta i mottakaren (`"mottakar_kompenserer": true`). Norman har alt sett at dette
  verkar: hoppet på 2,2 m når IMU blir slått av og på.
- **Berre `$INGGA` er stangspissen.** Felttest 7.11: R12i direkte på USB (utan Trimble Access) sende `$GNGGA` –
  antennefasesenteret, IMU-en ikkje i bruk. Stangspissen kom berre gjennom Access. Geoscan reknar no posisjonen som
  stangspiss berre når talker-ID-en er `IN` og `mottakar_kompenserer` er på. Elles er det antenna, og Status
  åtvarar om at masta ikkje blir retta for helling. *(0.9.5. Før vart mastehøgda lagd til høgda òg for `$GNGGA`,
  så høgda til OneVision vart 1,8 m for høg.)* Om R12i kan sende `$INGGA` utan Access, og om det då er spissen
  eller antenna, er ikkje stadfest.
- **Stangspissen er ikkje midt på radaren.** Han ligg der masta står (GPS 0,6 m til venstre). Med `rett_antenne`
  sender Geoscan antenna som om vogna var vatrett: rett over stangspissen, utan sideflytting, og OneVision legg
  til forskyvinga si sjølv. Med `referansepunkt` blir den vassrette delen av spakarmen trekt frå.
  *(Retta 7.11.2026 i 0.9.4: før vart spissen rekna som referansepunktet, og punktet vart flytta 0,6 m ein gong
  for mykje til venstre – spor køyrde motsett veg kom då ca. 1,2 m frå kvarandre.)*
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
| `sone` | UTM-sone for loggen (32 for Sunnmøre). Objekt i ei anna sone (t.d. UTM33 / EPSG:5973) blir rekna om automatisk. |
| `stamp_null`, `krenging_null`, `snu_stamp`, `snu_krenging` | Kalibrering av ein ekstra IMU, sjå nedanfor. |
| `utan_helling` | `send_ukorrigert` (standard) eller `stopp` når hellinga manglar. |
| `opptak` | `true`: all rå NMEA blir lagra i `logg/raa_*.nmea`, så ein felttur kan spelast av att med `--fil`. |
| `status_port`, `status_lan` | Statussida (8088). `status_lan: true` opnar ho for nettbrett/mobil på same nett. |
| `ntrip` | `{"pa": true, "rtcm_til": "COM20", "gga_intervall": 10}`. Innlogginga ligg i `pc/ntrip_lokal.json` (ikkje i git, sjå `ntrip_lokal.eksempel.json`). `rtcm_til`: porten RTCM skal til, til dømes Bluetooth port 2 på R12i. Utan han går RTCM på første inngang (USB). |
| `sjekk_oppdatering` | Sjå etter ny versjon på GitHub ved oppstart (vist på statussida). |

## NTRIP (erstattar Trimble Access)

R12i har ikkje eige internett. Geoscan hentar korreksjonane frå casteren og sender dei til mottakaren. GGA blir
sendt til casteren kvart `gga_intervall` sekund. Det koplar til att av seg sjølv, og har ein vakthund som slår
inn når det ikkje har kome data på 15 s. Ved feil passord eller ukjent mountpoint ventar det 60 s, så casteren
ikkje blir hamra på. NTRIP-klienten er kopiert frå Snødjupne.

Ikkje avklart (frå overleveringa): om R12i tek imot RTCM over USB, eller berre på Bluetooth port 2. Begge delar er
støtta. Prøv først utan `rtcm_til` (USB). Viser statussida at NTRIP er tilkopla, men fixen ikkje blir RTK, set
`rtcm_til` til Bluetooth-porten.

## Grensesnittet i nettlesaren

Sjå [BRUKARRETTLEIING.md](BRUKARRETTLEIING.md). Fanene er Status, Resultat, Send inn og Innstillingar.
Status-fana på http://localhost:8088 viser fix, helling (med ei teikning av vogna), kor mykje som blir retta no, kor stor
djupnfeilen ville vore på 2,5 m, NTRIP og portar. Ho oppdaterer seg kvart sekund og fungerer på mobil.

## Oppdatering utan ny installasjon

- **Statussida:** når det finst ein nyare versjon på GitHub, kjem det opp ein knapp, «Oppdater no». Geoscan lastar
  ned, kontrollerer, legg inn og startar på nytt av seg sjølv (START-GEOSCAN.bat startar på nytt ved kode 3).
- **OPPDATER.bat:** gjer det same frå Utforskaren.
- **TILBAKE-TIL-FORRIGE.bat:** rullar tilbake til versjonen før siste oppdatering.

Tryggleik:
- Den nye versjonen blir kompilert og sjekka før noko blir skrive.
- Filene som blir bytte ut, blir lagra i `pc/reserve/`.
- `geoscan_config.json`, `ntrip_lokal.json` og `logg/` blir aldri rørte.
- Nye innstillingar får standardverdiar automatisk.
- Oppdateringa kan berre startast frå PC-en sjølv, ikkje frå mobil eller nett.

Repoet er privat. PC-en treng difor ein GitHub-nøkkel med berre lesetilgang i `pc/oppdatering_lokal.json`:
`{"token": "github_pat_..."}`. Lag han på GitHub under Settings → Developer settings → Fine-grained tokens, berre
for Snowman-3d-scanner, med «Contents: Read-only». Er git installert og mappa ein git-klon, blir `git pull` brukt i
staden.

## Simulator

`python simuler.py --caster 2101` startar ein SIMULERT mottakar på `socket://127.0.0.1:7777`. Han køyrer vogna fram
og tilbake i ein sidebakke med ±6° krenging. Simulatoren startar òg ein falsk NTRIP-caster med mountpoint SIM, så
heile kjeda kan prøvast utan utstyr. Simulerte data må aldri brukast som målingar.

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
python korriger_objekt.py --objekt eksport.geojson --logg logg\geoscan_*.csv --ut eksport_retta.geojson
python oppdater.py --sjekk               (finst det ein nyare versjon?)
python geoscan.py --fil opptak.nmea     (spel av eit opptak, skriv retta NMEA til skjermen)
```

## Objekt frå OneVision (.svy)

OneVision lagrar dei automatisk funne objekta inne i målefila (`Survey_….svy`, `<Targets>`), ikkje i ei eiga
eksportfil. `svy_objekt.py` les dei og gjer dei om til GeoJSON (namn, linje/punkt, E, N, djupn, EPSG frå fila).
Resultat-fana og `korriger_objekt.py` tek `.svy` direkte. Formatet er tolka frå Kagholvegen-målinga 29.11.2022
(81 objekt) og står i toppen av `svy_objekt.py`.

## Ikkje avklart

Sjå [OPNE-SPORSMAL.md](OPNE-SPORSMAL.md) for den fullstendige lista, og [DJUPNESNITT.md](DJUPNESNITT.md) for
planen om å rette sjølve radarbiletet.

- RTK FIX (4) ute med R12i og mountpoint TH.
- Om R12i-IMU-en held justeringa på ei vogn som blir trekt.
- Ekstra IMU på ramma (for djupnfeilen).
