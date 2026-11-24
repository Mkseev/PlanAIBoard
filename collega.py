#!/usr/bin/env python3
"""Passo 3: legge SOLO le cartelle accese dall'utente e scrive collegamenti.json/.md (0 token, nessun modello, nessun invio).
Non entra mai in ciò che è nelle esclusioni; dei file di testo legge l'inizio, e nel risultato salva solo percorsi e legami, mai il contenuto."""
import collections, fnmatch, json, os, re
import scansione

QUI = os.path.dirname(os.path.abspath(__file__))
OUT_JSON, OUT_MD = os.path.join(QUI, "collegamenti.json"), os.path.join(QUI, "collegamenti.md")
TESTO = {".md", ".txt", ".rst", ".org"}
SALTA = {"node_modules", ".git", "__pycache__", "venv", ".venv", "Library", "Applications"}
MAX_FILE, MAX_SUB, MAX_LETTO, MAX_PROF = 5000, 300, 8192, 4   # MAX_SUB: una cartella enorme (es. 5000 file .tbx) non deve mangiare tutto il limite
GENERICI = {"readme", "index", "main", "license", "licence", "changelog", "todo", "notes", "note", "test", "tests", "config", "setup", "script", "scripts", "docs", "doc", "src", "lib", "app", "backup", "temp", "tmp", "new", "copia"}
RE_WIKI = re.compile(r"\[\[([^\]|#]{2,80})")


def escluso(p, escl, casa):
    rel = os.path.relpath(p, casa) if p.startswith(casa) else p
    parti = rel.split(os.sep)
    for e in escl:
        e = e.strip().strip("/")
        if "/" in e:
            if rel == e or rel.startswith(e + "/"):
                return True
        elif any(fnmatch.fnmatch(x, e) for x in parti):
            return True
    return False


def cammina(radice, escl, casa, tot, sub):
    base = radice.count(os.sep)
    for cur, dirs, files in os.walk(radice, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SALTA and not d.startswith(".") and not escluso(os.path.join(cur, d), escl, casa))
        if cur.count(os.sep) - base >= MAX_PROF:
            dirs[:] = []
        for f in sorted(files):
            p = os.path.join(cur, f)
            if f.startswith(".") or ".bak" in f or os.path.islink(p) or escluso(p, escl, casa):   # i backup sono copie, non legami
                continue
            if tot[0] >= MAX_FILE:
                return
            k = (radice, os.path.relpath(p, radice).split(os.sep)[0])
            sub[k] += 1
            if sub[k] > MAX_SUB:
                continue
            tot[0] += 1
            yield p


def collega(d):
    casa = os.path.expanduser("~")
    escl = d["esclusioni"]
    radici = [os.path.realpath(os.path.expanduser(c["percorso"])) for c in d["cartelle"] if c["leggi"]]
    radici = [r for r in radici if os.path.isdir(r) and not escluso(r, escl, os.path.realpath(casa))]
    casa = os.path.realpath(casa)
    tot, file_, estens, sub = [0], [], collections.Counter(), collections.Counter()
    for r in radici:
        for p in cammina(r, escl, casa, tot, sub):
            file_.append(p); estens[os.path.splitext(p)[1].lower() or "(senza)"] += 1
    progetti = sorted({os.path.relpath(p, r).split(os.sep)[0] for r in radici for p in file_ if p.startswith(r + os.sep) and os.sep in os.path.relpath(p, r)})
    def prog(p):
        r = next(r for r in radici if p.startswith(r + os.sep))
        return os.path.relpath(p, r).split(os.sep)[0]
    stessi = collections.defaultdict(list)
    for p in file_:
        stessi[os.path.splitext(os.path.basename(p))[0].lower()].append(p)
    # legame vero = stesso progetto e (formati diversi o copia nello stesso progetto); stesso nome in progetti diversi = rumore
    stessi = {k: v for k, v in stessi.items() if len(v) > 1 and len(k) > 3 and k not in GENERICI and len({prog(x) for x in v}) == 1}
    cit = collections.defaultdict(set)   # file -> cose citate
    stem = {os.path.splitext(os.path.basename(p))[0].lower(): p for p in file_}
    for p in file_:
        if os.path.splitext(p)[1].lower() not in TESTO:
            continue
        try:
            t = open(p, encoding="utf-8", errors="ignore").read(MAX_LETTO)
        except OSError:
            continue
        for w in RE_WIKI.findall(t):
            if w.strip().lower() in stem and stem[w.strip().lower()] != p:
                cit[p].add(stem[w.strip().lower()])
        for pr in progetti:
            if len(pr) >= 5 and pr.lower() not in GENERICI and re.search(r"\b" + re.escape(pr) + r"\b", t) and prog(p) != pr:   # maiuscole come il nome vero; mai verso il proprio progetto
                cit[p].add("progetto:" + pr)
    res = {"cartelle_lette": radici, "file_visti": len(file_), "limite_raggiunto": tot[0] >= MAX_FILE, "cartelle_troncate": sorted(k[1] for k, n in sub.items() if n > MAX_SUB), "tipi": dict(estens.most_common(10)),
           "progetti": progetti, "stessi_nomi": dict(sorted(stessi.items(), key=lambda kv: -len(kv[1]))[:30]),
           "citazioni": {k: sorted(v) for k, v in sorted(cit.items())[:200]}}
    json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(OUT_MD, "w", encoding="utf-8").write(markdown(res))
    return res


def markdown(r):
    m = ["# Collegamenti (generato, si rifà dalla pagina «Il tuo sistema»)\n", "Cartelle lette: " + (", ".join(r["cartelle_lette"]) or "nessuna"),
         "File visti: %d%s" % (r["file_visti"], " (limite raggiunto)" if r["limite_raggiunto"] else ""),
         ("Cartelle molto grandi, lette solo in parte: " + ", ".join(r["cartelle_troncate"]) + "\n") if r["cartelle_troncate"] else "",
         "## Progetti (sottocartelle)\n"] + ["- " + p for p in r["progetti"]] + ["\n## Stessi nomi in posti diversi (versioni o copie)\n"]
    m += ["- %s: %s" % (k, "; ".join(v)) for k, v in r["stessi_nomi"].items()]
    m += ["\n## Chi cita cosa\n"] + ["- %s → %s" % (k, ", ".join(v)) for k, v in r["citazioni"].items()]
    return "\n".join(m) + "\n"
