#!/usr/bin/env python3
"""Auto-load scheda progetto all'avvio sessione (SessionStart).

v3 (post-audit 2026-07-07): niente più ranking lessicale sui token del path —
la rilevanza per contenuto la copre memory-retrieve.py a ogni prompt. Qui resta
solo la garanzia deterministica: se CWD = dir di progetto, la sua scheda
`progetto-<nome>.md` viene proposta per match esatto sul filename, in qualunque
radice della memoria (melchior_match.radici).

Memoria spenta (melchior_match.memoria_accesa): esce subito, senza output. Al primo avvio senza
scelta nelle impostazioni la accende e lo dice una volta (melchior_match.accendi_al_primo_avvio).
Zero-dipendenze. Non-blocking: errore → exit 0 silenzioso.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import melchior_match as mm  # noqa: E402

ACCESS_LOG = mm.access_log_path()  # un file per macchina, vedi melchior_match


def log_access(paths, context):
    mm.registra_accessi(paths, context, log_path=ACCESS_LOG)


find_scheda = mm.trova_scheda  # la ricerca sta in melchior_match: la usano anche arturo contesto e arturo memoria scheda


def main():
    avviso = mm.accendi_al_primo_avvio()
    if avviso:
        print(avviso)
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
        # La risalita si ferma alla home: il nome della home è il nome dell'utente, e se
        # coincide con quello di una scheda, la cartella contenitore la proponeva a ogni
        # avvio (#5868, 17/11/2026). Anche la cwd si risolve: su Windows resta col nome corto 8.3 con cui
        # il processo è partito (RUNNER~1 sul runner di GitHub), la home risolta ha quello lungo, e il confronto
        # non si fermava mai (provato su Windows 11 il 23/11/2026).
        cwd = Path.cwd()
        try:
            cwd = cwd.resolve()
            home = Path.home().resolve()
            fermi = {home, *home.parents}
        except (RuntimeError, OSError):
            fermi = set()
        names = []
        for q in [cwd, *list(cwd.parents)[:3]]:
            if q in fermi:
                break
            names.append(q.name)
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
