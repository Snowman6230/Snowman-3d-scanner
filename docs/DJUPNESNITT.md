# Plan: rette djupnesnitta (radarbiletet) for hellinga – Snowman Geoscan

*Alpindata HP Brunstad Sørensen*

Oppretta 6. november 2026 etter svar frå Norman Hole: «Det er dette som er interessant.»

## Mål

I dag rettar Geoscan berre objekta (røyr og kablar) for hellinga. Målet er å rette **heile radarbiletet**, sweep
for sweep. Då ligg djupnesnitta (time slices) rett i kartet òg i sidebakkar. Resultatet skal vere snitt som
GeoTIFF/PNG på kartet i Resultat-fana, med og utan retting.

## Kva vi veit om rådataa (IQMaps-konvertert mappe)

| Fil | Innhald | Stadfest |
|---|---|---|
| `Survey` (XML) | Prosjekt, EPSG:3857, swath-liste, RadarConfiguration | Norman |
| `SwathNNN.path` | 100 byte header, deretter postar på 36 byte: uint32 indeks, uint32 ms av UTC-døgnet, uint32 0, og X, Y, h (double, EPSG:3857, ellipsoidisk) | Norman (tid og posisjon lik første GGA) |
| `SwathNNN_ArrayMM.index` | versjon, hash, array (1 = V24, 2 = H10), 600, tal kanalar (23/9), 512 sampel, sweep-steg 0,0399 m, sampleintervall 1,25e-10 s, kanalrekkjefølgje og tabell per sweep | Delvis |
| `SwathNNN_ArrayMM.data` | 108 byte header, deretter sweeps × kanalar × 512 sampel (int16 LE) | Berre Array02, heuristisk |
| `Stream C.xml` | 64 ns, 512 sampel, enkodar 0,000798 m × 50 = 0,0399 m per sweep, antenner V24 (x 0,38) og H10 (x 0,57, snudd 180°) | Ja |
| `.svy` | UTM32, fart 0,1 m/ns, objekt i `<Targets>` | Ja (`svy_objekt.py`) |

## Framgangsmåte

1. **Les ein swath:** `.index` (kanalar og sampel), `.data` (spor) og `.path` (tid og posisjon).
2. **Plasser kvart sweep:**
   - Langs sporet: sweep-nummer × 0,0399 m, interpolert langs `.path`.
   - Tvers: kanalposisjonen i antennerekkja. Den skal lesast frå antennefilene i `config\antennas`.
3. **Hent hellinga** for kvart sweep frå Geoscan-loggen (stamp, krenging og kurs). Koplinga skjer på tid: ms av
   UTC-døgnet i `.path` mot tida i loggen. Same tidsbase som GGA, sidan OneVision synkar på GGA-tida.
4. **Rekn djupna for kvart sampel:** d = v · (t − t0) / 2, der v = 0,1 m/ns som i OneVision, eller kalibrert.
   - Retta posisjon: punktet blir flytt d · sin(helling) mot oppsida, same formel som `helling.object_shift`.
   - Loddrett djupn: d · cos(helling).
5. **Lag rutenett:** 5 cm × 5 cm, med eitt snitt per 5 cm djupn (0–2,5 m). Vis med og utan retting. Eksporter som
   GeoTIFF i UTM32 og som PNG-overlegg i Resultat-fana.
6. **Kontroll:**
   1. Utan helling skal snitta likne C-scan-filene og IQMaps.
   2. Felttest: skann eit kjent røyr i sidebakke i begge retningar. Retta snitt skal leggje røyret på same stad.

## Det som trengst frå Norman

1. `Swath001_Array01.data` og `Swath001_Array02.data` delte i bitar under ca. 5 MB (eller berre første 5 MB av
   kvar). Drive-tilkoplinga til Claude brotnar på 8 MB.
2. Antennefilene i `C:\Program Files (x86)\IDSGeoRadar\OneVision\config\antennas` (kanalposisjonar).
3. Eit skjermbilete av eit djupnesnitt frå IQMaps (til dømes 0,8 m) for Swath001, til samanlikning.
4. Kvar kompasset i radaren blir lagra (sjå punkt 9 i [OPNE-SPORSMAL.md](OPNE-SPORSMAL.md)).
5. Ein felttur med Geoscan-logg (helling) og OneVision samtidig, så retting faktisk kan prøvast.

## Avgrensing

Retting av radarbiletet skjer **etterpå** på PC-en, ikkje i sanntid. OneVision og IQMaps blir brukte som før.
Geoscan les berre kopiar av filene og skriv aldri til OneVision- eller IQMaps-prosjekta.
