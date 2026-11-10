#!/usr/bin/env python3
"""arturo aggiornamenti: Arturo si aggiorna da solo, come Claude Code (16/10/2026, #3477).

Mentre lavori, la barra in basso dice quando c'è una versione nuova. Alla chiusura della sessione
Arturo la installa da solo, con la stessa procedura di /aggiorna: copia di prova, le tue aggiunte
in personale/, controllo della config. Si installano solo i rilasci con tag firmati dalla chiave di
chi mantiene Arturo, verificati con la chiave che hai già installata (firme/rilasci.allowed_signers).

  stato        cosa sa adesso, senza rete: l'avvio della sessione lo stampa
  controlla    scarica i tag e aggiorna lo stato, al massimo una volta all'ora (la barra in basso)
  applica      installa la versione nuova, se tutto torna (la chiusura della sessione); con --avvio
               ammette una sessione aperta, quella che parte (l'avvio, dopo un rinvio)
  manuali      niente si installa da solo: resta l'avviso, e aggiorni tu con /aggiorna
  automatici   torna all'aggiornamento automatico (la scelta di partenza)
  firmato      l'ultimo rilascio, solo se la sua firma è valida: è l'unico che /aggiorna applica
  plugin       col plugin: aggiorna il catalogo, verifica che il tag indicato sia firmato e porti lo sha
               del catalogo, poi claude plugin update e il controllo della copia installata col suo
               MANIFEST firmato; con --verifica si ferma prima di installare (strati F3)

Non si installa niente da solo se: la firma manca o non è di Arturo; la storia pubblicata è stata
riscritta; hai modifiche non salvate in ~/.claude; un'altra sessione di Claude Code è aperta (lo
installa la chiusura dopo, anche con altre sessioni aperte, dal 4/11/2026, oppure l'apertura dopo di Claude
Code se è l'unica sessione, dal 3/11/2026, mai un /clear, dal 4/11/2026); l'aggiornamento va in conflitto su
settings.json o su un CLAUDE.md (negli altri file vince il rilascio, e la tua versione resta in personale/conflitti,
dal 3/11/2026). In tutti questi
casi l'avviso resta, col motivo, e /aggiorna fa il resto con te. Una firma che manca o non torna non
si scavalca neanche con /aggiorna: è il segno di un repository manomesso, e l'avviso dice di non
aggiornare e di segnalarlo a chi mantiene Arturo (17/10/2026, #3504). Una firma che questo computer
non sa verificare (git prima della 2.34, OpenSSH prima della 8.2) blocca allo stesso modo, ma senza
allarme: "firma non verificabile", uscita 4 di firmato. ARTURO_AGGIORNAMENTI=manuali
ha lo stesso effetto di "manuali". Solo libreria standard, Python 3.8 o successivo.

Col plugin (strati F3, 5/11/2026) il codice sta nella cache di Claude Code e non c'è git: stato e
controlla dicono soltanto se c'è un rilascio nuovo, applica non fa niente, e l'aggiornamento passa da
`plugin`, che /aggiorna lancia. Claude
Code installa lo sha scritto nel catalogo anche se nessun tag firmato lo indica (prova del 5/11/2026):
per questo il tag si verifica qui, prima, con la chiave dell'ancora nell'Orsa (hooks/fiducia.py). Se il plugin
arriva da un'altra strada (claude plugin update, il pannello /plugin), stato e il "GIÀ AGGIORNATO" di plugin
uniscono a settings.json le impostazioni nuove, da una copia che torna col suo MANIFEST firmato (#5101).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))

AIUTO = __doc__.split("\n\n")[2] if __doc__ else ""
NOME_PLUGIN = "arturo@arturo"
TAG_PLUGIN = re.compile(r"plugin-v(\d{1,4})\.(\d{1,4})\.(\d{1,6})")
ORA = 3600            # controlla scarica al massimo una volta all'ora
ATTESA_MAX = 90       # secondi: quanto applica aspetta che Claude Code si chiuda davvero
FIRME = "firme/rilasci.allowed_signers"
# Il messaggio di una firma che manca o non torna, uguale ovunque compare (avvio, barra, /aggiorna).
COMPROMISSIONE = "possibile compromissione: non aggiornare, segnala a chi mantiene Arturo"
# Solo questi errori dicono che la firma c'è stata verificata e non torna. Ogni altro errore (git prima
# della 2.34 che non conosce gpg.format=ssh, OpenSSH prima della 8.2 senza `ssh-keygen -Y`, un timeout)
# vuol dire che la verifica non è partita: niente si installa lo stesso, ma non è una compromissione
# (revisione del rilascio del 17/10/2026).
FIRMA_SBAGLIATA = re.compile(r"no signature found|no principal matched|could not verify signature|bad signature|non-tag object",
                             re.I)
# Gli archivi della persona: una loro modifica non salvata non ferma l'aggiornamento. Copia di
# ARCHIVI_PERSONALI di bin/aggiorna-applica.sh, allineata dal banco CP04.
ARCHIVI_PERSONALI = (":(exclude)data/handoffs", ":(exclude)data/todo", ":(exclude)data/memory")
NON_VERIFICABILE = ("questo computer non sa controllare la firma dei rilasci: servono git 2.34 e OpenSSH 8.2, "
                    "o più recenti")


def radice() -> Path:
    return Path(os.environ.get("ARTURO_RADICE") or os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def git(r: Path, *argomenti, timeout: int = 30) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_SSH_COMMAND="ssh -o BatchMode=yes")
    try:
        return subprocess.run(["git", "-C", str(r), *argomenti], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError) as errore:
        return subprocess.CompletedProcess(argomenti, 1, "", str(errore))


def file_stato(r: Path) -> Path:
    return r / "session-env" / "aggiornamento.json"


def file_esito(r: Path) -> Path:
    return r / "session-env" / "aggiornamento-esito.json"


def file_scelta(r: Path) -> Path:
    return r / "data" / "aggiornamenti.json"


def leggi(f: Path) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(f))


def manuali(r: Path) -> bool:
    if os.environ.get("ARTURO_AGGIORNAMENTI", "").strip().lower() == "manuali":
        return True
    return leggi(file_scelta(r)).get("modo") == "manuali"


def sorgente(r: Path) -> str:
    return "upstream" if git(r, "remote", "get-url", "upstream").returncode == 0 else "origin"


def scarica(r: Path, src: str) -> None:
    """Fetch di main e dei tag. Se la versione pubblicata non discende più da quella che la copia
    conosceva, la storia è stata riscritta: lo stato lo ricorda finché un /aggiorna non lo chiarisce."""
    prima = git(r, "rev-parse", "-q", "--verify", f"{src}/main").stdout.strip()
    git(r, "fetch", "--quiet", "--tags", src, "main", timeout=90)
    dopo = git(r, "rev-parse", "-q", "--verify", f"{src}/main").stdout.strip()
    if prima and dopo and prima != dopo and git(r, "merge-base", "--is-ancestor", prima, dopo).returncode != 0:
        scrivi(r / "session-env" / "aggiornamento-storia-riscritta.json", {"prima": prima, "dopo": dopo})


def ultimo_tag(r: Path, src: str) -> str:
    """L'ultimo rilascio pubblicato: il tag più vicino a main della sorgente degli aggiornamenti.
    Un tag firmato ripubblicato sotto un altro nome esce col nome scritto dentro e un suffisso
    (`v1-0-g…`): non è un tag, e verify-tag lo rifiuta.
    Il filtro v* è più largo di quello di sito/installa.sh (v[0-9]*.[0-9]*.[0-9]*), di proposito: un tag
    v-qualcosa senza firma qui diventa l'ultimo rilascio e dà l'avviso di possibile compromissione.
    installa.sh confronta il nome con VERSIONE_MINIMA e gli serve un numero: quel tag lo salta."""
    return git(r, "describe", "--tags", "--abbrev=0", "--match", "v*", f"{src}/main").stdout.strip()


def verifica_firma(r: Path, tag: str) -> tuple:
    """(motivo, compromesso): motivo vuoto se il tag è firmato da una chiave di firme/rilasci.allowed_signers
    della copia installata. compromesso solo se la firma manca o non torna, non se la verifica non è partita.
    È l'unica verifica: la usano l'aggiornamento automatico e /aggiorna."""
    return verifica_tag(r, tag, r / FIRME)


def verifica_tag(r: Path, tag: str, firme: Path) -> tuple:
    """La stessa verifica di verifica_firma, con la chiave in `firme`: la usa anche il plugin."""
    if not firme.is_file():
        return f"manca {FIRME}: la firma non si può verificare", True
    # Un tag leggero non ha firma: verify-tag lo dice con "non-tag object", che non è un errore della
    # verifica ma un rilascio senza firma (review del 7/11/2026, finding 111).
    tipo = git(r, "cat-file", "-t", f"refs/tags/{tag}")
    if tipo.returncode == 0 and tipo.stdout.strip() != "tag":
        return f"il rilascio {tag} non ha la firma di Arturo (tag senza firma)", True
    verifica = git(r, "-c", "gpg.format=ssh", "-c", f"gpg.ssh.allowedSignersFile={firme}", "verify-tag", tag)
    if verifica.returncode == 0:
        # La firma copre il nome scritto dentro il tag, non il nome del ref: un tag firmato vecchio ripubblicato
        # sotto un nome nuovo riporterebbe indietro il codice con una firma valida (finding 109).
        dentro = re.search(r"^tag (\S+)$", git(r, "cat-file", "tag", tag).stdout, re.M)
        if not dentro or dentro.group(1) != tag:
            scritto = dentro.group(1) if dentro else "nessuno"
            return f"il tag {tag} è il rilascio firmato {scritto} ripubblicato con un altro nome", True
        return "", False
    if FIRMA_SBAGLIATA.search(verifica.stderr or ""):
        return f"il rilascio {tag} non ha la firma di Arturo", True
    return NON_VERIFICABILE, False


def calcola(r: Path) -> dict:
    """Lo stato senza rete: la versione nuova, se c'è, e se si può installare da sola."""
    src = sorgente(r)
    tag = ultimo_tag(r, src)
    stato = {"controllato": int(time.time()), "versione": tag, "sorgente": src}
    if not tag:
        return dict(stato, stato="aggiornato", motivo="nessun rilascio con tag")
    commit = git(r, "rev-list", "-n", "1", tag).stdout.strip()
    stato["commit"] = commit
    if not commit or git(r, "merge-base", "--is-ancestor", commit, "HEAD").returncode == 0:
        return dict(stato, stato="aggiornato", motivo="")
    if (r / "session-env" / "aggiornamento-storia-riscritta.json").exists():
        return dict(stato, stato="bloccato", motivo="la storia pubblicata di Arturo è stata riscritta")
    base = git(r, "merge-base", "HEAD", f"{src}/main").stdout.strip()
    if not base or git(r, "merge-base", "--is-ancestor", base, commit).returncode != 0:
        return dict(stato, stato="bloccato", motivo="la versione nuova non discende da quella installata")
    motivo, compromesso = verifica_firma(r, tag)
    if motivo:
        return dict(stato, stato="bloccato", motivo=motivo, compromesso=compromesso,
                    non_verificabile=not compromesso)
    if manuali(r):
        return dict(stato, stato="manuale", motivo="aggiornamenti a mano")
    # Un rilascio tolto con /aggiorna indietro non torna da solo alla chiusura dopo (7/11/2026): lo rimette
    # /aggiorna, o arriva un rilascio più nuovo. Il segno lo scrive bin/aggiorna-applica.sh indietro.
    try:
        tolto = (r / "session-env" / "aggiornamento-tolto").read_text(encoding="utf-8").strip()
    except OSError:
        tolto = ""
    if tolto and tolto == commit:
        return dict(stato, stato="manuale", motivo="l'hai tolto con /aggiorna indietro")
    # Con modifiche non salvate la procedura non parte (APPLICAZIONE NON PARTITA): lo stato lo dice prima,
    # così l'avvio e la barra non promettono un'installazione che non succede (segnalazione n. 49, #4767).
    file = modificati(r)
    if file:
        elenco = ", ".join(file[:5]) + (f" e altri {len(file) - 5}" if len(file) > 5 else "")
        return dict(stato, stato="bloccato", modifiche=file,
                    motivo=f"hai modifiche non ancora salvate con un commit ({elenco})")
    return dict(stato, stato="pronto", motivo="")


