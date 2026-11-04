#!/usr/bin/env python3
"""AW01-AW05: la segnalazione n. 51 di Filippo del 4/11/2026 (hooks/agente-worktree.py).

Un agente lanciato con `isolation: "worktree"` che si ferma senza modifiche perde la copia: Claude Code la
toglie. Ripreso con SendMessage, riparte nella cartella della sessione madre. Provato il 4/11/2026 su
Claude Code 2.1.318 con `claude -p`: alla ripresa SubagentStart riscatta con lo stesso agent_id e il cwd
della madre, e le chiamate dei tool portano agent_id e quel cwd.

AW01 ripreso fuori dalla copia: l'avvio porta l'avviso col percorso della copia, Write e Bash ricevono un
     deny, Read passa.
AW02 un agente senza copia separata e la sessione principale: l'hook tace.
AW03 ripreso nella sua copia: nessun avviso, Write passa, e un segno `fuori` di prima si toglie.
AW04 la sessione madre cancella l'annotazione: l'agente può scrivere.
AW05 settings.json registra l'hook su SubagentStart e su PreToolUse per Edit, Write, Bash; la telemetria
     della deriva lo conosce.

Sulla base c9ee540 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AGENTE = "a04cb91be82a48937"


def hook(repo: Path, codice: str) -> Path:
    h = repo / "hooks" / "agente-worktree.py"
    assert h.is_file(), f"{codice} manca hooks/agente-worktree.py"
    return h


def lancia(h: Path, config: Path, dati: dict) -> dict:
    r = subprocess.run([sys.executable, str(h)], input=json.dumps(dati), text=True, capture_output=True,
                       env={"CLAUDE_CONFIG_DIR": str(config), "PATH": "/usr/bin:/bin"}, timeout=30)
    assert r.returncode == 0, f"hook uscito {r.returncode}: {r.stderr}"
    return json.loads(r.stdout) if r.stdout.strip() else {}


def avvio(h, config, cwd, agente=AGENTE):
    return lancia(h, config, {"hook_event_name": "SubagentStart", "agent_id": agente,
                              "agent_type": "general-purpose", "cwd": str(cwd)})


def tool(h, config, cwd, nome, agente=AGENTE):
    dati = {"hook_event_name": "PreToolUse", "tool_name": nome, "cwd": str(cwd),
            "tool_input": {"command": "git commit -am x"} if nome == "Bash" else {"file_path": str(Path(cwd) / "x")}}
    if agente:
        dati.update(agent_id=agente, agent_type="general-purpose")
    return lancia(h, config, dati)


def decisione(out: dict) -> str:
    return str((out.get("hookSpecificOutput") or {}).get("permissionDecision") or "")


def laboratorio(t: str):
    d = Path(t)
    madre = d / "repo"
    copia = madre / ".claude" / "worktrees" / f"agent-{AGENTE}"
    copia.mkdir(parents=True)
    return d / "config", madre, copia


def test_aw01(repo: Path) -> None:
    h = hook(repo, "AW01")
    with tempfile.TemporaryDirectory() as t:
        config, madre, copia = laboratorio(t)
        assert avvio(h, config, copia) == {}, "AW01 il primo avvio nella copia non deve dire niente"
        assert tool(h, config, copia, "Write") == {}, "AW01 nella sua copia l'agente deve poter scrivere"
        copia.rmdir()  # Claude Code toglie la copia di un agente fermo senza modifiche
        out = avvio(h, config, madre)
        testo = str((out.get("hookSpecificOutput") or {}).get("additionalContext") or "")
        assert str(copia) in testo and "non esiste più" in testo, f"AW01 la ripresa fuori dalla copia non avvisa: {out}"
        for nome in ("Write", "Edit", "Bash"):
            assert decisione(tool(h, config, madre, nome)) == "deny", f"AW01 {nome} fuori dalla copia non riceve deny"
        assert tool(h, config, madre, "Read") == {}, "AW01 Read fuori dalla copia deve passare"


def test_aw02(repo: Path) -> None:
    h = hook(repo, "AW02")
    with tempfile.TemporaryDirectory() as t:
        config, madre, _ = laboratorio(t)
        assert avvio(h, config, madre, "senzacopia1") == {}, "AW02 un agente senza copia riceve un avviso"
        assert avvio(h, config, madre, "senzacopia1") == {}, "AW02 un agente senza copia ripreso riceve un avviso"
        assert tool(h, config, madre, "Write", "senzacopia1") == {}, "AW02 un agente senza copia non può scrivere"
        assert tool(h, config, madre, "Bash", None) == {}, "AW02 la sessione principale riceve una decisione"


def test_aw03(repo: Path) -> None:
    h = hook(repo, "AW03")
    with tempfile.TemporaryDirectory() as t:
        config, madre, copia = laboratorio(t)
        avvio(h, config, copia)
        avvio(h, config, madre)  # una ripresa fuori, poi di nuovo dentro
        assert avvio(h, config, copia) == {}, "AW03 la ripresa nella sua copia avvisa"
        assert tool(h, config, copia / "sotto", "Write") == {}, "AW03 nella sua copia l'agente non può scrivere"
        nota = json.loads((config / "cache" / "agenti-worktree" / f"{AGENTE}.json").read_text(encoding="utf-8"))
        assert "fuori" not in nota, f"AW03 il segno fuori resta dopo la ripresa nella copia: {nota}"


def test_aw04(repo: Path) -> None:
    h = hook(repo, "AW04")
    with tempfile.TemporaryDirectory() as t:
        config, madre, copia = laboratorio(t)
        avvio(h, config, copia)
        out = avvio(h, config, madre)
        testo = str((out.get("hookSpecificOutput") or {}).get("additionalContext") or "")
        nota = config / "cache" / "agenti-worktree" / f"{AGENTE}.json"
        assert str(nota) in testo, f"AW04 l'avviso non dice quale file cancellare: {testo}"
        nota.unlink()
        assert tool(h, config, madre, "Write") == {}, "AW04 dopo la cancellazione l'agente non può scrivere"


def test_aw05(repo: Path) -> None:
    comando = "python3 ~/.claude/hooks/agente-worktree.py"
    s = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    hooks = s.get("hooks", {})
    avvio_ok = any(comando == h.get("command") for g in hooks.get("SubagentStart", []) for h in g.get("hooks", []))
    assert avvio_ok, "AW05 settings.json non registra l'hook su SubagentStart"
    gruppi = [g for g in hooks.get("PreToolUse", []) if any(comando == h.get("command") for h in g.get("hooks", []))]
    coperti = {n for g in gruppi for n in str(g.get("matcher", "")).split("|")}
    assert {"Edit", "MultiEdit", "Write", "NotebookEdit", "Bash"} <= coperti, f"AW05 PreToolUse non copre la scrittura: {coperti}"
    logica = (repo / "server" / "logica.js").read_text(encoding="utf-8")
    elenco = re.search(r"DERIVA_HOOK = \[(.*?)\];", logica, re.S)
    assert elenco and '"agente-worktree.py"' in elenco.group(1), "AW05 la telemetria della deriva non conosce l'hook"


TESTS = {"AW01": test_aw01, "AW02": test_aw02, "AW03": test_aw03, "AW04": test_aw04, "AW05": test_aw05}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
