#!/usr/bin/env python3
"""arturo ripartenza scrivi: la ripartenza di /inizio come dati, per la checklist di Volta (17/11/2026, #5910).

/inizio stampa la ripartenza nel terminale e poi passa lo stesso elenco a questo comando su stdin. Il comando
lo scrive in <config>/cache/ripartenza/<sessione>.json; la sonda di Volta (volta_sonda.py) lo legge e la vista
Checklist lo mostra, con una casella e una nota per riga. La scelta della persona torna alla sessione come
messaggio ("Lavora su 2 5. Note: 7: ..."), e /inizio lo legge nella FASE 6. Senza Volta il file non lo legge
nessuno e si cancella da solo dopo due giorni: è l'età oltre cui Volta lo ignora.

Ingresso (stdin, JSON):
  {"progetto": "il-libro", "titolo": "Il libro · branch main · ultimo handoff 14/10",
   "filoni": [{"nome": "Capitolo tre", "voci": [{"n": 1, "id": 5, "testo": "Mandare la bozza all'editor",
                                               "marca": "Preparo io, poi tu: invio a terzi", "sotto": ""}]}],
   "partenza": {"n": 1, "motivo": "sblocca la rilettura"}}
Uscita: il file, con versione, sid e quando aggiunti. `n` è il numero che la persona vede nel terminale.
Tetti: FILONI filoni, VOCI voci in tutto, TESTO caratteri per campo. Un campo sconosciuto si scarta.
Le voci oltre i tetti non entrano, e l'uscita dice quante sono: VOCI è 300 dal 25/11/2026 (#6687), perché a
60 su 85 task di un progetto 25 non arrivavano alla checklist.

Esce 2 se lo schema è rotto (lo dice su stderr, così Claude corregge). Senza CLAUDE_CODE_SESSION_ID esce 0 e
non scrive: la ripartenza fuori da una sessione non ha una checklist. Senza la cartella di Volta
(~/.config/herdr-app) esce 0 e non scrive: la checklist la legge solo Volta, e chi non la usa non deve
trovarsi file di Volta (22/11/2026, rilievo A9). Si spegne con ARTURO_RIPARTENZA=0.
Solo libreria standard, Python 3.8+. Banco: tests/test_ripartenza_2026_11_17.py.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

VERSIONE = 1
FILONI = 12
VOCI = 300
TESTO = 300
VECCHIA = 2 * 86400  # secondi: oltre questa età Volta non mostra la ripartenza, e il comando la cancella
SID = re.compile(r"^[A-Za-z0-9-]{8,64}$")
USO = ('arturo ripartenza: un comando, "arturo ripartenza scrivi", con la ripartenza in JSON su stdin '
       "(lo lancia /inizio, per la checklist di Volta)")


def cartella() -> Path:
    return radice_orsa() / "cache" / "ripartenza"


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = f.with_name(f"{f.stem}.{os.getpid()}.tmp")
    provvisorio.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    os.replace(str(provvisorio), str(f))


def pulisci_vecchie(dove: Path, adesso: float) -> None:
    """Le ripartenze di sessioni passate: Volta non le mostra più, e senza Volta non le legge nessuno."""
    try:
        for f in dove.glob("*.json"):
            try:
                if adesso - f.stat().st_mtime > VECCHIA:
                    f.unlink()
            except OSError:
                pass
    except OSError:
        pass


def corto(v, campo: str) -> str:
    if v is None:
        return ""
    if isinstance(v, bool) or not isinstance(v, (str, int)):
        raise ValueError(f"{campo}: serve un testo")
    return " ".join(str(v).split())[:TESTO]


def numero(v, campo: str, nullo: bool = False):
    if v is None and nullo:
        return None
    if isinstance(v, str) and v.lstrip("#").isdigit():
        return int(v.lstrip("#"))
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{campo}: serve un numero")
    return v


def pulisci(grezzo) -> tuple:
    """Lo schema controllato e tagliato ai tetti, con il numero di voci rimaste fuori dai tetti.
    ValueError dice il campo rotto."""
    if not isinstance(grezzo, dict):
        raise ValueError("serve un oggetto JSON")
    filoni = grezzo.get("filoni")
    if not isinstance(filoni, list) or not filoni:
        raise ValueError("filoni: serve un elenco non vuoto")
    fuori, contate, visti = [], 0, set()
    tagliate = sum(len(f["voci"]) for f in filoni[FILONI:] if isinstance(f, dict) and isinstance(f.get("voci"), list))
    for i, f in enumerate(filoni[:FILONI]):
        if not isinstance(f, dict) or not isinstance(f.get("voci"), list):
            raise ValueError(f"filoni[{i}]: serve un oggetto con voci")
        voci = []
        for j, v in enumerate(f["voci"]):
            if contate >= VOCI:
                tagliate += len(f["voci"]) - j
                break
            if not isinstance(v, dict):
                raise ValueError(f"filoni[{i}].voci[{j}]: serve un oggetto")
            n = numero(v.get("n"), f"filoni[{i}].voci[{j}].n")
            if n in visti:
                raise ValueError(f"filoni[{i}].voci[{j}].n: il numero {n} c'è già")
            testo = corto(v.get("testo"), f"filoni[{i}].voci[{j}].testo")
            if not testo:
                raise ValueError(f"filoni[{i}].voci[{j}].testo: vuoto")
            visti.add(n)
            contate += 1
            voci.append({"n": n, "id": numero(v.get("id"), f"filoni[{i}].voci[{j}].id", nullo=True),
                         "testo": testo, "marca": corto(v.get("marca"), "marca"),
                         "sotto": corto(v.get("sotto"), "sotto")})
        if voci:
            fuori.append({"nome": corto(f.get("nome"), f"filoni[{i}].nome"), "voci": voci})
    if not fuori:
        raise ValueError("nessuna voce")
    dati = {"progetto": corto(grezzo.get("progetto"), "progetto"),
            "titolo": corto(grezzo.get("titolo"), "titolo"), "filoni": fuori}
    p = grezzo.get("partenza")
    if isinstance(p, dict) and p.get("n") is not None:
        dati["partenza"] = {"n": numero(p.get("n"), "partenza.n"), "motivo": corto(p.get("motivo"), "partenza.motivo")}
    return dati, tagliate


def volta_presente() -> bool:
    """Volta tiene la sua config in ~/.config/herdr-app, sul Mac e su Windows: senza, nessuno legge la checklist."""
    return (Path.home() / ".config" / "herdr-app").is_dir()


def main(argv: list) -> int:
    if argv[:1] != ["scrivi"] or len(argv) > 1:
        print(USO, file=sys.stderr)
        return 2
    if os.environ.get("ARTURO_RIPARTENZA") == "0":
        return 0
    try:
        dati, tagliate = pulisci(json.loads(sys.stdin.read()))
    except (ValueError, json.JSONDecodeError) as e:
        print(f"arturo ripartenza: schema rotto: {e}", file=sys.stderr)
        return 2
    if not volta_presente():
        print("arturo ripartenza: Volta non c'è, niente checklist")
        return 0
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not SID.match(sid):
        print("arturo ripartenza: nessuna sessione, niente checklist")
        return 0
    adesso = time.time()
    dove = cartella()
    pulisci_vecchie(dove, adesso)
    f = dove / f"{sid}.json"
    scrivi(f, dict(versione=VERSIONE, sid=sid, quando=adesso, **dati))
    voci = sum(len(x["voci"]) for x in dati["filoni"])
    print(f"arturo ripartenza: {voci} voci per la checklist di Volta")
    if tagliate:
        print(f"arturo ripartenza: {tagliate} voci oltre il tetto ({FILONI} filoni, {VOCI} voci): non entrano nella checklist")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
