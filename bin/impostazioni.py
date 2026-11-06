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
  arturo impostazioni applica --togli-doppi
                                         toglie prima dai settings della persona gli hook che il plugin
                                         porta già (un clone di prima li aveva lì): senza, scatterebbero
                                         due volte e applica si ferma
  arturo impostazioni adotta [--forza]   scrive il file di blocco col frammento di oggi e non cambia
                                         settings.json: chi passa al plugin con settings suoi già fatti
                                         (la config da cui Arturo è nato) tiene le sue voci, e da lì
                                         riceve solo i cambi futuri di Arturo. --forza sostituisce un
                                         blocco già scritto da un frammento diverso

Nel clone (Arturo dentro ~/.claude) settings.json è già quello di Arturo: non c'è niente da applicare.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

CODICE = Path(__file__).resolve().parent.parent


def orsa() -> Path:
    return radice_orsa()


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


def _registrati() -> set:
    """I file (hooks/x, bin/y) che gli hook del plugin lanciano, da hooks/hooks.json."""
    hooks = _leggi(CODICE / "hooks" / "hooks.json").get("hooks", {})
    file = set()
    for gruppi in hooks.values():
        for gruppo in gruppi:
            for hook in gruppo.get("hooks", []):
                file.update(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/((?:hooks|bin)/[^\s\"']+)", hook.get("command", "")))
    return file


def doppi(settings: dict) -> list:
    """Gli hook dei settings della persona che lanciano un file di Arturo che il plugin registra già.
    Li lascia un clone di prima (settings.json era quello di Arturo): col plugin scatterebbero due volte."""
    registrati = _registrati()
    radici = ["~/.claude", "$HOME/.claude", "${HOME}/.claude", str(orsa()).replace("\\", "/")]
    prefisso = "|".join(re.escape(r) for r in radici)
    trovati = []
    for evento, gruppi in (settings.get("hooks") or {}).items():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            for hook in gruppo.get("hooks", []) if isinstance(gruppo, dict) else []:
                comando = hook.get("command", "") if isinstance(hook, dict) else ""
                usati = re.findall(rf"(?:{prefisso})/((?:hooks|bin)/[^\s\"']+)", comando.replace("\\", "/"))
                if any(u in registrati for u in usati):
                    trovati.append((evento, comando))
    return trovati


def senza_doppi(settings: dict) -> dict:
    """I settings senza gli hook doppi; gruppi ed eventi rimasti vuoti escono anche loro."""
    via = {(e, c) for e, c in doppi(settings)}
    copia = json.loads(json.dumps(settings))
    hooks = copia.get("hooks") or {}
    for evento in list(hooks):
        gruppi = []
        for gruppo in hooks[evento]:
            restanti = [h for h in gruppo.get("hooks", []) if (evento, h.get("command", "")) not in via]
            if restanti:
                gruppi.append(dict(gruppo, hooks=restanti))
        if gruppi:
            hooks[evento] = gruppi
        else:
            del hooks[evento]
    if "hooks" in copia and not hooks:
        del copia["hooks"]
    return copia


def calcola(togli_doppi: bool = False):
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
    nostro = senza_doppi(attuale) if togli_doppi else attuale
    try:
        unito = unisci.unisci(base, nostro, frammento)
    except unisci.Conflitto as errore:
        return attuale, None, frammento, f"{_dove(unisci, base, nostro, frammento) or 'settings.json'}: {errore}"
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


def adotta(forza: bool = False) -> int:
    """Il frammento di oggi diventa la base dell'unione, e settings.json resta com'è.

    Perché esiste (strati F5, 5/11/2026): la config di Federico ha già le sue voci, scelte una per una.
    Con applica la prima unione partirebbe da una base vuota, e ogni voce che il frammento ha diversa
    dai suoi settings sarebbe un conflitto. Con adotta la base è il frammento di oggi: le voci di oggi
    restano sue, e un applica dopo porta solo quello che Arturo cambia da qui in avanti."""
    frammento_file = CODICE / "impostazioni" / "arturo.json"
    if not frammento_file.exists():
        print("IMPOSTAZIONI: Arturo è installato come clone in ~/.claude: settings.json è già il suo.")
        return 0
    try:
        frammento = _leggi(frammento_file)
        blocco_file = orsa() / "data" / "arturo-impostazioni.lock"
        blocco = _leggi(blocco_file)
    except (OSError, ValueError) as e:
        print(f"IMPOSTAZIONI: non leggo il frammento o il blocco ({e}): non scrivo niente.", file=sys.stderr)
        return 1
    if blocco.get("frammento") == frammento:
        print("IMPOSTAZIONI: già adottate, il blocco ha il frammento di oggi.")
        return 0
    if "frammento" in blocco and not forza:
        # Il blocco vecchio è la base dei cambi che Arturo non ha ancora portato: sostituirlo li perde.
        print("IMPOSTAZIONI: il blocco ha già un frammento diverso da quello di oggi: con adotta i cambi di "
              "Arturo fra i due non arriverebbero più. Usa `arturo impostazioni applica`, oppure "
              "`adotta --forza` se vuoi davvero tenere i tuoi settings come sono.", file=sys.stderr)
        return 1
    versione = _leggi(CODICE / ".claude-plugin" / "plugin.json").get("version", "")
    _scrivi(blocco_file, {"versione": versione, "frammento": frammento, "adottato": True})
    print(f"IMPOSTAZIONI: adottate ({versione or 'versione senza numero'}). settings.json non è cambiato; "
          "da qui arrivano solo i cambi futuri di Arturo.")
    return 0


def main(argv: list) -> int:
    azione = argv[0] if argv else "stato"
    if azione in ("-h", "--help", "aiuto"):
        print(__doc__)
        return 0
    if azione not in ("stato", "applica", "adotta"):
        print(f"Comando sconosciuto: {azione}. I comandi sono \"stato\", \"applica\" e \"adotta\".", file=sys.stderr)
        return 2
    if azione == "adotta":
        return adotta("--forza" in argv)
    togli = "--togli-doppi" in argv
    try:
        attuale, unito, frammento, errore = calcola(togli)
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
    restano = doppi(unito)
    if restano:
        print(f"IMPOSTAZIONI: {len(restano)} hook dei tuoi settings lanciano file che il plugin di Arturo "
              "lancia già, e scatterebbero due volte:", file=sys.stderr)
        for evento, comando in restano[:20]:
            print(f"  {evento}: {comando[:100]}", file=sys.stderr)
        print("  Con `arturo impostazioni applica --togli-doppi` li tolgo, con una copia dei settings di prima.",
              file=sys.stderr)
        if azione == "applica" and "--prova" not in argv:
            print("IMPOSTAZIONI: non scrivo niente finché ci sono hook doppi.", file=sys.stderr)
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
