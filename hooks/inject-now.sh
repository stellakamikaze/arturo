#!/usr/bin/env bash
# UserPromptSubmit hook: inietta data/ora aggiornata in italiano.
# stdout viene aggiunto al context della sessione corrente.

# Forza locale italiano (fallback a default se non disponibile).
if locale -a 2>/dev/null | grep -qi '^it_IT\.UTF-8$'; then
  LC_TIME=it_IT.UTF-8 date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
else
  date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
fi

# --- Telemetria: quale comando di Arturo viene usato -----------------------------
# Solo il nome di un comando che esiste in ~/.claude/commands, mai il testo del prompt.
# read con tetto di 2 secondi: uno stdin lasciato aperto non deve appendere il prompt.
INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' INPUT || true
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

# --- Promemoria prompt-master ------------------------------------------------
# Il brief serve dove una richiesta può essere capita male, non a ogni messaggio: Arturo non deve
# intralciare l'uso naturale dell'LLM (Federico, 14/10/2026). Un comando /nome ha già il suo flusso
# e non riceve il promemoria. Questo hook non blocca e non chiede niente: aggiunge una riga al
# contesto. Se l'aderenza non sale, la riga va tolta invece che irrobustita.
# Per spegnerlo: cancella il blocco cat qui sotto, oppure togli la skill prompt-master.
if [ -z "$COMANDO" ]; then
cat <<'PROMEMORIA'
BRIEF: se questo messaggio chiede un lavoro che tocca piu' file, ha effetti fuori da questo
computer o si puo' capire in due modi, carica Skill(prompt-master) e mostra PROMPT e BRIEF in
poche righe prima di lavorare. Domande, conversazione e richieste chiare e piccole: rispondi e fai,
senza brief.
PROMEMORIA
fi

exit 0
