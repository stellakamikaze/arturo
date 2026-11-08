#!/usr/bin/env bash
# UserPromptSubmit hook: inietta data/ora aggiornata in italiano.
# stdout viene aggiunto al context della sessione corrente.
# Un solo file per la config dell'autore e per Arturo (20/10/2026): telemetria e aggiunte
# personali tacciono dove mancano bin/telemetria.py e personale/.

# Il prompt arriva in UTF-8 e Claude Code legge l'uscita in UTF-8: su Windows python3 userebbe cp1252
# su stdin e stdout (5/11/2026, #4790; stesso rimedio di bash-dispatcher.sh).
export PYTHONIOENCODING=utf-8

# Forza locale italiano (fallback a default se non disponibile).
if locale -a 2>/dev/null | grep -qi '^it_IT\.UTF-8$'; then
  LC_TIME=it_IT.UTF-8 date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
else
  date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
fi

# read con tetto di 2 secondi: uno stdin lasciato aperto non deve appendere il prompt.
INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' INPUT || true

# Il hook scatta anche sui report dei subagent e sui messaggi fra sessioni (hooks.md,
# UserPromptSubmit): lì il promemoria non serve e finiva attaccato a ogni report
# (19/10/2026). Stesso filtro di SYSTEM_ENVELOPE in memory-retrieve.py.
if printf '%s' "$INPUT" | python3 -c 'import sys, json, re
try:
    p = json.loads(sys.stdin.buffer.read().decode("utf-8")).get("prompt", "")
except Exception:
    sys.exit(1)
busta = r"\s*(?:Another Claude session sent a message:\s*)?<(task-notification|agent-message|cross-session-message|teammate-message|bash-stdout|local-command-stdout)\b"
sys.exit(0 if isinstance(p, str) and re.match(busta, p) else 1)' 2>/dev/null; then
  exit 0
fi

# --- Correzioni della sessione (Computer Club N.3, [0:01:09]; #4099, 4/11/2026) ----------
# "Tre volte di fila ho fatto un errore, tu me l'hai fatto notare tutte e tre le volte": una correzione
# scritta con `arturo correzione aggiungi` torna qui a ogni messaggio, anche dopo una compattazione.
# Nessuna correzione, nessuna riga. Cosa è una correzione lo decide Claude (promemoria qui sotto).
_A="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ -f "$_A/bin/correzioni.py" ]; then
  printf '%s' "$INPUT" | python3 "$_A/bin/correzioni.py" blocco 2>/dev/null || true
fi

# --- Avviso prima di un ultracode (Computer Club N.3, 28/10/2026) ----------------
# Un ultracode lancia molti agenti: il 27/10 uno ha usato circa il 5% della finestra di 5 ore
# in pochi minuti, e chi lo lanciava non lo sapeva. La quota la scrive la statusline in
# cache/statusline/quota.json; se manca, la riga dice solo il costo.
if [[ "$INPUT" =~ [Uu][Ll][Tt][Rr][Aa][Cc][Oo][Dd][Ee] ]]; then
  QUOTA="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/cache/statusline/quota.json"
  python3 - "$QUOTA" <<'ULTRACODE' 2>/dev/null || true
import json, sys, time
riga = ("ULTRACODE: prima di lanciarlo, di' alla persona che lancia molti agenti e costa quota "
        "(il 27/10 un lancio ha usato circa il 5% della finestra di 5 ore in pochi minuti)")
try:
    q = json.load(open(sys.argv[1], encoding="utf-8")).get("cinque_ore") or {}
    pct, resets = q.get("pct"), q.get("resets")
    if isinstance(pct, int):
        riga += f"; oggi la finestra di 5 ore è al {pct}%"
        if isinstance(resets, (int, float)) and resets > time.time():
            riga += f" e si azzera alle {time.strftime('%H:%M', time.localtime(resets))}"
except Exception:
    pass
print(riga + ". Chiedi il sì e di' quanti agenti partono.")
ULTRACODE
fi

