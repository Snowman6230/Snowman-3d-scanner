# Endringslogg – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

## 0.9.25 – 14. november 2026
Ny skjerm (utkast B2, vald av Hans Petter 14.11 etter tre utkast), 3D-grøft og satellittar per system:
- **Ny skjerm (B2): kartet fyller midten.** Infomenyen til venstre viser Fix, satellittar, QH/QV, PJK, helling med
  vognskissa, retting, korreksjonar med aktivitetsstolpen og posisjonen – alltid, same kva fane som er open. Ho kan
  minimerast (⇤) til ei smal stripe med nøkkeltala (fix, satellittar, QH/QV, helling, retting, korreksjonar, varsel).
  Til høgre er ei ikonstripe (Status, Resultat, Send inn, Innstillingar, og nede Dagslys, Lyd, Varsel i Windows,
  Avslutt) og eit panel med innhaldet i fana. Panelet kan faldast saman (») og gjerast breiare eller smalare ved å dra
  i kanten (dobbeltklikk = standard). Vala blir hugsa i nettlesaren. Under Resultat viser kartet i midten
  resultatkartet, elles live-kartet. Alle funksjonane frå 0.9.24 er med, berre flytta. Meldingane frå Hans Petter er
  falda saman til tittelen, og berre den nyaste ulesne står open («vis» / «merk alle som lesne» for dei eldre).
- **3D-grøft under Resultat (av/på).** Knappen «🧊 3D-grøft» over kartet viser røyr og kablar frå målinga i ei grøft
  i 3D: farga etter djupn som i 2D, med diameter når han er kjend, og grå og gjennomsiktige der GRED HD/OneVision la
  dei før retting. Grøfta følgjer hovudretninga til objekta. Terrenget kan ha flyfoto eller same kart som i 2D (krev
  internett), og bakgrunnsfilene (DXF/KOF) blir lagde på bakken, eller i rett djupn når linjene har høgd. «Grav
  nedover» er eit plan i grøfta. «📏 Målsetting» av/på viser lengd, breidd og djupn på grøfta, djupna til toppen av
  kvart røyr og klaringa der to objekt kryssar kvarandre. Overhøgd 1–3×, kameraknappar (ovanfrå, skrått, langs
  grøfta), klikk på eit røyr for å velje det, og «Lagre bilete» (PNG med namn, versjon og fil). Byggjer berre på
  objekta Geoscan alt har – radardataa (.scan/.data) er ikkje med enno. three.js (MIT) ligg i `pc/web/vendor`.
- **Satellittar per system (ønske frå Hans Petter 14.11).** Nytt `pc/satellittar.py` les GSA (i bruk) og GSV (i
  sikte), med og utan system-ID (NMEA 4.10), og finn systemet frå PRN-nummeret når det trengst. Under Fix står t.d.
  «10 av 12 GPS · 8 av 9 GLO · – av 7 GAL». R12i må sende GSA og GSV for porten (I/O Configuration → NMEA).
  Til OneVision går framleis berre GGA. Simulatoren sender GSA/GSV, og ny test.
- **Feilretting (viktig): Status vart ikkje oppdatert i 0.9.24.** I 0.9.23 hamna deklarasjonen av `autoPause`,
  `lforrB`, `lforrRt` og `lpausa` bak ein kommentar på same line. Live-kartet stoppa då med «lforrB is not defined»
  kvart sekund, før Fix, helling og korreksjonar vart skrivne. Tala vart difor ikkje oppdaterte. Retta, og funne med
  ein test i nettlesaren (DEMO).
- Målestokken på karta står no nede til høgre, så han ikkje kolliderer med knappane og «Grav nedover».

