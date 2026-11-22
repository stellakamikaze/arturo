---
description: >-
  Apre la sessione su un progetto: sync, contesto (git, handoff, todo con chi agisce, scadenze) e la
  ripartenza per filone. Le parole dopo il nome, o dopo " -- ", sono il compito. Un nome non trovato
  porta i nomi simili. Con " -- --rotazione <compito>" (lo scrive il mod rotazione) riparte in una riga.
argument-hint: "<nome-progetto> [--tutti] [<compito>]"
---

# Inizio sessione

Argomenti: **$ARGUMENTS**. Le parole dopo il nome del progetto, o dopo " -- ", sono il compito della
sessione (vedi "Con un compito" qui sotto); una frase senza nome di progetto è tutta compito. `--tutti` è un flag: aggiorna anche tutti i progetti (FASE 0) e non entra nel nome. Senza nome
usa la cartella in cui sei. Con `--tutti` e senza nome ti fermi dopo la FASE 0.

## Con un compito

Con la riga `compito:` nell'uscita la ripartenza esce breve: il titolo, "Da allora" in una o due
frasi, una riga per filone col numero di todo e quanti sono "Faccio io". Al posto di "Da dove
partirei" scrivi "Oggi: <compito>", con l'ID del todo che lo copre se esiste. Se la FASE 1 stampa
FACCIO IO FERMI, aggiungi una riga: "Todo di Claude fermi da più di 3 giorni: #12 (7 g), #13 (5 g).
Dopo il compito ne chiudo uno breve, o chiedo se toglierlo." A compito finito mantieni la promessa:
riprendine uno, o chiedi alla persona se scartarlo o passarlo a lei. Poi carica
`prompt-master` col tool `Skill` sul compito, mostra PROMPT e BRIEF come li prescrive la skill e parti
senza aspettare una scelta.

## Modo rotazione

Il contesto stampa `rotazione: sì` quando la sessione l'ha aperta il mod `rotazione`, dopo un
`/fine --rotazione`: la persona non ha scritto niente e il lavoro continua da solo.
- FASE 0 e FASE 1 restano intere: sync, contesto, altre sessioni, worktree.
- La ripartenza è una riga: "Ripreso <progetto> · <step N+1 di M, se c'è un piano> · <compito>". Niente
  elenco dei todo e niente "Da allora", salvo un fatto che cambia il lavoro (commit di un'altra sessione,
  conflitto, scadenza arrivata): quello va in una seconda riga. I FACCIO IO FERMI della FASE 1 stanno
  anche loro in una riga sola, con ID e giorni: la rotazione è il caso in cui il compito nuovo li scavalca.
  L'avviso della terza sessione aperta non compare: la rotazione non apre una sessione in più.
  Nemmeno la domanda dell'intervista o la proposta di uno spazio: in rotazione nessuno risponde, e
  `arturo contesto` non le stampa.
- Se l'handoff ha la riga `- Piano: <percorso>`, leggi il piano e prendi lo step dopo quello fatto.
- `prompt-master` si carica come in ogni sessione nuova, ma il brief è una riga, "Brief: <compito>": il
  brief pieno l'ha avuto lo step prima. Poi parti subito.
- A compito chiuso vale di nuovo `/fine --rotazione`, e il giro riparte se il passo dopo è di Claude.
- Con la riga `in attesa: <domanda>` non parti: la sessione di prima ha fatto una domanda alla persona dopo
  la rotazione, e la risposta non è arrivata (segnalazione n. 65). La ripartenza è la riga "Ripreso…" e
  sotto la domanda, con le parole di risposta in grassetto. Aspetti la risposta prima di ogni lavoro.

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
# Col plugin il codice sta fuori da ~/.claude, che non è il repository di Arturo: niente git, l'aggiornamento
# si controlla sul catalogo firmato (review del 7/11/2026, finding 76).
PLUGIN=0
[ -n "${ARTURO_CODICE:-}" ] && [ "$(cd "$ARTURO_CODICE" 2>/dev/null && pwd -P)" != "$(cd ~/.claude 2>/dev/null && pwd -P)" ] && PLUGIN=1
if [ "$PLUGIN" = 1 ]; then
  VERIFICA=$(python3 ~/.claude/bin/aggiornamenti.py plugin --verifica 2>&1); FIRMA=$?
  case "$FIRMA" in
    0) case "$VERIFICA" in *"GIÀ AGGIORNATO"*) ;; *"DA RIMETTERE"*) echo "ARTURO: la copia del plugin non è come il rilascio firmato: /aggiorna la reinstalla e la controlla" ;; *) echo "ARTURO: c'è la versione $(printf '%s\n' "$VERIFICA" | tail -1) — i rilasci firmati si installano da soli alla chiusura, o subito con /aggiorna" ;; esac ;;
    3) echo "ARTURO: possibile compromissione: non aggiornare, segnala a chi mantiene Arturo ($(printf '%s\n' "$VERIFICA" | tail -1))" ;;
    4) echo "ARTURO: questo computer non sa controllare la firma dei rilasci (servono git 2.34 e OpenSSH 8.2): Arturo non si aggiorna finché non li aggiorni. Non è un problema di sicurezza" ;;
    *) echo "Config sync: controllo aggiornamenti non riuscito: $(printf '%s\n' "$VERIFICA" | tail -1)" ;;
  esac
