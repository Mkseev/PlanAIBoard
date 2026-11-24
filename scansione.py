#!/usr/bin/env python3
"""Guarda il PC (solo esistenza di file/cartelle, mai il contenuto) e scrive impostazioni.json.
Ripassando, tutto ciò che l'utente ha cambiato resta: interruttori, nomi, colori, comandi, cartelle, esclusioni, aspetto."""
import json, os, platform, shutil

H = os.path.expanduser("~")
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "impostazioni.json")
# id, nome, comando da cercare, cartella di configurazione, colore
CLIENT = [("claude", "Claude Code", "claude", "~/.claude", "#d97757"), ("opencode", "OpenCode", "opencode", "~/.config/opencode", "#3b82f6"),
          ("codex", "Codex", "codex", "~/.codex", "#10a37f"), ("gemini", "Gemini CLI", "gemini", "~/.gemini", "#8b5cf6"),
          ("cursor", "Cursor", "cursor", "~/.cursor", "#64748b"), ("copilot", "GitHub Copilot CLI", "copilot", "~/.copilot", "#475569")]
CARTELLE = ["~/Desktop", "~/Documents", "~/Documenti", "~/Projects", "~/Progetti", "~/code", "~/dev", "~/src"]
ESCLUSIONI = [".env", "*.pem", "*.key", ".ssh", ".aws", ".gnupg", "Library/Keychains", "Library/Application Support/Google/Chrome",
              "Library/Messages", "Library/Mail", "AppData/Local/Google/Chrome", ".mozilla"]
ASPETTO = {"titolo": "PlanAIBoard", "tema": "auto", "colore": "#3ddc97", "lingua": "auto"}   # primo avvio: neutro, lingua del computer


def rileva(c):
    """Cerca il programma per comando o per cartella di configurazione; riempie trovato e percorso."""
    cfg = os.path.expanduser(c.get("cartella", "")) if c.get("cartella") else ""
    p = (shutil.which(c["comando"]) if c.get("comando") else None) or (cfg if cfg and os.path.isdir(cfg) else "")
    c["trovato"], c["percorso"] = bool(p), p
    return c


def trova():
    client = [rileva({"id": i, "nome": n, "comando": cmd, "cartella": cfg, "colore": col, "custom": False, "attivo": False}) for i, n, cmd, cfg, col in CLIENT]
    cartelle = [{"percorso": c, "leggi": False} for c in CARTELLE if os.path.isdir(os.path.expanduser(c))]
    return {"sistema": {"os": platform.system(), "versione": platform.release(), "home": H, "python": platform.python_version()},
            "aspetto": dict(ASPETTO), "moduli": {}, "client": client, "cartelle": cartelle, "esclusioni": list(ESCLUSIONI)}


def unisci(nuovo, vecchio):
    """Le scelte dell'utente vincono; dal PC arrivano solo «trovato» e «percorso», e i programmi nuovi."""
    vec = {c["id"]: c for c in vecchio.get("client", [])}
    for c in nuovo["client"]:
        if c["id"] in vec:
            c.update({k: v for k, v in vec[c["id"]].items() if k not in ("trovato", "percorso")})
            rileva(c)
            if not c["trovato"]:
                c["attivo"] = False
    visti = {c["id"] for c in nuovo["client"]}
    nuovo["client"] += [rileva(c) for i, c in vec.items() if i not in visti]   # quelli aggiunti a mano
    nuovo["aspetto"].update({k: v for k, v in vecchio.get("aspetto", {}).items() if k in ASPETTO})
    nuovo["moduli"] = vecchio.get("moduli", {})
    gia = {c["percorso"] for c in nuovo["cartelle"]}
    vc = {c["percorso"]: c for c in vecchio.get("cartelle", [])}
    nuovo["cartelle"] = [vc.get(c["percorso"], c) for c in nuovo["cartelle"]] + [c for p, c in vc.items() if p not in gia]
    if "esclusioni" in vecchio:
        nuovo["esclusioni"] = vecchio["esclusioni"]
    return nuovo


def carica():
    try:
        return json.load(open(FILE, encoding="utf-8"))
    except Exception:
        return {}


def scansiona():
    dati = unisci(trova(), carica())
    json.dump(dati, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return dati


if __name__ == "__main__":
    print(json.dumps(scansiona(), ensure_ascii=False, indent=2))
