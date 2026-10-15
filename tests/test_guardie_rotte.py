#!/usr/bin/env python3
"""GR01: una guardia che si rompe non lascia passare in silenzio.

Le guardie Bash passano dal dispatcher, che trasforma un crash in «ask». web-egress-guard è
registrata da sola in settings.json: fino al 15/10/2026, rotta, usciva con 1, un errore non
bloccante, e l'URL passava. Ora chiede, come ask_guard. protect_claude_md resta com'è: rotta esce
con 2 e blocca, per scelta (invariante I02 di test_permissivita_2026_09_08.py).

Il banco rompe una copia della guardia con un'eccezione dentro l'analisi e guarda l'uscita.
Sulla base 4515e63 GR01 è rosso.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["GR01"]


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
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        esito = rotta(repo, "web-egress-guard.py", "for url in _iter_urls(tool_input):",
                      {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com/"}}, Path(tmp, "a"))
        if not chiede(esito):
            rossi.append(f"GR01 web-egress-guard rotta non chiede: rc={esito.returncode} out={esito.stdout[:120]!r}")

    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"guardie rotte: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
