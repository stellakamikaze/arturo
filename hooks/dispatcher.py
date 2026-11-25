#!/usr/bin/env python3
"""Il dispatcher delle guardie di Bash in Python: bash-dispatcher.sh in un processo solo (#6492, 23/11/2026).

Legge su stdin l'evento PreToolUse di Bash o Monitor, chiede al pre-filtro (evento_bash.py, prefiltro_bash.py)
quali guardie servono e le lancia nell'ordine di sempre. Una guardia `.py` gira nello stesso processo
(nel_processo.py), una `.sh` resta un processo. Così hooks/hub.py lo esegue insieme agli altri hook di
PreToolUse, senza bash e senza un python per guardia: su Windows ogni processo costava 0,1-0,9 s, e il
dispatcher arrivava a 1,6 s di mediana prima di ogni comando (misura del 23/11/2026).

bash-dispatcher.sh resta come guscio: legge l'evento, lancia questo file e, se Python non parte o si ferma,
chiede conferma. I banchi delle guardie passano dal guscio, quindi provano anche questo file.

Ogni guardia può:
  - uscire con 2           -> blocco duro (stderr al modello);
  - uscire con altro codice -> guardia rotta: si chiede conferma (fail-closed);
  - stampare il JSON di permissionDecision e uscire con 0 -> ask, allow o deny esplicito;
  - non stampare niente e uscire con 0 -> tace, e si passa alla guardia seguente.
Al massimo una decisione esce: la prima guardia che decide chiude il giro.

Il tetto: tutto il giro ha 25 secondi (TETTO), come le guardie di bash-dispatcher.sh con ARTURO_RESTANTE
(#6363). Lo conta faulthandler da un suo thread, anche dentro una regex: oltre, il processo esce con 1, e il
guscio o la coda della voce di hub in settings.json chiedono conferma. Claude Code ferma l'hook dopo 30
secondi, e allora il comando partiva senza giudizio.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
if QUI not in sys.path:
    sys.path.insert(0, QUI)
import evento_bash  # noqa: E402
import nel_processo  # noqa: E402

TETTO = 25.0
LIMITE = 1_000_000
PUNTI_LOCALI = ("prima-danger", "danger-claude", "attenua", "finale")
_RE_GUARDIA = re.compile(r"[A-Za-z0-9_.-]+\.(py|sh)")
_RE_NOME = re.compile(r"[a-z0-9-]{1,30}")
# "command" seguito da un valore non vuoto, con la classe [[:space:]] di bash scritta per intero.
_RE_HA_COMANDO = re.compile(r'"command"[ \t\n\r\f\v]*:[ \t\n\r\f\v]*"[^"]')


def _ask(motivo):
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                              "permissionDecisionReason": motivo}}, ensure_ascii=False,
                      separators=(",", ":"))


ASK_PYTHON = _ask("Le guardie non leggono il comando: manca un python3 che funziona. Conferma solo se sai "
                  "cosa fa. Per sistemare: /diagnosi.")
ASK_LUNGO = _ask("Comando troppo lungo per le guardie (oltre 1.000.000 di caratteri): non lo hanno letto. "
                 "Conferma solo se sai cosa fa, oppure metti il contenuto in un file.")
ASK_COPIA = _ask("Le guardie non riescono a leggere questo comando (troppo lungo o con caratteri non validi). "
                 "Conferma solo se sai cosa fa.")
ASK_PREFILTRO = _ask("Il pre-filtro delle guardie si è fermato su questo comando. Conferma solo se sai cosa "
                     "fa. Per sistemare: /diagnosi.")
ASK_GUARDIA = _ask("Una guardia non ha prodotto una decisione valida. Conferma prima di eseguire il comando.")
ALLOW_MEMORIA = json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse", "permissionDecision": "allow",
    "permissionDecisionReason": "scrittura di un handoff o di una memoria in ~/.claude: approvata dal ramo "
                                "memoria del dispatcher"}}, ensure_ascii=False, separators=(",", ":"))


class Fine(Exception):
    """Il giro finisce: `codice` e il testo per stdout (vuoto: niente da dire)."""

    def __init__(self, codice, uscita=""):
        super().__init__(codice)
        self.codice = codice
        self.uscita = uscita


def _casa():
    return os.environ.get("HOME") or os.path.expanduser("~")


def _bash():
    import shutil
    # Su Windows un nome nudo passato a CreateProcess cerca prima in System32, dove `bash.exe` è WSL.
    return shutil.which("bash") or "bash"


class Dispatcher:
    def __init__(self, grezzo):
        self.grezzo = grezzo
        self.casa = _casa()
        self.hooks = QUI
        self.bin = os.path.join(os.path.dirname(QUI), "bin")
        self.orsa = os.path.join(self.casa, ".claude", "hooks")
        self.errori = []                 # stderr da passare a chi chiama, nell'ordine
        self.riserva = ""
        self.senza_allow = False
        self.bd_fatto = False
        self.locali = []                 # (punto, guardia, argomenti)
        self.comando = self.guardie = self.copia = self.uso = self.ridotto = ""
        self.viste = set()
        self.viste_testo = []

    # --- flussi ---
    def scrivi_err(self, testo):
        if testo:
            self.errori.append(testo)

    def vista(self, nome):
        return nome in self.viste

    # --- file e lancio ---
    def guardia_file(self, nome):
        qui = os.path.join(self.hooks, nome)
        return qui if os.path.isfile(qui) else os.path.join(self.orsa, nome)

    def py(self, percorso, argomenti, entrata, ambiente=None):
        """Uno script Python nello stesso processo. Torna (codice, stdout, stderr) in bytes."""
        codice, out, err, scaduto = nel_processo.lancia(percorso, argomenti, entrata, ambiente)
        if scaduto:
            # Interrotto da hub a fine tempo: una guardia ferma a metà non ha giudicato, e vale come rotta.
            return 1, b"", err
        return codice, out, err

    def lancia_guardia(self, nome, argomenti, ambiente=None):
        entrata = (self.copia + "\n").encode("utf-8", "replace")
        amb = {"ARTURO_REGOLA": "1"}
        amb.update(ambiente or {})
        percorso = self.guardia_file(nome)
        if nome.endswith(".sh"):
            import subprocess
            env = dict(os.environ, **amb)
            try:
                r = subprocess.run([_bash(), percorso] + list(argomenti), input=entrata, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=env,
                                   timeout=max(TETTO - (time.monotonic() - self.inizio), 0.5))
                return r.returncode, r.stdout, r.stderr
            except subprocess.TimeoutExpired:
                return 1, b"", b""
            except OSError as e:
                return 127, b"", str(e).encode("utf-8")
        return self.py(percorso, argomenti, entrata, amb)

    def telemetria(self, *argomenti):
        f = os.path.join(self.bin, "telemetria.py")
        if os.path.isfile(f):
            try:
                self.py(f, list(argomenti), b"")
            except Exception:
                pass

    # --- telemetria e conferme ---
    def ask_guardia(self, nome=""):
        if nome:
            self.telemetria("registra", "errore", nome)
        raise Fine(0, ASK_GUARDIA)

    def segna_errore(self, nome, causa):
        self.telemetria("registra", "errore", "%s.%s" % (nome, causa))

    def segna_guardia(self, nome):
        self.telemetria("registra", "guardia", nome)

    def segna_chiede(self, nome, regola):
        if self.uso:
            self.telemetria("chiede", nome + ("." + regola if regola else ""), self.uso)

    # --- guardie personali ---
    def leggi_locali(self):
        f = os.path.join(self.casa, ".claude", "arturo", "bash-dispatcher.local")
        vecchio = os.path.join(self.casa, ".claude", "hooks", "bash-dispatcher.local")
        if not os.path.isfile(f) and os.path.isfile(vecchio):
            f = vecchio
        if not os.path.isfile(f):
            return
        try:
            with open(f, "rb") as h:
                testo = h.read().decode("utf-8", "replace")
        except OSError:
            return
        for riga in testo.split("\n"):
            riga = riga.split("#", 1)[0].replace("\r", "")
            parti = riga.split(None, 2)
            if not parti:
                continue
            punto = parti[0]
            nome = parti[1] if len(parti) > 1 else ""
            resto = parti[2].strip() if len(parti) > 2 else ""
            if punto in PUNTI_LOCALI and _RE_GUARDIA.fullmatch(nome) and os.path.isfile(self.guardia_file(nome)):
                self.locali.append((punto, nome, resto.split()))
            else:
                self.scrivi_err("bash-dispatcher.local: riga ignorata, forma non valida o guardia assente: %s\n"
                                % riga)

    def di_punto(self, punto):
        return [(n, a) for p, n, a in self.locali if p == punto]

    def attenua(self, nome, uscita):
        for guardia, argomenti in self.di_punto("attenua"):
            codice, out, _err = self.lancia_guardia(guardia, argomenti + [nome], {"ATTENUA_OUT": uscita})
            if codice != 0:
                continue
            if out.decode("utf-8", "replace").replace("\r", "").replace("\n", "") == "tace":
                return True
        return False

    # --- una guardia ---
    def run_guard(self, nome, *argomenti):
        riserva, senza_allow = self.riserva, self.senza_allow
        self.riserva, self.senza_allow = "", False
        codice, out_b, err_b = self.lancia_guardia(nome, list(argomenti))
        self.scrivi_err(err_b.decode("utf-8", "replace"))
        if codice not in (0, 2) and riserva:
            self.run_guard(riserva)
            return
        out = out_b.decode("utf-8", "replace").replace("\0", "").rstrip("\n")
        causa = regola = ""
        # Dopo il JSON una guardia può scrivere "REGOLA: <nome>" e, sotto, "CAUSA: <nome>" (22/10 e 21/11/2026):
        # si tolgono prima di ogni controllo, Claude Code riceve solo il JSON.
        if "\nCAUSA: " in out:
            i = out.rindex("\nCAUSA: ")
            causa = out[i + len("\nCAUSA: "):]
            causa = causa[:-1] if causa.endswith("\r") else causa
            out = out[:i]
            out = out[:-1] if out.endswith("\r") else out
            causa = causa if _RE_NOME.fullmatch(causa) else ""
        if "\nREGOLA: " in out:
            i = out.rindex("\nREGOLA: ")
            regola = out[i + len("\nREGOLA: "):]
            regola = regola[:-1] if regola.endswith("\r") else regola
            out = out[:i]
            out = out[:-1] if out.endswith("\r") else out
            regola = regola if _RE_NOME.fullmatch(regola) else ""
        if codice == 2:
            if out:
                self.scrivi_err(out + "\n")
            self.segna_guardia(nome)
            raise Fine(2)
        if codice != 0:
            self.ask_guardia(nome)
        if not out:
            return
        try:
            valida = json.loads(out)["hookSpecificOutput"]["permissionDecision"] in ("ask", "allow", "deny")
        except Exception:
            valida = False
        if not valida:
            self.ask_guardia(nome)
        if senza_allow and '"allow"' in out:
            self.ask_guardia(nome)
        if causa and '"ask"' in out:
            self.segna_errore(nome, causa)
        if '"ask"' in out and nome in self.attenuabili and self.attenua(nome, out):
            return
        if '"deny"' in out:
            self.segna_guardia(nome)
        if '"ask"' in out:
            self.segna_chiede(nome, regola)
        raise Fine(0, out)

    def danger_una_volta(self):
        # block-dangerous riceve sempre lo stesso comando: se ha già taciuto, non riparte (#6259).
        if self.bd_fatto:
            return
        self.bd_fatto = True
        self.run_guard("block-dangerous.py")

    def esporta_ridotto(self):
        if self.vista("ridotto"):
            os.environ["COMMS_REDUCED"] = self.ridotto

    # --- il giro ---
    def leggi(self):
        opzioni = set()
        if os.name == "nt" or sys.platform in ("cygwin", "msys"):
            opzioni |= {"crlf", "nocase"}
        elif sys.platform == "darwin":
            opzioni.add("nocase")
        # Git Bash passa SHELL a un programma nativo come percorso Windows (`C:\...\usr\bin\zsh`): il nome si
        # prende dopo l'ultima barra di tutti e due i tipi, come `${SHELL##*/}` sul valore POSIX.
        shell = re.split(r"[\\/]", os.environ.get("SHELL", ""))[-1]
        if shell.lower() in ("zsh", "zsh.exe"):
            opzioni.add("zsh")
        try:
            campi, dati, grezzo = evento_bash.campi_da(self.grezzo, "crlf" in opzioni)
            viste, ridotto = evento_bash.viste_da(campi, dati, grezzo, opzioni)
        except Exception:
            return
        self.comando, self.guardie, self.copia, self.uso = campi
        # Le viste come le leggeva bash: parole separate da spazi.
        self.viste_testo = " ".join(viste).split()
        self.viste = set(self.viste_testo)
        self.ridotto = ridotto or ""

    def timeout_c_e(self):
        import shutil
        if shutil.which("timeout"):
            return True
        cartelle = os.environ.get("ARTURO_TIMEOUT_CARTELLE")
        for d in (cartelle.split() if cartelle is not None else ["/opt/homebrew/bin", "/usr/local/bin"]):
            f = os.path.join(d, "timeout")
            if os.path.isfile(f) and os.access(f, os.X_OK):
                return True
        return False

    def giro(self):
        self.inizio = time.monotonic()
        self.leggi()
        if not self.comando and _RE_HA_COMANDO.search(self.grezzo):
            raise Fine(0, ASK_PYTHON)
        if len(self.guardie) > LIMITE:
            raise Fine(0, ASK_LUNGO)
        if self.comando and not self.copia:
            raise Fine(0, ASK_COPIA)
        if self.vista("errore"):
            raise Fine(0, ASK_PREFILTRO)
        os.environ.pop("COMMS_REDUCED", None)

        # Glob dentro un'opzione, in zsh: `--include=*.md` senza virgolette muore con "no matches found".
        for v in self.viste_testo:
            if v.startswith("glob-zsh="):
                optglob = v[len("glob-zsh="):]
                opt, _, val = optglob.partition("=")
                self.scrivi_err("BLOCCATO: in zsh '%s' senza virgolette e' un glob che fallisce con 'no matches "
                                "found'. Scrivi %s='%s'.\n" % (optglob, opt, val))
                raise Fine(2)
        # timeout su macOS: non esiste, e la pipeline riceve stdout vuoto.
        if self.vista("timeout") and not self.timeout_c_e():
            self.scrivi_err("BLOCCATO: 'timeout' non esiste su questo sistema. Fallirebbe con 'command not "
                            "found' e stdout vuoto. Usa il parametro timeout del tool Bash, 'curl --max-time N', "
                            "oppure 'cmd & pid=$!; sleep N; kill $pid'.\n")
            raise Fine(2)

        self.leggi_locali()
        self.attenuabili = {"block-dangerous.py", "exfil-guard.py", "data-guard.py"}
        dc = self.di_punto("danger-claude")
        if dc:
            self.attenuabili.add(dc[0][0])

        if self.vista("commit"):
            self.run_guard("commit-secret-gate.py")
        if self.vista("push"):
            self.run_guard("commit-secret-gate.py", "push")
        if self.vista("danger-git"):
            self.danger_una_volta()
        # Skip git puro: ogni programma eseguito è git o cd, senza sostituzioni né opzioni che scrivono fuori.
        # Un programma nascosto (`git rm "$F"`) lo giudica block-dangerous anche qui, prima dello skip.
        if self.vista("git-puro"):
            if self.vista("nascosto"):
                self.danger_una_volta()
            raise Fine(0)
        if self.vista("git-opzioni"):
            self.danger_una_volta()
        if self.vista("comms"):
            self.esporta_ridotto()
            self.run_guard("comms-guard.py")
        if self.vista("danger"):
            for nome, argomenti in self.di_punto("prima-danger"):
                self.run_guard(nome, *argomenti)
            if dc and self.vista("claude"):
                self.riserva, self.senza_allow = "block-dangerous.py", True
                self.run_guard(dc[0][0], *dc[0][1])
            else:
                self.danger_una_volta()
        # Il programma nascosto parla dopo prima-danger: block-dangerous ha la regola codice-nascosto (#6323).
        if self.vista("nascosto"):
            self.danger_una_volta()
        if self.vista("exfil"):
            self.esporta_ridotto()
            self.run_guard("exfil-guard.py")
        if self.vista("egress"):
            self.esporta_ridotto()
            self.run_guard("exfil-guard.py")
        elif self.vista("egress-tcp"):
            os.environ["COMMS_REDUCED"] = self.guardie
            self.run_guard("exfil-guard.py")
        if self.vista("data"):
            self.run_guard("data-guard.py")
        if self.vista("gh"):
            self.run_guard("gh-destructive-guard.py")
        if self.vista("claude"):
            for nome, argomenti in self.di_punto("finale"):
                self.run_guard(nome, *argomenti)
        # Ramo memoria e handoff: nessuna guardia ha deciso, e forma_comando.py ammette il comando.
        if self.vista("memoria"):
            codice, _o, _e = self.py(os.path.join(self.hooks, "forma_comando.py"), ["ramo-memoria"],
                                     (self.grezzo + "\n").encode("utf-8", "replace"))
            if codice == 0:
                raise Fine(0, ALLOW_MEMORIA)
        raise Fine(0)


def _arma_tetto():
    """faulthandler esce con 1 dopo TETTO secondi, da un suo thread: anche dentro una regex o una sleep."""
    try:
        import faulthandler
        faulthandler.dump_traceback_later(TETTO, exit=True, file=sys.__stderr__ or sys.stderr)
        return True
    except Exception:
        try:
            import faulthandler
            fd = os.open(os.devnull, os.O_WRONLY)
            faulthandler.dump_traceback_later(TETTO, exit=True, file=fd)
            return True
        except Exception:
            return False


def _disarma_tetto():
    try:
        import faulthandler
        faulthandler.cancel_dump_traceback_later()
    except Exception:
        pass


def main():
    grezzo = sys.stdin.buffer.read().decode("utf-8", "replace").rstrip("\n")
    prima = dict(os.environ)
    os.environ["PYTHONIOENCODING"] = "utf-8"
    d = Dispatcher(grezzo)
    _arma_tetto()
    try:
        try:
            d.giro()
            esito = Fine(0)
        except Fine as f:
            esito = f
        except BaseException:  # noqa: BLE001  un guasto qui, anche un'interruzione di hub, chiede conferma
            esito = Fine(0, ASK_GUARDIA)
    finally:
        _disarma_tetto()
        if dict(os.environ) != prima:
            os.environ.clear()
            os.environ.update(prima)
    if d.errori:
        sys.stderr.write("".join(d.errori))
        sys.stderr.flush()
    if esito.uscita:
        sys.stdout.write(esito.uscita + "\n")
        sys.stdout.flush()
    return esito.codice


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
