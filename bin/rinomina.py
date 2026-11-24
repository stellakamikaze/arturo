#!/usr/bin/env python3
"""arturo progetti rinomina: cambia il nome di un progetto in un passo, e il nome vecchio resta valido.

Uso: arturo progetti rinomina VECCHIO NUOVO [--prova]

Nasce dalla proposta n. 90 (19/11/2026): a mano servivano sei passi, e le righe vecchie restavano col nome
vecchio. Il comando sposta insieme:
  - i todo del progetto, anche quelli chiusi: un evento "modifica" per ognuno, nel registro;
  - la riga di stato (arturo todo stato), se il nome nuovo non ne ha una più recente;
  - la cartella degli handoff, con le righe "- Nome:" e "- Filone:" che portano il nome vecchio;
  - l'INDEX.md degli handoff, rigenerato da index-rigenera.py;
  - la scheda progetto-<nome>.md della memoria: nome del file, `name:`, il nome vecchio in `alias:`, e i
    link [[progetto-<vecchio>]] delle altre note.
Il nome vecchio entra negli alias della scheda: /inizio col nome vecchio apre il progetto nuovo.

Entrambi i nomi passano dallo slug di /inizio e di arturo todo: "fenice_blu" diventa "fenice-blu".
Un progetto con una cartella sua nella base dei progetti non si rinomina qui: la cartella dà il nome ai todo
nuovi, e va rinominata prima, a sessioni chiuse. La fonte esterna dei task, se c'è, non cambia: lo dice
l'avviso finale. --prova stampa cosa cambierebbe e non scrive niente.
Per tornare indietro: arturo progetti rinomina NUOVO VECCHIO.
Exit: 0 fatto · 2 non si può (cartella, conflitto, niente da rinominare) · 3 uso sbagliato.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import contesto as cx  # noqa: E402
import progetti as pg  # noqa: E402
import todo_store as ts  # noqa: E402

sys.path.insert(0, str(QUI.parent / "hooks"))
from radici import scrivi_atomico as _atomico  # noqa: E402

RIGA_NOME = re.compile(r"^(- Nome:\s*)(\S+)(.*)$")
RIGA_FILONE = re.compile(r"^(- Filone:\s*)(\S+?)(/.*)?$")


def todo_del(vecchio: str, file=None) -> list:
    """I todo del progetto, aperti e chiusi: il campo progetto ha lo slug vecchio."""
    todo, _ = ts.carica(file)
    return [t for t in todo.values() if cx.slug(t.get("progetto") or "") == vecchio]


def cartella_progetto(s: str):
    """La cartella della base dei progetti che ha questo slug, o None."""
    nome = pg.cartelle().get(s)
    return cx.base_progetti() / nome if nome else None


def handoff_nuovi(cartella: Path, vecchio: str, nuovo: str) -> dict:
    """{file: testo nuovo} degli handoff che nominano il progetto vecchio in "- Nome:" o "- Filone:"."""
    fuori = {}
    for f in sorted(cartella.glob("HANDOFF_*.md")):
        try:
            righe = f.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError):
            continue
        cambiate = False
        for i, r in enumerate(righe):
            corpo, fine = r.rstrip("\r\n"), r[len(r.rstrip("\r\n")):]
            for forma in (RIGA_NOME, RIGA_FILONE):
                m = forma.match(corpo)
                if m and cx.slug(m.group(2)) == vecchio:
                    righe[i] = m.group(1) + nuovo + (m.group(3) or "") + fine
                    cambiate = True
                    break
        if cambiate:
            fuori[f] = "".join(righe)
    return fuori


def link_nelle_note(vecchio: str, nuovo: str, salta: Path | None) -> dict:
    """{nota: testo nuovo} delle note della memoria con [[progetto-<vecchio>]] o [[progetto-<vecchio>|...]]."""
    forma = re.compile(r"\[\[progetto-" + re.escape(vecchio) + r"(?=[\]|#])")
    fuori = {}
    for radice in pg.radici_memoria():
        try:
            note = sorted(radice.rglob("*.md"))
        except OSError:
            continue
        for f in note:
            if salta is not None and f == salta:
                continue
            try:
                testo = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if forma.search(testo):
                fuori[f] = forma.sub(f"[[progetto-{nuovo}", testo)
    return fuori


def scheda_nuova(testo: str, vecchio: str, nuovo: str) -> str:
    """Il testo della scheda con `name:` nuovo e il nome vecchio in `alias:` (creato se manca)."""
    righe = testo.splitlines(keepends=True)
    if not righe or righe[0].strip() != "---":
        raise ValueError("la scheda non ha il frontmatter")
    fine = next((i for i, r in enumerate(righe[1:], 1) if r.strip() == "---"), None)
    if fine is None:
        raise ValueError("il frontmatter della scheda non si chiude")
    i_alias = None
    for i in range(1, fine):
        if righe[i].startswith("name:"):
            righe[i] = f"name: progetto-{nuovo}\n"
        elif righe[i].startswith("alias:"):
            i_alias = i
    if i_alias is not None:
        valore = righe[i_alias][len("alias:"):].strip()
        voci = [x.strip().strip("\"'") for x in valore.strip("[]").split(",") if x.strip()]
        voci = [v for v in voci if cx.slug(v) != nuovo]
        if vecchio not in (cx.slug(v) for v in voci):
            voci.append(vecchio)
        righe[i_alias] = f"alias: [{', '.join(voci)}]\n"
    else:
        righe.insert(fine, f"alias: [{vecchio}]\n")
    return "".join(righe)


def index_nuovo(testo: str, vecchio: str, nuovo: str) -> str:
    """Le righe della tabella di INDEX.md del progetto vecchio, col nome nuovo nell'etichetta e nel link."""
    righe = testo.splitlines(keepends=True)
    parola = re.compile(r"(?<![a-z0-9-])" + re.escape(vecchio) + r"(?=$|[\s/—)|])")
    for i, r in enumerate(righe):
        if not r.startswith("|"):
            continue
        celle = r.split("|")
        if len(celle) < 4 or not (parola.search(celle[1]) or f"]({vecchio}/" in celle[2] or celle[2].strip().startswith(f"{vecchio}/")):
            continue
        celle[1] = parola.sub(nuovo, celle[1])
        celle[2] = celle[2].replace(f"]({vecchio}/", f"]({nuovo}/")
        righe[i] = "|".join(celle)
    return "".join(righe)


