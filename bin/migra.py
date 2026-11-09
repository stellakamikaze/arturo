"""arturo migra: porta Arturo dal clone in ~/.claude al plugin (strati F4, #4534, docs/strati.md).

Col clone Arturo e i file della persona stanno nella stessa cartella, e ogni modifica personale a un file
di Arturo va in conflitto con l'aggiornamento. Col plugin il codice sta nella cache dei plugin e ~/.claude
resta tutta della persona (l'Orsa). Questo comando fa il passaggio una volta, con la prova prima e la
strada per tornare indietro.

  arturo migra --prova    il rapporto: cosa cambia, cosa resta tuo, cosa ferma la migrazione. Non tocca
                          niente: scrive solo il rapporto in ~/.claude/data/migra/, da mandare con /segnala
  arturo migra            la migrazione, con Claude Code chiuso, da un Terminale
  arturo migra indietro   rimette il clone com'era, dall'ultima copia di sicurezza
  --unica-macchina        con --prova o da solo: ~/.claude è un repository della persona con Arturo come upstream,
                          usato solo da questo computer. .git resta, e i file di Arturo escono con un commit
  arturo migra avviso     la riga che l'avvio del clone dà al modello, una volta al giorno, finché la
                          persona non migra: col plugin non stampa niente

La migrazione, in quest'ordine:
  1. i controlli del rapporto: con un motivo che ferma non parte niente;
  2. la copia di sicurezza in ~/.claude-arturo-clone-<data>: i file di Arturo, .git e ogni file che i
     passi dopo cambiano;
  3. personale.py separa --senza-commit: le modifiche ai comandi di Arturo vanno in personale/;
  4. il plugin dal catalogo (stellakamikaze/arturo#catalogo), solo se il tag del catalogo è firmato con
     la chiave del clone e porta lo sha del catalogo; poi la copia installata si controlla col MANIFEST;
  5. settings.json, in una scrittura sola: escono gli hook di Arturo (ora li porta il plugin), entrano le
     voci del plugin con l'unione a tre vie di impostazioni.py, restano le voci della persona;
  6. i file di Arturo e .git escono da ~/.claude: la copia di sicurezza li tiene.
Se un passo fallisce, la migrazione torna indietro da sola. `indietro` rifà lo stesso ritorno a mano.

Uscite: 0 fatto (o rapporto senza motivi che fermano); 1 fermo, niente cambiato; 2 uso sbagliato;
3 possibile compromissione del catalogo; 4 firma non verificabile su questo computer.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import filecmp
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BIN = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(BIN))
sys.path.append(str(BIN.parent / "hooks"))
from radici import comando_arturo, radice_arturo, radice_orsa  # noqa: E402

CATALOGO = "stellakamikaze/arturo#catalogo"
PLUGIN = "arturo@arturo"
MERCATO = "arturo"
COPIA = "-arturo-clone-"  # ~/.claude-arturo-clone-<data>, accanto all'Orsa: fuori da ~/.claude
# I file fuori dai file di Arturo che i passi 3-5 possono scrivere: la copia di sicurezza li tiene, o
# ricorda che non c'erano.
TOCCATI = ("settings.json", "data/arturo-impostazioni.lock", "arturo/rilasci.allowed_signers",
           "plugins/installed_plugins.json", "plugins/known_marketplaces.json")


class Ferma(Exception):
    def __init__(self, messaggio: str, uscita: int = 1):
        super().__init__(messaggio)
        self.uscita = uscita


def _modulo(nome: str, file: Path):
    spec = importlib.util.spec_from_file_location(nome, str(file))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def senza_fsmonitor() -> None:
    """Il demone fsmonitor di git tiene aperta la cartella .git che la migrazione copia e porta via: per
    questo processo si spegne, e quello già acceso si ferma. Vale anche per i git di personale.py."""
    n = int(os.environ.get("GIT_CONFIG_COUNT") or 0)
    os.environ.update({"GIT_CONFIG_COUNT": str(n + 1), f"GIT_CONFIG_KEY_{n}": "core.fsmonitor",
                       f"GIT_CONFIG_VALUE_{n}": "false"})
    try:
        subprocess.run(["git", "-C", str(radice_orsa()), "fsmonitor--daemon", "stop"], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


def git(r: Path, *argomenti) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(r), *argomenti], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=60)


def git_persona(r: Path, *argomenti, stdin: str = "") -> subprocess.CompletedProcess:
    """git nel repository della persona (forma upstream), con un'identità di riserva se lei non ne ha una: un commit
    di migra non deve fermarsi per questo."""
    identita = [] if git(r, "config", "user.email").stdout.strip() else ["-c", "user.name=arturo migra",
                                                                          "-c", "user.email=migra@arturo.invalid"]
    return subprocess.run(["git", "-C", str(r), *identita, *argomenti], input=stdin, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def leggi_json(f: Path) -> dict:
    try:
        dati = json.loads(f.read_text(encoding="utf-8"))
        return dati if isinstance(dati, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi_json(f: Path, dati: dict) -> None:
    """Scrittura atomica: un settings.json a metà spegne guardie e permessi alla sessione dopo."""
    f.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(f.parent), prefix=f".{f.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as uscita:
        uscita.write(json.dumps(dati, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, str(f))


def corto(p: Path) -> str:
    testo = str(p)
    casa = str(Path.home())
    return "~" + testo[len(casa):] if testo == casa or testo.startswith(casa + os.sep) else testo


def esiste(p: Path) -> bool:
    return os.path.lexists(str(p))


def catalogo() -> str:
    return os.environ.get("ARTURO_CATALOGO") or CATALOGO


# --- analisi -------------------------------------------------------------------------------------------

def hook_di_arturo(settings: dict, albero: set, orsa: Path) -> list:
    """(evento, comando) degli hook che lanciano un file di Arturo dentro l'Orsa."""
    radici = ["~/.claude", "$HOME/.claude", "${HOME}/.claude", str(orsa).replace("\\", "/")]
    schema = re.compile("(?:" + "|".join(re.escape(r) for r in radici) + r")/([^\s\"']+)")
    trovati = []
    for evento, gruppi in (settings.get("hooks") or {}).items():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            for hook in gruppo.get("hooks", []) if isinstance(gruppo, dict) else []:
                comando = hook.get("command", "") if isinstance(hook, dict) else ""
                if any(u in albero for u in schema.findall(str(comando).replace("\\", "/"))):
                    trovati.append((evento, comando))
    return trovati


