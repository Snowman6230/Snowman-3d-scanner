# Endringslogg – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

## 0.9.11 – 8. november 2026
- Resultat finn målingane frå OneVision sjølv (`Survey_ÅÅÅÅ.MM.DD_NNN … .svy`, nytt `onevision_filer.py`). Lista
  «Måling frå OneVision» viser alle, nyaste først, med dato, nummer og tal objekt. Er ingenting lasta inn, blir den
  nyaste målinga med objekt brukt automatisk. Ein kan velje ei anna og trykkje «Bruk denne». Ønske frå Hans Petter
  og Norman etter test 8.11.
- Geoscan leitar i `<Dokument>/OneVision/Projects` og `X:/Dokumenter/OneVision/Projects` på alle stasjonar (hos
  Norman `E:/Dokumenter/OneVision/Projects`). Ny innstilling `onevision_mappe` (Retting og lagring) om målingane
  ligg ein annan stad. Berre `.svy`-filer i desse mappene kan hentast frå nettsida.

## 0.9.10 – 8. november 2026
- Resultat: «✚ Tverrsnitt» og «Grav nedover» står no alltid over kartet. Før var dei gøymde til ei eksportfil med
  objekt var lasta inn, og Norman fann dei ikkje. No er dei grå med ei forklaring om å laste inn `.svy`-fila frå
  OneVision først, og blir aktive når objekta (med djupn) er lasta.

## 0.9.9 – 8. november 2026
- Status → NTRIP-kortet viser no koordinatane til punktet som blir sendt til OneVision: UTM (E, N, sone) og høgd
  i NN2000 (og bakkehøgd under radaren når «rett antenne» er valt). Då ser ein med ein gong at posisjon, korreksjonar
  og geoide verkar. Ønske frå Hans Petter etter test 8.11.

## 0.9.8 – 8. november 2026
- Stripa om ugyldig GitHub-nøkkel blir ikkje lenger vist øvst på sida. Repoet er ope i testperioden, og
  oppdateringane går utan nøkkel, så meldinga forstyrra berre testen. Det står no som ei lita linje under
  Innstillingar → Oppdatering.

## 0.9.7 – 7. november 2026
- **Resultatet av «Finn utstyr» kjem til utviklaren av seg sjølv.** Kvar skanning blir lagra i loggmappa
  (`finn_utstyr_*.json`, dei 5 siste), og samandraget blir skrive i kommentaren til sjekkpunkt r0 (merkt «[auto]»,
  berre om operatøren ikkje har skrive noko sjølv). Pakka får `SKANNING.txt` med siste skanning: mottakar, talker,
  Hz, fix, satellittar, baud, com0com-portane, Stream C.xml og åtvaringar. Operatøren treng ikkje ta skjermbilete.

## 0.9.6 – 7. november 2026
- **Finn utstyr automatisk** (Norman 7.11: «oppstartsekvens som tolkar kva som blir sendt, kva COM-port, GGA-type
  … heilautomatisk – vi kan bruke forskjellige roverar»). Ny `pc/finn_utstyr.py`:
  - Skannar alle ledige portar parallelt på vanlege baudrater og tolkar dataa: GNSS (talker, Hz, fix, sat),
    hellingsmålar ($PTNL,AVR / $PASHR / HPR), RTCM/UBX, stille, oppteken av anna program.
  - Portar Geoscan alt les, blir ikkje opna – der blir live-dataa brukte. com0com-ender blir ikkje opna.
  - Les OneVision sitt `Stream C.xml` og åtvarar om komma, mastehøgd og sideforskyving som ikkje stemmer.
  - Forslag (IMU-retta `$INGGA` og høgast rate først) med «Bruk dette og start på nytt». `mottakar_kompenserer`
    blir sett etter talker-ID-en.
  - Startar av seg sjølv når mottakaren ikkje gir posisjon dei første 10 s (ikkje i demo).
- Portoversikta på Status viser no talker, «stangspiss/antenne», Hz, fix og satellittar for kvar inngang.
- Nytt sjekkpunkt r0.

## 0.9.5 – 7. november 2026
- **Berre `$INGGA` blir rekna som stangspiss.** Norman 7.11: «Access reknar ut når det blir brukt, men streaming
  ut elles trur eg er i fasepunktet til antenna.» Rådataa frå felttesten stadfestar det: alle 2 760 posisjonane
  var `$GNGGA`. Geoscan la likevel til mastehøgda (fordi `mottakar_kompenserer` var på), så høgda til OneVision
  vart 1,8 m for høg. No avgjer talker-ID-en: `IN` = stangspiss, elles antenne. Rådata frå testen gir 0,0 m
  skilnad i høgd. Status åtvarar når mottakaren sender antenneposisjon og masta ikkje blir retta.
- Nytt ope punkt 15: kan R12i sende `$INGGA` utan Trimble Access?

