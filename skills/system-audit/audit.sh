#!/usr/bin/env bash
# system-audit: verifica isolata della superficie distribuita ~/.claude.
set -uo pipefail

STRICT=false
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=true
elif [[ $# -gt 0 ]]; then
  echo "Uso: $0 [--strict]" >&2
  exit 2
fi

CLAUDE_DIR="${HOME}/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"
pass=0
warn=0
fail=0
report=()

ok() { report+=("PASS  $*"); pass=$((pass + 1)); }
warning() { report+=("WARN  $*"); warn=$((warn + 1)); }
ko() { report+=("FAIL  $*"); fail=$((fail + 1)); }

if ! command -v python3 >/dev/null 2>&1; then
  ko "python3 mancante"
elif ! python3 -c 'import yaml' >/dev/null 2>&1; then
  warning "PyYAML assente: il frontmatter si controlla con un parser ridotto (bastano name e description)"
else
  ok "parser YAML disponibile"
fi

if [[ ! -f "$SETTINGS" ]]; then
  ko "settings.json mancante"
elif python3 - "$SETTINGS" <<'PY' >/dev/null 2>&1
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    value = json.load(source)
if not isinstance(value, dict):
    raise TypeError("settings root non mapping")
PY
then
  ok "settings.json: JSON valido"
else
  ko "settings.json: JSON malformato o root non mapping"
fi

hook_commands=()
if [[ -f "$SETTINGS" ]] && command -v python3 >/dev/null 2>&1; then
  # while read al posto di mapfile: bash 3.2 (il bash di sistema su macOS) non ha mapfile,
  # e senza questo l'array resta vuoto e l'audit non controlla piu' nessun hook.
  while IFS= read -r hook_command; do
    [[ -n "$hook_command" ]] && hook_commands+=("$hook_command")
  done < <(python3 - "$SETTINGS" <<'PY' 2>/dev/null
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    settings = json.load(source)
for blocks in settings.get("hooks", {}).values():
    for block in blocks:
        for hook in block.get("hooks", []):
            command = hook.get("command")
            if isinstance(command, str):
                print(command)
status = settings.get("statusLine")
if isinstance(status, dict) and isinstance(status.get("command"), str):
    print(status["command"])
PY
)
fi

hook_files=()
for command in "${hook_commands[@]}"; do
  while IFS= read -r script; do
    [[ -z "$script" ]] && continue
    script="${script%$'\r'}"
    if [[ "$script" == "::parse-error::" ]]; then
      ko "comando hook non interpretabile: $command"
      continue
    fi
    if [[ "$script" == *".claude/"* ]]; then
      script="$CLAUDE_DIR/${script#*.claude/}"
    fi
    script="${script/#\~/$HOME}"
    hook_files+=("$script")
    if [[ -f "$script" ]]; then
      ok "hook diretto: $(basename "$script")"
    else
      ko "hook diretto mancante: $script"
    fi
  done < <(python3 - "$command" <<'PY'
import re
import shlex
import sys
# shlex toglie le virgolette e tiene insieme i path con spazi.
try:
    tokens = shlex.split(sys.argv[1])
except ValueError:
    print("::parse-error::")
    raise SystemExit(0)
print("\n".join(token for token in tokens if re.search(r"\.(?:py|sh|js)$", token)))
PY
)
done

# Il dispatcher richiama guardie transitive: il settings da solo non le mostra.
dispatcher="$CLAUDE_DIR/hooks/bash-dispatcher.sh"
if [[ -f "$dispatcher" ]]; then
  while IFS= read -r guard; do
    [[ -z "$guard" ]] && continue
    if [[ -f "$CLAUDE_DIR/hooks/$guard" ]]; then
      ok "guardia transitiva: $guard"
    else
      ko "guardia transitiva mancante: $guard"
    fi
  done < <(grep -E '^[[:space:]]*\[\[.*run_guard[[:space:]]+[A-Za-z0-9_.-]+' "$dispatcher" | grep -oE 'run_guard[[:space:]]+[A-Za-z0-9_.-]+' | awk '{print $2}' | sort -u)
fi

smoke=0
for script in "${hook_files[@]}"; do
  [[ -f "$script" ]] || continue
  case "$script" in
    *.py) runner=(python3 -B "$script") ;;
    *.js) runner=(node --check "$script") ;;
    *) continue ;;
  esac
  if [[ "$script" == *.py ]]; then
    if command -v timeout >/dev/null 2>&1; then
      printf '{}' | timeout 5 "${runner[@]}" >/dev/null 2>&1
    else
      printf '{}' | "${runner[@]}" >/dev/null 2>&1
    fi
    rc=$?
  else
    "${runner[@]}" >/dev/null 2>&1
    rc=$?
  fi
  smoke=$((smoke + 1))
  if [[ $rc -eq 0 ]]; then
    ok "smoke: $(basename "$script")"
  else
    ko "smoke fallito: $(basename "$script") (rc=$rc)"
  fi
done
[[ $smoke -gt 0 ]] || ko "nessun hook safe per smoke"

