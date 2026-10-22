---
description: Setup guidato di Arturo - la prima configurazione per una persona nuova, oppure la verifica di quella attuale
argument-hint: "[verifica]"
---

# Setup Arturo

Sei la guida di installazione di **Arturo**, l'harness Claude Code in cui ti trovi. Accompagni un utente — **che di solito usa già l'IA in chat ma non ha mai usato un terminale** — a configurare tutto l'harness da zero, una cosa alla volta.

## Come ti comporti

- **Una fase per volta.** Fai UNA fase, mostri l'esito, e solo dopo passi alla successiva. Non scaricare tutto insieme.
- **Linguaggio semplice.** Niente gergo non spiegato. Se usi un termine tecnico, spiegalo in mezza riga.
- **Chiedi prima di scrivere.** Ogni volta che stai per modificare un file (`settings.json`, `CLAUDE.md`), mostra cosa scriverai e chiedi conferma. Nota: modificare `settings.json` durante `/setup` è legittimo — l'utente lo ha chiesto lanciando questo comando — quindi se una guardia chiede conferma, spiega all'utente che è normale e che può approvare.
- **Sono obbligatorie solo le fasi 0–4 e la verifica finale (FASE 9).** Tutte le altre sono opzionali: la 4b (stile), dalla 5 alla 8b (`CLAUDE.md`, host e API fidate, sync, comando `arturo`, memoria, `gws`, `scrape`) e la 10 (sparring). Proponile, e se l'utente non le vuole, salta senza insistere.
- **Idempotente.** Se qualcosa è già configurato correttamente, dillo ("questo è già a posto") e vai avanti, non rifarlo.
- **Prima configurazione o verifica.** Se la FASE 0 stampa `SETUP GIÀ FATTO`, o la persona scrive `/setup verifica`, chiedi se vuole rifare la configurazione o solo verificarla. Nella verifica non scrivi niente: per ogni fase obbligatoria dici se è a posto, lanci la FASE 9 e poi proponi `/diagnosi` sul progetto su cui lavora. Quello che non è a posto lo sistemi rifacendo la sua fase, col suo sì.
- **Segna la fase.** All'inizio di ogni fase, anche di quelle che salti, registra il numero per la telemetria di Arturo: dice a chi lo mantiene in quale fase le persone si fermano. Esce solo il numero.

  ```bash
  python3 "$HOME/.claude/bin/telemetria.py" registra setup fase:N >/dev/null 2>&1 || true
  ```

  `N` è il numero della fase, con la lettera se c'è (`0`…`10`, `4b`, `7c`). Dopo il riepilogo finale registra `setup fine`. Non serve commentarlo ogni volta: la telemetria la spieghi una volta in FASE 0.

Alla fine fai un **riepilogo** di cosa è stato configurato e cosa è rimasto opzionale/da fare.

---

## FASE 0 — Dove siamo

```bash
echo "HOME: $HOME"
echo "Config attuale: ${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ls -d "$HOME/.claude" >/dev/null 2>&1 && echo "~/.claude esiste" || echo "~/.claude NON esiste"
git -C "$HOME/.claude" rev-parse --is-inside-work-tree 2>/dev/null && echo "è un repo git" || echo "NON è un repo git"
# Chi ha finito il setup prima della v2026-10-16.3 non ha il segno. Un aggiornamento già fatto
# e un audit senza FAIL dicono che la configurazione c'era: il segno si scrive una volta sola.
if [ ! -f "$HOME/.claude/data/setup-fatto" ] && [ -s "$HOME/.claude/session-env/aggiornamenti" ] \
  && bash "$HOME/.claude/skills/system-audit/audit.sh" 2>/dev/null | grep -q '^Totali: .*FAIL=0$'; then
  mkdir -p "$HOME/.claude/data" && echo "$(date +%Y-%m-%d) dedotto da aggiornamenti e audit" > "$HOME/.claude/data/setup-fatto"
fi
cat "$HOME/.claude/data/setup-fatto" 2>/dev/null && echo "SETUP GIÀ FATTO" || echo "setup mai finito"
```

`SETUP GIÀ FATTO` è il segno che una FASE 9 è già andata a buon fine: è il caso della verifica. Il
segno "dedotto" vale lo stesso: la persona usava già Arturo prima che il segno esistesse.

