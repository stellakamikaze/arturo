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
caso "gate-yaml: il FAIL delle skill nomina la cartella rotta" trova '^FAIL  skill: .*\(_banco-avvelenato\)$'

printf -- '---\nname: _banco-avvelenato\ndescription: >-\n  Skill sana di prova, con i due punti: dentro un blocco folded.\n---\n# x\n' > "$S/SKILL.md"
caso "gate-yaml passa una skill sana" manca '^FAIL  skill'
rm -rf "$S"

# Claude Code lascia in skills/ la cartella nascosta .trash, senza SKILL.md: non è una skill (11/11/2026).
mkdir -p "$C/skills/.trash/skill-buttata"
printf '# resto di una skill tolta\n' > "$C/skills/.trash/skill-buttata/note.md"
caso "gate-yaml salta una cartella nascosta in skills/" manca '^FAIL  skill'
rm -rf "$C/skills/.trash"

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

printf -- '---\ndescription: banco\n---\nLa dashboard è la superficie di revisione (vista `/pagina-che-non-esiste-mai` su uf-dashboard).\n' > "$K"
caso "gate-fantasma: il percorso di una pagina web non è un comando" manca 'pagina-che-non-esiste-mai'

printf -- '---\ndescription: banco\n---\nApri la pagina `/roadmap/`, poi lancia `/comando-che-non-esiste-mai`.\n' > "$K"
caso "gate-fantasma: dopo una pagina web il comando vero resta controllato" trova '^WARN  commands/_banco.md:4 cita /comando-che-non-esiste-mai'

# Segnalazione 109 (26/11/2026): /rename è un comando di Claude Code, e "pagina web `/x`" è una pagina.
printf -- '---\ndescription: banco\n---\nConta solo il nome dato a mano, con `--name` o `/rename`.\n' > "$K"
caso "gate-fantasma passa /rename di Claude Code" manca '_banco.md.*cita /rename'

printf -- '---\ndescription: banco\n---\nApri la pagina web `/pagina-che-non-esiste-mai` nel browser.\n' > "$K"
caso "gate-fantasma: la pagina web scritta con la barra non è un comando" manca 'pagina-che-non-esiste-mai'

{ printf -- '---\ndescription: banco\n---\n'; i=0; while [ $i -lt 700 ]; do printf 'riga di riempimento per superare il tetto di peso del corpo.\n'; i=$((i+1)); done; } > "$K"
caso "peso dei corpi: un comando oltre 30 KB" trova '^WARN  commands/_banco.md pesa [0-9]+ KB'

# Segnalazione 109: 30 KB sono 30720 byte. Un corpo da circa 30200 byte sta sotto il tetto.
{ printf -- '---\ndescription: banco\n---\n'; i=0; while [ $i -lt 495 ]; do printf 'riga di riempimento per superare il tetto di peso del corpo.\n'; i=$((i+1)); done; } > "$K"
caso "peso dei corpi: un comando da 29 KB sta sotto il tetto di 30 KB" manca '_banco.md pesa'
rm -f "$K"

mkdir -p "$C/plugins"
printf '{"plugins": {"pluginfinto@banco": [{"scope": "user"}]}}\n' > "$C/plugins/installed_plugins.json"
caso "plugin installato che settings.json non nomina" trova '^WARN  plugin installati che settings.json non nomina più: pluginfinto@banco'
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

# `test -f X || python3 Y`: X è la condizione del ripiego, lo script lanciato è Y (11/11/2026).
# hook_extra <comando>: aggiunge un hook SessionStart a una copia di settings.json.
cp "$C/settings.json" "$LAVORO/settings.bak"
hook_extra() {
  python3 - "$LAVORO/settings.bak" "$C/settings.json" "$1" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
d.setdefault("hooks", {}).setdefault("SessionStart", []).append({"hooks": [{"type": "command", "command": sys.argv[3]}]})
json.dump(d, open(sys.argv[2], "w", encoding="utf-8"))
PY
}
if [ -n "$H" ] && [ -f "$C/hooks/$H" ]; then
  hook_extra "test -f \"\$HOME/.claude/hooks/condizione-che-manca.py\" || python3 \"\$HOME/.claude/hooks/$H\""
  caso "hook diretti: il file di test -f è la condizione, non l'hook" manca 'condizione-che-manca'
  hook_extra "test -f \"\$HOME/.claude/hooks/$H\" || python3 \"\$HOME/.claude/hooks/lanciato-che-manca.py\""
  caso "hook diretti: dopo test -f lo script lanciato resta controllato" trova '^FAIL  hook diretto mancante: .*lanciato-che-manca\.py'
else
  CASI+=("hook diretti con test -f (nessun hook Python in settings.json)"); ESITI+=("ROSSO")
fi
cp "$LAVORO/settings.bak" "$C/settings.json"

# Le skill della persona senza "Finito quando" e gli attrezzi citati e assenti (21/11/2026, #6277): solo WARN.
caso "skill tue: le skill di Arturo non contano come skill senza Finito quando" manca 'skill tue senza'
V="$C/skills/banco-vecchia"
mkdir -p "$V"
printf -- '---\nname: banco-vecchia\ndescription: Skill della persona nata prima delle due sezioni.\n---\n# Lettera\n\n## Che cosa deve uscire\n\nUna lettera.\n' > "$V/SKILL.md"
caso "skill tue: una skill senza Finito quando dà un WARN col nome" trova '^WARN  1 skill tue senza "Finito quando": banco-vecchia '
caso "skill tue: una skill senza Finito quando non dà mai FAIL" manca '^FAIL'
V2="$C/skills/banco-altra"
mkdir -p "$V2"
printf -- '---\nname: banco-altra\ndescription: Seconda skill della persona, con la lista vuota.\n---\n# Conti\n\n## Finito quando\n\n## Attrezzi\n' > "$V2/SKILL.md"
caso "skill tue: due skill stanno in un WARN solo" trova '^WARN  2 skill tue senza "Finito quando": banco-altra, banco-vecchia '
rm -rf "$V2"
printf -- '---\nname: banco-vecchia\ndescription: Skill della persona con le due sezioni.\n---\n# Lettera\n\n## Finito quando\n\n- La data è in alto?\n\n## Attrezzi\n\n- `conti.py`: somma le righe, a ogni lettera.\n- `modello-che-manca.docx`: il modello della lettera.\n- Il sito https://esempio.it/pagina.html resta fuori.\n' > "$V/SKILL.md"
printf 'print(1)\n' > "$V/conti.py"
caso "attrezzi: un file citato e assente dà un WARN" trova '^WARN  skill banco-vecchia: "Attrezzi" cita modello-che-manca\.docx, che non c'"'"'è$'
caso "attrezzi: un file citato e presente e un indirizzo web passano" manca 'cita (conti\.py|.*pagina\.html)'
caso "skill tue: con Finito quando il WARN riassuntivo sparisce" manca 'skill tue senza'
rm -f "$V/SKILL.md" "$V/conti.py"; rmdir "$V"

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
