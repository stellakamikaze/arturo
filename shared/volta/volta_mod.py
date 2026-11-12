#!/usr/bin/env python3
"""volta_mod: il mod `arturo` di Volta si aggiorna da solo da un repository git.

La fonte è la cartella `arturo/` di questo repository (ramo `volta`): mods/arturo, layouts, themes e
i lanciatori. Ogni macchina ne tiene un clone leggero in ~/.cache/volta/mod-git e lo confronta con
il mod installato in ~/.config/herdr-app/mods/arturo (file VERSIONE).

  python3 volta_mod.py controlla            scarica, controlla e installa se c'è una versione nuova
  python3 volta_mod.py installa --da DIR    installa da una cartella `arturo/` locale (prove, /setup)
  python3 volta_mod.py attiva URL [--ramo R]  scrive la sorgente in arturo.json e mette il controllo orario
  python3 volta_mod.py automatico | manuale   accende o spegne il controllo, la sorgente resta
  python3 volta_mod.py stato                l'ultimo esito, in JSON (anche immagini, core, plugin e app)
  python3 volta_mod.py immagini             copia le immagini dei progetti nella cartella dell'app
  python3 volta_mod.py programmi [--subito] il giro di core, plugin e app, come lo fa il sistema
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
    cartella dentro un altro repository non si toccano.

Variabili per i banchi: HERDR_APP_HOME, VOLTA_CACHE, VOLTA_IMMAGINI (la cartella dei WebP), VOLTA_HERDR_APP (JSON: l'argv di herdr-app),
VOLTA_NO_AGENTE=1 (niente LaunchAgent né schtasks), VOLTA_HC (JSON: l'argv di hc), VOLTA_PLUGINS
(installed_plugins.json), VOLTA_APP_PACCHETTO, VOLTA_ORA, VOLTA_FERMO, VOLTA_FIRMA_FINTA, VOLTA_NO_APRI,
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
LANCIATORI = (("volta-claude.sh", "volta-claude"), ("nascita.sh", "volta-nascita.sh"),
              ("volta-claude.ps1", "volta-claude.ps1"), ("servizio-claude.ps1", "servizio-claude.ps1"))
# I mod di Arturo tolti: un tasto rimasto su uno di questi non apre più niente (installa-herdr.sh ha lo stesso elenco).
TASTI_VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")
# Comandi nati dopo le prime installazioni: il giro fra le sessioni (⌘↓ e ⌘↑, 12/11/2026) e, su Windows,
# Ctrl+W che chiude la scheda come ⌘W sul Mac, cioè col congedo (Federico, 12/11 sera). Ctrl+Maiusc+W di
# Herdr resta.
TASTI_NUOVI = ("arturo.volta-giro-avanti", "arturo.volta-giro-indietro", "tab.close")
# Tasti nuovi di un comando che c'era già: ⌘K apre la stessa ricerca di ⌘O (#5369). Si offre il solo tasto:
# un ⌘O tolto dalla persona non torna.
TASTI_AGGIUNTI = (("cmd-k", "arturo.apri"),)
# Comandi che la fonte ha spostato: il tasto che li porta ancora prende il comando nuovo della fonte. ⌘T
# (ctrl-shift-t) apre le tessere dei progetti, e "Nuova richiesta" è la prima tessera (12/11/2026, #5371).
TASTI_SPOSTATI = ("arturo.volta-nuova",)
# Il tasto che Arturo prende a Herdr (installa-herdr.sh ha lo stesso): la scheda nuova di Herdr (tab.new,
# una shell) diventa le tessere dei progetti, se quel tasto fa ancora la scheda di Herdr o manca (#5290).
PRENDE = {"arturo.casa": ("tab.new",)}
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


def git(args: list, cwd: Path | None = None, timeout: int = ATTESA_GIT) -> tuple[int, str]:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", ssh_di_git() + " -o BatchMode=yes -o ConnectTimeout=15")
    # git parte in un gruppo suo: allo scadere del tempo si chiude tutto il gruppo, figli compresi.
    suo = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        p = subprocess.Popen(GIT + args, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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

    def clona() -> str:
        togli(clone)
        clone.parent.mkdir(parents=True, exist_ok=True)
        rc, out = git(["clone", "--quiet", "--filter=blob:none", "--sparse", "--depth", "1", "--branch", ramo,
                       url, str(clone)], timeout=ATTESA_GIT * 2)
        if rc != 0:
            togli(clone)
            return ultima_riga(out) or "clone fallito"
        # --no-cone: solo la cartella della fonte, senza i file della radice del repository
        rc, out = git(["sparse-checkout", "set", "--no-cone", "/" + CARTELLA + "/"], cwd=clone)
        return "" if rc == 0 else (ultima_riga(out) or "sparse-checkout fallito")

    def allinea() -> str:
        git(["remote", "set-url", "origin", url], cwd=clone)
        rc, out = git(["fetch", "--quiet", "--depth", "1", "origin", ramo], cwd=clone)
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


def herdr_app() -> list | None:
    finto = os.environ.get("VOLTA_HERDR_APP")
    if finto:
        return json.loads(finto)
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
            chiave = "%s %s" % (sezione, tasto)
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
    """Layout, temi e lanciatori accanto al mod. arturo.json resta della persona, e così keys.json,
    salvo i tasti rimasti su un mod di Arturo tolto."""
    app = app_home()
    for nome in ("layouts", "themes"):
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


def cmd_controlla() -> int:
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
        installato = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        v = str(installato.get("versione") or "")
        messo = float(installato.get("installato") or 0)
        if v.startswith("locale") and time.time() - messo < TENUTA_LOCALE * 3600:
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
    elenco = leggi(Path(os.environ.get("VOLTA_PLUGINS") or Path.home() / ".claude" / "plugins" / "installed_plugins.json"))
    voci = (elenco.get("plugins") or {}).get("arturo@arturo") or []
    percorso = str(voci[0].get("installPath") or "") if voci and isinstance(voci[0], dict) else ""
    script = Path(percorso) / "bin" / "aggiornamenti.py"
    if not percorso or not script.is_file():
        return {"esito": "assente"}
    versione = str(voci[0].get("version") or "")
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


def radice_arturo() -> Path | None:
    """La copia di Arturo che il mod legge: `radice` di arturo.json, altrimenti la cartella sopra
    `bin/arturo` della voce `arturo` (come config() di dati.js). None se arturo.json non la nomina."""
    c = config()
    r = c.get("radice")
    if not (isinstance(r, str) and r):
        voce = c.get("arturo")
        bin_ = Path(str(voce[-1])) if isinstance(voce, list) and voce else None
        r = str(bin_.parent.parent) if bin_ and bin_.name == "arturo" and bin_.parent.name == "bin" else ""
    return Path(os.path.expanduser(r)) if r else None


def copia_arturo() -> dict:
    """Porta avanti la copia di Arturo che Volta legge (un clone o un worktree, come arturo-herdr), solo con
    un fast-forward e solo se è pulita: un file tracciato modificato, un commit suo o un ramo senza remoto la
    lasciano com'è, con esito "ferma". ~/.claude resta fuori: lì Arturo e la config si aggiornano da sé
    (12/11/2026, #5442: la copia era indietro su due Mac, e la colonna dei progetti con lei)."""
    radice = radice_arturo()
    if radice is None:
        return {"esito": "assente", "motivo": "arturo.json non nomina la copia di Arturo"}
    if radice.resolve() == (Path.home() / ".claude").resolve():
        return {"esito": "assente", "motivo": "~/.claude si aggiorna da sé"}
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


def firma_buona(pacchetto: Path) -> str:
    """"" se il pacchetto è firmato con l'identità locale (o Developer ID) e la firma regge, altrimenti il
    motivo. VOLTA_FIRMA_FINTA=ok|no la finge per il banco."""
    finta = os.environ.get("VOLTA_FIRMA_FINTA")
    if finta:
        return "" if finta == "ok" else "firma finta rifiutata"
    rc, out = corri(["/usr/bin/codesign", "-dvv", str(pacchetto)], 30)
    if rc != 0 or not any(r == "Authority=Arturo firma locale" or r.startswith("Authority=Developer ID Application:")
                          for r in out.splitlines()):
        return "il pacchetto non è firmato con Arturo firma locale"
    rc, out = corri(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(pacchetto)], 60)
    return "" if rc == 0 else "firma non valida: " + ultima_riga(out)


