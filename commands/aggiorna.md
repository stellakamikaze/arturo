---
description: Scarica e applica l'ultima versione di Arturo, poi racconta cosa è cambiato. Con `indietro`, riporta alla versione prima dell'ultimo aggiornamento. Con `personale`, sposta le modifiche ai comandi di Arturo in file suoi
argument-hint: "(nessuno) | indietro | personale"
---

# Aggiorna

Porti la copia di Arturo di chi ti parla all'ultima versione. Di solito non serve: dal 16/10/2026
Arturo si aggiorna da solo alla chiusura della sessione, con i soli rilasci firmati
(`bin/aggiornamenti.py`). `/aggiorna` serve quando l'avvio o la barra in basso dicono "serve
/aggiorna" (modifiche non salvate, conflitto, aggiornamenti a mano), per tornare indietro, per le
aggiunte personali, o quando la persona vuole guardare prima.

`/aggiorna` applica **solo l'ultimo rilascio con un tag firmato**, con la stessa verifica
dell'aggiornamento automatico (`bin/aggiornamenti.py firmato`), e legge la procedura da quel tag.
Non applica mai `main`: i commit pubblicati dopo l'ultimo tag non arrivano. Se l'ultimo tag non è
firmato, o la firma non torna, compare `POSSIBILE COMPROMISSIONE`: niente si applica, neanche con
il suo sì (vedi il Passo 1). Se invece compare `FIRMA NON VERIFICABILE` (uscita 4), il computer non sa
controllare la firma: non è una compromissione, niente si applica finché la persona non aggiorna git e
OpenSSH, e lo dici senza allarme.

Chi ti parla **potrebbe non essere una persona tecnica**: niente gergo di Git, nessun output
grezzo incollato senza spiegazione.

## Passo 1 — Guarda cosa c'è di nuovo

Gli aggiornamenti arrivano da `upstream` se ha un repository suo come `origin` (vedi `/setup`
FASE 7), altrimenti da `origin`.

```bash
cd ~/.claude
export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
NOTA=$(git rev-parse -q --verify "$SRC/main" || echo "")
git fetch --quiet --tags "$SRC" main 2>&1 || echo "fetch non riuscito (rete?)"
if [ -n "$NOTA" ] && ! git merge-base --is-ancestor "$NOTA" "$SRC/main"; then
  echo "STORIA RISCRITTA: la versione pubblicata non discende più da quella che conoscevi"
fi
echo "Versione installata: $(git describe --tags --abbrev=0 --match 'v*' HEAD 2>/dev/null)"
# Solo l'ultimo tag firmato di $SRC, verificato con la chiave già installata: main non si applica mai.
TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato) || TAG=""
if [ -n "$TAG" ]; then
  echo "Versione disponibile (firmata): $TAG"
  BEHIND=$(git rev-list --count "HEAD..$TAG" 2>/dev/null || echo 0)
  echo "Aggiornamenti da $SRC: ${BEHIND:-0}"
  git log --oneline "HEAD..$TAG" 2>/dev/null | head -50
  echo "--- file che cambiano"
  git diff --stat "HEAD...$TAG" 2>/dev/null | tail -40
fi
```

Se compare `POSSIBILE COMPROMISSIONE`, **fermati e non applicare niente**, neanche col suo sì.
L'ultimo rilascio pubblicato non ha la firma di chi mantiene Arturo, o la firma non torna con la
chiave che ha già: è il segno di un repository manomesso. Diglielo con queste parole: "possibile
compromissione: non aggiornare, segnala a chi mantiene Arturo". Proponi `/segnala`, oppure la
segnalazione privata descritta in `SECURITY.md`. Non cercare un'altra strada per aggiornare
(`main`, un tag più vecchio, un `git pull`): la verifica esiste per questo.

Se compare `FIRMA NON VERIFICABILE`, il suo computer non sa controllare la firma: servono git 2.34
e OpenSSH 8.2, o più recenti. Non applicare niente nemmeno qui, ma non parlare di compromissione:
aiutalo ad aggiornare git e OpenSSH (su macOS con Homebrew, `brew install git openssh`), poi
rilancia `/aggiorna`.

Se compare `NESSUN RILASCIO`, la sorgente degli aggiornamenti non ha tag: non c'è niente da
applicare. Diglielo in una riga e fermati.

Se `BEHIND` è `0`, diglielo in una riga (è già aggiornato) e fermati.

