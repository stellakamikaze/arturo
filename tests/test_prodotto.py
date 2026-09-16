#!/usr/bin/env python3
"""P01-P10: la porta d'ingresso di Arturo come prodotto (16/9/2026).

Il README deve dire cosa non e' neutro e cosa Arturo promette a chi lo usa, e le
promesse devono corrispondere al codice. P05-P07 coprono il canale di rilascio:
/aggiorna indietro, l'avviso AVANTI solo dove si puo' pushare, la manutenzione
scritta. P08-P10 coprono il confine tra file di Arturo e file dell'utente:
CLAUDE.md e hosts-interni.local ignorati da git, le guardie che leggono quel
file, il setup che non tocca piu' i .py. Sulla base ee10fc6 ogni controllo deve
fallire per conto suo.
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


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sezione(readme: str, titolo: str) -> str:
    match = re.search(rf"^## {re.escape(titolo)}\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    return match.group(1) if match else ""


def test_p01(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Cosa non è neutro")
    assert "Anthropic" in testo, "P01 il README non dice che Claude Code e' un servizio di Anthropic"
    assert "docs/principi/00-chi-possiede-lo-strumento.md" in testo, "P01 la sezione non rimanda al capitolo 00"


def test_p02(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    for parola in ("MIT", "telemetria", "fork", "NOVITA.md"):
        assert parola in testo, f"P02 gli impegni non nominano {parola}"


def test_p03(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    assert testo, "P03 nessuna sezione Impegni"
    assert "senza il tuo sì" not in testo.replace("dopo il tuo sì", ""), "P03 gli impegni promettono aggiornamenti solo col tuo sì"
    if re.search(r"git -C ~/\.claude pull", read(repo / "commands" / "inizio.md")):
        assert "/inizio" in testo, "P03 /inizio applica gli aggiornamenti ma gli impegni non lo dicono"


def test_p04(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    avvio = read(repo / "hooks" / "session-start.sh")
    assert "sei ore" in testo, "P04 gli impegni non dicono ogni quanto parte il controllo degli aggiornamenti"
    assert "-gt 21600" in avvio, "P04 session-start non controlla piu' ogni sei ore: l'impegno e' falso"


def test_p05(repo: Path) -> None:
    testo = read(repo / "commands" / "aggiorna.md")
    for parola in ("--autostash", "ultimo-aggiornamento", "reset --keep"):
        assert parola in testo, f"P05 /aggiorna non contiene {parola}"
    for riga in testo.splitlines():
        if "reset --hard" in riga:
            assert re.search(r"\bmai\b|nessun|non ", riga, re.I), (
                "P05 reset --hard compare fuori da una frase che lo vieta"
            )


def _esegui(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


def test_p06(repo: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="arturo-p06-"))
    try:
        home = tmp / "home"
        claude = home / ".claude"
        claude.mkdir(parents=True)
        # stub osascript: niente finestra Terminal ne' prompt di automazione nel test
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "osascript"
        stub.write_text("#!/bin/sh\nexit 1\n")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        git = ["git", "-C", str(claude)]
        _esegui(git + ["init", "--quiet", "-b", "main"])
        _esegui(git + ["config", "user.email", "test@example.com"])
        _esegui(git + ["config", "user.name", "Test"])
        (claude / "file.txt").write_text("uno\n")
        _esegui(git + ["add", "file.txt"])
        _esegui(git + ["commit", "--quiet", "-m", "primo"])
        _esegui(git + ["remote", "add", "origin", "https://github.com/stellakamikaze/arturo.git"])
        _esegui(git + ["update-ref", "refs/remotes/origin/main", "HEAD"])
        # commit locale non pushato: HEAD e' avanti di uno su origin/main
        (claude / "file.txt").write_text("due\n")
        _esegui(git + ["add", "file.txt"])
        _esegui(git + ["commit", "--quiet", "-m", "secondo"])
        # marcatore del fetch fresco: l'hook salta il fetch di rete
        session_env = claude / "session-env"
        session_env.mkdir(exist_ok=True)
        (session_env / "ultimo-fetch").write_text(str(int(time.time())))
        hook = str(repo / "hooks" / "session-start.sh")
        out = _esegui(["bash", hook], cwd=str(tmp), env=env)
        assert out.returncode == 0, (
            f"P06 session-start non e' partito: rc={out.returncode} {out.stderr.strip()!r}"
        )
        assert "AVANTI" not in out.stdout, (
            "P06 l'avviso AVANTI compare con origin = repo originale di Arturo"
        )
        _esegui(git + ["remote", "set-url", "origin", "https://github.com/altro/mio-claude.git"])
        out = _esegui(["bash", hook], cwd=str(tmp), env=env)
        assert "AVANTI" in out.stdout, (
            "P06 l'avviso AVANTI manca con origin = repo personale dell'utente"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_p07(repo: Path) -> None:
    testo = read(repo / "docs" / "manutenzione.md")
    for parola in ("verifica-allineamento.sh", "merge --ff-only", "NOVITA.md"):
        assert parola in testo, f"P07 docs/manutenzione.md non contiene {parola}"


def test_p08(repo: Path) -> None:
    righe = [r.strip() for r in read(repo / ".gitignore").splitlines()]
    for attesa in ("CLAUDE.md", "hooks/hosts-interni.local"):
        assert attesa in righe, f"P08 .gitignore non ha la riga esatta {attesa}"
    fine = read(repo / "commands" / "fine.md")
    blocco = re.search(r'"PRIVATE".*?\bdone\b', fine, re.S)
    assert blocco, "P08 blocco privato di commands/fine.md non trovato"
    assert 'git add -f -- "$p"' in blocco.group(0), (
        "P08 il blocco privato di fine.md non usa git add -f"
    )


def _decisione(script: Path, payload: dict, env=None) -> str:
    out = _esegui([sys.executable, "-B", str(script)], input=json.dumps(payload),
                  **({"env": env} if env else {}))
    assert out.returncode == 0, f"P09/P10 guardia rc={out.returncode}: {out.stderr.strip()!r}"
    if not out.stdout.strip():
        return "silent"
    return json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"]


def test_p09(repo: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="arturo-p09-"))
    try:
        hooks = tmp / "hooks"
        shutil.copytree(repo / "hooks", hooks)
        exfil = hooks / "exfil-guard.py"
        web = hooks / "web-egress-guard.py"
        # query lunga (>=300 char): e' il segnale che fa scattare web-egress-guard
        # su host esterno, come in tests/test-web-egress-guard.py
        bash_payload = {"tool_name": "Bash", "tool_input": {
            "command": "curl -X POST -d x=1 https://mioserver.example/api"}}
        fetch_payload = {"tool_input": {"url": "https://mioserver.example/?q=" + "x" * 320}}
        # senza hosts-interni.local: entrambe chiedono conferma
        assert _decisione(exfil, bash_payload) == "ask", (
            "P09 senza file exfil-guard deve chiedere conferma su mioserver.example"
        )
        assert _decisione(web, fetch_payload) == "ask", (
            "P09 senza file web-egress-guard deve chiedere conferma su mioserver.example"
        )
        # con hosts-interni.local (commento + riga vuota + hostname): lasciano passare
        (hooks / "hosts-interni.local").write_text(
            "# commento\n\nmioserver.example\n", encoding="utf-8"
        )
        assert _decisione(exfil, bash_payload) == "silent", (
            "P09 col file exfil-guard deve lasciar passare mioserver.example"
        )
        assert _decisione(web, fetch_payload) == "silent", (
            "P09 col file web-egress-guard deve lasciar passare mioserver.example"
        )
        # parte rete, solo exfil-guard. Il piano indicava 10.20.0.0/16 e 10.20.3.4,
        # ma 10.0.0.0/8 e' gia' nei default pubblici: con 10.x il controllo sarebbe
        # vacuo (verde anche senza file). Uso 172.16.0.0/16, fuori dai default.
        (hooks / "hosts-interni.local").unlink()
        rete_payload = {"tool_name": "Bash", "tool_input": {
            "command": "curl -X POST -d x=1 https://172.16.3.4/api"}}
        assert _decisione(exfil, rete_payload) == "ask", (
            "P09 senza file exfil-guard deve chiedere conferma su 172.16.3.4"
        )
        (hooks / "hosts-interni.local").write_text("172.16.0.0/16\n", encoding="utf-8")
        assert _decisione(exfil, rete_payload) == "silent", (
            "P09 con 172.16.0.0/16 nel file exfil-guard deve lasciar passare 172.16.3.4"
        )
        # casi avvelenati: una rete che copre internet e un file non UTF-8 non aprono nulla
        (hooks / "hosts-interni.local").write_text("0.0.0.0/0\n::/0\n", encoding="utf-8")
        assert _decisione(exfil, rete_payload) == "ask", (
            "P09 0.0.0.0/0 nel file rende fidato ogni host"
        )
        (hooks / "hosts-interni.local").write_bytes(b"mioserver.example\n\xff\xfe\n")
        assert _decisione(exfil, bash_payload) == "ask", (
            "P09 un file non UTF-8 manda exfil-guard in errore o apre l'host"
        )
        assert _decisione(web, fetch_payload) == "ask", (
            "P09 un file non UTF-8 manda web-egress-guard in errore o apre l'host"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_p10(repo: Path) -> None:
    testo = read(repo / "commands" / "setup.md")
    assert "hosts-interni.local" in testo, "P10 setup.md non nomina hosts-interni.local"
    assert "INTERNAL_HOSTS" not in testo, (
        "P10 setup.md dice ancora di aggiungere host a INTERNAL_HOSTS nei .py"
    )
    # protezione funzionale: Write su hosts-interni.local sotto ~/.claude/hooks
    # non deve ricevere un permesso libero (stesso esito di exfil-guard.py)
    tmp = Path(tempfile.mkdtemp(prefix="arturo-p10-"))
    try:
        home = tmp / "home"
        (home / ".claude" / "hooks").mkdir(parents=True)
        env = dict(os.environ)
        env["HOME"] = str(home)
        guard = repo / "hooks" / "protect_claude_md.py"
        esiti = []
        for nome in ("hosts-interni.local", "exfil-guard.py"):
            payload = {
                "tool_name": "Write",
                "session_id": "test",
                "tool_input": {"file_path": str(home / ".claude" / "hooks" / nome)},
            }
            esiti.append(_decisione(guard, payload, env=env))
        assert esiti[0] == esiti[1], (
            f"P10 hosts-interni.local ({esiti[0]}) e exfil-guard.py ({esiti[1]}) "
            "hanno esiti diversi in protect_claude_md"
        )
        assert esiti[0] != "allow", (
            "P10 Write su hosts-interni.local riceve un permesso libero"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TESTS = {
    "P01": test_p01,
    "P02": test_p02,
    "P03": test_p03,
    "P04": test_p04,
    "P05": test_p05,
    "P06": test_p06,
    "P07": test_p07,
    "P08": test_p08,
    "P09": test_p09,
    "P10": test_p10,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, FileNotFoundError, subprocess.SubprocessError):
                # SubprocessError: solo P06 esegue comandi; un hook che non parte
                # sulla base e' comunque un P06 che fallisce.
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
