#!/usr/bin/env python3
"""PostToolUse su Edit, MultiEdit, Write e NotebookEdit: l'indice della Scoperta (bin/scoperta.py).

Claude Code salva le versioni dei file che modifica, ma le cancella dopo `cleanupPeriodDays`. Questo
hook tiene una riga per modifica in ~/.claude/data/scoperta/indice.jsonl: ora, sessione, percorso,
strumento, righe entrate e uscite, e i nomi dei campi o dei paragrafi cambiati. Mai il testo. Così
la Scoperta vede le ripetizioni anche oltre quella finestra.

Non blocca e non parla mai: un errore qualsiasi esce zitto con 0. I file esclusi dalla Scoperta
(`arturo scoperta esclusioni`) non entrano. Oltre i 4 MB l'indice si accorcia alla metà più recente.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

PESO_MASSIMO = 4 * 1024 * 1024


def main() -> int:
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(dati, dict):
        return 0
    strumento = dati.get("tool_name")
    ingresso = dati.get("tool_input") if isinstance(dati.get("tool_input"), dict) else {}
    percorso = ingresso.get("file_path") or ingresso.get("notebook_path")
    sessione = dati.get("session_id")
    if strumento not in ("Edit", "MultiEdit", "Write", "NotebookEdit") or not isinstance(percorso, str) \
            or not isinstance(sessione, str) or not sessione:
        return 0
    sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "bin"))
    import scoperta  # noqa: E402

    assoluto = scoperta.normalizza(percorso, dati.get("cwd") if isinstance(dati.get("cwd"), str) else None)
    if scoperta.escluso(assoluto, scoperta.esclusioni()):
        return 0
    if strumento == "Edit":
        coppie = [(ingresso.get("old_string"), ingresso.get("new_string"))]
    elif strumento == "MultiEdit":
        coppie = [(e.get("old_string"), e.get("new_string")) for e in ingresso.get("edits") or [] if isinstance(e, dict)]
    elif strumento == "Write":
        coppie = [("", ingresso.get("content"))]
    else:
        coppie = [("", ingresso.get("new_source"))]
    campi, piu, meno = [], 0, 0
    titoli = os.path.splitext(assoluto)[1].lower() in scoperta.TITOLI
    for vecchio, nuovo in coppie:
        if not isinstance(vecchio, str) or not isinstance(nuovo, str):
            continue
        nomi, p, m = scoperta.etichette(vecchio, nuovo, titoli=titoli)
        piu, meno = piu + p, meno + m
        campi += [n for n in nomi if n not in campi]
    if strumento == "Write":
        campi = []  # un file riscritto intero: i suoi titoli non dicono cosa è cambiato
    indice = scoperta.cartella() / "indice.jsonl"
    indice.parent.mkdir(parents=True, exist_ok=True)
    riga = {"ora": dt.datetime.now().isoformat(timespec="seconds"), "sessione": sessione, "percorso": assoluto,
            "strumento": strumento, "piu": piu, "meno": meno, "campi": campi[:6]}
    with open(indice, "a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    if indice.stat().st_size > PESO_MASSIMO:
        righe = indice.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        tmp = indice.with_name(indice.name + f".{os.getpid()}.tmp")
        tmp.write_text("".join(righe[len(righe) // 2:]), encoding="utf-8")
        os.replace(tmp, indice)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - un hook di sola registrazione non deve mai fermare Claude
        sys.exit(0)
