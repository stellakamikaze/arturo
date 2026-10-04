#!/usr/bin/env python3
"""W01-W15: la pagina dei todo nel browser, `arturo web` (ciclo 3, 3/10/2026).

W01 parte e ascolta solo su 127.0.0.1, si ferma dopo 30 minuti, --host non esiste e le
opzioni sbagliate rispondono in italiano. W02 la chiave: senza, niente pagina e niente API.
W03 un altro sito (Host, Origin, Content-Type, OPTIONS) non passa e nessuna risposta apre
CORS. W04 la pagina legge quello che legge la CLI. W05 un todo aggiunto dalla pagina arriva
alla CLI con gli accenti veri e con i separatori Unicode. W06 la stessa sequenza dalla CLI e
dalla pagina scrive gli stessi eventi. W07 gli errori sono del store, in italiano, e il
terminale resta zitto. W08 un numero che indica un altro todo dà 409 e non scrive. W09
Annulla rimette lo stato di prima, anche dopo «Ho deciso», e non cancella niente. W10 un
titolo ostile resta testo, e la pagina non usa la rete esterna. W11 solo i file statici
previsti. W12 si spegne da sola dopo il tempo di inattività e dal bottone, mai senza chiave.
W13 accessibilità statica, Regola della Stella, nomi di «chi» uguali allo store, pannello che
tiene i campi e si chiude con il suo todo (nel browser se Chrome c'è, sul sorgente sempre).
W14 pagina e CLI scrivono insieme senza id doppi. W15 aiuto, skill, README e NOVITA raccontano
la pagina. W16 il tavolo dei progetti: da_dove e percorso nella vista, /api/todo
con chiave, Host e Origin, storia con i numeri e non con gli uid.

Ogni server parte davvero (--non-aprire --porta 0) in una HOME isolata e si chiude sempre.
Sulla base 6ef1c0c (l'ultimo commit prima del ciclo 3) ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

OGGI = "2026-10-03"  # un sabato
VIETATI_JS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function",
              'setAttribute("style"', "setAttribute('style'")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ambiente(home: Path, **altro) -> dict:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_OGGI=OGGI, PYTHONIOENCODING="utf-8",
               PYTHONUNBUFFERED="1")
    for chiave in ("ARTURO_TODO", "ARTURO_WEB_INATTIVO"):
        env.pop(chiave, None)
    env.update(altro)
    return env


class Casa:
    """Una HOME di prova: la CLI del repo e il suo registro."""

    def __init__(self, repo: Path, base: Path, nome: str = "home"):
        self.repo = repo
        self.home = base / nome
        self.home.mkdir()
        self.registro = self.home / ".claude" / "data" / "todo" / "eventi.jsonl"

    def cli(self, *argomenti: str, ok: bool = True) -> subprocess.CompletedProcess:
        r = subprocess.run([sys.executable, str(self.repo / "bin" / "arturo"), *argomenti], cwd=str(self.home),
                           env=ambiente(self.home), capture_output=True, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        if ok:
            assert r.returncode == 0, f"arturo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()}"
        return r

    def todo(self, *argomenti: str) -> subprocess.CompletedProcess:
        return self.cli("todo", *argomenti)

    def json(self, *argomenti: str) -> dict:
        return json.loads(self.todo(*argomenti, "--json").stdout)

    def byte(self) -> bytes:
        return self.registro.read_bytes() if self.registro.exists() else b""


class Server:
    """`arturo web` avviato davvero. Il blocco with lo chiude sempre, anche se il test fallisce."""

    def __init__(self, casa: Casa, *argomenti: str, **env):
        self.casa = casa
        self.argomenti = argomenti or ("--non-aprire", "--porta", "0")
        self.env = env
        self.uscita, self.errori = [], []

    def __enter__(self):
        self.p = subprocess.Popen([sys.executable, str(self.casa.repo / "bin" / "arturo"), "web", *self.argomenti],
                                  cwd=str(self.casa.home), env=ambiente(self.casa.home, **self.env),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for flusso, righe in ((self.p.stdout, self.uscita), (self.p.stderr, self.errori)):
            threading.Thread(target=self._leggi, args=(flusso, righe), daemon=True).start()
        limite = time.time() + 15
        while time.time() < limite:
            for riga in list(self.uscita):
                m = re.search(r"http://127\.0\.0\.1:(\d+)/\?t=([A-Za-z0-9_-]+)", riga)
                if m:
                    self.porta, self.token = int(m.group(1)), m.group(2)
                    return self
            if self.p.poll() is not None:
                time.sleep(0.2)
                break
            time.sleep(0.05)
        self.chiudi()
        raise AssertionError(f"arturo web non stampa il link entro 15 s: {self.uscita} {self.errori}")

    @staticmethod
    def _leggi(flusso, righe: list) -> None:
        for riga in iter(flusso.readline, b""):
            righe.append(riga.decode("utf-8", errors="replace"))

    def chiudi(self) -> None:
        if self.p.poll() is None:
            self.p.kill()
        try:
            self.p.wait(10)
        except subprocess.TimeoutExpired:
            pass

    def __exit__(self, *_):
        self.chiudi()

    def chiedi(self, metodo: str, percorso: str, corpo=None, chiave: bool = True, intestazioni: dict = None,
               grezzo: bytes = None) -> tuple:
        """Una richiesta HTTP. Torna (codice, intestazioni in minuscolo, corpo in byte)."""
        h = {}
        if chiave:
            h["X-Arturo-Token"] = self.token
        if corpo is not None or grezzo is not None:
            h["Content-Type"] = "application/json"
        h.update(intestazioni or {})
        dati = grezzo if grezzo is not None else (json.dumps(corpo).encode("utf-8") if corpo is not None else None)
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=15)
        try:
            c.request(metodo, percorso, body=dati, headers=h)
            r = c.getresponse()
            return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
        finally:
            c.close()

    def vista(self) -> dict:
        codice, _, corpo = self.chiedi("GET", "/api/vista")
        assert codice == 200, f"/api/vista: {codice} {corpo[:200]!r}"
        return json.loads(corpo)

    def azione(self, attesa: int = 200, **corpo) -> dict:
        codice, _, risposta = self.chiedi("POST", "/api/azione", corpo)
        assert codice == attesa, f"azione {corpo}: {codice} invece di {attesa}: {risposta[:300]!r}"
        return json.loads(risposta)

    def attendi_uscita(self, secondi: float):
        try:
            return self.p.wait(secondi)
        except subprocess.TimeoutExpired:
            return None


def con_casa(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(Casa(repo, Path(tmp)))


def italiano(corpo: bytes, cosa: str) -> None:
    testo = corpo.decode("utf-8")
    assert "Error" not in testo and "Not Found" not in testo, f"{cosa}: risposta in inglese {testo[:200]!r}"
    assert re.search(r"[a-zàèéìòù]{4,}", testo) and any(p in testo.lower() for p in (" la ", " il ", " non ", "solo", "qui")), \
        f"{cosa}: la risposta non è una frase italiana {testo[:200]!r}"


def ip_esterno():
    """L'indirizzo con cui la macchina esce in rete, senza mandare pacchetti. None senza rete."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))
        ip = s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()
    return None if ip.startswith("127.") or ip == "0.0.0.0" else ip


