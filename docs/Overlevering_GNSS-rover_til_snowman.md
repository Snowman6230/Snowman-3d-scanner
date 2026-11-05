Til: Claude-prosjektet for snowman (snødybdemåling i tråkkemaskin)\
Frå: Norman Hole, Hole Anlegg AS\
Dato: 5. november 2026\
Status: Delar er testa og fungerer, delar er berre eit utkast. Det står
tydeleg kva som er kva.

# 1. Føremål og kvifor dette kan vere nyttig for snowman

Eg bygger eit rover-program som gir ein PC posisjon frå ein Trimble R12i
(RTK) som NMEA, og som sjølv hentar NTRIP-korreksjonar. I dag brukar eg
Trimble Access til dette; målet er å erstatte Access. Same
problemstilling gjeld ei tråkkemaskin: ein mottakar med RTK,
korreksjonar over mobilnett, og NMEA vidare til eit program på ein PC.
Eg ber deg vurdere kva som kan gjenbrukast. Eg har ikkje sett
snowman-koden og veit ikkje kva som allereie finst der.

# 2. Maskinvare og programvare

  -----------------------------------------------------------------------
  Del                                 Detalj
  ----------------------------------- -----------------------------------
  GNSS-mottakar                       Trimble R12i, firmware 6.40. Alle
                                      opsjonar på (GNSS, NMEA, INS/IMU
                                      for stangtilt). Garanti/vedlikehald
                                      gjekk ut 30.11.2024.

  PC                                  Trimble T100, Windows 11

  Mottakar til PC                     USB (virtuell seriell port, COM23)
                                      og Bluetooth (portar COM19--21).
                                      Wi-Fi-tilgangspunkt i mottakaren
                                      finst, men er ope og brukast berre
                                      til konfigurasjonsportal.

  Mottakar-internett                  Mottakaren har ikkje eige
                                      internett. NTRIP må hentast av
                                      PC-en.

  Korreksjonskjelde                   Eigen NTRIP-caster, mountpoint TH.
                                      Basen er ca. 12 km unna.
                                      Teneste-opplysingar og passord er
                                      utelatne med vilje.

  Mottakar-konsument                  OneVision 2.1.4 (IDS Stream C
                                      georadar), som les NMEA frå ein
                                      COM-port
  -----------------------------------------------------------------------

# 3. Dataflyt i dag (fungerer)

NTRIP-caster → Trimble Access (på T100) → RTCM v3 over Bluetooth port 2
→ R12i.\
R12i → Trimble Access (lagar NMEA med jobbkoordinatar og
IMU-kompensasjon) → USB COM23 → eit PowerShell-skript som deler straumen
→ com0com-par (COM34→COM24 til OneVision, COM35→COM25 til
visingsprogram).

-   NMEA frå Access: \$GNGGA 5 Hz, i tillegg GGK og GLL. Bevist
    fungerande i OneVision: «GNSS connection OK -- DGPS Fix».

-   Splitteren må køyre for at COM24 skal få data. Berre eitt program
    kan ha COM23 open. Skripta ligg i
    C:\\Users\\HoleMaskin\\NMEA_Splitter.

-   Til no er fix-kvaliteten berre testa som DGPS (2) med mottakaren
    inne. RTK Fixed (4) er ikkje stadfesta ute.

# 4. Dataflyt eg vil ha (utkast, ikkje testa)

NTRIP-caster → eige program på PC → RTCM til R12i. R12i → NMEA (\$INGGA,
IMU-kompensert) → programmet → virtuell COM → konsument.

-   Utgangspunkt er scriptet ntrip_rtk_imu.py (Python, berre
    standardbibliotek og pyserial): NTRIP v1/v2 med automatisk
    reconnect, GGA tilbake til casteren, NMEA-validering med sjekksum,
    RTK-status frå GGA, grunnparsing av HDT/HDG/ROT/PTNL,AVR/PASHR,
    TCP-server på port 5000 og valfri seriell utgang, statuslogg.

