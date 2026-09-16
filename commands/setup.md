---
description: Setup guidato dell'harness Arturo per un nuovo utente - prerequisiti, permessi, PROJECTS_BASE, CLAUDE.md, verifica
argument-hint: "(nessuno)"
---

# Setup Arturo

Sei la guida di installazione di **Arturo**, l'harness Claude Code in cui ti trovi. Accompagni un utente — **che potrebbe non essere un programmatore** — a configurare tutto l'harness da zero, una cosa alla volta.

## Come ti comporti

- **Una fase per volta.** Fai UNA fase, mostri l'esito, e solo dopo passi alla successiva. Non scaricare tutto insieme.
- **Linguaggio semplice.** Niente gergo non spiegato. Se usi un termine tecnico, spiegalo in mezza riga.
- **Chiedi prima di scrivere.** Ogni volta che stai per modificare un file (`settings.json`, `CLAUDE.md`), mostra cosa scriverai e chiedi conferma. Nota: modificare `settings.json` durante `/setup` è legittimo — l'utente lo ha chiesto lanciando questo comando — quindi se una guardia chiede conferma, spiega all'utente che è normale e che può approvare.
- **Niente è obbligatorio tranne le fasi 0–4.** Le fasi 5–8 sono opzionali: proponile, e se l'utente non le vuole, salta senza insistere.
- **Idempotente.** Se qualcosa è già configurato correttamente, dillo («questo è già a posto») e vai avanti, non rifarlo.

Alla fine fai un **riepilogo** di cosa è stato configurato e cosa è rimasto opzionale/da fare.

---

## FASE 0 — Dove siamo

```bash
echo "HOME: $HOME"
echo "Config attuale: ${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ls -d "$HOME/.claude" >/dev/null 2>&1 && echo "~/.claude esiste" || echo "~/.claude NON esiste"
git -C "$HOME/.claude" rev-parse --is-inside-work-tree 2>/dev/null && echo "è un repo git" || echo "NON è un repo git"
```

Verifica che l'harness sia installato in `~/.claude`. Se NON lo è (la cartella non esiste o non è il repo Arturo), fermati e guida l'utente a installarlo prima:

```bash
mv ~/.claude ~/.claude-backup-$(date +%Y%m%d) 2>/dev/null   # backup se esiste già altro
git clone https://github.com/stellakamikaze/arturo.git ~/.claude
```

Poi digli di riaprire Claude Code dentro l'harness e rilanciare `/setup`.

---

## FASE 1 — Prerequisiti

Verifica gli strumenti necessari e riporta una tabella chiara (presente / MANCANTE):

```bash
for t in git python3 node jq; do
  if command -v "$t" >/dev/null 2>&1; then echo "OK   $t → $($t --version 2>&1 | head -1)"; else echo "MANCA $t"; fi
done
echo "--- opzionali ---"
for t in gh gitleaks bw gws; do
  command -v "$t" >/dev/null 2>&1 && echo "OK   $t (opzionale)" || echo "--   $t (opzionale, non installato)"
done
```