# --- W01-W15 --------------------------------------------------------------------

def test_w01(repo: Path) -> None:
    def prova(c: Casa) -> None:
        with Server(c) as s:
            seconda = next((r for r in s.uscita if "In ascolto su" in r), "")
            assert f"In ascolto su 127.0.0.1:{s.porta}" in seconda, f"W01 seconda riga: {s.uscita}"
            assert "Si ferma dopo 30 minuti" in seconda, f"W01 il tempo di spegnimento non è 30 minuti: {seconda!r}"
            codice, h, corpo = s.chiedi("GET", f"/?t={s.token}", chiave=False)
            testo = corpo.decode("utf-8")
            assert codice == 200 and h["content-type"].startswith("text/html"), f"W01 pagina: {codice} {h}"
            assert 'lang="it"' in testo and f'content="{s.token}"' in testo and "{{TOKEN}}" not in testo, \
                "W01 la pagina non porta lang o la chiave"
            csp = h.get("content-security-policy", "")
            assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp and "unsafe-inline" not in csp, \
                f"W01 CSP: {csp!r}"
            ip = ip_esterno()
            if ip is None:
                print("W01 nota: nessun indirizzo di rete, resta solo il controllo sul sorgente")
            else:
                prova_tcp = socket.socket()
                prova_tcp.settimeout(3)
                try:
                    prova_tcp.connect((ip, s.porta))
                    raggiunto = True
                except OSError:
                    raggiunto = False
                finally:
                    prova_tcp.close()
                assert not raggiunto, f"W01 la pagina risponde anche su {ip}:{s.porta}"
        r = c.cli("web", "--host", "0.0.0.0", ok=False)
        assert r.returncode == 2 and "127.0.0.1" in r.stderr and "usage" not in r.stderr.lower(), \
            f"W01 --host: rc={r.returncode} {r.stderr!r}"
        for aiuto in (("aiuto",), ("-h",), ("--help",), ("--non-aprire", "--help"), ("--non-aprire", "aiuto"),
                      ("--porta", "0", "-h")):
            r = c.cli("web", *aiuto, ok=False)
            assert r.returncode == 0 and "--porta" in r.stdout and "--non-aprire" in r.stdout, \
                f"W01 arturo web {' '.join(aiuto)}: rc={r.returncode} {r.stdout!r} {r.stderr!r}"
        for sbagliati in (("--porta", "abc"), ("--porta", "-1"), ("--porta", "70000"), ("--boh",)):
            r = c.cli("web", *sbagliati, "--non-aprire", ok=False)
            inglese = [x for x in ("Traceback", "Error", "argument", "invalid", "unrecognized", "usage") if x in r.stderr]
            assert r.returncode == 2 and r.stderr.startswith("arturo web:") and not inglese, \
                f"W01 arturo web {' '.join(sbagliati)}: rc={r.returncode} {r.stderr!r}"
        with Server(c, ARTURO_WEB_INATTIVO="nan") as s:
            seconda = next((r for r in s.uscita if "In ascolto su" in r), "")
            assert "Si ferma dopo 30 minuti" in seconda, f"W01 ARTURO_WEB_INATTIVO=nan: {seconda!r}"
    con_casa(repo, prova)

    # Senza rete il controllo dall'esterno non c'è: il sorgente deve legare il server a 127.0.0.1.
    sorgente = read(repo / "bin" / "arturo_web.py")
    assert re.search(r'^HOST = "127\.0\.0\.1"$', sorgente, re.M), "W01 HOST non è 127.0.0.1"
    legami = re.findall(r"ThreadingHTTPServer\(\(([^,]+),", sorgente)
    assert legami == ["HOST"], f"W01 il server non si lega a HOST: {legami}"


def test_w02(repo: Path) -> None:
    def prova(c: Casa) -> None:
        with Server(c) as s:
            for percorso in ("/", "/?t=sbagliata", "/?t="):
                codice, _, corpo = s.chiedi("GET", percorso, chiave=False)
                assert codice == 403, f"W02 {percorso}: {codice}"
                italiano(corpo, f"W02 {percorso}")
                assert "link" in corpo.decode("utf-8"), "W02 la pagina negata non dice cosa aprire"
                assert 'href="static/stile.css"' in corpo.decode("utf-8"), "W02 la pagina negata collega lo stile con un percorso assoluto"
            assert s.chiedi("GET", "/api/vista", chiave=False)[0] == 403, "W02 /api/vista senza chiave"
            assert s.chiedi("GET", "/api/vista", chiave=False, intestazioni={"X-Arturo-Token": "x" * 43})[0] == 403, \
                "W02 /api/vista con la chiave sbagliata"
            assert s.chiedi("GET", f"/api/vista?t={s.token}", chiave=False)[0] == 403, \
                "W02 la chiave nel link vale anche per le API"
            v = s.vista()
            assert "gruppi" in v["vista"] and "progetti" in v, f"W02 forma della vista: {sorted(v)}"
    con_casa(repo, prova)


