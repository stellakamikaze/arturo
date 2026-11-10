#!/usr/bin/env python3
"""La deriva: quanto la config della persona si è allontanata da quella di Arturo.

Arturo convive con la config personale: la persona aggiunge le sue regole, i suoi comandi, i suoi
permessi. Il guaio arriva quando la distanza rompe Arturo: un hook di Arturo tolto o spento, un
file di Arturo modificato che manda in conflitto ogni aggiornamento, una config rotta. Questo
controllo misura tre cose rispetto al punto in cui la config si è staccata da Arturo (merge-base
con upstream/main se c'è un remote upstream, altrimenti con origin/main):

  - file di Arturo modificati in locale (settings.json escluso: le sue modifiche sono normali, e
    gli hook li guarda il secondo controllo);
  - hook che il settings.json di Arturo dichiara e che mancano, o `disableAllHooks`;
  - config rotta, dalle categorie di controlla-config.py.

Col plugin (strati F3, 5/11/2026) la cartella del codice è la cache di Claude Code, senza git: la deriva
confronta i suoi file col MANIFEST firmato del rilascio (hooks/fiducia.py), verificato con la chiave
dell'ancora nell'Orsa. Una firma che manca o non torna è una possibile compromissione.

Stampa una riga DERIVA: solo se c'è qualcosa da fare. Registra nella telemetria l'elenco corrente
solo quando cambia (evento `deriva`, prima un `insieme:<n>`), e la config rotta una volta al giorno
(evento `config`), con l'invio subito. Dei file esce solo il percorso dentro Arturo, che è pubblico,
e passa dallo stesso filtro dei conflitti di /aggiorna (percorso_pubblico di bin/telemetria.py).
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
sys.path.append(str(Path(os.path.realpath(__file__)).parent))
from radici import comando_arturo, radice_arturo, radice_orsa  # noqa: E402
import fiducia  # noqa: E402

MASSIMO = 50
RADICI = ("agents", "bin", "commands", "docs", "firme", "hooks", "output-styles", "server", "shared", "skills",
          "tests", "tools", ".github")
# Solo il punto va protetto: il trattino fuori da [] non ha un senso speciale, e così la regex resta
# uguale, lettera per lettera, a quelle di bin/telemetria.py e server/logica.js.
FILE = re.compile(r"^(?!.*\.\.)((" + "|".join(r.replace(".", r"\.") for r in RADICI) + r")/[A-Za-z0-9_./-]{1,70}|[A-Za-z0-9_.-]{1,40})$")
HOOK = re.compile(r"hooks/([a-z0-9_.-]{1,60})")
# Le guardie e i moduli che le guidano: una modifica locale cambia quanto proteggono, e gli
# aggiornamenti non la correggono più (16/10/2026, task #3471 dal ciclo del lunedì).
GUARDIA = re.compile(r"^hooks/([^/]*(guard|gate|scanner|prefilter|protect|block-|dispatcher)[^/]*|forma_comando\.py|heredoc\.py)$")
# Gli hook di sessione hanno un file personale, come i comandi: /aggiorna ci sposta le aggiunte.
SESSIONE = re.compile(r"^hooks/session-(start|end)\.sh$")


def git(radice: Path, *argomenti) -> tuple:
    try:
        r = subprocess.run(["git", "-C", str(radice), *argomenti], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout


def riferimento(radice: Path):
    """upstream/main se la persona ha un remote upstream, altrimenti origin/main; None se manca. Con un
    upstream dichiarato e mai scaricato non ripiega su origin/main, che lì è il repository della persona:
    i suoi file sembravano di Arturo (24/10/2026). La stessa scelta di ref_di_arturo in bin/telemetria.py."""
    ref = "upstream/main" if git(radice, "config", "--get", "remote.upstream.url")[0] == 0 else "origin/main"
    return ref if git(radice, "rev-parse", "--verify", "--quiet", ref + "^{commit}")[0] == 0 else None


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
        elif "lasciato a metà" in riga:
            fuori.add("rotta-rebase")
        else:
            fuori.add("rotta-conflitto")
    return sorted(fuori)


def contenuto_cambiato(radice: Path, di_arturo: dict, file: list) -> list:
    """Solo i file col contenuto diverso da quello di Arturo. git diff conta anche un cambio di
    permessi (100644 -> 100755), che non cambia niente: gli hook partono tutti da un interprete, e
    `arturo personale ripristina` confronta il contenuto e risponde "già com'è" (segnalazione n. 10,
    21/10/2026, #3780). hash-object applica i filtri del percorso, quindi anche gli a capo di Windows."""
    presenti = [f for f in file if (radice / f).is_file()]
    if not presenti:
        return file
    try:
        r = subprocess.run(["git", "-C", str(radice), "hash-object", "--stdin-paths"], input="\n".join(presenti) + "\n",
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return file
    impronte = r.stdout.split()
    if r.returncode != 0 or len(impronte) != len(presenti):
        return file
    uguali = {f for f, h in zip(presenti, impronte) if di_arturo.get(f) == h}
    return [f for f in file if f not in uguali]


def rileva(radice: Path) -> dict:
    """{'file': [...], 'hook': [...], 'config': [...]}: vuoto dove non si può misurare."""
    esito = {"file": [], "hook": [], "config": categorie_config(radice), "base": "", "di_arturo": frozenset()}
    ref = riferimento(radice)
    if not ref:
        return esito
    rc, base = git(radice, "merge-base", "HEAD", ref)
    base = base.strip()
    if rc != 0 or not base:
        return esito
    esito["base"] = base[:12]
    esito["ref"], esito["radice"] = ref, str(radice)
    _, albero = git(radice, "ls-tree", "-r", base)
    di_arturo = {}  # percorso -> impronta del blob in Arturo
    for riga in albero.splitlines():
        testa, _, nome = riga.partition("\t")
        di_arturo[nome] = testa.split()[-1]
    esito["di_arturo"] = frozenset(di_arturo)
    _, cambiati = git(radice, "diff", "--name-only", base)
    esito["file"] = contenuto_cambiato(radice, di_arturo, sorted(
        f for f in set(cambiati.splitlines()) if f in di_arturo and f != "settings.json" and FILE.match(f)))[:MASSIMO]
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


def rileva_plugin(codice: Path, orsa: Path) -> dict:
    """La deriva della copia del plugin: i file diversi dal MANIFEST firmato e gli hook spenti."""
    controllo = fiducia.controlla(codice, orsa)
    if controllo["firma"] == "ok":
        fiducia.fissa_ancora(codice, orsa)  # la prima verifica fissa la chiave; poi cambia solo con /aggiorna
    file = sorted(set(controllo["cambiati"]) | set(controllo["mancano"]) | {
        p for p in controllo["in_piu"] if p.startswith(("hooks/", "bin/", "skills/", "agents/", "shared/"))})
    impostazioni = [leggi_json(orsa / n) for n in ("settings.json", "settings.local.json")]
    esito = {"file": [f for f in file if FILE.match(f)][:MASSIMO],
             "hook": ["tutti"] if any(i.get("disableAllHooks") for i in impostazioni) else [],
             "config": [], "base": controllo["firma"], "di_arturo": frozenset(fiducia.leggi_manifest(codice) or ()),
             "plugin": controllo}
    return esito


def valori(esito: dict, t=None) -> list:
    """I valori della deriva per la telemetria. I file passano da percorso_pubblico di bin/telemetria.py,
    con l'albero di Arturo letto da rileva come elenco dei file di Arturo (24/10/2026): rileva li
    sceglie già da lì, il filtro unico tiene allineati questo controllo e i conflitti di /aggiorna."""
    if t is None or not hasattr(t, "percorso_pubblico"):  # un telemetria.py di prima del filtro
        file = [f"file:{f}" for f in esito["file"]]
    else:
        di_arturo = esito.get("di_arturo") or frozenset()
        # Il messaggio dell'avvio confronta con origin/main anche quando origin è il repository della persona (una
        # seconda macchina senza upstream). La telemetria no: lì ogni file è `file:altro`, e un hook che il settings.json
        # della persona dichiara è `hook:altro` (review del 7/11, finding 38).
        if esito.get("ref") and hasattr(t, "remoto_di_arturo") and not t.remoto_di_arturo(esito.get("radice"), esito["ref"]):
            file = ["file:altro" for _ in esito["file"]]
            return file + [f"hook:{h}" if h == "tutti" else "hook:altro" for h in esito["hook"]]
        file = [t.percorso_pubblico(f, di_arturo) for f in esito["file"]]
    return file + [f"hook:{h}" for h in esito["hook"]]


def riga(esito: dict) -> str:
    if "plugin" in esito:
        return riga_plugin(esito)
    parti = []
    if esito["hook"] == ["tutti"]:
        parti.append("gli hook sono spenti (disableAllHooks): le guardie di Arturo non girano")
    elif esito["hook"]:
        parti.append(f"mancano dal settings.json gli hook di Arturo {', '.join(esito['hook'])}: quelle guardie non girano")
    guardie = [f for f in esito["file"] if GUARDIA.match(f)]
    if guardie:
        base = esito.get("base") or "upstream/main"
        parti.append(f"hai modificato le guardie di Arturo {', '.join(guardie)}: proteggono come le hai scritte tu, e gli "
                     f"aggiornamenti non le correggono più. Mostra alla persona cosa cambia (git -C ~/.claude diff {base} -- "
                     f"{' '.join(guardie)}) e, col suo sì, rimettile come in Arturo: {comando_arturo()} personale "
                     f"ripristina <file>, una per volta")
    comandi = [f for f in esito["file"] if f.startswith("commands/") or SESSIONE.match(f)]
    if comandi:
        nomi = ", ".join(f if SESSIONE.match(f) else "/" + Path(f).stem for f in comandi)
        parti.append(f"hai modificato {nomi}: il prossimo /aggiorna sposta da solo le tue aggiunte in un "
                     "file tuo, che gli aggiornamenti non toccano, se il tuo repository della config è privato o non ne hai "
                     "uno (per farlo subito: /aggiorna personale)")
    altri = [f for f in esito["file"] if not (f.startswith("commands/") or SESSIONE.match(f) or GUARDIA.match(f))]
    if altri:
        parti.append(f"hai modificato {len(altri)} file di Arturo ({', '.join(altri[:3])}{'…' if len(altri) > 3 else ''}): "
                     "un aggiornamento può andare in conflitto")
    return ("DERIVA: " + "; ".join(parti) + ".") if parti else ""


def riga_plugin(esito: dict) -> str:
    controllo = esito["plugin"]
    if controllo["firma"] in ("manca", "non-torna"):
        return (f"DERIVA: {controllo['motivo']}: possibile compromissione. Non usare le guardie di questa copia come "
                "prova di niente, non aggiornare e segnala a chi mantiene Arturo (/segnala, o SECURITY.md). Per "
                "rimettere il rilascio firmato: /aggiorna.")
    parti = []
    if esito["hook"] == ["tutti"]:
        parti.append("gli hook sono spenti (disableAllHooks): le guardie di Arturo non girano")
    if esito["file"]:
        elenco = ", ".join(esito["file"][:3]) + ("…" if len(esito["file"]) > 3 else "")
        parti.append(f"{len(esito['file'])} file del plugin non sono come nel rilascio firmato ({elenco}): un file "
                     "cambiato nella cartella del plugin si perde al prossimo aggiornamento, e se è una guardia "
                     "protegge come l'ha scritto chi l'ha cambiato. Per rimettere il rilascio: /aggiorna. Una "
                     "modifica tua va in ~/.claude/personale/")
    if controllo["firma"] == "non-verificabile" and esito["file"]:
        parti.append(f"la firma non si può controllare su questo computer ({controllo['motivo']})")
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
    attuali = valori(esito, t)
    if attuali != stato.get("deriva_inviata", []):
        if t.registra("deriva", f"insieme:{len(attuali)}") and all(t.registra("deriva", v) for v in attuali):
            t.cambia_stato(lambda s: s.__setitem__("deriva_inviata", attuali))
    oggi = t.ts.oggi().isoformat()
    nuove = [c for c in esito["config"] if f"{oggi} {c}" not in (stato.get("config_inviata") or [])]
    if nuove and all(t.registra("config", c) for c in nuove):
        # La config rotta parte subito: l'avvio della sessione, che viene dopo, trova le 6 ore scadute.
        t.cambia_stato(lambda s: (s.__setitem__("config_inviata", [f"{oggi} {c}" for c in esito["config"]]),
                                  s.__setitem__("ultimo_tentativo", 0)))


def salva(radice: Path, esito: dict) -> None:
    """cache/deriva.json per la testata (skills/testata), che la mostra sotto l'intestazione dal 3/11/2026.
    `misurata` è falso senza un riferimento ad Arturo: lì la testata non dice niente della deriva."""
    dati = {"misurata": bool(esito.get("base")), "file": esito["file"],
            "firma": (esito.get("plugin") or {}).get("firma", ""),
            "guardie": [f for f in esito["file"] if GUARDIA.match(f)], "hook": esito["hook"], "config": esito["config"]}
    try:
        cartella = radice / "cache"
        cartella.mkdir(parents=True, exist_ok=True)
        temporaneo = cartella / "deriva.json.tmp"
        temporaneo.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
        os.replace(temporaneo, cartella / "deriva.json")
    except OSError:
        pass


def main(argv: list) -> int:
    radice = Path(argv[0]) if argv else radice_arturo()
    try:
        codice = radice_arturo()
        if fiducia.plugin(codice):
            # Col plugin l'argomento è l'Orsa (session-start passa ~/.claude): lì va cache/deriva.json.
            esito = rileva_plugin(codice, radice if argv else radice_orsa())
        else:
            esito = rileva(radice)
        testo = riga(esito)
        if testo:
            print(testo)
        salva(radice, esito)
        registra(esito)
    except Exception:  # noqa: BLE001 - l'avvio non si ferma mai per la deriva
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