## 0.9.24 – 12. november 2026
Etter pakka frå Norman 12.11 (målebok tom for straum, RTK borte frå kl. 15:15):
- **Aktivitetsstolpe for korreksjonane (ønske frå Norman, som NTRIP-stolpen i Xsite).** Ruta heiter no
  «Korreksjonar». Geoscan les alderen på korreksjonane frå GGA (felt 13) og tel kvar gong han fell, det vil seie kvar
  gong ein ny korreksjon kjem fram til mottakaren. Det verkar same om korreksjonane kjem frå Trimble Access
  (Bluetooth) eller frå Geoscan (USB). Gul = under 3 s, oransje = 3–10 s, raud ramme = ingen korreksjonar. Med NTRIP
  av i Geoscan står det «via mottakaren» når korreksjonane kjem frå Access. Ny `status.korr.korreksjon`
  (`alder`, `nye`, `ny_t`).
- **Kabel eller Bluetooth i «Finn utstyr» (ønske frå Norman).** Val øvst: alle portar, berre kabel (USB) eller berre
  Bluetooth. `finn_utstyr.filtrer()`, `kjelde` i `/api/finn_utstyr`. Valet blir hugsa i nettlesaren.
- **Statussida som mistar kontakten med Geoscan:** før stod siste varsel og tal att som om dei var ferske (sett
  12.11 kl. 22:37 under omstart). No kjem ei mørk ramme «Geoscan svarar ikkje» med lyd og Windows-varsel, og tala blir
  tømde. Sida koplar til att av seg sjølv.

## 0.9.23 – 11. november 2026
- **Tap av IMU – Norman hadde rett.** Testen på grusbana ved Velledalen grendahus 11.11 viste tre byte frå `$INGGA`
  (RTK FIX) til `$GNGGA` med hopp i høgd på +0,003, +0,010 og +0,003 m: når IMU-en fell ut medan R12i sender
  spissen, held han fram med spissen (stanghøgda trekt frå). 0.9.21 venta antenna og trekte frå 1,808 m, så
  OneVision fekk bakken 1,8 m for lågt i dei sekunda. No: byte frå IN til GN → ingenting blir trekt frå. Berre når
  R12i sender `$GNGGA` utan å ha sendt `$INGGA` først (IMU slått av i Access, som 9.11 kl. 08:52) blir antenna
  rekna med. Hoppet blir no målt òg når den eine sida er DGPS/FLOAT (RTK FIX på minst éi side, under 1 s mellom).
- **Sporet i kartet (ønske frå Norman 11.11):** knappen er no grøn «● Sporet blir teikna» / raud «▶ Start sporet
  (stoppa)». Auto-pause av skannestripa er strengare: under 0,25 m/s, over 15°/s, knekk over 25° på 1 m, eller
  rygging, og pausen held 1,5 s etter siste sving, så stripa ikkje blir teikna når du snur og rangerer.

## 0.9.22 – 11. november 2026
- **Ikonet på skrivebordet:** Norman hadde mista ikonet på snarvegen. Nytt `snarveg.py`: ved første start etter kvar
  oppdatering lagar Geoscan snarvegane «Snowman Geoscan» og «Snowman Geoscan DEMO» på skrivebordet på nytt (same som
  INSTALL.bat), med `ikon/geoscan.ico`, og ber Windows oppdatere ikon-mellomlageret (`ie4uinit -show`). Merket ligg i
  `logg/snarveg.txt`. Ny knapp «Lag snarvegar på nytt» under Innstillingar → Oppdatering.

## 0.9.21 – 9. november 2026
Etter Holetomta test 2 og svar frå Norman: spissen av stonga står i GPS-støtta på ramma, 0,09 m over bakken, og er
0-punktet. Med Trimble Access og IMU skal Geoscan ikkje endre noko – OneVision flyttar frå spissen til radaren.
- **«R12i med Trimble Access (IMU)» sender punktet urørt** (`$INGGA` = spissen). Berre høgda blir gjort om til NN2000
  med geoiden frå Kartverket (R12i brukar ein annan geoide – 9.11 var skilnaden 0,44 m). Bakkehøgda = spissen −
  `spiss_over_bakken` (ny innstilling, standard 0,09 m), òg i dei andre oppsetta.
