#!/usr/bin/env bash
# banco-gate.sh: i gate di audit.sh discriminano davvero?
# Ogni caso avvelenato (costruito sbagliato apposta) deve essere bocciato; ogni caso sano deve passare.
#
#   bash ~/.claude/skills/system-audit/tests/banco-gate.sh [cartella-di-arturo]
#
# Il banco copia Arturo in una HOME temporanea e avvelena solo la copia: la tua ~/.claude non cambia.
# BANCO_AUDIT=<path> prova un altro audit.sh: un caso nuovo va provato anche sul codice vecchio,
# che lo deve sbagliare. Un caso che anche la versione rotta supera non discrimina niente.
# Exit 0 tutti i casi verdi, 1 almeno un caso rosso, 3 banco guasto.
set -u
SORGENTE="${1:-$(cd "$(dirname "$0")/../../.." && pwd)}"
[ -f "$SORGENTE/skills/system-audit/audit.sh" ] || { echo "banco guasto: $SORGENTE non è una copia di Arturo"; exit 3; }
LAVORO="$(mktemp -d "${TMPDIR:-/tmp}/banco-audit.XXXXXX")" || exit 3
trap 'rm -rf "$LAVORO"' EXIT INT TERM
CASA="$LAVORO/home"
C="$CASA/.claude"
mkdir -p "$C"
# La copia senza .git: l'audit legge solo i file.
(cd "$SORGENTE" && tar -cf - --exclude .git .) | (cd "$C" && tar -xf -) || { echo "banco guasto: copia fallita"; exit 3; }
AUD="${BANCO_AUDIT:-$C/skills/system-audit/audit.sh}"
OUT="$LAVORO/out.txt"

CASI=(); ESITI=()
audit() { HOME="$CASA" USERPROFILE="$CASA" bash "$AUD" >"$OUT" 2>&1 </dev/null; }
# caso <nome> <trova|manca> <regex>: dopo l'audit, la regex deve comparire (trova) o mancare (manca)
caso() {
  local nome="$1" atteso="$2" regex="$3"
  CASI+=("$nome"); audit
  if grep -qE -- "$regex" "$OUT"; then trovato=trova; else trovato=manca; fi
  if [ "$trovato" = "$atteso" ]; then ESITI+=("VERDE"); else ESITI+=("ROSSO"); fi
}

S="$C/skills/_banco-avvelenato"
mkdir -p "$S"
if python3 -c 'import yaml' >/dev/null 2>&1; then
  printf -- '---\nname: _banco-avvelenato\ndescription: Rotta così: i due punti spezzano il mapping YAML\n---\n# x\n' > "$S/SKILL.md"
  caso "gate-yaml boccia ': ' non quotato in una skill" trova '^FAIL  skill: SKILL.md mancante oppure frontmatter non valido'
else
  CASI+=("gate-yaml boccia ': ' non quotato (serve PyYAML, assente)"); ESITI+=("ROSSO")
fi

printf -- '---\nname: _banco-avvelenato\n---\n# x\n' > "$S/SKILL.md"
caso "gate-yaml boccia description mancante" trova '^FAIL  skill: SKILL.md mancante oppure frontmatter non valido'

printf -- '---\nname: _banco-avvelenato\ndescription: >-\n  Skill sana di prova, con i due punti: dentro un blocco folded.\n---\n# x\n' > "$S/SKILL.md"
caso "gate-yaml passa una skill sana" manca '^FAIL  skill'
rm -rf "$S"

A="$C/agents/zbanco-avvelenato.md"
mkdir -p "$C/agents"
printf -- '---\nname: zbanco-avvelenato\n---\n# agent senza description\n' > "$A"
caso "gate-yaml boccia un agent senza description" trova '^FAIL  frontmatter agenti'
rm -f "$A"

K="$C/commands/_banco.md"
printf -- '---\ndescription: banco\n---\nUsa `/comando-che-non-esiste-mai` per provare.\n' > "$K"
caso "gate-fantasma boccia un comando inesistente" trova '^WARN  commands/_banco.md:4 cita /comando-che-non-esiste-mai'

printf -- '---\ndescription: banco\n---\nHa assorbito il vecchio `/comando-che-non-esiste-mai`, rimosso.\n' > "$K"
caso "gate-fantasma ignora la menzione storica" manca 'comando-che-non-esiste-mai'

printf -- '---\ndescription: banco\n---\nLancia `/fine` a fine sessione, poi `/clear`.\n' > "$K"
caso "gate-fantasma passa un comando di Arturo e uno di Claude Code" manca '_banco.md.*cita'

printf -- '---\ndescription: banco\n---\nLegge i comandi `perl`/`nc`/redirezioni e `/dafare`.\n' > "$K"
caso "gate-fantasma: un backtick che chiude non apre un comando" manca '_banco.md.*cita'

{ printf -- '---\ndescription: banco\n---\n'; i=0; while [ $i -lt 700 ]; do printf 'riga di riempimento per superare il tetto di peso del corpo.\n'; i=$((i+1)); done; } > "$K"
caso "peso dei corpi: un comando oltre 30 KB" trova '^WARN  commands/_banco.md pesa [0-9]+ KB'
rm -f "$K"

mkdir -p "$C/plugins"
printf '{"plugins": {"pluginfinto@banco": [{"scope": "user"}]}}\n' > "$C/plugins/installed_plugins.json"
caso "plugin installato ma non attivo" trova '^WARN  plugin installati ma non attivi: pluginfinto@banco'
rm -f "$C/plugins/installed_plugins.json"

# Smoke: un hook Python cablato in settings.json che esce 1 deve dare FAIL.
H=$(python3 - "$C/settings.json" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for blocchi in d.get("hooks", {}).values():
    for b in blocchi:
        for h in b.get("hooks", []):
            m = re.search(r"hooks/([A-Za-z0-9_.-]+\.py)", h.get("command", ""))
            if m:
                print(m.group(1)); raise SystemExit
PY
)
if [ -n "$H" ] && [ -f "$C/hooks/$H" ]; then
  cp "$C/hooks/$H" "$LAVORO/hook.bak"
  printf 'import sys\nsys.exit(1)\n' > "$C/hooks/$H"
  caso "smoke boccia un hook Python che esce 1" trova "^FAIL  smoke fallito: $H"
  cp "$LAVORO/hook.bak" "$C/hooks/$H"
else
  CASI+=("smoke boccia un hook Python che esce 1 (nessun hook Python in settings.json)"); ESITI+=("ROSSO")
fi

caso "la copia pulita non ha FAIL" manca '^FAIL'

echo
n=${#CASI[@]}; ko=0; i=0
while [ $i -lt $n ]; do
  printf "  %-6s %s\n" "${ESITI[$i]}" "${CASI[$i]}"
  [ "${ESITI[$i]}" = "ROSSO" ] && ko=$((ko+1))
  i=$((i+1))
done
echo
echo "  totale casi: $n · rossi: $ko"
[ "$ko" -eq 0 ] || exit 1