def modificati(r: Path) -> list:
    """I file tracciati con modifiche non salvate, archivi della persona esclusi: la stessa domanda di
    modificati() in bin/aggiorna-applica.sh, che resta il controllo che decide. Se git non risponde, la
    lista è vuota e decide la procedura."""
    p = git(r, "status", "--porcelain", "--untracked-files=no", "--", ".", *ARCHIVI_PERSONALI)
    if p.returncode != 0:
        return []
    return [x[3:] for x in p.stdout.splitlines() if x.strip()]


def processi_claude() -> int:
    """Le sessioni di Claude Code aperte su questo computer (l'app desktop non conta)."""
    prova = os.environ.get("ARTURO_ALTRE_SESSIONI")
    if prova is not None:
        return int(prova) if prova.isdigit() else 0
    try:
        if os.name == "nt":
            comando = ("Get-CimInstance Win32_Process -Filter \"Name='claude.exe' or Name='node.exe'\" | "
                       "ForEach-Object { \"$($_.ExecutablePath)`t$($_.CommandLine)\" }")
            uscita = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                                    capture_output=True, text=True, timeout=30).stdout
            return conta_sessioni(uscita.splitlines(), windows=True)
        uscita = subprocess.run(["ps", "-Ao", "args="], capture_output=True, text=True, timeout=30).stdout
        return conta_sessioni(uscita.splitlines(), windows=False)
    except (OSError, subprocess.SubprocessError, ValueError):
        return 1  # nel dubbio una sessione è aperta: si rimanda


