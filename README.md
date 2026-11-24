<p align="center"><img src="logo.png" alt="PlanAIBoard logo" width="120"></p>

<h1 align="center">PlanAIBoard</h1>

<p align="center">
  <b>One local dashboard for all the AI assistants on your Mac.</b><br>
  <sub>macOS only · Python 3 · no dependencies · MIT</sub>
</p>

> **Nothing leaves your computer unless you ask your own AI for help, and you approve every change.**

🇮🇹 [Leggi in italiano](#italiano)

---

## What is it?

PlanAIBoard is a small web page that runs **on your own Mac** (`http://127.0.0.1:20150`) and gives you one place to see and control how your AI assistants are set up.

If you use more than one AI tool (Claude Code, Codex, Gemini CLI, Cursor, Copilot CLI, OpenCode…), each one keeps its own hidden config folder and its own instructions file. You quickly lose track of *what is installed*, *which of your folders each tool may look at*, and *what you never want them to touch*. PlanAIBoard puts all of that in a single, readable page and lets you decide.

It is **not** an AI, it does not call any model by itself, and it does not need an account, an API key or an internet connection.

## What is it for?

The problem: every AI tool you install has its **own** config folder and its **own** instructions file, and each one decides on its own what to read. Nothing tells you, in one place, what is installed, what your tools may look at, or whether they all follow the same rules.

What PlanAIBoard does about it, concretely:

- **One rule list for all your agents.** You write once which folders may be read and what must never be read (`.env`, `*.pem`, `.ssh`, browser data…). PlanAIBoard turns that into a rules file (`memoria-pannello.md`) and adds a short pointer to it in the instructions file of Claude Code, OpenCode, Codex and Gemini CLI. From then on each of them is *told* to follow the same list. Change the list in the page and every hooked tool gets the new rules. *(These are instructions the tools read, not a technical sandbox: it makes your intent explicit and consistent, it does not physically block a tool.)*
- **An inventory you can trust.** Which AI programs exist on this Mac, where their config lives, which ones are hooked and which are not.
- **A map of your work.** From the folders you allow, it writes `collegamenti.md`: your projects, files with the same name in different places (versions or copies), and which notes mention which files. You or your agent can open it to find things instead of searching blindly. It stores paths and relations, never the contents.
- **Less guessing when you set things up.** A setup assistant (your own local or installed AI) can propose a configuration, and a ready-made prompt lets any AI agent explain the dashboard and walk you through the integration.
- **Everything reversible.** Every change to a tool's file is shown first, backed up, and can be undone.

A typical first session: scan → turn on the 2–3 folders you actually work in → add `.env`-like patterns you care about → **Create links now** → **Show what will change** → **Apply (with backup)**. Your tools now share the same rules and you have a project map.

## How it works

Everything is a button on the page. Nothing happens on its own.

| Step | What you do | What happens |
|---|---|---|
| **1. Scan** | Open the page | It looks for known AI programs (by command name or config folder) and common work folders. It only checks *whether files and folders exist*, never what is inside. |
| **2. Choose** | Turn programs and folders on or off, edit the "never read" list | Your choices are stored in `impostazioni.json` when you press **Save**. Nothing else changes. |
| **3. Link** | Press **Create links now** | It reads **only the folders you turned on** (max 5,000 files, skipping `node_modules`, `.git`, `venv`, `Library`…) and writes `collegamenti.md` / `collegamenti.json`: projects, same-name files in different places, and which notes mention which files. Of text files (`.md`, `.txt`, `.rst`, `.org`) it reads only the beginning, and **saves only paths and relations, never contents**. |
| **4. Hook** | Press **Show what will change**, then **Apply (with backup)** | For Claude Code, OpenCode, Codex and Gemini CLI it adds **one marked block** to their instructions file (`~/.claude/CLAUDE.md`, `~/.config/opencode/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`) pointing to a generated rules file. A `.bak-YYYYMMDD` backup is made first and **Undo hook-up** removes the block. Cursor and Copilot CLI are detected but cannot be hooked yet. |

The **Overview** page then shows what was found, how many folders are read, and a summary of the links.

## Customize it

You can change almost everything from the page, or by editing `impostazioni.json` by hand (the page re-reads it on start).

| What | How |
|---|---|
| **Programs** | Turn each on or off. Rename it, change its command or config folder, change its badge color, or **add your own program** (name + command). |
| **Folders to read** | Pick any folder with the Finder dialog, or type a path. Each can be switched on or off. |
| **"Never read" list** | Add or remove patterns (`.env`, `*.pem`, `.ssh`…). They apply to every folder, to the link step, and to the rules file your hooked tools read. |
| **Look** | Title (up to 40 characters), theme (auto / light / dark), accent color, language. |
| **Language** | English, Italian, German, Spanish, French. To add one, copy `lingue/en.json` to `lingue/xx.json`, set `"_nome"` and translate the values. It appears automatically. |
| **Features (modules)** | Drop a `.json` file in `moduli/` with `id`, `nome`, `descrizione`, a `rileva` rule (`cartella`, `file`, `comando`, `glob`, `qualsiasi`, `tutte`, `sempre`) and `predefinito`. The feature appears in the page only if your Mac really has it, and you can switch it on or off. |
| **Port** | `PORTA_SISTEMA=20200 python3 sistema.py` |
| **Setup assistant endpoints** | `ASSISTENTE_OLLAMA` (default `http://127.0.0.1:11434`) and `ASSISTENTE_LMSTUDIO` (default `http://127.0.0.1:1234`). |

**Recipes**

- *"Keep my tools out of client work."* Leave that folder off, and add its name to the never-read list.
- *"Only my code."* Turn on just `~/Projects` (or `~/code`) and press **Create links now**.
- *"A tool I use isn't listed."* **Add program**, type its name and command; it shows up in the list and can be turned on or off like the others (hooking works for the four tools above).
- *"Another language."* Copy `lingue/en.json` to `lingue/pt.json`, set `"_nome": "Português"`, translate.
- *"Run it on a different port."* `PORTA_SISTEMA=20200 python3 sistema.py`.

## Let your own AI set it up

Two optional helpers, both under your control:

- **Setup assistant** — press **1 · Find the AIs on my Mac**. It lists local AIs (Ollama, LM Studio) and installed ones (Claude Code, Codex). Pick one with **Use this AI**, tick the consent box, press **2 · See what would be sent** to read the exact text, then **3 · Ask for a suggestion**. You tick what you want to apply. Only a summary of **names** (programs and folders), never file contents, is sent. Local AIs keep it on your Mac; for online ones it goes to that program's provider, and only after your consent.
- **Prompt for your AI agent** — a section with a ready-to-copy prompt. Paste it into any AI agent you already use: it explains what PlanAIBoard is, where it lives, what is configured now, and asks the agent to propose a setup and explain the integration. The prompt tells the agent to ask before changing anything, back up files and never read secrets.

## Install

You need a Mac with **Python 3**. Check in Terminal:

```bash
python3 --version
```

If it's missing, install it from [python.org](https://www.python.org/downloads/macos/).

**Option A: download the ZIP (no git)**

1. Get `PlanAIBoard-x.y.z.zip` from the [latest release](https://github.com/Mkseev/PlanAIBoard/releases/latest) and unzip it.
2. Double-click **`avvia.command`**.
3. The first time, macOS may block it: right-click the file → **Open** → **Open**.

**Option B: with git**

```bash
git clone https://github.com/Mkseev/PlanAIBoard.git
cd PlanAIBoard
./avvia.command
```

Your browser opens on `http://127.0.0.1:20150`. Follow the short guided tour (10 steps) and you're done. Press `Ctrl+C` in the Terminal window to stop it.

## Files it creates

All inside the PlanAIBoard folder, none of them published by git:

- `impostazioni.json` — your choices.
- `collegamenti.json` / `collegamenti.md` — the links overview.
- `memoria-pannello.md`, `agganci.json` — the generated rules file and a log of what was hooked, so it can be undone.

## Privacy and safety

- The server listens **only on `127.0.0.1`**. No account, no cloud, no telemetry.
- The scan checks **whether files and folders exist**, never what is inside them.
- The "never read" list is respected everywhere, including the link step.
- Hooking a tool changes one marked block and always makes a backup first.
- With the optional assistant, a **summary of names** goes to the AI *you* choose, after your consent.

## Uninstall

Press **Undo hook-up** in the Hook section to remove the blocks added to your tools, then delete the folder. Nothing is installed anywhere else.

## Disclaimer

Not affiliated with Anthropic, OpenAI, Google, GitHub, Cursor or any other vendor mentioned. Their names are trademarks of their owners and are used only to recognise installed programs.

## License

[MIT](LICENSE)

---

## Italiano

**Solo macOS.** PlanAIBoard è una dashboard locale per i tuoi assistenti AI su Mac. Gira solo sul tuo computer (`http://127.0.0.1:20150`) e non è una IA: non usa modelli, account o internet.

**A cosa serve**
- Vedi in un elenco quali programmi AI hai installato (Claude Code, Codex, Gemini CLI, Cursor, Copilot CLI, OpenCode…).
- Decidi quali cartelle possono leggere e cosa **non** devono mai leggere (`.env`, chiavi, `.ssh`, dati del browser…).
- Dai le stesse regole a tutti i programmi: PlanAIBoard scrive un file di regole e lo collega alle loro istruzioni.
- Ottieni una mappa dei tuoi progetti e dei file che sembrano versioni, copie o citazioni l'uno dell'altro.
- Puoi farti aiutare dalla tua IA con un prompt già pronto.

**Come funziona** (tutto con pulsanti, niente parte da solo)
1. **Scansione:** cerca i programmi AI e le cartelle di lavoro più comuni. Controlla solo se esistono, mai cosa contengono.
2. **Scelta:** accendi o spegni programmi e cartelle e modifichi l'elenco "Mai letto". Premi **Salva**: si scrive solo `impostazioni.json`.
3. **Collegamenti:** legge solo le cartelle che hai acceso e scrive `collegamenti.md`. Salva percorsi e legami, mai i contenuti.
4. **Aggancio:** aggiunge un blocco marcato al file di istruzioni di Claude Code, OpenCode, Codex e Gemini CLI, con copia `.bak` prima. Si annulla con un pulsante.

**Personalizzazione:** programmi (anche aggiunti da te), cartelle, elenco "Mai letto", titolo, tema, colore, lingua (IT, EN, DE, ES, FR; se ne aggiungono altre copiando `lingue/it.json`), funzioni in `moduli/`, porta (`PORTA_SISTEMA`). Puoi anche modificare `impostazioni.json` a mano.

**Avvio:** serve Python 3 (da [python.org](https://www.python.org/downloads/macos/) se manca). Scarica lo ZIP dalla [release](https://github.com/Mkseev/PlanAIBoard/releases/latest), decomprimilo e fai doppio clic su `avvia.command`. La prima volta macOS potrebbe bloccarlo: clic destro → Apri → Apri.

**Privacy:** niente esce dal tuo computer. Solo se usi l'assistente facoltativo, un riassunto di nomi (mai contenuti di file) va alla IA che scegli, dopo il tuo consenso.
