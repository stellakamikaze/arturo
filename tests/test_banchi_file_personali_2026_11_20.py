#!/usr/bin/env python3
"""BP01-BP03: i banchi all'avvio non danno il rosso per un hook che la persona ha scritto per sé (20/11/2026, #5383).

L'11/11/2026 test_hook_utf8.py era rosso su un'installazione con U08 su hooks/notifica-focus.sh: un hook
personale, registrato nel settings.json della persona, che chi mantiene Arturo non può correggere. Il rosso
partiva con la telemetria e alla persona non serviva.

BP01 U08 salta un hook .sh personale quando ARTURO_FILE_ARTURO non lo elenca, e lo giudica senza la variabile.
BP02 U01 e U07 fanno lo stesso con un hooks/*.py personale che legge stdin come testo.
BP03 banchi-avvio.sh mette in ARTURO_FILE_ARTURO i file di Arturo: quelli della base con origin/main, o con
     upstream/main quando la persona ha un remote upstream. Un file personale committato resta fuori.

Sulla base 4801ee0 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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
PERSONALE_SH = "#!/usr/bin/env bash\npython3 -c 'import sys; print(sys.stdin.read())'\n"
PERSONALE_PY = "import sys\nprint(sys.stdin.read())\n"


def _copia(repo: Path, radice: Path) -> Path:
    copia = radice / "claude"
    for parte in ("hooks", "bin", "tests"):
        shutil.copytree(repo / parte, copia / parte, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(repo / "settings.json", copia / "settings.json")
    return copia


def _elenco_arturo(copia: Path, radice: Path) -> Path:
    """I file della copia prima dell'hook personale: nel gate la base non è un repository git."""
    nomi = sorted(p.relative_to(copia).as_posix() for p in copia.rglob("*") if p.is_file())
    f = radice / "file-arturo.txt"
    f.write_text("\n".join(nomi) + "\n", encoding="utf-8")
    return f


def _registra(copia: Path, comando: str) -> None:
    f = copia / "settings.json"
    dati = json.loads(f.read_text(encoding="utf-8"))
    dati.setdefault("hooks", {}).setdefault("Notification", []).append(
        {"hooks": [{"type": "command", "command": comando}]})
    f.write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")


