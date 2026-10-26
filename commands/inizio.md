---
description: >-
  Apre la sessione su un progetto: sync della config (con --tutti anche dei progetti), contesto in una
  chiamata con arturo contesto (git, handoff recenti, todo con chi agisce, scadenze), le altre sessioni
  sullo stesso progetto, poi la ripartenza per filone con ogni todo marcato per chi agisce. Con «--
  <compito>» parte subito sul compito. Progetto non trovato: propone i nomi simili e non crea niente
  senza un sì. La chiusura è /fine.
argument-hint: "<nome-progetto> [--tutti] [-- <compito>]"
---

# Inizio sessione

Argomenti: **$ARGUMENTS**. Il testo dopo " -- " è il compito della sessione (vedi "Con un compito" in
fondo). `--tutti` è un flag: aggiorna anche tutti i progetti (FASE 0) e non entra nel nome. Senza nome
usa la cartella in cui sei. Con `--tutti` e senza nome ti fermi dopo la FASE 0.

## FASE -1: Onboarding speciali

Se `$ARGUMENTS` è `gws`: NON è un progetto. Leggi `~/.claude/docs/onboarding/gws.md`.
Proponi prima la strada semplice, i connettori di claude.ai (sezione 0): l'utente li
attiva su claude.ai, riapre Claude Code e tu controlli con `/mcp` che ci siano. Passa
alla Google Workspace CLI (installazione → progetti GCP → config dir → login → alias →
verifica) solo se l'utente vuole più account, i comandi `gws` nel terminale, o se i
connettori non sono disponibili per lui. Esegui i comandi verificabili, chiedi
all'utente quelli interattivi (login browser). Alla fine esegui la checklist della
strada scelta. Poi FERMATI: le fasi sotto non si applicano.

## FASE 0: Sync Config

`/inizio` non applica mai gli aggiornamenti di Arturo: li controlla e li segnala. I rilasci
firmati si installano da soli alla chiusura della sessione, gli altri li applica `/aggiorna` dopo
il sì dell'utente (Impegno 2 del README). Se `origin` è un repository
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
  git -C ~/.claude fetch --quiet --tags origin main 2>&1 || echo "Config sync: controllo aggiornamenti non riuscito (rete?)"
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
      SYNC_OUTPUT=$(bash "$APPLICA" ~/.claude sync origin/main 2>&1)
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
git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && git -C ~/.claude fetch --quiet --tags upstream main 2>&1
# Conta solo l'ultimo tag firmato (bin/aggiornamenti.py firmato): i commit di main dopo il tag non si applicano mai.
TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato 2>/dev/null); FIRMA=$?
if [ "$FIRMA" = 0 ]; then
  BEHIND=$(git -C ~/.claude rev-list --count "HEAD..$TAG" 2>/dev/null || echo 0)
  [ "${BEHIND:-0}" -gt 0 ] && echo "ARTURO: c'è la versione $TAG — i rilasci firmati si installano da soli alla chiusura, o subito con /aggiorna"
elif [ "$FIRMA" = 3 ]; then
  echo "ARTURO: possibile compromissione: non aggiornare, segnala a chi mantiene Arturo (l'ultimo rilascio non ha una firma valida)"
elif [ "$FIRMA" = 4 ]; then
  echo "ARTURO: questo computer non sa controllare la firma dei rilasci (servono git 2.34 e OpenSSH 8.2): Arturo non si aggiorna finché non li aggiorni. Non è un problema di sicurezza"