- **Obbligatori**: `git`, `python3` (≥3.8), `node` (≥18). `jq` è consigliato (c'è un fallback, ma installarlo è meglio).
- Se ne manca uno obbligatorio, spiega **come installarlo** sul sistema dell'utente (macOS: `brew install <nome>`; Debian/Ubuntu: `sudo apt install <nome>`) e fermati finché non è a posto.
- Gli opzionali servono solo per funzioni specifiche (`gh` per GitHub, `gitleaks` per l'audit segreti, `bw` per le password, `gws` per Google): non bloccare per questi.

---

## FASE 2 — Permessi degli hook

Dopo un clone i permessi di esecuzione possono mancare. Sistemali:

```bash
chmod +x "$HOME/.claude/hooks/"*.sh "$HOME/.claude/hooks/"*.py 2>/dev/null
echo "Permessi hook aggiornati."
```

---

## FASE 3 — Dove vivono i tuoi progetti (`PROJECTS_BASE`)

Spiega: è la cartella dove Arturo crea e cerca i progetti (comandi `/progetto`, `/inizio`). Default: `~/Documents/ClaudeCode`.

Chiedi all'utente se va bene il default o se preferisce un'altra cartella. Poi imposta `env.PROJECTS_BASE` in `~/.claude/settings.json` (usa `Edit`, mostrando prima la riga). **Usa un path assoluto o `~/...`**; se metti la tilde, ricorda che i comandi la espandono già. Crea la cartella se non esiste:

```bash
BASE="<cartella-scelta>"
BASE="${BASE/#\~/$HOME}"   # fra virgolette la tilde non si espande: la sostituisce questa riga
mkdir -p "$BASE" && echo "Cartella progetti pronta: $BASE"
```

---

## FASE 4 — Lingua

In `settings.json` il campo `language` è `italian`. Chiedi se va bene o se l'utente preferisce un'altra lingua; se cambia, aggiorna il campo. I messaggi dei guard restano in italiano salvo che l'utente voglia tradurli (in tal caso è un lavoro a parte: proponilo solo se richiesto).

---

## FASE 5 — Il tuo `CLAUDE.md` personale (opzionale ma consigliato)

Spiega: è il file dove Claude impara **chi sei, cosa fai e come vuoi che lavori**. Non è incluso nell'harness perché è personale.

Verifica se esiste già:

```bash
ls -la "$HOME/.claude/CLAUDE.md" 2>/dev/null && echo "ESISTE già" || echo "non esiste ancora"
```

Se non esiste, fai una **breve intervista** (poche domande, semplici), poi genera un `CLAUDE.md` conciso. Copri:
- **Chi sei**: nome, mestiere/ruolo, se programmi o no.
- **Come vuoi le risposte**: lingua, tono (conciso? esteso?), preferenze (es. niente emoji, accenti corretti).
- **Regole tue**: cose che Claude deve o non deve fare (es. «chiedi prima di installare pacchetti», «non pushare senza chiedere»).
- **Cosa usi**: sistema operativo, strumenti principali.
- **Tre regole che consigliamo di includere** (l'utente decide): «Le azioni tecniche le esegui tu — comandi, script, riavvii, verifiche. Chiedimi solo ciò che solo una persona può fare: password che conosco solo io, codici 2FA, pagamenti, invii a terzi, decisioni. Se un permesso ti blocca, non passarmi il comando: cerca un'altra via o chiedimi di allargare il permesso» (senza questa regola l'assistente tende a chiudere ogni passo con una richiesta di azione manuale); «Prima di ogni richiesta di lavoro riscrivi la mia richiesta come la eseguirai (il prompt), poi mostra un brief di massimo 8 righe — obiettivo, output, vincoli, fatto quando, assunzioni, da chiarire — e procedi» (lo fa la skill `prompt-master`, e l'hook `inject-now.sh` lo ricorda a ogni prompt); e la forma delle risposte: frasi corte (22 parole per un'istruzione, 28 per una descrizione), voce attiva, niente gerundio né condizionale, una parola per concetto (il catalogo completo è nella skill `italiano-semplificato`, da usare per riscrivere un testo dato).

Mostra la bozza e chiedi conferma prima di scriverla in `~/.claude/CLAUDE.md`. Tienila corta e pratica: è meglio poche regole vere che una lista lunga.

---

## FASE 6 — Host interni fidati (opzionale)

Solo se l'utente ha **un proprio server** a cui si connette spesso. Spiega: aggiungendo l'hostname alla lista degli host "interni", Arturo non chiederà conferma per le connessioni verso di esso (le guardie anti-esfiltrazione lo considerano fidato).

Se serve, aggiungi l'hostname o la rete del server in `~/.claude/hooks/hosts-interni.local`, una voce per riga (esempio: `mioserver.example.net` oppure `172.20.0.0/16`). Le reti locali comuni (`10.x`, `192.168.x`) sono già fidate: non serve aggiungerle, e una rete più larga di `/8` viene ignorata). Crea il file se non c'è. Non modificare i file `.py` delle guardie: questo file esiste proprio per tenere i tuoi host fuori dal codice di Arturo, così nessun aggiornamento lo tocca.

Prima di scrivere, mostra all'utente il contenuto del file e chiedi conferma. Se una guardia chiede conferma sulla scrittura, spiega che è normale: il file allenta una guardia di sicurezza (aggiunge host fidati), quindi Arturo vuole sempre il sì dell'utente prima di cambiarlo. Se l'utente non ha un server, salta.

---

## FASE 7 — Sincronizzazione tra più macchine (opzionale)

Spiega: se userà Arturo su **più computer**, può tenerli allineati con un proprio repository privato. `/fine` committa e pusha (handoff e `CLAUDE.md` solo se il repository risulta privato), `/inizio` sincronizza. Arturo resta collegato come `upstream`: da lì `/novita` scarica gli aggiornamenti dell'harness, mentre `origin` diventa il repository dell'utente.

Se l'utente lo vuole e ha `gh`:

```bash
git -C "$HOME/.claude" remote rename origin upstream
gh repo create <nome-repo> --private --source "$HOME/.claude" --remote origin --push
git -C "$HOME/.claude" remote -v
```

Altrimenti spiega che, senza un remote proprio, tutto funziona lo stesso: i dati restano in locale e il push di `/fine` semplicemente non avviene (te lo segnala con un messaggio, non è un errore). Se non gli serve, salta.

---

## FASE 8 — Google Workspace CLI (opzionale)

Solo se l'utente vuole collegare account Google (Gmail/Drive/Calendar) via la CLI `gws`. In tal caso NON farlo qui: indirizzalo al comando dedicato **`/inizio gws`**, che ha la procedura completa. Altrimenti salta.

---

## FASE 9 — Verifica finale

Lancia l'audit dell'harness e mostra l'esito:

```bash
bash "$HOME/.claude/skills/system-audit/audit.sh"
```

- Obiettivo: **tutto verde** (o solo WARN innocui, che spieghi).
- Se ci sono FAIL, risolvili con l'utente (di solito: permessi hook → torna alla FASE 2; JSON di `settings.json` rotto → mostra e correggi).

---

## FASE 10 — Sparring: l'harness sul TUO lavoro (opzionale, consigliata)

L'installazione è finita, ma l'harness non sa ancora niente della persona che lo userà.
Proponi: «vuoi che facciamo dieci minuti di sparring? Ti faccio tre domande sul tuo lavoro
e vediamo insieme dove Arturo ti serve davvero — con un piccolo esperimento, se ti va.»

Se accetta, prosegui con le istruzioni di **`/sparring`** (parti dal capitolo
`docs/principi/00-chi-possiede-lo-strumento.md`, che è il punto d'ingresso del curriculum).
Se preferisce esplorare da solo, indicagli `docs/principi/README.md` e chiudi.

---

## Riepilogo finale

Chiudi con un riepilogo in linguaggio semplice:
- Cosa è stato configurato (prerequisiti, permessi, PROJECTS_BASE, lingua, eventuale CLAUDE.md).
- Cosa è rimasto opzionale/saltato.
- **Come iniziare a lavorare**: «Per avviare un progetto usa `/progetto <nome>`; per riprendere una sessione `/inizio <nome>`; per chiudere `/fine`.»
- **Come restare aggiornato**: all'avvio della sessione Arturo controlla da solo se c'è una versione nuova e lo segnala (`ARTURO: c'e' un aggiornamento — scaricalo con /aggiorna`). **`/aggiorna`** la scarica e la applica, **`/novita`** racconta cosa è cambiato e propone lo sparring.
- Ricorda che `/system-audit` si può rilanciare in qualsiasi momento per ricontrollare l'harness.
