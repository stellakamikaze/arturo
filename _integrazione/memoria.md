# Integrazione del lotto «memoria» (15/10/2026)

Il modulo è facoltativo e spento di default. File del lotto: `bin/memoria.py` (motore e CLI
`arturo memoria`), `hooks/memoria-richiamo.py`, `hooks/memoria-scrittura.py`,
`hooks/memoria-subagente.py`, `tests/test_memoria.py` (Y01-Y07). Modificati: `bin/arturo` (voce
`memoria` in COMANDI), `commands/setup.md` (FASE 7d e una parola nel riepilogo), `.gitignore`
(`data/memoria/`).

Interruttore: `~/.claude/data/memoria/impostazioni.json` (`{"accesa": true, "cartelle": [...]}`),
fuori da git. `ARTURO_MEMORIA=1` o `=0` nell'ambiente, o in `env` di settings.json, vince sul file.
Accensione e spegnimento: `python3 ~/.claude/bin/arturo memoria accendi` / `spegni`.
A memoria spenta i tre hook escono con 0 e nessun output (banco Y01).

## 1. settings.json: hook da registrare

Nessun permesso nuovo (`Bash(python3:*)` c'è già). Nessuna voce in `env`: la memoria resta spenta.

- **UserPromptSubmit**: nel blocco esistente (quello di `inject-now.sh`, senza matcher) aggiungi
  in coda all'array `hooks`:
  ```json
  {"type": "command", "command": "python3 ~/.claude/hooks/memoria-richiamo.py", "timeout": 5}
  ```
- **PostToolUse**: blocco nuovo con matcher `Edit|MultiEdit|Write`:
  ```json
  {
    "matcher": "Edit|MultiEdit|Write",
    "hooks": [
      {"type": "command", "command": "python3 ~/.claude/hooks/memoria-scrittura.py", "timeout": 5}
    ]
  }
  ```
  (In alternativa si aggiunge al blocco di `emoji_remover.py`: quel matcher ha anche
  `NotebookEdit`, che lo scanner ignora da solo.)
- **SubagentStart**: evento nuovo.
  ```json
  "SubagentStart": [
    {
      "matcher": "",
      "hooks": [
        {"type": "command", "command": "python3 ~/.claude/hooks/memoria-subagente.py", "timeout": 5}
      ]
    }
  ]
  ```

Dopo la registrazione `audit.sh --strict` fa lo smoke dei tre hook con `{}`: escono 0 (provato a
mano su tutti e tre, accesi e spenti).

## 2. tests/verifica-allineamento.sh

- In `BANCHI`, in coda: `test_memoria.py`
- In `PY38_BANCHI`, in coda: `test_memoria.py` (CLI e hook dichiarano Python 3.8; il banco è
  verde anche con `/usr/bin/python3` 3.9).
- In `BASELINE`, in coda:
  ```bash
    # La memoria facoltativa (15/10/2026): cbd8305, l'ultimo dev prima del lotto memoria.
    "test_memoria.py cbd8305"
  ```

## 3. README.md

### 3a. Sezione «I guardiani (`hooks/`)», elenco «Fuori dal dispatcher»

Aggiungi dopo la riga di `prompt-injection-scanner.py`:

```markdown
- `memoria-richiamo.py`, `memoria-scrittura.py`, `memoria-subagente.py` — la memoria facoltativa, spenta di default: a memoria spenta escono subito senza fare niente. Vedi «La memoria (facoltativa)».
```

### 3b. Sezione nuova, subito prima di «## Cosa NON c'è (di proposito)»

```markdown
**La memoria (facoltativa).** Claude Code salva da solo alcune note sulle sessioni passate, in
`~/.claude/projects/*/memory/`: cosa preferisci, cosa hai deciso, dove stanno le cose. Di solito le
rilegge solo nel progetto in cui le ha scritte. La memoria di Arturo le rende utili ovunque, ed è
spenta finché non la accendi (`/setup` te lo chiede, oppure `python3 ~/.claude/bin/arturo memoria accendi`).
Quando è accesa:

- a ogni tuo messaggio `memoria-richiamo.py` cerca le note che parlano della stessa cosa e ne dà a
  Claude il percorso. Claude apre una nota solo se gli serve. Sotto una soglia di pertinenza tace;
- `memoria-scrittura.py` controlla ogni nota e ogni handoff che Claude scrive: se dentro c'è una
  password, una chiave o un'istruzione nascosta, Claude riceve un avviso. Il valore trovato non
  viene mai stampato;
- `memoria-subagente.py` dice ai subagenti che la memoria esiste e come cercarla.

`arturo memoria cerca "parole"` cerca a mano, anche a memoria spenta. `arturo memoria controlla`
trova note senza descrizione, frontmatter illeggibili e link rotti. `arturo memoria cartella aggiungi
<cartella>` aggiunge una tua cartella di note markdown (con `name` e `description` in testa).
`arturo memoria spegni` la spegne: le note restano dove sono. Tutto resta su questo computer:
nessun server, nessun archivio nuovo, e niente della memoria entra nella telemetria.
L'interruttore sta in `~/.claude/data/memoria/`, fuori da git; `ARTURO_MEMORIA=0` lo scavalca.
```

### 3c. Sezione «Cosa NON c'è (di proposito)»

Sostituisci il paragrafo d'apertura:

```markdown
Arturo è stato estratto da una config che include anche memoria persistente, task manager centralizzato e integrazioni con server privati. Quei pezzi **non ci sono** e le loro funzioni sono coperte in modo autosufficiente:
```

con:

```markdown
Arturo è stato estratto da una config che include anche una memoria su server, un task manager centralizzato e integrazioni con server privati. Quei pezzi **non ci sono** e le loro funzioni sono coperte in modo autosufficiente:
```

e la riga della tabella:

```markdown
| Memoria su database/server | il tuo `CLAUDE.md` + gli handoff in `data/handoffs/` |
```

con:

```markdown
| Memoria su database/server | il tuo `CLAUDE.md`, gli handoff in `data/handoffs/` e, se la accendi, la memoria facoltativa: le note di Claude Code su questo computer (`arturo memoria`) |
```

### 3d. Impegno 3 (telemetria)

Nessuna modifica obbligatoria: l'elenco degli eventi non cambia. Se si vuole dirlo, in coda alla
frase «Mai prompt, file tuoi, percorsi del tuo computer, nomi, risposte o il tuo percorso a tappe.»
aggiungi « Né le note della memoria.» (M09 legge solo i nomi degli eventi.)

## 4. NOVITA.md (entry in cima)

```markdown
## 2026-10-15 — Una memoria che puoi accendere

**Cosa cambia**: Claude Code salva da solo alcune note sulle sessioni passate: cosa preferisci,
cosa hai deciso, dove stanno le cose. Ora Arturo può usarle in ogni progetto. Se accendi la
memoria, a ogni messaggio Arturo cerca le note che parlano della stessa cosa e dice a Claude dove
sono. Claude le apre solo se servono. Ogni nota e ogni handoff che Claude scrive passa da un
controllo: se dentro c'è una password o un'istruzione nascosta, Claude riceve un avviso. Con
`arturo memoria cerca "parole"` cerchi a mano, con `arturo memoria controlla` trovi le note senza
descrizione e i link rotti. Puoi aggiungere una tua cartella di note con
`arturo memoria cartella aggiungi <cartella>`.

**Il principio dietro**: una memoria serve se la trovi quando ti serve, e se non porta dentro
niente che non hai scritto tu. Le note restano tue e restano qui: nessun server, nessun archivio
nuovo, niente nella telemetria.

**Da sapere**: la memoria è spenta. Si accende in `/setup` oppure con
`python3 ~/.claude/bin/arturo memoria accendi`, e si spegne con `arturo memoria spegni`. Spegnerla
non cancella nessuna nota. `arturo memoria` da solo ti dice se è accesa e quante note vede.
```

## 5. Scelte e cose lasciate fuori

- Autoload della scheda di progetto: lasciato fuori. Claude Code carica già il `MEMORY.md` del
  progetto all'avvio, e il richiamo per contenuto copre il resto.
- Postwrite (data `updated`, registro di audit) e registro delle letture: lasciati fuori. Sono
  metriche della config d'origine; qui nessuno li legge. Il controllo del frontmatter illeggibile
  vive in `arturo memoria controlla`.
- Lint: solo frontmatter (assente, `name`/`description` mancanti, `: ` senza virgolette, `type`
  fuori dai quattro di Claude Code), indice `MEMORY.md` che punta a file assenti, link markdown
  rotti, note fuori dall'indice (avviso). I `[[nome]]` senza nota sono «da scrivere», non errori:
  è la convenzione scritta da Claude Code stesso.
- Lo scanner delle scritture è spento con la memoria, come chiesto. Si potrebbe tenerlo sempre
  acceso come guardia (le note native e gli handoff esistono anche a memoria spenta): basta
  togliere il controllo `mem.accesa()` in `hooks/memoria-scrittura.py` e aggiornare Y01.
- Formato nativo verificato sul binario di Claude Code 2.1.300: frontmatter `name`, `description`,
  `metadata:` con `type:` annidato (user, feedback, project, reference), corpo con `[[nome]]`,
  indice `MEMORY.md` con righe `- [Titolo](file.md) — gancio`. Il parser legge anche `type` di
  primo livello e i campi facoltativi `triggers`/`answers` di una cartella della persona.
