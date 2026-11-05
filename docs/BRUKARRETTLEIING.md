# Snowman Geoscan – brukarrettleiing

*Alpindata v/Hans Petter B. Sørensen*

Snowman Geoscan rettar GNSS-posisjonen til IDS Stream C for hellinga til vogna. Programmet gjer to ting:

- **Under skanninga** blir posisjonen som går til OneVision, retta for masta.
- **Etter skanninga** blir røyr og kablar retta for djupna.

Alt blir styrt frå ei side i nettlesaren som opnar seg av seg sjølv.

## 1. Installere (éin gong)

1. Last ned programmet. Hans Petter sender deg ei zip-fil, eller du lastar ned frå GitHub med **Code → Download ZIP**.
   Pakk ut, til dømes til `C:\Snowman Geoscan`.
2. Opne mappa `pc` og dobbeltklikk **INSTALL.bat**.
   - Manglar Python, blir det installert. Dobbeltklikk så INSTALL.bat éin gong til.
   - Til slutt kjem det to snarvegar på skrivebordet: **Snowman Geoscan** og **Snowman Geoscan DEMO**.

## 2. Prøv demoen først

Dobbeltklikk **Snowman Geoscan DEMO**. Ein simulert mottakar køyrer ei georadarvogn i stripar i ein sidebakke.
Nettlesaren opnar seg med Snowman Geoscan, og øvst står det ei raud DEMO-linje. Sjå gjennom alle fanene. Under
**Resultat** ser du sporet farga etter helling. Demoen rører ikkje utstyret ditt.

## 3. Kople til R12i og OneVision

1. **Lukk Trimble Access.** Berre eitt program kan bruke mottakaren om gongen.
2. Start **Snowman Geoscan** frå skrivebordet og gå til fana **Innstillingar**:
   - **Mottakar:** porten til R12i, til dømes COM23 (USB). Lista viser portane PC-en finn.
   - **Til OneVision:** com0com-porten, til dømes COM34. OneVision les den andre enden, COM24.
   - **Mastehøgd:** mål frå merket for antennehøgd ned til underkanten av radaren.
   - **NTRIP:** caster, port, mountpoint, brukarnamn og passord. Passordet blir berre lagra på PC-en.
   - **R12i rettar masta sjølv:** kryss av når tilt er på i R12i og stanghøgda er sett lik mastehøgda.
3. Trykk **Lagre og start på nytt**.
4. Sjå på fana **Status**. Fix skal bli **RTK FIX** ute, og NTRIP skal vere **tilkopla**. Hellinga blir vist med ei
   teikning av vogna.

## 4. Skanne

Skann i OneVision som vanleg. Snowman Geoscan må vere i gang heile tida, og vindauget kan liggje i bakgrunnen.
Kvar skanning blir lagra med posisjon og helling.

## 5. Sjå resultatet

Fana **Resultat**:

- **Skanningar:** ei line per gong programmet har vore i gang, med kor mykje vogna hallar. Trykk på ei line for å
  sjå sporet på kartet. Fargen viser hellinga: grøn under 1°, gul 1–3°, oransje 3–6° og raud over 6°.
- **Rett røyr og kablar:**
  1. Eksporter objekta frå GRED HD eller OneVision som **GeoJSON** (eller CSV med austing, nording og djupn).
  2. Trykk **Vel eksportfil …**.
  3. Kartet viser objekta **før** (grå stipla) og **etter** retting (blå). Tabellen viser kor mykje kvart objekt
     er flytta.
- **Djupna:** tabellen viser djupna før og etter retting for kvart objekt, med snitt og spenn (grunnaste–djupaste).
  Djupn er alltid loddrett avstand frå bakken ned til objektet. På kartet er objekta farga etter djupn: lys blå
  er grunt, lilla og rosa er over 2 m. Hald musa over eit punkt for å sjå djupna der. Trykk **Vis djupn på
  kartet** for å få djupna skriven ved punkta.
- **Djupneprofil:** trykk på eit objekt i tabellen eller på kartet. Då ser du korleis røyret eller kabelen går
  nedover i bakken langs heile lengda.
