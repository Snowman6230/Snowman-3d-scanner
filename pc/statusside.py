# Snowman Geoscan – Alpindata v/Hans Petter B. Sørensen. Copyright © 2026. Alle rettar reserverte.
"""Statusside for operatøren i Snowman Geoscan: http://localhost:8088 (berre på denne PC-en, med mindre status_lan er sett).
Viser fix, helling, forskyving, NTRIP og portar. Oppdaterer seg kvart sekund. /status gir JSON."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SIDE = """<!doctype html><html lang="nn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Snowman Geoscan</title>
<style>
:root{--bg:#0f1418;--kort:#1a2228;--tekst:#e8eef2;--svak:#8a9aa6;--ok:#3ecf74;--var:#f2b33d;--feil:#ef5b5b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tekst);font:16px/1.4 system-ui,sans-serif;padding:16px}
h1{font-size:22px;margin:0;color:var(--tekst);font-weight:700}
.prod{color:var(--svak);font-size:13px;margin:2px 0 14px}
.rad{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.k{background:var(--kort);border-radius:10px;padding:14px}
.l{color:var(--svak);font-size:13px;text-transform:uppercase;letter-spacing:.06em}
.v{font-size:34px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:4px}
.s{color:var(--svak);font-size:14px;margin-top:4px}
.ok{color:var(--ok)}.var{color:var(--var)}.feil{color:var(--feil)}
svg{display:block;margin:6px auto 0}
pre{white-space:pre-wrap;color:var(--svak);font-size:13px;margin:0}
</style></head><body>
<h1>Snowman Geoscan <span id="ver" style="font-weight:400;color:var(--svak);font-size:15px"></span></h1>
<div class="prod">Alpindata v/Hans Petter B. Sørensen</div>
<div class="k" id="demo" style="display:none;margin-bottom:12px;background:#5a1f1f;color:#fff;font-weight:700">DEMO – simulert mottakar og NTRIP-caster. Dette er ikkje ekte målingar.</div>
<div class="k" id="oppd" style="display:none;margin-bottom:12px;border:1px solid var(--var)">
 <span id="otekst"></span> <button id="obtn" onclick="oppdater()" style="margin-left:8px;padding:6px 14px;border-radius:6px;border:0;background:var(--var);color:#111;font-weight:700;cursor:pointer">Oppdater no</button>
 <pre id="ologg" style="margin-top:8px"></pre></div>
<div class="rad">
 <div class="k"><div class="l">Fix</div><div class="v" id="fix">–</div><div class="s" id="sat"></div></div>
 <div class="k"><div class="l">Helling</div><div class="v" id="hell">–</div><div class="s" id="hsrc"></div>
   <svg width="120" height="70" viewBox="-60 -35 120 70"><line x1="-55" y1="25" x2="55" y2="25" stroke="#2c3a44" stroke-width="2"/>
   <g id="vogn"><rect x="-40" y="10" width="80" height="14" rx="3" fill="#3b4b57"/><line x1="0" y1="10" x2="0" y2="-28" stroke="#8a9aa6" stroke-width="3"/><circle cx="0" cy="-30" r="5" fill="#e8eef2"/></g></svg></div>
 <div class="k"><div class="l">Retting no</div><div class="v" id="fors">–</div><div class="s" id="djup"></div></div>
 <div class="k"><div class="l">NTRIP</div><div class="v" id="ntrip" style="font-size:22px">–</div><div class="s" id="nmeld"></div></div>
 <div class="k" style="grid-column:1/-1"><div class="l">Portar</div><pre id="portar"></pre></div>
</div>
<script>
const FIX={0:["INGEN","feil"],1:["GPS","feil"],2:["DGPS","var"],4:["RTK FIX","ok"],5:["RTK FLOAT","var"],6:["INS","var"],9:["SBAS","var"]};
const F=(x,d)=>x.toFixed(d).replace(".",",");
function set(id,t,c){const e=document.getElementById(id);e.textContent=t;e.className=e.className.replace(/ ?(ok|var|feil)/g,"")+(c?" "+c:"")}
async function tikk(){try{const s=await (await fetch("status")).json(),k=s.korr;
 const f=FIX[k.fix]||[k.fix==null?"–":"FIX "+k.fix,"var"];set("fix",f[0],f[1]);set("sat",(k.sats||"–")+" satellittar · data "+(s.gnss_alder==null?"–":F(s.gnss_alder,1)+" s"));
 if(k.korrigert){set("hell",(k.krenging>0?"+":"")+F(k.krenging,1)+"°",Math.abs(k.krenging)>5||Math.abs(k.stamp)>5?"var":"ok");
  set("hsrc","krenging · stamp "+F(k.stamp,1)+"° · "+k.hellingskjelde);document.getElementById("vogn").setAttribute("transform","rotate("+k.krenging+" 0 24)")}
 else{set("hell","–","var");set("hsrc",k.melding)}
 set("fors",k.forskyving_cm==null?"–":F(k.forskyving_cm,1)+" cm");
 set("djup",s.djupnfeil_25==null?"":"objekt på 2,5 m: "+s.djupnfeil_25.toFixed(0)+" cm (blir retta etterpå)");
 const n=s.ntrip;set("ntrip",n.tilstand,n.tilstand=="tilkopla"?"ok":n.tilstand=="av"?"":"feil");
 set("nmeld",n.tilstand=="tilkopla"?(n.protokoll+" · "+(n.byte/1024).toFixed(0)+" kB · alder "+(n.alder==null?"–":n.alder.toFixed(0)+" s")):n.melding);
 visOppd(s.oppdatering);document.getElementById("demo").style.display=s.demo?"block":"none";document.getElementById("portar").textContent=Object.entries(s.inn).map(([p,v])=>"inn "+p+": "+v).concat(s.ut.map(o=>"ut "+o.port+": "+(o.feil||"ok")),["TCP "+s.tcp_port+": "+s.tcp_klientar+" klientar"]).join("\\n")
}catch(e){set("fix","ikkje kontakt","feil")}}
async function oppdater(){if(!confirm("Hente og leggje inn ny versjon? Geoscan startar på nytt."))return;
 document.getElementById("obtn").disabled=true;try{await fetch("oppdater",{method:"POST"})}catch(e){}}
function visOppd(o){document.getElementById("ver").textContent="v"+o.lokal;const b=document.getElementById("oppd");
 const vis=o.nyare||o.koyrer||o.logg.length;b.style.display=vis?"block":"none";
 document.getElementById("otekst").textContent=o.koyrer?"Oppdaterer …":o.omstart?"Ny versjon lagd inn – startar på nytt …":o.nyare?"Ny versjon v"+o.github+" finst.":"";
 document.getElementById("obtn").style.display=o.nyare&&!o.koyrer&&!o.omstart?"inline-block":"none";
 document.getElementById("ologg").textContent=o.logg.join("\\n")}
setInterval(tikk,1000);tikk();
</script></body></html>"""


def start(app, port=8088, lan=False):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path.startswith("/status"):
                body, typ = json.dumps(app.snapshot(), ensure_ascii=False).encode(), "application/json"
            elif self.path in ("/", "/index.html"):
                body, typ = SIDE.encode(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", typ)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            # Berre frå denne PC-en: ingen kan starte ei oppdatering frå nettet sjølv om status_lan er på
            if self.path != "/oppdater" or self.client_address[0] not in ("127.0.0.1", "::1"):
                self.send_error(403)
                return
            threading.Thread(target=app.run_update, daemon=True).start()
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()

    srv = ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