-   Det er også ein konfigurasjonsfil (ntrip_config.json) og ei
    Start-NTRIP.bat. Brukarnamn og passord i konfigurasjonen er tomme.

-   Mangel: scriptet les NMEA og skriv RTCM på same port. R12i bruker to
    Bluetooth-portar for dette (port 1 NMEA, port 2 RTCM/GSOF).
    Programmet må enten ha to forbindelsar eller få RTCM over USB. Ikkje
    avklart.

-   Programmet er ikkje køyrt mot R12i. Det er ikkje testa i det heile.

# 5. Funn som er verdt å vite

  -----------------------------------------------------------------------
  Tema                                Funn
  ----------------------------------- -----------------------------------
  USB-fall                            USB-sambandet gjekk av og på.
                                      Årsaka var ein plugg som hadde
                                      glidd ut. Laus USB-C-overgang er
                                      risiko. Slå av USB-selektiv
                                      deaktivering i Windows. Programmet
                                      må koble til att av seg sjølv når
                                      porten kjem tilbake.

  Høgd                                Access-NMEA gir jobbhøgd (geoide
                                      45,224 m). Mottakaren sjølv gir
                                      EGM96 (44,775 m). Ca. 0,45 m
                                      skilnad på orto­metrisk høgd.
                                      Ellipsoidehøgda er lik. Relevant
                                      for snødybde, der høgda er målet.

  Frekvens                            Access: 5 Hz. Mottakaren direkte
                                      (Bluetooth port 1): 1 Hz. Om høgare
                                      rate går an direkte er ikkje
                                      undersøkt.

  Stangspiss kontra antenne           Med IMU på og jobbkoordinatar på
                                      gir NMEA stangspiss. Med IMU av gir
                                      NMEA antennens faseentrum (APC).
                                      Observert høgdehopp på ca. 2,2 m
                                      ved skifte. For tråkkemaskin er
                                      montasjen heilt annleis, så
                                      IMU-oppsett må vurderast på nytt.

  Talker                              Direkte frå mottakaren heiter
                                      setninga \$INGGA, ikkje \$GNGGA.
                                      OneVision godtok det. Anna
                                      programvare kan krevje GN/GP.

  Satellittar i RTK                   Mottakaren sporar GPS, GLONASS,
                                      Galileo og BeiDou, men RTK-løysinga
                                      brukte berre GPS og GLONASS. Truleg
                                      avgrensa av korreksjonskjelda.

  Port Summary                        Viser ikkje NMEA på USB sjølv om
                                      data kjem. Ikkje bruk det som
                                      bevis.

  Sikkerheit                          Mottakaren sitt Wi-Fi-tilgangspunkt
                                      er ope utan kryptering, portal på
                                      HTTP og FTP på. Ikkje kopier dette
                                      oppsettet til feltbruk utan å sikre
                                      det.
  -----------------------------------------------------------------------

# 6. Det eg ikkje veit

-   Om RTCM kan gå over USB til R12i, eller om det må gå på Bluetooth
    port 2.

-   Om 5 Hz er mogleg direkte frå mottakaren.

-   Om IMU-justering kan gjerast utan Trimble Access.

-   Om R12i er rett mottakar for tråkkemaskin, eller om det finst
    enklare mottakarar som gir same NMEA.

-   Kva snowman allereie har av NTRIP- og NMEA-handtering. Saml gjerne
    dette før gjenbruk.

# 7. Filer som høyrer til

-   C:\\Users\\HoleMaskin\\Documents\\OneVision: ntrip_rtk_imu.py,
    ntrip_config.json, Start-NTRIP.bat, Sett-GeoscannerIP.ps1/.bat

-   C:\\Users\\HoleMaskin\\NMEA_Splitter: splitter-skript for com0com og
    overleveringa frå 5. november

-   C:\\Users\\HoleMaskin\\Documents\\TRIMBLE OPPSETTSFILER: SCANNH.xml
    (clone-fil frå R12i, utan sikkerheitsdata)

Eg sender filene separat ved behov. Passord og brukarnamn skal ikkje
følge med.
