#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate anti-leak prima di `git commit` / `gh pr create`.

Scansiona il diff STAGED (git diff --cached) alla ricerca di secret ad ALTA
confidenza nelle righe aggiunte. Se trovati -> ask (non blocco: evita di rompere
commit legittimi; l'utente decide). Usa un set curato di pattern per minimizzare
i falsi positivi (NO "password=..." generico che matcha codice/test).

I leak in un commit sono irreversibili una volta pushati: questo e' l'unico
layer PREVENTIVO (gli scanner PostToolUse avvisano a cose fatte).

Fail-open su qualsiasi errore. Legge cwd dal payload per lanciare git nel repo giusto.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import signal
import subprocess
import sys


def _stdin_timeout(signum, frame):
    # 9/10/2026: un gate che scade e tace e' un gate spento (git lento, disco freddo).
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                      "permissionDecisionReason": "Scansione dei segreti nel commit scaduta: conferma prima di proseguire."}}))
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


HIGH_CONF = [
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "chiave privata"),
    (r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "AWS Access Key"),
    (r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{22,}\b", "GitHub PAT"),
    (r"\bsk-ant-[A-Za-z0-9-]{20,}", "Anthropic API key"),
    (r"\bsk_live_[A-Za-z0-9]{20,}", "Stripe live key"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\bAIza[A-Za-z0-9_-]{35}\b", "Google API key"),
    (r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b", "Google OAuth client secret"),
    (r"\b1//[A-Za-z0-9_-]{20,}\b", "Google refresh token"),
    (r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b", "Telegram bot token"),
    (r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"postgres(?:ql)?://[^:@\s]+:[^@\s]+@[^/\s]+", "connection string con password"),
]
COMPILED = [(re.compile(p), name) for p, name in HIGH_CONF]


# Gli heredoc li riconosce heredoc.py, lo stesso modulo delle altre guardie (15/10/2026).
# Se manca, nessun corpo sparisce: la guardia controlla tutto il testo.
try:
    _spec_hd = importlib.util.spec_from_file_location(
        "arturo_heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
    _hd = importlib.util.module_from_spec(_spec_hd)
    _spec_hd.loader.exec_module(_hd)
    _togli_heredoc = _hd.togli
except Exception:
    def _togli_heredoc(cmd, via, segnaposto=None):
        return cmd
_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.S)
_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
# Le shell sono quelle di forma_comando.py, un solo elenco per tutte le guardie (15/10/2026).
try:
    _spec_fc = importlib.util.spec_from_file_location(
        "forma_comando", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forma_comando.py"))
    _fc = importlib.util.module_from_spec(_spec_fc)
    _spec_fc.loader.exec_module(_fc)
    _SHELL = _fc.SHELL
except Exception:
    _SHELL = frozenset("sh bash zsh dash ksh fish".split())
_WRAPPERS = _SHELL | {"eval", "xargs", "env", "command", "exec", "nohup", "time", "sudo"}
_UNRESOLVED = object()


def _senza_heredoc(command: str) -> str:
    """Il comando senza i corpi di heredoc che vanno a un lettore (cat, tee) o a codice di un
    interprete che non lancia programmi. Nel dubbio il corpo resta (vedi heredoc.py)."""
    return _togli_heredoc(command, lambda h: h.inerte() or h.codice_inerte())


def _expand(word: str, variables: dict):
    if "`" in word or "$(" in word:
        return _UNRESOLVED

    def sub(m):
        name = m.group(1) or m.group(2)
        if name in variables:
            return variables[name]
        if name == "HOME":
            return os.path.expanduser("~")
        raise KeyError(name)

    try:
        expanded = os.path.expanduser(_VAR.sub(sub, word))
    except KeyError:
        return _UNRESOLVED
    return _UNRESOLVED if "$" in expanded else expanded


def _segments(command: str):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    segment = []
    for token in lexer:
        if token and set(token) <= set(";&|()\n"):
            if segment:
                yield segment
            segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def _repo_for_command(command: str, cwd: str):
    """Il repository su cui girera' `git commit`.

    Restituisce il percorso, None se non risolvibile (-> ask), oppure False se
    nessun `git commit` viene eseguito davvero (il pattern ha visto la parola
    in un messaggio o in un heredoc). Il parsing rispetta le virgolette: un
    messaggio di commit su piu' righe non spezza il comando.
    """
    location = os.path.abspath(cwd)
    variables: dict = {}
    try:
        segments = list(_segments(_senza_heredoc(command)))
    except ValueError:
        return None
    for tokens in segments:
        index = 0
        assigned = {}
        while index < len(tokens) and _ASSIGN.match(tokens[index]):
            name, value = _ASSIGN.match(tokens[index]).groups()
            assigned[name] = value
            index += 1
        if tokens[index:index + 1] == ["export"]:
            for token in tokens[index + 1:]:
                if _ASSIGN.match(token):
                    name, value = _ASSIGN.match(token).groups()
                    assigned[name] = value
            index = len(tokens)
        if index >= len(tokens):
            for name, value in assigned.items():
                expanded = _expand(value, variables)
                if expanded is _UNRESOLVED:
                    variables.pop(name, None)
                else:
                    variables[name] = expanded
            continue
        tokens = tokens[index:]
        head = os.path.basename(tokens[0])
        if head in ("cd", "pushd"):
            if len(tokens) > 1:
                target = _expand(tokens[1], variables)
                if target is _UNRESOLVED:
                    location = None
                elif location is not None:
                    location = os.path.abspath(os.path.join(location, target))
            continue
        # `env VAR=… git …` e `command git …` (4/10/2026, #2832): si tolgono il wrapper e le
        # assegnazioni e si guarda il git che resta. Gli altri wrapper restano «non risolvibile».
        if head in ("env", "command"):
            resto = tokens[1:]
            while resto and _ASSIGN.match(resto[0]):
                resto = resto[1:]
            if resto and os.path.basename(resto[0]) == "git":
                tokens, head = resto, "git"
        if head in _WRAPPERS and "commit" in " ".join(tokens[1:]):
            return None
        if head != "git":
            continue
        index = 1
        # Opzioni globali prima del sottocomando (15/10/2026): `--no-pager`, `-p` e simili
        # si saltano; prima `git --no-pager -C repo commit` usciva come «nessun commit».
        while index < len(tokens) and tokens[index].startswith("-"):
            opzione = tokens[index]
            if opzione in ("-C", "-c"):
                if index + 1 >= len(tokens):
                    return None
                if opzione == "-C":
                    target = _expand(tokens[index + 1], variables)
                    if target is _UNRESOLVED or location is None:
                        return None
                    location = os.path.abspath(os.path.join(location, target))
                index += 2
                continue
            if opzione.startswith(("--git-dir", "--work-tree", "--namespace", "--config-env", "--exec-path")):
                return None
            index += 1
        if index < len(tokens) and tokens[index] == "commit":
            return location
    if re.search(r"\bgh\s+pr\s+create\b", command):
        return location
    return False


def _diff(repo: str, commit_all: bool, add_prima: bool = False) -> str | None:
    commands = [["git", "-C", repo, "diff", "--cached", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"]]
    if commit_all or add_prima:
        commands.append(["git", "-C", repo, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"])
    output = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=4, check=False)
        if result.returncode:
            return None
        output.append(result.stdout)
    if add_prima:
        # 9/10/2026: `git add X && git commit` mette X in stage dopo questo controllo.
        # Si leggono anche i file non tracciati che git add potrebbe aggiungere.
        result = subprocess.run(["git", "-C", repo, "ls-files", "--others", "--exclude-standard", "-z"],
                                capture_output=True, text=True, timeout=4, check=False)
        if result.returncode:
            return None
        for nome in [n for n in result.stdout.split("\0") if n][:200]:
            try:
                with open(os.path.join(repo, nome), encoding="utf-8", errors="ignore") as f:
                    output.append("\n".join("+" + riga for riga in f.read(200_000).splitlines()))
            except OSError:
                continue
    return "\n".join(part for part in output if part)


def _ask(reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason}}))
    return 0


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(6)
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0
    cwd = data.get("cwd") or os.path.expanduser("~")
    repo = _repo_for_command(command, cwd)
    if repo is False:
        return 0
    if not repo:
        return _ask("Repository destinatario del commit non risolvibile: conferma prima di proseguire.")
    # Fuori da un repository Git il commit fallisce da solo: niente da scansionare.
    try:
        dentro = subprocess.run(["git", "-C", repo, "rev-parse", "--git-dir"], capture_output=True,
                                text=True, timeout=4, check=False).returncode == 0
    except Exception:
        dentro = True
    if not dentro:
        return 0

    # `git commit -a/--all` mette in stage i file tracciati modificati DURANTE il
    # commit: al momento di questo check (PreToolUse) l'index non li contiene ancora,
    # quindi il solo `diff --cached` mancherebbe un secret in un file gia' tracciato.
    commit_all = bool(re.search(r"\bcommit\b[^|;&]*\s-{1,2}(a\b|all\b|[a-zA-Z]*a[a-zA-Z]*\b)", command))
    add_prima = bool(re.search(r"\bgit\b[^;&|\n]*\sadd\b", command))
    try:
        out = _diff(repo, commit_all, add_prima)
    except Exception:
        out = None
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    if out is None:
        return _ask("Scansione Git del repository destinatario fallita: conferma prima di proseguire.")

    if not out:
        return 0

    added = "\n".join(
        ln[1:] for ln in out.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    )
    if not added:
        return 0

    found = []
    for rx, name in COMPILED:
        if rx.search(added):
            found.append(name)
    if not found:
        return 0

    uniq = list(dict.fromkeys(found))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                "Possibile secret nel diff staged: " + ", ".join(uniq[:5]) + ". "
                "Un leak pushato e' irreversibile. Conferma solo dopo aver "
                "verificato che non sia una credenziale reale."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
