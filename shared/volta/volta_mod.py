#!/usr/bin/env python3
"""volta_mod: il mod `arturo` di Volta si aggiorna da solo da un repository git.

La fonte è la cartella `arturo/` di questo repository (ramo `volta`): mods/arturo, layouts, themes e
i lanciatori. Ogni macchina ne tiene un clone leggero in ~/.cache/volta/mod-git e lo confronta con
il mod installato in ~/.config/herdr-app/mods/arturo (file VERSIONE).

  python3 volta_mod.py controlla [--forza]  scarica, controlla e installa se c'è una versione nuova; --forza
                                           non aspetta le ore di un mod installato a mano (volta/dirama.py)
  python3 volta_mod.py installa --da DIR    installa da una cartella `arturo/` locale (prove, /setup)
  python3 volta_mod.py attiva URL [--ramo R]  scrive la sorgente in arturo.json e mette il controllo orario
  python3 volta_mod.py disattiva            toglie il controllo orario e mette "manuale": `attiva URL` riaccende
  python3 volta_mod.py automatico | manuale   accende o spegne il controllo, la sorgente resta
  python3 volta_mod.py stato                l'ultimo esito, in JSON (anche immagini, core, plugin, app e dove sta Arturo)
  python3 volta_mod.py immagini             copia le immagini dei progetti nella cartella dell'app
  python3 volta_mod.py programmi [--subito] il giro di core, plugin e app, come lo fa il sistema
  python3 volta_mod.py specchio             porta l'ultima release dell'app nello specchio locale (app_specchio)
  python3 volta_mod.py prove [--chiudi]     i core di prova rimasti accesi (HC_SESSION diversa da default); --chiudi li chiude
  python3 volta_mod.py diagnosi [--uscita DIR]  archivio zip per capire un guasto: versioni, stati, registro e log,
                                           senza testi né segreti (di serie sulla Scrivania); anche `volta diagnosi`
  python3 volta_mod.py log                  ruota i log dei LaunchAgent oltre LOG_MAX e dice dove stanno i log
  python3 volta_mod.py --prova              esce 0: lo usa la copia vecchia prima di sostituirsi

Perché sta fuori dalla cartella del mod (in ~/.config/herdr-app/volta_mod.py): lo lanciano il mod,
all'apertura e ogni ora, e un'attività del sistema ogni ora. Un mod rotto non blocca così il proprio
aggiornamento.

Regole:
  - acceso solo se arturo.json ha `mod_sorgente` e `mod_modo` non è "manuale";
  - la versione è l'impronta git della cartella `arturo/` (non cambia quando il ramo viene ribasato);
  - la copia nuova passa `herdr-app check` prima dello scambio: se è rossa resta il mod di prima, e
    quella versione non si riprova per RIPROVA_RIFIUTATA ore. Un controllo che non è girato (herdr-app
    assente, timeout, Volta che non risponde) non è un rifiuto: è un errore, e si riprova al giro dopo;
  - lo scambio è una rinomina; il mod di prima resta in volta-mod/prima/. Se il sistema rifiuta la
    rinomina (Windows, file in uso) i file si sostituiscono uno alla volta, main.js e poi VERSIONE per
    ultimi; se la copia si rompe a metà torna il mod di prima;
  - un mod installato a mano con `installa --da` resta TENUTA_LOCALE ore, poi torna quello del repo;
  - keys.json e arturo.json sono della persona: non si toccano;
  - a ogni controllo e a ogni `installa --da` la telemetria di Herdr si spegne in settings.json se il file
    non dice niente (telemetria(), #5932): le app di prima la tenevano accesa e mandavano i dati a
    telemetry.herdr.dev. Un valore scritto dalla persona resta;
  - senza rete o senza accesso al repo l'esito va in mod-stato.json, e il mod lo dice dopo un giorno;
  - a ogni controllo e a ogni `installa --da` le immagini dei progetti (i WebP di
    ~/.claude/data/volta-immagini) si copiano in ~/.config/herdr-app/immagini, dove il mod le apre con
    image("immagini/<slug>.webp"). Si copiano solo le nuove e le cambiate, e si tolgono quelle sparite
    dalla fonte; senza fonte, o con la fonte vuota, non si tocca niente. Una copia che non riesce va in
    immagini-stato.json e non ferma l'aggiornamento del mod. `volta_mod.py immagini` la lancia da sola;
  - se arturo.json ha `immagini_genera` (un argv), ogni controllo lancia quel generatore staccato, senza
    aspettarlo: fa le immagini dei progetti nuovi, e la copia del giro dopo le porta nell'app. La voce sta
    su una macchina sola; l'esito del lancio va in immagini-genera.json;
  - quando lo lancia il sistema (LaunchAgent, attività `controlla --sistema`) aggiorna anche core, plugin
    e app (programmi(), 12/11/2026): core e plugin ogni ora, l'app di notte a computer fermo.
    Dal mod no: un `hc update` o un riavvio dell'app fermerebbero la finestra che lo chiede;
  - nello stesso giro orario la copia di Arturo che il mod legge (`radice` di arturo.json, come
    arturo-herdr) va avanti con un fast-forward, solo se è pulita: un file tracciato modificato, un commit
    suo, un HEAD staccato o un ramo senza remoto la lasciano com'è (esito "ferma"). ~/.claude e una
    cartella dentro un altro repository non si toccano;
  - nello stesso giro del sistema si chiudono i core di prova rimasti (prove(), 14/11/2026): un core
    `--hc-launchd` con un socket di sessione diverso da default.sock (le istanze hzp delle prove), acceso da
    più di PROVA_VECCHIA ore e senza un claude fra i suoi discendenti. SIGTERM ai suoi `hold`, poi al core.
    Il core vero (default) non si tocca mai; un core di cui non si legge il socket nemmeno. Solo macOS e Linux;
  - se arturo.json ha `app_specchio` (il repository GitHub delle release, "proprietario/nome"), lo stesso giro
    del sistema fa da specchio (specchio(), 20/11/2026): `gh release download` porta l'ultima release in
    <cache>/canale/app/<versione>/, controlla sha256 e contenuto, e scrive <cache>/canale/app/latest.json
    con l'indirizzo file://. L'app legge da lì (`app_canale`: file://<cache>/canale). Serve a chi sta fuori
    dalla rete privata; senza la voce è spento e non lascia traccia nello stato;
  - una sorgente https di GitHub si clona con l'accesso di gh, passato a git per comando (accesso_gh()):
    ~/.gitconfig non si tocca. Le sorgenti ssh e file girano come prima;
  - Arturo si trova da `radice` di arturo.json, poi da ~/.claude/arturo/radice, poi dal plugin installato
    (radice_di()). Solo la copia che arturo.json nomina si porta avanti col fast-forward.

Log e diagnosi (step 7, 18/11/2026): a ogni `controlla` i log dei LaunchAgent (LOG_SISTEMA) oltre LOG_MAX
passano a <nome>.1.log, fino a LOG_TENUTI; l'app ruota il suo volta.log da sé (src/applog.rs). Ogni
controllo scrive anche il comando `volta` in ~/.local/bin (comando_volta), mai sopra un `volta` d'altri.

Variabili per i banchi: VOLTA_LOGS (log del sistema), VOLTA_LOG_DIR (log dell'app), VOLTA_LOG_MAX, VOLTA_BIN
(dove va il comando volta), VOLTA_CLAUDE (JSON: l'argv di claude), VOLTA_REGISTRO, HERDR_APP_HOME, VOLTA_CACHE, VOLTA_IMMAGINI (la cartella dei WebP), VOLTA_HERDR_APP (JSON: l'argv di herdr-app),
VOLTA_NO_AGENTE=1 (niente LaunchAgent né schtasks), VOLTA_HC (JSON: l'argv di hc), VOLTA_GH (JSON: l'argv di gh), VOLTA_PLUGINS
(installed_plugins.json), VOLTA_APP_PACCHETTO, VOLTA_ORA, VOLTA_FERMO, VOLTA_CODESIGN (JSON: l'argv di
codesign), VOLTA_FIRME (la cartella delle firme), VOLTA_NO_APRI,
VOLTA_PS (file con l'uscita di ps al posto di ps), VOLTA_SOCKET (JSON pid -> socket al posto di lsof),
VOLTA_RELEASES_URL e HERDR_RELEASES_URL (i canali; quello dell'app di solito da arturo.json, app_canale), VOLTA_RINOMINA_NEGATA=1 (finge il rifiuto della
rinomina), VOLTA_COPIA_ROTTA=<file> (la copia file per file si rompe su quel file), VOLTA_AGENTE_PROVA=<cartella>
(scrive lì il plist, senza launchctl). Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

RAMO = "volta"
CARTELLA = "arturo"            # la cartella del repository che fa da fonte
TENUTA_LOCALE = 6              # ore in cui un mod installato a mano non viene sostituito
RIPROVA_RIFIUTATA = 24         # ore dopo cui una versione col controllo rosso si riprova
# Uscite di `herdr-app check` che dicono "il controllo non è girato", non "il mod è rotto".
NON_GIRATO = ("did not connect", "connection refused", "timed out", "timeout")
LUCCHETTO_VECCHIO = 15 * 60    # secondi: oltre, un lucchetto rimasto si ignora
ATTESA_GIT = 90                # secondi per fetch e clone
ETICHETTA = "org.stellakamikaze.volta.mod"   # LaunchAgent
ATTIVITA = "VoltaCelesteMod"                  # attività pianificata di Windows
# I lanciatori che l'installazione copia accanto al mod: origine nella fonte, nome di arrivo.
# trova-progetti.md è la guida di "Trova i miei progetti": accanto al mod c'è anche dove l'Arturo installato
# non la porta (il plugin pubblico, #6217).
LANCIATORI = (("volta-claude.sh", "volta-claude"), ("nascita.sh", "volta-nascita.sh"),
              ("volta-claude.ps1", "volta-claude.ps1"), ("servizio-claude.ps1", "servizio-claude.ps1"),
              ("trova-progetti.md", "trova-progetti.md"))
# I mod di Arturo tolti: un tasto rimasto su uno di questi non apre più niente (installa-herdr.sh ha lo stesso elenco).
TASTI_VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")
# Comandi nati dopo le prime installazioni: il giro fra le sessioni (⌘↓ e ⌘↑, 12/11/2026). Ctrl+W su
# Windows e ⌘W sul Mac stanno in PRENDE (arturo.volta-chiudi). Ctrl+Maiusc+W di Herdr resta.
# La Coda delle decisioni (⌘⇧J, Ctrl+Shift+J su Windows, #5720, 15/11/2026).
# La checklist della ripartenza (⌘⇧S, Ctrl+Shift+S su Windows, 17/11/2026).
# ⌘Z (Ctrl+Alt+Z su Windows) annulla la chiusura di una sessione nei primi 10 s (#5883, 17/11/2026).
TASTI_NUOVI = ("arturo.muto", "arturo.volta-giro-avanti", "arturo.volta-giro-indietro", "arturo.coda", "arturo.checklist", "arturo.volta-annulla")
# Tasti nuovi di un comando che c'era già: ⌘K apre la stessa ricerca di ⌘O (#5369). Si offre il solo tasto:
# un ⌘O tolto dalla persona non torna.
TASTI_AGGIUNTI = (("cmd-k", "arturo.apri"),)
# Comandi che la fonte ha spostato: il tasto che li porta ancora prende il comando nuovo della fonte. ⌘T
# (ctrl-shift-t) apre le tessere dei progetti, e "Nuova richiesta" è la prima tessera (12/11/2026, #5371).
TASTI_SPOSTATI = ("arturo.volta-nuova",)
# Il tasto che Arturo prende a Herdr (installa-herdr.sh ha lo stesso): la scheda nuova di Herdr (tab.new,
# una shell) diventa le tessere dei progetti, se quel tasto fa ancora la scheda di Herdr o manca (#5290).
# ⌘N (Ctrl+Shift+N su Windows) apre il compito nuovo (#6186, 20/11/2026) e prende lo spazio nuovo di Herdr
# (space.new), che resta nel menu File: in Volta gli spazi nascono dai progetti.
PRENDE = {"arturo.casa": ("tab.new",), "arturo.volta-chiudi": ("tab.close",), "arturo.compito": ("space.new",)}
# ⌘W e Ctrl+W chiudono la sessione davanti col congedo e la tolgono subito da elenco e giro
# (12/11/2026 sera): prendono il tab.close di Herdr. Il registro li segna per tasto e comando, perché su
# Windows "global ctrl-w" era già segnato da quando Ctrl+W faceva tab.close (TASTI_NUOVI di prima).
# Lo stesso per ⌘N e Ctrl+Shift+N (#6186): "global cmd-n" era già segnato come tasto di serie di Herdr, e col
# solo tasto il compito nuovo non arrivava a chi ha già Volta (sonda del 20/11/2026 su due Mac).
REGISTRO_PER_COMANDO = ("arturo.volta-chiudi", "arturo.compito")
# I tasti di serie di Herdr, copie di defaults/ (il banco VM36 le confronta). Herdr li scrive in keys.json
# solo se il file manca: un keys.json scritto prima del primo avvio (installa-herdr.sh fino al 12/11/2026)
# aveva i soli tasti di Arturo, e mancavano ⌘W, ⌘C, ⌘V e gli altri.
TASTI_SERIE = "keys-herdr-macos.json" if sys.platform == "darwin" else "keys-herdr.json"
# La cartella dell'app dove arrivano le immagini dei progetti (tessere di Volta, 12/11/2026).
IMMAGINI = "immagini"


def app_home() -> Path:
    return Path(os.environ.get("HERDR_APP_HOME") or Path.home() / ".config" / "herdr-app")


def cache() -> Path:
    """La cartella di Volta, come cacheVolta() di dati.js: VOLTA_CACHE (banchi), altrimenti ~/.cache/volta
    per la finestra vera e <HERDR_APP_HOME>/cache/volta per una finestra di prova, che così non scrive
    i file della vera (#5449)."""
    if os.environ.get("VOLTA_CACHE"):
        return Path(os.environ["VOLTA_CACHE"])
    serie = Path.home() / ".config" / "herdr-app"
    app = Path(os.environ.get("HERDR_APP_HOME") or serie)
    if os.path.normcase(os.path.abspath(app)) != os.path.normcase(os.path.abspath(serie)):
        return app / "cache" / "volta"
    return Path.home() / ".cache" / "volta"


def leggi(f: Path) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def config() -> dict:
    return leggi(app_home() / "arturo.json")


def stato_file() -> Path:
    return cache() / "mod-stato.json"


def segna(esito: str, **altro) -> dict:
    """L'esito dell'ultimo controllo. `giu_da` resta dal primo errore di fila, per l'avviso del mod."""
    prima = leggi(stato_file())
    d = {"esito": esito, "controllato": time.time(), **altro}
    if esito == "errore":
        d["giu_da"] = prima.get("giu_da") or d["controllato"]
    if esito != "aggiornato":  # un'installazione riuscita chiude ogni rifiuto di prima
        for k in ("rifiutata", "rifiutata_il"):
            if k in prima and k not in d:
                d[k] = prima[k]
    scrivi(stato_file(), d)
    return d


# Il programma git, come elenco di argomenti. VOLTA_GIT (JSON) lo cambia: serve al banco.
try:
    GIT = [str(x) for x in json.loads(os.environ.get("VOLTA_GIT") or '["git"]')] or ["git"]
except (ValueError, TypeError):
    GIT = ["git"]


def ssh_di_git() -> str:
    """L'ssh che la macchina ha scelto per git (core.sshCommand), altrimenti "ssh". GIT_SSH_COMMAND batte
    core.sshCommand: su Windows un "ssh" nudo prende quello di Git for Windows, che non vede l'agente di Windows
    dove sta la chiave, e GitHub rifiuta (il PC Windows dello studio, 11/11/2026)."""
    try:
        r = subprocess.run(GIT + ["config", "--get", "core.sshCommand"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "ssh"
    return (r.stdout or "").strip() or "ssh"


GITHUB_HTTPS = "https://github.com/"
SENZA_GH = "gh non c'è: installa GitHub CLI (brew install gh) e lancia gh auth login"


def accesso_gh(url: str) -> list:
    """Gli argomenti che danno a git l'accesso di gh per un repository https di GitHub (#6217, 20/11/2026):
    i tester clonano il repository privato della distribuzione senza chiave ssh. L'aiutante delle credenziali
    passa per comando, con `-c`: ~/.gitconfig non si tocca, e `gh auth setup-git` non serve. Il primo `-c`
    vuoto toglie gli aiutanti della macchina (il portachiavi può avere un accesso vecchio), il secondo mette
    quello di gh. Per ogni altro indirizzo (ssh, file, un altro sito) e senza gh torna un elenco vuoto: lì
    git gira com'era."""
    if not url.lower().startswith(GITHUB_HTTPS):
        return []
    gh = argv_di("VOLTA_GH", "gh")
    if not gh:
        return []
    import shlex
    aiutante = "!" + " ".join(shlex.quote(str(x)) for x in gh + ["auth", "git-credential"])
    return ["-c", "credential.%s.helper=" % GITHUB_HTTPS.rstrip("/"),
            "-c", "credential.%s.helper=%s" % (GITHUB_HTTPS.rstrip("/"), aiutante)]


def git(args: list, cwd: Path | None = None, timeout: int = ATTESA_GIT, prima: list | None = None) -> tuple[int, str]:
    """`prima`: argomenti di git da mettere davanti al comando (accesso_gh)."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", ssh_di_git() + " -o BatchMode=yes -o ConnectTimeout=15")
    # git parte in un gruppo suo: allo scadere del tempo si chiude tutto il gruppo, figli compresi.
    suo = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        p = subprocess.Popen(GIT + (prima or []) + args, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=env, **suo)
    except OSError as e:
        return 127, "git non parte: %s" % e
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        ferma(p)
        return 124, "git %s non ha risposto in %d s" % (args[0], timeout)
    return p.returncode, (out or "").strip() if p.returncode == 0 else ((err or out or "").strip() or "rc %d" % p.returncode)


def ferma(p) -> None:
    """Chiude un git scaduto insieme ai suoi figli. Chiudere il solo git non basta: l'ssh che ha lanciato
    resta vivo e tiene aperta l'uscita, e su Windows chi la legge resta ad aspettare senza fine (sul PC
    Windows un controllo è rimasto appeso nove minuti, 11/11/2026). Poi non aspetta oltre 5 secondi."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True,
                           stdin=subprocess.DEVNULL, timeout=15)
        else:
            os.killpg(p.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        p.kill()
    except OSError:
        pass
    try:
        p.communicate(timeout=5)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        for f in (p.stdout, p.stderr):
            try:
                f.close()
            except (OSError, AttributeError):
                pass


def ultima_riga(testo: str) -> str:
    righe = [x.strip() for x in testo.splitlines() if x.strip()]
    return righe[-1][:200] if righe else ""


def togli(cartella: Path) -> None:
    """Cancella una cartella anche se dentro ci sono file o cartelle di sola lettura. Su Windows git scrive
    così i suoi oggetti e shutil.rmtree li lascia lì: il clone da rifare restava a metà, git clone
    rispondeva "already exists and is not an empty directory" e ogni giro dopo dava lo stesso errore
    (PC Windows, 12/11/2026). Quello che non si riesce a togliere resta, senza eccezioni."""
    def riprova(funzione, percorso, _errore):
        try:
            os.chmod(os.path.dirname(percorso), stat.S_IRWXU)
            os.chmod(percorso, stat.S_IRWXU)
            funzione(percorso)
        except OSError:
            pass
    if sys.version_info >= (3, 12):
        shutil.rmtree(str(cartella), onexc=riprova)
    else:
        shutil.rmtree(str(cartella), onerror=riprova)


def scarica(url: str, ramo: str) -> tuple[Path | None, str]:
    """Il clone leggero allineato al ramo. Torna (cartella della fonte, "") oppure (None, motivo)."""
    clone = cache() / "mod-git"
    accesso = accesso_gh(url)

    def clona() -> str:
        togli(clone)
        clone.parent.mkdir(parents=True, exist_ok=True)
        rc, out = git(["clone", "--quiet", "--filter=blob:none", "--sparse", "--depth", "1", "--branch", ramo,
                       url, str(clone)], timeout=ATTESA_GIT * 2, prima=accesso)
        if rc != 0:
            togli(clone)
            return ultima_riga(out) or "clone fallito"
        # --no-cone: solo la cartella della fonte, senza i file della radice del repository
        rc, out = git(["sparse-checkout", "set", "--no-cone", "/" + CARTELLA + "/"], cwd=clone)
        return "" if rc == 0 else (ultima_riga(out) or "sparse-checkout fallito")

    def allinea() -> str:
        git(["remote", "set-url", "origin", url], cwd=clone)
        rc, out = git(["fetch", "--quiet", "--depth", "1", "origin", ramo], cwd=clone, prima=accesso)
        if rc == 0:
            rc, out = git(["reset", "--quiet", "--hard", "FETCH_HEAD"], cwd=clone)
        return "" if rc == 0 else (ultima_riga(out) or "fetch fallito")

    if (clone / ".git").exists():
        motivo = allinea()
        if motivo:
            # Un clone rimasto a metà (index.lock di un git ucciso dal timeout) non guarisce da solo:
            # si butta e si rifà, una volta. Senza rete fallisce anche il clone, e il motivo è il suo.
            motivo = clona()
    else:
        motivo = clona()
    if motivo:
        if url.lower().startswith(GITHUB_HTTPS) and not accesso:
            motivo += " · " + SENZA_GH
        return None, motivo
    if not (clone / CARTELLA / "mods" / "arturo" / "main.js").is_file():
        return None, "nel ramo %s non c'è %s/mods/arturo" % (ramo, CARTELLA)
    return clone / CARTELLA, ""


def versione_di(clone: Path) -> dict:
    """L'impronta della cartella della fonte: resta la stessa quando il ramo viene ribasato."""
    _, albero = git(["rev-parse", "HEAD:" + CARTELLA], cwd=clone)
    _, commit = git(["rev-parse", "--short", "HEAD"], cwd=clone)
    _, data = git(["log", "-1", "--format=%cI"], cwd=clone)
    return {"versione": albero, "corta": albero[:7], "commit": commit, "data": data}


def volta_installata() -> list:
    """Dove sta l'eseguibile di Volta quando è installata: `Volta.app` nelle Applicazioni della persona sui
    Mac, `Programs\\volta-celeste` su Windows (volta/installa-windows.ps1)."""
    if os.name == "nt":
        locale = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return [Path(locale) / "Programs" / "volta-celeste" / "herdr-app.exe"]
    return [Path.home() / "Applications" / APP_NUOVA / "Contents" / "MacOS" / "Volta"]


def herdr_app() -> list | None:
    """Il programma di Volta come elenco di argomenti: la variabile del banco, poi la Volta installata, poi
    `herdr-app` nel PATH o in ~/.local/bin. La Volta installata viene prima del PATH: dove c'è anche Herdr,
    il suo `herdr-app` boccia il mod di Volta e la versione resta rifiutata per un giorno (#6233)."""
    finto = os.environ.get("VOLTA_HERDR_APP")
    if finto:
        return json.loads(finto)
    for exe in volta_installata():
        if exe.is_file():
            return [str(exe)]
    fine = ".exe" if os.name == "nt" else ""
    trovato = shutil.which("herdr-app") or str(Path.home() / ".local" / "bin" / ("herdr-app" + fine))
    return [trovato] if os.path.exists(trovato) else None


def controlla_mod(cartella: Path) -> tuple[str, bool]:
    """("", False) se `herdr-app check` passa sulla copia, altrimenti (motivo, rosso). `rosso` è vero solo
    se il controllo è girato e ha bocciato il mod: herdr-app assente, un timeout o una Volta che non
    risponde dicono che il controllo non è girato, e quella versione si riprova al giro dopo."""
    argv = herdr_app()
    if not argv:
        return "non trovo herdr-app per controllare il mod", False
    try:
        r = subprocess.run(argv + ["check", str(cartella)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        return "herdr-app check non parte: %s" % str(e)[:160], False
    if r.returncode == 0:
        return "", False
    motivo = ultima_riga((r.stdout or "") + "\n" + (r.stderr or "")) or "check rosso"
    return motivo, not any(x in motivo.lower() for x in NON_GIRATO)


def file_di(radice: Path) -> list:
    return sorted(str(p.relative_to(radice)) for p in radice.rglob("*") if p.is_file())


def un_file_alla_volta(nuovo: Path, mod: Path, rotta: str = "") -> None:
    """Il ripiego quando la rinomina della cartella è rifiutata: main.js per ultimo, così il mod
    ricarica una volta sola, a copia finita, e VERSIONE dopo di lui: una copia rotta a metà non si
    dichiara mai nuova. I file che non ci sono più si tolgono."""
    nuovi = file_di(nuovo)
    for rel in sorted(nuovi, key=lambda r: (r == "VERSIONE", r == "main.js", r)):
        if rotta and rel == rotta:
            raise PermissionError("copia rotta su %s (prova)" % rel)
        arrivo = mod / rel
        arrivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = arrivo.with_name(arrivo.name + ".nuovo")
        shutil.copyfile(str(nuovo / rel), str(tmp))  # data di adesso: main.js risulta l'ultimo scritto
        os.replace(str(tmp), str(arrivo))
    for rel in file_di(mod):
        if rel not in nuovi and "__pycache__" not in rel:
            try:
                (mod / rel).unlink()
            except OSError:
                pass


def scambia(nuovo: Path, mod: Path, prima: Path) -> str:
    """Mette `nuovo` al posto di `mod`. Torna come: "rinomina" o "file"."""
    if not mod.exists():
        mod.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(nuovo), str(mod))
        return "rinomina"
    shutil.rmtree(prima, ignore_errors=True)
    prima.parent.mkdir(parents=True, exist_ok=True)
    try:
        if os.environ.get("VOLTA_RINOMINA_NEGATA"):
            raise PermissionError("rinomina negata (prova)")
        os.replace(str(mod), str(prima))
    except OSError:
        shutil.copytree(str(mod), str(prima), ignore=shutil.ignore_patterns("__pycache__"))
        try:
            un_file_alla_volta(nuovo, mod, os.environ.get("VOLTA_COPIA_ROTTA") or "")
        except OSError:
            un_file_alla_volta(prima, mod)  # torna il mod di prima, intero
            raise
        shutil.rmtree(nuovo, ignore_errors=True)
        return "file"
    try:
        os.replace(str(nuovo), str(mod))
    except OSError:
        os.replace(str(prima), str(mod))  # torna il mod di prima
        raise
    return "rinomina"


def sostituisci(origine: Path, arrivo: Path) -> None:
    """Copia accanto e rinomina: chi sta leggendo o eseguendo il file di prima (una shell dentro
    volta-claude) tiene il suo, intero, e non legge pezzi di quello nuovo."""
    arrivo.parent.mkdir(parents=True, exist_ok=True)
    tmp = arrivo.with_name(arrivo.name + ".%d.nuovo" % os.getpid())
    shutil.copy2(str(origine), str(tmp))
    try:
        os.replace(str(tmp), str(arrivo))
    except OSError:
        # Windows rifiuta la rinomina sopra un file che un altro programma tiene aperto: lì si copia sul posto.
        try:
            shutil.copy2(str(origine), str(arrivo))
        finally:
            tmp.unlink(missing_ok=True)


def tasti(fonte: Path) -> int:
    """Riallinea i tasti di Arturo rimasti su un mod tolto: prendono il comando che la fonte dà a quel
    tasto. I comandi di TASTI_NUOVI entrano anche in un'installazione che c'è già, se il loro tasto è
    libero, e il tasto di PRENDE se fa ancora il comando di Herdr. Poi i tasti di serie di Herdr che
    mancano (TASTI_SERIE). Un tasto nuovo, preso o di serie si offre una volta sola: il registro
    volta-mod/tasti-offerti.json lo segna anche quando c'è già, così un tasto tolto dalla persona non
    torna. Ogni altro tasto resta della persona, e senza un tasto da cambiare keys.json non si riscrive.
    Senza keys.json non si tocca niente: al primo avvio Herdr scrive i suoi."""
    nuovi = leggi(fonte / ("keys.json" if sys.platform == "darwin" else "keys-ctrl.json"))
    serie = leggi(fonte / TASTI_SERIE)
    f = app_home() / "keys.json"
    miei = leggi(f)
    registro = app_home() / "volta-mod" / "tasti-offerti.json"
    visti = set(leggi(registro).get("tasti") or [])
    prima = set(visti)
    quanti = 0
    for sezione, voci in nuovi.items():
        mia = miei.get(sezione)
        if not isinstance(voci, dict) or not isinstance(mia, dict):
            continue
        for tasto, comando in voci.items():
            chiave = ("%s %s %s" % (sezione, tasto, comando)) if comando in REGISTRO_PER_COMANDO else ("%s %s" % (sezione, tasto))
            if mia.get(tasto) in TASTI_VECCHI or (mia.get(tasto) in TASTI_SPOSTATI and comando != mia.get(tasto)):
                mia[tasto] = comando
                quanti += 1
            elif tasto not in mia and (comando in TASTI_NUOVI or (tasto, comando) in TASTI_AGGIUNTI):
                if chiave not in visti:
                    mia[tasto] = comando
                    quanti += 1
            elif comando in PRENDE and mia.get(tasto, PRENDE[comando][0]) in PRENDE[comando] and chiave not in visti:
                # anche col tasto che manca: quello di serie sarebbe il comando di Herdr che si prende
                mia[tasto] = comando
                quanti += 1
            if comando in TASTI_NUOVI or (tasto, comando) in TASTI_AGGIUNTI or comando in PRENDE:
                visti.add(chiave)
    for sezione, voci in serie.items() if miei else ():
        if not isinstance(voci, dict) or not isinstance(miei.get(sezione, {}), dict):
            continue
        for tasto, comando in voci.items():
            chiave = "%s %s" % (sezione, tasto)
            if chiave in visti:
                continue
            visti.add(chiave)
            if tasto not in miei.get(sezione, {}):
                miei.setdefault(sezione, {})[tasto] = comando
                quanti += 1
    if quanti:
        scrivi(f, miei)
    if visti != prima:
        scrivi(registro, {"tasti": sorted(visti)})
    return quanti


def contorno(fonte: Path) -> None:
    """Layout, temi, firme e lanciatori accanto al mod. arturo.json resta della persona, e così keys.json,
    salvo i tasti rimasti su un mod di Arturo tolto. Le firme (#6244) vanno prima di volta_mod.py, che le legge."""
    app = app_home()
    for nome in ("layouts", "themes", "firme"):
        for f in sorted((fonte / nome).glob("*")) if (fonte / nome).is_dir() else []:
            if f.is_file():
                sostituisci(f, app / nome / f.name)
    for origine, arrivo in LANCIATORI:
        if origine.endswith(".ps1") and os.name != "nt":
            continue
        if (fonte / origine).is_file():
            sostituisci(fonte / origine, app / arrivo)
    try:
        tasti(fonte)
    except OSError:
        pass  # keys.json non scrivibile: il mod è già a posto, il tasto aspetta la prossima installazione
    # Questo script si sostituisce solo con una copia che parte.
    io_nuovo = fonte / "volta_mod.py"
    if io_nuovo.is_file():
        try:
            parte = subprocess.run([sys.executable, str(io_nuovo), "--prova"], capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.SubprocessError):
            parte = False
        if parte:
            sostituisci(io_nuovo, app / "volta_mod.py")


def fonte_immagini() -> Path:
    return Path(os.environ.get("VOLTA_IMMAGINI") or Path.home() / ".claude" / "data" / "volta-immagini")


def immagini() -> dict:
    """Porta i WebP dei progetti nella cartella dell'app. Un file con la stessa dimensione e la stessa data
    di quello arrivato prima non si riscrive; uno cambiato passa da sostituisci(), così il mod che lo sta
    leggendo tiene quello di prima, intero. Si tolgono solo i .webp spariti dalla fonte. Senza la fonte, o
    con la fonte vuota (dati non ancora scaricati su questa macchina), non si tocca niente: le tessere non
    devono svuotarsi per una cartella che manca."""
    fonte = fonte_immagini()
    arrivo = app_home() / IMMAGINI
    nuove = {f.name: f for f in fonte.glob("*.webp") if f.is_file()} if fonte.is_dir() else {}
    if not nuove:
        return {"esito": "fonte vuota" if fonte.is_dir() else "nessuna fonte", "fonte": str(fonte), "copiate": 0, "tolte": 0}
    copiate = tolte = 0
    for nome, f in sorted(nuove.items()):
        dove = arrivo / nome
        s = f.stat()
        try:
            d = dove.stat()
            if d.st_size == s.st_size and int(d.st_mtime) == int(s.st_mtime):
                continue
        except OSError:
            pass
        sostituisci(f, dove)
        copiate += 1
    for vecchia in sorted(arrivo.glob("*.webp")):
        if vecchia.name not in nuove:
            vecchia.unlink()
            tolte += 1
    # L'elenco degli slug arrivati: le tessere (casa.js) mostrano l'immagine solo di chi c'è, e le iniziali
    # per gli altri. Si riscrive solo se cambia.
    elenco = arrivo / "elenco.json"
    testo = json.dumps(sorted(Path(n).stem for n in nuove), ensure_ascii=False) + "\n"
    try:
        prima = elenco.read_text(encoding="utf-8")
    except OSError:
        prima = None
    if prima != testo:
        tmp = elenco.with_name("elenco.json.%d.nuovo" % os.getpid())
        tmp.write_text(testo, encoding="utf-8")
        os.replace(str(tmp), str(elenco))
    return {"esito": "ok", "fonte": str(fonte), "copiate": copiate, "tolte": tolte, "totale": len(nuove)}


def passo_immagini() -> dict:
    """immagini() con l'esito in immagini-stato.json. Un guasto qui non ferma l'aggiornamento del mod."""
    try:
        d = immagini()
    except Exception as e:  # noqa: BLE001 le immagini sono un contorno: il mod va avanti anche senza
        d = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160])}
    d["controllato"] = time.time()
    try:
        scrivi(cache() / "immagini-stato.json", d)
    except OSError:
        pass
    if d["esito"] == "errore":
        print("IMMAGINI: errore, %s" % d["motivo"])
    elif d.get("copiate") or d.get("tolte"):
        print("IMMAGINI: %d copiate, %d tolte, %d in tutto" % (d["copiate"], d["tolte"], d["totale"]))
    return d


