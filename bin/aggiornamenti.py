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
  riapri       esce con 0 e lo dice se un rilascio aspetta una chiusura vera di Claude Code (/fine --rotazione)
  plugin       col plugin: aggiorna il catalogo, verifica che il tag indicato sia firmato e porti lo sha
               del catalogo, poi claude plugin update e il controllo della copia installata col suo
               MANIFEST firmato; con --verifica si ferma prima di installare (strati F3). Una copia
               diversa dal MANIFEST sulla versione già installata la reinstalla (DA RIMETTERE, #5480)

Non si installa niente da solo se: la firma manca o non è di Arturo; la storia pubblicata è stata
riscritta; hai modifiche non salvate in ~/.claude; un'altra sessione di Claude Code è aperta (lo
installa la chiusura dopo, anche con altre sessioni aperte, dal 4/11/2026, oppure l'apertura dopo di Claude
Code se è l'unica sessione, dal 3/11/2026, mai un /clear, dal 4/11/2026); l'aggiornamento va in conflitto su
settings.json o su un CLAUDE.md (negli altri file vince il rilascio, e la tua versione resta in personale/conflitti,
dal 3/11/2026). In tutti questi
casi l'avviso resta, col motivo, e /aggiorna fa il resto con te. Dal 14/11/2026 (S2) un settings.json non salvato,
se è l'unico file e non ha un segreto nelle righe nuove, si salva con un commit suo e non ferma niente; il controllo lo fa
il bin/aggiornamenti.py del rilascio firmato in arrivo (avvia_dal_tag); un rilascio pronto da più di 24 ore senza una
chiusura vera fa dire ad avvio e barra di chiudere e riaprire Claude Code. Una firma che manca o non torna non
si scavalca neanche con /aggiorna: è il segno di un repository manomesso, e l'avviso dice di non
aggiornare e di segnalarlo a chi mantiene Arturo (17/10/2026, #3504). Una firma che questo computer
non sa verificare (git prima della 2.34, OpenSSH prima della 8.2) blocca allo stesso modo, ma senza
allarme: "firma non verificabile", uscita 4 di firmato. ARTURO_AGGIORNAMENTI=manuali
ha lo stesso effetto di "manuali". Solo libreria standard, Python 3.8 o successivo.

Col plugin (strati F3, 5/11/2026) il codice sta nella cache di Claude Code e non c'è git: stato e
controlla dicono se c'è un rilascio nuovo, e l'aggiornamento passa da `plugin`, che /aggiorna lancia.
Dal 10/11/2026 anche `applica`, alla chiusura della sessione, passa da lì: stesse verifiche, stesso
lucchetto, nessun rinvio (Claude Code tiene la copia di prima per le sessioni rimaste aperte), e l'avvio
dopo ne dice l'esito. Con "manuali" resta solo l'avviso. Se la copia installata non supera il controllo e quella
di prima non torna, il plugin si disattiva (claude plugin disable), e l'uscita dice come riattivarlo
(11/11/2026). Claude
Code installa lo sha scritto nel catalogo anche se nessun tag firmato lo indica (prova del 5/11/2026):
per questo il tag si verifica qui, prima, con la chiave dell'ancora nell'Orsa (hooks/fiducia.py). Se il plugin
arriva da un'altra strada (claude plugin update, il pannello /plugin), stato e il "GIÀ AGGIORNATO" di plugin
uniscono a settings.json le impostazioni nuove, da una copia che torna col suo MANIFEST firmato (#5101).
"""
from __future__ import annotations

import contextlib
import io
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
OCCUPATO = 6          # uscita interna di cmd_applica: un'altra applicazione tiene il lucchetto
ATTESA_MAX = 90       # secondi: quanto applica aspetta che Claude Code si chiuda davvero
SENZA_CONTROLLO = 7 * 86400  # col plugin: dopo 7 giorni senza un controllo riuscito l'avvio lo dice
FIRME = "firme/rilasci.allowed_signers"
# Il messaggio di una firma che manca o non torna, uguale ovunque compare (avvio, barra, /aggiorna).
COMPROMISSIONE = "possibile compromissione: non aggiornare, segnala a chi mantiene Arturo"
RIATTIVA = "claude plugin enable arturo@arturo"
BARRA_FERMA = Path("arturo") / "barra-ferma"  # sotto la cartella della config: lo legge il comando statusLine
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


def scrivi_stato(r: Path, stato: dict, chiusura: bool = False) -> None:
    """Lo stato in session-env/aggiornamento.json, con due date che sopravvivono alle riscritture (14/11/2026, S2):
    `pronto_da`, da quando questa versione aspetta di installarsi, e `chiusura_vera`, l'ultima chiusura vera che l'ha vista
    pronta. Le usa fermo_da_un_giorno. Valgono solo finché la stessa versione resta pronta."""
    nuovo = dict(stato)
    nuovo.pop("pronto_da", None)
    nuovo.pop("chiusura_vera", None)
    if nuovo.get("stato") == "pronto" and nuovo.get("versione"):
        vecchio = leggi(file_stato(r))
        stessa = vecchio.get("stato") == "pronto" and vecchio.get("versione") == nuovo["versione"]
        nuovo["pronto_da"] = float(vecchio.get("pronto_da") or time.time()) if stessa else time.time()
        if chiusura:
            nuovo["chiusura_vera"] = time.time()
        elif stessa and vecchio.get("chiusura_vera"):
            nuovo["chiusura_vera"] = vecchio["chiusura_vera"]
    scrivi(file_stato(r), nuovo)


GIORNO = 86400


def fermo_da_un_giorno(stato: dict, adesso: float = None) -> bool:
    """Vero se la versione è pronta da più di 24 ore e nessuna chiusura vera l'ha vista nelle ultime 24 (S2): chi lavora
    solo con /clear e la rotazione non chiude mai Claude Code, e il rilascio aspettava per sempre. La barra in basso
    (hooks/statusline.js, fermoDaUnGiorno) fa lo stesso conto."""
    if stato.get("stato") != "pronto" or not stato.get("pronto_da"):
        return False
    adesso = time.time() if adesso is None else adesso
    ultima = max(float(stato.get("pronto_da") or 0), float(stato.get("chiusura_vera") or 0))
    return adesso - ultima > GIORNO


RIAPRI = "chiudi e riapri Claude Code: /clear non basta"


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
    # Il caso più frequente col clone (14/11/2026, S2): Claude Code riscrive settings.json da solo (un permesso
    # "sempre", /config), e quel file bastava a fermare ogni rilascio. Se è l'unico, la chiusura lo salva con un commit
    # suo (salva_settings) e l'aggiornamento lo unisce come JSON con unisci-settings.py. Con un segreto dentro resta
    # fermo: un commit automatico non lo deve mai salvare.
    if file == ["settings.json"] and not segreto_in_settings(r):
        return dict(stato, stato="pronto", motivo="", salva_settings=True)
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


def segreto_in_settings(r: Path) -> bool:
    """Vero se le righe nuove di settings.json hanno la forma di un segreto, con i pattern di
    hooks/commit-secret-gate.py (HIGH_CONF). Senza la guardia, o se non si legge, vale vero: nel dubbio niente commit."""
    diff = git(r, "diff", "--no-color", "-U0", "--", "settings.json")
    if diff.returncode != 0:
        return True
    righe = "\n".join(x[1:] for x in diff.stdout.splitlines() if x.startswith("+") and not x.startswith("+++"))
    try:
        testo = (r / "hooks" / "commit-secret-gate.py").read_text(encoding="utf-8")
        blocco = re.search(r"^HIGH_CONF = \[\n(.*?)^\]", testo, re.M | re.S)
        schemi = re.findall(r'^\s*\(r"((?:[^"\\]|\\.)*)",', blocco.group(1), re.M) if blocco else []
    except OSError:
        return True
    if not schemi:
        return True
    try:
        return any(re.search(s, righe) for s in schemi)
    except re.error:
        return True


def salva_settings(r: Path) -> str:
    """Salva settings.json con un commit suo, prima dell'aggiornamento (S2). L'identità di git della persona se c'è,
    altrimenti quella di Arturo; gli hook di commit della persona girano. Restituisce il motivo se non riesce."""
    identita = []
    if not git(r, "config", "user.email").stdout.strip():
        identita = ["-c", "user.name=Arturo", "-c", "user.email=arturo@localhost"]
    p = git(r, *identita, "commit", "-q", "-m", "settings.json salvato da Arturo prima dell'aggiornamento",
            "--", "settings.json", timeout=60)
    if p.returncode != 0:
        return (p.stderr or p.stdout).strip().splitlines()[-1][:160] if (p.stderr or p.stdout).strip() \
            else "commit non riuscito"
    return ""


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
        scrivi_stato(r, stato)
        stato = dict(stato, **{k: v for k, v in leggi(file_stato(r)).items() if k in ("pronto_da", "chiusura_vera")})
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
    elif fermo_da_un_giorno(stato) and fallito != stato["versione"]:
        righe.append(f"ARTURO: la versione {stato['versione']} aspetta da più di 24 ore una chiusura vera di Claude Code: "
                     f"{RIAPRI}, né la rotazione. Dillo alla persona in una frase.")
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
        scrivi_stato(r, calcola(r))
    except OSError:
        pass
    return 0


def cmd_applica(r: Path, ammesse: int = 0, fare=None, occupato: int = 0) -> int:
    """Un'applicazione alla volta, col lucchetto session-env/aggiornamento.lock. `fare` è la procedura (di serie
    _applica, quella del clone); `occupato` è l'uscita se un'altra applicazione è in corso. Col plugin lo stesso
    lucchetto vale per la chiusura e per /aggiorna: mai due `claude plugin update` insieme (10/11/2026).
    Lanciato da avvia_dal_tag il lucchetto è già del processo che l'ha lanciato, e aspetta che finisca."""
    if os.environ.get("ARTURO_DA_TAG"):
        return fare(r) if fare else _applica(r, ammesse)
    blocco = r / "session-env" / "aggiornamento.lock"
    try:
        blocco.parent.mkdir(parents=True, exist_ok=True)
        blocco.mkdir()
    except FileExistsError:
        try:
            if not _lucchetto_orfano(blocco) and time.time() - blocco.stat().st_mtime < 900:
                return occupato  # un'altra applicazione è in corso
            shutil.rmtree(str(blocco), ignore_errors=True)
            blocco.mkdir()
        except OSError:
            return 1
    except OSError:
        return 1
    senza_pid = False
    try:
        (blocco / "pid").write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        senza_pid = True
    # Due processi possono aver visto lo stesso lucchetto orfano: resta quello che rilegge il proprio pid.
    if not senza_pid and _pid_lucchetto(blocco) != os.getpid():
        return occupato
    try:
        return fare(r) if fare else _applica(r, ammesse)
    finally:
        # Solo il lucchetto proprio: dopo 900 secondi un altro processo può averlo preso (review del 10/11/2026).
        if _pid_lucchetto(blocco) == os.getpid() or (senza_pid and not (blocco / "pid").exists()):
            shutil.rmtree(str(blocco), ignore_errors=True)


def _pid_lucchetto(blocco: Path) -> int:
    try:
        return int((blocco / "pid").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def _lucchetto_orfano(blocco: Path) -> bool:
    """Vero se il processo che ha preso il lucchetto non c'è più (computer spento a metà installazione): senza,
    per 15 minuti la chiusura taceva e /aggiorna diceva "si sta già aggiornando" (review del 10/11/2026).
    Su Windows os.kill(pid, 0) chiude il processo: lì resta solo la scadenza."""
    pid = _pid_lucchetto(blocco)
    if not pid or os.name == "nt":
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except (OSError, OverflowError, ValueError):  # un file pid rotto: resta la scadenza
        return False
    return False


def _rinnova_lucchetto() -> None:
    """Prima del passo lungo (claude plugin update): la scadenza del lucchetto riparte da qui."""
    try:
        os.utime(str(radice() / "session-env" / "aggiornamento.lock"), None)
    except OSError:
        pass


def avvia_dal_tag(r: Path, ammesse: int):
    """Il controllo lo fa il codice del rilascio in arrivo, non quello installato (14/11/2026, S2). Prima decideva
    calcola() della copia installata, e un suo difetto fermava anche il rilascio che lo correggeva. Qui resta solo la
    verifica della firma, con la chiave già installata: se il tag è firmato e porta un bin/aggiornamenti.py diverso,
    quello gira al posto di questo, con lo stesso lucchetto e la stessa chiave. Restituisce la sua uscita, oppure None
    se decide questo codice (nessun rilascio nuovo, firma che non torna, stesso file, lancio non riuscito)."""
    src = sorgente(r)
    tag = ultimo_tag(r, src)
    commit = git(r, "rev-list", "-n", "1", tag).stdout.strip() if tag else ""
    if not commit or git(r, "merge-base", "--is-ancestor", commit, "HEAD").returncode == 0:
        return None
    motivo, _ = verifica_firma(r, tag)
    # Il tag si rilegge dopo la verifica: il file si prende dal commit verificato, mai da un ref spostato intanto.
    if motivo or git(r, "rev-list", "-n", "1", tag).stdout.strip() != commit:
        return None
    nuovo = git(r, "show", f"{commit}:bin/aggiornamenti.py")
    try:
        mio = Path(os.path.realpath(__file__)).read_text(encoding="utf-8")
    except OSError:
        mio = ""
    if nuovo.returncode != 0 or not nuovo.stdout.strip() or nuovo.stdout == mio:
        return None
    lavoro = Path(tempfile.mkdtemp(prefix="arturo-dal-tag."))
    try:
        script = lavoro / "aggiornamenti.py"
        with open(str(script), "w", encoding="utf-8", newline="\n") as uscita:
            uscita.write(nuovo.stdout)
        p = subprocess.run([sys.executable, str(script), "applica", *(["--avvio"] if ammesse else [])],
                           stdin=subprocess.DEVNULL, cwd=str(r), timeout=1500,
                           env=dict(os.environ, ARTURO_DA_TAG=tag, ARTURO_RADICE=str(r)))
        return p.returncode
    except subprocess.TimeoutExpired:
        return 1  # il rilascio ha provato e non ha finito: questo codice non riparte sopra il suo lavoro
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        shutil.rmtree(str(lavoro), ignore_errors=True)


def _applica(r: Path, ammesse: int = 0) -> int:
    """ammesse: le sessioni che possono restare aperte. 0 alla chiusura; 1 all'avvio (`applica --avvio`),
    dove la sessione che parte è una."""
    if manuali(r) or not git(r, "remote").stdout.strip():
        return 0
    dal_tag = bool(os.environ.get("ARTURO_DA_TAG"))
    # Prima si guarda se c'è qualcosa da installare: aspettare le sessioni senza motivo terrebbe
    # vivo un processo (e il suo log) per niente. Il processo lanciato da avvia_dal_tag ha già scaricato.
    if not dal_tag:
        scarica(r, sorgente(r))
        rc = avvia_dal_tag(r, ammesse)
        if rc is not None:
            return rc
    stato = calcola(r)
    # Solo la chiusura vera conta per fermo_da_un_giorno: `applica --avvio` è un'apertura.
    scrivi_stato(r, stato, chiusura=ammesse == 0)
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
    if stato.get("salva_settings"):
        motivo = salva_settings(r)
        if motivo:
            _segnala_ostacolo(r, dict(stato, modifiche=["settings.json"]))
            return _esito(r, stato["versione"], "APPLICAZIONE NON PARTITA",
                          f"settings.json ha modifiche non salvate e il commit non è riuscito ({motivo})")
    tag, src = stato["versione"], stato["sorgente"]
    lavoro = Path(tempfile.mkdtemp(prefix="arturo-aggiorna."))
    try:
        procedura = lavoro / "aggiorna-applica.sh"
        testo = git(r, "show", f"{tag}:bin/aggiorna-applica.sh")
        if testo.returncode != 0 or not testo.stdout.strip():
            _segnala_ostacolo(r, stato, "non-partito")
            return _esito(r, tag, "APPLICAZIONE NON PARTITA", "il rilascio non ha la procedura di applicazione")
        with open(str(procedura), "w", encoding="utf-8", newline="\n") as uscita:  # write_text(newline=) vuole Python 3.10
            uscita.write(testo.stdout)
        bash = os.environ.get("ARTURO_BASH") or shutil.which("bash") or "bash"
        modo = "merge" if src == "upstream" else "rebase"
        p = subprocess.run([bash, str(procedura), str(r), modo, tag], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600, cwd=str(r),
                           env=dict(os.environ, ARTURO_AGGIORNA_AUTOMATICO="1"))
    except (OSError, subprocess.SubprocessError) as errore:
        _segnala_ostacolo(r, stato, "non-partito")
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
        scrivi_stato(r, calcola(r))
        return 0
    parola = "APPLICATO" if esito.startswith("APPLICATO") else (esito.split(":")[0] or "FALLITO")
    # Le righe aggiunte a un hook di sessione che separa ha spostato, commentate, in personale/: non girano più, e
    # l'avvio lo dice una volta (finding 22 del 7/11/2026). /aggiorna le rilegge con la persona; qui nessuno le vedeva.
    commentate = [re.sub(r"^\s*SEPARATO:\s*", "", x).split(" -> ")[0].strip() for x in righe
                  if "SEPARATO:" in x and "righe commentate" in x]
    _esito(r, tag, parola, esito[:240], commentate=commentate[:10])
    if parola == "APPLICAZIONE NON PARTITA":
        attesa = "copia di prova con un conflitto aspetta" in esito
        _segnala_ostacolo(r, stato, "bloccato-attesa" if attesa else "non-partito")
    scrivi_stato(r, calcola(r))
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


def programma_claude() -> str:
    """La CLI di Claude Code. Il processo staccato della chiusura può avere un PATH senza `claude` (app desktop,
    shell senza ~/.local/bin): si provano i due posti dove Claude Code si installa."""
    # ARTURO_CLAUDE vale solo se indica un programma che c'è: in Git Bash `command -v claude` dà un percorso
    # POSIX che Python su Windows non sa lanciare, e batteva il ripiego (review del 10/11/2026).
    dato = os.environ.get("ARTURO_CLAUDE") or ""
    scelto = (shutil.which(dato) if dato else None) or shutil.which("claude")
    if scelto:
        return scelto
    for cartella in (Path.home() / ".local" / "bin", Path.home() / ".claude" / "local"):
        for nome in (("claude.exe", "claude.cmd") if os.name == "nt" else ("claude",)):
            if (cartella / nome).is_file():
                return str(cartella / nome)
    return "claude"


def _claude(*argomenti, timeout: int = 300) -> subprocess.CompletedProcess:
    comando = [programma_claude(), "plugin", *argomenti]
    # `claude plugin update` chiude con gli hook di Arturo, e session-end.sh lancia un altro `applica` staccato:
    # lo ferma il lucchetto di cmd_applica (PC09). Niente ARTURO_AGGIORNAMENTI=manuali qui: un processo di
    # servizio di Claude Code nato da questo comando la erediterebbe, e spegnerebbe gli aggiornamenti delle
    # sessioni dopo senza dirlo (review dell'11/11/2026).
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


def _barra_ferma(orsa: Path, versione: str = "", togli: bool = False) -> None:
    """Il testo che la barra in basso mostra quando il plugin è spento e la cartella della copia di prima non c'è
    più: lì nessun codice di Arturo può girare, e il comando statusLine dei settings legge questo file (prova con
    la CLI vera dell'11/11/2026, #5319). `togli` lo cancella quando la persona ha riattivato il plugin."""
    f = orsa / BARRA_FERMA
    try:
        if togli:
            if f.exists():
                f.unlink()
            return
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"\x1b[31m! Arturo disattivato: la copia {versione} non è verificata. Segnala a chi mantiene "
                     f"Arturo. Dopo la sua risposta: {RIATTIVA}\x1b[0m\n", encoding="utf-8")
    except OSError:
        pass


def _indietro(orsa: Path, prima: dict, compromesso: bool, tag: str = "", motivo: str = "") -> str:
    """Dopo un controllo fallito su una copia già installata: rimette la voce di prima ("rimessa"). Se non torna e
    la copia non è verificata, disattiva il plugin ("disattivata"): una copia non verificata non deve partire
    all'apertura dopo (11/11/2026). "scaricata" se neanche questo riesce. Se la copia non verificata resta
    installata lo stato lo dice qui, anche quando chiama /aggiorna: col plugin spento parla solo la barra."""
    esito = _ripristina(orsa, prima)
    if esito == "rimessa" or not compromesso:
        return esito
    if _claude("disable", NOME_PLUGIN, timeout=120).returncode == 0:
        esito = "disattivata"
    stato = {"stato": "bloccato", "plugin": True, "chiusura": True, "compromesso": True, "motivo": motivo[:200],
             "versione": ".".join(str(x) for x in numero(tag)), "sha_prima": str(prima.get("gitCommitSha") or ""),
             "controllato": time.time()}
    if esito == "disattivata":
        stato["disattivato"] = True
        _barra_ferma(orsa, stato["versione"])
    try:
        scrivi_stato(radice(), stato)
    except OSError:
        pass
    return esito


def plugin_acceso(orsa: Path) -> bool:
    """Falso solo se settings.json dice che il plugin è disattivato (`claude plugin disable`)."""
    for nome in ("settings.json", "settings.local.json"):
        if (leggi(orsa / nome).get("enabledPlugins") or {}).get(NOME_PLUGIN) is False:
            return False
    return True


def installata_pulita(orsa: Path) -> bool:
    """Vero se la copia installata è lo sha del catalogo e torna col suo MANIFEST firmato."""
    fiducia, _ = _moduli()
    voce, sorgente = installato(orsa), voce_catalogo(orsa).get("source")
    percorso = str(voce.get("installPath") or "")
    if not percorso or not isinstance(sorgente, dict) or voce.get("gitCommitSha") != sorgente.get("sha"):
        return False
    try:
        controllo = fiducia.controlla(Path(percorso), orsa)
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return controllo["firma"] == "ok" and not controllo["cambiati"] and not controllo["mancano"]


def _blocca(motivo: str, compromesso: bool, scaricata: str = "") -> int:
    if compromesso and scaricata == "rimessa":
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). Ho rimesso la versione di "
              "prima: si segnala con /segnala, o in privato come dice SECURITY.md.", file=sys.stderr)
        return 3
    if compromesso and scaricata == "disattivata":
        print(f"POSSIBILE COMPROMISSIONE: {COMPROMISSIONE.split(': ', 1)[1]} ({motivo}). La copia nuova è già "
              "scaricata e non sono riuscito a rimettere quella di prima: ho disattivato Arturo, così quella copia "
              "non parte. Si segnala in privato come dice SECURITY.md. Per riattivarlo dopo la risposta di chi "
              f"mantiene Arturo: {RIATTIVA}", file=sys.stderr)
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