# I processi di servizio di Claude Code dalla 2.1.31x: il daemon delle sessioni in background e le sessioni di
# riserva già pronte (bg-spare, bg-pty-host). Non sono una sessione della persona: contati, l'aggiornamento si
# rinviava a ogni chiusura e a ogni avvio, per sempre (9/11/2026: tre installazioni ferme alla v0.2.3 dal 6/11).
# Il servizio si riconosce dai primi argomenti: una sessione con la parola "daemon" nel prompt non è un servizio
# (review del 9/11/2026, #5102).
SERVIZI_CLAUDE = re.compile(r"(?:daemon run|bg-spare --bg-spare|bg-pty-host --bg-pty-host)(?=\s|$)")


def conta_sessioni(righe: list, windows: bool) -> int:
    """Quante righe dei processi sono sessioni di Claude Code. Il ponte con Chrome
    (`claude --chrome-native-host`) non è una sessione: resta acceso finché Chrome è aperto, e contato
    rimandava l'aggiornamento per sempre (segnalazione n. 7, 20/10/2026)."""
    conta = 0
    for riga in righe:
        if not riga.strip() or "--chrome-native-host" in riga:
            continue
        argomenti = riga.split("\t", 1)[-1] if windows else riga
        if SERVIZI_CLAUDE.match(" ".join(argomenti.split()[1:])):
            continue
        if windows:
            if "AnthropicClaude" not in riga and "WindowsApps" not in riga and \
                    (re.search(r"\\\.local\\bin\\claude\.exe", riga, re.I) or "claude-code" in riga.lower()):
                conta += 1
            continue
        parti = riga.split()
        if os.path.basename(parti[0]) == "claude" or "@anthropic-ai/claude-code" in riga:
            conta += 1
    return conta


def cmd_stato(r: Path) -> int:
    """Per l'avvio della sessione: righe da dire a Claude, solo se c'è qualcosa."""
    righe = []
    annuncio = r / "session-env" / "aggiornamenti-annuncio"
    if not annuncio.exists():
        righe.append("ARTURO: da questa versione Arturo si aggiorna da solo alla chiusura della sessione, solo con "
                     "rilasci firmati da chi lo mantiene. La barra in basso dice quando ce n'è uno. Per tenerlo a mano: "
                     "python3 ~/.claude/bin/arturo aggiornamenti manuali. Dillo alla persona in una frase.")
        try:
            annuncio.parent.mkdir(parents=True, exist_ok=True)
            annuncio.write_text(time.strftime("%Y-%m-%d"), encoding="utf-8")
        except OSError:
            pass
    esito = leggi(file_esito(r))
    rinviato = fallito = ""
    # Un rinvio si installa solo all'apertura di Claude Code (#4732, 4/11/2026). SessionStart scatta anche
    # dopo /clear, /compact e una ripresa, col processo di prima vivo: un rilascio che cambia o toglie un mod
    # glielo leva sotto i piedi, e Claude Code carica il mod nuovo solo all'apertura dopo. Così la rotazione
    # automatica (/clear e /inizio) restava senza il tool ruota. ARTURO_AVVIO è il "source" dell'hook:
    # vuoto vale come apertura, per chi lancia `stato` a mano.
    a_freddo = os.environ.get("ARTURO_AVVIO", "startup") in ("", "startup")
    if esito and not esito.get("mostrato"):
        if esito.get("esito") == "APPLICATO":
            righe.append(f"ARTURO: aggiornato a {esito.get('versione')} alla chiusura della sessione. /novita racconta "
                         "cosa cambia.")
            for nome in esito.get("commentate") or []:
                righe.append(f"ARTURO: l'aggiornamento ha cambiato {nome}, e le righe che la persona ci aveva aggiunto sono "
                             f"ora in personale/{Path(nome).name}, commentate: non girano più. Diglielo in una frase e "
                             "rileggile con lei: quelle che servono tornano attive togliendo il commento.")
        elif esito.get("esito") == "RINVIATO":
            rinviato = esito.get("versione", "")
        else:
            fallito = esito.get("versione", "")
            righe.append(f"ARTURO: l'aggiornamento automatico a {esito.get('versione')} non è partito "
                         f"({esito.get('riga') or 'motivo sconosciuto'}). Scaricalo con /aggiorna.")
        try:
            # Il rinvio visto dopo un /clear resta da mostrare: lo installa l'apertura dopo.
            if a_freddo or esito.get("esito") != "RINVIATO":
                scrivi(file_esito(r), dict(esito, mostrato=True))
        except OSError:
            pass
    righe.extend(conflitti_da_dire(r))
    stato = calcola(r)
    vecchio = leggi(file_stato(r))
    stato["controllato"] = vecchio.get("controllato", 0)  # calcola non scarica: l'ultimo controllo resta quello
    try:
        scrivi(file_stato(r), stato)
    except OSError:
        pass
    if stato["stato"] == "pronto" and rinviato == stato["versione"] and not a_freddo:
        righe.append(f"ARTURO: la versione {rinviato} si installa alla prossima chiusura di una sessione o alla prossima "
                     "apertura di Claude Code, non dopo un /clear: la sessione aperta tiene i suoi strumenti.")
    elif stato["stato"] == "pronto" and rinviato == stato["versione"] and processi_claude() <= 1             and avvia_staccato(r, "applica", "--avvio"):
        # Un rilascio rinviato si installa all'avvio dopo, se questa è l'unica sessione (3/11/2026): un'installazione è
        # restata indietro al 23/10 perché alla chiusura c'era sempre un'altra sessione aperta, e l'attesa scadeva.
        righe.append(f"ARTURO: installo ora la versione {rinviato}, rinviata alla chiusura scorsa perché c'era un'altra "
                     "sessione aperta. Se un hook dà errore, riapri la sessione. Dillo alla persona in una frase.")
    elif stato["stato"] == "pronto" and rinviato == stato["versione"]:
        righe.append(f"ARTURO: la versione {rinviato} non si è installata alla chiusura scorsa, perché un'altra "
                     "sessione di Claude Code era ancora aperta. Si installa alla prossima chiusura di una sessione, anche "
                     "con altre aperte, all'avvio di una sessione sola, oppure subito con /aggiorna. Se dopo una sessione "
                     "rimasta aperta dà errori, chiudila e riaprila. Dillo alla persona in una frase.")
    elif stato["stato"] == "pronto" and fallito == stato["versione"]:
        pass  # la riga di "non è partito" basta: dire anche "si installa da sola" la contraddice (n. 49)
    elif stato["stato"] == "pronto":
        righe.append(f"ARTURO: c'è la versione {stato['versione']}: si installa da sola alla chiusura della sessione.")
    elif stato.get("modifiche"):
        righe.append(f"ARTURO: la versione {stato['versione']} non si installa da sola: {stato['motivo']}. Si installa "
                     "alla chiusura dopo che le salvi (/fine lo fa), oppure subito con /aggiorna, che le salva col tuo "
                     "sì. Dillo alla persona in una frase.")
    elif stato.get("compromesso"):
        righe.append(f"ARTURO: {COMPROMISSIONE}. {stato['motivo'][0].upper()}{stato['motivo'][1:]}: la versione "
                     f"{stato['versione']} non si installa, né da sola né con /aggiorna. Dillo alla persona con queste "
                     "parole, e proponi /segnala o la segnalazione privata di SECURITY.md.")
    elif stato.get("non_verificabile"):
        righe.append(f"ARTURO: c'è la versione {stato['versione']}, ma {stato['motivo']}. Non si installa, né da sola "
                     "né con /aggiorna, finché git e OpenSSH non sono aggiornati. Dillo alla persona in una frase: "
                     "non è un problema di sicurezza.")
    elif stato["stato"] in ("manuale", "bloccato"):
        righe.append(f"ARTURO: c'è un aggiornamento ({stato['versione']}): scaricalo con /aggiorna. "
                     f"Non si installa da solo: {stato['motivo']}.")
    if righe:
        print("\n".join(righe))
    return 0


