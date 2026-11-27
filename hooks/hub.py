#!/usr/bin/env python3
"""Un processo per evento: `hub.py <voce>` lancia nello stesso processo gli hook Python che prima
partivano uno per uno (#6492, 23/11/2026).

Perché: su Windows ogni processo costa 0,1-0,9 s, mentre la logica di un hook ne usa 0,02. Su un PC Windows
ogni Bash avviava 3 hook prima e 6 dopo: 1,6 s di mediana prima del comando, e in 3 giorni 56 hook di
prompt e di avvio annullati per tempo scaduto (misura del 23/11 sui transcript).

Voci: `pre` (PreToolUse), `post` (PostToolUse), `postfail` (PostToolUseFailure), `prompt`
(UserPromptSubmit; azzera anche il conto di continua.py). La TABELLA dice, per ogni voce, quali hook girano su quale strumento, nell'ordine di
settings.json. Nella voce `prompt` un codice 2 (il prompt si scarta) ferma gli hook dopo.

Come gira un hook:
- il suo file si esegue come `__main__`, col bytecode in cache (come `evento_bash.py esegui`);
- stdin è il payload, stdout e stderr si raccolgono, `sys.exit` dà il codice;
- ogni hook ha il suo tetto: oltre, il thread di guardia interrompe il thread principale e l'hook si
  salta, come quando Claude Code lo annullava. Dopo un hook scaduto gli altri girano ognuno nel suo
  processo, perché quello scaduto può ancora scrivere nei flussi condivisi;
- un hook che si rompe (eccezione, codice diverso da 0 e da 2) non ferma gli altri e finisce nel registro.

Come si fondono le uscite (le stesse regole di Claude Code con più hook):
- un codice 2 blocca: esce 2 con lo stderr di tutti gli hook che hanno dato 2;
- `permissionDecision`: vince la più stretta, deny, poi ask, poi allow; il motivo è quello dei vincitori;
- `additionalContext` e `systemMessage` si accodano; `decision: block` e `continue: false` valgono se
  li dà un hook solo.

Sul tetto complessivo: settings.json dà a hub il suo timeout. Un secondo e mezzo prima, il thread di
guardia stampa ciò che ha raccolto ed esce, così Claude Code non butta via le decisioni già prese.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, QUI)
import nel_processo  # noqa: E402  esegue un hook come __main__, dal bytecode in cache

EDIT = "Edit|MultiEdit|Write|NotebookEdit"
WEB_EGRESS = ("WebFetch|mcp__jina__.*|mcp__tavily__.*|mcp__playwright__browser_navigate|"
              "mcp__playwright-ff__browser_navigate|mcp__claude-in-chrome__navigate|"
              "mcp__claude-in-chrome__browser_batch")

# Una riga: (matcher di Claude Code, parola che il comando Bash deve contenere o None, file relativo alla
# radice, argomenti, tetto in secondi, condizione). La parola sostituisce il campo `if` di settings.json
# (`Bash(*gws*)`): gli hook col filtro escono già da soli se la parola manca (HI03). Vale solo su Bash, e "a|b"
# vuol dire una delle due.
# La condizione "telemetria-attese" è il controllo di bin/telemetria-esito.sh: senza il file l'hook tace.
TABELLA = {
    "pre": [
        (EDIT + "|Bash", None, "hooks/agente-worktree.py", [], 5, None),
        ("Read|Grep", None, "hooks/block-dangerous.py", [], 10, None),
        (EDIT, None, "hooks/protect_claude_md.py", [], 20, None),
        # Il dispatcher delle guardie di Bash (dispatcher.py, ex bash-dispatcher.sh): ha un suo tetto di 25 s,
        # e oltre chiede conferma. In settings.json la voce di Bash ha la coda che chiede anche se hub muore.
        ("Bash|Monitor", None, "hooks/dispatcher.py", [], 30, None),
        ("Bash", "gws", "hooks/gws-esito.py", [], 10, None),
        ("mcp__.*[Dd]raft.*", None, "hooks/bozze-mcp-auto-approve.py", [], 5, None),
        (WEB_EGRESS, None, "hooks/web-egress-guard.py", [], 20, None),
    ],
    "post": [
        ("Bash", "commit", "hooks/block-dangerous.py", ["dopo"], 10, None),
        ("Bash", "gws", "hooks/gws-esito.py", [], 10, None),
        (EDIT, None, "hooks/emoji_remover.py", [], 10, None),
        (EDIT + "|Bash|WebFetch|WebSearch|mcp__.*|Monitor", None, "bin/telemetria.py", ["esito"], 10,
         "telemetria-attese"),
        # Su Bash solo coi programmi che leggono fonti esterne (#5601): gli stessi nomi di FONTI_ESTERNE nello scanner.
        ("WebFetch|WebSearch|mcp__.*|Bash", "gws|curl|wget|scrape|gh|yt-dlp|gallery-dl",
         "hooks/prompt-injection-scanner.py", [], 10, None),
        ("Bash|WebFetch|WebSearch|mcp__.*", None, "hooks/credential-leak-scanner.py", [], 10, None),
        ("Skill", None, "hooks/estensione-skill.py", [], 5, None),
        (EDIT + "|Bash", None, "hooks/memory-write-scanner.py", [], 6, None),
        # context-monitor.py (ex context-monitor.js, #6492 B5): un processo node in meno dopo ogni Bash e Edit.
        (EDIT + "|Bash", None, "hooks/context-monitor.py", [], 5, None),
    ],
    "postfail": [
        ("", None, "bin/telemetria.py", ["esito"], 10, "telemetria-attese"),
        ("", None, "hooks/memory-firma.py", [], 5, None),
        ("Bash", "gws", "hooks/gws-esito.py", [], 10, None),
    ],
    # inject-now.py (ex inject-now.sh, #6492 B4) e il ricordo della memoria: prima due processi più fino a 7
    # python3 avviati da inject-now.sh, a ogni messaggio.
    "prompt": [
        ("", None, "hooks/inject-now.py", [], 4, None),
        ("", None, "hooks/memory-retrieve.py", [], 5, None),
    ],
}

# Il timeout di hub in settings.json, per voce: il tetto complessivo parte da qui.
TETTO_VOCE = {"pre": 30, "post": 30, "postfail": 15, "prompt": 10}
MARGINE = 1.5
ORDINE = {"deny": 3, "ask": 2, "allow": 1}


def _tabella(voce):
    """ARTURO_HUB_TABELLA (solo per i banchi): un file JSON con le righe della voce, stessa forma."""
    finta = os.environ.get("ARTURO_HUB_TABELLA")
    if finta:
        with open(finta, encoding="utf-8") as f:
            return [tuple(r) for r in json.load(f).get(voce, [])]
    return TABELLA.get(voce, [])


def _combacia(matcher, strumento):
    import re
    if not matcher:
        return True
    try:
        return re.fullmatch(matcher, strumento or "") is not None
    except re.error:
        return False


def _condizione(nome):
    if nome == "telemetria-attese":
        casa = os.environ.get("HOME") or os.path.expanduser("~")
        return os.path.isfile(os.path.join(casa, ".claude", "session-env", "telemetria-attese.json"))
    return True


def scelti(voce, dati):
    strumento = dati.get("tool_name") or ""
    comando = ""
    if strumento == "Bash":
        comando = str((dati.get("tool_input") or {}).get("command") or "")
    righe = []
    for matcher, parola, file, argomenti, tetto, cond in _tabella(voce):
        if not _combacia(matcher, strumento):
            continue
        # La parola vale solo per Bash; "a|b" vuol dire una delle due (#5601).
        if parola and strumento == "Bash" and not any(p in comando for p in parola.split("|")):
            continue
        if cond and not _condizione(cond):
            continue
        percorso = file if os.path.isabs(file) else os.path.join(RADICE, file)
        if os.path.isfile(percorso):
            righe.append((percorso, list(argomenti), float(tetto)))
    return righe


class Guardia:
    """Thread di guardia: interrompe l'hook che sfora il suo tetto e, vicino al tetto complessivo,
    stampa ciò che c'è ed esce."""

    def __init__(self, fine_totale, emetti):
        self.fine_totale = fine_totale
        self.emetti = emetti
        self.fine_hook = None
        self.attivo = None
        self.lock = threading.Lock()
        t = threading.Thread(target=self._giro, daemon=True)
        t.start()

    def inizia(self, fine):
        with self.lock:
            self.fine_hook = fine
            self.attivo = object()
            return self.attivo

    def finisce(self):
        with self.lock:
            self.fine_hook = None
            self.attivo = None

    def _giro(self):
        import _thread
        interrotto = None
        while True:
            time.sleep(0.05)
            ora = time.monotonic()
            if ora >= self.fine_totale:
                self.emetti(uscita_forzata=True)
                os._exit(_codice_corrente[0])
            with self.lock:
                if self.fine_hook is not None and ora >= self.fine_hook and self.attivo is not interrotto:
                    interrotto = self.attivo
                    _thread.interrupt_main()