## 0.9.4 – 7. november 2026
Etter felttest hos Norman 7.11 (pakke SnowmanGeoscan_pakke_20261107_165722):
- **Feil retta: spora i OneVision låg feil og bytte side når ein snudde.** Med R12i-tilt
  (`mottakar_kompenserer`) og `rett_antenne` vart stangspissen rekna som referansepunktet midt på radaren, og
  kvar posisjon vart flytta 0,60 m til venstre for køyreretninga ein gong for mykje. Stadfest på alle 3 887
  punkt i loggen (alltid 270° frå kursen). No: rett antenne = rett over stangspissen (ingen sideflytting).
  Referansepunkt = stangspissen minus den vassrette spakarmen. Rådata frå testen gir 0,1 mm (avrunding).
  Ny test med sidearm (den gamle hadde berre loddrett arm og fanga ikkje feilen).
- **Mountpoint frå casteren:** knappen «Hent liste frå casteren» hentar kjeldetabellen (nærmaste først når
  posisjonen er kjend) og fyller ei nedtrekksliste. Brukar lagra brukar/passord om felta er tomme.
- **«⏸ Pause sporet»** på live-kartet: stoppar teikninga når ein snur og rangerer. Loggen held fram.
- Simulatoren sin caster har no to mountpoints i kjeldetabellen.
- OPNE-SPORSMAL: RTK FIX ute avklart (under 1 min, 92 % FIX). Nye opne punkt: mastehøgd 1,80/1,86/1,9,
  sideforskyving 0,42 i `Stream C.xml` mot 0,6 målt, og 1 Hz frå R12i.

## 0.9.3 – 7. november 2026
- **Dagslysmodus for skjerm ute i sollys.** Knappen «☀ Dagslys» oppe til høgre byter til kvit bakgrunn,
  svart tekst, mørkare og sterkare statusfargar, tjukkare kantar, større skrift og større tal på Status.
  «🌙 Mørk» byter tilbake. Valet blir lagra i `geoscan_config.json` («tema») og gjeld neste gong.
- Teikningane (vogna sett bakfrå, tverrsnitt, djupneprofil, forklaringar og mottakarringen på live-kartet)
  brukar no fargane til temaet, så dei synest i begge modusane.

## 0.9.2 – 7. november 2026
- **Ugyldig GitHub-nøkkel stoppar ikkje lenger oppdateringa.** På PC-en til Norman stod det «repoet er privat og
  nøkkel manglar» sjølv om repoet er ope: den lagra nøkkelen vart avvist (401), og då vart det ikkje prøvd utan.
  No blir det prøvd utan nøkkel når GitHub avviser han. Ei gul stripe seier at nøkkelen er ugyldig.
  Meldinga ved privat repo seier no «nøkkelen manglar eller er ugyldig».
- Merk: PC-ar på 0.8.10 eller eldre med ugyldig nøkkel må slette `pc/oppdatering_lokal.json` éin gong for å nå
  denne versjonen.

## 0.9.1 – 7. november 2026
- Vogna på live-kartet følgjer zoomen: omtrent verkeleg storleik (1,6 m frå front til handtak, overslag til
  vogna er målt), men aldri under 44 eller over 130 pikslar, så ho alltid synest og aldri fyller kartet.
  I praksis 44 px fram til zoom 21 og ca. 93 px ved største zoom.

## 0.9.0 – 7. november 2026
- **Live-kart på Status.** Kartet viser kvar vogna er medan ein skannar, og blir oppdatert kvart sekund.
  - Vogna er teikna som på logoen, sett ovanfrå: raud radarkasse, hjul, handtak bak og GNSS-antenna 0,6 m til
    venstre. Ho snur seg etter køyreretninga. GPS-prikken har farge etter fix (grøn RTK FIX, gul FLOAT/DGPS, raud GPS).
  - Vogna står på den retta posisjonen som blir sendt til OneVision. Ein open ring viser posisjonen frå
    mottakaren, så ein ser kor mykje Geoscan flyttar punktet i sidebakke.
  - Sporet veks medan ein køyrer, med farge etter hellinga (som i Resultat).
  - «Følg vogna», «Vis mottakarposisjon», «Tøm sporet» og same kartval som i Resultat (flyfoto o.a.).
- Status-svaret har ny `korr.pos` (lat/lon inn og ut, fix, kurs, stamp, krenging).

## 0.8.10 – 6. november 2026
- **NTRIP-adressa blir reinska:** «http://caster.no:2101/TH» blir lagra som caster «caster.no», port 2101 og
  mountpoint TH. Køyring 6.11 kl. 23.04 gav «getaddrinfo failed» (namnet på casteren vart ikkje funne).
