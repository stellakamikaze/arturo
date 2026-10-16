---
description: Avvia la sessione su un progetto - sync della config (con --tutti anche dei progetti), contesto in una chiamata (git, handoff, todo con chi agisce, scadenze), cruscotto e scelta del lavoro
argument-hint: "<nome-progetto> [--tutti] [-- <compito>]"
---

# Inizio Sessione

Avvia sessione di lavoro su **$ARGUMENTS**.

`--tutti` è un flag: aggiorna anche tutti i progetti (FASE 0) e non entra nel nome. Il testo dopo
« -- » è il compito della sessione (vedi «Con un compito» in fondo). Con `--tutti` e senza nome
ti fermi dopo la FASE 0.

---

## FASE -1: Onboarding speciali

Se `$ARGUMENTS` è `gws`: NON è un progetto. Leggi `~/.claude/docs/onboarding/gws.md`.
Proponi prima la strada semplice, i connettori di claude.ai (sezione 0): l'utente li
attiva su claude.ai, riapre Claude Code e tu controlli con `/mcp` che ci siano. Passa
alla Google Workspace CLI (installazione → progetti GCP → config dir → login → alias →
verifica) solo se l'utente vuole più account, i comandi `gws` nel terminale, o se i
connettori non sono disponibili per lui. Esegui i comandi verificabili, chiedi
all'utente quelli interattivi (login browser). Alla fine esegui la checklist della
strada scelta. Poi FERMATI: le fasi sotto non si applicano.

---

## FASE 0: Sync Config

`/inizio` non applica mai gli aggiornamenti di Arturo: li controlla e li segnala. Li applica
solo `/aggiorna`, dopo il sì dell'utente (Impegno 2 del README). Se `origin` è un repository
suo (vedi `/setup` FASE 7), `/inizio` sincronizza quello: sono le sue macchine, non codice di
altri.

```bash
ORIGIN_URL=$(git -C ~/.claude remote get-url origin 2>/dev/null || echo "")
case "$ORIGIN_URL" in
  *github.com[:/]stellakamikaze/arturo|*github.com[:/]stellakamikaze/arturo.git) ORIGIN_ARTURO=1 ;;
  *) ORIGIN_ARTURO=0 ;;
esac
export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
if [ "$ORIGIN_ARTURO" = 1 ] || [ -z "$ORIGIN_URL" ]; then
  git -C ~/.claude fetch --quiet origin main 2>&1 || echo "Config sync: controllo aggiornamenti non riuscito (rete?)"
else
  MODIFICATI=$(git -C ~/.claude status --porcelain --untracked-files=no | cut -c4-)
  if [ -n "$MODIFICATI" ]; then
    echo "Config sync: non ho scaricato dal tuo repository. Questi file della config hanno modifiche non ancora salvate con un commit:"
    printf '%s\n' "$MODIFICATI" | sed 's/^/  /'
    echo "Config sync: non ho toccato niente. Le salva /fine, poi il prossimo /inizio scarica."
  elif ! git -C ~/.claude fetch --quiet origin main 2>&1; then
    echo "Config sync: non riesco a scaricare dal tuo repository (rete?). Non ho toccato niente."
  else
    # Il rebase gira in una copia di prova: ~/.claude cambia solo con un risultato integro.
    APPLICA=$(mktemp)
    cp ~/.claude/bin/aggiorna-applica.sh "$APPLICA" 2>/dev/null
    if [ ! -s "$APPLICA" ]; then
      echo "Config sync: manca bin/aggiorna-applica.sh, non ho scaricato. Non ho toccato niente."
    else
      SYNC_OUTPUT=$(bash "$APPLICA" "$HOME/.claude" sync origin/main 2>&1)
      case $? in
        0) printf '%s\n' "$SYNC_OUTPUT" | grep -q '^APPLICATO' && echo "Config sync: scaricate le modifiche delle tue altre macchine." ;;
        1) echo "Config sync: il sync dal tuo repository non è riuscito. La config è com'era prima."
           printf '%s\n' "$SYNC_OUTPUT" ;;
        *) echo "Config sync: il sync dal tuo repository non è riuscito, e NON sono riuscito a riportare la config a prima."
           printf '%s\n' "$SYNC_OUTPUT" ;;
      esac
    fi
    rm -f "$APPLICA"
  fi
fi
git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && git -C ~/.claude fetch --quiet upstream main 2>&1
SRC=$(git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
BEHIND=$(git -C ~/.claude rev-list --count "HEAD..$SRC/main" 2>/dev/null || echo 0)
[ "${BEHIND:-0}" -gt 0 ] && echo "ARTURO: $BEHIND aggiornamenti disponibili — li applica /aggiorna, dopo il tuo sì"
python3 ~/.claude/hooks/controlla-config.py --quiet || exit 1
```