_codice_corrente = [0]


# L'esecuzione nello stesso processo sta in nel_processo.py, comune con dispatcher.py.
_stato = nel_processo.stato
_ripristina = nel_processo.ripristina
_nel_processo = nel_processo.esegui


def _in_processo_a_parte(percorso, argomenti, payload, tetto):
    try:
        r = subprocess.run([sys.executable, percorso] + argomenti, input=payload, capture_output=True,
                           timeout=tetto)
        return r.returncode, r.stdout, r.stderr, False
    except subprocess.TimeoutExpired:
        return 0, b"", b"", True
    except OSError as e:
        return 1, b"", str(e).encode("utf-8"), False


class Raccolta:
    def __init__(self, evento):
        self.evento = evento
        self.blocchi = []        # stderr degli hook con codice 2
        self.decisioni = []      # (decisione, motivo)
        self.contesti = []
        self.messaggi = []
        self.block = []          # motivi di decision: block
        self.ferma = None        # stopReason di continue: false
        self.altri = {}          # altri campi di hookSpecificOutput (il primo vince)
        self.lock = threading.Lock()
        self.emesso = False

    def aggiungi(self, codice, out, err):
        with self.lock:
            if codice == 2:
                self.blocchi.append(err.decode("utf-8", "replace").strip())
                return
            if codice != 0:
                return
            testo = out.decode("utf-8", "replace").strip()
            if not testo:
                return
            try:
                d = json.loads(testo)
            except ValueError:
                d = None
            if not isinstance(d, dict):
                if self.evento in ("UserPromptSubmit", "SessionStart"):
                    # Su Windows Python scrive \r\n anche nel processo: il contesto resta a righe \n come sul Mac.
                    self.contesti.append(testo.replace("\r\n", "\n"))
                return
            hso = d.get("hookSpecificOutput") or {}
            if isinstance(hso, dict):
                dec = hso.get("permissionDecision")
                if dec in ORDINE:
                    self.decisioni.append((dec, hso.get("permissionDecisionReason") or ""))
                if hso.get("additionalContext"):
                    self.contesti.append(str(hso["additionalContext"]))
                for k, v in hso.items():
                    if k not in ("hookEventName", "permissionDecision", "permissionDecisionReason",
                                 "additionalContext"):
                        self.altri.setdefault(k, v)
            if d.get("systemMessage"):
                self.messaggi.append(str(d["systemMessage"]))
            if d.get("decision") == "block":
                self.block.append(str(d.get("reason") or ""))
            if d.get("continue") is False and self.ferma is None:
                self.ferma = str(d.get("stopReason") or "")

    def risultato(self):
        """(codice, testo per stdout, testo per stderr)."""
        if self.blocchi:
            return 2, "", "\n".join(b for b in self.blocchi if b)
        out = {}
        hso = {}
        if self.decisioni:
            vince = max(self.decisioni, key=lambda x: ORDINE[x[0]])[0]
            hso["permissionDecision"] = vince
            motivi = [m for d, m in self.decisioni if d == vince and m]
            if motivi:
                hso["permissionDecisionReason"] = "\n".join(motivi)
        if self.contesti:
            hso["additionalContext"] = "\n\n".join(self.contesti)
        for k, v in self.altri.items():
            hso.setdefault(k, v)
        if hso:
            hso["hookEventName"] = self.evento
            out["hookSpecificOutput"] = hso
        if self.messaggi:
            out["systemMessage"] = "\n".join(self.messaggi)
        if self.block:
            out["decision"] = "block"
            out["reason"] = "\n".join(m for m in self.block if m)
        if self.ferma is not None:
            out["continue"] = False
            if self.ferma:
                out["stopReason"] = self.ferma
        return 0, (json.dumps(out, ensure_ascii=False) if out else ""), ""


