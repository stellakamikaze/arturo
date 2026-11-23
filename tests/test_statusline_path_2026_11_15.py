#!/usr/bin/env python3
"""SP01: la barra trova node anche col PATH minimo di una sessione aperta via ssh (15/11/2026).

Volta apre le sessioni di un'altra macchina con `ssh -t <macchina> claude attach <id>`. Il client
`claude attach` nasce dalla shell di ssh, che non legge il file di avvio della persona: il PATH è
/usr/bin:/bin:/usr/sbin:/sbin, senza Homebrew e senza ~/.local/bin. Il comando della barra in
settings.json cercava node solo nel PATH, quindi in quelle sessioni la riga spariva e restava l'avviso
"manca node" anche con node installato.

SP01 con node solo in ~/.local/bin e PATH minimo, il comando di settings.json stampa la riga della
     barra e non l'avviso "manca node".
SP02 lo stesso per l'avviso sul contesto: col PATH minimo di una sessione di `claude --bg` o di ssh il comando
     partiva con `node` nudo e usciva 127 (16/11/2026). Dal 23/11/2026 (#6492, B5) l'avviso è context-monitor.py
     dentro `hooks/hub.py post`: col PATH minimo e senza node il comando di settings.json avvisa lo stesso.
SP03 la barra misura il contesto sulla finestra della compattazione (#6492, B5, 23/11/2026). Con 1M di finestra e
     autoCompactWindow 300000 una sessione si è compattata a 266.797 token, il 27% della scala grezza: l'avviso
     del 50% non arrivava mai. Con il 27% grezzo e quella chiave la barra e il file per il monitor dicono 90%.

Sulla base 8f62532 (il dev prima di questo passo) SP01 è rosso: il comando non allarga il PATH.
Sulla base fe199ff SP02 è rosso: l'hook dell'avviso sul contesto non allarga il PATH.
Sulla base 015041d SP03 è rosso: la barra dice 27%.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def comando(repo: Path) -> str:
    return json.loads((repo / "settings.json").read_text(encoding="utf-8"))["statusLine"]["command"]


def test_sp01(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "SP01 serve node su questa macchina per la prova"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(repo / "hooks" / "statusline.js", home / ".claude" / "hooks" / "statusline.js")
        (home / ".local" / "bin").mkdir(parents=True)
        os.symlink(os.path.realpath(node), home / ".local" / "bin" / "node")
        dati = json.dumps({"model": {"display_name": "Opus 5.5"}, "workspace": {"current_dir": tmp},
                           "context_window": {"remaining_percentage": 78}})
        r = subprocess.run(["/bin/sh", "-c", comando(repo)], input=dati, capture_output=True, text=True,
                           timeout=30, cwd=tmp,
                           env={"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"})
        assert "manca node" not in r.stdout and "│" in r.stdout, \
            f"SP01 col PATH di ssh la barra non trova node in ~/.local/bin: {r.stdout.strip()[:160]!r}"


def comando_contesto(repo: Path):
    """Il comando di settings.json che porta l'avviso sul contesto, e se è quello di hub (dal 23/11/2026)."""
    impostazioni = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    comandi = [h["command"] for m in impostazioni["hooks"]["PostToolUse"] for h in m["hooks"]
               if "context-monitor.js" in h["command"]]
    if comandi:
        assert len(comandi) == 1, f"SP02 atteso un solo hook di context-monitor.js, trovati {len(comandi)}"
        return comandi[0], False
    hub = [h["command"] for m in impostazioni["hooks"]["PostToolUse"] for h in m["hooks"] if "hub.py post" in h["command"]]
    assert len(hub) == 1, f"SP02 né context-monitor.js né un solo hub.py post in PostToolUse: {hub}"
    return hub[0], True


