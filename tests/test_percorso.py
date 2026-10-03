#!/usr/bin/env python3
"""G01-G15: il percorso a tappe, `arturo percorso` (3/10/2026, ciclo 5).

G01 una HOME vuota: il contratto JSON, tappa 0, nessun file creato. G02 Osserva e Prova, con
il todo che le prova. G03 il volume non conta: trenta todo delegati restano alla tappa 2, e
nessun conteggio entra nel contratto o nel testo. G04 Delega: una decisione della persona più
un limite o un no motivato (perché, scarto con motivo, riapertura). G05 Orchestra: una
decisione chiusa prima del lavoro di Claude che la aspettava. G06 la domanda: un todo tuo
aperto senza perché, uno per volta. G07 gli esercizi: la rotazione per settimana, gli esercizi
fatti escono, uno aperto resta, il file reale ha la forma giusta, un file rotto dà un avviso.
G08 le letture non scrivono niente. G09 il segnalibro della tappa vista e un file di stato
rotto. G10 i suggerimenti: uno al giorno, tre giorni di silenzio dopo un no, quattordici dopo
due no di fila, basta e riprendi. G11 tutto resta in locale e il referente non lo legge.
G12 gli accenti restano accenti. G13 niente colpa nei testi. G14 i raccordi nei testi
(skill, /inizio, /fine, /guidami, /setup, README, NOVITA, capitolo 05). G15 gli annulli del
pannello e della pagina non sbloccano nessuna tappa, e la decisione si legge dalla storia.
Sulla base 3001fcc ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OGGI = "2026-10-05"  # un lunedì
CHIAVI = {"versione", "oggi", "tappa", "nome", "nuova_tappa", "tappe", "tieni_tu", "domanda", "esercizio",
          "suggerimenti", "avvisi"}
# Tutte le chiavi che il contratto può avere, a ogni livello.
CONTRATTO = CHIAVI | {"numero", "fatta", "segni", "capitolo", "testo", "prova", "codice", "titolo", "todo",
                      "id", "disponibile", "motivo", "pausa"}
TAPPE = ["Osserva", "Prova", "Delega", "Orchestra"]
COLPA = ("indietro", "saltat", "mancat", "ritardo", "streak", "punti", "dovresti")
REGOLA = "da tu a io o decidi senza un sì"
NOTA_AUTORE = "<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def piu(giorni: int, base: str = OGGI) -> str:
    return (dt.date.fromisoformat(base) + dt.timedelta(days=giorni)).isoformat()


class Casa:
    """Una HOME di prova con la CLI del repo da provare."""

    def __init__(self, repo: Path, base: Path):
        self.repo = repo
        self.home = base / "home"
        self.home.mkdir()
        self.registro = self.home / ".claude" / "data" / "todo" / "eventi.jsonl"
        self.stato = self.home / ".claude" / "session-env" / "percorso.json"

    def arturo(self, *argomenti: str, ok: bool = True, oggi: str = OGGI) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_OGGI=oggi,
                   PYTHONIOENCODING="utf-8")
        env.pop("ARTURO_TODO", None)
        r = subprocess.run([sys.executable, str(self.repo / "bin" / "arturo"), *argomenti],
                           cwd=str(self.home), env=env, capture_output=True, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        if ok:
            assert r.returncode == 0, f"arturo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()}"
        return r

    def todo(self, *argomenti: str, **opzioni) -> subprocess.CompletedProcess:
        return self.arturo("todo", *argomenti, **opzioni)

    def percorso(self, *argomenti: str, **opzioni) -> subprocess.CompletedProcess:
        return self.arturo("percorso", *argomenti, **opzioni)

    def json(self, oggi: str = OGGI) -> dict:
        return json.loads(self.percorso("--json", oggi=oggi).stdout)

    def prova(self, nome: str, oggi: str = OGGI) -> list:
        """Le prove dei segni della tappa `nome`."""
        voce = next(t for t in self.json(oggi)["tappe"] if t["nome"] == nome)
        return [s["prova"] for s in voce["segni"]]


def con_casa(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(Casa(repo, Path(tmp)))


def chiavi(valore) -> set:
    if isinstance(valore, dict):
        return set(valore) | set().union(*(chiavi(v) for v in valore.values()))
    if isinstance(valore, list):
        return set().union(*(chiavi(v) for v in valore)) if valore else set()
    return set()


def interi(valore) -> list:
    if isinstance(valore, bool):
        return []
    if isinstance(valore, int):
        return [valore]
    if isinstance(valore, dict):
        return [n for v in valore.values() for n in interi(v)]
    if isinstance(valore, list):
        return [n for v in valore for n in interi(v)]
    return []


def decisione(c: Casa, titolo: str = "Scegliere il piano") -> None:
    """Un todo decidi, la decisione con `deciso`, poi Claude lo chiude: Prova e Delega (a)."""
    c.todo("aggiungi", titolo, "--chi", "decidi", "--progetto", "p")
    numero = re.search(r"#(\d+)", c.todo("aggiungi", "segnaposto", "--progetto", "p").stdout).group(1)
    c.todo("scarta", numero, "--annullo")  # un todo in piu' che non deve contare
    primo = str(int(numero) - 1)
    c.todo("deciso", primo, "piano B")
    c.todo("fatto", primo)


def test_g01(repo: Path) -> None:
    def prova(c: Casa) -> None:
        v = c.json()
        assert set(v) == CHIAVI, f"G01 chiavi del contratto: {sorted(v)}"
        assert v["versione"] == 1 and v["tappa"] == 0 and v["domanda"] is None and v["nome"] is None, f"G01: {v}"
        assert [t["nome"] for t in v["tappe"]] == TAPPE, f"G01 ordine delle tappe: {v['tappe']}"
        assert v["esercizio"] and v["esercizio"]["tappa"] == "Osserva", f"G01 esercizio: {v['esercizio']}"
        assert "uid" not in chiavi(v), "G01 un uid nel contratto"
        assert not c.registro.exists() and not c.stato.exists(), "G01 la lettura ha creato un file"
    con_casa(repo, prova)


def test_g02(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Leggere i materiali", "--progetto", "p")
        v = c.json()
        assert v["tappa"] == 1 and v["tappe"][0]["segni"][0]["prova"] == 1, f"G02 Osserva: {v['tappe'][0]}"
        c.todo("aggiungi", "Riassumere il bando", "--chi", "io", "--progetto", "p")
        assert c.json()["tappa"] == 1, "G02 un todo io aperto apre Prova"
        c.todo("fatto", "2")
        v = c.json()
        assert v["tappa"] == 2 and v["nome"] == "Prova" and v["tappe"][1]["segni"][0]["prova"] == 2, \
            f"G02 Prova: {v['tappe'][1]}"
    con_casa(repo, prova)


def test_g03(repo: Path) -> None:
    def prova(c: Casa) -> None:
        for i in range(30):
            c.todo("aggiungi", f"Lavoro {i + 1}", "--chi", "io", "--progetto", "p")
            c.todo("fatto", str(i + 1))
        v = c.json()
        assert v["tappa"] < 3, "G03 tappa 3 con soli todo delegati"
        assert v["tappa"] == 2, f"G03 tappa {v['tappa']}"
        assert chiavi(v) <= CONTRATTO, f"G03 chiavi fuori contratto: {sorted(chiavi(v) - CONTRATTO)}"
        assert 30 not in interi(v), "G03 un conteggio nel contratto"
        assert "30" not in c.percorso().stdout, "G03 un conteggio nel testo"
    con_casa(repo, prova)


def test_g04(repo: Path) -> None:
    def casa_a(c: Casa) -> None:
        decisione(c)
        assert c.json()["tappa"] == 2, "G04 casa A: una decisione senza limite apre Delega"
        c.todo("aggiungi", "Firmare il contratto", "--chi", "tu", "--perche", "firma", "--progetto", "p")
        v = c.json()
        assert v["tappa"] == 3 and v["tieni_tu"] == ["firma"], f"G04 casa A: {v['tappa']} {v['tieni_tu']}"

    def casa_b(c: Casa) -> None:
        decisione(c)
        c.todo("aggiungi", "Rivedere la lettera", "--chi", "io", "--progetto", "p")
        c.todo("scarta", "3", "non è la mia voce")
        assert c.json()["tappa"] == 3 and c.prova("Delega")[1] == 3, "G04 casa B: il no motivato non conta"

    def casa_c(c: Casa) -> None:
        decisione(c)
        c.todo("aggiungi", "Spedire la bozza", "--chi", "io", "--progetto", "p")
        c.todo("fatto", "3")
        assert c.json()["tappa"] == 2, "G04 casa C: tappa 3 prima della riapertura"
        c.todo("riprendi", "3")
        assert c.json()["tappa"] == 3, "G04 casa C: la riapertura di un lavoro di Claude non conta"

    def casa_d(c: Casa) -> None:
        decisione(c)
        c.todo("aggiungi", "Rivedere la lettera", "--chi", "io", "--progetto", "p")
        c.todo("scarta", "3")
        assert c.json()["tappa"] == 2, "G04 casa D: uno scarto senza motivo apre Delega"

    for caso in (casa_a, casa_b, casa_c, casa_d):
        con_casa(repo, caso)


def test_g05(repo: Path) -> None:
    def preparazione(c: Casa) -> None:
        c.todo("aggiungi", "Decidere se partecipare", "--chi", "decidi", "--progetto", "p")
        c.todo("aggiungi", "Scrivere la scaletta", "--chi", "io", "--progetto", "p")
        c.todo("dopo", "2", "1")
        c.todo("aggiungi", "Firmare la domanda", "--chi", "tu", "--perche", "firma", "--progetto", "p")
        c.todo("deciso", "1", "partecipo")

    def in_ordine(c: Casa) -> None:
        preparazione(c)
        c.todo("fatto", "1")
        c.todo("fatto", "2")
        v = c.json()
        assert v["tappa"] == 4 and c.prova("Orchestra") == [2], f"G05 decisione prima del lavoro: {v['tappe'][3]}"

    def al_contrario(c: Casa) -> None:
        preparazione(c)
        c.todo("fatto", "2")
        c.todo("fatto", "1")
        assert c.json()["tappa"] == 3, "G05 Orchestra con la decisione chiusa dopo il lavoro che la aspettava"

    def senza_decisione(c: Casa) -> None:
        decisione(c)  # #1 deciso e fatto, #2 scartato con annullo
        c.todo("aggiungi", "Firmare la domanda", "--chi", "tu", "--perche", "firma", "--progetto", "p")
        c.todo("aggiungi", "Leggere i requisiti", "--chi", "io", "--progetto", "p")
        c.todo("aggiungi", "Scrivere la scaletta", "--chi", "io", "--progetto", "p")
        c.todo("dopo", "5", "4")
        c.todo("fatto", "4")
        c.todo("fatto", "5")
        assert c.json()["tappa"] == 3, "G05 un collegamento fra due lavori di Claude apre Orchestra"

    for caso in (in_ordine, al_contrario, senza_decisione):
        con_casa(repo, caso)


def test_g06(repo: Path) -> None:
    def prova(c: Casa) -> None:
        for titolo, altro in (("Uno", ()), ("Due", ()), ("Tre", ()), ("Quattro", ()),
                              ("Cinque", ("--perche", "firma")), ("Sei", ("--progetto", "_percorso"))):
            c.todo("aggiungi", titolo, "--chi", "tu", *(altro if "--progetto" in altro else ("--progetto", "p", *altro)))
        c.todo("ferma", "3", "aspetta una risposta")
        c.todo("fatto", "4")
        assert c.json()["domanda"] == {"id": 1, "titolo": "Uno"}, f"G06 domanda: {c.json()['domanda']}"
        c.todo("modifica", "1", "--perche", "invio")
        assert c.json()["domanda"] == {"id": 2, "titolo": "Due"}, f"G06 dopo il perché: {c.json()['domanda']}"
        c.todo("modifica", "2", "--chi", "decidi")
        assert c.json()["domanda"] is None, f"G06 domanda su un todo fermo, chiuso, con perché o del percorso: " \
                                            f"{c.json()['domanda']}"
    con_casa(repo, prova)


def test_g07(repo: Path) -> None:
    testo = read(repo / "docs" / "esercizi.md")
    intestazione = re.compile(r"^## (E\d{2}) · (Osserva|Prova|Delega|Orchestra) · (.+)$")
    pezzi = re.split(r"^(?=## E\d{2} )", testo, flags=re.M)[1:]
    assert pezzi, "G07 docs/esercizi.md senza esercizi"
    per_tappa = {}
    for pezzo in pezzi:
        m = intestazione.match(pezzo.splitlines()[0])
        assert m, f"G07 intestazione non conforme: {pezzo.splitlines()[0]!r}"
        per_tappa.setdefault(m.group(2), []).append(m.group(1))
        for blocco in ("**Cosa fai**", "**Cosa resta a te**", "**Come sai che è fatto**", "**Federico lo fa così**",
                       "**Il principio**"):
            assert blocco in pezzo, f"G07 {m.group(1)} senza {blocco}"
        link = re.search(r"\*\*Il principio\*\*.*?\]\(([^)]+)\)", pezzo)
        assert link and (repo / "docs" / link.group(1)).is_file(), f"G07 {m.group(1)}: link al principio rotto"
    assert all(len(per_tappa.get(t, [])) >= 2 for t in TAPPE), f"G07 meno di due esercizi per tappa: {per_tappa}"

    def prova(c: Casa) -> None:
        lunedi, dopo = c.json(OGGI)["esercizio"], c.json(piu(7))["esercizio"]
        assert lunedi["codice"] != dopo["codice"], f"G07 l'esercizio non cambia con la settimana: {lunedi}"
        c.todo("aggiungi", "Esercizio E01: Fatti raccontare una cartella", "--progetto", "_percorso")
        c.todo("fatto", "1")
        for giorno in (OGGI, piu(7)):
            assert c.json(giorno)["esercizio"]["codice"] != "E01", "G07 un esercizio fatto torna"
        c.todo("aggiungi", "Esercizio E02: Tre todo dalla posta", "--progetto", "_percorso")
        for giorno in (OGGI, piu(7)):
            e = c.json(giorno)["esercizio"]
            assert e["codice"] == "E02" and e["todo"] == 2, f"G07 l'esercizio aperto non resta: {e}"
    con_casa(repo, prova)

    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "repo"
        shutil.copytree(str(repo / "bin"), str(copia / "bin"), ignore=shutil.ignore_patterns("__pycache__"))
        (copia / "docs").mkdir()
        (copia / "docs" / "esercizi.md").write_text("# Esercizi\n\n## E1 - Osserva - senza forma\n", encoding="utf-8")
        c = Casa(copia, Path(tmp))
        r = c.percorso("--json")
        v = json.loads(r.stdout)
        assert v["esercizio"] is None and any("esercizi non trovati" in a for a in v["avvisi"]), \
            f"G07 un file di esercizi rotto: {v['esercizio']} {v['avvisi']}"


def test_g08(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.percorso()
        c.percorso("--json")
        assert not c.registro.exists(), "G08 la lettura crea l'archivio dei todo"
        assert not c.stato.exists(), "G08 la lettura crea percorso.json"
        c.todo("aggiungi", "Uno", "--progetto", "p")
        c.stato.parent.mkdir(parents=True)
        c.stato.write_text('{"tappa_vista": 0, "suggerimenti": [], "pausa": null}\n', encoding="utf-8")
        prima =(c.registro.read_bytes(), c.stato.read_bytes())
        cartella = sorted(p.name for p in c.stato.parent.iterdir())
        c.percorso()
        c.percorso("--json")
        assert (c.registro.read_bytes(), c.stato.read_bytes()) == prima, "G08 la lettura cambia i file"
        assert sorted(p.name for p in c.stato.parent.iterdir()) == cartella, "G08 la lettura lascia file nuovi"
    con_casa(repo, prova)


def test_g09(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Uno", "--progetto", "p")
        assert c.json()["nuova_tappa"] is True, "G09 la prima tappa non è nuova"
        c.percorso("visto")
        assert c.json()["nuova_tappa"] is False, "G09 visto non salva il segnalibro"
        assert json.loads(read(c.stato))["tappa_vista"] == 1, f"G09 percorso.json: {read(c.stato)}"
        c.todo("aggiungi", "Due", "--chi", "io", "--progetto", "p")
        c.todo("fatto", "2")
        assert c.json()["nuova_tappa"] is True, "G09 la tappa 2 non è nuova"
        c.stato.write_text("questo non è JSON", encoding="utf-8")
        assert c.json()["avvisi"], "G09 un percorso.json rotto non dà un avviso"
        c.percorso()
        assert c.percorso("suggerisci", ok=False).returncode in (0, 3), "G09 suggerisci fallisce su un file rotto"
        c.stato.write_text("[1, 2", encoding="utf-8")
        c.percorso("visto")
        assert json.loads(read(c.stato))["tappa_vista"] == 2, "G09 visto non riscrive pulito un file rotto"
    con_casa(repo, prova)


def test_g10(repo: Path) -> None:
    def rc(c: Casa, giorno: str) -> int:
        return c.percorso("suggerisci", ok=False, oggi=giorno).returncode

    def prova(c: Casa) -> None:
        assert c.json()["suggerimenti"]["disponibile"] is True, "G10 --json non dice che si può proporre"
        assert rc(c, OGGI) == 0, "G10 il primo suggerimento del giorno"
        r = c.percorso("suggerisci", ok=False)
        assert r.returncode == 3 and "già uno oggi" in r.stdout, f"G10 il secondo suggerimento dello stesso giorno: {r.stdout}"
        c.percorso("no")
        assert [rc(c, piu(1)), rc(c, piu(2))] == [3, 3], "G10 dopo un no Claude non tace tre giorni"
        assert rc(c, piu(3)) == 0, "G10 dopo tre giorni il silenzio non finisce"
        c.percorso("no", oggi=piu(3))
        assert rc(c, piu(3 + 13)) == 3, "G10 dopo due no di fila il silenzio dura meno di quattordici giorni"
        assert rc(c, piu(3 + 14)) == 0, "G10 dopo quattordici giorni il silenzio non finisce"
        c.percorso("basta", oggi=piu(3 + 14))
        assert rc(c, piu(3 + 14 + 30)) == 3, "G10 basta non ferma le proposte"
        assert c.json(piu(3 + 14 + 30))["suggerimenti"]["pausa"] == "sempre", "G10 --json non dice la pausa"
        c.percorso("riprendi", oggi=piu(3 + 14 + 30))
        assert rc(c, piu(3 + 14 + 30)) == 0, "G10 riprendi non riapre le proposte"
    con_casa(repo, prova)

    def senza_consumo(c: Casa) -> None:
        for _ in range(2):
            assert c.json()["suggerimenti"]["disponibile"] is True, "G10 --json consuma il suggerimento del giorno"
        assert rc(c, OGGI) == 0, "G10 --json ha consumato il suggerimento del giorno"
    con_casa(repo, senza_consumo)


def test_g11(repo: Path) -> None:
    sorgente = read(repo / "bin" / "percorso.py")
    vietati = {"urllib", "http", "socket", "ssl", "subprocess", "requests"}
    for nodo in ast.walk(ast.parse(sorgente)):
        nomi = []
        if isinstance(nodo, ast.Import):
            nomi = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nomi = [nodo.module or ""]
        for nome in nomi:
            assert nome.split(".")[0] not in vietati, f"G11 bin/percorso.py importa {nome}: il percorso va in rete"
    assert "http" not in sorgente, "G11 bin/percorso.py contiene un indirizzo"

    def prova(c: Casa) -> None:
        trovate = chiavi(c.json())
        for parola in ("invio", "inviato", "telemetria", "url", "endpoint", "server"):
            assert parola not in trovate, f"G11 chiave {parola} nel contratto"
    con_casa(repo, prova)
    referente = read(repo / "docs" / "referente.md")
    assert "percorso" in referente and "non vede il percorso" in referente, "G11 docs/referente.md non dice che il referente non vede il percorso"
    for path in (repo / "templates" / "strato").rglob("*"):
        if path.is_file():
            testo = path.read_text(encoding="utf-8", errors="replace")
            assert "percorso.json" not in testo and "arturo percorso" not in testo, f"G11 lo strato legge il percorso: {path}"
    assert "Niente telemetria" in read(repo / "README.md"), "G11 l'Impegno 3 non c'è più"


def test_g12(repo: Path) -> None:
    perche = "Perché è già lì: le cifre, più avanti"
    tenuto = "non ho incollato i nomi, è mio"

    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Firmare", "--chi", "tu", "--perche", perche, "--progetto", "p")
        c.todo("aggiungi", "Esercizio E01: Fatti raccontare una cartella", "--progetto", "_percorso")
        c.todo("nota", "2", "Tenuto: " + tenuto)
        grezzo = c.percorso("--json").stdout
        assert perche in grezzo and tenuto in grezzo and "\\u" not in grezzo, "G12 accenti scritti come escape nel JSON"
        assert json.loads(grezzo)["tieni_tu"] == [perche, tenuto], f"G12 tieni_tu: {json.loads(grezzo)['tieni_tu']}"
        testo = c.percorso().stdout
        assert perche in testo and tenuto in testo, f"G12 accenti persi nel testo: {testo!r}"
    con_casa(repo, prova)


def test_g13(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Esercizio E01: Fatti raccontare una cartella", "--progetto", "_percorso")
        c.todo("aggiungi", "Riassumere il bando", "--chi", "io", "--progetto", "p")
        tardi = piu(21)
        uscite = [c.percorso(oggi=tardi).stdout, c.percorso("aiuto", oggi=tardi).stdout]
        for comando in ("suggerisci", "no", "suggerisci", "basta", "riprendi", "visto"):
            r = c.percorso(comando, ok=False, oggi=tardi)
            uscite.append(r.stdout + r.stderr)
        for testo in uscite:
            basso = testo.lower()
            for parola in COLPA:
                assert parola not in basso, f"G13 parola di colpa «{parola}» in: {testo!r}"
            assert not re.search(r"\d+\s*settiman", basso), f"G13 un numero di settimane in: {testo!r}"
    con_casa(repo, prova)


def frontmatter(testo: str) -> dict:
    blocco = testo.split("---\n", 2)[1]
    return {m.group(1): m.group(2) for m in re.finditer(r"^([a-z_]+):\s*(.*)$", blocco, re.M)}


def sezione(testo: str, inizio: str, fine: str) -> str:
    return testo[testo.index(inizio):testo.index(fine, testo.index(inizio))]


def test_g14(repo: Path) -> None:
    skill = read(repo / "skills" / "percorso" / "SKILL.md")
    campi = frontmatter(skill)
    assert {"name", "description", "when_to_use"} <= set(campi) and campi["name"] == "percorso", f"G14 frontmatter: {campi}"
    assert "python3 ~/.claude/bin/arturo percorso" in skill, "G14 la skill non lancia la CLI"
    assert "/percorso" in skill and "a che punto sono" in skill, "G14 la skill non risponde a /percorso"
    for path in (repo / "skills" / "percorso").rglob("*.md"):
        assert "Documents/ClaudeCode" not in read(path), f"G14 la macchina dell'autore in {path.name}"
    inizio = read(repo / "commands" / "inizio.md")
    assert "arturo\" percorso --json" in sezione(inizio, "## FASE 4", "## FASE 5"), "G14 /inizio FASE 4 non legge il percorso"
    fase5 = sezione(inizio, "## FASE 5", "## FASE 6")
    assert "## Percorso" in fase5 and fase5.index("## Todo") < fase5.index("## Percorso"), \
        "G14 /inizio FASE 5 non ha la sezione Percorso dopo i Todo"
    assert "percorso visto" in fase5 and "pausa" in fase5, "G14 /inizio FASE 5: segnalibro o pausa"
    fine = read(repo / "commands" / "fine.md")
    assert "percorso suggerisci" in fine and "percorso no" in fine and "Tenuto:" in fine, "G14 /fine"
    for nome, testo in (("skill todo", read(repo / "skills" / "todo" / "SKILL.md")), ("/fine", fine)):
        assert REGOLA in " ".join(testo.split()), f"G14 {nome} non dice: mai spostare {REGOLA}"
    assert "esercizio della settimana" in read(repo / "commands" / "guidami.md"), "G14 /guidami"
    assert "/percorso" in sezione(read(repo / "commands" / "setup.md") + "\n## FINE", "## Riepilogo finale", "## FINE"), \
        "G14 il riepilogo di /setup non nomina /percorso"
    readme = read(repo / "README.md")
    vere = len([d for d in (repo / "skills").iterdir() if (d / "SKILL.md").is_file()])
    assert vere == 5 and "**5 skill**" in readme, f"G14 il README e le skill: {vere}"
    assert "docs/esercizi.md" in readme and "`percorso`" in readme, "G14 il README non racconta il percorso"
    novita = read(repo / "NOVITA.md")
    intestazioni = [r for r in novita.splitlines() if r.startswith("## ")]
    assert intestazioni[0] == "## 2026-10-03 — Il percorso a tappe", f"G14 NOVITA in cima: {intestazioni[:1]}"
    entry = novita.split(intestazioni[0], 1)[1].split("\n## ", 1)[0]
    assert entry.rstrip().endswith(NOTA_AUTORE) and "/percorso" in entry, "G14 la entry di NOVITA"
    capitolo = repo / "docs" / "principi" / "05-tieni-la-decisione.md"
    testo = read(capitolo)
    assert testo.startswith("Bozza: la rilegge e la corregge Federico prima del rilascio su main."), "G14 il capitolo non è segnato come bozza"
    assert "automatizza la forma, frena l'impegno" in testo.lower(), "G14 il capitolo non parte dalla regola"
    riga = next((r for r in read(repo / "docs" / "principi" / "README.md").splitlines() if r.startswith("| 05 ")), "")
    assert "05-tieni-la-decisione.md" in riga and "disponibile" in riga, f"G14 indice dei principi: {riga!r}"

    def prova(c: Casa) -> None:
        for voce in c.json()["tappe"]:
            if voce["capitolo"]:
                assert (repo / voce["capitolo"]).is_file(), f"G14 capitolo inesistente: {voce['capitolo']}"
    con_casa(repo, prova)


def test_g15(repo: Path) -> None:
    def fatto_annullato(c: Casa) -> None:
        decisione(c)
        c.todo("aggiungi", "Spedire la bozza", "--chi", "io", "--progetto", "p")
        c.todo("fatto", "3")
        c.todo("ripristina", "3", "da", "fare")  # «u» del pannello dopo «f»
        assert c.json()["tappa"] == 2, "G15 un fatto annullato vale come riapertura"

    def aggiungi_annullato(c: Casa) -> None:
        c.todo("aggiungi", "Per sbaglio", "--chi", "io", "--progetto", "p")
        c.todo("ripristina", "1", "scartato", "annullato dalla pagina")  # Annulla della pagina
        v = c.json()
        assert v["tappa"] == 0, f"G15 un aggiungi annullato apre Osserva: {v['tappe'][0]}"
        decisione(c)
        assert c.prova("Delega")[1] is None, "G15 lo scarto di un annullo vale come no motivato"

    def deciso_annullato(c: Casa) -> None:
        c.todo("aggiungi", "Scegliere il piano", "--chi", "decidi", "--progetto", "p")
        c.todo("deciso", "1", "piano B")
        c.todo("modifica", "1", "--chi", "decidi", "--annullo")  # Annulla di «Ho deciso» nella pagina
        assert c.prova("Delega")[0] is None, "G15 una decisione annullata conta"

    def tasto_chi(c: Casa) -> None:
        c.todo("aggiungi", "Scegliere il piano", "--chi", "decidi", "--progetto", "p")
        c.todo("modifica", "1", "--chi", "io")  # «c» del pannello: la decisione passa dalla storia
        assert c.prova("Delega")[0] == 1, "G15 il passaggio da decidi a io non è una decisione"
        c.todo("aggiungi", "Scegliere il titolo", "--chi", "decidi", "--progetto", "p")
        c.todo("modifica", "2", "--chi", "io")
        c.todo("modifica", "2", "--chi", "decidi", "--annullo")  # «u» dopo «c»
        assert c.prova("Delega")[0] == 1, "G15 un passaggio annullato conta come decisione"

    for caso in (fatto_annullato, aggiungi_annullato, deciso_annullato, tasto_chi):
        con_casa(repo, caso)


TESTS = {
    "G01": test_g01, "G02": test_g02, "G03": test_g03, "G04": test_g04, "G05": test_g05,
    "G06": test_g06, "G07": test_g07, "G08": test_g08, "G09": test_g09, "G10": test_g10,
    "G11": test_g11, "G12": test_g12, "G13": test_g13, "G14": test_g14, "G15": test_g15,
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
            except (AssertionError, OSError, ValueError, IndexError, KeyError, TypeError, StopIteration,
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
