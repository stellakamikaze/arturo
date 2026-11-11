#!/usr/bin/env python3
"""HZ01-HZ55: Herdr, la finestra di Arturo (8/11/2026, ramo di prova `herdr`).

/setup installa Herdr (herdr.dev) con `shared/volta-celeste/installa-herdr.sh`, e l'hook `hooks/herdr-stato.sh`
dice a Herdr se Claude lavora, aspetta la persona o ha finito (OSC 7501). Il banco prova l'installazione
in una casa finta con un installer finto, senza rete e senza Herdr vero.

HZ01 primo giro: Herdr scaricato, layout, tema e mod copiati, arturo.json punta al bin di Arturo,
     shared.json apre il layout Arturo senza il benvenuto di Herdr, telemetria di Herdr spenta.
HZ02 secondo giro su una casa già usata: un tasto della persona resta suo, la sua telemetria e il suo
     shared.json restano com'erano, e il giro dopo non cambia niente.
HZ03 Mac Intel e Linux: esce 0 con `HERDR NO` e non scrive niente.
HZ04 hook: fuori da Herdr non scrive; dentro Herdr scrive `ESC]7501;state=<s>:app=claude-code ESC\\`
     sul terminale di controllo.
HZ05 settings.json registra l'hook sugli otto eventi con lo stato giusto, e la telemetria della deriva
     lo conosce.
HZ06 /setup porta a shared/setup-herdr.md, che lancia installa-herdr.sh. Sul Mac senza l'identità "Arturo firma
     locale" l'installatore propone firma-locale.sh con la riga HERDR FIRMA, e il passo dice cosa farne (#5020).
HZ07 il mod: ogni modulo importato esiste, ogni parte nominata dal layout esiste in main.js.
HZ08 chi ha già Arturo (setup fatto) e non ha Herdr riceve all'avvio l'invito `HERDR:` una volta sola;
     chi non ha finito /setup non lo riceve.
HZ09 i suggerimenti della finestra puntano a cose che esistono: ogni comando slash a un file di
     commands/, "Trova i miei progetti" a trova-progetti.md, che usa la parte 2c del ritratto e i
     sottocomandi veri di ritratto.py.
HZ10 "Da dove partire" in cima al pannello Da fare (partenza.js, con node): il todo di da_dove col motivo,
     poi al massimo tre passi della catena dopo di lui, senza i todo segnati fatti; niente scheda senza
     da_dove o col todo già fatto. Senza node il caso si salta.
HZ11 "La settimana" (settimana.js, con node): ogni progetto in una lista sola, la più urgente (scaduti,
     poi aspettano te, poi fermi da più di sette giorni), ognuna dal caso peggiore, col motivo che dice
     tutti i fatti; un progetto senza niente da guardare resta fuori. La settimana ISO regge il cambio
     d'anno. La finestra è una parte di main.js e il piede la apre. Senza node il caso si salta.
HZ12 le azioni sui todo del pannello Da fare (azioni.js, con node): ogni gesto del menu e "Aggiungi"
     girano sulla CLI vera in una casa finta e lasciano il todo come promettono (chi, quando, fermo col
     motivo, ripreso, nota, scartato, fatto); il menu non propone il chi e il quando che il todo ha già,
     né "Fermo" a un todo fermo; un titolo vuoto non aggiunge niente. Lavoraci (#4994) segna il todo
     in corso prima di aprire Claude, non riscrive un todo già in corso, e il menu lo rimette da fare.
     Menu e finestra sono parti di main.js. Senza node il caso si salta.
HZ13 Arturo.app (arturo-app.sh, solo macOS, #5002): da un Herdr.app finto nasce Arturo.app col nome, l'id e
     l'icona di Arturo e la firma locale valida; il secondo giro non la tocca; dopo un aggiornamento che le
     ridà il nome di Herdr torna Arturo alla versione nuova; un Herdr.app più nuovo la rifà; il LaunchAgent
     guarda i due Info.plist e lancia la copia dello script fuori da Documenti (#5087). L'installatore la chiama solo sul Mac e solo senza installer finto. Fuori da
     macOS resta solo il controllo sull'installatore.
HZ14 le note sulla finestra (⌘⇧N, nota.js con node): la nota porta testo, punto, misura della finestra e
     progetto; diventa una cosa da fare di Claude per oggi, con punto e cartella nelle note, sulla CLI vera
     in una casa finta; vuota non parte; senza progetto resta nella cartella; note_progetto vince sul
     progetto aperto. barra.js fa lo screenshot prima del velo, keys.json lega cmd-shift-n, main.js ha la
     parte, l'installatore tiene note_progetto in arturo.json. Senza node la parte con node si salta.
HZ15 ogni cartella o file che la parte Herdr scrive in ~/.claude/data/ (mod, hook herdr-stato.sh, invito di
     session-start.sh) è escluso dal .gitignore di Arturo (#5018): uno screenshot delle note fermava
     l'aggiornamento automatico o finiva in un commit di /fine.
HZ16 servizi-gui.sh (9/11/2026): herdr-core da LaunchAgent senza KeepAlive (si passa da solo a
     launchd ed esce 0); il gestore delle sessioni non va in launchd senza --launchd (senza l'accesso
     a Documenti le sessioni morirebbero all'avvio), con --launchd sì e con KeepAlive; plist validi.
HZ17 Volta Celeste, i gruppi (sessioni.js con node, #5068): per macchina nell'ordine del file con la nota
     della macchina giù; per progetto con la nota sull'ultimo gruppo; dentro il gruppo la più recente,
     poi l'alfabeto (HZ51); i nomi automatici ("claudecode-ca") lasciano il posto alla risposta.
HZ18 Volta Celeste, il clic (sessioni.js con node): una sessione in background si aggancia con l'argv
     del file (locale o ssh), un'interattiva ferma passa da porta-volta, una al lavoro, che aspetta o di
     una macchina giù no, col motivo; la scheda già aperta si riconosce anche dall'argv avvolto da zsh
     da un ciclo ssh dentro sh -c e da pwsh -Command su Windows, senza prendere un id che ne contiene un altro.
HZ19 Volta Celeste nella barra: barra.js monta volta.js e accetta il comando volta-<id>, volta.js
     lancia teletrasporto.py volta --scrivi e porta-volta, e senza teletrasporto.py non mostra niente.
HZ20 Volta Celeste su Windows (9/11/2026): volta.js lancia volta_sonda.py e teletrasporto.py col Python di arturo.json
     (quello che installa-herdr.sh ha trovato), mai con un Python scritto a mano.
HZ21 installa-herdr.sh su Windows scrive layout, mod e arturo.json in ~/.config/herdr-app e la shell
     di herdr-core in ~/.config/herdr-core/config.toml, dove Herdr 0.1.14 li legge; niente in %APPDATA%.
HZ22 i tasti per sistema: su Windows keys-ctrl.json (Ctrl+Shift+A apre un progetto, Ctrl+Shift+M la nota)
     e nessun cmd, che lì è il tasto Windows; sui Mac keys.json con cmd-o. Su Windows nessun tasto di
     Arturo è già di Herdr: col keys.json che Herdr scrive al primo avvio, tutti i tasti di Arturo
     entrano e nessuno resta "lasciato com'era" (Ctrl+Shift+E divideva il riquadro in basso, #5162).
HZ23 l'installatore prende il primo Python che risponde, non il primo che esiste: con un python3 che esce
     9009 come lo stub dello Store, arturo.json usa python (#5079).
HZ24 barra di stato e guida scrivono i tasti da tasti() di comuni.js, mai ⌘ a mano; volta.js avvisa se
     il comando do porta l'id di una sessione che non è nell'elenco (#5078).
HZ25 nelle finestre di dialogo (Cosa posso chiedere, Apri un progetto, La settimana, menu dei todo)
     l'azione parte prima che la finestra si chiuda: chiusa, la finestra ferma il suo codice al primo
     await, e i pulsanti di Cosa posso chiedere non facevano niente (9/11/2026).
HZ26 su cosa è una nota (#5117 passo 1, nota.js con node): regione() rifà i rettangoli di
     layouts/arturo.json con le misure prese nell'istanza di prova (finestra 1440x900, barra 292, lavoro
     1147) e dice la parte sotto il punto, anche con barra e pannello allargati, col pannello nascosto e col
     benvenuto; con misure vecchie o assenti dà null. main.js fa riportare la misura alle parti del layout,
     notaui.js mette la parte e il terminale in nota.json. Senza node la parte con node si salta.
HZ27 il velo delle note (#5117 passo 2, nota.js con node): nota.json versione 2 con id, numero, tipo, stato,
     filo e todo; una nota versione 1 si legge come aperta; i segni delle note aperte del progetto hanno
     numeri unici e si riportano in scala sulla finestra; lo script LEGGI_NOTE legge la cartella col
     Python; la CLI vera dà l'id del todo con --json, e le note del todo portano `arturo note mostra <id>`.
     Senza node la parte con node si salta.
HZ28 l'elenco delle note (#5117 passo 3, nota.js con node): prima le aperte coi numeri dei segni, con
     "tutte" anche le chiuse dalla più recente e senza numero; ultima risposta di Claude, età in parole,
     conteggio per progetto; una risposta nuova di Claude si annuncia, ma non alla prima lettura. ⌘⇧E sui
     Mac e Ctrl+Shift+I altrove aprono la parte `note`; la barra di stato guarda la cartella delle note e
     il suo conteggio apre l'elenco; una riga aperta porta al velo con arturo.nota-<id>.
HZ29 il giro di Claude con `arturo note` (#5117 passo 4, CLI vera in una casa finta): elenco coi numeri dei
     segni (una nota versione 1 prende il primo libero), --md come brief, mostra col ritaglio attorno al
     punto in scala sullo scatto al doppio, prendi, rispondi e risolvi che portano il todo in corso, nota e
     fatto; una nota chiusa non si richiude, scarta chiude col motivo, un percorso al posto dell'id esce 2.
HZ30 scrittura concorrente: se il velo scrive fra la lettura e la scrittura della CLI, la CLI rilegge e
     rifà la sua modifica, e nel filo restano tutte e due le risposte.
HZ31 Rispondi, Risolta e Scarta del velo (#5117 passo 5): notaui.js li manda ad `arturo note` con --chi
     federico (gestoNota di dati.js), senza scrivere nota.json da sé; con la CLI vera in una casa finta la
     risposta di Federico arriva una volta sul todo, Risolta senza testo chiude nota e todo, Scarta col
     motivo scarta il todo, e una nota già chiusa da Claude esce 2 col motivo.
HZ32 il formato in due copie (#5117 passo 6): TIPI, TIPO_PREDEFINITO, STATI, APERTE e VUOTO di nota.js
     (node) e di bin/note_finestra.py dicono lo stesso; l'aiuto di arturo note e docs/volta-celeste.md
     spiegano --chi e --json, e la guida parla a chi usa Arturo.
HZ33 "Trova i miei progetti" su ogni macchina (#5111, con node): il pulsante manda Claude al file di
     istruzioni nella cartella di Arturo, presa da arturo.json o, in un arturo.json di prima, dal bin
     (anche con le barre di Windows), mai da ~/.claude scritto a mano. Senza node il caso si salta.
HZ34 la sonda di Volta per tutti (#5172, volta_sonda.py con un hc finto): le macchine vengono da
     hc machine ls e si leggono con hc exec --on; questa macchina per prima come "qui"; Windows senza
     python3 ripiega su python; una macchina senza Python ma con Claude dà l'elenco nudo; senza Claude
     (o senza nessuno dei due) resta fuori; una che non risponde compare, con le righe vecchie, solo se
     Claude ci era già stato visto; aggancio locale e via ssh col percorso di claude della macchina.
     volta.js lancia volta_sonda.py del mod e lascia porta-volta a teletrasporto.py.
HZ35 la nascita in background (#5172 passo 2, volta-claude.sh con un claude finto): in un terminale vero
     claude e claude "<prompt>" nascono con --bg e si aprono con claude attach <id>; CLAUDE_QUI=1, i
     sottocomandi, -p, --resume senza id, i terminali di Herdr, le sessioni dentro Claude e chi non ha un
     terminale passano a claude com'è; se --bg è rifiutato la sessione si apre qui e lo dice. Prima di
     --bg accende il servizio di Claude con la sonda del mod, ma non da ssh; se il servizio non parte
     lo dice e la sessione nasce lo stesso (#5215).
HZ36 il blocco della nascita (nascita.sh e installa-herdr.sh): metti lo scrive una volta sola anche
     rilanciato, togli lascia il file com'era, stato vede la funzione claude della persona fuori dal
     blocco, e in zsh e bash il blocco definisce claude solo se la persona non ne ha già una.
     L'installatore copia i file e propone soltanto; metti della copia installata accende, no spegne e
     ricorda il no (l'installatore non ripropone), metti dopo un no lo dimentica.
HZ37 la nascita in PowerShell (#5172 passo 3): metti scrive il blocco nei profili di PowerShell (anche in
     una cartella che non c'è), solo ASCII, una volta sola; togli lascia il profilo com'era anche con le
     righe di Windows; un profilo UTF-16 resta com'è; stato vede la funzione claude della persona e la
     policy Restricted; l'installatore di Windows copia volta-claude.ps1 e dice della policy.
HZ38 dove c'è PowerShell (Windows): volta-claude.ps1 fa nascere in background e aggancia, lascia qui via di fuga,
     sottocomandi e --resume senza id, ripiega se --bg è rifiutato; il blocco definisce claude solo se
     la persona non ne ha già una.
HZ39 la nascita su un'altra macchina (#5172 passo 4, volta_sonda.py nasci con un hc finto, dati.js con
     node): la sessione nasce con hc exec --on, col prompt e il progetto intatti, e torna l'aggancio via
     ssh; un Python partito non si ripete (mai due sessioni), python3 assente ripiega su python; macchina
     spenta o sconosciuta e --bg rifiutato danno un errore leggibile; su questa macchina parte nella base
     dell'arturo.json di HERDR_APP_HOME. In Volta Nuova richiesta e Apri un progetto nascono sulla macchina
     di "Nasce su" (anche dal benvenuto, che la mostra), una macchina che Volta non elenca torna qui, il
     percorso di volta_sonda.py è uno, i suggerimenti restano qui, e Lavoraci su uno spazio nato altrove
     scrive nella scheda che lo aggancia. Anche qui una sessione nasce in background e si aggancia dalla
     home (#5072); lo stato di una scheda agganciata viene dall'ultima lettura di Volta, quello di Herdr
     vince, Lavoraci non scrive in chi aspetta, e un suggerimento scrive nella sessione agganciata aperta.

HZ40 i gesti di Volta su una sessione (#5172 passo 4): volta_sonda.py azione lancia claude logs, stop,
     respawn e rm qui o con hc exec --on, rifiuta un verbo o un id strani senza lanciare niente, e
     l'anteprima rifà lo schermo di claude logs (parole spaziate dai movimenti del cursore). sessioni.js
     (node): Anteprima su ogni sessione in background, Ferma solo se è viva, Riavvia dopo un errore,
     Elimina con conferma solo se è ferma; avviso solo per chi passa a "ti aspetta" dopo la prima
     lettura; stato per id corto senza le righe vecchie. volta.js usa azioni(), nuoveInAttesa() e
     statiCorti(), e dati.js passa da volta_sonda.py azione.
HZ41 il servizio di Claude prima della nascita (#5208, volta_sonda.py servizio con un hc finto e un claude
     finto): un servizio che risponde non si tocca; Windows senza attività lo accende con hc run in un
     terminale di herdr-core, e uno che dopo non risponde dà errore; nasci accende il servizio prima della
     sessione e senza servizio non fa nascere niente; su questa macchina il servizio spento nasce
     staccato (una sessione sua) nella home. Riavvia passa dal servizio come nasci, Ferma no (#5215).
HZ42 le attese della nascita (#5214): Volta (dati.js nasciSu) aspetta più della somma dei tetti di
     volta_sonda.py, con 30 s di margine; il servizio che non risponde si ferma al suo tetto, anche
     dopo hc run. Riavvia aspetta servizio più azione più il margine, gli altri gesti azione più il
     margine (#5215).
HZ43 il servizio fisso con un nome solo (#5213): l'etichetta del LaunchAgent di servizi-gui.sh e il nome
     dell'attività di servizio-claude.ps1 sono gli stessi in installa-herdr.sh e in volta_sonda.py; ogni
     riga HERDR che l'installazione stampa ha la sua istruzione in shared/setup-herdr.md.
HZ44 le sessioni chiuse nell'elenco di Volta (#5203): la sonda chiede claude agents --all, così una
     sessione fermata (un clic la riapre) e una in errore (Riavvia) restano a vista; delle chiuse tiene
     le nate negli ultimi CHIUSE_GIORNI giorni; un Claude senza --all dà l'elenco di prima. I comandi
     arturo.volta-altro-<id> e arturo.volta-gesto-<verbo>-<id> aprono "Altro" e premono un suo bottone,
     e la barra li legge prima di arturo.volta-<id>.
HZ45 il titolo delle sessioni (hooks/titolo-sessione.py con un claude finto): la prima richiesta dà il
     compito di /inizio senza chiamare il modello; a fine turno il modello è chiamato una volta, senza
     strumenti né hook, e il titolo va in cache/titolo/<sessione>.json; un secondo fine turno entro
     l'intervallo non chiama; una risposta di più righe o troppo lunga lascia il titolo di prima; spento
     con ARTURO_TITOLI=0 e dentro la chiamata figlia non chiama; un claude che fallisce lascia exit 0.
     La sonda porta il campo titolo, sessioni.js lo mette davanti al nome, Volta si apre per progetto,
     e settings.json registra l'hook asincrono su UserPromptSubmit e Stop.
HZ46 l'Anteprima di una sessione (#5240): la sonda taglia l'ultima risposta a una parola intera, col segno
     "…", e porta l'ultima azione; il documento di Volta non la taglia una seconda volta. sessioni.js
     (node): anteprima() dà "Ultima risposta" con le righe senza i segni del markdown e i nomi col
     trattino basso interi, poi "Ultima azione"; null senza trascrizione. volta.js mostra quei blocchi a
     capo dalla riga già letta, senza lanciare claude logs, che resta per chi non ha trascrizione.
HZ47 i gesti di "Altro" si vedono anche su una sessione in fondo all'elenco (#5241): volta.js li disegna
     in pannello(), sotto l'elenco e fuori dalla parte che scorre (alta al massimo 360 px), col titolo
     della sessione e "Chiudi"; la riga non li porta più, e l'avviso di un gesto sta nel pannello.
HZ48 una sessione in background si aggancia anche dopo /clear (11/11/2026): righe() di volta_sonda.py
     usa l'id del lavoro di claude agents per attach e gesti, non l'inizio del sessionId, che dopo
     /clear o una rotazione cambia ("No job matching"); un'interattiva tiene l'inizio del sessionId.
HZ49 una X in hover chiude per sempre una sessione ferma (11/11/2026): volta.js la mette nella riga solo
     se azioni() dà rm, visibile col puntatore sopra la riga (on_hover) o mentre chiede conferma, e il
     clic passa da fare(), che al primo clic chiede "Sì, elimina".
HZ50 le note si trovano a vista (11/11/2026): il piede della barra ha la voce "Note", che apre l'elenco
     e scrive accanto i tasti della nota nuova e dell'elenco; il layout arturo dà al piede 190 px, cinque voci.
HZ51 Volta Celeste, l'ordine è l'ultima interazione (11/11/2026): dentro un gruppo la sessione toccata per
     ultima sta in cima, qualunque stato abbia (una ferma di un minuto fa sta sopra una che aspetta da
     ieri); viene per primo il gruppo con la più recente, per progetto e per macchina, e "Senza progetto"
     non va in fondo d'ufficio. Senza trascrizione la sonda mette in "ultimo" la nascita (startedAt), così
     una sessione appena nata sta in cima.
HZ52 una sessione aperta mostra Claude già avviato (#5290, dati.js apriSessione con herdr finto): la scheda
     si ritrova per etichetta (arturo.sessione) e per argv, mai per nome; se dentro gira ancora Claude va
     davanti senza comandi; se è rimasta la shell nuda (primo piano = la shell del terminale, argv cambiato)
     il servizio si accende e claude attach riparte lì con hc send; se manca nasce una scheda nuova, anche
     accanto a una con lo stesso nome. Una sessione in errore passa da --riavvia. La veglia guarda dopo
     qualche secondo: se Claude è uscito riavvia una volta e rilancia, se esce ancora lo dice. Una shell
     che si sta ancora avviando non è nuda. Una sessione appena nata non ripassa dal servizio.
HZ53 il verbo apri della sonda e la scheda nuova (#5290): apri accende il servizio prima e senza servizio
     dà errore; con --riavvia lancia claude respawn dopo il servizio; un id strano non parte. ⌘T e
     Ctrl+Shift+T sono arturo.volta-nuova: l'installazione si prende il tasto solo se faceva tab.new di
     Herdr, e lascia quello che la persona ha legato ad altro. barra.js porta il comando a nuovaScheda(),
     che fa nascere una sessione senza prompt nel progetto dello spazio aperto (nessuno da "Volta").
HZ54 il menu del tasto destro su una sessione (#5291): menu() di sessioni.js dà Apri, Chiudi, Duplica, Fork
     e i gesti di "Altro" senza Ferma; un'interattiva non ha Chiudi, una riga vecchia non ha menu. Duplica e
     Fork (dati.js copiaSessione, herdr finto) nascono sulla macchina della sessione, nella sua cartella e
     nel suo progetto, col sessionId per il fork e il nome "<titolo> (fork)"; un errore torna alla riga
     senza avviso. Chiudi chiude la scheda intera se è sola, altrimenti il solo terminale, poi ferma.
     volta.js apre il menu col tasto destro, il menu manda il gesto come comando prima di chiudersi.
HZ55 i verbi duplica e fork della sonda (#5291): passano da nasci, col servizio acceso prima; fork porta
     --resume <sessionId> --fork-session e parte dalla cartella della sessione, e senza cartella dà errore
     senza lanciare claude; duplica senza cartella ripiega sulla base. Un id strano non parte.

Con --avvelena le copie rotte del repository devono far rosso il caso che le sorveglia.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ("HZ01", "HZ02", "HZ03", "HZ04", "HZ05", "HZ06", "HZ07", "HZ08", "HZ09", "HZ10", "HZ11", "HZ12", "HZ13", "HZ14", "HZ15", "HZ16", "HZ17", "HZ18", "HZ19", "HZ20", "HZ21", "HZ22", "HZ23", "HZ24", "HZ25", "HZ26", "HZ27", "HZ28", "HZ29", "HZ30", "HZ31", "HZ32", "HZ33", "HZ34", "HZ35", "HZ36", "HZ37", "HZ38", "HZ39", "HZ40", "HZ41", "HZ42", "HZ43", "HZ44", "HZ45", "HZ46", "HZ47", "HZ48", "HZ49", "HZ50", "HZ51", "HZ52", "HZ53", "HZ54", "HZ55")
INSTALLA = Path("shared/volta-celeste/installa-herdr.sh")
HOOK = Path("hooks/herdr-stato.sh")
ATTESI = {  # evento: (matcher o None, stato)
    "SessionStart": ("", "idle"),
    "UserPromptSubmit": (None, "working"),
    "PermissionRequest": (None, "blocked"),
    "Notification": ("permission_prompt|elicitation_dialog", "blocked"),
    "PreToolUse": ("AskUserQuestion", "blocked"),
    "PostToolUse": (None, "working"),
    "Stop": (None, "done"),
    "SessionEnd": ("", "idle"),
}


def installa(repo: Path, casa: Path, sistema: str = "mac-arm", extra: dict | None = None) -> subprocess.CompletedProcess:
    app = casa / "app"
    segno = casa / "scaricato"
    finto = casa / "installer-finto.sh"
    finto.write_text(f"#!/bin/sh\necho scaricato >> '{segno}'\n", encoding="utf-8")
    env = {
        **os.environ,
        "HOME": str(casa / "home"),
        "USERPROFILE": str(casa / "home"),
        "HERDR_APP_HOME": str(app),
        "PROJECTS_BASE": str(casa / "progetti"),
        "ARTURO_HERDR_INSTALLER": str(finto),
        "ARTURO_HERDR_SISTEMA": sistema,
        "ARTURO_HERDR_NON_APRIRE": "1",
        "ARTURO_HERDR_VERSIONE": "0.1.13",
        **(extra or {}),
    }
    (casa / "home").mkdir(parents=True, exist_ok=True)
    return subprocess.run(["sh", str(repo / INSTALLA)], env=env, capture_output=True, text=True, timeout=60)


def leggi(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def hz01(repo: Path, casa: Path) -> str | None:
    r = installa(repo, casa)
    app = casa / "app"
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    if not (casa / "scaricato").exists():
        return "l'installer di Herdr non è partito"
    for rel in ("layouts/arturo.json", "layouts/arturo.svg", "themes/arturo.json", "mods/arturo/main.js", "mods/arturo/dati.js", "mods/arturo/fonts"):
        if not (app / rel).exists():
            return f"manca {rel}"
    conf = leggi(app / "arturo.json")
    if not conf["arturo"][-1].endswith("bin/arturo") or Path(conf["arturo"][-1]).resolve() != (repo / "bin/arturo").resolve():
        return f"arturo.json non punta al bin di Arturo: {conf['arturo']}"
    # su Windows installa-herdr.sh scrive C:/... con le barre dritte (cygpath -m): si confrontano i percorsi
    if Path(conf["base"]).resolve() != (casa / "progetti").resolve():
        return f"arturo.json ignora PROJECTS_BASE: {conf['base']}"
    if not conf.get("radice") or Path(conf["radice"]).resolve() != repo.resolve():
        return f"arturo.json non dice la cartella di Arturo: {conf.get('radice')}"
    sh = leggi(app / "shared.json")
    if sh.get("layout") != "arturo" or sh.get("frame.welcomed") != "skipped":
        return f"il primo avvio non apre il layout Arturo: {sh}"
    if leggi(app / "update-notes.json").get("presented") != ["0.1.13"]:
        return "le note di versione di Herdr si aprirebbero al primo avvio"
    if leggi(app / "settings.json").get("telemetry") is not False:
        return "la telemetria di Herdr non è spenta"
    return None


def hz02(repo: Path, casa: Path) -> str | None:
    app = casa / "app"
    app.mkdir(parents=True)
    (app / "keys.json").write_text('{"global": {"cmd-o": "tab.new"}}', encoding="utf-8")
    (app / "settings.json").write_text('{"telemetry": true, "zoom": 1.2}', encoding="utf-8")
    (app / "shared.json").write_text('{"layout": "main"}', encoding="utf-8")
    r = installa(repo, casa)
    if r.returncode != 0:
        return f"installazione fallita: {r.stderr[-200:]}"
    if leggi(app / "keys.json")["global"].get("cmd-o") != "tab.new":
        return "un tasto della persona è stato sovrascritto"
    if "agent.next" not in leggi(app / "keys.json")["global"].values():
        return "i tasti di Arturo non sono stati aggiunti"
    imp = leggi(app / "settings.json")
    if imp.get("telemetry") is not True or imp.get("zoom") != 1.2:
        return f"le impostazioni della persona sono cambiate: {imp}"
    if leggi(app / "shared.json") != {"layout": "main"}:
        return "lo stato di Herdr della persona è stato riscritto"
    prima = {p.name: p.read_bytes() for p in app.glob("*.json")}
    installa(repo, casa)
    dopo = {p.name: p.read_bytes() for p in app.glob("*.json")}
    if prima != dopo:
        return f"il secondo giro cambia {sorted(k for k in dopo if prima.get(k) != dopo[k])}"
    return None


def hz03(repo: Path, casa: Path) -> str | None:
    for sistema in ("mac-intel", "linux"):
        c = casa / sistema
        c.mkdir()
        r = installa(repo, c, sistema)
        if r.returncode != 0 or "HERDR NO" not in r.stdout:
            return f"{sistema}: rc={r.returncode} {r.stdout[-120:]}"
        if (c / "app").exists() or (c / "scaricato").exists():
            return f"{sistema}: ha scritto o scaricato qualcosa"
    return None


def nel_terminale(repo: Path, env: dict) -> bytes:
    """L'hook lanciato con un terminale di controllo finto: restituisce quello che vi ha scritto.
    Il lato madre si legge mentre l'hook gira: su macOS una scrittura sul terminale aspetta chi legge."""
    import pty
    import select
    madre, figlia = pty.openpty()
    codice = (
        "import os,fcntl,termios,subprocess,sys;"
        "os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0);"
        f"subprocess.run(['sh',{str(repo / HOOK)!r},'working'],input=b'{{}}',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)"
    )
    p = subprocess.Popen([sys.executable, "-c", codice], stdin=figlia, stdout=figlia, stderr=subprocess.PIPE, env=env, close_fds=True)
    os.close(figlia)
    letto = b""
    fine = __import__("time").time() + 20
    while __import__("time").time() < fine:
        pronti = select.select([madre], [], [], 0.2)[0]
        if pronti:
            try:
                pezzo = os.read(madre, 4096)
            except OSError:
                break
            if not pezzo:
                break
            letto += pezzo
        elif p.poll() is not None:
            break
    p.kill() if p.poll() is None else None
    p.wait(timeout=5)
    os.close(madre)
    return letto


