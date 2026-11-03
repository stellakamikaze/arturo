#!/usr/bin/env python3
"""arturo impostazioni: le voci di settings.json che il plugin di Arturo non può portare (docs/strati.md).

Un plugin porta hook, skill e stili, ma non permessi, autoMode, env, statusLine e lo stile di base.
Queste voci stanno nel frammento `impostazioni/arturo.json` del plugin, e questo comando le unisce
in ~/.claude/settings.json, il file della persona.

Il file di blocco ~/.claude/data/arturo-impostazioni.lock tiene il frammento applicato l'ultima volta.
L'unione è a tre vie, con le regole di unisci-settings.py: base = il blocco, nostro = settings.json
della persona, loro = il frammento nuovo. Così Arturo cambia solo le voci che la persona ha lasciato
com'erano, e una voce cambiata da tutte e due le parti non si scrive: si segnala e decide la persona.

  arturo impostazioni stato              applicato o no, e cosa cambierebbe
  arturo impostazioni applica [--prova]  unisce il frammento; --prova mostra senza scrivere

Nel clone (Arturo dentro ~/.claude) settings.json è già quello di Arturo: non c'è niente da applicare.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

CODICE = Path(__file__).resolve().parent.parent


def orsa() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def _unione():
    spec = importlib.util.spec_from_file_location("unisci_settings", CODICE / "bin" / "unisci-settings.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _leggi(percorso: Path) -> dict:
    if not percorso.exists():
        return {}
    testo = percorso.read_text(encoding="utf-8")
    return json.loads(testo) if testo.strip() else {}


def _scrivi(percorso: Path, dati: dict) -> None:
    """Scrittura atomica: un settings.json a metà spegne guardie e permessi alla sessione dopo."""
    percorso.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=percorso.parent, prefix=f".{percorso.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(dati, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, percorso)


def _differenze(prima, dopo, via="") -> list:
    if isinstance(prima, dict) and isinstance(dopo, dict):
        righe = []
        for k in list(dopo) + [k for k in prima if k not in dopo]:
            righe += _differenze(prima.get(k), dopo.get(k), f"{via}.{k}" if via else k)
        return righe
    if prima == dopo:
        return []
    if isinstance(prima, list) and isinstance(dopo, list):
        aggiunte = [x for x in dopo if x not in prima]
        tolte = [x for x in prima if x not in dopo]
        return [f"{via}: +{json.dumps(x, ensure_ascii=False)[:90]}" for x in aggiunte] + \
               [f"{via}: -{json.dumps(x, ensure_ascii=False)[:90]}" for x in tolte]
    return [f"{via}: {json.dumps(prima, ensure_ascii=False)[:60]} -> {json.dumps(dopo, ensure_ascii=False)[:60]}"]


def calcola():
    """(settings attuale, settings unito, frammento, errore) per la radice dell'Orsa."""
    frammento_file = CODICE / "impostazioni" / "arturo.json"
    if not frammento_file.exists():
        return None, None, None, "clone"
    settings_file = orsa() / "settings.json"
    blocco = _leggi(orsa() / "data" / "arturo-impostazioni.lock")
    frammento = _leggi(frammento_file)
    attuale = _leggi(settings_file)
    unisci = _unione()
    base = blocco.get("frammento", unisci.MANCA)
    try:
        unito = unisci.unisci(base, attuale, frammento)
    except unisci.Conflitto as errore:
        return attuale, None, frammento, f"{_dove(unisci, base, attuale, frammento) or 'settings.json'}: {errore}"
    return attuale, unito, frammento, None


def _dove(unisci, base, nostro, loro, via=""):
    """La voce più interna in cui l'unione si ferma, per dirla alla persona."""
    if not (isinstance(nostro, dict) and isinstance(loro, dict)):
        return via
    b = base if isinstance(base, dict) else {}
    for k in loro:
        try:
            unisci.unisci(b.get(k, unisci.MANCA), nostro.get(k, unisci.MANCA), loro[k])
        except unisci.Conflitto:
            return _dove(unisci, b.get(k, unisci.MANCA), nostro.get(k), loro[k], f"{via}.{k}" if via else k)
    return via


def main(argv: list) -> int:
    azione = argv[0] if argv else "stato"
    if azione in ("-h", "--help", "aiuto"):
        print(__doc__)
        return 0
    if azione not in ("stato", "applica"):
        print(f"Comando sconosciuto: {azione}. I comandi sono \"stato\" e \"applica\".", file=sys.stderr)
        return 2
    try:
        attuale, unito, frammento, errore = calcola()
    except (OSError, ValueError) as e:
        print(f"IMPOSTAZIONI: non leggo i settings ({e}): non scrivo niente.", file=sys.stderr)
        return 1
    if errore == "clone":
        print("IMPOSTAZIONI: Arturo è installato come clone in ~/.claude: settings.json è già il suo.")
        return 0
    if errore:
        print(f"IMPOSTAZIONI: una voce è cambiata sia da te sia da Arturo ({errore}). Non scrivo niente: "
              "decidi con Claude quale tenere, poi rilancia.", file=sys.stderr)
        return 1
    righe = _differenze(attuale, unito)
    if not righe:
        print("IMPOSTAZIONI: già applicate, niente da cambiare.")
    else:
        prova = azione == "stato" or "--prova" in argv
        print(f"IMPOSTAZIONI: {len(righe)} voci {'da cambiare' if prova else 'cambiate'}:")
        for r in righe[:40]:
            print("  " + r)
    if azione == "stato" or "--prova" in argv:
        return 0
    settings_file = orsa() / "settings.json"
    copia = orsa() / "settings.json.prima-di-arturo"
    if righe and settings_file.exists() and not copia.exists():
        shutil.copy2(settings_file, copia)
    if righe:
        _scrivi(settings_file, unito)
    versione = _leggi(CODICE / ".claude-plugin" / "plugin.json").get("version", "")
    _scrivi(orsa() / "data" / "arturo-impostazioni.lock", {"versione": versione, "frammento": frammento})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