def telemetria() -> bool:
    """Spegne la telemetria di Herdr nelle installazioni di prima (#5932, 17/11/2026). Le app costruite fino
    al 17/11 la tengono accesa quando settings.json non dice niente, e mandano un rapporto al giorno a
    telemetry.herdr.dev: qui la voce mancante diventa "telemetry": false, anche in un settings.json che non
    c'è ancora. Un valore scritto dalla persona resta suo (le build nuove non mandano comunque niente), e un
    file che non si legge come JSON non si tocca. Torna vero se ha scritto."""
    f = app_home() / "settings.json"
    try:
        testo = f.read_text(encoding="utf-8") if f.exists() else "{}"
        dati = json.loads(testo or "{}")
    except (OSError, ValueError):
        return False
    if not isinstance(dati, dict) or "telemetry" in dati:
        return False
    dati["telemetry"] = False
    try:
        scrivi(f, dati)
    except OSError:
        return False
    print("TELEMETRIA: spenta quella di Herdr in settings.json")
    return True


def passo_genera() -> dict:
    """Lancia staccato il generatore delle immagini dei progetti nuovi, se arturo.json lo indica con
    `immagini_genera` (l'argv, con ~ per la casa: per esempio volta-immagini.py nuovi --max 3). Non lo
    aspetta: le immagini nuove arrivano nell'app al giro dopo. Il generatore tiene il suo lucchetto, così
    due giri vicini (mod e sistema) non lo fanno girare due volte. Senza la voce non parte niente: la voce
    va solo sulla macchina che genera, perché due macchine farebbero due immagini dello stesso progetto."""
    argv = config().get("immagini_genera")
    if not argv:
        return {"esito": "spento"}
    if not isinstance(argv, list) or not all(isinstance(x, str) and x for x in argv):
        d = {"esito": "errore", "motivo": "immagini_genera non è un elenco di parole: %s" % str(argv)[:80]}
    else:
        argv = [os.path.expanduser(x) for x in argv]
        staccato = ({"creationflags": getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
                    if os.name == "nt" else {"start_new_session": True})
        try:
            cache().mkdir(parents=True, exist_ok=True)
            with open(cache() / "immagini-genera.log", "ab") as log:
                p = subprocess.Popen(argv, stdout=log, stderr=log, stdin=subprocess.DEVNULL, close_fds=True, **staccato)
            d = {"esito": "lanciato", "pid": p.pid, "argv": argv}
        except OSError as e:
            d = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160])}
    d["controllato"] = time.time()
    try:
        scrivi(cache() / "immagini-genera.json", d)
    except OSError:
        pass
    if d["esito"] == "errore":
        print("GENERA: errore, %s" % d["motivo"])
    return d


