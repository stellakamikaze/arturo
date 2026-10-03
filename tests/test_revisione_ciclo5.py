#!/usr/bin/env python3
"""X01-X29: la revisione del ciclo 5 (3/10/2026). Ogni controllo prende un difetto confermato.

X01 una riga finale senza a capo non si mangia l'evento dopo, una write parziale si completa, e
nessuna conferma senza rilettura. X02 la rinumerazione dopo un merge tocca solo il todo in
collisione, e un todo nuovo non sposta i numeri gia' dati. X03 i comandi che scrivono stampano
gli avvisi di rinumerazione del numero indicato, `--titolo-atteso` e `--atteso` fermano la
scrittura, e il pannello li passa negli argv e negli inversi. X04 un evento con il ts prima del
crea (orologio indietro) resta suo. X05 l'Annulla della pagina risponde 409 se il todo e' cambiato
nel frattempo. X06 /aggiorna mostra guardie e permessi interi e l'elenco completo del codice che
gira da solo, mod compresi, senza taglio. X07 un todo preso in ~/.claude e' «generale», e la
FASE 4 di /inizio mostra il progetto e «generale», senza una variabile di un altro blocco. X08
fuori da git /fine legge lo stesso progetto di «ricordami di…». X09 il blocco todo di /fine regge
una HOME con uno spazio e non usa variabili fra le chiamate. X10 /inizio non butta gli avvisi.
X11 il perche' di un todo tu lo dice la persona. X12 Delega chiede due segni, e i testi lo dicono.
X13 i comandi da terminale delle novita' funzionano senza l'alias. X14 un todo decidi chiuso dalla
persona e' una decisione, e Prova conta solo i lavori di Claude. X15 un annullo dopo un passo in
mezzo toglie il passo giusto. X17 la prova nel browser di W13, nel gate, non salta. X18 il veleno
su motivo_esatto va in rosso anche senza un Python fino alla 3.11, e il gate esige un Python
vecchio. X19 la controprova di questo banco conta solo un rosso col codice del controllo. X20 il
gate rilancia todo, pagina e percorso con Python 3.8.
I difetti bassi: X21 niente caratteri di controllo nel terminale, X22 una richiesta respinta non
tiene acceso arturo web, X23 E07 senza numeri fissi, X24 «percorso riprendi» toglie il silenzio,
X25 errori della CLI con nomi per la persona, X27 la skill di /system-audit conosce i mod, X28
lo stato del percorso dichiarato locale, X29 un `dopo` scritto a cose fatte non apre Orchestra.
(X16 e X26 sono confluiti in G15 di test_percorso.py e in X07.)

Sulla base 81431a2, l'ultimo dev prima delle correzioni, ogni controllo deve fallire con un
AssertionError che comincia con il suo codice: un rosso per un file assente non conta.
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.client
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

OGGI = "2026-10-03"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}
_CARICATI = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def modulo(repo: Path, relativo: str, nome: str):
    """Carica un file del repo da provare come modulo nuovo, con il todo_store del suo bin/."""
    file = repo / relativo
    assert file.is_file(), f"{nome[:3]} manca {relativo}"
    bin_dir = str(repo / "bin")
    sys.path.insert(0, bin_dir)
    vecchio = sys.modules.pop("todo_store", None)
    try:
        caricatore = importlib.machinery.SourceFileLoader(f"x_{len(_CARICATI)}_{nome}", str(file))
        spec = importlib.util.spec_from_loader(caricatore.name, caricatore)
        m = importlib.util.module_from_spec(spec)
        caricatore.exec_module(m)
    finally:
        sys.path.remove(bin_dir)
        sys.modules.pop("todo_store", None)
        if vecchio is not None:
            sys.modules["todo_store"] = vecchio
    _CARICATI.append(m)
    return m


class Casa:
    """Una HOME di prova: la CLI del repo da provare, lanciata da una cartella a scelta."""

    def __init__(self, repo: Path, base: Path, nome: str = "home"):
        self.repo = repo
        self.home = base / nome
        self.home.mkdir(parents=True)
        self.registro = self.home / ".claude" / "data" / "todo" / "eventi.jsonl"

    def env(self, **altro) -> dict:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_OGGI=OGGI,
                   PYTHONIOENCODING="utf-8", GIT_CEILING_DIRECTORIES=str(self.home.parent), **GIT_ENV)
        env.pop("ARTURO_TODO", None)
        env.update(altro)
        return env

    def arturo(self, *argomenti: str, cwd: Path | None = None, codice: str = "X", ok: bool = True,
               oggi: str = OGGI) -> subprocess.CompletedProcess:
        r = subprocess.run([sys.executable, str(self.repo / "bin" / "arturo"), *argomenti], cwd=str(cwd or self.home),
                           env=self.env(ARTURO_OGGI=oggi), capture_output=True, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        if ok:
            assert r.returncode == 0, f"{codice} arturo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()[-300:]}"
        return r

    def todo(self, *argomenti: str, **opzioni) -> subprocess.CompletedProcess:
        return self.arturo("todo", *argomenti, **opzioni)

    def vista(self, codice: str) -> dict:
        return json.loads(self.todo("--tutti", "--json", codice=codice).stdout)

    def aperti(self, codice: str) -> dict:
        return {t["id"]: t for g in self.vista(codice)["gruppi"] for t in g["todo"]}

    def percorso(self, codice: str) -> dict:
        return json.loads(self.arturo("percorso", "--json", codice=codice).stdout)

    def bash(self, script: str, cwd: Path, codice: str) -> subprocess.CompletedProcess:
        r = subprocess.run(["bash", "-c", script], cwd=str(cwd), env=self.env(), capture_output=True, timeout=120)
        r.stdout, r.stderr = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
        return r

    def installa(self) -> None:
        """La CLI dove la cercano i comandi: ~/.claude/bin."""
        shutil.copytree(str(self.repo / "bin"), str(self.home / ".claude" / "bin"),
                        ignore=shutil.ignore_patterns("__pycache__"))

    def scrivi_righe(self, eventi: list) -> None:
        self.registro.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registro, "a", encoding="utf-8") as f:
            for e in eventi:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


def con_casa(repo: Path, prova, nome: str = "home") -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(Casa(repo, Path(tmp), nome))


def crea(uid: str, numero: int, titolo: str, ts: str, **dati) -> dict:
    return {"v": 1, "ts": ts, "ev": "c" + uid[1:], "todo": uid, "tipo": "crea", "id": numero,
            "dati": dict({"titolo": titolo, "progetto": "p"}, **dati)}


def evento(uid: str, tipo: str, ts: str, ev: str, **dati) -> dict:
    return {"v": 1, "ts": ts, "ev": ev, "todo": uid, "tipo": tipo, "dati": dati}


def ora(minuti: float) -> str:
    return (dt.datetime(2026, 10, 3, 10, 0, tzinfo=dt.timezone.utc) + dt.timedelta(minutes=minuti)).isoformat(
        timespec="microseconds")


def blocco(testo: str, dopo: str, codice: str) -> str:
    """Il primo blocco bash dopo il testo `dopo`."""
    assert dopo in testo, f"{codice} non trovo «{dopo}»"
    m = re.search(r"```bash\n(.*?)```", testo.split(dopo, 1)[1], re.S)
    assert m, f"{codice} nessun blocco bash dopo «{dopo}»"
    return m.group(1)


def righe_todo(testo: str) -> str:
    """Le sole righe che leggono i todo con la CLI, per lanciarle senza il resto del blocco."""
    return "\n".join(r for r in testo.splitlines() if "arturo" in r and " todo" in r and not r.lstrip().startswith("#"))


# --- X01 ----------------------------------------------------------------------------------------

def test_x01(repo: Path) -> None:
    def tronca(c: Casa) -> None:
        c.todo("aggiungi", "uno", "--progetto", "p", codice="X01")
        c.todo("aggiungi", "due", "--progetto", "p", codice="X01")
        dati = c.registro.read_bytes()
        c.registro.write_bytes(dati[:-40])  # una scrittura interrotta: l'ultima riga senza a capo
        r = c.todo("fatto", "1", codice="X01", ok=False)
        aperti = c.aperti("X01")
        assert 1 not in aperti, f"X01 «{r.stdout.strip()}» rc={r.returncode}, ma #1 resta aperto: l'evento si è incollato alla riga rotta"
        assert r.returncode == 0, f"X01 la chiusura di #1 è scritta, ma la CLI esce {r.returncode}: {r.stderr}"
    con_casa(repo, tronca)

    ts = modulo(repo, "bin/todo_store.py", "x01_store")
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "eventi.jsonl"
        vero = os.write
        with mock.patch.object(ts.os, "write", side_effect=lambda fd, b: vero(fd, bytes(b[:7]))):
            t = ts.aggiungi({"titolo": "Un titolo abbastanza lungo da servire più write", "progetto": "p"}, file)
        todo, avvisi = ts.carica(file)
        assert not avvisi and [x["titolo"] for x in todo.values()] == [t["titolo"]], \
            f"X01 una write parziale lascia la riga a metà: {avvisi}"
        with mock.patch.object(ts, "_scrivi_molti", lambda *a, **k: None):
            try:
                ts.registra(t["id"], "nota", {"testo": "persa"}, file)
            except ts.ErroreTodo:
                pass
            else:
                raise AssertionError("X01 una scrittura che non arriva nel registro viene confermata")


# --- X02 ----------------------------------------------------------------------------------------

def test_x02(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.scrivi_righe([crea("a" * 32, 1, "A: primo", ora(0)), crea("b" * 32, 1, "B: comprare il pane", ora(1)),
                        crea("d" * 32, 2, "A: mandare il contratto", ora(2))])
        v = c.vista("X02")
        numeri = {t["titolo"]: t["id"] for g in v["gruppi"] for t in g["todo"]}
        assert numeri["A: mandare il contratto"] == 2, f"X02 un todo senza collisione cambia numero: {numeri}"
        assert numeri == {"A: primo": 1, "A: mandare il contratto": 2, "B: comprare il pane": 3}, f"X02 numeri: {numeri}"
        assert len(v["avvisi"]) == 1 and "B: comprare il pane" in v["avvisi"][0], f"X02 avvisi falsi: {v['avvisi']}"
        c.todo("aggiungi", "Nuovo", "--progetto", "p", codice="X02")
        dopo = {t["titolo"]: t["id"] for g in c.vista("X02")["gruppi"] for t in g["todo"]}
        assert dopo["B: comprare il pane"] == 3 and dopo["Nuovo"] == 4, f"X02 un todo nuovo sposta i numeri: {dopo}"
        r = c.todo("fatto", "2", codice="X02")
        assert "A: mandare il contratto" in r.stdout, f"X02 fatto 2 chiude un altro todo: {r.stdout}"
    con_casa(repo, prova)


# --- X03 ----------------------------------------------------------------------------------------

def verbi_del_pannello(repo: Path, riga: dict, codice: str) -> dict:
    verbi = repo / "skills" / "dafare" / "hooks" / "verbi.mjs"
    programma = ("const { pathToFileURL } = require('url');"
                 "import(pathToFileURL(process.argv[1]).href).then(m => {"
                 " const t = JSON.parse(process.argv[2]); const fuori = {};"
                 " for (const [k, v] of Object.entries(m.VERBI)) fuori[k] = { argv: v.argv(t), inverso: v.inverso(t) };"
                 " process.stdout.write(JSON.stringify(fuori)); })")
    node = shutil.which("node")
    assert node, f"{codice} node mancante: il gate lo richiede"
    r = subprocess.run([node, "-e", programma, str(verbi), json.dumps(riga)], capture_output=True, timeout=60)
    assert r.returncode == 0, f"{codice} node non carica verbi.mjs: {r.stderr.decode('utf-8', 'replace')[-300:]}"
    return json.loads(r.stdout.decode("utf-8"))


def test_x03(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.scrivi_righe([crea("a" * 32, 1, "Mandare il preventivo", ora(0)),
                        crea("b" * 32, 1, "Firmare il contratto", ora(1))])
        r = c.todo("fatto", "1", codice="X03")
        assert "Attenzione" in r.stderr and "#1" in r.stderr and "ora è #2" in r.stderr, \
            f"X03 fatto 1 dopo una rinumerazione non mostra l'avviso: {r.stderr!r}"
        prima = c.registro.read_bytes()
        r = c.todo("fatto", "2", "--titolo-atteso=Mandare il preventivo", codice="X03", ok=False)
        assert r.returncode == 2 and "non è più come lo aspettavi" in r.stderr, \
            f"X03 --titolo-atteso non ferma la scrittura su un altro todo: rc={r.returncode} {r.stderr}"
        assert c.registro.read_bytes() == prima, "X03 --titolo-atteso diverso ha scritto nel registro"
        r = c.todo("ripristina", "1", "--atteso=stato=fermo", "--", "da fare", codice="X03", ok=False)
        assert r.returncode == 2 and c.registro.read_bytes() == prima, f"X03 --atteso non ferma ripristina: {r.stderr}"
        # Il pannello: ogni tasto e ogni inverso portano il titolo, gli inversi anche lo stato atteso.
        riga = {"id": 2, "titolo": "Firmare il contratto", "stato": "da fare", "motivo": None, "chi": "tu",
                "quando": "settimana"}
        verbi = verbi_del_pannello(repo, riga, "X03")
        for nome, v in verbi.items():
            for chiave in ("argv", "inverso"):
                assert "--titolo-atteso=Firmare il contratto" in v[chiave], f"X03 {nome} {chiave} senza il titolo: {v[chiave]}"
        assert "--atteso=stato=fatto" in verbi["fatto"]["inverso"], f"X03 l'inverso di fatto: {verbi['fatto']['inverso']}"
        assert "--atteso=chi=decidi" in verbi["chi"]["inverso"], f"X03 l'inverso di chi: {verbi['chi']['inverso']}"
        c.todo(*verbi["fatto"]["argv"], codice="X03")
        c.todo("riprendi", "2", codice="X03")
        c.todo("ferma", "2", "aspetto la firma", codice="X03")  # Claude, fra il tasto e «u»
        r = c.todo(*verbi["fatto"]["inverso"], codice="X03", ok=False)
        t = c.aperti("X03").get(2) or {}
        assert r.returncode == 2 and t.get("stato") == "fermo" and t.get("motivo") == "aspetto la firma", \
            f"X03 «u» del pannello cancella il FERMO scritto nel frattempo: rc={r.returncode} {t}"
    con_casa(repo, prova)


# --- X04 ----------------------------------------------------------------------------------------

def test_x04(repo: Path) -> None:
    def prova(c: Casa) -> None:
        uid = "a" * 32
        c.scrivi_righe([crea(uid, 1, "Rinnovare la PEC", ora(3)),
                        evento(uid, "stato", ora(0), "e" * 32, stato="fatto", motivo="")])
        v = c.vista("X04")
        chiusi = {t["id"]: t["stato"] for t in v.get("chiusi_todo", [])}
        assert chiusi.get(1) == "fatto" and not v["avvisi"], \
            f"X04 un evento con il ts prima del crea si perde: chiusi={chiusi} avvisi={v['avvisi']}"
    con_casa(repo, prova)


# --- X05 ----------------------------------------------------------------------------------------

def test_x05(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ambiente = {"ARTURO_TODO": str(Path(tmp) / "eventi.jsonl"), "ARTURO_OGGI": OGGI}
        with mock.patch.dict(os.environ, ambiente):
            web = modulo(repo, "bin/arturo_web.py", "x05_web")
            stato = web.Stato("chiave", "p", 1800)

            def azione(**corpo):
                return web.esegui(stato, web.controlla_corpo(corpo))

            def rifiutata(corpo: dict) -> bool:
                try:
                    azione(**corpo)
                except web.ErroreRichiesta as e:
                    return e.codice == 409
                return False

            azione(azione="aggiungi", campi={"titolo": "Scrivere a Rossi", "progetto": "p"})
            annulla = azione(azione="fatto", id=1)["annulla"]
            web.ts.registra(1, "stato", {"stato": "da fare"})  # Claude, dalla CLI: riprendi
            web.ts.registra(1, "stato", {"stato": "fermo", "motivo": "aspetto la risposta di Rossi"})
            assert rifiutata(annulla), "X05 l'Annulla di un fatto vecchio cancella il FERMO scritto nel frattempo"
            t = web.ts.per_id(web.ts.carica()[0], 1)
            assert (t["stato"], t["motivo"]) == ("fermo", "aspetto la risposta di Rossi"), f"X05 dopo il 409: {t['stato']}"

            annulla = azione(azione="modifica", id=1, campi={"quando": "oggi"})["annulla"]
            web.ts.registra(1, "modifica", {"quando": "più avanti"})
            assert rifiutata(annulla), "X05 l'Annulla di una modifica cancella un valore scritto nel frattempo"

            annulla = azione(azione="riprendi", id=1)["annulla"]
            assert not rifiutata(annulla), "X05 un Annulla subito dopo il passo viene rifiutato"
    sys.modules.pop("todo_store", None)


# --- X06 ----------------------------------------------------------------------------------------

def test_x06(repo: Path) -> None:
    testo = read(repo / "commands" / "aggiorna.md")
    codice = blocco(testo, "**Leggi cosa cambia nel codice che gira da solo**", "X06").replace('cd "$HOME/.claude"\n', "")
    assert not re.search(r"\|\s*head\b", codice), "X06 il diff di /aggiorna è tagliato con head"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        env = dict(os.environ, HOME=str(base), **GIT_ENV)

        def git(cwd: Path, *argomenti: str) -> None:
            subprocess.run(["git", *argomenti], cwd=str(cwd), env=env, check=True, capture_output=True, timeout=60)

        def scrivi(radice: Path, file: dict) -> None:
            for nome, contenuto in file.items():
                (radice / nome).parent.mkdir(parents=True, exist_ok=True)
                (radice / nome).write_text(contenuto, encoding="utf-8")

        remoto, locale = base / "remoto", base / "locale"
        remoto.mkdir()
        git(remoto, "init", "-q", "-b", "main")
        scrivi(remoto, {"hooks/guardia.py": "blocca = True\n", "settings.json": "{}\n", "bin/arturo": "vecchio\n",
                        "skills/todo/SKILL.md": "skill\n"})
        git(remoto, "add", "-A")
        git(remoto, "commit", "-q", "-m", "base")
        git(base, "clone", "-q", str(remoto), str(locale))
        scrivi(remoto, {"bin/arturo": "".join(f"riga {i}\n" for i in range(900)),
                        "hooks/guardia.py": "blocca = False  # GUARDIA_ALLENTATA\n",
                        "settings.json": '{"permissions": {"allow": ["Bash(*)"]}}\n',
                        "skills/nuovo/.claude-plugin/plugin.json": '{"name": "nuovo"}\n',
                        "skills/nuovo/hooks/hooks.json": "{}\n",
                        "skills/nuovo/types/index.d.ts": "export type X = 1\n",
                        "skills/todo/SKILL.md": "skill cambiata\n"})
        git(remoto, "add", "-A")
        git(remoto, "commit", "-q", "-m", "aggiornamento")
        git(locale, "fetch", "-q", "origin")
        r = subprocess.run(["bash", "-c", "SRC=origin\n" + codice], cwd=str(locale), env=env, capture_output=True, timeout=60)
        uscita = r.stdout.decode("utf-8", "replace")
        assert "GUARDIA_ALLENTATA" in uscita and "Bash(*)" in uscita, \
            f"X06 le guardie e i permessi non arrivano interi con un bin/ grande: {uscita[-400:]!r}"
        for file in ("bin/arturo", "skills/nuovo/types/index.d.ts", "skills/nuovo/.claude-plugin/plugin.json"):
            assert re.search(r"^(?:\d+|-)\t(?:\d+|-)\t" + re.escape(file) + "$", uscita, re.M) or \
                f"diff --git a/{file} " in uscita, f"X06 /aggiorna non elenca {file}: {uscita[-600:]!r}"
    assert "Il diff copre le guardie" not in testo, "X06 /aggiorna dice ancora che un diff tagliato copre tutto"


# --- X07 ----------------------------------------------------------------------------------------

def test_x07(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.installa()
        config, libro, altro = c.home / ".claude", c.home / "libro", c.home / "altro"
        for cartella in (config, libro, altro):
            cartella.mkdir(exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=str(cartella), env=c.env(), check=True, capture_output=True)
        r = c.todo("aggiungi", "Chiamare il commercialista", "--chi", "tu", cwd=config, codice="X07")
        assert "(generale)" in r.stdout, f"X07 un todo preso dentro ~/.claude non è «generale»: {r.stdout.strip()}"
        c.todo("aggiungi", "Scrivere il capitolo tre", cwd=libro, codice="X07")
        c.todo("aggiungi", "Lavoro di un altro progetto", cwd=altro, codice="X07")
        inizio = read(repo / "commands" / "inizio.md")
        fase4 = inizio[inizio.index("## FASE 4"):inizio.index("## FASE 5")]
        codice = blocco(fase4, "## FASE 4", "X07")
        assert "$SLUG" not in codice, "X07 la FASE 4 usa $SLUG, che nasce in un altro blocco"
        r = c.bash(righe_todo(codice), libro, "X07")
        assert "Scrivere il capitolo tre" in r.stdout, f"X07 /inizio non mostra i todo del progetto: {r.stdout}"
        assert "Chiamare il commercialista" in r.stdout, f"X07 /inizio libro non mostra i todo di «generale»: {r.stdout}"
        assert "Lavoro di un altro progetto" not in r.stdout, f"X07 /inizio mostra i todo di ogni progetto: {r.stdout}"
    con_casa(repo, prova)


# --- X08 e X09 ----------------------------------------------------------------------------------

def blocco_fine(repo: Path, codice: str) -> str:
    return blocco(read(repo / "commands" / "fine.md"), "**Todo.**", codice)


def fuori_da_git(repo: Path, codice: str, nome: str) -> None:
    def prova(c: Casa) -> None:
        c.installa()
        lavoro = c.home / "Documents" / "Lavoro"
        lavoro.mkdir(parents=True)
        c.todo("aggiungi", "Chiamare la tipografia", "--chi", "tu", cwd=lavoro, codice=codice)
        r = c.bash(righe_todo(blocco_fine(repo, codice)), lavoro, codice)
        assert "Chiamare la tipografia" in r.stdout, \
            f"{codice} /fine non vede il todo di «ricordami di…» nella stessa cartella: {r.stdout!r} {r.stderr[-300:]!r}"
        assert "can't open file" not in r.stderr and "command not found" not in r.stderr, f"{codice} {r.stderr[-300:]}"
    con_casa(repo, prova, nome)


def test_x08(repo: Path) -> None:
    fuori_da_git(repo, "X08", "home")


def test_x09(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    assert "$TODO" not in fine and "TODO=" not in fine, "X09 /fine usa una variabile TODO, che sparisce fra le chiamate"
    fuori_da_git(repo, "X09", "Mario Rossi")


# --- X10 ----------------------------------------------------------------------------------------

def test_x10(repo: Path) -> None:
    inizio = read(repo / "commands" / "inizio.md")
    fase4 = inizio[inizio.index("## FASE 4"):inizio.index("## FASE 5")]
    righe = righe_todo(blocco(fase4, "## FASE 4", "X10"))
    assert "2>/dev/null" not in righe, "X10 /inizio butta gli avvisi dei todo con 2>/dev/null"
    fase5 = inizio[inizio.index("## FASE 5"):inizio.index("## FASE 6")]
    assert "Attenzione" in fase5, "X10 la FASE 5 non dice di riportare gli avvisi «Attenzione»"

    def prova(c: Casa) -> None:
        c.installa()
        c.scrivi_righe([crea("a" * 32, 1, "Mandare il preventivo", ora(0), progetto="generale"),
                        crea("b" * 32, 1, "Firmare il contratto", ora(1), progetto="generale")])
        r = c.bash("{\n" + righe + "\n} 2>&1", c.home, "X10")
        assert "Attenzione" in r.stdout and "ora è #2" in r.stdout, f"X10 la rinumerazione non arriva: {r.stdout!r}"
    con_casa(repo, prova)


# --- X11-X13: i testi ---------------------------------------------------------------------------

def test_x11(repo: Path) -> None:
    skill = read(repo / "skills" / "todo" / "SKILL.md")
    esempio = skill[skill.index("## Che cosa deve uscire"):skill.index("## I campi")]
    aggiunte = [r for r in esempio.splitlines() if "todo aggiungi" in r]
    assert aggiunte and not any("--perche" in r for r in aggiunte), \
        f"X11 l'esempio della skill todo scrive un perché che la persona non ha detto: {aggiunte}"
    for nome, testo in (("skill todo", skill), ("/fine", read(repo / "commands" / "fine.md"))):
        piatto = " ".join(testo.split())
        assert "parole sue" in piatto, f"X11 {nome} non dice che il perché lo dice la persona con parole sue"
        assert "quando lo sai dalla" not in piatto, f"X11 {nome} chiede ancora di dedurre il perché"


def test_x12(repo: Path) -> None:
    skill = " ".join(read(repo / "skills" / "percorso" / "SKILL.md").split())
    passo = skill[skill.index("2. **Racconta la tappa**"):skill.index("3. **Mostra")]
    assert "tutti" in passo and "limite" in passo, f"X12 la skill percorso dice che basta un segno per Delega: {passo[:300]}"
    novita = " ".join(read(repo / "NOVITA.md").split())
    entry = novita[novita.index("## 2026-10-03 — Il percorso a tappe"):]
    entry = entry[:entry.index("## 2026-10-03 — Il pannello")]
    assert "due segni" in entry, "X12 NOVITA dice che una decisione, un limite o un no aprono le tappe"
    readme = " ".join(read(repo / "README.md").split())
    assert "Delega chiede due segni" in readme, "X12 il README non dice che Delega chiede due segni"


def test_x13(repo: Path) -> None:
    for nome in ("NOVITA.md", "README.md"):
        testo = " ".join(read(repo / nome).split())
        assert "`arturo web` nel terminale" not in testo and "con `arturo web`." not in testo, \
            f"X13 {nome} fa scrivere `arturo web`, che esiste solo con l'alias di /setup"
        assert "python3 ~/.claude/bin/arturo web" in testo, f"X13 {nome} non dà la forma che funziona sempre"
    novita = " ".join(read(repo / "NOVITA.md").split())
    assert "scrivi `arturo todo deciso" not in novita, "X13 NOVITA fa scrivere `arturo todo deciso` senza l'alias"
    assert "FASE 7c" in read(repo / "commands" / "aggiorna.md"), "X13 /aggiorna non propone il comando breve"


# --- X14 e X15: il percorso ---------------------------------------------------------------------

def prove(v: dict, nome: str) -> list:
    return [s["prova"] for s in next(t for t in v["tappe"] if t["nome"] == nome)["segni"]]


def test_x14(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Mandare la parola d'ordine", "--chi", "tu", "--perche", "è una password", "--progetto", "p", codice="X14")
        c.todo("aggiungi", "Scegliere la tariffa", "--chi", "decidi", "--progetto", "p", codice="X14")
        c.todo("nota", "2", "Ho scelto 400 al giorno", codice="X14")
        c.todo("fatto", "2", codice="X14")
        c.todo("aggiungi", "Partecipare al bando", "--chi", "decidi", "--progetto", "p", codice="X14")
        c.todo("scarta", "3", "non partecipo: non è il nostro pubblico", codice="X14")
        v = c.percorso("X14")
        assert prove(v, "Prova") == [None], f"X14 Prova attribuisce a Claude il todo decidi chiuso dalla persona: {prove(v, 'Prova')}"
        assert prove(v, "Delega")[0] == 2, f"X14 il todo decidi chiuso dalla persona non è una decisione: {prove(v, 'Delega')}"
        c.todo("aggiungi", "Riassunto del bando", "--chi", "io", "--progetto", "p", codice="X14")
        c.todo("fatto", "4", codice="X14")
        v = c.percorso("X14")
        assert v["tappa"] == 3 and prove(v, "Prova") == [4], f"X14 tappa {v['tappa']}, Prova {prove(v, 'Prova')}"
    con_casa(repo, prova)


def test_x15(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Spedire la bozza", "--chi", "io", "--progetto", "p", codice="X15")
        c.todo("fatto", "1", codice="X15")
        c.todo("riprendi", "1", codice="X15")  # «r» nel pannello: l'inverso salvato è «ripristina 1 fatto»
        c.todo("fatto", "1", codice="X15")  # Claude rifà il lavoro
        c.todo("ripristina", "1", "fatto", codice="X15")  # «u»: annulla la riapertura
        v = c.percorso("X15")
        assert prove(v, "Prova") == [1], f"X15 l'annullo toglie la chiusura vera: Prova {prove(v, 'Prova')}"
        assert prove(v, "Delega")[1] is None, f"X15 la riapertura annullata conta come limite: {prove(v, 'Delega')}"
    con_casa(repo, prova)


# --- X17-X20: i banchi e il gate ----------------------------------------------------------------

def gate(repo: Path) -> str:
    return read(repo / "tests" / "verifica-allineamento.sh")


def test_x17(repo: Path) -> None:
    assert "node 22" in read(repo / "tests" / "prova_pagina.js"), "X17 prova_pagina.js promette node 18, che non ha WebSocket"
    assert re.search(r"ARTURO_PROVA_BROWSER=obbligatoria", gate(repo)), "X17 il gate lascia saltare la prova nel browser"
    banco = modulo(repo, "tests/test_web.py", "x17_web")
    with mock.patch.dict(os.environ, {"ARTURO_PROVA_BROWSER": "obbligatoria"}), \
            mock.patch.object(banco, "cerca_chrome", lambda: None):
        try:
            banco.test_w13(repo)
        except AssertionError as e:
            assert "obbligatoria" in str(e), f"X17 W13 fallisce per un altro motivo: {e}"
        else:
            raise AssertionError("X17 senza Chrome W13 passa anche quando la prova nel browser è obbligatoria")


def test_x18(repo: Path) -> None:
    testo = gate(repo)
    assert "PYTHON_VECCHIO" in testo and "3.11" in testo, "X18 il gate non esige un Python fino alla 3.11 per U04"
    banco = modulo(repo, "tests/test_pannello.py", "x18_pannello")
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "repo"
        shutil.copytree(str(repo), str(copia), ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        cli = copia / "bin" / "arturo"
        sorgente = read(cli)
        firma = "def motivo_esatto(argv: list) -> tuple:\n"
        assert firma in sorgente, "X18 motivo_esatto manca in bin/arturo"
        cli.write_text(sorgente.replace(firma, firma + "    return argv, None  # veleno\n", 1), encoding="utf-8")
        assert "# veleno" in read(cli), "X18 il veleno non entra in motivo_esatto"
        with mock.patch.object(banco, "pythons", lambda: [sys.executable]):
            try:
                banco.test_u04(copia)
            except AssertionError as e:
                assert "U04" in str(e), f"X18 U04 fallisce per un altro motivo: {e}"
            else:
                raise AssertionError("X18 con il solo Python del banco il veleno su motivo_esatto passa U04")


def baseline(tests: dict, repo: Path) -> tuple:
    """La controprova: (codici rossi col loro codice, controlli rossi per un altro motivo o verdi)."""
    rossi, altro = [], []
    for nome, test in tests.items():
        try:
            test(repo)
        except AssertionError as e:
            if str(e).startswith(nome):
                rossi.append(nome)
            else:
                altro.append(f"{nome}: AssertionError senza il codice: {str(e)[:160]}")
        except Exception as e:  # noqa: BLE001 - un file assente non e' il motivo del controllo
            altro.append(f"{nome}: {type(e).__name__} {str(e)[:160]}")
        else:
            altro.append(f"{nome}: verde")
    return rossi, altro


def test_x19(repo: Path) -> None:
    assert "test_revisione_ciclo5.py 81431a2" in gate(repo), "X19 il gate non controprova la revisione del ciclo 5 su 81431a2"

    def assente(_repo):
        raise FileNotFoundError("bin/percorso.py")

    def giusto(_repo):
        raise AssertionError("X98 il motivo atteso")

    def sbagliato(_repo):
        raise AssertionError("X97 manca bin/arturo")

    rossi, altro = baseline({"X99": assente, "X98": giusto, "X96": sbagliato}, repo)
    assert rossi == ["X98"] and len(altro) == 2, f"X19 la controprova conta un rosso senza il suo codice: {rossi} {altro}"


def test_x20(repo: Path) -> None:
    testo = gate(repo)
    m = re.search(r"PY38_BANCHI=\(([^)]*)\)", testo)
    assert m and '"$PY38" -B "$REPO/tests/$test"' in testo, "X20 il gate non rilancia i banchi con Python 3.8"
    for banco in ("test_todo.py", "test_web.py", "test_percorso.py"):
        assert banco in m.group(1), f"X20 il gate non rilancia {banco} con Python 3.8"


# --- i difetti bassi ----------------------------------------------------------------------------

def test_x21(repo: Path) -> None:
    def prova(c: Casa) -> None:
        sporco = "Paga \x1b]52;c;ZWNobyBwd25lZA==\x07bolletta \x1b[2J"
        c.todo("aggiungi", sporco, "--progetto", "p", codice="X21")
        c.scrivi_righe([crea("b" * 32, 7, "Vecchia \x1b[31mriga\x9b2J", ora(0))])
        for argomenti in ((), ("mostra", "1"), ("mostra", "7"), ("--json",), ("oggi", "--giorni", "30")):
            r = c.todo(*argomenti, codice="X21")
            assert not re.search(r"[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f]", r.stdout + r.stderr), \
                f"X21 caratteri di controllo nel terminale con «todo {' '.join(argomenti)}»: {(r.stdout + r.stderr)!r}"
        assert "Paga ]52;c;ZWNobyBwd25lZA==bolletta [2J" in c.todo(codice="X21").stdout, "X21 il titolo pulito si perde"
    con_casa(repo, prova)


def test_x22(repo: Path) -> None:
    def prova(c: Casa) -> None:
        processo = subprocess.Popen([sys.executable, str(repo / "bin" / "arturo"), "web", "--non-aprire"], cwd=str(c.home),
                                    env=c.env(ARTURO_WEB_INATTIVO="2", PYTHONUNBUFFERED="1"),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            riga = processo.stdout.readline().decode("utf-8")
            m = re.search(r"http://127\.0\.0\.1:(\d+)/", riga)
            assert m, f"X22 arturo web non stampa il link: {riga!r}"
            porta, fine = int(m.group(1)), time.monotonic() + 8
            while time.monotonic() < fine and processo.poll() is None:
                try:
                    conn = http.client.HTTPConnection("127.0.0.1", porta, timeout=2)
                    conn.request("GET", "/static/app.js", headers={"Host": "altro.example"})
                    conn.getresponse().read()
                    conn.close()
                except (OSError, http.client.HTTPException, socket.timeout):
                    pass
                time.sleep(0.3)
            assert processo.poll() is not None, "X22 richieste respinte tengono acceso arturo web oltre il tempo di inattività"
        finally:
            if processo.poll() is None:
                processo.kill()
            processo.wait(timeout=10)
            processo.stdout.close()
            processo.stderr.close()
    con_casa(repo, prova)


def test_x23(repo: Path) -> None:
    testo = read(repo / "docs" / "esercizi.md")
    e07 = testo[testo.index("## E07"):testo.index("## E08")]
    assert not re.search(r"arturo todo (?:dopo|deciso) \d", e07), "X23 E07 usa numeri di todo fissi"


def test_x24(repo: Path) -> None:
    def prova(c: Casa) -> None:
        domani = (dt.date.fromisoformat(OGGI) + dt.timedelta(days=1)).isoformat()
        assert c.arturo("percorso", "suggerisci", codice="X24", ok=False).returncode == 0, "X24 il primo suggerimento"
        c.arturo("percorso", "no", codice="X24")
        c.arturo("percorso", "riprendi", codice="X24", oggi=domani)
        r = c.arturo("percorso", "suggerisci", codice="X24", ok=False, oggi=domani)
        assert r.returncode == 0, f"X24 dopo «riprendi» il silenzio del no resta: {r.stdout.strip()}"
    con_casa(repo, prova)


def test_x25(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Uno", "--progetto", "p", codice="X25")
        r = c.todo("ripristina", "1", codice="X25", ok=False)
        assert r.returncode == 2 and "resto" not in r.stderr.split("\n\n")[0], f"X25 un nome interno nell'errore: {r.stderr[:200]}"
        r = c.todo("aggiungi", "-x", codice="X25", ok=False)
        assert "--" in r.stderr.split("\n\n")[0] and "trattino" in r.stderr, \
            f"X25 un titolo con il trattino non dice come scriverlo: {r.stderr[:200]}"
    con_casa(repo, prova)


def test_x27(repo: Path) -> None:
    skill = read(repo / "skills" / "system-audit" / "SKILL.md")
    punto = next((r for r in skill.splitlines() if r.startswith("6. ")), "")
    assert "plugin.json" in punto and "mod" in punto, f"X27 il punto 6 di /system-audit non conosce i mod: {punto}"


def test_x28(repo: Path) -> None:
    def prova(c: Casa) -> None:
        aiuto = c.arturo("aiuto", codice="X28").stdout
        assert "session-env/percorso.json" in aiuto, "X28 l'aiuto di arturo non dice dove sta lo stato del percorso"
    con_casa(repo, prova)
    for nome in ("NOVITA.md", "skills/percorso/SKILL.md"):
        assert "solo sul computer" in " ".join(read(repo / nome).split()) or \
            "solo su questo computer" in " ".join(read(repo / nome).split()), \
            f"X28 {nome} non dice che pausa e silenzi valgono su un computer solo"


def test_x29(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Scegliere il titolo", "--chi", "decidi", "--progetto", "p", codice="X29")
        c.todo("deciso", "1", "titolo B", codice="X29")
        c.todo("aggiungi", "Impaginare", "--chi", "io", "--progetto", "p", codice="X29")
        c.todo("fatto", "2", codice="X29")
        c.todo("dopo", "2", "1", codice="X29")  # il collegamento arriva a cose fatte
        v = c.percorso("X29")
        assert prove(v, "Orchestra") == [None], f"X29 un dopo scritto a cose fatte apre Orchestra: {prove(v, 'Orchestra')}"
    con_casa(repo, prova)


TESTS = {
    "X01": test_x01, "X02": test_x02, "X03": test_x03, "X04": test_x04, "X05": test_x05, "X06": test_x06,
    "X07": test_x07, "X08": test_x08, "X09": test_x09, "X10": test_x10, "X11": test_x11, "X12": test_x12,
    "X13": test_x13, "X14": test_x14, "X15": test_x15, "X17": test_x17, "X18": test_x18, "X19": test_x19,
    "X20": test_x20, "X21": test_x21, "X22": test_x22, "X23": test_x23, "X24": test_x24, "X25": test_x25,
    "X27": test_x27, "X28": test_x28, "X29": test_x29,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
