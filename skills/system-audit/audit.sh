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
  # Ogni chiamata `run_guard X` (anche dentro un blocco if) e ogni script chiamato per percorso
  # (`python3 "$HOME/.claude/hooks/X"`). Le righe di commento non contano.
  done < <(grep -vE '^[[:space:]]*#' "$dispatcher" \
    | grep -oE 'run_guard[[:space:]]+[A-Za-z0-9_.-]+\.(py|sh|js)|\.claude/hooks/[A-Za-z0-9_.-]+\.(py|sh|js)' \
    | sed -E 's#^run_guard[[:space:]]+##; s#^\.claude/hooks/##' | sort -u)
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

# Comandi fantasma: un documento vivo cita come vivo uno slash-comando che non esiste più
# (nessuna skill, nessun comando, nessun mod lo registra). La mappa non deve scollarsi dal territorio.
# Le righe di storia («rimosso», «archiviata», «ha assorbito»…) e gli indirizzi web non contano.
# Il blocco Python scrive su file: dentro $(...) bash 3.2 conta gli apici del heredoc e si rompe.
ghost_file=$(mktemp "${TMPDIR:-/tmp}/audit-fantasmi.XXXXXX")
python3 - "$CLAUDE_DIR" > "$ghost_file" 2>/dev/null <<'PY'
import glob
import os
import re
import sys

H = sys.argv[1]
skills = {os.path.basename(os.path.dirname(p)) for p in glob.glob(H + "/skills/*/SKILL.md")}
cmds = {os.path.basename(p)[:-3] for p in glob.glob(H + "/commands/*.md")}
wfs = {os.path.basename(p)[:-3] for p in glob.glob(H + "/workflows/*.js")}
# I comandi registrati dai mod si leggono dal sorgente: un mod tolto fa tornare fantasma la sua menzione.
modcmds = set()
for f in glob.glob(H + "/skills/*/hooks/*.ts*") + glob.glob(H + "/mods/*/hooks/*.ts*"):
    with open(f, encoding="utf-8", errors="ignore") as src:
        modcmds |= set(re.findall(r"command\.register\(\{\s*name:\s*'([^']+)'", src.read()))
# Comandi di Claude Code: non stanno su disco.
NATIVE = {"add-dir", "agents", "artifacts", "btw", "bug", "clear", "code-review", "compact", "config",
          "context", "cost", "debug", "doctor", "effort", "exit", "export", "fast", "feedback", "goal", "help",
          "hooks", "ide", "init", "insights", "install-github-app", "login", "logout", "loop", "mcp",
          "memory", "model", "output-style", "permissions", "plan", "plugin", "plugins",
          "privacy-settings", "release-notes", "remember", "resume", "review", "rewind", "schedule",
          "security-review", "simplify", "status", "statusline", "terminal-setup", "todos", "upgrade",
          "usage", "verify", "vim", "workflows"}
# Parole che compaiono come `/parola` senza essere comandi: path e rotte.
NOTCMD = {"api", "bin", "dev", "etc", "graphql", "home", "opt", "proc", "root", "tmp", "usr", "var",
          "well-known", "xargs"}
known = skills | cmds | wfs | modcmds | NATIVE | NOTCMD
STORICO = re.compile(r"rimoss|deprecat|eliminat|dismess|assorbit|archiviat|sostituisc|precedent|"
                     r"\bfus[oiae]\b|\bvecchi[oi]\b|\bex\b|non esiste|retrocompatibilit", re.I)
ENDPOINT = re.compile(r"endpoint|\broute\b|\bAPI\b|\bGET\b|\bPOST\b|https?://|:\d{4}", re.I)
# Il backtick d'apertura non segue una lettera: in «`nc`/altro» il backtick chiude, non apre.
PAT = re.compile(r"(?<![A-Za-z0-9_])`/([a-z][a-z0-9:_-]{1,30})(?:\s[^`]*)?`")
docs = ["CLAUDE.md", "README.md"] + sorted(
    os.path.relpath(p, H).replace(os.sep, "/") for p in glob.glob(H + "/commands/*.md") + glob.glob(H + "/skills/*/SKILL.md")
    + glob.glob(H + "/agents/*.md") + glob.glob(H + "/shared/*.md"))
tot = 0
for doc in docs:
    fp = os.path.join(H, doc)
    if not os.path.isfile(fp):
        continue
    with open(fp, encoding="utf-8", errors="ignore") as src:
        righe = src.read().split("\n")
    for i, line in enumerate(righe, 1):
        if STORICO.search(line) or ENDPOINT.search(line):
            continue
        for nome in PAT.findall(line):
            if nome not in known:
                print("WARN|%s:%d cita /%s, che non esiste (nessuna skill, comando o mod)" % (doc, i, nome))
                tot += 1
print("COUNT|%d" % tot)
PY
ghost_report=$(cat "$ghost_file")
rm -f "$ghost_file"
ghost_n=$(printf '%s\n' "$ghost_report" | sed -n 's/^COUNT|//p')
if [[ -z "$ghost_n" ]]; then
  warning "comandi fantasma: controllo non eseguito (python3 non ha risposto)"
elif [[ "$ghost_n" -eq 0 ]]; then
  ok "documentazione: nessuno slash-comando citato senza una skill, un comando o un mod"
else
  while IFS='|' read -r livello messaggio; do
    [[ "$livello" == WARN ]] && warning "$messaggio"
  done < <(printf '%s\n' "$ghost_report")
fi

# Peso dei corpi: il corpo di una skill o di un comando entra intero nel contesto a ogni uso.
# Sopra soglia, le parti lette solo in un caso vanno in un file a parte nella stessa skill.
for f in "$CLAUDE_DIR"/skills/*/SKILL.md "$CLAUDE_DIR"/commands/*.md; do
  [[ -f "$f" ]] || continue
  sz=$(wc -c < "$f" | tr -d ' ')
  if [[ "$sz" -gt 30000 ]]; then
    warning "${f#$CLAUDE_DIR/} pesa $((sz / 1024)) KB (tetto 30 KB): sposta in references/ le parti lette solo in un caso"
  fi
done

# Plugin installati ma non attivi in settings.json: solo il report, con il comando per toglierli.
stale_sh="$CLAUDE_DIR/bin/cleanup-stale-plugins.sh"
if [[ -f "$stale_sh" ]]; then
  stale_out=$(bash "$stale_sh" --dry-run </dev/null 2>&1)
  stale_rc=$?
  stale_lista=$(printf '%s\n' "$stale_out" | sed -n 's/^  - //p' | paste -sd ',' - | sed 's/,/, /g')
  if [[ $stale_rc -ne 0 ]]; then
    warning "plugin: cleanup-stale-plugins.sh --dry-run uscito $stale_rc: $(printf '%s\n' "$stale_out" | tail -1)"
  elif [[ -n "$stale_lista" ]]; then
    warning "plugin installati ma non attivi: $stale_lista -> bash ~/.claude/bin/cleanup-stale-plugins.sh --yes"
  else
    ok "plugin: tutti gli installati sono attivi"
  fi
fi

echo "=== System Audit ==="
printf '%s\n' "${report[@]}"
printf 'Totali: PASS=%s WARN=%s FAIL=%s\n' "$pass" "$warn" "$fail"
if $STRICT && [[ $fail -gt 0 ]]; then
  exit 1
fi
