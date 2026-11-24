#!/usr/bin/env python3
"""Pagina «Il tuo sistema»: server locale solo 127.0.0.1:20150. Mostra impostazioni.json e lo salva quando l'utente modifica."""
import glob, json, os, re, secrets, shutil, subprocess, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import scansione, aggancio, collega, assistente

PORTA = int(os.environ.get("PORTA_SISTEMA", 20150))
GETTONE = secrets.token_hex(16)
QUI = os.path.dirname(os.path.abspath(__file__))


def valido(d):
    """Accetta solo la forma attesa: l'utente non deve poter rompere il file dalla pagina."""
    hx = lambda x: isinstance(x, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", x)
    try:
        return (all(isinstance(c["id"], str) and c["id"].strip() and isinstance(c["nome"], str) and c["nome"].strip() and isinstance(c["attivo"], bool)
                    and hx(c["colore"]) and isinstance(c["comando"], str) and isinstance(c["cartella"], str) for c in d["client"])
                and len({c["id"] for c in d["client"]}) == len(d["client"])
                and all(isinstance(c["percorso"], str) and c["percorso"].strip() and isinstance(c["leggi"], bool) for c in d["cartelle"])
                and all(isinstance(e, str) and e.strip() for e in d["esclusioni"])
                and d["aspetto"]["tema"] in ("auto", "chiaro", "scuro") and hx(d["aspetto"]["colore"])
                and isinstance(d["aspetto"]["titolo"], str) and 0 < len(d["aspetto"]["titolo"].strip()) <= 40
                and re.fullmatch(r"auto|[a-z]{2,3}", d["aspetto"]["lingua"]) and isinstance(d.get("moduli", {}), dict) and all(k in rilevati() and isinstance(v, bool) for k, v in d.get("moduli", {}).items()))
    except Exception:
        return False


def sfoglia(p, nascoste=False):
    """Sottocartelle di p (solo nomi, mai file), sempre dentro la cartella personale: serve al pulsante «Scegli cartella»."""
    casa = os.path.realpath(os.path.expanduser("~"))
    q = os.path.realpath(os.path.expanduser(p))
    if q != casa and not q.startswith(casa + os.sep):
        q = casa
    try:
        nomi = sorted(n for n in os.listdir(q) if (nascoste or not n.startswith(".")) and n not in scansione.ESCLUSIONI and os.path.isdir(os.path.join(q, n)))
    except OSError:
        nomi = []
    vis = lambda x: "~" + x[len(casa):] if x.startswith(casa) else x
    return {"percorso": vis(q), "su": vis(os.path.dirname(q)) if q != casa else "", "cartelle": nomi}


GIRO = 'tell application "System Events"\nactivate\nPOSIX path of (choose folder with prompt "Scegli una cartella")\nend tell'


def scegli_mac():
    """Apre il selettore cartelle vero di macOS (il server gira sul Mac dell'utente). ok=False + annullato se chiude la finestra; ok=False senza annullato se non è un Mac."""
    if sys.platform != "darwin":
        return {"ok": False}
    try:
        r = subprocess.run(["/usr/bin/osascript", "-e", GIRO], capture_output=True, text=True, timeout=300)
    except Exception:
        return {"ok": False}
    if r.returncode != 0:
        return {"ok": False, "annullato": "-128" in r.stderr}
    casa = os.path.expanduser("~")
    q = r.stdout.strip().rstrip("/") or "/"
    return {"ok": True, "percorso": "~" + q[len(casa):] if q == casa or q.startswith(casa + "/") else q}


APRIBILI = {}   # lo imposta il Pannello: file/indirizzi che i suoi pulsanti «Apri» sanno aprire


def _regola(r):
    """Una regola di rilevamento: cartella | file | comando | glob | qualsiasi:[...] | tutte:[...] | sempre."""
    p = lambda x: os.path.expanduser(x)
    if "cartella" in r: return os.path.isdir(p(r["cartella"]))
    if "file" in r: return os.path.exists(p(r["file"]))
    if "comando" in r: return bool(shutil.which(r["comando"]))
    if "glob" in r: return bool(glob.glob(p(r["glob"])))
    if "qualsiasi" in r: return any(_regola(x) for x in r["qualsiasi"])
    if "tutte" in r: return all(_regola(x) for x in r["tutte"])
    return r.get("sempre") is True


def carica_moduli():
    """Legge moduli/*.json: ogni modulo dice da solo cosa serve per comparire. Un file rotto viene ignorato."""
    out = []
    for f in sorted(glob.glob(QUI + "/moduli/*.json")):
        try:
            m = json.load(open(f, encoding="utf-8"))
            if isinstance(m.get("id"), str) and re.fullmatch(r"[a-z0-9\-]{2,30}", m["id"]) and isinstance(m.get("rileva"), dict): out.append(m)
        except Exception:
            pass
    return out


def rilevati():
    """Cosa c'è DAVVERO su questo PC, modulo per modulo."""
    return {m["id"]: _regola(m["rileva"]) for m in carica_moduli()}


def moduli(d):
    """{modulo: {presente, attivo, nome, descrizione}}: attivo = presente e non spento dall'utente (il predefinito lo decide il modulo)."""
    sc = d.get("moduli", {}); out = {}
    for m in carica_moduli():
        pres = _regola(m["rileva"])
        out[m["id"]] = {"presente": pres, "attivo": pres and bool(sc.get(m["id"], m.get("predefinito", True))), "nome": m.get("nome", m["id"]), "descrizione": m.get("descrizione", {})}
    return out


def apri_ok():
    """Chiavi dei pulsanti «Apri» il cui file esiste davvero su questo PC (gli indirizzi web non si controllano: restano nascosti)."""
    return [k for k, v in APRIBILI.items() if not v.startswith("http") and os.path.exists(v)]


def _lingue():
    return [os.path.basename(f)[:-5] for f in sorted(glob.glob(QUI + "/lingue/*.json"))]


def _assistente(path, d):
    """Assistente di configurazione: rileva le IA, mostra cosa verrebbe inviato, chiede il suggerimento, applica le voci scelte."""
    dati = scansione.scansiona()
    r = assistente.riassunto(dati, [k for k, v in rilevati().items() if v and k != "aspetto"], _lingue())
    if path == "/assistente/rileva": return 200, json.dumps({"ia": assistente.rileva()})
    if path == "/assistente/anteprima":
        return 200, json.dumps({"riassunto": r, "prompt": assistente.prompt(r), "comando": assistente.comando(d.get("ia", ""))})
    if path == "/assistente/chiedi":
        if d.get("consenso") is not True: return 400, '{"ok":false}'
        ia = next((x for x in assistente.rileva() if x["id"] == d.get("ia")), None)   # solo una IA che il Pannello ha appena trovato
        if not ia: return 200, json.dumps({"ok": False, "errore": "ia"})
        mod = d.get("modello") if d.get("modello") in ia["modelli"] else (ia["modelli"][0] if ia["modelli"] else "")
        try: ris = assistente.chiedi(ia["id"], mod, assistente.prompt(r))
        except Exception: return 200, json.dumps({"ok": False, "errore": "risposta"})
        p = assistente.proposte(ris, r, dati)
        return 200, json.dumps(dict(p, ok=True) if p else {"ok": False, "errore": "formato"})
    if path == "/assistente/applica":
        voci = d.get("voci"); copia = json.loads(json.dumps(dati))
        n = assistente.applica(copia, voci if isinstance(voci, list) else [], r)
        if not valido(copia): return 400, '{"ok":false}'
        json.dump(copia, open(scansione.FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 200, json.dumps({"ok": True, "applicate": n})
    return 404, "{}"


TIPI_SCHEDA = ("cartella", "file", "link", "nota")
SCRIPT = {".command", ".sh", ".zsh", ".bash", ".tool", ".terminal", ".scpt", ".workflow", ".jar"}   # questi non si aprono: si mostrano nel Finder


def schede_valide(l):
    """Lista di schede dell'utente: forma controllata, mai altro nel file."""
    try:
        return (isinstance(l, list) and len(l) <= 60 and len({c["id"] for c in l}) == len(l)
                and all(re.fullmatch(r"[a-z0-9]{4,16}", c["id"]) and c["tipo"] in TIPI_SCHEDA
                        and isinstance(c["titolo"], str) and 0 < len(c["titolo"].strip()) <= 60
                        and isinstance(c["valore"], str) and 0 < len(c["valore"]) <= 2000
                        and (c["tipo"] != "link" or re.match(r"https?://", c["valore"])) for c in l))
    except Exception:
        return False


def schede_info():
    """Schede salvate + cosa si può dire di ognuna (esiste? quanti elementi): solo nomi, mai contenuti."""
    out = []
    for c in scansione.carica().get("schede", []):
        c = dict(c)
        if c.get("tipo") in ("cartella", "file"):
            p = os.path.expanduser(c["valore"]); c["esiste"] = os.path.exists(p)
            if c["tipo"] == "cartella" and c["esiste"]:
                try: c["elementi"] = len([n for n in os.listdir(p) if not n.startswith(".")])
                except OSError: c["elementi"] = None
        out.append(c)
    return out


def apri_scheda(i):
    """Apre una scheda SALVATA dall'utente (mai un percorso arrivato da fuori)."""
    c = next((c for c in scansione.carica().get("schede", []) if c.get("id") == i), None)
    if not c or sys.platform != "darwin" or c["tipo"] == "nota": return {"ok": False}
    try:
        if c["tipo"] == "link": subprocess.run(["/usr/bin/open", c["valore"]], timeout=10); return {"ok": True}
        p = os.path.expanduser(c["valore"])
        if not os.path.exists(p): return {"ok": False}
        subprocess.run(["/usr/bin/open"] + (["-R"] if os.path.splitext(p)[1].lower() in SCRIPT else []) + [p], timeout=10); return {"ok": True}
    except Exception:
        return {"ok": False}


def azione(d):
    """Azioni rapide generate dal PC: apre un file del Pannello o avvia, in Terminale, un programma trovato e acceso dall'utente."""
    casa = {"impostazioni": scansione.FILE, "collegamenti": collega.OUT_MD, "cartella": QUI}
    if sys.platform != "darwin":
        return {"ok": False}
    try:
        if d.get("tipo") == "file" and d.get("chiave") in casa and os.path.exists(casa[d["chiave"]]):
            subprocess.run(["/usr/bin/open", casa[d["chiave"]]], timeout=10); return {"ok": True}
        if d.get("tipo") == "scheda": return apri_scheda(d.get("id"))
        if d.get("tipo") == "programma":
            c = next((c for c in scansione.scansiona()["client"] if c["id"] == d.get("id")), None)
            if c and c["trovato"] and c["attivo"] and re.fullmatch(r"[A-Za-z0-9_.\-]{1,40}", c["comando"] or ""):   # solo un nome di comando, mai una riga di shell
                subprocess.run(["/usr/bin/osascript", "-e", 'tell application "Terminal"\nactivate\ndo script "%s"\nend tell' % c["comando"]], timeout=15); return {"ok": True}
    except Exception:
        pass
    return {"ok": False}


def get(path, gettone):
    """Rotte GET della configurazione: (codice, corpo, tipo) oppure None se non è una nostra rotta."""
    if path in ("/impostazioni", "/sistema.html"):
        return 200, open(QUI + "/sistema.html", encoding="utf-8").read().replace("__GETTONE__", gettone), "text/html"
    if path.startswith("/sfoglia"):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        return 200, json.dumps(sfoglia(q.get("p", ["~"])[0], q.get("n", ["0"])[0] == "1")), "application/json"
    if path == "/logo.png":
        return 200, open(QUI + "/logo.png", "rb").read(), "image/png"
    if path == "/dati":
        return 200, json.dumps(dict(scansione.scansiona(), moduli=moduli(scansione.carica()), apri=apri_ok(), cartella=QUI)), "application/json"
    if path == "/i18n.js":
        return 200, open(QUI + "/i18n.js", encoding="utf-8").read(), "application/javascript"
    if path == "/lingue":
        out = []
        for f in sorted(glob.glob(QUI + "/lingue/*.json")):
            try: out.append({"codice": os.path.basename(f)[:-5], "nome": json.load(open(f, encoding="utf-8")).get("_nome", os.path.basename(f)[:-5])})
            except Exception: pass   # un file di lingua rotto non deve rompere la pagina
        return 200, json.dumps(out), "application/json"
    if path.startswith("/lingua?"):
        c = urllib.parse.parse_qs(urllib.parse.urlparse(path).query).get("c", [""])[0]
        f = QUI + "/lingue/" + c + ".json"
        if re.fullmatch(r"[a-z]{2,3}", c) and os.path.isfile(f): return 200, open(f, encoding="utf-8").read(), "application/json"
        return 404, "{}", "application/json"
    if path == "/riassunto":
        d = scansione.scansiona()   # sempre unito ai dati del PC: regge anche un impostazioni.json scritto a mano e incompleto
        try: col = json.load(open(collega.OUT_JSON, encoding="utf-8"))
        except Exception: col = None
        agg = {r["id"] for r in aggancio.piano(d) if r["azione"] == "niente" and r["anteprima"]}
        return 200, json.dumps({"programmi": [{"id": c["id"], "nome": c["nome"], "colore": c["colore"], "attivo": c["attivo"], "trovato": c["trovato"], "agganciato": c["id"] in agg, "avviabile": bool(re.fullmatch(r"[A-Za-z0-9_.\-]{1,40}", c["comando"] or ""))} for c in d["client"]],
                                "cartelle": sum(1 for c in d["cartelle"] if c["leggi"]), "aspetto": d["aspetto"],
                                "schede": schede_info(), "collegamenti": {"file": col["file_visti"], "progetti": len(col["progetti"])} if col else None, "ha_collegamenti": os.path.exists(collega.OUT_MD), "moduli": moduli(d), "apri": apri_ok()}), "application/json"


def post(path, d):
    """Rotte POST (il chiamante ha già controllato origine e gettone): (codice, corpo) oppure None."""
    if path in ("/aggancia/piano", "/aggancia/applica", "/aggancia/annulla"):
        dati = scansione.carica()   # sempre il file salvato: la pagina salva prima di chiedere
        if path.endswith("piano"): return 200, json.dumps(aggancio.piano(dati))
        if d.get("conferma") is not True: return 400, '{"ok":false}'
        return 200, json.dumps(aggancio.applica(dati) if path.endswith("applica") else aggancio.annulla(dati))
    if path.startswith("/assistente/"): return _assistente(path, d)
    if path == "/sistema/azione": return 200, json.dumps(azione(d))
    if path == "/collega": return 200, json.dumps(collega.collega(scansione.carica()))
    if path == "/scegli": return 200, json.dumps(scegli_mac())
    if path == "/riscansiona": return 200, json.dumps(scansione.scansiona())
    if path == "/schede/salva":
        if not schede_valide(d.get("schede")): return 400, '{"ok":false}'
        vec = scansione.carica(); vec["schede"] = d["schede"]
        json.dump(vec, open(scansione.FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 200, '{"ok":true}'
    if path == "/salva":
        if not valido(d): return 400, '{"ok":false}'
        vec = scansione.carica(); vec.update({k: d[k] for k in ("client", "cartelle", "esclusioni", "aspetto", "moduli") if k in d})
        json.dump(vec, open(scansione.FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 200, '{"ok":true}'


class G(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _ok(self):
        return self.headers.get("Host") in ("127.0.0.1:%d" % PORTA, "localhost:%d" % PORTA) and \
            self.headers.get("Origin") in (None, "http://127.0.0.1:%d" % PORTA, "http://localhost:%d" % PORTA)

    def _manda(self, cod, corpo, tipo="application/json"):
        b = corpo if isinstance(corpo, bytes) else corpo.encode(); self.send_response(cod)
        self.send_header("Content-Type", tipo + "; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if not self._ok(): return self._manda(403, "{}")
        if self.path == "/":
            return self._manda(200, open(QUI + "/base.html", encoding="utf-8").read().replace("__GETTONE__", GETTONE), "text/html")
        r = get(self.path, GETTONE)
        self._manda(*(r or (404, "{}")))

    def do_POST(self):
        if not self._ok() or self.headers.get("X-Gettone") != GETTONE: return self._manda(403, '{"ok":false}')
        try: d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        except Exception: return self._manda(400, '{"ok":false}')
        r = post(self.path, d)
        self._manda(*(r or (404, "{}")))


if __name__ == "__main__":
    for PORTA in range(PORTA, PORTA + 10):   # se la porta è occupata prova la successiva
        try: srv = ThreadingHTTPServer(("127.0.0.1", PORTA), G); break
        except OSError: pass
    else: sys.exit("Nessuna porta libera tra %d e %d" % (PORTA - 9, PORTA))
    print("Apri http://127.0.0.1:%d" % PORTA)
    if os.environ.get("NO_APRI") != "1": __import__("threading").Timer(1, lambda: __import__("webbrowser").open("http://127.0.0.1:%d" % PORTA)).start()
    srv.serve_forever()
