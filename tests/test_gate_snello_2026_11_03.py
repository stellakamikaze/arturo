#!/usr/bin/env python3
"""GS01-GS08: il gate snello (3/11/2026), cioè tests/esegui_gate.py che fa girare i lavori del gate in parallelo.

GS01 un lavoro rosso non ferma gli altri: due rossi in liste diverse (un banco e una controprova) escono
     tutti e due nel rapporto, i verdi girano lo stesso e l'esecutore esce 1.
GS02 due worker hanno HOME e TMPDIR diversi: un lavoro che scrive nella sua HOME non si vede dall'altro.
GS03 l'ordine segue i tempi dell'ultimo giro (prima i lunghi); senza tempi segue le liste.
GS04 --rossi rifà solo i rossi del giro prima e stampa PARZIALE.
GS05 una controprova verde, al giro dopo con banco, fonti e base uguali, si salta e la riga finale la
     conta; una controprova rossa non entra in cache e si rifà (controprove in cache, 3/11/2026).
GS06 una controprova si rifà se cambia il banco, o un file che il banco importa (le sue fonti).
GS07 --rilascio, e ARTURO_GATE_RILASCIO=1, rifanno tutte le controprove anche in cache.
GS08 --toccati fa girare solo i lavori con una fonte fra i file cambiati e stampa PARZIALE.

Ogni caso gira su un repository finto con banchi finti, così misura l'esecutore e non i banchi veri.
Con --avvelena girano tre esecutori rotti. Uno ignora il codice d'uscita dei lavori: GS01 e GS04 devono
essere rossi. Uno salta sempre le controprove: rossi GS05, GS06 e GS07. Uno non le salta mai: rosso GS05.

Sulla base 177852f ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull}
BANCHI = {
    "ok_a.py": "print('PASS a')\n",
    "ok_b.py": "print('PASS b')\n",
    "rosso.py": "import sys\nprint('ROTTO-X')\nsys.exit(1)\n",
    "rosso2.py": "import sys\nprint('ROTTO-Y')\nsys.exit(1)\n",
    "casa.py": (
        "import json, os, sys, time\nfrom pathlib import Path\n"
        "nome = Path(sys.argv[0]).stem\nhome = Path(os.environ['HOME'])\n"
        "(home / f'segno-{nome}').write_text('x')\ntime.sleep(1.5)\n"
        "altri = sorted(p.name for p in home.glob('segno-*') if p.name != f'segno-{nome}')\n"
        "Path(os.environ['GS_OUT'], nome + '.json').write_text(json.dumps("
        "{'home': str(home), 'tmp': os.environ['TMPDIR'], 'altri': altri}))\n"),
}
BANCHI["casa2.py"] = BANCHI["casa.py"]
BANCHI["aiuto.py"] = "VALORE = 1\n"
BANCHI["usa_aiuto.py"] = "import aiuto\nprint('PASS', aiuto.VALORE)\n"
SALTO = "        if not rilascio and x.impronta and impronte.get(x.id) == x.impronta:\n"
VELENI = (
    (("GS01", "GS04"), "        lavoro.rosso = p.returncode != 0\n", "        lavoro.rosso = False\n"),
    (("GS05", "GS06", "GS07"), SALTO, "        if True:\n"),
    (("GS05",), SALTO, "        if False:\n"),
)


class Lab:
    def __init__(self, base: Path, esecutore: Path) -> None:
        self.root = base / "repo"
        (self.root / "tests").mkdir(parents=True)
        (self.root / "tests" / "esegui_gate.py").write_bytes(esecutore.read_bytes())
        for nome, testo in BANCHI.items():
            (self.root / "tests" / nome).write_text(testo, encoding="utf-8")
        env = dict(os.environ, **GIT_ENV)
        for c in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "finto"]):
            subprocess.run(["git", "-C", str(self.root), *c], env=env, check=True, capture_output=True)
        self.base = base
        self.giro = 0

    def esegui(self, *argomenti: str, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        self.giro += 1
        fixture = self.base / f"fixture{self.giro}"
        return subprocess.run([sys.executable, "-B", str(self.root / "tests" / "esegui_gate.py"), "esegui",
                               "--root", str(self.root), "--fixture", str(fixture), *argomenti],
                              capture_output=True, text=True, encoding="utf-8", timeout=300,
                              env=dict(os.environ, **(env or {})))

    def tempi(self) -> Path:
        return self.root / ".git" / "arturo-gate-tempi.json"

    def scrivi(self, nome: str, testo: str) -> None:
        (self.root / "tests" / nome).write_text(testo, encoding="utf-8")


def esecutore_di(repo: Path, codice: str) -> Path:
    f = repo / "tests" / "esegui_gate.py"
    assert f.is_file(), f"{codice} manca tests/esegui_gate.py"
    return f


def ordine(uscita: str) -> List[str]:
    return [r.split()[-1] for r in uscita.splitlines() if r.startswith(("OK ", "ROSSO "))]


def test_gs01(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        r = lab.esegui("--lavori", "2", "--banchi", "ok_a.py", "rosso.py", "--controprove", "rosso2.py HEAD",
                       "--veleni", "ok_b.py")
        out = r.stdout + r.stderr
        assert r.returncode == 1, f"GS01 con due rossi l'esecutore esce {r.returncode}: {out[-400:]}"
        for atteso in ("=== ROSSO banco:rosso.py", "ROTTO-X", "=== ROSSO controprova:rosso2.py@HEAD", "ROTTO-Y"):
            assert atteso in out, f"GS01 il rapporto non dice {atteso!r}: {out[-600:]}"
        fatti = ordine(out)
        assert "banco:ok_a.py" in fatti and "veleno:ok_b.py" in fatti, f"GS01 dopo un rosso i verdi non girano: {fatti}"


def test_gs02(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        uscite = Path(t) / "uscite"
        uscite.mkdir()
        r = lab.esegui("--lavori", "2", "--banchi", "casa.py", "casa2.py", env={"GS_OUT": str(uscite)})
        assert r.returncode == 0, f"GS02 l'esecutore esce {r.returncode}: {(r.stdout + r.stderr)[-400:]}"
        a, b = (json.loads((uscite / f"{n}.json").read_text(encoding="utf-8")) for n in ("casa", "casa2"))
        assert a["home"] != b["home"] and a["tmp"] != b["tmp"], f"GS02 i due worker condividono HOME o TMPDIR: {a} {b}"
        assert not a["altri"] and not b["altri"], f"GS02 un worker vede i file dell'altro: {a['altri']} {b['altri']}"


def test_gs03(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        r = lab.esegui("--lavori", "1", "--banchi", "ok_a.py", "ok_b.py")
        assert ordine(r.stdout) == ["banco:ok_a.py", "banco:ok_b.py"], f"GS03 senza tempi non segue le liste: {r.stdout!r}"
        lab.tempi().write_text(json.dumps({"banco:ok_a.py": 1, "banco:ok_b.py": 50}), encoding="utf-8")
        r = lab.esegui("--lavori", "1", "--banchi", "ok_a.py", "ok_b.py")
        assert ordine(r.stdout) == ["banco:ok_b.py", "banco:ok_a.py"], f"GS03 il lavoro lungo non parte per primo: {r.stdout!r}"


def test_gs04(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--banchi", "ok_a.py", "rosso.py", "--controprove", "rosso2.py HEAD")
        lab.esegui(*liste)
        r = lab.esegui("--rossi", *liste)
        fatti = ordine(r.stdout)
        assert sorted(fatti) == ["banco:rosso.py", "controprova:rosso2.py@HEAD"], f"GS04 --rossi non rifà solo i rossi: {fatti}"
        assert "PARZIALE" in r.stdout and r.returncode == 1, f"GS04 --rossi non dice PARZIALE o non esce 1: {r.returncode} {r.stdout[-300:]!r}"


def saltate(uscita: str) -> int:
    for riga in uscita.splitlines():
        if riga.startswith("LAVORI:") and "controprove saltate=" in riga:
            return int(riga.split("controprove saltate=")[1].split()[0])
    return -1


def test_gs05(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--controprove", "ok_a.py HEAD", "rosso2.py HEAD")
        r = lab.esegui(*liste)
        assert "controprova:ok_a.py@HEAD" in ordine(r.stdout), f"GS05 al primo giro la controprova non gira: {r.stdout!r}"
        r = lab.esegui(*liste)
        fatti = ordine(r.stdout)
        assert "controprova:ok_a.py@HEAD" not in fatti and saltate(r.stdout) == 1, \
            f"GS05 con banco e base uguali la controprova verde non si salta: {fatti} {r.stdout[-300:]!r}"
        assert "controprova:rosso2.py@HEAD" in fatti, f"GS05 una controprova rossa è finita in cache: {fatti}"


def test_gs06(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--controprove", "ok_a.py HEAD", "usa_aiuto.py HEAD")
        lab.esegui(*liste)
        lab.scrivi("ok_a.py", "print('PASS a, cambiato')\n")
        lab.scrivi("aiuto.py", "VALORE = 2\n")
        r = lab.esegui(*liste)
        fatti = sorted(ordine(r.stdout))
        assert fatti == ["controprova:ok_a.py@HEAD", "controprova:usa_aiuto.py@HEAD"] and saltate(r.stdout) == 0, \
            f"GS06 con banco o fonte cambiati la controprova non si rifà: {fatti} {r.stdout[-300:]!r}"


def test_gs07(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "1", "--controprove", "ok_a.py HEAD", "ok_b.py HEAD")
        lab.esegui(*liste)
        for argomenti, env in ((("--rilascio",), None), ((), {"ARTURO_GATE_RILASCIO": "1"})):
            r = lab.esegui(*argomenti, *liste, env=env)
            fatti = sorted(ordine(r.stdout))
            assert fatti == ["controprova:ok_a.py@HEAD", "controprova:ok_b.py@HEAD"] and saltate(r.stdout) == 0, \
                f"GS07 al rilascio ({argomenti or env}) non girano tutte le controprove: {fatti} {r.stdout[-300:]!r}"


def test_gs08(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--banchi", "ok_a.py", "ok_b.py", "usa_aiuto.py", "--veleni", "ok_a.py")
        r = lab.esegui("--toccati", *liste)
        assert ordine(r.stdout) == [] and "PARZIALE" in r.stdout and r.returncode == 0, \
            f"GS08 senza file cambiati --toccati fa girare qualcosa: {r.returncode} {r.stdout[-300:]!r}"
        lab.scrivi("aiuto.py", "VALORE = 3\n")
        r = lab.esegui("--toccati", *liste)
        fatti = ordine(r.stdout)
        assert fatti == ["banco:usa_aiuto.py"] and "PARZIALE" in r.stdout, \
            f"GS08 --toccati non tiene solo i lavori del file cambiato: {fatti} {r.stdout[-300:]!r}"


TESTS = {"GS01": test_gs01, "GS02": test_gs02, "GS03": test_gs03, "GS04": test_gs04, "GS05": test_gs05,
         "GS06": test_gs06, "GS07": test_gs07, "GS08": test_gs08}


def avvelena(repo: Path) -> None:
    vero = esecutore_di(repo, "VELENO")
    testo = vero.read_text(encoding="utf-8")
    for codici, giusta, rotta in VELENI:
        assert testo.count(giusta) == 1, f"VELENO la riga {giusta.strip()!r} non c'è più: aggiorna VELENI"
        with tempfile.TemporaryDirectory() as t:
            rotto = Path(t) / "esegui_gate.py"
            rotto.write_text(testo.replace(giusta, rotta), encoding="utf-8")
            for codice in codici:
                try:
                    TESTS[codice](rotto)
                except AssertionError as e:
                    assert str(e).startswith(codice), f"VELENO {codice} rosso per un altro motivo: {e}"
                    print(f"VELENO {codice} ROSSO ({rotta.strip()}): {str(e)[:120]}")
                    continue
                raise AssertionError(f"VELENO {codice} verde con l'esecutore rotto da {rotta.strip()!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        avvelena(repo)
        return 0
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(esecutore_di(repo, nome))
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for nome, test in TESTS.items():
        test(esecutore_di(repo, nome))
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
