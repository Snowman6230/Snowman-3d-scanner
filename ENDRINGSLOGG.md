# Endringslogg – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

## 0.7.1 – 5. november 2026
- Repoet blir **offentleg i testperioden** og lukka seinare. Oppdateringa fungerer utan nøkkel medan det er
  ope. Er repoet privat og nøkkel manglar, viser programmet ei tydeleg åtvaring med lenke til Innstillingar.
- Programmet ser etter ny versjon ved oppstart og så kvar 3. time.
- LICENSE: alle rettar reserverte. At koden er synleg, gir ingen rett til bruk. Lista over tredjepartslisensar
  (Leaflet, Kartverket) er med.

## 0.7.0 – 5. november 2026
- **Testsjekkliste** under «Send inn» med dei fire stega frå testplanen (16 punkt). Kvart punkt har status og
  kommentar. Ho blir lagra med ein gong (innsendt/sjekkliste.json), og pakka får SJEKKLISTE.txt og
  sjekkliste.json.
- **Send til hansps@alpindata.no:** e-postknapp med ferdig emne og tekst, og knappen «Opne mappa med pakka», så
  zip-fila kan dragast inn i e-posten. Adressa ligg i opphav.KONTAKT_EPOST og står i SVAR.txt.
- **Meldingar frå utviklaren** (pc/meldingar.json, kjem med oppdateringa):
  - ulesne meldingar står øvst i programmet til operatøren trykker «OK, lese»
  - svar ved punkta i sjekklista, med «prøv på nytt»
  - «Ny versjon»-lina viser tittelen på den nyaste meldinga
- Demo: knappen «Prøv med eksempelfil (DEMO)» under Resultat, med ei oppdikta eksportfil som passar til
  simulatoren.

## 0.6.1 – 5. november 2026
- Produsentnamnet er no «Alpindata HP Brunstad Sørensen» (utan «v/») overalt: logo, oppstartbilete, rapportar,
  eksportfiler, nettlesar og dokument. Signaturen (SNWGEO-…) er uendra, så eldre filer blir framleis kjende att.

## 0.6.0 – 5. november 2026
- **Logo:** same uttrykk som SNOWMAN Snødjupne (natthimmel, fjelltoppar, snø), men med georadarvogna, GNSS-mast,
  radarbølgjer og eit nedgrave røyr. Kjelda er pc/ikon/lag-ikon.py. Ho lagar SVG, PNG, ICO og oppstartbiletet.
- **Oppstartbilete** når programmet startar (kan slåast av med vis_oppstartlogo). Ikonet blir brukt på snarvegane
  på skrivebordet. Namnet står i kommandovindauget.
- Logo og namn øvst i nettlesaren, med eige ikon i fana.
- **Rapport** (skriv ut / PDF / HTML) med:
  - logo og namn
  - oversikt og oversiktsteikning
  - objekttabell
  - profil og koordinatar per objekt
  - merknader

  Namn og signatur står nedst på kvar side.
- **Namnet er gøymt i alt programmet lagar** (pc/opphav.py, docs/LOGO.md):
  - DXF: kommentar og tittelfelt
  - GeoJSON: generator
  - CSV: tittelline
  - zip: kommentar
  - rå NMEA-logg: første line
  - HTTP-hovud og HTML-meta

  opphav.sjekk_signatur() finn signaturen att i ei fil.
- DXF blir skriven i Windows-1252 (R12-standard), så æøå blir rette i CAD.

## 0.5.0 – 5. november 2026
- **Koordinatar til objekt under bakken.** Klikk på eller ved eit objekt (innan 2 m) for å sjå:
  - austing og nording (EUREF89 UTM) og breidd/lengd
  - djupn før og etter retting
  - høgd over havet (NN2000) for objektet og bakken
  - kor mykje hellinga flytta objektet

  Tala kan kopierast, opnast i kart og eksporterast.
- Punktliste med koordinatar for heile objektet i djupneprofilen. Tverrsnittet har koordinatar og høgd for kvar
  kryssing.
- **Velje og eksportere:** klikk på objekt på kartet, eller kryss av i tabellen. Eksporter utvalet som:
  - **Utsetting:** punktfil for Trimble Access/R12i (namn, nord, aust, høgd, kode)
  - **CSV** for Excel
  - **GeoJSON** (EPSG 5972/5973 = UTM + NN2000)
  - **DXF** med djupnetekst

  Eksporten blir laga i nettlesaren og fungerer utan nett. Profilen har «Eksporter dette objektet», og
  posisjonspanelet har «Eksporter punktet».
- Ny innstilling: «Djupast georadaren skannar» (radar_djupn, standard 2,5 m, opptil 30 m). Ho styrer Status og
  «Grav nedover». Fargeskalaen for djupn er utvida til over 5 m.
- Per punkt i GeoJSON/CSV: hoegd_nn2000_m og bakke_nn2000_m.

