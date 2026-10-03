#!/usr/bin/env python3
"""T01-T24: l'archivio dei todo e la CLI `arturo todo` (3/10/2026).

T01 aggiungi, lista, fatto. T02 la ricostruzione dal registro non cambia se una
riga arriva due volte da un merge. T03 una riga rotta si salta e il resto si
legge. T04 gli accenti restano accenti. T05 scadenze, date in italiano e `oggi`.
T06 un todo che aspetta un altro. T07 lo schema di --json, che leggono pannello
e web. T08 otto processi che scrivono insieme non perdono eventi ne' doppiano id.
T09 FERMO viene dallo stato, non da chi agisce. T10 i todo partono con /fine solo
verso un remote privato. T11 /inizio, /fine e la skill usano l'archivio. T12 due
macchine con lo stesso id: il piu' recente cambia numero e gli eventi seguono.
T13 un valore fuori lista si rifiuta e non scrive niente.

Ciclo 1.5, i prerequisiti comuni di pannello, pagina web e percorso:
T14 ripristina rimette stato e motivo esatti, inizia porta in corso. T15 il segno
annullo resta negli eventi di stato e modifica e si vede nella storia. T16 deciso
scrive nota e passaggio a io in una sola write, solo da decidi. T17 la versione
degli eventi e quella delle viste sono separate. T18 il contratto: CHIAVI_TODO,
scadenza_testo e la descrizione dei gruppi. T19 Lucchetto pubblico e
scrivi_json_atomico. T20 il progetto riservato del percorso. T21 COMANDI fa aiuto,
smistamento e messaggio di errore. T22 un .lock non parte mai con /fine.
T23 tabella degli stati e conteggi per progetto stanno nel store. T24 /aggiorna
mostra il codice di bin/ e dei mod, /diagnosi legge l'archivio.
Sulla base b8eff39 ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASH = shutil.which("bash") or "bash"
OGGI = "2026-10-03"  # un sabato
GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}
_CARICATI = []


def modulo(repo: Path, nome: str):
    """Carica bin/<nome> del repo da provare come modulo nuovo (niente cache tra repo diversi)."""
    file = repo / "bin" / nome
    if not file.is_file():
        raise FileNotFoundError(file)
    bin_dir = str(repo / "bin")
    sys.path.insert(0, bin_dir)
    vecchio_store = sys.modules.pop("todo_store", None)
    try:
        caricatore = importlib.machinery.SourceFileLoader(f"prova_{len(_CARICATI)}_{file.stem}", str(file))
        spec = importlib.util.spec_from_loader(caricatore.name, caricatore)
        m = importlib.util.module_from_spec(spec)
        caricatore.exec_module(m)
    finally:
        sys.path.remove(bin_dir)
        sys.modules.pop("todo_store", None)
        if vecchio_store is not None:
            sys.modules["todo_store"] = vecchio_store
    _CARICATI.append(m)
    return m


def store(repo: Path):
    return modulo(repo, "todo_store.py")


def chiavi_todo(repo: Path) -> set:
    """Le chiavi del contratto si leggono dal store: e' l'unico punto in cui stanno (P6)."""
    return set(store(repo).CHIAVI_TODO)


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
        chiavi = chiavi_todo(repo)
        assert set(t) == chiavi, f"T07 chiavi del todo: {sorted(set(t) ^ chiavi)}"
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


def _sync(repo: Path, base: Path, visibilita: str, lucchetto: bool = False) -> str:
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
    if lucchetto:  # un processo di arturo todo in corso, o interrotto, mentre gira /fine
        (cfg / "data" / "todo" / "eventi.jsonl.lock").write_text("", encoding="utf-8")
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
    assert "bin/arturo" in readme, "T11 il README non racconta la CLI"
    vere = len([d for d in (repo / "skills").iterdir() if (d / "SKILL.md").is_file()])
    scritti = re.findall(r"\*\*(\d+) skill\*\*", readme) + re.findall(r"^skills/\s+(\d+) skill", readme, re.M)
    assert len(scritti) == 2 and set(scritti) == {str(vere)}, \
        f"T11 il README dice {scritti} skill, nel repository ce ne sono {vere}"
    albero = [r for r in readme.splitlines() if re.match(r"bin/\S*\s{2,}", r)]
    assert len(albero) == 1 and re.fullmatch(r"bin/\s+La CLI arturo e i suoi moduli", albero[0]), \
        f"T11 nell'albero del README bin/ va descritto una volta, come cartella: {albero}"


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


def test_t14(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p", "--chi", "io")
        c.cli("inizia", "1")
        assert c.aperti()[1]["stato"] == "in corso", f"T14 inizia non porta in corso: {c.aperti()[1]}"
        c.cli("ferma", "1", "aspetta la firma")
        c.cli("fatto", "1")
        assert not c.aperti(), "T14 fatto non chiude"
        c.cli("ripristina", "1", "fermo", "aspetta la firma")
        t = c.aperti()[1]
        assert (t["stato"], t["motivo"], t["gruppo"]) == ("fermo", "aspetta la firma", "fermo"), \
            f"T14 ripristina perde stato o motivo: {t}"
        c.cli("ripristina", "1", "in corso")
        t = c.aperti()[1]
        assert (t["stato"], t["motivo"], t["gruppo"]) == ("in corso", None, "io"), f"T14 ripristina in corso: {t}"
        prima = c.registro.read_bytes()
        r = c.cli("ripristina", "1", "boh", ok=False)
        assert r.returncode == 2 and "Valori ammessi" in r.stderr, f"T14 stato non valido: {r.stderr!r}"
        assert c.registro.read_bytes() == prima, "T14 un ripristina rifiutato ha scritto"
    con_casa(repo, prova)


def test_t15(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p", "--chi", "io")
        c.cli("fatto", "1")
        c.cli("ripristina", "1", "da fare")
        c.cli("modifica", "1", "--chi", "tu", "--annullo")
        c.cli("scarta", "1", "annullato dalla pagina", "--annullo")
        c.cli("riprendi", "1")
        eventi = [json.loads(r) for r in read(c.registro).splitlines() if r.strip()]
        segni = [(e["tipo"], e["dati"].get("annullo")) for e in eventi]
        assert segni == [("crea", None), ("stato", None), ("stato", True), ("modifica", True),
                         ("stato", True), ("stato", None)], f"T15 il segno annullo nel registro: {segni}"
        storia = c.json("mostra", "1")["storia"]
        assert [s["dati"].get("annullo", False) for s in storia] == [False, False, True, True, True, False], \
            f"T15 la storia di --json perde il segno: {storia}"
        testo = c.cli("mostra", "1").stdout
        assert testo.count("(annullo)") == 3, f"T15 mostra non segna gli annulli: {testo!r}"
        r = c.cli("nota", "1", "x", ok=False)
        assert r.returncode == 0, "T15 una nota normale si rompe"
    con_casa(repo, prova)


def test_t16(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Scegliere il piano", "--progetto", "p", "--chi", "decidi")
        c.cli("aggiungi", "Tocca a me", "--progetto", "p", "--chi", "tu")
        prima = c.registro.read_bytes()
        r = c.cli("deciso", "2", "piano B", ok=False)
        assert r.returncode == 2 and r.stderr.startswith("Errore:") and "decidi" in r.stderr, \
            f"T16 deciso su un todo che non aspetta una scelta: rc={r.returncode} {r.stderr!r}"
        assert c.registro.read_bytes() == prima, "T16 un deciso rifiutato ha scritto"
        c.cli("deciso", "1", "piano B")
        t = c.aperti()[1]
        assert (t["chi"], t["gruppo"], t["note"]) == ("io", "io", ["Deciso: piano B"]), f"T16 deciso: {t}"
        nuove = c.registro.read_bytes()[len(prima):].decode("utf-8").splitlines()
        assert [json.loads(x)["tipo"] for x in nuove] == ["nota", "modifica"], f"T16 eventi: {nuove}"
    con_casa(repo, prova)
    # Una sola write: chi legge a meta' non vede la nota senza il passaggio a io.
    ts = store(repo)
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "eventi.jsonl"
        ts.aggiungi({"titolo": "Scegliere", "chi": "decidi"}, file)
        scritture = []
        vera = os.write

        def conta(fd, dati):
            scritture.append(dati)
            return vera(fd, dati)
        os.write = conta
        try:
            ts.deciso(1, "piano B", file)
        finally:
            os.write = vera
        assert len(scritture) == 1 and scritture[0].count(b"\n") == 2, \
            f"T16 deciso non scrive in una sola write: {len(scritture)} write"


def test_t17(repo: Path) -> None:
    ts = store(repo)
    assert (ts.VERSIONE_EVENTI, ts.VERSIONE_VISTA) == (1, 1), "T17 le due versioni devono valere 1"
    assert not hasattr(ts, "VERSIONE"), "T17 resta una VERSIONE unica per eventi e viste"
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "eventi.jsonl"
        # Eventi a una versione nuova: la vista resta alla sua, e viceversa.
        ts.VERSIONE_EVENTI = 7
        try:
            ts.aggiungi({"titolo": "Uno"}, file)
            todo, avvisi = ts.carica(file)
            vista_eventi_nuovi = ts.vista(todo, avvisi)["versione"]
        finally:
            ts.VERSIONE_EVENTI = 1
        assert json.loads(read(file).splitlines()[0])["v"] == 7, "T17 gli eventi non usano VERSIONE_EVENTI"
        assert vista_eventi_nuovi == 1, "T17 la vista segue la versione degli eventi"
        ts.VERSIONE_VISTA = 5
        try:
            ts.registra(1, "nota", {"testo": "x"}, file)
            vista_nuova = ts.vista(*ts.carica(file))["versione"]
        finally:
            ts.VERSIONE_VISTA = 1
        assert json.loads(read(file).splitlines()[1])["v"] == 1, "T17 gli eventi seguono la versione della vista"
        assert vista_nuova == 5, "T17 la vista non usa VERSIONE_VISTA"

    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Uno", "--progetto", "p", "--scadenza", "oggi")
        for argomenti in ((), ("oggi",), ("progetti",)):
            assert c.json(*argomenti)["versione"] == 1, f"T17 versione di {argomenti or 'lista'}"
    con_casa(repo, prova)


def test_t18(repo: Path) -> None:
    ts = store(repo)
    assert isinstance(ts.CHIAVI_TODO, tuple) and "scadenza_testo" in ts.CHIAVI_TODO, "T18 CHIAVI_TODO"
    src = read(Path(__file__))
    assert not re.search(r"^CHIAVI\w*\s*=", src, re.M), "T18 il banco tiene una sua copia delle chiavi"

    def prova(c: Casa) -> None:
        for titolo, scadenza in (("Oggi", "oggi"), ("Domani", "domani"), ("Tra cinque", "2026-10-08"),
                                 ("Ieri", "2026-10-02"), ("Due giorni fa", "2026-10-01"), ("Mai", "")):
            c.cli("aggiungi", titolo, "--progetto", "p", "--scadenza", scadenza)
        v = c.json()
        testi = {t["titolo"]: t["scadenza_testo"] for g in v["gruppi"] for t in g["todo"]}
        atteso = {"Oggi": "scade oggi", "Domani": "scade domani", "Tra cinque": "scade tra 5 g",
                  "Ieri": "scaduto ieri", "Due giorni fa": "scaduto da 2 g", "Mai": None}
        assert testi == atteso, f"T18 scadenza_testo: {testi}"
        for t in (t for g in v["gruppi"] for t in g["todo"]):
            assert set(t) == set(ts.CHIAVI_TODO), f"T18 chiavi: {sorted(set(t) ^ set(ts.CHIAVI_TODO))}"
        descrizioni = {g["tipo"]: g["descrizione"] for g in v["gruppi"]}
        assert descrizioni == {"tu": "Lo fai tu.", "decidi": "Serve una tua scelta, poi lavora Claude.",
                               "io": "Lo fa Claude.", "fermo": "Aspetta qualcosa o qualcuno."}, \
            f"T18 descrizione dei gruppi: {descrizioni}"
        lista = c.cli().stdout
        for testo in atteso.values():
            assert testo is None or testo in lista, f"T18 la lista non usa scadenza_testo: manca {testo!r}"
    con_casa(repo, prova)
    cli = read(repo / "bin" / "arturo")
    assert "def quando_scade" not in cli and "scadenza_testo" in cli, "T18 la CLI ha un suo testo della scadenza"


def test_t19(repo: Path) -> None:
    ts = store(repo)
    assert ts._Lucchetto is ts.Lucchetto, "T19 _Lucchetto non è più l'alias di Lucchetto"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        file = base / "percorso.json"
        entrato = threading.Event()

        def secondo() -> None:
            with ts.Lucchetto(file):
                entrato.set()
        with ts.Lucchetto(file):
            assert (base / "percorso.json.lock").exists(), "T19 il lucchetto non crea il suo .lock"
            altro = threading.Thread(target=secondo)
            altro.start()
            time.sleep(0.3)
            assert not entrato.is_set(), "T19 il lucchetto lascia entrare un secondo processo"
        altro.join(5)
        assert entrato.is_set() and not (base / "percorso.json.lock").exists(), "T19 il lucchetto non si libera"

        ts.scrivi_json_atomico(file, {"tappa": "Delega", "città": "è"})
        assert json.loads(read(file)) == {"tappa": "Delega", "città": "è"}, "T19 scrivi_json_atomico"
        prima = read(file)
        try:
            ts.scrivi_json_atomico(file, {"rotto": object()})
        except TypeError:
            pass
        else:
            raise AssertionError("T19 un dato non serializzabile non dà errore")
        assert read(file) == prima, "T19 una scrittura fallita rovina il file di prima"
        assert sorted(x.name for x in base.iterdir()) == ["percorso.json"], \
            f"T19 restano file temporanei: {sorted(x.name for x in base.iterdir())}"


def test_t20(repo: Path) -> None:
    ts = store(repo)
    assert ts.PROGETTO_PERCORSO == "_percorso", f"T20 PROGETTO_PERCORSO: {ts.PROGETTO_PERCORSO!r}"

    def prova(c: Casa) -> None:
        cartella = c.home / "lavoro" / "_percorso"
        cartella.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(cartella), check=True, timeout=30,
                       env=dict(os.environ, **GIT_ENV))
        env = dict(os.environ, HOME=str(c.home), USERPROFILE=str(c.home), ARTURO_OGGI=OGGI, PYTHONIOENCODING="utf-8")
        env.pop("ARTURO_TODO", None)
        r = subprocess.run([sys.executable, str(repo / "bin" / "arturo"), "todo", "aggiungi", "Dal repo"],
                           cwd=str(cartella), env=env, capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"T20 aggiungi: {r.stderr}"
        c.cli("aggiungi", "Esercizio", "--progetto", ts.PROGETTO_PERCORSO)
        a = c.aperti()
        assert a[1]["progetto"] != ts.PROGETTO_PERCORSO, f"T20 lo slug di una cartella produce il progetto riservato: {a[1]}"
        assert a[2]["progetto"] == ts.PROGETTO_PERCORSO and a[2]["gruppo"] == "tu", f"T20 il todo del percorso: {a[2]}"
        assert "Esercizio" in c.cli().stdout, "T20 i todo del percorso non compaiono nella lista"
    con_casa(repo, prova)


def test_t21(repo: Path) -> None:
    cli = modulo(repo, "arturo")
    assert isinstance(cli.COMANDI, dict) and list(cli.COMANDI) == ["todo"], f"T21 COMANDI: {cli.COMANDI}"
    funzione, aiuto = cli.COMANDI["todo"]
    assert callable(funzione) and isinstance(aiuto, str) and aiuto, "T21 la voce todo di COMANDI"
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, HOME=tmp, USERPROFILE=tmp, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(repo / "bin" / "arturo")], env=env, capture_output=True,
                           text=True, timeout=60)
        assert r.returncode == 0 and aiuto in r.stdout, f"T21 l'aiuto non nasce da COMANDI: {r.stdout!r}"
        r = subprocess.run([sys.executable, str(repo / "bin" / "arturo"), "boh"], env=env, capture_output=True,
                           text=True, timeout=60)
        assert r.returncode == 2 and "«arturo todo»" in r.stderr, f"T21 comando sconosciuto: {r.stderr!r}"
    # Una riga in piu' in COMANDI basta: aiuto, smistamento ed errore la vedono da soli.
    cli.COMANDI["prova"] = (lambda argv: 7 if argv == ["x"] else 1, "una riga di prova")
    assert cli.main(["prova", "x"]) == 7, "T21 lo smistamento non legge COMANDI"
    assert "una riga di prova" in cli.uso() and "arturo prova" in cli.uso(), "T21 l'aiuto non legge COMANDI"
    assert "«arturo prova»" in cli.sconosciuto("boh"), "T21 il messaggio di errore non legge COMANDI"


def test_t22(repo: Path) -> None:
    assert "data/todo/*.lock" in read(repo / ".gitignore").splitlines(), "T22 il .lock non è in .gitignore"
    with tempfile.TemporaryDirectory() as tmp:
        privato = _sync(repo, Path(tmp), "PRIVATE", lucchetto=True)
    assert "data/todo/eventi.jsonl" in privato.splitlines(), f"T22 i todo non viaggiano: {privato!r}"
    assert not [r for r in privato.splitlines() if r.endswith(".lock")], f"T22 /fine committa un .lock: {privato!r}"


def test_t23(repo: Path) -> None:
    ts = store(repo)
    assert ts.AZIONI_STATO["inizia"][0] == "in corso" and ts.AZIONI_STATO["riprendi"][0] == "da fare", \
        f"T23 AZIONI_STATO: {getattr(ts, 'AZIONI_STATO', None)}"
    cli = read(repo / "bin" / "arturo")
    assert "ts.AZIONI_STATO" in cli and "ts.progetti(" in cli and "conti.setdefault" not in cli, \
        "T23 la CLI tiene una sua tabella degli stati o un suo conteggio"

    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Scaduto", "--progetto", "a", "--scadenza", "1/10")
        c.cli("aggiungi", "Fermo", "--progetto", "a")
        c.cli("ferma", "2", "attesa")
        c.cli("aggiungi", "Chiuso", "--progetto", "b")
        c.cli("fatto", "3")
        conti = c.json("progetti")["progetti"]
        assert conti == {"a": {"aperti": 2, "scaduti": 1, "fermi": 1, "chiusi": 0},
                         "b": {"aperti": 0, "scaduti": 0, "fermi": 0, "chiusi": 1}}, f"T23 progetti: {conti}"
        os.environ["ARTURO_OGGI"] = OGGI
        try:
            assert ts.progetti(ts.carica(c.registro)[0]) == conti, "T23 ts.progetti e la CLI non coincidono"
        finally:
            os.environ.pop("ARTURO_OGGI", None)
    con_casa(repo, prova)


def test_t24(repo: Path) -> None:
    aggiorna = read(repo / "commands" / "aggiorna.md")
    riga = [r for r in aggiorna.splitlines() if r.startswith('git diff "HEAD...$SRC/main" -- hooks')]
    assert len(riga) == 1, f"T24 /aggiorna: il diff del codice che gira da solo: {riga}"
    for parte in ("hooks", "settings.json", "skills/*/scripts", "bin", "skills/*/hooks", "skills/*/.claude-plugin"):
        assert f" {parte} " in riga[0] + " ", f"T24 /aggiorna non mostra {parte}: {riga[0]}"
    diagnosi = read(repo / "commands" / "diagnosi.md")
    assert "arturo todo --json" in diagnosi and "avvisi" in diagnosi, "T24 /diagnosi non legge l'archivio dei todo"
    skill = read(repo / "skills" / "todo" / "SKILL.md")
    for verbo in ("ripristina ID STATO", "inizia ID", "deciso ID"):
        assert verbo in skill, f"T24 la skill todo non documenta {verbo}"


TESTS = {
    "T01": test_t01, "T02": test_t02, "T03": test_t03, "T04": test_t04, "T05": test_t05,
    "T06": test_t06, "T07": test_t07, "T08": test_t08, "T09": test_t09, "T10": test_t10,
    "T11": test_t11, "T12": test_t12, "T13": test_t13, "T14": test_t14, "T15": test_t15,
    "T16": test_t16, "T17": test_t17, "T18": test_t18, "T19": test_t19, "T20": test_t20,
    "T21": test_t21, "T22": test_t22, "T23": test_t23, "T24": test_t24,
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
            except (AssertionError, OSError, ValueError, IndexError, KeyError, ImportError, AttributeError,
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