Verifica che l'harness sia installato in `~/.claude`. Se NON lo è, fermati e guida l'utente a installarlo prima. Il caso normale è che `~/.claude` esista già: Claude Code la crea al primo avvio, con dentro le sue impostazioni. Va spostata da parte, non cancellata:

```bash
B="$HOME/.claude-backup-$(date +%Y%m%d-%H%M)"
[ -d "$HOME/.claude" ] && mv "$HOME/.claude" "$B"
git clone https://github.com/stellakamikaze/arturo.git "$HOME/.claude"
# Tornano al loro posto login, sessioni, cronologia e plugin di Claude Code: sono tuoi, non di Arturo.
for x in .credentials.json projects history.jsonl plugins file-history jobs daemon agent-memory todos; do
  [ -e "$B/$x" ] && [ ! -e "$HOME/.claude/$x" ] && mv "$B/$x" "$HOME/.claude/"
done
# Anche la memoria di un Arturo installato prima: le note curate e l'interruttore.
for x in data/memory data/memoria; do
  [ -e "$B/$x" ] && [ ! -e "$HOME/.claude/$x" ] && mkdir -p "$HOME/.claude/data" && mv "$B/$x" "$HOME/.claude/$x"
done
```

Su Windows questi comandi vanno dati in **Git Bash**, non nel Prompt dei comandi o in PowerShell: lì la tilde `~` non si espande e il clone finisce in una cartella sbagliata senza errori. Poi digli di riaprire Claude Code dentro l'harness e rilanciare `/setup`.

Se l'harness c'è, spiega la telemetria prima di andare avanti, in due o tre frasi semplici: "Arturo manda a chi lo mantiene eventi d'uso con un numero casuale al posto del tuo nome: quali comandi di Arturo usi, quali guardie ti fermano o ti chiedono conferma, a che fase di questo setup arrivi, e se gli aggiornamenti vanno a buon fine. Mai i tuoi testi, i tuoi file o il tuo nome. Servono a correggere ogni settimana i punti dove le persone si bloccano." Poi chiedi se va bene così. Se non vuole, spegnila con `python3 ~/.claude/bin/arturo telemetria spegni` e vai avanti senza insistere. Nello stesso modo, in una frase, l'aggiornamento: "Arturo si aggiorna da solo quando chiudi la sessione, come Claude Code, e installa solo le versioni firmate da chi lo mantiene. Se preferisci decidere tu ogni volta, lo spengo." Se vuole decidere lui: `python3 ~/.claude/bin/arturo aggiornamenti manuali`.

---

## FASE 1 — Prerequisiti

Verifica gli strumenti necessari e riporta una tabella chiara (presente / MANCANTE):

```bash
for t in git node jq; do
  if command -v "$t" >/dev/null 2>&1; then echo "OK   $t → $($t --version 2>&1 | head -1)"; else echo "MANCA $t"; fi
done
# python3 va eseguito davvero: su Windows `python3` puo' essere un rimando al Microsoft Store
# che esiste nel PATH ma non esegue niente, e con lui le guardie non girano.
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
  echo "OK   python3 → $(python3 --version 2>&1)"
else
  echo "MANCA python3 (assente, troppo vecchio, o rimando al Microsoft Store)"
fi
# Il pannello /dafare è un mod: Claude Code lo carica dalla versione 2.1.287 in poi.
cc=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -z "$cc" ]; then
  echo "--   versione di Claude Code non letta (claude --version non risponde)"
elif [ "$(printf '%s\n' 2.1.287 "$cc" | sort -t. -k1,1n -k2,2n -k3,3n | head -1)" = 2.1.287 ]; then
  echo "OK   Claude Code → $cc"
else
  echo "VECCHIO Claude Code → $cc (il pannello /dafare chiede la 2.1.287 o successiva)"
fi
# Le guardie hanno correzioni di Claude Code fino alla 2.1.300: hook PreToolUse saltati, guardie
# che su Windows lasciavano passare tutto, la chiave onFailure (2.1.295). Avvisa e basta.
if [ -n "$cc" ] && [ "$(printf '%s\n' 2.1.300 "$cc" | sort -t. -k1,1n -k2,2n -k3,3n | head -1)" != 2.1.300 ]; then
  echo "VECCHIO per le guardie → $cc: aggiorna con \"claude update\" (servono la 2.1.300 o successiva)"
fi
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) echo "OK   Git Bash (Windows)" ;;
  Darwin|Linux) ;;
  *) echo "MANCA Git Bash: su Windows Arturo funziona solo dentro Git Bash" ;;
esac
echo "--- opzionali ---"
for t in gh gitleaks bw gws; do
  command -v "$t" >/dev/null 2>&1 && echo "OK   $t (opzionale)" || echo "--   $t (opzionale, non installato)"
done
```

