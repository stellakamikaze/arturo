#!/usr/bin/env bash
# review-prep.sh: prepara i digest per review.workflow.js (revisione con più agenti della config).
#
# Gli agenti di un workflow leggono soltanto (Read): ogni ricerca la fa questo script, prima, e gli
# agenti leggono i file che scrive.
#
#   bash ~/.claude/skills/system-audit/review-prep.sh <cartella-di-uscita> [dal AAAA-MM-GG]
#
# Scrive in <cartella>: config-log.txt, touched-files.txt, gone-files.txt, git-status.txt,
# root-ls.txt, tree.txt, ignored-root.txt, grep-index.txt. Stampa i conteggi.
# Exit 1 se manca la cartella di uscita o se ~/.claude non è un repository git.
#
# I termini dell'indice grep: un elenco neutro qui sotto, più le righe del file facoltativo
# review-termini.local accanto a questo script (una parola o un'espressione per riga, fuori da git).
# Lì vanno i nomi che solo tu sai riconoscere: un servizio dismesso, un tuo vecchio percorso.
set -u
OUT="${1:-}"; DAL="${2:-$(date -v-21d +%Y-%m-%d 2>/dev/null || date -d '21 days ago' +%Y-%m-%d)}"
[ -n "$OUT" ] || { echo "uso: $0 <cartella-di-uscita> [dal AAAA-MM-GG]"; exit 1; }
H="$HOME/.claude"
git -C "$H" rev-parse --git-dir >/dev/null 2>&1 || { echo "$H non è un repository git: la revisione legge la sua storia"; exit 1; }
mkdir -p "$OUT"
# I dati della persona (todo, handoff, memoria, telemetria) non sono config: restano fuori.
ESCL=(':!data' ':!projects' ':!personale')

git -C "$H" log --since="$DAL" --pretty='=== %h %ad %s' --date=short --stat=160 -- . "${ESCL[@]}" > "$OUT/config-log.txt"
git -C "$H" log --since="$DAL" --name-only --pretty=format: -- . "${ESCL[@]}" | sort -u | grep -v '^$' > "$OUT/touched-files.txt"
while IFS= read -r f; do [ -e "$H/$f" ] || echo "GONE $f"; done < "$OUT/touched-files.txt" > "$OUT/gone-files.txt"
git -C "$H" status --short > "$OUT/git-status.txt"
ls -la "$H" > "$OUT/root-ls.txt"
(cd "$H" && ls -R skills commands agents hooks bin shared tests tools docs output-styles 2>/dev/null | grep -v '^$') > "$OUT/tree.txt"
(cd "$H" && git check-ignore -v $(ls -A) 2>/dev/null) > "$OUT/ignored-root.txt"

# Indice grep: credenziali lette a mano, percorsi fissi di una sola macchina, exit code letti dopo
# una pipe, timeout che su un Mac senza coreutils non esiste, segnaposti rimasti nel codice.
TERMINI='cat ~/.claude/data/credentials|/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|C:\\Users\\|PIPESTATUS|(^|[^-])timeout [0-9]|\bTODO\b|\bFIXME\b'
DOVE=(CLAUDE.md README.md settings.json commands skills agents hooks bin shared tests tools docs output-styles)
cerca() { (cd "$H" && grep -rnIE "$@" "${DOVE[@]}" 2>/dev/null | grep -v '/node_modules/\|/\.venv/\|/__pycache__/' | cut -c1-240); }
{
  cerca "$TERMINI"
  # I termini tuoi, senza distinguere maiuscole e minuscole.
  LOCALE="$(dirname "$0")/review-termini.local"
  if [ -f "$LOCALE" ]; then
    MIEI=$(grep -vE '^[[:space:]]*(#|$)' "$LOCALE" | paste -sd '|' -)
    [ -n "$MIEI" ] && cerca -i "$MIEI"
  fi
} | sort -u > "$OUT/grep-index.txt"

for f in config-log touched-files gone-files git-status root-ls tree ignored-root grep-index; do
  printf '%-14s %6s righe\n' "$f" "$(wc -l < "$OUT/$f.txt" | tr -d ' ')"
done
echo "dal: $DAL · cartella: $OUT"
