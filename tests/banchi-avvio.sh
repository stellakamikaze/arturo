#!/usr/bin/env bash
# Banchi rapidi delle guardie, lanciati in background da session-start.sh al massimo ogni 12 ore.
#
# Il gate completo (tests/verifica-allineamento.sh) chiede Claude Code, Chrome e un Python
# vecchio: non gira sul computer di chi usa Arturo. Questi banchi invece provano solo le
# guardie, con python3 e bash: se una guardia si rompe su questo computer (un Python diverso,
# un file cambiato a mano, una pipe che su Windows non e' in UTF-8), la sessione dopo lo dice
# invece di tacere.
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
BANCHI="test-block-dangerous-falsi-positivi.py test-web-egress-guard.py test_guardie_minori.py test_guardie_involucri.py test_guardie_unite.py test_heredoc.py test_heredoc_confini.py test_hook_utf8.py test_lavoro_proprio_2026_10_31.py test_revisione_2026_11_01.py"

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
TMPDIR_ORIGINALE="${TMPDIR:-/tmp}"
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
  # Dal 3/11/2026 la persona non lo sente: il rosso parte da solo verso chi mantiene Arturo, con la
  # telemetria (evento banchi, il nome del banco), solo quando l'elenco dei rossi cambia. La telemetria
  # spenta dalla persona resta spenta: la decide bin/telemetria.py. I banchi qui sopra girano con
  # ARTURO_TELEMETRIA=0, che vale per loro e non per questa chiamata.
  nomi=$(printf '%s' "$rossi" | sed 's/:.*//' | sort)
  prima=$(sed -n '3,$p' "$ESITO" 2>/dev/null | sed 's/:.*//' | sort)
  TELEMETRIA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/bin/telemetria.py"
  if [ "$nomi" != "$prima" ] && [ -f "$TELEMETRIA" ]; then
    for nome in $nomi; do
      env -u ARTURO_TELEMETRIA TMPDIR="${TMPDIR_ORIGINALE:-/tmp}" python3 -B "$TELEMETRIA" registra banchi "$nome" >/dev/null 2>&1
    done
  fi
  quanti=$(printf '%s' "$rossi" | grep -c .)
  printf 'ROSSO\n%s banchi delle guardie rossi su %s (%s)\n%s' "$quanti" "$n" "$(date '+%Y-%m-%d %H:%M')" "$rossi" > "$ESITO"
  exit 1
fi
printf 'VERDE\n%s banchi delle guardie verdi (%s)\n' "$n" "$(date '+%Y-%m-%d %H:%M')" > "$ESITO"
exit 0
