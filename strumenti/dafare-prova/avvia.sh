#!/bin/zsh
# Prototipo del pannello /dafare (linguette A3 e catena B2, 23/10/2026) con dati di esempio.
# Apre Claude Code in una cartella vuota col mod caricato:
#   avvia.sh a-lato    schermo intero: pannello a lato da 110 colonne, in linea sotto, clic del mouse
#   avvia.sh in-linea  terminale normale: pannello sopra il prompt, solo tasti
#   avvia.sh testo     terminale normale: /dafare-prova testo scrive l'elenco nella conversazione
# Test: claude plugin test <questa cartella>
MOD=${0:A:h}
PROVA=$(mktemp -d)
cd "$PROVA" || exit 1
case "${1:-a-lato}" in
  a-lato)   exec claude --plugin-dir "$MOD" --settings '{"tui":"fullscreen"}' "/dafare-prova" ;;
  in-linea) exec claude --plugin-dir "$MOD" --settings '{"tui":"default"}' "/dafare-prova" ;;
  testo)    exec claude --plugin-dir "$MOD" --settings '{"tui":"default"}' "/dafare-prova testo" ;;
  *) echo "Uso: avvia.sh a-lato | in-linea | testo" >&2; exit 2 ;;
esac
