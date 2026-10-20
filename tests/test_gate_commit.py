#!/usr/bin/env python3
"""G214-G215: il gate dei segreti nei commit, portati dai banchi della config dell'autore.

G214 commit-secret-gate.py da solo: trova il repository del commit anche dopo un cd con un
     messaggio su piu' righe, una variabile assegnata o esportata, `git -C`, un heredoc verso
     python prima del commit, `commit -a`, un heredoc verso bash. Chiede senza poter leggere il
     diff quando il repository non si risolve (variabile ignota, $( ), bash -c, xargs,
     --git-dir, virgolette aperte). Tace su un commit scritto in un heredoc verso cat, citato in
     un echo, o fuori da un repository.
G215 `git add X && git commit` nello stesso comando: il gate guarda anche quello che l'add mette
     in stage, sia da solo sia passando dal dispatcher. In un repository pulito tace.
     Le forme del commit nel dispatcher (a capo, git -c, env, subshell, --no-pager, cartella in
     variabile) stanno in K01 di test_config_2026_10_15.py e qui non si ripetono.

Sulla base 842b06f (prima del gate allineato alla config dell'autore) ogni controllo deve
fallire con un AssertionError che comincia con il suo codice.
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

BASH = shutil.which("bash") or "bash"
# Token finti composti a runtime: nessun segreto nel sorgente.
AWS_FINTO = "AKIA" + "X" * 16
GH_FINTO = "gh" + "p_" + "A1b2C3d4" * 5
GIT_ENV = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@esempio.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@esempio.org"}


def _git(cartella: Path, *argomenti: str) -> None:
    subprocess.run(["git", "-C", str(cartella), *argomenti], env=dict(os.environ, **GIT_ENV),
                   capture_output=True, text=True, timeout=60, check=True)


def _gate(repo: Path, comando: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(repo / "hooks" / "commit-secret-gate.py")], text=True,
                          input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd)}),
                          capture_output=True, timeout=60, env=dict(os.environ, **GIT_ENV))


def _esito(proc: subprocess.CompletedProcess) -> tuple:
    if proc.returncode == 2:
        return "block", ""
    out = proc.stdout.strip()
    if not out:
        return "silent", ""
    try:
        h = json.loads(out.splitlines()[-1])["hookSpecificOutput"]
        return h["permissionDecision"], h.get("permissionDecisionReason", "")
    except (json.JSONDecodeError, KeyError, TypeError):
        return "?", out[:80]


def test_g214(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        r = Path(d) / "repo"
        r.mkdir()
        fuori = Path(d) / "fuori"
        fuori.mkdir()
        _git(r, "init", "-q")
        (r / "a").write_text("base\n", encoding="utf-8")
        _git(r, "add", "a")
        _git(r, "commit", "-qm", "base")
        (r / "leak.txt").write_text(f"k={AWS_FINTO}\n", encoding="utf-8")
        _git(r, "add", "leak.txt")
        segreto, irrisolto, passa = "segreto", "irrisolto", "passa"
        # Barre dritte: in bash le barre di Windows non quotate sono escape e "cd" non arriva al repository.
        rp, fp = r.as_posix(), fuori.as_posix()
        casi = [
            ("messaggio su piu' righe dopo cd", f'cd {rp} && git commit -q -m "riga uno\n\nriga tre; con | pipe"', segreto),
            ("variabile assegnata", f"P={rp}; cd $P && git commit -m x", segreto),
            ("variabile con graffe", f'P={rp}\ncd "${{P}}" && git commit -m "a\nb"', segreto),
            ("export", f"export P={rp}; git -C $P commit -m x", segreto),
            ("git -C letterale", f'git -C {rp} commit -q -m "a\nb"', segreto),
            ("heredoc python prima del commit", f"cd {rp} && python3 - <<'X'\nprint('it''s; | && fine')\nX\ngit commit -m 'ok'", segreto),
            ("commit -a", f'cd {rp} && git commit -am "x"', segreto),
            ("heredoc verso bash", f"bash <<'X'\ncd {rp} && git commit -m x\nX", segreto),
            ("variabile ignota", 'cd "$IGNOTA" && git commit -m x', irrisolto),
            ("cd su sostituzione", "cd $(mktemp -d) && git commit -m x", irrisolto),
            ("bash -c", f"bash -c 'cd {rp} && git commit -m x'", irrisolto),
            ("xargs", "echo x | xargs git commit -m", irrisolto),
            ("git --git-dir", f"git --git-dir={rp}/.git commit -m x", irrisolto),
            ("virgoletta non chiusa", f'cd {rp} && git commit -m "aperta', irrisolto),
            ("solo testo in heredoc cat", "cat > /dev/null <<'X'\ngit commit -m prova\nX", passa),
            ("commit citato in un echo", 'echo "poi git commit"; ls', passa),
            ("fuori da un repository", f"cd {fp} && git commit -m x", passa),
        ]
        for nome, comando, atteso in casi:
            decisione, motivo = _esito(_gate(repo, comando, fuori))
            ottenuto = segreto if "Possibile secret" in motivo else (irrisolto if motivo else passa)
            assert ottenuto == atteso, f"G214 {nome}: atteso {atteso}, ottenuto {ottenuto} ({decisione}: {motivo[:60]})"


def test_g215(repo: Path) -> None:
    def prepara(cartella: Path, con_segreto: bool) -> None:
        cartella.mkdir()
        _git(cartella, "init", "-q")
        (cartella / "pulito.txt").write_text("niente di segreto\n", encoding="utf-8")
        if con_segreto:
            (cartella / "conf.py").write_text(f'TOKEN = "{GH_FINTO}"\n', encoding="utf-8")

    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        for i, comando in enumerate(("git add conf.py && git commit -m prova", "git add -A; git commit -m prova",
                                     # limite noto: si chiede anche se il file col segreto non viene aggiunto
                                     "git add pulito.txt && git commit -m prova")):
            r = radice / f"r{i}"
            prepara(r, True)
            decisione, _ = _esito(_gate(repo, comando, r))
            assert decisione == "ask", f"G215 add e commit nello stesso comando passano: {comando} ({decisione})"
        pulito = radice / "pulito"
        prepara(pulito, False)
        decisione, motivo = _esito(_gate(repo, "git add pulito.txt && git commit -m prova", pulito))
        assert decisione == "silent", f"G215 add e commit in un repository pulito chiedono: {motivo[:80]}"

        home = radice / "home"
        shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
        sporco = radice / "sporco"
        prepara(sporco, True)

        def dispatcher(comando: str) -> str:
            p = subprocess.run([BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")], text=True,
                               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando},
                                                 "cwd": str(sporco)}),
                               capture_output=True, timeout=60,
                               env=dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_TELEMETRIA="0", **GIT_ENV))
            return _esito(p)[0]

        sp = sporco.as_posix()  # barre dritte, come nel K01
        assert dispatcher(f"cd {sp} && git add conf.py && git commit -m prova") == "ask", \
            "G215 dal dispatcher add e commit con un segreto passano"
        for comando in (f'cd {sp} && echo "git commit"', f"cd {sp} && git status",
                        "cat > nota.md <<'X'\ngit add conf.py && git commit -m x\nX"):
            assert dispatcher(comando) == "silent", f"G215 il dispatcher ferma un comando che non fa commit: {comando!r}"


TESTS = {"G214": test_g214, "G215": test_g215}


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
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
