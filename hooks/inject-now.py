#!/usr/bin/env python3
"""UserPromptSubmit: l'ora in italiano e le righe di Arturo per il prompt (#6492, B4, 23/11/2026).

Porta in Python hooks/inject-now.sh, che avviava fino a 7 processi python3 a ogni messaggio: su Windows un
processo costa 0,1-0,9 s, e il 22/11 i 3 s del tetto bastavano a fermare l'hook 56 volte. In settings.json gira
dentro `hooks/hub.py prompt`; gli script che chiama (fine-gia-chiusa, correzioni, telemetria,
estensione-skill) girano nello stesso processo con nel_processo.lancia. inject-now.sh resta come guscio per
le config vecchie e per i banchi. stdout va nel contesto della sessione.

Un solo file per la config dell'autore e per Arturo (20/10/2026): telemetria e aggiunte personali tacciono
dove mancano bin/telemetria.py e personale/.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
if QUI not in sys.path:
    sys.path.insert(0, QUI)
import nel_processo  # noqa: E402

# Il codice sta accanto a questo file (docs/strati.md).
A = os.path.dirname(QUI)
GIORNI = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")

# Il hook scatta anche sui report dei subagent e sui messaggi fra sessioni (hooks.md, UserPromptSubmit): lì il
# promemoria non serve e finiva attaccato a ogni report (19/10/2026). Stesso filtro di SYSTEM_ENVELOPE in
# memory-retrieve.py.
BUSTA = (r"\s*(?:Another Claude session sent a message:\s*)?<(task-notification|agent-message|"
         r"cross-session-message|teammate-message|bash-stdout|local-command-stdout)\b")
# Le espressioni girano sul JSON grezzo dell'hook, come le [[ =~ ]] di inject-now.sh.
RE_FINE = r'"prompt"\s*:\s*"\s*/(arturo:)?fine([^a-z0-9:-])'
# Col plugin il comando si scrive anche /arturo:fine: il nome è quello dopo il prefisso. Fino al 22/11/2026 il
# nome finiva ai due punti e valeva "arturo", e personale/fine.md restava muto (A8, revisione del 20/11).
RE_COMANDO = r'"prompt"\s*:\s*"/(arturo:)?([a-z0-9-]+)'
RE_INIZIO = r'"prompt"\s*:\s*"/(arturo:)?inizio([^a-z0-9:-])'
RE_ROTAZIONE = r'"prompt"\s*:\s*"/(arturo:)?inizio[^"]*--rotazione'

# --- Promemoria prompt-master (dal 9/9/2026) ----------------------------------
# La regola "PROMPT + BRIEF prima, su ogni richiesta di lavoro" scritta e basta non reggeva: la misura del 9/9/2026
# dava un brief in 16 sessioni su 54. Questo hook non blocca e non chiede niente: aggiunge una riga al contesto,
# dove la regola serve. Un comando /nome ha già il suo flusso e non riceve il promemoria. Dal 27/10/2026
# (segnalazione n. 17) la skill si carica una volta per sessione: ogni Skill(prompt-master) rimetteva nel contesto
# il corpo intero. Una correzione a lavoro iniziato è una riga, come nella skill (segnalazione n. 34, 29/10/2026).
# L'8/11/2026 il testo è sceso da 903 a circa 470 byte: il resto sta già nel corpo della skill. Gli stop sono
# esenti come nel corpo. La riga sulle correzioni esce solo dove c'è bin/correzioni.py: senza, il comando
# `arturo correzione` non esiste e la riga prometteva una cosa che non succede.
# Il 19/11/2026 il testo è passato da ordine a fatto, senza "REGOLA FISSA" in maiuscolo: la guida degli hook di
# Claude Code chiede fatti, perché un testo imperativo iniettato può sembrare una prompt injection.
# Per spegnerlo: svuota PROMEMORIA qui sotto, oppure togli la skill prompt-master.
PROMEMORIA = """\
BRIEF: in Arturo un lavoro, anche piccolo, si apre con PROMPT e BRIEF e la riga "Skill:". Il corpo di
prompt-master si carica col tool Skill una volta per sessione, e di nuovo dopo una compattazione.
Domande, commenti, risposte a un menu, stop e comandi di controllo non hanno brief: lì una skill si
consiglia solo se c'entra davvero. Una correzione a lavoro iniziato è una riga, "Brief corretto: ...".
"""
CORREZIONE = """\
CORREZIONI: se la persona corregge un errore, un modo di fare o una parola, la regola si registra in
una riga prima di rifare, con arturo correzione aggiungi "..." , e vale per tutta la sessione.
"""


def _casa():
    return os.environ.get("HOME") or os.path.expanduser("~")


def ora():
    """`Ora corrente: 2026-11-23 21:33 CET (lunedì)`. Il giorno è sempre in italiano, anche senza il locale
    it_IT (Windows non lo ha). Un fuso col nome lungo (Windows: "ora solare Europa occidentale") esce come
    scarto da UTC."""
    t = time.localtime()
    fuso = time.strftime("%Z", t)
    if not re.fullmatch(r"[A-Za-z]{2,5}", fuso or ""):
        fuso = time.strftime("%z", t)
    return "Ora corrente: %s %s (%s)" % (time.strftime("%Y-%m-%d %H:%M", t), fuso, GIORNI[t.tm_wday])


def leggi_entrata():
    """Lo stdin dell'hook, con un tetto di 2 secondi: uno stdin lasciato aperto non deve appendere il prompt."""
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return b""
    except (AttributeError, ValueError):
        return b""
    preso = []

    def leggi():
        try:
            preso.append(sys.stdin.buffer.read())
        except Exception:
            pass

    t = threading.Thread(target=leggi, daemon=True)
    t.start()
    t.join(2)
    return preso[0] if preso else b""


