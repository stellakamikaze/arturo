#!/usr/bin/env bash
# UserPromptSubmit hook: inietta data/ora aggiornata in italiano.
# stdout viene aggiunto al context della sessione corrente.

# Forza locale italiano (fallback a default se non disponibile).
if locale -a 2>/dev/null | grep -qi '^it_IT\.UTF-8$'; then
  LC_TIME=it_IT.UTF-8 date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
else
  date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
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
Skill(prompt-master) e le prime righe che scrivi sono PROMPT e BRIEF, prima di
qualunque altro lavoro. Esente solo la conversazione pura: domande, commenti,
risposte a un menu. Il brief non e' un gate: mostrato il prompt, se e' giusto si procede.
PROMEMORIA

exit 0
