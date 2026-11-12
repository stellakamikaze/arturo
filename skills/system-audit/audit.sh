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
# Il codice di Arturo sta due cartelle sopra questo script: ~/.claude col clone, la cartella del plugin
# col plugin (review del 7/11/2026, finding 73). ~/.claude resta la cartella dei settings e dei dati.
CODICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
[[ -n "$CODICE" ]] || CODICE="$CLAUDE_DIR"
# Col plugin gli hook stanno in hooks/hooks.json del plugin, non nei settings della persona.
PLUGIN_HOOKS=""
if [[ "$(cd "$CODICE" && pwd -P)" != "$(cd "$CLAUDE_DIR" 2>/dev/null && pwd -P)" && -f "$CODICE/hooks/hooks.json" ]]; then
  PLUGIN_HOOKS="$CODICE/hooks/hooks.json"
fi
# Le cartelle da guardare per agenti, skill e comandi: il codice, e ~/.claude se è un'altra cartella.
radici=("$CODICE")
[[ -n "$PLUGIN_HOOKS" ]] && radici+=("$CLAUDE_DIR")
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
  # Il blocco Python scrive su file: dentro <(...) bash 3.2, il bash di macOS, conta gli apici del heredoc
  # e lo script non si legge più (segnalazione n. 68).
  comandi_file=$(mktemp "${TMPDIR:-/tmp}/audit-comandi.XXXXXX")
  python3 - "$SETTINGS" "$PLUGIN_HOOKS" > "$comandi_file" 2>/dev/null <<'PY' || true
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    settings = json.load(source)
fonti = [settings]
if sys.argv[2]:
    with open(sys.argv[2], encoding="utf-8") as source:
        fonti.append(json.load(source))
for fonte in fonti:
    for blocks in fonte.get("hooks", {}).values():
        for block in blocks:
            for hook in block.get("hooks", []):
                command = hook.get("command")
                if isinstance(command, str):
                    print(command)
status = settings.get("statusLine")
if isinstance(status, dict) and isinstance(status.get("command"), str):
    print(status["command"])
PY
  while IFS= read -r hook_command; do
    [[ -n "$hook_command" ]] && hook_commands+=("$hook_command")
  done < "$comandi_file"
  rm -f "$comandi_file"
fi

hook_files=()
for command in "${hook_commands[@]}"; do
  # Come sopra: il heredoc fuori da <(...), perché un apostrofo nel commento rompeva bash 3.2 (n. 68).
  script_file=$(mktemp "${TMPDIR:-/tmp}/audit-script.XXXXXX")
  python3 - "$command" "$CLAUDE_DIR" "$CODICE" > "$script_file" <<'PY' || true
import os
import re
import shlex
import sys
comando, orsa, codice = sys.argv[1], sys.argv[2], sys.argv[3]
# Col plugin il codice sta in ${CLAUDE_PLUGIN_ROOT}, e la barra lo legge dal puntatore che l'avvio
# riscrive: si risolvono prima di leggere il comando. Un puntatore che manca resta un hook mancante.
comando = comando.replace("${CLAUDE_PLUGIN_ROOT}", codice)
try:
    with open(os.path.join(orsa, "arturo", "radice"), encoding="utf-8") as src:
        puntatore = src.read().strip()
except OSError:
    puntatore = os.path.join(orsa, "arturo", "radice (puntatore mancante)")
comando = re.sub(r"""\$\(cat\s+["']?(?:~|\$HOME|\$\{HOME\})/\.claude/arturo/radice["']?(?:\s+2>\s*/dev/null)?\s*\)""",
                 lambda _: puntatore, comando)
