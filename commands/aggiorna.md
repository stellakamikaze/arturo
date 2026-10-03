---
description: Scarica e applica l'ultima versione di Arturo, poi racconta cosa è cambiato. Con `indietro`, riporta alla versione prima dell'ultimo aggiornamento
argument-hint: "(nessuno) | indietro"
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
CLI `arturo` (`bin`), gli script delle skill (`skills/*/scripts`) e ogni file dei mod di Claude
Code (una cartella di `skills/` con `.claude-plugin/plugin.json`, come il pannello `/dafare`).

```bash
cd "$HOME/.claude"
echo "=== guardie e permessi, interi"
git diff "HEAD...$SRC/main" -- hooks settings.json 2>/dev/null
echo "=== codice che gira da solo: righe aggiunte e tolte, file per file"
git diff --name-only "HEAD...$SRC/main" -- bin skills 2>/dev/null | while IFS= read -r f; do
  case "$f" in
    bin/*|skills/*/scripts/*) echo "$f" ;;
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
git status --short
echo "--- file che hai cambiato rispetto ad Arturo"
git diff --stat "$SRC/main...HEAD" 2>/dev/null | tail -20
echo "--- file cambiati sia da te sia dall'aggiornamento"
comm -12 <(git diff --name-only "$SRC/main...HEAD" 2>/dev/null | sort) <(git diff --name-only "HEAD...$SRC/main" 2>/dev/null | sort)
```

Se ci sono file cambiati da tutti e due, **mostraglieli e chiedi conferma prima di procedere**:
sono i punti dove può nascere un conflitto. Sono suoi, e un aggiornamento non deve mangiarseli.

## Passo 3 — Applica

Solo dopo il suo sì.

```bash
cd "$HOME/.claude"
mkdir -p session-env
PRIMA=$(git rev-parse HEAD)
if [ "$SRC" = upstream ]; then
  # Con un repository suo, i suoi commit sono gia' pubblicati: un merge non li riscrive.
  git merge --no-edit upstream/main || { git merge --abort; echo "APPLICAZIONE ANNULLATA: conflitto"; }
else
  git rebase --autostash origin/main || { git rebase --abort; echo "APPLICAZIONE ANNULLATA: conflitto"; }
fi
if ! python3 hooks/controlla-config.py; then
  git reset --keep "$PRIMA" && echo "APPLICAZIONE ANNULLATA: la config risultava rotta, la copia è tornata a prima"
fi
DOPO=$(git rev-parse HEAD)
if [ "$DOPO" != "$PRIMA" ]; then
  printf '%s %s %s\n' "$PRIMA" "$DOPO" "$(date +%Y-%m-%d_%H-%M)" >> session-env/aggiornamenti
  printf '%s\n' "$PRIMA" > session-env/ultimo-aggiornamento
fi
```

Se compare `APPLICAZIONE ANNULLATA`, la sua copia è **esattamente com'era prima**: nessun file
è rimasto a metà. Mostragli quali file sono cambiati sia da lui sia dall'aggiornamento
(Passo 2) e risolvi con lui, uno per volta, spiegando cosa c'era prima e cosa arriva. Poi
rilancia il Passo 3. Mai `--force`, mai `reset --hard`, mai un `checkout` che butti via il
suo lavoro.

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
- Un'applicazione che fallisce si annulla da sola: la copia non resta mai a metà.
- Per tornare indietro mai `reset --hard`: solo `reset --keep`, e solo dopo il suo sì.
- Mai scartare modifiche sue per far passare l'aggiornamento.
- Se il fetch fallisce, è quasi sempre la rete o un repository non raggiungibile: dillo senza
  drammatizzare e non ritentare a oltranza.