def conflitti_da_dire(r: Path) -> list:
    """Le cartelle nuove di personale/conflitti (bin/aggiorna-applica.sh, 3/11/2026): una riga per l'avvio, una
    volta sola per cartella. Il registro di quelle già dette sta in session-env/conflitti-detti.json."""
    cartella = r / "personale" / "conflitti"
    detti_f = r / "session-env" / "conflitti-detti.json"
    detti = leggi(detti_f).get("detti", [])
    nuove = sorted(d for d in (cartella.iterdir() if cartella.is_dir() else []) if d.is_dir() and d.name not in detti)
    if not nuove:
        return []
    righe = []
    for d in nuove:
        try:
            file = [x for x in (d / "FILE.txt").read_text(encoding="utf-8").splitlines() if x.strip()]
        except OSError:
            file = []
        versione = ""
        try:
            versione = (d / "VERSIONE.txt").read_text(encoding="utf-8").strip()
        except OSError:
            pass
        cosa = ", ".join(file[:5]) + (f" e altri {len(file) - 5}" if len(file) > 5 else "") if file else             "una copia di prova che aspettava (copia-in-attesa.patch)"
        righe.append(f"ARTURO: nell'aggiornamento{' a ' + versione if versione else ''} le modifiche della persona a {cosa} "
                     f"andavano in conflitto col rilascio: ora c'è la versione di Arturo, e le sue stanno in "
                     f"personale/conflitti/{d.name} (differenze.patch dice cosa aveva cambiato). Diglielo in una frase e "
                     "proponi di riportarle nell'Orsa: personale/<comando>.md, una skill sua, un'impostazione .local.")
    try:
        scrivi(detti_f, {"detti": detti + [d.name for d in nuove]})
    except OSError:
        pass
    return righe


def avvia_staccato(r: Path, *comando: str) -> bool:
    """Lancia questo file con `comando` staccato dalla sessione, come fa hooks/session-end.sh: l'uscita va in
    session-env/aggiornamento.log. ARTURO_BASH arriva da chi chiama (session-start.sh passa il suo $BASH): su
    Windows `bash` del PATH può essere quello di WSL."""
    if manuali(r):
        return False
    try:
        (r / "session-env").mkdir(parents=True, exist_ok=True)
        log = open(r / "session-env" / "aggiornamento.log", "ab")
    except OSError:
        return False
    opzioni = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log, "cwd": str(r)}
    if os.name == "nt":
        opzioni["creationflags"] = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP: con DETACHED_PROCESS ogni git figlio apriva una finestra
    else:
        opzioni["start_new_session"] = True
    try:
        subprocess.Popen([sys.executable, os.path.realpath(__file__), *comando], **opzioni)
        return True
    except OSError:
        return False
    finally:
        log.close()


def cmd_firmato(r: Path) -> int:
    """Per /aggiorna: stampa l'ultimo rilascio della sorgente solo se la firma è valida (uscita 0).
    Senza rilasci esce con 1, con una firma che manca o non torna esce con 3 e lo dice, se la firma
    non si può verificare su questo computer esce con 4. Un rilascio già installato si stampa senza
    verifica, come in calcola: un tag vecchio senza firma non è un allarme. Non scarica niente: il
    fetch lo fa chi chiama. main non si applica mai, solo questo tag."""
    tag = ultimo_tag(r, sorgente(r))
    if not tag:
        print("NESSUN RILASCIO: la sorgente degli aggiornamenti non ha tag di rilascio. Non applico niente.",
              file=sys.stderr)
        return 1
    commit = git(r, "rev-list", "-n", "1", tag).stdout.strip()
    if commit and git(r, "merge-base", "--is-ancestor", commit, "HEAD").returncode == 0:
        print(tag)
        return 0
    motivo, compromesso = verifica_firma(r, tag)
    if motivo and compromesso:
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). Non applico niente: "
              "si segnala con /segnala, o in privato come dice SECURITY.md.", file=sys.stderr)
        return 3
    if motivo:
        print(f"FIRMA NON VERIFICABILE: {motivo}. Non applico niente. Non è un problema di sicurezza: aggiorna "
              "git e OpenSSH, poi rilancia /aggiorna.", file=sys.stderr)
        return 4
    print(tag)
    return 0


def cmd_controlla(r: Path, forza: bool = False) -> int:
    vecchio = leggi(file_stato(r))
    if not forza and time.time() - float(vecchio.get("controllato") or 0) < ORA:
        return 0
    scarica(r, sorgente(r))
    try:
        scrivi(file_stato(r), calcola(r))
    except OSError:
        pass
    return 0


def cmd_applica(r: Path, ammesse: int = 0) -> int:
    blocco = r / "session-env" / "aggiornamento.lock"
    try:
        blocco.parent.mkdir(parents=True, exist_ok=True)
        blocco.mkdir()
    except FileExistsError:
        if time.time() - blocco.stat().st_mtime < 900:
            return 0  # un'altra applicazione è in corso
        shutil.rmtree(str(blocco), ignore_errors=True)
        blocco.mkdir()
    except OSError:
        return 1
    try:
        return _applica(r, ammesse)
    finally:
        shutil.rmtree(str(blocco), ignore_errors=True)


