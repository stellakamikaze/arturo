#!/usr/bin/env python3
"""arturo sandbox: la sandbox di Claude Code, che /setup accende sul Mac (19/11/2026; #6322, 21/11/2026).

La sandbox di Claude Code chiude i comandi Bash in un recinto del sistema operativo: un comando, e ogni
programma che lancia, legge e scrive solo dove la config lo permette. Le guardie di Arturo vedono il
comando, non quello che fa uno script lanciato da quel comando: la sandbox copre quel buco. Un plugin
non può accenderla (docs di Claude Code, sandboxing e plugins): la accende /setup sul Mac, o la persona con
questo comando. Su Windows Claude Code non ha la sandbox, e accendi non scrive niente. Dopo spegni resta
data/arturo-sandbox.spenta: lo stato dice "spenta da te", e accendi --setup non la riaccende.

  arturo sandbox stato     accesa o spenta, e le voci che Arturo ha aggiunto
  arturo sandbox accendi   scrive il blocco in ~/.claude/settings.json, con una copia di prima
  arturo sandbox accendi --setup   lo stesso, ma lascia spenta la sandbox che la persona ha spento
  arturo sandbox spegni    toglie solo le voci che accendi ha aggiunto

Cosa scrive accendi, e perché:
- enabled: true. Il resto del blocco senza questa voce non fa niente.
- credentials.files in deny per chiavi SSH, AWS, GPG, gh e Bitwarden CLI: la sandbox di base legge
  quasi tutta la macchina, credenziali comprese ("There is no built-in credential deny list").
- excludedCommands per git in rete, ssh, scp, rsync, gh, gws, bw e claude: su macOS git e ssh su SSH
  falliscono dentro la sandbox, e gh, gws e bw devono leggere le loro credenziali. Girano fuori, come oggi.
- filesystem.allowWrite per data, cache e session-env di ~/.claude: Arturo ci scrive da Bash (todo,
  correzioni, segnalazioni, ripartenza). La voce per data c'è già nel frammento di Arturo.
- network.allowedDomains per il server di Arturo e i registri dei pacchetti. github.com resta fuori:
  la doc avverte che un dominio largo apre una via per portare fuori i dati, e git e gh girano già fuori.
allowUnsandboxedCommands resta al default: un comando bloccato può ripartire fuori, col permesso.

Le voci aggiunte stanno in ~/.claude/data/arturo-sandbox.json: spegni toglie quelle e nient'altro. Il
frammento di Arturo non porta enabled, quindi l'unione a tre vie di `arturo impostazioni` non va in
conflitto con la scelta della persona. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

BLOCCO = {
    "enabled": True,
    "credentials": {"files": [
        {"path": "~/.ssh", "mode": "deny"},
        {"path": "~/.aws", "mode": "deny"},
        {"path": "~/.gnupg", "mode": "deny"},
        {"path": "~/.config/gh", "mode": "deny"},
        {"path": "~/Library/Application Support/Bitwarden CLI", "mode": "deny"},
        {"path": "~/.config/Bitwarden CLI", "mode": "deny"},
    ]},
    "excludedCommands": [
        "git fetch *", "git pull *", "git push *", "git clone *", "ssh *", "scp *", "rsync *",
        "gh *", "gws *", "bw *", "claude *",
    ],
    "filesystem": {"allowWrite": ["~/.claude/data", "~/.claude/cache", "~/.claude/session-env"]},
    "network": {"allowedDomains": [
        "arturo-dati.stellakamikaze.org", "registry.npmjs.org", "pypi.org", "files.pythonhosted.org",
    ]},
}


def _file_settings() -> Path:
    return radice_orsa() / "settings.json"


def _file_registro() -> Path:
    return radice_orsa() / "data" / "arturo-sandbox.json"


def _file_spenta() -> Path:
    """Scritto da spegni: la persona l'ha spenta lei, e /setup non la riaccende (#6322)."""
    return radice_orsa() / "data" / "arturo-sandbox.spenta"


def _leggi(percorso: Path) -> dict:
    if not percorso.exists():
        return {}
    testo = percorso.read_text(encoding="utf-8")
    return json.loads(testo) if testo.strip() else {}


def _scrivi(percorso: Path, dati: dict) -> None:
    """Scrittura atomica, come bin/impostazioni.py: un settings.json a metà spegne le guardie."""
    percorso = Path(os.path.realpath(str(percorso)))
    percorso.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=percorso.parent, prefix=f".{percorso.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(dati, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, percorso)


def _foglie(blocco: dict, via: tuple = ()):
    """(percorso di chiavi, valore) per ogni voce del blocco: le liste danno un elemento per volta."""
    for chiave, valore in blocco.items():
        if isinstance(valore, dict):
            yield from _foglie(valore, via + (chiave,))
        elif isinstance(valore, list):
            for elemento in valore:
                yield via + (chiave,), elemento, True
        else:
            yield via + (chiave,), valore, False


def aggiungi(settings: dict) -> tuple:
    """(settings con il blocco, voci aggiunte). Una voce che la persona ha già non si tocca e non si
    registra: spegni non la toglierà."""
    nuovo = copy.deepcopy(settings)
    sandbox = nuovo.setdefault("sandbox", {})
    aggiunte = []
    for via, valore, in_lista in _foglie(BLOCCO):
        nodo = sandbox
        for chiave in via[:-1]:
            nodo = nodo.setdefault(chiave, {})
        ultima = via[-1]
        if in_lista:
            lista = nodo.setdefault(ultima, [])
            if valore not in lista:
                lista.append(valore)
                aggiunte.append({"via": list(via), "valore": valore, "lista": True})
        elif nodo.get(ultima) != valore:
            voce = {"via": list(via), "valore": valore, "lista": False}
            if ultima in nodo:  # per esempio enabled: false scritto dalla persona: spegni lo rimette
                voce["prima"] = nodo[ultima]
            nodo[ultima] = valore
            aggiunte.append(voce)
    return nuovo, aggiunte