def verifica_catalogo(orsa: Path, anche_installato: bool = False) -> tuple:
    """(rc, tag, sha): rc 0 se il catalogo indica un tag firmato dalla chiave dell'ancora e il tag porta
    proprio lo sha del catalogo; rc 2 se quello sha è già installato, salvo con `anche_installato` (la copia da
    rimettere di _rimetti). Gli errori li stampa."""
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
    # Il campo version del catalogo non è firmato: se non dice la versione del tag, avvio e barra ripetono per
    # sempre una versione che non arriva (review del 10/11/2026).
    if voce.get("version") and numero(str(voce["version"])) != numero(tag):
        return _blocca(f"il catalogo chiama {voce['version']} il rilascio {tag}", True), tag, sha
    prima = installato(orsa)
    if prima.get("gitCommitSha") == sha and not anche_installato:
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
    orsa = radici.radice_orsa()
    catalogo = _claude("marketplace", "update", "arturo", timeout=120)
    # Lo scarico può durare due minuti: lo stato si rilegge qui, o l'allarme scritto intanto dalla chiusura di
    # un'altra sessione finiva sovrascritto (review del 10/11/2026).
    vecchio = leggi(file_stato(r))
    estranea = voce_estranea(voce_catalogo(orsa))
    nuova = versione_nuova_plugin(orsa)
    # La copia non verificata è rimasta installata (quella di prima non è tornata): il catalogo non è più nuovo
    # dell'installato, e senza questo l'allarme spariva al controllo dell'ora dopo (review del 10/11/2026).
    # L'allarme cade da solo quando la copia installata è lo sha del catalogo e torna col suo MANIFEST firmato:
    # una versione buona arrivata da un'altra strada non resta "compromessa" per sempre.
    sospetta = bool(vecchio.get("chiusura") and vecchio.get("compromesso") and vecchio.get("sha_prima")
                    and installato(orsa).get("gitCommitSha") != vecchio["sha_prima"]
                    and not installata_pulita(orsa))
    if estranea:
        stato = {"stato": "bloccato", "compromesso": True, "motivo": estranea, "versione": nuova, "plugin": True}
    elif sospetta or (nuova and vecchio.get("chiusura") and vecchio.get("versione") == nuova):
        # Una firma che non torna o non si verifica, vista dalla chiusura: il controllo dell'ora dopo non la
        # riscrive "pronto". La toglie un'installazione riuscita (segna_aggiornato).
        stato = {k: v for k, v in vecchio.items() if k != "controllato"}
        if stato.get("disattivato") and plugin_acceso(orsa):
            del stato["disattivato"]  # la persona l'ha riattivato: la barra non dice più "disattivato"
            _barra_ferma(orsa, togli=True)
    elif nuova:
        stato = {"stato": "manuale" if manuali(r) else "pronto", "versione": nuova, "plugin": True}
    else:
        stato = {"stato": "aggiornato", "plugin": True}
    # L'ultimo controllo riuscito: da offline `marketplace update` fallisce, e senza questo lo stato restava
    # "aggiornato" per sempre. Il primo fallimento fa partire il conto dall'ultimo controllo che si conosce.
    if catalogo.returncode == 0:
        stato["riuscito"] = time.time()
    else:
        stato["riuscito"] = float(vecchio.get("riuscito") or vecchio.get("controllato") or time.time())
    try:
        scrivi_stato(r, dict(stato, controllato=time.time()))
    except OSError:
        pass
    return 0


