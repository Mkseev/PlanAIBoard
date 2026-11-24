# PlanAIBoard — guide for AI agents

This page is written for an AI agent (Claude Code, Codex, Gemini CLI, OpenCode…) that was asked to **understand, configure or customize** PlanAIBoard on a user's Mac. A human can read it too.

**Ground rules (follow them):** ask the user before changing anything · change one thing at a time · back up a file before editing it · never read or print passwords, keys, tokens or `.env` files · never send file contents anywhere.

---

## 1. What it is

A tiny local web app (Python 3 standard library, no dependencies). It serves a page on `http://127.0.0.1:20150` and keeps its state in plain files next to the code. It does **not** run models and does **not** send anything out. Its job:

1. keep an **inventory** of the AI programs on this Mac,
2. keep **one rule list** (folders that may be read, patterns never to read),
3. **push that rule list to the AI programs** by adding one pointer block to their instructions file,
4. build a **map of the user's projects** from the folders the user allows.

## 2. Files (all in the PlanAIBoard folder)

| File | Role | Edit it? |
|---|---|---|
| `impostazioni.json` | The user's settings (see §3). Created on first run. | **Yes** — this is the main way to configure. |
| `memoria-pannello.md` | Generated rules file the hooked tools read. | No, regenerated from settings. |
| `agganci.json` | Log of what was hooked, used by Undo. | No. |
| `collegamenti.md` / `.json` | Generated project map. | No. |
| `moduli/*.json` | Optional features (see §5). | Yes, add files. |
| `lingue/xx.json` | Translations (see §6). | Yes, add files. |
| `base.html`, `sistema.html` | The two pages (plain HTML + JS, one file each). | Yes, for look-and-feel changes. |
| `sistema.py`, `scansione.py`, `aggancio.py`, `collega.py`, `assistente.py` | Server and logic. | Only if you must; keep changes small. |

## 3. `impostazioni.json`

```json
{
  "aspetto":   { "titolo": "PlanAIBoard", "tema": "auto", "colore": "#3ddc97", "lingua": "auto" },
  "client":    [ { "id": "claude", "nome": "Claude Code", "comando": "claude",
                   "cartella": "~/.claude", "colore": "#d97757", "custom": false,
                   "attivo": true, "trovato": true, "percorso": "/path/to/claude" } ],
  "cartelle":  [ { "percorso": "~/Projects", "leggi": true } ],
  "esclusioni":[ ".env", "*.pem", ".ssh" ],
  "moduli":    { }
}
```

Validation (the server rejects anything else when saving from the page):

- `client[]`: `id` unique non-empty string; `nome` non-empty; `attivo` boolean; `colore` `#rrggbb`; `comando` and `cartella` strings. `trovato`/`percorso` are recomputed by the scan.
- `cartelle[]`: `percorso` non-empty string (`~` allowed), `leggi` boolean. Only `leggi: true` folders are ever read.
- `esclusioni[]`: non-empty strings (names or simple patterns). They apply to **every** folder and are written into the rules file.
- `aspetto`: `tema` is `auto`, `chiaro` or `scuro` (Italian words); `colore` `#rrggbb`; `titolo` 1–40 chars; `lingua` is `auto` or a code that has a file in `lingue/`.
- `moduli`: object `{ moduleId: true|false }`.

Known programs are detected by command name or config folder: Claude Code (`claude`), OpenCode, Codex, Gemini CLI, Cursor, GitHub Copilot CLI, Ollama. To teach it another one, add an object to `client` with `"custom": true`, your own `id`, `nome`, `comando`, `cartella`, `colore`, `attivo`. A custom program is listed and can be switched on/off; it can only be **hooked** if it is one of the four below.

After editing the file by hand, reload the page (or press **Search the PC again**; your choices are kept).

## 4. How the AI hook works

For each program that is **found and switched on**, PlanAIBoard can add exactly one block to that program's instructions file:

| Program | File |
|---|---|
| Claude Code | `~/.claude/CLAUDE.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Codex | `~/.codex/AGENTS.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |

(Cursor, Copilot CLI and Ollama are detected and listed but not hookable: Ollama has no instructions file; it works as the local AI of the setup assistant.)

The block is delimited by `<!-- pannello-ai:inizio -->` and `<!-- pannello-ai:fine -->` and contains one sentence telling the tool to read and follow `memoria-pannello.md`. That rules file is generated from the settings: the folders with `leggi: true` and the whole `esclusioni` list, plus "if a file or folder is in this list, do not open, copy or quote it".

Safety properties: the plan is shown first (**Show what will change**); before writing, a copy `<file>.bak-YYYYMMDD` is made; only the marked block is touched; **Undo hook-up** removes the block and nothing else. These are *instructions the tools read*, not a sandbox: they make the user's intent explicit and shared, they do not technically prevent a read.

