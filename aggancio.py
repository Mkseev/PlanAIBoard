#!/usr/bin/env python3
"""Passo 2: aggancia i programmi AI accesi al Pannello. Aggiunge UN blocco marcato al loro file di istruzioni
(prima fa il backup .bak-AAAAMMGG) che rimanda a memoria-pannello.md. Il blocco si toglie con annulla(); il resto del file non si tocca."""
import datetime, json, os, re, shutil, tempfile
import scansione

QUI = os.path.dirname(os.path.abspath(__file__))
REGOLE = os.path.join(QUI, "memoria-pannello.md")
LOG = os.path.join(QUI, "agganci.json")
IN, FI = "<!-- pannello-ai:inizio -->", "<!-- pannello-ai:fine -->"
RE_BLOCCO = re.compile(re.escape(IN) + r".*?" + re.escape(FI) + r"\n?", re.S)
# programma -> file di istruzioni che legge da solo (gli altri non sono ancora supportati)
FILE = {"claude": "~/.claude/CLAUDE.md", "opencode": "~/.config/opencode/AGENTS.md", "codex": "~/.codex/AGENTS.md", "gemini": "~/.gemini/GEMINI.md"}


def blocco():
    return "%s\nRegole del Pannello AI: leggi e segui %s (cartelle che puoi leggere e cose da non leggere mai).\n%s\n" % (IN, REGOLE, FI)


def testo_regole(d):
    ok = [c["percorso"] for c in d["cartelle"] if c["leggi"]]
    return ("# Regole del Pannello AI (generato, non modificare a mano: si cambia dalla pagina «Il tuo sistema»)\n\n"
            "## Cartelle che puoi leggere\n" + ("".join("- %s\n" % p for p in ok) or "- nessuna\n") +
            "\n## Da non leggere mai (in nessuna cartella)\n" + "".join("- %s\n" % e for e in d["esclusioni"]) +
            "\nSe un file o una cartella è in questo elenco, non aprirlo, non copiarlo, non citarlo.\n")


def _leggi(f):
    try:
        return open(f, encoding="utf-8").read()
    except FileNotFoundError:
        return None


def piano(d):
    """Elenco di cosa cambierebbe, senza scrivere niente."""
    righe = []
    for c in d["client"]:
        f = FILE.get(c["id"])
        r = {"id": c["id"], "nome": c["nome"], "file": os.path.realpath(os.path.expanduser(f)) if f else "", "anteprima": ""}
        if not f:
            r["azione"], r["nota"] = "niente", "nonsup"
        else:
            t = _leggi(r["file"]) or ""
            ha = IN in t
            if ha and FI not in t:
                r["azione"], r["nota"] = "errore", "rovinato"
            elif c["attivo"] and c["trovato"]:
                r["azione"] = "niente" if (ha and blocco() in t) else ("aggiorna" if ha else "aggiungi")
                r["anteprima"] = blocco()
            else:
                r["azione"] = "togli" if ha else "niente"
        righe.append(r)
    return righe


def _scrivi(f, t):
    os.makedirs(os.path.dirname(f), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(f)); os.write(fd, t.encode()); os.close(fd)
    if os.path.exists(f): shutil.copymode(f, tmp)
    os.replace(tmp, f)


def applica(d):
    """Esegue il piano. Backup del file (uno al giorno, non sovrascrive) prima di toccarlo. Scrive anche memoria-pannello.md."""
    esiti, log = [], (json.load(open(LOG)) if os.path.exists(LOG) else [])
    for r in piano(d):
        if r["azione"] in ("niente", "errore"):
            esiti.append(r); continue
        f = r["file"]; t = _leggi(f)
        if t is not None:
            bak = f + ".bak-" + datetime.date.today().strftime("%Y%m%d")
            if not os.path.exists(bak): shutil.copy2(f, bak)
            r["backup"] = bak
        nuovo = RE_BLOCCO.sub("", t or "")
        if r["azione"] != "togli":
            nuovo = nuovo + ("" if nuovo.endswith("\n") or not nuovo else "\n") + blocco()
        _scrivi(f, nuovo)
        log.append({"id": r["id"], "file": f, "azione": r["azione"], "quando": datetime.datetime.now().isoformat(timespec="seconds"), "backup": r.get("backup", "")})
        esiti.append(r)
    _scrivi(REGOLE, testo_regole(d)); json.dump(log, open(LOG, "w"), indent=2)
    return esiti


def annulla(d):
    """Toglie il blocco da ogni file in cui c'è (anche se il programma ora è spento)."""
    d = json.loads(json.dumps(d))
    for c in d["client"]: c["attivo"] = False
    return applica(d)