def segna_aggiornato(r: Path) -> None:
    """Dopo /aggiorna la barra non deve dire ancora "serve /aggiorna" fino al controllo dopo."""
    try:
        # Chi arriva qui ha appena scaricato e verificato il tag del catalogo: il controllo è riuscito.
        scrivi_stato(r, {"stato": "aggiornato", "plugin": True, "controllato": time.time(),
                               "riuscito": time.time()})
    except OSError:
        pass


def segna_sessione(r: Path, in_uso: str) -> None:
    """Scrive con quale versione gira questa sessione (session-env/versione-sessione/<id>): la barra in basso la
    confronta con quella installata e dice "riapri Claude Code" alla sessione rimasta aperta. L'id arriva
    dall'avvio (ARTURO_SESSIONE). I segni più vecchi di 30 giorni si tolgono qui."""
    sessione = os.environ.get("ARTURO_SESSIONE") or ""
    if not in_uso or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", sessione):
        return
    cartella = r / "session-env" / "versione-sessione"
    try:
        cartella.mkdir(parents=True, exist_ok=True)
        (cartella / sessione).write_text(in_uso, encoding="utf-8")
        for f in cartella.iterdir():
            if time.time() - f.stat().st_mtime > 30 * 86400:
                f.unlink()
    except OSError:
        pass