- **Tap av IMU:** når R12i byter til `$GNGGA`, måler Geoscan hoppet i høgd (RTK FIX begge sider, under 2 s). Ca.
  mast + 0,179 → R12i sender antenna, og det blir trekt frå. Ca. 0 → stanghøgda er alt trekt frå (Norman meiner det),
  og ingenting blir endra. Før første byte blir antenna rekna med (9.11 kl. 08:52 med IMU av: `$GNGGA` 1,98 m over Access).
- **Kvalitetsvakt** (`Vakt`): IMU borte, RTK FIX tapt, QH > 5 / QV > 8 cm, data eldre enn 2 s. Aktiv etter 1 s, borte
  2 s etter. Raud stripe øvst på alle faner, pip (Web Audio) og varsel i Windows (Notification). Geoscan held fram med
  å sende, fordi OneVision stoppar opptaket når GPS-en forsvinn (OneVision 2.0-manualen). Gul stripe for faste feil i
  oppsettet (mast 0 eller fasesenter 0 med Access/IMU). Loggen har nye kolonnar `talker;imu;varsel`.
- **Stream C-boksen:** felt for x (0,13), y (0,42) og z (spissen over bakken, 0,09), med skisse av vogna ovanfrå og frå
  sida (mål frå Stream C-manualen). z til OneVision blir rekna ut frå oppsettet (`streamc.z_for`). Geoscan viser kva
  OneVision brukte i den nyaste målinga (`Survey_…/Data/Stream C.xml`) og åtvarar om ein skjult kopi i VirtualStore.
  Forslaget blir ikkje lenger rekna frå mastehøgda.
- **Resultat:** objekt frå mappa `Exports` (DXF og ESRI Shapefile frå «Target Export», nytt `onevision_eksport.py`) når
  `<Targets>` i `.svy` er tom. Har den nyaste målinga ingen objekt, seier Geoscan det i staden for å velje ei eldre i
  stillheit (det skjedde ved Holetomta: Resultat viste 7.11 frå 40 m lenger nord). Bakkehøgda frå alle loggrader blir
  brukt til høgda over havet òg utan hellingsretting. Sporet er oransje der IMU-en var borte, og objekt målte der blir merkte.
- **Bakgrunn:** farge per fil, høgd (Z) frå DXF (POLYLINE/VERTEX, LINE, POINT, LWPOLYLINE-elevasjon) og KOF. Filer lagde
  før 0.9.21 blir gjorde om på nytt med Z. Ny kolonne «Mot innmålt» i Resultat: avvik til næraste innmålte linje,
  sidevegs og i høgd (`bakgrunn.avvik`, `/api/avvik`).
- Statussida utan rulling er flytta til 0.9.22.

## 0.9.20 – 9. november 2026
- **Bakken kom 18 cm for høgt** (skjermbilete frå Norman 9.11 kl. 08:52): Geoscan og Trimble Access var samde på
  1 cm i nord, aust og antennehøgd (66,34 m), men Geoscan viste bakken 64,53 m og Access 64,359 m. Mastehøgda er
  målt til undersida av hurtigfestet (som stanghøgda i Access), og fasesenteret i R12i ligg 0,179 m høgare
  (Access: 1,898 m → APC 2,077 m). Ny innstilling `apc_tillegg` (standard 0,179 m) under Vogn og mast, og
  `helling.spakarm(cfg)` gir spakarmen til fasesenteret (mast + apc_tillegg). Brukt i rettinga, bakkehøgda,
  loggen, sporet og Stream C-forslaget.
- **z i Stream C.xml:** forslaget er no høgda til fasesenteret (1,99 m med mast 1,808), ikkje mastehøgda. Med
  z = 1,9 kjem bakken i OneVision om lag 8 cm for høgt. «Finn utstyr» og OneVision-målingane åtvarar òg.
- **Åtvaring ved feil GPS-kjelde:** kjem det `$GPGGA` utan GST, står det under Fix at Geoscan truleg les den
  innebygde GPS-en i PC-en og ikkje R12i (skjermbilete 07:46: «GPS», 8 satellittar, 4,7 m feil i høgd, medan
  Access hadde RTK med 13 satellittar).