def _applica(r: Path, ammesse: int = 0) -> int:
    """ammesse: le sessioni che possono restare aperte. 0 alla chiusura; 1 all'avvio (`applica --avvio`),
    dove la sessione che parte è una."""
    if manuali(r) or not git(r, "remote").stdout.strip():
        return 0
    # Prima si guarda se c'è qualcosa da installare: aspettare le sessioni senza motivo terrebbe
    # vivo un processo (e il suo log) per niente.
    scarica(r, sorgente(r))
    stato = calcola(r)
    scrivi(file_stato(r), stato)
    if stato["stato"] != "pronto":
        if stato["stato"] != "aggiornato":
            _segnala_ostacolo(r, stato)
        return 0
    limite = time.time() + float(os.environ.get("ARTURO_ATTESA_MAX", ATTESA_MAX))
    # Un rilascio già rinviato una volta non aspetta più le altre sessioni (#4074, Federico 2/11/2026): chi
    # tiene sempre una sessione aperta restava indietro per giorni, come un'installazione al 23/10. Le sessioni rimaste
    # aperte leggono gli hook nuovi da subito, come dopo un /aggiorna; i mod cambiano alla loro riapertura.
    attende = ammesse > 0 or not rinvio_in_attesa(r, stato)
    while attende and processi_claude() > ammesse:
        if time.time() >= limite:
            _segnala_ostacolo(r, stato, "rinviato")
            # Un'altra sessione è aperta: la installa la chiusura dopo. L'esito resta scritto, così
            # l'avvio dopo dice perché non è successo, invece di ripetere che si installa da sola.
            _esito(r, stato["versione"], "RINVIATO", "un'altra sessione di Claude Code era ancora aperta")
            return 0
        time.sleep(2)
    stato = calcola(r)
    if stato["stato"] != "pronto":
        return 0
    tag, src = stato["versione"], stato["sorgente"]
    lavoro = Path(tempfile.mkdtemp(prefix="arturo-aggiorna."))
    try:
        procedura = lavoro / "aggiorna-applica.sh"
        testo = git(r, "show", f"{tag}:bin/aggiorna-applica.sh")
        if testo.returncode != 0 or not testo.stdout.strip():
            return _esito(r, tag, "APPLICAZIONE NON PARTITA", "il rilascio non ha la procedura di applicazione")
        with open(str(procedura), "w", encoding="utf-8", newline="\n") as uscita:  # write_text(newline=) vuole Python 3.10
            uscita.write(testo.stdout)
        bash = os.environ.get("ARTURO_BASH") or shutil.which("bash") or "bash"
        modo = "merge" if src == "upstream" else "rebase"
        p = subprocess.run([bash, str(procedura), str(r), modo, tag], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600, cwd=str(r),
                           env=dict(os.environ, ARTURO_AGGIORNA_AUTOMATICO="1"))
    except (OSError, subprocess.SubprocessError) as errore:
        return _esito(r, tag, "APPLICAZIONE NON PARTITA", str(errore)[:200])
    finally:
        shutil.rmtree(str(lavoro), ignore_errors=True)
    righe = [x for x in (p.stdout + p.stderr).splitlines() if x.strip()]
    i = next((n for n, x in enumerate(righe) if re.match(r"^(APPLICATO|GIÀ AGGIORNATO|APPLICAZIONE|RIPRISTINO)", x)), -1)
    esito = righe[i] if i >= 0 else ""
    if esito.endswith(":"):
        # "questi file hanno modifiche tue…:" e l'elenco sotto, rientrato: l'avvio dice quali file (n. 49).
        sotto = [x.strip() for x in righe[i + 1:i + 6] if x.startswith("  ")]
        if sotto:
            esito += " " + ", ".join(sotto)
    if esito.startswith("GIÀ AGGIORNATO"):
        scrivi(file_stato(r), calcola(r))
        return 0
    parola = "APPLICATO" if esito.startswith("APPLICATO") else (esito.split(":")[0] or "FALLITO")
    # Le righe aggiunte a un hook di sessione che separa ha spostato, commentate, in personale/: non girano più, e
    # l'avvio lo dice una volta (finding 22 del 7/11/2026). /aggiorna le rilegge con la persona; qui nessuno le vedeva.
    commentate = [re.sub(r"^\s*SEPARATO:\s*", "", x).split(" -> ")[0].strip() for x in righe
                  if "SEPARATO:" in x and "righe commentate" in x]
    _esito(r, tag, parola, esito[:240], commentate=commentate[:10])
    scrivi(file_stato(r), calcola(r))
    return 0 if parola == "APPLICATO" else 1


def _moduli():
    """fiducia e radici si caricano solo col plugin: l'aggiornamento della copia in ~/.claude non deve
    dipendere da file arrivati dopo, come una copia ferma a prima di F3 che riceve questo script."""
    import fiducia  # noqa: PLC0415
    import radici  # noqa: PLC0415
    return fiducia, radici


def modo_plugin() -> bool:
    """Vero se questo codice gira dalla cache dei plugin (niente git accanto): strati F3."""
    try:
        fiducia, radici = _moduli()
    except ImportError:
        return False
    return fiducia.plugin(radici.radice_arturo())


def _claude(*argomenti, timeout: int = 300) -> subprocess.CompletedProcess:
    comando = [os.environ.get("ARTURO_CLAUDE") or "claude", "plugin", *argomenti]
    try:
        return subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as errore:
        return subprocess.CompletedProcess(comando, 1, "", str(errore))


def installato(orsa: Path) -> dict:
    """La voce di Arturo in plugins/installed_plugins.json: installPath, version, gitCommitSha."""
    voci = (leggi(orsa / "plugins" / "installed_plugins.json").get("plugins") or {}).get(NOME_PLUGIN) or []
    voci = [v for v in voci if isinstance(v, dict)]
    return next((v for v in voci if v.get("scope") == "user"), voci[0] if voci else {})


def voce_catalogo(orsa: Path) -> dict:
    """La voce di Arturo nel catalogo scaricato da Claude Code (plugins/known_marketplaces.json)."""
    catalogo = (leggi(orsa / "plugins" / "known_marketplaces.json").get("arturo") or {}).get("installLocation")
    if not catalogo:
        return {}
    dati = leggi(Path(catalogo) / ".claude-plugin" / "marketplace.json")
    return next((p for p in dati.get("plugins") or [] if isinstance(p, dict) and p.get("name") == "arturo"), {})


# La voce di Arturo nel catalogo dice solo quale rilascio installare (7/11/2026). Claude Code unisce al plugin
# anche hooks, mcpServers, commands e le altre chiavi della voce, che il catalogo non firmato potrebbe
# aggiungere a un rilascio firmato senza cambiarne lo sha: ogni chiave fuori da queste è una manomissione.
CHIAVI_VOCE = {"name", "description", "version", "source", "author", "homepage", "repository", "license",
               "keywords", "category", "tags"}