def installa(fonte: Path, versione: dict) -> tuple[bool, str, bool]:
    """Copia, controlla e scambia. Torna (riuscito, come o motivo, rosso): `rosso` è vero solo se il
    controllo del mod è girato e l'ha bocciato."""
    app = app_home()
    sorgente = fonte / "mods" / "arturo"
    if not (sorgente / "main.js").is_file():
        return False, "in %s non c'è mods/arturo" % fonte, False
    nuovo = app / "volta-mod" / "nuovo" / "arturo"
    shutil.rmtree(nuovo.parent, ignore_errors=True)
    try:
        shutil.copytree(str(sorgente), str(nuovo), ignore=shutil.ignore_patterns("__pycache__", "VERSIONE"))
        scrivi(nuovo / "VERSIONE", dict(versione, installato=time.time()))
        motivo, rosso = controlla_mod(nuovo)
        if motivo:
            return False, motivo, rosso
        come = scambia(nuovo, app / "mods" / "arturo", app / "volta-mod" / "prima" / "arturo")
    finally:
        shutil.rmtree(nuovo.parent, ignore_errors=True)
    contorno(fonte)
    return True, come, False


def lucchetto() -> Path | None:
    l = cache() / "mod.lucchetto"
    l.parent.mkdir(parents=True, exist_ok=True)
    try:
        if l.exists() and time.time() - l.stat().st_mtime > LUCCHETTO_VECCHIO:
            l.rmdir()
        l.mkdir()
        return l
    except OSError:
        return None