def hz04(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # niente pty su Windows: il caso vale su macOS e Linux
    fuori = {k: v for k, v in os.environ.items() if k != "HC_TERMINAL_ID"}
    if b"7501" in nel_terminale(repo, fuori):
        return "fuori da Herdr l'hook scrive sul terminale"
    dentro = {**fuori, "HC_TERMINAL_ID": "t1"}
    letto = nel_terminale(repo, dentro)
    if b"\x1b]7501;state=working:app=claude-code\x1b\\" not in letto:
        return f"dentro Herdr l'hook non scrive lo stato: {letto[:80]!r}"
    return None


def hz05(repo: Path, casa: Path) -> str | None:
    hooks = leggi(repo / "settings.json")["hooks"]
    for evento, (matcher, stato) in ATTESI.items():
        trovati = [g for g in hooks.get(evento, []) for h in g.get("hooks", []) if "herdr-stato.sh" in h.get("command", "")]
        if not trovati:
            return f"{evento} senza herdr-stato.sh"
        comandi = [h["command"] for g in trovati for h in g["hooks"] if "herdr-stato.sh" in h["command"]]
        if not any(c.endswith(f" {stato}") for c in comandi):
            return f"{evento} non manda {stato}: {comandi}"
        if matcher is not None and not any(g.get("matcher", "") == matcher for g in trovati):
            return f"{evento} col matcher sbagliato"
    logica = (repo / "server/logica.js").read_text(encoding="utf-8")
    elenco = re.search(r"DERIVA_HOOK = \[(.*?)\];", logica, re.S)
    if not elenco or '"herdr-stato.sh"' not in elenco.group(1):
        return "DERIVA_HOOK non conosce herdr-stato.sh"
    return None


def hz06(repo: Path, casa: Path) -> str | None:
    setup = (repo / "commands/setup.md").read_text(encoding="utf-8")
    if "shared/setup-herdr.md" not in setup:
        return "/setup non porta a shared/setup-herdr.md"
    passo = (repo / "shared/setup-herdr.md").read_text(encoding="utf-8")
    if "shared/volta-celeste/installa-herdr.sh" not in passo:
        return "setup-herdr.md non lancia installa-herdr.sh"
    for parola in ("HERDR OK", "HERDR NO", "HERDR ERRORE"):
        if parola not in passo or (parola != "HERDR ERRORE" and parola not in (repo / INSTALLA).read_text(encoding="utf-8")):
            return f"l'esito {parola} non torna fra passo e script"
    # #5020: la firma locale si propone con una riga e il comando, e lo script è eseguibile come gli altri.
    if "HERDR FIRMA" not in passo:
        return "setup-herdr.md non dice cosa fare con la riga HERDR FIRMA"
    if not os.access(repo / "shared/volta-celeste/firma-locale.sh", os.X_OK):
        return "firma-locale.sh non è eseguibile"
    for firma, attesa in (("assente", True), ("presente", False)):
        with tempfile.TemporaryDirectory() as d:
            r = installa(repo, Path(d), extra={"ARTURO_HERDR_FIRMA": firma})
        riga = next((x for x in r.stdout.splitlines() if x.startswith("HERDR FIRMA")), "")
        if attesa and "firma-locale.sh" not in riga:
            return "senza la firma locale l'installatore non propone firma-locale.sh"
        if not attesa and riga:
            return "con la firma locale già fatta l'installatore la propone lo stesso"
    with tempfile.TemporaryDirectory() as d:
        if "HERDR FIRMA" in installa(repo, Path(d), "windows", {"ARTURO_HERDR_FIRMA": "assente"}).stdout:
            return "l'installatore propone la firma locale fuori dal Mac"
    return None


def hz07(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    for js in mod.glob("*.js"):
        for rel in re.findall(r'from "\./([^"]+)"', js.read_text(encoding="utf-8")):
            if not (mod / rel).exists():
                return f"{js.name} importa {rel}, che non c'è"
    main = (mod / "main.js").read_text(encoding="utf-8")
    parti = set(re.findall(r"(\w+): \w+", re.search(r"const PARTI = \{(.*?)\};", main).group(1)))
    layout = (repo / "shared/volta-celeste/layouts/arturo.json").read_text(encoding="utf-8")
    # [^"]+ e non \w+: un nome col trattino o col punto non deve sparire dal controllo
    usate = set(re.findall(r'"parte": "([^"]+)"', layout)) | set(re.findall(r'parte: "([^"]+)"'," ".join(p.read_text(encoding="utf-8") for p in mod.glob("*.js"))))
    if usate - parti:
        return f"parti senza codice: {sorted(usate - parti)}"
    return None


def hz08(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # sysctl e i percorsi del Mac: il caso vale fuori da Windows
    if sys.platform == "darwin":
        r = subprocess.run(["sysctl", "-n", "hw.optional.arm64"], capture_output=True, text=True)
        if r.stdout.strip() != "1":
            return None
    elif not sys.platform.startswith("linux"):
        return None
    if sys.platform.startswith("linux"):
        return None  # su Linux l'invito non parte: niente da provare qui
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
           "ARTURO_BANCHI_AVVIO": "0", "ARTURO_AGGIORNAMENTI": "manuali"}
    def avvio() -> str:
        r = subprocess.run(["bash", str(repo / "hooks/session-start.sh")], env=env, capture_output=True, text=True,
                           timeout=60, stdin=subprocess.DEVNULL)
        return r.stdout
    (casa / ".claude/data").mkdir(parents=True)
    if "HERDR:" in avvio():
        return "invito a chi non ha finito /setup"
    (casa / ".claude/data/setup-fatto").write_text("2026-11-08\n", encoding="utf-8")
    primo, secondo = avvio(), avvio()
    if primo.count("HERDR:") != 1:
        return "chi ha già Arturo non riceve l'invito a Herdr"
    if "HERDR:" in secondo:
        return "l'invito a Herdr torna a ogni avvio"
    return None


def hz09(repo: Path, casa: Path) -> str | None:
    dati = (repo / "shared/volta-celeste/mods/arturo/dati.js").read_text(encoding="utf-8")
    blocco = re.search(r"export const SUGGERIMENTI = \[(.*?)\n\];", dati, re.S)
    if not blocco:
        return "SUGGERIMENTI non trovato in dati.js"
    prompt = re.findall(r'prompt: "([^"]+)"', blocco.group(1))
    for p in prompt:
        if p.startswith("/"):
            nome = p[1:].split()[0]
            if not (repo / "commands" / f"{nome}.md").exists():
                return f"il suggerimento {p} non ha un comando in commands/"
        if "~/.claude/" in p:
            return f"il suggerimento scrive ~/.claude a mano, che non sempre è la cartella di Arturo: {p[:80]}"
        for rel in re.findall(r"\{radice\}/([\w./-]+\.md)", p):
            if not (repo / rel).exists():
                return f"il suggerimento rimanda a {rel}, che non c'è"
    trova = (repo / "shared/volta-celeste/trova-progetti.md").read_text(encoding="utf-8")
    ritratto = (repo / "shared/setup-ritratto.md").read_text(encoding="utf-8")
    if "2c. Le cartelle" not in trova or "## 2c. Le cartelle" not in ritratto:
        return "trova-progetti.md non usa la parte 2c del ritratto"
    sotto = set(re.findall(r'add_parser\("(\w+)"', (repo / "bin/ritratto.py").read_text(encoding="utf-8")))
    if not {"cartelle", "scan"} <= sotto:
        return f"ritratto.py non ha più cartelle e scan: {sorted(sotto)}"
    if "arturo todo stato --progetto" not in trova:
        return "trova-progetti.md non scrive la riga di stato dei progetti nuovi"
    return None


PROVA_PARTENZA = r"""
import { partenza } from %s;
const t = (id) => ({ id, titolo: "todo " + id });
const vista = (da, catena) => ({ gruppi: [{ tipo: "io", todo: [1, 2, 3, 4, 5, 6, 7].map(t) }],
  progetti: [{ nome: "p", catena, da_dove: da ? { id: da, motivo: "Sblocca #3" } : null }] });
const forma = (r) => r && { id: r.todo.id, motivo: r.motivo, poi: r.poi.map((x) => x.id) };
console.log(JSON.stringify([
  forma(partenza(vista(2, [1, 2, 3, 4, 5, 6]))),
  forma(partenza(vista(2, [1, 2, 3, 4, 5, 6]), new Set([3]))),
  forma(partenza(vista(null, [1, 2]))),
  forma(partenza(vista(2, [2, 3]), new Set([2]))),
  forma(partenza(vista(7, [1, 2]))),
  forma(partenza(null)),
]));
"""


def hz10(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "partenza.mjs"  # .mjs: senza package.json node leggerebbe il .js come CommonJS
    shutil.copyfile(repo / "shared/volta-celeste/mods/arturo/partenza.js", copia)
    modulo = copia.as_uri()
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_PARTENZA % json.dumps(modulo)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"partenza.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    atteso = [{"id": 2, "motivo": "Sblocca #3", "poi": [3, 4, 5]}, {"id": 2, "motivo": "Sblocca #3", "poi": [4, 5, 6]},
              None, None, {"id": 7, "motivo": "Sblocca #3", "poi": []}, None]
    avuto = json.loads(r.stdout.strip().splitlines()[-1])
    for n, (a, b) in enumerate(zip(atteso, avuto), 1):
        if a != b:
            return f"caso {n}: atteso {a}, avuto {b}"
    return None


PROVA_SETTIMANA = r"""
import { revisione, settimanaDi } from %s;
const t = (progetto, giorni) => ({ progetto, giorni });
const vista = {
  gruppi: [{ tipo: "tu", todo: [t("a", -3), t("a", -20), t("b", 2), t("c", -1)] }],
  progetti: [
    { nome: "a", chiedono_te: 4, eta_gg: 15 },
    { nome: "b", chiedono_te: 1, eta_gg: 2 },
    { nome: "c", chiedono_te: 0, eta_gg: null },
    { nome: "d", chiedono_te: 9, eta_gg: 1 },
    { nome: "e", chiedono_te: 0, eta_gg: 8 },
    { nome: "f", chiedono_te: 0, eta_gg: 7 },
    { nome: "g", chiedono_te: 0, eta_gg: 30 },
  ],
};
const r = revisione(vista);
const forma = (l) => l.map((v) => [v.progetto.nome, v.motivo]);
console.log(JSON.stringify({ scaduti: forma(r.scaduti), te: forma(r.te), fermi: forma(r.fermi),
  settimane: ["2026-11-08", "2026-11-09", "2021-01-03", "2024-12-30", "x"].map(settimanaDi) }));
"""


def hz11(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if "settimana: Settimana" not in main or 'from "./revisione.js"' not in main:
        return "main.js non ha la parte settimana"
    if "apriRevisione()" not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "barra.js non apre La settimana"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "settimana.mjs"
    shutil.copyfile(mod / "settimana.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_SETTIMANA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"settimana.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    avuto = json.loads(r.stdout.strip().splitlines()[-1])
    atteso = {
        "scaduti": [["a", "2 todo scaduti, il più vecchio da 20 giorni · 4 todo aspettano te · ultimo punto 15 giorni fa"],
                    ["c", "1 todo scaduto da 1 giorno"]],
        "te": [["d", "9 todo aspettano te"], ["b", "1 todo aspetta te"]],
        "fermi": [["g", "Ultimo punto 30 giorni fa"], ["e", "Ultimo punto 8 giorni fa"]],
        "settimane": ["2026-W45", "2026-W46", "2020-W53", "2025-W01", ""],
    }
    for k, v in atteso.items():
        if avuto.get(k) != v:
            return f"{k}: atteso {v}, avuto {avuto.get(k)}"
    return None


PROVA_AZIONI = r"""
import { azioni, aggiungi, fatto, inizia } from %s;
import { readFileSync } from "fs";
const righe = JSON.parse(readFileSync(%s, "utf-8"));
const testo = "perché sì";
console.log(JSON.stringify({
  aggiungi: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => aggiungi({ titolo: `  prova   ${n} `, progetto: "prova", chi: "io", quando: "oggi" })?.argv),
  vuoto: aggiungi({ titolo: "   ", progetto: "prova" }),
  righe: righe.map((t) => ({ id: t.id, voci: Object.fromEntries(azioni(t).map((v) => [v.id, v.argv(testo)])), fatto: fatto(t).argv, inizia: inizia(t)?.argv ?? null })),
}));
"""

# Per ogni todo di prova (in ordine) il gesto da fare e cosa deve lasciare: campo, valore.
GESTI = [("chi-tu", "chi", "tu"), ("chi-decidi", "chi", "decidi"), ("quando-settimana", "quando", "settimana"),
         ("quando-più avanti", "quando", "più avanti"), ("ferma", "motivo", "perché sì"), ("nota", "note", ["perché sì"]),
         ("scarta", "stato", "scartato"), ("fatto", "stato", "fatto"), ("ferma", "stato", "fermo")]


def hz12(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if "azioni: Azioni" not in main or "nuovo: Nuovo" not in main:
        return "main.js non ha le parti azioni e nuovo"
    pannello = (mod / "todo.js").read_text(encoding="utf-8")
    if "apriMenu(item)" not in pannello:
        return "il pannello Da fare non apre il menu delle azioni"
    # Lavoraci, nella riga e nella scheda in cima, segna il todo in corso prima di aprire Claude.
    corpo = pannello.split("  lavoraci(item, cx) {", 1)[-1].split("\n  }\n", 1)[0]
    if pannello.count("this.lavoraci(item, cx)") != 2 or "const g = inizia(item);" not in corpo \
            or corpo.find("todo(g.argv)") > corpo.find("await apri(progetto, scelto)"):
        return "Lavoraci non segna il todo in corso prima di aprire Claude"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "azioni.mjs"
    shutil.copyfile(mod / "azioni.js", copia)
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-08"}

    def cli(argv):
        return subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *argv], capture_output=True,
                              text=True, timeout=60, env=env, cwd=casa)

    def gesti(righe):
        (casa / "righe.json").write_text(json.dumps(righe), encoding="utf-8")
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_AZIONI % (json.dumps(copia.as_uri()),
                            json.dumps(str(casa / "righe.json")))], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f"azioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}")
        return json.loads(r.stdout.strip().splitlines()[-1])

    def mostra(n):
        return json.loads(cli(["mostra", str(n), "--json"]).stdout)

    g = gesti([])
    if g["vuoto"] is not None:
        return "un titolo vuoto aggiunge un todo"
    for argv in g["aggiungi"]:
        r = cli(argv)
        if r.returncode != 0:
            return f"Aggiungi non va sulla CLI: {argv} → {(r.stderr or r.stdout).strip()[:120]}"
    righe = [mostra(n) for n in range(1, len(GESTI) + 1)]
    if [(t["titolo"], t["chi"], t["quando"]) for t in righe[:1]] != [("prova 1", "io", "oggi")]:
        return f"Aggiungi non scrive titolo, chi e quando: {righe[0]}"
    voci = gesti(righe)["righe"]
    if any(k in voci[0]["voci"] for k in ("chi-io", "quando-oggi", "riprendi")):
        return f"il menu propone quello che il todo ha già: {sorted(voci[0]['voci'])}"
    for (gesto, campo, valore), riga in zip(GESTI, voci):
        argv = riga["fatto"] if gesto == "fatto" else riga["voci"][gesto]
        r = cli(argv)
        if r.returncode != 0:
            return f"il gesto {gesto} non va sulla CLI: {argv} → {(r.stderr or r.stdout).strip()[:120]}"
        avuto = mostra(riga["id"]).get(campo)
        if avuto != valore:
            return f"il gesto {gesto} lascia {campo} = {avuto!r}, atteso {valore!r}"
    fermo = mostra(len(GESTI))
    voci = gesti([fermo])["righe"][0]["voci"]
    if "ferma" in voci or "riprendi" not in voci:
        return f"a un todo fermo il menu propone {sorted(voci)}"
    r = cli(voci["riprendi"])
    if r.returncode != 0 or mostra(len(GESTI))["stato"] != "da fare":
        return f"Riprendi non riapre il todo fermo: {(r.stderr or r.stdout).strip()[:120]}"
    # Lavoraci: il todo passa in corso, non si riscrive se lo è già, e il menu lo rimette da fare.
    n = len(GESTI) + 1
    r = cli(gesti([mostra(n)])["righe"][0]["inizia"])
    if r.returncode != 0 or mostra(n)["stato"] != "in corso":
        return f"Lavoraci non segna il todo in corso: {mostra(n)['stato']} {(r.stderr or r.stdout).strip()[:120]}"
    corso = gesti([mostra(n)])["righe"][0]
    if corso["inizia"] is not None:
        return "Lavoraci riscrive un todo già in corso"
    if "riprendi" not in corso["voci"] or "ferma" not in corso["voci"]:
        return f"a un todo in corso il menu propone {sorted(corso['voci'])}"
    r = cli(corso["voci"]["riprendi"])
    if r.returncode != 0 or mostra(n)["stato"] != "da fare":
        return f"il menu non rimette da fare un todo in corso: {(r.stderr or r.stdout).strip()[:120]}"
    return None


def hz13(repo: Path, casa: Path) -> str | None:
    installa_sh = (repo / INSTALLA).read_text(encoding="utf-8")
    if 'sh "$qui/arturo-app.sh" --agente' not in installa_sh \
            or '[ -z "${ARTURO_HERDR_INSTALLER:-}" ] && [ -d "$HOME/Applications/Herdr.app" ]' not in installa_sh:
        return "l'installatore non crea Arturo.app sul Mac, o la crea anche nei banchi"
    if sys.platform != "darwin":
        return None
    import plistlib

    def app(dove: Path, nome: str, versione: str, ident: str) -> None:
        (dove / "Contents/MacOS").mkdir(parents=True, exist_ok=True)
        (dove / "Contents/Resources").mkdir(parents=True, exist_ok=True)
        eseg = dove / "Contents/MacOS/Herdr"
        eseg.write_text("#!/bin/sh\necho herdr\n", encoding="utf-8")
        eseg.chmod(0o755)
        with open(dove / "Contents/Info.plist", "wb") as f:
            plistlib.dump({"CFBundleName": nome, "CFBundleDisplayName": nome, "CFBundleIdentifier": ident,
                           "CFBundleExecutable": "Herdr", "CFBundleIconFile": "Herdr", "CFBundlePackageType": "APPL",
                           "CFBundleShortVersionString": versione}, f)

    herdr, arturo, agenti = casa / "Applications/Herdr.app", casa / "Applications/Arturo.app", casa / "agenti"
    copia = casa / "Library/Application Support/Arturo/arturo-app"
    env = {**os.environ, "ARTURO_HERDR_APP": str(herdr), "ARTURO_APP": str(arturo), "ARTURO_APP_AGENTI": str(agenti),
           "ARTURO_APP_COPIA": str(copia), "ARTURO_APP_NO_LAUNCHCTL": "1", "ARTURO_APP_FIRMA": "adhoc"}

    def giro(*arg):
        return subprocess.run(["sh", str(repo / "shared/volta-celeste/arturo-app.sh"), *arg], capture_output=True,
                              text=True, timeout=60, env=env)

    def arturo_ok(versione):
        with open(arturo / "Contents/Info.plist", "rb") as f:
            i = plistlib.load(f)
        avuto = (i.get("CFBundleName"), i.get("CFBundleIdentifier"), i.get("CFBundleShortVersionString"))
        if avuto != ("Arturo", "org.stellakamikaze.arturo", versione):
            return f"Arturo.app ha {avuto}, attesa Arturo {versione}"
        if not (arturo / "Contents/Resources/Arturo.icns").exists():
            return "Arturo.app senza icona"
        v = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(arturo)], capture_output=True, text=True)
        return f"firma di Arturo.app non valida: {v.stderr.strip()[:120]}" if v.returncode else None

    app(herdr, "Herdr", "0.1.13", "dev.herdr.app")
    r = giro("--agente")
    if r.returncode != 0:
        return f"arturo-app.sh esce {r.returncode}: {(r.stderr or r.stdout).strip()[:160]}"
    if (m := arturo_ok("0.1.13")):
        return m
    with open(agenti / "org.stellakamikaze.arturo-app.plist", "rb") as f:
        agente = plistlib.load(f)
    guarda = agente.get("WatchPaths", [])
    # launchd non legge Documenti: l'agente lancia la copia fuori dal repository, con l'icona accanto (#5087).
    lancia = agente.get("ProgramArguments", [])
    if lancia != ["/bin/sh", str(copia / "arturo-app.sh")]:
        return f"il LaunchAgent non lancia la copia fuori dal repository: {lancia}"
    if not (copia / "arturo-icona.svg").exists() \
            or (copia / "arturo-app.sh").read_bytes() != (repo / "shared/volta-celeste/arturo-app.sh").read_bytes():
        return "la copia per il LaunchAgent manca o non è uguale allo script del repository"
    if sorted(guarda) != sorted([str(herdr / "Contents/Info.plist"), str(arturo / "Contents/Info.plist")]):
        return f"il LaunchAgent non guarda i due Info.plist: {guarda}"
    prima = (arturo / "Contents/Info.plist").stat().st_mtime_ns
    if "già a posto" not in giro().stdout or (arturo / "Contents/Info.plist").stat().st_mtime_ns != prima:
        return "il secondo giro rifà Arturo.app"
    shutil.rmtree(arturo)
    app(arturo, "Herdr", "0.1.14", "dev.herdr.app")  # l'aggiornamento fatto da dentro Arturo.app
    giro()
    if (m := arturo_ok("0.1.14")):
        return f"dopo l'aggiornamento: {m}"
    shutil.rmtree(herdr)
    app(herdr, "Herdr", "0.1.15", "dev.herdr.app")  # Herdr.app aggiornato dall'installer
    giro()
    if (m := arturo_ok("0.1.15")):
        return f"con Herdr.app più nuovo: {m}"
    return None


PROVA_NOTA = r"""
import { nota, cartellaNota, progettoNota } from %s;
const base = { x: 412.6, y: 233.2, larghezza: 1440, altezza: 900, cartella: "/casa/.claude/data/note-finestra/x", schermo: "Ricette", quando: "2026-11-09T09:00:00Z" };
console.log(JSON.stringify({
  piena: nota({ ...base, testo: "  Il   pulsante è troppo piccolo ", progetto: "prova" }),
  vuota: nota({ ...base, testo: "   ", progetto: "prova" }),
  senza: nota({ ...base, testo: "ciao", progetto: null }),
  cartella: cartellaNota("/casa", new Date(2026, 10, 9, 9, 5, 7)),
  scelto: progettoNota("arturo", "ricette"), aperto: progettoNota(null, "ricette"),
}));
"""


def hz14(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    if "nota: Nota" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non ha la parte nota"
    if json.loads((repo / "shared/volta-celeste/keys.json").read_text(encoding="utf-8")).get("global", {}).get("cmd-shift-n") != "arturo.nota":
        return "keys.json non lega cmd-shift-n alle note"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    # apriNota sta in comuni.js dal passo 3 di #5117: la usano la barra e l'elenco delle note.
    corpo = (mod / "comuni.js").read_text(encoding="utf-8").split("export async function apriNota(apri = null) {", 1)[-1].split("\n}\n", 1)[0]
    if 'else if (c === "nota") await apriNota();' not in barra or corpo.find(" shot ") < 0 or corpo.find(" shot ") > corpo.find("openOverlay("):
        return "barra.js non fa lo screenshot prima di aprire il velo delle note"
    if 'arturo = leggi("arturo.json") or {}' not in (repo / INSTALLA).read_text(encoding="utf-8"):
        return "l'installatore riscrive arturo.json perdendo note_progetto"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_NOTA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["vuota"] is not None:
        return "una nota vuota parte lo stesso"
    if g["senza"]["argv"] is not None or g["senza"]["dati"]["testo"] != "ciao":
        return "senza progetto la nota non resta solo nella cartella"
    d = g["piena"]["dati"]
    if (d["testo"], d["punto"], d["finestra"], d["progetto"], d["screenshot"]) != (
            "Il pulsante è troppo piccolo", {"x": 413, "y": 233}, {"larghezza": 1440, "altezza": 900}, "prova", "finestra.png"):
        return f"nota.json non porta testo, punto, finestra e progetto: {d}"
    if g["cartella"] != "/casa/.claude/data/note-finestra/2026-11-09_09-05-07":
        return f"cartella della nota sbagliata: {g['cartella']}"
    if (g["scelto"], g["aperto"]) != ("arturo", "ricette"):
        return "il progetto delle note non preferisce note_progetto al progetto aperto"
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-09"}
    r = subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *g["piena"]["argv"]], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    if r.returncode != 0:
        return f"la nota non va sulla CLI: {(r.stderr or r.stdout).strip()[:160]}"
    t = json.loads(subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", "mostra", "1", "--json"],
                                  capture_output=True, text=True, timeout=60, env=env, cwd=casa).stdout)
    if (t["chi"], t["quando"], t["progetto"]) != ("io", "oggi", "prova") or not t["titolo"].startswith("Nota sulla finestra: Il pulsante"):
        return f"la nota non diventa una cosa da fare di Claude per oggi: {t['chi']} {t['quando']} {t['progetto']} {t['titolo']}"
    if not any("note-finestra/x" in n and "413,233" in n for n in t.get("note", [])):
        return f"la cosa da fare non porta punto e cartella nelle note: {t.get('note')}"
    return None


def scritti_in_data(repo: Path) -> set[str]:
    """I nomi sotto ~/.claude/data/ che la parte Herdr scrive: mod, hook di stato e invito all'avvio."""
    fonti = [f for f in (repo / "shared/volta-celeste").rglob("*") if f.is_file() and f.suffix in (".js", ".sh", ".py")]
    fonti.append(repo / "hooks/herdr-stato.sh")
    testi = [f.read_text(encoding="utf-8") for f in fonti]
    testi += [r for r in (repo / "hooks/session-start.sh").read_text(encoding="utf-8").splitlines() if "herdr" in r]
    return {m for testo in testi for m in re.findall(r"\.claude/data/([A-Za-z0-9_.-]+)", testo)}


def hz15(repo: Path, casa: Path) -> str | None:
    nomi = scritti_in_data(repo)
    if not {"note-finestra", "herdr-invito"} <= nomi:
        return f"il banco non trova più le scritture in data/: {sorted(nomi)}"
    prova_git = casa / "git"
    prova_git.mkdir()
    shutil.copyfile(repo / ".gitignore", prova_git / ".gitignore")
    subprocess.run(["git", "init", "-q"], cwd=prova_git, check=True)
    fuori = []
    for nome in sorted(nomi):
        # Una cartella si prova con un file dentro, un file col suo nome: check-ignore risponde 0 se è escluso.
        # Le note hanno tre file per cartella (nota.json, lo scatto, il ritaglio di arturo note mostra):
        # nessuno dei tre entra in git.
        if nome == "note-finestra":
            fuori += [rel for rel in (f"data/{nome}/x/{f}" for f in ("nota.json", "finestra.png", "ritaglio.png"))
                      if subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=prova_git).returncode != 0]
            continue
        forme = (f"data/{nome}/x/nota.json", f"data/{nome}")
        if not any(subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=prova_git).returncode == 0
                   for rel in forme):
            fuori.append(f"data/{nome}")
    return f".gitignore non esclude {', '.join(fuori)}" if fuori else None


