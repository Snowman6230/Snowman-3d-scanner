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
| 12 | **Forteiknet på y i OneVision.** y = 0,42 er avklart (sjå avklart 20), men ikkje om +y er venstre. IDS-malen for GPS-støtta bak til venstre har +0,42, så truleg er + venstre. `Swath_NNNN.pos` lagrar berre antenneposisjonen, så forteiknet går ikkje fram av filene. | Feil forteikn gir spor som byter side når ein snur (ca. 0,84 m). | Test: køyr langs eit kjent røyr begge vegar med 0.13;0.42;0.09 |
| 22 | **Kva sender R12i når IMU-en fell ut midt i ei køyring?** Antenna (som med IMU av 9.11 kl. 08:52: `$GNGGA` 1,98 m over det Access viste), eller spissen med stanghøgda trekt frå (Norman 9.11)? Byta i rådata 8.–9.11 var innandørs/DGPS og seier ingenting. | Høgda i OneVision blir 2 m feil om Geoscan gjettar feil. Frå 0.9.21 måler Geoscan hoppet ved bytet og rettar berre når det trengst. | Test ute med RTK: slå av IMU i Access medan Geoscan går, og sjå om høgda hoppar ca. 2 m |
| 15 | **Held R12i fram med `$INGGA` når Trimble Access blir lukka?** 8.11 kom `$INGGA` ut på USB medan IMU-en var slått på frå demoutgåva av Access (sjå avklart 16). Felttesten 7.11 gav `$GNGGA` (antenne, IMU ikkje i bruk). Norman: «Access reknar ut når det blir brukt, men streaming ut elles trur eg er i fasepunktet til antenna.» Krev IMU-justering utan Access? Gir `$INGGA` spissen eller antenna? | Utan IMU-retta posisjon blir masta ikkje retta for helling: ca. 16 cm feil per 5° med 1,8 m mast. | Ekstra hellingsmålar på ramma (punkt 3) er den sikre vegen |
| 9 | **Kompasset i georadaren.** Norman: radaren har ein sensor som viser mot nord, og kompasset går inn i skannedataa. 7.11: «trur den blir lagra i OneVision». Kvar ligg kursen i filene (.scan, .data eller .index), og er han magnetisk eller sann nord? | Kursen trengst for å vende hellinga rett når kvart sweep skal rettast (punkt 8). Kompass kan òg bli forstyrra av stål. | Kurs frå GNSS-sporet |

## Planlagt og moglege opsjonar

Heile planen fram mot 1.0 og vidare (versjon 2–4) står i [VEGKART.md](VEGKART.md).

| # | Kva | Status |
|---|---|---|
| P1 | **0.9.19: bakgrunnsfiler i kartet** (ønske frå Norman 8.11). DXF og KOF blir viste på Status og Resultat, med eit val for kva filer og lag som skal visast. DWG må lagrast som DXF. IFC kan kome seinare. Test helst med ei ekte fil frå Norman (t.d. `…M.dxf` på skrivebordet hans). | **Laga i 0.9.19** |
| P1b | **0.9.19: PJK og GGK frå Trimble Access under Fix** (ønske frå Norman 9.11). Access har berre fire NMEA-plassar (GGA, GGK, GLL, PJK) og ingen GST, så QH/QV kan mangle. Geoscan les `$PTNL,PJK` (koordinatane i Access-jobben, N/E/høgd) og `$PTNL,GGK` (DOP, ellipsoidehøgd) og viser dei under Fix, med avvik mot Geoscan sine UTM/NN2000-tal. Utan GST: tydeleg tekst og HDOP. Merk: `$INGST` kom med Access kopla til 8.11, så GST frå webgrensesnittet til R12i kan fungere samtidig – Norman sjekkar. | **Laga i 0.9.19** |
| P2 | **Opsjon: automatisk opplasting av testpakkar til eit privat GitHub-repo.** Geoscan lastar opp pakka (zip og eit kort samandrag) til t.d. `Snowman6230/geoscan-innsending` under `innsendt/<maskin>/<dato_tid>/`, med knappen «Send til utviklar» og eventuelt «Send automatisk når økta blir avslutta». Nøkkelen (fine-grained token, berre «Contents: write» på det eine repoet) blir lagra berre lokalt på PC-en, som NTRIP-passordet. Utviklaren (Claude) hentar og analyserer pakkane på førespurnad, eller med ei planlagd oppgåve kvar morgon. Pakkane må **ikkje** inn i hovudrepoet, som er ope, fordi dei har GPS-loggar frå arbeidsstadene. Store radardata (`.scan`, ca. 16 MB kvar) bør vere valfrie; GitHub tek filer opp til 100 MB. Det går ikkje an å sende rett inn i ein Claude-chat. | Mogleg. Krev at Norman er med på det, og at Hans Petter opprettar repoet og nøkkelen |