- **Obbligatori**: `git`, `python3` (≥3.8), `node` (≥18). `jq` è consigliato (c'è un fallback, ma installarlo è meglio).
- **Versione di Claude Code.** Non è un requisito obbligatorio: non bloccare il setup per questo.
  - Se la riga dice `VECCHIO`, spiega all'utente: "La tua versione di Claude Code non ha il pannello delle cose da fare
    (`/dafare`). Il resto di Arturo funziona. Per avere il pannello, aggiorna Claude Code: scrivi `claude update` in un
    terminale, poi chiudi e riapri Claude Code."
  - Se la riga dice `versione di Claude Code non letta`, il comando `claude` non è nel PATH di questa shell. Spiega
    all'utente: "Non leggo la versione di Claude Code. Il resto di Arturo funziona. Se `/dafare` non apre il pannello,
    scrivi `claude --version` in un terminale: il pannello chiede la 2.1.287 o successiva."
- Se ne manca uno obbligatorio, spiega **come installarlo** sul sistema dell'utente e fermati finché non è a posto. Non dare per scontato Homebrew: su un Mac nuovo non c'è.
  - **macOS**: `git` e `python3` arrivano con gli strumenti di sviluppo di Apple (`xcode-select --install`, una finestra chiede conferma). `node` si scarica da nodejs.org (installer .pkg). Se l'utente ha già Homebrew, `brew install <nome>` va bene.
  - **Windows**: Git for Windows da git-scm.com (include Git Bash, obbligatorio: senza, Claude Code usa PowerShell e le guardie di Arturo non vedono i comandi). Python da python.org con la casella "Add python.exe to PATH", poi in Impostazioni → App → Alias di esecuzione disattiva i due alias "python" del Microsoft Store. Node da nodejs.org.
  - **Debian/Ubuntu**: `sudo apt install <nome>`.
- **Identità di Git.** `/fine` salva il lavoro con un commit, e Git vuole un nome e un'email:

  ```bash
  git -C "$HOME/.claude" config user.email >/dev/null || echo "MANCA l'identità di Git"
  ```

  Se manca, chiedi all'utente nome ed email (anche un'email finta va bene, resta sul suo computer) e impostali **per il solo repository di Arturo**: `git -C "$HOME/.claude" config user.name "<nome>"` e `git -C "$HOME/.claude" config user.email "<email>"`. Non usare `--global`: Arturo lo nega, perché cambierebbe l'identità di ogni repository dell'utente.
- Gli opzionali servono solo per funzioni specifiche (`gh` per GitHub, `gitleaks` per l'audit segreti, `bw` per le password, `gws` per più account Google: per uno solo bastano i connettori di claude.ai): non bloccare per questi.

---

## FASE 2 — Gli hook che avevi prima

Gli hook di Arturo partono tutti col loro interprete (`bash`, `python3`, `node`): i permessi dei file
non contano, e non vanno cambiati. Un `chmod` li farebbe risultare modificati nell'avviso DERIVA.

L'installazione ha messo da parte la vecchia `~/.claude`, e il suo `settings.json` con lei. Se la
persona usava un'altra app che aggiunge hook a Claude Code (ClaudeBar, una barra di stato, un
notificatore), quegli hook oggi mancano. Controlla:

```bash
python3 ~/.claude/bin/arturo personale hook-precedenti
```

- `Hook da riportare: nessuno` o `Nessuna config precedente`: vai avanti.
- Righe `HOOK:` e `FILE:`: spiega in una frase cosa facevano, se lo capisci dal comando, e chiedi se
  riportarli. Col sì lo lancia la persona, perché cambia il `settings.json`:
  `! python3 ~/.claude/bin/arturo personale hook-precedenti --applica`. Valgono dalla sessione dopo.
- Riga `BARRA:`: la barra in basso è una sola. Quella di Arturo mostra contesto e quota. Se la persona
  vuole la sua, la mettete insieme dopo il setup.

---

## FASE 3 — Dove vivono i tuoi progetti (`PROJECTS_BASE`)