else
ORIGIN_URL=$(git -C ~/.claude remote get-url origin 2>/dev/null || echo "")
case "$ORIGIN_URL" in
  *github.com[:/]stellakamikaze/arturo|*github.com[:/]stellakamikaze/arturo.git) ORIGIN_ARTURO=1 ;;
  *) ORIGIN_ARTURO=0 ;;
esac
export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
if [ "$ORIGIN_ARTURO" = 1 ] || [ -z "$ORIGIN_URL" ]; then
  git -C ~/.claude fetch --quiet --tags origin main 2>&1 || echo "Config sync: controllo aggiornamenti non riuscito (rete?)"
else
  # Gli archivi della persona non fermano il pull, come in bin/aggiorna-applica.sh (segnalazione n. 14).
  MODIFICATI=$(git -C ~/.claude status --porcelain --untracked-files=no -- . ':(exclude)data/handoffs' ':(exclude)data/todo' ':(exclude)data/memory' | cut -c4-)
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

`$ARGUMENTS` può contenere `--tutti` e il compito della sessione, dopo il nome o dopo " -- ": lo
script trova il progetto nelle prime parole e il nome resta pulito. Senza nome usa la cartella in cui sei.

```bash
# Tutto il contesto in un processo solo: tra due blocchi bash le variabili si perdono.
# Gli argomenti passano su stdin, fra le due righe ARGOMENTI e mai nella riga di comando: il compito
# può contenere virgolette, # e $(...), e la shell li taglierebbe o li eseguirebbe.
python3 ~/.claude/bin/arturo contesto --stdin <<'ARGOMENTI'; echo "rc=$?"
$ARGUMENTS
ARGOMENTI
```

Se c'è un compito, lo script lo stampa nella riga `compito:`. Se stampa `NOME: interpretato "X" come Y`,
ha scelto l'unico progetto che somiglia al nome: scrivilo nella prima riga della ripartenza, così la
persona corregge subito se intendeva un altro progetto. `FILONI NOTI` elenca i filoni di tutti gli
handoff del progetto.

Lo script legge e non scrive niente. Calcola lo slug del progetto come `/fine`
(`basename | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'`), così
ritrova gli handoff e i todo della cartella. Stampa, in quest'ordine:
- `PROGETTO` e la riga `cartella:` (il percorso, oppure `nessuna`);
- la riga `quota:` con la finestra di 5 ore e quella della settimana, come le ha viste la barra in
  basso; manca se la barra non ha ancora un dato valido;
- `SCHEDA DEL PROGETTO`: la scheda che `/fine` scrive nella memoria, con cos'è, decisioni chiuse ed
  errori da non ripetere. Manca a memoria spenta o senza scheda. La cartella scritta nella scheda vale
  anche fuori dalla base dei progetti, e la scheda da sola basta a trovare il progetto;
- `GIT`: branch, modifiche non salvate, CONFLITTI DI MERGE, i commit arrivati dopo l'ultimo handoff;
  e i RAMI CON COMMIT che il branch corrente non ha, col worktree se ne hanno uno e con "chiuso da
  /fine" se la sessione l'ha segnato (un ramo coi commit già arrivati con un cherry-pick o un rebase
  non compare);
- `RIPARTENZA`: la Ripartenza e il prossimo passo degli handoff degli ultimi 14 giorni, col filone
  quando c'è, e il percorso dell'ultimo handoff da leggere per intero. La riga `SALVATO IN AUTOMATICO`
  dice che l'ultima sessione si è chiusa senza `/fine`: l'handoff l'ha scritto Arturo dal transcript,
  con le ultime richieste e il lavoro aperto;