CHIAVI_SORGENTE = {"source", "repo", "url", "ref", "sha"}
# Un indirizzo del catalogo si scarica solo con questi schemi: un testo che comincia con "-" git lo
# leggerebbe come opzione (--upload-pack=<comando>), prima di ogni verifica della firma (7/11/2026).
URL_AMMESSO = re.compile(r"(https://|file://)\S+")


def voce_estranea(voce: dict) -> str:
    """Il motivo, se la voce del catalogo porta chiavi che non servono a scegliere il rilascio; altrimenti ""."""
    estranee = sorted(set(voce) - CHIAVI_VOCE)
    sorgente = voce.get("source")
    if isinstance(sorgente, dict):
        estranee += sorted(f"source.{k}" for k in set(sorgente) - CHIAVI_SORGENTE)
    if estranee:
        return f"il catalogo aggiunge ad Arturo componenti non firmati ({', '.join(estranee[:4])})"
    return ""


def numero(testo: str) -> tuple:
    m = re.search(r"(\d{1,4})\.(\d{1,4})\.(\d{1,6})", testo or "")
    return tuple(int(x) for x in m.groups()) if m else ()


def _ripristina(orsa: Path, prima: dict) -> str:
    """Dopo un controllo fallito su una copia già installata, rimette in installed_plugins.json la voce di prima, se
    la sua cartella c'è ancora (review del 7/11/2026, finding 110). "rimessa" se è riuscito, "scaricata" se no."""
    f = orsa / "plugins" / "installed_plugins.json"
    dati = leggi(f)
    voci = (dati.get("plugins") or {}).get(NOME_PLUGIN)
    if not prima.get("installPath") or not Path(str(prima["installPath"])).is_dir() or not isinstance(voci, list):
        return "scaricata"
    utente = next((i for i, v in enumerate(voci) if isinstance(v, dict) and v.get("scope") == prima.get("scope")), None)
    if utente is None:
        return "scaricata"
    voci[utente] = prima
    try:
        scrivi(f, dati)
    except OSError:
        return "scaricata"
    return "rimessa" if installato(orsa).get("gitCommitSha") == prima.get("gitCommitSha") else "scaricata"


def _blocca(motivo: str, compromesso: bool, scaricata: str = "") -> int:
    if compromesso and scaricata == "rimessa":
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). Ho rimesso la versione di "
              "prima: si segnala con /segnala, o in privato come dice SECURITY.md.", file=sys.stderr)
        return 3
    if compromesso and scaricata:
        # Dopo claude plugin update la copia nuova è già nella cache, e parte alla prossima apertura.
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). La copia nuova è già "
              "scaricata e non sono riuscito a rimettere quella di prima: non riavviare Claude Code prima di aver "
              "segnalato con /segnala, o in privato come dice SECURITY.md.", file=sys.stderr)
        return 3
    if compromesso:
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). Non applico niente: "
              "si segnala con /segnala, o in privato come dice SECURITY.md.", file=sys.stderr)
        return 3
    print(f"FIRMA NON VERIFICABILE: {motivo}. Non applico niente. Non è un problema di sicurezza: aggiorna "
          "git e OpenSSH, poi rilancia /aggiorna.", file=sys.stderr)
    return 4


def verifica_catalogo(orsa: Path) -> tuple:
    """(rc, tag, sha): rc 0 se il catalogo indica un tag firmato dalla chiave dell'ancora e il tag porta
    proprio lo sha del catalogo; rc 2 se quello sha è già installato. Gli errori li stampa."""
    fiducia, radici = _moduli()
    radice_arturo = radici.radice_arturo
    voce = voce_catalogo(orsa)
    sorgente = voce.get("source") if isinstance(voce.get("source"), dict) else {}
    tag, sha = str(sorgente.get("ref") or ""), str(sorgente.get("sha") or "")
    if not voce:
        print("NESSUN RILASCIO: il catalogo di Arturo non c'è o non elenca Arturo (claude plugin marketplace list).",
              file=sys.stderr)
        return 1, "", ""
    estranea = voce_estranea(voce)
    if estranea:
        return _blocca(estranea, True), tag, sha
    if not TAG_PLUGIN.fullmatch(tag) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        return _blocca("il catalogo non fissa Arturo a un tag plugin-vN.N.N e al suo sha", True), tag, sha
    if sorgente.get("source") == "github" and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", str(sorgente.get("repo"))):
        url = f"https://github.com/{sorgente['repo']}.git"
    elif sorgente.get("source") == "url" and URL_AMMESSO.fullmatch(str(sorgente.get("url"))):
        url = sorgente["url"]
    else:
        return _blocca("il catalogo indica una sorgente che Arturo non sa verificare", True), tag, sha
    prima = installato(orsa)
    if prima.get("gitCommitSha") == sha:
        return 2, tag, sha
    if numero(tag) < numero(str(prima.get("version") or "")):
        return _blocca(f"il catalogo indica {tag}, più vecchio della versione installata {prima.get('version')}",
                       True), tag, sha
    lavoro = Path(tempfile.mkdtemp(prefix="arturo-tag."))
    try:
        git(lavoro, "init", "-q")
        scarico = git(lavoro, "fetch", "--quiet", "--depth=1", "--no-tags", "--", url, f"+refs/tags/{tag}:refs/tags/{tag}",
                      timeout=120)
        if scarico.returncode != 0:
            print(f"NESSUN RILASCIO: non riesco a scaricare il tag {tag} ({(scarico.stderr or '').strip()[:160]}). "
                  "Rete? Non applico niente.", file=sys.stderr)
            return 1, tag, sha
        motivo, compromesso = verifica_tag(lavoro, tag, fiducia.firmatari_per(radice_arturo(), orsa))
        if motivo:
            return _blocca(motivo, compromesso), tag, sha
        if git(lavoro, "rev-parse", f"{tag}^{{commit}}").stdout.strip() != sha:
            return _blocca(f"lo sha del catalogo non è quello del rilascio firmato {tag}", True), tag, sha
        # Il MANIFEST firmato si controlla qui, prima di claude plugin update: dopo, la copia nuova è già nella
        # cache e parte alla prossima apertura (review del 7/11/2026, finding 110).
        albero = lavoro / "albero"
        albero.mkdir()
        estratto = git(lavoro, "-c", "core.autocrlf=false", f"--work-tree={albero}", "checkout", "-q", "-f", sha,
                       "--", ".", timeout=120)
        if estratto.returncode != 0:
            print(f"NESSUN RILASCIO: non riesco a leggere i file di {tag} ({(estratto.stderr or '').strip()[:160]}). "
                  "Non applico niente.", file=sys.stderr)
            return 1, tag, sha
        controllo = fiducia.controlla(albero, orsa)
        if controllo["firma"] != "ok":
            return _blocca(controllo["motivo"], controllo["firma"] != "non-verificabile"), tag, sha
        diversi = controllo["cambiati"] + controllo["mancano"]
        if diversi:
            return _blocca(f"il rilascio {tag} non è come il suo MANIFEST firmato ({', '.join(diversi[:3])})",
                           True), tag, sha
    finally:
        shutil.rmtree(str(lavoro), ignore_errors=True)
    return 0, tag, sha