fi
python3 ~/.claude/hooks/controlla-config.py --quiet || exit 1
```

Se l'ultima riga stampa `CONFIG ROTTA`, fermati: spiega all'utente il problema in parole
semplici e proponi il comando che la riga suggerisce. Non lavorare su una config rotta: le
guardie potrebbero essere spente.

Se il sync dice `CONFLITTO`, due tue macchine hanno cambiato le stesse righe della config. La
sua `~/.claude` è com'era: il conflitto aspetta nella copia di prova stampata. Proponigli di
risolverlo subito come in `/aggiorna`, sezione "Risolvere un conflitto" (con un rebase). Finché
la copia di prova aspetta, il sync non riparte, e l'avvio della sessione lo ricorda. Se il sync
risponde che una copia di prova aspetta da prima, vale lo stesso: si conclude, oppure col suo sì si
scarta come in `/aggiorna`.

Se compare "non ho scaricato dal tuo repository", la config è com'era: diglielo in una riga e
nomina i file. Sono modifiche sue (anche `/setup` ne scrive in `settings.json`) che `/fine`
salverà con un commit. Il sync riparte al prossimo `/inizio`.

Se compare "possibile compromissione", l'ultimo rilascio di Arturo non ha una firma valida: diglielo
con quelle parole e non proporre `/aggiorna`, che non lo applica. Proponi `/segnala`, oppure la
segnalazione privata di `SECURITY.md`.

**Con `--tutti`** aggiorna anche ogni progetto della cartella dei progetti (`PROJECTS_BASE`):
per ognuno mette da parte le modifiche non salvate, scarica, e le rimette al loro posto.

```bash
bash ~/.claude/bin/sync-progetti.sh; echo "rc=$?"
```

Con `rc=1` almeno un progetto ha un pull fallito, uno stash in conflitto o file in conflitto:
riporta quale e cosa dice la riga `ERRORE`, e non toccarlo. Lo sistemi con `/inizio <quel progetto>`.
Un progetto senza remote è solo locale: non è un errore.

## FASE 1: Contesto in una chiamata

`$ARGUMENTS` può contenere `--tutti` e, dopo " -- ", il compito della sessione: lo script li
riconosce e il nome del progetto resta pulito. Senza nome usa la cartella in cui sei.

```bash
# Tutto il contesto in un processo solo: tra due blocchi bash le variabili si perdono.
python3 ~/.claude/bin/arturo contesto "$ARGUMENTS"; echo "rc=$?"
```

Lo script legge e non scrive niente. Calcola lo slug del progetto come `/fine`
(`basename | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'`), così
ritrova gli handoff e i todo della cartella. Stampa, in quest'ordine:
- `PROGETTO` e la riga `cartella:` (il percorso, oppure `nessuna`);
- `GIT`: branch, modifiche non salvate, CONFLITTI DI MERGE, i commit arrivati dopo l'ultimo handoff;
- `RIPARTENZA`: la Ripartenza e il prossimo passo degli handoff degli ultimi 14 giorni, col filone
  quando c'è, e il percorso dell'ultimo handoff da leggere per intero;
- i todo aperti del progetto divisi per chi agisce (TOCCA A TE, DECIDI TU POI FACCIO IO, FACCIO
  IO, FERMO), i todo chiusi dopo l'ultimo handoff, le SCADENZE dei prossimi 7 giorni anche fuori
  dal progetto, il todo DA DOVE PARTIRE e gli avvisi.

Con `rc=0` entra nella cartella della riga `cartella:` con `cd "<cartella>"`: la sessione e
`/fine` lavorano lì. Con `cartella: nessuna` il progetto vive solo negli handoff o nei todo:
resta dove sei.

- **Pull.** Se il progetto ha un remote, aggiornalo senza riscrivere la storia:

  ```bash
  git remote 2>/dev/null | grep -q . && { GIT_TERMINAL_PROMPT=0 git pull --ff-only 2>&1 || echo "Pull non riuscito: il progetto e il remote hanno storie diverse. Non ho toccato niente."; }
  ```

  Se il pull non riesce, dillo alla persona: niente rebase in automatico. Se `GIT` mostra CONFLITTI
  DI MERGE, risolvili PRIMA di tutto il resto. I commit arrivati vanno nel «Da allora».
- **Altre sessioni.** Lancia `ListAgents`. Un'altra sessione di Claude Code sullo stesso progetto va
  in cima alla ripartenza, con quello che sta facendo.