- i todo aperti del progetto divisi per chi agisce (TOCCA A TE, DECIDI TU POI FACCIO IO, FACCIO
  IO, FERMO), i FACCIO IO FERMI DA PIÙ DI 3 GIORNI (nessun passo vero: una nota non conta), i todo
  chiusi dopo l'ultimo handoff, le SCADENZE dei prossimi 7 giorni anche fuori dal progetto, il todo DA
  DOVE PARTIRE e gli avvisi.
- `INTERVISTA`: nelle prime sei settimane dopo `/setup`, al massimo una domanda al giorno su quello che
  Arturo non sa ancora del lavoro della persona: cosa fa, per chi, come. Le domande stanno in
  `~/.claude/docs/mestieri.md`, per famiglia di mestiere. Manca in rotazione, a memoria spenta, a intervista spenta
  o se oggi una domanda c'è già stata.
- `SPAZIO`: nei giorni senza domanda dell'intervista, al massimo una proposta a settimana di uno spazio,
  col segnale che l'ha fatta nascere: Melchior se la memoria è spenta e il lavoro cresce, l'Orsa se
  corregge la stessa cosa in più sessioni. Ogni spazio si propone una
  volta sola. Manca in rotazione e a proposte spente.

Con `rc=0` entra nella cartella della riga `cartella:` con `cd "<cartella>"`: la sessione e
`/fine` lavorano lì. Con `cartella: nessuna` il progetto vive solo negli handoff o nei todo:
resta dove sei.

Dopo il `cd` lancia `python3 ~/.claude/bin/arturo scoperta impronta`: prende l'impronta dei file di testo
del progetto, e `/fine` la confronta per vedere le modifiche fatte a mano (la Scoperta). La sua riga non
va nella ripartenza.

Se dopo il `cd` Claude Code risponde "Shell cwd was reset", la cartella sta fuori dalle cartelle
della sessione e ogni comando torna alla cartella di partenza. Di' alla persona in una riga di
scrivere `/add-dir <cartella>`, o di riaprire Claude Code da lì. Fino ad allora ogni comando, anche
in `/fine`, comincia con `cd "<cartella>" &&`: senza, `arturo todo --progetto .` e lo slug di
`/fine` prendono la cartella di partenza (segnalazione n. 37, 30/10/2026).

- **Pull.** Se il progetto ha un remote, aggiornalo senza riscrivere la storia:

  ```bash
  git remote 2>/dev/null | grep -q . && { GIT_TERMINAL_PROMPT=0 git pull --ff-only 2>&1 || echo "Pull non riuscito: il progetto e il remote hanno storie diverse. Non ho toccato niente."; }
  ```

  Se il pull non riesce, dillo alla persona: niente rebase in automatico. Se `GIT` mostra CONFLITTI
  DI MERGE, risolvili PRIMA di tutto il resto. I commit arrivati vanno nel «Da allora».