def hz16(repo: Path, casa: Path) -> str | None:
    if sys.platform != "darwin":
        return None
    bin_ = casa / ".local" / "bin"
    bin_.mkdir(parents=True)
    for nome in ("claude", "herdr-core"):
        (bin_ / nome).write_text("#!/bin/sh\n")
        (bin_ / nome).chmod(0o755)
    agenti = casa / "agenti"
    env = dict(os.environ, HOME=str(casa), SERVIZI_AGENTI=str(agenti), SERVIZI_NO_LAUNCHCTL="1")
    script = repo / "shared" / "volta-celeste" / "servizi-gui.sh"

    def leggi(nome: str) -> dict | None:
        f = agenti / f"org.stellakamikaze.arturo.{nome}.plist"
        if not f.exists():
            return None
        r = subprocess.run(["plutil", "-convert", "json", "-o", "-", str(f)], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else {"rotto": r.stderr}

    r = subprocess.run(["sh", str(script)], env=env, capture_output=True, text=True)
    if r.returncode:
        return f"servizi-gui.sh esce {r.returncode}: {r.stderr.strip()[-200:]}"
    core = leggi("herdr-core")
    if not core or core.get("KeepAlive") is not False or core.get("ProgramArguments", [])[-1:] != ["serve"]:
        return f"herdr-core: plist mancante, rotto o con KeepAlive: {core}"
    if leggi("claude-daemon") is not None:
        return "senza --launchd il gestore delle sessioni non deve stare in launchd"
    r = subprocess.run(["sh", str(script), "--launchd"], env=env, capture_output=True, text=True)
    gestore = leggi("claude-daemon")
    if r.returncode or not gestore or gestore.get("KeepAlive") is not True or gestore.get("ProgramArguments", [])[1:] != ["daemon", "run"]:
        return f"--launchd: gestore mancante o sbagliato: {gestore}"
    return None


PROVA_VOLTA = r"""
import * as v from %s;
const ADESSO = Date.parse("2026-11-09T18:00:00Z");
const r = (o) => ({ macchina: "MacBook Air", host: "macbook", questa: true, tipo: "background", stato: "ferma", ultimo: "", risposta: "", progetto: null, attach: ["claude", "attach", o.id], ...o });
const dati = {
  macchine: [{ macchina: "MacBook Air", host: "macbook", questa: true }, { macchina: "Amaltea", host: "amaltea", questa: false },
             { macchina: "Torre", host: "torre", questa: false, irraggiungibile: "timeout" }],
  sessioni: [
    r({ id: "a1", nome: "uno", stato: "ferma", ultimo: "2026-11-09T15:00:00Z", progetto: "arturo" }),
    r({ id: "a2", nome: "due", stato: "lavora", progetto: "arturo" }),
    r({ id: "a3", nome: "claudecode-ca", tipo: "interattiva", attach: null, risposta: "**Fatto:** il deck è pronto\nresto", stato: "aspetta" }),
    r({ id: "b1", nome: "tre", host: "amaltea", macchina: "Amaltea", questa: false, stato: "errore", progetto: "due-mondi", attach: ["ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"] }),
    r({ id: "b2", nome: "quattro", host: "amaltea", macchina: "Amaltea", questa: false, stato: "ferma", progetto: "arturo" }),
  ],
};
const forma = (gs) => gs.map((g) => [g.titolo, g.nota ?? "", g.sessioni.map((s) => s.id)]);
const s = (id) => dati.sessioni.find((x) => x.id === id);
console.log(JSON.stringify({
  macchina: forma(v.gruppi(dati, "macchina")),
  progetto: forma(v.gruppi(dati, "progetto")),
  titoli: ["a1", "a3"].map((id) => v.titolo(s(id))),
  quanto: [v.daQuanto("2026-11-09T17:56:00Z", ADESSO), v.daQuanto("2026-11-09T15:00:00Z", ADESSO), v.daQuanto("2026-11-07T18:00:00Z", ADESSO), v.daQuanto("", ADESSO)],
  dettaglio: [v.dettaglio(s("a1"), "macchina", ADESSO).testo, v.dettaglio(s("b1"), "progetto", ADESSO).testo],
  clic: [
    v.clic(s("a1")), v.clic(s("b1")), v.clic({ ...s("a3"), stato: "ferma" }), v.clic(s("a3")).azione,
    v.clic({ ...s("a3"), stato: "lavora" }).azione, v.clic({ ...s("a1"), vecchia: true }).azione, v.clic({ ...s("a1"), attach: null }).azione,
    v.clic({ ...s("a3"), terminale: "t23" }), v.clic({ ...s("a3"), terminale: "t1m", questa: false, host: "amaltea" }),
    v.clic({ ...s("a3"), terminale: "t23", vecchia: true }).azione,
  ],
  aggancio: [v.agganciata(["/bin/zsh", "-lic", "x", "/bin/zsh", "ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"], s("b1")),
             v.agganciata(["claude", "attach", "zz"], s("b1")), v.agganciata(undefined, s("b1")),
             v.agganciata(["/bin/zsh", "-lic", "x", "/bin/zsh", "sh", "-c", "while :; do ssh -t amaltea .local/bin/claude attach b1; [ $? -eq 255 ] || break; done"], s("b1")),
             v.agganciata(["sh", "-c", "ssh amaltea claude attach b10"], s("b1")), v.agganciata(["sh", "-c", "echo b1"], s("b1")),
             v.agganciata(["pwsh.exe", "-NoExit", "-Command", "& 'C:\\\\Windows\\\\System32\\\\OpenSSH\\\\ssh.exe' '-t' 'amaltea' '.local/bin/claude' 'attach' 'b1'"], s("b1"))],
}));
"""


def volta_node(repo: Path, casa: Path) -> dict | str | None:
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(repo / "shared/volta-celeste/mods/arturo/sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_VOLTA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def hz17(repo: Path, casa: Path) -> str | None:
    avuto = volta_node(repo, casa)
    if not isinstance(avuto, dict):
        return avuto
    atteso = {
        "macchina": [["MacBook Air", "", ["a1", "a2", "a3"]], ["Amaltea", "", ["b2", "b1"]], ["Torre", "Non risponde", []]],
        "progetto": [["Senza progetto", "Torre non risponde", ["a3"]]],
        "titoli": ["uno", "Fatto: il deck è pronto"],
        "quanto": ["da 4 min", "da 3 ore", "da 2 giorni", ""],
        "dettaglio": ["Arturo · Ferma da 3 ore", "Amaltea · Si è fermata con un errore"],
    }
    gp = avuto.get("progetto", [])
    if [g[0] for g in gp] != ["Arturo", "Due mondi", "Senza progetto"]:
        return f"progetto: ordine dei gruppi {[g[0] for g in gp]}, atteso Arturo, Due mondi, Senza progetto"
    if gp[0][2] != ["a1", "a2", "b2"]:
        return f"progetto: dentro Arturo {gp[0][2]}, atteso la più recente e poi l'alfabeto"
    for k, v in atteso.items():
        a = avuto.get(k)
        if k == "progetto":
            a = a[-1:]
        if a != v:
            return f"{k}: atteso {v}, avuto {a}"
    return None


def hz18(repo: Path, casa: Path) -> str | None:
    avuto = volta_node(repo, casa)
    if not isinstance(avuto, dict):
        return avuto
    atteso = {
        "clic": [{"azione": "aggancia", "argv": ["claude", "attach", "a1"]},
                 {"azione": "aggancia", "argv": ["ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"]},
                 {"azione": "porta"}, "no", "no", "no", "no",
                 {"azione": "mostra", "terminale": "t23"}, {"azione": "mostra", "terminale": "amaltea/t1m"}, "no"],
        "aggancio": [True, False, False, True, False, False, True],
    }
    for k, v in atteso.items():
        if avuto.get(k) != v:
            return f"{k}: atteso {v}, avuto {avuto.get(k)}"
    return None


def hz19(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, dove in (('import { Volta } from "./volta.js";', "barra.js"), ("this.volta.init(cx);", "barra.js"),
                        ("this.volta.render(cx)", "barra.js"), ('c.startsWith("volta-")) this.volta.premiId(', "barra.js")):
        if pezzo not in barra:
            return f"{dove} senza {pezzo}"
    for pezzo in ('"volta", "--scrivi"', '"porta-volta"', "if (!this.script) return null;", "if (!this.script || this.inCorso) return;",
                  'from "./sessioni.js"', "this.apri(s, d.argv, false, cx);", "await apriSessione(s, argv, pronta)"):
        if pezzo not in volta:
            return f"volta.js senza {pezzo}"
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    if "agganciata(x.argv, s)" not in dati:
        return "dati.js senza agganciata(x.argv, s): una scheda già aperta non si riconosce"
    return None


def hz20(repo: Path, casa: Path) -> str | None:
    volta = (repo / "shared/volta-celeste/mods/arturo/volta.js").read_text(encoding="utf-8")
    if "this.py = c.arturo[0];" not in volta or "const c = await config();" not in volta:
        return "volta.js non prende Python da arturo.json"
    for pezzo in ('exec(this.py, [this.script, "volta"', 'exec(this.py, [this.sposta, "porta-volta"'):
        if pezzo not in volta:
            return f"volta.js senza {pezzo}"
    if 'exec("python' in volta:
        return "volta.js lancia ancora un Python scritto a mano"
    return None


def hz21(repo: Path, casa: Path) -> str | None:
    # APPDATA finto: il veleno (la cartella di prima) non deve scrivere nella cartella vera
    r = installa(repo, casa, "windows", {"HERDR_APP_HOME": "", "APPDATA": str(casa / "appdata")})
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione Windows fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    app = casa / "home" / ".config" / "herdr-app"
    if not (app / "layouts" / "arturo.json").is_file() or not (app / "arturo.json").is_file():
        return f"layout e arturo.json non sono in ~/.config/herdr-app, dove Herdr li legge su Windows"
    core = casa / "home" / ".config" / "herdr-core" / "config.toml"
    if not core.is_file() or "shell = [" not in core.read_text(encoding="utf-8"):
        return "la shell di herdr-core non è in ~/.config/herdr-core/config.toml"
    if (casa / "appdata").exists():
        return "l'installatore ha scritto in %APPDATA%, che Herdr su Windows non legge"
    return None


HERDR_CTRL = (
    "ctrl-shift-/", "ctrl-shift-?", "ctrl-shift-b", "ctrl-shift-c", "ctrl-shift-e", "ctrl-shift-f",
    "ctrl-shift-k", "ctrl-shift-l", "ctrl-shift-n", "ctrl-shift-o", "ctrl-shift-p", "ctrl-shift-pagedown",
    "ctrl-shift-pageup", "ctrl-shift-t", "ctrl-shift-tab", "ctrl-shift-v", "ctrl-shift-w", "ctrl-shift-x",
    "ctrl-shift-z", "ctrl-,", "ctrl-?",
)


def hz22(repo: Path, casa: Path) -> str | None:
    esiti = {}
    for sistema in ("windows", "mac-arm"):
        sotto = casa / sistema
        sotto.mkdir()
        extra = {"ARTURO_HERDR_FIRMA": "presente"} if sistema == "mac-arm" else {}
        r = installa(repo, sotto, sistema, extra)
        if r.returncode != 0 or "HERDR OK" not in r.stdout:
            return f"installazione {sistema} fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
        esiti[sistema] = leggi(sotto / "app" / "keys.json").get("global", {})
    win, mac = esiti["windows"], esiti["mac-arm"]
    # I tasti che Herdr scrive in keys.json al primo avvio su Windows (src/keys/shipped/v0.1.12-keys.json
    # di Volta Celeste, più ctrl-shift-c, -v e -f del terminale): Arturo non deve prenderne nessuno.
    sopra = casa / "sopra-herdr"
    (sopra / "app").mkdir(parents=True)
    (sopra / "app" / "keys.json").write_text(json.dumps({"global": {**dict.fromkeys(HERDR_CTRL, "herdr"), "ctrl-shift-t": "tab.new"}}), encoding="utf-8")
    r = installa(repo, sopra, "windows")
    if r.returncode != 0 or "lasciato com'era" in r.stdout:
        return f"su Windows un tasto di Arturo è già di Herdr: {r.stdout.strip()[-200:]}"
    if win.get("ctrl-shift-a") != "arturo.apri" or win.get("ctrl-shift-m") != "arturo.nota":
        return f"su Windows mancano Ctrl+Shift+A e Ctrl+Shift+M: {win}"
    if any(k.startswith("cmd-") for k in win):
        return f"su Windows sono finiti tasti con cmd (il tasto Windows): {sorted(k for k in win if k.startswith('cmd-'))}"
    if mac.get("cmd-o") != "arturo.apri" or "ctrl-shift-a" in mac:
        return f"sui Mac i tasti non sono quelli con ⌘: {mac}"
    return None


def hz23(repo: Path, casa: Path) -> str | None:
    # python3 finto come lo stub di WindowsApps (esce 9009), python che porta al Python vero
    finti = casa / "finti"
    finti.mkdir()
    vero = Path(sys.executable).as_posix()
    (finti / "python3").write_text("#!/bin/sh\necho 'Python was not found' >&2\nexit 9009\n", encoding="utf-8", newline="\n")
    (finti / "python").write_text(f'#!/bin/sh\nexec "{vero}" "$@"\n', encoding="utf-8", newline="\n")
    for f in finti.iterdir():
        f.chmod(0o755)
    r = installa(repo, casa, "windows", {"PATH": str(finti) + os.pathsep + os.environ.get("PATH", "")})
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    py = leggi(casa / "app" / "arturo.json")["arturo"][0]
    if py != "python":
        return f"arturo.json usa {py!r}: con python3 che non risponde serve python"
    return None


def hz24(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    testata = (mod / "testata.js").read_text(encoding="utf-8")
    guida = (mod / "guida.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for nome, testo in (("testata.js", testata), ("guida.js", guida)):
        codice = "\n".join(r for r in testo.splitlines() if not r.lstrip().startswith("//"))
        if "⌘" in codice:
            return f"{nome} scrive ⌘ a mano: i tasti vengono da tasti() di comuni.js"
        if "tasti()" not in codice:
            return f"{nome} non prende i tasti da tasti()"
    if 'window()?.platform === "macos"' not in (mod / "comuni.js").read_text(encoding="utf-8"):
        return "tasti() non sceglie per sistema"
    if "if (!s) notify({ title: `Non trovo la sessione ${id}`" not in volta:
        return "premiId non avvisa quando la sessione non è nell'elenco"
    return None


def hz25(repo: Path, casa: Path) -> str | None:
    # Una finestra di dialogo chiusa ferma il suo codice al primo await: la chiusura viene dopo l'azione.
    mod = repo / "shared/volta-celeste/mods/arturo"
    prima = re.compile(r"(this\.chiudi\(\)|dopo\?\.\(\)|closeOverlay\([^)]*\));\s*(?:await\s+)?(apri|esegui|scrivi|chiedi|nuova)\(")
    for f in sorted(mod.glob("*.js")):
        m = prima.search(f.read_text(encoding="utf-8"))
        if m:
            return f"{f.name} chiude la finestra prima di {m.group(2)}(): l'azione non parte"
    attesi = {"suggerimenti.js": "try { await esegui(sug); } finally { dopo?.(); }",
              "apri.js": "try { await apri(nome); } finally { this.chiudi(); }",
              "revisione.js": "try { await apri(k); } finally { this.chiudi(); }",
              "menu.js": "scrivi(v.argv(testo), v.esito, titolo).finally(() => this.chiudi());"}
    for nome, pezzo in attesi.items():
        if pezzo not in (mod / nome).read_text(encoding="utf-8"):
            return f"{nome} non aspetta l'azione prima di chiudere"
    return None


PROVA_REGIONE = r"""
const { regione, misureDaLayout, ultimeRighe, nota } = await import(%s);
const lay = %s;
const mis = (l, a) => ({ larghezza: l, altezza: a });
const parti = { marchio: mis(292, 54), barra: mis(292, 690), piede: mis(292, 156), testata: mis(1147, 54),
  todo: mis(340, 792), stato: mis(1147, 30), benvenuto: mis(0, 0) };
const m = misureDaLayout(lay, parti, mis(1440, 900));
const b = (x, y, mm = m) => regione({ x, y }, mm)?.blocco ?? null;
const largo = { ...m, marchio: mis(400, 54), barra: mis(400, 690), piede: mis(400, 156), testata: mis(1039, 54),
  stato: mis(1039, 30), todo: mis(500, 792) };
console.log(JSON.stringify({
  base: [[100, 20], [100, 300], [100, 800], [292, 300], [600, 20], [600, 880], [600, 400], [1200, 400], [1080, 400], [1086, 400]].map(([x, y]) => b(x, y)),
  main: regione({ x: 600, y: 400 }, m)?.rettangolo,
  largo: [[350, 300], [402, 400], [1000, 400], [900, 400]].map(([x, y]) => b(x, y, largo)),
  nascosto: b(1200, 400, misureDaLayout({ ...lay, children: JSON.parse(JSON.stringify(lay.children).replace('"id":"pannello",', '"id":"pannello","hidden":true,')) }, parti, mis(1440, 900))),
  benvenuto: b(690, 100, { ...m, benvenuto: mis(520, 300) }),
  vecchie: [b(600, 400, { ...m, finestra: mis(1440, 820) }), b(600, 400, { ...m, finestra: mis(1280, 900) })],
  assenti: b(600, 400, misureDaLayout(lay, {}, mis(1440, 900))),
  righe: ultimeRighe("a\nb\nc\n\n  \n", 2),
  dove: nota({ testo: "x", x: 1, y: 2, larghezza: 3, altezza: 4, progetto: "p", cartella: "/c", quando: "q",
    dove: { blocco: "main", cwd: "/w" } }),
}));
"""


def hz26(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if '"marchio", "barra", "piede", "testata", "todo", "stato", "benvenuto"' not in main \
            or "if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;" not in main \
            or "return el.id(`misura-${this.nome}`).on_size_change(" not in main or "arturo.misura.${this.nome}" not in main:
        return "main.js non fa riportare la misura alle parti del layout"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    if "const dove = await doveNota(this.punto, this.misura);" not in ui or "quando: new Date().toISOString(), dove, tipo: this.tipo" not in ui:
        return "notaui.js non mette la parte e il terminale nella nota"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    lay = (repo / "shared/volta-celeste/layouts/arturo.json").read_text(encoding="utf-8")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_REGIONE % (json.dumps(copia.as_uri()), lay)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    attese = ["marchio", "progetti", "piede", "progetti", "testata", "stato", "main", "pannello", "main", "pannello"]
    if g["base"] != attese:
        return f"regione() sbaglia la parte sotto il punto: {g['base']}"
    if g["main"] != {"x": 305, "y": 66, "larghezza": 771, "altezza": 792}:
        return f"il rettangolo della sessione non è quello dello scatto: {g['main']}"
    if g["largo"] != ["progetti", "main", "pannello", "main"]:
        return f"con barra e pannello allargati regione() sbaglia: {g['largo']}"
    if g["nascosto"] != "main":
        return "col pannello nascosto il punto a destra non va alla sessione"
    if g["benvenuto"] != "benvenuto":
        return "il benvenuto sopra la sessione non si riconosce"
    if g["vecchie"] != [None, None] or g["assenti"] is not None:
        return "con misure vecchie o assenti regione() inventa una parte"
    if g["righe"] != "b\nc":
        return f"ultimeRighe() tiene le righe vuote in fondo: {g['righe']!r}"
    if g["dove"]["dati"].get("dove", {}).get("blocco") != "main" or "parte main (terminale in /w)" not in g["dove"]["argv"][8]:
        return "nota.json e il todo non portano la parte e il terminale"
    return None


PROVA_VELO = r"""
const n = await import(%s);
const base = { x: 700, y: 400, larghezza: 1440, altezza: 900, progetto: "p", cartella: "/c/note-finestra/2026-11-10_07-00-00",
  quando: "2026-11-10T06:00:00Z", testo: "Il bottone è storto" };
const v1 = JSON.stringify({ versione: 1, quando: "2026-11-09T10:00:00Z", testo: "vecchia", punto: { x: 10, y: 20 },
  finestra: { larghezza: 1440, altezza: 900 }, progetto: "p" });
const letta = n.leggiNota(v1, "2026-11-09_10-00-00");
const mk = (id, numero, stato, progetto = "p", quando = id) => ({ id, numero, stato, progetto, quando, punto: { x: 1, y: 1 }, finestra: { larghezza: 1, altezza: 1 } });
const aperte = n.noteAperte([letta, mk("b", 1, "aperta"), mk("c", 3, "presa"), mk("d", 2, "risolta"), mk("e", 5, "aperta", "altro")], "p");
const nuova = n.nota({ ...base, numero: 4 }).dati;
console.log(JSON.stringify({
  nuova, argv: n.nota(base).argv, tipo: [n.nota({ ...base, tipo: "domanda" }).dati.tipo, n.nota({ ...base, tipo: "boh" }).dati.tipo],
  letta, rotta: [n.leggiNota("{", "x"), n.leggiNota("{}", "x")],
  aperte: aperte.map((a) => [a.id, a.numero]), prossimo: [n.prossimoNumero(aperte), n.prossimoNumero([])],
  segni: [n.segno(nuova, { larghezza: 1440, altezza: 900 }), n.segno(nuova, { larghezza: 720, altezza: 450 }),
    n.segno({ ...nuova, punto: { x: 1439, y: 899 } }, { larghezza: 700, altezza: 400 })],
  script: n.LEGGI_NOTE,
}));
"""


def hz27(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    for pezzo, perche in [
        ('exec(py, ["-c", LEGGI_NOTE, cartellaNote(home())]', "il velo non legge le note col Python di arturo.json"),
        ("writeTextFile(file, json({ ...n.dati, todo: r.json.id }), scritto)", "la nota non salva l'id del todo"),
        ("el.children(this.segni(t))", "il velo non disegna i segni delle note aperte"),
        (".child(this.pastiglie(t))", "il campo non ha le pastiglie del tipo"),
        ("numero: prossimoNumero(aperte)", "la nota nuova non prende il numero dopo le aperte")]:
        if pezzo not in ui:
            return perche
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_VELO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    d = g["nuova"]
    if (d["versione"], d["id"], d["numero"], d["tipo"], d["stato"], d["todo"], d["filo"]) != (
            2, "2026-11-10_07-00-00", 4, "correggere", "aperta", None,
            [{"chi": "federico", "quando": "2026-11-10T06:00:00Z", "testo": "Il bottone è storto"}]):
        return f"nota.json versione 2 sbagliata: {d}"
    if g["tipo"] != ["domanda", "correggere"]:
        return f"il tipo della nota non si tiene o non ricade sul predefinito: {g['tipo']}"
    if "--json" not in g["argv"] or g["argv"].index("--json") > g["argv"].index("--"):
        return "il todo della nota non si chiede con --json: l'id non torna nella nota"
    note_todo = g["argv"][g["argv"].index("--note") + 1]
    if not note_todo.endswith("Per partire: arturo note mostra 2026-11-10_07-00-00"):
        return f"le note del todo non dicono a Claude da dove partire: {note_todo[-80:]}"
    l = g["letta"]
    if (l["versione"], l["id"], l["stato"], l["numero"], l["tipo"], l["filo"][0]["testo"], l["dove"]["blocco"]) != (
            2, "2026-11-09_10-00-00", "aperta", None, "correggere", "vecchia", None):
        return f"una nota versione 1 non si legge come aperta versione 2: {l}"
    if g["rotta"] != [None, None]:
        return "un nota.json rotto o vuoto diventa una nota"
    if g["aperte"] != [["b", 1], ["2026-11-09_10-00-00", 2], ["c", 3]] or g["prossimo"] != [4, 1]:
        return f"numeri dei segni sbagliati: {g['aperte']} prossimo {g['prossimo']}"
    if g["segni"] != [{"x": 700, "y": 400}, {"x": 350, "y": 200}, {"x": 699, "y": 399}]:
        return f"i segni non si riportano in scala sulla finestra: {g['segni']}"
    cartella = casa / "note"
    for nome, testo in [("a", '{"x": 1}'), ("b", None), ("c", "ciao")]:
        (cartella / nome).mkdir(parents=True)
        if testo:
            (cartella / nome / "nota.json").write_text(testo, encoding="utf-8")
    letto = [json.loads(subprocess.run([sys.executable, "-c", g["script"], str(c)], capture_output=True, text=True, timeout=30).stdout)
             for c in (cartella, casa / "manca")]
    if letto != [[["a", '{"x": 1}'], ["c", "ciao"]], []]:
        return f"LEGGI_NOTE non legge la cartella delle note: {letto}"
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-10"}
    r = subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *g["argv"]], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    try:
        if json.loads(r.stdout)["id"] != 1:
            return f"la CLI non dà l'id del todo: {r.stdout[:120]}"
    except (ValueError, KeyError):
        return f"la CLI con --json non risponde in JSON: {(r.stderr or r.stdout).strip()[:160]}"
    return None




PROVA_ELENCO = r"""
const n = await import(%s);
const f = { larghezza: 1440, altezza: 900 };
const mk = (id, numero, stato, extra = {}) => ({ id, numero, stato, progetto: "p", quando: `2026-11-10T0${id}:00:00Z`, tipo: "domanda",
  testo: `nota ${id}`, punto: { x: 1, y: 1 }, finestra: f, filo: [{ chi: "federico", quando: "t", testo: `nota ${id}` }], ...extra });
const lista = [
  mk("1", 2, "aperta"),
  mk("2", 1, "presa", { filo: [{ chi: "federico", testo: "x" }, { chi: "claude", testo: "prima" }, { chi: "claude", testo: "ultima" }] }),
  mk("3", 1, "risolta", { chiusa_quando: "2026-11-10T05:00:00Z", riassunto: "fatto" }),
  mk("4", 3, "scartata", { chiusa_quando: "2026-11-10T06:00:00Z", motivo: "doppia" }),
  { ...mk("5", 4, "aperta"), progetto: "altro" },
];
const ora = "2026-11-10T08:00:00Z";
const r = (filtro) => n.righeElenco(lista, "p", filtro, ora).map((x) => [x.id, x.numero, x.etichettaStato, x.risposta, x.chiusura, x.eta, x.tipo]);
const viste = n.risposteClaude(lista);
const dopo = lista.map((x) => x.id === "1" ? { ...x, filo: [...x.filo, { chi: "claude", testo: "nuova" }] } : x);
console.log(JSON.stringify({
  aperte: r("aperte"), tutte: r("tutte"), conta: [n.contaNote(lista, "p"), n.contaNote(lista, null)],
  eta: ["2026-11-10T07:59:30Z", "2026-11-10T07:48:00Z", "2026-11-10T07:00:00Z", "2026-11-10T03:00:00Z", "2026-11-09T07:00:00Z", "2026-11-06T07:00:00Z", "boh"].map((q) => n.eta(q, ora)),
  nuove: n.risposteNuove(viste, dopo).map((x) => x.id), primo: n.risposteNuove(null, dopo).length,
  nuovaNota: n.risposteNuove(viste, [...lista, mk("6", 5, "aperta", { filo: [{ chi: "claude", testo: "subito" }] })]).map((x) => x.id),
}));
"""


def hz28(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta-celeste"
    mod = vc / "mods/arturo"
    testo = {f: (mod / f).read_text(encoding="utf-8") for f in ("main.js", "barra.js", "testata.js", "noteui.js", "comuni.js")}
    for f, pezzo, perche in [
        ("main.js", "note: Note };", "main.js non monta la parte note"),
        ("barra.js", 'else if (c === "note") apriElenco();', "il comando arturo.note non apre l'elenco"),
        ("barra.js", 'else if (c.startsWith("nota-")) await apriNota(c.slice(5));', "arturo.nota-<id> non apre il velo su quella nota"),
        ("comuni.js", 'props: { parte: "nota", cartella, apri }', "il velo non riceve la nota da aprire"),
        ("comuni.js", 'props: { parte: "note" }', "apriElenco non apre la parte note"),
        ("comuni.js", 'elenco: "⌘⇧E"', "tasti() non dice ⌘⇧E sui Mac"),
        ("comuni.js", 'elenco: "Ctrl+Shift+I"', "tasti() non dice Ctrl+Shift+I fuori dal Mac"),
        ("testata.js", "await watchFolder(cartellaNote(home()))", "la barra di stato non guarda la cartella delle note"),
        ("testata.js", ".on_click(() => apriElenco())", "il conteggio della barra di stato non apre l'elenco"),
        ("testata.js", "const nuove = risposteNuove(this.viste, note);", "la barra di stato non annuncia le risposte di Claude"),
        ("noteui.js", "run(`arturo.nota-${r.id}`);\n    this.chiudi();", "l'elenco chiude prima di mandare il comando: il codice di un overlay chiuso si ferma"),
    ]:
        if pezzo not in testo[f]:
            return perche
    mac = leggi(vc / "keys.json").get("global", {})
    win = leggi(vc / "keys-ctrl.json").get("global", {})
    if mac.get("cmd-shift-e") != "arturo.note" or win.get("ctrl-shift-i") != "arturo.note":
        return f"⌘⇧E o Ctrl+Shift+I non aprono l'elenco: {mac.get('cmd-shift-e')} {win.get('ctrl-shift-i')}"
    if "cmd-shift-l" in mac:
        return "⌘⇧L è di Herdr (layout.switch): l'installatore lo lascerebbe alla persona"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_ELENCO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    aperte = [["2", 1, "Claude ci lavora", "ultima", None, "6 ore fa", "Domanda"], ["1", 2, "Aperta", None, None, "7 ore fa", "Domanda"]]
    if g["aperte"] != aperte:
        return f"righe delle aperte sbagliate: {g['aperte']}"
    if g["tutte"] != aperte + [["4", None, "Scartata", None, "doppia", "2 ore fa", "Domanda"], ["3", None, "Risolta", None, "fatto", "3 ore fa", "Domanda"]]:
        return f"con tutte le chiuse non seguono dalla più recente, o tengono il numero: {g['tutte'][2:]}"
    if g["conta"] != [{"aperte": 2, "tutte": 4}, {"aperte": 0, "tutte": 0}]:
        return f"conteggio per progetto sbagliato: {g['conta']}"
    if g["eta"] != ["adesso", "12 min fa", "1 ora fa", "5 ore fa", "ieri", "4 giorni fa", ""]:
        return f"età in parole sbagliata: {g['eta']}"
    if g["nuove"] != ["1"] or g["primo"] != 0 or g["nuovaNota"] != ["6"]:
        return f"le risposte nuove di Claude non si annunciano giuste: {g['nuove']} {g['primo']} {g['nuovaNota']}"
    return None


def png(file: Path, larghezza: int, altezza: int) -> None:
    """Un PNG grigio vero, con la sola libreria standard: lo scatto finto della finestra."""
    import struct
    import zlib

    def pezzo(tipo: bytes, dati: bytes) -> bytes:
        return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF)
    riga = b"\x00" + b"\x80" * (larghezza * 3)
    file.write_bytes(b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", larghezza, altezza, 8, 2, 0, 0, 0))
                     + pezzo(b"IDAT", zlib.compress(riga * altezza)) + pezzo(b"IEND", b""))


def casa_note(casa: Path) -> tuple:
    """L'ambiente di una casa finta per arturo note e la cartella delle sue note: (env, cartella)."""
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-10"}
    env.pop("CLAUDE_CONFIG_DIR", None)
    return env, casa / ".claude/data/note-finestra"


def nota_v2(base: Path, ident: str, todo, **altro) -> None:
    d = {"versione": 2, "id": ident, "numero": 1, "quando": "2026-11-10T06:00:00.000Z", "tipo": "domanda",
         "testo": "Perché il bottone è storto?", "punto": {"x": 700, "y": 450}, "finestra": {"larghezza": 800, "altezza": 500},
         "progetto": "p", "dove": {"blocco": "testata", "parte": "testata"}, "stato": "aperta",
         "filo": [{"chi": "federico", "quando": "2026-11-10T06:00:00.000Z", "testo": "Perché il bottone è storto?"}],
         "todo": todo, "screenshot": "finestra.png", **altro}
    (base / ident).mkdir(parents=True, exist_ok=True)
    (base / ident / "nota.json").write_text(json.dumps(d), encoding="utf-8")


def hz29(repo: Path, casa: Path) -> str | None:
    env, base = casa_note(casa)
    arturo = [sys.executable, str(repo / "bin/arturo")]

    def cli(*argv):
        return subprocess.run([*arturo, *argv], capture_output=True, text=True, timeout=120, env=env, cwd=casa)
    aiuto = cli().stdout
    if "arturo note" not in aiuto:
        return "l'aiuto di arturo non nomina arturo note"
    r = cli("todo", "aggiungi", "--progetto", "p", "--chi", "io", "--json", "--", "Nota sulla finestra: il bottone")
    try:
        tid = json.loads(r.stdout)["id"]
    except (ValueError, KeyError):
        return f"il todo della nota non nasce: {(r.stderr or r.stdout)[:120]}"
    nota_v2(base, "2026-11-10_07-00-00", tid)
    png(base / "2026-11-10_07-00-00/finestra.png", 1600, 1000)
    (base / "vecchia").mkdir(parents=True)
    (base / "vecchia/nota.json").write_text(json.dumps({"testo": "v1", "punto": {"x": 5, "y": 5}, "progetto": "p",
        "finestra": {"larghezza": 800, "altezza": 500}, "quando": "2026-11-10T05:00:00Z"}), encoding="utf-8")
    (base / "vuota").mkdir()
    r = cli("note", "elenco", "--json")
    try:
        note = json.loads(r.stdout)["note"]
    except (ValueError, KeyError):
        return f"elenco --json non risponde in JSON: {(r.stderr or r.stdout)[:160]}"
    if [(n["id"], n["numero"], n["stato"]) for n in note] != [("2026-11-10_07-00-00", 1, "aperta"), ("vecchia", 2, "aperta")]:
        return f"elenco: numeri o stati sbagliati (una v1 prende il primo libero, mai uno già preso): {[(n['id'], n['numero'], n['stato']) for n in note]}"
    md = cli("note", "elenco", "--md").stdout
    if "# Note sulla finestra di Volta Celeste: 2 aperte" not in md or "`arturo note mostra 2026-11-10_07-00-00`" not in md:
        return f"elenco --md non è il brief: {md[:160]}"
    r = cli("note", "mostra", "1", "--json")
    try:
        m = json.loads(r.stdout)
    except ValueError:
        return f"mostra --json non risponde in JSON: {(r.stderr or r.stdout)[:160]}"
    rq = m["ritaglio"]["riquadro"]
    if m["id"] != "2026-11-10_07-00-00" or not rq or (rq["x"], rq["y"], rq["larghezza"], rq["altezza"], rq["punto"]) != (
            320, 200, 1280, 800, {"x": 1080, "y": 700}):
        return f"il ritaglio non sta attorno al punto, in scala e dentro lo scatto: {m['ritaglio']}"
    if (shutil.which("ffmpeg") or shutil.which("sips")) and m["ritaglio"]["come"] not in ("ffmpeg", "sips"):
        return f"ritaglio.png non nasce con ffmpeg o sips: {m['ritaglio']}"
    preso = cli("note", "prendi", "1")
    if preso.returncode or json.loads((base / "2026-11-10_07-00-00/nota.json").read_text(encoding="utf-8"))["stato"] != "presa":
        return f"prendi non segna la nota come presa: {preso.stderr.strip()[:80]}"
    passi = [preso,
             cli("note", "rispondi", "2026-11-10_07-00-00", "Ci guardo:", "è il padding"),
             cli("note", "risolvi", "2026-11-10_07-00-00", "Padding corretto")]
    if any(p.returncode for p in passi):
        return f"il giro prendi, rispondi, risolvi non passa: {[(p.returncode, p.stderr.strip()[:80]) for p in passi]}"
    d = json.loads((base / "2026-11-10_07-00-00/nota.json").read_text(encoding="utf-8"))
    if (d["stato"], d["riassunto"], d["motivo"], d["numero"], [(v["chi"], v["testo"]) for v in d["filo"]]) != (
            "risolta", "Padding corretto", None, 1, [("federico", "Perché il bottone è storto?"),
                                                    ("claude", "Ci guardo: è il padding"), ("claude", "Padding corretto")]) \
            or not str(d.get("chiusa_quando", "")).endswith("Z"):
        return f"la nota risolta non porta stato, riassunto e filo: {d}"
    t = json.loads(cli("todo", "mostra", str(tid), "--json").stdout)
    tipi = [s["dati"].get("stato") for s in t["storia"] if s["tipo"] == "stato"]
    if t["stato"] != "fatto" or tipi != ["in corso", "fatto"] or not any("Claude sulla nota 1: Ci guardo" in n for n in t["note"]):
        return f"il todo non segue la nota (in corso, nota, fatto): {t['stato']} {tipi} {t['note']}"
    di_nuovo = cli("note", "risolvi", "2026-11-10_07-00-00", "ancora")
    if di_nuovo.returncode != 2 or "già risolta" not in di_nuovo.stderr:
        return "una nota già chiusa si richiude"
    r = cli("note", "scarta", "1", "doppia")
    v = json.loads((base / "vecchia/nota.json").read_text(encoding="utf-8"))
    if r.returncode or (v["stato"], v["motivo"], v["riassunto"], v["versione"]) != ("scartata", "doppia", None, 2):
        return f"scarta non chiude col motivo la nota versione 1: {r.stderr.strip()[:80]} {v}"
    for argv, perche in [(("note", "mostra", "../vecchia"), "un percorso"), (("note", "risolvi", "2026-11-10_07-00-00"), "un risolvi senza testo"),
                         (("note", "boh"), "un verbo sconosciuto")]:
        if cli(*argv).returncode != 2:
            return f"{perche} non esce con 2"
    if cli("note", "elenco").stdout.strip() != "Nessuna nota aperta sulla finestra.":
        return "con tutte le note chiuse l'elenco non lo dice"
    return None


PROVA_CONCORRENTE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import note_finestra as nf
file = nf.cartella() / sys.argv[2] / "nota.json"
originale = nf._sostituisci
chiamate = []
def sostituisci(f, letto, nuovo):
    chiamate.append(1)
    if len(chiamate) == 1:  # il velo scrive proprio adesso, fra la lettura e la scrittura della CLI
        d = json.loads(f.read_text(encoding="utf-8"))
        d["filo"].append({"chi": "federico", "quando": "t", "testo": "dal velo"})
        f.write_text(json.dumps(d), encoding="utf-8")
    return originale(f, letto, nuovo)
nf._sostituisci = sostituisci
nf.aggiorna(sys.argv[2], lambda n: nf.rispondi(n, "dalla CLI"))
nf._sostituisci = originale
print(json.dumps({"chiamate": len(chiamate), "filo": [v["testo"] for v in json.loads(file.read_text(encoding="utf-8"))["filo"]]}))
"""


def hz30(repo: Path, casa: Path) -> str | None:
    env, base = casa_note(casa)
    nota_v2(base, "n1", None)
    r = subprocess.run([sys.executable, "-c", PROVA_CONCORRENTE, str(repo / "bin"), "n1"], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    if r.returncode != 0:
        return f"la scrittura concorrente si rompe: {(r.stderr or r.stdout).strip()[-200:]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["filo"] != ["Perché il bottone è storto?", "dal velo", "dalla CLI"] or g["chiamate"] != 2:
        return f"con il file cambiato fra lettura e scrittura una delle due risposte si perde: {g}"
    if any(p.name.startswith(".nota.") for p in (base / "n1").iterdir()):
        return "la scrittura rifiutata lascia un file temporaneo nella cartella della nota"
    return None


def hz31(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    for testo, pezzo, perche in [
        (ui, "const r = await gestoNota(VERBI[che], n.id, testo);", "i bottoni della scheda non passano da arturo note"),
        (ui, 'const VERBI = { rispondi: "rispondi", risolta: "risolvi", scarta: "scarta" };', "un bottone porta al verbo sbagliato"),
        (dati, 'arturo("note", [verbo, id, "--chi", "federico", "--json", ...(t ? ["--", t] : [])]',
         "gestoNota non chiama arturo note con --chi federico, --json e il testo dopo --")]:
        if pezzo not in testo:
            return perche
    corpo = ui[ui.index("  azione(cx, che) {"):ui.index("  // Un riquadro largo w e alto h")]
    if "writeTextFile" in corpo or "todo([" in corpo:
        return "i bottoni della scheda scrivono ancora nota.json o il todo da sé: due copie del gesto"
    env, base = casa_note(casa)
    arturo = [sys.executable, str(repo / "bin/arturo")]

    def cli(*argv):
        return subprocess.run([*arturo, *argv], capture_output=True, text=True, timeout=120, env=env, cwd=casa)

    def gesto(verbo, ident, testo=""):  # gli argomenti di gestoNota()
        return cli("note", verbo, ident, "--chi", "federico", "--json", *(["--", testo] if testo else []))
    ids = []
    for nome in ("n1", "n2", "n3"):
        r = cli("todo", "aggiungi", "--progetto", "p", "--chi", "io", "--json", "--", f"Nota sulla finestra: {nome}")
        try:
            ids.append(json.loads(r.stdout)["id"])
        except (ValueError, KeyError):
            return f"il todo della nota non nasce: {(r.stderr or r.stdout)[:120]}"
        nota_v2(base, nome, ids[-1])
    r = gesto("rispondi", "n1", "-- è il margine")
    if r.returncode:
        return f"Rispondi del velo non passa: {r.stderr.strip()[:120]}"
    try:
        esito = json.loads(r.stdout)
    except ValueError:
        return f"arturo note con --json non risponde in JSON: {r.stdout[:120]}"
    filo = json.loads((base / "n1/nota.json").read_text(encoding="utf-8"))["filo"]
    t = json.loads(cli("todo", "mostra", str(ids[0]), "--json").stdout)
    if (filo[-1]["chi"], filo[-1]["testo"]) != ("federico", "-- è il margine") \
            or [x for x in t["note"] if "sulla nota" in x] != ["Federico sulla nota 1: -- è il margine"] \
            or not str(esito.get("todo_esito", "")).startswith("Todo #"):
        return f"la risposta di Federico non arriva una volta, sua, su nota e todo: {filo[-1]} {t['note']} {esito.get('todo_esito')}"
    r = gesto("risolvi", "n2")
    d = json.loads((base / "n2/nota.json").read_text(encoding="utf-8"))
    t = json.loads(cli("todo", "mostra", str(ids[1]), "--json").stdout)
    if r.returncode or (d["stato"], d["riassunto"], len(d["filo"])) != ("risolta", None, 1) or t["stato"] != "fatto":
        return f"Risolta senza testo non chiude nota e todo: {r.stderr.strip()[:80]} {d['stato']} {t['stato']}"
    r = gesto("scarta", "n3", "doppia")
    d = json.loads((base / "n3/nota.json").read_text(encoding="utf-8"))
    t = json.loads(cli("todo", "mostra", str(ids[2]), "--json").stdout)
    if r.returncode or (d["stato"], d["motivo"], d["filo"][-1]["chi"]) != ("scartata", "doppia", "federico") or t["stato"] != "scartato":
        return f"Scarta non chiude la nota col motivo o non scarta il todo: {r.stderr.strip()[:80]} {d['stato']} {t['stato']}"
    r = gesto("scarta", "n2", "tardi")
    if r.returncode != 2 or "già risolta" not in r.stderr:
        return f"Scarta su una nota già chiusa da Claude non lo dice: {r.returncode} {r.stderr.strip()[:80]}"
    return None


PROVA_FORMATO = r"""
const m = await import(%s);
console.log(JSON.stringify({ tipi: Object.fromEntries(m.TIPI.map((x) => [x.id, x.etichetta])),
  predefinito: m.TIPO_PREDEFINITO, stati: m.STATI, aperte: [...m.APERTE], vuoto: m.VUOTO }));
"""

FORMATO_PY = r"""
import importlib.util, json, sys
s = importlib.util.spec_from_file_location("note_finestra", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
sys.stdout.reconfigure(encoding="utf-8")  # il banco legge in UTF-8 anche su Windows (#5166)
print(json.dumps({"tipi": m.TIPI, "predefinito": m.TIPO_PREDEFINITO, "stati": m.STATI,
                  "aperte": list(m.APERTE), "vuoto": m.VUOTO}, ensure_ascii=False))
"""


def hz32(repo: Path, casa: Path) -> str | None:
    """Il formato di nota.json vive in due copie, nota.js del mod e bin/note_finestra.py: tipi, stati, stati
    aperti e dove vuoto devono dire lo stesso. L'aiuto e la guida nominano --chi e --json dei verbi."""
    aiuto = subprocess.run([sys.executable, str(repo / "bin/arturo"), "note", "aiuto"],  # il percorso vero, con l'UTF-8
                           capture_output=True, text=True, timeout=30).stdout
    guida = (repo / "docs/volta-celeste.md").read_text(encoding="utf-8")
    for dove, testo in (("l'aiuto di arturo note", aiuto), ("docs/volta-celeste.md", guida)):
        for pezzo in ("--chi", "--json"):
            if pezzo not in testo:
                return f"{dove} non spiega {pezzo}"
    if "dice a Federico" in guida:
        return "la guida parla a Federico invece che a chi usa Arturo"
    py = subprocess.run([sys.executable, "-c", FORMATO_PY, str(repo / "bin/note_finestra.py")],
                        capture_output=True, text=True, timeout=30)
    if py.returncode != 0:
        return f"note_finestra.py non si carica: {(py.stderr or py.stdout).strip()[-160:]}"
    lato_py = json.loads(py.stdout)
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(repo / "shared/volta-celeste/mods/arturo/nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_FORMATO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    lato_js = json.loads(r.stdout.strip().splitlines()[-1])
    diversi = [k for k in lato_js if lato_js[k] != lato_py.get(k)]
    if diversi:
        k = diversi[0]
        return f"nota.js e note_finestra.py non dicono lo stesso su {', '.join(diversi)}: {lato_js[k]} contro {lato_py.get(k)}"
    return None


HERDR_FINTO = r"""
import { readFileSync } from "node:fs";
export const lanciati = [];
export const appHome = () => process.env.HZ_APP;
export const home = () => process.env.HZ_CASA;
export const readTextFile = async (p) => { try { return readFileSync(p, "utf-8"); } catch { return null; } };
export const eseguiti = [];
export const avvisi = [];
const condivisi = JSON.parse(process.env.HZ_SHARED || "{}");
export const exec = async (cmd, args) => {
  eseguiti.push([cmd, ...args]);
  return process.env.HZ_EXEC ? { code: 0, stdout: process.env.HZ_EXEC, stderr: "" } : { code: 1, stdout: "", stderr: "" };
};
export const inviati = [];
// HZ_HC_GET: { <terminale>: [risposta, risposta, ...] } per hc get, una per chiamata (l'ultima resta).
const letture = JSON.parse(process.env.HZ_HC_GET || "{}");
export const hc = async (a) => {
  inviati.push(a);
  const l = a[0] === "get" ? letture[a[1]] : null;
  if (l) return { code: 0, stdout: JSON.stringify(l.length > 1 ? l.shift() : l[0]), stderr: "" };
  return { code: process.env.HZ_HC_ROTTO === a[0] ? 1 : 0, stdout: "", stderr: "" };
};
const finti = JSON.parse(process.env.HZ_HERDR || "{}");
export const spaces = () => finti.spaces ?? [];
export const agents = () => finti.agents ?? [];
export const terminals = () => finti.terminals ?? [];
export const panes = () => finti.panes ?? [];
export const shared = (k) => condivisi[k];
export const setShared = (k, v) => { condivisi[k] = v; };
export const notify = (n) => avvisi.push(n);
export const run = (cmd, a) => {
  lanciati.push({ cmd, ...a });
  // HZ_NASCE: la scheda creata compare fra i terminali, come in Herdr dopo tab.new e space.new
  if (process.env.HZ_NASCE && (cmd === "tab.new" || cmd === "space.new") && a?.argv) {
    (finti.terminals ??= []).push({ address: process.env.HZ_NASCE, argv: a.argv });
    (finti.panes ??= []).push({ terminal: process.env.HZ_NASCE, tab: "tb-nuova" });
  }
};
"""

def mod_dati(repo: Path, mod: Path, dati: str) -> None:
    """dati.js per node: herdr finto, sessioni.js (puro) accanto come .mjs."""
    sessioni = (repo / "shared/volta-celeste/mods/arturo/sessioni.js").read_text(encoding="utf-8")
    (mod / "sessioni.mjs").write_text(sessioni, encoding="utf-8")
    dati = dati.replace('from "herdr";', 'from "./herdr.mjs";').replace('from "./sessioni.js";', 'from "./sessioni.mjs";')
    (mod / "dati.mjs").write_text(dati, encoding="utf-8")
    (mod / "herdr.mjs").write_text(HERDR_FINTO, encoding="utf-8")


PROVA_TROVA = r"""
import { config, radiceDa, chiedi, SUGGERIMENTI } from "./dati.mjs";
import { eseguiti } from "./herdr.mjs";
await chiedi(SUGGERIMENTI.find((s) => s.id === "trova"));
console.log(JSON.stringify({
  radice: (await config()).radice,
  argv: eseguiti,
  win: radiceDa("C:\\Users\\x\\arturo\\bin\\arturo"),
  posix: radiceDa("/Users/x/.claude/bin/arturo"),
  altro: radiceDa("/usr/bin/python3"),
}));
"""


def hz33(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    dati = (repo / "shared/volta-celeste/mods/arturo/dati.js").read_text(encoding="utf-8")
    if 'from "herdr";' not in dati:
        return "dati.js non importa più da herdr: il banco non sa sostituirlo"
    mod = casa / "mod"
    mod.mkdir()
    mod_dati(repo, mod, dati)
    (mod / "prova.mjs").write_text(PROVA_TROVA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    altrove = casa / "copia-di-prova"  # Arturo fuori da ~/.claude, come il worktree di prova sulle macchine di Federico
    bin_ = str(altrove / "bin" / "arturo")
    env = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa")}
    esiti = {}
    for nome, conf in (("nuovo", {"arturo": ["python3", bin_], "radice": str(repo), "base": str(casa)}),
                       ("di prima", {"arturo": ["python3", bin_], "base": str(casa)})):
        (app / "arturo.json").write_text(json.dumps(conf), encoding="utf-8")
        r = subprocess.run([node, str(mod / "prova.mjs")], capture_output=True, text=True, timeout=30, env=env)
        if r.returncode != 0:
            return f"dati.js non gira ({nome}): {(r.stderr or r.stdout).strip()[:160]}"
        esiti[nome] = json.loads(r.stdout.strip().splitlines()[-1])
    nuovo, prima = esiti["nuovo"], esiti["di prima"]
    if nuovo["radice"] != str(repo) or prima["radice"] != str(altrove):
        return f"la cartella di Arturo non viene da arturo.json o dal bin: {nuovo['radice']} {prima['radice']}"
    argv = nuovo["argv"]
    # anche qui la conversazione nasce in background (#5072): volta_sonda.py nasci qui -- <prompt>
    if len(argv) != 1 or argv[0][2:4] != ["nasci", "qui"] or argv[0][-2] != "--":
        return f"il pulsante non fa nascere una conversazione nuova qui: {argv}"
    prompt = argv[0][-1]
    if "{radice}" in prompt or "~/.claude" in prompt:
        return f"il prompt del pulsante non ha la cartella di Arturo: {prompt[:120]}"
    rimandi = [Path(x) for x in re.findall(r"(\S+/trova-progetti\.md)", prompt)]
    if not rimandi or not rimandi[0].is_file() or rimandi[0].resolve() != (repo / "shared/volta-celeste/trova-progetti.md").resolve():
        return f"il prompt non porta a un trova-progetti.md che esiste: {prompt[:160]}"
    if str(altrove) not in prima["argv"][0][-1]:
        return f"con un arturo.json di prima il prompt non usa la cartella del bin: {prima['argv'][0][-1][:120]}"
    casa_arturo = f"{casa / 'casa'}/.claude"
    if (nuovo["win"], nuovo["posix"], nuovo["altro"]) != ("C:\\Users\\x\\arturo", "/Users/x/.claude", casa_arturo):
        return f"radiceDa sbaglia la cartella: {nuovo['win']} {nuovo['posix']} {nuovo['altro']}"
    return None


HC_FINTO = r'''
import json, os, sys
conf = json.loads(os.environ["HZ_HC"])
a = sys.argv[1:]
if "--timeout" in a[:6]:
    i = a.index("--timeout"); del a[i:i + 2]
if os.environ.get("HZ_HC_LOG"):
    with open(os.environ["HZ_HC_LOG"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(a) + "\n")
if a[:3] == ["machine", "ls", "--json"]:
    print(json.dumps({"machines": conf["macchine"]})); sys.exit(0)
stato = os.environ.get("HZ_HC_STATO")
if a[:1] == ["run"]:
    if stato:
        with open(stato, "a", encoding="utf-8") as fh:
            fh.write(a[a.index("--on") + 1] + "\n")
    print(json.dumps({"id": "t9"})); sys.exit(conf.get("run_rc", 0))
if a[:2] == ["exec", "--on"] and a[-1] == "remoto":  # SERVIZIO di volta_sonda.py
    if a[3] not in conf["exec"].get(a[2], {}):
        print(json.dumps({"error": {"kind": "spawn_failed", "message": "cannot start %s" % a[3]}})); sys.exit(1)
    accesi = open(stato, encoding="utf-8").read().split() if stato and os.path.exists(stato) else []
    s = conf.get("servizio", {}).get(a[2])
    if a[2] in accesi:
        s = conf.get("dopo_run", {}).get(a[2], s)
    print(json.dumps(s if s is not None else {"acceso": True, "come": "già acceso"})); sys.exit(0)
if a[:2] == ["exec", "--on"]:
    esito = conf["exec"].get(a[2], {}).get(a[3])
    if esito is None:
        print(json.dumps({"error": {"kind": "spawn_failed", "message": "cannot start %s" % a[3]}})); sys.exit(1)
    print(esito if isinstance(esito, str) else json.dumps(esito)); sys.exit(0)
sys.exit(2)
'''


def hz34(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    # il percorso sta solo in config() di dati.js, e volta.js lo prende da lì
    if "${appHome()}/mods/arturo/volta_sonda.py" not in dati or "esiste(c.volta)" not in volta or "volta_sonda.py`" in volta:
        return "volta.js non lancia volta_sonda.py del mod"
    if "[this.sposta, \"porta-volta\"" not in volta:
        return "volta.js non lascia porta-volta a teletrasporto.py"
    sessione = lambda sid, **k: dict({"sessionId": sid, "kind": "background", "state": "done"}, **k)  # noqa: E731
    conf = {
        "macchine": [
            {"name": "Studio", "target": "studio.lan", "state": "connected"},
            {"name": "Torre", "target": "torre.lan", "state": "connected"},
            {"name": "Server", "target": "server", "state": "connected"},
            {"name": "Pi", "target": "pi", "state": "connected"},
            {"name": "Nuvola", "target": "nuvola", "state": "unreachable", "why": "spenta"},
            {"name": "Lontana", "target": "lontana", "state": "unreachable", "why": "spenta"},
            {"name": "Nuda", "target": "nuda", "state": "connected"},
        ],
        "exec": {
            "Studio": {"python3": {"claude": "/u/.local/bin/claude", "sessioni": [
                sessione("bbbb1111-s", kind="interactive", status="busy", pid=4),
                sessione("bbbb2222-s", state="blocked", waitingFor="permesso")]}},
            "Torre": {"python": {"claude": "C:/u/claude.exe", "sessioni": [sessione("cccc1111-t")]}},
            "Pi": {"python3": {"claude": None, "sessioni": []}},
            "Nuda": {"claude": json.dumps([sessione("dddd1111-n")])},
        },
    }
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    uscita = casa / "sessioni.json"
    uscita.write_text(json.dumps({"macchine": [{"host": "Nuvola"}], "sessioni": [
        {"host": "Nuvola", "id": "eeee1111", "sessionId": "eeee1111-v"}]}), encoding="utf-8")
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]),
           "VOLTA_SONDA_LOCALE": json.dumps({"claude": "/q/claude", "sessioni": [sessione("aaaa1111-q")]})}
    r = subprocess.run([sys.executable, str(mod / "volta_sonda.py"), "volta", "--scrivi", str(uscita)],
                       capture_output=True, text=True, timeout=60, env=env)
    if r.returncode != 0:
        return f"volta_sonda.py esce {r.returncode}: {(r.stderr or r.stdout).strip()[-160:]}"
    d = json.loads(uscita.read_text(encoding="utf-8"))
    host = [m["host"] for m in d["macchine"]]
    if host != ["qui", "Studio", "Torre", "Nuvola", "Nuda"]:
        return f"macchine {host}, attese qui, Studio, Torre, Nuvola, Nuda"
    if [m for m in d["macchine"] if m["host"] == "Nuvola"][0].get("irraggiungibile") != "spenta":
        return "la macchina che non risponde non porta il motivo di Herdr"
    per = {x["id"]: x for x in d["sessioni"]}
    attese = {"aaaa1111": ("qui", "ferma"), "bbbb1111": ("Studio", "lavora"), "bbbb2222": ("Studio", "aspetta"),
              "cccc1111": ("Torre", "ferma"), "dddd1111": ("Nuda", "ferma"), "eeee1111": ("Nuvola", None)}
    if set(per) != set(attese):
        return f"sessioni {sorted(per)}, attese {sorted(attese)}"
    for i, (h, st) in attese.items():
        if per[i]["host"] != h or (st and per[i]["stato"] != st):
            return f"{i}: host {per[i]['host']} stato {per[i].get('stato')}, atteso {h} {st}"
    if not per["eeee1111"].get("vecchia"):
        return "la riga della macchina che non risponde non è segnata vecchia"
    if per["aaaa1111"]["attach"] != ["/q/claude", "attach", "aaaa1111"]:
        return f"aggancio locale {per['aaaa1111']['attach']}"
    if per["cccc1111"]["attach"][1:] != ["-t", "torre.lan", "C:/u/claude.exe", "attach", "cccc1111"]:
        return f"aggancio remoto {per['cccc1111']['attach']}"
    if per["bbbb1111"]["attach"] is not None or per["bbbb1111"]["tipo"] != "interattiva":
        return "un'interattiva ha un aggancio: va prima portata in background"
    return None


CLAUDE_FINTO = r"""#!/bin/sh
{ for a in "$@"; do printf '[%s]' "$a"; done; echo; } >> "$HZ_LOG"
if [ "${1:-}" = --bg ]; then
  if [ -n "${HZ_RIFIUTA:-}" ]; then printf 'Starting background service\342\200\246\n'; echo "Workspace not trusted. Run claude once."; exit 1; fi
  printf 'backgrounded \302\267 abcd1234\n  claude agents             list sessions\n  claude attach abcd1234    open in this terminal\n'
fi
exit 0
"""


# La sonda finta del servizio per volta-claude.sh e .ps1 (#5215): segna la chiamata nel log dei claude
# finti, con HZ_SONDA_PREFISSO davanti, e con HZ_SONDA_ERRORE risponde come un servizio che non parte.
SONDA_FINTA = r"""import json, os, sys
with open(os.environ["HZ_LOG"], "a", encoding="utf-8") as fh:
    fh.write(os.environ.get("HZ_SONDA_PREFISSO", "") + "".join("[%s]" % x for x in sys.argv[1:]) + "\n")
if os.environ.get("HZ_SONDA_ERRORE"):
    print(json.dumps({"errore": "il servizio di Claude non si accende (staccato)"})); sys.exit(1)
print(json.dumps({"come": "gi\u00e0 acceso"}))
"""


def volta_claude(repo: Path, casa: Path, args: list[str], tty: bool = True, **extra: str) -> tuple[list[str], str]:
    finto = casa / "claude-finto"
    finto.write_text(CLAUDE_FINTO, encoding="utf-8", newline="\n")
    sonda = casa / "sonda-finta.py"
    sonda.write_text(SONDA_FINTA, encoding="utf-8")
    log = casa / "chiamate.log"
    log.write_text("", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "HC_TERMINAL_ID", "CLAUDE_QUI", "SSH_CONNECTION")}
    env.update({"VOLTA_CLAUDE_BIN": str(finto) if os.name != "nt" else finto.as_posix(), "HZ_LOG": str(log),
                "VOLTA_SONDA": str(sonda) if os.name != "nt" else sonda.as_posix()})
    if tty:
        env["VOLTA_CLAUDE_TTY"] = "1"
    env.update(extra)
    r = subprocess.run(["sh", str(repo / "shared/volta-celeste/volta-claude.sh"), *args],
                       capture_output=True, text=True, timeout=30, env=env)
    if os.name != "nt":
        os.chmod(finto, 0o755)
    return log.read_text(encoding="utf-8").splitlines(), r.stderr


def hz35(repo: Path, casa: Path) -> str | None:
    if os.name != "nt":
        (casa / "claude-finto").write_text("", encoding="utf-8")
        os.chmod(casa / "claude-finto", 0o755)
    bg = lambda *a: ["[servizio][qui]", "[--bg]" + "".join(f"[{x}]" for x in a), "[attach][abcd1234]"]  # noqa: E731
    qui = lambda *a: ["".join(f"[{x}]" for x in a)]  # noqa: E731
    casi = [
        ("claude nudo", [], {}, True, bg()),
        ("da ssh, senza servizio", ["ciao"], {"SSH_CONNECTION": "10.0.0.2 5000 10.0.0.1 22"}, True, bg("ciao")[1:]),
        ("sonda del servizio assente", [], {"VOLTA_SONDA": "/non/c/e.py"}, True, bg()[1:]),
        ("claude col prompt di /inizio", ["/inizio arturo -- #12 un todo"], {}, True, bg("/inizio arturo -- #12 un todo")),
        ("--resume con l'id", ["--resume", "abc-123"], {}, True, bg("--resume", "abc-123")),
        ("--model e prompt", ["--model", "haiku", "ciao"], {}, True, bg("--model", "haiku", "ciao")),
        ("CLAUDE_QUI=1", [], {"CLAUDE_QUI": "1"}, True, qui()),
        ("sottocomando agents", ["agents", "--json"], {}, True, qui("agents", "--json")),
        ("sottocomando mcp", ["mcp", "list"], {}, True, qui("mcp", "list")),
        ("-p", ["-p", "ciao"], {}, True, qui("-p", "ciao")),
        ("--version", ["--version"], {}, True, qui("--version")),
        ("--resume senza id", ["--resume"], {}, True, qui("--resume")),
        ("--resume senza id prima di un'opzione", ["--resume", "--model", "haiku"], {}, True, qui("--resume", "--model", "haiku")),
        ("--continue", ["-c"], {}, True, qui("-c")),
        ("terminale di Herdr", [], {"HC_TERMINAL_ID": "t3"}, True, qui()),
        ("dentro una sessione Claude", [], {"CLAUDECODE": "1"}, True, qui()),
        ("senza terminale", ["ciao"], {}, False, qui("ciao")),
    ]
    for nome, args, extra, tty, attese in casi:
        chiamate, _ = volta_claude(repo, casa, args, tty, **extra)
        if os.name != "nt" and chiamate != attese:
            return f"{nome}: chiamate {chiamate}, attese {attese}"
        if os.name == "nt" and chiamate != attese and chiamate:
            return f"{nome}: chiamate {chiamate}, attese {attese}"
    chiamate, err = volta_claude(repo, casa, ["ciao"], True, HZ_SONDA_ERRORE="1")
    if os.name != "nt" and chiamate != bg("ciao"):
        return f"servizio che non parte: chiamate {chiamate}, la sessione nasce lo stesso in background"
    if os.name != "nt" and "il servizio di Claude non si accende (" not in err:
        return f"servizio che non parte senza dirlo: {err.strip()[-160:]}"
    chiamate, err = volta_claude(repo, casa, ["ciao"], True, HZ_RIFIUTA="1")
    if chiamate[1:2] != ["[--bg][ciao]"] or chiamate[2:] != ["[ciao]"]:
        return f"--bg rifiutato: chiamate {chiamate}, attese --bg e poi la sessione qui"
    if "non parte in background (Workspace not trusted" not in err:
        return f"--bg rifiutato senza dirlo: {err.strip()[-160:]}"
    _, err = volta_claude(repo, casa, [], True)
    if "claude attach abcd1234 la riapre" not in err:
        return "dopo l'aggancio non dice come riaprire la sessione"
    return None


def hz36(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # su Windows la nascita va nel profilo di PowerShell (HZ37, HZ38): non_gira_qui lo dichiara
    vc = repo / "shared/volta-celeste"
    home = casa / "home"
    home.mkdir()
    app = casa / "app"
    app.mkdir()
    (app / "volta-claude").write_text("#!/bin/sh\necho VOLTA \"$@\"\n", encoding="utf-8", newline="\n")
    os.chmod(app / "volta-claude", 0o755)
    prima = "export A=1\nalias ll='ls -l'"  # senza a capo in fondo
    (home / ".zshrc").write_text(prima, encoding="utf-8", newline="\n")
    (home / ".zshenv").write_text("claude() {\n  command claude \"$@\"\n}\n", encoding="utf-8", newline="\n")
    env = {**os.environ, "HOME": str(home), "SHELL": "/bin/zsh"}
    nascita = lambda *a: subprocess.run(["sh", str(vc / "nascita.sh"), *a], capture_output=True, text=True, timeout=30, env=env)  # noqa: E731
    for _ in range(2):
        r = nascita("metti", str(app))
        if r.returncode != 0:
            return f"nascita.sh metti esce {r.returncode}: {r.stderr.strip()[-160:]}"
    zshrc = (home / ".zshrc").read_text(encoding="utf-8")
    if zshrc.count(">>> Volta Celeste") != 1:
        return f"metti rilanciato scrive il blocco {zshrc.count('>>> Volta Celeste')} volte"
    if not zshrc.startswith(prima + "\n# >>> Volta Celeste"):
        return "il blocco si attacca all'ultima riga del file della persona"
    st = nascita("stato").stdout.splitlines()
    if f"presente {home / '.zshrc'}" not in st or f"funzione {home / '.zshenv'}" not in st:
        return f"stato {st}: attesi il blocco in .zshrc e la funzione della persona in .zshenv"
    if f"funzione {home / '.zshrc'}" in st:
        return "stato scambia la funzione del blocco per una della persona"
    for shell in ("zsh", "bash"):
        if not shutil.which(shell):
            continue
        blocco = home / ".zshrc"
        # senza i file di avvio: il .zshenv della casa finta ha la funzione claude della persona
        nudo = [shell, "-f"] if shell == "zsh" else [shell, "--norc", "--noprofile"]
        r = subprocess.run([*nudo, "-c", f'. "{blocco}"; claude uno due'], capture_output=True, text=True, timeout=30, env=env)
        if r.stdout.strip() != "VOLTA uno due":
            return f"in {shell} il blocco non fa passare claude da volta-claude: {(r.stdout + r.stderr).strip()[-120:]}"
        r = subprocess.run([*nudo, "-c", f'claude() {{ echo MIA; }}; . "{blocco}"; claude'], capture_output=True, text=True, timeout=30, env=env)
        if r.stdout.strip() != "MIA":
            return f"in {shell} il blocco scavalca la funzione claude della persona: {r.stdout.strip()[-80:]}"
    nascita("togli")
    if (home / ".zshrc").read_text(encoding="utf-8") != prima + "\n":
        return "togli non lascia il file della persona com'era"
    if nascita("stato").stdout.splitlines()[0] != "assente":
        return "dopo togli lo stato non dice assente"
    # L'installatore: copia e propone soltanto. La scelta passa da volta-nascita.sh, una strada sola.
    sotto = casa / "inst"
    sotto.mkdir()
    base = {"ARTURO_HERDR_FIRMA": "presente", "SHELL": "/bin/zsh"}
    r = installa(repo, sotto, "mac-arm", base)
    rc = sotto / "home" / ".zshrc"
    if "HERDR NASCITA:" not in r.stdout or rc.exists():
        return f"senza scelta l'installatore non propone la nascita o la accende da solo: {r.stdout[-200:]}"
    for nome in ("volta-claude", "volta-nascita.sh"):
        if not os.access(sotto / "app" / nome, os.X_OK):
            return f"l'installatore non mette {nome} eseguibile nella cartella di Herdr"
    env_i = {**os.environ, "HOME": str(sotto / "home"), "SHELL": "/bin/zsh"}
    installato = lambda *a: subprocess.run(["sh", str(sotto / "app" / "volta-nascita.sh"), *a], capture_output=True, text=True, timeout=30, env=env_i)  # noqa: E731
    installato("metti")
    if not rc.is_file() or f'"{sotto / "app"}/volta-claude"' not in rc.read_text(encoding="utf-8"):
        return "metti senza cartella non punta a volta-claude della sua cartella di Herdr"
    r = installa(repo, sotto, "mac-arm", base)
    if "HERDR NASCITA:" in r.stdout:
        return "con la nascita accesa l'installatore la ripropone"
    installato("no")
    if ">>> Volta Celeste" in rc.read_text(encoding="utf-8"):
        return "dopo no il blocco resta"
    r = installa(repo, sotto, "mac-arm", base)
    if "HERDR NASCITA:" in r.stdout:
        return "dopo un no l'installatore ripropone la nascita"
    installato("metti")
    installato("togli")
    r = installa(repo, sotto, "mac-arm", base)
    if "HERDR NASCITA:" not in r.stdout:
        return "metti dopo un no non dimentica il no: la proposta non torna più"
    (sotto / "home" / ".zshenv").write_text("claude() { command claude \"$@\"; }\n", encoding="utf-8")
    r = installa(repo, sotto, "mac-arm", base)
    if "HERDR NASCITA FUNZIONE: in " not in r.stdout:
        return "l'installatore non dice che la funzione claude della persona vince sul blocco"
    return None


CLAUDE_FINTO_PS = r"""Add-Content -LiteralPath $env:HZ_LOG -Value ('C' + (-join ($args | ForEach-Object { "[$_]" })))
if ($args.Count -gt 0 -and $args[0] -eq '--bg') {
  Write-Output ('Starting background service' + [char]0x2026)  # su stdout: l'ordine con lo stderr non è garantito
  if ($env:HZ_RIFIUTA) { Write-Output 'Workspace not trusted. Run claude once.'; exit 1 }
  Write-Output ('backgrounded ' + [char]0xB7 + ' abcd1234')
  Write-Output '  claude attach abcd1234    open in this terminal'
}
exit 0
"""


def powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def hz37(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta-celeste"
    home = casa / "home"
    home.mkdir()
    app = casa / "app"
    app.mkdir()
    shutil.copy(vc / "nascita.sh", app / "volta-nascita.sh")
    p5 = home / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
    p7 = home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    p5.parent.mkdir(parents=True)
    prima = b"Set-Alias ll Get-ChildItem\r\n$env:A = 1"  # righe di Windows, senza a capo in fondo
    p5.write_bytes(prima)
    env = {**os.environ, "HOME": str(home), "SHELL": "/bin/zsh", "VOLTA_PROFILI_PS": f"{p5}\n{p7}", "VOLTA_POLICY_PS": "RemoteSigned"}
    nascita = lambda *a, **e: subprocess.run(["sh", str(app / "volta-nascita.sh"), *a], capture_output=True, text=True, timeout=60, env={**env, **e})  # noqa: E731
    for _ in range(2):
        r = nascita("metti")
        if r.returncode != 0:
            return f"metti esce {r.returncode}: {r.stderr.strip()[-160:]}"
    for f in (p5, p7):
        if not f.is_file():
            return f"metti non crea il profilo {f.parent.name}"
        b = f.read_bytes()
        if b.count(b">>> Volta Celeste") != 1:
            return f"in {f.parent.name} il blocco c'è {b.count(b'>>> Volta Celeste')} volte"
        if any(c > 127 for c in b):
            return f"il blocco in {f.parent.name} non è solo ASCII: Windows PowerShell 5.1 lo legge storto"
        if b"function global:claude" not in b or b"volta-claude.ps1" not in b:
            return f"il blocco in {f.parent.name} non fa passare claude da volta-claude.ps1"
    if not p5.read_bytes().startswith(prima + b"\n# >>> Volta Celeste"):
        return "il blocco si attacca all'ultima riga del profilo"
    if (home / ".zshrc").exists() and "Volta" in (home / ".zshrc").read_text(encoding="utf-8") and os.name == "nt":
        return "su Windows il blocco va anche nei file di avvio di zsh"
    st = nascita("stato").stdout.splitlines()
    if f"presente {p5}" not in st or f"presente {p7}" not in st:
        return f"stato {st}: attesi i due profili"
    if any(r.startswith("funzione ") for r in st):
        return "stato scambia la funzione del blocco per una della persona"
    # un editor di Windows può risalvare tutto il profilo con le righe di Windows, blocco compreso
    p5.write_bytes(p5.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    nascita("togli")
    if p5.read_bytes() != prima + b"\r\n":
        return "togli non lascia il profilo com'era, o non trova il blocco con le righe di Windows"
    p7.write_text("function Claude { claude.exe @args }\n", encoding="utf-8")
    st = nascita("stato", VOLTA_POLICY_PS="Restricted").stdout.splitlines()
    if f"funzione {p7}" not in st:
        return f"stato non vede la funzione claude della persona nel profilo: {st}"
    if f"policy {p5} Restricted" not in st:
        return f"stato non dice della policy Restricted: {st}"
    sedici = "Set-Alias ll Get-ChildItem\r\n".encode("utf-16")
    p5.write_bytes(sedici)
    r = nascita("metti")
    if p5.read_bytes() != sedici or f"NASCITA UTF16 {p5}" not in r.stdout:
        return "metti tocca un profilo in UTF-16 o non lo dice"
    # L'installatore di Windows copia volta-claude.ps1 e dice della policy.
    sotto = casa / "inst"
    sotto.mkdir()
    q5 = sotto / "home" / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
    r = installa(repo, sotto, "windows", {"VOLTA_PROFILI_PS": str(q5), "VOLTA_POLICY_PS": "Restricted"})
    if not (sotto / "app" / "volta-claude.ps1").is_file():
        return "l'installatore di Windows non copia volta-claude.ps1"
    if "HERDR NASCITA:" not in r.stdout or "HERDR NASCITA POLICY: PowerShell non legge il profilo" not in r.stdout:
        return f"l'installatore di Windows non propone la nascita o non dice della policy: {r.stdout[-240:]}"
    if q5.exists():
        return "l'installatore di Windows scrive il profilo senza la scelta della persona"
    return None


def hz38(repo: Path, casa: Path) -> str | None:
    ps = powershell()
    if not ps:
        return None  # gira dove c'è PowerShell (Windows): non_gira_qui lo dichiara
    vc = repo / "shared/volta-celeste"
    app = casa / "app"
    app.mkdir()
    shutil.copy(vc / "nascita.sh", app / "volta-nascita.sh")
    env = {**os.environ, "HOME": str(casa), "VOLTA_POLICY_PS": "RemoteSigned"}
    nascita = lambda *a, **e: subprocess.run(["sh", str(app / "volta-nascita.sh"), *a], capture_output=True, text=True, timeout=60, env={**env, **e})  # noqa: E731
    # volta-claude.ps1 con un claude finto
    finto = casa / "claude-finto.ps1"
    finto.write_text(CLAUDE_FINTO_PS, encoding="utf-8-sig")
    sonda = casa / "sonda-finta.py"
    sonda.write_text(SONDA_FINTA, encoding="utf-8")
    log = casa / "chiamate.log"
    def vps(args: list[str], **extra: str) -> tuple[list[str], str]:
        log.write_text("", encoding="utf-8")
        e = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "HC_TERMINAL_ID", "CLAUDE_QUI", "SSH_CONNECTION")}
        e.update({"VOLTA_CLAUDE_BIN": str(finto), "HZ_LOG": str(log), "VOLTA_CLAUDE_TTY": "1", "VOLTA_SONDA": str(sonda),
                  "VOLTA_SONDA_PY": sys.executable, "HZ_SONDA_PREFISSO": "C", **extra})
        r = subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(vc / "volta-claude.ps1"), *args],
                           capture_output=True, text=True, timeout=60, env=e, encoding="utf-8", errors="replace")
        return [x[1:] for x in log.read_text(encoding="utf-8-sig").splitlines() if x.startswith("C")], r.stderr
    bg = lambda *a: ["[servizio][qui]", "[--bg]" + "".join(f"[{x}]" for x in a), "[attach][abcd1234]"]  # noqa: E731
    qui = lambda *a: ["".join(f"[{x}]" for x in a)]  # noqa: E731
    casi = [
        ("claude nudo", [], {}, bg()),
        ("da ssh, senza servizio", ["ciao"], {"SSH_CONNECTION": "10.0.0.2 5000 10.0.0.1 22"}, bg("ciao")[1:]),
        ("sonda del servizio assente", [], {"VOLTA_SONDA": str(casa / "non-c-e.py")}, bg()[1:]),
        ("claude col prompt", ["/inizio arturo -- #12 un todo"], {}, bg("/inizio arturo -- #12 un todo")),
        ("--resume con l'id", ["--resume", "abc-123"], {}, bg("--resume", "abc-123")),
        ("CLAUDE_QUI", [], {"CLAUDE_QUI": "1"}, qui()),
        ("sottocomando agents", ["agents", "--json"], {}, qui("agents", "--json")),
        ("-p", ["-p", "ciao"], {}, qui("-p", "ciao")),
        ("--resume senza id", ["--resume"], {}, qui("--resume")),
        ("--output-format=json", ["--output-format=json"], {}, qui("--output-format=json")),
        ("terminale di Herdr", [], {"HC_TERMINAL_ID": "t3"}, qui()),
    ]
    for nome, args, extra, attese in casi:
        chiamate, err = vps(args, **extra)
        if chiamate != attese:
            return f"volta-claude.ps1, {nome}: chiamate {chiamate}, attese {attese} ({err.strip()[-120:]})"
    chiamate, err = vps(["ciao"], HZ_SONDA_ERRORE="1")
    if chiamate != bg("ciao") or "il servizio di Claude non si accende (" not in err:
        return f"volta-claude.ps1, servizio che non parte: chiamate {chiamate} ({err.strip()[-120:]})"
    chiamate, err = vps(["ciao"], HZ_RIFIUTA="1")
    if chiamate != ["[servizio][qui]", "[--bg][ciao]", "[ciao]"]:
        return f"volta-claude.ps1, --bg rifiutato: chiamate {chiamate}"
    if "non parte in background (Workspace not trusted" not in err:
        return f"volta-claude.ps1, --bg rifiutato senza dire perché: {err.strip()[-160:]}"
    _, err = vps([])
    if "claude attach abcd1234 la riapre" not in err:
        return "volta-claude.ps1: dopo l'aggancio non dice come riaprire la sessione"
    # il blocco vero in PowerShell: claude passa da volta-claude.ps1, ma la funzione della persona vince
    (app / "volta-claude.ps1").write_text("Write-Output ('VOLTA ' + ($args -join ' '))\n", encoding="utf-8-sig")
    p6 = casa / "profilo.ps1"
    nascita("metti", VOLTA_PROFILI_PS=str(p6))
    corri = lambda prima: subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"{prima}. '{p6}'; claude uno due"],  # noqa: E731
                                         capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace").stdout.strip()
    if corri("") != "VOLTA uno due":
        return f"in PowerShell il blocco non fa passare claude da volta-claude.ps1: {corri('')[-120:]}"
    if corri("function claude { 'MIA' }; ") != "MIA":
        return "in PowerShell il blocco scavalca la funzione claude della persona"
    return None


PROVA_NASCI = r"""
import { nuova, apri, chiedi, statoSpazio, statiQui, SUGGERIMENTI } from "./dati.mjs";
import { lanciati, eseguiti, avvisi, inviati, spaces } from "./herdr.mjs";
const caso = process.env.HZ_CASO;
const stati = {};
if (caso === "stato") { stati.spazio = statoSpazio(spaces()[0]); stati.qui = statiQui(); stati.niente = statoSpazio(undefined); }
if (caso === "nuova") await nuova("ciao Volta");
else if (caso === "apri") await apri("progetto-x");
else if (caso === "lavoraci") await apri("progetto-x", { id: 42, titolo: "Prova" });
else if (caso === "trova") await chiedi(SUGGERIMENTI.find((s) => s.id === "trova"));
else if (caso === "ricorda") await chiedi(SUGGERIMENTI.find((s) => s.id === "ricorda"));
console.log(JSON.stringify({ lanciati, eseguiti, avvisi, inviati, stati }));
"""


def hz39(repo: Path, casa: Path) -> str | None:
    import base64
    mod = repo / "shared/volta-celeste/mods/arturo"
    sonda = mod / "volta_sonda.py"
    nata = {"id": "ffff1111", "sessionId": "ffff1111-aaaa", "claude": "C:/u/claude.exe", "cartella": "C:/u/ClaudeCode"}
    conf = {
        "macchine": [
            {"name": "Torre", "target": "torre.lan", "state": "connected"},
            {"name": "Studio", "target": "studio.lan", "state": "connected"},
            {"name": "Rotta", "target": "rotta", "state": "connected"},
            {"name": "Nuvola", "target": "nuvola", "state": "unreachable", "why": "spenta"},
        ],
        "exec": {
            "Torre": {"python": nata},  # Windows: python3 non c'è
            "Studio": {"python3": {"errore": "non parte in background: Workspace not trusted"}},
            "Rotta": {"python3": "Traceback: qualcosa si è rotto"},  # partito e caduto: non si ripete
        },
    }
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    log = casa / "hc.log"
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]), "HZ_HC_LOG": str(log)}

    def nasci(*args):
        log.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, str(sonda), "nasci", *args], capture_output=True, text=True, timeout=60, env=env)
        chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), chiamate
        except (ValueError, IndexError):
            return r.returncode, {"uscita": (r.stderr or r.stdout).strip()[-160:]}, chiamate

    rc, d, ch = nasci("Torre", "--progetto", "progetto-x", "--", 'ciao "Volta"', "àccenti")
    if rc != 0 or d.get("attach") is None:
        return f"nasci su Torre: rc {rc}, {d}"
    if d["attach"][1:] != ["-t", "torre.lan", "C:/u/claude.exe", "attach", "ffff1111"] or d["id"] != "ffff1111":
        return f"nasci su Torre: aggancio {d['attach']}"
    if (d["sessionId"], d["macchina"], d["progetto"]) != ("ffff1111-aaaa", "Torre", "progetto-x"):
        return f"nasci su Torre: {d}"
    exe = [c for c in ch if c[:2] == ["exec", "--on"] and c[-1] != "remoto"]
    if [c[3] for c in exe] != ["python3", "python"] or any(c[2] != "Torre" for c in exe):
        return f"nasci su Torre: chiamate {[c[:4] for c in exe]}, attese python3 poi python su Torre"
    arg = json.loads(base64.b64decode(exe[-1][-1]).decode("utf-8"))
    if arg != {"prompt": 'ciao "Volta" àccenti', "progetto": "progetto-x"}:
        return f"prompt e progetto non arrivano intatti: {arg}"
    rc, d, ch = nasci("Studio", "--", "ciao")
    if rc == 0 or "Workspace not trusted" not in d.get("errore", ""):
        return f"--bg rifiutato su Studio: rc {rc}, {d}"
    if len([c for c in ch if c[:2] == ["exec", "--on"] and c[-1] != "remoto"]) != 1:
        return "dopo un errore detto dalla macchina nasci riprova con un altro Python"
    rc, d, ch = nasci("Rotta")
    if rc == 0 or "errore" not in d:
        return f"un Python partito e caduto non dà errore: {d}"
    if [c[3] for c in ch if c[:2] == ["exec", "--on"] and c[-1] != "remoto"] != ["python3"]:
        return "un Python partito e caduto si ripete con python: può far nascere due sessioni"
    for nome, atteso in (("Nuvola", "spenta"), ("Fantasma", "non è fra le macchine")):
        rc, d, ch = nasci(nome, "--", "x")
        if rc == 0 or atteso not in d.get("errore", "") or any(c[:2] == ["exec", "--on"] for c in ch):
            return f"nasci su {nome}: rc {rc}, {d}"
    # Su questa macchina, con un claude finto: la base viene dall'arturo.json di HERDR_APP_HOME, come
    # per installa-herdr.sh. Il claude finto è uno script con shebang: su Windows il caso si salta.
    if os.name != "nt":
        fbin, fapp, fbase, fcasa = casa / "fbin", casa / "fapp", casa / "fbase", casa / "fcasa"
        for d_ in (fbin, fapp, fbase, fcasa):
            d_.mkdir()
        (fapp / "arturo.json").write_text(json.dumps({"base": str(fbase)}), encoding="utf-8")
        dove_log = casa / "fcwd.log"
        fc = fbin / "claude"
        fc.write_text("#!/bin/sh\n[ \"$1\" = agents ] && { echo '[]'; exit 0; }\n[ \"$1\" = daemon ] && { echo 'control.sock: reachable'; exit 0; }\npwd > %s\necho 'claude attach abcd1234'\n" % shlex.quote(str(dove_log)), encoding="utf-8")
        fc.chmod(0o755)
        e = {**os.environ, "PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "HERDR_APP_HOME": str(fapp)}
        r = subprocess.run([sys.executable, str(sonda), "nasci", "qui", "--", "ciao"], capture_output=True, text=True, timeout=60, env=e)
        try:
            d = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            d = {"uscita": (r.stderr or r.stdout).strip()[-160:]}
        if d.get("id") != "abcd1234" or d.get("attach") != [str(fc), "attach", "abcd1234"]:
            return f"nasci qui con un claude finto: {d}"
        if os.path.realpath(d.get("cartella") or "") != os.path.realpath(fbase) or not dove_log.exists() \
                or os.path.realpath(dove_log.read_text(encoding="utf-8").strip()) != os.path.realpath(fbase):
            return f"nasci non parte nella base di HERDR_APP_HOME/arturo.json: {d.get('cartella')}"

    # Volta: Nuova richiesta, Apri un progetto e i suggerimenti, con node
    node = shutil.which("node")
    if not node:
        return None
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_NASCI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    esito_ok = json.dumps({"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]})
    macchine = [{"host": "qui", "macchina": "Questa", "questa": True}, {"host": "Torre", "macchina": "Torre", "giu": False}]

    def volta(caso, dove, uscita=esito_ok, herdr=None, cartella=app, stati=None):
        e = {**os.environ, "HZ_APP": str(cartella), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": uscita,
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": macchine, "arturo.dove": dove, "arturo.volta.stati": stati or {}}),
             "HZ_HERDR": json.dumps(herdr or {})}
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    try:
        v = volta("nuova", "Torre")
        if not v["eseguiti"] or v["eseguiti"][0][0] != "python9" or v["eseguiti"][0][2:] != ["nasci", "Torre", "--", "ciao Volta"]:
            return f"Nuova richiesta su Torre non chiama volta_sonda.py nasci: {v['eseguiti']}"
        if not v["eseguiti"][0][1].endswith("mods/arturo/volta_sonda.py"):
            return f"Nuova richiesta lancia {v['eseguiti'][0][1]}, non volta_sonda.py del mod"
        if len(v["lanciati"]) != 1 or v["lanciati"][0].get("argv") != ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]:
            return f"la sessione nata su Torre non si aggancia qui: {v['lanciati']}"
        v = volta("apri", "Torre")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "Torre", "--progetto", "progetto-x", "--", "/inizio progetto-x"]:
            return f"Apri un progetto su Torre: {v['eseguiti']}"
        if v["lanciati"][0].get("name") != "progetto-x":
            return f"la sessione del progetto non nasce nello spazio del progetto: {v['lanciati']}"
        v = volta("nuova", "Torre", json.dumps({"errore": "Torre non risponde: spenta"}))
        if v["lanciati"] or not v["avvisi"] or "spenta" not in v["avvisi"][0].get("body", ""):
            return f"una nascita fallita non lo dice: {v}"
        # anche qui la sessione nasce in background e si aggancia (#5072)
        v = volta("nuova", "Spenta")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "qui", "--", "ciao Volta"] or len(v["lanciati"]) != 1:
            return f"con una macchina che Volta non elenca la richiesta non nasce qui in background: {v}"
        v = volta("apri", "qui")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "qui", "--progetto", "progetto-x", "--", "/inizio progetto-x"]:
            return f"Apri un progetto qui non nasce in background: {v['eseguiti']}"
        if v["lanciati"][0].get("name") != "progetto-x" or v["lanciati"][0].get("folder") != str(casa / "casa"):
            return f"la sessione nata qui non si aggancia nello spazio del progetto dalla home: {v['lanciati']}"
        v = volta("trova", "Torre")
        if not v["eseguiti"] or v["eseguiti"][0][2:4] != ["nasci", "qui"]:
            return f"Trova i miei progetti va su un'altra macchina: {v}"
        v = volta("ricorda", "Torre")
        if not v["eseguiti"] or v["eseguiti"][0][2:4] != ["nasci", "qui"]:
            return f"Ricordami una cosa senza conversazione va su un'altra macchina: {v}"
        # "volta" in arturo.json vale anche per la nascita: un solo percorso di volta_sonda.py
        prova = casa / "app-prova"
        prova.mkdir()
        (prova / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "base": "/base", "volta": "/prova/volta_sonda.py"}), encoding="utf-8")
        v = volta("nuova", "Torre", cartella=prova)
        if not v["eseguiti"] or v["eseguiti"][0][1] != "/prova/volta_sonda.py":
            return f"la nascita ignora \"volta\" di arturo.json: {v['eseguiti']}"
        # Lavoraci con lo spazio di una sessione nata altrove: Herdr non ci vede un agente, si scrive
        # nella scheda che la aggancia invece di dire che la sessione è chiusa
        agganciato = {"spaces": [{"id": "s1", "name": "progetto-x", "tabs": [{"id": "tb0", "name": "Shell"}, {"id": "tb1", "name": "Progetto x"}]}],
                      "panes": [{"terminal": "t3", "tab": "tb0"}, {"terminal": "t7", "tab": "tb1"}],
                      "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]}]}
        v = volta("lavoraci", "Torre", herdr=agganciato)
        if v["avvisi"] or v["inviati"] != [["send", "t7", "Lavoriamo sul todo #42: Prova"]]:
            return f"Lavoraci su uno spazio agganciato non scrive nella sua scheda: {v['inviati']}, {v['avvisi']}"
        if {"cmd": "tab.select", "id": "tb1"} not in v["lanciati"] or v["eseguiti"]:
            return f"Lavoraci su uno spazio agganciato non porta alla sua scheda: {v['lanciati']}"
        senza = {**agganciato, "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["zsh"]}]}
        v = volta("lavoraci", "Torre", herdr=senza)
        if v["inviati"] or not v["avvisi"] or "chiusa" not in v["avvisi"][0].get("title", ""):
            return f"uno spazio senza sessione non dice che è chiusa: {v}"
        # #5072: lo stato di una scheda agganciata viene dall'ultima lettura di Volta (arturo.volta.stati)
        stati = {"ffff1111": {"stato": "aspetta", "host": "qui"}, "aaaa2222": {"stato": "lavora", "host": "Torre"}}
        v = volta("stato", "qui", herdr=agganciato, stati=stati)
        if v["stati"] != {"spazio": "blocked", "qui": {"ffff1111": "aspetta"}, "niente": None}:
            return f"lo stato di una sessione agganciata non viene da Volta: {v['stati']}"
        # due schede agganciate nello stesso spazio: conta quella attiva
        due = {"spaces": [{"id": "s1", "name": "Volta", "tabs": [{"id": "tb0", "name": "Altra"}, {"id": "tb1", "name": "Questa", "active": True}]}],
               "panes": [{"terminal": "t3", "tab": "tb0"}, {"terminal": "t7", "tab": "tb1"}],
               "terminals": [{"address": "t3", "argv": ["ssh", "-t", "torre.lan", "claude", "attach", "aaaa2222"]},
                             {"address": "t7", "argv": ["claude", "attach", "ffff1111"]}]}
        if volta("stato", "qui", herdr=due, stati=stati)["stati"]["spazio"] != "blocked":
            return "con due schede agganciate lo stato non viene da quella attiva"
        lavora = {**agganciato, "spaces": [{**agganciato["spaces"][0], "status": "working"}]}
        if volta("stato", "qui", herdr=lavora, stati=stati)["stati"]["spazio"] != "working":
            return "lo stato di Herdr non vince su quello di Volta"
        v = volta("lavoraci", "Torre", herdr=agganciato, stati=stati)
        if v["inviati"] or not v["avvisi"] or "aspetta" not in v["avvisi"][0].get("title", ""):
            return f"Lavoraci scrive in una sessione agganciata che aspetta una risposta: {v}"
        attivo = {**agganciato, "spaces": [{**agganciato["spaces"][0], "active": True,
                                            "tabs": [{"id": "tb0", "name": "Shell"}, {"id": "tb1", "name": "Progetto x", "active": True}]}]}
        v = volta("ricorda", "Torre", herdr=attivo)
        if v["eseguiti"] or len(v["inviati"]) != 1 or v["inviati"][0][:2] != ["send", "t7"]:
            return f"Ricordami una cosa non scrive nella sessione agganciata aperta: {v['inviati']}, {v['eseguiti']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    if "nasceSu(t)" not in (mod / "testata.js").read_text(encoding="utf-8"):
        return "il benvenuto non mostra Nasce su, ma la sua Nuova richiesta la segue"
    # #5072: barra, testata e todo leggono lo stato di uno spazio da statoSpazio(), anche agganciato
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    for file, pezzo in (("dati.js", "stato: statoSpazio(s)"), ("testata.js", "const st = statoSpazio(s);"),
                        ("todo.js", "statoSpazio(spazio(p))"), ("todo.js", "    const st = statoSpazio(s);"),
                        ("barra.js", '|| Object.values(statiQui()).includes("aspetta")'), ("barra.js", "`|${JSON.stringify(statiQui())}|")):
        if pezzo not in (dj if file == "dati.js" else (mod / file).read_text(encoding="utf-8")):
            return f"{file} non legge lo stato di Volta per le sessioni agganciate: manca {pezzo}"
    return None



HC_FINTO_AZIONE = r"""import json, os, sys
with open(os.environ["HZ_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
print("stopped " + sys.argv[-1])
"""

CLAUDE_FINTO_AZIONE = r"""#!/bin/sh
printf '%s\n' "$*" >> "$HZ_LOG"
if [ "$1" = logs ]; then printf 'Sta\033[5Glavorando\033[15Gsul\033[19Gdeck\n\033[2Cpronto\nChecking for updates\n'; exit 0; fi
if [ "$1" = rm ] && [ -n "${HZ_RIFIUTA:-}" ]; then echo "has unpushed commits" >&2; exit 1; fi
echo "$1 ok"
"""

PROVA_GESTI = """
import * as m from %s;
const bg = (stato, altro = {}) => ({ tipo: "background", stato, host: "qui", sessionId: "s-" + stato, id: stato.slice(0, 4), ...altro });
const verbi = (s) => m.azioni(s).map((a) => a.verbo + (a.conferma ? "!" : ""));
const prima = { sessioni: [bg("lavora"), bg("aspetta"), bg("ferma", { sessionId: "s-x" })] };
const dopo = { sessioni: [bg("aspetta", { sessionId: "s-lavora" }), bg("aspetta"), bg("aspetta", { sessionId: "s-x", vecchia: true }), bg("aspetta", { sessionId: "s-nuova" })] };
console.log(JSON.stringify({
  lavora: verbi(bg("lavora")), aspetta: verbi(bg("aspetta")), ferma: verbi(bg("ferma")), errore: verbi(bg("errore")),
  interattiva: verbi({ ...bg("ferma"), tipo: "interattiva" }), vecchia: verbi(bg("ferma", { vecchia: true })),
  nuove: m.nuoveInAttesa(prima, dopo).map((s) => s.sessionId), primaLettura: m.nuoveInAttesa(null, dopo).length,
  stati: m.statiCorti({ sessioni: [bg("lavora"), bg("ferma", { id: "vv", vecchia: true })] }),
}));
"""


def hz40(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    sonda = mod / "volta_sonda.py"
    log = casa / "log"
    log.write_text("", encoding="utf-8")
    hcf = casa / "hc_finto.py"
    hcf.write_text(HC_FINTO_AZIONE, encoding="utf-8")
    bindir = casa / "bin"
    bindir.mkdir()
    env = {**os.environ, "HZ_LOG": str(log), "VOLTA_HC": json.dumps([sys.executable, str(hcf)]), "PYTHONIOENCODING": "utf-8"}
    if os.name != "nt":
        cl = bindir / "claude"
        cl.write_text(CLAUDE_FINTO_AZIONE, encoding="utf-8")
        os.chmod(cl, 0o755)
        env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    az = lambda *a, **e: subprocess.run([sys.executable, str(sonda), "azione", *a], capture_output=True, text=True, timeout=60, env={**env, **e})  # noqa: E731
    r = az("Studio", "stop", "abcd1234")
    chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.startswith("[")]
    if chiamate != [["exec", "--on", "Studio", "--timeout", "55", "claude", "stop", "abcd1234"]]:
        return f"azione su un'altra macchina: hc riceve {chiamate}, atteso exec --on Studio --timeout 55 claude stop abcd1234"
    if json.loads(r.stdout.strip().splitlines()[-1]).get("ok") is not True:
        return f"azione riuscita senza ok: {r.stdout.strip()[-120:]}"
    log.write_text("", encoding="utf-8")
    for strano in (["Studio", "kill", "abcd1234"], ["Studio", "stop", "abcd;rm -rf"], ["Studio", "stop", "--all"]):
        r = az(*strano)
        if r.returncode == 0 or "errore" not in r.stdout or log.read_text(encoding="utf-8").strip():
            return f"azione {strano} non rifiutata, o lanciata lo stesso"
    if os.name != "nt":
        r = az("qui", "logs", "abcd1234")
        righe = json.loads(r.stdout.strip().splitlines()[-1]).get("righe")
        if righe != ["Sta lavorando sul deck", "  pronto"]:
            return f"anteprima {righe}: attese le parole spaziate dai movimenti del cursore, senza Checking for updates"
        r = az("qui", "rm", "abcd1234", HZ_RIFIUTA="1")
        if r.returncode == 0 or "has unpushed commits" not in r.stdout:
            return f"rm rifiutato da claude senza il suo motivo: {r.stdout.strip()[-120:]}"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_GESTI % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        attesi = {"lavora": ["logs", "stop"], "aspetta": ["logs", "stop"], "ferma": ["logs", "rm!"], "errore": ["logs", "respawn", "rm!"],
                  "interattiva": [], "vecchia": [], "nuove": ["s-lavora", "s-nuova"], "primaLettura": 0,
                  "stati": {"lavo": {"stato": "lavora", "host": "qui"}}}
        for k, v in attesi.items():
            if d.get(k) != v:
                return f"sessioni.js {k}: {d.get(k)}, atteso {v}"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("azioni(s)", "nuoveInAttesa(prima, this.dati)", 'setShared("arturo.volta.stati"', "azioneSessione(s, a.verbo)"):
        if pezzo not in vj:
            return f"volta.js non usa {pezzo}"
    if '[c.volta, "azione", s.host, verbo, s.id]' not in (mod / "dati.js").read_text(encoding="utf-8"):
        return "dati.js non passa da volta_sonda.py azione"
    return None

# Il claude finto di HZ41: daemon status risponde solo dopo un daemon run, che segna se è nato in una
# sessione sua (staccato) e in quale cartella.
CLAUDE_FINTO_SERVIZIO = r"""#!/usr/bin/env python3
import json, os, sys
log = os.environ["HZ_LOG"]
acceso = os.path.join(os.path.dirname(log), "acceso")
with open(log, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"argv": sys.argv[1:], "staccato": os.getsid(0) == os.getpid(), "cwd": os.getcwd()}) + "\n")
if sys.argv[1:3] == ["daemon", "status"]:
    print("control.sock: reachable" if os.path.exists(acceso) or os.environ.get("HZ_ACCESO") else "not running\n  control.sock: unreachable")
elif sys.argv[1:3] == ["daemon", "run"]:
    open(acceso, "w").close()
"""


def hz41(repo: Path, casa: Path) -> str | None:
    sonda = repo / "shared/volta-celeste/mods/arturo/volta_sonda.py"
    nata = {"id": "ffff1111", "sessionId": "ffff1111-aaaa", "claude": "C:/u/claude.exe", "cartella": "C:/u/ClaudeCode"}
    conf = {
        "macchine": [{"name": n, "target": n.lower(), "state": "connected"} for n in ("Torre", "Win", "Rotto", "Muto")],
        "exec": {"Torre": {"python": nata}, "Win": {"python": nata, "claude": "respawned ffff1111"},
                 "Rotto": {"python3": nata, "claude": "respawned ffff1111"}, "Muto": {"python3": nata}},
        "servizio": {"Win": {"serve": "hc-run"}, "Rotto": {"errore": "Claude Code non c'è su questa macchina"},
                     "Muto": {"serve": "hc-run"}},
        "dopo_run": {"Win": {"acceso": True, "come": "già acceso"}},
    }
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    log, stato = casa / "hc.log", casa / "hc.stato"
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]),
           "HZ_HC_LOG": str(log), "HZ_HC_STATO": str(stato)}

    def lancia(*args):
        log.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, str(sonda), *args], capture_output=True, text=True, timeout=90, env=env)
        chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), chiamate
        except (ValueError, IndexError):
            return r.returncode, {"uscita": (r.stderr or r.stdout).strip()[-160:]}, chiamate

    rc, d, ch = lancia("servizio", "Torre")
    if rc != 0 or d.get("come") != "già acceso" or [c[3] for c in ch if c[:2] == ["exec", "--on"]] != ["python3", "python"]:
        return f"servizio su Torre acceso: rc {rc}, {d}, {ch}"
    if any(c[:1] == ["run"] for c in ch):
        return "un servizio che risponde non si riaccende"
    rc, d, ch = lancia("servizio", "Win")
    corsa = [c for c in ch if c[:1] == ["run"]]
    if rc != 0 or d.get("come") != "terminale di Herdr":
        return f"Windows senza attività: il servizio non nasce con hc run: rc {rc}, {d}"
    if corsa != [["run", "--on", "Win", "--name", "servizio-claude", "--no-parent", "--rm", "--bg", "claude", "daemon", "run"]]:
        return f"hc run del servizio: {corsa}"
    rc, d, ch = lancia("servizio", "Muto")
    if rc == 0 or "non risponde ancora" not in d.get("errore", ""):
        return f"un servizio acceso con hc run che non risponde deve dare errore: rc {rc}, {d}"
    # nasci passa prima dal servizio, e senza servizio non fa nascere niente
    rc, d, ch = lancia("nasci", "Rotto", "--", "ciao")
    if rc == 0 or "servizio di Claude non parte su Rotto" not in d.get("errore", ""):
        return f"nasci su Rotto senza servizio: rc {rc}, {d}"
    if any(c[:2] == ["exec", "--on"] and c[-1] != "remoto" for c in ch):
        return "nasci fa nascere la sessione anche se il servizio non parte"
    stato.unlink(missing_ok=True)
    rc, d, ch = lancia("nasci", "Win", "--", "ciao")
    if rc != 0 or d.get("id") != "ffff1111":
        return f"nasci su Win col servizio da accendere: rc {rc}, {d}"
    giro = [("run" if c[:1] == ["run"] else "servizio" if c[-1] == "remoto" else "nasci") for c in ch if c[:1] == ["run"] or c[:2] == ["exec", "--on"]]
    if giro.index("run") > giro.index("nasci") or giro[-1] != "nasci":
        return f"nasci non accende il servizio prima della sessione: {giro}"
    # Riavvia passa dal servizio come nasci (#5215); gli altri gesti no
    rc, d, ch = lancia("azione", "Rotto", "respawn", "ffff1111")
    if rc == 0 or "servizio di Claude non parte su Rotto" not in d.get("errore", ""):
        return f"Riavvia su Rotto senza servizio: rc {rc}, {d}"
    if any(c[:2] == ["exec", "--on"] and "respawn" in c for c in ch):
        return "Riavvia lancia claude respawn anche se il servizio non parte"
    stato.unlink(missing_ok=True)
    rc, d, ch = lancia("azione", "Win", "respawn", "ffff1111")
    giro = [("run" if c[:1] == ["run"] else "respawn" if "respawn" in c else "servizio") for c in ch if c[:1] == ["run"] or c[:2] == ["exec", "--on"]]
    if rc != 0 or d.get("ok") is not True or "run" not in giro or giro.index("run") > giro.index("respawn") or giro[-1] != "respawn":
        return f"Riavvia su Win non accende il servizio prima: rc {rc}, {d}, {giro}"
    rc, d, ch = lancia("azione", "Rotto", "stop", "ffff1111")
    if rc != 0 or any(c[-1] == "remoto" for c in ch):
        return f"Ferma non deve passare dal servizio: rc {rc}, {d}, {ch}"
    # SERVIZIO vero su questa macchina, con un claude finto (script con shebang: su Windows si salta)
    if os.name == "nt":
        return None
    fbin, fcasa = casa / "sbin", casa / "scasa"
    fbin.mkdir(); fcasa.mkdir()
    fc = fbin / "claude"
    fc.write_text(CLAUDE_FINTO_SERVIZIO.replace("/usr/bin/env python3", sys.executable), encoding="utf-8")
    fc.chmod(0o755)
    slog = casa / "s" / "claude.log"
    slog.parent.mkdir()
    e = {**os.environ, "PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "HZ_LOG": str(slog)}
    e.pop("VOLTA_HC", None)

    def qui(**extra):
        slog.write_text("", encoding="utf-8")
        (slog.parent / "acceso").unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(sonda), "servizio", "qui"], capture_output=True, text=True, timeout=60, env={**e, **extra})
        for _ in range(20):  # il servizio staccato scrive il suo log da solo
            righe = [json.loads(x) for x in slog.read_text(encoding="utf-8").splitlines() if x.strip()]
            if r.returncode != 0 or any(x["argv"][:2] == ["daemon", "run"] for x in righe) or extra:
                break
            time.sleep(0.1)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1]), righe
        except (ValueError, IndexError):
            return {"uscita": (r.stderr or r.stdout).strip()[-160:]}, righe

    d, righe = qui()
    corse = [x for x in righe if x["argv"][:2] == ["daemon", "run"]]
    if d.get("come") != "staccato" or len(corse) != 1:
        return f"servizio qui spento: {d}, {righe}"
    if not corse[0]["staccato"] or os.path.realpath(corse[0]["cwd"]) != os.path.realpath(fcasa):
        return f"il servizio non nasce staccato nella home: {corse[0]}"
    d, righe = qui(HZ_ACCESO="1")
    if d.get("come") != "già acceso" or any(x["argv"][:2] == ["daemon", "run"] for x in righe):
        return f"servizio qui già acceso: {d}, {righe}"
    return None


