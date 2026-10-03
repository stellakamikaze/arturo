#!/usr/bin/env python3
"""T01-T13: l'archivio dei todo e la CLI `arturo todo` (3/10/2026).

T01 aggiungi, lista, fatto. T02 la ricostruzione dal registro non cambia se una
riga arriva due volte da un merge. T03 una riga rotta si salta e il resto si
legge. T04 gli accenti restano accenti. T05 scadenze, date in italiano e `oggi`.
T06 un todo che aspetta un altro. T07 lo schema di --json, che leggono pannello
e web. T08 otto processi che scrivono insieme non perdono eventi ne' doppiano id.
T09 FERMO viene dallo stato, non da chi agisce. T10 i todo partono con /fine solo
verso un remote privato. T11 /inizio, /fine e la skill usano l'archivio. T12 due
macchine con lo stesso id: il piu' recente cambia numero e gli eventi seguono.
T13 un valore fuori lista si rifiuta e non scrive niente.
Sulla base b8eff39 ogni controllo deve fallire.
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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASH = shutil.which("bash") or "bash"
OGGI = "2026-10-03"  # un sabato
GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}
CHIAVI = {"id", "titolo", "progetto", "scadenza", "giorni", "priorita", "stato", "quando", "chi", "perche",
          "motivo", "gruppo", "dopo", "attende", "note"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Casa:
    """Una HOME di prova con la CLI del repo da provare."""

    def __init__(self, repo: Path, base: Path):
        self.repo = repo
        self.home = base / "home"
        self.home.mkdir()
        self.registro = self.home / ".claude" / "data" / "todo" / "eventi.jsonl"

    def cli(self, *argomenti: str, ok: bool = True) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_OGGI=OGGI,
                   PYTHONIOENCODING="utf-8")
        env.pop("ARTURO_TODO", None)
        r = subprocess.run([sys.executable, str(self.repo / "bin" / "arturo"), "todo", *argomenti],
                           cwd=str(self.home), env=env, capture_output=True, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        if ok:
            assert r.returncode == 0, f"arturo todo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()}"
        return r

    def json(self, *argomenti: str) -> dict:
        return json.loads(self.cli(*argomenti, "--json").stdout)

    def aperti(self) -> dict:
        return {t["id"]: t for g in self.json()["gruppi"] for t in g["todo"]}


def con_casa(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(Casa(repo, Path(tmp)))


def test_t01(repo: Path) -> None:
    def prova(c: Casa) -> None:
        assert "Nessun todo" in c.cli().stdout, "T01 la lista vuota non lo dice"
        r = c.cli("aggiungi", "Mandare il preventivo", "--progetto", "libro", "--chi", "tu")
        assert "#1" in r.stdout, f"T01 il numero non torna alla persona: {r.stdout!r}"
        testo = c.cli().stdout
        assert "TOCCA A TE" in testo and "Mandare il preventivo" in testo, f"T01 lista: {testo!r}"
        c.cli("fatto", "1")
        v = c.json()
        assert not c.aperti() and v["chiusi"] == 1, f"T01 fatto non chiude: {v}"
    con_casa(repo, prova)


def test_t02(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p")
        c.cli("nota", "1", "prima nota")
        c.cli("modifica", "1", "--priorita", "alta")
        prima = c.json("mostra", "1")
        righe = read(c.registro)
        c.registro.write_text(righe + righe, encoding="utf-8")  # il merge che porta tutto due volte
        dopo = c.json("mostra", "1")
        assert prima == dopo, f"T02 la ricostruzione cambia con righe doppie:\n{prima}\n{dopo}"
        assert c.json()["avvisi"] == [], "T02 righe doppie trattate come errori"
    con_casa(repo, prova)


def test_t03(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Prima", "--progetto", "p")
        with open(c.registro, "a", encoding="utf-8") as f:
            f.write('{"rotta": \n')
        c.cli("aggiungi", "Dopo la riga rotta", "--progetto", "p")
        r = c.cli()
        assert "Prima" in r.stdout and "Dopo la riga rotta" in r.stdout, f"T03 lista: {r.stdout!r}"
        assert "illeggibile" in r.stderr, f"T03 la riga rotta non viene segnalata: {r.stderr!r}"
    con_casa(repo, prova)


def test_t04(repo: Path) -> None:
    def prova(c: Casa) -> None:
        titolo = "Perché è già lì: città, più avanti — «Ciò»"
        c.cli("aggiungi", titolo, "--progetto", "p", "--quando", "più avanti")
        assert c.aperti()[1]["titolo"] == titolo, "T04 il titolo con gli accenti cambia"
        assert c.aperti()[1]["quando"] == "più avanti", "T04 il quando con l'accento cambia"
        assert titolo.encode("utf-8") in c.registro.read_bytes(), "T04 il registro non è utf-8"
        assert titolo in c.cli().stdout, "T04 la lista stampa male gli accenti"
    con_casa(repo, prova)


def test_t05(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Scaduto", "--progetto", "p", "--scadenza", "1/10")
        c.cli("aggiungi", "Domani", "--progetto", "p", "--scadenza", "domani")
        c.cli("aggiungi", "Venerdì", "--progetto", "p", "--scadenza", "venerdì")
        c.cli("aggiungi", "Senza data", "--progetto", "p")
        a = c.aperti()
        assert (a[1]["scadenza"], a[1]["giorni"]) == ("2026-10-01", -2), f"T05 gg/mm: {a[1]}"
        assert a[2]["scadenza"] == "2026-10-04", f"T05 domani: {a[2]}"
        assert a[3]["scadenza"] == "2026-10-09", f"T05 venerdì da sabato: {a[3]}"
        ordine = [t["id"] for t in c.json()["gruppi"][0]["todo"]]
        assert ordine[0] == 1, f"T05 lo scaduto non sta in cima: {ordine}"
        assert "scaduto da 2 g" in c.cli().stdout, "T05 la lista non dice da quanto è scaduto"
        oggi = [t["id"] for t in c.json("oggi")["todo"]]
        assert oggi == [1, 2], f"T05 oggi --giorni 3 deve dare scaduto e domani: {oggi}"
    con_casa(repo, prova)


def test_t06(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Prova dello strato", "--progetto", "p", "--chi", "decidi")
        c.cli("aggiungi", "Rilascio su main", "--progetto", "p", "--chi", "io")
        c.cli("dopo", "2", "1")
        assert c.aperti()[2]["attende"] == [1], f"T06 #2 non aspetta #1: {c.aperti()[2]}"
        assert "aspetta #1" in c.cli().stdout, "T06 la lista non mostra l'attesa"
        c.cli("fatto", "1")
        t = c.aperti()[2]
        assert t["dopo"] == [1] and t["attende"] == [], f"T06 chiuso #1, #2 aspetta ancora: {t}"
    con_casa(repo, prova)


def test_t07(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p", "--perche", "firma")
        v = c.json()
        assert {"versione", "oggi", "progetto", "gruppi", "chiusi", "avvisi"} <= set(v), f"T07 chiavi: {set(v)}"
        assert [g["tipo"] for g in v["gruppi"]] == ["tu", "decidi", "io", "fermo"], "T07 ordine dei gruppi"
        t = v["gruppi"][0]["todo"][0]
        assert set(t) == CHIAVI, f"T07 chiavi del todo: {sorted(set(t) ^ CHIAVI)}"
        assert "uid" not in json.dumps(v), "T07 l'uid interno esce nel contratto"
    con_casa(repo, prova)


def test_t08(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Todo comune", "--progetto", "p")

        def crea(n: int) -> int:
            return c.cli("aggiungi", f"processo {n}", "--progetto", "p", ok=False).returncode

        def annota(n: int) -> int:
            return c.cli("nota", "1", f"nota {n}", ok=False).returncode  # le note non passano dal lucchetto
        with ThreadPoolExecutor(max_workers=12) as pool:
            esiti = list(pool.map(crea, range(24)))
        with ThreadPoolExecutor(max_workers=16) as pool:
            esiti += list(pool.map(annota, range(64)))
        assert esiti == [0] * 88, f"T08 {88 - esiti.count(0)} scritture in parallelo fallite"
        righe = [r for r in read(c.registro).splitlines() if r.strip()]
        assert len(righe) == 89, f"T08 eventi persi o spezzati: {len(righe)} righe su 89"
        for r in righe:
            json.loads(r)
        aperti = c.aperti()
        assert sorted(aperti) == list(range(1, 26)), f"T08 id doppi o mancanti: {sorted(aperti)}"
        assert len(aperti[1]["note"]) == 64, f"T08 note perse: {len(aperti[1]['note'])} su 64"
        assert c.json()["avvisi"] == [], f"T08 avvisi: {c.json()['avvisi']}"
    con_casa(repo, prova)


def test_t09(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Login Google", "--progetto", "p", "--chi", "io")
        c.cli("ferma", "1", "aspetta le credenziali")
        v = c.json()
        assert [t["id"] for t in v["gruppi"][3]["todo"]] == [1], f"T09 ferma non porta in FERMO: {v['gruppi']}"
        assert not v["gruppi"][2]["todo"], "T09 un todo fermo resta in FACCIO IO"
        assert "aspetta le credenziali" in c.cli().stdout, "T09 il motivo non si vede"
        c.cli("riprendi", "1")
        assert c.aperti()[1]["gruppo"] == "io", "T09 riprendi non torna a chi agisce"
    con_casa(repo, prova)


def _sync(repo: Path, base: Path, visibilita: str) -> str:
    """Esegue il Config Sync di /fine con un `gh` finto. Torna i file nel commit di sync."""
    home = base / visibilita / "home"
    cfg = home / ".claude"
    shutil.copytree(repo, cfg, ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"))
    env = dict(os.environ, HOME=str(home), **GIT_ENV)
    finto = base / visibilita / "bin"
    finto.mkdir()
    (finto / "gh").write_text(f"#!/bin/sh\necho {visibilita}\n")
    (finto / "gh").chmod(0o755)
    env["PATH"] = f"{finto}{os.pathsep}{env['PATH']}"
    remoto = base / visibilita / "remoto.git"

    def git(*a: str, cwd: Path = cfg) -> str:
        r = subprocess.run(["git", *a], cwd=str(cwd), env=env, capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"git {a}: {r.stderr}"
        return r.stdout
    git("init", "-q", "--bare", str(remoto), cwd=base)
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-qm", "base")
    git("remote", "add", "origin", str(remoto))
    git("push", "-q", "origin", "main")
    (cfg / "data" / "todo").mkdir(parents=True)
    (cfg / "data" / "todo" / "eventi.jsonl").write_text('{"tipo":"crea"}\n', encoding="utf-8")
    (cfg / "commands" / "nota-locale.md").write_text("modifica\n", encoding="utf-8")
    testo = read(repo / "commands" / "fine.md")
    inizio = testo.index("### 6. Config Sync")
    script = re.findall(r"```bash\n(.*?)```", testo[inizio:], re.S)[0]
    r = subprocess.run([BASH, "-c", script], cwd=str(home), env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"T10 sync {visibilita}: {r.stderr}"
    return git("show", "--name-only", "--format=", "HEAD")


def test_t10(repo: Path) -> None:
    assert "data/todo/" in read(repo / ".gitignore").splitlines(), "T10 data/todo non è in .gitignore"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        pubblico = _sync(repo, base, "PUBLIC")
        assert "commands/nota-locale.md" in pubblico, f"T10 il sync pubblico non ha committato niente: {pubblico!r}"
        assert "data/todo" not in pubblico, "T10 i todo partono verso un remote pubblico"
        privato = _sync(repo, base, "PRIVATE")
        assert "data/todo/eventi.jsonl" in privato, f"T10 i todo non viaggiano col remote privato: {privato!r}"


def test_t11(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    inizio = read(repo / "commands" / "inizio.md")
    fase4 = inizio[inizio.index("## FASE 4"):inizio.index("## FASE 5")]
    assert "arturo todo aggiungi" in fine or "$TODO aggiungi" in fine, "T11 /fine non scrive i todo"
    assert "bin/arturo" in fine and "bin/arturo" in fase4, "T11 /fine e /inizio non usano la CLI"
    assert "TaskCreate" not in fase4.replace("Non creare task di sessione (`TaskCreate`)", ""), \
        "T11 /inizio ricrea i task con TaskCreate invece di leggere l'archivio"
    skill = read(repo / "skills" / "todo" / "SKILL.md")
    assert "ricordami" in skill and "python3 ~/.claude/bin/arturo todo" in skill, "T11 skill todo"
    readme = read(repo / "README.md")
    assert "bin/arturo" in readme and "4 skill" in readme, "T11 il README non racconta la CLI"


def test_t12(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Su questa macchina", "--progetto", "p")
        altra = {"v": 1, "ts": "2099-01-01T00:00:00.000000+00:00", "ev": "e" * 32, "todo": "a" * 32,
                 "tipo": "crea", "id": 1, "dati": {"titolo": "Dall'altra macchina", "progetto": "p"}}
        nota = {"v": 1, "ts": "2099-01-01T00:00:01.000000+00:00", "ev": "f" * 32, "todo": "a" * 32,
                "tipo": "nota", "dati": {"testo": "nota dell'altra"}}
        with open(c.registro, "a", encoding="utf-8") as f:
            f.write(json.dumps(altra) + "\n" + json.dumps(nota) + "\n")
        a = c.aperti()
        assert a[1]["titolo"] == "Su questa macchina", f"T12 il todo più vecchio perde il numero: {a}"
        assert a[2]["titolo"] == "Dall'altra macchina" and a[2]["note"] == ["nota dell'altra"], f"T12: {a}"
        assert any("ora è #2" in x for x in c.json()["avvisi"]), "T12 il cambio di numero non viene detto"
    con_casa(repo, prova)


def test_t13(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p")
        prima = c.registro.read_bytes()
        for argomenti in (("modifica", "1", "--chi", "boh"), ("aggiungi", "Due", "--priorita", "urgente"),
                          ("aggiungi", "Tre", "--scadenza", "31/02"), ("fatto", "9")):
            r = c.cli(*argomenti, ok=False)
            assert r.returncode == 2 and r.stderr.startswith("Errore:"), f"T13 {argomenti}: rc={r.returncode} {r.stderr!r}"
        assert "tu, decidi, io" in c.cli("modifica", "1", "--chi", "boh", ok=False).stderr, "T13 i valori ammessi"
        assert c.registro.read_bytes() == prima, "T13 un comando rifiutato ha scritto nel registro"
    con_casa(repo, prova)


TESTS = {
    "T01": test_t01, "T02": test_t02, "T03": test_t03, "T04": test_t04, "T05": test_t05,
    "T06": test_t06, "T07": test_t07, "T08": test_t08, "T09": test_t09, "T10": test_t10,
    "T11": test_t11, "T12": test_t12, "T13": test_t13,
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
            except (AssertionError, FileNotFoundError, ValueError, IndexError, KeyError,
                    json.JSONDecodeError, subprocess.SubprocessError):
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
