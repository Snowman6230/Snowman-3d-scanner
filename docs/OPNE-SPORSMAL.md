# Opne spørsmål – SNOWMAN Geoscan

Ting som manglar før hellingskorreksjonen kan setjast i drift. Eigaren (Hans Petter) er ikkje sikker på desse enno.
**Spør eigaren om dei** når arbeidet held fram, og flytt svaret til «Avklart» med dato.

Oppretta 5. november 2026.

## Opne

| # | Spørsmål | Kvifor det trengst | Inntil vidare |
|---|---|---|---|
| 1 | **Mastehøgda på Stream C:** høgda frå antennefestet (merket for antennehøgd) ned til radaren. | Spakarmen (`spakarm.opp`) og stanghøgda i R12i. Feil høgd gir feil retting for masta. | 1,20 m (berre eit anslag) |
| 2 | **Referansepunktet til OneVision:** kva punkt på vogna posisjonen gjeld for (midt i antennerekkja? på bakken?), og kva antenneoppsett OneVision har no. | Om `utgang` skal vere `rett_antenne` eller `referansepunkt`, og om antenna står forskoven fram/sidelengs (`spakarm.fram`/`hogre`). | `rett_antenne`, inga forskyving |
| 3 | **Ekstra IMU på ramma, ja eller nei.** R12i gir ikkje ut stamp/krenging som tal. | Utan ekstra IMU blir berre masta retta, ikkje djupnfeilen (opptil ca. 32 cm på 2,5 m ved 5° helling). | Berre masta (R12i rettar sjølv) |
| 4 | **Eksempelfil frå GRED HD / OneVision med objekt** (røyr, kablar): format, kolonnar, tid, koordinatsystem. | `korriger_objekt.py` må kunne lese eksporten. | Generisk CSV: austing; nording; djupn |
| 5 | **Brukar OneVision kurs frå NMEA (HDT)** til å leggje skannebeltet, eller berre sporet? | Om Geoscan bør sende ut ein retta kurs. | Kurs blir ikkje sendt |
| 6 | **Held R12i-IMU-en justeringa** på ei vogn som blir trekt (støyt, snuing)? | Om R12i kan rette masta åleine i felt. | Ikkje testa |
| 7 | **RTK FIX (4) ute** med R12i og eigen caster (mountpoint TH). | Alt over føreset cm-nøyaktigheit. Er berre testa som DGPS innandørs. | Ikkje stadfest |

## Avklart

(ingenting enno)