def cmd_controlla(forza: bool = False) -> int:
    c = config()
    url = c.get("mod_sorgente")
    if not isinstance(url, str) or not url:
        print("SPENTO: arturo.json non ha mod_sorgente")
        return 0
    if c.get("mod_modo") == "manuale":
        print("MANUALE: il controllo è spento (volta_mod.py automatico lo riaccende)")
        return 0
    agente_aggiorna()
    l = lucchetto()
    if l is None:
        print("OCCUPATO: un altro controllo è in corso")
        return 0
    try:
        passo_immagini()
        passo_genera()
        telemetria()
        comando_volta()
        installato = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        v = str(installato.get("versione") or "")
        messo = float(installato.get("installato") or 0)
        if v.startswith("locale") and time.time() - messo < TENUTA_LOCALE * 3600 and not forza:
            segna("locale", versione="locale", fino=messo + TENUTA_LOCALE * 3600)
            print("LOCALE: il mod è stato installato a mano, lo tengo per %d ore" % TENUTA_LOCALE)
            return 0
        fonte, motivo = scarica(url, str(c.get("mod_ramo") or RAMO))
        if fonte is None:
            segna("errore", motivo=motivo)
            print("ERRORE: " + motivo)
            return 1
        versione = versione_di(fonte.parent)
        if versione["versione"] == v:
            # I tasti si riallineano anche qui: alla versione nuova il controllo gira ancora con lo script
            # di prima, e un tasto nuovo (⌘K, #5369) arrivava solo alla versione dopo (#5470).
            try:
                tasti(fonte)
            except OSError:
                pass
            segna("allineato", versione=versione["corta"])
            print("ALLINEATO %s" % versione["corta"])
            return 0
        prima = leggi(stato_file())
        if prima.get("rifiutata") == versione["versione"]:
            # Senza data (stato scritto da uno script di prima) vale come appena rifiutata.
            il = float(prima.get("rifiutata_il") or 0) or time.time()
            if time.time() - il < RIPROVA_RIFIUTATA * 3600:
                segna("rifiutato", versione=versione["corta"], motivo=prima.get("motivo") or "", rifiutata_il=il)
                print("RIFIUTATA %s: il controllo del mod era rosso, la riprovo fra %d ore o con una versione nuova"
                      % (versione["corta"], RIPROVA_RIFIUTATA))
                return 1
        riuscito, come, rosso = installa(fonte, versione)
        if not riuscito and rosso:
            segna("rifiutato", versione=versione["corta"], motivo=come, rifiutata=versione["versione"], rifiutata_il=time.time())
            print("RIFIUTATO %s: %s" % (versione["corta"], come))
            return 1
        if not riuscito:
            segna("errore", versione=versione["corta"], motivo=come)
            print("ERRORE: il controllo del mod non è girato (%s), riprovo al prossimo giro" % come)
            return 1
        segna("aggiornato", versione=versione["corta"], come=come, aggiornato=time.time())
        print("AGGIORNATO %s (%s)" % (versione["corta"], come))
        return 0
    except Exception as e:  # noqa: BLE001 lo stato deve dire anche il guasto che nessuno aveva previsto
        segna("errore", motivo="%s: %s" % (type(e).__name__, str(e)[:160]))
        print("ERRORE: %s: %s" % (type(e).__name__, e))
        return 1
    finally:
        try:
            l.rmdir()
        except OSError:
            pass


def cmd_installa(argv: list) -> int:
    if len(argv) != 2 or argv[0] != "--da":
        print("uso: volta_mod.py installa --da <cartella arturo/>")
        return 2
    l = lucchetto()
    if l is None:
        print("OCCUPATO: un controllo è in corso, riprova fra poco")
        return 1
    try:
        adesso = time.time()
        riuscito, come, _ = installa(Path(argv[1]).resolve(), {"versione": "locale:%d" % adesso, "corta": "locale", "commit": "", "data": ""})
        if riuscito:
            segna("locale", versione="locale", fino=adesso + TENUTA_LOCALE * 3600)
            passo_immagini()
            telemetria()
            comando_volta()
        print(("INSTALLATO a mano (%s): resta %d ore" % (come, TENUTA_LOCALE)) if riuscito else "NON INSTALLATO: " + come)
        return 0 if riuscito else 1
    except Exception as e:  # noqa: BLE001
        segna("errore", motivo="installa --da: %s: %s" % (type(e).__name__, str(e)[:160]))
        print("NON INSTALLATO: %s: %s" % (type(e).__name__, e))
        return 1
    finally:
        try:
            l.rmdir()
        except OSError:
            pass


# --- Core, plugin e app (passo 5 del piano del 12/11/2026, #5370) ---------------------------------------
# Il mod si aggiorna dal suo repository; qui si aggiornano gli altri tre pezzi. Solo quando lancia il
# sistema (LaunchAgent o attività pianificata): dentro il mod un `hc update` o un riavvio dell'app
# fermerebbero la finestra che lo sta chiedendo.

# Secondi fra due giri di core, plugin e copia di Arturo. Il sistema lancia ogni ora: 50 minuti tengono il
# giro orario anche quando l'ora fra due lanci esce di qualche secondo più corta (12/11/2026, #5442).
OGNI_PROGRAMMI = 50 * 60
FASCIA_APP = (2, 6)               # ore locali in cui l'app può riavviarsi
FERMO_APP = 30 * 60               # secondi senza tastiera né mouse prima di riavviare l'app
APP_NUOVA = "Volta.app"           # il nome del pacchetto dal 12/11/2026
APP_VECCHIA = "Volta Celeste.app"
# Il canale dell'app sta in arturo.json (`app_canale`), come VOLTA_RELEASES in src/update.rs: è un indirizzo
# della rete privata e non va scritto in un repository pubblico.


def programmi_file() -> Path:
    return cache() / "programmi-stato.json"


def dal_sistema(argv: list) -> bool:
    """Vero se il controllo lo lancia il sistema: il LaunchAgent (XPC_SERVICE_NAME è la sua etichetta) o
    l'attività di Windows (`controlla --sistema`)."""
    return os.environ.get("XPC_SERVICE_NAME") == ETICHETTA or "--sistema" in argv


def argv_di(variabile: str, nome: str) -> list | None:
    """Un programma come elenco di argomenti: la variabile del banco (JSON), oppure il nome nel PATH o in
    ~/.local/bin. None se non c'è."""
    finto = os.environ.get(variabile)
    if finto:
        return json.loads(finto)
    fine = ".exe" if os.name == "nt" else ""
    trovato = shutil.which(nome) or str(Path.home() / ".local" / "bin" / (nome + fine))
    return [trovato] if os.path.exists(trovato) else None


def corri(argv: list, timeout: int, env: dict | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return 124, "%s non ha risposto in %d s" % (Path(str(argv[0])).name, timeout)
    except OSError as e:
        return 127, "%s non parte: %s" % (Path(str(argv[0])).name, e)
    return r.returncode, ((r.stdout or "") + "\n" + (r.stderr or "")).strip()


def apri_url(url: str, timeout: int):
    """Un indirizzo col nome di questo script: il canale di Herdr rifiuta con 403 il client di Python
    senza nome (Python-urllib), e il core non si aggiornava mai (12/11/2026)."""
    import urllib.request
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "volta-mod"}), timeout=timeout)  # noqa: S310


def scarica_testo(url: str, timeout: int = 30) -> str:
    with apri_url(url, timeout) as r:
        return r.read().decode("utf-8")


def piu_nuova(a: str, b: str) -> bool:
    """`a` viene dopo `b` (0.1.20 dopo 0.1.9; 0.2.0-rc.1 prima di 0.2.0). Come `newer` di src/update.rs."""
    def parti(v: str):
        v = v.strip().lstrip("v")
        base, _, pre = v.partition("-")
        numeri = []
        for x in base.split("."):
            try:
                numeri.append(int(x))
            except ValueError:
                numeri.append(0)
        return numeri, pre
    (na, pa), (nb, pb) = parti(a), parti(b)
    if na != nb:
        return na > nb
    return (not pa and bool(pb)) or (bool(pa) and bool(pb) and pa > pb)


def core() -> dict:
    """Il core che gira (`hc server status`, non `hc --version`: il binario può essere già nuovo e la
    memoria no) contro core/latest.json di Herdr. Solo verso una versione più nuova; mai --force, mai
    `hc server stop`. Un core di un gestore di pacchetti (Homebrew) resta a lui."""
    hc = argv_di("VOLTA_HC", "hc")
    if not hc:
        return {"esito": "assente"}
    rc, out = corri(hc + ["server", "status"], 30)
    try:
        s = json.loads(out.strip().splitlines()[-1]) if rc == 0 and out.strip() else {}
    except ValueError:
        s = {}
    gira = str(s.get("version") or "")
    if not gira:
        return {"esito": "spento", "motivo": ultima_riga(out)}
    if s.get("installed_by"):
        return {"esito": "gestito", "versione": gira, "da": s["installed_by"]}
    base = os.environ.get("HERDR_RELEASES_URL") or "https://releases.herdr.dev"
    try:
        ultima = str(json.loads(scarica_testo(base.rstrip("/") + "/core/latest.json")).get("version") or "")
    except Exception as e:  # noqa: BLE001 senza rete il giro dopo riprova
        return {"esito": "errore", "versione": gira, "motivo": "core/latest.json: %s" % str(e)[:160]}
    if not ultima or not piu_nuova(ultima, gira):
        return {"esito": "allineato", "versione": gira}
    rc, out = corri(hc + ["update", "--version", ultima, "--json"], 300)
    if rc != 0:
        return {"esito": "errore", "versione": gira, "verso": ultima, "motivo": ultima_riga(out)}
    return {"esito": "aggiornato", "versione": ultima, "prima": gira}


def plugin(prima: dict) -> dict:
    """Il plugin di Arturo con la sua procedura (`aggiornamenti.py applica`): tag firmato, sha del catalogo,
    MANIFEST, la scelta "manuali" della persona. Una possibile compromissione non si riprova per
    RIPROVA_RIFIUTATA ore: l'avviso resta nel piede e nella barra di Claude Code."""
    if prima.get("esito") == "compromesso" and time.time() - float(prima.get("il") or 0) < RIPROVA_RIFIUTATA * 3600:
        return prima
    voce = voce_plugin()
    percorso = str(voce.get("installPath") or "")
    script = Path(percorso) / "bin" / "aggiornamenti.py"
    if not percorso or not script.is_file():
        return {"esito": "assente"}
    versione = str(voce.get("version") or "")
    # ARTURO_ATTESA_MAX=0: dalla chiusura di una sessione applica aspetta che Claude Code esca; qui non
    # si chiude niente, e le sessioni aperte tengono la loro copia del plugin.
    rc, out = corri([sys.executable, str(script), "applica"], 900, env=dict(os.environ, ARTURO_ATTESA_MAX="0"))
    if "POSSIBILE COMPROMISSIONE" in out or rc == 3:
        return {"esito": "compromesso", "versione": versione, "il": time.time(), "motivo": ultima_riga(out)}
    riga = next((x.strip() for x in out.splitlines() if x.strip().startswith(("APPLICATO", "GIÀ AGGIORNATO"))), "")
    if riga.startswith("APPLICATO"):
        return {"esito": "aggiornato", "prima": versione, "motivo": riga[:200]}
    if rc != 0:
        return {"esito": "errore", "versione": versione, "motivo": ultima_riga(out)}
    return {"esito": "allineato", "versione": versione}


def voce_plugin() -> dict:
    """La voce del plugin di Arturo in installed_plugins.json di Claude Code, o un dizionario vuoto."""
    elenco = leggi(Path(os.environ.get("VOLTA_PLUGINS") or Path.home() / ".claude" / "plugins" / "installed_plugins.json"))
    voci = (elenco.get("plugins") or {}).get("arturo@arturo") or []
    return voci[0] if voci and isinstance(voci[0], dict) else {}


def radice_di() -> tuple[Path | None, str]:
    """Dove sta Arturo, e chi lo dice. Nell'ordine: "config", cioè `radice` di arturo.json o la cartella sopra
    `bin/arturo` della voce `arturo` (come config() di dati.js); "file", cioè ~/.claude/arturo/radice, che il
    plugin di Arturo riscrive a ogni sessione; "plugin", cioè installPath di installed_plugins.json. Gli
    ultimi due servono a chi ha Arturo come plugin e niente `radice` in arturo.json (#6217, 20/11/2026).
    (None, "") se nessuno lo dice."""
    c = config()
    r = c.get("radice")
    if not (isinstance(r, str) and r):
        voce = c.get("arturo")
        bin_ = Path(str(voce[-1])) if isinstance(voce, list) and voce else None
        r = str(bin_.parent.parent) if bin_ and bin_.name == "arturo" and bin_.parent.name == "bin" else ""
    fonte = "config"
    if not r:
        fonte = "file"
        try:
            r = (Path.home() / ".claude" / "arturo" / "radice").read_text(encoding="utf-8").strip()
        except (OSError, ValueError):
            r = ""
    if not r:
        fonte = "plugin"
        r = str(voce_plugin().get("installPath") or "")
    return (Path(os.path.expanduser(r)), fonte) if r else (None, "")