# HZ42 carica la sonda come modulo, con un tetto del servizio corto, e chiede il servizio a Muto: hc run
# parte, ma il servizio non risponde mai. Stampa l'esito e i secondi passati.
SERVIZIO_CORTO = r"""
import importlib.util, json, sys, time
spec = importlib.util.spec_from_file_location("volta_sonda", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ATTESA_SERVIZIO = 8
t0 = time.monotonic()
d = m.servizio("Muto")
print(json.dumps({"esito": d, "secondi": time.monotonic() - t0}))
"""


def hz42(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    sonda = mod / "volta_sonda.py"
    import ast  # noqa: PLC0415
    costanti = {n.targets[0].id: n.value.value for n in ast.parse(sonda.read_text(encoding="utf-8")).body
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.startswith("ATTESA_") and isinstance(n.value, ast.Constant)}
    if set(costanti) != {"ATTESA_MACCHINE", "ATTESA_SERVIZIO", "ATTESA_NASCITA", "ATTESA_AZIONE"}:
        return f"le attese della nascita in volta_sonda.py: {costanti}"
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    # i gesti (#5215): Riavvia aspetta servizio più azione più 30 s, gli altri azione più 30 s
    gesto = dati[dati.index("async function azioneSessione("):]
    gesto = gesto[:gesto.index("\n}\n")]
    t = re.search(r'timeout:\s*verbo === "respawn" \? (\d+) : (\d+)', gesto)
    if not t:
        return "dati.js (azioneSessione) non dà a Riavvia un'attesa sua"
    if int(t.group(1)) < (costanti["ATTESA_SERVIZIO"] + costanti["ATTESA_AZIONE"] + 30) * 1000 or int(t.group(2)) < (costanti["ATTESA_AZIONE"] + 30) * 1000:
        return f"Volta aspetta i gesti {t.groups()} ms, ma la sonda può metterci di più"
    corpo = dati[dati.index("async function nasciSu("):]
    corpo = corpo[:corpo.index("\n}\n")]
    attese = [int(x) for x in re.findall(r"timeout:\s*(\d+)", corpo)]
    somma = costanti["ATTESA_MACCHINE"] + costanti["ATTESA_SERVIZIO"] + costanti["ATTESA_NASCITA"]
    # 30 s di margine: avvio dei Python, il secondo Python dopo uno che non parte, le pause del servizio
    if len(attese) != 1 or attese[0] < (somma + 30) * 1000:
        return f"Volta aspetta la nascita {attese} ms, ma la sonda può metterci fino a {somma} s"
    conf = {"macchine": [{"name": "Muto", "target": "muto", "state": "connected"}],
            "exec": {"Muto": {"python3": {}}}, "servizio": {"Muto": {"serve": "hc-run"}}}
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)])}
    r = subprocess.run([sys.executable, "-c", SERVIZIO_CORTO, str(sonda)], capture_output=True, text=True, timeout=60, env=env)
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return f"servizio con il tetto corto: {(r.stderr or r.stdout).strip()[-160:]}"
    if "in 8 s" not in d["esito"].get("errore", "") or d["secondi"] > 8:
        return f"il servizio non si ferma al suo tetto: {d}"
    return None