def _registra(voce, righe):
    """Una riga per hook rotto o scaduto in ~/.claude/session-env/hub.log, tenuto sotto 200 KB."""
    if not righe:
        return
    try:
        casa = os.environ.get("HOME") or os.path.expanduser("~")
        d = os.path.join(casa, ".claude", "session-env")
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "hub.log")
        if os.path.isfile(f) and os.path.getsize(f) > 200_000:
            os.replace(f, f + ".1")
        with open(f, "a", encoding="utf-8") as h:
            for r in righe:
                h.write(time.strftime("%Y-%m-%dT%H:%M:%S") + " " + voce + " " + r + "\n")
    except OSError:
        pass


def _azzera_continua(dati):
    """Un messaggio della persona azzera il conto di continua.py (l'hook di Stop che fa continuare la sessione
    quando il passo dopo è di Claude): il tetto conta le continuazioni di fila senza la persona."""
    try:
        import continua
        continua.azzera(dati.get("session_id"))
    except Exception:  # noqa: BLE001 - il conto che non si azzera non deve fermare il prompt
        pass


def main(argv):
    voce = argv[1] if len(argv) > 1 else ""
    if voce not in TETTO_VOCE:
        sys.stderr.write("uso: hub.py pre|post|postfail|prompt\n")
        return 64
    payload = sys.stdin.buffer.read()
    try:
        dati = json.loads(payload.decode("utf-8") or "{}")
    except ValueError:
        dati = {}
    if not isinstance(dati, dict):
        dati = {}
    evento = dati.get("hook_event_name") or {"pre": "PreToolUse", "post": "PostToolUse",
                                               "postfail": "PostToolUseFailure", "prompt": "UserPromptSubmit"}[voce]
    if voce == "prompt":
        _azzera_continua(dati)
    raccolta = Raccolta(evento)
    vero_out, vero_err = sys.stdout, sys.stderr

    def emetti(uscita_forzata=False):
        with raccolta.lock:
            if raccolta.emesso:
                return
            raccolta.emesso = True
        codice, out, err = raccolta.risultato()
        _codice_corrente[0] = codice
        try:
            if out:
                vero_out.write(out)
                vero_out.flush()
            if err:
                vero_err.write(err)
                vero_err.flush()
        except Exception:
            pass

    tetto_totale = float(os.environ.get("ARTURO_HUB_TETTO") or TETTO_VOCE[voce])
    fine_totale = time.monotonic() + max(tetto_totale - MARGINE, 0.5)
    guardia = Guardia(fine_totale, emetti)
    dopo_scaduto = False
    registro = []
    for percorso, argomenti, tetto in scelti(voce, dati):
        resta = fine_totale - time.monotonic()
        if resta <= 0:
            break
        t = min(tetto, resta)
        inizio = time.monotonic()
        if dopo_scaduto:
            codice, out, err, scaduto = _in_processo_a_parte(percorso, argomenti, payload, t)
        else:
            stato = _stato()
            try:
                codice, out, err, scaduto = _nel_processo(percorso, argomenti, payload, guardia, t)
            except KeyboardInterrupt:
                codice, out, err, scaduto = 0, b"", b"", True
            finally:
                _ripristina(stato)
        nome = os.path.relpath(percorso, RADICE).replace(os.sep, "/")
        if scaduto:
            dopo_scaduto = True
            registro.append("%s scaduto dopo %.1f s" % (nome, time.monotonic() - inizio))
            continue
        if codice not in (0, 2):
            registro.append("%s codice %s: %s" % (nome, codice, err.decode("utf-8", "replace")[:300]))
        raccolta.aggiungi(codice, out, err)
        if codice == 2 and voce == "prompt":
            break
    _registra(voce, registro)
    emetti()
    return _codice_corrente[0]


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main(sys.argv))