## Avklart

| # | Spørsmål | Svar | Dato / kjelde |
|---|---|---|---|
| 1 | Mastehøgda | **1,8 m** (9.11: 1,808 m til undersida av hurtigfestet – sjå avklart 19). Same som i OneVision-målinga 2022. Malen `Stream C.xml` har «1,6» med desimalkomma, som er ein feil. Standard `spakarm.opp` er no 1,80. Set same verdi som stanghøgd i R12i når `mottakar_kompenserer` er på. | 6.11.2026, Norman (målt) |
| 2 | Referansepunktet til OneVision og forskyving | GPS-mottakaren står **0,6 m til venstre** sett bakfrå i skanneretninga. OneVision har origo i enkodaren og flyttar sjølv posisjonen frå GPS-antenna til antennene (V24 på x = 0,38, H10 på x = 0,57). **`utgang = rett_antenne` er rett**, og antenneoppsettet i OneVision står urørt. Standard `spakarm.hogre` er no −0,60, slik at hellingsrettinga reknar med rett geometri. OneVision-malen har y = 0,42 og må rettast til 0,6 m. | 6.11.2026, Norman (målt), `Stream C.xml` |
| 4 | Eksportfil med objekt | Det finst inga eksportfil. OneVision lagrar objekta inne i målefila (`Survey_….svy`, `<Targets>`, base64). Formatet er tolka (81 objekt i Kagholvegen: linjer «L…» og punkt «T…», med E, N i UTM32 og djupn) og blir lese av `pc/svy_objekt.py`. Resultat-fana og `korriger_objekt.py` tek `.svy` direkte. | 6.11.2026, Kagholvegen-.svy |
| 5 | Brukar OneVision kurs frå NMEA (HDT)? | **Nei.** OneVision les berre GGA (StringFilter GGA, COM32, 9600 8N1). Georadaren har eigen nordsensor (kompass) som går inn i skannedataa (sjå punkt 9). Geoscan treng ikkje sende kurs. | 6.11.2026, .svy og Norman |
| 7 | RTK FIX (4) ute med R12i og eigen caster (TH) | **Ja.** Felttest 7.11: RTK FIX på under eitt minutt, NTRIP tilkopla (gpsbase), 92 % FIX / 8 % FLOAT over ein time. RTCM gjekk over USB (COM3). OneVision: «GNSS connection OK – RTK Fix» gjennom com0com (COM24). | 7.11.2026, felttest Norman |
| 14 | Kvifor kom spora i OneVision feil («som om dei var snudde»)? | **Feil i Geoscan, retta i 0.9.4.** Med R12i-tilt og `rett_antenne` vart kvar posisjon flytta 0,60 m til venstre for køyreretninga (stadfest på alle 3 887 punkt i loggen). Feilen byter side når ein snur, så spor køyrde motsett veg låg ca. 1,2 m frå kvarandre. Rådataa frå testen gir ingen sideflytting med 0.9.4. | 7.11.2026, logg frå felttest |
| 13 | Rate frå R12i | **10 Hz.** GGA og GST på 10 Hz på USB-porten (webgrensesnittet til R12i, I/O Configuration). Rådata 8.11 kl. 23:25: ca. 10 GGA i sekundet. | 8.11.2026, bilete og logg frå Norman |
| 16 | Kan R12i sende `$INGGA` (IMU) ut på USB? | **Ja, når IMU-en er slått på frå Trimble Access** (demolisens på Panasonic-PC-en, Access over Bluetooth). Rådata 8.11 kl. 22:57–23:37 har `$INGGA` og `$INGST`. Testen var innandørs med berre DGPS, så nøyaktigheita er ikkje vurdert. Geoscan har val av GPS-oppsett «R12i med Trimble Access» frå 0.9.18. | 8.11.2026, rådata frå Norman |
| 17 | Kan GPS-forskyvinga endrast i OneVision? | **Nei**, berre i `Stream C.xml` ved OneVision.exe (Program Files). Geoscan skriv fila frå 0.9.18 (Innstillingar → Vogn og mast), med kopi og administratorløyve. | 8.11.2026, Norman |
| 19 | Mastehøgda, og kva ho er målt til (opne punkt 11) | **1,808 m frå spissen av stonga til undersida av hurtigfestet** (9.11 kveld: spissen står i støtta 0,09 m over bakken, sjå avklart 20) på R12i, same som stanghøgda i Trimble Access («Målt til: Undersiden av hurtig feste»). Fasesenteret i antenna ligg **0,179 m** over (Access: 1,898 m gir APC 2,077 m), altså **1,987 m** over bakken. GGA frå R12i er fasesenteret. Geoscan legg til 0,179 m frå 0.9.20 (før kom bakken 0,18 m for høgt). z i `Stream C.xml` var tenkt **1.99** når Geoscan sender antenna. Frå 0.9.21 sender Geoscan spissen urørt med IMU, og z = 0,09 (sjå avklart 20). Kontroll 9.11 kl. 08:52: Geoscan og Access samde på 1 cm i nord, aust og antennehøgd. | 9.11.2026, skjermbilete frå Norman |
| 20 | Kvar spissen av stonga står, og xyz i `Stream C.xml` | **Spissen står i GPS-støtta på ramma, 0,09 m over bakken** (Norman 9.11). Det er 0-punktet. R12i med IMU sender spissen (`$INGGA`), og Geoscan skal sende han urørt (Norman 9.11). **x = 0,13** fram frå enkoderen i det venstre bakhjulet (origo i OneVision), **y = 0,42** sidevegs til midten av radaren (Norman målte 9.11 – same som IDS-malen for støtta bak til venstre). z = **0,09**. Stream C-manualen (MN/2016/011): antenneboks 120 × 57 × 20 cm, enkoder i venstre bakhjul, GPS-støtta bak til venstre. Laga i 0.9.21. | 9.11.2026, Norman og IDS-manualane |
| 21 | Kvar ligg objekta når `.svy` er tom? | OneVision-manualen (MNG/2016/0018): «Target Export» lagar DXF, ESRI Shapefile, KML og IDS Geomap i mappa **Exports** i målemappa. Survey_2026.11.09_006 hadde tom `<Targets>`. Geoscan les Exports frå 0.9.21. Formatet frå OneVision er ikkje sett enno. | 9.11.2026, manualane |
| 18 | Skannebreidda til Stream C | **96 cm.** Objekt tvers over beltet i `.svy` (7.11) går ±0,479 m, og IDS oppgir 96 cm. (0.9.17 viste 77 cm frå målinga i 2022 – feil, retta i 0.9.18.) | 8.11.2026, `.svy` frå Norman |
| 10 | Treng radaren ein eigen PPS-kabel frå GNSS? | **Nei.** Posisjoneringssystemet i OneVision/IQMaps er «PPS» med `Device="Internal"`. Radaren går over LAN-kabel (med overgang til USB) til PC-en, og GNSS kjem som NMEA på ein COM-port. GGA-tida må likevel gå uendra gjennom Geoscan. | 6.11.2026, .svy, IQMaps og Norman |

## Kjelder

- 5.11.2026: eit KI-samandrag som Hans Petter delte (ikkje frå IDS si dokumentasjon).
- 6.11.2026: svar frå Norman Hole, og OneVision- og IQMaps-filer frå Kagholvegen 29.11.2022 (loggar, `Stream C.xml`,
  `.svy`, `Swath001.nmea`, C-scan, LESMEG.txt). Analysen ligg i Claude-prosjektet «Snowman 3dscan».