def _utf8(copia: Path, **extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("ARTURO_FILE_ARTURO", None)
    env.update(extra)
    return subprocess.run([sys.executable, "-B", str(copia / "tests" / "test_hook_utf8.py"), "--repo", str(copia)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)


def _personale(repo: Path, codice: str, file: str, corpo: str, comando: str) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        copia = _copia(repo, radice)
        elenco = _elenco_arturo(copia, radice)
        (copia / "hooks" / file).write_text(corpo, encoding="utf-8")
        _registra(copia, comando)
        sigla = "U08" if file.endswith(".sh") else "U01"
        senza = _utf8(copia)
        assert senza.returncode != 0 and sigla in senza.stderr and file in senza.stderr, \
            f"{codice} senza l'elenco il file personale non è giudicato: rc={senza.returncode} {senza.stderr[-300:]!r}"
        con = _utf8(copia, ARTURO_FILE_ARTURO=str(elenco))
        assert con.returncode == 0 and "PASS" in con.stdout, \
            f"{codice} il file personale {file} dà ancora il rosso: rc={con.returncode} {con.stderr[-300:]!r}"


def test_bp01(repo: Path) -> None:
    _personale(repo, "BP01", "notifica-focus.sh", PERSONALE_SH, "bash ~/.claude/hooks/notifica-focus.sh")


def test_bp02(repo: Path) -> None:
    _personale(repo, "BP02", "mio_hook.py", PERSONALE_PY, "python3 ~/.claude/hooks/mio_hook.py")


def _git(cartella: Path, *argomenti: str) -> str:
    return subprocess.run(["git", "-C", str(cartella), "-c", "user.name=prova", "-c", "user.email=prova@example.com",
                           "-c", "commit.gpgsign=false", *argomenti],
                          capture_output=True, text=True, check=True).stdout


SPIA = """import os
elenco = os.environ.get("ARTURO_FILE_ARTURO")
nomi = set(open(elenco, encoding="utf-8").read().splitlines()) if elenco else set()
assert "hooks/session-start.sh" in nomi and "hooks/notifica-focus.sh" not in nomi, f"Error elenco: {sorted(nomi)}"
"""


def _arturo_finto(repo: Path, cartella: Path) -> None:
    """Un Arturo minimo: banchi-avvio.sh vero, ogni banco passa, test_hook_utf8.py controlla l'elenco."""
    (cartella / "tests").mkdir(parents=True)
    (cartella / "hooks").mkdir()
    shutil.copy2(repo / "tests" / "banchi-avvio.sh", cartella / "tests" / "banchi-avvio.sh")
    testo = (repo / "tests" / "banchi-avvio.sh").read_text(encoding="utf-8")
    elenco = next(r for r in testo.splitlines() if r.startswith('BANCHI="')).split('"')[1].split()
    for nome in elenco:
        (cartella / "tests" / nome).write_text(SPIA if nome == "test_hook_utf8.py" else "pass\n", encoding="utf-8")
    (cartella / "hooks" / "session-start.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    # Dal 21/11/2026 (#6216) banchi-avvio.sh chiede la base a hooks/deriva.py --base.
    for nome in ("deriva.py", "radici.py", "fiducia.py"):
        if (repo / "hooks" / nome).exists():
            shutil.copy2(repo / "hooks" / nome, cartella / "hooks" / nome)
    _git(cartella, "init", "-q", "-b", "main")
    _git(cartella, "add", "-A")
    _git(cartella, "commit", "-q", "-m", "arturo")


def _personalizza(config: Path) -> None:
    (config / "hooks" / "notifica-focus.sh").write_text(PERSONALE_SH, encoding="utf-8")
    _git(config, "add", "hooks/notifica-focus.sh")
    _git(config, "commit", "-q", "-m", "mio hook")


def _avvio(config: Path, home: Path) -> str:
    env = dict(os.environ, ARTURO_DIR=str(config), HOME=str(home), USERPROFILE=str(home),
               ARTURO_TELEMETRIA="0", ARTURO_TELEMETRIA_URL="http://127.0.0.1:9")
    env.pop("ARTURO_FILE_ARTURO", None)
    subprocess.run([BASH, str(config / "tests" / "banchi-avvio.sh")], env=env, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=300)
    f = config / "cache" / "banchi-ultimo-esito.txt"
    return f.read_text(encoding="utf-8") if f.exists() else "(nessun esito)"


def test_bp03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = radice / "home"
        (home / ".claude").mkdir(parents=True)
        arturo = radice / "arturo"
        _arturo_finto(repo, arturo)
        # Forma clone: origin è Arturo.
        config = radice / "config"
        subprocess.run(["git", "clone", "-q", str(arturo), str(config)], check=True, capture_output=True)
        _personalizza(config)
        esito = _avvio(config, home)
        assert esito.startswith("VERDE"), f"BP03 con origin/main l'hook personale entra fra i file di Arturo: {esito[:300]}"
        # Fork della persona come origin, Arturo come upstream: origin/main ha già l'hook personale.
        fork = radice / "fork"
        subprocess.run(["git", "clone", "-q", "--bare", str(config), str(fork)], check=True, capture_output=True)
        config2 = radice / "config2"
        subprocess.run(["git", "clone", "-q", str(fork), str(config2)], check=True, capture_output=True)
        _git(config2, "remote", "add", "upstream", str(arturo))
        _git(config2, "fetch", "-q", "upstream")
        esito = _avvio(config2, home)
        assert esito.startswith("VERDE"), f"BP03 con upstream/main l'hook personale entra fra i file di Arturo: {esito[:300]}"


TESTS = {"BP01": test_bp01, "BP02": test_bp02, "BP03": test_bp03}


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