def scrivi_atomico(f: Path, testo: str) -> None:
    _atomico(f, testo)


def rinomina(vecchio_nome: str, nuovo_nome: str, prova: bool = False) -> int:
    vecchio, nuovo = cx.slug(vecchio_nome), cx.slug(nuovo_nome)
    if not vecchio or not nuovo:
        print("Errore: i due nomi devono avere almeno una lettera o una cifra", file=sys.stderr)
        return 3
    if vecchio == nuovo:
        print(f'Errore: "{vecchio_nome}" e "{nuovo_nome}" danno lo stesso nome, {nuovo}: non c\'è niente da '
              "rinominare", file=sys.stderr)
        return 3
    cartella = cartella_progetto(vecchio)
    if cartella is not None:
        print(f"Errore: {vecchio} ha la cartella {cartella}, che dà il nome ai todo nuovi. Chiudi le sessioni "
              f"su quel progetto, rinomina la cartella in {nuovo}, poi rilancia questo comando.", file=sys.stderr)
        return 2

    todo = todo_del(vecchio)
    stato = ts.stati().get(vecchio)
    stato_nuovo = ts.stati().get(nuovo)
    porta_stato = bool(stato) and (not stato_nuovo or stato["ts"] > stato_nuovo["ts"])
    hd_vecchia, hd_nuova = cx.handoff_dir() / vecchio, cx.handoff_dir() / nuovo
    handoff = sorted(p for p in hd_vecchia.iterdir()) if cx.e_cartella(hd_vecchia) else []
    doppi = [p.name for p in handoff if (hd_nuova / p.name).exists()]
    if doppi:
        print(f"Errore: {hd_nuova} ha già {', '.join(doppi[:3])}: sposta o togli quei file prima di rinominare",
              file=sys.stderr)
        return 2
    scheda = pg.scheda_di(vecchio)
    scheda_dest = scheda.with_name(f"progetto-{nuovo}.md") if scheda else None
    if scheda_dest is not None and scheda_dest.exists():
        print(f"Errore: la scheda {scheda_dest.name} esiste già: unisci le due schede a mano, poi rilancia",
              file=sys.stderr)
        return 2
    if scheda is not None:
        try:
            testo_scheda = scheda_nuova(scheda.read_text(encoding="utf-8"), vecchio, nuovo)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            print(f"Errore: {scheda.name}: {e}", file=sys.stderr)
            return 2
    link = link_nelle_note(vecchio, nuovo, scheda)
    if not (todo or stato or handoff or scheda):
        print(f"Errore: non trovo niente di {vecchio}: né todo, né stato, né handoff, né scheda", file=sys.stderr)
        return 2

    righe = [f"{vecchio} → {nuovo}",
             f"  todo: {len(todo)}",
             f"  riga di stato: {'sì' if porta_stato else 'no'}",
             f"  handoff: {sum(1 for p in handoff if p.name.startswith('HANDOFF_'))} file nella cartella nuova",
             f"  scheda: {scheda.name + ' → ' + scheda_dest.name if scheda else 'nessuna'}",
             f"  link nelle altre note: {len(link)}"]
    if prova:
        print("\n".join(["Prova, niente scritto:"] + righe))
        return 0

    if todo:
        eventi = [ts._evento("modifica", t["uid"], ts.normalizza({"progetto": nuovo})) for t in todo]
        ts._scrivi_molti(eventi, ts.percorso())
        rimasti = todo_del(vecchio)
        if rimasti:
            print(f"Errore: rileggendo il registro {len(rimasti)} todo hanno ancora {vecchio}: mi fermo qui",
                  file=sys.stderr)
            return 2
    if porta_stato:
        ts.scrivi_stato(nuovo, stato["riga"])
    if handoff:
        hd_nuova.mkdir(parents=True, exist_ok=True)
        for p in handoff:
            shutil.move(str(p), str(hd_nuova / p.name))
        try:
            hd_vecchia.rmdir()
        except OSError:
            pass
        for f, testo in handoff_nuovi(hd_nuova, vecchio, nuovo).items():
            scrivi_atomico(f, testo)
    avvisi = []
    index = cx.handoff_dir() / "INDEX.md"
    if index.exists():
        # index-rigenera.py tiene le righe senza file di un progetto che non ha una riga nuova: quelle del nome
        # vecchio restavano come "file non più presente". Prima si riportano al nome nuovo.
        try:
            testo_index = index.read_text(encoding="utf-8")
            nuovo_index = index_nuovo(testo_index, vecchio, nuovo)
            if nuovo_index != testo_index:
                scrivi_atomico(index, nuovo_index)
        except (OSError, UnicodeDecodeError) as e:
            avvisi.append(f"INDEX.md non letto: {e}")
    if handoff or index.exists():
        r = subprocess.run([sys.executable, str(QUI / "index-rigenera.py"), "--scrivi"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            avvisi.append("INDEX.md non rigenerato: " + (r.stderr.strip().splitlines() or ["errore"])[-1])
    if scheda is not None:
        scrivi_atomico(scheda, testo_scheda)
        os.replace(scheda, scheda_dest)
    for f, testo in link.items():
        scrivi_atomico(f, testo)
    if ts.comando_fonte():
        avvisi.append(f"la fonte esterna dei task ha ancora {vecchio}: rinominalo anche lì")

    print("\n".join(["Fatto:"] + righe))
    for a in avvisi:
        print(f"AVVISO: {a}")
    print(f"Il nome vecchio resta valido in /inizio. Per tornare indietro: arturo progetti rinomina {nuovo} {vecchio}")
    return 0


def main(argv: list) -> int:
    prova = "--prova" in argv
    nomi = [a for a in argv if a != "--prova"]
    if len(nomi) != 2 or any(a.startswith("-") for a in nomi):
        print("uso: arturo progetti rinomina VECCHIO NUOVO [--prova]", file=sys.stderr)
        return 3
    return rinomina(nomi[0], nomi[1], prova)


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
