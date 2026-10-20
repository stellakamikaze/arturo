#!/usr/bin/env python3
"""Auto-load scheda progetto all'avvio sessione (SessionStart).

v3 (post-audit 2026-07-07): niente più ranking lessicale sui token del path —
la rilevanza per contenuto la copre memory-retrieve.py a ogni prompt. Qui resta
solo la garanzia deterministica: se CWD = dir di progetto, la sua scheda
`progetto-<nome>.md` viene proposta per match esatto sul filename, in qualunque
radice della memoria (melchior_match.radici).

Memoria spenta (melchior_match.memoria_accesa): esce subito, senza output.
Zero-dipendenze. Non-blocking: errore → exit 0 silenzioso.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import melchior_match as mm  # noqa: E402

ACCESS_LOG = mm.access_log_path()  # un file per macchina, vedi melchior_match


def log_access(paths, context):
    mm.registra_accessi(paths, context, log_path=ACCESS_LOG)


def find_scheda(name):
    """Scheda progetto per match esatto sul filename, path-independent."""
    if not name:
        return None
    target = f"progetto-{name.lower()}.md"
    for radice in mm.radici():
        for p in sorted(radice.rglob(target)):
            try:
                rel = p.relative_to(radice).parts
            except ValueError:
                continue
            if not any(x.startswith(("_", ".")) for x in rel):
                return p
    return None


def main():
    if not mm.memoria_accesa():
        return
    # argv opzionale come hint manuale (es. da /inizio <progetto>), altrimenti CWD.
    # Retention v2 (2026-08-01): il canale era muto da settimane perché matcha solo
    # il nome ESATTO della cwd, e le sessioni partono quasi sempre dalla cartella che
    # contiene i progetti o da una sottocartella del progetto. Ora risale i parent
    # (max 3) e prende la prima scheda che esiste: partire da <progetto>/frontend/src
    # trova comunque progetto-<progetto>.md.
    if sys.argv[1:]:
        names = list(sys.argv[1:])
    else:
        cwd = Path.cwd()
        names = [cwd.name] + [q.name for q in list(cwd.parents)[:3]]
    found = []
    for n in names:
        p = find_scheda(n)
        if p:
            found.append(p)
            break  # la scheda più vicina alla cwd basta: niente rumore dai parent
    if not found:
        return

    log_access(found, "cwd")
    print("")
    print("MEMORY-AUTOLOAD: scheda progetto per questa directory (leggi con Read se ti serve):")
    for p in found:
        fm = mm.parse_frontmatter_simple(mm.leggi(p)) or {}
        desc = str(mm.campo(fm, "description") or "")[:100]
        print(f"  - {mm.breve(p)} — {desc}")


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        main()
    except Exception as e:
        print(f"# memory-autoload error: {e}", file=sys.stderr)
