#!/usr/bin/env python3
"""D01-D11: la deriva fra la config della persona e quella di Arturo (hooks/deriva.py).

Ogni caso costruisce un Arturo finto (un repository con settings.json, un comando e due hook), lo
clona come ~/.claude in una HOME finta e cambia la config come farebbe una persona. La telemetria
resta su disco: la coda si legge, niente parte verso la rete. Sulla base f750408, prima della
deriva, ogni controllo deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IMPOSTAZIONI = {
    "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": "bash ~/.claude/hooks/session-start.sh"}]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/bash-dispatcher.sh"}]}],
    },
    "permissions": {"deny": ["Bash(rm -rf /)"]},
}


def git(cartella: Path, *argomenti: str) -> str:
    return subprocess.run(["git", "-C", str(cartella), *argomenti], check=True, capture_output=True, text=True).stdout


class Lab:
    def __init__(self, repo: Path, **env):
        self.repo = repo
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-d."))
        atexit.register(shutil.rmtree, self.dir, True)
        self.home = self.dir / "home"
        self.home.mkdir()
        self.arturo = self.dir / "arturo"
        (self.arturo / "commands").mkdir(parents=True)
        (self.arturo / "hooks").mkdir()
        (self.arturo / "settings.json").write_text(json.dumps(IMPOSTAZIONI, indent=2), encoding="utf-8")
        (self.arturo / "commands" / "inizio.md").write_text("# /inizio\n\nApri la sessione.\n", encoding="utf-8")
        (self.arturo / "hooks" / "bash-dispatcher.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        # Ogni script citato da IMPOSTAZIONI esiste: dal 15/10/2026 uno mancante è config rotta (rotta-hook).
        (self.arturo / "hooks" / "session-start.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        (self.arturo / "README.md").write_text("Arturo\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.arturo)], check=True)
        for chiave, valore in (("user.name", "t"), ("user.email", "t@example.org"), ("commit.gpgsign", "false")):
            git(self.arturo, "config", chiave, valore)
        git(self.arturo, "add", "-A")
        git(self.arturo, "commit", "-q", "-m", "seme")
        self.claude = self.home / ".claude"
        subprocess.run(["git", "clone", "-q", str(self.arturo), str(self.claude)], check=True)
        for chiave, valore in (("user.name", "p"), ("user.email", "p@example.org"), ("commit.gpgsign", "false")):
            git(self.claude, "config", chiave, valore)
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TELEMETRIA_URL="http://127.0.0.1:9")
        for chiave in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_OGGI"):
            self.env.pop(chiave, None)
        self.env.update(env)

    def scrivi(self, nome: str, testo: str, commit: bool = True) -> None:
        f = self.claude / nome
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(testo, encoding="utf-8")
        if commit:
            git(self.claude, "add", "-f", nome)
            git(self.claude, "commit", "-q", "-m", f"mio: {nome}")

    def deriva(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.repo / "hooks" / "deriva.py"), str(self.claude)],
                              capture_output=True, text=True, env=self.env, timeout=60)

    def coda(self) -> list:
        f = self.claude / "data" / "telemetria" / "coda.jsonl"
        righe = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
        return [(e["evento"], e["valore"]) for e in map(json.loads, righe)]

    def stato(self) -> dict:
        f = self.claude / "session-env" / "telemetria.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def test_d01(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.deriva()
    assert r.returncode == 0 and r.stdout == "", f"D01 una config uguale ad Arturo stampa qualcosa: {r.stdout!r} {r.stderr!r}"
    assert lab.coda() == [], f"D01 un'installazione pulita manda una deriva: {lab.coda()}"
    assert (repo / "hooks" / "deriva.py").exists(), "D01 manca hooks/deriva.py"


def test_d02(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("commands/inizio.md", "# /inizio\n\nApri la sessione.\n\n## Mie aggiunte\nTabella progetti.\n")
    r = lab.deriva()
    assert r.stdout.startswith("DERIVA:") and "/inizio" in r.stdout and "/aggiorna personale" in r.stdout, \
        f"D02 la riga non dice cosa fare: {r.stdout!r} {r.stderr!r}"
    assert lab.coda() == [("deriva", "insieme:1"), ("deriva", "file:commands/inizio.md")], f"D02 coda: {lab.coda()}"


def test_d03(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("commands/inizio.md", "# /inizio\n\naltro\n", commit=False)
    lab.deriva()
    prima = lab.coda()
    lab.deriva()
    assert prima and lab.coda() == prima, f"D03 un elenco invariato si registra di nuovo: {lab.coda()}"
    assert lab.stato().get("deriva_inviata") == ["file:commands/inizio.md"], "D03 lo stato non ricorda l'elenco inviato"


def test_d04(repo: Path) -> None:
    lab = Lab(repo)
    mie = json.loads(json.dumps(IMPOSTAZIONI))
    del mie["hooks"]["PreToolUse"]
    mie["permissions"]["allow"] = ["Bash(ls)"]
    lab.scrivi("settings.json", json.dumps(mie))
    r = lab.deriva()
    assert "bash-dispatcher.sh" in r.stdout and "non girano" in r.stdout, f"D04 hook tolto non detto: {r.stdout!r}"
    assert lab.coda() == [("deriva", "insieme:1"), ("deriva", "hook:bash-dispatcher.sh")], \
        f"D04 coda (settings.json non deve comparire come file): {lab.coda()}"


def test_d05(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("settings.local.json", json.dumps({"disableAllHooks": True}), commit=False)
    r = lab.deriva()
    assert "disableAllHooks" in r.stdout, f"D05 hook spenti in settings.local.json non detti: {r.stdout!r}"
    assert ("deriva", "hook:tutti") in lab.coda(), f"D05 coda: {lab.coda()}"


def test_d06(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("commands/cliente-rossi.md", "# un comando mio\n")
    lab.scrivi("CLAUDE.md", "# chi sono\n", commit=False)
    lab.scrivi("hooks/bash-dispatcher.sh", "#!/bin/bash\n# mio\nexit 0\n")
    r = lab.deriva()
    valori = [v for _, v in lab.coda()]
    assert "file:hooks/bash-dispatcher.sh" in valori, f"D06 una guardia modificata non esce: {valori}"
    assert not any("cliente-rossi" in v or "CLAUDE" in v for v in valori) and "cliente-rossi" not in r.stdout, \
        f"D06 esce il nome di un file della persona: {valori} {r.stdout!r}"


def test_d07(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("settings.json", "{ rotto", commit=False)
    lab.deriva()
    assert ("config", "rotta-settings") in lab.coda(), f"D07 la config rotta non si registra: {lab.coda()}"
    assert not any(v.startswith("hook:") for _, v in lab.coda()), "D07 con settings.json rotto gli hook risultano tolti"
    assert lab.stato().get("ultimo_tentativo") == 0, "D07 la config rotta aspetta le 6 ore per partire"
    lab.deriva()
    assert lab.coda().count(("config", "rotta-settings")) == 1, f"D07 la config rotta si registra a ogni avvio: {lab.coda()}"


def test_d08(repo: Path) -> None:
    lab = Lab(repo, ARTURO_TELEMETRIA="0")
    lab.scrivi("commands/inizio.md", "# /inizio\n\nmio\n")
    r = lab.deriva()
    assert r.stdout.startswith("DERIVA:"), "D08 a telemetria spenta la persona non vede la deriva"
    assert lab.coda() == [] and "deriva_inviata" not in lab.stato(), f"D08 a telemetria spenta si registra: {lab.coda()}"


def test_d09(repo: Path) -> None:
    lab = Lab(repo)
    lab.scrivi("commands/inizio.md", "# /inizio\n\nmio\n", commit=False)
    lab.deriva()
    git(lab.claude, "checkout", "--", "commands/inizio.md")
    r = lab.deriva()
    assert r.stdout == "", f"D09 deriva rientrata ma la riga resta: {r.stdout!r}"
    assert lab.coda()[-1] == ("deriva", "insieme:0"), f"D09 il rientro non si registra: {lab.coda()}"


def test_d10(repo: Path) -> None:
    # Con un repository personale come origin, Arturo è upstream: la deriva si misura da lì.
    lab = Lab(repo)
    personale = lab.dir / "personale.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(lab.claude), str(personale)], check=True)
    git(lab.claude, "remote", "rename", "origin", "upstream")
    git(lab.claude, "remote", "add", "origin", str(personale))
    git(lab.claude, "fetch", "-q", "origin")
    lab.scrivi("commands/inizio.md", "# /inizio\n\nmio\n")
    git(lab.claude, "push", "-q", "origin", "HEAD:main")
    git(lab.claude, "fetch", "-q", "origin")
    lab.deriva()
    assert ("deriva", "file:commands/inizio.md") in lab.coda(), f"D10 con upstream la deriva si misura da origin: {lab.coda()}"
    avvio = (repo / "hooks" / "session-start.sh").read_text(encoding="utf-8")
    assert "hooks/deriva.py" in avvio and avvio.index("deriva.py") < avvio.index("telemetria.py\" avvio"), \
        "D10 session-start non lancia la deriva prima della telemetria"


def test_d11(repo: Path) -> None:
    # 16/10/2026, dal ciclo del lunedì: una guardia modificata ha un avviso suo, col ripristino;
    # un hook di sessione modificato va nel file personale, come un comando.
    lab = Lab(repo)
    lab.scrivi("hooks/bash-dispatcher.sh", "#!/bin/bash\n# tolta la guardia sugli invii\nexit 0\n")
    r = lab.deriva()
    assert "guardie di Arturo hooks/bash-dispatcher.sh" in r.stdout and "personale ripristina" in r.stdout \
        and "git -C ~/.claude diff " in r.stdout, f"D11 la guardia modificata non ha il suo avviso: {r.stdout!r}"
    assert "un aggiornamento può andare in conflitto" not in r.stdout, f"D11 la guardia è contata fra gli altri file: {r.stdout!r}"
    lab = Lab(repo)
    lab.scrivi("hooks/session-start.sh", "#!/bin/bash\necho mio\nexit 0\n")
    r = lab.deriva()
    assert "hooks/session-start.sh: il prossimo /aggiorna sposta" in r.stdout, \
        f"D11 l'hook di sessione modificato non va nel file personale: {r.stdout!r}"


TESTS = {"D01": test_d01, "D02": test_d02, "D03": test_d03, "D04": test_d04, "D05": test_d05,
         "D06": test_d06, "D07": test_d07, "D08": test_d08, "D09": test_d09, "D10": test_d10, "D11": test_d11}


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
            except (AssertionError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError, subprocess.SubprocessError):
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