Se compare `STORIA RISCRITTA`, **fermati e non applicare niente**. Spiegagli che la storia
pubblicata di Arturo è cambiata rispetto a quella che la sua copia conosceva. Può essere una
correzione dell'autore, ma è anche il segno di un repository compromesso. Suggerisci di
controllare le novità del progetto su GitHub prima di aggiornare.

**Leggi cosa cambia nel codice che gira da solo**, prima di chiedere il sì. Prima le guardie
(`hooks`) e i permessi (`settings.json`), interi e senza taglio: sono i file che decidono cosa
Claude può fare sul suo computer. Poi l'elenco completo dell'altro codice che gira da solo: la
CLI `arturo` (`bin`), gli script delle skill (`skills/*/scripts`), i banchi che l'avvio lancia da
solo ogni 12 ore (`tests`), gli strumenti come `scrape` (`tools`) e ogni file dei mod di Claude
Code (una cartella di `skills/` con `.claude-plugin/plugin.json`, come il pannello `/dafare`).

```bash
cd ~/.claude
TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato) || exit 1
echo "=== guardie e permessi di $TAG, interi"
git diff "HEAD...$TAG" -- hooks settings.json 2>/dev/null
echo "=== codice che gira da solo: righe aggiunte e tolte, file per file"
git diff --name-only "HEAD...$TAG" -- bin tests tools skills 2>/dev/null | while IFS= read -r f; do
  case "$f" in
    bin/*|tests/*|tools/*|skills/*/scripts/*) echo "$f" ;;
    skills/*/*)
      m=${f#skills/}; m="skills/${m%%/*}"
      { git cat-file -e "$TAG:$m/.claude-plugin/plugin.json" || git cat-file -e "HEAD:$m/.claude-plugin/plugin.json"; } 2>/dev/null && echo "$f" ;;
  esac
done | while IFS= read -r f; do
  git diff --numstat "HEAD...$TAG" -- "$f" 2>/dev/null   # righe aggiunte, tolte, file
done
```

Poi leggi il diff di **ogni** file dell'elenco, uno per volta e intero:
`git diff "HEAD...<tag>" -- "FILE"`, con il tag firmato che il blocco ha stampato. Un font o un'immagine basta nominarli. Se un output
arriva tagliato, dillo e leggi il resto a pezzi (`| sed -n '1,400p'`, poi `'401,800p'`):
niente sì su un diff letto a metà. Lascia i percorsi tra virgolette: così la shell non li
espande, e git mostra anche i file delle cartelle che questa copia non ha ancora, come un mod
nuovo. Il pannello `/dafare` è codice che gira da solo dentro Claude Code e lancia la CLI `arturo`.
Raccontagli in parole semplici cosa cambia nelle guardie, nei permessi e nel codice che lancia. Segnala in modo
esplicito ogni modifica che manda dati fuori dal computer, che cancella file, o che rende una
guardia meno severa. Un aggiornamento è codice di altri che gira sul suo computer: è il motivo
per cui questo passo esiste.

## Passo 2 — Controlla le sue modifiche

Le sue modifiche possono stare in due posti: file cambiati e non ancora salvati, e commit suoi
(per esempio il "session sync" di `/fine`).

```bash
cd ~/.claude
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato) || exit 1
git status --short --untracked-files=no
echo "--- file che hai cambiato rispetto ad Arturo"
git diff --stat "$TAG...HEAD" 2>/dev/null | tail -20
echo "--- file cambiati sia da te sia dall'aggiornamento"
comm -12 <(git diff --name-only "$TAG...HEAD" 2>/dev/null | sort) <(git diff --name-only "HEAD...$TAG" 2>/dev/null | sort)
if [ "$SRC" = upstream ]; then
  VIS=$(gh repo view "$(git remote get-url origin)" --json visibility -q .visibility 2>/dev/null)
  echo "--- il suo repository della config: ${VIS:-visibilità sconosciuta}"
fi
```

Se ci sono file cambiati da tutti e due, **mostraglieli e chiedi conferma prima di procedere**:
sono i punti dove può nascere un conflitto. Sono suoi, e un aggiornamento non deve mangiarseli.
I comandi di Arturo (`commands/<nome>.md`) e i due hook di sessione (`hooks/session-start.sh`,
`hooks/session-end.sh`) non contano: li sistema da solo il Passo 3 (Passo 2b).
Contano invece se ha un suo repository della config e la riga qui sopra non dice `PRIVATE`: lì il
Passo 3 non li sposta, e un comando cambiato da tutti e due può andare in conflitto come ogni file.