if [[ -d "$CLAUDE_DIR/agents" ]] && python3 - "$CLAUDE_DIR/agents" <<'PY' >/dev/null 2>&1
import sys
from pathlib import Path
try:
    import yaml
    carica = yaml.safe_load
except ImportError:
    def carica(testo):
        # Parser ridotto senza PyYAML: chiavi di primo livello, blocchi > e | inclusi.
        valori, chiave = {}, None
        for riga in testo.splitlines():
            if riga[:1] in (" ", "\t"):
                if chiave and riga.strip():
                    valori[chiave] = (valori[chiave] + " " + riga.strip()).strip()
                continue
            if ":" in riga:
                chiave, _, valore = riga.partition(":")
                chiave, valore = chiave.strip(), valore.strip()
                valori[chiave] = "" if valore in (">", "|", ">-", "|-") else valore.strip("\"'")
        return valori
for path in Path(sys.argv[1]).glob("*.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(path)
    frontmatter = text.split("---\n", 2)[1]
    value = carica(frontmatter)
    if not isinstance(value, dict) or not all(isinstance(value.get(key), str) and value[key] for key in ("name", "description")):
        raise ValueError(path)
PY
then
  ok "frontmatter agenti: YAML valido"
else
  ko "frontmatter agenti: YAML non valido o campi mancanti"
fi

# Esito del blocco Python: 0 tutto valido, 1 una skill rotta, 3 un mod rotto, 4 tutti e due.
# Un mod rotto ha il suo messaggio: «SKILL.md mancante» porterebbe ad aggiungere una SKILL.md al mod.
skills_rc=1
if [[ -d "$CLAUDE_DIR/skills" ]]; then
  skills_rc=0
  python3 - "$CLAUDE_DIR/skills" <<'PY' >/dev/null 2>&1 || skills_rc=$?
import sys
from pathlib import Path
try:
    import yaml
    carica = yaml.safe_load
except ImportError:
    def carica(testo):
        # Parser ridotto senza PyYAML: chiavi di primo livello, blocchi > e | inclusi.
        valori, chiave = {}, None
        for riga in testo.splitlines():
            if riga[:1] in (" ", "\t"):
                if chiave and riga.strip():
                    valori[chiave] = (valori[chiave] + " " + riga.strip()).strip()
                continue
            if ":" in riga:
                chiave, _, valore = riga.partition(":")
                chiave, valore = chiave.strip(), valore.strip()
                valori[chiave] = "" if valore in (">", "|", ">-", "|-") else valore.strip("\"'")
        return valori
import json


def mod_valido(directory):
    # Una cartella con .claude-plugin/plugin.json e' un mod di Claude Code (il pannello /dafare),
    # non una skill: niente SKILL.md, ma un manifest valido col nome della cartella e i suoi hook.
    try:
        dati = json.loads((directory / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(dati, dict) and dati.get("name") == directory.name and (directory / "hooks" / "hooks.json").is_file()


def skill_valida(directory):
    skill = directory / "SKILL.md"
    if not skill.is_file():
        return False
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False
    frontmatter = carica(text.split("---\n", 2)[1])
    return isinstance(frontmatter, dict) and all(isinstance(frontmatter.get(key), str) and frontmatter[key] for key in ("name", "description"))


skill_rotta = mod_rotto = False
for directory in Path(sys.argv[1]).iterdir():
    if not directory.is_dir() or directory.name == "shared":
        continue
    if (directory / ".claude-plugin" / "plugin.json").is_file():
        mod_rotto = mod_rotto or not mod_valido(directory)
    else:
        skill_rotta = skill_rotta or not skill_valida(directory)
sys.exit((1 if skill_rotta else 0) + (3 if mod_rotto else 0))
PY
fi
case "$skills_rc" in
  0) ok "skill: directory e frontmatter YAML validi" ;;
  3) ko "mod: .claude-plugin/plugin.json non valido (name diverso dalla cartella oppure hooks/hooks.json mancante)" ;;
  4) ko "skill: SKILL.md mancante oppure frontmatter non valido"
     ko "mod: .claude-plugin/plugin.json non valido (name diverso dalla cartella oppure hooks/hooks.json mancante)" ;;
  *) ko "skill: SKILL.md mancante oppure frontmatter non valido" ;;
esac

[[ -f "$CLAUDE_DIR/README.md" ]] && ok "README pubblico presente" || ko "README pubblico mancante"

if [[ -f "$SETTINGS" ]] && python3 - "$SETTINGS" <<'PY' >/dev/null 2>&1
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    permissions = json.load(source).get("permissions", {})
if not permissions.get("defaultMode"):
    raise ValueError("defaultMode mancante")
if set(permissions.get("allow", ())) & set(permissions.get("deny", ())):
    raise ValueError("permessi sovrapposti")
PY
then
  ok "permessi: defaultMode presente, nessuna sovrapposizione allow/deny"
else
  ko "permessi: defaultMode mancante, pattern sovrapposti o settings non leggibile"
fi

echo "=== System Audit ==="
printf '%s\n' "${report[@]}"
printf 'Totali: PASS=%s WARN=%s FAIL=%s\n' "$pass" "$warn" "$fail"
if $STRICT && [[ $fail -gt 0 ]]; then
  exit 1
fi