- **Tverrsnitt på valfri stad:**
  1. Trykk **✚ Tverrsnitt**, og klikk to punkt på kartet, A og B, til dømes på tvers av ei grøft.
  2. Under kartet kjem eit snitt ned i bakken langs lina A–B. Det viser kvar røyr og kablar kryssar, og kor djupt
     dei ligg.
  3. Den stipla ringen viser kvar GRED HD/OneVision la objektet, og pila viser kor mykje hellinga flytta det.
  4. Står diameteren i eksporten (`diameter_mm`), blir røyret teikna i rett storleik.
  5. Tabellen viser avstanden frå A, djupna før og etter, og flyttinga.
- **Grav nedover:** dra glidebrytaren over kartet for å grave centimeter for centimeter, eller trykk **▶ Spel
  av**. Objekt som ligg på den djupna (±5 cm), lyser opp med ein ring der dei kryssar djupna. Det som ligg
  grunnare, blir blekt, og det som ligg djupare, er enno skjult. Profilen viser same djupn som ei stipla line.
  **Vis alt** tek deg tilbake.
- **Last ned** dei retta objekta som **GeoJSON, CSV eller DXF** (for AutoCAD, Gemini og GIS). DXF-fila har djupna som
  tekst ved kvart punkt (laget `<lag>_DJUPN`), og CSV-fila har djupna før og etter for kvart punkt. Filene ligg
  òg i mappa `pc\resultat`.

**Sjølve radarbiletet** cm for cm, som djupnesnitt eller radargram, ser du i OneVision og GRED HD som før. Snowman
Geoscan har berre objekta du eksporterer, ikkje radardataa.

Djupna kan berre rettast når hellinga er målt som tal, og det krev ein ekstra hellingsmålar (IMU) på ramma. Med
berre R12i blir masta retta under skanninga, men ikkje djupna. Då seier Resultat-fana frå om det.

## 6. Send inn det Hans Petter treng

Fana **Send inn**:

1. Svar på spørsmåla, til dømes mastehøgda og antenneoppsettet i OneVision. Det som er ukjent, kan stå tomt.
   Trykk **Lagre svara**.
2. Legg ved filer: ei ekte eksportfil, SCANNH.xml frå R12i, bilete av vogna og masta, og skjermbilete av
   GPS-oppsettet i OneVision.
3. Trykk **Lag pakke** og så **Last ned**. Send zip-fila til Hans Petter på e-post eller via OneDrive. Pakka har
   aldri passord eller brukarnamn med seg.

## 7. Oppdatere

Når det finst ein ny versjon, kjem det ein gul linje øvst med knappen **Oppdater no**. Trykk på han, så lastar
programmet ned den nye versjonen og startar på nytt av seg sjølv. Innstillingane dine blir verande som dei er.
Går noko gale, dobbeltklikk `pc\TILBAKE-TIL-FORRIGE.bat`.

For å hente oppdateringar treng PC-en ein GitHub-nøkkel. Du får han av Hans Petter, og legg han inn under
**Innstillingar → Oppdatering**.

## Når noko ikkje verkar

| Det du ser | Gjer dette |
|---|---|
| Porten står med «feil» på Status | Er Trimble Access lukka? Er USB-kabelen sett godt inn? Programmet koplar til att av seg sjølv. |
| NTRIP «feil: … passord» | Sjekk brukarnamn og passord under Innstillingar. |
| NTRIP tilkopla, men berre DGPS/FLOAT | Vent 1–3 min med fri sikt. Hjelper det ikkje, set «RTCM til port» til Bluetooth port 2 (til dømes COM20). |
| «ingen fersk helling» | Normalt med berre R12i: masta blir retta i mottakaren. For djupna trengst ein ekstra IMU. |
| Svart kart | Kartet frå Kartverket krev internett. Spor og objekt blir viste likevel. |

Alt som skjer, blir lagra i `pc\logg`. Lag ei pakke under **Send inn** og send henne til Hans Petter, så kan han
sjå nøyaktig kva som skjedde.
