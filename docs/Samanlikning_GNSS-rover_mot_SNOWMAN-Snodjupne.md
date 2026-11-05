# Samanlikning: GNSS-rover (Norman Hole) mot SNOWMAN Snødjupne v1.6

Dato: 5. november 2026. Kjelde: overleveringsdokumentet og repoet Snowman6230/Snowman-Snowdeept (commit 8a05dc4, pc/v1.6). Repoet er berre lese, ikkje endra.

## Det SNOWMAN Snødjupne allereie har

| Tema i overleveringa | SNOWMAN v1.6 |
|---|---|
| NTRIP v1/v2, GGA til casteren | Har det (ntripklient.py): auto v1→v2, chunked, kjeldetabell. Feil passord og mountpoint blir ikkje prøvde på nytt. |
| Talker $INGGA/$GNGGA | Har det: godtek alle setningar som sluttar på «GGA». |
| Høgd (geoide-avvik 0,45 m) | Har det: ellipsoidehøgd = alt + sep, deretter NN2000 med Kartverket-geoiden. Uavhengig av mottakaren sin geoide. |
| Helling / antennehøgd | Har det (helling.py): antZ, korreksjon både i høgd og plassering. Hellinga kjem frå PTNL,AVR/PASHR/HPR eller blir rekna ut. |
| Reconnect / port som fell ut | Har det: auto-port, vakthund og feltlogg. |
| RTK-status | Har det: fix-overgangar blir logga, med alder på korreksjonane og base-ID. |
| NMEA-deling til fleire program (splitter/TCP 5000) | Har det ikkje. |

## Den store arkitekturskilnaden

- **Norman** sender RTCM til mottakaren, og mottakaren reknar RTK.
- **SNOWMAN** sender aldri noko til mottakaren. Porten er berre lese («LesePort»). RTK blir rekna i SNOWMAN med RTKLIB, frå rådata (RTCM 3 MSM / UBX RAWX) frå mottakaren og basen frå NTRIP.
  - Alternativ modus: «mottakar_sjolv», der mottakaren hentar korreksjonane sjølv med eige SIM eller radio.

Konsekvens for R12i: mottakaren har ikkje eige internett, så «mottakar_sjolv» går ikkje. R12i må då sende rådata (RTCM 3 MSM) ut på porten som SNOWMAN les. Om R12i kan det, og med kva opsjon, er ikkje undersøkt.

## Kva frå Norman sitt skript er verdt å ta med

- TCP-server for NMEA-deling. Den kunne erstatte com0com-splitteren og gi andre program (georadar, 3D-skannar) posisjon frå SNOWMAN.
- Elles dekkjer SNOWMAN meir enn skriptet, og SNOWMAN-koden er testa i felt.
