#!/usr/bin/env python3
"""VA01-VA03: le tre viste dei todo sanno fare le stesse cose (3/11/2026, #3868).

I todo si cambiano da quattro posti: la CLI `arturo todo`, la pagina `arturo web`, il pannello /dafare e,
dall'8/11/2026 sul ramo herdr, il pannello Da fare di Herdr (shared/volta-celeste/mods/arturo/azioni.js).
Questo banco legge i verbi che scrivono in ognuno e li confronta. Un verbo manca da una vista solo se
la tabella ECCEZIONI lo dice, col motivo: così un verbo nuovo della CLI non resta fuori dalla pagina
o dal pannello senza che nessuno l'abbia deciso.

VA01 ogni verbo che scrive della CLI c'è nella pagina e nei due pannelli, o ha la sua eccezione.
VA02 la pagina e i pannelli non hanno verbi che la CLI non conosce.
VA03 nessuna eccezione è superata: se la vista ora fa il verbo, l'eccezione va tolta.

Con --avvelena quattro copie rotte del repository devono far rosso il caso che le sorveglia: `dopo` tolto
dalla pagina (VA01), un verbo inventato nel pannello (VA02) e in quello di Herdr (VA02), `su` aggiunto alla pagina con
l'eccezione ancora scritta (VA03). Sulla base acb4a39 la pagina non ha `dopo`: VA01 è rosso.
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

# (vista, verbo della CLI): perché quella vista non lo fa.
ECCEZIONI = {
    ("pagina", "su"): "la pagina cambia \"quando\" dal campo della modifica, con modifica",
    ("pagina", "giu"): "la pagina cambia \"quando\" dal campo della modifica, con modifica",
    ("pannello", "aggiungi"): "il pannello ha solo gesti da un tasto, senza testo: si aggiunge dalla pagina o da Claude",
    ("pannello", "nota"): "una nota è testo da scrivere: il pannello non ha campi",
    ("pannello", "deciso"): "una decisione è testo da scrivere: il pannello non ha campi",
    ("pannello", "scarta"): "scartare chiede un motivo: il pannello non ha campi, si chiede a Claude",
    ("pannello", "dopo"): "un legame chiede di scegliere un secondo todo: il pannello ha un tasto per riga",
    ("pannello", "inizia"): "\"in corso\" non è fra i sei tasti del pannello, che tiene i gesti più frequenti",
    ("herdr", "su"): "il menu di Herdr sceglie \"quando\" per nome, con modifica --quando",
    ("herdr", "giu"): "il menu di Herdr sceglie \"quando\" per nome, con modifica --quando",
    ("herdr", "deciso"): "una decisione si scrive a Claude, che la registra: il menu ha i gesti, non le scelte",
    ("herdr", "dopo"): "un legame chiede di scegliere un secondo todo: si chiede a Claude",
    ("herdr", "ripristina"): "serve solo all'annullo di pagina e /dafare: Herdr rimette le cose dal menu",
}


def _modulo(nome: str, file: Path):
    caricatore = importlib.machinery.SourceFileLoader(nome, str(file))
    spec = importlib.util.spec_from_loader(nome, caricatore)
    modulo = importlib.util.module_from_spec(spec)
    caricatore.exec_module(modulo)
    return modulo


def verbi(repo: Path) -> dict:
    """I verbi che scrivono, per vista. I moduli si caricano in un processo pulito dal repo indicato."""
    bin_ = str(repo / "bin")
    for nome in ("todo_store", "arturo_web"):
        sys.modules.pop(nome, None)
    sys.path.insert(0, bin_)
    try:
        cli = _modulo("arturo_cli_prova", repo / "bin" / "arturo")
        web = _modulo("arturo_web", repo / "bin" / "arturo_web.py")
    finally:
        sys.path.remove(bin_)
    testo = (repo / "skills" / "arturo" / "hooks" / "dafare" / "verbi.mjs").read_text(encoding="utf-8")
    # Ogni voce di VERBI lancia `arturo todo <verbo> ...` in argv e nel suo inverso: conta il primo elemento.
    pannello = set(re.findall(r"(?:argv|inverso):\s*t\s*=>\s*\[\s*'([a-z]+)'", testo))
    pannello |= set(re.findall(r"return\s*\[\s*'([a-z]+)'", testo))  # gli inversi scritti come funzione
    # Il pannello di Herdr: il primo elemento di ogni argv di azioni.js, anche dentro una funzione.
    herdr = repo / "shared" / "volta-celeste" / "mods" / "arturo" / "azioni.js"
    testo_h = herdr.read_text(encoding="utf-8") if herdr.exists() else ""
    vista_h = set(re.findall(r'argv:\s*(?:\(\s*\w*\s*\)\s*=>\s*)?\[\s*"([a-z]+)"', testo_h))
    return {"cli": set(cli.SCRIVONO) | {"aggiungi"}, "pagina": set(web.AZIONI), "pannello": pannello, "herdr": vista_h}


ARTICOLO = {"pagina": "la pagina", "pannello": "il pannello", "herdr": "il pannello di Herdr"}
VISTE = tuple(ARTICOLO)


def prova(repo: Path) -> list:
    v = verbi(repo)
    rossi = []
    for vista in VISTE:
        mancano = sorted(x for x in v["cli"] - v[vista] if (vista, x) not in ECCEZIONI)
        if mancano:
            rossi.append(f"VA01 {ARTICOLO[vista]} non fa {', '.join(mancano)}: aggiungili o scrivi l'eccezione col motivo")
    for vista in VISTE:
        estranei = sorted(v[vista] - v["cli"])
        if estranei:
            rossi.append(f"VA02 {ARTICOLO[vista]} usa verbi che la CLI non conosce: {', '.join(estranei)}")
    superate = sorted(f"{vista}/{x}" for vista, x in ECCEZIONI if x in v[vista])
    if superate:
        rossi.append(f"VA03 eccezioni superate, la vista ora fa il verbo: {', '.join(superate)}")
    return rossi


VELENI = [
    ("VA01", "bin/arturo_web.py", '"ripristina", "dopo") + tuple', '"ripristina") + tuple'),
    ("VA02", "skills/arturo/hooks/dafare/verbi.mjs", "argv: t => ['fatto', String(t.id), titolo(t)]",
     "argv: t => ['archivia', String(t.id), titolo(t)]"),
    ("VA02", "shared/volta-celeste/mods/arturo/azioni.js", 'argv: () => ["riprendi"', 'argv: () => ["archivia"'),
    ("VA03", "bin/arturo_web.py", '"ripristina", "dopo") + tuple', '"ripristina", "dopo", "su") + tuple'),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests", "cache"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia)
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


CASI = ("VA01", "VA02", "VA03")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        return avvelena(repo)
    rossi = prova(repo)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert "VA01" in codici, f"baseline non discriminante: rossi {codici}, atteso VA01 (la pagina senza dopo)"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"viste allineate: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