def hz43(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta-celeste"
    gui = (vc / "servizi-gui.sh").read_text(encoding="utf-8")
    ps1 = (vc / "servizio-claude.ps1").read_text(encoding="utf-8-sig")
    installa = (vc / "installa-herdr.sh").read_text(encoding="utf-8")
    sonda = (vc / "mods/arturo/volta_sonda.py").read_text(encoding="utf-8")
    prefisso = re.search(r"^PREFISSO=(\S+)$", gui, re.M)
    attivita = re.search(r'^\$nome = "([^"]+)"', ps1, re.M)
    if not prefisso or "plist claude-daemon true" not in gui or not attivita:
        return "servizi-gui.sh o servizio-claude.ps1 non dicono più il nome del servizio"
    agente, attivita = prefisso.group(1) + ".claude-daemon", attivita.group(1)
    attese = [
        ("installa-herdr.sh", installa, f"Library/LaunchAgents/{agente}.plist"),
        ("installa-herdr.sh", installa, f"schtasks /query /tn {attivita} "),
        ("volta_sonda.py", sonda, f'etichetta = "{agente}"'),
        ("volta_sonda.py", sonda, f'attivita = "{attivita}"'),
    ]
    for nome, testo, atteso in attese:
        if atteso not in testo:
            return f"{nome} non usa il nome del servizio fisso: manca {atteso!r}"
    setup = (repo / "shared/setup-herdr.md").read_text(encoding="utf-8")
    righe = set(re.findall(r'say "(HERDR [A-Z0-9]+(?: [A-Z0-9]+)*):', installa))
    if len(righe) < 5:
        return f"le righe HERDR dell'installazione non si leggono più: {sorted(righe)}"
    senza = sorted(r for r in righe if f"`{r}`" not in setup)
    if senza:
        return f"/setup non sa cosa fare delle righe {senza} (shared/setup-herdr.md)"
    return None


# Il claude finto di HZ44: agents --json con e senza --all, come il 2.1.317 (le chiuse solo con --all).
# HZ_SENZA_ALL fa il Claude vecchio, che non conosce --all.
CLAUDE_FINTO_ELENCO = r"""#!/usr/bin/env python3
import json, os, sys, time
ora = time.time() * 1000
giorno = 86400 * 1000
def b(i, stato, eta):
    return {"id": i, "sessionId": i + "-x", "kind": "background", "state": stato, "startedAt": ora - eta, "cwd": "/p"}
viste = [{"id": "inter", "sessionId": "inter-x", "kind": "interactive", "status": "idle", "cwd": "/p"}, b("fatta", "done", 3600000)]
chiuse = [b("fermata", "stopped", 3600000), b("rotta", "failed", giorno), b("vecchia", "stopped", 10 * giorno)]
if sys.argv[1:2] == ["agents"]:
    if "--all" in sys.argv:
        if os.environ.get("HZ_SENZA_ALL"):
            print("error: unknown option '--all'", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(viste + chiuse))
    else:
        print(json.dumps(viste))
"""


def hz44(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    altro, gesto, clic = bj.find('c.startsWith("volta-altro-")'), bj.find("/^volta-gesto-[a-z]+-/.test(c)"), bj.find('c.startsWith("volta-")')
    if min(altro, gesto) < 0 or clic < 0 or max(altro, gesto) > clic:
        return "barra.js non legge volta-altro- e volta-gesto- prima di volta-<id>"
    if "this.volta.altroId(c.slice(12), cx)" not in bj or "this.volta.gestoId(verbo, id, cx)" not in bj:
        return "barra.js non passa i comandi ad altroId e gestoId"
    if "this.menu = s.sessionId;\n    this.scopri(s);\n    this.fare(s, a, cx);" not in vj or "this.menu = this.menu === s.sessionId ? null : s.sessionId;\n    this.scopri(s);" not in vj:
        return "volta.js: gestoId non preme il bottone, o altroId non apre e chiude Altro"
    if 'if (g && s.stato === "ferma") this.aperti[g.chiave] = true;' not in vj:
        return "volta.js: il comando non apre il gruppo delle ferme, e la sessione resta nascosta"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    bindir = casa / "bin"
    bindir.mkdir()
    cl = bindir / "claude"
    cl.write_text(CLAUDE_FINTO_ELENCO, encoding="utf-8")
    os.chmod(cl, 0o755)
    hcf = casa / "hc_finto.py"
    hcf.write_text('print(\'{"machines": []}\')\n', encoding="utf-8")
    (casa / "conf").mkdir()
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "VOLTA_HC": json.dumps([sys.executable, str(hcf)]),
           "CLAUDE_CONFIG_DIR": str(casa / "conf"), "PYTHONIOENCODING": "utf-8"}
    env.pop("VOLTA_SONDA_LOCALE", None)
    for extra, attesi in (({}, {"inter": "ferma", "fatta": "ferma", "fermata": "ferma", "rotta": "errore"}),
                          ({"HZ_SENZA_ALL": "1"}, {"inter": "ferma", "fatta": "ferma"})):
        r = subprocess.run([sys.executable, str(mod / "volta_sonda.py"), "volta"], capture_output=True, text=True, timeout=60, env={**env, **extra})
        try:
            righe = json.loads(r.stdout)["sessioni"]
        except (ValueError, IndexError, KeyError):
            return f"volta_sonda.py volta {extra}: uscita senza elenco: {(r.stdout + r.stderr).strip()[-160:]}"
        visti = {x["sessionId"].removesuffix("-x"): x["stato"] for x in righe}
        if visti != attesi:
            return f"elenco {extra or 'con --all'}: {visti}, atteso {attesi}"
    return None


# Il claude finto di HZ45: segna la chiamata (argv, la variabile della figlia, l'ingresso) e risponde
# con HZ_RISPOSTA; con HZ_ROTTO esce 1.
CLAUDE_FINTO_TITOLO = r"""#!/usr/bin/env python3
import json, os, sys
with open(os.environ["HZ_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"argv": sys.argv[1:], "figlia": os.environ.get("ARTURO_TITOLO_FIGLIO"), "ingresso": sys.stdin.read()}) + "\n")
if os.environ.get("HZ_ROTTO"):
    sys.exit(1)
print(os.environ.get("HZ_RISPOSTA", "Prova dei gesti sulle sessioni"))
"""

PROVA_TITOLO = """
import * as m from %s;
const s = (altro) => ({ id: "aaaa1111", nome: "volta-crea-sessione-remota", risposta: "Fatto: i gesti funzionano.", ...altro });
console.log(JSON.stringify({
  scritto: m.titolo(s({ titolo: "  Prova dei gesti  sulle sessioni " })),
  nome: m.titolo(s({ titolo: null })),
  risposta: m.titolo(s({ titolo: "", nome: "claudecode-0b" })),
}));
"""


def hz45(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    hook = repo / "hooks/titolo-sessione.py"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_TITOLO % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        attesi = {"scritto": "Prova dei gesti sulle sessioni", "nome": "volta-crea-sessione-remota", "risposta": "Fatto: i gesti funzionano."}
        if d != attesi:
            return f"titolo() di sessioni.js: {d}, atteso {attesi}"
    if 'shared("arturo.volta.gruppi") === "macchina" ? "macchina" : "progetto"' not in (mod / "volta.js").read_text(encoding="utf-8"):
        return "volta.js: senza una scelta l'elenco non si apre per progetto"
    if "(s.titolo ? div().whitespace_normal() : div().truncate())" not in (mod / "volta.js").read_text(encoding="utf-8"):
        return "volta.js: un titolo scritto non va a capo, e nella barra stretta si taglia"
    if 'setShared("arturo.volta.gruppi", c.slice(13))' not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "barra.js: manca il comando arturo.volta-gruppi-<modo>"
    conf = leggi(repo / "settings.json")
    for evento in ("UserPromptSubmit", "Stop"):
        voci = [h for e in conf["hooks"].get(evento, []) for h in e.get("hooks", []) if "titolo-sessione.py" in h.get("command", "")]
        if len(voci) != 1 or voci[0].get("async") is not True:
            return f"settings.json: titolo-sessione.py su {evento} deve esserci una volta, asincrono: {voci}"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    bindir, radice, log = casa / "bin", casa / "conf", casa / "log"
    bindir.mkdir()
    (radice / "cache" / "scheda").mkdir(parents=True)
    log.write_text("", encoding="utf-8")
    cl = bindir / "claude"
    cl.write_text(CLAUDE_FINTO_TITOLO, encoding="utf-8")
    os.chmod(cl, 0o755)
    (radice / "cache" / "scheda" / "sess1.json").write_text(json.dumps({"progetto": "deck"}), encoding="utf-8")
    tr = casa / "tr.jsonl"

    def turno(richiesta: str, risposta: str) -> None:
        with tr.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "user", "message": {"content": richiesta}}) + "\n")
            fh.write(json.dumps({"type": "user", "isMeta": True, "message": {"content": "Corpo di una skill accodato da Claude Code, lungo abbastanza"}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": risposta}, {"type": "tool_use", "name": "Bash", "input": {"description": "Lancia il banco"}}]}}) + "\n")

    tr.write_text(json.dumps({"type": "summary"}) + "\n", encoding="utf-8")
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "CLAUDE_CONFIG_DIR": str(radice), "HZ_LOG": str(log), "PYTHONIOENCODING": "utf-8"}
    for k in ("ARTURO_TITOLI", "ARTURO_TITOLO_FIGLIO", "ARTURO_TITOLI_OGNI"):
        env.pop(k, None)

    def evento(nome: str, sessione: str = "sess1", prompt: str = "", **extra) -> int:
        dati = {"hook_event_name": nome, "session_id": sessione, "transcript_path": str(tr), "prompt": prompt}
        return subprocess.run([sys.executable, str(hook)], input=json.dumps(dati), capture_output=True, text=True, timeout=60, env={**env, **extra}).returncode

    chiamate = lambda: [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]  # noqa: E731
    file = radice / "cache" / "titolo" / "sess1.json"
    evento("UserPromptSubmit", prompt="/inizio deck -- --rotazione Rifare le slide del capitolo due (#77), sul ramo deck")
    t = leggi(file) if file.exists() else {}
    if t.get("titolo") != "Rifare le slide del capitolo due, sul ramo deck" or t.get("fonte") != "avvio" or chiamate():
        return f"titolo di partenza: {t}, chiamate {len(chiamate())}; atteso il compito di /inizio senza modello"
    evento("UserPromptSubmit", prompt="un'altra richiesta lunga abbastanza")
    if leggi(file).get("titolo") != t["titolo"]:
        return "una seconda richiesta ha riscritto il titolo di partenza"
    turno("Rifai le slide del capitolo due con le foto nuove", "Ho rifatto sei slide.")
    if evento("Stop") != 0:
        return "Stop non esce 0"
    c = chiamate()
    t = leggi(file)
    if len(c) != 1 or t.get("titolo") != "Prova dei gesti sulle sessioni" or t.get("fonte") != "modello":
        return f"fine turno: {len(c)} chiamate, file {t}; attesa una chiamata e il titolo del modello"
    a = c[0]["argv"]
    for pezzo in (["--model", "haiku"], ["--tools", ""], ["--no-session-persistence"], ["--strict-mcp-config"], ["--settings", '{"disableAllHooks":true}']):
        if not any(a[i:i + len(pezzo)] == pezzo for i in range(len(a))):
            return f"la chiamata al modello non porta {pezzo}: {a}"
    if c[0]["figlia"] != "1":
        return "la chiamata al modello non porta ARTURO_TITOLO_FIGLIO=1"
    ing = c[0]["ingresso"]
    if "Progetto: deck" not in ing or "Rifai le slide del capitolo due" not in ing or "Ho rifatto sei slide" not in ing or "Corpo di una skill" in ing:
        return f"appunti per il modello sbagliati: {ing[:200]}"
    turno("Adesso sistema anche le note del relatore", "Note sistemate.")
    evento("Stop", HZ_RISPOSTA="Note del relatore")
    if len(chiamate()) != 1 or leggi(file).get("titolo") != "Prova dei gesti sulle sessioni":
        return "un secondo fine turno entro l'intervallo ha richiamato il modello"
    for risposta in ("Riga uno\nRiga due", "x" * 80):
        evento("Stop", HZ_RISPOSTA=risposta, ARTURO_TITOLI_OGNI="0")
        if leggi(file).get("titolo") != "Prova dei gesti sulle sessioni":
            return f"una risposta non valida ({risposta[:12]!r}) ha cambiato il titolo"
    prima = len(chiamate())
    evento("Stop", HZ_RISPOSTA="Note del relatore", ARTURO_TITOLI_OGNI="0")
    if len(chiamate()) != prima + 1 or leggi(file).get("titolo") != "Note del relatore":
        return "passato l'intervallo, con la trascrizione cresciuta, il titolo non si aggiorna"
    evento("Stop", HZ_RISPOSTA="Altro titolo", ARTURO_TITOLI_OGNI="0")
    if len(chiamate()) != prima + 1:
        return "con la trascrizione ferma il modello è stato richiamato"
    turno("Ultima cosa: esporta il PDF del capitolo", "PDF esportato.")
    for extra in ({"ARTURO_TITOLI": "0"}, {"ARTURO_TITOLO_FIGLIO": "1"}):
        evento("Stop", ARTURO_TITOLI_OGNI="0", **extra)
        evento("UserPromptSubmit", sessione="sess2", prompt="una richiesta che non deve lasciare titoli", **extra)
        if len(chiamate()) != prima + 1 or (radice / "cache" / "titolo" / "sess2.json").exists():
            return f"con {extra} l'hook ha lavorato lo stesso"
    if evento("Stop", ARTURO_TITOLI_OGNI="0", HZ_ROTTO="1") != 0 or leggi(file).get("titolo") != "Note del relatore":
        return "un claude che fallisce cambia il titolo o l'uscita dell'hook"
    # la sonda porta il titolo nell'elenco
    cla = bindir / "claude"
    cla.write_text(CLAUDE_FINTO_ELENCO, encoding="utf-8")
    hcf = casa / "hc_finto.py"
    hcf.write_text('print(\'{"machines": []}\')\n', encoding="utf-8")
    (radice / "cache" / "titolo" / "inter-x.json").write_text(json.dumps({"titolo": "Slide del capitolo due"}), encoding="utf-8")
    r = subprocess.run([sys.executable, str(mod / "volta_sonda.py"), "volta"], capture_output=True, text=True, timeout=60,
                       env={**env, "VOLTA_HC": json.dumps([sys.executable, str(hcf)])})
    try:
        titoli = {x["sessionId"]: x.get("titolo") for x in json.loads(r.stdout)["sessioni"]}
    except (ValueError, KeyError):
        return f"volta_sonda.py volta: uscita senza elenco: {(r.stdout + r.stderr).strip()[-160:]}"
    if titoli.get("inter-x") != "Slide del capitolo due" or titoli.get("fatta-x") is not None:
        return f"la sonda non porta il titolo nell'elenco: {titoli}"
    return None


PROVA_ANTEPRIMA = """
import * as m from %s;
console.log(JSON.stringify({
  piena: m.anteprima({ risposta: "**Fatto:** `volta_sonda.py` gira.\\n\\n## Poi\\n> il resto", azione: "Bash: Lancia il banco" }),
  solaAzione: m.anteprima({ risposta: "", azione: "Read: " }),
  vuota: m.anteprima({ risposta: "", azione: "" }),
  senzaCampi: m.anteprima({}),
}));
"""


def hz46(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    presa, comando = vj.find('if (a.verbo === "logs" && anteprima(s)) { this.anteprime[k] = true; return cx.notify(); }'), vj.find("await azioneSessione(s, a.verbo)")
    if presa < 0 or comando < 0 or presa > comando:
        return "volta.js: l'Anteprima non parte dalla riga già letta prima di lanciare claude logs"
    for pezzo in ("vista === true ? anteprima(s)", "div().id(id).whitespace_normal()", "child(b.etichetta)"):
        if pezzo not in vj:
            return f"volta.js non mostra l'anteprima a capo con le etichette ({pezzo})"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_ANTEPRIMA % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        attesi = {"piena": [{"etichetta": "Ultima risposta", "righe": ["Fatto: volta_sonda.py gira.", "Poi", "il resto"]},
                            {"etichetta": "Ultima azione", "righe": ["Bash: Lancia il banco"]}],
                  "solaAzione": [{"etichetta": "Ultima azione", "righe": ["Read"]}], "vuota": None, "senzaCampi": None}
        for k, v in attesi.items():
            if d.get(k) != v:
                return f"anteprima() {k}: {d.get(k)}, atteso {v}"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    bindir = casa / "bin"
    bindir.mkdir()
    cl = bindir / "claude"
    cl.write_text(CLAUDE_FINTO_ELENCO, encoding="utf-8")
    os.chmod(cl, 0o755)
    hcf = casa / "hc_finto.py"
    hcf.write_text('print(\'{"machines": []}\')\n', encoding="utf-8")
    tr = casa / "conf" / "projects" / "-p"
    tr.mkdir(parents=True)
    lunga = "Fatto: " + "parola " * 80  # 567 caratteri: oltre il taglio a 400
    with (tr / "inter-x.jsonl").open("w", encoding="utf-8") as fh:
        fh.write("{}\n")  # la sonda salta la prima riga, che può essere a metà
        fh.write(json.dumps({"type": "assistant", "timestamp": "2026-11-10T10:00:00Z", "message": {"content": [
            {"type": "text", "text": lunga}, {"type": "tool_use", "name": "Bash", "input": {"description": "Lancia il banco"}}]}}) + "\n")
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "VOLTA_HC": json.dumps([sys.executable, str(hcf)]),
           "CLAUDE_CONFIG_DIR": str(casa / "conf"), "PYTHONIOENCODING": "utf-8"}
    env.pop("VOLTA_SONDA_LOCALE", None)
    r = subprocess.run([sys.executable, str(mod / "volta_sonda.py"), "volta"], capture_output=True, text=True, timeout=60, env=env)
    try:
        riga = next(x for x in json.loads(r.stdout)["sessioni"] if x["sessionId"] == "inter-x")
    except (ValueError, KeyError, StopIteration):
        return f"volta_sonda.py volta: uscita senza la sessione con la trascrizione: {(r.stdout + r.stderr).strip()[-160:]}"
    risposta = riga.get("risposta") or ""
    if not (380 < len(risposta) <= 401 and risposta.endswith("parola…") and risposta.startswith("Fatto: parola")):
        return f"risposta lunga {len(risposta)} che finisce con {risposta[-12:]!r}: attesa tagliata a una parola intera entro 400, col segno …"
    if riga.get("azione") != "Bash: Lancia il banco":
        return f"ultima azione {riga.get('azione')!r}, attesa 'Bash: Lancia il banco'"
    return None


def hz47(repo: Path, casa: Path) -> str | None:
    vj = (repo / "shared/volta-celeste/mods/arturo/volta.js").read_text(encoding="utf-8")
    inizio, fine = vj.find("  pannello(t) {"), vj.find("  riga(t, s, modo, cx) {")
    if inizio < 0 or fine < inizio:
        return "volta.js non ha pannello() prima di riga()"
    corpo = vj[inizio:fine]
    if vj.count("this.gesti(t, s, az)") != 1 or "this.gesti(t, s, az)" not in corpo:
        return "volta.js: i gesti non stanno solo nel pannello (una riga in fondo li apre sotto il bordo)"
    for pezzo in ("x.sessionId === this.menu", "child(titolo(s))", "this.menu = null; cx.notify();", "child(avviso)"):
        if pezzo not in corpo:
            return f"volta.js: al pannello dei gesti manca {pezzo}"
    elenco = vj.find('.id("volta-elenco").max_h(360).min_h(0).flex_shrink(1).overflow_y_scroll()')
    fuori = vj.find("const gesti = chiusa || !corpo ? null : this.pannello(t);")
    dopo = vj.find(".when(Boolean(corpo), (el) => el.child(corpo))\n      .when(Boolean(gesti), (el) => el.child(gesti));")
    if min(elenco, fuori, dopo) < 0 or not elenco < fuori < dopo:
        return "volta.js: il pannello dei gesti non sta sotto l'elenco, fuori dalla parte che scorre"
    if ".when(Boolean(avviso) && !aperto, (el)" not in vj[fine:]:
        return "volta.js: con Altro aperto l'avviso del gesto esce due volte, nella riga e nel pannello"
    return None


def hz48(repo: Path, casa: Path) -> str | None:
    import importlib.util
    sp = importlib.util.spec_from_file_location("volta_sonda_hz48", repo / "shared/volta-celeste/mods/arturo/volta_sonda.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    voce = {"macchina": "amaltea", "host": "amaltea", "questa": False, "target": "amaltea", "claude": "/c", "sessioni": [
        {"sessionId": "2f179bde-e963-47ce", "id": "0a0579ea", "kind": "background", "state": "done", "status": "idle"},
        {"sessionId": "abcd1234-ffff", "id": "zz", "kind": "interactive", "status": "idle", "terminale": "t23"},
        {"sessionId": "eeee5678-ffff", "kind": "interactive", "status": "idle", "terminale": "t23; rm"}]}
    r = {x["sessionId"]: x for x in m.righe([voce])}
    fondo, inter = r.get("2f179bde-e963-47ce"), r.get("abcd1234-ffff")
    if not fondo or fondo["id"] != "0a0579ea" or fondo["attach"][-2:] != ["attach", "0a0579ea"]:
        return "volta_sonda.py: una sessione in background si aggancia con l'inizio del sessionId, non con l'id del lavoro"
    if not inter or inter["id"] != "abcd1234" or inter["attach"] is not None:
        return "volta_sonda.py: un'interattiva non tiene l'inizio del sessionId come id"
    if inter.get("terminale") != "t23" or fondo.get("terminale") is not None or r["eeee5678-ffff"].get("terminale") is not None:
        return "volta_sonda.py: la scheda di Herdr che ospita un'interattiva non arriva pulita nella riga"
    return None


def hz49(repo: Path, casa: Path) -> str | None:
    vj = (repo / "shared/volta-celeste/mods/arturo/volta.js").read_text(encoding="utf-8")
    inizio, fine = vj.find("  riga(t, s, modo, cx) {"), vj.find("  interruttore(t) {")
    if inizio < 0 or fine < inizio:
        return "volta.js non ha riga() prima di interruttore()"
    corpo = vj[inizio:fine]
    for pezzo, perche in (('const rm = az.find((a) => a.verbo === "rm");', "la X non nasce dal gesto rm di azioni()"),
                          ("const vediX = Boolean(rm) && (this.sopra === k || chiedoRm || facciorm);", "la X non segue il puntatore"),
                          (".when(!vediX, (el) => el.invisible())", "la X nascosta non tiene il suo posto"),
                          (".on_click((_e, cx) => this.fare(s, rm, cx))", "il clic sulla X non passa da fare() con la conferma"),
                          ('ICONA("x")', "manca l'icona x"),
                          (".on_hover((h, cx) =>", "la riga non segue il puntatore"),
                          (".when(Boolean(x), (el) => el.child(x))", "la riga non mostra la X")):
        if pezzo not in corpo:
            return f"volta.js: {perche} ({pezzo})"
    if "this.sopra = null;" not in vj[:inizio]:
        return "volta.js: init non prepara this.sopra"
    return None


def hz50(repo: Path, casa: Path) -> str | None:
    bj = (repo / "shared/volta-celeste/mods/arturo/barra.js").read_text(encoding="utf-8")
    piede = bj[bj.find("export class Piede {"):]
    if '.child(voce("note", "pin", "Note", () => apriElenco())' not in piede:
        return "barra.js: il piede non ha la voce Note che apre l'elenco delle note"
    if "${tasti().nota} nuova · ${tasti().elenco}" not in piede:
        return "barra.js: la voce Note non scrive i tasti della nota nuova e dell'elenco"
    lay = json.loads((repo / "shared/volta-celeste/layouts/arturo.json").read_text(encoding="utf-8"))
    alti = []
    def cerca(n):
        if isinstance(n, dict):
            if n.get("id") == "piede":
                alti.append((n.get("size") or {}).get("px"))
            for v in n.values():
                cerca(v)
        elif isinstance(n, list):
            for v in n:
                cerca(v)
    cerca(lay)
    if alti != [190]:
        return f"layout arturo: il piede è alto {alti}, le cinque voci vogliono 190 px"
    return None


PROVA_ORDINE = r"""
import * as v from %s;
const r = (o) => ({ macchina: "MacBook Air", host: "macbook", questa: true, tipo: "background", stato: "ferma", ultimo: "", risposta: "", progetto: null, attach: ["claude", "attach", o.id], nome: o.id, ...o });
const amaltea = { macchina: "Amaltea", host: "amaltea", questa: false };
const dati = {
  macchine: [{ macchina: "MacBook Air", host: "macbook", questa: true }, amaltea],
  sessioni: [
    r({ id: "ieri-aspetta", stato: "aspetta", ultimo: "2026-11-10T09:00:00Z", progetto: "arturo" }),
    r({ id: "ora-ferma", stato: "ferma", ultimo: "2026-11-11T08:59:00Z", progetto: "arturo" }),
    r({ id: "stamattina-lavora", stato: "lavora", ultimo: "2026-11-11T07:00:00Z", progetto: "arturo" }),
    r({ id: "senza-tempo", stato: "errore", progetto: "arturo" }),
    r({ id: "aaa", progetto: "zucca" }),
    r({ id: "bbb", progetto: "mela" }),
    r({ id: "sciolta", ...amaltea, ultimo: "2026-11-11T08:30:00Z" }),
    r({ id: "vecchia", ...amaltea, ultimo: "2026-11-01T08:00:00Z", progetto: "zeta" }),
    r({ id: "ultima", ...amaltea, stato: "lavora", ultimo: "2026-11-11T09:10:00Z", progetto: "basement" }),
  ],
};
const forma = (gs) => gs.map((g) => [g.titolo, g.sessioni.map((s) => s.id)]);
console.log(JSON.stringify({ progetto: forma(v.gruppi(dati, "progetto")), macchina: forma(v.gruppi(dati, "macchina")) }));
"""


def hz51(repo: Path, casa: Path) -> str | None:
    import importlib.util
    mod = repo / "shared/volta-celeste/mods/arturo"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_ORDINE % json.dumps(copia.as_uri())],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        avuto = json.loads(r.stdout.strip().splitlines()[-1])
        atteso = {
            "progetto": [["Basement", ["ultima"]], ["Arturo", ["ora-ferma", "stamattina-lavora", "ieri-aspetta", "senza-tempo"]],
                         ["Senza progetto", ["sciolta"]], ["Zeta", ["vecchia"]], ["Mela", ["bbb"]], ["Zucca", ["aaa"]]],
            "macchina": [["Amaltea", ["ultima", "sciolta", "vecchia"]],
                         ["MacBook Air", ["ora-ferma", "stamattina-lavora", "ieri-aspetta", "aaa", "bbb", "senza-tempo"]]],
        }
        for k, v in atteso.items():
            if avuto.get(k) != v:
                return f"ordine {k}: atteso {v}, avuto {avuto.get(k)}"
    sp = importlib.util.spec_from_file_location("volta_sonda_hz51", mod / "volta_sonda.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    voce = {"macchina": "amaltea", "host": "amaltea", "questa": False, "target": "amaltea", "claude": "/c", "sessioni": [
        {"sessionId": "aaaa1111-0000", "id": "nata", "kind": "background", "status": "idle", "startedAt": 1794387600000},
        {"sessionId": "bbbb2222-0000", "id": "letta", "kind": "background", "status": "idle", "startedAt": 1794387600000,
         "ultimo": "2026-11-11T08:00:00.000Z"},
        {"sessionId": "cccc3333-0000", "id": "nuda", "kind": "background", "status": "idle"},
        {"sessionId": "dddd4444-0000", "id": "storta", "kind": "background", "status": "idle", "startedAt": "ieri"}]}
    r = {x["id"]: x["ultimo"] for x in m.righe([voce])}
    atteso = {"nata": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(1794387600)), "letta": "2026-11-11T08:00:00.000Z", "nuda": "", "storta": ""}
    if r != atteso:
        return f"volta_sonda.py, ultimo senza trascrizione: {r}, atteso {atteso}"
    if not atteso["nata"].startswith("20"):
        return f"la nascita non è una data di questo secolo: {atteso['nata']}"
    return None


