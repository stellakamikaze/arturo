"""arturo correzione: le correzioni della persona, scritte una volta e valide per tutta la sessione.

Nasce dal Computer Club N.3 (27/10/2026, [0:01:09]): "tre volte di fila ho fatto un errore, tu me
l'hai fatto notare tutte e tre le volte". Detta in chat, una correzione resta lontana nel contesto
dopo qualche giro, sparisce con una compattazione e non arriva mai ai subagenti. Scritta qui, torna
davanti a Claude a ogni messaggio (inject-now.sh), dopo una compattazione (session-start.sh) e
all'avvio di un subagente (subagent-memory-context.py).

Cosa è una correzione lo decide Claude: questo modulo conserva e ristampa, non riconosce niente.

  aggiungi "TESTO"   scrive la correzione, in una riga: la regola da seguire, non la cronaca. Se la
                     sessione ha aperto una skill della persona, la voce porta il suo nome (campo
                     `skill`, scritto da hooks/estensione-skill.py in <sessione>.skill): /fine sa
                     in quale skill portarla (21/11/2026, #6277)
  elenco             le correzioni di questa sessione, numerate (anche senza argomenti)
  togli N            toglie la correzione N, se la persona la ritira o non vale più
  blocco             per gli hook: legge il JSON dell'hook su stdin e stampa il blocco, o niente

La sessione è quella di CLAUDE_CODE_SESSION_ID, che Claude Code passa ai comandi della sessione e
che gli hook ricevono come session_id. Un file per sessione in ~/.claude/data/correzioni/, tolto
dopo 14 giorni. Sta in data/ perché il sandbox dei comandi lascia scrivere solo lì (segnalazione n. 88);
fino al 18/11/2026 stava in cache/correzioni/, che leggi() legge ancora per la sessione in corso: /clear apre una sessione nuova e parte senza correzioni. Una correzione che vale
sempre va nel CLAUDE.md o in memoria con /fine (FASE 8). Solo libreria standard, Python 3.8 o
successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

MASSIMO = 20         # correzioni tenute per sessione: oltre, esce la più vecchia
LUNGHEZZA = 300      # caratteri di una correzione
GIORNI = 14          # dopo, il file di una sessione si toglie
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
NOME_SKILL = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

AIUTO = """arturo correzione: le correzioni della persona, valide per tutta la sessione di Claude Code.

  arturo correzione aggiungi "TESTO"   scrive la correzione in una riga: la regola, non la cronaca
  arturo correzione elenco             le correzioni di questa sessione, numerate
  arturo correzione togli N            toglie la correzione N
  arturo correzione blocco             per gli hook: JSON dell'hook su stdin, stampa il blocco"""


def cartella() -> Path:
    return Path(os.environ.get("ARTURO_RADICE") or radice_orsa()) / "data" / "correzioni"


def cartella_vecchia() -> Path:
    # Fino al 18/11/2026 (segnalazione n. 88): fuori dal sandbox dei comandi. Si legge, non si scrive più.
    return Path(os.environ.get("ARTURO_RADICE") or radice_orsa()) / "cache" / "correzioni"


def file_di(sessione: str) -> Path:
    return cartella() / f"{sessione}.json"


def leggi(sessione: str) -> list:
    f = file_di(sessione)
    if not f.exists():
        f = cartella_vecchia() / f"{sessione}.json"
    try:
        voci = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [v for v in voci if isinstance(v, dict) and isinstance(v.get("testo"), str)] \
        if isinstance(voci, list) else []


def skill_in_uso(sessione: str) -> str:
    """L'ultima skill della persona aperta nella sessione, o "". La scrive hooks/estensione-skill.py."""
    try:
        nome = (cartella() / f"{sessione}.skill").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return nome if NOME_SKILL.match(nome) else ""


def skill_di(voce: dict) -> str:
    nome = voce.get("skill")
    return nome if isinstance(nome, str) and NOME_SKILL.match(nome) else ""


def riga(numero: int, voce: dict) -> str:
    """Una correzione numerata, con la skill a cui appartiene se c'è."""
    return f"{numero}. {voce['testo']}" + (f" [skill: {skill_di(voce)}]" if skill_di(voce) else "")


def scrivi(sessione: str, voci: list) -> None:
    f = file_di(sessione)
    f.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = f.with_suffix(".tmp")
    provvisorio.write_text(json.dumps(voci, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(provvisorio, f)
    limite = time.time() - GIORNI * 86400
    for vecchio in list(f.parent.glob("*.json")) + list(f.parent.glob("*.skill")):
        try:
            if vecchio != f and vecchio.stat().st_mtime < limite:
                vecchio.unlink()
        except OSError:
            pass


def blocco(voci: list) -> str:
    if not voci:
        return ""
    righe = [riga(i, v) for i, v in enumerate(voci, 1)]
    return ("CORREZIONI DI QUESTA SESSIONE (la persona le ha già dette: valgono fino alla fine, "
            "controllale prima di rispondere e prima di ogni azione che le tocca):\n" + "\n".join(righe))


def sessione_corrente() -> str:
    sessione = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not ID.match(sessione):
        raise SystemExit("Errore: manca CLAUDE_CODE_SESSION_ID. Il comando vale dentro una sessione di "
                         "Claude Code, che lo passa da sola ai suoi comandi.")
    return sessione


def main(argv: list) -> int:
    verbo = argv[0] if argv else "elenco"
    if verbo in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    if verbo == "blocco":
        try:
            dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return 0
        sessione = str(dati.get("session_id") or "") if isinstance(dati, dict) else ""
        if ID.match(sessione):
            testo = blocco(leggi(sessione))
            if testo:
                print(testo)
        return 0
    sessione = sessione_corrente()
    voci = leggi(sessione)
    if verbo == "elenco":
        print(blocco(voci) or "Nessuna correzione in questa sessione.")
        return 0
    if verbo == "aggiungi":
        testo = " ".join(" ".join(argv[1:]).split())
        if not testo:
            print('Errore: scrivi la correzione, per esempio arturo correzione aggiungi "Le date in forma 4/11, '
                  'mai 04/11".', file=sys.stderr)
            return 2
        if len(testo) > LUNGHEZZA:
            print(f"Errore: la correzione supera {LUNGHEZZA} caratteri. Scrivi la regola in una riga.",
                  file=sys.stderr)
            return 2
        if any(v["testo"].casefold() == testo.casefold() for v in voci):
            print("Già scritta: " + testo)
            return 0
        voce = {"testo": testo, "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
        skill = skill_in_uso(sessione)
        if skill:
            voce["skill"] = skill
        voci.append(voce)
        uscita = voci[:-MASSIMO] if len(voci) > MASSIMO else []
        scrivi(sessione, voci[-MASSIMO:])
        print(f"Scritta, vale per tutta la sessione: {testo}" + (f" [skill: {skill}]" if skill else ""))
        for v in uscita:
            print(f"Tolta la più vecchia (si tengono {MASSIMO} correzioni): {v['testo']}")
        return 0
    if verbo == "togli":
        try:
            n = int(argv[1])
            tolta = voci.pop(n - 1) if n >= 1 else None
        except (IndexError, ValueError):
            tolta = None
        if tolta is None:
            print(f"Errore: scrivi il numero di una correzione, da 1 a {len(voci)}." if voci
                  else "Errore: nessuna correzione in questa sessione.", file=sys.stderr)
            return 2
        scrivi(sessione, voci)
        print("Tolta: " + tolta["testo"])
        return 0
    print(f"Comando sconosciuto: {verbo}. I comandi sono aggiungi, elenco, togli e blocco.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