def stato_plugin(r: Path) -> int:
    """La riga dell'avvio col plugin: solo se l'ultimo controllo ha visto un rilascio più nuovo, ancora non installato.

    Il controllo lo lancia anche l'avvio, staccato: chi ha una barra sua non lancia mai quello della barra di Arturo."""
    _, radici = _moduli()
    stato = leggi(file_stato(r))
    if time.time() - float(stato.get("controllato") or 0) >= ORA:
        avvia_staccato(r, "controlla")
    in_uso = str(leggi(radici.radice_arturo() / ".claude-plugin" / "plugin.json").get("version") or "")
    segna_sessione(r, in_uso)
    fallito = esito_plugin(r, in_uso, stato)
    riuscito = float(stato.get("riuscito") or 0)
    if stato.get("plugin") and riuscito and time.time() - riuscito > SENZA_CONTROLLO:
        print("ARTURO: da più di 7 giorni non riesco a controllare gli aggiornamenti di Arturo (rete, proxy o "
              "credenziali). /aggiorna mostra l'errore. Dillo alla persona in una frase.")
    if stato.get("plugin") and stato.get("compromesso"):
        print(f"ARTURO: {COMPROMISSIONE}. {stato.get('motivo', '')}. Non riaprire Claude Code prima di aver segnalato: "
              "dillo alla persona con queste parole, e proponi /segnala o la segnalazione privata di SECURITY.md.")
        return 0
    riga = "" if stato.get("compromesso") else impostazioni_indietro(radici.radice_arturo(), radici.radice_orsa())
    if riga:
        print(f"ARTURO: {riga} Dillo alla persona in una frase.")
    nuova = versione_nuova_plugin(radici.radice_orsa()) if stato.get("plugin") and stato.get("versione") else ""
    if stato.get("plugin") and stato.get("stato") == "manuale" and stato.get("versione") \
            and nuova == stato["versione"]:
        print(f"ARTURO: c'è la versione {stato['versione']} di Arturo. /aggiorna la installa dopo averne verificato la "
              "firma, poi riapri Claude Code. Dillo alla persona in una frase.")
    elif nuova and nuova == stato["versione"] and stato.get("non_verificabile"):
        print(f"ARTURO: c'è la versione {nuova} di Arturo, ma {stato.get('motivo') or NON_VERIFICABILE}. Non si "
              "installa, né da sola né con /aggiorna, finché git e OpenSSH non sono aggiornati. Dillo alla persona in "
              "una frase: non è un problema di sicurezza.")
    elif nuova and nuova == stato["versione"] and stato.get("stato") == "pronto" and fallito != nuova \
            and not manuali(r):
        if fermo_da_un_giorno(stato):
            print(f"ARTURO: la versione {nuova} di Arturo aspetta da più di 24 ore una chiusura vera di Claude Code: "
                  f"{RIAPRI}, né la rotazione. Subito: /aggiorna. Dillo alla persona in una frase.")
        else:
            print(f"ARTURO: c'è la versione {nuova} di Arturo: si installa da sola alla chiusura della sessione, dopo "
                  "la verifica della firma. Subito: /aggiorna.")
    return 0