def togli(settings: dict, aggiunte: list) -> dict:
    """Toglie le voci registrate; un dict o una lista rimasti vuoti per questo spariscono."""
    nuovo = copy.deepcopy(settings)
    sandbox = nuovo.get("sandbox")
    if not isinstance(sandbox, dict):
        return nuovo
    for voce in aggiunte:
        catena = [sandbox]
        for chiave in voce["via"][:-1]:
            nodo = catena[-1].get(chiave)
            if not isinstance(nodo, dict):
                break
            catena.append(nodo)
        else:
            ultima = voce["via"][-1]
            nodo = catena[-1]
            if voce["lista"] and isinstance(nodo.get(ultima), list):
                nodo[ultima] = [x for x in nodo[ultima] if x != voce["valore"]]
                if not nodo[ultima]:
                    del nodo[ultima]
            elif not voce["lista"] and nodo.get(ultima) == voce["valore"]:
                if "prima" in voce:
                    nodo[ultima] = voce["prima"]
                else:
                    del nodo[ultima]
            for genitore, chiave in zip(reversed(catena[:-1]), reversed(voce["via"][:-1])):
                if genitore.get(chiave) == {}:
                    del genitore[chiave]
    if nuovo.get("sandbox") == {}:
        del nuovo["sandbox"]
    return nuovo


def accesa(settings: dict) -> bool:
    return bool((settings.get("sandbox") or {}).get("enabled"))


def stato() -> int:
    settings = _leggi(_file_settings())
    registro = _leggi(_file_registro())
    if accesa(settings):
        print("sandbox: accesa")
    elif _file_spenta().exists():
        print("sandbox: spenta da te (arturo sandbox spegni). Per riaccenderla: arturo sandbox accendi")
    else:
        print("sandbox: spenta. Per accenderla: arturo sandbox accendi")
    if registro.get("aggiunte"):
        print(f"voci aggiunte da Arturo: {len(registro['aggiunte'])} (le toglie arturo sandbox spegni)")
    return 0


PER_LA_PERSONA = ("I comandi che Claude lancia girano in un recinto: leggono e scrivono solo dove serve, e le tue "
                  "chiavi (SSH, AWS, GitHub, Bitwarden) restano fuori. Git, ssh e gh girano come prima. Vale dalla "
                  "prossima sessione; se un programma non funziona, chiedi di spegnerla.")


def accendi(da_setup: bool = False) -> int:
    """Con da_setup (/setup, FASE 8d) lascia spenta la sandbox che la persona ha spento con spegni."""
    if da_setup and _file_spenta().exists():
        print("sandbox: spenta da te con arturo sandbox spegni; /setup non la riaccende")
        return 0
    if sys.platform == "win32":
        # Claude Code ha la sandbox su macOS, Linux e WSL2, non su Windows (docs di Claude Code, sandboxing):
        # le voci scritte qui non farebbero niente e direbbero alla persona che è protetta (#6322).
        print("sandbox: su Windows Claude Code non ha la sandbox (solo macOS, Linux e WSL2); "
              "le guardie di Arturo restano la protezione. Niente scritto.")
        return 0
    file_settings = _file_settings()
    settings = _leggi(file_settings)
    nuovo, aggiunte = aggiungi(settings)
    if _file_spenta().exists():
        _file_spenta().unlink()
    if not aggiunte:
        print("sandbox: già accesa, niente da aggiungere")
        return 0
    if file_settings.exists():
        shutil.copy2(file_settings, file_settings.with_name("settings.json.prima-della-sandbox"))
    registro = _leggi(_file_registro())
    _scrivi(_file_registro(), {"aggiunte": (registro.get("aggiunte") or []) + aggiunte})
    _scrivi(file_settings, nuovo)
    print(f"sandbox: accesa, {len(aggiunte)} voci aggiunte in {file_settings}")
    print("vale dalla prossima sessione di Claude Code; copia di prima: settings.json.prima-della-sandbox")
    if da_setup:
        print(f"per la persona: {PER_LA_PERSONA}")
    return 0


def spegni() -> int:
    registro = _leggi(_file_registro())
    aggiunte = registro.get("aggiunte") or []
    if not aggiunte:
        print("sandbox: Arturo non ha voci da togliere")
        return 0
    file_settings = _file_settings()
    _scrivi(file_settings, togli(_leggi(file_settings), aggiunte))
    _file_registro().unlink()
    _file_spenta().write_text("spenta da arturo sandbox spegni\n", encoding="utf-8")
    print(f"sandbox: spenta, tolte {len(aggiunte)} voci aggiunte da Arturo; il resto di settings.json è com'era")
    return 0


def main(argv: list) -> int:
    azione = argv[0] if argv else "stato"
    azioni = {"stato": stato, "accendi": lambda: accendi("--setup" in argv[1:]), "spegni": spegni}
    if azione not in azioni:
        print(f"arturo sandbox: azione sconosciuta {azione!r} (stato, accendi, spegni)", file=sys.stderr)
        return 2
    try:
        return azioni[azione]()
    except (OSError, ValueError) as errore:
        print(f"arturo sandbox: {errore}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