def sposta_app(vecchio: Path, app: list) -> dict:
    """La prima volta: `Volta Celeste.app` diventa `Volta.app`. Un'app 0.1.15 non sa leggere un pacchetto
    `Volta.app` (src/update.rs prima del 12/11/2026), quindi la prima reinstallazione la fa questo script:
    scarica dal canale, controlla sha256, firma e versione, chiude l'app, mette il pacchetto nuovo accanto,
    sposta il collegamento ~/.local/bin/herdr-app e riapre. Il pacchetto vecchio resta in volta-prima-<v>.
    Dopo, gli aggiornamenti li scarica l'app da sola."""
    import hashlib
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
        if hashlib.sha256(pacco.read_bytes()).hexdigest() != sha.lower():
            return {"esito": "errore", "motivo": "il pacchetto scaricato è rovinato (sha256 diverso)"}
        with tarfile.open(pacco) as t:
            for membro in t.getmembers():
                if membro.name.startswith(("/", "..")) or "/../" in membro.name:
                    return {"esito": "errore", "motivo": "il pacchetto ha un percorso fuori posto: %s" % membro.name}
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
    app = argv_di("VOLTA_HERDR_APP", "herdr-app")
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
        try:
            stato["app"] = dict(app_volta(stato.get("app") or {}), il=time.time())
        except Exception as e:  # noqa: BLE001
            stato["app"] = {"esito": "errore", "motivo": "%s: %s" % (type(e).__name__, str(e)[:160]), "il": time.time()}
        scrivi(programmi_file(), stato)
        return stato
    finally:
        try:
            l.rmdir()
        except OSError:
            pass


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
<key>ProgramArguments</key><array><string>/usr/bin/env</string><string>python3</string><string>%s</string><string>controlla</string></array>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>%s</string></dict>
<key>StartInterval</key><integer>3600</integer>
<key>RunAtLoad</key><true/>
<key>StandardOutPath</key><string>%s</string>
<key>StandardErrorPath</key><string>%s</string>
</dict></plist>
""" % (ETICHETTA, script, percorso, registro, registro)


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
        if not plist.is_file() or "<string>/usr/bin/env</string>" in plist.read_text(encoding="utf-8"):
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
        rc = cmd_controlla()
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
    if argv[:1] == ["installa"]:
        return cmd_installa(argv[1:])
    if argv[:1] == ["immagini"]:
        return 1 if passo_immagini()["esito"] == "errore" else 0
    if argv[:1] == ["attiva"]:
        return cmd_attiva(argv[1:])
    if argv[:1] in (["automatico"], ["manuale"]):
        return cmd_modo(argv[0])
    if argv[:1] == ["stato"]:
        d = leggi(stato_file())
        d["installato"] = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        d["sorgente"] = config().get("mod_sorgente")
        d["modo"] = config().get("mod_modo") or "automatico"
        d["immagini"] = leggi(cache() / "immagini-stato.json")
        d["genera"] = leggi(cache() / "immagini-genera.json")
        d["programmi"] = {k: v for k, v in leggi(programmi_file()).items() if k in ("core", "plugin", "copia", "app")}
        print(json.dumps(d, ensure_ascii=False))
        return 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
