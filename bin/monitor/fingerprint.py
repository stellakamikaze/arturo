#!/usr/bin/env python3
"""Fingerprint di /monitor: valida la stringa canonica e calcola l'hash (lotto 2, 3/10/2026).

La tabella delle forme ammesse e' la stessa di SKILL.md 2.2: un fingerprint vale solo se
nasce da ID stabili. Una stringa che non combacia con nessuna forma si rifiuta, invece di
produrre un hash che la run dopo non ritrova (deriva di N su Meet, testo libero sul filo
Francesca). Hash: i primi 8 caratteri dell'md5, come `echo -n S | md5 -q | cut -c1-8`.

  fingerprint.py "email:1a0f7a23d0379a35"      -> stampa `hash<TAB>stringa`, exit 0
  fingerprint.py "testo libero"                -> motivo su stderr, exit 2
  fingerprint.py --jsonl IN OUT                -> aggiunge "hash" a ogni riga con fp_canonico
"""
import hashlib
import json
import re
import sys

DATA = r"\d{4}-\d{2}-\d{2}"
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
THREAD = r"[0-9a-f]{16}"
SUFF = r"(?::[a-z0-9]{1,3})?"          # disambiguazione di 2.2: `:b`, `:5b`
DOC = r"[A-Za-z0-9_-]{20,}"

FORME = [
    ("email", rf"email:{THREAD}{SUFF}"),
    ("slack", rf"slack:[CDG][A-Z0-9]{{6,}}:\d{{10}}\.\d{{6}}{SUFF}"),
    ("wa", rf"wa:[^:\s]+@(?:g\.us|s\.whatsapp\.net|lid):{DATA}T\d{{2}}:\d{{2}}:\d{{2}}(?:[+-]\d{{2}}:\d{{2}})?{SUFF}"),
    ("wa (vecchia, fino al 3/10/2026)", rf"wa:[^:\s]+@(?:g\.us|s\.whatsapp\.net|lid):{DATA}:\d+{SUFF}"),
    ("meet", rf"meet:{DOC}:(?:\d+[a-z]?|\d{{1,2}}:\d{{2}}(?::\d{{2}})?){SUFF}"),
    # come "meet": indice Fireflies oppure marcatore hh:mm:ss, che meet.prompt.md chiede (3/10/2026)
    ("meet-eco", rf"meet-eco:{DOC}:(?:\d+[a-z]?|\d{{1,2}}:\d{{2}}(?::\d{{2}})?){SUFF}"),
    # call registrata da Cornetta: nome del file e marcatore mm:ss (26/10/2026). Il suffisso di
    # 2.2 contiene sempre una lettera (`:b`, `:5b`): un `:12` resterebbe ambiguo col marcatore.
    # Impegno economico: `cornetta-eco:` con la stessa forma (#3965, 2/11/2026).
    ("cornetta", r"cornetta:[^:\n]+:\d{1,3}:\d{2}(?::\d{0,2}[a-z])?"),
    ("cornetta-eco", r"cornetta-eco:[^:\n]+:\d{1,3}:\d{2}(?::\d{0,2}[a-z])?"),
    ("pec", r"pec:<[^<>\s]+@[^<>\s]+>"),
    ("promessa", rf"promessa:{THREAD}"),
    ("manuale", rf"manuale:{DATA}:\S.*"),
    ("sollecito", rf"sollecito:(?:task\d+|{UUID}|\d+):{DATA}"),
    ("crm", rf"crm:\d+:{DATA}"),
    ("eccezione", rf"eccezione:task\d+:{DATA}"),
    ("chiusura45", rf"chiusura45:(?:task\d+|\d+):{DATA}"),
    ("fisc:emettere", r"fisc:emettere:[a-z0-9-]+:\d{4}-\d{2}"),
    ("fisc:pagare", rf"fisc:pagare:{UUID}:{DATA}"),
    ("fisc:f24", rf"fisc:f24:[a-z0-9-]+:{DATA}"),
    ("fisc:francesca", rf"fisc:francesca:{THREAD}"),
    ("fisc:persa", rf"fisc:persa:{THREAD}"),
    ("fisc:anomalia", rf"fisc:anomalia:{UUID}"),
]
_RE = [(nome, re.compile(f"^{rx}$")) for nome, rx in FORME]


def valida(s):
    """(True, forma) se la stringa combacia con una forma di 2.2, altrimenti (False, motivo)."""
    s = (s or "").strip()
    if not s:
        return False, "stringa vuota"
    for nome, rx in _RE:
        if rx.match(s):
            return True, nome
    pref = s.split(":", 1)[0]
    noti = sorted({n.split(" ")[0].split(":")[0] for n, _ in FORME})
    if pref not in noti:
        return False, f"prefisso \"{pref}\" sconosciuto (ammessi: {', '.join(noti)})"
    return False, f'forma "{pref}" con campi non validi: servono ID stabili (SKILL.md 2.2)'


def hash_di(s):
    return hashlib.md5(s.strip().encode("utf-8")).hexdigest()[:8]


def main(argv):
    if len(argv) == 4 and argv[1] == "--jsonl":
        ok = scartate = 0
        with open(argv[2], encoding="utf-8") as fin, open(argv[3], "w", encoding="utf-8") as fout:
            for n, riga in enumerate(fin, 1):
                if not riga.strip():
                    continue
                item = json.loads(riga)
                fp = item.get("fp_canonico")
                if fp is not None:
                    valido, motivo = valida(fp)
                    if not valido:
                        print(f"riga {n}: {motivo}: {fp}", file=sys.stderr)
                        scartate += 1
                        continue
                    item["hash"] = hash_di(fp)
                    ok += 1
                fout.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"# fingerprint: {ok} validi, {scartate} scartati", file=sys.stderr)
        return 1 if scartate else 0
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    valido, motivo = valida(argv[1])
    if not valido:
        print(f"ERROR: {motivo}", file=sys.stderr)
        return 2
    print(f"{hash_di(argv[1])}\t{argv[1].strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