Se l'ultima riga stampa `CONFIG ROTTA`, fermati: spiega all'utente il problema in parole
semplici e proponi il comando che la riga suggerisce. Non lavorare su una config rotta: le
guardie potrebbero essere spente.

Se il sync dice `CONFLITTO`, due tue macchine hanno cambiato le stesse righe della config. La
sua `~/.claude` è com'era: il conflitto aspetta nella copia di prova stampata. Proponigli di
risolverlo subito come in `/aggiorna`, sezione «Risolvere un conflitto» (con un rebase). Finché
la copia di prova aspetta, il sync non riparte, e l'avvio della sessione lo ricorda. Se il sync
risponde che una copia di prova aspetta da prima, vale lo stesso: si conclude, oppure col suo sì si
scarta come in `/aggiorna`.

Se compare «non ho scaricato dal tuo repository», la config è com'era: diglielo in una riga e
nomina i file. Sono modifiche sue (anche `/setup` ne scrive in `settings.json`) che `/fine`
salverà con un commit. Il sync riparte al prossimo `/inizio`.

**Con `--tutti`** aggiorna anche ogni progetto della cartella dei progetti (`PROJECTS_BASE`):
per ognuno mette da parte le modifiche non salvate, scarica, e le rimette al loro posto.

```bash
bash "$HOME/.claude/bin/sync-progetti.sh"; echo "rc=$?"
```

Con `rc=1` almeno un progetto ha un pull fallito, uno stash in conflitto o file in conflitto:
riporta quale e cosa dice la riga `ERRORE`, e non toccarlo. Lo sistemi con `/inizio <quel progetto>`.
Un progetto senza remote è solo locale: non è un errore.

---

## FASE 1: Contesto in una chiamata

`$ARGUMENTS` può contenere `--tutti` e, dopo « -- », il compito della sessione: lo script li
riconosce e il nome del progetto resta pulito. Senza nome usa la cartella in cui sei.

```bash
# Tutto il contesto in un processo solo: tra due blocchi bash le variabili si perdono.
python3 "$HOME/.claude/bin/arturo" contesto "$ARGUMENTS"; echo "rc=$?"
```

Lo script legge e non scrive niente. Calcola lo slug del progetto come `/fine`
(`basename | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'`), così
ritrova gli handoff e i todo della cartella. Stampa, in quest'ordine:
- `PROGETTO` e la riga `cartella:` (il percorso, oppure `nessuna`);
- `GIT`: branch, modifiche non salvate, CONFLITTI DI MERGE, i commit arrivati dopo l'ultimo handoff;
- `RIPARTENZA`: la Ripartenza e il prossimo passo degli handoff degli ultimi 14 giorni, e il
  percorso dell'ultimo handoff da leggere per intero;
- i todo aperti del progetto divisi per chi agisce (TOCCA A TE, DECIDI TU POI FACCIO IO, FACCIO
  IO, FERMO), i todo chiusi dopo l'ultimo handoff, le SCADENZE dei prossimi 7 giorni anche fuori
  dal progetto, il todo DA DOVE PARTIRE e gli avvisi.

Con `rc=0` entra nella cartella della riga `cartella:` con `cd "<cartella>"`: la sessione e
`/fine` lavorano lì. Con `cartella: nessuna` il progetto vive solo negli handoff o nei todo:
resta dove sei. Se il progetto ha un remote, aggiornalo senza riscrivere la storia:

```bash
git remote 2>/dev/null | grep -q . && { GIT_TERMINAL_PROMPT=0 git pull --ff-only 2>&1 || echo "Pull non riuscito: il progetto e il remote hanno storie diverse. Non ho toccato niente."; }
```