def esito_plugin(r: Path, in_uso: str, stato: dict = None) -> str:
    """L'esito dell'ultima chiusura col plugin, detto una volta all'avvio dopo. `in_uso` è la versione della copia
    che gira. Restituisce la versione di un'installazione non partita: per quella l'avvio non dice anche "si
    installa da sola" (come nel clone, n. 49). Firma che non torna o non verificabile: parla lo stato; se lo
    stato non porta più la compromissione, la dice l'esito."""
    esito = leggi(file_esito(r))
    if not esito or esito.get("mostrato"):
        return ""
    parola, versione = esito.get("esito"), str(esito.get("versione") or "")
    fallito = ""
    if parola == "APPLICATO" and numero(in_uso) < numero(versione):
        # Una sessione rimasta aperta sulla copia di prima (dopo un /clear): l'esito resta da dire a quella nuova.
        print(f"ARTURO: la versione {versione} di Arturo è installata: parte alla prossima apertura di Claude Code.")
        return ""
    if parola == "APPLICATO":
        print(f"ARTURO: aggiornato a {versione} alla chiusura della sessione, firma verificata. /novita racconta "
              "cosa cambia.")
        if esito.get("impostazioni"):
            print(f"ARTURO: {esito['impostazioni']} Dillo alla persona in una frase.")
    elif parola == "POSSIBILE COMPROMISSIONE" and not (stato or {}).get("compromesso") \
            and numero(in_uso) < numero(versione):
        print(f"ARTURO: {COMPROMISSIONE}. L'aggiornamento automatico a {versione} si è fermato "
              f"({esito.get('riga') or 'firma che non torna'}). Dillo alla persona con queste parole, e proponi la "
              "segnalazione privata di SECURITY.md.")
    elif parola not in ("POSSIBILE COMPROMISSIONE", "FIRMA NON VERIFICABILE") and numero(versione) \
            and numero(in_uso) >= numero(versione):
        pass  # arrivata intanto con /aggiorna: dire "non è partito" sarebbe falso (review del 10/11/2026)
    elif parola not in ("POSSIBILE COMPROMISSIONE", "FIRMA NON VERIFICABILE"):
        fallito = versione
        print(f"ARTURO: l'aggiornamento automatico a {versione} non è partito "
              f"({esito.get('riga') or 'motivo sconosciuto'}). Ci riprova alla prossima chiusura, o subito con /aggiorna.")
    try:
        scrivi(file_esito(r), dict(esito, mostrato=True))
    except OSError:
        pass
    return fallito


