#!/usr/bin/env python3
"""MP01-MP04: passo 2 dei mod (3/11/2026, #4619). Nessun mod cambia più il comando Bash.

In modalità auto Claude Code respinge un comando cambiato da un mod dopo l'approvazione, e il comando
va rilanciato identico (segnalazioni n. 46-48). Escono i mod riscrivi-bash e gws; il loro lavoro lo
fanno l'avvio, bash-dispatcher.sh e hooks/gws-esito.py, che fermano e spiegano senza cambiare niente.

MP01 prima del comando l'hook gws nega `gws gmail messages` e scrive la forma con `users`; lascia
     passare la forma giusta, un comando senza gws e un gws che non è in posizione di comando.
MP02 dopo il comando, col codice d'uscita diverso da 0 (PostToolUseFailure, campo error) o uguale a 0
     (PostToolUse, stdout e stderr), un guasto di credenziali dà un avviso alla persona, una nota a
     Claude con l'account della cartella di config e il login da rifare, e lancia
     gws-token-health.py --refresh. Un errore che non è di credenziali, o un comando senza gws, tace.
MP03 settings.json registra l'hook su PreToolUse, PostToolUse e PostToolUseFailure di Bash; i mod
     skills/gws e skills/riscrivi-bash non ci sono più e NOVITA.md annuncia l'uscita di tutti e due.
MP04 con il marcatore arturo-zsh-come-bash nel file d'ambiente della sessione bash-dispatcher.sh non
     blocca un glob in un'opzione (zsh ha nonomatch); senza il marcatore, o per Monitor, lo blocca.

Sulla base 08d09cf ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List

EVENTI = ("PreToolUse", "PostToolUse", "PostToolUseFailure")
FINTO_HEALTH = """import sys, pathlib
pathlib.Path(__file__).with_name("refresh.txt").write_text(" ".join(sys.argv[1:]), encoding="utf-8")
"""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def hook_gws(repo: Path, codice: str, cartella: Path) -> Path:
    sorgente = repo / "hooks" / "gws-esito.py"
    assert sorgente.is_file(), f"{codice} manca hooks/gws-esito.py"
    shutil.copy2(sorgente, cartella / "gws-esito.py")
    (cartella / "gws-token-health.py").write_text(FINTO_HEALTH, encoding="utf-8")
    return cartella / "gws-esito.py"


def lancia(hook: Path, payload: dict, env_extra: Dict[str, str] | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "GOOGLE_WORKSPACE_CLI_CONFIG_DIR"}
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, str(hook)], input=json.dumps(payload), text=True, capture_output=True,
                       encoding="utf-8", env=env, timeout=30)
    assert r.returncode == 0, f"hook uscito {r.returncode}: {r.stderr[-300:]}"
    return json.loads(r.stdout) if r.stdout.strip() else {}


def test_mp01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        hook = hook_gws(repo, "MP01", Path(t))
        pre = lambda c: lancia(hook, {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": c}})
        out = pre("GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-a gws gmail messages list --params '{}'")
        spec = out.get("hookSpecificOutput", {})
        assert spec.get("permissionDecision") == "deny", f"MP01 gws gmail messages passa: {out}"
        assert "gws gmail users messages list" in spec.get("permissionDecisionReason", ""), \
            f"MP01 il diniego non scrive la forma con users: {spec}"
        for c in ("gws gmail users messages list", "ls -la", "echo gws gmail messages", "grep 'gws gmail messages' f.md"):
            assert pre(c) == {}, f"MP01 l'hook risponde a {c!r}: {pre(c)}"


def test_mp02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        hook = hook_gws(repo, "MP02", d)
        refresh = d / "refresh.txt"
        casi = [
            ({"hook_event_name": "PostToolUseFailure", "error": "Exit code 1\n{\"error\":\"No credentials provided\"}"},
             "GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/x/gws-prova gws drive files list", {}, "gws-prova", "No credentials provided"),
            ({"hook_event_name": "PostToolUse", "tool_response": {"stdout": "", "stderr": "invalid_grant: token revoked"}},
             "gws calendar events list", {"GOOGLE_WORKSPACE_CLI_CONFIG_DIR": "/y/gws-sessione"}, "gws-sessione", "invalid_grant"),
        ]
        for base, cmd, env, nome, guasto in casi:
            refresh.unlink(missing_ok=True)
            out = lancia(hook, {**base, "tool_name": "Bash", "tool_input": {"command": cmd}}, env)
            avviso = out.get("systemMessage", "")
            nota = out.get("hookSpecificOutput", {}).get("additionalContext", "")
            assert nome in avviso and guasto in avviso and "login" in avviso, f"MP02 avviso sbagliato per {cmd!r}: {out}"
            assert out.get("hookSpecificOutput", {}).get("hookEventName") == base["hook_event_name"], \
                f"MP02 hookEventName sbagliato: {out}"
            assert nome in nota and "gws auth login" in nota and "Non riprovare" in nota, f"MP02 nota sbagliata: {nota!r}"
            for _ in range(50):
                if refresh.exists():
                    break
                time.sleep(0.1)
            assert read(refresh) == "--refresh", f"MP02 il controllo dei token non riparte dopo {guasto}"
        refresh.unlink(missing_ok=True)
        zitti = [
            {"hook_event_name": "PostToolUseFailure", "error": "Exit code 1\n403 insufficient scopes"},
            {"hook_event_name": "PostToolUseFailure", "error": "No credentials provided", "_cmd": "ls"},
            {"hook_event_name": "PostToolUse", "tool_response": {"stdout": "ok", "stderr": ""}},
        ]
        for z in zitti:
            cmd = z.pop("_cmd", "gws drive files list")
            out = lancia(hook, {**z, "tool_name": "Bash", "tool_input": {"command": cmd}})
            assert out == {}, f"MP02 l'hook parla senza un guasto di credenziali: {z} -> {out}"
        time.sleep(0.3)
        assert not refresh.exists(), "MP02 il controllo dei token riparte senza guasto"


def test_mp03(repo: Path) -> None:
    settings = json.loads(read(repo / "settings.json") or "{}")
    mancano: List[str] = []
    for evento in EVENTI:
        gruppi = settings.get("hooks", {}).get(evento, [])
        if not any(re.fullmatch(g.get("matcher") or ".*", "Bash") and
                   any("hooks/gws-esito.py" in h.get("command", "") for h in g.get("hooks", [])) for g in gruppi):
            mancano.append(evento)
    assert not mancano, f"MP03 settings.json non registra gws-esito.py su {mancano}"
    rimasti = [m for m in ("gws", "riscrivi-bash") if (repo / "skills" / m).exists()]
    assert not rimasti, f"MP03 mod ancora presenti: {rimasti}"
    novita = read(repo / "NOVITA.md")
    assert re.search(r"Escono i mod `riscrivi-bash` e `gws`", novita), "MP03 NOVITA.md non annuncia l'uscita dei due mod"


def test_mp04(repo: Path) -> None:
    dispatcher = repo / "hooks" / "bash-dispatcher.sh"
    with tempfile.TemporaryDirectory() as t:
        conf = Path(t) / "conf"
        sid = "sessione-di-prova"
        ambiente = conf / "session-env" / sid
        ambiente.mkdir(parents=True)
        bash = shutil.which("bash") or "bash"

        def rc(tool: str, sessione: str) -> int:
            p = {"tool_name": tool, "session_id": sessione, "tool_input": {"command": "grep -rn x --include=*.md ."}}
            env = {**os.environ, "SHELL": "/bin/zsh", "CLAUDE_CONFIG_DIR": str(conf)}
            return subprocess.run([bash, str(dispatcher)], input=json.dumps(p), text=True, capture_output=True,
                                  env=env, timeout=60).returncode

        assert rc("Bash", sid) == 2, "MP04 senza il marcatore il dispatcher non blocca più il glob in un'opzione"
        (ambiente / "sessionstart-hook-0.sh").write_text(
            "if [ -n \"${ZSH_VERSION:-}\" ]; then setopt nonomatch noequals shwordsplit; fi  # arturo-zsh-come-bash\n",
            encoding="utf-8")
        assert rc("Bash", sid) == 0, "MP04 col marcatore il dispatcher blocca ancora il glob in un'opzione"
        assert rc("Monitor", sid) == 2, "MP04 per Monitor, che non esegue il file d'ambiente, il blocco salta"
        assert rc("Bash", "../" + sid) == 2, "MP04 un session_id con .. sblocca il glob"


TESTS: Dict[str, Callable[[Path], None]] = {"MP01": test_mp01, "MP02": test_mp02, "MP03": test_mp03, "MP04": test_mp04}


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
