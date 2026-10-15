#!/usr/bin/env python3
"""GR01-GR02: una guardia che si rompe chiede conferma, come ask_guard in bash-dispatcher.sh.

Le guardie Bash passano dal dispatcher, che trasforma un crash in «ask». web-egress-guard e
protect_claude_md sono registrate da sole in settings.json: fino al 15/10/2026 la prima, rotta,
usciva con 1 (errore non bloccante: l'URL passava) e la seconda con 2 (ogni modifica bloccata).

Il banco rompe una copia della guardia con un'eccezione dentro l'analisi e guarda l'uscita.
Sulla base 4515e63 GR01 e GR02 sono rossi.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["GR01", "GR02"]


def rotta(repo: Path, nome: str, dove: str, dati: dict, cartella: Path) -> subprocess.CompletedProcess:
    """La guardia con `raise` subito prima della riga `dove`, lanciata su `dati`."""
    sorgente = (repo / "hooks" / nome).read_text(encoding="utf-8")
    righe = sorgente.split("\n")
    trovate = [i for i, r in enumerate(righe) if r.strip().startswith(dove)]
    assert len(trovate) == 1, f"{nome}: la riga «{dove}» va trovata una volta, trovata {len(trovate)}"
    i = trovate[0]
    rientro = righe[i][: len(righe[i]) - len(righe[i].lstrip())]
    righe.insert(i, f"{rientro}raise RuntimeError('veleno del banco')")
    (cartella / "hooks").mkdir(parents=True, exist_ok=True)
    copia = cartella / "hooks" / nome
    copia.write_text("\n".join(righe), encoding="utf-8")
    return subprocess.run([sys.executable, "-B", str(copia)], input=json.dumps(dati),
                          capture_output=True, text=True, timeout=30)


def chiede(esito: subprocess.CompletedProcess) -> bool:
    try:
        decisione = json.loads(esito.stdout)["hookSpecificOutput"]["permissionDecision"]
    except Exception:  # noqa: BLE001
        return False
    return esito.returncode == 0 and decisione == "ask" and "rotta" in esito.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    repo = Path(parser.parse_args().repo)
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        esito = rotta(repo, "web-egress-guard.py", "for url in _iter_urls(tool_input):",
                      {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com/"}}, Path(tmp, "a"))
        if not chiede(esito):
            rossi.append(f"GR01 web-egress-guard rotta non chiede: rc={esito.returncode} out={esito.stdout[:120]!r}")

        esito = rotta(repo, "protect_claude_md.py", "rp = os.path.realpath(",
                      {"tool_name": "Write", "tool_input": {"file_path": str(Path(tmp, "nota.md")), "content": "x"}},
                      Path(tmp, "b"))
        if not chiede(esito):
            rossi.append(f"GR02 protect_claude_md rotta non chiede: rc={esito.returncode} out={esito.stdout[:120]!r}")

    for r in rossi:
        print("ROSSO", r)
    print(f"guardie rotte: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