Se il pull non riesce, dillo alla persona: niente rebase in automatico. Se `GIT` mostra
CONFLITTI DI MERGE, risolvili PRIMA di procedere.

---

## FASE 2: Progetto non trovato

Con `rc=2` lo script stampa `NON TROVATO` e i progetti con un nome simile: spesso è un refuso.
Proponi i candidati e aspetta la scelta. Per una vista di cosa c'è da fare ovunque leggi
`~/.claude/data/handoffs/INDEX.md` (una riga per progetto con stato e prossimo passo) e proponi
da lì. Con `rc=3` il nome non è valido: chiedi quello giusto.

Se la persona dice che è un progetto nuovo, chiedi in una frase cosa è. Non creare cartelle e non
lanciare `git init` senza un sì. Col sì crei il progetto in `PROJECTS_BASE`, poi rilanci la FASE 1
col nome nuovo:

```bash
BASE="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"
NOME="nome-del-progetto"   # minuscole e trattini, come lo slug della FASE 1
mkdir -p "$BASE/$NOME" && cd "$BASE/$NOME" && git init -q -b main
printf '.DS_Store\nnode_modules/\n*.log\n.env\n' > .gitignore
```

Scrivi un `CLAUDE.md` breve: cosa è il progetto in due righe, e una sezione «Materiali» con i
percorsi dei file che stanno fuori dal repo (all'inizio può essere vuota). Poi il primo commit:
`git add .gitignore CLAUDE.md && git commit -q -m "inizio del progetto"`. Gli handoff non entrano
mai nel repo del progetto.

---

## FASE 3: Carica Contesto

Leggi in ordine (se esistono):
1. `CLAUDE.md` — Istruzioni progetto
2. L'ultimo handoff per intero: il percorso è nella riga «da leggere per intero» della FASE 1.
   Se la FASE 1 segnala un handoff nella cartella del progetto più recente dello store (lasciato
   da una versione vecchia di `/fine`), leggi quello.

---

## FASE 4: Carica i Todo con Cross-Reference

I todo stanno nell'archivio `~/.claude/data/todo/eventi.jsonl`, scritto da `/fine` e dalle
richieste della persona («ricordami di…»). È la fonte di verità: la tabella `## Task Pendenti`
dell'handoff è solo la fotografia dell'ultima sessione. La lista del progetto l'hai già dalla
FASE 1: questo blocco aggiunge gli avvisi di rinumerazione, i todo di «generale», il git log per
il confronto e il pannello.

```bash
# Il progetto dei todo è quello della cartella (FASE 1 ci è entrata), calcolato dalla CLI come per
# «ricordami di…»: nessuna variabile di un blocco precedente. Gli avvisi («Attenzione: …») restano
# visibili: dopo il pull un todo può aver cambiato numero.
python3 "$HOME/.claude/bin/arturo" todo progetto
python3 "$HOME/.claude/bin/arturo" todo --progetto .
# I todo di «generale»: quelli presi fuori da un progetto (nella HOME, in /setup, fuori da git).
[ "$(python3 "$HOME/.claude/bin/arturo" todo progetto)" = generale ] || python3 "$HOME/.claude/bin/arturo" todo --progetto generale
git log --oneline -20 2>/dev/null
# Il pannello /dafare c'è? I comandi di un mod non compaiono fra quelli che vedi.
claude plugin list --json 2>/dev/null | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato" if v and v[0].get("enabled") else "mod assente")' 2>/dev/null || echo "mod assente"
```

1. Per ogni todo aperto del progetto, verifica se un commit recente lo ha già completato. Se sì,
   chiudilo con `python3 ~/.claude/bin/arturo todo fatto ID --titolo-atteso="titolo"` e dillo
   alla persona. I todo di «generale» non si confrontano con il git log del progetto.
2. Un item della tabella `## Task Pendenti` senza ID e senza todo (handoff di una versione
   precedente) diventa un todo con `arturo todo aggiungi`. Un todo già chiuso non si ricrea.
3. Non creare task di sessione (`TaskCreate`) all'apertura: si crea solo quello che la persona
   sceglie di riprendere.

---

## FASE 5: Presenta Dashboard

```
----------------------------------------------------
 SESSIONE: $ARGUMENTS
----------------------------------------------------

## Contesto
- Branch: [nome]
- Ultimo stato: [HANDOFF / nessuno]
- Config sync: [ok / failed]  (con --tutti: progetti aggiornati / con errori)
- Merge conflicts: [nessuno / LISTA]

## Da allora
[2-4 frasi: la Ripartenza dell'ultimo handoff e cosa è cambiato dopo: i commit arrivati, i todo
 chiusi, le scadenze arrivate, un handoff di un'altra macchina. Chiudi con quello che ne segue.]

## Todo
[se la lettura della FASE 4 stampa righe «Attenzione:», riportale qui per prime, una riga
 ciascuna, con parole tue: «#1 adesso è #2, dopo il merge con l'altro computer».]
[i gruppi di `arturo todo`: TOCCA A TE, DECIDI TU POI FACCIO IO, FACCIO IO, FERMO.
 Ogni todo con l'ID a destra e una riga su a cosa serve. Le scadenze passate in cima.
 Un FERMO dice cosa aspetta. Un todo di Claude che prepara una parte prima del gesto della
 persona (una pagina aperta, una bozza) si legge «Preparo io, poi tu».]
[Da dove partirei: UN todo, quello di DA DOVE PARTIRE della FASE 1 o uno migliore, col motivo.]
[poi, se ci sono, i todo aperti di «generale», in un gruppo «Fuori dai progetti».]
[solo se il controllo del pannello della FASE 4 stampa «mod caricato»:]
Per chiuderli o spostarli con un tasto: /dafare

## Skill Progetto
[suggerisci le poche skill davvero utili a QUESTO progetto ora, in base a stack,
 stato dell'handoff e task pendenti — non una lista meccanica. Ometti la sezione
 se non c'è nulla di rilevante da proporre.]

----------------------------------------------------
```

Per farti un'idea dello stack (segnale per il tuo giudizio, non una regola):
```bash
[ -f "package.json" ] && echo "HAS_PKG=true"
[ -f "prisma/schema.prisma" ] && echo "HAS_PRISMA=true"
[ -d "docs" ] && echo "HAS_DOCS=true"
ls next.config.* 2>/dev/null && echo "HAS_NEXT=true"
```

---

## FASE 6: Selezione Lavoro

Usa AskUserQuestion:

**Header**: "Cosa vuoi fare?"

**Opzioni**:
1. **Continua task** — "Riprendi [primo task pending]"
2. **Nuovo task** — "Inizia nuovo lavoro"
3. **Diagnosi** — "Qualcosa non torna: controllo Arturo e il progetto" → apri con Read
   `~/.claude/commands/diagnosi.md` e seguilo
4. **Debug** — "C'è un bug da fixare"

Se la persona corregge un todo dal cruscotto («il 4 lo faccio io», «il 5 scartalo»), scrivilo
subito nell'archivio con `arturo todo modifica ID --chi …` o `arturo todo scarta ID "motivo"`
e riporta la riga di conferma. Non spostare un todo da tu a io o decidi senza un suo sì.

---

## Con un compito

Con « -- <compito>» negli argomenti il cruscotto esce breve: il titolo, «Da allora» in una o due
frasi, una riga per gruppo di todo con il loro numero. Al posto di «Da dove partirei» scrivi
«Oggi: <compito>», con l'ID del todo che lo copre se esiste. Salta la FASE 6 e parti sul compito.

---

## Orchestrazione

Questo workflow chiama automaticamente:
- Sync GitHub config (`git -C`), e con `--tutti` di ogni progetto (`bin/sync-progetti.sh`)
- `arturo contesto` — git, handoff recenti, todo con chi agisce, scadenze, in una chiamata
- Check merge conflicts
- Cross-reference task vs `git log` (skip task già completati)
- `arturo todo` — I todo aperti del progetto (chiude quelli già fatti da un commit)

**L'utente chiama solo /inizio, il resto è automatico.**

---

## Avvia

Esegui FASE 0: sync config, poi FASE 1: contesto del progetto $ARGUMENTS.