def senza_hook(settings: dict, via: list) -> dict:
    togli = set(via)
    copia = json.loads(json.dumps(settings))
    hooks = copia.get("hooks") or {}
    for evento in list(hooks):
        gruppi = []
        for gruppo in hooks[evento] if isinstance(hooks[evento], list) else []:
            if not isinstance(gruppo, dict):
                continue
            restanti = [h for h in gruppo.get("hooks", []) if (evento, h.get("command", "")) not in togli]
            if restanti:
                gruppi.append(dict(gruppo, hooks=restanti))
        if gruppi:
            hooks[evento] = gruppi
        else:
            del hooks[evento]
    if "hooks" in copia and not hooks:
        del copia["hooks"]
    return copia


def chiavi_diverse(prima, dopo, via="") -> list:
    """Le voci cambiate, senza i valori: il rapporto va a chi mantiene Arturo."""
    if isinstance(prima, dict) and isinstance(dopo, dict):
        righe = []
        for k in list(dopo) + [k for k in prima if k not in dopo]:
            righe += chiavi_diverse(prima.get(k), dopo.get(k), f"{via}.{k}" if via else k)
        return righe
    if prima == dopo:
        return []
    if isinstance(prima, list) and isinstance(dopo, list):
        piu = len([x for x in dopo if x not in prima])
        meno = len([x for x in prima if x not in dopo])
        return [f"{via}: " + ", ".join(p for p in (f"+{piu}" if piu else "", f"-{meno}" if meno else "") if p)]
    if prima is None:
        return [f"{via}: nuova"]
    if dopo is None:
        return [f"{via}: tolta"]
    return [f"{via}: cambia"]


def settings_nuovi(orsa: Path, base: str, albero: set, frammento: dict) -> tuple:
    """(attuale, unito, hook tolti): settings.json senza gli hook di Arturo, unito al frammento del plugin.

    L'unione è quella di impostazioni.py, a tre vie. La base è il settings.json di Arturo da cui il clone
    è partito: Arturo cambia solo le voci che la persona ha lasciato com'erano. Base e voci della persona
    passano dalla stessa traduzione del pacchetto (barra dal puntatore, stile col prefisso arturo:), così
    una voce lasciata com'era nel clone vale "com'era" anche nel plugin."""
    impacchetta = _modulo("impacchetta_migra", radice_arturo() / "bin" / "impacchetta.py")
    unisci = _modulo("unisci_settings_migra", radice_arturo() / "bin" / "unisci-settings.py")
    attuale = leggi_json(orsa / "settings.json")
    mostra = git(orsa, "show", f"{base}:settings.json")
    try:
        di_arturo = json.loads(mostra.stdout) if mostra.returncode == 0 else {}
    except ValueError:
        di_arturo = {}
    tolti = hook_di_arturo(attuale, albero, orsa)
    restante = senza_hook(attuale, tolti)
    base, nostro = impacchetta.impostazioni(di_arturo), impacchetta.impostazioni(restante)
    try:
        unito = unisci.unisci(base, nostro, frammento)
    except unisci.Conflitto as errore:
        voce = _modulo("impostazioni_voce", BIN / "impostazioni.py")._dove(unisci, base, nostro, frammento)
        raise Ferma(f"settings.json: la voce {voce or '?'} è cambiata sia da te sia da Arturo ({errore}). Si decide "
                    "con Claude quale tenere, poi si rilancia.")
    if "$schema" in restante:
        unito = {"$schema": restante["$schema"], **unito}
    if restante.get("hooks"):
        unito["hooks"] = restante["hooks"]
    barra = unito.get("statusLine") if isinstance(unito.get("statusLine"), dict) else {}
    if hook_di_arturo({"hooks": {"barra": [{"hooks": [{"command": str(barra.get("command") or "")}]}]}}, albero, orsa):
        raise Ferma("la tua barra in basso (statusLine) usa un file di Arturo che esce da ~/.claude: va rifatta "
                    "con Claude prima di migrare.")
    return attuale, unito, tolti


