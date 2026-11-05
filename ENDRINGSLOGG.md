# Endringslogg – Snowman Geoscan

*Alpindata v/Hans Petter B. Sørensen*

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
- Namnet er no **Snowman Geoscan**, med «Alpindata v/Hans Petter B. Sørensen» under, på statussida, ved oppstart,
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