- **Worktree, solo se c'è quella sessione.** Due sessioni nella stessa cartella si pestano i piedi:
  test, build e commit vedono anche il lavoro dell'altra. Prima di qualsiasi modifica entra con
  `EnterWorktree` (nome `<slug>-<aaaammgg-hhmm>`, parte dall'ultimo commit locale). La ripartenza dice
  che la sessione lavora in una copia a parte, e `/fine` riporta il lavoro nella cartella principale.
  Nel worktree la guardia di Claude Code rifiuta i comandi che non sa leggere: scrivi un comando per
  chiamata, senza cicli, variabili, `$(...)` né `cd ... &&`. Un ciclo o una copia di più file va in uno
  script Python nello scratchpad. I file nuovi nascono nel worktree, anche quelli ignorati da git, e
  `/fine` li riporta nella cartella principale (segnalazione n. 13, 26/10/2026).
  Sessione unica: resta nella cartella principale.

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

Scrivi un `CLAUDE.md` breve: cosa è il progetto in due righe, e una sezione "Materiali" con i
percorsi dei file che stanno fuori dal repo (all'inizio può essere vuota). Poi il primo commit:
`git add .gitignore CLAUDE.md && git commit -q -m "inizio del progetto"`. Gli handoff non entrano
mai nel repo del progetto.

## FASE 3: Carica il contesto

Leggi in ordine, se esistono:
1. il `CLAUDE.md` del progetto;
2. l'ultimo handoff per intero: il percorso è nella riga "da leggere per intero" della FASE 1.
   Se la FASE 1 segnala un handoff nella cartella del progetto più recente dello store (lasciato
   da una versione vecchia di `/fine`), leggi quello.

Per farti un'idea dello stack (un segnale per il tuo giudizio, non una regola):

```bash
[ -f "package.json" ] && echo "HAS_PKG=true"
[ -f "prisma/schema.prisma" ] && echo "HAS_PRISMA=true"
[ -d "docs" ] && echo "HAS_DOCS=true"
ls next.config.* 2>/dev/null && echo "HAS_NEXT=true"
```

## FASE 4: Carica i Todo con Cross-Reference

I todo stanno nell'archivio `~/.claude/data/todo/eventi.jsonl`, scritto da `/fine` e dalle
richieste della persona ("ricordami di…"). È la fonte di verità: la tabella `## Task Pendenti`
dell'handoff è solo la fotografia dell'ultima sessione. La lista del progetto l'hai già dalla
FASE 1: questo blocco aggiunge gli avvisi di rinumerazione, i todo di "generale", il git log per
il confronto e il pannello.

```bash
# Il progetto dei todo è quello della cartella (FASE 1 ci è entrata), calcolato dalla CLI come per
# "ricordami di…": nessuna variabile di un blocco precedente. Gli avvisi ("Attenzione: …") restano
# visibili: dopo il pull un todo può aver cambiato numero.
python3 ~/.claude/bin/arturo todo progetto
python3 ~/.claude/bin/arturo todo --progetto .
# I todo di "generale": quelli presi fuori da un progetto (nella HOME, in /setup, fuori da git).
# Se la prima riga ha stampato "generale", questa ripete la stessa lista: leggila una volta sola.
# Niente sostituzione di comando per saltarla: in un worktree la guardia di Claude Code rifiuta il blocco.
python3 ~/.claude/bin/arturo todo --progetto generale
git log --oneline -20 2>/dev/null
# Il pannello /dafare c'è? I comandi di un mod non compaiono fra quelli che vedi.
claude plugin list --json 2>/dev/null | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato" if v and v[0].get("enabled") else "mod assente")' 2>/dev/null || echo "mod assente"
```

1. Per ogni todo aperto del progetto, verifica se un commit recente lo ha già completato. Se sì,
   chiudilo con `python3 ~/.claude/bin/arturo todo fatto ID --titolo-atteso="titolo"` e dillo
   alla persona nel "Da allora". I todo di "generale" non si confrontano con il git log del progetto.
2. Un item della tabella `## Task Pendenti` senza ID e senza todo (handoff di una versione
   precedente) diventa un todo con `arturo todo aggiungi`. Un todo già chiuso non si ricrea.
3. Non creare task di sessione (`TaskCreate`) all'apertura: si crea solo quello che la persona
   sceglie di riprendere.

## FASE 5: La ripartenza

La persona guarda la lista e sceglie da dove partire. La ripartenza è markdown semplice: niente
blocco di codice, niente riquadri. Un buon risultato:

---
**Il libro** · branch main · ultimo handoff 14/10 alle 18:40

**Da allora.** Il 14/10 il capitolo tre è stato riscritto e mancano solo le note dell'editor. Oggi
sono arrivati 3 commit dall'altro computer, e nessun handoff li racconta. Il todo dell'indice è già
fatto da uno di quei commit: l'ho chiuso.

**Capitolo tre**
1. Mandare la bozza all'editor · #5 · Preparo io, poi tu: invio a terzi
2. Rileggere il capitolo con le note · #4 · Fermo: aspetta il 5

**Copertina**
3. Scegliere fra le due proposte della grafica · #7 · Decidi tu
   Mi serve sapere quale delle due ti convince, poi preparo i file per la tipografia.
4. Preparare i file per la tipografia · #8 · Faccio io

**Fuori dai progetti**
5. Rinnovare l'abbonamento al dominio, scade venerdì · #2 · Tocca a te: pagamento

**Da dove partirei:** #5. Sblocca la rilettura, e la rilettura chiude il capitolo. Scrivimi "vai" e
preparo la mail.

Rispondi **tutto il delegabile**, il nome di un filone (**copertina**) o i numeri (**3 4**). Per
correggere: **8 a te**, **7 scarta**.

---

Perché è fatta così:
- **Prima le avvertenze.** Se la lettura della FASE 4 stampa righe «Attenzione:», riportale in cima,
  una riga ciascuna, con parole tue: «#1 adesso è #2, dopo il merge con l'altro computer». Un'altra
  sessione sullo stesso progetto (FASE 1) sta lì accanto.
- **Da allora** (2-4 frasi) unisce la Ripartenza degli handoff e cosa è cambiato dopo: i commit
  arrivati, i todo chiusi (anche quelli chiusi ora dal confronto col git log), le scadenze arrivate,
  un handoff di un'altra macchina. Chiude con la considerazione che ne segue.
- **I todo stanno per filone**, numerati, con l'ID. I filoni vengono dalle righe «filone» della
  RIPARTENZA, coi nomi che la persona riconosce. Senza filoni, un gruppo solo col nome del progetto.
  Entrano tutti i todo aperti del progetto. I todo di «generale» chiudono la lista, nel gruppo «Fuori
  dai progetti». Le scadenze passate salgono in cima al loro filone.
- **Ogni todo ha il verbo all'infinito** e una riga sotto solo se serve: a cosa serve, o cosa manca.
- **La marca viene da chi agisce.** FACCIO IO dà «Faccio io». DECIDI TU, POI FACCIO IO dà «Decidi
  tu». TOCCA A TE dà «Tocca a te: <perché>», col perché del todo quando c'è. Se Claude prepara una parte
  prima del gesto della persona (una bozza, una pagina aperta), vale «Preparo io, poi tu: <perché>».
  FERMO dà «Fermo: aspetta X», con X dal motivo del todo.
- **Un Chi che sembra sbagliato si stima.** Un todo segnato «tocca a te» che Claude può fare da solo,
  senza password, pagamenti, invii a terzi o decisioni della persona, porta la marca «Faccio io
  (stima)». Nell'archivio cambia solo dopo il suo sì.
- **Bozze in attesa** in cima al loro filone, con la data: oltre tre giorni proponi di riscriverle.
- **Da dove partirei** è uno solo, col motivo: il todo di DA DOVE PARTIRE della FASE 1, o uno migliore.
- **Il pannello.** [solo se il controllo della FASE 4 stampa «mod caricato»] dopo la lista scrivi
  «Per chiuderli o spostarli con un tasto: /dafare».
- **Skill del progetto.** Se una skill serve davvero a questo progetto ora (per lo stack, l'handoff o
  i todo), nominala in una riga. Altrimenti niente.
- **La riga di sistema compare solo se qualcosa non va** (sync, pull, conflitti, config): sale in
  cima se blocca il lavoro.
- **Il messaggio chiude senza menu**, con le parole di risposta in grassetto. La persona risponde a
  parole.

## FASE 6: La risposta della persona

- **Correzioni.** "8 a te" o "7 scarta" vanno subito nell'archivio, e riporti la riga di conferma:
  `python3 ~/.claude/bin/arturo todo modifica ID --chi tu|decidi|io` oppure
  `python3 ~/.claude/bin/arturo todo scarta ID "motivo"`, col motivo nelle sue parole. Non spostare un
  todo da tu a io o decidi senza un suo sì.
- **"tutto il delegabile".** Esegui in sessione, uno dopo l'altro, i todo "Faccio io" reversibili,
  stime comprese dopo il suo sì. Chiudi ognuno solo dopo aver controllato il risultato vero (il test
  che passa, il file che c'è, la pagina che si apre): poi `arturo todo fatto ID`. Di un "Preparo io,
  poi tu" fai la tua parte e il todo resta aperto. Davanti a un'azione con effetti che non si annullano
  (un invio, un pagamento, una cancellazione) ti fermi e chiedi.
- **Un filone o dei numeri.** Parti da quei todo. Il task di sessione (`TaskCreate`) nasce solo per
  i todo scelti: due numerazioni insieme confondono i numeri.
- **"qualcosa non torna".** Se la persona dice che Arturo o il progetto non funzionano come si
  aspetta, apri con Read `~/.claude/commands/diagnosi.md` e seguilo.

## Con un compito

Con " -- <compito>" negli argomenti la ripartenza esce breve: il titolo, "Da allora" in una o due
frasi, una riga per filone col numero di todo e quanti sono "Faccio io". Al posto di "Da dove
partirei" scrivi "Oggi: <compito>", con l'ID del todo che lo copre se esiste. Poi carica
`prompt-master` col tool `Skill` sul compito, mostra PROMPT e BRIEF come li prescrive la skill e parti
senza aspettare una scelta.

Esegui ora la FASE 0, poi la FASE 1 su $ARGUMENTS.
