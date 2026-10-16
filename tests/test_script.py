#!/usr/bin/env python3
"""Z01-Z08: gli script portati dalla config dell'autore il 15/10/2026.

Z01 bin/gate-run.sh: il gate parte solo se il veleno è rosso col motivo atteso (banco test_gate_run.sh).
Z02 bin/validation-gate-lang.sh: shared/validation-gate.md lo chiama e legge l'exit da file, mai da
    PIPESTATUS; il banco tests/gate/test_gate.sh è verde; senza pytest il gate esce 2, non 0.
Z03 bin/bgjob.sh: esito su file, job in corso, stop, ripiego /proc dove ps non ha -o (Git Bash).
Z04 bin/cleanup-stale-plugins.sh: la prova a vuoto elenca i plugin non attivi e non disinstalla niente.
Z05 bin/sonda_servito.py: il selftest (servito uguale, diverso, 404, redirect al login).
Z06 bin/monthly-cleanup.sh: --prova non tocca niente, la cartella dei progetti è facoltativa,
    nessun percorso personale.
Z07 /system-audit: comandi fantasma, plugin non attivi e il banco avvelenato tests/banco-gate.sh.
Z08 tools/scrapling: niente livello stealth, un blocco consiglia il browser, /setup chiede prima.

Sulla base cbd8305 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASH = shutil.which("bash") or "bash"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def esiste(repo: Path, rel: str, codice: str) -> Path:
    p = repo / rel
    assert p.is_file(), f"{codice} manca {rel}"
    return p


def lancia(argv: list, codice: str, env: dict | None = None, cwd: str | None = None,
           timeout: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                              cwd=cwd, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise AssertionError(f"{codice} scaduto il tempo: {argv[:3]}")


def stub(cartella: Path, nome: str, corpo: str) -> None:
    f = cartella / nome
    f.write_text(corpo, encoding="utf-8")
    f.chmod(0o755)


# Un pytest minimo: esegue le funzioni test_* dei file test_*.py della cartella corrente.
# Il banco non dipende da un pytest installato sulla macchina.
PYTEST_MINIMO = """#!/usr/bin/env python3
import glob, importlib.util, os, sys
if "--version" in sys.argv:
    print("pytest minimo del banco")
    sys.exit(0)
fatti = falliti = 0
for f in sorted(glob.glob("test_*.py")):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k in sorted(dir(m)):
        if k.startswith("test_"):
            fatti += 1
            try:
                getattr(m, k)()
            except AssertionError:
                falliti += 1
