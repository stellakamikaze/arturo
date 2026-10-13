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
if [[ "$INPUT" =~ \"prompt\"[[:space:]]*:[[:space:]]*\"/([a-z0-9-]+) ]]; then
  NOME="${BASH_REMATCH[1]}"
  if [ -f "$HOME/.claude/commands/$NOME.md" ] && [ -f "$HOME/.claude/bin/telemetria.py" ]; then
    python3 "$HOME/.claude/bin/telemetria.py" registra comando "$NOME" >/dev/null 2>&1 || true
  fi
fi

# --- Promemoria prompt-master ------------------------------------------------
# La regola «PROMPT + BRIEF prima di ogni richiesta di lavoro» vive nella skill
# prompt-master, ma una regola scritta solo nel CLAUDE.md non regge: la misura sulla
# config da cui nasce Arturo dice che veniva applicata in meno di un terzo delle
# sessioni. Questo hook non blocca e non chiede niente: aggiunge una riga al contesto,
# dove la regola serve. Se l'aderenza non sale, la riga va tolta invece che irrobustita:
# sarebbe uno scaffold che non compensa niente.
# Per spegnerlo: cancella il blocco cat qui sotto, oppure togli la skill prompt-master.
cat <<'PROMEMORIA'
REGOLA FISSA: se questo messaggio e' una richiesta di lavoro, il primo tool e'
Skill(prompt-master) e le prime righe che scrivi sono PROMPT e BRIEF, con la riga
«Skill:» (quale skill usi e perche', o «nessuna»), prima di qualunque altro lavoro.
Esente solo la conversazione pura: domande, commenti, risposte a un menu; li' consiglia
una skill solo se c'entra davvero. Il brief non e' un gate: mostrato il prompt, se e'
giusto si procede.
PROMEMORIA

exit 0