def cmd_plugin(solo_verifica: bool = False) -> int:
    """/aggiorna col plugin. Uscite: 0 applicato, rimesso o già aggiornato, 1 niente da applicare o errore, 3 possibile
    compromissione, 4 firma non verificabile su questo computer. Con lo sha del catalogo già installato ma la copia
    diversa dal suo MANIFEST firmato, la reinstalla (_rimetti, #5480)."""
    _, radici = _moduli()
    orsa = radici.radice_orsa()
    catalogo = _claude("marketplace", "update", "arturo", timeout=180)
    if catalogo.returncode != 0:
        print(f"CATALOGO NON AGGIORNATO: {(catalogo.stderr or catalogo.stdout).strip()[:200]}. Verifico quello che ho.",
              file=sys.stderr)
    rc, tag, sha = verifica_catalogo(orsa)
    if rc == 2:
        vecchio = leggi(file_stato(radice()))
        if vecchio.get("chiusura") and vecchio.get("compromesso") and not installata_pulita(orsa):
            # Lo sha è quello del catalogo, ma la copia non ha superato il controllo dopo l'installazione: dire
            # "già aggiornato" cancellerebbe l'allarme con la copia ancora lì (review dell'11/11/2026).
            return _blocca(str(vecchio.get("motivo") or "la copia installata non è verificata"), True)
        cambiata = da_rimettere(orsa)
        if cambiata:
            return _rimetti(orsa, cambiata, solo_verifica)
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
    _rinnova_lucchetto()
    aggiorna = _claude("update", NOME_PLUGIN)
    if aggiorna.returncode != 0:
        print(f"APPLICAZIONE NON PARTITA: claude plugin update non è riuscito "
              f"({(aggiorna.stderr or aggiorna.stdout).strip()[:200]}). Non ho toccato niente.")
        return 1
    return _controlla_installata(orsa, prima, tag, sha)


