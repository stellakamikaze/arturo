---
description: Lo strato dell'organizzazione sopra Arturo. `crea` e `pubblica` per il referente, `installa <indirizzo>` per i colleghi
argument-hint: "crea | pubblica | installa <indirizzo-del-repository>"
---

# Strato dell'organizzazione

Lo **strato** è ciò che rende Arturo «suo» per un'organizzazione: chi siamo, la voce e le regole
di scrittura, i lavori ricorrenti trasformati in skill, i dati che non devono uscire. È un plugin
di Claude Code che vive nel repository dell'organizzazione. Lo cura un **referente** interno, i
colleghi lo installano e lo ricevono aggiornato. La guida del ruolo è in
`~/.claude/docs/referente.md`.

Chi ti parla **potrebbe non essere una persona tecnica**: una fase per volta, parole semplici,
nessun output grezzo senza spiegazione.

Leggi `$ARGUMENTS` e segui solo la fase che corrisponde. Senza argomento, spiega in tre righe le
tre fasi e chiedi quale serve.

---

## crea — il referente prepara lo strato

1. **Nome.** Chiedi il nome dell'organizzazione e ricavane lo slug (minuscole, trattini):

   ```bash
   ORG="<nome dell'organizzazione>"
   SLUG=$(printf '%s' "$ORG" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
   PB="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"; PB="${PB/#\~/$HOME}"
   DEST="$PB/$SLUG-strato"
   [ -e "$DEST" ] && echo "ESISTE GIA': $DEST" || echo "Cartella: $DEST"
   ```

   Se la cartella esiste, fermati: lo strato c'è già. Proponi di aprirlo invece di rifarlo.

2. **Copia il modello e riempi il nome.**

   ```bash
   cp -R "$HOME/.claude/templates/strato" "$DEST"
   python3 - "$DEST" "$SLUG" "$ORG" <<'PY'
   import sys
   from pathlib import Path
   radice, slug, org = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
   for f in radice.rglob("*"):
       if f.is_file() and f.suffix in (".json", ".md"):
           f.write_text(f.read_text(encoding="utf-8").replace("{{SLUG}}", slug).replace("{{ORGANIZZAZIONE}}", org), encoding="utf-8")
   PY
   git -C "$DEST" init -q -b main && echo "Strato creato in $DEST"
   ```

3. **Intervista breve**, una domanda per volta. Con le risposte riempi i file, mostrando prima
   cosa scrivi:
   - chi siete, per chi lavorate, parole con un significato vostro → `plugins/strato/ORGANIZZAZIONE.md`;
   - come suonano i vostri testi, parole che usate e che evitate, forma di email e documenti →
     `plugins/strato/skills/voce/regole.md`. Se esiste già un documento di stile, parti da quello;
   - **due** lavori che si ripetono ogni settimana o ogni mese → due skill, copiando
     `plugins/strato/skills/modello-lavoro/` con un nome nuovo e togliendo
     `disable-model-invocation`;
   - cosa non deve mai uscire dal computer senza una conferma (progetti riservati, cartelle,
     domini interni) → `plugins/strato/dati-riservati.txt`. Mai password o token in questo file:
     è letto da tutti i colleghi.

4. **Prova prima di pubblicare.** Il referente apre una sessione nuova con lo strato caricato
   dalla cartella, senza installarlo:

   ```bash
   claude plugin validate "$DEST" && claude plugin validate "$DEST/plugins/strato"
   echo "Per provarlo: cd \"$DEST\" && claude --plugin-dir plugins/strato"
   ```

   Non usare `claude plugin marketplace add` sulla cartella locale: creerebbe un secondo
   marketplace con lo stesso nome di quello che i colleghi installeranno dal repository.

5. **Il repository dell'organizzazione.** Deve essere **privato**. Se c'è `gh` ed è collegato:

   ```bash
   gh repo create "$SLUG-strato" --private --source "$DEST" --remote origin
   ```

   Se l'organizzazione ha un'organizzazione GitHub, usa `<org-github>/$SLUG-strato`. Se `gh` non
   c'è, guida il referente sul sito: nuovo repository, visibilità Private, poi
   `git -C "$DEST" remote add origin <indirizzo>`. Poi passa a **pubblica**.

