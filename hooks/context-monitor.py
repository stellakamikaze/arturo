#!/usr/bin/env python3
"""PostToolUse: avvisa l'agente quando il contesto si riempie (#6492, B5, 23/11/2026).

Porta in Python hooks/context-monitor.js, che avviava node dopo ogni Bash, Edit e Write: in settings.json gira
dentro `hooks/hub.py post`, senza processi in più. context-monitor.js resta come guscio per le config vecchie.

Come funziona: la statusline scrive le metriche in <tmp>/claude-ctx-<session_id>.json; dopo ogni strumento
questo hook le legge e, quando resta poco contesto, mette un avviso in additionalContext. La statusline lo
mostra solo alla persona: l'agente il suo contesto non lo vede.

Soglie (percento rimasto):
  WARNING  (<= 50%): chiudere il compito in corso. Era 35% fino al 23/11/2026: la rotazione è passata da
           ogni compito chiuso a metà contesto, e l'avviso segna il punto della rotazione.
  CRITICAL (<= 25%): fermarsi e salvare.
Una soglia fissa non regge finestre di misura diversa: CLAUDE_CTX_WARN e CLAUDE_CTX_CRIT (percento rimasto) la
cambiano. La persona sceglie il punto della rotazione con `arturo rotazione N` (bin/rotazione.py, 23/11/2026): N è
il percento USATO, da 30 a 70, in personale/rotazione.txt dell'Orsa. La variabile d'ambiente vince.
Fra due avvisi passano 5 strumenti; il passaggio da WARNING a CRITICAL avvisa subito.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

STALE_SECONDS = 60     # metriche più vecchie di 60 s: si ignorano
DEBOUNCE_CALLS = 5     # strumenti minimi fra due avvisi


def _casa():
    """os.homedir() di node: USERPROFILE su Windows, HOME altrove."""
    if os.name == "nt":
        return os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return os.environ.get("HOME") or os.path.expanduser("~")


def _tmp():
    """os.tmpdir() di node, dove la statusline scrive le metriche. Su Windows TEMP o TMP: un TMPDIR=/tmp di Git
    Bash non vale, perché statusline.js non lo guarda."""
    if os.name == "nt":
        d = os.environ.get("TEMP") or os.environ.get("TMP") or os.path.join(
            os.environ.get("SystemRoot") or os.environ.get("windir") or "C:\\Windows", "temp")
        if len(d) > 1 and d.endswith("\\") and not d.endswith(":\\"):
            d = d[:-1]
        return d
    d = os.environ.get("TMPDIR") or os.environ.get("TMP") or os.environ.get("TEMP") or "/tmp"
    if len(d) > 1 and d.endswith("/"):
        d = d[:-1]
    return d


def _numero(testo):
    """Number() di JavaScript su una variabile d'ambiente: 0 se manca o non è un numero."""
    try:
        n = float(str(testo).strip())
    except (TypeError, ValueError):
        return 0
    return n if n == n else 0


def soglia_persona():
    try:
        radice = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(_casa(), ".claude")
        with open(os.path.join(radice, "personale", "rotazione.txt"), encoding="utf-8") as f:
            testo = f.read()
        riga = next((r for r in re.split(r"\r?\n", testo) if r.strip() and not r.strip().startswith("#")), "")
        usato = float(re.sub(r"%$", "", riga.strip()))
        if usato.is_integer() and 30 <= usato <= 70:
            return 100 - int(usato)
    except (OSError, ValueError):
        pass
    return 0


