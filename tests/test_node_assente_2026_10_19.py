#!/usr/bin/env python3
"""NA01-NA03: Arturo senza node (19/10/2026).

Claude Code si installa anche senza node. La barra in basso (hooks/statusline.js) e l'avviso sul
contesto (hooks/context-monitor.js) girano con node: su un Mac appena installato restavano spenti
in silenzio, e la persona non vedeva né contesto né quota.

NA01 senza node il comando della barra in settings.json esce con 0 e scrive una riga che nomina
     node. Con node la riga è quella di statusline.js.
NA02 senza node l'avvio (hooks/session-start.sh) scrive la riga NODE.
NA03 node fuori dal PATH ma in una cartella nota (Homebrew, ~/.local/node/bin): è il PATH minimo di una
     sessione aperta dal demone di `claude --bg` (15/11/2026). L'avvio non scrive la riga NODE e mette
     la cartella in coda al PATH dei comandi una volta sola (marcatore arturo-path-completo), senza
     ripetere le cartelle che il PATH ha già.

Sulla base dbaefa1 ogni controllo deve fallire (NA03 sulla base fcda2d1) con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from salti_windows import SaltoWindows, dichiara, link

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"
SH_VERO = shutil.which("sh") or "/bin/sh"

ENTRATA = json.dumps({
    "model": {"display_name": "Opus 5.5"},
    "workspace": {"current_dir": "/tmp"},
    "session_id": "na",
    "context_window": {"remaining_percentage": 90},
    "rate_limits": {"five_hour": {"used_percentage": 15}, "seven_day": {"used_percentage": 16}},
})


# Lo stato che l'avvio scrive in ~/.claude: nella copia non entra, e nel repo provato non arriva.
STATO = {".git", "cache", "session-env", "node_modules", "__pycache__"}


def casa_finta(repo: Path, radice: Path) -> Path:
    """Una HOME con ~/.claude copia del repository: il comando usa ~/.claude/hooks/…
    Una copia e non un link: con --repo su un albero vero l'avvio scriveva lì data/contatto.json,
    data/memoria/, cache/ e session-env/, e lanciava il fetch del repository (#5888)."""
    dati = repo / "data"

    def fuori(cartella: str, nomi: list[str]) -> set[str]:
        if Path(cartella) == dati:  # in data/ il repository traccia solo transito.paths
            return {n for n in nomi if n != "transito.paths"}
        return STATO.intersection(nomi)

    home = radice / "home"
    home.mkdir()
    shutil.copytree(repo, home / ".claude", symlinks=True, ignore=fuori)
    return home


def senza_node(radice: Path) -> str:
    """Un PATH con i soli comandi di sistema che servono, e senza node."""
    nomi = ("sh", "bash", "cat", "sed", "find", "git", "hostname", "scutil", "date", "mkdir",
            "grep", "head", "tr", "basename", "dirname", "python3", "uname", "printf", "rm")
    if os.name == "nt":
        # Su Windows un programma di msys aperto da un link non trova la sua DLL: grep falliva in silenzio e NA03
        # scriveva il PATH due volte (#6455). Qui bastano le cartelle vere dei comandi, purché senza node.
        cartelle = []
        for nome in nomi:
            vero = shutil.which(nome)
            cartella = str(Path(vero).parent) if vero else ""
            if cartella and cartella not in cartelle and shutil.which("node", path=cartella) is None:
                cartelle.append(cartella)
        return os.pathsep.join(cartelle)
    bin_ = radice / "bin"
    bin_.mkdir()
    for nome in nomi:
        vero = shutil.which(nome)
        if vero:
            link(bin_ / nome, Path(vero))
    assert shutil.which("node", path=str(bin_)) is None
    return str(bin_)


def per_bash(percorsi: str) -> str:
    """Percorsi separati da os.pathsep, nella forma che l'hook divide sui due punti: su Windows C:\\x è /c/x."""
    if os.name != "nt":
        return percorsi
    fuori = []
    for d in percorsi.split(os.pathsep):
        d = d.replace("\\", "/")
        if len(d) > 1 and d[1] == ":":
            d = "/" + d[0].lower() + d[2:]
        fuori.append(d)
    return ":".join(fuori)


def comando_barra(repo: Path) -> str:
    return json.loads((repo / "settings.json").read_text(encoding="utf-8"))["statusLine"]["command"]


def test_na01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = casa_finta(repo, radice)
        # ARTURO_NODE_DIRS vuota: anche Homebrew e ~/.local/bin senza node, come su una macchina che non l'ha
        # (dal 15/11/2026 il comando della barra cerca node anche lì, per il PATH minimo di ssh).
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": senza_node(radice), "ARTURO_NODE_DIRS": ""}
        p = subprocess.run([SH_VERO, "-c", comando_barra(repo)], input=ENTRATA, env=env,
                           capture_output=True, text=True, timeout=20)
        assert p.returncode == 0 and "node" in p.stdout, \
            f"NA01 senza node la barra non dice cosa manca: rc={p.returncode} out={p.stdout!r} err={p.stderr[-200:]!r}"
        node = shutil.which("node")
        if node:
            env["PATH"] = f"{Path(node).parent}{os.pathsep}{env['PATH']}"
            p = subprocess.run([SH_VERO, "-c", comando_barra(repo)], input=ENTRATA, env=env,
                               capture_output=True, text=True, timeout=20)
            assert p.returncode == 0 and "quota 5 ore 15%" in p.stdout and "manca node" not in p.stdout, \
                f"NA01 con node la barra non è quella di statusline.js: {p.stdout!r}"


def test_na02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = casa_finta(repo, radice)
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": senza_node(radice), "ARTURO_BANCHI_AVVIO": "0",
               "ARTURO_TELEMETRIA": "0", "CLAUDE_PROJECT_DIR": str(radice), "ARTURO_PATH_CANDIDATE": ""}
        p = subprocess.run([BASH_VERO, str(home / ".claude" / "hooks" / "session-start.sh")], input="{}", env=env,
                           cwd=radice, capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert any(r.startswith("NODE: manca node") for r in p.stdout.splitlines()), \
            f"NA02 senza node l'avvio non lo dice: rc={p.returncode} out={p.stdout[-400:]!r}"


def test_na03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = casa_finta(repo, radice)
        brew = radice / "brew-bin"
        brew.mkdir()
        finto = brew / "node"
        finto.write_text("#!/bin/sh\necho v0-finto\n", encoding="utf-8")
        finto.chmod(0o755)
        base = senza_node(radice)
        ambiente = radice / "env-sessione"
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": base, "ARTURO_BANCHI_AVVIO": "0",
               "ARTURO_TELEMETRIA": "0", "CLAUDE_PROJECT_DIR": str(radice), "CLAUDE_ENV_FILE": str(ambiente),
               "ARTURO_PATH_CANDIDATE": per_bash(os.pathsep.join([str(brew), base, str(radice / "non-esiste")]))}
        for giro in (1, 2):
            p = subprocess.run([BASH_VERO, str(home / ".claude" / "hooks" / "session-start.sh")], input="{}", env=env,
                               cwd=radice, capture_output=True, text=True, encoding="utf-8", timeout=60)
            assert not any(r.startswith("NODE:") for r in p.stdout.splitlines()), \
                f"NA03 giro {giro}: node c'è in {brew} ma l'avvio dice che manca: {p.stdout[-400:]!r}"
        testo = ambiente.read_text(encoding="utf-8") if ambiente.exists() else ""
        righe = [r for r in testo.splitlines() if "arturo-path-completo" in r]
        assert len(righe) == 1, f"NA03 il PATH completo va scritto una volta sola: {righe!r}"
        # Su Windows msys chiama /usr/bin nel PATH le cartelle di Git che i candidati del banco scrivono come
        # /c/Program Files/Git/...: rientrano in coda dopo brew-bin, e qui conta solo che la coda parta da lì.
        coda = f'export PATH="$PATH:{per_bash(str(brew))}'
        fini = ('"', ":") if os.name == "nt" else ('"',)
        assert any(coda + f in righe[0] for f in fini), f"NA03 la riga non mette in coda solo {brew}: {righe[0]!r}"


TESTS = {"NA01": test_na01, "NA02": test_na02, "NA03": test_na03}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro, saltati = [], [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except SaltoWindows as e:
                saltati.append(nome)
                dichiara(f"{nome} (base)", e)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
        assert not altro and len(rossi) == len(TESTS) - len(saltati), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    saltati = []
    for nome, test in TESTS.items():
        try:
            test(repo)
        except SaltoWindows as e:
            saltati.append(nome)
            dichiara(nome, e)
    provati = [nome for nome in TESTS if nome not in saltati]
    print(f"PASS {','.join(provati)} controlli={len(provati)}" + (f" saltati={','.join(saltati)}" if saltati else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
