#!/usr/bin/env python3
"""IG01-IG04: l'igiene del repository pubblico regge e non contiene i nomi che cerca (17/10/2026, #3505).

Fino al 16/10/2026 i test tenevano i nomi della config privata spezzati in due ("xx", "yy"): leggibili
da chiunque apra il file, e il controllo li cercava solo interi o staccati da uno spazio o un trattino.

IG01 il controllo nuovo (tests/igiene.py, accanto a questo banco) non trova niente nel repository: né
     i nomi né le loro metà. Sulla base 93f323e trova le tuple spezzate dei test.
IG02 il controllo del repository riconosce un termine anche con un punto in mezzo, un a capo dopo un
     trattino, un carattere invisibile, una lettera cirillica, uno spazio, le maiuscole, la forma larga.
     Il termine di prova è inventato: le impronte vere non si mettono alla prova senza scriverle.
IG03 il controllo legge anche i percorsi dei file e i messaggi dei commit dell'intervallo, e il rapporto
     non ripete mai il termine.
IG04 un workflow di GitHub Actions lancia il solo controllo di igiene su ogni pull request, su ogni push, su ogni branch, in
     sola lettura, e solo nel repository pubblico di Arturo (19/10/2026, segnalazione n. 4).
IG05 (review del 7/11/2026) le persone e gli id veri usciti nei file stanno nel controllo di default, e i byte
     di un file binario non contano come testo, mentre il suo percorso sì.
IG06 (10/11/2026) l'hook .githooks/pre-push blocca un nome nel messaggio o in un file del commit spinto verso
     il repository pubblico, lascia passare un push pulito, un file non salvato e un altro repository.
IG07 (10/11/2026) fuori da dev il workflow toglie dall'intervallo i commit che dev ha già: un nome già
     segnalato su dev non manda di nuovo l'email da main o da un ramo che unisce dev.
IG08 (18/11/2026, #6063) il workflow toglie anche i commit che un altro ramo pubblico ha già: il primo push di
     un ramo che porta commit vecchi e unirlo in dev non danno rosso. Un ramo che contiene già il commit spinto
     non conta, così due rami spinti insieme non si tolgono a vicenda un nome nuovo. In una pull request contano
     tutti i rami di origin, e il commit di un fork resta controllato. Il passo del workflow gira davvero, in bash.
IG09 (22/11/2026, #6425) l'hook pre-push toglie, come il workflow, i commit che un ramo del remoto ha già: main
     che avanza fino a un commit già su origin/dev, col nome nel messaggio, parte. Un nome in un commit nuovo
     sopra resta bloccato, e così un commit che solo un altro remoto conosce.
IG10 (revisione del 22/11/2026, A8, #6419) un banco datato nuovo, tests/test_<cosa>_AAAA_MM_GG.py dal 23/11/2026, fa
     rosso; i banchi datati di prima, i banchi senza data e quelli di guardie, segreti e gate passano.

Sulla base 93f323e ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"

QUI = Path(__file__).resolve().parent
PROVA = "zorbaquix"  # inventato: nessun significato, nessuna persona
VARIANTI = ("zorba.quix", "zorba-\nquix", "zor​baquix", "zоrbaquix", "Zorba Quix", "ZorbaQuix", "ZORBA_QUIX",
            "ｚｏｒｂａｑｕｉｘ", "zorba­quix")
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def modulo(percorso: Path, codice: str):
    assert percorso.is_file(), f"{codice} manca {percorso.name}: il controllo di igiene non ha un modulo suo"
    spec = importlib.util.spec_from_file_location(f"igiene_{codice}", str(percorso))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ig01(repo: Path) -> None:
    nuovo = modulo(QUI / "igiene.py", "IG01")
    problemi = nuovo.controlla(repo)
    assert not problemi, "IG01 nomi della config privata, interi o spezzati, nel repository: " + "; ".join(problemi[:8])


def test_ig02(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG02")
    h = ig.impronta(PROVA)
    mancate = [repr(v) for v in VARIANTI if not ig.trova(f"prima {v} dopo", {h})]
    assert not mancate, f"IG02 varianti che il controllo non vede: {mancate}"
    assert not ig.trova("una zorba e una quixote", {h}) and not ig.trova("zorbaquixote", {h}), \
        "IG02 il controllo unisce parole che non formano il termine"


def test_ig03(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG03")
    h = ig.impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)

        def git(*a: str) -> str:
            return subprocess.run(["git", "-C", str(r), *a], env=dict(os.environ, **GIT_ENV), capture_output=True,
                                  text=True, check=True, timeout=30).stdout.strip()
        git("init", "-q", "-b", "main")
        (r / "pulito.md").write_text("niente\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "vecchio commit con Zorba.Quix, gia' pubblicato")
        vecchio = git("rev-parse", "HEAD")
        (r / "note").mkdir()
        (r / "note" / "zorba-quix.md").write_text("niente\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "aggiunge le note\n\nscritte da Zor​ba Quix")
        problemi = ig.controlla(r, f"{vecchio}..HEAD", {h})
        assert any("percorso" in p and "note/" in p for p in problemi), f"IG03 il percorso non si controlla: {problemi}"
        assert any(p.startswith("commit") for p in problemi), f"IG03 i messaggi dei commit non si controllano: {problemi}"
        assert not any(vecchio[:7] in p for p in problemi), f"IG03 un commit fuori dall'intervallo si controlla: {problemi}"
        assert not any("zorba" in p.lower() or "quix" in p.lower() for p in problemi if not p.startswith("percorso")), \
            f"IG03 il rapporto ripete il termine: {problemi}"


def test_ig04(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "IG04 manca .github/workflows/igiene.yml"
    dati = yaml.safe_load(f.read_text(encoding="utf-8"))
    quando = dati.get("on", dati.get(True)) or {}
    assert set(quando) == {"push", "pull_request"} and quando["push"].get("branches") == ["**"], f"IG04 non parte su ogni push di ogni branch e su ogni pull request: {quando}"
    assert dati.get("permissions") == {"contents": "read"}, f"IG04 permessi non in sola lettura: {dati.get('permissions')}"
    lavori = dati.get("jobs") or {}
    assert len(lavori) == 1, f"IG04 il workflow fa più di un lavoro: {list(lavori)}"
    passi = next(iter(lavori.values())).get("steps") or []
    comandi = [p["run"] for p in passi if "run" in p]
    azioni = [p["uses"] for p in passi if "uses" in p]
    assert len(comandi) == 1 and "python3 tests/igiene.py" in comandi[0] and "--intervallo" in comandi[0], \
        f"IG04 il workflow non lancia il solo controllo di igiene: {comandi}"
    assert all(a.startswith("actions/checkout@") and len(a.split("@")[1]) == 40 for a in azioni), \
        f"IG04 azioni non fissate a un commit: {azioni}"


# Le impronte entrate il 9/11/2026 (review del 7/11, finding 95, 96 e 105): persone, id veri, macchina e account.
NUOVE_2026_11_09 = frozenset((
    "d63d71f407ad92113aa5b858936038d68e0fde0a7ed8b8a03a4fea2c2eab80d5", "f51ab9d849938a4f1e88903912ccdc17090df2bd9a432adc6aab61ffaf325d82",
    "8d0cfd6182ef851052565eb5c11e79f73c691307f7b6ddb877b4303cc726f260", "f6a761f669dfeafd8086a367b336cbee496a1b13ac5128c8cb9346ca7891ccf3",
    "9e22710e05fe6c6dde97788b248a88855912816408ff8beb48a275be3c4a4700", "21b2b7a347077906259e043592a4b6458035575cd4b4539f00095d4d48522817",
    "301da88d49fc5f4f6ce0dd63b7f9b840c50149a2b25b27b417638ebdecb78248", "1a9f445a124c9e63a407e54ff13bc4c2cd05068d174e34eaec7ab1a06acc71ed",
    "57dfab13dd843f3a29a4b8021866559a7b182e0d315ddec53e89a8ec597d8115",
))


def test_ig05(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG05")
    mancano = sorted(h[:12] for h in NUOVE_2026_11_09 - ig.GLOBALE)
    assert not mancano, f"IG05 persone e id veri fuori dal controllo di default: {mancano}"
    h = ig.impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "testo.md").write_text(f"riga\n{PROVA}\n", encoding="utf-8")
        (r / "font.woff2").write_bytes(b"wOF2\0\0" + PROVA.encode())
        (r / f"{PROVA}.bin").write_bytes(b"\0")
        problemi = ig.controlla(r, None, {h})
    assert any(p.startswith("testo.md:2") for p in problemi), f"IG05 il testo non si controlla: {problemi}"
    assert not any(p.startswith("font.woff2") for p in problemi), f"IG05 i byte di un binario contano come testo: {problemi}"
    assert any(p.startswith("percorso") and ".bin" in p for p in problemi), f"IG05 il percorso di un binario non si controlla: {problemi}"


def test_ig06(repo: Path) -> None:
    gancio = repo / ".githooks" / "pre-push"
    assert gancio.is_file(), "IG06 manca .githooks/pre-push: igiene gira solo su GitHub, dopo il push"
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        pubblico = base / "stellakamikaze" / "arturo.git"
        altro = base / "altro" / "progetto.git"
        r = base / "lavoro"
        env = dict(os.environ, **GIT_ENV, HOME=str(base), ARTURO_IGIENE_IMPRONTE_EXTRA=impronta_prova(repo))
        env.pop("PRE_PUSH_SKIP", None)

        def git(*a: str, cartella: Path = r, ok: bool = True) -> subprocess.CompletedProcess:
            p = subprocess.run(["git", "-C", str(cartella), *a], env=env, capture_output=True, text=True, timeout=120)
            assert not ok or p.returncode == 0, f"IG06 git {' '.join(a)}: {p.stderr}"
            return p
        for nudo in (pubblico, altro):
            nudo.mkdir(parents=True)
            git("init", "-q", "--bare", cartella=nudo)
        r.mkdir()
        git("init", "-q", "-b", "dev")
        (r / "tests").mkdir()
        (r / "tests" / "igiene.py").write_bytes((repo / "tests" / "igiene.py").read_bytes())
        (r / ".githooks").mkdir()
        (r / ".githooks" / "pre-push").write_bytes(gancio.read_bytes())
        (r / ".githooks" / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", ".githooks")
        # as_posix: l'hook riconosce .../stellakamikaze/arturo con le barre dritte, come in ogni URL vero; con
        # C:\...\stellakamikaze\arturo.git su Windows lo prendeva per un altro repository (#6455).
        git("remote", "add", "origin", pubblico.as_posix())
        git("remote", "add", "altro", altro.as_posix())
        git("add", "-A")
        git("commit", "-q", "-m", "base pulita")
        assert git("push", "-q", "origin", "dev", ok=False).returncode == 0, "IG06 l'hook blocca un push pulito"

        def spinge(remoto: str = "origin") -> subprocess.CompletedProcess:
            return git("push", "-q", remoto, "HEAD:refs/heads/lavoro", ok=False)
        # Un nome nel messaggio di un commit.
        git("commit", "-q", "--allow-empty", "-m", f"aggiunge le note\n\nscritte da {PROVA}")
        p = spinge()
        assert p.returncode != 0 and "BLOCK" in p.stderr, f"IG06 l'hook non blocca un nome nel messaggio: {p.stderr}"
        assert "zorba" not in p.stderr.lower(), f"IG06 il rapporto ripete il termine: {p.stderr}"
        assert spinge("altro").returncode == 0, "IG06 l'hook blocca un push verso un repository che non è Arturo"
        git("reset", "-q", "--hard", "HEAD~1")
        # Un nome in un file del commit spinto.
        (r / "nota.md").write_text(f"riga\n{PROVA}\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "nota")
        p = spinge()
        assert p.returncode != 0 and "nota.md:2" in p.stderr, f"IG06 l'hook non blocca un nome in un file: {p.stderr}"
        git("reset", "-q", "--hard", "HEAD~1")
        # Un nome in un file non salvato non parte col push e non conta.
        (r / "bozza.md").write_text(f"{PROVA}\n", encoding="utf-8")
        git("commit", "-q", "--allow-empty", "-m", "pulito")
        p = spinge()
        assert p.returncode == 0, f"IG06 un file non salvato blocca il push: {p.stderr}"


def impronta_prova(repo: Path) -> str:
    return modulo(repo / "tests" / "igiene.py", "IG06").impronta(PROVA)


def test_ig07(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    testo = f.read_text(encoding="utf-8") if f.is_file() else ""
    assert "^origin/dev" in testo and '"$RAMO" != "dev"' in testo, \
        "IG07 fuori da dev il workflow ricontrolla i commit già su dev: la stessa email da main e da ogni ramo"
    ig = modulo(repo / "tests" / "igiene.py", "IG07")
    h = ig.impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)

        def git(*a: str) -> str:
            return subprocess.run(["git", "-C", str(r), *a], env=dict(os.environ, **GIT_ENV), capture_output=True,
                                  text=True, check=True, timeout=30).stdout.strip()
        git("init", "-q", "-b", "dev")
        git("commit", "-q", "--allow-empty", "-m", "radice")
        radice = git("rev-parse", "HEAD")
        git("commit", "-q", "--allow-empty", "-m", f"su dev, con {PROVA}")
        git("checkout", "-q", "-b", "lavoro")
        git("commit", "-q", "--allow-empty", "-m", "sul ramo, pulito")
        assert ig.controlla(r, f"{radice}..HEAD", {h}), "IG07 la prova non ha il nome su dev"
        problemi = ig.controlla(r, f"{radice}..HEAD ^dev", {h})
        assert not problemi, f"IG07 l'intervallo non toglie i commit di dev: {problemi}"


def test_ig08(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "IG08 manca .github/workflows/igiene.yml"
    passi = next(iter((yaml.safe_load(f.read_text(encoding="utf-8")).get("jobs") or {}).values())).get("steps") or []
    blocco = next((p["run"] for p in passi if "run" in p), "")
    assert blocco, "IG08 il workflow non ha il passo che lancia il controllo"
    sorgente = repo / "tests" / "igiene.py"
    h = modulo(sorgente, "IG08").impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        ambiente = dict(os.environ, **GIT_ENV, ARTURO_IGIENE_IMPRONTE_EXTRA=h)

        def git(*a: str) -> str:
            return subprocess.run(["git", "-C", str(r), *a], env=ambiente, capture_output=True, text=True,
                                  check=True, timeout=30).stdout.strip()

        def commit(messaggio: str) -> str:
            git("commit", "-q", "--allow-empty", "-m", messaggio)
            return git("rev-parse", "HEAD")

        def pubblica(**rami: str) -> None:
            for nome, sha in rami.items():
                git("update-ref", f"refs/remotes/origin/{nome}", sha)

        def esito(prima: str, dopo: str, ramo: str, evento: str = "push") -> int:
            env = dict(ambiente, PRIMA=prima, DOPO=dopo, RAMO=ramo, EVENTO=evento)
            return subprocess.run([BASH_VERO, "-e", "-c", blocco], cwd=str(r), env=env, capture_output=True, text=True,
                                  timeout=60).returncode

        git("init", "-q", "-b", "dev")
        (r / "tests").mkdir()
        (r / "tests" / "igiene.py").write_bytes(sorgente.read_bytes())
        git("add", "-A")
        radice = commit("radice")
        pubblica(dev=radice)
        git("checkout", "-q", "-b", "vecchio")
        vecchio = commit(f"di ottobre, con {PROVA}, già pubblico")
        pubblica(vecchio=vecchio)
        git("checkout", "-q", "-b", "landing")
        landing = commit("landing, pulito")
        pubblica(landing=landing)
        zero = "0" * 40
        assert esito(zero, landing, "landing") == 0, \
            "IG08 il primo push di un ramo nuovo ricontrolla i commit che un altro ramo pubblico ha già (#6063)"
        git("checkout", "-q", "-b", "solo", radice)
        solo = commit(f"spinto con {PROVA}, il push l'ha segnalato")
        pubblica(solo=solo)
        assert esito(zero, solo, "solo") == 1, "IG08 il push di un ramo non controlla i suoi commit nuovi"
        assert esito(radice, solo, "7/merge", "pull_request") == 0, \
            "IG08 una pull request dallo stesso repository ricontrolla i commit che il push ha già controllato"
        git("checkout", "-q", "dev")
        git("merge", "-q", "--no-ff", "-m", "unisce landing", "landing")
        unione = git("rev-parse", "HEAD")
        pubblica(dev=unione)
        assert esito(radice, unione, "dev") == 0, \
            "IG08 unire in dev un ramo già pubblico ricontrolla i suoi commit vecchi (#6063)"
        nuovo = commit(f"nuovo, con {PROVA}")
        pubblica(dev=nuovo, main=nuovo)
        assert esito(unione, nuovo, "dev") == 1, \
            "IG08 due rami spinti insieme con lo stesso commit nuovo si tolgono a vicenda: il nome passa"
        git("checkout", "-q", "-b", "fork", unione)
        fork = commit(f"da un fork, con {PROVA}")
        assert esito(unione, fork, "9/merge", "pull_request") == 1, \
            "IG08 una pull request da un fork non controlla i suoi commit"
        git("checkout", "-q", "-b", "ramo", unione)
        ramo = commit(f"ramo nuovo, con {PROVA}")
        pubblica(ramo=ramo)
        assert esito(zero, ramo, "ramo") == 1, "IG08 il primo push di un ramo nuovo non controlla i suoi commit nuovi"


def test_ig09(repo: Path) -> None:
    gancio = repo / ".githooks" / "pre-push"
    assert gancio.is_file(), "IG09 manca .githooks/pre-push"
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        pubblico = base / "stellakamikaze" / "arturo.git"
        altro = base / "altro" / "progetto.git"
        r = base / "lavoro"
        env = dict(os.environ, **GIT_ENV, HOME=str(base), ARTURO_IGIENE_IMPRONTE_EXTRA=impronta_prova(repo))
        env.pop("PRE_PUSH_SKIP", None)

        def git(*a: str, ok: bool = True, salta: bool = False, cartella: Path = r) -> subprocess.CompletedProcess:
            e = dict(env, PRE_PUSH_SKIP="1") if salta else env
            p = subprocess.run(["git", "-C", str(cartella), *a], env=e, capture_output=True, text=True, timeout=120)
            assert not ok or p.returncode == 0, f"IG09 git {' '.join(a)}: {p.stderr}"
            return p
        for nudo in (pubblico, altro):
            nudo.mkdir(parents=True)
            git("init", "-q", "--bare", cartella=nudo)
        r.mkdir()
        git("init", "-q", "-b", "dev")
        (r / "tests").mkdir()
        (r / "tests" / "igiene.py").write_bytes((repo / "tests" / "igiene.py").read_bytes())
        (r / ".githooks").mkdir()
        (r / ".githooks" / "pre-push").write_bytes(gancio.read_bytes())
        (r / ".githooks" / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", ".githooks")
        # as_posix: l'hook riconosce .../stellakamikaze/arturo con le barre dritte, come in ogni URL vero; con
        # C:\...\stellakamikaze\arturo.git su Windows lo prendeva per un altro repository (#6455).
        git("remote", "add", "origin", pubblico.as_posix())
        git("remote", "add", "altro", altro.as_posix())
        git("add", "-A")
        git("commit", "-q", "-m", "base pulita")
        git("push", "-q", "origin", "dev", "dev:main")
        # Un nome nel messaggio di un commit già arrivato su origin/dev (spinto da una macchina senza l'hook).
        git("commit", "-q", "--allow-empty", "-m", f"su dev\n\nprovato da {PROVA}")
        git("push", "-q", "origin", "dev", salta=True)
        p = git("push", "-q", "origin", "dev:main", ok=False)
        assert p.returncode == 0, f"IG09 main non avanza fino a un commit già su origin/dev: {p.stderr[-400:]}"
        # Un commit nuovo col nome, sopra, resta bloccato.
        git("commit", "-q", "--allow-empty", "-m", f"nuovo\n\ncon {PROVA}")
        p = git("push", "-q", "origin", "dev:main", ok=False)
        assert p.returncode != 0 and "BLOCK" in p.stderr, f"IG09 l'hook lascia partire un nome nuovo: {p.stderr[-400:]}"
        # Un commit che conosce solo un altro remoto non è pubblico nel repository di Arturo.
        git("push", "-q", "altro", "dev")
        p = git("push", "-q", "origin", "dev:main", ok=False)
        assert p.returncode != 0 and "BLOCK" in p.stderr, \
            f"IG09 un commit noto solo a un altro remoto conta come già pubblico: {p.stderr[-400:]}"


def test_ig10(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG10")
    assert hasattr(ig, "banchi_datati"), "IG10 igiene non controlla i banchi datati nuovi: un file per incidente passa"
    nomi = ("test_nuovo_2026_11_23.py", "test_vecchio_2026_11_22.py", "test_guardie_nuove_2026_12_01.py",
            "test_segreti_x_2026_12_01.py", "test_gate_y_2026_12_01.py", "test_componente.py", "test_altro_2027_01_05b.py")
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "tests").mkdir()
        for nome in nomi:
            (r / "tests" / nome).write_text("print('PASS')\n", encoding="utf-8")
        problemi = ig.controlla(r, None, set())
    datati = sorted(p.split()[2].rstrip(":") for p in problemi if p.startswith("banco datato"))
    assert datati == ["tests/test_altro_2027_01_05b.py", "tests/test_nuovo_2026_11_23.py"], \
        f"IG10 i banchi datati che igiene boccia non sono i nuovi fuori da guardie, segreti e gate: {datati} {problemi}"


TESTS = {"IG01": test_ig01, "IG02": test_ig02, "IG03": test_ig03, "IG04": test_ig04, "IG05": test_ig05,
         "IG06": test_ig06, "IG07": test_ig07, "IG08": test_ig08,
         "IG09": test_ig09, "IG10": test_ig10}


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
