#!/usr/bin/env python3
"""La deriva: quanto la config della persona si è allontanata da quella di Arturo.

Arturo convive con la config personale: la persona aggiunge le sue regole, i suoi comandi, i suoi
permessi. Il guaio arriva quando la distanza rompe Arturo: un hook di Arturo tolto o spento, un
file di Arturo modificato che manda in conflitto ogni aggiornamento, una config rotta. Questo
controllo misura tre cose rispetto al punto in cui la config si è staccata da Arturo (merge-base
con upstream/main se esiste, altrimenti origin/main):

  - file di Arturo modificati in locale (settings.json escluso: le sue modifiche sono normali, e
    gli hook li guarda il secondo controllo);
  - hook che il settings.json di Arturo dichiara e che mancano, o `disableAllHooks`;
  - config rotta, dalle categorie di controlla-config.py.

Stampa una riga DERIVA: solo se c'è qualcosa da fare. Registra nella telemetria l'elenco corrente
solo quando cambia (evento `deriva`, prima un `insieme:<n>`), e la config rotta una volta al giorno
(evento `config`), con l'invio subito. Dei file esce solo il percorso dentro Arturo, che è pubblico.
Non ferma mai l'avvio: ogni errore tace.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MASSIMO = 50
RADICI = ("agents", "bin", "commands", "docs", "hooks", "output-styles", "server", "shared", "skills", "templates",
          "tests", "tools", ".github")
# Solo il punto va protetto: il trattino fuori da [] non ha un senso speciale, e così la regex resta
# uguale, lettera per lettera, a quelle di bin/telemetria.py e server/logica.js.
FILE = re.compile(r"^(?!.*\.\.)((" + "|".join(r.replace(".", r"\.") for r in RADICI) + r")/[A-Za-z0-9_./-]{1,70}|[A-Za-z0-9_.-]{1,40})$")
HOOK = re.compile(r"hooks/([a-z0-9_.-]{1,60})")


def git(radice: Path, *argomenti) -> tuple:
    try:
        r = subprocess.run(["git", "-C", str(radice), *argomenti], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout


def riferimento(radice: Path):
    for ref in ("upstream/main", "origin/main"):
        if git(radice, "rev-parse", "--verify", "--quiet", ref)[0] == 0:
            return ref
    return None


def hook_dichiarati(impostazioni: dict) -> set:
    nomi = set()
    for gruppi in (impostazioni.get("hooks") or {}).values():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            for h in (gruppo.get("hooks") or []) if isinstance(gruppo, dict) else []:
                if isinstance(h, dict):
                    nomi.update(HOOK.findall(str(h.get("command", ""))))
    return nomi


def leggi_json(percorso: Path) -> dict:
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
        return dati if isinstance(dati, dict) else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def categorie_config(radice: Path) -> list:
    try:
        spec = importlib.util.spec_from_file_location("controlla_config", Path(__file__).with_name("controlla-config.py"))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        trovati = modulo.problemi(str(radice))
    except Exception:  # noqa: BLE001
        return []
    fuori = set()
    for riga in trovati:
        if riga.startswith("settings"):
            fuori.add("rotta-settings")
        elif riga.startswith("hook mancante"):
            fuori.add("rotta-hook")
        elif "lasciato a meta'" in riga:
            fuori.add("rotta-rebase")
        else:
            fuori.add("rotta-conflitto")
    return sorted(fuori)


def rileva(radice: Path) -> dict:
    """{'file': [...], 'hook': [...], 'config': [...]}: vuoto dove non si può misurare."""
    esito = {"file": [], "hook": [], "config": categorie_config(radice)}
    ref = riferimento(radice)
    if not ref:
        return esito
    rc, base = git(radice, "merge-base", "HEAD", ref)
    base = base.strip()
    if rc != 0 or not base:
        return esito
    _, albero = git(radice, "ls-tree", "-r", "--name-only", base)
    di_arturo = set(albero.splitlines())
    _, cambiati = git(radice, "diff", "--name-only", base)
    esito["file"] = sorted(f for f in set(cambiati.splitlines())
                           if f in di_arturo and f != "settings.json" and FILE.match(f))[:MASSIMO]
    rc, testo = git(radice, "show", f"{base}:settings.json")
    try:
        attesi = hook_dichiarati(json.loads(testo)) if rc == 0 else set()
    except ValueError:
        attesi = set()
    attuali = leggi_json(radice / "settings.json")
    locali = leggi_json(radice / "settings.local.json")
    if attuali.get("disableAllHooks") or locali.get("disableAllHooks"):
        esito["hook"] = ["tutti"]
    elif attesi and (radice / "settings.json").exists() and "rotta-settings" not in esito["config"]:
        esito["hook"] = sorted(attesi - hook_dichiarati(attuali))[:MASSIMO]
    return esito


def valori(esito: dict) -> list:
    return [f"file:{f}" for f in esito["file"]] + [f"hook:{h}" for h in esito["hook"]]


def riga(esito: dict) -> str:
    parti = []
    if esito["hook"] == ["tutti"]:
        parti.append("gli hook sono spenti (disableAllHooks): le guardie di Arturo non girano")
    elif esito["hook"]:
        parti.append(f"mancano dal settings.json gli hook di Arturo {', '.join(esito['hook'])}: quelle guardie non girano")
    comandi = [f for f in esito["file"] if f.startswith("commands/")]
    if comandi:
        nomi = ", ".join("/" + Path(f).stem for f in comandi)
        parti.append(f"hai modificato i comandi di Arturo {nomi}: il prossimo /aggiorna sposta da solo le tue aggiunte in un "
                     "file tuo, che gli aggiornamenti non toccano, se il tuo repository della config è privato o non ne hai "
                     "uno (per farlo subito: /aggiorna personale)")
    altri = [f for f in esito["file"] if not f.startswith("commands/")]
    if altri:
        parti.append(f"hai modificato {len(altri)} file di Arturo ({', '.join(altri[:3])}{'…' if len(altri) > 3 else ''}): "
                     "un aggiornamento può andare in conflitto")
    return ("DERIVA: " + "; ".join(parti) + ".") if parti else ""


def telemetria():
    spec = importlib.util.spec_from_file_location("telemetria", Path(__file__).resolve().parent.parent / "bin" / "telemetria.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(spec.origin).parent))
    spec.loader.exec_module(modulo)
    return modulo


def registra(esito: dict) -> None:
    t = telemetria()
    if t.perche_spenta():
        return
    stato = t.leggi_stato()
    attuali = valori(esito)
    if attuali != stato.get("deriva_inviata", []):
        if t.registra("deriva", f"insieme:{len(attuali)}") and all(t.registra("deriva", v) for v in attuali):
            t.cambia_stato(lambda s: s.__setitem__("deriva_inviata", attuali))
    oggi = t.ts.oggi().isoformat()
    nuove = [c for c in esito["config"] if f"{oggi} {c}" not in (stato.get("config_inviata") or [])]
    if nuove and all(t.registra("config", c) for c in nuove):
        # La config rotta parte subito: l'avvio della sessione, che viene dopo, trova le 6 ore scadute.
        t.cambia_stato(lambda s: (s.__setitem__("config_inviata", [f"{oggi} {c}" for c in esito["config"]]),
                                  s.__setitem__("ultimo_tentativo", 0)))


def main(argv: list) -> int:
    radice = Path(argv[0]) if argv else Path.home() / ".claude"
    try:
        esito = rileva(radice)
        testo = riga(esito)
        if testo:
            print(testo)
        registra(esito)
    except Exception:  # noqa: BLE001 - l'avvio non si ferma mai per la deriva
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