print("%d passed, %d failed" % (fatti - falliti, falliti))
sys.exit(1 if falliti else 0)
"""


def test_z01(repo: Path) -> None:
    gr = esiste(repo, "bin/gate-run.sh", "Z01")
    banco = esiste(repo, "tests/test_gate_run.sh", "Z01")
    with tempfile.TemporaryDirectory() as d:
        r = lancia([BASH, str(banco)], "Z01", env=dict(os.environ, GATE_RUN=str(gr), TMPDIR=d), cwd=d)
    assert r.returncode == 0 and "totale casi: 7 · verdi: 7" in r.stdout, f"Z01 banco di gate-run rosso: {r.stdout[-600:]}"
    gate = read(repo / "shared" / "validation-gate.md")
    assert "bin/gate-run.sh" in gate and "--poison" in gate and "--expect" in gate, \
        "Z01 shared/validation-gate.md non dice come eseguire un banco nuovo con gate-run.sh"


def test_z02(repo: Path) -> None:
    gl = esiste(repo, "bin/validation-gate-lang.sh", "Z02")
    banco = esiste(repo, "tests/gate/test_gate.sh", "Z02")
    gate = read(repo / "shared" / "validation-gate.md")
    assert "PIPESTATUS[0]" not in gate and "${PIPESTATUS" not in gate, "Z02 validation-gate.md legge ancora PIPESTATUS"
    assert "bin/validation-gate-lang.sh" in gate and 'echo $? > "$G.rc"' in gate, \
        "Z02 validation-gate.md non chiama lo script o non scrive l'exit su file"
    testo = read(gl)
    for parola in ("Bal" + "thasar", "mel" + "chior", "/Users/"):
        assert parola.lower() not in testo.lower(), f"Z02 validation-gate-lang.sh nomina una macchina personale: {parola}"
    with tempfile.TemporaryDirectory() as d:
        finti = Path(d) / "pytest-minimo"
        finti.mkdir()
        stub(finti, "pytest", PYTEST_MINIMO)
        env = dict(os.environ, PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""), TMPDIR=d)
        r = lancia([BASH, str(banco)], "Z02", env=env, timeout=300)
        assert r.returncode == 0 and "0 FAIL" in r.stdout, f"Z02 banco del gate rosso: {r.stdout[-900:]}"
        # Senza pytest (né l'eseguibile né python -m pytest) il gate non può dire verde.
        senza = Path(d) / "senza-pytest"
        senza.mkdir()
        rotto = "#!/bin/sh\nexit 1\n"
        for nome in ("pytest", "python3", "python"):
            stub(senza, nome, rotto)
        for nome in ("ruff", "mypy"):
            stub(senza, nome, "#!/bin/sh\nexit 0\n")
        prog = Path(d) / "prog"
        prog.mkdir()
        (prog / "requirements.txt").write_text("# req\n", encoding="utf-8")
        (prog / "test_a.py").write_text("def test_a():\n    assert 1 == 2\n", encoding="utf-8")
        env = dict(os.environ, PATH=str(senza) + os.pathsep + "/usr/bin" + os.pathsep + "/bin")
        r = lancia([BASH, str(gl), "--dir", str(prog), "--mode", "quick"], "Z02", env=env)
        assert r.returncode == 2 and "INCONCLUSIVO" in r.stdout, \
            f"Z02 senza pytest il gate esce {r.returncode} invece di 2: {r.stdout[-500:]}"


def test_z03(repo: Path) -> None:
    bg = esiste(repo, "bin/bgjob.sh", "Z03")
    doc = read(repo / "shared" / "lavori-lunghi.md")
    assert "bin/bgjob.sh" in doc, "Z03 shared/lavori-lunghi.md non spiega bgjob.sh"
    assert "shared/lavori-lunghi.md" in read(repo / "commands" / "setup.md"), \
        "Z03 /setup non propone la regola dei lavori lunghi per il CLAUDE.md"
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, BGJOB_DIR=str(Path(d) / "jobs"))

        def bgjob(*a: str) -> subprocess.CompletedProcess:
            return lancia([BASH, str(bg)] + list(a), "Z03", env=env, timeout=30)

        r = bgjob("start", "prova", "--", BASH, "-c", "echo ciao; exit 3")
        assert r.returncode == 0 and "marker:" in r.stdout, f"Z03 start non parte: {r.stdout}{r.stderr}"
        cartella = Path(r.stdout.split("job:", 1)[1].split("\n", 1)[0].strip())
        fine = time.time() + 15
        while not (cartella / "exit").exists() and time.time() < fine:
            time.sleep(0.2)
        r = bgjob("status", "prova")
        assert r.returncode == 1 and "finito exit=3" in r.stdout, f"Z03 esito non letto dal marker: {r.returncode} {r.stdout}"
        assert "ciao" in read(cartella / "log"), "Z03 il log non ha l'output del comando"

        r = bgjob("start", "lungo", "--", "sleep", "30")
        assert r.returncode == 0, f"Z03 start del job lungo: {r.stderr}"
        r = bgjob("status", "lungo")
        assert r.returncode == 2 and "in corso" in r.stdout, f"Z03 job in corso non riconosciuto: {r.returncode} {r.stdout}"
        r = bgjob("stop", "lungo")
        assert "SIGTERM" in r.stdout, f"Z03 stop non ferma il job: {r.stdout}"
        time.sleep(0.5)
        r = bgjob("status", "lungo")
        assert r.returncode in (1, 3), f"Z03 dopo stop il job risulta ancora vivo: {r.returncode} {r.stdout}"

        # Git Bash: il ps non ha -o, l'ora di avvio si legge da /proc/<pid>/stat.
        finti = Path(d) / "gitbash"
        finti.mkdir()
        stub(finti, "ps", '#!/bin/sh\necho "Usage: ps [-aefls] [-u UID] [-p PID]" >&2\nexit 1\n')
        proc = Path(d) / "proc" / "4242"
        proc.mkdir(parents=True)
        campi = " ".join(str(i) for i in range(4, 22))
        (proc / "stat").write_text(f"4242 (nome (con) spazi) S {campi} 987654 23 24\n", encoding="utf-8")
        env2 = dict(env, PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""), BGJOB_PROC=str(Path(d) / "proc"))
        r = lancia([BASH, str(bg), "_avvio", "4242"], "Z03", env=env2)
        assert r.stdout.strip() == "proc:987654", f"Z03 ripiego /proc per Git Bash sbagliato: {r.stdout!r} {r.stderr!r}"


def casa_finta(d: str, settings: dict, installati: dict | None) -> Path:
    casa = Path(d) / "casa"
    (casa / ".claude" / "plugins").mkdir(parents=True)
    (casa / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    if installati is not None:
        (casa / ".claude" / "plugins" / "installed_plugins.json").write_text(json.dumps(installati), encoding="utf-8")
    return casa


def test_z04(repo: Path) -> None:
    sp = esiste(repo, "bin/cleanup-stale-plugins.sh", "Z04")
    with tempfile.TemporaryDirectory() as d:
        finti = Path(d) / "bin"
        finti.mkdir()
        segno = Path(d) / "claude-chiamato"
        stub(finti, "claude", f"#!/bin/sh\ntouch '{segno}'\n")
        casa = casa_finta(d, {"enabledPlugins": {"attivo@x": True, "spento@x": False}},
                          {"plugins": {"attivo@x": [], "spento@x": [], "orfano@y": []}})
        env = dict(os.environ, HOME=str(casa), USERPROFILE=str(casa),
                   PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""))
        r = lancia([BASH, str(sp), "--dry-run"], "Z04", env=env)
        assert r.returncode == 0 and "  - orfano@y" in r.stdout and "  - spento@x" in r.stdout \
            and "attivo@x" not in r.stdout, f"Z04 la prova a vuoto non elenca i plugin giusti: {r.stdout}"
        assert not segno.exists(), "Z04 la prova a vuoto ha chiamato claude"
        (casa / ".claude" / "plugins" / "installed_plugins.json").unlink()
        r = lancia([BASH, str(sp), "--dry-run"], "Z04", env=env)
        assert r.returncode == 0 and "Nessun plugin" in r.stdout, f"Z04 senza plugin installati: {r.returncode} {r.stdout}{r.stderr}"


def test_z05(repo: Path) -> None:
    sonda = esiste(repo, "bin/sonda_servito.py", "Z05")
    r = lancia([sys.executable, "-B", str(sonda), "--selftest"], "Z05", timeout=60)
    assert r.returncode == 0 and "totale casi: 4 · rossi: 0" in r.stdout, f"Z05 selftest della sonda rosso: {r.stdout}{r.stderr}"
    assert "bin/sonda_servito.py" in read(repo / "shared" / "validation-gate.md"), \
        "Z05 validation-gate.md non dice di sondare il servito dopo un deploy"


def test_z06(repo: Path) -> None:
    mc = esiste(repo, "bin/monthly-cleanup.sh", "Z06")
    testo = read(mc)
    for parola in ("Documents/" + "ClaudeCode", "com." + "fede" + "rico", "Spark", "Beep" + "er", "_orphans"):
        assert parola not in testo, f"Z06 monthly-cleanup.sh ha ancora un percorso personale: {parola}"
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d) / "casa"
        paste = casa / ".claude" / "paste-cache"
        paste.mkdir(parents=True)
        progetti = casa / "progetti"
        progetti.mkdir()
        vecchio, nuovo, sciolto = paste / "vecchio.txt", paste / "nuovo.txt", progetti / "sciolto.txt"
        for f in (vecchio, nuovo, sciolto):
            f.write_text("x", encoding="utf-8")
        antico = time.time() - 400 * 86400
        os.utime(vecchio, (antico, antico))
        os.utime(sciolto, (antico, antico))
        env = dict(os.environ, HOME=str(casa), USERPROFILE=str(casa), PULIZIA_CACHE="0")
        env.pop("PULIZIA_CARTELLA_PROGETTI", None)
        r = lancia([BASH, str(mc), "--prova"], "Z06", env=dict(env, PULIZIA_CARTELLA_PROGETTI=str(progetti)))
        assert r.returncode == 0 and vecchio.exists() and sciolto.exists() and "sposterei" in r.stdout, \
            f"Z06 --prova ha toccato file o non elenca: {r.stdout}"
        r = lancia([BASH, str(mc)], "Z06", env=env)
        assert r.returncode == 0 and not vecchio.exists() and nuovo.exists(), f"Z06 paste-cache non pulita: {r.stdout}"
        assert sciolto.exists(), "Z06 senza PULIZIA_CARTELLA_PROGETTI la pulizia ha spostato file dei progetti"
        r = lancia([BASH, str(mc)], "Z06", env=dict(env, PULIZIA_CARTELLA_PROGETTI=str(progetti)))
        archiviati = list((progetti / "_archivio").glob("*/sciolto.txt"))
        assert not sciolto.exists() and archiviati, f"Z06 il file sciolto non è archiviato: {r.stdout}"
        if platform.system() == "Darwin":
            la = casa / "Library" / "LaunchAgents"
            la.mkdir(parents=True)
            (la / "com.bancoprova.servizio.plist").write_text("<plist/>", encoding="utf-8")
            r = lancia([BASH, str(mc), "--prova"], "Z06", env=dict(env, PULIZIA_PREFISSI_LAUNCHAGENT="com.bancoprova."))
            assert "com.bancoprova.servizio" in r.stdout, f"Z06 il prefisso dei LaunchAgent non è configurabile: {r.stdout}"


def test_z07(repo: Path) -> None:
    banco = esiste(repo, "skills/system-audit/tests/banco-gate.sh", "Z07")
    skill = read(repo / "skills" / "system-audit" / "SKILL.md")
    assert "tests/banco-gate.sh" in skill and "Comandi fantasma" in skill and "Plugin" in skill, \
        "Z07 SKILL.md di /system-audit non descrive i gate nuovi o il banco"
    with tempfile.TemporaryDirectory() as d:
        r = lancia([BASH, str(banco), str(repo)], "Z07", env=dict(os.environ, TMPDIR=d), timeout=600)
    assert r.returncode == 0 and "rossi: 0" in r.stdout, f"Z07 banco avvelenato dell'audit rosso: {r.stdout[-1200:]}"


class PaginaFinta:
    def __init__(self, titolo: str, testo: str) -> None:
        self.titolo, self.testo = titolo, testo

    def get_all_text(self) -> str:
        return self.testo

    def css(self, _sel: str) -> "PaginaFinta":
        return self

    def get(self) -> str:
        return self.titolo


def test_z08(repo: Path) -> None:
    base = repo / "tools" / "scrapling"
    for nome in ("scrape.py", "scrape", "setup.sh", "banco.sh", "README.md", ".gitignore"):
        esiste(repo, f"tools/scrapling/{nome}", "Z08")
    py = read(base / "scrape.py")
    for vietato in ("StealthyFetcher", "--stealth", "solve_cloudflare", 'impersonate="chrome"', "google_search"):
        assert vietato not in py, f"Z08 scrape.py ha ancora il livello stealth: {vietato}"
    assert "impersonate=None" in py and "stealthy_headers=False" in py, "Z08 Fetcher finge ancora di essere Chrome"
    righe_setup = [r for r in read(base / "setup.sh").splitlines() if not r.lstrip().startswith("#")]
    assert not any("scrapling install" in r for r in righe_setup), "Z08 setup.sh scarica i browser dello stealth"
    assert ".venv/" in read(base / ".gitignore"), "Z08 il venv di scrape può finire nel repository"
    spec = importlib.util.spec_from_file_location("scrape_banco", str(base / "scrape.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    rc, msg = modulo.esito(403, False)
    assert rc == 3 and "browser" in msg, f"Z08 un 403 non consiglia il browser: {rc} {msg}"
    assert modulo.esito(200, True)[0] == 3, "Z08 una pagina di verifica anti-bot passa come pagina vera"
    assert modulo.esito(404, False)[0] == 2, "Z08 un 404 viene scambiato per un blocco"
    assert modulo.esito(200, False) == (0, ""), "Z08 una pagina buona non passa"
    assert modulo.e_challenge(PaginaFinta("Just a moment...", "Checking your browser")), "Z08 challenge non riconosciuta"
    assert not modulo.e_challenge(PaginaFinta("Bandi aperti", "Contributi per la cultura")), "Z08 pagina vera presa per challenge"
    setup = read(repo / "commands" / "setup.md")
    assert "tools/scrapling/setup.sh" in setup and "300 MB" in setup and "sì" in setup.split("FASE 8b", 1)[-1][:1500], \
        "Z08 /setup non propone scrape come fase facoltativa con il sì prima"


TESTS = {"Z01": test_z01, "Z02": test_z02, "Z03": test_z03, "Z04": test_z04,
         "Z05": test_z05, "Z06": test_z06, "Z07": test_z07, "Z08": test_z08}


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
