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
  ko "PyYAML mancante: installa la dipendenza documentata in README"
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
import yaml
for path in Path(sys.argv[1]).glob("*.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(path)
    frontmatter = text.split("---\n", 2)[1]
    value = yaml.safe_load(frontmatter)
    if not isinstance(value, dict) or not all(isinstance(value.get(key), str) and value[key] for key in ("name", "description")):
        raise ValueError(path)
PY
then
  ok "frontmatter agenti: YAML valido"
else
  ko "frontmatter agenti: YAML non valido o campi mancanti"
fi

if [[ -d "$CLAUDE_DIR/skills" ]] && python3 - "$CLAUDE_DIR/skills" <<'PY' >/dev/null 2>&1
import sys
from pathlib import Path
import yaml
for directory in Path(sys.argv[1]).iterdir():
    if not directory.is_dir() or directory.name == "shared":
        continue
    skill = directory / "SKILL.md"
    if not skill.is_file():
        raise FileNotFoundError(skill)
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(skill)
    frontmatter = yaml.safe_load(text.split("---\n", 2)[1])
    if not isinstance(frontmatter, dict) or not all(isinstance(frontmatter.get(key), str) and frontmatter[key] for key in ("name", "description")):
        raise ValueError(skill)
PY
then
  ok "skill: directory e frontmatter YAML validi"
else
  ko "skill: SKILL.md mancante oppure frontmatter non valido"
fi

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