# shlex toglie le virgolette e tiene insieme i path con spazi. punctuation_chars stacca ; && | dal
# path: con `... statusline.js; echo ...` (barra senza node, 19/10/2026) il token era "statusline.js;"
# e il controllo saltava in silenzio.
try:
    lex = shlex.shlex(comando, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    tokens = list(lex)
except ValueError:
    print("::parse-error::")
    raise SystemExit(0)
for i, token in enumerate(tokens):
    if not re.search(r"\.(?:py|sh|js)$", token):
        continue
    # `test -f X || python3 Y` (ripiego del clone quando il plugin non ha il file): X è la condizione,
    # lo script lanciato è Y. Contarlo dava un FAIL su un hook che parte (11/11/2026).
    if tokens[max(i - 2, 0):i] in (["test", "-f"], ["[", "-f"], ["test", "-e"], ["[", "-e"]):
        continue
    token = re.sub(r"^(?:~|\$HOME|\$\{HOME\})/\.claude/", lambda _: orsa + "/", token)
    print(os.path.expanduser(token))
PY
  while IFS= read -r script; do
    [[ -z "$script" ]] && continue
    script="${script%$'\r'}"
    if [[ "$script" == "::parse-error::" ]]; then
      ko "comando hook non interpretabile: $command"
      continue
    fi
    hook_files+=("$script")
    if [[ -f "$script" ]]; then
      ok "hook diretto: $(basename "$script")"
    else
      ko "hook diretto mancante: $script"
    fi
  done < "$script_file"
  rm -f "$script_file"
done

# Il dispatcher richiama guardie transitive: il settings da solo non le mostra.
dispatcher="$CODICE/hooks/bash-dispatcher.sh"
if [[ -f "$dispatcher" ]]; then
  while IFS= read -r guard; do
    [[ -z "$guard" ]] && continue
    if [[ -f "$CODICE/hooks/$guard" ]]; then
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

agent_dirs=()
for r in "${radici[@]}"; do [[ -d "$r/agents" ]] && agent_dirs+=("$r/agents"); done
if [[ ${#agent_dirs[@]} -gt 0 ]] && python3 - "${agent_dirs[@]}" <<'PY' >/dev/null 2>&1
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
for path in [p for d in sys.argv[1:] for p in Path(d).glob("*.md")]:
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
# Un mod rotto ha il suo messaggio: "SKILL.md mancante" porterebbe ad aggiungere una SKILL.md al mod.
skills_rc=1
skill_rotte=""
skill_dirs=()
for r in "${radici[@]}"; do [[ -d "$r/skills" ]] && skill_dirs+=("$r/skills"); done
if [[ ${#skill_dirs[@]} -gt 0 ]]; then
  skills_rc=0
  skill_rotte_file=$(mktemp "${TMPDIR:-/tmp}/audit-skill.XXXXXX")
  ARTURO_AUDIT_MODULI="$PLUGIN_HOOKS" python3 - "${skill_dirs[@]}" <<'PY' >"$skill_rotte_file" 2>/dev/null || skills_rc=$?
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
import os
import re

# Col plugin il mod di Arturo non ha .claude-plugin: lo porta il plugin, sotto "modules" di hooks/hooks.json.
moduli = set()
if os.environ.get("ARTURO_AUDIT_MODULI"):
    try:
        with open(os.environ["ARTURO_AUDIT_MODULI"], encoding="utf-8") as src:
            for m in json.load(src).get("modules", []):
                trovato = re.fullmatch(r"\.\./skills/([^/]+)/hooks/register\.tsx", m)
                if trovato:
                    moduli.add(trovato.group(1))
    except (OSError, ValueError):
        pass


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
for directory in [d for radice in sys.argv[1:] for d in Path(radice).iterdir()]:
    # synced/ la tiene Claude Code per le skill di claude.ai: ha le sue cartelle, non un SKILL.md
    # Una cartella nascosta (.trash, che Claude Code lascia in skills/) non è una skill (11/11/2026).
    if not directory.is_dir() or directory.name in ("shared", "synced") or directory.name.startswith("."):
        continue
    if directory.name in moduli and not (directory / "SKILL.md").exists():
        mod_rotto = mod_rotto or not (directory / "hooks" / "register.tsx").is_file()
    elif (directory / ".claude-plugin" / "plugin.json").is_file():
        mod_rotto = mod_rotto or not mod_valido(directory)
    else:
        try:
            valida = skill_valida(directory)
        except Exception:
            valida = False
        if not valida:
            print(directory.name)
        skill_rotta = skill_rotta or not valida
sys.exit((1 if skill_rotta else 0) + (3 if mod_rotto else 0))
PY
  skill_rotte=$(tr '\n' ' ' < "$skill_rotte_file" | sed 's/ *$//')
  rm -f "$skill_rotte_file"
fi
case "$skills_rc" in
  0) ok "skill: directory e frontmatter YAML validi" ;;
  3) ko "mod: .claude-plugin/plugin.json non valido (name diverso dalla cartella oppure hooks/hooks.json mancante)" ;;
  4) ko "skill: SKILL.md mancante oppure frontmatter non valido${skill_rotte:+ ($skill_rotte)}"
     ko "mod: .claude-plugin/plugin.json non valido (name diverso dalla cartella oppure hooks/hooks.json mancante)" ;;
  *) ko "skill: SKILL.md mancante oppure frontmatter non valido${skill_rotte:+ ($skill_rotte)}" ;;
esac

[[ -f "$CODICE/README.md" ]] && ok "README pubblico presente" || ko "README pubblico mancante"

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
# Le righe di storia ("rimosso", "archiviata", "ha assorbito"…) e gli indirizzi web non contano.
# Il blocco Python scrive su file: dentro $(...) bash 3.2 conta gli apici del heredoc e si rompe.
ghost_file=$(mktemp "${TMPDIR:-/tmp}/audit-fantasmi.XXXXXX")
python3 - "$CLAUDE_DIR" "${radici[@]}" > "$ghost_file" 2>/dev/null <<'PY'
import glob
import os
import re
import sys

# La cartella della persona (CLAUDE.md), poi le radici: il codice e, col plugin, anche ~/.claude.
ORSA, RADICI = sys.argv[1], sys.argv[2:]


def trova(modello, **kw):
    return [p for H in RADICI for p in glob.glob(H + modello, **kw)]


skills = {os.path.basename(os.path.dirname(p)) for p in trova("/skills/*/SKILL.md")}
cmds = {os.path.basename(p)[:-3] for p in trova("/commands/*.md")}
wfs = {os.path.basename(p)[:-3] for p in trova("/workflows/*.js")}
# I comandi registrati dai mod si leggono dal sorgente: un mod tolto fa tornare fantasma la sua menzione.
modcmds = set()
# Dal 3/11/2026 un mod ha le sue parti in hooks/<parte>/: si cerca a ogni profondità sotto hooks/.
for f in trova("/skills/*/hooks/**/*.ts*", recursive=True) + trova("/mods/*/hooks/**/*.ts*", recursive=True):
    with open(f, encoding="utf-8", errors="ignore") as src:
        modcmds |= set(re.findall(r"command\.register\(\{\s*name:\s*'([^']+)'", src.read()))
# Comandi di Claude Code: non stanno su disco.
NATIVE = {"add-dir", "agents", "artifacts", "bg", "btw", "bug", "clear", "code-review", "compact", "config",
          "context", "cost", "debug", "doctor", "effort", "exit", "export", "fast", "feedback", "goal", "help",
          "hooks", "ide", "init", "insights", "install-github-app", "login", "logout", "loop", "mcp",
          "memory", "model", "output-style", "permissions", "plan", "plugin", "plugins",
          "privacy-settings", "release-notes", "remember", "resume", "review", "rewind", "schedule",
          "security-review", "simplify", "status", "statusline", "terminal-setup", "todos", "upgrade",
          "usage", "verify", "vim", "workflows"}
# Parole che compaiono come `/parola` senza essere comandi: path e rotte.
NOTCMD = {"api", "bin", "dev", "etc", "graphql", "home", "opt", "proc", "root", "tmp", "usr", "var",
          "well-known", "xargs"}
# Skill che la persona installa dall'autore, fuori dal repo (/setup fase 8c, 16/10/2026; hallmark dal 30/10/2026).
UPSTREAM = {"impeccable", "hallmark"}
known = skills | cmds | wfs | modcmds | NATIVE | NOTCMD | UPSTREAM
STORICO = re.compile(r"rimoss|deprecat|eliminat|dismess|assorbit|archiviat|sostituisc|precedent|"
                     r"\bfus[oiae]\b|\bvecchi[oi]\b|\bex\b|non esiste|retrocompatibilit", re.I)
ENDPOINT = re.compile(r"endpoint|\broute\b|\bAPI\b|\bGET\b|\bPOST\b|https?://|:\d{4}", re.I)
# Il backtick d'apertura non segue una lettera: in "`nc`/altro" il backtick chiude, non apre.
PAT = re.compile(r"(?<![A-Za-z0-9_])`/([a-z][a-z0-9:_-]{1,30})(?:\s[^`]*)?`")
# Un percorso di pagina web ("vista `/gare` su uf-dashboard", "la pagina `/roadmap/`") non è un comando.
# Conta solo la parola subito prima: un comando vero più avanti nella stessa riga resta controllato.
PAGINA = re.compile(r"\b(?:vista|pagina|rotta|indirizzo|url|sezione)\s*$", re.I)
docs = [(ORSA, "CLAUDE.md")] + [(H, "README.md") for H in RADICI] + sorted(
    (H, os.path.relpath(p, H).replace(os.sep, "/")) for H in RADICI for p in glob.glob(H + "/commands/*.md")
    + glob.glob(H + "/skills/*/SKILL.md") + glob.glob(H + "/agents/*.md") + glob.glob(H + "/shared/*.md"))
tot = 0
for H, doc in dict.fromkeys(docs):
    fp = os.path.join(H, doc)
    if not os.path.isfile(fp):
        continue
    with open(fp, encoding="utf-8", errors="ignore") as src:
        righe = src.read().split("\n")
    for i, line in enumerate(righe, 1):
        if STORICO.search(line) or ENDPOINT.search(line):
            continue
        for m in PAT.finditer(line):
            nome = m.group(1)
            if PAGINA.search(line[:m.start()]):
                continue
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
for f in "$CODICE"/skills/*/SKILL.md "$CODICE"/commands/*.md; do
  [[ -f "$f" ]] || continue
  sz=$(wc -c < "$f" | tr -d ' ')
  if [[ "$sz" -gt 30000 ]]; then
    warning "${f#$CODICE/} pesa $((sz / 1024)) KB (tetto 30 KB): sposta in references/ le parti lette solo in un caso"
  fi
done

# Plugin installati ma non attivi in settings.json: solo il report, con il comando per toglierli.
stale_sh="$CODICE/bin/cleanup-stale-plugins.sh"
if [[ -f "$stale_sh" ]]; then
  stale_out=$(bash "$stale_sh" --dry-run </dev/null 2>&1)
  stale_rc=$?
  stale_lista=$(printf '%s\n' "$stale_out" | sed -n 's/^  - //p' | paste -sd ',' - | sed 's/,/, /g')
  if [[ $stale_rc -ne 0 ]]; then
    warning "plugin: cleanup-stale-plugins.sh --dry-run uscito $stale_rc: $(printf '%s\n' "$stale_out" | tail -1)"
  elif [[ -n "$stale_lista" ]]; then
    warning "plugin installati ma non attivi: $stale_lista -> bash $stale_sh --yes"
  else
    ok "plugin: tutti gli installati sono attivi"
  fi
fi

# Omonimi col plugin (strati F5, 5/11/2026): una skill, un comando o uno stile della persona con lo stesso
# nome di uno di Arturo prende il nome nudo. Voluto si dichiara in personale/sostituzioni.txt; non dichiarato
# è una skill di Arturo che la persona non vedrà. Il codice sta due cartelle sopra questo script, nel clone
# come nel plugin. Nel clone le skill sono le stesse e il controllo tace.
personale_py="$CODICE/bin/personale.py"
if [[ -f "$personale_py" ]] && command -v python3 >/dev/null 2>&1; then
  omonimi_out=$(ARTURO_RADICE="$CLAUDE_DIR" python3 "$personale_py" omonimi 2>&1)
  omonimi_rc=$?
  if [[ $omonimi_rc -eq 0 ]]; then
    ok "omonimi: $(printf '%s\n' "$omonimi_out" | head -1)"
  else
    while IFS= read -r riga; do
      case "$riga" in "OMONIMO NON DICHIARATO:"*|"DICHIARATO SENZA OMONIMO:"*) warning "$riga" ;; esac
    done < <(printf '%s\n' "$omonimi_out")
  fi
fi

echo "=== System Audit ==="
printf '%s\n' "${report[@]}"
printf 'Totali: PASS=%s WARN=%s FAIL=%s\n' "$pass" "$warn" "$fail"
if $STRICT && [[ $fail -gt 0 ]]; then
  exit 1
fi