def _controlla_installata(orsa: Path, prima: dict, tag: str, sha: str, rimessa: bool = False) -> int:
    """Dopo `claude plugin update`, o dopo la reinstallazione di _rimetti: la copia installata è lo sha verificato e
    torna col suo MANIFEST firmato, se no si torna alla voce di `prima` (vuota per _rimetti: si disattiva)."""
    fiducia, _ = _moduli()
    dopo = installato(orsa)
    copia = Path(str(dopo.get("installPath") or ""))
    if dopo.get("gitCommitSha") != sha:
        return _blocca(f"Claude Code ha installato {str(dopo.get('gitCommitSha'))[:12]}, non lo sha verificato "
                       f"{sha[:12]}", True, scaricata=_indietro(orsa, prima, True, tag, "sha non verificato"))
    controllo = fiducia.controlla(copia, orsa)
    if controllo["firma"] != "ok":
        compromesso = controllo["firma"] != "non-verificabile"
        return _blocca(controllo["motivo"], compromesso,
                       scaricata=_indietro(orsa, prima, compromesso, tag, controllo["motivo"]))
    diversi = controllo["cambiati"] + controllo["mancano"]
    if diversi:
        motivo = f"la copia installata non è come il MANIFEST firmato ({', '.join(diversi[:3])})"
        return _blocca(motivo, True, scaricata=_indietro(orsa, prima, True, tag, motivo))
    # Una chiave nuova entra nell'ancora solo da una copia verificata con la chiave di prima.
    fiducia.fissa_ancora(copia, orsa)
    segna_aggiornato(radice())
    impostazioni = applica_impostazioni(copia)
    if rimessa:
        print(f"RIMESSO: {tag}. La copia del plugin è di nuovo come il rilascio firmato. Riavvia Claude Code per usarla.")
    else:
        print(f"APPLICATO: {tag}. Riavvia Claude Code per usarlo.")
    if impostazioni:
        print(impostazioni)
    return 0


# Le cartelle dove un file in più cambia quello che Arturo fa: le stesse della riga DERIVA (hooks/deriva.py).
CARTELLE_ATTIVE = ("hooks/", "bin/", "skills/", "agents/", "shared/")


def da_rimettere(orsa: Path) -> str:
    """Il motivo per reinstallare la copia del plugin, se è lo sha del catalogo ma i suoi file non sono come nel
    MANIFEST firmato; altrimenti "". `claude plugin update` e `install` su una versione già installata non
    rimettono niente (prova con la CLI vera del 13/11/2026, #5480). Con la firma non verificabile su questo
    computer la copia reinstallata non si potrebbe controllare: "" anche lì."""
    fiducia, _ = _moduli()
    percorso = str(installato(orsa).get("installPath") or "")
    if not percorso:
        return ""
    try:
        controllo = fiducia.controlla(Path(percorso), orsa)
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""
    if controllo["firma"] == "non-verificabile":
        return ""
    if controllo["firma"] != "ok":
        return str(controllo["motivo"] or "la copia installata non ha una firma valida")
    diversi = sorted(set(controllo["cambiati"]) | set(controllo["mancano"])
                     | {p for p in controllo["in_piu"] if p.startswith(CARTELLE_ATTIVE)})
    if not diversi:
        return ""
    return (f"{len(diversi)} file della copia installata non sono come nel rilascio firmato "
            f"({', '.join(diversi[:3])}{'…' if len(diversi) > 3 else ''})")


def _rimetti(orsa: Path, motivo: str, solo_verifica: bool) -> int:
    """Rimette la copia firmata del rilascio già installato (#5480): verifica il tag come per una versione nuova,
    poi `claude plugin uninstall --keep-data` e `claude plugin install`, l'unica strada che con la CLI vera
    riscrive la cartella della copia (13/11/2026). Tiene il plugin spento se la persona l'aveva spento: install
    lo riaccende."""
    rc, tag, sha = verifica_catalogo(orsa, anche_installato=True)
    if rc != 0:
        return rc
    if solo_verifica:
        print(f"DA RIMETTERE: {tag}: {motivo}. Col sì lancia aggiornamenti.py plugin: reinstalla il rilascio "
              "firmato e lo controlla.")
        return 0
    acceso = plugin_acceso(orsa)
    _rinnova_lucchetto()
    tolto = _claude("uninstall", "--keep-data", NOME_PLUGIN, timeout=120)
    if tolto.returncode != 0:
        print(f"APPLICAZIONE NON PARTITA: claude plugin uninstall non è riuscito "
              f"({(tolto.stderr or tolto.stdout).strip()[:200]}). Non ho toccato niente.")
        return 1
    messo = _claude("install", NOME_PLUGIN)
    if messo.returncode != 0:
        print(f"APPLICAZIONE NON PARTITA: ho tolto la copia cambiata, ma claude plugin install non è riuscito "
              f"({(messo.stderr or messo.stdout).strip()[:200]}). Arturo adesso non è installato: rilancia /aggiorna, "
              f"o nel terminale claude plugin install {NOME_PLUGIN}.")
        return 1
    if not acceso:
        _claude("disable", NOME_PLUGIN, timeout=120)
    return _controlla_installata(orsa, {}, tag, sha, rimessa=True)


ESITI_PLUGIN = re.compile(r"(APPLICATO|GIÀ AGGIORNATO|POSSIBILE COMPROMISSIONE|FIRMA NON VERIFICABILE|NESSUN RILASCIO|"
                          r"APPLICAZIONE NON PARTITA)")


