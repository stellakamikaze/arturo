#!/usr/bin/env python3
"""arturo progetti: l'elenco dei progetti letto dalla memoria che c'è già (bin/progetti.py, 11/11/2026).

PM01 un progetto che vive solo negli handoff (nessuna cartella, nessun todo) compare, con data, stato e
     prossimo passo.
PM02 con l'INDEX aggiornato stato e prossimo passo vengono dall'INDEX, e i filoni si contano.
PM03 con l'INDEX rimasto indietro vale l'ultimo handoff.
PM04 il comando non scrive: l'albero della HOME di prova è identico prima e dopo.
PM05 la fonte esterna col verbo catalogo unisce due nomi dello stesso progetto in una voce sola: il nome
     senza handoff (qui lo slug della fonte, che ha solo una cartella) va in alias di quello con gli
     handoff, e titolo e categoria vengono dalla fonte.
PM06 una fonte senza il verbo catalogo (exit 2) lascia l'elenco locale intero, con un avviso.
PM07 una cartella senza handoff compare, con la sua riga di stato; quelle con "_" o "." davanti no.
PM08 la scheda progetto-<slug>.md della memoria dà la descrizione.
PM09 un progetto che sta solo nel catalogo della fonte compare.
PM10 con 150 progetti il comando risponde entro 3 secondi.
PM11 un nome alternativo con i suoi handoff resta una voce a parte, con la categoria del gruppo e fuori
     dagli alias: la persona lo apre da solo con /inizio.
PM12 la scheda di un progetto porta titolo e nomi alternativi (12/11/2026): il campo `titolo:` vince sul
     titolo della fonte, e `alias:` fonde nel progetto una cartella col nome vecchio, come la fonte.
PM13 `arturo progetti titolo <slug> "<Titolo>"` scrive solo la riga `titolo:` della scheda: la prima volta
     la aggiunge sotto `name:`, la seconda la riscrive, il resto del file resta identico; una scheda che
     non c'è esce 2 e non crea niente.
PM14 il catalogo sono le schede della memoria (13/11/2026): una scheda aperta senza cartella né handoff compare, con dove,
     macchine e repo del frontmatter anche oltre la quarantesima riga; una scheda chiusa da sola no.
PM16 `arturo progetti doppioni --json` (23/11/2026, #6422): due nomi che cambiano di una lettera, ognuno coi suoi
     handoff, sono una coppia, e resta quello con più filoni; una cartella senza handoff (guscio) non entra.
PM17 le coppie scartate (--scartate FILE): n dispari la toglie, n pari la rimette, un numero solo vale n 1;
     un file che non è JSON esce 4 e non dà un elenco vuoto.
PM15 uno slug della fonte che è già alias di una scheda (vecchio-nome) si fonde nella voce della scheda
     (22/11/2026): non nasce un progetto nuovo, e la voce prende la categoria della fonte.
PM18 un nome alternativo già unito (21/11/2026): la sua cartella di handoff è un collegamento a quella del
     progetto, quindi non ha handoff suoi. Non resta una voce a parte: entra negli alias, anche con la sua
     cartella di codice. Dove il sistema non fa creare collegamenti il caso si salta.

Veleno: --avvelena rompe bin/progetti.py nella copia di prova, un punto per caso, ed esce 0 solo se ogni
rottura fa rosso il suo caso (VELENI del gate).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import os
from pathlib import Path

CASI = ["PM01", "PM02", "PM03", "PM04", "PM05", "PM06", "PM07", "PM08", "PM09", "PM10", "PM11", "PM12", "PM13", "PM14", "PM15", "PM16", "PM17", "PM18"]
CATALOGO = ('import json, sys\n'
            'if sys.argv[1:] != ["catalogo", "--json"]:\n'
            '    sys.exit(2)\n'
            'print(json.dumps({"progetti": [\n'
            '    {"slug": "aria", "titolo": "Tutto Vero", "categoria": "Prodotti", "alias": ["tutto-vero"]},\n'
            '    {"slug": "madre", "titolo": "Madre", "categoria": "Dev", "alias": ["filone"]},\n'
            '    {"slug": "solo-fonte", "titolo": "Solo Fonte", "categoria": "Clienti", "alias": []},\n'
            '    {"slug": "vecchio-nome", "titolo": "Fonte Vecchio", "categoria": "Clienti", "alias": []},\n'
            '    {"slug": "titolata", "titolo": "Dalla Fonte", "categoria": "Clienti", "alias": []}]}))\n')
SENZA = 'import sys\nsys.exit(2)\n'
# caso -> (testo di bin/progetti.py, testo rotto): ogni rottura deve far rosso il suo caso
VELENI = {
    "PM01": ("if lista and s and (", "if False and ("),
    "PM02": ('if riga and riga["file"] >= percorso.name:', "if False:"),
    "PM03": ('if riga and riga["file"] >= percorso.name:', "if riga:"),
    "PM04": ("    dati = elenco()\n", '    dati = elenco()\n    (cx.handoff_dir() / "SPIA").write_text("x")\n'),
    "PM05": ('            del voci[v["slug"]]\n', "            pass\n"),
    "PM06": ('avvisi.append("la fonte dei task non ha', 'str("la fonte dei task non ha'),
    "PM07": ('if p.name[:1] in "._" or not cx.e_cartella(p):', "if not cx.e_cartella(p):"),
    "PM08": ('if chiave == "description":', "if False:"),
    "PM09": ('            voci[c["slug"]] = capo\n', "            pass\n"),
    "PM10": ("    dati = elenco()\n", "    import time\n    time.sleep(4)\n    dati = elenco()\n"),
    "PM11": ('            if v["handoff"]:  # un filone', '            if False:  # un filone'),
    "PM12": ('= capo["titolo"] or c["titolo"], c["categoria"]', '= c["titolo"] or capo["titolo"], c["categoria"]'),
    "PM14": ('aperte = {s for s, n in note.items() if n.get("status") != "closed"}', "aperte = set()"),
    "PM15": ('        gruppo += [propri[s]', '        gruppo += [] and [propri[s]'),
    "PM13": ("        righe[i] = nuova\n", "        righe[i:fine] = [nuova]\n"),
    # terzo elemento: il file da rompere, se non è bin/progetti.py
    "PM16": ("(d == 1 and corto >= 5)", "(d == 1 and corto >= 50)", "doppioni.py"),
    "PM17": ("if isinstance(n, int) and n % 2 == 1:", "if True:", "doppioni.py"),
    "PM18": ("or not cx.e_cartella(d) or collegata(d):", "or not cx.e_cartella(d):"),
}


def handoff(stato: str, prossimo: str) -> str:
    return (f"# Session Handoff\n## Progetto\n- Nome: x / Branch: main\n- Status: {stato}\n\n"
            f"## Ripartenza\n**Prossimo passo:** {prossimo}\n")


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.tmp, self.home = tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=ignora)
        shutil.copytree(str(repo / "hooks"), str(self.cl / "hooks"), ignore=ignora)
        self.base = self.home / "Documents" / "ClaudeCode"
        self.base.mkdir(parents=True)
        self.h = self.cl / "data" / "handoffs"
        self.h.mkdir(parents=True)
        self.fonte = tmp / "fonte.py"

    def scrivi_handoff(self, slug: str, quando: str, stato: str, prossimo: str) -> None:
        f = self.h / slug / f"HANDOFF_{quando}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(handoff(stato, prossimo), encoding="utf-8")

    def index(self, righe: list) -> None:
        testo = "| Progetto | Ultimo handoff | Data | Stato | Prossimo passo |\n|---|---|---|---|---|\n"
        for etichetta, slug, quando, stato, prossimo in righe:
            testo += (f"| {etichetta} | [HANDOFF_{quando}.md]({slug}/HANDOFF_{quando}.md) | {quando[:10]} | {stato} "
                      f"| {prossimo} |\n")
        (self.h / "INDEX.md").write_text(testo, encoding="utf-8")

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-11", ARTURO_MEMORIA="1")
        for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR"):
            e.pop(k, None)
        return e

    def locale(self, codice) -> None:
        f = self.cl / "arturo" / "fonte-task.local"
        if codice is None:
            if f.exists():
                f.unlink()
            return
        f.parent.mkdir(exist_ok=True)
        self.fonte.write_text(codice, encoding="utf-8")
        f.write_text(f"comando = {Path(sys.executable).as_posix()} {self.fonte.as_posix()}\n", encoding="utf-8")

    def arturo(self, *a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), *a], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.env(), timeout=120, cwd=str(self.home))

    def progetti(self):
        r = self.arturo("progetti", "--json")
        try:
            d = json.loads(r.stdout)
            return {p["slug"]: p for p in d["progetti"]}, d["avvisi"], r
        except (ValueError, KeyError, TypeError):
            return {}, [], r

    def impronta(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.home.rglob("*")):
            st = p.lstat()
            h.update(f"{p.relative_to(self.home).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
        return h.hexdigest()


def prova(lab: Lab) -> list:
    rossi = []
    # la memoria di prova
    lab.scrivi_handoff("solo-handoff", "2026-11-10_09-00", "in progress", "PASSO-DAL-FILE")
    lab.scrivi_handoff("con-index", "2026-11-09_09-00", "vecchio", "PASSO-DAL-FILE")
    lab.scrivi_handoff("indietro", "2026-11-01_09-00", "vecchio", "PASSO-VECCHIO")
    lab.scrivi_handoff("indietro", "2026-11-08_09-00", "bloccato", "PASSO-NUOVO-DAL-FILE")
    lab.scrivi_handoff("tutto-vero", "2026-11-07_09-00", "in progress", "PASSO-TUTTO-VERO")
    lab.scrivi_handoff("madre", "2026-10-01_09-00", "completato", "PASSO-MADRE")
    lab.scrivi_handoff("filone", "2026-11-06_09-00", "in progress", "PASSO-FILONE")
    lab.index([("con-index — filone uno", "con-index", "2026-11-09_09-00", "completato", "PASSO-DALL-INDEX"),
               ("con-index — filone due", "con-index", "2026-11-02_09-00", "in progress", "PASSO-FILONE-DUE"),
               ("indietro", "indietro", "2026-11-01_09-00", "vecchio", "PASSO-INDEX-INDIETRO")])
    for nome in ("solo-cartella", "tutto-vero", "aria", "_bozze", ".nascosta"):
        (lab.base / nome).mkdir()
    lab.arturo("todo", "stato", "--progetto", "solo-cartella", "RIGA-DI-STATO")
    scheda = lab.cl / "data" / "memory" / "progetti" / "progetto-solo-handoff.md"
    scheda.parent.mkdir(parents=True)
    scheda.write_text("---\nname: progetto-solo-handoff\ndescription: DESCRIZIONE-DALLA-SCHEDA\ntype: project\n---\ncorpo\n",
                      encoding="utf-8")
    (lab.base / "vecchio-nome").mkdir()
    (scheda.parent / "progetto-titolata.md").write_text("---\nname: progetto-titolata\ntitolo: \"TITOLO-SCHEDA\"\ndescription: x\n---\n",
                                                        encoding="utf-8")
    (scheda.parent / "progetto-con-index.md").write_text("---\nname: progetto-con-index\nalias: [vecchio-nome, nome-unito]\n---\n", encoding="utf-8")
    (lab.base / "nome-unito").mkdir()
    try:
        os.symlink("con-index", str(lab.h / "nome-unito"), target_is_directory=True)
        collegamenti = True
    except (OSError, NotImplementedError):
        collegamenti = False  # Windows senza il permesso dei collegamenti
    lab.scrivi_handoff("titolata", "2026-10-02_09-00", "in progress", "PASSO-TITOLATA")
    lunghe = "".join(f"  - domanda {n}\n" for n in range(50))
    (scheda.parent / "progetto-sola-scheda.md").write_text(
        "---\nname: progetto-sola-scheda\nstatus: active\nanswers:\n" + lunghe
        + "cartella: ~/Documents/ClaudeCode/sola-src\nmacchina: [studio, torre]\nrepo: stellakamikaze/sola\n---\n",
        encoding="utf-8")
    (scheda.parent / "progetto-chiusa-sola.md").write_text("---\nname: progetto-chiusa-sola\nstatus: closed\n---\n",
                                                           encoding="utf-8")

    prima = lab.impronta()
    p, avvisi, r = lab.progetti()
    dopo = lab.impronta()
    v = p.get("solo-handoff", {})
    if r.returncode != 0 or v.get("data") != "2026-11-10" or v.get("stato") != "in progress" \
            or v.get("prossimo") != "PASSO-DAL-FILE" or v.get("cartella") or not v.get("handoff"):
        rossi.append(f"PM01 solo handoff: rc={r.returncode} voce={v} {r.stderr.strip()[-200:]!r}")
    v = p.get("con-index", {})
    if v.get("stato") != "completato" or v.get("prossimo") != "PASSO-DALL-INDEX" or v.get("filoni") != 2:
        rossi.append(f"PM02 INDEX: {v}")
    v = p.get("indietro", {})
    if v.get("data") != "2026-11-08" or v.get("stato") != "bloccato" or v.get("prossimo") != "PASSO-NUOVO-DAL-FILE":
        rossi.append(f"PM03 INDEX indietro: {v}")
    if prima != dopo or not p:
        rossi.append(f"PM04 il comando ha scritto nella HOME di prova (o non ha risposto): {len(p)} voci")
    v = p.get("solo-cartella", {})
    if v.get("riga") != "RIGA-DI-STATO" or not v.get("cartella") or v.get("handoff") \
            or "bozze" in p or "nascosta" in p or avvisi:
        rossi.append(f"PM07 cartella e stato: {v} bozze={'bozze' in p} nascosta={'nascosta' in p} avvisi={avvisi}")
    v = p.get("sola-scheda", {})
    if v.get("dove") != "~/Documents/ClaudeCode/sola-src" or v.get("macchine") != ["studio", "torre"] \
            or v.get("repo") != "stellakamikaze/sola" or "chiusa-sola" in p:
        rossi.append(f"PM14 scheda sola: {v} chiusa in elenco={'chiusa-sola' in p}")
    v = p.get("con-index", {})
    if collegamenti and ("nome-unito" in p or "nome-unito" not in v.get("alias", []) or v.get("filoni") != 2 or not v.get("cartella")):
        rossi.append(f"PM18 nome già unito, handoff collegati: nome-unito in elenco={'nome-unito' in p} con-index={v}")
    if p.get("solo-handoff", {}).get("descrizione") != "DESCRIZIONE-DALLA-SCHEDA":
        rossi.append(f"PM08 scheda: {p.get('solo-handoff')}")

    lab.locale(CATALOGO)
    p, avvisi, r = lab.progetti()
    v = p.get("tutto-vero", {})
    if "aria" in p or v.get("alias") != ["aria"] or v.get("titolo") != "Tutto Vero" or v.get("categoria") != "Prodotti" \
            or v.get("data") != "2026-11-07" or avvisi:
        rossi.append(f"PM05 alias: aria in elenco={'aria' in p} voce={v} avvisi={avvisi}")
    v, w = p.get("madre", {}), p.get("filone", {})
    if v.get("titolo") != "Madre" or v.get("alias") != [] or w.get("categoria") != "Dev" or w.get("titolo") \
            or w.get("data") != "2026-11-06":
        rossi.append(f"PM11 filone con i suoi handoff: madre={v} filone={w}")
    v = p.get("solo-fonte", {})
    if v.get("titolo") != "Solo Fonte" or v.get("fonte") != ["fonte"]:
        rossi.append(f"PM09 solo nella fonte: {v}")
    if p.get("titolata", {}).get("titolo") != "TITOLO-SCHEDA" or "vecchio-nome" in p \
            or "vecchio-nome" not in p.get("con-index", {}).get("alias", []):
        rossi.append(f"PM12 titolo e alias della scheda: titolata={p.get('titolata')} vecchio-nome in elenco={'vecchio-nome' in p} "
                     f"con-index={p.get('con-index')}")
    if "vecchio-nome" in p or p.get("con-index", {}).get("categoria") != "Clienti":
        rossi.append(f"PM15 slug della fonte uguale a un alias: vecchio-nome in elenco={'vecchio-nome' in p} "
                     f"con-index={p.get('con-index')}")
    prima_s = scheda.read_text(encoding="utf-8")
    r1 = lab.arturo("progetti", "titolo", "solo-handoff", "Nome Nuovo")
    uno = scheda.read_text(encoding="utf-8")
    r2 = lab.arturo("progetti", "titolo", "solo-handoff", "Nome Ancora")
    due = scheda.read_text(encoding="utf-8")
    r3 = lab.arturo("progetti", "titolo", "non-esiste", "X")
    atteso = prima_s.replace("name: progetto-solo-handoff\n", 'name: progetto-solo-handoff\ntitolo: "Nome Nuovo"\n')
    if r1.returncode != 0 or uno != atteso or due != atteso.replace("Nome Nuovo", "Nome Ancora") or r3.returncode != 2 \
            or (scheda.parent / "progetto-non-esiste.md").exists():
        rossi.append(f"PM13 verbo titolo: rc={r1.returncode},{r2.returncode},{r3.returncode} uno={uno!r} due={due!r}")

    # PM16-PM17: doppioni. Due nomi a una lettera, e un guscio (solo la cartella) che non deve entrare.
    lab.locale(None)
    lab.scrivi_handoff("teleclub", "2026-11-10_09-00", "in progress", "primo")
    lab.scrivi_handoff("teleclub", "2026-11-11_09-00", "in progress", "secondo")
    lab.scrivi_handoff("telecub", "2026-11-09_09-00", "in progress", "vecchio")
    (lab.base / "telecubo").mkdir()
    r = lab.arturo("progetti", "doppioni", "--json")
    try:
        coppie = {c["chiave"]: c for c in json.loads(r.stdout)["coppie"]}
    except (ValueError, KeyError):
        coppie = {}
    c = coppie.get("teleclub|telecub", {})
    if r.returncode != 0 or c.get("vincitore") != "teleclub" or c.get("perdente") != "telecub" \
            or any("telecubo" in k for k in coppie):
        rossi.append(f"PM16 coppia a una lettera: rc={r.returncode} coppie={sorted(coppie)} voce={c}")
    scarti = lab.tmp / "scartate.json"

    def con_scarti(contenuto):
        scarti.write_text(contenuto, encoding="utf-8")
        x = lab.arturo("progetti", "doppioni", "--json", "--scartate", str(scarti))
        try:
            return x.returncode, {k["chiave"] for k in json.loads(x.stdout)["coppie"]}
        except (ValueError, KeyError):
            return x.returncode, None

    uno = con_scarti('{"teleclub|telecub": 1700000000000}')
    n1 = con_scarti('{"teleclub|telecub": {"n": 1, "quando": 5}}')
    n2 = con_scarti('{"teleclub|telecub": {"n": 2, "quando": 5}}')
    rotto = con_scarti("{non json")
    if uno != (0, set()) or n1 != (0, set()) or n2[0] != 0 or "teleclub|telecub" not in (n2[1] or ()) or rotto != (4, None):
        rossi.append(f"PM17 scartate: numero solo={uno} n1={n1} n2={n2} rotto={rotto}")

    lab.locale(SENZA)
    p, avvisi, r = lab.progetti()
    if r.returncode != 0 or "aria" not in p or "tutto-vero" not in p or "solo-handoff" not in p \
            or not any("catalogo" in a for a in avvisi):
        rossi.append(f"PM06 fonte senza catalogo: rc={r.returncode} voci={sorted(p)} avvisi={avvisi}")

    lab.locale(None)
    for n in range(150):
        lab.scrivi_handoff(f"tanti-{n:03d}", "2026-10-20_09-00", "in progress", f"passo {n}")
    t0 = time.time()
    p, _, r = lab.progetti()
    durata = time.time() - t0
    if sum(1 for s in p if s.startswith("tanti-")) != 150 or durata > 3:
        rossi.append(f"PM10 tempo: {durata:.2f}s per {len(p)} voci")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        inerti = []
        for caso in CASI:
            vecchio, rotto = VELENI[caso][:2]
            with tempfile.TemporaryDirectory(prefix="arturo-pm-") as tmp:
                lab = Lab(Path(argomenti.repo), Path(tmp))
                sorgente = lab.cl / "bin" / (VELENI[caso][2] if len(VELENI[caso]) > 2 else "progetti.py")
                testo = sorgente.read_text(encoding="utf-8")
                if testo.count(vecchio) != 1:
                    inerti.append(f"{caso}: il punto da rompere compare {testo.count(vecchio)} volte")
                    continue
                sorgente.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
                rossi = prova(lab)
                if caso == "PM18" and not (lab.h / "nome-unito").is_symlink():
                    continue  # senza collegamenti il caso non gira, e il veleno non ha niente da rompere
                if not any(r.startswith(caso + " ") for r in rossi):
                    inerti.append(f"{caso}: la rottura non lo fa rosso")
        assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
        print(f"VELENI_ROSSI={','.join(CASI)} veleni={len(CASI)}")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-pm-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), Path(tmp)))
    for r in rossi:
        print("ROSSO", r)
    print(f"progetti dalla memoria: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