def versione_nuova_plugin(orsa: Path) -> str:
    """La versione del catalogo scaricato, se è più nuova di quella installata; altrimenti "".
    Solo un confronto di numeri: la verifica del tag firmato la fa /aggiorna (cmd_plugin)."""
    voce = voce_catalogo(orsa)
    nel_catalogo = str(voce.get("version") or (voce.get("source") or {}).get("ref") or "")
    installata = str(installato(orsa).get("version") or "")
    if numero(nel_catalogo) and numero(installata) and numero(nel_catalogo) > numero(installata):
        return ".".join(str(x) for x in numero(nel_catalogo))
    return ""


def controlla_plugin(r: Path, forza: bool = False) -> int:
    """Col plugin (#4860, 6/11/2026): al massimo una volta all'ora la barra fa scaricare il catalogo, e lo stato
    dice se c'è un rilascio più nuovo di quello installato. Non installa niente: lo fa /aggiorna, verificato."""
    vecchio = leggi(file_stato(r))
    if not forza and time.time() - float(vecchio.get("controllato") or 0) < ORA:
        return 0
    _, radici = _moduli()
    _claude("marketplace", "update", "arturo", timeout=120)
    estranea = voce_estranea(voce_catalogo(radici.radice_orsa()))
    nuova = versione_nuova_plugin(radici.radice_orsa())
    if estranea:
        stato = {"stato": "bloccato", "compromesso": True, "motivo": estranea, "versione": nuova, "plugin": True}
    elif nuova:
        stato = {"stato": "manuale", "versione": nuova, "plugin": True}
    else:
        stato = {"stato": "aggiornato", "plugin": True}
    try:
        scrivi(file_stato(r), dict(stato, controllato=time.time()))
    except OSError:
        pass
    return 0


def segna_aggiornato(r: Path) -> None:
    """Dopo /aggiorna la barra non deve dire ancora "serve /aggiorna" fino al controllo dopo."""
    try:
        scrivi(file_stato(r), {"stato": "aggiornato", "plugin": True, "controllato": time.time()})
    except OSError:
        pass


def stato_plugin(r: Path) -> int:
    """La riga dell'avvio col plugin: solo se l'ultimo controllo ha visto un rilascio più nuovo, ancora non installato.

    Il controllo lo lancia anche l'avvio, staccato: chi ha una barra sua non lancia mai quello della barra di Arturo."""
    _, radici = _moduli()
    stato = leggi(file_stato(r))
    if time.time() - float(stato.get("controllato") or 0) >= ORA:
        avvia_staccato(r, "controlla")
    if stato.get("plugin") and stato.get("compromesso"):
        print(f"ARTURO: {COMPROMISSIONE}. {stato.get('motivo', '')}. Non riaprire Claude Code prima di aver segnalato: "
              "dillo alla persona con queste parole, e proponi /segnala o la segnalazione privata di SECURITY.md.")
        return 0
    riga = "" if stato.get("compromesso") else impostazioni_indietro(radici.radice_arturo(), radici.radice_orsa())
    if riga:
        print(f"ARTURO: {riga} Dillo alla persona in una frase.")
    if stato.get("plugin") and stato.get("stato") == "manuale" and stato.get("versione") \
            and versione_nuova_plugin(radici.radice_orsa()) == stato["versione"]:
        print(f"ARTURO: c'è la versione {stato['versione']} di Arturo. /aggiorna la installa dopo averne verificato la "
              "firma, poi riapri Claude Code. Dillo alla persona in una frase.")
    return 0


def cmd_plugin(solo_verifica: bool = False) -> int:
    """/aggiorna col plugin. Uscite: 0 applicato o già aggiornato, 1 niente da applicare o errore, 3 possibile
    compromissione, 4 firma non verificabile su questo computer."""
    fiducia, radici = _moduli()
    orsa = radici.radice_orsa()
    catalogo = _claude("marketplace", "update", "arturo", timeout=180)
    if catalogo.returncode != 0:
        print(f"CATALOGO NON AGGIORNATO: {(catalogo.stderr or catalogo.stdout).strip()[:200]}. Verifico quello che ho.",
              file=sys.stderr)
    rc, tag, sha = verifica_catalogo(orsa)
    if rc == 2:
        segna_aggiornato(radice())
        print(f"GIÀ AGGIORNATO: {tag}")
        # Il plugin può essere arrivato da un'altra strada (claude plugin update, il pannello /plugin): le
        # impostazioni restavano quelle di prima, e qui nessuno lo diceva (#5101).
        percorso = str(installato(orsa).get("installPath") or "")
        riga = impostazioni_indietro(Path(percorso), orsa) if percorso else ""
        if riga:
            print(riga)
        return 0
    if rc != 0:
        return rc
    if solo_verifica:
        print(tag)
        return 0
    prima = installato(orsa)
    aggiorna = _claude("update", NOME_PLUGIN)
    if aggiorna.returncode != 0:
        print(f"APPLICAZIONE NON PARTITA: claude plugin update non è riuscito "
              f"({(aggiorna.stderr or aggiorna.stdout).strip()[:200]}). Non ho toccato niente.")
        return 1
    dopo = installato(orsa)
    copia = Path(str(dopo.get("installPath") or ""))
    if dopo.get("gitCommitSha") != sha:
        return _blocca(f"Claude Code ha installato {str(dopo.get('gitCommitSha'))[:12]}, non lo sha verificato "
                       f"{sha[:12]}", True, scaricata=_ripristina(orsa, prima))
    controllo = fiducia.controlla(copia, orsa)
    if controllo["firma"] != "ok":
        return _blocca(controllo["motivo"], controllo["firma"] != "non-verificabile", scaricata=_ripristina(orsa, prima))
    diversi = controllo["cambiati"] + controllo["mancano"]
    if diversi:
        return _blocca(f"la copia installata non è come il MANIFEST firmato ({', '.join(diversi[:3])})", True,
                       scaricata=_ripristina(orsa, prima))
    # Una chiave nuova entra nell'ancora solo da una copia verificata con la chiave di prima.
    fiducia.fissa_ancora(copia, orsa)
    segna_aggiornato(radice())
    impostazioni = applica_impostazioni(copia)
    print(f"APPLICATO: {tag}. Riavvia Claude Code per usarlo.")
    if impostazioni:
        print(impostazioni)
    return 0