def radice_arturo() -> Path | None:
    """L'Arturo che il mod legge (radice_di). None se nessuno lo nomina."""
    return radice_di()[0]


def copia_arturo() -> dict:
    """Porta avanti la copia di Arturo che Volta legge (un clone o un worktree, come arturo-herdr), solo con
    un fast-forward e solo se è pulita: un file tracciato modificato, un commit suo o un ramo senza remoto la
    lasciano com'è, con esito "ferma". ~/.claude resta fuori: lì Arturo e la config si aggiornano da sé
    (12/11/2026, #5442: la copia era indietro su due Mac, e la colonna dei progetti con lei)."""
    radice = radice_arturo()
    if radice is None:
        return {"esito": "assente", "motivo": "arturo.json non nomina la copia di Arturo"}
    if radice_di()[1] in ("file", "plugin"):
        # Solo una copia che arturo.json nomina si porta avanti: l'Arturo installato come plugin lo aggiorna plugin().
        return {"esito": "assente", "motivo": "%s è l'Arturo installato: si aggiorna con la sua procedura" % radice}
    if radice.resolve() == (Path.home() / ".claude").resolve():
        return {"esito": "assente", "motivo": "~/.claude si aggiorna da sé"}
    if os.environ.get("VOLTA_SANDBOX") and in_protetta(radice):
        # il controllo orario gira in sandbox e lì non entra: una copia in Documenti la porta avanti il giro
        # lanciato dalla finestra, o si sposta fuori (~/src/arturo-herdr, 19/11/2026)
        return {"esito": "ferma", "motivo": "%s sta in una cartella protetta di macOS: il controllo orario non ci entra" % radice}
    if not radice.is_dir():
        return {"esito": "assente", "motivo": "%s non c'è" % radice}
    rc, cima = git(["rev-parse", "--show-toplevel"], cwd=radice, timeout=20)
    if rc != 0 or Path(cima).resolve() != radice.resolve():
        # Una cartella dentro un altro repository non è una copia sua: quel repository non si tocca.
        return {"esito": "assente", "motivo": "%s non è una copia git" % radice}

    def sporca() -> str:
        # --no-optional-locks: il controllo non prende il lucchetto dell'indice a una sessione che lavora lì.
        rc, out = git(["--no-optional-locks", "status", "--porcelain", "--untracked-files=no"], cwd=radice, timeout=30)
        if rc != 0:
            return "git status: " + ultima_riga(out)
        righe_ = [x for x in out.splitlines() if x.strip()]
        return "%d file modificati" % len(righe_) if righe_ else ""

    rc, ramo = git(["symbolic-ref", "--quiet", "--short", "HEAD"], cwd=radice, timeout=20)
    if rc != 0 or not ramo:
        return {"esito": "ferma", "motivo": "HEAD staccato"}
    rc_r, remoto = git(["config", "--get", "branch.%s.remote" % ramo], cwd=radice, timeout=20)
    rc_u, unione = git(["config", "--get", "branch.%s.merge" % ramo], cwd=radice, timeout=20)
    if rc_r != 0 or rc_u != 0 or not remoto or not unione or remoto == ".":
        return {"esito": "ferma", "ramo": ramo, "motivo": "il ramo %s non segue un ramo remoto" % ramo}
    motivo = sporca()
    if motivo:
        return {"esito": "ferma", "ramo": ramo, "motivo": motivo}
    rc, out = git(["fetch", "--quiet", remoto, unione], cwd=radice)
    if rc != 0:
        return {"esito": "errore", "ramo": ramo, "motivo": "fetch: " + ultima_riga(out)}
    rc, conti = git(["rev-list", "--left-right", "--count", "HEAD...@{upstream}"], cwd=radice, timeout=30)
    try:
        suoi, nuovi = (int(x) for x in conti.split())
    except ValueError:
        return {"esito": "errore", "ramo": ramo, "motivo": "rev-list: " + ultima_riga(conti)}
    _, prima = git(["rev-parse", "--short", "HEAD"], cwd=radice, timeout=20)
    if suoi:
        return {"esito": "ferma", "ramo": ramo, "versione": prima, "motivo": "%d commit suoi, non sul remoto" % suoi}
    if not nuovi:
        return {"esito": "allineato", "ramo": ramo, "versione": prima}
    motivo = sporca()  # di nuovo: durante il fetch una sessione può aver toccato un file
    if motivo:
        return {"esito": "ferma", "ramo": ramo, "versione": prima, "motivo": motivo}
    rc, out = git(["merge", "--ff-only", "--quiet", "@{upstream}"], cwd=radice, timeout=60)
    if rc != 0:
        return {"esito": "errore", "ramo": ramo, "versione": prima, "motivo": "merge --ff-only: " + ultima_riga(out)}
    _, dopo = git(["rev-parse", "--short", "HEAD"], cwd=radice, timeout=20)
    return {"esito": "aggiornato", "ramo": ramo, "versione": dopo, "prima": prima,
            "motivo": "%s → %s, %d commit" % (prima, dopo, nuovi)}


def fermo_da() -> float:
    """Secondi senza tastiera né mouse (HIDIdleTime). VOLTA_FERMO lo finge per il banco."""
    if os.environ.get("VOLTA_FERMO"):
        return float(os.environ["VOLTA_FERMO"])
    rc, out = corri(["/usr/sbin/ioreg", "-c", "IOHIDSystem"], 20)
    for riga in out.splitlines():
        if "HIDIdleTime" in riga:
            try:
                return int(riga.rsplit("=", 1)[1].strip()) / 1e9
            except (ValueError, IndexError):
                break
    return 0.0


def ora_locale() -> int:
    return int(os.environ["VOLTA_ORA"]) if os.environ.get("VOLTA_ORA") else time.localtime().tm_hour


def pacchetto_app() -> Path | None:
    """Il pacchetto installato: dove porta il collegamento ~/.local/bin/herdr-app (…/X.app/Contents/MacOS/X)."""
    if os.environ.get("VOLTA_APP_PACCHETTO"):
        return Path(os.environ["VOLTA_APP_PACCHETTO"])
    eseguibile = Path(os.path.realpath(str(Path.home() / ".local" / "bin" / "herdr-app")))
    pacchetto = eseguibile.parent.parent.parent
    return pacchetto if pacchetto.suffix == ".app" and eseguibile.is_file() else None


def versione_app(eseguibile: Path) -> str:
    rc, out = corri([str(eseguibile), "--version"], 30)
    return out.strip().splitlines()[-1].replace("herdr-app ", "").strip() if rc == 0 and out.strip() else ""


def app_aperta(app: list, pacchetto: Path | None = None) -> bool:
    """La finestra risponde a `herdr-app status`, oppure un processo gira dal pacchetto."""
    rc, _ = corri(app + ["status"], 20)
    if rc == 0:
        return True
    if pacchetto is None or os.environ.get("VOLTA_HERDR_APP"):
        return False
    rc, _ = corri(["/usr/bin/pgrep", "-f", str(pacchetto) + "/Contents/MacOS/"], 10)
    return rc == 0


def firme() -> Path:
    """La cartella delle firme di Volta (#6244): accanto a questo script, nel repository (arturo/firme) come
    nella cartella dell'app, dove la porta contorno(). VOLTA_FIRME la indica al banco."""
    return Path(os.environ.get("VOLTA_FIRME") or Path(__file__).resolve().parent / "firme")


REQUISITO_APP = "volta-app.requisito"   # identificatore e impronta del certificato che firma Volta.app


def firma_buona(pacchetto: Path) -> str:
    """"" se il pacchetto è firmato col certificato di Volta, riconosciuto dall'impronta (firme()/
    volta-app.requisito, #6244, 21/11/2026), e la firma regge; altrimenti il motivo. Un certificato col nome
    giusto e un'altra impronta, una firma ad hoc o nessuna firma non passano. VOLTA_CODESIGN (JSON) è il
    codesign del banco."""
    try:
        requisito = (firme() / REQUISITO_APP).read_text(encoding="utf-8").strip()
    except OSError:
        requisito = ""
    if 'certificate leaf = H"' not in requisito:
        return "manca il requisito della firma (%s): non installo un pacchetto che non so riconoscere" % REQUISITO_APP
    codesign = argv_di("VOLTA_CODESIGN", "/usr/bin/codesign") or ["/usr/bin/codesign"]
    rc, out = corri(codesign + ["--verify", "--deep", "--strict", "-R=" + requisito, str(pacchetto)], 60)
    return "" if rc == 0 else "il pacchetto non è firmato col certificato di Volta: " + (ultima_riga(out) or "rc %d" % rc)


def pacco_buono(pacco: Path, sha: str) -> str:
    """"" se il pacchetto dell'app ha lo sha256 atteso, nessun percorso fuori posto e dentro l'eseguibile di
    Volta.app; altrimenti il motivo. Lo usano lo spostamento in Volta.app e lo specchio."""
    import hashlib
    import tarfile
    if hashlib.sha256(pacco.read_bytes()).hexdigest() != sha.lower():
        return "il pacchetto scaricato è rovinato (sha256 diverso)"
    try:
        with tarfile.open(pacco) as t:
            nomi = [membro.name for membro in t.getmembers()]
    except (tarfile.TarError, OSError, EOFError) as e:
        return "il pacchetto scaricato non si apre: %s" % str(e)[:120]
    for nome in nomi:
        if nome.startswith(("/", "..")) or "/../" in nome:
            return "il pacchetto ha un percorso fuori posto: %s" % nome
    if not any(nome in (APP_NUOVA + "/Contents/MacOS/Volta", "./" + APP_NUOVA + "/Contents/MacOS/Volta") for nome in nomi):
        return "nel pacchetto non c'è %s/Contents/MacOS/Volta" % APP_NUOVA
    return ""


SPECCHIO_PACCO = "herdr-app-macos-aarch64.tar.gz"


def specchio() -> dict:
    """Lo specchio delle release per chi sta fuori dalla rete privata (#6217, 20/11/2026). `app_specchio` di
    arturo.json è il repository GitHub delle release ("proprietario/nome"); senza quella voce è spento.
    `gh release download` (l'accesso è di gh, nessun token passa da qui) porta l'ultima release in
    <cache>/canale/app/<versione>/, il pacchetto passa pacco_buono, e per ultimo si scrive
    <cache>/canale/app/latest.json con l'indirizzo file:// del pacchetto. L'app lo legge da lì: il suo
    `app_canale` è file://<cache>/canale. Mai verso una versione più vecchia; restano la versione nuova e
    quella di prima."""
    import re
    repo = config().get("app_specchio")
    if not isinstance(repo, str) or not repo.strip():
        return {"esito": "spento"}
    repo = repo.strip()
    gh = argv_di("VOLTA_GH", "gh")
    if not gh:
        return {"esito": "errore", "motivo": SENZA_GH}
    canale = cache() / "canale"
    lavoro = canale / "scarico.noindex"
    if lavoro.exists():
        togli(lavoro)
    lavoro.mkdir(parents=True)
    try:
        scarico = gh + ["release", "download", "--repo", repo, "--dir", str(lavoro)]
        rc, out = corri(scarico + ["--pattern", "latest.json"], 120)
        if rc != 0:
            return {"esito": "errore", "motivo": "gh release download di latest.json: %s" % (ultima_riga(out) or "rc %d" % rc)}
        m = leggi(lavoro / "latest.json")
        bersagli = m.get("targets") if isinstance(m.get("targets"), dict) else {}
        voce = bersagli.get("macos-aarch64") if isinstance(bersagli.get("macos-aarch64"), dict) else {}
        versione, sha = str(m.get("version") or ""), str(voce.get("sha256") or "").lower()
        # la versione diventa il nome di una cartella: solo lettere, cifre, punto, più e trattino
        if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+-]*", versione) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            return {"esito": "errore", "motivo": "latest.json della release senza versione o sha256 leggibili"}
        qui = leggi(canale / "app" / "latest.json")
        qui_voce = (qui.get("targets") or {}).get("macos-aarch64") or {} if isinstance(qui.get("targets"), dict) else {}
        qui_versione = str(qui.get("version") or "")
        arrivo = canale / "app" / versione
        if qui_versione == versione and str(qui_voce.get("sha256") or "") == sha and (arrivo / SPECCHIO_PACCO).is_file():
            return {"esito": "allineato", "versione": versione}
        if qui_versione and piu_nuova(qui_versione, versione):
            return {"esito": "allineato", "versione": qui_versione, "motivo": "la release è %s, più vecchia" % versione}
        rc, out = corri(scarico + ["--pattern", SPECCHIO_PACCO, "--pattern", "changelog.md"], 900)
        pacco = lavoro / SPECCHIO_PACCO
        if rc != 0 or not pacco.is_file():
            return {"esito": "errore", "verso": versione, "motivo": "gh release download del pacchetto: %s" % (ultima_riga(out) or "rc %d" % rc)}
        guasto = pacco_buono(pacco, sha)
        if guasto:
            return {"esito": "errore", "verso": versione, "motivo": guasto}
        arrivo.mkdir(parents=True, exist_ok=True)
        os.replace(str(pacco), str(arrivo / SPECCHIO_PACCO))
        if (lavoro / "changelog.md").is_file():
            os.replace(str(lavoro / "changelog.md"), str(arrivo / "changelog.md"))
        # latest.json per ultimo e in modo atomico: l'app trova sempre un pacchetto completo
        scrivi(canale / "app" / "latest.json", {"version": versione, "targets": {"macos-aarch64": {
            "url": (arrivo / SPECCHIO_PACCO).resolve().as_uri(), "sha256": sha}}})
        for vecchia in (canale / "app").iterdir():
            if vecchia.is_dir() and vecchia.name not in (versione, qui_versione):
                togli(vecchia)
        return {"esito": "aggiornato", "versione": versione, "prima": qui_versione}
    finally:
        if lavoro.exists():
            togli(lavoro)


