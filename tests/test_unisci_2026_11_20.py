#!/usr/bin/env python3
"""arturo progetti unisci: due progetti doppioni diventano uno (bin/unisci.py, piano di Volta del 20/11/2026, #6187).

UN01 i todo del perdente, aperti e chiusi, passano al vincitore; quelli del vincitore restano; al perdente non
     resta nessun todo.
UN02 la riga di stato del perdente, più recente, passa al vincitore.
UN03 gli handoff passano nella cartella del vincitore con "- Nome:" e "- Filone:" riscritti; un nome già preso
     passa al minuto dopo; la cartella del perdente sparisce e INDEX.md punta ai file nuovi.
UN04 la scheda del vincitore prende gli alias del perdente, la sua `cartella:` e il suo corpo sotto
     "## Da <perdente>"; la scheda del perdente va in _archive/progetti/ con status closed e unito_in; il link
     [[progetto-<perdente>]] di un'altra nota diventa [[progetto-<vincitore>]].
UN05 --prova non scrive niente (l'albero della HOME di prova è identico) e --json dà i conti dell'anteprima.
UN06 due cartelle di codice con repo diversi: exit 2 e niente scritto.
UN07 la copia di sicurezza c'è, col manifesto, e contiene la scheda del perdente com'era prima.
UN08 dopo l'unione /inizio col nome del perdente apre il vincitore.
UN09 la fonte esterna che rifiuta l'unione nell'anteprima ferma tutto: exit 2, niente scritto.
UN10 la fonte esterna giù: l'unione esce 3 e non scrive; l'anteprima esce 0 e lo dice in un avviso.
UN11 la fonte esterna che unisce riceve --backup dentro la copia di sicurezza, e il suo avviso arriva all'esito.
UN12 la scheda di un terminale col progetto del perdente passa al vincitore.
UN13 la cartella degli handoff del perdente è un collegamento a quella del vincitore (herdr-arturo -> volta):
     nessun handoff si sposta né cambia nome; un collegamento verso un'altra cartella esce 2 e non scrive.
UN14 dopo l'unione la riga di stato del perdente non c'è più: arturo progetti non elenca il suo nome, e la
     riga portata al vincitore resta (#6213).
UN15 un secondo giro sullo stesso doppione esce 2 con "è già unito" e non scrive niente, anche con --prova.
UN16 ogni errore in --json porta il suo tipo (#6314): repo diversi e fonte che rifiuta = scelta, collegamento
     altrove = riparabile, fonte giù = transitorio, secondo giro = gia_unito, "non trovo niente" = scelta.
UN17 un guasto a metà (un'eccezione dopo la copia) esce 1 con un JSON: tipo riparabile, fase scrittura, la
     copia; nella copia ci sono errore.txt col traceback ed esito.json con la fase.
UN18 un'unione riuscita lascia esito.json nella copia con fatto vero e fase "fatto".
UN19 un secondo giro dopo un guasto che aveva già scritto la scheda del vincitore non ripete "## Da <perdente>".
UN20 un giro fermato durante i link lascia solo link e l'alias: il secondo giro li finisce ed esce 0, invece di
     dire "è già unito".

Veleno: --avvelena rompe bin/unisci.py nella copia di prova, un punto per caso, ed esce 0 solo se ogni
rottura fa rosso il suo caso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["UN01", "UN02", "UN03", "UN04", "UN05", "UN06", "UN07", "UN08", "UN09", "UN10", "UN11", "UN12", "UN13",
        "UN14", "UN15", "UN16", "UN17", "UN18", "UN19", "UN20"]
# caso -> (file in bin/, testo, testo rotto)
VELENI = {
    "UN01": ("unisci.py", 'ts.normalizza({"progetto": vincitore})', 'ts.normalizza({"titolo": "x"})'),
    "UN02": ("unisci.py", '        ts.scrivi_stato(vincitore, r["stato_p"]["riga"])\n', "        pass\n"),
    "UN03": ("unisci.py", "                    ora += dt.timedelta(minutes=1)\n", "                    break\n"),
    "UN04": ("unisci.py", '    unito = f"\\n## Da {perdente}', '    unito = f"\\n## {perdente}'),
    "UN05": ("unisci.py", "    if prova:\n        if come_json:", "    if False:\n        if come_json:"),
    "UN06": ("unisci.py", "and not (cod_p[1] and cod_p[1] == cod_v[1]):", "and False:"),
    "UN07": ("unisci.py", "            shutil.copy2(str(f), str(copia_f))\n", "            copia_f.write_text('')\n"),
    "UN08": ("unisci.py", "    for a in [perdente] + lista(", "    for a in lista("),
    "UN09": ("unisci.py", '    if codice == 2 and dati and dati.get("rifiuto"):', '    if False:'),
    "UN10": ("unisci.py", '    if prova:\n        avvisi.append(f"la fonte dei task è giù', '    if True:\n        avvisi.append(f"la fonte dei task è giù'),
    "UN11": ("unisci.py", '"--backup", str(backup / "fonte"),', ''),
    "UN12": ("unisci.py", 'sf.imposta_progetto(f.stem, vincitore, forza=True)', 'sf.imposta_progetto(f.stem, "x", forza=True)'),
    "UN13": ("unisci.py", "    if hd_p.is_symlink() or", "    if False and"),
    "UN14": ("unisci.py", "        ts.togli_stato(perdente)\n", "        pass\n"),
    "UN15": ("unisci.py", "        if gia and not link:\n", "        if False:\n"),
    "UN16": ("unisci.py", '"sistemala a mano, poi rilancia", "riparabile")', '"sistemala a mano, poi rilancia", "scelta")'),
    "UN17": ("unisci.py", "    except Exception as e:  # noqa: BLE001", "    except KeyboardInterrupt as e:  # noqa: BLE001"),
    "UN18": ("unisci.py", '    fase("fatto", avvisi=avvisi)\n', "    pass\n"),
    "UN19": ("unisci.py", '        unito = ""  # un giro fermato dopo la scheda', '        pass  # un giro fermato dopo la scheda'),
    "UN20": ("unisci.py", "        if not gia:\n", "        if True:\n"),
}

HANDOFF = ("# Session Handoff - {data}\n## Progetto\n- Nome: {nome} / Branch: nessuno / Status: in progress\n"
           "- Filone: {nome}/stampa\n\n## Ripartenza\n**Prossimo passo:** {passo}\n")

FONTE = r'''import json, os, sys
from pathlib import Path
a = sys.argv[1:]
log = Path(os.environ["HOME"]) / "fonte.log"
with open(log, "a", encoding="utf-8") as f:
    f.write(json.dumps(a) + "\n")
modo = (Path(os.environ["HOME"]) / "fonte.modo").read_text().strip()
if a[:1] != ["unisci"]:
    sys.exit(2)
if modo == "rifiuta":
    print(json.dumps({"rifiuto": "bucket condiviso"}))
    sys.exit(2)
if modo == "giu":
    print("Errore: lo strumento non risponde", file=sys.stderr)
    sys.exit(3)
if "--backup" in a:
    Path(a[a.index("--backup") + 1]).mkdir(parents=True, exist_ok=True)
print(json.dumps({"task": 4, "riassunto": "4 task", "avvisi": ["la commessa vecchia resta in Progetti"]}))
'''


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=ignora)
        shutil.copytree(str(repo / "hooks"), str(self.cl / "hooks"), ignore=ignora)
        self.base = self.home / "Documents" / "ClaudeCode"
        self.base.mkdir(parents=True)
        self.h = self.cl / "data" / "handoffs"
        self.mem = self.cl / "data" / "memory"

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                 ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"), ARTURO_TELEMETRIA="0",
                 PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-20", ARTURO_MEMORIA="1")
        for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR"):
            e.pop(k, None)
        return e

    def arturo(self, *a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), *a], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=self.env(), timeout=120,
                              cwd=str(self.home))

    def handoff(self, nome: str, data: str, passo: str) -> None:
        d = self.h / nome
        d.mkdir(parents=True, exist_ok=True)
        giorno, ora = data.split("_")
        (d / f"HANDOFF_{data}.md").write_text(
            HANDOFF.format(data=f"{giorno} {ora.replace('-', ':')}", nome=nome, passo=passo), encoding="utf-8")

    def prepara(self) -> None:
        for titolo in ("Chiamare la tipografia", "Mandare le bozze"):
            r = self.arturo("todo", "aggiungi", titolo, "--progetto", "fenice-vecchia")
            assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "fatto", "2")
        assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "aggiungi", "Lavoro del vincitore", "--progetto", "fenice")
        assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "stato", "bozze in stampa", "--progetto", "fenice-vecchia")
        assert r.returncode == 0, r.stderr
        self.handoff("fenice-vecchia", "2026-11-18_10-00", "io chiamo la tipografia.")
        self.handoff("fenice-vecchia", "2026-11-19_09-00", "rileggo le bozze.")
        self.handoff("fenice", "2026-11-18_10-00", "scelgo la carta.")
        (self.h / "INDEX.md").write_text(
            "| Progetto | Ultimo handoff | Data | Stato | Prossimo passo |\n|---|---|---|---|---|\n"
            "| fenice-vecchia — fenice-vecchia/stampa | [HANDOFF_2026-11-19_09-00.md](fenice-vecchia/HANDOFF_2026-11-19_09-00.md)"
            " | 2026-11-19 | in progress | rileggo le bozze. |\n"
            "| fenice — fenice/stampa | [HANDOFF_2026-11-18_10-00.md](fenice/HANDOFF_2026-11-18_10-00.md)"
            " | 2026-11-18 | in progress | scelgo la carta. |\n", encoding="utf-8")
        p = self.mem / "progetti"
        p.mkdir(parents=True)
        (p / "progetto-fenice-vecchia.md").write_text(
            "---\nname: progetto-fenice-vecchia\ndescription: la rivista, vecchia\nalias: [rivista]\n"
            "cartella: ~/Documents/ClaudeCode/fenice-codice\nstatus: active\n---\nLa tipografia è a Torino.\n",
            encoding="utf-8")
        (p / "progetto-fenice.md").write_text(
            "---\nname: progetto-fenice\ndescription: la rivista\nstatus: active\n---\nCorpo del vincitore.\n",
            encoding="utf-8")
        (p / "persona-tipografo.md").write_text(
            "---\nname: persona-tipografo\n---\nStampa [[progetto-fenice-vecchia]] e [[progetto-altro]].\n",
            encoding="utf-8")
        sc = self.cl / "cache" / "scheda"
        sc.mkdir(parents=True)
        (sc / "s1.json").write_text(json.dumps({"stato": "attende", "progetto": "fenice-vecchia"}), encoding="utf-8")
        (sc / "s2.json").write_text(json.dumps({"stato": "attende", "progetto": "altro"}), encoding="utf-8")

    def fonte(self, modo: str | None) -> None:
        f = self.cl / "arturo" / "fonte-task.local"
        if modo is None:
            if f.exists():
                f.unlink()
            return
        f.parent.mkdir(parents=True, exist_ok=True)
        (self.home / "fonte.py").write_text(FONTE, encoding="utf-8")
        (self.home / "fonte.modo").write_text(modo, encoding="utf-8")
        f.write_text(f'comando = "{sys.executable}" "{self.home / "fonte.py"}"\n', encoding="utf-8")

    def todo(self, progetto: str) -> list:
        r = self.arturo("todo", "lista", "--progetto", progetto, "--tutti", "--json")
        try:
            d = json.loads(r.stdout)
            return [t["titolo"] for g in d["gruppi"] for t in g["todo"]] + [t["titolo"] for t in d.get("chiusi_todo", [])]
        except (ValueError, KeyError, TypeError):
            return []

    def impronta(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.home.rglob("*")):
            if p.name == "fonte.log":
                continue
            st = p.lstat()
            h.update(f"{p.relative_to(self.home).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
        return h.hexdigest()


def prova(repo: Path, rompi=None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="arturo-un-") as tmp:
        lab = Lab(repo, Path(tmp))
        if rompi:
            f, vecchio, rotto = rompi
            sorgente = lab.cl / "bin" / f
            testo = sorgente.read_text(encoding="utf-8")
            assert testo.count(vecchio) == 1, f"il punto da rompere in {f} compare {testo.count(vecchio)} volte"
            sorgente.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
        lab.prepara()

        # UN06: due cartelle di codice con repo diversi
        for nome, url in (("uno", "https://example.org/uno.git"), ("due", "https://example.org/due.git")):
            d = lab.base / nome
            d.mkdir()
            subprocess.run(["git", "init", "-q", str(d)], check=True)
            subprocess.run(["git", "-C", str(d), "remote", "add", "origin", url], check=True)
            lab.arturo("todo", "aggiungi", f"Lavoro di {nome}", "--progetto", nome)
        prima = lab.impronta()
        r = lab.arturo("progetti", "unisci", "uno", "due")
        if r.returncode != 2 or lab.impronta() != prima:
            rossi.append(f"UN06 repo diversi: rc={r.returncode}, albero cambiato={lab.impronta() != prima} {r.stderr[-200:]}")

        # UN13: un collegamento alla cartella del vincitore, poi uno verso un'altra cartella
        lab.handoff("specchio-vero", "2026-11-17_08-00", "guardo lo specchio.")
        (lab.h / "specchio").symlink_to("specchio-vero")
        lab.arturo("todo", "aggiungi", "Lavoro dello specchio", "--progetto", "specchio")
        r = lab.arturo("progetti", "unisci", "specchio", "specchio-vero")
        nomi = sorted(p.name for p in (lab.h / "specchio-vero").iterdir())
        if r.returncode != 0 or nomi != ["HANDOFF_2026-11-17_08-00.md"]:
            rossi.append(f"UN13 collegamento: rc={r.returncode} {nomi} {r.stderr[-200:]}")
        lab.handoff("altrove", "2026-11-16_08-00", "altrove.")
        (lab.h / "deviato").symlink_to("altrove")
        lab.arturo("todo", "aggiungi", "Lavoro deviato", "--progetto", "deviato")
        prima = lab.impronta()
        r = lab.arturo("progetti", "unisci", "deviato", "fenice")
        if r.returncode != 2 or lab.impronta() != prima:
            rossi.append(f"UN13 collegamento altrove: rc={r.returncode}, albero cambiato={lab.impronta() != prima}")

        # UN05: anteprima
        prima = lab.impronta()
        r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice", "--prova", "--json")
        try:
            a = json.loads(r.stdout)
        except ValueError:
            a = {}
        if (r.returncode != 0 or lab.impronta() != prima or a.get("todo") != 2 or a.get("handoff") != 2
                or a.get("link") != 1 or a.get("terminali") != 1 or not a.get("rinominati")):
            rossi.append(f"UN05 --prova: rc={r.returncode}, albero cambiato={lab.impronta() != prima}, {r.stdout[-300:]}")

        # UN09 e UN10: la fonte rifiuta o è giù
        for caso, modo, atteso in (("UN09", "rifiuta", 2), ("UN10", "giu", 3)):
            lab.fonte(modo)
            prima = lab.impronta()
            r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice")
            if r.returncode != atteso or lab.impronta() != prima:
                rossi.append(f"{caso} fonte {modo}: rc={r.returncode}, albero cambiato={lab.impronta() != prima} "
                             f"{r.stderr[-200:]}")

        lab.fonte("giu")
        r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice", "--prova")
        if r.returncode != 0 or "la fonte dei task è giù" not in r.stdout or "todo: 2" not in r.stdout:
            rossi.append(f"UN10 anteprima con la fonte giù: rc={r.returncode} {r.stdout[-200:]!r} {r.stderr[-200:]!r}")

        # l'unione vera, con la fonte che unisce
        lab.fonte("unisce")
        r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice")
        if r.returncode != 0:
            rossi.append(f"UN01 unione: rc={r.returncode} {r.stderr[-300:]} {r.stdout[-300:]}")
        lab.fonte(None)

        vinc, perd = lab.todo("fenice"), lab.todo("fenice-vecchia")
        if sorted(vinc) != ["Chiamare la tipografia", "Lavoro del vincitore", "Mandare le bozze"] or perd:
            rossi.append(f"UN01 todo: vincitore={vinc}, perdente={perd}")
        s = lab.arturo("todo", "stato", "--progetto", "fenice")
        if "bozze in stampa" not in s.stdout:
            rossi.append(f"UN02 stato: {s.stdout.strip()!r} {s.stderr.strip()[-200:]}")

        d = lab.h / "fenice"
        nomi = sorted(p.name for p in d.iterdir()) if d.exists() else []
        index = (lab.h / "INDEX.md").read_text(encoding="utf-8")
        spostato = d / "HANDOFF_2026-11-18_10-01.md"
        testo = spostato.read_text(encoding="utf-8") if spostato.exists() else ""
        if (nomi != ["HANDOFF_2026-11-18_10-00.md", "HANDOFF_2026-11-18_10-01.md", "HANDOFF_2026-11-19_09-00.md"]
                or (lab.h / "fenice-vecchia").exists() or "- Nome: fenice /" not in testo
                or "- Filone: fenice/stampa" not in testo or "io chiamo la tipografia" not in testo
                or "scelgo la carta" not in (d / "HANDOFF_2026-11-18_10-00.md").read_text(encoding="utf-8")
                or "fenice/HANDOFF_2026-11-19_09-00.md" not in index or "fenice-vecchia/" in index):
            rossi.append(f"UN03 handoff: {nomi}, testo={testo[:160]!r}, index={index[-300:]!r}")

        p = lab.mem / "progetti"
        sch_v = (p / "progetto-fenice.md").read_text(encoding="utf-8") if (p / "progetto-fenice.md").exists() else ""
        arch = lab.mem / "_archive" / "progetti" / "progetto-fenice-vecchia.md"
        sch_a = arch.read_text(encoding="utf-8") if arch.exists() else ""
        nota = (p / "persona-tipografo.md").read_text(encoding="utf-8")
        if ((p / "progetto-fenice-vecchia.md").exists() or "alias: [fenice-vecchia, rivista]\n" not in sch_v
                or "cartella: ~/Documents/ClaudeCode/fenice-codice\n" not in sch_v
                or "## Da fenice-vecchia (unito il 20/11/2026)\n\nLa tipografia è a Torino." not in sch_v
                or "Corpo del vincitore." not in sch_v or "status: closed\n" not in sch_a
                or "unito_in: progetto-fenice\n" not in sch_a or "[[progetto-fenice]]" not in nota
                or "[[progetto-altro]]" not in nota):
            rossi.append(f"UN04 scheda: {sch_v!r} archivio: {sch_a!r} nota: {nota!r}")

        unioni = sorted((lab.cl / "data" / "progetti" / "unioni").glob("*-fenice-vecchia-in-fenice"))
        ok7 = False
        if len(unioni) == 1 and (unioni[0] / "manifesto.json").exists():
            m = json.loads((unioni[0] / "manifesto.json").read_text(encoding="utf-8"))
            copie = [Path(v["copia"]) for v in m["file"] if v["origine"].endswith("progetto-fenice-vecchia.md")]
            ok7 = bool(copie) and "La tipografia è a Torino." in copie[0].read_text(encoding="utf-8") \
                and "status: active" in copie[0].read_text(encoding="utf-8")
        if not ok7:
            rossi.append(f"UN07 copia di sicurezza: {unioni}")

        c = lab.arturo("contesto", "fenice-vecchia")
        if c.returncode != 0 or "nome vecchio" not in c.stdout or "fenice" not in c.stdout:
            rossi.append(f"UN08 contesto: rc={c.returncode} {c.stdout[:300]!r}")

        log = (lab.home / "fonte.log").read_text(encoding="utf-8").splitlines() if (lab.home / "fonte.log").exists() else []
        chiamate = [json.loads(x) for x in log]
        vera = [x for x in chiamate if "--backup" in x]
        if (not vera or not unioni or not vera[-1][vera[-1].index("--backup") + 1].startswith(str(unioni[0]))
                or "la commessa vecchia resta in Progetti" not in r.stdout):
            rossi.append(f"UN11 fonte: chiamate={chiamate[-3:]}, esito={r.stdout[-300:]!r}")

        t1 = json.loads((lab.cl / "cache" / "scheda" / "s1.json").read_text(encoding="utf-8"))
        t2 = json.loads((lab.cl / "cache" / "scheda" / "s2.json").read_text(encoding="utf-8"))
        if t1.get("progetto") != "fenice" or t2.get("progetto") != "altro" or t1.get("stato") != "attende":
            rossi.append(f"UN12 terminali: {t1} {t2}")

        # UN14: la riga di stato del perdente è tolta, quella del vincitore resta
        e = lab.arturo("progetti", "--json")
        try:
            nomi = [str(v.get("slug")) for v in json.loads(e.stdout)["progetti"]]
        except (ValueError, KeyError, TypeError, AttributeError):
            nomi = None
        s = lab.arturo("todo", "stato", "--progetto", "fenice")
        registro = lab.cl / "data" / "todo" / "progetti.jsonl"
        righe = [json.loads(x) for x in registro.read_text(encoding="utf-8").splitlines() if x.strip()]
        ultima = ([v for v in righe if v.get("progetto") == "fenice-vecchia"] or [{}])[-1]
        if (nomi is None or "fenice" not in nomi or "fenice-vecchia" in nomi or "bozze in stampa" not in s.stdout
                or ultima.get("tolto") is not True or ultima.get("riga") != ""):
            rossi.append(f"UN14 riga di stato del perdente: progetti={nomi}, stato={s.stdout.strip()!r}, "
                         f"ultima riga={ultima} {e.stderr[-200:]}")

        # UN15: il secondo giro è rifiutato, vero e di prova
        prima = lab.impronta()
        r2 = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice")
        p2 = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice", "--prova", "--json")
        try:
            rifiuto = str(json.loads(p2.stdout).get("rifiuto"))
        except (ValueError, AttributeError):
            rifiuto = ""
        if (r2.returncode != 2 or "è già unito in fenice" not in r2.stderr or p2.returncode != 2
                or "è già unito in fenice" not in rifiuto or lab.impronta() != prima):
            rossi.append(f"UN15 secondo giro: rc={r2.returncode}/{p2.returncode}, albero cambiato={lab.impronta() != prima} "
                         f"{r2.stderr[-200:]!r} {p2.stdout[-200:]!r}")

        def errore_json(*a: str) -> tuple:
            r = lab.arturo("progetti", "unisci", *a, "--json")
            try:
                d = json.loads(r.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                d = {}
            return r.returncode, d

        # UN16: il tipo di ogni errore
        tipi = {"repo diversi": (errore_json("uno", "due", "--prova"), 2, "scelta"),
                "collegamento altrove": (errore_json("deviato", "fenice", "--prova"), 2, "riparabile"),
                "secondo giro": (errore_json("fenice-vecchia", "fenice", "--prova"), 2, "gia_unito"),
                "niente": (errore_json("nessuno", "fenice", "--prova"), 2, "scelta")}
        lab.arturo("todo", "aggiungi", "Lavoro della fonte", "--progetto", "fonte-a")
        lab.fonte("rifiuta")
        tipi["fonte rifiuta"] = (errore_json("fonte-a", "fenice", "--prova"), 2, "scelta")
        lab.fonte("giu")
        tipi["fonte giù"] = (errore_json("fonte-a", "fenice"), 3, "transitorio")
        lab.fonte(None)
        sbagli = {k: (rc, d.get("tipo")) for k, ((rc, d), rc_a, tipo) in tipi.items()
                  if rc != rc_a or d.get("tipo") != tipo or d.get("fatto") is not False or "fase" not in d}
        if sbagli:
            rossi.append(f"UN16 tipi: {sbagli}")

        # UN17: un guasto a metà. La cartella handoff del vincitore è un file: mkdir cade dopo copia e todo.
        lab.handoff("rotto-a", "2026-11-15_08-00", "rompo.")
        lab.arturo("todo", "aggiungi", "Lavoro rotto", "--progetto", "rotto-a")
        (lab.h / "rotto-b").write_text("non sono una cartella\n", encoding="utf-8")
        rc, d = errore_json("rotto-a", "rotto-b")
        cp = Path(d.get("backup") or "/nessuna")
        esito = json.loads((cp / "esito.json").read_text(encoding="utf-8")) if (cp / "esito.json").exists() else {}
        tb = (cp / "errore.txt").read_text(encoding="utf-8") if (cp / "errore.txt").exists() else ""
        if (rc != 1 or d.get("tipo") != "riparabile" or d.get("fase") != "scrittura" or "Traceback" not in tb
                or esito.get("fase") != "scrittura" or esito.get("fatto") is not False
                or esito.get("tipo") != "riparabile" or "guasto durante la fase scrittura" not in str(d.get("rifiuto"))):
            rossi.append(f"UN17 guasto a metà: rc={rc} {d} esito={esito} tb={tb[-120:]!r}")

        # UN18: esito.json di un'unione riuscita
        esiti = [json.loads((u / "esito.json").read_text(encoding="utf-8")) for u in unioni if (u / "esito.json").exists()]
        if len(esiti) != 1 or esiti[0].get("fatto") is not True or esiti[0].get("fase") != "fatto":
            rossi.append(f"UN18 esito dell'unione riuscita: {esiti}")

        # UN19: la scheda del vincitore ha già la sezione del perdente, la scheda del perdente è ancora lì
        p = lab.mem / "progetti"
        (p / "progetto-doppia-a.md").write_text(
            "---\nname: progetto-doppia-a\nstatus: closed\nunito_in: progetto-doppia-b\n---\nCorpo di a.\n",
            encoding="utf-8")
        (p / "progetto-doppia-b.md").write_text(
            "---\nname: progetto-doppia-b\nalias: [doppia-a]\nstatus: active\n---\nCorpo di b.\n\n"
            "## Da doppia-a (unito il 20/11/2026)\n\nCorpo di a.\n", encoding="utf-8")
        r = lab.arturo("progetti", "unisci", "doppia-a", "doppia-b")
        sch = (p / "progetto-doppia-b.md").read_text(encoding="utf-8")
        if r.returncode != 0 or sch.count("## Da doppia-a (") != 1 or (p / "progetto-doppia-a.md").exists():
            rossi.append(f"UN19 secondo giro sulla scheda: rc={r.returncode} {sch!r} {r.stderr[-200:]}")

        # UN20: restano solo un link e l'alias
        (p / "progetto-link-b.md").write_text(
            "---\nname: progetto-link-b\nalias: [link-a]\nstatus: active\n---\nCorpo.\n", encoding="utf-8")
        (p / "persona-lettore.md").write_text("---\nname: persona-lettore\n---\nLegge [[progetto-link-a]].\n",
                                              encoding="utf-8")
        r = lab.arturo("progetti", "unisci", "link-a", "link-b")
        nota = (p / "persona-lettore.md").read_text(encoding="utf-8")
        if r.returncode != 0 or "[[progetto-link-b]]" not in nota:
            rossi.append(f"UN20 link rimasti: rc={r.returncode} {nota!r} {r.stderr[-200:]}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    repo = Path(a.repo)
    if a.avvelena:
        inerti = []
        for caso in CASI:
            try:
                rossi = prova(repo, VELENI[caso])
            except AssertionError as e:
                inerti.append(f"{caso}: {e}")
                continue
            if not any(r.startswith(caso + " ") for r in rossi):
                inerti.append(f"{caso}: la rottura non lo fa rosso")
        assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
        print(f"VELENI_ROSSI={','.join(CASI)} veleni={len(CASI)}")
        return 0
    rossi = prova(repo)
    for r in rossi:
        print("ROSSO", r)
    print(f"unisci: {len(CASI) - len(set(r.split()[0] for r in rossi))}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