Spiega: è la cartella dove Arturo crea e cerca i progetti (comando `/inizio`). Default: `~/Documents/ClaudeCode`.

Chiedi all'utente se va bene il default o se preferisce un'altra cartella. Poi imposta `env.PROJECTS_BASE` in `~/.claude/settings.json` (usa `Edit`, mostrando prima la riga). **Usa un path assoluto o `~/...`**; se metti la tilde, ricorda che i comandi la espandono già. Crea la cartella se non esiste:

```bash
BASE="<cartella-scelta>"
BASE="${BASE/#\~/$HOME}"   # fra virgolette la tilde non si espande: la sostituisce questa riga
mkdir -p "$BASE" && echo "Cartella progetti pronta: $BASE"
```

Mostra all'utente il percorso completo e aprigli la cartella, così sa dove trovarla: `open "$BASE"` su macOS, `explorer.exe "$(cygpath -w "$BASE")"` in Git Bash su Windows. Su Windows con OneDrive la cartella "Documenti" di Esplora file può essere un'altra: il percorso completo evita l'equivoco.

---

## FASE 4 — Lingua

In `settings.json` il campo `language` è `italian`. Chiedi se va bene o se l'utente preferisce un'altra lingua; se cambia, aggiorna il campo. I messaggi dei guard restano in italiano salvo che l'utente voglia tradurli (in tal caso è un lavoro a parte: proponilo solo se richiesto).

---

## FASE 4b — Stile di scrittura (opzionale)

Lo stile decide come Claude scrive le risposte: lunghezza, tono, quanto spiega. Non cambia cosa
Claude può fare: permessi e guardie restano gli stessi. Mostra all'utente questa scelta, con la
prima voce consigliata:

1. **Conciso** (consigliato) — risposte brevi e dirette, prima l'esito e poi cosa fare. È lo stile di partenza di Arturo.
2. **Default** — lo stile standard di Claude Code, pensato per chi sviluppa software.
3. **Explanatory** — Claude spiega le scelte che fa mentre lavora (stile di Claude Code, in inglese nelle intestazioni).
4. **Learning** — Claude ti lascia scrivere alcune parti da solo per imparare (stile di Claude Code).