def applica_impostazioni(copia: Path) -> str:
    """Le voci di settings.json che il plugin non porta (permessi, regole di blocco, env, autoMode), dal frammento
    della copia appena verificata: senza, un rilascio che aggiungeva una regola deny non arrivava mai (finding 18
    del 7/11/2026). La riga da dire, vuota se è andato tutto bene."""
    script = copia / "bin" / "impostazioni.py"
    if not (copia / "impostazioni" / "arturo.json").is_file() or not script.is_file():
        return ""
    try:
        p = subprocess.run([sys.executable, str(script), "applica"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as errore:
        return f"IMPOSTAZIONI NON APPLICATE ({str(errore)[:120]}): le voci nuove di Arturo arrivano con /setup."
    if p.returncode == 0:
        return ""
    motivo = next((x.strip() for x in (p.stderr + p.stdout).splitlines() if x.strip()), "motivo sconosciuto")
    return (f"IMPOSTAZIONI NON APPLICATE: {motivo[:240]} Le voci nuove di Arturo in settings.json (permessi, regole di "
            "blocco) arrivano con /setup, che chiede a te le voci in conflitto.")


def impostazioni_indietro(copia: Path, orsa: Path) -> str:
    """Le impostazioni di una copia arrivata fuori da /aggiorna (claude plugin update, il pannello /plugin): hook e
    skill nuovi, settings.json di prima, e una regola di blocco nuova non arrivava mai (#5101, 10/11/2026). Se il
    frammento della copia è diverso da quello del blocco, e la copia torna col suo MANIFEST firmato, lo unisce.
    Senza blocco tace: la prima unione la fa /setup. La riga da dire, vuota se non c'era niente da fare."""
    frammento = leggi(copia / "impostazioni" / "arturo.json")
    blocco = leggi(orsa / "data" / "arturo-impostazioni.lock")
    if not frammento or not blocco or blocco.get("frammento") == frammento:
        return ""
    fiducia, _ = _moduli()
    try:
        controllo = fiducia.controlla(copia, orsa)
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""  # all'avvio un errore qui non deve togliere le righe che seguono
    if controllo["firma"] != "ok" or controllo["cambiati"] or controllo["mancano"]:
        return ""  # la deriva dell'avvio dice già che la copia non torna
    riga = applica_impostazioni(copia)
    if riga:
        return riga
    versione = leggi(copia / ".claude-plugin" / "plugin.json").get("version") or "installata"
    return (f"IMPOSTAZIONI APPLICATE: le voci nuove della versione {versione} di Arturo (permessi, regole di blocco) "
            "sono ora in settings.json.")


def rinvio_in_attesa(r: Path, stato: dict) -> bool:
    """Vero se una chiusura di prima ha già rinviato un rilascio che manca ancora: lo stesso che è pronto ora,
    o uno più vecchio rimasto fuori. Un rinvio poi installato con /aggiorna non conta più."""
    esito = leggi(file_esito(r))
    if esito.get("esito") != "RINVIATO" or not esito.get("versione"):
        return False
    if esito["versione"] == stato.get("versione"):
        return True
    commit = git(r, "rev-list", "-n", "1", esito["versione"]).stdout.strip()
    return bool(commit) and git(r, "merge-base", "--is-ancestor", commit, "HEAD").returncode != 0


def _segnala_ostacolo(r: Path, stato: dict, valore: str = "") -> None:
    """Un evento `aggiorna` per il motivo che ferma un rilascio, una sola volta per versione e motivo
    (20/10/2026, #3637): senza, un aggiornamento rinviato o bloccato non lasciava traccia, e non si
    capiva perché un'installazione restava indietro. Le categorie sono chiuse: mai il testo del motivo."""
    if not valore:
        motivo = stato.get("motivo", "")
        if stato.get("stato") == "manuale":
            valore = "manuale"
        elif stato.get("compromesso"):
            valore = "bloccato-firma"
        elif stato.get("non_verificabile"):
            valore = "bloccato-verifica"
        elif "riscritta" in motivo:
            valore = "bloccato-storia"
        elif "non discende" in motivo:
            valore = "bloccato-versione"
        else:
            return
    versione = stato.get("versione", "")
    f = r / "session-env" / "aggiornamento-segnalato.json"
    if leggi(f).get(versione) == valore:
        return
    try:
        scrivi(f, {versione: valore})
        subprocess.run([sys.executable, str(r / "bin" / "telemetria.py"), "registra", "aggiorna", valore],
                       capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        pass


def _esito(r: Path, tag: str, parola: str, riga: str, commentate: list = None) -> int:
    dati = {"quando": int(time.time()), "versione": tag, "esito": parola, "riga": riga, "mostrato": False}
    if commentate:
        dati["commentate"] = commentate
    scrivi(file_esito(r), dati)
    return 0 if parola == "APPLICATO" else 1


def main(argv: list) -> int:
    r = radice()
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    try:
        if argv and argv[0] == "plugin" and argv[1:] in ([], ["--verifica"]):
            if not modo_plugin():
                print("COPIA IN ~/.claude: Arturo non è installato come plugin, vale la procedura con git.")
                return 5
            return cmd_plugin(solo_verifica=len(argv) == 2)
        if modo_plugin() and argv and argv[0] in ("stato", "controlla", "applica", "firmato"):
            # Col plugin non c'è git: niente si installa da solo, /aggiorna passa da `plugin`. Stato e controlla
            # dicono soltanto se c'è un rilascio nuovo (#4860).
            if argv == ["stato"]:
                return stato_plugin(r)
            if argv in (["controlla"], ["controlla", "--subito"]):
                return controlla_plugin(r, forza=len(argv) == 2)
            return cmd_plugin(solo_verifica=True) if argv == ["firmato"] else 0
        if argv == ["stato"]:
            return cmd_stato(r)
        if argv in (["controlla"], ["controlla", "--subito"]):
            return cmd_controlla(r, forza=len(argv) == 2)
        if argv == ["applica"]:
            return cmd_applica(r)
        if argv == ["applica", "--avvio"]:
            return cmd_applica(r, ammesse=1)
        if argv == ["firmato"]:
            return cmd_firmato(r)
        if argv in (["manuali"], ["automatici"]):
            scrivi(file_scelta(r), {"modo": argv[0]})
            print("Aggiornamenti a mano: la barra in basso e l'avvio ti dicono quando ce n'è uno, e lo scarichi con "
                  "/aggiorna." if argv[0] == "manuali" else
                  "Aggiornamenti automatici: i rilasci firmati si installano da soli alla chiusura della sessione.")
            return 0
    except Exception as errore:  # noqa: BLE001 - un hook non si ferma mai per un aggiornamento
        print(f"Errore: {errore}", file=sys.stderr)
        return 1
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