def busta(entrata):
    try:
        p = json.loads(entrata.decode("utf-8")).get("prompt", "")
    except Exception:
        return False
    return isinstance(p, str) and re.match(BUSTA, p) is not None


def script(relativo, argomenti, entrata, uscita=True, errori=False):
    """Uno script di Arturo nello stesso processo. Torna il codice; 127 se il file manca."""
    f = os.path.join(A, relativo)
    if not os.path.isfile(f):
        return 127
    codice, out, err, scaduto = nel_processo.lancia(f, argomenti, entrata)
    if uscita and out:
        sys.stdout.write(out.decode("utf-8", "replace"))
    if errori and err:
        sys.stderr.write(err.decode("utf-8", "replace"))
    sys.stdout.flush()
    return 1 if scaduto else codice


def ultracode():
    """Avviso prima di un ultracode (Computer Club N.3, 28/10/2026). Un ultracode lancia molti agenti: il 27/10
    uno ha usato circa il 5% della finestra di 5 ore in pochi minuti, e chi lo lanciava non lo sapeva. La quota la
    scrive la statusline in cache/statusline/quota.json; se manca, la riga dice solo il costo."""
    quota = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(_casa(), ".claude"),
                         "cache", "statusline", "quota.json")
    riga = ("ULTRACODE: prima di lanciarlo, di' alla persona che lancia molti agenti e costa quota "
            "(il 27/10 un lancio ha usato circa il 5% della finestra di 5 ore in pochi minuti)")
    try:
        with open(quota, encoding="utf-8") as f:
            q = json.load(f).get("cinque_ore") or {}
        pct, resets = q.get("pct"), q.get("resets")
        if isinstance(pct, int):
            riga += f"; oggi la finestra di 5 ore è al {pct}%"
            if isinstance(resets, (int, float)) and resets > time.time():
                riga += f" e si azzera alle {time.strftime('%H:%M', time.localtime(resets))}"
    except Exception:
        pass
    print(riga + ". Chiedi il sì e di' quanti agenti partono.")


