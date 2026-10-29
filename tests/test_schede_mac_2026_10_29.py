#!/usr/bin/env python3
"""SM01-SM09: arturo schede, il profilo del Terminale di macOS senza processo nel titolo (29/10/2026).

SM01 fuori dal Terminale di Apple, o fuori da macOS, non tocca niente e non lascia il segno.
SM02 un profilo predefinito già pulito lascia solo il segno: nessun profilo nuovo.
SM03 applica crea "Arturo": copia del predefinito (colori, font) con le sette chiavi spente, ne fa il
     predefinito e il profilo d'avvio, e il segno ricorda quello di prima.
SM04 si chiude solo la finestra vuota dell'import, anche quando arriva dopo il profilo o resta occupata
     dal login per un attimo (come nel Terminale vero): mai una finestra di prima, mai una al lavoro,
     mai una aperta dalla persona negli stessi secondi.
SM05 il profilo nuovo va solo sulle schede che usavano il predefinito: le altre tengono il loro.
SM06 un errore di AppleScript non lascia il segno "fatto", conta il tentativo e non ferma l'avvio
     (exit 0); dopo tre tentativi l'avvio non riprova.
SM07 col segno "fatto" --una-volta non chiama niente.
SM08 ripristina rimette il profilo di prima su schede e predefinito, cancella "Arturo", e l'avvio dopo
     non lo rimette.
SM09 session-start.sh lo lancia nel Terminale di Apple e ne riporta la riga SCHEDE:; col segno non
     avvia Python.
SM10 un profilo "Arturo" che la persona aveva già non si tocca: né predefinito né cancellato.
SM11 un processo ucciso a metà (il timeout dell'avvio) ha già contato il tentativo.
SM12 su macOS gli AppleScript veri compilano (osacompile): i finti li riconoscono solo per sottostringa.

osascript, open e defaults sono finti: simulano Terminale in un file JSON, niente tocca il Mac vero.
Sulla base 3b1e66f ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHIAVI = ("ShowActiveProcessInTabTitle", "ShowActiveProcessArgumentsInTabTitle", "ShowComponentsWhenTabHasCustomTitle",
          "ShowRepresentedURLInTabTitle", "ShowRepresentedURLPathInTabTitle", "ShowTTYNameInTabTitle",
          "ShowActivityIndicatorInTab")

# Terminale finto. Lo stato: finestre {id: [[profilo, occupata], ...]}, profili, predefinito, avvio,
# prefs (quello che defaults export rende), rompi (osascript esce 1), apertura_occupata.
FINTO = r'''#!/usr/bin/env python3
import json, os, plistlib, sys, time
from pathlib import Path
STATO = Path(os.environ["SM_STATO"])
s = json.loads(STATO.read_text())
nome = Path(sys.argv[0]).name
with open(os.environ["SM_LOG"], "a") as log:
    log.write(nome + " " + " ".join(sys.argv[1:])[:200].replace("\n", " ") + "\n")
def salva():
    STATO.write_text(json.dumps(s))
if nome == "defaults":
    time.sleep(s.get("lento") or 0)
    prefs = dict(s["prefs"], **{"Default Window Settings": s["predefinito"], "Startup Window Settings": s["avvio"]})
    prefs["Window Settings"] = {k: {kk: (vv.encode() if kk.endswith("Color") else vv) for kk, vv in v.items()}
                                for k, v in prefs.get("Window Settings", {}).items()}
    sys.stdout.write(plistlib.dumps(prefs).decode())
    sys.exit(0)
if nome == "open":
    file = Path(sys.argv[-1])
    p = plistlib.loads(file.read_bytes())
    s["importato"] = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in p.items()}
    if p["name"] not in s["profili"]:
        s["profili"].append(p["name"])
    nuovo = str(max([int(w) for w in s["finestre"]] + [0]) + 1)
    s["nuova"] = nuovo
    finestra = [[p["name"], bool(s.get("apertura_occupata"))]]
    if s.get("finestra_in_ritardo"):  # come Terminale vero: il profilo c'è subito, la finestra dopo
        s["in_arrivo"] = [nuovo, finestra, s["finestra_in_ritardo"]]
    else:
        s["finestre"][nuovo] = finestra
    if s.get("finestra_utente"):  # Cmd+N della persona negli stessi secondi: profilo di prima, libera
        s["finestre"][str(int(nuovo) + 1)] = [[s["predefinito"], False]]
    salva()
    sys.exit(0)
# osascript: gli -e sono lo script, il resto argv
righe, argv, i = [], [], 1
while i < len(sys.argv):
    if sys.argv[i] == "-e":
        righe.append(sys.argv[i + 1]); i += 2
    else:
        argv.append(sys.argv[i]); i += 1
testo = "\n".join(righe)
if s.get("rompi"):
    sys.stderr.write("execution error: finto (-1728)\n"); sys.exit(1)
if "id of every window" in testo:
    if s.get("in_arrivo"):
        wid, finestra, attese = s["in_arrivo"]
        if attese <= 0:
            s["finestre"][wid] = finestra
            s.pop("in_arrivo")
        else:
            s["in_arrivo"][2] = attese - 1
        salva()
    print(", ".join(s["finestre"]))
elif "exists settings set" in testo:
    print("true" if argv[0] in s["profili"] else "false")
elif "busy of every tab" in testo:
    schede = s["finestre"][argv[0]]
    if s.get("login_lento") and argv[0] == s.get("nuova"):  # il login occupa la finestra per qualche controllo
        s["login_lento"] -= 1; salva()
        print(", ".join(["true" for _ in schede] + [schede[0][0]]))
    else:
        print(", ".join(["true" if t[1] else "false" for t in schede] + [schede[0][0]]))
elif "close window id" in testo:
    s["finestre"].pop(argv[0]); salva()
elif "set default settings to nuovo" in testo:
    vecchio, nuovo = argv
    if nuovo not in s["profili"]:
        sys.stderr.write("execution error: settings set non trovato\n"); sys.exit(1)
    for schede in s["finestre"].values():
        for t in schede:
            if t[0] == vecchio:
                t[0] = nuovo
    if s["avvio"] == vecchio:
        s["avvio"] = nuovo
    s["predefinito"] = nuovo
    salva()
    print(nuovo)
elif "delete settings set" in testo:
    s["profili"].remove(argv[0]); salva()
else:
    sys.stderr.write("script non previsto: " + testo[:80] + "\n"); sys.exit(1)
'''


class Mac:
    """Una HOME e un Terminale finti; esegui() lancia arturo schede come lo lancia l'avvio."""

    def __init__(self, repo: Path, codice: str, predefinito="Basic", chiavi_spente=False, altre_schede=()):
        self.repo, self.codice = repo, codice
        modulo = repo / "bin" / "schede_mac.py"
        assert modulo.is_file(), f"{codice} manca bin/schede_mac.py"
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-schede-mac."))
        self.home = self.dir / "home"
        (self.home / ".claude").mkdir(parents=True)
        shutil.copytree(repo / "bin", self.home / ".claude" / "bin",
                        ignore=shutil.ignore_patterns("__pycache__", "web"))
        self.bin = self.dir / "finti"
        self.bin.mkdir()
        for nome in ("osascript", "open", "defaults"):
            (self.bin / nome).write_text(FINTO, encoding="utf-8")
            (self.bin / nome).chmod(0o755)
        self.log = self.dir / "chiamate.log"
        self.log.write_text("")
        profilo = {"FontAntialias": True, "BackgroundColor": "nero", "name": predefinito, "type": "Window Settings"}
        if chiavi_spente:
            profilo.update({k: False for k in CHIAVI})
        self.stato_file = self.dir / "terminale.json"
        self.scrivi_stato({
            "finestre": {"10": [[predefinito, True]], "11": [[predefinito, False]] + [[p, False] for p in altre_schede]},
            "profili": ["Basic", "Pro", predefinito] if predefinito not in ("Basic", "Pro") else ["Basic", "Pro"],
            "predefinito": predefinito, "avvio": predefinito,
            "prefs": {"Window Settings": {predefinito: profilo}},
        })
        self.env = {k: v for k, v in os.environ.items() if k not in ("TERM_PROGRAM", "ARTURO_SISTEMA")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home), PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                        SM_STATO=str(self.stato_file), SM_LOG=str(self.log), ARTURO_SISTEMA="darwin",
                        TERM_PROGRAM="Apple_Terminal", ARTURO_SCHEDE_TETTO="10", ARTURO_TELEMETRIA="0",
                        PYTHONDONTWRITEBYTECODE="1")

    def stato(self) -> dict:
        return json.loads(self.stato_file.read_text())

    def scrivi_stato(self, s: dict) -> None:
        self.stato_file.write_text(json.dumps(s))

    def segno(self) -> dict:
        f = self.home / ".claude" / "data" / "schede-terminale.json"
        return json.loads(f.read_text()) if f.exists() else {}

    def chiamate(self) -> list:
        return [r for r in self.log.read_text().splitlines() if r]

    def esegui(self, *argomenti: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.home / ".claude" / "bin" / "arturo"), "schede", *argomenti],
                              capture_output=True, text=True, env=dict(self.env, **env), timeout=60)

    def chiudi(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


def con(repo: Path, codice: str, prova, **opzioni) -> None:
    m = Mac(repo, codice, **opzioni)
    try:
        prova(m)
    finally:
        m.chiudi()


def test_sm01(repo: Path) -> None:
    def prova(m):
        r = m.esegui("applica", "--una-volta", TERM_PROGRAM="iTerm.app")
        assert r.returncode == 0 and not m.chiamate() and not m.segno(), \
            f"SM01 fuori dal Terminale di Apple tocca qualcosa: {m.chiamate()} {r.stderr[-200:]!r}"
        r = m.esegui("applica", ARTURO_SISTEMA="linux")
        assert r.returncode == 0 and not m.chiamate() and not m.segno(), "SM01 fuori da macOS tocca qualcosa"
    con(repo, "SM01", prova)


def test_sm02(repo: Path) -> None:
    def prova(m):
        r = m.esegui("applica", "--una-volta")
        s = m.stato()
        assert r.returncode == 0 and m.segno().get("fatto") is True, f"SM02 profilo già pulito senza segno: {r.stderr!r}"
        assert "Arturo" not in s["profili"] and s["predefinito"] == "Pro", "SM02 crea un profilo che non serve"
        assert not any(c.startswith("open") for c in m.chiamate()), "SM02 importa un profilo che non serve"
    con(repo, "SM02", prova, predefinito="Pro", chiavi_spente=True)


def test_sm03(repo: Path) -> None:
    def prova(m):
        r = m.esegui("applica", "--una-volta")
        s = m.stato()
        assert r.returncode == 0 and "SCHEDE:" in r.stdout, f"SM03 nessuna riga SCHEDE: {r.stdout!r} {r.stderr[-300:]!r}"
        imp = s.get("importato") or {}
        assert all(imp.get(k) is False for k in CHIAVI), f"SM03 il profilo importato non spegne le sette chiavi: {imp}"
        assert imp.get("name") == "Arturo" and imp.get("BackgroundColor") == "nero" and imp.get("FontAntialias") is True, \
            f"SM03 il profilo nuovo non è una copia del predefinito: {imp}"
        assert s["predefinito"] == "Arturo" and s["avvio"] == "Arturo", f"SM03 predefinito o avvio non cambiati: {s}"
        assert m.segno().get("fatto") is True and m.segno().get("prima") == "Basic", f"SM03 segno sbagliato: {m.segno()}"
    con(repo, "SM03", prova)


def test_sm04(repo: Path) -> None:
    def prova(m):
        m.esegui("applica")
        f = m.stato()["finestre"]
        assert set(f) == {"10", "11"}, f"SM04 la finestra dell'import resta, o ne chiude una di prima: {sorted(f)}"
    con(repo, "SM04", prova)

    def occupata(m):
        s = m.stato()
        s["apertura_occupata"] = True
        m.scrivi_stato(s)
        m.esegui("applica")
        assert "12" in m.stato()["finestre"], "SM04 chiude una finestra nuova con un processo al lavoro"
    con(repo, "SM04", occupata)

    def in_ritardo(m):
        s = m.stato()
        s["finestra_in_ritardo"] = 2
        m.scrivi_stato(s)
        m.esegui("applica")
        s = m.stato()
        f = set(s["finestre"]) | ({s["in_arrivo"][0]} if s.get("in_arrivo") else set())
        assert f == {"10", "11"}, f"SM04 la finestra dell'import che arriva dopo il profilo resta aperta: {sorted(f)}"
    con(repo, "SM04", in_ritardo)

    def login_lento(m):
        s = m.stato()
        s["login_lento"] = 3
        m.scrivi_stato(s)
        m.esegui("applica")
        f = m.stato()["finestre"]
        assert set(f) == {"10", "11"}, f"SM04 la finestra dell'import occupata dal login resta aperta: {sorted(f)}"
    con(repo, "SM04", login_lento)

    def utente(m):
        s = m.stato()
        s["finestra_utente"] = True
        m.scrivi_stato(s)
        m.esegui("applica")
        f = m.stato()["finestre"]
        assert set(f) == {"10", "11", "13"}, \
            f"SM04 chiude la finestra aperta dalla persona, o lascia quella dell'import: {sorted(f)}"
    con(repo, "SM04", utente)


def test_sm05(repo: Path) -> None:
    def prova(m):
        m.esegui("applica")
        schede = [t[0] for w in m.stato()["finestre"].values() for t in w]
        assert schede.count("Pro") == 1 and schede.count("Arturo") == 2, \
            f"SM05 il profilo va anche sulle schede con un altro profilo, o manca su quelle col predefinito: {schede}"
    con(repo, "SM05", prova, altre_schede=("Pro",))


def test_sm06(repo: Path) -> None:
    def prova(m):
        s = m.stato()
        s["rompi"] = True
        m.scrivi_stato(s)
        for giro in (1, 2, 3):
            r = m.esegui("applica", "--una-volta")
            assert r.returncode == 0, f"SM06 un errore ferma l'avvio: exit {r.returncode}"
            assert m.segno().get("fatto") is False and m.segno().get("tentativi") == giro, \
                f"SM06 al tentativo {giro} il segno è sbagliato: {m.segno()}"
        m.log.write_text("")
        m.esegui("applica", "--una-volta")
        assert not m.chiamate(), "SM06 dopo tre tentativi falliti l'avvio riprova"
    con(repo, "SM06", prova)


def test_sm07(repo: Path) -> None:
    def prova(m):
        m.esegui("applica", "--una-volta")
        m.log.write_text("")
        m.esegui("applica", "--una-volta")
        assert not m.chiamate(), f"SM07 col segno l'avvio chiama ancora Terminale: {m.chiamate()}"
    con(repo, "SM07", prova)


def test_sm08(repo: Path) -> None:
    def prova(m):
        m.esegui("applica")
        r = m.esegui("ripristina")
        s = m.stato()
        schede = {t[0] for w in s["finestre"].values() for t in w}
        assert r.returncode == 0 and s["predefinito"] == "Basic" and s["avvio"] == "Basic" and schede == {"Basic"}, \
            f"SM08 il profilo di prima non torna: {s} {r.stderr[-200:]!r}"
        assert "Arturo" not in s["profili"], "SM08 il profilo Arturo resta"
        m.log.write_text("")
        m.esegui("applica", "--una-volta")
        assert not m.chiamate(), "SM08 dopo il ripristino l'avvio rimette il profilo"
    con(repo, "SM08", prova)


def test_sm09(repo: Path) -> None:
    def prova(m):
        avvio = m.home / ".claude" / "hooks" / "session-start.sh"
        avvio.parent.mkdir(parents=True)
        shutil.copy(repo / "hooks" / "session-start.sh", avvio)
        env = dict(m.env, ARTURO_BANCHI_AVVIO="0")
        r = subprocess.run(["bash", str(avvio)], cwd=str(m.dir), capture_output=True, text=True, env=env, timeout=60,
                           stdin=subprocess.DEVNULL)
        assert "SCHEDE:" in r.stdout and m.stato()["predefinito"] == "Arturo", \
            f"SM09 l'avvio non sistema il profilo: {r.stdout[-300:]!r}"
        m.log.write_text("")
        r = subprocess.run(["bash", str(avvio)], cwd=str(m.dir), capture_output=True, text=True, env=env, timeout=60,
                           stdin=subprocess.DEVNULL)
        assert "SCHEDE:" not in r.stdout and not m.chiamate(), f"SM09 col segno l'avvio riparte: {m.chiamate()}"
    con(repo, "SM09", prova)


def test_sm10(repo: Path) -> None:
    def prova(m):
        s = m.stato()
        s["profili"].append("Arturo")
        s["prefs"]["Window Settings"]["Arturo"] = {"name": "Arturo", "BackgroundColor": "rosa"}
        m.scrivi_stato(s)
        m.esegui("applica", "--una-volta")
        s = m.stato()
        assert s["predefinito"] == "Basic" and "importato" not in s, f"SM10 usa o sovrascrive l'Arturo della persona: {s}"
        assert m.segno().get("fatto") is False, f"SM10 segna fatto senza aver cambiato niente: {m.segno()}"
        r = m.esegui("ripristina")
        assert "Arturo" in m.stato()["profili"], f"SM10 ripristina cancella l'Arturo della persona: {r.stdout!r}"
    con(repo, "SM10", prova)


def test_sm11(repo: Path) -> None:
    def prova(m):
        s = m.stato()
        s["lento"] = 30
        m.scrivi_stato(s)
        p = subprocess.Popen([sys.executable, "-B", str(m.home / ".claude" / "bin" / "arturo"), "schede", "applica",
                              "--una-volta"], env=m.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                if m.chiamate():
                    break
                time.sleep(0.1)
        finally:
            p.kill()
            p.wait()
        assert m.segno().get("tentativi") == 1 and m.segno().get("fatto") is False, \
            f"SM11 un processo ucciso a metà non ha contato il tentativo: {m.segno()}"
    con(repo, "SM11", prova)


def test_sm12(repo: Path) -> None:
    modulo = repo / "bin" / "schede_mac.py"
    assert modulo.is_file(), "SM12 manca bin/schede_mac.py"
    if sys.platform != "darwin" or not shutil.which("osacompile"):
        print("SM12 saltato: osacompile c'è solo su macOS")
        return
    spazio = {"__name__": "schede_mac_banco"}
    exec(compile(modulo.read_text(encoding="utf-8"), str(modulo), "exec"), spazio)
    with tempfile.TemporaryDirectory() as d:
        for nome, script in spazio["SCRIPT"].items():
            argv = ["osacompile", "-o", str(Path(d) / f"{nome}.scpt")]
            for riga in script:
                argv += ["-e", riga]
            r = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            assert r.returncode == 0, f"SM12 lo script {nome} non compila: {r.stderr.strip()[:200]}"


TESTS = {"SM01": test_sm01, "SM02": test_sm02, "SM03": test_sm03, "SM04": test_sm04, "SM05": test_sm05,
         "SM06": test_sm06, "SM07": test_sm07, "SM08": test_sm08, "SM09": test_sm09,
         "SM10": test_sm10, "SM11": test_sm11, "SM12": test_sm12}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if os.name == "nt":
        print("SM saltati: il profilo del Terminale c'è solo su macOS, e i finti sono script senza estensione")
        return 0
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
