#!/usr/bin/env python3
"""SF01-SF04: commit-secret-gate dice perché la scansione dei segreti non parte (3/11/2026, #4472).

In una settimana "scansione-fallita" ha chiesto 8 volte con 7 sì, su un'installazione: il commit è
partito senza controllo dei segreti, e il popup non diceva perché. Ora nomina la causa e il rimedio.

SF01 indice di git rotto: il popup nomina l'indice e `git status`.
SF02 cartella di un altro utente (git stampa "dubious ownership"): il popup dà il comando safe.directory.
SF03 git più lento di 4 secondi sul diff: il popup lo dice.
SF04 invariante: in tutti e tre i casi la guardia chiede, non lascia passare.

SF02 e SF03 usano un git finto nel PATH, uno script bash: su Windows sono saltati e dichiarati.
Sulla base e2106f0 (dev prima della modifica) sono rossi SF01, SF02 e SF03.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import salti_windows  # noqa: E402

CASI = ["SF01", "SF02", "SF03", "SF04"]
DISCRIMINANTI = ["SF01"] if os.name == "nt" else ["SF01", "SF02", "SF03"]
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@esempio.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@esempio.org"}
GIT_VERO = shutil.which("git") or "git"


def _repo(cartella: Path) -> Path:
    cartella.mkdir()
    env = dict(os.environ, **GIT_ENV)
    subprocess.run([GIT_VERO, "init", "-q", str(cartella)], env=env, check=True, capture_output=True)
    (cartella / "a.txt").write_text("ciao\n", encoding="utf-8")
    subprocess.run([GIT_VERO, "-C", str(cartella), "add", "a.txt"], env=env, check=True, capture_output=True)
    return cartella


def _git_finto(cartella: Path, sul_diff: str) -> Path:
    """Un git che fa `sul_diff` quando gli chiedono diff, e passa il resto al git vero."""
    cartella.mkdir()
    finto = cartella / "git"
    finto.write_text(f'#!/usr/bin/env bash\nfor a in "$@"; do\n  if [ "$a" = diff ]; then\n    {sul_diff}\n'
                     f'  fi\ndone\nexec "{GIT_VERO}" "$@"\n', encoding="utf-8")
    finto.chmod(0o755)
    return cartella


def _decidi(repo: Path, cwd: Path, path: str | None = None) -> tuple[str, str]:
    env = dict(os.environ, PYTHONUTF8="1", ARTURO_TELEMETRIA="0", **GIT_ENV)
    if path:
        env["PATH"] = path + os.pathsep + env.get("PATH", "")
    p = subprocess.run([sys.executable, "-B", str(repo / "hooks" / "commit-secret-gate.py")], text=True,
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"},
                                         "cwd": str(cwd)}),
                       capture_output=True, timeout=60, env=env, encoding="utf-8")
    if p.returncode == 2:
        return "block", p.stderr
    out = p.stdout.strip()
    if not out:
        return "silent", ""
    h = json.loads(out.splitlines()[-1])["hookSpecificOutput"]
    return h["permissionDecision"], h.get("permissionDecisionReason", "")


def prova(repo: Path) -> list[str]:
    rossi, decisioni = [], []
    with tempfile.TemporaryDirectory() as tmp:
        radice = Path(tmp)
        rotto = _repo(radice / "rotto")
        (rotto / ".git" / "index").write_bytes(b"DIRC questo indice non e' valido")
        d, motivo = _decidi(repo, rotto)
        decisioni.append(("SF01", d))
        if "indice" not in motivo or "git status" not in motivo:
            rossi.append(f"SF01 indice rotto: il popup non nomina l'indice e git status: {motivo[:100]!r}")

        if os.name == "nt":
            salti_windows.dichiara("SF02", "il git finto è uno script bash")
            salti_windows.dichiara("SF03", "il git finto è uno script bash")
        else:
            pulito = _repo(radice / "altrui")
            finto = _git_finto(radice / "bin-altrui",
                               "echo \"fatal: detected dubious ownership in repository at '$PWD'\" >&2; exit 128")
            d, motivo = _decidi(repo, pulito, str(finto))
            decisioni.append(("SF02", d))
            if "safe.directory" not in motivo:
                rossi.append(f"SF02 dubious ownership: manca il comando safe.directory: {motivo[:100]!r}")

            lento = _repo(radice / "lento")
            finto = _git_finto(radice / "bin-lento", "exec sleep 6")
            d, motivo = _decidi(repo, lento, str(finto))
            decisioni.append(("SF03", d))
            if "4 secondi" not in motivo:
                rossi.append(f"SF03 git lento: il popup non dice dei 4 secondi: {motivo[:100]!r}")

    if any(d != "ask" for _, d in decisioni):
        rossi.append(f"SF04 la guardia non chiede in ogni caso: {decisioni}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo))
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"scansione fallita spiegata: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
