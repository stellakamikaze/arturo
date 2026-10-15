#!/usr/bin/env python3
"""Pre-filtro del comms-guard: separa il CODICE eseguito dalla PROSA.

Misura 2026-09-04 (30 giorni di transcript): 14 blocchi duri del comms-guard, 13
erano testo che NOMINAVA smtplib/sendmail/gws +send senza inviare nulla: heredoc
scritti su file, `grep -ril smtp`, edit di script, messaggi di commit. Il 28/8 il
modello ha riscritto un comando «evitando keyword bloccate»: una regex che sbaglia
13 volte su 14 addestra ad aggirarla.

Stampa la versione RIDOTTA del comando, su cui il dispatcher e comms-guard.py
rimatchano i pattern:
  - i corpi degli heredoc consumati da binari che NON eseguono (cat, tee, sed, awk,
    grep, jq, sort, head, tail, wc, patch, diff, git) vengono rimossi. Un heredoc
    dato a python/bash/perl/node RESTA: quel testo gira davvero;
  - se ogni segmento del comando inizia con un binario di sola lettura (grep, rg,
    cat, head, tail, less, wc, ls, find, jq, diff, sort, uniq, awk, sed -n, file,
    stat, git, cd) stampa vuoto: si sta leggendo, non inviando.
Se l'analisi fallisce stampa il comando intero (fail-closed: si rimatcha tutto).
"""
import json
import re
import sys

# Sonda del 13/10/2026: `find -exec sendmail`, `awk 'BEGIN{system("sendmail ...")}'` e
# `git send-email` si riducevano a vuoto e passavano senza comms-guard. find, awk e sed
# eseguono comandi (-exec, system(), il comando e di sed): non sono ne' sola lettura ne'
# consumatori inerti di un heredoc. git resta sola lettura salvo i sottocomandi che inviano.
NON_EXEC = {"cat", "tee", "grep", "rg", "jq", "sort", "head", "tail",
            "wc", "patch", "diff", "git", "cut", "tr", "uniq", "less", "more"}
READ_ONLY = {"grep", "rg", "cat", "head", "tail", "less", "more", "wc", "ls",
             "jq", "diff", "sort", "uniq", "file", "stat", "git", "cd", "echo",
             "printf", "which", "type", "true", "cut", "tr", "column"}
GIT_INVIA = re.compile(r"\bgit\b[^|;&]*\b(send-email|imap-send|request-pull)\b")

HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1([^\n]*)\n(.*?)\n\s*\2\s*(?=\n|$)", re.S)


def _first_bin(segment: str) -> str:
    seg = segment.strip()
    # salta assegnazioni env e wrapper
    while True:
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*=\S*\s+|sudo\s+|env\s+|command\s+|nohup\s+)", seg)
        if not m:
            break
        seg = seg[m.end():]
    m = re.match(r"([^\s;&|()]+)", seg)
    return m.group(1).rsplit("/", 1)[-1] if m else ""


def reduce(cmd: str) -> str:
    # 1) heredoc consumati da binari non-esecutori: via il corpo
    def _strip(m):
        start = cmd.rfind("\n", 0, m.start()) + 1
        line = cmd[start:m.start()]
        consumer = _first_bin(line.split("|")[-1] if "|" in line else line)
        # 13/10/2026: `cat <<'EOF' | sh` passa il corpo a sh, che lo esegue. Conta anche ogni
        # programma dopo il delimitatore sulla stessa riga: pipe, &&, ;.
        for seg in re.split(r"\|\||&&|;|\|", m.group(3))[1:]:
            dopo = _first_bin(seg)
            if dopo and dopo not in NON_EXEC:
                return m.group(0)
        # `python3 - <<EOF` o `bash <<EOF`: il corpo gira, si tiene
        if consumer and consumer not in NON_EXEC:
            return m.group(0)
        # Delimitatore senza virgolette: la shell esegue le $( ) e i backtick del corpo
        # anche verso cat. Quel corpo resta.
        if not m.group(1) and ("$(" in m.group(4) or "`" in m.group(4)):
            return m.group(0)
        return m.group(0)[: m.start(4) - m.start()] + "[heredoc]" + m.group(0)[m.end(4) - m.start():]
    reduced = HEREDOC_RE.sub(_strip, cmd)

    # 2) ogni segmento e' sola lettura? -> vuoto
    stripped = re.sub(r"'[^']*'|\"[^\"]*\"", "", reduced)
    segments = [s for s in re.split(r"\|\||&&|;|\||\n", stripped) if s.strip()]
    if segments and all(_first_bin(s) in READ_ONLY for s in segments) and not GIT_INVIA.search(stripped):
        # eccezione: `echo ... | mail` non arriva qui (mail non e' read-only);
        # `git commit -m "..."` era gia' git-puro nel dispatcher
        return ""
    return reduced


def main() -> int:
    try:
        data = json.load(sys.stdin)
        cmd = (data.get("tool_input") or {}).get("command") or ""
        sys.stdout.write(reduce(cmd))
    except Exception:
        try:
            sys.stdout.write(cmd)  # type: ignore[name-defined]
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