### Passo 2b — Le sue aggiunte ai comandi e agli hook di sessione

Non deve fare niente, salvo con un suo repository della config che non è privato (sotto,
`NON SEPARATO`). Se ha modificato un comando di Arturo (`commands/<nome>.md`) che anche
l'aggiornamento cambia, il Passo 3 sposta le sue modifiche in `~/.claude/personale/<nome>.md`. Il
comando torna quello di Arturo, le sue righe restano sue, e quando lancia `/<nome>` l'avvio del
prompt dice a Claude di leggerle. Così il comando non va in conflitto, né adesso né dopo. Lo
spostamento avviene nella copia di prova: se l'aggiornamento si annulla, non cambia niente.

Il Passo 3 stampa una riga `SEPARATO: /<nome> -> personale/<nome>.md` per ogni comando spostato.
Diglielo in una frase: "le tue aggiunte a /inizio ora stanno in un file tuo, e /inizio fa tutto come
prima". Non chiedere conferma e non spiegare il meccanismo, se non lo chiede. Se vuole, rileggete
insieme il file personale: le parti sono copiate così come erano.

Vale lo stesso per `hooks/session-start.sh` e `hooks/session-end.sh`, con una differenza: la riga è
`SEPARATO: hooks/<hook>.sh -> personale/<hook>.sh (righe commentate, da rileggere)`. L'hook di
Arturo esegue quel file alla fine, ma le righe spostate arrivano commentate: tolte dal loro posto
possono non funzionare, o fare altro. Qui la rilettura serve: diglielo in una frase, apri con lei
`~/.claude/personale/<hook>.sh` e togli il `#` alle righe che devono girare, controllando che
reggano da sole (una variabile dell'hook c'è, una dentro un `if` tolto no).

Se stampa `NON SEPARATO`, il suo repository della config non risulta privato: `personale/` non
viaggerebbe fra le sue macchine, quindi le modifiche restano nel comando e un conflitto si risolve
come sotto. Diglielo in una frase, e digli che con un repository privato la prossima volta succede
da solo. `visibilità sconosciuta` vuol dire quasi sempre che `gh` non ha il login: con `gh auth login`
la prossima volta Arturo lo sa.

Se `git status` elenca dei file, sono modifiche sue non ancora salvate con un commit (le scrive
anche `/setup`, per esempio `PROJECTS_BASE` o la lingua in `settings.json`). Il Passo 3 non parte
finché ci sono: un aggiornamento sopra modifiche non salvate può lasciare un file mezzo suo e mezzo
di Arturo. Non contano gli archivi suoi, `data/handoffs/`, `data/todo/` e `data/memory/`: Arturo
non li versiona e il Passo 3 li lascia come sono. Per gli altri file spiegaglielo e proponi di
salvarle prima con un commit, col suo sì:
`git -C ~/.claude commit -am "chore: modifiche locali prima di /aggiorna"`. Poi rilancia il Passo 2:
adesso i file toccati da tutti e due compaiono nell'elenco qui sopra.

## Passo 3 — Applica

Solo dopo il suo sì. Se dice no, vai a "Se dice no" in fondo a questo passo. Ogni blocco gira in
una shell nuova: questo ricava da sé da dove arrivano gli aggiornamenti.

L'aggiornamento non si fa dentro `~/.claude`: lo fa `bin/aggiorna-applica.sh` in una copia di prova a
parte, controlla lì la config, e porta dentro solo un risultato integro. Così un conflitto non scrive
mai marcatori in `settings.json` o negli hook che Claude Code sta usando. La procedura si legge dal
**tag firmato in arrivo**, non dalla versione installata né da `main`: una correzione alla procedura
protegge già l'aggiornamento che la porta, e un `main` manomesso non la sostituisce. È codice che gira
da solo, e il Passo 1 te ne ha mostrato il diff. La firma si verifica di nuovo qui, subito prima.