To hook from a script instead of the page, `python3 -c "import aggancio, scansione; print(aggancio.piano(scansione.carica()))"` (from the PlanAIBoard folder) prints the plan without writing. `aggancio.applica(...)` / `aggancio.annulla(...)` do the real work; **ask the user first**.

## 5. Modules (optional features)

A module is one JSON file in `moduli/`:

```json
{ "id": "my-feature", "nome": "My feature", "descrizione": { "it": "Cos'è", "en": "What it is" },
  "rileva": { "comando": "ollama" }, "predefinito": true }
```

- `id`: 2–30 chars of `a-z 0-9 -`. `descrizione` is keyed by language code; `it` is the fallback.
- `rileva` (detection rule) is one of: `{ "cartella": "~/x" }`, `{ "file": "~/x/y" }`, `{ "comando": "name" }`, `{ "glob": "~/x/*.md" }`, `{ "qualsiasi": [rule, …] }` (any), `{ "tutte": [rule, …] }` (all), `{ "sempre": true }`.
- The module shows up under **Features found** only if the rule matches on this Mac; the user can switch it on or off (stored in `moduli`). A broken file is ignored.
- A module is a *declared, detectable, switchable feature*; it does not add code by itself. Add behaviour by editing the pages if the user asks for it.

## 6. Languages

`lingue/xx.json` is a flat `key → text` map with `"_nome"` (the language name). Missing keys fall back to Italian (`it.json`). Copy `en.json`, change `_nome`, translate: the language appears in the picker automatically. Text may use `**bold**` and `` `code` ``.

## 7. Look and feel

- Quick: `aspetto` (title, theme, accent color, language) from the page or the JSON; it styles the settings page.
- The **Appearance** page of the dashboard (themes, colors, backgrounds, card style, font…) is stored **in the browser** (`localStorage`, keys `pannello.asp.*`), not in `impostazioni.json`. It can be exported/imported as text from that page. To change the default look for everyone, edit the `DEF` object in the script of `base.html` (`pal`, `sfondo`, `sti`, `car`…).
- Deeper: `base.html` (overview page, side bar, quick actions) and `sistema.html` (settings page) are single files with their CSS and JS inline. Colors are CSS variables at the top of each file (`--bg`, `--card`, `--acc`… in `base.html`; `--bg`, `--pan`, `--ac`… in `sistema.html`): changing those re-skins everything. Back up before editing and keep the structure; the page ids (`#hColl`, `#azRap`, `#client`…) are used by the scripts.

## 8. Project map (`collegamenti`)

**Create links now** reads only the folders with `leggi: true`, up to 5,000 files, skipping `node_modules`, `.git`, `venv`, `Library`, `Applications` and every pattern in `esclusioni`. Of text files (`.md`, `.txt`, `.rst`, `.org`) it reads only the beginning. It writes **paths and relations only**: projects (first-level subfolders), same-name files in different places, and who mentions whom. Open `collegamenti.md` to find files instead of searching blindly.

## 9. Local HTTP interface

All routes accept only `127.0.0.1`/`localhost` as Host and Origin.

| Method | Route | Purpose |
|---|---|---|
| GET | `/dati` | settings merged with a fresh scan, plus install folder (`cartella`) |
| GET | `/riassunto` | what the overview shows (programs, folder count, links summary) |
| GET | `/lingue`, `/lingua?c=xx` | language list / one dictionary |
| GET | `/sfoglia?p=~` | sub-folder names (inside the home folder only) |
| POST | `/salva` | validate and save settings |
| POST | `/riscansiona` | fresh scan, keeps the user's choices |
| POST | `/collega` | build the project map |
| POST | `/aggancia/piano`, `/applica`, `/annulla` | hook plan / apply / undo (apply and undo need `{"conferma": true}`) |
| POST | `/assistente/...` | optional setup assistant |

POST calls need the header `X-Gettone`, a random token generated at each start and embedded in the served page, so a stray web page cannot call them. **For an agent the simplest and safest way to configure is to edit `impostazioni.json` directly** (§3) and tell the user to press *Search the PC again* or reload.

## 10. A good session for an agent

1. Read `README.md`, this file and `impostazioni.json`. Run nothing yet.
2. Summarise to the user: what is installed, which folders are on, what is never read.
3. Propose changes as a short list (programs on/off, folders, never-read patterns). Wait for the answer.
4. Back up `impostazioni.json`, apply **one** change, check the page still loads.
5. Offer **Create links now**, then **Show what will change**. Never press **Apply** or run `aggancio.applica` without an explicit yes.
6. Tell the user how to undo (**Undo hook-up**, or restore the `.bak-YYYYMMDD`).
