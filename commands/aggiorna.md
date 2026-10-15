---
description: Scarica e applica l'ultima versione di Arturo, poi racconta cosa è cambiato. Con `indietro`, riporta alla versione prima dell'ultimo aggiornamento. Con `personale`, sposta le modifiche ai comandi di Arturo in file suoi
argument-hint: "(nessuno) | indietro | personale"
---

# Aggiorna

Porti la copia di Arturo di chi ti parla all'ultima versione. È l'unico comando che applica
gli aggiornamenti: l'avvio e `/inizio` li controllano e basta.

Chi ti parla **potrebbe non essere una persona tecnica**: niente gergo di Git, nessun output
grezzo incollato senza spiegazione.

## Passo 1 — Guarda cosa c'è di nuovo

Gli aggiornamenti arrivano da `upstream` se ha un repository suo come `origin` (vedi `/setup`
FASE 7), altrimenti da `origin`.

```bash
cd "$HOME/.claude"
export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
NOTA=$(git rev-parse -q --verify "$SRC/main" || echo "")
git fetch --quiet --tags "$SRC" main 2>&1 || echo "fetch non riuscito (rete?)"
if [ -n "$NOTA" ] && ! git merge-base --is-ancestor "$NOTA" "$SRC/main"; then
  echo "STORIA RISCRITTA: la versione pubblicata non discende più da quella che conoscevi"
fi
echo "Versione installata: $(git describe --tags --always HEAD 2>/dev/null)"
echo "Versione disponibile: $(git describe --tags --always "$SRC/main" 2>/dev/null)"
BEHIND=$(git rev-list --count "HEAD..$SRC/main" 2>/dev/null || echo 0)
echo "Aggiornamenti da $SRC: ${BEHIND:-0}"
git log --oneline "HEAD..$SRC/main" 2>/dev/null | head -50
echo "--- file che cambiano"
git diff --stat "HEAD...$SRC/main" 2>/dev/null | tail -40
```

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
cd "$HOME/.claude"
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
echo "=== guardie e permessi, interi"
git diff "HEAD...$SRC/main" -- hooks settings.json 2>/dev/null
echo "=== codice che gira da solo: righe aggiunte e tolte, file per file"
git diff --name-only "HEAD...$SRC/main" -- bin tests tools skills 2>/dev/null | while IFS= read -r f; do
  case "$f" in
    bin/*|tests/*|tools/*|skills/*/scripts/*) echo "$f" ;;
    skills/*/*)
      m=${f#skills/}; m="skills/${m%%/*}"
      { git cat-file -e "$SRC/main:$m/.claude-plugin/plugin.json" || git cat-file -e "HEAD:$m/.claude-plugin/plugin.json"; } 2>/dev/null && echo "$f" ;;
  esac
done | while IFS= read -r f; do
  git diff --numstat "HEAD...$SRC/main" -- "$f" 2>/dev/null   # righe aggiunte, tolte, file
done
```

Poi leggi il diff di **ogni** file dell'elenco, uno per volta e intero:
`git diff "HEAD...$SRC/main" -- "FILE"`. Un font o un'immagine basta nominarli. Se un output
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
(per esempio il «session sync» di `/fine`).

```bash
cd "$HOME/.claude"
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
git status --short --untracked-files=no
echo "--- file che hai cambiato rispetto ad Arturo"
git diff --stat "$SRC/main...HEAD" 2>/dev/null | tail -20
echo "--- file cambiati sia da te sia dall'aggiornamento"
comm -12 <(git diff --name-only "$SRC/main...HEAD" 2>/dev/null | sort) <(git diff --name-only "HEAD...$SRC/main" 2>/dev/null | sort)
```

Se ci sono file cambiati da tutti e due, **mostraglieli e chiedi conferma prima di procedere**:
sono i punti dove può nascere un conflitto. Sono suoi, e un aggiornamento non deve mangiarseli.
I comandi di Arturo (`commands/<nome>.md`) non contano: li sistema da solo il Passo 3 (Passo 2b).

### Passo 2b — Le sue aggiunte ai comandi

Non deve fare niente. Se ha modificato un comando di Arturo (`commands/<nome>.md`), il Passo 3
sposta le sue modifiche in `~/.claude/personale/<nome>.md` prima di applicare l'aggiornamento. Il
comando torna quello di Arturo, le sue righe restano sue, e quando lancia `/<nome>` l'avvio del
prompt dice a Claude di leggerle. Così il comando non va in conflitto, né adesso né dopo.

Lo spostamento è un commit, e il Passo 3 stampa una riga `SEPARATO: /<nome> -> personale/<nome>.md`
per ogni comando. Diglielo in una frase: «le tue aggiunte a /inizio ora stanno in un file tuo, e
/inizio fa tutto come prima». Non chiedere conferma e non spiegare il meccanismo, se non lo chiede.
Se vuole, rileggete insieme il file personale: le parti sono copiate così come erano.

Se `git status` elenca dei file, sono modifiche sue non ancora salvate con un commit (le scrive
anche `/setup`, per esempio `PROJECTS_BASE` o la lingua in `settings.json`). Il Passo 3 non parte
finché ci sono: un aggiornamento sopra modifiche non salvate può lasciare un file mezzo suo e mezzo
di Arturo. Spiegaglielo e proponi di salvarle prima con un commit, col suo sì:
`git -C ~/.claude commit -am "chore: modifiche locali prima di /aggiorna"`. Poi rilancia il Passo 2:
adesso i file toccati da tutti e due compaiono nell'elenco qui sopra.

## Passo 3 — Applica

Solo dopo il suo sì. Se dice no, vai a «Se dice no» in fondo a questo passo. Ogni blocco gira in
una shell nuova: questo ricava da sé da dove arrivano gli aggiornamenti.

L'aggiornamento non si fa dentro `~/.claude`: lo fa `bin/aggiorna-applica.sh` in una copia di prova a
parte, controlla lì la config, e porta dentro solo un risultato integro. Così un conflitto non scrive
mai marcatori in `settings.json` o negli hook che Claude Code sta usando. La procedura si legge dalla
**versione in arrivo**, non da quella installata: una correzione alla procedura protegge già
l'aggiornamento che la porta. È codice che gira da solo, e il Passo 1 te ne ha mostrato il diff.

```bash
cd "$HOME/.claude"
SRC=$(git remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
MODO=$([ "$SRC" = upstream ] && echo merge || echo rebase)
# Con un repository suo, i suoi commit sono gia' pubblicati: il merge non li riscrive.
APPLICA=$(mktemp)
git show "$SRC/main:bin/aggiorna-applica.sh" > "$APPLICA" 2>/dev/null || cp bin/aggiorna-applica.sh "$APPLICA" 2>/dev/null
if [ -s "$APPLICA" ]; then
  bash "$APPLICA" "$HOME/.claude" "$MODO" "$SRC/main"
else
  echo "APPLICAZIONE NON PARTITA: non trovo la procedura di applicazione. Non ho toccato niente."
fi
rm -f "$APPLICA"
```

La prima parola dell'esito dice cosa è successo:

- `APPLICATO`: l'aggiornamento è dentro e la config è integra. La procedura lo ha registrato in
  `session-env/aggiornamenti` (per `/aggiorna indietro`) e in `session-env/ultimo-aggiornamento`.
  Vai al Passo 3b.
- `GIÀ AGGIORNATO`: niente da fare.
- `APPLICAZIONE NON PARTITA`: la sua copia non è cambiata. Se il motivo sono file modificati e non
  salvati, diglielo in parole semplici e spiega perché l'aggiornamento aspetta (Passo 2). Col suo sì
  salvali con un commit, poi rilancia il Passo 2 e il Passo 3. Se il motivo è una config già rotta
  (un merge o un pull rimasto a metà da prima), fermati: mostragli le righe `CONFIG ROTTA` e
  sistemale con lui prima di aggiornare. Non scartare mai le sue modifiche per far passare
  l'aggiornamento. Se il motivo è **una copia di prova che aspetta**, l'esito dice da quando e da
  cosa (il sync fra le sue macchine o un aggiornamento). Dentro può esserci il lavoro di chi stava
  risolvendo un conflitto. Proponi di concluderla con «Risolvere un conflitto» qui sotto. Solo se
  lui dice che non serve, col suo sì, scartala:

  ```bash
  cd "$HOME/.claude" && bash bin/aggiorna-applica.sh "$HOME/.claude" scarta
  ```

  Poi rilancia il Passo 3.
- `APPLICAZIONE ANNULLATA`: la sua copia è **esattamente com'era prima**. Se la riga dice
  `CONFLITTO`, vai a «Risolvere un conflitto» qui sotto.
- `RIPRISTINO NON RIUSCITO`: **fermati**, la config può avere le guardie spente. Digli che la copia è
  rimasta a metà, mostragli i file elencati e lancia `python3 ~/.claude/hooks/controlla-config.py`,
  che dice cosa non va e come tornare a prima. Non lavorare su altro finché non dice `CONFIG OK`.

### Se dice no

Rispetta il no e fermati, dopo aver registrato l'esito per la telemetria di Arturo (dice quali
aggiornamenti le persone non vogliono, mai il perché):

```bash
python3 "$HOME/.claude/bin/telemetria.py" registra aggiorna rifiutato >/dev/null 2>&1 || true
```

### Risolvere un conflitto

Con `CONFLITTO` la sua `~/.claude` non è stata toccata. I conflitti stanno nella **copia di prova**,
nella cartella che l'esito ha stampato, con i file elencati. Si risolvono lì, mai in `~/.claude`.

1. Se il file in conflitto è un comando di Arturo (`commands/<nome>.md`), proponi prima la strada
   che non si ripete: col suo sì scarta la copia di prova (il blocco `scarta` qui sopra: le sue
   modifiche restano in `~/.claude`), sposta le sue aggiunte col Passo 2b e rilancia il Passo 3. Altrimenti, o se preferisce così,
   per ogni file in conflitto della copia di prova, mostragli in parole semplici cosa c'era da lui e
   cosa arriva da Arturo, e chiedi cosa tenere. Di solito si tengono tutti e due: per esempio tutte le
   righe di una lista `deny`. Scrivi il file risolto nella copia di prova, senza marcatori.
2. Chiudi l'aggiornamento nella copia di prova. Con un merge: `git -C <copia> add <file>` per ogni
   file, poi `git -C <copia> commit --no-edit`. Con un rebase: `git -C <copia> add <file>`, poi
   `GIT_EDITOR=true git -C <copia> rebase --continue`, finché il rebase non finisce.
3. Solo dopo il suo sì, porta il risultato dentro:

```bash
cd "$HOME/.claude"
COPIA=$(cut -d' ' -f1 "$(git rev-parse --git-path arturo-aggiorna-copia)" 2>/dev/null)
APPLICA=$(mktemp)
cp "$COPIA/bin/aggiorna-applica.sh" "$APPLICA" 2>/dev/null || cp bin/aggiorna-applica.sh "$APPLICA" 2>/dev/null
if [ -s "$APPLICA" ]; then
  bash "$APPLICA" "$HOME/.claude" concludi
else
  echo "APPLICAZIONE NON PARTITA: non trovo la procedura di applicazione. Non ho toccato niente."
fi
rm -f "$APPLICA"
```

Gli esiti sono gli stessi del Passo 3. Se dice che nella copia di prova restano conflitti, torna al
punto 1. Mai `--force`, mai `reset --hard`, mai un `checkout` che butti via il suo lavoro.

## Passo 3b — Lo strato dell'organizzazione

Se ha installato lo strato della sua organizzazione (`/strato installa`), aggiornalo nello stesso
giro, così la porta resta una sola:

```bash
claude plugin marketplace list 2>/dev/null | grep -i -- "-strato" \
  && { claude plugin marketplace update && echo "Strato: marketplace aggiornato"; } \
  || echo "Nessuno strato installato"
```

Se il marketplace dello strato risponde, aggiorna anche il plugin con `claude plugin update
<plugin>@<marketplace>` (i nomi li leggi da `claude plugin list`). Se fallisce per accesso negato,
spiega che serve l'invito del referente o il collegamento dell'account (`gh auth login`), come in
`/strato installa`.

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

## Le sue aggiunte, senza aggiornare

Se chi ti parla scrive `/aggiorna personale` (oppure l'avvio ha mostrato una riga `DERIVA:` sui
comandi), non scarichi niente: sposti solo le sue modifiche ai comandi di Arturo.

```bash
python3 "$HOME/.claude/bin/arturo" personale separa
```

È lo stesso spostamento che fa ogni aggiornamento (Passo 2b). Ogni riga `SEPARATO:` è un comando
spostato: diglielo in una frase, come nel Passo 2b. Se non stampa niente, non c'era niente da
spostare: diglielo in una riga.

## Tornare indietro

Se chi ti parla scrive `/aggiorna indietro`, vuole annullare l'ultimo aggiornamento. Ogni
`/aggiorna` scrive una riga in `session-env/aggiornamenti` (versione prima, versione dopo,
data): tornare indietro toglie l'ultima riga, e un secondo `/aggiorna indietro` toglie la
precedente. I passi 1-4 qui sopra non c'entrano.

1. **Leggi l'ultimo aggiornamento.**

   ```bash
   cd "$HOME/.claude"
   tail -1 session-env/aggiornamenti 2>/dev/null || echo "nessun aggiornamento registrato"
   ```

   Se non c'è una riga, digli che non hai un aggiornamento da annullare e fermati.

2. **Mostra cosa torna indietro**, in parole semplici: i commit arrivati
   (`git log --oneline <prima>..<dopo>`) e le intestazioni `## ` di `NOVITA.md` che
   spariranno. Mostra anche i commit suoi fatti **dopo** l'aggiornamento
   (`git log --oneline <dopo>..HEAD`): li conservi. Chiedi il suo sì.

3. **Solo dopo il suo sì**, torna indietro portando con te i suoi commit successivi:

   ```bash
   cd "$HOME/.claude"
   read -r PRIMA DOPO _ < <(tail -1 session-env/aggiornamenti)
   ADESSO=$(git rev-parse HEAD)
   if git reset --keep "$PRIMA"; then
     if [ "$DOPO" != "$ADESSO" ] && ! git cherry-pick "$DOPO..$ADESSO"; then
       git cherry-pick --abort; git reset --keep "$ADESSO"
       echo "RITORNO ANNULLATO: i tuoi commit successivi non si applicano sulla versione vecchia"
     else
       sed -i.bak '$d' session-env/aggiornamenti && rm -f session-env/aggiornamenti.bak
       python3 bin/telemetria.py registra aggiorna indietro >/dev/null 2>&1 || true
       python3 hooks/controlla-config.py
     fi
   fi
   ```

   Se `reset --keep` si rifiuta, un file che lui ha cambiato e non salvato è toccato anche
   dall'aggiornamento: mostragli quale, spiega che le sue modifiche hanno la precedenza, e **non
   forzare**. Mai `reset --hard`.

4. Digli di **chiudere e riaprire Claude Code**, come dopo ogni aggiornamento.

## Freni

- Si applica dopo un sì, mai in automatico. `/inizio` e l'avvio non applicano niente.
- Con `STORIA RISCRITTA` non si applica niente.
- Con modifiche non salvate l'applicazione non parte. Il merge gira in una copia di prova:
  `~/.claude` cambia solo con un risultato integro, e i conflitti si risolvono nella copia di prova.
- La procedura di applicazione si legge dalla versione in arrivo, dopo che il Passo 1 ne ha
  mostrato il diff.
- Per tornare indietro mai `reset --hard`: solo `reset --keep`, e solo dopo il suo sì.
- Mai scartare modifiche sue per far passare l'aggiornamento.
- Se il fetch fallisce, è quasi sempre la rete o un repository non raggiungibile: dillo senza
  drammatizzare e non ritentare a oltranza.
