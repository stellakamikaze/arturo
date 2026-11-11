#!/usr/bin/env python3
"""volta_mod: il mod `arturo` di Volta Celeste si aggiorna da solo da un repository git.

La fonte è la cartella `arturo/` di questo repository (ramo `volta`): mods/arturo, layouts, themes e
i lanciatori. Ogni macchina ne tiene un clone leggero in ~/.cache/volta/mod-git e lo confronta con
il mod installato in ~/.config/herdr-app/mods/arturo (file VERSIONE).

  python3 volta_mod.py controlla            scarica, controlla e installa se c'è una versione nuova
  python3 volta_mod.py installa --da DIR    installa da una cartella `arturo/` locale (prove, /setup)
  python3 volta_mod.py attiva URL [--ramo R]  scrive la sorgente in arturo.json e mette il controllo orario
  python3 volta_mod.py automatico | manuale   accende o spegne il controllo, la sorgente resta
  python3 volta_mod.py stato                l'ultimo esito, in JSON
  python3 volta_mod.py --prova              esce 0: lo usa la copia vecchia prima di sostituirsi

Perché sta fuori dalla cartella del mod (in ~/.config/herdr-app/volta_mod.py): lo lanciano il mod,
all'apertura e ogni ora, e un'attività del sistema ogni ora. Un mod rotto non blocca così il proprio
aggiornamento.

Regole:
  - acceso solo se arturo.json ha `mod_sorgente` e `mod_modo` non è "manuale";
  - la versione è l'impronta git della cartella `arturo/` (non cambia quando il ramo viene ribasato);
  - la copia nuova passa `herdr-app check` prima dello scambio: se è rossa resta il mod di prima, e
    quella versione non si riprova;
  - lo scambio è una rinomina; il mod di prima resta in volta-mod/prima/. Se il sistema rifiuta la
    rinomina (Windows, file in uso) i file si sostituiscono uno alla volta, main.js per ultimo;
  - un mod installato a mano con `installa --da` resta TENUTA_LOCALE ore, poi torna quello del repo;
  - keys.json e arturo.json sono della persona: non si toccano;
  - senza rete o senza accesso al repo l'esito va in mod-stato.json, e il mod lo dice dopo un giorno.

Variabili per i banchi: HERDR_APP_HOME, VOLTA_CACHE, VOLTA_HERDR_APP (JSON: l'argv di herdr-app),
VOLTA_NO_AGENTE=1 (niente LaunchAgent né schtasks), VOLTA_RINOMINA_NEGATA=1 (finge il rifiuto della
rinomina). Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAMO = "volta"
CARTELLA = "arturo"            # la cartella del repository che fa da fonte
TENUTA_LOCALE = 6              # ore in cui un mod installato a mano non viene sostituito
LUCCHETTO_VECCHIO = 15 * 60    # secondi: oltre, un lucchetto rimasto si ignora
ATTESA_GIT = 90                # secondi per fetch e clone
ETICHETTA = "org.stellakamikaze.volta.mod"   # LaunchAgent
ATTIVITA = "VoltaCelesteMod"                  # attività pianificata di Windows
# I lanciatori che l'installazione copia accanto al mod: origine nella fonte, nome di arrivo.
LANCIATORI = (("volta-claude.sh", "volta-claude"), ("nascita.sh", "volta-nascita.sh"),
              ("volta-claude.ps1", "volta-claude.ps1"), ("servizio-claude.ps1", "servizio-claude.ps1"))


def app_home() -> Path:
    return Path(os.environ.get("HERDR_APP_HOME") or Path.home() / ".config" / "herdr-app")


def cache() -> Path:
    return Path(os.environ.get("VOLTA_CACHE") or Path.home() / ".cache" / "volta")


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
    for k in ("rifiutata",):
        if k in prima and k not in d:
            d[k] = prima[k]
    scrivi(stato_file(), d)
    return d


def git(args: list, cwd: Path | None = None, timeout: int = ATTESA_GIT) -> tuple[int, str]:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=15")
    try:
        r = subprocess.run(["git"] + args, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return 124, "git %s non ha risposto in %d s" % (args[0], timeout)
    except OSError as e:
        return 127, "git non parte: %s" % e
    return r.returncode, (r.stdout or "").strip() if r.returncode == 0 else ((r.stderr or r.stdout or "").strip() or "rc %d" % r.returncode)


def ultima_riga(testo: str) -> str:
    righe = [x.strip() for x in testo.splitlines() if x.strip()]
    return righe[-1][:200] if righe else ""


def scarica(url: str, ramo: str) -> tuple[Path | None, str]:
    """Il clone leggero allineato al ramo. Torna (cartella della fonte, "") oppure (None, motivo)."""
    clone = cache() / "mod-git"
    if not (clone / ".git").exists():
        if clone.exists():
            shutil.rmtree(clone, ignore_errors=True)
        clone.parent.mkdir(parents=True, exist_ok=True)
        rc, out = git(["clone", "--quiet", "--filter=blob:none", "--sparse", "--depth", "1", "--branch", ramo,
                       url, str(clone)], timeout=ATTESA_GIT * 2)
        if rc != 0:
            shutil.rmtree(clone, ignore_errors=True)
            return None, ultima_riga(out)
        # --no-cone: solo la cartella della fonte, senza i file della radice del repository
        rc, out = git(["sparse-checkout", "set", "--no-cone", "/" + CARTELLA + "/"], cwd=clone)
        if rc != 0:
            return None, ultima_riga(out)
    else:
        git(["remote", "set-url", "origin", url], cwd=clone)
        rc, out = git(["fetch", "--quiet", "--depth", "1", "origin", ramo], cwd=clone)
        if rc != 0:
            return None, ultima_riga(out)
        rc, out = git(["reset", "--quiet", "--hard", "FETCH_HEAD"], cwd=clone)
        if rc != 0:
            return None, ultima_riga(out)
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


def controlla_mod(cartella: Path) -> str:
    """"" se `herdr-app check` passa sulla copia, altrimenti il motivo."""
    argv = herdr_app()
    if not argv:
        return "non trovo herdr-app per controllare il mod"
    try:
        r = subprocess.run(argv + ["check", str(cartella)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        return "herdr-app check non parte: %s" % str(e)[:160]
    return "" if r.returncode == 0 else (ultima_riga((r.stdout or "") + "\n" + (r.stderr or "")) or "check rosso")


def file_di(radice: Path) -> list:
    return sorted(str(p.relative_to(radice)) for p in radice.rglob("*") if p.is_file())


def un_file_alla_volta(nuovo: Path, mod: Path) -> None:
    """Il ripiego quando la rinomina della cartella è rifiutata: main.js per ultimo, così il mod
    ricarica una volta sola, a copia finita; i file che non ci sono più si tolgono."""
    nuovi = file_di(nuovo)
    for rel in sorted(nuovi, key=lambda r: (r == "main.js", r)):
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
        un_file_alla_volta(nuovo, mod)
        shutil.rmtree(nuovo, ignore_errors=True)
        return "file"
    try:
        os.replace(str(nuovo), str(mod))
    except OSError:
        os.replace(str(prima), str(mod))  # torna il mod di prima
        raise
    return "rinomina"


def contorno(fonte: Path) -> None:
    """Layout, temi e lanciatori accanto al mod. keys.json e arturo.json restano della persona."""
    app = app_home()
    for nome in ("layouts", "themes"):
        for f in sorted((fonte / nome).glob("*")) if (fonte / nome).is_dir() else []:
            if f.is_file():
                (app / nome).mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(f), str(app / nome / f.name))
    for origine, arrivo in LANCIATORI:
        if origine.endswith(".ps1") and os.name != "nt":
            continue
        if (fonte / origine).is_file():
            shutil.copy2(str(fonte / origine), str(app / arrivo))
    # Questo script si sostituisce solo con una copia che parte.
    io_nuovo = fonte / "volta_mod.py"
    if io_nuovo.is_file():
        try:
            parte = subprocess.run([sys.executable, str(io_nuovo), "--prova"], capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.SubprocessError):
            parte = False
        if parte:
            tmp = app / "volta_mod.py.nuovo"
            shutil.copy2(str(io_nuovo), str(tmp))
            os.replace(str(tmp), str(app / "volta_mod.py"))


def installa(fonte: Path, versione: dict) -> tuple[bool, str]:
    """Copia, controlla e scambia. Torna (riuscito, come o motivo)."""
    app = app_home()
    sorgente = fonte / "mods" / "arturo"
    if not (sorgente / "main.js").is_file():
        return False, "in %s non c'è mods/arturo" % fonte
    nuovo = app / "volta-mod" / "nuovo" / "arturo"
    shutil.rmtree(nuovo.parent, ignore_errors=True)
    shutil.copytree(str(sorgente), str(nuovo), ignore=shutil.ignore_patterns("__pycache__", "VERSIONE"))
    scrivi(nuovo / "VERSIONE", dict(versione, installato=time.time()))
    motivo = controlla_mod(nuovo)
    if motivo:
        shutil.rmtree(nuovo.parent, ignore_errors=True)
        return False, motivo
    come = scambia(nuovo, app / "mods" / "arturo", app / "volta-mod" / "prima" / "arturo")
    shutil.rmtree(nuovo.parent, ignore_errors=True)
    contorno(fonte)
    return True, come


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
    l = lucchetto()
    if l is None:
        print("OCCUPATO: un altro controllo è in corso")
        return 0
    try:
        installato = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        v = str(installato.get("versione") or "")
        if v.startswith("locale") and time.time() - float(installato.get("installato") or 0) < TENUTA_LOCALE * 3600:
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
        if leggi(stato_file()).get("rifiutata") == versione["versione"]:
            print("RIFIUTATA %s: il controllo del mod era rosso, aspetto una versione nuova" % versione["corta"])
            return 1
        riuscito, come = installa(fonte, versione)
        if not riuscito:
            segna("rifiutato", versione=versione["corta"], motivo=come, rifiutata=versione["versione"])
            print("RIFIUTATO %s: %s" % (versione["corta"], come))
            return 1
        segna("aggiornato", versione=versione["corta"], come=come, aggiornato=time.time())
        print("AGGIORNATO %s (%s)" % (versione["corta"], come))
        return 0
    finally:
        try:
            l.rmdir()
        except OSError:
            pass


def cmd_installa(argv: list) -> int:
    if len(argv) != 2 or argv[0] != "--da":
        print("uso: volta_mod.py installa --da <cartella arturo/>")
        return 2
    adesso = time.time()
    riuscito, come = installa(Path(argv[1]).resolve(), {"versione": "locale:%d" % adesso, "corta": "locale", "commit": "", "data": ""})
    print(("INSTALLATO a mano (%s): resta %d ore" % (come, TENUTA_LOCALE)) if riuscito else "NON INSTALLATO: " + come)
    return 0 if riuscito else 1


def agente(accendi: bool) -> str:
    """Il controllo orario del sistema: LaunchAgent sul Mac, attività pianificata su Windows."""
    if os.environ.get("VOLTA_NO_AGENTE"):
        return "saltato"
    script = str(app_home() / "volta_mod.py")
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / (ETICHETTA + ".plist")
        dominio = "gui/%d" % os.getuid()
        subprocess.run(["launchctl", "bootout", dominio + "/" + ETICHETTA], capture_output=True)
        if not accendi:
            plist.unlink(missing_ok=True)
            return "tolto"
        percorso = os.pathsep.join([str(Path.home() / ".local" / "bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>%s</string>
<key>ProgramArguments</key><array><string>%s</string><string>%s</string><string>controlla</string></array>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>%s</string></dict>
<key>StartInterval</key><integer>3600</integer>
<key>RunAtLoad</key><true/>
<key>StandardOutPath</key><string>%s</string>
<key>StandardErrorPath</key><string>%s</string>
</dict></plist>
""" % (ETICHETTA, sys.executable, script, percorso, Path.home() / "Library/Logs/volta-mod.log", Path.home() / "Library/Logs/volta-mod.log"), encoding="utf-8")
        r = subprocess.run(["launchctl", "bootstrap", dominio, str(plist)], capture_output=True, text=True)
        return "LaunchAgent" if r.returncode == 0 else "LaunchAgent non caricato: " + ultima_riga(r.stderr or r.stdout)
    if os.name == "nt":
        if not accendi:
            subprocess.run(["schtasks", "/Delete", "/TN", ATTIVITA, "/F"], capture_output=True)
            return "tolta"
        py = Path(sys.executable)
        senza_finestra = py.with_name("pythonw.exe")
        comando = '"%s" "%s" controlla' % (senza_finestra if senza_finestra.exists() else py, script)
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
        return cmd_controlla()
    if argv[:1] == ["installa"]:
        return cmd_installa(argv[1:])
    if argv[:1] == ["attiva"]:
        return cmd_attiva(argv[1:])
    if argv[:1] in (["automatico"], ["manuale"]):
        return cmd_modo(argv[0])
    if argv[:1] == ["stato"]:
        d = leggi(stato_file())
        d["installato"] = leggi(app_home() / "mods" / "arturo" / "VERSIONE")
        d["sorgente"] = config().get("mod_sorgente")
        d["modo"] = config().get("mod_modo") or "automatico"
        print(json.dumps(d, ensure_ascii=False))
        return 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
