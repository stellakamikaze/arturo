#!/usr/bin/env python3
"""Banco di sito/installa.sh, l'installatore di una riga.

Ogni caso gira in una HOME usa e getta, con un PATH di sistema senza il claude vero e un
repository locale al posto di GitHub (ARTURO_REPO). Nessun caso tocca la rete.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PATH_BASE = "/usr/bin:/bin:/usr/sbin:/sbin"


def sh(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def origine(radice: Path) -> Path:
    """Un repository con 'stellakamikaze/arturo' nel percorso, come il remoto vero."""
    lavoro = radice / "lavoro"
    lavoro.mkdir()
    sh("git", "init", "-q", "-b", "main", cwd=lavoro)
    (lavoro / "README.md").write_text("Arturo\n")
    sh("git", "add", "README.md", cwd=lavoro)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x", cwd=lavoro)
    nudo = radice / "stellakamikaze" / "arturo.git"
    sh("git", "clone", "-q", "--bare", str(lavoro), str(nudo))
    return nudo


class Lab:
    def __init__(self, script: Path, radice: Path, nome: str):
        self.script = script
        self.home = radice / nome / "home"
        self.bin = radice / nome / "bin"
        self.home.mkdir(parents=True)
        self.bin.mkdir()
        self.repo = str(radice / "stellakamikaze" / "arturo.git")

    def claude_locale(self):
        p = self.home / ".local" / "bin" / "claude"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#!/bin/sh\necho 2.1.308\n")
        p.chmod(0o755)

    def finto(self, nome: str, corpo: str):
        p = self.bin / nome
        p.write_text("#!/bin/sh\n" + corpo + "\n")
        p.chmod(0o755)

    def config_vecchia(self):
        c = self.home / ".claude"
        (c / "projects").mkdir(parents=True)
        (c / ".credentials.json").write_text("{}")
        (c / "mio.txt").write_text("mio")

    def lancia(self, repo=None, extra=None):
        env = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}:{PATH_BASE}",
            "SHELL": "/bin/zsh",
            "ARTURO_REPO": repo or self.repo,
            "LANG": "C.UTF-8",
        }
        env.update(extra or {})
        r = subprocess.run(["bash", str(self.script)], env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        return r.returncode, r.stdout + r.stderr

    def backup(self):
        return sorted(p.name for p in self.home.glob(".claude-backup-*"))


def caso_nuova(lab):
    lab.claude_locale()
    lab.config_vecchia()
    rc, out = lab.lancia()
    c = lab.home / ".claude"
    b = lab.backup()
    assert rc == 0, f"rc {rc}\n{out}"
    assert (c / ".git").is_dir() and (c / "README.md").is_file(), "Arturo non è in ~/.claude"
    assert (c / ".credentials.json").is_file() and (c / "projects").is_dir(), "login o sessioni non tornati"
    assert len(b) == 1 and (lab.home / b[0] / "mio.txt").is_file(), f"backup sbagliato: {b}"
    rcfile = (lab.home / ".zshrc").read_text()
    assert rcfile.count(".local/bin") == 1, f"PATH non aggiunto una volta:\n{rcfile}"
    assert "Arturo installato" in out and "tappa-5" in out, out
    # Seconda volta: niente backup nuovo, niente riga doppia.
    rc, out = lab.lancia()
    assert rc == 0 and "già installato" in out, f"rc {rc}\n{out}"
    assert lab.backup() == b, f"backup in più: {lab.backup()}"
    assert (lab.home / ".zshrc").read_text().count(".local/bin") == 1, "riga del PATH doppia"


def caso_senza_cartella(lab):
    lab.claude_locale()
    rc, out = lab.lancia()
    assert rc == 0 and (lab.home / ".claude" / ".git").is_dir(), f"rc {rc}\n{out}"
    assert lab.backup() == [] and "configurazione di prima" not in out, out


def caso_clone_fallito(lab):
    lab.claude_locale()
    lab.config_vecchia()
    rc, out = lab.lancia(repo=str(lab.home / "non-esiste" / "stellakamikaze" / "arturo.git"))
    assert rc == 1, f"rc {rc}\n{out}"
    assert (lab.home / ".claude" / "mio.txt").is_file(), "la cartella di prima non è tornata"
    assert not (lab.home / ".claude" / ".git").exists(), "resta un clone a metà"
    assert lab.backup() == [], f"backup rimasto: {lab.backup()}"
    assert "tornata com'era" in out, out


def caso_python_vecchio(lab):
    lab.claude_locale()
    lab.config_vecchia()
    lab.finto("python3", "exit 1")
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA  python3" in out, f"rc {rc}\n{out}"
    assert (lab.home / ".claude" / "mio.txt").is_file() and lab.backup() == [], "ha toccato ~/.claude"


def caso_senza_claude(lab):
    lab.config_vecchia()
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA  claude" in out and "tappa-3" in out, f"rc {rc}\n{out}"
    assert (lab.home / ".claude" / "mio.txt").is_file() and lab.backup() == [], "ha toccato ~/.claude"


def caso_dentro_claude_code(lab):
    lab.claude_locale()
    rc, out = lab.lancia(extra={"CLAUDECODE": "1"})
    assert rc == 0 and "/exit" in out, f"rc {rc}\n{out}"


def caso_config_di_prima(lab):
    # La ~/.claude di prima ha cose della persona: tornano al loro posto (#3825).
    lab.claude_locale()
    c = lab.home / ".claude"
    (c / "data" / "memory").mkdir(parents=True)
    (c / "data" / "memory" / "nota.md").write_text("mia")
    (c / "CLAUDE.md").write_text("# Gunnar")
    (c / "session-env").mkdir()
    (c / "session-env" / "telemetria.json").write_text('{"spenta": true}')
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    for f, t in (("data/memory/nota.md", "mia"), ("CLAUDE.md", "# Gunnar"), ("session-env/telemetria.json", '{"spenta": true}')):
        assert (c / f).is_file() and (c / f).read_text() == t, f"non torna {f}"


def caso_sincronizzata(lab):
    # Arturo sincronizzato su un repository privato: origin è suo, upstream è Arturo. Non si reinstalla.
    lab.claude_locale()
    c = lab.home / ".claude"
    sh("git", "init", "-q", str(c))
    sh("git", "-C", str(c), "remote", "add", "origin", "https://github.com/qualcuno/config-privata.git")
    sh("git", "-C", str(c), "remote", "add", "upstream", "https://github.com/stellakamikaze/arturo.git")
    (c / "mio.txt").write_text("mio")
    rc, out = lab.lancia()
    assert rc == 0 and "già installato" in out, f"rc {rc}\n{out}"
    assert (c / "mio.txt").is_file() and lab.backup() == [], "ha spostato una config sincronizzata"


CASI = [caso_nuova, caso_config_di_prima, caso_sincronizzata, caso_senza_cartella, caso_clone_fallito, caso_python_vecchio,
        caso_senza_claude, caso_dentro_claude_code]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    script = Path(a.repo) / "sito" / "installa.sh"
    if not script.is_file():
        print(f"FAIL: manca {script}")
        return 1
    passati = 0
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        origine(radice)
        for caso in CASI:
            try:
                caso(Lab(script, radice, caso.__name__))
                passati += 1
                print(f"PASS {caso.__name__}")
            except AssertionError as e:
                print(f"FAIL {caso.__name__}: {e}")
    print(f"installa.sh: {passati}/{len(CASI)}")
    return 0 if passati == len(CASI) else 1


if __name__ == "__main__":
    sys.exit(main())