- Meldinga ved slik feil seier no kva som skal sjekkast: adressa (berre namn eller IP, utan http:// og port) og
  internett.
- Køyringa stadfesta òg at Geoscan ikkje heng når OneVision ikkje les COM34 («ingen les porten – 287 linjer kasta»).

## 0.8.9 – 6. november 2026
- **com0com-para blir funne i registeret.** På PC-en vart paret COM44 ↔ COM45 laga, men Geoscan sa framleis
  «ikkje noko portpar»: com0com-portar utan «use Ports class» er ikkje med i portlista frå pyserial. Geoscan les no
  òg `HARDWARE\DEVICEMAP\SERIALCOMM` (\Device\com0com1n = A-enden, com0com2n = B-enden) og
  `Enum\COM0COM\PORT\…\PortName`. «Lag portpar» unngår òg namn som alt er i SERIALCOMM.

## 0.8.8 – 6. november 2026
- «Lag portpar no» unngår no portnamn som Windows har reservert (ComDB, «in use» i COM port database), til dømes
  COM24 etter eit tidlegare com0com-par. Første køyring stoppa på dialogen «The port name COM24 is already logged as
  in use». Geoscan vel då neste ledige par (COM35 ↔ COM25 osb.).

## 0.8.7 – 6. november 2026
Etter første køyring på PC-en (skjermbilete 6.11 kl. 22.35):
- **«Lag portpar no»:** com0com var installert, men utan portpar. Knappen i com0com-vindauget lagar no paret
  sjølv (COM34 ↔ COM24, eller neste ledige) med `setupc install` som administrator – Windows spør om løyve – og
  set «Til OneVision» til Geoscan-enden.
- **Portnamn blir retta:** «25» vart prøvd opna som fila «25». No blir «25» og «com25» til «COM25», både når
  innstillingane blir lagra og når porten blir opna.
- NTRIP 401: meldinga nemner no Trimble Access (same konto på to einingar) og kvar passordet blir sett.

## 0.8.6 – 6. november 2026
- **Vel bakgrunnskart i Resultat:** ny meny med fargekart og gråtonekart (Kartverket), flyfoto (Esri World
  Imagery) og OpenStreetMap. Flyfoto viser kantsteinar, kummar og asfaltkantar, som hjelper når ein skal finne att
  røyr. Valet blir lagra i `geoscan_config.json` («kartlag»), og «✓ lagra» blir vist ved menyen. Same kart kjem
  opp neste gong. Knappen «Gråtonekart/Fargekart» er erstatta av menyen.

## 0.8.5 – 6. november 2026
- **com0com-sjekk ved oppstart (Windows).** Ny `pc/com0com.py` finn ut om com0com er installert og kva portpar som
  finst (portlista frå Windows, `setupc list` og registeret).
  - Ikkje installert: eit vindauge forklarar kva com0com er og korleis det blir installert (nedlastingslenke,
    stegvis), og ein raud stripe står øvst til det er på plass. Vindauget kan lukkast.
  - Installert: eit vindauge viser para (t.d. COM34 ↔ COM24), kva ende Geoscan og OneVision skal bruke, og ein
    knapp «Bruk COM34 til OneVision». Åtvarar om feil port eller «emulate baud rate». Kan lukkast, med «Ikkje vis
    igjen før noko endrar seg».
  - Innstillingar → Portar viser com0com-status og «Vis forklaring». Ikkje i demo.
- **Innstillingane blir lagra automatisk** medan ein skriv. Ei stripe øvst viser «✓ Lagra kl. 18:52:07 i
  geoscan_config.json», og feltet lyser grønt. Er eitt felt ugyldig, blir resten lagra, og stripa seier kva som
  ikkje vart lagra (den gamle verdien står att). Endringane gjeld etter «Start på nytt no – bruk endringane».
  Sida les innstillingane frå fila, så autolagra verdiar blir viste og ikkje skrivne over.
- **Svara under «Send inn» blir lagra automatisk** (knappen «Lagre svara» er borte). Sjekklista viser klokkeslett.

## 0.8.4 – 6. november 2026
- Brukarrettleiinga: korleis ein sjekkar om com0com finst, installerer den signerte versjonen og lagar paret
  COM34 ↔ COM24, og korleis testen kan gjerast utan com0com (OneVision på Bluetooth, Geoscan loggar, retting etterpå).
- Meldinga til Norman er oppdatert med det same.

## 0.8.3 – 6. november 2026
- **Geoscan heng ikkje lenger om OneVision ikkje les com0com-porten.** Skrivinga til OneVision-porten hadde
  ingen tidsgrense. Var OneVision lukka, hekk eller ikkje kopla til COM24, kunne bufferen bli full og heile
  Geoscan stoppe (logg, GGA til NTRIP, status). No er grensa 0,2 s: linja blir kasta, teljaren «kasta» aukar, og
  statussida viser «ingen les porten».
- **Berre GGA til OneVision** (`"setningar": ["GGA"]` på utgangen). OneVision les berre GGA (StringFilter GGA),
  så mindre trafikk og ingen køyring av RMC/GLL/GGK/GSV gjennom porten. Gjeld når OneVision-porten blir lagra
  under Innstillingar.
- Brukarrettleiinga: stopp NMEA-splitteren og Trimble Access før start.

## 0.8.2 – 6. november 2026
- **«Send inn» oppdatert til testen:** spørsmåla viser no det som er avklart (mast 1,80, GPS 0,6 m til venstre)
  så Norman kan stadfeste det, og nye spørsmål om kompasset i radaren og om radardata er lagde ved.
  Gamle spørsmål om kurs (HDT) og eksportformat er tekne bort eller endra, sidan dei er avklarte.
- Ny filtype «Radardata» (.svy, .path, .index, .data, antennefiler) for planen om å rette djupnesnitta.
- Nye sjekkpunkt: r4 (mast og forskyving lagra i Innstillingar og R12i) og f6 (.svy blir lesen under Resultat).
- Meldinga til Norman forklarer det nye og kva han skal leggje ved.

## 0.8.1 – 6. november 2026
- **Objekt rett frå OneVision-målefila (.svy).** OneVision lagrar dei automatisk funne objekta inne i
  `Survey_….svy` (`<Targets>`), ikkje i ei eksportfil. Nytt `pc/svy_objekt.py` les dei (namn, linje/punkt, E, N,
  djupn, EPSG) og gjer dei om til GeoJSON. Resultat-fana og `korriger_objekt.py` tek no `.svy` direkte.
  Formatet er tolka frå Kagholvegen-målinga 29.11.2022 (81 objekt).
- **Spakarm etter mål på vogna (Norman 6.11):** mastehøgd 1,80 m og GPS-mottakaren 0,6 m til venstre
  (`spakarm.hogre = −0,60`). Gjeld nye oppsett. Eksisterande `geoscan_config.json` blir ikkje rørt, så set
  verdiane under Innstillingar.
- Opne spørsmål oppdaterte: mastehøgd, referansepunkt, eksport, kurs (HDT) og PPS er avklarte. Nye punkt:
  rette sjølve radarbiletet (plan i `docs/DJUPNESNITT.md`) og kompasset i radaren.

## 0.8.0 – 5. november 2026
- **Økter: halde fram der ein slapp.** Alt blir lagra fortløpande i logg/okt.json:
  - fane og kartutsnitt
  - skanningar, siste retta eksportfil og valde objekt
  - profil, «grav nedover», tverrsnitt og djupnetekst

  Ved oppstart spør programmet: «Hald fram med førre økt» eller «Start ny økt» (med namn). Ei ny økt arkiverer
  den førre (logg/okt_arkiv/). Etter omstart (oppdatering, lagra innstillingar) held programmet fram utan å
  spørje. Skanningane i økta er merkte «denne økta».
- **⏻ Avslutt-knapp** øvst: lagrar alt, stoppar reint og lukkar det svarte vindauget. I demoen blir òg
  simulatoren stoppa. Ved feil blir vindauget ståande, så feilen kan lesast.
- **Oppdatering under Innstillingar:**
  - installert versjon og versjon på GitHub
  - når det sist vart sjekka
  - knappane «Sjå etter ny versjon no», «Oppdater no» og «Gå tilbake til førre versjon»

## 0.7.5 – 5. november 2026
- Namnet blir skrive éin gong øvst i vindauget (med versjon), ikkje to.

## 0.7.4 – 5. november 2026
- Det svarte vindauget er roleg: ei line berre når fix, helling, NTRIP, portar eller feil endrar seg, og elles
  éi line i minuttet (statuslinje_sek). Før kom det ei line annakvart sekund.
- START-GEOSCAN.bat og START-DEMO.bat startar vindauget (og simulatoren) minimert. Vindauget seier at det må
  vere ope medan ein skannar.

## 0.7.3 – 5. november 2026
- CSV-filene frå Resultat og korriger_objekt.py blir no skrivne som UTF-8 med BOM. Utan BOM las Excel «–» og
  «ø» som «â€“» og «Ã¸» (melde av Hans Petter). CSV-eksporten frå nettlesaren hadde alt BOM.
- Utsettingsfila for Trimble er berre ASCII: æøå blir til ae/o/aa i punktnamn og kode, så importen ikkje feilar.

## 0.7.2 – 5. november 2026
- DEMO: «Prøv med eksempelfil» brukar ein ferdig demologg som dekkjer heile simulatorfeltet
  (web/vendor/demo-logg.csv). Før vart berre nokre få punkt retta rett etter at demoen var starta, fordi den
  simulerte vogna brukar 5–6 minutt på ei full runde. Funne i ein test av heile vegen frå GitHub-zip, slik
  Norman får programmet.

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
