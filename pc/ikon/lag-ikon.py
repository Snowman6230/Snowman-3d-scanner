#!/usr/bin/env python3
# Snowman Geoscan – Alpindata HP Brunstad Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Lagar ikona og logoen til Snowman Geoscan frå éi kjelde.

Same uttrykk som SNOWMAN Snødjupne (pc/v1.6/ikon/lag-ikon.py i Snowman6230/Snowman-Snowdeept): natthimmel,
dei kvite fjelltoppane frå SNOWMAN-logoen og snøflata, same fargar og skrift. I staden for tråkkemaskina står
georadarvogna (IDS Stream C, sett frå sida) med GNSS-masta på snøflata, og radarbølgjene går ned i bakken mot
eit nedgrave røyr.

Skriv:
  geoscan.svg            hovudikon (512 × 512), kjeldefil
  geoscan-enkel.svg      forenkla ikon for små storleikar (16–32 px)
  geoscan-logo.svg       logo med tekst (fjelltoppar, SNOWMAN GEOSCAN, Alpindata HP Brunstad Sørensen)
  geoscan-256.png, geoscan-512.png, geoscan.ico (16–256 px)   – snarvegar og oppstartbilete
  oppstart.png           oppstartbiletet (ikon + logo) som blir vist når programmet startar
  ../web/vendor/geoscan-ikon.png (64 px), ../web/vendor/geoscan-logo.svg   – nettlesaren

Bruk (berre ved utvikling – krev Playwright/Chromium og Pillow):  python3 lag-ikon.py
"""
import asyncio
import io
import sys
from pathlib import Path

HER = Path(__file__).resolve().parent
NAMN, PRODUSENT = "Snowman Geoscan", "Alpindata HP Brunstad Sørensen"

# Frå SNOWMAN-logoen (viewBox 120 × 30) – same form som i Snødjupne
PEAKS = "M14 30 L46 2 L66 20 L74 13 L104 30 Z"
PEAK_CUT = "M33 14 L39 17 L46 11 L52 17 L57 14 M68 18 L74 16 L80 19"
NATT0, NATT1, SNO0, SNO1 = "#0b2a44", "#15507c", "#ffffff", "#dcecf7"
RAUD, RAUD_MORK, SKJER, BELTE, GPS = "#d42c2c", "#7a1010", "#8d9ba5", "#1a252d", "#19e07a"
JORD0, JORD1, BOLGE, ROYR = "#6b5138", "#2f2318", "#7fe9ff", "#ff9d3c"


def _arc(cx, cy, r):
    return f"M{cx - r} {cy} A{r} {r} 0 0 0 {cx + r} {cy}"


def radarvogn(detail=True):
    """Georadarvogna sett frå sida: raud kasse (radaren), hjul, handtak og mast med GNSS-antenne."""
    g = [f'<path d="M150 236 L196 270" stroke="{SKJER}" stroke-width="9" stroke-linecap="round"/>',          # handtak
         f'<rect x="138" y="228" width="22" height="9" rx="4" fill="{BELTE}"/>',
         f'<rect x="196" y="258" width="124" height="40" rx="9" fill="{RAUD}" stroke="{RAUD_MORK}" stroke-width="4"/>',
         f'<line x1="256" y1="258" x2="256" y2="150" stroke="{SKJER}" stroke-width="8" stroke-linecap="round"/>',  # mast
         f'<ellipse cx="256" cy="146" rx="30" ry="11" fill="{BELTE}" stroke="#ffffff" stroke-width="3"/>',          # antenne
         f'<circle cx="256" cy="140" r="5" fill="{GPS}"/>',
         f'<circle cx="214" cy="299" r="11" fill="{BELTE}" stroke="#5d6f7b" stroke-width="3"/>',
         f'<circle cx="306" cy="299" r="13" fill="{BELTE}" stroke="#5d6f7b" stroke-width="3"/>']
    if detail:
        g += [f'<rect x="210" y="266" width="96" height="12" rx="3" fill="#ec5048"/>',
              '<g stroke="#8f1717" stroke-width="3">' + "".join(
                  f'<line x1="{x}" y1="282" x2="{x}" y2="294"/>' for x in range(214, 306, 12)) + "</g>",
              f'<circle cx="214" cy="299" r="4" fill="#5d6f7b"/><circle cx="306" cy="299" r="5" fill="#5d6f7b"/>']
    return "".join(g)


def ikon(detail=True):
    flate = 312
    arcs = (44, 84, 124, 164) if detail else (60, 120)
    bolgjer = "".join(f'<path d="{_arc(256, flate + 4, r)}" fill="none" stroke="{BOLGE}" stroke-width="{7 if detail else 12}" '
                      f'stroke-opacity="{0.95 - i * 0.2:.2f}" stroke-linecap="round"/>' for i, r in enumerate(arcs))
    royr = (f'<circle cx="338" cy="438" r="20" fill="{ROYR}" stroke="#ffffff" stroke-width="4"/>'
            f'<circle cx="338" cy="438" r="8" fill="{JORD1}"/>') if detail else \
        f'<circle cx="340" cy="440" r="26" fill="{ROYR}" stroke="#ffffff" stroke-width="6"/>'
    lag = ('<path d="M0 372 C140 362 372 384 512 370" fill="none" stroke="#7d6248" stroke-width="3" stroke-opacity=".6"/>'
           '<path d="M0 430 C150 440 360 420 512 432" fill="none" stroke="#5a4430" stroke-width="3" stroke-opacity=".6"/>') if detail else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="natt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NATT0}"/><stop offset="1" stop-color="{NATT1}"/></linearGradient>
    <linearGradient id="sno" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SNO0}"/><stop offset="1" stop-color="{SNO1}"/></linearGradient>
    <linearGradient id="jord" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{JORD0}"/><stop offset="1" stop-color="{JORD1}"/></linearGradient>
    <clipPath id="ramme"><rect x="16" y="16" width="480" height="480" rx="108"/></clipPath>
  </defs>
  <rect x="16" y="16" width="480" height="480" rx="108" fill="url(#natt)"/>
  <g clip-path="url(#ramme)">
    <g transform="translate(46 54) scale(3.5)"><path d="{PEAKS}" fill="#ffffff"/>{'<path d="' + PEAK_CUT + '" fill="none" stroke="#123c5c" stroke-width="2.2" stroke-linejoin="round"/>' if detail else ''}</g>
    <path d="M0 {flate - 22} C120 {flate - 40} 392 {flate - 40} 512 {flate - 22} V{flate + 4} H0 Z" fill="url(#sno)"/>
    <rect x="0" y="{flate + 4}" width="512" height="{512 - flate}" fill="url(#jord)"/>
    {lag}{bolgjer}{royr}
    {radarvogn(detail)}
  </g>
  <rect x="16" y="16" width="480" height="480" rx="108" fill="none" stroke="#ffffff" stroke-opacity=".14" stroke-width="4"/>
</svg>
'''


def logo(tekst="#ffffff", under="#8cc8f0", aksent=BOLGE):
    """Logo med tekst – same oppbygging som snowman-logo.svg i Snødjupne, med GEOSCAN og opphavet under."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 190" width="420" height="190">
  <title>{NAMN} – {PRODUSENT}</title>
  <g transform="translate(138 2) scale(1.2)"><path d="{PEAKS}" fill="{tekst}"/><path d="{PEAK_CUT}" fill="none" stroke="#02141d" stroke-width="2.2" stroke-linejoin="round"/></g>
  <text x="210" y="100" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="64" letter-spacing="1" fill="{tekst}">SNOWMAN</text>
  <text x="210" y="142" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="36" letter-spacing="9" fill="{aksent}">GEOSCAN</text>
  <text x="210" y="176" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="17" fill="{under}">{PRODUSENT}</text>