def test_sp02(repo: Path) -> None:
    import time
    comando, con_hub = comando_contesto(repo)
    node = shutil.which("node")
    assert con_hub or node, "SP02 serve node su questa macchina per la prova"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        if con_hub:
            for cartella in ("hooks", "bin"):
                shutil.copytree(repo / cartella, home / ".claude" / cartella,
                                ignore=shutil.ignore_patterns("__pycache__"))
            percorso = "/usr/bin:/bin:/usr/sbin:/sbin"  # senza node: l'avviso non ne ha più bisogno
        else:
            (home / ".claude" / "hooks").mkdir(parents=True)
            shutil.copy(repo / "hooks" / "context-monitor.js", home / ".claude" / "hooks" / "context-monitor.js")
            (home / ".local" / "bin").mkdir(parents=True)
            os.symlink(os.path.realpath(node), home / ".local" / "bin" / "node")
            percorso = "/usr/bin:/bin:/usr/sbin:/sbin"
        (home / "claude-ctx-sp02.json").write_text(json.dumps(
            {"session_id": "sp02", "remaining_percentage": 40, "used_pct": 60, "timestamp": int(time.time())}),
            encoding="utf-8")
        dati = json.dumps({"session_id": "sp02", "hook_event_name": "PostToolUse", "tool_name": "Bash",
                           "tool_input": {"command": "ls"}, "cwd": tmp})
        r = subprocess.run(["/bin/sh", "-c", comando], input=dati, capture_output=True, text=True,
                           timeout=60, cwd=tmp,
                           env={"HOME": str(home), "USERPROFILE": str(home), "PATH": percorso,
                                "TMPDIR": tmp, "ARTURO_NODE_DIRS": "" if con_hub else str(home / ".local" / "bin"),
                                "ARTURO_TELEMETRIA": "0"})
        assert r.returncode != 127 and "not found" not in r.stderr, \
            f"SP02 col PATH minimo l'avviso sul contesto non parte: rc={r.returncode} err={r.stderr.strip()[:160]!r}"
        assert "CONTEXT WARNING" in r.stdout, \
            f"SP02 col PATH minimo e il 60% usato nessun avviso: rc={r.returncode} out={r.stdout.strip()[:160]!r} " \
            f"err={r.stderr.strip()[:160]!r}"


def test_sp03(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "SP03 serve node su questa macchina per la prova"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(repo / "hooks" / "statusline.js", home / ".claude" / "hooks" / "statusline.js")
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""), "TMPDIR": tmp}

        def barra(remaining, finestra, chiave):
            impostazioni = home / ".claude" / "settings.json"
            impostazioni.write_text(json.dumps({"autoCompactWindow": chiave} if chiave else {}), encoding="utf-8")
            dati = json.dumps({"model": {"display_name": "Opus 5.5"}, "workspace": {"current_dir": tmp},
                               "session_id": "sp03",
                               "context_window": {"remaining_percentage": remaining, "context_window_size": finestra}})
            r = subprocess.run([node, str(home / ".claude" / "hooks" / "statusline.js")], input=dati,
                               capture_output=True, text=True, encoding="utf-8", timeout=30, cwd=tmp, env=env)
            ponte = json.loads((home / "claude-ctx-sp03.json").read_text(encoding="utf-8"))
            return r.stdout, ponte

        out, ponte = barra(73, 1000000, 300000)
        assert ponte["used_pct"] == 90 and ponte["remaining_percentage"] == 10 and "90%" in out, \
            f"SP03 al 27% grezzo con autoCompactWindow 300000 atteso 90%: ponte {ponte} barra {out.strip()[:120]!r}"
        out, ponte = barra(73, 1000000, None)
        assert ponte["used_pct"] == 27 and ponte["remaining_percentage"] == 73, \
            f"SP03 senza autoCompactWindow la scala non è più quella grezza: {ponte}"
        out, ponte = barra(73, 200000, 300000)
        assert ponte["used_pct"] == 27, f"SP03 con la finestra del modello più piccola la scala cambia: {ponte}"


TESTS = {"SP01": test_sp01, "SP02": test_sp02, "SP03": test_sp03}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--baseline-ref")
    args = ap.parse_args()
    casi = dict(TESTS)
    if os.name == "nt":
        print("SALTO SP01 SP02 la shell di ssh col PATH minimo è di Mac e Linux")
        casi = {"SP03": test_sp03}
    rossi = []
    for nome, test in casi.items():
        try:
            test(Path(args.repo))
        except AssertionError as e:
            rossi.append((nome, str(e)))
    if args.baseline_ref:
        if rossi and all(m.startswith(n) for n, m in rossi):
            print("BASELINE_DISCRIMINANTE=" + ",".join(n for n, _ in rossi))
            return 0
        print("baseline non discriminante: " + ("tutti verdi sulla base" if not rossi else str(rossi)))
        return 1
    if rossi:
        for _, m in rossi:
            print(f"ROSSO {m}")
        return 1
    print(f"PASS {','.join(casi)} controlli={len(casi)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