```bash
cd ~/.claude
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
MODO=$([ "$SRC" = upstream ] && echo merge || echo rebase)
# Con un repository suo, i suoi commit sono gia' pubblicati: il merge non li riscrive.
APPLICA=$(mktemp)
if TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato); then
  git show "$TAG:bin/aggiorna-applica.sh" > "$APPLICA" 2>/dev/null
  if [ -s "$APPLICA" ]; then
    bash "$APPLICA" ~/.claude "$MODO" "$TAG"
  else
    echo "APPLICAZIONE NON PARTITA: il rilascio $TAG non ha la procedura di applicazione. Non ho toccato niente."
  fi
else
  echo "APPLICAZIONE NON PARTITA: nessun rilascio firmato e verificabile da applicare (vedi la riga di firmato qui sopra). Non ho toccato niente."
fi
rm -f "$APPLICA"
```

La prima parola dell'esito dice cosa è successo:

- `APPLICATO`: l'aggiornamento è dentro e la config è integra. La procedura lo ha registrato in
  `session-env/aggiornamenti` (per `/aggiorna indietro`) e in `session-env/ultimo-aggiornamento`.
  Vai al Passo 4.
- `GIÀ AGGIORNATO`: niente da fare.
- `APPLICAZIONE NON PARTITA`: la sua copia non è cambiata. Se il motivo sono file modificati e non
  salvati, diglielo in parole semplici e spiega perché l'aggiornamento aspetta (Passo 2). Col suo sì
  salvali con un commit, poi rilancia il Passo 2 e il Passo 3. Se il motivo è una config già rotta
  (un merge o un pull rimasto a metà da prima), fermati: mostragli le righe `CONFIG ROTTA` e
  sistemale con lui prima di aggiornare. Non scartare mai le sue modifiche per far passare
  l'aggiornamento. Se il motivo è **una copia di prova che aspetta**, l'esito dice da quando e da
  cosa (il sync fra le sue macchine o un aggiornamento). Dentro può esserci il lavoro di chi stava
  risolvendo un conflitto. Proponi di concluderla con "Risolvere un conflitto" qui sotto. Solo se
  lui dice che non serve, col suo sì, scartala:

  ```bash
  cd ~/.claude && bash bin/aggiorna-applica.sh ~/.claude scarta
  ```

  Poi rilancia il Passo 3.
- `APPLICAZIONE ANNULLATA`: la sua copia è **esattamente com'era prima**. Se la riga dice
  `CONFLITTO`, vai a "Risolvere un conflitto" qui sotto.
- `RIPRISTINO NON RIUSCITO`: **fermati**, la config può avere le guardie spente. Digli che la copia è
  rimasta a metà, mostragli i file elencati e lancia `python3 ~/.claude/hooks/controlla-config.py`,
  che dice cosa non va e come tornare a prima. Non lavorare su altro finché non dice `CONFIG OK`.

### Se dice no

Rispetta il no e fermati, dopo aver registrato l'esito per la telemetria di Arturo (dice quali
aggiornamenti le persone non vogliono, mai il perché):

```bash
python3 ~/.claude/bin/telemetria.py registra aggiorna rifiutato >/dev/null 2>&1 || true
```

### Risolvere un conflitto

Con `CONFLITTO` la sua `~/.claude` non è stata toccata. I conflitti stanno nella **copia di prova**,
nella cartella che l'esito ha stampato, con i file elencati. Si risolvono lì, mai in `~/.claude`.

1. Se il file in conflitto è un comando di Arturo (`commands/<nome>.md`), l'esito ha detto
   `NON SEPARATO`: il suo repository della config non risulta privato e lo spostamento non si fa.
   Rilanciare il Passo 3 così com'è riporta allo stesso conflitto. Proponi prima la strada che non si
   ripete: rendere privato il repository (su GitHub, Settings del repository, o `gh auth login` se
   la visibilità era sconosciuta), poi col suo sì scartare la copia di prova (il blocco `scarta` qui
   sopra: le sue modifiche restano in `~/.claude`) e rilanciare il Passo 3, che allora le sposta da solo.
   Altrimenti, o se preferisce così,
   per ogni file in conflitto della copia di prova, mostragli in parole semplici cosa c'era da lui e
   cosa arriva da Arturo, e chiedi cosa tenere. Di solito si tengono tutti e due: per esempio tutte le
   righe di una lista `deny`. Scrivi il file risolto nella copia di prova, senza marcatori.
   Se Arturo ha tolto un comando che lei aveva modificato, il conflitto dice che da una parte è
   cancellato. Se accetta che esca, al punto 2 usa `rm` al posto di `add` per quel file. Se vuole
   tenerlo, il file resta suo e si usa `add` come per gli altri.