## 0.9.19 – 9. november 2026
- **Bakgrunnsfiler i kartet** (ønske frå Norman 8.11): knappen «🗺 Bakgrunn» på begge karta. DXF-teikningar og
  KOF-filer blir lasta opp, gjorde om til breidd/lengd og viste under sporet. Koordinatsystem UTM 32/33/35 eller
  NTM 5–30 (EUREF89), eller «finn sjølv» (UTM eller NTM etter storleiken på tala; NTM-sona frå posisjonen til
  vogna). Kvar fil og kvart lag kan slåast av og på. DWG blir avvist med beskjed om å lagre som DXF. Nytt
  `bakgrunn.py` (eigen DXF- og KOF-lesar, ingen nye pakkar) og `koordinat.tm_forward/tm_inverse` (NTM).
  Filene ligg i `pc/bakgrunn/`, som berre finst på PC-en og aldri blir overskriven.
- **PJK og GGK frå Trimble Access under Fix** (ønske frå Norman 9.11): Access har ingen GST, så QH/QV kan mangle.
  Geoscan les `$PTNL,PJK` (koordinatane i Access-jobben) og viser dei under Fix med avviket mot Geoscan sine eigne
  UTM/NN2000-tal for same epoke (same UTC-tid). Med «EHT» blir høgda samanlikna med ellipsoidehøgda, elles med
  NN2000 (avviket viser då skilnaden mellom geoiden i Access og Kartverket-geoiden). Kjem berre GGK, blir DOP og
  ellipsoidehøgd viste. Utan GST står det no kvifor QH/QV manglar.
- «Retting no» på Status har fått underteksten «flytting for helling» (ein annan KI las kortet som korreksjonar
  til OneVision).

## 0.9.18 – 9. november 2026
Etter testpakka frå Norman 8.11.
- **Skannebreidda er 96 cm**, ikkje 77 cm. Objekt tvers over beltet i `.svy` frå 7.11 går ±0,479 m, som IDS oppgir.
  0.9.17 brukte ±0,383 m frå målinga i 2022. Stripa på karta er no 96 cm (`skannebreidd`), utan lysare kantfelt.
- **Val av GPS-oppsett** øvst under Innstillingar (ønske frå Norman): «R12i utan Trimble Access – Geoscan hentar
  NTRIP», «R12i med Trimble Access – Access hentar NTRIP og rettar med IMU» og «Berre rådata». Valet set NTRIP og
  «R12i rettar masta sjølv» når det blir endra (`gps_oppsett`, `innstillingar.GPS_OPPSETT`).
- **Geoscan skriv GPS-forskyvinga til OneVision** (Innstillingar → Vogn og mast). OneVision kan ikkje endre ho sjølv.
  Nytt `streamc.py`: les `Stream C.xml`, viser før og etter, tek kopi (reserve/ og .bak ved fila) og skriv
  y = |høgre| (forteiknet i fila blir halde) og z = mastehøgda. Krev det administratorløyve, spør Windows.
- **Mountpoint som meny**: lista blir henta frå casteren av seg sjølv når Innstillingar blir opna (ønske frå Norman).
- **Auto-pause av stripa** når vogna står (under 0,15 m/s) eller svingar kraftig (over 20°/s), slik at snuing og
  ranger ikkje teiknar stripe (ønske frå Norman). Brytar «Auto-pause ved snuing» på live-kartet. På Resultat blir
  stykke der sporet knekk meir enn 35° hoppa over.
- Same OneVision-måling blir ikkje lagra på nytt kvar gong ein trykkjer «Bruk denne» (`fil_lagre(gjenbruk=True)`).
- «Finn utstyr» rangerer GPS-en i LTE-modemet (Sierra Wireless, COM21 på Panasonic CS35) under R12i.

