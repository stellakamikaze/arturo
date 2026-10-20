#!/usr/bin/env python3
"""arturo aggiornamenti: Arturo si aggiorna da solo, come Claude Code (16/10/2026, #3477).

Mentre lavori, la barra in basso dice quando c'è una versione nuova. Alla chiusura della sessione
Arturo la installa da solo, con la stessa procedura di /aggiorna: copia di prova, le tue aggiunte
in personale/, controllo della config. Si installano solo i rilasci con tag firmati dalla chiave di
chi mantiene Arturo, verificati con la chiave che hai già installata (firme/rilasci.allowed_signers).

  stato        cosa sa adesso, senza rete: l'avvio della sessione lo stampa
  controlla    scarica i tag e aggiorna lo stato, al massimo una volta all'ora (la barra in basso)
  applica      installa la versione nuova, se tutto torna (la chiusura della sessione)
  manuali      niente si installa da solo: resta l'avviso, e aggiorni tu con /aggiorna
  automatici   torna all'aggiornamento automatico (la scelta di partenza)
  firmato      l'ultimo rilascio, solo se la sua firma è valida: è l'unico che /aggiorna applica

Non si installa niente da solo se: la firma manca o non è di Arturo; la storia pubblicata è stata
riscritta; hai modifiche non salvate in ~/.claude; un'altra sessione di Claude Code è aperta (la
installa l'ultima che chiude); l'aggiornamento va in conflitto con le tue modifiche. In tutti questi
casi l'avviso resta, col motivo, e /aggiorna fa il resto con te. Una firma che manca o non torna non
si scavalca neanche con /aggiorna: è il segno di un repository manomesso, e l'avviso dice di non
aggiornare e di segnalarlo a chi mantiene Arturo (17/10/2026, #3504). Una firma che questo computer
non sa verificare (git prima della 2.34, OpenSSH prima della 8.2) blocca allo stesso modo, ma senza
allarme: «firma non verificabile», uscita 4 di firmato. ARTURO_AGGIORNAMENTI=manuali
ha lo stesso effetto di «manuali». Solo libreria standard, Python 3.8 o successivo.
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

AIUTO = __doc__.split("\n\n")[2] if __doc__ else ""
ORA = 3600            # controlla scarica al massimo una volta all'ora
ATTESA_MAX = 90       # secondi: quanto applica aspetta che Claude Code si chiuda davvero
FIRME = "firme/rilasci.allowed_signers"
# Il messaggio di una firma che manca o non torna, uguale ovunque compare (avvio, barra, /aggiorna).
COMPROMISSIONE = "possibile compromissione: non aggiornare, segnala a chi mantiene Arturo"
# Solo questi errori dicono che la firma c'è stata verificata e non torna. Ogni altro errore (git prima
# della 2.34 che non conosce gpg.format=ssh, OpenSSH prima della 8.2 senza `ssh-keygen -Y`, un timeout)
# vuol dire che la verifica non è partita: niente si installa lo stesso, ma non è una compromissione
# (revisione del rilascio del 17/10/2026).
FIRMA_SBAGLIATA = re.compile(r"no signature found|no principal matched|could not verify signature|bad signature",
                             re.I)
NON_VERIFICABILE = ("questo computer non sa controllare la firma dei rilasci: servono git 2.34 e OpenSSH 8.2, "
                    "o più recenti")


def radice() -> Path:
    return Path(os.environ.get("ARTURO_RADICE") or Path.home() / ".claude")


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
    (`v1-0-g…`): non è un tag, e verify-tag lo rifiuta."""
    return git(r, "describe", "--tags", "--abbrev=0", "--match", "v*", f"{src}/main").stdout.strip()