2. Chiudi l'aggiornamento nella copia di prova. Con un merge: `git -C <copia> add <file>` per ogni
   file, poi `git -C <copia> commit --no-edit`. Con un rebase: `git -C <copia> add <file>`, poi il
   blocco qui sotto, finché il rebase non finisce.
   Il rebase riparte con l'unione di `settings.json` presa dalla versione in arrivo: senza, i commit
   dopo il conflitto tornano a unire `settings.json` riga per riga.

   ```bash
   cd ~/.claude
   COPIA=$(cut -d' ' -f1 "$(git rev-parse --git-path arturo-aggiorna-copia)" 2>/dev/null)
   L=$(dirname "$COPIA")
   if [ -f "$L/attributi" ] && [ -f "$L/unisci-settings.py" ]; then
     GIT_EDITOR=true git -c "core.attributesFile=$L/attributi" \
       -c "merge.arturo-settings.driver=python3 \"$L/unisci-settings.py\" %O %A %B" -C "$COPIA" rebase --continue
   else
     GIT_EDITOR=true git -C "$COPIA" rebase --continue
   fi
   ```
3. Solo dopo il suo sì, porta il risultato dentro:

```bash
cd ~/.claude
COPIA=$(cut -d' ' -f1 "$(git rev-parse --git-path arturo-aggiorna-copia)" 2>/dev/null)
APPLICA=$(mktemp)
cp "$COPIA/bin/aggiorna-applica.sh" "$APPLICA" 2>/dev/null || cp bin/aggiorna-applica.sh "$APPLICA" 2>/dev/null
if [ -s "$APPLICA" ]; then
  bash "$APPLICA" ~/.claude concludi
else
  echo "APPLICAZIONE NON PARTITA: non trovo la procedura di applicazione. Non ho toccato niente."
fi
rm -f "$APPLICA"
```

Gli esiti sono gli stessi del Passo 3. Se dice che nella copia di prova restano conflitti, torna al
punto 1. Mai `--force`, mai `reset --hard`, mai un `checkout` che butti via il suo lavoro.

## Passo 4 — Riavvio e racconto

Due cose, in quest'ordine:

1. Digli di **chiudere e riaprire Claude Code**. Comandi, hook e skill si leggono all'avvio della
   sessione: finché non riapre, quello che è appena arrivato non esiste per lui. È il passo che si
   dimentica più spesso, quindi dillo esplicitamente. Anche il pannello `/dafare` nuovo c'è solo
   dopo la riapertura.
2. Dopo il riavvio, **`/novita`** gli racconta cosa è cambiato e perché gli conviene saperlo.
3. Se le novità nominano un comando da scrivere nel terminale (`arturo todo`, `arturo web`),
   controlla se ha il comando breve: `type arturo`. Se non c'è, digli la forma che funziona
   sempre (`python3 ~/.claude/bin/arturo …`) e proponigli la FASE 7c di `/setup`, che lo aggiunge.

## Le guardie che ha modificato

Se l'avvio ha mostrato una riga `DERIVA:` che nomina "le guardie di Arturo", una guardia di sicurezza
(o un modulo che la guida) è diversa da quella di Arturo. Protegge come l'ha scritta lei, e nessun
aggiornamento la corregge più. Non è un errore: può averla allentata apposta. Mostrale cosa cambia
col comando `git diff` che la riga indica, spiegando in parole semplici cosa la guardia ferma o
lascia passare in più. Poi chiedi se rimetterla com'è in Arturo. Col suo sì, una guardia per volta:

```bash
python3 ~/.claude/bin/arturo personale ripristina hooks/<guardia>
```

`RIPRISTINATO` vuol dire che la guardia è tornata quella di Arturo e il prossimo `/aggiorna` la porta
all'ultima versione. Se dice di no, rispetta la scelta: la riga tornerà a ogni avvio finché la
guardia resta diversa, e sta a lei. Se una guardia la ferma troppo spesso, proponi `/segnala`: la
correzione giusta va in Arturo, per tutti.

## Le sue aggiunte, senza aggiornare

Se chi ti parla scrive `/aggiorna personale` (oppure l'avvio ha mostrato una riga `DERIVA:` sui
comandi o sugli hook di sessione), non scarichi niente: sposti solo le sue modifiche ai comandi e
agli hook di sessione di Arturo.

