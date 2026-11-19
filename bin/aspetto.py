"""arturo aspetto: i colori e i pezzi della barra che hai scelto tu, in ~/.claude/personale/aspetto.json.

  mostra [dafare|scheda|barra]   i valori validi in JSON (il pannello /dafare legge i suoi colori da qui)
  controlla                      gli errori del file, uno per riga; esce 1 se ce ne sono
  esempio                        un file d'esempio da copiare, con tutti i nomi che valgono

Il file sta fuori da git: gli aggiornamenti di Arturo non lo toccano (proposta n. 73, 18/11/2026). Un valore
sbagliato resta fuori e vale quello di Arturo. La spiegazione completa sta in docs/strati.md, "Cambiare l'aspetto".
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
import aspetto_valori as aspetto  # noqa: E402

ESEMPIO = {
    "dafare": {"colori": {"tela": "#1e1e1e", "inchiostro": "#f0f0f0"}},
    "scheda": {"colori": {"chiusa": [135, 95, 215]}, "decac": {"chiusa": 5}},
    "barra": {"spenti": ["aggiornamento"], "aggiunta": "barra.js"},
}


def controlla() -> int:
    f = aspetto.file_aspetto()
    validi, errori = aspetto.leggi(f)
    aggiunta = (validi.get("barra") or {}).get("aggiunta")
    if aggiunta and not (f.parent / aggiunta).is_file():
        errori.append(f"barra.aggiunta: manca il file {f.parent / aggiunta}")
    if not f.exists():
        print(f"Nessun file dell'aspetto: Arturo usa i suoi colori. Per cambiarli crea {f} (arturo aspetto esempio).")
        return 0
    for e in errori:
        print(f"ERRORE {e}")
    if not errori:
        print(f"{f}: tutto valido.")
    return 1 if errori else 0


def main(argv: list) -> int:
    comando = argv[0] if argv else "controlla"
    if comando == "mostra":
        validi, _ = aspetto.leggi()
        sezione = argv[1] if len(argv) > 1 else ""
        if sezione and sezione not in ("dafare", "scheda", "barra"):
            print("Uso: arturo aspetto mostra [dafare|scheda|barra]", file=sys.stderr)
            return 2
        print(json.dumps(validi.get(sezione, {}) if sezione else validi, ensure_ascii=False))
        return 0
    if comando == "controlla":
        return controlla()
    if comando == "esempio":
        print(json.dumps(ESEMPIO, ensure_ascii=False, indent=2))
        return 0
    print(__doc__.strip())
    return 0 if comando in ("aiuto", "-h", "--help") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