def verifica_firma(r: Path, tag: str) -> tuple:
    """(motivo, compromesso): motivo vuoto se il tag è firmato da una chiave di firme/rilasci.allowed_signers
    della copia installata. compromesso solo se la firma manca o non torna, non se la verifica non è partita.
    È l'unica verifica: la usano l'aggiornamento automatico e /aggiorna."""
    firme = r / FIRME
    if not firme.is_file():
        return f"manca {FIRME}: la firma non si può verificare", True
    verifica = git(r, "-c", "gpg.format=ssh", "-c", f"gpg.ssh.allowedSignersFile={firme}", "verify-tag", tag)
    if verifica.returncode == 0:
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
    return dict(stato, stato="pronto", motivo="")


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
            righe = [x for x in uscita.splitlines() if x.strip()]
            return sum(1 for x in righe if "AnthropicClaude" not in x and "WindowsApps" not in x
                       and (re.search(r"\\\.local\\bin\\claude\.exe", x, re.I) or "claude-code" in x.lower()))
        uscita = subprocess.run(["ps", "-Ao", "args="], capture_output=True, text=True, timeout=30).stdout
        conta = 0
        for riga in uscita.splitlines():
            parti = riga.split()
            if parti and (os.path.basename(parti[0]) == "claude" or "@anthropic-ai/claude-code" in riga):
                conta += 1
        return conta
    except (OSError, subprocess.SubprocessError, ValueError):
        return 1  # nel dubbio una sessione è aperta: si rimanda


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
    if esito and not esito.get("mostrato"):
        if esito.get("esito") == "APPLICATO":
            righe.append(f"ARTURO: aggiornato a {esito.get('versione')} alla chiusura della sessione. /novita racconta "
                         "cosa cambia.")
        else:
            righe.append(f"ARTURO: l'aggiornamento automatico a {esito.get('versione')} non è partito "
                         f"({esito.get('riga') or 'motivo sconosciuto'}). Scaricalo con /aggiorna.")
        try:
            scrivi(file_esito(r), dict(esito, mostrato=True))
        except OSError:
            pass
    stato = calcola(r)
    vecchio = leggi(file_stato(r))
    stato["controllato"] = vecchio.get("controllato", 0)  # calcola non scarica: l'ultimo controllo resta quello
    try:
        scrivi(file_stato(r), stato)
    except OSError:
        pass
    if stato["stato"] == "pronto":
        righe.append(f"ARTURO: c'è la versione {stato['versione']}: si installa da sola alla chiusura della sessione.")
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


def cmd_applica(r: Path) -> int:
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
        return _applica(r)
    finally:
        shutil.rmtree(str(blocco), ignore_errors=True)


def _applica(r: Path) -> int:
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
    while processi_claude() > 0:
        if time.time() >= limite:
            _segnala_ostacolo(r, stato, "rinviato")
            return 0  # un'altra sessione è aperta: la installa l'ultima che chiude
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
        procedura.write_text(testo.stdout, encoding="utf-8", newline="\n")
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
    esito = next((x for x in righe if re.match(r"^(APPLICATO|GIÀ AGGIORNATO|APPLICAZIONE|RIPRISTINO)", x)), "")
    if esito.startswith("GIÀ AGGIORNATO"):
        scrivi(file_stato(r), calcola(r))
        return 0
    parola = "APPLICATO" if esito.startswith("APPLICATO") else (esito.split(":")[0] or "FALLITO")
    _esito(r, tag, parola, esito[:240])
    scrivi(file_stato(r), calcola(r))
    return 0 if parola == "APPLICATO" else 1


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


def _esito(r: Path, tag: str, parola: str, riga: str) -> int:
    scrivi(file_esito(r), {"quando": int(time.time()), "versione": tag, "esito": parola, "riga": riga, "mostrato": False})
    return 0 if parola == "APPLICATO" else 1


def main(argv: list) -> int:
    r = radice()
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    try:
        if argv == ["stato"]:
            return cmd_stato(r)
        if argv in (["controlla"], ["controlla", "--subito"]):
            return cmd_controlla(r, forza=len(argv) == 2)
        if argv == ["applica"]:
            return cmd_applica(r)
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
    print(f"Errore: comando sconosciuto: «{' '.join(argv)}»\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
