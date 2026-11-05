#!/usr/bin/env bash
# Reinstallazione di Arturo: riporta dalla copia messa da parte gli handoff, le skill, i comandi e i
# file .local che la persona ha fatto da sé (#3842, deciso da Federico il 2/11/2026: "riporta tutti i file personali").
#
# Uso: bash ~/.claude/bin/riporta-tuoi.sh <copia messa da parte>
# Lo lancia il blocco d'installazione del README e di /setup, dopo il clone e dopo la lista fissa.
#
# Un file è della persona se Arturo non l'ha mai avuto: nessun commit della storia di Arturo lo nomina.
# Così torna una skill fatta con /creaskill anche se /fine l'aveva salvata in un commit locale, e non torna
# un comando che Arturo ha tolto in un rilascio. Un file che il clone ha già non si tocca.
set -u
B="${1:-}"
D="$(cd "$(dirname "$0")/.." && pwd)"  # il clone appena fatto: lo script sta nel suo bin/
[ -n "$B" ] && [ -d "$B" ] || { echo "riporta-tuoi: copia messa da parte assente: $B" >&2; exit 2; }
git -C "$D" rev-parse --git-dir >/dev/null 2>&1 || { echo "riporta-tuoi: $D non è un clone di Arturo" >&2; exit 2; }
shopt -s nullglob
riportati=0
for x in "$B"/data/handoffs/* "$B"/skills/* "$B"/commands/* "$B"/agents/* "$B"/output-styles/* \
  "$B"/hooks/*.local "$B"/bin/*.local "$B"/skills/*/*.local "$B"/arturo/*.local; do
  r="${x#"$B"/}"
  [ -e "$D/$r" ] && continue
  [ -n "$(git -C "$D" log --format=%h -1 -- "$r" 2>/dev/null)" ] && continue
  mkdir -p "$(dirname "$D/$r")" && mv "$x" "$D/$r" && riportati=$((riportati + 1)) && echo "riportato: $r"
done
echo "riporta-tuoi: $riportati file o cartelle tuoi riportati"