PROVA_APRI = r"""
import { apriSessione, nuovaScheda, comando, ETICHETTA } from "./dati.mjs";
import { lanciati, eseguiti, avvisi, inviati } from "./herdr.mjs";
const caso = process.env.HZ_CASO;
let esito = null, veglia = null;
if (caso === "nuova-scheda") await nuovaScheda();
else if (caso === "comando") esito = comando(["ssh", "-t", "h", "/a b/claude", "attach", "x'y", "a=b,c:d@e"]);
else {
  const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "Torre", macchina: "Torre", nome: "Progetto x", progetto: "progetto-x",
              stato: process.env.HZ_STATO || "ferma", tipo: "background" };
  const r = await apriSessione(s, ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"], process.env.HZ_PRONTA === "1");
  veglia = r.veglia ? await r.veglia : null;
  esito = { ...r, veglia: undefined };
}
console.log(JSON.stringify({ lanciati, eseguiti, avvisi, inviati, esito, veglia, etichetta: ETICHETTA }));
"""


def hz52(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta-celeste/mods/arturo"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_APRI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]
    riga = "ssh -t torre.lan claude attach ffff1111"
    nascita = ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", *attach]
    viva = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 77, "argv": attach}}
    nuda = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 10, "argv": ["/bin/zsh", "-li"]}}
    avvio = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 10, "argv": nascita}}
    spazio = {"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb0", "name": "Shell"}, {"id": "tb1", "name": "Progetto x"}]}
    herdr = {"spaces": [spazio], "panes": [{"terminal": "t3", "tab": "tb0"}, {"terminal": "t7", "tab": "tb1"}],
             "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": nascita}]}

    def volta(caso="apri", herdr=herdr, uscita='{"ok": true}', letture=None, **extra):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": uscita,
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}),
             "HZ_HERDR": json.dumps(herdr), "HZ_HC_GET": json.dumps(letture or {}), **extra}
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    sonda = lambda v: [x[2:] for x in v["eseguiti"] if len(x) > 2 and x[2] == "apri"]  # noqa: E731
    nuove = lambda v: [x for x in v["lanciati"] if x["cmd"] in ("tab.new", "space.new")]  # noqa: E731
    invii = lambda v: [x for x in v["inviati"] if x[0] == "send"]  # noqa: E731
    try:
        # Claude gira ancora nella scheda: davanti, senza servizio né comandi, e l'etichetta resta scritta
        v = volta(letture={"t7": [viva]})
        if v["esito"].get("come") != "davanti" or sonda(v) or nuove(v) or invii(v):
            return f"una scheda con Claude dentro non va solo davanti: {v['esito']}, {sonda(v)}, {nuove(v)}, {invii(v)}"
        if {"cmd": "pane.focus", "terminal": "t7"} not in v["lanciati"]:
            return f"la scheda viva non viene portata davanti: {v['lanciati']}"
        if ["label", "t7", f"{v['etichetta']}=ffff1111"] not in v["inviati"] or v["etichetta"] != "arturo.sessione":
            return f"la scheda ritrovata per argv non riceve l'etichetta: {v['inviati']}"
        # ritrovata per etichetta, anche se l'argv non dice niente e il nome è un altro
        etichettata = {**herdr, "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["zsh"], "labels": {"arturo.sessione": "ffff1111"}}]}
        v = volta(herdr=etichettata, letture={"t7": [viva]})
        if v["esito"].get("come") != "davanti" or nuove(v) or any(x[0] == "label" for x in v["inviati"]):
            return f"una scheda con l'etichetta non si ritrova, o si rietichetta: {v['esito']}, {v['inviati']}"
        # la shell nuda: servizio, poi claude attach riparte nella stessa scheda
        v = volta(letture={"t7": [nuda, viva]})
        if v["esito"].get("come") != "rilanciata" or sonda(v) != [["apri", "Torre", "ffff1111"]] or nuove(v):
            return f"una scheda con la shell nuda non rilancia Claude lì: {v['esito']}, {sonda(v)}, {nuove(v)}"
        if invii(v) != [["send", "t7", riga]] or v["veglia"] != {}:
            return f"il rilancio non scrive claude attach nella scheda: {invii(v)}, veglia {v['veglia']}"
        ordine = [x[0] for x in v["inviati"] if x[0] in ("get", "send")]
        if ordine[:2] != ["get", "send"] or not v["eseguiti"] or v["eseguiti"][0][2:3] != ["apri"]:
            return f"il servizio non viene prima del rilancio: {ordine}, {v['eseguiti'][:1]}"
        # stesso nome, altra cosa dentro: nasce una scheda nuova (prima il clic sceglieva quella per nome)
        omonima = {**herdr, "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["zsh"]}]}
        v = volta(herdr=omonima)
        if len(nuove(v)) != 1 or nuove(v)[0].get("argv") != attach or sonda(v) != [["apri", "Torre", "ffff1111"]]:
            return f"con una scheda dallo stesso nome non nasce la scheda della sessione: {v['lanciati']}"
        if any(x["cmd"] == "tab.select" for x in v["lanciati"]):
            return "il clic sceglie ancora una scheda per nome"
        if v["eseguiti"][0][2:3] != ["apri"]:
            return f"la scheda nasce prima del servizio: {v['eseguiti'][:1]}"
        # senza servizio non nasce niente, e lo si dice
        v = volta(herdr=omonima, uscita=json.dumps({"errore": "il servizio di Claude non parte su Torre: spenta"}))
        if nuove(v) or invii(v) or "spenta" not in (v["esito"].get("errore") or ""):
            return f"senza servizio la scheda nasce lo stesso, o l'errore si perde: {v['esito']}, {nuove(v)}"
        # una sessione in errore riparte prima (respawn)
        v = volta(herdr=omonima, HZ_STATO="errore")
        if sonda(v) != [["apri", "Torre", "ffff1111", "--riavvia"]]:
            return f"una sessione in errore non passa da --riavvia: {sonda(v)}"
        # appena nata: il servizio è acceso, niente apri
        v = volta(herdr=omonima, HZ_PRONTA="1")
        if sonda(v) or len(nuove(v)) != 1:
            return f"una sessione appena nata ripassa dal servizio: {sonda(v)}"
        # la veglia: Claude esce subito dalla scheda nuova, la sessione si riavvia una volta e riparte
        v = volta(herdr=omonima, HZ_NASCE="t9", letture={"t9": [nuda, viva]})
        if sonda(v) != [["apri", "Torre", "ffff1111"], ["apri", "Torre", "ffff1111", "--riavvia"]] or invii(v) != [["send", "t9", riga]]:
            return f"la veglia non riavvia e non rilancia: {sonda(v)}, {invii(v)}"
        if v["veglia"] != {"riavviata": True} or ["label", "t9", "arturo.sessione=ffff1111"] not in v["inviati"]:
            return f"la veglia riuscita non lo dice, o la scheda nuova resta senza etichetta: {v['veglia']}, {v['inviati']}"
        v = volta(herdr=omonima, HZ_NASCE="t9", letture={"t9": [nuda]})
        if "non resta aperto" not in (v["veglia"] or {}).get("errore", "") or len(invii(v)) != 1:
            return f"una sessione che non si riapre non lo dice, o si riprova senza fine: {v['veglia']}, {invii(v)}"
        v = volta(herdr=omonima, HZ_NASCE="t9", HZ_STATO="errore", letture={"t9": [nuda]})
        if len(sonda(v)) != 1 or invii(v) or "errore" not in (v["veglia"] or {}):
            return f"dopo un riavvio la veglia riavvia ancora: {sonda(v)}, {invii(v)}"
        # Claude resta, oppure la shell si sta ancora avviando: niente riavvio
        for nome, lettura in (("viva", viva), ("in avvio", avvio)):
            v = volta(herdr=omonima, HZ_NASCE="t9", letture={"t9": [lettura]})
            if len(sonda(v)) != 1 or invii(v) or v["veglia"] != {}:
                return f"scheda {nome}: la veglia riavvia una sessione sana: {sonda(v)}, {invii(v)}, {v['veglia']}"
        v = volta(herdr={**herdr}, letture={"t7": [avvio]})
        if v["esito"].get("come") != "davanti":
            return f"una shell che si sta avviando passa per nuda: {v['esito']}"
        # il comando per la shell: fra apici ciò che non è una parola semplice
        v = volta("comando")
        if v["esito"] != "ssh -t h '/a b/claude' attach 'x'\\''y' a=b,c:d@e":
            return f"comando(): {v['esito']}"
        # la scheda nuova: una sessione senza prompt nel progetto dello spazio aperto
        v = volta("nuova-scheda", herdr=omonima, uscita=json.dumps({"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": attach}))
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "qui", "--progetto", "progetto-x"]:
            return f"la scheda nuova non fa nascere una sessione nel progetto aperto: {v['eseguiti'][:1]}"
        if len(nuove(v)) != 1 or nuove(v)[0].get("name") != "Nuova sessione" or nuove(v)[0].get("space") != "s1" or nuove(v)[0].get("argv") != attach:
            return f"la scheda nuova non si aggancia nello spazio aperto: {nuove(v)}"
        if sonda(v):
            return "la scheda nuova ripassa dal servizio dopo la nascita"
        volta_ = {**omonima, "spaces": [{**spazio, "name": "Volta"}]}
        v = volta("nuova-scheda", herdr=volta_, uscita=json.dumps({"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": attach}))
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "qui"]:
            return f"dallo spazio Volta la scheda nuova prende un progetto: {v['eseguiti'][:1]}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("this.apro[k] = true;", "if (r.errore) this.avvisa(s, r.errore, cx);", "if (v?.errore) this.avvisa(s, v.errore, cx);",
                  "this.apri({ ...s, id: esito.id ?? s.id }, esito.attach, true, cx);", '{ testo: "La apro…", colore: "working" }'):
        if pezzo not in vj:
            return f"volta.js senza {pezzo}"
    return None