def passo_specchio(stato: dict) -> dict:
    """Un giro dello specchio dentro lo stato dei programmi. Spento non lascia traccia: sulle macchine che
    hanno il canale in rete la voce non compare."""
    try:
        d = specchio()
    except Exception as e:  # noqa: BLE001 un pezzo rotto non ferma gli altri
        d = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160])}
    if d.get("esito") == "spento":
        stato.pop("specchio", None)
    else:
        stato["specchio"] = dict(d, il=time.time())
    return d


def sposta_app(vecchio: Path, app: list) -> dict:
    """La prima volta: `Volta Celeste.app` diventa `Volta.app`. Un'app 0.1.15 non sa leggere un pacchetto
    `Volta.app` (src/update.rs prima del 12/11/2026), quindi la prima reinstallazione la fa questo script:
    scarica dal canale, controlla sha256, firma e versione, chiude l'app, mette il pacchetto nuovo accanto,
    sposta il collegamento ~/.local/bin/herdr-app e riapre. Il pacchetto vecchio resta in volta-prima-<v>.
    Dopo, gli aggiornamenti li scarica l'app da sola."""
    import tarfile
    canale = str(os.environ.get("VOLTA_RELEASES_URL") or config().get("app_canale") or "").rstrip("/")
    if not canale:
        return {"esito": "attesa", "motivo": "arturo.json non ha app_canale: lo spostamento in Volta.app aspetta"}
    try:
        m = json.loads(scarica_testo(canale + "/app/latest.json"))
        voce = (m.get("targets") or {}).get("macos-aarch64") or {}
        versione, url, sha = str(m.get("version") or ""), str(voce.get("url") or ""), str(voce.get("sha256") or "")
    except Exception as e:  # noqa: BLE001
        return {"esito": "errore", "motivo": "app/latest.json: %s" % str(e)[:160]}
    adesso = versione_app(vecchio / "Contents" / "MacOS" / "Volta Celeste")
    if not (versione and url and sha):
        return {"esito": "errore", "motivo": "app/latest.json senza versione, indirizzo o sha256"}
    if adesso and piu_nuova(adesso, versione):
        return {"esito": "allineato", "versione": adesso, "motivo": "il canale ha %s, più vecchia" % versione}
    lavoro = vecchio.parent / (APP_NUOVA + ".scarico.noindex")
    nuovo = vecchio.parent / APP_NUOVA
    if nuovo.exists():
        return {"esito": "errore", "motivo": "%s c'è già accanto a %s: non lo sovrascrivo" % (APP_NUOVA, APP_VECCHIA)}
    if lavoro.exists():
        togli(lavoro)
    lavoro.mkdir(parents=True)
    try:
        pacco = lavoro / "app.tar.gz"
        with apri_url(url, 600) as r, open(pacco, "wb") as f:
            shutil.copyfileobj(r, f)
        guasto = pacco_buono(pacco, sha)
        if guasto:
            return {"esito": "errore", "motivo": guasto}
        with tarfile.open(pacco) as t:
            if hasattr(tarfile, "data_filter"):
                t.extractall(str(lavoro), filter="data")  # niente link né permessi fuori posto
            else:
                t.extractall(str(lavoro))  # noqa: S202 percorsi controllati sopra
        estratto = lavoro / APP_NUOVA
        eseguibile = estratto / "Contents" / "MacOS" / "Volta"
        if not eseguibile.is_file():
            return {"esito": "errore", "motivo": "nel pacchetto non c'è %s/Contents/MacOS/Volta" % APP_NUOVA}
        motivo = firma_buona(estratto)
        if motivo:
            return {"esito": "errore", "motivo": motivo}
        if versione_app(eseguibile) != versione:
            return {"esito": "errore", "motivo": "il pacchetto scaricato non risponde come %s" % versione}
        aperta = app_aperta(app, vecchio)
        if aperta:
            corri(app + ["do", "app.quit"], 30)
            for _ in range(60):
                if not app_aperta(app, vecchio):
                    break
                time.sleep(1)
            else:
                return {"esito": "errore", "motivo": "l'app non si è chiusa in 60 secondi: riprovo la notte dopo"}
        os.replace(str(estratto), str(nuovo))
        collegamento = Path.home() / ".local" / "bin" / "herdr-app"
        if collegamento.is_symlink() or not collegamento.exists():
            tmp = collegamento.with_name("herdr-app.%d.nuovo" % os.getpid())
            tmp.unlink(missing_ok=True)
            os.symlink(str(nuovo / "Contents" / "MacOS" / "Volta"), str(tmp))
            os.replace(str(tmp), str(collegamento))
        prima = vecchio.parent / ("volta-prima-%s" % (adesso or "vecchia"))
        n = 2
        while prima.exists():
            prima = vecchio.parent / ("volta-prima-%s-%d" % (adesso or "vecchia", n))
            n += 1
        prima.mkdir()
        os.replace(str(vecchio), str(prima / APP_VECCHIA))
        if aperta and not os.environ.get("VOLTA_NO_APRI"):
            corri(["/usr/bin/open", str(nuovo)], 30)
        return {"esito": "spostato", "versione": versione, "prima": adesso, "riaperta": aperta}
    finally:
        if lavoro.exists():
            togli(lavoro)


def app_volta(prima: dict) -> dict:
    """L'app, solo sul Mac, solo fra le 2 e le 6 e a computer fermo da 30 minuti: si riavvia nella versione
    che ha già scaricato (`herdr-app do app.update`, i terminali restano vivi nel core). La prima volta
    sposta `Volta Celeste.app` in `Volta.app` (sposta_app)."""
    if sys.platform != "darwin" and not os.environ.get("VOLTA_APP_PACCHETTO"):
        return {"esito": "assente", "motivo": "solo sul Mac"}
    pacchetto = pacchetto_app()
    app = herdr_app()
    if pacchetto is None or not app:
        return {"esito": "assente"}
    ora = ora_locale()
    # Fuori fascia o col computer in uso resta l'esito di prima, con il motivo dell'attesa.
    if not FASCIA_APP[0] <= ora < FASCIA_APP[1]:
        return dict(prima, attesa="fuori fascia") if prima else {"esito": "attesa", "attesa": "fuori fascia"}
    if fermo_da() < FERMO_APP:
        return dict(prima, attesa="computer in uso") if prima else {"esito": "attesa", "attesa": "computer in uso"}
    if pacchetto.name == APP_VECCHIA:
        return sposta_app(pacchetto, app)
    ricevuta = pacchetto.with_name(pacchetto.name + ".new.json.noindex")
    pronta = str(leggi(ricevuta).get("version") or "")
    if not pronta:
        return {"esito": "allineato", "versione": versione_app(pacchetto / "Contents" / "MacOS" / "Volta")}
    if not app_aperta(app, pacchetto):
        return {"esito": "attesa", "versione": pronta, "motivo": "l'app è chiusa: la versione nuova entra alla prossima apertura"}
    rc, out = corri(app + ["do", "app.update"], 60)
    if rc != 0 or "no update is ready" in out:
        return {"esito": "errore", "versione": pronta, "motivo": ultima_riga(out) or "app.update rc %d" % rc}
    return {"esito": "riavviata", "versione": pronta}


PROVA_VECCHIA = 6   # ore: oltre, un core di prova senza claude dentro si chiude


def eta_secondi(etime: str) -> int:
    """L'etime di ps ([[gg-]hh:]mm:ss) in secondi; -1 se non si legge."""
    try:
        giorni, _, resto = etime.strip().rpartition("-")
        parti = [int(x) for x in resto.split(":")]
        while len(parti) < 3:
            parti.insert(0, 0)
        return int(giorni or 0) * 86400 + parti[0] * 3600 + parti[1] * 60 + parti[2]
    except ValueError:
        return -1


def processi() -> list:
    """[(pid, ppid, secondi, comando)] da ps, o dal file di VOLTA_PS nei banchi."""
    finto = os.environ.get("VOLTA_PS")
    if finto:
        testo = Path(finto).read_text(encoding="utf-8")
    else:
        rc, testo = corri(["ps", "-axo", "pid=,ppid=,etime=,command="], 30)
        if rc != 0:
            return []
    righe = []
    for r in testo.splitlines():
        c = r.split(None, 3)
        if len(c) == 4 and c[0].isdigit() and c[1].isdigit():
            righe.append((int(c[0]), int(c[1]), eta_secondi(c[2]), c[3]))
    return righe


def socket_di(pid: int) -> list:
    """I socket unix che il processo tiene aperti (lsof), o quelli di VOLTA_SOCKET nei banchi."""
    finto = os.environ.get("VOLTA_SOCKET")
    if finto:
        return list(json.loads(finto).get(str(pid)) or [])
    rc, testo = corri(["lsof", "-a", "-p", str(pid), "-U", "-F", "n"], 30)
    return [r[1:] for r in testo.splitlines() if r.startswith("n") and r.endswith(".sock")] if rc == 0 else []


def prove(chiudi: bool = False) -> dict:
    """I core di prova rimasti accesi: le istanze con HC_SESSION=hzp (o un'altra diversa da default) che le prove
    avviano e non chiudono. Il 14/11/2026 sul MacBook ce n'erano tre, dall'8 e dal 12/11, con nove shell vuote."""
    if os.name == "nt":
        return {"esito": "saltato", "motivo": "solo macOS e Linux"}
    tutti = processi()
    figli: dict = {}
    for pid, ppid, _, _ in tutti:
        figli.setdefault(ppid, []).append(pid)
    comando = {pid: cmd for pid, _, _, cmd in tutti}

    def discendenti(pid: int) -> list:
        fuori, coda = [], list(figli.get(pid, []))
        while coda:
            p = coda.pop()
            fuori.append(p)
            coda.extend(figli.get(p, []))
        return fuori

    trovati = []
    for pid, _, eta, cmd in tutti:
        # il core è l'eseguibile herdr-core (o hc) lanciato con --hc-launchd, non una riga che lo nomina;
        # il percorso può avere spazi ("Herdr Core.app"), quindi si taglia sull'opzione, non sugli spazi
        eseguibile, opzione, _ = cmd.partition(" --hc-launchd")
        if not opzione or Path(eseguibile).name not in ("herdr-core", "hc"):
            continue
        sessioni = [Path(s).name for s in socket_di(pid) if ".holder." not in Path(s).name]
        if not sessioni or "default.sock" in sessioni:
            continue
        sotto = discendenti(pid)
        con_claude = any("claude" in comando.get(p, "") for p in sotto)
        if eta < PROVA_VECCHIA * 3600 or con_claude:
            continue
        trovati.append({"pid": pid, "sessione": sessioni[0][:-5], "ore": eta // 3600,
                        "hold": [p for p in figli.get(pid, []) if " hold " in comando.get(p, "")]})
    chiusi = []
    if chiudi:
        for t in trovati:
            for p in t["hold"] + [t["pid"]]:
                try:
                    os.kill(p, signal.SIGTERM)
                except OSError:
                    continue
            chiusi.append(t["pid"])
    return {"esito": "chiusi" if chiusi else ("trovati" if trovati else "nessuno"), "prove": trovati, "chiusi": chiusi}