def analizza(orsa: Path, unica: bool = False) -> dict:
    """Tutto quello che serve al rapporto e alla migrazione. Non scrive niente. `unica`: la persona dice che il suo
    repository (forma upstream) sta solo su questo computer (--unica-macchina)."""
    a = {"orsa": orsa, "ferma": [], "avvisi": [], "albero": set(), "base": "", "separa": [], "modificati": [],
         "cancellati": [], "hook_tolti": [], "hook_tuoi": 0, "voci": [], "sessioni": 0, "omonimi": [],
         "tuoi": [], "versione": "", "forma": "clone"}
    if radice_arturo().resolve() != orsa.resolve():
        a["ferma"].append(f"questo comando non gira dal clone in {corto(orsa)}: Arturo è già un plugin, o il clone "
                          "sta altrove")
        return a
    if not (orsa / ".git").exists():
        a["ferma"].append(f"{corto(orsa)} non è un repository git: non trovo il clone di Arturo")
        return a
    remoti = git(orsa, "remote").stdout.split()
    if "upstream" in remoti:
        # La forma upstream (segnalazione n. 62, 9/11/2026): .git è il repository della persona e resta. I file di
        # Arturo escono con un commit, che alla prima sincronizzazione arriva agli altri computer del repository e lì
        # toglierebbe Arturo e le guardie senza avviso: per questo vale solo con un computer, dichiarato.
        a["forma"] = "upstream"
        if not unica:
            a["ferma"].append("il tuo ~/.claude è un repository tuo con Arturo come upstream. Se lo usi solo su questo "
                              "computer, rilancia con --unica-macchina: i file di Arturo escono con un commit nel tuo "
                              "repository, e .git resta. Se lo usi su più computer, la migrazione di uno toglierebbe "
                              "Arturo agli altri: per questa forma scrivi a chi mantiene Arturo con /segnala, si fa a mano")
    for segno, cosa in (("rebase-merge", "un rebase"), ("rebase-apply", "un rebase"), ("MERGE_HEAD", "un merge")):
        percorso = git(orsa, "rev-parse", "--git-path", segno).stdout.strip()
        if percorso and esiste(orsa / percorso if not os.path.isabs(percorso) else Path(percorso)):
            a["ferma"].append(f"in {corto(orsa)} c'è {cosa} a metà: va chiuso prima")
    personale = _modulo("personale_migra", BIN / "personale.py")
    a["base"] = personale.base(orsa) or ""
    if not a["base"]:
        a["ferma"].append("non trovo Arturo (origin/main) nel clone: senza il punto di partenza non so quali file "
                          "sono di Arturo")
        return a
    a["versione"] = git(orsa, "describe", "--tags", "--always", "--match", "v[0-9]*.[0-9]*.[0-9]*").stdout.strip()
    a["albero"] = set(git(orsa, "ls-tree", "-r", "--name-only", a["base"]).stdout.splitlines()) - {"settings.json"}
    a["separa"] = personale.modificati(orsa, a["base"])
    cambiati = git(orsa, "diff", "--name-only", a["base"]).stdout.splitlines()
    a["modificati"] = sorted(f for f in cambiati if f in a["albero"] and esiste(orsa / f) and f not in a["separa"])
    a["cancellati"] = sorted(f for f in a["albero"] if not esiste(orsa / f))
    installati = (leggi_json(orsa / "plugins" / "installed_plugins.json").get("plugins") or {})
    if installati.get(PLUGIN):
        a["ferma"].append("il plugin di Arturo è già installato: la migrazione l'hai già fatta, o va tolto prima")
    if not shutil.which(os.environ.get("ARTURO_CLAUDE") or "claude"):
        a["ferma"].append("non trovo il comando claude: serve per installare il plugin")
    for programma in ("git", "ssh-keygen"):
        if not shutil.which(programma):
            a["ferma"].append(f"non trovo {programma}: serve per verificare la firma del rilascio")
    aggiornamenti = _modulo("aggiornamenti_migra", BIN / "aggiornamenti.py")
    a["sessioni"] = aggiornamenti.processi_claude()
    # Il frammento che il plugin porterà: per il rapporto vale quello del clone, che è la stessa versione.
    impacchetta = _modulo("impacchetta_migra", radice_arturo() / "bin" / "impacchetta.py")
    mostra = git(orsa, "show", "HEAD:settings.json")
    try:
        frammento = impacchetta.impostazioni(json.loads(mostra.stdout)) if mostra.returncode == 0 else {}
        attuale, unito, tolti = settings_nuovi(orsa, a["base"], a["albero"], frammento)
        a["hook_tolti"] = tolti
        a["hook_tuoi"] = sum(len(g.get("hooks", [])) for gs in (unito.get("hooks") or {}).values() for g in gs
                             if isinstance(g, dict))
        a["voci"] = [r for r in chiavi_diverse(attuale, unito) if not r.startswith("hooks")]
    except Ferma as errore:
        a["ferma"].append(str(errore))
    except ValueError as errore:
        a["ferma"].append(f"settings.json non si legge ({errore})")
    nomi_arturo = {Path(f).stem for f in a["albero"] if re.fullmatch(r"commands/[^/]+\.md", f)} | \
                  {f.split("/")[1] for f in a["albero"] if f.startswith("skills/") and f.count("/") >= 2}
    for cartella in sorted((orsa / "skills").glob("*")) if (orsa / "skills").is_dir() else []:
        if cartella.name in nomi_arturo and not any(f.startswith(f"skills/{cartella.name}/") for f in a["albero"]):
            a["omonimi"].append(cartella.name)
    cime = {f.split("/")[0] for f in a["albero"]} | {".git", "settings.json"}
    a["tuoi"] = sorted(v.name for v in orsa.iterdir() if v.name not in cime)
    if (orsa / "CLAUDE.md").is_file():
        # Le regole consigliate da /setup che il CLAUDE.md ripete (#4874): col plugin arrivano col metodo.
        personale = _modulo("personale_migra", BIN / "personale.py")
        try:
            testo = (orsa / "CLAUDE.md").read_text(encoding="utf-8")
            a["regole_doppie"] = regole_doppie(personale, testo)
        except (OSError, UnicodeDecodeError):
            a["regole_doppie"] = 0
    return a


def regole_doppie(personale, testo: str) -> int:
    """Quante righe del CLAUDE.md sono uguali a una regola consigliata. righe_doppie dà la coppia (doppie, simili):
    contarne la lunghezza diceva sempre 2 (finding 23 della review del 7/11/2026)."""
    return len(personale.righe_doppie(testo, personale.regole_consigliate(radice_arturo()))[0])