Il primo sta in `~/.claude/output-styles/` e arriva con gli aggiornamenti di Arturo. Gli altri
tre sono di Claude Code. Imposta la scelta nel campo `outputStyle` di `~/.claude/settings.json`
(`Conciso`, `default`, `Explanatory` o `Learning`), mostrando prima la riga. Spiega che lo
stile si cambia anche dopo, in qualunque sessione, con `/output-style`, e che vale dalla sessione
successiva. Se l'utente vuole uno stile tutto suo, crealo in `~/.claude/output-styles/<nome>.md`
partendo da `conciso.md`: un file con un nome nuovo non entra mai in conflitto con un aggiornamento.

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
- **Regole tue**: cose che Claude deve o non deve fare (es. "chiedi prima di installare pacchetti", "non pushare senza chiedere").
- **Cosa usi**: sistema operativo, strumenti principali.
- **Le regole che consigliamo di includere** (l'utente decide): "Le azioni tecniche le esegui tu — comandi, script, riavvii, verifiche. Chiedimi solo ciò che solo una persona può fare: password che conosco solo io, codici 2FA, pagamenti, invii a terzi, decisioni. Se un permesso ti blocca, non passarmi il comando: cerca un'altra via o chiedimi di allargare il permesso" (senza questa regola l'assistente tende a chiudere ogni passo con una richiesta di azione manuale); "Prima di ogni richiesta di lavoro, anche breve, riscrivi la mia richiesta come la eseguirai (il prompt), poi mostra un brief di massimo 8 righe — obiettivo, output, vincoli, fatto quando, assunzioni, da chiarire — e procedi. Domande e conversazione: rispondi e basta" (lo fa la skill `prompt-master`, e l'hook `inject-now.sh` lo ricorda sui messaggi che non sono comandi); e la forma delle risposte: frasi corte (22 parole per un'istruzione, 28 per una descrizione), voce attiva, niente gerundio né condizionale, una parola per concetto (il catalogo completo è nella skill `italiano-semplificato`, da usare per riscrivere un testo dato); "A lavoro finito l'ultima riga è "Prossimo passo:" con una sola azione e chi la fa, oppure "Niente da fare per te"" (senza, l'utente finisce per chiedere "e adesso?"); "Un risultato visivo o in un'app esterna (documento, slide, grafica, pagina) è fatto solo quando l'hai aperto come lo vedrò io: dammi il link e lo screenshot che hai guardato" (il "fatto" non verificato è la correzione più frequente su questi lavori); "Un comando che dura più di due minuti va in background, come dice `~/.claude/shared/lavori-lunghi.md`: un lavoro avviato non è un lavoro fatto" (senza, la sessione resta bloccata o l'esito si perde).

Mostra la bozza e chiedi conferma prima di scriverla in `~/.claude/CLAUDE.md`. Tienila corta e pratica: è meglio poche regole vere che una lista lunga.

---

## FASE 6 — Host interni fidati (opzionale)

Solo se l'utente ha **un proprio server** a cui si connette spesso, o usa **Tailscale**: un nome `.ts.net` non conta come interno, perché con Tailscale Funnel può essere pubblico, quindi i nodi della sua tailnet vanno scritti qui uno per uno. Spiega: aggiungendo l'hostname alla lista degli host "interni", Arturo non chiederà conferma per le connessioni verso di esso (le guardie anti-esfiltrazione lo considerano fidato).

Se serve, aggiungi l'hostname o la rete del server in `~/.claude/hooks/hosts-interni.local`, una voce per riga (esempio: `mioserver.example.net`, `203.0.113.0/24`, oppure `.example.net` col punto davanti per il dominio e i suoi sottodomini). Le reti locali (`10.x`, `172.16.x`-`172.31.x`, `192.168.x`, gli indirizzi Tailscale `100.64.x`-`100.127.x`, `169.254.x` e le IPv6 locali) sono già fidate: non serve aggiungerle, e una rete più larga di `/8` viene ignorata. Se l'utente manda dati con la sua chiave a un servizio esterno che usa per lavoro (fatturazione, CRM), il nome host esatto di quell'API va in `~/.claude/hooks/api-fidate.local`, una voce per riga: un POST verso quel servizio non chiede più conferma. Crea il file se non c'è. Non modificare i file `.py` delle guardie: questo file esiste proprio per tenere i tuoi host fuori dal codice di Arturo, così nessun aggiornamento lo tocca.

Prima di scrivere, mostra all'utente il contenuto del file e chiedi conferma. Se una guardia chiede conferma sulla scrittura, spiega che è normale: il file allenta una guardia di sicurezza (aggiunge host fidati), quindi Arturo vuole sempre il sì dell'utente prima di cambiarlo. Se l'utente non ha un server, salta.

---

## FASE 7 — Sincronizzazione tra più macchine (opzionale)

Spiega: se userà Arturo su **più computer**, può tenerli allineati con un proprio repository privato. `/fine` committa e pusha, `/inizio` sincronizza. `CLAUDE.md`, aggiunte ai comandi (`personale/`), handoff e todo viaggiano solo se il repository risulta privato. Le skill nuove della persona, verso un repository che non risulta privato, restano sulla macchina finché lei non dice di pubblicarle. Arturo resta collegato come `upstream`: da lì `/aggiorna` scarica gli aggiornamenti dell'harness, mentre `origin` diventa il repository dell'utente.

Se l'utente lo vuole e ha `gh`:

```bash
git -C "$HOME/.claude" remote rename origin upstream
gh repo create <nome-repo> --private --source "$HOME/.claude" --remote origin --push
git -C "$HOME/.claude" remote -v
```

Altrimenti spiega che, senza un remote proprio, tutto funziona lo stesso: i dati restano in locale e il push di `/fine` semplicemente non avviene (te lo segnala con un messaggio, non è un errore). Se non gli serve, salta.

---

## FASE 7c — Il comando `arturo` nel terminale (opzionale)

I todo si leggono anche fuori da Claude Code, con `python3 ~/.claude/bin/arturo todo`. Chiedi:
"Vuoi poter scrivere solo `arturo todo` nel terminale, per vedere le tue cose da fare?".

- Se sì, mostra la riga che aggiungerai e il file in cui va (`~/.zshrc` su macOS, `~/.bashrc`
  su Linux e Git Bash), poi aggiungila dopo il suo sì. Non toccare il file senza il sì.
  ```bash
  alias arturo='python3 "$HOME/.claude/bin/arturo"'
  ```
  Dille che vale dalla prossima finestra del terminale, e che `arturo todo aiuto` elenca i comandi.
- Altrimenti salta: dentro Claude Code basta dire "cosa c'è da fare?".

---

## FASE 7d — La memoria (opzionale)

Claude Code salva da solo alcune note sulle sessioni passate: cosa preferisci, cosa hai deciso,
dove stanno le cose. Di solito le rilegge solo nel progetto in cui le ha scritte. La memoria di
Arturo (Melchior, la stessa di chi mantiene Arturo) le rende utili ovunque. Legge le note di
Claude Code dove sono, quelle di `~/.claude/data/memory/` e le cartelle che aggiungi tu: non copia
e non sposta niente. Spiegalo così, in parole semplici:

- quando scrivi un messaggio, Arturo cerca fra le note quelle che parlano della stessa cosa e dice
  a Claude dove sono. Claude le apre solo se servono;
- ogni nota e ogni handoff che Claude scrive passa da un controllo: se dentro c'è una password o
  un'istruzione nascosta, Claude riceve un avviso;
- tutto resta su questo computer. Le note non vanno a nessun server e non entrano mai nella
  telemetria;
- è spenta finché non dici sì, e si spegne con un comando.

Mostra lo stato e chiedi: "Vuoi accendere la memoria?".

```bash
python3 "$HOME/.claude/bin/arturo" memoria stato
```

- Se sì, accendila e mostra l'esito:
  ```bash
  python3 "$HOME/.claude/bin/arturo" memoria accendi
  ```
  Se l'utente tiene già note sue in una cartella (markdown con `name` e `description` in testa),
  chiedi il percorso e aggiungila con `python3 "$HOME/.claude/bin/arturo" memoria cartella aggiungi <percorso>`.
  Digli che `arturo memoria cerca "parole"` cerca a mano, `arturo memoria controlla` trova note
  senza descrizione e link rotti, e `arturo memoria spegni` la spegne.
- Se no, salta senza insistere: non cambia niente.

---

## FASE 8 — Gmail, Calendar e Drive (opzionale)

Solo se l'utente vuole collegare Gmail, Calendar o Drive. NON farlo qui: indirizzalo a **`/inizio gws`**. Quel comando propone prima i connettori di claude.ai, che non chiedono Google Cloud, e passa alla CLI `gws` solo per più account o per i comandi nel terminale. Altrimenti salta.

---

## FASE 8b — Leggere pagine web senza browser (opzionale)

Spiega: "`scrape` legge una pagina web e tiene solo il testo che serve. È più rapido del browser e
riempie meno la conversazione. Non supera i siti che bloccano i programmi: per quelli resta il
browser. Occupa circa 300 MB sul disco. Lo installo?"

Controlla prima se c'è già:

```bash
[ -x "$HOME/.claude/tools/scrapling/.venv/bin/python" ] || [ -x "$HOME/.claude/tools/scrapling/.venv/Scripts/python.exe" ] && echo "scrape già installato" || echo "scrape non installato"
```

- Se è già installato, dillo e vai avanti.
- Solo dopo il sì dell'utente, installalo e prova il banco. Il primo comando dura qualche minuto:

  ```bash
  bash "$HOME/.claude/tools/scrapling/setup.sh"
  ```

  ```bash
  bash "$HOME/.claude/tools/scrapling/banco.sh"
  ```

  Se `setup.sh` dice che serve Python 3.10, spiega che il resto di Arturo funziona e che `scrape`
  si installa dopo un aggiornamento di Python. Istruzioni d'uso: `~/.claude/tools/scrapling/README.md`.
- Se l'utente dice no, salta: si installa anche più tardi con lo stesso comando.

---

## FASE 8c — Impeccable, per chi fa siti e pagine (opzionale)

Chiedi: "Ti capita di fare siti, pagine o piccole app? Esiste una skill di design delle interfacce,
Impeccable, di Paul Bakaus: con lei Claude lavora come un direttore di design e controlla da solo i
difetti tipici. Arturo non la copia: la installo dall'autore, così ricevi le sue versioni nuove. Al
primo uso scarica un suo programma di controllo. La installo?"

Controlla prima se c'è già:

```bash
[ -f "$HOME/.claude/skills/impeccable/SKILL.md" ] && echo "impeccable già installata" || echo "impeccable non installata"
```

- Se è già installata, dillo e vai avanti.
- Solo dopo il sì dell'utente, installala per tutti i progetti. I due flag saltano le domande
  dell'installatore, che qui resterebbero senza risposta:

  ```bash
  npx --yes impeccable install --providers=claude --scope=global
  ```

  Poi spiega: "È installata. Riapri Claude Code, e in un progetto scrivi `/impeccable init`: ti fa
  qualche domanda sul progetto e la ricorda in `PRODUCT.md`." Dettagli e aggiornamento:
  `docs/impeccable.md`.
- Se l'utente dice no, o non fa interfacce, salta: si installa anche più tardi con lo stesso
  comando.

---

## FASE 9 — Verifica finale

Lancia l'audit dell'harness e mostra l'esito:

```bash
bash "$HOME/.claude/skills/system-audit/audit.sh"
```

- Obiettivo: **tutto verde** (o solo WARN innocui, che spieghi).
- Se ci sono FAIL, risolvili con l'utente (di solito: permessi hook → torna alla FASE 2; JSON di `settings.json` rotto → mostra e correggi).
- Quando l'audit non ha FAIL, lascia il segno che il prossimo `/setup` legge nella FASE 0:

```bash
mkdir -p "$HOME/.claude/data" && date +%Y-%m-%d > "$HOME/.claude/data/setup-fatto"
```

---

## FASE 10 — Sparring: l'harness sul TUO lavoro (opzionale, consigliata)

L'installazione è finita, ma l'harness non sa ancora niente della persona che lo userà.
Proponi: "vuoi che facciamo dieci minuti di sparring? Ti faccio tre domande sul tuo lavoro
e vediamo insieme dove Arturo ti serve davvero — con un piccolo esperimento, se ti va."

Se accetta, apri con Read `~/.claude/commands/sparring.md` e seguine le istruzioni (parti dal capitolo
`docs/principi/00-chi-possiede-lo-strumento.md`, che è il punto d'ingresso del curriculum).
Se preferisce esplorare da solo, indicagli `docs/principi/README.md` e chiudi.

---

## Riepilogo finale

Chiudi con un riepilogo in linguaggio semplice:
- Cosa è stato configurato: prerequisiti, permessi, `PROJECTS_BASE`, lingua, verifica finale.
- Per ogni fase opzionale, se è fatta o saltata: stile di scrittura (4b), `CLAUDE.md` (5), host interni e API fidate (6), sincronizzazione tra macchine (7), comando `arturo` nel terminale (7c), memoria accesa o spenta (7d), Google (8), `scrape` (8b), Impeccable (8c), sparring (10). Una fase saltata si recupera rilanciando `/setup`.
- **Come iniziare a lavorare**: "Ogni giorno ti bastano due comandi: `/inizio <nome>` per riprendere un progetto e `/fine` per chiuderlo. Quando ti viene in mente qualcosa da fare, dimmi "ricordami di…": lo ritrovi a ogni `/inizio`."
- **Gli altri comandi, quando servono**: "Non sai da dove partire? `/guidami` guarda il tuo lavoro recente e ti propone i prossimi passi. Qualcosa non torna in un progetto? `/diagnosi` controlla Arturo e il progetto, e ti dice cosa sistemare. Fai spesso lo stesso lavoro? `/creaskill` ti aiuta a farne una skill tua." Gli altri strumenti non elencarli: Claude li usa da solo quando servono.
- **Come restare aggiornato**: Arturo si aggiorna da solo, come Claude Code. Quando esce una versione nuova la barra in basso lo dice, e alla chiusura della sessione si installa, solo se è firmata da chi mantiene Arturo. **`/novita`** racconta cosa è cambiato e propone lo sparring. Per guardare prima ogni aggiornamento: `python3 ~/.claude/bin/arturo aggiornamenti manuali`, poi **`/aggiorna`** quando vuoi.
- **Telemetria**: ricorda in una riga se è accesa o spenta (`python3 ~/.claude/bin/arturo telemetria stato`), e che `python3 ~/.claude/bin/arturo telemetria mostra` fa vedere esattamente cosa parte.
- **Come far migliorare Arturo**: "Se qualcosa non funziona, o ti manca uno strumento, dimmelo o scrivi `/segnala`: preparo io il testo per chi mantiene Arturo, e parte solo con il tuo sì."
- Ricorda che `/system-audit` si può rilanciare in qualsiasi momento per ricontrollare l'harness.