def test_w03(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Uno", "--progetto", "p")
        prima = c.byte()
        with Server(c) as s:
            risposte = []
            for percorso in (f"/?t={s.token}", "/api/vista", "/static/app.js"):
                r = s.chiedi("GET", percorso, intestazioni={"Host": f"evil.example:{s.porta}"})
                risposte.append(r)
                assert r[0] == 403, f"W03 Host estraneo su {percorso}: {r[0]}"
            r = s.chiedi("GET", "/api/vista", intestazioni={"Host": f"localhost:{s.porta}"})
            risposte.append(r)
            assert r[0] == 200, f"W03 Host localhost: {r[0]}"
            azione = {"azione": "fatto", "id": 1}
            r = s.chiedi("POST", "/api/azione", azione, intestazioni={"Origin": "https://evil.example"})
            risposte.append(r)
            assert r[0] == 403, f"W03 Origin estraneo: {r[0]}"
            r = s.chiedi("POST", "/api/azione", grezzo=json.dumps(azione).encode(), intestazioni={"Content-Type": "text/plain"})
            risposte.append(r)
            assert r[0] == 415, f"W03 Content-Type text/plain: {r[0]}"
            r = s.chiedi("OPTIONS", "/api/azione", intestazioni={"Origin": "https://evil.example",
                                                                  "Access-Control-Request-Method": "POST"})
            risposte.append(r)
            assert r[0] == 405, f"W03 OPTIONS: {r[0]}"
            risposte.append(s.chiedi("GET", f"/?t={s.token}", chiave=False))
            risposte.append(s.chiedi("GET", "/static/stile.css", chiave=False))
            for codice, h, _ in risposte:
                cors = [k for k in h if k.startswith("access-control-allow")]
                assert not cors, f"W03 una risposta {codice} apre CORS: {cors}"
        assert c.byte() == prima, "W03 un rifiuto ha cambiato il registro"
    con_casa(repo, prova)


def test_w04(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Chiuso", "--progetto", "a")
        c.todo("fatto", "1")
        c.todo("aggiungi", "Fermo", "--progetto", "a")
        c.todo("ferma", "2", "aspetto Rossi")
        c.todo("aggiungi", "Scaduto", "--progetto", "b", "--scadenza", "2026-10-01")
        cli_vista = c.json("--tutti")
        cli_progetti = c.json("progetti")["progetti"]
        with Server(c) as s:
            codice, _, corpo = s.chiedi("GET", "/api/vista")
            web = json.loads(corpo)
        assert web["vista"] == cli_vista, f"W04 vista diversa dalla CLI:\n{web['vista']}\n{cli_vista}"
        assert web["progetti"] == cli_progetti, f"W04 progetti diversi: {web['progetti']} {cli_progetti}"
        assert "uid" not in corpo.decode("utf-8"), "W04 la risposta porta gli uid"
    con_casa(repo, prova)


def test_w05(repo: Path) -> None:
    titolo = "Perché è già lì: città"

    def prova(c: Casa) -> None:
        with Server(c) as s:
            r = s.azione(azione="aggiungi", campi={"titolo": titolo, "scadenza": "venerdì", "chi": "decidi", "progetto": "p"})
            assert r["annulla"] and r["messaggio"].startswith("Aggiunto #1"), f"W05 risposta: {r}"
        decidi = next(g for g in c.json()["gruppi"] if g["tipo"] == "decidi")["todo"]
        assert [(t["titolo"], t["scadenza"], t["progetto"]) for t in decidi] == [(titolo, "2026-10-09", "p")], \
            f"W05 la CLI non trova il todo come scritto dalla pagina: {decidi}"
        grezzo = c.byte()
        assert titolo.encode("utf-8") in grezzo and b"\\u00" not in grezzo, "W05 il registro non è in UTF-8 diretto"
    con_casa(repo, prova)

    # Un titolo incollato da un PDF può contenere U+0085, U+2028 e U+2029: il registro resta una
    # riga per evento, e un registro vecchio che li ha crudi si legge lo stesso.
    incollato = "Rileggere\u2028il capitolo\u2029tre\x85fine"

    def separatori(c: Casa) -> None:
        with Server(c) as s:
            r = s.azione(azione="aggiungi", campi={"titolo": incollato, "progetto": "p"})
            assert r["vista"]["avvisi"] == [], f"W05 avvisi dopo un titolo incollato: {r['vista']['avvisi']}"
        v = c.json()
        assert [t["titolo"] for g in v["gruppi"] for t in g["todo"]] == [incollato] and v["avvisi"] == [], \
            f"W05 il titolo incollato non torna uguale: {v}"
        testo = c.byte().decode("utf-8")
        assert not any(x in testo for x in "\u0085\u2028\u2029"), "W05 il registro scrive crudi i separatori Unicode"
        evento = json.loads(testo.split("\n")[0])
        evento["dati"]["titolo"] = "Vecchio\u2028registro"
        evento["ev"] = "0" * 32
        evento["todo"] = "1" * 32
        evento["id"] = 2
        with open(c.registro, "ab") as f:
            f.write((json.dumps(evento, ensure_ascii=False) + "\n").encode("utf-8"))
        v = c.json()
        titoli = sorted(t["titolo"] for g in v["gruppi"] for t in g["todo"])
        assert titoli == sorted([incollato, "Vecchio\u2028registro"]) and v["avvisi"] == [], \
            f"W05 un registro con i separatori crudi non si legge: {titoli} {v['avvisi']}"
    con_casa(repo, separatori)


def _passi_cli(c: Casa) -> None:
    for argomenti in (("aggiungi", "Uno", "--progetto", "p"), ("modifica", "1", "--chi", "io", "--scadenza", "venerdì"),
                      ("nota", "1", "prima nota"), ("ferma", "1", "aspetto Rossi"), ("riprendi", "1"), ("fatto", "1"),
                      ("aggiungi", "Due", "--progetto", "p"), ("scarta", "2", "non serve più"),
                      ("aggiungi", "Tre", "--progetto", "p", "--chi", "decidi"), ("deciso", "3", "piano B")):
        c.todo(*argomenti)


def _passi_web(s: Server) -> None:
    s.azione(azione="aggiungi", campi={"titolo": "Uno", "progetto": "p"})
    s.azione(azione="modifica", id=1, campi={"chi": "io", "scadenza": "venerdì"})
    s.azione(azione="nota", id=1, testo="prima nota")
    s.azione(azione="ferma", id=1, motivo="aspetto Rossi")
    s.azione(azione="riprendi", id="1")
    s.azione(azione="fatto", id=1, titolo_atteso="Uno")
    s.azione(azione="aggiungi", campi={"titolo": "Due", "progetto": "p"})
    s.azione(azione="scarta", id=2, motivo="non serve più")
    s.azione(azione="aggiungi", campi={"titolo": "Tre", "progetto": "p", "chi": "decidi"})
    s.azione(azione="deciso", id=3, testo="piano B")


def _senza_ts(todo: dict) -> dict:
    return dict(todo, storia=[{k: v for k, v in e.items() if k != "ts"} for e in todo["storia"]])


def _coppie(registro: Path) -> list:
    return [(e["tipo"], e["dati"], e.get("id")) for e in map(json.loads, read(registro).splitlines())]


def test_w06(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Casa(repo, Path(tmp), "a"), Casa(repo, Path(tmp), "b")
        _passi_cli(a)
        with Server(b) as s:
            _passi_web(s)
        for n in ("1", "2", "3"):
            ma, mb = _senza_ts(a.json("mostra", n)), _senza_ts(b.json("mostra", n))
            assert ma == mb, f"W06 #{n} diverso tra CLI e pagina:\n{ma}\n{mb}"
        assert _coppie(a.registro) == _coppie(b.registro), \
            f"W06 eventi diversi:\n{_coppie(a.registro)}\n{_coppie(b.registro)}"
        tre = b.json("mostra", "3")
        assert tre["chi"] == "io" and tre["note"] == ["Deciso: piano B"], f"W06 deciso: {tre}"
        assert b.json("mostra", "1")["scadenza"] == "2026-10-09", "W06 la scadenza «venerdì» non è una data"


def test_w07(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Uno", "--progetto", "p")
        c.todo("aggiungi", "Due", "--progetto", "p", "--chi", "decidi")
        prima = c.byte()
        with Server(c) as s:
            casi = (
                ({"azione": "aggiungi", "campi": {"titolo": "X", "chi": "boh"}}, "tu, decidi, io"),
                ({"azione": "aggiungi", "campi": {"titolo": "X", "priorita": "urgente"}}, "alta, media, bassa"),
                ({"azione": "cancella", "id": 1}, "cancella"),
                ({"azione": "fatto", "id": 99}, "non esiste"),
                ({"azione": "modifica", "id": 1, "campi": {"uid": "x"}}, "campo sconosciuto"),
                ({"azione": "modifica", "id": 1, "campi": {"titolo": ["a", "b"]}}, "deve essere testo"),
                ({"azione": "deciso", "id": 2, "testo": "   "}, "scrivi cosa hai deciso"),
            )
            for corpo, atteso in casi:
                codice, _, risposta = s.chiedi("POST", "/api/azione", corpo)
                errore = json.loads(risposta).get("errore", "")
                assert codice == 400 and atteso in errore, f"W07 {corpo}: {codice} {errore!r}"
            codice, _, risposta = s.chiedi("POST", "/api/azione", grezzo=b"{non json")
            assert codice == 400, f"W07 corpo non JSON: {codice}"
            italiano(risposta, "W07 corpo non JSON")
            codice, _, risposta = s.chiedi("POST", "/api/azione", grezzo=b'{"azione":"' + b"x" * 20480 + b'"}')
            assert codice == 413, f"W07 corpo di 20 KB: {codice}"
            for cosa, risposta in (("403", s.chiedi("GET", "/api/vista", chiave=False)),
                                   ("404", s.chiedi("GET", "/niente")),
                                   ("405", s.chiedi("DELETE", "/api/vista")),
                                   ("413", (413, {}, risposta)),
                                   ("415", s.chiedi("POST", "/api/azione", grezzo=b"{}", intestazioni={"Content-Type": "text/plain"}))):
                assert str(risposta[0]) == cosa, f"W07 atteso {cosa}, arriva {risposta[0]}"
                italiano(risposta[2], f"W07 corpo del {cosa}")
            for _ in range(20):
                s.vista()
            s.chiedi("POST", "/api/azione", {"azione": "nota", "id": 1, "testo": ""})
            time.sleep(0.3)
            terminale = "".join(s.errori)
        assert c.byte() == prima, "W07 un errore ha scritto nel registro"
        assert "GET /" not in terminale and "POST /" not in terminale, f"W07 il server scrive il log: {terminale[:300]!r}"
    con_casa(repo, prova)


def test_w08(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Comprare il pane", "--progetto", "p")
        prima = c.byte()
        with Server(c) as s:
            codice, _, corpo = s.chiedi("POST", "/api/azione", {"azione": "fatto", "id": 1, "titolo_atteso": "Altro titolo"})
            assert codice == 409, f"W08 un titolo diverso da quello del todo #1 dà {codice}, non 409"
            r = json.loads(corpo)
            assert "vista" in r and "progetti" in r and "#1" in r["errore"], f"W08 risposta 409: {r}"
            assert c.byte() == prima, "W08 un 409 ha scritto nel registro"
            s.azione(azione="fatto", id=1, titolo_atteso="Comprare il pane")
        assert c.json("mostra", "1")["stato"] == "fatto", "W08 con il titolo giusto il todo non si chiude"
    con_casa(repo, prova)


def test_w09(repo: Path) -> None:
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Uno", "--progetto", "p", "--scadenza", "2026-10-10")
        c.todo("ferma", "1", "aspetto Rossi")
        with Server(c) as s:
            r = s.azione(azione="fatto", id=1, titolo_atteso="Uno")
            annulla = r["annulla"]
            assert annulla and annulla["azione"] == "ripristina", f"W09 annulla di fatto: {annulla}"
            r = s.azione(**annulla)
            assert r["messaggio"] == "Fermato #1: Uno", f"W09 esito dell'Annulla di fatto: {r['messaggio']!r}"
            uno = c.json("mostra", "1")
            assert (uno["stato"], uno["motivo"]) == ("fermo", "aspetto Rossi"), f"W09 dopo Annulla: {uno['stato']} {uno['motivo']}"
            assert uno["storia"][-1]["dati"].get("annullo") is True, "W09 l'annullo non porta il segno"

            r = s.azione(azione="modifica", id=1, titolo_atteso="Uno", campi={"scadenza": ""})
            assert c.json("mostra", "1")["scadenza"] is None, "W09 la scadenza non si toglie"
            s.azione(**r["annulla"])
            uno = c.json("mostra", "1")
            assert uno["scadenza"] == "2026-10-10", "W09 Annulla non rimette la scadenza"
            assert uno["storia"][-1]["dati"].get("annullo") is True, "W09 l'Annulla di una modifica non porta il segno"

            righe = len(c.byte().splitlines())
            r = s.azione(azione="aggiungi", campi={"titolo": "Sbagliato", "progetto": "p"})
            tolto = s.azione(**r["annulla"])
            due = c.json("mostra", str(r["id"]))
            assert due["stato"] == "scartato", f"W09 l'aggiungi annullato è {due['stato']}"
            assert tolto["messaggio"] == f"Tolto #{r['id']}: Sbagliato", f"W09 esito dell'Annulla di aggiungi: {tolto['messaggio']!r}"
            assert len(c.byte().splitlines()) == righe + 2, "W09 Annulla cancella o salta righe del registro"
            nota = s.azione(azione="nota", id=1, titolo_atteso="Uno", testo="una nota")
            assert nota["annulla"] is None, f"W09 una nota offre Annulla, ma le note non si annullano: {nota['annulla']}"

            r = s.azione(azione="aggiungi", campi={"titolo": "Scegliere la sala", "progetto": "p", "chi": "decidi"})
            n = str(r["id"])
            r = s.azione(azione="deciso", id=r["id"], titolo_atteso="Scegliere la sala", testo="la sala grande")
            assert r["messaggio"] == f"Deciso #{n}: Scegliere la sala", f"W09 esito di «Ho deciso»: {r['messaggio']!r}"
            assert c.json("mostra", n)["chi"] == "io", "W09 deciso non passa il todo a Claude"
            s.azione(**r["annulla"])
            sala = c.json("mostra", n)
            assert sala["chi"] == "decidi", f"W09 Annulla di «Ho deciso» non rimette chi=decidi: {sala['chi']}"
            assert sala["storia"][-1]["dati"].get("annullo") is True, "W09 l'Annulla di «Ho deciso» non porta il segno"
    con_casa(repo, prova)


def test_w10(repo: Path) -> None:
    ostile = "<img src=x onerror=alert(1)>"

    def prova(c: Casa) -> None:
        c.todo("aggiungi", ostile, "--progetto", "p")
        with Server(c) as s:
            codice, h, corpo = s.chiedi("GET", "/api/vista")
        assert h["content-type"].startswith("application/json") and h.get("x-content-type-options") == "nosniff", \
            f"W10 intestazioni: {h}"
        titoli = [t["titolo"] for g in json.loads(corpo)["vista"]["gruppi"] for t in g["todo"]]
        assert titoli == [ostile], f"W10 il titolo cambia: {titoli}"
    con_casa(repo, prova)

    web = repo / "bin" / "web"
    app = read(web / "app.js")
    for vietato in VIETATI_JS:
        assert vietato not in app, f"W10 app.js usa {vietato}"
    for nome in ("index.html", "stile.css", "app.js"):
        testo = read(web / nome)
        for vietato in ("http://", "https://", "//cdn", "@import", "xmlns"):
            assert vietato not in testo, f"W10 {nome} contiene {vietato}"
    collegamenti = re.findall(r'\b(?:src|href)="([^"]*)"', read(web / "index.html"))
    fuori = [x for x in collegamenti if x not in ("static/stile.css", "static/app.js")
             and not x.startswith("data:") and not x.startswith("#")]
    assert not fuori and collegamenti, f"W10 index.html collega altro: {fuori}"
    # Percorsi relativi: la pagina funziona anche sotto un prefisso, dietro un proxy.
    assert not re.search(r'chiama\("(GET|POST)", "/', app), "W10 app.js chiama le API con un percorso assoluto"


def test_w11(repo: Path) -> None:
    attesi = {"stile.css": "text/css", "app.js": "text/javascript", "font/sorts-mill-goudy.woff2": "font/woff2",
              "font/atkinson-next.woff2": "font/woff2", "font/atkinson-mono.woff2": "font/woff2"}

    def prova(c: Casa) -> None:
        with Server(c) as s:
            for nome, tipo in attesi.items():
                codice, h, corpo = s.chiedi("GET", f"/static/{nome}", chiave=False)
                assert codice == 200 and h["content-type"].startswith(tipo), f"W11 {nome}: {codice} {h.get('content-type')}"
                assert corpo == (repo / "bin" / "web" / nome).read_bytes(), f"W11 {nome}: byte diversi dal file"
            for percorso in ("/static/../todo_store.py", "/static/%2e%2e/arturo", "/static/font/../../todo_store.py",
                             "/static/nuovo.css", "/../../.claude/data/todo/eventi.jsonl", "/static/font/OFL.txt"):
                codice, _, corpo = s.chiedi("GET", percorso, chiave=False)
                assert codice == 404, f"W11 {percorso}: {codice}"
                assert b"todo_store" not in corpo and b"import" not in corpo, f"W11 {percorso} rivela un file"
    con_casa(repo, prova)


def test_w12(repo: Path) -> None:
    def prova(c: Casa) -> None:
        with Server(c, ARTURO_WEB_INATTIVO="2") as s:
            fine = time.time() + 4
            while time.time() < fine:
                assert s.p.poll() is None, "W12 il server si spegne mentre la pagina chiede"
                try:
                    s.vista()
                except OSError:
                    assert False, "W12 il server si spegne mentre la pagina chiede"
                time.sleep(0.5)
            assert s.p.poll() is None, "W12 il server si spegne mentre la pagina chiede"
            rc = s.attendi_uscita(10)
            assert rc == 0, f"W12 senza richieste non si spegne entro 10 s con rc 0: {rc}"
            time.sleep(0.2)
            assert "si è fermato" in "".join(s.uscita), f"W12 messaggio di uscita: {s.uscita}"
        with Server(c) as s:
            codice, _, _ = s.chiedi("POST", "/api/spegni", {}, chiave=False)
            assert codice == 403, f"W12 /api/spegni senza chiave: {codice}"
            time.sleep(0.5)
            assert s.p.poll() is None, "W12 una richiesta senza chiave spegne il server"
            codice, _, corpo = s.chiedi("POST", "/api/spegni", {})
            assert codice == 200, f"W12 /api/spegni: {codice} {corpo!r}"
            rc = s.attendi_uscita(5)
            assert rc == 0, f"W12 dopo «Spegni la pagina» il processo non esce entro 5 s: {rc}"
    con_casa(repo, prova)


class Pagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag = []
        self.etichette_for = set()
        self.dentro_label = 0
        self.campi = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tag.append((tag, a))
        if tag == "label":
            self.dentro_label += 1
            if a.get("for"):
                self.etichette_for.add(a["for"])
        if tag in ("input", "select", "textarea"):
            self.campi.append((tag, a, self.dentro_label > 0))

    def handle_endtag(self, tag):
        if tag == "label":
            self.dentro_label -= 1


def test_w13(repo: Path) -> None:
    web = repo / "bin" / "web"
    html = read(web / "index.html")
    p = Pagina()
    p.feed(html)
    tag = [t for t, _ in p.tag]
    assert re.search(r'<html[^>]*\blang="it"', html), "W13 lang"
    assert tag.count("h1") == 1 and tag.count("main") == 1, "W13 un h1 e un main"
    ids = {a["id"] for _, a in p.tag if a.get("id")}
    # Il tavolo dei progetti (4/10): un titolo che cambia con la vista e riceve il fuoco, le briciole
    # per tornare al tavolo, una sola regione della vista.
    titolo = [a for t, a in p.tag if t == "h1"]
    assert titolo and titolo[0].get("id") == "titolo" and titolo[0].get("tabindex") == "-1", f"W13 h1 della vista: {titolo}"
    assert any(t == "nav" and a.get("aria-label") and a.get("id") == "briciole" for t, a in p.tag), "W13 nav delle briciole"
    vista = [a for _, a in p.tag if a.get("id") == "vista"]
    assert vista and "pannello" in vista[0].get("class", "") and vista[0].get("aria-labelledby") == "titolo", f"W13 regione della vista: {vista}"
    assert "role=\"tab\"" not in html, "W13 restano schede della pagina di prima"
    assert any(a.get("role") == "status" and a.get("aria-live") == "polite" for _, a in p.tag), "W13 regione status"
    assert any(a.get("role") == "alert" for _, a in p.tag), "W13 regione alert"
    for t, a, dentro in p.campi:
        if a.get("type") == "hidden":
            continue
        assert dentro or a.get("id") in p.etichette_for, f"W13 {t} senza etichetta: {a}"

    css = read(web / "stile.css")
    for cosa in (":focus-visible", "prefers-reduced-motion", "prefers-color-scheme: dark"):
        assert cosa in css, f"W13 stile.css senza {cosa}"
    for misura in re.findall(r"font-size\s*:\s*([^;}]+)", css):
        m = re.fullmatch(r"\s*([\d.]+)(px|rem)\s*", misura)
        if m:
            px = float(m.group(1)) * (16 if m.group(2) == "rem" else 1)
            assert px >= 12, f"W13 font-size sotto 12 px: {misura}"
    for nome, valore in re.findall(r"(--t-[\w-]+)\s*:\s*([\d.]+rem)", css):
        assert float(valore[:-3]) >= 0.75, f"W13 {nome} sotto 0.75rem"

    # La Regola della Stella: l'arancio solo nel marchio e nelle regole .stella / .marchio.
    stella = "#f2a24a"
    assert stella not in read(web / "app.js").lower(), "W13 app.js usa l'arancio della stella"
    righe_html = [r for r in html.lower().splitlines() if stella in r]
    assert righe_html and all("<circle" in r for r in righe_html), f"W13 l'arancio in index.html fuori dal marchio: {righe_html}"
    senza_commenti = re.sub(r"/\*.*?\*/", "", css, flags=re.S).lower()
    trovate = 0
    for selettore, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", senza_commenti):
        if stella in corpo:
            trovate += 1
            assert "stella" in selettore or "marchio" in selettore, f"W13 l'arancio nella regola {selettore.strip()!r}"
    assert trovate, "W13 la stella non ha la sua regola in stile.css"

    # Una parola per concetto: i nomi di «chi» (gruppi, chip, select, radio) sono i titoli dei
    # gruppi dello store in tondo. La pagina non ha un secondo elenco di nomi.
    r = subprocess.run([sys.executable, "-c", "import json, sys; sys.path.insert(0, sys.argv[1]); import todo_store as t; "
                        "print(json.dumps([[g[0], g[1]] for g in t.GRUPPI]))", str(repo / "bin")],
                       capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, f"W13 GRUPPI dello store: {r.stderr[-300:]}"
    nomi = {tipo: titolo[0] + titolo[1:].lower() for tipo, titolo in json.loads(r.stdout)}
    radio = dict(re.findall(r'<span data-chi="(\w+)">([^<]*)</span>', html))
    assert radio == {k: nomi[k] for k in ("tu", "decidi", "io")}, f"W13 i radio di «Chi agisce» non usano i nomi dei gruppi: {radio} {nomi}"
    app = read(web / "app.js")
    for altro in ("poi Claude", "Lo fa Claude", "NOMI_CHI"):
        assert altro not in app, f"W13 app.js ha un secondo nome per «chi»: {altro!r}"
    assert app.count("nomiChi()") >= 3, "W13 chip e select non prendono i nomi dei gruppi"
    # Gli avvisi dell'archivio non sono solo righe illeggibili: anche una rinumerazione è un avviso.
    assert "non si legg" not in app, "W13 il riquadro degli avvisi dice «non si legge» per ogni avviso"

    # Il pannello aperto tiene i campi non salvati: ogni campo ricorda il valore disegnato, e il
    # ridisegno li legge prima e li rimette dopo. La prova vera è nel browser, qui sotto.
    def corpo(nome: str) -> str:
        m = re.search(r"\n  function " + nome + r"\(.*?\n  }\n", app, re.S)
        assert m, f"W13 app.js senza la funzione {nome}"
        return m.group(0)
    applica = corpo("applica")
    posti = [applica.find(x) for x in ("ricordaCampi()", "disegna()", "rimettiCampi(")]
    assert -1 not in posti and posti == sorted(posti), f"W13 applica non tiene i campi intorno a disegna(): {posti}"
    for nome in ("campoTesto", "scelta"):
        assert '"data-iniziale"' in corpo(nome), f"W13 {nome} non segna data-iniziale"
    assert re.search(r'el\("textarea", \{[^}]*"data-iniziale"', app), "W13 la nota non segna data-iniziale"
    assert "stato.aperto = null" in corpo("disegna"), "W13 disegna non chiude il pannello di un todo sparito"

    # La prova nel browser, se Chrome e node 22 ci sono: senza, resta il controllo sul sorgente, che
    # non vede un rimettiCampi svuotato. Nel gate (ARTURO_PROVA_BROWSER=obbligatoria) il salto è
    # un fallimento: il gate non resta verde senza la prova vera.
    prova_nel_browser(repo)


def salta_browser(motivo: str) -> None:
    obbligatoria = os.environ.get("ARTURO_PROVA_BROWSER") == "obbligatoria"
    assert not obbligatoria, f"W13 la prova nel browser è obbligatoria (ARTURO_PROVA_BROWSER) e non parte: {motivo}"
    print(f"W13 nota: salto la prova nel browser: {motivo}")


def versione_node(node: str) -> int:
    r = subprocess.run([node, "-e", "process.stdout.write(process.versions.node)"], capture_output=True,
                       encoding="utf-8", timeout=30)
    try:
        return int(r.stdout.split(".")[0]) if r.returncode == 0 else 0
    except ValueError:
        return 0


def prova_nel_browser(repo: Path) -> None:
    node, chrome = shutil.which("node"), cerca_chrome()
    if not node or not chrome:
        salta_browser("Chrome o node assenti")
        return
    if versione_node(node) < 22:
        salta_browser(f"node {versione_node(node)} senza WebSocket: serve node 22 o successivo")
        return
    for tentativo in (1, 2):  # Chrome a volte non apre la porta di debug al primo avvio
        r = subprocess.run([node, str(repo / "tests" / "prova_pagina.js"), str(repo), sys.executable, chrome],
                           capture_output=True, encoding="utf-8", timeout=180)
        if r.returncode != 77:
            break
    if r.returncode == 77:
        salta_browser(r.stdout.strip())
        return
    assert r.returncode == 0 and "PROVA_PAGINA_OK" in r.stdout, \
        f"W13 la prova nel browser: rc={r.returncode} {r.stdout.strip()[-800:]} {r.stderr.strip()[-300:]}"


def cerca_chrome():
    """Chrome o Chromium per la prova nel browser. ARTURO_CHROME sceglie un percorso. None se non c'è."""
    candidati = [os.environ.get("ARTURO_CHROME", ""),
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    candidati += [shutil.which(n) or "" for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")]
    for cartella in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")):
        if cartella:
            candidati.append(os.path.join(cartella, "Google", "Chrome", "Application", "chrome.exe"))
    return next((c for c in candidati if c and os.path.isfile(c)), None)


def test_w14(repo: Path) -> None:
    def prova(c: Casa) -> None:
        with Server(c) as s:
            def web(i: int) -> int:
                return s.chiedi("POST", "/api/azione", {"azione": "aggiungi", "campi": {"titolo": f"Web {i}", "progetto": "p"}})[0]

            def cli(i: int) -> int:
                return c.cli("todo", "aggiungi", f"Cli {i}", "--progetto", "p", ok=False).returncode
            with ThreadPoolExecutor(16) as pool:
                esiti = list(pool.map(lambda k: web(k[1]) if k[0] == "w" else cli(k[1]),
                                      [(x, i) for i in range(8) for x in ("w", "c")]))
            assert esiti.count(200) == 8 and esiti.count(0) == 8, f"W14 esiti: {esiti}"
        v = c.json()
        numeri = sorted(t["id"] for g in v["gruppi"] for t in g["todo"])
        assert numeri == list(range(1, 17)) and v["avvisi"] == [], f"W14 id {numeri} avvisi {v['avvisi']}"
        for riga in read(c.registro).splitlines():
            json.loads(riga)
    con_casa(repo, prova)


def test_w15(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        c = Casa(repo, Path(tmp))
        assert "arturo web" in c.cli().stdout, "W15 l'aiuto di arturo non cita arturo web"
        assert "deciso" in c.todo("aiuto").stdout, "W15 l'aiuto dei todo non cita deciso"
    skill = read(repo / "skills" / "todo" / "SKILL.md")
    assert "arturo web" in skill and "deciso" in skill and "run_in_background" in skill, "W15 la skill todo"
    readme = read(repo / "README.md")
    # L'albero descrive bin/ una volta, come cartella (T11): la pagina sta nel testo, accanto alla CLI.
    assert "`arturo web`" in readme and "arturo todo aiuto`. Se chiedi di vederli in una pagina" in readme, \
        "W15 il README non racconta la pagina accanto alla CLI dei todo"
    assert "Nessun server, nessun account, nessun dominio richiesto" in readme, "W15 la frase pubblica è cambiata"
    paragrafo = next((p for p in readme.split("\n\n") if "arturo web" in p and "facoltativa" in p), "")
    assert "127.0.0.1" in paragrafo or "tuo computer" in paragrafo, "W15 il README non dice che la pagina è locale"
    assert "si spegne da sola" in paragrafo, "W15 il README non dice che la pagina si spegne da sola"
    novita = read(repo / "NOVITA.md")
    intestazioni = [r for r in novita.splitlines() if r.startswith("## ")]
    titolo = "## 2026-10-03 — La pagina delle cose da fare"
    assert titolo in intestazioni, f"W15 NOVITA non ha la entry della pagina: {intestazioni[:3]}"
    assert len(intestazioni) == len(set(intestazioni)), "W15 intestazioni doppie in NOVITA"
    prima = novita.split(titolo, 1)[1].split("\n## ", 1)[0]
    assert "`arturo web`" in prima, "W15 la entry non cita `arturo web`"
    assert "salvo dopo una nota" in prima, "W15 la entry promette «Annulla» anche dopo una nota"
    assert prima.rstrip().endswith("<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->"), \
        "W15 la entry non chiude con la nota dell'autore"
    r = subprocess.run([sys.executable, "-B", str(repo / "tests" / "test_allineamento.py"), "--repo", str(repo)],
                       capture_output=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, f"W15 test_allineamento con i file nuovi: {r.stdout[-300:]} {r.stderr[-300:]}"


def test_w16(repo: Path) -> None:
    """Il tavolo dei progetti: da_dove e percorso nella vista, /api/todo con la sua chiave."""
    def prova(c: Casa) -> None:
        c.todo("aggiungi", "Mandare il preventivo", "--chi", "tu", "--progetto", "libro", "--scadenza", "2026-10-04")
        c.todo("aggiungi", "<img src=x onerror=alert(1)>", "--chi", "io", "--progetto", "libro")
        c.todo("dopo", "2", "1")
        c.todo("nota", "1", "Rossi vuole il PDF")
        with Server(c) as s:
            v = s.vista()
            assert v["da_dove"] == {"id": 1, "motivo": "Sblocca #2"}, f"W16 da_dove nella vista: {v.get('da_dove')}"
            assert v["percorso"] and v["percorso"]["totale"] == 4, f"W16 percorso nella vista: {v.get('percorso')}"
            codice, _, corpo = s.chiedi("GET", "/api/todo?id=1", chiave=False)
            assert codice == 403, f"W16 /api/todo senza chiave: {codice}"
            italiano(corpo, "W16 /api/todo senza chiave")
            codice, _, corpo = s.chiedi("GET", "/api/todo?id=1", intestazioni={"Origin": "http://altro.example"})
            assert codice == 403, f"W16 /api/todo da un altro sito: {codice}"
            codice, _, corpo = s.chiedi("GET", "/api/todo")
            assert codice == 400, f"W16 /api/todo senza numero: {codice}"
            italiano(corpo, "W16 /api/todo senza numero")
            codice, _, corpo = s.chiedi("GET", "/api/todo?id=99")
            assert codice == 400 and "99" in corpo.decode("utf-8"), f"W16 /api/todo numero assente: {codice} {corpo!r}"
            codice, h, corpo = s.chiedi("GET", "/api/todo?id=1")
            assert codice == 200 and h["content-type"].startswith("application/json"), f"W16 /api/todo: {codice}"
            t = json.loads(corpo)["todo"]
            assert t["sblocca"] == [2] and [n["testo"] for n in t["note_datate"]] == ["Rossi vuole il PDF"], f"W16 scheda: {t}"
            assert {e["tipo"] for e in t["storia"]} >= {"crea", "nota"}, f"W16 storia: {t['storia']}"
            due = json.loads(s.chiedi("GET", "/api/todo?id=2")[2])["todo"]
            dopo = [e for e in due["storia"] if e["tipo"] == "dopo"]
            assert dopo and dopo[0]["dati"]["aggiungi"] == 1, f"W16 la storia mostra un uid invece del numero: {dopo}"
            assert due["titolo"] == "<img src=x onerror=alert(1)>", "W16 il titolo ostile non resta testo nel JSON"
    con_casa(repo, prova)


TESTS = {
    "W01": test_w01, "W02": test_w02, "W03": test_w03, "W04": test_w04, "W05": test_w05,
    "W06": test_w06, "W07": test_w07, "W08": test_w08, "W09": test_w09, "W10": test_w10,
    "W11": test_w11, "W12": test_w12, "W13": test_w13, "W14": test_w14, "W15": test_w15, "W16": test_w16,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", help="esegue solo questi controlli, separati da virgola")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, IndexError, KeyError, StopIteration, json.JSONDecodeError,
                    subprocess.SubprocessError, http.client.HTTPException):
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