def hz53(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    sonda = mod / "volta_sonda.py"
    nata = {"id": "ffff1111", "sessionId": "ffff1111-aaaa", "claude": "C:/u/claude.exe", "cartella": "C:/u/ClaudeCode"}
    conf = {
        "macchine": [{"name": n, "target": n.lower(), "state": "connected"} for n in ("Torre", "Win", "Rotto")],
        "exec": {"Torre": {"python": nata, "claude": "respawned ffff1111"}, "Win": {"python": nata, "claude": "respawned ffff1111"},
                 "Rotto": {"python3": nata, "claude": "respawned ffff1111"}},
        "servizio": {"Win": {"serve": "hc-run"}, "Rotto": {"errore": "Claude Code non c'è su questa macchina"}},
        "dopo_run": {"Win": {"acceso": True, "come": "già acceso"}},
    }
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    log, stato = casa / "hc.log", casa / "hc.stato"
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]),
           "HZ_HC_LOG": str(log), "HZ_HC_STATO": str(stato)}

    def lancia(*args):
        log.write_text("", encoding="utf-8")
        stato.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(sonda), *args], capture_output=True, text=True, timeout=90, env=env)
        chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), chiamate
        except (ValueError, IndexError):
            return r.returncode, {"uscita": (r.stderr or r.stdout).strip()[-160:]}, chiamate

    servizi = lambda ch: [c for c in ch if c[:2] == ["exec", "--on"] and c[-1] == "remoto"]  # noqa: E731
    riavvii = lambda ch: [c for c in ch if "respawn" in c]  # noqa: E731
    rc, d, ch = lancia("apri", "Torre", "ffff1111")
    if rc != 0 or d.get("ok") is not True or d.get("riavviata") is not False or not servizi(ch) or riavvii(ch):
        return f"apri su Torre: rc {rc}, {d}, servizio {len(servizi(ch))}, riavvii {len(riavvii(ch))}"
    rc, d, ch = lancia("apri", "Win", "ffff1111")
    if rc != 0 or not any(c[:1] == ["run"] for c in ch):
        return f"apri su Win non accende il servizio che manca: rc {rc}, {d}"
    rc, d, ch = lancia("apri", "Rotto", "ffff1111")
    if rc == 0 or "servizio di Claude non parte su Rotto" not in d.get("errore", ""):
        return f"apri su Rotto senza servizio non dà errore: rc {rc}, {d}"
    rc, d, ch = lancia("apri", "Torre", "ffff1111", "--riavvia")
    if rc != 0 or d != {"ok": True, "riavviata": True} or len(riavvii(ch)) != 1:
        return f"apri --riavvia su Torre: rc {rc}, {d}, {riavvii(ch)}"
    if riavvii(ch)[0][-3:] != ["claude", "respawn", "ffff1111"] or ch.index(riavvii(ch)[0]) < ch.index(servizi(ch)[0]):
        return f"apri --riavvia non accende il servizio prima di claude respawn: {ch}"
    rc, d, ch = lancia("apri", "Rotto", "ffff1111", "--riavvia")
    if rc == 0 or "non si riavvia" not in d.get("errore", "") or riavvii(ch):
        return f"apri --riavvia senza servizio: rc {rc}, {d}, {riavvii(ch)}"
    for strano in (["Torre", "--all"], ["Torre", "abcd;rm -rf"], ["Torre"], ["Torre", "ffff1111", "altro"]):
        rc, d, ch = lancia("apri", *strano)
        if rc == 0 or ch:
            return f"apri {strano} non rifiutato, o lanciato lo stesso: rc {rc}, {d}"
    # i tasti: la scheda nuova è una sessione di Claude
    vc = repo / "shared/volta-celeste"
    if leggi(vc / "keys.json").get("global", {}).get("cmd-t") != "arturo.volta-nuova":
        return "keys.json non lega cmd-t alla scheda nuova di Volta"
    if leggi(vc / "keys-ctrl.json").get("global", {}).get("ctrl-shift-t") != "arturo.volta-nuova":
        return "keys-ctrl.json non lega ctrl-shift-t alla scheda nuova di Volta"
    for nome, prima, atteso in (("di Herdr", "tab.new", "arturo.volta-nuova"), ("della persona", "pane.split:right", "pane.split:right")):
        sotto = casa / f"tasti-{atteso[:4]}"
        (sotto / "app").mkdir(parents=True)
        (sotto / "app" / "keys.json").write_text(json.dumps({"global": {"cmd-t": prima, "cmd-o": "tab.new"}}), encoding="utf-8")
        r = installa(repo, sotto, "mac-arm", {"ARTURO_HERDR_FIRMA": "presente"})
        if r.returncode != 0:
            return f"installazione fallita: {(r.stdout + r.stderr)[-200:]}"
        avuti = leggi(sotto / "app" / "keys.json")["global"]
        if avuti.get("cmd-t") != atteso:
            return f"cmd-t {nome} ({prima}) diventa {avuti.get('cmd-t')}, atteso {atteso}"
        if avuti.get("cmd-o") != "tab.new":
            return "l'installazione si prende un tasto che non è la scheda nuova"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    if 'else if (c === "volta-nuova") await nuovaScheda();' not in barra:
        return "barra.js non porta arturo.volta-nuova a nuovaScheda()"
    if barra.index('c === "volta-nuova"') > barra.index('c.startsWith("volta-")) this.volta.premiId('):
        return "barra.js: volta-nuova finisce nel clic su una sessione, che viene prima"
    return None


PROVA_MENU = """
import * as m from %s;
const bg = (stato, altro = {}) => ({ tipo: "background", stato, host: "qui", sessionId: "s-" + stato, id: stato.slice(0, 4), ...altro });
const verbi = (s) => m.menu(s).map((a) => a.verbo + (a.conferma ? "!" : ""));
console.log(JSON.stringify({
  lavora: verbi(bg("lavora")), ferma: verbi(bg("ferma")), errore: verbi(bg("errore")),
  interattiva: verbi({ ...bg("ferma"), tipo: "interattiva" }), vecchia: verbi(bg("ferma", { vecchia: true })), niente: verbi(null),
  testi: m.menu(bg("ferma")).map((a) => a.testo), solo: [...m.SOLO_MENU].sort(),
  fork: [m.titoloFork({ titolo: "Rifare il deck" }), m.titoloFork({ titolo: "x".repeat(80) }).length],
}));
"""

PROVA_COPIA = r"""
import { copiaSessione, chiudiSchede } from "./dati.mjs";
import { lanciati, eseguiti, avvisi, inviati } from "./herdr.mjs";
const caso = process.env.HZ_CASO;
const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "Torre", macchina: "Torre", nome: "Progetto x", titolo: "Rifare il deck",
            progetto: "Progetto X", cartella: "/lavori/x", stato: "ferma", tipo: "background" };
let esito = null;
if (caso === "chiudi") esito = chiudiSchede(s);
else if (caso === "nuda") esito = await copiaSessione({ id: "ffff1111", sessionId: "ffff1111-aaaa", nome: "ffff1111", questa: true }, "duplica");
else esito = await copiaSessione(s, caso);
console.log(JSON.stringify({ lanciati, eseguiti, avvisi, inviati, esito }));
"""


def hz54(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    testi = {n: (mod / n).read_text(encoding="utf-8") for n in ("volta.js", "barra.js", "main.js", "menusessione.js", "dati.js")}
    attesi = (
        ("volta.js", '.on_mouse_down("right", (_e, cx) => { if (apriMenuSessione(s)) cx.stop_propagation(); })', "il tasto destro non apre il menu"),
        ("volta.js", "if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);", "un gesto del solo menu apre il riquadro di Altro"),
        ("volta.js", 'if (a.verbo === "apri") return this.premi(s, cx);', "Apri non è il clic sulla sessione"),
        ("volta.js", '    chiudiSchede(s);\n    return azioneSessione(s, "stop");', "Chiudi non chiude la scheda prima di fermare la sessione"),
        ("volta.js", 'a.verbo === "duplica" || a.verbo === "fork" ? await copiaSessione(s, a.verbo)', "Duplica e Fork non passano da copiaSessione"),
        ("volta.js", ': lavoro ? { testo: lavoro, colore: "working" }', "la riga non dice che il gesto è in corso"),
        ("volta.js", "const voci = menu(s).concat(", "gestoId non conosce le voci del menu"),
        ("barra.js", 'else if (c.startsWith("volta-menu-")) this.volta.menuId(c.slice(11));', "barra.js non apre il menu da comando"),
        ("main.js", "sessione: MenuSessione,", "main.js non monta il menu di una sessione"),
        ("menusessione.js", 'openOverlay({ mod: "arturo", props: { parte: "sessione", sessione: s }, kind: "popup"', "il menu non è un popup del mod"),
        ("menusessione.js", "    run(comandoGesto(this.s, v));\n    this.chiudi();", "il menu si chiude prima di mandare il gesto"),
        ("menusessione.js", "`arturo.volta-gesto-${v.verbo}-${s.id}`", "il menu non manda il comando che barra.js legge"),
        ("menusessione.js", "this.voci = menu(this.s);", "le voci del menu non vengono da menu() di sessioni.js"),
    )
    for file, pezzo, motivo in attesi:
        if pezzo not in testi[file]:
            return f"{file}: {motivo}"
    bj = testi["barra.js"]
    if bj.index('c.startsWith("volta-menu-")') > bj.index('c.startsWith("volta-")) this.volta.premiId('):
        return "barra.js: volta-menu-<id> finisce nel clic su una sessione, che viene prima"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(mod / "sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_MENU % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    voci = {"lavora": ["apri", "chiudi", "duplica", "fork", "logs"], "ferma": ["apri", "chiudi", "duplica", "fork", "logs", "rm!"],
            "errore": ["apri", "chiudi", "duplica", "fork", "logs", "respawn", "rm!"], "interattiva": ["apri", "duplica", "fork"],
            "vecchia": [], "niente": [], "testi": ["Apri", "Chiudi", "Duplica", "Fork", "Anteprima", "Elimina"],
            "solo": ["apri", "chiudi", "duplica", "fork"], "fork": ["Rifare il deck (fork)", 60]}
    for k, v in voci.items():
        if d.get(k) != v:
            return f"menu di sessioni.js, {k}: {d.get(k)}, atteso {v}"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, testi["dati.js"])
    (m / "prova.mjs").write_text(PROVA_COPIA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["ssh", "-t", "torre.lan", "claude", "attach", "eeee2222"]
    nata = json.dumps({"id": "eeee2222", "sessionId": "eeee2222-bbbb", "attach": attach})
    spazio = {"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb1"}, {"id": "tb2"}]}
    herdr = {"spaces": [spazio], "panes": [{"terminal": "t7", "tab": "tb1"}, {"terminal": "t8", "tab": "tb2"}, {"terminal": "t9", "tab": "tb2"}],
             "terminals": [{"address": "t7", "argv": ["claude", "attach", "ffff1111"]}, {"address": "t9", "argv": ["zsh"]},
                           {"address": "t8", "argv": ["zsh"], "labels": {"arturo.sessione": "ffff1111"}}]}

    def volta(caso, uscita=nata, dove="Altra"):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": uscita,
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [{"host": "Altra", "macchina": "Altra"}], "arturo.dove": dove}),
             "HZ_HERDR": json.dumps(herdr)}
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    nuove = lambda v: [x for x in v["lanciati"] if x["cmd"] in ("tab.new", "space.new")]  # noqa: E731
    try:
        v = volta("fork")
        atteso = ["fork", "Torre", "ffff1111-aaaa", "--progetto", "Progetto X", "--cartella", "/lavori/x", "--titolo", "Rifare il deck (fork)"]
        if not v["eseguiti"] or v["eseguiti"][0][2:] != atteso:
            return f"Fork non chiama la sonda sulla macchina della sessione, col sessionId e la cartella: {v['eseguiti'][:1]}"
        if len(nuove(v)) != 1 or nuove(v)[0].get("argv") != attach or nuove(v)[0].get("name") != "Rifare il deck (fork)" or nuove(v)[0].get("space") != "s1":
            return f"la copia non si aggancia nello spazio del progetto col suo nome: {nuove(v)}"
        if v["esito"] != {"ok": True, "id": "eeee2222"} or v["avvisi"]:
            return f"Fork riuscito: esito {v['esito']}, avvisi {v['avvisi']}"
        v = volta("duplica")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["duplica", "Torre", "--progetto", "Progetto X", "--cartella", "/lavori/x"]:
            return f"Duplica non chiama la sonda sulla macchina della sessione, nella sua cartella: {v['eseguiti'][:1]}"
        if len(nuove(v)) != 1 or nuove(v)[0].get("name") != "Nuova sessione":
            return f"la sessione duplicata non si aggancia: {nuove(v)}"
        v = volta("nuda")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["duplica", "qui"]:
            return f"Duplica di una sessione senza progetto né cartella: {v['eseguiti'][:1]}"
        v = volta("fork", json.dumps({"errore": "la cartella della sessione non c'è più: /lavori/x"}))
        if nuove(v) or v["avvisi"] or "non c'è più" not in (v["esito"] or {}).get("errore", ""):
            return f"un fork fallito apre una scheda, avvisa due volte o perde il motivo: {v['esito']}, {v['avvisi']}, {nuove(v)}"
        v = volta("chiudi")
        chiuse = sorted(json.dumps(x, sort_keys=True) for x in v["lanciati"])
        if v["esito"] != 2 or chiuse != sorted(json.dumps(x, sort_keys=True) for x in ({"cmd": "tab.close", "id": "tb1"}, {"cmd": "terminal.kill", "terminal": "t8"})):
            return f"Chiudi non chiude la scheda sola e il solo terminale di quella divisa: {v['esito']}, {v['lanciati']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None


