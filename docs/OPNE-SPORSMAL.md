# Opne spørsmål – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

Ting som manglar før hellingskorreksjonen kan setjast i drift. **Spør eigaren (Hans Petter) om dei** når arbeidet
held fram, og flytt svaret til «Avklart» med dato.

Oppretta 5. november 2026. Oppdatert 6. november 2026 med svar frå Norman Hole og funn i OneVision-data frå
Kagholvegen (29.11.2022).

## Opne

| # | Spørsmål | Kvifor det trengst | Inntil vidare |
|---|---|---|---|
| 3 | **Ekstra IMU på ramma, ja eller nei.** R12i gir ikkje ut stamp/krenging som tal. *Førebels: tilrådd. Kva modell og kva NMEA-melding han skal sende, står att.* | Utan ekstra IMU blir berre masta retta, ikkje djupnfeilen (opptil ca. 32 cm på 2,5 m ved 5° helling). | Berre masta (R12i rettar sjølv) |
| 6 | **Held R12i-IMU-en justeringa** på ei vogn som blir trekt (støyt, snuing)? | Om R12i kan rette masta åleine i felt. | Ikkje testa |
| 7 | **RTK FIX (4) ute** med R12i og eigen caster (mountpoint TH). | Alt over føreset cm-nøyaktigheit. Er berre testa som DGPS innandørs. Kagholvegen 2022 hadde RTK fix heile vegen, men med anna GPS-utstyr (Norman 6.11). | Ikkje stadfest |
| 8 | **Rette sjølve radarbiletet (djupnesnitt) for hellinga.** Norman: «Det er dette som er interessant.» Det går i rådataform: IQMaps-mappa har spor (.data) og posisjon med tid per sweep (.path). Plan i [DJUPNESNITT.md](DJUPNESNITT.md). | Då blir heile biletet retta cm for cm, ikkje berre objekta. | Berre objekt. Ventar på `.data` (delt i bitar under 5 MB) for å stadfeste formatet. |
| 9 | **Kompasset i georadaren.** Norman: radaren har ein sensor som viser mot nord, og kompasset går inn i skannedataa. Kvar ligg kursen i filene (.scan, .data eller .index), og er han magnetisk eller sann nord? | Kursen trengst for å vende hellinga rett når kvart sweep skal rettast (punkt 8). Kompass kan òg bli forstyrra av stål. | Kurs frå GNSS-sporet |

## Avklart

| # | Spørsmål | Svar | Dato / kjelde |
|---|---|---|---|
| 1 | Mastehøgda | **1,8 m.** Same som i OneVision-målinga 2022. Malen `Stream C.xml` har «1,6» med desimalkomma, som er ein feil. Standard `spakarm.opp` er no 1,80. Set same verdi som stanghøgd i R12i når `mottakar_kompenserer` er på. | 6.11.2026, Norman (målt) |
| 2 | Referansepunktet til OneVision og forskyving | GPS-mottakaren står **0,6 m til venstre** sett bakfrå i skanneretninga. OneVision har origo i enkodaren og flyttar sjølv posisjonen frå GPS-antenna til antennene (V24 på x = 0,38, H10 på x = 0,57). **`utgang = rett_antenne` er rett**, og antenneoppsettet i OneVision står urørt. Standard `spakarm.hogre` er no −0,60, slik at hellingsrettinga reknar med rett geometri. OneVision-malen har y = 0,42 og må rettast til 0,6 m. | 6.11.2026, Norman (målt), `Stream C.xml` |
| 4 | Eksportfil med objekt | Det finst inga eksportfil. OneVision lagrar objekta inne i målefila (`Survey_….svy`, `<Targets>`, base64). Formatet er tolka (81 objekt i Kagholvegen: linjer «L…» og punkt «T…», med E, N i UTM32 og djupn) og blir lese av `pc/svy_objekt.py`. Resultat-fana og `korriger_objekt.py` tek `.svy` direkte. | 6.11.2026, Kagholvegen-.svy |
| 5 | Brukar OneVision kurs frå NMEA (HDT)? | **Nei.** OneVision les berre GGA (StringFilter GGA, COM32, 9600 8N1). Georadaren har eigen nordsensor (kompass) som går inn i skannedataa (sjå punkt 9). Geoscan treng ikkje sende kurs. | 6.11.2026, .svy og Norman |
| 10 | Treng radaren ein eigen PPS-kabel frå GNSS? | **Nei.** Posisjoneringssystemet i OneVision/IQMaps er «PPS» med `Device="Internal"`. Radaren går over LAN-kabel (med overgang til USB) til PC-en, og GNSS kjem som NMEA på ein COM-port. GGA-tida må likevel gå uendra gjennom Geoscan. | 6.11.2026, .svy, IQMaps og Norman |

## Kjelder

- 5.11.2026: eit KI-samandrag som Hans Petter delte (ikkje frå IDS si dokumentasjon).
- 6.11.2026: svar frå Norman Hole, og OneVision- og IQMaps-filer frå Kagholvegen 29.11.2022 (loggar, `Stream C.xml`,
  `.svy`, `Swath001.nmea`, C-scan, LESMEG.txt). Analysen ligg i Claude-prosjektet «Snowman 3dscan».