def main():
    print(ora())
    entrata = leggi_entrata()
    if busta(entrata):
        return 0
    grezzo = entrata.decode("utf-8", "replace")

    # --- Un /fine su una sessione già chiusa (22/11/2026, #6274, segnalazioni n. 79, 87 e 93) -----
    # Un mod della persona rilanciava /fine ogni 45 minuti su una sessione ferma: ogni giro costava quota per
    # niente. Se la sessione ha già l'handoff e dopo l'ultimo /fine non è arrivato niente, fine-gia-chiusa.py
    # esce 2 e Claude Code scarta il prompt senza chiamare il modello. Ogni altra uscita lascia partire il /fine.
    if re.search(RE_FINE, grezzo) and script("bin/fine-gia-chiusa.py", [], entrata, errori=True) == 2:
        return 2

    # --- Correzioni della sessione (Computer Club N.3, [0:01:09]; #4099, 4/11/2026) ----------
    # "Tre volte di fila ho fatto un errore, tu me l'hai fatto notare tutte e tre le volte": una correzione
    # scritta con `arturo correzione aggiungi` torna qui a ogni messaggio, anche dopo una compattazione.
    # Nessuna correzione, nessuna riga. Cosa è una correzione lo decide Claude (promemoria qui sotto).
    script("bin/correzioni.py", ["blocco"], entrata)

    if re.search("ultracode", grezzo, re.IGNORECASE):
        ultracode()

    # --- Telemetria: quale comando di Arturo viene usato -----------------------------
    # Solo il nome di un comando che esiste, mai il testo del prompt. Un comando della persona esce come `altro`
    # (bin/telemetria.py, COMANDI), dal 24/10/2026.
    comando = ""
    m = re.search(RE_COMANDO, grezzo)
    if m:
        comando = m.group(2)
        casa = os.path.join(_casa(), ".claude")
        # Nel plugin un comando è una skill. Un comando di Arturo o dell'Orsa: telemetria.py manda il nome solo
        # se è di Arturo, se no `altro`.
        if any(os.path.isfile(os.path.join(d, *p)) for d in (A, casa)
               for p in (("commands", comando + ".md"), ("skills", comando, "SKILL.md"))):
            script("bin/telemetria.py", ["registra", "comando", comando], b"", uscita=False)
        # Chi apre /inizio (M7 della memoria, 15/11/2026): la persona, o il mod rotazione con "-- --rotazione".
        # Senza, la quota di sessioni aperte con /inizio si gonfia a ogni rotazione. Anche come /arturo:inizio.
        if re.search(RE_INIZIO, grezzo):
            origine = "rotazione" if re.search(RE_ROTAZIONE, grezzo) else "persona"
            script("bin/telemetria.py", ["registra", "inizio", origine], b"", uscita=False)
        # --- Aggiunte personali al comando ------------------------------------------------
        # Le aggiunte della persona a un comando di Arturo stanno in ~/.claude/personale/<comando>.md, fuori da
        # git: gli aggiornamenti non le toccano e non vanno in conflitto (arturo personale).
        if os.path.isfile(os.path.join(casa, "personale", comando + ".md")):
            print(f"PERSONALE: /{comando} ha aggiunte della persona in ~/.claude/personale/{comando}.md. Leggile "
                  "prima di cominciare e applicale insieme al comando, dove non contraddicono i Freni.")
        # --- La skill della persona in uso (21/11/2026, #6277) -----------------------------
        # Una skill scritta a mano con /<nome> non passa dal tool Skill: estensione-skill.py --prompt segna la
        # skill nella sessione (le correzioni prendono il suo nome) e stampa la sua lista "Finito quando".
        # Su un comando di Arturo o su una skill senza la lista non stampa niente.
        script("hooks/estensione-skill.py", ["--prompt"], entrata)

    if not comando:
        sys.stdout.write(PROMEMORIA)
        if os.path.isfile(os.path.join(A, "bin", "correzioni.py")):
            sys.stdout.write(CORREZIONE)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
