#!/usr/bin/env python3
"""CA01-CA06: la catena dei todo e la riga di stato del progetto (3/11/2026, #3888).

CA01 `aggiungi --dopo N,M` fa nascere il todo già legato: aspetta N e M, e "Da dove partire" lo salta.
CA02 un numero di --dopo che non esiste ferma tutto con 2: nessun todo nuovo nel registro.
CA03 `arturo todo stato` scrive e rilegge la riga di stato; vuota si rifiuta; l'ultima vince; sta in
     progetti.jsonl e non nel registro dei todo; `progetti --json` la porta sotto "stati".
CA04 la pagina web lega e slega due todo con l'azione "dopo", il suo Annulla torna indietro, e la
     lettura porta gli stati.
CA05 /inizio (bin/contesto.py) mostra la riga di stato prima dei todo.
CA06 /fine e il contratto della fonte esterna nominano `--dopo` e `todo stato`.
Sulla base acb4a39 (il dev prima della catena) ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

OGGI = "2026-11-03"


class Casa:
    def __init__(self, repo: Path, base: Path):
        self.repo = repo
        self.home = base / "home"
        self.home.mkdir()
        self.registro = self.home / ".claude" / "data" / "todo" / "eventi.jsonl"

    def env(self) -> dict:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_OGGI=OGGI,
                   PYTHONIOENCODING="utf-8")
        env.pop("ARTURO_TODO", None)
        return env

    def cli(self, *argomenti: str, ok: bool = True) -> subprocess.CompletedProcess:
        r = subprocess.run([sys.executable, str(self.repo / "bin" / "arturo"), "todo", *argomenti],
                           cwd=str(self.home), env=self.env(), capture_output=True, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        if ok:
            assert r.returncode == 0, f"arturo todo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()}"
        return r

    def aperti(self) -> dict:
        v = json.loads(self.cli("--json").stdout)
        return {t["id"]: t for g in v["gruppi"] for t in g["todo"]}

    def py(self, codice: str) -> str:
        """Codice Python che importa i moduli di bin/ del repo, in un processo suo (niente moduli condivisi)."""
        r = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(self.repo / 'bin')!r})\n" + codice],
                           cwd=str(self.home), env=self.env(), capture_output=True, timeout=60)
        assert r.returncode == 0, f"codice di prova: rc={r.returncode} {r.stderr.decode('utf-8', 'replace')[-800:]}"
        return r.stdout.decode("utf-8")


def con_casa(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(Casa(repo, Path(tmp)))


def test_ca01(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Scrivere la bozza", "--progetto", "libro")
        c.cli("aggiungi", "Rileggere la bozza", "--progetto", "libro", "--dopo", "1")
        c.cli("aggiungi", "Mandare la bozza", "--progetto", "libro", "--dopo", "#1, 2", "--chi", "tu")
        a = c.aperti()
        assert a[2]["dopo"] == [1] and a[2]["attende"] == [1], f"CA01 #2 non aspetta #1: {a[2]}"
        assert a[3]["dopo"] == [1, 2], f"CA01 #3 non aspetta #1 e #2: {a[3]}"
        da_dove = json.loads(c.py("import todo_store as ts, json; print(json.dumps(ts.da_dove(ts.carica()[0])))"))
        assert da_dove["id"] == 1 and "Sblocca" in da_dove["motivo"], f"CA01 da dove partire: {da_dove}"
        righe = [json.loads(r) for r in c.registro.read_text(encoding="utf-8").splitlines() if r.strip()]
        crea = [r for r in righe if r["tipo"] == "crea" and r["id"] == 3][0]
        legami = [r for r in righe if r["tipo"] == "dopo" and r["todo"] == crea["todo"]]
        assert len(legami) == 2 and all(r["ts"] == crea["ts"] for r in legami), f"CA01 legami di #3: {legami}"
    con_casa(repo, prova)


def test_ca02(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Primo", "--progetto", "p")
        prima = c.registro.read_bytes()
        r = c.cli("aggiungi", "Secondo", "--progetto", "p", "--dopo", "1,9", ok=False)
        assert r.returncode == 2, f"CA02 --dopo con #9 inesistente: rc={r.returncode}"
        assert "#9" in r.stderr, f"CA02 l'errore non nomina #9: {r.stderr}"
        assert c.registro.read_bytes() == prima, "CA02 il registro è cambiato dopo un --dopo sbagliato"
    con_casa(repo, prova)


def test_ca03(repo: Path) -> None:
    def prova(c: Casa) -> None:
        r = c.cli("stato", "--progetto", "libro")
        assert "nessuna riga di stato" in r.stdout, f"CA03 lettura senza stato: {r.stdout}"
        c.cli("stato", "--progetto", "libro", "La bozza è a metà")
        c.cli("stato", "--progetto", "libro", "Manca  la rilettura\tdel capitolo 3")
        letto = json.loads(c.cli("stato", "--progetto", "libro", "--json").stdout)
        assert letto["riga"] == "Manca la rilettura del capitolo 3", f"CA03 vale l'ultima riga, a spazi semplici: {letto}"
        vuota = c.cli("stato", "--progetto", "libro", "   ", ok=False)
        assert vuota.returncode == 2, f"CA03 riga vuota: rc={vuota.returncode}"
        assert not c.registro.exists(), "CA03 lo stato è finito nel registro dei todo"
        file_stati = c.registro.with_name("progetti.jsonl")
        assert len(file_stati.read_text(encoding="utf-8").splitlines()) == 2, "CA03 progetti.jsonl non ha due righe"
        conti = json.loads(c.cli("progetti", "--json").stdout)
        assert conti["stati"]["libro"]["riga"] == letto["riga"], f"CA03 progetti --json: {conti}"
        # Una riga rotta in progetti.jsonl si salta.
        with open(file_stati, "a", encoding="utf-8") as f:
            f.write("{rotta\n")
        assert json.loads(c.cli("stato", "--progetto", "libro", "--json").stdout)["riga"] == letto["riga"], \
            "CA03 una riga rotta ferma la lettura"
    con_casa(repo, prova)


WEB = """
import json, threading, types
import arturo_web as w
s = types.SimpleNamespace(scrittura=threading.Lock())
passi = []
r = w.esegui(s, w.controlla_corpo({"azione": "dopo", "id": 2, "altro": 1, "titolo_atteso": "B"}))
passi.append({"messaggio": r["messaggio"], "annulla": r["annulla"], "attende": [t["attende"] for g in r["vista"]["gruppi"] for t in g["todo"] if t["id"] == 2][0]})
r = w.esegui(s, w.controlla_corpo(r["annulla"]))
passi.append({"attende": [t["attende"] for g in r["vista"]["gruppi"] for t in g["todo"] if t["id"] == 2][0], "annulla": r["annulla"]})
try:
    w.controlla_corpo({"azione": "dopo", "id": 2, "altro": True})
    passi.append("accettato")