</svg>
'''


def oppstart():
    """Oppstartbiletet: ikonet til venstre, logoen til høgre, på natthimmel."""
    ik = ikon(True).split("\n", 1)[1].rsplit("</svg>", 1)[0]
    lg = logo().split("\n", 1)[1].rsplit("</svg>", 1)[0]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 380" width="900" height="380">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NATT0}"/><stop offset="1" stop-color="{NATT1}"/></linearGradient></defs>
  <rect width="900" height="380" rx="24" fill="url(#bg)"/>
  <g transform="translate(36 34) scale(0.6)">{ik}</g>
  <g transform="translate(400 70) scale(1.12)">{lg}</g>
  <text x="620" y="350" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#8cc8f0">Startar …</text>
</svg>
'''


async def _render(svg, w, h):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": w, "height": h})
        await pg.set_content(f'<html><body style="margin:0;background:transparent">{svg.replace(f"width=", "data-w=", 1)}</body></html>')
        await pg.evaluate(f"(()=>{{const s=document.querySelector('svg');s.setAttribute('width',{w});s.setAttribute('height',{h})}})()")
        png = await pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h})
        await b.close()
        return png


def main():
    from PIL import Image
    full, enkel, lg = ikon(True), ikon(False), logo()
    (HER / "geoscan.svg").write_text(full, encoding="utf-8")
    (HER / "geoscan-enkel.svg").write_text(enkel, encoding="utf-8")
    (HER / "geoscan-logo.svg").write_text(lg, encoding="utf-8")
    web = HER.parent / "web" / "vendor"
    web.mkdir(parents=True, exist_ok=True)
    (web / "geoscan-logo.svg").write_text(lg, encoding="utf-8")
    (web / "geoscan-ikon.svg").write_text(full, encoding="utf-8")
    big = {s: asyncio.run(_render(full, s, s)) for s in (64, 256, 512)}
    small = {s: asyncio.run(_render(enkel, s, s)) for s in (16, 24, 32, 48)}
    (HER / "geoscan-256.png").write_bytes(big[256])
    (HER / "geoscan-512.png").write_bytes(big[512])
    (web / "geoscan-ikon.png").write_bytes(big[64])
    imgs = [Image.open(io.BytesIO(small[s])).convert("RGBA") for s in (16, 24, 32, 48)] + \
           [Image.open(io.BytesIO(big[s])).convert("RGBA") for s in (64, 256)]
    imgs[-1].save(HER / "geoscan.ico", sizes=[(i.width, i.height) for i in imgs], append_images=imgs[:-1])
    op = oppstart()
    (HER / "oppstart.svg").write_text(op, encoding="utf-8")
    (HER / "oppstart.png").write_bytes(asyncio.run(_render(op, 900, 380)))
    print("Laga:", ", ".join(sorted(p.name for p in HER.iterdir() if p.suffix in (".svg", ".png", ".ico"))))


if __name__ == "__main__":
    sys.exit(main())