def rapporto(a: dict) -> str:
    """Il rapporto della prova. Nomina i file di Arturo e conta quelli della persona, senza nomi:
    va a chi mantiene Arturo con /segnala."""
    orsa = a["orsa"]
    adesso = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    cc = subprocess.run([os.environ.get("ARTURO_CLAUDE") or "claude", "--version"], capture_output=True, text=True,
                        timeout=30).stdout.strip() if shutil.which(os.environ.get("ARTURO_CLAUDE") or "claude") else "?"
    righe = [f"RAPPORTO DI MIGRAZIONE (arturo migra --prova) · {adesso}",
             f"Arturo {a['versione'] or '?'} (clone, base {a['base'][:8] or '?'}) · {platform.system()} "
             f"{platform.release()} · Claude Code {cc or '?'} · Python {platform.python_version()}", ""]
    if a["ferma"]:
        righe.append(f"ESITO: FERMA, {len(a['ferma'])} motivi. La migrazione non parte:")
        righe += [f"  - {m}" for m in a["ferma"]]
    else:
        righe.append("ESITO: PRONTA. La migrazione si può fare.")
    righe += ["", "Cosa succede, in ordine:",
              f"1. Copia di sicurezza in {corto(orsa.parent / (orsa.name + COPIA + '<data>'))}: "
              f"{len(a['albero']) - len(a['cancellati'])} file di Arturo, la cartella .git e settings.json.",
              "2. Le tue modifiche ai comandi di Arturo passano in personale/: "
              + (", ".join(f"{f} -> personale/{Path(f).stem}.{'sh' if f.endswith('.sh') else 'md'}" for f in a["separa"])
                 if a["separa"] else "nessuna da spostare."),
              f"3. Il plugin si installa dal catalogo {catalogo()}, solo da un rilascio firmato.",
              f"4. settings.json: escono {len(a['hook_tolti'])} hook di Arturo (ora li porta il plugin), restano "
              f"{a['hook_tuoi']} hook tuoi; " + (f"{len(a['voci'])} voci cambiano:" if a["voci"] else "nessun'altra voce cambia.")]
    righe += [f"     {v}" for v in a["voci"][:30]]
    if a.get("forma") == "upstream":
        righe.append(f"5. Escono da ~/.claude {len(a['albero']) - len(a['cancellati'])} file di Arturo, con un commit nel "
                     "tuo repository che la prossima /fine pubblica: .git e .gitignore restano, e restano tuoi.")
    else:
        righe.append(f"5. Escono da ~/.claude {len(a['albero']) - len(a['cancellati'])} file di Arturo e la cartella .git.")
    if a["modificati"]:
        righe += ["", f"Tue modifiche a file di Arturo che il plugin non porta ({len(a['modificati'])}): restano nella "
                  "copia di sicurezza, e col plugin vale la versione di Arturo:"]
        righe += [f"  {f}" for f in a["modificati"][:40]]
    if a["cancellati"]:
        righe += ["", f"File di Arturo che avevi tolto ({len(a['cancellati'])}): col plugin ci sono di nuovo."]
        righe += [f"  {f}" for f in a["cancellati"][:20]]
    if a["omonimi"]:
        righe += ["", "Skill tue con lo stesso nome di una di Arturo (il nome da solo porta alla tua, per quella di Arturo "
                  "scrivi arturo:<nome>): " + ", ".join(a["omonimi"])]
    if a.get("regole_doppie"):
        righe += ["", f"Il tuo CLAUDE.md ripete {a['regole_doppie']} regole del metodo, che col plugin arriva all'avvio: "
                  "dopo la migrazione chiedi a Claude di lanciare `arturo personale regole-doppie`, che le elenca e le toglie con una copia."]
    righe += ["", f"Restano tuoi: {len(a['tuoi'])} file e cartelle di ~/.claude fuori da Arturo"
              + (", fra cui " + ", ".join(n for n in ("CLAUDE.md", "personale", "data", "projects") if n in a["tuoi"])
                 if any(n in a["tuoi"] for n in ("CLAUDE.md", "personale", "data", "projects")) else "") + "."]
    if a["avvisi"]:
        righe += [""] + [f"Avviso: {x}." for x in a["avvisi"]]
    if not a["ferma"]:
        righe += ["", "Per migrare: chiudi " + (f"le {a['sessioni']} sessioni di Claude Code aperte"
                                                 if a["sessioni"] else "Claude Code")
                  + f", poi da un Terminale: {comando_arturo()} migra"
                  + (" --unica-macchina" if a.get("forma") == "upstream" else "")]
    return "\n".join(righe) + "\n"


# --- la copia di sicurezza -----------------------------------------------------------------------------

def speciali(cartella: str, nomi: list) -> list:
    """Socket e pipe (il demone fsmonitor di git ne lascia uno in .git): non si copiano e non si confrontano."""
    return [n for n in nomi if not os.path.islink(os.path.join(cartella, n))
            and not os.path.isdir(os.path.join(cartella, n)) and not os.path.isfile(os.path.join(cartella, n))]