def programmi(forza: bool = False) -> dict:
    """Un giro su core, plugin, copia di Arturo e app. I primi tre al più ogni OGNI_PROGRAMMI secondi, l'app a ogni giro
    del sistema (fa da sé i controlli di fascia e di riposo). L'esito va in programmi-stato.json."""
    l = cache() / "programmi.lucchetto"
    l.parent.mkdir(parents=True, exist_ok=True)
    try:
        if l.exists() and time.time() - l.stat().st_mtime > 3600:
            l.rmdir()
        l.mkdir()
    except OSError:
        return {"occupato": True}
    try:
        stato = leggi(programmi_file())
        adesso = time.time()
        if forza or adesso - float(stato.get("giro") or 0) >= OGNI_PROGRAMMI:
            for nome, fare in (("core", core), ("plugin", lambda: plugin(stato.get("plugin") or {})), ("copia", copia_arturo)):
                try:
                    stato[nome] = fare()
                    stato[nome].setdefault("il", time.time())  # un plugin compromesso tiene l'ora del blocco
                except Exception as e:  # noqa: BLE001 un pezzo rotto non ferma gli altri
                    stato[nome] = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160])}
            stato["giro"] = adesso
        passo_specchio(stato)  # prima dell'app: la notte l'app trova già la release nuova
        try:
            stato["app"] = dict(app_volta(stato.get("app") or {}), il=time.time())
        except Exception as e:  # noqa: BLE001
            stato["app"] = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160]), "il": time.time()}
        try:
            stato["prove"] = dict(prove(chiudi=True), il=time.time())
        except Exception as e:  # noqa: BLE001
            stato["prove"] = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160]), "il": time.time()}
        scrivi(programmi_file(), stato)
        return stato
    finally:
        try:
            l.rmdir()
        except OSError:
            pass


PROTETTE = ("Documents", "Desktop", "Downloads")


def profilo_sandbox() -> str:
    """Il profilo di sandbox-exec del controllo orario: Documenti, Scrivania e Download negati (19/11/2026).
    Da launchd un programma non di sistema che tocca Documenti apre il dialogo dei permessi di macOS su uno
    schermo spesso vuoto, e finché nessuno risponde Documenti resta bloccato per tutta la macchina (Amaltea,
    18 e 19/11). Negato dalla sandbox, lo stesso accesso fallisce subito e nessun dialogo si apre. La casa
    va col percorso reale: la sandbox confronta quello."""
    case = {str(Path.home()), os.path.realpath(str(Path.home()))}
    vie = " ".join('(subpath "%s/%s")' % (c, d) for c in sorted(case) for d in PROTETTE)
    return "(version 1)(allow default)(deny file-read* file-write* %s)" % vie


def in_protetta(p: Path) -> bool:
    """Vero se `p` sta in Documenti, Scrivania o Download della casa (senza entrarci: niente resolve)."""
    casa = os.path.realpath(str(Path.home()))
    q = os.path.abspath(os.path.expanduser(str(p)))
    for c in {str(Path.home()), casa}:
        if any(q == os.path.join(c, d) or q.startswith(os.path.join(c, d) + os.sep) for d in PROTETTE):
            return True
    return False


# --- Log e diagnosi (step 7 della revisione, 18/11/2026) ------------------------------------------------
# I tre log dei LaunchAgent (volta-mod, volta-sync e volta-canale) crescevano senza fine: launchd scrive in
# coda e non li accorcia mai. L'app scrive il suo volta.log con una rotazione sua (src/applog.rs).
# `volta diagnosi` mette in un archivio quello che serve a capire un guasto, senza testi né segreti.

LOG_MAX = 1024 * 1024        # byte: oltre, un log del sistema passa a <nome>.1.log
LOG_TENUTI = 3               # quanti log vecchi restano per nome
LOG_SISTEMA = ("volta-mod.log", "volta-sync.log", "volta-canale.log")
DIAGNOSI_CODA = 256 * 1024   # byte: di ogni log entra solo la coda
DIAGNOSI_GIORNI = 3          # giorni del registro nell'archivio
SEGNO_COMANDO = "# volta: lanciatore scritto da volta_mod.py"


def cartella_log_sistema() -> Path:
    """Dove i LaunchAgent scrivono i loro log (VOLTA_LOGS per i banchi)."""
    return Path(os.environ.get("VOLTA_LOGS") or Path.home() / "Library" / "Logs")


def cartella_log_app() -> Path | None:
    """La cartella di volta.log, con le regole di dir() in src/applog.rs."""
    if os.environ.get("VOLTA_LOG_DIR"):
        return Path(os.environ["VOLTA_LOG_DIR"])
    if os.environ.get("HERDR_APP_HOME"):
        return app_home() / "logs"
    if os.name == "nt":
        return Path(os.environ["LOCALAPPDATA"]) / "Volta" / "Logs" if os.environ.get("LOCALAPPDATA") else None
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "Volta"
    stato = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(stato) / "volta"


def vecchio_log(f: Path, n: int) -> Path:
    """volta-mod.log -> volta-mod.1.log, volta-mod.2.log, …"""
    return f.with_name("%s.%d%s" % (f.stem, n, f.suffix))


def ruota_log() -> list:
    """Un log del sistema oltre LOG_MAX si copia in <nome>.1.log (i vecchi scalano fino a LOG_TENUTI) e si
    svuota sul posto. Svuotare e non rinominare: launchd tiene il file aperto in coda (O_APPEND), e dopo una
    rinomina continuerebbe a scrivere nel .1. Le righe scritte fra la copia e lo svuotamento si perdono: è
    una finestra di millisecondi, una volta per mega. Torna i nomi ruotati; non solleva."""
    try:
        massimo = int(os.environ.get("VOLTA_LOG_MAX") or LOG_MAX)
    except ValueError:
        massimo = LOG_MAX
    ruotati = []
    for nome in LOG_SISTEMA:
        f = cartella_log_sistema() / nome
        try:
            if not f.is_file() or f.stat().st_size <= massimo:
                continue
            vecchio_log(f, LOG_TENUTI).unlink(missing_ok=True)
            for n in range(LOG_TENUTI - 1, 0, -1):
                if vecchio_log(f, n).exists():
                    os.replace(str(vecchio_log(f, n)), str(vecchio_log(f, n + 1)))
            shutil.copyfile(str(f), str(vecchio_log(f, 1)))
            with open(f, "r+b") as fh:
                fh.truncate(0)
            ruotati.append(nome)
        except OSError:
            continue
    return ruotati


def cartella_comandi() -> Path:
    return Path(os.environ.get("VOLTA_BIN") or Path.home() / ".local" / "bin")


# I sottocomandi di questo script che il comando `volta` gli passa; il resto va a herdr-app (VOLTA.md: `volta`
# è un alias di `herdr-app`). Nessuno di questi nomi è un comando di herdr-app (do, status, ls, check, …).
DI_VOLTA_MOD = ("diagnosi", "stato", "log", "controlla", "installa", "attiva", "disattiva", "automatico", "manuale",
                "immagini", "programmi", "specchio", "prove")


def comando_volta() -> str:
    """Scrive il comando `volta` in ~/.local/bin, accanto a herdr-app: `volta diagnosi`, `volta stato` e gli
    altri DI_VOLTA_MOD passano a questo script, ogni altro argomento a herdr-app. Solo sul Mac e su Linux,
    solo per la finestra vera (non per una casa di prova), e mai sopra un `volta` che non ha il segno di
    questo script (Volta.js, per esempio, ha un comando con lo stesso nome). Torna l'esito; non solleva."""
    if os.name == "nt":
        return "windows: python volta_mod.py"
    if os.environ.get("HERDR_APP_HOME") and not os.environ.get("VOLTA_BIN"):
        return "casa di prova"
    f = cartella_comandi() / "volta"
    testo = ('#!/bin/sh\n%s\ncase "$1" in\n  %s)\n    exec /usr/bin/env python3 "%s" "$@" ;;\nesac\n'
             'exec "$(dirname "$0")/herdr-app" "$@"\n' % (SEGNO_COMANDO, "|".join(DI_VOLTA_MOD), app_home() / "volta_mod.py"))
    try:
        if f.exists() or f.is_symlink():
            prima = f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""
            if SEGNO_COMANDO not in prima:
                return "c'è già un altro volta"
            if prima == testo:
                return "c'è"
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(".volta.%d.tmp" % os.getpid())
        tmp.write_text(testo, encoding="utf-8")
        tmp.chmod(0o755)
        os.replace(str(tmp), str(f))
        return "scritto"
    except OSError as e:
        return "non scritto: %s" % str(e)[:120]


# Quello che non esce mai da questa macchina in un archivio di diagnosi. L'ordine conta: prima le
# credenziali dentro gli indirizzi, poi chiavi e token per forma, poi chiave=valore, poi le email.
SEGRETI = (
    (r"://[^/\s:@]+:[^/\s@]+@", "://<credenziali>@"),
    (r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|xox[abprs]-[A-Za-z0-9-]{8,}"
     r"|AKIA[0-9A-Z]{12,}|AIza[0-9A-Za-z_-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,})", "<segreto>"),
    (r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}", r"\1 <segreto>"),
    (r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|chiave|parola)(\"?\s*[=:]\s*\"?)[^\s\",;&]+",
     r"\1\2<segreto>"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<email>"),
)


def pulisci_testo(testo: str) -> str:
    """Il testo come entra nell'archivio: la casa diventa ~, il nome della persona nei percorsi <utente>,
    i segreti e le email spariscono."""
    import re  # noqa: PLC0415
    casa = str(Path.home())
    for c in {casa, casa.replace("\\", "/"), os.path.realpath(casa)}:
        if len(c) > 3:
            testo = testo.replace(c, "~")
    testo = re.sub(r"(?i)([/\\](?:Users|home)[/\\])[^/\\\s\"']+", r"\1<utente>", testo)
    for schema, al_posto in SEGRETI:
        testo = re.sub(schema, al_posto, testo)
    return testo


def coda_di(f: Path, quanti: int = DIAGNOSI_CODA) -> str:
    """Gli ultimi `quanti` byte di un file, da una riga intera."""
    try:
        with open(f, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            n = fh.tell()
            fh.seek(max(0, n - quanti))
            dati = fh.read()
    except OSError:
        return ""
    if n > quanti and b"\n" in dati:
        dati = dati.split(b"\n", 1)[1]
    return dati.decode("utf-8", errors="replace")


def versioni() -> dict:
    """Versioni di app, mod, core, claude e del sistema. Un programma che manca dice "assente"."""
    import platform  # noqa: PLC0415
    v = {"sistema": platform.platform(), "python": platform.python_version(),
         "mod": leggi(app_home() / "mods" / "arturo" / "VERSIONE"), "volta_mod": leggi(stato_file()).get("esito")}
    app = herdr_app()
    if app:
        rc, out = corri(app + ["--version"], 20)
        v["app"] = ultima_riga(out) if rc == 0 else "rc %d: %s" % (rc, ultima_riga(out))
    else:
        v["app"] = "assente"
    hc = argv_di("VOLTA_HC", "hc")
    if hc:
        rc, out = corri(hc + ["server", "status"], 20)
        try:
            v["core"] = json.loads(out.strip().splitlines()[-1]).get("version") if rc == 0 else "rc %d" % rc
        except (ValueError, IndexError, AttributeError):
            v["core"] = ultima_riga(out)
    else:
        v["core"] = "assente"
    claude = argv_di("VOLTA_CLAUDE", "claude")
    if claude:
        rc, out = corri(claude + ["--version"], 20)
        v["claude"] = ultima_riga(out) if rc == 0 else "rc %d" % rc
    else:
        v["claude"] = "assente"
    return v


def cartella_registro() -> Path:
    """La cartella del registro, con le regole di cartella() in volta_registro.py."""
    if os.environ.get("VOLTA_REGISTRO"):
        return Path(os.environ["VOLTA_REGISTRO"])
    if os.environ.get("HERDR_APP_HOME"):
        return app_home() / "cache" / "volta-registro"
    return Path.home() / ".cache" / "volta-registro"


def diagnosi(uscita: Path, giorni: int = DIAGNOSI_GIORNI) -> tuple[Path, dict]:
    """Scrive volta-diagnosi-<data>.zip in `uscita` e torna (archivio, indice). Dentro: versioni, gli stati
    dei controlli, il registro degli ultimi `giorni` giorni con gli errori a parte, la coda dei log dell'app e
    del sistema, e di settings.json e arturo.json solo le voci che non dicono niente della persona. Non entra
    sessioni.json né la lettura della sonda (titoli, progetti): ogni testo passa da pulisci_testo()."""
    import zipfile  # noqa: PLC0415
    quando = time.strftime("%Y%m%d-%H%M%S")
    uscita.mkdir(parents=True, exist_ok=True)
    archivio = uscita / ("volta-diagnosi-%s.zip" % quando)
    indice = {"creato": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "file": {}}
    pezzi = {}

    def metti(nome: str, testo: str) -> None:
        pezzi[nome] = pulisci_testo(testo)
        indice["file"][nome] = len(pezzi[nome].encode("utf-8"))

    metti("versioni.json", json.dumps(versioni(), ensure_ascii=False, indent=2))
    for nome in ("mod-stato.json", "programmi-stato.json", "immagini-stato.json", "immagini-genera.json"):
        f = cache() / nome
        if f.is_file():
            metti("stati/" + nome, coda_di(f))
    impostazioni = leggi(app_home() / "settings.json")
    c = config()
    metti("impostazioni.json", json.dumps({
        "settings": {"voci": sorted(impostazioni), "telemetry": impostazioni.get("telemetry")},
        "arturo": {"voci": sorted(c), "mod_modo": c.get("mod_modo") or "automatico", "mod_ramo": c.get("mod_ramo"),
                   "mod_sorgente": bool(c.get("mod_sorgente")), "app_canale": bool(c.get("app_canale"))},
    }, ensure_ascii=False, indent=2))
    reg = cartella_registro()
    errori = []
    for i in range(giorni - 1, -1, -1):
        g = time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400))
        f = reg / ("eventi-%s.jsonl" % g)
        if not f.is_file():
            continue
        testo = coda_di(f, 4 * DIAGNOSI_CODA)
        metti("registro/" + f.name, testo)
        for riga in testo.splitlines():
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            liv = d.get("livello") or ("info" if d.get("esito") in (None, "ok") else "avviso" if d.get("esito") == "ripiego" else "errore")
            if liv in ("avviso", "errore"):
                errori.append(riga)
    metti("registro/errori.jsonl", "\n".join(errori[-500:]) + ("\n" if errori else ""))
    log_app = cartella_log_app()
    for cartella, nomi in ((log_app, ("volta.log", "volta.1.log")),
                           (cartella_log_sistema(), [n for x in LOG_SISTEMA for n in (x, vecchio_log(Path(x), 1).name)])):
        for nome in nomi:
            f = cartella / nome if cartella else None
            if f is not None and f.is_file():
                metti("log/" + nome, coda_di(f))
    indice["leggimi"] = ("Archivio di diagnosi di Volta. Percorsi della casa scritti come ~, nomi utente come <utente>, "
                         "segreti come <segreto>, email come <email>. Niente conversazioni, titoli o nomi dei progetti.")
    tmp = archivio.with_name(archivio.name + ".tmp")
    with zipfile.ZipFile(str(tmp), "w", zipfile.ZIP_DEFLATED) as z:
        for nome, testo in pezzi.items():
            z.writestr(nome, testo)
        z.writestr("indice.json", json.dumps(indice, ensure_ascii=False, indent=2))
    os.replace(str(tmp), str(archivio))
    return archivio, indice