def hz55(repo: Path, casa: Path) -> str | None:
    import base64  # noqa: PLC0415
    sonda = repo / "shared/volta-celeste/mods/arturo/volta_sonda.py"
    nata = {"id": "eeee2222", "sessionId": "eeee2222-bbbb", "claude": "C:/u/claude.exe", "cartella": "C:/lavori/x"}
    conf = {"macchine": [{"name": "Torre", "target": "torre.lan", "state": "connected"}], "exec": {"Torre": {"python3": nata}}}
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    log = casa / "hc.log"
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]), "HZ_HC_LOG": str(log)}

    def lancia(*args, **extra):
        log.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, str(sonda), *args], capture_output=True, text=True, timeout=90, env={**env, **extra})
        chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), chiamate
        except (ValueError, IndexError):
            return r.returncode, {"uscita": (r.stderr or r.stdout).strip()[-160:]}, chiamate

    def arg(ch):
        nascite = [c for c in ch if c[:2] == ["exec", "--on"] and c[-1] != "remoto"]
        return json.loads(base64.b64decode(nascite[-1][-1]).decode("utf-8")) if nascite else None

    rc, d, ch = lancia("fork", "Torre", "ffff1111-aaaa", "--progetto", "Progetto X", "--cartella", "C:/lavori/x", "--titolo", "Rifare il deck (fork)")
    if rc != 0 or d.get("attach", [None])[1:] != ["-t", "torre.lan", "C:/u/claude.exe", "attach", "eeee2222"] or d.get("progetto") != "Progetto X":
        return f"fork su Torre: rc {rc}, {d}"
    if arg(ch) != {"prompt": "", "progetto": "Progetto X", "cartella": "C:/lavori/x", "riprendi": "ffff1111-aaaa", "nome": "Rifare il deck (fork)"}:
        return f"fork su Torre: alla macchina arriva {arg(ch)}"
    servizi = [i for i, c in enumerate(ch) if c[:2] == ["exec", "--on"] and c[-1] == "remoto"]
    nascite = [i for i, c in enumerate(ch) if c[:2] == ["exec", "--on"] and c[-1] != "remoto"]
    if not servizi or not nascite or servizi[0] > nascite[0]:
        return "fork non accende il servizio di Claude prima di far nascere la copia"
    rc, d, ch = lancia("duplica", "Torre", "--cartella", "C:/lavori/x")
    if rc != 0 or arg(ch) != {"prompt": "", "progetto": None, "cartella": "C:/lavori/x"}:
        return f"duplica su Torre: rc {rc}, {d}, alla macchina arriva {arg(ch)}"
    for strano in (["fork", "Torre", "--all"], ["fork", "Torre", "abcd;rm -rf"], ["fork", "Torre"], ["duplica"], ["duplica", "Torre", "altro"]):
        rc, d, ch = lancia(*strano)
        if rc == 0 or ch:
            return f"{strano} non rifiutato, o lanciato lo stesso: rc {rc}, {d}"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    fbin, fapp, fbase, fcasa, lavoro = (casa / n for n in ("fbin", "fapp", "fbase", "fcasa", "lavoro x"))
    for d_ in (fbin, fapp, fbase, fcasa, lavoro):
        d_.mkdir()
    (fapp / "arturo.json").write_text(json.dumps({"base": str(fbase)}), encoding="utf-8")
    visto = casa / "claude.log"
    fc = fbin / "claude"
    fc.write_text("#!/bin/sh\n[ \"$1\" = agents ] && { echo '[]'; exit 0; }\n[ \"$1\" = daemon ] && { echo 'control.sock: reachable'; exit 0; }\n"
                  "{ pwd; printf '%%s\\n' \"$@\"; } > %s\necho 'claude attach abcd1234'\n" % shlex.quote(str(visto)), encoding="utf-8")
    fc.chmod(0o755)
    locale = {"PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "HERDR_APP_HOME": str(fapp)}

    def qui(*args):
        visto.unlink(missing_ok=True)
        rc, d, _ = lancia(*args, **locale)
        righe = visto.read_text(encoding="utf-8").splitlines() if visto.exists() else None
        return rc, d, righe

    reale = lambda x: os.path.realpath(x)  # noqa: E731
    rc, d, righe = qui("fork", "qui", "ffff1111-aaaa", "--cartella", str(lavoro), "--titolo", "--Rifare il deck (fork)")
    if rc != 0 or d.get("id") != "abcd1234" or not righe:
        return f"fork qui con un claude finto: rc {rc}, {d}"
    if reale(righe[0]) != reale(lavoro) or righe[1:] != ["--bg", "--resume", "ffff1111-aaaa", "--fork-session", "-n", "Rifare il deck (fork)"]:
        return f"fork non parte dalla cartella della sessione con --resume e --fork-session: {righe}"
    rc, d, righe = qui("fork", "qui", "ffff1111-aaaa", "--cartella", str(casa / "sparita"))
    if rc == 0 or "non c'è più" not in d.get("errore", "") or righe is not None:
        return f"fork senza la cartella della sessione: rc {rc}, {d}, claude lanciato {righe}"
    rc, d, righe = qui("fork", "qui", "ffff1111-aaaa")
    if rc == 0 or righe is not None:
        return f"fork senza cartella parte lo stesso dalla base: rc {rc}, {d}"
    rc, d, righe = qui("duplica", "qui", "--cartella", str(lavoro))
    if rc != 0 or not righe or reale(righe[0]) != reale(lavoro) or righe[1:] != ["--bg"]:
        return f"duplica non nasce vuota nella cartella della sessione: rc {rc}, {d}, {righe}"
    rc, d, righe = qui("duplica", "qui", "--cartella", str(casa / "sparita"))
    if rc != 0 or not righe or reale(righe[0]) != reale(fbase):
        return f"duplica senza la cartella non ripiega sulla base dei progetti: rc {rc}, {d}, {righe}"
    return None


PROVE = {"HZ01": hz01, "HZ02": hz02, "HZ03": hz03, "HZ04": hz04, "HZ05": hz05, "HZ06": hz06, "HZ07": hz07, "HZ08": hz08, "HZ09": hz09, "HZ10": hz10, "HZ11": hz11, "HZ12": hz12, "HZ13": hz13, "HZ14": hz14, "HZ15": hz15, "HZ16": hz16, "HZ17": hz17, "HZ18": hz18, "HZ19": hz19, "HZ20": hz20, "HZ21": hz21, "HZ22": hz22, "HZ23": hz23, "HZ24": hz24, "HZ25": hz25, "HZ26": hz26, "HZ27": hz27, "HZ28": hz28, "HZ29": hz29, "HZ30": hz30, "HZ31": hz31, "HZ32": hz32, "HZ33": hz33, "HZ34": hz34, "HZ35": hz35, "HZ36": hz36, "HZ37": hz37, "HZ38": hz38, "HZ39": hz39, "HZ40": hz40, "HZ41": hz41, "HZ42": hz42, "HZ43": hz43, "HZ44": hz44, "HZ45": hz45, "HZ46": hz46, "HZ47": hz47, "HZ48": hz48, "HZ49": hz49, "HZ50": hz50, "HZ51": hz51, "HZ52": hz52, "HZ53": hz53, "HZ54": hz54, "HZ55": hz55}


def prova(repo: Path, solo: str | None = None) -> list[str]:
    rossi = []
    for codice, f in PROVE.items():
        if solo and codice != solo:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                motivo = f(repo, Path(tmp))
            except Exception as e:  # un caso che si rompe è rosso, non ferma gli altri
                motivo = f"eccezione {type(e).__name__}: {e}"
        if motivo:
            rossi.append(f"{codice} {motivo}")
    return rossi


VELENI = [
    ("HZ35", "shared/volta-celeste/volta-claude.sh", 'if [ -z "${SSH_CONNECTION:-}" ] && [ -f "$sonda" ]', 'if [ -f "$sonda" ]'),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", '  esito=$(python3 "$sonda" servizio qui 2>&1) ||', '  esito=$(true) ||'),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", 'servizio qui 2>&1) ||', 'servizio qui 2>&1) || exit 1 ||'),
    ("HZ38", "shared/volta-celeste/volta-claude.ps1", "if (-not $env:SSH_CONNECTION -and $py", "if ($py"),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", '    if verbo == "respawn":\n        s = servizio(nome)', '    if False:\n        s = servizio(nome)'),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", '            return {"errore": "il servizio di Claude non parte su %s: %s" % (nome or "questa macchina", s["errore"])}\n    try:', '            pass\n    try:'),
    ("HZ42", "shared/volta-celeste/mods/arturo/dati.js", 'verbo === "respawn" ? 210000 : 90000', 'verbo === "respawn" ? 150000 : 90000'),
    ("HZ43", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'etichetta = "org.stellakamikaze.arturo.claude-daemon"', 'etichetta = "org.stellakamikaze.arturo.claude"'),
    ("HZ43", "shared/volta-celeste/installa-herdr.sh", "schtasks /query /tn ArturoServizioClaude ", "schtasks /query /tn ArturoServizio "),
    ("HZ43", "shared/setup-herdr.md", "`HERDR SERVIZIO`", "la riga del servizio"),
    ("HZ42", "shared/volta-celeste/mods/arturo/dati.js", "{ timeout: 360000 }", "{ timeout: 200000 }"),
    ("HZ42", "shared/volta-celeste/mods/arturo/volta_sonda.py", "            t = min(90, int(entro - time.monotonic()))", "            t = 90"),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", "if acceso():\n    esci(acceso=True, come=\"già acceso\")", "if False:\n    pass"),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", "(#5208)\n    s = servizio(nome)\n", "(#5208)\n    s = {}\n"),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", '"--name", "servizio-claude", "--no-parent", "--rm",', '"--name", "servizio-claude", "--rm",'),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True, **nulla)\n        come = "staccato"\nelif', 'subprocess.Popen([cl, "daemon", "run"], cwd=casa, **nulla)\n        come = "staccato"\nelif'),
    ("HZ41", "shared/volta-celeste/mods/arturo/volta_sonda.py", '        return {"errore": d.get("errore") or "acceso con hc run, ma non risponde ancora"}', '        return {"come": "terminale di Herdr"}'),
    ("HZ01", "shared/volta-celeste/installa-herdr.sh", '"frame.welcomed": "skipped"', '"frame.welcomed": "finished"'),
    ("HZ02", "shared/volta-celeste/installa-herdr.sh", "if k in mia and mia[k] != v and mia[k] != PRENDE.get(v):", "if False:"),
    ("HZ03", "shared/volta-celeste/installa-herdr.sh", 'Arturo funziona lo stesso nel Terminale."; exit 0 ;;', 'Arturo funziona lo stesso nel Terminale." ;;'),
    ("HZ04", "hooks/herdr-stato.sh", '[ -n "${HC_TERMINAL_ID:-}" ] || exit 0', ":"),
    ("HZ05", "settings.json", "herdr-stato.sh done", "herdr-stato.sh idle"),
    ("HZ09", "shared/volta-celeste/mods/arturo/dati.js", 'prompt: "/guidami"', 'prompt: "/guidamii"'),
    ("HZ10", "shared/volta-celeste/mods/arturo/partenza.js", "catena.slice(qui + 1)", "catena.slice(qui)"),
    ("HZ11", "shared/volta-celeste/mods/arturo/settimana.js", "else if (te) liste.te.push", "if (te) liste.te.push"),
    ("HZ12", "shared/volta-celeste/mods/arturo/azioni.js", "if (quando === t.quando) continue;", ""),
    ("HZ12", "shared/volta-celeste/mods/arturo/azioni.js", 'argv: ["inizia"', 'argv: ["riprendi"'),
    ("HZ12", "shared/volta-celeste/mods/arturo/todo.js", "const g = inizia(item);", "const g = null;"),
    ("HZ14", "shared/volta-celeste/mods/arturo/nota.js", "if (!t) return null;", ""),
    ("HZ14", "shared/volta-celeste/mods/arturo/nota.js", '"--chi", "io"', '"--chi", "tu"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", 'python3 - "$plist" "$copia/arturo-app.sh"', 'python3 - "$plist" "$qui/arturo-app.sh"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", '-c "Set :CFBundleIdentifier $ID"', '-c "Set :CFBundleIdentifier dev.herdr.app"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", 'if [ -d "$arturo" ] && { [ ! -d "$herdr" ] || ! piu_nuova "$v_herdr" "$v_arturo"; }; then base=$arturo; fi', ":"),
    ("HZ06", "shared/volta-celeste/installa-herdr.sh", '[ "$firma" = assente ]', '[ "$firma" = mai ]'),
    ("HZ07", "shared/volta-celeste/mods/arturo/main.js", 'from "./notaui.js"', 'from "./notaui-perso.js"'),
    ("HZ07", "shared/volta-celeste/mods/arturo/main.js", ", nota: Nota, note: Note };", ", note: Note };"),
    ("HZ07", "shared/volta-celeste/layouts/arturo.json", '"parte": "stato"', '"parte": "stato-perso"'),
    ("HZ16", "shared/volta-celeste/servizi-gui.sh", "plist herdr-core false", "plist herdr-core true"),
    ("HZ16", "shared/volta-celeste/servizi-gui.sh", 'rm -f "$agenti/$PREFISSO.claude-daemon.plist"', 'plist claude-daemon true "$claude" daemon run'),
    ("HZ15", ".gitignore", "data/note-finestra/\n", ""),
    ("HZ15", ".gitignore", "data/herdr-invito\n", ""),
    ("HZ17", "shared/volta-celeste/mods/arturo/sessioni.js", "|| titolo(a).localeCompare(titolo(b)));", "|| titolo(b).localeCompare(titolo(a)));"),
    ("HZ17", "shared/volta-celeste/mods/arturo/sessioni.js", "if (giu.length && out.length) out[out.length - 1].nota", "if (giu.length && out.length) out[0].nota"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", 'if (s.stato === "lavora") return { azione', "if (false) return { azione"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "if (s.vecchia) return { azione", "if (false) return { azione"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "|| argv.some((a) => dentro(a, s.id)))", ")"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", '${id.replace(/[^\\w-]/g, "")}\\\\b`', '${id.replace(/[^\\w-]/g, "")}`'),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "\\\\battach['\"]?\\\\s+['\"]?", "\\\\battach\\\\s+"),
    ("HZ19", "shared/volta-celeste/mods/arturo/barra.js", 'else if (c.startsWith("volta-")) this.volta.premiId(c.slice(6), cx);', ""),
    ("HZ19", "shared/volta-celeste/mods/arturo/volta.js", "if (!this.script) return null;", ""),
    ("HZ20", "shared/volta-celeste/mods/arturo/volta.js", 'exec(this.py, [this.script, "volta"', 'exec("python3", [this.script, "volta"'),
    ("HZ21", "shared/volta-celeste/installa-herdr.sh", "app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}",
     'if [ "$sistema" = windows ]; then app_home=${HERDR_APP_HOME:-${APPDATA:-$HOME/AppData/Roaming}/herdr-app}; '
     "else app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}; fi"),
    ("HZ22", "shared/volta-celeste/installa-herdr.sh", '[ "$sistema" = mac-arm ] || tasti=keys-ctrl.json', ":"),
    ("HZ22", "shared/volta-celeste/keys-ctrl.json", '"ctrl-shift-i": "arturo.note"', '"ctrl-shift-e": "arturo.note"'),
    ("HZ23", "shared/volta-celeste/installa-herdr.sh", 'if "$c" -c "import sys" >/dev/null 2>&1; then py=$c; break; fi',
     'if command -v "$c" >/dev/null 2>&1; then py=$c; break; fi'),
    ("HZ24", "shared/volta-celeste/mods/arturo/testata.js", "const scorciatoie = `${k.apri} apri un progetto",
     "const scorciatoie = `⌘O apri un progetto"),
    ("HZ25", "shared/volta-celeste/mods/arturo/suggerimenti.js", ".on_click(async () => { try { await esegui(sug); } finally { dopo?.(); } })",
     ".on_click(() => { dopo?.(); esegui(sug); })"),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "const mainW = testata.larghezza - 2 * pad - (pannelloW ? pannelloW + gap : 0);",
     "const mainW = testata.larghezza - 2 * pad;"),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "if (Math.abs(marchio.altezza + barra.altezza + piede.altezza - H) > 2) return null;", ""),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "if (Math.abs(S + (m.divisore ?? 1) + testata.larghezza - W) > 2) return null;", ""),
    ("HZ26", "shared/volta-celeste/mods/arturo/main.js", "if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;", "return el;"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", "if (Number.isInteger(n.numero)) return n;", "return n;"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", 'stato: "aperta", chiusa_quando: null', 'stato: "presa", chiusa_quando: null'),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", "n.punto.x * W / f.larghezza", "n.punto.x"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", '"--note", riga, "--json", "--"', '"--note", riga, "--"'),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", "Per partire: arturo note mostra ${dati.id}", "Per partire: ${dati.id}"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "recente(b).localeCompare(recente(a))", "recente(a).localeCompare(recente(b))"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "numero: aperta ? n.numero : null", "numero: n.numero"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "  if (!prima) return [];\n", ""),
    ("HZ28", "shared/volta-celeste/keys.json", '"cmd-shift-e": "arturo.note"', '"cmd-shift-l": "arturo.note"'),
    ("HZ28", "shared/volta-celeste/mods/arturo/testata.js", ".on_click(() => apriElenco())", ""),
    ("HZ28", "shared/volta-celeste/mods/arturo/noteui.js", "run(`arturo.nota-${r.id}`);\n    this.chiudi();", "this.chiudi();\n    run(`arturo.nota-${r.id}`);"),
    ("HZ29", "bin/note_finestra.py", 'return {**n, "stato": "presa"}', "return n"),
    ("HZ29", "bin/note_finestra.py", 'presi = {n["numero"] for n in qui if n["numero"] is not None}', "presi = set()"),
    ("HZ29", "bin/note_finestra.py", 'sul_todo(n, ["fatto"] if stato == "risolta"', 'sul_todo(n, ["inizia"] if stato == "risolta"'),
    ("HZ29", "bin/note_finestra.py", "x = min(max(px - w // 2, 0), W - w)", "x = max(px - w // 2, 0)"),
    ("HZ29", "bin/note_finestra.py", "scala = W / f[\"larghezza\"] if f.get(\"larghezza\") else 1", "scala = 1"),
    ("HZ29", "bin/note_finestra.py", 'if n["stato"] not in APERTE:\n        raise ErroreNota(f"la nota {n[\'id\']} è già {n[\'stato\']}")\n    v = ', "v = "),
    ("HZ29", "bin/arturo", '    "note": ("note_finestra",', '    "notte": ("note_finestra",'),
    ("HZ30", "bin/note_finestra.py", "        if ora != letto:", "        if False:"),
    ("HZ31", "shared/volta-celeste/mods/arturo/notaui.js", "const r = await gestoNota(VERBI[che], n.id, testo);", "const r = { ok: true };"),
    ("HZ31", "shared/volta-celeste/mods/arturo/notaui.js", 'risolta: "risolvi"', 'risolta: "scarta"'),
    ("HZ31", "shared/volta-celeste/mods/arturo/dati.js", '"--chi", "federico", "--json"', '"--json"'),
    ("HZ31", "shared/volta-celeste/mods/arturo/dati.js", '...(t ? ["--", t] : [])', '...(t ? [t] : [])'),
    ("HZ31", "bin/note_finestra.py", 'if not testo and chi == "claude":', "if not testo:"),
    ("HZ32", "shared/volta-celeste/mods/arturo/nota.js", '{ id: "va-bene", etichetta: "Va bene così" }', '{ id: "va-bene", etichetta: "Va bene" }'),
    ("HZ32", "bin/note_finestra.py", '"presa": "Claude ci lavora", "risolta"', '"presa": "Presa", "risolta"'),
    ("HZ32", "bin/note_finestra.py", 'APERTE = ("aperta", "presa")', 'APERTE = ("aperta",)'),
    ("HZ32", "shared/volta-celeste/mods/arturo/nota.js", 'export const TIPO_PREDEFINITO = "correggere";', 'export const TIPO_PREDEFINITO = "domanda";'),
    ("HZ32", "bin/note_finestra.py", '"cwd": None, "testo_terminale": None}', '"cwd": None}'),
    ("HZ32", "docs/volta-celeste.md", "dice a chi l'ha scritta che ci lavori", "dice a Federico che ci lavori"),
    ("HZ09", "shared/volta-celeste/mods/arturo/dati.js", "Segui {radice}/shared/volta-celeste/trova-progetti.md", "Segui ~/.claude/shared/volta-celeste/trova-progetti.md"),
    ("HZ01", "shared/volta-celeste/installa-herdr.sh", '"radice": os.environ["ARTURO_RADICE"], ', ""),
    ("HZ33", "shared/volta-celeste/mods/arturo/dati.js", "const prompt = richiesta(sug.prompt, (await config()).radice);", "const prompt = sug.prompt;"),
    ("HZ33", "shared/volta-celeste/mods/arturo/dati.js", ": radiceDa(arturo[arturo.length - 1]),", ": `${home()}/.claude`,"),
    ("HZ33", "shared/volta-celeste/mods/arturo/dati.js", "[\\\\/]bin[\\\\/]arturo", "[/]bin[/]arturo"),
    ("HZ08", "hooks/session-start.sh", 'mkdir -p "$HOME/.claude/data" && date +%Y-%m-%d > "$HOME/.claude/data/herdr-invito"', ":"),
    ("HZ34", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'for py in ("python3", "python"):', 'for py in ("python3",):'),
    ("HZ34", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'return [v for v in voci if v.get("claude") or ("irraggiungibile" in v and (v["questa"] or v["host"] in viste))]', 'return voci'),
    ("HZ34", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'sessioni += [dict(r, vecchia=True)', 'sessioni += [dict(r)'),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", '[ "${CLAUDE_QUI:-0}" = 1 ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", "  agents | attach | auth |", "  agentsX | attach | auth |"),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", "grep -v '^Starting background service' | ", ""),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", '[ -n "$senza_id" ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", '[ -n "${HC_TERMINAL_ID:-}" ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta-celeste/volta-claude.sh", 'printf \'Volta: la sessione non parte in background (%s). La apro qui, come prima.\\n\' "$motivo" >&2', "exit 1"),
    ("HZ36", "shared/volta-celeste/nascita.sh", "!dentro' \"$f\" > \"$tmp\"", "1' \"$f\" > \"$tmp\""),
    ("HZ36", "shared/volta-celeste/nascita.sh", "! typeset -f claude >/dev/null 2>&1; then", "true; then"),
    ("HZ36", "shared/volta-celeste/nascita.sh", "then printf '\\n' >> \"$1\"; fi", "then :; fi"),
    ("HZ36", "shared/volta-celeste/installa-herdr.sh", "&& ! printf '%s\\n' \"$stato_nascita\" | grep -q '^rifiutata'; then", "; then"),
    ("HZ36", "shared/volta-celeste/installa-herdr.sh", "if printf '%s\\n' \"$stato_nascita\" | grep -q '^assente' &&", "if false &&"),
    ("HZ36", "shared/volta-celeste/nascita.sh", 'rm -f "$NO" "$app/nascita-no"', ":"),
    ("HZ37", "shared/volta-celeste/nascita.sh", "    for f in $(tutti_i_file); do\n      if [ -f \"$f\" ] && grep -qF \"$INIZIO\" \"$f\"; then togli_da", "    for f in $(file_shell); do\n      if [ -f \"$f\" ] && grep -qF \"$INIZIO\" \"$f\"; then togli_da"),
    ("HZ37", "shared/volta-celeste/nascita.sh", "{ l = $0; sub(/\\r$/, \"\", l) } l == a { dentro = 1; next }", "{ l = $0 } l == a { dentro = 1; next }"),
    ("HZ37", "shared/volta-celeste/nascita.sh", "awk -v BINMODE=3 -v a=", "awk -v a=", "windows"),  # l'awk di Git per Windows toglie i \r
    ("HZ37", "shared/volta-celeste/nascita.sh", '      if utf16 "$f"; then say "NASCITA UTF16 $f"; continue; fi', "      :"),
    ("HZ37", "shared/volta-celeste/nascita.sh", '      mkdir -p "$(dirname "$f")"', "      :"),
    ("HZ37", "shared/volta-celeste/nascita.sh", 'case "$pol" in Restricted | AllSigned) say', 'case "$pol" in Nessuna) say'),
    ("HZ38", "shared/volta-celeste/nascita.sh", "and -not (Get-Command claude -CommandType Function -ErrorAction SilentlyContinue)) {", ") {"),
    ("HZ37", "shared/volta-celeste/installa-herdr.sh", '[ "$sistema" = windows ] && cp "$qui/volta-claude.ps1"', '[ "$sistema" = nessuno ] && cp "$qui/volta-claude.ps1"'),
    ("HZ38", "shared/volta-celeste/volta-claude.ps1", "if ($env:CLAUDE_QUI -eq '1') { Qui }", "#"),
    ("HZ38", "shared/volta-celeste/volta-claude.ps1", "if ($senzaId) { Qui }", "#"),
    ("HZ38", "shared/volta-celeste/volta-claude.ps1", "$_ -and $_ -notmatch '^Starting background service'", "$_"),
    ("HZ39", "shared/volta-celeste/mods/arturo/volta_sonda.py", "\n        if rc != 0 and (non_parte(out, err) or rc == 9009):", "\n        if True:"),  # quella di nasci, non di servizio
    ("HZ40", "shared/volta-celeste/mods/arturo/volta_sonda.py", '        argv = hc() + ["exec", "--on", nome, "--timeout", str(ATTESA_AZIONE - 5), "claude", verbo, sid]', '        argv = hc() + ["exec", nome, "--timeout", str(ATTESA_AZIONE - 5), "claude", verbo, sid]'),
    ("HZ40", "shared/volta-celeste/mods/arturo/volta_sonda.py", '    if not ID.fullmatch(sid or ""):  # mai', "    if False:  # mai"),
    ("HZ40", "shared/volta-celeste/mods/arturo/volta_sonda.py", "    if verbo not in VERBI:", "    if False:"),
    ("HZ40", "shared/volta-celeste/mods/arturo/volta_sonda.py", '            if fin == "G":\n                c = n - 1', '            if fin == "G":\n                pass'),
    ("HZ40", "shared/volta-celeste/mods/arturo/volta_sonda.py", "    fuori = (\"Checking for updates\",)", "    fuori = (\"zzz\",)"),
    ("HZ40", "shared/volta-celeste/mods/arturo/sessioni.js", 'if (s.stato === "lavora" || s.stato === "aspetta") out.push', 'if (s.stato === "lavora") out.push'),
    ("HZ40", "shared/volta-celeste/mods/arturo/sessioni.js", "  if (!prima) return [];", "  if (!prima) prima = { sessioni: [] };"),
    ("HZ40", "shared/volta-celeste/mods/arturo/sessioni.js", "if (s.id && !s.vecchia) out[s.id]", "if (s.id) out[s.id]"),
    ("HZ40", "shared/volta-celeste/mods/arturo/sessioni.js", 'out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" })', 'out.push({ verbo: "rm", testo: "Elimina" })'),
    ("HZ39", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'dati = {"prompt": prompt or "", "progetto": progetto}', 'dati = {"prompt": "", "progetto": progetto}'),
    ("HZ39", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'if m["stato"] not in (None, "connected"):', "if False:"),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'return nasciSu(soloQui ? "qui" : dove(), prompt, null);', 'return nasciSu(dove(), prompt, null);'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'return typeof d === "string" && altreMacchine().some((m) => m.host === d) ? d : "qui";', 'return typeof d === "string" && d ? d : "qui";'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'return nasciSu(dove(), prompt, nome);', 'return nasciSu("qui", prompt, nome);'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'const v = await apriSessione({ id: esito.id, sessionId: esito.sessionId, nome, progetto, questa: macchina === "qui", host: macchina }, esito.attach, true);', "const v = {};"),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'questa: macchina === "qui", host: macchina }, esito.attach, true);', 'questa: macchina === "qui", cartella: "/base", host: macchina }, esito.attach, true);'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'return s.status ?? statoAgganciata(schedaAgganciata(s));', 'return s.status ?? null;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'return s.status ?? statoAgganciata(schedaAgganciata(s));', 'return statoAgganciata(schedaAgganciata(s)) ?? s.status;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'if (v?.host === "qui") out[id] = v.stato;', 'out[id] = v.stato;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", "(b.tab === attiva) - (a.tab === attiva)", "0"),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'if (statoAgganciata(g) === "blocked") return notify', 'if (false) return notify'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'const g = a || !s ? null : schedaAgganciata(s);', 'const g = null;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'stato: statoSpazio(s)', 'stato: s?.status ?? null'),
    ("HZ39", "shared/volta-celeste/mods/arturo/testata.js", 'const st = statoSpazio(s);', 'const st = s?.status;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/todo.js", 'statoSpazio(spazio(p))', 'spazio(p)?.status'),
    ("HZ39", "shared/volta-celeste/mods/arturo/todo.js", '    const st = statoSpazio(s);', '    const st = s.status;'),
    ("HZ39", "shared/volta-celeste/mods/arturo/barra.js", '|| Object.values(statiQui()).includes("aspetta")', ''),
    ("HZ39", "shared/volta-celeste/mods/arturo/barra.js", '`|${JSON.stringify(statiQui())}|', '`|'),
    ("HZ39", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'app = os.environ.get("HERDR_APP_HOME") or ', "app = "),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'const args = [c.volta, copia ? copia.verbo : "nasci", macchina,', 'const args = [`${appHome()}/mods/arturo/volta_sonda.py`, copia ? copia.verbo : "nasci", macchina,'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", "const g = a ? null : schedaAgganciata(s);", "const g = null;"),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'if (Array.isArray(t?.argv) && t.argv.includes("attach"))', "if (false)"),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", 'if (sug.dove === "nuova") return nuova(prompt, true);', 'if (sug.dove === "nuova") return nuova(prompt);'),
    ("HZ39", "shared/volta-celeste/mods/arturo/dati.js", "if (!a && !g) return nuova(prompt, true);", "if (!a && !g) return nuova(prompt);"),
    ("HZ39", "shared/volta-celeste/mods/arturo/testata.js", ".when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)));", ";"),
    ("HZ34", "shared/volta-celeste/mods/arturo/dati.js", "`${appHome()}/mods/arturo/volta_sonda.py`", "`${home()}/.claude/scripts/teletrasporto.py`"),
    ("HZ34", "shared/volta-celeste/mods/arturo/volta.js", "esiste(c.volta)", "esiste(`${home()}/x/volta_sonda.py`)"),
    ("HZ44", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'sessioni = agenti(["--all"])', "sessioni = agenti([])"),
    ("HZ44", "shared/volta-celeste/mods/arturo/volta_sonda.py", '            or (s.get("startedAt") or 0) >= soglia]', "            or True]"),
    ("HZ44", "shared/volta-celeste/mods/arturo/volta_sonda.py", "    sessioni = agenti([]) or []", "    sessioni = []"),
    ("HZ44", "shared/volta-celeste/mods/arturo/barra.js", 'else if (c.startsWith("volta-altro-")) this.volta.altroId(c.slice(12), cx);', ""),
    ("HZ44", "shared/volta-celeste/mods/arturo/volta.js", "this.menu = s.sessionId;\n    this.scopri(s);\n    this.fare(s, a, cx);", "this.menu = s.sessionId;"),
    ("HZ44", "shared/volta-celeste/mods/arturo/volta.js", 'if (g && s.stato === "ferma") this.aperti[g.chiave] = true;', ""),
    ("HZ45", 'hooks/titolo-sessione.py', '        if salvato.get("titolo"):\n            return 0\n', ''),
    ("HZ45", 'hooks/titolo-sessione.py', '    if salvato.get("fonte") == "modello" and adesso - float(salvato.get("quando") or 0) < ogni:\n        return 0\n', ''),
    ("HZ45", 'hooks/titolo-sessione.py', '    if salvato.get("fonte") == "modello" and peso <= int(salvato.get("peso") or 0):\n        return 0\n', ''),
    ("HZ45", 'hooks/titolo-sessione.py', '    if len(righe) != 1:\n        return ""\n', '    righe = righe[:1]\n'),
    ("HZ45", 'hooks/titolo-sessione.py', '    return t if 2 <= len(t) <= LUNGO else ""', '    return t'),
    ("HZ45", 'hooks/titolo-sessione.py', 'if os.environ.get("ARTURO_TITOLI") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):', 'if os.environ.get("ARTURO_TITOLO_FIGLIO"):'),
    ("HZ45", 'hooks/titolo-sessione.py', 'if os.environ.get("ARTURO_TITOLI") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):', 'if os.environ.get("ARTURO_TITOLI") == "0":'),
    ("HZ45", 'hooks/titolo-sessione.py', 'env = dict(os.environ, ARTURO_TITOLO_FIGLIO="1", ', 'env = dict(os.environ, '),
    ("HZ45", 'hooks/titolo-sessione.py', '"--settings", \'{"disableAllHooks":true}\', ', ''),
    ("HZ45", 'hooks/titolo-sessione.py', '    return r.stdout if r.returncode == 0 else ""', '    return r.stdout or "Titolo di ripiego"'),
    ("HZ45", 'hooks/titolo-sessione.py', ' or d.get("isMeta"):', ':'),
    ("HZ45", 'hooks/titolo-sessione.py', '        if " -- " in resto:\n            resto = resto.split(" -- ", 1)[1]\n', ''),
    ("HZ45", 'shared/volta-celeste/mods/arturo/volta_sonda.py', '            s["titolo"] = t.strip()[:80]', '            pass'),
    ("HZ45", 'shared/volta-celeste/mods/arturo/sessioni.js', '  if (scritto) return scritto;\n', ''),
    ("HZ45", 'shared/volta-celeste/mods/arturo/volta.js', '=== "macchina" ? "macchina" : "progetto"', '=== "progetto" ? "progetto" : "macchina"'),
    ("HZ45", "shared/volta-celeste/mods/arturo/volta.js", "(s.titolo ? div().whitespace_normal() : div().truncate())", "div().truncate()"),
    ("HZ46", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'tx[:400].rsplit(None, 1)[0] + "\\u2026"', 'tx[:400]'),
    ("HZ46", "shared/volta-celeste/mods/arturo/volta_sonda.py", '"risposta": (s.get("risposta") or "")[:420],', '"risposta": (s.get("risposta") or "")[:200],'),
    ("HZ46", "shared/volta-celeste/mods/arturo/sessioni.js", '.replace(/^\\s*(#+|>)\\s*/, "")', ''),
    ("HZ46", "shared/volta-celeste/mods/arturo/sessioni.js", 'const senzaSegni = (r) => r.replace(/\\*\\*|`/g, "")', 'const senzaSegni = (r) => r.replace(/[*_`]/g, "")'),
    ("HZ46", "shared/volta-celeste/mods/arturo/sessioni.js", '  return out.length ? out : null;', '  return out;'),
    ("HZ46", "shared/volta-celeste/mods/arturo/sessioni.js", '.replace(/:$/, "")', ''),
    ("HZ46", "shared/volta-celeste/mods/arturo/volta.js", '    if (a.verbo === "logs" && anteprima(s)) { this.anteprime[k] = true; return cx.notify(); }\n', ''),
    ("HZ46", "shared/volta-celeste/mods/arturo/volta.js", ': div().id(id).whitespace_normal().text_size(12.5)', ': div().id(id).truncate().text_size(12.5)'),
    ("HZ47", "shared/volta-celeste/mods/arturo/volta.js", "      .when(Boolean(avviso) && !aperto, (el)", "      .when(aperto, (el) => el.child(this.gesti(t, s, az)))\n      .when(Boolean(avviso) && !aperto, (el)"),
    ("HZ47", "shared/volta-celeste/mods/arturo/volta.js", "\n      .when(Boolean(gesti), (el) => el.child(gesti));", ";"),
    ("HZ47", "shared/volta-celeste/mods/arturo/volta.js", "const gesti = chiusa || !corpo ? null : this.pannello(t);", "const gesti = null;"),
    ("HZ47", "shared/volta-celeste/mods/arturo/volta.js", "      .child(this.gesti(t, s, az))\n      .when(Boolean(avviso), (el)", "      .when(Boolean(avviso), (el)"),
    ("HZ47", "shared/volta-celeste/mods/arturo/volta.js", ".when(Boolean(avviso) && !aperto, (el)", ".when(Boolean(avviso), (el)"),
    ("HZ48", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'lavoro = s.get("id") if fondo else None', "lavoro = None"),
    ("HZ48", "shared/volta-celeste/mods/arturo/volta_sonda.py", 'corto = lavoro if isinstance(lavoro, str)', 'corto = sid[:8] if isinstance(lavoro, str)'),
    ("HZ49", "shared/volta-celeste/mods/arturo/volta.js", 'const rm = az.find((a) => a.verbo === "rm");', 'const rm = az.find((a) => a.verbo === "stop");'),
    ("HZ49", "shared/volta-celeste/mods/arturo/volta.js", "const vediX = Boolean(rm) && (this.sopra === k || chiedoRm || facciorm);", "const vediX = Boolean(rm);"),
    ("HZ49", "shared/volta-celeste/mods/arturo/volta.js", ".on_click((_e, cx) => this.fare(s, rm, cx))", ""),
    ("HZ50", "shared/volta-celeste/mods/arturo/barra.js", '.child(voce("note", "pin", "Note", () => apriElenco())', '.child(voce("note", "pin", "Note", () => apriGuida())'),
    ("HZ50", "shared/volta-celeste/layouts/arturo.json", '"px": 190', '"px": 156'),
    ("HZ51", "shared/volta-celeste/mods/arturo/sessioni.js", "].sort((a, b) => tempo(b) - tempo(a) || titolo(a)", "].sort((a, b) => tempo(a) - tempo(b) || titolo(a)"),
    ("HZ51", "shared/volta-celeste/mods/arturo/sessioni.js", "    out.sort((a, b) => recente(b) - recente(a) || a.titolo.localeCompare(b.titolo));\n", ""),
    ("HZ51", "shared/volta-celeste/mods/arturo/sessioni.js", ".filter((g) => g.sessioni.length)).sort((a, b) => recente(b) - recente(a));", ".filter((g) => g.sessioni.length));"),
    ("HZ51", "shared/volta-celeste/mods/arturo/sessioni.js", "const recente = (g) => Math.max(0, ...g.sessioni.map(tempo));", "const recente = (g) => Math.min(...g.sessioni.map(tempo));"),
    ("HZ51", "shared/volta-celeste/mods/arturo/volta_sonda.py", '"ultimo": s.get("ultimo") or nascita(s),', '"ultimo": s.get("ultimo") or "",'),
    ("HZ51", "shared/volta-celeste/mods/arturo/volta_sonda.py", "time.gmtime(t / 1000))", "time.gmtime(t))"),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'const etichetta = l.filter((x) => x.labels?.[ETICHETTA] === s.id);', 'const etichetta = [];'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'for (const x of schede) if (!(await nuda(x.address))) { scheda = x; break; }', 'for (const x of schede) { scheda = x; break; }'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'f.pid === d.pid && JSON.stringify(f.argv) !== JSON.stringify(d.argv);', 'f.pid === d.pid;'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'const a = await prepara(s, s.stato === "errore");', 'const a = await prepara(s, false);'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '  if (!pronta) {', '  if (true) {'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '    if (a.errore) return { errore: `Non la apro: ${a.errore}.` };\n', ''),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '  if (riavviata) return fallita;\n', ''),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '  if (!(await nuda(indirizzo))) return {};\n  const fallita', '  const fallita'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '    run("space.select", { id: sp.id });\n    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv });', '    const tab = sp.tabs.find((tb) => tb.name === nome);\n    if (tab) return run("tab.select", { id: tab.id });\n    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv });'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '(/^[\\w@%+=:,./-]+$/.test(String(a)) ? String(a)', '(true ? String(a)'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'slug(s.name) !== "volta" ? slug(s.name) : null;', 'slug(s.name) !== "volta" ? slug(s.name) : slug(s.name);'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', '    if (scheda) await etichetta(scheda, s);\n  }\n  return { come: rilancia', '  }\n  return { come: rilancia'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'const r = await hc(["send", scheda.address, comando(argv)]);', 'const r = { code: 0 };'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/dati.js', 'return nasciSu(dove(), "", progetto, "Nuova sessione");', 'return nasciSu(dove(), "", progetto);'),
    ('HZ52', 'shared/volta-celeste/mods/arturo/volta.js', '      if (v?.errore) this.avvisa(s, v.errore, cx);\n', ''),
    ('HZ19', 'shared/volta-celeste/mods/arturo/volta.js', 'if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);', 'if (d.azione === "aggancia") return this.apri(s, d.argv, true, cx);'),
    ('HZ53', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '    if riavvia:\n        r = azione(nome, "respawn", sid)', '    if False:\n        r = azione(nome, "respawn", sid)'),
    ('HZ53', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '    if ID.fullmatch(sid or "") is None:', '    if False:'),
    ('HZ53', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '        return {"ok": True, "riavviata": True}\n    s = servizio(nome)', '        return {"ok": True, "riavviata": True}\n    s = {}'),
    ('HZ53', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '        if not r.get("ok"):\n            return {"errore": "non si riavvia: %s"', '        if False:\n            return {"errore": "non si riavvia: %s"'),
    ('HZ53', 'shared/volta-celeste/keys.json', '"cmd-t": "arturo.volta-nuova"', '"cmd-y": "arturo.volta-nuova"'),
    ('HZ53', 'shared/volta-celeste/keys-ctrl.json', '"ctrl-shift-t": "arturo.volta-nuova"', '"ctrl-shift-y": "arturo.volta-nuova"'),
    ('HZ53', 'shared/volta-celeste/installa-herdr.sh', 'if k in mia and mia[k] != v and mia[k] != PRENDE.get(v):', 'if k in mia and mia[k] != v:'),
    ('HZ53', 'shared/volta-celeste/installa-herdr.sh', 'mia[k] != PRENDE.get(v):', 'v not in PRENDE:'),
    ('HZ53', 'shared/volta-celeste/mods/arturo/barra.js', '        else if (c === "volta-nuova") await nuovaScheda();\n', ''),
    ('HZ22', 'shared/volta-celeste/installa-herdr.sh', 'PRENDE = {"arturo.volta-nuova": "tab.new"}', 'PRENDE = {}'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', 'if (s.tipo === "background") out.push({ verbo: "chiudi", testo: "Chiudi" });', 'out.push({ verbo: "chiudi", testo: "Chiudi" });'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', 'if (!s || s.vecchia) return [];\n  const out = [{ verbo: "apri"', 'if (!s) return [];\n  const out = [{ verbo: "apri"'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', 'return out.concat(azioni(s).filter((a) => a.verbo !== "stop"));', 'return out.concat(azioni(s));'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', '.slice(0, 53).trim()} (fork)`', '.slice(0, 53).trim()} (copia)`'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', '`${titolo(s).slice(0, 53).trim()} (fork)`', '`${titolo(s)} (fork)`'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/sessioni.js', 'out.push({ verbo: "duplica", testo: "Duplica" }, { verbo: "fork", testo: "Fork" });', 'out.push({ verbo: "duplica", testo: "Duplica" });'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '...(copia?.verbo === "fork" ? [copia.sessionId] : []),', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '...(copia?.cartella ? ["--cartella", copia.cartella] : []),', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '...(copia?.titolo ? ["--titolo", copia.titolo] : []),', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', 'if (!copia) notify({ title: `La sessione non nasce su', 'notify({ title: `La sessione non nasce su'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', 'return nasciSu(s.host ?? "qui", "", s.progetto', 'return nasciSu(dove(), "", s.progetto'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '{ verbo: fork ? "fork" : "duplica", sessionId: s.sessionId,', '{ verbo: fork ? "fork" : "duplica", sessionId: s.id,'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', 'fork ? titoloFork(s).slice(0, 40) : "Nuova sessione",', '"Nuova sessione",'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', 'if (panes().filter((x) => x.tab === p.tab).length === 1) run("tab.close", { id: p.tab });', 'if (true) run("tab.close", { id: p.tab });'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '    else run("terminal.kill", { terminal: t.address });\n', '    else run("tab.close", { id: p.tab });\n'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/dati.js', '      return v.errore ? { errore: v.errore } : { ok: true, id: esito.id };\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', '      .on_mouse_down("right", (_e, cx) => { if (apriMenuSessione(s)) cx.stop_propagation(); })\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', '    if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', '    if (a.verbo === "apri") return this.premi(s, cx);\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', '    chiudiSchede(s);\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', 'a.verbo === "duplica" || a.verbo === "fork" ? await copiaSessione(s, a.verbo)', 'false ? await copiaSessione(s, a.verbo)'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', '      : lavoro ? { testo: lavoro, colore: "working" } : dettaglio(s, modo);', '      : dettaglio(s, modo);'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/volta.js', 'const voci = menu(s).concat(azioni(s).filter((x) => x.verbo === "stop"));', 'const voci = azioni(s);'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/barra.js', '        else if (c.startsWith("volta-menu-")) this.volta.menuId(c.slice(11));\n', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/main.js', 'sessione: MenuSessione, ', ''),
    ('HZ54', 'shared/volta-celeste/mods/arturo/menusessione.js', '    run(comandoGesto(this.s, v));\n    this.chiudi();', '    this.chiudi();\n    run(comandoGesto(this.s, v));'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/menusessione.js', '`arturo.volta-gesto-${v.verbo}-${s.id}`', '`arturo.volta-fai-${v.verbo}-${s.id}`'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/menusessione.js', 'kind: "popup", width: 230', 'kind: "dialog", width: 230'),
    ('HZ54', 'shared/volta-celeste/mods/arturo/menusessione.js', 'this.voci = menu(this.s);', 'this.voci = [];'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'argv += ["--resume", a["riprendi"], "--fork-session"]', 'argv += ["--resume", a["riprendi"]]'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'if a.get("riprendi") and not qui:', 'if False:'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'if qui:\n    base = cartella', 'if False:\n    base = cartella'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'qui = bool(cartella) and os.path.isdir(cartella)', 'qui = bool(cartella)'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'nome = str(a.get("nome") or "").lstrip("-").strip()[:60]', 'nome = str(a.get("nome") or "").strip()[:60]'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'if riprendi is not None and not ID.fullmatch(riprendi or ""):', 'if False:'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '(("cartella", cartella), ("riprendi", riprendi), ("nome", titolo))', '(("cartella", cartella), ("riprendi", None), ("nome", titolo))'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '(("cartella", cartella), ("riprendi", riprendi), ("nome", titolo)) if v})', '(("cartella", cartella), ("riprendi", riprendi), ("nome", None)) if v})'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '        esito = nasci(resto[0], "", opz.get("progetto"), opz.get("cartella"))\n', '        esito = nasci(resto[0], "", opz.get("progetto"))\n'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '        esito = nasci(resto[0], "", opz.get("progetto"), opz.get("cartella"), resto[1], opz.get("titolo"))', '        esito = nasci(resto[0], "", None, opz.get("cartella"), resto[1], opz.get("titolo"))'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '    if argv and argv[0] in COPIE:\n', '    if False:\n'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', '    attesi = 2 if verbo == "fork" else 1\n', '    attesi = len(resto)\n'),
    ('HZ55', 'shared/volta-celeste/mods/arturo/volta_sonda.py', 'argv += ["-n", nome]', 'argv += [nome]'),
]


def non_gira_qui(caso: str) -> str | None:
    """Il motivo per cui il caso esce verde subito su questa macchina, o None se gira (#5163).

    Le condizioni sono quelle dei casi: hz04 vuole un pty, hz08 un Mac Apple Silicon, hz13 e hz16
    un Mac. Dove il caso non gira il suo veleno non ha cosa rompere, e il giro lo dichiara saltato
    invece di fermarsi su "NON ATTACCA". Dove il caso gira, il veleno resta obbligatorio.
    """
    mac = sys.platform == "darwin"
    if caso == "HZ04" and os.name == "nt":
        return "niente pty su Windows: il caso gira su macOS e Linux"
    if caso == "HZ08" and not (mac and subprocess.run(["sysctl", "-n", "hw.optional.arm64"],
                                                      capture_output=True, text=True).stdout.strip() == "1"):
        return "l'invito a Herdr parte solo sui Mac Apple Silicon"
    if caso == "HZ36" and os.name == "nt":
        return "su Windows la nascita va nel profilo di PowerShell, non nei file di zsh e bash"
    if caso == "HZ38" and not (shutil.which("pwsh") or shutil.which("powershell")):
        return "niente PowerShell qui: volta-claude.ps1 gira su Windows"
    if caso in ("HZ13", "HZ16") and not mac:
        return "Arturo.app e i servizi di launchd ci sono solo sul Mac"
    return None


def avvelena(repo: Path) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from salti_windows import dichiara  # noqa: PLC0415
    esiti, saltati = [], 0
    for caso, rel, giusto, rotto, *solo in VELENI:
        motivo = non_gira_qui(caso)
        if not motivo and solo == ["windows"] and os.name != "nt":
            motivo = "il difetto che rompe c'è solo su Windows"
        if motivo:  # il testo da rompere si controlla lo stesso: un veleno vecchio cade anche qui
            assert (repo / rel).read_text(encoding="utf-8").count(giusto) == 1, \
                f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            dichiara(f"veleno {caso} ({rel})", f"{motivo}, il veleno non ha cosa rompere")
            esiti.append(caso)
            saltati += 1
            continue
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "cache"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia, caso)  # solo il caso sorvegliato: tutti i casi per ogni veleno superano i 30 minuti del gate
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)} saltati={saltati}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        return avvelena(repo)
    if argomenti.baseline_ref:
        print("BASELINE_DISCRIMINANTE=nessuna (banco nuovo: il veleno lo prova con --avvelena)")
        return 0
    rossi = prova(repo)
    for r in rossi:
        print("ROSSO", r)
    print(f"herdr: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        # Su Windows text=True e la console sono cp1252: il banco leggerebbe storto l'UTF-8 di node e dei mod,
        # e 8 casi uscivano rossi per le sole accentate (#5166). -X utf8 vale solo per il banco: i figli
        # Python partono come li lancia il prodotto, senza ereditare la modalità.
        raise SystemExit(subprocess.run([sys.executable, "-X", "utf8", *sys.argv]).returncode)
    raise SystemExit(main())