except w.ErroreRichiesta as e:
    passi.append(e.codice)
passi.append(w.lettura()["stati"])
print(json.dumps(passi))
"""


def test_ca04(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "A", "--progetto", "p")
        c.cli("aggiungi", "B", "--progetto", "p")
        c.cli("stato", "--progetto", "p", "Si parte da A")
        passi = json.loads(c.py(WEB))
        assert passi[0]["attende"] == [1], f"CA04 la pagina non lega #2 a #1: {passi[0]}"
        assert passi[0]["messaggio"].startswith("#2 aspetta #1"), f"CA04 messaggio: {passi[0]['messaggio']}"
        assert passi[0]["annulla"]["togli"] is True, f"CA04 Annulla non toglie il legame: {passi[0]['annulla']}"
        assert passi[1]["attende"] == [] and passi[1]["annulla"] is None, f"CA04 Annulla non torna indietro: {passi[1]}"
        assert passi[2] == 400, f"CA04 altro=true accettato: {passi[2]}"
        assert passi[3]["p"]["riga"] == "Si parte da A", f"CA04 la lettura non porta gli stati: {passi[3]}"
        app = (repo / "bin" / "web" / "app.js").read_text(encoding="utf-8")
        assert 'azione: "dopo"' in app and "stati: dati.stati" in app, "CA04 la pagina non usa dopo o stati"
    con_casa(repo, prova)


def test_ca05(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.cli("aggiungi", "Primo", "--progetto", "libro")
        c.cli("stato", "--progetto", "libro", "Bozza finita, manca la rilettura")
        uscita = c.py("import contesto, todo_store as ts\nprint('\\n'.join(contesto.sezione_todo(ts.carica()[0], 'libro', None)))")
        righe = uscita.splitlines()
        assert righe[0].startswith("STATO DEL PROGETTO") and "Bozza finita" in righe[1], f"CA05 contesto: {righe[:4]}"
        assert any(r.startswith('TODO APERTI DEL PROGETTO "libro"') for r in righe), f"CA05 todo spariti: {righe}"
    con_casa(repo, prova)


def test_ca06(repo: Path) -> None:
    fine = (repo / "commands" / "fine.md").read_text(encoding="utf-8")
    fonte = (repo / "docs" / "fonte-task.md").read_text(encoding="utf-8")
    assert "--dopo" in fine and "arturo todo stato" in fine, "CA06 /fine non nomina --dopo e arturo todo stato"
    assert "--dopo" in fonte and "`stato [--progetto" in fonte, "CA06 il contratto della fonte non ha --dopo e stato"


TESTS = {"CA01": test_ca01, "CA02": test_ca02, "CA03": test_ca03, "CA04": test_ca04, "CA05": test_ca05,
         "CA06": test_ca06}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        falliti = []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError,
                    subprocess.SubprocessError):
                falliti.append(nome)
        assert falliti == list(TESTS), f"baseline non discriminante: falliscono solo {falliti} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(falliti)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
