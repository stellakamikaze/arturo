#!/usr/bin/env bash
# UserPromptSubmit hook: inietta data/ora aggiornata in italiano.
# stdout viene aggiunto al context della sessione corrente.

# Forza locale italiano (fallback a default se non disponibile).
if locale -a 2>/dev/null | grep -qi '^it_IT\.UTF-8$'; then
  LC_TIME=it_IT.UTF-8 date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
else
  date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
fi

exit 0
