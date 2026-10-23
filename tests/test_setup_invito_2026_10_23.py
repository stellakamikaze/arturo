#!/usr/bin/env python3
"""SI01-SI03: l'avvio invita a finire /setup (23/10/2026).

Nella telemetria del 23/10 Liliana aveva installato Arturo senza mai lanciare /setup, e Alessio si era
fermato prima della fase 9. L'avvio (hooks/session-start.sh) ora scrive una riga SETUP, una volta al
giorno, in un'installazione vera senza data/setup-fatto e nata dal 16/10, quando il segno è arrivato.

SI01 un'installazione nuova riceve la riga SETUP, e nello stesso giorno una volta sola.
SI02 col segno data/setup-fatto la riga non torna, nemmeno il giorno dopo.
SI03 un'installazione nata prima del 16/10 non la riceve: poteva aver finito /setup senza segno.

Sulla base f4ae0aa ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def installazione(repo: Path, radice: Path, nata: str | None = None) -> Path:
    """Una HOME con ~/.claude repository git nato oggi, o nel giorno `nata`, coi file di Arturo in link."""
    home = radice / "home"
    claude = home / ".claude"
    claude.mkdir(parents=True)
    for voce in repo.iterdir():
        if voce.name not in (".git", "data", "session-env"):
            (claude / voce.name).symlink_to(voce, target_is_directory=voce.is_dir())
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")
    if nata:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"{nata}T10:00:00"
    subprocess.run(["git", "init", "-q", str(claude)], check=True, env=env)
    subprocess.run(["git", "-C", str(claude), "commit", "-q", "--allow-empty", "-m", "clone"], check=True, env=env)
    return home


def avvio(home: Path, radice: Path) -> list:
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ["PATH"], "ARTURO_BANCHI_AVVIO": "0",
           "ARTURO_TELEMETRIA": "0", "CLAUDE_PROJECT_DIR": str(radice)}
    p = subprocess.run(["bash", str(home / ".claude" / "hooks" / "session-start.sh")], input="{}", env=env,
                       cwd=radice, capture_output=True, text=True, timeout=60)
    return [r for r in p.stdout.splitlines() if r.startswith("SETUP:")]


def test_si01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = installazione(repo, radice)
        prima = avvio(home, radice)
        assert len(prima) == 1 and "/setup" in prima[0], f"SI01 un'installazione nuova non riceve l'invito: {prima!r}"
        seconda = avvio(home, radice)
        assert seconda == [], f"SI01 l'invito torna nello stesso giorno: {seconda!r}"


def test_si02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = installazione(repo, radice)
        assert avvio(home, radice), "SI02 un'installazione nuova non riceve l'invito"
        (home / ".claude" / "data").mkdir()
        (home / ".claude" / "data" / "setup-fatto").write_text("2026-10-23\n", encoding="utf-8")
        (home / ".claude" / "session-env" / "setup-invito").write_text("2026-01-01\n", encoding="utf-8")
        dopo = avvio(home, radice)
        assert dopo == [], f"SI02 l'invito torna anche col segno setup-fatto: {dopo!r}"


def test_si03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        assert avvio(installazione(repo, radice), radice), "SI03 un'installazione nuova non riceve l'invito"
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        vecchia = avvio(installazione(repo, radice, nata="2026-10-14"), radice)
        assert vecchia == [], f"SI03 un'installazione del 14/10 riceve l'invito: {vecchia!r}"


TESTS = {"SI01": test_si01, "SI02": test_si02, "SI03": test_si03}


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
