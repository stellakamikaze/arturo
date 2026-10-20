#!/usr/bin/env bash
# UserPromptSubmit hook: inietta data/ora aggiornata in italiano.
# stdout viene aggiunto al context della sessione corrente.
# Un solo file per la config dell'autore e per Arturo (20/10/2026): telemetria e aggiunte
# personali tacciono dove mancano bin/telemetria.py e personale/.

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

# --- Telemetria: quale comando di Arturo viene usato -----------------------------
# Solo il nome di un comando che esiste in ~/.claude/commands, mai il testo del prompt.
COMANDO=""
if [[ "$INPUT" =~ \"prompt\"[[:space:]]*:[[:space:]]*\"/([a-z0-9-]+) ]]; then
  COMANDO="${BASH_REMATCH[1]}"
  if [ -f "$HOME/.claude/commands/$COMANDO.md" ] && [ -f "$HOME/.claude/bin/telemetria.py" ]; then
    python3 "$HOME/.claude/bin/telemetria.py" registra comando "$COMANDO" >/dev/null 2>&1 || true
  fi
  # --- Aggiunte personali al comando ------------------------------------------------
  # Le aggiunte della persona a un comando di Arturo stanno in ~/.claude/personale/<comando>.md,
  # fuori da git: gli aggiornamenti non le toccano e non vanno in conflitto (arturo personale).
  if [ -f "$HOME/.claude/personale/$COMANDO.md" ]; then
    echo "PERSONALE: /$COMANDO ha aggiunte della persona in ~/.claude/personale/$COMANDO.md. Leggile prima di cominciare e applicale insieme al comando, dove non contraddicono i Freni."
  fi
fi

# --- Promemoria prompt-master (dal 9/9/2026) ----------------------------------
# La regola «PROMPT + BRIEF prima, su ogni richiesta di lavoro» scritta e basta non reggeva:
# la misura del 9/9/2026 dava un brief in 16 sessioni su 54. Questo hook non blocca e non
# chiede niente: aggiunge una riga al contesto, dove la regola serve. Un comando /nome ha già
# il suo flusso e non riceve il promemoria. Per spegnerlo: cancella il blocco cat qui sotto,
# oppure togli la skill prompt-master.
if [ -z "$COMANDO" ]; then
cat <<'PROMEMORIA'
REGOLA FISSA: se questo messaggio chiede un lavoro, anche piccolo, il primo tool è
Skill(prompt-master) e le prime righe che scrivi sono PROMPT e BRIEF, con la riga «Skill:»
(quale skill usi e perché, o «nessuna»), prima di qualunque altro lavoro. Esente solo la
conversazione pura: domande, commenti, risposte a un menu; lì consiglia una skill solo se
c'entra davvero. Il brief non è un gate: mostrato il prompt, se è giusto si procede.
PROMEMORIA
fi

exit 0