## 0.9.17 – 8. november 2026
- Skannestripe på karta (Status → Kart – live og Resultat → Kart): stripa radaren dekkjer, 77 cm (dei ytste spora i
  Stream C, ±0,383 m) med eit lysare felt ut til 96 cm (det IDS oppgir). Ho ligg midt på radaren, ikkje på antenna:
  med «rett antenne» blir midten rekna ut frå antenneposisjonen, kursen og spakarmen. Før låg sporet i Geoscan
  0,6 m ved sida av stripa i OneVision og bytte side når ein snudde. Brytar «Vis skannestripe» på begge karta
  (hugsa i nettlesaren). Når stripa blir vist, står vogna midt på radaren.
- Loggen har to nye kolonnar, `lat_radar` og `lon_radar` (midten av radaren). For eldre loggar blir stripa rekna
  ut frå kursen med spakarmen som står no. Nye innstillingar `skannebreidd` (0,77) og `skannebreidd_ytre` (0,96).
- Feil retta: ein generell CSS-regel (`svg{margin:6px auto 0}`) flytta alt Leaflet teiknar med SVG – spor, objekt og
  vogn – 6 pikslar sørover på karta. Ved stor zoom var det få cm, ved liten zoom fleire meter.
- Tekstane for spakarmen under Vogn og mast er retta så dei stemmer med koden: «Masta (antenna) til høgre for
  midten av radaren (minus = venstre)» og «… framfor midten av radaren (minus = bak)». Verdiane er uendra
  (−0,6 = antenna 0,6 m til venstre). Før stod det motsett, og eit positivt tal for «radaren framfor masta» ville
  ha gitt feil forteikn.

## 0.9.16 – 8. november 2026
- Melding til Norman om versjon 0.9.15 (QH/QV og GST i R12i) og oversikt over 0.9.8–0.9.14. Ingen kodeendring.

## 0.9.15 – 8. november 2026
- Status → Fix viser no nøyaktigheita frå mottakaren, som QH/QV i Novatron Xsite: **QH** (horisontal) og **QV**
  (vertikal) i cm, 1 σ, frå NMEA GST. Fargen er grøn under 3 cm, gul under 10 cm og raud over. Utan GST blir HDOP
  vist, med eit hint om å slå på GST i R12i (I/O Configuration → USB → NMEA → GST). GST går ikkje vidare til
  OneVision (berre GGA). Ønske frå Norman 8.11.
- Simulatoren sender GST, så QH/QV kan prøvast i demo.

## 0.9.14 – 8. november 2026
- «Finn utstyr» og com0com-dialogen kunne bli høgare enn skjermen på Panasonic-nettbrettet. Då forsvann ✕ og
  knappane, og dialogen kunne verken lukkast eller rullast. No får ingen dialog bli høgare enn skjermen. Han
  rullar inni, og ✕ står alltid synleg øvst til høgre. Esc og trykk utanfor lukkar òg.
- Lange Windows-feilmeldingar for portar er gjort korte («svarar ikkje (Bluetooth-port utan tilkopla eining)»,
  «oppteken av eit anna program»).

## 0.9.13 – 8. november 2026
- Resultat: nytt val «Rett for helling» (på som standard). Av: objekta frå OneVision blir viste og eksporterte
  urørte. Før stoppa Geoscan med feilen «loggane har ingen posisjonar med helling» når R12i køyrde utan IMU, og
  då kunne ein ikkje sjå målinga i det heile. No blir objekta viste likevel, med ein merknad om at dei ikkje er
  retta, og kart, tverrsnitt og «grav nedover» verkar. Ønske frå Hans Petter etter test 8.11.

## 0.9.12 – 8. november 2026
- OneVision lagrar kvar måling som `Projects/Survey_…/Survey_….svy`, med vogneoppsettet i `Data/Stream C.xml`
  (sett hos Norman 8.11). Når ei måling blir teken i bruk under Resultat, viser Geoscan GPS-forskyvinga (x, y, z)
  OneVision brukte i akkurat den målinga, og åtvarar om sida eller mastehøgda ikkje stemmer med Geoscan.

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