```bash
cd ~/.claude
VIS=PRIVATE
if git remote get-url upstream >/dev/null 2>&1; then
  VIS=$(gh repo view "$(git remote get-url origin)" --json visibility -q .visibility 2>/dev/null)
fi
if [ "$VIS" = PRIVATE ]; then
  python3 ~/.claude/bin/arturo personale separa
else
  echo "NON SEPARATO: il tuo repository della config non risulta privato (${VIS:-visibilità sconosciuta}), e personale/ non viaggerebbe fra le tue macchine."
fi
```

È lo stesso spostamento che fa ogni aggiornamento (Passo 2b), con la stessa regola: con un suo
repository della config, solo se è privato. Ogni riga `SEPARATO:` è un comando spostato: diglielo
in una frase, come nel Passo 2b. Con `NON SEPARATO` diglielo come nel Passo 2b. Se non stampa
niente, non c'era niente da spostare: diglielo in una riga.

## Tornare indietro

Se chi ti parla scrive `/aggiorna indietro`, vuole annullare l'ultimo aggiornamento. Ogni
`/aggiorna` scrive una riga in `session-env/aggiornamenti` (versione prima, versione dopo,
data): tornare indietro toglie l'ultima riga, e un secondo `/aggiorna indietro` toglie la
precedente. I passi 1-4 qui sopra non c'entrano.

1. **Leggi l'ultimo aggiornamento.**

   ```bash
   cd ~/.claude
   tail -1 session-env/aggiornamenti 2>/dev/null || echo "nessun aggiornamento registrato"
   ```

   Se non c'è una riga, digli che non hai un aggiornamento da annullare e fermati.

2. **Mostra cosa torna indietro**, in parole semplici: i commit arrivati
   (`git log --oneline <prima>..<dopo>`) e le intestazioni `## ` di `NOVITA.md` che
   spariranno. Mostra anche i commit suoi fatti **dopo** l'aggiornamento
   (`git log --oneline <dopo>..HEAD`): li conservi. Chiedi il suo sì.

3. **Solo dopo il suo sì**, torna indietro portando con te i suoi commit successivi:

   ```bash
   cd ~/.claude && bash bin/aggiorna-applica.sh ~/.claude indietro
   ```

   I suoi commit successivi si rifanno sulla versione vecchia in una copia di prova, come il
   merge del Passo 3: `~/.claude` cambia solo con un risultato integro, con `reset --keep`.
   Leggi la prima parola dell'esito:

   - `TORNATO INDIETRO`: fatto, la config è integra e la riga dell'aggiornamento è tolta.
   - `RITORNO ANNULLATO`: `~/.claude` è com'era prima. La riga dice perché: modifiche non salvate,
     una copia di prova che aspetta, o commit suoi che non si applicano sulla versione vecchia.
     Spiegaglielo in parole semplici e **non forzare**. Le sue modifiche hanno la precedenza.
   - `RIPRISTINO NON RIUSCITO`: **fermati**, come nel Passo 3.

4. Digli di **chiudere e riaprire Claude Code**, come dopo ogni aggiornamento.

## Freni

- Si applica dopo un sì, mai in automatico. `/inizio` e l'avvio non applicano niente.
- Con `STORIA RISCRITTA` non si applica niente.
- Si applica solo l'ultimo tag firmato, mai `main`. Con `POSSIBILE COMPROMISSIONE` non si applica
  niente, neanche col suo sì: "possibile compromissione: non aggiornare, segnala a chi mantiene Arturo".
  Con `FIRMA NON VERIFICABILE` non si applica niente finché git e OpenSSH non sono aggiornati: non è
  un allarme, e non si dice "compromissione".
- Con modifiche non salvate l'applicazione non parte. Il merge gira in una copia di prova:
  `~/.claude` cambia solo con un risultato integro, e i conflitti si risolvono nella copia di prova.
- La procedura di applicazione si legge dal tag firmato in arrivo, dopo che il Passo 1 ne ha
  mostrato il diff.
- Per tornare indietro mai `reset --hard`: solo `aggiorna-applica.sh indietro`, e solo dopo il suo sì.
- Mai scartare modifiche sue per far passare l'aggiornamento.
- Se il fetch fallisce, è quasi sempre la rete o un repository non raggiungibile: dillo senza
  drammatizzare e non ritentare a oltranza.
