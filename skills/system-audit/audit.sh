#!/usr/bin/env bash
# system-audit: integrity check di ~/.claude/.
# Report-only, exit 0 sempre (anche con FAIL: gli errori vanno nel report).
# Usage: bash ~/.claude/skills/system-audit/audit.sh

set -u
CLAUDE_DIR="${HOME}/.claude"
SETTINGS="${CLAUDE_DIR}/settings.json"

pass=0
warn=0
fail=0
report=()

ok()   { report+=("PASS  $*"); pass=$((pass+1)); }
warning() { report+=("WARN  $*"); warn=$((warn+1)); }
ko()   { report+=("FAIL  $*"); fail=$((fail+1)); }

# 1. settings.json valid
if [ -f "$SETTINGS" ]; then
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SETTINGS" 2>/dev/null; then
    ok "settings.json: JSON valido"
  else
    ko "settings.json: JSON malformato → \`python3 -c \"import json; json.load(open('$SETTINGS'))\"\` per diagnosi"
  fi
else
  ko "settings.json: file mancante in $SETTINGS"
fi

# 2. Hooks-on-disk
if [ -f "$SETTINGS" ]; then
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    # Estrai il path script dal command (es. "bash ~/.claude/hooks/foo.sh", "python3 ~/.claude/hooks/bar.py", "node ...")
    script=$(echo "$cmd" | awk '{
      for (i=1; i<=NF; i++) {
        if ($i ~ /\.(sh|py|js)$/ || $i ~ /\.(sh|py|js)[[:space:]]/) { print $i; exit }
      }
    }')
    [ -z "$script" ] && continue
    # Espandi tilde
    script_expanded="${script/#\~/$HOME}"
    if [ ! -f "$script_expanded" ]; then
      ko "hook mancante: $script (referenziato in settings.json)"
    elif [ ! -x "$script_expanded" ] && [[ "$script_expanded" != *.js ]]; then
      warning "hook non eseguibile: $script (chmod +x $script_expanded)"
    else
      ok "hook OK: $(basename "$script_expanded")"
    fi
  done < <(python3 -c "
import json, sys
try:
    cfg = json.load(open('$SETTINGS'))
except Exception:
    sys.exit(0)
for evt, blocks in cfg.get('hooks', {}).items():
    for blk in blocks:
        for h in blk.get('hooks', []):
            cmd = h.get('command', '')
            if cmd: print(cmd)
")
fi

# 2b. Hook smoke test — ogni hook non deve crashare su input JSON vuoto (timeout 3s).
# Un hook che va in traceback fallisce aperto (rc!=0 non gestito) e potrebbe non
# proteggere nulla: qui si verifica che regga `{}` senza esplodere.
if [ -f "$SETTINGS" ]; then
  smoke_fail=0
  smoke_run=0
  # `timeout` non esiste su macOS di default (è `gtimeout` da coreutils). Se manca
  # nessuno dei due, si esegue senza timeout: gli hook hanno già un alarm interno.
  if command -v timeout >/dev/null 2>&1; then TO="timeout 3"
  elif command -v gtimeout >/dev/null 2>&1; then TO="gtimeout 3"
  else TO=""; fi
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    script=$(echo "$cmd" | awk '{for(i=1;i<=NF;i++){if($i ~ /\.(sh|py|js)$/){print $i; exit}}}')
    [ -z "$script" ] && continue
    script_expanded="${script/#\~/$HOME}"
    [ -f "$script_expanded" ] || continue
    # Solo guard/scanner .py e .js: sono puri su input vuoto. Gli hook .sh di
    # lifecycle (session-start/end, notifier) hanno side-effect e NON vanno
    # eseguiti in un audit report-only.
    case "$script_expanded" in
      *.py) runner="python3" ;;
      *.js) runner="node" ;;
      *) continue ;;
    esac
    smoke_run=$((smoke_run+1))
    err=$(echo '{}' | $TO "$runner" "$script_expanded" 2>&1 >/dev/null)
    rc=$?
    if [ "$rc" -eq 124 ]; then
      ko "hook smoke: $(basename "$script_expanded") va in timeout su input vuoto"
      smoke_fail=$((smoke_fail+1))
    elif echo "$err" | grep -qiE 'Traceback|SyntaxError|command not found|Cannot find module'; then
      ko "hook smoke: $(basename "$script_expanded") crasha su input vuoto → $(echo "$err" | tail -1)"
      smoke_fail=$((smoke_fail+1))
    fi
  done < <(python3 -c "
import json, sys
try:
    cfg = json.load(open('$SETTINGS'))
except Exception:
    sys.exit(0)
for evt, blocks in cfg.get('hooks', {}).items():
    for blk in blocks:
        for h in blk.get('hooks', []):
            cmd = h.get('command', '')
            if cmd: print(cmd)
")
  if [ "$smoke_fail" -eq 0 ] && [ "$smoke_run" -gt 0 ]; then
    ok "hook smoke test: $smoke_run hook reggono input vuoto senza crash"
  fi
fi

# 3. Agent frontmatter
agent_count=0
agent_issues=0
if [ -d "$CLAUDE_DIR/agents" ]; then
  for f in "$CLAUDE_DIR/agents"/*.md; do
    [ -f "$f" ] || continue
    [[ "$(basename "$f")" == _* ]] && continue
    agent_count=$((agent_count+1))
    if ! head -10 "$f" | grep -q "^name:"; then
      ko "agent $(basename "$f"): manca 'name:' nel frontmatter"
      agent_issues=$((agent_issues+1))
    fi
    if ! head -10 "$f" | grep -q "^description:"; then
      ko "agent $(basename "$f"): manca 'description:' nel frontmatter"
      agent_issues=$((agent_issues+1))
    fi
  done
  if [ "$agent_issues" -eq 0 ] && [ "$agent_count" -gt 0 ]; then
    ok "agents: $agent_count file, frontmatter OK"
  fi
fi

# 4. Skill frontmatter
skill_count=0
skill_issues=0
if [ -d "$CLAUDE_DIR/skills" ]; then
  for d in "$CLAUDE_DIR/skills"/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    [[ "$name" == shared ]] && continue
    skill_count=$((skill_count+1))
    sk="$d/SKILL.md"
    if [ ! -f "$sk" ]; then
      ko "skill $name: manca SKILL.md"
      skill_issues=$((skill_issues+1))
      continue
    fi
    if ! head -10 "$sk" | grep -q "^name:"; then
      warning "skill $name: manca 'name:' nel frontmatter"
      skill_issues=$((skill_issues+1))
    fi
    if ! head -10 "$sk" | grep -q "^description:"; then
      ko "skill $name: manca 'description:' nel frontmatter"
      skill_issues=$((skill_issues+1))
    fi
  done
  if [ "$skill_issues" -eq 0 ] && [ "$skill_count" -gt 0 ]; then
    ok "skills: $skill_count dir, frontmatter OK"
  fi
fi

# 5. MEMORY.md presente (SOLO se il sistema di memoria esterno e' installato).
# Arturo di base non lo include: la memoria e' CLAUDE.md + handoff. Senza data/memory/
# questo check e' N/A, non un warning (evita un WARN perenne su installazione fresca).
MEMORY_INDEX="$CLAUDE_DIR/data/memory/MEMORY.md"
if [ ! -d "$CLAUDE_DIR/data/memory" ]; then
  ok "Memoria esterna non installata (usa CLAUDE.md + handoff): check MEMORY.md N/A"
elif [ -f "$MEMORY_INDEX" ]; then
  line_count=$(wc -l < "$MEMORY_INDEX" | tr -d ' ')
  if [ "$line_count" -gt 200 ]; then
    warning "MEMORY.md: $line_count righe (limite raccomandato 200, righe oltre vengono troncate)"
  else
    ok "MEMORY.md: $line_count righe (sotto limite 200)"
  fi
  # Link broken: estrai [[slug]] e verifica file esistenti (glob ricorsivo)
  broken=0
  while IFS= read -r slug; do
    [ -z "$slug" ] && continue
    found=$(find "$CLAUDE_DIR/data/memory" -name "${slug}.md" -type f 2>/dev/null | head -1)
    if [ -z "$found" ]; then
      broken=$((broken+1))
      [ "$broken" -le 5 ] && report+=("WARN  link MEMORY.md non risolto: [[$slug]]")
    fi
  done < <(grep -oE '\[\[[a-z0-9_-]+\]\]' "$MEMORY_INDEX" 2>/dev/null | tr -d '[]' | sort -u)
  if [ "$broken" -eq 0 ]; then
    ok "MEMORY.md: tutti i link [[slug]] risolvono"
  else
    warn=$((warn+broken))
    [ "$broken" -gt 5 ] && report+=("WARN  (+ $((broken-5)) link broken non mostrati)")
  fi
else
  warning "MEMORY.md non trovato in $MEMORY_INDEX"
fi

# 6. Permessi contraddittori (stesso pattern in allow e deny)
if [ -f "$SETTINGS" ]; then
  conflicts=$(python3 -c "
import json
cfg = json.load(open('$SETTINGS'))
perms = cfg.get('permissions', {})
allow = set(perms.get('allow', []))
deny = set(perms.get('deny', []))
overlap = allow & deny
if overlap:
    print('\n'.join(sorted(overlap)))
" 2>/dev/null)
  if [ -z "$conflicts" ]; then
    ok "permessi: nessun pattern duplicato tra allow e deny"
  else
    while IFS= read -r p; do
      ko "permesso ambiguo (sia allow che deny): $p"
    done <<< "$conflicts"
  fi
fi

# Output finale
echo ""
echo "=== System Audit: $(date '+%Y-%m-%d %H:%M') ==="
echo ""
if [ "$fail" -eq 0 ] && [ "$warn" -eq 0 ]; then
  echo "Verdetto: tutto verde ($pass PASS)"
elif [ "$fail" -eq 0 ]; then
  echo "Verdetto: $pass PASS, $warn WARN, 0 FAIL"
else
  echo "Verdetto: $fail problemi, $warn warning, $pass PASS"
fi
echo ""
for line in "${report[@]}"; do
  echo "  $line"
done
echo ""
if [ "$fail" -gt 0 ]; then
  first_fail=$(printf '%s\n' "${report[@]}" | grep -m1 '^FAIL' | sed 's/^FAIL  //')
  echo "Prima cosa da fixare: $first_fail"
fi

exit 0