---

## pubblica — il referente manda le modifiche ai colleghi

```bash
DEST="${DEST:-$(pwd)}"
cd "$DEST" || exit 1
python3 -c 'import json,sys; [json.load(open(f)) for f in sys.argv[1:]]' .claude-plugin/marketplace.json plugins/strato/.claude-plugin/plugin.json plugins/strato/hooks/hooks.json && echo "JSON validi"
python3 -c 'open("plugins/strato/dati-riservati.txt", encoding="utf-8").read()' && echo "dati-riservati.txt leggibile"
claude plugin validate . >/dev/null && echo "marketplace valido"
date +%Y-%m-%d > plugins/strato/.ultima-pubblicazione
git add -A && git commit -m "strato: pubblicazione $(date +%Y-%m-%d)" && git push -u origin main
```

Il commit passa dal controllo segreti di Arturo: se trova un segreto, fermati e spiega come
toglierlo. Se un controllo sopra fallisce, non pubblicare: mostra quale file è rotto e sistemalo
con il referente. Dopo il push, i colleghi ricevono la modifica con `/aggiorna`.

---

## installa — un collega riceve lo strato

Prerequisiti: Arturo installato (è da qui che arriva questo comando) e un invito del referente al
repository. Chi non usa Arturo può installare lo strato dal comando `/plugin` di Claude Code.

1. **Prova l'accesso**, prima di tutto il resto:

   ```bash
   URL="<indirizzo del repository>"
   GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes" git ls-remote "$URL" >/dev/null 2>&1 \
     && echo "ACCESSO OK" || echo "ACCESSO NEGATO"
   command -v gh >/dev/null && gh auth status 2>&1 | head -3
   ```

   Con `ACCESSO NEGATO` non mostrare l'errore di git. Spiega cosa manca, nell'ordine:
   - un account sul servizio dove sta il repository (GitHub, GitLab);
   - l'invito del referente al repository, accettato;
   - il collegamento di questo computer all'account: `gh auth login`, poi `gh auth setup-git`.

   Il collega può eseguirli scrivendo `! gh auth login` nel prompt. Poi ripeti la prova.

2. **Installa.**

   ```bash
   # Nomi di marketplace e plugin letti dal repository stesso, non indovinati dall'indirizzo.
   COPIA=$(mktemp -d)
   git clone -q --depth 1 "$URL" "$COPIA/strato"
   read -r MKT PLUGIN < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(m["name"], m["plugins"][0]["name"])' "$COPIA/strato/.claude-plugin/marketplace.json")
   # La copia resta nella cartella temporanea: la pulisce il sistema. Un `rm -rf` su una
   # variabile farebbe chiedere conferma alla guardia di Arturo.
   claude plugin marketplace add "$URL"
   claude plugin install "$PLUGIN@$MKT"
   claude plugin list 2>/dev/null | grep -i "$PLUGIN"
   ```

   Mostra al collega cosa hai installato, con i nomi letti qui sopra.

3. **Aggiornamenti automatici.** Per i marketplace delle organizzazioni sono spenti di serie. Digli
   come accenderli: `/plugin` → Marketplaces → il marketplace dello strato → aggiornamento
   automatico. In ogni caso `/aggiorna` scarica anche lo strato.

4. **Riapri Claude Code.** Un plugin appena installato si carica solo nella sessione successiva.
   Dopo il riavvio lo strato si presenta da solo: all'avvio Claude sa per quale organizzazione
   lavora, e la skill della voce compare come `/<nome-dello-strato>:voce`.

---

## Freni

- Lo strato si cambia solo nel suo repository e si pubblica con `pubblica`. Mai modificare i file
  installati in `~/.claude/plugins/`: il prossimo aggiornamento li sovrascrive.
- Mai password, token o dati personali nello strato: lo leggono tutti i colleghi.
- Il repository dello strato è privato. Se `gh repo view` lo dice pubblico, fermati e avvisa.
