#!/usr/bin/env python3
"""arturo progetti elimina e arturo progetti nuovo (bin/elimina.py, bin/nuovo_progetto.py, 22/11/2026): i due gesti
della schermata Progetti di Volta, "Elimina progetto…" e "Nuovo progetto".

NP01 nuovo "Prova Nuova" --cosa … --json crea progetto-prova-nuova.md col titolo e la riga in "## Cos'è", ed
     esce 0 con lo slug; arturo progetti --json lo elenca col suo titolo.
NP02 un nome già preso esce 2 e non scrive: lo slug di un progetto, un suo nome alternativo, Miscellanea.
NP03 uso sbagliato esce 3 e non scrive: senza --cosa, senza lettere.
EL01 elimina --prova --json non scrive niente e dice che Miscellanea nasce adesso e che la cartella del codice
     resta dov'è.
EL02 elimina vera: i todo e gli handoff passano a Miscellanea, che nasce col titolo Miscellanea, prende il nome
     eliminato fra gli alias e non prende la cartella del codice; la scheda del progetto va in archivio; la riga
     di stato del progetto non passa; la cartella del codice resta su disco.
EL03 due progetti con due repo diversi si eliminano tutti e due, anche con una cartella che si chiama come
     Miscellanea: Miscellanea non ha mai cartella né repo.
EL04 Miscellanea non si elimina e non entra in un altro progetto: exit 3, niente scritto.
EL05 dopo l'eliminazione il nome eliminato apre Miscellanea in /inizio, e nuovo con quel nome esce 2 e dice
     che è un progetto eliminato.

Veleno: --avvelena rompe bin/ nella copia di prova, un punto per caso, ed esce 0 solo se ogni rottura fa rosso
il suo caso.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("test_unisci", str(QUI / "test_unisci_2026_11_20.py"))
_un = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_un)
Lab = _un.Lab

CASI = ["NP01", "NP02", "NP03", "EL01", "EL02", "EL03", "EL04", "EL05"]
# caso -> (file in bin/, testo, testo rotto)
VELENI = {
    "NP01": ("nuovo_progetto.py", 'codice = me.comando_scheda([s, "--cosa", cosa, "--titolo", nome])', 'codice = me.comando_scheda([s, "--cosa", cosa])'),
    "NP02": ("nuovo_progetto.py", "    if di:\n        return rifiuta(2,", "    if False:\n        return rifiuta(2,"),
    "NP03": ("nuovo_progetto.py", "    if not cosa:\n        return rifiuta(3,", "    if False:\n        return rifiuta(3,"),
    "EL01": ("unisci.py", '+ (", che nasce adesso" if r.get("nuova_v") else "")', ""),
    "EL02": ("unisci.py", "    porta_stato = not archivio and bool(stato_p)", "    porta_stato = bool(stato_p)"),
    "EL03": ("unisci.py", "    if archivio:\n        cod_v = (None, \"\")\n", ""),
    "EL04": ("unisci.py", "    if perdente == MISCELLANEA:\n        raise Ferma(3,", "    if False:\n        raise Ferma(3,"),
    "EL05": ("nuovo_progetto.py", "    if di == MISCELLANEA:\n", "    if False:\n"),
}


def leggi(f: Path) -> str:
    return f.read_text(encoding="utf-8") if f.exists() else ""


def js(r) -> dict:
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {}


def prova(repo: Path, rompi=None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="arturo-el-") as tmp:
        lab = Lab(repo, Path(tmp))
        # la memoria (bin/memoria.py) legge scripts/melchior_recall.py: Lab copia solo bin/ e hooks/
        shutil.copytree(str(repo / "scripts"), str(lab.cl / "scripts"), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
        for f in ("elimina.py", "nuovo_progetto.py"):
            assert (lab.cl / "bin" / f).exists(), f"manca bin/{f}"
        if rompi:
            f, vecchio, rotto = rompi
            sorgente = lab.cl / "bin" / f
            testo = sorgente.read_text(encoding="utf-8")
            assert testo.count(vecchio) == 1, f"il punto da rompere in {f} compare {testo.count(vecchio)} volte"
            sorgente.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
        lab.prepara()
        p = lab.mem / "progetti"
        codice = lab.home / "Documents" / "ClaudeCode" / "fenice-codice"
        codice.mkdir(parents=True)
        (codice / "README.md").write_text("codice\n", encoding="utf-8")

        # NP01
        r = lab.arturo("progetti", "nuovo", "Prova Nuova", "--cosa", "un progetto di prova", "--json")
        d, sch = js(r), leggi(p / "progetto-prova-nuova.md")
        el = js(lab.arturo("progetti", "--json"))
        voce = next((v for v in el.get("progetti", []) if v.get("slug") == "prova-nuova"), {})
        if (r.returncode != 0 or d.get("fatto") is not True or d.get("slug") != "prova-nuova" or 'titolo: "Prova Nuova"' not in sch
                and "titolo: Prova Nuova" not in sch or "## Cos'è\nun progetto di prova" not in sch or voce.get("titolo") != "Prova Nuova"):
            rossi.append(f"NP01 nuovo: rc={r.returncode} {r.stdout[-200:]!r} {r.stderr[-200:]!r} scheda={sch[:200]!r} voce={voce}")

        # NP02 e NP03
        for caso, argomenti, atteso, parola in (
                ("NP02", ("fenice", "--cosa", "x"), 2, "c'è già"),
                ("NP02", ("Rivista", "--cosa", "x"), 2, "è un nome di fenice-vecchia"),
                ("NP02", ("Miscellanea", "--cosa", "x"), 2, "Miscellanea c'è già"),
                ("NP03", ("Senza riga",), 3, "serve --cosa: di cosa si tratta"),
                ("NP03", ("!!!", "--cosa", "x"), 3, "almeno una lettera")):
            prima = lab.impronta()
            r = lab.arturo("progetti", "nuovo", *argomenti, "--json")
            if r.returncode != atteso or lab.impronta() != prima or parola not in js(r).get("rifiuto", ""):
                rossi.append(f"{caso} {argomenti[0]}: rc={r.returncode}, albero cambiato={lab.impronta() != prima} {r.stdout[-200:]!r}")

        # EL04: Miscellanea non si elimina (ancora prima che esista) e non entra in un altro progetto
        for argomenti in (("elimina", "miscellanea"), ("unisci", "miscellanea", "fenice")):
            prima = lab.impronta()
            r = lab.arturo("progetti", *argomenti)
            if r.returncode != 3 or lab.impronta() != prima or "Miscellanea non si elimina" not in r.stderr:
                rossi.append(f"EL04 {argomenti}: rc={r.returncode}, albero cambiato={lab.impronta() != prima} {r.stderr[-200:]!r}")

        # EL01: l'anteprima
        prima = lab.impronta()
        r = lab.arturo("progetti", "elimina", "fenice-vecchia", "--prova", "--json")
        a = js(r)
        if (r.returncode != 0 or lab.impronta() != prima or a.get("vincitore") != "miscellanea" or a.get("todo") != 2
                or "che nasce adesso" not in a.get("scheda", "") or a.get("stato") is not False
                or not any("fenice-codice" in x and "resta dov'è" in x for x in a.get("avvisi", []))):
            rossi.append(f"EL01 anteprima: rc={r.returncode}, albero cambiato={lab.impronta() != prima} {r.stdout[-400:]!r}")

        # EL02: l'eliminazione vera
        r = lab.arturo("progetti", "elimina", "fenice-vecchia", "--json")
        e = js(r)
        misc = leggi(p / "progetto-miscellanea.md")
        arch = leggi(lab.mem / "_archive" / "progetti" / "progetto-fenice-vecchia.md")
        stato = lab.arturo("todo", "stato", "--progetto", "miscellanea").stdout
        if (r.returncode != 0 or e.get("fatto") is not True or sorted(lab.todo("miscellanea")) != ["Chiamare la tipografia", "Mandare le bozze"]
                or lab.todo("fenice-vecchia") or not (lab.h / "miscellanea" / "HANDOFF_2026-11-19_09-00.md").exists()
                or 'titolo: "Miscellanea"' not in misc or "fenice-vecchia" not in misc.split("---")[1] or "cartella:" in misc
                or "## Da fenice-vecchia (unito il 20/11/2026)" not in misc or (p / "progetto-fenice-vecchia.md").exists()
                or "unito_in: progetto-miscellanea" not in arch or "bozze in stampa" in stato
                or not (codice / "README.md").exists()):
            rossi.append(f"EL02 elimina: rc={r.returncode} {r.stderr[-200:]!r} misc={misc[:300]!r} arch={arch[:120]!r} stato={stato.strip()!r}")

        # EL03: due repo diversi, e una cartella che si chiama come Miscellanea, con un suo repo
        for nome, url in (("uno", "https://example.org/uno.git"), ("due", "https://example.org/due.git"),
                          ("miscellanea", "https://example.org/misc.git")):
            dd = lab.base / nome
            dd.mkdir()
            subprocess.run(["git", "init", "-q", str(dd)], check=True)
            subprocess.run(["git", "-C", str(dd), "remote", "add", "origin", url], check=True)
            if nome == "miscellanea":
                continue
            (p / f"progetto-{nome}.md").write_text(
                f"---\nname: progetto-{nome}\ndescription: {nome}\ncartella: ~/Documents/ClaudeCode/{nome}\nrepo: x/{nome}\n---\n{nome}.\n",
                encoding="utf-8")
            lab.arturo("todo", "aggiungi", f"Lavoro di {nome}", "--progetto", nome)
        esiti = [lab.arturo("progetti", "elimina", nome) for nome in ("uno", "due")]
        misc = leggi(p / "progetto-miscellanea.md")
        testa = misc.split("---")[1] if misc.count("---") >= 2 else ""
        if (any(x.returncode != 0 for x in esiti) or "cartella:" in testa or "repo:" in testa or "uno" not in testa or "due" not in testa
                or not (lab.base / "uno" / ".git").exists() or not (lab.base / "due" / ".git").exists()):
            rossi.append(f"EL03 repo diversi: rc={[x.returncode for x in esiti]} {[x.stderr[-160:] for x in esiti]} testa={testa!r}")

        # EL05: il nome eliminato
        c = lab.arturo("contesto", "fenice-vecchia")
        prima = lab.impronta()
        r = lab.arturo("progetti", "nuovo", "fenice-vecchia", "--cosa", "x", "--json")
        if (c.returncode != 0 or "miscellanea" not in c.stdout or r.returncode != 2 or lab.impronta() != prima
                or "progetto eliminato" not in js(r).get("rifiuto", "")):
            rossi.append(f"EL05 nome eliminato: contesto rc={c.returncode} {c.stdout[:200]!r} nuovo rc={r.returncode} {r.stdout[-200:]!r}")
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
    print(f"elimina e nuovo: {len(CASI) - len(set(r.split()[0] for r in rossi))}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