# --- Telemetria: quale comando di Arturo viene usato -----------------------------
# Solo il nome di un comando che esiste in ~/.claude/commands, mai il testo del prompt. Un comando
# della persona esce come `altro` (bin/telemetria.py, COMANDI), dal 24/10/2026.
COMANDO=""
if [[ "$INPUT" =~ \"prompt\"[[:space:]]*:[[:space:]]*\"/([a-z0-9-]+) ]]; then
  COMANDO="${BASH_REMATCH[1]}"
  # Il codice sta accanto a questo file (docs/strati.md): $_A, definito sopra. Nel plugin un comando è una skill.
  # Un comando di Arturo o dell'Orsa: telemetria.py manda il nome solo se è di Arturo, se no `altro`.
  if { [ -f "$_A/commands/$COMANDO.md" ] || [ -f "$_A/skills/$COMANDO/SKILL.md" ] \
       || [ -f "$HOME/.claude/commands/$COMANDO.md" ] || [ -f "$HOME/.claude/skills/$COMANDO/SKILL.md" ]; } \
     && [ -f "$_A/bin/telemetria.py" ]; then
    python3 "$_A/bin/telemetria.py" registra comando "$COMANDO" >/dev/null 2>&1 || true
  fi
  # --- Aggiunte personali al comando ------------------------------------------------
  # Le aggiunte della persona a un comando di Arturo stanno in ~/.claude/personale/<comando>.md,
  # fuori da git: gli aggiornamenti non le toccano e non vanno in conflitto (arturo personale).
  if [ -f "$HOME/.claude/personale/$COMANDO.md" ]; then
    echo "PERSONALE: /$COMANDO ha aggiunte della persona in ~/.claude/personale/$COMANDO.md. Leggile prima di cominciare e applicale insieme al comando, dove non contraddicono i Freni."
  fi
fi

# --- Promemoria prompt-master (dal 9/9/2026) ----------------------------------
# La regola "PROMPT + BRIEF prima, su ogni richiesta di lavoro" scritta e basta non reggeva:
# la misura del 9/9/2026 dava un brief in 16 sessioni su 54. Questo hook non blocca e non
# chiede niente: aggiunge una riga al contesto, dove la regola serve. Un comando /nome ha già
# il suo flusso e non riceve il promemoria. Dal 27/10/2026 (segnalazione n. 17) la skill si
# carica una volta per sessione: ogni Skill(prompt-master) rimetteva nel contesto il corpo
# intero. Una correzione a lavoro iniziato è una riga, come nella skill (segnalazione n. 34, 29/10/2026).
# L'8/11/2026 il testo è sceso da 903 a circa 470 byte: il resto sta già nel corpo della skill. Gli stop
# sono esenti come nel corpo. La riga sulle correzioni esce solo dove c'è bin/correzioni.py: senza, il
# comando `arturo correzione` non esiste e la riga prometteva una cosa che non succede.
# Per spegnerlo: cancella il blocco cat qui sotto, oppure togli la skill prompt-master.
if [ -z "$COMANDO" ]; then
cat <<'PROMEMORIA'
REGOLA FISSA: se questo messaggio chiede un lavoro, anche piccolo, le prime righe sono PROMPT e
BRIEF con la riga "Skill:". Se il corpo di prompt-master non è nel contesto (sessione nuova o dopo
una compattazione), il primo tool è Skill(prompt-master), una volta per sessione. Esenti: domande,
commenti, risposte a un menu, stop e comandi di controllo; lì consiglia una skill solo se c'entra
davvero. Una correzione a lavoro iniziato è una riga, "Brief corretto: ...".
PROMEMORIA
  if [ -f "$_A/bin/correzioni.py" ]; then
cat <<'CORREZIONE'
Se questo messaggio ti corregge (un errore, un modo di fare, una parola), prima di rifare scrivi la
regola in una riga con: arturo correzione aggiungi "..." . Da lì vale per tutta la sessione.
CORREZIONE
  fi
fi

exit 0