## 0.4.0 – 5. november 2026
- **Djupna synest på Resultat:**
  - Tabellen viser djupna før og etter retting, med snitt og spenn.
  - Objekta på kartet er farga etter djupn. Kvart punkt viser djupna når ein held musa over, og «Vis djupn på
    kartet» skriv djupna ved punkta.
  - Djupneprofil for kvart objekt: lengd langs objektet mot djupn, før og etter.
- **Tverrsnitt på valfri stad:** klikk A og B på kartet, så viser programmet eit snitt ned i bakken med alle
  kryssingane. Det viser djupna etter retting, kvar objektet låg før (stipla) med ei pil for flyttinga, og
  røyrdiameter når han er kjend. Under er ein tabell.
- **Grav nedover:** ein glidebrytar som grev centimeter for centimeter (±5 cm), med avspeling. Han viser kva
  objekt som ligg på kvar djupn, både på kartet og i profilen.
- Djupn per punkt i GeoJSON (djupn_for_m, djupn_retta_m, flytta_cm) og i CSV. CSV-fila har desimalkomma
  overalt. DXF-fila har djupna som tekst på laget <lag>_DJUPN.
- Feilretting: ein logg med berre overskrift, eller ein tom logg, stoppa heile rettinga («Could not determine
  delimiter»). Slike loggar blir no hoppa over.
- Feilretting i grensesnittet: attributtverdiar utan hermeteikn før «/>» gøymde punkta i djupneprofilen.
- Nytt ope spørsmål (8): djupnesnitt av radarbiletet frå GRED HD/OneVision.

## 0.3.1 – 5. november 2026
- Data frå operatøren (innsendt/, pakkar/, resultat/, logg_demo/) blir aldri lagt i git og aldri rørt av oppdateringa.

## 0.3.0 – 5. november 2026
Klar til testing hos Norman Hole.
- Nytt grensesnitt i nettlesaren med fire faner. Det opnar seg av seg sjølv ved oppstart.
  - **Status:** fix, helling, retting, NTRIP og portar.
  - **Resultat:** skanningane (loggane), og kart med sporet farga etter helling (Kartverket). Eksport frå GRED
    HD/OneVision (GeoJSON/CSV) blir retta. Objekta blir viste før og etter, og kan lastast ned som GeoJSON, CSV og
    DXF.
  - **Send inn:** svar på dei opne spørsmåla, vedlegg (eksport, SCANNH.xml, bilete), og ei pakke (zip) til
    utviklaren utan passord og brukarnamn.
  - **Innstillingar:** portar (med liste over COM-portar), mast, retting, NTRIP-innlogging og GitHub-nøkkel for
    oppdatering. Lagring startar programmet på nytt.
- Berre PC-en sjølv kan endre noko. Mobil og nettbrett kan berre sjå.
- INSTALL.bat installerer Python med winget om det manglar, og lagar snarvegar på skrivebordet (vanleg og DEMO).
- Simulatoren køyrer no i parallelle stripar, som ein ekte georadar.
- statusside.py er erstatta av webtenar.py og web/index.html. Leaflet 1.9.4 er kopiert frå Snødjupne (BSD-2,
  web/vendor/LEAFLET-LICENSE).
- docs/BRUKARRETTLEIING.md for operatøren.

## 0.2.2 – 5. november 2026
- Namnet er no **Snowman Geoscan**, med «Alpindata HP Brunstad Sørensen» under, på statussida, ved oppstart,
  i startfilene og i dokumenta.

## 0.2.1 – 5. november 2026
- START-DEMO.bat og geoscan_config_demo.json: demo med eitt klikk, med simulert mottakar og NTRIP-caster. Han er
  tydeleg merkt DEMO på skjermen og statussida, og brukar aldri ekte NTRIP-innlogging.
- docs/TESTPLAN.md: testplan i fire steg, frå demo til felt.

## 0.2.0 – 5. november 2026
- NTRIP i Geoscan: hentar korreksjonar og sender RTCM til R12i (USB eller eigen port, t.d. Bluetooth port 2).
  Målet er å erstatte Trimble Access. Klienten er kopiert frå Snødjupne.
- Statusside på http://localhost:8088: fix, helling, retting, NTRIP og portar. Fungerer på mobil.
- Oppdatering utan ny installasjon: knapp på statussida, OPPDATER.bat og TILBAKE-TIL-FORRIGE.bat. Den nye versjonen
  blir kontrollert før han blir lagd inn, med reserve og tilbakerulling. Oppsett og innloggingar blir aldri rørte.
- Opptak av rå NMEA (logg/raa_*.nmea), og simulator med falsk NTRIP-caster.
- korriger_objekt.py les GeoJSON (djupn eller høgd) og reknar om mellom UTM-soner (t.d. EPSG:5973 / UTM33).
  Loggen har fått høgda på bakken (h_bakke).
- Mastehøgd 1,40 m som standard. Det er eit førebels svar, sjå docs/OPNE-SPORSMAL.md.

## 0.1.0 – 5. november 2026
- Første versjon: hellingskorreksjon for IDS Stream C. Masta blir retta i sanntid, djupna etterpå
  (korriger_objekt.py). Støttar R12i sin eigen tilt-kompensasjon. NN2000 via Kartverket-geoiden.