def _applica_plugin(r: Path) -> int:
    """La chiusura della sessione col plugin (10/11/2026): la stessa strada di /aggiorna, cmd_plugin, con le sue
    verifiche (tag firmato, sha del catalogo, MANIFEST). Non rinvia mai: dopo `claude plugin update` Claude Code
    tiene la copia di prima, e le sessioni rimaste aperte continuano da lì. Aspetta solo che la sessione che si
    chiude sia uscita. L'esito lo racconta l'avvio dopo (stato_plugin)."""
    if manuali(r):
        return 0
    prima = processi_claude()
    _, radici = _moduli()
    _claude("marketplace", "update", "arturo", timeout=120)
    versione = versione_nuova_plugin(radici.radice_orsa())
    sha_prima = str(installato(radici.radice_orsa()).get("gitCommitSha") or "")
    if not versione:
        return 0
    vecchio = leggi(file_stato(r))
    if vecchio.get("stato") == "pronto" and vecchio.get("versione") == versione:
        try:
            scrivi_stato(r, vecchio, chiusura=True)  # la chiusura vera che l'ha vista pronta (fermo_da_un_giorno)
        except OSError:
            pass
    limite = time.time() + float(os.environ.get("ARTURO_ATTESA_MAX", ATTESA_MAX))
    while prima > 0 and processi_claude() >= prima and time.time() < limite:
        time.sleep(2)
    uscita = io.StringIO()
    try:
        with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(uscita):
            rc = cmd_plugin()
    except Exception as errore:  # noqa: BLE001 - l'esito va scritto comunque
        rc = 1
        uscita.write(f"\nAPPLICAZIONE NON PARTITA: {str(errore)[:200]}")
    righe = [x.strip() for x in uscita.getvalue().splitlines() if x.strip()]
    if righe:
        print("\n".join(righe))
    riga = next((x for x in righe if ESITI_PLUGIN.match(x)), "")
    if riga.startswith("GIÀ AGGIORNATO"):
        return 0
    if rc == 0 and riga.startswith("APPLICATO"):
        # Col clone l'evento lo scrive aggiorna-applica.sh; col plugin mancava (14/11/2026, #5610).
        _segnala_ostacolo(r, {"versione": versione}, "automatico")
        _esito(r, versione, "APPLICATO", riga[:240],
               impostazioni=next((x[:400] for x in righe if x.startswith("IMPOSTAZIONI NON APPLICATE")), ""))
        return 0
    if rc in (3, 4):
        # Il motivo senza la cornice: l'avvio e la barra hanno già le loro parole.
        m = re.search(r"\((.+?)\)\. " if rc == 3 else r": (.+?)\. Non applico", riga)
        stato = {"stato": "bloccato", "versione": versione, "plugin": True, "chiusura": True,
                 "motivo": m.group(1) if m else riga[:200], "controllato": time.time(), "sha_prima": sha_prima,
                 "compromesso" if rc == 3 else "non_verificabile": True}
        if rc == 3 and "ho disattivato Arturo" in riga:
            stato["disattivato"] = True
        if not sha_prima or installato(radici.radice_orsa()).get("gitCommitSha") == sha_prima:
            stato.pop("sha_prima", None)  # la copia di prima è ancora lì: vale la regola della versione
        try:
            scrivi_stato(r, stato)
        except OSError:
            pass
        _segnala_ostacolo(r, stato)
    if rc not in (3, 4):
        _segnala_ostacolo(r, {"versione": versione}, "non-partito")
    _esito(r, versione, riga.split(":")[0] if riga else "NON PARTITO", (riga or (righe[-1] if righe else ""))[:240])
    return 1


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
    # Solo la copia installata scrive nell'Orsa: una sessione rimasta aperta sulla copia di prima (dopo un /clear)
    # riportava indietro settings.json, e toglieva la regola di blocco appena arrivata (review del 10/11/2026).
    percorso = str(installato(orsa).get("installPath") or "")
    if not percorso or os.path.realpath(percorso) != os.path.realpath(str(copia)):
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
        elif stato.get("modifiche"):
            # Il caso più frequente col clone (14/11/2026, #5610): settings.json riscritto da Claude Code basta a
            # fermare ogni rilascio, e prima non lasciava traccia.
            valore = "bloccato-modifiche"
        else:
            return
    versione = stato.get("versione", "")
    f = r / "session-env" / "aggiornamento-segnalato.json"
    if leggi(f).get(versione) == valore:
        return
    try:
        scrivi(f, {versione: valore})
        telemetria = r / "bin" / "telemetria.py"
        if not telemetria.is_file():  # col plugin il codice non sta nell'Orsa
            telemetria = Path(os.path.realpath(__file__)).parent / "telemetria.py"
        subprocess.run([sys.executable, str(telemetria), "registra", "aggiorna", valore],
                       capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        pass


def cmd_riapri(r: Path) -> int:
    """Per /fine --rotazione (S2): uscita 0 e una riga se un rilascio aspetta una chiusura vera, 1 se no. La rotazione
    fa /clear, che non chiude Claude Code: con un rilascio pronto la sessione propone di chiudere e riaprire."""
    stato = leggi(file_stato(r))
    if stato.get("stato") != "pronto" or not stato.get("versione") or manuali(r):
        return 1
    print(f"RIAPRI: la versione {stato['versione']} di Arturo è pronta e si installa solo a una chiusura vera: "
          f"{RIAPRI}.")
    return 0


def _esito(r: Path, tag: str, parola: str, riga: str, commentate: list = None, impostazioni: str = "") -> int:
    dati = {"quando": int(time.time()), "versione": tag, "esito": parola, "riga": riga, "mostrato": False}
    if commentate:
        dati["commentate"] = commentate
    if impostazioni:
        dati["impostazioni"] = impostazioni
    scrivi(file_esito(r), dati)
    return 0 if parola == "APPLICATO" else 1


def main(argv: list) -> int:
    r = radice()
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    try:
        if argv == ["riapri"]:
            return cmd_riapri(r)
        if argv and argv[0] == "plugin" and argv[1:] in ([], ["--verifica"]):
            if not modo_plugin():
                print("COPIA IN ~/.claude: Arturo non è installato come plugin, vale la procedura con git.")
                return 5
            if len(argv) == 2:
                return cmd_plugin(solo_verifica=True)
            rc = cmd_applica(r, fare=lambda _r: cmd_plugin(), occupato=OCCUPATO)
            if rc == OCCUPATO:
                print("AGGIORNAMENTO IN CORSO: Arturo si sta già aggiornando, dalla chiusura di un'altra sessione. "
                      "Riprova tra un minuto.")
                return 1
            return rc
        if modo_plugin() and argv and argv[0] in ("stato", "controlla", "applica", "firmato"):
            # Col plugin non c'è git: stato e controlla dicono se c'è un rilascio nuovo (#4860), e la chiusura lo
            # installa con la strada di /aggiorna (10/11/2026). `applica --avvio` non serve: il plugin non rinvia.
            if argv == ["stato"]:
                return stato_plugin(r)
            if argv in (["controlla"], ["controlla", "--subito"]):
                return controlla_plugin(r, forza=len(argv) == 2)
            if argv == ["applica"]:
                return cmd_applica(r, fare=_applica_plugin)
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
