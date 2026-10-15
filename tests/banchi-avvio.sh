#!/usr/bin/env bash
# Banchi rapidi delle guardie, lanciati in background da session-start.sh al massimo ogni 12 ore.
#
# Il gate completo (tests/verifica-allineamento.sh) chiede Claude Code, Chrome e un Python
# vecchio: non gira sul computer di chi usa Arturo. Questi banchi invece provano solo le
# guardie, con python3 e bash: se una guardia si rompe su questo computer (un Python diverso,
# un file cambiato a mano), la sessione dopo lo dice invece di tacere.
#
# Lavora su una copia dei soli file tracciati di ~/.claude (modifiche comprese), in una
# cartella temporanea: i banchi copiano il repo piu' volte, e ~/.claude puo' pesare giga.
# Scrive l'esito in ~/.claude/cache/banchi-ultimo-esito.txt:
#   riga 1: VERDE o ROSSO
#   riga 2: riepilogo
#   righe seguenti: i banchi rossi
# Uso: bash ~/.claude/tests/banchi-avvio.sh  (esce 1 se un banco e' rosso)

CLAUDE_DIR="${ARTURO_DIR:-$HOME/.claude}"
CACHE="$CLAUDE_DIR/cache"
ESITO="$CACHE/banchi-ultimo-esito.txt"
BANCHI="test-block-dangerous-falsi-positivi.py test-web-egress-guard.py test_guardie_minori.py test_guardie_involucri.py test_guardie_unite.py"

mkdir -p "$CACHE" || exit 1
LAVORO=$(mktemp -d "${TMPDIR:-/tmp}/arturo-banchi.XXXXXX") || exit 1
trap 'rm -rf "$LAVORO"' EXIT
COPIA="$LAVORO/claude"
mkdir -p "$COPIA"

# Solo i file tracciati, con le modifiche non salvate. Senza git: le cartelle che servono ai banchi.
if git -C "$CLAUDE_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$CLAUDE_DIR" ls-files -z | (cd "$CLAUDE_DIR" && tar --null -T - -cf - 2>/dev/null) | tar -xf - -C "$COPIA" 2>/dev/null
else
  for parte in hooks tests bin settings.json .gitignore; do
    [ -e "$CLAUDE_DIR/$parte" ] && cp -R "$CLAUDE_DIR/$parte" "$COPIA/" 2>/dev/null
  done
fi

# I banchi non devono rilanciare se stessi da una session-start di prova.
export ARTURO_BANCHI_AVVIO=0 ARTURO_TELEMETRIA=0 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$LAVORO"

rossi=""
n=0
for banco in $BANCHI; do
  [ -f "$COPIA/tests/$banco" ] || continue
  n=$((n + 1))
  python3 -B "$COPIA/tests/$banco" --repo "$COPIA" > "$LAVORO/esito.txt" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then
    motivo=$(grep -m1 -E 'AssertionError|Error' "$LAVORO/esito.txt" | cut -c1-160)
    rossi="${rossi}${banco}: ${motivo:-rc $rc}
"
  fi
done

if [ -n "$rossi" ]; then
  quanti=$(printf '%s' "$rossi" | grep -c .)
  printf 'ROSSO\n%s banchi delle guardie rossi su %s (%s)\n%s' "$quanti" "$n" "$(date '+%Y-%m-%d %H:%M')" "$rossi" > "$ESITO"
  exit 1
fi
printf 'VERDE\n%s banchi delle guardie verdi (%s)\n' "$n" "$(date '+%Y-%m-%d %H:%M')" > "$ESITO"
exit 0
