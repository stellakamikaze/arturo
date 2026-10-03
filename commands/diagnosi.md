---
description: Protocollo debug - disciplina diagnostica, poi delega la meccanica al debugging nativo
argument-hint: "[file/descrizione bug] (opzionale)"
---

# Debug

**Target**: $ARGUMENTS (o le git changes correnti).

Questo comando impone la **disciplina diagnostica**. La meccanica sistematica
(ispezione, ipotesi iterate, bisect, fix) la esegue il debugging nativo di Claude Code
— qui NON la riscriviamo.

---

## Prima di ipotizzare — raccogli i fatti (obbligatorio)

Non partire dalla prima ipotesi. Chiedi all'utente, se non già chiaro:

1. **Errore esatto** — messaggio/stack trace testuale, non parafrasato.
2. **Behavior atteso** vs osservato.
3. **Cosa ha già escluso** — se dà context negativo ("NON è X"), rispettalo e cerca altrove.
4. **Riproduzione** — passi, input, condizioni.

Se il bug sembra di ambiente (install/auth/config Claude Code, non codice del progetto):
`claude doctor` e fermati lì.

Se il problema riguarda i todo (`arturo todo`, `/inizio`, `/fine`), leggi prima l'archivio:

```bash
python3 ~/.claude/bin/arturo todo --json | PYTHONIOENCODING=utf-8 python3 -c 'import json,sys; v=json.load(sys.stdin); print("archivio leggibile, avvisi:", len(v["avvisi"])); [print("avviso:", a) for a in v["avvisi"]]'
```

Riporta all'utente ogni avviso con le sue parole: una riga illeggibile, un evento per un todo
che non esiste, un numero cambiato dopo un merge. Non correggere il file a mano: ogni riga
resta, e il resto dell'archivio funziona. Se il comando esce con un errore, riporta l'errore
esatto: è il primo fatto della diagnosi.

Se il problema riguarda il pannello `/dafare` o la riga sopra il prompt, controlla anche che il
mod sia caricato e che Claude Code sia abbastanza nuovo:

```bash
claude plugin list --json | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato: dafare@skills-dir" if v and v[0].get("enabled") else "mod spento: dafare@skills-dir" if v else "mod NON caricato: dafare@skills-dir manca")'
echo "versione di Claude Code: $(claude --version) (il pannello chiede la 2.1.287 o successiva)"
```

Se il mod manca, guarda se esiste `~/.claude/skills/dafare/.claude-plugin/plugin.json` e se il
plugin è spento (`claude plugin enable dafare@skills-dir` lo riaccende). In un'organizzazione, le
managed settings possono spegnere i mod: lo spiega `docs/referente.md`.

---

## Diagnosi prima del fix

Esponi l'ipotesi in **2-3 bullet** (causa sospetta + come la testeresti) e attendi conferma
prima di toccare il codice. Ragiona sui 4 path del data flow coinvolto: happy / nil / empty /
error — il bug vive quasi sempre in uno shadow path non gestito.

**L'ipotesi vale quanto la prova che la esclude.** Formulala così: *se la causa fosse X,
allora dovrebbe succedere Y* — e progetta la verifica che risponde sì o no, non quella che
«fa vedere cosa succede». Un check che non può smentirti non è una diagnosi: è un fix
travestito, ed è da lì che nascono i loop di tentativi.

Poi lascia lavorare il debugging nativo: ispezione, test dell'ipotesi, `git bisect` se è una
regressione, fix minimo con test che riproduce.

---

## Regole invalicabili

- **Max 3 tentativi** sullo stesso errore. Se 3 approcci diversi falliscono → STOP, il problema
  richiede un cambio di strategia, non un quarto tentativo. Chiedi all'utente.
- **Fix minimo**: solo la correzione, niente refactoring o "miglioramenti" a lato.
- **Commit selettivo** (`git add` dei file toccati, mai `.`/`-A`), messaggio `fix:` con root cause
  in una riga. NON usare Co-Authored-By.
- Per bug significativi ricorrenti: valuta una riga in `## Errori Comuni` del CLAUDE.md di progetto
  ("NON fare X — causa Y").

---

## Avvia

Raccogli i fatti (errore esatto, atteso, cosa escluso). Poi esponi l'ipotesi in 2-3 bullet
e attendi conferma prima di modificare codice.