def _testo(n):
    """Un numero come lo stampa un template di JavaScript: 50 e non 50.0."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def avviso(data):
    """Il testo dell'avviso per questo evento, o None."""
    sessione = data.get("session_id")
    if not sessione or not isinstance(sessione, str):
        return None
    # Un session_id con separatori o `..` costruirebbe un percorso fuori dalla cartella temporanea.
    if re.search(r"[/\\]|\.\.", sessione):
        return None
    # Un subagente porta il session_id del padre: leggerebbe le sue metriche e riceverebbe il consiglio di
    # rotazione del ciclo principale (e lancerebbe /fine --rotazione a metà compito). Le sue chiamate hanno
    # agent_id: qui si tace, e il file del padre resta com'è (review 7/11, finding 48).
    if data.get("agent_id"):
        return None
    cartella = _tmp()
    metriche_f = os.path.join(cartella, "claude-ctx-%s.json" % sessione)
    if not os.path.exists(metriche_f):
        return None
    with open(metriche_f, encoding="utf-8") as f:
        metriche = json.load(f)
    adesso = int(time.time())
    if metriche.get("timestamp") and adesso - metriche["timestamp"] > STALE_SECONDS:
        return None
    rimasto = metriche.get("remaining_percentage")
    usato = metriche.get("used_pct")
    if not isinstance(rimasto, (int, float)) or isinstance(rimasto, bool):
        return None
    avviso_soglia = _numero(os.environ.get("CLAUDE_CTX_WARN")) or soglia_persona() or 50
    critico_soglia = _numero(os.environ.get("CLAUDE_CTX_CRIT")) or 25
    if rimasto > avviso_soglia:
        return None

    avvisato_f = os.path.join(cartella, "claude-ctx-%s-warned.json" % sessione)
    stato = {"callsSinceWarn": 0, "lastLevel": None}
    primo = True
    if os.path.exists(avvisato_f):
        try:
            with open(avvisato_f, encoding="utf-8") as f:
                letto = json.load(f)
            if isinstance(letto, dict):
                stato = letto
            primo = False
        except (OSError, ValueError):
            pass  # file rotto: si riparte
    stato["callsSinceWarn"] = (stato.get("callsSinceWarn") or 0) + 1
    critico = rimasto <= critico_soglia
    livello = "critical" if critico else "warning"

    def scrivi():
        with open(avvisato_f, "w", encoding="utf-8") as f:
            f.write(json.dumps(stato, separators=(",", ":"), ensure_ascii=False))

    # Il primo avviso esce subito, i successivi a distanza; il passaggio a CRITICAL salta l'attesa.
    salito = livello == "critical" and stato.get("lastLevel") == "warning"
    if not primo and stato["callsSinceWarn"] < DEBOUNCE_CALLS and not salito:
        scrivi()
        return None
    stato["callsSinceWarn"] = 0
    stato["lastLevel"] = livello
    # /fine è un salvataggio, e la persona spesso continua nella stessa sessione: /clear e /inizio si propongono
    # una volta per sessione, non a ogni avviso (#3883). Avviso di consiglio, mai un ordine che scavalca le
    # preferenze della persona (#884).
    prima_rotazione = not stato.get("rotazioneProposta")
    stato["rotazioneProposta"] = True
    scrivi()
    # Con il mod rotazione (tool mcp__<plugin>__ruota, 3/11/2026) il giro è automatico: niente da proporre. Il
    # modello sa se il tool c'è; senza, vale il testo di sempre.
    # #6765 (27/11/2026): il vecchio "Altrimenti: proponi /fine" valeva anche col tool, e in sei sessioni con la
    # persona che scriveva il modello ha chiuso con "scrivi /fine" invece di ruotare.
    con_rotazione = ("Se la sessione ha il tool della rotazione (mcp__arturo__ruota, o un altro nome che finisce in "
                     "__ruota): chiudi lo step in corso, lancia /fine --rotazione, poi chiama quel tool. Ruota "
                     "anche se la persona ha scritto in questo turno o se il passo dopo chiede lei: la domanda va "
                     "nell'ultima riga, e il tool la porta nella sessione nuova. Non proporre /fine, /clear o "
                     "/inizio alla persona. Solo se il tool manca: ")
    u, r = _testo(usato) if usato is not None else "undefined", _testo(rimasto)
    if critico:
        return (f"CONTEXT CRITICAL: contesto usato al {u}%, restano {r}%. " + con_rotazione +
                "proponi /fine alla persona adesso, prima di altro lavoro.")
    return (f"CONTEXT WARNING: contesto usato al {u}%, restano {r}%. " + con_rotazione +
            "questa è la soglia della rotazione: finisci il compito in corso, poi proponi /fine "
            "alla persona in una riga, come salvataggio. Niente lavoro nuovo complesso. " +
            ("Di' una volta che /clear e /inizio aprono una sessione pulita: la persona può continuare qui dopo /fine."
             if prima_rotazione else "/clear e /inizio sono già stati proposti in questa sessione: non ripeterli."))


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        testo = avviso(data) if isinstance(data, dict) else None
    except Exception:
        return 0  # mai fermare uno strumento
    if testo:
        sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                            "additionalContext": testo}},
                                    separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
