#!/usr/bin/env bash
# SessionStart del plugin: mette nel contesto il metodo di Arturo (shared/metodo.md, strati F2, docs/strati.md).
# Un plugin non può portare un CLAUDE.md: il metodo arriva da qui, sotto i 10.000 caratteri che Claude Code
# passa al modello per ogni hook. È un hook a sé, non una riga di session-start.sh, perché il tetto vale per
# l'uscita di ogni hook e quella dell'avvio cresce con handoff e memoria.
# Col clone il metodo non scatta: settings.json non registra questo hook, e le regole stanno nel CLAUDE.md
# che la persona ha scritto con /setup (shared/setup-claude-md.md).
CODICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)" || exit 0
[ -f "$CODICE/shared/metodo.md" ] || exit 0
testo="$(cat "$CODICE/shared/metodo.md")"
# Read non espande le variabili: il percorso al codice arriva già risolto.
printf '%s\n' "${testo//\$ARTURO_CODICE/$CODICE}"
exit 0