- **Rami non riportati.** Un ramo coi commit di una sessione (nome `<slug>-<aaaammgg-hhmm>`, o con
  un worktree) è lavoro che `/fine` non ha riportato nella cartella principale: va in cima alla
  ripartenza, col numero dei commit. Proponi di riportarlo con `git merge --ff-only <ramo>`; se non
  basta e la cartella principale non ha modifiche, `git merge --no-edit <ramo>`, con `git merge
  --abort` al primo conflitto. Un conflitto lo dici alla persona e non lo risolvi da solo. Gli altri
  rami (prove, vecchie versioni) restano una riga col conteggio (segnalazione n. 20, 27/10/2026).
  Un ramo "chiuso da /fine, da riportare" viene da una sessione che non poteva toccare il tree
  principale (riporto differito di `~/.claude/shared/fine-worktree.md`, #4007). Non serve proporlo:
  dal tree principale, fuori da un worktree, lo riporti tu coi passi 5-8 di quel file, prima del
  lavoro. Da dentro un worktree non lo tocchi: lo fa il prossimo `/inizio` nel tree principale.
- **Altre sessioni.** Lancia `ListAgents`. Un'altra sessione di Claude Code sullo stesso progetto va
  in cima alla ripartenza, con quello che sta facendo.
- **Terza sessione aperta.** Il limite delle 5 ore è uno solo per tutte le sessioni dell'account, anche
  su altri computer. Dal 15/10 al 4/11 è scattato 9 volte, sempre con tre sessioni o più, e ogni volta
  ha fermato più progetti insieme (proposta n. 54, 4/11/2026). Conta nell'elenco di `ListAgents` le
  sessioni di qualunque progetto che stanno lavorando (busy) e quelle aperte in un terminale di questo
  computer (interactive, idle). Le sessioni offline non contano, e nemmeno quelle remote o cloud ferme
  (idle): non consumano. Se le sessioni contate sono 2 o più, la ripartenza apre con una riga: "Ci sono
  già 2 sessioni aperte (<nome>, <nome>). Il limite delle 5 ore vale per tutte: con questa terza arriva
  prima." Se la FASE 1 stampa la riga `quota:`, aggiungi la percentuale e l'orario delle 5 ore. È solo un
  avviso: il lavoro parte lo stesso, e chiudere una sessione lo decide la persona. In rotazione l'avviso
  non compare: la sessione era già aperta.
- **Worktree, solo se c'è quella sessione.** Due sessioni nella stessa cartella si pestano i piedi:
  test, build e commit vedono anche il lavoro dell'altra. Prima di qualsiasi modifica entra con
  `EnterWorktree` (nome `<slug>-<aaaammgg-hhmm>`). Parte dall'ultimo commit locale perché
  `settings.json` ha `worktree.baseRef: "head"`: la descrizione del tool dice `fresh`, cioè la copia
  online, ma quello è il default senza la chiave. Appena dentro, confronta `git rev-parse HEAD` con
  l'HEAD della cartella principale. Se sono diversi, esci con `ExitWorktree`, crea la copia con
  `git worktree add -b <nome> .claude/worktrees/<nome> HEAD` e rientra con `EnterWorktree` e `path`
  (segnalazione n. 45, 3/11/2026). Prima aggiungi
  `.claude/worktrees/` e `node_modules` a `<cartella>/.git/info/exclude`, se mancano: quel file vale per
  tutti i worktree del repository, resta sulla macchina e non tocca il `.gitignore` del progetto. La ripartenza dice
  che la sessione lavora in una copia a parte, e `/fine` riporta il lavoro nella cartella principale.
  Nel worktree la guardia di Claude Code rifiuta i comandi che non sa leggere: scrivi un comando per
  chiamata, senza cicli, variabili, `$(...)`, heredoc (`python3 - <<'E'`) né `cd ... &&`. Un ciclo,
  un heredoc o una copia di più file va in uno script nello scratchpad, lanciato con `python3 <file>`
  o `bash <file>` (segnalazione n. 15, 26/10/2026). I file nuovi nascono nel worktree, anche quelli
  ignorati da git, e `/fine` li riporta nella cartella principale (segnalazione n. 13, 26/10/2026).
  Sessione unica: resta nella cartella principale.

## FASE 2: Progetto non trovato

Con `rc=2` lo script stampa `NON TROVATO` e i progetti con un nome simile: spesso è un refuso.
Proponi i candidati e aspetta la scelta. Se l'uscita ha la riga `compito:`, la persona ha scritto cosa
vuole fare senza il nome del progetto: proponi il progetto più vicino al compito, oppure di lavorare qui
senza progetto, e col sì parti sul compito senza farglielo riscrivere. Se quel lavoro riprende nei giorni
dopo, `/fine` lascia un handoff breve col nome del lavoro, e `/inizio <nome>` lo ritrova (#4071). Per una vista di cosa c'è da fare ovunque leggi
`~/.claude/data/handoffs/INDEX.md` (una riga per progetto con stato e prossimo passo) e proponi
da lì. Con `rc=3` il nome non è valido: chiedi quello giusto.

Se la persona dice che è un progetto nuovo, chiedi in una frase cosa è. Non creare cartelle e non
lanciare `git init` senza un sì. Col sì crei il progetto in `PROJECTS_BASE`, poi rilanci la FASE 1
col nome nuovo:

```bash
BASE="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"
case "$BASE" in "~"*) BASE="$HOME${BASE#\~}" ;; esac   # la tilde fra virgolette non si espande (segnalazione n. 19)
NOME="nome-del-progetto"   # minuscole e trattini, come lo slug della FASE 1
mkdir -p "$BASE/$NOME" && cd "$BASE/$NOME" && git init -q -b main
printf '.DS_Store\nnode_modules/\n*.log\n.env\n' > .gitignore
```

Scrivi un `CLAUDE.md` breve: cosa è il progetto in due righe, e una sezione "Materiali" con i
percorsi dei file che stanno fuori dal repo (all'inizio può essere vuota). Poi il primo commit, con l'identità di Git scelta da `/setup`:
`bash ~/.claude/bin/identita-git.sh . && git add .gitignore CLAUDE.md && git commit -q -m "inizio del progetto"`. Gli handoff non entrano
mai nel repo del progetto.

Se lo script stampa `AVVISO`, il commit parte con l'identità automatica di Git: riporta la riga nella
ripartenza, con l'invito a sceglierne una con `/setup`. Solo `MANCA` ferma il commit: riportalo, e il
progetto resta senza il primo commit finché la persona non sceglie l'identità.

## FASE 3: Carica il contesto

Leggi in ordine, se esistono:
1. il `CLAUDE.md` del progetto. Le decisioni chiuse e gli errori della `SCHEDA DEL PROGETTO` della FASE 1
   valgono come vincoli: non si rimettono in discussione;
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
# Le letture partono insieme e il comando aspetta la più lenta: con una fonte esterna dei task ognuna
# può aspettare la rete fino a 90 s (#6368). Il progetto è quello della cartella (FASE 1 ci è entrata),
# calcolato dalla CLI come per "ricordami di…". Gli avvisi ("Attenzione: …") restano visibili: dopo il
# pull un todo può aver cambiato numero.
python3 ~/.claude/bin/arturo apertura
```

Le sezioni escono in quest'ordine:
- `PROGETTO`: il progetto dei todo della cartella.
- `TODO DEL PROGETTO`: la lista che hai già dalla FASE 1, con gli avvisi di rinumerazione.
- `TODO DI GENERALE`: i todo presi fuori da un progetto (nella HOME, in /setup, fuori da git). Se il
  progetto è `generale`, la sezione rimanda alla lista sopra.
- `GIT LOG`: gli ultimi 20 commit, per il confronto del punto 1.
- `PANNELLO`: "mod caricato" se il pannello /dafare c'è. I comandi di un mod non compaiono fra quelli
  che vedi, e la riga li legge da `claude plugin list --json`.

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
- **Salvato in automatico.** Con la riga `SALVATO IN AUTOMATICO` il "Da allora" comincia così: "L'ultima
  volta non hai chiuso con /fine: ecco cosa stavi facendo", con l'ultima richiesta e il lavoro aperto
  in parole semplici. Poi una riga: "Il primo /fine di oggi lo completa".
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
- **Todo di Claude fermi.** Se la FASE 1 stampa FACCIO IO FERMI, la lista li segna con «fermo da N g».
  Uno che chiede le mani della persona (una prova a banco, un gesto, un accesso) era assegnato male:
  marcalo «Tocca a te (stima)» e proponi la correzione «N a te» (proposta n. 52, 4/11/2026).
- **Da dove partirei** è uno solo, col motivo: il todo di DA DOVE PARTIRE della FASE 1, o uno migliore.
- **Il pannello.** [solo se il controllo della FASE 4 stampa «mod caricato»] dopo la lista scrivi
  «Per chiuderli o spostarli con un tasto: /dafare».
- **Skill del progetto.** Se una skill serve davvero a questo progetto ora (per lo stack, l'handoff o
  i todo), nominala in una riga. Altrimenti niente.
- **La riga di sistema compare solo se qualcosa non va** (sync, pull, conflitti, config): sale in
  cima se blocca il lavoro.
- **La domanda dell'intervista.** [solo se la FASE 1 stampa `INTERVISTA`] prima della riga di risposta
  metti una riga: "Una domanda per conoscerti meglio: <domanda>", e sotto "Rispondi quando vuoi, oppure
  **salta**". La domanda non ferma il lavoro: con un compito parti lo stesso.
- **La proposta di uno spazio.** [solo se la FASE 1 stampa `SPAZIO`] prima della riga di risposta metti
  due righe con parole tue: cosa hai visto (il "perché" della riga, coi suoi numeri) e cosa proponi (la
  "proposta"). Sotto: "Se ti va, scrivimi **sì**; se no, **no** e non te lo ripropongo". Anche la proposta
  non ferma il lavoro.
- **Il messaggio chiude senza menu**, con le parole di risposta in grassetto. La persona risponde a
  parole.
- **La checklist di Volta.** [solo se la FASE 1 stampa `VOLTA`] Subito dopo la ripartenza passa lo stesso
  elenco, con gli stessi numeri e le stesse parole, a `arturo ripartenza scrivi` su stdin, in un solo comando
  Bash. La persona lo vede in Volta come checklist con una nota per riga, e la sua scelta torna qui come
  messaggio (FASE 6). Senza la riga `VOLTA` salta questo passo: Volta non c'è, e nessuno leggerebbe il file. Exit 2 = schema rotto: correggi il campo che dice e
  rilancia. Non vale per il Modo rotazione e per la ripartenza breve di "Con un compito", che non hanno
  l'elenco numerato. `id` è il numero del todo, oppure `null` per una riga senza todo.
  ```bash
  python3 ~/.claude/bin/arturo ripartenza scrivi <<'RIPARTENZA'
  {"progetto": "<progetto>", "titolo": "<la riga del titolo>",
   "filoni": [{"nome": "<filone>", "voci": [{"n": 1, "id": 5, "testo": "<todo>", "marca": "<marca>", "sotto": "<riga sotto o vuoto>"}]}],
   "partenza": {"n": 1, "motivo": "<il motivo di Da dove partirei>"}}
  RIPARTENZA
  ```

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
- **La risposta dalla checklist di Volta.** Arriva come un messaggio della persona, con i numeri della
  ripartenza: "Lavora su 2 5. Già fatto: 3. Scartati: 4. Rimandati: 6. A Claude: 7. A me: 8. Note: 2:
  testo. Nota generale". Ogni parte vale come se la persona l'avesse scritta a parole. "Lavora su" sono
  i numeri da cui parti. "Già fatto" chiude il todo con `arturo todo fatto ID`: lo dice la persona, e
  non serve un controllo tuo. "Scartati" usa `arturo todo scarta ID "<motivo>"`, col motivo dalla sua
  nota o "scartato dalla checklist". "Rimandati" usa `arturo todo modifica ID --quando "più avanti"`. "A
  Claude" usa `--chi io`, "A me" usa `--chi tu`. Una nota sotto un numero vale per quel todo, la nota
  generale per tutta la sessione. Una riga senza todo (`id` nullo) si tratta a parole. Riporta in una
  riga cosa hai scritto nell'archivio, poi parti da "Lavora su".
- **La risposta all'intervista.** Riscrivi la risposta in una o due frasi coi fatti della persona, senza
  aggiungerne. Mostrala e chiedi: "La salvo nella memoria?". Solo col sì lancia
  `python3 ~/.claude/bin/arturo intervista risposta <id> --testo "<le frasi approvate>"`: la nota entra
  come `persona-<id>` e la annuncia `/fine`. Se la risposta dice il mestiere, fissa anche la famiglia con
  `arturo intervista famiglia <1-6>`. Con **salta** lancia `arturo intervista salta <id>`. Con "basta
  domande" lancia `arturo intervista spegni`. Un no al salvataggio non salva niente, e la domanda può
  tornare un altro giorno.
- **La skill dal lavoro che torna.** [solo se `arturo intervista risposta` stampa la riga `SKILL`] La
  persona ha appena detto quale lavoro rifà ogni settimana o ogni mese. Chiedile, una volta sola: "Vuoi
  che ne faccia una skill tua, così non me lo rispieghi ogni volta?". Col sì apri con Read
  `~/.claude/commands/creaskill.md` e seguilo: la sua risposta vale come domanda 1 e riparti dalla 2. Poi
  lancia `arturo intervista skill si`. Col no lancia `arturo intervista skill no`. La riga `SKILL` esce
  una volta sola: senza risposta non richiedere.
- **La risposta alla proposta di uno spazio.** Col sì esegui il passo della riga `col sì` di `SPAZIO`:
  per Melchior accendi la memoria;
  per l'Orsa scrivi la regola in una riga, mostrala e solo col suo sì sul testo aggiungila al suo
  `CLAUDE.md`. Poi lancia `python3 ~/.claude/bin/arturo spazi si <spazio>`. Col no lancia
  `arturo spazi no <spazio>`, con "basta proposte" `arturo spazi spegni`. Senza risposta non fare niente:
  la proposta non torna comunque.
- **Il nome.** Se la persona vuole chiamare Arturo in un altro modo ("chiamati Bruno"), lancia
  `python3 ~/.claude/bin/arturo nome "<nome>"`: il nome sta nell'Orsa e l'avvio lo ripete a ogni sessione.
  Da subito usalo quando parli di te.
- **"qualcosa non torna".** Se la persona dice che Arturo o il progetto non funzionano come si
  aspetta, apri con Read `~/.claude/commands/diagnosi.md` e seguilo.

Esegui ora la FASE 0, poi la FASE 1 su $ARGUMENTS.
