# Vegkart – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

Skrive 9. november 2026, då versjon 0.9.18 var ute. Dette er ein plan og ei idéliste, ikkje lovnader. Punkta
etter 1.0 er moglegheiter som bør vurderast mot kva Norman og andre kundar faktisk treng.

## Kvar vi står (0.9.18)

Kjeda R12i → Snowman Geoscan → com0com → OneVision verkar, med NTRIP, RTK FIX, 10 Hz, QH/QV, live-kart med
skannestripe, val av GPS-oppsett, skriving av `Stream C.xml` og Resultat med objekt frå `.svy`, tverrsnitt og
grav nedover. Det som manglar mest, er **prov frå felt**: at posisjonane i OneVision stemmer når ein køyrer
fram og tilbake.

## Versjon 1.0 – krav

1.0 er første versjon Norman kan bruke i vanleg arbeid utan hjelp, og der det er prova at posisjonane stemmer.

**Prova i felt (med logg):**
1. **Rett plassering i OneVision.** Kjent røyr skanna fram og tilbake med RTK FIX: treffa ligg oppå kvarandre
   (innan ca. 5 cm). Avgjer forteiknet på sideforskyvinga og stadfestar `Stream C.xml`.
2. **Rett høgd.** Mastehøgda målt nøyaktig og lik i Geoscan, OneVision og Access. Kontrollert mot eit fastmerke
   (t.d. kumlokk med kjend høgd).
3. **Ei heil arbeidsøkt utan stopp.** Minst ein time med 10 Hz, NTRIP, OneVision og Geoscan saman. Ingen kasta
   linjer, og Geoscan koplar til att av seg sjølv når USB fell ut.
4. **Resultat med ekte data.** `.svy` blir lesen, objekta kjem rett på kartet, og eksporten (DXF, CSV, GeoJSON)
   kan opnast hos landmålar eller i GRED/IQMaps.

**Avgjort:**

5. **Helling:** IMU i R12i (krev Trimble Access) eller eigen hellingsmålar (SBG Ellipse-A, eller billeg
   WitMotion/Rion etter test).
6. **Lisens og repo:** privat repo med nøkkel, eller ope.

**Ferdig i programmet:**

7. Bakgrunnsfiler (DXF og KOF) i kartet.
8. Status-sida utan rulling: kart og info på same skjerm.
9. Brukarrettleiing og ei éi-sides «kom i gang» med skjermbilete frå den versjonen Norman har.
10. Testsjekklista oppdatert til 1.0, og alle punkt godkjende éin gong.

## Fram mot 1.0

| Versjon | Innhald |
|---|---|
| 0.9.19 ✓ | Bakgrunnsfiler DXF og KOF, med val av kva filer og lag som skal visast (P1), og PJK/GGK frå Trimble Access under Fix med avvik mot Geoscan (P1b) |
| 0.9.20 ✓ | Rett bakkehøgd: mastehøgd til undersida av hurtigfestet + 0,179 m til fasesenteret. z i Stream C.xml = 1,99. Åtvaring ved feil GPS-kjelde |
| 0.9.21 ✓ | Access/IMU: punktet går urørt, spissen 0,09 over bakken, hoppet ved tap av IMU blir målt. Kvalitetsvakt (raud stripe, lyd, Windows-varsel). Stream C-boks med x/y/z og skisse. Objekt frå Exports. Bakgrunn: farge, Z og avvik mot innmålt |
| 0.9.22 ✓ | Ikonet på skrivebordet blir laga på nytt etter oppdatering, og knapp for det under Innstillingar |
| 0.9.23 ✓ | Tap av IMU: R12i held fram med spissen (målt 11.11). Tydeleg start/stopp for sporet, strengare auto-pause av stripa |
| 0.9.24 ✓ | Gul aktivitetsstolpe for korreksjonane (alder frå GGA, som Xsite). Kabel eller Bluetooth i «Finn utstyr». Tydeleg melding når statussida mistar kontakten med Geoscan |
| 0.9.25 | Status utan rulling (oppsett C: infokolonne + kart i full høgd, A som reserve), app-modus i nettlesaren. Lesar for hellingsmålaren som blir vald (WitMotion/Rion), eller ingenting om det blir SBG. Kalibrering av x/y mot innmålt røyr (grusbana 11.11 og 12.11) |
| 0.9.2x | Rettingar etter felttesten med røyret. Eventuelt opplasting av testpakkar til privat repo (P2) |
| **1.0** | Når krava over er oppfylte |

## Etter 1.0 – versjon 1.x (vidare på same grunnmur)

- **1.1 – Djupnesnitt.** Rette sjølve radarbiletet (kvar sweep) for helling, ikkje berre objekta.
  Krev `.data`/`.scan`-formatet stadfest (DJUPNESNITT.md).
- **1.2 – Dekning.** Kart over kva som er skanna: glipper mellom stripene, prosent dekt av eit område, og
  forslag til neste stripe.
