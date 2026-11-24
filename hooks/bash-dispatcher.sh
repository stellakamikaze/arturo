#!/bin/bash
# Guscio del dispatcher delle guardie di Bash: il lavoro lo fa hooks/dispatcher.py (#6492, 23/11/2026).
# Fino al 23/11/2026 questo file faceva tutto in bash: il pre-filtro, i rami e un processo python per guardia.
# Su Windows erano 1,6 s di mediana prima di ogni comando. Ora hooks/hub.py lancia dispatcher.py nello stesso
# processo degli altri hook di PreToolUse; questo guscio resta per i banchi e per le config che lo chiamano.
#
# Esiti di dispatcher.py:
#   0  -> la decisione su stdout, oppure niente;
#   2  -> blocco duro, il motivo è già su stderr;
#   altro (python3 che non parte, come il rimando del Microsoft Store che esce 49, un guasto, il tetto di
#   25 secondi superato) -> si chiede conferma se l'evento porta un comando, mai un allow implicito
#   (revisione del 10/11/2026, HK-2; #6363).

# Il JSON di Claude Code è UTF-8. Su Windows ogni python3 leggeva e scriveva in cp1252 (16/10/2026).
export PYTHONIOENCODING=utf-8
QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
INPUT=$(cat)
OUT=$(printf '%s' "$INPUT" | python3 "$QUI/dispatcher.py")
RC=$?
case $RC in
    0) [[ -n "$OUT" ]] && printf '%s\n' "$OUT"; exit 0 ;;
    2) exit 2 ;;
esac
_RE_HA_COMANDO='"command"[[:space:]]*:[[:space:]]*"[^"]'
if [[ "$INPUT" =~ $_RE_HA_COMANDO ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Le guardie non hanno letto il comando: manca un python3 che funziona, oppure si sono fermate oltre il tempo. Conferma solo se sai cosa fa. Per sistemare: /diagnosi."}}'
fi
exit 0