def copia_voce(sorgente: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if os.path.islink(str(sorgente)):
        os.symlink(os.readlink(str(sorgente)), str(dest))
    elif sorgente.is_dir():
        shutil.copytree(str(sorgente), str(dest), symlinks=True, ignore=speciali)
    else:
        shutil.copy2(str(sorgente), str(dest))


def togli(voce: Path) -> None:
    """Toglie un file, un collegamento o una cartella. Su Windows git lascia file in sola lettura in .git."""
    def sblocca(funzione, percorso, _errore):
        os.chmod(percorso, 0o700)
        funzione(percorso)
    if os.path.islink(str(voce)) or voce.is_file():
        try:
            voce.unlink()
        except PermissionError:
            os.chmod(str(voce), 0o600)
            voce.unlink()
    elif voce.is_dir():
        shutil.rmtree(str(voce), onerror=sblocca)


def uguali(a: Path, b: Path) -> bool:
    if os.path.islink(str(a)) or os.path.islink(str(b)):
        return os.path.islink(str(b)) and os.readlink(str(a)) == os.readlink(str(b))
    if a.is_dir():
        confronto = filecmp.dircmp(str(a), str(b), ignore=speciali(str(a), os.listdir(str(a)))
                                   + speciali(str(b), os.listdir(str(b))))
        return not (confronto.left_only or confronto.right_only or confronto.diff_files or confronto.funny_files) \
            and all(uguali(a / d, b / d) for d in confronto.common_dirs)
    return b.is_file() and filecmp.cmp(str(a), str(b), shallow=False)


def fai_copia(a: dict) -> Path:
    orsa = a["orsa"]
    adesso = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    cartella = orsa.parent / f"{orsa.name}{COPIA}{adesso}"
    cartella.mkdir()
    try:
        return _riempi_copia(a, cartella, adesso)
    except BaseException:
        # Una copia a metà non deve restare (finding 84 del 7/11/2026): `indietro` la prendeva per buona e metteva
        # un .git parziale al posto di quello vero. La cartella è nata qui sopra, quindi è solo della copia.
        togli(cartella)
        raise


def _riempi_copia(a: dict, cartella: Path, adesso: str) -> Path:
    orsa = a["orsa"]
    dentro = cartella / "copia"
    presenti = sorted(f for f in a["albero"] if esiste(orsa / f))
    personali = [f"personale/{Path(f).stem}.{'sh' if f.endswith('.sh') else 'md'}" for f in a["separa"]]
    toccati = {f: esiste(orsa / f) for f in list(TOCCATI) + personali}
    registro = {"versione": 1, "orsa": str(orsa), "creata": adesso, "passi": [], "albero": presenti,
                "toccati": toccati, "git": True, "forma": a.get("forma", "clone")}
    scrivi_json(cartella / "migra.json", registro)
    for rel in [".git", *presenti, *[f for f, c in toccati.items() if c]]:
        copia_voce(orsa / rel, dentro / rel)
        if not uguali(orsa / rel, dentro / rel):
            raise Ferma(f"la copia di sicurezza di {rel} non torna: non tocco niente")
    # Il codice che fa la migrazione, per tornare indietro anche quando bin/ è già fuori da ~/.claude e il
    # rilascio di partenza non aveva ancora migra.py.
    for parte in ("bin", "hooks"):
        shutil.copytree(str(radice_arturo() / parte), str(cartella / "codice" / parte), symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    registro["passi"].append("copia")
    scrivi_json(cartella / "migra.json", registro)
    salva_identita(orsa)
    return cartella


def salva_identita(orsa: Path) -> None:
    """L'identità di Git che /setup scriveva in ~/.claude/.git/config passa in ~/.claude/arturo/git-identita prima
    che .git esca: la leggono bin/identita-git.sh, /inizio e /fine (review del 7/11/2026, finding 80)."""
    file = orsa / "arturo" / "git-identita"
    if file.exists():
        return
    valori = {k: git(orsa, "config", "--local", f"user.{k}").stdout.strip() for k in ("name", "email")}
    if not valori["email"]:
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    for chiave, valore in valori.items():
        if valore:
            subprocess.run(["git", "config", "--file", str(file), f"user.{chiave}", valore], capture_output=True,
                           timeout=60)


def passo(cartella: Path, nome: str) -> None:
    registro = leggi_json(cartella / "migra.json")
    registro.setdefault("passi", []).append(nome)
    scrivi_json(cartella / "migra.json", registro)


# --- i passi -------------------------------------------------------------------------------------------

def _claude(*argomenti, timeout: int = 300) -> subprocess.CompletedProcess:
    comando = [os.environ.get("ARTURO_CLAUDE") or "claude", "plugin", *argomenti]
    # Anche `claude plugin` chiude con gli hook del clone: session-end.sh lancerebbe l'aggiornamento automatico
    # staccato, proprio mentre i file di Arturo stanno uscendo da ~/.claude (6/11/2026).
    env = {**os.environ, "ARTURO_AGGIORNAMENTI": "manuali"}
    try:
        return subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL, env=env)
    except (OSError, subprocess.SubprocessError) as errore:
        return subprocess.CompletedProcess(comando, 1, "", str(errore))


def installa_plugin(orsa: Path, cartella: Path) -> Path:
    """Catalogo, verifica del tag con la chiave del clone, installazione, controllo della copia."""
    aggiornamenti = _modulo("aggiornamenti_migra", BIN / "aggiornamenti.py")
    fiducia = _modulo("fiducia_migra", radice_arturo() / "hooks" / "fiducia.py")
    if not (leggi_json(orsa / "plugins" / "known_marketplaces.json").get(MERCATO)):
        aggiunto = _claude("marketplace", "add", catalogo(), timeout=300)
        if aggiunto.returncode != 0:
            raise Ferma(f"il catalogo di Arturo non si aggiunge ({(aggiunto.stderr or aggiunto.stdout).strip()[:200]})")
        passo(cartella, "catalogo")
    # La chiave che verifica è quella del clone, che git ha già verificato: diventa l'ancora dell'Orsa.
    fiducia.fissa_ancora(radice_arturo(), orsa)
    rc, tag, sha = aggiornamenti.verifica_catalogo(orsa)
    if rc != 0:
        raise Ferma(f"il catalogo non indica un rilascio firmato che posso installare ({tag or 'nessun tag'})",
                    rc if rc in (3, 4) else 1)
    messo = _claude("install", PLUGIN)
    passo(cartella, "plugin")
    if messo.returncode != 0:
        raise Ferma(f"claude plugin install non è riuscito ({(messo.stderr or messo.stdout).strip()[:200]})")
    voce = aggiornamenti.installato(orsa)
    copia = Path(str(voce.get("installPath") or ""))
    if voce.get("gitCommitSha") != sha:
        raise Ferma(f"Claude Code ha installato {str(voce.get('gitCommitSha'))[:12]}, non lo sha verificato {sha[:12]}", 3)
    controllo = fiducia.controlla(copia, orsa)
    if controllo["firma"] != "ok" or controllo["cambiati"] or controllo["mancano"]:
        raise Ferma(f"la copia installata non è come il MANIFEST firmato ({controllo['motivo'] or controllo['cambiati'][:3] or controllo['mancano'][:3]})",
                    4 if controllo["firma"] == "non-verificabile" else 3)
    print(f"PLUGIN: {tag} installato e verificato")
    return copia


def scrivi_settings(a: dict, copia: Path) -> None:
    orsa = a["orsa"]
    frammento = leggi_json(copia / "impostazioni" / "arturo.json")
    if not frammento:
        raise Ferma("il plugin installato non porta impostazioni/arturo.json")
    attuale, unito, tolti = settings_nuovi(orsa, a["base"], a["albero"], frammento)
    impostazioni = _modulo("impostazioni_migra", copia / "bin" / "impostazioni.py")
    if impostazioni.doppi(unito) or hook_di_arturo(unito, a["albero"], orsa):
        raise Ferma("dopo l'unione restano hook che lanciano file di Arturo da ~/.claude")
    scrivi_json(orsa / "settings.json", unito)
    versione = leggi_json(copia / ".claude-plugin" / "plugin.json").get("version", "")
    scrivi_json(orsa / "data" / "arturo-impostazioni.lock", {"versione": versione, "frammento": frammento})
    voci = [r for r in chiavi_diverse(attuale, unito) if not r.startswith("hooks")]
    print(f"IMPOSTAZIONI: {len(tolti)} hook di Arturo tolti, {len(voci)} voci cambiate")


def togli_arturo(a: dict, cartella: Path) -> None:
    """I file di Arturo e .git escono da ~/.claude. Ognuno ha già la sua copia, controllata al passo 2."""
    orsa = a["orsa"]
    registro = leggi_json(cartella / "migra.json")
    dentro = cartella / "copia"
    # Prima si controllano tutte le copie, poi si toglie: un controllo dentro il ciclo toglieva già .git quando
    # mancava la copia di un file dopo (finding 86 del 7/11/2026).
    upstream = registro.get("forma") == "upstream"
    # Nella forma upstream .git e .gitignore sono della persona: restano (il .gitignore tiene fuori dai suoi commit
    # credenziali, cache e dati).
    voci = [f for f in registro["albero"] if f != ".gitignore"] if upstream else [".git", *registro["albero"]]
    manca = next((rel for rel in voci if not esiste(dentro / rel)), None)
    if manca:
        raise Ferma(f"manca la copia di {manca}: non tolgo niente")
    for rel in voci:
        togli(orsa / rel)
    # Ogni cartella sopra un file di Arturo, dalla più profonda: skills/arturo ha solo sottocartelle.
    cartelle = sorted({str(antenato) for f in registro["albero"] for antenato in Path(f).parents if str(antenato) != "."},
                      key=lambda c: -c.count("/"))
    for rel in cartelle:
        c = orsa / rel
        cache = c / "__pycache__"
        if cache.is_dir():
            shutil.rmtree(str(cache), ignore_errors=True)
        try:
            c.rmdir()  # solo se è vuota: un file tuo dentro una cartella di Arturo resta
        except OSError:
            pass
    if upstream:
        commit_migrazione(orsa, voci, cartella)


def commit_migrazione(orsa: Path, voci: list, cartella: Path) -> None:
    """Forma upstream: i file di Arturo escono anche dal repository della persona, in un commit. Senza, ogni /fine
    vedrebbe centinaia di cancellazioni, e l'avvio direbbe "file non salvati". Il push lo fa la /fine dopo."""
    tolti = git_persona(orsa, "rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "--pathspec-from-file=-",
                        stdin="\n".join(voci) + "\n")
    if tolti.returncode != 0:
        raise Ferma(f"il tuo repository non toglie i file di Arturo dall'indice ({tolti.stderr.strip()[:160]})")
    if esiste(orsa / "settings.json"):
        git_persona(orsa, "add", "--", "settings.json")
    fatto = git_persona(orsa, "commit", "--quiet", "-m", "Arturo passa al plugin: il codice esce da questo repository",
                        "-m", "arturo migra --unica-macchina. Per tornare al clone: arturo migra indietro.")
    if fatto.returncode != 0:
        raise Ferma(f"il commit nel tuo repository non è riuscito ({(fatto.stderr or fatto.stdout).strip()[:160]})")
    registro = leggi_json(cartella / "migra.json")
    registro["commit"] = git(orsa, "rev-parse", "HEAD").stdout.strip()
    scrivi_json(cartella / "migra.json", registro)


# --- i comandi -----------------------------------------------------------------------------------------

def cmd_prova(unica: bool = False) -> int:
    orsa = radice_orsa()
    a = analizza(orsa, unica)
    testo = rapporto(a)
    print(testo, end="")
    try:
        cartella = orsa / "data" / "migra"
        cartella.mkdir(parents=True, exist_ok=True)
        file = cartella / f"rapporto-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        file.write_text(testo, encoding="utf-8")
        print(f"\nIl rapporto è anche in {corto(file)}. Mandalo a chi mantiene Arturo con /segnala.")
    except OSError as errore:
        print(f"\nIl rapporto non si salva ({errore}): copialo da qui.", file=sys.stderr)
    return 1 if a["ferma"] else 0


def cmd_migra(unica: bool = False) -> int:
    orsa = radice_orsa()
    a = analizza(orsa, unica)
    if a["ferma"]:
        print("FERMA: la migrazione non parte, niente è cambiato.\n" + "\n".join(f"  - {m}" for m in a["ferma"])
              + f"\nIl rapporto completo: {comando_arturo()} migra --prova" + (" --unica-macchina" if unica else ""),
              file=sys.stderr)
        return 1
    if a["sessioni"]:
        print(f"FERMA: ci sono {a['sessioni']} sessioni di Claude Code aperte. Gli hook di Arturo escono da "
              "~/.claude, e una sessione aperta resterebbe senza guardie. Chiudile e rilancia da un Terminale.",
              file=sys.stderr)
        return 1
    try:
        cartella = fai_copia(a)
    except (Ferma, OSError) as errore:
        print(f"FERMA: la copia di sicurezza non è riuscita ({errore}). Niente è cambiato in ~/.claude.", file=sys.stderr)
        return 1
    print(f"COPIA: {corto(cartella)}")
    try:
        personale = _modulo("personale_migra", BIN / "personale.py")
        if personale.separa(commit=False, r=orsa) != 0:
            raise Ferma("le modifiche ai comandi non passano in personale/")
        passo(cartella, "personale")
        copia = installa_plugin(orsa, cartella)
        scrivi_settings(a, copia)
        passo(cartella, "impostazioni")
        togli_arturo(a, cartella)
        # Lo stato dice cose del clone, come "si installa alla chiusura": col plugin sarebbero false.
        try:
            (a["orsa"] / "session-env" / "aggiornamento.json").unlink()
        except OSError:
            pass
        passo(cartella, "fuori")
        registra_dopo(cartella, orsa)
    except (Ferma, OSError, subprocess.SubprocessError, ValueError, KeyError) as errore:
        uscita = errore.uscita if isinstance(errore, Ferma) else 1
        print(f"FERMA: {str(errore).rstrip('.')}. Torno indietro.", file=sys.stderr)
        indietro(cartella, conserva=False)
        return uscita
    print(f"MIGRATO: Arturo è un plugin, e ~/.claude tiene solo i tuoi file. Apri Claude Code come sempre.\n"
          f"Per tornare al clone, con Claude Code chiuso: python3 {corto(cartella / 'codice' / 'bin' / 'arturo')} migra indietro")
    if a.get("regole_doppie"):
        print(f"Il tuo CLAUDE.md ripete {a['regole_doppie']} regole che ora arrivano col plugin all'avvio. In Claude Code "
              "chiedi di lanciare `arturo personale regole-doppie`: le elenca, e con --togli le toglie con una copia.")
    return 0


def impronta(voce: Path) -> str:
    """Il contenuto di un file, o "" se non c'è. Una cartella o un collegamento valgono per il loro nome."""
    if os.path.islink(str(voce)):
        return "-> " + os.readlink(str(voce))
    if voce.is_file():
        import hashlib  # noqa: PLC0415
        return hashlib.sha256(voce.read_bytes()).hexdigest()
    return "cartella" if voce.is_dir() else ""


def registra_dopo(cartella: Path, orsa: Path) -> None:
    """Come la migrazione ha lasciato i file toccati: `indietro` mette da parte solo quello che la persona ha
    cambiato dopo (finding 14)."""
    try:  # la migrazione è già riuscita: un registro che non si scrive non la deve disfare
        registro = leggi_json(cartella / "migra.json")
        registro["dopo"] = {rel: impronta(orsa / rel) for rel in (registro.get("toccati") or {})}
        scrivi_json(cartella / "migra.json", registro)
    except OSError:
        pass


def ultima_copia(orsa: Path):
    """L'ultima copia di sicurezza completa. Una copia senza il passo "copia" è rimasta a metà (disco pieno, un
    errore): riportarla metteva un .git parziale al posto di quello vero (finding 84 del 7/11/2026)."""
    copie = sorted(p for p in orsa.parent.glob(f"{orsa.name}{COPIA}*")
                   if "copia" in (leggi_json(p / "migra.json").get("passi") or []))
    return copie[-1] if copie else None


def indietro(cartella: Path, conserva: bool = True) -> int:
    """Rimette il clone com'era: toglie plugin e catalogo se li ha messi la migrazione, poi riporta dalla
    copia ogni file dei passi. La copia resta: si può rifare.

    conserva: un file che la persona ha scritto o cambiato dopo la migrazione (una riga in personale/inizio.md,
    un'impostazione, un altro plugin) va in <copia>/sostituiti-<ora>/ prima di tornare com'era (finding 14 del
    7/11/2026): prima spariva senza copia. Il ritorno automatico di una migrazione fallita non conserva: lì i
    file diversi li ha scritti la migrazione stessa."""
    registro = leggi_json(cartella / "migra.json")
    orsa = Path(registro.get("orsa") or radice_orsa())
    dentro = cartella / "copia"
    passi = registro.get("passi") or []
    problemi = []
    dopo = registro.get("dopo") or {}
    da_parte = cartella / f"sostituiti-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    messi = []

    # Prima di tutto, anche prima di togliere il plugin: plugins/installed_plugins.json conta com'era.
    for rel in (registro.get("albero") or []) + list(registro.get("toccati") or {}):
        voce = orsa / rel
        if not conserva or not esiste(voce) or rel in messi:
            continue
        if esiste(dentro / rel) and uguali(dentro / rel, voce):
            continue
        if rel in dopo and dopo[rel] == impronta(voce):
            continue
        copia_voce(voce, da_parte / rel)
        messi.append(rel)

    if "plugin" in passi:
        tolto = _claude("uninstall", PLUGIN)
        if tolto.returncode != 0:
            problemi.append(f"claude plugin uninstall: {(tolto.stderr or tolto.stdout).strip()[:120]}")
    if "catalogo" in passi:
        tolto = _claude("marketplace", "remove", MERCATO)
        if tolto.returncode != 0:
            problemi.append(f"claude plugin marketplace remove: {(tolto.stderr or tolto.stdout).strip()[:120]}")
    if registro.get("forma") == "upstream":
        # Il .git della persona non si sostituisce: dopo la migrazione può avere commit suoi, già pubblicati, e una
        # copia vecchia li perderebbe e riporterebbe il commit della migrazione alla prima sincronizzazione.
        problemi += ritorno_upstream(orsa, registro.get("commit") or "", list(registro.get("toccati") or {}))
    elif (dentro / ".git").exists() and not (esiste(orsa / ".git") and uguali(dentro / ".git", orsa / ".git")):
        if esiste(orsa / ".git"):
            scarto = cartella / f"git-sostituito-{dt.datetime.now().strftime('%H%M%S')}"
            shutil.move(str(orsa / ".git"), str(scarto))
        copia_voce(dentro / ".git", orsa / ".git")
    for rel in registro.get("albero") or []:
        voce = orsa / rel
        if esiste(voce) and not uguali(dentro / rel, voce):
            togli(voce)
        if not esiste(voce):
            copia_voce(dentro / rel, voce)
    for rel, c_era in (registro.get("toccati") or {}).items():
        voce = orsa / rel
        if c_era:
            if esiste(voce):
                togli(voce)
            copia_voce(dentro / rel, voce)
        elif esiste(voce):
            togli(voce)
    registro.setdefault("passi", []).append("indietro")
    scrivi_json(cartella / "migra.json", registro)
    if problemi:
        print("INDIETRO con avvisi: i file sono tornati com'erano, ma " + "; ".join(problemi), file=sys.stderr)
    print(f"INDIETRO: il clone è di nuovo in {corto(orsa)}, com'era prima della migrazione.")
    if messi:
        print(f"I file che avevi cambiato dopo la migrazione sono in {corto(da_parte)}: "
              + ", ".join(messi[:8]) + (f" e altri {len(messi) - 8}" if len(messi) > 8 else "")
              + ". Riporta con Claude quello che ti serve.")
    return 0


def ritorno_upstream(orsa: Path, commit: str, toccati: list) -> list:
    """Forma upstream: un commit che annulla quello della migrazione, sopra i commit della persona. Se il commit non
    c'è (la migrazione si è fermata prima), si toglie solo quello che era già nell'indice. I problemi, se ce ne sono.

    I file toccati (settings.json, che `claude plugin uninstall` riscrive) tornano prima alla versione del commit:
    il revert rifiuta un file cambiato, e `indietro` li rimette subito dopo dalla copia, con le modifiche della
    persona già messe da parte."""
    if not commit or git(orsa, "merge-base", "--is-ancestor", commit, "HEAD").returncode != 0:
        git(orsa, "reset", "-q")
        return []
    tracciati = set(git(orsa, "ls-files", "--", *toccati).stdout.splitlines()) if toccati else set()
    if tracciati:
        git(orsa, "checkout", "-q", "HEAD", "--", *sorted(tracciati))
    annullato = git_persona(orsa, "revert", "--no-edit", commit)
    if annullato.returncode != 0:
        git(orsa, "revert", "--abort")
        return [f"il commit che annulla la migrazione non è riuscito ({(annullato.stderr or annullato.stdout).strip()[:120]}): "
                f"i file sono tornati, il repository no; rifallo con git revert {commit[:12]}"]
    return []


# I sistemi dove il passaggio al plugin è provato: solo lì l'avvio lo propone.
SISTEMI_PROVATI = ("posix",)


def avviso() -> str:
    """La riga dell'avvio per chi ha ancora il clone: una volta al giorno, senza git (l'avvio deve essere
    svelto). Col plugin, o con un ~/.claude che non è il clone, è vuota. Anche su Windows, finché il passaggio
    non è provato lì (#4873, docs/strati.md; review del 7/11/2026, finding 99)."""
    if os.name not in SISTEMI_PROVATI:
        return ""
    orsa = radice_orsa()
    try:
        if radice_arturo().resolve() != orsa.resolve() or not (orsa / ".git").exists():
            return ""
    except OSError:
        return ""
    if (leggi_json(orsa / "plugins" / "installed_plugins.json").get("plugins") or {}).get(PLUGIN):
        return ""
    segno = orsa / "session-env" / "migra-avviso.json"
    oggi = dt.date.today().isoformat()
    if leggi_json(segno).get("giorno") == oggi:
        return ""
    try:
        scrivi_json(segno, {"giorno": oggi})
    except OSError:
        pass
    config = orsa / ".git" / "config"
    try:
        upstream = '[remote "upstream"]' in config.read_text(encoding="utf-8", errors="replace")
    except OSError:
        upstream = False
    comando = comando_arturo()
    testa = ("ARTURO PLUGIN: Arturo adesso si installa come plugin di Claude Code. Col plugin un aggiornamento cambia "
             "solo Arturo e non tocca mai i file della persona; questa installazione è ancora la copia dentro "
             "~/.claude. Dillo alla persona all'inizio, in due frasi semplici, una volta sola in questa sessione: ")
    if upstream:
        return testa + ("il suo ~/.claude è un repository suo con Arturo come upstream. Se lo usa solo su questo computer, "
                        f"con `{comando} migra --prova --unica-macchina` vede cosa cambierebbe, senza che niente cambi; "
                        f"la migrazione vera si lancia da un Terminale con Claude Code chiuso (`{comando} migra "
                        "--unica-macchina`), e `migra indietro` rimette tutto com'era. Con più computer il passaggio "
                        "si fa a mano con chi mantiene Arturo: può scrivergli con /segnala.")
    return testa + (f"con `{comando} migra --prova` vede cosa cambierebbe, senza che niente cambi, e può mandare il "
                    "rapporto a chi mantiene Arturo con /segnala. La migrazione vera si lancia da un Terminale con "
                    f"Claude Code chiuso (`{comando} migra`), fa prima una copia di sicurezza, e "
                    "`migra indietro` rimette tutto com'era.")


def main(argv: list) -> int:
    if argv == ["avviso"]:
        riga = avviso()
        if riga:
            print(riga)
        return 0
    senza_fsmonitor()
    if argv in (["-h"], ["--help"], ["aiuto"], ["help"]):
        print(__doc__)
        return 0
    if argv in (["--prova"], ["--prova", "--unica-macchina"], ["--unica-macchina", "--prova"]):
        return cmd_prova("--unica-macchina" in argv)
    if argv in ([], ["--unica-macchina"]):
        return cmd_migra(argv == ["--unica-macchina"])
    if argv == ["indietro"]:
        orsa = radice_orsa()
        cartella = ultima_copia(orsa)
        if cartella is None:
            print(f"Nessuna copia di sicurezza della migrazione accanto a {corto(orsa)}: non c'è niente da riportare.",
                  file=sys.stderr)
            return 1
        if "indietro" in (leggi_json(cartella / "migra.json").get("passi") or []) \
                and "fuori" not in (leggi_json(cartella / "migra.json").get("passi") or []):
            print(f"INDIETRO: la migrazione di {corto(cartella)} non è finita ed è già tornata indietro da sola: "
                  "il clone è com'era. Non c'è niente da riportare.")
            return 0
        aggiornamenti = _modulo("aggiornamenti_migra", BIN / "aggiornamenti.py")
        if aggiornamenti.processi_claude():
            print("FERMA: chiudi le sessioni di Claude Code e rilancia da un Terminale.", file=sys.stderr)
            return 1
        return indietro(cartella)
    print(f"Uso: {comando_arturo()} migra [--prova] [--unica-macchina] | indietro", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