- **1.3 – Meir på kartet.** IFC/BIM-modellar, utsetting (navigere til eit punkt eller langs ei line),
  samanlikning av to målingar av same område.
- **1.4 – Rapport.** Ferdig rapport per oppdrag (kart, objekt med djupn og høgd, nøyaktigheit, kven, når) som PDF,
  klar til byggherre eller kommune.

## Versjon 2 – eigen posisjonsfusjon og live objekt

Mål: Geoscan blir uavhengig av Trimble Access og veit sjølv kvar kvar sweep ligg.

- **Eigen fusjon av GNSS, IMU og enkodar.** Stream C har enkodar på hjulet. Saman med GNSS og ein hellingsmålar
  kan Geoscan rekne posisjon og helling for kvar sweep, òg i korte GNSS-utfall (under tre, inntil vegg).
  Rygging kan skiljast frå køyring, og stripa blir rett i svingar.
- **Live objekt på kartet.** Geoscan les objekta i `.svy` medan OneVision lagrar, og viser dei retta på
  live-kartet straks operatøren merkjer dei.
- **Kurs med to antenner** (eller frå IMU) i staden for frå sporet, så kursen er rett òg når vogna står.
- **Fleire mottakarar.** Leica, Topcon, Septentrio og billeg RTK (u-blox F9P) i tillegg til R12i, gjennom same
  NMEA-grensesnitt.
- **Prosjekt og økter.** Eit oppdrag har namn, område, bakgrunnsfiler, målingar og rapport samla, og kan
  opnast att.

## Versjon 3 – plattform og samspel med andre system

Mål: Resultata går rett inn i arbeidet til dei som skal grave, prosjektere eller forvalte.

- **Fleire georadarar.** IDS Stream DP/UP, Leica DS2000 og andre (GSSI, MALÅ), der formatet kan lesast.
- **Maskinstyring.** Eksport til gravemaskiner med maskinstyring (LandXML/DXF/KOF til t.d. Novatron Xsite,
  Leica iCON, Trimble Earthworks), så maskinføraren ser røyr og kablar i skjermen sin. Varsel når skuffa
  nærmar seg eit kjent objekt.
- **Ledningsdata til forvaltninga.** Eksport i formata kommunane og leidningseigarane brukar for innmålte
  leidningar (t.d. SOSI-ledning). Krev at det blir avklart kva format og nøyaktigheitskrav som gjeld.
- **Deling i skya.** Målingar og rapportar blir lasta opp og delte med byggherre eller kommune via lenkje,
  med tilgangsstyring.
- **Fleire brukarar og PC-ar.** Same prosjekt på fleire einingar. Statussida på mobil for formannen.

## Versjon 4 – automatikk og nye bruksområde

Mål: Mindre manuelt arbeid, og teknologien brukt der det i dag er vanskeleg.

- **Maskinlæring på radarbileta.** Finne og klassifisere røyr og kablar automatisk (hyperblar i B-scan), med kor
  sikker tolkinga er. Rekne farten i grunnen frå forma på hyperblane, så djupna blir rett utan å gjette 0,1 m/ns.
- **Utvida røyndom (AR).** Vise røyr og kablar i kamerabiletet på nettbrett eller telefon på staden.
- **Sjølvkøyrande eller fjernstyrt vogn** som følgjer planlagde striper og dekkjer eit område utan glipper.
- **Endringar over tid.** Samanlikne målingar av same område for å sjå setning, ras, vatn eller nye leidningar.
- **Digital tvilling av grunnen.** Alle målingar i eit område samla til ein 3D-modell som kan brukast i BIM.
- **Andre bruksområde for same grunnmur.** Til dømes snø- og isdjupn med georadar på tråkkemaskin eller
  skuter. NB: SNOWMAN Snødjupne er eit eige prosjekt. Kode blir kopiert med opphav notert, aldri kopla saman
  (CLAUDE.md).

## Forretning (gjeld alle versjonar)

- Geoscan er laga for Norman Hole, Hole Anlegg AS. Om programmet skal seljast til andre, må lisens, installasjon,
  brukarstøtte og oppdatering vere på plass (privat repo, lisensnøkkel, installasjonsprogram).
- Kvar ny radar, mottakar eller eksport bør ha ein kunde som treng han, og ekte testdata før han blir laga.

## Avhengigheiter og risiko

- **Felttest med kjent røyr** avgjer om 1.0 er nær. Ingenting i versjon 2–4 gir meining før posisjonane er prova.
- **OneVision-formata er ikkje dokumenterte av IDS.** Djupnesnitt og live objekt byggjer på eiga tolking av `.svy`,
  `.scan` og `.data`, og kan bli broten av ein ny OneVision-versjon.
- **Trimble Access** trengst for IMU i R12i. Eigen hellingsmålar fjernar den avhengigheita.
