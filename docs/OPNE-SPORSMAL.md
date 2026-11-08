# Opne spørsmål – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

Ting som manglar før hellingskorreksjonen kan setjast i drift. **Spør eigaren (Hans Petter) om dei** når arbeidet
held fram, og flytt svaret til «Avklart» med dato.

Oppretta 5. november 2026. Oppdatert 6. november 2026 med svar frå Norman Hole og funn i OneVision-data frå
Kagholvegen (29.11.2022), og 9. november 2026 med testpakka frå Norman 8.11.

## Opne

| # | Spørsmål | Kvifor det trengst | Inntil vidare |
|---|---|---|---|
| 3 | **Ekstra IMU på ramma, ja eller nei.** R12i gir ikkje ut stamp/krenging som tal. *Førebels: tilrådd. Kva modell og kva NMEA-melding han skal sende, står att.* | Utan ekstra IMU blir berre masta retta, ikkje djupnfeilen (opptil ca. 32 cm på 2,5 m ved 5° helling). | Berre masta (R12i rettar sjølv) |
| 6 | **Held R12i-IMU-en justeringa** på ei vogn som blir trekt (støyt, snuing)? | Om R12i kan rette masta åleine i felt. | Ikkje testa |
| 8 | **Rette sjølve radarbiletet (djupnesnitt) for hellinga.** Norman: «Det er dette som er interessant.» Det går i rådataform: IQMaps-mappa har spor (.data) og posisjon med tid per sweep (.path). Plan i [DJUPNESNITT.md](DJUPNESNITT.md). | Då blir heile biletet retta cm for cm, ikkje berre objekta. | Berre objekt. Ventar på `.data` (delt i bitar under 5 MB) for å stadfeste formatet. |
| 11 | **Mastehøgda: 1,80 eller 1,86 m?** Norman målte ca. 1,86 m på verkstadgolvet (gjentatt 8.11, «trur eg»). Han spurde om stanghøgda bør vere 1,6 for mindre avvik: nei – talet må vere den verkelege høgda; berre ei fysisk kortare mast gir mindre feil. OneVision (`Stream C.xml`) har GPS-høgd **1.9**. Same tal må stå tre stader: stanghøgd i R12i, «Mastehøgd» i Geoscan og z i `Stream C.xml`. | Ulik høgd gir feil høgd på bakken, og med R12i-tilt feil plassering i sidebakke. Ikkje set lågare (t.d. 1,6) for å «minske avvik» – det gir feil. | 1,80 i Geoscan, 1.9 i OneVision |
| 12 | **Forteiknet på y i OneVision.** GPS-en står 0,6 m til venstre (Norman 6.11). Er +y i OneVision venstre eller høgre? 8.11: Norman skriv at spora i OneVision «virka nesten som dei var snudd». `Swath_NNNN.pos` lagrar berre antenneposisjonen, så forteiknet går ikkje fram av filene. | Feil forteikn gir spor som byter side når ein snur (ca. 1,2 m). | Test: køyr over eit kjent røyr begge vegar med y = 0.6, og deretter −0.6. Geoscan skriv `Stream C.xml` frå 0.9.18 og held forteiknet som står |
| 15 | **Held R12i fram med `$INGGA` når Trimble Access blir lukka?** 8.11 kom `$INGGA` ut på USB medan IMU-en var slått på frå demoutgåva av Access (sjå avklart 16). Felttesten 7.11 gav `$GNGGA` (antenne, IMU ikkje i bruk). Norman: «Access reknar ut når det blir brukt, men streaming ut elles trur eg er i fasepunktet til antenna.» Krev IMU-justering utan Access? Gir `$INGGA` spissen eller antenna? | Utan IMU-retta posisjon blir masta ikkje retta for helling: ca. 16 cm feil per 5° med 1,8 m mast. | Ekstra hellingsmålar på ramma (punkt 3) er den sikre vegen |
| 9 | **Kompasset i georadaren.** Norman: radaren har ein sensor som viser mot nord, og kompasset går inn i skannedataa. 7.11: «trur den blir lagra i OneVision». Kvar ligg kursen i filene (.scan, .data eller .index), og er han magnetisk eller sann nord? | Kursen trengst for å vende hellinga rett når kvart sweep skal rettast (punkt 8). Kompass kan òg bli forstyrra av stål. | Kurs frå GNSS-sporet |

## Planlagt og moglege opsjonar

| # | Kva | Status |
|---|---|---|
| P1 | **0.9.19: bakgrunnsfiler i kartet** (ønske frå Norman 8.11). DXF og KOF blir viste på Status og Resultat, med eit val for kva filer og lag som skal visast. DWG må lagrast som DXF. IFC kan kome seinare. Test helst med ei ekte fil frå Norman (t.d. `…M.dxf` på skrivebordet hans). | Neste versjon |
| P2 | **Opsjon: automatisk opplasting av testpakkar til eit privat GitHub-repo.** Geoscan lastar opp pakka (zip og eit kort samandrag) til t.d. `Snowman6230/geoscan-innsending` under `innsendt/<maskin>/<dato_tid>/`, med knappen «Send til utviklar» og eventuelt «Send automatisk når økta blir avslutta». Nøkkelen (fine-grained token, berre «Contents: write» på det eine repoet) blir lagra berre lokalt på PC-en, som NTRIP-passordet. Utviklaren (Claude) hentar og analyserer pakkane på førespurnad, eller med ei planlagd oppgåve kvar morgon. Pakkane må **ikkje** inn i hovudrepoet, som er ope, fordi dei har GPS-loggar frå arbeidsstadene. Store radardata (`.scan`, ca. 16 MB kvar) bør vere valfrie; GitHub tek filer opp til 100 MB. Det går ikkje an å sende rett inn i ein Claude-chat. | Mogleg. Krev at Norman er med på det, og at Hans Petter opprettar repoet og nøkkelen |

