#!/usr/bin/env python3
"""PF01-PF10: protect_claude_md.py chiede quando non riesce a giudicare (26/11/2026, #6416).

Prima un settings*.json che il controllo del JSON non legge (assente, illeggibile, non UTF-8) dava deny,
come un JSON rotto, anche con lo sblocco o con una preferenza che apre la categoria; e un errore dentro
l'analisi usciva con 2 e bloccava ogni Edit e ogni Write. Ora il primo chiede con "non legge", salvo un deny
già scritto (il default di Arturo sui settings, la categoria o una riga per percorso), e il secondo chiede
con "errore interno". Restano: il deny per il JSON che non sarebbe valido e il blocco su un input che non si
legge (invariante I02 di test_permissivita_2026_09_08.py).

Il guasto dell'analisi è un veleno dentro il file della guardia: un raise in testa a _persistenza, che
ogni Edit e ogni Write attraversano.

Invarianti (verdi anche sulla base): PF07, PF08, PF09, PF10.
Sulla base 0951400 sono rossi PF01, PF02, PF03, PF04, PF05, PF06.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = [f"PF{n:02d}" for n in range(1, 11)]
DISCRIMINANTI = ["PF01", "PF02", "PF03", "PF04", "PF05", "PF06"]
VELENO_DOVE = "def _persistenza(rp):\n"
VELENO = VELENO_DOVE + "    raise RuntimeError('guasto del banco')\n"


def rotta(guardia: str) -> str:
    """La guardia con un errore dentro l'analisi."""
    assert guardia.count(VELENO_DOVE) == 1, "PF04: _persistenza va trovata una volta nella guardia"
    return guardia.replace(VELENO_DOVE, VELENO, 1)


def decidi(guardia: str, strumento: str, relativo: str, ti: dict | None = None, radice: str = ".claude",
           grezzo: bytes | None = None, input_grezzo: str | None = None, local: str = "",
           sblocco: bool = False) -> tuple[str, str]:
    """Esito e motivo della guardia. `grezzo` scrive il bersaglio con quei byte; None lascia il file assente."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        claude = home / ".claude"
        (claude / "hooks").mkdir(parents=True)
        (claude / "hooks" / "protect_claude_md.py").write_text(guardia, encoding="utf-8")
        if local:
            (claude / "arturo").mkdir()
            (claude / "arturo" / "protect_claude_md.local").write_text(local, encoding="utf-8")
        if sblocco:
            (claude / "config-unlock-s1").write_text("", encoding="utf-8")
        bersaglio = home / radice / relativo
        bersaglio.parent.mkdir(parents=True, exist_ok=True)
        if grezzo is not None:
            bersaglio.write_bytes(grezzo)
        dati = {"tool_name": strumento, "tool_input": {"file_path": str(bersaglio), **(ti or {})}, "session_id": "s1"}
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        env.pop("CLAUDE_CONFIG_DIR", None)
        p = subprocess.run([sys.executable, "-B", str(claude / "hooks" / "protect_claude_md.py")],
                           input=input_grezzo if input_grezzo is not None else json.dumps(dati),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        if p.returncode == 2:
            return "block", p.stderr.strip()
        if p.returncode != 0:
            return f"rc{p.returncode}", p.stderr.strip()
        if not p.stdout.strip():
            return "silent", ""
        h = json.loads(p.stdout)["hookSpecificOutput"]
        return h["permissionDecision"], h.get("permissionDecisionReason", "")


def prova(guardia: str) -> list[str]:
    edit = {"old_string": '"a": 1', "new_string": '"a": 2'}
    latin1 = b'{"a": "\xe8"}\n'
    ok = b'{"a": 1}\n'
    ask = "ask settings-radice\n"
    # (codice, guardia, strumento, file, input, radice, byte del file, stdin grezzo, .local, sblocco, esito, parola)
    casi = [
        # Con la preferenza che chiede sui settings della radice (la scelta dell'autore): un settings assente
        # o non UTF-8 chiede come uno leggibile, non nega.
        ("PF01", guardia, "Edit", "settings.local.json", edit, ".claude", None, None, ask, False, "ask", "non legge"),
        ("PF02", guardia, "Edit", "settings.json", edit, ".claude", latin1, None, ask, False, "ask", "non legge"),
        # Con la categoria aperta o con lo sblocco chiede: mai allow su un file che il controllo non legge.
        ("PF03", guardia, "Edit", "settings.json", edit, ".claude", latin1, None, "allow settings-radice\n", False,
         "ask", "non legge"),
        ("PF04", guardia, "Edit", "settings.json", edit, ".claude", latin1, None, "", True, "ask", "non legge"),
        # Un errore dentro l'analisi chiede, sul settings e su un file qualsiasi: mai blocco, mai allow.
        ("PF05", rotta(guardia), "Edit", "settings.json", edit, ".claude", ok, None, "", False, "ask", "errore interno"),
        ("PF06", rotta(guardia), "Write", "nota.txt", {"content": "x\n"}, "progetto", None, None, "", False,
         "ask", "errore interno"),
        # Invarianti: senza preferenze il settings illeggibile resta deny (il default di Arturo sui settings),
        # e così con un deny della persona; il JSON che non sarebbe valido resta deny; l'input illeggibile blocca.
        ("PF07", guardia, "Edit", "settings.json", edit, ".claude", latin1, None, "", False, "deny", ""),
        ("PF08", guardia, "Edit", ".claude/settings.json", edit, "progetto", latin1, None, "deny dot-claude-progetto\n",
         False, "deny", ""),
        ("PF09", guardia, "Edit", "settings.json", {"old_string": '"a": 1', "new_string": '"a": 1,'}, ".claude", ok,
         None, "allow settings-radice\n", False, "deny", "JSON"),
        ("PF10", guardia, "Edit", "settings.json", edit, ".claude", ok, "{", "", False, "block", ""),
    ]
    rossi = []
    for codice, g, strumento, relativo, ti, radice, grezzo, input_grezzo, local, sblocco, atteso, parola in casi:
        esito, motivo = decidi(g, strumento, relativo, ti, radice, grezzo, input_grezzo, local, sblocco)
        if esito != atteso or parola not in motivo:
            rossi.append(f"{codice} {strumento} {relativo}: atteso {atteso} con {parola!r}, avuto {esito} {motivo[:120]!r}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    if argomenti.baseline_ref:
        vecchia = subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:hooks/protect_claude_md.py"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
        codici = [r.split()[0] for r in prova(vecchia)]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    rossi = prova((repo / "hooks" / "protect_claude_md.py").read_text(encoding="utf-8"))
    for r in rossi:
        print("ROSSO", r)
    print(f"protect fail-closed: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