def cmd_diagnosi(argv: list) -> int:
    uscita = None
    if "--uscita" in argv:
        resto = argv[argv.index("--uscita") + 1:]
        if not resto:
            print("uso: volta diagnosi [--uscita <cartella>]")
            return 2
        uscita = Path(resto[0]).expanduser()
    if uscita is None:
        scrivania = Path.home() / "Desktop"
        uscita = scrivania if scrivania.is_dir() else Path.home()
    try:
        archivio, indice = diagnosi(uscita)
    except OSError as e:
        print("DIAGNOSI NON SCRITTA: %s" % e)
        return 1
    print("DIAGNOSI: %s (%d file, %d KB)" % (archivio, len(indice["file"]) + 1, max(1, archivio.stat().st_size // 1024)))
    print("Dentro: versioni, stati, registro, log. Niente conversazioni né segreti: puoi mandarlo a chi ti aiuta.")
    return 0


def plist_agente(script: str) -> str:
    """Il LaunchAgent. Parte con `/usr/bin/env python3` e non col Python di chi l'ha acceso: un percorso
    con la versione dentro (python@3.14) sparisce al primo aggiornamento di Homebrew, e il controllo
    orario si fermerebbe senza dirlo."""
    percorso = ":".join([str(Path.home() / ".local" / "bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])
    registro = Path.home() / "Library/Logs/volta-mod.log"
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>%s</string>
<key>ProgramArguments</key><array><string>/usr/bin/sandbox-exec</string><string>-p</string><string>%s</string><string>/usr/bin/env</string><string>python3</string><string>%s</string><string>controlla</string></array>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>%s</string><key>VOLTA_SANDBOX</key><string>1</string></dict>
<key>StartInterval</key><integer>3600</integer>
<key>RunAtLoad</key><true/>
<key>StandardOutPath</key><string>%s</string>
<key>StandardErrorPath</key><string>%s</string>
</dict></plist>
""" % (ETICHETTA, profilo_sandbox(), script, percorso, registro, registro)


def agente_aggiorna() -> None:
    """Un LaunchAgent scritto da uno script di prima, col Python di allora nel percorso, si riscrive.
    Dentro l'agente stesso si cambia solo il file (vale dal prossimo accesso): un bootout lo ucciderebbe."""
    if os.environ.get("VOLTA_NO_AGENTE") or os.environ.get("VOLTA_AGENTE_PROVA"):
        return
    if os.name == "nt":
        # Un'attività di prima non passa --sistema: il giro di core e plugin non partirebbe mai (12/11/2026).
        try:
            r = subprocess.run(["schtasks", "/Query", "/TN", ATTIVITA, "/XML"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=30)
            if r.returncode == 0 and "--sistema" not in (r.stdout or ""):
                agente(True)
        except (OSError, subprocess.SubprocessError):
            pass
        return
    if sys.platform != "darwin":
        return
    plist = Path.home() / "Library" / "LaunchAgents" / (ETICHETTA + ".plist")
    try:
        # si riscrive anche quello senza sandbox (19/11/2026)
        if not plist.is_file() or "<string>/usr/bin/sandbox-exec</string>" in plist.read_text(encoding="utf-8"):
            return
        if os.environ.get("XPC_SERVICE_NAME") == ETICHETTA:
            tmp = plist.with_name(plist.name + ".nuovo")
            tmp.write_text(plist_agente(str(app_home() / "volta_mod.py")), encoding="utf-8")
            os.replace(str(tmp), str(plist))
        else:
            agente(True)
    except OSError:
        pass


def agente(accendi: bool) -> str:
    """Il controllo orario del sistema: LaunchAgent sul Mac, attività pianificata su Windows."""
    script = str(app_home() / "volta_mod.py")
    prova = os.environ.get("VOLTA_AGENTE_PROVA")
    if prova:
        Path(prova).mkdir(parents=True, exist_ok=True)
        if not accendi:
            (Path(prova) / (ETICHETTA + ".plist")).unlink(missing_ok=True)
            return "prova tolta"
        (Path(prova) / (ETICHETTA + ".plist")).write_text(plist_agente(script), encoding="utf-8")
        return "prova"
    if os.environ.get("VOLTA_NO_AGENTE"):
        return "saltato"
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / (ETICHETTA + ".plist")
        dominio = "gui/%d" % os.getuid()
        subprocess.run(["launchctl", "bootout", dominio + "/" + ETICHETTA], capture_output=True)
        if not accendi:
            plist.unlink(missing_ok=True)
            return "tolto"
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(plist_agente(script), encoding="utf-8")
        r = subprocess.run(["launchctl", "bootstrap", dominio, str(plist)], capture_output=True, text=True)
        return "LaunchAgent" if r.returncode == 0 else "LaunchAgent non caricato: " + ultima_riga(r.stderr or r.stdout)
    if os.name == "nt":
        if not accendi:
            subprocess.run(["schtasks", "/Delete", "/TN", ATTIVITA, "/F"], capture_output=True)
            return "tolta"
        py = Path(sys.executable)
        senza_finestra = py.with_name("pythonw.exe")
        comando = '"%s" "%s" controlla --sistema' % (senza_finestra if senza_finestra.exists() else py, script)
        r = subprocess.run(["schtasks", "/Create", "/TN", ATTIVITA, "/SC", "HOURLY", "/TR", comando, "/F"], capture_output=True, text=True)
        return "attività pianificata" if r.returncode == 0 else "attività non creata: " + ultima_riga(r.stderr or r.stdout)
    return "nessun controllo orario su questo sistema: resta quello del mod"


def cmd_attiva(argv: list) -> int:
    if not argv or argv[0].startswith("-"):
        print("uso: volta_mod.py attiva <url del repository> [--ramo <ramo>]")
        return 2
    app = app_home()
    c = leggi(app / "arturo.json")
    c["mod_sorgente"] = argv[0]
    if "--ramo" in argv[1:] and argv.index("--ramo") + 1 < len(argv):
        c["mod_ramo"] = argv[argv.index("--ramo") + 1]
    c.pop("mod_modo", None)
    scrivi(app / "arturo.json", c)
    qui = Path(__file__).resolve()
    if qui != (app / "volta_mod.py").resolve():
        shutil.copy2(str(qui), str(app / "volta_mod.py"))
    print("ATTIVO: sorgente %s, controllo orario: %s" % (argv[0], agente(True)))
    return 0


def cmd_disattiva() -> int:
    """Il contrario di `attiva` (#6217, 20/11/2026): toglie il controllo orario del sistema e mette il mod in
    "manuale", così anche il controllo che il mod lancia da sé si ferma, e con lui core, plugin, specchio e
    app. La sorgente resta scritta: `attiva <url>` riaccende tutto. Il mod installato resta com'è."""
    app = app_home()
    c = leggi(app / "arturo.json")
    c.update(mod_modo="manuale")
    scrivi(app / "arturo.json", c)
    print("DISATTIVO: il mod non si aggiorna più, controllo orario: %s. Per riaccendere: volta_mod.py attiva %s"
          % (agente(False), c.get("mod_sorgente") or "<url del repository>"))
    return 0


def cmd_modo(modo: str) -> int:
    app = app_home()
    c = leggi(app / "arturo.json")
    if modo == "manuale":
        c["mod_modo"] = "manuale"
    else:
        c.pop("mod_modo", None)
    scrivi(app / "arturo.json", c)
    print("Il mod di Volta ora %s." % ("si aggiorna solo a mano" if modo == "manuale" else "si aggiorna da solo"))
    return 0


def main(argv: list) -> int:
    if argv[:1] == ["--prova"]:
        return 0
    if argv[:1] == ["controlla"]:
        for nome in ruota_log():
            print("LOG: %s ruotato" % nome)
        rc = cmd_controlla(forza="--forza" in argv)
        c = config()
        if dal_sistema(argv) and c.get("mod_sorgente") and c.get("mod_modo") != "manuale":
            for nome, d in programmi().items():
                if isinstance(d, dict):
                    print("%s: %s%s" % (nome.upper(), d.get("esito"), (" · " + str(d["motivo"])) if d.get("motivo") else ""))
        return rc
    if argv[:1] == ["programmi"]:
        # A mano, per le prove: lo stesso giro del sistema, subito (--subito salta l'attesa di OGNI_PROGRAMMI).
        print(json.dumps(programmi(forza="--subito" in argv), ensure_ascii=False))
        return 0
    if argv[:1] == ["specchio"]:
        stato = leggi(programmi_file())
        d = passo_specchio(stato)
        if d.get("esito") != "spento":
            scrivi(programmi_file(), stato)
        print(json.dumps(d, ensure_ascii=False))
        return 1 if d.get("esito") == "errore" else 0
    if argv[:1] == ["prove"]:
        print(json.dumps(prove(chiudi="--chiudi" in argv), ensure_ascii=False))
        return 0
    if argv[:1] == ["installa"]:
        return cmd_installa(argv[1:])
    if argv[:1] == ["diagnosi"]:
        return cmd_diagnosi(argv[1:])
    if argv[:1] == ["log"]:
        print(json.dumps({"ruotati": ruota_log(), "app": str(cartella_log_app() or ""),
                          "sistema": str(cartella_log_sistema())}, ensure_ascii=False))
        return 0
    if argv[:1] == ["immagini"]:
        return 1 if passo_immagini()["esito"] == "errore" else 0
    if argv[:1] == ["attiva"]:
        return cmd_attiva(argv[1:])
    if argv[:1] == ["disattiva"]:
        return cmd_disattiva()
    if argv[:1] in (["automatico"], ["manuale"]):
        return cmd_modo(argv[0])
    if argv[:1] == ["stato"]:
        d = leggi(stato_file())
        d["installato"] = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        d["sorgente"] = config().get("mod_sorgente")
        d["modo"] = config().get("mod_modo") or "automatico"
        radice, fonte = radice_di()
        d["arturo"] = {"radice": str(radice) if radice else None, "fonte": fonte}
        d["herdr_app"] = herdr_app()
        d["immagini"] = leggi(cache() / "immagini-stato.json")
        d["genera"] = leggi(cache() / "immagini-genera.json")
        d["programmi"] = {k: v for k, v in leggi(programmi_file()).items() if k in ("core", "plugin", "copia", "specchio", "app", "prove")}
        print(json.dumps(d, ensure_ascii=False))
        return 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