## Avklart

| # | Spørsmål | Svar | Dato / kjelde |
|---|---|---|---|
| 1 | Mastehøgda | **1,8 m** (7.11: Norman målte ca. 1,86 m på golvet – sjå opne punkt 11). Same som i OneVision-målinga 2022. Malen `Stream C.xml` har «1,6» med desimalkomma, som er ein feil. Standard `spakarm.opp` er no 1,80. Set same verdi som stanghøgd i R12i når `mottakar_kompenserer` er på. | 6.11.2026, Norman (målt) |
| 2 | Referansepunktet til OneVision og forskyving | GPS-mottakaren står **0,6 m til venstre** sett bakfrå i skanneretninga. OneVision har origo i enkodaren og flyttar sjølv posisjonen frå GPS-antenna til antennene (V24 på x = 0,38, H10 på x = 0,57). **`utgang = rett_antenne` er rett**, og antenneoppsettet i OneVision står urørt. Standard `spakarm.hogre` er no −0,60, slik at hellingsrettinga reknar med rett geometri. OneVision-malen har y = 0,42 og må rettast til 0,6 m. | 6.11.2026, Norman (målt), `Stream C.xml` |
| 4 | Eksportfil med objekt | Det finst inga eksportfil. OneVision lagrar objekta inne i målefila (`Survey_….svy`, `<Targets>`, base64). Formatet er tolka (81 objekt i Kagholvegen: linjer «L…» og punkt «T…», med E, N i UTM32 og djupn) og blir lese av `pc/svy_objekt.py`. Resultat-fana og `korriger_objekt.py` tek `.svy` direkte. | 6.11.2026, Kagholvegen-.svy |
| 5 | Brukar OneVision kurs frå NMEA (HDT)? | **Nei.** OneVision les berre GGA (StringFilter GGA, COM32, 9600 8N1). Georadaren har eigen nordsensor (kompass) som går inn i skannedataa (sjå punkt 9). Geoscan treng ikkje sende kurs. | 6.11.2026, .svy og Norman |
| 7 | RTK FIX (4) ute med R12i og eigen caster (TH) | **Ja.** Felttest 7.11: RTK FIX på under eitt minutt, NTRIP tilkopla (gpsbase), 92 % FIX / 8 % FLOAT over ein time. RTCM gjekk over USB (COM3). OneVision: «GNSS connection OK – RTK Fix» gjennom com0com (COM24). | 7.11.2026, felttest Norman |
| 14 | Kvifor kom spora i OneVision feil («som om dei var snudde»)? | **Feil i Geoscan, retta i 0.9.4.** Med R12i-tilt og `rett_antenne` vart kvar posisjon flytta 0,60 m til venstre for køyreretninga (stadfest på alle 3 887 punkt i loggen). Feilen byter side når ein snur, så spor køyrde motsett veg låg ca. 1,2 m frå kvarandre. Rådataa frå testen gir ingen sideflytting med 0.9.4. | 7.11.2026, logg frå felttest |
| 13 | Rate frå R12i | **10 Hz.** GGA og GST på 10 Hz på USB-porten (webgrensesnittet til R12i, I/O Configuration). Rådata 8.11 kl. 23:25: ca. 10 GGA i sekundet. | 8.11.2026, bilete og logg frå Norman |
| 16 | Kan R12i sende `$INGGA` (IMU) ut på USB? | **Ja, når IMU-en er slått på frå Trimble Access** (demolisens på Panasonic-PC-en, Access over Bluetooth). Rådata 8.11 kl. 22:57–23:37 har `$INGGA` og `$INGST`. Testen var innandørs med berre DGPS, så nøyaktigheita er ikkje vurdert. Geoscan har val av GPS-oppsett «R12i med Trimble Access» frå 0.9.18. | 8.11.2026, rådata frå Norman |
| 17 | Kan GPS-forskyvinga endrast i OneVision? | **Nei**, berre i `Stream C.xml` ved OneVision.exe (Program Files). Geoscan skriv fila frå 0.9.18 (Innstillingar → Vogn og mast), med kopi og administratorløyve. | 8.11.2026, Norman |
| 18 | Skannebreidda til Stream C | **96 cm.** Objekt tvers over beltet i `.svy` (7.11) går ±0,479 m, og IDS oppgir 96 cm. (0.9.17 viste 77 cm frå målinga i 2022 – feil, retta i 0.9.18.) | 8.11.2026, `.svy` frå Norman |
| 10 | Treng radaren ein eigen PPS-kabel frå GNSS? | **Nei.** Posisjoneringssystemet i OneVision/IQMaps er «PPS» med `Device="Internal"`. Radaren går over LAN-kabel (med overgang til USB) til PC-en, og GNSS kjem som NMEA på ein COM-port. GGA-tida må likevel gå uendra gjennom Geoscan. | 6.11.2026, .svy, IQMaps og Norman |

## Kjelder

- 5.11.2026: eit KI-samandrag som Hans Petter delte (ikkje frå IDS si dokumentasjon).
- 6.11.2026: svar frå Norman Hole, og OneVision- og IQMaps-filer frå Kagholvegen 29.11.2022 (loggar, `Stream C.xml`,
  `.svy`, `Swath001.nmea`, C-scan, LESMEG.txt). Analysen ligg i Claude-prosjektet «Snowman 3dscan».
