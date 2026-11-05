# Opne spørsmål – SNOWMAN Geoscan

Ting som manglar før hellingskorreksjonen kan setjast i drift. Eigaren (Hans Petter) er ikkje sikker på desse enno.
**Spør eigaren om dei** når arbeidet held fram, og flytt svaret til «Avklart» med dato.

Oppretta 5. november 2026.

## Opne

| # | Spørsmål | Kvifor det trengst | Inntil vidare |
|---|---|---|---|
| 1 | **Mastehøgda på Stream C:** høgda frå antennefestet (merket for antennehøgd) ned til radaren. *Førebels: 1,40 eller 1,50 m, avhengig av brakett. Må målast på vogna.* | Spakarmen (`spakarm.opp`) og stanghøgda i R12i. Feil høgd gir feil retting for masta. | 1,40 m |
| 2 | **Referansepunktet til OneVision:** *Førebels: midt i antennerekkja, på bakken. Masta sit bak/midt på vogna, og OneVision flyttar posisjonen fram og ned med eige oppsett.* Står att: **kor langt fram** referansepunktet ligg frå masta (`spakarm.fram`), og kva tal som står i OneVision no. | Om `utgang` skal vere `rett_antenne` eller `referansepunkt`, og om antenna står forskoven fram/sidelengs (`spakarm.fram`/`hogre`). | `rett_antenne`, inga forskyving |
| 3 | **Ekstra IMU på ramma, ja eller nei.** R12i gir ikkje ut stamp/krenging som tal. *Førebels: tilrådd. Kva modell og kva NMEA-melding han skal sende, står att.* | Utan ekstra IMU blir berre masta retta, ikkje djupnfeilen (opptil ca. 32 cm på 2,5 m ved 5° helling). | Berre masta (R12i rettar sjølv) |
| 4 | **Ekte eksportfil frå GRED HD / OneVision med objekt** (røyr, kablar). *Førebels: GeoJSON med [E, N, djupn eller høgd] og crs (t.d. EPSG:5973). Det er no støtta, men eksempelet var oppdikta (koordinatane ligg i Jämtland). Ei ekte fil trengst for å stadfeste formatet.* | `korriger_objekt.py` må kunne lese eksporten. | GeoJSON og CSV |
| 5 | **Brukar OneVision kurs frå NMEA (HDT)** til å leggje skannebeltet, eller berre sporet? | Om Geoscan bør sende ut ein retta kurs. | Kurs blir ikkje sendt |
| 6 | **Held R12i-IMU-en justeringa** på ei vogn som blir trekt (støyt, snuing)? | Om R12i kan rette masta åleine i felt. | Ikkje testa |
| 7 | **RTK FIX (4) ute** med R12i og eigen caster (mountpoint TH). | Alt over føreset cm-nøyaktigheit. Er berre testa som DGPS innandørs. | Ikkje stadfest |

## Avklart

(ingenting stadfest enno)

## Kjelde for dei førebels svara

5.11.2026: eit KI-samandrag som Hans Petter delte (ikkje frå IDS si dokumentasjon). Bør stadfestast mot vogna,
OneVision-oppsettet til Norman og ei ekte eksportfil.
